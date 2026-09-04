#!/usr/bin/env python3
"""nyiso-185 Phase 0 — G0 (armed no-LP fidelity) and G1 (the grounding bar), NO LP.

PREREG-nyiso185-stgas-family-hr-ab §3 / §6: every bar read verbatim.

* **G0** — ``reconstruct_bundle_fleet`` flag-OFF reproduces nyiso-184's
  Ravenswood bases (9.50 ST / 8.80 CC); flag-ON moves ONLY generators at the
  nyiso-184 G4 footprint plants, with every (2500, ST_GAS) tranche scaled by
  12.2918/9.5 and every (2500, CC_REGULAR) tranche by 7.3499/8.8005.
* **G1a** — F_H = CAMPD all-hours HR / running-hour HR over the plant's
  ST_GAS units: Ravenswood inside the eight peers' [min, max].
* **G1b** — F_B = eGRID-2023 ST-family HTIAN / CAMPD steam heat within
  [0.99, 1.01] at Ravenswood (peers reported).
* **G1c** — plant-level EIA-923 net (PLNGENAN) / CAMPD gross over EVERY unit
  of the facility: Ravenswood inside the eight peers' [min, max].
* **G1d** — reported only: F_D per family / per generator at 2500 with CF.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO), str(_REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from scripts.data.derive_egrid_family_heat_rates import (  # noqa: E402
    APPLIED_VINTAGE,
    _sheets,
)
from scripts.lib.bundle_fleet import (  # noqa: E402
    assert_reconstruction_fidelity,
    bundle_gas_price,
    full_run_year_kwargs,
    reconstruct_bundle_fleet,
)
from scripts.probes.nyiso183_g4c_offer_position import stgas_units  # noqa: E402
from scripts.probes.nyiso183_g4d_offer_anatomy import NAMES  # noqa: E402
from scripts.probes.nyiso184_heat_rate_basis import (  # noqa: E402
    _campd_unit_totals,
    _groups,
    _plant_frame,
)

KEEPER = _REPO / "results" / "calibration" / "nyiso177_vintage_B1p"
ARTIFACT = PROCESSED_DIR / "egrid_family_heat_rates_NYISO.csv"
RAW = _REPO / "data" / "raw"
ISO = "NYISO"
YEAR = 2023
RAVENSWOOD = 2500
PEERS = (2527, 2625, 2516, 2490, 2517, 2480, 8006, 2511)
FOOTPRINT = {2490, 2500, 2511, 2516, 2517, 8906, 50292}  # nyiso-184 G4
ST_BASE_OFF, CC_BASE_OFF = 9.5, 8.8005
FB_TOL = 0.01
G0_TOL = 1e-3


def armed_state(year: int) -> dict:
    """The keeper's no-LP reconstruction with egrid_family_heat_rates=True."""
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = full_run_year_kwargs(meta)
    kw["egrid_family_heat_rates"] = True
    state = run_year(
        year, meta["iso"], int(meta["hours"]), bundle_gas_price(meta, year), **kw
    )
    assert_reconstruction_fidelity(meta, state["config"])
    assert state["config"].egrid_family_heat_rates is True
    return state


def facility_gross(year: int, facilities: set[int]) -> dict[int, float]:
    """All-hours CAMPD gross MWh over EVERY unit of each facility (raw rows)."""
    out: dict[int, float] = {}
    for st in campd.states_for_iso(ISO):
        path = RAW / "campd-unit-level" / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=["facilityId", "grossLoad"])
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(facilities)]
        g = (
            pd.to_numeric(df["grossLoad"], errors="coerce")
            .fillna(0.0)
            .groupby(df["facilityId"])
            .sum()
        )
        for f, v in g.items():
            out[int(f)] = out.get(int(f), 0.0) + float(v)
    return out


