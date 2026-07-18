"""Build the MEASURED 2023 ERCOT load-resource RRS-UFR series (the run131 credit).

Companion to ``scripts/data/build_ercot_as_by_restype_from_60day.py`` (which builds
the measured 2023 *storage*-AS ``ercot_2023_as_by_restype_hourly.parquet`` from
the 60-Day Gen Resource Data battery awards): this script builds
``ercot_2023_as_up_mw.parquet`` — the per-service system totals the co-opt
load-resource credit (``scarcity.ercot_load_resource_reserve_mw``) consumes via
its ``rrsufr_mw`` column. Only ``rrsufr_mw`` is read downstream; the other
columns are written for schema parity with the 2024/2025 ``*_as_up_mw.parquet``.

Why RRS-UFR needs its own build (it is not measurable like storage):
RRS-UFR is the Responsive Reserve provided by Load Resources via high-set
under-frequency relays — an exclusively load-side service (generator RRSUFR
awards are 0, verified). Its *cleared* MW is not directly in the repo's 2023
files: the 60-Day Load_Resource source is **offers** (offered RRSUFR ~1.5 GW,
~2x cleared), and the residual identity ``RRS_req - cleared_genPFR -
cleared_genFFR`` also overstates (~1.6 GW vs the 0.85 GW cleared anchor) because
Load Resources provide non-UFR RRS too. So ``rrsufr_mw`` is built as a
**measured-shape, cleared-level** series: the measured 2023 load-side RRS
residual (``RRS_req`` from ASPLANNP433 minus cleared generator PFR/FFR from the
Gen Resource Data) supplies the intra-year *shape*, level-anchored to the
measured cleared RRS-UFR (NP3-911 Dec-2023 = 896 MW; 60-Day-derived 2024/2025 =
904 / 787 MW). The Dec 10-31 tail is the measured NP3-911 cleared series
directly; the Oct 2 - Dec 9 gap (no Gen Resource Data, pre-NP3-911) is
interpolated between the two measured ends (both ~0.85-0.9 GW). Documented as a
hybrid in the parquet metadata — the shape is measured, the level is
cross-source-calibrated.

Sources (``data/raw/ercot/``):
    60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_*.parquet -> cleared
        generator RRS PFR/FFR + RegUp/NonSpin awards (Jan 1 - Oct 1 delivery).
    ASPLANNP433_2023.parquet -> full-year cleared AS plan by type; ERCOT
        procures to plan, so cleared system totals == plan for the mandatory
        products (RegUp/RRS/ECRS/NSpin).
    DAMASAGGNP419_2023.parquet -> aggregated cleared-offer curve (--validate).
    data/raw/ercot-AS/*2d_cleared_dam_as_rrsufr*.zip (NP3-911) -> measured
        cleared RRS-UFR for the Dec 10-31 tail.

Run:
    python scripts/data/build_ercot_as_2023.py            # build the up_mw parquet
    python scripts/data/build_ercot_as_2023.py --validate # + DAMASAGG reconciliation
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from build_ercot_as_withholding import (  # noqa: E402
    HOURS_PER_YEAR,
    _read_service,
    _to_model_clock,
    prevailing_he_to_cst,
)
from build_ercot_hsl import _prevailing_to_standard  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
ERCOT_DIR = REPO_ROOT / "data" / "raw" / "ercot"
AS_DIR = REPO_ROOT / "data" / "raw" / "ercot-AS"

# Generator award columns read from the Gen Resource Data (Reg-Down excluded).
# ECRSSD appears only from the June-2023 ECRS go-live, so it is read when present.
_GEN_AWARD_COLS: tuple[str, ...] = (
    "RegUp Awarded",
    "RRSPFR Awarded",
    "RRSFFR Awarded",
    "RRSUFR Awarded",
    "NonSpin Awarded",
    "ECRSSD Awarded",
)

_GEN_FILES: tuple[str, ...] = (
    "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_Jan-Mar.parquet",
    "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_Apr-Jun.parquet",
    "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_Jul-Sep.parquet",
    "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_Oct-Nov.parquet",
)

# Measured cleared RRS-UFR levels anchoring the 2023 reconstruction's *level*:
# NP3-911 Dec-2023 = 896 MW, 60-Day-derived 2024 = 904, 2025 = 787. The 2023
# target is their central value (~0.86 GW), squarely in the 0.8-0.9 GW anchor.
_RRSUFR_TARGET_MEAN_MW: float = 862.0


def _rows_to_hb(df: pd.DataFrame, value: pd.Series) -> pd.DataFrame:
    """Convert (Delivery Date, Hour Ending) rows to hour-beginning ``(ts, mw)``.

    The 60-Day labels are Central Prevailing Time with sequential HE numbering
    on the DST days (HE 1-25 at fall-back), converted to the fixed CST model
    clock via ``prevailing_he_to_cst``.
    """
    date = pd.to_datetime(df["Delivery Date"], format="%m/%d/%Y")
    ts = prevailing_he_to_cst(date, df["Hour Ending"].astype(int))
    return pd.DataFrame({"ts": ts, "mw": np.asarray(value, dtype=float)})


def _load_gen_awards() -> pd.DataFrame:
    """Read the 2023 Gen Resource Data per-resource AS award columns."""
    frames: list[pd.DataFrame] = []
    for name in _GEN_FILES:
        path = ERCOT_DIR / name
        have = set(pq.read_schema(path).names)
        cols = ["Delivery Date", "Hour Ending"] + [
            c for c in _GEN_AWARD_COLS if c in have
        ]
        g = pd.read_parquet(path, columns=cols)
        for c in _GEN_AWARD_COLS:
            if c not in g.columns:
                g[c] = 0.0
        frames.append(g)
    g = pd.concat(frames, ignore_index=True)
    return g[pd.to_datetime(g["Delivery Date"], format="%m/%d/%Y").dt.year == 2023]


def _asplan_by_type() -> pd.DataFrame:
    """Return ASPLAN 2023 cleared requirement by CST hour-beginning ts per AS type.

    ASPLAN labels are Central Prevailing Time in the repeated-HE convention
    (the fall-back hour's second occurrence is flagged ``DSTFlag == 'Y'``);
    they are converted to the fixed CST model clock before indexing, so no
    DST duplicate survives and no mean-collapse is needed.
    """
    asp = pd.read_parquet(ERCOT_DIR / "ASPLANNP433_2023.parquet")
    asp["date"] = pd.to_datetime(asp["DeliveryDate"], format="%m/%d/%Y")
    asp = asp[asp["date"].dt.year == 2023].copy()
    he = asp["HourEnding"].str.slice(0, 2).astype(int)
    asp["ts"] = _prevailing_to_standard(
        asp["date"] + pd.to_timedelta(he - 1, unit="h"), asp["DSTFlag"]
    )
    asp = asp.dropna(subset=["ts"])
    return asp.groupby(["ts", "AncillaryType"])["Quantity"].mean().unstack()


def _to_model_clock_keep_gaps(rows: pd.DataFrame, year: int) -> np.ndarray:
    """Like ``_to_model_clock`` but leaves uncovered hours as NaN (no zero/interp).

    Used for series with intentional multi-month gaps (the Jan-Oct Gen window,
    the Dec-only NP3-911 feed) that the caller splices / interpolates.
    """
    cal = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    full = pd.MultiIndex.from_arrays(
        [cal.month, cal.day, cal.hour], names=["month", "day", "hour"]
    )
    if rows.empty:
        return np.full(HOURS_PER_YEAR, np.nan)
    ts = rows["ts"]
    keep = (ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    rows = rows[keep]
    if rows.empty:
        return np.full(HOURS_PER_YEAR, np.nan)
    grouped = rows.groupby(
        [rows["ts"].dt.month, rows["ts"].dt.day, rows["ts"].dt.hour]
    )["mw"].mean()
    grouped.index.names = ["month", "day", "hour"]
    return grouped.reindex(full).to_numpy(dtype=float)


def _build_rrsufr(g: pd.DataFrame, plan: pd.DataFrame) -> tuple[np.ndarray, dict]:
    """Build the measured-shape, cleared-level 2023 RRS-UFR series (8760,).

    Shape = the measured 2023 load-side RRS residual ``RRS_req - genPFR -
    genFFR`` (Jan 1 - Oct 1), scaled so its mean matches the measured cleared
    anchor; Dec 10-31 = the measured NP3-911 cleared series; the Oct 2 - Dec 9
    gap is linearly interpolated between the two measured ends.
    """
    gp = (
        g.assign(pf=g[["RRSPFR Awarded", "RRSFFR Awarded"]].sum(axis=1))
        .groupby(["Delivery Date", "Hour Ending"])["pf"]
        .sum()
        .reset_index()
    )
    # Prevailing sequential-HE labels -> CST, then join the (ts-indexed) plan.
    ts = prevailing_he_to_cst(
        pd.to_datetime(gp["Delivery Date"], format="%m/%d/%Y"),
        gp["Hour Ending"].astype(int),
    )
    rrs_req = (
        plan["RRS"].reindex(ts).to_numpy(dtype=float)
        if "RRS" in plan.columns
        else np.zeros(len(ts))
    )
    residual = np.clip(rrs_req - gp["pf"].to_numpy(), 0.0, None)
    resid_rows = pd.DataFrame({"ts": ts, "mw": residual})
    resid_grid = _to_model_clock_keep_gaps(resid_rows, 2023)

    np3 = _to_model_clock_keep_gaps(_read_service("rrsufr"), 2023)

    covered = ~np.isnan(resid_grid)
    scale = _RRSUFR_TARGET_MEAN_MW / float(np.nanmean(resid_grid[covered]))
    series = np.full(HOURS_PER_YEAR, np.nan)
    series[covered] = resid_grid[covered] * scale
    has_np3 = ~np.isnan(np3)
    series[has_np3] = np3[has_np3]
    out = pd.Series(series).interpolate(limit_direction="both").to_numpy(dtype=float)
    diag = {
        "residual_mean_covered": float(np.nanmean(resid_grid[covered])),
        "scale": float(scale),
        "np3_dec_mean": float(np.nanmean(np3[has_np3])) if has_np3.any() else 0.0,
        "out_mean": float(out.mean()),
        "out_peak": float(out.max()),
    }
    return out, diag


def _write_up_mw(rrsufr: np.ndarray, plan: pd.DataFrame, g: pd.DataFrame) -> Path:
    """Write the per-service system-total up_mw parquet (rrsufr_mw is the keeper)."""

    def plan_clock(name: str) -> np.ndarray:
        if name not in plan.columns:
            return np.zeros(HOURS_PER_YEAR)
        ser = plan[name].dropna()  # ts-indexed (CST) by _asplan_by_type
        rows = pd.DataFrame({"ts": ser.index, "mw": ser.to_numpy()})
        return _to_model_clock(rows, 2023)

    def gen_clock(col: str) -> np.ndarray:
        per = g.groupby(["Delivery Date", "Hour Ending"])[col].sum().reset_index()
        return np.nan_to_num(_to_model_clock(_rows_to_hb(per, per[col]), 2023))

    frame = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "regup_mw": plan_clock("REGUP"),
            "rrspfr_mw": gen_clock("RRSPFR Awarded"),
            "rrsffr_mw": gen_clock("RRSFFR Awarded"),
            "rrsufr_mw": rrsufr,
            # ECRS online/manual and NonSpin online/offline are not split in the
            # 2023 plan; book each total to the *_s / nspin column.
            "ecrss_mw": plan_clock("ECRS"),
            "ecrsm_mw": np.zeros(HOURS_PER_YEAR),
            "nspin_mw": plan_clock("NSPIN"),
            "nspnm_mw": np.zeros(HOURS_PER_YEAR),
        }
    )
    frame["as_up_mw"] = frame[
        [c for c in frame.columns if c.endswith("_mw") and c != "as_up_mw"]
    ].sum(axis=1)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": "ERCOT 60-Day DAM Disclosure + ASPLANNP433_2023 + NP3-911 "
            "2-Day cleared DAM AS (RRS-UFR Dec tail).",
            "description": "ERCOT 2023 system-wide hourly UP-AS MW. rrsufr_mw is "
            "the measured-shape/cleared-level load-resource RRS-UFR (the consumed "
            "co-opt credit; see scripts/data/build_ercot_as_2023.py docstring). Other "
            "columns are cleared-to-plan (ASPLAN) / measured gen awards for schema "
            "parity and are not consumed downstream.",
            "units": "MW (hour-beginning)",
            "clock": "Fixed non-leap 8760h ERCOT-local STANDARD time (CST, "
            "UTC-6): the sources' Central-Prevailing labels (60-Day/NP3-911 "
            "sequential HE; ASPLAN repeated-HE + DSTFlag) are converted "
            "CPT->CST before placement, matching the EIA-930 demand clock.",
            "year": "2023",
        }
    )
    out = AS_DIR / "ercot_2023_as_up_mw.parquet"
    pq.write_table(table, out)
    return out


def _validate(rrsufr: np.ndarray) -> None:
    """Reconcile RRS-UFR against the anchors and DAMASAGGNP419."""
    print("\n=== Validation ===")
    print(
        f"rrsufr_mw  : mean {rrsufr.mean():.0f} MW  peak {rrsufr.max():.0f}  "
        f"(anchor 0.8-0.9 GW; 2024/2025 cleared 904/787; Dec-23 NP3-911 896)"
    )
    agg = pd.read_parquet(ERCOT_DIR / "DAMASAGGNP419_2023.parquet")
    agg = agg[pd.to_datetime(agg["DeliveryDate"], format="%m/%d/%Y").dt.year == 2023]
    ru = (
        agg[agg["AncillaryType"] == "RRSUF"]
        .groupby(["DeliveryDate", "HourEnding"])["Quantity"]
        .max()
    )
    print(
        f"DAMASAGG RRSUF offered (cleared-proxy): mean {ru.mean():.0f} MW "
        f"— offers run ~2x cleared, confirming the offers file overstates the "
        f"credit (the reason rrsufr_mw is cleared-level anchored, not read raw)."
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_ercot_as_2023")
    p.add_argument(
        "--validate",
        action="store_true",
        help="Print the DAMASAGG reconciliation and anchor checks.",
    )
    args = p.parse_args(argv)

    print("Reading 2023 60-Day DAM Gen Resource Data + ASPLAN ...")
    g = _load_gen_awards()
    plan = _asplan_by_type()
    print("Building measured-shape/cleared-level RRS-UFR series ...")
    rrsufr, diag = _build_rrsufr(g, plan)
    print(
        f"  residual shape mean {diag['residual_mean_covered']:.0f} -> scaled "
        f"x{diag['scale']:.3f} -> rrsufr mean {diag['out_mean']:.0f} MW "
        f"(Dec NP3-911 measured {diag['np3_dec_mean']:.0f})"
    )
    out = _write_up_mw(rrsufr, plan, g)
    print(f"\nWrote {out.relative_to(REPO_ROOT)}")
    if args.validate:
        _validate(rrsufr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
