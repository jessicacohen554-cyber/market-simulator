"""ERCOT-68 monthly + event-day anatomy scorer (rule-16 diagnostic; no solve).

Prints, for each probe bundle:

* monthly demand-weighted settled price, model − actual ($/MWh, rt_lw_mon
  bench basis) — the moderate-tightness formation targets are May/Nov/Apr-2024
  (and May-2025);
* the May-2024 daily decomposition: day-mean model vs actual RT (raw hourly
  pairing — valid post clock-fix), flagging the event day (May 8) vs the
  DA-shoulder family (each −$15..31 on the keeper);
* C3c tail composition by month × hour-of-day block (the gate is the tail
  forming in the RIGHT hours: winter mornings / shoulder evenings, not more
  Jul/Aug evening amplitude);
* the ordc_adder column stats when present (leg J rungs).

Usage::

    python scripts/probes/_ercot68_anatomy.py BUNDLE [BUNDLE ...] --year 2024
"""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "results" / "calibration"
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    year = args.year
    cal = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    month = cal.month.to_numpy()
    day = cal.day.to_numpy()
    hod = np.arange(8760) % 24

    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == year].set_index("hour")["rt"].reindex(range(8760))
    act_np = act.to_numpy(dtype=float)

    bench = json.loads(
        gzip.open(REPO / f"frontend/data/backcast/bench/ERCOT/{year}.json.gz").read()
    )["bench"]["avgLMP"]
    rt_lw_mon = np.array(
        [v if v is not None else np.nan for v in bench["rt_lw_mon"]], dtype=float
    )

    for name in args.bundles:
        b = ROOT / name
        df = pd.read_parquet(b / "system.parquet")
        df = df[(df["pass"] == "P1") & (df["year"] == year)].copy()

        # demand-weighted hourly system settled price
        w = df["price"] * df["demand"]
        lw = w.groupby(df["hour"]).sum() / df.groupby("hour")["demand"].sum()
        lw = lw.reindex(range(8760)).to_numpy(dtype=float)
        zmax = df.groupby("hour")["price"].max().reindex(range(8760)).to_numpy()

        print(f"\n===== {name} ({year}) =====")
        # monthly model - actual (bench rt_lw_mon)
        print("-- monthly lw model-actual ($/MWh) --")
        parts = []
        for m in range(1, 13):
            msk = month == m
            mdl = np.nansum(lw[msk] * 1.0) / msk.sum()
            # demand-weighted within month
            d = df[df["hour"].isin(np.flatnonzero(msk))]
            mdl = float((d["price"] * d["demand"]).sum() / d["demand"].sum())
            a = rt_lw_mon[m - 1]
            parts.append(
                f"{m:>2}: {mdl - a:+6.1f}" if np.isfinite(a) else f"{m:>2}: n/a"
            )
        print("  " + "  ".join(parts[:6]))
        print("  " + "  ".join(parts[6:]))

        # May daily decomposition (raw hourly pairing, equal-weight day means)
        print(f"-- May-{year} day means: model | actual | delta --")
        rows = []
        for dd in range(1, 32):
            msk = (month == 5) & (day == dd)
            if not msk.any():
                continue
            mm, aa = np.nanmean(lw[msk]), np.nanmean(act_np[msk])
            rows.append((dd, mm, aa, mm - aa))
        worst = sorted(rows, key=lambda r: r[3])[:10]
        for dd, mm, aa, dl in sorted(worst):
            print(f"  May-{dd:02d}  {mm:8.1f} | {aa:8.1f} | {dl:+7.1f}")

        # C3c tail composition
        tail_h = zmax > 200.0
        print(f"-- C3c tail: {int(tail_h.sum())} h (max zonal settled > $200) --")
        if tail_h.any():
            tm = pd.Series(month[tail_h]).value_counts().sort_index()
            print("  by month:", dict(tm))
            blocks = pd.cut(
                hod[tail_h],
                bins=[-1, 5, 11, 16, 21, 23],
                labels=["h0-5", "h6-11", "h12-16", "h17-21", "h22-23"],
            )
            print(
                "  by hod block:", dict(pd.Series(blocks).value_counts().sort_index())
            )

        # ordc_adder stats when present (leg J)
        if "ordc_adder" in df.columns:
            oa = (
                df.groupby("hour")["ordc_adder"].first().reindex(range(8760)).to_numpy()
            )
            print(
                f"-- ordc_adder: mean ${np.nanmean(oa):.2f}, >$10 in "
                f"{int((oa > 10).sum())} h, >$200 in {int((oa > 200).sum())} h, "
                f"max ${np.nanmax(oa):,.0f} --"
            )
        if "rtordpa_overlay" in df.columns:
            ov = (
                df.groupby("hour")["rtordpa_overlay"]
                .first()
                .reindex(range(8760))
                .to_numpy()
            )
            print(
                f"-- rtordpa_overlay: mean ${np.nanmean(ov):.2f}, >$10 in "
                f"{int((ov > 10).sum())} h --"
            )


if __name__ == "__main__":
    main()
