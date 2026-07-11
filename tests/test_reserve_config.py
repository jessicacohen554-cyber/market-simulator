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


class TestPjmPergenDesign(unittest.TestCase):
    """PJM per-asset reserve columns (pjm_reserve_pergen): (zone, fuel-class)
    pooled R columns — the miso-39 memory tier — bounded by the summed
    hourly availability-scaled 10-min deliverable ramp."""

    _ZONES = ["PJM_West", "PJM_EMAAC"]

    def _fleet(self, T=24, with_ramp10=True):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc = FUEL_TYPE_NAMES.index("gas_cc")
        ct = FUEL_TYPE_NAMES.index("gas_ct")
        nuc = FUEL_TYPE_NAMES.index("nuclear")
        n = 5
        # West: two CC plants (must POOL into one column) + nuclear.
        # EMAAC (a MAD zone): one CC + one CT.
        return FleetArrays(
            pmax=np.array([1000.0, 600.0, 1000.0, 800.0, 500.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 7.2, 10.0, 7.5, 11.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0, 0, 1, 1]),
            fuel_type_idx=np.array([cc, cc, nuc, cc, ct]),
            availability=np.ones((n, T)),
            unit_ids=["cc_w1", "cc_w2", "nuc_w", "cc_e", "ct_e"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 150, 200, 300, 400]),
            # RAMP10_FRAC analogue: CC 0.40, nuclear 0, CT 1.00.
            ramp10=(
                np.array([400.0, 240.0, 0.0, 320.0, 500.0]) if with_ramp10 else None
            ),
        )

    def _cfg(self, **kw):
        # weather_year 1999: no measured PJM-AS parquet exists, so the design
        # deterministically takes the 1.5x-MSSC formula fallback and omits
        # the MAD family (environment-independent test).
        return _cfg(iso="PJM", weather_year=1999, pjm_reserve_pergen=True, **kw)

    def test_default_off_no_pergen_fields(self):
        cfg = _cfg(iso="PJM", weather_year=1999)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        self.assertIsNone(design.pergen_gen_idx)
        self.assertIsNone(design.pergen_ramp10)

    def test_pergen_pools_by_zone_and_class(self):
        design = get_reserve_design(self._cfg(), self._fleet(), 24, self._ZONES)
        # Members: reserve-eligible units with ramp10 > 0 — nuclear drops out.
        np.testing.assert_array_equal(design.pergen_gen_idx, [0, 1, 3, 4])
        col = np.asarray(design.pergen_col)
        # Three pools: (West, cc) shared by BOTH West CC plants, (EMAAC, cc),
        # (EMAAC, ct) — the class tier never gives a plant its own column.
        self.assertEqual(np.unique(col).size, 3)
        self.assertEqual(int(col[0]), int(col[1]))
        self.assertNotEqual(int(col[1]), int(col[2]))
        # Hourly (n_r, T) caps: West CC pool = 400 + 240 = 640.
        self.assertEqual(design.pergen_ramp10.shape, (3, 24))
        west_cc = int(col[0])
        self.assertAlmostEqual(float(design.pergen_ramp10[west_cc, 0]), 640.0)
        self.assertAlmostEqual(float(design.pergen_ramp10[:, 0].sum()), 1460.0)

    def test_pergen_ramp_cap_scales_with_availability(self):
        fleet = self._fleet()
        # Outage one West CC plant (gen 1) in hour 5: the pool's deliverable
        # ramp drops by exactly its member share in that hour only.
        fleet.availability[1, 5] = 0.0
        design = get_reserve_design(self._cfg(), fleet, 24, self._ZONES)
        col = np.asarray(design.pergen_col)
        west_cc = int(col[0])
        self.assertAlmostEqual(float(design.pergen_ramp10[west_cc, 5]), 400.0)
        self.assertAlmostEqual(float(design.pergen_ramp10[west_cc, 4]), 640.0)

    def test_pergen_requires_ramp10(self):
        with self.assertRaises(ValueError):
            get_reserve_design(
                self._cfg(), self._fleet(with_ramp10=False), 24, self._ZONES
            )

    def test_pergen_kwargs_propagate(self):
        design = get_reserve_design(self._cfg(), self._fleet(), 24, self._ZONES)
        kw = build_reserve_dispatch_kwargs(design)
        self.assertIn("reserve_pergen_gen_idx", kw)
        self.assertIn("reserve_pergen_ramp10", kw)
        self.assertIn("reserve_pergen_col", kw)


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


