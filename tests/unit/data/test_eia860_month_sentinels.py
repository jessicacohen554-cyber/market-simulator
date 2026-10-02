"""W0 E.8: EIA-860 ``Operating Month`` 88 / 99 means "unknown", never December."""

from __future__ import annotations

import pandas as pd

from market_sim.data import cod_ramp
from market_sim.data.fleet import eia860 as e860


def test_sentinels_resolve_to_the_ramp_fallback():
    out = cod_ramp.resolve_eia860_month(pd.Series([88, 99, 3, None, 13]))
    assert out.tolist() == [
        cod_ramp.COD_FALLBACK_MONTH,
        cod_ramp.COD_FALLBACK_MONTH,
        3,
        cod_ramp.COD_FALLBACK_MONTH,
        cod_ramp.COD_FALLBACK_MONTH,
    ]


def test_generator_online_month_reads_sentinel_as_mid_year():
    assert e860._operating_month(88) == cod_ramp.COD_FALLBACK_MONTH
    assert e860._operating_month("99") == cod_ramp.COD_FALLBACK_MONTH
    assert e860._operating_month(5) == 5
    # A blank cell keeps the loader's long-standing January default.
    assert e860._operating_month(None) == 1


def test_unit_month_join_passes_the_sentinel_through(tmp_path):
    pd.DataFrame(
        {
            "Plant Code": [1, 1, 2],
            "Generator ID": ["A", "B", "C"],
            "Operating Month": [99, 4, None],
        }
    ).to_parquet(tmp_path / "eia860_generator_operable.parquet")
    months = e860._operating_month_by_unit(tmp_path)
    assert months == {(1, "A"): 99, (1, "B"): 4}
    assert e860._operating_month(months[(1, "A")]) == cod_ramp.COD_FALLBACK_MONTH
