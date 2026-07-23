"""ERCOT-99 intra-hour bound: the honest C3c denominator net of transients.

An hourly perfect-foresight LP prices the hourly-mean RT; a tail hour whose
hourly mean clears $200 only because ONE 15-minute SCED interval spiked is a
transient the model structurally smooths and can never reach.  Before any
offer-surface tuning we bound how many of the missed tail hours are *sustained*
(most intervals > $200 — reachable) vs *transient* (a single interval — not).

Reads the committed 15-minute settlement-point workbook
(``data/raw/lmp-data/RTMLZHBSPP_<year>.zip``, HB_BUSAVG) on the model's fixed
non-leap 8760 clock (identical construction to
``scripts/data/derive_ercot_zonal_lmp.py`` — HE-1, Feb-29 dropped), and the
keeper bundle's demand-weighted hub price for the missed-hour set.  No LP solve.

Usage:
    python -m scripts.probes.ercot99_intrahour_bound \\
        [--bundle results/calibration/ercot98_np6_hsl_fullspan] [--year 2023]

Diagnostic only; never registered.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

# Reuse the committed hourly deriver's DST prevailing->CST shift and clock so the
# 15-minute reconstruction lands on the SAME slot as actual_lmp_hourly_ERCOT.rt
# (HB_HUBAVG, CST standard clock) — otherwise summer tail hours misalign ~1 h.
from scripts.data.derive_actual_lmp import (  # noqa: E402
    _MONTH_START_HOUR as _MSH,
    _PrevailingShift,
)

TAIL_THRESHOLD = 200.0  # rubric §5 ERCOT scarcity threshold, $/MWh
_MONTH_START_HOUR = np.asarray(_MSH, dtype=np.int64)


def _hub_price(bundle: Path, year: int) -> pd.Series:
    """Demand-weighted hub price from a keeper bundle's P1 system sidecar."""
    sysdf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = sysdf[sysdf["pass"] == "P1"]
    price = p1.pivot(index="hour", columns="zone", values="price")
    demand = p1.pivot(index="hour", columns="zone", values="demand")
    return (price * demand).sum(axis=1) / demand.sum(axis=1)


def _actual_rt(year: int) -> pd.Series:
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    return lmp[lmp["year"] == year].set_index("hour")["rt"]


