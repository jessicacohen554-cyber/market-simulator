"""miso-142 gate G-A — attribute the MISO C3a gap by MONTH x HOUR-OF-DAY, in dollars.

No solve.  Reads the committed keeper bundle's ``hourly/system_<year>.parquet``
and the committed measured actual hourly series, and decomposes the signed
load-weighted annual gap onto a calendar surface.  This is the FIRST gate of
PREREG ``results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md``:
*attribution before anything else* — the owner's O1 window (Jun/Jul h8-20,
concentrated Jun 21-24 and all of July) is a HYPOTHESIS whose share is measured
here, not a premise.

Basis discipline (PREREG §2.1, the miso-133 ONE-BASIS bar).  Every price number
is the scorer's load-weighted RT basis; DA is carried as a separate companion
and never blended.  The instrument is miso-137's — ``model_hourly`` /
``actual_hourly`` / ``contrib`` are imported from
``_miso137_c3a_gap_decomposition`` rather than re-implemented, because miso-137
gate G-0(ii) verified that path reproduces the scorer's C3a model scalar to the
penny in all three years with additivity residual exactly 0.0.  Re-deriving the
comparator a third way is on DO-NOT-REDO (miso-140 PREREG S1).

The decomposition is exact and additive because both sides carry the same
weights (PREREG §2.1)::

    model_lw - actual_lw = sum_h W_h (p_h - a_h) / sum_h W_h
    C(S)                 = sum_{h in S} W_h (p_h - a_h) / sum_h W_h

so the 288 month x hour-of-day cells sum to the annual total with no residual.

TRAP 4 (calendar cherry-pick) counter-measurement: the FULL 12 x 24 surface is
emitted for every year and basis, with the owner's named windows marked ON it.
A window is never reported alone.

PREREG §4 percentage guard: a year whose |total gap| < $0.50/MWh gets absolute
dollar contributions only -- no shares -- because a share against a near-zero
denominator is not measuring a stable quantity (the miso-137 threshold bar).

NaN masking follows miso-137's own G-1 convention EXACTLY -- every array is
restricted to ``keep = isfinite(p) & isfinite(a) & (w > 0)`` before any
contribution is computed, so ``contrib``'s denominator is the kept weight and
the 288 cells sum to the kept-hours total.  This is not cosmetic: the 2025 RT
actual series carries NaN hours, and computing the surface on the unmasked
array returns a NaN annual total.  G-A0 caught exactly that on this probe's
first run -- recorded because a gate that only ever passes has not been tested.
Each year's kept-hour count is reported so the coverage is visible.

Probe hygiene (miso-140b §6): the REPO ROOT is on ``sys.path`` (not only
``src/``), and ``load_zonal_shares`` is asserted non-None even though this probe
takes its demand weights from the keeper's own committed sidecar, so the
assertion cannot rot if a later edit adds a per-zone consumer.

Usage::

    .venv/bin/python scripts/probes/_miso142_gap_attribution.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
# PROBE HYGIENE (miso-140b §6): the REPO ROOT, not just ``src/`` --
# ``eia930.zonal_shares._zonal_shares_from_raw`` imports
# ``scripts.data.curate_zonal_shares``; without the repo root ``load_demand``
# SILENTLY falls back to the static Gold-Book split (up to 6,747 MW per
# zone-hour on MISO 2025).
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso137_c3a_gap_decomposition import (  # noqa: E402
    HOURS,
    MONTH_START,
    actual_hourly,
    contrib,
    model_hourly,
    month_of_hour,
    scorer_model_scalar,
)

OUT = REPO / "results/calibration/_miso142_gap_attribution.json"

YEARS = (2023, 2024, 2025)  # rule 22: MISO holds no marker -- training window only
# PREREG §0: the committed per-year annual totals this gate must reproduce.
G_A0_EXPECT = {2023: -0.13, 2024: -1.93, 2025: -6.41}
G_A0_TOL = 0.02
# PREREG §4 percentage guard.
SHARE_GUARD_USD = 0.50

# PREREG §4 -- the owner's O1 windows, NAMED IN ADVANCE (Trap 4).
W1_MONTHS = (6, 7)
W1_HOD = (8, 21)  # h8-20 inclusive
W2_DATES = ((6, 21), (6, 24))  # Jun 21-24 inclusive, same hours


def day_of_year(hr: np.ndarray) -> np.ndarray:
    """0-based day index on the model's non-leap 8760 calendar."""
    return hr // 24


