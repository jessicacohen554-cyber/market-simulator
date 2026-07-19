"""NEISO measured operable-capacity / generation-outage availability overlay.

The ISO-NE analogue of the ERCOT measured DAM class-day thermal availability
(:func:`market_sim.data.outages.ercot_thermal_dam_availability_series`), for the
NEISO backcast to use IN PLACE OF the CAMPD-derived unit-outage fallback
(``campd-unit-outages-NEISO.csv``). Source: the ISO-NE Morning Report Section 3
"Operable Capacity Analysis" (committed per-year CSVs
``data/raw/neiso-operable-capacity/neiso_operable_capacity_<YYYY>.csv`` -- the
ERCOT-analogue committed-CSV precedent, built by
``scripts/data/build_neiso_operable_capacity.py`` from the daily CSVs the sibling
``fetch_neiso_morning_report.py`` downloads).

**Grain.** ISO-NE publishes this at FLEET grain (it does not publish per-unit or
per-fuel availability -- only masked-asset DA offers). So, unlike the ERCOT
per-class DAM series, this yields ONE fleet thermal availability fraction per
day, which the fleet builder imposes on the covered dispatchable-thermal classes
together (:func:`market_sim.data.fleet.generators_to_fleet_arrays`, gated by
``ScenarioConfig.neiso_operable_capacity_availability``). This module (the data +
loader) is committed directly; the gate + the fleet application ship as
``docs/handoffs/patches/neiso-operable-capacity-wiring.patch`` -- the repo's
transport for edits to core files too large for the API-only push path -- and
apply after this branch merges.

**Admissibility (CLAUDE.md rules 13/14).** Every stored figure is a MW quantity
ISO-NE publishes -- a physical generation-outage / operable-capacity measurement
(planned maintenance + forced outages) that regenerates for a forward year from
forward maintenance/forced-outage drivers and responds to changed conditions.
The consumed availability FRACTION is a transparent ratio of those published
figures (``1 - outages / (CSO + EcoMax-above-CSO)``), never a price and never an
outcome rescaled onto the price/volume residual. Backcast-only, default OFF;
forecast keeps the statistical WEFOR/POF stack (the mode-aware seam).
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.outages import _hour_of_year

logger = logging.getLogger(__name__)

#: Committed operable-capacity directory (per-year CSVs built by
#: build_neiso_operable_capacity.py: neiso_operable_capacity_<YYYY>.csv).
NEISO_OPERABLE_CAPACITY_DIR = RAW_DATA_DIR / "neiso-operable-capacity"
#: Per-year CSV glob (four-digit year; excludes the gitignored daily/ pulls).
NEISO_OPERABLE_CAPACITY_GLOB = "neiso_operable_capacity_[0-9][0-9][0-9][0-9].csv"


@lru_cache(maxsize=None)
def load_operable_capacity_frame() -> pd.DataFrame | None:
    """Return the full daily operable-capacity frame, or ``None`` when absent.

    Concatenates the committed per-year CSVs (a faithful transcription of the
    Morning Report Section 3 figures, one row per delivery date), sorted by
    ``report_date``. Returns ``None`` when no per-year file is present. Cached
    read-only; callers must not mutate the result.
    """
    paths = sorted(NEISO_OPERABLE_CAPACITY_DIR.glob(NEISO_OPERABLE_CAPACITY_GLOB))
    if not paths:
        return None
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    df["report_date"] = pd.to_datetime(df["report_date"])
    return df.sort_values("report_date").reset_index(drop=True)


@lru_cache(maxsize=None)
def neiso_thermal_availability_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> np.ndarray:
    """Return a length-``hours`` measured fleet thermal availability fraction.

    Each covered delivery date contributes a flat 24-hour block of that day's
    measured availability fraction on the model's fixed non-leap 8760 clock
    (:func:`market_sim.data.outages._hour_of_year`; a leap year's Feb 29 row is
    dropped, the archive convention). Hours the Morning Report does not cover are
    ``NaN`` -- the caller keeps its statistical availability there. Returns an
    all-``NaN`` array when the parquet is absent or the year has no rows, so the
    caller degrades to the statistical model unchanged.

    The daily fraction is the published-figure outage rate

        avail(day) = 1 - outages / (CSO + EcoMax-above-CSO)

    i.e. one minus the day's generation outages and reductions (planned +
    forced) as a share of the obligated + additionally-offered operable capacity
    the identity ``H = A+B-C-...`` reduces from. Clipped to ``[0, 1]``; a day
    whose operable base is non-positive (never observed in the archive) is left
    uncovered.
    """
    out = np.full(hours, np.nan)
    df = load_operable_capacity_frame()
    if df is None:
        return out
    df = df[df["report_date"].dt.year == int(year)]
    if df.empty:
        return out
    for r in df.itertuples(index=False):
        base = (r.cso_mw or 0.0) + (r.capacity_additions_ecomax_gt_cso_mw or 0.0)
        outage = r.gen_outages_reductions_mw
        if not base > 0.0 or outage is None or pd.isna(outage):
            continue
        frac = float(np.clip(1.0 - float(outage) / float(base), 0.0, 1.0))
        mo, dy = int(r.report_date.month), int(r.report_date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        out[lo:hi] = frac
    return out
