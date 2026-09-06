"""miso-175 ``miso_seam_envelope_hour_ending_key`` — config surface guards.

Hermetic (no data reads): the field's default, its drop-at-default cache-key
registration (the nyiso-119 discipline) and the pinned global default key.
The data-backed rotation behaviour is covered in
``tests/iso/miso/test_miso_seam_flow_limit.py::TestSeamEnvelopeHourEndingKey``.
"""

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    TIER_TAGS,
    ScenarioConfig,
)

FIELD = "miso_seam_envelope_hour_ending_key"


def test_default_is_off() -> None:
    """The repair is opt-in: replay fidelity for pre-miso-175 bundles."""
    assert ScenarioConfig().miso_seam_envelope_hour_ending_key is False


def test_registered_drop_at_default() -> None:
    """Registered in both cache-key ledgers at its merge-time default."""
    assert FIELD in _CACHE_KEY_OPTIONAL_FIELDS
    assert _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[FIELD] == "False"
    assert TIER_TAGS[FIELD] == 1  # structural flag, not a numeric parameter


def test_armed_run_keys_distinctly_and_default_key_is_unmoved() -> None:
    """Registered at False: the pinned default key holds; armed hashes apart."""
    default = ScenarioConfig()
    armed = ScenarioConfig(miso_seam_envelope_hour_ending_key=True)
    # The GLOBAL default forecast key. ADVANCED e5ecd4105ada3e58 ->
    # 547053bdfccd4264 on 2026-09-06 by capx D65-B (owner ruling Q47): the
    # COUPLED arming of ccs_retrofit_fixed_cost_co2_scaling (Act A, a declared
    # (b'-1) default flip) with ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh 2026$
    # (Act B, re-identified off the widened ATB extract). Act B is NOT a
    # _CACHE_KEY_OPTIONAL_FIELDS member, so it has no drop value and re-keys
    # unconditionally. Pre-declared BEFORE the solve in
    # docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md §3; cache-epoch ledger
    # entry 2026-09-06c in src/market_sim/results/cache.py. Nothing about THIS
    # field moved — the pin advances because the global default did.
    assert default.cache_key() == "547053bdfccd4264"
    assert armed.cache_key() != default.cache_key()
