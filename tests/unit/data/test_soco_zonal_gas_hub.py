"""SOCO zonal gas-hub table wiring (lane SOCO-32).

The table is a **registered measured input, not an armed mechanism**: this lane
adds no ``ScenarioConfig`` field (plan §7 gate G8), so nothing in a solve reads
it yet. What these tests pin is that it will be read *correctly* when SOCO-40 or
a later lever arms an applier, and — the load-bearing part — that the route
choice behind the numbers cannot quietly regress to the state-series one the
zone map makes wrong.

The schema tests run against synthetic tables in a tempdir (plan §7 gate G17);
the tests that inspect the committed table are marked ``fulldata`` and skip when
it is not hydrated.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fuel import SOCO_ZONAL_GAS_HUB_PATH
from market_sim.data.fuel.basis import meanzero

_COLUMNS = ["zone", "year", "basis_vs_hh_usd_mmbtu", "hub", "source"]
_ZONES = ("SOCO_AL", "SOCO_GA", "SOCO_MS")
_YEARS = (2023, 2024, 2025)


def _write_hub_table(path, rows):
    """Write a hub table in the shared MISO/PJM/CAISO schema."""
    pd.DataFrame(
        [
            {
                "zone": zone,
                "year": year,
                "basis_vs_hh_usd_mmbtu": basis,
                "hub": "test hub",
                "source": "synthetic fixture",
            }
            for zone, year, basis in rows
        ],
        columns=_COLUMNS,
    ).to_csv(path, index=False)


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------


def test_path_is_registered_and_named_like_its_siblings():
    """SOCO's table sits beside the other regions' in the same registry module."""
    assert SOCO_ZONAL_GAS_HUB_PATH is meanzero.SOCO_ZONAL_GAS_HUB_PATH
    assert SOCO_ZONAL_GAS_HUB_PATH.name == "soco_zonal_gas_hub.csv"


def test_the_shared_loader_reads_the_shared_schema(tmp_path):
    """No new parsing code: the sibling loader reads SOCO's table as-is."""
    path = tmp_path / "soco_zonal_gas_hub.csv"
    _write_hub_table(
        path,
        [("SOCO_AL", 2023, 0.955), ("SOCO_GA", 2023, 0.539), ("SOCO_MS", 2023, 0.166)],
    )
    assert meanzero._zonal_gas_basis_by_zone(path, 2023) == {
        "SOCO_AL": 0.955,
        "SOCO_GA": 0.539,
        "SOCO_MS": 0.166,
    }


def test_a_year_with_no_rows_reads_as_absent(tmp_path):
    """A year the table does not cover returns None, so an applier no-ops.

    This is the failure mode SPP-32 documented and this table avoids by
    construction: a PARTIAL year (some zones present, others missing) would let
    the missing zones default to 0.0 at the call site and fabricate a spread out
    of a publication gap. SOCO's EIA-923 route covers all three zones in all
    three years, so the partial case cannot arise — but the loader's behaviour
    for a genuinely absent year is still what an applier relies on.
    """
    path = tmp_path / "soco_zonal_gas_hub.csv"
    _write_hub_table(path, [("SOCO_AL", 2023, 0.955)])
    assert meanzero._zonal_gas_basis_by_zone(path, 2024) is None


def test_no_applier_is_armed_for_soco():
    """G8: no ScenarioConfig field reads this table, so no cache key moves."""
    from market_sim.config.scenarios import ScenarioConfig

    # SOCO+gas fields that are NOT hub-table appliers, each confirmed not to
    # read SOCO_ZONAL_GAS_HUB_PATH. soco_gas_st_campaign_commitment (soco-53d,
    # 1b289fcf, 2026-09-19) is a gas-STEAM commitment floor read only by
    # pipeline/commitment.py; the name heuristic below caught it (Y-30).
    not_hub_appliers = {"soco_gas_st_campaign_commitment"}
    fields = set(vars(ScenarioConfig()).keys()) - not_hub_appliers
    assert not any("soco" in name and "gas" in name for name in fields)


