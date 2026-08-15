"""Adjudicate NYISO's P-24A "Time Stamp" convention against NYISO's OWN published data.

The instrument behind the NYISO-RTD-CLOCK addendum to
``docs/handoffs/d32-f6fix-2026-08-13.md`` (§A.3 / §A.5). It answers one question:
does the ``Time Stamp`` column of NYISO's 5-minute real-time zonal LBMP export
label an interval by its **beginning** or by its **ending**?

``scripts/data/derive_actual_lmp.py::_nyiso_wide`` assumes beginning (plain
``.floor("h")``); ``scripts/data/curate_lmp.py::parse_nyiso_zip`` assumes ending
(``(ts - 1s).floor("h")``). Exactly one is right, and the disagreement is the
whole of the NYISO residual that survived the D-32-F6FIX repair.

**Why this is an adjudication and not a score.** NYISO publishes two products off
the same 5-minute prices:

* **P-24A** ``csv/realtime/<yyyymmdd>realtime_zone_csv.zip`` — the 5-minute
  preliminary ex-post zonal LBMPs. This is our source.
* **P-4A** ``csv/rtlbmp/<yyyymm>01rtlbmp_zone_csv.zip`` — "Time-Weighted /
  Integrated Real-Time LBMP [Zonal]", hourly.

and publishes, in prose, that the second is built from the first:

    "Zonal, Generator and Transmission Node Time Weighted/Integrated LBMP
    information will be produced by the MIS, using the 5-minute real-time
    prices, also from the MIS."
    -- Manual 12, Transmission and Dispatch Operations Manual, p. 136

    "Each RTD interval [value] is multiplied by the length of the RTD interval
    (in seconds) and then divided by 3,600 seconds per hour, the results of
    which are summed over the hour."
    -- Manual 14, Accounting and Billing Manual, section 4

So P-4A *is* NYISO's own published answer to "which 5-minute stamps belong to
which hour". Binning P-24A under each candidate convention and diffing against
P-4A therefore decides the question. P-4A carries two decimals, so a max
absolute difference of 0.005 IS exact agreement.

The ``--strict`` mode restricts to zone-hours holding exactly twelve 300-second
intervals, where the Manual-14 duration weighting collapses to a plain mean and
the hour assignment is the ONLY remaining free choice. Measured result: ENDING
never exceeds 0.0050 on any of 65,384 such zone-hours across nine months of
2022-2025; BEGINNING is wrong on 62,598 of them, by up to $151.67.

Read-only. Touches no product, writes nothing, solves nothing. P-4A months are
downloaded to a cache directory on first use.

Usage::

    python3 scripts/probes/nyiso_rtd_clock_adjudication.py 202406
    python3 scripts/probes/nyiso_rtd_clock_adjudication.py --strict 202201 202203 202211
"""

from __future__ import annotations

import argparse
import io
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

#: P-24A monthly archives, as staged by the NYISO LMP intake.
RT5_DIR = RAW_DATA_DIR / "lmp-data" / "NYISO"
#: P-4A monthly archives, NYISO MIS public postings.
P4A_URL = "http://mis.nyiso.com/public/csv/rtlbmp/{ym}01rtlbmp_zone_csv.zip"
#: Where downloaded P-4A months are cached (gitignored scratch, not a product).
P4A_CACHE = Path("/tmp/nyiso_p4a_cache")

#: The eleven internal NYISO load zones, mirroring
#: ``derive_actual_lmp.NYISO_INTERNAL``. The four external proxy buses
#: (H Q / NPX / O H / PJM) are excluded from both sides so the hub definition
#: cannot confound the clock question.
INTERNAL = (
    "CAPITL",
    "CENTRL",
    "DUNWOD",
    "GENESE",
    "HUD VL",
    "LONGIL",
    "MHK VL",
    "MILLWD",
    "N.Y.C.",
    "NORTH",
    "WEST",
)
LMP_COL = "LBMP ($/MWHr)"
#: Published P-4A values carry two decimals, so this is the exact-agreement bound.
#: The epsilon keeps a difference sitting exactly ON the bound (float64 renders
#: 0.005 as 0.005000000000000000104…, so a bare ``> 0.005`` counts it as over)
#: on the agreeing side, where it belongs.
ROUNDING = 0.005
ROUNDING_EPS = 1e-9


def _read_zip(path: Path) -> pd.DataFrame:
    """Concatenate every CSV member of one NYISO monthly archive."""
    parts = []
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            if name.lower().endswith(".csv"):
                parts.append(pd.read_csv(io.BytesIO(zf.read(name))))
    if not parts:
        raise ValueError(f"no CSV members in {path}")
    return pd.concat(parts, ignore_index=True)


