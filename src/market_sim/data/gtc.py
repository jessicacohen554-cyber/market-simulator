"""Read the curated ``gtc-limits`` clean datatype and build hourly link caps.

The model's consumption seam for ERCOT's measured Generic Transmission
Constraint limits (NP6-86 SCED archive → ``scripts/curate_gtc_limits.py`` →
``data/clean/gtc-limits``). The one public builder,
:func:`ercot_gtc_ttc_hourly`, expands the static per-link TTC array to a
``(hours, n_links)`` export-direction cap matrix on the links that carry a
published GTC (``constants.ERCOT_GTC_LINK_MAP``), leaving every other link at
its static rating.

Hourly cap construction (per GTC, all quantities measured):

* an hour where the constraint was in SCED's active set takes the
  **time-average of its per-interval caps** — the hour's transfer energy
  cannot exceed the mean of the 5-minute limits — with the intervals where
  SCED was *not* enforcing the constraint standing in at the constraint's
  measured **envelope** (its year-max mean limit; the real limit those
  intervals was at least the flow, and the envelope is the largest limit
  ERCOT itself published that year);
* an hour with no row (SCED never enforced the constraint) rides the
  envelope.

This reconstruction is formulaic over the published series — nothing is
scaled to the reported curtailment totals (the validation target). Callers
gate on ``ScenarioConfig.ercot_gtc_limits_measured`` (backcast overlay,
default off) and degrade to the static ratings when the clean partition for
the year is absent.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    ERCOT_GTC_LINK_MAP,
    ERCOT_SCED_INTERVALS_PER_HOUR,
)

logger = logging.getLogger(__name__)

DATATYPE = "gtc-limits"


def load_gtc_hourly(iso: str, year: int) -> pd.DataFrame | None:
    """Return the year's sparse hourly GTC frame, or ``None`` when absent.

    A missing partition (archives not supplied / curation not run) is logged
    and returns ``None`` so callers degrade to the static link ratings.
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:
        logger.warning("gtc-limits: scripts.lib.clean_io unavailable")
        return None
    try:
        return read_clean(DATATYPE, iso=iso.upper(), year=year)
    except FileNotFoundError:
        logger.info(
            "gtc-limits: no clean partition for %s %d (supply the NP6-86 "
            "archives and run scripts/curate_gtc_limits.py)",
            iso,
            year,
        )
        return None


def _gtc_cap_series(sub: pd.DataFrame, hours: int) -> np.ndarray:
    """Return one GTC's ``(hours,)`` cap series from its sparse hourly rows.

    ``cap[h] = (limit_mean*n + envelope*(cadence-n)) / cadence`` for hours
    with ``n = min(n_active, cadence)`` active intervals, ``envelope``
    elsewhere. Vectorized — no loop over hours.
    """
    cadence = float(ERCOT_SCED_INTERVALS_PER_HOUR)
    envelope = float(sub["limit_mean_mw"].max())
    cap = np.full(hours, envelope, dtype=float)
    idx = sub["hour"].to_numpy(dtype=int)
    keep = idx < hours
    idx = idx[keep]
    n = np.minimum(sub["n_active"].to_numpy(dtype=float)[keep], cadence)
    mean = sub["limit_mean_mw"].to_numpy(dtype=float)[keep]
    cap[idx] = (mean * n + envelope * (cadence - n)) / cadence
    return cap


def ercot_gtc_ttc_hourly(
    ttc: np.ndarray, iso_config, year: int, hours: int
) -> tuple[np.ndarray, np.ndarray] | None:
    """Expand the static TTC to measured hourly export caps on the GTC links.

    Args:
        ttc: Static per-link capability, shape ``(n_links,)``.
        iso_config: The ERCOT :class:`ISOConfig` (supplies link zone pairs).
        year: Backcast year to read the ``gtc-limits`` partition for.
        hours: Dispatch horizon (rows of the output matrix).

    Returns:
        ``(ttc_hourly, ttc_import)`` — the ``(hours, n_links)``
        export-direction cap matrix and the static ``(n_links,)`` array to
        keep as the import-direction bound (a GTC is an export stability
        limit, not an import rating) — or ``None`` when the year has no
        clean partition (caller keeps the static symmetric path).
    """
    frame = load_gtc_hourly("ERCOT", year)
    if frame is None or frame.empty:
        return None

    ttc = np.asarray(ttc, dtype=float)
    ttc_hourly = np.broadcast_to(ttc, (hours, len(ttc))).copy()
    link_idx = {
        (link.from_zone, link.to_zone): i for i, link in enumerate(iso_config.links)
    }
    present = set(frame["gtc"].unique())
    mapped = present & set(ERCOT_GTC_LINK_MAP)
    for name in sorted(present - set(ERCOT_GTC_LINK_MAP)):
        logger.info(
            "gtc-limits %d: constraint %s has no representable link in the "
            "reduced topology (intra-zone pocket or unmapped era name) — "
            "ignored",
            year,
            name,
        )
    assigned: set[int] = set()
    for name in sorted(mapped):
        sub = frame[frame["gtc"] == name]
        cap = _gtc_cap_series(sub, hours)
        for zones, share in ERCOT_GTC_LINK_MAP[name]:
            i = link_idx.get(zones)
            if i is None:
                logger.warning(
                    "gtc-limits %d: link %s->%s not in topology — skipped",
                    year,
                    zones[0],
                    zones[1],
                )
                continue
            # The measured series REPLACES the static rating on its link —
            # the static ttc_mw is a binding-hour mean of the same GTC, so
            # min-combining against it would clip the measured envelope back
            # to an estimate (rule #15). Two GTCs mapping onto one link (not
            # the case today) combine conservatively via the minimum.
            if i in assigned:
                ttc_hourly[:, i] = np.minimum(ttc_hourly[:, i], cap * share)
            else:
                ttc_hourly[:, i] = cap * share
                assigned.add(i)
            logger.info(
                "gtc-limits %d: %s -> %s->%s x %.3f (export cap %0.0f-%0.0f "
                "MW over %d active hours; static %0.0f)",
                year,
                name,
                zones[0],
                zones[1],
                share,
                (cap * share).min(),
                (cap * share).max(),
                int(sub["hour"].nunique()),
                ttc[i],
            )
    if not mapped:
        logger.warning(
            "gtc-limits %d: partition present but no mapped GTC names "
            "(%s) — static TTC kept",
            year,
            ", ".join(sorted(present)),
        )
        return None
    return ttc_hourly, ttc
