"""Flag→field mapping tests for ``pipeline.backcast_config.backcast_config``.

``backcast_config`` is the single source of truth for how a calibration run's
CLI flags become :class:`ScenarioConfig` fields (the surface the flag registry
in the orchestrator-unification plan will eventually generate). These tests pin
that mapping directly — same pattern as ``test_recorded_cfg_fidelity.py``, but
for the ``backcast_config`` argument surface itself rather than the meta/
run_config reconstruction. No solves.

They guard two failure modes: a flag silently not reaching its field (the
ERCOT-65 recorder-defect class), and the ISO-conditioned structural defaults
(gas monthly actuals, zonal gas basis, mode) drifting.
"""

from __future__ import annotations

import unittest

from market_sim.pipeline.backcast_config import backcast_config


class TestBackcastStructuralDefaults(unittest.TestCase):
    """The fixed backcast levers every calibration year sets, regardless of ISO."""

    def _cfg(self, iso="ERCOT", **kw):
        return backcast_config(2024, iso, 24, 3.0, **kw)

    def test_mode_is_backcast_not_inferred(self):
        # CLAUDE.md: mode is an explicit signal, never inferred from gas price.
        self.assertEqual(self._cfg().mode, "backcast")

    def test_weather_year_and_hours_passthrough(self):
        cfg = backcast_config(2023, "PJM", 8760, 3.0)
        self.assertEqual(cfg.weather_year, 2023)
        self.assertEqual(cfg.hours, 8760)

    def test_fixed_backcast_levers(self):
        cfg = self._cfg()
        self.assertTrue(cfg.vintage_capacity_ramp)
        self.assertTrue(cfg.gas_seasonality)
        self.assertEqual(cfg.td_loss_factor, 0.0)  # EIA-930 is generation-side
        self.assertFalse(cfg.rps_enabled)
        self.assertEqual(cfg.carbon_price, 0.0)  # federal 0 -> state program

    def test_gas_price_reaches_override_field(self):
        # The measured Henry Hub price threads into gas_price_override.
        self.assertEqual(self._cfg().gas_price_override, 3.0)
        self.assertEqual(
            backcast_config(2024, "ERCOT", 24, 4.25).gas_price_override, 4.25
        )


class TestBackcastIsoConditionedDefaults(unittest.TestCase):
    """ISO-conditioned structural defaults (gas hubs), from the config's own
    per-ISO branches — not a residual-tuned surface."""

    def test_gas_monthly_actuals_by_iso(self):
        # CAISO/NYISO/NEISO price gas off measured monthly hubs; ERCOT/PJM don't.
        for iso in ("CAISO", "NYISO", "NEISO"):
            self.assertTrue(
                backcast_config(2024, iso, 24, 3.0).gas_monthly_actuals, iso
            )
        for iso in ("ERCOT", "PJM", "MISO"):
            self.assertFalse(
                backcast_config(2024, iso, 24, 3.0).gas_monthly_actuals, iso
            )

    def test_nyiso_zonal_gas_basis_only_nyiso(self):
        self.assertTrue(backcast_config(2024, "NYISO", 24, 3.0).nyiso_zonal_gas_basis)
        self.assertFalse(backcast_config(2024, "CAISO", 24, 3.0).nyiso_zonal_gas_basis)


