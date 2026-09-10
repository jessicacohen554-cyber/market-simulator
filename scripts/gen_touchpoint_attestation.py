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


def classify_declared(
    conflicts: dict, declared: tuple[str, ...], defaults: dict | None
) -> tuple[dict, dict]:
    """Split ``conflicts`` into DECLARED DEGRADATIONS and real conflicts.

    A **declared degradation** is a recipe delta a purged upstream source
    FORCES on a held-out year: a rule-13 measured overlay whose record simply
    does not exist before some vintage, and whose loader hard-errors rather
    than falling back silently. MISO is the case this was written for — MISO
    published no ASM reserve record before 2023 (``docs.misoenergy.org``
    retains ~3.5 years; every 2022 probe 404s) and
    ``miso_measured_reserve_requirements`` therefore cannot solve ANY MISO year
    before 2023, nor can its hard dependent ``miso_reserve_online_gated``.
    Without a channel here, no MISO year before 2023 could ever be attested and
    the holdout ladder would be closed by construction rather than by evidence
    — and that is not MISO-specific: any ISO whose measured overlay post-dates
    its holdout years hits the same wall.

    THE CHANNEL CANNOT BECOME A TUNING KNOB, and that is enforced, not
    promised. A declared key is admitted ONLY when the touchpoint's value is
    the field's ``ScenarioConfig`` DEFAULT — i.e. the degradation can only
    DISARM an overlay, dropping the run onto the construction a FORECAST year
    uses (rule 13 ``[R-MEASURED]``'s forward test). A declared key sitting at
    any other value is a conflict exactly as before, so this can never admit an
    armed mechanism, a re-tuned multiplier or a fitted scalar. When the
    ``ScenarioConfig`` defaults are unavailable the channel FAILS CLOSED: every
    declared key stays a conflict, because an unverifiable declaration is worth
    nothing.

    Args:
        conflicts: Differing shared keys from the recipe comparison.
        declared: Key names the operator declared as forced degradations.
        defaults: ``ScenarioConfig`` field defaults, or None when unavailable.

    Returns:
        ``(admitted, remaining)`` — the declared degradations that verified,
        and the conflicts that stand.
    """
    admitted: dict = {}
    remaining: dict = {}

    def _verify(key: str, kv, tv) -> dict | None:
        """Admit one field, or return None when it must stay a conflict."""
        if key not in declared or defaults is None or key not in defaults:
            return None
        if tv is not None and tv != defaults[key]:
            return None
        return {"keeper": kv, "touchpoint": tv, "scenario_default": defaults[key]}

    for key, vals in conflicts.items():
        kv, tv = vals["keeper"], vals["touchpoint"]
        # The generic ``prb_overrides`` channel nests config fields inside one
        # container dict, so replay_keeper's --set writes BOTH the top-level
        # kwarg and the container. Admit the container only when every field
        # that moved inside it verifies on its own terms — one un-declared or
        # non-default nested field and the whole container stays a conflict.
        if isinstance(kv, dict) and isinstance(tv, dict):
            nested = sorted(k for k in set(kv) | set(tv) if kv.get(k) != tv.get(k))
            checked = {k: _verify(k, kv.get(k), tv.get(k)) for k in nested}
            if nested and all(v is not None for v in checked.values()):
                admitted[key] = {"nested": checked}
            else:
                remaining[key] = dict(
                    vals,
                    refused="nested fields that did not verify: "
                    + ", ".join(k for k, v in checked.items() if v is None),
                )
            continue
        ok = _verify(key, kv, tv)
        if ok is None:
            remaining[key] = dict(
                vals,
                refused=(
                    "not declared"
                    if key not in declared
                    else "declared, but the touchpoint value is not the "
                    f"ScenarioConfig default "
                    f"{(defaults or {}).get(key)!r} — a declared degradation "
                    "may only DISARM an overlay, never set one"
                    if defaults is not None
                    else "declared, but ScenarioConfig defaults are "
                    "unavailable here, so the disarm cannot be verified "
                    "(fail-closed)"
                ),
            )
            continue
        admitted[key] = ok
    return admitted, remaining


