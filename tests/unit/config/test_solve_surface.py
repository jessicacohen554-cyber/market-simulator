"""Tests for the capx D79 solve-surface fingerprint (owner ruling Q54).

**The hazard.** ``ScenarioConfig.cache_key()`` hashes the config and nothing
else, so re-deriving a registry table changes what a solve produces while every
key stays put and the pre-change bundle is silently re-served — the SCN-LOAD
incident, `docs/handoffs/DESIGN-capx-d79-2026-09-06.md` §1.

These tests pin the properties the construction rests on, so none can regress
silently:

* **canonicalisation** is order-independent (a re-ordered dict literal or
  ``frozenset`` moves nothing) and TYPE-FAITHFUL (a tuple is not a list, ``1``
  is not ``1.0``, an ``Enum`` member is not its bare value);
* **ISO projection** — a by-ISO table contributes one row to its own ISO, an
  ISO-token name to that ISO, everything else to all six;
* **the frozen-hash drop** — a docstring edit moves nothing, a value edit to one
  ISO's row moves that ISO alone, an ADDED name with a declaration moves nothing
  (and without one fails guard check 5), and a REVERT restores both the declared
  hash and the pre-change key;
* **``SolveEpoch`` scope predicates**, including the backcast-inert case;
* **the append-only guard's four cases**, mirroring D24-R's.

The guard halves run against synthetic source text (pure ``ast``, no import), so
they never mutate the real modules; the projection halves mutate a COPY of the
fingerprint rather than a registry, and the live-registry cases restore the
value they moved.
"""

from __future__ import annotations

import sys
import pytest
import unittest
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config import solve_surface as S  # noqa: E402
from market_sim.config.iso_configs import SUPPORTED_ISOS  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.config.solve_surface_declared import DECLARED  # noqa: E402

# This file is ABOUT the surface entering the key, so it opts out of the
# autouse neutralization in tests/conftest.py.
pytestmark = pytest.mark.solve_surface_live
from scripts import check_cache_key_registration as G  # noqa: E402


class _Colour(Enum):
    RED = "red"


@dataclass(frozen=True)
class _Pair:
    a: int
    b: float


class CanonicalisationTest(unittest.TestCase):
    """``canonical`` is order-independent and type-faithful."""

    def test_dict_key_order_is_irrelevant(self):
        self.assertEqual(
            S.row_hash({"a": 1, "b": 2}),
            S.row_hash({"b": 2, "a": 1}),
        )

    def test_frozenset_and_set_order_is_irrelevant(self):
        self.assertEqual(
            S.row_hash(frozenset({3, 1, 2})), S.row_hash(frozenset({1, 2, 3}))
        )
        self.assertEqual(S.row_hash({3, 1, 2}), S.row_hash({1, 2, 3}))

    def test_tuple_order_is_NOT_irrelevant(self):
        """A sequence's order is part of its value — merit order, band edges."""
        self.assertNotEqual(S.row_hash((1, 2)), S.row_hash((2, 1)))

    def test_tuple_and_list_hash_differently(self):
        self.assertNotEqual(S.row_hash((1, 2)), S.row_hash([1, 2]))

    def test_set_and_frozenset_hash_differently(self):
        self.assertNotEqual(S.row_hash({1, 2}), S.row_hash(frozenset({1, 2})))

    def test_int_and_float_hash_differently(self):
        self.assertNotEqual(S.row_hash(1), S.row_hash(1.0))

    def test_bool_is_not_an_int(self):
        self.assertNotEqual(S.row_hash(True), S.row_hash(1))

    def test_float_precision_is_exact(self):
        self.assertNotEqual(S.row_hash(0.1 + 0.2), S.row_hash(0.3))

    def test_enum_is_not_its_value(self):
        self.assertNotEqual(S.row_hash(_Colour.RED), S.row_hash("red"))

    def test_dataclass_fields_are_hashed(self):
        self.assertNotEqual(S.row_hash(_Pair(1, 2.0)), S.row_hash(_Pair(1, 3.0)))

    def test_nested_structures_round_trip(self):
        value = {"x": ({1: [2.5, None]}, frozenset({"b", "a"})), "y": _Pair(1, 2.0)}
        self.assertEqual(
            S.row_hash(value), S.row_hash(dict(reversed(list(value.items()))))
        )

    def test_a_class_has_no_canonical_image(self):
        with self.assertRaises(S.Unhashable):
            S.canonical(_Pair)


