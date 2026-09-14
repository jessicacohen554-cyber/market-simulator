"""Tests for audit_keepers E14 — solve-environment pin currency.

A keeper is its ISO's reference result, so which solver and numeric stack
produced it is part of its provenance — ``highspy`` above all, since a different
HiGHS is a different LP solver. Before this check, **nothing in ``audit_keepers``
read the ``environment`` block at all**, which is how the nyiso-231 off-pin
keeper reached the dashboard unremarked
(``docs/FINDING-nyiso231-the-keeper-is-off-pin-2026-09-13.md``). E1 checks the
keeper's three stores exist; E11 diffs the *recipe*; neither can see the
environment the recipe was solved in.

WHAT THIS GUARD PINS, and why each half matters:

* a recorded package whose version differs from the ``requirements.txt`` pin is
  REPORTED — the plain off-pin case the check exists for;
* a package the bundle records but this repo does **not** pin comes back as
  *unverifiable*, never as a mismatch. Silently passing it would claim a
  verification that did not happen; failing it would red every keeper the day
  someone adds a dependency without a pin;
* a bundle with no ``environment`` block at all is *unverifiable* too, not a
  pass. Bundles predate the block, and "no evidence" is not "on-pin";
* only exact ``==`` pins are read from the requirements file. A range or an
  unpinned name yields no entry, so a package this repo deliberately leaves
  loose can never be reported as drift;
* **severity lives at the call site and is WARN, never FAIL** — asserted here by
  the helper returning findings rather than raising, so an off-pin keeper
  surfaces as provenance without retroactively invalidating a committed result
  whose numbers are already on the site. A drifting pin is a repo-wide event;
  failing it would red six lanes that did nothing wrong (rule 25
  ``[R-ISO-SCOPE]``).

Measured green on all seven designated keepers when it was added (nyiso-234,
2026-09-14), so it lands as a no-op guard rather than a new blocker.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_keepers import (  # noqa: E402
    _requirements_pins,
    solve_pin_findings,
)

PINS = {"highspy": "1.14.0", "numpy": "2.4.6", "pandas": "3.0.3"}


def test_matching_versions_produce_no_findings() -> None:
    """The on-pin case: every recorded package equals its pin."""
    mismatches, unverifiable = solve_pin_findings(
        {"highspy": "1.14.0", "numpy": "2.4.6"}, PINS
    )
    assert mismatches == []
    assert unverifiable == []


def test_off_pin_solver_is_reported() -> None:
    """The nyiso-231 class: the LP was solved on a different HiGHS."""
    mismatches, _ = solve_pin_findings({"highspy": "1.11.0"}, PINS)
    assert len(mismatches) == 1
    assert "highspy" in mismatches[0]
    assert "1.11.0" in mismatches[0] and "1.14.0" in mismatches[0]


def test_every_off_pin_package_is_reported_not_just_the_first() -> None:
    """A stack that drifted in more than one place reports each one."""
    mismatches, _ = solve_pin_findings(
        {"highspy": "1.11.0", "numpy": "2.0.0", "pandas": "3.0.3"}, PINS
    )
    assert len(mismatches) == 2
    assert any("highspy" in m for m in mismatches)
    assert any("numpy" in m for m in mismatches)


def test_unpinned_package_is_unverifiable_never_a_mismatch() -> None:
    """A package the repo does not pin cannot be drift — it is unverified."""
    mismatches, unverifiable = solve_pin_findings({"pyarrow": "24.0.0"}, PINS)
    assert mismatches == []
    assert len(unverifiable) == 1
    assert "pyarrow" in unverifiable[0]


def test_missing_environment_block_is_unverifiable_not_a_pass() -> None:
    """Bundles predate the block; "no evidence" is not "on-pin"."""
    for recorded in (None, {}):
        mismatches, unverifiable = solve_pin_findings(recorded, PINS)
        assert mismatches == []
        assert len(unverifiable) == 1


def test_requirements_parser_reads_only_exact_pins(tmp_path: Path) -> None:
    """Ranges, comments, bare names and markers yield no pin."""
    req = tmp_path / "requirements.txt"
    req.write_text(
        "# a comment\n"
        "highspy==1.14.0\n"
        "numpy>=2.0\n"
        "pandas\n"
        "scipy==1.17.1  # trailing comment\n"
        "pydantic==2.13.4 ; python_version >= '3.11'\n"
        "\n"
    )
    pins = _requirements_pins(req)
    assert pins == {
        "highspy": "1.14.0",
        "scipy": "1.17.1",
        "pydantic": "2.13.4",
    }


def test_requirements_parser_tolerates_a_missing_file(tmp_path: Path) -> None:
    """A missing requirements file yields no pins rather than raising."""
    assert _requirements_pins(tmp_path / "nope.txt") == {}


def test_the_live_keepers_are_on_pin() -> None:
    """Every designated keeper on disk is on-pin — the state E14 landed in.

    Skips any keeper whose bundle is not hydrated in this container, so the
    test is meaningful under a partial data profile rather than vacuous.
    """
    import json

    from scripts import calibration_verdict as cv

    pins = _requirements_pins(REPO_ROOT / "requirements.txt")
    assert pins, "requirements.txt must carry exact pins for E14 to mean anything"

    checked = 0
    for shard in sorted((REPO_ROOT / "frontend/data/backcast/keepers").glob("*.json")):
        if shard.stem == "index":
            continue
        keeper_id = json.loads(shard.read_text()).get("keeper")
        side_path = cv.REGISTRY_DIR / f"{keeper_id}.json"
        if not keeper_id or not side_path.exists():
            continue
        bundle = json.loads(side_path.read_text()).get("bundle") or ""
        run_config = REPO_ROOT / bundle / "run_config.json"
        if not bundle or not run_config.exists():
            continue
        env = json.loads(run_config.read_text()).get("environment") or {}
        mismatches, _ = solve_pin_findings(env.get("packages"), pins)
        assert mismatches == [], (
            f"{shard.stem} keeper {keeper_id} is off-pin: {mismatches}"
        )
        checked += 1

    assert checked > 0, "no keeper bundle was hydrated — the assertion would be vacuous"
