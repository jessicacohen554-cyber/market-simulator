"""capx D67-ARM (2026-09-06): owner ruling **Q52** — "ARM for PJM".

Arms ``capacity_adequacy_requirement_published_by_iso`` for **PJM only**, through
``_pjm_config`` ``default_scenario_overrides`` (the D57/Q44 pattern; rule 25
``[R-ISO-SCOPE]``). The shared ``ScenarioConfig`` dataclass default stays
``None``, so this is an ISO override rather than a declared default flip and no
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` entry is involved.

Evidence: ``FINDING-capx-d67-2026-09-06.md`` §4 (phase 0, four checks to
0.000 MW), §6.1 (the structural screen, G1–G5 PASS) and §7.1 (the full span:
``arm − published = 0.000 MW`` in all four screened delivery years).
Execution and every pre-declared key: ``PRECOMMIT-capx-d67arm-2026-09-06.md``.

These tests pin what the arming must and must not move. The override must move
**no** other ISO's forecast key and **no** backcast key at all, and the arm must
stay fully invertible — the (b′-1) inverse test: an explicit ``--no-`` caller
reaches the pre-arm posture and keeps its key, so every pre-arm bundle's recipe
remains reachable and identified.
"""

from __future__ import annotations

import unittest

from market_sim.config.iso_configs import (
    SUPPORTED_ISOS,
    apply_iso_scenario_defaults,
    get_iso_config,
)
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)

FIELD = "capacity_adequacy_requirement_published_by_iso"

#: Pre-declared in ``PRECOMMIT-capx-d67arm-2026-09-06.md`` §2 and §5 (P-F/P-G),
#: measured through the shipped harness path at base ``131291b5`` BEFORE the
#: override landed. The bare PJM key advances; every other ISO's is unmoved.
#:
#: RE-PINNED 2026-09-07: PJM's bare key is a function of EVERY armed PJM override,
#: so each new arm on ``_pjm_config`` moves it and restales this constant. Q55
#: (``pjm_vre_accreditation_vintage``, capx D75-R) armed after D67 and moved it
#: ``a9c66d8ea25acb9d`` -> ``b518f5fe7d02f961`` without re-pinning here, which left
#: this file RED on ``main``. The old value is not wrong-in-itself — it is exactly
#: the pre-Q55 bare key, i.e. ``_hindcast_key("PJM", pjm_vre_accreditation_vintage=
#: False)`` — it had simply stopped naming "bare".
#:
#: The NAME is kept for its D67 genealogy but it means "PJM bare, every current arm
#: applied", not "D67-armed only". A future PJM arm must re-measure it here.
#:
#: RE-MEASURED 2026-09-07 for capx D78-ARM: owner ruling Q56 arms
#: ``retirement_sector_gate`` on ``_pjm_config`` — the next arm this note
#: anticipated — moving bare ``b518f5fe7d02f961`` -> ``fb16fda2ddb0a94a``
#: (``docs/handoffs/d78arm/keys_measured.json``, the PRECOMMIT §2 literal).
#:
#: RE-MEASURED 2026-09-07 for capx D76-ARM-B: owner ruling Q58 arms
#: ``capacity_screen_peak_measured_hindcast`` as the SHARED ``ScenarioConfig``
#: default -- the first arm to move this constant WITHOUT touching
#: ``_pjm_config``, so the note above ("a future PJM arm must re-measure it")
#: understated the trigger: a shared default flip that a hindcast recipe
#: resolves moves it too. Bare ``fb16fda2ddb0a94a`` -> ``f736025631d0d27e``
#: (``docs/handoffs/d76armb/key-census-variant-b-postflip.json``, the
#: PRECOMMIT-capx-d76-arm-b §2.6 literal, and the value the inverse test below
#: is anchored against).
#:
#: RE-MEASURED AGAIN 2026-09-07 for capx D84-ARM (owner ruling on
#: ``FINDING-capx-d84-2026-09-07.md`` §8), which arms
#: ``pjm_thermal_accreditation_vintage`` -- the THERMAL RATING half of the D48
#: devintage, the counterpart of Q55's VRE half -- through ``_pjm_config``,
#: so this is back to being a PJM-scoped override rather than a shared flip.
#: Bare ``f736025631d0d27e`` -> ``b9fa47dedb6c3319``, which is D84's OWN
#: measured full-window arm key (its control is the pre-arm bare recipe to the
#: digit), so the arm names the recipe the A/B was measured on. The inverse is
#: completed below, not re-pinned: 15 of 15 legs restore exactly
#: (``PRECOMMIT-capx-d84arm-2026-09-07.md`` §3).
BARE_PJM_ARMED = "b9fa47dedb6c3319"

