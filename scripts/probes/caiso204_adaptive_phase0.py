"""caiso-204 Phase-0: CAISO adaptive-expectation storage offer identification.

Pre-registration: results/calibration/PRECHECK-caiso204-adaptive-phase0-2026-08-19.md
(pushed before any bid value was read). Instrument summary:

- Response: per fetched trade date, the MW-weighted p50 of discharge-side
  (MW > 0) energy-bid segment prices of storage-classified resources over
  hours 18-21 PT (DST-exact), from the PUB_BID_DAM subset re-fetch.
  implied_P(d) = response / $1,000 (CAISO soft-cap park level, caiso-178 §3).
- Classifier: caiso-178's price-blind S1/S2/S3/S4 verbatim, with S2's
  absolute floor scaled to the subset's per-day density (PRECHECK §2).
- Driver: S(d) = 1 iff measured CA-system daily max RT >= $200 (committed
  actual_lmp_hourly_CAISO.parquet, nan-aware); P_trail via the committed
  ercot_adaptive_expectation_daily helper with beta=1 (identical EWMA
  construction, per-year reset).
- Fit: grid half-life in {5,7,10,15,20,30,45} d; beta >= 0 OLS through the
  origin of implied_P on P_trail; SSE-optimal pair is the identified value.
- Gates (PRECHECK §3): G-DRIVER, G-COV, G-ID, G-DECAY, G-BOOT, G-SAFE. The
  verdict JSON is written unrewritten whatever it says.

NO SOLVE. Measured prices enter only as identification evidence about
conduct (rule 13's sanctioned class); the armed path, if ever built, reads
only the model's own scored path (G-BOOT/G-SAFE read the keeper's committed
sidecars for exactly that reason).
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.results.scarcity import (  # noqa: E402
    ercot_adaptive_expectation_daily,
)
from scripts.lib.dam_public_bids.caiso import parse_day  # noqa: E402
from scripts.probes.caiso204_fetch_subset import (  # noqa: E402
    EVENT_USD,
    LMP_PARQUET,
    selected_days,
)

ZIPS = REPO / "data" / "raw" / "caiso-public-bids" / "zips"
KEEPER = REPO / "results" / "calibration" / "caiso200_h1_memberpanel" / "hourly"
OUT = REPO / "results" / "calibration" / "caiso204_adaptive_phase0.json"

YEARS = (2023, 2024, 2025)
CA_ZONES = ["LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26"]
WINDOW_PT = (18, 19, 20, 21)  # PRECHECK §1: CAISO evening net-load peak
PARK_CAP_USD = 1000.0  # CAISO soft energy bid cap (caiso-178 §3 park level)
HALF_LIFE_GRID = (5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 45.0)
MIN_SEG_ROWS = 40  # admissibility (ercot-154 convention)
# caiso-178 committed classifier thresholds (PRECHECK §2 — none tunable here)
WD_MW_EPS = 1.0
S2_WD_FRAC = 0.50
S2_MIN_HOURS_FULL = 500  # on a 365-day scan; scaled to the subset density
S3_SYM_LO, S3_SYM_HI = 0.5, 2.0
S4_PS_MW = 200.0
S4_PS_DRIFT = 0.10
# caiso-178 committed fidelity reference (curve_geometry.share_p_hi_gt_caiso176_bound)
FIDELITY_REF = {2023: 0.8954, 2024: 0.8128, 2025: 0.8158}
FIDELITY_TOL_PP = 10.0
# G-SAFE bar: floors <= vom + $100 in >= 95% of all hours; vom taken as 0
# (the strictest reading — CAISO battery offer is vom + adder ~= $5).
SAFE_FLOOR_USD = 100.0
SAFE_SHARE = 0.95
BOOT_MIN_EVENT_DAYS = 3
BOOT_FLOOR_USD = 200.0
BOOT_MIN_WINDOW_HOURS = 12


def measured_daily_max() -> dict[int, np.ndarray]:
    """Nan-aware daily max of the committed CA-system RT series, per year."""
    df = pd.read_parquet(LMP_PARQUET)
    out = {}
    for yr in YEARS:
        rt = df.loc[df["year"] == yr, "rt"].to_numpy(dtype=float)
        n = rt.size // 24
        body = np.where(np.isnan(rt[: n * 24]), -np.inf, rt[: n * 24])
        out[yr] = body.reshape(n, 24).max(axis=1)
    return out


def keeper_daily_max(year: int) -> np.ndarray:
    """Daily max of the keeper's committed CA demand-weighted scored price."""
    s = pd.read_parquet(KEEPER / f"system_{year}.parquet")
    p1 = s[(s["pass"] == "P1") & (s["zone"].isin(CA_ZONES))]
    piv_p = p1.pivot_table(index="hour", columns="zone", values="price")
    piv_d = p1.pivot_table(index="hour", columns="zone", values="demand")
    lam = ((piv_p * piv_d).sum(axis=1) / piv_d.sum(axis=1)).to_numpy(dtype=float)
    n = lam.size // 24
    return lam[: n * 24].reshape(n, 24).max(axis=1)


