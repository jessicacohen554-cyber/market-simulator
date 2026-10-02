"""Reader over the ``stb-coal-loadings`` clean datatype (STB EP 724 Category 9).

Weekly Class I coal unit-train loadings, the carrier's filed plan and the realised loadings, by coal
production region. This is a rail-service (supply-side) condition, not a plant outcome: the ratio of
realised to planned loadings is set by the carrier's crews, power and network.

Rule 13 ``[R-MEASURED]``: admissible as a measured service condition of the year, like an outage
window, because a forward year can carry it as a rail-service scenario. No function here turns it
into a plant's generation or a burn target.
"""

from __future__ import annotations

import sys

import pandas as pd

from market_sim.config import paths

_DATATYPE = "stb-coal-loadings"


def _read_clean():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily (it lives under ``scripts/``)."""
    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io

    return clean_io


def load_coal_loadings() -> pd.DataFrame:
    """Return the long frame ``carrier, region, measure ('plan'|'actual'), week, value``.

    Raises ``FileNotFoundError`` (via the clean seam) when the datatype is not curated; run
    ``scripts/data/curate_stb_coal_loadings.py``.
    """
    return _read_clean().read_clean(_DATATYPE)


def annual_loadings_ratio(carriers: tuple[str, ...], region: str) -> pd.DataFrame:
    """Return per calendar year the summed ``plan``, ``actual`` and ``ratio = actual / plan``.

    Weeks are summed over ``carriers`` before the ratio is taken, so a carrier with a larger plan
    weighs more. Only weeks where every listed measure is filed contribute.
    """
    d = load_coal_loadings()
    d = d[d.carrier.isin(carriers) & (d.region == region)]
    w = d.pivot_table(
        index="week", columns="measure", values="value", aggfunc="sum"
    ).dropna()
    yr = w.groupby(w.index.year)[["plan", "actual"]].sum()
    yr["ratio"] = yr.actual / yr.plan
    yr.index.name = "year"
    return yr
