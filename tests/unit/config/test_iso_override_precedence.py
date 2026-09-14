"""The OVERRIDE-FIX seam: an ISO default fills only a field the caller did NOT pass.

**The defect this pins closed**
(``docs/handoffs/FINDING-ffr-9c-iso-override-precedence-2026-08-12.md``).
``iso_configs.apply_iso_scenario_defaults`` used to decide "the caller left this
field unset" by comparing the caller's value against the ``ScenarioConfig``
field default. Every promotable flag defaults ``False``/``None``, so *the OFF
value was exactly the value that could not be requested*: an explicit
``entry_pipeline_aware_signal=False`` was indistinguishable from absence and was
silently re-armed. A control arm for any ISO-armed flag was therefore
INEXPRESSIBLE through the config path, in ERCOT (D-30 stage B, five flags) and
MISO (D-29) alike — and it failed silently, so a lane could believe it solved a
control arm, register the bundle and quote the number (the FFR-2E defect class
one layer up).

The remedy is FINDING §4 **remedy 2**: ``ScenarioConfig`` records which fields
its caller actually passed (``scenarios.explicitly_set_fields``) and the seam
consults that record instead of guessing from values. Remedy 3 (raise) was
rejected as a destination — a model whose control arm is an error cannot run the
A/B discipline.

What these tests hold, in both directions:

* **the fix** — an explicit default-valued argument now WINS, for every field
  every ISO promotes, so a control arm is expressible;
* **byte-stability** — a caller that passes nothing still gets the full ISO
  posture (ERCOT's five stage-B flags plus the D12-A entry pair armed at
  ``68a207068509f2b0`` — the pole was ``8d9ef77edb3e44cb`` until the Q15
  arming of 2026-08-30 moved it, see
  ``docs/handoffs/FINDING-capx-d12a-arming-2026-08-30.md`` — the global
  pin unmoved BY THE FIX: ``cedadc285f8603b9`` when this was written,
  ``4c6b03ae098b6e3e`` since capx D44's 2026-09-03 flip of an unrelated
  field), and a non-default explicit value still wins as it always did. The
  fix is a strict NARROWING;
* **cache-key invisibility** — the record is a NON-FIELD attribute, so it can
  never reach ``asdict()``/``cache_key()`` and rule 28's ledger duty does not
  arise;
* **the fail-safe** — an untracked copy (bare ``dataclasses.replace``, an
  unpickled config) degrades to the PRE-FIX value comparison rather than losing
  its ISO defaults wholesale.

Pure config construction — no solve, no data root (the FFR-1D
``test_forecast_mode_guards`` discipline).
"""

from __future__ import annotations

import copy
import dataclasses
import pickle

import pytest

from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.scenarios import ScenarioConfig, explicitly_set_fields

ALL_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")

