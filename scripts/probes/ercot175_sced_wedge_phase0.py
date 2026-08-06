"""ercot-175 Phase 0 (NO LP): the offered-vs-deliverable wedge at SCED grain.

Executes `docs/PRECOMMIT-ercot175-sced-deliverable-wedge-2026-08-06.md` §1–§4
exactly. Per 5-min SCED interval, per ONLINE scope-S resource, the monotone
min-chain (precommit §2):

    O = sub-$200 offered MW (35-step SCED1 segment sum, clipped to [0, HSL])
    A = min(O, HASL)          W_AS   = O − A   (AS holdback)
    R = min(O, HASL, HDL)     W_RAMP = A − R   (ramp reachability)
    D = min(O, HASL, HDL, BP) W_RESID= R − D   (5-min congestion / economics)

aggregated interval-mean per hour over H123 (verdict-bearing) and H61
(descriptive), per class and total, against the committed model-side figures
(V_m, M(h)) and the keeper's own AS holdback (reserve_family sidecar).

Hour sets, clock, scope maps and status sets are the ercot-173 constructions,
IMPORTED VERBATIM from `ercot173_depth_phase0` (its own 123/61 asserts stand).
The per-hour M(h) series is recomputed by that probe's own face_tables
arithmetic (capture A + P1 bid matrix + sidecar dispatch, cheapest-first fill)
and must reproduce the committed aggregate within 1 % (precommit §0).

Rule 13 [R-MEASURED]: HASL/HDL/Base Point are read ONLY as measurement
evidence of the wedge — nothing here writes a model input. Rule 22: 2023 only.
No LP, no network.

Usage:
    PYTHONPATH=.:src python scripts/probes/ercot175_sced_wedge_phase0.py \
        [--work /tmp/claude-0/ercot175_captures] \
        [--out results/calibration/ercot175_sced_wedge_phase0.json]
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import ercot173_depth_phase0 as e173  # noqa: E402  (constructions, verbatim)

YEAR = 2023
BUNDLE = e173.BUNDLE
CORPUS = e173.CORPUS
DEFAULT_OUT = REPO / "results/calibration/ercot175_sced_wedge_phase0.json"

# Precommit §3 bars — read, never recomputed.
BAR_L1, BAR_L2, BAR_L3 = 0.90, 0.90, 0.05
BAR_SHARE = 0.60  # §4, the majority-plus-margin standard, twice
PRICE_BAR = 200.0
CHAIN_TOL_MW = 1.0

MW35 = [f"SCED1 Curve-MW{i}" for i in range(1, 36)]
PR35 = [f"SCED1 Curve-Price{i}" for i in range(1, 36)]
AS_COLS = [
    f"Ancillary Service {p}"
    for p in ("REGUP", "REGDN", "RRS", "RRSFFR", "NSRS", "ECRS")
]
#: Withheld-class reserve families = the model's online-energy AS holdback
#: (precommit §1: a REPORT classification, no gate rests on it).
WITHHELD_FAMILIES = ("RegUp_withheld", "RRS_withheld", "ECRS_withheld")

COARSE = e173.COARSE


def load_wedge_rows(hours: np.ndarray) -> pd.DataFrame:
    """Scope-S corpus rows at ``hours`` with the wedge fields (precommit §1).

    The shard/month selection, CPT→CST conversion and hour-key membership are
    `ercot173_depth_phase0.market_stack`'s own, reproduced line for line; the
    column set adds HASL/HDL/Base Point/AS awards and widens the curve read to
    all 35 SCED1 steps (declared in the precommit, not silent).
    """
    clock = e173.model_clock(YEAR)
    want_ts = clock[hours]
    want = set(want_ts.strftime("%Y-%m-%d %H"))
    months_needed = sorted(set(want_ts.month))
    shard_keys = []
    for m in months_needed:
        fy, fm = (YEAR, m + 2) if m + 2 <= 12 else (YEAR + 1, m + 2 - 12)
        shard_keys.append(f"{fy}-{fm:02d}")
    files: list[str] = []
    for k in sorted(set(shard_keys)):
        files += sorted(glob.glob(str(CORPUS / f"{k}.part*.parquet")))
    if not files:
        raise SystemExit("no SCED corpus shards for the requested hours")
    from zoneinfo import ZoneInfo

    cpt = ZoneInfo("America/Chicago")
    cols = [
        "SCED Time Stamp",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "HSL",
        "HASL",
        "HDL",
        "LSL",
        "Base Point",
        *AS_COLS,
        *MW35,
        *PR35,
    ]
    frames = []
    for f in files:
        have = set(pq.ParquetFile(f).schema_arrow.names)
        t = pq.read_table(f, columns=[c for c in cols if c in have]).to_pandas()
        t = t[t["Resource Type"].isin(e173.RESTYPE_CLS)]
        if t.empty:
            continue
        ts = pd.to_datetime(
            t["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
        )
        loc = ts.dt.tz_localize(cpt, nonexistent="NaT", ambiguous="NaT")
        cst = loc.dt.tz_convert("Etc/GMT+6").dt.tz_localize(None)
        key = cst.dt.strftime("%Y-%m-%d %H")
        keep = key.isin(want)
        if keep.any():
            sub = t[keep].copy()
            sub["cst_hour"] = key[keep]
            sub["stamp"] = t.loc[keep, "SCED Time Stamp"]
            frames.append(sub)
    df = pd.concat(frames, ignore_index=True)
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan  # pre-Jun-2023 shards carry no ECRS column
    df["coarse"] = df["Resource Type"].map(e173.RESTYPE_CLS)
    stat = df["Telemetered Resource Status"].astype(str).str.upper().str.strip()
    df["state"] = np.where(
        stat.str.startswith("ON"),
        "online",
        np.where(stat.isin(e173.STARTABLE), "startable", "other"),
    )
    num = ["HSL", "HASL", "HDL", "LSL", "Base Point", *AS_COLS, *MW35, *PR35]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def sub200_offered(df: pd.DataFrame, n_steps: int) -> np.ndarray:
    """Per-row sub-$200 offered MW — the ercot-173 segment construction.

    Incremental step MW = clipped diff of the cumulative curve MW, summed where
    the step price is finite and < $200, clipped to [0, HSL]. ``n_steps`` = 35
    for the wedge (full corpus width) or 10 for the committed-V_r cross-check.
    """
    mw = df[MW35[:n_steps]].to_numpy(float)
    prc = df[PR35[:n_steps]].to_numpy(float)
    seg = np.clip(np.diff(np.nan_to_num(mw, nan=0.0), axis=1, prepend=0.0), 0, None)
    fin = np.isfinite(prc)
    o = (seg * (fin & (prc < PRICE_BAR))).sum(axis=1)
    hsl = np.nan_to_num(df["HSL"].to_numpy(float), nan=0.0)
    return np.clip(o, 0.0, np.maximum(hsl, 0.0))


def model_m_series(work: Path) -> tuple[np.ndarray, dict]:
    """Per-hour M(h) over 8760 — the ercot-173 face_tables arithmetic, per class.

    Capture A availability × pmax, P1 bid matrix, sidecar class dispatch,
    cheapest-first fill; M = undispatched sub-$200 capability summed over S.
    """
    cap_a = e173.run_capture("A", YEAR, work, [])
    A = np.load(cap_a, allow_pickle=True)
    avail_a = A["availability"].astype(float)
    pmax = A["pmax"].astype(float)
    groups = np.array([str(g) for g in A["group"]])
    state, mc_bid = e173.model_state()
    fa = state["fleet_arrays"]
    st_avail = np.asarray(fa.availability, dtype=float)
    drift = float(np.abs(st_avail[:, :8760] - avail_a[:, :8760]).max())
    if drift > 1e-4:
        raise SystemExit("reconstructed availability diverges from capture A")
    coarse_of = np.array([e173.MODEL_CLS.get(g, "") for g in groups])
    dispatch = e173.class_dispatch()
    cap_hourly = avail_a[:, :8760] * pmax[:, None]
    bid = np.asarray(mc_bid)[:, :8760]
    m_series = np.zeros(8760)
    for c in COARSE:
        m = coarse_of == c
        caph = cap_hourly[m, :]
        bh = bid[m, :]
        disp = dispatch[c]
        for h in range(8760):
            bhh = bh[:, h]
            order = np.argsort(bhh, kind="stable")
            cum = np.cumsum(caph[order, h])
            nb = int(np.searchsorted(bhh[order], PRICE_BAR))
            sub_cap = float(cum[nb - 1]) if nb > 0 else 0.0
            m_series[h] += max(0.0, sub_cap - min(float(disp[h]), sub_cap))
    return m_series, {"availability_drift": drift}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", default="/tmp/claude-0/ercot175_captures")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    print("== hour sets (ercot-173 construction, imported) ==", flush=True)
    hs = e173.hour_sets()
    h123, h61 = hs["h123"], hs["h61"]

    print("== per-hour M(h) (capture A + bid matrix, no LP) ==", flush=True)
    m_series, m_meta = model_m_series(work)
    m123 = m_series[h123]
    m_check = {
        "mean_gw": float(m123.mean() / 1e3),
        "p50_gw": float(np.median(m123) / 1e3),
        "committed_mean_gw": 3.3007,
        "committed_p50_gw": 2.2165,
    }
    m_check["mean_ok"] = abs(m_check["mean_gw"] - m_check["committed_mean_gw"]) <= 0.01 * m_check["committed_mean_gw"]
    m_check["p50_ok"] = abs(m_check["p50_gw"] - m_check["committed_p50_gw"]) <= 0.01 * m_check["committed_p50_gw"]
    print(f"  M(h) H123 mean {m_check['mean_gw']:.4f} GW (committed 3.3007), "
          f"p50 {m_check['p50_gw']:.4f} GW (committed 2.2165)", flush=True)
    if not (m_check["mean_ok"] and m_check["p50_ok"]):
        raise SystemExit("M(h) reproduction outside 1% of the committed record "
                         "(precommit §0 stop-the-session)")

    print("== corpus wedge rows at H123 ∪ H61 ==", flush=True)
    all_hours = np.unique(np.concatenate([h123, h61]))
    df = load_wedge_rows(all_hours)
    n_iv_by_hour = df.groupby("cst_hour")["stamp"].nunique()

    clock = e173.model_clock(YEAR)
    key_of = pd.Series(clock.strftime("%Y-%m-%d %H"), index=range(8760))

    # ---- licensing (precommit §3) -----------------------------------------
    onl = df[df["state"] == "online"].copy()
    k123 = set(key_of[h123])
    onl123 = onl[onl["cst_hour"].isin(k123)]
    covered = set(onl123["cst_hour"])
    l1 = len(covered) / len(k123)
    l2 = {
        c: float(np.isfinite(onl123[c].to_numpy(float)).mean())
        for c in ("HASL", "HDL", "Base Point")
    }
    hasl = onl123["HASL"].to_numpy(float)
    hdl = onl123["HDL"].to_numpy(float)
    bp = onl123["Base Point"].to_numpy(float)
    both = np.isfinite(hasl) & np.isfinite(hdl)
    l3 = {
        "hdl_gt_hasl": float((hdl[both] > hasl[both] + CHAIN_TOL_MW).mean()),
        "bp_gt_hdl": float(
            (bp[np.isfinite(bp) & np.isfinite(hdl)] > hdl[np.isfinite(bp) & np.isfinite(hdl)] + CHAIN_TOL_MW).mean()
        ),
    }
    print(f"  L1 {l1:.4f}  L2 {l2}  L3 {l3}", flush=True)

    # ---- wedge terms per row (precommit §2) --------------------------------
    df["O"] = sub200_offered(df, 35)
    df["O10"] = sub200_offered(df, 10)
    # UNCLIPPED 10-step read — the committed ercot-173 V_r construction carries
    # no HSL clip, so the comparability cross-check must not either.
    mw10 = df[MW35[:10]].to_numpy(float)
    pr10 = df[PR35[:10]].to_numpy(float)
    seg10 = np.clip(np.diff(np.nan_to_num(mw10, nan=0.0), axis=1, prepend=0.0), 0, None)
    fin10 = np.isfinite(pr10)
    df["O10_unclipped"] = (seg10 * (fin10 & (pr10 < PRICE_BAR))).sum(axis=1)
    h = np.nan_to_num(df["HASL"].to_numpy(float), nan=np.inf)
    d = np.nan_to_num(df["HDL"].to_numpy(float), nan=np.inf)
    b = np.nan_to_num(df["Base Point"].to_numpy(float), nan=0.0)
    o = df["O"].to_numpy(float)
    A = np.minimum(o, np.maximum(h, 0.0))
    R = np.minimum(A, np.maximum(d, 0.0))
    D = np.minimum(R, np.maximum(b, 0.0))
    df["stepA"], df["stepR"], df["stepD"] = A, R, D
    df["W_AS"] = o - A
    df["W_RAMP"] = A - R
    df["W_RESID"] = R - D
    df["as_award"] = df[AS_COLS].fillna(0.0).clip(lower=0.0).sum(axis=1)

    def hourly(sub: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        """Interval-mean per cst_hour of the summed cols."""
        g = sub.groupby("cst_hour")[cols].sum()
        return g.div(n_iv_by_hour.reindex(g.index), axis=0)

    wedge_cols = [
        "O", "O10", "O10_unclipped", "stepA", "stepR", "stepD",
        "W_AS", "W_RAMP", "W_RESID", "as_award",
    ]
    on_h = hourly(df[df["state"] == "online"], wedge_cols)
    st_h = hourly(df[df["state"] == "startable"], ["O", "O10", "O10_unclipped", "Base Point"])
    by_class = {
        c: hourly(df[(df["state"] == "online") & (df["coarse"] == c)], wedge_cols)
        for c in COARSE
    }

    # ---- model-side AS holdback (keeper sidecar) ---------------------------
    rf = pd.read_parquet(BUNDLE / "hourly" / f"reserve_family_{YEAR}.parquet")
    rf = rf[rf["pass"] == "P1"]
    held = {
        str(fam): g.groupby("hour")["held_mw"].sum().reindex(range(8760)).fillna(0.0).to_numpy()
        for fam, g in rf.groupby("family", observed=True)
    }
    h_model = sum(held[f] for f in WITHHELD_FAMILIES if f in held)

    # ---- statistics over the two hour sets ---------------------------------
    def stats(hours: np.ndarray) -> dict:
        keys = [key_of[hh] for hh in hours]
        out: dict = {"n_hours": int(len(hours))}

        def block(tbl: pd.DataFrame, cols: list[str]) -> dict:
            v = tbl.reindex(keys)
            return {
                c: {
                    "mean_gw": float(np.nanmean(v[c]) / 1e3),
                    "p50_gw": float(np.nanmedian(v[c]) / 1e3),
                }
                for c in cols
            }

        out["online_total"] = block(on_h, wedge_cols)
        out["startable"] = block(st_h, ["O", "O10", "O10_unclipped", "Base Point"])
        out["online_by_class"] = {c: block(by_class[c], wedge_cols) for c in COARSE}
        m_h = m_series[hours]
        w_ramp = on_h.reindex(keys)["W_RAMP"].to_numpy(float)
        w_as = on_h.reindex(keys)["W_AS"].to_numpy(float)
        w_res = on_h.reindex(keys)["W_RESID"].to_numpy(float)
        tot = w_as + w_ramp + w_res
        ratio = np.where(m_h > 0, w_ramp / np.maximum(m_h, 1e-9), np.nan)
        out["w_ramp_over_M_p50"] = float(np.nanmedian(ratio))
        out["w_as_over_M_p50"] = float(np.nanmedian(np.where(m_h > 0, w_as / np.maximum(m_h, 1e-9), np.nan)))
        out["w_resid_over_M_p50"] = float(np.nanmedian(np.where(m_h > 0, w_res / np.maximum(m_h, 1e-9), np.nan)))
        out["s_ramp_p50"] = float(np.nanmedian(np.where(tot > 0, w_ramp / np.maximum(tot, 1e-9), np.nan)))
        out["s_as_p50"] = float(np.nanmedian(np.where(tot > 0, w_as / np.maximum(tot, 1e-9), np.nan)))
        out["s_resid_p50"] = float(np.nanmedian(np.where(tot > 0, w_res / np.maximum(tot, 1e-9), np.nan)))
        out["M_gw"] = {"mean": float(np.mean(m_h) / 1e3), "p50": float(np.median(m_h) / 1e3)}
        hm = h_model[hours]
        out["H_model_gw"] = {"mean": float(np.mean(hm) / 1e3), "p50": float(np.median(hm) / 1e3)}
        out["W_AS_minus_H_model_gw_p50"] = float(np.nanmedian((w_as - hm)) / 1e3)
        out["as_award_gw"] = {
            "mean": float(np.nanmean(on_h.reindex(keys)["as_award"]) / 1e3),
            "p50": float(np.nanmedian(on_h.reindex(keys)["as_award"]) / 1e3),
        }
        # P-W adjudication statistic: per-hour TOTAL online wedge O − D.
        out["wedge_total_gw"] = {
            "mean": float(np.nanmean(tot) / 1e3),
            "p50": float(np.nanmedian(tot) / 1e3),
        }
        out["wedge_total_over_M_p50"] = float(
            np.nanmedian(np.where(m_h > 0, tot / np.maximum(m_h, 1e-9), np.nan))
        )
        # Compact per-hour table for later diagnostics (GW, 3 decimals).
        v = on_h.reindex(keys)
        out["per_hour"] = [
            {
                "h": int(hh),
                "O": round(float(v["O"].iloc[i]) / 1e3, 3),
                "W_AS": round(float(v["W_AS"].iloc[i]) / 1e3, 3),
                "W_RAMP": round(float(v["W_RAMP"].iloc[i]) / 1e3, 3),
                "W_RESID": round(float(v["W_RESID"].iloc[i]) / 1e3, 3),
                "D": round(float(v["stepD"].iloc[i]) / 1e3, 3),
                "M": round(float(m_h[i]) / 1e3, 3),
                "H_model": round(float(hm[i]) / 1e3, 3),
            }
            for i, hh in enumerate(hours)
        ]
        return out

    s123 = stats(h123)
    s61 = stats(h61)

    # ---- decision rule (precommit §4, branches in order) -------------------
    hdl_licensed = l2["HDL"] >= BAR_L2
    licensed = l1 >= BAR_L1 and hdl_licensed
    l3_flag = {k: v > BAR_L3 for k, v in l3.items()}
    w_ramp_m = s123["w_ramp_over_M_p50"]
    s_ramp = s123["s_ramp_p50"]
    if not licensed:
        branch = "FILED-UNLICENSED"
    elif not (w_ramp_m >= BAR_SHARE):
        branch = "FILED-REDIRECTED"
    elif s_ramp >= BAR_SHARE:
        branch = "CHARTER-RAMP (subject to in-session owner adjudication, precommit §4.3)"
    elif w_ramp_m >= BAR_SHARE:
        branch = "FILED-SPLIT"
    else:
        branch = "FILED-NULL"

    out = {
        "session": "ercot-175",
        "phase": 0,
        "lp_solved": False,
        "year": YEAR,
        "bundle": str(BUNDLE.relative_to(REPO)),
        "precommit": "docs/PRECOMMIT-ercot175-sced-deliverable-wedge-2026-08-06.md",
        "m_reproduction": {**m_check, **m_meta},
        "licence": {
            "L1_corpus": round(l1, 4),
            "L2_fields": {k: round(v, 4) for k, v in l2.items()},
            "L3_chain_violation_share": {k: round(v, 5) for k, v in l3.items()},
            "L3_flagged": l3_flag,
            "bars": {"L1": BAR_L1, "L2": BAR_L2, "L3": BAR_L3, "share": BAR_SHARE},
        },
        "H123": s123,
        "H61": s61,
        "decision": {
            "w_ramp_over_M_p50": round(w_ramp_m, 4),
            "s_ramp_p50": round(s_ramp, 4),
            "branch": branch,
        },
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["decision"], indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