#: UNCHANGED, and deliberately so: the D67 pre-arm recipe is still reachable and
#: still keeps its own key. What went stale was the INVOCATION below, not this pin —
#: reaching the pre-arm posture now requires inverting Q55 as well as D67. Re-pinning
#: this constant instead of completing the inverse would have silently discarded the
#: (b'-1) invertibility property the test exists to hold.
BARE_PJM_PRE_ARM = "15a723ba3b6dc856"
#: The five non-PJM bare T1-H recipe keys. The NAME still means what it says
#: about D67 -- a PJM-scoped arm must not move another ISO's key -- and that is
#: still what a regression here would catch.
#:
#: RE-MEASURED 2026-09-07 for capx D76-ARM-B (owner ruling Q58). These moved for
#: a reason D67 has nothing to do with: ``capacity_screen_peak_measured_hindcast``
#: armed on the SHARED ``ScenarioConfig`` default, which every hindcast recipe of
#: every ISO resolves. Re-pinning is therefore a re-BASELINE, not a relaxation,
#: and the proof is beside it: :data:`BARE_BY_ISO_PRE_D76` holds each ISO's
#: PRE-flip literal and ``test_no_other_isos_bare_key_moves`` asserts that
#: inverting the D76 flag alone reaches it EXACTLY -- the (b'-1) invertibility
#: property, now pinned for six ISOs instead of one.
BARE_BY_ISO_UNMOVED = {
    "MISO": "71156d9eb2ea896d",
    "NYISO": "ee0d44e7d6f26397",
    "NEISO": "806f31b59b10c911",
    "CAISO": "28f4f62b90e2f74b",
    "ERCOT": "f238df2e5b1ef838",
}

#: Each ISO's bare key BEFORE the capx D76-ARM-B flip, i.e. the literals
#: :data:`BARE_BY_ISO_UNMOVED` carried until 2026-09-07. Reachable today by
#: inverting the one flag, which is what makes every pre-flip hindcast bundle
#: still identified by its own key.
BARE_BY_ISO_PRE_D76 = {
    "MISO": "1f92943f84f42fd0",
    "NYISO": "ee6a3e764324f28f",
    "NEISO": "5b292e24dd752ea4",
    "CAISO": "8f1c3766703a90c4",
    "ERCOT": "46d013cbf1f35d27",
}


def _hindcast_key(iso: str, **kwargs) -> str:
    """The T1-H recipe's resolved cache key, through the shipped CLI builder."""
    from scripts.run_capacity_hindcast import build_config

    cfg = build_config(
        iso,
        2021,
        2025,
        "realized",
        vintage=2020,
        entry_screen_diagnostics=True,
        **kwargs,
    )
    return apply_iso_scenario_defaults(cfg, iso).cache_key()


def _forecast(iso: str) -> ScenarioConfig:
    return apply_iso_scenario_defaults(
        ScenarioConfig(iso=iso, mode="forecast", hindcast=True), iso
    )


