"""Read the curated ``gtc-limits`` clean datatype and build hourly link caps.

The model's consumption seam for ERCOT's measured Generic Transmission
Constraint limits (NP6-86 SCED archive → ``scripts/data/curate_gtc_limits.py`` →
``data/clean/gtc-limits``). The one public builder,
:func:`ercot_gtc_ttc_hourly`, expands the static per-link TTC array to a
``(hours, n_links)`` export-direction cap matrix on the links that carry a
published GTC (``constants.ERCOT_GTC_LINK_MAP``), leaving every other link at
its static rating.

Hourly cap construction (per GTC, all quantities measured):

* an hour where the constraint was in SCED's active set takes the
  **time-average of its per-interval limits** — the hour's transfer energy
  cannot exceed the mean of the 5-minute limits SCED enforced;
* an hour with no row (SCED never enforced the constraint) reverts to the
  link's **static derived limit-at-bind** (the calibrated ``ttc_mw``), NOT a
  year-max envelope — the GTC still physically exists those hours, and its
  flows are simply below the (roughly static) limit, so filling with the
  static rating neither relaxes nor tightens the ~85% of hours SCED does not
  report the constraint.

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
            "archives and run scripts/data/curate_gtc_limits.py)",
            iso,
            year,
        )
        return None


def _gtc_measured_series(sub: pd.DataFrame, hours: int) -> np.ndarray:
    """Return a GTC's ``(hours,)`` measured hourly limit, NaN where unobserved.

    ``cap[h]`` is the mean enforced limit over hour ``h``'s active SCED
    intervals; hours where the constraint was never in SCED's active set are
    ``NaN`` so the caller can fill them with the static derived rating rather
    than an inflated year-max envelope. Vectorized — no loop over hours.

    Using the measured mean only where SCED actually reported the constraint
    keeps this a pure "real data where we have it" input (rule #12): the
    reduced network's export cap follows the published hourly stability limit
    on the hours it was enforced, and reverts to the calibrated static
    limit-at-bind otherwise.
    """
    cap = np.full(hours, np.nan, dtype=float)
    idx = sub["hour"].to_numpy(dtype=int)
    keep = idx < hours
    cap[idx[keep]] = sub["limit_mean_mw"].to_numpy(dtype=float)[keep]
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
        measured = _gtc_measured_series(sub, hours)
        active = ~np.isnan(measured)
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
            # Measured hourly limit where SCED reported the constraint; the
            # static derived limit-at-bind (ttc[i]) on unobserved hours — never
            # a year-max envelope, which would relax the network below its
            # calibrated rating for the ~85% of hours the GTC is not in SCED's
            # active set. Two GTCs mapping onto one link (not the case today)
            # combine conservatively via the elementwise minimum.
            link_cap = np.where(active, measured * share, ttc[i])
            if i in assigned:
                ttc_hourly[:, i] = np.minimum(ttc_hourly[:, i], link_cap)
            else:
                ttc_hourly[:, i] = link_cap
                assigned.add(i)
            logger.info(
                "gtc-limits %d: %s -> %s->%s x %.3f (measured export cap "
                "%0.0f-%0.0f MW over %d active hours; static fill %0.0f)",
                year,
                name,
                zones[0],
                zones[1],
                share,
                float(np.nanmin(measured) * share),
                float(np.nanmax(measured) * share),
                int(active.sum()),
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
