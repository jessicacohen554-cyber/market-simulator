"""D-26 arming of ``miso_rps_compliance_regions`` for the MISO forecast lane.

Owner decision D-26 (sitting Addendum Y.4, signed 2026-08-06; measured basis
FFR-7B-2 §3.1) arms the FFR-7B Arm 2 / FFR-6B E-1 K-row per-compliance-region
RPS grain as a MISO **forecast** default, via
``ISOConfig.default_scenario_overrides`` (the D-2' /
``entry_vre_capacity_revenue`` precedent).

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

ALL_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")


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

    def test_clean_tier_rows_stays_unarmed_everywhere(self):
        """Arm 3 is BLOCKED on the open §45U composition (owner D-22 / X.2).

        Not this lane's decision. The flag is implemented and default-off; the
        FFR-7B-2 Arm-3 leg on the dashboard is *measurement evidence*, never an
        arming.
        """
        for iso in ALL_ISOS:
            overrides = get_iso_config(iso).default_scenario_overrides
            assert "miso_clean_tier_rows" not in overrides, iso

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
