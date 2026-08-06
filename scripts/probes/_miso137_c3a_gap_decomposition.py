"""miso-137 lane (a) — decompose the MISO mean-LMP gap into tail and BODY parts.

No solve. Reads the committed keeper bundle's ``hourly/system_<year>.parquet``
and the committed measured actual hourly series, reproduces the scorer's C3a
load-weighted basis exactly (validated against the committed ``rt_lw`` /
``da_lw`` bench scalars and the scorer's own model scalar), then splits the
signed annual gap into the actual-spike-hour component (the C3c frontier
component, out of admissible scope) and the BODY component, and cuts the body
by season x hour-of-day.

Basis discipline (CLAUDE.md rule 13 / the miso-133 ONE-BASIS bar): every level
quoted is the scorer's load-weighted basis and nothing else, and the RT and DA
bases are decomposed separately and never blended. The decomposition is EXACT
and additive because both sides carry the same weights -- see PREREG
``results/calibration/PREREG-miso137-c3a-gap-decomposition-2026-08-06.md`` §1:

    model_lw - actual_lw = sum_h W_h (p_h - a_h) / sum_h W_h

so any hour-set's contribution C(S) = sum_{h in S} W_h (p_h - a_h) / sum_h W_h
and the parts of any partition sum to the total with no residual term.

Usage:
    python scripts/probes/_miso137_c3a_gap_decomposition.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/miso132_ccmin_B"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"
BENCH = REPO / "frontend/data/backcast/bench/MISO"
OUT = REPO / "results/calibration/_miso137_c3a_gap_decomposition.json"

YEARS = (2023, 2024, 2025)  # rule 22: training window only
HOURS = 8760
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_START = tuple(int(sum(DAYS_IN_MONTH[:m]) * 24) for m in range(12))

# PREREG §2 tolerances
G0_TOL_USD = 0.05
G0_TOL_PP = 0.2
G1_MIN_HOURS = 8000
# PREREG §3
TAIL_MAIN = 200.0
TAIL_SENS = (100.0, 500.0)
SPILL_K_MAIN = 3
SPILL_K_ALL = (1, 3, 6)
DOMINANT_SHARE = 0.25
SEASONS = {
    "winter": (12, 1, 2),
    "spring": (3, 4, 5),
    "summer": (6, 7, 8),
    "fall": (9, 10, 11),
}
BLOCKS = {"h00-05": (0, 6), "h06-11": (6, 12), "h12-17": (12, 18), "h18-23": (18, 24)}


def month_of_hour(hr: np.ndarray) -> np.ndarray:
    """1-12 month label for chronological hour-of-year indices."""
    return np.clip(np.searchsorted(np.array(MONTH_START), hr, side="right"), 1, 12)


def model_hourly(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Return ``(hours, p_h, W_h, zone_scalar_info)`` for the P1 pass.

    ``p_h`` is the model's load-weighted system price per hour and ``W_h`` the
    model's total demand per hour; ``zone_scalar_info`` carries the scorer's
    per-zone ``p``/``d`` payload fields so C3a's model scalar can be
    reproduced with the payload's own rounding.
    """
    df = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    piv_p = df.pivot_table(index="hour", columns="zone", values="price")
    piv_d = df.pivot_table(index="hour", columns="zone", values="demand")
    piv_d = piv_d.reindex(columns=piv_p.columns)
    hours = piv_p.index.to_numpy()
    P = piv_p.to_numpy(float)
    D = np.nan_to_num(piv_d.to_numpy(float))
    W = D.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        p_h = np.where(W > 0, (P * D).sum(axis=1) / W, np.nan)
    # scorer payload fields: p_z (2 dp), d_z in millions (4 dp)
    zinfo = {}
    for j, z in enumerate(piv_p.columns):
        dtot = float(D[:, j].sum())
        pz = (
            float((P[:, j] * D[:, j]).sum()) / dtot
            if dtot > 0
            else float(P[:, j].mean())
        )
        zinfo[str(z)] = {"p": round(pz, 2), "d": round(dtot / 1e6, 4)}
    return hours, p_h, W, zinfo


def scorer_model_scalar(zinfo: dict) -> float:
    """Reproduce ``calibration_verdict._wmean`` over the payload's zone fields."""
    num = sum(v["p"] * v["d"] for v in zinfo.values())
    den = sum(v["d"] for v in zinfo.values())
    return num / den


def actual_hourly(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Dense (rt, da) actual arrays on the model's chronological 8760 calendar."""
    a = pd.read_parquet(ACTUAL)
    a = a[a["year"] == year].sort_values("hour")
    rt = np.full(HOURS, np.nan)
    da = np.full(HOURS, np.nan)
    hr = a["hour"].to_numpy(int)
    ok = hr < HOURS
    rt[hr[ok]] = a["rt"].to_numpy(float)[ok]
    da[hr[ok]] = a["da"].to_numpy(float)[ok]
    return rt, da


def bench_scalars(year: int) -> dict:
    b = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["avgLMP"]
    return b


def measured_system_demand(year: int) -> np.ndarray | None:
    """The deriver's own weights: ``eia_loader.load_demand`` summed over zones."""
    try:
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia_loader import load_demand

        return np.asarray(load_demand("MISO", year, get_iso_config("MISO"))).sum(axis=0)
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"  (measured demand unavailable: {exc})")
        return None


