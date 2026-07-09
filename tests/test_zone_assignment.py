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


def test_ercot_northeast_zone():
    """NE-Texas plants (Martin Lake) sit in the NE_LOB lobe -> Northeast."""
    assert assign_zone_by_coords(32.26, -94.57, "ERCOT") == "Northeast"  # Martin Lake
    assert assign_zone_by_coords(33.06, -94.86, "ERCOT") == "Northeast"  # Welsh
    # Central-Texas coal (Limestone) stays in North, not the NE lobe.
    assert assign_zone_by_coords(31.4, -96.3, "ERCOT") == "North"


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
    """States that fall cleanly inside one PJM zone map by FIPS state code."""
    assert assign_zone_by_fips("17", None, "PJM") == "PJM_ComEd"  # IL ComEd
    assert assign_zone_by_fips("18", None, "PJM") == "PJM_AEP_Ohio"  # IN AEP
    assert assign_zone_by_fips("26", None, "PJM") == "PJM_AEP_Ohio"  # MI AEP
    assert assign_zone_by_fips("21", None, "PJM") == "PJM_AEP_Ohio"  # KY EKPC
    # OH / WV with no coordinates default to the southern AEP_Ohio belt.
    assert assign_zone_by_fips("39", None, "PJM") == "PJM_AEP_Ohio"  # OH
    assert assign_zone_by_fips("54", None, "PJM") == "PJM_AEP_Ohio"  # WV
    # EMAAC — the eastern NJ/DE/Philadelphia load pocket.
    assert assign_zone_by_fips("34", None, "PJM") == "PJM_EMAAC"  # NJ PSEG
    assert assign_zone_by_fips("10", None, "PJM") == "PJM_EMAAC"  # DE DPL
    # SWMAAC — Baltimore/DC.
    assert assign_zone_by_fips("11", None, "PJM") == "PJM_SWMAAC"  # DC PEPCO
    # Dominion (DOM).
    assert assign_zone_by_fips("51", None, "PJM") == "PJM_Dominion"  # VA DOM
    assert assign_zone_by_fips("37", None, "PJM") == "PJM_Dominion"  # NC DOM


def test_pjm_unknown_state_falls_back_to_largest():
    """A PJM-BA plant whose state lacks a rule falls back to the largest zone.

    PJM has a lone seam plant in Minnesota (FIPS 27); with no zone rule it
    lands in the largest-load-share zone (PJM_AEP_Ohio) rather than dropped.
    """
    assert assign_zone_by_fips("27", None, "PJM") == "PJM_AEP_Ohio"


def test_pjm_pennsylvania_split():
    """Pennsylvania straddles EMAAC, West_APS and Central_PA.

    The Philadelphia metro (PECO counties) is EMAAC; western PA (west of
    ~-79.0) is West_APS; the central PPL/METED/PENELEC corridor is the
    Central_PA default when no western longitude places it.
    """
    # Philadelphia county (FIPS 42/101) — EMAAC via the county rule.
    assert assign_zone_by_fips("42", "101", "PJM") == "PJM_EMAAC"
    # Montgomery county (42/091, Limerick) is also Philadelphia metro → EMAAC.
    assert assign_zone_by_fips("42", "91", "PJM") == "PJM_EMAAC"
    # A PA plant with no coordinates falls back to the Central PA corridor.
    assert assign_zone_by_fips("42", "63", "PJM") == "PJM_Central_PA"


def test_pjm_maryland_split():
    """Maryland is SWMAAC except the APS western panhandle (West_APS)."""
    # Most of MD (BGE/PEPCO) with no coordinates → SWMAAC.
    assert assign_zone_by_fips("24", None, "PJM") == "PJM_SWMAAC"