def compare_recipes(
    keeper: dict, touchpoint: dict, declared: tuple[str, ...] = ()
) -> dict:
    """Compare two bundle ``meta.json`` recipes.

    Args:
        keeper: The designated keeper bundle's ``meta.json``.
        touchpoint: The touchpoint bundle's ``meta.json``.
        declared: Key names the operator declared as source-forced
            degradations; see :func:`classify_declared` for what admits one.

    Returns:
        A dict with ``conflicts`` (shared keys differing outside
        :data:`PROVENANCE_KEYS`, minus any verified declared degradation),
        ``declared_degradations`` (the verified ones), ``added`` / ``removed``
        (solve-surface drift), and ``added_nondefault`` (added keys not sitting
        at their ``ScenarioConfig`` default; ``None`` when the check was
        skipped).
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
    admitted, conflicts = classify_declared(conflicts, declared, defaults)
    return {
        "conflicts": conflicts,
        "declared_degradations": admitted,
        "added": added,
        "removed": removed,
        "added_nondefault": added_nondefault,
    }


def build(
    keeper_bundle: Path,
    keeper_run_id: str,
    touchpoint_bundle: Path,
    supersedes: str | None,
    declared: tuple[str, ...] = (),
    degradation_reason: str | None = None,
) -> dict:
    """Build the touchpoint attestation payload.

    Args:
        keeper_bundle: Designated keeper's bundle directory.
        keeper_run_id: The keeper's registered dashboard run id.
        touchpoint_bundle: The touchpoint bundle produced by the replay solve.
        supersedes: Optional run id of a stale touchpoint this one replaces.
        declared: Source-forced degradation keys (:func:`classify_declared`).
        degradation_reason: Why the source cannot supply them. Required
            whenever ``declared`` is non-empty — a degradation with no stated
            cause is exactly the silent recipe drift this generator exists to
            refuse.

    Returns:
        The attestation dict, ready to serialize.

    Raises:
        SystemExit: if the recipe-identity assertion fails, if a declared
            degradation does not verify, if a newly added solve kwarg is at a
            non-default value, or if the holdout years span more than one tier.
    """
    if declared and not degradation_reason:
        raise SystemExit(
            "--declared-degradation requires --degradation-reason: a recipe "
            "delta with no stated cause is the silent drift this generator "
            "exists to refuse."
        )
    kmeta = json.loads((keeper_bundle / "meta.json").read_text())
    tmeta = json.loads((touchpoint_bundle / "meta.json").read_text())
    katt = json.loads((keeper_bundle / "calibration_attestation.json").read_text())

    cmp_ = compare_recipes(kmeta, tmeta, declared)
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
    # RULE 1 [R-STRUCT] CARVE-OUT (owner ruling 2026-09-05), mirrored from
    # calibration_verdict.score_governance. A keeper that tunes price through
    # the authorized `offer_curve_by_group` channel carries
    # `levers_trace_to_measured_input` and `no_fit_to_price_residuals` as
    # FALSE, scoped by a `authorized_price_tuning` declaration — and its own C6
    # PASSES on that basis. This generator predated the amendment and demanded
    # all four assertions be true, which made every such keeper's touchpoint
    # unattestable (MISO's keeper is exactly that shape). The carve-out reaches
    # those two assertions and NOTHING else: `no_pinning_to_actuals` and
    # `outage_filter_exogenous_net_load` must still be true, and a keeper with
    # the two false and NO declaration is still refused.
    scoped = {"levers_trace_to_measured_input", "no_fit_to_price_residuals"}
    declaration = kgov.get("authorized_price_tuning")
    has_decl = isinstance(declaration, dict)
    missing = [
        a
        for a in GOVERNANCE_ASSERTIONS
        if not kgov.get(a) and not (a in scoped and has_decl)
    ]
    if missing:
        raise SystemExit(
            f"keeper attestation does not assert: {missing}"
            + (
                ""
                if has_decl
                else " (and carries no authorized_price_tuning declaration, "
                "which is the only thing that scopes the two price-tuning "
                "assertions — rule 1 [R-STRUCT] carve-out)"
            )
        )

    degraded = cmp_["declared_degradations"]
    if degraded:

        def _one(k: str, v: dict) -> str:
            if "nested" in v:
                inner = ", ".join(
                    f"{ik}: {iv['keeper']!r} -> {iv['touchpoint']!r} "
                    f"(default {iv['scenario_default']!r})"
                    for ik, iv in sorted(v["nested"].items())
                )
                return f"{k} (generic-override container) [{inner}]"
            return (
                f"{k}: {v['keeper']!r} -> {v['touchpoint']!r} (ScenarioConfig "
                f"default {v['scenario_default']!r})"
            )

        deg_txt = "; ".join(_one(k, v) for k, v in sorted(degraded.items()))
        degradation_note = (
            f" {len(degraded)} DECLARED SOURCE-FORCED DEGRADATION(S), applied to the held-out "
            f"year(s) only and VERIFIED rather than asserted: {deg_txt}. REASON: "
            f"{degradation_reason} Each key is admitted ONLY because its "
            "touchpoint value is the field's ScenarioConfig DEFAULT — the "
            "generator refuses a declared key set to anything else — so the "
            "degradation can only DISARM a measured overlay and drop the run "
            "onto the construction a FORECAST year uses (rule 13 [R-MEASURED]'s "
            "forward test), never arm a mechanism, re-cut a multiplier or "
            "introduce a scalar. NOTHING ELSE MOVED: recipe identity is computed "
            "over every other shared key and is exact. The degradation is NOT a "
            "lever, was NOT selected against any gate, and is the SAME disarm in "
            "every touchpoint year of this ISO."
        )
    else:
        degradation_note = ""

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
        f"this file otherwise.{degradation_note} "
        "ZERO free parameters introduced or moved, so the rule-20 "
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
    # Carry the KEEPER's own assertion VALUES, not a blanket True: a touchpoint
    # re-solves the keeper's recipe, so it inherits the keeper's governance
    # posture exactly — including a scoped price-tuning declaration. Writing
    # True over a keeper's declared False would be the generator asserting
    # something the keeper does not.
    out["governance"] = {a: bool(kgov.get(a)) for a in GOVERNANCE_ASSERTIONS} | {
        "attested_by": attested
    }
    if has_decl:
        # (b) "ONE config across EVERY scored year" is checked against the RUN's
        # scored years, so the carried declaration is re-pointed at this
        # touchpoint's span. The value itself is byte-identical to the keeper's
        # — the same one config, now also held on a year it was never fitted to,
        # which is the strongest form of (b), not a weakening of it. The keeper's
        # own span is preserved beside it so nothing is lost.
        out["governance"]["authorized_price_tuning"] = dict(declaration) | {
            "years_held": years,
            "years_held_keeper_span": declaration.get("years_held"),
            "touchpoint_note": (
                "Carried UNCHANGED from the keeper "
                f"{keeper_run_id}: the same multiplier value, never re-cut for "
                "this year and never swept against any gate here. `years_held` "
                "is re-pointed to this run's scored year(s) because rule 1 (b) "
                "is checked against the run's own span; the keeper's span is "
                "kept in `years_held_keeper_span`, so the config is one config "
                "across the union of both."
            ),
        }
    out["touchpoint"] = {
        "tier": tier,
        "holdout_years": years,
        "keeper_run_id": keeper_run_id,
        "keeper_bundle": str(keeper_bundle.relative_to(REPO)),
        "keeper_git_sha": kmeta.get("git_sha"),
        "touchpoint_git_sha": tmeta.get("git_sha"),
        "recipe_identity": (
            "PASS — 0 differing shared meta.json keys outside the provenance set"
            if not degraded
            else f"PASS — 0 differing shared meta.json keys outside the "
            f"provenance set and the {len(degraded)} VERIFIED declared "
            "source-forced degradation(s) below, each of which the generator "
            "admitted only because its touchpoint value is the field's "
            "ScenarioConfig default (a disarm, never an arm)"
        ),
        "declared_degradations": degraded or None,
        "declared_degradation_reason": degradation_reason if degraded else None,
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
    ap.add_argument(
        "--declared-degradation",
        action="append",
        default=[],
        metavar="FIELD",
        help="A meta.json key whose difference from the keeper is FORCED by a "
        "purged upstream source (repeatable). Admitted ONLY when the "
        "touchpoint's value is that field's ScenarioConfig default — i.e. the "
        "overlay is DISARMED onto the construction a forecast year uses; a "
        "declared key set to anything else is still a hard error, so this can "
        "never admit an armed mechanism or a tuned value. Requires "
        "--degradation-reason.",
    )
    ap.add_argument(
        "--degradation-reason",
        default=None,
        help="Why the source cannot supply the declared field(s). Written "
        "verbatim into the attestation; required with --declared-degradation.",
    )
    args = ap.parse_args()

    att = build(
        args.keeper_bundle.resolve(),
        args.keeper_run_id,
        args.touchpoint_bundle.resolve(),
        args.supersedes,
        tuple(args.declared_degradation),
        args.degradation_reason,
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
