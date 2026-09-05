"""Emit the nyiso-159 A/B arms' ``calibration_attestation.json`` (C6 governance gate).

nyiso-159 is the zonal-loss-surface test chartered by
``results/calibration/PREREG-nyiso159-zonal-loss-surface-2026-08-30.md`` on the
phase-0 MATERIAL verdict
(``FINDING-nyiso159-loss-surface-phase0-2026-08-30.md``). Two bundles:

* **Control** (``nyiso159_lossctl_A``) — the committed keeper
  ``2026-08-30-nyiso-157-par-attribution`` recipe replayed ZERO-DELTA at HEAD;
  ledger carried VERBATIM.
* **Loss arm** (``nyiso159_lossarm_B``) — + ``nyiso_zonal_loss_surface``: one
  DOF entry appended (the measured per-zone monthly delivery-factor deviation
  surface, NYISO's own posted RT LBMP components; ZERO scalars;
  ``n_residual`` UNCHANGED — PREREG §2).

THE GENERATOR IS THE SOURCE OF TRUTH: editing the emitted JSON by hand is
reverted by the next run of this script.

Usage:
    python scripts/gen_nyiso159_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results" / "calibration" / "nyiso157_pararm_B"
CONTROL = REPO / "results" / "calibration" / "nyiso159_lossctl_A"
ARM = REPO / "results" / "calibration" / "nyiso159_lossarm_B"

PREREG = "results/calibration/PREREG-nyiso159-zonal-loss-surface-2026-08-30.md"

CONTROL_ATTESTED_BY = (
    "session nyiso-159 (2026-08-30). ZERO-DELTA CONTROL of the loss-surface "
    f"A/B ({PREREG}, pushed and blob-verified before any solve): the "
    "committed keeper 2026-08-30-nyiso-157-par-attribution recipe replayed "
    "unchanged at HEAD via scripts/replay_keeper.py. No lever, no parameter, "
    "no mechanism change — the ledger is the keeper's own, carried verbatim. "
    "K6 PASSES at zero distance: C3a +1.00/-1.96/-12.01 vs the committed "
    "+1.0/-2.0/-12.0, and the control is BIT-IDENTICAL to the committed "
    "keeper in zonal prices in all three years (max |dprice| 0.0)."
)

ARM_ATTESTED_BY = (
    "session nyiso-159 (2026-08-30). LOSS ARM of the A/B "
    f"({PREREG}), against same-HEAD control 2026-08-30-nyiso-159-loss-"
    "control: --set nyiso_zonal_loss_surface=true — the four internal chain "
    "links split into one-way loss pairs and NYISO's own measured monthly "
    "delivery-factor deviation surface (dev = sum(MCL)/sum(E) on the posted "
    "RT LBMP components, the frozen MISO/PJM/CAISO estimator on NYISO's own "
    "data, rule 25) entering the energy balance as receiving-side loss "
    "fractions. ZERO free parameters: every number is a published component "
    "ratio; the derive's offline acceptance held 12/12 pair-years in "
    "[0.5x,1.5x] (ratios 0.93-1.02x) BEFORE any solve was spent. Gates "
    "(_nyiso159_loss_ab_gates.json): K1/K2/K6/ADVERSE PASS; P1 10/12 "
    "pair-years in band — the >=10 bar — with ONE outer miss at 0.23x vs "
    "the 0.25 floor on the smallest-denominator pair (NYC->LI 2024, "
    "measured dMCL $0.19, the pair where the measured July gradient flip "
    "clamps and the 1,650 MW cable congestion dominates); LOYO breaks only "
    "through that same cell. W-K3d fires on magnitude (|arm-control| UW "
    "-1.22/-1.71 $ in 2024/2025 vs the 0.75 bound) and is adjudicated "
    "against its own premise by the actual-anchored decomposition "
    "(WK3d_actual_anchor in the gates JSON): the arm moves UW TOWARD the "
    "measured relative gradient in both years (UW-below-LW 6.6->10.5% vs "
    "measured 13.3% in 2024; 8.8->12.2% vs measured 16.4% in 2025) and "
    "2024's absolute UW error IMPROVES ($1.86->$0.64); the gate's premise "
    "(UW's dual set by its own balance, so any move is relocation) is "
    "refuted by the measurement — in unbound hours the lossless LP's "
    "east-west parity WAS the bias. REPORTED AT FULL MAGNITUDE: C3a "
    "+1.00->+2.35 / -1.96->-1.21 / -12.01->-11.48; C3b-2025 NRMSE improves "
    "0.2268->0.2224 (control basis); C3c deltas only (nyiso-137 clock "
    "caveat). The 2025 uplift (+0.36 LW) is BELOW the phase-0 upper bound "
    "(+1.5-2.5) because the surface moves west zones down as it moves "
    "downstate up — the LW-weighted net is smaller than the downstate-only "
    "bound; the winter/summer faces stay Leg-2 / ledgered-C3c work exactly "
    "as nyiso-158 routed them."
)

LOSS_DOF_ENTRY = {
    "name": "nyiso_zonal_loss_surface",
    "where": (
        "ScenarioConfig.nyiso_zonal_loss_surface -> "
        "interchange.nyiso.apply_nyiso_zonal_loss_links / "
        "build_nyiso_link_loss <- data.loss_surface.load_zone_month_deviation "
        "<- data/raw/iso-specific-transmission/NYISO_loss_surface.csv "
        "(scripts/data/derive_nyiso_loss_surface.py, frozen rule 23)"
    ),
    "identification": "measured",
    "lineage_solves": (
        "nyiso-159 phase-0 (2026-08-30, committed-artifacts measurement, "
        "FINDING-nyiso159-loss-surface-phase0-2026-08-30.md); offline "
        "acceptance 12/12 pair-years pre-solve; nyiso-159 A/B "
        "(2026-08-30, _nyiso159_loss_ab_gates.json)"
    ),
    "value": {
        "n_scalars": 0,
        "note": (
            "Per-zone monthly delivery-factor deviations dev_z,m = "
            "sum(MCL_z)/sum(E) from NYISO's own posted RT LBMP components "
            "(LBMP = E + MCL - MCC, MST §17.1/Manual 12), model-zone "
            "aggregation = the scoring actuals' own simple-mean crosswalk; "
            "per-year rows for backcast train years (the CEMS-rate "
            "admissibility class, rule 13 — regenerates for any year from "
            "the same public feed and responds to changed grid conditions), "
            "pooled year=0 rows as the forecast-mode forward analogue. The "
            "eps tiebreak (1e-3 $/MWh) is the rule-9 storage-epsilon "
            "numerical device, identical in construction and value to the "
            "PJM/CAISO twins, declared in NYISO's own module (rule 25)."
        ),
    },
}


def _emit(bundle: Path, attested_by: str, extra_entries: list[dict]) -> None:
    """Write one bundle's attestation from the keeper's committed one."""
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    doc = json.loads(json.dumps(base))
    doc["governance"]["attested_by"] = attested_by
    doc["governance"]["note"] = (
        "nyiso-159 chain (2026-08-30): the nyiso-157 keeper recipe, plus "
        "(loss arm only) the measured zonal loss surface — see attested_by "
        "for this bundle's exact role and evidence. The prior keeper "
        "lineage's mechanism notes live in their own bundles' attestations "
        "and the keeper shard's promotion-note chain."
    )
    fp = doc["free_parameters"]
    names = [e.get("name") for e in fp["entries"]]
    for entry in extra_entries:
        if entry["name"] not in names:
            fp["entries"].append(entry)
    fp["n_entries"] = len(fp["entries"])
    # n_residual UNCHANGED: the appended entry carries zero scalars and a
    # measured identification (rule 21 [R-DOF]; PREREG-nyiso159 §2 promises
    # exactly this — n_residual stays at the keeper's value).
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(doc, indent=1) + "\n"
    )
    print(
        f"wrote {bundle / 'calibration_attestation.json'} "
        f"(n_entries {fp['n_entries']}, n_residual {fp['n_residual']})"
    )


def main() -> None:
    """Write the two nyiso-159 bundles' attestations."""
    _emit(CONTROL, CONTROL_ATTESTED_BY, [])
    _emit(ARM, ARM_ATTESTED_BY, [LOSS_DOF_ENTRY])


if __name__ == "__main__":
    main()
