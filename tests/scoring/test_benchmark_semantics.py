"""Drift guard + behavior tests for ``scripts.lib.benchmark_semantics``.

The gas/coal family tuples are hard-coded in the stdlib-only shared module (the
scorer is numpy-free), so a taxonomy change that isn't mirrored there would
silently desync the renderer from the scorer. These tests assert the hard-coded
tuples still equal the live ``plant_taxonomy.classes_for_fuel930`` roll-up, and
pin the fold-in arithmetic.
"""

from __future__ import annotations

from market_sim.config.plant_taxonomy import classes_for_fuel930
from market_sim.data.fleet import OTHER_FOSSIL_CLASS

from scripts.lib import benchmark_semantics as bs


def test_gas_coal_classes_match_taxonomy():
    assert bs.GAS_CLASSES == tuple(classes_for_fuel930("gas"))
    assert bs.COAL_CLASSES == tuple(classes_for_fuel930("coal"))


def test_other_fossil_matches_fleet_constant():
    assert bs.OTHER_FOSSIL == OTHER_FOSSIL_CLASS == "OTHER_FOSSIL"


def test_groups_are_families_plus_other_fossil():
    assert bs.GAS_GROUPS == (*classes_for_fuel930("gas"), OTHER_FOSSIL_CLASS)
    assert bs.COAL_GROUPS == tuple(classes_for_fuel930("coal"))


def test_reconcile_frac_and_corruption_registries():
    assert bs.VINTAGE_RECONCILE_FRAC == 0.97
    assert bs.EIA930_NG_CELL_CORRUPT == frozenset({"CAISO"})
    # 2024 -> 2023: owner ruling 2026-07-26 (caiso-121). The pre-onset
    # "the two agree" premise fails at the level too — 2023 deflated-930 gas is
    # +10.5% over EIA-923 and +8.0% over CEMS+cogen, which themselves agree
    # within 2.3%; the contamination is a monotone ramp (+10.5/+21.1/+32.8%
    # over 923 across 2023/24/25), not a step at 2024-05.
    assert bs.EIA930_NG_CORRUPT_ONSET == {"CAISO": 2023}
    assert bs.EIA930_GAS_FOLDS_GEO_BIOMASS == frozenset({"CAISO"})


def test_gas_foldin_deflation_reextracted_regime():
    # ``other`` present -> subtract only the leaked portion, floored at 0.
    assert (
        bs.gas_foldin_deflation({"OTHER": 5.0, "biomass": 2.0}, {"other": 3.0}, "X")
        == 4.0
    )
    assert (
        bs.gas_foldin_deflation({"OTHER": 1.0, "biomass": 0.0}, {"other": 3.0}, "X")
        == 0.0
    )


def test_gas_foldin_deflation_legacy_regime():
    # No ``other`` series -> full model other+biomass for an allowlist BA, else 0.
    assert bs.gas_foldin_deflation({"OTHER": 5.0, "biomass": 2.0}, {}, "CAISO") == 7.0
    assert bs.gas_foldin_deflation({"OTHER": 5.0, "biomass": 2.0}, {}, "PJM") == 0.0


def test_gas_foldin_deflation_refuted_ba_is_zero():
    # SOCO-60: SOCO's EIA-930 gas cell is measured NOT to carry the fold (930 gas
    # <= 923 gas classes in every year 2019-2024), so the deflation is 0 in both
    # regimes; every other BA is unchanged.
    assert bs.EIA930_GAS_FOLD_REFUTED == frozenset({"SOCO"})
    cf, e930 = {"OTHER": -0.478, "biomass": 9.315}, {"other": 2.469}
    assert bs.gas_foldin_deflation(cf, e930, "SOCO") == 0.0
    assert bs.gas_foldin_deflation(cf, {}, "SOCO") == 0.0
    assert abs(bs.gas_foldin_deflation(cf, e930, "MISO") - 6.368) < 1e-9
