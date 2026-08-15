"""Write ``calibration_attestation.json`` for the neiso-70 CT heat-rate keeper.

Seeds from the outgoing ``neiso61_netrev_margin`` keeper's attestation and
applies exactly the changes neiso-70 earns (precedent:
``scripts/gen_miso98_attestation.py``):

1. **Governance block** re-attested to this session, naming the single delta
   (``measured_ct_heat_rates=true``) and the same-HEAD control it was scored
   against.
2. **Exceptions carried VERBATIM.** C3c is BIT-IDENTICAL between control and
   arm — model 0 tail hours in both, all three years — so the three
   ``price_tail`` ledger entries and the other carried exceptions transfer
   unchanged. No new disposition is created and no ledger slot is spent
   (the caiso-147 / owner-commit ``82bd346`` precedent).
3. **DOF ledger** gains one entry for the measured CT loaded heat rates,
   identification ``measured`` — so ``n_entries`` rises by one while
   ``n_residual`` is UNCHANGED at 5. The arm introduces **zero** fitted
   parameters (rule 21 ``[R-DOF]`` / rule 24 ``[R-REGISTRY]``).

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_neiso70_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

SRC = REPO / "results/calibration/neiso61_netrev_margin/calibration_attestation.json"
DST = REPO / "results/calibration/neiso70_ctheatrate_B/calibration_attestation.json"

ATTESTED_BY = (
    "neiso-70 heat-rate provenance session 2026-07-31 (branch "
    "claude/neiso-70-heat-rate-provenance-xg9qge): the neiso-61 keeper recipe + "
    "ONE structural delta (measured_ct_heat_rates=true) — the eGRID PLANT-AVERAGE "
    "ANNUAL heat rate replaced on CT_PEAKER rows by the CAMPD-measured LOADED "
    "rate, on the same NET basis. Zero fitted scalars: the artifact is derived "
    "(scripts/data/derive_campd_ct_heat_rates.py --iso NEISO, rule 23 "
    "[R-FROZEN-DERIVE]), its screen constants (0.8 x p95, >=50 loaded hours, "
    "physical band [6.0, 25.0]) are the committed shipped values, and the "
    "gross-to-net conversion uses the SAME committed parasitic_load_factors "
    "artifact the benchmark's net actual uses — so the derived rate and the "
    "actual it is scored against share one basis convention. Scored against a "
    "SAME-HEAD zero-delta control (2026-07-31-neiso-70-control), never against "
    "the committed keeper, whose git_sha eede1c4 is no longer in the repo "
    "(the neiso-69 drift precedent). Pre-registered before any solve: "
    "results/calibration/PREREG-neiso70-heat-rate-provenance-2026-07-31.md "
    "(commit 20ce479)."
)

NOTE = (
    "neiso-70 = the neiso-61 keeper recipe with measured CT loaded heat rates "
    "armed. EVERY pre-registered gate PASSES and there are ZERO status changes "
    "across all 70 scored records vs the same-HEAD control — C1 stays all 12/12 "
    "/ free 8/8 and C3c is BIT-IDENTICAL (model 0h vs RT 15/8/20h), so the three "
    "price_tail ledger entries below carry over verbatim and no new ledger slot "
    "is spent. THE STRUCTURAL DELIVERABLE: the D-2 CT_PEAKER reliability_floor "
    "forced share COLLAPSES 0.3958 -> 0.2013 (2023), 0.2735 -> 0.0736 (2024), "
    "0.0680 -> 0.0272 (2025) — correctly priced, the class clears ECONOMICALLY "
    "instead of leaning on its commitment floor, i.e. the floor stops being "
    "load-bearing. This is the MISO-107 result in reverse (there, arming the same "
    "mechanism made MISO's CT floor MORE load-bearing because its CTs had been "
    "carrying combined-cycle heat rates). C1 CT_PEAKER absolute error improves in "
    "BOTH scored years: 0.282 -> 0.156 TWh (2023) and 0.292 -> 0.177 (2024). "
    "REPORTED, NOT GATED, and disclosed because it is the one number that moved "
    "adversely on the repriced class: 2025 CT_PEAKER D-1 cv_ratio 0.521 -> 0.288, "
    "below the 0.50 D-1 threshold — this is NOT a broken protective gate because "
    "C7 shape is SKIPPED for NEISO in keeper, control and arm alike, and "
    "profile_r stays far above its floor (0.930->0.965, 0.982->0.976, "
    "0.976->0.976). CT_PEAKER is 0.19-1.0 % of ISO load, under rule 20's 2 % "
    "materiality line, so its D-2 share is a reported diagnostic, not a gate; "
    "C8 forced_share PASSES in both arms. Artifact reach: 8/8 rows applied, ZERO "
    "excluded by the physical band, 75.6 % of class capacity but 100.0 % of the "
    "class's own metered CAMPD CT energy; adverse selection is PRESENT and stated "
    "(covered cap-wt incumbent HR 10.208 vs uncovered 11.830), mitigated but not "
    "erased by every uncovered plant metering zero CT energy. Direction is "
    "NEISO's OWN — two-sided (6 plants/817 MW cheaper, 2/94 MW dearer), cap-wt "
    "-0.579 MMBtu/MWh (-5.7 %) — matching no precedent ISO's pattern (rule 25 "
    "[R-ISO-SCOPE]: nothing transferred from CAISO/PJM/NYISO/MISO)."
)

DOF_ENTRY = {
    "name": "measured_ct_heat_rates[NEISO]",
    "where": "run_config.scenario_config.measured_ct_heat_rates + "
    "data/raw/_processed-legacy/campd_ct_heat_rates_NEISO.csv",
    "identification": "measured",
    "lineage_solves": "0 residual solves — derived from EPA CAMPD unit-level "
    "hourly grossLoad/heatInput, never swept against a residual",
    "value": {
        "rows_applied": 8,
        "rows_excluded_by_physical_band": 0,
        "class_capacity_covered_pct": 75.6,
        "class_metered_energy_covered_pct": 100.0,
        "cap_weighted_delta_mmbtu_per_mwh": -0.579,
        "screen_constants": {
            "loaded_frac_of_p95": 0.8,
            "min_loaded_hours": 50,
            "physical_band_mmbtu_per_mwh": [6.0, 25.0],
        },
        "net_basis_source": "parasitic_load_factors.parquet (the committed map "
        "the benchmark's net actual uses)",
    },
    "note": "A unit's loaded heat rate is a physical characteristic of the "
    "machine — rule 13 [R-MEASURED] admissible as an INPUT (it regenerates for a "
    "forward year from the same pipeline and responds to changed conditions: a "
    "retrofit moves it, a new unit carries its design rate). It is NOT a measured "
    "outcome fed back to close a residual. Per rule 23 [R-FROZEN-DERIVE] it "
    "re-derives ONLY when CAMPD publishes new or revised vintages, and that "
    "commit must cite the data change.",
}


def main() -> int:
    """Write the neiso-70 attestation from the neiso-61 keeper's."""
    att = json.loads(SRC.read_text())

    att["governance"]["attested_by"] = ATTESTED_BY
    att["governance"]["note"] = NOTE

    dof = att["free_parameters"]
    names = {e["name"] for e in dof["entries"]}
    if DOF_ENTRY["name"] not in names:
        dof["entries"].append(DOF_ENTRY)
    dof["n_entries"] = len(dof["entries"])
    # n_residual is UNCHANGED: this arm adds a MEASURED entry, not a fitted one.
    dof["n_residual"] = sum(
        1 for e in dof["entries"] if e["identification"] == "residual"
    )

    DST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DST.relative_to(REPO)}")
    print(f"  DOF entries {dof['n_entries']} (residual {dof['n_residual']})")
    print(f"  exceptions carried: {len(att['exceptions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