class TestQ52PjmRequirementArming(unittest.TestCase):
    def test_pjm_forecast_resolves_the_gate_on(self):
        self.assertEqual(getattr(_forecast("PJM"), FIELD), {"PJM": True})

    def test_the_dataclass_default_stays_none(self):
        # An ISO override, NOT a declared default flip: the shared default is
        # untouched, so no other ISO can inherit the arm and no
        # _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS entry is required.
        self.assertIsNone(getattr(ScenarioConfig(), FIELD))
        self.assertIn(FIELD, _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[FIELD], "None")

    def test_every_other_iso_resolves_the_gate_off(self):
        # Rule 25 [R-ISO-SCOPE]: a PJM posture. The mechanism is generic in
        # form and PJM-scoped by data — another ISO arms on its own market's
        # published table, never on this one's verdict.
        for iso in SUPPORTED_ISOS:
            if iso == "PJM":
                continue
            self.assertIsNone(getattr(_forecast(iso), FIELD), iso)
            self.assertNotIn(FIELD, get_iso_config(iso).default_scenario_overrides, iso)

    def test_pjm_backcast_coerces_the_gate_off_with_its_key_unmoved(self):
        # Every backcast keeper of every ISO stays byte-identical: the field is
        # coerced back to None in a plain backcast and the key does not move.
        bare = ScenarioConfig(iso="PJM", mode="backcast")
        res = apply_iso_scenario_defaults(bare, "PJM")
        self.assertIsNone(getattr(res, FIELD))
        self.assertEqual(res.cache_key(), bare.cache_key())


class TestQ52ArmingKeys(unittest.TestCase):
    """The pre-declared re-key, and the (b′-1) inverse test."""

    def test_bare_pjm_t1h_advances_to_the_declared_key(self):
        self.assertEqual(_hindcast_key("PJM"), BARE_PJM_ARMED)

    def test_explicit_off_reaches_the_pre_arm_posture_and_keeps_its_key(self):
        # (b′-1) inverse test: the arm is fully invertible, so every pre-arm
        # bundle's recipe stays reachable AND identified by its own key.
        # Every arm that landed on ``_pjm_config`` AFTER D67 has to be inverted too,
        # or this reaches an intermediate posture rather than the pre-arm one. Q55
        # (``pjm_vre_accreditation_vintage``) is that arm; without it the key is
        # ``33041553d7541538``, which is not any declared posture. Q56
        # (``retirement_sector_gate``, capx D78-ARM) is the second such arm and
        # is inverted here for the same reason: without it the key is
        # ``bc387828f931e0ac``, another intermediate posture. Q58
        # (``capacity_screen_peak_measured_hindcast``, capx D76-ARM-B) is the
        # THIRD, and the first that is not a ``_pjm_config`` override at all --
        # it is a shared default flip this hindcast recipe resolves -- so it is
        # inverted here for the same reason: without it the key is
        # ``296d933530c3123f``, a third intermediate posture. capx D84-ARM
        # (``pjm_thermal_accreditation_vintage``, the THERMAL RATING half of the
        # D48 devintage) is the FOURTH, and back to being a ``_pjm_config``
        # override; without it the key is ``3de34020c139589f``, a fourth
        # intermediate posture. BARE_PJM_PRE_ARM
        # is deliberately NOT re-pinned; completing the inverse is what holds
        # the (b'-1) property the test exists for.
        self.assertEqual(
            _hindcast_key(
                "PJM",
                capacity_adequacy_requirement_published=False,
                pjm_vre_accreditation_vintage=False,
                retirement_sector_gate=False,
                capacity_screen_peak_measured_hindcast=False,
                pjm_thermal_accreditation_vintage=False,
            ),
            BARE_PJM_PRE_ARM,
        )

    def test_no_other_isos_bare_key_moves(self):
        for iso, expected in BARE_BY_ISO_UNMOVED.items():
            self.assertEqual(_hindcast_key(iso), expected, iso)

    def test_every_iso_pre_d76_recipe_is_still_reachable_and_identified(self):
        """The (b'-1) inverse, for the five non-PJM ISOs (capx D76-ARM-B).

        The 2026-09-07 arm moved every ISO's bare hindcast key, which is the
        intended effect. What must ALSO hold -- and is the reason a moved key is
        a cost rather than a loss -- is that inverting the one flag reaches the
        PRE-flip key exactly, so every hindcast bundle solved before the arm
        stays both reachable and identified by its own key. PJM's version of
        this is the test above; this is the other five.
        """
        for iso, pre in BARE_BY_ISO_PRE_D76.items():
            with self.subTest(iso=iso):
                self.assertEqual(
                    _hindcast_key(iso, capacity_screen_peak_measured_hindcast=False),
                    pre,
                )
                self.assertNotEqual(BARE_BY_ISO_UNMOVED[iso], pre)


