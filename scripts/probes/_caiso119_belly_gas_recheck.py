"""caiso-119 RECHECK: is the caiso-118 headline "reality runs 2-3.6x MORE belly
gas than the model" actually true? Independent re-measurement of BOTH sides on a
like-for-like basis, from the KEEPER's own committed hourly sidecars and raw
CEMS. NO LP.

Why this exists: `FINDING-caiso118-belly-price-undercommit-2026-07-24.md` rests
entirely on one comparison (its Headline / INV5) —

    model belly gas 4,260 / 3,721 / 2,947 MW   vs
    ACTUAL belly gas 8,461 / 9,633 / 10,537 MW   (2.0x / 2.6x / 3.6x)

and the whole caiso-118b RA-obligation-commitment redirect follows from it. The
caiso-119 min-load derive (`_caiso119_committed_minload_derive.py`) measured
CAISO belly gas GROSS output straight off CEMS at 4,255 / 3,773 / 2,867 MW for
the non-CHP gas fleet — i.e. essentially ON the model, not 2-3.6x above it. One
of the two is wrong, and a mechanism that force-commits ~10 GW of belly gas on a
wrong actual would be a large, rule-1-violating over-forcing.

This probe puts the two candidate "actual" bases side by side against the same
model series, at the same hours, and reports the scope of each:

  BASIS A  CEMS gas, CAISO bench facility set, by class — the fleet the LP
           actually carries. Reported both excluding and including CHP, and
           gross vs net-to-grid (CEMS grossLoad includes parasitic/steam-host
           load that never reaches the CAISO grid).
  BASIS B  EIA-930 CISO natural-gas fuel-type generation — the whole CISO BA,
           which includes gas capacity that is NOT in the CEMS/LP fleet and is
           reported net at the BA boundary.

Model side comes from the CURRENT keeper's own sidecar
(`results/calibration/caiso_netrev_margin/hourly/class_hourly_<year>.parquet`),
so no proxy is involved.

Run:  .venv/bin/python scripts/probes/_caiso119_belly_gas_recheck.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "CAISO"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
KEEPER = REPO / "results" / "calibration" / "caiso_netrev_margin" / "hourly"
CISO_930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
YEARS = (2023, 2024, 2025)
BELLY = (10, 11, 12, 13, 14, 15)
GAS_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP")
NONCHP = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
# caiso-118 INV5 headline, for direct confrontation.
C118_ACTUAL = {2023: 8461, 2024: 9633, 2025: 10537}
C118_MODEL = {2023: 4260, 2024: 3721, 2025: 2947}


def model_belly(year: int) -> dict[str, float]:
    df = pd.read_parquet(KEEPER / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    hod = df["hour"].to_numpy() % 24
    df = df.assign(hod=hod)
    belly = df[df["hod"].isin(BELLY)]
    by = belly.groupby("klass")["mw"].mean()
    out = {k: float(by.get(k, 0.0)) for k in GAS_CLASSES}
    out["gas_nonchp"] = sum(out[k] for k in NONCHP)
    out["gas_all"] = sum(out[k] for k in GAS_CLASSES)
    return out


def cems_belly(year: int) -> dict[str, float]:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        plants = {int(k): v for k, v in json.load(fh)["bench"]["plants"].items()}
    df = pd.read_parquet(CAMPD / f"CA_{year}.parquet")
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df = df[df["facilityId"].astype(int).isin(plants)].copy()
    df["group"] = df["facilityId"].astype(int).map(lambda f: plants[f]["group"])
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    df = df[df["hour"].isin(BELLY)]
    n_belly_hours = df.groupby(["date", "hour"]).ngroups
    by = df.groupby("group")["grossLoad"].sum() / max(n_belly_hours, 1)
    out = {k: float(by.get(k, 0.0)) for k in GAS_CLASSES}
    out["gas_nonchp"] = sum(out[k] for k in NONCHP)
    out["gas_all"] = sum(out[k] for k in GAS_CLASSES)
    out["_belly_hours"] = float(n_belly_hours)
    return out


def e930_belly(year: int) -> float:
    df = pd.read_parquet(CISO_930)
    tcol = next((c for c in df.columns if "period" in c.lower() or "time" in c.lower()
                 or c.lower() in ("utc", "hour", "timestamp", "datetime")), None)
    gcol = next((c for c in df.columns if c.upper() in ("NG", "GAS", "NATURALGAS")
                 or "natural" in c.lower()), None)
    if tcol is None or gcol is None:
        return float("nan")
    d = df[[tcol, gcol]].copy()
    ts = pd.to_datetime(d[tcol], utc=True, errors="coerce").dt.tz_convert("US/Pacific")
    d = d.assign(y=ts.dt.year, hod=ts.dt.hour)
    d = d[(d["y"] == year) & (d["hod"].isin(BELLY))]
    return float(pd.to_numeric(d[gcol], errors="coerce").mean())


def main() -> None:
    print("=" * 96)
    print("caiso-119 RECHECK — belly (hod 10-15) gas, model vs candidate ACTUAL bases")
    print("=" * 96)
    for year in YEARS:
        m, c = model_belly(year), cems_belly(year)
        e = e930_belly(year)
        print(f"\n--- {year} ---  (CEMS belly hour-slots: {c['_belly_hours']:.0f})")
        print(f"  {'class':<14}{'MODEL keeper MW':>18}{'CEMS actual MW':>17}{'ratio A/M':>12}")
        for k in GAS_CLASSES:
            r = c[k] / m[k] if m[k] > 1 else float("nan")
            print(f"  {k:<14}{m[k]:>18,.0f}{c[k]:>17,.0f}{r:>12.2f}")
        print(f"  {'-'*60}")
        print(f"  {'gas non-CHP':<14}{m['gas_nonchp']:>18,.0f}{c['gas_nonchp']:>17,.0f}"
              f"{c['gas_nonchp']/m['gas_nonchp']:>12.2f}")
        print(f"  {'gas ALL':<14}{m['gas_all']:>18,.0f}{c['gas_all']:>17,.0f}"
              f"{c['gas_all']/m['gas_all']:>12.2f}")
        print(f"  {'EIA-930 CISO NG (whole BA, net)':<44}{e:>17,.0f}")
        print(f"  caiso-118 claimed: model {C118_MODEL[year]:,} / ACTUAL "
              f"{C118_ACTUAL[year]:,}  ({C118_ACTUAL[year]/C118_MODEL[year]:.1f}x)")

    print("\n" + "=" * 96)
    print("VERDICT TABLE — which 'actual' does the caiso-118 headline correspond to?")
    print("=" * 96)
    print(f"{'year':>6}{'model(all gas)':>16}{'CEMS(all gas)':>15}{'CEMS(nonCHP)':>14}"
          f"{'EIA930 NG':>12}{'c118 actual':>13}")
    for year in YEARS:
        m, c = model_belly(year), cems_belly(year)
        print(f"{year:>6}{m['gas_all']:>16,.0f}{c['gas_all']:>15,.0f}"
              f"{c['gas_nonchp']:>14,.0f}{e930_belly(year):>12,.0f}{C118_ACTUAL[year]:>13,.0f}")


if __name__ == "__main__":
    main()
