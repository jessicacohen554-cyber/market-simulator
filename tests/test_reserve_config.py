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


class TestMisoPergenDesign(unittest.TestCase):
    """MISO per-asset reserve columns (miso_reserve_pergen): (zone, fuel-class)
    pooled R columns bounded by the summed 10-min deliverable ramp."""

    _ZONES = ["MISO-West", "MISO-South"]

    def _fleet(self, T=24, with_ramp10=True):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc = FUEL_TYPE_NAMES.index("gas_cc")
        ct = FUEL_TYPE_NAMES.index("gas_ct")
        nuc = FUEL_TYPE_NAMES.index("nuclear")
        n = 4
        # West: 1,000 MW CC + 1,000 MW nuclear. South: 800 MW CC + 500 MW CT.
        return FleetArrays(
            pmax=np.array([1000.0, 1000.0, 800.0, 500.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 10.0, 7.5, 11.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0, 1, 1]),
            fuel_type_idx=np.array([cc, nuc, cc, ct]),
            availability=np.ones((n, T)),
            unit_ids=["cc_w", "nuc_w", "cc_s", "ct_s"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 200, 300, 400]),
            # RAMP10_FRAC analogue: CC 0.40, nuclear 0 (no upward reserve),
            # CT 1.00.
            ramp10=(np.array([400.0, 0.0, 320.0, 500.0]) if with_ramp10 else None),
        )

    def test_default_off_no_pergen_fields(self):
        cfg = _cfg(iso="MISO")
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        self.assertIsNone(design.pergen_gen_idx)
        self.assertIsNone(design.pergen_ramp10)

    def test_pergen_pools_by_zone_and_class(self):
        cfg = _cfg(iso="MISO", miso_reserve_pergen=True)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        # Members: reserve-eligible units with ramp10 > 0 — the nuclear unit
        # (ramp10 = 0, baseload) drops out.
        np.testing.assert_array_equal(design.pergen_gen_idx, [0, 2, 3])
        # Columns: (West, gas_cc), (South, gas_cc), (South, gas_ct) — three
        # pools; each column's cap is its members' summed availability-scaled
        # hourly ramp10, (n_r, T).
        self.assertEqual(design.pergen_ramp10.shape, (3, 24))
        self.assertAlmostEqual(float(design.pergen_ramp10[:, 0].sum()), 1220.0)

    def test_pergen_ramp_cap_scales_with_availability(self):
        cfg = _cfg(iso="MISO", miso_reserve_pergen=True)
        fleet = self._fleet()
        # Outage the South CT (gen 3) in hour 5: its pool's deliverable
        # 10-min ramp must drop to zero in that hour only.
        fleet.availability[3, 5] = 0.0
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        col = np.asarray(design.pergen_col)
        ct_col = int(col[np.asarray(design.pergen_gen_idx) == 3][0])
        self.assertAlmostEqual(float(design.pergen_ramp10[ct_col, 5]), 0.0)
        self.assertAlmostEqual(float(design.pergen_ramp10[ct_col, 4]), 500.0)
        col = np.asarray(design.pergen_col)
        # Same-zone same-class members share a column; cross-zone never do.
        self.assertEqual(np.unique(col).size, 3)
        by_col = {
            int(c): sorted(int(g) for g in design.pergen_gen_idx[col == c])
            for c in np.unique(col)
        }
        self.assertIn([0], by_col.values())  # West CC alone
        self.assertIn([2], by_col.values())  # South CC alone
        self.assertIn([3], by_col.values())  # South CT alone

    def test_pergen_kwargs_propagate(self):
        cfg = _cfg(iso="MISO", miso_reserve_pergen=True)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        kw = build_reserve_dispatch_kwargs(design)
        self.assertIn("reserve_pergen_gen_idx", kw)
        self.assertIn("reserve_pergen_ramp10", kw)
        self.assertIn("reserve_pergen_col", kw)

    def test_pergen_composes_with_zonal_families(self):
        cfg = _cfg(iso="MISO", miso_reserve_pergen=True, miso_zonal_reserves=True)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        self.assertEqual(len(design.families), 2)
        self.assertIsNotNone(design.pergen_gen_idx)

    def test_missing_ramp10_raises(self):
        cfg = _cfg(iso="MISO", miso_reserve_pergen=True)
        with self.assertRaises(ValueError):
            get_reserve_design(cfg, self._fleet(with_ramp10=False), 24, self._ZONES)


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


