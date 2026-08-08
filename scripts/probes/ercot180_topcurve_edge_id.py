"""ercot-180 edge identification: conduct-structure breaks above p97 (form b).

Executes PRECOMMIT-ercot180-top-scoped-grain-2026-08-08.md §2 EXACTLY as fixed
there, BEFORE any derive or solve. Residual-blind: reads SUBMITTED SCED2 offer
curves only — never realized prices, clearing outcomes, LMPs, model outputs or
any residual.

Instrument (all constants fixed in the precommit, never swept):

* Corpus: delivery-2023 NP3-965 60-Day SCED Gen Resource Data (the only
  full-coverage year). 2024/2025 are read ONLY for coverage disclosure.
* Statistic: per (hour, resource) top-of-curve conduct — the MW-weighted
  distribution of each ON-status merchant-gas resource's LAST-3 finite SCED2
  segment prices as delivered-gas HR multipliers (HCAP-clipped), reusing the
  wall derive's parsers unchanged (rule 19: CLASS_OF_RESTYPE scope, CC + CT).
* Break detection, restricted to hours ranked > 0.97 on the within-year
  net-load percentile axis: scan candidate edges on the top-slice hours' own
  rank grid; at each candidate the MW-weighted two-sample Kolmogorov–Smirnov
  distance between the below/above sub-populations (pooled across classes
  decides; per-class profiles reported). A SHAPE BREAK = the profile argmax
  with (i) >= MIN_HOURS hours each side and (ii) a day-block permutation
  p-value < P_BAR. Recursive within resulting sub-bins, hard cap MAX_EDGES.
* KS is computed on a fixed common quantile grid of the pooled top-slice
  multiplier distribution (GRID_N points) — a deterministic implementation of
  the same statistic, disclosed here.

Output: results/calibration/ercot180_edge_identification.json (KS profiles,
chosen edges + p-values, per-sub-bin 2023 hour/interval/MW counts, 2024/2025
coverage disclosure, source inventories).

Zero fitted scalars: the edges are positions found by this instrument; the
instrument's constants are identification-instrument constants pre-registered
in the precommit (rule 23 [R-DOF] discipline).
"""

from __future__ import annotations

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
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
)
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _READ_COLS,
    _SCED2_MW,
    _SCED2_PR,
    _STD_TZ,
    CLASS_OF_RESTYPE,
    _coerce_sced_numeric,
    _delivery_year_rows,
    _sced_source_files,
)

OUT_PATH = REPO / "results" / "calibration" / "ercot180_edge_identification.json"

# ---- precommit §2 instrument constants (FIXED, never swept) ----
TOP_FLOOR = 0.97  # the existing family top edge; identification is above it
LAST_K = 3  # last-K finite SCED2 steps = "top of curve"
MIN_HOURS = 30  # minimum 2023 hours per resulting sub-bin
P_BAR = 0.01  # day-block permutation p-value bar
MAX_EDGES = 2  # hard bound on new edges
N_PERM = 999  # permutation count (resolution 0.001 at the 0.01 bar)
GRID_N = 1024  # common quantile grid for the weighted-KS implementation
SEED = 180  # deterministic permutation stream (session number)


def _top_curve_rows(year: int, pct: np.ndarray) -> tuple[pd.DataFrame, list[str]]:
    """Stream the year's shards -> top-of-curve segment rows for ranked>floor hours.

    Returns (frame with hoy, day, cls, mult, mw) and the source file names.
    Mirrors the wall derive's streaming discipline (one shard in memory at a
    time); rows are filtered to hours ranked > TOP_FLOOR before segment
    extraction so the frame stays small.
    """
    gas_day = _gas_day_series()
    top_hoy = set(np.flatnonzero(pct > TOP_FLOOR).tolist())
    files = _sced_source_files(year)
    parts: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, year)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.str.startswith("ON")].copy()
        if df.empty:
            continue
        ts = pd.to_datetime(df["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert(_STD_TZ)
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        df = df.loc[np.asarray(ok)].copy()
        if df.empty:
            continue
        hoy = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        keep = np.isin(hoy, list(top_hoy))
        if not keep.any():
            continue
        df = df.loc[keep].copy()
        hoy = hoy[keep]
        dates = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)][keep]
        gd = gas_day.reindex(pd.DatetimeIndex(dates)).to_numpy(float)
        df = _coerce_sced_numeric(df)
        MW = df[_SCED2_MW].to_numpy(float)
        PR = df[_SCED2_PR].to_numpy(float)
        valid = np.isfinite(MW) & np.isfinite(PR)
        n = len(df)
        # per-step widths against the previous finite step's MW (curve steps
        # are cumulative MW breakpoints, the wall derive's own convention)
        width = np.zeros_like(MW)
        prev = np.zeros(n)
        for k in range(MW.shape[1]):
            q = MW[:, k]
            v = valid[:, k]
            width[:, k] = np.where(v, np.maximum(q - prev, 0.0), 0.0)
            prev = np.where(v, np.maximum(prev, q), prev)
        # last-K finite steps per row
        cnt_from_end = np.cumsum(valid[:, ::-1], axis=1)[:, ::-1]
        lastk = valid & (cnt_from_end <= LAST_K)
        take = lastk & (width > 0) & (gd[:, None] > 0)
        if not take.any():
            continue
        r, c = np.nonzero(take)
        parts.append(
            pd.DataFrame(
                {
                    "hoy": hoy[r],
                    "day": hoy[r] // 24,
                    "cls": df["Resource Type"].map(CLASS_OF_RESTYPE).to_numpy()[r],
                    "mult": np.minimum(PR[r, c], HCAP_USD_MWH) / gd[r],
                    "mw": width[r, c],
                }
            )
        )
    if not parts:
        return pd.DataFrame(columns=["hoy", "day", "cls", "mult", "mw"]), [
            p.name for p in files
        ]
    return pd.concat(parts, ignore_index=True), [p.name for p in files]


