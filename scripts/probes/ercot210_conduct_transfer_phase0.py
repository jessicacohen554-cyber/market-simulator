#!/usr/bin/env python
"""ercot-210 CONDUCT-PHASE-0 — the out-of-year conduct-transfer identifiability test.

Pre-registered in ``docs/PRECOMMIT-ercot210-conduct-transfer-phase0-2026-08-16.md``
and executed exactly as written there. **Read-only**: no LP, no solve, no year
scored, no run registered, no ``ScenarioConfig`` field, no mechanism-matrix
edit, no keeper contact (rules 5/13/22/24/25/28; the ercot-182/189/196/200
card-is-a-read precedent).

THE QUESTION (ASSESSMENT-ercot209 §3, Door A). Are ERCOT scarcity-hour offer
surfaces -- storage foremost, thermal top-of-stack alongside -- expressible as a
function of forward-computable drivers (tightness/PRC percentile; SOC/AS
position for storage) such that a function fit ONLY on delivery-2024/2025 60-day
disclosures reproduces the delivery-2023 scarcity-hour surfaces at matched
tightness?

WHAT IS AND IS NOT READ. The drivers are QUANTITY-ONLY by construction: ``prc``
and ``rtolcap`` from ``ercot_<year>_ordc_reserves_hourly.parquet`` plus
telemetered ``HSL``/``HASL``/``LSL`` from the NP3-965 corpus. The price columns
of the reserves parquet (``system_lambda``, ``rtorpa``, ``rtoffpa``,
``rtordpa``) are NEVER read -- that is the rule-19/13 line the published-RTORPA
overlay crossed (ercot-204 §A / ercot-203b), and the read set is written into
the output JSON so the claim is auditable rather than asserted. No settlement
price, no LMP, no RTSPP, no model output and no scored criterion enters at any
point; delivery-2023 conduct appears ONLY as the evaluation target
(measured-vs-measured, rule 13).

CONSTRUCTIONS ARE IMPORTED, NEVER RE-IMPLEMENTED -- the ercot-169/170 discipline,
so this session's numbers stay comparable to the record they must bridge:

* ``_sced_source_files`` / ``_delivery_year_rows`` / ``_SCED2_MW`` / ``_SCED2_PR``
  / ``_NUMERIC_COLS`` / ``_weighted_quantiles`` from
  ``scripts/data/derive_ercot_sced_offer_wall.py``;
* ``_MONTH_START_HOUR`` from ``scripts/data/derive_ercot_dam_cleared_share.py``;
* ``SCED_THERMAL_TYPES`` / ``ONLINE_STATES`` from
  ``scripts/probes/ercot155_dispersion_census.py``;
* the above-LSL/HASL segment construction and the ONTEST exclusion are the
  ERCOT-154/161 population discipline (``ercot161_pwrstr_conduct_census``).

The RTC+B quarantine (``data/raw/ercot/SCED/rtcb-format-2026/``) is NOT read:
the corpus glob stays non-recursive and this lane stops at delivery 2025-12-04,
exactly as ``sced_corpus_instruments`` pins it.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/ercot210_conduct_transfer_phase0.py
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

DEFAULT_OUT = REPO / "results/calibration/ercot210_conduct_transfer_phase0.json"

# ---------------------------------------------------------------------------
# PRE-REGISTERED CONSTANTS (precommit §5-§7). None of these is fitted, and none
# may be moved after a 2023 row has been read.
# ---------------------------------------------------------------------------

FIT_YEARS: tuple[int, ...] = (2024, 2025)
TEST_YEAR: int = 2023

#: Fit population: tightest 10 % of each fit year (precommit §6.1).
FIT_TIGHT_MIN: float = 0.90
#: Transfer target: tightest 2 %, matched tightness (precommit §6.2).
EVAL_TIGHT_MIN: float = 0.98
#: Non-degeneracy contrast band for T3 (precommit §7).
T3_BAND: tuple[float, float] = (0.40, 0.60)
T3_RATIO: float = 3.0

#: ECRS go-live. Primary 2023 evaluation is post-ECRS only (precommit §6.2/§6.4).
ECRS_LIVE_HOY: int = (31 + 28 + 31 + 30 + 31) * 24 + (10 - 1) * 24  # 2023-06-10 00:00

#: Summer indicator months (driver x5).
SUMMER_MONTHS: frozenset[int] = frozenset({6, 7, 8, 9})

#: Offer-price floor before log10 (precommit §5.2).
PRICE_FLOOR: float = 1.0
#: The $/MWh rung defining the `s500` share response.
RUNG_500: float = 500.0

#: T1/T2 bands (precommit §7). T1's 35 % is tied to the C3a-2023 miss (-33.2 %).
T1_REL: float = 0.35
T1_ABS: float = 50.0          # $/MWh
T2_REL: float = 0.40
T2_ABS: float = 0.15          # absolute share
#: Monthly fold admissibility and the counting rule.
FOLD_MIN_HOURS: int = 10
T1_MIN_FOLDS: int = 5
T1_REQUIRED_MONTHS: tuple[int, ...] = (8, 9)   # Aug/Sep 2023 carry 96.2 % of C3b
T4_MIN_FOLDS: int = 5
#: T5 model-free tie test (V0 §4's own construction at hour grain).
T5_TAU: float = 0.05
T5_MAX_FAIL_SHARE: float = 0.10

CLASSES: tuple[str, ...] = ("STORAGE", "THERMAL")
#: Class headline statistic that T1 binds (precommit §5.2).
HEADLINE: dict[str, str] = {"STORAGE": "p50", "THERMAL": "p90"}

#: Reserve-telemetry columns this probe reads. The price columns of the same
#: parquet are deliberately absent -- see the module docstring.
RESERVE_COLS_READ: tuple[str, ...] = ("hour", "prc", "rtolcap")
RESERVE_COLS_REFUSED: tuple[str, ...] = (
    "system_lambda", "rtorpa", "rtoffpa", "rtordpa",
)


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
# Drivers from committed reserve telemetry
# ---------------------------------------------------------------------------


def hourly_drivers(year: int) -> pd.DataFrame:
    """Per-hour-of-year `x1` (tightness) and `x2` (online capability).

    Both are WITHIN-YEAR percentile ranks, never levels: measured `prc` p50
    rises 6,750 -> 9,039 -> 11,055 MW across 2023 -> 2025, so a level-conditioned
    variable would measure the fleet rather than conduct (precommit §4.3 -- the
    ercot-195 V0 failure mode, refused here by construction).
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
# Corpus reads
# ---------------------------------------------------------------------------


