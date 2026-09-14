"""Cross-cutting pins for the SOCO registration (lane SOCO-20, 2026-09-14).

SOCO — the Southern Company balancing authority — is the ninth region in
``config.iso_configs._ISO_BUILDERS`` (``docs/multi-iso/soco-addition-plan-
2026-09.md`` §2.3; NWPP, the eighth, was registered the same day by lane
NWPP-20 and merged first). The per-registry values are pinned next to their own
modules' tests (``test_iso_config``, ``test_zone_assignment``,
``test_backcast_config``, ``test_data_profiles_tokens``); this file pins the
seams that cut ACROSS modules and would otherwise fail only at solve time:

* the atomic registration set (`_ISO_BUILDERS` / `DEMAND_LOADERS` /
  `SURFACE_ISOS` together, plan §2.3 row 1),
* what SOCO deliberately does NOT carry — no capacity market, no import node,
  no ancillary-service design (owner cards S4 / S5; gates G7),
* the McIntosh CAES representation (card S7): a 25 MW gas CT in the thermal
  fleet, and NOT a storage unit,
* the EIA-930 balancing-authority plumbing and the eight-neighbour interface
  registry (card S4, default-off),
* the two seam repairs the registration required (COD-aware nuclear-CF
  denominator; CAES skip in the storage loader), each pinned as a no-op for the
  seven incumbent regions.

No solves; no data beyond the committed curated parquets (tests that need
them skip when the hydration profile lacks SOCO's subtree).
"""

from __future__ import annotations

import pytest

from market_sim.config import capacity_market as cm
from market_sim.config.iso_configs import _ISO_BUILDERS, SUPPORTED_ISOS, get_iso_config
from market_sim.config.solve_surface import SURFACE_ISOS
from market_sim.data.eia930 import DEMAND_LOADERS
from market_sim.data.fleet.eia860 import _map_fuel_type
from market_sim.data.fleet.models import BA_CODE_TO_ISO
from market_sim.data.zone_assignment import _ISO_TO_BA_CODE
from market_sim.model.interchange.registry import INTERCHANGE_INJECTIONS
from market_sim.model.interchange.spec import INTERFACE_NEIGHBORS

# Registration order of the incumbent regions (iso_configs._ISO_BUILDERS): the
# seven this lane was chartered against, plus NWPP (lane NWPP-20, merged the
# same day, ahead of SOCO).
SEVEN = ("ERCOT", "CAISO", "MISO", "PJM", "NYISO", "NEISO", "SPP")
INCUMBENTS = (*SEVEN, "NWPP")


# --- Row 1: the atomic registration set -------------------------------------


def test_soco_is_the_ninth_region_and_registered_last():
    assert list(_ISO_BUILDERS) == [*INCUMBENTS, "SOCO"]
    assert SUPPORTED_ISOS == tuple(_ISO_BUILDERS)


def test_registration_set_is_atomic():
    """`_ISO_BUILDERS`, `DEMAND_LOADERS` and `SURFACE_ISOS` move together —
    the import-time assert in demand.py and test_solve_surface enforce each
    pair; this pins the triple by name."""
    assert "SOCO" in DEMAND_LOADERS
    assert "SOCO" in SURFACE_ISOS
    assert set(SURFACE_ISOS) == set(SUPPORTED_ISOS)


def test_balancing_authority_code_round_trips():
    """SOCO is a BALANCING AUTHORITY, so its EIA-930 / EIA-860 BA code IS the
    region key — no crosswalk indirection in either direction."""
    assert _ISO_TO_BA_CODE["SOCO"] == "SOCO"
    assert BA_CODE_TO_ISO["SOCO"] == "SOCO"


# --- What SOCO deliberately does not carry ----------------------------------


def test_soco_has_no_capacity_market():
    """Cards S4/S6: vertically-integrated, IRP-planned; no RPM/PRA analogue.
    Absence from every capacity-market registry is the design, not a gap."""
    assert "SOCO" not in cm.MARKET_DESIGN
    assert "SOCO" not in cm.MARKET_DESIGN_VINTAGES
    assert "SOCO" not in cm.CAPACITY_CURVE_ELIGIBLE_BY_ISO
    assert "SOCO" not in cm.RENEWABLE_ELCC_CURVES_BY_ISO
    # ...while the adequacy inputs the reliability floor reads ARE present.
    assert cm.PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"] == 0.26
    assert cm.ADEQUACY_EXTERNAL_TIE_FIRM_MW["SOCO"] == 0.0


