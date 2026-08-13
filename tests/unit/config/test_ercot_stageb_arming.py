"""D-30 arming of FFR-9C stage B as the ERCOT forecast default.

Owner decision **D-30** (sitting Addendum AK.8, signed 2026-08-11; lane
FFR-9C-PROMOTE, pre-registration
``docs/handoffs/PREREG-ffr-9c-promote-stageb-2026-08-12.md``) promotes stage B
(R-a ``entry_pipeline_aware_signal``, R-b ``smr_available_year``,
R-d ``vre_procurement_additions_enabled``) **as one coherent unit with the two
capacity-screen control-recipe flags** it was measured on top of
(``capacity_screen_unified_lookahead`` + ``capacity_screen_scarcity_restoration``),
via ``ISOConfig.default_scenario_overrides`` — the D-29 seam from the same
sitting (``test_miso_rps_region_arming.py`` is this module's model).

The ISO-scoped seam is FORCED, not stylistic: ``ScenarioConfig.__post_init__``
raises when the restoration flag is armed without the lookahead, and raises for
ANY non-ERCOT ISO carrying the restoration flag (the RTOLCAP/RTOFFCAP share
tables are ERCOT-identified, rule 25 ``[R-ISO-SCOPE]``). A shipped-default flip
on the ``ScenarioConfig`` scalars cannot express this posture at all.

D-30 is a declared **cache epoch for the ERCOT forecast/hindcast lane**
(``062d440558103f81`` -> ``8d9ef77edb3e44cb``) and for that lane only. Every
pre-epoch ERCOT forecast/hindcast sidecar — FH-5's ERCOT legs included — is
historical record and never a post-epoch baseline. The measured half of the
declaration is ``scripts/probes/_ffr9c_stageb_cache_epoch.py``; the tests below
pin both halves of what makes the epoch clean: the ``ScenarioConfig`` field
defaults stay ``False``/``None`` (so an armed run ENTERS the digest rather than
colliding with its pre-arm predecessor, and the global pin ``603c2498bf71d21d``
cannot move), and no ERCOT backcast key shifts.

FORMER LIVE EXPOSURE — **CLOSED 2026-08-13**, and deliberately never pinned
here: ``apply_iso_scenario_defaults`` used to treat a caller value equal to the
field default as "unset" and re-arm it, so an ERCOT control arm for any of the
five flags was inexpressible through the config path
(``docs/handoffs/FINDING-ffr-9c-iso-override-precedence-2026-08-12.md``). The
OVERRIDE-FIX lane landed FINDING §4 remedy 2 (the caller's explicitly-set-field
record, ``scenarios.explicitly_set_fields``); the fixed seam is pinned by
``tests/unit/config/test_iso_override_precedence.py``. Because this module never
pinned the defective precedence, none of its assertions moved across that fix —
it pins only the behaviour both sides must preserve, which is exactly why it
still passes unchanged.

Pure config construction — no solve, no data root (the FFR-1D
``test_forecast_mode_guards`` discipline).
"""

from __future__ import annotations

import dataclasses

import pytest

from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.pipeline.backcast_config import backcast_config

ALL_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

# The five promoted fields and their D-30 values (PREREG §1.6).
STAGE_B = {
    "capacity_screen_unified_lookahead": True,
    "capacity_screen_scarcity_restoration": True,
    "entry_pipeline_aware_signal": True,
    "smr_available_year": 2030,
    "vre_procurement_additions_enabled": True,
}


def _backcast(iso: str) -> ScenarioConfig:
    """A minimal real backcast config from the lane's own builder."""
    return backcast_config(year=2024, iso=iso, hours=8760, gas_price=3.0)


