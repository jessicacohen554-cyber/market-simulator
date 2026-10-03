"""Tests for the FC-7 forecast DOF-ledger INSTRUMENT (capx-D8).

Grew out of the FR-27 stub tests. The load-bearing properties, in order:

1. **An UNIDENTIFIED entry never improves a verdict.** It carries the literal
   ``unattested`` token, and FC-7 scores a ledger holding one exactly as it
   scores an absent ledger. If that stops holding, the instrument has become
   the artifact rule 21 exists to prevent — a ledger that looks attested and
   is not.
2. **The instrument reports identification, it never supplies one** (rule 21):
   a curated row is applied only when its cross-check gate passes — the run
   value must match the registered override / the row's expected value — and
   a refused row leaves the entry UNIDENTIFIED with the refusal recorded.
3. The enumeration scope is unchanged from the stub: non-default
   solve-affecting fields only, selectors excluded, representation
   (tuple/list) normalized.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import forecast_verdict as fv  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "build_forecast_dof_ledger_under_test",
    str(REPO_ROOT / "scripts" / "build_forecast_dof_ledger.py"),
)
bl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bl)


def _ledger(sc, **kw):
    """Trivial-fixture builder: wrap a bare scenario dict, no git context."""
    kw.setdefault("use_git", False)
    return bl.build_ledger({"scenario_config": sc}, **kw)


class UnidentifiedNeverImprovesAVerdictTests(unittest.TestCase):
    """Property 1 — the honesty pin carried over from the stub.

    NOTE on fixture values: the ledger excludes fields sitting at their
    shipped default, so every fixture supplies a genuinely NON-default value
    (``entry_rate_limits``/``entry_commissioning_lag`` ship ``True`` since
    owner decision D-2, 2026-08-02 — hence ``False`` here). Nothing depends on
    WHICH value is armed, only that it differs from the shipped default and
    carries no committed identification.
    """

    def test_an_unidentified_entry_scores_exactly_as_an_absent_ledger(self):
        led = _ledger({"iso": "PJM", "entry_rate_limits": False})
        self.assertTrue(led["entries"], "instrument produced no entries to test")
        self.assertEqual(led["n_unidentified"], led["n_entries"])
        for tier in ("t1", "t2", "t3"):
            with self.subTest(tier=tier):
                absent = fv._score_dof_ledger({}, tier)
                got = fv._score_dof_ledger({"dof_ledger": led}, tier)
                self.assertEqual(got["status"], absent["status"])

    def test_the_caveat_detail_names_what_must_be_attested(self):
        led = _ledger({"iso": "PJM", "entry_rate_limits": False})
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertIn("entry_rate_limits", row["detail"])

    def test_unidentified_entries_carry_only_the_unattested_token(self):
        led = _ledger({"iso": "MISO", "entry_commissioning_lag": False})
        self.assertTrue(led["entries"])
        for e in led["entries"]:
            self.assertEqual(e["identification"], bl.UNATTESTED)
            self.assertEqual(e["status"], "UNIDENTIFIED")
            self.assertIn("attestation_question", e)
        self.assertEqual(led["n_unattested"], led["n_entries"])

    def test_a_mixed_ledger_still_caveats(self):
        # One identified entry (the D-10 posture) + one unidentified: the
        # unidentified row must keep the CAVEAT.
        led = _ledger(
            {
                "iso": "PJM",
                "forecast_xyear_warmstart": False,
                "entry_rate_limits": False,
            }
        )
        self.assertEqual(led["n_identified"], 1)
        self.assertEqual(led["n_unidentified"], 1)
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.CAVEAT)

    def test_a_fully_identified_ledger_can_pass_fc7(self):
        # The design intent, pinned: identification drawn from committed
        # evidence CAN retire the CAVEAT on a chartered re-score.
        led = _ledger({"iso": "PJM", "forecast_xyear_warmstart": False})
        self.assertEqual(led["n_unidentified"], 0)
        self.assertTrue(led["entries"])
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.PASS)

    def test_a_residual_without_a_root_cause_still_fails(self):
        led = _ledger({"iso": "PJM", "forecast_xyear_warmstart": False})
        led["entries"][0]["identification"] = "residual"
        led["entries"][0].pop("root_cause", None)
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.FAIL)
        self.assertIn("root_cause", row["detail"])


class AttributionCrossCheckTests(unittest.TestCase):
    """Property 2 — a curated row applies only when its gate passes."""

    def test_the_d10_warmstart_posture_is_identified_as_design_decision(self):
        led = _ledger({"iso": "NYISO", "forecast_xyear_warmstart": False})
        (e,) = led["entries"]
        self.assertEqual(e["name"], "forecast_xyear_warmstart")
        self.assertEqual(e["identification"], "design-decision")
        self.assertEqual(e["status"], "IDENTIFIED")
        self.assertIn("D-10", e["source"])
        self.assertEqual(e["provenance"], "runner-posture")

    def test_a_value_mismatch_refuses_the_curated_identification(self):
        # forecast_xyear_warmstart=True is non-default AND fails the curated
        # row's expected-value gate (D-10 says False) — the entry must stay
        # UNIDENTIFIED with the refusal recorded, never be identified anyway.
        defaults = {"forecast_xyear_warmstart": False}
        entries, _ = bl.build_entries(
            {"forecast_xyear_warmstart": True},
            defaults,
            iso="NYISO",
            use_git=False,
        )
        (e,) = entries
        self.assertEqual(e["identification"], bl.UNATTESTED)
        self.assertEqual(e["status"], "UNIDENTIFIED")
        self.assertIn("refused", e["curation_refused"])

    def test_neiso_registry_overrides_identify_only_at_the_registered_value(self):
        overrides = bl._iso_registry_overrides("NEISO")
        if not overrides:
            self.skipTest("market_sim ISO registry not importable here")
        self.assertIn("ordc_voll", overrides)
        registered = overrides["ordc_voll"]
        # At the registered value: identified, published, iso-registry.
        led = _ledger({"iso": "NEISO", "ordc_voll": registered})
        (e,) = led["entries"]
        self.assertEqual(e["identification"], "published")
        self.assertEqual(e["provenance"], "iso-registry")
        self.assertIn("iso_configs", e["where"])
        # At any other value the registry match fails, the curated row's
        # requires-gate refuses, and the entry stays UNIDENTIFIED.
        led = _ledger({"iso": "NEISO", "ordc_voll": registered + 123.0})
        (e,) = led["entries"]
        self.assertEqual(e["identification"], bl.UNATTESTED)
        self.assertIn("registry", e["curation_refused"])

    def test_another_isos_run_never_borrows_neiso_curation(self):
        # Rule 25 [R-ISO-SCOPE]: the NEISO ordc rows are NEISO's. The same
        # field/value in a PJM run must stay UNIDENTIFIED (PJM registers no
        # such override).
        overrides = bl._iso_registry_overrides("NEISO")
        if not overrides:
            self.skipTest("market_sim ISO registry not importable here")
        led = _ledger({"iso": "PJM", "ordc_voll": overrides["ordc_voll"]})
        (e,) = led["entries"]
        self.assertEqual(e["identification"], bl.UNATTESTED)

    def test_design_decision_never_identifies_a_numeric_magnitude(self):
        entry = {
            "name": "x",
            "identification": bl.UNATTESTED,
            "status": "UNIDENTIFIED",
            "source": "",
            "evidence": "",
        }
        row = {"identification": "design-decision", "source": "s", "evidence": "e"}
        bl.CURATED_IDENTIFICATIONS[("*", "x")] = row
        try:
            bl._apply_curation(entry, 3.14, None, registry_matched=False)
        finally:
            del bl.CURATED_IDENTIFICATIONS[("*", "x")]
        self.assertEqual(entry["identification"], bl.UNATTESTED)
        self.assertIn("magnitude", entry["curation_refused"])


class EnumerationScopeTests(unittest.TestCase):
    """Property 3 — what the ledger enumerates, and what it deliberately does not."""

    def test_scenario_selectors_are_not_free_parameters(self):
        led = _ledger({"iso": "PJM", "start_year": 2026, "end_year": 2030})
        names = {e["name"] for e in led["entries"]}
        self.assertNotIn("start_year", names)
        self.assertNotIn("iso", names)

    def test_default_valued_fields_are_excluded_when_defaults_resolve(self):
        # An un-armed mechanism flag is not a free parameter OF THIS RUN.
        defaults = {"entry_rate_limits": False, "entry_commissioning_lag": False}
        entries, _ = bl.build_entries(
            {"entry_rate_limits": False, "entry_commissioning_lag": True},
            defaults,
            use_git=False,
        )
        self.assertEqual([e["name"] for e in entries], ["entry_commissioning_lag"])

    def test_tuple_vs_list_representation_is_not_a_free_parameter(self):
        # The FFR-3B stub compared raw and mis-listed every tuple-valued
        # default (the offer-surface families) as non-default. Pinned fixed.
        defaults = {"pjm_offer_surface_netload_pcts": (0.8, 0.9, 0.97)}
        entries, _ = bl.build_entries(
            {"pjm_offer_surface_netload_pcts": [0.8, 0.9, 0.97]},
            defaults,
            use_git=False,
        )
        self.assertEqual(entries, [])

    def test_a_null_where_head_ships_a_default_is_reported_not_scored(self):
        defaults = {"capacity_market_clearing_by_iso": {"PJM": True}}
        entries, drift = bl.build_entries(
            {"capacity_market_clearing_by_iso": None},
            defaults,
            use_git=False,
        )
        self.assertEqual(entries, [])
        (d,) = drift
        self.assertEqual(d["name"], "capacity_market_clearing_by_iso")
        self.assertIsNone(d["run_value"])

    def test_without_defaults_the_wider_scope_is_declared_not_hidden(self):
        real = bl._defaults
        bl._defaults = lambda: None
        try:
            led = _ledger({"entry_rate_limits": False})
        finally:
            bl._defaults = real
        self.assertFalse(led["defaults_available"])
        self.assertIn("WIDER", led["scope"])

    def test_grouping_assigns_every_entry_exactly_one_group(self):
        led = _ledger(
            {
                # Deliberately non-default (the shipped default is 3), so the
                # default-value filter keeps it.
                "retirement_years_coal": 7,
                "entry_rate_limits": False,
                "ercot_gas_commitment_bridge": True,
            }
        )
        groups = {e["name"]: e["group"] for e in led["entries"]}
        self.assertEqual(groups.get("retirement_years_coal"), "retirement")
        self.assertEqual(groups.get("entry_rate_limits"), "entry")
        self.assertEqual(
            groups.get("ercot_gas_commitment_bridge"), "dispatch_mechanism"
        )

    def test_n_scalars_matches_the_backcast_census_convention(self):
        # Booleans are decisions, not magnitudes — they must not inflate the
        # tuned-scalar count the backcast ledger reports the same way.
        self.assertEqual(bl._count_scalars(True), 0)
        self.assertEqual(bl._count_scalars({"a": 1.0, "b": {"c": 2}}), 2)


class CliTests(unittest.TestCase):
    def test_writes_a_ledger_next_to_the_run_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "run_config.json").write_text(
                json.dumps(
                    {"scenario_config": {"iso": "PJM", "entry_rate_limits": False}}
                )
            )
            self.assertEqual(bl.main([str(bundle), "--no-git"]), 0)
            led = json.loads((bundle / "dof_ledger.json").read_text())
            self.assertEqual(led["schema"], "dof-ledger/v1")
            self.assertIn("INSTRUMENT", led["status"])
            self.assertIn("UNIDENTIFIED", led["status"])

    def test_missing_config_is_an_explicit_error_not_an_empty_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                bl.main([tmp, "--no-git"])


#: The six (ISO, field) pairs capx D63 curated — the two negatives
#: FINDING-capx-d60-2026-09-05.md §8 routed rather than absorbing.
D63_ROWS = (
    ("MISO", "entry_vre_capacity_revenue"),
    ("MISO", "entry_vre_zone_selection"),
    ("MISO", "miso_rps_compliance_regions"),
    ("MISO", "miso_clean_tier_rows"),
    ("MISO", "retirement_sector_gate"),
    ("CAISO", "negative_renewable_offers"),
)


class D63CuratedRowTests(unittest.TestCase):
    """capx D63 — the MISO + CAISO rows, under the same properties as D60-R3's.

    These are attestation rows only: each REPORTS an identification already
    committed to the repository (rule 21 ``[R-DOF]``), keyed ``(ISO, field)``
    so it can never reach another ISO (rule 25 ``[R-ISO-SCOPE]``), and gated on
    ``requires="iso-registry"`` so it identifies only the value the registry
    actually carries.
    """

    def test_every_row_is_iso_keyed_and_registry_gated(self):
        # Rule 25 by construction: a ("*", field) row would identify the same
        # field in every ISO. None of the six may be one.
        for iso, field in D63_ROWS:
            with self.subTest(iso=iso, field=field):
                self.assertIn((iso, field), bl.CURATED_IDENTIFICATIONS)
                self.assertNotIn(("*", field), bl.CURATED_IDENTIFICATIONS)
                row = bl.CURATED_IDENTIFICATIONS[(iso, field)]
                self.assertEqual(row["requires"], "iso-registry")
                self.assertNotIn("expected", row)
                self.assertEqual(row["identification"], "design-decision")
                self.assertTrue(row["source"].strip())
                self.assertTrue(row["evidence"].strip())

    def test_each_row_identifies_only_at_the_registered_value(self):
        for iso, field in D63_ROWS:
            with self.subTest(iso=iso, field=field):
                overrides = bl._iso_registry_overrides(iso)
                if not overrides:
                    self.skipTest("market_sim ISO registry not importable here")
                self.assertIn(field, overrides, f"{iso} no longer registers {field}")
                led = _ledger({"iso": iso, field: overrides[field]})
                (e,) = [x for x in led["entries"] if x["name"] == field]
                self.assertEqual(e["identification"], "design-decision")
                self.assertEqual(e["status"], "IDENTIFIED")
                self.assertEqual(e["provenance"], "iso-registry")
                self.assertNotIn("curation_refused", e)

    def test_the_requires_gate_refuses_when_the_registry_match_fails(self):
        # The values are booleans, so the "wrong value" pole is the dataclass
        # default and is excluded from the ledger entirely. The gate itself is
        # therefore exercised directly, which is the property that matters: a
        # run carrying the field from anywhere but the live registered override
        # stays UNIDENTIFIED and the artifact records why.
        for iso, field in D63_ROWS:
            with self.subTest(iso=iso, field=field):
                entry = {
                    "name": field,
                    "identification": bl.UNATTESTED,
                    "status": "UNIDENTIFIED",
                    "source": "",
                    "evidence": "",
                }
                bl._apply_curation(entry, True, iso, registry_matched=False)
                self.assertEqual(entry["identification"], bl.UNATTESTED)
                self.assertIn("registry", entry["curation_refused"])

    def test_another_isos_run_never_borrows_a_d63_row(self):
        # Rule 25 [R-ISO-SCOPE]: MISO's five are MISO's and CAISO's is CAISO's.
        # The same field at the same value in another ISO's run stays
        # UNIDENTIFIED — a verdict never transfers across an ISO boundary.
        for iso, field in D63_ROWS:
            other = "NEISO" if iso != "NEISO" else "PJM"
            with self.subTest(iso=iso, field=field, other=other):
                led = _ledger({"iso": other, field: True})
                rows = [x for x in led["entries"] if x["name"] == field]
                if not rows:
                    self.skipTest(f"{field} is not non-default for {other}")
                (e,) = rows
                self.assertEqual(e["identification"], bl.UNATTESTED)

    def test_the_miso_and_caiso_registry_override_sets_are_now_fully_identified(
        self,
    ):
        # The lane's own object, asserted end to end: with the six rows in
        # place, no MISO or CAISO registry override enumerated by the ledger
        # carries the `unattested` token, so FC-7's DOF-ledger row can read
        # PASS on those two ISOs. This is the property that would silently rot
        # if a later lane armed a seventh override without its curated row.
        for iso in ("MISO", "CAISO"):
            with self.subTest(iso=iso):
                overrides = bl._iso_registry_overrides(iso)
                if not overrides:
                    self.skipTest("market_sim ISO registry not importable here")
                led = _ledger({"iso": iso, **overrides})
                unattested = [
                    e["name"]
                    for e in led["entries"]
                    if e["identification"] == bl.UNATTESTED
                ]
                self.assertEqual(unattested, [], f"{iso} overrides unattested")

    def test_a_fully_identified_ledger_retires_the_fc7_caveat(self):
        # The measurement half of the same property, through the scorer the
        # board actually reads: a ledger whose every entry is identified no
        # longer draws the CAVEAT an absent ledger draws.
        overrides = bl._iso_registry_overrides("CAISO")
        if not overrides:
            self.skipTest("market_sim ISO registry not importable here")
        led = _ledger({"iso": "CAISO", **overrides})
        self.assertEqual(led["n_unidentified"], 0)
        row = fv._score_dof_ledger({"dof_ledger": led}, "t1")
        self.assertEqual(row["status"], fv.PASS)


if __name__ == "__main__":
    unittest.main()


def _carry_repo(
    tmp: Path, *, keeper: str | None, entries, bundle_rel="results/calibration/x_span"
):
    """A synthetic checkout: keeper shard -> registry sidecar -> bundle attestation.

    ``keeper=None`` writes no shard at all; ``entries=None`` writes the shard and
    the registry sidecar but no attestation (an unresolvable bundle).
    """
    if keeper is None:
        return tmp
    shard_dir = tmp / "frontend" / "data" / "backcast" / "keepers"
    shard_dir.mkdir(parents=True)
    (shard_dir / "NEISO.json").write_text(
        json.dumps({"iso": "NEISO", "keeper": keeper})
    )
    reg_dir = tmp / "frontend" / "data" / "backcast" / "registry"
    reg_dir.mkdir(parents=True)
    (reg_dir / f"{keeper}.json").write_text(
        json.dumps({"id": keeper, "iso": "NEISO", "bundle": bundle_rel})
    )
    if entries is not None:
        bundle = tmp / bundle_rel
        bundle.mkdir(parents=True)
        (bundle / "calibration_attestation.json").write_text(
            json.dumps({"free_parameters": {"entries": entries}})
        )
    return tmp


#: A keeper ledger shaped like the W0 NEISO one: four residual rows (two curated
#: not-live, one curated live, one uncurated) and two measured rows (one curated
#: not-live, one curated live for NEISO only).
_KEEPER_ENTRIES = [
    {
        "name": "offer_curve_by_group",
        "identification": "residual",
        "root_cause": "open: D-6",
    },
    {
        "name": "offer_curve_committed_below_floor[NEISO]",
        "identification": "residual",
        "root_cause": "open",
    },
    {
        "name": "offer_curve_smoothing",
        "identification": "residual",
        "root_cause": "open",
    },
    {"name": "wefor_multiplier", "identification": "residual", "root_cause": "open"},
    {"name": "reliability_floor coefficients", "identification": "measured-physical"},
    {
        "name": "IMPORT_TRANCHES/EXPORT_TRANCHES[NEISO]",
        "identification": "measured-physical",
    },
]

_SCORED_FIELDS = (
    "status",
    "n_entries",
    "n_identified",
    "n_unidentified",
    "n_unattested",
    "n_by_group",
    "entries",
)


class KeeperCarryIsReportOnlyTests(unittest.TestCase):
    """capx D107 (D103 §3): the keeper_carry block reports, never scores."""

    SC = {"iso": "NEISO", "entry_rate_limits": False}

    def _with_and_without(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            with_repo = _carry_repo(Path(a), keeper="k-1", entries=_KEEPER_ENTRIES)
            without_repo = _carry_repo(Path(b), keeper=None, entries=None)
            return (
                _ledger(self.SC, repo=with_repo),
                _ledger(self.SC, repo=without_repo),
            )

    def test_block_present_for_an_iso_with_a_keeper_and_curated_rows(self):
        led, _ = self._with_and_without()
        carry = led["keeper_carry"]
        self.assertEqual(carry["keeper"], "k-1")
        self.assertEqual(carry["keeper_bundle"], "results/calibration/x_span")
        names = lambda k: [r["name"] for r in carry[k]]  # noqa: E731
        self.assertEqual(names("carried_residual"), ["offer_curve_smoothing"])
        self.assertEqual(
            names("carried_measured"), ["IMPORT_TRANCHES/EXPORT_TRANCHES[NEISO]"]
        )
        self.assertEqual(
            names("not_applicable_in_forecast"),
            [
                "offer_curve_by_group",
                "offer_curve_committed_below_floor[NEISO]",
                "wefor_multiplier",
                "reliability_floor coefficients",
            ],
        )
        # Every row keeps the keeper's own identification; a carried residual
        # names its source in rule-21 wording and its forecast field.
        self.assertTrue(
            all(
                r["keeper"] == "k-1"
                for k in (
                    "carried_residual",
                    "carried_measured",
                    "not_applicable_in_forecast",
                )
                for r in carry[k]
            )
        )
        res = carry["carried_residual"][0]
        self.assertEqual(res["identification"], "residual")
        self.assertIn(
            "carried residual — k-1 free_parameters[offer_curve_smoothing]",
            res["source"],
        )
        self.assertIn(
            "identification unchanged from the backcast keeper (rule 21)", res["source"]
        )
        self.assertEqual(res["forecast_field"], "offer_curve_smoothing_n/_exp")
        self.assertEqual(res["root_cause"], "open")
        # The uncurated row reports no field and no why — it is not claimed live.
        uncurated = next(
            r
            for r in carry["not_applicable_in_forecast"]
            if r["name"] == "offer_curve_committed_below_floor[NEISO]"
        )
        self.assertIsNone(uncurated["forecast_field"])
        self.assertIsNone(uncurated["why"])
        self.assertEqual(carry["n_carried_residual"], 1)
        self.assertEqual(carry["n_carried_measured"], 1)
        self.assertEqual(carry["n_not_applicable_in_forecast"], 4)
        # The block never masquerades as a scored entry.
        for key in (
            "carried_residual",
            "carried_measured",
            "not_applicable_in_forecast",
        ):
            for r in carry[key]:
                self.assertNotIn("status", r)
                self.assertNotIn("group", r)

    def test_block_absent_without_a_keeper(self):
        _, led = self._with_and_without()
        self.assertNotIn("keeper_carry", led)
        self.assertNotIn("registry_identification", led)

    def test_block_absent_when_the_keeper_bundle_does_not_resolve(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _carry_repo(Path(d), keeper="k-1", entries=None)
            led = _ledger(self.SC, repo=repo)
        # The designation is still reported; the carry is not invented.
        self.assertEqual(
            led["registry_identification"]["backcast_keeper_at_build"], "k-1"
        )
        self.assertNotIn("keeper_carry", led)
        self.assertIsNone(bl._keeper_bundle("absent-keeper", repo=Path(d)))

    def test_block_absent_when_the_attestation_carries_no_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _carry_repo(Path(d), keeper="k-1", entries=[])
            self.assertIsNone(bl._keeper_carry("NEISO", "k-1", repo=repo))
            self.assertIsNone(bl._keeper_carry(None, "k-1", repo=repo))
            self.assertIsNone(bl._keeper_carry("NEISO", None, repo=repo))

    def test_bundle_resolves_only_through_the_registry_sidecar(self):
        with tempfile.TemporaryDirectory() as d:
            repo = _carry_repo(
                Path(d),
                keeper="2026-10-02-w0-x",
                entries=_KEEPER_ENTRIES,
                bundle_rel="results/calibration/w0_x_span",
            )
            # The id implies nothing; the sidecar's `bundle` field is the map.
            self.assertEqual(
                bl._keeper_bundle("2026-10-02-w0-x", repo=repo),
                repo / "results" / "calibration" / "w0_x_span",
            )
            (repo / "frontend/data/backcast/registry/2026-10-02-w0-x.json").write_text(
                json.dumps({"id": "2026-10-02-w0-x"})
            )
            self.assertIsNone(bl._keeper_bundle("2026-10-02-w0-x", repo=repo))

    def test_scored_entries_and_fc7_are_byte_identical_with_and_without_the_block(self):
        with_block, without_block = self._with_and_without()
        self.assertIn("keeper_carry", with_block)
        self.assertNotIn("keeper_carry", without_block)
        self.assertTrue(with_block["entries"], "instrument produced no entries")
        for key in _SCORED_FIELDS:
            with self.subTest(field=key):
                self.assertEqual(
                    json.dumps(with_block[key], sort_keys=True),
                    json.dumps(without_block[key], sort_keys=True),
                )
        for tier in ("t1", "t2", "t3"):
            with self.subTest(tier=tier):
                a = fv._score_dof_ledger({"dof_ledger": with_block}, tier)
                b = fv._score_dof_ledger({"dof_ledger": without_block}, tier)
                self.assertEqual(a, b)

    def test_a_carried_residual_never_identifies_a_scored_entry(self):
        # The same armed field stays UNIDENTIFIED whether or not the keeper
        # carries a residual for a neighbouring parameter: the block supplies
        # no identification.
        with_block, _ = self._with_and_without()
        self.assertEqual(with_block["n_unidentified"], with_block["n_entries"])
        self.assertEqual(with_block["keeper_carry"]["n_carried_residual"], 1)
