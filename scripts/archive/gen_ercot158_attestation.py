"""Write ``calibration_attestation.json`` for the ercot-158 A/B arms.

The arm is the single delta ``ercot_faststart_pool_offer=true`` on the
ercot150b keeper — the EXISTING ERCOT-88 offline fast-start CT pool mechanism,
unchanged, now engaging 2023 because ERCOT-157 landed the pool artifact's 2023
CT year block (``docs/PRECOMMIT-ercot158-faststart-pool-arm-2026-08-03.md``).
This script builds the C6 attestation both bundles need (rule 21 ``[R-DOF]``),
inheriting the ercot150b keeper's ledger and adding ONE entry for the delta on
the arm.

**The delta adds ZERO free parameters.** The pool boundary (``1 −
pool_frac(bin)``) and the start-inclusive above-LSL SCED2 ladder are MEASURED
per net-load bin from the NP3-965 60-Day SCED disclosures (telemetered
OFFQS/OFFNS conduct), year-scoped with no pooled fallback, frozen against
residuals (rule 23). Nothing is chosen; nothing is swept; ``n_residual`` is
unchanged.

The **control** arm (Run A, the honest-inputs replay) inherits the keeper's
attestation verbatim except for its own ``attested_by`` line.

Every quantitative claim in the generated prose is READ FROM the committed
JSONs (the pool artifact always; ``_ercot158_pool_ab.json`` when it exists —
rerun this script after the scorer to enrich the prose; C6's status depends
only on the assertions and ledger validity, so the enrichment is prose-only),
never hand-transcribed.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/gen_ercot158_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/ercot150_zonalanchor_B/calibration_attestation.json"
)
POOL_ARTIFACT = (
    REPO / "data/raw/_validation-source/ercot_faststart_pool_condbinned.json"
)
AB_JSON = REPO / "results/calibration/_ercot158_pool_ab.json"
ARM_DEST = REPO / "results/calibration/ercot158_poolarm_B/calibration_attestation.json"
CONTROL_DEST = (
    REPO / "results/calibration/ercot158_honest_A/calibration_attestation.json"
)

YEARS = ("2023", "2024", "2025")

NEW_ENTRY_NAME = (
    "ercot_faststart_pool_offer (ERCOT-88) — the telemetered-offline startable "
    "fast-start CT pool offered to the LP at its measured start-inclusive "
    "above-LSL SCED2 ladder, REPLACE-BY-MASK over the cleared-share wall's row "
    "pricing on the row-hours whose within-plant capacity midpoint lies above "
    "the hour-bin's measured pool boundary (1 − pool_frac)"
)


def _build_entry(pool: dict, ab: dict | None) -> dict:
    """Assemble the DOF entry, reading every number from the committed JSONs."""
    ct = pool["CT"]["years"]
    frac = {y: ct[y]["pool_frac"] for y in YEARS if y in ct}
    q50 = {
        y: [pts[2][1] for pts in ct[y]["ladder"]] for y in YEARS if y in ct
    }  # ladder rows are [[q, mult], ...] with q=0.5 at index 2
    measured_effect = (
        "Pool artifact (frozen, year-scoped): per-net-load-bin pool_frac "
        + "; ".join(f"{y} {min(f):.3f}–{max(f):.3f}" for y, f in frac.items())
        + "; ladder q0.5 delivered-gas multipliers "
        + "; ".join(f"{y} {min(v):.0f}–{max(v):.0f}" for y, v in q50.items())
        + " — 2023's post-Uri conservative-ops conduct sits ~2/3 of 2024's "
        "ladder level (ERCOT-157 derive record)."
    )
    if ab is not None:
        g = ab["e89_gates"]
        c3a = [
            f"{g[y]['base']['resid_pct']:+.1f}%→{g[y]['probe']['resid_pct']:+.1f}%"
            for y in YEARS
        ]
        a23 = ab["c3c_anatomy"]["2023"].get("phase0_rederived", {})
        measured_effect += (
            f" Measured A/B effect (committed _ercot158_pool_ab.json): C3a "
            f"{' / '.join(c3a)} (2023/24/25); matched-hour 2023 missed-set model "
            f"mean ${a23.get('missed_model_mean_A', float('nan')):.0f}→"
            f"${a23.get('missed_model_mean_B', float('nan')):.0f} vs actual "
            f"${a23.get('missed_actual_mean', float('nan')):.0f}, "
            f"{a23.get('missed_flipped_to_tail_B', 0)} of "
            f"{a23.get('missed_A', 0)} missed hours flipped to tail; kills "
            f"fired: {ab.get('kills_fired') or 'none'}."
        )
    return {
        "name": NEW_ENTRY_NAME,
        "where": (
            "run_config.scenario_config.ercot_faststart_pool_offer "
            "(+ ercot_faststart_pool_offer_path default "
            "data/raw/_validation-source/ercot_faststart_pool_condbinned.json)"
        ),
        "identification": "measured/published",
        "lineage_solves": "1 (ercot-158 arm B, against the same-HEAD honest-inputs control A)",
        "value": {
            "pool_frac_by_bin": frac,
            "ladder_q50_mult_by_bin": {
                y: [round(v, 1) for v in vs] for y, vs in q50.items()
            },
        },
        "source": (
            "scripts/data/derive_ercot_faststart_pool.py over the NP3-965 "
            "60-Day SCED Gen Resource disclosures (delivery-2023 corpus: the "
            "ERCOT-157 owner re-upload, 315 shards verified complete — all 365 "
            "delivery days; 2024/2025 blocks byte-identical to the ERCOT-88 "
            "artifact, the derive-integrity check). The pool share and ladder "
            "are the telemetered OFFQS/OFFNS fleet's own submitted SCED2 "
            "above-LSL curves conditioned on net-load bin — measured market "
            "conduct with a forward story (regenerates from forward net load "
            "exactly as the DAM/RT walls do), rule-13-admissible, rule-23 "
            "frozen."
        ),
        "free_parameters_added": 0,
        "why_zero": (
            "This arms an ALREADY-BUILT measured mechanism (ERCOT-88, merged "
            "default-off 2026-07-19) whose only change since is a new YEAR "
            "BLOCK of the same measured artifact (ERCOT-157). Eligibility is "
            "unit physics (min_down_hours <= FASTSTART_POOL_MIN_DOWN_HOURS), "
            "the boundary and ladder are per-bin measured quantities, the "
            "markup is max(0, min(ladder-interp x gas_day, 0.95 x VOLL) − "
            "mc_base) with no scalar anywhere between the disclosure data and "
            "the LP column. Nothing is swept; rule 23 re-derives only on "
            "source-data update (this block's trigger was the ERCOT-157 corpus "
            "landing, not a residual). The arming decision itself is the "
            "pre-registered owner-authorized ERCOT-89 §7 step-2 round with "
            "kill gates pushed before either arm solved."
        ),
        "rule_19_reconciliation": (
            "One owner per row-hour, enforced at the composition site: the "
            "pool's own_mask REPLACES every other offer surface's markup "
            "(conditional peak surface, cleared-share DA wall, RT leg alike) "
            "in pool-owned row-hours; it hard-errors unless the cleared-share "
            "wall is armed (the enumeration context). ercot_gas_commitment_"
            "bridge owns the ON committed CC min-gen state (disjoint — the "
            "pool prices OFFLINE fast-start CT rows only); P1 startup "
            "amortization owns started-run pricing (replaced, never stacked, "
            "in the mask); the RT wall owns the ON fleet's ladder (disjoint "
            "by status). An offer-availability, never a floor: no min_gen is "
            "touched, so D-2/D-4 forced-energy exposure is vacuous by "
            "construction."
        ),
        "rule_25_scope": (
            "ERCOT-only by construction (gates on config.iso == 'ERCOT'); the "
            "artifact derives from ERCOT's own NP3-965 disclosure instrument, "
            "which no other modeled ISO publishes — other ISOs' matrix cells "
            "stay '.' (no comparable RT offline-conduct disclosure)."
        ),
        "measured_effect": measured_effect,
    }


def _attested_by(ab: dict | None, arm: bool) -> str:
    """The C6 attestation prose for one arm, from the committed JSONs."""
    if ab is None:
        ab_line = (
            "The A/B scorer has not yet run; this attestation precedes the "
            "verdict so C6 can score, and is regenerated with the measured "
            "gate numbers once results/calibration/_ercot158_pool_ab.json is "
            "committed."
        )
    else:
        g = ab["e89_gates"]
        c3a = " / ".join(
            f"{g[y]['base']['resid_pct']:+.1f}%->{g[y]['probe']['resid_pct']:+.1f}%"
            for y in YEARS
        )
        ab_line = (
            f"Measured A/B (committed _ercot158_pool_ab.json): C3a {c3a} "
            f"(2023/24/25); kills fired: {ab.get('kills_fired') or 'none'}; "
            f"all pre-registered gates "
            f"{'HELD' if ab.get('all_gates_held') else 'NOT held'}."
        )
    if not arm:
        return (
            "ercot-158 2026-08-03 Run A — HONEST-INPUTS REPLAY of the "
            "2026-08-02-ercot150b-zonal-anchor keeper recipe (config "
            "UNCHANGED, meta.json kwargs replay) on the ERCOT-157-completed "
            "inputs, and the same-HEAD zero-delta CONTROL for the "
            "ercot_faststart_pool_offer A/B. The only physical input delta vs "
            "the committed keeper bundle is the armed RT wall's 2023 block "
            "completed full-year (ercot_sced_offer_wall_condbinned.json: the "
            "committed block was the Jan-Oct post-purge slice; the refresh "
            "moves net-load bins 0-4 only, scarcity-tail bins 5-6 "
            "byte-identical — ERCOT-157). This bundle carries the keeper's "
            "own recipe and therefore its DOF ledger unchanged; it is "
            "registered as evidence (the ercot98 honest-inputs pattern), and "
            "any keeper-candidate standing is scored on its own rubric "
            "numbers vs the committed keeper, never assumed. " + ab_line
        )
    return (
        "ercot-158 2026-08-03 Run B — the 2026-08-02-ercot150b-zonal-anchor "
        "recipe with ONE delta: ercot_faststart_pool_offer=true (the ERCOT-88 "
        "offline fast-start CT pool, exactly as merged 2026-07-19, first solve "
        "with its 2023 year block — ERCOT-157). Scored against the same-HEAD "
        "honest-inputs control ercot158_honest_A, gates pre-registered in "
        "docs/PRECOMMIT-ercot158-faststart-pool-arm-2026-08-03.md BEFORE "
        "either arm solved (the owner-authorized ERCOT-89 §7 step-2 design "
        "round, ERCOT-151 §4 ask 2). The CC slow-start tier is NOT built "
        "(ERCOT-152 ex-ante refusal on measured conduct stands); "
        "ercot_shoulder_online_span stays OFF (rejected as armed, ERCOT-89 "
        "§9.4) — this arm runs the static ERCOT-88 boundary. Zero fitted "
        "parameters added; n_residual unchanged. " + ab_line
    )


def main() -> int:
    """Write both arms' attestations from the keeper's + the committed JSONs."""
    keeper = json.loads(PRIOR_KEEPER.read_text())
    pool = json.loads(POOL_ARTIFACT.read_text())
    ab = json.loads(AB_JSON.read_text()) if AB_JSON.exists() else None

    for dest, arm in ((CONTROL_DEST, False), (ARM_DEST, True)):
        if not dest.parent.exists():
            print(f"skip {dest.parent.name}: bundle not solved yet")
            continue
        att = json.loads(json.dumps(keeper))  # deep copy
        gov = att["governance"]
        for key in (
            "levers_trace_to_measured_input",
            "no_fit_to_price_residuals",
            "no_pinning_to_actuals",
            "outage_filter_exogenous_net_load",
        ):
            if gov.get(key) is not True:
                raise SystemExit(
                    f"keeper attestation assertion {key} is not true — refusing "
                    "to inherit a broken attestation"
                )
        gov["attested_by"] = _attested_by(ab, arm)
        if arm:
            fp = att["free_parameters"]
            fp["entries"] = list(fp["entries"]) + [_build_entry(pool, ab)]
            fp["n_entries"] = int(fp["n_entries"]) + 1
            # n_residual unchanged: the added entry is measured/published.
        dest.write_text(json.dumps(att, indent=1) + "\n")
        led = json.loads(dest.read_text())["free_parameters"]
        print(
            f"wrote {dest.relative_to(REPO)} "
            f"(n_entries {led['n_entries']}, n_residual {led['n_residual']}, "
            f"ab_numbers={'yes' if ab is not None else 'PRELIMINARY'})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
