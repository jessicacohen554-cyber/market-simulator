"""Prior-year measured commitment profiles for ERCOT CC / ST_GAS plants (R-ERCOT-19).

Loader for the frozen artifact
``data/raw/_validation-source/ercot_prior_year_commitment_profile.csv``
(``scripts/data/derive_ercot_prior_year_commitment_profile.py``): each metered
plant's measured online CAPACITY share by month x hour-of-day, per CAMPD year.

Two backcast-only sub-gates read it, both at vintage ``Y - 1`` (rule 13
[R-MEASURED]: information on file before the solve year opens, never the
year's own conduct):

* ``ScenarioConfig.cc_committed_prior_year_commitment_eligibility`` —
  :func:`market_sim.data.offer_curves.apply_cc_committed_offer_margin` weights
  the ERCOT-139 below-cost committed-block shift by ``q_p(t)``.
* ``ScenarioConfig.netload_drag_prior_year_hour_profile`` —
  :func:`market_sim.data.fleet.floors.apply_gas_st_netload_drag_floor`
  reshapes each plant's drag floor by ``q_p(t) / mean q_p``.

Both fail closed (``None`` -> byte-identical to the flag off) when the flag is
off, the run is not a backcast, the artifact is absent, or it carries no row
for the ISO / class / vintage (2019, whose TX 2018 CAMPD extract is not on
disk). Zero free parameters (rule 21 [R-DOF]).
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.utils.hour_calendar import month_of_hour

logger = logging.getLogger(__name__)

ARTIFACT_NAME = "ercot_prior_year_commitment_profile.csv"


@lru_cache(maxsize=4)
def _read_artifact(path_str: str):
    """Read the profile CSV once per path (the artifact is frozen, rule 23)."""
    import pandas as pd

    return pd.read_csv(path_str)


def load_prior_year_commitment_profile(
    config: ScenarioConfig,
    iso: str,
    year: int,
    klass: str,
    flag: str,
    hours: int,
) -> dict[int, np.ndarray] | None:
    """Per-plant prior-year online share on the model clock, or ``None``.

    Args:
        config: Scenario configuration; ``flag`` names the gating field.
        iso: ISO whose rows to read (the artifact is ERCOT-only; rule 25).
        year: Solve year; the vintage read is ``year - 1`` (``weather_year - 1``
            when one is pinned).
        klass: ``"CC_REGULAR"`` or ``"ST_GAS"`` — the plant set to return.
        flag: The ``ScenarioConfig`` boolean that arms this consumer.
        hours: Length of the model clock (8760 for a full year).

    Returns:
        ``{plant_code: q (hours,)}`` for every METERED plant of ``klass`` —
        ``q[t]`` the plant's measured online capacity share in the month and
        hour-of-day of model hour ``t`` — or ``None`` when fail-closed.
    """
    if not getattr(config, flag, False):
        return None
    if getattr(config, "mode", "forecast") != "backcast":
        return None
    from market_sim.config import paths as _paths

    path = _paths.CALIBRATION_DIR / ARTIFACT_NAME
    if not path.exists():
        logger.warning("%s: %s absent — fail-closed (flag inert)", flag, path)
        return None
    vintage = int(getattr(config, "weather_year", 0) or year) - 1
    df = _read_artifact(str(path))
    sub = df[
        (df["iso"].astype(str).str.upper() == (iso or "").upper())
        & (df["klass"] == klass)
        & (df["year"] == vintage)
    ]
    if "metered" in sub.columns:  # the derive writes metered rows only
        sub = sub[sub["metered"].astype(str).str.lower() == "true"]
    if sub.empty:
        logger.info("%s: no %s %s %d vintage — fail-closed", flag, iso, klass, vintage)
        return None
    t = np.arange(int(hours))
    cell = (month_of_hour(t) - 1) * 24 + (t % 24)  # (month, hour-of-day) per hour
    out: dict[int, np.ndarray] = {}
    for code, g in sub.groupby("plant_code"):
        grid = np.ones(288)
        grid[(g["month"].to_numpy(int) - 1) * 24 + g["hour"].to_numpy(int)] = g[
            "on_frac"
        ].to_numpy(float)
        out[int(code)] = grid[cell]
    logger.info(
        "%s ARMED (%s %d): vintage %d, %d metered %s plants, mean online share %.3f",
        flag,
        iso,
        year,
        vintage,
        len(out),
        klass,
        float(np.mean([v.mean() for v in out.values()])),
    )
    return out
