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
        self.assertTrue((d.supply_cap[2] == 1.0e9).all())  # the repo's
        # standing uncapped sentinel (_RESERVE_SUPPLY_CAP_UNCAPPED_MW) — a
        # finite value, because shared logging int()s the row means.


class TestGuards(unittest.TestCase):
    """Pairing guards fire at DESIGN time, never __post_init__ — the
    calibration channels build the config in stages (the keeper-replay
    crash this build measured), so only the final config is checkable."""

    def test_requires_multiproduct(self):
        cfg = _config(ercot_as_held_location=True, ercot_multiproduct_as_coopt=False)
        with self.assertRaises(ValueError):
            _design(cfg, _fleet())

    def test_requires_a_rigid_family(self):
        cfg = _config(
            ercot_as_held_location=True,
            ercot_ecrs_conservative_deployment=False,
            ercot_nonreleasable_as_withholding=False,
        )
        p = _patches()
        with p[0], p[1], p[2]:
            with self.assertRaises(ValueError):
                _design(cfg, _fleet())

    def test_forecast_mode_hard_errors(self):
        # The _BACKCAST_ONLY_OVERLAY_FIELDS registration fires at CONFIG
        # construction (mode is a base-channel field, so this one IS safe
        # in __post_init__) — earlier than the design-time backstop.
        with self.assertRaises(ValueError):
            _config(ercot_as_held_location=True, mode="forecast")

    def test_endogenous_storage_pairing_refused(self):
        # Simulate the staged/hostile state directly (post_init bypassed),
        # exactly what a design-time guard exists to catch.
        cfg = _config(ercot_as_held_location=True)
        object.__setattr__(cfg, "ercot_storage_as_endogenous", True)
        p = _patches()
        with p[0], p[1], p[2]:
            with self.assertRaises(ValueError):
                _design(cfg, _fleet())


if __name__ == "__main__":
    unittest.main()


class TestHeldRequirementDepth(unittest.TestCase):
    """ercot-227 F1/F1b: max(plan, held) on the requirement basis."""

    def test_off_by_default_and_zeros_identical(self):
        fleet = _fleet()
        p = _patches()  # held loader returns zeros for every product
        with (
            p[0],
            p[1],
            p[2],
            mock.patch.object(
                scarcity,
                "ercot_as_responsibility_mw",
                lambda y, h, c: np.zeros(h),
            ),
        ):
            off = _design(_config(), fleet)
            on = _design(
                _config(
                    ercot_as_held_requirement=True,
                    ercot_as_held_requirement_nspin=True,
                ),
                fleet,
            )
        for a, b in zip(on.families, off.families):
            np.testing.assert_array_equal(a.requirement, b.requirement)

    def test_max_deepens_rigid_window_only(self):
        fleet = _fleet()
        held = {"RRS": 150.0, "NSPIN": 0.0}
        p = _patches(plan=100.0)
        with (
            p[0],
            p[1],
            p[2],
            mock.patch.object(
                scarcity,
                "ercot_as_responsibility_mw",
                lambda y, h, c: np.full(h, held.get(c, 0.0)),
            ),
        ):
            d = _design(_config(ercot_as_held_requirement=True), fleet)
        names = [f.name for f in d.families]
        rrs = d.families[names.index("RRS_withheld")]
        np.testing.assert_allclose(rrs.requirement, 150.0)  # deepened
        regup = d.families[names.index("RegUp_withheld")]
        np.testing.assert_allclose(regup.requirement, 100.0)  # held=0 ⇒ plan

    def test_nspin_leg_gated_separately(self):
        fleet = _fleet()
        p = _patches(plan=100.0)
        with (
            p[0],
            p[1],
            p[2],
            mock.patch.object(
                scarcity,
                "ercot_as_responsibility_mw",
                lambda y, h, c: np.full(h, 400.0 if c == "NSPIN" else 0.0),
            ),
        ):
            f1_only = _design(_config(ercot_as_held_requirement=True), fleet)
            both = _design(
                _config(
                    ercot_as_held_requirement=True,
                    ercot_as_held_requirement_nspin=True,
                ),
                fleet,
            )
        n1 = [f.name for f in f1_only.families]
        nb = [f.name for f in both.families]
        np.testing.assert_allclose(
            f1_only.families[n1.index("NonSpin")].requirement, 100.0
        )
        np.testing.assert_allclose(
            both.families[nb.index("NonSpin")].requirement, 400.0
        )


class TestRucCommitmentFloor(unittest.TestCase):
    """ercot-227 F3: the measured ONRUC instruction-state floor."""

    def _fa(self):
        return _fleet(groups=("ST_GAS", "CT_PEAKER"), pmax=100.0)

    def test_off_or_no_data_returns_base(self):
        from market_sim.pipeline.commitment import wrap_ercot_ruc_floor_prep

        fa = self._fa()
        cfg = _config()  # flag off
        self.assertIsNone(wrap_ercot_ruc_floor_prep(cfg, "ERCOT", fa, None))
        cfg2 = _config(ercot_ruc_commitment_floor=True)
        with mock.patch.object(
            scarcity, "ercot_ruc_committed_mw", lambda y, h, k: np.zeros(h)
        ):
            prep = wrap_ercot_ruc_floor_prep(cfg2, "ERCOT", fa, None)
            self.assertIsNone(prep(None))  # zero series -> no floored fleet

    def test_pro_rata_distribution_and_clip(self):
        from market_sim.pipeline.commitment import _ercot_ruc_floor

        fa = self._fa()
        series = {"ST_GAS": 40.0}
        with mock.patch.object(
            scarcity,
            "ercot_ruc_committed_mw",
            lambda y, h, k: np.full(h, series.get(k, 0.0)),
        ):
            floor = _ercot_ruc_floor(_config(ercot_ruc_commitment_floor=True), fa)
        self.assertIsNotNone(floor)
        np.testing.assert_allclose(floor[0], 40.0)  # the ST_GAS member
        np.testing.assert_allclose(floor[1], 0.0)  # the CT member untouched
        # Clip: series above class capability caps at capability.
        with mock.patch.object(
            scarcity,
            "ercot_ruc_committed_mw",
            lambda y, h, k: np.full(h, 500.0 if k == "ST_GAS" else 0.0),
        ):
            floor = _ercot_ruc_floor(_config(ercot_ruc_commitment_floor=True), fa)
        np.testing.assert_allclose(floor[0], 100.0)  # pmax-capped

    def test_composes_after_base_prep_with_mech_tag(self):
        from market_sim.data.floor_mechanisms import MECH_ERCOT_RUC_COMMITMENT
        from market_sim.pipeline.commitment import wrap_ercot_ruc_floor_prep

        fa = self._fa()
        with mock.patch.object(
            scarcity,
            "ercot_ruc_committed_mw",
            lambda y, h, k: np.full(h, 30.0 if k == "ST_GAS" else 0.0),
        ):
            prep = wrap_ercot_ruc_floor_prep(
                _config(ercot_ruc_commitment_floor=True), "ERCOT", fa, None
            )
            out = prep(None)
        self.assertIsNotNone(out)
        np.testing.assert_allclose(out.min_gen[0], 30.0)
        mech = np.asarray(out.min_gen_mechanism)
        self.assertTrue((mech[0] == MECH_ERCOT_RUC_COMMITMENT).all())
