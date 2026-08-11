"""Seam proof for the ercot-186 rule-18 [R-PHYSICS] grain repair.

Executes, on the REAL keeper solve inputs for every scored year, the five
assertions pre-registered in ``docs/PRECOMMIT-ercot186-rule18-grain-2026-08-10.md``
§3 — SP-1 (the stamped plant physics is exactly the ercot-176 Amendment-2
per-plant read), SP-2 (the shipped row-grain gate is vacuous: it rejects zero
rows), SP-3 (the corrected gate's measured scope, reported at full magnitude),
SP-4 (the inertness adjudication the pre-registered prediction P-2 turns on),
SP-5 (the source-side stamp moves no ``FleetArrays`` field).

Run BEFORE any solve. Every assertion is checked against the fleet, offer
surfaces and net load the LP itself would see, reconstructed from the keeper
bundle with no LP built.

Usage::

    python scripts/probes/ercot186_grain_seamproof.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/ercot185_shapedarm_B"
YEARS = (2023, 2024, 2025)
OUT = REPO / "results/calibration/ercot186_grain_seamproof.json"

# The keeper's own armed gates, asserted on the reconstruction so the proof
# measures the keeper's surface and not a drifted one (the miso-116 trap).
ERCOT_REQUIRED_FLAGS = (
    "ercot_offer_surface_cleared_share",
    "ercot_offer_surface_cleared_share_rt",
    "ercot_faststart_pool_offer",
)


def _net_load(state: dict) -> np.ndarray:
    """The LP-served net load the offer surfaces condition on."""
    demand = state["demand"]
    return (
        demand.sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )


def _armed(config, **over):
    """A copy of ``config`` with ``over`` applied (pydantic or dataclass)."""
    if hasattr(config, "model_copy"):
        return config.model_copy(update=over)
    return dataclasses.replace(config, **over)


def _ct_prefixes(fleet) -> dict[str, list[int]]:
    """The pool builder's own row universe, prefix -> row indices."""
    from market_sim.data.fleet.offer_surfaces import _ERCOT_CLEARED_SHARE_CLASS_OF

    ct_groups = {
        grp for grp, key in _ERCOT_CLEARED_SHARE_CLASS_OF.items() if key == "CT"
    }
    prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(fleet):
        if (getattr(gen, "plant_group", None) or "") not in ct_groups:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
    return prefixes


