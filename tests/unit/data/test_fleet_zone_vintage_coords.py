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


def test_vintage_lookup_reads_an_explicit_directory(tmp_path: Path) -> None:
    pd.DataFrame(
        {
            "Plant Code": [884],
            "Balancing Authority Code": ["PJM"],
            "Latitude": [41.6334],
            "Longitude": [-88.0629],
            "State": ["IL"],
        }
    ).to_parquet(tmp_path / za._EIA860_PLANT_PATH.name)
    other = tmp_path / "elsewhere"
    other.mkdir()
    with patch("market_sim.config.paths.active_eia860_dir", return_value=other):
        assert za.vintage_coords_zone_lookup("PJM", tmp_path) == {884: "PJM_ComEd"}


# Renewables: the same fallback admits wind/solar plants eGRID 2023 lacks
# (closeout W0 census: PJM 2024/2025 solar+wind dropped from the fleet).


def _wind_capacity(tmp_path: Path, vintage: dict[int, str]):
    from market_sim.data import renewables

    pd.DataFrame(
        {
            "Plant Code": [1, 2, 3],
            "Status": ["OP", "OP", "OP"],
            "Nameplate Capacity (MW)": [10.0, 20.0, 40.0],
            "Operating Year": [2020, 2020, 2020],
            "Operating Month": [1, 1, 1],
        }
    ).to_parquet(tmp_path / "eia860_wind_operable.parquet")
    seen: list[Path] = []

    def _vintage(iso: str, eia860_dir: Path | None = None) -> dict[int, str]:
        seen.append(Path(eia860_dir))
        return vintage

    with (
        patch.object(za, "build_zone_lookup", return_value={1: "A"}),
        patch.object(za, "vintage_coords_zone_lookup", side_effect=_vintage),
    ):
        monthly = renewables._eia860_monthly_capacity(
            "PJM", "wind", ["A", "B"], None, data_dir=tmp_path
        )
    return monthly, seen


def test_renewables_off_drops_plants_egrid_lacks(tmp_path: Path) -> None:
    monthly, seen = _wind_capacity(tmp_path, {1: "B", 2: "B"})
    assert seen == []  # the vintage lookup is never read while off
    assert monthly[:, 0].tolist() == [10.0, 0.0]


def test_renewables_on_admits_from_the_read_vintage(tmp_path: Path) -> None:
    za.set_fleet_zone_vintage_coords(True)
    monthly, seen = _wind_capacity(tmp_path, {1: "B", 2: "B"})
    # The plant coordinates come from the directory being read.
    assert seen == [tmp_path]
    # plant 1 keeps its eGRID zone A (never re-zoned); plant 2 (eGRID-absent)
    # is admitted to its vintage zone B; plant 3 is in neither and stays out.
    assert monthly[:, 0].tolist() == [10.0, 20.0]
    assert (monthly == monthly[:, :1]).all()
