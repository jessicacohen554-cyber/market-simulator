"""NWPP transfer-interface-limits spec: BPA OPI intertie operating limits.

Source: BPA Transmission "OPI Interties & Flowgates" monthly spreadsheets,
fetched by ``scripts/data/fetch_bpa_intertie_otc.py`` and folded into the
committed ``data/raw/nwpp-intertie-otc/bpa_intertie_otc_<year>.parquet``
(long: ``path``, ``ts_end_local``, ``actual_mw``, ``ns_ttc_mw``,
``sn_ttc_mw``, ``loop_mw``; 15-minute rows, Pacific prevailing period-ending
stamps, values and signs exactly as published). The README in that
directory records the source, its SCADA points and its sign conventions.

Each intertie (``AC`` -> ``COI``, ``BC`` -> ``BC``) and direction becomes one
limit SERIES, named ``"<COI|BC>|<NS|SN>|OTC"``: BPA's operating limit (the
SOL it monitors against, all owners), as published. The S-N limit of COI and
the N-S limit of the BC Intertie are published NEGATIVE and are kept that
way (the schema's faithful-to-source contract); the model-side consumer
(``market_sim.data.transfer_interface_limits.nwpp_seam_limits_hourly``) takes
each direction's magnitude.

``transfer_mw`` carries the path's measured actual loading (COI: + = to
California; BC: + = to BC). Diagnostic only, never a model input or target
(rule 13).

``tz`` is fixed PST (``Etc/GMT+8``), not prevailing Pacific time: NWPP's
dispatch clock is the fixed-PST non-leap 8760 clock
(``market_sim.data.eia930.demand``), so the partition lands on the hours the
LP solves with no DST shift. The four 15-minute rows of an hour are averaged
into the hour (the parse floors each row's interval start to its UTC hour).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import IsoSpec, register

#: Folded ``path`` code -> published series prefix.
PATH_NAMES: dict[str, str] = {"AC": "COI", "BC": "BC"}

#: Folded limit column -> direction tag (N-S = toward California / the US).
LIMIT_COLUMNS: dict[str, str] = {"ns_ttc_mw": "NS", "sn_ttc_mw": "SN"}

#: Length of one published row (the 15-minute SCADA average).
ROW_MINUTES = 15


def series_name(path: str, direction: str) -> str:
    """Canonical NWPP series name, e.g. ``"COI|NS|OTC"``."""
    return f"{path}|{direction}|OTC"


def _utc_start(stamps: pd.Series) -> pd.DatetimeIndex:
    """Period-ending Pacific prevailing stamps -> UTC interval starts.

    The fall-back repeated hour is resolved by file order (``infer``); a
    block whose order does not allow inference falls back to marking the
    repeat as standard time, so no row is dropped.
    """
    local = pd.DatetimeIndex(stamps)
    try:
        aware = local.tz_localize(
            "America/Los_Angeles", ambiguous="infer", nonexistent="shift_forward"
        )
    except Exception:  # repeated stamps not in file order
        aware = local.tz_localize(
            "America/Los_Angeles", ambiguous=False, nonexistent="shift_forward"
        )
    return aware.tz_convert("UTC") - pd.Timedelta(minutes=ROW_MINUTES)


def _parse(path: Path) -> pd.DataFrame:
    """Parse one folded BPA year into the shared tidy parsed columns."""
    raw = pd.read_parquet(path)
    frames = []
    for code, name in PATH_NAMES.items():
        sub = raw[raw["path"].astype(str) == code].sort_values("ts_end_local")
        if sub.empty:
            continue
        start = _utc_start(sub["ts_end_local"]).floor("h")
        for col, tag in LIMIT_COLUMNS.items():
            frames.append(
                pd.DataFrame(
                    {
                        "interface": pd.Series(
                            series_name(name, tag), index=sub.index, dtype="string"
                        ),
                        "ts_utc": start,
                        "limit_mw": sub[col].astype("float64").to_numpy(),
                        "transfer_mw": sub["actual_mw"].astype("float64").to_numpy(),
                    }
                )
            )
    if not frames:
        return pd.DataFrame(columns=["interface", "ts_utc", "limit_mw", "transfer_mw"])
    out = pd.concat(frames, ignore_index=True)
    return out.dropna(subset=["interface", "ts_utc", "limit_mw"])


SPEC = register(
    IsoSpec(
        iso="NWPP",
        tz="Etc/GMT+8",
        raw_subdir="nwpp-intertie-otc",
        raw_glob="bpa_intertie_otc_*.parquet",
        parse=_parse,
    )
)
