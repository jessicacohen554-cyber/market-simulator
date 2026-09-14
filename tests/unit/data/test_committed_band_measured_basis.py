"""pjm-h6 — the Route A REPLACE committed-band measured basis.

``ScenarioConfig.committed_band_measured_basis`` is ONE mechanism with TWO
coupled halves (rule 19 ``[R-ONE-MECH]``):

* (a) every covered class's ``committed`` multiplier is replaced by that class's
  own measured ``avg_committed_p50``
  (:func:`market_sim.data.offer_curves.apply_committed_band_measured_basis`);
* (b) the coal supply passthrough sigmoid is dropped from the ``_committed``
  band only (:func:`market_sim.data.fleet.campd_tranche_fuel_frac`), so the
  band's effective basis IS the measured multiplier in every hour.

These pin the properties the charter
(``docs/PRECOMMIT-pjm-h5-coal-committed-charter-2026-09-13.md`` §4/§7) froze
before any solve: flag-off byte identity, the IDENTITY the arm claims, the
non-selective class scope, band confinement, the zero-free-parameter operand,
and the rule-25 ``[R-ISO-SCOPE]`` posture (default off for every ISO).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import campd_tranche_fuel_frac
from market_sim.data.offer_curves import (
    _COMMITTED_MEASURED_COLUMN,
    _COMMITTED_MEASURED_ROW,
    apply_committed_band_measured_basis,
    committed_measured_basis,
)

#: The PJM keeper's own registered committed bands (pjm_d4_4_A run_config),
#: trimmed to the bands these tests read.
KEEPER = {
    "CC_REGULAR": {"committed": 1.0, "econ_low": 0.96, "econ_high": 1.5, "peak": 5.0},
    "CT_CHP": {"committed": 0.864, "econ_low": 0.864, "econ_high": 0.864},
    "COAL_BIT": {"committed": 0.548, "econ_low": 0.6556, "econ_high": 1.2664},
    "COAL_WC": {"committed": 0.512, "econ_low": 0.548, "econ_high": 0.6344},
}


class _Gen:
    """Minimal stand-in for the Generator fields the passthrough reads."""

    def __init__(self, unit_id: str, fuel_type: str = "coal", supply="bituminous"):
        self.unit_id = unit_id
        self.fuel_type = fuel_type
        self.plant_code = 3944
        self.coal_supply = supply


class TestDefaultPosture:
    def test_field_defaults_off(self):
        """Rule 25 [R-ISO-SCOPE]: off for every ISO and every lane."""
        assert ScenarioConfig().committed_band_measured_basis is False

    def test_cache_key_is_dropped_at_its_default(self):
        """Registered as cache-optional, so no existing key moves."""
        assert (
            ScenarioConfig().cache_key()
            == ScenarioConfig(committed_band_measured_basis=False).cache_key()
        )

    def test_armed_run_is_a_distinct_scenario(self):
        assert (
            ScenarioConfig(committed_band_measured_basis=True).cache_key()
            != ScenarioConfig().cache_key()
        )


class TestOperand:
    def test_operand_is_the_registered_convention(self):
        """Rule 21 [R-DOF]: the column is precedent, never chosen here."""
        assert _COMMITTED_MEASURED_COLUMN == "avg_committed_p50"

    def test_every_coal_class_reads_the_single_COAL_row(self):
        """The artifact carries ONE COAL row, so no per-supply value exists."""
        coal = {c for c in _COMMITTED_MEASURED_ROW if c.startswith("COAL")}
        assert coal == {"COAL", "COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC"}
        assert {_COMMITTED_MEASURED_ROW[c] for c in coal} == {"COAL"}

    def test_pjm_operands_reproduce_the_committed_artifact(self):
        """The values the charter §2 table was built on, byte for byte."""
        m = committed_measured_basis("PJM")
        assert m["COAL_BIT"] == pytest.approx(0.916)
        assert m["CC_REGULAR"] == pytest.approx(1.015)
        assert m["CC_CHP"] == pytest.approx(1.359)
        assert m["CT_CHP"] == pytest.approx(1.163)
        assert m["CT_PEAKER"] == pytest.approx(1.049)
        assert m["ST_GAS"] == pytest.approx(1.006)

    def test_unknown_iso_is_a_no_op(self):
        """No artifact ⇒ the registered curve is returned untouched."""
        curve, moved = apply_committed_band_measured_basis(KEEPER, "NOT_AN_ISO")
        assert curve is KEEPER
        assert moved == []


class TestHalfA:
    def test_committed_is_replaced_with_the_measured_value(self):
        curve, moved = apply_committed_band_measured_basis(KEEPER, "PJM")
        assert curve["COAL_BIT"]["committed"] == pytest.approx(0.916)
        assert curve["COAL_WC"]["committed"] == pytest.approx(0.916)
        assert curve["CC_REGULAR"]["committed"] == pytest.approx(1.015)
        assert curve["CT_CHP"]["committed"] == pytest.approx(1.163)
        assert {c for c, _, _ in moved} == set(KEEPER)

    def test_no_other_band_moves(self):
        """G-1 confinement: `committed` only, in every class."""
        curve, _ = apply_committed_band_measured_basis(KEEPER, "PJM")
        for cls, bands in KEEPER.items():
            for band, value in bands.items():
                if band == "committed":
                    continue
                assert curve[cls][band] == value

    def test_it_is_non_selective(self):
        """Rule 1 [R-STRUCT]: every covered class, never the helpful subset."""
        _, moved = apply_committed_band_measured_basis(KEEPER, "PJM")
        assert len(moved) == len(KEEPER)

    def test_the_input_curve_is_never_mutated(self):
        before = {c: dict(b) for c, b in KEEPER.items()}
        apply_committed_band_measured_basis(KEEPER, "PJM")
        assert KEEPER == before

    def test_uncovered_class_is_neutral(self):
        """Rule-24 generic fallback, not a literal."""
        curve, moved = apply_committed_band_measured_basis(
            {"NUCLEAR": {"committed": 0.42}}, "PJM"
        )
        assert curve["NUCLEAR"]["committed"] == 0.42
        assert moved == []

    def test_non_numeric_band_is_skipped(self):
        """`peak_ladder` rungs are lists; a band that is not a float is left."""
        curve, moved = apply_committed_band_measured_basis(
            {"COAL_BIT": {"committed": [1.0, 2.0]}}, "PJM"
        )
        assert curve["COAL_BIT"]["committed"] == [1.0, 2.0]
        assert moved == []


class TestHalfB:
    #: A gas-keyed bituminous sigmoid, as an (T,) array — the shape
    #: `coal_passthrough_by_supply` hands the tranche function.
    PT = {"bituminous": np.array([0.65, 1.0, 1.32, 0.9])}

    def test_coal_committed_drops_the_sigmoid(self):
        got = campd_tranche_fuel_frac(
            _Gen("COAL_p3944_committed"), self.PT, committed_measured_basis=True
        )
        assert got == 1.0

    def test_flag_off_keeps_the_sigmoid(self):
        got = campd_tranche_fuel_frac(_Gen("COAL_p3944_committed"), self.PT)
        assert np.allclose(got, self.PT["bituminous"])

    @pytest.mark.parametrize("suffix", ["econc00", "econc05", "econlo", "peak"])
    def test_econ_and_peak_bands_keep_the_sigmoid(self, suffix):
        """Rule 19: the crossover rationale is about INCREMENTAL coal."""
        got = campd_tranche_fuel_frac(
            _Gen(f"COAL_p3944_{suffix}"), self.PT, committed_measured_basis=True
        )
        assert np.allclose(got, self.PT["bituminous"])

    def test_mustrun_and_sync_are_untouched(self):
        assert (
            campd_tranche_fuel_frac(
                _Gen("COAL_p3944_mustrun"), self.PT, committed_measured_basis=True
            )
            == 0.0
        )
        assert (
            campd_tranche_fuel_frac(
                _Gen("COAL_p3944_sync"), self.PT, committed_measured_basis=True
            )
            == 1.0
        )

    def test_it_bypasses_every_committed_band_fuel_modifier(self):
        """The identity holds even with a take-or-pay discount configured."""
        got = campd_tranche_fuel_frac(
            _Gen("COAL_p3944_committed"),
            self.PT,
            takeorpay_by_plant={3944: 0.9},
            committed_takeorpay_all=True,
            committed_measured_basis=True,
        )
        assert got == 1.0

    def test_commitcyc_slice_is_not_matched(self):
        """The suffix scope is exactly `_committed`, never `_commitcyc`."""
        got = campd_tranche_fuel_frac(
            _Gen("COAL_p3944_commitcyc"), self.PT, committed_measured_basis=True
        )
        assert np.allclose(got, self.PT["bituminous"])

    def test_gas_committed_is_unaffected(self):
        """Gas already passes full fuel cost; half (b) is coal-only in effect."""
        for armed in (False, True):
            assert (
                campd_tranche_fuel_frac(
                    _Gen("CC_p1_committed", fuel_type="gas_cc"),
                    self.PT,
                    committed_measured_basis=armed,
                )
                == 1.0
            )


class TestIdentity:
    """G-2 — the arm's defining claim, at the two halves' composition."""

    def test_effective_basis_equals_the_measured_value_in_every_hour(self):
        curve, _ = apply_committed_band_measured_basis(KEEPER, "PJM")
        mult = curve["COAL_BIT"]["committed"]
        ff = campd_tranche_fuel_frac(
            _Gen("COAL_p3944_committed"),
            TestHalfB.PT,
            committed_measured_basis=True,
        )
        assert np.max(np.abs(np.asarray(mult * ff) - 0.916)) < 1e-12

    #: The bituminous sigmoid's ANNUAL MEAN passthrough on the PJM keeper's own
    #: gas series, 2020-2025 (charter §4, measured off `coal_passthrough_series`
    #: before any solve).
    KEEPER_PASSTHROUGH = (0.6744, 1.0105, 1.3150, 0.7573, 0.7530, 0.9645)

    def test_multiplier_only_lands_on_the_measurement_in_no_year(self):
        """Why (b) is not optional (charter §4, the arithmetic that settles it).

        Substituting the multiplier while the sigmoid still scales the same
        block gives an effective basis of ``0.916 x passthrough``. On the
        keeper's own six years that is 0.618 .. 1.205 -- it misses 0.916 in
        EVERY year, and it misses in BOTH directions, so no single correction
        could rescue it. That is the stacking rule 19 [R-ONE-MECH] forbids.
        """
        stacked = np.array(self.KEEPER_PASSTHROUGH) * 0.916
        assert np.min(np.abs(stacked - 0.916)) > 0.008
        assert stacked.min() < 0.62 < 0.916 < 1.20 < stacked.max()
