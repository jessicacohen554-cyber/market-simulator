"""Tests for the unified reserve co-optimization config (reserve_config.py).

Validates per-ISO reserve design shapes, values, and dispatch-kwargs
consistency for all 6 ISOs. Each test uses a trivial fleet (2 gens, 24 hours)
to verify structure; full LP integration is in test_reserve_coopt.py.
"""

import unittest

import numpy as np

from market_sim.config.reserve_config import (
    ReserveDesign,
    ReserveFamily,
    build_reserve_dispatch_kwargs,
    get_reserve_design,
)
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays


def _fleet(n_zones=1, T=24):
    """Minimal 2-gen fleet: one gas_cc (reserve-eligible), one wind (not)."""
    cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
    wind_idx = FUEL_TYPE_NAMES.index("wind")
    n = 2
    return FleetArrays(
        pmax=np.array([1000.0, 500.0]),
        pmin=np.array([200.0, 0.0]),
        heat_rate=np.array([7.0, 0.0]),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.array([0, min(n_zones - 1, 0)]),
        fuel_type_idx=np.array([cc_idx, wind_idx]),
        availability=np.ones((n, T)),
        unit_ids=["cc0", "wind0"],
        efficiency_bin=np.zeros(n),
        plant_code=np.array([100, 200]),
    )


