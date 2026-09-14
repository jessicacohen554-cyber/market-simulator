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
colliding with its pre-arm predecessor, and the global pin ``cedadc285f8603b9``
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

**D12-A (owner ruling Q15, r#18 sitting, 2026-08-30;
``docs/handoffs/FINDING-capx-d12a-arming-2026-08-30.md``)** armed a SECOND
pair on the same seam — ``entry_margin_exhaustion`` +
``entry_forward_reserve_leg``, the D12-C confirm-pair's single logical delta,
judged confirming-in-substance per that finding's §4.3 clause — declaring a
new ERCOT forecast-lane epoch ``8d9ef77edb3e44cb`` -> ``68a207068509f2b0``
(probe ``scripts/probes/_d12a_arming_cache_epoch.py``; the registered armed
bundle ``ercot-2021-2025-realized-t1h-d12c-armed``, key ``f061b2646bfaac8b``,
is the record of the armed posture). ``TestD12AArming`` below pins it; the
D-30 pole assertions now strip the D12-A pair first, exactly as the D-30 test
already reconstructs its own pre-arm pole.

Pure config construction — no solve, no data root (the FFR-1D
``test_forecast_mode_guards`` discipline).

ALL THREE POLE LITERALS ADVANCED 2026-09-02 BY A NON-ERCOT CAUSE, and the
narrative literals above are left as the dated measurements they are. The
owner-authorized capx D41 re-identification moved two SHARED ``ScenarioConfig``
defaults onto the NREL ATB 2024 (2026$) basis — ``fixed_om_gas_cc_ccs``
25.0 -> 65.0 and ``ccs_retrofit_capex_kw`` 900.0 -> 1521.4 — and neither is a
``_CACHE_KEY_OPTIONAL_FIELDS`` member, so every config in the program re-keys,
these ERCOT poles included. NOTHING ABOUT THE STAGE-B OR D12-A ARMING CHANGED:
the poles moved together, by the same delta, so every relation this file pins
(armed vs pre-arm distinct, the global pin unmoved BY THIS ARMING) holds exactly
as before. Advances: D12-A armed ``68a207068509f2b0`` -> ``6bb61037c072502d``,
Stage-B armed ``8d9ef77edb3e44cb`` -> ``71f20d708a810f0a``, pre-Stage-B
``062d440558103f81`` -> ``ddeb8a9aaffe1f6b``, global pin ``603c2498bf71d21d``
-> ``cedadc285f8603b9``. Cause block and full blast radius: the pins in
``tests/regression/test_persisted_identity.py`` and the cache-epoch ledger in
``src/market_sim/results/cache.py`` (epoch 2026-09-02).

ALL THREE POLE LITERALS ADVANCED AGAIN 2026-09-03, BY ANOTHER NON-ERCOT CAUSE,
and again the narrative literals above are left as the dated measurements they
are. Capx D44 flipped ``fossil_announced_exits_enabled`` default-on (owner
ruling Q30). That field IS a ``_CACHE_KEY_OPTIONAL_FIELDS`` member, but under
capx D24-R option (b'-1) the key drops it at its FROZEN declaration (``False``,
unedited), so the armed default ENTERS every config's digest and every pole
moves together — by design, and by the same delta, so every relation this file
pins (armed vs pre-arm distinct, the global pin unmoved BY THE STAGE-B/D12-A
ARMINGS, no ERCOT backcast key shifted) again holds exactly as before.
Advances: D12-A armed ``6bb61037c072502d`` -> ``1e1002d480fc180d``, Stage-B
armed ``71f20d708a810f0a`` -> ``ef70a350ac15fd0f``, pre-Stage-B
``ddeb8a9aaffe1f6b`` -> ``11a94474a0c824e3``, global pin ``cedadc285f8603b9``
-> ``4c6b03ae098b6e3e``. Cause block: the pins in
``tests/regression/test_persisted_identity.py``; cache-epoch ledger entry
2026-09-03 in ``src/market_sim/results/cache.py``.

