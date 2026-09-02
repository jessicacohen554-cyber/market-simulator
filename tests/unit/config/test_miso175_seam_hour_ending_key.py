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
    assert default.cache_key() == "cedadc285f8603b9"
    assert armed.cache_key() != default.cache_key()