def _cfg(**kw):
    """Minimal config namespace."""
    from types import SimpleNamespace

    defaults = dict(
        iso="ERCOT",
        weather_year=2024,
        ordc_voll=5000.0,
        ordc_mcl_mw=3000.0,
        ordc_lolp_mu_mw=0.0,
        ordc_lolp_sigma_mw=1400.0,
        ordc_lolp_shift_sigma=0.5,
        ordc_multistep_floor=False,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


class TestReserveFamily(unittest.TestCase):
    """Basic dataclass construction."""

    def test_defaults(self):
        fam = ReserveFamily(
            name="test",
            requirement=np.zeros(24),
            zone_mask=np.ones(2, dtype=bool),
            ordc_penalties=np.array([100.0]),
            ordc_step_widths=np.array([500.0]),
        )
        self.assertEqual(fam.reserve_class, 0)


class TestBuildReserveDispatchKwargs(unittest.TestCase):
    """The kwargs builder correctly converts designs to dispatch dicts."""

    def test_single_family_squeezes(self):
        T, n_gen, n_zones = 24, 3, 2
        fam = ReserveFamily(
            name="test",
            requirement=np.ones(T) * 500.0,
            zone_mask=np.ones(n_zones, dtype=bool),
            ordc_penalties=np.array([100.0, 500.0]),
            ordc_step_widths=np.array([200.0, 300.0]),
        )
        design = ReserveDesign(
            families=[fam],
            eligible=np.array([[True, True, False]]),
            storage_eligible=True,
        )
        kw = build_reserve_dispatch_kwargs(design)
        self.assertEqual(kw["reserve_requirement"].shape, (T,))
        self.assertEqual(kw["reserve_eligible"].shape, (n_gen,))
        self.assertTrue(kw["reserve_storage"])
        self.assertNotIn("reserve_balance_zone_mask", kw)

    def test_multi_family_keeps_shape(self):
        T, n_gen, n_zones = 24, 2, 3
        fams = [
            ReserveFamily(
                name=f"f{i}",
                requirement=np.ones(T) * (i + 1) * 100,
                zone_mask=np.ones(n_zones, dtype=bool),
                ordc_penalties=np.array([50.0 * (i + 1)]),
                ordc_step_widths=np.array([100.0]),
                reserve_class=i,
            )
            for i in range(3)
        ]
        design = ReserveDesign(
            families=fams,
            eligible=np.ones((2, n_gen), dtype=bool),
        )
        kw = build_reserve_dispatch_kwargs(design)
        self.assertEqual(kw["reserve_requirement"].shape, (3, T))
        self.assertEqual(kw["reserve_balance_zone_mask"].shape, (3, n_zones))
        np.testing.assert_array_equal(kw["reserve_balance_class"], [0, 1, 2])
        np.testing.assert_array_equal(kw["reserve_balance_ordc_counts"], [1, 1, 1])

    def test_headroom_fields_propagated(self):
        T, n_gen, n_zones = 24, 2, 1
        fam = ReserveFamily(
            name="test",
            requirement=np.ones(T) * 500,
            zone_mask=np.ones(n_zones, dtype=bool),
            ordc_penalties=np.array([100.0]),
            ordc_step_widths=np.array([500.0]),
        )
        hr_elig = np.ones((2, n_gen), dtype=bool)
        hr_prod = np.ones((2, 1), dtype=bool)
        design = ReserveDesign(
            families=[fam],
            eligible=np.ones((1, n_gen), dtype=bool),
            headroom_eligible=hr_elig,
            headroom_products=hr_prod,
        )
        kw = build_reserve_dispatch_kwargs(design)
        self.assertIn("reserve_headroom_eligible", kw)
        self.assertIn("reserve_headroom_products", kw)
        self.assertIn("reserve_balance_zone_mask", kw)

    def test_online_gated_fields(self):
        T, n_gen, n_zones = 24, 2, 1
        fam = ReserveFamily(
            name="test",
            requirement=np.ones(T) * 500,
            zone_mask=np.ones(n_zones, dtype=bool),
            ordc_penalties=np.array([100.0]),
            ordc_step_widths=np.array([500.0]),
        )
        design = ReserveDesign(
            families=[fam],
            eligible=np.ones((1, n_gen), dtype=bool),
            online_gated=np.array([True]),
            online_rho=2.5,
        )
        kw = build_reserve_dispatch_kwargs(design)
        np.testing.assert_array_equal(kw["reserve_online_gated"], [True])
        self.assertEqual(kw["reserve_online_rho"], 2.5)

    def test_supply_cap_propagated(self):
        T, n_gen, n_zones = 24, 2, 1
        fam = ReserveFamily(
            name="test",
            requirement=np.ones(T) * 500,
            zone_mask=np.ones(n_zones, dtype=bool),
            ordc_penalties=np.array([100.0]),
            ordc_step_widths=np.array([500.0]),
        )
        cap = np.ones((1, T)) * 800.0
        design = ReserveDesign(
            families=[fam],
            eligible=np.ones((1, n_gen), dtype=bool),
            supply_cap=cap,
        )
        kw = build_reserve_dispatch_kwargs(design)
        np.testing.assert_array_equal(kw["reserve_supply_cap"], cap)


class TestErcotSingleProduct(unittest.TestCase):
    """ERCOT single-product ORDC design."""

    def test_shapes(self):
        fleet = _fleet()
        design = get_reserve_design(_cfg(), fleet, 24, ["ERCOT"])
        self.assertEqual(len(design.families), 1)
        self.assertEqual(design.families[0].requirement.shape, (24,))
        self.assertTrue(design.storage_eligible)
        self.assertEqual(design.eligible.shape, (1, 2))
        np.testing.assert_array_equal(design.eligible[0], [True, False])

    def test_requirement_positive(self):
        fleet = _fleet()
        design = get_reserve_design(_cfg(), fleet, 24, ["ERCOT"])
        self.assertTrue((design.families[0].requirement > 0).all())

    def test_penalties_ascend(self):
        fleet = _fleet()
        design = get_reserve_design(_cfg(), fleet, 24, ["ERCOT"])
        pens = design.families[0].ordc_penalties
        self.assertTrue(np.all(np.diff(pens) >= -1e-9))


class TestErcotMultiProduct(unittest.TestCase):
    """ERCOT multi-product AS co-optimization design."""

    def test_four_families(self):
        fleet = _fleet()
        cfg = _cfg(ercot_multiproduct_as_coopt=True)
        design = get_reserve_design(
            cfg,
            fleet,
            24,
            ["ERCOT"],
            system_load=np.ones(24) * 50000,
            wind_gen=np.ones(24) * 10000,
            solar_gen=np.ones(24) * 5000,
        )
        self.assertEqual(len(design.families), 4)
        for fam in design.families:
            self.assertEqual(fam.requirement.shape, (24,))

    def test_headroom_rows_present(self):
        fleet = _fleet()
        cfg = _cfg(ercot_multiproduct_as_coopt=True)
        design = get_reserve_design(
            cfg,
            fleet,
            24,
            ["ERCOT"],
            system_load=np.ones(24) * 50000,
            wind_gen=np.ones(24) * 10000,
            solar_gen=np.ones(24) * 5000,
        )
        self.assertIsNotNone(design.headroom_eligible)
        self.assertIsNotNone(design.headroom_products)
        self.assertEqual(design.headroom_eligible.shape[0], 2)

    def test_kwargs_multi_family(self):
        fleet = _fleet()
        cfg = _cfg(ercot_multiproduct_as_coopt=True)
        design = get_reserve_design(
            cfg,
            fleet,
            24,
            ["ERCOT"],
            system_load=np.ones(24) * 50000,
            wind_gen=np.ones(24) * 10000,
            solar_gen=np.ones(24) * 5000,
        )
        kw = build_reserve_dispatch_kwargs(design)
        self.assertEqual(kw["reserve_requirement"].shape, (4, 24))
        self.assertIn("reserve_balance_zone_mask", kw)
        self.assertIn("reserve_headroom_eligible", kw)


class TestPjmDesign(unittest.TestCase):
    """PJM reserve design shapes and values."""

    def test_shapes(self):
        fleet = _fleet()
        cfg = _cfg(iso="PJM")
        design = get_reserve_design(cfg, fleet, 24, ["PJM_RTO"])
        self.assertEqual(len(design.families), 1)
        self.assertEqual(design.families[0].name, "pjm_primary")
        self.assertEqual(design.families[0].requirement.shape, (24,))
        self.assertFalse(design.storage_eligible)
        np.testing.assert_array_equal(design.eligible[0], [True, False])

    def test_requirement_positive(self):
        fleet = _fleet()
        cfg = _cfg(iso="PJM")
        design = get_reserve_design(cfg, fleet, 24, ["PJM_RTO"])
        self.assertTrue((design.families[0].requirement > 0).all())

    def test_online_gating(self):
        fleet = _fleet()
        cfg = _cfg(iso="PJM", pjm_reserve_online_gated=True, pjm_reserve_online_rho=2.0)
        design = get_reserve_design(cfg, fleet, 24, ["PJM_RTO"])
        np.testing.assert_array_equal(design.online_gated, [True])
        self.assertEqual(design.online_rho, 2.0)

    def test_kwargs_single_family(self):
        fleet = _fleet()
        cfg = _cfg(iso="PJM")
        design = get_reserve_design(cfg, fleet, 24, ["PJM_RTO"])
        kw = build_reserve_dispatch_kwargs(design)
        self.assertEqual(kw["reserve_requirement"].shape, (24,))
        self.assertEqual(kw["reserve_eligible"].shape, (2,))


class TestMisoDesign(unittest.TestCase):
    """MISO reserve design shapes and values."""

    def test_shapes(self):
        fleet = _fleet()
        cfg = _cfg(iso="MISO")
        design = get_reserve_design(cfg, fleet, 24, ["MISO_Central"])
        self.assertEqual(len(design.families), 1)
        self.assertEqual(design.families[0].name, "miso_rbdc")
        self.assertFalse(design.storage_eligible)

    def test_requirement_includes_regulation(self):
        from market_sim.config.reserve_config import MISO_REGULATING_RESERVE_MW

        fleet = _fleet()
        cfg = _cfg(iso="MISO")
        design = get_reserve_design(cfg, fleet, 24, ["MISO_Central"])
        req = design.families[0].requirement
        self.assertTrue(np.allclose(req, 1000.0 + MISO_REGULATING_RESERVE_MW))


class TestMisoZonalDesign(unittest.TestCase):
    """MISO locational (zonal) reserve families (miso_zonal_reserves)."""

    _ZONES = ["MISO-West", "MISO-South"]

    def _south_fleet(self, T=24):
        """2-zone fleet: 1,000 MW CC in West (zone 0), 800 MW CC in South."""
        from market_sim.data.fleet import FUEL_TYPE_NAMES

        cc = FUEL_TYPE_NAMES.index("gas_cc")
        return FleetArrays(
            pmax=np.array([1000.0, 800.0]),
            pmin=np.array([200.0, 150.0]),
            heat_rate=np.array([7.0, 7.5]),
            vom=np.zeros(2),
            emission_rate=np.zeros(2),
            nox_rate=np.zeros(2),
            so2_rate=np.zeros(2),
            zone_idx=np.array([0, 1]),
            fuel_type_idx=np.array([cc, cc]),
            availability=np.ones((2, T)),
            unit_ids=["cc_west", "cc_south"],
            efficiency_bin=np.zeros(2),
            plant_code=np.array([100, 300]),
        )

    def test_default_off_single_family(self):
        cfg = _cfg(iso="MISO")
        design = get_reserve_design(cfg, self._south_fleet(), 24, self._ZONES)
        self.assertEqual(len(design.families), 1)

    def test_south_family_added(self):
        cfg = _cfg(iso="MISO", miso_zonal_reserves=True)
        design = get_reserve_design(cfg, self._south_fleet(), 24, self._ZONES)
        self.assertEqual(len(design.families), 2)
        fam = design.families[1]
        self.assertEqual(fam.name, "miso_zonal_or_miso_south")
        np.testing.assert_array_equal(fam.zone_mask, [False, True])
        # Requirement = within-zone MSSC = the 800 MW South CC.
        self.assertTrue(np.allclose(fam.requirement, 800.0))

    def test_zonal_curve_is_published_steps(self):
        from market_sim.config.reserve_config import MISO_ZONAL_ORDC_STEPS

        cfg = _cfg(iso="MISO", miso_zonal_reserves=True)
        design = get_reserve_design(cfg, self._south_fleet(), 24, self._ZONES)
        fam = design.families[1]
        np.testing.assert_allclose(
            fam.ordc_penalties, [p for _, p in MISO_ZONAL_ORDC_STEPS]
        )
        np.testing.assert_allclose(
            fam.ordc_step_widths,
            [frac * 800.0 for frac, _ in MISO_ZONAL_ORDC_STEPS],
        )
        # Step widths span the full requirement (balance row stays feasible
        # at zero cleared zonal reserve).
        self.assertAlmostEqual(float(fam.ordc_step_widths.sum()), 800.0)

    def test_zone_override(self):
        cfg = _cfg(
            iso="MISO",
            miso_zonal_reserves=True,
            miso_zonal_reserve_zones=("MISO-West",),
        )
        design = get_reserve_design(cfg, self._south_fleet(), 24, self._ZONES)
        fam = design.families[1]
        self.assertEqual(fam.name, "miso_zonal_or_miso_west")
        self.assertTrue(np.allclose(fam.requirement, 1000.0))

    def test_unknown_zone_raises(self):
        cfg = _cfg(
            iso="MISO",
            miso_zonal_reserves=True,
            miso_zonal_reserve_zones=("MISO-Narnia",),
        )
        with self.assertRaises(ValueError):
            get_reserve_design(cfg, self._south_fleet(), 24, self._ZONES)

    def test_multi_family_kwargs(self):
        cfg = _cfg(iso="MISO", miso_zonal_reserves=True)
        design = get_reserve_design(cfg, self._south_fleet(), 24, self._ZONES)
        kw = build_reserve_dispatch_kwargs(design)
        self.assertEqual(kw["reserve_requirement"].shape, (2, 24))
        np.testing.assert_array_equal(
            kw["reserve_balance_zone_mask"], [[True, True], [False, True]]
        )
        np.testing.assert_array_equal(kw["reserve_balance_class"], [0, 0])


class TestNyisoDesign(unittest.TestCase):
    """NYISO locational reserve design."""

    _ZONES = ["Upstate", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]

    def test_seven_families(self):
        fleet = _fleet(n_zones=5)
        cfg = _cfg(iso="NYISO")
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        self.assertEqual(len(design.families), 7)

    def test_two_eligibility_classes(self):
        fleet = _fleet(n_zones=5)
        cfg = _cfg(iso="NYISO")
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        self.assertEqual(design.eligible.shape[0], 2)

    def test_synchronised_adds_online_gated(self):
        fleet = _fleet(n_zones=5)
        cfg = _cfg(iso="NYISO", nyiso_synchronised_reserve=True)
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        self.assertEqual(len(design.families), 8)
        self.assertIsNotNone(design.online_gated)
        self.assertEqual(design.eligible.shape[0], 3)


class TestNeisoDesign(unittest.TestCase):
    """NEISO system-wide reserve design."""

    _ZONES = ["CT", "ME", "NH_VT", "SEMA_RI"]

    def test_three_families(self):
        fleet = _fleet(n_zones=4)
        cfg = _cfg(iso="NEISO")
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        self.assertEqual(len(design.families), 3)
        self.assertTrue(design.storage_eligible)

    def test_two_eligibility_classes(self):
        fleet = _fleet(n_zones=4)
        cfg = _cfg(iso="NEISO")
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        self.assertEqual(design.eligible.shape[0], 2)

    def test_kwargs_multi_family(self):
        fleet = _fleet(n_zones=4)
        cfg = _cfg(iso="NEISO")
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        kw = build_reserve_dispatch_kwargs(design)
        self.assertEqual(kw["reserve_requirement"].shape, (3, 24))
        self.assertIn("reserve_balance_zone_mask", kw)
        self.assertIn("reserve_balance_ordc_counts", kw)


class TestCaisoRejected(unittest.TestCase):
    """CAISO has no reserve co-opt — get_reserve_design should raise."""

    def test_raises(self):
        fleet = _fleet()
        cfg = _cfg(iso="CAISO")
        with self.assertRaises(ValueError):
            get_reserve_design(cfg, fleet, 24, ["CAISO_SP15"])


class TestDispatcherRouting(unittest.TestCase):
    """get_reserve_design routes to the correct ISO helper."""

    def test_all_supported_isos(self):
        zones = {
            "ERCOT": ["ERCOT"],
            "PJM": ["PJM_RTO"],
            "MISO": ["MISO_Central"],
            "NYISO": [
                "Upstate",
                "Capital_Hudson",
                "Lower_Hudson",
                "NYC",
                "Long_Island",
            ],
            "NEISO": ["CT", "ME", "NH_VT", "SEMA_RI"],
        }
        for iso, zone_names in zones.items():
            n_zones = len(zone_names)
            fleet = _fleet(n_zones=n_zones)
            cfg = _cfg(iso=iso)
            design = get_reserve_design(cfg, fleet, 24, zone_names)
            self.assertIsInstance(design, ReserveDesign)
            self.assertTrue(len(design.families) > 0)
            kw = build_reserve_dispatch_kwargs(design)
            self.assertIn("reserve_requirement", kw)
            self.assertIn("reserve_eligible", kw)
            self.assertIn("ordc_penalties", kw)
            self.assertIn("ordc_step_widths", kw)


if __name__ == "__main__":
    unittest.main()
