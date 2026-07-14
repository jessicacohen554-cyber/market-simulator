"""THROWAWAY no-LP wiring check for ``coal_committed_takeorpay_regulated``.

Reconstructs the MISO fleet + assembled P0 offers via
``run_year(fleet_only=True)`` (no solve) twice — the miso-65 keeper recipe
verbatim (coal_bit_committed_takeorpay armed) vs the lane-1 conduct candidate
(coal_committed_takeorpay_regulated armed, the BIT flag dropped so the
regulated scope SUPERSEDES it, rule 19) — and reports, per coal supply x
EIA-860 Regulatory Status, which ``_committed`` tranches' offers moved and
by how much (cap-weighted $/MWh). Expected from the design
(docs/handoffs/miso-coal-conduct-design-2026-07.md):

- RE prb/lignite ``_committed`` tranches drop from full delivered SRMC to
  sunk-fuel bids (VOM + non-fuel adders; ~9.9 GW);
- RE bituminous ``_committed`` tranches UNCHANGED (covered under both flags);
- NR bituminous ``_committed`` (Prairie State, Warrick, ADM Decatur, Filer
  City; ~1.05 GW) RISE back to full delivered cost (the BIT flag had
  discounted them; merchants bid economically per SOM Table 7);
- every non-committed tranche and every non-coal unit byte-identical.

Usage: PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso_coalconduct_wiring.py [year]
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"


def _state(meta: dict, year: int, regulated: bool) -> dict:
    from run_calibration import run_year  # heavy import

    prb = dict(meta.get("coal_prb_sigmoid_overrides") or {})
    # the miso-64/65 keeper recipe additions (all stay armed)
    prb["miso_rpe_pricing"] = True
    prb["unit_outage_short_windows"] = True
    prb["class_aware_fuel_price_fallback"] = True
    if regulated:
        prb["coal_bit_committed_takeorpay"] = False
        prb["coal_committed_takeorpay_regulated"] = True
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
    off = _state(meta, year, regulated=False)
    on = _state(meta, year, regulated=True)

    fa = off["fleet_arrays"]
    assert list(on["fleet_arrays"].unit_ids) == list(fa.unit_ids)
    mc_off = off["mc_base"]
    mc_on = on["mc_base"]

    from market_sim.data.fleet import eia860_regulated_plants

    re_set = eia860_regulated_plants()
    supply = pd.read_csv(
        Path("data/raw/_processed-legacy/coal_supply_MISO.csv")
    ).set_index("plant_code")["supply_class"]

    uids = np.array([str(u) for u in fa.unit_ids], dtype=object)
    plants = np.asarray(fa.plant_code, dtype=int)
    ann_off = mc_off.mean(axis=1)
    ann_on = mc_on.mean(axis=1)
    moved = ~np.isclose(ann_off, ann_on)

    committed = np.array([u.endswith("_committed") for u in uids])
    print(f"MISO {year}: {int(moved.sum())} / {len(uids)} units moved")
    rows: dict[tuple[str, str], list[int]] = {}
    for i in np.where(moved)[0]:
        sup = str(supply.get(plants[i], "?"))
        reg = "RE" if plants[i] in re_set else "NR"
        rows.setdefault((sup, reg), []).append(i)
    for (sup, reg), idx in sorted(rows.items()):
        idx = np.array(idx)
        w = fa.pmax[idx]
        print(
            f"  {sup:14s} {reg}  moved {len(idx):3d} tranches {w.sum():8.0f} MW: "
            f"cap-wtd ${np.average(ann_off[idx], weights=w):.2f} -> "
            f"${np.average(ann_on[idx], weights=w):.2f}/MWh"
        )
    # Guards: only _committed coal tranches may move; everything else identical.
    bad = moved & ~committed
    print("  non-committed movers:", int(bad.sum()))
    same = ~moved
    print(
        "  unmoved max |delta|:",
        float(np.abs(mc_off[same] - mc_on[same]).max()) if same.any() else 0.0,
    )


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2024)
