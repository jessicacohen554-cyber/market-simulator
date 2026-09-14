"""D-26 / D-29 arming of the two MISO row families for the MISO forecast lane.

Owner decision D-26 (sitting Addendum Y.4, signed 2026-08-06; measured basis
FFR-7B-2 §3.1) arms the FFR-7B Arm 2 / FFR-6B E-1 K-row per-compliance-region
RPS grain as a MISO **forecast** default, via
``ISOConfig.default_scenario_overrides`` (the D-2' /
``entry_vre_capacity_revenue`` precedent).

Owner decision **D-29** (sitting Addendum AK.8, signed 2026-08-11; lane
ARM-3-ARM, measured basis ARM3-FIX §4) arms **Arm 3**
(``miso_clean_tier_rows``) through the same seam. Until D-29 this module pinned
the opposite — "Arm 3 stays unarmed everywhere" — because arming was blocked on
the open §45U-vs-clean-dual composition (D-22 / X.2); that blocker was closed by
D-28 option A, and the zone-mask defect that made the family untestable was
fixed by ARM3-FIX. Arm 3 needs no gate of its own: the clean arrays are built
only inside the Arm-2 branch, so it inherits that gate (rule 19
``[R-ONE-MECH]``).

D-29 is a declared **cache epoch for the MISO forecast lane**
(``cd2403cc031515db`` -> ``9337e00504e1e72a``) and for that lane only. The
tests below pin both halves of what makes it clean: the ``ScenarioConfig``
field default stays ``False`` (so an armed run ENTERS the digest rather than
colliding with its pre-arm predecessor, and the global pin — ``cedadc285f8603b9``
when this was written, ``4c6b03ae098b6e3e`` since the 2026-09-03 capx D44 flip
of an unrelated field — cannot move BY THIS ARMING), and no MISO backcast key
shifts.

The flag's forecast-mode restriction is enforced at **CONSUMPTION**
(``runner._rps_region_grain_active``), not at config construction — the arming
override is applied unconditionally by ``runner.run_scenario_iso``, so a
backcast-mode MISO config can legitimately carry ``miso_rps_compliance_regions
= True``. That makes "backcast is untouched" a claim that has to be PROVEN
rather than asserted in a comment, which is what this module does.

**Three independent layers insulate the backcast lane**, each tested here:

1. ``rps_enabled`` is ``False`` in every backcast by construction, so the whole
   RPS block — either grain — is skipped before the gate is even reached.
2. The backcast lane (``scripts/run_calibration_full.py`` /
   ``pipeline.backcast_config``) never applies ``default_scenario_overrides``
   at all, so the flag never becomes ``True`` on a backcast config.
3. The consumption gate itself requires ``config.mode == "forecast"``.

Layer 2 is load-bearing for **cache identity**, not just for dispatch:
``miso_rps_compliance_regions`` is a ``_CACHE_KEY_OPTIONAL_FIELDS`` member
registered at ``False``, so an armed backcast config would hash DISTINCTLY from
today's keepers even though it would solve identically. ``test_an_armed_backcast_
would_move_the_cache_key`` pins that hazard explicitly so a future session
cannot wire the overrides into the backcast lane without a failing test.

Pure config construction — no solve, no data root (the FFR-1D
``test_forecast_mode_guards`` discipline).
"""

from __future__ import annotations

import dataclasses

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.pipeline.backcast_config import backcast_config
from market_sim.runner import _rps_region_grain_active

ALL_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")


def _backcast(iso: str) -> ScenarioConfig:
    """A minimal real backcast config from the lane's own builder."""
    return backcast_config(year=2024, iso=iso, hours=8760, gas_price=3.0)


