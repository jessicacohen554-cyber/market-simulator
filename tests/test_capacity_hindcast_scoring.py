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


# --------------------------------------------------------------------------- #
# IS-2020 information-set scoring (RC-0B §c.5, T-R8) — hand-built 3-unit cases
# --------------------------------------------------------------------------- #
def test_channel_of_maps_legacy_known_to_announced():
    """§c.5-4: legacy ``known`` → announced; new vocabulary passes through."""
    assert S.channel_of("known") == "announced"
    assert S.channel_of("confirmed") == "confirmed"
    assert S.channel_of("announced") == "announced"
    assert S.channel_of("economic") == "economic"
    assert S.channel_of(None) == "economic"


def test_model_plant_gen_raw_and_tranche_forms():
    """Reversal membership needs raw ``<plant>_<gen>``; tranche forms are None."""
    assert S.model_plant_gen("6023_1") == ("6023", "1")
    assert S.model_plant_gen("869_2") == ("869", "2")
    assert S.model_plant_gen("COAL_NE_p6146_committed") is None
    assert S.model_plant_gen("coal_COAL_South_Central") is None


def test_load_reversal_set_pjm_byron_dresden_only():
    """§c.5-1 membership from the real registry: the four Byron/Dresden units
    qualify (instrument ≤ V, superseded post-V); Eddystone (no
    superseding_instrument_date) and non-superseded rows do not."""
    rev = S.load_reversal_set("PJM")
    assert set(rev) == {("6023", "1"), ("6023", "2"), ("869", "2"), ("869", "3")}
    assert ("3161", "3") not in rev  # Eddystone: superseded, but no post-V date
    assert ("6166", "1") not in rev  # Rockport: not superseded
    # Other ISOs carry no post-V reversal row.
    assert S.load_reversal_set("NYISO") == {}
    assert S.load_reversal_set("MISO") == {}


def test_reversal_exclusion_is2020_false_retire(monkeypatch):
    """§c.5-1: a reversed nuclear retirement is excluded from IS-2020 false-retire
    and reported as reversal_exposure_gw; raw keeps it (unit runs today)."""
    reversal_set = {
        ("6023", "1"): {
            "instrument": "IL CEJA",
            "unit_name": "Byron 1",
            "capacity_mw": 1224.9,
        }
    }
    model = pd.DataFrame(
        [
            {
                "unit_id": "6023_1",
                "fuel": "nuclear",
                "mw": 1200,
                "year": 2022,
                "reason": "known",
            },
            {
                "unit_id": "9999_1",
                "fuel": "coal",
                "mw": 500,
                "year": 2023,
                "reason": "economic",
            },
        ]
    )
    actuals = _actuals(
        [
            {
                "kind": "retirement",
                "fuel": "coal",
                "mw": 500,
                "year": 2023,
                "plant_id": 9999,
            }
        ]
    )
    raw = S.score_retirements(model, actuals)
    ret_is = S.score_retirements_is2020(model, actuals, reversal_set)
    # Raw: the 1.2 GW nuclear has no actual → false-retire.
    assert abs(raw["false_retire"]["false_gw"] - 1.2) < 1e-6
    # IS-2020: excluded → false-retire drops to 0, reported as exposure.
    assert ret_is["false_retire"]["false_gw"] == 0.0
    assert abs(ret_is["reversal_exposure_gw"] - 1.2) < 1e-6
    assert ret_is["reversal_rows"][0]["unit_name"] == "Byron 1"


def test_restart_addition_excluded_is2020(monkeypatch):
    """§c.5-2 Palisades convention: a restart addition (a nuclear addition at a
    plant the actuals also record retiring in-window) is excluded from IS-2020
    additions; the physical exit stays."""
    actuals = _actuals(
        [
            {
                "kind": "retirement",
                "fuel": "nuclear",
                "mw": 800,
                "year": 2022,
                "plant_id": 1715,
            },
            {
                "kind": "addition",
                "fuel": "nuclear",
                "mw": 800,
                "year": 2025,
                "plant_id": 1715,
            },
        ]
    )
    model_add = pd.DataFrame([], columns=["fuel", "mw", "year"])
    add_is = S.additions_is2020(model_add, actuals)
    assert abs(add_is["restart_excluded_gw"] - 0.8) < 1e-6
    assert add_is["restart_rows"][0]["plant_id"] == "1715"


def test_coverage_fix_recall_both_modes():
    """§c.5-3 (Indian Point): once the nuclear unit is in the actuals, a model
    nuclear retirement ≥ its MW is a correct recall (raw == IS, no reversal)."""
    actuals = _actuals(
        [
            {
                "kind": "retirement",
                "fuel": "nuclear",
                "mw": 1000,
                "year": 2021,
                "plant_id": 8907,
            }
        ]
    )
    model = pd.DataFrame(
        [
            {
                "unit_id": "8907_3",
                "fuel": "nuclear",
                "mw": 1030,
                "year": 2022,
                "reason": "known",
            }
        ]
    )
    raw = S.score_retirements(model, actuals)
    ret_is = S.score_retirements_is2020(model, actuals, reversal_set={})
    assert raw["unit_recall_gt300"]["recall"] == 1.0
    assert raw["unit_recall_gt300"]["plant_recall_frac"] == 1.0
    assert ret_is["reversal_exposure_gw"] == 0.0
    assert ret_is["unit_recall_gt300"]["recall"] == 1.0