def _wanted_ordinals(year: int, want_hoy: set[int], msh: np.ndarray) -> set[int]:
    """Calendar ordinals of the delivery days holding a pre-registered hour.

    The model clock is non-leap, so Feb 29 carries no hour-of-year and is never
    wanted; every other real date maps to its 24-hour block.
    """
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
    """Cheap first pass: keep only shards carrying a wanted delivery day.

    Reads ONE column per shard. The shard set follows MECHANICALLY from the
    precommit's hour rule -- it is never chosen by looking at conduct.
    """
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
    """Per-resource delivery-year p98 telemetered HSL (`_cap_ref`'s construction).

    Taken over the FULL delivery year, not over the scarcity subset, so `x4` is
    a genuine availability fraction rather than a scarcity-conditioned one.
    """
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

    The ERCOT-154/161 population discipline: telemetered-ONLINE only, ONTEST
    excluded, segment MW = min(cum_MW, HASL) - max(prev, LSL), prices in
    ABSOLUTE $/MWh (the gas-multiple basis is refuted for storage -- a battery
    has no heat rate).
    """
    restypes = ("PWRSTR",) + tuple(imp["SCED_THERMAL_TYPES"])
    online = set(imp["ONLINE_STATES"]) | {"ONTEST"}   # ONTEST kept then dropped
    msh = np.asarray(imp["MONTH_START_HOUR"], dtype=int)
    read_cols = [
        "SCED Time Stamp", "Resource Name", "Resource Type",
        "Telemetered Resource Status", "HSL", "HASL", "LSL",
    ] + [c for pair in zip(imp["SCED2_MW"], imp["SCED2_PR"]) for c in pair]

    paths = imp["sced_source_files"](year)
    keep = _shard_days(paths, _wanted_ordinals(year, want_hoy, msh))

    out: list[pd.DataFrame] = []
    for p in paths:
        if p not in keep:
            continue
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

        ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S",
                            errors="coerce")
        keep = ts.notna()
        df, ts = df[keep], ts[keep]
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

        num = [c for c in imp["NUMERIC_COLS"] if c in df.columns]
        df[num] = df[num].apply(pd.to_numeric, errors="coerce")

        MW = df[imp["SCED2_MW"]].to_numpy(float)
        PR = df[imp["SCED2_PR"]].to_numpy(float)
        lsl = np.maximum(df["LSL"].to_numpy(float), 0.0)
        hasl = df["HASL"].to_numpy(float)
        hsl = df["HSL"].to_numpy(float)
        cls = np.where(df["Resource Type"].to_numpy() == "PWRSTR",
                       "STORAGE", "THERMAL")
        ref = df["Resource Name"].astype(str).map(hsl_ref).to_numpy(float)

        acc = {k: [] for k in ("hoy", "mw", "price", "cls", "hsl", "hasl", "ref",
                               "status")}
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
            prev = np.where(valid, np.maximum(prev, q), prev)
        if acc["mw"]:
            out.append(pd.DataFrame({k: np.concatenate(v) for k, v in acc.items()}))

    if not out:
        return pd.DataFrame(
            columns=["hoy", "mw", "price", "cls", "hsl", "hasl", "ref", "status"]
        )
    seg = pd.concat(out, ignore_index=True)
    return seg[seg["status"] != "ONTEST"].reset_index(drop=True)   # ERCOT-154


# ---------------------------------------------------------------------------
# Responses and design matrix
# ---------------------------------------------------------------------------


def build_rows(seg: pd.DataFrame, drv: pd.DataFrame, imp, year: int) -> pd.DataFrame:
    """Collapse segments to one (hour, class) row: responses + drivers."""
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
        recs.append(
            {
                "year": year,
                "hoy": int(hoy),
                "cls": cls,
                "p50": float(p50),
                "p90": float(p90),
                "s500": float(mw[pr >= RUNG_500].sum() / tot),
                "offered_mw": tot,
                "x3": float(np.nansum(as_share * mw) / tot),
                "x4": float(np.nansum(av_share * mw) / tot),
            }
        )
    rows = pd.DataFrame(recs)
    if rows.empty:
        return rows
    rows = rows.merge(drv[["hoy", "x1", "x2"]], on="hoy", how="left")
    rows["month"] = _hoy_month(rows["hoy"].to_numpy(), msh)
    rows["x5"] = rows["month"].isin(SUMMER_MONTHS).astype(float)
    rows["day"] = rows["hoy"] // 24
    for c in ("x3", "x4"):
        rows[c] = rows[c].fillna(rows[c].median())
    return rows.dropna(subset=["x1", "x2"]).reset_index(drop=True)


def _design(rows: pd.DataFrame, form: str) -> np.ndarray:
    """Design matrix for one pre-registered candidate form (precommit §5.4)."""
    x1 = rows["x1"].to_numpy(float)
    base = [np.ones(len(rows)), x1, rows["x2"].to_numpy(float),
            rows["x3"].to_numpy(float), rows["x4"].to_numpy(float),
            rows["x5"].to_numpy(float)]
    if form == "linear":
        cols = base
    elif form == "quad":
        cols = base + [x1 ** 2]
    elif form == "logit":
        e = np.clip(x1, 1e-4, 1 - 1e-4)
        cols = [np.ones(len(rows)), np.log(e / (1 - e))] + base[2:]
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
        # T3's contrast band is a FIT-YEAR read, so its hours load with the fit.
        want[y] |= set(
            d.loc[d["valid"] & d["x1"].between(*T3_BAND), "hoy"].astype(int)
        )
        # T4 evaluates 2025 at the eval cut; already inside the >=0.90 set.
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
        coverage[str(y)] = {
            "hours_requested": len(want[y]),
            "hours_with_offer_rows": int(rows["hoy"].nunique()) if len(rows) else 0,
            "n_resources_with_hsl_ref": int(len(ref)),
            "rows_by_class": (
                rows.groupby("cls")["hoy"].nunique().to_dict() if len(rows) else {}
            ),
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

    # ---- T5: model-free tie test (V0 §4 at hour grain) ------------------
    t5 = {}
    for cls in CLASSES:
        stat = HEADLINE[cls]
        A = fit_hi[fit_hi["cls"] == cls]
        B = post[(post["cls"] == cls) & (post["x1"] >= EVAL_TIGHT_MIN)]
        if A.empty or B.empty:
            t5[cls] = {"n_pairs": 0, "ok": False, "reason": "empty side"}
            continue
        cols = ["x1", "x2", "x3", "x4"]
        XA, XB = A[cols].to_numpy(float), B[cols].to_numpy(float)
        yA = A[stat].to_numpy(float)
        yB = B[stat].to_numpy(float)
        sA, sB = A["x5"].to_numpy(float), B["x5"].to_numpy(float)
        n_pairs = n_bad = 0
        worst = 0.0
        for j in range(len(XB)):
            tie = (np.max(np.abs(XA - XB[j]), axis=1) <= T5_TAU) & (sA == sB[j])
            if not tie.any():
                continue
            gaps = np.abs(yA[tie] - yB[j])
            irr = gaps / 2.0
            band = np.maximum(T1_REL * np.abs(yB[j]), T1_ABS)
            n_pairs += int(tie.sum())
            n_bad += int((irr > band).sum())
            worst = max(worst, float(irr.max()))
        share = (n_bad / n_pairs) if n_pairs else None
        t5[cls] = {"n_pairs": n_pairs, "n_exceeding_band": n_bad,
                   "share_exceeding": (round(share, 4) if share is not None else None),
                   "max_irreducible_error": round(worst, 2),
                   "ok": bool(n_pairs > 0 and share is not None
                              and share < T5_MAX_FAIL_SHARE)}
    T5_PASS = all(v.get("ok") for v in t5.values())

    verdict = ("TRANSFERABLE" if all([T1_PASS, T2_PASS, T3_PASS, T4_PASS, T5_PASS])
               else "NOT-TRANSFERABLE")

    # ---- reported-not-gating contrasts ---------------------------------
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

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot210_conduct_transfer_phase0.py",
            "session": "ercot-210 CONDUCT-PHASE-0 (Door A Phase-0; no LP, no solve)",
            "precommit": "docs/PRECOMMIT-ercot210-conduct-transfer-phase0-2026-08-16.md",
            "charter": "X-1 (owner), ASSESSMENT-ercot209 §3 Door A",
            "keeper_at_run": "2026-08-15-ercot204-rule26-delete",
            "reserve_columns_read": list(RESERVE_COLS_READ),
            "reserve_columns_refused": list(RESERVE_COLS_REFUSED),
            "no_price_series_read": True,
            "rtcb_quarantine_read": False,
        },
        "design": {
            "fit_years": list(FIT_YEARS), "test_year": TEST_YEAR,
            "fit_tight_min": FIT_TIGHT_MIN, "eval_tight_min": EVAL_TIGHT_MIN,
            "ecrs_live_hoy": ECRS_LIVE_HOY,
            "headline_statistic": HEADLINE,
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
        "T5_model_free_tie_test": {"pass": T5_PASS, "by_class": t5},
        "VERDICT": verdict,
        "reported_not_gating": contrast,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"VERDICT: {verdict}")
    for k, v in (("T1", T1_PASS), ("T2", T2_PASS), ("T3", T3_PASS),
                 ("T4", T4_PASS), ("T5", T5_PASS)):
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
