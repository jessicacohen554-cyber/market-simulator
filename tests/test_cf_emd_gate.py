"""The operating-shape regression gate (cf_emd / pearson_r) in the report.

`_print_cf_emd_gate` is the live-path gate the audit's §D3 / follow-up D-tests
recommend: a tuning run must not degrade per-class operating shape below the
keeper baseline. It is the check the annual-volume gate is blind to (a class
can pass on TWh while missing its CF distribution).
"""
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "run_calibration_full", REPO / "scripts" / "run_calibration_full.py")
_RCF = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RCF)

_BASELINE = REPO / "inputs" / "calibration" / "cf_emd_baseline_ERCOT.json"
_KEEPER_FIT = (REPO / "results" / "calibration" / "keeper_anchor"
               / "plant_hourly_fit.parquet")


def test_baseline_file_is_well_formed():
    base = json.loads(_BASELINE.read_text())["classes"]
    assert "CC_REGULAR" in base
    cc = base["CC_REGULAR"]
    assert set(cc) == {"2023", "2024", "2025"}
    for yr in cc.values():
        assert 0.0 < yr["cf_emd"] < 1.0
        assert -1.0 <= yr["pearson_r"] <= 1.0


@pytest.mark.skipif(not _KEEPER_FIT.exists(),
                    reason="keeper_anchor bundle not present")
def test_keeper_passes_its_own_baseline(capsys):
    # The baseline is the keeper of record, so the keeper's own fit must PASS.
    fit = pd.read_parquet(_KEEPER_FIT)
    _RCF._print_cf_emd_gate(fit, "ERCOT")
    out = capsys.readouterr().out
    assert "operating-shape gate: PASS" in out


@pytest.mark.skipif(not _KEEPER_FIT.exists(),
                    reason="keeper_anchor bundle not present")
def test_degraded_shape_is_flagged(capsys):
    # Inflate every plant's cf_emd far past the margin and crush r: must FAIL.
    fit = pd.read_parquet(_KEEPER_FIT).copy()
    fit["cf_emd"] = fit["cf_emd"] + 0.30
    fit["pearson_r"] = fit["pearson_r"] - 0.30
    _RCF._print_cf_emd_gate(fit, "ERCOT")
    out = capsys.readouterr().out
    assert "regression(s)" in out
    assert "PASS" != out.strip().splitlines()[-1]


def test_missing_baseline_skips_not_passes(capsys):
    # A class/ISO with no baseline must SKIP, never silently pass.
    fit = pd.read_parquet(_KEEPER_FIT) if _KEEPER_FIT.exists() else pd.DataFrame(
        {"plant_code": [], "year": [], "cf_emd": [], "pearson_r": [],
         "cap_mw": []})
    _RCF._print_cf_emd_gate(fit, "MISO")  # no cf_emd_baseline_MISO.json
    out = capsys.readouterr().out
    assert "SKIPPED" in out
