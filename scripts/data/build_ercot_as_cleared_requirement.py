"""Build ERCOT's hourly cleared DAM ancillary-service quantity for a back year.

**Why this exists (ercot-253, 2026-09-06).** The co-optimization's per-product AS
requirement is read from ERCOT's published AS Plan,
``data/raw/ercot/ASPLANNP433_<year>.parquet``
(:func:`market_sim.results.scarcity.ercot_as_plan_requirement_mw`), and that
report is on disk for **2022 onward only** — ERCOT MIS retention does not reach
the earlier delivery years. The loader's contract for a missing file is
"all-zero, no-op", which in a FORECAST fails loud but in a BACKCAST is silent:
a pre-2022 backcast year therefore procures **no reserve at all**, the ORDC
family never binds, and every price criterion measures the missing input rather
than the model. The ERCOT 2021 validation rung hit exactly that
(``per-product req means [0, 0, 0, 0] MW``).

**What replaces it, and why it is a measurement rather than an estimate.** The
60-Day DAM Disclosure publishes the cleared DAM AS **awards** per resource per
hour on both sides of the market — ``60d_DAM_Gen_Resource_Data_<year>_*`` and
``60d_DAM_Load_Resource_Data_<posting-year>`` — and their system sum per product
IS the quantity ERCOT procured in the Day-Ahead Market for that hour. ERCOT
procures the AS Plan quantity in DAM, so cleared ≈ planned by market design, and
:func:`validate_against_plan` measures that identity on the window where both
sources exist rather than asserting it. Rule 13 ``[R-MEASURED]``: an
ERCOT-published cleared MW quantity, never a price, and the identical
construction regenerates for any year the disclosure covers. Rule 14
``[R-ACCURATE]``: it is preferred over the forward requirement-setting formula
precisely because the measurement exists.

**Coverage.** The Gen files are named by DELIVERY quarter; the Load files by
POSTING year, each spanning deliveries Nov 2 (Y-1) .. Nov 1 (Y) — so a delivery
year needs the Y and Y+1 Load files. Delivery 2021 is fully covered (Load 2021 +
2022). Delivery 2022 is covered Jan 1 .. Nov 1 only, because the posting-year
2023 Load file is not in the repo; that is the VALIDATION window, not a gap in
any produced series.

**Products.** ``REGUP`` / ``RRS`` / ``NSPIN``, the upward products the co-opt
prices, keyed to :data:`market_sim.model.reserves.spec.ERCOT_AS_PRODUCTS`
codes. ``RegDown`` is published and deliberately ignored (the co-opt is upward).
``ECRS`` has no column before its 2023-06-10 go-live and is emitted all-zero, so
the onset stays carried by the data exactly as the AS-Plan loader has it. The
pre-2022-10-15 files carry a single undifferentiated ``RRS Awarded`` column and
the post-split ones carry the three components; both are summed to the product
total, which is what the requirement is stated in.

**Clock.** The disclosure stamps Central *Prevailing* Time (HE 1-24) while the
fleet clock is fixed CST, so the same conversion the AS-Plan loader documents is
applied here. Neither disclosure file carries a ``DSTFlag``, so the repeated
fall-back hour is disambiguated by AVERAGING its two postings — the same
treatment the AS-Plan loader gives duplicate postings of one operating hour, and
a one-hour-a-year effect on a requirement series.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

#: Disclosure award column -> AS-Plan product code. A code with several columns
#: (post-split RRS) is the SUM of them; a code with none in a file is all-zero.
_AWARD_COLUMNS: dict[str, tuple[str, ...]] = {
    "REGUP": ("RegUp Awarded",),
    "RRS": ("RRS Awarded", "RRSPFR Awarded", "RRSFFR Awarded", "RRSUFR Awarded"),
    "NSPIN": ("NonSpin Awarded",),
    "ECRS": ("ECRS Awarded", "ECRSSD Awarded", "ECRSMD Awarded"),
}
_PRODUCTS: tuple[str, ...] = ("REGUP", "RRS", "ECRS", "NSPIN")

_AS_DIR = RAW_DATA_DIR / "ercot-AS"
_ERCOT_DIR = RAW_DATA_DIR / "ercot"


def _gen_files(year: int) -> list[Path]:
    """Every 60-Day DAM Gen Resource fragment for DELIVERY *year*."""
    return sorted(
        {
            *_AS_DIR.glob(f"60d_DAM_Gen_Resource_Data_{year}_*.parquet"),
            *_ERCOT_DIR.glob(f"*60d_DAM_Gen_Resource_Data_{year}_*.parquet"),
        }
    )


def _load_files(year: int) -> list[Path]:
    """The Load Resource files a DELIVERY *year* needs (posting years Y, Y+1)."""
    return [
        p
        for p in (
            _AS_DIR / f"60d_DAM_Load_Resource_Data_{year}.parquet",
            _AS_DIR / f"60d_DAM_Load_Resource_Data_{year + 1}.parquet",
        )
        if p.exists()
    ]


def _hourly_award_totals(path: Path, year: int) -> pd.DataFrame:
    """System-total awards per (delivery hour, product) from one disclosure file.

    Returns a frame indexed by CPT hour-beginning timestamp with one column per
    product code present in the file. Rows outside *year* are dropped, so a
    posting-year Load file contributes only its in-year deliveries.
    """
    head = pd.read_parquet(path, columns=None).head(0)
    present = {
        code: [c for c in cols if c in head.columns]
        for code, cols in _AWARD_COLUMNS.items()
    }
    wanted = ["Delivery Date", "Hour Ending", *[c for v in present.values() for c in v]]
    df = pd.read_parquet(path, columns=wanted)
    date = pd.to_datetime(df["Delivery Date"], format="mixed", dayfirst=False)
    keep = date.dt.year == int(year)
    if not keep.any():
        return pd.DataFrame()
    df, date = df[keep], date[keep]
    he = pd.to_numeric(df["Hour Ending"], errors="coerce").astype("Int64")
    ts_cpt = date + pd.to_timedelta(he.astype(float) - 1.0, unit="h")
    out = pd.DataFrame({"ts_cpt": ts_cpt})
    for code, cols in present.items():
        if cols:
            out[code] = sum(
                pd.to_numeric(df[c], errors="coerce").fillna(0.0) for c in cols
            )
    return out.groupby("ts_cpt").sum(numeric_only=True)


def _to_fleet_clock(cpt_hourly: pd.Series, year: int, hours: int) -> np.ndarray:
    """CPT hour-beginning series -> the fleet's fixed-CST non-leap 8760 array.

    Mirrors ``scarcity.ercot_as_plan_requirement_mw``'s placement exactly. The
    ambiguous fall-back hour carries no flag in this source, so its two postings
    are averaged by the caller's ``groupby`` and the pair is localized to the
    FIRST occurrence; the spring-forward gap is dropped and left at zero, which
    the CST conversion then fills from the CPT HE-4 row.
    """
    local = cpt_hourly.index.tz_localize(
        "US/Central", ambiguous=True, nonexistent="NaT"
    )
    ts = local.tz_convert("Etc/GMT+6").tz_localize(None)
    ok = ts.notna() & (ts.year == int(year))
    key = (
        pd.Series(cpt_hourly.to_numpy()[ok], index=ts[ok])
        .groupby([ts[ok].month, ts[ok].day, ts[ok].hour])
        .mean()
        .to_dict()
    )
    out = np.zeros(int(hours), dtype=float)
    i = 0
    for day in pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D"):
        if day.month == 2 and day.day == 29:
            continue  # fleet clock is non-leap
        for h in range(24):
            if i >= hours:
                break
            out[i] = float(key.get((day.month, day.day, h), 0.0))
            i += 1
    return out


def build_year(year: int, hours: int = 8760) -> pd.DataFrame:
    """Cleared DAM AS quantity per product for DELIVERY *year*, on the fleet clock.

    Args:
        year: Delivery year.
        hours: Fleet-clock length (8760).

    Returns:
        Frame with ``hour`` plus one MW column per product code, lowercased
        (``regup_mw``, ``rrs_mw``, ``ecrs_mw``, ``nspin_mw``), and a
        ``covered`` boolean marking hours any source file actually reached.
    """
    files = _gen_files(year) + _load_files(year)
    if not files:
        raise SystemExit(f"no 60-Day DAM disclosure files found for delivery {year}")
    parts = [f for f in (_hourly_award_totals(p, year) for p in files) if not f.empty]
    if not parts:
        raise SystemExit(f"no {year} delivery rows in any disclosure file")
    total = (
        pd.concat(parts).groupby(level=0).sum(numeric_only=True).sort_index()
    )
    out = pd.DataFrame({"hour": np.arange(hours, dtype=int)})
    for code in _PRODUCTS:
        series = total[code] if code in total.columns else pd.Series(dtype=float)
        out[f"{code.lower()}_mw"] = (
            _to_fleet_clock(series, year, hours)
            if not series.empty
            else np.zeros(hours, dtype=float)
        )
    covered = pd.Series(1.0, index=total.index)
    out["covered"] = _to_fleet_clock(covered, year, hours) > 0
    # The spring-forward CST hour has no CPT posting of its own, so it lands
    # uncovered and would otherwise read a REQUIREMENT OF ZERO for one hour —
    # a one-hour reserve collapse the market never had. Carry the neighbouring
    # hour across it (ffill then bfill, so a gap at either end is also filled).
    # Reported by the `covered` column, never silent.
    gap = ~out["covered"].to_numpy()
    if gap.any():
        cols = [c for c in out.columns if c.endswith("_mw")]
        out[cols] = out[cols].mask(pd.Series(gap, index=out.index), other=pd.NA).ffill().bfill()
    return out


def validate_against_plan(year: int, hours: int = 8760) -> pd.DataFrame:
    """Measure cleared-vs-plan on a year where BOTH sources exist.

    The identity this checks is a market-design one — ERCOT procures the AS Plan
    quantity in the Day-Ahead Market — so it is measured, never assumed. Only
    hours the disclosure actually covers are compared; a posting-year Load gap
    would otherwise read as a spurious shortfall.
    """
    from market_sim.results.scarcity import ercot_as_plan_requirement_mw

    cleared = build_year(year, hours)
    rows = []
    cov = cleared["covered"].to_numpy()
    for code in _PRODUCTS:
        plan = ercot_as_plan_requirement_mw(year, hours, code)
        clr = cleared[f"{code.lower()}_mw"].to_numpy()
        sel = cov & ((plan > 0) | (clr > 0))
        if not sel.any():
            rows.append({"product": code, "n_h": 0})
            continue
        d = clr[sel] - plan[sel]
        rows.append(
            {
                "product": code,
                "n_h": int(sel.sum()),
                "plan_mean": round(float(plan[sel].mean()), 1),
                "cleared_mean": round(float(clr[sel].mean()), 1),
                "diff_mean": round(float(d.mean()), 1),
                "diff_p50": round(float(np.median(d)), 1),
                "diff_p95_abs": round(float(np.percentile(np.abs(d), 95)), 1),
                "within_2pct_h": round(
                    float(
                        (np.abs(d) <= 0.02 * np.maximum(plan[sel], 1.0)).mean() * 100
                    ),
                    1,
                ),
                "corr": round(float(np.corrcoef(clr[sel], plan[sel])[0, 1]), 4),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """CLI: validate on a plan year, and/or write a back year's cleared series."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate-year", type=int, default=None)
    ap.add_argument("--build-year", type=int, default=None)
    ap.add_argument("--hours", type=int, default=8760)
    args = ap.parse_args()
    if args.validate_year:
        print(f"cleared-vs-plan, delivery {args.validate_year}:")
        print(validate_against_plan(args.validate_year, args.hours).to_string(index=False))
    if args.build_year:
        df = build_year(args.build_year, args.hours)
        out = _ERCOT_DIR / f"ercot_{args.build_year}_as_cleared_requirement_hourly.parquet"
        df.to_parquet(out, index=False)
        means = {c: round(float(df[c].mean()), 1) for c in df.columns if c.endswith("_mw")}
        print(f"wrote {out} — {len(df)} h, covered {int(df['covered'].sum())} h, means {means}")


if __name__ == "__main__":
    main()
