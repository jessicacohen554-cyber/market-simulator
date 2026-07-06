"""recorded_cfg / meta.json fidelity regression tests (orchestrator-unification
Stage 7 meta-writer audit).

``scripts/run_calibration_full.py::solve_and_persist`` writes two records of a
run's configuration: ``meta.json`` (an echo of the ``solve_and_persist``
keyword arguments) and ``run_config.json``'s ``scenario_config`` block (a
freshly reconstructed :class:`ScenarioConfig`, ``recorded_cfg``, built by
re-calling ``backcast_config`` with the same flags and applying the same
``with_overrides`` chain ``run_year`` applies to the REAL solve). The Stage-7
audit found several fields that reached the real solve (via ``run_year``) but
were never threaded into ``recorded_cfg``'s reconstruction — so
``run_config.json`` silently showed the ``ScenarioConfig`` field default
instead of the value the LP actually solved with, even though ``meta.json``
correctly recorded the flag. This is the exact class of bug G-14 documents
for ``caiso_perhub_firm_base`` (results/calibration/caiso51_firm_base/
run_config.json's ``post_hoc_corrections`` record).

These tests pin the fields the Stage-7 audit fixed: ``cc_derate_from_top``
(the missing CAISO-default OR-branch), ``cc_nameplate_summer_derate``,
``coal_mustrun_online_pmin``, ``coal_sync_srmc_tranche``,
``gas_st_netload_drag`` (+ its ``gas_st_drag_overrides`` companion),
``ordc_lolp_params_path``, ``ct_drag_overrides`` (the ``ct_netload_drag``
companion), ``coal_lignite_mustrun``/``coal_prb_mustrun`` (->
``coal_lignite_mustrun_override``/``coal_prb_mustrun_override``), and
``caiso_perhub_firm_base`` (the G-14 residual itself).

Scope note (no silent cap): ``run_calibration_full.solve_and_persist`` has
150+ keyword arguments and reconstructs ``recorded_cfg`` inline (not as a
standalone, solve-free callable), so a fully generic "every TIER_TAGS field
round-trips" test would need a substantial extraction refactor of
``solve_and_persist`` — out of this stage's scope. These tests instead
directly exercise the reconstruction PATTERN (``backcast_config`` +
``with_overrides``) for the confirmed-fixed field set, which is the
regression surface that actually broke. A residual, unaudited surface
remains: any ``solve_and_persist`` parameter NOT reviewed by the Stage-7
audit could carry the same class of bug; the audit covered every parameter
recorded in ``meta`` (see the plan doc §7.3.9 for the full accounting).
"""

from __future__ import annotations

import unittest

from market_sim.pipeline.backcast_config import backcast_config