def lw(vals: np.ndarray, w: np.ndarray) -> float:
    v = np.isfinite(vals) & (w > 0)
    return float((vals[v] * w[v]).sum() / w[v].sum())


def contrib(mask: np.ndarray, p: np.ndarray, a: np.ndarray, w: np.ndarray) -> float:
    """C(S) in $/MWh -- the signed gap contribution of the hour-set ``mask``."""
    return float((w[mask] * (p[mask] - a[mask])).sum() / w.sum())


def neighbourhood(mask: np.ndarray, k: int) -> np.ndarray:
    """Hours within +/-k of any True in ``mask`` (same-array index adjacency)."""
    out = mask.copy()
    for s in range(1, k + 1):
        out[s:] |= mask[:-s]
        out[:-s] |= mask[s:]
    return out


def decompose(p: np.ndarray, a: np.ndarray, w: np.ndarray, hr: np.ndarray) -> dict:
    """Full tail/body decomposition for one basis-year on already-masked arrays."""
    total = contrib(np.ones_like(p, dtype=bool), p, a, w)
    rec: dict = {"total_gap": round(total, 4), "thresholds": {}}
    for thr in (TAIL_MAIN, *TAIL_SENS):
        tail = a > thr
        body = ~tail
        c_tail, c_body = contrib(tail, p, a, w), contrib(body, p, a, w)
        entry = {
            "tail_hours": int(tail.sum()),
            "C_tail": round(c_tail, 4),
            "C_body": round(c_body, 4),
            "body_share": round(c_body / total, 4) if total != 0 else None,
            "additivity_residual": round(total - (c_tail + c_body), 9),
        }
        if thr == TAIL_MAIN:
            spill = {}
            for k in SPILL_K_ALL:
                excl = body & ~neighbourhood(tail, k)
                c_ex = contrib(excl, p, a, w)
                spill[f"k{k}"] = {
                    "C_body_excl": round(c_ex, 4),
                    "spill": round(1 - c_ex / c_body, 4) if c_body != 0 else None,
                    "hours_excluded": int(body.sum() - excl.sum()),
                }
            entry["spillover"] = spill
            # season x hour-of-day map of the BODY contribution
            mon = month_of_hour(hr)
            hod = hr % 24
            cells = {}
            for sname, months in SEASONS.items():
                for bname, (lo, hi) in BLOCKS.items():
                    sel = body & np.isin(mon, months) & (hod >= lo) & (hod < hi)
                    c = contrib(sel, p, a, w)
                    cells[f"{sname}/{bname}"] = {
                        "C": round(c, 4),
                        "hours": int(sel.sum()),
                        "share_of_body": round(c / c_body, 4) if c_body else None,
                    }
            entry["season_hod"] = cells
            entry["dominant_cells"] = sorted(
                (
                    k
                    for k, v in cells.items()
                    if (v["share_of_body"] or 0) >= DOMINANT_SHARE
                ),
                key=lambda k: -abs(cells[k]["C"]),
            )
            # full 12x24 grid, so the blocking cannot hide structure
            grid = np.full((12, 24), np.nan)
            for m in range(1, 13):
                for h in range(24):
                    sel = body & (mon == m) & (hod == h)
                    if sel.any():
                        grid[m - 1, h] = contrib(sel, p, a, w)
            entry["month_hod_grid"] = np.round(grid, 5).tolist()
        rec["thresholds"][f"gt{int(thr)}"] = entry
    return rec


# --------------------------------------------------------------------------
# POST-VERDICT DESCRIPTIVE BLOCK.
# Everything below runs AFTER the PREREG §4 verdict is already determined by
# the §3 statistics above, and CANNOT change it: the pre-registered guard
# ("a verdict that flips across the $100/$500 sensitivity is reported as
# threshold-dependent and NOT asserted") is evaluated on the §3 numbers alone.
# These statistics are DESCRIPTIVE — they characterise WHY the threshold cut
# is unstable and WHERE the window map points. They are not adjudicating, and
# no decision rule reads them.
# --------------------------------------------------------------------------
PRICE_BANDS = (
    (-1e9, 0.0),
    (0.0, 20.0),
    (20.0, 40.0),
    (40.0, 60.0),
    (60.0, 100.0),
    (100.0, 200.0),
    (200.0, 500.0),
    (500.0, 1e9),
)


