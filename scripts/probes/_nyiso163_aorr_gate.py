#!/usr/bin/env python3
"""On-receipt identifiability gate for NYISO AORR / Local-Reliability-Rule rows.

This is an executable, FAIL-CLOSED re-run of the nyiso-97 §4 content test, built
at nyiso-163 *before* any current-vintage rows exist, so that the test a future
session applies is pre-committed rather than shaped around the data it receives.

WHAT IT DECIDES
---------------
Given a set of AORR / LRR rows transcribed from a received source, the gate
answers exactly one question, the one `INTAKE-SPEC-nyiso156-winter-locational
-2026-08-30.md` §2 pre-committed:

    PASS = at least one 2023-2025-applicable NYC (Zone J) pocket row carries a
           derivable MW level or minimum-units-online, an eligible unit set, and
           an observable trigger -- the three quantities nyiso-97 §1 requires --
           plus a rule-13 forward story.
    FAIL = anything else. The leg then closes with cause exactly as nyiso-97
           closed.

FAIL-CLOSED BY CONSTRUCTION
---------------------------
Every test defaults to failure. A missing field, a null, an unparseable number,
an unrecognised enum, an unquotable claim, or a malformed row is a FAIL of that
test -- never a skip and never a pass. The gate never infers a value it was not
given, and a row that raises while being evaluated fails rather than aborting
the run.

THE ANTI-INFERENCE GUARD (rule 13 `[R-MEASURED]`, nyiso-97 §5 re-open bar)
-------------------------------------------------------------------------
Each of the three quantities must carry a `quote` that is a VERBATIM SUBSTRING
of that row's own published `text`. A number that does not appear in the source
row cannot pass, which is what mechanically forbids backing a parameter out of
observed unit conduct, BPCG/make-whole uplift, LBMP, or the C3a/C3c residual.
`derivation_basis` additionally hard-fails on the forbidden bases by name.

USAGE
-----
    python3 scripts/probes/_nyiso163_aorr_gate.py --rows <rows.json>
    python3 scripts/probes/_nyiso163_aorr_gate.py --self-test

Exit status: 0 = PASS, 2 = FAIL, 3 = the input could not be read at all (which
is itself a fail-closed outcome, reported distinctly so a transcription error is
not misread as an adjudication).

The row schema is documented in `ROW_SCHEMA_DOC` below and exercised by the
committed 2008-vintage negative control, `_nyiso163_aorr_control_2008.json`.

nyiso-163, 2026-08-31. No solve; no mechanism; nothing armed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Constants -- every admissibility list is an allowlist, so an unrecognised
# value fails rather than passing through (rule 5 `[R-NO-MAGIC]`: each list
# carries its citation).
# --------------------------------------------------------------------------

#: The scored training span. A row must be applicable to some part of it.
#: (rule 22 `[R-HOLDOUT]`: the freeze is active; 2023-2025 is the only span.)
SPAN_START = "2023-01-01"
SPAN_END = "2025-12-31"

#: PASS is reserved to NYC Zone J pocket rows. nyiso-97 §4 blocker 1 records
#: that the LIPA (Zone K) rows ARE concrete, but that the Zone-K side already
#: carries the published `nyiso_li_lcr_tsl` import limit in the keeper -- so a
#: Zone-K row is not the object this intake serves and cannot carry the gate.
QUALIFYING_ZONES = ("J",)

#: Trigger sources the model can actually observe in a forecast year. Anything
#: outside this list is unobservable for our purposes and fails T4 -- this is
#: what nyiso-97 §4 blocker 1 turns on (Con Ed's own real-time contingency
#: analysis on its sub-transmission network is not observable to us).
OBSERVABLE_TRIGGER_SOURCES = frozenset(
    {
        "forecast_load_mw",
        "measured_load_mw",
        "temperature",
        "unit_outage_state",
        "published_schedule",
        "calendar_season",
    }
)

#: Forward drivers a requirement may regenerate from (rule 13's regeneration
#: test: "could this same quantity be produced for a forward year from forward
#: drivers, and would it respond to changed conditions?").
FORWARD_DRIVERS = frozenset(
    {
        "forecast_load_mw",
        "temperature",
        "fleet_state",
        "published_constant",
        "calendar_season",
    }
)

#: Derivation bases the nyiso-97 §5 re-open bar forbids outright. Restated
#: verbatim as binding by INTAKE-SPEC-nyiso156 §2.
FORBIDDEN_DERIVATION_BASES = frozenset(
    {
        "unit_conduct",
        "bpcg_uplift",
        "make_whole",
        "lbmp",
        "residual",
        "model_inference",
    }
)

#: The only admissible provenance: the requirement as published.
ALLOWED_DERIVATION_BASES = frozenset({"published_document"})

#: Parameter kinds that satisfy nyiso-97 §1(i).
PARAMETER_KINDS = frozenset({"mw", "min_units"})

#: Eligible-unit-set kinds that satisfy nyiso-97 §1(ii). A "class" is admitted
#: only when it is closed and enumerable against the fleet (e.g. "all Astoria
#: units"); an open qualitative phrase ("certain areas of the Con Edison
#: system") is not a class and must be encoded as null, which fails.
UNIT_SET_KINDS = frozenset({"enumerated", "closed_class"})

ROW_SCHEMA_DOC = """
Each row in the `--rows` JSON file is an object:

  row_id                  str   e.g. "Table B.4 LRR 3" / "ARR 37" / "LRR I-R3"
  source                  str   document + URL the row was transcribed from
  vintage_effective_start str   ISO date, or null if the source does not state it
  vintage_effective_end   str   ISO date, or null meaning "still in force"
  nyca_zone               str   "J" (NYC), "K" (Long Island), ... or null
  pocket                  str   named sub-zonal pocket, or null
  text                    str   the row's VERBATIM published text
  derivation_basis        str   must be "published_document"

  parameter        { kind: "mw"|"min_units", value: number, quote: str } | null
  eligible_unit_set{ kind: "enumerated"|"closed_class", units: [str],
                     quote: str } | null
  trigger          { observable_from: str, quote: str,
                     depends_on_unpublished_procedure: bool } | null
  forward_story    { regenerates_from: str,
                     responds_to_changed_conditions: bool } | null