def test_pjm_known_plants_resolve_to_expected_zones():
    """Named PJM plants land in their real eight-zone LDAs.

    Exercises every zone and the OH/WV/PA/MD boundary rules. ORIS codes from
    eGRID 2023 PLNT23 (BACODE == PJM).
    """
    cases = {
        6023: "PJM_ComEd",  # Byron nuclear (IL, ComEd)
        6149: "PJM_ATSI",  # Davis-Besse nuclear (northern OH, FirstEnergy)
        6040: "PJM_West_APS",  # Beaver Valley nuclear (western PA, lon -80.4)
        3118: "PJM_West_APS",  # Conemaugh coal (Indiana County PA, lon -79.1)
        6103: "PJM_Central_PA",  # Susquehanna nuclear (central PA, PPL)
        6105: "PJM_EMAAC",  # Limerick nuclear (Montgomery County, Philly)
        2410: "PJM_EMAAC",  # Salem nuclear (NJ, PSEG)
        602: "PJM_SWMAAC",  # Brandon Shores (Anne Arundel County MD, BGE)
        6168: "PJM_Dominion",  # North Anna nuclear (VA, Dominion)
        3806: "PJM_Dominion",  # Surry nuclear (VA, Dominion)
    }
    for oris, expected in cases.items():
        assert assign_zone(oris, "PJM") == expected, f"ORIS {oris}"


def test_pjm_every_plant_resolves():
    """Every PJM plant resolves to one of the four zones; none are dropped."""
    config = get_iso_config("PJM")
    lookup = build_zone_lookup("PJM")
    assert len(lookup) > 1000  # PJM has ~1,700 plants in eGRID
    valid = set(config.zone_names)
    assert set(lookup.values()) <= valid
    # All four zones are populated.
    assert valid <= set(lookup.values())


def test_caiso_np15_zone():
    """A Northern California plant (north of Path 15) lands in NP15."""
    # San Francisco Bay area: lat ~37.8 — north of the ~36.5 Path 15 line.
    assert assign_zone_by_coords(37.8, -122.4, "CAISO") == "NP15"


def test_caiso_zp26_zone():
    """A southern San Joaquin Valley plant lands in ZP26."""
    # Bakersfield / Kern: lat ~35.3 — between Path 26 (~35.0) and Path 15.
    assert assign_zone_by_coords(35.3, -119.0, "CAISO") == "ZP26"


def test_caiso_sp15_la_basin_zone():
    """A Southern California plant (south of Path 26) lands in LA_BASIN.

    Los Angeles: lat ~34.0 — south of the ~35.0 Path 26 line, north of the
    ~33.4 coords-only SDGE cutoff, so the coords-only fallback places it in
    the LA-basin LCR pocket.
    """
    assert assign_zone_by_coords(34.0, -118.2, "CAISO") == "LA_BASIN"


def test_caiso_sp15_sdge_zone():
    """A San Diego-latitude plant (south of the SDGE coords-only cutoff) lands in SDGE."""
    # San Diego: lat ~32.7 — south of the ~33.4 coords-only SDGE cutoff.
    assert assign_zone_by_coords(32.7, -117.1, "CAISO") == "SDGE"


def test_caiso_central_coast_fips_rule():
    """Central-coast PG&E counties are lifted to NP15 despite ZP26 latitude.

    San Luis Obispo (FIPS 6/79, Diablo Canyon) sits at lat ~35.2 — inside
    the ZP26 latitude band — but is coastal PG&E north of Path 26, so the
    county rule places it in NP15.
    """
    assert assign_zone_by_fips("6", "79", "CAISO") == "NP15"


def test_caiso_out_of_state_arizona():
    """Arizona CISO resources (Palo Verde / West-of-River) land in SP15_rest.

    Path 46/WOR and the WECC_DSW corridor terminate on SP15_rest post-split
    (docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md).
    """
    assert assign_zone_by_fips("4", "27", "CAISO") == "SP15_rest"


