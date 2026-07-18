"""PJM transfer-interface-limits spec (reference ISO implementation).

Source: PJM Data Miner 2 ``transfer_limits_and_flows``
(https://dataminer2.pjm.com/feed/transfer_limits_and_flows) — hourly rows per
published ``transfer_limit_area`` with the enforced ``transfer_limit`` (MW)
and measured ``transfers`` (MW). The committed raw drops are
``data/raw/iso-specific-transmission/PJM_<year>_transfer_limits_and_flows.csv``
(2023-2025; extendable via ``scripts/data/fetch_pjm_transmission.py`` — rule 22:
do not fetch outside authorized windows). Ten series in the drops: AP-South
and Bedington-BlackOak pre-/post-contingency, AEP/DOM, 50045005, Cleveland,
and the Average Western/Central/Eastern regional envelopes.

The rows are UTC-keyed (``datetime_beginning_utc``) and complete — one row
per series per UTC hour — so the shared clock reconciliation
(:func:`..to_model_clock`) only has to handle the EPT wall-clock DST
merge/fill. PJM's EPT is America/New_York prevailing time.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import IsoSpec, register

# Columns consumed from the Data Miner 2 CSV (full header documented in
# data/raw/iso-specific-transmission/README.md).
_USECOLS = [
    "datetime_beginning_utc",
    "transfer_limit_area",
    "transfers",
    "transfer_limit",
]

# Data Miner 2 timestamp rendering, e.g. "1/1/2024 5:00:00 AM".
_TS_FORMAT = "%m/%d/%Y %I:%M:%S %p"

# The ten series the 2023-2025 drops carry. Documentary constant — the parser
# does not require series to be in this set (a future drop may add areas),
# but it records the expected vocabulary for reviewers and tests.
EXPECTED_INTERFACES: tuple[str, ...] = (
    "50045005 Post-Contingency",
    "AEP/DOM Post-Contingency",
    "AP-South Post-Contingency",
    "AP-South Pre-Contingency",
    "Average Central",
    "Average Eastern",
    "Average Western",
    "Bedington-BlackOak Post-Contingency",
    "Bedington-BlackOak Pre-Contingency",
    "Cleveland",
)


def _parse(path: Path) -> pd.DataFrame:
    """Parse one Data Miner 2 CSV into the shared tidy parsed columns."""
    df = pd.read_csv(path, usecols=_USECOLS)
    ts = pd.to_datetime(df["datetime_beginning_utc"], format=_TS_FORMAT).dt.tz_localize(
        "UTC"
    )
    out = pd.DataFrame(
        {
            "interface": df["transfer_limit_area"].astype("string"),
            "ts_utc": ts,
            "limit_mw": df["transfer_limit"].astype("float64"),
            "transfer_mw": df["transfers"].astype("float64"),
        }
    )
    return out.dropna(subset=["interface", "ts_utc", "limit_mw"])


SPEC = register(
    IsoSpec(
        iso="PJM",
        tz="America/New_York",
        raw_subdir="iso-specific-transmission",
        raw_glob="PJM_*_transfer_limits_and_flows.csv",
        parse=_parse,
    )
)
