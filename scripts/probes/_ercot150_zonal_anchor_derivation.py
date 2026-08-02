#!/usr/bin/env python3
"""ercot-150 derivation record — the weights behind the ERCOT zone anchors.

Documents the arithmetic of the ERCOT zonal-anchor derivation
(PREREG-ercot150-zonal-margin-anchor-2026-08-02.md §1.3): per-year per-zone gas
capacity from the keeper's own fleet (``reconstruct_bundle_fleet``, no LP — the
same reconstruction the derive uses), the capacity-weighted mean of the raw
basis the applier removes each year, the measured EP level correction the
applier ADDS each year (``ercot_electric_power_gas_basis`` minus the ``-0.50``
scalar — ERCOT's difference from PJM's pure mean-zero convention), the
marked-up-tranche census, and the consistency stat that the capacity-weighted
mean of the derived zone anchors reproduces **ISO anchor + window-mean level
correction** (NOT the bare ISO anchor: the level term is one-sided by
construction; any residual beyond it is the applier's own ``_GAS_PRICE_FLOOR``
hourly clip on the deep-discount West tail).

Also REPORTS (prereg §1.4, disclosed limitation, never a gate): the keeper's
``ercot_west_netload_gas_shape`` runs AFTER the zonal basis and redistributes
the West/Panhandle series across hours mean-preservingly EXCEPT its delivered
burner-tip floor (0.4 $/MMBtu), whose binding lifts the West annual mean above
the zone anchor derived here. The would-be lift is computed no-LP from the
measured collapse frequency + the keeper's firm basis + the floor, so the
FINDING can carry both numbers. Pure record; no value here feeds a solve.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_ercot150_zonal_anchor_derivation.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/ercot149_gas_event_cap_arm"
OUT_PATH = REPO / "results/calibration/_ercot150_zonal_anchor_derivation.json"

YEARS = (2023, 2024, 2025)

#: The keeper's West-shape parameters (meta.json coal_prb_sigmoid_overrides):
#: burner-tip delivered floor; the firm basis defaults to
#: GAS_BASIS_DIFFERENTIAL["ERCOT"] because the keeper does not set
#: ercot_west_gas_firm_basis.
WEST_DELIV_FLOOR = 0.4


def main() -> int:
    """Rebuild the keeper fleet per year and record the weighting arithmetic."""
    import sys

    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    from market_sim.config.constants import (
        GAS_BASIS_DIFFERENTIAL,
        GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
    )
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX, _pkg_ns
    from market_sim.data.fuel.basis.ercot import (
        ercot_electric_power_gas_basis,
        ercot_waha_collapse_freq,
        ercot_zonal_gas_basis_by_zone,
    )
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    zone_names = list(get_iso_config("ERCOT").zone_names)
    iso_anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"]
    scalar = GAS_BASIS_DIFFERENTIAL.get("ERCOT", 0.0)
    table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE.get("ERCOT", {})

    per_year: dict[str, dict] = {}
    window_w = {z: 0.0 for z in zone_names}
    level_corrs: list[float] = []
    for year in YEARS:
        state, _meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=True)
        fleet = state["fleet_arrays"]
        gens = state["fleet"]
        gas = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
        w_by_zone = {
            z: float(fleet.pmax[gas[fleet.zone_idx[gas] == i]].sum())
            for i, z in enumerate(zone_names)
        }
        basis = ercot_zonal_gas_basis_by_zone(year) or {}
        # The applier's own weighting: per-UNIT basis over gas rows (all rows
        # in a zone share it — the keeper arms no contract haircut).
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
        # West netload-shape floor-lift REPORT (no LP; approximation notes in
        # the prereg): collapse fraction = measured neg-day frequency (the
        # solve's realised fraction differs only through net-load quantile
        # ties); firm = HH annual mean + the keeper's firm basis (the -0.50
        # scalar default), floored at the burner-tip delivered floor.
        hh = _pkg_ns()._henry_hub_monthly(None)
        hh_months = [hh[(year, m)] for m in range(1, 13) if (year, m) in hh]
        hh_mean = float(np.mean(hh_months)) if hh_months else None
        freq = ercot_waha_collapse_freq(year)
        west_lift = None
        if hh_mean is not None and freq is not None and "West" in table:
            firm = max(hh_mean + scalar, WEST_DELIV_FLOOR)
            f = min(max(float(freq), 0.01), 0.99)
            # Per-year West level = the derive's per-year value, read back out
            # of the registered window anchor is not possible — so the lift is
            # computed against the per-year post-basis mean recorded by the
            # derive run (filled from the derive stdout, prereg §1.3 table).
            # Here we bound it with the WINDOW anchor as the base (labelled).
            p_mean = float(table["West"])
            deep = (p_mean - (1.0 - f) * firm) / f
            deep_floored = max(deep, WEST_DELIV_FLOOR)
            west_lift = round(f * (deep_floored - deep), 4)
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
            "west_measured_collapse_freq": freq,
            "west_netload_floor_lift_on_window_anchor_REPORTED": west_lift,
        }
        for z in zone_names:
            window_w[z] += w_by_zone[z] / len(YEARS)
        del state

    zones_in_table = [z for z in zone_names if z in table]
    capw_anchor = (
        sum(window_w[z] * table[z] for z in zones_in_table)
        / sum(window_w[z] for z in zones_in_table)
        if table and sum(window_w[z] for z in zones_in_table)
        else None
    )
    mean_level_corr = float(np.mean(level_corrs)) if level_corrs else 0.0
    expected = iso_anchor + mean_level_corr
    res = {
        "probe": "ercot-150 zonal-anchor derivation record (weights + invariant)",
        "weights_bundle": str(BUNDLE.relative_to(REPO)),
        "iso_anchor": iso_anchor,
        "scalar_basis_in_iso_anchor": scalar,
        "zone_anchor_table": table,
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
            "ERCOT's invariant is capw(zone anchors) == ISO anchor + "
            "window-mean level correction (the applier adds the flat EP level "
            "term on top of the mean-zero spread — scenarios/basis.ercot "
            "docstrings), up to the applier's own _GAS_PRICE_FLOOR hourly clip "
            "on the deep-discount West tail (a positive residual). "
            "capw uses the window-mean weights; the per-year invariant holds "
            "with that year's weights and level correction. The West "
            "netload-shape floor lift is REPORTED per year (prereg §1.4): the "
            "West anchor is the post-zonal-basis level (the registered "
            "ZONAL_BASIS_APPLIERS transform, definition uniform with "
            "NYISO/PJM); the hour-redistribution mechanism that runs after it "
            "owns its own floor lift (rule 19)."
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
            f"{row['n_marked_up_tranches']} marked-up tranches "
            f"({row['n_with_band_scoped_anchor']} band-scoped)"
        )
    if capw_anchor is not None:
        print(
            f"  capw(zone anchors) = {capw_anchor:.4f} vs ISO+level "
            f"{expected:.4f} (delta {capw_anchor - expected:+.4f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