# ---------------------------------------------------------------------------
# The committed table
# ---------------------------------------------------------------------------


@pytest.mark.fulldata
def test_committed_table_covers_every_zone_and_year():
    """Three zones x three backcast years, with no hole for an applier to fill.

    The whole reason this lane took the EIA-923 per-plant route rather than
    SOCO-12's state series: EIA publishes no state series for GA or MS after
    2024-12, so a state-series table would have stopped mid-backcast.
    """
    if not SOCO_ZONAL_GAS_HUB_PATH.exists():
        pytest.skip("soco_zonal_gas_hub.csv not hydrated")
    frame = pd.read_csv(SOCO_ZONAL_GAS_HUB_PATH)
    assert list(frame.columns) == _COLUMNS
    assert set(frame["zone"]) == set(_ZONES)
    for year in _YEARS:
        assert set(frame.loc[frame["year"] == year, "zone"]) == set(_ZONES)


@pytest.mark.fulldata
def test_committed_zones_are_the_model_zones():
    """Every row names a real SOCO model zone."""
    if not SOCO_ZONAL_GAS_HUB_PATH.exists():
        pytest.skip("soco_zonal_gas_hub.csv not hydrated")
    frame = pd.read_csv(SOCO_ZONAL_GAS_HUB_PATH)
    assert set(frame["zone"]) <= set(get_iso_config("SOCO").zone_names)


@pytest.mark.fulldata
def test_committed_table_carries_its_provenance_on_every_row():
    """Rule 5 [R-NO-MAGIC]: each value names its source and its construction."""
    if not SOCO_ZONAL_GAS_HUB_PATH.exists():
        pytest.skip("soco_zonal_gas_hub.csv not hydrated")
    frame = pd.read_csv(SOCO_ZONAL_GAS_HUB_PATH)
    assert frame["source"].str.contains("EIA-923").all()
    assert frame["source"].str.contains("derive_soco_zonal_gas_hub.py").all()
    assert frame["hub"].notna().all()


@pytest.mark.fulldata
def test_the_alabama_row_declares_its_two_delivered_markets():
    """SOCO_AL spans two gas markets and says so on the row.

    Card S3 puts the six SERC Florida-panhandle plants in SOCO_AL; the two that
    burn gas are a fifth of the zone's burn at a ~$1.10/MMBtu premium. That is
    the whole reason the state series is the wrong input here, so a future
    rebuild that silently drops the disclosure would also have dropped the
    reason.
    """
    if not SOCO_ZONAL_GAS_HUB_PATH.exists():
        pytest.skip("soco_zonal_gas_hub.csv not hydrated")
    frame = pd.read_csv(SOCO_ZONAL_GAS_HUB_PATH)
    alabama = frame[frame["zone"] == "SOCO_AL"]
    assert alabama["hub"].str.startswith("MIXED").all()
    assert alabama["source"].str.contains("FL-panhandle").all()


@pytest.mark.fulldata
def test_the_measured_spread_is_material_and_signed_consistently():
    """Mississippi is the cheap zone in every year, and the spread is real.

    Reported rather than gated: the mean-zero applier re-centres the level, so
    what an armed run would see is the cross-zonal spread, which measures
    0.79 / 0.47 / 0.54 $/MMBtu. If a rebuild ever collapsed it to ~0 the table
    would have stopped saying anything, which is worth failing on.
    """
    if not SOCO_ZONAL_GAS_HUB_PATH.exists():
        pytest.skip("soco_zonal_gas_hub.csv not hydrated")
    frame = pd.read_csv(SOCO_ZONAL_GAS_HUB_PATH)
    for year in _YEARS:
        row = frame[frame["year"] == year].set_index("zone")["basis_vs_hh_usd_mmbtu"]
        assert row["SOCO_MS"] == row.min()
        assert row.max() - row.min() > 0.3
