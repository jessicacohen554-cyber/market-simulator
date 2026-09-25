"""Validation of the MISO regulated-coal within-run night floor (miso-113).

Covers :func:`market_sim.pipeline.commitment.build_miso_coal_night_floor_p1_prep`
and the per-unit ``min_load_frac_by_gen`` leg it adds to the shared ISO-neutral
detector (:func:`market_sim.model.commitment.caiso_ra_mustoffer_min_gen`) — the
successor to the two REJECTED offer-side arms, ``coal_prb_committed_dispatchable``
(miso-111) and ``coal_prb_committed_split`` (miso-112). Contract:

* flag off / non-MISO ⇒ ``None`` (byte-identical P1 — rules 14/26);
* ``min_load_frac_by_gen=None`` is byte-identical on the shared detector, so the
  CAISO / ERCOT / NYISO bridges are untouched;
* a per-unit vector floors each row at ITS OWN level, and a row whose entry is
  ``<= 0`` is skipped entirely — the population gate expressed as a level rather
  than a class-name tuple;
* the floor is written on the PLANT total (``frac × plant_pmax``) clipped to the
  tranche's own capacity, over the P0-detected ONLINE hours — never in an hour
  the model has the plant off (rule 17 [R-FLOOR-WINDOW]);
* only the ``_committed`` tranche is eligible, and that comes from unit PHYSICS
  (``_ra_bridge_unit_params``: min-down > 0, not a binned incremental tranche),
  not from a class-name tuple (rule 18 [R-PHYSICS]);
* the level is NET of the plant's own ``_mustrun`` band, so the plant total is
  ``night_p50 × capacity`` and never ``mustrun + night`` (rule 19 [R-ONE-MECH]);
* composition preserves the ``pmin < 0`` priced export sinks (caiso-138 §D) —
  MISO runs seam export sinks and a zeros-init floor would otherwise delete
  them from the scored P1;
* D-2 attribution: floored gen-hours tagged ``MECH_MISO_COAL_NIGHT_FLOOR``,
  separate from ``MECH_COAL_MUSTRUN`` and ``MECH_COAL_MIN_CONFIG``.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_MISO_COAL_NIGHT_FLOOR,
    MECH_NAMES,
    assert_ablation_coverage,
)
from market_sim.model.commitment import caiso_ra_mustoffer_min_gen
from market_sim.pipeline.commitment import (
    _bridge_floored_fleet,
    _miso_coal_night_floor,
    build_miso_coal_night_floor_p1_prep,
)

_HOURS = 72
# A coal CAMPD bin's committed tranche carries a real min-run/min-down window
# and a startup cost; the incremental tranches carry zeros. Mirrors
# data.fleet.assembly.bins_to_fleet.
_COAL_MIN_RUN = 36
_COAL_MIN_DOWN = 12


def _committed(unit_id="P1733_committed", pmax=400.0, must_run_pct=0.0):
    """An eligible coal `_committed` tranche (min-down > 0, startup > 0)."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="z",
        fuel_type="coal",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=10.0,
        eford=0.0,
        is_campd_bin=True,
        plant_group="COAL_BIT",
        min_run_hours=_COAL_MIN_RUN,
        min_down_hours=_COAL_MIN_DOWN,
        startup_cost_per_mw=60.0,
        must_run_pct=must_run_pct,
        coal_supply="prb",
        plant_code=1733,
    )