Every `quote` must appear verbatim (whitespace-normalised) inside `text`.
A null anywhere is a FAIL of the test that reads it, never a skip.
"""

TEST_IDS = ("T0_vintage", "T1_zone", "T2_parameter", "T3_unit_set", "T4_trigger",
            "T5_forward_story", "T6_provenance")


# --------------------------------------------------------------------------
# Result containers
# --------------------------------------------------------------------------


@dataclass
class TestResult:
    """One named test applied to one row: passed/failed plus a stated reason."""

    test_id: str
    passed: bool
    reason: str


@dataclass
class RowResult:
    """The full verdict for one row: every test, and whether the row qualifies."""

    row_id: str
    qualifies: bool
    tests: list[TestResult] = field(default_factory=list)

    @property
    def failed_tests(self) -> list[str]:
        """Return the ids of the tests this row failed, in declaration order."""
        return [t.test_id for t in self.tests if not t.passed]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view of this row's verdict."""
        return {
            "row_id": self.row_id,
            "qualifies": self.qualifies,
            "failed_tests": self.failed_tests,
            "tests": [
                {"test_id": t.test_id, "passed": t.passed, "reason": t.reason}
                for t in self.tests
            ],
        }


@dataclass
class GateResult:
    """The gate's overall verdict over a set of rows."""

    verdict: str
    rows: list[RowResult] = field(default_factory=list)

    @property
    def qualifying_rows(self) -> list[str]:
        """Return the ids of rows that passed every test."""
        return [r.row_id for r in self.rows if r.qualifies]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view of the gate verdict."""
        return {
            "gate": "nyiso-163 AORR on-receipt identifiability gate",
            "spec": "nyiso-97 §1/§4 content test; INTAKE-SPEC-nyiso156 §2",
            "verdict": self.verdict,
            "n_rows": len(self.rows),
            "n_qualifying": len(self.qualifying_rows),
            "qualifying_rows": self.qualifying_rows,
            "rows": [r.to_dict() for r in self.rows],
        }


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _norm(text: str) -> str:
    """Collapse whitespace so a quote matches its source across line wrapping."""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def _quote_is_verbatim(quote: Any, text: Any) -> bool:
    """Return True iff `quote` is a non-empty verbatim substring of `text`.

    This is the anti-inference guard: a claimed quantity that cannot be quoted
    from the row's own published text is, by construction, inferred from
    somewhere else -- which rule 13 forbids.
    """
    if not isinstance(quote, str) or not quote.strip():
        return False
    if not isinstance(text, str) or not text.strip():
        return False
    return _norm(quote) in _norm(text)


def _is_number(value: Any) -> bool:
    """Return True iff `value` is a real, finite number (bools excluded)."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return value == value and value not in (float("inf"), float("-inf"))


