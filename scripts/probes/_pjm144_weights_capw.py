#!/usr/bin/env python3
"""pjm-144 derivation record — the weights behind the PJM zone anchors.

Documents the capacity-weighted mean-zero arithmetic of the PJM zonal-anchor
derivation (PREREG-pjm144-zonal-margin-anchor-2026-08-02.md §1.3): per-year
per-zone gas capacity from the keeper's own fleet
(``reconstruct_bundle_fleet``, no LP — the same reconstruction the derive
uses), the capacity-weighted mean of the raw basis the applier removes each
year, the marked-up-tranche census, and the consistency stat that the
capacity-weighted mean of the derived zone anchors reproduces the ISO anchor
(the applier's mean-zero invariant). Pure record; no value here feeds a solve.

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_pjm144_weights_capw.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/pjm143_hy_level_B"
OUT_PATH = REPO / "results/calibration/_pjm144_zonal_anchor_derivation.json"

YEARS = (2023, 2024, 2025)


def main() -> int:
    """Rebuild the keeper fleet per year and record the weighting arithmetic."""
    import sys

    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    from market_sim.config.constants import (
        GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
    )
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX
    from market_sim.data.fuel.basis.pjm import pjm_zonal_gas_basis_by_zone
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    zone_names = list(get_iso_config("PJM").zone_names)
    iso_anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"]
    table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE.get("PJM", {})

    per_year: dict[str, dict] = {}
    window_w = {z: 0.0 for z in zone_names}
    for year in YEARS:
        state, _meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=True)
        fleet = state["fleet_arrays"]
        gens = state["fleet"]
        gas = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
        w_by_zone = {
            z: float(fleet.pmax[gas[fleet.zone_idx[gas] == i]].sum())
            for i, z in enumerate(zone_names)
        }
        basis = pjm_zonal_gas_basis_by_zone(year) or {}
        total = sum(w_by_zone.values())
        capw_mean = (
            sum(w_by_zone[z] * basis.get(z, 0.0) for z in zone_names) / total
            if total
            else 0.0
        )
        marked = [
            g
            for g in gens
            if getattr(g, "offer_markup_hr", 0.0) > 0.0
        ]
        on_band_anchor = [
            g for g in marked if getattr(g, "offer_margin_anchor", None) is not None
        ]
        per_year[str(year)] = {
            "gas_capacity_mw_by_zone": {
                z: round(v, 1) for z, v in w_by_zone.items()
            },
            "raw_basis_vs_hh": {z: basis.get(z) for z in zone_names},
            "capacity_weighted_mean_removed": round(capw_mean, 4),
            "unweighted_mean_basis": round(
                float(np.mean([basis.get(z, 0.0) for z in zone_names])), 4
            ),
            "n_gas_rows": int(gas.size),
            "n_marked_up_tranches": len(marked),
            "n_with_band_scoped_anchor": len(on_band_anchor),
        }
        for z in zone_names:
            window_w[z] += w_by_zone[z] / len(YEARS)
        del state

    capw_anchor = (
        sum(window_w[z] * table.get(z, 0.0) for z in zone_names)
        / sum(window_w.values())
        if table and sum(window_w.values())
        else None
    )
    res = {
        "probe": "pjm-144 zonal-anchor derivation record (weights + invariant)",
        "weights_bundle": str(BUNDLE.relative_to(REPO)),
        "iso_anchor": iso_anchor,
        "zone_anchor_table": table,
        "per_year": per_year,
        "window_mean_gas_capacity_mw_by_zone": {
            z: round(v, 1) for z, v in window_w.items()
        },
        "capw_mean_of_zone_anchors": (
            round(capw_anchor, 4) if capw_anchor is not None else None
        ),
        "capw_minus_iso_anchor": (
            round(capw_anchor - iso_anchor, 4) if capw_anchor is not None else None
        ),
        "note": (
            "capw_mean_of_zone_anchors uses the window-mean weights; the "
            "applier's invariant is exact per-year (each year's "
            "capacity-weighted mean of the transformed levels equals that "
            "year's ISO series mean, up to the 0.10 $/MMBtu gas floor), so the "
            "window stat differs from the ISO anchor only through "
            "year-to-year weight drift."
        ),
    }
    OUT_PATH.write_text(json.dumps(res, indent=1) + "\n")
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")
    for year in YEARS:
        row = per_year[str(year)]
        print(
            f"  {year}: capw mean removed {row['capacity_weighted_mean_removed']:+.4f} "
            f"(unweighted {row['unweighted_mean_basis']:+.4f}), "
            f"{row['n_marked_up_tranches']} marked-up tranches "
            f"({row['n_with_band_scoped_anchor']} band-scoped)"
        )
    if capw_anchor is not None:
        print(
            f"  capw(zone anchors) = {capw_anchor:.4f} vs ISO anchor "
            f"{iso_anchor} (delta {capw_anchor - iso_anchor:+.4f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
