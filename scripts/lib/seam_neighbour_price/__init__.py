"""Shared contract for the ``seam-neighbour-price`` clean datatype.

Hourly prices at BOTH ends of an ISO's external seams: the home ISO's price at
its proxy buses / landing zones, and each neighbour's own price at the node
facing the home ISO.  Built for NYISO-NEXT-10 (NEXT-7 FINDING §3(c)): a
per-neighbour seam construction needs each seam's spread, not the home price.

One tidy frame, declared in
``data/dictionary/schema/seam-neighbour-price.schema.yaml``.  Each publishing
market has its own sibling module (``nyiso.py``, ``pjm.py``, ``neiso.py``,
``ieso.py``) registering an :class:`IsoSpec` whose ``parse(raw_dir, year)``
returns that market's rows for one year; shared code never branches on the ISO
(``docs/adding-new-data-types.md``).  Raw lives under
``data/raw/seam-neighbour-price/<iso>/``, written by
``scripts/data/fetch_seam_neighbour_price_<iso>.py``.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "seam-neighbour-price"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "node",
    "market",
    "interval_start_utc",
    "home_iso",
    "seam_group",
    "currency",
    "price",
    "price_usd",
)

_reg = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
        ("parse", Callable),
        ("years", tuple, ()),
        ("source", str, ""),
    ],
    package=__name__,
    iso_modules=("nyiso", "pjm", "neiso", "ieso"),
    raw_subpath=("seam-neighbour-price",),
    string_cols=("iso", "node", "market", "home_iso", "seam_group", "currency"),
    float_cols=("price", "price_usd"),
    sort_by=("iso", "node", "market", "interval_start_utc"),
)
IsoSpec = _reg.IsoSpec
REGISTRY = _reg.REGISTRY
register = _reg.register
load_registry = _reg.load_registry
raw_dir_for = _reg.raw_dir_for


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to canonical dtypes/order; keep ``interval_start_utc`` tz-aware UTC."""
    out = _reg.finalize(df)
    out["interval_start_utc"] = pd.to_datetime(out["interval_start_utc"], utc=True)
    return out


def local_seq_to_utc(date: pd.Series, seq: pd.Series, tz: str) -> pd.Series:
    """UTC hour start from (local operating date, 0-based hour position).

    Position within the day is what makes DST days (23 / 25 rows) carry through:
    row ``k`` begins exactly ``k`` real hours after that day's local midnight.
    """
    midnight = pd.to_datetime(date).dt.tz_localize(tz)
    return midnight.dt.tz_convert("UTC") + pd.to_timedelta(seq.astype(int), unit="h")