class TestErcotEcrsConservativeDeployment(unittest.TestCase):
    """WS2: the published pre-reform ECRS deployment design on the ECRS family."""

    def _design(self, year, T=24, monkey_req=150.0, reform_hour=None):
        import unittest.mock as mock

        import market_sim.config.reserve_config as rc

        def fake_req(_year, hours, code):
            base = {"REGUP": 50.0, "RRS": 100.0, "ECRS": monkey_req, "NSPIN": 120.0}
            return np.full(hours, base[str(code)])

        cfg = _cfg(
            weather_year=year,
            ercot_multiproduct_as_coopt=True,
            ercot_ecrs_conservative_deployment=True,
            ercot_as_critical_frac=0.0,
            ercot_as_n_ramp=4,
        )
        patches = [
            mock.patch(
                "market_sim.results.scarcity.ercot_as_plan_requirement_mw",
                side_effect=fake_req,
            )
        ]
        if reform_hour is not None:
            patches.append(
                mock.patch.object(rc, "ERCOT_ECRS_RELEASE_REFORM_HOUR", reform_hour)
            )
        with patches[0]:
            if reform_hour is not None:
                with patches[1]:
                    return get_reserve_design(cfg, _fleet(T=T), T, ["Z0"])
            return get_reserve_design(cfg, _fleet(T=T), T, ["Z0"])

    def test_2023_rigid_at_cap_all_year(self):
        design = self._design(2023)
        names = [f.name for f in design.families]
        self.assertIn("ECRS_withheld", names)
        self.assertNotIn("ECRS_released", names)
        fam = design.families[names.index("ECRS_withheld")]
        np.testing.assert_array_equal(fam.ordc_penalties, [5000.0])
        self.assertEqual(fam.ordc_step_widths[0], 150.0)
        self.assertTrue((fam.requirement == 150.0).all())

    def test_2024_splits_at_reform_hour(self):
        design = self._design(2024, T=24, reform_hour=12)
        names = [f.name for f in design.families]
        self.assertIn("ECRS_withheld", names)
        self.assertIn("ECRS_released", names)
        # released family appended LAST so the first 4 keep product identity
        self.assertEqual(names[-1], "ECRS_released")
        rigid = design.families[names.index("ECRS_withheld")]
        rel = design.families[names.index("ECRS_released")]
        self.assertTrue((rigid.requirement[:12] == 150.0).all())
        self.assertTrue((rigid.requirement[12:] == 0.0).all())
        self.assertTrue((rel.requirement[:12] == 0.0).all())
        self.assertTrue((rel.requirement[12:] == 150.0).all())
        # both draw on the ECRS reserve class
        self.assertEqual(rigid.reserve_class, rel.reserve_class)
        # released window keeps the standing ramp (multi-step, tops at VOLL)
        self.assertGreater(len(rel.ordc_penalties), 1)
        self.assertAlmostEqual(float(rel.ordc_penalties[-1]), 5000.0)

    def test_2025_reverts_to_standing_ramp(self):
        design = self._design(2025)
        names = [f.name for f in design.families]
        self.assertIn("ECRS", names)
        self.assertNotIn("ECRS_withheld", names)

    def test_flag_off_is_unchanged(self):
        import unittest.mock as mock

        def fake_req(_year, hours, code):
            return np.full(hours, 100.0)

        cfg = _cfg(weather_year=2023, ercot_multiproduct_as_coopt=True)
        with mock.patch(
            "market_sim.results.scarcity.ercot_as_plan_requirement_mw",
            side_effect=fake_req,
        ):
            design = get_reserve_design(cfg, _fleet(), 24, ["Z0"])
        self.assertEqual([f.name for f in design.families][2], "ECRS")


class TestErcotCommitmentHeadroomOverrides(unittest.TestCase):
    """WS1: commitment-state-aware headroom re-scope for the P2 solve."""

    def _fleet4(self, T=6):
        idx = {n: i for i, n in enumerate(FUEL_TYPE_NAMES)}
        fuels = ["gas_cc", "gas_ct", "oil", "wind"]
        n = len(fuels)
        return FleetArrays(
            pmax=np.array([500.0, 200.0, 100.0, 300.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 10.0, 11.0, 0.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0, 1, 1]),
            fuel_type_idx=np.array([idx[f] for f in fuels]),
            availability=np.full((n, T), 0.9),
            unit_ids=["cc", "ct", "oil", "wind"],
            efficiency_bin=np.zeros(n),
            plant_code=np.arange(1, n + 1),
        )

    def test_overrides(self):
        from market_sim.config.reserve_config import (
            ercot_commitment_headroom_overrides,
        )

        T = 6
        fa = self._fleet4(T)
        # P1-style rows: fast = responsive & ~quick (cc only), all = responsive
        he_p1 = np.array(
            [
                [True, False, False, False],
                [True, True, True, False],
            ]
        )
        committed = np.ones((4, T), dtype=bool)
        committed[1, :3] = False  # CT offline first 3 hours
        committed[2, :] = False  # oil offline all hours
        ov = ercot_commitment_headroom_overrides(fa, committed, he_p1)
        he = ov["reserve_headroom_eligible"]
        extra = ov["reserve_headroom_extra_cap"]
        # fast row now spans the full responsive set (per-hour gate = P2 avail)
        np.testing.assert_array_equal(he[0], [True, True, True, False])
        # offline quick-start capacity lands on the "all" row only, in-zone
        self.assertEqual(extra.shape, (2, 2, T))
        self.assertTrue((extra[0] == 0).all())
        # zone 0: CT (200 * 0.9) offline hours 0-2 only
        np.testing.assert_allclose(extra[1, 0, :3], 180.0)
        np.testing.assert_allclose(extra[1, 0, 3:], 0.0)
        # zone 1: oil (100 * 0.9) offline every hour
        np.testing.assert_allclose(extra[1, 1, :], 90.0)
