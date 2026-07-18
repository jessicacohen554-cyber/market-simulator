"""Reader for the ``nyiso-renewable-curtailment`` / ``-monthly`` curated datatypes.

NYISO's own coarse annual/monthly, NYCA-wide and 4-zone (West/Central/North/
Mohawk Valley) wind and FTM-solar curtailment aggregate, hand-transcribed from
its NYCA Renewables presentation series (see
``data/raw/nyiso-renewable-curtailment/README.md`` for sources and documented
year gaps). This is a **labeled diagnostic dataset only** — it does not feed
dispatch. NYISO publishes no hourly per-plant uncurtailed-potential (HSL)
series comparable to ERCOT NP6 or CAISO's Production-and-Curtailment
workbooks, so the model's dispatch renewable profiles continue to use the
EIA-930 delivered-generation fallback documented in
:mod:`market_sim.data.renewables` (see its module docstring and
``_hsl_file``'s NYISO stub) — this reader exists so the coarse aggregate is
queryable/reportable rather than living only as inline code comments.

Reads the curated clean Parquet through :func:`scripts.lib.clean_io.read_clean`;
if the clean partition is absent (not yet regenerated), falls back to building
the identical frame straight from ``data/raw`` via
:mod:`scripts.data.curate_nyiso_renewable_curtailment` so a caller never silently
gets nothing on a fresh checkout without a regenerated clean tree.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

ANNUAL_DATATYPE = "nyiso-renewable-curtailment"
MONTHLY_DATATYPE = "nyiso-renewable-curtailment-monthly"


def _read_or_rebuild(datatype: str, build_frame) -> pd.DataFrame | None:
    """Read a clean partition, falling back to rebuilding it from raw."""
    try:
        from scripts.lib.clean_io import read_clean

        frame = read_clean(datatype, iso="NYISO", validate=False)
        if frame is not None and not frame.empty:
            return frame
    except FileNotFoundError:
        pass
    except ModuleNotFoundError:
        pass

    try:
        from scripts.lib.clean_io import paths

        frame = build_frame(paths.RAW_DIR)
    except (ModuleNotFoundError, KeyError, ValueError, FileNotFoundError) as exc:
        logger.info(
            "%s: no clean partition and raw build failed (%s); caller falls back.",
            datatype,
            exc,
        )
        return None
    return frame if frame is not None and not frame.empty else None


def _filter(
    frame: pd.DataFrame | None,
    resource_type: str | None,
    geographic_scope: str | None,
) -> pd.DataFrame:
    if frame is None:
        return pd.DataFrame()
    out = frame
    if resource_type is not None:
        out = out[out["resource_type"] == resource_type]
    if geographic_scope is not None:
        out = out[out["geographic_scope"] == geographic_scope]
    return out.reset_index(drop=True)


def load_annual_curtailment(
    resource_type: str | None = None,
    geographic_scope: str | None = None,
) -> pd.DataFrame:
    """Return NYISO's annual curtailment aggregate, optionally filtered.

    ``resource_type``: "wind" or "ftm_solar"; ``geographic_scope``: "NYCA" or
    one of "WEST"/"CENTRAL"/"NORTH"/"MOHAWK_VALLEY" (wind only). Omit either to
    get every row. Returns an empty frame if nothing is available (should not
    happen once the raw CSVs are committed).
    """
    from scripts.data.curate_nyiso_renewable_curtailment import build_annual_frame

    frame = _read_or_rebuild(ANNUAL_DATATYPE, build_annual_frame)
    return _filter(frame, resource_type, geographic_scope)


def load_monthly_curtailment(
    resource_type: str | None = None,
    geographic_scope: str | None = None,
) -> pd.DataFrame:
    """Return NYISO's monthly curtailment aggregate, optionally filtered.

    NYCA-wide rows carry ``curtailed_pct`` (percent of that month's
    production); zonal rows carry ``curtailed_energy_gwh``. See
    :func:`load_annual_curtailment` for the filter semantics.
    """
    from scripts.data.curate_nyiso_renewable_curtailment import build_monthly_frame

    frame = _read_or_rebuild(MONTHLY_DATATYPE, build_monthly_frame)
    return _filter(frame, resource_type, geographic_scope)
