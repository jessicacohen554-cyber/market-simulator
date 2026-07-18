"""Read the ``transfer-interface-limits`` clean datatype and build hourly link caps.

The model's consumption seam for PJM's measured internal interface transfer
limits (PJM Data Miner 2 ``transfer_limits_and_flows`` →
``scripts/data/curate_transfer_interface_limits.py`` →
``data/clean/transfer-interface-limits``) — the PJM analogue of
:mod:`market_sim.data.gtc`. The one public builder,
:func:`pjm_interface_ttc_hourly`, expands the static per-link TTC array to a
``(hours, n_links)`` forward-direction cap matrix on the links whose static
``ttc_mw`` was seeded from these postings
(``constants.PJM_INTERFACE_LINK_MAP``), leaving every other link static.

Hourly cap construction (per link, all quantities measured):

* the link's forward (west→east congestion direction) cap each hour is the
  **elementwise min of its mapped published series** — where an interface
  publishes both pre- and post-contingency limits, both are
  simultaneously-enforced security limits and the operative capability is
  the tighter one;
* non-positive published limits clamp to **0** (no secure transfer that
  hour) — never a negative bound, which would FORCE counterflow;
* the reverse direction keeps the static capability (the published limits
  are directional security limits on the west→east cut, not reverse
  ratings) — the same asymmetric-seam convention as the ERCOT measured GTC
  overlay;
* an hour a series does not cover (never the case for the committed dense
  2023-25 partitions; a guard for partial future drops) rides the static
  rating.

This reconstruction is formulaic over the published series — nothing is
scaled to a price or volume residual (rules #13/#14). Callers gate on
``ScenarioConfig.pjm_measured_interface_limits`` (backcast overlay, default
off) and degrade to the static ratings when the year's clean partition is
absent. Forecast years never call this: the static seeds (2024 means of the
same feed) are the forward story.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from market_sim.config.constants import PJM_INTERFACE_LINK_MAP

logger = logging.getLogger(__name__)

DATATYPE = "transfer-interface-limits"


def load_interface_hourly(iso: str, year: int) -> pd.DataFrame | None:
    """Return the year's dense hourly interface-limit frame, or ``None``.

    A missing partition (raw drop not curated) is logged and returns ``None``
    so callers degrade to the static link ratings.
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:
        logger.warning("transfer-interface-limits: scripts.lib.clean_io unavailable")
        return None
    try:
        return read_clean(DATATYPE, iso=iso.upper(), year=year)
    except FileNotFoundError:
        logger.info(
            "transfer-interface-limits: no clean partition for %s %d (run "
            "scripts/data/curate_transfer_interface_limits.py)",
            iso,
            year,
        )
        return None


def _series_hourly(frame: pd.DataFrame, name: str, hours: int) -> np.ndarray | None:
    """One published series' ``(hours,)`` limit, NaN where uncovered.

    Returns ``None`` when the series is absent from the partition entirely
    (an older drop) so the caller can fall back to the static rating and log
    it. Vectorized — no loop over hours.
    """
    sub = frame[frame["interface"] == name]
    if sub.empty:
        return None
    out = np.full(hours, np.nan, dtype=float)
    idx = sub["hour"].to_numpy(dtype=int)
    keep = idx < hours
    out[idx[keep]] = sub["limit_mw"].to_numpy(dtype=float)[keep]
    return out


#: The Manual-03 EASTERN reactive transfer interface series (PJM Manual 03
#: §3.8 Rev 71: Breinigsville–Alburtis ×2, Juniata–Alburtis,
#: Lauschtown–Hosensack, Peach Bottom–Limerick, Rock Springs–Keeney,
#: Lackawanna–Hopatcong — the EHV cut into the eastern Mid-Atlantic). The
#: DataMiner2 feed posts its hourly-averaged TLC limit as "Average Eastern".
PJM_EASTERN_INTERFACE_SERIES = "Average Eastern"