# --------------------------------------------------------------------------- #
# The arming itself (D-26)
# --------------------------------------------------------------------------- #
class TestD26Arming:
    def test_miso_isoconfig_arms_the_flag(self):
        overrides = get_iso_config("MISO").default_scenario_overrides
        assert overrides.get("miso_rps_compliance_regions") is True

    def test_no_other_iso_arms_it(self):
        """Rule 25 [R-ISO-SCOPE] — the verdict is MISO's and only MISO's.

        The four other RPS ISOs' single ISO-wide row is arithmetically exact
        under free intra-ISO REC trade (FFR-6B §2.1); PJM/NEISO zonal rows were
        refused on structure (FFR-6B §7). None may inherit MISO's arming.
        """
        for iso in ALL_ISOS:
            if iso == "MISO":
                continue
            overrides = get_iso_config(iso).default_scenario_overrides
            assert "miso_rps_compliance_regions" not in overrides, iso

    def test_miso_isoconfig_arms_the_clean_tier_family(self):
        """Arm 3 is ARMED for MISO by owner decision D-29 (2026-08-11).

        This test is the INVERSE of the one it replaces. Until D-29 the module
        pinned "Arm 3 stays unarmed everywhere", because arming was blocked on
        the open §45U-vs-clean-dual composition (owner D-22 / X.2). BOTH
        blockers are now closed — the composition by D-28 option A (F2-45U), and
        the generator-column zone-mask defect by ARM3-FIX — and D-29 (sitting
        Addendum AK.8) arms the family through the SAME seam D-26 used for
        Arm 2. Measured basis: ARM3-FIX §4,
        ``docs/handoffs/arm3-fix-zone-mask-2026-08-09.md``.
        """
        overrides = get_iso_config("MISO").default_scenario_overrides
        assert overrides.get("miso_clean_tier_rows") is True

    def test_no_other_iso_arms_the_clean_tier_family(self):
        """Rule 25 [R-ISO-SCOPE] — D-29's verdict is MISO's and only MISO's.

        ``MISO_CLEAN_TIER_REGIONS`` has no member outside MISO, and the family
        carries a strict one-directional dependency on the Arm-2 K-row grain
        (``runner.py`` refuses it loudly without) that no other ISO can satisfy.
        """
        for iso in ALL_ISOS:
            if iso == "MISO":
                continue
            overrides = get_iso_config(iso).default_scenario_overrides
            assert "miso_clean_tier_rows" not in overrides, iso

    def test_the_arming_seam_is_the_iso_override_not_the_field_default(self):
        """The ``ScenarioConfig`` field default MUST stay ``False`` under D-29.

        Two independent things break if a future session "syncs" the field
        default to the ISO override:

        * **Rule 25.** The field default is ISO-agnostic, so ``True`` there arms
          the family for all six ISOs and trips the strict Arm-2 dependency for
          the five that never carry the K-row grain.
        * **Cache identity.** ``miso_clean_tier_rows`` is a
          ``_CACHE_KEY_OPTIONAL_FIELDS`` member, which ``cache_key()`` drops
          against the LIVE field default. At field-default ``False`` an armed
          MISO forecast run differs from it and so ENTERS the digest, keying
          distinctly — that is what makes the D-29 arming a clean cache epoch
          (cd2403cc031515db -> 9337e00504e1e72a) instead of a silent collision
          in which armed runs re-use their pre-arm bundles.
        """
        assert "miso_clean_tier_rows" in _CACHE_KEY_OPTIONAL_FIELDS
        assert ScenarioConfig().miso_clean_tier_rows is False

    def test_the_d29_arming_moves_the_miso_forecast_key_and_not_the_pin(self):
        """The declared cache epoch, asserted on the live config.

        The GLOBAL pin is computed on ``ScenarioConfig()`` — iso ERCOT, no ISO
        override applied — where the field is still ``False``, so the arming
        cannot move it. The MISO forecast lane's own default key must move, or
        armed runs would silently re-use pre-arm bundles.
        """
        base = ScenarioConfig(mode="forecast", iso="MISO")
        armed = dataclasses.replace(base, miso_clean_tier_rows=True)
        assert armed.cache_key() != base.cache_key()
        # ADVANCED 2026-09-06, e5ecd4105ada3e58 -> 547053bdfccd4264, by capx
        # D65-B (owner ruling Q47): the coupled arming of
        # ccs_retrofit_fixed_cost_co2_scaling (a declared (b'-1) flip) with
        # ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh 2026$. Nothing to do with
        # MISO's RPS arming — the global pin moved, so this pole moves with it.
        # PRECOMMIT-capx-d65b-2026-09-06.md §3; ledger entry 2026-09-06c.
        assert ScenarioConfig().cache_key() == "547053bdfccd4264"

    def test_arming_does_not_disturb_the_d2prime_entry(self):
        """The pre-existing D-2' override survives alongside the new one."""
        overrides = get_iso_config("MISO").default_scenario_overrides
        assert overrides.get("entry_vre_capacity_revenue") is True


# --------------------------------------------------------------------------- #
# The consumption gate — forecast fires, backcast does not
# --------------------------------------------------------------------------- #
class TestConsumptionGate:
    def test_forecast_miso_armed_builds_the_region_grain(self):
        cfg = ScenarioConfig(
            mode="forecast", iso="MISO", miso_rps_compliance_regions=True
        )
        assert _rps_region_grain_active(cfg, "MISO") is True

    def test_backcast_miso_resolves_the_legacy_row_even_when_armed(self):
        """THE D-26 backcast-untouched proof (gate is mode-checked here).

        The arming override is applied unconditionally by ``run_scenario_iso``,
        so this exact config — MISO, flag True, mode backcast — is reachable.
        It must still fall through to the scalar ``rps_target`` path, whose
        K=1/mask-all equivalence to the region builder is proven byte-identical
        in ``tests/unit/model/test_dispatch.py::TestRpsComplianceRegionRows``.
        """
        cfg = ScenarioConfig(
            mode="backcast", iso="MISO", miso_rps_compliance_regions=True
        )
        assert _rps_region_grain_active(cfg, "MISO") is False

    def test_forecast_non_miso_never_builds_the_grain(self):
        """Rule 25 at the gate: even a hand-armed non-MISO config is refused."""
        for iso in ALL_ISOS:
            if iso == "MISO":
                continue
            cfg = ScenarioConfig(
                mode="forecast", iso=iso, miso_rps_compliance_regions=True
            )
            assert _rps_region_grain_active(cfg, iso) is False, iso

    def test_unarmed_forecast_miso_keeps_the_iso_wide_row(self):
        """Makes the arming test non-vacuous: the flag is what flips it."""
        cfg = ScenarioConfig(
            mode="forecast", iso="MISO", miso_rps_compliance_regions=False
        )
        assert _rps_region_grain_active(cfg, "MISO") is False