def test_caiso_known_plants_resolve_to_expected_zones():
    """Named California plants land in their real CAISO trading zones."""
    # ORIS codes from eGRID 2023 PLNT23 (BACODE == CISO).
    cases = {
        260: "NP15",  # Moss Landing (Monterey)
        286: "NP15",  # Geysers geothermal (Sonoma)
        52169: "ZP26",  # Midway Sunset Cogen (Kern)
        55151: "ZP26",  # La Paloma Generating Plant (Kern)
        302: "SDGE",  # Encina / Cabrillo (San Diego)
        350: "LA_BASIN",  # Ormond Beach (Ventura, coords-only LA-basin band)
        6099: "NP15",  # Diablo Canyon (San Luis Obispo, central-coast rule)
        57373: "SP15_rest",  # Agua Caliente Solar (Arizona)
        52015: "NP15",  # Dixie Valley geothermal (northern Nevada)
        315: "LA_BASIN",  # AES Alamitos (Los Angeles County)
    }
    for oris, expected in cases.items():
        assert assign_zone(oris, "CAISO") == expected, f"ORIS {oris}"


def test_caiso_every_plant_resolves():
    """Every CISO plant resolves to a real trading zone; none are dropped."""
    lookup = build_zone_lookup("CAISO")
    assert len(lookup) > 1000  # CAISO has ~1,500 plants in eGRID
    valid = {"NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"}
    assert set(lookup.values()) <= valid
    # All five trading zones are populated.
    assert valid <= set(lookup.values())
    # The import node is never a plant zone.
    assert "WECC_import" not in lookup.values()
    assert "CAISO_main" not in lookup.values()
    # No plant silently returns the old, now-deleted SP15 zone name.
    assert "SP15" not in lookup.values()


def test_miso_state_mapping():
    """MISO zones follow the sub-BA (LRZ) boundaries; FIPS state is authoritative.

    Zones are whole EIA-930 sub-BA unions so the fleet and load partitions match
    (eia_loader._MISO_SUBBA_ZONE_GROUPS): MO sits with IA in the Plains group
    (sub-BA 0035) and WI sits with MI in the East group (sub-BA 0027).
    """
    assert assign_zone_by_fips("27", None, "MISO") == "MISO-West"  # MN
    assert assign_zone_by_fips("46", None, "MISO") == "MISO-West"  # SD
    assert assign_zone_by_fips("38", None, "MISO") == "MISO-West"  # ND
    assert assign_zone_by_fips("19", None, "MISO") == "MISO-Plains"  # IA
    assert assign_zone_by_fips("29", None, "MISO") == "MISO-Plains"  # MO (LRZ 5)
    assert assign_zone_by_fips("17", None, "MISO") == "MISO-Illinois"  # IL
    assert assign_zone_by_fips("18", None, "MISO") == "MISO-Indiana"  # IN
    assert assign_zone_by_fips("21", None, "MISO") == "MISO-Indiana"  # KY (LRZ 6)
    assert assign_zone_by_fips("55", None, "MISO") == "MISO-East"  # WI (LRZ 2)
    assert assign_zone_by_fips("26", None, "MISO") == "MISO-East"  # MI
    assert assign_zone_by_fips("22", None, "MISO") == "MISO-South"  # LA
    assert assign_zone_by_fips("5", None, "MISO") == "MISO-South"  # AR
    assert assign_zone_by_fips("48", None, "MISO") == "MISO-South"  # TX (Entergy)


def test_miso_unmapped_state_falls_back_to_pinned_midwest_default():
    """A plant outside the MISO state map falls back to the pinned default.

    NOT the largest-load-share zone: at six zones that flipped to MISO-South
    (0.2711), an unacceptable default for the overwhelmingly Midwest
    unlocated cohort — the fallback is pinned to MISO-Illinois.
    """
    assert assign_zone_by_fips(None, None, "MISO") == "MISO-Illinois"