# The D-30 stage-B five and their armed values (PREREG §1.6), plus the pinned
# poles the epoch declaration rests on.
STAGE_B = {
    "capacity_screen_unified_lookahead": True,
    "capacity_screen_scarcity_restoration": True,
    "entry_pipeline_aware_signal": True,
    "smr_available_year": 2030,
    "vre_procurement_additions_enabled": True,
}
# The LIVE resolved ERCOT forecast-lane default key. D-30 declared it at
# "8d9ef77edb3e44cb"; the D12-A arming (owner ruling Q15, 2026-08-30 —
# entry_margin_exhaustion + entry_forward_reserve_leg, epoch probe
# scripts/probes/_d12a_arming_cache_epoch.py) moved it here. This module pins
# the CURRENT pole; the per-epoch genealogy lives in
# tests/unit/config/test_ercot_stageb_arming.py, which reconstructs each
# prior pole explicitly.
# ADVANCED 2026-09-02, 68a207068509f2b0 -> 6bb61037c072502d, by a NON-ERCOT
# cause: the owner-authorized capx D41 re-identification of the shared defaults
# fixed_om_gas_cc_ccs (25.0 -> 65.0) and ccs_retrofit_capex_kw (900.0 -> 1521.4)
# onto the NREL ATB 2024 (2026$) basis. Neither is a _CACHE_KEY_OPTIONAL_FIELDS
# member, so every config re-keys and this pole moved with the global pin — the
# D12-A arming itself is untouched, and the "pole unmoved by the fix" property
# this file pins holds exactly as before. Cause block:
# tests/regression/test_persisted_identity.py.
# ADVANCED AGAIN 2026-09-03, 6bb61037c072502d -> 1e1002d480fc180d, by another
# NON-ERCOT cause: capx D44's declared default flip of
# fossil_announced_exits_enabled (owner ruling Q30). It IS registered, but the
# key drops it at its FROZEN "False" declaration (capx D24-R (b'-1)), so the
# armed default enters every digest and this pole moves with the global pin —
# the D12-A arming and the "pole unmoved by the fix" property are untouched.
# ADVANCED AGAIN 2026-09-05, 1e1002d480fc180d -> b5ab30d0fae9f8a3, by a third
# NON-ERCOT cause of the same class: capx D60's declared default flip of
# ccs_retrofit_capex_co2_scaling (owner ruling Q42), the SECOND entry in
# _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS. Registered, dropped at its FROZEN
# "False" declaration, so the armed default enters every digest and this pole
# moves with the global pin — the D12-A arming and the "pole unmoved by the
# fix" property are untouched.
# ADVANCED AGAIN 2026-09-06, b5ab30d0fae9f8a3 -> 95d789d6dfb98831, by a FOURTH
# non-ERCOT cause — and the first of a different CLASS. capx D65-B (owner
# ruling Q47) arms ccs_retrofit_fixed_cost_co2_scaling as a declared (b'-1)
# default flip (the THIRD _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS entry, same
# mechanic as the three causes above) COUPLED with a plain VALUE change,
# ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh 2026$, re-identified off the ATB
# 2024 v4.0.0 basis. The value change is NOT a registered-optional field, so it
# has no frozen declaration to drop at and re-keys unconditionally — which is
# why this advance also moves keys the three earlier flips left alone.
# The D12-A arming and the 'pole unmoved by the fix' property are untouched.
# Pre-declared before the solve: docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md
# §3; cache-epoch ledger entry 2026-09-06c in src/market_sim/results/cache.py.
ERCOT_ARMED_KEY = "95d789d6dfb98831"
GLOBAL_PINNED_KEY = "547053bdfccd4264"

FIELD_DEFAULTS = {
    f.name: getattr(ScenarioConfig(), f.name)
    for f in dataclasses.fields(ScenarioConfig)
}


def _promoted() -> list[tuple[str, str, object]]:
    """Every (iso, field, iso_value) an ISO promotes through its overrides."""
    rows: list[tuple[str, str, object]] = []
    for iso in ALL_ISOS:
        for field, value in (
            get_iso_config(iso).default_scenario_overrides or {}
        ).items():
            rows.append((iso, field, value))
    return rows


PROMOTED = _promoted()
PROMOTED_IDS = [f"{iso}-{field}" for iso, field, _ in PROMOTED]

# Fields that cannot be turned off ALONE. ``__post_init__`` refuses
# ``capacity_screen_scarcity_restoration`` without
# ``capacity_screen_unified_lookahead`` (FFR-8A: the restoration extends the
# unified lookahead object's armed stack), so switching one off while the ISO
# override still arms the other is an illegal posture and RAISES. That raise is
# correct and is the loud half of the fix — the caller is told the combination
# is untested instead of silently receiving the armed posture. The control arm
# for this pair is therefore both-off, which is how it is exercised here and in
# ``test_ercot_screen_pair_control_arm_is_both_off``.
_CO_VARYING: dict[str, tuple[str, ...]] = {
    "capacity_screen_unified_lookahead": ("capacity_screen_scarcity_restoration",),
    "capacity_screen_scarcity_restoration": ("capacity_screen_unified_lookahead",),
}


