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
    """A plant in the Permian / CREZ belt should be assigned to West zone."""
    # Midland, TX area: lat ~32.0, lon ~-102.1
    zone = assign_zone_by_coords(32.0, -102.1, "ERCOT")
    assert zone == "West"


def test_ercot_panhandle_zone():
    """A plant in the Texas Panhandle should be assigned to Panhandle zone."""
    # Amarillo, TX: lat ~35.2, lon ~-101.8 — north of the West Texas belt.
    assert assign_zone_by_coords(35.2, -101.8, "ERCOT") == "Panhandle"
    # Lubbock, TX: lat ~33.6, lon ~-101.9 — just above the 33.5 boundary.
    assert assign_zone_by_coords(33.6, -101.9, "ERCOT") == "Panhandle"


def test_ercot_houston_zone():
    """A plant in Harris County should be assigned to Houston zone."""
    # Use FIPS: state=48, county=201 (Harris)
    zone = assign_zone_by_fips("48", "201", "ERCOT")
    assert zone == "Houston"


def test_ercot_north_zone():
    """A plant near Dallas should be assigned to North zone."""
    zone = assign_zone_by_coords(32.8, -96.8, "ERCOT")
    assert zone == "North"


def test_ercot_south_central_zone():
    """Austin and San Antonio plants should be assigned to South_Central."""
    # Austin, TX: lat ~30.3, lon ~-97.7
    assert assign_zone_by_coords(30.3, -97.7, "ERCOT") == "South_Central"
    # San Antonio, TX: lat ~29.4, lon ~-98.5
    assert assign_zone_by_coords(29.4, -98.5, "ERCOT") == "South_Central"


def test_ercot_south_zone():
    """A plant near Corpus Christi should be assigned to South zone."""
    # Corpus Christi, TX: lat ~27.8, lon ~-97.4 — south of the 29.0 boundary.
    zone = assign_zone_by_coords(27.8, -97.4, "ERCOT")
    assert zone == "South"


def test_pjm_state_mapping():
    """PJM zones follow state boundaries."""
    assert assign_zone_by_fips("39", None, "PJM") == "PJM_West"     # OH
    assert assign_zone_by_fips("42", None, "PJM") == "PJM_Central"  # PA
    assert assign_zone_by_fips("34", None, "PJM") == "PJM_East"     # NJ
    assert assign_zone_by_fips("51", None, "PJM") == "PJM_South"    # VA


def test_single_zone_isos():
    """NYISO, NEISO always return their single zone."""
    assert assign_zone(12345, "NYISO") == "NYISO_main"
    assert assign_zone(12345, "NEISO") == "NEISO_main"


def test_caiso_np15_zone():
    """A Northern California plant (north of Path 15) lands in NP15."""
    # San Francisco Bay area: lat ~37.8 — north of the ~36.5 Path 15 line.
    assert assign_zone_by_coords(37.8, -122.4, "CAISO") == "NP15"


def test_caiso_zp26_zone():
    """A southern San Joaquin Valley plant lands in ZP26."""
    # Bakersfield / Kern: lat ~35.3 — between Path 26 (~35.0) and Path 15.
    assert assign_zone_by_coords(35.3, -119.0, "CAISO") == "ZP26"


def test_caiso_sp15_zone():
    """A Southern California plant (south of Path 26) lands in SP15."""
    # Los Angeles: lat ~34.0 — south of the ~35.0 Path 26 line.
    assert assign_zone_by_coords(34.0, -118.2, "CAISO") == "SP15"


def test_caiso_central_coast_fips_rule():
    """Central-coast PG&E counties are lifted to NP15 despite ZP26 latitude.

    San Luis Obispo (FIPS 6/79, Diablo Canyon) sits at lat ~35.2 — inside
    the ZP26 latitude band — but is coastal PG&E north of Path 26, so the
    county rule places it in NP15.
    """
    assert assign_zone_by_fips("6", "79", "CAISO") == "NP15"


def test_caiso_out_of_state_arizona():
    """Arizona CISO resources (Palo Verde / West-of-River) land in SP15."""
    assert assign_zone_by_fips("4", "27", "CAISO") == "SP15"


def test_caiso_known_plants_resolve_to_expected_zones():
    """Named California plants land in their real CAISO trading zones."""
    # ORIS codes from eGRID 2023 PLNT23 (BACODE == CISO).
    cases = {
        260: "NP15",     # Moss Landing (Monterey)
        286: "NP15",     # Geysers geothermal (Sonoma)
        52169: "ZP26",   # Midway Sunset Cogen (Kern)
        55151: "ZP26",   # La Paloma Generating Plant (Kern)
        302: "SP15",     # Encina / Cabrillo (San Diego)
        350: "SP15",     # Ormond Beach (Ventura)
        6099: "NP15",    # Diablo Canyon (San Luis Obispo, central-coast rule)
        57373: "SP15",   # Agua Caliente Solar (Arizona)
        52015: "NP15",   # Dixie Valley geothermal (northern Nevada)
    }
    for oris, expected in cases.items():
        assert assign_zone(oris, "CAISO") == expected, f"ORIS {oris}"


def test_caiso_every_plant_resolves():
    """Every CISO plant resolves to a real trading zone; none are dropped."""
    lookup = build_zone_lookup("CAISO")
    assert len(lookup) > 1000  # CAISO has ~1,500 plants in eGRID
    valid = {"NP15", "ZP26", "SP15"}
    assert set(lookup.values()) <= valid
    # All three trading zones are populated.
    assert valid <= set(lookup.values())
    # The import node is never a plant zone.
    assert "WECC_import" not in lookup.values()
    assert "CAISO_main" not in lookup.values()


def test_egrid_lookup_loads():
    """eGRID PLNT23 lookup table loads without error."""
    lookup = build_zone_lookup("ERCOT")
    assert len(lookup) > 500  # ERCOT has ~700 plants in eGRID


def test_ercot_zone_capacity_balance():
    """Geographic assignment spreads thermal capacity across the load zones.

    The Panhandle zone is a pure wind exporter: its in-ERCOT fleet is
    entirely wind and solar (the Amarillo thermal stations sit in SPP, not
    ERCOT), so geographic assignment correctly leaves it with no thermal
    capacity. Every other zone holds a non-trivial share; the 3% (not 5%)
    threshold accommodates the West zone, which is genuinely thermal-light
    behind the West Texas Export interface.
    """
    config = get_iso_config("ERCOT")
    fleet = load_fleet_from_csv("ERCOT", config)
    cap_by_zone: dict[str, float] = defaultdict(float)
    for g in fleet:
        cap_by_zone[g.zone] += g.pmax_mw
    total = sum(cap_by_zone.values())
    assert cap_by_zone["Panhandle"] == 0.0
    for zone in config.zone_names:
        if zone == "Panhandle":
            continue
        share = cap_by_zone[zone] / total
        assert share > 0.03, f"{zone} has only {share:.1%} of capacity"


def test_pjm_fleet_loads():
    """PJM fleet loads and all 4 zones are populated."""
    config = get_iso_config("PJM")
    fleet = load_fleet_from_csv("PJM", config)
    zones_seen = {g.zone for g in fleet}
    for z in config.zone_names:
        assert z in zones_seen, f"Zone {z} has no generators"