def test_per_channel_separates_announced_from_economic():
    """§c.5-4: per-channel table keeps an announced nuclear false-retire off the
    economic screen's grade (and vice-versa). Legacy ``known`` → announced."""
    model = pd.DataFrame(
        [
            {
                "unit_id": "6023_1",
                "fuel": "nuclear",
                "mw": 1000,
                "year": 2022,
                "reason": "known",
            },
            {
                "unit_id": "COAL_z_p1_econ",
                "fuel": "coal",
                "mw": 4000,
                "year": 2023,
                "reason": "economic",
            },
        ]
    )
    actuals = _actuals(
        [{"kind": "retirement", "fuel": "coal", "mw": 500, "year": 2023, "plant_id": 1}]
    )
    ch = S.score_channels(model, actuals)
    # announced owns the phantom nuclear; economic owns the coal over-retire.
    assert abs(ch["announced"]["false_retire_gw"] - 1.0) < 1e-6
    assert ch["announced"]["recall_matched"] == 0
    assert abs(ch["economic"]["false_retire_gw"] - 3.5) < 1e-6  # 4000-500
    assert ch["economic"]["recall_matched"] == 1  # coal pool covers the 500 unit
    assert ch["_n_big_actual"] == 1
    assert ch["_legacy_known_mapped_to"] == "announced"


# --------------------------------------------------------------------------- #
# Flip-gate extras (FF-1A): T-R10, LOYO folds, BLK-10 — trivial cases first.
# --------------------------------------------------------------------------- #
def test_tr10_trivial_pass():
    """1 coal econ exit against real coal retirements → both gates PASS."""
    model = pd.DataFrame(
        [
            {
                "unit_id": "m1",
                "fuel": "coal",
                "mw": 500,
                "year": 2023,
                "reason": "economic",
            }
        ]
    )
    actuals = _actuals([{"kind": "retirement", "fuel": "coal", "mw": 600, "year": 2023}])
    tr = S.score_tr10(model, actuals)
    assert tr["tr10a"] == "PASS"
    assert tr["tr10b"] == "PASS"
    assert tr["first_mover_fuels"] == ["coal"]
    assert tr["first_mover_year"] == 2023


def test_tr10_vacuous_pass_no_econ_exits():
    """No economic thermal exits → vacuous PASS (no wave, no inversion)."""
    model = pd.DataFrame(
        [
            {
                "unit_id": "6023_1",
                "fuel": "nuclear",
                "mw": 1000,
                "year": 2022,
                "reason": "announced",
            }
        ]
    )
    actuals = _actuals([{"kind": "retirement", "fuel": "coal", "mw": 600, "year": 2023}])
    tr = S.score_tr10(model, actuals)
    assert tr["tr10a"] == "PASS" and tr["tr10b"] == "PASS"
    assert tr["first_mover_fuels"] == []


def test_tr10a_fails_zero_real_first_mover():
    """MISO D1=3 signature: gas_st (A=0) first economic mover, >1 GW → both FAIL."""
    model = pd.DataFrame(
        [
            {
                "unit_id": "m1",
                "fuel": "gas_st",
                "mw": 8643,
                "year": 2023,
                "reason": "economic",
            },
            {
                "unit_id": "m2",
                "fuel": "coal",
                "mw": 2000,
                "year": 2024,
                "reason": "economic",
            },
        ]
    )
    actuals = _actuals(
        [{"kind": "retirement", "fuel": "coal", "mw": 10000, "year": 2024}]
    )
    tr = S.score_tr10(model, actuals)
    assert tr["tr10a"] == "FAIL"  # first mover gas_st has A=0
    assert tr["tr10b"] == "FAIL"  # zero-real gas_st accumulates 8.643 GW
    assert tr["zero_real_fuels_over_1gw"] == ["gas_st"]


def test_tr10b_tolerates_sub_1gw_zero_real():
    """A zero-real fuel below the pre-registered 1 GW bar does not trip b."""
    model = pd.DataFrame(
        [
            {
                "unit_id": "m1",
                "fuel": "coal",
                "mw": 5000,
                "year": 2023,
                "reason": "economic",
            },
            {
                "unit_id": "m2",
                "fuel": "oil",
                "mw": 900,
                "year": 2024,
                "reason": "economic",
            },
        ]
    )
    actuals = _actuals(
        [{"kind": "retirement", "fuel": "coal", "mw": 5000, "year": 2023}]
    )
    tr = S.score_tr10(model, actuals)
    assert tr["tr10a"] == "PASS"
    assert tr["tr10b"] == "PASS"  # oil 0.9 GW <= 1.0 GW bar