def p_trail(events: np.ndarray, half_life: float) -> np.ndarray:
    """Normalized trailing EWMA in [0,1] — the committed helper at beta=1."""
    return ercot_adaptive_expectation_daily(
        events, half_life_days=half_life, beta=1.0
    )


def weighted_p50(width: np.ndarray, price: np.ndarray) -> float:
    """MW-weighted median price."""
    order = np.argsort(price)
    w = width[order].cumsum()
    return float(price[order][np.searchsorted(w, 0.5 * w[-1])])


def scan_day(path: Path) -> dict | None:
    """One zip -> compact per-day record (classifier inputs + window segments)."""
    try:
        df = parse_day(path)
    except Exception as exc:  # noqa: BLE001 — a bad day is coverage, not a crash
        return {"error": repr(exc)}
    gen = df[
        (df["resource_type"] == "GENERATOR")
        & (df["product"] == "EN")
        & (df["row_kind"] == "segment")
    ]
    if not len(gen):
        return None
    en_hours = gen.groupby("resource_seq")["interval_start_utc"].nunique().to_dict()
    gen = gen.sort_values(["resource_seq", "interval_start_utc", "segment_mw"])
    mw_all = gen["segment_mw"].to_numpy(dtype=float)
    px_all = gen["segment_price_usd_per_mwh"].to_numpy(dtype=float)
    rs_all = gen["resource_seq"].to_numpy()
    hr_all = gen["interval_start_utc"].to_numpy()
    hod_all = (
        gen["interval_start_utc"].dt.tz_convert("America/Los_Angeles").dt.hour
    ).to_numpy()
    new = np.empty(len(gen), dtype=bool)
    new[0] = True
    new[1:] = (rs_all[1:] != rs_all[:-1]) | (hr_all[1:] != hr_all[:-1])
    starts = np.flatnonzero(new)
    stops = np.append(starts[1:], len(gen))
    curves = []  # (rs, min_mw, max_mw, p_hi)
    segs = []  # (rs, width, price) for window hours, discharge side
    for i0, i1 in zip(starts, stops):
        mw = mw_all[i0:i1]
        px = px_all[i0:i1]
        if not np.isfinite(mw).all() or not np.isfinite(px).all():
            continue
        lo, hi = mw[0], mw[-1]
        if lo > -WD_MW_EPS or hi < WD_MW_EPS:
            continue  # S1: not withdrawal-capable this hour
        rs = int(rs_all[i0])
        j_hi = int(np.searchsorted(mw, 0.0, side="left"))
        curves.append((rs, float(lo), float(hi), float(px[j_hi])))
        if int(hod_all[i0]) in WINDOW_PT:
            top = np.maximum(mw[1:], 0.0)
            bot = np.maximum(mw[:-1], 0.0)
            width = top - bot
            for k in np.flatnonzero(width > 0):
                segs.append((rs, float(width[k]), float(px[k])))
    return {"en_hours": en_hours, "curves": curves, "segs": segs}


def classify(per_year: dict[int, dict], days_parsed: dict[int, int]) -> dict[int, set]:
    """caiso-178 S2/S3/S4, price-blind; S2 floor scaled to subset density."""
    rows = []
    for yr in YEARS:
        acc = per_year[yr]
        for rs, mins in acc["min_mw"].items():
            arr_min = np.array(mins)
            arr_max = np.array(acc["max_mw"][rs])
            en = int(acc["en_hours"].get(rs, 0))
            wd = arr_min.size
            p05 = float(np.percentile(arr_min, 5))
            p95 = float(np.percentile(arr_max, 95))
            sym = abs(p05) / p95 if p95 > 0 else np.nan
            floor = S2_MIN_HOURS_FULL * days_parsed[yr] / 365.0
            in_s = (wd / en >= S2_WD_FRAC if en else False) and en >= floor
            in_b = in_s and (S3_SYM_LO <= sym <= S3_SYM_HI)
            rows.append(
                {"rs": rs, "year": yr, "in_B": in_b, "p95_max": p95}
            )
    df = pd.DataFrame(rows)
    ps: set[int] = set()
    for rs, grp in df[df["in_B"]].groupby("rs"):
        if set(grp["year"]) != set(YEARS):
            continue
        caps = grp.set_index("year")["p95_max"]
        if caps.min() < S4_PS_MW:
            continue
        if (caps.max() - caps.min()) / caps.max() < S4_PS_DRIFT:
            ps.add(int(rs))
    return {
        yr: set(df[(df["year"] == yr) & df["in_B"] & ~df["rs"].isin(ps)]["rs"])
        for yr in YEARS
    }


