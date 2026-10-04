"""The benchmark rebuild recovers ``mustrun_chp_btm_holdout`` from every run_config block."""

import scripts.run_calibration_full as rcf


def test_off_when_absent():
    assert rcf._run_config_mustrun_chp_btm({}) is False
    assert rcf._run_config_mustrun_chp_btm({"scenario_config": {"mustrun_chp_btm_holdout": False}}) is False


def test_top_level_and_calibration_flags():
    assert rcf._run_config_mustrun_chp_btm({"mustrun_chp_btm_holdout": True}) is True
    assert rcf._run_config_mustrun_chp_btm({"calibration_flags": {"mustrun_chp_btm_holdout": True}}) is True


def test_replay_set_lands_in_scenario_config():
    """A replay_keeper --set records the flag only in the resolved scenario_config."""
    cfg = {"calibration_flags": {}, "scenario_config": {"mustrun_chp_btm_holdout": True}}
    assert rcf._run_config_mustrun_chp_btm(cfg) is True
