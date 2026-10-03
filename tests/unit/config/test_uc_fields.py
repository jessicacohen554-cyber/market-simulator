"""Registry behaviour of the ``unit_commitment_milp`` fields (docs/testing.md "one rule").

Properties, never literals: an explicit default hashes like an absent one, an
armed gate moves the key, every declared refusal raises, and every field is
registered at its declared default.
"""

from __future__ import annotations

import pytest

from market_sim.config import scenarios as sc
from market_sim.config.scenarios import ScenarioConfig

UC_FIELDS = (
    "unit_commitment_milp",
    "uc_window_hours",
    "uc_lookahead_hours",
    "uc_mip_rel_gap",
    "uc_window_time_limit_s",
    "uc_integer_scope",
    "uc_noload_source",
    "uc_boundary_mode",
    "uc_prefixing",
)


def test_every_uc_field_is_registered_at_its_default():
    for name in UC_FIELDS:
        assert name in sc._CACHE_KEY_OPTIONAL_FIELDS
        assert name in sc._CACHE_KEY_OPTIONAL_FIELD_DEFAULTS
        assert sc.TIER_TAGS[name] == 1


def test_explicit_default_hashes_like_absent_and_armed_moves():
    base = ScenarioConfig(iso="NEISO", mode="backcast")
    explicit = ScenarioConfig(
        iso="NEISO", mode="backcast", unit_commitment_milp=False, uc_window_hours=24
    )
    assert base.cache_key() == explicit.cache_key()
    armed = base.with_overrides(unit_commitment_milp=True)
    assert armed.cache_key() != base.cache_key()
    assert armed.with_overrides(uc_lookahead_hours=24).cache_key() != armed.cache_key()


@pytest.mark.parametrize(
    "stack",
    [
        dict(caiso_ra_mustoffer=True, iso="CAISO"),
        dict(ercot_gas_commitment_bridge=True, iso="ERCOT"),
        dict(nyiso_gas_commitment_bridge=True, iso="NYISO"),
        dict(spp_gas_commitment_bridge=True, iso="SPP"),
        dict(pjm_gas_commitment_bridge=True, iso="PJM"),
        dict(miso_gas_ecomin_online_floor=True, iso="MISO"),
        dict(ercot_commitment_posture=True, iso="ERCOT"),
        dict(miso_commitment_posture=True, iso="MISO"),
        dict(spp_commitment_posture=True, iso="SPP"),
    ],
)
def test_rule_19_stacks_are_refused(stack):
    iso = stack.pop("iso")
    mode = stack.pop("mode", "forecast")
    with pytest.raises(ValueError, match="REPLACES"):
        ScenarioConfig(iso=iso, mode=mode, unit_commitment_milp=True, **stack)


@pytest.mark.parametrize(
    "bad",
    [
        dict(uc_window_hours=0),
        dict(uc_window_hours=24, uc_lookahead_hours=8760),
        dict(uc_mip_rel_gap=0.0),
        dict(uc_window_time_limit_s=0.0),
        dict(uc_integer_scope="all"),
        dict(uc_noload_source="table"),
        dict(uc_boundary_mode="cyclic"),
    ],
)
def test_declared_value_sets_are_enforced(bad):
    with pytest.raises(ValueError):
        ScenarioConfig(iso="NEISO", unit_commitment_milp=True, **bad)


def test_values_are_not_checked_when_the_gate_is_off():
    ScenarioConfig(iso="NEISO", uc_integer_scope="whatever")


def test_refusal_tuples_are_the_whole_set():
    """Every UC_REFUSED_ALWAYS member is a real field and is refused; the ruling
    tuple is empty at birth; the D-5 cases are not refused (owner card)."""
    import dataclasses

    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    assert len(sc.UC_REFUSED_ALWAYS) >= 15
    for name, _what in sc.UC_REFUSED_ALWAYS:
        assert name in names
        iso = {
            "caiso": "CAISO",
            "ercot": "ERCOT",
            "nyiso": "NYISO",
            "spp": "SPP",
            "pjm": "PJM",
            "miso": "MISO",
        }[name.split("_")[0]]
        with pytest.raises(ValueError, match="REPLACES"):
            ScenarioConfig(
                iso=iso, mode="backcast", unit_commitment_milp=True, **{name: True}
            )
    assert sc.UC_REFUSED_BY_RULING == ()
    ScenarioConfig(
        iso="PJM", mode="backcast", unit_commitment_milp=True, cc_mustrun_per_plant=True
    )
    ScenarioConfig(
        iso="SOCO",
        mode="backcast",
        unit_commitment_milp=True,
        soco_gas_st_campaign_commitment=True,
    )