# --------------------------------------------------------------------------- #
# 1. The fix — an explicit caller value wins even at the field default
# --------------------------------------------------------------------------- #
class TestExplicitDefaultValuedArgumentWins:
    @pytest.mark.parametrize(("iso", "field", "iso_value"), PROMOTED, ids=PROMOTED_IDS)
    def test_explicit_default_value_is_not_re_armed(self, iso, field, iso_value):
        """THE FIX, for every field every ISO promotes.

        Passing the field at its ``ScenarioConfig`` default is a control arm and
        must survive resolution. Before the fix each of these resolved to
        *iso_value* instead.
        """
        default = FIELD_DEFAULTS[field]
        assert default != iso_value, (
            f"{iso}.{field}: the ISO override equals the field default, so this "
            "row cannot discriminate — the override is a no-op and should be "
            "dropped from default_scenario_overrides."
        )
        passed = {field: default}
        # A field with a gated partner is turned off WITH it (see _CO_VARYING).
        passed.update({p: FIELD_DEFAULTS[p] for p in _CO_VARYING.get(field, ())})
        cfg = apply_iso_scenario_defaults(ScenarioConfig(iso=iso, **passed), iso)
        assert getattr(cfg, field) == default

    def test_ercot_screen_pair_control_arm_is_both_off(self):
        """``__post_init__`` refuses restoration without lookahead, so the
        screen-pair control arm is both-off — and both must stay off."""
        cfg = apply_iso_scenario_defaults(
            ScenarioConfig(
                iso="ERCOT",
                capacity_screen_unified_lookahead=False,
                capacity_screen_scarcity_restoration=False,
            ),
            "ERCOT",
        )
        assert cfg.capacity_screen_unified_lookahead is False
        assert cfg.capacity_screen_scarcity_restoration is False

    def test_turning_off_half_the_screen_pair_RAISES(self):
        """A real behaviour change, pinned deliberately.

        Turning off ONLY the lookahead leaves the ISO override arming the
        restoration (it is still unset), and ``__post_init__`` refuses
        restoration-without-lookahead. Before the fix this posture was
        unreachable — the seam re-armed both — so the raise is new. It is the
        LOUD half of the remedy and strictly better than the alternative: the
        caller is told the combination is untested (FFR-8A) instead of silently
        receiving the armed posture it asked to turn off.
        """
        with pytest.raises(ValueError, match="requires capacity_screen_unified"):
            apply_iso_scenario_defaults(
                ScenarioConfig(iso="ERCOT", capacity_screen_unified_lookahead=False),
                "ERCOT",
            )

    def test_a_full_ercot_stage_b_control_arm_is_expressible(self):
        """The whole point of the lane: the pre-epoch ERCOT posture is
        reachable through the config path, all five flags at once."""
        control = apply_iso_scenario_defaults(
            ScenarioConfig(iso="ERCOT", **{f: FIELD_DEFAULTS[f] for f in STAGE_B}),
            "ERCOT",
        )
        assert {f: getattr(control, f) for f in STAGE_B} == {
            f: FIELD_DEFAULTS[f] for f in STAGE_B
        }

    def test_positional_construction_is_recorded(self):
        """Positional args are tracked too — the record is built from BOTH the
        positional slots and the kwargs, not kwargs alone."""
        first = dataclasses.fields(ScenarioConfig)[0].name
        cfg = ScenarioConfig(FIELD_DEFAULTS[first])
        assert explicitly_set_fields(cfg) == frozenset({first})