def run() -> dict:
    out: dict = {
        "session": "nyiso-185",
        "prereg": "results/calibration/PREREG-nyiso185-stgas-family-hr-ab.md",
    }
    # ---------------- G0 ----------------
    off, _ = reconstruct_bundle_fleet(KEEPER, YEAR, verbose=True)
    on = armed_state(YEAR)
    a, b = _plant_frame(off), _plant_frame(on)
    fa, fb = off["fleet_arrays"], on["fleet_arrays"]
    a["unit"] = np.asarray(fa.unit_ids, dtype=object)
    b["unit"] = np.asarray(fb.unit_ids, dtype=object)
    m = a.merge(b, on=["unit", "plant", "klass"], suffixes=("_off", "_on"))
    assert len(m) == len(a) == len(b), (len(m), len(a), len(b))
    moved = m[(m["heat_rate_off"] - m["heat_rate_on"]).abs() > 1e-9]
    outside = sorted(set(moved["plant"]) - FOOTPRINT)
    rav_st = m[(m["plant"] == RAVENSWOOD) & (m["klass"] == "ST_GAS")]
    rav_cc = m[(m["plant"] == RAVENSWOOD) & (m["klass"] == "CC_REGULAR")]
    st_ratio = (rav_st["heat_rate_on"] / rav_st["heat_rate_off"]).to_numpy()
    cc_ratio = (rav_cc["heat_rate_on"] / rav_cc["heat_rate_off"]).to_numpy()
    art = pd.read_csv(ARTIFACT)
    fam = art[art["plant_id"] == RAVENSWOOD].set_index("family")["heat_rate_mmbtu_mwh"]
    want_st, want_cc = float(fam["ST"]) / ST_BASE_OFF, float(fam["CC"]) / CC_BASE_OFF
    base_st_off = float(rav_st["heat_rate_off"].min()) / 1.05
    base_cc_off = float(rav_cc["heat_rate_off"].min()) / 0.90
    g0 = {
        "base_st_off": round(base_st_off, 4),
        "base_cc_off": round(base_cc_off, 4),
        "rows_moved": int(len(moved)),
        "plants_moved": sorted(int(p) for p in set(moved["plant"])),
        "plants_outside_footprint": outside,
        "st_ratio_on_over_off": [
            round(float(x), 5) for x in sorted(set(np.round(st_ratio, 5)))
        ],
        "st_ratio_expected": round(want_st, 5),
        "cc_ratio_on_over_off": [
            round(float(x), 5) for x in sorted(set(np.round(cc_ratio, 5)))
        ],
        "cc_ratio_expected": round(want_cc, 5),
        "mw_moved": round(float(moved["cap_mw_off"].sum()), 1),
    }
    g0["fires"] = bool(
        abs(base_st_off - ST_BASE_OFF) <= 0.01
        and abs(base_cc_off - CC_BASE_OFF) <= 0.01
        and not outside
        and np.allclose(st_ratio, want_st, atol=G0_TOL)
        and np.allclose(cc_ratio, want_cc, atol=G0_TOL)
    )
    out["G0"] = g0
    print("G0", json.dumps(g0, indent=1))
    if not g0["fires"]:
        out["stop"] = "S0"
        return out

    # ---------------- G1 ----------------
    groups = _groups(a)
    members = stgas_units(YEAR, groups)
    facs = set(PEERS) | {RAVENSWOOD}
    tot = _campd_unit_totals(YEAR, facs)
    plnt, unt, gen = _sheets(APPLIED_VINTAGE)
    unt["HTIAN"] = pd.to_numeric(unt["HTIAN"], errors="coerce")
    gen["GENNTAN"] = pd.to_numeric(gen["GENNTAN"], errors="coerce")
    st_htian = unt[unt["PRMVR"].astype(str) == "ST"].groupby("ORISPL")["HTIAN"].sum()
    st_genntan = (
        gen[gen["PRMVR"].astype(str) == "ST"].groupby("ORISPL")["GENNTAN"].sum()
    )
    plngenan = plnt.set_index("ORISPL")["PLNGENAN"]
    fac_gross = facility_gross(YEAR, facs)
    per_plant: dict[int, dict] = {}
    for p in sorted(facs):
        units = [u for (f, u) in members if f == p]
        sub = tot[(tot["facility"] == p) & (tot["unit"].isin(units))]
        if sub.empty:
            continue
        gross, heat = float(sub["gross_mwh"].sum()), float(sub["heat_mmbtu"].sum())
        ok = sub.dropna(subset=["hr_run"])
        hr_run = (
            float((ok["hr_run"] * ok["gross_mwh"]).sum() / ok["gross_mwh"].sum())
            if not ok.empty
            else None
        )
        F_H = (heat / gross) / hr_run if (gross and hr_run) else None
        F_B = float(st_htian.get(p, np.nan)) / heat if heat else None
        F_D = (
            gross / float(st_genntan.get(p, np.nan)) if p in st_genntan.index else None
        )
        plant_net_over_gross = (
            float(plngenan.get(p, np.nan)) / fac_gross[p] if fac_gross.get(p) else None
        )
        per_plant[p] = {
            "name": NAMES.get(p, ""),
            "units": units,
            "F_H": F_H,
            "F_B": F_B,
            "F_D_st_family": F_D,
            "plant_PLNGENAN_over_campd_gross_all_units": plant_net_over_gross,
        }
    peers = {p: v for p, v in per_plant.items() if p in PEERS}
    rav = per_plant[RAVENSWOOD]
    fh = [v["F_H"] for v in peers.values() if v["F_H"]]
    pg = [
        v["plant_PLNGENAN_over_campd_gross_all_units"]
        for v in peers.values()
        if v["plant_PLNGENAN_over_campd_gross_all_units"]
    ]
    g1 = {
        "peers": peers,
        "G1a_peer_F_H_range": [min(fh), max(fh)],
        "G1a_ravenswood_F_H": rav["F_H"],
        "G1b_ravenswood_F_B": rav["F_B"],
        "G1c_peer_plant_net_over_gross_range": [min(pg), max(pg)],
        "G1c_ravenswood_plant_net_over_gross": rav[
            "plant_PLNGENAN_over_campd_gross_all_units"
        ],
    }
    print("G1a peers' F_H range (computed first):", g1["G1a_peer_F_H_range"])
    print(
        "G1c peers' plant net/gross range (computed first):",
        g1["G1c_peer_plant_net_over_gross_range"],
    )
    g1["G1a"] = bool(min(fh) <= rav["F_H"] <= max(fh))
    g1["G1b"] = bool(abs(rav["F_B"] - 1.0) <= FB_TOL)
    g1["G1c"] = bool(
        min(pg) <= rav["plant_PLNGENAN_over_campd_gross_all_units"] <= max(pg)
    )
    g1["fires"] = bool(g1["G1a"] and g1["G1b"] and g1["G1c"])
    # G1d — reported only.
    ravu = tot[tot["facility"] == RAVENSWOOD].set_index("unit")
    g_rav = gen[gen["ORISPL"] == RAVENSWOOD].copy()
    g_rav.index = g_rav["GENID"].astype(str)
    hours = 8760
    peaks = (
        pd.read_parquet(
            RAW / "campd-unit-level" / f"NY_{YEAR}.parquet",
            columns=["facilityId", "unitId", "grossLoad"],
        )
        .assign(facilityId=lambda d: pd.to_numeric(d["facilityId"], errors="coerce"))
        .query("facilityId == @RAVENSWOOD")
        .groupby("unitId")["grossLoad"]
        .max()
    )
    g1["G1d_reported"] = {
        "F_D_st_family": rav["F_D_st_family"],
        "F_D_cc_family": float(ravu.loc["UCC001", "gross_mwh"])
        / float(g_rav.loc["4", "GENNTAN"] + g_rav.loc["4S", "GENNTAN"]),
        "per_generator": {
            f"gen {gid} / unit {uid}": {
                "net_over_gross": float(g_rav.loc[gid, "GENNTAN"])
                / float(ravu.loc[uid, "gross_mwh"]),
                "cf_2023": float(ravu.loc[uid, "gross_mwh"])
                / (float(peaks[uid]) * hours),
            }
            for gid, uid in (("1", "10"), ("2", "20"), ("3", "30"))
        },
        "peers_F_D_st_family": {p: v["F_D_st_family"] for p, v in peers.items()},
    }
    out["G1"] = g1
    print(
        "G1",
        json.dumps(
            {k: v for k, v in g1.items() if k != "peers"}, indent=1, default=str
        ),
    )
    out["G3_rule19_code_check"] = {
        "2500_in_campd_ct_heat_rates": False,
        "2500_in_chp_power_only_heat_rates": False,
        "2500_in_egrid_identity_heat_rates": False,
        "note": "grep -c '^2500,' on the three artifacts = 0 each (2026-09-04); the dict skip is exercised by G0 (ST rows scale from 9.5, not 8.80)",
    }
    if not g1["fires"]:
        out["stop"] = (
            "S1: G1 failed — the A/B runs under the owner's ruling; the arm is a PROBE, never a candidate"
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(_REPO / "results" / "calibration" / "_nyiso185_grounding.json"),
    )
    args = ap.parse_args()
    res = run()
    Path(args.out).write_text(json.dumps(res, indent=2, default=str))
    print("\nstop:", res.get("stop", "none — G0 and G1 fired"))
    print("written:", args.out)


if __name__ == "__main__":
    main()
