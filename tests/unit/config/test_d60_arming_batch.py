"""capx D60 (2026-09-05): the three-ruling arming batch Q40 / Q41 / Q42.

Owner rulings of the director sitting r#37, executed together so every
re-solve lands on the final posture once:

* **Q40** — ``adequacy_accounting_ratio_dated_net`` armed **for MISO only**
  through ``_miso_config`` ``default_scenario_overrides`` (rule 25
  ``[R-ISO-SCOPE]``); the ``ScenarioConfig`` default stays ``False``.
  Evidence: ``FINDING-capx-d51-2026-09-04.md`` §7.
* **Q41** — ``nyiso_requirement_forecast_peak`` and
  ``nyiso_requirement_vintage_factors`` armed **for NYISO only** through
  ``_nyiso_config`` ``default_scenario_overrides`` (rule 25); both dataclass
  defaults stay ``False``. Evidence: ``FINDING-capx-d52-2026-09-04.md`` §8(1).
* **Q42** — ``ccs_retrofit_capex_co2_scaling`` armed as **the dataclass
  default for all six ISOs**, declared in
  ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` with the frozen drop value left
  at ``"False"`` (option (b'-1), the D44 pattern). Evidence:
  ``FINDING-capx-d50-2026-09-04.md`` §8.

These tests pin what the batch must and must not move. The two ISO overrides
must move NO other ISO's forecast key and no backcast key at all; the Q42
default flip DOES advance both pinned default keys, which is the declared
behaviour of (b'-1) and is asserted here as such rather than left implicit.
"""

from __future__ import annotations

import unittest

from market_sim.config.iso_configs import (
    SUPPORTED_ISOS,
    apply_iso_scenario_defaults,
    get_iso_config,
)
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS,
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    ScenarioConfig,
)

MISO_FIELD = "adequacy_accounting_ratio_dated_net"
NYISO_FIELDS = ("nyiso_requirement_forecast_peak", "nyiso_requirement_vintage_factors")
CCS_FIELD = "ccs_retrofit_capex_co2_scaling"


def _forecast(iso: str) -> ScenarioConfig:
    return apply_iso_scenario_defaults(
        ScenarioConfig(iso=iso, mode="forecast", hindcast=True), iso
    )


class TestQ40MisoRatioArming(unittest.TestCase):
    def test_miso_forecast_resolves_the_ratio_on(self):
        self.assertTrue(getattr(_forecast("MISO"), MISO_FIELD))

    def test_the_dataclass_default_stays_off(self):
        self.assertFalse(getattr(ScenarioConfig(), MISO_FIELD))

    def test_every_other_iso_resolves_the_ratio_off(self):
        for iso in SUPPORTED_ISOS:
            if iso == "MISO":
                continue
            self.assertFalse(getattr(_forecast(iso), MISO_FIELD), iso)
            self.assertNotIn(
                MISO_FIELD, get_iso_config(iso).default_scenario_overrides, iso
            )

    def test_miso_backcast_still_coerces_the_ratio_to_default(self):
        cfg = apply_iso_scenario_defaults(
            ScenarioConfig(iso="MISO", mode="backcast"), "MISO"
        )
        self.assertFalse(getattr(cfg, MISO_FIELD))


class TestQ41NyisoRequirementArming(unittest.TestCase):
    def test_nyiso_forecast_resolves_both_gates_on(self):
        cfg = _forecast("NYISO")
        for field in NYISO_FIELDS:
            self.assertTrue(getattr(cfg, field), field)

    def test_the_dataclass_defaults_stay_off(self):
        for field in NYISO_FIELDS:
            self.assertFalse(getattr(ScenarioConfig(), field), field)

    def test_every_other_iso_resolves_both_gates_off(self):
        for iso in SUPPORTED_ISOS:
            if iso == "NYISO":
                continue
            cfg = _forecast(iso)
            overrides = get_iso_config(iso).default_scenario_overrides
            for field in NYISO_FIELDS:
                self.assertFalse(getattr(cfg, field), (iso, field))
                self.assertNotIn(field, overrides, (iso, field))

    def test_nyiso_backcast_still_coerces_both_gates_to_default(self):
        cfg = apply_iso_scenario_defaults(
            ScenarioConfig(iso="NYISO", mode="backcast"), "NYISO"
        )
        for field in NYISO_FIELDS:
            self.assertFalse(getattr(cfg, field), field)

    def test_the_curve_and_locality_gates_stay_off(self):
        """D52 §8(2) / D59: neither the NYCA ICAP curve nor the locality
        curves were armed by Q41, and neither may ride in on it."""
        cfg = _forecast("NYISO")
        self.assertFalse(cfg.locality_capacity_curves)
        overrides = get_iso_config("NYISO").default_scenario_overrides
        self.assertEqual(set(overrides), set(NYISO_FIELDS))


