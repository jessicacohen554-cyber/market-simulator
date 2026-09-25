"""PJM-NEXT: ``fleet_zone_vintage_coords`` — fallback-branch zoning from the active vintage.

A plant absent from the eGRID-2023 zone lookup falls to the ISO's pinned
default zone. With the flag armed the fleet first zones it from the ACTIVE
EIA-860 vintage's own plant coordinates; an eGRID-placed plant is never
re-zoned, and with the flag off the assignment is unchanged.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from market_sim.data import zone_assignment as za
from market_sim.data.fleet import eia860


@pytest.fixture(autouse=True)
def _disarm():
    za.set_fleet_zone_vintage_coords(False)
    za._vintage_coords_zone_lookup_cached.cache_clear()
    yield
    za.set_fleet_zone_vintage_coords(False)
    za._vintage_coords_zone_lookup_cached.cache_clear()


def _records() -> list[dict]:
    return [{"plant_id": 1}, {"plant_id": 2}, {"plant_id": 3}]


def _assign(vintage: dict[int, str]) -> list[str]:
    with (
        patch.object(za, "build_zone_lookup", return_value={1: "PJM_EMAAC"}),
        patch.object(za, "vintage_coords_zone_lookup", return_value=vintage),
    ):
        return eia860._assign_zones(_records(), "PJM", None)


def test_off_is_the_fallback_path() -> None:
    zones = _assign({2: "PJM_ComEd", 1: "PJM_ComEd"})
    assert zones == ["PJM_EMAAC", za._LARGEST_ZONE["PJM"], za._LARGEST_ZONE["PJM"]]


def test_on_zones_unlocated_plants_from_vintage_coords() -> None:
    za.set_fleet_zone_vintage_coords(True)
    zones = _assign({2: "PJM_ComEd", 1: "PJM_ComEd"})
    # plant 1 keeps its eGRID zone (never re-zoned); 2 takes the vintage zone;
    # 3 is in neither and still falls back.
    assert zones == ["PJM_EMAAC", "PJM_ComEd", za._LARGEST_ZONE["PJM"]]


def test_vintage_lookup_reads_the_active_directory(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "Plant Code": [884],
            "Balancing Authority Code": ["PJM"],
            "Latitude": [41.6334],
            "Longitude": [-88.0629],
            "State": ["IL"],
        }
    ).to_parquet(tmp_path / za._EIA860_PLANT_PATH.name)
    with patch("market_sim.config.paths.active_eia860_dir", return_value=tmp_path):
        lk = za.vintage_coords_zone_lookup("PJM")
    assert lk == {884: "PJM_ComEd"}