def _hour_histograms(
    rows: pd.DataFrame, grid: np.ndarray, hoys: np.ndarray
) -> np.ndarray:
    """(n_hours, len(grid)) MW-weight histograms of mult binned on the grid."""
    pos = {h: i for i, h in enumerate(hoys)}
    hi = rows["hoy"].map(pos).to_numpy(int)
    gi = np.clip(
        np.searchsorted(grid, rows["mult"].to_numpy(), side="right") - 1,
        0,
        len(grid) - 1,
    )
    H = np.zeros((len(hoys), len(grid)))
    np.add.at(H, (hi, gi), rows["mw"].to_numpy())
    return H


def _ks(H: np.ndarray, mask_lo: np.ndarray) -> float:
    """Weighted KS between the pooled histograms of mask_lo vs its complement."""
    lo = H[mask_lo].sum(axis=0)
    hi = H[~mask_lo].sum(axis=0)
    if lo.sum() <= 0 or hi.sum() <= 0:
        return 0.0
    return float(np.max(np.abs(np.cumsum(lo) / lo.sum() - np.cumsum(hi) / hi.sum())))


def _perm_p(
    H: np.ndarray,
    ranks: np.ndarray,
    days: np.ndarray,
    lo_bound: float,
    hi_bound: float,
    edge: float,
    obs_ks: float,
    rng: np.random.Generator,
) -> float:
    """Day-block permutation p-value for the split at ``edge`` within a segment."""
    sel = (ranks > lo_bound) & (ranks <= hi_bound)
    idx = np.flatnonzero(sel)
    order = idx[np.argsort(ranks[idx])]
    n_lo = int(np.sum(ranks[order] <= edge))
    seg_days = days[order]
    blocks: dict[int, list[int]] = {}
    for i, d in zip(order, seg_days):
        blocks.setdefault(int(d), []).append(int(i))
    keys = list(blocks)
    hits = 0
    for _ in range(N_PERM):
        rng.shuffle(keys)
        pseudo: list[int] = []
        for k in keys:
            pseudo.extend(blocks[k])
            if len(pseudo) >= n_lo:
                break
        mask_lo = np.zeros(len(ranks), bool)
        mask_lo[pseudo[:n_lo]] = True
        mask_seg = np.zeros(len(ranks), bool)
        mask_seg[order] = True
        # KS within the segment: below-set vs (segment minus below-set)
        lo_h = H[mask_lo].sum(axis=0)
        hi_h = H[mask_seg & ~mask_lo].sum(axis=0)
        if lo_h.sum() <= 0 or hi_h.sum() <= 0:
            ks = 0.0
        else:
            ks = float(
                np.max(np.abs(np.cumsum(lo_h) / lo_h.sum() - np.cumsum(hi_h) / hi_h.sum()))
            )
        if ks >= obs_ks:
            hits += 1
    return (1 + hits) / (N_PERM + 1)