# --------------------------------------------------------------------------- #
# The arming itself (D-30)
# --------------------------------------------------------------------------- #
class TestD30Arming:
    def test_ercot_isoconfig_arms_all_five(self):
        """Stage B is ONE coherent unit — all five rows, together (PREREG §1.1).

        Partial promotion is mechanically impossible (the restoration flag
        requires the lookahead by construction) and evidentially unsound (the
        R-a/R-b/R-d magnitudes were measured ON TOP of the armed screens; a
        posture shipping three without two was never solved, rule 13
        ``[R-MEASURED]``).
        """
        overrides = get_iso_config("ERCOT").default_scenario_overrides
        for field, value in STAGE_B.items():
            assert overrides.get(field) == value, field

    def test_no_other_iso_arms_any_of_them(self):
        """Rule 25 [R-ISO-SCOPE] — D-30's verdict is ERCOT's and only ERCOT's."""
        for iso in ALL_ISOS:
            if iso == "ERCOT":
                continue
            overrides = get_iso_config(iso).default_scenario_overrides
            for field in STAGE_B:
                assert field not in overrides, (iso, field)

    def test_non_ercot_restoration_raises_at_construction(self):
        """The rule-25 wall is structural, not conventional.

        The restoration flag's committed-capability (RTOLCAP/RTOFFCAP) share
        tables are ERCOT-identified, so a hand-armed non-ERCOT config is
        refused at ``__post_init__`` — stronger than a consumption gate.
        """
        with pytest.raises(ValueError, match="ERCOT-only"):
            ScenarioConfig(
                iso="CAISO",
                capacity_screen_unified_lookahead=True,
                capacity_screen_scarcity_restoration=True,
            )

    def test_restoration_requires_lookahead(self):
        """The two screen flags are a pair by construction (PREREG §1.2)."""
        with pytest.raises(ValueError, match="capacity_screen_unified_lookahead"):
            ScenarioConfig(iso="ERCOT", capacity_screen_scarcity_restoration=True)

    def test_the_arming_seam_is_the_iso_override_not_the_field_defaults(self):
        """The ``ScenarioConfig`` field defaults MUST stay unarmed under D-30.

        Two independent things break if a future session "syncs" a field
        default to the ISO override:

        * **Rule 25 / construction.** ``capacity_screen_scarcity_restoration``
          as a field default would make every non-ERCOT config raise at
          construction — the dataclass scalar cannot express the posture.
        * **Cache identity.** All five are ``_CACHE_KEY_OPTIONAL_FIELDS``
          members, which ``cache_key()`` drops against the LIVE field default.
          At unarmed field defaults an armed ERCOT run differs from them and so
          ENTERS the digest, keying distinctly — that is what makes D-30 a
          clean cache epoch (062d440558103f81 -> 8d9ef77edb3e44cb) instead of
          a silent collision in which armed runs re-use pre-arm bundles.
        """
        defaults = ScenarioConfig()
        for field, armed_value in STAGE_B.items():
            assert field in _CACHE_KEY_OPTIONAL_FIELDS, field
            assert getattr(defaults, field) != armed_value, field

    def test_the_d30_arming_moves_the_ercot_forecast_key_and_not_the_pin(self):
        """The declared cache epoch, asserted on the live config.

        The GLOBAL pin is computed on ``ScenarioConfig()`` — no ISO override
        applied — where every stage-B field is still at its unarmed default,
        so the arming cannot move it. The ERCOT forecast lane's own resolved
        default key must move, or armed runs would silently re-use pre-arm
        bundles. Both poles are pinned as literals so the epoch has a test
        naming it (sitting Addendum AQ.2 found it fired undeclared).

        The pre-arm pole is reconstructed by ``dataclasses.replace`` on the
        RESOLVED config — passing the default values to the constructor would
        be re-armed by the seam (the FINDING's inexpressibility, not pinned
        here).
        """
        resolved = apply_iso_scenario_defaults(ScenarioConfig(iso="ERCOT"), "ERCOT")
        for field, value in STAGE_B.items():
            assert getattr(resolved, field) == value, field

        defaults = ScenarioConfig(iso="ERCOT")
        pre_arm = dataclasses.replace(
            resolved, **{f: getattr(defaults, f) for f in STAGE_B}
        )
        assert resolved.cache_key() == "8d9ef77edb3e44cb"
        assert pre_arm.cache_key() == "062d440558103f81"
        assert ScenarioConfig().cache_key() == "603c2498bf71d21d"

    def test_arming_does_not_disturb_the_scarcity_overlay_entry(self):
        """The pre-existing ERCOT override survives alongside the five."""
        overrides = get_iso_config("ERCOT").default_scenario_overrides
        assert overrides.get("scarcity_price_overlay") is True


# --------------------------------------------------------------------------- #
# The backcast lane — untouched by the epoch (rule 22)
# --------------------------------------------------------------------------- #
class TestBackcastLaneUntouched:
    def test_backcast_builder_never_arms_the_five(self):
        """The calibration lane applies no ISO scenario overrides.

        ``scripts/run_calibration_full.py`` / ``pipeline.backcast_config`` read
        ``get_iso_config`` for topology only and never apply
        ``default_scenario_overrides`` — that application lives solely in
        ``runner.run_scenario_iso`` (and the forecast-side export tools). So
        the D-30 arming is invisible here and the ERCOT backcast keeper
        (2026-08-12-run192-arm-coal-peak at declaration) is untouched.
        """
        cfg = _backcast("ERCOT")
        defaults = ScenarioConfig()
        assert cfg.mode == "backcast"
        for field in STAGE_B:
            assert getattr(cfg, field) == getattr(defaults, field), field

    def test_backcast_key_is_byte_stable_across_the_arming(self):
        """No ERCOT backcast cache key is moved by D-30.

        Each field sits at its registered ``_CACHE_KEY_OPTIONAL_FIELDS``
        default in the backcast lane, so it is dropped from the hash and every
        existing ERCOT keeper bundle keys exactly as before.
        """
        cfg = _backcast("ERCOT")
        defaults = ScenarioConfig()
        at_default = dataclasses.replace(
            cfg, **{f: getattr(defaults, f) for f in STAGE_B}
        )
        assert cfg.cache_key() == at_default.cache_key()

    def test_an_armed_backcast_would_move_the_cache_key(self):
        """THE HAZARD THE LANE SEPARATION IS PROTECTING — pinned so it cannot
        regress.

        This is why the backcast lane must keep ignoring
        ``default_scenario_overrides``. Arming the three non-screen stage-B
        fields on a backcast config yields a DISTINCT cache key, which would
        silently orphan every ERCOT backcast keeper's cached results. A future
        session that wires the overrides into the calibration lane fails here.
        (The screen pair is exercised through the construction guard tests
        above; this uses the three fields constructible in any mode.)
        """
        cfg = _backcast("ERCOT")
        armed = dataclasses.replace(
            cfg,
            entry_pipeline_aware_signal=True,
            smr_available_year=2030,
            vre_procurement_additions_enabled=True,
        )
        assert armed.cache_key() != cfg.cache_key()
