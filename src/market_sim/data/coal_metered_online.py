"""Read the DIAGNOSTIC metered coal online-state floor (never a keeper input).

Consumption seam for ``scripts/data/derive_coal_metered_online_floor.py`` ->
``data/raw/_processed-legacy/coal_metered_online_floor_{ISO}.parquet``, read by
:func:`market_sim.pipeline.commitment.wrap_coal_metered_online_diagnostic_prep`
only when ``ScenarioConfig.diagnostic_coal_metered_online_floor`` is on.

Rule 13 ``[R-MEASURED]``: the artifact is each coal plant's measured
commitment STATE (the hours its own CEMS meter shows it online) at the P5 of
its own online net MW. That is an observed outcome with no forward story, so it
exists only behind a default-off, labelled diagnostic flag that is backcast-only
and must never be armed on a keeper (closeout-SOCO-w3, desk direction
2026-10-04).

A missing artifact is a normal state (the derivation is per-ISO); the loader
returns an empty mapping and the consumption seam logs that it is inert.
"""

from __future__ import annotations

import logging

import numpy as np

from market_sim.config.paths import PROCESSED_DIR

logger = logging.getLogger(__name__)


def load_coal_metered_online_floor(
    iso: str, year: int, hours: int
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) floor MW}`` for ``iso`` in ``year``.

    The floor is the plant's P5 online net MW in every hour its coal units were
    metered online and 0 elsewhere. Empty when the ISO has no artifact or the
    artifact carries no row for ``year``.
    """
    import pandas as pd

    path = PROCESSED_DIR / f"coal_metered_online_floor_{iso}.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    df = df[df["year"] == int(year)]
    out: dict[int, np.ndarray] = {}
    for code, sub in df.groupby("plant_code"):
        floor = np.zeros(hours, dtype=float)
        h = sub["hour"].to_numpy(dtype=int)
        ok = (h >= 0) & (h < hours)
        floor[h[ok]] = sub["floor_mw"].to_numpy(dtype=float)[ok]
        out[int(code)] = floor
    return out
