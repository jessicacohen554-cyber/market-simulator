#!/usr/bin/env python
"""ercot-218 DIRECT-DRIVER PHASE-0 — the ercot-211 identifiability instrument
re-run with the measured AS-state driver swap.

Pre-registered in ``docs/PRECOMMIT-ercot218-direct-driver-phase0-2026-08-17.md``
and executed exactly as written there. **Read-only**: no LP, no solve, no year
scored, no run registered, no ``ScenarioConfig`` field, no mechanism-matrix
cell verdict, no keeper contact (rules 5/13/22/24/25/28).

THE QUESTION (ercot-211 handback item (ii), chartered by the ercot-218 owner
dispatch). Does replacing the instrument's proxied SOC/AS-position drivers
with the MEASURED per-product AS-responsibility state change its verdict — and
how much of T5's model-free tie-pair violation (storage 95.1 %, max
irreducible error $2,487.50/MWh at ercot-211) survives when
driver-indistinguishability is measured on the TRUE AS state?

THE SWAP (precommit §2 — the ONLY change to the instrument):

* ``x3`` (aggregate ``(HSL−HASL)/HSL`` AS-position proxy) is REPLACED by five
  measured per-product responsibility shares from the NP3-965 corpus's own
  ``Ancillary Service <svc>`` columns (REGUP, RRS, RRSFFR, NSRS, ECRS), each
  MW-weighted over the same segment population. RRSFFR is NOT assumed nested
  in RRS (measured 90.1 % only); the five columns enter verbatim. The ECRS
  column is absent from pre-2023-06 shards because the product did not exist:
  share 0.0, a true zero.
* ``x4`` (``HSL/HSL_ref``) is RETAINED as the telemetered-capability driver.
  Its SOC-proxy role cannot be replaced: measured per-hour ESR SOC exists in
  NO committed corpus for 2023-2025 — the ``60d_DAM_ESR_Data`` family is an
  RTC+B-era addition (first delivery 2025-12-06, after this lane's stop date)
  and carries no SOC column even there (precommit §1, verified).
* Everything else — population discipline, responses, fit/test windows,
  folds, candidate forms, CV selection, T1-T5 bands and counting rules — is
  the ercot-210/211 instrument verbatim.

WHAT IS AND IS NOT READ. Drivers are QUANTITY-ONLY: ``prc`` and ``rtolcap``
from ``ercot_<year>_ordc_reserves_hourly.parquet`` plus telemetered
``HSL``/``HASL``/``LSL`` and the five ``Ancillary Service <svc>`` MW columns
from the NP3-965 corpus. The reserves parquet's price columns
(``system_lambda``, ``rtorpa``, ``rtoffpa``, ``rtordpa``) are NEVER read; no
settlement price, LMP, RTSPP, DAM price, MCPC, model output or scored
criterion enters at any point. Delivery-2023 conduct appears ONLY as the
evaluation target (measured-vs-measured, rule 13). The RTC+B quarantine is
NOT read (non-recursive globs; the lane stops at delivery 2025-12-04) and no
2026-delivery file is opened.

CONSTRUCTIONS ARE IMPORTED, NEVER RE-IMPLEMENTED (the ercot-169/170/210
discipline): ``_sced_source_files`` / ``_delivery_year_rows`` / ``_SCED2_MW``
/ ``_SCED2_PR`` / ``_NUMERIC_COLS`` / ``_weighted_quantiles`` from
``scripts/data/derive_ercot_sced_offer_wall.py``; ``_MONTH_START_HOUR`` from
``scripts/data/derive_ercot_dam_cleared_share.py``; ``SCED_THERMAL_TYPES`` /
``ONLINE_STATES`` from ``scripts/probes/ercot155_dispersion_census.py``; the
above-LSL/HASL segment construction and ONTEST exclusion are the
ERCOT-154/161 population discipline.

Usage::

    python scripts/probes/ercot218_direct_driver_phase0.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data",
           REPO / "scripts" / "probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DEFAULT_OUT = REPO / "results/calibration/ercot218_direct_driver_phase0.json"

# ---------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS — copied VERBATIM from the ercot-210 instrument
# (precommit §4: same thresholds, bands, folds, windows; none may be moved
# after a 2023 row has been read).
# ---------------------------------------------------------------------------

FIT_YEARS: tuple[int, ...] = (2024, 2025)
TEST_YEAR: int = 2023

FIT_TIGHT_MIN: float = 0.90
EVAL_TIGHT_MIN: float = 0.98
T3_BAND: tuple[float, float] = (0.40, 0.60)
T3_RATIO: float = 3.0

ECRS_LIVE_HOY: int = (31 + 28 + 31 + 30 + 31) * 24 + (10 - 1) * 24  # 2023-06-10

SUMMER_MONTHS: frozenset[int] = frozenset({6, 7, 8, 9})

PRICE_FLOOR: float = 1.0
RUNG_500: float = 500.0

T1_REL: float = 0.35
T1_ABS: float = 50.0          # $/MWh
T2_REL: float = 0.40
T2_ABS: float = 0.15          # absolute share
FOLD_MIN_HOURS: int = 10
T1_MIN_FOLDS: int = 5
T1_REQUIRED_MONTHS: tuple[int, ...] = (8, 9)
T4_MIN_FOLDS: int = 5
T5_TAU: float = 0.05
T5_MAX_FAIL_SHARE: float = 0.10

CLASSES: tuple[str, ...] = ("STORAGE", "THERMAL")
HEADLINE: dict[str, str] = {"STORAGE": "p50", "THERMAL": "p90"}

RESERVE_COLS_READ: tuple[str, ...] = ("hour", "prc", "rtolcap")
RESERVE_COLS_REFUSED: tuple[str, ...] = (
    "system_lambda", "rtorpa", "rtoffpa", "rtordpa",
)

# ---------------------------------------------------------------------------
# THE DRIVER SWAP (precommit §2 — the only change vs ercot-210)
# ---------------------------------------------------------------------------

#: The five measured per-product AS-responsibility columns of the NP3-965
#: corpus (its audited 108-column consumer union; the ECRS column is absent
#: from pre-2023-06 shards — the product did not exist, share 0.0).
AS_COLS: dict[str, str] = {
    "x3_regup": "Ancillary Service REGUP",
    "x3_rrs": "Ancillary Service RRS",
    "x3_ffr": "Ancillary Service RRSFFR",
    "x3_nspin": "Ancillary Service NSRS",
    "x3_ecrs": "Ancillary Service ECRS",
}
#: The direct driver vector (T5 ties on all of these, scaled; x5 must match).
DIRECT_DRIVERS: tuple[str, ...] = (
    "x1", "x2", "x3_regup", "x3_rrs", "x3_ffr", "x3_nspin", "x3_ecrs", "x4",
)
#: The ercot-211 proxy vector, reproduced on the same rows for the §4
#: decomposition ONLY (x3_old is never a driver of any fitted form here).
PROXY_DRIVERS: tuple[str, ...] = ("x1", "x2", "x3_old", "x4")


def _imports():
    """The committed constructions, imported verbatim (never re-derived)."""
    from derive_ercot_dam_cleared_share import _MONTH_START_HOUR
    from derive_ercot_sced_offer_wall import (
        _NUMERIC_COLS,
        _SCED2_MW,
        _SCED2_PR,
        _delivery_year_rows,
        _sced_source_files,
        _weighted_quantiles,
    )
    from ercot155_dispersion_census import ONLINE_STATES, SCED_THERMAL_TYPES

    return dict(
        MONTH_START_HOUR=_MONTH_START_HOUR,
        SCED2_MW=_SCED2_MW,
        SCED2_PR=_SCED2_PR,
        NUMERIC_COLS=_NUMERIC_COLS,
        delivery_year_rows=_delivery_year_rows,
        sced_source_files=_sced_source_files,
        weighted_quantiles=_weighted_quantiles,
        ONLINE_STATES=ONLINE_STATES,
        SCED_THERMAL_TYPES=SCED_THERMAL_TYPES,
    )


# ---------------------------------------------------------------------------
# Drivers from committed reserve telemetry (verbatim from ercot-210)
# ---------------------------------------------------------------------------


def hourly_drivers(year: int) -> pd.DataFrame:
    """Per-hour-of-year `x1` (tightness) and `x2` (online capability).

    Within-year percentile ranks, never levels (the ercot-195 V0 failure mode,
    refused by construction — ercot-210 precommit §4.3).
    """
    path = REPO / "data/raw/ercot" / f"ercot_{year}_ordc_reserves_hourly.parquet"
    df = pd.read_parquet(path, columns=list(RESERVE_COLS_READ))
    prc = df["prc"].to_numpy(float)
    cap = df["rtolcap"].to_numpy(float)
    x1 = 1.0 - pd.Series(prc).rank(pct=True).to_numpy()   # high = tight
    x2 = pd.Series(cap).rank(pct=True).to_numpy()
    out = pd.DataFrame(
        {"hoy": df["hour"].to_numpy(int), "x1": x1, "x2": x2, "prc": prc}
    )
    out["valid"] = np.isfinite(prc) & np.isfinite(cap)
    return out


def _hoy_month(hoy: np.ndarray, month_start: np.ndarray) -> np.ndarray:
    """Calendar month of each non-leap hour-of-year index."""
    edges = np.asarray(month_start, dtype=int)
    return np.searchsorted(edges, np.asarray(hoy, dtype=int), side="right")


# ---------------------------------------------------------------------------
# Corpus reads (verbatim from ercot-210 except the five AS columns)
# ---------------------------------------------------------------------------


def _wanted_ordinals(year: int, want_hoy: set[int], msh: np.ndarray) -> set[int]:
    """Calendar ordinals of the delivery days holding a pre-registered hour."""
    out: set[int] = set()
    d = pd.Timestamp(year=year, month=1, day=1)
    end = pd.Timestamp(year=year, month=12, day=31)
    while d <= end:
        if not (d.month == 2 and d.day == 29):
            h0 = int(msh[d.month - 1]) + (d.day - 1) * 24
            if any(h in want_hoy for h in range(h0, h0 + 24)):
                out.add(int(d.toordinal()))
        d += pd.Timedelta(days=1)
    return out


def _shard_days(paths, want_ord: set[int]) -> set[Path]:
    """Cheap first pass: keep only shards carrying a wanted delivery day."""
    keep: set[Path] = set()
    for p in paths:
        try:
            ts = pd.read_parquet(p, columns=["SCED Time Stamp"])["SCED Time Stamp"]
        except Exception:
            continue
        if ts.empty:
            continue
        t = pd.to_datetime(ts, format="%m/%d/%Y %H:%M:%S", errors="coerce").dropna()
        if t.empty:
            continue
        lo, hi = int(t.min().toordinal()), int(t.max().toordinal())
        if any(o in want_ord for o in range(lo, hi + 1)):
            keep.add(p)
    return keep


def hsl_reference(year: int, imp, restypes: tuple[str, ...]) -> pd.Series:
    """Per-resource delivery-year p98 telemetered HSL (`_cap_ref`'s construction)."""
    cols = ["SCED Time Stamp", "Resource Name", "Resource Type", "HSL"]
    acc: dict[str, list[np.ndarray]] = {}
    for p in imp["sced_source_files"](year):
        try:
            df = pd.read_parquet(p, columns=cols)
        except Exception:
            continue
        df = imp["delivery_year_rows"](df, year)
        df = df[df["Resource Type"].isin(restypes)]
        if df.empty:
            continue
        hsl = pd.to_numeric(df["HSL"], errors="coerce").to_numpy(float)
        names = df["Resource Name"].astype(str).to_numpy()
        ok = np.isfinite(hsl) & (hsl > 0)
        if not ok.any():
            continue
        for nm, v in zip(names[ok], hsl[ok]):
            acc.setdefault(nm, []).append(v)
    return pd.Series(
        {k: float(np.percentile(np.asarray(v, float), 98)) for k, v in acc.items()}
    )


def load_segments(
    year: int, imp, want_hoy: set[int], hsl_ref: pd.Series
) -> pd.DataFrame:
    """Above-LSL offer segments capped at HASL for the pre-registered hours.

    The ERCOT-154/161 population discipline, verbatim from ercot-210 — plus
    the five per-segment AS-responsibility MW columns of the swap (precommit
    §2): each segment row inherits its resource-interval's telemetered
    ``Ancillary Service <svc>`` values exactly as it inherits HSL/HASL.
    """
    restypes = ("PWRSTR",) + tuple(imp["SCED_THERMAL_TYPES"])
    online = set(imp["ONLINE_STATES"]) | {"ONTEST"}   # ONTEST kept then dropped
    msh = np.asarray(imp["MONTH_START_HOUR"], dtype=int)
    as_cols = list(AS_COLS.values())
    base_cols = [
        "SCED Time Stamp", "Resource Name", "Resource Type",
        "Telemetered Resource Status", "HSL", "HASL", "LSL",
    ] + [c for pair in zip(imp["SCED2_MW"], imp["SCED2_PR"]) for c in pair]

    paths = imp["sced_source_files"](year)
    keep_shards = _shard_days(paths, _wanted_ordinals(year, want_hoy, msh))

    out: list[pd.DataFrame] = []
    for p in paths:
        if p not in keep_shards:
            continue
        # Pre-2023-06 shards carry no ECRS column (107-column vintage): read
        # what exists; an absent AS column is the product not existing -> 0.0.
        import pyarrow.parquet as _pq
        have = set(_pq.ParquetFile(p).schema_arrow.names)
        read_cols = base_cols + [c for c in as_cols if c in have]
        df = pd.read_parquet(p, columns=[c for c in read_cols])
        df = imp["delivery_year_rows"](df, year)
        if df.empty:
            continue
        df = df[df["Resource Type"].isin(restypes)]
        if df.empty:
            continue
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.isin(online)]
        if df.empty:
            continue
        df = df.assign(status=stat[stat.isin(online)])
        for c in as_cols:
            if c not in df.columns:
                df[c] = 0.0            # product did not exist (true zero)

        ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S",
                            errors="coerce")
        ts_ok = ts.notna()
        df, ts = df[ts_ok], ts[ts_ok]
        if df.empty:
            continue
        cst = (ts.dt.tz_localize("America/Chicago", ambiguous=True,
                                 nonexistent="shift_forward")
                 .dt.tz_convert("Etc/GMT+6"))
        mo, dy, hh = cst.dt.month.to_numpy(), cst.dt.day.to_numpy(), cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))          # model clock is non-leap
        if not ok.any():
            continue
        df = df.loc[np.asarray(ok)].copy()
        hoy = msh[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        sel = np.isin(hoy, list(want_hoy))
        if not sel.any():
            continue
        df = df.loc[sel].copy()
        df["hoy"] = hoy[sel]

        num = [c for c in imp["NUMERIC_COLS"] if c in df.columns] + as_cols
        df[num] = df[num].apply(pd.to_numeric, errors="coerce")

        MW = df[imp["SCED2_MW"]].to_numpy(float)
        PR = df[imp["SCED2_PR"]].to_numpy(float)
        lsl = np.maximum(df["LSL"].to_numpy(float), 0.0)
        hasl = df["HASL"].to_numpy(float)
        hsl = df["HSL"].to_numpy(float)
        cls = np.where(df["Resource Type"].to_numpy() == "PWRSTR",
                       "STORAGE", "THERMAL")
        ref = df["Resource Name"].astype(str).map(hsl_ref).to_numpy(float)
        asr = {k: df[c].to_numpy(float) for k, c in AS_COLS.items()}

        keys = (["hoy", "mw", "price", "cls", "hsl", "hasl", "ref", "status"]
                + list(AS_COLS))
        acc = {k: [] for k in keys}
        prev = lsl.copy()
        for k in range(MW.shape[1]):
            q, pr = MW[:, k], PR[:, k]
            valid = np.isfinite(q) & np.isfinite(pr)
            cap = np.minimum(q, hasl)
            seg = np.where(valid, np.maximum(cap - np.maximum(prev, lsl), 0.0), 0.0)
            take = seg > 0
            if take.any():
                acc["hoy"].append(df["hoy"].to_numpy()[take])
                acc["mw"].append(seg[take])
                acc["price"].append(pr[take])
                acc["cls"].append(cls[take])
                acc["hsl"].append(hsl[take])
                acc["hasl"].append(hasl[take])
                acc["ref"].append(ref[take])
                acc["status"].append(df["status"].to_numpy()[take])
                for a in AS_COLS:
                    acc[a].append(asr[a][take])
            prev = np.where(valid, np.maximum(prev, q), prev)
        if acc["mw"]:
            out.append(pd.DataFrame({k: np.concatenate(v) for k, v in acc.items()}))

    if not out:
        return pd.DataFrame(
            columns=["hoy", "mw", "price", "cls", "hsl", "hasl", "ref", "status"]
            + list(AS_COLS)
        )
    seg = pd.concat(out, ignore_index=True)
    return seg[seg["status"] != "ONTEST"].reset_index(drop=True)   # ERCOT-154


# ---------------------------------------------------------------------------
# Responses and design matrix
# ---------------------------------------------------------------------------


def build_rows(seg: pd.DataFrame, drv: pd.DataFrame, imp, year: int) -> pd.DataFrame:
    """Collapse segments to one (hour, class) row: responses + drivers.

    Verbatim from ercot-210 except the swap: the five per-product shares
    replace the aggregate x3; x3_old (the proxy) is computed alongside for the
    precommit-§4 decomposition only.
    """
    if seg.empty:
        return pd.DataFrame()
    msh = np.asarray(imp["MONTH_START_HOUR"], dtype=int)
    wq = imp["weighted_quantiles"]
    recs = []
    for (hoy, cls), g in seg.groupby(["hoy", "cls"], sort=False):
        pr = g["price"].to_numpy(float)
        mw = g["mw"].to_numpy(float)
        tot = float(mw.sum())
        if tot <= 0:
            continue
        p50, p90 = wq(pr, mw, (0.5, 0.9))
        hsl = g["hsl"].to_numpy(float)
        hasl = g["hasl"].to_numpy(float)
        ref = g["ref"].to_numpy(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            as_share = np.where(hsl > 0, (hsl - hasl) / hsl, np.nan)
            av_share = np.where(np.isfinite(ref) & (ref > 0), hsl / ref, np.nan)
        rec = {
            "year": year,
            "hoy": int(hoy),
            "cls": cls,
            "p50": float(p50),
            "p90": float(p90),
            "s500": float(mw[pr >= RUNG_500].sum() / tot),
            "offered_mw": tot,
            "x3_old": float(np.nansum(as_share * mw) / tot),
            "x4": float(np.nansum(av_share * mw) / tot),
        }
        for a in AS_COLS:
            v = g[a].to_numpy(float)
            with np.errstate(invalid="ignore", divide="ignore"):
                sh = np.where(hsl > 0, v / hsl, np.nan)
            rec[a] = float(np.nansum(sh * mw) / tot)
        recs.append(rec)
    rows = pd.DataFrame(recs)
    if rows.empty:
        return rows
    rows = rows.merge(drv[["hoy", "x1", "x2"]], on="hoy", how="left")
    rows["month"] = _hoy_month(rows["hoy"].to_numpy(), msh)
    rows["x5"] = rows["month"].isin(SUMMER_MONTHS).astype(float)
    rows["day"] = rows["hoy"] // 24
    for c in ("x3_old", "x4", *AS_COLS):
        rows[c] = rows[c].fillna(rows[c].median())
    return rows.dropna(subset=["x1", "x2"]).reset_index(drop=True)


def _design(rows: pd.DataFrame, form: str) -> np.ndarray:
    """Design matrix for one pre-registered candidate form, over the swapped
    driver vector (precommit §2; forms verbatim from ercot-210 §5.4)."""
    x1 = rows["x1"].to_numpy(float)
    rest = [rows[c].to_numpy(float) for c in DIRECT_DRIVERS if c != "x1"]
    rest.append(rows["x5"].to_numpy(float))
    base = [np.ones(len(rows)), x1] + rest
    if form == "linear":
        cols = base
    elif form == "quad":
        cols = base + [x1 ** 2]
    elif form == "logit":
        e = np.clip(x1, 1e-4, 1 - 1e-4)
        cols = [np.ones(len(rows)), np.log(e / (1 - e))] + rest
    else:
        raise ValueError(form)
    return np.column_stack(cols)


def _resp(rows: pd.DataFrame, stat: str, space: str) -> np.ndarray:
    v = rows[stat].to_numpy(float)
    if stat == "s500":
        return v
    return np.log10(np.maximum(v, PRICE_FLOOR)) if space == "log" else v


def _inv(pred: np.ndarray, stat: str, space: str) -> np.ndarray:
    if stat == "s500":
        return np.clip(pred, 0.0, 1.0)
    return 10.0 ** pred if space == "log" else pred


def _wls(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    sw = np.sqrt(np.maximum(w, 0.0))
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return beta


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------


def _within(pred: float, meas: float, rel: float, absf: float) -> bool:
    return abs(pred - meas) <= max(rel * abs(meas), absf)


def _agg(rows: pd.DataFrame, stat: str) -> float:
    """Offered-MW-weighted aggregate of a per-hour statistic over a fold."""
    w = rows["offered_mw"].to_numpy(float)
    v = rows[stat].to_numpy(float)
    return float(np.sum(v * w) / np.sum(w)) if np.sum(w) > 0 else float("nan")


def _tie_test(A: pd.DataFrame, B: pd.DataFrame, stat: str,
              drivers: tuple[str, ...]) -> dict:
    """T5's model-free tie test over an arbitrary scaled driver vector.

    Returns the verbatim counting statistics plus per-B-row tie masks so the
    precommit-§4 proxy-vs-direct decomposition can be computed on identical
    row populations.
    """
    XA = A[list(drivers)].to_numpy(float)
    XB = B[list(drivers)].to_numpy(float)
    yA, yB = A[stat].to_numpy(float), B[stat].to_numpy(float)
    sA, sB = A["x5"].to_numpy(float), B["x5"].to_numpy(float)
    n_pairs = n_bad = 0
    worst = 0.0
    ties: list[np.ndarray] = []
    for j in range(len(XB)):
        tie = (np.max(np.abs(XA - XB[j]), axis=1) <= T5_TAU) & (sA == sB[j])
        ties.append(tie)
        if not tie.any():
            continue
        gaps = np.abs(yA[tie] - yB[j])
        irr = gaps / 2.0
        band = np.maximum(T1_REL * np.abs(yB[j]), T1_ABS)
        n_pairs += int(tie.sum())
        n_bad += int((irr > band).sum())
        worst = max(worst, float(irr.max()))
    share = (n_bad / n_pairs) if n_pairs else None
    return {
        "n_pairs": n_pairs, "n_exceeding_band": n_bad,
        "share_exceeding": (round(share, 4) if share is not None else None),
        "max_irreducible_error": round(worst, 2),
        "ok": bool(n_pairs > 0 and share is not None
                   and share < T5_MAX_FAIL_SHARE),
        "_ties": ties,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    imp = _imports()
    restypes = ("PWRSTR",) + tuple(imp["SCED_THERMAL_TYPES"])

    # ---- drivers + the pre-registered hour sets -------------------------
    drv = {y: hourly_drivers(y) for y in (*FIT_YEARS, TEST_YEAR)}
    want: dict[int, set[int]] = {}
    for y in FIT_YEARS:
        d = drv[y]
        want[y] = set(d.loc[d["valid"] & (d["x1"] >= FIT_TIGHT_MIN), "hoy"].astype(int))
        want[y] |= set(
            d.loc[d["valid"] & d["x1"].between(*T3_BAND), "hoy"].astype(int)
        )
    d = drv[TEST_YEAR]
    want[TEST_YEAR] = set(
        d.loc[d["valid"] & (d["x1"] >= EVAL_TIGHT_MIN), "hoy"].astype(int)
    )

    coverage, rows_by_year = {}, {}
    for y in (*FIT_YEARS, TEST_YEAR):
        ref = hsl_reference(y, imp, restypes)
        seg = load_segments(y, imp, want[y], ref)
        rows = build_rows(seg, drv[y], imp, y)
        rows_by_year[y] = rows
        as_nonnull = {}
        if len(seg):
            pw = seg[seg["cls"] == "STORAGE"]
            for a in AS_COLS:
                as_nonnull[a] = (round(float(pw[a].notna().mean()), 4)
                                 if len(pw) else None)
        coverage[str(y)] = {
            "hours_requested": len(want[y]),
            "hours_with_offer_rows": int(rows["hoy"].nunique()) if len(rows) else 0,
            "n_resources_with_hsl_ref": int(len(ref)),
            "rows_by_class": (
                rows.groupby("cls")["hoy"].nunique().to_dict() if len(rows) else {}
            ),
            "as_responsibility_nonnull_share_storage_segments": as_nonnull,
        }

    fit = pd.concat([rows_by_year[y] for y in FIT_YEARS], ignore_index=True)
    fit_hi = fit[fit["x1"] >= FIT_TIGHT_MIN].reset_index(drop=True)
    test = rows_by_year[TEST_YEAR]

    # ---- candidate selection: 5-fold day-block CV, FIT YEARS ONLY -------
    forms = ("linear", "quad", "logit")
    selected, cv_table = {}, []
    for cls in CLASSES:
        sub = fit_hi[fit_hi["cls"] == cls].reset_index(drop=True)
        for stat in ("p50", "p90", "s500"):
            best = None
            for form in forms:
                for space in (("log", "level") if stat != "s500" else ("level",)):
                    errs = []
                    days = np.sort(sub["day"].unique())
                    blocks = np.array_split(days, 5) if len(days) >= 5 else [days]
                    for b in blocks:
                        tr = sub[~sub["day"].isin(b)]
                        te = sub[sub["day"].isin(b)]
                        if len(tr) < 20 or te.empty:
                            continue
                        beta = _wls(_design(tr, form), _resp(tr, stat, space),
                                    tr["offered_mw"].to_numpy(float))
                        pr = _inv(_design(te, form) @ beta, stat, space)
                        errs.append(float(np.average(
                            np.abs(pr - te[stat].to_numpy(float)),
                            weights=te["offered_mw"].to_numpy(float))))
                    if not errs:
                        continue
                    score = float(np.mean(errs))
                    cv_table.append({"cls": cls, "stat": stat, "form": form,
                                     "space": space, "cv_mae": round(score, 5)})
                    if best is None or score < best[0]:
                        best = (score, form, space)
            if best:
                selected[f"{cls}:{stat}"] = {"form": best[1], "space": best[2],
                                             "cv_mae": round(best[0], 5)}

    # ---- fit the frozen forms on ALL fit-year hours ---------------------
    coef = {}
    for cls in CLASSES:
        sub = fit_hi[fit_hi["cls"] == cls]
        for stat in ("p50", "p90", "s500"):
            key = f"{cls}:{stat}"
            if key not in selected or sub.empty:
                continue
            f, sp = selected[key]["form"], selected[key]["space"]
            coef[key] = _wls(_design(sub, f), _resp(sub, stat, sp),
                             sub["offered_mw"].to_numpy(float))

    def predict(key: str, rows: pd.DataFrame) -> np.ndarray:
        stat = key.split(":")[1]
        s = selected[key]
        return _inv(_design(rows, s["form"]) @ coef[key], stat, s["space"])

    # ---- T1 / T2: out-of-year transfer, LOYO across 2023 months ---------
    def fold_table(target: pd.DataFrame, cls: str, stat: str, rel: float,
                   absf: float, months: list[int], tight_min: float) -> dict:
        key = f"{cls}:{stat}"
        sub = target[(target["cls"] == cls) & (target["x1"] >= tight_min)]
        folds, adm, passed = [], 0, 0
        for m in months:
            g = sub[sub["month"] == m]
            n = int(g["hoy"].nunique())
            if n == 0:
                folds.append({"month": m, "n_hours": 0, "admissible": False})
                continue
            meas = _agg(g, stat)
            pred = float(np.average(predict(key, g),
                                    weights=g["offered_mw"].to_numpy(float)))
            adm_f = n >= FOLD_MIN_HOURS
            ok = _within(pred, meas, rel, absf)
            adm += int(adm_f)
            passed += int(adm_f and ok)
            folds.append({
                "month": m, "n_hours": n, "admissible": adm_f,
                "measured": round(meas, 4), "predicted": round(pred, 4),
                "abs_err": round(abs(pred - meas), 4),
                "rel_err": (round((pred - meas) / meas, 4) if meas else None),
                "within_band": bool(ok),
            })
        return {"folds": folds, "n_admissible": adm, "n_pass": passed}

    post = test[test["hoy"] >= ECRS_LIVE_HOY]
    pre = test[test["hoy"] < ECRS_LIVE_HOY]
    months_post = list(range(6, 13))

    t1, t2 = {}, {}
    for cls in CLASSES:
        t1[cls] = fold_table(post, cls, HEADLINE[cls], T1_REL, T1_ABS,
                             months_post, EVAL_TIGHT_MIN)
        t2[cls] = fold_table(post, cls, "s500", T2_REL, T2_ABS,
                             months_post, EVAL_TIGHT_MIN)

    def gate_ok(tbl: dict) -> bool:
        by_m = {f["month"]: f for f in tbl["folds"]}
        req = all(by_m.get(m, {}).get("admissible") and by_m[m]["within_band"]
                  for m in T1_REQUIRED_MONTHS)
        return bool(tbl["n_pass"] >= T1_MIN_FOLDS and req)

    T1_PASS = all(gate_ok(t1[c]) for c in CLASSES)
    T2_PASS = all(gate_ok(t2[c]) for c in CLASSES)

    # ---- T3: non-degeneracy, FIT YEARS ONLY -----------------------------
    t3 = {}
    for cls in CLASSES:
        key = f"{cls}:{HEADLINE[cls]}"
        hi = fit[(fit["cls"] == cls) & (fit["x1"] >= EVAL_TIGHT_MIN)]
        lo = fit[(fit["cls"] == cls) & fit["x1"].between(*T3_BAND)]
        if hi.empty or lo.empty or key not in coef:
            t3[cls] = {"ok": False, "reason": "empty band"}
            continue
        ph = float(np.average(predict(key, hi),
                              weights=hi["offered_mw"].to_numpy(float)))
        pl = float(np.average(predict(key, lo),
                              weights=lo["offered_mw"].to_numpy(float)))
        t3[cls] = {"pred_tight": round(ph, 3), "pred_mid": round(pl, 3),
                   "ratio": round(ph / pl, 3) if pl else None,
                   "n_tight": len(hi), "n_mid": len(lo),
                   "ok": bool(pl > 0 and ph / pl >= T3_RATIO)}
    T3_PASS = all(v.get("ok") for v in t3.values())

    # ---- T4: within-regime control, fit 2024 -> predict 2025 ------------
    f24 = rows_by_year[2024]
    f24 = f24[f24["x1"] >= FIT_TIGHT_MIN]
    coef24, t4 = {}, {}
    for cls in CLASSES:
        sub = f24[f24["cls"] == cls]
        key = f"{cls}:{HEADLINE[cls]}"
        if sub.empty or key not in selected:
            t4[cls] = {"n_admissible": 0, "n_pass": 0, "folds": []}
            continue
        s = selected[key]
        coef24[key] = _wls(_design(sub, s["form"]),
                           _resp(sub, HEADLINE[cls], s["space"]),
                           sub["offered_mw"].to_numpy(float))

    def predict24(key: str, rows: pd.DataFrame) -> np.ndarray:
        s = selected[key]
        return _inv(_design(rows, s["form"]) @ coef24[key],
                    key.split(":")[1], s["space"])

    tgt25 = rows_by_year[2025]
    for cls in CLASSES:
        key = f"{cls}:{HEADLINE[cls]}"
        if key not in coef24:
            continue
        sub = tgt25[(tgt25["cls"] == cls) & (tgt25["x1"] >= EVAL_TIGHT_MIN)]
        folds, adm, passed = [], 0, 0
        for m in range(1, 13):
            g = sub[sub["month"] == m]
            n = int(g["hoy"].nunique())
            if n == 0:
                continue
            meas = _agg(g, HEADLINE[cls])
            pred = float(np.average(predict24(key, g),
                                    weights=g["offered_mw"].to_numpy(float)))
            adm_f = n >= FOLD_MIN_HOURS
            ok = _within(pred, meas, T1_REL, T1_ABS)
            adm += int(adm_f)
            passed += int(adm_f and ok)
            folds.append({"month": m, "n_hours": n, "admissible": adm_f,
                          "measured": round(meas, 4), "predicted": round(pred, 4),
                          "rel_err": (round((pred - meas) / meas, 4) if meas else None),
                          "within_band": bool(ok)})
        t4[cls] = {"folds": folds, "n_admissible": adm, "n_pass": passed}
    T4_PASS = all(t4.get(c, {}).get("n_pass", 0) >= T4_MIN_FOLDS for c in CLASSES)

    # ---- T5: model-free tie test — DIRECT vector gates; PROXY vector and
    # the survival decomposition reported (precommit §4) ------------------
    t5, t5_proxy, t5_decomp = {}, {}, {}
    for cls in CLASSES:
        stat = HEADLINE[cls]
        A = fit_hi[fit_hi["cls"] == cls].reset_index(drop=True)
        B = post[(post["cls"] == cls)
                 & (post["x1"] >= EVAL_TIGHT_MIN)].reset_index(drop=True)
        if A.empty or B.empty:
            t5[cls] = {"n_pairs": 0, "ok": False, "reason": "empty side"}
            t5_proxy[cls] = {"n_pairs": 0, "reason": "empty side"}
            t5_decomp[cls] = None
            continue
        direct = _tie_test(A, B, stat, DIRECT_DRIVERS)
        proxy = _tie_test(A, B, stat, PROXY_DRIVERS)

        # Survival decomposition on identical row populations: of the pairs
        # tied under the PROXY drivers (ercot-211's construction), which stay
        # tied when indistinguishability is measured on the TRUE AS state?
        yA, yB = A[stat].to_numpy(float), B[stat].to_numpy(float)
        n_p = n_pv = n_surv = n_surv_v = n_surv_bad = 0
        worst_surv = 0.0
        for j in range(len(B)):
            tp, td = proxy["_ties"][j], direct["_ties"][j]
            if not tp.any():
                continue
            band = max(T1_REL * abs(yB[j]), T1_ABS)
            irr = np.abs(yA[tp] - yB[j]) / 2.0
            viol = irr > band
            surv = td[tp]                      # proxy-tied pairs still tied
            n_p += int(tp.sum())
            n_pv += int(viol.sum())
            n_surv += int(surv.sum())
            n_surv_v += int((viol & surv).sum())
            if (viol & surv).any():
                n_surv_bad += 1
                worst_surv = max(worst_surv, float(irr[viol & surv].max()))
        t5_decomp[cls] = {
            "proxy_tied_pairs": n_p,
            "proxy_violating_pairs": n_pv,
            "proxy_pairs_still_tied_on_direct": n_surv,
            "share_of_proxy_ties_broken_by_direct": (
                round(1.0 - n_surv / n_p, 4) if n_p else None),
            "violating_pairs_still_tied_on_direct": n_surv_v,
            "share_of_violation_surviving_direct": (
                round(n_surv_v / n_pv, 4) if n_pv else None),
            "max_irreducible_error_among_surviving": round(worst_surv, 2),
        }
        direct.pop("_ties")
        proxy.pop("_ties")
        t5[cls] = direct
        t5_proxy[cls] = proxy
    T5_PASS = all(v.get("ok") for v in t5.values())

    verdict = ("TRANSFERABLE" if all([T1_PASS, T2_PASS, T3_PASS, T4_PASS, T5_PASS])
               else "NOT-TRANSFERABLE")

    # ---- reported-not-gating contrasts (verbatim from ercot-210) --------
    contrast = {}
    for cls in CLASSES:
        key = f"{cls}:{HEADLINE[cls]}"
        for label, g in (("pre_ecrs_2023", pre[(pre["cls"] == cls)
                                               & (pre["x1"] >= EVAL_TIGHT_MIN)]),
                         ("post_ecrs_2023_summer",
                          post[(post["cls"] == cls) & (post["x5"] == 1.0)
                               & (post["x1"] >= EVAL_TIGHT_MIN)])):
            if g.empty or key not in coef:
                contrast[f"{cls}:{label}"] = None
                continue
            meas = _agg(g, HEADLINE[cls])
            pred = float(np.average(predict(key, g),
                                    weights=g["offered_mw"].to_numpy(float)))
            contrast[f"{cls}:{label}"] = {
                "n_hours": int(g["hoy"].nunique()),
                "measured": round(meas, 3), "predicted": round(pred, 3),
                "rel_err": (round((pred - meas) / meas, 4) if meas else None),
            }

    # ---- the relaxed-fold diagnostic (re-reported, gating nothing) ------
    relaxed = {}
    saved = globals()["FOLD_MIN_HOURS"]
    try:
        globals()["FOLD_MIN_HOURS"] = 1
        for cls in CLASSES:
            relaxed[f"{cls}:T1"] = fold_table(post, cls, HEADLINE[cls], T1_REL,
                                              T1_ABS, months_post, EVAL_TIGHT_MIN)
            relaxed[f"{cls}:T2"] = fold_table(post, cls, "s500", T2_REL, T2_ABS,
                                              months_post, EVAL_TIGHT_MIN)
    finally:
        globals()["FOLD_MIN_HOURS"] = saved

    # ---- the direct AS-state at the eval cut, per year (context) --------
    as_state = {}
    for y in (*FIT_YEARS, TEST_YEAR):
        r = rows_by_year[y]
        g = r[(r["cls"] == "STORAGE") & (r["x1"] >= EVAL_TIGHT_MIN)]
        if g.empty:
            as_state[str(y)] = None
            continue
        as_state[str(y)] = {
            "n_hours": int(g["hoy"].nunique()),
            **{a: round(float(g[a].mean()), 4) for a in
               (*AS_COLS, "x3_old", "x4")},
        }

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot218_direct_driver_phase0.py",
            "session": "ercot-218 DIRECT-DRIVER PHASE-0 (no LP, no solve)",
            "precommit": "docs/PRECOMMIT-ercot218-direct-driver-phase0-2026-08-17.md",
            "charter": "the ercot-218 owner dispatch (the owner card for "
                       "ercot-211 handback item (ii))",
            "keeper_at_run": "2026-08-17-ercot215-arm-decontam",
            "instrument": "ercot-210/211 verbatim except the driver swap "
                          "(precommit §2)",
            "reserve_columns_read": list(RESERVE_COLS_READ),
            "reserve_columns_refused": list(RESERVE_COLS_REFUSED),
            "as_responsibility_columns_read": AS_COLS,
            "no_price_series_read": True,
            "rtcb_quarantine_read": False,
            "dam_esr_file_read": False,
            "esr_data_family_note": (
                "60d_DAM_ESR_Data is an RTC+B-era artifact (first delivery "
                "2025-12-06, after this lane's 2025-12-04 stop) and carries "
                "no SOC column; measured ESR SOC exists in no committed "
                "corpus for 2023-2025 (precommit §1). The SOC coordinate of "
                "the direct driver set is therefore honestly ABSENT; x4 "
                "remains the telemetered-capability driver."
            ),
        },
        "design": {
            "fit_years": list(FIT_YEARS), "test_year": TEST_YEAR,
            "fit_tight_min": FIT_TIGHT_MIN, "eval_tight_min": EVAL_TIGHT_MIN,
            "ecrs_live_hoy": ECRS_LIVE_HOY,
            "headline_statistic": HEADLINE,
            "direct_drivers": list(DIRECT_DRIVERS),
            "proxy_drivers_decomposition_only": list(PROXY_DRIVERS),
            "thresholds": {
                "T1": {"rel": T1_REL, "abs_usd": T1_ABS,
                       "min_folds": T1_MIN_FOLDS,
                       "required_months": list(T1_REQUIRED_MONTHS)},
                "T2": {"rel": T2_REL, "abs_share": T2_ABS},
                "T3": {"ratio": T3_RATIO, "band": list(T3_BAND)},
                "T4": {"min_folds": T4_MIN_FOLDS},
                "T5": {"tau": T5_TAU, "max_fail_share": T5_MAX_FAIL_SHARE},
            },
        },
        "coverage": coverage,
        "candidate_selection_fit_years_only": {
            "selected": selected, "cv_table": cv_table,
        },
        "T1_out_of_year_headline": {"pass": T1_PASS, "by_class": t1},
        "T2_share_ge_500": {"pass": T2_PASS, "by_class": t2},
        "T3_non_degeneracy_fit_years": {"pass": T3_PASS, "by_class": t3},
        "T4_within_regime_control_2024_to_2025": {"pass": T4_PASS, "by_class": t4},
        "T5_model_free_tie_test_DIRECT": {"pass": T5_PASS, "by_class": t5},
        "T5_proxy_reproduction": t5_proxy,
        "T5_direct_vs_proxy_decomposition": t5_decomp,
        "VERDICT": verdict,
        "reported_not_gating": contrast,
        "post_hoc_diagnostics": {
            "_note": ("Gates nothing; the relaxed-fold table re-reports the "
                      "ercot-211 §3.2 diagnostic on this run's rows."),
            "t1_t2_with_fold_min_hours_relaxed_to_1": relaxed,
            "storage_direct_as_state_at_eval_cut": as_state,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"VERDICT: {verdict}")
    for k, v in (("T1", T1_PASS), ("T2", T2_PASS), ("T3", T3_PASS),
                 ("T4", T4_PASS), ("T5", T5_PASS)):
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    for cls in CLASSES:
        print(f"  T5 {cls}: direct={t5[cls].get('share_exceeding')} "
              f"proxy={t5_proxy[cls].get('share_exceeding')} "
              f"decomp={t5_decomp.get(cls)}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