class TestErcotOrdcTotalReserve(unittest.TestCase):
    """The lumped ORDC total-reserve family layered on the multi-product stack."""

    def _design(self, **cfg_kw):
        import unittest.mock as mock

        def fake_req(_year, hours, code):
            base = {"REGUP": 50.0, "RRS": 100.0, "ECRS": 150.0, "NSPIN": 120.0}
            return np.full(hours, base[str(code)])

        cfg = _cfg(ercot_multiproduct_as_coopt=True, **cfg_kw)
        with mock.patch(
            "market_sim.results.scarcity.ercot_as_plan_requirement_mw",
            side_effect=fake_req,
        ):
            return get_reserve_design(cfg, _fleet(), 24, ["Z0"])

    def test_flag_off_no_extra_family(self):
        design = self._design()
        self.assertEqual(len(design.families), 4)
        self.assertNotIn("ercot_ordc_total", [f.name for f in design.families])

    def test_total_family_appended_last_all_class(self):
        design = self._design(ercot_ordc_total_reserve=True)
        names = [f.name for f in design.families]
        # first 4 keep their product identity for downstream consumers
        self.assertEqual(len(names), 5)
        self.assertEqual(names[-1], "ercot_ordc_total")
        total = design.families[-1]
        self.assertEqual(total.reserve_class, -1)
        # requirement = the ORDC curve span (mcl + mu_eff + 5 sigma), flat
        expected_top = 3000.0 + 0.5 * 1400.0 + 5.0 * 1400.0
        np.testing.assert_allclose(total.requirement, expected_top)
        # widths span the full curve; penalties ascend toward VOLL
        self.assertAlmostEqual(float(total.ordc_step_widths.sum()), expected_top)
        self.assertTrue(np.all(np.diff(total.ordc_penalties) >= -1e-9))
        self.assertLessEqual(float(total.ordc_penalties.max()), 5000.0)

    def test_kwargs_carry_all_class_sentinel(self):
        design = self._design(ercot_ordc_total_reserve=True)
        kw = build_reserve_dispatch_kwargs(design)
        self.assertEqual(kw["reserve_requirement"].shape, (5, 24))
        self.assertEqual(int(kw["reserve_balance_class"][-1]), -1)
        # the family-major ORDC block partitions exactly
        self.assertEqual(
            int(kw["reserve_balance_ordc_counts"].sum()), len(kw["ordc_penalties"])
        )

    def test_load_resource_credit_nets_off_total(self):
        import unittest.mock as mock

        with mock.patch(
            "market_sim.results.scarcity.ercot_load_resource_reserve_credit_mw",
            return_value=np.full(24, 800.0),
        ):
            design = self._design(
                ercot_ordc_total_reserve=True,
                ercot_load_resource_reserve=True,
                ercot_load_resource_reserve_from_year=2023,
                mode="backcast",
            )
        total = design.families[-1]
        expected_top = 3000.0 + 0.5 * 1400.0 + 5.0 * 1400.0
        np.testing.assert_allclose(total.requirement, expected_top - 800.0)