def _date_ok(value: Any) -> bool:
    """Return True iff `value` is an ISO `YYYY-MM-DD` date string."""
    return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


# --------------------------------------------------------------------------
# The seven tests
# --------------------------------------------------------------------------


def _test_vintage(row: dict[str, Any]) -> TestResult:
    """T0 -- the row must be applicable to some part of 2023-2025.

    nyiso-97 §4 blocker 2: deriving a 2023-2025 obligation from a 2008 table
    would be an inaccurate input worn as a measured one (the reverse of rule 14
    `[R-ACCURATE]`). An unstated effective date fails: we do not guess vintage.
    """
    start = row.get("vintage_effective_start")
    end = row.get("vintage_effective_end")
    if not _date_ok(start):
        return TestResult("T0_vintage", False,
                          "no stated effective start date (fail-closed: vintage is never assumed)")
    if start > SPAN_END:
        return TestResult("T0_vintage", False,
                          f"effective from {start}, after the {SPAN_END} span end")
    if end is not None:
        if not _date_ok(end):
            return TestResult("T0_vintage", False,
                              "effective end present but not an ISO date (fail-closed)")
        if end < SPAN_START:
            return TestResult("T0_vintage", False,
                              f"superseded {end}, before the {SPAN_START} span start")
    return TestResult("T0_vintage", True,
                      f"applicable to 2023-2025 (effective {start} -> {end or 'in force'})")


def _test_zone(row: dict[str, Any]) -> TestResult:
    """T1 -- the row must be an NYC (Zone J) sub-zonal pocket row."""
    zone = row.get("nyca_zone")
    pocket = row.get("pocket")
    if zone not in QUALIFYING_ZONES:
        return TestResult("T1_zone", False,
                          f"zone {zone!r} is not a qualifying NYC pocket zone "
                          f"{QUALIFYING_ZONES} (Zone K already carries the published "
                          "nyiso_li_lcr_tsl import limit -- nyiso-97 §4)")
    if not isinstance(pocket, str) or not pocket.strip():
        return TestResult("T1_zone", False, "no named sub-zonal pocket")
    return TestResult("T1_zone", True, f"NYC Zone J pocket {pocket!r}")


def _test_parameter(row: dict[str, Any]) -> TestResult:
    """T2 -- nyiso-97 §1(i): a derivable MW level or minimum-units-online."""
    param = row.get("parameter")
    if not isinstance(param, dict):
        return TestResult("T2_parameter", False,
                          "no MW level or minimum-units-online (qualitative row)")
    kind = param.get("kind")
    if kind not in PARAMETER_KINDS:
        return TestResult("T2_parameter", False,
                          f"parameter kind {kind!r} not in {sorted(PARAMETER_KINDS)}")
    if not _is_number(param.get("value")):
        return TestResult("T2_parameter", False,
                          f"parameter value {param.get('value')!r} is not a number")
    if not _quote_is_verbatim(param.get("quote"), row.get("text")):
        return TestResult("T2_parameter", False,
                          "parameter not quotable verbatim from the row text "
                          "(rule 13: no parameter may be inferred)")
    return TestResult("T2_parameter", True,
                      f"{kind}={param['value']} quoted verbatim from the row")


def _test_unit_set(row: dict[str, Any]) -> TestResult:
    """T3 -- nyiso-97 §1(ii): an eligible unit set."""
    unit_set = row.get("eligible_unit_set")
    if not isinstance(unit_set, dict):
        return TestResult("T3_unit_set", False,
                          "no eligible unit set (no unit list to derive)")
    kind = unit_set.get("kind")
    if kind not in UNIT_SET_KINDS:
        return TestResult("T3_unit_set", False,
                          f"unit-set kind {kind!r} not in {sorted(UNIT_SET_KINDS)}")
    units = unit_set.get("units")
    if not isinstance(units, list) or not units or not all(
        isinstance(u, str) and u.strip() for u in units
    ):
        return TestResult("T3_unit_set", False, "unit set is empty or malformed")
    if not _quote_is_verbatim(unit_set.get("quote"), row.get("text")):
        return TestResult("T3_unit_set", False,
                          "unit set not quotable verbatim from the row text")
    return TestResult("T3_unit_set", True,
                      f"{kind} set of {len(units)} unit(s), quoted verbatim")


