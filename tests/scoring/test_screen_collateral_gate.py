"""Unit tests for the rule-29 screen G-4 comparison (scripts/screen_collateral_gate.py).

Synthetic verdict dicts only — the pure ``compare_verdicts`` function is what a
screen's STOP gate rests on, so its flip / move / unscorable classification is
pinned here without any bundle, registry or solve.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "screen_collateral_gate", REPO / "scripts" / "screen_collateral_gate.py"
)
scg = importlib.util.module_from_spec(_spec)
sys.modules["screen_collateral_gate"] = scg
_spec.loader.exec_module(scg)


def _verdict(cells: dict[str, list[dict]]) -> dict:
    return {
        "determination": "n/a",
        "criteria": {cid: {"records": recs} for cid, recs in cells.items()},
    }


def _rec(cid, year, key, status, model=None, actual=None):
    return {
        "criterion": cid,
        "year": year,
        "key": key,
        "status": status,
        "model": model,
        "actual": actual,
        "magnitude": f"{status}",
    }


def test_pass_to_fail_on_gated_criterion_is_a_flip():
    keeper = _verdict({"fuelmix": [_rec("fuelmix", 2024, "CT_PEAKER", "PASS", 10, 12)]})
    arm = _verdict({"fuelmix": [_rec("fuelmix", 2024, "CT_PEAKER", "FAIL", 1, 12)]})
    out = scg.compare_verdicts(keeper, arm)
    assert out["verdict"] == "FAIL"
    assert [f["key"] for f in out["flips"]] == ["CT_PEAKER"]
    assert out["flips"][0]["direction"] == "away"


def test_reported_criterion_never_flips_but_is_recorded_as_a_move():
    keeper = _verdict(
        {"forced_share": [_rec("forced_share", 2024, "CT_PEAKER", "PASS")]}
    )
    arm = _verdict({"forced_share": [_rec("forced_share", 2024, "CT_PEAKER", "FAIL")]})
    out = scg.compare_verdicts(keeper, arm)
    assert out["verdict"] == "PASS"
    assert out["flips"] == []
    assert out["moves"] and out["moves"][0]["gated"] is False


def test_price_tail_is_never_compared():
    keeper = _verdict({"price_tail": [_rec("price_tail", 2024, None, "CAVEAT")]})
    arm = _verdict({"price_tail": [_rec("price_tail", 2024, None, "FAIL")]})
    out = scg.compare_verdicts(keeper, arm)
    assert out == {"flips": [], "moves": [], "unscorable": [], "verdict": "PASS"}


def test_unattested_governance_is_unscorable_not_a_flip():
    keeper = _verdict({"governance": [_rec("governance", None, None, "PASS")]})
    arm = _verdict({"governance": [_rec("governance", None, None, "UNATTESTED")]})
    out = scg.compare_verdicts(keeper, arm)
    assert out["verdict"] == "PASS"
    assert out["unscorable"][0]["note"].startswith("not scorable at a screen")


def test_magnitude_move_toward_actual_is_reported_with_same_status():
    keeper = _verdict(
        {"fuelmix": [_rec("fuelmix", 2024, "COAL_PRB", "PASS", 100, 110)]}
    )
    arm = _verdict({"fuelmix": [_rec("fuelmix", 2024, "COAL_PRB", "PASS", 105, 110)]})
    out = scg.compare_verdicts(keeper, arm)
    assert out["verdict"] == "PASS"
    (m,) = out["moves"]
    assert (
        m["direction"] == "toward" and m["keeper_gap"] == -10.0 and m["arm_gap"] == -5.0
    )


def test_years_filter_restricts_the_comparison():
    keeper = _verdict(
        {
            "fuelmix": [
                _rec("fuelmix", 2023, "X", "PASS", 1, 2),
                _rec("fuelmix", 2024, "X", "PASS", 1, 2),
            ]
        }
    )
    arm = _verdict(
        {
            "fuelmix": [
                _rec("fuelmix", 2023, "X", "FAIL", 9, 2),
                _rec("fuelmix", 2024, "X", "PASS", 1, 2),
            ]
        }
    )
    assert scg.compare_verdicts(keeper, arm, years={2024})["verdict"] == "PASS"
    assert scg.compare_verdicts(keeper, arm, years={2023})["verdict"] == "FAIL"