def _incremental(unit_id="P1733_econ", pmax=300.0):
    """An incremental coal tranche: no min-run window, no startup cost."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="z",
        fuel_type="coal",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=11.0,
        eford=0.0,
        is_campd_bin=True,
        plant_group="COAL_BIT",
        min_run_hours=0,
        min_down_hours=0,
        startup_cost_per_mw=0.0,
        coal_supply="prb",
        plant_code=1733,
    )


class _R0:
    """The minimal ``r0`` shape the P1 fleet prep reads."""

    def __init__(self, dispatch):
        self.dispatch = dispatch


class TestPerUnitMinLoadVector(unittest.TestCase):
    """The ``min_load_frac_by_gen`` leg on the shared ISO-neutral detector."""

    def _fleet(self):
        gens = [_committed(), _incremental()]
        return gens, generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)

    def _one_run(self):
        """One 24 h committed run; both tranches loaded, then both off."""
        disp = np.zeros((2, _HOURS))
        disp[0, 20:44] = 400.0
        disp[1, 20:44] = 150.0
        return disp

    def test_none_is_byte_identical(self):
        """No vector ⇒ the scalar path, unchanged (CAISO/ERCOT/NYISO safety)."""
        gens, fa = self._fleet()
        disp = self._one_run()
        scalar = caiso_ra_mustoffer_min_gen(
            disp, fa, gens, 0.30, fuel_types=("coal",), floor_online_hours=True
        )
        vector = caiso_ra_mustoffer_min_gen(
            disp,
            fa,
            gens,
            0.0,
            fuel_types=("coal",),
            floor_online_hours=True,
            min_load_frac_by_gen=np.array([0.30, 0.30]),
        )
        np.testing.assert_array_equal(scalar, vector)

    def test_level_is_the_plant_total_over_online_hours_only(self):
        """floor = frac × PLANT pmax, on the detected run, zero elsewhere."""
        gens, fa = self._fleet()
        disp = self._one_run()
        floor = caiso_ra_mustoffer_min_gen(
            disp,
            fa,
            gens,
            0.0,
            fuel_types=("coal",),
            floor_online_hours=True,
            min_load_frac_by_gen=np.array([0.40, 0.40]),
        )
        # plant pmax = 400 + 300 = 700; 0.40 × 700 = 280, under the committed
        # tranche's own 400 MW cap, so it is written in full.
        self.assertAlmostEqual(floor[0, 30], 280.0)
        # Rule 17: never floored in an hour the P0 pattern has the plant off.
        self.assertEqual(floor[0, 0], 0.0)
        self.assertEqual(floor[0, _HOURS - 1], 0.0)
        self.assertEqual(int((floor[0] > 0).sum()), 24)

    def test_zero_entry_scopes_a_row_out(self):
        """A non-positive per-unit entry skips the row entirely."""
        gens, fa = self._fleet()
        floor = caiso_ra_mustoffer_min_gen(
            self._one_run(),
            fa,
            gens,
            0.0,
            fuel_types=("coal",),
            floor_online_hours=True,
            min_load_frac_by_gen=np.zeros(2),
        )
        self.assertEqual(float(floor.sum()), 0.0)

    def test_incremental_tranche_is_never_floored_by_physics(self):
        """Rule 18: the econ tranche is rejected by parameter, not by name."""
        gens, fa = self._fleet()
        floor = caiso_ra_mustoffer_min_gen(
            self._one_run(),
            fa,
            gens,
            0.0,
            fuel_types=("coal",),
            floor_online_hours=True,
            min_load_frac_by_gen=np.array([0.40, 0.40]),
        )
        self.assertGreater(float(floor[0].sum()), 0.0)
        self.assertEqual(float(floor[1].sum()), 0.0)

    def test_shape_mismatch_raises(self):
        gens, fa = self._fleet()
        with self.assertRaises(ValueError):
            caiso_ra_mustoffer_min_gen(
                self._one_run(),
                fa,
                gens,
                0.0,
                fuel_types=("coal",),
                min_load_frac_by_gen=np.array([0.4]),
            )


class TestMustrunReconciliation(unittest.TestCase):
    """Rule 19: the level is NET of the plant's own `_mustrun` band."""

    def test_frac_subtracts_the_plants_own_mustrun_band(self):
        night = {1733: 0.50}
        gen = _committed(must_run_pct=30.0)
        fracs = self._fracs([gen], night, regulated={1733})
        # 0.50 measured night − 0.30 mustrun band = 0.20 written on _committed,
        # so the PLANT total floor is 0.30 + 0.20 = 0.50 = night_p50 exactly.
        self.assertAlmostEqual(float(fracs[0]), 0.20)

    def test_band_at_or_above_the_night_level_writes_nothing(self):
        """A plant whose mustrun band already covers its night level is inert."""
        gen = _committed(must_run_pct=60.0)
        fracs = self._fracs([gen], {1733: 0.50}, regulated={1733})
        self.assertEqual(float(fracs[0]), 0.0)

    def test_unregulated_or_unmeasured_plant_is_out_of_scope(self):
        gen = _committed(must_run_pct=0.0)
        self.assertEqual(
            float(self._fracs([gen], {1733: 0.5}, regulated=set())[0]), 0.0
        )
        self.assertEqual(float(self._fracs([gen], {}, regulated={1733})[0]), 0.0)

    def test_non_prb_supply_is_out_of_scope(self):
        gen = _committed()
        gen = gen.model_copy(update={"coal_supply": "lignite"})
        self.assertEqual(
            float(self._fracs([gen], {1733: 0.5}, regulated={1733})[0]), 0.0
        )

    @staticmethod
    def _fracs(fleet, night, regulated):
        """Run the level builder against injected artifact/scope stand-ins."""
        import market_sim.pipeline.commitment as pc

        from market_sim.data.fleet import campd_bins, eia860

        orig_night = campd_bins.coal_prb_committed_split_night
        orig_reg = eia860.eia860_selfcommit_scope_plants
        campd_bins.coal_prb_committed_split_night = lambda iso: dict(night)
        eia860.eia860_selfcommit_scope_plants = lambda: frozenset(regulated)
        try:
            return pc.miso_coal_night_min_load_fracs(fleet)
        finally:
            campd_bins.coal_prb_committed_split_night = orig_night
            eia860.eia860_selfcommit_scope_plants = orig_reg


