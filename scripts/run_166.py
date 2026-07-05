"""Run 166 = run 164 + STORAGE AS DURATION GATE (WS-B, G5 follow-up).

The one-delta probe for the ERCOT storage-AS duration gate: identical to
``run_164.py`` (the run157 keeper recipe with the DAM-AS overlay swapped for the
endogenous multi-product AS co-opt + forward AS requirement + RTOLCAP supply
cap, P1-only) with exactly ONE new delta:

  * ercot_storage_as_duration_gate=True — adds the published per-product ESR
    State-of-Charge durations (RegUp/RRS 1 h, ECRS 2 h, Non-Spin 4 h;
    ERCOT_AS_PRODUCT_DURATION_H) to the endogenous split. Storage's upward AS
    becomes an explicit per-zone reserve variable RS[c,z] bounded by the
    LP-linear gate Σ_c dur_c·RS[c,z] ≤ Σ_{s∈z} SOC[s], so a short-duration
    battery can no longer sell long-duration AS on its full power. Fixes the
    endogenous split's 2.1–2.4× over-hold vs the measured 60-Day DAM award
    (ercot32 root cause 1). Cleared storage AS still counts under RTOLCAP.

The measured storage treatment stays fully OFF (the endogenous split forces
storage_as_commitment / ercot_storage_as_reserve / ercot_storage_as_product_credit
off) — the consistent swap, never mixed (the ercot30 blow-up). The split table
is validated against the measured 60-Day DAM award (target 0.8–1.3×), never
pinned to it (CLAUDE.md #12).

Usage: python scripts/run_166.py [YEAR ...]   (default 2023 2024 2025)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

REPO = Path("/home/user/market-simulator")
cf = json.load(
    open(REPO / "results/calibration/ercot_run157_damas2024/run_config.json")
)["calibration_flags"]

prb = dict(cf["coal_prb_sigmoid_overrides"])
if isinstance(prb.get("wefor_residual_groups"), list):
    prb["wefor_residual_groups"] = frozenset(prb["wefor_residual_groups"])

years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
out_name = (
    "166" if years == [2023, 2024, 2025] else f"166_smoke_{'_'.join(map(str, years))}"
)
run_dir = REPO / "results/calibration" / out_name
run_dir.mkdir(parents=True, exist_ok=True)

solve_and_persist(
    years,
    "ERCOT",
    8760,
    _load_reference(),
    commitment=cf["commitment"],
    screen_coal=cf["commitment_screen_coal"],
    run_dir=run_dir,
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
    prb_overrides=prb,
    coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
    bit_overrides=cf["coal_bit_sigmoid_overrides"],
    offer_curve_overrides=cf["offer_curve_overrides"],
    offer_curve_deltas=cf["offer_curve_deltas"],
    ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],
    ercot_dam_as_overlay=False,
    ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
    ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
    energy_reserve_coopt=True,
    ercot_multiproduct_as_coopt=True,
    ercot_as_forward_requirement=True,
    ercot_storage_as_endogenous=True,
    ercot_storage_as_duration_gate=True,  # the one delta vs run164
    ercot_reserve_supply_cap=True,
    ercot_reserve_supply_cap_from_year=2023,
)
print("166 done:", run_dir)
