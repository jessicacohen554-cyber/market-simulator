"""F1 zero-LP heat-rate-source census (audit §3a / §3b, re-run after the fix).

Reproduces ``docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md``
§6 for every ISO x backcast year 2019-2025, and adds the per-plant residual list
the F1 acceptance needs. No LP is built or solved: every number is a fleet load.

Two measures of "priced at the asset-class table", reported side by side:

* ``bins_share`` — the AUDIT's own heuristic, kept so the pre/post numbers are
  comparable with §3a: thermal nameplate whose loaded heat rate equals a value in
  ``HEAT_RATE_BINS`` for its fuel. It over-counts slightly (the simple-cycle
  floor clamp and a plant whose measured rate happens to equal a bin value both
  read as "class table").
* ``null_share`` — the EXACT measure: thermal nameplate whose EIA-860 source row
  carries no joined eGRID ``heat_rate`` (the only path into the loader's
  ``HEAT_RATE_BINS`` fallback). The residual plant list is built from this.

Postures:

* ``--posture egrid`` (default) — every measured-heat-rate flag OFF, i.e. the
  eGRID layer alone: what D1/D2 are about.
* ``--posture backcast-default`` — the post-F1 backcast default: the year-matched
  vintage AND every ``measured_*_heat_rates`` flag ON at the solve year (ERCOT
  keeps its measured flags off, as the default does).

Sources per ISO-year:

* ``--source tracked`` (default) — the post-F1 backcast default: ``vintage_<Y>/``
  where committed (2018-2024), else the canonical snapshot (2025), each loaded
  at ``year=Y``.
* ``--source audit`` — the audit's §3a columns: canonical, vintage_2021,
  vintage_2023 (plus every other vintage).

Usage::

    uv run python docs/handoffs/f1/census.py --out docs/handoffs/f1/census_post.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import HEAT_RATE_BINS  # noqa: E402
from market_sim.config.paths import EIA_860_DIR, set_eia860_vintage  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.fleet.eia860 import (  # noqa: E402
    ba_codes,
    load_retired_within_window,
)

ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NWPP", "NYISO", "PJM", "SOCO", "SPP")
YEARS = tuple(range(2019, 2026))
THERMAL = ("coal", "gas_cc", "gas_ct", "gas_st", "oil")
RETIRED = "eia860_generator_retired_within_window.parquet"


def _is_bin_value(fuel: str, hr: float) -> bool:
    """True when ``hr`` equals one of ``HEAT_RATE_BINS[fuel]``'s values (audit §6)."""
    return any(abs(hr - v) < 1e-9 for v in HEAT_RATE_BINS.get(fuel, {}).values())


def _null_hr_plants(path: Path, iso: str) -> set[int]:
    """Plant codes whose source rows carry no joined eGRID heat rate."""
    df = pd.read_parquet(path)
    codes = ba_codes(iso)
    if codes and "balancing_authority_code" in df.columns:
        df = df[df["balancing_authority_code"].astype(str).str.strip().isin(codes)]
    if "heat_rate" not in df.columns:
        return set(pd.to_numeric(df["plant_id"], errors="coerce").dropna().astype(int))
    hr = pd.to_numeric(df["heat_rate"], errors="coerce")
    null = df[hr.isna() | (hr <= 0.0)]
    return set(pd.to_numeric(null["plant_id"], errors="coerce").dropna().astype(int))


def _flags(posture: str, iso: str) -> dict:
    on = posture == "backcast-default" and iso != "ERCOT"
    return {
        "measured_ct_heat_rates": on,
        "measured_coal_heat_rates": on,
        "measured_st_heat_rates": on,
        "measured_cc_heat_rates": on,
        "measured_chp_heat_rates": on,
    }