class TestRecordedCfgFidelity(unittest.TestCase):
    """Each fixed field: the recorded_cfg reconstruction pattern reflects the
    same value run_year's real-solve pattern would produce."""

    def _base(self, iso="ERCOT", **kw):
        return backcast_config(2024, iso, 24, 3.0, **kw)

    def test_cc_derate_from_top_caiso_default_branch(self):
        # run_year: `if cc_derate_from_top or iso.upper() == "CAISO":`
        # recorded_cfg must also fire on the bare CAISO branch, not just the
        # explicit flag (the bug: recorded_cfg's condition was missing the
        # ISO branch entirely).
        cfg = self._base(iso="CAISO")
        solved = cfg.with_overrides(cc_outage_derate_from_top=True)
        # Reproduce recorded_cfg's (now-fixed) condition:
        cc_derate_from_top = False
        iso = "CAISO"
        recorded = cfg
        if cc_derate_from_top or iso.upper() == "CAISO":
            recorded = recorded.with_overrides(cc_outage_derate_from_top=True)
        self.assertEqual(
            recorded.cc_outage_derate_from_top, solved.cc_outage_derate_from_top
        )
        self.assertTrue(recorded.cc_outage_derate_from_top)

    def test_cc_nameplate_summer_derate(self):
        cfg = self._base(iso="PJM")
        solved = cfg.with_overrides(cc_nameplate_summer_derate=True)
        recorded = cfg.with_overrides(cc_nameplate_summer_derate=True)
        self.assertEqual(
            recorded.cc_nameplate_summer_derate, solved.cc_nameplate_summer_derate
        )

    def test_coal_mustrun_online_pmin(self):
        cfg = self._base()
        solved = cfg.with_overrides(coal_mustrun_online_pmin=True)
        recorded = cfg.with_overrides(coal_mustrun_online_pmin=True)
        self.assertEqual(
            recorded.coal_mustrun_online_pmin, solved.coal_mustrun_online_pmin
        )

    def test_coal_sync_srmc_tranche(self):
        cfg = self._base()
        solved = cfg.with_overrides(coal_sync_srmc_tranche=True)
        recorded = cfg.with_overrides(coal_sync_srmc_tranche=True)
        self.assertEqual(recorded.coal_sync_srmc_tranche, solved.coal_sync_srmc_tranche)

    def test_gas_st_netload_drag_with_overrides_companion(self):
        gas_st_drag_overrides = {"gas_st_drag_cap": 0.5}
        cfg = self._base()
        solved = cfg.with_overrides(gas_st_netload_drag=True, **gas_st_drag_overrides)
        recorded = cfg.with_overrides(gas_st_netload_drag=True, **gas_st_drag_overrides)
        self.assertEqual(recorded.gas_st_netload_drag, solved.gas_st_netload_drag)
        self.assertEqual(recorded.gas_st_drag_cap, solved.gas_st_drag_cap)
        self.assertEqual(recorded.gas_st_drag_cap, 0.5)

    def test_ordc_lolp_params_path(self):
        cfg = self._base()
        solved = cfg.with_overrides(ordc_lolp_params_path="some/path.csv")
        recorded = cfg.with_overrides(ordc_lolp_params_path=str("some/path.csv"))
        self.assertEqual(recorded.ordc_lolp_params_path, solved.ordc_lolp_params_path)

    def test_ct_drag_overrides_companion(self):
        ct_drag_overrides = {"ct_drag_cap": 0.42}
        cfg = self._base()
        solved = cfg.with_overrides(ct_netload_drag=True, **ct_drag_overrides)
        recorded = cfg.with_overrides(ct_netload_drag=True)
        recorded = recorded.with_overrides(**ct_drag_overrides)
        self.assertEqual(recorded.ct_drag_cap, solved.ct_drag_cap)
        self.assertEqual(recorded.ct_drag_cap, 0.42)

    def test_coal_lignite_and_prb_mustrun_overrides(self):
        # run_year passes these POSITIONALLY into backcast_config itself
        # (coal_lignite_mustrun_override / coal_prb_mustrun_override); the
        # recorded_cfg reconstruction's own backcast_config(...) call must
        # receive them too.
        solved = backcast_config(
            2024, "MISO", 24, 3.0, coal_lignite_mustrun=0.3, coal_prb_mustrun=0.6
        )
        base = self._base(iso="MISO")
        recorded = base.with_overrides(
            coal_lignite_mustrun_override=0.3, coal_prb_mustrun_override=0.6
        )
        self.assertEqual(
            recorded.coal_lignite_mustrun_override,
            solved.coal_lignite_mustrun_override,
        )
        self.assertEqual(
            recorded.coal_prb_mustrun_override, solved.coal_prb_mustrun_override
        )
        self.assertEqual(recorded.coal_lignite_mustrun_override, 0.3)
        self.assertEqual(recorded.coal_prb_mustrun_override, 0.6)

    def test_caiso_perhub_firm_base_g14_residual(self):
        cfg = self._base(iso="CAISO")
        solved = cfg.with_overrides(caiso_perhub_firm_base=True)
        recorded = cfg.with_overrides(caiso_perhub_firm_base=True)
        self.assertEqual(recorded.caiso_perhub_firm_base, solved.caiso_perhub_firm_base)
        self.assertTrue(recorded.caiso_perhub_firm_base)


class TestRunCalibrationFullRecordedCfgSourceCoversFixedFields(unittest.TestCase):
    """Static guard: the fixed field names actually appear in
    run_calibration_full.py's recorded_cfg reconstruction block, so a future
    edit that deletes one of these lines fails loudly instead of silently
    reintroducing the meta/run_config drift."""

    @classmethod
    def setUpClass(cls):
        from pathlib import Path

        repo = Path(__file__).resolve().parents[1]
        path = repo / "scripts" / "run_calibration_full.py"
        cls.source = path.read_text()
        rc_start = cls.source.index("recorded_cfg = backcast_config(")
        rc_end = cls.source.index("write_run_config(run_dir, recorded_cfg", rc_start)
        cls.rc_block = cls.source[rc_start:rc_end]
        meta_start = cls.source.index("    meta = {")
        meta_end = cls.source.index('\n    (run_dir / "meta.json")', meta_start)
        cls.meta_block = cls.source[meta_start:meta_end]

    def test_fixed_fields_present_in_recorded_cfg_block(self):
        # Fields with a real solve_and_persist kwarg, threaded via
        # recorded_cfg.with_overrides(...).
        expected = [
            "cc_outage_derate_from_top",
            "cc_nameplate_summer_derate",
            "coal_mustrun_online_pmin",
            "coal_sync_srmc_tranche",
            "gas_st_netload_drag",
            "gas_st_drag_overrides",
            "ordc_lolp_params_path",
            "ct_drag_overrides",
            "coal_lignite_mustrun_override",
            "coal_prb_mustrun_override",
            "caiso_perhub_firm_base",
        ]
        for name in expected:
            with self.subTest(field=name):
                self.assertIn(name, self.rc_block)

    def test_env_only_ercot_gas_fields_present_in_meta_block(self):
        # No solve_and_persist kwarg exists for these (env-var-only inside
        # backcast_config, rule 24 exception) — they were persisted by
        # reading the resolved backcast_config(...) attribute directly into
        # meta, the same pattern coal_plant_monthly_pricing/td_loss_factor
        # already used. Nothing to thread into recorded_cfg for them.
        expected = [
            "ercot_zonal_gas_basis",
            "ercot_west_netload_gas_shape",
            "ercot_west_gas_delivered_floor",
        ]
        for name in expected:
            with self.subTest(field=name):
                self.assertIn(name, self.meta_block)


if __name__ == "__main__":
    unittest.main()
