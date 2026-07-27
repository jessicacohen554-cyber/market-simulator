#!/usr/bin/env python
"""ERCOT-123 — what the unoffered 83 % of coal DAM headroom does in real time.

Phase 1 of the lane chartered by
``docs/DIAGNOSIS-ercot122-coal-offer-envelope-2026-07-27.md`` §4/§5.4. That
session measured, from the 60-Day **DAM** disclosure, that only 0.161-0.184 of
online coal operating headroom carries any submitted incremental DAM energy
offer (CC control 0.594-0.677), and deliberately built no mechanism because
DAM reach alone cannot say whether the unoffered remainder is **withheld**,
**self-scheduled** (price-taking), or simply **priced in RT** through SCED's
three-part offer. This probe reads that third instrument — the 60-Day SCED
disclosure's ``Submitted TPO`` curves — and decomposes the headroom into
mutually exclusive, exhaustive buckets.

Diagnostic only: no LP is built, no year is solved, nothing is registered, and
no ``ScenarioConfig`` field or solve path is touched. Rule 23 is honoured — every
quantity here is read from the raw disclosure against the charter's measurement
question; no residual enters any derivation.

Sections
--------
A  headroom decomposition (buckets a/b/c/e over the telemetered range)
B  the RT offer LEVEL — price distribution of the offered bucket
C  the AS-reservation cross-check (HSL-HASL against the awarded AS block)
D  the derate layer (bucket d) — HSL against each resource's own reference
E  Telemetered Net Output reconciled against the EIA-930 bench coal actuals
F  DAM reach reproduced on the SAME probe days (the sampling check)
G  hour-of-day bias bound, from the one subset that covers all 24 hours

SAMPLING — carry this caveat on every number
--------------------------------------------
The on-disk SCED subsets are **probe days, not a full span**: 82 delivery days
across 2024-2025 only (no 2023 SCED exists on disk), and three of the four
subsets sample **only hours 11-22**. Only ``2025_ercot86_tail_days`` covers all
24 hours, on 11 days. Nothing here is an annual statistic; §G bounds the
hour-of-day bias directly rather than assuming it away.

Usage
-----
    python scripts/probes/ercot123_coal_sced_reach.py [--json-out PATH]
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from market_sim.config import paths  # noqa: E402

_RAW = paths.RAW_DIR / "ercot"

# Resource Type -> comparison class. CLLIG ("Coal and Lignite") is the ONLY
# steam-coal code: SCLE90/SCGT90 are simple-cycle GAS and GSREH/GSNONR/GSSUP are
# gas steam (the ERCOT-122 session's documented trap). CCGT90/CCLE90 are the CC
# lineage used as the control, matching derive_dam_offer_hrmults.CC_RESOURCE_TYPES.
TYPE_TO_CLASS: dict[str, str] = {
    "CLLIG": "COAL",
    "CCGT90": "CC",
    "CCLE90": "CC",
}

# Telemetered statuses that mean "synchronised and dispatchable" — an OFF/OUT
# unit has no incremental offer to make, so including it would measure
# commitment rather than offer behaviour (the ERCOT-122 reach convention).
ONLINE = frozenset(
    {"ON", "ONOS", "ONRR", "ONTEST", "ONEMR", "ONREG", "EMR", "EMRSWGR",
     "ONRUC", "ONHOLD"}
)

# Up-direction AS responsibilities: these are what ERCOT subtracts from HSL to
# form HASL, so they are the measured power reservation §C cross-checks.
AS_UP_COLS = [
    "Ancillary Service REGUP",
    "Ancillary Service RRS",
    "Ancillary Service RRSFFR",
    "Ancillary Service NSRS",
    "Ancillary Service ECRS",
]

TPO_MW = [f"Submitted TPO-MW{k}" for k in range(1, 11)]
TPO_PR = [f"Submitted TPO-Price{k}" for k in range(1, 11)]

# Offer-price bands for §B. The first two boundaries are the ERCOT-117/122
# crossing band ($20 = the measured DAM top-of-curve, $25 = where measured RT
# coal supply saturates); the rest resolve the tail.
PRICE_BANDS: tuple[float, ...] = (0.0, 20.0, 25.0, 40.0, 100.0, 500.0)

SUBSETS: tuple[tuple[str, int, str], ...] = (
    ("2024_ercot74_tail_days", 2024, "tail"),
    ("2024_ercot75_control_days", 2024, "control"),
    ("2025_ercot75_control_days", 2025, "control"),
    ("2025_ercot86_tail_days", 2025, "tail"),
)

_BASE_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Output Schedule",
    "HSL",
    "HASL",
    "HDL",
    "LSL",
    "Telemetered Resource Status",
    "Base Point",
]

# ERCOT revised the 60-Day SCED disclosure schema in DECEMBER 2025. In the new
# layout ``HASL``/``LASL`` and the ``Ancillary Service <svc>`` AWARD block are
# dropped outright and replaced by ``AS Capability <svc>`` + ``Ramp Rate
# Up/Down``, and ``Telemetered Net Output`` loses its trailing space. The two
# net-output spellings are the same quantity and are coalesced; HASL is NOT
# recoverable, and AS *capability* is a different quantity from an AS *award*,
# so December-2025 intervals cannot enter the headroom decomposition at all.
# They are dropped explicitly and counted, never silently NaN-skipped.
NETOUT_COLS = ("Telemetered Net Output ", "Telemetered Net Output")
NETOUT = "netout"


def _subset_path(tag: str) -> Path:
    """On-disk parquet for one probe-day subset."""
    return _RAW / f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{tag}.parquet"


def load_sced(tag: str) -> tuple[pd.DataFrame, dict] | None:
    """Load one SCED probe-day subset, restricted to the coal and CC classes.

    Returns the online resource-intervals with every quantity the decomposition
    needs coerced to float and the class label attached, plus a coverage dict
    recording what was dropped and why. Rows are excluded when the telemetered
    range is degenerate (``HSL <= 0`` or ``HSL <= LSL``) — no headroom to
    decompose — or when ``HASL`` is absent, which on these subsets means exactly
    the December-2025 schema revision described at :data:`NETOUT_COLS`.
    """
    path = _subset_path(tag)
    if not path.exists():
        return None
    import pyarrow.parquet as pq

    have = set(pq.ParquetFile(path).schema_arrow.names)
    netout_cols = [c for c in NETOUT_COLS if c in have]
    cols = _BASE_COLS + netout_cols + [c for c in AS_UP_COLS if c in have] + TPO_MW + TPO_PR
    df = pd.read_parquet(path, columns=cols)
    df["cls"] = df["Resource Type"].map(TYPE_TO_CLASS)
    df = df[df["cls"].notna()]
    df = df[df["Telemetered Resource Status"].astype(str).str.strip().isin(ONLINE)]
    if df.empty:
        return None
    num = (["Output Schedule", "HSL", "HASL", "HDL", "LSL", "Base Point"]
           + netout_cols + [c for c in AS_UP_COLS if c in have] + TPO_MW + TPO_PR)
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in AS_UP_COLS:
        if c not in df.columns:
            df[c] = np.nan
    # The two net-output spellings are the same telemetered quantity.
    net = df[netout_cols[0]]
    for c in netout_cols[1:]:
        net = net.fillna(df[c])
    df[NETOUT] = net
    df["ts"] = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    df = df[(df["HSL"] > 0) & (df["HSL"] > df["LSL"])]
    if df.empty:
        return None
    keep = df["HASL"].notna() & df[NETOUT].notna()
    cov = {
        "rows_online": int(len(df)),
        "rows_kept": int(keep.sum()),
        "dropped_no_hasl": int((~keep).sum()),
        "dropped_days": sorted(
            str(d.date()) for d in df.loc[~keep, "ts"].dt.normalize().unique()
        ),
    }
    df = df[keep]
    return (df.reset_index(drop=True), cov) if not df.empty else None


def _decompose(df: pd.DataFrame) -> pd.DataFrame:
    """Attach the per-interval bucket MW to a loaded SCED frame.

    The algebra, per online resource-interval, over the **telemetered operating
    range** ``H_tel = HSL - LSL``:

    * ``as_mw``  = ``HSL - HASL`` — capability held out of SCED's reach by an
      ancillary-service responsibility. This is the charter's bucket (c), and
      §C shows it is also *identically* the charter's bucket (d) as the charter
      defined it ("HASL < HSL"), which is why (d) is measured separately in §D.
    * ``H_rt``   = ``HASL - LSL`` — the RT-dispatchable headroom, the charter's
      denominator, decomposed exhaustively into:
      - ``off_mw``   (a) covered by a submitted TPO curve point;
      - ``ss_mw``    (b) price-taking above the curve's reach — the unit is
        scheduled or already generating there without an incremental offer;
      - ``res_mw``   (e) the genuine residual: not offered, not scheduled, not
        AS-reserved, not generated.

    The (b) reference is ``max(Output Schedule, Telemetered Net Output)``. Using
    net output is not circular: output at or below the curve's reach is the
    curve being dispatched and is already inside (a); only output **above** the
    reach is capacity moving without an incremental offer, which is exactly what
    price-taking means.
    """
    hsl = df["HSL"].to_numpy(float)
    hasl = np.clip(df["HASL"].to_numpy(float), 0.0, hsl)
    lsl = np.clip(df["LSL"].to_numpy(float), 0.0, hsl)
    h_tel = np.clip(hsl - lsl, 0.0, None)
    as_mw = np.clip(hsl - hasl, 0.0, h_tel)
    h_rt = np.clip(hasl - lsl, 0.0, None)

    P = df[TPO_PR].to_numpy(float)
    M = df[TPO_MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    has_curve = ok.any(axis=1)
    top = np.max(np.where(ok, M, -np.inf), axis=1)
    reach = np.where(np.isfinite(top), top, lsl)
    off_mw = np.clip(np.clip(reach, lsl, hasl) - lsl, 0.0, h_rt)

    osched = np.nan_to_num(df["Output Schedule"].to_numpy(float))
    netout = np.nan_to_num(df[NETOUT].to_numpy(float))
    ss_ref = np.clip(np.maximum(osched, netout), lsl, hasl)
    ss_mw = np.clip((ss_ref - lsl) - off_mw, 0.0, h_rt - off_mw)

    out = df.copy()
    out["h_tel"] = h_tel
    out["h_rt"] = h_rt
    out["as_mw"] = as_mw
    out["off_mw"] = off_mw
    out["ss_mw"] = ss_mw
    out["res_mw"] = np.clip(h_rt - off_mw - ss_mw, 0.0, None)
    out["has_curve"] = has_curve
    out["up_as"] = df[AS_UP_COLS].fillna(0.0).to_numpy(float).sum(axis=1)
    out["hdl_short"] = np.clip(hasl - np.nan_to_num(df["HDL"].to_numpy(float)), 0.0, None)
    return out


def section_a(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """A — MW-weighted bucket shares per (year, day-family, class).

    Shares are capacity-weighted fleet aggregates (``sum bucket / sum
    denominator``), not per-unit means: a 750 MW Oak Grove interval and a 90 MW
    CC interval are not the same evidence.
    """
    rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        for cls, g in d.groupby("cls", observed=True):
            h_rt, h_tel = g["h_rt"].sum(), g["h_tel"].sum()
            if h_rt <= 0 or h_tel <= 0:
                continue
            rows.append({
                "year": year, "family": fam, "class": cls,
                "res_hours": len(g), "resources": g["Resource Name"].nunique(),
                "HSL_GW": g["HSL"].mean() / 1e3,
                "a_offered": g["off_mw"].sum() / h_rt,
                "b_selfsched": g["ss_mw"].sum() / h_rt,
                "e_residual": g["res_mw"].sum() / h_rt,
                "c_as_of_Htel": g["as_mw"].sum() / h_tel,
                "curve_share": float(g["has_curve"].mean()),
                "hdl_short_of_Hrt": g["hdl_short"].sum() / h_rt,
                # The price-taking BASE share: LSL is bought regardless of the
                # energy curve, so LSL/HSL is the measured must-run fraction the
                # ERCOT-117 §5.3 successor asked for (model coal 0.28).
                "lsl_over_hsl": g["LSL"].sum() / g["HSL"].sum(),
                "loading": g[NETOUT].sum() / g["HSL"].sum(),
            })
    return pd.DataFrame(rows)


def section_b(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """B — the RT offer LEVEL: price distribution of the offered bucket (a).

    For each interval the monotone TPO curve is evaluated at every band edge,
    ``supply(x) = clip(max{MW_k : price_k <= x}, LSL, HASL)`` with
    ``supply(-inf) = LSL``; the MW in band ``[x1, x2)`` is
    ``supply(x2) - supply(x1)``. Summed over the fleet this is the
    capacity-weighted price composition of bucket (a) — the direct test of
    whether coal's RT offers are dearer than the $20.5-21.8 measured DAM level.

    Also returns the capacity-weighted p25/p50/p75 of each resource's
    **median-day RT top-of-curve price**, the RT analogue of the ERCOT-122
    ``peak_typical`` statistic that reproduced FINDING-ercot112 §6's ~$21.
    """
    band_rows, top_rows = [], []
    edges = list(PRICE_BANDS)
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        for cls, g in d.groupby("cls", observed=True):
            P = g[TPO_PR].to_numpy(float)
            M = g[TPO_MW].to_numpy(float)
            ok = np.isfinite(P) & np.isfinite(M)
            hsl = g["HSL"].to_numpy(float)
            hasl = np.clip(g["HASL"].to_numpy(float), 0.0, hsl)
            lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hsl)
            prev = lsl.copy()
            rec: dict[str, float] = {}
            for x in edges:
                sel = ok & (P <= x)
                sup = np.max(np.where(sel, M, -np.inf), axis=1)
                sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), lsl, hasl)
                sup = np.maximum(sup, prev)  # enforce monotonicity across edges
                rec[f"<{x:g}"] = float((sup - prev).sum())
                prev = sup
            total_off = float(g["off_mw"].sum())
            rec[f">={edges[-1]:g}"] = max(0.0, total_off - sum(rec.values()))
            if total_off <= 0:
                continue
            row = {"year": year, "family": fam, "class": cls}
            row.update({k: v / total_off for k, v in rec.items()})
            band_rows.append(row)

            # capacity-weighted p50 of the per-resource median-day top price
            topp = np.max(np.where(ok, P, -np.inf), axis=1)
            m = np.isfinite(topp)
            if not m.any():
                continue
            t = pd.DataFrame({
                "res": g["Resource Name"].to_numpy()[m],
                "day": g["ts"].dt.normalize().to_numpy()[m],
                "p": topp[m],
                "cap": hsl[m],
            })
            per_res = t.groupby(["res", "day"])["p"].max().groupby("res").median()
            cap = t.groupby("res")["cap"].max()
            j = pd.concat([per_res.rename("p"), cap.rename("cap")], axis=1).dropna()
            j = j.sort_values("p")
            w = j["cap"].to_numpy(float).cumsum() / j["cap"].sum()
            q = {f"p{int(k * 100)}": float(np.interp(k, w, j["p"].to_numpy(float)))
                 for k in (0.25, 0.5, 0.75)}
            top_rows.append({"year": year, "family": fam, "class": cls,
                             "resources": int(len(j)), **q})
    return pd.DataFrame(band_rows), pd.DataFrame(top_rows)


def section_c(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """C — is ``HSL - HASL`` the AS reservation the co-optimisation already models?

    Rule 19 guard: if the gap the charter calls bucket (c)/(d) *is* the awarded
    AS block, then a mechanism that re-reserved it would double-count what
    ``ercot_thermal_as_endogenous`` already prices. Reported as the fleet MW
    totals plus the interval-level agreement.
    """
    rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        for cls, g in d.groupby("cls", observed=True):
            gap = g["as_mw"].to_numpy(float)
            up = g["up_as"].to_numpy(float)
            rows.append({
                "year": year, "family": fam, "class": cls,
                "gap_mean_MW": float(gap.mean()),
                "upAS_mean_MW": float(up.mean()),
                "gap_over_upAS": float(gap.sum() / up.sum()) if up.sum() > 0 else np.nan,
                "corr": float(np.corrcoef(gap, up)[0, 1]) if gap.std() > 0 and up.std() > 0 else np.nan,
                "share_gap_ge_upAS": float((gap >= up - 1e-6).mean()),
                "upAS_share_of_Htel": float(up.sum() / g["h_tel"].sum()),
            })
    return pd.DataFrame(rows)


def section_d(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """D — the derate layer: telemetered HSL against each resource's own maximum.

    The charter's bucket (d) is "the unit declared the capability away". §C shows
    ``HSL - HASL`` is the AS block, not a derate, so the derate is measured where
    it actually lives: ``max_HSL(resource, year) - HSL``, i.e. capability the unit
    is not telemetering at all. This is the ERCOT-116/121 **availability
    envelope's** territory and is quantified here only to size the overlap — it
    is not an offer question.
    """
    rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        for cls, g in d.groupby("cls", observed=True):
            ref = g.groupby("Resource Name")["HSL"].transform("max")
            der = np.clip(ref.to_numpy(float) - g["HSL"].to_numpy(float), 0.0, None)
            rows.append({
                "year": year, "family": fam, "class": cls,
                "ref_cap_GW": float(g.groupby("Resource Name")["HSL"].max().sum() / 1e3),
                "derate_share_of_ref": float(der.sum() / ref.sum()),
                "derate_mean_MW": float(der.mean()),
                "share_intervals_derated_5pct": float((der > 0.05 * ref.to_numpy(float)).mean()),
            })
    return pd.DataFrame(rows)


def _hour_of_year(ts: pd.Series) -> np.ndarray:
    """Index into the model's non-leap 8760 clock for a local timestamp series.

    Feb 29 is dropped by :func:`load_eia_hourly_benchmark`, so leap-year days
    after February shift back one day to line up with the benchmark array.
    """
    doy = ts.dt.dayofyear.to_numpy()
    leap = ts.dt.is_leap_year.to_numpy()
    after_feb = (ts.dt.month.to_numpy() > 2) & leap
    doy = doy - after_feb.astype(int)
    return (doy - 1) * 24 + ts.dt.hour.to_numpy()


def section_e(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """E — Telemetered Net Output reconciled against the EIA-930 bench coal.

    The credibility check on the whole decomposition: if the SCED CLLIG fleet's
    telemetered output does not track the benchmark coal series on the same
    hours, the instrument is not measuring the fleet we score against.

    Carries the ERCOT-121 §1a SCORING-data caveat unfixed: the bench coal series
    includes plants whose model/CAMPD lineage mixes gas steamers (Parish 3470),
    so a few points of positive bias in the bench is expected and is **not**
    corrected here.
    """
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    rows = []
    bench: dict[int, np.ndarray | None] = {}
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        if year not in bench:
            b = load_eia_hourly_benchmark("ERCOT", year)
            bench[year] = np.asarray(b["coal"], float) if b and "coal" in b else None
        act = bench[year]
        if act is None:
            continue
        g = d[d["cls"] == "COAL"]
        if g.empty:
            continue
        hr = _hour_of_year(g["ts"])
        per_iv = g.groupby([hr, g["ts"]])[NETOUT].sum()
        per_hr = per_iv.groupby(level=0).mean()
        idx = per_hr.index.to_numpy()
        ok = (idx >= 0) & (idx < len(act))
        sced = per_hr.to_numpy(float)[ok]
        ba = act[idx[ok]]
        m = np.isfinite(sced) & np.isfinite(ba)
        rows.append({
            "year": year, "family": fam, "hours": int(m.sum()),
            "sced_mean_MW": float(sced[m].mean()),
            "bench_mean_MW": float(ba[m].mean()),
            "ratio": float(sced[m].sum() / ba[m].sum()),
            "corr": float(np.corrcoef(sced[m], ba[m])[0, 1]),
        })
    return pd.DataFrame(rows)


def section_f(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """F — DAM reach recomputed on the SAME probe days (the sampling check).

    Reproduces ``derive_dam_offer_hrmults.measure_offered_headroom_share`` — the
    0.168/0.184/0.161 coal figure — restricted to the probe days and hours the
    SCED subsets cover, so the DAM and RT reads sit on one footing. A probe-day
    reach that differs materially from the annual figure bounds everything else
    in this diagnosis.
    """
    day_hours: dict[int, set[tuple[pd.Timestamp, int]]] = {}
    for tag, year, _fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        ts = d["ts"]
        key = set(zip(ts.dt.normalize(), ts.dt.hour + 1))  # DAM Hour Ending
        day_hours.setdefault(year, set()).update(key)

    mw = [f"QSE submitted Curve-MW{k}" for k in range(1, 11)]
    cols = ["Delivery Date", "Hour Ending", "Resource Type", "Resource Name",
            "HSL", "LSL", "Resource Status"] + mw
    pat = str(_RAW / "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet")
    acc: dict[tuple[int, str, str], list[float]] = {}
    for f in sorted(globmod.glob(pat)):
        d = pd.read_parquet(f, columns=cols)
        d["cls"] = d["Resource Type"].map(TYPE_TO_CLASS)
        d = d[d["cls"].notna()]
        if d.empty:
            continue
        dt = pd.to_datetime(d["Delivery Date"])
        d = d.assign(_y=dt.dt.year.to_numpy(), _d=dt.dt.normalize().to_numpy())
        d = d[d["_y"].isin(day_hours)]
        d = d[d["Resource Status"].astype(str).str.startswith("ON")]
        d = d[(d["HSL"] > d["LSL"]) & (d["HSL"] > 0)]
        if d.empty:
            continue
        he = pd.to_numeric(d["Hour Ending"], errors="coerce").fillna(0).astype(int)
        reach = d[mw].max(axis=1).fillna(d["LSL"])
        head = (d["HSL"] - d["LSL"]).clip(lower=0.0)
        inc = (reach - d["LSL"]).clip(lower=0.0)
        for y in day_hours:
            probe = np.array([(dd, hh) in day_hours[y] for dd, hh in zip(d["_d"], he)])
            for scope, mask in (("all_year", (d["_y"] == y).to_numpy()),
                                ("probe_days", (d["_y"] == y).to_numpy() & probe)):
                for cls in ("COAL", "CC"):
                    m = mask & (d["cls"] == cls).to_numpy()
                    if not m.any():
                        continue
                    k = (y, scope, cls)
                    a = acc.setdefault(k, [0.0, 0.0])
                    a[0] += float(inc[m].sum())
                    a[1] += float(head[m].sum())
    rows = [{"year": y, "scope": s, "class": c,
             "dam_reach": (v[0] / v[1]) if v[1] > 0 else np.nan}
            for (y, s, c), v in sorted(acc.items())]
    return pd.DataFrame(rows)


def section_g(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """G — hour-of-day bias bound, from the only all-24-hour subset.

    Three of the four subsets sample hours 11-22 only. ``2025_ercot86_tail_days``
    covers all 24 hours, so the same decomposition split h11-22 against h23-h10
    inside that one subset measures directly how much the daytime-only sampling
    moves each bucket — instead of leaving it as an unquantified caveat.
    """
    d = frames.get("2025_ercot86_tail_days")
    if d is None:
        return pd.DataFrame()
    h = d["ts"].dt.hour
    rows = []
    for label, mask in (("h11-22", (h >= 11) & (h <= 22)), ("h23-h10", (h < 11) | (h > 22))):
        for cls, g in d[mask].groupby("cls", observed=True):
            h_rt, h_tel = g["h_rt"].sum(), g["h_tel"].sum()
            if h_rt <= 0:
                continue
            rows.append({
                "window": label, "class": cls, "res_hours": len(g),
                "a_offered": g["off_mw"].sum() / h_rt,
                "b_selfsched": g["ss_mw"].sum() / h_rt,
                "e_residual": g["res_mw"].sum() / h_rt,
                "c_as_of_Htel": g["as_mw"].sum() / h_tel,
                "loading": float(g[NETOUT].sum() / g["HSL"].sum()),
            })
    return pd.DataFrame(rows)


def section_h(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """H — the utilization offset: output against the fleet's OWN RT offer curve.

    §A shows the coal fleet offers essentially all of its headroom into SCED, so
    the over-run cannot be an offer-reach defect. This section measures where the
    error actually sits by evaluating each unit's own TPO curve at the prevailing
    **hourly RT settlement price** and comparing that offered supply against the
    unit's telemetered output:

        ``supply(p) = clip(max{MW_k : price_k <= p}, LSL, HASL)``

    A fleet that sits materially below its own offered supply at the clearing
    price is being held back by something that is not price — the ERCOT-117 §5.2
    "summer price-flat coal utilization offset". Reported as fleet MW and as the
    offset in points of reference capability, split summer / non-summer.

    The price is the hourly ERCOT RT settlement series (the same
    ``actual_lmp_hourly_ERCOT`` the scorer uses), not the 5-minute SCED LMP: the
    interval-level price is not on disk, so an interval whose 5-minute price ran
    above the hourly mean will show a spurious shortfall and one below it a
    spurious surplus. Averaged over thousands of intervals the bias is second
    order, but the number is an hourly-price approximation and is labelled so.
    """
    lmp = _REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
    if not lmp.exists():
        return pd.DataFrame()
    px = pd.read_parquet(lmp)
    rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        pr = px[px["year"] == year].sort_values("hour")["rt"].to_numpy(float)
        g = d[d["cls"] == "COAL"]
        if g.empty or pr.size == 0:
            continue
        hoy = _hour_of_year(g["ts"])
        ok_h = (hoy >= 0) & (hoy < pr.size)
        g = g[ok_h]
        p = pr[hoy[ok_h]]
        P = g[TPO_PR].to_numpy(float)
        M = g[TPO_MW].to_numpy(float)
        ok = np.isfinite(P) & np.isfinite(M)
        hsl = g["HSL"].to_numpy(float)
        hasl = np.clip(g["HASL"].to_numpy(float), 0.0, hsl)
        lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hsl)
        sel = ok & (P <= p[:, None])
        sup = np.max(np.where(sel, M, -np.inf), axis=1)
        sup = np.clip(np.where(np.isfinite(sup), sup, 0.0), lsl, hasl)
        out = g[NETOUT].to_numpy(float)
        mo = g["ts"].dt.month.to_numpy()
        for label, m in (("all", np.ones(len(g), bool)),
                         ("summer(Jun-Sep)", np.isin(mo, (6, 7, 8, 9))),
                         ("non-summer", ~np.isin(mo, (6, 7, 8, 9)))):
            if not m.any():
                continue
            rows.append({
                "year": year, "family": fam, "season": label,
                "res_hours": int(m.sum()),
                "offered_at_price_MW": float(sup[m].mean()),
                "output_MW": float(out[m].mean()),
                "output_over_offered": float(out[m].sum() / sup[m].sum()) if sup[m].sum() > 0 else np.nan,
                "offset_pp_of_HSL": float((sup[m].sum() - out[m].sum()) / hsl[m].sum() * 100.0),
            })
    return pd.DataFrame(rows)


_SUPPLY_GRID: tuple[float, ...] = (15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 60.0, 100.0, 500.0)


def section_i(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """I — the measured RT coal supply curve, and how many hours its tail bites in.

    §B1 shows coal's offered MW are not uniformly cheap: roughly a tenth of the
    offered headroom sits above $40 and a fifteenth above $100. The model's coal
    stack has no such tail — ERCOT-122 §3 measured its dearest band at $32.17
    (COAL_PRB peak). This section states the measured curve on the ERCOT-117 §1.1
    convention (share of telemetered HASL, curve-carrying units floored at LSL)
    so the two are directly comparable, and pairs it with the **full-year**
    distribution of ERCOT RT settlement prices so the tail's exposure is sized in
    hours rather than asserted.

    The supply curve is probe-day evidence; the hour distribution is the full
    year from ``actual_lmp_hourly_ERCOT``. They are reported side by side, never
    multiplied into a single TWh claim — a probe-day supply share is not an
    annual weight.
    """
    sup_rows = []
    for tag, year, fam in SUBSETS:
        d = frames.get(tag)
        if d is None:
            continue
        for cls, g in d.groupby("cls", observed=True):
            P = g[TPO_PR].to_numpy(float)
            M = g[TPO_MW].to_numpy(float)
            ok = np.isfinite(P) & np.isfinite(M)
            hsl = g["HSL"].to_numpy(float)
            hasl = np.clip(g["HASL"].to_numpy(float), 0.0, hsl)
            lsl = np.clip(g["LSL"].to_numpy(float), 0.0, hasl)
            row = {"year": year, "family": fam, "class": cls}
            den = hasl.sum()
            prev = np.zeros(len(g))
            for x in _SUPPLY_GRID:
                sel = ok & (P <= x)
                s = np.max(np.where(sel, M, -np.inf), axis=1)
                s = np.clip(np.where(np.isfinite(s), s, 0.0), lsl, hasl)
                s = np.maximum(s, prev)
                row[f"<={x:g}"] = float(s.sum() / den) if den > 0 else np.nan
                prev = s
            sup_rows.append(row)

    lmp = _REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
    hr_rows = []
    if lmp.exists():
        px = pd.read_parquet(lmp)
        for year in sorted({y for _t, y, _f in SUBSETS}):
            rt = px[px["year"] == year]["rt"].to_numpy(float)
            rt = rt[np.isfinite(rt)]
            if rt.size == 0:
                continue
            edges = [-np.inf, 25.0, 30.0, 35.0, 40.0, 60.0, 100.0, np.inf]
            row = {"year": year, "hours": int(rt.size)}
            for lo, hi in zip(edges[:-1], edges[1:]):
                lab = f"[{'' if np.isneginf(lo) else f'{lo:g}'},{'' if np.isposinf(hi) else f'{hi:g}'})"
                row[lab] = float(((rt >= lo) & (rt < hi)).mean())
            hr_rows.append(row)
    return pd.DataFrame(sup_rows), pd.DataFrame(hr_rows)


def _show(title: str, df: pd.DataFrame) -> None:
    """Print one section table."""
    print(f"\n=== {title} ===")
    if df is None or df.empty:
        print("(no rows)")
        return
    with pd.option_context("display.width", 200, "display.max_columns", 40,
                           "display.float_format", lambda v: f"{v:.4f}"):
        print(df.to_string(index=False))


def main(argv: list[str] | None = None) -> int:
    """Run every section and print the tables; optionally dump them as JSON."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json-out", default=None,
                    help="write all section tables to this JSON path")
    args = ap.parse_args(argv)

    frames: dict[str, pd.DataFrame] = {}
    coverage: dict[str, dict] = {}
    for tag, _y, _f in SUBSETS:
        loaded = load_sced(tag)
        if loaded is None:
            print(f"WARNING: subset missing or empty: {tag}")
            continue
        raw, cov = loaded
        frames[tag] = _decompose(raw)
        coverage[tag] = cov
        n = len(frames[tag])
        days = frames[tag]["ts"].dt.normalize().nunique()
        hrs = sorted(frames[tag]["ts"].dt.hour.unique().tolist())
        print(f"loaded {tag}: {n:,} online resource-intervals, {days} days, "
              f"hours {hrs[0]}-{hrs[-1]} ({len(hrs)} distinct)")
        if cov["dropped_no_hasl"]:
            print(f"  DROPPED {cov['dropped_no_hasl']:,} of {cov['rows_online']:,} "
                  f"online rows — Dec-2025 schema revision has no HASL/AS-award: "
                  f"{', '.join(cov['dropped_days'])}")

    a = section_a(frames)
    bands, tops = section_b(frames)
    c = section_c(frames)
    d = section_d(frames)
    e = section_e(frames)
    f = section_f(frames)
    g = section_g(frames)
    h = section_h(frames)
    sup, hrs = section_i(frames)

    _show("A - headroom decomposition (shares of HASL-LSL; c over HSL-LSL)", a)
    _show("B1 - offered-bucket price composition (share of bucket a)", bands)
    _show("B2 - RT top-of-curve price, cap-wtd over per-resource median day", tops)
    _show("C - AS reservation cross-check (HSL-HASL vs awarded up-AS)", c)
    _show("D - derate layer (HSL vs each resource's own max HSL)", d)
    _show("E - SCED telemetered net output vs EIA-930 bench coal", e)
    _show("F - DAM reach: full year vs the SCED probe days", f)
    _show("G - hour-of-day bias (2025 ercot86, the all-24h subset)", g)
    _show("H - coal output vs its OWN RT offer curve at the clearing price", h)
    _show("I1 - measured RT supply, share of HASL (ERCOT-117 convention)", sup)
    _show("I2 - full-year ERCOT RT price distribution (share of hours)", hrs)

    if args.json_out:
        out = {"A_decomposition": a, "B1_price_bands": bands, "B2_top_price": tops,
               "C_as_crosscheck": c, "D_derate": d, "E_bench_recon": e,
               "F_dam_reach": f, "G_hour_bias": g,
               "H_utilization": h,
               "I1_supply_curve": sup, "I2_price_hours": hrs}
        payload: dict = {k: json.loads(v.to_json(orient="records"))
                         for k, v in out.items()}
        payload["coverage"] = coverage
        Path(args.json_out).write_text(json.dumps(payload, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
