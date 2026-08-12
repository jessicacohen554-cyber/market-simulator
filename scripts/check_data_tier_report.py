"""Loud-failure guard for the scheduled data-provisioned test tier.

Reads the junit XML report the ``golden-data-tier.yml`` workflow produces and
enforces the two halves of card F's execution contract (owner signature F1,
2026-08-11, ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md``:
"the job must actually provision the data the tier needs or
skip-with-loud-failure if it cannot"):

1. **No data-missing skips.** A test skipped because a ``data/raw`` input or a
   ``data/clean`` partition is absent means the workflow's provisioning
   (sparse-checkout list / regenerate_clean slice) has a gap. ``requires_raw``
   skips are silent by design in the local lanes — here they FAIL, so the gap
   is fixed in the workflow instead of eroding the tier one skip at a time.

2. **The golden ran and passed.** ``test_fleet_arrays_golden`` went red on
   2026-07-26 and was carried as noise for fifteen days precisely because the
   fast tier's ``-m`` expression deselected it (FINDING-ercot187 §5). If a
   future marker/expression drift deselects it again, this guard turns that
   silence into a red run.

Usage::

    python3 scripts/check_data_tier_report.py tier-report.xml

Stdlib-only (CI cost policy): no third-party imports.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

#: Skip-message substrings that mean "a data input this tier needs is absent".
#: ``requires_raw`` produces "raw data input absent: missing [...]"
#: (tests/helpers/base.py); the clean-store loaders raise/skip on
#: "clean partition"; a bare path mention is caught by the last two.
DATA_MISSING_MARKERS = (
    "raw data input absent",
    "clean partition",
    "data/raw",
    "data/clean",
)

GOLDEN_CLASSNAME = "tests.regression.test_fleet_arrays_golden"
GOLDEN_NAME = "test_generators_to_fleet_arrays_ercot_2023_golden"


def check_report(report_path: Path) -> list[str]:
    """Return the list of guard violations found in ``report_path``."""
    problems: list[str] = []
    if not report_path.exists():
        return [
            f"junit report {report_path} does not exist — pytest died before "
            "writing it; the tier did not run"
        ]

    tree = ET.parse(report_path)
    golden_seen = False
    golden_clean = False

    for case in tree.iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        skipped = case.find("skipped")
        failed = case.find("failure") is not None or case.find("error") is not None

        if skipped is not None:
            message = (skipped.get("message") or "") + (skipped.text or "")
            if any(marker in message for marker in DATA_MISSING_MARKERS):
                problems.append(
                    f"DATA-MISSING SKIP: {classname}::{name} — {message.strip()!r}. "
                    "The workflow's provisioning has a gap: add the missing "
                    "data path to golden-data-tier.yml (sparse-checkout list "
                    "or regenerate_clean slice); never let it skip silently."
                )

        if classname == GOLDEN_CLASSNAME and name == GOLDEN_NAME:
            golden_seen = True
            golden_clean = skipped is None and not failed

    if not golden_seen:
        problems.append(
            f"GOLDEN NOT RUN: {GOLDEN_CLASSNAME}::{GOLDEN_NAME} is absent from "
            "the report — the tier expression or the test's markers drifted "
            "and deselected it. That silence is the exact card-F failure mode; "
            "fix the selection, do not ship this workflow without the golden."
        )
    elif not golden_clean:
        problems.append(
            f"GOLDEN NOT GREEN: {GOLDEN_CLASSNAME}::{GOLDEN_NAME} was skipped "
            "or failed. A red golden is a finding (attribute it per the "
            "fixture docstring's regeneration governance), never noise."
        )

    return problems


def main(argv: list[str]) -> int:
    """CLI entry point: exit 1 with every violation printed, 0 when clean."""
    if len(argv) != 2:
        print(__doc__)
        return 2
    problems = check_report(Path(argv[1]))
    for p in problems:
        print(f"FAIL: {p}")
    if problems:
        return 1
    print("data-tier report clean: no data-missing skips; golden ran and passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