def run_year(year: int) -> dict:
    """Return the seam-proof record for ``year``."""
    from market_sim.config.constants import FASTSTART_POOL_MIN_DOWN_HOURS
    from market_sim.data.fleet import build_ercot_faststart_pool_markup
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(
        BUNDLE, year, required_flags=ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    cfg_off = state["config"]
    fa, fleet, mc_base = state["fleet_arrays"], state["fleet"], state["mc_base"]
    nl = _net_load(state)
    rec: dict = {"year": year, "n_gen": int(mc_base.shape[0])}

    # ---------------------------------------------------------------- SP-1
    # The stamp is a pure grain restatement: for EVERY plant prefix in the
    # whole fleet, the stamped plant physics equals the max over that plant's
    # rows of the UC-coupling tag (the ercot-176 Amendment-2 read).
    all_prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(fleet):
        all_prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
    sp1_bad: list[str] = []
    sp1_bad_groups: dict[str, int] = {}
    sp1_bad_have_committed = 0
    n_stamped = 0
    for pref, rows in all_prefixes.items():
        stamped_md = {
            float(getattr(fleet[g], "plant_min_down_hours", 0) or 0) for g in rows
        }
        stamped_mr = {
            float(getattr(fleet[g], "plant_min_run_hours", 0) or 0) for g in rows
        }
        row_md = max(float(getattr(fleet[g], "min_down_hours", 0) or 0) for g in rows)
        row_mr = max(float(getattr(fleet[g], "min_run_hours", 0) or 0) for g in rows)
        # constant across the plant's rows AND equal to the max-over-rows read
        if len(stamped_md) != 1 or len(stamped_mr) != 1:
            sp1_bad.append(f"{pref}: not constant across rows")
            continue
        if max(stamped_md) != row_md or max(stamped_mr) != row_mr:
            sp1_bad.append(
                f"{pref}: stamped ({max(stamped_md)}, {max(stamped_mr)}) != "
                f"max-over-rows ({row_md}, {row_mr})"
            )
            grp = getattr(fleet[rows[0]], "plant_group", None) or "?"
            sp1_bad_groups[grp] = sp1_bad_groups.get(grp, 0) + 1
            # WHY a prefix can diverge (characterization of the SP-1 failure,
            # descriptive only — it changes no assertion): assembly drops a
            # tranche whose capacity is <= 0.5 MW, so a plant with no
            # `committed` slice records its physics on NO row at all and the
            # ercot-176 max-over-rows read returns 0 for it. The stamp does
            # not depend on which tranches survive.
            if any(
                fleet[g].unit_id.rpartition("_")[2].startswith("committed")
                for g in rows
            ):
                sp1_bad_have_committed += 1
        if max(stamped_md) > 0 or max(stamped_mr) > 0:
            n_stamped += 1
    rec["SP1_stamp_equals_ercot176_read"] = not sp1_bad
    rec["SP1_n_plant_prefixes"] = len(all_prefixes)
    rec["SP1_n_prefixes_with_nonzero_physics"] = n_stamped
    rec["SP1_n_mismatches"] = len(sp1_bad)
    rec["SP1_mismatch_by_group"] = sp1_bad_groups
    rec["SP1_n_mismatches_with_a_committed_tranche"] = sp1_bad_have_committed
    rec["SP1_mismatches"] = sp1_bad[:20]

    # ---------------------------------------------------------------- SP-2
    # The shipped (row-grain) gate is VACUOUS: over the pool's own row
    # universe it rejects zero bid rows.
    prefixes = _ct_prefixes(fleet)
    bid_rows = [
        g
        for rows in prefixes.values()
        for g in rows
        if fleet[g].unit_id.rpartition("_")[2].startswith(("econ", "peak"))
    ]
    rejected_rowgrain = [
        g
        for g in bid_rows
        if float(getattr(fleet[g], "min_down_hours", 0) or 0)
        > FASTSTART_POOL_MIN_DOWN_HOURS
    ]
    rec["SP2_n_ct_bid_rows"] = len(bid_rows)
    rec["SP2_n_rejected_by_row_grain_gate"] = len(rejected_rowgrain)
    rec["SP2_row_gate_is_vacuous"] = len(rejected_rowgrain) == 0

    # ---------------------------------------------------------------- SP-3
    # The corrected (plant-grain) gate's measured scope, at full magnitude.
    from market_sim.data.fleet.offer_surfaces import _plant_unit_physics

    plant_md, plant_mr = _plant_unit_physics(fleet, prefixes)
    eligible = {p for p, md in plant_md.items() if md <= FASTSTART_POOL_MIN_DOWN_HOURS}
    excluded = sorted(set(plant_md) - eligible)
    rec["SP3_n_ct_plants"] = len(prefixes)
    rec["SP3_n_plants_eligible"] = len(eligible)
    rec["SP3_n_plants_excluded"] = len(excluded)
    rec["SP3_excluded_plants"] = [
        {"prefix": p, "min_down_h": plant_md[p], "min_run_h": plant_mr[p]}
        for p in excluded
    ]
    rec["SP3_plant_min_down_histogram"] = {
        str(v): sum(1 for x in plant_md.values() if x == v)
        for v in sorted(set(plant_md.values()))
    }
    rec["SP3_n_bid_rows_eligible"] = sum(
        1
        for p in eligible
        for g in prefixes[p]
        if fleet[g].unit_id.rpartition("_")[2].startswith(("econ", "peak"))
    )

    # SP-3b — the SP-1 divergence, measured WHERE THIS GATE READS. Descriptive
    # (it is not an assertion and moves no bound): does the ercot-176
    # max-over-rows read reach the same ELIGIBILITY SET over the pool's own row
    # universe as the stamped read? This is the fact a successor round needs,
    # because it says whether the two candidate constructions are separable on
    # the object at all.
    row_md_by_pref = {
        p: max(float(getattr(fleet[g], "min_down_hours", 0) or 0) for g in rows)
        for p, rows in prefixes.items()
    }
    eligible_rowread = {
        p for p, md in row_md_by_pref.items() if md <= FASTSTART_POOL_MIN_DOWN_HOURS
    }
    rec["SP3b_ct_prefixes_where_reads_differ"] = sorted(
        p for p in prefixes if row_md_by_pref[p] != plant_md[p]
    )
    rec["SP3b_same_eligibility_set"] = eligible_rowread == eligible
    rec["SP3b_n_eligible_rowread"] = len(eligible_rowread)

    # ---------------------------------------------------------------- SP-4
    # Inertness adjudication: is the armed surface array-equal to the control's?
    off = build_ercot_faststart_pool_markup(fa, fleet, mc_base, nl, cfg_off, year)
    cfg_on = _armed(cfg_off, ercot_faststart_pool_plant_physics=True)
    on = build_ercot_faststart_pool_markup(fa, fleet, mc_base, nl, cfg_on, year)
    rec["SP4_control_is_none"] = off is None
    rec["SP4_armed_is_none"] = on is None
    if off is None or on is None:
        rec["SP4_arrays_equal"] = off is None and on is None
        rec["SP4_n_rowhours_changed"] = None
        rec["SP4_max_abs_markup_delta"] = None
    else:
        m_off, k_off = off
        m_on, k_on = on
        rec["SP4_arrays_equal"] = bool(
            np.array_equal(m_off, m_on) and np.array_equal(k_off, k_on)
        )
        rec["SP4_n_rowhours_changed"] = int(
            np.count_nonzero(m_off != m_on) + np.count_nonzero(k_off != k_on)
        )
        rec["SP4_max_abs_markup_delta"] = float(np.abs(m_on - m_off).max())
        rec["SP4_n_rows_priced_control"] = int(k_off.any(axis=1).sum())
        rec["SP4_n_rows_priced_armed"] = int(k_on.any(axis=1).sum())

    # ---------------------------------------------------------------- SP-5
    # The source-side stamp moves nothing, proved structurally rather than by
    # a second array build: a field NOTHING reads cannot move an array. So
    # (a) FleetArrays carries no attribute of either name, and (b) the only
    # source references anywhere under src/ outside the model declaration
    # (fleet/__init__.py) and the writer (fleet/assembly.py) are inside
    # offer_surfaces._plant_unit_physics — the licensing read this session
    # adds. Any third reader would be an undeclared consumer and fails SP-5.
    rec["SP5_fleetarrays_has_no_such_field"] = not any(
        hasattr(fa, n) for n in ("plant_min_run_hours", "plant_min_down_hours")
    )
    readers = sorted(
        str(p.relative_to(REPO))
        for p in (REPO / "src").rglob("*.py")
        if "plant_min_down_hours" in p.read_text()
        or "plant_min_run_hours" in p.read_text()
    )
    rec["SP5_source_readers"] = readers
    rec["SP5_readers_as_declared"] = readers == [
        "src/market_sim/data/fleet/__init__.py",
        "src/market_sim/data/fleet/assembly.py",
        "src/market_sim/data/fleet/offer_surfaces.py",
    ]
    rec["SP5_fleetarrays_unmoved"] = bool(
        rec["SP5_fleetarrays_has_no_such_field"] and rec["SP5_readers_as_declared"]
    )
    return rec


def main() -> None:
    """Run every year's seam proof and write the JSON record."""
    years = [run_year(y) for y in YEARS]
    checks = (
        "SP1_stamp_equals_ercot176_read",
        "SP2_row_gate_is_vacuous",
        "SP5_fleetarrays_unmoved",
    )
    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot186_grain_seamproof.py",
            "precommit": "docs/PRECOMMIT-ercot186-rule18-grain-2026-08-10.md",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "note": (
                "SP-3 is a MEASUREMENT reported at full magnitude, not an "
                "assertion; SP-4 adjudicates inertness (prediction P-2). No "
                "bound moves in response to either."
            ),
        },
        "years": {str(r["year"]): r for r in years},
        "ALL_ASSERTIONS_PASS": all(bool(r[c]) for r in years for c in checks),
        "ARM_IS_INERT": all(bool(r["SP4_arrays_equal"]) for r in years),
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "years"}, indent=2))
    for r in years:
        print(
            f"  {r['year']}: CT plants {r['SP3_n_ct_plants']} -> eligible "
            f"{r['SP3_n_plants_eligible']}, excluded {r['SP3_n_plants_excluded']}; "
            f"row-grain rejections {r['SP2_n_rejected_by_row_grain_gate']}; "
            f"armed==control {r['SP4_arrays_equal']}"
        )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
