"""Tests for the commitment-feasibility clip of the per-plant must-run floors.

``ScenarioConfig.mustrun_commitment_feasibility_clip`` (spp-42, card R-be)
changes only WHAT the floor asserts in hours the plant cannot carry it. The
incumbent global clip derates the floor LINEARLY
(``np.minimum(min_gen, pmax * availability)``) and, because a committed
tranche's ``cc_mustrun_pmin_mw`` IS its own ``pmax``, that leaves exactly
``tranche pmax x availability`` — a fractional "commitment" that no
configuration of the plant can actually operate at. Where the plant-group's
own available capacity falls below the committed level the floor asserts, the
floor is zeroed instead of scaled; every other hour keeps the incumbent clip
(rule 19 ``[R-ONE-MECH]``), and the gate reads only arrays the LP already
holds (rules 13 ``[R-MEASURED]`` / 21 ``[R-DOF]``: zero measured inputs, zero
free parameters).
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_NUCLEAR,
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
)

ZONES = ["Dominion"]
HOURS = 240
_ST_CODE = 1403
_OUTAGE = slice(24, 72)  # the hours the test derates


def _load(hours: int = HOURS) -> np.ndarray:
    """Monotone-ish load so the top-``frac`` window is a known prefix."""
    return 30_000.0 + 100.0 * np.arange(hours, dtype=float)


def _fleet() -> list[Generator]:
    """One ST_GAS plant as two tranches: a committed anchor plus an econ block.

    The committed tranche carries the floor; the econ tranche carries the rest
    of the plant's capacity, which is what makes the plant-group able to serve
    the committed level at all.
    """
    common = dict(
        zone="Dominion",
        fuel_type="gas_st",
        plant_group="ST_GAS",
        plant_code=_ST_CODE,
        is_campd_bin=True,
        eford=0.0,
    )
    return [
        Generator(
            unit_id="ST_GAS_Dominion_p1403_committed",
            name="steamer committed",
            pmax_mw=20.0,
            cc_mustrun_pmin_mw=20.0,
            cc_mustrun_online_frac=1.0,
            **common,
        ),
        Generator(
            unit_id="ST_GAS_Dominion_p1403_econ",
            name="steamer econ",
            pmax_mw=80.0,
            **common,
        ),
    ]


def _arrays(clip: bool, outage_factor: float):
    cfg = ScenarioConfig(
        iso="SPP",
        weather_year=2024,
        mode="backcast",
        hours=HOURS,
        st_gas_mustrun_per_plant=True,
        mustrun_commitment_feasibility_clip=clip,
    )
    fa = generators_to_fleet_arrays(
        _fleet(), ZONES, hours=HOURS, iso="SPP", config=cfg, load_shape=_load()
    )
    # Derate the whole plant-group to ``outage_factor`` over _OUTAGE, the way a
    # dated CAMPD full-stop window does, then recompose the floors against it.
    from market_sim.data.fleet.arrays import _compose_min_gen_floors

    avail = np.asarray(fa.availability, dtype=float).copy()
    avail[:, _OUTAGE] = outage_factor
    min_gen, mech = _compose_min_gen_floors(
        _fleet(),
        avail,
        np.asarray(fa.pmax, dtype=float),
        np.asarray(fa.pmin, dtype=float),
        np.asarray(fa.heat_rate, dtype=float),
        HOURS,
        cfg,
        "SPP",
        2024,
        _load(),
        None,
        {},
        0.0,
        set(),
        {},
        0.0,
        set(),
        {},
        0.0,
        set(),
    )
    return np.asarray(min_gen, dtype=float), np.asarray(mech)


class TestCommitmentFeasibilityClip(unittest.TestCase):
    """The gate zeroes an infeasible commitment and touches nothing else."""

    def test_off_is_the_incumbent_linear_clip(self) -> None:
        """Default-off reproduces ``pmax x availability`` exactly."""
        min_gen, _ = _arrays(clip=False, outage_factor=0.05)
        # 5 % of the plant's 100 MW is 5 MW, well under the 20 MW committed
        # level — the incumbent leaves a 1 MW fractional floor on the 20 MW
        # committed tranche (20 x 0.05), which is the defect under test.
        self.assertAlmostEqual(min_gen[0, _OUTAGE].max(), 1.0, places=9)
        self.assertGreater(min_gen[0, _OUTAGE].min(), 0.0)

    def test_armed_zeroes_the_infeasible_hours(self) -> None:
        """Available capacity below the committed level ⇒ no floor at all."""
        min_gen, mech = _arrays(clip=True, outage_factor=0.05)
        self.assertEqual(min_gen[0, _OUTAGE].max(), 0.0)
        # The mechanism stamp goes with it (clear_where_unfloored).
        self.assertTrue((mech[0, _OUTAGE] != MECH_ST_GAS_MUSTRUN_PER_PLANT).all())

    def test_feasible_hours_are_byte_identical(self) -> None:
        """Outside the infeasible hours the armed floor is unchanged."""
        off, _ = _arrays(clip=False, outage_factor=0.05)
        on, _ = _arrays(clip=True, outage_factor=0.05)
        keep = np.ones(HOURS, dtype=bool)
        keep[_OUTAGE] = False
        np.testing.assert_array_equal(off[:, keep], on[:, keep])

    def test_partial_derate_that_still_carries_the_level_is_untouched(self) -> None:
        """A derate leaving >= the committed level keeps the incumbent clip.

        50 % of 100 MW is 50 MW, above the 20 MW committed level, so the
        commitment stays feasible and the linear clip stands — the gate is a
        feasibility test, not a blanket "any outage removes the floor".
        """
        off, _ = _arrays(clip=False, outage_factor=0.5)
        on, _ = _arrays(clip=True, outage_factor=0.5)
        np.testing.assert_array_equal(off, on)
        self.assertGreater(on[0, _OUTAGE].max(), 0.0)

    def test_no_other_mechanism_is_reachable(self) -> None:
        """Only the two per-plant commitment stamps can lose their floor.

        A nuclear flat must-run derated into the same hours keeps its floor,
        because the gate masks on the mechanism id (rule 19 ``[R-ONE-MECH]``).
        """
        cfg = ScenarioConfig(
            iso="SPP",
            weather_year=2024,
            mode="backcast",
            hours=HOURS,
            st_gas_mustrun_per_plant=True,
            mustrun_commitment_feasibility_clip=True,
        )
        fleet = [
            *_fleet(),
            Generator(
                unit_id="NUC_Dominion_p9999",
                name="nuke",
                zone="Dominion",
                fuel_type="nuclear",
                pmax_mw=1000.0,
                plant_code=9999,
                plant_group="NUCLEAR",
                eford=0.0,
            ),
        ]
        fa = generators_to_fleet_arrays(
            fleet, ZONES, hours=HOURS, iso="SPP", config=cfg, load_shape=_load()
        )
        from market_sim.data.fleet.arrays import _compose_min_gen_floors

        avail = np.asarray(fa.availability, dtype=float).copy()
        avail[:, _OUTAGE] = 0.05
        min_gen, mech = _compose_min_gen_floors(
            fleet,
            avail,
            np.asarray(fa.pmax, dtype=float),
            np.asarray(fa.pmin, dtype=float),
            np.asarray(fa.heat_rate, dtype=float),
            HOURS,
            cfg,
            "SPP",
            2024,
            _load(),
            None,
            {},
            0.0,
            set(),
            {},
            0.0,
            set(),
            {},
            0.0,
            set(),
        )
        nuc = len(fleet) - 1
        self.assertEqual(float(np.asarray(min_gen)[0, _OUTAGE].max()), 0.0)
        self.assertGreater(float(np.asarray(min_gen)[nuc, _OUTAGE].max()), 0.0)
        self.assertTrue(
            (np.asarray(mech)[nuc, _OUTAGE] == MECH_NUCLEAR).all(),
        )

    def test_gate_is_registered_at_its_declared_default(self) -> None:
        """Rule 24 ``[R-REGISTRY]`` / the nyiso-119 cache-key discipline."""
        from market_sim.config.scenarios import (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
            _CACHE_KEY_OPTIONAL_FIELDS,
        )

        self.assertIn("mustrun_commitment_feasibility_clip", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["mustrun_commitment_feasibility_clip"],
            "False",
        )
        self.assertIs(ScenarioConfig().mustrun_commitment_feasibility_clip, False)


if __name__ == "__main__":
    unittest.main()