def _summarise(gens, null_plants: set[int], online_in: int | None) -> dict:
    """Class-table MW / thermal MW for one generator list."""
    thermal = 0.0
    bins_mw = 0.0
    null_mw = 0.0
    residual: dict[int, dict] = {}
    for g in gens:
        if g.fuel_type not in THERMAL:
            continue
        if online_in is not None:
            if int(g.online_year or 0) > online_in:
                continue
            if g.retirement_year is not None and int(g.retirement_year) < online_in:
                continue
        mw = float(g.pmax_mw)
        thermal += mw
        if _is_bin_value(g.fuel_type, float(g.heat_rate)):
            bins_mw += mw
        code = int(g.plant_code or 0)
        if code in null_plants and _is_bin_value(g.fuel_type, float(g.heat_rate)):
            null_mw += mw
            row = residual.setdefault(
                code,
                {"plant_code": code, "name": g.name, "fuels": set(), "mw": 0.0},
            )
            row["fuels"].add(g.fuel_type)
            row["mw"] += mw
    return {
        "thermal_mw": round(thermal, 1),
        "bins_mw": round(bins_mw, 1),
        "bins_share": round(bins_mw / thermal, 4) if thermal else None,
        "null_mw": round(null_mw, 1),
        "null_share": round(null_mw / thermal, 4) if thermal else None,
        "residual": [
            {**r, "fuels": sorted(r["fuels"]), "mw": round(r["mw"], 1)}
            for r in sorted(residual.values(), key=lambda r: -r["mw"])
        ],
    }


def operable_census(iso: str, source: str, posture: str) -> dict:
    """§3a: class-table share of thermal nameplate per EIA-860 source."""
    out: dict[str, dict] = {}
    if source == "tracked":
        plan = [
            (str(y), y if (EIA_860_DIR / f"vintage_{y}").is_dir() else None, y)
            for y in YEARS
        ]
    else:
        plan = [("canonical", None, 2025)] + [
            (f"vintage_{v}", v, v)
            for v in range(2018, 2025)
            if (EIA_860_DIR / f"vintage_{v}").is_dir()
        ]
    for label, vintage, year in plan:
        data_dir = set_eia860_vintage(vintage)
        try:
            gens = load_fleet_from_csv(iso, year=year, **_flags(posture, iso))
        finally:
            set_eia860_vintage(None)
        null_plants = _null_hr_plants(data_dir / "eia860_generators.parquet", iso)
        rec = _summarise(gens, null_plants, None)
        rec["source"] = data_dir.name if data_dir != EIA_860_DIR else "canonical"
        out[label] = rec
    return out


def retiree_census(iso: str) -> dict:
    """§3b: within-window retirees online in each year, at a class-table rate."""
    set_eia860_vintage(None)
    null_plants = _null_hr_plants(EIA_860_DIR / RETIRED, iso)
    out: dict[str, dict] = {}
    for year in YEARS[:-1]:
        gens = load_retired_within_window(iso, year=year)
        rec = _summarise(gens, null_plants, year)
        rec["retiree_units"] = len(gens)
        out[str(year)] = rec
    return out


def main() -> int:
    """Run the census and write its JSON."""
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--iso", nargs="+", default=list(ISOS))
    ap.add_argument("--source", choices=("tracked", "audit"), default="tracked")
    ap.add_argument("--posture", choices=("egrid", "backcast-default"), default="egrid")
    a = ap.parse_args()
    record: dict = {"source": a.source, "posture": a.posture, "isos": {}}
    for iso in a.iso:
        print(f"{iso} ...", flush=True)
        record["isos"][iso] = {
            "operable": operable_census(iso, a.source, a.posture),
            "retirees": retiree_census(iso),
        }
    Path(a.out).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    for iso, rec in record["isos"].items():
        cells = " ".join(
            f"{k}:{v['bins_share']}/{v['null_share']}"
            for k, v in rec["operable"].items()
        )
        ret = " ".join(
            f"{k}:{v['null_mw']:.0f}/{v['thermal_mw']:.0f}"
            for k, v in rec["retirees"].items()
        )
        print(f"{iso:6s} operable bins/null {cells}")
        print(f"{'':6s} retirees null/online {ret}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
