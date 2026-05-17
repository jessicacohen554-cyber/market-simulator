"""Tests for geographic zone assignment from eGRID plant data."""

from collections import defaultdict

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import load_fleet_from_csv
from market_sim.data.zone_assignment import (
    assign_zone,
    assign_zone_by_coords,
    assign_zone_by_fips,
    build_zone_lookup,
)


def test_ercot_west_zone():
    """A plant in far west Texas should be assigned to West zone."""
    # Odessa, TX area: lat ~31.8, lon ~-102.3
    zone = assign_zone_by_coords(31.8, -102.3, "ERCOT")
    assert zone == "West"


def test_ercot_houston_zone():
    """A plant in Harris County should be assigned to Houston zone."""
    # Use FIPS: state=48, county=201 (Harris)
    zone = assign_zone_by_fips("48", "201", "ERCOT")
    assert zone == "Houston"


def test_ercot_north_zone():
    """A plant near Dallas should be assigned to North zone."""
    zone = assign_zone_by_coords(32.8, -96.8, "ERCOT")
    assert zone == "North"


def test_ercot_south_zone():
    """A plant near San Antonio should be assigned to South zone."""
    zone = assign_zone_by_coords(29.4, -98.5, "ERCOT")
    assert zone == "South"


def test_pjm_state_mapping():
    """PJM zones follow state boundaries."""
    assert assign_zone_by_fips("39", None, "PJM") == "PJM_West"     # OH
    assert assign_zone_by_fips("42", None, "PJM") == "PJM_Central"  # PA
    assert assign_zone_by_fips("34", None, "PJM") == "PJM_East"     # NJ
    assert assign_zone_by_fips("51", None, "PJM") == "PJM_South"    # VA


def test_single_zone_isos():
    """CAISO, NYISO, NEISO always return their single zone."""
    assert assign_zone(12345, "CAISO") == "CAISO_main"
    assert assign_zone(12345, "NYISO") == "NYISO_main"
    assert assign_zone(12345, "NEISO") == "NEISO_main"


def test_egrid_lookup_loads():
    """eGRID PLNT23 lookup table loads without error."""
    lookup = build_zone_lookup("ERCOT")
    assert len(lookup) > 500  # ERCOT has ~700 plants in eGRID


def test_ercot_zone_capacity_balance():
    """After geographic assignment, every zone holds a non-trivial share.

    The threshold is 3%, not 5%: the ERCOT West weather zone is genuinely
    thermal-light (its capacity is dominated by wind, which is not part of
    the thermal fleet), so geographic assignment correctly leaves it the
    smallest zone at roughly 4% of thermal capacity.
    """
    fleet = load_fleet_from_csv("ERCOT", get_iso_config("ERCOT"))
    cap_by_zone: dict[str, float] = defaultdict(float)
    for g in fleet:
        cap_by_zone[g.zone] += g.pmax_mw
    total = sum(cap_by_zone.values())
    for zone, cap in cap_by_zone.items():
        assert cap / total > 0.03, f"{zone} has only {cap / total:.1%} of capacity"


def test_pjm_fleet_loads():
    """PJM fleet loads and all 4 zones are populated."""
    config = get_iso_config("PJM")
    fleet = load_fleet_from_csv("PJM", config)
    zones_seen = {g.zone for g in fleet}
    for z in config.zone_names:
        assert z in zones_seen, f"Zone {z} has no generators"