def test_soco_has_no_import_node():
    """Gate G7: served interchange is the measured EIA-930 envelope, priced
    neighbours are the DEFAULT-OFF `INTERFACE_NEIGHBORS` blocks. No zone is an
    import node and no tranche registry names SOCO."""
    from market_sim.config.interchange_config import IMPORT_TRANCHES, IMPORT_ZONE

    cfg = get_iso_config("SOCO")
    assert [z.name for z in cfg.zones] == ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
    assert "SOCO" not in IMPORT_ZONE
    assert "SOCO" not in IMPORT_TRANCHES
    assert all(z.load_share > 0.0 for z in cfg.zones)


def test_soco_neighbour_registry_is_the_eight_default_off_blocks():
    blocks = INTERFACE_NEIGHBORS["SOCO"]
    names = [b.name for b in blocks]
    assert len(names) == len(set(names)) == 8
    assert set(names) == {
        "SOCO_TVA",
        "SOCO_MISO",
        "SOCO_DUK",
        "SOCO_SCEG",
        "SOCO_SC",
        "SOCO_FPL",
        "SOCO_FPC",
        "SOCO_TAL",
    }
    # Every block borders a real SOCO zone and none is armed by default.
    zones = {"SOCO_AL", "SOCO_GA", "SOCO_MS"}
    for b in blocks:
        assert set(b.border_zones) <= zones, b.name
        assert b.interface_limit_mw > 0.0, b.name
        assert b.hurdle == 2.0, b.name
    # No neighbour name collides with another ISO's registry.
    for iso, other in INTERFACE_NEIGHBORS.items():
        if iso != "SOCO":
            assert not (set(names) & {b.name for b in other}), iso
    assert INTERCHANGE_INJECTIONS["SOCO"]


def test_soco_reserve_design_is_refused_by_name():
    """Card S5: no ancillary-service market, so `energy_reserve_coopt` has no
    design to build. Refused loudly rather than a silent generic no-op."""
    from unittest import mock

    from market_sim.model.reserves.spec import get_reserve_design

    cfg = mock.Mock()
    cfg.iso = "SOCO"
    with pytest.raises(ValueError, match="SOCO clears no ancillary-service market"):
        get_reserve_design(cfg, mock.Mock(), 24, ["SOCO_AL", "SOCO_GA", "SOCO_MS"])


# --- Card S7: McIntosh CAES -------------------------------------------------


def test_caes_maps_to_gas_ct():
    assert (
        _map_fuel_type("Natural Gas with Compressed Air Storage", "NG", "CE")
        == "gas_ct"
    )


def test_storage_loader_skips_caes_everywhere():
    """The one CAES unit nationally (McIntosh, plant 7063) is a 25 MW gas CT in
    the thermal fleet; the storage loader must never also carry it, for SOCO
    or for any other region's footprint."""
    import inspect

    from market_sim.model import storage

    src = inspect.getsource(storage.load_eia860_storage)
    assert "Compressed Air" in src


def test_soco_storage_fleet_excludes_mcintosh():
    """McIntosh (110 MW nameplate, Alabama) is the only energy-storage-
    schedule row in SOCO_AL; with the CAES skip the 2024 SOCO storage fleet
    is the two battery aggregates (SOCO_GA ~146 MW, SOCO_MS ~1.5 MW) plus the
    Georgia pumped-storage aggregate from the generator schedule, and nothing
    in Alabama. The other seven regions have no CAES row, so the skip is a
    no-op there by construction (source pin above)."""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.storage import load_eia860_storage

    try:
        units = load_eia860_storage("SOCO", 2024, ScenarioConfig(iso="SOCO"))
    except FileNotFoundError:
        pytest.skip("SOCO EIA-860 storage source not hydrated")
    assert units, "SOCO 2024 storage fleet is empty"
    assert "SOCO_AL" not in {u.zone for u in units}
    assert {u.zone for u in units} <= {"SOCO_GA", "SOCO_MS"}
    batteries = [u for u in units if u.tech_name != "pumped_storage"]
    assert 100.0 < sum(u.power_cap_mw for u in batteries) < 200.0


