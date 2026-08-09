"""The one storage-accreditation resolver, its gate, and its blast radius.

Pins the FFR-4E guarantees that make the intake safe to land:

* **G-INERT** — unarmed, ``storage_accreditation_credit`` is byte-identical to
  the ``_elcc_for_duration`` call it replaced, on the CAISO keeper's own
  measured storage fleet. This is what makes the designated CAISO backcast
  keeper inert BY CONSTRUCTION rather than by measurement.
* **Rule 19 [R-ONE-MECH]** — rung 1 REPLACES rung 2, never multiplies it.
* **Rule 25 [R-ISO-SCOPE]** — arming CAISO moves no other ISO.
* **The class boundary** — the ratio is Table 1.1's *Battery* row, and CAISO
  books pumped storage on its Hydro row, so PS stays on the by-duration rung.
"""

from __future__ import annotations

import unittest

from market_sim.config.constants import STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.storage import (
    _elcc_for_duration,
    storage_accreditation_credit,
)

# The CAISO keeper 2026-08-09-caiso-184-c1-lpbasis's storage-relevant recipe,
# read from its committed run_config.json.
_KEEPER_RECIPE = dict(
    iso="CAISO",
    mode="backcast",
    storage_measured_base_fleet=True,
    storage_vintage_ramp=True,
    caiso_storage_shape_anchor=True,
    storage_capacity_value=True,
    storage_degradation=True,
    capacity_deliverability_limits=True,
    renewable_elcc_curves=True,
)
_OTHER_ISOS = ("ERCOT", "PJM", "MISO", "NYISO", "NEISO")


class StorageAccreditationResolverTest(unittest.TestCase):
    """Rung selection, the gate, and the ISO/class boundaries."""

    def setUp(self) -> None:
        self.off = ScenarioConfig(iso="CAISO", mode="forecast")
        self.on = ScenarioConfig(
            iso="CAISO", mode="forecast", caiso_storage_nqc_accreditation=True
        )

    def test_gate_defaults_off(self) -> None:
        """Default-OFF is the keeper guard; it is not an incidental default."""
        self.assertFalse(ScenarioConfig().caiso_storage_nqc_accreditation)
        self.assertFalse(self.off.caiso_storage_nqc_accreditation)

    def test_unarmed_is_byte_identical_to_the_duration_table(self) -> None:
        """G-INERT, at resolver grain: every duration, exactly equal."""
        for duration in (0.5, 1.0, 2.0, 3.4, 4.0, 6.0, 8.0, 12.0, 100.0):
            with self.subTest(duration=duration):
                self.assertEqual(
                    storage_accreditation_credit(duration, "CAISO", self.off),
                    _elcc_for_duration(duration, "CAISO"),
                )

    def test_armed_returns_the_published_ratio_regardless_of_duration(self) -> None:
        """Rung 1 is a WHOLE-CLASS ratio: duration-independent by construction."""
        expected = STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"]
        for duration in (1.0, 2.0, 4.0, 8.0, 100.0):
            with self.subTest(duration=duration):
                self.assertAlmostEqual(
                    storage_accreditation_credit(duration, "CAISO", self.on),
                    expected,
                    places=12,
                )

    def test_rung_1_replaces_rung_2_rather_than_stacking(self) -> None:
        """Rule 19: the armed credit is the ratio itself, not ratio x ELCC."""
        armed = storage_accreditation_credit(4.0, "CAISO", self.on)
        product = STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"] * (
            _elcc_for_duration(4.0, "CAISO")
        )
        self.assertNotAlmostEqual(armed, product, places=6)
        self.assertAlmostEqual(
            armed, STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"], places=12
        )

    def test_pumped_storage_stays_on_the_duration_rung(self) -> None:
        """CAISO books PS on Table 1.1's Hydro row, not the Battery row."""
        for duration in (8.0, 12.0):
            with self.subTest(duration=duration):
                self.assertEqual(
                    storage_accreditation_credit(
                        duration, "CAISO", self.on, "pumped_storage"
                    ),
                    _elcc_for_duration(duration, "CAISO"),
                )

    def test_batteries_take_the_ratio_when_armed(self) -> None:
        """The other side of the class boundary."""
        self.assertAlmostEqual(
            storage_accreditation_credit(4.0, "CAISO", self.on, "li_ion_4hr"),
            STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"],
            places=12,
        )

    def test_arming_caiso_moves_no_other_iso(self) -> None:
        """Rule 25 [R-ISO-SCOPE], measured on the armed config."""
        for iso in _OTHER_ISOS:
            for duration in (2.0, 4.0, 8.0):
                with self.subTest(iso=iso, duration=duration):
                    self.assertEqual(
                        storage_accreditation_credit(duration, iso, self.on),
                        _elcc_for_duration(duration, iso),
                    )

    def test_cache_key_stable_off_and_distinct_on(self) -> None:
        """Registered in _CACHE_KEY_OPTIONAL_FIELDS: unarmed keys must not move."""
        self.assertEqual(ScenarioConfig().cache_key(), "603c2498bf71d21d")
        self.assertNotEqual(self.off.cache_key(), self.on.cache_key())


class KeeperInertnessTest(unittest.TestCase):
    """G-INERT on the CAISO keeper's OWN measured storage fleet."""

    def test_keeper_storage_firm_mw_unmoved_with_the_gate_off(self) -> None:
        """The keeper's accredited storage ledger is exactly unchanged."""
        from market_sim.model.storage import load_eia860_storage

        config = ScenarioConfig(**_KEEPER_RECIPE)
        for year in (2023, 2024, 2025):
            units = load_eia860_storage("CAISO", year, config)
            self.assertTrue(units, f"no measured CAISO storage for {year}")
            head = sum(
                u.power_cap_mw
                * _elcc_for_duration(
                    u.energy_cap_mwh / u.power_cap_mw if u.power_cap_mw > 0 else 0.0,
                    "CAISO",
                )
                for u in units
            )
            gated = sum(
                u.power_cap_mw
                * storage_accreditation_credit(
                    u.energy_cap_mwh / u.power_cap_mw if u.power_cap_mw > 0 else 0.0,
                    "CAISO",
                    config,
                    u.tech_name,
                )
                for u in units
            )
            with self.subTest(year=year):
                self.assertEqual(gated, head)


if __name__ == "__main__":
    unittest.main()
