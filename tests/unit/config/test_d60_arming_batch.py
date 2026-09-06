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

    def test_an_explicit_false_is_still_constructible_and_still_drops(self):
        """(b'-1)'s useful inverse: a control arm keeps its bundle.

        REWRITTEN 2026-09-06 (capx D65-B). This test used to pin the two
        explicit-``False`` keys at ``4c6b03ae098b6e3e`` / ``8211c72bb1960adc``.
        Both moved, and NEITHER movement is Q42's: D65-B Act B re-identifies
        ``ccs_retrofit_vom_adder`` 8.0 -> 2.95 $/MWh (2026$), and that field is
        a plain value with no frozen declaration to drop at, so it re-keys
        EVERY config including this control arm. Re-pinning the two literals
        would have kept the letter of the test and lost its subject, so what
        it pins is now the PROPERTY the literals stood for — the D50 field
        still drops out of the hash at its frozen declaration — expressed as an
        invariance that survives the next unrelated re-key.
        """
        for mode in ("forecast", "backcast"):
            explicit = ScenarioConfig(mode=mode, **{CCS_FIELD: False})
            # Constructible AT ALL. D65-B Act A's flip made the pair
            # (seam 1 explicit False, seam 4 at its now-armed default) raise in
            # __post_init__, which would have made THIS control arm — and six
            # committed bundles — unreachable. The pair resolution moved to
            # _scenario_config_init, where the caller's explicitness is visible.
            self.assertFalse(getattr(explicit, CCS_FIELD), mode)
            # The seam-4 shape gate demotes with it: without seam 1 there is no
            # k to scale by, so it is inert by construction and False is the
            # truthful record.
            self.assertFalse(
                explicit.ccs_retrofit_fixed_cost_co2_scaling,
                f"{mode}: seam 4 must follow seam 1 down, not raise",
            )
            # STILL DROPPED at the frozen declaration: an explicit False hashes
            # identically to a config that never mentions the field. This is the
            # property "a control arm keeps its bundle" actually rests on, and
            # it holds independently of what any other field is worth.
            same = ScenarioConfig(
                mode=mode,
                **{CCS_FIELD: False},
                ccs_retrofit_fixed_cost_co2_scaling=False,
            )
            self.assertEqual(explicit.cache_key(), same.cache_key(), mode)

    def test_an_explicit_incoherent_pair_is_still_refused(self):
        """Seam 4 asked for EXPLICITLY without seam 1 remains an error.

        The D65-B repair relaxes the DEFAULT pairing, never the declared one:
        a caller who believes they armed the shape gate while seam 1 is off is
        still told otherwise (rule 24 — no tunable that cannot change a solve).
        """
        with self.assertRaises(ValueError) as ctx:
            ScenarioConfig(
                **{CCS_FIELD: False}, ccs_retrofit_fixed_cost_co2_scaling=True
            )
        self.assertIn("ccs_retrofit_fixed_cost_co2_scaling", str(ctx.exception))

    def test_the_armed_default_advances_both_pins(self):
        # ADVANCED 2026-09-06 by capx D65-B / owner ruling Q47, NOT by Q42:
        # e5ecd4105ada3e58 -> 547053bdfccd4264 and 6a2845e50951394e ->
        # f61891696e671969. Cause block: tests/regression/test_persisted_identity.py;
        # pre-declared in docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md §3;
        # cache-epoch ledger entry 2026-09-06c.
        self.assertEqual(ScenarioConfig().cache_key(), "547053bdfccd4264")
        self.assertEqual(
            ScenarioConfig(mode="backcast").cache_key(), "f61891696e671969"
        )

    def test_q42s_own_drop_mechanic_survives_the_d65b_coupling(self):
        """Q42's (b'-1) mechanic, isolated from D65-B Act B's value change.

        The honest way to show a flip's drop mechanic still works after an
        unrelated re-key: hold the OTHER act at its pre-change value and check
        that the explicit-``False`` arm lands on the key it always had. This is
        the same decomposition PRECOMMIT-capx-d65b-2026-09-06.md §3.1 uses to
        show D65-B's own STOP does not fire.
        """
        pre_act_b = dict(ccs_retrofit_vom_adder=8.0)
        self.assertEqual(
            ScenarioConfig(**{CCS_FIELD: False}, **pre_act_b).cache_key(),
            "4c6b03ae098b6e3e",
        )
        self.assertEqual(
            ScenarioConfig(
                mode="backcast", **{CCS_FIELD: False}, **pre_act_b
            ).cache_key(),
            "8211c72bb1960adc",
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

    def test_the_sector_gate_arms_per_iso(self):
        """D53's arming is untouched by D60 (it is the reason miso-t1f's
        post-D60 key is b1a73a087064ffd8 rather than 3f85ecc45d90c248).
        PJM arms it on its OWN evidence (owner ruling Q56, capx D78-ARM,
        2026-09-06); every other ISO still resolves the gate OFF (rule 25)."""
        self.assertTrue(_forecast("MISO").retirement_sector_gate)
        self.assertTrue(_forecast("PJM").retirement_sector_gate)
        for iso in SUPPORTED_ISOS:
            if iso in ("MISO", "PJM"):
                continue
            self.assertFalse(_forecast(iso).retirement_sector_gate, iso)


if __name__ == "__main__":
    unittest.main()
