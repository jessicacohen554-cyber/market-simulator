"""Deterministic lane assignment for session-record documents.

Session records (FINDING-, PRECOMMIT-, RESULT-, … docs, and the loose phase-0
census outputs) are filed under ``docs/records/<lane>/`` and
``results/phase0/<lane>/``. The lane is the FIRST lane token in the file (or
directory) name, after any record prefix is stripped; a name naming two ISOs
goes to the first. Names with no lane token file under ``misc``.

Usage::

    python3 scripts/lib/record_lanes.py FINDING-ercot253-foo-2026-09-06.md
    # -> ercot
"""

from __future__ import annotations

import re
import sys

# Record-document prefixes (case-sensitive, followed by "-"). Order matters
# only where one prefix extends another (DECISION-CARD before DECISION).
RECORD_PREFIXES: tuple[str, ...] = (
    "FINDING",
    "PRECOMMIT",
    "RESULTS",
    "RESULT",
    "ADDENDUM",
    "DIAGNOSIS",
    "DECISION-CARD",
    "DECISION-MAP",
    "DECISION",
    "SHARDREPORT",
    "SHARD",
    "PREREG",
    "CHARTER",
    "DESIGN",
    "RESEARCH",
    "INTAKE",
    "ASSESSMENT",
    "HANDOFF",
    "PREDECL",
    "PROBE",
    "PRECHECK",
    "GATESPEC",
    "MEMO",
    "EXECNOTE",
    "PLAN",
    "SUMMARY",
    "METRICS",
    "ATTESTATION",
    "AMENDMENT",
    "ASK",
)

_PREFIX_RE = re.compile(r"^(?:%s)-" % "|".join(re.escape(p) for p in RECORD_PREFIXES))

# (lane, pattern) — matched against the lower-cased name with the record
# prefix stripped; the earliest match position wins, ties go to list order.
_B = r"(?<![a-z0-9])"  # left word boundary (digits/letters only; _ and - break)
LANE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (lane, re.compile(pat))
    for lane, pat in (
        ("ercot", r"ercot"),
        ("caiso", r"caiso"),
        ("pjm", _B + r"r?pjm"),
        ("nyiso", r"nyiso"),
        ("neiso", r"neiso|" + _B + r"isone|" + _B + r"iso-ne(?![a-z])"),
        ("miso", _B + r"r?miso"),
        ("spp", _B + r"r?spp"),
        ("soco", _B + r"r?soco"),
        ("nwpp", _B + r"r?nwpp"),
        (
            "forecast",
            _B + r"(?:ffr|ff|fh|scn|ces|t1|hindcast|forecast)(?![a-z])"
            r"|" + _B + r"capx"
            r"|" + _B + r"d\d{2}(?!\d)",
        ),
        (
            "governance",
            _B + r"(?:gov|governance|bloat\d*|perf[a-z]*|refactor|rewrite"
            r"|audit[a-z]*|rubric|holdout|matrix|xiso|x-iso|cross-iso|crossiso)"
            r"|" + _B + r"y\d+(?![a-z0-9])",
        ),
    )
)

LANES: tuple[str, ...] = tuple(lane for lane, _ in LANE_PATTERNS) + ("misc",)


def is_record_name(name: str) -> bool:
    """Return True if ``name`` starts with a session-record prefix."""
    return bool(_PREFIX_RE.match(name))


def lane_for(name: str) -> str:
    """Return the record lane for a file or directory basename."""
    stem = _PREFIX_RE.sub("", name).lower()
    best: tuple[int, int, str] | None = None
    for order, (lane, pat) in enumerate(LANE_PATTERNS):
        m = pat.search(stem)
        if m and (best is None or (m.start(), order) < best[:2]):
            best = (m.start(), order, lane)
    return best[2] if best else "misc"


def main(argv: list[str]) -> int:
    """Print ``<lane>\\t<name>`` for each name given on the command line."""
    for name in argv:
        print(f"{lane_for(name)}\t{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
