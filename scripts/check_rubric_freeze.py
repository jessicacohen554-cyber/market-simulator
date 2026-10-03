#!/usr/bin/env python3
"""CI guard — CLAUDE.md rule 37 ``[R-RUBRIC-FREEZE]``: the determination rubric
is frozen between promotions, so one PR never changes BOTH the rubric surface
and the keeper surface.

**The failure this prevents.** Between 2026-09-27 and 2026-10-02 the rubric
moved v3.10 → v3.17 — seven amendments in five days, each admitting a named
failing ISO-year cell to the caveat ledger (``docs/audit/2026-10/
C-data-calibration-governance.md`` §5 finding 3; genealogy in
``docs/governance/rule-history.md`` §23–§27). Nothing stopped an amendment from
landing in the same PR as the keeper it rescued, so the scorer and the thing
scored could move together and an external reader could not tell a keeper that
passed from a rubric that was widened until it did. The owner's ruling of
2026-10-03: *"Freeze the rubric between promotions: a rubric amendment is a
promotion decision, proposed in a PRECOMMIT and ruled on by the owner, never
landed in the same PR as a keeper."*

**What it checks (``--base <sha>`` diff mode).** Over ``git diff --name-only
<base>...HEAD`` (``<base> HEAD`` when the triple-dot form fails in a shallow
clone) it builds two sets:

* **A — rubric surface changed.** ``docs/calibration-determination-rubric.md``;
  ``scripts/calibration_verdict.py`` when any added/removed diff line names one
  of its rubric constants (``RUBRIC_SURFACE_IDENTIFIERS`` below: the version
  constant, the caveat budgets and ledger admissibility sets, the criterion
  bands, the forced-energy budget shares and the ``CRITERIA`` table); and any
  other ``scripts/`` or ``src/`` file whose diff DEFINES or MUTATES one of those
  names (a mirror or a re-pin — a read such as ``cv.TAIL_THRESHOLD[iso]`` is
  not a rubric edit). ``scripts/probes/`` and ``scripts/archive/``, the frozen
  per-run record, are exempt as they are from ruff.
* **B — keeper surface changed.** ``frontend/data/backcast/keepers/*.json``
  (keeper designation), ``frontend/data/backcast/status/*.js`` (status parts),
  ``frontend/data/backcast/calibration-complete.json`` (the forecast gate-(a)
  stamp) and anything under ``results/calibration/`` (keeper bundles).

A and B both non-empty → **FAIL** (exit 1), naming both lists and rule 37.
Either empty → ok (exit 0). Without ``--base`` there is no diff to gate, so
the script prints ``diff gate NOT RUN`` and exits 0, like
``check_mechanism_matrix.py`` — the gate is meaningful only on a PR.

**Escape hatch — the owner's promotion-with-amendment.** A PR label is not
visible here, so the override is the environment variable
``RUBRIC_FREEZE_OVERRIDE``, set to the owner's ruling citation (for example
``"owner ruling R-21, 2026-10-07, PRECOMMIT docs/records/soco/PRECOMMIT-…"``)
and passed ONLY by the CI step of the PR the owner has ruled may carry both.
When it is set the collision is printed, the citation is printed beside it,
and the exit code is 0. It is never set in the workflow by default: an
amendment proposed in a PRECOMMIT and ruled on lands in its own PR, and the
promotion it enables follows in the next one. The citation must match the
commit message's ruling citation (rule 37); the script cannot verify that, the
reviewer does.

Stdlib-only (argparse, re, subprocess) so it runs on a bare ``python3`` in CI
before ``uv sync``.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent

RULE = "CLAUDE.md rule 37 [R-RUBRIC-FREEZE]"
OVERRIDE_ENV = "RUBRIC_FREEZE_OVERRIDE"

RUBRIC_DOC = "docs/calibration-determination-rubric.md"

# The scorer's rubric constants (``scripts/calibration_verdict.py``). A diff
# line that adds or removes one of these names is a rubric-surface edit even
# when the file is not the scorer itself (a mirror, a generator, a test pin).
RUBRIC_SURFACE_IDENTIFIERS: tuple[str, ...] = (
    # version
    "RUBRIC_VERSION",
    # caveat budgets and ledger admissibility
    "MAX_LEDGERED_CAVEATS",
    "MAX_PROTECTIVE_CAVEATS",
    "LEDGERABLE_CRITERIA",
    "SCOPED_LEDGER_ENTRIES",
    "CONFIG_EXCEPTION_ENTRIES",
    "REFERENCE_COVERAGE_ENTRIES",
    "C3C_READING_LABELS",
    "LAMBDA_REFERENCED_ISOS",
    "REFERENCE_DEFINITION_CRITERIA",
    "C3C_NOT_SCORED",
    # criterion bands / thresholds
    "FUELMIX_VOL_LOAD_FRAC",
    "FUELMIX_VOL_CAP_TWH",
    "FUELMIX_SHARE_PP",
    "SYSVOL_TOL",
    "SYSVOL_COMMERCIAL",
    "SYSVOL_MIN_TWH",
    "DISP_MIN_TWH",
    "PRICE_MEAN_TOL",
    "PRICE_MEAN_COMMERCIAL",
    "PRICE_SHAPE_NRMSE_MAX",
    "PRICE_SHAPE_NRMSE_COMMERCIAL",
    "TAIL_THRESHOLD",
    "TAIL_SMALL_COUNT",
    "DISP_R_FLOOR",
    "DISP_NRMSE_MAX",
    "CO2_TOL",
    "CO2_COMMERCIAL",
    "PRICE_MONTH_COVERAGE_MIN",
    # forced-energy budget (C8 / rule 20)
    "PROTECTIVE_MIN_LOAD_FRAC",
    "FORCED_SHARE_PEAKER_MAX",
    "FORCED_SHARE_MERCHANT_MAX",
    # the criteria table itself
    "CRITERIA",
)

# Files whose diff lines are scanned for the identifiers above.
CODE_SURFACE_PREFIXES: tuple[str, ...] = ("scripts/", "src/")

# The keeper surface: designation, status parts, the gate-(a) stamp, bundles.
KEEPER_SURFACE_GLOBS: tuple[str, ...] = (
    "frontend/data/backcast/keepers/*.json",
    "frontend/data/backcast/status/*.js",
    "frontend/data/backcast/calibration-complete.json",
    "results/calibration/*",
    "results/calibration/**",
)

# The scorer itself: ANY added/removed line naming an identifier counts.
SCORER_REL = "scripts/calibration_verdict.py"

# The frozen per-run probe / retired-driver record (pyproject ``[tool.ruff]``
# scope note): never a live scorer surface, exempt here as there.
CODE_SURFACE_EXEMPT: tuple[str, ...] = ("scripts/probes/", "scripts/archive/")

# How many paths to print per set before eliding the rest.
LIST_CAP = 20

_IDENTS_ALT = "|".join(map(re.escape, RUBRIC_SURFACE_IDENTIFIERS))
# Any mention (used on the scorer's own diff).
_IDENT_RE = re.compile(rf"(?<![A-Za-z0-9_])(?:{_IDENTS_ALT})(?![A-Za-z0-9_])")
# A definition or mutation at the start of a diff line (used on every other
# file): ``NAME = …``, ``NAME: T = …``, ``NAME[k] = …``, ``NAME.update(…)``. A
# read (``cv.TAIL_THRESHOLD[iso]``, ``from … import TAIL_THRESHOLD``) is not a
# rubric edit.
_DEFINE_RE = re.compile(
    rf"^[+-]\s*({_IDENTS_ALT})\s*(?:\[[^\]]*\]\s*)?"
    r"(?::|=(?!=)|\.(?:update|append|add|pop|clear|setdefault)\()"
)


def _git(*args: str) -> str | None:
    """Run ``git <args>`` at the repo root; None when git fails."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, OSError):
        return None


