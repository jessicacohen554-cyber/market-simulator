"""Tests for the ercot-226 held-location carve (``ercot_as_held_location``).

Trivial cases first (CLAUDE.md testing pattern), hermetic throughout: the
measured loaders are monkeypatched so no data files are read, and every
assertion targets the design/LP objects the mechanism actually changes —
class families, the conserving product credit, the class-capability clip,
the rigid-window masks, and the flag-off / no-data byte-neutrality that
carries the 2024/2025 invariance (PRECOMMIT-ercot226 §5.7).
"""

import unittest
from unittest import mock

import numpy as np

import market_sim.results.scarcity as scarcity
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.reserves.spec import (
    _ercot_rigid_end,
    build_reserve_dispatch_kwargs,
    get_reserve_design,
)

H = 24


def _config(**kw) -> ScenarioConfig:
    base = dict(
        iso="ERCOT",
        mode="backcast",
        weather_year=2023,
        energy_reserve_coopt=True,
        ercot_multiproduct_as_coopt=True,
        ercot_ecrs_conservative_deployment=True,
        ercot_nonreleasable_as_withholding=True,
    )
    base.update(kw)
    return ScenarioConfig(**base)


def _fleet(groups=("CC_REGULAR", "CT_PEAKER"), pmax=100.0):
    """One gas generator per plant group, single zone, ``plant_group`` set."""
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone="Z0",
            fuel_type="gas_cc" if g.startswith("CC") else "gas_ct",
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, g in enumerate(groups)
    ]
    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=H)
    try:
        fa.plant_group = np.array(groups)
    except Exception:  # frozen dataclass fallback
        object.__setattr__(fa, "plant_group", np.array(groups))
    return fa


def _patches(plan=100.0, held=None):
    """Patch the measured loaders the multiproduct design imports.

    ``held``: dict[(klass, code)] -> flat MW (default all-zero).
    """
    held = held or {}

    def _plan(year, hours, code):
        return np.full(hours, float(plan))

    def _held(year, hours, klass, code):
        return np.full(hours, float(held.get((klass, code), 0.0)))

    return [
        mock.patch.object(scarcity, "ercot_as_plan_requirement_mw", _plan),
        mock.patch.object(scarcity, "ercot_as_held_by_class_mw", _held),
        mock.patch.object(
            scarcity, "ercot_rtolcap_supply_cap_mw", lambda *a, **k: None
        ),
    ]


def _design(config, fleet):
    return get_reserve_design(config, fleet, H, ["Z0"])


class TestRigidEndHelper(unittest.TestCase):
    """The behavior-identical refactor of the rigid-window date logic."""

    def test_windows(self):
        cfg = _config()
        self.assertEqual(_ercot_rigid_end(cfg, 2023, 8760, "ECRS"), 8760)
        self.assertEqual(_ercot_rigid_end(cfg, 2024, 8760, "ECRS"), 212 * 24)
        self.assertEqual(_ercot_rigid_end(cfg, 2025, 8760, "ECRS"), 0)
        self.assertEqual(_ercot_rigid_end(cfg, 2024, 8760, "RRS"), 8760)
        self.assertEqual(_ercot_rigid_end(cfg, 2025, 8760, "REGUP"), 338 * 24)
        self.assertEqual(_ercot_rigid_end(cfg, 2023, 8760, "NSPIN"), 0)
        off = _config(
            ercot_ecrs_conservative_deployment=False,
            ercot_nonreleasable_as_withholding=False,
            ercot_as_held_location=False,
        )
        self.assertEqual(_ercot_rigid_end(off, 2023, 8760, "ECRS"), 0)


class TestOffByDefault(unittest.TestCase):
    def test_no_class_machinery_when_off(self):
        cfg = _config()  # flag defaults False
        with _patches()[0], _patches()[1], _patches()[2]:
            d = _design(cfg, _fleet())
        self.assertFalse(any(f.name.endswith("_held") for f in d.families))
        self.assertEqual(d.headroom_eligible.shape[0], 2)
        self.assertIsNone(d.headroom_storage)

    def test_no_data_is_flag_off_identical(self):
        """Zero held series ⇒ design equals the flag-off design (invariance)."""
        fleet = _fleet()
        p = _patches(held={})
        with p[0], p[1], p[2]:
            off = _design(_config(), fleet)
            on = _design(_config(ercot_as_held_location=True), fleet)
        self.assertEqual([f.name for f in on.families], [f.name for f in off.families])
        for a, b in zip(on.families, off.families):
            np.testing.assert_array_equal(a.requirement, b.requirement)
        np.testing.assert_array_equal(on.eligible, off.eligible)
        np.testing.assert_array_equal(on.headroom_products, off.headroom_products)
        self.assertIsNone(on.headroom_storage)


