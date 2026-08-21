"""Read the CHP fleet's economic-lay-up census.

The model's *consumption seam* for
``scripts/data/derive_campd_chp_layup_census.py`` →
``data/raw/_processed-legacy/chp_layup_census_{ISO}.csv``, consumed by
:func:`market_sim.data.fleet.campd_bins.fleet_to_bins` (and mirrored in
:mod:`market_sim.data.offer_curves`) when
``ScenarioConfig.chp_layup_duty_split`` is on (GATED, default off, so a
control run is byte-identical).

The cogeneration analogue of :mod:`market_sim.data.reserve_duty`, whose
CC_REGULAR cohort this one is disjoint from by class scope (rule 19
``[R-ONE-MECH]``: the two populations can never overlap, so nothing stacks).

nyiso-147 / nyiso-148: restoring the NYISO CHP fleet's measured grid capacity
(``nyiso_chp_btm_measured``) exposes semi-mothballed cogens the 35 % sector
carve had been hiding — Selkirk (10725) dispatches 730 GWh against a 92 GWh
meter — with ZERO floor involved (D-2 books CHP forcing at 0.38 % of CC_CHP
energy and the CHP classes are D-2-exempt), so the phantom energy is
*economic*, where D-2 and D-4 do not look. The census identifies those plants
from their own meters; the split prices them at the class peak band.

Qualifying test (derive-side, and deliberately blind to the mechanism's own
behaviour): median plant gross load is zero in EVERY (year, 4-hour block) cell
of the pooled window — the nyiso-140/144 criterion verbatim — AND the plant's
CAMPD series is non-degenerate (p99.5 HSL > 0). The second half is the guard
the measurement forced: three NYISO CHP plants carry an identically-zero CAMPD
series while EIA-923 reports 439-950 GWh, so a naive census would convict
plants CAMPD simply cannot see. A silent meter is no evidence, and the census
abstains rather than convicting.

A missing artifact is a normal state (the derivation is per-ISO and additive),
so :func:`load_chp_layup_census` returns an empty set rather than raising — but
the caller LOGS the membership it armed, so a run cannot silently claim a
duty-role correction it never read.
"""

from __future__ import annotations

import csv
import logging

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)


def load_chp_layup_census(iso: str) -> frozenset[int]:
    """Return the EIA plant codes of *iso*'s laid-up CHP cohort.

    Args:
        iso: The ISO name.

    Returns:
        The qualifying plant codes, empty when the ISO has no artifact.
    """
    path = PROCESSED_DIR / f"chp_layup_census_{iso.upper()}.csv"
    if not path.exists():
        logger.warning(
            "no CHP lay-up census for %s (%s) — every CHP plant keeps its "
            "class offer curve",
            iso,
            path.name,
        )
        return frozenset()
    with path.open(newline="") as fh:
        return frozenset(
            int(row["plant_code"])
            for row in csv.DictReader(fh)
            if str(row.get("laid_up", "")).strip().lower() in ("true", "1", "yes")
        )