def changed_files(base: str) -> list[str] | None:
    """``git diff --name-only base...HEAD``, falling back to the two-dot form.

    The triple-dot form diffs against the merge base, which a shallow CI clone
    may not hold; the two-dot form then compares the two commits directly.
    """
    out = _git("diff", "--name-only", f"{base}...HEAD")
    if out is None:
        out = _git("diff", "--name-only", base, "HEAD")
    if out is None:
        return None
    return sorted(line.strip() for line in out.splitlines() if line.strip())


def diff_touches_identifiers(base: str, rel: str) -> list[str]:
    """Rubric identifiers named on an added or removed line of ``rel``'s diff."""
    out = _git("diff", f"{base}...HEAD", "--", rel)
    if out is None:
        out = _git("diff", base, "HEAD", "--", rel)
    if out is None:
        return []
    any_mention = rel == SCORER_REL
    hits: set[str] = set()
    for line in out.splitlines():
        if not line or line[0] not in "+-" or line.startswith(("+++", "---")):
            continue
        if any_mention:
            hits.update(_IDENT_RE.findall(line))
        else:
            hits.update(_DEFINE_RE.findall(line))
    return sorted(hits)


def rubric_surface(base: str, files: list[str]) -> dict[str, list[str]]:
    """Set A: each changed rubric-surface file → the identifiers it touches."""
    hits: dict[str, list[str]] = {}
    for rel in files:
        if rel == RUBRIC_DOC:
            hits[rel] = ["(the rubric document)"]
            continue
        if not rel.startswith(CODE_SURFACE_PREFIXES) or not rel.endswith(".py"):
            continue
        if rel.startswith(CODE_SURFACE_EXEMPT):
            continue
        idents = diff_touches_identifiers(base, rel)
        if idents:
            hits[rel] = idents
    return hits


