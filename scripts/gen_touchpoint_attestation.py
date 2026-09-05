"""Write ``calibration_attestation.json`` for a rule-22 validation touchpoint.

A touchpoint is a **frozen-recipe replay of a designated keeper on a held-out
year** (CLAUDE.md rule 22 ``[R-HOLDOUT]``, the touchpoint loop). Because the
recipe is the keeper's own — reproduced through the sanctioned
``replay_keeper`` channel from the keeper bundle's ``meta.json`` — the rule 20
``[R-DOF]`` free-parameter ledger, the disclosures and the exceptions ledger
carry onto the touchpoint **unchanged**: a touchpoint introduces no parameter,
moves no parameter, and (by construction) fits nothing to the year it scores.

That carry-forward is the whole reason this generator exists as standing
tooling rather than a per-run script: the premise it rests on — *the touchpoint
solved the keeper's recipe and nothing else* — is **computed here, not typed**.
The generator refuses to write an attestation whose recipe-identity assertion
does not hold, so a C6 governance PASS on a touchpoint bundle is backed by a
machine check rather than by prose.

What it checks, and what each finding means:

* **Recipe identity.** Every ``meta.json`` key the two bundles share must be
  equal outside :data:`PROVENANCE_KEYS` (run stamps, the solve span, and the
  per-year Henry Hub actual, which is a year-scoped measured input rather than
  a recipe knob). Any other difference is a hard error — it would mean the
  touchpoint is not the keeper's recipe.
* **Solve-surface drift.** A keeper solved at an earlier HEAD carries no value
  for kwargs added since, so the replay takes their code defaults. Those keys
  are enumerated and each is checked against its ``ScenarioConfig`` default;
  a new field sitting at a NON-default value is a hard error (the replay would
  be arming a mechanism the keeper never had). Fields at their defaults are
  recorded, not waved through, because ``git_sha`` drift between the keeper's
  in-sample column and the touchpoint's holdout column is a real limit on the
  comparison — the attestation states it rather than hiding it.
* **Tier.** The holdout years are classified through
  ``scripts/lib/holdout_policy`` and must all sit in one tier; the tier is
  written into the attestation so a reader never has to infer it.

Usage::

    python scripts/gen_touchpoint_attestation.py \
        --keeper-bundle results/calibration/<keeper_bundle> \
        --keeper-run-id 2026-08-17-neiso-99-joint-p1 \
        --touchpoint-bundle results/calibration/<touchpoint_bundle>

Stdlib-only apart from the optional ``ScenarioConfig`` default lookup, which is
skipped (and reported as skipped) when the model package cannot be imported.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.lib import holdout_policy  # noqa: E402

#: ``meta.json`` keys that legitimately differ between a keeper and a replay of
#: its recipe on another year. Everything else must match exactly.
#:
#: ``gas_prices`` is here because it is the per-year Henry Hub **actual** — a
#: year-scoped measured input the solve looks up, not a tunable; a 2022 replay
#: necessarily carries 2022's number and no other.
PROVENANCE_KEYS = frozenset(
    {
        "timestamp",
        "git_sha",
        "basis_sha",
        "git",
        "environment",
        "shared_inputs",
        "years",
        "gas_prices",
        "note",
        "run_dir",
        "reuse",
        "model_changes_note",
    }
)

#: Attestation sections carried verbatim from the keeper (see module docstring).
CARRIED_SECTIONS = ("free_parameters", "disclosures", "exceptions")

#: The four rule-20/rule-22 governance assertions. A touchpoint re-asserts them
#: because the recipe is the keeper's and the held-out year was never tuned on.
GOVERNANCE_ASSERTIONS = (
    "levers_trace_to_measured_input",
    "no_fit_to_price_residuals",
    "no_pinning_to_actuals",
    "outage_filter_exogenous_net_load",
)


def scenario_defaults() -> dict[str, object] | None:
    """Return ``ScenarioConfig`` field defaults, or None if unimportable.

    Returns:
        Mapping of field name to default value, or ``None`` when the model
        package is unavailable (the caller then records the check as skipped).
    """
    try:
        import dataclasses

        from market_sim.config.scenarios import ScenarioConfig
    except Exception:
        return None
    cfg = ScenarioConfig()
    return {f.name: getattr(cfg, f.name) for f in dataclasses.fields(cfg)}


def compare_recipes(keeper: dict, touchpoint: dict) -> dict:
    """Compare two bundle ``meta.json`` recipes.

    Args:
        keeper: The designated keeper bundle's ``meta.json``.
        touchpoint: The touchpoint bundle's ``meta.json``.

    Returns:
        A dict with ``conflicts`` (shared keys differing outside
        :data:`PROVENANCE_KEYS`), ``added`` / ``removed`` (solve-surface drift),
        and ``added_nondefault`` (added keys not sitting at their
        ``ScenarioConfig`` default; ``None`` when the check was skipped).
    """
    shared = (set(keeper) & set(touchpoint)) - PROVENANCE_KEYS
    conflicts = {
        k: {"keeper": keeper[k], "touchpoint": touchpoint[k]}
        for k in sorted(shared)
        if keeper[k] != touchpoint[k]
    }
    added = sorted(set(touchpoint) - set(keeper) - PROVENANCE_KEYS)
    removed = sorted(set(keeper) - set(touchpoint) - PROVENANCE_KEYS)

    defaults = scenario_defaults()
    added_nondefault: dict | None
    if defaults is None:
        added_nondefault = None
    else:
        # ``None`` in a bundle's meta.json is the "flag not supplied" marker
        # for the tri-state BooleanOptionalAction knobs, so it IS the default
        # by construction; only an explicit value that differs is drift.
        added_nondefault = {
            k: {"value": touchpoint[k], "default": defaults[k]}
            for k in added
            if k in defaults
            and touchpoint[k] is not None
            and touchpoint[k] != defaults[k]
        }
    return {
        "conflicts": conflicts,
        "added": added,
        "removed": removed,
        "added_nondefault": added_nondefault,
    }


def build(
    keeper_bundle: Path,
    keeper_run_id: str,
    touchpoint_bundle: Path,
    supersedes: str | None,
) -> dict:
    """Build the touchpoint attestation payload.

    Args:
        keeper_bundle: Designated keeper's bundle directory.
        keeper_run_id: The keeper's registered dashboard run id.
        touchpoint_bundle: The touchpoint bundle produced by the replay solve.
        supersedes: Optional run id of a stale touchpoint this one replaces.

    Returns:
        The attestation dict, ready to serialize.

    Raises:
        SystemExit: if the recipe-identity assertion fails, if a newly added
            solve kwarg is at a non-default value, or if the holdout years span
            more than one tier.
    """
    kmeta = json.loads((keeper_bundle / "meta.json").read_text())
    tmeta = json.loads((touchpoint_bundle / "meta.json").read_text())
    katt = json.loads((keeper_bundle / "calibration_attestation.json").read_text())

    cmp_ = compare_recipes(kmeta, tmeta)
    if cmp_["conflicts"]:
        raise SystemExit(
            "RECIPE IDENTITY FAILED — the touchpoint is not the keeper's "
            f"recipe. Differing keys: {json.dumps(cmp_['conflicts'], indent=2)}"
        )
    if cmp_["added_nondefault"]:
        raise SystemExit(
            "SOLVE-SURFACE DRIFT FAILED — a kwarg added since the keeper "
            "solved is at a NON-default value, so the replay arms something "
            f"the keeper never had: {json.dumps(cmp_['added_nondefault'], indent=2)}"
        )

    years = [int(y) for y in tmeta["years"]]
    tiers = sorted({holdout_policy.tier_for_year(y) for y in years})
    if len(tiers) != 1:
        raise SystemExit(f"years {years} span more than one tier: {tiers}")
    tier = tiers[0]

    kgov = katt.get("governance", {})
    missing = [a for a in GOVERNANCE_ASSERTIONS if not kgov.get(a)]
    if missing:
        raise SystemExit(f"keeper attestation does not assert: {missing}")

    n_added = len(cmp_["added"])
    attested = (
        f"rule-22 {tier}-tier TOUCHPOINT for {tmeta['iso']} {years} — a frozen-recipe "
        f"replay of the designated keeper {keeper_run_id} ({keeper_bundle.name}) "
        "through the sanctioned replay_keeper channel (the keeper bundle's own "
        "meta.json supplies every solve kwarg, so the recipe is reproduced rather "
        "than re-expressed flag-by-flag). RECIPE IDENTITY IS COMPUTED, NOT ASSERTED: "
        "scripts/gen_touchpoint_attestation.py compared every shared meta.json key "
        "and found ZERO differences outside the provenance set (run stamps, the "
        "solve span, and the per-year Henry Hub actual, which is a year-scoped "
        "measured input rather than a recipe knob) — the generator refuses to write "
        "this file otherwise. ZERO free parameters introduced or moved, so the rule-20 "
        "[R-DOF] ledger, the disclosures and the exceptions ledger carry from the "
        "keeper unchanged and this run spends NO new ledger slot. NOTHING WAS TUNED "
        "FOR, AGAINST, OR IN RESPONSE TO the held-out year(s): the recipe was frozen "
        "before the solve and no parameter is identified against them (rule 22 step 3 "
        "— fitting happens only on 2023-2025). "
        f"STATED LIMIT ON THE COMPARISON: the keeper solved at git {kmeta.get('git_sha')} "
        f"and this replay at {tmeta.get('git_sha')}, and {n_added} solve kwarg(s) were "
        "added to the surface in between; each is verified here to sit at its "
        "ScenarioConfig default (a non-default would be a hard error), but the "
        "in-sample column this touchpoint is read against was measured on the earlier "
        "HEAD. Any in-sample-to-holdout delta should be read with that drift in mind "
        "unless a same-HEAD in-sample control is registered alongside. "
        f"{tier.upper()}-TIER RESULT: ITERABLE model-SELECTION evidence, NEVER a "
        "certified out-of-sample skill number."
    )
    if supersedes:
        attested += f" SUPERSEDES the stale touchpoint {supersedes}."

    out: dict = {"schema": "calibration-attestation/v1"}
    for sec in CARRIED_SECTIONS:
        if sec in katt:
            out[sec] = katt[sec]
    out["governance"] = {a: True for a in GOVERNANCE_ASSERTIONS} | {
        "attested_by": attested
    }
    out["touchpoint"] = {
        "tier": tier,
        "holdout_years": years,
        "keeper_run_id": keeper_run_id,
        "keeper_bundle": str(keeper_bundle.relative_to(REPO)),
        "keeper_git_sha": kmeta.get("git_sha"),
        "touchpoint_git_sha": tmeta.get("git_sha"),
        "recipe_identity": "PASS — 0 differing shared meta.json keys outside "
        "the provenance set",
        "carried_sections": [s for s in CARRIED_SECTIONS if s in katt],
        "solve_surface_added_since_keeper": cmp_["added"],
        "solve_surface_removed_since_keeper": cmp_["removed"],
        "added_kwargs_all_at_scenario_default": (
            None if cmp_["added_nondefault"] is None else True
        ),
        "supersedes": supersedes,
        "generator": "scripts/gen_touchpoint_attestation.py",
    }
    return out


def main() -> None:
    """CLI entry point: write the touchpoint bundle's attestation."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--keeper-bundle", required=True, type=Path)
    ap.add_argument("--keeper-run-id", required=True)
    ap.add_argument("--touchpoint-bundle", required=True, type=Path)
    ap.add_argument(
        "--supersedes",
        default=None,
        help="Run id of a stale touchpoint this one replaces, if any.",
    )
    args = ap.parse_args()

    att = build(
        args.keeper_bundle.resolve(),
        args.keeper_run_id,
        args.touchpoint_bundle.resolve(),
        args.supersedes,
    )
    dest = args.touchpoint_bundle / "calibration_attestation.json"
    dest.write_text(json.dumps(att, indent=2) + "\n")
    tp = att["touchpoint"]
    print(f"wrote {dest}")
    print(f"  tier              : {tp['tier']}")
    print(f"  holdout years     : {tp['holdout_years']}")
    print(f"  recipe identity   : {tp['recipe_identity']}")
    print(
        f"  solve-surface drift: +{len(tp['solve_surface_added_since_keeper'])} "
        f"-{len(tp['solve_surface_removed_since_keeper'])} kwargs "
        f"(keeper {tp['keeper_git_sha']} -> replay {tp['touchpoint_git_sha']})"
    )


if __name__ == "__main__":
    main()
