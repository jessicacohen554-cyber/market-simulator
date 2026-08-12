"""Hermetic tests for ``scripts/check_data_tier_report.py``.

The guard is the loud-failure half of card F's scheduled data tier (owner
signature F1, 2026-08-11): a data-missing skip or a deselected/red golden must
fail the workflow run, never pass silently. These tests pin both halves on
synthetic junit reports — no data, no pytest subprocess, fast tier.
"""

from __future__ import annotations

import sys

from tests.helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_data_tier_report import (  # noqa: E402
    GOLDEN_CLASSNAME,
    GOLDEN_NAME,
    check_report,
)

_GOLDEN_OK = (
    f'<testcase classname="{GOLDEN_CLASSNAME}" name="{GOLDEN_NAME}" time="70"/>'
)


def _write(tmp_path, body: str):
    path = tmp_path / "tier-report.xml"
    path.write_text(
        f'<testsuites><testsuite name="pytest">{body}</testsuite></testsuites>'
    )
    return path


def test_clean_report_passes(tmp_path):
    report = _write(
        tmp_path,
        _GOLDEN_OK
        + '<testcase classname="tests.curation.test_consume_fuel" name="t" time="1"/>',
    )
    assert check_report(report) == []


def test_missing_report_fails(tmp_path):
    problems = check_report(tmp_path / "absent.xml")
    assert len(problems) == 1
    assert "does not exist" in problems[0]


def test_data_missing_skip_fails(tmp_path):
    report = _write(
        tmp_path,
        _GOLDEN_OK
        + '<testcase classname="tests.curation.test_consume_fuel" name="t" time="0">'
        + '<skipped message="raw data input absent: missing '
        + "['data/raw/gas-prices/henry_hub_daily.csv']\"/></testcase>",
    )
    problems = check_report(report)
    assert len(problems) == 1
    assert "DATA-MISSING SKIP" in problems[0]


def test_benign_skip_passes(tmp_path):
    report = _write(
        tmp_path,
        _GOLDEN_OK
        + '<testcase classname="tests.regression.test_golden_forecast_bands" '
        + 'name="test_golden_bands_hold" time="0">'
        + '<skipped message="set RUN_GOLDEN_FORECAST=1 to solve the real '
        + '15-year ERCOT reference forecast (2026-2040)"/></testcase>',
    )
    assert check_report(report) == []


def test_golden_absent_fails(tmp_path):
    report = _write(
        tmp_path,
        '<testcase classname="tests.curation.test_consume_fuel" name="t" time="1"/>',
    )
    problems = check_report(report)
    assert len(problems) == 1
    assert "GOLDEN NOT RUN" in problems[0]


def test_golden_failed_fails(tmp_path):
    report = _write(
        tmp_path,
        f'<testcase classname="{GOLDEN_CLASSNAME}" name="{GOLDEN_NAME}" time="70">'
        '<failure message="FleetArrays drift vs the pre-split golden"/></testcase>',
    )
    problems = check_report(report)
    assert len(problems) == 1
    assert "GOLDEN NOT GREEN" in problems[0]


def test_golden_skipped_fails(tmp_path):
    report = _write(
        tmp_path,
        f'<testcase classname="{GOLDEN_CLASSNAME}" name="{GOLDEN_NAME}" time="0">'
        '<skipped message="some future gate"/></testcase>',
    )
    problems = check_report(report)
    assert len(problems) == 1
    assert "GOLDEN NOT GREEN" in problems[0]
