"""Read the commitment bridge's laid-up plant exclusions.

The model's *consumption seam* for
``scripts/data/derive_campd_bridge_layup_exclusions.py`` →
``data/raw/_processed-legacy/campd_bridge_layup_exclusions_{ISO}.csv``,
consumed by :func:`market_sim.pipeline.commitment._nyiso_gas_bridge_floor`
when ``ScenarioConfig.nyiso_gas_bridge_plant_exclusions`` is on (GATED,
default off, so a control run is byte-identical).

The bridge's analogue of the reliability floor's ``exclude_plant_codes``
(``config.iso_configs.apply_reliability_floor_plant_exclusions``). Both
mechanisms floor the merchant slow-start gas fleet, and both must skip a plant
in economic LAY-UP — idle in its own metered conduct while reading ~100 %
available in the outage extract, because lay-up is correctly not booked as a
forced outage. The exclusion channel existed only on the floor, so nyiso-140
fixed one MECHANISM rather than the plant; this is the second half (rule 19
``[R-ONE-MECH]``: enumerate what already floors the same class).

Qualifying test (derive-side, and deliberately blind to the mechanism's own
behaviour): median plant gross load is zero in EVERY (year, 4-hour block) cell
of the pooled window. The per-cell quantifier is what distinguishes lay-up from
a low capacity factor — a pooled median of zero also catches ordinary cyclers,
which are the population a commitment bridge exists to serve.

A missing artifact is a normal state (the derivation is per-ISO and additive),
so :func:`load_layup_exclusions` returns an empty set rather than raising — but
the caller LOGS the count it armed, so a run cannot silently claim a membership
correction it never read.
"""

from __future__ import annotations

import csv
import logging

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)


def load_layup_exclusions(iso: str) -> frozenset[int]:
    """Return the EIA plant codes in economic lay-up for *iso*.

    Args:
        iso: The ISO name.

    Returns:
        The qualifying plant codes, empty when the ISO has no artifact.
    """
    path = PROCESSED_DIR / f"campd_bridge_layup_exclusions_{iso.upper()}.csv"
    if not path.exists():
        logger.warning(
            "no bridge lay-up exclusion artifact for %s (%s) — the commitment "
            "bridge keeps its full population",
            iso,
            path.name,
        )
        return frozenset()
    with path.open(newline="") as fh:
        codes = {
            int(row["plant_code"])
            for row in csv.DictReader(fh)
            if str(row.get("laid_up", "")).strip().lower() in ("true", "1", "yes")
        }
    return frozenset(codes)
