"""Reader for the ``nyiso-downstate-gas`` curated datatype — model consumption seam.

Returns the daily delivered-gas index a non-firm downstate NYISO gas peaker faces,
**per downstate zone** (NYC / Long_Island): the measured Transco Zone 6 NY
pipeline-hub daily spot (the peaker's own commodity) plus the measured monthly LDC
non-firm transportation delivery rate for that zone's LDC (KEDNY SC-22 for NYC,
KEDLI SC-19 for Long Island). See the schema and
``data/raw/gas-prices/SOURCES_nyiso_downstate_ldc_transport.md``. The single seam
the model uses to re-ground the downstate CT-peaker offer level on measured daily
delivered gas (:func:`market_sim.data.fuel.apply_nyiso_downstate_ct_gas_daily`).

Reads the curated clean Parquet through :func:`scripts.lib.clean_io.read_clean`;
if the clean partition is absent (not yet regenerated), it falls back to
building the identical daily frame straight from ``data/raw`` via the shared
builder (``scripts/lib/nyiso_downstate_gas.build_daily_frame``) so an enabled
mechanism never silently no-ops. Returns ``None`` only when the raw inputs
themselves have no rows for the year (a forward year without the series
extended), so the caller degrades to the monthly-premium path.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DATATYPE = "nyiso-downstate-gas"


def delivered_gas_by_zone_month_day(
    iso: str, year: int
) -> dict[str, dict[int, dict[int, float]]] | None:
    """Return ``{zone: {month(1-12): {day-of-month: delivered_gas_$/MMBtu}}}`` or ``None``.

    The delivered-gas index keyed by downstate model zone then calendar
    (month, day-of-month) so the caller can place each zone-day's value on the
    model's fixed 365-day (28-day-February) calendar — a leap-year Feb-29 row is
    simply never referenced. Prefers the curated clean partition; falls back to
    building from raw when clean is absent. ``None`` when no rows exist for
    ``iso``/``year``.
    """
    frame = None
    try:
        from scripts.lib.clean_io import read_clean

        frame = read_clean(DATATYPE, iso=iso, year=year, validate=False)
    except FileNotFoundError:
        frame = None
    except ModuleNotFoundError:
        frame = None

    if frame is None or frame.empty:
        # Raw fallback: build the identical daily frame from data/raw so an
        # explicitly-enabled mechanism never silently no-ops on a fresh checkout
        # without a regenerated clean tree.
        try:
            from scripts.lib.clean_io import paths
            from scripts.lib.nyiso_downstate_gas import build_daily_frame

            frame = build_daily_frame(iso, year, paths.RAW_DIR)
        except (ModuleNotFoundError, KeyError, ValueError, FileNotFoundError) as exc:
            logger.info(
                "nyiso-downstate-gas: no clean partition and raw build failed "
                "for %s %d (%s); caller falls back.",
                iso,
                year,
                exc,
            )
            return None

    if frame is None or frame.empty:
        return None

    out: dict[str, dict[int, dict[int, float]]] = {}
    for row in frame.itertuples():
        date = row.date
        zone = str(row.zone)
        out.setdefault(zone, {}).setdefault(int(date.month), {})[int(date.day)] = float(
            row.delivered_gas_usd_per_mmbtu
        )
    return out
