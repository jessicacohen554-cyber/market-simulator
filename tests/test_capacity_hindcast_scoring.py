"""Unit tests for the capacity-hindcast scorer (W2-P5, plan §1.4).

Covers the grain-corrected retirement recall / false-retire (G-31) on synthetic
cases — including the lumpy-zone and split-tranche derates the old 1:1 fuel+size
match mis-scored — plus the addition-band and tech-mix scoring, so the metric
logic is verified without a real solve.
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


def test_recall_credits_lumpy_zone_derate():
    """G-31: a single 4 GW zone-coal derate recalls both real coal units.

    The old 1:1 fuel+size match required a model row inside [0.5×,1.5×] of one
    actual unit, so a 4000 MW zone aggregate matched *nothing* (0 recall, all
    false). Grain-corrected per-fuel coverage credits both real units.
    """
    actuals = _actuals(
        [
            {"kind": "retirement", "fuel": "coal", "mw": 500, "year": 2023},
            {"kind": "retirement", "fuel": "coal", "mw": 446, "year": 2023},
        ]
    )
    model = pd.DataFrame(
        [
            {
                "unit_id": "coal_COAL_South_Central",
                "fuel": "coal",
                "mw": 4000,
                "year": 2024,
            }
        ]
    )
    ret = S.score_retirements(model, actuals)
    assert ret["unit_recall_gt300"]["matched"] == 2
    assert ret["unit_recall_gt300"]["recall"] == 1.0
    assert ret["unit_recall_gt300"]["band"] == "PASS"
    # Genuine over-retire: 4000 - 946 = 3054 MW excess coal.
    assert abs(ret["false_retire"]["false_gw"] - 3.054) < 1e-6
    # Plant identity was collapsed in the zone aggregate → no plant-exact hit.
    assert ret["unit_recall_gt300"]["plant_recall_frac"] == 0.0


def test_recall_credits_split_tranches_and_plant_exact():
    """G-31: a plant's coal split across tranche rows recalls its real unit.

    One plant (6146) exits as committed + peak CAMPD tranches; the actual is one
    486 MW unit at that plant. Per-fuel coverage recalls it, and the plant-exact
    diagnostic confirms the model retired the *same* plant.
    """
    actuals = _actuals(
        [
            {
                "kind": "retirement",
                "fuel": "coal",
                "mw": 486,
                "year": 2023,
                "plant_id": 6146,
            }
        ]
    )
    model = pd.DataFrame(
        [
            {
                "unit_id": "COAL_NE_p6146_committed",
                "fuel": "coal",
                "mw": 300,
                "year": 2022,
            },
            {"unit_id": "COAL_NE_p6146_peak", "fuel": "coal", "mw": 200, "year": 2022},
        ]
    )
    ret = S.score_retirements(model, actuals)
    assert ret["unit_recall_gt300"]["matched"] == 1  # 500 pool >= 486
    assert ret["unit_recall_gt300"]["recall"] == 1.0
    assert ret["unit_recall_gt300"]["plant_recall_frac"] == 1.0
    assert ret["unit_recall_gt300"]["plant_matched"] == 1
    # false = 500 - 486 = 14 MW excess coal.
    assert abs(ret["false_retire"]["false_gw"] - 0.014) < 1e-6


def test_false_retire_is_per_fuel_excess_only():
    """G-31: retiring the right fuel-MW nets to zero false-retire regardless of
    how the derate is shaped; only the per-fuel excess counts."""
    actuals = _actuals(
        [{"kind": "retirement", "fuel": "coal", "mw": 1000, "year": 2023}]
    )
    # Model retires exactly 1000 MW of coal, but split across three tranche rows
    # that individually match no single actual unit under the old logic.
    model = pd.DataFrame(
        [
            {"unit_id": "COAL_z_p1_mustrun", "fuel": "coal", "mw": 600, "year": 2022},
            {"unit_id": "COAL_z_p1_committed", "fuel": "coal", "mw": 250, "year": 2022},
            {"unit_id": "COAL_z_p1_peak", "fuel": "coal", "mw": 150, "year": 2022},
        ]
    )
    ret = S.score_retirements(model, actuals)
    assert ret["false_retire"]["false_gw"] == 0.0
    assert ret["false_retire"]["band"] == "PASS"


def test_model_plant_code_forms():
    """Plant-code parsing across the three model unit_id forms."""
    assert S.model_plant_code("COAL_South_p6183_committed") == "6183"
    assert S.model_plant_code("ST_GAS_North_p3490_econ") == "3490"
    assert S.model_plant_code("3490_GEN1") == "3490"
    assert S.model_plant_code("coal_COAL_South_Central") is None


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
