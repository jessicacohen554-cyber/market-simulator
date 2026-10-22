"""Shared contract for the ``flowgate-limits-at-bind`` clean datatype.

Measured operating limits of transmission constraints in the hours they bound,
per ``data/dictionary/schema/flowgate-limits-at-bind.schema.yaml``. First ISO:
SPP, from the portal's ``effective-limits`` product (RTBM-EFFLIMIT daily files,
2022-04-14 onward). The limit is an admissible physical input (rule 13); when a
constraint binds is a dispatch outcome and stays validation evidence.

Per-ISO parsing lives in sibling modules (``spp.py``, ...) that register an
``IsoSpec`` with ``raw_subdir`` (the ISO's directory under ``data/raw``) and
``parse(raw_dir, year) -> DataFrame``; shared code never branches on the ISO.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "flowgate-limits-at-bind"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "market",
    "constraint_name",
    "constraint_type",
    "monitored_facility",
    "contingent_facility",
    "hour_start_utc",
    "n_binding_intervals",
    "n_breached_intervals",
    "shadow_price_mean_usd_mwh",
    "source_limit_mw",
    "effective_limit_mw",
    "effective_limit_min_mw",
    "initial_effective_limit_mw",
)
_STRING_COLS = (
    "iso",
    "market",
    "constraint_name",
    "constraint_type",
    "monitored_facility",
    "contingent_facility",
)
_FLOAT_COLS = (
    "shadow_price_mean_usd_mwh",
    "source_limit_mw",
    "effective_limit_mw",
    "effective_limit_min_mw",
    "initial_effective_limit_mw",
)
_COUNT_COLS = ("n_binding_intervals", "n_breached_intervals")

_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [("iso", str), ("raw_subdir", str), ("parse", Callable)],
    package=__name__,
    iso_modules=("spp",),
    raw_subpath=(),
    string_cols=_STRING_COLS,
    float_cols=_FLOAT_COLS,
    sort_by=(
        "constraint_name",
        "monitored_facility",
        "contingent_facility",
        "hour_start_utc",
    ),
)
IsoSpec, REGISTRY, register = _R.IsoSpec, _R.REGISTRY, _R.register
load_registry = _R.load_registry


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Canonical dtypes and order; interval counts stay ``int64`` per the schema."""
    out = _R.finalize(df)
    for col in _COUNT_COLS:
        out[col] = out[col].astype("int64")
    out["hour_start_utc"] = pd.to_datetime(out["hour_start_utc"], utc=True)
    return out
