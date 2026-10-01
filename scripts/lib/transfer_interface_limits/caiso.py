"""CAISO transfer-interface-limits spec: OASIS ``TRNS_USAGE`` (DAM) intertie ratings.

Source: CAISO OASIS ``queryname=TRNS_USAGE&market_run_id=DAM``, fetched by
``scripts/data/fetch_caiso_trns_usage.py`` and folded into the committed
``data/raw/caiso-trns-usage/caiso_trns_usage_dam_<year>.parquet`` (wide: one
row per UTC hour x ``ti_id`` x ``ti_constraint_id`` x ``direction``, one
column per published item). Retained history starts 2023-06-19 (OASIS
~39-month rolling retention, measured 2026-10-01); the README in that
directory records what is lost.

Each (ITC, direction) is split into four limit SERIES, named
``"<ti_id>|<direction>|<item>"`` (``direction`` I = import, E = export):

* ``OTC``  -- ``OTC_MW``, CAISO's "Hourly TTC": the hourly operating transfer
  capability after derates. The rule-14 measured counterpart of the model's
  corridor caps.
* ``TTC``  -- ``TTC_MW``, the seasonal path rating.
* ``TRM``  -- ``TRM_MW``, total transmission reliability margin.
* ``MTC``  -- ``MKT_XFER_CAP_MW``, the market transfer capability IFM enforces.

``transfer_mw`` carries ``ENE_IMPORT_MW`` — the DAM SCHEDULED net energy from
imports/exports on that ITC (sign as published: positive = net import), NOT a
metered flow. Diagnostic only, never a model input or target (rule 13).

``99999`` is OASIS's "unlimited" sentinel (the ``CISO_NET_*`` aggregates) and
is kept verbatim per the schema's "faithful to the source" contract.

``max_fill_hours = 1``: only the spring-forward hour is filled; the months
before retention starts are absent, not invented. Rows carry Pacific
prevailing time (America/Los_Angeles).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import IsoSpec, register

# Published item -> short series tag. The four limit items this datatype
# carries; the other nine TRNS_USAGE items stay in the committed raw parquet.
LIMIT_ITEMS: dict[str, str] = {
    "OTC_MW": "OTC",
    "TTC_MW": "TTC",
    "TRM_MW": "TRM",
    "MKT_XFER_CAP_MW": "MTC",
}

# Scheduled DAM net energy, carried as the diagnostic transfer column.
SCHEDULE_ITEM = "ENE_IMPORT_MW"


def series_name(ti_id: str, direction: str, tag: str) -> str:
    """Canonical CAISO series name, e.g. ``"MALIN500_ISL|I|OTC"``."""
    return f"{ti_id}|{direction}|{tag}"


def _parse(path: Path) -> pd.DataFrame:
    """Parse one folded TRNS_USAGE year into the shared tidy parsed columns."""
    w = pd.read_parquet(path)
    if (w["ti_id"] != w["ti_constraint_id"]).any():
        raise ValueError(f"{path.name}: ti_constraint_id differs from ti_id")
    frames = []
    for item, tag in LIMIT_ITEMS.items():
        frames.append(
            pd.DataFrame(
                {
                    "interface": (
                        w["ti_id"].astype(str)
                        + "|"
                        + w["direction"].astype(str)
                        + f"|{tag}"
                    ).astype("string"),
                    "ts_utc": pd.to_datetime(w["interval_start_utc"], utc=True),
                    "limit_mw": w[item].astype("float64"),
                    "transfer_mw": w[SCHEDULE_ITEM].astype("float64"),
                }
            )
        )
    out = pd.concat(frames, ignore_index=True)
    return out.dropna(subset=["interface", "ts_utc", "limit_mw"])


SPEC = register(
    IsoSpec(
        iso="CAISO",
        tz="America/Los_Angeles",
        raw_subdir="caiso-trns-usage",
        raw_glob="caiso_trns_usage_dam_*.parquet",
        parse=_parse,
        max_fill_hours=1,
    )
)
