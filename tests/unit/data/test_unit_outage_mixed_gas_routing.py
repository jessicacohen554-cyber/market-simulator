"""miso-200: the multi-gas-group routing gate in ``_resolve_unit_group``.

The defect (FINDING-miso200): ``_resolve_unit_group`` short-circuits on the
FACILITY's group whenever that group is a qualifying non-COAL one, but the
facility group is built LAST-WRITER-WINS over the fleet rows, so at a facility
carrying two or more model gas bins every unit is handed to whichever bin came
last. ``ScenarioConfig.unit_outage_mixed_gas_routing`` skips the short-circuit
there and falls through to the resolver's own per-unit ``unitType`` routing.

These tests pin the four things the repair must be: CORRECT at a mixed facility,
BYTE-INERT at a single-gas facility, ORDERED AFTER the coal and liquid-CT
guards, and CACHE-KEY NEUTRAL while off.
"""

from __future__ import annotations

import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.outages import (
    unit_outage_csv_for_iso,
    unit_outage_maxgen_csv_for_iso,
)
from scripts.data.derive_campd_unit_outages import (
    _is_multi_gas_facility,
    _resolve_unit_group,
)

# The measured MISO cell (census _miso200_outage_routing_phase0.json):
# Ninemile Point 1403 carries ST_GAS 1,465.4 MW + CC_REGULAR 649.5 MW, the last
# fleet writer is CC_REGULAR, and units 4/5 are "Tangentially-fired" boilers.
MIXED = {"CC_REGULAR", "ST_GAS"}
SINGLE_CC = {"CC_REGULAR"}
SINGLE_ST = {"ST_GAS"}


class TestMultiGasDetector:
    def test_two_gas_bins_is_multi(self):
        assert _is_multi_gas_facility(MIXED)

    def test_one_gas_bin_is_not_multi(self):
        assert not _is_multi_gas_facility(SINGLE_CC)
        assert not _is_multi_gas_facility(SINGLE_ST)

    def test_gas_bin_plus_non_gas_bins_is_not_multi(self):
        # A CC plant that also carries a peaker and a coal bin still has ONE
        # gas BIN, so the short-circuit's premise holds and nothing changes.
        assert not _is_multi_gas_facility({"CC_REGULAR", "CT_PEAKER", "COAL"})

    def test_chp_variants_count(self):
        assert _is_multi_gas_facility({"CC_CHP", "ST_CHP"})


class TestMixedFacilityRouting:
    """The 1403 cell: the boilers must reach the bin that actually holds them."""

    @pytest.mark.parametrize("unit_type", ["Tangentially-fired", "Dry bottom wall-fired boiler"])
    def test_steam_boiler_misroutes_when_off(self, unit_type):
        assert (
            _resolve_unit_group(False, unit_type, MIXED, "CC_REGULAR", "Pipeline Natural Gas")
            == "CC_REGULAR"
        )

    @pytest.mark.parametrize("unit_type", ["Tangentially-fired", "Dry bottom wall-fired boiler"])
    def test_steam_boiler_routes_to_st_gas_when_on(self, unit_type):
        assert (
            _resolve_unit_group(
                False,
                unit_type,
                MIXED,
                "CC_REGULAR",
                "Pipeline Natural Gas",
                mixed_gas_routing=True,
            )
            == "ST_GAS"
        )

    def test_combined_cycle_unit_is_unmoved_by_the_gate(self):
        """The repair must not disturb the units the short-circuit got right."""
        for flag in (False, True):
            assert (
                _resolve_unit_group(
                    False,
                    "Combined cycle",
                    MIXED,
                    "CC_REGULAR",
                    "Pipeline Natural Gas",
                    mixed_gas_routing=flag,
                )
                == "CC_REGULAR"
            )

    def test_steam_host_routes_to_st_chp_when_that_is_the_bin(self):
        assert (
            _resolve_unit_group(
                False,
                "Tangentially-fired",
                {"CC_CHP", "ST_CHP"},
                "CC_CHP",
                "Pipeline Natural Gas",
                mixed_gas_routing=True,
            )
            == "ST_CHP"
        )


class TestByteInertWhereThePremiseHolds:
    """A single-gas facility must be untouched -- that is the whole scope."""

    @pytest.mark.parametrize(
        "unit_type", ["Combined cycle", "Tangentially-fired", "Cyclone boiler"]
    )
    @pytest.mark.parametrize("groups,fac", [(SINGLE_CC, "CC_REGULAR"), (SINGLE_ST, "ST_GAS")])
    def test_single_gas_group_identical_on_and_off(self, unit_type, groups, fac):
        off = _resolve_unit_group(False, unit_type, groups, fac, "Pipeline Natural Gas")
        on = _resolve_unit_group(
            False, unit_type, groups, fac, "Pipeline Natural Gas", mixed_gas_routing=True
        )
        assert off == on == fac


class TestGuardOrdering:
    """The gate must sit BEHIND the two guards that already precede it."""

    def test_coal_still_wins_at_a_mixed_facility(self):
        assert (
            _resolve_unit_group(
                True, "Cyclone boiler", MIXED | {"COAL"}, "CC_REGULAR", "Coal",
                mixed_gas_routing=True,
            )
            == "COAL"
        )

    def test_liquid_only_ct_still_drops_at_a_mixed_facility(self):
        # neiso-99's guard runs first, so an oil-only peaker never becomes a
        # member of a sibling gas bin just because the facility is mixed.
        assert (
            _resolve_unit_group(
                False, "Combustion turbine", MIXED, "CC_REGULAR", "Diesel Oil",
                mixed_gas_routing=True,
            )
            == "CT_PEAKER"
        )


class TestPathSelection:
    def test_off_returns_the_incumbent_extract(self):
        assert unit_outage_csv_for_iso("MISO").name == "campd-unit-outages-MISO.csv"
        assert (
            unit_outage_maxgen_csv_for_iso("MISO").name
            == "campd-unit-outages-maxgen-MISO.csv"
        )

    def test_on_selects_the_companion_when_it_exists(self):
        p = unit_outage_csv_for_iso("MISO", True)
        # Falls back to the incumbent when the companion has not been derived,
        # so assert one of the two -- never a crash, never a wrong ISO.
        assert p.name in (
            "campd-unit-outages-unitroute-MISO.csv",
            "campd-unit-outages-MISO.csv",
        )

    def test_never_crosses_an_iso_boundary(self):
        assert "MISO" in unit_outage_csv_for_iso("MISO", True).name
        assert "PJM" in unit_outage_csv_for_iso("PJM", True).name


class TestRegistration:
    def test_field_exists_and_defaults_off(self):
        assert ScenarioConfig().unit_outage_mixed_gas_routing is False

    def test_cache_key_neutral_while_off(self):
        a = ScenarioConfig()
        b = ScenarioConfig(unit_outage_mixed_gas_routing=False)
        assert a.cache_key() == b.cache_key()

    def test_cache_key_distinct_while_armed(self):
        assert (
            ScenarioConfig(unit_outage_mixed_gas_routing=True).cache_key()
            != ScenarioConfig().cache_key()
        )
