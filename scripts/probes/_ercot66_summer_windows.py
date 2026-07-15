"""ERCOT-66 summer phantom-evening window scorer (rule-16 diagnostic; no solve).

Scores a probe/candidate bundle's ``system.parquet`` against the audit's
target windows (docs/DIAGNOSIS-ercot-summer-availability-audit-2026-07.md;
actuals from the chronologically re-paired reference, clock fix landed
2026-07-15):

* **Aug 18-20 2024 evening amplitude** — actual RT window max $3,060, no
  shed; the ercot63 keeper saturates VOLL ($5,000) with load shed.
* **Jul 30-31 2025 + Aug 18-25 2025 phantoms** — actual Aug-2025 carries
  ZERO hours > $200 (window max $243); the keeper prints $250-1,944 plateaus.
* **Storage throughput (C5b direction)** — bundle battery discharge TWh
  (keeper 2025: 4.11 vs 5.46 measured EIA-930).
* **Endogenous split honesty** (endog rungs) — the bundle's
  ``storage_as.parquet`` measured-vs-modeled table (divergence is an M4
  requirement finding, never a reason to re-pin the award — rule 13).

Usage::

    python scripts/probes/_ercot66_summer_windows.py BUNDLE [BUNDLE ...] \
        [--years 2024 2025]
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

_CAL = pd.date_range("2023-01-01", periods=8760, freq="h")  # non-leap model clock


def _window_hours(month: int, days: range | list[int]) -> np.ndarray:
    return np.flatnonzero(_CAL.month.isin([month]) & _CAL.day.isin(list(days)))


WINDOWS = {
    2024: [("Aug 18-20 2024", _window_hours(8, [18, 19, 20]))],
    2025: [
        ("Jul 30-31 2025", _window_hours(7, [30, 31])),
        ("Aug 18-25 2025", _window_hours(8, range(18, 26))),
        ("Aug 2025 (all)", _window_hours(8, range(1, 32))),
    ],
}


def score(bundle: str, years: list[int]) -> None:
    bdir = ROOT / bundle
    sys_pq = bdir / "system.parquet"
    if not sys_pq.exists():
        print(f"{bundle}: no system.parquet — skipping")
        return
    df = pd.read_parquet(sys_pq)
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    act = pd.read_parquet(ACTUAL)
    print(f"\n===== {bundle} =====")
    for year in years:
        sub = df[df["year"] == year]
        if sub.empty:
            continue
        # Settled price convention of the C3 gates: max across zones per hour
        # for the tail; demand-weighted for the level.
        piv = sub.pivot_table(index="hour", columns="zone", values="price")
        hmax = piv.max(axis=1).reindex(range(8760))
        wsum = (
            sub.groupby("hour")
            .apply(
                lambda g: float(
                    (g["price"] * g["demand"]).sum() / max(g["demand"].sum(), 1e-9)
                ),
                include_groups=False,
            )
            .reindex(range(8760))
        )
        shed = sub.groupby("hour")["slack"].sum().reindex(range(8760)).fillna(0.0)
        a = act[act["year"] == year].set_index("hour")["rt"].reindex(range(8760))
        for label, hrs in WINDOWS.get(year, []):
            print(
                f"  {label}: model max {hmax.iloc[hrs].max():7.0f}  "
                f"lw-mean {wsum.iloc[hrs].mean():7.1f}  "
                f"h>$200 {(hmax.iloc[hrs] > 200).sum():3d}  "
                f"h@VOLL {(hmax.iloc[hrs] >= 4999).sum():2d}  "
                f"shed {shed.iloc[hrs].sum() / 1e3:6.1f} GWh   |   "
                f"actual max {a.iloc[hrs].max():7.0f}  "
                f"h>$200 {(a.iloc[hrs] > 200).sum():3d}"
            )
        # Storage throughput
        st = bdir / "storage.parquet"
        if st.exists():
            sdf = pd.read_parquet(st)
            sdf = sdf[sdf["year"] == year] if "year" in sdf.columns else sdf
            if "pass" in sdf.columns:
                sdf = sdf[sdf["pass"] == "P1"]
            if "tech" in sdf.columns:
                sdf = sdf[sdf["tech"] == "li_ion"]  # battery, vs EIA-930 battery
            if "discharge_mw" in sdf.columns:
                print(
                    f"  {year} battery discharge: "
                    f"{sdf['discharge_mw'].sum() / 1e6:.2f} TWh"
                )
        # Endogenous split honesty gate
        sa = bdir / "storage_as.parquet"
        if sa.exists():
            adf = pd.read_parquet(sa)
            adf = adf[adf["year"] == year]
            if not adf.empty:
                r = np.corrcoef(adf["modeled_as_mw"], adf["measured_as_mw"])[0, 1]
                print(
                    f"  {year} AS split: modeled mean "
                    f"{adf['modeled_as_mw'].mean():5.0f} MW vs measured "
                    f"{adf['measured_as_mw'].mean():5.0f} MW (hourly r {r:.3f})"
                )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    args = ap.parse_args()
    for b in args.bundles:
        score(b, args.years)


if __name__ == "__main__":
    main()