def _load(path: Path) -> pd.DataFrame:
    """One monthly archive reduced to the internal zones, with parsed stamps."""
    df = _read_zip(path)
    df = df[df["Name"].isin(INTERNAL)].copy()
    df["ts"] = pd.to_datetime(df["Time Stamp"], format="mixed")
    return df


def _p4a(ym: str) -> pd.DataFrame:
    """NYISO's published hourly integration for ``ym`` (``YYYYMM``), cached."""
    P4A_CACHE.mkdir(parents=True, exist_ok=True)
    dest = P4A_CACHE / f"p4a_{ym}.zip"
    if not dest.exists():
        subprocess.run(
            ["curl", "-sSf", "-o", str(dest), P4A_URL.format(ym=ym)], check=True
        )
    return _load(dest)


def adjudicate(ym: str, strict: bool) -> list[tuple]:
    """Return one ``(month, convention, n, mean, max, n_over)`` row per convention.

    Args:
        ym: Month as ``YYYYMM``.
        strict: Restrict to zone-hours of exactly twelve 300-second intervals,
            where the hour assignment is the only free choice and the
            integration is a plain mean. Otherwise weight each interval by its
            own length per Manual 14.

    Returns:
        A row per candidate convention, comparable across conventions: the count
        of zone-hours compared, and the mean / max / over-rounding count of the
        absolute difference against NYISO's published P-4A, in $/MWh.
    """
    five = _load(RT5_DIR / f"{ym}01realtime_zone_csv.zip").sort_values(["Name", "ts"])
    ref = (
        _p4a(ym)
        .pivot_table(index="ts", columns="Name", values=LMP_COL, aggfunc="mean")
        .stack()
    )

    # Interval-ENDING reading: this stamp closes the interval the previous one
    # opened, so the gap back to the previous stamp IS the interval length.
    # RTD really does emit sub-minute intervals, so this is not clipped below.
    five["dur"] = (
        (five["ts"] - five.groupby("Name")["ts"].shift(1))
        .dt.total_seconds()
        .fillna(300.0)
        .clip(upper=3600)
    )
    five["weighted"] = five[LMP_COL] * five["dur"]

    rows = []
    conventions = (
        ("BEGINNING", five["ts"].dt.floor("h")),
        ("ENDING", (five["ts"] - pd.Timedelta(seconds=1)).dt.floor("h")),
    )
    for label, hour in conventions:
        grouped = five.assign(slot=hour).groupby(["slot", "Name"])
        if strict:
            regular = grouped.apply(
                lambda g: len(g) == 12 and (g["dur"] == 300).all(),
                include_groups=False,
            )
            agg = grouped[LMP_COL].mean()
            agg = agg[regular.reindex(agg.index).fillna(False).to_numpy()]
        else:
            agg = grouped["weighted"].sum() / grouped["dur"].sum()
        agg.index.names = ref.index.names
        shared = agg.index.intersection(ref.index)
        diff = (agg.loc[shared] - ref.loc[shared]).abs()
        rows.append(
            (
                ym,
                label,
                len(diff),
                float(diff.mean()),
                float(diff.max()),
                int((diff > ROUNDING + ROUNDING_EPS).sum()),
            )
        )
    return rows


def main() -> None:
    """Print the per-month adjudication table and the pooled totals."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("months", nargs="+", help="months as YYYYMM")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="only zone-hours of exactly twelve 300s intervals (plain-mean case)",
    )
    args = ap.parse_args()

    rows = [r for ym in args.months for r in adjudicate(ym, args.strict)]

    mode = "strict (12 x 300s hours only)" if args.strict else "duration-weighted"
    print(f"NYISO P-24A binned to hours vs NYISO's published P-4A -- {mode}")
    print(
        f"11 internal zones. |diff| in $/MWh; P-4A has 2 decimals, so "
        f"{ROUNDING} IS exact.\n"
    )
    print(
        f"{'month':8s} {'convention':11s} {'zone-hours':>10s} "
        f"{'mean|d|':>10s} {'max|d|':>10s} {'n>rounding':>11s}"
    )
    for ym, label, n, mean, mx, over in rows:
        print(f"{ym:8s} {label:11s} {n:10d} {mean:10.6f} {mx:10.4f} {over:11d}")

    print()
    for label in ("BEGINNING", "ENDING"):
        sel = [r for r in rows if r[1] == label]
        n = sum(r[2] for r in sel)
        mean = sum(r[3] * r[2] for r in sel) / n
        print(
            f"TOTAL {label:11s} n={n:6d}  mean|d|={mean:.6f}  "
            f"max|d|={max(r[4] for r in sel):.4f}  "
            f"n>rounding={sum(r[5] for r in sel)}"
        )


if __name__ == "__main__":
    main()
