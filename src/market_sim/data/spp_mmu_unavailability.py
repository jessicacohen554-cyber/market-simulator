"""SPP MMU offer-side and unreported-derate unavailability shares (SPP-106).

Armed by ``ScenarioConfig.spp_mmu_offer_unavailability`` (default off, SPP-only). Record:
``docs/records/spp/DESIGN-spp-106-offer-side-unavailability-2026-10-01.md`` §5 (carrier EX). The owner card
"Build EX anyway" was ruled on 2026-10-01.

Source: SPP MMU, *Unavailable Generation Capacity in SPP Markets: Causes and Impacts* (2025-12-19),
committed as ``data/raw/spp-mmu-unavailable-capacity`` (annual MW, 2020-2024; digitized, README).

The carrier REPLACES the keeper's flat GADS performance derate and flat summer class derate on every
fossil row (rule 19 [R-ONE-MECH]); those are skipped in ``data.fleet.arrays._availability_matrix``.
After the measured outage overlays have run, every fossil row then loses three bands:

* the MMU's "above emergency maximum" MW, as a share of rated conventional capacity, all year;
* the MMU's "between economic and emergency maximum" MW (reachable only in an emergency), same basis,
  all year;
* the MMU's unreported ambient derate MW-days (Fig 12), spread evenly over Jun-Sep as a share of the
  fleet's fossil pmax.

Every value is read from the table; there are zero fitted parameters (rule 21 [R-DOF]). Years outside
2020-2024 take the nearest published year, a hold rule fixed in the DESIGN before any number was
computed. That rule is also the forward story (rule 13 [R-MEASURED]): a forward year holds the last
published MMU year.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from market_sim.config.paths import SPP_MMU_UNAVAILABLE_CSV

# Jun-Sep, the MMU's derate-day season (Fig 12: "most of these days occurred during the summer"),
# as a day count for spreading the annual MW-days.
JUN_SEP_DAYS = 30 + 31 + 31 + 30


@dataclass(frozen=True)
class MMUShares:
    """One year's bands, each as a fraction of capacity (``ambient_mw`` in MW on Jun-Sep hours)."""

    year_used: int
    above_emer: float
    eco_to_emer: float
    ambient_mw: float


@lru_cache(maxsize=1)
def _table() -> pd.DataFrame:
    """The committed MMU table, indexed by year."""
    if not SPP_MMU_UNAVAILABLE_CSV.exists():
        raise FileNotFoundError(
            f"{SPP_MMU_UNAVAILABLE_CSV} missing (spp_mmu_offer_unavailability needs the MMU table)"
        )
    return pd.read_csv(SPP_MMU_UNAVAILABLE_CSV).set_index("year").sort_index()


def mmu_shares(year: int) -> MMUShares:
    """The MMU bands for ``year`` under the nearest-published-year hold rule."""
    t = _table()
    y = int(min(max(int(year), int(t.index.min())), int(t.index.max())))
    r = t.loc[y]
    rated = float(r.rated_conventional_mw)
    return MMUShares(
        year_used=y,
        above_emer=float(r.above_emer_max_mw) / rated,
        eco_to_emer=float(r.eco_to_emer_max_mw) / rated,
        ambient_mw=float(r.ambient_derate_mw_on_days)
        * float(r.ambient_derate_days)
        / JUN_SEP_DAYS,
    )