class TestErcotOrdcOnlyScarcity(unittest.TestCase):
    """Pre-RTC+B ORDC-only scarcity pricing (ercot57 joint round, v2).

    Under ``ercot_ordc_only_scarcity`` the standing product families keep the
    measured AS-plan requirement but their k×VOLL/n_ramp shortfall ladders
    become a single plan-hold epsilon step (held when headroom exists, never
    priced); the pre-reform ECRS_withheld family keeps its rigid VOLL step;
    the in-LP ORDC total family is forbidden (rule 19) — RT reserve scarcity
    prices post-solve on the realized envelope room
    (``scarcity.ercot_ordc_realized_adder``).
    """

    def _design(self, **cfg_kw):
        import unittest.mock as mock

        def fake_req(_year, hours, code):
            base = {"REGUP": 50.0, "RRS": 100.0, "ECRS": 150.0, "NSPIN": 120.0}
            return np.full(hours, base[str(code)])

        cfg = _cfg(ercot_multiproduct_as_coopt=True, **cfg_kw)
        with mock.patch(
            "market_sim.results.scarcity.ercot_as_plan_requirement_mw",
            side_effect=fake_req,
        ):
            return get_reserve_design(cfg, _fleet(), 24, ["Z0"])

    def test_flag_off_keeps_voll_ladders(self):
        design = self._design()
        for fam in design.families[:4]:
            self.assertGreater(fam.ordc_penalties.size, 1)
            self.assertGreater(float(fam.ordc_penalties.max()), 100.0)

    def test_flag_on_products_carry_plan_hold_eps_only(self):
        from market_sim.config.constants import ERCOT_AS_PLAN_HOLD_EPS

        design = self._design(ercot_ordc_only_scarcity=True)
        names = [f.name for f in design.families]
        # No in-LP ORDC total family under the v2 design (rule 19).
        self.assertNotIn("ercot_ordc_total", names)
        self.assertEqual(len(names), 4)
        for fam in design.families:
            # One epsilon step spanning the plan peak — held, never priced.
            self.assertEqual(fam.ordc_penalties.size, 1)
            self.assertAlmostEqual(float(fam.ordc_penalties[0]), ERCOT_AS_PLAN_HOLD_EPS)
            np.testing.assert_allclose(
                fam.ordc_step_widths, [float(fam.requirement.max())]
            )
        # Requirements themselves are unchanged (the measured plan is held).
        self.assertAlmostEqual(float(design.families[0].requirement.max()), 50.0)

    def test_ecrs_withheld_keeps_rigid_voll_step(self):
        # 2023 conservative-deployment year: the withheld family's single VOLL
        # step (the IMM-documented no-price-release design) survives ORDC-only.
        design = self._design(
            ercot_ordc_only_scarcity=True,
            ercot_ecrs_conservative_deployment=True,
            weather_year=2023,
        )
        names = [f.name for f in design.families]
        self.assertIn("ECRS_withheld", names)
        withheld = design.families[names.index("ECRS_withheld")]
        self.assertEqual(withheld.ordc_penalties.size, 1)
        self.assertAlmostEqual(float(withheld.ordc_penalties[0]), 5000.0)

    def test_scenario_config_gates(self):
        from market_sim.config.scenarios import ScenarioConfig

        base = dict(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            energy_reserve_coopt=True,
            ercot_multiproduct_as_coopt=True,
            ercot_online_capacity_envelope_measured=True,
            ercot_thermal_dam_availability=True,
        )
        # Valid v2 combination constructs cleanly.
        ScenarioConfig(**base, ercot_ordc_only_scarcity=True)
        # In-LP total family alongside -> rule-19 hard error.
        with self.assertRaises(ValueError):
            ScenarioConfig(
                **base,
                ercot_ordc_only_scarcity=True,
                ercot_ordc_total_reserve=True,
            )
        # No envelope variant -> no room quantity -> hard error.
        no_env = dict(base, ercot_online_capacity_envelope_measured=False)
        with self.assertRaises(ValueError):
            ScenarioConfig(**no_env, ercot_ordc_only_scarcity=True)
        # No multi-product co-opt -> hard error.
        no_mp = dict(base, ercot_multiproduct_as_coopt=False)
        with self.assertRaises(ValueError):
            ScenarioConfig(**no_mp, ercot_ordc_only_scarcity=True)

    def test_envelope_is_pricing_only_under_ordc_only(self):
        # Under ordc_only the envelope array moves to the pricing-basis field
        # and the LP row is NOT installed (v3: pre-RTC+B SCED carries no
        # committed-capability dispatch constraint).
        import unittest.mock as mock

        def fake_req(_year, hours, code):
            base = {"REGUP": 50.0, "RRS": 100.0, "ECRS": 150.0, "NSPIN": 120.0}
            return np.full(hours, base[str(code)])

        dummy_env = np.vstack([np.full(24, 1.0e9), np.full(24, 9_000.0)])
        cfg = _cfg(
            ercot_multiproduct_as_coopt=True,
            ercot_ordc_only_scarcity=True,
            ercot_online_capacity_envelope_measured=True,
        )
        with (
            mock.patch(
                "market_sim.results.scarcity.ercot_as_plan_requirement_mw",
                side_effect=fake_req,
            ),
            mock.patch(
                "market_sim.results.scarcity.ercot_online_capacity_envelope_mw",
                return_value=dummy_env,
            ),
        ):
            # The envelope branch needs the net-load driver threaded in.
            design = get_reserve_design(
                cfg,
                _fleet(),
                24,
                ["Z0"],
                system_load=np.full(24, 1_000.0),
                wind_gen=np.zeros(24),
                solar_gen=np.zeros(24),
            )
        self.assertIsNone(design.online_capacity_cap)
        np.testing.assert_allclose(design.online_capacity_pricing_mw, dummy_env)
        kw = build_reserve_dispatch_kwargs(design)
        self.assertNotIn("reserve_online_capacity_cap", kw)

    def test_realized_adder_prices_low_room_not_fat_room(self):
        from types import SimpleNamespace

        from market_sim.results.scarcity import ercot_ordc_realized_adder

        T = 24
        cfg = SimpleNamespace(
            mode="backcast",
            weather_year=2024,
            ordc_voll=5000.0,
            ordc_mcl_mw=3000.0,
            ordc_lolp_mu_mw=0.0,
            ordc_lolp_sigma_mw=1400.0,
            ordc_lolp_shift_sigma=0.5,
            ordc_multistep_floor=False,
            ordc_lolp_params_path=None,
            ercot_storage_as_reserve=False,
            storage_as_commitment=False,
            ercot_storage_as_endogenous=False,
            ercot_load_resource_reserve=False,
        )
        # Two units, both all-tier eligible; env 10 GW flat; supply cap rows
        # give a 1 GW offline term.
        design = SimpleNamespace(
            online_capacity_cap=np.vstack([np.full(T, 1.0e9), np.full(T, 10_000.0)]),
            headroom_products=np.array([[True, False], [True, True]]),
            headroom_eligible=np.ones((2, 2), dtype=bool),
            supply_cap=np.vstack([np.full(T, 8_000.0), np.full(T, 9_000.0)]),
        )
        prices = np.full((1, T), 30.0)
        demand = np.full((1, T), 5_000.0)
        # Fat room: dispatch 2 GW -> room 8 GW -> LOLP ~ 0 -> adder ~ 0.
        fat = ercot_ordc_realized_adder(
            cfg,
            2024,
            design=design,
            dispatch=np.full((2, T), 1_000.0),
            prices=prices,
            demand=demand,
        )
        # Tight room: dispatch 8 GW -> room 2 GW < MCL -> adder ~ VOLL - lambda.
        tight = ercot_ordc_realized_adder(
            cfg,
            2024,
            design=design,
            dispatch=np.full((2, T), 4_000.0),
            prices=prices,
            demand=demand,
        )
        self.assertLess(float(fat.max()), 5.0)
        self.assertGreater(float(tight.min()), 2_000.0)
        # No envelope in the design -> None (the caller must not price).
        none_design = SimpleNamespace(
            online_capacity_cap=None,
            headroom_products=design.headroom_products,
            headroom_eligible=design.headroom_eligible,
            supply_cap=design.supply_cap,
        )
        self.assertIsNone(
            ercot_ordc_realized_adder(
                cfg,
                2024,
                design=none_design,
                dispatch=np.full((2, T), 1_000.0),
                prices=prices,
                demand=demand,
            )
        )