def day_of_month(hr: np.ndarray) -> np.ndarray:
    """1-31 day-of-month on the model's non-leap 8760 calendar."""
    mon = month_of_hour(hr)
    start_hour = np.array(MONTH_START)[mon - 1]
    return (hr - start_hour) // 24 + 1


def surface(p, a, w, hr) -> tuple[list[list[float]], float, float]:
    """The full 12 x 24 month x hour-of-day contribution grid, in $/MWh.

    Returns ``(grid, total, additivity_residual)``.  ``grid[m-1][h]`` is C(S)
    for month ``m`` hour-of-day ``h``; the 288 cells sum to ``total``.
    """
    mon, hod = month_of_hour(hr), hr % 24
    total = contrib(np.ones_like(p, dtype=bool), p, a, w)
    grid = np.zeros((12, 24))
    for m in range(1, 13):
        for h in range(24):
            sel = (mon == m) & (hod == h)
            grid[m - 1, h] = contrib(sel, p, a, w) if sel.any() else 0.0
    return (
        np.round(grid, 6).tolist(),
        round(total, 6),
        round(total - float(grid.sum()), 9),
    )


def window_stats(sel, p, a, w, total) -> dict:
    """Contribution, hours, and load-weighted model/actual levels for a window."""
    valid = sel & np.isfinite(p) & np.isfinite(a) & (w > 0)
    ww = w[valid]
    out = {
        "hours": int(valid.sum()),
        "C_usd_per_mwh": round(contrib(valid, p, a, w), 6),
        "model_lw": round(float((p[valid] * ww).sum() / ww.sum()), 4)
        if ww.sum() > 0
        else None,
        "actual_lw": round(float((a[valid] * ww).sum() / ww.sum()), 4)
        if ww.sum() > 0
        else None,
        "load_share_of_year": round(float(ww.sum() / w[w > 0].sum()), 6),
    }
    if out["model_lw"] is not None:
        out["level_pct_err"] = round(
            100.0 * (out["model_lw"] - out["actual_lw"]) / out["actual_lw"], 2
        )
    # PREREG §4: shares only when the denominator is not near zero.
    out["share_of_total"] = (
        round(out["C_usd_per_mwh"] / total, 4) if abs(total) >= SHARE_GUARD_USD else None
    )
    return out


