"""Facade / same-name-shim re-export guards for the orchestrator-unification
lane (refactor-consolidation plan §5, wave-3 facade note).

Every extraction out of ``scripts/run_calibration.py`` /
``scripts/run_calibration_full.py`` leaves PERMANENT same-name aliases behind
(the scripts' exported symbols are load-bearing for probe scripts, tests, and
``run_calibration_full``'s seam imports — frozen surface, never renamed).
These tests pin each shim to its canonical pipeline home so a later cleanup
cannot silently drop one.
"""

from __future__ import annotations

import market_sim.pipeline as pipeline
import market_sim.pipeline.ttc as ttc
import market_sim.pipeline.year as year_mod
import scripts.run_calibration as rc


class TestTtcShims:
    """run_calibration keeps same-name aliases for the moved TTC helpers."""

    def test_apply_ttc_overrides_shim(self):
        assert rc._apply_ttc_overrides is ttc.apply_ttc_overrides

    def test_apply_iso_year_ttc_shim(self):
        assert rc._apply_iso_year_ttc is ttc.apply_iso_year_ttc

    def test_apply_iso_monthly_ttc_shim(self):
        assert rc._apply_iso_monthly_ttc is ttc.apply_iso_monthly_ttc

    def test_ttc_link_zones_shim(self):
        assert rc._TTC_LINK_ZONES is ttc.TTC_LINK_ZONES

    def test_backcast_config_shim(self):
        # Stage-7 precedent this lane extends: the old private name stays.
        assert rc._calibration_config is pipeline.backcast_config

    def test_commitment_pass_shim(self):
        assert rc._commitment_pass is pipeline.run_commitment_pass


class TestReferenceShims:
    """run_calibration keeps same-name aliases for the reference half."""

    def test_load_reference_shim(self):
        import market_sim.pipeline.reference as ref

        assert rc._load_reference is ref.load_reference
        assert rc._henry_hub_actual is ref.henry_hub_actual
        assert rc._HENRY_HUB_FALLBACK is ref.HENRY_HUB_FALLBACK
        assert rc.REFERENCE_PATH == ref.REFERENCE_PATH


class TestPersistReportShims:
    """run_calibration_full keeps same-name aliases for persist/report."""

    def test_persist_shims(self):
        import market_sim.pipeline.persist as persist
        import scripts.run_calibration_full as rcf

        assert rcf._environment_block is persist.environment_block
        assert rcf._parse_offer_curve_json is persist.parse_offer_curve_json
        assert rcf._json_default is persist.json_default
        assert rcf._git_sha is persist.git_sha
        assert rcf._git is persist.git_cmd
        assert rcf._git_state is persist.git_state
        assert rcf._highspy_version is persist.highspy_version
        assert rcf._ENVIRONMENT_PACKAGES is persist.ENVIRONMENT_PACKAGES
        assert rcf._GIT_STATE_EXCLUDE is persist.GIT_STATE_EXCLUDE
        assert rcf.write_run_config is persist.write_run_config

    def test_report_shims(self):
        import market_sim.pipeline.report as report
        import scripts.run_calibration_full as rcf

        assert rcf._hour_to_month is report.hour_to_month
        assert rcf._hourly_to_monthly is report.hourly_to_monthly
        assert rcf._pearson_r is report.pearson_r
        assert rcf._nrmse is report.nrmse
        assert rcf._print_table is report.print_table
        assert rcf._DAYS_IN_MONTH is report.DAYS_IN_MONTH
        assert rcf._MONTH_NAMES is report.MONTH_NAMES


class TestPipelinePackageSurface:
    """The pipeline package re-exports the lane's new public surface."""

    def test_year_exports(self):
        assert pipeline.run_year_solve is year_mod.run_year_solve
        assert pipeline.YearSolveOutput is year_mod.YearSolveOutput

    def test_ttc_exports(self):
        assert pipeline.build_transmission_base is ttc.build_transmission_base
        assert pipeline.apply_ttc_overrides is ttc.apply_ttc_overrides
        assert pipeline.apply_iso_year_ttc is ttc.apply_iso_year_ttc
        assert pipeline.apply_iso_monthly_ttc is ttc.apply_iso_monthly_ttc

    def test_api_exports(self):
        import market_sim.pipeline.api as api

        assert pipeline.run_scenario is api.run_scenario
        assert pipeline.run_pair is api.run_pair