def _hubavg_15min(year: int) -> pd.DataFrame:
    """HB_HUBAVG 15-minute prices → wide (hoy x interval[1..4]) on the CST clock.

    Same settlement point (HB_HUBAVG) and same prevailing->standard DST shift as
    the committed hourly deriver, so the interval mean reproduces the scored tail.
    """
    zpath = REPO / f"data/raw/lmp-data/RTMLZHBSPP_{year}.zip"
    with zipfile.ZipFile(zpath) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            book = pd.read_excel(io.BytesIO(fh.read()), sheet_name=None, engine="openpyxl")
    df = pd.concat(book.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Settlement Point Name"] == "HB_HUBAVG"].copy()
    dt = pd.to_datetime(df["Delivery Date"])
    mo = dt.dt.month.to_numpy()
    dy = dt.dt.day.to_numpy()
    hod = df["Delivery Hour"].astype(int).to_numpy() - 1  # hour-beginning
    rep = df["Repeated Hour Flag"].astype(str).str.strip().str.upper().to_numpy() == "Y"
    keep = ~((mo == 2) & (dy == 29))
    shift = _PrevailingShift(year, "America/Chicago")
    shifts = np.array(
        [shift(int(m), int(d), int(h), bool(rr))
         for m, d, h, rr in zip(mo[keep], dy[keep], hod[keep], rep[keep])]
    )
    df = df[keep].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[keep] - 1] + (dy[keep] - 1) * 24 + hod[keep] - shifts
    df = df[(df["hoy"] >= 0) & (df["hoy"] < 8760)]
    wide = df.pivot_table(
        index="hoy", columns="Delivery Interval", values="Settlement Point Price",
        aggfunc="mean",
    )
    return wide.reindex(range(8760))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ercot99_intrahour_bound")
    parser.add_argument(
        "--bundle", default="results/calibration/ercot98_np6_hsl_fullspan"
    )
    parser.add_argument("--year", type=int, default=2023)
    args = parser.parse_args(argv)

    bundle = REPO / args.bundle
    year = args.year

    wide = _hubavg_15min(year)
    intervals = wide.to_numpy()  # (8760, 4)
    hourly_mean = np.nanmean(intervals, axis=1)
    n_above = np.nansum(intervals > TAIL_THRESHOLD, axis=1)  # 0..4 intervals hot

    # Reproduce the tail on my own hourly mean, and cross-check vs the committed
    # HB_BUSAVG hourly (they should agree to rounding).
    rt = _actual_rt(year).reindex(range(8760)).to_numpy()
    my_tail = hourly_mean > TAIL_THRESHOLD
    ref_tail = rt > TAIL_THRESHOLD
    print(
        f"[verify] my 15-min hourly-mean tail {int(np.nansum(my_tail))} h vs "
        f"committed HB_BUSAVG hourly tail {int(np.nansum(ref_tail))} h "
        f"(agree on {int(np.nansum(my_tail == ref_tail))}/8760)"
    )

    hub = _hub_price(bundle, year).reindex(range(8760)).to_numpy()
    tail = ref_tail
    missed = tail & (hub <= TAIL_THRESHOLD)
    caught = tail & (hub > TAIL_THRESHOLD)
    print(
        f"[set] actual tail {int(tail.sum())} h | model missed {int(missed.sum())} "
        f"| caught {int(caught.sum())}"
    )

    # Intra-hour hotness distribution over the missed hours.
    print("\n[intra-hour] # of 15-min intervals > $200, over the MISSED tail hours:")
    for k in range(5):
        cnt = int(((n_above == k) & missed).sum())
        share = cnt / max(1, int(missed.sum()))
        tag = {0: "(mean>200 from a sub-200 spread — pure smoothing)",
               1: "(single-interval transient — hourly LP cannot reach)",
               2: "(half-hour — borderline)",
               3: "(sustained)", 4: "(fully sustained)"}[k]
        print(f"    {k}/4 hot: {cnt:3d} h  ({share:4.0%})  {tag}")

    sustained = missed & (n_above >= 3)
    borderline = missed & (n_above == 2)
    transient = missed & (n_above <= 1)
    print(
        f"\n[bound] of {int(missed.sum())} missed: sustained(>=3/4) "
        f"{int(sustained.sum())} | borderline(2/4) {int(borderline.sum())} "
        f"| transient(<=1/4) {int(transient.sum())}"
    )
    caught_n = int(caught.sum())
    reach_ceiling = caught_n + int(sustained.sum())
    reach_ceiling_lax = caught_n + int(sustained.sum()) + int(borderline.sum())
    print(
        f"[bound] C3c REACHABILITY CEILING (caught + sustained-missed) = "
        f"{reach_ceiling}/{int(tail.sum())} "
        f"[+borderline: {reach_ceiling_lax}/{int(tail.sum())}]  "
        f"— tuning cannot exceed this with an hourly LP"
    )

    # By month, sustained vs transient, so we know where the reachable hours live.
    cal = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    print("\n[bound] sustained-missed by month (the reachable targets):")
    for m in range(1, 13):
        mm = np.asarray(cal.month == m)
        s = int((sustained & mm).sum())
        t = int((transient & mm).sum())
        b = int((borderline & mm).sum())
        if s + t + b:
            print(f"    {year}-{m:02d}: sustained {s:2d} | borderline {b:2d} | transient {t:2d}")

    # Peek at the marquee heat-wave days: per-hour interval prices.
    print("\n[detail] sample sustained-vs-transient missed hours (hod 13-20):")
    hod = cal.hour.to_numpy()
    dates = cal.strftime("%m-%d").to_numpy()
    show = missed & np.isin(hod, range(13, 21))
    idx = np.where(show)[0]
    # Show a handful spanning the classification.
    for i in list(idx[:6]) + list(idx[-4:]):
        row = intervals[i]
        cls = "SUST" if n_above[i] >= 3 else ("BORD" if n_above[i] == 2 else "TRAN")
        print(
            f"    {dates[i]} HE{hod[i]+1:02d} [{cls}] mean ${hourly_mean[i]:7.1f} "
            f"model ${hub[i]:6.1f} | 15-min "
            f"[{row[0]:7.1f} {row[1]:7.1f} {row[2]:7.1f} {row[3]:7.1f}]"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
