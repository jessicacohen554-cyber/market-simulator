"""Closeout PJM renewables fix, zero LP: membership + inertness before/after.

Re-measures the W0 renewable-membership census
(``scripts/probes/_w0_renewable_membership.py`` on
``claude/closeout-b-w0-phase3``) through the loader's own lookup,
``renewables._renewable_zone_lookup``, with ``fleet_zone_vintage_coords`` off
(the pre-fix admission) and armed (the fix), for every ISO and solved year
against that year's EIA-860 ``vintage_<Y>`` directory — the directory a
``eia860_vintage_tracks_solve_year`` solve reads. For each ISO-year it also
compares, byte for byte, the three loader outputs the lookup feeds
(``_eia860_monthly_capacity`` wind/solar, ``wind_ptc_eligible_monthly_share``,
``_eia860_zone_solar_geometry``) off vs armed. Writes one JSON.

Usage::

    python scripts/probes/_pjm_renewable_membership_fix.py --out <json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")
FILES = {
    "wind": "eia860_wind_operable.parquet",
    "solar": "eia860_solar_operable.parquet",
}


def _footprint(iso: str, vdir: Path) -> set[int]:
    from market_sim.data import zone_assignment as za

    plant = pd.read_parquet(vdir / "eia860_plant.parquet")
    ba = plant["Balancing Authority Code"].astype(str).str.strip()
    if iso == "NWPP":
        nerc = plant["NERC Region"] if "NERC Region" in plant.columns else None
        keep = za._nwpp_admitted(ba, nerc)
    else:
        keep = ba.isin(za._iso_ba_codes(iso))
    return set(
        pd.to_numeric(plant.loc[keep, "Plant Code"], errors="coerce")
        .dropna()
        .astype(int)
    )


def _digest(obj) -> str:
    """sha256 over the loader output's bytes (None -> 'None')."""
    if obj is None:
        return "None"
    if isinstance(obj, tuple):
        return "|".join(_digest(o) for o in obj)
    return hashlib.sha256(np.ascontiguousarray(obj).tobytes()).hexdigest()[:16]


def _loader_digests(iso: str, year: int, vdir: Path) -> dict[str, str]:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data import renewables as R

    zones = get_iso_config(iso).zone_names
    return {
        "monthly_wind": _digest(
            R._eia860_monthly_capacity(iso, "wind", zones, year, vdir)
        ),
        "monthly_solar": _digest(
            R._eia860_monthly_capacity(iso, "solar", zones, year, vdir)
        ),
        "ptc_share": _digest(R.wind_ptc_eligible_monthly_share(iso, zones, year, vdir)),
        "solar_geometry": _digest(
            R._eia860_zone_solar_geometry(iso, zones, year, vdir)
        ),
    }


def _monthly_total(iso: str, year: int, vdir: Path, fuel: str) -> float:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data import renewables as R

    m = R._eia860_monthly_capacity(
        iso, fuel, get_iso_config(iso).zone_names, year, vdir
    )
    return 0.0 if m is None else round(float(m[:, -1].sum()), 1)


def main(argv: list[str] | None = None) -> int:
    """Measure admitted/missed MW and loader byte-identity, flag off vs armed."""
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data import zone_assignment as za
    from market_sim.data.renewables import _renewable_zone_lookup

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    args = ap.parse_args(argv)
    out: dict = {}
    for iso in ISOS:
        for year in args.years:
            vdir = EIA_860_DIR / f"vintage_{year}"
            if not vdir.is_dir():
                continue
            fp = _footprint(iso, vdir)
            state: dict[bool, dict] = {}
            for armed in (False, True):
                za.set_fleet_zone_vintage_coords(armed)
                state[armed] = {
                    "lookup": set(_renewable_zone_lookup(iso, vdir)),
                    "digests": _loader_digests(iso, year, vdir),
                    "dec_mw": {f: _monthly_total(iso, year, vdir, f) for f in FILES},
                }
            za.set_fleet_zone_vintage_coords(False)
            identical = state[False]["digests"] == state[True]["digests"]
            for fuel, fname in FILES.items():
                df = pd.read_parquet(vdir / fname)
                df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
                code = pd.to_numeric(df["Plant Code"], errors="coerce")
                mw = pd.to_numeric(
                    df["Nameplate Capacity (MW)"], errors="coerce"
                ).fillna(0)
                infp = code.isin(fp)
                rec = {"footprint_mw": round(float(mw[infp].sum()), 1)}
                for armed, tag in ((False, "off"), (True, "on")):
                    adm = code.isin(state[armed]["lookup"])
                    rec[f"missed_mw_{tag}"] = round(float(mw[infp & ~adm].sum()), 1)
                    rec[f"missed_plants_{tag}"] = int(code[infp & ~adm].nunique())
                    rec[f"admitted_outside_ba_mw_{tag}"] = round(
                        float(mw[~infp & adm].sum()), 1
                    )
                    rec[f"loader_dec_mw_{tag}"] = state[armed]["dec_mw"][fuel]
                rec["loader_outputs_identical"] = identical
                rec["digests_off"] = state[False]["digests"]
                rec["digests_on"] = state[True]["digests"]
                out[f"{iso}|{year}|{fuel}"] = rec
                print(
                    f"{iso:6s} {year} {fuel:5s} fp {rec['footprint_mw']:9.1f} "
                    f"missed off {rec['missed_mw_off']:8.1f} on {rec['missed_mw_on']:8.1f} "
                    f"loader Dec {rec['loader_dec_mw_off']:9.1f} -> {rec['loader_dec_mw_on']:9.1f} "
                    f"identical={identical}"
                )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
