"""FERC Form 714 hourly planning-area demand — the measured member substitute.

FERC Form 714 Part III Schedule 2 is each planning area's own hourly load
report, filed annually and independent of EIA-930. It is the measured source
the NWPP pool frame falls back to when a member balancing authority's EIA-930
``Demand (Adjusted)`` series carries a hole longer than the pool is allowed to
bridge by interpolation
(:func:`market_sim.data.eia930.frames._pool_hourly_frame`, lane NWPP-NEXT).

The committed store is ``data/raw/ferc-714/`` (README + SHA256SUMS): one CSV
per respondent, extracted verbatim from Catalyst Cooperative's PUDL
``out_ferc714__hourly_planning_area_demand`` table — ``demand_reported_mwh``
only, never PUDL's ``demand_imputed_pudl_mwh`` (an imputation is a model, not a
measurement, rule 13). Timestamps are PUDL's ``datetime_utc``, which lands on
the EIA-930 ``UTC time`` stamp at lag 0 wherever the two report one basis
(PSEI 2021-2024: median ratio 0.996-0.999, first-difference r 0.956-0.972 at
lag 0 against 0.79-0.83 at ±1 h).
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from market_sim.config.paths import FERC_714_DIR

# EIA-930 balancing-authority code -> committed FERC 714 respondent extract.
# PSEI = Puget Sound Energy, Inc., FERC 714 respondent_id 129 (csv id 240,
# XBRL C000171, EIA utility code 15500) — PUDL ``core_ferc714__respondent_id``.
FERC714_MEMBER_FILES: dict[str, str] = {
    "PSEI": "psei_hourly_planning_area_demand_2018_2024.csv",
}


@lru_cache(maxsize=8)
def load_ferc714_hourly_demand(ba_code: str) -> pd.Series | None:
    """Return a member's FERC 714 hourly demand (MW) indexed by UTC, or ``None``.

    Args:
        ba_code: EIA-930 balancing-authority code (a key of
            :data:`FERC714_MEMBER_FILES`).

    Returns:
        ``demand_reported_mwh`` as a float Series on a naive-UTC
        ``DatetimeIndex`` (duplicates dropped, sorted), or ``None`` when the
        member has no registered extract or its file is absent.
    """
    name = FERC714_MEMBER_FILES.get(ba_code)
    if name is None:
        return None
    path = FERC_714_DIR / name
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["datetime_utc", "demand_reported_mwh"])
    idx = pd.DatetimeIndex(pd.to_datetime(df["datetime_utc"]))
    s = pd.Series(df["demand_reported_mwh"].to_numpy(dtype=float), index=idx)
    return s[~s.index.duplicated()].sort_index()
