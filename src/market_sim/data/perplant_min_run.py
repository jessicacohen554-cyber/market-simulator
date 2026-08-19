"""Read the commitment bridge's per-plant measured minimum-run durations.

The model's *consumption seam* for
``scripts/data/derive_campd_perplant_min_run.py`` →
``data/raw/_processed-legacy/campd_perplant_min_run_{ISO}.csv``, consumed by
:func:`market_sim.pipeline.commitment._nyiso_bridge_min_run_hours` when
``ScenarioConfig.nyiso_gas_bridge_plant_min_run`` is on (GATED, default off,
so a control run is byte-identical).

nyiso-146: the bridge's minimum-run extension previously filled every LP row
of a class from one scalar (the capacity-weighted CAMPD class p50), but the
class is not one run-length population — per-plant p25 spans 7 h (Carr
Street, a true cycler) to 646 h (Caithness, near-baseload), and the class
scalar simultaneously over-constrains the cyclers and lets the LP shatter the
near-baseload CCs into hundreds of phantom starts (Bethlehem: 262-302 model
starts a year against 5-7 metered). The per-plant value REPLACES the class
scalar for every plant the artifact covers (rule 19 [R-ONE-MECH] — never
stacked); uncovered plants (no CAMPD series of their own, the mixed-class
drops, and the misaligned Astoria campus pair) keep the class fallback.

The identified value is each plant's own measured run-length p25 — the
pre-registered order statistic (see the derive script's docstring for the
constraint-side reasoning) — a measured per-plant statistic with zero fitted
scalars, the same DOF shape as the lay-up plant-code set (rule 21 [R-DOF]).

A missing artifact is a normal state (the derivation is per-ISO and
additive), so :func:`load_perplant_min_run` returns an empty mapping rather
than raising — but the consumption seam LOGS the coverage it armed, so a run
cannot silently claim a per-plant identification it never read.
"""

from __future__ import annotations

import csv
import logging

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)


def load_perplant_min_run(iso: str) -> dict[int, float]:
    """Return ``{plant_code: min_run_hours}`` measured for *iso*'s bridge fleet.

    Args:
        iso: The ISO name.

    Returns:
        The per-plant measured minimum-run durations (hours), empty when the
        ISO has no artifact.
    """
    path = PROCESSED_DIR / f"campd_perplant_min_run_{iso.upper()}.csv"
    if not path.exists():
        logger.warning(
            "no per-plant min-run artifact for %s (%s) — the commitment "
            "bridge keeps its class-scalar minimum-run values",
            iso,
            path.name,
        )
        return {}
    with path.open(newline="") as fh:
        return {
            int(row["plant_code"]): float(row["min_run_hours"])
            for row in csv.DictReader(fh)
            if row.get("min_run_hours")
        }
