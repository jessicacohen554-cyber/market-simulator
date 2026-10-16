"""Shared contract for the ``load-forecast-vintages`` clean datatype.

Every issued vintage of an ISO's own short-term hourly load forecast, one row
per (issue time, forecast interval), declared in
``data/dictionary/schema/load-forecast-vintages.schema.yaml``. Intake lane
UC-DF-AUDIT (owner ruling UC-DESK r14, 2026-10-16): the reliability-commitment
(RUC) load basis is the vintage in force at a commitment cycle before each
operating hour, so vintages are never collapsed here; the consumer picks one
by lead (``market_sim.data.load_forecast_vintages``).

Per-ISO parsing lives in sibling modules (``spp.py``) that register an
:class:`IsoSpec`; shared code never branches on the ISO name. Raw inputs live
under ``data/raw/load-forecast-vintages/<iso>/``.

The registry scaffolding comes from
:func:`scripts.lib.datatype_registry.make_registry`; only the columns,
``validate_tidy`` and ``parse_iso`` are datatype-specific.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "load-forecast-vintages"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "area",
    "issue_time_utc",
    "interval_end_utc",
    "lead_hours",
    "forecast_mw",
    "actual_mw",
)

KEY_COLUMNS: tuple[str, ...] = ("iso", "area", "issue_time_utc", "interval_end_utc")

_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
        ("parse", "Callable[[Path, 'IsoSpec'], dict[int, pd.DataFrame]]"),
        ("description", str, ""),
    ],
    package=__name__,
    iso_modules=("spp",),
    raw_subpath=(DATATYPE,),
    string_cols=("iso", "area"),
    float_cols=("forecast_mw", "actual_mw"),
    sort_by=KEY_COLUMNS,
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
raw_dir_for = _R.raw_dir_for
_finalize_base = _R.finalize


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to the canonical dtypes / order; ``lead_hours`` from the timestamps."""
    out = _finalize_base(df)
    for col in ("issue_time_utc", "interval_end_utc"):
        out[col] = out[col].astype("datetime64[ns, UTC]")
    out["lead_hours"] = (
        (out["interval_end_utc"] - out["issue_time_utc"]) // pd.Timedelta(hours=1)
    ).astype("int64")
    return out


def validate_tidy(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` on a duplicate key or an inconsistent ``lead_hours``."""
    dup = df.duplicated(list(KEY_COLUMNS))
    if dup.any():
        raise ValueError(f"{DATATYPE}: {int(dup.sum())} duplicate key rows")
    lead = (df["interval_end_utc"] - df["issue_time_utc"]) // pd.Timedelta(hours=1)
    if not (lead.astype("int64") == df["lead_hours"]).all():
        raise ValueError(f"{DATATYPE}: lead_hours disagrees with the timestamps")
    if df["forecast_mw"].isna().any():
        raise ValueError(f"{DATATYPE}: null forecast_mw")


def parse_iso(iso: str, raw_root: Path) -> dict[int, pd.DataFrame]:
    """``{issue year: tidy frame}`` for one ISO via its registered parser."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise KeyError(f"{DATATYPE}: no registered spec for {iso}")
    out = {}
    for year, df in spec.parse(raw_dir_for(iso, raw_root), spec).items():
        df = finalize(df)
        validate_tidy(df)
        out[int(year)] = df
    return out
