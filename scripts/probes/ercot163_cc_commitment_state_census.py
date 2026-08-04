"""ERCOT-163 Phase 0 — is the model's cheap CC offline depth PHANTOM?

NO LP, no solve, no mechanism armed, keeper UNCHANGED
(``2026-08-03-ercot158-pool-arm``).

**The question.** ERCOT-162 closed the storage OFFER-PRICE lane with a decisive
``R``: the measured multi-tranche battery RT offer surface lifted the top-100
2023 gap hours only +$16 because the model's crossing never runs deep into the
tranches — a cheap combined-cycle block absorbs the load first and caps the
price. ERCOT-151 §0.2/§0.4 attributed that block, on the **60-Day DAM**
disclosure, as ``10.3 GW of startable-but-OFF CC, 8.2 GW of it <= $200`` at the
missed tail hours, and ERCOT-152 refused to RE-PRICE it (measured no-op),
upheld at ERCOT-158. This probe asks the availability question instead, on the
**RT telemetry** the DAM disclosure cannot see:

    At the committed top-100 gap hours, does reality carry the same multi-GW
    block of cheap OFFLINE-startable CC that the model's merit order carries,
    or was that capacity already COMMITTED (dispatched, not spare) or
    UNAVAILABLE (on outage), so the real crossing had to climb past it?

**Construction.** Every ERCOT CC/CT SCED resource is given a fixed capability
reference ``cap_ref`` = its p98 telemetered HSL over delivery-2023 (pass 1), so
the state accounting has a FIXED denominator and a resource that stops
telemetering entirely is not silently dropped — it lands in an explicit
``ABSENT`` state (pass 2). At each hour set every resource's ``cap_ref`` is
attributed to the state it telemetered:

    ONLINE (ON/ONREG/ONRR/ONOS/ONRUC/...)  — committed; its energy-side
                                             increment is HASL - Base Point
    ONTEST                                 — online, out of market (ERCOT-154
                                             population discipline)
    OFFLINE_STARTABLE (OFFQS/OFFNS)        — the ERCOT-88 pool states
    OFFLINE_OTHER (OFF/...)                — offline, not intra-hour startable
    OUT                                    — unavailable (outage)
    TRANSITION (STARTUP/SHUTDOWN), OTHER, ABSENT

against the model's own CC availability/dispatch/bid ladder reconstructed from
the keeper bundle (no LP). Four hour sets are scored so the ORDINARY-hour
commitment level — the object ERCOT-159's rejection re-pointed at — is measured
on the same instrument as the gap hours: ``gap`` (the committed top-100),
``bin6_nongap`` (the wall's top net-load bin minus the gap hours),
``summer_afternoon_nongap`` (Jun-Sep h13-19, gap hours removed) and ``all``.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot163_cc_commitment_state_census.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    REPO,
    REPO / "src",
    REPO / "scripts",
    REPO / "scripts" / "data",
    Path(__file__).resolve().parent,
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = REPO / "results/calibration/ercot158_poolarm_B"
HOURLY = BUNDLE / "hourly"
PHASE0_JSON = REPO / "results/calibration/_ercot161_wall_phase0.json"
DEFAULT_OUT = REPO / "results/calibration/_ercot163_cc_commitment.json"
YEAR = 2023

#: SCED ``Resource Type`` -> the census class. CCGT90/CCLE90 are the combined
#: cycle trains (>= / < 90 MW); SCGT90/SCLE90 the simple-cycle CTs — the same
#: keys ``derive_ercot_sced_offer_wall`` / ``derive_ercot_faststart_pool`` use.
CLASS_OF_RESTYPE = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT",
    "SCLE90": "CT",
}

#: Model ``plant_group`` values mapped onto each census class. CC_CHP is
#: carried separately as well: an unknown share of ERCOT cogeneration sits
#: behind private-use networks and never telemeters to SCED, so the
#: CC_REGULAR-only comparison is the crosswalk-clean one and the CC-total
#: comparison is the upper bound (disclosed, never silently merged).
MODEL_GROUPS = {
    "CC": ("CC_REGULAR", "CC_CHP"),
    "CC_REGULAR_ONLY": ("CC_REGULAR",),
    "CT": ("CT_PEAKER", "CT_CHP"),
}

#: Telemetered status -> capability state. Anything unlisted whose status
#: starts with ``ON`` is ONLINE, with ``OFF`` is OFFLINE_OTHER, with ``OUT`` is
#: OUT; the remainder is OTHER (never silently dropped — the raw per-status
#: table is emitted alongside).
STATE_OF_STATUS = {
    "ONTEST": "ONTEST",
    "OFFQS": "OFFLINE_STARTABLE",
    "OFFNS": "OFFLINE_STARTABLE",
    "STARTUP": "TRANSITION",
    "SHUTDOWN": "TRANSITION",
}
STATES = (
    "ONLINE",
    "ONTEST",
    "OFFLINE_STARTABLE",
    "OFFLINE_OTHER",
    "OUT",
    "TRANSITION",
    "OTHER",
    "ABSENT",
)

#: Absolute-$ bands for the offer ladders (the ERCOT-161 stack-census bands).
PRICE_BANDS = (0.0, 100.0, 200.0, 300.0, 500.0, 1000.0, 2000.0, float("inf"))

#: MW-weighted quantiles reported for every measured offer ladder.
LADDER_Q = (0.1, 0.3, 0.5, 0.7, 0.9, 0.99)

#: Offer-ladder price grid ($1 bins spanning the ERCOT offer floor/cap, LCAP
#: -$251 .. HCAP $5,000). Ladders are accumulated as MW histograms rather than
#: raw segment arrays so the whole-year hour set cannot blow memory; quantiles
#: are exact to the $1 bin.
_PR_LO, _PR_HI = -251.0, 5000.0
_PR_EDGES = np.arange(_PR_LO, _PR_HI + 2.0, 1.0)
_PR_MID = _PR_EDGES[:-1] + 0.5

_S2_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
_S2_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
_LIGHT_COLS = ["SCED Time Stamp", "Resource Name", "Resource Type", "HSL"]
_FULL_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "HASL",
    "LSL",
    "Base Point",
] + [c for pair in zip(_S2_MW, _S2_PR) for c in pair]


def _state_of(status: pd.Series) -> np.ndarray:
    """Map stripped telemetered statuses onto the capability-state taxonomy."""
    s = status.astype(str).str.strip().str.upper()
    out = np.full(len(s), "OTHER", dtype=object)
    arr = s.to_numpy()
    for k, v in STATE_OF_STATUS.items():
        out[arr == k] = v
    unset = out == "OTHER"
    out[unset & np.char.startswith(arr.astype(str), "ON")] = "ONLINE"
    out[unset & np.char.startswith(arr.astype(str), "OFF")] = "OFFLINE_OTHER"
    out[unset & np.char.startswith(arr.astype(str), "OUT")] = "OUT"
    for k, v in STATE_OF_STATUS.items():  # explicit map always wins
        out[arr == k] = v
    return out


#: A combined-cycle SCED resource name is ``<TRAIN>_<configuration index>`` and
#: the name CHANGES as the train switches configuration (``BASTEN_CC1_1`` ->
#: ``BASTEN_CC1_2``), so the resource-name universe over a year holds several
#: aliases of the same physical train. Every capability denominator here is
#: therefore taken at TRAIN grain — the ERCOT-151 §0.2 config-inflation trap
#: (its raw name-grain CC block reads 52 GW against a ~34 GW physical fleet).
_CONFIG_SUFFIX = re.compile(r"_(\d+)$")


def _train(name: str) -> str:
    """``BASTEN_CC1_2`` -> ``BASTEN_CC1``; names without a config index unchanged."""
    return _CONFIG_SUFFIX.sub("", str(name))


def _hoy(ts: pd.Series) -> np.ndarray:
    """SCED Time Stamp -> hour-of-year on the model's fixed-standard clock."""
    from derive_ercot_dam_cleared_share import _MONTH_START_HOUR

    t = pd.to_datetime(ts)
    cst = t.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert("Etc/GMT+6")
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    return _MONTH_START_HOUR[mo - 1] + (dy - 1) * 24 + hh


