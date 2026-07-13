"""THROWAWAY no-LP wiring check for ``class_aware_fuel_price_fallback``.

Reconstructs the MISO fleet + resolved fuel prices via
``run_year(fleet_only=True)`` (no solve) twice — gate off vs on — and reports,
per gas/coal model class, how many units' delivered fuel price moved and the
capacity-weighted before/after $/MMBtu. Expected from the measured diagnosis
(docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md §6): the ~33% of CT_PEAKER
capacity without its own F923 filing moves from the CC-dominated ~$2.6-2.8
state mean toward the CT filers' ~$4.1 cap-weighted class mean; CC gap-fills
barely move (they already dominate the class-blind pool).

Usage: PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso_classdonor_wiring.py [year]
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"


def _state(meta: dict, year: int, class_aware: bool) -> dict:
    from run_calibration import run_year  # heavy import

    prb = dict(meta.get("coal_prb_sigmoid_overrides") or {})
    # miso-63's two additions ride the same channel; irrelevant to fuel
    # prices but kept so the config matches the current keeper.
    prb["miso_rpe_pricing"] = True
    prb["unit_outage_short_windows"] = True
    if class_aware:
        prb["class_aware_fuel_price_fallback"] = True
    return run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        meta["gas_prices"][str(year)],
        ttc_overrides={},
        commitment_enabled=False,
        commitment_screen_coal=meta.get("commitment_screen_coal", True),
        outage_source=meta.get("outage_source", "historic"),
        coal_prb_passthrough=meta.get("coal_prb_passthrough", 1.0),
        coal_prb_passthrough_sigmoid=meta.get("coal_prb_passthrough_sigmoid", False),
        coal_prb_passthrough_tiered=meta.get("coal_prb_passthrough_tiered", False),
        coal_bit_sigmoid=meta.get("coal_bit_passthrough_sigmoid", False),
        coal_mustrun_per_plant=meta.get("coal_mustrun_per_plant", False),
        coal_drop_pof=meta.get("coal_drop_pof", False),
        ct_intermediate_split=meta.get("ct_intermediate_split", False),
        cc_intermediate_split=meta.get("cc_intermediate_split", False),
        st_gas_intermediate=meta.get("st_gas_intermediate", False),
        miso_zonal_gas_basis=meta.get("miso_zonal_gas_basis", False),
        miso_rdt_tcdc=meta.get("miso_rdt_tcdc", False),
        miso_zonal_reserves=meta.get("miso_zonal_reserves", False),
        miso_reserve_pergen=meta.get("miso_reserve_pergen", False),
        miso_measured_reserve_requirements=meta.get(
            "miso_measured_reserve_requirements", False
        ),
        miso_south_seam_split=meta.get("miso_south_seam_split", False),
        miso_firm_imports=meta.get("miso_firm_imports"),
        miso_seam_flow_limit=meta.get("miso_seam_flow_limit", False),
        miso_seam_export_limit=meta.get("miso_seam_export_limit", False),
        miso_seam_measured_ladder=meta.get("miso_seam_measured_ladder", False),
        miso_pjm_border_anchor=meta.get("miso_pjm_border_anchor", False),
        cc_nameplate_summer_derate=meta.get("cc_nameplate_summer_derate", False),
        priced_interchange=meta.get("priced_interchange", False),
        prb_overrides=prb,
        fleet_only=True,
    )


def main(year: int) -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    off = _state(meta, year, class_aware=False)
    on = _state(meta, year, class_aware=True)

    fa = off["fleet_arrays"]
    fp_off = off["fuel_prices"]
    fp_on = on["fuel_prices"]
    assert fa.plant_group is not None, "MISO fleet must carry plant_group"
    assert list(on["fleet_arrays"].unit_ids) == list(fa.unit_ids)

    groups = np.array([str(g) for g in fa.plant_group], dtype=object)
    ann_off = fp_off.mean(axis=1)
    ann_on = fp_on.mean(axis=1)
    moved = ~np.isclose(ann_off, ann_on)

    print(f"MISO {year}: {int(moved.sum())} / {fa.n_gen} units moved")
    for klass in sorted(set(groups)):
        sel = groups == klass
        m = sel & moved
        if not m.any():
            continue
        w = fa.pmax[m]
        print(
            f"  {klass:12s} moved {int(m.sum()):4d} units {w.sum():8.0f} MW "
            f"(of {fa.pmax[sel].sum():8.0f} MW): "
            f"cap-wtd ${np.average(ann_off[m], weights=w):.2f} -> "
            f"${np.average(ann_on[m], weights=w):.2f}/MMBtu"
        )
    # Unmoved sanity: everything else byte-identical.
    same = ~moved
    print(
        "  unmoved max |delta|:",
        float(np.abs(fp_off[same] - fp_on[same]).max()) if same.any() else 0.0,
    )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2024)