def main() -> int:
    days = selected_days()
    day_max = measured_daily_max()

    # ---- scan the fetched subset --------------------------------------- #
    per_year = {
        yr: {
            "min_mw": defaultdict(list),
            "max_mw": defaultdict(list),
            "en_hours": defaultdict(int),
            "p_hi": defaultdict(list),  # rs -> list of first-rung prices
        }
        for yr in YEARS
    }
    day_segs: dict[dt.date, list] = {}
    coverage = {yr: {"selected": 0, "present": 0, "parsed": 0, "errors": []} for yr in YEARS}
    for day in days:
        yr = day.year
        coverage[yr]["selected"] += 1
        path = ZIPS / f"{day.strftime('%Y%m%d')}_PUB_BID_DAM_v3_csv.zip"
        if not path.exists() or path.stat().st_size <= 10_000:
            continue
        coverage[yr]["present"] += 1
        rec = scan_day(path)
        if rec is None:
            continue
        if "error" in rec:
            coverage[yr]["errors"].append({day.isoformat(): rec["error"]})
            continue
        coverage[yr]["parsed"] += 1
        acc = per_year[yr]
        for rs, n in rec["en_hours"].items():
            acc["en_hours"][int(rs)] += int(n)
        for rs, lo, hi, p_hi in rec["curves"]:
            acc["min_mw"][rs].append(lo)
            acc["max_mw"][rs].append(hi)
            acc["p_hi"][rs].append(p_hi)
        day_segs[day] = rec["segs"]

    days_parsed = {yr: coverage[yr]["parsed"] for yr in YEARS}
    members = classify(per_year, days_parsed)

    # ---- fidelity leg (G-COV): share of first rungs > $15, classified set  #
    fidelity = {}
    for yr in YEARS:
        vals = np.concatenate(
            [np.array(per_year[yr]["p_hi"][rs]) for rs in members[yr] if per_year[yr]["p_hi"][rs]]
        ) if members[yr] else np.array([])
        share = float((vals > 15.0).mean()) if vals.size else float("nan")
        fidelity[yr] = {
            "share_p_hi_gt_15": round(share, 4),
            "committed_ref": FIDELITY_REF[yr],
            "abs_diff_pp": round(abs(share - FIDELITY_REF[yr]) * 100, 2) if vals.size else None,
            "ok": bool(vals.size and abs(share - FIDELITY_REF[yr]) * 100 <= FIDELITY_TOL_PP),
            "n_curve_hours": int(vals.size),
        }

    # ---- response series ------------------------------------------------ #
    resp: dict[dt.date, float] = {}
    n_rows: dict[dt.date, int] = {}
    for day, segs in day_segs.items():
        segs_m = [(w, p) for rs, w, p in segs if rs in members[day.year]]
        n_rows[day] = len(segs_m)
        if len(segs_m) >= MIN_SEG_ROWS:
            w = np.array([s[0] for s in segs_m])
            p = np.array([s[1] for s in segs_m])
            resp[day] = weighted_p50(w, p)
    admissible = sorted(resp)

    # ---- driver / trailing state ---------------------------------------- #
    events = {yr: (day_max[yr] >= EVENT_USD).astype(float) for yr in YEARS}
    events_1000 = {yr: int((day_max[yr] >= 1000.0).sum()) for yr in YEARS}
    quarters_with_2 = 0
    for yr in YEARS:
        ev_days = np.flatnonzero(events[yr])
        q = pd.Series(
            [
                (dt.date(yr, 1, 1) + dt.timedelta(days=int(d))).month
                for d in ev_days
            ]
        ).map(lambda m: (m - 1) // 3 + 1)
        quarters_with_2 += int((q.value_counts() >= 2).sum())
    total_events = int(sum(events[yr].sum() for yr in YEARS))

    def trail_for(days_list: list[dt.date], hl: float) -> np.ndarray:
        per_yr = {yr: p_trail(events[yr], hl) for yr in YEARS}
        return np.array(
            [per_yr[d.year][(d - dt.date(d.year, 1, 1)).days] for d in days_list]
        )

    y_all = np.array([resp[d] for d in admissible]) / PARK_CAP_USD

    def fit(days_list: list[dt.date], y: np.ndarray) -> dict:
        best = None
        for hl in HALF_LIFE_GRID:
            x = trail_for(days_list, hl)
            beta = max(0.0, float((x * y).sum() / (x * x).sum())) if (x * x).sum() > 0 else 0.0
            pred = np.clip(beta * x, 0.0, 1.0)
            sse = float(((y - pred) ** 2).sum())
            if best is None or sse < best["sse"]:
                best = {"half_life": hl, "beta": round(beta, 4), "sse": round(sse, 4)}
        return best

    full_fit = fit(admissible, y_all)

    # quiet-day base: no event in the trailing 120 within-year days
    x120 = trail_for(admissible, 120.0)  # any nonzero trailing event -> > 0
    quiet = [d for d, x in zip(admissible, x120) if x == 0.0]
    base = float(np.median([resp[d] for d in quiet])) if quiet else float("nan")

    # ---- G-ID ------------------------------------------------------------ #
    x_fit = trail_for(admissible, full_fit["half_life"])
    p_hat = np.clip(full_fit["beta"] * x_fit, 0.0, 1.0)
    corr = float(np.corrcoef(y_all, p_hat)[0, 1]) if p_hat.std() > 0 else 0.0

    def monthly_leg(fit_c: dict, target_days: list[dt.date], band: float) -> dict:
        x = trail_for(target_days, fit_c["half_life"])
        pred_d = np.maximum(fit_c["beta"] * x * PARK_CAP_USD, base)
        meas_d = np.array([resp[d] for d in target_days])
        key = [(d.year, d.month) for d in target_days]
        cells = {}
        for k in sorted(set(key)):
            idx = [i for i, kk in enumerate(key) if kk == k]
            if len(idx) < 5:
                continue
            m = float(np.median(meas_d[idx]))
            p = float(np.median(pred_d[idx]))
            rel = (p - m) / m if m else float("inf")
            cells[f"{k[0]}-{k[1]:02d}"] = {
                "n_days": len(idx),
                "measured_p50": round(m, 1),
                "predicted": round(p, 1),
                "rel_err": round(rel, 4),
                "in_band": bool(abs(rel) <= band),
            }
        n_in = sum(c["in_band"] for c in cells.values())
        return {
            "cells": cells,
            "n_cells": len(cells),
            "n_in_band": n_in,
            "share_in_band": round(n_in / len(cells), 3) if cells else None,
        }

    gid_monthly = monthly_leg(full_fit, admissible, 0.35)
    g_id = {
        "daily_corr": round(corr, 4),
        "corr_ok": bool(corr >= 0.6),
        "base_usd": round(base, 1),
        "n_quiet_days": len(quiet),
        "monthly": gid_monthly,
        "monthly_ok": bool(gid_monthly["share_in_band"] is not None and gid_monthly["share_in_band"] >= 0.6),
    }
    g_id["ok"] = bool(g_id["corr_ok"] and g_id["monthly_ok"])

    # ---- G-DECAY --------------------------------------------------------- #
    d23 = [d for d in admissible if d.year == 2023]
    d2425 = [d for d in admissible if d.year in (2024, 2025)]
    fit23 = fit(d23, np.array([resp[d] for d in d23]) / PARK_CAP_USD) if d23 else None
    decay_monthly = monthly_leg(fit23, d2425, 0.50) if fit23 and d2425 else None
    # base-only ablation: prediction is constant -> corr leg fails by construction
    ablation_corr = 0.0
    g_decay = {
        "fit_2023_only": fit23,
        "monthly_2024_2025": decay_monthly,
        "monthly_ok": bool(
            decay_monthly and decay_monthly["share_in_band"] is not None and decay_monthly["share_in_band"] >= 0.6
        ),
        "base_only_ablation_corr": ablation_corr,
        "ablation_fails_corr_leg": True,
    }
    g_decay["ok"] = bool(g_decay["monthly_ok"] and g_decay["ablation_fails_corr_leg"])

    # ---- G-DRIVER -------------------------------------------------------- #
    g_driver = {
        "event_days_200": {yr: int(events[yr].sum()) for yr in YEARS},
        "total": total_events,
        "quarters_with_ge2": quarters_with_2,
        "diagnostic_event_days_1000": events_1000,
        "ok": bool(total_events >= 10 and quarters_with_2 >= 2),
    }

    # ---- G-COV ----------------------------------------------------------- #
    q_adm = pd.Series([(d.month - 1) // 3 + 1 for d in admissible]).value_counts()
    g_cov = {
        "coverage": coverage,
        "parsed_total": int(sum(days_parsed.values())),
        "admissible_days": len(admissible),
        "admissible_by_quarter_of_year": {int(k): int(v) for k, v in q_adm.sort_index().items()},
        "quarter_ok": bool(len(q_adm) == 4 and (q_adm >= 15).all()),
        "fidelity": fidelity,
        "fidelity_ok": bool(all(f["ok"] for f in fidelity.values())),
        "n_members": {yr: len(members[yr]) for yr in YEARS},
    }
    g_cov["ok"] = bool(
        g_cov["parsed_total"] >= 250 and g_cov["quarter_ok"] and g_cov["fidelity_ok"]
    )

    # ---- G-BOOT / G-SAFE (keeper's committed scored path) ---------------- #
    model_events = {}
    boot_floor = {}
    for yr in YEARS:
        dm = keeper_daily_max(yr)
        s_m = (dm >= EVENT_USD).astype(float)
        model_events[yr] = int(s_m.sum())
        ph = np.clip(
            full_fit["beta"] * p_trail(s_m, full_fit["half_life"]), 0.0, 1.0
        )
        floor = ph * PARK_CAP_USD
        boot_floor[yr] = {
            "window_hours_floor_ge_200": int((floor >= BOOT_FLOOR_USD).sum()) * len(WINDOW_PT),
            "max_floor": round(float(floor.max()), 1),
            "share_all_hours_floor_le_100": round(
                1.0 - (floor > SAFE_FLOOR_USD).sum() * len(WINDOW_PT) / (dm.size * 24), 4
            ),
        }
    best_yr = max(YEARS, key=lambda y: model_events[y])
    g_boot = {
        "model_event_days_200": model_events,
        "leg_i_ok": bool(model_events[best_yr] >= BOOT_MIN_EVENT_DAYS),
        "per_year": boot_floor,
        "leg_ii_ok": bool(
            boot_floor[best_yr]["window_hours_floor_ge_200"] >= BOOT_MIN_WINDOW_HOURS
        ),
    }
    g_boot["ok"] = bool(g_boot["leg_i_ok"] and g_boot["leg_ii_ok"])
    g_safe = {
        yr: {
            "share_hours_floor_le_100": boot_floor[yr]["share_all_hours_floor_le_100"],
            "ok": bool(boot_floor[yr]["share_all_hours_floor_le_100"] >= SAFE_SHARE),
        }
        for yr in (2023, 2025)
    }
    g_safe_ok = bool(all(v["ok"] for v in g_safe.values()))

    gates = {
        "G-DRIVER": g_driver,
        "G-COV": g_cov,
        "G-ID": g_id,
        "G-DECAY": g_decay,
        "G-BOOT": g_boot,
        "G-SAFE": {"years": g_safe, "ok": g_safe_ok},
    }
    all_pass = bool(all(g["ok"] for g in [g_driver, g_cov, g_id, g_decay, g_boot]) and g_safe_ok)

    monthly_measured = {}
    key = [(d.year, d.month) for d in admissible]
    for k in sorted(set(key)):
        idx = [i for i, kk in enumerate(key) if kk == k]
        monthly_measured[f"{k[0]}-{k[1]:02d}"] = {
            "n_days": len(idx),
            "measured_p50": round(float(np.median([resp[admissible[i]] for i in idx])), 1),
        }

    record = {
        "probe": "caiso204_adaptive_phase0",
        "date": "2026-08-19",
        "precheck": "results/calibration/PRECHECK-caiso204-adaptive-phase0-2026-08-19.md",
        "conventions": {
            "event_usd": EVENT_USD,
            "trail_days": 120,
            "window_pt": list(WINDOW_PT),
            "park_cap_usd": PARK_CAP_USD,
            "per_year_reset": True,
            "half_life_grid": list(HALF_LIFE_GRID),
        },
        "fitted_constants": full_fit,
        "base_usd": round(base, 1),
        "daily_monthly_measured_p50": monthly_measured,
        "gates": gates,
        "ALL_PASS": all_pass,
    }
    OUT.write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"fitted": full_fit, "ALL_PASS": all_pass,
                      "gate_ok": {k: v["ok"] for k, v in gates.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