class TestQ42CcsCapexDefaultFlip(unittest.TestCase):
    def test_the_default_is_armed_for_every_iso(self):
        self.assertTrue(getattr(ScenarioConfig(), CCS_FIELD))
        for iso in SUPPORTED_ISOS:
            self.assertTrue(getattr(_forecast(iso), CCS_FIELD), iso)

    def test_it_is_a_posture_not_an_iso_override(self):
        """Rule 25: the flip is global, so NO ISO carries it as an override."""
        for iso in SUPPORTED_ISOS:
            self.assertNotIn(
                CCS_FIELD, get_iso_config(iso).default_scenario_overrides, iso
            )

    def test_the_flip_is_declared_and_the_frozen_drop_value_is_untouched(self):
        declared = {
            name: value for _, name, value in _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS
        }
        self.assertEqual(declared.get(CCS_FIELD), "True")
        self.assertEqual(_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[CCS_FIELD], "False")

    def test_an_explicit_false_keeps_the_pre_flip_keys(self):
        """(b'-1)'s useful inverse: a control arm keeps its bundle."""
        self.assertEqual(
            ScenarioConfig(**{CCS_FIELD: False}).cache_key(), "4c6b03ae098b6e3e"
        )
        self.assertEqual(
            ScenarioConfig(mode="backcast", **{CCS_FIELD: False}).cache_key(),
            "8211c72bb1960adc",
        )

    def test_the_armed_default_advances_both_pins(self):
        self.assertEqual(ScenarioConfig().cache_key(), "e5ecd4105ada3e58")
        self.assertEqual(
            ScenarioConfig(mode="backcast").cache_key(), "6a2845e50951394e"
        )


class TestNothingElseArmed(unittest.TestCase):
    """The batch arms the three rulings and nothing else."""

    OFF_EVERYWHERE = ("locality_capacity_curves", "capacity_deliverability_limits")

    # Armed for PJM ALONE by capx D57's own owner ruling (2026-09-05, PR #4786),
    # which merged while this lane was in flight. D60 neither armed nor disarmed
    # them; what it asserts is that they stayed PJM-scoped, and that D60's own
    # flip did not ride in on them. Their live consequence for D60 is recorded
    # rather than hidden: PJM's bare t1f recipe moved to 09996eca71ee80fd, so
    # D60's pre-declared `pjm-t1f` rename was REVERSED before pushing (STOP 1)
    # and the PJM t1f re-solve is routed. See FINDING-capx-d60-2026-09-05.md.
    PJM_ONLY = ("pjm_accreditation_design_vintage", "pjm_demand_response_supply")

    def test_the_named_gates_stay_off_in_every_iso(self):
        for iso in SUPPORTED_ISOS:
            cfg = _forecast(iso)
            for field in self.OFF_EVERYWHERE:
                self.assertFalse(getattr(cfg, field), (iso, field))

    def test_the_d57_pjm_gates_stay_pjm_only(self):
        for iso in SUPPORTED_ISOS:
            cfg = _forecast(iso)
            for field in self.PJM_ONLY:
                self.assertEqual(getattr(cfg, field), iso == "PJM", (iso, field))

    def test_the_sector_gate_stays_miso_only(self):
        """D53's arming is untouched by D60 (it is the reason miso-t1f's
        post-D60 key is b1a73a087064ffd8 rather than 3f85ecc45d90c248)."""
        self.assertTrue(_forecast("MISO").retirement_sector_gate)
        for iso in SUPPORTED_ISOS:
            if iso == "MISO":
                continue
            self.assertFalse(_forecast(iso).retirement_sector_gate, iso)


if __name__ == "__main__":
    unittest.main()