class IsoProjectionTest(unittest.TestCase):
    """The projection rule, on the live surface."""

    def test_iso_tuple_matches_the_registry(self):
        """A seventh ISO cannot land in ``iso_configs`` and not here."""
        self.assertEqual(set(S.SURFACE_ISOS), set(SUPPORTED_ISOS))

    def test_by_iso_table_contributes_only_its_own_row(self):
        fp = S.surface_fingerprint()
        by_iso = {n: v for n, v in fp.items() if isinstance(v, dict)}
        self.assertTrue(by_iso, "no by-ISO table found on the surface")
        name, rows = next(iter(by_iso.items()))
        for iso in rows:
            self.assertEqual(S.surface_rows(iso)[name], rows[iso])
        absent = set(S.SURFACE_ISOS) - set(rows)
        for iso in absent:
            self.assertNotIn(name, S.surface_rows(iso))

    def test_iso_token_name_reaches_only_that_iso(self):
        self.assertEqual(S._iso_tokens("ERCOT_GTC_LINK_MAP"), frozenset({"ERCOT"}))
        self.assertEqual(S._iso_tokens("CORRELATED_OUTAGE_CURVE"), frozenset())
        self.assertIn("ERCOT_GTC_LINK_MAP", S.surface_rows("ERCOT"))
        self.assertNotIn("ERCOT_GTC_LINK_MAP", S.surface_rows("PJM"))

    def test_an_iso_name_is_never_matched_as_a_substring(self):
        self.assertEqual(S._iso_tokens("PRECISOMETER_LIMIT"), frozenset())

    def test_shared_names_reach_every_iso(self):
        shared = [
            n
            for n, v in S.surface_fingerprint().items()
            if not isinstance(v, dict) and not S._iso_tokens(n)
        ]
        self.assertTrue(shared)
        for iso in S.SURFACE_ISOS:
            self.assertLessEqual(set(shared), set(S.surface_rows(iso)))

    def test_an_unregistered_iso_sees_only_shared_rows(self):
        rows = S.surface_rows("NOT_AN_ISO")
        self.assertTrue(rows)
        for name in rows:
            self.assertFalse(S._iso_tokens(name))


