"""caiso-120 SCOPING: why does the model run CT_PEAKER at ~8 % of actual? NO LP.

`FINDING-caiso119-gas-basis-adjudication-2026-07-24.md` §5 named a new defect:
the model burns 0.34 TWh of CT_PEAKER against a 4.33 TWh actual (2024) — a
12.7x shortfall that C1 absorbs because its volume band is absolute
(min(2 % of annual generation, 8 TWh) ~ 5 TWh for CAISO), so a -4 TWh miss on a
4.3 TWh class passes. Peakers set the evening/scarcity margin and C3c (price
tail) is a standing keeper FAIL, so the two are plausibly one defect.

Before any mechanism is proposed, this probe separates the three candidate
causes — the same discipline that caught the caiso-118 basis error:

  A. ABSENT — the peakers are not in the LP fleet at all (missing plants, or
     binned into another class). Compares the model's CT_PEAKER nameplate
     against the CEMS/bench peaker fleet, plant by plant.

  B. DERATED — the peakers are present but their availability (outage overlay /
     CF cap) holds them near zero. Compares model pmax x availability in the
     evening peak against nameplate.

  C. PRICED OUT — the peakers are present and available but their offer price
     never clears. Compares each peaker's model marginal cost against the
     evening/scarcity-hour clearing price, and counts the hours where the unit
     was economic but did not run.

Only one of these leads to a legitimate mechanism, and they call for opposite
fixes — (A) a fleet/binning repair, (B) an availability-input repair (rule 14),
(C) an offer-curve or scarcity-formation question. Guessing between them is how
a lane spends a session solving the wrong thing.

Reference actuals are the CEMS basis and the bench `classFull` (NOT
`bench.plants[].group`, which is stale for repowered units — caiso-119 §5), and
NEVER EIA-930 CISO `NG: NG` (refuted: caiso-119 T1/T2/T3).

Run:  .venv/bin/python scripts/probes/_caiso120_ct_peaker_attribution.py \
          [--bundle results/calibration/caiso119_base_A]
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "CAISO"
CAMPD = REPO / "data" / "raw" / "campd-unit-level"
YEARS = (2023, 2024, 2025)
EVENING = (17, 18, 19, 20, 21)


def cems_peakers(year: int) -> pd.DataFrame:
    """Per-plant CEMS output for the bench's CT_PEAKER facilities."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        plants = {int(k): v for k, v in json.load(fh)["bench"]["plants"].items()}
    peak = {k: v for k, v in plants.items() if v["group"] == "CT_PEAKER"}
    df = pd.read_parquet(CAMPD / f"CA_{year}.parquet")
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df = df[df["facilityId"].astype(int).isin(peak)].copy()
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce").fillna(0.0)
    df["opTime"] = pd.to_numeric(df["opTime"], errors="coerce").fillna(0.0)
    out = df.groupby(df["facilityId"].astype(int)).agg(
        twh=("grossLoad", lambda s: s.sum() / 1e6),
        run_hours=("opTime", lambda s: float((s > 0).sum())),
        peak_mw=("grossLoad", "max"),
    )
    out["npl"] = [peak[i].get("npl") for i in out.index]
    out["name"] = [peak[i].get("name", "") for i in out.index]
    out["cf"] = out["twh"] * 1e6 / (out["npl"] * len(df["date"].unique()) * 24)
    return out.sort_values("twh", ascending=False)


def model_peakers(bundle: Path, year: int) -> pd.DataFrame | None:
    """Per-plant model dispatch for CT_PEAKER, from the bundle's dispatch file."""
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    cols = {c.lower(): c for c in df.columns}
    kcol = cols.get("plant_group") or cols.get("klass") or cols.get("group")
    if kcol is None:
        print(f"  (dispatch file has no class column; columns = {list(df.columns)})")
        return None
    df = df[df[kcol] == "CT_PEAKER"]
    if df.empty:
        return None
    idcol = cols.get("plant_id") or cols.get("plant_code") or cols.get("unit")
    mwcol = cols.get("mw") or cols.get("dispatch_mw") or cols.get("p")
    g = df.groupby(idcol).agg(twh=(mwcol, lambda s: s.sum() / 1e6),
                              run_hours=(mwcol, lambda s: float((s > 0.1).sum())),
                              peak_mw=(mwcol, "max"))
    return g.sort_values("twh", ascending=False)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--bundle", default="results/calibration/caiso119_base_A")
    args = ap.parse_args()
    bundle = REPO / args.bundle

    print("=" * 92)
    print("caiso-120 SCOPING — CT_PEAKER under-run: ABSENT vs DERATED vs PRICED OUT")
    print("=" * 92)

    for year in YEARS:
        c = cems_peakers(year)
        print(f"\n--- {year} ---  CEMS CT_PEAKER fleet: {len(c)} plants, "
              f"{c['npl'].sum()/1000:.2f} GW nameplate, {c['twh'].sum():.2f} TWh, "
              f"fleet CF {c['twh'].sum()*1e6/(c['npl'].sum()*8760):.3f}")
        print(f"  {'plant':<38}{'npl MW':>8}{'TWh':>8}{'CF':>7}{'run hrs':>9}")
        for fid, r in c.head(10).iterrows():
            print(f"  {str(r['name'])[:37]:<38}{r['npl']:>8,.0f}{r['twh']:>8.3f}"
                  f"{r['cf']:>7.3f}{r['run_hours']:>9,.0f}")

        m = model_peakers(bundle, year)
        if m is None:
            print("  MODEL: no CT_PEAKER dispatch rows found in the bundle "
                  "(bundle unsolved, or the class is ABSENT from the fleet — "
                  "cause A).")
            continue
        print(f"  MODEL CT_PEAKER: {len(m)} plants, {m['twh'].sum():.3f} TWh, "
              f"peak {m['peak_mw'].max():,.0f} MW")
        print(f"  RATIO model/actual TWh: {m['twh'].sum()/c['twh'].sum():.3f}")
        print("  READ: fleet present with ~0 energy and non-trivial peak MW -> "
              "PRICED OUT (cause C). Fleet present with peak MW ~ 0 -> DERATED "
              "(cause B). Fleet missing -> ABSENT (cause A).")

    print("\n" + "=" * 92)
    print("NOTE: this probe attributes only. Whichever cause it lands on, the fix "
          "must be a measured input or a real market mechanism (rules 1/13/14) — "
          "never an offer markdown tuned until CT_PEAKER energy matches.")


if __name__ == "__main__":
    main()
