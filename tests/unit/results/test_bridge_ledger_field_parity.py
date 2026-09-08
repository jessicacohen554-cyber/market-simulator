"""A bridge year's evolution ledger records the same FIELDS as a solved year's.

``runner.run_scenario_iso`` writes ``evolution_<year>.json`` from **two**
hand-maintained field lists: the ``if is_bridge:`` writer, for a rule-22
quarantined year the fleet is evolved across but whose LP is never solved, and
the solved-year writer at the end of the loop. Nothing connected them, so the
bridge list silently fell eight fields behind the solved one —
``wind_cap_mw``, ``solar_cap_mw``, ``renewable_credit_applied``,
``storage_power_mw``, ``storage_firm_mw``, ``firm_clean_accredited_mw``,
``capacity_reserve_position`` and ``adequacy_requirement_mw``.

That made a bridge year the one year whose capacity screen was not reproducible
from its own record. The screens **did** consume those pools — they are inside
the ``screen_entering_firm_mw`` the same ledger records — so the values existed
and simply went unwritten, and two separate lanes had to reconstruct them by
hand (capx D75 §6 item 3; ``FINDING-capx-d75r-2026-09-06.md`` §6 item 1, whose
phase 0 and full-window analyzer each rebuilt the pools). capx D83 repaired the
writer; this test is what stops the two lists drifting apart again, in either
direction — a field added to the solved writer and not the bridge writer fails
here just as loudly as one removed from the bridge writer.

It is deliberately source-level, for the reason
``tests/unit/pipeline/test_p1_prep_wiring.py`` gives: driving a real hindcast
window to assert a field-list fact costs an LP solve per run, and the thing
that broke was a missing name in a dict literal. Field PRESENCE is what this
asserts; the bridge writer sets the four LP-derived fields to ``None``
(``peak_demand_mw``, ``adequacy_requirement_mw``, ``reserve_margin``,
``rps_dual``) because a bridge year has no LP peak and no duals, which is
faithful — the seam quantities its screens really consumed are carried by the
``screen_ledger_fields`` block both writers splat.
"""

import ast
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

_RUNNER = Path(REPO_ROOT) / "src" / "market_sim" / "runner.py"

#: The four fields a bridge year records as ``None`` on purpose: each is
#: derived from the LP's own load or duals, and ``peak_demand`` is re-derived
#: below the bridge branch, so a bridge year genuinely has no value for them.
_LP_DERIVED_NULLS = frozenset(
    {
        "peak_demand_mw",
        "adequacy_requirement_mw",
        "reserve_margin",
        "rps_dual",
    }
)

#: The accreditation-trail fields whose absence was the D83 defect. Named
#: explicitly so the test states what it is protecting, rather than only
#: asserting an abstract set equality that a future edit could satisfy by
#: deleting fields from BOTH writers.
_ACCREDITATION_TRAIL = frozenset(
    {
        "wind_cap_mw",
        "solar_cap_mw",
        "renewable_credit_applied",
        "storage_power_mw",
        "storage_firm_mw",
        "firm_clean_mw",
        "firm_clean_accredited_mw",
        "capacity_reserve_position",
    }
)


def _ledger_update_fields() -> dict[str, set[str]]:
    """Field names each ``<name>.update(...)`` ledger writer supplies.

    Returns a mapping of the local ledger variable (``_ledger`` for the bridge
    writer, ``ledger`` for the solved one) to the set of keys that call
    contributes — explicit keywords plus the names of any ``**splat``, so a
    block moved into a shared dict is still counted as supplied.
    """
    tree = ast.parse(_RUNNER.read_text())
    found: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "update"):
            continue
        if not isinstance(func.value, ast.Name):
            continue
        target = func.value.id
        if target not in ("ledger", "_ledger"):
            continue
        names: set[str] = set()
        for kw in node.keywords:
            if kw.arg is not None:
                names.add(kw.arg)
            elif isinstance(kw.value, ast.Name):
                names.add(f"**{kw.value.id}")
        found.setdefault(target, set()).update(names)
    return found


class BridgeLedgerFieldParity(unittest.TestCase):
    """The two evolution-ledger writers supply one field list."""

    def setUp(self) -> None:
        self.writers = _ledger_update_fields()

    def test_both_writers_are_found(self) -> None:
        """The AST scan actually located both writers.

        Without this, a rename would turn every assertion below into a vacuous
        pass on an empty set — the failure mode a source-level test has to
        rule out first.
        """
        self.assertEqual(
            set(self.writers),
            {"ledger", "_ledger"},
            "expected exactly two evolution-ledger writers in runner.py "
            "(`ledger` = solved year, `_ledger` = rule-22 bridge year); "
            "found: " + repr(sorted(self.writers)),
        )

    def test_bridge_and_solved_writers_agree(self) -> None:
        """Neither writer carries a field the other does not.

        This is the D83 guard. A bridge year's ledger is the only record of
        what its capacity screen tested, so a field the solved writer records
        and the bridge writer drops is a hole in provenance, not a cosmetic
        gap.
        """
        bridge, solved = self.writers["_ledger"], self.writers["ledger"]
        self.assertEqual(
            solved - bridge,
            set(),
            "the bridge-year ledger writer is missing fields the solved-year "
            "writer records (capx D83). Add them to the `if is_bridge:` block "
            "in runner.run_scenario_iso, using the SAME expression the solved "
            "writer uses -- or, if the field is genuinely LP-derived, record "
            "it as None there and add it to _LP_DERIVED_NULLS here.",
        )
        self.assertEqual(
            bridge - solved,
            set(),
            "the bridge-year ledger writer records fields the solved-year "
            "writer does not; one ledger schema, both years.",
        )

    def test_accreditation_trail_is_present_in_both(self) -> None:
        """The specific fields D83 restored are recorded by both writers."""
        for target, names in self.writers.items():
            missing = _ACCREDITATION_TRAIL - names
            self.assertEqual(
                missing,
                set(),
                f"ledger writer `{target}` no longer records "
                f"{sorted(missing)} -- these are fleet-state quantities that "
                "exist in every evolved year, solved or bridged (capx D83).",
            )

    def test_lp_derived_fields_are_recorded_as_none_in_the_bridge(self) -> None:
        """The bridge writer supplies the LP-derived fields as literal ``None``.

        Their absence was part of the same defect, but the repair is to record
        them as ``None`` rather than to invent a value: a bridge year has no LP
        peak (``peak_demand`` is re-derived from the LP's own load *below* the
        bridge branch) and no duals. Recording them keeps one schema across
        both years without asserting a number that was never computed.
        """
        tree = ast.parse(_RUNNER.read_text())
        nulls: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "update"
                and isinstance(func.value, ast.Name)
                and func.value.id == "_ledger"
            ):
                continue
            for kw in node.keywords:
                if (
                    kw.arg in _LP_DERIVED_NULLS
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value is None
                ):
                    nulls.add(kw.arg)
        self.assertEqual(
            nulls,
            set(_LP_DERIVED_NULLS),
            "the bridge-year writer must record every LP-derived field as an "
            "explicit None; missing: " + repr(sorted(_LP_DERIVED_NULLS - nulls)),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
