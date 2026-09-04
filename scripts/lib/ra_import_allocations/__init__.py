"""Shared contract for the ``ra-import-allocations`` clean datatype.

Resource-adequacy IMPORT CAPABILITY HOLDINGS — the MW of RA import capability
each load-serving entity holds on each intertie branch group for an RA year,
as the ISO publishes it after its annual allocation process. Each ISO's
published layout is reconciled onto ONE tidy frame declared in
``data/dictionary/schema/ra-import-allocations.schema.yaml``.

Per-ISO logic lives in sibling modules (``caiso.py``, ...), each of which
registers an ``IsoSpec`` via :func:`register`. Shared code never branches on
the ISO name — it looks the spec up in :data:`REGISTRY`; new ISOs are additive
(drop a module, register a spec), per ``docs/adding-new-data-types.md``. The
registry scaffolding is built by
:func:`scripts.lib.datatype_registry.make_registry`; only the columns, the
spec fields and :func:`validate_tidy` are datatype-specific and live here.

Intake-only as of caiso-245: no model mechanism consumes it (the
pre-registered arm's stop rule fired —
``results/calibration/FINDING-caiso245-firm-import-allocation-split-2026-09-04.md``).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "ra-import-allocations"

#: Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "delivery_year",
    "lse",
    "branch_group",
    "allocation_mw",
    "start_date",
    "end_date",
    "source_doc",
)

_STRING_COLS = ("iso", "delivery_year", "lse", "branch_group", "source_doc")
_FLOAT_COLS = ("allocation_mw",)

_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
        ("parse", "Callable[[Path], pd.DataFrame]"),
        ("years", "Callable[[Path], list[int]]"),
        ("source", str),
    ],
    package=__name__,
    iso_modules=("caiso",),
    raw_subpath=(DATATYPE,),
    string_cols=_STRING_COLS,
    float_cols=_FLOAT_COLS,
    sort_by=("delivery_year", "lse", "branch_group", "start_date"),
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
raw_dir_for = _R.raw_dir_for
finalize = _R.finalize


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Value-level checks the schema cannot express; raises ``ValueError``.

    Every holding must be a positive MW quantity inside its own RA year, and
    the (lse, branch_group, window) key must be unique — the published sheets
    carry one row per holding, so a duplicate means a parse defect, never a
    quantity to sum silently.
    """
    problems: list[str] = []
    if bool((df["allocation_mw"] <= 0).any()):
        problems.append(
            f"{int((df['allocation_mw'] <= 0).sum())} non-positive allocation_mw row(s)"
        )
    yr_start = pd.to_datetime(df["start_date"]).dt.year.astype(str)
    if bool((yr_start != df["delivery_year"]).any()):
        problems.append("start_date year differs from delivery_year on some rows")
    key = ["iso", "delivery_year", "lse", "branch_group", "start_date", "end_date"]
    dups = int(df.duplicated(key).sum())
    if dups:
        problems.append(f"{dups} duplicate holding key(s)")
    if problems:
        raise ValueError(
            "ra-import-allocations tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw workbooks into a validated canonical frame."""
    spec = load_registry()[iso.upper()]
    df = finalize(spec.parse(Path(raw_root)))
    if df.empty:
        return df
    return validate_tidy(df)
