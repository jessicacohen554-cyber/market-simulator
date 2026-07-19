"""ERCOT-87 measure-first probe: the two residual mid-band candidate bases.

Charter step 1 of `docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md`
§6 — MEASUREMENT ONLY, no apply seam, no solve, no artifact consumed by the
model. Measures, from the NP3-965 60-Day SCED Gen Resource parquets already on
disk (the ERCOT-84/86 sample-day corpus — no new intake), whether either
candidate basis can reproduce the actual $150-500 mid-band hours the ERCOT-86
online-spare RT wall leaves un-formed:

* **Basis A — offline-CT startup-inclusive RT participation.** The offline
  quick-start pool (``Telemetered Resource Status`` OFFQS, disclosed separately
  from OFF/OFFNS) carries full SCED1/SCED2 curves, startup offers and Min Gen
  Cost, and SCED demonstrably dispatches it (OFFQS rows with Base Point > 0).
  Measured quantities: the pool's curve-price mass by net-load bin, the
  OFF->ON transition count per hour, and the as-offered marginal cleared price
  (SCED2 price at Base Point) of CTs in their first 60 min after a start —
  the curve segment the online-spare derive drops by construction. A startup
  amortization diagnostic (Start Up Hot Offer spread over 1h/3h at Base Point
  MW) is reported alongside, but the as-offered price is what formed lambda.

* **Basis B — CC spare above the mitigated SCED2 ceiling.** For ON-status CC
  the same Base Point -> HASL spare segments are priced on all three steps the
  disclosure carries — SCED2 (mitigated, the ERCOT-86 wall's basis), SCED1
  (pre-mitigation) and Submitted TPO — so the charter's adjudication question
  ("which step reproduces observed lambda in CC-marginal mid-band hours") is
  answered directly per hour.

Per covered mid-band hour (actual RT in [$150, $500], hourly, from
``actual_lmp_hourly_ERCOT.parquet``, date in the sample-day corpus) the probe
emits lambda plus, per surface: spare MW, max price, MW priced in-band and MW
priced within +/-33% of lambda. Per (year x surface x net-load bin) it emits
the MW-weighted effective-HR-multiplier ladder + coverage counts (intervals,
days, and for basis A the transition counts), the ERCOT-86 disclosure
convention.

Provenance / admissibility (rule 13): every quantity is an ex-ante posted
offer, a telemetered status, or a market-design construction (mitigated vs
unmitigated step); observed lambda enters ONLY as the adjudication reference
on the measurement side — nothing here feeds the model. Coverage is disclosed,
never silently capped (charter §4: OFF->ON transitions are rarer than online
spare; thin bins must be visible). Hourly lambda is an average over 4-12 SCED
intervals — intra-hour spikes are smoothed; noted in the artifact.

Usage::

    python scripts/probes/ercot87_midband_basis_measure.py \
        [--years 2024 2025] \
        [--out data/raw/_validation-source/ercot87_midband_basis_measurement.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    HOURS,
    LADDER_QUANTILES,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)
from derive_ercot_sced_offer_wall import CLASS_OF_RESTYPE, SCED_DIR  # noqa: E402

DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot87_midband_basis_measurement.json"
)
ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)

_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (derive_actual_lmp)

MID_BAND = (150.0, 500.0)  # the ERCOT-86/87 moderate-tightness band, $/MWh
LAMBDA_TOL = 1.0 / 3.0  # +/-33% "reproduces lambda" window (mult-space, ERCOT-86)
START_WINDOW_MIN = 60  # "first dispatched intervals after a start" horizon

# The offline startable pool: OFFQS is the telemetered offline-quick-start
# status (SCED-startable within the operating hour); OFFNS is offline carrying
# a Non-Spin responsibility (startable via NSRS deployment). OFF (plain) is
# NOT startable intra-hour and is excluded from the pool — reported only as a
# transition source. Statuses per ERCOT Nodal Protocols §3.9.1 telemetry codes.
OFFLINE_POOL = ("OFFQS", "OFFNS")
_ON_PREFIX = "ON"  # ON/ONREG/ONOS/ONRUC/ONTEST/... all telemeter dispatchable

_S1_MW = [f"SCED1 Curve-MW{i}" for i in range(1, 36)]
_S1_PR = [f"SCED1 Curve-Price{i}" for i in range(1, 36)]
_S2_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
_S2_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
_TPO_MW = [f"Submitted TPO-MW{i}" for i in range(1, 11)]
_TPO_PR = [f"Submitted TPO-Price{i}" for i in range(1, 11)]

_READ_COLS = (
    [
        "SCED Time Stamp",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "HASL",
        "HSL",
        "LSL",
        "Base Point",
        "Start Up Hot Offer",
        "Min Gen Cost",
    ]
    + _S1_MW
    + _S1_PR
    + _S2_MW
    + _S2_PR
    + _TPO_MW
    + _TPO_PR
)


def _load_year(year: int) -> tuple[pd.DataFrame, list[str]]:
    """ALL-status merchant gas SCED rows for ``year`` (offline pool included)."""
    files = sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    )
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        frames.append(df[df["Resource Type"].isin(CLASS_OF_RESTYPE)].copy())
    if not frames:
        return pd.DataFrame(columns=_READ_COLS), []
    return pd.concat(frames, ignore_index=True), [p.name for p in files]


def _clock(df: pd.DataFrame) -> pd.DataFrame:
    """Attach hoy / date / class on the model's non-leap fixed-CST clock."""
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["_date"] = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)].to_numpy()
    df["_ts"] = pd.to_datetime(df["SCED Time Stamp"]).to_numpy()[np.asarray(ok)]
    df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
    df["stat"] = df["Telemetered Resource Status"].astype(str).str.strip()
    return df