class TestErcotStorageAsProductCredit(unittest.TestCase):
    """Measured battery AS award netted pro-rata off the fast products."""

    def _design(self, **cfg_kw):
        import unittest.mock as mock

        def fake_req(_year, hours, code):
            base = {"REGUP": 100.0, "RRS": 300.0, "ECRS": 200.0, "NSPIN": 400.0}
            return np.full(hours, base[str(code)])

        cfg = _cfg(
            ercot_multiproduct_as_coopt=True,
            storage_as_commitment=True,
            ercot_storage_as_reserve_from_year=2024,
            weather_year=2024,
            **cfg_kw,
        )
        with (
            mock.patch(
                "market_sim.results.scarcity.ercot_as_plan_requirement_mw",
                side_effect=fake_req,
            ),
            mock.patch(
                "market_sim.results.scarcity.ercot_storage_as_reserve_mw",
                return_value=np.full(24, 300.0),
            ),
        ):
            return get_reserve_design(cfg, _fleet(), 24, ["Z0"])

    def test_credit_nets_fast_products_pro_rata(self):
        design = self._design(ercot_storage_as_product_credit=True)
        by_name = {f.name: f for f in design.families}
        # fast total 600, credit 300 -> each fast product halves; NSPIN intact
        self.assertAlmostEqual(float(by_name["RegUp"].requirement[0]), 50.0)
        self.assertAlmostEqual(float(by_name["RRS"].requirement[0]), 150.0)
        self.assertAlmostEqual(float(by_name["ECRS"].requirement[0]), 100.0)
        self.assertAlmostEqual(float(by_name["NonSpin"].requirement[0]), 400.0)
        # penalty curves untouched (still sized to the published plan)
        self.assertGreater(len(by_name["RRS"].ordc_penalties), 1)

    def test_flag_off_unchanged(self):
        design = self._design()
        by_name = {f.name: f for f in design.families}
        self.assertAlmostEqual(float(by_name["RRS"].requirement[0]), 300.0)

    def test_noop_under_endogenous(self):
        design = self._design(
            ercot_storage_as_product_credit=True, ercot_storage_as_endogenous=True
        )
        by_name = {f.name: f for f in design.families}
        self.assertAlmostEqual(float(by_name["RRS"].requirement[0]), 300.0)


