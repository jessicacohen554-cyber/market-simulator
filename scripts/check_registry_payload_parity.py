"""CI gate: registry sidecars and run payloads must be in 1:1 parity.

`scripts/build_manifest.py` silently skips a `registry/<id>.json` sidecar
whose `runs/<id>.js` payload is absent (the "half-synced checkout" guard) —
that is the right behavior for an incomplete local checkout, but it means a
sidecar pushed WITHOUT its payload is invisible in the Run Explorer with no
error anywhere. This happened in practice: several probes (nyiso-54, nyiso-58,
pjm-84, pjm-85, caiso-66) were registered sidecar-only and never rendered
(2026-07 loading-issue investigation). This script makes that failure loud
instead of silent, and additionally catches dangling `ablation_twin` /
`ablation_of` cross-references (a link to a sidecar-only or nonexistent run).

It checks BOTH directions of the parity so retention can never leave a store
behind:

* sidecar -> payload: a `registry/<id>.json` with no `runs/<id>.js` (above).
* payload -> sidecar: a `runs/<id>.js` **orphan** with no `registry/<id>.json`.
  These arise when a sidecar is pruned without its payload — the exact drift
  `dashboard_add_run.py`'s three-store retention exists to prevent — leaving a
  dead payload committed forever (it is never rendered, since only registered
  runs appear in the manifest).

Since the Class-E retention rule's adoption (2026-08-16, closing BLOAT-2 —
rule text: `frontend/data/backcast/keepers/README.md`) it also sweeps the
THIRD retention store, per the rule's point 4:

* bundle -> sidecar: a top-level `results/calibration/<bundle>/` DIRECTORY
  that no retained registry sidecar's `bundle` field maps and that is not
  otherwise keep-required (`check_bundle_retention`). Retention
  (`dashboard_add_run.prune_iso`) deletes sidecar + payload + bundle
  together, so an unmapped bundle dir is the last drift channel — dead solve
  output committed forever with nothing rendering or scoring it. The rule
  asked for a quarterly sweep; living in this always-on CI gate is a strict
  superset of that cadence.

It also asserts the namespace BOUNDARY (audit FR-24, added by FFR-1D): a
forecast-family run — T1-F / T1-X / T1-H / crossover / CES-POC / readiness —
must never be registered into the backcast registry. Those runs belong to the
separate forecast namespace (`frontend/data/forecast/**`, registered via
`scripts/register_forecast_run.py`), and CLAUDE.md rule 15 plus forecast plan
§7.5 say the two never mix: a forecast run in the backcast registry would put a
2026-2050 solve in front of `audit_keepers` and the rule-22 quarantine gates,
which reason about calibration years. The check reads only the backcast entry's
OWN fields — it never opens the forecast namespace, so the backcast gates stay
blind to it exactly as §7.5 requires.

Usage: ``python scripts/check_registry_payload_parity.py`` (exit 1 on any gap).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import keeper_store  # noqa: E402  (after sys.path insert)
from scripts.lib.known_unsynced_keepers import (  # noqa: E402
    UNSYNCED_RUN_PAYLOADS,
)

REGISTRY_DIR = ba.REGISTRY
RUNS_DIR = ba.RUNS

# --- the CLASS-LEVEL carve-out (B-8 / audit board checklist item 10) -------
#
# Two classes of artifact under `results/calibration/` are SUPPOSED to exist
# before any sidecar does, so the point-4 sweep fires on them by design:
# pre-registered campaign POINTS and replay RECIPE dirs. Before this carve-out
# the only relief was `KEEP_REQUIRED_UNMAPPED_BUNDLES`, a hand-maintained
# allowlist that grew one to three entries per A/B session (40 entries by
# 2026-09-01, up from the 26 the audit board last counted) — so the gate's
# green was a maintenance state, not a property, and its own docstring's
# warning that a stale entry is "a re-armable hole" was on the way to coming
# true (`nyiso147_control` was named here after its dir was already gone).
# `results/calibration/FINDING-ws6-parity-nyiso-recipe-dirs-2026-08-20.md` §5
# recommended replacing the enumeration with a structural test; this is it.
#
# WHAT IS ADMITTED — both conjuncts required, in both classes:
#
#   (1) The dir carries NO SOLVE OUTPUT. Not "few files", not "small": none of
#       `metrics.json`, `calibration_attestation.json`,
#       `legitimacy_diagnostics.json`, and no `*.parquet` / `*.npz`. Point 4's
#       stated target is "dead solve output committed forever with nothing
#       rendering or scoring it"; a dir holding no solve output is not the
#       thing the rule is about. This is what keeps the carve-out honest — a
#       real abandoned bundle always carries solve output and can never enter.
#   (2) A COMMITTED RECORD names it. Class R (a recipe dir) must be named by
#       dir name; class P (a campaign point) must have its point-score marker
#       FILENAME named, because the pre-registration records the campaign and
#       its record file, not each of ten grid points. This is the "cited by a
#       committed record" test the `miso170_layup_A/B` entries were already
#       kept on, promoted from a prose justification to code.
#
# The two classes, derived from the allowlist comments' own stated reasons:
#
#   * **Class R — replay-recipe dir.** Its ONLY file is `meta.json`.
#     `run_calibration_full.run_replay_bundle` reads nothing else, so a
#     one-file dir is a COMPLETE and valid `--replay-bundle` input by
#     construction — solve INPUT, not truncated output. Committed BEFORE its
#     arm solves (the NYISO lane's pre-registration discipline) and cited as
#     the sole input of a reproduction command in a committed PREREG/RESULT.
#   * **Class P — pre-registered campaign point.** Carries a
#     `*_point_score.json` marker: the machine-readable per-point record a
#     kill-gated grid campaign commits for its non-winner points (the winner
#     registers the ordinary way). The heavy bundle contents are gitignored by
#     the campaign's own scratch rule, so the marker plus its sibling record
#     JSONs are the whole committed artifact.
#
# WHAT IS NOT ADMITTED, and why a looser rule re-creates the dead-bundle class:
#
#   * A dir with solve output — parquet, metrics, an attestation — NEVER
#     enters, however it is named or cited. Dropping conjunct (1) and keeping
#     only the citation test would admit every abandoned control and A/B arm
#     that any doc happens to mention, which is precisely the dead solve
#     output point 4 exists to sweep.
#   * A record-free dir NEVER enters. Dropping conjunct (2) would admit any
#     stray `meta.json` or point-score file, so an abandoned lane's litter
#     would exempt itself — an allowlist with no keeper of the list.
#   * A dir is NOT admitted for being named `*_control` / `*_recipe` / for
#     living under a campaign prefix. Naming patterns are not evidence; a
#     batch-prune keyed to `_recipe` is what the 2026-08-20 finding was
#     written to stop.
#
# NOT A PRE-MERGE CHECK, deliberately (finding §5.3). Nothing here is made
# stricter or earlier. A pre-registered artifact is legitimately unmapped for
# hours or days while its lane is mid-flight, so an earlier gate would block
# correct pre-registration commits and train lanes to skip it — the opposite
# of what the program wants. The defect was in the classifier, not the timing.

#: Files that exist only because a solve wrote them. Presence of ANY of these
#: (or of a `*.parquet` / `*.npz`) makes a dir solve OUTPUT, which no
#: class-level carve-out admits.
SOLVE_OUTPUT_NAMES: frozenset[str] = frozenset(
    {"metrics.json", "calibration_attestation.json", "legitimacy_diagnostics.json"}
)
SOLVE_OUTPUT_SUFFIXES: tuple[str, ...] = (".parquet", ".npz")

#: The one file `run_replay_bundle` reads — a dir holding only this is a
#: complete replay INPUT (class R).
REPLAY_RECIPE_FILE = "meta.json"

#: Marker naming the per-point record a pre-registered grid campaign commits
#: (class P): `<campaign>_point_score.json`.
POINT_SCORE_SUFFIX = "_point_score.json"

#: Committed-record corpus the citation conjunct is tested against. Both roots
#: hold the program's PREREG / PRECOMMIT / RESULT / FINDING / ASSESSMENT
#: records; the ERCOT campaign records live under `docs/`, the NYISO lane's
#: under `results/calibration/`, so both are needed. Read cost measured
#: 2026-09-01: 1,824 files / 34.9 MB / 0.14 s.
RECORD_DOC_ROOTS: tuple[tuple[str, str], ...] = (
    ("results/calibration", "*.md"),
    ("docs", "**/*.md"),
)

# Class-E retention rule point 4 (keepers/README.md): keep-required bundle
# dirs that legitimately hold NO retained sidecar mapping, AND that the
# class-level carve-out above does not already admit. What is left here after
# the 2026-09-01 classifier repair is the genuinely one-off residue: FULL
# bundles (solve output present, so conjunct (1) excludes them by design)
# kept on a case-by-case justification — in-flight controls and bit-identical
# replication arms. Every entry names the top-level dir and carries a reason
# comment; a stale entry is a re-armable hole in the gate (delete it when the
# bundle goes). Empty at adoption (2026-08-16): every non-`_` dir on the tree
# was sidecar-mapped.
KEEP_REQUIRED_UNMAPPED_BUNDLES: frozenset[str] = frozenset(
    {
        # miso-170b independent-replication evidence (2026-08-19): this pair
        # was solved concurrently with — and verified BIT-IDENTICAL to — the
        # registered miso170_membership_A/B (probe --identity, max|diff|=0 on
        # every scored sidecar of every year). Their duplicate registrations
        # were reconciled away in favour of the canonical ids, but the bundles
        # are cited by the 2026-08-19-miso-170-sitegrain keeper's promotion
        # note and RESULT-miso170b-sitegrain-execution-2026-08-19.md as the
        # replication record (which also proves the intervening merges
        # MISO-inert), so they legitimately outlive their sidecars.
        "miso170_layup_A",
        "miso170_layup_B",
        # RETIRED 2026-09-01 (audit checklist item 10) — the ercot-235
        # 2023-discrete offer-sweep grid points (r1-r9, r11) and the ercot-236
        # h4097 shed-repair points (diag_k30, k24_clip, k27_clip, k30_clip) are
        # now admitted STRUCTURALLY as class P: each carries a committed
        # `*_point_score.json` marker, no solve output at all, and its marker
        # filename is named by the campaign's own committed PRECOMMIT/FINDING.
        # Their reasons are unchanged; they are simply no longer enumerated.
        # A future campaign point needs no entry here.
        # caiso-224 FSNO arc, MID-CONCLUSION (2026-08-30) — INTERIM ENTRIES.
        # Both dirs are deliberate artifacts of an arc that has not yet reached
        # its verdict, so they must outlive their absent sidecars until it does.
        #  * caiso224_a0_control (fd428d8 "A0 control complete: G-CTRL BIT-ZERO
        #    vs the committed caiso-220 keeper sidecars"; 4213c90 legitimacy
        #    diagnostics; 183a690 + d112f1e hourly checkpoints) is the G-CTRL
        #    control arm, reconciled BIT-ZERO against the committed caiso-220
        #    keeper sidecars. Being bit-identical to an already-registered run,
        #    it is deliberately NOT registered a second time — the miso170_layup
        #    precedent above, same reasoning, same class.
        #  * caiso224_b1_fsno (3ec3549 + 63a5678 hourly checkpoints; completed
        #    by 7f84d8a "B1 arm complete: bundle slim files + split-witness/
        #    F1-F2 artifact", PR #4395) is COMPLETE but its verdict and
        #    registration had not landed when this gate repair was dispatched;
        #    its falsifier probe was pre-registered at 995eedb.
        # INTERIM: these two entries are the caiso-224 continuation's to remove.
        # That session registers or prunes both bundles at arc conclusion and
        # deletes these lines in the same change — a stale entry here is a
        # re-armable hole in the gate.
        "caiso224_a0_control",
        "caiso224_b1_fsno",
        # --- NYISO A/B CONTROL BUNDLES (ws6-parity-repair, 2026-08-20) -----
        # RETIRED 2026-09-01 (audit checklist item 10): the SEVENTEEN one-file
        # `*_recipe` dirs formerly enumerated here (nyiso-144/146/146b/146c/
        # 147/148/149/150/151/152/153/154) are now admitted STRUCTURALLY as
        # class R — their only file is `meta.json`, so they carry no solve
        # output, and each is named by a committed PREREG/RESULT reproduction
        # command. This is the structural fix
        # `FINDING-ws6-parity-nyiso-recipe-dirs-2026-08-20.md` §5.1 asked for,
        # and it is why this list stops growing one arm at a time. Their
        # justifications are unchanged and live in that finding; a future
        # recipe dir needs no entry here.
        #
        # `nyiso147_control` was ALSO removed — its dir no longer exists on
        # the tree at all (verified against `origin/main` 2026-09-01), so the
        # entry was exactly the "re-armable hole in the gate" this list's own
        # comment warns about.
        #
        # WHAT REMAINS is the residue the class deliberately does not admit:
        # FULL A/B control and replication bundles, which DO carry solve
        # output (hourly parquet + diagnostics) and so fail conjunct (1) by
        # design. Each is kept on its own case-by-case justification.
        #
        # `nyiso150_control` (session nyiso-150) is the A/B reference arm:
        # verified byte-identical to the keeper (IDENT gate, max |dprice| =
        # 0.0 over every zone-hour ×3 years, _nyiso150_ab_gates.json) and
        # deliberately NOT registered (the nyiso-149 base-replay convention);
        # its slim files + hourly sidecars + regenerated diagnostics (the D-4
        # vintage-guard live verification) are committed, and every C-K/W-K
        # gate is defined vs it.
        "nyiso150_control",
        #
        # session nyiso-151 (PREREG-nyiso151-egrid-identity-hr-and-regate-
        # 2026-08-22.md). ARM HC is deliberately NOT registered — it is
        # BIT-IDENTICAL to the registered 2026-08-22-nyiso-150-reserve-rearm
        # (max |dprice| = 0.0 x3 years, _nyiso151_ab_gates.json) and a second
        # registration of identical bytes would be a double entry (the
        # nyiso-149 convention); its committed bundle is the replication
        # record the RESULT cites. `nyiso151_control` is the IDENT reference
        # arm at the post-merge HEAD (proven == the 149 keeper), the baseline
        # every H/HC gate is defined against. REMOVAL CONDITION: the citing
        # PREREG/RESULT docs are retired or re-pointed at registered bundles.
        "nyiso151_armHC",
        "nyiso151_control",
        #
        # session nyiso-152 (PREREG-nyiso152-bridge-reserve-duty-exclusion-
        # 2026-08-22.md). `nyiso152_control` is the IDENT reference arm at the
        # post-#4203 HEAD (proven == the 151 keeper, max |dprice| = 0.0 x3
        # years, _nyiso152_ab_gates.json) and deliberately NOT registered (the
        # nyiso-149 base-replay convention); its slim files + hourly sidecars
        # + regenerated diagnostics are committed, and every SE-K gate is
        # defined vs it. REMOVAL CONDITION: the citing PREREG/RESULT docs are
        # retired or re-pointed at registered bundles.
        "nyiso152_control",
        # sessions nyiso-185 / 186 / 187 / 188 (2026-09-04): the same-HEAD
        # bit-identity controls of the four consecutive Astoria-lane A/Bs
        # (PREREG-nyiso185-stgas-family-hr-ab, PREREG-nyiso186-cc-regular-
        # 2024-class, PREREG-nyiso187-ct-steam-merit-position, PREREG-nyiso188-
        # astoria-footprint-cc-reconcile-bethlehem). Each is the replay of the
        # then-committed keeper recipe on the committed artifacts, proven
        # BIT-IDENTICAL to that keeper (0 of 52,560 hourly zonal prices differ
        # in every year) and deliberately NOT registered (the nyiso-149
        # base-replay convention: a control identical to a registered run is
        # never registered twice). Their slim files + hourly sidecars are the
        # instrument the committed attestation generators RE-READ (G-CONTROL in
        # scripts/gen_nyiso185_attestation.py, scripts/gen_nyiso186_attestation.py,
        # scripts/gen_nyiso187_attestation.py and scripts/gen_nyiso188_attestation.py
        # reads <control>/hourly/system_<year>.parquet against the keeper's), so the
        # keepers' C6 attestations are recomputable only while these dirs
        # carry their sidecars. REMOVAL CONDITION: the attestation generators
        # are retired or re-pointed at registered bundles.
        "nyiso185_control",
        "nyiso186_control",
        "nyiso187_control",
        "nyiso188_control",
        # session nyiso-189 (2026-09-05): the same-HEAD bit-identity control of
        # the B2 steam-collapse identity A/B (PREREG-nyiso189-steam-collapse-
        # identity-ab.md), the replay of the nyiso-188 keeper recipe on the
        # committed artifacts, proven BIT-IDENTICAL to that keeper (0 of 52,560
        # prices differ in every year) and deliberately NOT registered (the
        # same convention); scripts/gen_nyiso189_attestation.py re-reads its
        # hourly/system_<year>.parquet (G-CONTROL) and unit_hourly (G-ENGAGE).
        # REMOVAL CONDITION: the attestation generator is retired or
        # re-pointed at a registered bundle.
        "nyiso189_control",
    }
)

# Namespace-boundary vocabulary (FR-24). `kind`/`mode` are FORECAST-sidecar
# fields — a backcast registry entry has neither — so their presence with a
# forecast value is a registration that went to the wrong namespace.
FORECAST_KINDS = frozenset(
    {"t1f", "t1x", "t1h", "crossover", "hindcast", "ces-poc", "adequacy", "readiness"}
)
# Result-tree roots the forecast/hindcast harnesses write to. A backcast bundle
# lives under results/calibration/.
FORECAST_BUNDLE_PREFIXES = (
    "results/hindcast/",
    "results/full-horizon/",
    "results/crossover/",
    "results/ff-",
    "results/ces-",
)
BACKCAST_RUNS_PREFIX = "frontend/data/backcast/runs/"


def check_namespace_boundary(rid: str, rec: dict) -> list[str]:
    """Return problems if ``rec`` is a forecast-family run in the backcast registry.

    Args:
        rid: The run id.
        rec: The registry sidecar's parsed contents.

    Returns:
        A list of human-readable problems; empty when the entry is a backcast
        registration.
    """
    problems: list[str] = []
    remedy = (
        "Forecast-family runs register on the forecast namespace via "
        "scripts/register_forecast_run.py (CLAUDE.md rule 15; forecast plan "
        "§7.5 — the backcast gates must never see a forecast run)."
    )
    kind = rec.get("kind") or (rec.get("meta") or {}).get("kind")
    mode = rec.get("mode") or (rec.get("meta") or {}).get("mode")
    if kind in FORECAST_KINDS:
        problems.append(f"{rid}: kind={kind!r} is a FORECAST run kind. {remedy}")
    if mode == "forecast":
        problems.append(f"{rid}: mode='forecast' in the BACKCAST registry. {remedy}")
    bundle = str(rec.get("bundle") or "")
    if bundle.startswith(FORECAST_BUNDLE_PREFIXES):
        problems.append(
            f"{rid}: bundle {bundle!r} is under a forecast/hindcast results "
            f"root. {remedy}"
        )
    file_ref = str(rec.get("file") or "")
    if file_ref and not file_ref.startswith(BACKCAST_RUNS_PREFIX):
        problems.append(
            f"{rid}: file {file_ref!r} points outside "
            f"{BACKCAST_RUNS_PREFIX} — a backcast payload lives there. {remedy}"
        )
    return problems


def _has_solve_output(bundle: Path) -> bool:
    """Whether ``bundle`` holds any file only a solve could have written.

    Conjunct (1) of the class-level carve-out. Recursive, because a bundle's
    hourly sidecars live under ``hourly/``.

    Args:
        bundle: A top-level ``results/calibration/<name>`` directory.

    Returns:
        True if any committed file is solve output.
    """
    for path in bundle.rglob("*"):
        if not path.is_file():
            continue
        if path.name in SOLVE_OUTPUT_NAMES:
            return True
        if path.suffix in SOLVE_OUTPUT_SUFFIXES:
            return True
    return False


def record_corpus(repo: Path | None = None) -> str:
    """Read the committed PREREG / PRECOMMIT / RESULT / FINDING record corpus.

    Conjunct (2) of the class-level carve-out is a substring test against this
    text. Both roots in :data:`RECORD_DOC_ROOTS` are needed: the ERCOT campaign
    records live under ``docs/``, the NYISO lane's under
    ``results/calibration/``.

    Args:
        repo: Repo root override (tests); defaults to this checkout.

    Returns:
        Every record document's text, concatenated. Unreadable files are
        skipped — an unreadable doc must never widen the carve-out.
    """
    repo = repo or REPO
    chunks: list[str] = []
    for root, pattern in RECORD_DOC_ROOTS:
        base = repo / root
        if not base.is_dir():
            continue
        for path in sorted(base.glob(pattern)):
            try:
                chunks.append(path.read_text(errors="replace"))
            except OSError:
                continue
    return "\n".join(chunks)


def _is_cited(token: str, corpus: str) -> bool:
    """Whether ``token`` is named in the record corpus as a whole identifier.

    The delimiter guard matters: without it ``ercot235_r1`` would match inside
    ``ercot235_r10``, so a pruned point could be excused by its neighbour's
    citation.

    Args:
        token: A directory name or a marker filename.
        corpus: Text from :func:`record_corpus`.

    Returns:
        True when the corpus names the token exactly.
    """
    return re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", corpus) is not None


def classify_prereg_artifact(bundle: Path, corpus: str) -> str | None:
    """Class-level carve-out: is ``bundle`` a pre-registered non-output artifact?

    Implements the two admissible classes documented at
    :data:`KEEP_REQUIRED_UNMAPPED_BUNDLES` — class R (a ``--replay-bundle``
    recipe dir) and class P (a pre-registered campaign point). Both require
    that the dir carry NO solve output AND that a committed record name it, so
    a dead bundle with solve output, or an uncited stray, is never admitted.

    Args:
        bundle: A top-level ``results/calibration/<name>`` directory.
        corpus: Text from :func:`record_corpus`.

    Returns:
        A short reason string naming the class, or ``None`` when the dir is
        not admitted and must be judged the ordinary way.
    """
    files = [p for p in bundle.rglob("*") if p.is_file()]
    if not files:
        return None  # an EMPTY dir is litter, not a pre-registered artifact
    if _has_solve_output(bundle):
        return None  # conjunct (1): solve output is never carved out

    names = [p.name for p in files]

    # Class R — the only file is `meta.json`, a complete replay INPUT.
    if names == [REPLAY_RECIPE_FILE] and _is_cited(bundle.name, corpus):
        return (
            "class R: replay-recipe dir (meta.json only), named by a committed record"
        )

    # Class P — a pre-registered campaign point, identified by its marker.
    markers = sorted(n for n in names if n.endswith(POINT_SCORE_SUFFIX))
    for marker in markers:
        if _is_cited(marker, corpus):
            return f"class P: pre-registered campaign point (carries {marker}, named by a committed record)"
    return None


def check_bundle_retention(
    sidecars: dict[str, dict], *, repo: Path | None = None
) -> tuple[list[str], int]:
    """Class-E retention rule point 4: sweep `results/calibration/` bundle dirs.

    Fails any top-level DIRECTORY under `results/calibration/` that no
    retained sidecar's `bundle` field maps and that is not keep-required
    (rule text: `frontend/data/backcast/keepers/README.md`). Keep-required
    carve-outs, in the order tested:

    * `_`-prefixed dirs — the §5.2 working/archive dirs
      (`docs/bloat-removal-plan-2026-08.md` §5.2, citation-checked KEEP);
      never run bundles.
    * dirs a `results/regression-goldens/*/manifest.json` capture record
      references in a `keepers.<ISO>.bundle` field.
    * the documented `KEEP_REQUIRED_UNMAPPED_BUNDLES` allowlist (a
      keep-required bundle that legitimately outlives its sidecar).
    * the CLASS-LEVEL carve-out (:func:`classify_prereg_artifact`): a
      pre-registered artifact that carries no solve output AND is named by a
      committed record — a replay-recipe dir (class R) or a campaign point
      (class P). This replaced 31 of the allowlist's 39 live entries on
      2026-09-01; see :data:`KEEP_REQUIRED_UNMAPPED_BUNDLES` for exactly what
      it does and does not admit.

    Out of scope by construction: root-level loose records (files, not
    dirs), and the `results/hindcast/` / `results/regression-goldens/`
    roots (different trees). The current keeper, ablation-referenced and
    structural-prior bundles need no carve-out here — the prune immunity
    keeps their sidecars retained, so they are mapped the ordinary way.

    Args:
        sidecars: Parsed retained registry sidecars, keyed by run id.
        repo: Repo root override (tests); defaults to this checkout.

    Returns:
        ``(problems, swept)`` — human-readable failures, and how many bundle
        dirs the sweep examined. An absent `results/calibration/` (partial
        checkout) sweeps nothing and returns no problems, mirroring the
        RUNS_DIR guard.
    """
    repo = repo or REPO
    calib_root = repo / "results" / "calibration"
    goldens_root = repo / "results" / "regression-goldens"
    if not calib_root.is_dir():
        return [], 0

    mapped: set[str] = set()
    for rec in sidecars.values():
        b = ba.bundle_dir_for(rec, repo=repo, calib_root=calib_root)
        if b is None:
            continue  # no bundle field, or outside the root (safety guard)
        rel = b.resolve().relative_to(calib_root.resolve())
        if rel.parts:  # a sidecar may map a nested path; the dir is top-level
            mapped.add(rel.parts[0])

    golden_refs: set[str] = set()
    for manifest in sorted(goldens_root.glob("*/manifest.json")):
        try:
            doc = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue  # unreadable capture record never widens the carve-out
        for entry in (doc.get("keepers") or {}).values():
            raw = str((entry or {}).get("bundle") or "")
            parts = Path(raw).parts
            if parts[:2] == ("results", "calibration") and len(parts) > 2:
                golden_refs.add(parts[2])

    problems: list[str] = []
    swept = 0
    corpus: str | None = None  # read lazily: only an unmapped dir needs it
    for path in sorted(p for p in calib_root.iterdir() if p.is_dir()):
        name = path.name
        if name.startswith("_"):
            continue
        swept += 1
        if name in mapped or name in golden_refs:
            continue
        if name in KEEP_REQUIRED_UNMAPPED_BUNDLES:
            continue
        if corpus is None:
            corpus = record_corpus(repo)
        if classify_prereg_artifact(path, corpus) is not None:
            continue
        problems.append(
            f"results/calibration/{name}: bundle dir maps to no retained "
            f"sidecar `bundle` field and is not keep-required — dead solve "
            f"output (Class-E retention rule point 4, "
            f"frontend/data/backcast/keepers/README.md). Either register "
            f"it, prune it (dashboard_add_run.prune_iso deletes the three "
            f"stores together), or record why it must outlive its sidecar "
            f"in KEEP_REQUIRED_UNMAPPED_BUNDLES."
        )
    return problems, swept


def main() -> int:
    problems: list[str] = []
    # Pre-existing sidecar-only registrations whose payloads were never
    # committed (scripts/lib/known_unsynced_keepers.py). Reported as tracked
    # warnings so this gate stays green for unrelated PRs; any OTHER missing
    # payload still fails. Not a blanket ignore.
    warnings: list[str] = []
    sidecars: dict[str, dict] = {}
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{path.name}: invalid JSON ({exc})")
            continue
        rid = rec.get("id", path.stem)
        sidecars[rid] = rec
        problems.extend(check_namespace_boundary(rid, rec))
        if not (RUNS_DIR / f"{rid}.js").exists():
            msg = (
                f"{path.name}: registry sidecar has no matching "
                f"runs/{rid}.js payload — invisible in the Run Explorer"
            )
            (warnings if rid in UNSYNCED_RUN_PAYLOADS else problems).append(msg)

    # payload -> sidecar: an orphan runs/<id>.js with no registry sidecar. A
    # sidecar pruned without its payload leaves this dead file committed
    # forever; retention (dashboard_add_run.prune_iso) deletes both together, so
    # any orphan here is a parity break to fix.
    if RUNS_DIR.exists():
        for path in sorted(RUNS_DIR.glob("*.js")):
            rid = path.stem
            if rid not in sidecars:
                problems.append(
                    f"runs/{path.name}: orphan payload has no registry/{rid}.json "
                    f"sidecar — dead file, never rendered"
                )

    for rid, rec in sidecars.items():
        for field in ("ablation_twin", "ablation_of"):
            ref = rec.get(field)
            if not ref or not ref.startswith("20"):  # skip prose placeholders
                continue
            if ref not in sidecars:
                problems.append(f"{rid}: {field} -> {ref!r} has no registry sidecar")
            elif not (RUNS_DIR / f"{ref}.js").exists():
                problems.append(
                    f"{rid}: {field} -> {ref!r} has a sidecar but no runs/{ref}.js payload"
                )

    for iso, rid in keeper_store.keeper_ids().items():
        if rid not in sidecars:
            problems.append(
                f"keepers/{iso}.json: keeper {rid!r} has no registry sidecar"
            )
        elif not (RUNS_DIR / f"{rid}.js").exists():
            msg = f"keepers/{iso}.json: keeper {rid!r} has no runs/{rid}.js payload"
            (warnings if rid in UNSYNCED_RUN_PAYLOADS else problems).append(msg)

    # bundle -> sidecar (Class-E retention rule point 4).
    bundle_problems, swept_bundles = check_bundle_retention(sidecars)
    problems.extend(bundle_problems)

    if warnings:
        print(
            "registry/payload parity: known-unsynced runs (tracked, not a gate "
            "failure — see scripts/lib/known_unsynced_keepers.py):",
            file=sys.stderr,
        )
        for w in warnings:
            print(f"  ! {w}", file=sys.stderr)

    if problems:
        print("registry/payload parity FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(
        f"registry/payload parity OK ({len(sidecars)} runs checked, "
        f"{swept_bundles} bundle dirs swept, "
        f"{len(warnings)} known-unsynced tolerated)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