def pjm_eastern_interface_hourly(year: int, hours: int) -> np.ndarray | None:
    """The measured EMAAC-import-cut hourly limit (``pjm_east_interface_cut``).

    Returns the ``(hours,)`` "Average Eastern" published limit — the joint
    cap for the Central_PA→EMAAC + SWMAAC→EMAAC link pair (the reduced
    network's EMAAC import cut; see the ScenarioConfig field docstring and
    diagnosis §10.5). Uncovered hours (never the case for the committed dense
    2023–25 partitions) ride ``+inf`` so the group row is simply non-binding
    there rather than inventing a static joint rating. Returns ``None`` when
    the year has no clean partition or the series is absent — callers skip
    the group (byte-identical to the flag being off) and warn.
    """
    frame = load_interface_hourly("PJM", year)
    if frame is None or frame.empty:
        return None
    measured = _series_hourly(frame, PJM_EASTERN_INTERFACE_SERIES, hours)
    if measured is None:
        logger.warning(
            "pjm_east_interface_cut %d: series %r absent from the clean "
            "partition — joint EMAAC cut skipped",
            year,
            PJM_EASTERN_INTERFACE_SERIES,
        )
        return None
    out = np.where(np.isnan(measured), np.inf, measured)
    # Non-positive published limits clamp to 0 (no secure transfer that
    # hour), matching the per-link overlay's convention.
    return np.maximum(out, 0.0)


def pjm_interface_ttc_hourly(
    ttc: np.ndarray, iso_config, year: int, hours: int
) -> tuple[np.ndarray, np.ndarray] | None:
    """Expand static TTC to measured hourly forward caps on the mapped links.

    Args:
        ttc: Static per-link capability, shape ``(n_links,)`` — after any
            static overrides (``pjm_congestion``) so the reverse direction
            and uncovered-hour fill stay consistent with the run's statics.
        iso_config: The PJM :class:`ISOConfig` (supplies link zone pairs).
        year: Backcast year to read the clean partition for.
        hours: Dispatch horizon (rows of the output matrix).

    Returns:
        ``(ttc_hourly, ttc_import)`` — the ``(hours, n_links)`` forward-
        direction cap matrix and the static ``(n_links,)`` array kept as the
        reverse-direction bound — or ``None`` when the year has no clean
        partition (caller keeps the static symmetric path).
    """
    frame = load_interface_hourly("PJM", year)
    if frame is None or frame.empty:
        return None

    ttc = np.asarray(ttc, dtype=float)
    ttc_hourly = np.broadcast_to(ttc, (hours, len(ttc))).copy()
    link_idx = {
        (link.from_zone, link.to_zone): i for i, link in enumerate(iso_config.links)
    }
    n_mapped = 0
    for zones, series_names in PJM_INTERFACE_LINK_MAP.items():
        i = link_idx.get(zones)
        if i is None:
            logger.warning(
                "transfer-interface-limits %d: link %s->%s not in topology — skipped",
                year,
                zones[0],
                zones[1],
            )
            continue
        stack = []
        for name in series_names:
            measured = _series_hourly(frame, name, hours)
            if measured is None:
                logger.warning(
                    "transfer-interface-limits %d: series %r absent from the "
                    "partition — %s->%s falls back to the static rating for "
                    "that series",
                    year,
                    name,
                    zones[0],
                    zones[1],
                )
                continue
            stack.append(measured)
        if not stack:
            continue
        # Operative hourly cap = min over the link's simultaneously-enforced
        # published limits; uncovered hours (all-NaN — impossible for the
        # dense committed partitions) ride the static rating; non-positive
        # published limits clamp to 0 (no secure forward transfer), never a
        # negative bound (which would force counterflow).
        with np.errstate(invalid="ignore"):
            combined = np.nanmin(np.vstack(stack), axis=0)
        combined = np.where(np.isnan(combined), ttc[i], combined)
        ttc_hourly[:, i] = np.maximum(combined, 0.0)
        n_mapped += 1
        logger.info(
            "transfer-interface-limits %d: %s->%s forward cap follows %s "
            "(hourly %0.0f-%0.0f MW, mean %0.0f; static %0.0f kept on the "
            "reverse direction)",
            year,
            zones[0],
            zones[1],
            " min ".join(series_names),
            float(ttc_hourly[:, i].min()),
            float(ttc_hourly[:, i].max()),
            float(ttc_hourly[:, i].mean()),
            ttc[i],
        )
    if n_mapped == 0:
        logger.warning(
            "transfer-interface-limits %d: partition present but no mapped "
            "series found — static TTC kept",
            year,
        )
        return None
    return ttc_hourly, ttc