def top_cells(grid: list[list[float]], n: int = 12) -> list[dict]:
    """The n most under-priced (most negative) month x hod cells."""
    g = np.asarray(grid)
    flat = np.argsort(g, axis=None)[:n]
    return [
        {
            "month": int(i // 24) + 1,
            "hod": int(i % 24),
            "C_usd_per_mwh": round(float(g.flat[i]), 6),
        }
        for i in flat
    ]


def main() -> None:
    # PROBE HYGIENE (miso-140b §6): assert the measured zonal-share route is
    # reachable, even though this probe's weights come from the committed
    # sidecar -- so the assertion cannot rot if a later edit adds a consumer.
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zs = load_zonal_shares("MISO", 2025, [z.name for z in get_iso_config("MISO").zones])
    assert zs is not None, (
        "load_zonal_shares returned None -- repo root is off sys.path and "
        "load_demand would SILENTLY use the static Gold-Book split (miso-140b §6)"
    )

    hr_full = np.arange(HOURS)

    def windows(hr: np.ndarray) -> dict[str, np.ndarray]:
        """The PREREG-named windows, evaluated on an arbitrary hour index."""
        mon, hod = month_of_hour(hr), hr % 24
        dom = day_of_month(hr)
        in_hod = (hod >= W1_HOD[0]) & (hod < W1_HOD[1])
        return {
            "W1_jun_jul_h8_20": np.isin(mon, W1_MONTHS) & in_hod,
            "W2_jun21_24_h8_20": (mon == W2_DATES[0][0])
            & (dom >= W2_DATES[0][1])
            & (dom <= W2_DATES[1][1])
            & in_hod,
            "jun_only_h8_20": (mon == 6) & in_hod,
            "jul_only_h8_20": (mon == 7) & in_hod,
            "complement_of_W1": ~(np.isin(mon, W1_MONTHS) & in_hod),
        }

    out: dict = {
        "prereg": "results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md",
        "gate": "G-A (attribution before anything else)",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "bundle": "results/calibration/miso132_ccmin_B",
        "instrument": "_miso137_c3a_gap_decomposition (reused, not rebuilt -- PREREG §2.1)",
        "basis": "scorer load-weighted; RT gated, DA companion, never blended",
        "share_guard_usd": SHARE_GUARD_USD,
        "years": {},
    }

    for year in YEARS:
        hours, p_full, W_full, zinfo = model_hourly(year)
        assert np.array_equal(hours, hr_full), "sidecar hour index is not 0..8759"
        rt, da = actual_hourly(year)

        yr: dict = {
            "scorer_model_scalar": round(scorer_model_scalar(zinfo), 4),
            "bases": {},
        }
        for bname, act_full in (("RT", rt), ("DA", da)):
            # miso-137 G-1 masking convention, verbatim: everything downstream
            # runs on the kept subset, so contrib's denominator is the kept
            # weight and the 288 cells sum to the kept-hours total.
            keep = np.isfinite(p_full) & np.isfinite(act_full) & (W_full > 0)
            p_h, act, W_h, hr = (
                p_full[keep],
                act_full[keep],
                W_full[keep],
                hr_full[keep],
            )
            mon, hod = month_of_hour(hr), hr % 24
            win = windows(hr)

            grid, total, resid = surface(p_h, act, W_h, hr)
            entry = {
                "kept_hours": int(keep.sum()),
                "dropped_hours": int(HOURS - keep.sum()),
                "total_gap_usd_per_mwh": total,
                "additivity_residual": resid,
                "month_hod_grid": grid,
                "top_under_priced_cells": top_cells(grid),
                "windows": {
                    k: window_stats(sel, p_h, act, W_h, total)
                    for k, sel in win.items()
                },
                "month_totals": {
                    str(m): round(contrib(mon == m, p_h, act, W_h), 6)
                    for m in range(1, 13)
                },
                "hod_totals": {
                    str(h): round(contrib(hod == h, p_h, act, W_h), 6)
                    for h in range(24)
                },
            }
            if bname == "RT":
                # G-A0: the gate that licenses everything downstream.
                exp = G_A0_EXPECT[year]
                entry["G_A0"] = {
                    "expected_total": exp,
                    "measured_total": total,
                    "delta": round(total - exp, 6),
                    "tol": G_A0_TOL,
                    "pass_total": bool(abs(total - exp) <= G_A0_TOL),
                    "pass_additivity": bool(abs(resid) < 1e-9),
                }
            yr["bases"][bname] = entry
        out["years"][str(year)] = yr

    OUT.write_text(json.dumps(out, indent=1))

    # ---- console readout -------------------------------------------------
    print("=" * 78)
    print("miso-142 G-A -- gap attribution by month x hour-of-day (RT, load-weighted)")
    print("=" * 78)
    for year in YEARS:
        rtv = out["years"][str(year)]["bases"]["RT"]
        g0 = rtv["G_A0"]
        print(
            f"\n{year}  total {rtv['total_gap_usd_per_mwh']:+.4f} $/MWh  "
            f"({rtv['kept_hours']} h kept, {rtv['dropped_hours']} dropped)  "
            f"[G-A0 total {'PASS' if g0['pass_total'] else 'FAIL'} "
            f"(exp {g0['expected_total']:+.2f}, d {g0['delta']:+.4f}); "
            f"additivity {'PASS' if g0['pass_additivity'] else 'FAIL'} "
            f"({rtv['additivity_residual']:.2e})]"
        )
        for k, v in rtv["windows"].items():
            share = (
                f"{100 * v['share_of_total']:6.1f}%"
                if v["share_of_total"] is not None
                else "  n/a "
            )
            lvl = (
                f"model {v['model_lw']:7.2f} vs actual {v['actual_lw']:7.2f} "
                f"({v['level_pct_err']:+6.1f}%)"
                if v["model_lw"] is not None
                else ""
            )
            print(
                f"   {k:22s} {v['hours']:5d} h  C {v['C_usd_per_mwh']:+7.4f}  "
                f"share {share}  {lvl}"
            )
        print("   month totals ($/MWh): ", end="")
        print(
            " ".join(
                f"{m}:{rtv['month_totals'][str(m)]:+.2f}" for m in range(1, 13)
            )
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