def test_miso_coords_fallback_south_vs_midwest():
    """Coords-only callers degrade to South vs the pinned Midwest default.

    Latitude cannot resolve the six-zone Midwest split (the W-E boundaries
    are longitudinal), so only the Entergy South band survives.
    """
    # Deep South (Gulf Coast) -> South.
    assert assign_zone_by_coords(30.0, -91.0, "MISO") == "MISO-South"
    # Any Midwest latitude -> the pinned Midwest default.
    assert assign_zone_by_coords(46.0, -94.0, "MISO") == "MISO-Illinois"
    assert assign_zone_by_coords(40.0, -89.0, "MISO") == "MISO-Illinois"


def test_miso_known_plants_resolve_to_expected_zones():
    """Named MISO plants land in their real sub-regions."""
    # ORIS codes from eGRID 2023 PLNT23 (BACODE == MISO).
    cases = {
        6090: "MISO-West",  # Sherburne County / Sherco (Minnesota)
        1925: "MISO-West",  # Prairie Island nuclear (Minnesota)
        6098: "MISO-West",  # Big Stone (South Dakota)
        6254: "MISO-Plains",  # Ottumwa (Iowa)
        1733: "MISO-East",  # Monroe (Michigan)
        6034: "MISO-East",  # Belle River (Michigan)
        6113: "MISO-Indiana",  # Gibson (Indiana)
        4270: "MISO-South",  # Waterford 3 nuclear (Louisiana)
        8055: "MISO-South",  # Arkansas Nuclear One (Arkansas)
        6072: "MISO-South",  # Grand Gulf nuclear (Mississippi)
    }
    for oris, expected in cases.items():
        assert assign_zone(oris, "MISO") == expected, f"ORIS {oris}"


def test_miso_every_plant_resolves():
    """Every MISO plant resolves to a real zone; none are dropped."""
    lookup = build_zone_lookup("MISO")
    assert len(lookup) > 2000  # MISO has ~2,100 plants in eGRID
    valid = {
        "MISO-West",
        "MISO-Plains",
        "MISO-Illinois",
        "MISO-Indiana",
        "MISO-East",
        "MISO-South",
    }
    assert set(lookup.values()) <= valid
    # All six zones are populated.
    assert valid <= set(lookup.values())


def test_nyiso_nyc_zone():
    """A Manhattan plant lands in NYC by coordinates."""
    # Midtown Manhattan: lat ~40.76, lon ~-73.95.
    assert assign_zone_by_coords(40.76, -73.95, "NYISO") == "NYC"


def test_nyiso_long_island_zone():
    """A Long Island plant (east of NYC) lands in Long_Island."""
    # Northport, Suffolk County: lat ~40.92, lon ~-73.34.
    assert assign_zone_by_coords(40.92, -73.34, "NYISO") == "Long_Island"


def test_nyiso_upstate_west_by_coords():
    """Western and far-north NY plants land in Upstate_West.

    Niagara (west of the Hudson corridor) and the St. Lawrence North Country
    (north of the Capital region) both resolve upstate, where the Niagara and
    St. Lawrence hydro belong.
    """
    # Niagara Falls: lat ~43.14, lon ~-79.04 (west of the -75.0 line).
    assert assign_zone_by_coords(43.14, -79.04, "NYISO") == "Upstate_West"
    # Massena / St. Lawrence: lat ~45.0, lon ~-74.8 (north of the 43.3 line).
    assert assign_zone_by_coords(45.0, -74.8, "NYISO") == "Upstate_West"


def test_nyiso_county_fips_mapping():
    """NY county FIPS codes map to the aggregated NYISO zones."""
    assert assign_zone_by_fips("36", "61", "NYISO") == "NYC"  # Manhattan
    assert assign_zone_by_fips("36", "103", "NYISO") == "Long_Island"  # Suffolk
    assert assign_zone_by_fips("36", "119", "NYISO") == "Lower_Hudson"  # Westchester
    assert assign_zone_by_fips("36", "1", "NYISO") == "Capital_Hudson"  # Albany
    assert assign_zone_by_fips("36", "63", "NYISO") == "Upstate_West"  # Niagara
    assert assign_zone_by_fips("36", "89", "NYISO") == "Upstate_West"  # St. Lawrence


