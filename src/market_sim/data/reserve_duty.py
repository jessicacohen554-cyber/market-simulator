"""Read the reserve-duty (capacity-only) CC cohort membership.

The model's *consumption seam* for
``scripts/data/derive_reserve_duty_cc.py`` →
``data/raw/_processed-legacy/reserve_duty_cc_{ISO}.csv``, consumed by
:func:`market_sim.data.fleet.campd_bins.fleet_to_bins` when
``ScenarioConfig.cc_reserve_duty_split`` is on (GATED, default off, so a
control run is byte-identical).

nyiso-146 / nyiso-145 defect B: CC plants that hold capacity but essentially
never sell energy (measured on-share 1-6 %) carry competitive heat rates, so
the LP runs them 87-99 % of hours — model/EIA-923 ratios of 25-225x, with
ZERO floor involved (the energy is *economic*, where D-2/D-4 do not look).
The split routes the qualifying cohort's whole dispatchable capacity to the
class offer curve's PEAK band — the duty-role mirror of
``cc_intermediate_split``: that mechanism flattens offers for the measured
HIGH-CF cohort; this one steepens them for the measured RESERVE cohort. An
offer *shape* from a measured duty-role signal, never a pin to measured
output (rule 13, the ``ct_intermediate_plants`` admissibility lineage), with
ZERO new scalars (the peak band multiplier is the class's existing
identified constant — rule 21).

A missing artifact is a normal state (the derivation is per-ISO and
additive), so :func:`load_reserve_duty_cc` returns an empty set rather than
raising — but the consumption seam LOGS the membership it armed, so a run
cannot silently claim a duty-role correction it never read.
"""

from __future__ import annotations

import csv
import logging

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)


def load_reserve_duty_cc(iso: str) -> frozenset[int]:
    """Return the EIA plant codes of *iso*'s reserve-duty CC cohort.

    Args:
        iso: The ISO name.

    Returns:
        The qualifying plant codes, empty when the ISO has no artifact.
    """
    path = PROCESSED_DIR / f"reserve_duty_cc_{iso.upper()}.csv"
    if not path.exists():
        logger.warning(
            "no reserve-duty CC artifact for %s (%s) — every CC plant keeps "
            "its class offer curve",
            iso,
            path.name,
        )
        return frozenset()
    with path.open(newline="") as fh:
        return frozenset(
            int(row["plant_code"])
            for row in csv.DictReader(fh)
            if str(row.get("reserve_duty", "")).strip().lower() in ("true", "1", "yes")
        )