class FrozenHashDropTest(unittest.TestCase):
    """The (b′-1) drop: what moves a key, and what deliberately does not."""

    def tearDown(self):
        S.reset_caches()

    def test_moved_rows_reports_exactly_the_rows_off_their_declaration(self):
        """``moved_rows`` is sound and complete against ``DECLARED``.

        This USED to assert ``moved_rows(iso) == {}`` for every ISO — the D79
        landing state. That is a claim about repo state, not about the
        mechanism, and it goes stale the moment any registry value is
        legitimately repaired (the first was ercot-253's ERCOT
        ``NUCLEAR_MONTHLY_CF_BY_YEAR`` 2021 row, 2026-09-06). The merge gate on
        UNLEDGERED movement lives in
        ``tests/regression/test_persisted_identity.py`` — beside
        ``PINNED_SURFACE_ROWS_BY_ISO`` and ``LEDGERED_SURFACE_MOVES_BY_ISO``,
        which is where a cause block can actually be written — and it is not
        duplicated here. What this test pins is the property that gate rests on:
        a row is reported moved if and only if its live hash differs from its
        frozen declaration.
        """
        for iso in S.SURFACE_ISOS:
            live = S.surface_rows(iso)
            moved = S.moved_rows(iso)
            for name, live_hash in live.items():
                declared = DECLARED.get(name)
                if isinstance(declared, dict):
                    declared = declared.get(iso)
                if declared is None:  # undeclared names stay out of the key
                    self.assertNotIn(name, moved, f"{iso}/{name}")
                elif declared == live_hash:
                    self.assertNotIn(name, moved, f"{iso}/{name}")
                else:
                    self.assertEqual(moved.get(name), live_hash, f"{iso}/{name}")
            self.assertEqual(set(moved) - set(live), set(), f"{iso}: phantom rows")

    def test_every_surface_name_is_declared(self):
        self.assertEqual(set(S.surface_fingerprint()) - set(DECLARED), set())

    def test_a_docstring_edit_moves_nothing(self):
        """The fingerprint reads VALUES; prose is not one."""
        from market_sim.config import constants

        before = dict(S.surface_fingerprint())
        original = constants.__doc__
        try:
            constants.__doc__ = "an entirely different module docstring"
            S.reset_caches()
            self.assertEqual(S.surface_fingerprint(), before)
        finally:
            constants.__doc__ = original
            S.reset_caches()

    def test_a_value_edit_to_one_iso_row_moves_that_iso_alone(self):
        from market_sim.config import constants

        table = constants.DEMAND_GROWTH_RATES
        original = table["MISO"]
        baseline = {iso: dict(S.moved_rows(iso)) for iso in S.SURFACE_ISOS}
        try:
            table["MISO"] = (
                {**original, 2031: 0.4242} if isinstance(original, dict) else 0.4242
            )
            S.reset_caches()
            self.assertEqual(
                sorted(set(S.moved_rows("MISO")) - set(baseline["MISO"])),
                ["DEMAND_GROWTH_RATES"],
            )
            # Measured as a DELTA against each ISO's own pre-edit state, not
            # against {}: an ISO may legitimately carry a ledgered move of its
            # own (see the regression ledger), and the claim here is that this
            # edit reaches no ISO but MISO.
            for iso in set(S.SURFACE_ISOS) - {"MISO"}:
                self.assertEqual(S.moved_rows(iso), baseline[iso], f"{iso} moved too")
        finally:
            table["MISO"] = original
            S.reset_caches()

    def test_a_revert_restores_the_declared_hash_and_the_key(self):
        from market_sim.config import constants

        table = constants.DEMAND_GROWTH_RATES
        original = table["MISO"]
        config = ScenarioConfig(iso="MISO")
        before_key = config.cache_key()
        before_hash = S.surface_rows("MISO")["DEMAND_GROWTH_RATES"]
        table["MISO"] = {"sentinel": 1.0}
        S.reset_caches()
        self.assertNotEqual(config.cache_key(), before_key)
        table["MISO"] = original
        S.reset_caches()
        self.assertEqual(S.surface_rows("MISO")["DEMAND_GROWTH_RATES"], before_hash)
        self.assertEqual(config.cache_key(), before_key)

    def test_an_undeclared_name_stays_out_of_the_key(self):
        """A new table cannot re-key anything; guard check 5 is what catches it."""
        from market_sim.config import constants

        config = ScenarioConfig(iso="ERCOT")
        before = config.cache_key()
        before_moved = dict(S.moved_rows("ERCOT"))
        try:
            constants.A_BRAND_NEW_SURFACE_TABLE = {"ERCOT": 1.0}
            S.reset_caches()
            self.assertIn("A_BRAND_NEW_SURFACE_TABLE", S.surface_fingerprint())
            # Unchanged from before, not empty: an undeclared name adds no
            # moved row, whatever ledgered moves the ISO already carries.
            self.assertEqual(S.moved_rows("ERCOT"), before_moved)
            self.assertEqual(config.cache_key(), before)
        finally:
            del constants.A_BRAND_NEW_SURFACE_TABLE
            S.reset_caches()

    def test_a_declared_name_leaving_the_surface_moves_no_key(self):
        """Rule 26 [R-DELETE]: a retired name keeps its last hash."""
        from market_sim.config import constants

        config = ScenarioConfig(iso="ERCOT")
        before = config.cache_key()
        original = constants.EFORD
        try:
            del constants.EFORD
            S.reset_caches()
            self.assertNotIn("EFORD", S.surface_fingerprint())
            self.assertEqual(config.cache_key(), before)
        finally:
            constants.EFORD = original
            S.reset_caches()


