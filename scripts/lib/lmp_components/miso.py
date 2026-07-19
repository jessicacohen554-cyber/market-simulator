"""MISO ``lmp-components`` spec (daily ex-post report hub rows, D6 staging).

Parses the committed D6 hub staging
``data/raw/lmp-data/MISO/miso_hub_lmp_<year>_<market>.csv.gz`` (2023-2025;
later years as ``_p<NN>.csv`` chunks — verbatim ``LMP``/``MCC``/``MLC``
rows for the eight named MISO trading hubs from the daily
``YYYYMMDD_da_expost_lmp.csv`` / ``YYYYMMDD_rt_lmp_final.csv`` market
reports; see ``data/raw/lmp-components/README.md`` for the shared-staging
rationale) into the canonical tidy frame: one row per (node, hour) with the
three component columns pivoted wide.

Timestamp basis: the reports are hour-ending 1-24 in Eastern Standard Time
YEAR-ROUND (no DST — each daily file's header states it; same fixed UTC-5
convention as ``scripts/lib/transfer_constraint_binding/miso.py`` and
``scripts/data/derive_miso_hub_lmp.py``). Hour-beginning EST = market date
+ (HE-1) hours; UTC = EST + 5 hours. Values are verbatim: blank source
cells become null, never imputed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import CANONICAL_COLUMNS, IsoSpec, register

# MISO market time is EST year-round (no DST): fixed UTC-5.
_EST_UTC_OFFSET_HOURS = 5

# HE 1-24 staging columns (no DST hour under the fixed-offset clock).
_N_HOURS = 24
_HE_COLS = [f"he{h:02d}" for h in range(1, _N_HOURS + 1)]

# The staged component row labels, pivoted to these canonical columns.
_TYPE_TO_COLUMN = {
    "LMP": "lmp_usd_per_mwh",
    "MCC": "mcc_usd_per_mwh",
    "MLC": "mlc_usd_per_mwh",
}


def _staged_paths(raw_dir: Path, year: int, market: str) -> list[Path]:
    """Staged file(s) for (year, market): legacy yearly gzip, else chunks.

    Same resolution rule as ``derive_miso_hub_lmp._staged_paths``:
    2023-2025 ship as one ``miso_hub_lmp_<year>_<market>.csv.gz`` per year;
    2022+ (API-era fetches) as ~7-day plain-CSV ``_p<NN>`` chunks. Prefer
    the legacy yearly file if both exist.
    """
    legacy = raw_dir / f"miso_hub_lmp_{year}_{market}.csv.gz"
    if legacy.is_file():
        return [legacy]
    return sorted(raw_dir.glob(f"miso_hub_lmp_{year}_{market}_p??.csv"))


def _empty() -> pd.DataFrame:
    """Canonical empty frame for an absent (market, year) staging."""
    return pd.DataFrame(columns=list(CANONICAL_COLUMNS))


def parse(raw_dir: Path, market: str, year: int) -> pd.DataFrame:
    """Parse one (market, year) staging to the canonical tidy frame."""
    paths = _staged_paths(raw_dir, year, market)
    if not paths:
        return _empty()
    staged = pd.concat((pd.read_csv(p, dtype=str) for p in paths), ignore_index=True)
    staged = staged[staged["value"].isin(_TYPE_TO_COLUMN)]
    if staged.empty:
        return _empty()

    # Hour-beginning EST wall clock: market date 00:00 + (HE-1) hours, one
    # row per staged (node, component) row x 24 HE columns (vectorized).
    day = pd.to_datetime(staged["date"], format="%Y-%m-%d").to_numpy()
    est = (day[:, None] + np.arange(_N_HOURS) * np.timedelta64(1, "h")).ravel()
    values = (
        staged[_HE_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float).ravel()
    )
    long = pd.DataFrame(
        {
            "node": np.repeat(staged["node"].to_numpy(), _N_HOURS),
            "node_type": np.repeat(staged["type"].to_numpy(), _N_HOURS),
            "component": np.repeat(
                staged["value"].map(_TYPE_TO_COLUMN).to_numpy(), _N_HOURS
            ),
            "interval_start_est": est,
            "value": values,
        }
    )
    wide = (
        long.pivot_table(
            index=["node", "node_type", "interval_start_est"],
            columns="component",
            values="value",
            # A duplicated staged row (re-fetch overlap) carries identical
            # values; mean collapses it without inventing data.
            aggfunc="mean",
        )
        .reindex(columns=list(_TYPE_TO_COLUMN.values()))
        .reset_index()
    )
    wide.columns.name = None

    est_idx = pd.DatetimeIndex(wide["interval_start_est"])
    out = pd.DataFrame(
        {
            "iso": "MISO",
            "market": market,
            "node": wide["node"],
            "node_type": wide["node_type"],
            "interval_start_utc": (
                est_idx + pd.Timedelta(hours=_EST_UTC_OFFSET_HOURS)
            ).tz_localize("UTC"),
            "interval_start_est": wide["interval_start_est"],
            "lmp_usd_per_mwh": wide["lmp_usd_per_mwh"],
            "mcc_usd_per_mwh": wide["mcc_usd_per_mwh"],
            "mlc_usd_per_mwh": wide["mlc_usd_per_mwh"],
        }
    )
    out = (
        out[list(CANONICAL_COLUMNS)]
        .sort_values(["node", "interval_start_utc"])
        .reset_index(drop=True)
    )
    return out


register(IsoSpec(iso="MISO", raw_subdir="lmp-data/MISO", parse=parse))
