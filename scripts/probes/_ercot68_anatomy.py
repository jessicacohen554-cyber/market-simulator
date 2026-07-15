"""ERCOT-68 monthly + event-day anatomy scorer (rule-16 diagnostic; no solve).

Reproduces the registered-payload delta basis (render_calibration_html.py
``lmpDeltaHr``): hourly delta = demand-weighted model system price − actual RT
(raw hourly pairing — valid post clock-fix), monthly/daily means equal-weight
over hours, on the model's NON-LEAP 8760 calendar. Verified to reproduce the
ercot66 keeper 2024 controls byte-for-byte (May −12.5, Nov −5.8, Apr −4.2,
Aug −1.6; shoulder family May 9/10/12/13/21/27/29/30 at −15..−31).

Prints, for each probe bundle:

* monthly mean hourly delta ($/MWh) — the moderate-tightness formation
  targets are May/Nov/Apr-2024 (and May-2025);
* the May daily decomposition (worst days), flagging the event day (May 8)
  vs the DA-shoulder family;
* C3c tail composition by month × hour-of-day block (the gate is the tail
  forming in the RIGHT hours: winter mornings / shoulder evenings, not more
  Jul/Aug evening amplitude);
* the ordc_adder / rtordpa_overlay column stats when present (leg J rungs).

Usage::

    python scripts/probes/_ercot68_anatomy.py BUNDLE [BUNDLE ...] --year 2024
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "results" / "calibration"
ACTUAL = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)

# The model's non-leap 8760 clock (same convention as _ercot66_summer_windows).
_CAL = pd.date_range("2023-01-01", periods=8760, freq="h")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    year = args.year
    month = _CAL.month.to_numpy()
    day = _CAL.day.to_numpy()
    hod = np.arange(8760) % 24

    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == year].set_index("hour")["rt"].reindex(range(8760))
    act_np = act.to_numpy(dtype=float)

    for name in args.bundles:
        b = ROOT / name
        df = pd.read_parquet(b / "system.parquet")
        df = df[(df["pass"] == "P1") & (df["year"] == year)].copy()

        # demand-weighted hourly system settled price (the payload's mp_iso)
        lw = (
            df.groupby("hour")
            .apply(
                lambda g: float(
                    (g["price"] * g["demand"]).sum() / max(g["demand"].sum(), 1e-9)
                ),
                include_groups=False,
            )
            .reindex(range(8760))
            .to_numpy(dtype=float)
        )
        zmax = df.groupby("hour")["price"].max().reindex(range(8760)).to_numpy()
        delta = lw - act_np

        print(f"\n===== {name} ({year}) =====")
        print("-- monthly mean hourly delta, model-actual ($/MWh) --")
        parts = [f"{m:>2}: {np.nanmean(delta[month == m]):+6.1f}" for m in range(1, 13)]
        print("  " + "  ".join(parts[:6]))
        print("  " + "  ".join(parts[6:]))

        print(f"-- May-{year} worst day-mean deltas: model | actual | delta --")
        rows = []
        for dd in range(1, 32):
            msk = (month == 5) & (day == dd)
            if not msk.any():
                continue
            rows.append(
                (
                    dd,
                    np.nanmean(lw[msk]),
                    np.nanmean(act_np[msk]),
                    np.nanmean(delta[msk]),
                )
            )
        worst = sorted(rows, key=lambda r: r[3])[:10]
        for dd, mm, aa, dl in sorted(worst):
            print(f"  May-{dd:02d}  {mm:8.1f} | {aa:8.1f} | {dl:+7.1f}")

        tail_h = zmax > 200.0
        print(f"-- C3c tail: {int(tail_h.sum())} h (max zonal settled > $200) --")
        if tail_h.any():
            tm = pd.Series(month[tail_h]).value_counts().sort_index()
            print("  by month:", {int(k): int(v) for k, v in tm.items()})
            blocks = pd.cut(
                hod[tail_h],
                bins=[-1, 5, 11, 16, 21, 23],
                labels=["h0-5", "h6-11", "h12-16", "h17-21", "h22-23"],
            )
            bc = pd.Series(blocks).value_counts().sort_index()
            print("  by hod block:", {str(k): int(v) for k, v in bc.items()})

        for col in ("ordc_adder", "rtordpa_overlay"):
            if col in df.columns:
                s = (
                    df.groupby("hour")[col]
                    .first()
                    .reindex(range(8760))
                    .to_numpy(dtype=float)
                )
                print(
                    f"-- {col}: mean ${np.nanmean(s):.2f}, >$10 in "
                    f"{int((s > 10).sum())} h, >$200 in {int((s > 200).sum())} h, "
                    f"max ${np.nanmax(s):,.0f} --"
                )


if __name__ == "__main__":
    main()