# --------------------------------------------------------------------------- #
# The backcast lane — layers 1 and 2
# --------------------------------------------------------------------------- #
class TestBackcastLaneUntouched:
    def test_backcast_builder_never_arms_the_flag(self):
        """Layer 2: the calibration lane applies no ISO scenario overrides.

        ``scripts/run_calibration_full.py`` reads ``get_iso_config`` for
        topology only and never applies ``default_scenario_overrides`` — that
        application lives solely in ``runner.run_scenario_iso`` and the two
        forecast-side export tools. So the D-26 arming is invisible here.
        """
        cfg = _backcast("MISO")
        assert cfg.mode == "backcast"
        assert cfg.miso_rps_compliance_regions is False
        assert cfg.miso_clean_tier_rows is False

    def test_rps_is_disabled_in_every_backcast(self):
        """Layer 1: no RPS row of EITHER grain exists in a backcast at all."""
        for iso in ALL_ISOS:
            assert _backcast(iso).rps_enabled is False, iso

    def test_backcast_key_is_byte_stable_across_the_arming(self):
        """The MISO backcast cache key is unmoved by D-26.

        The field sits at its registered ``_CACHE_KEY_OPTIONAL_FIELDS``
        default in the backcast lane, so it is dropped from the hash and every
        existing MISO keeper keys exactly as before.
        """
        cfg = _backcast("MISO")
        assert (
            cfg.miso_rps_compliance_regions
            == ScenarioConfig().miso_rps_compliance_regions
        )
        at_default = dataclasses.replace(cfg, miso_rps_compliance_regions=False)
        assert cfg.cache_key() == at_default.cache_key()

    def test_an_armed_backcast_would_move_the_cache_key(self):
        """THE HAZARD LAYER 2 IS PROTECTING — pinned so it cannot regress.

        This is why the backcast lane must keep ignoring
        ``default_scenario_overrides``. Arming the flag on a backcast config
        yields a DISTINCT cache key even though the solve is identical (the
        gate suppresses the grain), which would silently orphan every MISO
        backcast keeper's cached results. A future session that wires the
        overrides into the calibration lane fails here.
        """
        cfg = _backcast("MISO")
        armed = dataclasses.replace(cfg, miso_rps_compliance_regions=True)
        assert armed.cache_key() != cfg.cache_key()
        # ...and the gate still refuses to build the grain for it, so the two
        # keys would name byte-identical solves — the orphaning, precisely.
        assert _rps_region_grain_active(armed, "MISO") is False

    def test_field_is_registered_cache_key_optional(self):
        """The registration the byte-stability above depends on."""
        assert "miso_rps_compliance_regions" in _CACHE_KEY_OPTIONAL_FIELDS

    def test_d29_clean_arming_cannot_reach_a_backcast(self):
        """The same three layers insulate Arm 3's D-29 arming (rule 22).

        Arm 3 needs no gate of its own: ``runner.run_scenario_iso`` builds
        ``clean_region_arrays`` only INSIDE the ``_rps_region_grain_active``
        branch, so the clean family inherits Arm 2's MISO-only + forecast-mode
        gate wholesale (rule 19 ``[R-ONE-MECH]`` — one gate, not two). Layer 2
        is asserted just above (the backcast builder leaves BOTH flags False);
        this pins the gate leg, which is what would still hold if a future
        session wired the overrides into the calibration lane.
        """
        armed = dataclasses.replace(
            _backcast("MISO"),
            miso_rps_compliance_regions=True,
            miso_clean_tier_rows=True,
        )
        assert armed.mode == "backcast"
        assert _rps_region_grain_active(armed, "MISO") is False

    def test_d29_clean_arming_leaves_the_backcast_key_byte_stable(self):
        """No MISO backcast keeper is re-keyed by D-29.

        The cache epoch D-29 declares is a FORECAST-lane epoch. In the backcast
        lane the flag sits at its registered default and is dropped from the
        digest, so ``2026-08-09-miso-148-basis-aware`` and every other MISO
        backcast bundle keys exactly as before.
        """
        cfg = _backcast("MISO")
        assert cfg.miso_clean_tier_rows == ScenarioConfig().miso_clean_tier_rows
        at_default = dataclasses.replace(cfg, miso_clean_tier_rows=False)
        assert cfg.cache_key() == at_default.cache_key()