# --------------------------------------------------------------------------- #
# 2. Byte-stability — the fix is a strict narrowing
# --------------------------------------------------------------------------- #
class TestUnsetStillArms:
    @pytest.mark.parametrize(("iso", "field", "iso_value"), PROMOTED, ids=PROMOTED_IDS)
    def test_a_caller_that_passes_nothing_still_gets_the_iso_posture(
        self, iso, field, iso_value
    ):
        """Makes the test above non-vacuous: unset resolves to the ISO value."""
        cfg = apply_iso_scenario_defaults(ScenarioConfig(iso=iso), iso)
        assert getattr(cfg, field) == iso_value

    def test_no_arg_ercot_still_arms_all_five_stage_b_flags(self):
        resolved = apply_iso_scenario_defaults(ScenarioConfig(iso="ERCOT"), "ERCOT")
        assert {f: getattr(resolved, f) for f in STAGE_B} == STAGE_B

    def test_the_declared_ercot_epoch_pole_is_unmoved(self):
        """The LIVE declared armed pole (D12-A since 2026-08-30) and the
        global pin both survive the fix."""
        resolved = apply_iso_scenario_defaults(ScenarioConfig(iso="ERCOT"), "ERCOT")
        assert resolved.cache_key() == ERCOT_ARMED_KEY
        assert ScenarioConfig().cache_key() == GLOBAL_PINNED_KEY

    @pytest.mark.parametrize(("iso", "field", "iso_value"), PROMOTED, ids=PROMOTED_IDS)
    def test_a_non_default_explicit_value_still_wins(self, iso, field, iso_value):
        """Unchanged by the fix — this half always worked, which is why the
        seam looked correct in use."""
        probe = _distinct_value(FIELD_DEFAULTS[field], iso_value)
        if probe is None:
            pytest.skip(f"{field}: no safe third value for this type")
        cfg = apply_iso_scenario_defaults(
            ScenarioConfig(iso=iso, **{field: probe}), iso
        )
        assert getattr(cfg, field) == probe


def _distinct_value(default, iso_value):
    """A legal value distinct from BOTH the field default and the ISO value."""
    if isinstance(default, bool) or isinstance(iso_value, bool):
        return None  # a bool has only two values; both are already taken
    if isinstance(iso_value, (int, float)) and not isinstance(iso_value, bool):
        return type(iso_value)(iso_value) + type(iso_value)(7)
    if default is None and isinstance(iso_value, int):
        return iso_value + 7
    return None


# --------------------------------------------------------------------------- #
# 3. Cache-key invisibility — the record is a NON-FIELD attribute (rule 28)
# --------------------------------------------------------------------------- #
class TestTrackingRecordIsInvisibleToTheDigest:
    ATTR = "_explicitly_set_fields"

    def test_absent_from_dataclass_fields(self):
        assert self.ATTR not in {f.name for f in dataclasses.fields(ScenarioConfig)}

    def test_absent_from_asdict(self):
        cfg = ScenarioConfig(iso="ERCOT", entry_pipeline_aware_signal=False)
        assert self.ATTR not in dataclasses.asdict(cfg)

    def test_absent_from_non_default_values_and_yaml(self, tmp_path):
        cfg = ScenarioConfig(iso="ERCOT", entry_pipeline_aware_signal=False)
        assert self.ATTR not in cfg._non_default_values()
        path = tmp_path / "full.yaml"
        cfg.to_yaml_full(path)
        assert self.ATTR not in path.read_text()

    def test_cache_key_is_blind_to_the_record(self):
        """Two configs with the SAME field values but DIFFERENT records hash
        identically — the record cannot fork a cache key."""
        explicit = ScenarioConfig(iso="ERCOT", entry_pipeline_aware_signal=False)
        unset = ScenarioConfig(iso="ERCOT")
        assert explicitly_set_fields(explicit) != explicitly_set_fields(unset)
        assert explicit.cache_key() == unset.cache_key()

    def test_every_field_is_init_true(self):
        """The record maps positional args by field order, which is only sound
        while every field is ``init=True``."""
        assert all(f.init for f in dataclasses.fields(ScenarioConfig))


