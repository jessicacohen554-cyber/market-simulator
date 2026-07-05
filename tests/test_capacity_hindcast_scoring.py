"""Unit tests for the capacity-hindcast scorer (W2-P5, plan §1.4).

Covers the greedy fuel+size retirement matching on a synthetic 5-unit case
(the plan's explicit test ask) plus the addition-band and tech-mix scoring, so
the metric logic is verified without a real solve.
"""

from __future__ import annotations

import pandas as pd

from scripts import score_capacity_hindcast as S


def _actuals(rows):
    return pd.DataFrame(rows)


def test_retirement_recall_greedy_5_unit():
    """Two big coal retirements actual; model catches one → 50% recall (FAIL)."""
    actuals = _actuals(
        [
            {"kind": "retirement", "fuel": "coal", "mw": 500, "year": 2023},
            {"kind": "retirement", "fuel": "coal", "mw": 400, "year": 2024},
            {
                "kind": "retirement",
                "fuel": "gas_ct",
                "mw": 100,
                "year": 2023,
            },  # <300, not counted
            {"kind": "addition", "fuel": "solar", "mw": 1000, "year": 2023},
            {"kind": "addition", "fuel": "wind", "mw": 500, "year": 2024},
        ]
    )
    model = pd.DataFrame(
        [
            {"unit_id": "m1", "fuel": "coal", "mw": 480, "year": 2023}
        ]  # matches the 500 MW one
    )
    ret = S.score_retirements(model, actuals)
    assert ret["unit_recall_gt300"]["n_big_actual"] == 2
    assert ret["unit_recall_gt300"]["matched"] == 1
    assert ret["unit_recall_gt300"]["recall"] == 0.5
    assert ret["unit_recall_gt300"]["band"] == "FAIL"


def test_retirement_total_gw_band():
    """Model retires within 10% of actual thermal GW → PASS."""
    actuals = _actuals(
        [
            {"kind": "retirement", "fuel": "coal", "mw": 1000, "year": 2023},
        ]
    )
    model = pd.DataFrame([{"unit_id": "m1", "fuel": "coal", "mw": 1050, "year": 2023}])
    ret = S.score_retirements(model, actuals)
    assert ret["total_gw"]["band"] == "PASS"
    assert abs(ret["total_gw"]["err_frac"] - 0.05) < 1e-9


def test_false_retirement_flagged():
    """A model retirement with no actual counterpart is a false retire."""
    actuals = _actuals(
        [{"kind": "retirement", "fuel": "coal", "mw": 1000, "year": 2023}]
    )
    model = pd.DataFrame(
        [
            {"unit_id": "m1", "fuel": "coal", "mw": 1000, "year": 2023},  # real
            {"unit_id": "m2", "fuel": "gas_cc", "mw": 800, "year": 2024},  # phantom
        ]
    )
    ret = S.score_retirements(model, actuals)
    assert ret["false_retire"]["false_gw"] == 0.8
    # 0.8 / 1.8 model GW = 0.44 > 0.15 → FAIL
    assert ret["false_retire"]["band"] == "FAIL"


def test_addition_bands_and_shares():
    """Solar within 15%, storage within 25%; tech-mix shares within 5pp."""
    actuals = _actuals(
        [
            {"kind": "addition", "fuel": "solar", "mw": 10000, "year": 2023},
            {"kind": "addition", "fuel": "storage", "mw": 5000, "year": 2024},
        ]
    )
    model = pd.DataFrame(
        [
            {"fuel": "solar", "mw": 10500, "year": 2023},  # +5% PASS
            {"fuel": "storage", "mw": 5500, "year": 2024},  # +10% PASS
        ]
    )
    add = S.score_additions(model, actuals)
    assert add["by_tech"]["solar"]["band"] == "PASS"
    assert add["by_tech"]["storage"]["band"] == "PASS"
    # Shares: actual solar 10/15=.667, model 10.5/16=.656 → Δ ~1pp PASS
    assert add["shares"]["solar"]["band"] == "PASS"


def test_addition_band_fails_on_large_miss():
    actuals = _actuals(
        [{"kind": "addition", "fuel": "wind", "mw": 10000, "year": 2023}]
    )
    model = pd.DataFrame([{"fuel": "wind", "mw": 5000, "year": 2023}])  # -50%
    add = S.score_additions(model, actuals)
    assert add["by_tech"]["wind"]["band"] == "FAIL"
