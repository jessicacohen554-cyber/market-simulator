"""``--set FIELD=VALUE`` must beat an ISO's ``default_scenario_overrides``.

capx D60-R4 (2026-09-06). ``run_full_horizon.apply_set_overrides`` returns a
config that is still UNRESOLVED — ``iso_configs.apply_iso_scenario_defaults``
runs later, inside ``runner.run_scenario_iso``. That resolver only fills a field
"the caller did not pass", and it reads "did not pass" from
:func:`market_sim.config.scenarios.explicitly_set_fields` first (the
OVERRIDE-FIX of 2026-08-13, which exists precisely so a control arm for an
ISO-armed flag is expressible).

A bare ``dataclasses.replace`` destroys that record — it re-invokes ``__init__``
with every field, which is indistinguishable from a caller who set everything —
so the resolver falls back to comparing values, an explicit ``False`` equals the
ScenarioConfig field default, and the ISO default silently re-arms the flag.
Before the repair a PJM leg asking for all three of that ISO's armed gates OFF
resolved to the ARM's own cache key. These tests pin the repair.
"""

from __future__ import annotations

import pytest

from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from scripts.run_full_horizon import apply_set_overrides, parse_set_overrides

PJM_GATES = (
    "pjm_demand_response_supply",
    "pjm_accreditation_design_vintage",
    "capacity_market_supply_clearing_by_iso",
)


def test_pjm_arms_the_three_gates_by_default() -> None:
    """The premise: PJM's ISO config arms all three, so the test has an object."""
    armed = get_iso_config("PJM").default_scenario_overrides or {}
    assert set(PJM_GATES) <= set(armed), armed


@pytest.mark.parametrize("gate", PJM_GATES)
def test_set_off_survives_the_iso_default(gate: str) -> None:
    """An explicit OFF via ``--set`` must still be OFF after ISO resolution."""
    off = "null" if gate == "capacity_market_supply_clearing_by_iso" else "false"
    overridden = apply_set_overrides(
        ScenarioConfig(iso="PJM", mode="forecast"),
        parse_set_overrides([f"{gate}={off}"]),
    )
    resolved = apply_iso_scenario_defaults(overridden, "PJM")
    assert not getattr(resolved, gate), (
        f"{gate} was re-armed by PJM's default_scenario_overrides despite an "
        "explicit --set; a control arm is inexpressible (rule 24 [R-REGISTRY])"
    )


def test_unset_gates_still_take_the_iso_default() -> None:
    """The repair is a strict narrowing: an unset field still gets the ISO default."""
    resolved = apply_iso_scenario_defaults(
        ScenarioConfig(iso="PJM", mode="forecast"), "PJM"
    )
    for gate in PJM_GATES:
        assert getattr(resolved, gate), gate


def test_set_and_unset_gates_coexist() -> None:
    """One gate turned off does not disarm the other two."""
    overridden = apply_set_overrides(
        ScenarioConfig(iso="PJM", mode="forecast"),
        parse_set_overrides(["pjm_demand_response_supply=false"]),
    )
    resolved = apply_iso_scenario_defaults(overridden, "PJM")
    assert not resolved.pjm_demand_response_supply
    assert resolved.pjm_accreditation_design_vintage
    assert resolved.capacity_market_supply_clearing_by_iso == {"PJM": True}