class TestBackcastFlagToField(unittest.TestCase):
    """Each explicit flag reaches the field the LP actually reads."""

    def _cfg(self, iso="ERCOT", **kw):
        return backcast_config(2024, iso, 24, 3.0, **kw)

    def test_boolean_flags_thread_through(self):
        for flag in (
            "commitment_enabled",
            "coal_mustrun_per_plant",
            "ct_mustrun_per_plant",
            "retiree_cems_cap",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(getattr(self._cfg(), flag))
                self.assertTrue(getattr(self._cfg(**{flag: True}), flag))

    def test_coal_prb_passthrough_value(self):
        self.assertEqual(
            self._cfg(coal_prb_passthrough=0.75).coal_prb_passthrough, 0.75
        )
        self.assertEqual(self._cfg().coal_prb_passthrough, 1.0)  # default

    def test_offer_curve_overrides_absolute_replace(self):
        cfg = backcast_config(
            2024,
            "PJM",
            24,
            3.0,
            offer_curve_overrides={"CC_REGULAR": {"committed": 0.5}},
        )
        self.assertEqual(cfg.offer_curve_by_group["CC_REGULAR"]["committed"], 0.5)

    def test_offer_curve_deltas_relative_nudge(self):
        base = backcast_config(2024, "PJM", 24, 3.0)
        base_val = base.offer_curve_by_group["CT_PEAKER"]["committed"]
        nudged = backcast_config(
            2024,
            "PJM",
            24,
            3.0,
            offer_curve_deltas={"CT_PEAKER": {"committed": 0.05}},
        )
        self.assertAlmostEqual(
            nudged.offer_curve_by_group["CT_PEAKER"]["committed"], base_val + 0.05
        )

    def test_coal_mustrun_overrides_positional(self):
        # coal_lignite_mustrun / coal_prb_mustrun land on the *_override fields.
        cfg = backcast_config(
            2024, "MISO", 24, 3.0, coal_lignite_mustrun=0.3, coal_prb_mustrun=0.6
        )
        self.assertEqual(cfg.coal_lignite_mustrun_override, 0.3)
        self.assertEqual(cfg.coal_prb_mustrun_override, 0.6)


if __name__ == "__main__":
    unittest.main()


class TestSppNeutralCoalBands(unittest.TestCase):
    """Rule 25 [R-ISO-SCOPE] for SPP (lane SPP-40, 2026-09-07): the generic
    ``COAL`` bands are ERCOT-fitted and a fallback ISO carries 1.0. The
    correction is SPP-scoped — every other ISO's coal bands are untouched."""

    _BANDS = ("committed", "econ_low", "econ_high", "peak")

    def test_spp_coal_bands_are_neutral(self):
        coal = backcast_config(2024, "SPP", 24, 3.0).offer_curve_by_group["COAL"]
        for band in self._BANDS:
            self.assertEqual(coal[band], 1.0, band)
        # The structural share is not a band and stays generic.
        self.assertEqual(coal["econ_low_share"], 0.55)

    def test_spp_supply_class_coal_entries_are_neutral(self):
        # SPP-42 (2026-09-07): once coal_supply_SPP.csv tags each plant
        # prb / lignite, the offer path resolves COAL_PRB / COAL_LIGNITE
        # (fleet._COAL_SUPPLY_TO_CURVE) instead of COAL, so the identity is
        # carried on every coal key — the crosswalk moves the class label,
        # never the offer. The structural share stays the value SPP coal read
        # from the generic COAL entry before the crosswalk.
        curve = backcast_config(2024, "SPP", 24, 3.0).offer_curve_by_group
        for cls in ("COAL", "COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "COAL_WC"):
            for band in self._BANDS:
                self.assertEqual(curve[cls][band], 1.0, (cls, band))
            self.assertEqual(curve[cls]["econ_low_share"], 0.55, cls)

    def test_spp_gas_bands_are_neutral_too(self):
        curve = backcast_config(2024, "SPP", 24, 3.0).offer_curve_by_group
        for cls in ("CC_REGULAR", "CC_CHP", "CT_CHP", "CT_PEAKER", "ST_GAS"):
            for band in self._BANDS:
                self.assertEqual(curve[cls][band], 1.0, (cls, band))

    def test_other_isos_keep_their_coal_bands(self):
        # CAISO / NEISO / NYISO keep the generic ERCOT-fitted coal entry by
        # design ("coal keep the generic defaults"); MISO carries its own.
        for iso in ("CAISO", "NEISO", "NYISO"):
            coal = backcast_config(2024, iso, 24, 3.0).offer_curve_by_group["COAL"]
            self.assertEqual(
                [coal[b] for b in self._BANDS], [0.90, 0.95, 1.10, 1.45], iso
            )
        miso = backcast_config(2024, "MISO", 24, 3.0).offer_curve_by_group["COAL"]
        self.assertEqual([miso[b] for b in self._BANDS], [1.00, 1.00, 1.10, 1.45])


class TestSocoIdentityBands(unittest.TestCase):
    """SOCO plan §7 gate G5 / rule 25 [R-ISO-SCOPE] (lane SOCO-20, 2026-09-14):
    SOCO is a no-price balancing authority, so EVERY class's four offer-curve
    bands read 1.0 — no ERCOT-fitted generic entry leaks in, and no SOCO
    entry is ever fitted (rubric v3.8 scores no SOCO price). Structural
    shares are not bands and keep their generic values."""

    _BANDS = ("committed", "econ_low", "econ_high", "peak")

    def test_every_soco_class_carries_identity_bands(self):
        from market_sim.pipeline.offer_curve_base.generic import (
            GENERIC_BASE_OFFER_CURVE,
        )

        curve = backcast_config(2024, "SOCO", 24, 3.0).offer_curve_by_group
        self.assertTrue(set(GENERIC_BASE_OFFER_CURVE) <= set(curve))
        non_identity = {
            (cls, band): curve[cls][band]
            for cls in curve
            for band in self._BANDS
            if band in curve[cls] and curve[cls][band] != 1.0
        }
        self.assertEqual(non_identity, {})

    def test_soco_structural_shares_stay_generic(self):
        from market_sim.pipeline.offer_curve_base.generic import (
            GENERIC_BASE_OFFER_CURVE,
        )

        curve = backcast_config(2024, "SOCO", 24, 3.0).offer_curve_by_group
        for cls, generic in GENERIC_BASE_OFFER_CURVE.items():
            for key, value in generic.items():
                if key in self._BANDS:
                    continue
                self.assertEqual(curve[cls][key], value, (cls, key))

    def test_other_isos_are_untouched_by_the_soco_branch(self):
        # ERCOT keeps its fitted generic coal entry; SPP its own identity.
        ercot = backcast_config(2024, "ERCOT", 24, 3.0).offer_curve_by_group["COAL"]
        self.assertEqual([ercot[b] for b in self._BANDS], [0.90, 0.95, 1.10, 1.45])
        spp = backcast_config(2024, "SPP", 24, 3.0).offer_curve_by_group["COAL"]
        self.assertEqual([spp[b] for b in self._BANDS], [1.0, 1.0, 1.0, 1.0])
