"""Generic-improvement coverage sweep across every registered ISO (Wave W1c).

These tests verify that the ERCOT engine improvements that are *already*
ISO-agnostic actually fire for every ISO registered in
``config.iso_configs._ISO_BUILDERS`` -- i.e. that no non-ERCOT ISO is
silently missing the per-ISO config datum a generic capability reads. They
assert configuration coverage, not LP behaviour; the engine logic itself is
exercised by ``test_capacity.py`` / ``test_transmission.py``.

Covered generic improvements (docs/multi-iso/09-ercot-propagation-prompt-pack.md
section 1B, docs/multi-iso/propagation-coverage.md):

* gas-CT peaker as a new-entry candidate (per-ISO interconnection queue cap),
* full thermal economic-retirement screen (every thermal fuel class),
* priced import node / tranches where the ISO has interchange,
* state/regional carbon pricing where the ISO has a program,

plus the ERCOT parity guard: ERCOT carries no import tranches and a zero
state carbon price, matching today's energy-only / electrical-island design.
"""

import pytest

from market_sim.config.constants import (
    IMPORT_TRANCHES,
    IMPORT_ZONE,
    NEW_ENTRY_COSTS,
    QUEUE_CAP_PER_TECH_GW,
    STATE_CARBON_PRICE_BY_ISO,
)
from market_sim.config.iso_configs import _ISO_BUILDERS, get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity import (
    _FOM_MULTIPLIER,
    _NEW_ENTRY_TECHS,
    _RETIREMENT_YEARS,
    _THERMAL_FOM,
)
from market_sim.model.transmission import build_import_generators
from market_sim.policy.carbon import state_carbon_price

# The registered ISOs the sweep is parametrized over.
ALL_ISOS = sorted(_ISO_BUILDERS)

# Every thermal fuel class the economic-retirement screen must cover. These
# mirror docs/multi-iso/09 W1c and the per-fuel ScenarioConfig defaults; the
# screen keys off _THERMAL_FOM, so a fuel missing here would be silently
# un-retirable for *every* ISO.
THERMAL_FUEL_CLASSES = (
    "coal",
    "gas_cc",
    "gas_ct",
    "gas_st",
    "oil",
    "gas_cc_ccs",
    "nuclear",
)


@pytest.mark.parametrize("iso", ALL_ISOS)
def test_iso_config_builds(iso):
    """Every registered ISO produces a valid topology (sanity anchor)."""
    config = get_iso_config(iso)
    assert config.name == iso
    config.validate_topology()


# --- Gas-CT peaker new entry ----------------------------------------------


def test_gas_ct_is_new_entry_candidate():
    """gas_ct is a classic new-entry technology for the entry screen."""
    assert "gas_ct" in _NEW_ENTRY_TECHS


def test_new_entry_costs_cover_gas_classes():
    """The entry screen can cost both gas_cc and gas_ct."""
    assert "gas_cc" in NEW_ENTRY_COSTS
    assert "gas_ct" in NEW_ENTRY_COSTS


@pytest.mark.parametrize("iso", ALL_ISOS)
def test_gas_ct_queue_cap_present(iso):
    """Every ISO has a gas_ct interconnection queue cap (gas_ct can build)."""
    per_tech = QUEUE_CAP_PER_TECH_GW.get(iso)
    assert per_tech is not None, f"{iso} missing from QUEUE_CAP_PER_TECH_GW"
    assert "gas_ct" in per_tech, f"{iso} has no gas_ct queue cap"
    assert per_tech["gas_ct"] >= 0.0


# --- Thermal economic-retirement screen -----------------------------------


@pytest.mark.parametrize("fuel", THERMAL_FUEL_CLASSES)
def test_thermal_fuel_in_retirement_screen(fuel):
    """Each thermal fuel class is screened for economic retirement.

    The screen reads _THERMAL_FOM/_RETIREMENT_YEARS/_FOM_MULTIPLIER, all of
    which name ScenarioConfig fields. A fuel missing any mapping -- or a
    mapping pointing at a non-existent field -- would skip retirement for
    that fuel across every ISO. The thresholds are global per-fuel defaults,
    so coverage is ISO-independent; parametrizing over fuel proves no class
    is silently dropped.
    """
    config = ScenarioConfig(iso="ERCOT")

    assert fuel in _THERMAL_FOM, f"{fuel} not in retirement FOM map"
    assert hasattr(config, _THERMAL_FOM[fuel])

    assert fuel in _RETIREMENT_YEARS, f"{fuel} not in retirement-years map"
    assert hasattr(config, _RETIREMENT_YEARS[fuel])

    assert fuel in _FOM_MULTIPLIER, f"{fuel} not in retirement FOM-mult map"
    assert hasattr(config, _FOM_MULTIPLIER[fuel])


def test_retirement_screen_has_no_extra_fuels():
    """The FOM map is exactly the documented thermal fuel set (no drift)."""
    assert set(_THERMAL_FOM) == set(THERMAL_FUEL_CLASSES)


# --- Priced import/export node --------------------------------------------


@pytest.mark.parametrize("iso", ALL_ISOS)
def test_import_node_resolves_where_imports_configured(iso):
    """Where an ISO has import tranches, its import node resolves.

    An ISO with IMPORT_TRANCHES must also name an IMPORT_ZONE, and
    build_import_generators must materialize one pseudo-generator per
    tranche in that zone. An ISO without tranches builds an empty node
    (ERCOT/MISO) -- a deliberate no-op, not a gap.
    """
    tranches = IMPORT_TRANCHES.get(iso, [])
    generators = build_import_generators(iso)

    if tranches:
        zone = IMPORT_ZONE.get(iso)
        assert zone is not None, f"{iso} has import tranches but no IMPORT_ZONE"
        assert len(generators) == len(tranches)
        assert all(g.zone == zone for g in generators)
        assert all(g.fuel_type == "import" for g in generators)
    else:
        assert generators == []


# --- State/regional carbon pricing ----------------------------------------


@pytest.mark.parametrize("iso", ALL_ISOS)
def test_state_carbon_price_resolves(iso):
    """ISOs with a carbon program price a backcast year; others resolve None.

    CAISO (CARB) and NYISO/NEISO (RGGI) carry measured 2023-2025 allowance
    prices; every other ISO has no program and falls through to None (the
    scenario carbon path), which is the correct energy-market default.
    """
    config = ScenarioConfig(iso=iso)
    price = state_carbon_price(config, 2023)

    if iso in STATE_CARBON_PRICE_BY_ISO:
        assert price is not None and price > 0.0
    else:
        assert price is None


# --- ERCOT parity guard ----------------------------------------------------


def test_ercot_has_no_imports():
    """ERCOT is an electrical island: no import/export node (parity)."""
    assert "ERCOT" not in IMPORT_TRANCHES
    assert "ERCOT" not in IMPORT_ZONE
    assert build_import_generators("ERCOT") == []


def test_ercot_has_zero_state_carbon_price():
    """ERCOT has no state carbon program (energy-only, no RGGI/CARB)."""
    assert "ERCOT" not in STATE_CARBON_PRICE_BY_ISO
    config = ScenarioConfig(iso="ERCOT")
    assert state_carbon_price(config, 2023) is None