class SolveEpochScopeTest(unittest.TestCase):
    """``applicable_epochs`` puts an id in exactly the keys its scope names."""

    def setUp(self):
        self.saved = S.SOLVE_EPOCHS

    def tearDown(self):
        S.SOLVE_EPOCHS = self.saved

    def test_the_ledger_is_empty_at_landing(self):
        """Owner ruling Q54 row 4 — the D65-B-R batch is D77's re-solve."""
        self.assertEqual(self.saved, ())
        self.assertEqual(S.applicable_epochs(ScenarioConfig()), [])

    def test_an_unscoped_epoch_reaches_every_config(self):
        S.SOLVE_EPOCHS = (S.SolveEpoch(id="e", cause="c"),)
        self.assertEqual(S.applicable_epochs(ScenarioConfig()), ["e"])
        self.assertEqual(S.applicable_epochs(ScenarioConfig(mode="backcast")), ["e"])

    def test_a_forecast_only_epoch_is_backcast_inert(self):
        S.SOLVE_EPOCHS = (S.SolveEpoch(id="e", cause="c", modes=("forecast",)),)
        self.assertEqual(S.applicable_epochs(ScenarioConfig(mode="forecast")), ["e"])
        self.assertEqual(S.applicable_epochs(ScenarioConfig(mode="backcast")), [])

    def test_an_iso_scoped_epoch_reaches_only_that_iso(self):
        S.SOLVE_EPOCHS = (S.SolveEpoch(id="e", cause="c", isos=("PJM",)),)
        self.assertEqual(S.applicable_epochs(ScenarioConfig(iso="PJM")), ["e"])
        self.assertEqual(S.applicable_epochs(ScenarioConfig(iso="ERCOT")), [])

    def test_reaches_year_excludes_a_shorter_horizon(self):
        S.SOLVE_EPOCHS = (S.SolveEpoch(id="e", cause="c", reaches_year=2028),)
        self.assertEqual(S.applicable_epochs(ScenarioConfig(end_year=2027)), [])
        self.assertEqual(S.applicable_epochs(ScenarioConfig(end_year=2030)), ["e"])

    def test_an_unknown_horizon_is_invalidated_not_served(self):
        S.SOLVE_EPOCHS = (S.SolveEpoch(id="e", cause="c", reaches_year=2028),)
        self.assertEqual(S.applicable_epochs(ScenarioConfig(end_year=None)), ["e"])

    def test_an_applicable_epoch_moves_the_key(self):
        config = ScenarioConfig()
        before = config.cache_key()
        S.SOLVE_EPOCHS = (S.SolveEpoch(id="e", cause="c"),)
        self.assertNotEqual(config.cache_key(), before)
        S.SOLVE_EPOCHS = self.saved
        self.assertEqual(config.cache_key(), before)


class AppendOnlyGuardTest(unittest.TestCase):
    """Guard check 6's four cases, mirroring D24-R's (pure, no git)."""

    def test_an_edited_hash_is_a_breach(self):
        self.assertTrue(
            G.surface_append_only_violations({"T": "'a'"}, {"T": "'b'"}, {"T"})
        )

    def test_adding_an_entry_is_clean(self):
        self.assertEqual(
            G.surface_append_only_violations(
                {"T": "'a'"}, {"T": "'a'", "U": "'b'"}, {"T", "U"}
            ),
            [],
        )

    def test_removing_an_entry_for_a_live_name_is_a_breach(self):
        self.assertTrue(G.surface_append_only_violations({"T": "'a'"}, {}, {"T"}))

    def test_removing_an_entry_for_a_RETIRED_name_is_ALSO_a_breach(self):
        """Unlike a ``ScenarioConfig`` field, a retired TABLE keeps its line.

        There is no ``_CACHE_KEY_RETIRED_FIELDS`` twin for the surface: the
        declaration IS the retirement record, so dropping it would re-key every
        config whose ISO carried the row.
        """
        self.assertTrue(G.surface_append_only_violations({"T": "'a'"}, {}, set()))


class GuardCheckFiveTest(unittest.TestCase):
    """Check 5 sees exactly the names the runtime does, and fails an omission."""

    def test_the_ast_view_matches_the_runtime_view(self):
        surface_src = (_ROOT / G._SURFACE_REL).read_text()
        sources = {
            rel: (_ROOT / rel).read_text()
            for rel in G.surface_module_paths(surface_src)
        }
        self.assertEqual(G.surface_names(sources), set(S.surface_fingerprint()))

    def test_an_undeclared_name_is_reported(self):
        names = G.surface_names({"m.py": "NEW_TABLE = {'ERCOT': 1.0}\n"})
        self.assertEqual(names, {"NEW_TABLE"})
        self.assertEqual(names - set(DECLARED), {"NEW_TABLE"})

    def test_private_and_lowercase_names_are_not_surface_names(self):
        self.assertEqual(
            G.surface_names({"m.py": "_PRIVATE = 1\nlower = 2\nMixed = 3\n"}), set()
        )

    def test_the_guard_passes_at_head(self):
        self.assertEqual(G.main([]), 0)


if __name__ == "__main__":
    unittest.main()
