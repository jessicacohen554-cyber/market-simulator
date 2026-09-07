"""miso-233 phase 0, part C (rule 29 clause 0) — is the SPP seam's price
response carried by the MISO-minus-SPP SPREAD, the way the PJM seam's was?
**Zero LP.**

WHY THIS SEAM, AND WHY NOW
--------------------------
Parts A and B of this phase 0 measured, from the miso-232 keeper's own committed
sidecars, that the residual decile-slope magnitude is NOT a PJM depth problem:

  * the PJM seam's reconstructed slope is ALREADY STEEPER than the measured PJM
    seam in every year (+2,377 / +2,611 / +2,704 MW vs measured +1,319 / +1,052
    / +815), and its cheapest decile loses only 194-271 MW to the measured
    deliverability envelope — so the queue's named hypothesis (deep bands k=6-8
    under-clearing in cheap hours) is falsified by the keeper's own artifacts;
  * the SPP and South seams, which still ride the INCUMBENT fixed MISO-hub Q-Q
    ladder, contribute slopes of -414 / -481 / -553 and -919 / -1,135 / -827 MW
    against measured seams of +317 / +466 / -50 and +72 / +60 / +646. They carry
    the exact defect miso-226 named and the hourly form repaired on PJM: a FIXED
    ladder cleared against the model's OWN price imports most when MISO is
    expensive.

Queue item 3 recorded the blocker: "SPP / South seams still ride the incumbent
annual anchor FOR WANT OF A MEASURED HOURLY PRICE SERIES." For SPP that blocker
is GONE — lane SPP-14 landed
``data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet``
(SPPNORTH_HUB / SPPSOUTH_HUB, DA + RT hourly, 2023-2025, 8,754/8,760 hours) on
2026-09-06 from SPP's own portal. This part asks whether that series passes the
SAME admissibility test the PJM border price passed in miso-231 §1.

WHICH HUB — DECLARED BEFORE THE NUMBERS (rule 14 [R-ACCURATE] misalignment)
--------------------------------------------------------------------------
The seam is ONE collapsed link on the ``MISO_external`` (Midwest) bus, while the
measured DIBAs behind it are SWPP + SPA and the real boundary is two paths:
MISO Midwest<->SPP North and MISO South<->SPP South. **SPPNORTH_HUB is the
anchor**, on the structural ground that the link our topology carries is hosted
on the Midwest external bus (the South seam has its own bus,
``split_miso_south_external_node``), so the MISO-facing SPP region is SPP North.
SPPSOUTH_HUB is computed and printed BESIDE it as a sensitivity — it is
**reported, never selected**: choosing the hub that scores better would be
exactly the fitted-mechanism selection rule 1 [R-STRUCT] forbids.

THE ADMISSIBILITY TEST (miso-231 §1's, applied unchanged)
---------------------------------------------------------
    corr(measured SPP seam flow, MISO DA)                  <- what the model has
    corr(measured SPP seam flow, MISO DA - SPP hub DA)     <- what the arm would have

If the spread carries a materially better-signed response than MISO's own price,
the construction has a measured basis; if it does not, the arm is dead here and
no LP is spent. Readout B additionally re-merits the seam at the KEEPER's own
committed prices, so the footprint is measured on the artifact a screen would
move.

Usage: python3 scripts/probes/_miso233_spp_hourly_phase0.py
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
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso232_hourlyseam_K"
SPP_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet"
OUT = REPO / "results/calibration/_miso233_spp_hourly_phase0.json"
YEARS = (2023, 2024, 2025)
ZONE = "MISO-Indiana"
BUS = "MISO_external"
ANCHOR_HUB = "SPPNORTH_HUB"      # declared above, before any number
SENSITIVITY_HUB = "SPPSOUTH_HUB"  # reported, never selected
HOURS = 8760


def decile_slope(price: np.ndarray, series: np.ndarray) -> float:
    order = np.argsort(price, kind="stable")
    parts = np.array_split(order, 10)
    means = [float(series[p].mean()) for p in parts]
    return means[0] - means[-1]


def spp_hub(year: int, hub: str) -> np.ndarray:
    d = pd.read_parquet(SPP_LMP)
    d = d[(d["year"] == year) & (d["zone"] == hub)].sort_values("hour")
    s = (
        d.set_index("hour")["da"]
        .reindex(range(HOURS))
        .interpolate(limit=3)
        .ffill()
        .bfill()
    )
    return s.to_numpy(float)


def main() -> int:
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import measured_seam_import_envelope
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    spec = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["SPP"]
    width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES

    report: dict[str, object] = {
        "probe": "miso-233 phase 0 part C — SPP hourly neighbour ladder, "
        "admissibility + footprint",
        "keeper": "2026-09-06-miso-232-hourly-seam",
        "zero_lp": True,
        "anchor_hub": ANCHOR_HUB,
        "sensitivity_hub": SENSITIVITY_HUB,
        "anchor_choice_basis": "structural — the SPP seam link is hosted on the "
        "MISO_external (Midwest) bus; SPPSOUTH is reported, never selected",
        "source": str(SPP_LMP.relative_to(REPO)),
        "band_width_mw": round(width, 1),
        "years": {},
    }
    years_out: dict[str, object] = {}

    for year in YEARS:
        gy = g_all.loc[year]
        da = gy["da"].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill().to_numpy(float)
        flow = gy["SPP"].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill().to_numpy(float)
        hubs = {h: spp_hub(year, h) for h in (ANCHOR_HUB, SENSITIVITY_HUB)}

        row: dict[str, object] = {
            "measured_spp_seam_mean_mw": round(float(flow.mean()), 1),
            "corr_flow_vs_miso_da": round(float(np.corrcoef(flow, da)[0, 1]), 3),
        }
        for h, p in hubs.items():
            sp = da - p
            row[f"corr_flow_vs_spread_{h}"] = round(float(np.corrcoef(flow, sp)[0, 1]), 3)
            row[f"corr_miso_da_vs_{h}"] = round(float(np.corrcoef(da, p)[0, 1]), 3)
            row[f"mean_{h}"] = round(float(p.mean()), 2)
            row[f"mean_spread_{h}"] = round(float(sp.mean()), 2)

        # --- the delta_k ladder on the anchor spread, frozen estimator -----
        gg = gy.dropna(subset=["da", "SPP"])
        idx = gg.index.to_numpy()
        anchor_on_idx = hubs[ANCHOR_HUB][idx]
        notes: list[str] = []
        lad_h = dm._derive_one(
            gg["da"].to_numpy(float) - anchor_on_idx,
            gg["SPP"].to_numpy(float),
            spec,
            notes,
        )
        # The REGISTRY entry is what a solve reads; the recomputation above is
        # the reproduction check (they agree to the derive's own rounding, and
        # tests/iso/miso/test_miso_seam_ladder.py pins it). Every static number
        # below is computed on the REGISTRY values so the footprint is the
        # footprint of the thing that will actually be solved.
        d_imp = np.asarray(
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"]["import"], float
        )
        row["delta_k_registry_import"] = [round(float(x), 2) for x in d_imp]
        row["delta_k_recompute_max_abs_diff"] = round(
            float(np.abs(d_imp - np.asarray(lad_h["import"], float)).max()), 3
        )
        inc = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["SPP"]["import"], float)
        row["delta_k_import"] = [round(float(x), 2) for x in d_imp]
        row["delta_k_export"] = [round(float(x), 2) for x in lad_h["export"]]
        row["incumbent_import"] = [round(float(x), 2) for x in inc]
        row["derive_notes"] = notes

        # --- A. OFFLINE, MEASURED RECORD ONLY (no model output at all) -----
        spread = da - hubs[ANCHOR_HUB]
        sim_inc = width * (da[None, :] > inc[:, None]).sum(0)
        sim_hr = width * (spread[None, :] > d_imp[:, None]).sum(0)
        offline = {}
        for tag, sim in (("measured_flow", flow), ("incumbent", sim_inc), ("hourly", sim_hr)):
            offline[tag] = {
                "mean_mw": round(float(sim.mean()), 1),
                "corr_vs_miso_da": round(float(np.corrcoef(sim, da)[0, 1]), 3),
                "decile_slope_on_miso_da_mw": round(decile_slope(da, sim), 1),
            }
            if tag != "measured_flow":
                offline[tag]["corr_vs_measured_flow"] = round(
                    float(np.corrcoef(sim, flow)[0, 1]), 3
                )
        row["offline"] = offline

        # --- B. STATIC RE-MERIT at the KEEPER's own committed prices -------
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        p_bus = sysf[sysf["zone"] == BUS].sort_values("hour")["price"].to_numpy(float)
        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        cap_i = np.asarray(env_i["SPP"], float)
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        band_i = np.clip(cap_i[None, :] - ks * width, 0.0, width)
        in_inc = p_bus[None, :] > inc[:, None]
        in_hr = (p_bus - hubs[ANCHOR_HUB])[None, :] > d_imp[:, None]
        mw_inc = (in_inc * band_i).sum(0)
        mw_hr = (in_hr * band_i).sum(0)

        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        row["static_remerit"] = {
            "incumbent_mean_mw": round(float(mw_inc.mean()), 1),
            "hourly_mean_mw": round(float(mw_hr.mean()), 1),
            "incumbent_slope_mw": round(decile_slope(act[ok], mw_inc[ok]), 1),
            "hourly_slope_mw": round(decile_slope(act[ok], mw_hr[ok]), 1),
            "measured_seam_slope_mw": round(decile_slope(act[ok], flow[ok]), 1),
            "slope_move_mw": round(
                decile_slope(act[ok], mw_hr[ok]) - decile_slope(act[ok], mw_inc[ok]), 1
            ),
        }
        disagree = in_hr ^ in_inc
        row["footprint"] = {
            "band_hours_disagree": int(disagree.sum()),
            "band_hours_disagree_pct": round(100.0 * float(disagree.mean()), 2),
            "hours_with_any_disagreement_pct": round(
                100.0 * float((disagree.sum(0) > 0).mean()), 2
            ),
            "abs_mw_moved_mean": round(float(np.abs(mw_hr - mw_inc).mean()), 1),
            "abs_twh_moved": round(float(np.abs(mw_hr - mw_inc).sum() / 1e6), 4),
        }
        years_out[str(year)] = row

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")

    print("ADMISSIBILITY (measured record only — no model output)")
    print(
        f"  {'yr':<5} {'corr(flow, MISO DA)':>20} {'corr(flow, spread N)':>21}"
        f" {'corr(flow, spread S)':>21} {'corr(MISO,N)':>13}"
    )
    for year in YEARS:
        r = years_out[str(year)]
        print(
            f"  {year:<5} {r['corr_flow_vs_miso_da']:>+20.3f}"
            f" {r[f'corr_flow_vs_spread_{ANCHOR_HUB}']:>+21.3f}"
            f" {r[f'corr_flow_vs_spread_{SENSITIVITY_HUB}']:>+21.3f}"
            f" {r[f'corr_miso_da_vs_{ANCHOR_HUB}']:>13.3f}"
        )
    for year in YEARS:
        r = years_out[str(year)]
        o, s, f = r["offline"], r["static_remerit"], r["footprint"]
        print(f"\n================== {year} ==================")
        print(f"  delta_k (import, on the {ANCHOR_HUB} spread): {r['delta_k_import']}")
        print(f"  incumbent import ladder                     : {r['incumbent_import']}")
        print("  A. OFFLINE, measured record only")
        print(
            f"    {'arm':<15} {'mean MW':>9} {'corr vs DA':>11} {'slope':>8} {'corr vs flow':>13}"
        )
        for tag in ("measured_flow", "incumbent", "hourly"):
            x = o[tag]
            cf = x.get("corr_vs_measured_flow")
            print(
                f"    {tag:<15} {x['mean_mw']:>9.0f} {x['corr_vs_miso_da']:>+11.3f}"
                f" {x['decile_slope_on_miso_da_mw']:>+8.0f}"
                f" {('%+.3f' % cf) if cf is not None else '       —':>13}"
            )
        print("  B. STATIC RE-MERIT at the keeper's own committed prices")
        print(
            f"    incumbent {s['incumbent_mean_mw']:.0f} MW slope {s['incumbent_slope_mw']:+.0f}"
            f"  ->  hourly {s['hourly_mean_mw']:.0f} MW slope {s['hourly_slope_mw']:+.0f}"
            f"   (move {s['slope_move_mw']:+.0f} MW; measured seam slope"
            f" {s['measured_seam_slope_mw']:+.0f})"
        )
        print(
            f"    FOOTPRINT: {f['band_hours_disagree']:,} band-hours"
            f" ({f['band_hours_disagree_pct']:.2f} %), any-disagreement hours"
            f" {f['hours_with_any_disagreement_pct']:.1f} %,"
            f" |dMW| mean {f['abs_mw_moved_mean']:.0f} = {f['abs_twh_moved']:.4f} TWh"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