def _test_trigger(row: dict[str, Any]) -> TestResult:
    """T4 -- nyiso-97 §1(iii) as sharpened by §4: an OBSERVABLE trigger.

    A trigger we cannot observe fails rule 13's regeneration test outright. The
    2008 Con Ed in-city rows fail here: the trigger is Con Ed's own real-time
    contingency analysis, and the parameters live in unpublished System
    Operation procedures (SO3-18 and kin).
    """
    trigger = row.get("trigger")
    if not isinstance(trigger, dict):
        return TestResult("T4_trigger", False, "no stated trigger")
    if trigger.get("depends_on_unpublished_procedure") is not False:
        return TestResult("T4_trigger", False,
                          "trigger depends on an unpublished TO procedure, or the "
                          "dependence is unstated (fail-closed)")
    source = trigger.get("observable_from")
    if source not in OBSERVABLE_TRIGGER_SOURCES:
        return TestResult("T4_trigger", False,
                          f"trigger source {source!r} is not observable to the model "
                          f"{sorted(OBSERVABLE_TRIGGER_SOURCES)}")
    if not _quote_is_verbatim(trigger.get("quote"), row.get("text")):
        return TestResult("T4_trigger", False,
                          "trigger not quotable verbatim from the row text")
    return TestResult("T4_trigger", True, f"observable from {source}, quoted verbatim")


def _test_forward_story(row: dict[str, Any]) -> TestResult:
    """T5 -- rule 13's regeneration test: forward drivers, responsive to change."""
    story = row.get("forward_story")
    if not isinstance(story, dict):
        return TestResult("T5_forward_story", False, "no rule-13 forward story")
    driver = story.get("regenerates_from")
    if driver not in FORWARD_DRIVERS:
        return TestResult("T5_forward_story", False,
                          f"forward driver {driver!r} not in {sorted(FORWARD_DRIVERS)}")
    if story.get("responds_to_changed_conditions") is not True:
        return TestResult("T5_forward_story", False,
                          "does not respond to changed conditions (a frozen constant "
                          "is not a forward story)")
    return TestResult("T5_forward_story", True, f"regenerates from {driver}")


def _test_provenance(row: dict[str, Any]) -> TestResult:
    """T6 -- the nyiso-97 §5 re-open bar, restated as binding by INTAKE-SPEC §2.

    Do not re-open by inferring the requirement from observed unit conduct,
    BPCG uplift, LBMP, or the C3c/CT_PEAKER residual.
    """
    basis = row.get("derivation_basis")
    if basis in FORBIDDEN_DERIVATION_BASES:
        return TestResult("T6_provenance", False,
                          f"derivation basis {basis!r} is forbidden by the nyiso-97 §5 "
                          "re-open bar (rule 13 pinning)")
    if basis not in ALLOWED_DERIVATION_BASES:
        return TestResult("T6_provenance", False,
                          f"derivation basis {basis!r} not in "
                          f"{sorted(ALLOWED_DERIVATION_BASES)} (fail-closed)")
    if not isinstance(row.get("source"), str) or not row["source"].strip():
        return TestResult("T6_provenance", False, "no cited source document")
    return TestResult("T6_provenance", True, "published document, source cited")


_TESTS = (
    _test_vintage,
    _test_zone,
    _test_parameter,
    _test_unit_set,
    _test_trigger,
    _test_forward_story,
    _test_provenance,
)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def evaluate_row(row: Any) -> RowResult:
    """Apply all seven tests to one row and return its verdict.

    A row that is not a dict, or that raises while being evaluated, fails every
    test rather than aborting the gate -- fail-closed.
    """
    if not isinstance(row, dict):
        return RowResult(
            row_id="<malformed row>",
            qualifies=False,
            tests=[TestResult(t, False, "row is not an object (fail-closed)")
                   for t in TEST_IDS],
        )
    row_id = row.get("row_id")
    row_id = row_id if isinstance(row_id, str) and row_id.strip() else "<unnamed row>"

    results: list[TestResult] = []
    for test in _TESTS:
        try:
            results.append(test(row))
        except Exception as exc:  # fail-closed: an error is never a pass
            results.append(TestResult(test.__name__, False, f"test raised: {exc!r}"))
    return RowResult(row_id=row_id, qualifies=all(r.passed for r in results),
                     tests=results)