def main() -> int:
    pct23 = _netload_pct(2023)
    rows, files23 = _top_curve_rows(2023, pct23)
    if rows.empty:
        raise SystemExit("no top-slice rows found in the delivery-2023 corpus")

    hoys = np.sort(rows["hoy"].unique())
    ranks = pct23[hoys]
    days = hoys // 24
    grid = np.unique(
        np.quantile(
            rows["mult"].to_numpy(),
            np.linspace(0.0, 1.0, GRID_N),
        )
    )
    grid_n = len(grid)
    H_pool = _hour_histograms(rows, grid, hoys)
    H_cls = {
        c: _hour_histograms(rows[rows["cls"] == c], grid, hoys)
        for c in sorted(rows["cls"].unique())
    }

    rng = np.random.default_rng(SEED)
    edges: list[dict] = []
    segments = [(TOP_FLOOR, 1.0 + 1e-12)]
    profiles: list[dict] = []
    while len(edges) < MAX_EDGES:
        best = None
        for lo, hi in segments:
            sel = (ranks > lo) & (ranks <= hi)
            idx = np.flatnonzero(sel)
            order = idx[np.argsort(ranks[idx])]
            prof = []
            for j in range(MIN_HOURS, len(order) - MIN_HOURS + 1):
                edge = float(ranks[order[j - 1]])
                if j < len(order) and float(ranks[order[j]]) == edge:
                    continue
                mask_lo = np.zeros(len(ranks), bool)
                mask_lo[order[:j]] = True
                lo_h = H_pool[mask_lo].sum(axis=0)
                hi_h = H_pool[np.isin(np.arange(len(ranks)), order) & ~mask_lo].sum(axis=0)
                if lo_h.sum() <= 0 or hi_h.sum() <= 0:
                    continue
                ks = float(
                    np.max(
                        np.abs(np.cumsum(lo_h) / lo_h.sum() - np.cumsum(hi_h) / hi_h.sum())
                    )
                )
                prof.append({"edge": edge, "n_lo": j, "n_hi": int(len(order) - j), "ks": ks})
            profiles.append({"segment": [lo, min(hi, 1.0)], "profile": prof})
            if prof:
                cand = max(prof, key=lambda r: r["ks"])
                if best is None or cand["ks"] > best["ks"]:
                    best = {**cand, "segment": (lo, hi)}
        if best is None:
            break
        p = _perm_p(
            H_pool, ranks, days, best["segment"][0], best["segment"][1],
            best["edge"], best["ks"], rng,
        )
        accepted = p < P_BAR
        edges.append(
            {
                "edge": best["edge"],
                "ks": best["ks"],
                "p_value": p,
                "n_lo": best["n_lo"],
                "n_hi": best["n_hi"],
                "segment": [best["segment"][0], min(best["segment"][1], 1.0)],
                "accepted": bool(accepted),
            }
        )
        if not accepted:
            break
        lo, hi = best["segment"]
        segments.remove((lo, hi))
        segments += [(lo, best["edge"]), (best["edge"], hi)]

    accepted_edges = sorted(e["edge"] for e in edges if e["accepted"])

    # per-class KS at the accepted edges (reported, not deciding)
    per_class = {}
    for c, Hc in H_cls.items():
        per_class[c] = [
            {
                "edge": e,
                "ks": _ks_at(Hc, ranks, e),
            }
            for e in accepted_edges
        ]

    # coverage: 2023 per final sub-bin; 2024/2025 disclosure
    bounds = [TOP_FLOOR] + accepted_edges + [1.0 + 1e-12]
    cov = {}
    for y in (2023, 2024, 2025):
        if y == 2023:
            r, files = rows, files23
            pct = pct23
        else:
            pct = _netload_pct(y)
            r, files = _top_curve_rows(y, pct)
        ycov = {"source_files_n": len(files)}
        for b in range(len(bounds) - 1):
            sub = r[(pct[r["hoy"]] > bounds[b]) & (pct[r["hoy"]] <= bounds[b + 1])]
            ycov[f"bin_{b}"] = {
                "lo": bounds[b],
                "hi": min(bounds[b + 1], 1.0),
                "hours": int(sub["hoy"].nunique()),
                "rows": int(len(sub)),
                "mw_sum": float(sub["mw"].sum()),
                "by_class": {
                    c: int(sub[sub["cls"] == c]["hoy"].nunique())
                    for c in sorted(r["cls"].unique())
                },
            }
        cov[str(y)] = ycov

    record = {
        "probe": "ercot180_topcurve_edge_id",
        "precommit": "docs/PRECOMMIT-ercot180-top-scoped-grain-2026-08-08.md §2",
        "constants": {
            "TOP_FLOOR": TOP_FLOOR,
            "LAST_K": LAST_K,
            "MIN_HOURS": MIN_HOURS,
            "P_BAR": P_BAR,
            "MAX_EDGES": MAX_EDGES,
            "N_PERM": N_PERM,
            "GRID_N_requested": 1024,
            "GRID_N_effective": grid_n,
            "SEED": SEED,
        },
        "identification_year": 2023,
        "top_slice_hours_2023": int(len(hoys)),
        "top_slice_rows_2023": int(len(rows)),
        "edge_tests": edges,
        "accepted_edges": accepted_edges,
        "per_class_ks_at_accepted": per_class,
        "ks_profiles": profiles,
        "coverage": cov,
        "residual_blind_attestation": (
            "inputs: SCED2 submitted curves, HH+basis delivered gas, EIA-930 "
            "net load. No LMPs, no clearing outcomes, no model outputs."
        ),
    }
    OUT_PATH.write_text(json.dumps(record, indent=1))
    print(f"accepted edges: {accepted_edges}")
    for e in edges:
        print(
            f"  edge {e['edge']:.6f} ks={e['ks']:.4f} p={e['p_value']:.4f} "
            f"n=({e['n_lo']},{e['n_hi']}) accepted={e['accepted']}"
        )
    print(f"wrote {OUT_PATH}")
    return 0


def _ks_at(H: np.ndarray, ranks: np.ndarray, edge: float) -> float:
    """Whole-top-slice KS split at ``edge`` (reporting helper)."""
    mask_lo = ranks <= edge
    return _ks(H, mask_lo)


if __name__ == "__main__":
    raise SystemExit(main())
