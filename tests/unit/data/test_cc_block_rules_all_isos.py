"""W0 E.8 / E.3: the miso-126 steam-part and miso-272 block predicates run everywhere."""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config.paths import cc_capacity_reconcile_path
from market_sim.config.plant_taxonomy import CC_STEAM_PART_REPAIR_ISOS
from market_sim.data.fleet import eia860 as e860

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")


def test_steam_part_repair_covers_every_iso():
    assert set(ISOS) <= set(CC_STEAM_PART_REPAIR_ISOS)


def _sheet(tmp_path, ca_fuel: str):
    pd.DataFrame(
        {
            "Plant Code": [7, 7, 7],
            "Generator ID": ["CT1", "CT2", "CA1"],
            "Prime Mover": ["CT", "CT", "CA"],
            "Unit Code": ["1", "1", "1"],
            "Status": ["OP", "OP", "OP"],
            "Nameplate Capacity (MW)": [100.0, 100.0, 100.0],
            "Summer Capacity (MW)": [None, None, 270.0],
            "Energy Source 1": ["NG", "NG", ca_fuel],
        }
    ).to_parquet(tmp_path / "eia860_generator_operable.parquet")
    e860._cc_block_summer_ratings.cache_clear()


def _frame():
    return pd.DataFrame(
        {
            "plant_id": [7, 7, 7],
            "generator_id": ["CT1", "CT2", "CA1"],
            "net_summer_capacity_mw": [None, None, 270.0],
            "nameplate_capacity_mw": [100.0, 100.0, 100.0],
        }
    )


@pytest.mark.parametrize("iso", ISOS)
def test_non_ng_block_same_result_in_every_iso(tmp_path, iso):
    _sheet(tmp_path, "SGC")
    out = e860._apply_cc_block_summer_rating(_frame(), tmp_path, iso)
    assert out["net_summer_capacity_mw"].tolist() == pytest.approx([90.0] * 3)


@pytest.mark.parametrize("iso", ISOS)
def test_ng_block_reconciled_exactly_where_no_measured_peak_table(tmp_path, iso):
    _sheet(tmp_path, "NG")
    out = e860._apply_cc_block_summer_rating(_frame(), tmp_path, iso)
    reconciled = out["net_summer_capacity_mw"].notna().all()
    assert reconciled == (not cc_capacity_reconcile_path(iso).exists())