# --- The registered fleet, where the curated parquet is present -------------


def test_soco_thermal_fleet_carries_mcintosh_at_25_mw_and_hillabee():
    from market_sim.data.fleet.eia860 import load_fleet_from_csv

    try:
        gens = load_fleet_from_csv("SOCO")
    except FileNotFoundError:
        pytest.skip("SOCO rows absent from the curated EIA-860 parquet")
    by_plant = {}
    for g in gens:
        by_plant.setdefault(int(g.plant_code), []).append(g)
    mcintosh = [g for g in by_plant.get(7063, []) if g.fuel_type == "gas_ct"]
    assert mcintosh, "McIntosh CAES (plant 7063) missing from the SOCO thermal fleet"
    assert any(abs(g.pmax_mw - 25.0) < 0.5 for g in mcintosh)
    # Hillabee (plant 55411) is inside the SOCO BA footprint (Alabama zone).
    assert by_plant.get(55411), "Hillabee (55411) missing"
    assert {g.zone for g in by_plant[55411]} == {"SOCO_AL"}
    # Vogtle 3 / 4 carry their own CODs (SOCO-15 COD seam), 2023-07 / 2024-04.
    vogtle = by_plant.get(649, [])
    assert vogtle, "Vogtle (649) missing"
    new_units = sorted(
        (g.online_year, g.online_month) for g in vogtle if g.online_year >= 2023
    )
    assert new_units == [(2023, 7), (2024, 4)]


# --- Seam repair 1: COD-aware nuclear-CF denominator ------------------------


@pytest.mark.parametrize("iso", INCUMBENTS)
def test_nuclear_cf_derive_is_a_noop_for_the_incumbents(iso):
    """The derive now divides by the MONTH-ONLINE nuclear pmax (a Vogtle 3/4
    unit counts only from its own COD). No incumbent region has a nuclear
    unit with a 2023-2025 COD (NWPP's one reactor, Columbia, is 1984), so
    every committed table re-derives byte-identically (rule 23
    [R-FROZEN-DERIVE]: no residual moved this)."""
    from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR

    try:
        from scripts.data import derive_nuclear_monthly_cf as d
    except ImportError:  # pragma: no cover - scripts package not importable
        pytest.skip("scripts.data not importable")
    if iso not in NUCLEAR_MONTHLY_CF_BY_YEAR:
        pytest.skip(f"{iso} carries no by-year nuclear table")
    for year in NUCLEAR_MONTHLY_CF_BY_YEAR[iso]:
        try:
            _codes, online_pmax = d._nuclear_fleet(iso, year)
        except (FileNotFoundError, SystemExit):
            pytest.skip(f"{iso} fleet source not hydrated")
        # Every month's online pmax equals the whole-fleet pmax: no unit is
        # COD-gated inside the year, so the denominator is the flat pmax.
        assert len({round(float(v), 3) for v in online_pmax}) == 1, (iso, year)


def test_soco_nuclear_denominator_is_cod_gated_in_2023_and_2024():
    """Vogtle 3 (2023-07) and 4 (2024-04) enter the SOCO denominator in their
    own COD months — the case the seam repair exists for."""
    try:
        from scripts.data import derive_nuclear_monthly_cf as d
    except ImportError:  # pragma: no cover
        pytest.skip("scripts.data not importable")
    try:
        _codes, pm23 = d._nuclear_fleet("SOCO", 2023)
        _codes, pm24 = d._nuclear_fleet("SOCO", 2024)
        _codes, pm25 = d._nuclear_fleet("SOCO", 2025)
    except (FileNotFoundError, SystemExit):
        pytest.skip("SOCO fleet source not hydrated")
    assert pm23[5] < pm23[6] and len({round(v, 3) for v in pm23[6:]}) == 1
    assert pm24[2] < pm24[3] and len({round(v, 3) for v in pm24[3:]}) == 1
    assert len({round(v, 3) for v in pm25}) == 1
    assert pm23[0] < pm24[0] < pm25[0]