def test_tr10_announced_channel_never_trips_guard():
    """PJM Byron/Dresden class: announced nuclear (A=0) is not an economic
    exit — the guard sees only the economic channel."""
    model = pd.DataFrame(
        [
            {
                "unit_id": "6023_1",
                "fuel": "nuclear",
                "mw": 4097,
                "year": 2021,
                "reason": "announced",
            },
            {
                "unit_id": "m2",
                "fuel": "coal",
                "mw": 3000,
                "year": 2023,
                "reason": "economic",
            },
        ]
    )
    actuals = _actuals(
        [{"kind": "retirement", "fuel": "coal", "mw": 6885, "year": 2023}]
    )
    tr = S.score_tr10(model, actuals)
    assert tr["first_mover_fuels"] == ["coal"]
    assert tr["tr10a"] == "PASS" and tr["tr10b"] == "PASS"


def test_blk10_trivial_none_fired():
    """Ledger with only economic additions → 0 fired MW."""
    ledgers = {
        2025: {
            "thermal_additions": [
                {
                    "unit_id": "gas_cc_new_2025_0",
                    "fuel": "gas_cc",
                    "mw": 3000.0,
                    "source": "economic",
                },
            ]
        }
    }
    b = S.blk10_backstop_fired(ledgers)
    assert b["fired_mw_total"] == 0.0
    assert b["fired_rows"] == []
    assert b["thermal_additions_mw_by_source"] == {"economic": 3000.0}


def test_blk10_counts_reserve_backstop_rows():
    """One gas_ct_adequacy row → its MW is the fired total, split by source."""
    ledgers = {
        2024: {
            "thermal_additions": [
                {
                    "unit_id": "gas_ct_adequacy_2024",
                    "fuel": "gas_ct",
                    "mw": 6430.0,
                    "source": "reserve_backstop",
                },
            ]
        },
        2025: {
            "thermal_additions": [
                {
                    "unit_id": "gas_ct_new_2025_0",
                    "fuel": "gas_ct",
                    "mw": 353.0,
                    "source": "economic",
                },
            ]
        },
    }
    b = S.blk10_backstop_fired(ledgers)
    assert b["fired_mw_total"] == 6430.0
    assert b["fired_gw_total"] == 6.43
    assert b["fired_rows"][0]["year"] == 2024
    assert b["thermal_additions_mw_by_source"] == {
        "economic": 353.0,
        "reserve_backstop": 6430.0,
    }


def test_loyo_folds_trivial_all_hold():
    """Recall/T-R10 verdicts identical in every fold → all hold >=2/3."""
    model = pd.DataFrame(
        [
            {
                "unit_id": f"m{y}",
                "fuel": "coal",
                "mw": 500,
                "year": y,
                "reason": "economic",
            }
            for y in (2023, 2024, 2025)
        ]
    )
    actuals = _actuals(
        [
            {"kind": "retirement", "fuel": "coal", "mw": 500, "year": y}
            for y in (2023, 2024, 2025)
        ]
    )
    lo = S.loyo_folds(model, actuals, reversal_set={})
    assert set(lo["folds"]) == {"2023", "2024", "2025"}
    for f in lo["folds"].values():
        assert f["recall_band"] == "PASS"
        assert f["tr10a"] == "PASS" and f["tr10b"] == "PASS"
    assert lo["holds_2of3"] == {
        "recall_pass": True,
        "tr10a_pass": True,
        "tr10b_pass": True,
    }


def test_loyo_fold_drops_year_from_both_sides():
    """A verdict carried by a single year flips only in that year's fold: the
    2023-only zero-real gas_st exit trips T-R10 in the 2024/2025 folds but not
    in the 2023 fold (its rows held out) → tr10 holds only 2/3... exactly the
    boundary the >=2/3 bar is registered on."""
    model = pd.DataFrame(
        [
            {
                "unit_id": "m1",
                "fuel": "gas_st",
                "mw": 2000,
                "year": 2023,
                "reason": "economic",
            },
            {
                "unit_id": "m2",
                "fuel": "coal",
                "mw": 500,
                "year": 2024,
                "reason": "economic",
            },
            {
                "unit_id": "m3",
                "fuel": "coal",
                "mw": 500,
                "year": 2025,
                "reason": "economic",
            },
        ]
    )
    actuals = _actuals(
        [
            {"kind": "retirement", "fuel": "coal", "mw": 500, "year": 2024},
            {"kind": "retirement", "fuel": "coal", "mw": 500, "year": 2025},
        ]
    )
    lo = S.loyo_folds(model, actuals, reversal_set={})
    assert lo["folds"]["2023"]["tr10a"] == "PASS"  # gas_st held out
    assert lo["folds"]["2024"]["tr10a"] == "FAIL"
    assert lo["folds"]["2025"]["tr10a"] == "FAIL"
    assert lo["holds_2of3"]["tr10a_pass"] is False  # 1/3 < 2/3
