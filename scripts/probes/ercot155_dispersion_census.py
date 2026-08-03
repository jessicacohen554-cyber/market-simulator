"""ERCOT-155 Phase 1 — the dispatchable stack's mid-merit evening price DISPERSION.

The ERCOT-154 successor object, measured before any lever is proposed.
ERCOT-154 §4 named it: the keeper's matched (month x hour-of-day) evening
supply-curve slope is 1.557/1.616 $/MWh per GW, so ERCOT-153's $20-66/MWh
evening-ramp premium has no former. This probe asks the three Phase-1 questions
on COMMITTED BYTES ONLY -- the ercot150b keeper's ``meta.json`` reconstruction
(``reconstruct_bundle_fleet``, no LP, no year solved) plus its committed hourly
sidecars, and the four committed 60-Day SCED extracts:

(a) WHICH CLASSES occupy the evening headroom band, and what is the model's own
    offer spread across it. Measured on ``mc_base`` -- the assembled P0
    objective the LP actually solved on (fuel + VOM + carbon + NOx + EAC + coal
    tranches + every pricing overlay applied), never a re-derivation.
(b) THE SAME BAND'S SPREAD in the real market's own conduct, from the 60-Day
    SCED TPO corpus (the ERCOT-136/138 per-plant instrument). Only the SHAPE of
    the stack over its own headroom is read -- this is NOT a re-derive of the
    closed LEVEL program (ERCOT-99/100/118/119/136-140/144/150).
(c) SLOPE or COMPOSITION? The band width is decomposed on BOTH sides into the
    ACROSS-resource term (the spread of resource-level offer levels) and the
    WITHIN-resource term (each resource's own rise from its bottom step to its
    top step). A model that matches the real across-term but not the within-term
    has a tranche-shape defect; one that matches neither while packing the same
    MW into a narrower band has a composition defect; and the headroom-share
    ladder (share of headroom MW offered above $100/$200/$500) says directly
    whether any pricing rule could reach the real market's upper region.

**Normalization.** Both sides are read at fixed ABSOLUTE MW offsets above each
interval's own realized dispatch point -- never a fraction of headroom, because
the model's headroom includes the MW its in-LP co-optimization holds as AS while
SCED's HASL has already netted the AS award out. ERCOT-154 §4's "~25 GW of
thermal headroom" is the gap between the ANNUAL MAXIMUM thermal dispatch
(60.4-61.1 GW) and the evening MEAN (35.3-35.7 GW), a cross-hour difference; the
headroom actually available in an evening hour is measured here and is
materially smaller.

**Day-class separation is mandatory.** Three of the four extracts are event
("tail") day samples and would overstate the real market's dispersion if pooled
with the control days. Every SCED statistic is reported per day-class, and the
model side is additionally read on the SAME calendar days so the comparison is
matched.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/ercot155_dispersion_census.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    _MONTH_START_HOUR,
)
from derive_ercot_faststart_pool import _STD_TZ  # noqa: E402
from derive_ercot_sced_offer_wall import SCED_DIR  # noqa: E402

BUNDLE = REPO / "results/calibration/ercot150_zonalanchor_B"
HOURLY = BUNDLE / "hourly"
DEFAULT_OUT = REPO / "results/calibration/ercot155_dispersion_census.json"

#: The ERCOT-153/154 evening block on the fixed-CST clock (inclusive).
EVENING = (17, 21)

#: ABSOLUTE MW offsets above the realized dispatch point the ladder is read at
#: (GW). Absolute offsets — not fractions of headroom — are what make the two
#: sides comparable: the model's headroom includes the MW its in-LP reserve
#: co-optimization holds as AS, while SCED's HASL cap has already netted each
#: resource's AS award out. That asymmetry moves where each stack ENDS, but at
#: a fixed offset above the dispatch point both sides answer the same question
#: ("what does the next N GW cost?"), so it cannot bias the region of interest.
BAND_OFFSETS_GW: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0)

#: Absolute price rungs the headroom-share ladder is reported at ($/MWh).
SHARE_RUNGS: tuple[float, ...] = (50.0, 75.0, 100.0, 150.0, 200.0, 300.0, 500.0, 1000.0)

#: The share/split statistics are computed over the first this-many GW of
#: headroom above the dispatch point, on both sides, for the same reason. 1 GW
#: is the widest band the SCED side actually covers (per-offset coverage falls
#: from 0.93/0.83 at +1 GW to 0.65/0.53 at +2 GW on the control-day extracts):
#: a wider band would compare the model's deep headroom against SCED intervals
#: that simply have no such MW online.
SHARE_BAND_GW: float = 1.0

#: Model dispatchable thermal groups (``FleetArrays.plant_group``).
THERMAL_GROUPS = ("COAL", "CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")

#: Model class labels in ``class_hourly_<year>.parquet`` that sum to the
#: thermal dispatch point the band sits above.
MODEL_THERMAL_CLASSES = frozenset(
    {
        "COAL_LIGNITE",
        "COAL_PRB",
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "ST_CHP",
        "OTHER_FOSSIL",
    }
)

#: SCED Resource Types that are the real market's dispatchable thermal stack --
#: the counterpart of THERMAL_GROUPS. Combined cycle (CCGT90/CCLE90), simple
#: cycle (SCGT90/SCLE90), lignite/coal (CLLIG/CLLIM), gas steam
#: (GSREH/GSNONR/GSSUP) and reciprocating/diesel (RECIP/DSL). WIND, PVGR,
#: PWRSTR, HYDRO, NUC and RENEW never enter.
SCED_THERMAL_TYPES = (
    "CCGT90",
    "CCLE90",
    "SCGT90",
    "SCLE90",
    "CLLIG",
    "CLLIM",
    "GSREH",
    "GSNONR",
    "GSSUP",
    "RECIP",
    "DSL",
)

#: Online, commercially-offering telemetry states (Nodal Protocols §3.9.1).
#: ONTEST is excluded (commissioning, not commercial); OUT/OFF/NA/ONHOLD never
#: enter. Same population rule as ERCOT-154.
ONLINE_STATES = ("ON", "ONREG", "ONFFRRRS", "FRRSUP", "ONRGL", "ONOS")

#: Day-class of each committed extract, from its filename token. The tail-day
#: samples are event days and are never pooled with the control days.
DAY_CLASS = {
    "ercot74_tail_days": "tail",
    "ercot86_tail_days": "tail",
    "ercot75_control_days": "control",
}

_S2_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
_S2_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
_READ_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "HASL",
    "LSL",
    "Base Point",
] + [c for pair in zip(_S2_MW, _S2_PR) for c in pair]


# ---------------------------------------------------------------------------
# Shared ladder arithmetic — one implementation, both sides
# ---------------------------------------------------------------------------
def _ladder(
    prices: np.ndarray, widths: np.ndarray, start: float
) -> tuple[np.ndarray, float] | None:
    """Read the offer ladder at :data:`BAND_OFFSETS_GW` above ``start``.

    Args:
        prices: Offer price of each MW block.
        widths: MW of each block, parallel to ``prices``.
        start: The realized dispatch MW the band sits above.

    Returns:
        ``(prices_at_offsets, headroom_mw)``; offsets past the top of the
        stack read ``NaN`` rather than clipping to the last rung (clipping
        would report a 38 MW junk-peaker tail as if it were the whole band).
        ``None`` when there is no headroom at all.
    """
    order = np.argsort(prices, kind="stable")
    pr = prices[order]
    cum = np.cumsum(widths[order])
    headroom = float(cum[-1]) - float(start)
    if headroom <= 0:
        return None
    out = np.full(len(BAND_OFFSETS_GW), np.nan)
    for i, off in enumerate(BAND_OFFSETS_GW):
        pt = start + off * 1000.0
        if pt > cum[-1]:
            continue
        out[i] = pr[min(int(np.searchsorted(cum, pt, side="left")), len(pr) - 1)]
    return out, headroom


def _band_slice(
    prices: np.ndarray, widths: np.ndarray, start: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """The ``(price, mw, order_index)`` blocks in the first SHARE_BAND_GW above ``start``."""
    order = np.argsort(prices, kind="stable")
    pr = prices[order]
    w = widths[order]
    cum = np.cumsum(w)
    lo = max(float(start), 0.0)
    hi = lo + SHARE_BAND_GW * 1000.0
    # MW of each block inside (lo, hi].
    inb = np.clip(np.minimum(cum, hi) - np.maximum(cum - w, lo), 0.0, None)
    keep = inb > 0
    if not keep.any():
        return None
    return pr[keep], inb[keep], order[keep]


def _share_above(
    prices: np.ndarray, widths: np.ndarray, start: float
) -> np.ndarray | None:
    """Share of the first SHARE_BAND_GW of headroom offered ABOVE each rung."""
    sl = _band_slice(prices, widths, start)
    if sl is None:
        return None
    pr, mw, _ = sl
    tot = mw.sum()
    if tot <= 0:
        return None
    return np.asarray([mw[pr > r].sum() / tot for r in SHARE_RUNGS])


def _split_within_across(
    prices: np.ndarray, widths: np.ndarray, keys: np.ndarray, start: float
) -> tuple[float, float] | None:
    """Decompose the headroom band into ACROSS- and WITHIN-resource spread.

    Args:
        prices: Offer price per MW block.
        widths: MW per block.
        keys: Resource/plant identity per block.
        start: Dispatch MW the band sits above.

    Returns:
        ``(across, within)`` in $/MWh — the p10-p90 spread of resource-level
        MW-weighted mean offer levels, and the MW-weighted mean of each
        resource's own p10-p90 internal rise, both over the first
        SHARE_BAND_GW of headroom. ``None`` when the band is empty.
    """
    sl = _band_slice(prices, widths, start)
    if sl is None:
        return None
    pr, mw, idx = sl
    df = pd.DataFrame({"p": pr, "w": mw, "k": keys[idx]})
    lev = df.groupby("k").apply(
        lambda g: float(np.average(g["p"], weights=g["w"])), include_groups=False
    )
    across = (
        0.0
        if len(lev) < 2
        else float(np.percentile(lev.to_numpy(), 90) - np.percentile(lev.to_numpy(), 10))
    )
    spans = df.groupby("k")["p"].agg(
        lambda s: float(np.percentile(s, 90) - np.percentile(s, 10))
    )
    wts = df.groupby("k")["w"].sum().reindex(spans.index)
    within = float(np.average(spans.to_numpy(), weights=wts.to_numpy()))
    return across, within


def _summarize(
    ladders: list[np.ndarray],
    shares: list[np.ndarray],
    splits: list[tuple[float, float]],
    headrooms: list[float],
) -> dict:
    """Fold per-interval ladders/shares/splits into the reported record."""
    lad = np.array(ladders)
    med = np.nanmedian(lad, axis=0)
    hr_gw = float(np.median(headrooms)) / 1000.0
    cover = (~np.isnan(lad)).mean(axis=0)
    seg = []
    for i in range(1, len(BAND_OFFSETS_GW)):
        d_gw = BAND_OFFSETS_GW[i] - BAND_OFFSETS_GW[i - 1]
        seg.append(round(float((med[i] - med[i - 1]) / d_gw), 3) if d_gw > 0 else None)
    sh = np.array(shares) if shares else None

    def _r(x: float) -> float | None:
        """Round, mapping NaN (offset past the top of the stack) to null."""
        return None if not np.isfinite(x) else round(float(x), 2)

    return {
        "intervals": int(len(ladders)),
        "headroom_gw_median": round(hr_gw, 3),
        "band_offsets_gw": list(BAND_OFFSETS_GW),
        "ladder_median_usd": [_r(v) for v in med],
        "ladder_p25_usd": [_r(v) for v in np.nanpercentile(lad, 25, axis=0)],
        "ladder_p75_usd": [_r(v) for v in np.nanpercentile(lad, 75, axis=0)],
        "ladder_offset_coverage": [round(float(v), 3) for v in cover],
        "segment_slope_usd_per_gw": [
            None if not np.isfinite(s if s is not None else np.nan) else s for s in seg
        ],
        "share_band_gw": SHARE_BAND_GW,
        "share_rungs_usd": list(SHARE_RUNGS),
        "headroom_share_above": (
            [round(float(v), 4) for v in np.median(sh, axis=0)]
            if sh is not None
            else None
        ),
        "across_resource_spread_usd_median": (
            round(float(np.median([s[0] for s in splits])), 2) if splits else None
        ),
        "within_resource_spread_usd_median": (
            round(float(np.median([s[1] for s in splits])), 2) if splits else None
        ),
    }


# ---------------------------------------------------------------------------
# (a) Model side
# ---------------------------------------------------------------------------
def model_band(state: dict, year: int, days: set[int] | None = None) -> dict:
    """Census the model's evening headroom band on the keeper's own offers.

    For each evening hour, builds the merit-order supply curve of AVAILABLE
    thermal capacity (``pmax x availability``) sorted by that hour's offer
    ``mc_base``, locates the hour's realized thermal dispatch on it from the
    committed class hourlies, and reads the ladder over the headroom above it.

    Args:
        state: ``reconstruct_bundle_fleet`` state.
        year: Solve year.
        days: Optional fleet-clock day-of-year set (0-based) to restrict to,
            so the model is matched to the SCED corpus's own days.

    Returns:
        The band record, plus class occupancy of the headroom.
    """
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    T = mc.shape[1]
    hod = np.arange(T) % 24
    sel = (hod >= EVENING[0]) & (hod <= EVENING[1])
    if days is not None:
        sel &= np.isin(np.arange(T) // 24, sorted(days))
    ev = np.nonzero(sel)[0]

    pg = fa.plant_group
    groups = np.array([str(pg[i]) if pg is not None else "" for i in range(fa.n_gen)])
    therm = np.nonzero(np.isin(groups, THERMAL_GROUPS))[0]
    avail = np.asarray(fa.availability, dtype=float)
    cap = fa.pmax[therm][:, None] * avail[therm, :]
    # Plant identity per LP row, so the within-/across- split is on the same
    # grain as the SCED resource (the CAMPD per-plant bin's plant code).
    plant = np.asarray(fa.plant_code, dtype=object)[therm]

    ch = pd.read_parquet(HOURLY / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    th = (
        ch[ch["klass"].astype(str).isin(MODEL_THERMAL_CLASSES)]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(T))
        .to_numpy(float)
    )

    lads: list[np.ndarray] = []
    shares: list[np.ndarray] = []
    splits: list[tuple[float, float]] = []
    hrs: list[float] = []
    occupancy: dict[str, float] = {}
    for t in ev:
        p = mc[therm, t]
        c = cap[:, t]
        keep = c > 1e-6
        if not keep.any():
            continue
        res = _ladder(p[keep], c[keep], float(th[t]))
        if res is None:
            continue
        lad, headroom = res
        lads.append(lad)
        hrs.append(headroom)
        s = _share_above(p[keep], c[keep], float(th[t]))
        if s is not None:
            shares.append(s)
        sp = _split_within_across(p[keep], c[keep], plant[keep], float(th[t]))
        if sp is not None:
            splits.append(sp)
        order = np.argsort(p[keep], kind="stable")
        rows = np.nonzero(keep)[0][order]
        cw = c[keep][order]
        inband = np.cumsum(cw) > th[t]
        for r, w in zip(rows[inband], cw[inband]):
            g = groups[therm[r]]
            occupancy[g] = occupancy.get(g, 0.0) + float(w)

    if not lads:
        return {}
    rec = _summarize(lads, shares, splits, hrs)
    tot = sum(occupancy.values()) or 1.0
    rec["class_occupancy_share"] = {
        g: round(v / tot, 4)
        for g, v in sorted(occupancy.items(), key=lambda kv: -kv[1])
        if v > 0
    }
    rec["evening_dispatch_gw_mean"] = round(float(np.nanmean(th[ev])) / 1000.0, 3)
    cap_ev = cap[:, ev].sum(axis=0)
    rec["available_thermal_gw_mean"] = round(float(np.nanmean(cap_ev)) / 1000.0, 3)
    rec["loading_factor"] = round(
        float(np.nanmean(th[ev]) / max(np.nanmean(cap_ev), 1e-9)), 4
    )
    return rec


# ---------------------------------------------------------------------------
# (c) Commitment state — the model's headroom against the real market's
# ---------------------------------------------------------------------------
def sced_commitment_state(year: int) -> dict:
    """Measure ERCOT's own evening thermal commitment state, per extract.

    The decisive (c) statistic. The model's LP has no integer commitment, so
    every non-outaged unit is dispatchable from zero in any hour at its
    marginal cost; ERCOT's SCED can only move resources that are already
    ONLINE and inside their ramp. This measures how much thermal capacity is
    online, how hard it is loaded, and how much sits offline and therefore
    absent from the real 5-minute stack entirely.
    """
    out: dict = {}
    for path in sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    ):
        token = path.stem.split(f"{year}_", 1)[-1]
        df = pd.read_parquet(
            path,
            columns=[
                "SCED Time Stamp",
                "Resource Name",
                "Resource Type",
                "Telemetered Resource Status",
                "HSL",
                "HASL",
                "LSL",
                "Base Point",
            ],
        )
        rt = df["Resource Type"].astype(str).str.strip()
        df = _prepare(df[rt.isin(SCED_THERMAL_TYPES)].copy())
        df = df[(df["hod"] >= EVENING[0]) & (df["hod"] <= EVENING[1])]
        if df.empty:
            continue
        on = df[df["stat"].isin(ONLINE_STATES)]
        off = df[~df["stat"].isin(ONLINE_STATES)]
        g = on.groupby("_ts").agg(
            hsl=("HSL", "sum"),
            hasl=("HASL", "sum"),
            bp=("Base Point", "sum"),
            n=("Resource Name", "nunique"),
        )
        go = off.groupby("_ts").agg(
            hsl_off=("HSL", "sum"), n_off=("Resource Name", "nunique")
        )
        out[token] = {
            "day_class": DAY_CLASS.get(token, token),
            "online_resources_median": float(g["n"].median()),
            "offline_resources_median": float(go["n_off"].median()),
            "online_hsl_gw_median": round(float(g["hsl"].median()) / 1000.0, 3),
            "online_hasl_gw_median": round(float(g["hasl"].median()) / 1000.0, 3),
            "base_point_gw_median": round(float(g["bp"].median()) / 1000.0, 3),
            "energy_headroom_gw_median": round(
                float((g["hasl"] - g["bp"]).median()) / 1000.0, 3
            ),
            "as_carveout_gw_median": round(
                float((g["hsl"] - g["hasl"]).median()) / 1000.0, 3
            ),
            "offline_thermal_hsl_gw_median": round(
                float(go["hsl_off"].median()) / 1000.0, 3
            ),
            "loading_factor": round(float((g["bp"] / g["hsl"]).median()), 4),
        }
    return out


# ---------------------------------------------------------------------------
# (b) Real-market side
# ---------------------------------------------------------------------------
def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Attach the CPT -> fixed-CST clock, hour-of-day and telemetered status."""
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    out = df.loc[np.asarray(ok)].copy()
    out["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    out["hod"] = hh[ok]
    out["stat"] = out["Telemetered Resource Status"].astype(str).str.strip()
    out["_ts"] = ts.to_numpy()[np.asarray(ok)]
    return out


def _segments(df: pd.DataFrame) -> pd.DataFrame:
    """AS-net offer segments of the SCED2 curves, spanning ``[0, HASL]``.

    One row per (interval-resource, curve step) slice in
    ``(max(prev_step, LSL, 0), min(step MW, HASL)]`` at the step's price,
    clipped to HCAP -- the ERCOT-86/87/88 construction, imported in form from
    ERCOT-154 so edges and the clock cannot drift. The HASL cap means the
    ladder prices only the energy headroom each resource's AS award leaves to
    energy.

    A resource's must-take ``[0, LSL]`` block is emitted too, priced at its own
    first curve step. Without it the stack would start at LSL while the
    dispatch point (Base Point) is measured from zero, so every interval would
    read as having negative headroom -- both sides must span the same
    ``[0, cap]`` domain for the offsets above the dispatch point to line up.
    The block itself sits below the dispatch point in every interval, so its
    price never enters a reported rung.
    """
    MW = df[_S2_MW].to_numpy(float)
    PR = df[_S2_PR].to_numpy(float)
    lsl = np.maximum(np.nan_to_num(df["LSL"].to_numpy(float), nan=0.0), 0.0)
    hasl = np.nan_to_num(df["HASL"].to_numpy(float), nan=0.0)
    cols = {
        "ts": df["_ts"].to_numpy(),
        "hod": df["hod"].to_numpy(int),
        "res": df["Resource Name"].to_numpy(),
    }
    seg: dict[str, list[np.ndarray]] = {k: [] for k in (*cols, "mw", "pr")}

    # The must-take [0, LSL] block, at the resource's own first finite step.
    first = np.full(len(df), np.nan)
    for k in range(PR.shape[1]):
        need = ~np.isfinite(first)
        if not need.any():
            break
        first = np.where(need & np.isfinite(PR[:, k]), PR[:, k], first)
    base_mw = np.minimum(lsl, hasl)
    take = (base_mw > 0) & np.isfinite(first)
    if take.any():
        seg["mw"].append(base_mw[take])
        seg["pr"].append(np.minimum(first[take], HCAP_USD_MWH))
        for name, arr in cols.items():
            seg[name].append(arr[take])

    prev = lsl.copy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        mw = np.where(
            valid, np.maximum(np.minimum(q, hasl) - np.maximum(prev, lsl), 0.0), 0.0
        )
        take = mw > 0
        if take.any():
            seg["mw"].append(mw[take])
            seg["pr"].append(np.minimum(p[take], HCAP_USD_MWH))
            for name, arr in cols.items():
                seg[name].append(arr[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    if not seg["mw"]:
        return pd.DataFrame()
    out = pd.DataFrame({k: np.concatenate(v) for k, v in seg.items()})
    return out.rename(columns={"pr": "price"})


def sced_band(year: int) -> dict:
    """Measure the real market's evening headroom band, per committed extract.

    The dispatch point is the interval's own summed Base Point over the same
    online thermal resources whose curves build the stack, so the band is
    normalized exactly as the model side is.
    """
    out: dict = {}
    for path in sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    ):
        token = path.stem.split(f"{year}_", 1)[-1]
        df = pd.read_parquet(path, columns=_READ_COLS)
        rt = df["Resource Type"].astype(str).str.strip()
        df = df[rt.isin(SCED_THERMAL_TYPES)].copy()
        if df.empty:
            continue
        df = _prepare(df)
        df = df[df["stat"].isin(ONLINE_STATES)]
        df = df[(df["hod"] >= EVENING[0]) & (df["hod"] <= EVENING[1])]
        if df.empty:
            continue
        seg = _segments(df)
        if seg.empty:
            continue
        # Dispatch point: the interval's own summed Base Point over exactly the
        # resources whose curves build the stack, capped at HASL so a Base
        # Point above the AS-net limit cannot manufacture negative headroom.
        bp = (
            df.assign(
                _bp=np.minimum(
                    np.nan_to_num(df["Base Point"].to_numpy(float), nan=0.0),
                    np.nan_to_num(df["HASL"].to_numpy(float), nan=0.0),
                )
            )
            .groupby("_ts")["_bp"]
            .sum()
        )
        lads: list[np.ndarray] = []
        shares: list[np.ndarray] = []
        splits: list[tuple[float, float]] = []
        hrs: list[float] = []
        for ts, g in seg.groupby("ts"):
            start = float(bp.get(ts, 0.0))
            pr = g["price"].to_numpy(float)
            w = g["mw"].to_numpy(float)
            res = _ladder(pr, w, start)
            if res is None:
                continue
            lad, headroom = res
            lads.append(lad)
            hrs.append(headroom)
            s = _share_above(pr, w, start)
            if s is not None:
                shares.append(s)
            sp = _split_within_across(pr, w, g["res"].to_numpy(), start)
            if sp is not None:
                splits.append(sp)
        if not lads:
            continue
        rec = _summarize(lads, shares, splits, hrs)
        rec["source_file"] = path.name
        rec["day_class"] = DAY_CLASS.get(token, token)
        rec["days"] = int(pd.to_datetime(df["_ts"]).dt.date.nunique())
        rec["resources"] = int(df["Resource Name"].nunique())
        rec["model_days"] = sorted({int(h) // 24 for h in df["hoy"].to_numpy(int)})
        out[token] = rec
    return out


def _fmt(r: dict) -> str:
    """One-line console summary of a band record."""
    lad = " ".join(
        f"{o:g}GW=" + ("  n/a" if v is None else f"${v:.0f}")
        for o, v in zip(BAND_OFFSETS_GW, r["ladder_median_usd"])
    )
    return (
        f"{r['intervals']:6d} iv, headroom {r['headroom_gw_median']:5.2f} GW | {lad}"
    )


def main(argv: list[str] | None = None) -> int:
    """Run the Phase-1 census and write the committed JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args(argv)

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    out: dict = {
        "bundle": str(BUNDLE.relative_to(REPO)),
        "evening_block_cst": list(EVENING),
        "share_rungs_usd": list(SHARE_RUNGS),
        "sced_thermal_types": list(SCED_THERMAL_TYPES),
        "sced_online_states": list(ONLINE_STATES),
        "model": {},
        "sced": {},
        "matched": {},
        "commitment_state": {},
    }

    # (b)/(c) first -- the SCED day sets scope the matched model read.
    for year in args.years:
        rec = sced_band(year)
        if rec:
            out["sced"][str(year)] = rec
            for tok, r in rec.items():
                print(f"SCED  {year} {tok:22s} ({r['day_class']:7s}): {_fmt(r)}")
        cs = sced_commitment_state(year)
        if cs:
            out["commitment_state"][str(year)] = cs
            for tok, c in cs.items():
                print(
                    f"CMMT  {year} {tok:22s} ({c['day_class']:7s}): online "
                    f"{c['online_resources_median']:4.0f} res / "
                    f"{c['online_hsl_gw_median']:5.2f} GW HSL at "
                    f"{100 * c['loading_factor']:5.1f}% load -> energy headroom "
                    f"{c['energy_headroom_gw_median']:5.2f} GW | OFFLINE "
                    f"{c['offline_resources_median']:4.0f} res / "
                    f"{c['offline_thermal_hsl_gw_median']:5.2f} GW"
                )

    for year in args.years:
        state, _meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=True)
        rec = model_band(state, year)
        out["model"][str(year)] = rec
        print(f"MODEL {year} all-evening               : {_fmt(rec)}")
        print(
            f"      available thermal {rec['available_thermal_gw_mean']:5.2f} GW, "
            f"dispatch {rec['evening_dispatch_gw_mean']:5.2f} GW, loading "
            f"{100 * rec['loading_factor']:5.1f}%"
        )
        print(f"      occupancy {rec['class_occupancy_share']}")
        for tok, r in out["sced"].get(str(year), {}).items():
            m = model_band(state, year, days=set(r["model_days"]))
            out["matched"].setdefault(str(year), {})[tok] = m
            print(f"MODEL {year} matched {tok:22s}    : {_fmt(m)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
