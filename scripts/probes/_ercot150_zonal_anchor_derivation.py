#!/usr/bin/env python3
"""ercot-150 derivation record — the weights and decomposition behind the ERCOT zone anchors.

Documents the arithmetic of the ERCOT zonal-anchor derivation
(PREREG-ercot150-zonal-margin-anchor-2026-08-02.md §1.3): per-year per-zone gas
capacity from the keeper's own fleet (``reconstruct_bundle_fleet``, no LP — the
same reconstruction the derive uses), the capacity-weighted mean of the raw
basis the applier removes each year, the measured EP level correction the
applier ADDS each year (``ercot_electric_power_gas_basis`` minus the ``-0.50``
scalar — ERCOT's difference from PJM's pure mean-zero convention), the
marked-up-tranche census, and the WEST DECOMPOSITION: the ERCOT anchors are
read from the reconstruction's own resolved ``fuel_prices`` (the exact array
``apply_gas_offer_margin`` prices against —
``derive_gas_offer_margin_anchor.SOLVE_FUEL_ARRAY_ISOS``), so the West value
includes the keeper's ``ercot_west_netload_gas_shape`` burner-tip floor lift
on top of the post-zonal-basis level. Both stages are recorded per year:

* ``post_basis`` — the synthetic-series + runtime-basis-applier construction
  (what the value would be if the fuel path ENDED at the zonal basis, the
  NYISO/PJM-shaped definition);
* ``realized`` — the solve-array mean (the registered anchor's per-year
  value), whose exact reproduction against the registered table is asserted.

The record also carries the consistency stat: capw(zone anchors) vs
ISO anchor + window-mean level correction, whose positive residual is the
West net-load floor lift (weighted by West's small gas-capacity share) plus
the ``_GAS_PRICE_FLOOR`` hourly clip. Pure record; no value here feeds a
solve.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_ercot150_zonal_anchor_derivation.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
# ercot-191 (signature A1, rule 23): the original weights bundle
# ercot149_gas_event_cap_arm was retention-pruned from disk (top-15 rule), so
# the record re-derives off the current keeper bundle — same recipe lineage
# (every keeper since ercot-149 carries the identical gas fleet and fuel
# path), and the ercot-191 re-derivation on the ruling-#9/#8/#10-repaired DAM
# artifacts reproduced the registered table EXACTLY (all six zones, 4-dp),
# which is the freeze clause's re-assertion.
BUNDLE = REPO / "results/calibration/ercot191_dam_rederive_regate"
OUT_PATH = REPO / "results/calibration/_ercot150_zonal_anchor_derivation.json"

YEARS = (2023, 2024, 2025)

#: Reproduction tolerance for the registered per-year table values ($/MMBtu):
#: the constants table stores 4-decimal roundings of the solve-array means.
REPRO_TOL = 5e-5


def main() -> int:
    """Rebuild the keeper fleet per year and record the derivation arithmetic."""
    import sys

    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    from market_sim.config.constants import (
        GAS_BASIS_DIFFERENTIAL,
        GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
    )
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.config.constants import HOURS_PER_YEAR
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX
    from market_sim.data.fuel.basis.ercot import (
        apply_ercot_zonal_gas_basis,
        ercot_electric_power_gas_basis,
        ercot_waha_collapse_freq,
        ercot_zonal_gas_basis_by_zone,
    )
    from market_sim.data.fuel.trajectories import _gas_series
    from scripts.data.derive_gas_offer_margin_anchor import (
        GAS_SERIES_FLAGS,
        TRAIN_WINDOW_HH,
    )
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    zone_names = list(get_iso_config("ERCOT").zone_names)
    iso_anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"]
    scalar = GAS_BASIS_DIFFERENTIAL.get("ERCOT", 0.0)
    table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE.get("ERCOT", {})
    base = ScenarioConfig(
        iso="ERCOT", mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS["ERCOT"]
    )

    per_year: dict[str, dict] = {}
    window_w = {z: 0.0 for z in zone_names}
    level_corrs: list[float] = []
    repro_fail: list[str] = []
    for year in YEARS:
        state, _meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=True)
        fleet = state["fleet_arrays"]
        gens = state["fleet"]
        rec_cfg = state["config"]
        fuel_prices = np.asarray(state["fuel_prices"], dtype=float)
        gas = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
        w_by_zone = {
            z: float(fleet.pmax[gas[fleet.zone_idx[gas] == i]].sum())
            for i, z in enumerate(zone_names)
        }
        basis = ercot_zonal_gas_basis_by_zone(year) or {}
        gen_basis = np.array(
            [basis.get(zone_names[int(zi)], 0.0) for zi in fleet.zone_idx[gas]]
        )
        weights = fleet.pmax[gas]
        capw_mean = (
            float((gen_basis * weights).sum() / weights.sum())
            if weights.sum()
            else 0.0
        )
        ep_basis = ercot_electric_power_gas_basis(year)
        level_corr = (ep_basis - scalar) if ep_basis is not None else 0.0
        level_corrs.append(level_corr)
        marked = [g for g in gens if getattr(g, "offer_markup_hr", 0.0) > 0.0]
        on_band_anchor = [
            g for g in marked if getattr(g, "offer_margin_anchor", None) is not None
        ]
        # Realized per-zone means from the solve's own array (the registered
        # values), plus the post-basis synthetic decomposition for the zones
        # the net-load shape touches.
        series = _gas_series(
            base.with_overrides(gas_price_override=TRAIN_WINDOW_HH[year]),
            year,
            HOURS_PER_YEAR,
        )
        n_gen = int(fleet.pmax.shape[0])
        synth = np.repeat(series[None, :], n_gen, axis=0)
        apply_ercot_zonal_gas_basis(synth, fleet, rec_cfg, year)
        realized: dict[str, float] = {}
        post_basis: dict[str, float] = {}
        for i, zone in enumerate(zone_names):
            rows = gas[fleet.zone_idx[gas] == i]
            if rows.size == 0:
                continue
            realized[zone] = round(
                float(np.median(np.nanmean(fuel_prices[rows, :], axis=1))), 4
            )
            post_basis[zone] = round(float(np.nanmean(synth[rows[0]])), 4)
        per_year[str(year)] = {
            "gas_capacity_mw_by_zone": {
                z: round(v, 1) for z, v in w_by_zone.items()
            },
            "raw_basis_vs_hh": {z: basis.get(z) for z in zone_names},
            "capacity_weighted_mean_removed": round(capw_mean, 4),
            "unweighted_mean_basis": round(
                float(np.mean([basis.get(z, 0.0) for z in zone_names])), 4
            ),
            "ep_basis_vs_hh": (
                round(ep_basis, 4) if ep_basis is not None else None
            ),
            "level_correction_added": round(level_corr, 4),
            "n_gas_rows": int(gas.size),
            "n_marked_up_tranches": len(marked),
            "n_with_band_scoped_anchor": len(on_band_anchor),
            "west_measured_collapse_freq": ercot_waha_collapse_freq(year),
            "realized_zone_mean_solve_array": realized,
            "post_basis_zone_mean_synthetic": post_basis,
            "west_netload_floor_lift": (
                round(realized["West"] - post_basis["West"], 4)
                if "West" in realized
                else None
            ),
        }
        for z in zone_names:
            window_w[z] += w_by_zone[z] / len(YEARS)
        del state, fuel_prices, synth

    zones_in_table = [z for z in zone_names if z in table]
    capw_anchor = (
        sum(window_w[z] * table[z] for z in zones_in_table)
        / sum(window_w[z] for z in zones_in_table)
        if table and sum(window_w[z] for z in zones_in_table)
        else None
    )
    mean_level_corr = float(np.mean(level_corrs)) if level_corrs else 0.0
    expected = iso_anchor + mean_level_corr
    # Exact-reproduction check: the registered window anchors are the mean of
    # the realized per-year values recorded above.
    for zone in zones_in_table:
        got = float(
            np.mean(
                [
                    per_year[str(y)]["realized_zone_mean_solve_array"][zone]
                    for y in YEARS
                ]
            )
        )
        if abs(got - float(table[zone])) > REPRO_TOL:
            repro_fail.append(f"{zone}: table {table[zone]} vs recomputed {got:.4f}")
    res = {
        "probe": "ercot-150 zonal-anchor derivation record (weights + decomposition)",
        "weights_bundle": str(BUNDLE.relative_to(REPO)),
        "iso_anchor": iso_anchor,
        "scalar_basis_in_iso_anchor": scalar,
        "zone_anchor_table": table,
        "table_reproduces_from_solve_array": not repro_fail,
        "table_reproduction_failures": repro_fail,
        "per_year": per_year,
        "window_mean_gas_capacity_mw_by_zone": {
            z: round(v, 1) for z, v in window_w.items()
        },
        "window_mean_level_correction": round(mean_level_corr, 4),
        "capw_mean_of_zone_anchors": (
            round(capw_anchor, 4) if capw_anchor is not None else None
        ),
        "iso_anchor_plus_level_corr": round(expected, 4),
        "capw_minus_iso_plus_level": (
            round(capw_anchor - expected, 4) if capw_anchor is not None else None
        ),
        "note": (
            "The ERCOT anchors are read from the reconstruction's own "
            "resolved fuel_prices (SOLVE_FUEL_ARRAY_ISOS), so they include "
            "every keeper fuel-path stage: the mean-zero zonal spread, the "
            "flat EP level correction, the _GAS_PRICE_FLOOR hourly clip, and "
            "the West net-load two-regime shape whose burner-tip floor lifts "
            "the realized West mean above the post-basis level "
            "(west_netload_floor_lift per year). The consistency stat "
            "capw(zone anchors) vs ISO anchor + window-mean level correction "
            "therefore carries a small POSITIVE residual = the West lift "
            "weighted by West's gas-capacity share plus the hourly-clip "
            "asymmetry. The registered window anchors reproduce exactly from "
            "the per-year solve-array means (table_reproduces_from_solve_array)."
        ),
    }
    OUT_PATH.write_text(json.dumps(res, indent=1) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")
    for year in YEARS:
        row = per_year[str(year)]
        print(
            f"  {year}: capw mean removed {row['capacity_weighted_mean_removed']:+.4f} "
            f"(unweighted {row['unweighted_mean_basis']:+.4f}), "
            f"level corr {row['level_correction_added']:+.4f}, "
            f"West lift {row['west_netload_floor_lift']}, "
            f"{row['n_marked_up_tranches']} marked-up tranches "
            f"({row['n_with_band_scoped_anchor']} band-scoped)"
        )
    if capw_anchor is not None:
        print(
            f"  capw(zone anchors) = {capw_anchor:.4f} vs ISO+level "
            f"{expected:.4f} (residual {capw_anchor - expected:+.4f})"
        )
    print(
        "  table reproduces from solve array: "
        f"{'YES' if not repro_fail else 'NO — ' + '; '.join(repro_fail)}"
    )
    return 0 if not repro_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