def test_nyiso_nj_merchant_plant_lands_downstate():
    """NJ merchant-cable plants (no NY county) route downstate by lat/lon.

    Bayonne Energy Center (Hudson County, NJ) injects into NYC through the
    Gowanus cable; it carries a NJ FIPS state so the county path is skipped
    and lat/lon places it in the NYC pocket it feeds.
    """
    # Bayonne, NJ: lat ~40.65, lon ~-74.09 — FIPS state 34, not New York.
    assert assign_zone(8012, "NYISO") == "NYC"


def test_nyiso_known_plants_resolve_to_expected_zones():
    """Named NYISO plants land in their real aggregated zones.

    ORIS codes from eGRID 2023 PLNT23 (BACODE == NYIS). The two NYPA hydro
    giants (Robert Moses Niagara, Robert Moses St. Lawrence) must land
    upstate; the downstate fleet (Ravenswood, Northport, Barrett) must land
    in the J/K pockets behind the import interfaces.
    """
    cases = {
        2693: "Upstate_West",  # Robert Moses Niagara hydro (Niagara, zone A)
        2694: "Upstate_West",  # Robert Moses St. Lawrence hydro (zone D)
        2500: "NYC",  # Ravenswood (Queens, zone J)
        2516: "Long_Island",  # Northport (Suffolk, zone K)
        2511: "Long_Island",  # E F Barrett (Nassau, zone K)
        55405: "Capital_Hudson",  # Athens Generating (Greene, zone F)
        2539: "Capital_Hudson",  # Bethlehem Energy Center (Albany, zone F)
        8006: "Capital_Hudson",  # Roseton (Orange, zone G)
        50882: "Lower_Hudson",  # Wheelabrator Westchester (zone H/I)
    }
    for oris, expected in cases.items():
        assert assign_zone(oris, "NYISO") == expected, f"ORIS {oris}"


def test_nyiso_every_plant_resolves():
    """Every NYIS plant resolves to a real model zone; none are dropped."""
    lookup = build_zone_lookup("NYISO")
    assert len(lookup) > 800  # NYISO has ~860 plants in eGRID
    valid = {
        "Upstate_West",
        "Capital_Hudson",
        "Lower_Hudson",
        "NYC",
        "Long_Island",
    }
    assert set(lookup.values()) <= valid
    # All five aggregated zones are populated.
    assert valid <= set(lookup.values())
    # The old single-zone stub name never appears.
    assert "NYISO_main" not in lookup.values()


def test_neiso_state_mapping():
    """NEISO zones follow state boundaries (FIPS state is authoritative)."""
    assert assign_zone_by_fips("23", None, "NEISO") == "North"  # ME
    assert assign_zone_by_fips("33", None, "NEISO") == "North"  # NH
    assert assign_zone_by_fips("50", None, "NEISO") == "North"  # VT
    assert assign_zone_by_fips("9", None, "NEISO") == "Connecticut"  # CT
    assert assign_zone_by_fips("44", None, "NEISO") == "Central"  # RI


