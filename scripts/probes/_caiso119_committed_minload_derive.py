"""caiso-119 DERIVE: the two MEASURED parameters the RA-obligation commitment
floor needs — (a) the physical minimum-stable-load fraction of a *committed*
CAISO gas unit, and (b) how much gas capacity CAISO actually holds COMMITTED
through the solar belly. DERIVE-FIRST, NO LP (rule #1, the ERCOT-63 template).

Context: `FINDING-caiso118b-ra-commitment-paradigm-2026-07-24.md` diagnosed the
CAISO belly defect as a commitment-PARADIGM error — the model commits gas by
ECONOMIC detection off its own (over-imported, therefore too-low) P0 belly duals
and lands at ~1.5 GW, while reality commits the RA must-offer fleet by
OBLIGATION and runs ~8-10 GW at min-load as price-takers. The redirect needs two
numbers, and rule 13/18 says BOTH must be measured, never fitted to the residual:

  M1  min-load fraction of a committed unit (`caiso_ra_min_load_frac`). The
      keeper carries 0.26 — BELOW the physical turn-down and below the code
      default 0.40 (a fit-to-shrink-forced-energy smell, rule 11-adjacent).
      Measured here as the observed turn-down floor of a fully-online unit:
      among hours with opTime == 1.0, the low percentile of grossLoad / pmax,
      capacity-weighted across units. ERCOT's analogue (60-Day DAM disclosure
      committed LSL/HSL p50) is 0.574.

  M2  the committed-capacity level the obligation floor should target: the MW of
      gas capacity actually online (opTime > 0) in the belly, vs the published
      obligation `CAISO_RA_MUSTOFFER_GAS_MW` (DMM Annual Report) the mechanism
      would key on. Confirms whether "published obligation x physical min-load"
      lands on reality's belly gas WITHOUT being tuned to it.

  M3  the implied belly load factor of the committed fleet (output / committed
      capacity) — the falsifier for M1: if reality's committed fleet runs at a
      load factor far above M1, then reality's belly gas is NOT min-load
      price-taking and the whole caiso-118b thesis is wrong.

Unit universe: the CAISO CEMS plant set is taken from the committed backcast
bench (`frontend/data/backcast/bench/CAISO/<year>.json.gz` -> bench.plants keys,
the model's own CAISO facility list), so this measures the same fleet the LP
carries — not all of California (LADWP/IID/SMUD are separate BAs).

Run:  .venv/bin/python scripts/probes/_caiso119_committed_minload_derive.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import CAISO_RA_MUSTOFFER_GAS_MW

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "CAISO"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
YEARS = (2023, 2024, 2025)
BELLY = (10, 11, 12, 13, 14, 15)
# CC and CT are the RA must-offer gas fleet the DMM quantity covers; ST_GAS is
# owned by its own drag mechanism and CHP by the steam host (rule 19).
CC_GROUPS = ("CC_REGULAR",)
GAS_GROUPS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
# CA CEMS carries non-CAISO balancing areas too; the bench plant list is the
# authoritative CAISO facility set.
STATES = ("CA",)


def _bench_plants(year: int) -> dict[int, dict]:
    """CAISO CEMS facility id -> {group, npl, zone} from the committed bench."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        bench = json.load(fh)["bench"]["plants"]
    return {int(k): v for k, v in bench.items()}


def _campd(year: int) -> pd.DataFrame:
    frames = [pd.read_parquet(CAMPD / f"{st}_{year}.parquet") for st in STATES]
    df = pd.concat(frames, ignore_index=True)
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    return df.dropna(subset=["facilityId"])


def _unit_frame(year: int) -> pd.DataFrame:
    """Per unit-hour CAISO gas frame with the unit's own observed pmax."""
    plants = _bench_plants(year)
    df = _campd(year)
    df = df[df["facilityId"].astype(int).isin(plants)].copy()
    df["group"] = df["facilityId"].astype(int).map(lambda f: plants[f]["group"])
    df = df[df["group"].isin(GAS_GROUPS)].copy()
    df["uid"] = df["facilityId"].astype(int).astype(str) + "|" + df["unitId"].astype(str)
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    df["opTime"] = pd.to_numeric(df["opTime"], errors="coerce").fillna(0.0)
    # Observed pmax: the p99.5 of running-hour output (robust to a single
    # metering spike; the unit's demonstrated sustained maximum).
    run = df[df["grossLoad"] > 0]
    pmax = run.groupby("uid")["grossLoad"].quantile(0.995).rename("pmax")
    df = df.join(pmax, on="uid")
    return df.dropna(subset=["pmax"])