class TestCaisoDesign(unittest.TestCase):
    """CAISO per-generator reserve co-optimization (_caiso_design, issue #1492).

    Two co-drawn contingency families (spin + non-spin) on a shared pergen R
    pool, requirement = max(MSSC, 6% load) split half/half, published
    §27.1.2.3.5 scarcity demand curves.
    """

    _ZONES = ["NP15", "ZP26", "SP15", "WECC_import"]

    def _fleet(self, T=24, with_ramp10=True):
        cc = FUEL_TYPE_NAMES.index("gas_cc")
        ct = FUEL_TYPE_NAMES.index("gas_ct")
        hyd = FUEL_TYPE_NAMES.index("hydro")
        n = 4
        # NP15: 1,000 MW CC. SP15: 800 MW CC + 500 MW CT + 600 MW hydro.
        return FleetArrays(
            pmax=np.array([1000.0, 800.0, 500.0, 600.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 7.5, 11.0, 0.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 2, 2, 2]),
            fuel_type_idx=np.array([cc, cc, ct, hyd]),
            availability=np.ones((n, T)),
            unit_ids=["cc_np", "cc_sp", "ct_sp", "hyd_sp"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 300, 400, 500]),
            # RAMP10_FRAC analogue: CC 0.40, CT 1.00, hydro 0 (no ramp10 entry).
            ramp10=(np.array([400.0, 320.0, 500.0, 0.0]) if with_ramp10 else None),
        )

    def test_two_contingency_families(self):
        cfg = _cfg(iso="CAISO", weather_year=1999)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        self.assertEqual(
            [f.name for f in design.families], ["caiso_spin", "caiso_nonspin"]
        )

    def test_requirement_is_mssc_floor_without_load(self):
        # No system_load -> flat MSSC floor. MSSC = largest plant = 1,000 MW
        # (NP15 CC), split half/half -> 500 MW each product.
        cfg = _cfg(iso="CAISO", weather_year=1999)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        for fam in design.families:
            self.assertAlmostEqual(float(fam.requirement[0]), 500.0)

    def test_requirement_tracks_six_percent_load(self):
        # 6% of a 20,000 MW load = 1,200 MW > MSSC 1,000 -> requirement binds
        # on load, split half/half -> 600 MW each.
        cfg = _cfg(iso="CAISO", weather_year=1999)
        load = np.full(24, 20000.0)
        design = get_reserve_design(
            cfg, self._fleet(), 24, self._ZONES, system_load=load
        )
        for fam in design.families:
            self.assertAlmostEqual(float(fam.requirement[0]), 600.0)

    def test_published_demand_curves(self):
        cfg = _cfg(iso="CAISO", weather_year=1999)
        load = np.full(24, 20000.0)  # requirement 600 MW/product
        design = get_reserve_design(
            cfg, self._fleet(), 24, self._ZONES, system_load=load
        )
        by_name = {f.name: f for f in design.families}
        # Spin: flat $100 (10% of the $1,000 soft cap), one step spanning req.
        np.testing.assert_allclose(by_name["caiso_spin"].ordc_penalties, [100.0])
        np.testing.assert_allclose(by_name["caiso_spin"].ordc_step_widths, [600.0])
        # Non-spin: $500/$600/$700 at 70 / 210 MW tiers, remainder to req.
        np.testing.assert_allclose(
            by_name["caiso_nonspin"].ordc_penalties, [500.0, 600.0, 700.0]
        )
        np.testing.assert_allclose(
            by_name["caiso_nonspin"].ordc_step_widths, [70.0, 140.0, 390.0]
        )

    def test_pergen_pools_include_hydro_with_backfilled_ramp(self):
        # Hydro joins the CAISO-local pool (issue #1492 constraint 3): the
        # fleet tables leave its ramp10 at 0, and _caiso_design backfills it
        # to CAISO_HYDRO_RAMP10_FRAC x pmax. Four (zone, fuel) columns:
        # (NP15,cc), (SP15,cc), (SP15,ct), (SP15,hydro); deliverable ramp
        # 400 + 320 + 500 + 600 (hydro full nameplate) = 1,820 MW.
        cfg = _cfg(iso="CAISO", weather_year=1999)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        np.testing.assert_array_equal(design.pergen_gen_idx, [0, 1, 2, 3])
        self.assertEqual(design.pergen_ramp10.shape, (4, 24))
        self.assertAlmostEqual(float(design.pergen_ramp10[:, 0].sum()), 1820.0)

    def test_hydro_backfill_leaves_mssc_unchanged(self):
        # The 600 MW hydro plant is smaller than the 1,000 MW CC, so admitting
        # hydro to the eligibility mask must not move the MSSC floor.
        cfg = _cfg(iso="CAISO", weather_year=1999)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        for fam in design.families:
            self.assertAlmostEqual(float(fam.requirement[0]), 500.0)

    def test_storage_participation_fields(self):
        # Issue #1492 constraint 2: batteries/pumped storage back reserve via
        # the duration-gated RS columns at the published 30-minute ASSOC
        # sustain — the design must carry storage_eligible + the duration.
        cfg = _cfg(iso="CAISO", weather_year=1999)
        design = get_reserve_design(cfg, self._fleet(), 24, self._ZONES)
        self.assertTrue(design.storage_eligible)
        np.testing.assert_allclose(design.storage_duration_h, [0.5])
        kw = build_reserve_dispatch_kwargs(design)
        self.assertTrue(kw.get("reserve_storage"))
        np.testing.assert_allclose(kw["reserve_storage_duration_h"], [0.5])

    def test_pergen_ramp_scales_with_availability(self):
        cfg = _cfg(iso="CAISO", weather_year=1999)
        fleet = self._fleet()
        fleet.availability[2, 5] = 0.0  # outage the SP15 CT in hour 5
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        col = np.asarray(design.pergen_col)
        ct_col = int(col[np.asarray(design.pergen_gen_idx) == 2][0])
        self.assertAlmostEqual(float(design.pergen_ramp10[ct_col, 5]), 0.0)
        self.assertAlmostEqual(float(design.pergen_ramp10[ct_col, 4]), 500.0)

    def test_kwargs_propagate_pergen_and_families(self):
        cfg = _cfg(iso="CAISO", weather_year=1999)
        load = np.full(24, 20000.0)
        design = get_reserve_design(
            cfg, self._fleet(), 24, self._ZONES, system_load=load
        )
        kw = build_reserve_dispatch_kwargs(design)
        self.assertIn("reserve_pergen_gen_idx", kw)
        self.assertIn("reserve_pergen_ramp10", kw)
        self.assertIn("reserve_balance_zone_mask", kw)
        self.assertIn("reserve_balance_ordc_counts", kw)
        # ORDC counts: 1 spin step + 3 non-spin steps.
        np.testing.assert_array_equal(kw["reserve_balance_ordc_counts"], [1, 3])

    def test_missing_ramp10_raises(self):
        cfg = _cfg(iso="CAISO", weather_year=1999)
        with self.assertRaises(ValueError):
            get_reserve_design(cfg, self._fleet(with_ramp10=False), 24, self._ZONES)