def keeper_surface(files: list[str]) -> list[str]:
    """Set B: changed files on the keeper surface."""
    return [
        f for f in files if any(fnmatch.fnmatch(f, g) for g in KEEPER_SURFACE_GLOBS)
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", help="PR base sha; enables the diff gate")
    args = ap.parse_args(argv)

    if not args.base:
        print(
            "rubric-freeze: diff gate NOT RUN — pass --base <sha> to check that "
            "the rubric surface and the keeper surface do not change together "
            f"({RULE})"
        )
        return 0

    files = changed_files(args.base)
    if files is None:
        print(f"FAIL: git diff against {args.base} failed (ref not fetched?)")
        return 1

    a = rubric_surface(args.base, files)
    b = keeper_surface(files)

    if not a or not b:
        which = "rubric surface" if a else "keeper surface" if b else "neither surface"
        print(
            f"ok: {len(files)} changed file(s) vs {args.base[:12]}; "
            f"{which} changed, never both ({RULE})"
        )
        return 0

    override = os.environ.get(OVERRIDE_ENV, "").strip()
    verdict = "OVERRIDDEN" if override else "FAILED"
    print(f"\nrubric-freeze guard {verdict} ({RULE})\n")
    print(f"  A — rubric surface changed ({len(a)} file(s)):")
    for rel, idents in sorted(a.items())[:LIST_CAP]:
        print(f"    {rel}: {', '.join(idents)}")
    if len(a) > LIST_CAP:
        print(f"    … and {len(a) - LIST_CAP} more")
    print(f"  B — keeper surface changed ({len(b)} file(s)):")
    for rel in b[:LIST_CAP]:
        print(f"    {rel}")
    if len(b) > LIST_CAP:
        print(f"    … and {len(b) - LIST_CAP} more")
    if override:
        print(
            f"\n  {OVERRIDE_ENV} set by the CI step — owner's "
            f"promotion-with-amendment ruling: {override}\n"
            "  The commit message must cite the same ruling; the reviewer checks."
        )
        return 0
    print(
        "\n  The rubric is frozen between promotions. A rubric amendment is a\n"
        "  promotion decision: propose it in a PRECOMMIT with its zero-LP effect\n"
        "  on every registered ISO (calibration_verdict.py over the committed\n"
        "  bundles, before and after), land it on the owner's ruling cited in\n"
        "  the commit, in a PR that changes no keeper designation, keeper shard,\n"
        "  status part or calibration-complete.json. Split this PR: rubric\n"
        "  amendment first, promotion second. Only the owner's\n"
        f"  promotion-with-amendment ruling, passed as {OVERRIDE_ENV} by the CI\n"
        "  step, carries both in one PR."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