# --------------------------------------------------------------------------
# Model side (no LP — fleet/offer arrays + the committed class sidecar)
# --------------------------------------------------------------------------


def _model_state() -> tuple[dict, dict, np.ndarray]:
    """Reconstruct the keeper's 2023 fleet/offer state and its P1 bid matrix."""
    import ercot161_afternoon_wall_phase0 as e161

    state = e161._reconstruct()
    marks = e161._compose_markups(state)
    geom = e161._wall_geometry(state["config"], marks["net_load"])
    return state, marks, geom["hour_bin"]


def _model_class_dispatch() -> dict[str, np.ndarray]:
    """P1 dispatch (MW) per model class from the keeper's committed sidecar."""
    ch = pd.read_parquet(HOURLY / f"class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    out: dict[str, np.ndarray] = {}
    for klass, d in ch.groupby("klass"):
        out[str(klass)] = d.set_index("hour")["mw"].reindex(range(8760)).to_numpy(float)
    return out


def _model_depth(
    state: dict,
    marks: dict,
    dispatch: dict[str, np.ndarray],
    groups: tuple[str, ...],
    hours: np.ndarray,
) -> dict:
    """Available / dispatched / undispatched-by-bid-band for a model class.

    The undispatched block is taken cheapest-first: the class's own P1 bids
    are sorted at each hour and the sidecar dispatch consumes the cheapest
    capacity, so the remainder is exactly the depth the crossing had still to
    climb through inside this class.
    """
    fa = state["fleet_arrays"]
    pg = np.asarray(fa.plant_group)
    m = np.isin(pg, list(groups))
    avail = fa.pmax[m][:, None] * fa.availability[m][:, hours]  # (n, H)
    bid = marks["mc_bid"][m][:, hours]
    disp = np.zeros(len(hours), dtype=float)
    for k in groups:
        if k in dispatch:
            disp = disp + dispatch[k][hours]

    order = np.argsort(bid, axis=0, kind="stable")
    a_s = np.take_along_axis(avail, order, axis=0)
    b_s = np.take_along_axis(bid, order, axis=0)
    cum = np.cumsum(a_s, axis=0)
    # MW of each sorted row left UNDISPATCHED once `disp` MW is consumed.
    consumed = np.clip(disp[None, :] - (cum - a_s), 0.0, a_s)
    left = a_s - consumed

    tot = avail.sum(axis=0)
    bands: dict[str, float] = {}
    left_le: dict[str, float] = {}
    for lo, hi in zip(PRICE_BANDS[:-1], PRICE_BANDS[1:]):
        sel = (b_s >= lo) & (b_s < hi)
        bands[f"{lo:g}-{hi:g}"] = round(float((a_s * sel).sum(axis=0).mean()) / 1e3, 4)
    for cap in (100.0, 200.0, 300.0, 500.0, 1000.0):
        left_le[f"le_{cap:g}"] = round(
            float((left * (b_s <= cap)).sum(axis=0).mean()) / 1e3, 4
        )
    # Bid of the marginal row inside the class (first row with capacity left).
    has_left = left > 1e-9
    idx = np.where(has_left.any(axis=0), has_left.argmax(axis=0), a_s.shape[0] - 1)
    marg = b_s[idx, np.arange(len(hours))]
    return {
        "n_hours": int(len(hours)),
        "mean_gw_available": round(float(tot.mean()) / 1e3, 4),
        "mean_gw_dispatched": round(float(disp.mean()) / 1e3, 4),
        "mean_gw_undispatched": round(float((tot - disp).mean()) / 1e3, 4),
        "mean_utilisation": round(float((disp / np.maximum(tot, 1e-9)).mean()), 4),
        "mean_gw_undispatched_by_bid_cap": left_le,
        "mean_gw_available_by_bid_band": bands,
        "marginal_bid_within_class": {
            "p10": round(float(np.percentile(marg, 10)), 2),
            "p50": round(float(np.median(marg)), 2),
            "p90": round(float(np.percentile(marg, 90)), 2),
        },
        "max_bid_in_class_p50_over_hours": round(float(np.median(b_s[-1, :])), 2),
    }


# --------------------------------------------------------------------------
# Reality side (SCED telemetry)
# --------------------------------------------------------------------------


def _cap_ref(files: list[Path]) -> tuple[pd.Series, pd.Series]:
    """Pass 1 — per-TRAIN capability reference (p98 HSL) and its class.

    p98 rather than max: a handful of intervals telemeter a transient HSL
    spike above the registered rating, and the reference is a denominator, so
    a robust upper quantile is the honest one. Keyed by :func:`_train`, so a
    train's configuration aliases collapse into one capability (see
    ``_CONFIG_SUFFIX``).
    """
    from derive_ercot_sced_offer_wall import _delivery_year_rows

    hsl: dict[str, list[np.ndarray]] = {}
    cls: dict[str, str] = {}
    for path in files:
        df = pd.read_parquet(path, columns=_LIGHT_COLS)
        df = _delivery_year_rows(df, YEAR)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        if df.empty:
            continue
        df["HSL"] = pd.to_numeric(df["HSL"], errors="coerce")
        df["train"] = df["Resource Name"].map(_train)
        for name, d in df.groupby("train"):
            hsl.setdefault(str(name), []).append(d["HSL"].to_numpy(float))
            cls[str(name)] = CLASS_OF_RESTYPE[str(d["Resource Type"].iloc[0])]
    ref = {
        n: float(np.nanpercentile(np.concatenate(v), 98))
        for n, v in hsl.items()
        if np.isfinite(np.concatenate(v)).any()
    }
    return pd.Series(ref, dtype=float), pd.Series(cls, dtype=object)


def _segments(
    df: pd.DataFrame, lo_col: str, hi_col: str
) -> tuple[np.ndarray, np.ndarray]:
    """(MW, price) of the SCED2 curve slices inside ``(lo_col, hi_col]``.

    The ERCOT-86/87/88 segment construction: one slice per curve step in
    ``(max(prev_step, lo), min(step_MW, hi)]`` at the step's price. Used with
    ``lo=LSL, hi=HASL`` for offline-startable rows (the fast-start-pool
    construction) and ``lo=Base Point, hi=HASL`` for online spare.
    """
    MW = df[_S2_MW].to_numpy(float)
    PR = df[_S2_PR].to_numpy(float)
    lo = np.maximum(np.nan_to_num(df[lo_col].to_numpy(float), nan=0.0), 0.0)
    hi = df[hi_col].to_numpy(float)
    mws: list[np.ndarray] = []
    prs: list[np.ndarray] = []
    prev = lo.copy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        mw = np.where(
            valid, np.maximum(np.minimum(q, hi) - np.maximum(prev, lo), 0.0), 0.0
        )
        take = mw > 0
        if take.any():
            mws.append(mw[take])
            prs.append(p[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    if not mws:
        return np.zeros(0), np.zeros(0)
    return np.concatenate(mws), np.concatenate(prs)


def _hist_add(hist: np.ndarray, mw: np.ndarray, pr: np.ndarray) -> None:
    """Accumulate segment MW into the shared $1 price histogram, in place."""
    if mw.size == 0:
        return
    idx = np.clip(
        np.searchsorted(_PR_EDGES, np.clip(pr, _PR_LO, _PR_HI), side="right") - 1,
        0,
        len(_PR_MID) - 1,
    )
    np.add.at(hist, idx, mw)


def _ladder(hist: np.ndarray, n_iv: int) -> dict:
    """MW-weighted quantiles + per-interval mean GW by band, from the histogram."""
    tot = float(hist.sum())
    if tot <= 0:
        return {"total_mean_gw": 0.0, "quantiles": {}, "mean_gw_by_band": {}}
    cw = np.cumsum(hist) / tot
    qs = {
        f"p{int(q * 100)}": round(float(_PR_MID[int(np.searchsorted(cw, q))]), 2)
        for q in LADDER_Q
    }
    bands = {
        f"{lo:g}-{hi:g}": round(
            float(hist[(_PR_MID >= lo) & (_PR_MID < hi)].sum()) / n_iv / 1e3, 4
        )
        for lo, hi in zip(PRICE_BANDS[:-1], PRICE_BANDS[1:])
    }
    return {
        "total_mean_gw": round(tot / n_iv / 1e3, 4),
        "quantiles": qs,
        "mean_gw_by_band": bands,
    }


def _reality(files: list[Path], hour_sets: dict[str, np.ndarray]) -> dict:
    """Pass 2 — capability-state census + measured offer ladders per hour set."""
    from derive_ercot_sced_offer_wall import _delivery_year_rows

    ref, cls = _cap_ref(files)
    fleet_cap = {c: float(ref[cls[ref.index] == c].sum()) for c in ("CC", "CT")}

    keep = {k: np.asarray(sorted(int(h) for h in v)) for k, v in hour_sets.items()}
    keep_mask = {k: np.zeros(8760, dtype=bool) for k in keep}
    for k, v in keep.items():
        keep_mask[k][v] = True

    # accumulators: [set][class][state] -> MW ; and interval counters
    acc_cap: dict = {}
    acc_hsl: dict = {}
    acc_bp: dict = {}
    acc_hasl: dict = {}
    acc_status: dict = {}
    seen_iv: dict = {k: set() for k in keep}
    off_hist = {k: {c: np.zeros(len(_PR_MID)) for c in ("CC", "CT")} for k in keep}
    on_hist = {k: {c: np.zeros(len(_PR_MID)) for c in ("CC", "CT")} for k in keep}
    n_res: dict = {k: {c: set() for c in ("CC", "CT")} for k in keep}
    for k in keep:
        acc_cap[k] = {c: dict.fromkeys(STATES, 0.0) for c in ("CC", "CT")}
        acc_hsl[k] = {c: dict.fromkeys(STATES, 0.0) for c in ("CC", "CT")}
        acc_bp[k] = {c: dict.fromkeys(STATES, 0.0) for c in ("CC", "CT")}
        acc_hasl[k] = {c: dict.fromkeys(STATES, 0.0) for c in ("CC", "CT")}
        acc_status[k] = {c: {} for c in ("CC", "CT")}

    num_cols = [
        c
        for c in _FULL_COLS
        if c
        not in (
            "SCED Time Stamp",
            "Resource Name",
            "Resource Type",
            "Telemetered Resource Status",
        )
    ]
    for path in files:
        df = pd.read_parquet(path, columns=_FULL_COLS)
        df = _delivery_year_rows(df, YEAR)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)].copy()
        if df.empty:
            continue
        df["hoy"] = _hoy(df["SCED Time Stamp"])
        df = df[(df["hoy"] >= 0) & (df["hoy"] < 8760)]
        if df.empty:
            continue
        df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
        df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
        df["state"] = _state_of(df["Telemetered Resource Status"])
        df["status"] = df["Telemetered Resource Status"].astype(str).str.strip()
        df["train"] = df["Resource Name"].map(_train)
        df["cap_ref"] = df["train"].map(ref).fillna(0.0)
        for c in ("HSL", "HASL", "Base Point"):
            df[c] = df[c].fillna(0.0)
        hoy = df["hoy"].to_numpy(int)

        for k in keep:
            sub = df.loc[keep_mask[k][hoy]]
            if sub.empty:
                continue
            seen_iv[k].update(sub["SCED Time Stamp"].unique().tolist())
            agg = sub.groupby(["cls", "state"], observed=True)[
                ["cap_ref", "HSL", "Base Point", "HASL"]
            ].sum()
            for (c, st), row in agg.iterrows():
                acc_cap[k][c][st] += float(row["cap_ref"])
                acc_hsl[k][c][st] += float(row["HSL"])
                acc_bp[k][c][st] += float(row["Base Point"])
                acc_hasl[k][c][st] += float(row["HASL"])
            for (c, s0), v in (
                sub.groupby(["cls", "status"], observed=True)["HSL"].sum().items()
            ):
                acc_status[k][c][s0] = acc_status[k][c].get(s0, 0.0) + float(v)
            for c in ("CC", "CT"):
                cc_rows = sub[sub["cls"] == c]
                if cc_rows.empty:
                    continue
                n_res[k][c].update(cc_rows["train"].unique().tolist())
                offs = cc_rows[cc_rows["state"] == "OFFLINE_STARTABLE"]
                if not offs.empty:
                    _hist_add(off_hist[k][c], *_segments(offs, "LSL", "HASL"))
                ons = cc_rows[cc_rows["state"] == "ONLINE"]
                if not ons.empty:
                    _hist_add(on_hist[k][c], *_segments(ons, "Base Point", "HASL"))

    out: dict = {
        "fleet_cap_ref_gw": {c: round(v / 1e3, 4) for c, v in fleet_cap.items()}
    }
    for k in keep:
        n_iv = max(len(seen_iv[k]), 1)
        blk: dict = {"n_hours": len(keep[k]), "n_intervals": n_iv, "classes": {}}
        for c in ("CC", "CT"):
            cap = dict(acc_cap[k][c])
            present = sum(cap.values())
            cap["ABSENT"] = max(fleet_cap[c] * n_iv - present, 0.0)
            on_cap = cap["ONLINE"]
            startable = cap["OFFLINE_STARTABLE"]
            blk["classes"][c] = {
                "mean_gw_capref_by_state": {
                    s: round(cap[s] / n_iv / 1e3, 4) for s in STATES
                },
                "mean_gw_hsl_by_state": {
                    s: round(acc_hsl[k][c].get(s, 0.0) / n_iv / 1e3, 4) for s in STATES
                },
                "mean_gw_basepoint_by_state": {
                    s: round(acc_bp[k][c].get(s, 0.0) / n_iv / 1e3, 4) for s in STATES
                },
                "mean_gw_hasl_online": round(
                    acc_hasl[k][c].get("ONLINE", 0.0) / n_iv / 1e3, 4
                ),
                "mean_gw_hsl_by_status": {
                    s: round(v / n_iv / 1e3, 4)
                    for s, v in sorted(acc_status[k][c].items(), key=lambda kv: -kv[1])
                },
                "committed_share_of_capref": round(
                    on_cap / max(present + cap["ABSENT"], 1e-9), 4
                ),
                "offline_startable_share_of_capref": round(
                    startable / max(present + cap["ABSENT"], 1e-9), 4
                ),
                "online_loading": round(
                    acc_bp[k][c].get("ONLINE", 0.0)
                    / max(acc_hsl[k][c].get("ONLINE", 0.0), 1e-9),
                    4,
                ),
                "n_resources_present": len(n_res[k][c]),
                "offline_startable_offer_ladder": _ladder(off_hist[k][c], n_iv),
                "online_spare_offer_ladder": _ladder(on_hist[k][c], n_iv),
            }
        out[k] = blk
    return out


# --------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    from derive_ercot_sced_offer_wall import _sced_source_files

    t0 = time.time()
    gap = np.array(
        sorted(int(h) for h in json.loads(PHASE0_JSON.read_text())["hour_set"]["hours"])
    )
    state, marks, hour_bin = _model_state()
    n_bins = int(hour_bin.max())
    bin_top = np.flatnonzero(hour_bin >= n_bins)
    bin6_nongap = np.setdiff1d(bin_top, gap)
    months = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h").month.to_numpy()
    hod = np.arange(8760) % 24
    summer = np.flatnonzero(np.isin(months, (6, 7, 8, 9)) & (hod >= 13) & (hod <= 19))
    hour_sets = {
        "gap": gap,
        "bin6_nongap": bin6_nongap,
        "summer_afternoon_nongap": np.setdiff1d(summer, gap),
        "all": np.arange(8760),
    }

    dispatch = _model_class_dispatch()
    model: dict = {}
    for label, groups in MODEL_GROUPS.items():
        model[label] = {
            k: _model_depth(state, marks, dispatch, groups, v)
            for k, v in hour_sets.items()
        }

    files = _sced_source_files(YEAR)
    reality = _reality(files, hour_sets)

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot163_cc_commitment_state_census.py",
            "session": "ercot-163 Phase 0 (no LP, no solve, keeper unchanged)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper": "2026-08-03-ercot158-pool-arm",
            "year": YEAR,
            "hour_set_source": str(PHASE0_JSON.relative_to(REPO)),
            "n_sced_shards": len(files),
            "cap_ref": (
                "per-TRAIN p98 telemetered HSL over delivery-2023 (configuration "
                "aliases collapsed on the trailing _<config> segment)"
            ),
            "states": list(STATES),
            "elapsed_s": None,
        },
        "hour_sets": {k: int(len(v)) for k, v in hour_sets.items()},
        "model": model,
        "reality": reality,
    }
    out["_provenance"]["elapsed_s"] = round(time.time() - t0, 1)
    args.out.write_text(json.dumps(out, indent=1))

    g = reality["gap"]["classes"]["CC"]
    m = model["CC"]["gap"]
    print(f"\n--- CC at the {len(gap)} gap hours ---")
    print(" reality cap_ref state GW:", g["mean_gw_capref_by_state"])
    print(" reality online loading:", g["online_loading"])
    print(" reality offline-startable ladder:", g["offline_startable_offer_ladder"])
    print(
        f" model available {m['mean_gw_available']} GW / dispatched "
        f"{m['mean_gw_dispatched']} GW / undispatched {m['mean_gw_undispatched']} GW"
    )
    print(" model undispatched by bid cap:", m["mean_gw_undispatched_by_bid_cap"])
    print(f"wrote {args.out} ({out['_provenance']['elapsed_s']} s)")


if __name__ == "__main__":
    main()
