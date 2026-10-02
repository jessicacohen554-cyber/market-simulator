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

SPP-107 repair sub-gate ``ScenarioConfig.spp_mmu_offer_repair`` (record
``docs/records/spp/DESIGN-spp-107-mmu-carrier-repair-2026-10-02.md``) builds the bands on the MMU's own
definitions: every band is a share of the row's post-outage AVAILABLE MW (multiplicative), and the
economic-to-emergency slice is not removed but pooled per zone as one ``emergency_band``
pseudo-generator (:func:`build_spp_mmu_pool_generators`) offered at the LP's load-shed price minus the
storage tiebreaker epsilon, so it clears only where the zone would otherwise shed load (the MMU: those MW
"are only accessible when SPP anticipates or identifies a reliability issue"). Its hourly capacity is
stamped by ``data.fleet.arrays._apply_spp_mmu_pool``.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from market_sim.config.constants import STORAGE_TIEBREAKER_EPSILON
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


def build_spp_mmu_pool_generators(
    config, iso: str, fleet: list, shed_price: float
) -> list:
    """The SPP-107 economic-to-emergency pool: one ``emergency_band`` row per zone with fossil rows.

    Empty unless ``spp_mmu_offer_unavailability`` and ``spp_mmu_offer_repair`` are both armed for SPP.
    ``pmax_mw`` is the eco-to-emer share of the zone's fossil pmax (an upper bound; the hourly
    availability is stamped by ``data.fleet.arrays._apply_spp_mmu_pool``). The offer is ``vom =
    shed_price - STORAGE_TIEBREAKER_EPSILON`` with heat rate and emissions 0, where ``shed_price`` is the
    LP's own load-slack price (``pipeline.spec.shed_penalty_voll``): zero fitted parameters (rule 21).
    The mapping year is ``config.weather_year``, the same year the bands use.
    """
    from market_sim.data.fleet import Generator
    from market_sim.data.fleet.arrays import _mmu_fossil

    if (
        iso != "SPP"
        or not getattr(config, "spp_mmu_offer_unavailability", False)
        or not getattr(config, "spp_mmu_offer_repair", False)
    ):
        return []
    sh = mmu_shares(int(config.weather_year))
    by_zone: dict[str, float] = {}
    for g in fleet:
        if _mmu_fossil(g):
            by_zone[g.zone] = by_zone.get(g.zone, 0.0) + float(g.pmax_mw)
    return [
        Generator(
            unit_id=f"SPP_MMU_EMER_{zone}",
            name=f"MMU economic-to-emergency pool {zone}",
            zone=zone,
            fuel_type="emergency_band",
            pmax_mw=sh.eco_to_emer * mw,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=float(shed_price) - STORAGE_TIEBREAKER_EPSILON,
            eford=0.0,
        )
        for zone, mw in sorted(by_zone.items())
        if mw > 0.0
    ]
