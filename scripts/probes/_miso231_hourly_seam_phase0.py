"""miso-231 phase 0 (rule 29 clause 0) — the HOURLY neighbour-anchored PJM seam
ladder: does re-anchoring the ladder HOUR BY HOUR move the seam's price
RESPONSIVENESS, which the promoted annual form measurably did not?

**Zero LP.** Everything below is computed from committed measured series and the
keeper's own committed sidecars.

THE DEFECT THIS ATTACKS
-----------------------
miso-226 measured the promoted neighbour-anchored ladder and stated its own
non-claim: it repairs the ladder's LEVEL and not its RESPONSIVENESS.

    corr(imports, own price)   keeper +0.750 -> arm +0.725   vs MEASURED -0.101
    price-decile slope d1-d10  keeper -3,573 -> arm -3,217 MW vs MEASURED +1,322

i.e. 3 % of the distance on the correlation, 10 % of the sign error on the
slope.  The structural reason miso-226 gave: the ladder is a FIXED price ladder
the LP clears against ITS OWN internal price, so re-anchoring changes the band
LEVELS but not the RESPONSIVENESS — the bands still leave merit exactly when
MISO's price falls, which is when MISO actually imports most.

THE CONSTRUCTION (zero fitted parameters)
-----------------------------------------
Band ``k``'s offer becomes HOURLY:

    pi_k(t) = pjm_border(t) + delta_k

so band ``k`` clears in hour ``t`` iff

    MISO_price(t) > pjm_border(t) + delta_k   <=>   spread(t) > delta_k

The offsets ``delta_k`` are derived by the SAME Q-Q duration coupling the
incumbent and the promoted annual ladder both use — same
``_derive_one``/``qq_import`` estimator, same midpoint-depth grid on the same
``SEAM_FLOW_TRANCHES``, same measured seam flows, same no-wash reconciliation.
The ONLY change is which measured series the coupling reads:

    incumbent          MISO hub DA                (MISO_SEAM_LADDER_BY_YEAR)
    promoted annual    PJM western-border DA      (..._NEIGHBOUR_BY_YEAR)
    THIS               DA - border SPREAD         (the offsets delta_k)

This is the owner's 2026-09-06 ruling taken at its word — an import offered at
the exporting market's own price, in the hour it is offered, rather than at a
frozen annual quantile of it.

WHY THIS IS NOT THE REFUTED HURDLE
----------------------------------
``derive_miso_seam_ladders``'s own docstring records why the seam was moved OFF
a spread basis in the first place: a hurdle-gated arbitrage seam structurally
deletes the flow in a zero-spread year, because the measured flow "is
uncorrelated with the RT LMP spread (r = +0.06)".  Two differences, both
measured here rather than asserted:

1. That statistic is the **RT** spread.  The DA spread against the **PJM
   western border** — the series the neighbour ruling actually points at —
   correlates with flow at **+0.240 / +0.265 / +0.194** (2023/24/25), against
   corr(flow, MISO DA) of **-0.136 / -0.039 / -0.059**.  The spread carries the
   sign the seam needs; MISO's own price carries the sign the model has wrong.
2. A hurdle is ONE threshold; this is the same 8-band ladder.  The Q-Q coupling
   puts the shallow bands at NEGATIVE offsets (band 1 at -$29.17 in 2023), i.e.
   they clear even when MISO is far below PJM — which is exactly the
   "46-56 % of measured import MWh moves at spreads inside/below the $2 hurdle"
   the docstring says a hurdle deletes.  Nothing is gated away.

WHAT THIS PROBE MEASURES
------------------------
Two independent readouts, both against the frozen miso-226 comparators:

* **A. Offline (the derivation's own ``offline_score`` analogue).**  Drive all
  three ladders with the MEASURED MISO DA and MEASURED border, and score the
  simulated flow's price-decile slope and correlation against the MEASURED seam
  flow.  This asks whether the CONSTRUCTION reproduces the measured seam's
  price response.  It contains no model output at all.
* **B. Static re-merit at the keeper's OWN committed prices**, in the exact
  composition miso-226 used (per-band width = ``interface_limit/8``, the
  keeper's uniform envelope derate, a band clears when its price is strictly
  below the bus price).  This predicts what the LP would do.

Neither is a residual.  Both are statements about what the mechanism does.

Usage: python3 scripts/probes/_miso231_hourly_seam_phase0.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/miso230_ctdrag_seam_K"
OUT = REPO / "results/calibration/_miso231_hourly_seam_phase0.json"
YEARS = (2023, 2024, 2025)
SCREEN_HINT_YEAR = 2023  # miso-226's frozen comparator year
ZONE = "MISO-Indiana"  # the C1/G-2 reference hub
BUS = "MISO_external"  # the bus the reference-price seam bands sit in
HOURS = 8760

# miso-226's frozen measurements, quoted so the deltas below are anchored to a
# published comparator rather than recomputed here.
MISO226 = {
    "corr_measured": -0.101,
    "corr_keeper": 0.750,
    "corr_arm_annual": 0.725,
    "slope_measured_mw": 1322.0,
    "slope_keeper_mw": -3573.0,
    "slope_arm_annual_mw": -3217.0,
}


def _derive_module():
    spec = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def spread_ladder(dm, g: pd.DataFrame, spec) -> dict[str, list[float]]:
    """The delta_k offsets: ``_derive_one`` on the DA-minus-border spread.

    Byte-for-byte the incumbent estimator, third series. The no-wash
    reconciliation carries through unchanged: both directions share the same
    ``pjm_border(t)``, so an ordering constraint on the offsets is the same
    constraint on the applied hourly prices.
    """
    gg = g.dropna(subset=["pjm_border", "da", spec.name])
    spread = (gg["da"] - gg["pjm_border"]).to_numpy(dtype=float)
    notes: list[str] = []
    return dm._derive_one(spread, gg[spec.name].to_numpy(dtype=float), spec, notes)


def decile_slope(price: np.ndarray, series: np.ndarray) -> tuple[float, list[float]]:
    """(d1 - d10) MW and the ten decile means, binned on ``price``."""
    order = np.argsort(price, kind="stable")
    parts = np.array_split(order, 10)
    means = [float(series[p].mean()) for p in parts]
    return means[0] - means[-1], means


def main() -> int:
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR,
    )
    from market_sim.data.eia_loader import measured_seam_import_envelope
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    dm = _derive_module()
    g_all = dm.load_joined()
    spec = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["PJM"]
    limit = float(spec.interface_limit_mw)
    width = limit / SEAM_FLOW_TRANCHES

    report: dict[str, object] = {
        "probe": "miso-231 phase 0 — HOURLY neighbour-anchored PJM seam ladder",
        "keeper": "2026-09-06-miso-230-ctdrag-seam",
        "construction": "pi_k(t) = pjm_border(t) + delta_k; delta_k = Q-Q "
        "duration coupling of the DA-minus-border SPREAD against measured seam "
        "flow, on the same midpoint-depth grid (zero fitted parameters)",
        "miso226_frozen_comparators": MISO226,
        "interface_limit_mw": limit,
        "seam_flow_tranches": SEAM_FLOW_TRANCHES,
        "years": {},
    }
    years_out: dict[str, object] = {}

    for year in YEARS:
        g = g_all.loc[year].dropna(subset=["pjm_border", "da", spec.name])
        da = g["da"].to_numpy(dtype=float)
        border = g["pjm_border"].to_numpy(dtype=float)
        flow = g[spec.name].to_numpy(dtype=float)
        spread = da - border

        lad_hourly = spread_ladder(dm, g_all.loc[year], spec)
        d_imp = np.asarray(lad_hourly["import"], dtype=float)
        inc = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["PJM"]["import"], float)
        ann = np.asarray(
            MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[year]["PJM"]["import"], float
        )

        # --- A. OFFLINE: drive every ladder with the MEASURED record --------
        # Simulated import MW = width x (number of bands in merit). No envelope
        # derate here — this readout is about the ladder's price response, and
        # the derate is common to all three arms.
        sim_inc = width * (da[None, :] > inc[:, None]).sum(0)
        sim_ann = width * (da[None, :] > ann[:, None]).sum(0)
        sim_hr = width * (spread[None, :] > d_imp[:, None]).sum(0)

        offline: dict[str, object] = {
            "n_hours": int(da.size),
            "corr_flow_vs_spread": round(float(np.corrcoef(flow, spread)[0, 1]), 3),
            "corr_flow_vs_miso_da": round(float(np.corrcoef(flow, da)[0, 1]), 3),
            "corr_da_vs_border": round(float(np.corrcoef(da, border)[0, 1]), 3),
            "delta_k": [round(float(x), 2) for x in d_imp],
            "ladder_incumbent": [round(float(x), 2) for x in inc],
            "ladder_annual_neighbour": [round(float(x), 2) for x in ann],
        }
        for tag, sim in (
            ("measured_flow", flow),
            ("incumbent", sim_inc),
            ("annual_neighbour", sim_ann),
            ("hourly", sim_hr),
        ):
            slope, means = decile_slope(da, sim)
            offline[tag] = {
                "mean_mw": round(float(sim.mean()), 1),
                "corr_vs_miso_da": round(float(np.corrcoef(sim, da)[0, 1]), 3),
                "decile_slope_d1_minus_d10_mw": round(float(slope), 1),
                "decile_means_mw": [round(x, 1) for x in means],
            }
            if tag != "measured_flow":
                offline[tag]["corr_vs_measured_flow"] = round(
                    float(np.corrcoef(sim, flow)[0, 1]), 3
                )
        # FOOTPRINT, MODEL-FREE BASIS (rule 29's "the mechanism's own measured
        # footprint"). Computed on the MEASURED record only, so it is a
        # property of the construction against the data rather than of the
        # incumbent solve. This is the PRIMARY basis for naming the screen
        # year; the keeper-price basis in readout B is reported beside it.
        in_ann_m = da[None, :] > ann[:, None]
        in_hr_m = spread[None, :] > d_imp[:, None]
        dis_m = in_ann_m ^ in_hr_m
        offline["footprint_measured_basis"] = {
            "band_hours_disagree": int(dis_m.sum()),
            "band_hours_disagree_pct": round(100.0 * float(dis_m.mean()), 2),
            "hours_with_any_disagreement_pct": round(
                100.0 * float((dis_m.sum(0) > 0).mean()), 2
            ),
            "abs_mw_moved_mean": round(
                float(np.abs(sim_hr - sim_ann).mean()), 1
            ),
            "abs_twh_moved": round(
                float(np.abs(sim_hr - sim_ann).sum() / 1e6), 4
            ),
        }
        years_out.setdefault(str(year), {})["offline"] = offline

        # --- B. STATIC RE-MERIT at the keeper's own committed prices --------
        # Rebuild the border series on the FULL 8760 grid (readout A's frame is
        # dropna'd) so it aligns with the keeper's own hourly sidecars.
        border_full = (
            g_all.loc[year]["pjm_border"]
            .reindex(range(HOURS))
            .interpolate(limit=3)
            .ffill()
            .bfill()
            .to_numpy(dtype=float)
        )
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        p_bus = (
            sysf[sysf["zone"] == BUS].sort_values("hour")["price"].to_numpy(float)
        )
        p_hub = (
            sysf[sysf["zone"] == ZONE].sort_values("hour")["price"].to_numpy(float)
        )
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
        keeper_imp = (
            cls.groupby("hour")["mw"]
            .sum()
            .reindex(range(HOURS))
            .fillna(0.0)
            .to_numpy(float)
        )
        env = measured_seam_import_envelope("MISO", year, HOURS, None, direction="import")
        cap = np.asarray(env["PJM"], float)
        # The keeper runs miso_seam_envelope_merit_cap = True, i.e. the
        # MERIT-ORDER (waterfall) envelope composition: band k's bound is
        # clip(cap - (k-1)*width, 0, width), so cheap base rungs keep full
        # width and the envelope's residual falls on the expensive rungs.
        # (miso-226's probe used the UNIFORM derate, which was that keeper's
        # setting; miso-230's keeper flipped it, so the composition is taken
        # from the keeper's own run_config rather than carried across.)
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        band_mw = np.clip(cap[None, :] - ks * width, 0.0, width)  # (8, 8760)

        # The keeper already runs the ANNUAL neighbour ladder, so that arm is
        # the harness check: its static series should track the keeper's own
        # committed import series.
        in_ann = p_bus[None, :] > ann[:, None]
        in_hr = (p_bus - border_full)[None, :] > d_imp[:, None]
        mw_ann = (in_ann * band_mw).sum(0)
        mw_hr = (in_hr * band_mw).sum(0)

        static: dict[str, object] = {
            "keeper_bus_price_mean": round(float(p_bus.mean()), 2),
            "keeper_import_mw_mean": round(float(keeper_imp.mean()), 1),
            "harness_check": {
                "note": "the keeper ARMS the annual neighbour ladder AND "
                "miso_seam_envelope_merit_cap, so this static reconstruction "
                "(same ladder, same waterfall composition) should track its "
                "committed imports",
                "envelope_composition": "merit_cap (waterfall), per the "
                "keeper's own run_config",
                "static_annual_mw_mean": round(float(mw_ann.mean()), 1),
                "corr_static_annual_vs_keeper_imports": round(
                    float(np.corrcoef(mw_ann, keeper_imp)[0, 1]), 3
                ),
            },
        }
        for tag, sim in (("annual_neighbour", mw_ann), ("hourly", mw_hr)):
            slope, means = decile_slope(p_hub, sim)
            slope_a, _ = decile_slope(p_bus, sim)
            static[tag] = {
                "mean_mw": round(float(sim.mean()), 1),
                "corr_vs_keeper_hub_price": round(
                    float(np.corrcoef(sim, p_hub)[0, 1]), 3
                ),
                "corr_vs_keeper_bus_price": round(
                    float(np.corrcoef(sim, p_bus)[0, 1]), 3
                ),
                "decile_slope_on_hub_price_mw": round(float(slope), 1),
                "decile_slope_on_bus_price_mw": round(float(slope_a), 1),
                "decile_means_mw": [round(x, 1) for x in means],
            }
        static["static_delta_hourly_minus_annual_mw"] = round(
            float((mw_hr - mw_ann).mean()), 1
        )
        # The FROZEN miso-225/226 G-2 hour set: the hours the REAL Indiana hub
        # cleared below $20. Quoted so this arm is measured on the same bar its
        # predecessor cleared, not a new one.
        sys.path.insert(0, str(REPO / "scripts" / "probes"))
        from _miso224_floor_anatomy_phase0 import actual_zone_price

        act = actual_zone_price(year)[ZONE].to_numpy(float)
        cheap = np.isfinite(act) & (act < 20.0)
        static["frozen_g2_cheap_hours"] = {
            "n_hours": int(cheap.sum()),
            "keeper_committed_import_mw": round(float(keeper_imp[cheap].mean()), 1),
            "static_annual_mw": round(float(mw_ann[cheap].mean()), 1),
            "static_hourly_mw": round(float(mw_hr[cheap].mean()), 1),
            "static_hourly_minus_annual_mw": round(
                float((mw_hr - mw_ann)[cheap].mean()), 1
            ),
        }
        # FOOTPRINT (rule 29: the screen year is named on the mechanism's own
        # footprint, never on a residual). The mechanism's footprint is the
        # band-hours on which the hourly ladder and the promoted annual ladder
        # DISAGREE about merit — where the construction can do anything at all.
        disagree = in_hr ^ in_ann
        static["footprint"] = {
            "band_hours_disagree": int(disagree.sum()),
            "band_hours_disagree_pct": round(
                100.0 * float(disagree.mean()), 2
            ),
            "hours_with_any_disagreement_pct": round(
                100.0 * float((disagree.sum(0) > 0).mean()), 2
            ),
            "abs_mw_moved_mean": round(float(np.abs(mw_hr - mw_ann).mean()), 1),
            "abs_twh_moved": round(float(np.abs(mw_hr - mw_ann).sum() / 1e6), 4),
        }
        years_out[str(year)]["static_remerit"] = static

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")

    for year in YEARS:
        o = years_out[str(year)]["offline"]
        s = years_out[str(year)]["static_remerit"]
        print(f"================ {year} ================")
        print(
            f"  measured: corr(flow, spread) {o['corr_flow_vs_spread']:+.3f}"
            f"   corr(flow, MISO DA) {o['corr_flow_vs_miso_da']:+.3f}"
            f"   corr(DA, border) {o['corr_da_vs_border']:.3f}"
        )
        print(f"  delta_k  {o['delta_k']}")
        print("  --- A. OFFLINE, driven by the MEASURED record ---")
        print(
            f"    {'arm':<20} {'mean MW':>9} {'corr vs DA':>11}"
            f" {'slope d1-d10':>13} {'corr vs flow':>13}"
        )
        for tag in ("measured_flow", "incumbent", "annual_neighbour", "hourly"):
            r = o[tag]
            cf = r.get("corr_vs_measured_flow")
            print(
                f"    {tag:<20} {r['mean_mw']:9.0f} {r['corr_vs_miso_da']:+11.3f}"
                f" {r['decile_slope_d1_minus_d10_mw']:+13.0f}"
                f" {('%+.3f' % cf) if cf is not None else '       —':>13}"
            )
        fm = o["footprint_measured_basis"]
        print(
            f"    FOOTPRINT (measured basis): {fm['band_hours_disagree']:,}"
            f" band-hours ({fm['band_hours_disagree_pct']:.2f} %),"
            f" |dMW| mean {fm['abs_mw_moved_mean']:.0f}"
            f" = {fm['abs_twh_moved']:.4f} TWh moved"
        )
        print("  --- B. STATIC RE-MERIT at the keeper's own prices ---")
        h = s["harness_check"]
        print(
            f"    harness: static(annual) {h['static_annual_mw_mean']:.0f} MW vs"
            f" keeper committed {s['keeper_import_mw_mean']:.0f} MW,"
            f" corr {h['corr_static_annual_vs_keeper_imports']:+.3f}"
        )
        for tag in ("annual_neighbour", "hourly"):
            r = s[tag]
            print(
                f"    {tag:<20} {r['mean_mw']:9.0f} MW"
                f"   corr vs hub price {r['corr_vs_keeper_hub_price']:+.3f}"
                f"   slope {r['decile_slope_on_hub_price_mw']:+.0f} MW"
            )
        print(
            f"    static delta hourly - annual:"
            f" {s['static_delta_hourly_minus_annual_mw']:+.1f} MW"
        )
        c = s["frozen_g2_cheap_hours"]
        print(
            f"    FROZEN G-2 cheap hours (n={c['n_hours']}):"
            f" keeper committed {c['keeper_committed_import_mw']:.0f}"
            f" | static annual {c['static_annual_mw']:.0f}"
            f" -> hourly {c['static_hourly_mw']:.0f}"
            f" ({c['static_hourly_minus_annual_mw']:+.0f} MW)"
        )
        fp = s["footprint"]
        print(
            f"    FOOTPRINT: {fp['band_hours_disagree']:,} band-hours disagree"
            f" ({fp['band_hours_disagree_pct']:.2f} %),"
            f" {fp['hours_with_any_disagreement_pct']:.1f} % of hours,"
            f" |dMW| mean {fp['abs_mw_moved_mean']:.0f}"
            f" = {fp['abs_twh_moved']:.4f} TWh moved\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