class TestD67ArmGdriftPosture(unittest.TestCase):
    """The G-DRIFT audit's INERT classifications, as assertions rather than prose.

    ``PRECOMMIT-capx-d67arm-2026-09-06.md`` §3 classifies every hunk in the
    window ``b1155995 → 131291b5`` on this recipe. The charter's instruction was
    **ASSERT, don't assume** for the two that look inert but are not gated by a
    ``ScenarioConfig`` flag (capx D77's emission-rate factor and capx D78's
    sector routing). Pinning the posture here means a later default flip that
    silently makes one of them live fails a test instead of quietly changing
    the shipped PJM T1-H run.
    """

    def _recipe(self) -> ScenarioConfig:
        from scripts.run_capacity_hindcast import build_config

        return apply_iso_scenario_defaults(
            build_config(
                "PJM",
                2021,
                2025,
                "realized",
                vintage=2020,
                entry_screen_diagnostics=True,
            ),
            "PJM",
        )

    def test_d77_emission_rate_factor_is_an_exact_noop(self):
        # capx D77 books the measured CAMPD rate as
        # ``co2 * (1 - gen.ccs_capture_fraction)``. The field defaults to 0.0,
        # so the factor is exactly 1.0 for every unabated unit — which is every
        # unit of a 2021-2025 hindcast, the retrofit screen being inert below
        # ``ccs_retrofit_available_year``.
        from market_sim.data.fleet import Generator

        self.assertEqual(Generator.model_fields["ccs_capture_fraction"].default, 0.0)

    def test_the_ccs_family_is_inert_below_its_availability_year(self):
        # D65-B (Act A/B), D50's capex scaling and D81's retrofit limb all reach
        # the fleet only through ``apply_ccs_retrofit``, which returns at its
        # first line for ``year < ccs_retrofit_available_year``.
        self.assertGreater(self._recipe().ccs_retrofit_available_year, 2025)

    def test_d78_sector_routing_is_armed_by_q56(self):
        # Pinned FALSE at D67-ARM (the G-DRIFT posture: D78's routing moved an
        # empty set on the shipped recipe). ARMED by owner ruling Q56 (capx
        # D78-ARM, 2026-09-06) through the same _pjm_config override path, so
        # the shipped recipe now carries the gate; the D67-ARM posture is
        # reachable as --no-retirement-sector-gate --no-pjm-vre-accreditation-
        # vintage (key a9c66d8ea25acb9d, pinned in test_capacity.py).
        self.assertTrue(self._recipe().retirement_sector_gate)

    def test_the_default_off_scenario_axes_resolve_off(self):
        cfg = self._recipe()
        self.assertIsNone(cfg.capacity_no_default_cap_convention_by_iso)
        self.assertIsNone(cfg.capacity_going_forward_bar_published_by_iso)
        self.assertIsNone(cfg.mass_cap_tons_by_year)
        self.assertEqual(cfg.voluntary_clean_demand_path, "off")

    def test_d81_is_recorded_as_LIVE_on_this_recipe(self):
        # The honest half of the audit. capx D81 routes the PENDING owner-filed
        # dated block out of the $0 price-taking residual and into the priced
        # sell-offer stack; its two arming conditions BOTH hold here, so the
        # hunk is live and the D67 §7.1 bundle's census/price rows are NOT
        # automatically this posture's. Asserted so the finding's decomposition
        # cannot be read as claiming inertness it never claimed.
        cfg = self._recipe()
        self.assertTrue(cfg.fossil_announced_exits_enabled)
        self.assertEqual(cfg.capacity_market_supply_clearing_by_iso, {"PJM": True})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
