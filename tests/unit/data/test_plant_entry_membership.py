"""Plant-grain ENTRY membership shared by the LP fleet and the benchmark (R-ERCOT-12).

``constants.ISO_PLANT_ENTRIES`` registers Frontera Energy Center (55098) as
outside ERCOT until hour-ending UTC 2023-04-13 06:00 (it exported to CFE).
``market_sim.data.ba_membership`` reads it for the fleet hour mask, the EIA-923
month split and the CAMPD backfill input, so the three stay on one boundary
(rule 19). Every other region reads an empty registry and is byte-identical.
"""

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import ISO_PLANT_ENTRIES
from market_sim.data import ba_membership as bm
from tests.helpers import REPO_ROOT

_HAVE_930 = any((REPO_ROOT / "data" / "raw").glob("eia-930*"))


def test_registry_is_frontera_only():
    assert ISO_PLANT_ENTRIES == {"ERCOT": {55098: "2023-04-13 06:00"}}


def test_non_members_by_year():
    for y in (2019, 2020, 2021, 2022):
        assert bm.plant_entry_non_members("ERCOT", y) == frozenset({55098})
    for y in (2023, 2024, 2025):
        assert bm.plant_entry_non_members("ERCOT", y) == frozenset()
    assert bm.plant_entry_non_members("ERCOT", None) == frozenset()
    for iso in ("SOCO", "PJM", "MISO"):
        assert bm.plant_entry_non_members(iso, 2020) == frozenset()


def test_unregistered_region_is_untouched():
    df = pd.DataFrame({"plant_id": [55098], "hour": [0], "net_mw": [100.0]})
    assert bm.zero_pre_entry_campd(df, "PJM", 2020) is df
    assert bm.plant_entry_first_inside_row("PJM", 2020) == {}
    assert bm.plant_entry_month_share("PJM", 2020) == {}


def test_campd_zeroed_whole_year_before_entry_year_keeps_rows():
    df = pd.DataFrame(
        {"plant_id": [55098, 55098, 3470], "hour": [0, 1, 0], "net_mw": [5.0, 6.0, 7.0]}
    )
    out = bm.zero_pre_entry_campd(df, "ERCOT", 2021)
    # rows are kept (the missing-month fill reads series by position)
    assert len(out) == 3
    assert out["net_mw"].tolist() == [0.0, 0.0, 7.0]
    assert bm.zero_pre_entry_campd(df, "ERCOT", 2024) is df


@pytest.mark.skipif(not _HAVE_930, reason="EIA-930 not hydrated")
def test_entry_year_split_on_region_clock():
    # Operating day 2023-04-13 HE01 CDT: local-year row 2447 (Jan 1 .. Apr 12
    # = 102 days, less the spring-forward hour).
    assert bm.plant_entry_first_inside_row("ERCOT", 2023) == {55098: 2447}
    assert bm.plant_entry_first_inside_row("ERCOT", 2021) == {55098: 2**31 - 1}
    assert bm.plant_entry_first_inside_row("ERCOT", 2024) == {}
    month, share = bm.plant_entry_month_share("ERCOT", 2023)[55098]
    assert month == 4 and 0.0 <= share <= 1.0
    hours = np.arange(8760)
    df = pd.DataFrame({"plant_id": 55098, "hour": hours, "net_mw": 1.0})
    out = bm.zero_pre_entry_campd(df, "ERCOT", 2023)
    # CAMPD is local standard hour-beginning: CST 2023-04-12 23:00 is the
    # first inside hour (hour-ending UTC 06:00): 102 days x 24 - 1 = 2447.
    first = int(np.argmax(out["net_mw"].to_numpy() > 0))
    assert first == 2447
    assert out["net_mw"].iloc[first:].eq(1.0).all()
