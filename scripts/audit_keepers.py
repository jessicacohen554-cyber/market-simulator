"""Audit that the dashboard text matches each designated keeper's actual results.

The backcast dashboard shows three kinds of keeper text, with very different
trust levels:

* The **Calibration Status** page (the per-ISO ``status/<ISO>.js`` parts +
  ``status/shared.js``) is regenerated from the SAME scorer the gate uses
  (``scripts/build_status.py`` -> ``calibration_verdict``), so it can never
  *say* the wrong determination — but a part goes **stale** the moment its
  keeper changes, its bundle is re-solved, or the benchmark/rubric moves.
* Each keeper's **run-report header** is the human-written ``definition`` in its
  registry sidecar (``frontend/data/backcast/registry/<id>.json``). This is the
  one surface that can silently *lie*: a placeholder, a copy from the wrong run,
  or a stale "NOT-YET" after the verdict turned green.
* The per-year scorecard / diagnostics are computed client-side from the run
  payload, so they are always faithful and are not audited here.

This module checks the editable surfaces against the bundle and the live
verdict. It is the deterministic core the ``calibration-keeper-auditor``
subagent runs (and is safe to wire into CI / a pre-commit ``--check``).

For every keeper in the sharded keeper store (``frontend/data/backcast/
keepers/<ISO>.json``, via ``scripts.lib.keeper_store`` — legacy monolith
parsed as a fallback) it verifies:

  E1  sidecar, run payload and bundle dir all exist.
  E2  sidecar ``iso`` matches the bundle's ``calibration_flags.iso``.
  E3  sidecar ``years`` matches the bundle's solved years AND, for a multi-year
      ISO, is the full span (claude.md #13: never a single-year keeper).
  E4  ``definition`` is real prose, not the auto-generated placeholder / empty.
  E5  any determination token the ``definition`` asserts ("NOT-YET",
      "CALIBRATED-WITH-CAVEATS", "CALIBRATED") matches the CURRENT verdict.
  E6  exactly one keeper per ISO (per-shard by construction; still catches a
      shard whose keeper's sidecar claims a DIFFERENT iso — the wrong lane).
  E8  the bundle attestation carries a ``free_parameters`` DOF ledger and every
      residual-sourced entry references an open root cause (CLAUDE.md rule 20).
  E9  a DECLARED ``ablation_twin`` sidecar link resolves to a registered run.
      The zero-forcing twin itself is OPTIONAL (CLAUDE.md rule 20, owner
      amendment 2026-07-14: keepers no longer build or register a twin;
      forcing-legitimacy rests on the DOF ledger + ``legitimacy_diagnostics``).
      Absence of a twin is OK; only a dangling link — a sidecar naming a twin
      with no registry payload — FAILs, as a data-integrity check.
  E10 the bundle attestation is STRUCTURALLY COMPLETE — ``schema``,
      ``governance`` (all four assertions present, boolean-typed and true) and
      an ``exceptions`` LIST — not just the ``free_parameters`` block E8 checks.
      Added by caiso-189 (2026-08-11) after the caiso-188 promotion shipped an
      attestation ``scripts/build_dof_ledger.py`` had written alone: E8 passed it
      ("0/0" on a bundle nobody had attested) while ``calibration_verdict``
      scored C6 UNATTESTED and forced NOT-YET, and the incumbent's C3c exceptions
      never carried forward. E8 alone can never catch that, because the missing
      blocks are exactly the ones it does not look at.
  E11 keeper-lineage recipe fidelity over the FULL ``solve_and_persist`` kwarg
      surface. The nyiso-108→155 silent-de-arm class
      (``docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md`` §2): the hydro
      repair pair are solve kwargs, NOT ``ScenarioConfig`` fields, so
      "all scenario_config fields identical" lineage checks were structurally
      blind to them and an armed keeper mechanism left the lineage with no
      de-arm decision anywhere. Whenever a shard records a structured lineage
      (``superseded.former_keeper`` — the NYISO convention) and both bundles
      are on disk, the CURRENT keeper's full recorded recipe (run_config.json
      scenario block ∪ meta.json solve-kwarg surface) is diffed against the
      FORMER keeper's, and every kwarg whose recorded value CHANGED must be
      declared somewhere in the shard's prose — an undeclared change FAILs.
      A kwarg present only in the former bundle (a field deleted from the
      codebase between the solves — the rule-26 class) WARNs; keys present
      only in the current bundle (fields born between the solves, recorded at
      their defaults across HEAD drift) are reported, never failed. Shards
      with no structured lineage record pass with an explanatory note — the
      guard arms lane-by-lane as shards adopt the convention.
  M1  ``complete``-marker currency + determination re-verification (owner
      decision D-5(b), signed 2026-08-02): every ISO holding a ``complete``
      entry in ``calibration-complete.json`` has that entry's ``keeper`` field
      pointing at its CURRENT designated keeper (M1a), and the determination the
      entry asserts still matches the LIVE verdict of the run it names (M1b), so
      a promotion can never silently transfer a determination onto a run it was
      never scored against. For an ISO whose keeper shard carries an
      owner-ruled ``config_partition.iso_determination`` (the ercot-246 ruling,
      2026-08-31), the live value M1b compares against is the partition rollup
      — worst config determination over the DESIGNATED TRAIN spans, held-out
      configs excluded per rule 30(c) — recomputed from committed artifacts,
      never read from the shard's own assertion. Costs no
      solve — ``calibration_verdict`` reads committed artifacts only.
  E12 referential integrity of the shard's LIVE run-id pointers — the fields
      ``build_status.py`` copies into ``status/<ISO>.js`` and
      ``calibration-status.js`` renders as a Run Explorer link
      (``config_partition.configs[].run_id``, ``holdout_touchpoint.run_id``,
      ``standing_note.probe_run_id``; ``keeper`` is E1's). Each must resolve to
      a registry sidecar, so a run pruned under rule 15 cannot leave a DEAD
      LINK — or, the neiso-102 / pjm-166 class, a hand-authored
      ``holdout_touchpoint`` panel whose determination CONTRADICTS the derived
      per-year table beneath it (rule 30 [R-TOUCHPOINT-FOLD](b)). Keeper
      GENEALOGY (``superseded``/``chain``, ``de_designation_history``,
      ``frontier_withdrawn_*``, ``source_run_id``) and narrative prose are OUT
      OF SCOPE on purpose: they cite pruned runs by design and are explicitly
      not retracted.
  E13 keeper-only retention of the ISO's REGISTERED SET (rule 35 ``[R-PROMOTE]``
      (f)): every run registered for an ISO is either its designated keeper or a
      run STAMPED to it (``holdout.keeper``, rule 30 (a)) — anything else is a
      superseded run a promotion failed to prune. A dangling stamp counts as
      unstamped, matching how rule 30 (a) renders one. This is the gap rule 35
      names: rule 15 ``[R-DASHBOARD]`` deferred the sweep to "the next
      registration", nobody owned that, and on 2026-09-12 this audit passed
      clean on 47 registered runs against 7 keepers because E1 sees only the
      keeper's own stores and E12 only the shard's live pointers. The OK line
      reports the year set the keeper carries, which is what rule 35 (b)/(c)
      require a promotion to preserve.
  E14 SOLVE-ENVIRONMENT PIN CURRENCY: the bundle's recorded
      ``environment.packages`` match the versions ``requirements.txt`` pins.
      A keeper is the ISO's reference result, so which solver and numeric
      stack produced it is part of its provenance — ``highspy`` above all,
      since a different HiGHS is a different LP solver. Nothing else in this
      audit looks at the environment at all, which is how the nyiso-231
      off-pin keeper reached the dashboard unremarked
      (``docs/FINDING-nyiso231-the-keeper-is-off-pin-2026-09-13.md``).
      Severity is **WARN, not FAIL**, deliberately: an off-pin keeper is a
      provenance fact to surface, not grounds to retroactively invalidate a
      committed result whose numbers are on the site — and a drifting pin is
      a repo-wide event that would otherwise red six lanes that did nothing
      wrong (rule 25 ``[R-ISO-SCOPE]``). Promote it to FAIL on an owner
      ruling if a re-solve-on-drift policy is ever adopted. Bundles predating
      the ``environment`` block, and packages a bundle records but
      ``requirements.txt`` does not pin, are reported as unverifiable rather
      than assumed good. Measured green on all seven keepers at the time it
      was added (nyiso-234, 2026-09-14).
  S1  the ``status/`` parts are in sync with the current verdicts
      (``build_status.py --check``, scoped to the audited ISOs).
  H1  holdout quarantine (CLAUDE.md rule 22 / audit D-6, amended 2026-07-04):
      NO registered bundle — keeper or probe — declares a solve year outside
      the 2023–2025 calibration window unless its ISO has a
      calibration-complete marker in
      ``frontend/data/backcast/calibration-complete.json``.

Usage:
    python scripts/audit_keepers.py                  # audit every keeper
    python scripts/audit_keepers.py --iso ERCOT PJM  # scope to ISOs
    python scripts/audit_keepers.py --check          # exit 1 on any FAIL
    python scripts/audit_keepers.py --json           # machine-readable report

Exit code is 0 when there are no FAILs (warnings allowed), 1 otherwise.
Stdlib-only; reuses ``scripts.calibration_verdict``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import calibration_verdict as cv  # noqa: E402  (after sys.path insert)
from scripts.lib import holdout_policy  # noqa: E402  (after sys.path insert)
from scripts.lib import keeper_store  # noqa: E402  (after sys.path insert)
from scripts.lib.known_unsynced_keepers import UNSYNCED_KEEPERS  # noqa: E402

# A sidecar whose definition still reads like this never described the run.
_PLACEHOLDER_RE = re.compile(r"^\s*calibration run from bundle\b", re.IGNORECASE)

# Determination tokens, longest-first so "CALIBRATED-WITH-CAVEATS" wins over
# the substring "CALIBRATED".
_DET_TOKENS = ("CALIBRATED-WITH-CAVEATS", "NOT-YET", "CALIBRATED")

# ISOs that must always carry the full backcast year span (claude.md #16).
# SPP joined at registration (2026-09-06, lane SPP-20): a single-year SPP keeper
# is refused from day one (rule 16 [R-ALLYEARS]; plan §3).
# NWPP added at registration (2026-09-14, lane NWPP-20; rule 16 [R-ALLYEARS]):
# a single-year NWPP keeper is refused from day one. SOCO — the Southern
# Company balancing authority — joined the same way at its registration
# (2026-09-14, lane SOCO-20; SOCO plan §3 defaults: "a single-year SOCO keeper
# is refused from day one").
_MULTI_YEAR_ISOS = {"CAISO", "PJM", "NEISO", "NYISO", "MISO", "SPP", "NWPP", "SOCO"}

# E9 no longer enforces a zero-forcing ablation twin (CLAUDE.md rule 20, owner
# amendment 2026-07-14: keepers no longer build or register one; forcing-
# legitimacy rests on the DOF ledger + legitimacy_diagnostics). The grandfather
# rollout list is deleted with the requirement; the only E9 check that remains is
# a data-integrity one — a DECLARED ``ablation_twin`` link must resolve —
# handled inline in ablation_twin_finding().

CALIBRATION_YEARS = holdout_policy.CALIBRATION_YEARS

#: Keeper-designation file. It SURVIVES ``[R-HOLDOUT]``'s removal (2026-09-09)
#: for the two jobs it does that were never authorization: naming each ISO's
#: current designated keeper (M1 below), and feeding the forecast program's
#: gate (a). It no longer authorizes any solve, score or registration.
MARKER_FILE = REPO / "frontend/data/backcast/calibration-complete.json"


def marker_currency_failures(
    isos: list[str] | None = None,
) -> list[tuple[str, str, str]]:
    """Return M1 findings: `complete`-block markers vs the designated keepers.

    D-5(b) (owner decision, signed 2026-08-02 —
    ``docs/handoffs/ffr-owner-sitting-2026-08-02.md`` Addendum C.1, OPTION B) made
    the marker's ``keeper`` field **track the ISO's current designated dashboard
    keeper** instead of freezing the declaration-time snapshot, and required the
    ``determination`` to be RE-VERIFIED against the newly named run on every
    promotion — "so the marker never asserts an unscored determination".

    This check enforces both halves, and it does so **without a solve**:
    ``calibration_verdict`` reads committed artifacts only and never re-solves the
    LP, so re-verifying a determination is a seconds-long, byte-reproducible read.

      M1a  the ``complete`` entry's ``keeper`` == the ISO's keeper shard.
      M1b  the determination token the entry's ``determination`` prose asserts ==
           the LIVE verdict of the run the entry names.

    A SPENT locked-test one-shot is never re-keyed (``locked_test_scored_on`` holds
    its frozen config, rule 22) and is not read here. Returns ``(iso, code, msg)``
    triples; empty means both halves hold for every audited ``complete`` ISO.
    """
    marker_doc = _load_json(MARKER_FILE) or {}
    complete = {
        k: v
        for k, v in (marker_doc.get("complete") or {}).items()
        if not k.startswith("_") and isinstance(v, dict)
    }
    want = {s.upper() for s in isos} if isos else None
    keeper_map = keeper_store.keeper_ids()
    out: list[tuple[str, str, str]] = []
    for iso in sorted(complete):
        if want and iso.upper() not in want:
            continue
        entry = complete[iso]
        marker_keeper = entry.get("keeper")
        designated = keeper_map.get(iso)
        if designated and marker_keeper != designated:
            out.append(
                (
                    iso,
                    "M1a",
                    f"{MARKER_FILE.name} 'complete'.{iso}.keeper = {marker_keeper!r} but "
                    f"the designated keeper is {designated!r} — re-key the marker and "
                    "re-verify its determination against the new run (owner decision "
                    "D-5(b), 2026-08-02; `python scripts/calibration_verdict.py "
                    f"--run-id {designated}` — no solve).",
                )
            )
            # M1a short-circuits M1b: the recorded determination belongs to the
            # superseded run, so re-verifying it there answers a stale question.
            # The re-key procedure carries the re-verification, and this audit
            # re-runs after it — so the fresh M1b check happens then.
            continue
        asserted = _asserted_determination(entry.get("determination") or "")
        if asserted and marker_keeper:
            try:
                live = _live_iso_determination(iso, marker_keeper)
            except Exception as exc:  # noqa: BLE001 - report, never crash the audit
                out.append(
                    (
                        iso,
                        "M1b",
                        f"cannot re-verify {iso}'s marker determination against "
                        f"{marker_keeper}: {exc}",
                    )
                )
                continue
            if live and asserted != live:
                out.append(
                    (
                        iso,
                        "M1b",
                        f"{MARKER_FILE.name} 'complete'.{iso}.determination asserts "
                        f"{asserted!r} but the live verdict of {marker_keeper} is "
                        f"{live!r} — the marker asserts a determination that was never "
                        "scored against the run it names (owner decision D-5(b)).",
                    )
                )
    return out


def _live_iso_determination(iso: str, run_id: str) -> str | None:
    """The ISO-level determination a marker is verified against, computed live.

    Default (every single-keeper ISO): the unrestricted registered verdict of
    ``run_id`` — the original D-5(b) M1b comparison, unchanged.

    For an ISO whose keeper shard carries an owner-declared ``config_partition``
    WITH the owner-ruled ``iso_determination`` field (the ercot-246 ruling,
    2026-08-31: a partitioned keeper's ISO-level determination is the WORST
    config determination over the DESIGNATED spans), the live value is that
    rollup RECOMPUTED here from the committed artifacts — each config scored on
    its designated span via ``calibration_verdict.determine(run, years=span)``,
    worst taken under the conservative ordering (NOT-YET < CAVEATS <
    CALIBRATED). The shard's own stored ``iso_determination`` is never trusted:
    a stale stored value is caught because the recomputed rollup is what the
    marker's assertion must match. Fail-closed on both edges: a partition
    without the ruling field keeps the plain single-run comparison, and an
    unscorable config raises (surfacing as an M1b failure), never skips.
    """
    shard = keeper_store.load_shard(iso) or {}
    cp = shard.get("config_partition") or {}
    if not (cp.get("iso_determination") and cp.get("configs")):
        return cv.determine(run_id).get("determination")

    def _rank(det: str | None) -> int:
        d = (det or "").upper()
        if "NOT" in d:
            return 0
        if "CAVEAT" in d:
            return 1
        return 2

    # RULE 30(c) [R-TOUCHPOINT-FOLD]: "The ISO's calibration determination is
    # the train-tier (2023-2025) verdict and nothing else. A validation-tier
    # score is iterable model-SELECTION evidence ... it cannot certify and it
    # cannot decertify." Since ercot-255 a partition may designate a HELD-OUT
    # span (ERCOT 2021/2022), so a config marked `tier: "validation"` is
    # excluded from this rollup while still being scored and rendered
    # everywhere else. Absent/`train` keeps every pre-existing ISO's rollup
    # byte-identical, and the fold stays fail-closed: a partition whose configs
    # are ALL held-out has no train-tier verdict to assert, so it falls back to
    # the plain single-run comparison rather than silently passing.
    span_dets = []
    for cfg in cp["configs"]:
        if str(cfg.get("tier") or "train").lower() != "train":
            continue
        span = [int(y) for y in cfg.get("years", [])]
        span_dets.append(cv.determine(cfg["run_id"], years=span).get("determination"))
    if not span_dets:
        return cv.determine(run_id).get("determination")
    return min(span_dets, key=_rank)


def ablation_twin_finding(
    run_id: str, side: dict, registry_dir: Path
) -> tuple[str, str]:
    """Return the E9 (ablation-twin link) finding for one keeper: (level, message).

    ``level`` is ``"OK"`` / ``"FAIL"``. The zero-forcing ablation twin is
    OPTIONAL (CLAUDE.md rule 20, owner amendment 2026-07-14): a keeper with NO
    ``ablation_twin`` link is OK. Only a DECLARED-but-dangling link — a sidecar
    naming a twin with no registry payload — FAILs, as a data-integrity check.
    Pure over its inputs so it is unit-testable without the live registry.
    """
    twin_id = side.get("ablation_twin")
    twin_side = _load_json(registry_dir / f"{twin_id}.json") if twin_id else None
    if twin_id and twin_side is not None:
        return "OK", f"ablation twin registered ({twin_id})"
    # A DECLARED-but-broken link fails purely as a data-integrity check: the twin
    # is no longer required, but a sidecar that ASSERTS a twin which does not
    # resolve is a typo / an unregistered twin, not an intentional "no twin".
    if twin_id and twin_side is None:
        return (
            "FAIL",
            f'sidecar "ablation_twin" points to {twin_id!r} but no '
            f"registry/{twin_id}.json exists — fix or remove the dangling link.",
        )
    # No twin declared: OK. Per CLAUDE.md rule 20 (owner amendment 2026-07-14)
    # the zero-forcing ablation twin is NO LONGER required — keepers no longer
    # build or register one; forcing-legitimacy rests on the DOF ledger plus the
    # D-2 / legitimacy_diagnostics.json attribution alone. No keeper can FAIL E9
    # for a missing twin.
    return (
        "OK",
        "no ablation twin (not required — CLAUDE.md rule 20, owner amendment "
        "2026-07-14; forcing-legitimacy via DOF ledger + legitimacy_diagnostics).",
    )


#: The four C6 assertions ``calibration_verdict.score_governance`` requires. Kept
#: as a literal here rather than imported so this check keeps working (and keeps
#: failing closed) even if the scorer's own list is refactored — a keeper whose
#: attestation omits one is unattestable either way.
GOVERNANCE_ASSERTIONS = (
    "levers_trace_to_measured_input",
    "no_fit_to_price_residuals",
    "no_pinning_to_actuals",
    "outage_filter_exogenous_net_load",
)


def attestation_shape_finding(att: dict | None) -> tuple[str, str]:
    """Return the E10 (attestation completeness) finding: ``(level, message)``.

    E8 validates the ``free_parameters`` DOF ledger and NOTHING else, so a
    bundle carrying only the block ``scripts/build_dof_ledger.py`` writes audits
    green while ``calibration_verdict`` scores C6 **UNATTESTED** and forces
    NOT-YET. That is exactly what happened to the caiso-188 keeper
    (``2026-08-09-caiso-188-d1-micseam``): its promotion shipped without the
    bespoke ``gen_caisoNNN_attestation.py`` every other CAISO promotion ships,
    E8 reported "0/0", and the governance gate and the whole C3c exceptions
    ledger were silently absent. This check closes that hole.

    Legs are graded by what they actually cost the verdict, so the check can
    never be green on a defect that moves a determination:

    * **FAIL** — no attestation file; no ``governance`` mapping (C6 reads
      UNATTESTED, which alone forces NOT-YET); any of the four assertions
      missing, non-boolean or false (C6 reads FAIL); or no ``exceptions``
      **list** (every ledgered caveat silently vanishes). Truthy non-booleans
      (``"yes"``, ``1``) are rejected: an assertion is a signed claim, not a
      coercion. An EMPTY ``exceptions`` list is fine — most keepers ledger
      nothing; what is not fine is the key being ABSENT, because then nobody has
      said whether there are exceptions at all.
    * **WARN** — everything load-bearing is present but the documentary
      ``schema`` version tag is missing. ``calibration_verdict`` never reads
      ``schema``, so this changes no determination; it is surfaced on every run
      rather than failing a lane whose governance is genuinely complete.

    Pure over its input so it is unit-testable without a bundle on disk.
    """
    if att is None:
        return "FAIL", "no calibration_attestation.json in bundle (CLAUDE.md rule 20)"
    problems: list[str] = []
    gov = att.get("governance")
    if not isinstance(gov, dict):
        problems.append(
            'no "governance" block — calibration_verdict scores C6 UNATTESTED, '
            "which alone forces NOT-YET"
        )
    else:
        # Rule 1 [R-STRUCT] carve-out (owner ruling 2026-09-05): the registered
        # offer-curve band multipliers are an authorized price-tuning channel, so
        # the two channel-scoped assertions may read false WHEN the run carries a
        # well-formed governance.authorized_price_tuning declaration. Mirrors
        # calibration_verdict.score_governance, and fails closed the same way: an
        # absent or malformed declaration leaves the false assertion a problem.
        scoped = {"no_fit_to_price_residuals", "levers_trace_to_measured_input"}
        declared = isinstance(gov.get("authorized_price_tuning"), dict) and all(
            f in gov["authorized_price_tuning"]
            for f in (
                "channel",
                "ruling",
                "value",
                "years_held",
                "set_ex_ante",
                "not_swept",
            )
        )
        for a in GOVERNANCE_ASSERTIONS:
            if a not in gov:
                problems.append(f"governance.{a} missing")
            elif not isinstance(gov[a], bool):
                problems.append(f"governance.{a} is {gov[a]!r}, not a bool")
            elif not gov[a]:
                if a in scoped and declared:
                    continue  # scoped by a declared authorized tuning channel
                problems.append(f"governance.{a} is false")
    if not isinstance(att.get("exceptions"), list):
        problems.append('no "exceptions" list (use [] when nothing is ledgered)')
    if problems:
        return (
            "FAIL",
            "attestation incomplete — "
            + "; ".join(problems)
            + ". Generate it with the promotion's scripts/gen_<run>_attestation.py "
            "(post-hoc precedents: gen_pjm153_collapse_attestation.py, "
            "gen_caiso189_attestation.py).",
        )
    if not str(att.get("schema", "")).strip():
        return (
            "WARN",
            'attestation has no "schema" version tag (governance and exceptions '
            "are complete, and calibration_verdict never reads schema, so no "
            "determination is affected) — add "
            '"schema": "calibration-attestation/v1" on the next regeneration',
        )
    n_exc = len(att["exceptions"])
    return (
        "OK",
        f"attestation complete (schema, 4/4 governance assertions true, "
        f"{n_exc} exception(s))",
    )


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _bundle_flags(bundle: Path) -> dict | None:
    cfg = _load_json(bundle / "run_config.json")
    return (cfg or {}).get("calibration_flags") if cfg else None


# E11 — meta.json keys that are provenance rather than solve kwargs, so a
# cross-promotion difference in them is never a recipe change. Mirrors
# ``scripts.replay_keeper._IGNORE`` plus the free-text ``note`` (duplicated
# because replay_keeper imports the numpy/model stack and this module is
# stdlib-only; ``tests/scoring/test_audit_keepers_lineage.py`` pins the two
# sets against each other so they cannot drift).
E11_META_PROVENANCE = {
    "timestamp",
    "note",
    "gas_prices",
    "passes",
    "td_loss_factor",
    "shared_inputs",
    "git_sha",
    "basis_sha",
    "highspy_version",
    "environment",
    # ercot-256: the composite per-year recipe overlay (see the matching
    # replay_keeper._IGNORE entry). Provenance, never a solve kwarg.
    "config_partition_overrides",
    "iso",
    "years",
    "hours",
    "reuse",
    # Y-29 (2026-09-24): mirror the two replay_keeper._IGNORE entries added
    # after this set was last synced — free-text session provenance (ercot-261)
    # and rule-32 composition provenance (pjm-d4-3). Neither selects a
    # mechanism or maps to a solve kwarg; see the matching _IGNORE comments.
    "model_changes_note",
    "composed_from",
}

_E11_ABSENT = object()


def _recipe_block(bundle: Path) -> dict | None:
    """The bundle's full recorded recipe: scenario block ∪ solve-kwarg surface.

    ``meta.json`` is the authoritative snapshot of the kwargs
    ``solve_and_persist`` was called with (resolved defaults included), and
    ``run_config.json``'s ``scenario_config`` records the resolved
    ``ScenarioConfig``. A lineage diff must read BOTH: the nyiso-108→155
    silent de-arm lived exactly in the meta-only half (the
    ``_config_block`` merge of ``scripts/probes/_nyiso155_hydro_repair_ab.py``
    is the pattern this generalizes). Keys are namespaced ``sc.<field>`` /
    ``meta.<kwarg>`` so the two surfaces can never shadow each other.

    Returns None when neither file is readable (no recipe to diff).
    """
    block: dict = {}
    cfg = _load_json(bundle / "run_config.json")
    for k, v in ((cfg or {}).get("scenario_config") or {}).items():
        block[f"sc.{k}"] = v
    meta = _load_json(bundle / "meta.json")
    for k, v in (meta or {}).items():
        if k not in E11_META_PROVENANCE:
            block[f"meta.{k}"] = v
    return block if (cfg or meta) else None


def _shard_prose(node) -> str:
    """Every string value in the shard, recursively — the declaration corpus.

    A recipe delta counts as declared when its bare kwarg/field name appears
    anywhere in the shard's prose (promotion_note, determination_note, nested
    superseded reasons, …). Substring match on the bare name is deliberate:
    the promotion note writes e.g. ``hydro_backfill_year=2024`` and the check
    must not depend on its phrasing.
    """
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        return "\n".join(_shard_prose(v) for v in node.values())
    if isinstance(node, list):
        return "\n".join(_shard_prose(v) for v in node)
    return ""


def lineage_recipe_finding(
    shard: dict, registry_dir: Path, repo_root: Path
) -> tuple[str, str]:
    """E11 — decide OK / WARN / FAIL for one shard's keeper-lineage recipe diff.

    Tiering by blast radius (module docstring E11):

    * value changed on a key BOTH bundles record → the silent-de-arm/re-arm
      class (solve kwargs record resolved defaults, so a kwarg no longer
      passed shows as a VALUE change, e.g. ``hydro_backfill_year`` 2024→None)
      → FAIL unless declared in the shard prose;
    * key only in the FORMER bundle → the field was deleted from the codebase
      between the solves (rule-26 class) → WARN unless declared;
    * key only in the CURRENT bundle → a field born between the solves,
      recorded at its default across HEAD drift — indistinguishable from an
      armed new mechanism without importing ``ScenarioConfig`` (this module is
      stdlib-only), and new solve-affecting mechanisms are already guarded by
      the rule-28 matrix CI — reported in the OK note, never failed.
    """
    former = (shard.get("superseded") or {}).get("former_keeper")
    cur = shard.get("keeper")
    if not former or not cur:
        return (
            "OK",
            "no structured former-keeper lineage recorded "
            "(superseded.former_keeper) — recipe diff not applicable; the "
            "guard arms when the shard adopts the convention",
        )
    bundles: dict[str, Path] = {}
    for label, rid in (("current", cur), ("former", former)):
        side = _load_json(registry_dir / f"{rid}.json")
        bundle = repo_root / (side or {}).get("bundle", "")
        if not side or not side.get("bundle") or not bundle.exists():
            return (
                "WARN",
                f"lineage recipe diff not computable: {label} keeper {rid} has "
                "no resolvable bundle on disk — the full-kwarg-surface guard "
                "has no baseline (a promotion should run before the former "
                "bundle is retention-pruned)",
            )
        bundles[label] = bundle
    blocks = {label: _recipe_block(b) for label, b in bundles.items()}
    for label, blk in blocks.items():
        if blk is None:
            return (
                "WARN",
                f"lineage recipe diff not computable: {label} keeper bundle "
                "has neither run_config.json nor meta.json",
            )
    prose = _shard_prose(shard)
    changed_undeclared: list[str] = []
    changed_declared: list[str] = []
    deleted_undeclared: list[str] = []
    born: list[str] = []
    a, b = blocks["former"], blocks["current"]
    for key in sorted(set(a) | set(b)):
        va, vb = a.get(key, _E11_ABSENT), b.get(key, _E11_ABSENT)
        if va is not _E11_ABSENT and vb is not _E11_ABSENT:
            if va != vb:
                bare = key.split(".", 1)[1]
                delta = f"{bare} ({va!r} -> {vb!r})"
                (changed_declared if bare in prose else changed_undeclared).append(
                    delta
                )
        elif vb is _E11_ABSENT:
            bare = key.split(".", 1)[1]
            if bare not in prose:
                deleted_undeclared.append(f"{bare} (was {va!r})")
        else:
            born.append(key.split(".", 1)[1])
    if changed_undeclared:
        return (
            "FAIL",
            "UNDECLARED keeper-recipe change(s) vs former keeper "
            f"{former}: {'; '.join(changed_undeclared)} — the silent-de-arm "
            "class (FINDING-nyiso-hydro-truncation-repair-2026-08.md §2): "
            "declare each in the shard's promotion prose or revert it",
        )
    if deleted_undeclared:
        return (
            "WARN",
            f"kwarg(s) recorded by former keeper {former} are absent from the "
            f"current bundle's surface: {'; '.join(deleted_undeclared)} — a "
            "codebase field deletion (rule-26 class) or a lost channel; "
            "declare it in the shard prose to silence",
        )
    note = f"recipe faithful to former keeper {former}"
    if changed_declared:
        note += f"; declared change(s): {'; '.join(changed_declared)}"
    if born:
        note += (
            f"; {len(born)} field(s) born since the former solve "
            f"(recorded, not gated): {', '.join(born)}"
        )
    return ("OK", note)


def _asserted_determination(definition: str) -> str | None:
    """Return the determination token the definition prose claims, if any.

    We only treat a token as an *assertion about this run's status* when it is
    not merely naming another run's recipe. The common, checkable phrasings are
    "Still NOT-YET", "now CALIBRATED", "remains CALIBRATED-WITH-CAVEATS", or a
    trailing "... NOT-YET." — i.e. the token stands on its own near a status
    verb. To stay conservative (avoid false positives) we require the token to
    appear AND not be immediately followed by "recipe"/"keeper"/"run".

    The scan is by POSITION, not by token-list order: the assertion is whatever
    the prose LEADS with, and among tokens matching at that same position the
    LONGEST wins (so "CALIBRATED-WITH-CAVEATS" is never mis-read as its own
    "CALIBRATED" prefix). Scanning token-list-first instead — the pre-2026-08-17
    behaviour — let a determination token buried in a marker's deliberately
    preserved genealogy ("|| PRIOR TEXT, preserved: CALIBRATED-WITH-CAVEATS
    on <superseded run> …") outrank the entry's own leading claim, so an
    accurate marker could not be written without deleting its history. Rubric
    v3.3 made that live: two markers now lead with CALIBRATED over prior text
    that records the superseded CALIBRATED-WITH-CAVEATS reading.
    """
    text = definition or ""
    # (start, -len, token, end) — sorting puts earlier positions first and, at
    # equal position, the LONGEST token first, so each position is judged as
    # the longest token that starts there and never as its own prefix.
    matches = sorted(
        (m.start(), -len(tok), tok, m.end())
        for tok in _DET_TOKENS
        for m in re.finditer(re.escape(tok), text)
    )
    claimed: set[int] = set()
    for start, _, tok, end in matches:
        if start in claimed:
            continue  # a longer token already owns this position
        claimed.add(start)
        tail = text[end : end + 8].lower()
        if tail.lstrip().startswith(("recipe", "keeper", "run", "step")):
            continue  # names another run's recipe — and so does its prefix
        return tok
    return None


# Shard fields whose run id the SITE RESOLVES INTO A RUN-EXPLORER LINK. Each is
# copied out of the shard by ``build_status.py`` into ``status/<ISO>.js`` and
# rendered by ``calibration-status.js`` as a ``run-id-link`` href of the form
# ``backcast-runs.html#iso=<ISO>&run=<id>``; the set is derived from those render
# sites, not hand-picked. ``keeper`` is deliberately ABSENT — E1 already fails a
# keeper whose sidecar is missing, and duplicating it here would double-report.
LIVE_RUN_POINTERS: tuple[tuple[str, ...], ...] = (
    ("config_partition", "configs", "[]", "run_id"),
    ("holdout_touchpoint", "run_id"),
    ("standing_note", "probe_run_id"),
)


def _pointer_values(shard: dict, path: tuple[str, ...]) -> list[tuple[str, str]]:
    """Resolve one dotted ``LIVE_RUN_POINTERS`` path to its ``(label, run_id)`` hits."""
    nodes: list[tuple[str, object]] = [(path[0], shard.get(path[0]))]
    for seg in path[1:]:
        nxt: list[tuple[str, object]] = []
        for label, node in nodes:
            if seg == "[]":
                if isinstance(node, list):
                    nxt += [(f"{label}[{i}]", v) for i, v in enumerate(node)]
            elif isinstance(node, dict):
                nxt.append((f"{label}.{seg}", node.get(seg)))
        nodes = nxt
    return [(lbl, v) for lbl, v in nodes if isinstance(v, str) and v.strip()]


def dangling_pointer_findings(shard: dict, registry_dir: Path) -> list[str]:
    """Return E12 findings: LIVE shard run-id pointers with no registry sidecar.

    A keeper shard mixes two kinds of run-id citation and only one is a defect
    when it dangles:

    * **Live pointers** — the ``LIVE_RUN_POINTERS`` fields above, which the
      Calibration Status card renders as a clickable run link. A pruned target
      here is a DEAD LINK on the live site, and — the class this check was
      written for — a hand-authored ``holdout_touchpoint`` naming a pruned run
      can render a determination that CONTRADICTS the auto-derived
      per-year table printed directly beneath it (NEISO showed 2022 as
      CALIBRATED-WITH-CAVEATS above a ladder reading CALIBRATED; PJM showed
      two different 2022 C1/C3b numbers). Rule 30 [R-TOUCHPOINT-FOLD](b) is
      what such a block breaches — the ladder is derived precisely so it cannot
      go stale, and hand-authoring beside it re-introduces the staleness.

    * **Historical citations** — keeper genealogy (``superseded.former_keeper``
      and its ``chain``, ``de_designation_history``, ``frontier_withdrawn_*``,
      ``config_partition.configs[].source_run_id``) and the narrative prose
      fields. These name pruned runs BY DESIGN: rule 15's keeper-only retention
      makes pruning the norm, and the shards say in terms that such citations
      "now point at runs no longer on the site, deliberately ... NOTHING IS
      RETRACTED". Checking them would fight the retention discipline and red
      every lane — so they are OUT OF SCOPE here, permanently and on purpose.

    Args:
        shard: One ISO's parsed ``keepers/<ISO>.json``.
        registry_dir: The registry sidecar directory to resolve run ids against.

    Returns:
        One human-readable finding per dangling live pointer; empty when clean.
    """
    out: list[str] = []
    for path in LIVE_RUN_POINTERS:
        for label, run_id in _pointer_values(shard, path):
            if not (registry_dir / f"{run_id}.json").exists():
                out.append(
                    f"shard field {label} names {run_id}, which has no registry "
                    "sidecar — a dead run link on the Calibration Status card. "
                    "If the run was pruned (rule 15), DELETE the field rather "
                    "than re-authoring it: the derived per-year table already "
                    "carries the touchpoint rungs per year (rule 30(b))."
                )
    return out


class Report:
    """Accumulates FAIL/WARN/OK findings, grouped by keeper, for one audit run."""

    def __init__(self) -> None:
        self.findings: list[dict] = []

    def add(self, run_id: str, iso: str, level: str, code: str, msg: str) -> None:
        self.findings.append(
            {"run_id": run_id, "iso": iso, "level": level, "code": code, "msg": msg}
        )

    def ok(self, run_id, iso, code, msg):
        self.add(run_id, iso, "OK", code, msg)

    def warn(self, run_id, iso, code, msg):
        self.add(run_id, iso, "WARN", code, msg)

    def fail(self, run_id, iso, code, msg):
        # A keeper whose bundle + payload were never committed (verified 0
        # commits; scripts/lib/known_unsynced_keepers.py) cannot be audited: its
        # E1/E5/E8 findings are all consequences of the absent artifacts, not
        # keeper-text defects. Downgrade them to a tracked WARN so CI lands on
        # the current tree, while every OTHER keeper still FAILs normally. Not a
        # blanket ignore — scoped to exactly these ids until their bundles sync.
        if run_id in UNSYNCED_KEEPERS:
            self.add(run_id, iso, "WARN", code, f"{msg} [known-unsynced keeper]")
            return
        self.add(run_id, iso, "FAIL", code, msg)

    @property
    def n_fail(self) -> int:
        return sum(1 for f in self.findings if f["level"] == "FAIL")

    @property
    def n_warn(self) -> int:
        return sum(1 for f in self.findings if f["level"] == "WARN")


def _requirements_pins(req_path: Path) -> dict[str, str]:
    """Return ``{lowercased package: pinned version}`` from a requirements file.

    Only exact ``==`` pins are read; a range, a marker-only line, a comment or
    an unpinned name yields no entry, so a package this repo does not pin can
    never be reported as a mismatch. Pure over its input for testability.
    """
    pins: dict[str, str] = {}
    if not req_path.exists():
        return pins
    for raw in req_path.read_text().splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*==\s*([0-9][^\s;#]*)", raw.strip())
        if m:
            pins[m.group(1).lower()] = m.group(2)
    return pins


def solve_pin_findings(
    recorded: dict[str, str] | None, pins: dict[str, str]
) -> tuple[list[str], list[str]]:
    """Return E14 ``(mismatches, unverifiable)`` for one bundle's solve environment.

    ``recorded`` is the bundle's ``environment.packages`` — what the solve
    actually ran on — and ``pins`` is what ``requirements.txt`` currently pins.
    A keeper is the ISO's reference result, so the solver and numeric stack that
    produced it are part of its provenance; ``highspy`` most of all, since a
    different HiGHS is a different LP solver.

    This is the check whose absence let the nyiso-231 off-pin keeper reach the
    dashboard unremarked (``docs/FINDING-nyiso231-the-keeper-is-off-pin-2026-09-13.md``)
    — nothing else in this audit reads the environment block at all.

    Severity is WARN at the call site, never FAIL: an off-pin keeper is a
    provenance fact to surface, not grounds to retroactively invalidate a
    committed result, and a drifting pin would otherwise red every lane at once
    (rule 25 ``[R-ISO-SCOPE]``). Anything that cannot be compared — a bundle
    predating the ``environment`` block, or a package this repo does not pin —
    is returned as *unverifiable* rather than silently passed.

    Pure over its inputs so it is unit-testable without a bundle on disk.
    """
    if not recorded:
        return [], ["bundle records no environment.packages block"]
    mismatches: list[str] = []
    unverifiable: list[str] = []
    for pkg, got in sorted(recorded.items()):
        want = pins.get(str(pkg).lower())
        if want is None:
            unverifiable.append(f"{pkg} {got} (not pinned in requirements.txt)")
        elif str(got) != want:
            mismatches.append(f"{pkg} solved {got}, requirements.txt pins {want}")
    return mismatches, unverifiable


def orphan_run_findings(
    iso: str, keeper_id: str, registry_dir: Path
) -> tuple[list[str], list[int]]:
    """Return E13 findings: runs registered for ``iso`` that the keeper does not own.

    Rule 35 ``[R-PROMOTE]`` (f). After a promotion every run registered for an
    ISO is either its designated keeper or a run STAMPED to it
    (``holdout.keeper``, rule 30 ``[R-TOUCHPOINT-FOLD]`` (a)); anything else is
    a superseded run the promoting session failed to prune, and rule 15
    ``[R-DASHBOARD]``'s keeper-only retention says it should not be on the site.

    This is the gap the rule was written for: rule 15 deferred the sweep to
    "the next registration", nobody owned that, and on 2026-09-12 the dashboard
    carried 47 registered runs against 7 keepers while this audit passed clean
    — because no check looked at the ISO's registered SET, only at the keeper's
    own three stores (E1) and the shard's live pointers (E12).

    A **dangling** stamp counts as unstamped, deliberately: rule 30 (a) already
    treats one that way for rendering, so a run whose ``holdout.keeper`` names a
    since-pruned keeper is an orphan here too rather than a silent pass.

    Pure over its inputs so it is unit-testable without the live registry.

    Args:
        iso: The ISO whose registered set is being checked.
        keeper_id: That ISO's designated keeper run id.
        registry_dir: The registry sidecar directory to enumerate.

    Returns:
        ``(findings, years)`` — one human-readable finding per orphan run
        (empty when clean), and the sorted union of solve years over the
        keeper-owned runs, which is the year set rule 35 (b)/(c) require a
        promotion to preserve.
    """
    owned: list[tuple[str, dict]] = []
    orphans: list[tuple[str, str | None]] = []
    for path in sorted(registry_dir.glob("*.json")):
        rec = _load_json(path) or {}
        if (rec.get("iso") or "").upper() != iso.upper():
            continue
        run_id = rec.get("id", path.stem)
        if run_id == keeper_id:
            owned.append((run_id, rec))
            continue
        stamped = ((rec.get("holdout") or {}).get("keeper")) or None
        if stamped == keeper_id:
            owned.append((run_id, rec))
        else:
            orphans.append((run_id, stamped))

    findings = []
    for run_id, stamped in orphans:
        why = (
            f"stamped to {stamped}, which is not this ISO's keeper"
            if stamped
            else "not the keeper and stamped to no keeper"
        )
        findings.append(
            f"{run_id} is registered for {iso} but {why} — a superseded run "
            f"left behind a promotion. Prune it in the promoting session "
            f"(scripts/prune_iso_runs.py --iso {iso}), per rule 35 "
            f"[R-PROMOTE] (a); keep it only if it is a rung the keeper needs, "
            f"in which case stamp it to {keeper_id} (rule 30 (a))."
        )
    years: set[int] = set()
    for _, rec in owned:
        for y in rec.get("years") or []:
            if isinstance(y, int):
                years.add(y)
    return findings, sorted(years)


def audit_keeper(run_id: str, rep: Report) -> None:
    """Run every per-keeper check (E1–E10) for one run id, recording findings."""
    side_path = cv.REGISTRY_DIR / f"{run_id}.json"
    side = _load_json(side_path)
    if side is None:
        rep.fail(run_id, "?", "E1", f"missing/unreadable sidecar {side_path.name}")
        return
    iso = side.get("iso", "?")

    # E1: payload + bundle exist.
    payload = REPO / side.get("file", "")
    if not side.get("file") or not payload.exists():
        rep.fail(run_id, iso, "E1", f"run payload missing: {side.get('file')!r}")
    bundle = REPO / side.get("bundle", "")
    if not side.get("bundle") or not bundle.exists():
        rep.fail(run_id, iso, "E1", f"bundle dir missing: {side.get('bundle')!r}")
        flags = None
    else:
        rep.ok(run_id, iso, "E1", "sidecar, payload and bundle present")
        flags = _bundle_flags(bundle)
        meta = _load_json(bundle / "meta.json")

    # E14: solve-environment pin currency. WARN, never FAIL — see the module
    # header: an off-pin keeper is provenance to surface, not grounds to
    # retroactively invalidate a committed result, and a drifting pin would
    # otherwise red every lane at once (rule 25 [R-ISO-SCOPE]). Nothing else in
    # this audit reads the environment block, which is how the nyiso-231
    # off-pin keeper reached the dashboard unremarked.
    if flags is not None:
        env = (_load_json(bundle / "run_config.json") or {}).get("environment") or {}
        mismatches, unverifiable = solve_pin_findings(
            env.get("packages"), _requirements_pins(REPO / "requirements.txt")
        )
        for msg in mismatches:
            rep.warn(run_id, iso, "E14", msg)
        if not mismatches:
            n_pkgs = len(env.get("packages") or {})
            note = f"; unverifiable: {', '.join(unverifiable)}" if unverifiable else ""
            rep.ok(
                run_id,
                iso,
                "E14",
                f"solve environment on-pin ({n_pkgs} recorded package(s)){note}",
            )

    # E2 / E3: iso + years agree with the bundle the run was solved from.
    if flags is not None:
        if flags.get("iso") and flags["iso"] != iso:
            rep.fail(
                run_id, iso, "E2", f"sidecar iso={iso} but bundle iso={flags['iso']}"
            )
        else:
            rep.ok(run_id, iso, "E2", f"iso matches bundle ({iso})")
        side_years = sorted(side.get("years") or [])
        # meta.json["years"] is the authoritative solved span (what the verdict
        # scores and the dashboard renders); calibration_flags["years"] is an
        # invocation echo that some probe wrappers leave incomplete, so it is
        # only a cross-check, never the basis for a text-accuracy FAIL.
        meta_years = sorted((meta or {}).get("years") or [])
        flag_years = sorted(flags.get("years") or [])
        bundle_years = meta_years or flag_years
        if meta_years and flag_years and meta_years != flag_years:
            rep.warn(
                run_id,
                iso,
                "E3",
                f"bundle metadata inconsistent: meta.json years {meta_years} != "
                f"calibration_flags years {flag_years} (using meta.json)",
            )
        if bundle_years and side_years != bundle_years:
            rep.fail(
                run_id,
                iso,
                "E3",
                f"sidecar years {side_years} != bundle years {bundle_years}",
            )
        elif iso in _MULTI_YEAR_ISOS and len(side_years) < 2:
            rep.fail(
                run_id,
                iso,
                "E3",
                f"{iso} keeper covers only {side_years} — multi-year ISOs must "
                "register the full year span (claude.md #13)",
            )
        else:
            rep.ok(run_id, iso, "E3", f"years {side_years} match bundle")

    # E4: definition is real prose.
    definition = (side.get("definition") or "").strip()
    if not definition:
        rep.fail(run_id, iso, "E4", "definition is empty")
    elif _PLACEHOLDER_RE.match(definition):
        rep.fail(
            run_id,
            iso,
            "E4",
            "definition is the auto-generated placeholder "
            f'("{definition[:60]}…") — describe what the run actually changed',
        )
    else:
        rep.ok(run_id, iso, "E4", "definition is descriptive prose")

    # E5: definition's asserted determination matches the live verdict.
    try:
        verdict = cv.determine(run_id)
        live_det = verdict["determination"]
    except Exception as exc:  # scoring failure is itself a finding
        rep.fail(run_id, iso, "E5", f"verdict could not be computed: {exc}")
        live_det = None
    if live_det is not None:
        asserted = _asserted_determination(definition)
        if asserted and asserted != live_det:
            rep.fail(
                run_id,
                iso,
                "E5",
                f'definition asserts "{asserted}" but current verdict is '
                f'"{live_det}" — update the sidecar text',
            )
        else:
            note = f" (text says {asserted})" if asserted else ""
            rep.ok(run_id, iso, "E5", f"verdict {live_det}{note}")

    # E8: DOF ledger (CLAUDE.md rule 20 / audit D-12): the attestation must
    # carry a free_parameters section, and every residual-sourced parameter
    # must reference an open root cause — a residual that can only be closed
    # by a tuned value is an open root-cause issue, not a parameter.
    if side.get("bundle") and (REPO / side["bundle"]).exists():
        att = _load_json(REPO / side["bundle"] / "calibration_attestation.json")
        ledger = (att or {}).get("free_parameters")
        if ledger is None:
            rep.fail(
                run_id,
                iso,
                "E8",
                "attestation carries no free_parameters DOF ledger — seed it "
                "with scripts/build_dof_ledger.py (CLAUDE.md rule 20)",
            )
        else:
            bare = [
                e.get("name", "?")
                for e in ledger.get("entries", [])
                if e.get("identification") == "residual"
                and not str(e.get("root_cause", "")).strip()
            ]
            if bare:
                rep.fail(
                    run_id,
                    iso,
                    "E8",
                    "residual-sourced free parameter(s) without an open "
                    f"root-cause reference: {', '.join(bare)}",
                )
            else:
                n_res = sum(
                    1
                    for e in ledger.get("entries", [])
                    if e.get("identification") == "residual"
                )
                rep.ok(
                    run_id,
                    iso,
                    "E8",
                    f"DOF ledger present ({len(ledger.get('entries', []))} "
                    f"entries, {n_res} residual, all with root causes)",
                )

        # E10: attestation completeness — the blocks E8 does NOT look at
        # (schema / governance / exceptions). Added by caiso-189 (2026-08-11):
        # the caiso-188 promotion shipped a free_parameters-only attestation,
        # which E8 passed while C6 read UNATTESTED and the C3c exceptions ledger
        # was silently empty. Evaluated on the SAME `att` E8 loaded.
        level, msg = attestation_shape_finding(att)
        {"OK": rep.ok, "WARN": rep.warn, "FAIL": rep.fail}[level](
            run_id, iso, "E10", msg
        )

    # E9: ablation-twin link integrity (CLAUDE.md rule 20, owner amendment
    # 2026-07-14). The twin itself is optional — absence is OK; only a DECLARED
    # "ablation_twin" sidecar link that does not resolve FAILs.
    level, msg = ablation_twin_finding(run_id, side, cv.REGISTRY_DIR)
    {"OK": rep.ok, "WARN": rep.warn, "FAIL": rep.fail}[level](run_id, iso, "E9", msg)


def audit(isos: list[str] | None) -> Report:
    """Audit every keeper in the sharded store (optionally filtered to ``isos``)."""
    rep = Report()
    keeper_map = keeper_store.keeper_ids()
    if not keeper_map:
        rep.fail("-", "-", "E0", f"no keepers found in {keeper_store.keepers_dir()}")
        return rep

    # E6: exactly one keeper per ISO. Sharding makes multiplicity impossible by
    # construction (one keepers/<ISO>.json each); what can still break is a
    # shard whose keeper's registry sidecar claims a DIFFERENT iso — the wrong
    # lane — or two shards naming runs that resolve to the same sidecar iso.
    seen: dict[str, list[str]] = {}
    for shard_iso, run_id in keeper_map.items():
        side = _load_json(cv.REGISTRY_DIR / f"{run_id}.json")
        side_iso = (side or {}).get("iso", "?")
        seen.setdefault(side_iso, []).append(run_id)
        if side is not None and side_iso != shard_iso:
            rep.fail(
                run_id,
                shard_iso,
                "E6",
                f"keepers/{shard_iso}.json names {run_id}, but its sidecar says "
                f"iso={side_iso} — wrong lane",
            )
    for iso, ids in seen.items():
        if len(ids) > 1:
            rep.fail(ids[0], iso, "E6", f"{iso} has {len(ids)} keepers: {ids}")

    want = {s.upper() for s in isos} if isos else None
    for shard_iso, run_id in keeper_map.items():
        if want and shard_iso.upper() not in want:
            continue
        audit_keeper(run_id, rep)
        # E11: keeper-lineage recipe fidelity over the full solve kwarg
        # surface (the nyiso-108→155 silent-de-arm class), driven by the
        # shard's structured ``superseded.former_keeper`` record.
        shard = keeper_store.load_shard(shard_iso) or {}
        level, msg = lineage_recipe_finding(shard, cv.REGISTRY_DIR, REPO)
        {"OK": rep.ok, "WARN": rep.warn, "FAIL": rep.fail}[level](
            run_id, shard_iso, "E11", msg
        )
        # E12: referential integrity of the shard's LIVE run-id pointers —
        # the fields the Calibration Status card renders as run links. Keeper
        # genealogy and prose are out of scope by design (see the function).
        dangling = dangling_pointer_findings(shard, cv.REGISTRY_DIR)
        for msg in dangling:
            rep.fail(run_id, shard_iso, "E12", msg)
        if not dangling:
            rep.ok(
                run_id,
                shard_iso,
                "E12",
                "every live shard run-id pointer resolves to a registry sidecar",
            )
        # E13: keeper-only retention of the ISO's REGISTERED SET (rule 35
        # [R-PROMOTE] (f)) — every run registered for this ISO is the keeper or
        # stamped to it. E1/E12 look at the keeper's own stores and the shard's
        # live pointers; neither sees a superseded run a promotion left behind.
        orphans, years = orphan_run_findings(shard_iso, run_id, cv.REGISTRY_DIR)
        for msg in orphans:
            rep.fail(run_id, shard_iso, "E13", msg)
        if not orphans:
            rep.ok(
                run_id,
                shard_iso,
                "E13",
                f"registered set is keeper-only; years carried: {years}",
            )

    # H1: holdout quarantine across EVERY registered bundle (keeper or probe).
    if not any(f["code"] == "H1" for f in rep.findings):
        rep.ok(
            "holdout",
            "-",
            "H1",
            f"no registered bundle breaches the {sorted(CALIBRATION_YEARS)} "
            "holdout quarantine",
        )

    # M1: `complete`-marker currency + determination re-verification, scoped to
    # the audited ISOs (owner decision D-5(b), 2026-08-02). No solve — the
    # verdict is recomputed from committed artifacts.
    m1 = marker_currency_failures(isos)
    for iso, code, msg in m1:
        rep.fail("marker", iso, code, msg)
    if not m1:
        rep.ok(
            "marker",
            "-",
            "M1",
            "every audited 'complete' marker names its ISO's designated keeper and "
            "its determination re-verifies against that run (owner decision D-5(b))",
        )

    # S1: status-part sync check, scoped to the audited ISOs so a stale part
    # in ANOTHER lane can never fail this lane's audit (per-ISO isolation).
    cmd = [sys.executable, str(REPO / "scripts" / "build_status.py"), "--check"]
    if isos:
        cmd += ["--iso", *sorted({s.upper() for s in isos})]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        rep.ok("status", "-", "S1", proc.stdout.strip() or "status parts in sync")
    else:
        rep.fail(
            "status",
            "-",
            "S1",
            (proc.stdout + proc.stderr).strip()
            or "status part(s) stale — run scripts/build_status.py",
        )
    return rep


def _print_human(rep: Report) -> None:
    icons = {"OK": "✓", "WARN": "!", "FAIL": "✗"}
    # Group by run_id preserving first-seen order.
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for f in rep.findings:
        if f["run_id"] not in groups:
            order.append(f["run_id"])
            groups[f["run_id"]] = []
        groups[f["run_id"]].append(f)
    print("=" * 72)
    print("KEEPER TEXT AUDIT")
    print("=" * 72)
    for run_id in order:
        items = groups[run_id]
        iso = items[0]["iso"]
        worst = (
            "FAIL"
            if any(i["level"] == "FAIL" for i in items)
            else ("WARN" if any(i["level"] == "WARN" for i in items) else "OK")
        )
        print(f"\n[{icons[worst]}] {iso:6} {run_id}")
        for i in items:
            if i["level"] == "OK":
                continue  # keep the human view focused on problems
            print(f"      {icons[i['level']]} {i['code']}: {i['msg']}")
        if all(i["level"] == "OK" for i in items):
            print("      all checks passed")
    print("\n" + "-" * 72)
    verdict = "PASS" if rep.n_fail == 0 else "FAIL"
    print(f"{verdict}: {rep.n_fail} failure(s), {rep.n_warn} warning(s)")
    print("=" * 72)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--iso", nargs="+", help="restrict to these ISOs")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit 1 on any FAIL (same as default exit code)",
    )
    args = ap.parse_args()

    rep = audit(args.iso)
    if args.json:
        print(
            json.dumps(
                {"fail": rep.n_fail, "warn": rep.n_warn, "findings": rep.findings},
                indent=2,
            )
        )
    else:
        _print_human(rep)
    sys.exit(1 if rep.n_fail else 0)


if __name__ == "__main__":
    main()
