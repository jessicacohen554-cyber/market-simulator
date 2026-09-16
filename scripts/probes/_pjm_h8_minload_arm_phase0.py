"""pjm-h8 phase 0 — the MIN-LOAD measured-offer arm, gates G-1/G-2/G-3. ZERO LP.

Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP.

THE ARM. ``pjm_offer_midcurve_minload_segments = ("LONG_RUN",)`` — PJM's already-armed
measured-offer surface is extended to the min-load rungs (``mustrun`` / ``committed``) of
the LONG_RUN segment, in **LEVEL form**: the measured offer REPLACES the
take-or-pay/passthrough construction on those rows instead of stacking a floor on it, so
exactly one mechanism sets each row's bid (rule 19 ``[R-ONE-MECH]``).

Chartered by the OWNER RULING 2026-09-16 re-opening the pjm-142 frontier on the strength of
``docs/FINDING-pjm-h8-coal-minload-is-the-undisciplined-offer-surface-2026-09-16.md``, which
measured that PJM coal's min-load block is the only part of its own offer stack that no
measured artifact governs.

NON-SELECTIVE WITHIN THE SEGMENT (pjm-h5's objection, honoured). The scope is the SEGMENT,
never a class: both COAL and ST_GAS min-load rungs move, and ST_GAS's moves DOWN (it sits
at 1.217-1.556 of measured). A coal-only form would be the rule-1 selection pjm-h5 refused
and the ``offer_curve_by_group`` cell's DO-NOT-REDO note forbids.

``sync`` IS NOT IN SCOPE and that is structural, not convenient: PJM coal's sync rung sits
at within-plant share 0.871 — ABOVE the econ band — and reads 1.31-1.40x measured, so it is
a top-of-curve rung. Repricing it would move coal the OTHER way (cheaper), i.e. leaving it
out is the choice that does NOT flatter the residual.

Because the markup is a **P1** ``mc_bid_adjust``, a ``fleet_only`` build alone cannot show
it: the fleet is built ONCE per year and the real builder is then called TWICE (control
scope, arm scope) and the two markups differenced — the ``pjm121_level_form_precheck``
pattern.

Run: ``python3 scripts/probes/_pjm_h8_minload_arm_phase0.py 2023 2024 2025``
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

BUNDLE_FOR_YEAR = {2023: "pjm_d4_4_A", 2024: "pjm_d4_4_A", 2025: "pjm_d4_4_A"}
ARM_SCOPE = ("LONG_RUN",)
MINLOAD = ("mustrun", "committed")
COAL_CLASSES = ("COAL", "COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE")


def build(year: int) -> dict:
    """Build the keeper's fleet for *year* on its own recipe. ZERO LP."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / BUNDLE_FOR_YEAR[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    kw["pjm_da_virtual_bids"] = False
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def main() -> None:
    from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup

    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    out: dict = {
        "arm": {"pjm_offer_midcurve_minload_segments": list(ARM_SCOPE)},
        "years": {},
    }

    for y in years:
        t0 = time.time()
        res = build(y)
        cfg, fleet, fa = res["config"], res["fleet"], res["fleet_arrays"]
        mc = np.asarray(res["mc_base"], dtype=float)
        net_load = (
            res["demand"].sum(axis=0)
            - (res["solar_cap"][:, None] * res["solar_cf"]).sum(axis=0)
            - (res["wind_cap"][:, None] * res["wind_cf"]).sum(axis=0)
        )
        cfg_arm = cfg.with_overrides(
            pjm_offer_midcurve_minload_segments=list(ARM_SCOPE)
        )

        m_ctl = build_pjm_offer_midcurve_conditional_markup(
            fa, fleet, mc, net_load, cfg, y
        )
        m_arm = build_pjm_offer_midcurve_conditional_markup(
            fa, fleet, mc, net_load, cfg_arm, y
        )
        m_ctl = np.zeros_like(mc) if m_ctl is None else m_ctl
        m_arm = np.zeros_like(mc) if m_arm is None else m_arm
        delta = m_arm - m_ctl

        cls = np.array(
            [getattr(g, "plant_group", None) or g.efficiency_bin for g in fleet]
        )
        sfx = np.array([g.unit_id.rpartition("_")[2] for g in fleet])
        cap = np.asarray(fa.pmax, dtype=float)
        moved = np.any(delta != 0.0, axis=1)

        # ---- G-1 CONFINEMENT: exactly the LONG_RUN min-load rows, nothing else.
        expect = np.isin(cls, list(COAL_CLASSES) + ["ST_GAS"]) & np.isin(sfx, MINLOAD)
        g1 = {
            "moved_rows": int(moved.sum()),
            "expected_rows": int(expect.sum()),
            "moved_not_expected": sorted(
                {f"{c}:{s}" for c, s in zip(cls[moved & ~expect], sfx[moved & ~expect])}
            ),
            "expected_not_moved": sorted(
                {f"{c}:{s}" for c, s in zip(cls[expect & ~moved], sfx[expect & ~moved])}
            ),
            "bands_moved": sorted(set(sfx[moved])),
            "classes_moved": sorted(set(cls[moved])),
        }
        g1["PASS"] = not g1["moved_not_expected"] and not g1["expected_not_moved"]

        # ---- G-2 IDENTITY: on every moved row the P1 bid IS the measured target.
        from market_sim.data.fleet.offer_surfaces import (
            _PJM_MIDCURVE_SEGMENT_OF,
            _pjm_midcurve_context,
            _pjm_midcurve_row_target,
        )

        ctx = _pjm_midcurve_context(
            fa, fleet, mc, net_load, cfg_arm, y, set(_PJM_MIDCURVE_SEGMENT_OF.values())
        )
        share_of = {g: s for g, s, _x, _seg in ctx.rows}
        seg_of = {g: seg for g, _s, _x, seg in ctx.rows}
        devs = []
        for g in np.where(moved)[0]:
            tgt = _pjm_midcurve_row_target(ctx, seg_of[int(g)], share_of[int(g)])
            bid = mc[g, :] + m_arm[g, :]
            ok = np.isfinite(tgt)
            devs.append(float(np.max(np.abs(bid[ok] - np.maximum(tgt[ok], 0.0)))))
        g2 = {
            "max_abs_dev_bid_vs_measured_target": max(devs) if devs else None,
            "n_rows_checked": len(devs),
        }
        g2["PASS"] = bool(devs) and max(devs) < 1e-9

        # ---- G-3 MAGNITUDE + the FLOORED-SHARE prediction.
        mg = np.asarray(fa.min_gen, dtype=float)
        avail = np.asarray(fa.availability, dtype=float)
        rows = []
        for c in ("COAL", "ST_GAS"):
            for b in MINLOAD:
                m = (cls == c) & (sfx == b) & moved
                if not m.any():
                    continue
                d = delta[m].mean(axis=1)
                w = cap[m]
                floored = mg[m].sum()
                potential = (cap[m][:, None] * avail[m]).sum()
                rows.append(
                    {
                        "class": c,
                        "band": b,
                        "mw": float(w.sum()),
                        "capwtd_delta_usd_mwh": float((d * w).sum() / w.sum()),
                        "floored_share_of_potential": float(floored / potential),
                        "footprint_usd_mw": float((d * w).sum()),
                    }
                )
        g3 = {
            "rows": rows,
            "coal_minload_footprint_usd_mw": float(
                sum(r["footprint_usd_mw"] for r in rows if r["class"] == "COAL")
            ),
            "h6_arm_footprint_usd_mw": 17.6561 * 12550.0,
        }

        yr = {"G1": g1, "G2": g2, "G3": g3, "elapsed_s": round(time.time() - t0, 1)}
        out["years"][str(y)] = yr

        print(f"\n[{y}] built {yr['elapsed_s']}s")
        print(
            f"  G-1 confinement {'PASS' if g1['PASS'] else 'FAIL'}: "
            f"{g1['moved_rows']} rows moved, classes={g1['classes_moved']}, "
            f"bands={g1['bands_moved']}, stray={g1['moved_not_expected']}, "
            f"missing={g1['expected_not_moved']}"
        )
        print(
            f"  G-2 identity    {'PASS' if g2['PASS'] else 'FAIL'}: "
            f"max |P1 bid - measured target| = {g2['max_abs_dev_bid_vs_measured_target']:.3e} "
            f"over {g2['n_rows_checked']} rows"
        )
        print(
            f"  G-3 magnitude:  {'class':<8}{'band':<11}{'MW':>8}{'d$/MWh':>9}{'floored':>9}"
        )
        for r in rows:
            print(
                f"                  {r['class']:<8}{r['band']:<11}{r['mw']:>8.0f}"
                f"{r['capwtd_delta_usd_mwh']:>9.2f}{r['floored_share_of_potential']:>9.1%}"
            )
        print(
            f"      COAL min-load footprint {g3['coal_minload_footprint_usd_mw']:,.0f} $-MW "
            f"vs h6 arm {g3['h6_arm_footprint_usd_mw']:,.0f}"
        )

    dest = REPO / "results/calibration/_pjm_h8_minload_arm_phase0.json"
    if dest.exists():
        try:
            prior = json.loads(dest.read_text())
        except json.JSONDecodeError:
            prior = {}
        merged = dict(prior.get("years") or {})
        merged.update(out["years"])
        out["years"] = merged
    dest.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {dest.relative_to(REPO)} (years {sorted(out['years'])})")


if __name__ == "__main__":
    main()