class TestGating(unittest.TestCase):
    """Flag / ISO gating and the D-2 attribution contract."""

    def test_off_and_non_miso_return_none(self):
        gens = [_committed()]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        off = ScenarioConfig(iso="MISO")
        self.assertIsNone(build_miso_coal_night_floor_p1_prep(off, "MISO", gens, fa))
        on = off.with_overrides(miso_coal_night_floor=True)
        self.assertIsNone(build_miso_coal_night_floor_p1_prep(on, "NYISO", gens, fa))
        self.assertIsNotNone(build_miso_coal_night_floor_p1_prep(on, "MISO", gens, fa))

    def test_no_scoped_plant_is_inert(self):
        """An out-of-scope fleet floors nothing rather than raising."""
        gens = [_committed(must_run_pct=100.0)]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        cfg = ScenarioConfig(iso="MISO").with_overrides(miso_coal_night_floor=True)
        disp = np.zeros((1, _HOURS))
        disp[0, 10:40] = 400.0
        self.assertIsNone(_miso_coal_night_floor(cfg, gens, fa, disp))

    def test_mechanism_id_is_registered_and_ablated(self):
        self.assertEqual(
            MECH_NAMES[MECH_MISO_COAL_NIGHT_FLOOR], "miso_coal_night_floor"
        )
        assert_ablation_coverage()

    def test_composition_tags_the_mechanism_and_spares_export_sinks(self):
        """Rule 19 max-composition + the caiso-138 §D absorption exemption."""
        coal = _committed()
        sink = Generator(
            unit_id="export_sink",
            name="export_sink",
            zone="z",
            fuel_type="import",
            pmax_mw=0.0,
            pmin_mw=-500.0,
            heat_rate=0.0,
            eford=0.0,
        )
        gens = [coal, sink]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        floor = np.zeros((2, _HOURS))
        floor[0, 10:20] = 100.0
        out = _bridge_floored_fleet(
            fa, floor, MECH_MISO_COAL_NIGHT_FLOOR, preserve_absorption=True
        )
        self.assertEqual(int(out.min_gen_mechanism[0, 12]), MECH_MISO_COAL_NIGHT_FLOOR)
        self.assertAlmostEqual(float(out.min_gen[0, 12]), 100.0)
        # The sink keeps its negative lower bound and is never tagged.
        self.assertLess(float(out.min_gen[1, 12]), 0.0)
        self.assertEqual(int(out.min_gen_mechanism[1, 12]), 0)


if __name__ == "__main__":
    unittest.main()