ADVANCED AGAIN 2026-09-05 by capx D60 / owner ruling Q42 — the
``ccs_retrofit_capex_co2_scaling`` default flip, the SECOND declared (b'-1)
flip and again nothing to do with ERCOT's armings. Same reading as the
paragraph above: an unrelated registered field left its declared default, so
every pole here moves together by the same delta and every relation this file
pins holds exactly as before. Advances: D12-A armed ``1e1002d480fc180d`` ->
``b5ab30d0fae9f8a3``, Stage-B armed ``ef70a350ac15fd0f`` ->
``2c3496db2252da1d``, pre-Stage-B ``11a94474a0c824e3`` ->
``2286402c91a65cf5``, global pin ``4c6b03ae098b6e3e`` -> ``e5ecd4105ada3e58``.
Cause block: the pins in ``tests/regression/test_persisted_identity.py``;
cache-epoch ledger entry 2026-09-05 in ``src/market_sim/results/cache.py``.

ADVANCED AGAIN 2026-09-06 by capx D65-B / owner ruling Q47 — and this one is a
DIFFERENT CLASS of cause, so the reading above is extended rather than repeated.
The batch couples a THIRD declared (b'-1) default flip
(``ccs_retrofit_fixed_cost_co2_scaling``, which behaves exactly like the two
flips above) with a plain VALUE re-identification, ``ccs_retrofit_vom_adder``
8.0 -> 2.95 $/MWh 2026$, read off the widened NREL ATB 2024 v4.0.0 extract. A
value change is not a registered-optional field: it has no frozen declaration to
drop at, so it re-keys UNCONDITIONALLY. Every pole here still moves together by
one delta and every relation this file pins still holds — but, unlike the three
earlier advances, so does every explicit-control key elsewhere in the suite.
Still nothing to do with ERCOT's armings. Advances: D12-A armed
``b5ab30d0fae9f8a3`` -> ``95d789d6dfb98831``, Stage-B armed ``2c3496db2252da1d``
-> ``a8fe46584c6ce29b``, pre-Stage-B ``2286402c91a65cf5`` -> ``a99e2cc0bb9707e3``,
global pin ``e5ecd4105ada3e58`` -> ``547053bdfccd4264``. Pre-declared BEFORE the
solve in ``docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md`` §3; cache-epoch
ledger entry 2026-09-06c in ``src/market_sim/results/cache.py``.
"""

from __future__ import annotations

import dataclasses

import pytest

from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.pipeline.backcast_config import backcast_config

ALL_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")

# The five promoted fields and their D-30 values (PREREG §1.6).
STAGE_B = {
    "capacity_screen_unified_lookahead": True,
    "capacity_screen_scarcity_restoration": True,
    "entry_pipeline_aware_signal": True,
    "smr_available_year": 2030,
    "vre_procurement_additions_enabled": True,
}

# The D12-A pair and its Q15 values (the D12-C single logical delta; module
# docstring). Armed AFTER D-30 on the same seam, so the D-30 pole assertions
# strip these fields before evaluating the D-30 epoch.
D12A_PAIR = {
    "entry_margin_exhaustion": True,
    "entry_forward_reserve_leg": True,
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
        here). Since D12-A the live resolution ALSO carries the entry pair,
        so the D-30 poles are evaluated with the pair stripped first — same
        reconstruction, one layer later (``TestD12AArming`` pins the live
        pole).
        """
        live = apply_iso_scenario_defaults(ScenarioConfig(iso="ERCOT"), "ERCOT")
        for field, value in STAGE_B.items():
            assert getattr(live, field) == value, field

        defaults = ScenarioConfig(iso="ERCOT")
        resolved = dataclasses.replace(
            live, **{f: getattr(defaults, f) for f in D12A_PAIR}
        )
        pre_arm = dataclasses.replace(
            resolved, **{f: getattr(defaults, f) for f in STAGE_B}
        )
        assert resolved.cache_key() == "a8fe46584c6ce29b"
        assert pre_arm.cache_key() == "a99e2cc0bb9707e3"
        assert ScenarioConfig().cache_key() == "547053bdfccd4264"

    def test_arming_does_not_disturb_the_scarcity_overlay_entry(self):
        """The pre-existing ERCOT override survives alongside the five."""
        overrides = get_iso_config("ERCOT").default_scenario_overrides
        assert overrides.get("scarcity_price_overlay") is True


# --------------------------------------------------------------------------- #
# The D12-A arming (owner ruling Q15, 2026-08-30)
# --------------------------------------------------------------------------- #
class TestD12AArming:
    """Q15 arms the D12-C entry pair as the ERCOT forecast default.

    Same seam, same discipline as D-30 above: the ``ScenarioConfig`` field
    defaults stay ``False`` (the unarmed pole, so armed runs ENTER the
    digest), the ISO override is the ONLY arming vehicle, and the declared
    epoch (``8d9ef77edb3e44cb`` -> ``68a207068509f2b0``) has a test naming
    it. Probe: ``scripts/probes/_d12a_arming_cache_epoch.py`` (which also
    reproduces the registered armed bundle's T1-H key ``f061b2646bfaac8b``
    from the bare harness construction — the registered
    ``ercot-2021-2025-realized-t1h-d12c-armed`` bundle IS the record of this
    default posture).
    """

    def test_ercot_isoconfig_arms_both(self):
        """The pair moves as ONE unit — the D12-C single logical delta.

        A posture shipping one field without the other was never solved
        (rule 13 ``[R-MEASURED]``): the confirm-pair measured exactly the
        two-field delta, and Q15 armed exactly that.
        """
        overrides = get_iso_config("ERCOT").default_scenario_overrides
        for field, value in D12A_PAIR.items():
            assert overrides.get(field) == value, field

    def test_no_other_iso_arms_the_pair(self):
        """Rule 25 [R-ISO-SCOPE] — Q15's verdict is ERCOT's and only ERCOT's;
        sister-ISO matrix cells stay U (rule 26)."""
        for iso in ALL_ISOS:
            if iso == "ERCOT":
                continue
            overrides = get_iso_config(iso).default_scenario_overrides
            for field in D12A_PAIR:
                assert field not in overrides, (iso, field)

    def test_the_arming_seam_is_the_iso_override_not_the_field_defaults(self):
        """Both field defaults MUST stay ``False`` under Q15 (cache identity:
        each is a ``_CACHE_KEY_OPTIONAL_FIELDS`` member dropped against the
        LIVE field default, so the armed values enter the digest and the
        epoch is a clean re-key instead of a silent collision)."""
        defaults = ScenarioConfig()
        for field, armed_value in D12A_PAIR.items():
            assert field in _CACHE_KEY_OPTIONAL_FIELDS, field
            assert getattr(defaults, field) != armed_value, field

    def test_the_d12a_arming_moves_the_ercot_forecast_key_and_not_the_pin(self):
        """The declared D12-A cache epoch, asserted on the live config.

        The pre-arm pole is the D-30 stage-B pole, reconstructed by
        ``dataclasses.replace`` on the live resolution (constructor-passed
        ``False`` would be an explicit control arm — valid, but not the
        "unset" pole the epoch declares).
        """
        resolved = apply_iso_scenario_defaults(ScenarioConfig(iso="ERCOT"), "ERCOT")
        for field, value in D12A_PAIR.items():
            assert getattr(resolved, field) == value, field

        defaults = ScenarioConfig(iso="ERCOT")
        pre_arm = dataclasses.replace(
            resolved, **{f: getattr(defaults, f) for f in D12A_PAIR}
        )
        assert resolved.cache_key() == "95d789d6dfb98831"
        assert pre_arm.cache_key() == "a8fe46584c6ce29b"
        assert ScenarioConfig().cache_key() == "547053bdfccd4264"

    def test_the_pair_control_arm_is_expressible(self):
        """An explicit both-off caller wins over the override (OVERRIDE-FIX
        precedence) — the D12-C control posture stays reachable."""
        control = apply_iso_scenario_defaults(
            ScenarioConfig(
                iso="ERCOT",
                entry_margin_exhaustion=False,
                entry_forward_reserve_leg=False,
            ),
            "ERCOT",
        )
        assert control.entry_margin_exhaustion is False
        assert control.entry_forward_reserve_leg is False

    def test_disarming_the_reprice_alone_now_raises(self):
        """The dependency wall, pinned deliberately (the FFR-8A pattern).

        Turning off ONLY ``entry_lookahead_reprice`` leaves the ISO override
        arming the pair (both still unset), and ``__post_init__`` refuses
        exhaustion/reserve-leg without the reprice. An ERCOT leg that disarms
        the reprice must disarm the pair WITH it — the caller is told the
        combination is untested instead of silently receiving an armed
        posture riding a dead instrument.
        """
        with pytest.raises(ValueError, match="entry_lookahead_reprice"):
            apply_iso_scenario_defaults(
                ScenarioConfig(iso="ERCOT", entry_lookahead_reprice=False),
                "ERCOT",
            )
        resolved = apply_iso_scenario_defaults(
            ScenarioConfig(
                iso="ERCOT",
                entry_lookahead_reprice=False,
                entry_margin_exhaustion=False,
                entry_forward_reserve_leg=False,
            ),
            "ERCOT",
        )
        assert resolved.entry_lookahead_reprice is False


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
        (2026-08-12-run192-arm-coal-peak at declaration) is untouched. The
        D12-A pair is DOUBLY untouched: not applied here, and backcast-coerced
        off in ``__post_init__`` even where the overrides ARE applied (a
        backcast runs no capacity evolution).
        """
        cfg = _backcast("ERCOT")
        defaults = ScenarioConfig()
        assert cfg.mode == "backcast"
        for field in (*STAGE_B, *D12A_PAIR):
            assert getattr(cfg, field) == getattr(defaults, field), field

    def test_backcast_key_is_byte_stable_across_the_arming(self):
        """No ERCOT backcast cache key is moved by D-30 or D12-A.

        Each field sits at its registered ``_CACHE_KEY_OPTIONAL_FIELDS``
        default in the backcast lane, so it is dropped from the hash and every
        existing ERCOT keeper bundle keys exactly as before.
        """
        cfg = _backcast("ERCOT")
        defaults = ScenarioConfig()
        at_default = dataclasses.replace(
            cfg, **{f: getattr(defaults, f) for f in (*STAGE_B, *D12A_PAIR)}
        )
        assert cfg.cache_key() == at_default.cache_key()

    def test_a_backcast_resolution_coerces_the_pair_off(self):
        """Even a backcast config pushed THROUGH the override seam keeps its
        key: ``with_overrides`` re-runs ``__post_init__``, whose backcast
        coercion turns the applied pair straight back off (the FF-2A
        ``entry_lookahead_reprice`` coercion pattern), so the arming cannot
        reach any backcast posture by any construction path."""
        cfg = _backcast("ERCOT")
        resolved = apply_iso_scenario_defaults(cfg, "ERCOT")
        assert resolved.entry_margin_exhaustion is False
        assert resolved.entry_forward_reserve_leg is False

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
