"""Tests for hindcast announced-exit verification (owner directive 2026-08-22).

Trivial-first, LP-free: the contract is that a hindcast's announced/"known"
retirement channel is confirmed and countered by the realized record — a plant
whose announced exit was reversed outright by a later public counter-instrument
(Byron/Dresden under IL CEJA's CMC) is never false-retired off stale vintage
EIA-860 data. Four seams are asserted without a solve:

* the ``ScenarioConfig`` field defaults off and is cache-key neutral at its
  default (the nyiso-119 registration discipline), hashing distinctly armed;
* the harness (``run_capacity_hindcast.build_config``) arms it by DEFAULT and
  ``--no-verified-announced-exits`` restores the ex-ante arm byte-identically;
* the harness meta records the SOLVED gate (``META_RECORD_SPEC``, FromConfig —
  FFR-3R: a meta may never claim a posture the solve lacked);
* the scorer's §c.5-1 lane classifies against the run's OWN vintage cutoff
  (``load_reversal_set(cutoff=...)``) and the default-path report renders the
  policy-saved note.
"""

from __future__ import annotations

from datetime import date

import pytest

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from scripts import run_capacity_hindcast as H
from scripts import score_capacity_hindcast as S


class TestConfigField:
    """Field default, registration, and cache-key behaviour."""

    def test_default_off(self):
        assert ScenarioConfig().hindcast_verified_announced_exits is False

    def test_registered_cache_key_optional(self):
        assert "hindcast_verified_announced_exits" in _CACHE_KEY_OPTIONAL_FIELDS
        assert (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["hindcast_verified_announced_exits"]
            == "False"
        )

    def test_cache_key_neutral_off_distinct_on(self):
        base = ScenarioConfig().cache_key()
        explicit_off = ScenarioConfig(
            hindcast_verified_announced_exits=False
        ).cache_key()
        armed = ScenarioConfig(hindcast_verified_announced_exits=True).cache_key()
        assert explicit_off == base  # dropped from the hash at its default
        assert armed != base  # an armed run is a distinct scenario


class TestHarnessPosture:
    """build_config arms verification by default; the off arm is ex-ante."""

    def test_harness_default_armed(self):
        cfg = H.build_config("NEISO", 2021, 2025, "realized")
        assert cfg.hindcast_verified_announced_exits is True

    def test_no_verified_announced_exits_arm(self):
        cfg = H.build_config(
            "NEISO", 2021, 2025, "realized", verified_announced_exits=False
        )
        assert cfg.hindcast_verified_announced_exits is False

    def test_arms_hash_distinctly(self):
        on = H.build_config("PJM", 2021, 2025, "realized")
        off = H.build_config(
            "PJM", 2021, 2025, "realized", verified_announced_exits=False
        )
        assert on.cache_key() != off.cache_key()

    def test_meta_records_solved_gate(self):
        """META_RECORD_SPEC carries the field FromConfig (never FromArgs)."""
        entry = H.META_RECORD_SPEC.sources["hindcast_verified_announced_exits"]
        assert isinstance(entry, H.FromConfig)


class TestScorerInformationSetCutoff:
    """load_reversal_set classifies against the run's own vintage cutoff V."""

    def test_default_cutoff_is_2020(self):
        rev = S.load_reversal_set("PJM")
        assert set(rev) == {("6023", "1"), ("6023", "2"), ("869", "2"), ("869", "3")}

    def test_explicit_2020_cutoff_matches_default(self):
        assert S.load_reversal_set("PJM", cutoff=date(2020, 12, 31)) == (
            S.load_reversal_set("PJM")
        )

    def test_post_reversal_cutoff_excludes(self):
        # V = 2022-12-31: the CEJA reversal (2021-09-15) was already knowable,
        # so Byron/Dresden leave the §c.5-1 class — a 2022-vintage run that
        # retired them has no information-set excuse.
        assert S.load_reversal_set("PJM", cutoff=date(2022, 12, 31)) == {}

    def test_pre_announcement_cutoff_excludes(self):
        # V = 2019-12-31: the ORIGINAL instrument (2020-08-27) was not yet
        # public either, so the rows fail the knowable-at-V original test.
        assert S.load_reversal_set("PJM", cutoff=date(2019, 12, 31)) == {}


class TestReportPolicySavedNote:
    """write_report renders the policy-saved section iff exposure is non-zero."""

    @staticmethod
    def _minimal_ret():
        return {
            "total_gw": {"actual": 1.0, "model": 5.0, "err_frac": 4.0, "band": "FAIL"},
            "unit_recall_gt300": {
                "n_big_actual": 1,
                "matched": 0,
                "recall": 0.0,
                "band": "FAIL",
                "plant_recall_frac": None,
                "plant_matched": 0,
            },
            "false_retire": {"false_gw": 4.0, "frac_of_model": 0.8, "band": "FAIL"},
            "per_fuel": {},
        }

    @staticmethod
    def _minimal_add():
        return {
            "basis": S.ADDITIONS_BASIS_DECISION,
            "by_tech": {
                t: {"actual_gw": 0.0, "model_gw": 0.0, "err_frac": None, "band": "PASS"}
                for t in S.ADDITION_TECHS
            },
            "shares": {
                t: {"actual_share": 0.0, "model_share": 0.0, "delta_pp": 0.0}
                for t in S.ADDITION_TECHS
            },
        }

    def _render(self, tmp_path, ret_is):
        path = tmp_path / "report.md"
        S.write_report(
            "PJM",
            "realized",
            {"bundle": "x"},
            self._minimal_ret(),
            self._minimal_add(),
            {"model": {}, "actual": {}},
            {"announced": {"retire_gw": 0.0, "add_gw": 0.0, "note": "test stub"}},
            path,
            ret_is=ret_is,
            is_cutoff="2020-12-31",
        )
        return path.read_text()

    def test_note_rendered_with_exposure(self, tmp_path):
        ret_is = {
            "reversal_exposure_gw": 4.097,
            "reversal_instruments": ["IL CEJA (P.A. 102-0662)"],
            "reversal_rows": [
                {
                    "unit_id": "6023_1",
                    "unit_name": "Byron 1",
                    "fuel": "nuclear",
                    "mw": 1164.0,
                    "instrument": "IL CEJA (P.A. 102-0662)",
                }
            ],
            "false_retire": {"false_gw": 0.5, "frac_of_model": 0.1, "band": "PASS"},
        }
        text = self._render(tmp_path, ret_is)
        assert "Announced exits reversed by later policy" in text
        assert "Byron 1" in text
        assert "4.097 GW" in text

    def test_note_absent_without_exposure(self, tmp_path):
        ret_is = {
            "reversal_exposure_gw": 0.0,
            "reversal_instruments": [],
            "reversal_rows": [],
            "false_retire": {"false_gw": 4.0, "frac_of_model": 0.8, "band": "FAIL"},
        }
        text = self._render(tmp_path, ret_is)
        assert "Announced exits reversed by later policy" not in text


class TestActualsMysticCoverage:
    """RD-5 third gap (2026-08-22): Mystic 8/9's 2024 exit is in the actuals."""

    def test_mystic_gas_cc_rows_present(self):
        actuals = S.load_actuals("NEISO")
        mystic = actuals[
            (actuals["kind"] == "retirement") & (actuals["plant_id"] == 1588)
        ]
        cc = mystic[mystic["fuel"] == "gas_cc"]
        assert len(cc) == 6  # GT81/GT82/ST85 + GT93/GT94/ST96
        assert cc["mw"].sum() == pytest.approx(1744.4)
        assert set(cc["year"]) == {2024}