def test_neiso_massachusetts_county_split():
    """Massachusetts splits the NEMA/Boston pocket from WCMA/SEMA by county.

    The Boston-metro counties (Suffolk, Middlesex, Essex, Norfolk) land in
    Boston; every other MA county folds into the Central (WCMA/SEMA/RI)
    aggregate. This mirrors ERCOT's Houston-county FIPS rule.
    """
    # NEMA/Boston metro counties -> Boston.
    assert assign_zone_by_fips("25", "25", "NEISO") == "Boston"  # Suffolk
    assert assign_zone_by_fips("25", "17", "NEISO") == "Boston"  # Middlesex
    assert assign_zone_by_fips("25", "9", "NEISO") == "Boston"  # Essex
    assert assign_zone_by_fips("25", "21", "NEISO") == "Boston"  # Norfolk
    # WCMA / SEMA counties -> Central.
    assert assign_zone_by_fips("25", "27", "NEISO") == "Central"  # Worcester (WCMA)
    assert assign_zone_by_fips("25", "13", "NEISO") == "Central"  # Hampden (WCMA)
    assert assign_zone_by_fips("25", "1", "NEISO") == "Central"  # Barnstable (SEMA)
    assert assign_zone_by_fips("25", "5", "NEISO") == "Central"  # Bristol (SEMA)


def test_neiso_unmapped_state_falls_back_to_central():
    """A plant outside the ISO-NE state map (no coords) falls back to Central."""
    # No FIPS state and no coordinates -> largest-load-share zone (Central).
    assert assign_zone_by_fips(None, None, "NEISO") == "Central"


def test_neiso_coords_fallback_bands():
    """Coords-only callers (no FIPS state) get the coarse lat/lon fallback."""
    # Northern New England (Maine coast) -> North.
    assert assign_zone_by_coords(43.75, -70.3, "NEISO") == "North"
    # Southwest corner (Connecticut coast) -> Connecticut.
    assert assign_zone_by_coords(41.31, -72.17, "NEISO") == "Connecticut"
    # Eastern Massachusetts coast (Boston metro) -> Boston.
    assert assign_zone_by_coords(42.4, -71.07, "NEISO") == "Boston"
    # SE Mass / Rhode Island -> Central.
    assert assign_zone_by_coords(41.77, -70.5, "NEISO") == "Central"  # Cape Cod
    assert assign_zone_by_coords(41.82, -71.39, "NEISO") == "Central"  # Providence RI


def test_neiso_known_plants_resolve_to_expected_zones():
    """Named ISO-NE plants land in their real aggregated zones."""
    # ORIS codes from eGRID 2023 PLNT23 (BACODE == ISNE).
    cases = {
        1507: "North",  # William F Wyman (Maine)
        6115: "North",  # Seabrook nuclear (New Hampshire)
        589: "North",  # J C McNeil (Vermont)
        566: "Connecticut",  # Millstone nuclear (CT, New London)
        562: "Connecticut",  # Middletown (CT)
        3236: "Central",  # Manchester Street Station (Rhode Island)
        1588: "Boston",  # Mystic (MA, Middlesex — NEMA)
        55317: "Boston",  # Fore River Energy Center (MA, Norfolk — NEMA)
        60903: "Boston",  # Salem Harbor NGCC (MA, Essex — NEMA)
        1599: "Central",  # Canal Station (MA, Barnstable — SEMA)
        547: "Central",  # Northfield Mountain (MA, Franklin — WCMA)
    }
    for oris, expected in cases.items():
        assert assign_zone(oris, "NEISO") == expected, f"ORIS {oris}"


def test_neiso_every_plant_resolves():
    """Every ISNE plant resolves to a real load zone; none are dropped."""
    lookup = build_zone_lookup("NEISO")
    assert len(lookup) > 1000  # ISO-NE has ~1,250 plants in eGRID
    valid = {"North", "Central", "Boston", "Connecticut"}
    assert set(lookup.values()) <= valid
    # All four load zones are populated.
    assert valid <= set(lookup.values())
    # The import node is never a plant zone.
    assert "HQ_import" not in lookup.values()
    assert "NEISO_main" not in lookup.values()


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


def test_pjm_fleet_loads():
    """PJM fleet loads and all 4 zones are populated."""
    config = get_iso_config("PJM")
    fleet = load_fleet_from_csv("PJM", config)
    zones_seen = {g.zone for g in fleet}
    for z in config.zone_names:
        assert z in zones_seen, f"Zone {z} has no generators"