def describe(p: np.ndarray, a: np.ndarray, w: np.ndarray, hr: np.ndarray) -> dict:
    """Descriptive (non-adjudicating) characterisation of the gap's structure."""
    tot_w = w.sum()
    strata = {}
    for lo, hi in PRICE_BANDS:
        sel = (a > lo) & (a <= hi)
        if not sel.any():
            continue
        strata[f"({lo:g},{hi:g}]"] = {
            "hours": int(sel.sum()),
            "C": round(float((w[sel] * (p[sel] - a[sel])).sum() / tot_w), 4),
            "actual_mean": round(float(a[sel].mean()), 2),
            "model_mean": round(float(p[sel].mean()), 2),
        }
    mon, hod = month_of_hour(hr), hr % 24
    windows = {}
    for name, months, lo, hi in (
        ("summer_afternoon", (6, 7, 8), 12, 18),
        ("summer_night", (6, 7, 8), 0, 6),
        ("fall_afternoon", (9, 10, 11), 12, 18),
    ):
        sel = np.isin(mon, months) & (hod >= lo) & (hod < hi)
        windows[name] = {
            "hours": int(sel.sum()),
            "model_lw": round(float((p[sel] * w[sel]).sum() / w[sel].sum()), 2),
            "actual_lw": round(float((a[sel] * w[sel]).sum() / w[sel].sum()), 2),
            "C": round(float((w[sel] * (p[sel] - a[sel])).sum() / tot_w), 4),
        }
    return {"price_strata": strata, "windows": windows}


def main() -> None:
    record: dict = {
        "session": "miso-137",
        "lane": "(a) gap decomposition",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "prereg": "results/calibration/PREREG-miso137-c3a-gap-decomposition-2026-08-06.md",
        "years": {},
    }
    for year in YEARS:
        print(f"\n=== {year} " + "=" * 60)
        hours, p_full, w_model, zinfo = model_hourly(year)
        rt_full, da_full = actual_hourly(year)
        bench = bench_scalars(year)
        y: dict = {"zones": sorted(zinfo), "n_model_hours": int(len(hours))}

        # ---- G-0 basis validation -------------------------------------
        w_meas = measured_system_demand(year)
        g0: dict = {}
        # model scalar, scorer emulation (payload rounding) and exact
        m_scorer = scorer_model_scalar(zinfo)
        m_exact = lw(p_full, w_model)
        g0["model_scalar_scorer"] = round(m_scorer, 4)
        g0["model_scalar_exact"] = round(m_exact, 4)
        for kind, act_full in (("rt", rt_full), ("da", da_full)):
            key = f"{kind}_lw"
            committed = bench.get(key)
            # (a) deriver weights (measured system demand) where available
            rep_meas = lw(act_full, w_meas) if w_meas is not None else None
            # (b) sidecar weights (model demand summed over zones)
            w_side = np.zeros(HOURS)
            w_side[hours] = w_model
            rep_side = lw(act_full, w_side)
            g0[key] = {
                "committed": committed,
                "repro_deriver_weights": None
                if rep_meas is None
                else round(rep_meas, 4),
                "repro_sidecar_weights": round(rep_side, 4),
                "delta_committed_vs_sidecar": (
                    None if committed is None else round(rep_side - committed, 4)
                ),
                "pass": (
                    committed is not None and abs(rep_side - committed) <= G0_TOL_USD
                ),
            }
            pct = (m_scorer - committed) / committed * 100 if committed else None
            g0[f"{kind}_pct_err_reproduced"] = None if pct is None else round(pct, 2)
        y["G0"] = g0
        print(f"  G-0 model scalar: scorer {m_scorer:.2f} exact {m_exact:.2f}")
        for kind in ("rt", "da"):
            e = g0[f"{kind}_lw"]
            print(
                f"  G-0 {kind}_lw committed {e['committed']} "
                f"repro(sidecar) {e['repro_sidecar_weights']} "
                f"repro(deriver) {e['repro_deriver_weights']} -> "
                f"{'PASS' if e['pass'] else 'FAIL'}   "
                f"pct_err {g0[f'{kind}_pct_err_reproduced']}"
            )

        # ---- G-1 coverage + masking -----------------------------------
        p = np.full(HOURS, np.nan)
        w = np.zeros(HOURS)
        p[hours] = p_full
        w[hours] = w_model
        hr_all = np.arange(HOURS)
        for kind, act_full in (("rt", rt_full), ("da", da_full)):
            keep = np.isfinite(p) & np.isfinite(act_full) & (w > 0)
            y[f"{kind}_kept_hours"] = int(keep.sum())
            if keep.sum() < G1_MIN_HOURS:
                y[kind] = {"skipped": "G-1 coverage"}
                continue
            rec = decompose(p[keep], act_full[keep], w[keep], hr_all[keep])
            rec["model_lw"] = round(lw(p[keep], w[keep]), 4)
            rec["actual_lw"] = round(lw(act_full[keep], w[keep]), 4)
            rec["descriptive_post_verdict"] = describe(
                p[keep], act_full[keep], w[keep], hr_all[keep]
            )
            y[kind] = rec
            m = rec["thresholds"][f"gt{int(TAIL_MAIN)}"]
            print(
                f"  [{kind.upper()}] kept {int(keep.sum())}h  gap {rec['total_gap']:+.3f}"
                f"  | tail({m['tail_hours']}h) {m['C_tail']:+.3f}"
                f"  body {m['C_body']:+.3f}  body_share {m['body_share']}"
                f"  | spill(k3) {m['spillover']['k3']['spill']}"
            )
            if m["dominant_cells"]:
                print(f"        dominant body cells: {m['dominant_cells']}")
        record["years"][str(year)] = y

    OUT.write_text(json.dumps(record, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