def run_gate(rows: Any) -> GateResult:
    """Run the gate over a list of rows.

    PASS iff at least one row passes every test. An empty, malformed, or
    non-list input is a FAIL, never an error and never a pass.
    """
    if not isinstance(rows, list) or not rows:
        return GateResult(verdict="FAIL", rows=[])
    results = [evaluate_row(r) for r in rows]
    verdict = "PASS" if any(r.qualifies for r in results) else "FAIL"
    return GateResult(verdict=verdict, rows=results)


def load_rows(path: Path) -> Any:
    """Load rows from a JSON file.

    Accepts either a bare list of rows or an object with a `rows` key, so a
    transcription can carry provenance metadata alongside its rows.
    """
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict):
        return payload.get("rows")
    return payload


def _format_report(result: GateResult) -> str:
    """Render a human-readable gate report."""
    lines = [
        "=" * 72,
        f"NYISO AORR ON-RECEIPT IDENTIFIABILITY GATE -- {result.verdict}",
        "  nyiso-97 §1/§4 content test; INTAKE-SPEC-nyiso156 §2; fail-closed",
        "=" * 72,
    ]
    for row in result.rows:
        mark = "PASS" if row.qualifies else "FAIL"
        lines.append(f"[{mark}] {row.row_id}")
        for test in row.tests:
            if not test.passed:
                lines.append(f"         ✗ {test.test_id}: {test.reason}")
        if row.qualifies:
            for test in row.tests:
                lines.append(f"         ✓ {test.test_id}: {test.reason}")
    lines.append("-" * 72)
    lines.append(
        f"{len(result.rows)} row(s) evaluated; "
        f"{len(result.qualifying_rows)} qualifying"
    )
    if result.verdict == "PASS":
        lines.append(
            "VERDICT PASS -- a mechanism prereg may now be written (P1-native "
            "commitment-bridge class). Qualifying: "
            + ", ".join(result.qualifying_rows)
        )
    else:
        lines.append(
            "VERDICT FAIL -- the leg closes with cause exactly as nyiso-97 closed. "
            "Nothing is inferred from conduct, BPCG uplift, LBMP, or the residual."
        )
    lines.append("=" * 72)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on PASS, 2 on FAIL, 3 on unreadable input."""
    parser = argparse.ArgumentParser(
        description="Fail-closed nyiso-97 §4 content test for received AORR/LRR rows.",
    )
    parser.add_argument("--rows", type=Path, help="JSON file of transcribed rows")
    parser.add_argument("--self-test", action="store_true",
                        help="run the committed 2008-vintage negative control")
    parser.add_argument("--json-out", type=Path, help="write the verdict as JSON")
    parser.add_argument("--schema", action="store_true", help="print the row schema")
    args = parser.parse_args(argv)

    if args.schema:
        print(ROW_SCHEMA_DOC)
        return 0

    if args.self_test:
        control = Path(__file__).with_name("_nyiso163_aorr_control_2008.json")
        return _run_self_test(control, args.json_out)

    if not args.rows:
        parser.error("one of --rows, --self-test, or --schema is required")

    try:
        rows = load_rows(args.rows)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"UNREADABLE INPUT (fail-closed, not an adjudication): {exc}")
        return 3

    result = run_gate(rows)
    print(_format_report(result))
    if args.json_out:
        args.json_out.write_text(json.dumps(result.to_dict(), indent=2) + "\n")
        print(f"wrote {args.json_out}")
    return 0 if result.verdict == "PASS" else 2


def _fail_closed_cases() -> list[tuple[str, Any]]:
    """Return (name, rows) pairs that must every one of them evaluate to FAIL.

    These pin the fail-closed contract: malformed, empty and partially-specified
    input must never reach PASS. The last case is the anti-inference guard -- a
    fully-specified row whose parameter is NOT quotable from its own text.
    """
    unquotable = {
        "row_id": "unquotable parameter (anti-inference guard)",
        "source": "SYNTHETIC", "vintage_effective_start": "2022-01-01",
        "vintage_effective_end": None, "nyca_zone": "J", "pocket": "in-City",
        "text": "Con Edison shall commit sufficient in-City generation.",
        "derivation_basis": "published_document",
        "parameter": {"kind": "min_units", "value": 3, "quote": "no fewer than 3"},
        "eligible_unit_set": {"kind": "enumerated", "units": ["Astoria"],
                              "quote": "in-City generation"},
        "trigger": {"observable_from": "forecast_load_mw", "quote": "shall commit",
                    "depends_on_unpublished_procedure": False},
        "forward_story": {"regenerates_from": "forecast_load_mw",
                          "responds_to_changed_conditions": True},
    }
    residual = dict(unquotable, row_id="residual-derived row (nyiso-97 §5 bar)",
                    derivation_basis="residual")
    return [
        ("empty list", []),
        ("not a list", {"rows": "oops"}),
        ("null rows", None),
        ("malformed row", [42]),
        ("empty row object", [{}]),
        ("unquotable parameter", [unquotable]),
        ("residual derivation basis", [residual]),
    ]


def _run_self_test(control_path: Path, json_out: Path | None) -> int:
    """Run the gate's acceptance suite. Returns 0 if the gate behaves, 1 if not.

    Three legs, all of which must hold for the gate to be trusted:

    1. NEGATIVE CONTROL -- the 2008-vintage Appendix B, adjudicated
       NON-IDENTIFYING ON CONTENT at nyiso-97 §4, must return FAIL. A gate that
       passes it is broken and must be fixed, never loosened.
    2. DISCRIMINATING POWER -- a synthetic row of identifying shape must return
       PASS. Without this leg a constant-FAIL function would "pass" leg 1 while
       being useless, so leg 1 alone is not acceptance evidence.
    3. FAIL-CLOSED -- malformed, empty, unquotable and residual-derived input
       must all return FAIL rather than erroring or passing.
    """
    ok = True

    try:
        rows = load_rows(control_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"SELF-TEST ERROR: cannot read control {control_path}: {exc}")
        return 1

    result = run_gate(rows)
    print(_format_report(result))
    if json_out:
        json_out.write_text(json.dumps(result.to_dict(), indent=2) + "\n")
        print(f"wrote {json_out}")

    print()
    print("=" * 72)
    print("ACCEPTANCE SUITE")
    print("=" * 72)

    # Leg 1 -- the negative control must FAIL.
    if result.verdict != "FAIL":
        print("[✗] LEG 1 NEGATIVE CONTROL: the gate PASSED the 2008 vintage, which "
              "nyiso-97 §4 adjudicated non-identifying. The gate is BROKEN -- fix "
              "it; do NOT loosen the test.")
        ok = False
    else:
        print("[✓] LEG 1 NEGATIVE CONTROL: 2008 Appendix B -> FAIL, as required.")
        print("    Per-row blockers (these must match the nyiso-97 §4 reasoning):")
        for row in result.rows:
            print(f"      {row.row_id}")
            print(f"        {', '.join(row.failed_tests)}")

    # Leg 2 -- discriminating power.
    positive_path = Path(__file__).with_name("_nyiso163_aorr_synthetic_positive.json")
    try:
        positive = run_gate(load_rows(positive_path))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[✗] LEG 2 DISCRIMINATION: cannot read {positive_path}: {exc}")
        ok = False
    else:
        if positive.verdict == "PASS":
            print("[✓] LEG 2 DISCRIMINATION: synthetic identifying row -> PASS, so "
                  "the gate is not a constant-FAIL function and leg 1 is meaningful.")
        else:
            failed = positive.rows[0].failed_tests if positive.rows else ["<no rows>"]
            print("[✗] LEG 2 DISCRIMINATION: the gate FAILED a row of identifying "
                  f"shape on {', '.join(failed)}. It can never return PASS, so it "
                  "would reject real qualifying rows. BROKEN -- fix it.")
            ok = False

    # Leg 3 -- fail-closed contract.
    leaks = [name for name, rows_in in _fail_closed_cases()
             if run_gate(rows_in).verdict != "FAIL"]
    if leaks:
        print(f"[✗] LEG 3 FAIL-CLOSED: these reached PASS: {', '.join(leaks)}")
        ok = False
    else:
        print(f"[✓] LEG 3 FAIL-CLOSED: all {len(_fail_closed_cases())} malformed / "
              "unquotable / residual-derived cases -> FAIL.")

    print("=" * 72)
    print("SELF-TEST " + ("PASSED -- the gate is fit to run on received rows."
                          if ok else "FAILED -- do not use this gate."))
    print("=" * 72)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
