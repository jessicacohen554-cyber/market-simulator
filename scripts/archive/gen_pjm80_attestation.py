"""Generate the pjm-80 keeper calibration_attestation.json (DOF ledger).

Transforms the pjm-77 keeper attestation into pjm-80's: the G-21 SRMC
re-grounding removes ST_GAS (and CT_INTERMEDIATE) from the sub-SRMC below-floor
residual DOF, and the CT_CHP reliability-limb scrub is noted on the
reliability-floor measured-physical entry. Run after the bundle is scored so the
residuals_note reflects the committed legitimacy numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path(
    "results/calibration/pjm77_ct_relfloor_reconcile/calibration_attestation.json"
)
DST = Path(
    "results/calibration/pjm80_srmc_reground_keeper/calibration_attestation.json"
)

D4_NOTE = (
    "D-4 reliability_floor x CT_CHP (the deciding pjm-77 keeper failure: "
    "0.0052/0.0095/0.009 TWh, 70.8% off-window all years) is RESOLVED — the "
    "EMAAC/Central_PA CT_CHP tmax limbs are scrubbed (L-13 step 1). The only "
    "residual D-4 flag is reliability_floor x CT_PEAKER 0.0002 TWh (100% "
    "off-window in 2023 only), a mixed-fuel-plant class-aggregation artifact "
    "(ORIS 50279 ST_GAS + 2406 CC_REGULAR each co-site a CT_PEAKER tranche; the "
    "reliability floor on their steam/CC tranche is labeled onto the plant's "
    "CT_PEAKER class at plant-grain). The authoritative solve floors "
    "(floors/*_P1.npz) carry ZERO CT_PEAKER reliability cells — the drag owns "
    "CT_PEAKER cleanly (drop_drag_owned_reliability_specs) and its D-4 is 0% "
    "off-window every year. 47x smaller than the pjm-77 CT_CHP failure and on a "
    "dropped, not a real, floor."
)


def main() -> None:
    att = json.loads(SRC.read_text())

    g = att["governance"]
    g["attested_by"] = "pjm-80 srmc-reground-keeper 2026-07-06 (L-13)"
    g["note"] = (
        "pjm-77 keeper recipe with two grounded structural changes: (1) G-21 "
        "SRMC re-grounding — the two sub-SRMC residual offer artifacts ST_GAS "
        "(committed/econ_low/econ_high 0.4752/0.6552/0.90) and CT_INTERMEDIATE "
        "(committed/econ_low 0.9/0.92) move to the Manual-15 composite-cost "
        "floor 1.00x (rule 1: a non-CHP steam/CT unit's part-load IHR exceeds "
        "full-load, so no tranche may clear below 1.0x AHR x delivered fuel — "
        "the same floor CC_REGULAR carries); (2) CT_CHP EMAAC/Central_PA "
        "reliability tmax limbs scrubbed (rule 19: the class's all-hours "
        "steam-host hot-day lift is owned by chp_steam, not a sub-daily floor). "
        "The ct_netload_drag window [15,22) is UNCHANGED: the L-13 "
        "overnight-reliability evidence check (scripts/diag_pjm_ct_overnight_"
        "evidence.py; docs/handoffs/pjm-ct-overnight-evidence-2026-07.md) "
        "confirmed overnight CT CF is a flat ~2% net-load-insensitive economic "
        "baseline (not reliability) plus a small extreme-net-load uptick 3-5x "
        "weaker than the ramp relationship — the correct window, with the "
        "extreme-net-load overnight duty owned by reserve/ORDC (G-20 Phase 2). "
        "No drag coefficient re-derived (rule 24)."
    )
    g["residuals_note"] = (
        D4_NOTE + " D-2 forced-energy PASS under rubric v2.1 (owner 2026-07-06 peaker "
        "budget 0.15): ct_netload_drag CT_PEAKER 9.2/14.5/10.2% (2024 tightest, "
        "< 15%); ST_GAS collapses to an immaterial <2%-load class once the "
        "sub-SRMC flood is removed. DISCOVERED BUG (rule 14, NOT a reason to "
        "revert): de-flooding ST_GAS relocates ~14-16 TWh/yr to CC_REGULAR "
        "(over-run) rather than to the actual level — real ST_GAS runs far more "
        "than a pure-efficiency merit order clears, an unmodeled RMR/local-"
        "deliverability driver (issue #1483). The CT_PEAKER under-dispatch this "
        "does not fix is reserve/ORDC deployment (G-20 Phase 2), not the offer "
        "axis. Scarcity tail unchanged (0 h, the memory-blocked per-gen "
        "reserve/ORDC item, burndown 3)."
    )

    fp = att["free_parameters"]
    fp["seeded"] = (
        fp["seeded"] + "; pjm-80 (L-13): ST_GAS + CT_INTERMEDIATE committed "
        "bands re-grounded to the Manual-15 SRMC floor (G-21), removing them "
        "from the residual below-floor DOF."
    )
    new_entries = []
    for e in fp["entries"]:
        if e["name"] == "offer_curve_committed_below_floor[PJM]":
            # ST_GAS re-grounded to 1.00 (no longer sub-floor); the remaining
            # below-floor committed bands are physics-grounded (coal
            # take-or-pay incremental cost, CHP steam-host credit), not
            # residual artifacts. Reclassify measured-physical.
            val = dict(e["value"])
            val.pop("ST_GAS", None)
            e = dict(e)
            e["value"] = val
            e["n_scalars"] = len(val)
            e["identification"] = "measured-physical"
            e["source"] = (
                "post-G-21: the only non-CHP/non-take-or-pay sub-SRMC committed "
                "bands (ST_GAS 0.4752, CT_INTERMEDIATE 0.90) were re-grounded to "
                "1.00x (Manual-15 floor); the remaining below-flag committed "
                "multipliers are physically grounded — COAL_* take-or-pay "
                "incremental cost (below full AHR by construction) and CC_CHP "
                "steam-host credit. No residual sub-SRMC artifact remains "
                "(FINDING-pjm-burndown-2026-07.md 2 grounding test: all SURVIVE)."
            )
            e["root_cause"] = (
                "G-21 CLOSED for ST_GAS/CT_INTERMEDIATE (re-grounded, pjm-80); "
                "ST_GAS actual-volume driver tracked as issue #1483."
            )
        elif e["name"] == "reliability_floor coefficients":
            e = dict(e)
            e["note"] = (
                e["note"]
                + " L-13 (pjm-80): the PJM EMAAC + Central_PA CT_CHP tmax limbs "
                "are SCRUBBED (enabled=False) — all-24h flat floors binding 70.8% "
                "off-window (rule 17), the class owned by chp_steam (rule 19). "
                "Locked by tests/test_reliability_floor.py::TestPjmCtChpScrubLocked "
                "(rule 26). Re-derive trigger remains the 2026 CAMPD publication."
            )
        new_entries.append(e)
    fp["entries"] = new_entries
    fp["n_residual"] = sum(
        1 for e in new_entries if e.get("identification") == "residual"
    )
    fp["n_entries"] = len(new_entries)

    DST.write_text(json.dumps(att, indent=4))
    print(f"wrote {DST} (n_entries={fp['n_entries']}, n_residual={fp['n_residual']})")


if __name__ == "__main__":
    main()