class TestCarveAndCredit(unittest.TestCase):
    def test_class_family_and_conserving_credit(self):
        fleet = _fleet()
        held = {("gas_cc", "RRS"): 40.0}
        p = _patches(plan=100.0, held=held)
        with p[0], p[1], p[2]:
            d = _design(_config(ercot_as_held_location=True), fleet)
        names = [f.name for f in d.families]
        self.assertIn("gas_cc_held", names)
        # Class family appended BEFORE any total family and AFTER products.
        self.assertGreater(names.index("gas_cc_held"), 3)
        fam = d.families[names.index("gas_cc_held")]
        np.testing.assert_allclose(fam.requirement, 40.0)
        self.assertEqual(int(fam.reserve_class), 4)  # first new class
        # Conserving credit: RRS_withheld gives up exactly the located MW.
        rrs = d.families[names.index("RRS_withheld")]
        np.testing.assert_allclose(rrs.requirement, 60.0)
        # Other rigid products untouched (their held is zero).
        regup = d.families[names.index("RegUp_withheld")]
        np.testing.assert_allclose(regup.requirement, 100.0)
        # Eligibility row = the CC member only; headroom grows to 3 rows.
        self.assertEqual(d.eligible.shape[0], 5)
        np.testing.assert_array_equal(d.eligible[4], [True, False])
        self.assertEqual(d.headroom_eligible.shape[0], 3)
        # headroom_products: (3, 5); class R rides both tier rows + its own.
        self.assertEqual(d.headroom_products.shape, (3, 5))
        self.assertTrue(d.headroom_products[0, 4])
        self.assertTrue(d.headroom_products[1, 4])
        self.assertTrue(d.headroom_products[2, 4])
        self.assertFalse(d.headroom_products[2, :4].any())
        # Storage backs the tier rows only.
        np.testing.assert_array_equal(d.headroom_storage, [True, True, False])
        # Kwargs carry the new mask through to the LP builder.
        kw = build_reserve_dispatch_kwargs(d)
        np.testing.assert_array_equal(
            kw["reserve_headroom_storage"], [True, True, False]
        )

    def test_clip_at_class_capability(self):
        fleet = _fleet(pmax=100.0)  # CC capability = 100 MW every hour
        held = {("gas_cc", "RRS"): 500.0}
        p = _patches(plan=1000.0, held=held)
        with p[0], p[1], p[2]:
            d = _design(_config(ercot_as_held_location=True), fleet)
        names = [f.name for f in d.families]
        fam = d.families[names.index("gas_cc_held")]
        np.testing.assert_allclose(fam.requirement, 100.0)  # clipped
        rrs = d.families[names.index("RRS_withheld")]
        np.testing.assert_allclose(rrs.requirement, 900.0)  # credited by USED

    def test_supply_cap_padded_with_uncapped_rows(self):
        fleet = _fleet()
        held = {("gas_cc", "RRS"): 40.0}
        p = _patches(plan=100.0, held=held)
        cap = np.full((2, H), 5000.0)
        with (
            p[0],
            p[1],
            mock.patch.object(
                scarcity, "ercot_rtolcap_supply_cap_mw", lambda *a, **k: cap
            ),
        ):
            d = _design(
                _config(ercot_as_held_location=True, ercot_reserve_supply_cap=True),
                fleet,
            )
        self.assertEqual(d.supply_cap.shape, (3, H))
        self.assertTrue(np.isinf(d.supply_cap[2]).all())


class TestGuards(unittest.TestCase):
    def test_requires_multiproduct(self):
        with self.assertRaises(ValueError):
            _config(ercot_as_held_location=True, ercot_multiproduct_as_coopt=False)

    def test_requires_a_rigid_family(self):
        with self.assertRaises(ValueError):
            _config(
                ercot_as_held_location=True,
                ercot_ecrs_conservative_deployment=False,
                ercot_nonreleasable_as_withholding=False,
            )

    def test_forecast_mode_hard_errors(self):
        # The _BACKCAST_ONLY_OVERLAY_FIELDS registration fires at CONFIG
        # construction — earlier (and stricter) than the design-time
        # _require_backcast_measured backstop.
        with self.assertRaises(ValueError):
            _config(ercot_as_held_location=True, mode="forecast")

    def test_endogenous_storage_pairing_refused(self):
        with self.assertRaises(ValueError):
            _config(
                ercot_as_held_location=True,
                ercot_storage_as_endogenous=True,
            )


if __name__ == "__main__":
    unittest.main()