def _segments(
    df: pd.DataFrame, mw_cols: list[str], pr_cols: list[str], lo: np.ndarray
) -> pd.DataFrame:
    """Curve segments in ``(max(prev, lo), min(step_MW, HASL)]`` at step price.

    The ERCOT-86 spare construction generalized to any curve basis and any
    lower bound (``lo`` = Base Point for online spare, 0 for the offline pool's
    full startable range).
    """
    MW = df[mw_cols].to_numpy(float)
    PR = df[pr_cols].to_numpy(float)
    hasl = df["HASL"].to_numpy(float)
    hoy = df["hoy"].to_numpy(int)
    ts = df["_ts"].to_numpy()
    gas = df["gas_day"].to_numpy(float)

    seg: dict[str, list[np.ndarray]] = {k: [] for k in ("mw", "pr", "hoy", "ts", "gas")}
    prev = np.maximum(lo, 0.0).copy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        hi = np.minimum(q, hasl)
        mw = np.where(valid, np.maximum(hi - np.maximum(prev, lo), 0.0), 0.0)
        take = mw > 0
        if take.any():
            seg["mw"].append(mw[take])
            seg["pr"].append(np.minimum(p[take], HCAP_USD_MWH))
            seg["hoy"].append(hoy[take])
            seg["ts"].append(ts[take])
            seg["gas"].append(gas[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    if not seg["mw"]:
        return pd.DataFrame(columns=["hoy", "mw", "price", "ts", "gas_day"])
    return pd.DataFrame(
        {
            "hoy": np.concatenate(seg["hoy"]),
            "mw": np.concatenate(seg["mw"]),
            "price": np.concatenate(seg["pr"]),
            "ts": np.concatenate(seg["ts"]),
            "gas_day": np.concatenate(seg["gas"]),
        }
    )


def _price_at(
    df: pd.DataFrame, mw_cols: list[str], pr_cols: list[str], at_mw: np.ndarray
) -> np.ndarray:
    """Curve price at MW level ``at_mw`` (first step whose cum-MW >= at_mw)."""
    MW = df[mw_cols].to_numpy(float)
    PR = df[pr_cols].to_numpy(float)
    MWf = np.where(np.isfinite(MW), MW, -np.inf)
    hit = MWf >= at_mw[:, None]
    idx = np.argmax(hit, axis=1)
    any_hit = hit.any(axis=1)
    # No step reaches at_mw -> last finite step's price.
    last = np.where(np.isfinite(MW), np.arange(MW.shape[1])[None, :], -1).max(axis=1)
    idx = np.where(any_hit, idx, np.maximum(last, 0))
    out = PR[np.arange(len(df)), idx]
    return np.minimum(np.where(np.isfinite(out), out, np.nan), HCAP_USD_MWH)


def _detect_starts(df: pd.DataFrame) -> pd.DataFrame:
    """OFF->ON transition rows: first dispatched intervals after a start.

    A start is a row with Base Point > 0 whose resource's previous interval had
    Base Point == 0 and an OFF-family/STARTUP status. Rows within
    START_WINDOW_MIN minutes of a start are tagged ``started`` with the
    start's hot startup offer carried along.
    """
    df = df.sort_values(["Resource Name", "_ts"]).copy()
    bp = df["Base Point"].to_numpy(float)
    same = df["Resource Name"].to_numpy()
    prev_same = np.r_[False, same[1:] == same[:-1]]
    prev_bp = np.r_[np.nan, bp[:-1]]
    prev_stat = np.r_[["NA"], df["stat"].to_numpy()[:-1]]
    off_family = np.char.startswith(prev_stat.astype(str), "OFF") | (
        prev_stat == "STARTUP"
    )
    is_start = prev_same & (bp > 0) & (prev_bp <= 0) & off_family
    df["is_start"] = is_start

    starts = df[is_start][["Resource Name", "_ts"]].rename(columns={"_ts": "_t0"})
    if starts.empty:
        df["started"] = False
        return df
    # Slim merge (row-id x resource x timestamp ONLY): merging the full
    # ~170-column curve frame here multiplies every curve column by the
    # per-resource start count and OOMs the container.
    slim = df[["Resource Name", "_ts"]].reset_index()
    merged = slim.merge(starts, on="Resource Name", how="left")
    dt_min = (merged["_ts"] - merged["_t0"]).dt.total_seconds() / 60.0
    in_win = (dt_min >= 0) & (dt_min < START_WINDOW_MIN)
    started_idx = merged.loc[in_win, "index"].unique()
    df["started"] = False
    df.loc[started_idx, "started"] = True
    return df


def _hour_stats(seg: pd.DataFrame, hoy: int, lam: float) -> dict:
    """Spare MW / max price / in-band MW / near-lambda MW for one hour."""
    g = seg[seg["hoy"] == hoy]
    if not len(g):
        return {"mw": 0.0, "max_pr": None, "mw_inband": 0.0, "mw_nearlam": 0.0}
    n_iv = max(g["ts"].nunique(), 1)
    pr = g["price"].to_numpy(float)
    mw = g["mw"].to_numpy(float)
    inband = (pr >= MID_BAND[0]) & (pr <= MID_BAND[1])
    near = (pr >= lam * (1 - LAMBDA_TOL)) & (pr <= lam * (1 + LAMBDA_TOL))
    return {
        "mw": round(float(mw.sum()) / n_iv, 1),
        "max_pr": round(float(pr.max()), 1),
        "mw_inband": round(float(mw[inband].sum()) / n_iv, 1),
        "mw_nearlam": round(float(mw[near].sum()) / n_iv, 1),
    }


def _ladder(seg: pd.DataFrame, hour_bin: np.ndarray, n_bins: int) -> tuple[list, list]:
    """(ladder, coverage) per net-load bin — the wall-derive convention."""
    b = hour_bin[np.minimum(seg["hoy"].to_numpy(int), HOURS - 1)] if len(seg) else []
    seg = seg.assign(bin=b) if len(seg) else seg
    ladders, cov = [], []
    for k in range(n_bins):
        g = seg[seg["bin"] == k] if len(seg) else seg
        mult = (
            g["price"].to_numpy(float) / g["gas_day"].to_numpy(float)
            if len(g)
            else np.array([])
        )
        qs = (
            _weighted_quantiles(mult, g["mw"].to_numpy(float), LADDER_QUANTILES)
            if len(g)
            else [float("nan")] * len(LADDER_QUANTILES)
        )
        ladders.append([[float(q), round(m, 3)] for q, m in zip(LADDER_QUANTILES, qs)])
        cov.append(
            {
                "intervals": int(g["ts"].nunique()) if len(g) else 0,
                "days": int(pd.Series(g["hoy"] // 24).nunique()) if len(g) else 0,
                "mean_mw": round(
                    float(g["mw"].sum()) / max(int(g["ts"].nunique()), 1), 1
                )
                if len(g)
                else 0.0,
            }
        )
    return ladders, cov


def measure_year(year: int, gas_day: pd.Series, actual: pd.DataFrame) -> dict:
    """Measure both candidate bases + per-hour adjudication for one year."""
    df, files = _load_year(year)
    if df.empty:
        return {"source_files": files, "note": "no SCED sample days on disk"}
    df = _clock(df)
    gas = gas_day.reindex(pd.DatetimeIndex(df["_date"])).to_numpy(float)
    df["gas_day"] = gas
    df = df[df["gas_day"] > 0].copy()

    on = df[df["stat"].str.startswith(_ON_PREFIX)]
    on_ct = on[on["cls"] == "CT"]
    on_cc = on[on["cls"] == "CC"]
    off_ct = df[(df["cls"] == "CT") & df["stat"].isin(OFFLINE_POOL)]

    bp = lambda d: np.maximum(d["Base Point"].to_numpy(float), 0.0)  # noqa: E731
    zero = lambda d: np.zeros(len(d))  # noqa: E731

    surfaces = {
        "ON_CT_SCED2": _segments(on_ct, _S2_MW, _S2_PR, bp(on_ct)),
        "ON_CC_SCED2": _segments(on_cc, _S2_MW, _S2_PR, bp(on_cc)),
        "ON_CC_SCED1": _segments(on_cc, _S1_MW, _S1_PR, bp(on_cc)),
        "ON_CC_TPO": _segments(on_cc, _TPO_MW, _TPO_PR, bp(on_cc)),
        "OFFPOOL_CT_SCED1": _segments(off_ct, _S1_MW, _S1_PR, zero(off_ct)),
        "OFFPOOL_CT_SCED2": _segments(off_ct, _S2_MW, _S2_PR, zero(off_ct)),
    }

    # Basis A: starts + as-offered marginal cleared price of started CTs.
    ct_all = _detect_starts(df[df["cls"] == "CT"].copy())
    started = ct_all[ct_all["started"] & (ct_all["Base Point"] > 0)].copy()
    if len(started):
        started["clr_pr"] = _price_at(
            started, _S2_MW, _S2_PR, started["Base Point"].to_numpy(float)
        )
        bpm = started["Base Point"].to_numpy(float)
        hot = started["Start Up Hot Offer"].to_numpy(float)
        started["su_adder_1h"] = np.where(bpm > 0, hot / np.maximum(bpm, 1e-9), np.nan)
        started["su_adder_3h"] = started["su_adder_1h"] / 3.0

    # Per-hour adjudication over covered actual mid-band hours.
    sample_dates = set(pd.DatetimeIndex(df["_date"]).normalize().unique())
    act = actual[actual["year"] == year]
    mb = act[(act["rt"] >= MID_BAND[0]) & (act["rt"] <= MID_BAND[1])]
    hours_out: list[dict] = []
    for _, row in mb.iterrows():
        hoy = int(row["hour"])
        lam = float(row["rt"])
        day_rows = df[df["hoy"] == hoy]
        if day_rows.empty:  # hour not on a sample day
            continue
        rec: dict = {
            "hoy": hoy,
            "date": str(pd.Timestamp(day_rows["_date"].iloc[0]).date()),
            "hh": hoy % 24,
            "lambda": round(lam, 1),
        }
        for name, seg in surfaces.items():
            rec[name] = _hour_stats(seg, hoy, lam)
        sh = started[started["hoy"] == hoy] if len(started) else started
        n_iv = max(day_rows["_ts"].nunique(), 1)
        rec["starts"] = {
            "n_units": int(sh["Resource Name"].nunique()) if len(sh) else 0,
            "mw": round(float(sh["Base Point"].sum()) / n_iv, 1) if len(sh) else 0.0,
            "clr_pr_max": round(float(sh["clr_pr"].max()), 1) if len(sh) else None,
            "clr_pr_wmed": (
                round(
                    float(
                        _weighted_quantiles(
                            sh["clr_pr"].to_numpy(float),
                            sh["Base Point"].to_numpy(float),
                            [0.5],
                        )[0]
                    ),
                    1,
                )
                if len(sh)
                else None
            ),
        }
        # Adjudication flags (raw fields above stay quotable either way).
        wall_reaches = (rec["ON_CT_SCED2"]["max_pr"] or 0) >= lam * (1 - LAMBDA_TOL)
        cc2 = (rec["ON_CC_SCED2"]["max_pr"] or 0) >= lam * (1 - LAMBDA_TOL)
        cc1 = (rec["ON_CC_SCED1"]["max_pr"] or 0) >= lam * (1 - LAMBDA_TOL)
        cctpo = (rec["ON_CC_TPO"]["max_pr"] or 0) >= lam * (1 - LAMBDA_TOL)
        a_started = rec["starts"]["n_units"] > 0 and (
            rec["starts"]["clr_pr_max"] or 0
        ) >= lam * (1 - LAMBDA_TOL)
        a_pool = rec["OFFPOOL_CT_SCED1"]["mw_nearlam"] > 0
        rec["adjudication"] = {
            "wall_reaches_lambda": bool(wall_reaches),
            "ccS2_reaches": bool(cc2),
            "ccS1_reaches": bool(cc1),
            "ccTPO_reaches": bool(cctpo),
            "basisB_gain": bool((cc1 or cctpo) and not cc2),
            "basisA_started_at_lambda": bool(a_started),
            "basisA_pool_priced_at_lambda": bool(a_pool),
        }
        hours_out.append(rec)

    # Ladders + coverage per surface per net-load bin.
    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")
    n_bins = len(edges) + 1
    ladders: dict[str, dict] = {}
    for name, seg in surfaces.items():
        lad, cov = _ladder(seg, hour_bin, n_bins)
        ladders[name] = {"ladder": lad, "coverage": cov}
    if len(started):
        seg_started = pd.DataFrame(
            {
                "hoy": started["hoy"].to_numpy(int),
                "mw": started["Base Point"].to_numpy(float),
                "price": started["clr_pr"].to_numpy(float),
                "ts": started["_ts"].to_numpy(),
                "gas_day": started["gas_day"].to_numpy(float),
            }
        ).dropna(subset=["price"])
        lad, cov = _ladder(seg_started, hour_bin, n_bins)
        n_starts_bin = [
            int(
                ct_all[
                    ct_all["is_start"]
                    & (hour_bin[np.minimum(ct_all["hoy"], HOURS - 1)] == k)
                ]["Resource Name"].count()
            )
            for k in range(n_bins)
        ]
        for k, c in enumerate(cov):
            c["n_starts"] = n_starts_bin[k]
        ladders["STARTED_CT_CLEARED"] = {"ladder": lad, "coverage": cov}

    n_mb = int(len(mb))
    return {
        "source_files": files,
        "n_midband_hours_actual": n_mb,
        "n_midband_hours_covered": len(hours_out),
        "n_ct_starts_total": int(ct_all["is_start"].sum()),
        "startup_adder_note": (
            "su_adder_1h/3h = Start Up Hot Offer / (Base Point MW x recovery "
            "hours) — diagnostic only; the as-offered clr_pr is what SCED "
            "actually priced"
        ),
        "hours": hours_out,
        "ladders": ladders,
    }


def main() -> None:
    """Run the measurement and write the JSON artifact + console summary."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    gas_day = _gas_day_series()
    actual = pd.read_parquet(ACTUAL_LMP)
    result: dict = {
        "_provenance": {
            "probe": "ercot87_midband_basis_measure",
            "charter": (
                "docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md §6.1"
            ),
            "role": (
                "MEASUREMENT ONLY — adjudicates the two candidate bases "
                "against observed lambda; not a model input, no apply seam"
            ),
            "mid_band_usd_mwh": list(MID_BAND),
            "lambda_tolerance": LAMBDA_TOL,
            "start_window_min": START_WINDOW_MIN,
            "offline_pool_statuses": list(OFFLINE_POOL),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "caveat_hourly_lambda": (
                "actual RT is hourly (mean of 4-12 SCED intervals); intra-hour "
                "spikes are smoothed, so per-hour reach flags are conservative"
            ),
        }
    }
    for y in args.years:
        result[str(y)] = measure_year(y, gas_day, actual)
        r = result[str(y)]
        print(
            f"\n=== {y}: covered {r['n_midband_hours_covered']}/"
            f"{r['n_midband_hours_actual']} actual mid-band hours; "
            f"{r['n_ct_starts_total']} CT starts in corpus ==="
        )
        adj = [h["adjudication"] for h in r["hours"]]
        for key in (
            "wall_reaches_lambda",
            "ccS2_reaches",
            "ccS1_reaches",
            "ccTPO_reaches",
            "basisB_gain",
            "basisA_started_at_lambda",
            "basisA_pool_priced_at_lambda",
        ):
            print(f"  {key:32s}: {sum(a[key] for a in adj)}/{len(adj)}")

    args.out.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