# --------------------------------------------------------------------------- #
# 4. Copy semantics — with_overrides carries the record, replace/pickle degrade
# --------------------------------------------------------------------------- #
class TestCopySemantics:
    def test_with_overrides_unions_the_record(self):
        cfg = ScenarioConfig(iso="ERCOT").with_overrides(smr_available_year=None)
        assert explicitly_set_fields(cfg) == frozenset({"iso", "smr_available_year"})

    def test_with_overrides_preserves_a_control_arm_through_resolution(self):
        """``runner.run_scenario_iso`` re-binds ``iso`` and resolves the policy
        bundle through ``with_overrides`` BEFORE ``apply_iso_scenario_defaults``
        — a control arm must survive that trip."""
        cfg = ScenarioConfig(iso="ERCOT", entry_pipeline_aware_signal=False)
        rebound = cfg.with_overrides(iso="ERCOT")
        assert (
            apply_iso_scenario_defaults(rebound, "ERCOT").entry_pipeline_aware_signal
            is False
        )

    def test_bare_replace_degrades_to_the_pre_fix_comparison(self):
        """FAIL-SAFE. ``dataclasses.replace`` re-invokes ``__init__`` with EVERY
        field, so the record is genuinely ambiguous and is recorded as unknown.
        Unknown must fall back to the pre-fix VALUE comparison (the ISO default
        applies), never to "nothing was set" and never to "everything was set" —
        the latter would silently strip every ISO default."""
        cfg = dataclasses.replace(ScenarioConfig(iso="ERCOT"), hours=8760)
        assert explicitly_set_fields(cfg) is None
        resolved = apply_iso_scenario_defaults(cfg, "ERCOT")
        assert {f: getattr(resolved, f) for f in STAGE_B} == STAGE_B

    def test_an_unpickled_config_reads_unknown_and_still_resolves(self):
        restored = pickle.loads(pickle.dumps(ScenarioConfig(iso="ERCOT")))
        assert explicitly_set_fields(restored) in (None, frozenset({"iso"}))
        resolved = apply_iso_scenario_defaults(restored, "ERCOT")
        assert {f: getattr(resolved, f) for f in STAGE_B} == STAGE_B

    def test_deepcopy_carries_the_record(self):
        cfg = ScenarioConfig(iso="ERCOT", entry_pipeline_aware_signal=False)
        assert explicitly_set_fields(copy.deepcopy(cfg)) == explicitly_set_fields(cfg)


# --------------------------------------------------------------------------- #
# 5. No call site depends on the silent re-arming
# --------------------------------------------------------------------------- #
class TestNoEntryPointDependsOnSilentReArming:
    """``scripts/run_full_horizon.py::reference_config`` forwarded
    ``miso_rps_compliance_regions``/``miso_clean_tier_rows`` as mirrored
    literals (``= False``), which the pre-fix seam re-armed and the post-fix
    seam would have honoured — silently un-arming owner decisions D-26/D-29 in
    exactly the T1-F legs that runner launches. Both are now ``None``-sentinels
    (the idiom that file already uses for the D-1/D-2 arms). Pinned so the
    mirrored-literal shape cannot come back."""

    def test_reference_config_leaves_the_miso_row_gates_unset(self):
        rfh = _load_run_full_horizon()
        cfg = rfh.reference_config(
            iso="MISO", start_year=2031, end_year=2032, cmc=False
        )
        record = explicitly_set_fields(cfg)
        assert record is not None
        assert "miso_rps_compliance_regions" not in record
        assert "miso_clean_tier_rows" not in record

    def test_a_no_flag_miso_forecast_leg_still_solves_the_armed_posture(self):
        rfh = _load_run_full_horizon()
        cfg = rfh.reference_config(
            iso="MISO", start_year=2031, end_year=2032, cmc=False
        )
        resolved = apply_iso_scenario_defaults(cfg, "MISO")
        assert resolved.miso_rps_compliance_regions is True
        assert resolved.miso_clean_tier_rows is True

    def test_an_explicit_off_leg_is_now_expressible(self):
        rfh = _load_run_full_horizon()
        cfg = rfh.reference_config(
            iso="MISO",
            start_year=2031,
            end_year=2032,
            cmc=False,
            miso_rps_compliance_regions=False,
            miso_clean_tier_rows=False,
        )
        resolved = apply_iso_scenario_defaults(cfg, "MISO")
        assert resolved.miso_rps_compliance_regions is False
        assert resolved.miso_clean_tier_rows is False


def _load_run_full_horizon():
    """Import the runner by path (it is a script, not a package module)."""
    import importlib.util

    from tests.helpers import REPO_ROOT

    path = f"{REPO_ROOT}/scripts/run_full_horizon.py"
    spec = importlib.util.spec_from_file_location("run_full_horizon_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
