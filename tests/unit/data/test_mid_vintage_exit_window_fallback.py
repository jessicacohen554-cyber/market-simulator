"""R-NEISO: mid-vintage-year exits for a vintage with no Retired-and-Canceled sheet.

``vintage_2023`` / ``vintage_2024`` ship no retired sheet, so the SPP-48 channel
used to return ``None`` there and a plant retiring DURING that year vanished from
the fleet. The fallback reads the canonical whole-plant retiree parquet with the
same selection rule (retired in the solved year, in the region, plant absent
from the vintage's operable sheet).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from market_sim.data.fleet import eia860
from market_sim.data.fleet.models import (
    EIA_860_PARQUET_NAME,
    EIA_860_RETIRED_WINDOW_PARQUET_NAME,
)


def _window_rows() -> pd.DataFrame:
    base = {
        "state": "MA",
        "technology": "NGCC",
        "energy_source": "NG",
        "prime_mover": "CT",
        "nameplate_capacity_mw": 250.0,
        "net_summer_capacity_mw": 225.0,
        "operating_year": 2003,
        "planned_retirement_month": 6,
        "status": "RE",
        "heat_rate": 7.3,
        "operating_month": 1,
    }
    rows = [
        # retired during 2024, plant absent from the vintage -> carried
        {
            **base,
            "plant_id": 1588,
            "generator_id": "GT81",
            "plant_name": "M",
            "balancing_authority_code": "ISNE",
            "planned_retirement_year": 2024,
        },
        # retired during 2024 but plant survives in the vintage -> partial channel's, not this one
        {
            **base,
            "plant_id": 7000,
            "generator_id": "1",
            "plant_name": "S",
            "balancing_authority_code": "ISNE",
            "planned_retirement_year": 2024,
        },
        # retired in 2023 -> did not run in 2024
        {
            **base,
            "plant_id": 563,
            "generator_id": "11",
            "plant_name": "SM",
            "balancing_authority_code": "ISNE",
            "planned_retirement_year": 2023,
        },
        # other region
        {
            **base,
            "plant_id": 9000,
            "generator_id": "1",
            "plant_name": "X",
            "balancing_authority_code": "NYIS",
            "planned_retirement_year": 2024,
        },
    ]
    return pd.DataFrame(rows)


def _layout(tmp: Path, with_retired_sheet: bool) -> Path:
    canon = tmp / "eia-860"
    vint = canon / "vintage_2024"
    vint.mkdir(parents=True)
    _window_rows().to_parquet(canon / EIA_860_RETIRED_WINDOW_PARQUET_NAME)
    pd.DataFrame({"plant_id": [7000, 1234]}).to_parquet(vint / EIA_860_PARQUET_NAME)
    pd.DataFrame(
        {"Plant Code": [1588, 7000], "Balancing Authority Code": ["ISNE", "ISNE"]}
    ).to_parquet(vint / eia860._PLANT_PARQUET_NAME)
    if with_retired_sheet:
        pd.DataFrame(
            {"Plant Code": [], "Generator ID": [], "Retirement Year": []}
        ).to_parquet(vint / eia860._RETIRED_CANCELED_PARQUET_NAME)
    return vint


def test_fallback_selects_only_whole_plant_exits_of_the_solved_year(tmp_path):
    vint = _layout(tmp_path, with_retired_sheet=False)
    with patch("market_sim.data.fleet.EIA_860_DIR", tmp_path / "eia-860"):
        out = eia860._mid_vintage_exit_rows(vint, ("ISNE",), 2024)
    assert out is not None
    assert list(out["plant_id"]) == [1588]
    assert set(out["status"]) == {"OP"}
    # carries the unit's own retirement month and its joined heat rate
    assert int(out["planned_retirement_month"].iloc[0]) == 6
    assert float(out["heat_rate"].iloc[0]) == 7.3


def test_fallback_not_taken_when_the_vintage_has_a_retired_sheet(tmp_path):
    vint = _layout(tmp_path, with_retired_sheet=True)
    with (
        patch("market_sim.data.fleet.EIA_860_DIR", tmp_path / "eia-860"),
        patch.object(eia860, "_mid_vintage_exit_rows_from_window") as fb,
    ):
        try:
            eia860._mid_vintage_exit_rows(vint, ("ISNE",), 2024)
        except Exception:
            pass  # the stub retired sheet is not a real one; only the routing matters
    fb.assert_not_called()


def test_canonical_snapshot_is_still_inert(tmp_path):
    canon = tmp_path / "eia-860"
    canon.mkdir()
    _window_rows().to_parquet(canon / EIA_860_RETIRED_WINDOW_PARQUET_NAME)
    with patch("market_sim.data.fleet.EIA_860_DIR", canon):
        assert eia860._mid_vintage_exit_rows(canon, ("ISNE",), 2024) is None
