"""pjm-h9 — apply the M1 mixture bound to PJM coal's min-load rows. ZERO LP.

Pre-registration: ``docs/PRECOMMIT-pjm-h9-coal-only-comparator-2026-09-16.md`` §4.
Reads the quantile artifact written by ``_pjm_h9_longrun_mixture_bound.py`` (whose G-REPRO
hard stop must have passed) and answers the pre-registered question:

    phi(w) = (measured_blend - lo(w)) / (measured_blend - model_bid)

the share of h8's own committed-band correction that a one-sided gas-steam admixture of
capacity weight ``w`` could account for, in its WORST case, where

    lo(w) = Q_blend(0.5 * (1 - w))          [PRECOMMIT §3]

Decision, fixed before any number was computed: **phi(w-hat) < 0.25 => (B-NO)** the comparator
is exonerated and route (a) is the object; **> 0.75 => (B-YES)** the comparator is the
explanation; otherwise **(B-PARTIAL)**. ``w-hat = 0.1893`` is the independent model-fleet
admixture estimate from the committed h8 ladder. ``w-half`` and ``w-star`` (the weights at
which phi = 0.5 and 1.0) are reported as the threshold-free form.

WHY THE BOUND COMPOSES. ``_pjm_midcurve_row_target`` maps a row's within-plant share and each
hour's net-load bin onto the ladder, so the reported ``measured_implied_gas_hr`` is a
POSITIVE-weighted average of ladder cells. A positive-weighted average of per-cell lower bounds
is a lower bound on the same average of the coal-only cells, provided ``w`` is common across
cells — which it is, being one fleet-level capacity share. So the per-cell bound carries
through to the row-level number without further assumption.

METHOD. The model's OWN code is the measuring instrument (the pjm-h8 method note): the fleet is
built once per year on the keeper's own recipe, ``_pjm_midcurve_context`` is built once, and
only the ``LONG_RUN`` ladder table is swapped per ``w``. Nothing here re-implements the
targeting, so every column is byte-for-byte what the armed mechanism would apply.

Run: ``python3 scripts/probes/_pjm_h9_apply_bound.py [--years 2023 2024 2025]``
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes._pjm_h8_offer_ladder import (  # noqa: E402
    BUNDLE_FOR_YEAR,
    COAL_CLASSES,
    _band,
    build,
)

QUANT = REPO / "results/calibration/_pjm_h9_longrun_mixture_bound.json"
OUT = REPO / "results/calibration/_pjm_h9_bound_applied.json"


def _out_path(ref: str) -> Path:
    """One artifact per blend reference so the two never overwrite each other."""
    return OUT if ref == "own" else OUT.with_name(f"_pjm_h9_bound_applied_{ref}.json")


#: Independent model-fleet admixture estimate (committed h8 ladder, 2023):
#: ST_GAS 11,525.5 MW of 60,897.2 MW mapped onto LONG_RUN.
W_HAT = 0.1893
#: Admixture weights the curve is reported on. A grid, never a selection.
W_GRID = [0.0, 0.05, 0.10, 0.1893, 0.25, 0.30, 0.40, 0.50, 0.60, 0.75, 0.90]
#: The two rows the question turns on; `committed` is load-bearing (h8 G-5: it
#: produced 87.7 % of the arm's coal energy change, `mustrun` 8.4 %).
ROWS = ("committed", "mustrun")


def ladder_at(qdoc: dict, seg: str, year: int, p: float) -> np.ndarray:
    """(n_bins, n_shares) ladder at blended quantile *p*, nearest stored p."""
    pg = np.asarray(qdoc["pgrid"], dtype=float)
    j = int(np.argmin(np.abs(pg - p)))
    bins = qdoc["quantiles"][seg][str(year)]
    return np.array([[row[j] for row in b] for b in bins], dtype=float)


def frozen_ladder(surface: dict, seg: str, year: int) -> np.ndarray:
    """(n_bins, n_shares) ladder straight off the COMMITTED frozen surface."""
    entry = surface[seg]
    lad = entry.get("years", {}).get(str(year)) or entry["pooled"]
    return np.array([[float(pt[1]) for pt in b] for b in lad], dtype=float)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--allow-provisional",
        action="store_true",
        help=(
            "proceed on a quantile artifact whose G-REPRO hard stop FAILED. Every "
            "number is then PROVISIONAL and stamped so in the output. Overriding the "
            "gate is deliberate and on the record; it is never the default."
        ),
    )
    ap.add_argument(
        "--blend-reference",
        choices=["own", "frozen"],
        default="own",
        help=(
            "which p=0.5 ladder is the 'measured_blend' the correction is measured "
            "from: this probe's own re-derivation (default) or the COMMITTED frozen "
            "surface. Running BOTH is the robustness check that says whether a "
            "G-REPRO failure can move the verdict at all."
        ),
    )
    args = ap.parse_args(argv)
    t0 = time.time()

    qdoc = json.loads(QUANT.read_text())
    provisional = not qdoc.get("g_repro", {}).get("pass")
    if provisional and not args.allow_provisional:
        print(
            "G-REPRO did not pass in the quantile artifact — refusing to proceed.\n"
            "Pass --allow-provisional to override; every number is then PROVISIONAL."
        )
        return 1
    pg = np.asarray(qdoc["pgrid"], dtype=float)
    frozen_surface = json.loads(
        (
            REPO / "data/raw/_validation-source/pjm_offer_midcurve_condbinned.json"
        ).read_text()
    )

    out: dict = {
        "what": (
            "worst-case coal-only offer level for PJM coal's min-load rows under a "
            "one-sided gas-steam admixture of capacity weight w, and the share of "
            "pjm-h8's own correction it could account for"
        ),
        "precommit": "docs/PRECOMMIT-pjm-h9-coal-only-comparator-2026-09-16.md",
        "w_hat": W_HAT,
        "PROVISIONAL": provisional,
        "provisional_note": (
            "G-REPRO FAILED on the quantile artifact: these numbers are NOT certified "
            "against the frozen surface. Run with --blend-reference frozen as well and "
            "compare the verdicts."
        )
        if provisional
        else None,
        "blend_reference": args.blend_reference,
        "decision_rule": "phi(w_hat) < 0.25 -> B-NO; > 0.75 -> B-YES; else B-PARTIAL",
        "g_repro_cells": qdoc["g_repro"]["cells_checked"],
        "years": {},
    }

    from market_sim.data.fleet.offer_surfaces import (
        _PJM_MIDCURVE_SEGMENT_OF,
        _pjm_midcurve_context,
        _pjm_midcurve_row_target,
    )

    for y in args.years:
        res = build(y)
        cfg, fleet = res["config"], res["fleet"]
        mc = np.asarray(res["mc_base"], dtype=float)
        if mc.ndim == 1:
            mc = mc[:, None]
        net_load = (
            res["demand"].sum(axis=0)
            - (res["solar_cap"][:, None] * res["solar_cf"]).sum(axis=0)
            - (res["wind_cap"][:, None] * res["wind_cf"]).sum(axis=0)
        )
        ctx = _pjm_midcurve_context(
            res["fleet_arrays"],
            fleet,
            mc,
            np.asarray(net_load, dtype=float),
            cfg,
            y,
            set(_PJM_MIDCURVE_SEGMENT_OF.values()),
        )
        gas = np.asarray(ctx.gas_day, dtype=float)
        share_of = {g: s for g, s, _sfx, _seg in ctx.rows}
        seg_of = {g: seg for g, _s, _sfx, seg in ctx.rows}

        df = pd.DataFrame(
            {
                "row": np.arange(len(fleet)),
                "group": [g.efficiency_bin for g in fleet],
                "cap": [float(g.pmax_mw) for g in fleet],
                "band": [_band(g.unit_id) for g in fleet],
            }
        )
        df["segment"] = [seg_of.get(g) for g in df["row"]]
        df["model_hr"] = [
            float(np.median(mc[g, :] / gas)) if seg_of.get(g) else np.nan
            for g in df["row"]
        ]
        coal = df[df["group"].isin(COAL_CLASSES) & (df["segment"] == "LONG_RUN")].copy()

        def capwtd(sub: pd.DataFrame, vals: np.ndarray) -> float:
            ok = np.isfinite(vals)
            cap = sub["cap"].to_numpy()[ok]
            return float((vals[ok] * cap).sum() / cap.sum()) if cap.sum() else np.nan

        def meas_at(sub: pd.DataFrame, table: np.ndarray) -> float:
            """Cap-weighted measured level for *sub* with LONG_RUN = *table*."""
            c = ctx._replace(tables={**ctx.tables, "LONG_RUN": table})
            vals = np.array(
                [
                    float(
                        np.nanmedian(
                            _pjm_midcurve_row_target(c, "LONG_RUN", share_of[g]) / gas
                        )
                    )
                    for g in sub["row"]
                ]
            )
            return capwtd(sub, vals)

        yr: dict = {"bundle": BUNDLE_FOR_YEAR[y], "gas_mean": float(gas.mean())}
        for band in ROWS:
            sub = coal[coal["band"] == band]
            if sub.empty:
                continue
            model = capwtd(sub, sub["model_hr"].to_numpy())
            blend = meas_at(
                sub,
                frozen_ladder(frozen_surface, "LONG_RUN", y)
                if args.blend_reference == "frozen"
                else ladder_at(qdoc, "LONG_RUN", y, 0.5),
            )
            gap = blend - model
            curve = []
            for w in W_GRID:
                lo = meas_at(sub, ladder_at(qdoc, "LONG_RUN", y, 0.5 * (1.0 - w)))
                hi = meas_at(sub, ladder_at(qdoc, "LONG_RUN", y, 0.5 * (1.0 + w)))
                curve.append(
                    {
                        "w": w,
                        "coal_only_lo": round(lo, 4),
                        "coal_only_hi": round(hi, 4),
                        "phi": round((blend - lo) / gap, 4) if gap else None,
                    }
                )
            # w-half / w-star by BISECTION on the stored p grid. phi is monotone
            # in w (a lower quantile is never above a higher one), so bisection
            # finds the crossing exactly on the grid in ~8 evaluations instead of
            # ~100 — no interpolation, no approximation of the crossing itself.
            cand = pg[pg <= 0.5][::-1]  # descending p == ascending w

            def phi_at(j: int) -> float:
                lo_j = meas_at(sub, ladder_at(qdoc, "LONG_RUN", y, float(cand[j])))
                return (blend - lo_j) / gap if gap else 0.0

            def first_at_least(target: float):
                """Smallest w on the grid whose phi >= target, or None."""
                if phi_at(len(cand) - 1) < target:
                    return None
                lo_i, hi_i = 0, len(cand) - 1
                while lo_i < hi_i:
                    mid = (lo_i + hi_i) // 2
                    if phi_at(mid) >= target:
                        hi_i = mid
                    else:
                        lo_i = mid + 1
                return round(1.0 - 2.0 * float(cand[lo_i]), 4)

            wh = first_at_least(0.5)
            ws = first_at_least(1.0)
            yr[band] = {
                "mw": round(float(sub["cap"].sum()), 1),
                "n_rows": int(len(sub)),
                "model_bid_hr": round(model, 4),
                "measured_blend_hr": round(blend, 4),
                "gap_hr": round(gap, 4),
                "gap_usd_mwh": round(gap * float(gas.mean()), 3),
                "phi_at_w_hat": next(
                    c["phi"] for c in curve if abs(c["w"] - W_HAT) < 1e-9
                ),
                "w_half": wh,
                "w_star": ws,
                "curve": curve,
            }
            r = yr[band]
            print(
                f"\n[{y}] COAL {band}: {r['mw']:.0f} MW  model {r['model_bid_hr']:.3f}  "
                f"blend {r['measured_blend_hr']:.3f}  gap {r['gap_hr']:.3f} HR "
                f"(={r['gap_usd_mwh']:.2f} $/MWh)"
            )
            print(
                f"   phi(w_hat={W_HAT}) = {r['phi_at_w_hat']}   "
                f"w_half = {r['w_half']}   w_star = {r['w_star']}"
            )
            print(f"   {'w':>7}{'lo':>9}{'hi':>9}{'phi':>8}")
            for c in curve:
                print(
                    f"   {c['w']:>7.4f}{c['coal_only_lo']:>9.3f}"
                    f"{c['coal_only_hi']:>9.3f}{(c['phi'] if c['phi'] is not None else float('nan')):>8.3f}"
                )
        out["years"][str(y)] = yr

    prim = out["years"][str(args.years[0])].get("committed", {})
    phi = prim.get("phi_at_w_hat")
    verdict = (
        "B-NO (comparator exonerated; route (a) is the object)"
        if phi is not None and phi < 0.25
        else "B-YES (comparator is the explanation)"
        if phi is not None and phi > 0.75
        else "B-PARTIAL"
    )
    out["verdict"] = {
        "year": args.years[0],
        "row": "committed",
        "phi": phi,
        "verdict": verdict,
    }
    print(
        f"\nPRE-REGISTERED VERDICT ({args.years[0]} COAL committed): phi={phi} -> {verdict}"
    )

    dest = _out_path(args.blend_reference)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
