"""Read the measured gas-steam CAMPAIGN commitment parameters.

The model's *consumption seam* for
``scripts/data/derive_campd_gas_st_campaign_params.py`` →
``data/raw/_processed-legacy/campd_gas_st_campaign_params_{ISO}.csv``,
consumed by
:func:`market_sim.pipeline.commitment._soco_gas_st_campaign_floor` when
``ScenarioConfig.soco_gas_st_campaign_commitment`` is on (GATED, default off,
so every control run and every other ISO is byte-identical).

WHAT THE ARTIFACT CARRIES, per plant: the PLANT-basis minimum stable load
(``min_load_frac`` — the basis a floor multiplied by plant ``pmax`` requires),
the measured minimum campaign duration (``min_run_hours``, the p25 of the
plant's own campaign-length distribution) and the membership flag. Only rows
with ``flag == "ok"`` are returned: a plant whose own meter shows it
synchronized less than half the year is standby iron, not campaign iron, and
holding it at minimum load would bind in hours its own driver evidence says it
is offline (CLAUDE.md rule 17 ``[R-FLOOR-WINDOW]``). The gate and its ex-ante
declaration live in the derive, never here, so the consumer cannot re-scope
the population without re-deriving (rule 23 ``[R-FROZEN-DERIVE]``).

Both values are per-PLANT measured statistics with zero fitted scalars — the
same DOF shape as the per-plant min-run artifact and the lay-up plant-code set
(rule 21 ``[R-DOF]``).

A missing artifact is a normal state (the derivation is per-ISO and additive),
so :func:`load_gas_st_campaign_params` returns an empty mapping rather than
raising — but the consumption seam LOGS the coverage it armed, so a run cannot
silently claim a measured identification it never read.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CampaignParams:
    """One plant's measured campaign-commitment parameters.

    Attributes:
        min_load_frac: PLANT-basis minimum stable load as a fraction of the
            plant's own maximum sustained output.
        min_run_hours: Measured minimum campaign duration in hours (the p25 of
            the plant's own campaign-length distribution).
        sync_share: Measured share of hours the plant is synchronized —
            carried for the D-4 window evidence, never read by the floor.
    """

    min_load_frac: float
    min_run_hours: int
    sync_share: float


def load_gas_st_campaign_params(iso: str) -> dict[int, CampaignParams]:
    """Return ``{plant_code: CampaignParams}`` for *iso*'s campaign-duty fleet.

    Args:
        iso: The ISO name.

    Returns:
        The applied (``flag == "ok"``) per-plant measured parameters, empty
        when the ISO has no artifact.
    """
    path = PROCESSED_DIR / f"campd_gas_st_campaign_params_{iso.upper()}.csv"
    if not path.exists():
        logger.warning(
            "no gas-steam campaign-params artifact for %s (%s) — the campaign "
            "commitment floor has nothing to arm and is inert",
            iso,
            path.name,
        )
        return {}
    out: dict[int, CampaignParams] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("flag") != "ok":
                continue
            frac = float(row["min_load_frac"])
            hours = int(float(row["min_run_hours"]))
            if frac <= 0.0 or hours <= 0:
                continue
            out[int(row["plant_code"])] = CampaignParams(
                min_load_frac=frac,
                min_run_hours=hours,
                sync_share=float(row.get("sync_share") or 0.0),
            )
    return out