def m1_minload(year: int, df: pd.DataFrame) -> dict:
    """Observed turn-down floor of a FULLY-ONLINE unit (opTime == 1.0)."""
    out = {}
    for label, groups in (("CC_REGULAR", CC_GROUPS), ("all gas", GAS_GROUPS)):
        sub = df[df["group"].isin(groups)]
        # A fully-online hour: opTime == 1 (no partial start/stop hour) and a
        # unit large enough that metering noise can't dominate.
        on = sub[(sub["opTime"] >= 0.999) & (sub["pmax"] >= 25.0) & (sub["grossLoad"] > 0)]
        if on.empty:
            continue
        on = on.assign(frac=on["grossLoad"] / on["pmax"])
        per_unit = on.groupby("uid").agg(
            p05=("frac", lambda s: float(np.percentile(s, 5))),
            p10=("frac", lambda s: float(np.percentile(s, 10))),
            hrs=("frac", "size"),
        )
        per_unit = per_unit.join(on.groupby("uid")["pmax"].first())
        # Require a unit to have a real operating history before it votes.
        per_unit = per_unit[per_unit["hrs"] >= 500]
        w = per_unit["pmax"].to_numpy()
        for tag in ("p05", "p10"):
            v = per_unit[tag].to_numpy()
            order = np.argsort(v)
            v, ww = v[order], w[order]
            cw = np.cumsum(ww) / ww.sum()
            out[f"{label}|{tag}_capwtd_p50"] = float(np.interp(0.5, cw, v))
        out[f"{label}|n_units"] = int(len(per_unit))
        out[f"{label}|pmax_gw"] = float(per_unit["pmax"].sum() / 1000.0)
    return out


def m2_committed(year: int, df: pd.DataFrame) -> dict:
    """Gas capacity ONLINE in the belly vs the published RA obligation."""
    belly = df[df["date"].notna()].copy()
    belly = belly[belly["hour"].isin(BELLY)]
    online = belly[belly["opTime"] > 0]
    # Per belly hour: committed MW (pmax of online units) and output MW.
    key = ["date", "hour"]
    cap = online.groupby(key)["pmax"].sum()
    gen = belly.groupby(key)["grossLoad"].sum()
    obligation = CAISO_RA_MUSTOFFER_GAS_MW.get(year, float("nan"))
    return {
        "belly_committed_cap_mw_mean": float(cap.mean()),
        "belly_committed_cap_mw_p50": float(cap.median()),
        "belly_gross_output_mw_mean": float(gen.mean()),
        "belly_load_factor_of_committed": float(gen.mean() / cap.mean()),
        "published_ra_obligation_mw": float(obligation),
        "committed_share_of_obligation": float(cap.mean() / obligation),
        "fleet_pmax_gw": float(df.groupby("uid")["pmax"].first().sum() / 1000.0),
    }


def main() -> None:
    print("=" * 78)
    print("caiso-119 DERIVE — measured committed min-load + belly commitment level")
    print("=" * 78)
    rows = {}
    for year in YEARS:
        df = _unit_frame(year)
        m1, m2 = m1_minload(year, df), m2_committed(year, df)
        rows[year] = {**m1, **m2}
        print(f"\n--- {year} ---")
        print("M1  physical min-load fraction of a fully-online unit "
              "(cap-weighted p50 of the per-unit low percentile):")
        for k in sorted(k for k in m1 if "capwtd" in k):
            print(f"      {k:38s} {m1[k]:.3f}")
        for k in sorted(k for k in m1 if "capwtd" not in k):
            print(f"      {k:38s} {m1[k]}")
        print("M2  belly commitment (hod 10-15, opTime > 0):")
        for k, v in m2.items():
            print(f"      {k:38s} {v:,.3f}" if isinstance(v, float) else f"      {k:38s} {v}")
        print(f"M3  implied belly load factor of the COMMITTED fleet: "
              f"{m2['belly_load_factor_of_committed']:.3f}   "
              f"(min-load M1 ~ {m1.get('all gas|p05_capwtd_p50', float('nan')):.3f})")

    print("\n" + "=" * 78)
    print("SUMMARY — the numbers the obligation floor keys on")
    print("=" * 78)
    hdr = f"{'year':>6} {'minload p05':>12} {'minload p10':>12} {'belly cmt GW':>13} " \
          f"{'RA oblig GW':>12} {'oblig x minload GW':>19} {'actual belly gas GW':>20}"
    print(hdr)
    actual_belly_gas = {2023: 8.461, 2024: 9.633, 2025: 10.537}  # caiso-118 INV5, CEMS basis
    for year, r in rows.items():
        ml = r.get("all gas|p10_capwtd_p50", float("nan"))
        ml5 = r.get("all gas|p05_capwtd_p50", float("nan"))
        print(f"{year:>6} {ml5:>12.3f} {ml:>12.3f} "
              f"{r['belly_committed_cap_mw_mean']/1000:>13.2f} "
              f"{r['published_ra_obligation_mw']/1000:>12.2f} "
              f"{r['published_ra_obligation_mw']*ml/1000:>19.2f} "
              f"{actual_belly_gas[year]:>20.2f}")
    print("\nREAD: if (published obligation x measured min-load) lands near the")
    print("actual belly gas WITHOUT tuning, the obligation floor is the right")
    print("structure (rule 1) on measured inputs (rule 13) — not a fitted level.")
    out = REPO / "results" / "calibration" / "caiso119_minload_derive.json"
    out.write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
