"""caiso-71 step-3 honesty check: can the SP26/NP26 AS minima be served for
free by IN-REGION un-postured supply? (handoff 2026-07-10, the caiso-70 lesson)

Cheap arithmetic BEFORE burning the solve. Intercepts the real CAISO fleet
arrays at ``get_reserve_design`` (fleet fully built, LP not yet solved),
computes per-region reserve-eligible 10-min ramp supply split into
fast-start (offline-capable, the spin back-spin leak) vs postured
(commitment-costed) vs hydro, and compares to the measured regional
spin/non-spin minima. Aborts before the LP.

Usage: python -m scripts.probes._caiso71_honesty_check
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"

SP26_ZONES = {"LA_BASIN", "SDGE", "SP15_rest"}
NP26_ZONES = {"NP15", "ZP26"}


class _Done(Exception):
    pass


def _report(config, fleet_arrays, zone_names):
    from market_sim.config.reserve_config import (
        _caiso_reserve_eligible,
        _posture_pool_params,
        FUEL_TYPE_NAMES,
        CAISO_HYDRO_RAMP10_FRAC,
    )

    fa = fleet_arrays
    zone_names = list(zone_names)
    eligible = _caiso_reserve_eligible(fa)
    fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
    pmax = np.asarray(fa.pmax, float)
    avail = np.asarray(fa.availability, float)
    # availability may be (n,) or (n,T); use mean over time for a scalar cap
    avail_mean = avail.mean(axis=1) if avail.ndim == 2 else avail
    ramp10 = np.asarray(fa.ramp10, float).copy()
    is_hydro = fuel == "hydro"
    ramp10 = np.where(
        is_hydro & (ramp10 <= 0.0), CAISO_HYDRO_RAMP10_FRAC * pmax, ramp10
    )
    zidx = np.asarray(fa.zone_idx, int)
    zname = np.array([zone_names[z] for z in zidx])

    pergen = eligible & (ramp10 > 0.0)
    # deliverable ramp per unit (availability-scaled), the pergen col cap basis
    dramp = ramp10 * avail_mean

    # Reproduce the pergen (zone,fuel) pool → fast-start classification exactly
    gidx = np.flatnonzero(pergen)
    zg = zidx[gidx]
    fg = np.asarray(fa.fuel_type_idx, int)[gidx]
    keys = np.stack([zg, fg], axis=1)
    _, col = np.unique(keys, axis=0, return_inverse=True)
    n_r = int(col.max()) + 1 if col.size else 0
    posture_pools, _, _ = _posture_pool_params(fa, gidx, col, n_r, str(config.iso))
    postured = np.zeros(n_r, dtype=bool)
    postured[posture_pools] = True
    # per-unit: is its pool postured (needs a start) or fast-start (free offline)?
    unit_postured = postured[col]

    def region_supply(zone_set):
        m = np.isin(zname[gidx], list(zone_set))
        r = dramp[gidx]
        fu = fuel[gidx]
        fast = ~unit_postured & m
        post = unit_postured & m
        hyd = (fu == "hydro") & m
        gas_fast = fast & np.isin(fu, ["gas"]) if "gas" in set(fu) else fast
        return {
            "fast_start_ramp": float(r[fast].sum()),
            "fast_start_ex_hydro": float(r[fast & ~(fu == "hydro")].sum()),
            "postured_ramp": float(r[post].sum()),
            "hydro_ramp": float(r[hyd].sum()),
            "total_ramp": float(r[m].sum()),
        }

    sp = region_supply(SP26_ZONES)
    npr = region_supply(NP26_ZONES)

    # Measured minima (evening peak, from data/raw/CAISO-AS)
    minima = {
        "SP26": {"spin_evening": 63.0, "nonspin_evening": 255.0},
        "NP26": {"spin_evening": 63.0, "nonspin_evening": 255.0},
    }

    print("\n================ caiso-71 HONESTY CHECK ================")
    print(f"iso={config.iso}  zones={zone_names}")
    print("Reserve-eligible pergen 10-min DELIVERABLE ramp (avail-scaled), MW:")
    for tag, s, req in [("SP26", sp, minima["SP26"]), ("NP26", npr, minima["NP26"])]:
        print(f"\n  {tag}  (zones {SP26_ZONES if tag == 'SP26' else NP26_ZONES})")
        print(
            f"    fast-start (offline-capable, spin back-spin LEAK): {s['fast_start_ramp']:8.0f}"
        )
        print(
            f"       of which non-hydro fast-start CT/oil          : {s['fast_start_ex_hydro']:8.0f}"
        )
        print(
            f"    hydro (fast, full-nameplate ramp10)              : {s['hydro_ramp']:8.0f}"
        )
        print(
            f"    postured (needs a start to provide reserve)      : {s['postured_ramp']:8.0f}"
        )
        print(
            f"    TOTAL in-region pergen ramp                      : {s['total_ramp']:8.0f}"
        )
        print(
            f"    measured evening minima  spin={req['spin_evening']:.0f}  nonspin={req['nonspin_evening']:.0f}  (sum={req['spin_evening'] + req['nonspin_evening']:.0f})"
        )
        free = s["fast_start_ramp"] + s["hydro_ramp"]
        need = req["spin_evening"] + req["nonspin_evening"]
        print(
            f"    FREE (fast-start+hydro, un-postured) = {free:.0f} MW  vs need {need:.0f} MW  -> "
            f"{'SERVABLE FOR FREE (posture inert; leak covers spin)' if free > need else 'binds'} ({free / need:.1f}x)"
        )
    print("=======================================================\n")
    raise _Done()


def main():
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "_caiso71_honesty_tmp"
    out.mkdir(parents=True, exist_ok=True)

    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["energy_reserve_coopt"] = True
    overrides["caiso_reserve_coopt"] = True
    overrides["caiso_commitment_posture"] = True
    overrides["caiso_scarcity_pricing"] = False

    import market_sim.config.reserve_config as rc

    orig = rc.get_reserve_design

    def patched(config, fleet_arrays, hours, zone_names, **kw):
        _report(config, fleet_arrays, zone_names)

    rc.get_reserve_design = patched

    try:
        solve_and_persist(
            [2024],
            cf["iso"],
            cf["hours"],
            _load_reference(),
            commitment=cf["commitment"],
            screen_coal=cf["commitment_screen_coal"],
            run_dir=out,
            coal_lignite_mustrun=cf["coal_lignite_mustrun"],
            coal_prb_mustrun=cf["coal_prb_mustrun"],
            coal_prb_passthrough=cf["coal_prb_passthrough"],
            outage_source=cf["outage_source"],
            coal_prb_passthrough_sigmoid=cf["coal_prb_passthrough_sigmoid"],
            coal_mustrun_per_plant=cf["coal_mustrun_per_plant"],
            retiree_cems_cap=cf["retiree_cems_cap"],
            ct_mustrun_per_plant=cf["ct_mustrun_per_plant"],
            ct_mustrun_floor_frac=cf["ct_mustrun_floor_frac"],
            coal_drop_pof=cf["coal_drop_pof"],
            coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
            prb_overrides=overrides,
            coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
            bit_overrides=cf["coal_bit_sigmoid_overrides"],
            ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],
            ercot_dam_as_overlay=cf["ercot_dam_as_overlay"],
            ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
            ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
            offer_curve_overrides=cf["offer_curve_overrides"],
            offer_curve_deltas=cf["offer_curve_deltas"],
            curve_smoothing={
                "offer_curve_smoothing_n": 6,
                "offer_curve_smoothing_exp": 1.0,
                "offer_curve_smoothing_mid": None,
            },
            priced_interchange=cf["priced_interchange"],
            capacity_deliverability_limits=True,
            caiso_ra_mustoffer=True,
            caiso_ra_min_load_frac=0.26,
            caiso_ra_startup_bridge=True,
            caiso_ra_bridge_decommit=True,
            caiso_gas_floor_frac=0.8,
            caiso_solar_deliverability=True,
            caiso_solar_endogenous_spill=True,
            caiso_per_hub_intertie=True,
            caiso_perhub_firm_base=True,
            caiso_corridor_flow_limit=True,
            temp_dependent_derate=True,
            ct_netload_drag=False,
            note="caiso-71 honesty check (aborts before LP)",
        )
    except _Done:
        print("aborted before LP as designed.")
    finally:
        rc.get_reserve_design = orig


if __name__ == "__main__":
    main()
