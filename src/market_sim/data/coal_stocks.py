"""Reader over the ``coal-stocks`` clean datatype (plant-level monthly coal stock).

The measured fuel-INVENTORY state for coal. Coal units in this model carry
take-or-pay and must-run FLOORS and no CEILING, and the only fuel-inventory
mechanism in the codebase is NEISO winter oil
(:mod:`market_sim.data.winter_fuel_inventory`) — so nothing today can represent
"the fleet drew its stockpile down in one year and could only burn what it
received in the next". ``docs/FINDING-miso256-2022-passthrough-inversion-
2026-09-13.md`` §4 identified that as the mechanism behind MISO's flat +4.3 GW
2022 coal block.

**There is no LP consumer yet, and no ``ScenarioConfig`` flag.** This module is
the read seam only: it serves the zero-LP falsification in
``docs/FINDING-miso258-coal-stock-falsification-2026-09-14.md`` and whatever
mechanism the owner later charters. Nothing here changes a solve.

RULE 13 ``[R-MEASURED]`` — THE TRAP, STATED AT THE SEAM. ``ending_stock_tons``
is a measured STATE, and its 12-month path embeds the very burn a backcast is
being asked to reproduce::

    ending[m] = ending[m-1] + receipts[m] - burn[m]

So sizing year *Y*'s coal budget from year *Y*'s own stock path (or its own
receipts) is pinning the backcast to the actual, which rule 13 forbids
absolutely. :func:`opening_stock_tons` exists to make the admissible read the
easy one: the opening stock is the prior year's December state, which for a
forecast year is simply the model's own carried-forward inventory — the same
role a storage SOC boundary plays. A delivery rate must likewise come from
years ``<= Y-1``; the NEISO oil precedent is explicit that F923 *receipts* are
"a measured deliveries-to-tank OUTCOME inadmissible under CLAUDE.md #13", so
the target year's receipts are not a delivery rate either.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from market_sim.config import paths

_DATATYPE = "coal-stocks"


def _read_clean():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily.

    ``clean_io`` lives under ``scripts/`` (not an installed package), so the repo
    root goes on ``sys.path`` the way the curation scripts and
    :mod:`market_sim.data.winter_fuel_inventory` do.
    """
    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io

    return clean_io


def load_coal_stocks(years: list[int] | None = None) -> pd.DataFrame:
    """Return plant x rank x month ending coal stocks for ``years``.

    Args:
        years: Calendar years to load. ``None`` loads every curated year.

    Returns:
        Frame on the ``coal-stocks`` schema grain, empty if no year is curated.
    """
    clean_io = _read_clean()
    frames: list[pd.DataFrame] = []
    root = paths.CLEAN_DIR / _DATATYPE
    if not root.is_dir():
        return pd.DataFrame()
    for path in sorted(root.glob(f"{_DATATYPE}_*.parquet")):
        year = int(Path(path).stem.rsplit("_", 1)[1])
        if years is not None and year not in years:
            continue
        frames.append(clean_io.read_clean(_DATATYPE, year=year))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def footprint_stock_tons(
    plant_ids: set[int] | list[int], years: list[int] | None = None
) -> pd.DataFrame:
    """Aggregate month-ending coal stock over one ISO footprint.

    ISO scoping is a READ-TIME join, never a partition of the datatype, so one
    curated national series serves every coal ISO with no per-ISO branch
    (rule 25 ``[R-ISO-SCOPE]``). Callers pass the plant ids their own fleet
    resolves — the modelled footprint — rather than trusting the EIA
    ``balancing_authority_code``, which disagrees with the modelled zone at
    several seams.

    Args:
        plant_ids: EIA plant codes making up the footprint.
        years: Calendar years to include; ``None`` for every curated year.

    Returns:
        Frame indexed ``(year, month)`` with column ``ending_stock_tons``.
    """
    df = load_coal_stocks(years)
    if df.empty:
        return df
    sel = df[df["plant_id"].isin(set(int(p) for p in plant_ids))]
    return (
        sel.groupby(["year", "month"], as_index=False)["ending_stock_tons"]
        .sum()
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )


def opening_stock_tons(plant_ids: set[int] | list[int], year: int) -> float | None:
    """Return the footprint's opening coal stock for ``year``.

    The December ending stock of ``year - 1`` — a prior-year state, and the ONLY
    stock read that is admissible as an input to a ``year`` budget under rule 13
    (see the module docstring). Returns ``None`` when the prior year is not
    curated, so a caller must handle the gap rather than silently substituting
    the target year's own stock.
    """
    prior = footprint_stock_tons(plant_ids, years=[year - 1])
    if prior.empty:
        return None
    dec = prior[prior["month"] == 12]
    return float(dec["ending_stock_tons"].sum()) if not dec.empty else None
