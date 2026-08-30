"""ercot-241 Phase-0: MEASURED CONDUCT-PARAMETERIZATION screen on the off-core object.

ZERO-SOLVE, measurement only, per
``docs/PRECOMMIT-ercot241-offcore-conduct-phase0-2026-08-30.md`` (pushed and
blob-verified before this probe ran). Executes ercot-239 §6 OBJECT 1: does
ERCOT's 60-Day SCED energy-offer conduct shift with measured reserve ROOM at
the 12 off-core missed-event hours (the 11-hour conduct core + h2058) vs
driver-matched controls, and does that dependence identify a zero-fitted-scalar
parameterization?

All constructions are the precommit's §2 declarations, byte-identical to their
cited sources:

* population/V-0 series: ``ercot239_missedevents_phase0._series`` (imported);
* SCED corpus access: ``derive_ercot_sced_offer_wall`` helpers (imported) —
  SCED2 curves only (SCED1 was dropped by the BLOAT-B-1 slim);
* CPT→CST hour-of-year: the ``ercot161_price_setter_census`` clock (verbatim);
* census slices (above-LSL) and spare slices (Base Point→HASL): the ercot-161
  and ``_spare_segments`` walks respectively;
* measured room: ``rtolcap`` year-fraction-≤ percentile (NaN-dropped);
* net-load percentile: ``derive_ercot_dam_cleared_share._netload_pct`` (the
  armed wall's own conditioning variable);
* HR-multiple: price / delivered-gas day (``_gas_day_series``), $ clipped to
  HCAP — the armed wall's own convention.

Measurements M-1..M-5, declared priors P1–P5, kills K-1..K-3 and the Phase-1
gate are all fixed in the precommit §2–§4; this probe computes them and writes
``results/calibration/ercot241_offcore_conduct_phase0.json``. Grading happens
in the FINDING, never here.

Run (~15 min, streams the 2023 delivery corpus shard by shard)::

    PYTHONPATH=.:src python3 scripts/probes/ercot241_offcore_conduct_phase0.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data",
           REPO / "scripts" / "probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    LADDER_QUANTILES,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)
from derive_ercot_sced_offer_wall import (  # noqa: E402
    CLASS_OF_RESTYPE,
    _READ_COLS,
    _SCED2_MW,
    _SCED2_PR,
    _coerce_sced_numeric,
    _delivery_year_rows,
    _sced_source_files,
    _spare_segments,
)
from ercot239_missedevents_phase0 import _series  # noqa: E402

MEASURED_ORDC = REPO / "data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet"
ERCOT239_JSON = REPO / "results/calibration/ercot239_missedevents_phase0.json"
K33_RUN_CONFIG = REPO / "results/calibration/ercot236_k33_clip/run_config.json"
OUT_JSON = REPO / "results/calibration/ercot241_offcore_conduct_phase0.json"

YEAR = 2023

#: V-0 identity expectation — the committed 14-hour family (precommit §1).
FAMILY_HOURS = sorted(
    [2058, 2971, 4578, 4623, 4626, 5369, 5484, 5777, 5943, 5945, 6399, 7001,
     7145, 7480]
)
#: Queued wind pair, excluded from the object set (ercot-239 §4 sub-pop 2).
WIND_PAIR = (6399, 7145)
#: The 12-hour OBJECT SET (11-hour conduct core + h2058).
OBJECT_HOURS = [h for h in FAMILY_HOURS if h not in WIND_PAIR]

#: Committed armed-wall net-load bin per object hour (precommit §1, from the
#: ercot-239 ``net_load_pctl_year`` record on edges 0.25/0.50/0.70/0.80/0.90/
#: 0.97). NOTE: the full-year M-4 surface and control matching run on
#: ``_netload_pct`` (rank), which lands 5 of the 12 in the adjacent lower bin;
#: both constructions are the precommit's own declarations and each is used
#: exactly where §1/§2 assigns it (recorded in conventions).
DECLARED_NL_BIN = {
    2058: 2, 2971: 3, 7480: 3, 7001: 4,
    4623: 5, 4626: 5, 5777: 5, 5943: 5,
    4578: 6, 5369: 6, 5484: 6, 5945: 6,
}

#: Declared room-percentile grid (precommit §2, fixed, never adjusted).
ROOM_EDGES = (0.02, 0.05, 0.10, 0.175, 0.30, 0.50, 0.70)
TIGHT_MAX = 0.10          # "tight" ≔ room pct ≤ 0.10 pooled
LOOSE_BAND = (0.30, 0.70)  # "loose" band for the tight/loose contrast
CONTROL_ROOM_MIN = 0.30    # control hours ≔ room pct ≥ 0.30
NL_MATCH_TOL = 0.075       # |nl_pct(c) − nl_pct(e)| ≤ 0.075
HOD_MATCH_TOL = 1          # |hod(c) − hod(e)| ≤ 1
MIN_CONTROLS = 6           # fallback widens to month ±1 below this

#: λ-neighbourhood band (fractions of the hour's system λ) — ercot-161's.
LAMBDA_BAND = (0.7, 1.3)
#: Gap-band floor: offered mass in [max(GAP_FLOOR, model(h)), λ(h)].
GAP_FLOOR = 200.0

#: M-3 curve positions (fractions of telemetered HSL).
POSITIONS = (0.5, 0.9)

#: Fixed log-spaced histogram grids (precommit M-4): 480 bins + underflow.
HIST_BINS = 480
USD_GRID = (0.5, 5000.0)
MULT_GRID = (0.05, 2000.0)

#: Wall-scope resource types (the armed RT wall's own scope).
WALL_TYPES = ("CCGT90", "CCLE90", "SCGT90", "SCLE90")

#: Report-only classes (precommit M-2: their pricing is owned by the
#: drag/steam and per-plant coal structures, rule 19). The corpus's single
#: coal code CLLIG covers both model coal classes at this grain.
REPORT_CLASS_OF_RESTYPE = {
    "GSREH": "ST_GAS", "GSNONR": "ST_GAS", "GSSUP": "ST_GAS",
    "CLLIG": "COAL",
}
ALL_CLASS_OF_RESTYPE = {**CLASS_OF_RESTYPE, **REPORT_CLASS_OF_RESTYPE}
GATED_CLASSES = ("CC", "CT")
ALL_CLASSES = ("CC", "CT", "ST_GAS", "COAL")

#: Non-leap cumulative month-start hours (calendar-month attribution).
_CUM = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24

_MONTHS = np.searchsorted(_CUM, np.arange(8760), side="right")
_HOD = np.arange(8760) % 24


def _room_pct() -> tuple[np.ndarray, np.ndarray]:
    """(room percentile 0–1 fraction-≤ NaN-dropped, system λ), len 8760."""
    mo = pd.read_parquet(MEASURED_ORDC).sort_values("hour").reset_index(drop=True)
    assert len(mo) == 8760, f"measured ORDC rows {len(mo)} != 8760"
    rt = mo["rtolcap"].to_numpy(float)
    lam = mo["system_lambda"].to_numpy(float)
    valid = rt[~np.isnan(rt)]
    room = np.array(
        [np.nan if np.isnan(x) else float((valid <= x).mean()) for x in rt]
    )
    return room, lam


def _controls(nl: np.ndarray, room: np.ndarray) -> tuple[dict, dict]:
    """Driver-matched control hours per object hour (precommit §2).

    month(c) = month(e), |hod| ≤ 1, |nl_pct| ≤ 0.075 (both on ``_netload_pct``),
    room_pct(c) ≥ 0.30. Declared fallback: < 6 controls widens to month ±1;
    still < 6 → UNMATCHED (excluded from paired aggregates). Controls are
    driver-defined only — never selected on any price outcome.
    """
    out: dict[int, list[int]] = {}
    meta: dict[int, dict] = {}
    for e in OBJECT_HOURS:
        base = (
            (_MONTHS == _MONTHS[e])
            & (np.abs(_HOD - _HOD[e]) <= HOD_MATCH_TOL)
            & (np.abs(nl - nl[e]) <= NL_MATCH_TOL)
            & (room >= CONTROL_ROOM_MIN)
        )
        base[e] = False
        widened = False
        if base.sum() < MIN_CONTROLS:
            base = (
                (np.abs(_MONTHS - _MONTHS[e]) <= 1)
                & (np.abs(_HOD - _HOD[e]) <= HOD_MATCH_TOL)
                & (np.abs(nl - nl[e]) <= NL_MATCH_TOL)
                & (room >= CONTROL_ROOM_MIN)
            )
            base[e] = False
            widened = True
        hours = [int(h) for h in np.where(base)[0]]
        out[e] = hours if len(hours) >= MIN_CONTROLS else []
        meta[e] = {
            "n_controls": len(hours),
            "widened_month_pm1": widened,
            "matched": len(hours) >= MIN_CONTROLS,
        }
    return out, meta


def _log_edges(grid: tuple[float, float]) -> np.ndarray:
    return np.geomspace(grid[0], grid[1], HIST_BINS + 1)


def _hist_add(hist: np.ndarray, edges: np.ndarray, v: np.ndarray,
              w: np.ndarray) -> None:
    """MW-weight values into (underflow + 480) buckets; > hi lands in the top."""
    idx = np.clip(np.searchsorted(edges, v, side="right"), 0, HIST_BINS)
    np.add.at(hist, idx, w)


def _hist_quantiles(hist: np.ndarray, edges: np.ndarray,
                    qs=LADDER_QUANTILES) -> list[float]:
    """Weighted quantiles from the fixed histogram (geometric bucket mids).

    Underflow bucket reports the grid's lower bound (a value ≤ lo). The
    ≤ 2 % grid error is the declared resolution.
    """
    tot = hist.sum()
    if tot <= 0:
        return [float("nan")] * len(qs)
    cum = np.cumsum(hist) / tot
    out = []
    for q in qs:
        i = int(np.searchsorted(cum, q, side="left"))
        i = min(i, HIST_BINS)
        if i == 0:
            out.append(float(edges[0]))
        else:
            out.append(float(np.sqrt(edges[i - 1] * edges[i])))
    return out


def _position_prices(df: pd.DataFrame) -> dict[float, np.ndarray]:
    """Price of the SCED2 step curve at frac×HSL per row; NaN if unreached."""
    MW = df[_SCED2_MW].to_numpy(float)
    PR = df[_SCED2_PR].to_numpy(float)
    hsl = df["HSL"].to_numpy(float)
    valid = np.isfinite(MW) & np.isfinite(PR)
    MWv = np.where(valid, MW, -np.inf)
    out = {}
    for frac in POSITIONS:
        pos = frac * hsl
        reach = MWv >= pos[:, None]
        ok = reach.any(axis=1) & np.isfinite(hsl) & (hsl > 0)
        idx = reach.argmax(axis=1)
        p = np.where(ok, PR[np.arange(len(df)), idx], np.nan)
        out[frac] = np.minimum(p, HCAP_USD_MWH)
    return out


def _census_slices(df: pd.DataFrame, lam: np.ndarray, model: np.ndarray,
                   acc: dict, iv_sets: dict) -> None:
    """M-1 above-LSL census at the object hours (the ercot-161 walk).

    Per (hour, Resource Type) accumulate MW sums: dispatched in the λ-band,
    dispatched/offered ≥ $500 / ≥ $1,000, offered in the gap band
    [max(200, model(h)), λ(h)]. ``iv_sets[h]`` collects distinct interval
    timestamps for the interval-mean normalization.
    """
    MW = df[_SCED2_MW].to_numpy(float)
    PR = df[_SCED2_PR].to_numpy(float)
    lsl = np.maximum(df["LSL"].to_numpy(float), 0.0)
    bp = df["Base Point"].to_numpy(float)
    hasl = df["HASL"].to_numpy(float)
    hoy = df["hoy"].to_numpy(int)
    rtype = df["Resource Type"].astype(str).to_numpy()
    lam_h = lam[hoy]
    gap_lo = np.maximum(GAP_FLOOR, model[hoy])
    for h in np.unique(hoy):
        iv_sets.setdefault(int(h), set()).update(
            df.loc[df["hoy"].to_numpy() == h, "SCED Time Stamp"].tolist()
        )
    prev = lsl.copy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        lo = np.maximum(prev, lsl)
        d_mw = np.where(valid, np.maximum(np.minimum(q, bp) - lo, 0.0), 0.0)
        o_mw = np.where(valid, np.maximum(np.minimum(q, hasl) - lo, 0.0), 0.0)
        in_band = valid & (p >= LAMBDA_BAND[0] * lam_h) & (p <= LAMBDA_BAND[1] * lam_h)
        in_gap = valid & (p >= gap_lo) & (p <= lam_h)
        any_mw = (d_mw > 0) | (o_mw > 0)
        for h in np.unique(hoy[any_mw]):
            at_h = hoy == h
            for t in np.unique(rtype[at_h & any_mw]):
                sel = at_h & (rtype == t)
                a = acc.setdefault((int(h), t), np.zeros(6))
                a[0] += d_mw[sel & in_band].sum()
                a[1] += d_mw[sel & valid & (p >= 500.0)].sum()
                a[2] += d_mw[sel & valid & (p >= 1000.0)].sum()
                a[3] += o_mw[sel & valid & (p >= 500.0)].sum()
                a[4] += o_mw[sel & valid & (p >= 1000.0)].sum()
                a[5] += o_mw[sel & in_gap].sum()
        prev = np.where(valid, np.maximum(prev, q), prev)


def main() -> None:  # noqa: PLR0915 — one linear precommit execution
    t0 = time.time()

    # ---- V-0 identity gate (precommit §1) — hard stop, nothing written.
    m, a = _series()
    pop = sorted(int(h) for h in np.where((m < 200.0) & (a >= 500.0))[0])
    assert pop == FAMILY_HOURS, f"V-0 FAIL population {pop} != {FAMILY_HOURS}"

    room, lam = _room_pct()
    nl = _netload_pct(YEAR)
    nl_bin = np.where(
        np.isnan(nl), -1, np.searchsorted(np.asarray(NETLOAD_PCT_EDGES), nl,
                                          side="right")
    ).astype(int)
    room_bin = np.where(
        np.isnan(room), -1, np.searchsorted(np.asarray(ROOM_EDGES), room,
                                            side="right")
    ).astype(int)
    n_room_bins = len(ROOM_EDGES) + 1
    n_nl_bins = len(NETLOAD_PCT_EDGES) + 1

    controls, control_meta = _controls(nl, room)
    matched_hours = [e for e in OBJECT_HOURS if control_meta[e]["matched"]]
    interest = set(OBJECT_HOURS)
    for e in matched_hours:
        interest.update(controls[e])

    gas_day = _gas_day_series()
    day_dates = pd.to_datetime(f"{YEAR}-01-01") + pd.to_timedelta(
        np.arange(365), "D"
    )
    gas_by_day = gas_day.reindex(day_dates).to_numpy(float)  # (365,)

    usd_edges = _log_edges(USD_GRID)
    mult_edges = _log_edges(MULT_GRID)
    cls_idx = {c: i for i, c in enumerate(GATED_CLASSES)}

    # M-4 accumulators: (class, nl_bin, room_bin) histograms + occupancy.
    usd_hist = np.zeros((2, n_nl_bins, n_room_bins, HIST_BINS + 1))
    mult_hist = np.zeros((2, n_nl_bins, n_room_bins, HIST_BINS + 1))
    riv_count = np.zeros((2, n_nl_bins, n_room_bins), dtype=np.int64)
    day_sets: dict[tuple[int, int, int], set] = {}
    seg_count = np.zeros((2, n_nl_bins, n_room_bins), dtype=np.int64)
    excluded_mw = 0.0  # spare MW at hours with NaN nl/room (never binned)

    # Hours-of-interest retention (compact): M-2 segments and M-3 rows.
    m2_segs: dict[tuple[str, int], list[np.ndarray]] = {}
    m3_rows: list[pd.DataFrame] = []
    m1_acc: dict[tuple[int, str], np.ndarray] = {}
    m1_iv: dict[int, set] = {}

    read_cols = _READ_COLS + ["Resource Name", "LSL", "HSL"]
    files = _sced_source_files(YEAR)
    interest_arr = np.zeros(8760, dtype=bool)
    interest_arr[list(interest)] = True
    object_arr = np.zeros(8760, dtype=bool)
    object_arr[OBJECT_HOURS] = True

    n_files = 0
    for path in files:
        df = pd.read_parquet(path, columns=read_cols)
        df = _delivery_year_rows(df, YEAR)
        if df.empty:
            continue
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.str.startswith("ON") & (stat != "ONTEST")].copy()
        if df.empty:
            continue
        n_files += 1
        # CPT → fixed CST → non-leap hour-of-year (the ercot-161 clock).
        ts = pd.to_datetime(df["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert("Etc/GMT+6")
        mo_ = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo_ == 2) & (dy == 29))
        df = df.loc[np.asarray(ok)].copy()
        if df.empty:
            continue
        df["hoy"] = _MONTH_START_HOUR[mo_[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        df = _coerce_sced_numeric(df)
        hoy_np = df["hoy"].to_numpy(int)

        # ---- M-4 full-year accumulation (gated classes only).
        g = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        if not g.empty:
            g = g.copy()
            g["cls"] = g["Resource Type"].map(CLASS_OF_RESTYPE)
            g["_ts_key"] = np.arange(len(g))  # row id → resource-interval
            seg = _spare_segments(g)
            if not seg.empty:
                s_hoy = seg["hoy"].to_numpy(int)
                s_ci = seg["cls"].map(cls_idx).to_numpy(int)
                s_nb = nl_bin[s_hoy]
                s_rb = room_bin[s_hoy]
                s_mw = seg["mw"].to_numpy(float)
                s_usd = seg["price"].to_numpy(float)
                s_mult = s_usd / gas_by_day[np.minimum(s_hoy // 24, 364)]
                binned = (s_nb >= 0) & (s_rb >= 0)
                excluded_mw += float(s_mw[~binned].sum())
                for ci in (0, 1):
                    selc = binned & (s_ci == ci)
                    for nb in np.unique(s_nb[selc]):
                        seln = selc & (s_nb == nb)
                        for rb in np.unique(s_rb[seln]):
                            sel = seln & (s_rb == rb)
                            _hist_add(usd_hist[ci, nb, rb], usd_edges,
                                      s_usd[sel], s_mw[sel])
                            _hist_add(mult_hist[ci, nb, rb], mult_edges,
                                      s_mult[sel], s_mw[sel])
                            riv_count[ci, nb, rb] += len(
                                np.unique(seg["ts"].to_numpy()[sel])
                            )
                            seg_count[ci, nb, rb] += int(sel.sum())
                            day_sets.setdefault(
                                (ci, int(nb), int(rb)), set()
                            ).update((s_hoy[sel] // 24).tolist())

        # ---- Hours-of-interest retention (all four classes).
        hi = df[interest_arr[hoy_np] & df["Resource Type"].isin(
            ALL_CLASS_OF_RESTYPE)]
        if not hi.empty:
            hi = hi.copy()
            hi["cls"] = hi["Resource Type"].map(ALL_CLASS_OF_RESTYPE)
            hi["_ts_key"] = np.arange(len(hi))
            seg = _spare_segments(hi)
            if not seg.empty:
                s_hoy = seg["hoy"].to_numpy(int)
                s_usd = seg["price"].to_numpy(float)
                arr = np.column_stack(
                    [seg["mw"].to_numpy(float), s_usd,
                     s_usd / gas_by_day[np.minimum(s_hoy // 24, 364)]]
                )
                for (cls, h), grp in pd.DataFrame(
                    {"cls": seg["cls"], "hoy": s_hoy}
                ).groupby(["cls", "hoy"], sort=False):
                    m2_segs.setdefault((str(cls), int(h)), []).append(
                        arr[grp.index.to_numpy()]
                    )
            pos = _position_prices(hi)
            m3_rows.append(pd.DataFrame({
                "hoy": hi["hoy"].to_numpy(int),
                "cls": hi["cls"].to_numpy(),
                "rname": hi["Resource Name"].astype(str).to_numpy(),
                "hsl": hi["HSL"].to_numpy(float),
                "p05": pos[0.5],
                "p09": pos[0.9],
            }))

        # ---- M-1 census (object hours, ALL resource types).
        obj = df[object_arr[hoy_np]]
        if not obj.empty:
            _census_slices(obj, lam, m, m1_acc, m1_iv)
        del df

    elapsed_scan = round(time.time() - t0, 1)

    # ================= assembly =================

    # ---- M-1: per-object-hour all-type census (interval means, GW).
    m1 = {}
    bucket_names = ("disp_lambda_band", "disp_ge500", "disp_ge1000",
                    "off_ge500", "off_ge1000", "off_gap_band")
    for h in OBJECT_HOURS:
        n_iv = max(len(m1_iv.get(h, set())), 1)
        types = sorted({t for (hh_, t) in m1_acc if hh_ == h})
        per_type = {
            t: {
                b: round(float(m1_acc[(h, t)][i]) / n_iv / 1e3, 4)
                for i, b in enumerate(bucket_names)
            }
            for t in types
        }
        tot = {b: sum(v[b] for v in per_type.values()) for b in bucket_names}
        wall = {
            b: sum(per_type.get(t, {}).get(b, 0.0) for t in WALL_TYPES)
            for b in bucket_names
        }
        band_by_type = {t: v["disp_lambda_band"] for t, v in per_type.items()}
        largest = max(band_by_type, key=band_by_type.get) if band_by_type else None
        coal_st = sum(
            per_type.get(t, {}).get("disp_lambda_band", 0.0)
            for t in REPORT_CLASS_OF_RESTYPE
        )
        m1[str(h)] = {
            "n_intervals": len(m1_iv.get(h, set())),
            "lambda": round(float(lam[h]), 2),
            "model": round(float(m[h]), 2),
            "gap_band_lo": round(float(max(GAP_FLOOR, m[h])), 2),
            "per_type_gw": per_type,
            "total_gw": {b: round(v, 4) for b, v in tot.items()},
            "wall_scope_gw": {b: round(v, 4) for b, v in wall.items()},
            "wall_share_lambda_band": round(
                wall["disp_lambda_band"] / tot["disp_lambda_band"], 4
            ) if tot["disp_lambda_band"] > 0 else float("nan"),
            "largest_type_lambda_band": largest,
            "coal_plus_stgas_lambda_band_share": round(
                coal_st / tot["disp_lambda_band"], 4
            ) if tot["disp_lambda_band"] > 0 else float("nan"),
        }

    # ---- M-2: event-vs-control spare ladders (pooled, per class).
    def _pool(cls: str, hours: list[int]) -> np.ndarray:
        parts = [x for h in hours for x in m2_segs.get((cls, h), [])]
        return np.vstack(parts) if parts else np.zeros((0, 3))

    def _wq(v: np.ndarray, w: np.ndarray, qs=LADDER_QUANTILES) -> list[float]:
        if len(v) == 0:
            return [float("nan")] * len(qs)
        return _weighted_quantiles(v, w, qs)

    m2 = {}
    for cls in ALL_CLASSES:
        ev = _pool(cls, OBJECT_HOURS)
        # each matched object hour contributes its own control pool
        # (multiplicity across object hours retained — see conventions).
        ct_parts = [_pool(cls, controls[e]) for e in matched_hours]
        ct = np.vstack([p for p in ct_parts if len(p)]) if ct_parts else np.zeros((0, 3))
        m2[cls] = {
            "report_only": cls not in GATED_CLASSES,
            "event": {
                "n_segments": int(len(ev)),
                "mw": round(float(ev[:, 0].sum()), 0),
                "usd": [round(v, 2) for v in _wq(ev[:, 1], ev[:, 0])],
                "hr_mult": [round(v, 3) for v in _wq(ev[:, 2], ev[:, 0])],
            },
            "control": {
                "n_segments": int(len(ct)),
                "mw": round(float(ct[:, 0].sum()), 0),
                "usd": [round(v, 2) for v in _wq(ct[:, 1], ct[:, 0])],
                "hr_mult": [round(v, 3) for v in _wq(ct[:, 2], ct[:, 0])],
            },
        }

    # ---- M-3: within-resource paired repricing (position-fixed).
    m3_df = (
        pd.concat(m3_rows, ignore_index=True)
        if m3_rows else pd.DataFrame(columns=["hoy", "cls", "rname", "hsl",
                                              "p05", "p09"])
    )
    gas_of_h = gas_by_day[np.minimum(np.arange(8760) // 24, 364)]

    def _hour_vals(cls: str, h: int) -> pd.DataFrame:
        """(rname, hsl, p05, p09) per resource at hour h (interval medians)."""
        sub = m3_df[(m3_df["cls"] == cls) & (m3_df["hoy"] == h)]
        if sub.empty:
            return sub
        g = sub.groupby("rname").agg(
            hsl=("hsl", "median"), p05=("p05", "median"), p09=("p09", "median")
        )
        return g

    m3 = {}
    for cls in ALL_CLASSES:
        per_hour = {}
        pooled_d = {0.5: ([], []), 0.9: ([], [])}
        pooled_dm = {0.5: [], 0.9: []}
        for e in matched_hours:
            ev = _hour_vals(cls, e)
            if ev.empty:
                per_hour[str(e)] = {"n_resources": 0}
                continue
            ctl = {c: _hour_vals(cls, c) for c in controls[e]}
            recs = {0.5: ([], []), 0.9: ([], [])}
            n_res = 0
            for rname, row in ev.iterrows():
                on_in = [c for c in controls[e]
                         if not ctl[c].empty and rname in ctl[c].index]
                if len(on_in) < 3:
                    continue
                n_res += 1
                for frac, col in ((0.5, "p05"), (0.9, "p09")):
                    pe = row[col]
                    pc = np.array([ctl[c].loc[rname, col] for c in on_in],
                                  dtype=float)
                    pc_ok = pc[np.isfinite(pc)]
                    if not np.isfinite(pe) or len(pc_ok) < 3:
                        continue
                    d_usd = float(pe - np.median(pc_ok))
                    pc_m = np.array(
                        [ctl[c].loc[rname, col] / gas_of_h[c]
                         for c in on_in], dtype=float)
                    pc_m_ok = pc_m[np.isfinite(pc_m)]
                    d_mult = float(pe / gas_of_h[e] - np.median(pc_m_ok))
                    recs[frac][0].append(d_usd)
                    recs[frac][1].append(float(row["hsl"]))
                    pooled_d[frac][0].append(d_usd)
                    pooled_d[frac][1].append(float(row["hsl"]))
                    pooled_dm[frac].append(d_mult)
            per_hour[str(e)] = {"n_resources": n_res}
            for frac in POSITIONS:
                d, w = recs[frac]
                if d:
                    qs = _weighted_quantiles(np.array(d), np.array(w),
                                             (0.25, 0.5, 0.75))
                    per_hour[str(e)][f"delta_usd_{frac}"] = {
                        "n": len(d), "p25": round(qs[0], 2),
                        "median": round(qs[1], 2), "p75": round(qs[2], 2),
                    }
        block = {"report_only": cls not in GATED_CLASSES, "per_hour": per_hour}
        for frac in POSITIONS:
            d, w = pooled_d[frac]
            if d:
                qs = _weighted_quantiles(np.array(d), np.array(w),
                                         (0.25, 0.5, 0.75))
                qm = _weighted_quantiles(np.array(pooled_dm[frac]),
                                         np.array(w), (0.25, 0.5, 0.75))
                block[f"pooled_delta_{frac}"] = {
                    "n_pairs": len(d),
                    "usd": {"p25": round(qs[0], 2), "median": round(qs[1], 2),
                            "p75": round(qs[2], 2)},
                    "hr_mult": {"p25": round(qm[0], 4),
                                "median": round(qm[1], 4),
                                "p75": round(qm[2], 4)},
                }
            else:
                block[f"pooled_delta_{frac}"] = {"n_pairs": 0}
        m3[cls] = block

    # ---- M-4: the pooled full-year candidate surface.
    tight_rbs = [i for i in range(n_room_bins)
                 if (ROOM_EDGES + (1.0,))[i] <= TIGHT_MAX]
    loose_rbs = [i for i in range(n_room_bins)
                 if ((0.0,) + ROOM_EDGES)[i] >= LOOSE_BAND[0]
                 and (ROOM_EDGES + (1.0,))[i] <= LOOSE_BAND[1]]

    def _cell(ci: int, nb: int, rbs: list[int]) -> dict:
        uh = usd_hist[ci, nb, rbs].sum(axis=0)
        mh = mult_hist[ci, nb, rbs].sum(axis=0)
        days = set()
        for rb in rbs:
            days |= day_sets.get((ci, nb, rb), set())
        return {
            "usd": [round(v, 2) for v in _hist_quantiles(uh, usd_edges)],
            "hr_mult": [round(v, 3) for v in _hist_quantiles(mh, mult_edges)],
            "segments": int(seg_count[ci, nb, rbs].sum()),
            "resource_intervals": int(riv_count[ci, nb, rbs].sum()),
            "days": len(days),
        }

    m4 = {"room_bin_edges": list(ROOM_EDGES),
          "netload_bin_edges": list(NETLOAD_PCT_EDGES),
          "quantiles": list(LADDER_QUANTILES),
          "histogram": {"bins": HIST_BINS, "usd_grid": list(USD_GRID),
                        "mult_grid": list(MULT_GRID),
                        "grid_error": "~1.9 % per bucket (geometric mids)"},
          "excluded_unbinned_spare_mw": round(excluded_mw, 0)}
    for cls in GATED_CLASSES:
        ci = cls_idx[cls]
        cells = {}
        for nb in range(n_nl_bins):
            for rb in range(n_room_bins):
                cells[f"nl{nb}|room{rb}"] = _cell(ci, nb, [rb])
        pooled = {}
        for nb in range(n_nl_bins):
            t = _cell(ci, nb, tight_rbs)
            lo = _cell(ci, nb, loose_rbs)
            t_p90m, lo_p90m = t["hr_mult"][4], lo["hr_mult"][4]
            t_p90u, lo_p90u = t["usd"][4], lo["usd"][4]
            pooled[f"nl{nb}"] = {
                "tight": t, "loose": lo,
                "p90_ratio_mult": round(t_p90m / lo_p90m, 3)
                if np.isfinite(t_p90m) and np.isfinite(lo_p90m) and lo_p90m > 0
                else float("nan"),
                "p90_ratio_usd": round(t_p90u / lo_p90u, 3)
                if np.isfinite(t_p90u) and np.isfinite(lo_p90u) and lo_p90u > 0
                else float("nan"),
            }
        m4[cls] = {"cells": cells, "tight_vs_loose_by_nl_bin": pooled}

    # ---- M-5: model-side reconciliation (committed values only).
    e239 = json.loads(ERCOT239_JSON.read_text())
    rows239 = {r["h"]: r for r in e239["rows"]}
    reserves239 = e239["context"]["measured_reserves"]["at_event_hours"]
    k33 = json.loads(K33_RUN_CONFIG.read_text())
    sc = k33["scenario_config"]
    m5 = {
        "per_hour": {
            str(h): {
                "model": rows239[h]["model"],
                "actual": rows239[h]["actual"],
                "ordc_total_dual": rows239[h]["model_side"]["families"]
                    .get("ercot_ordc_total", {}).get("dual"),
                "families": rows239[h]["model_side"]["families"],
                "reserve_shortfall_mw":
                    rows239[h]["model_side"]["reserve_shortfall_mw"],
                "rtordpa_overlay": rows239[h]["model_side"]["rtordpa_overlay"],
                "rtolcap_pctl_year": reserves239[str(h)]["rtolcap_pctl_year"],
                "net_load_pctl_year":
                    rows239[h]["actual_side"]["net_load_pctl_year"],
                "declared_nl_bin": DECLARED_NL_BIN[h],
            }
            for h in OBJECT_HOURS
        },
        "k33_armed_offer_path": {
            "ercot_offer_surface_cleared_share":
                sc["ercot_offer_surface_cleared_share"],
            "ercot_offer_surface_cleared_share_rt":
                sc["ercot_offer_surface_cleared_share_rt"],
            "ercot_offer_surface_cleared_share_rt_mode":
                sc["ercot_offer_surface_cleared_share_rt_mode"],
            "ercot_offer_surface_netload_pcts":
                sc["ercot_offer_surface_netload_pcts"],
            "ercot_offer_surface_conditional":
                sc["ercot_offer_surface_conditional"],
            "ercot_offer_surface_position_tail":
                sc["ercot_offer_surface_position_tail"],
            "ercot_offer_swcap_clip": sc["ercot_offer_swcap_clip"],
            "ercot_faststart_pool_offer": sc["ercot_faststart_pool_offer"],
            "k33_peak_bands_note": k33.get("model_changes_note"),
        },
        "reconciliation_note": (
            "a room axis would EXTEND the armed RT-wall conditioning (one "
            "mechanism, finer conditioning per rule 19) — never a stacked "
            "adder or floor"
        ),
    }

    # ---- Priors P1–P5 (computed here, GRADED in the FINDING).
    wall_shares = {h: m1[str(h)]["wall_share_lambda_band"] for h in OBJECT_HOURS}
    largest = {h: m1[str(h)]["largest_type_lambda_band"] for h in OBJECT_HOURS}
    gas_off500 = {
        h: sum(m1[str(h)]["per_type_gw"].get(t, {}).get("off_ge500", 0.0)
               for t in WALL_TYPES)
        for h in OBJECT_HOURS
    }
    coalst = {h: m1[str(h)]["coal_plus_stgas_lambda_band_share"]
              for h in OBJECT_HOURS}
    other_med = float(np.nanmedian([coalst[h] for h in OBJECT_HOURS if h != 2058]))
    p3_ratios = {
        cls: {f"nl{nb}": m4[cls]["tight_vs_loose_by_nl_bin"][f"nl{nb}"]
              ["p90_ratio_mult"] for nb in range(2, 7)}
        for cls in GATED_CLASSES
    }
    p5_cells = {}
    for cls in GATED_CLASSES:
        ci = cls_idx[cls]
        p5_cells[cls] = {
            f"nl{nb}": {
                "resource_intervals": _cell(ci, nb, tight_rbs)["resource_intervals"],
                "days": _cell(ci, nb, tight_rbs)["days"],
            }
            for nb in range(2, 7)
        }
    priors = {
        "P1_composition": {
            "hours_wall_share_lt_third": sum(
                1 for h in OBJECT_HOURS
                if np.isfinite(wall_shares[h]) and wall_shares[h] < 1 / 3
            ),
            "declared_ge": 8,
            "hours_pwrstr_largest": sum(
                1 for h in OBJECT_HOURS if largest[h] == "PWRSTR"
            ),
            "pwrstr_declared_ge": 8,
            "wall_share_by_hour": {str(h): wall_shares[h] for h in OBJECT_HOURS},
            "largest_by_hour": {str(h): largest[h] for h in OBJECT_HOURS},
        },
        "P2_gas_high_price_mass": {
            "hours_cc_ct_off500_le_0p15gw": sum(
                1 for h in OBJECT_HOURS if gas_off500[h] <= 0.15
            ),
            "declared_ge": 10,
            "cc_ct_off500_gw_by_hour": {
                str(h): round(gas_off500[h], 4) for h in OBJECT_HOURS
            },
        },
        "P3_room_shift_small": {
            "pooled_m3_median_delta_usd_0p9": {
                cls: m3[cls]["pooled_delta_0.9"].get("usd", {}).get("median")
                for cls in GATED_CLASSES
            },
            "declared_lt_usd": 25.0,
            "tight_loose_p90_mult_ratio_bins_2_6": p3_ratios,
            "declared_ratio_lt": 1.25,
        },
        "P4_h2058_differs": {
            "h2058_coal_stgas_share": coalst[2058],
            "other_hours_median_share": round(other_med, 4),
            "declared_ge_multiple": 2.0,
        },
        "P5_occupancy": {
            "tight_by_nl_bin": p5_cells,
            "declared_cc_min_resource_intervals": 100,
            "declared_min_days": 10,
        },
    }

    # ---- Kills and the Phase-1 gate (precommit §4, direction-blind).
    k1_n = priors["P1_composition"]["hours_wall_share_lt_third"]
    k1 = k1_n >= 8

    def _k2a(cls: str) -> bool:
        v = m3[cls]["pooled_delta_0.9"].get("usd", {}).get("median")
        return v is not None and v < 10.0

    def _k2b(cls: str) -> bool:
        r = [p3_ratios[cls][f"nl{nb}"] for nb in range(2, 7)]
        return all(np.isfinite(x) and x < 1.15 for x in r)

    k2 = all(_k2a(c) for c in GATED_CLASSES) and all(
        _k2b(c) for c in GATED_CLASSES
    )
    pooled_occ = {
        cls: {
            "resource_intervals": int(sum(
                p5_cells[cls][f"nl{nb}"]["resource_intervals"]
                for nb in range(2, 7)
            )),
            "days": len({
                d for nb in range(2, 7) for rb in tight_rbs
                for d in day_sets.get((cls_idx[cls], nb, rb), set())
            }),
        }
        for cls in GATED_CLASSES
    }
    k3 = all(
        pooled_occ[c]["resource_intervals"] < 100 or pooled_occ[c]["days"] < 10
        for c in GATED_CLASSES
    )

    def _tight_p90_usd(cls: str, nb: int) -> float:
        return _cell(cls_idx[cls], nb, tight_rbs)["usd"][4]

    gate_ii_hours = sum(
        1 for h in OBJECT_HOURS
        if any(
            np.isfinite(_tight_p90_usd(c, DECLARED_NL_BIN[h]))
            and _tight_p90_usd(c, DECLARED_NL_BIN[h]) >= 500.0
            for c in GATED_CLASSES
        )
    )
    gate_iii = {
        cls: sum(
            1 for nb in range(2, 7)
            if np.isfinite(p3_ratios[cls][f"nl{nb}"])
            and p3_ratios[cls][f"nl{nb}"] > 1.25
        )
        for cls in GATED_CLASSES
    }
    gate_iv = {
        cls: all(
            p5_cells[cls][f"nl{nb}"]["resource_intervals"] >= 100
            and p5_cells[cls][f"nl{nb}"]["days"] >= 10
            for nb in range(2, 7)
        )
        for cls in GATED_CLASSES
    }
    gate = {
        "K1_scope_kill": {"fired": bool(k1), "hours_lt_third": int(k1_n),
                          "threshold_ge": 8},
        "K2_no_dependence_kill": {
            "fired": bool(k2),
            "a_median_delta_lt_10": {c: _k2a(c) for c in GATED_CLASSES},
            "b_ratio_lt_1p15_all_bins": {c: _k2b(c) for c in GATED_CLASSES},
        },
        "K3_identifiability_kill": {"fired": bool(k3),
                                    "pooled_tight_bins_2_6": pooled_occ},
        "phase1_gate": {
            "i_no_kill": not (k1 or k2 or k3),
            "ii_reach_hours": int(gate_ii_hours),
            "ii_declared_ge": 6,
            "ii_pass": gate_ii_hours >= 6,
            "iii_ratio_gt_1p25_bins": gate_iii,
            "iii_pass": any(v >= 3 for v in gate_iii.values()),
            "iv_occupancy_per_class": gate_iv,
            "iv_pass_any_class": any(gate_iv.values()),
            "OPEN": bool(
                not (k1 or k2 or k3) and gate_ii_hours >= 6
                and any(v >= 3 for v in gate_iii.values())
                and any(gate_iv.values())
            ),
        },
    }

    res = {
        "session": "ercot-241",
        "keeper": "2026-08-25-236-swcap-clip-k33 (2023 carve-out, untouched)",
        "precommit": "docs/PRECOMMIT-ercot241-offcore-conduct-phase0-2026-08-30.md",
        "v0_identity": {"family": FAMILY_HOURS, "object_set": OBJECT_HOURS,
                        "pass": True},
        "conventions": {
            "status_filter": "startswith('ON') and != 'ONTEST' (ERCOT-154)",
            "clock": "CPT -> America/Chicago -> Etc/GMT+6, Feb-29 dropped "
                     "(ercot161_price_setter_census verbatim)",
            "netload_bins": (
                "object-hour bin references use the precommit §1 DECLARED "
                "mapping (committed ercot-239 net_load_pctl_year on the armed "
                "edges); the full-year M-4 surface and control matching use "
                "_netload_pct (rank), the armed wall's own conditioning "
                "variable — both as declared in §1/§2. The two differ at 5 of "
                "12 object hours (2971, 5369, 5484, 7001, 7480 land one bin "
                "lower on rank)"
            ),
            "room_pct": "rtolcap year fraction <=, NaN-dropped, 0-1",
            "m2_control_pooling": (
                "pooled control ladder concatenates each matched object "
                "hour's own control pool (a control hour serving k object "
                "hours contributes k times)"
            ),
            "m3_pairing": (
                "resource ON at e and ON in >= 3 of e's controls; a position "
                "needs >= 3 finite control per-hour values (per-hour value = "
                "median across the hour's intervals, NaN if the curve does "
                "not reach the position)"
            ),
            "primary_units": (
                "kill/gate ratio contrasts (K-2b, gate iii, P3) graded on "
                "HR-mult (the armed wall's own convention), $ reported "
                "alongside; explicit $ thresholds (K-2a $10, P3 $25, gate ii "
                "$500) graded in $ — fixed before measurement"
            ),
            "coal_code": "CLLIG is the corpus's single coal Resource Type",
            "hist_underflow": "values below the grid floor report the floor",
        },
        "population": {
            "matched_hours": matched_hours,
            "unmatched_hours": [e for e in OBJECT_HOURS
                                if not control_meta[e]["matched"]],
            "control_meta": {str(e): control_meta[e] for e in OBJECT_HOURS},
            "controls": {str(e): controls[e] for e in OBJECT_HOURS},
            "n_interest_hours": len(interest),
        },
        "scan": {"files_with_rows": n_files, "n_source_files": len(files),
                 "seconds": elapsed_scan},
        "M1_census": m1,
        "M2_event_vs_control_ladders": m2,
        "M3_paired_repricing": m3,
        "M4_candidate_surface": m4,
        "M5_model_side": m5,
        "priors": priors,
        "kills_and_gate": gate,
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))

    headline = {
        "P1": {k: priors["P1_composition"][k]
               for k in ("hours_wall_share_lt_third", "hours_pwrstr_largest")},
        "P2": priors["P2_gas_high_price_mass"]["hours_cc_ct_off500_le_0p15gw"],
        "P3_pooled_delta_usd_0p9":
            priors["P3_room_shift_small"]["pooled_m3_median_delta_usd_0p9"],
        "P3_ratios": p3_ratios,
        "P4": {k: priors["P4_h2058_differs"][k]
               for k in ("h2058_coal_stgas_share", "other_hours_median_share")},
        "kills": {k: gate[k]["fired"] for k in
                  ("K1_scope_kill", "K2_no_dependence_kill",
                   "K3_identifiability_kill")},
        "phase1_gate": gate["phase1_gate"],
    }
    print(json.dumps(headline, indent=1))
    print(f"wrote {OUT_JSON} ({round(time.time() - t0, 1)}s total)")


if __name__ == "__main__":
    main()
