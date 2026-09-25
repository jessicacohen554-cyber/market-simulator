"""Derive actual historical average LMP per ISO/year for the dashboard.

The backcast dashboard's summary page compares the model's average LMP against
the actual historical market price. Parsing the raw ERCOT settlement-point
workbooks (20+ MB xlsx, 15-minute real-time intervals) on every dashboard
render would be slow and would pull ``openpyxl`` into the render path, so this
script reduces the raw price files to a tiny committed reference,
``data/raw/_validation-source/actual_lmp.json``:

    {"ERCOT": {"2024": {"da": 28.09, "rt": 26.83,
                        "da_mon": [...12...], "rt_mon": [...12...],
                        "src": "..."}, ...},
     "PJM":   {"2024": {"da": 29.78, "rt": 29.53,
                        "da_pct": {"min": ..., "p1": ..., ..., "max": ...},
                        "rt_pct": {...}, ...}, ...}}

``da`` / ``rt`` are the annual mean day-ahead / real-time price in $/MWh, and
``da_mon`` / ``rt_mon`` the 12 monthly means (Jan-Dec; ``null`` for a month with
no data) feeding the summary page's monthly LMP table. All are taken from the
system-wide hub-average series of each market:

  * ERCOT — ``HB_HUBAVG`` settlement point in the DAM (hourly) and RTM
    (15-minute) Load-Zone/Hub settlement-point-price reports.
  * PJM — the mean across the 12 trading hubs in the hourly RT/DA LMP export.
  * CAISO — the three trading hubs (TH_NP15/TH_ZP26/TH_SP15) in the OASIS
    hourly aggregates (``scripts/data/postprocess_oasis_downloads.py``),
    load-weighted by zone share into a system price. DA is 2024-2025 only
    and RT 2024-2025 only: OASIS's ~39-month retention had already aged out
    most of 2023 DAM by the mid-2026 pull (only a few Feb-2023 trade dates
    survive), and 2023 RTM was never fetched.
  * NYISO — the eleven zonal LBMPs (DAM hourly / RTD 5-minute averaged to the
    hour) from ``NYISO/``. The system price is the simple mean of the eleven
    *internal* zones (the H Q / NPX / O H / PJM external-proxy buses are
    excluded); the five model zones are the simple mean of their constituent
    NYISO zones.
  * NEISO — the ISO-NE SMD ``*_smd_hourly.xlsx`` per-zone sheets (hourly
    ``DA_LMP`` / ``RT_LMP``) from ``NEISO/``. The system price is the
    ``.H.INTERNAL_HUB`` ("ISO NE CA" sheet); the four model zones are the
    simple mean of their constituent SMD load zones. ISO-NE ships those same
    nine pricing locations through a SECOND packaging — the ungated daily
    historical-report tree, reduced to
    ``NEISO/smd-zonal-lmp/NEISO_smd_zonal_lmp_<year>.csv`` by
    ``scripts/data/fetch_neiso_smd_zonal_lmp.py`` — which supplies years the
    CAPTCHA-gated workbook form cannot deliver to an unattended session
    (H1-2026). The two are ONE input, measured identical at the parquet's
    float32 precision by ``scripts/probes/neiso96_smd_route_equivalence.py``;
    see :func:`neiso_zone_hourly` for which is read when, and for the
    2018-2023 workbook DST defect that comparison exposed.

  * SPP — the two SPP trading hubs (``SPPNORTH_HUB`` / ``SPPSOUTH_HUB``) from
    the SPP Integrated Marketplace monthly settlement-location files; the
    system price is their simple mean. SPP's raw exports are not staged in the
    repo, so unlike every builder above :func:`_spp` reads the COMMITTED hourly
    sidecars ``actual_lmp_hourly_SPP.parquet`` and
    ``actual_lmp_hourly_zonal_SPP.parquet`` (fetched by
    ``scripts/data/build_spp_lmp_reference.py``, lanes SPP-12/SPP-14) and emits
    no hourly frame, so this script never rewrites them.

The zonal ISOs (NYISO, NEISO, SPP) additionally carry a ``zones`` sub-dict —
``{key: {da, rt, da_mon, rt_mon}}`` — alongside the hub-level
``da``/``rt``/``*_mon``/``*_pct``; the dashboard reads only the top-level hub
fields, so the sub-dict is additive and leaves the ERCOT/PJM/CAISO blocks
byte-identical. The key is a MODEL ZONE for NYISO/NEISO (and for MISO, whose
block is built by ``scripts/data/build_miso_lmp_reference.py``) but a TRADING
HUB for SPP, whose two hubs are node clusters rather than zone averages — each
SPP record states this in its own ``comment`` field (:data:`SPP_HUB_COMMENT`).

For ISOs with a true hourly source (PJM, CAISO, and ERCOT — the ERCOT
HB_HUBAVG hub-average is itself the comparable system price, from the DAM
hourly and the RTM 15-minute intervals averaged to the hour), two extras are
produced for the price-duration-curve overlay (J3a):

  * ``da_pct`` / ``rt_pct`` in the JSON — duration-curve percentiles of the
    hub-mean hourly price (``p99`` is a high price, ``p1`` a low one).
  * ``data/raw/_validation-source/actual_lmp_hourly_{ISO}.parquet`` — the hub-mean
    hourly series itself (columns ``year``, ``hour``, ``rt``, ``da``), dense
    on the model's CHRONOLOGICAL 8760-hour calendar: row ``k`` is the k-th
    real (UTC) hour after local standard-time midnight Jan 1, with the local
    standard-time Feb 29 dropped. This is the clock every model series shares
    (``eia_loader._eia_hourly_frame`` sorts by UTC — a fixed-offset clock with
    no DST discontinuities), so the parquet pairs hour-for-hour with model
    output. The market reports label hours on each ISO's DST *prevailing*
    clock; every reader converts those labels to real instants (UTC) first,
    so the DST fall-back's two instances each occupy their own real slot (no
    averaging) and no spring-forward hour is NaN'd. (Until 2026-07-14 the
    parquet was indexed on the prevailing clock directly, which paired every
    hourly comparison one real hour off for the ~5,600 DST hours/year — the
    scoring-clock artifact in
    docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md §1.)

Run after refreshing ``data/raw/lmp-data/``; commit the JSON and the
hourly parquet. Missing source files for an ISO/year are skipped, so a
partial data drop still produces a valid reference. ``--parquet-only``
rebuilds the hourly parquets without rewriting the JSON: the JSON's legacy
``da``/``rt``/``*_mon`` means weight raw report rows directly and are
clock-invariant, but its ``*_pct`` fields are computed from the dense series,
whose completeness improved with the chronological clock (the fall-back
hour's two instances and the spring-forward hour are now real values) —
those cent-level deltas land only at the next authorized JSON re-derivation,
with citation (rule 23).

Usage:
    python scripts/data/derive_actual_lmp.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import io
import json
import sys
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import openpyxl
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402  (resolves the data root)

# Paths resolve through config/paths.py (CLAUDE.md: never hardcode the legacy
# inputs/ tree — the W1 relocation collapsed inputs/raw-data -> data/raw and
# inputs/calibration -> data/raw/_validation-source).
LMP_DIR = paths.RAW_DATA_DIR / "lmp-data"
#: Reduced daily historical-report route for NEISO (fetch_neiso_smd_zonal_lmp).
NEISO_REPORT_DIR = LMP_DIR / "NEISO" / "smd-zonal-lmp"
OUT = paths.CALIBRATION_DIR / "actual_lmp.json"
HOURLY_OUT = paths.CALIBRATION_DIR  # actual_lmp_hourly_{ISO}.parquet

DEFAULT_YEARS = (2023, 2024, 2025)

PJM_SRC = "PJM RT/DA LMP, mean of the 12 trading hubs (hourly)"
ERCOT_SRC = "ERCOT HB_HUBAVG settlement point price (DAM hourly / RTM 15-min)"
CAISO_SRC = (
    "CAISO OASIS hub LMPs (PRC_LMP DAM / PRC_INTVL_LMP RTM hourly), "
    "load-weighted across TH_NP15/TH_ZP26/TH_SP15"
)
NYISO_SRC = (
    "NYISO zonal LBMP (DAM hourly / RTD 5-min averaged to the hour); "
    "hub is the simple mean of the 11 internal zones, model zones the "
    "simple mean of their constituent NYISO zones"
)
NEISO_SRC = (
    "ISO-NE SMD hourly DA_LMP / RT_LMP; hub is the .H.INTERNAL_HUB "
    "(ISO NE CA sheet), model zones the simple mean of their "
    "constituent SMD load zones"
)
SPP_SRC = (
    "SPP Integrated Marketplace DA-LMP-MONTHLY-SL / RTBM-LMP-MONTHLY-SL "
    "(portal.spp.org), system hub = simple mean of SPPNORTH_HUB and "
    "SPPSOUTH_HUB (actual_lmp_hourly_SPP.parquet)"
)
SPP_ZONAL_SRC = (
    "SPP Integrated Marketplace per-hub DA / RTBM LMP "
    "(actual_lmp_hourly_zonal_SPP.parquet, lane SPP-14), keyed by SPP TRADING "
    "HUB — not by model zone"
)
#: Stated on every SPP record because the key names invite the wrong reading.
#: SPP's two trading hubs are fixed clusters of pricing nodes (their member
#: nodes and weights are ``data/raw/spp-planning/Hub_Definitions.csv``), NOT
#: area averages of the SPP-North / SPP-South model zones: SPPNORTH_HUB prices
#: a Nebraska node cluster and SPPSOUTH_HUB a central-Oklahoma one, each a
#: small part of the zone whose name it echoes. Treat a hub series as the
#: locational reference the market itself quotes, never as a zone mean.
SPP_HUB_COMMENT = (
    "zones[] keys are SPP TRADING HUBS, not model zones: SPPNORTH_HUB is a "
    "Nebraska node cluster and SPPSOUTH_HUB a central-Oklahoma node cluster "
    "(node weightings: data/raw/spp-planning/Hub_Definitions.csv). Neither is "
    "an average over the SPP-North / SPP-South model zone it is named after."
)

# CAISO has no single system hub; the comparable-to-the-model "system price"
# is the three trading hubs load-weighted by their zone shares (the same
# static ``load_share`` values in ``config.iso_configs``; WECC_import is 0).
CAISO_HUB_WEIGHTS = {
    "TH_NP15_GEN-APND": 0.3969,
    "TH_ZP26_GEN-APND": 0.0646,
    "TH_SP15_GEN-APND": 0.5385,
}
# CISO localizes to Pacific prevailing time, like the model's dispatch clock
# (``scripts/data/convert_eia930.py`` BA_TIMEZONES["CISO"], ``eia_loader``).
CAISO_TZ = "America/Los_Angeles"

# Fixed STANDARD-time zone per ISO (Etc/GMT+N == UTC-N, POSIX sign), the
# chronological clock the hourly parquets are indexed on. The model's 8760
# calendar (``eia_loader._eia_hourly_frame``: rows sorted by UTC from local
# standard midnight Jan 1) is exactly this fixed-offset clock, so the actuals
# must be too — NOT the prevailing (DST) clock the reports label hours with.
_STD_TZ = {
    "ERCOT": "Etc/GMT+6",  # CST
    "PJM": "Etc/GMT+5",  # EST
    "CAISO": "Etc/GMT+8",  # PST
    "NYISO": "Etc/GMT+5",  # EST
    "NEISO": "Etc/GMT+5",  # EST
}
# Prevailing (DST-following) zone used to turn report wall-clock labels into
# real instants before std-clock indexing.
_EASTERN_TZ = "America/New_York"
# Minimum valid system-hours to emit a CAISO year. OASIS's ~39-month retention
# aged out CAISO DAM/RTM before ~2023-03-10 (probed 2026-06-22: ERR 1000 before
# Mar 10, data from Mar 10 on), so the deepest 2023 reference we can fetch is
# Mar-Dec (~7.1k DAM / ~7.3k RTM hours). The guard sits below that span so the
# partial-but-substantial 2023 year scores (Jan-Feb stay NaN in the dense
# series and simply don't contribute), while still rejecting a true stub.
CAISO_MIN_HOURS = 6500
# Years for which that guard is relaxed to ``CAISO_MIN_HOURS_PARTIAL``, because
# the window is SHORT BY PUBLICATION, not by a failed fetch — the H1-2026
# locked-test edge is a deliberate half-year (Jan 1 - Jun 30, 4,344 h), and
# rejecting it would leave the forward-edge window with no bench at all. The
# uncovered hours stay NaN in the dense series and contribute to nothing, so a
# partial year still cannot masquerade as a full one; the set is explicit (and
# not derived from today's date) so the deriver stays deterministic.
CAISO_PARTIAL_YEARS: frozenset[int] = frozenset({2026})
CAISO_MIN_HOURS_PARTIAL = 2000
# Years short by IRRECOVERABLE ARCHIVE RETENTION rather than by publication or a
# failed fetch (i-caiso, 2026-09-24). 2021: OASIS GroupZip served trade dates
# from 2021-04-27 when the committed aggregates were crawled (caiso-263/274) and
# serves none before 2021-09 today (re-probed 2026-09-24: 2021-08-12 no data,
# 2021-09-01 served), so Jan 1 - Apr 26 can never be fetched and the committed
# DAM file (5,977 h) cannot clear ``CAISO_MIN_HOURS``. Same floor as
# ``CAISO_PARTIAL_YEARS``; the difference is that these records ALSO carry the
# ``da_cov``/``rt_cov`` vectors (:func:`_coverage`) the verdict's like-for-like
# month mask reads (``calibration_verdict._covered_months``), so a month the
# archive holds only a few days of is dropped from C3a/C3b rather than read as a
# full month. Kept a separate set so the 2026 record stays byte-identical.
CAISO_RETENTION_PARTIAL_YEARS: frozenset[int] = frozenset({2021})

# Duration-curve percentile levels for the ``da_pct`` / ``rt_pct`` records.
_PCT_LEVELS = (1, 5, 10, 25, 50, 75, 90, 95, 99)

# The model's fixed non-leap dispatch calendar (matches
# market_sim.data.campd: Feb 29 is dropped, hours are local clock).
_HOURS_PER_YEAR = 8760
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12))


def _by_month(values, months) -> list:
    """12 monthly means ($/MWh, rounded) from a value series labelled by month.

    ``months`` is a 1-12 month label per row; empty months come back ``None``.
    """
    out: list = [None] * 12
    g = pd.Series(list(values)).groupby(list(months)).mean()
    for m, v in g.items():
        if pd.notna(m) and 1 <= int(m) <= 12 and pd.notna(v):
            out[int(m) - 1] = round(float(v), 2)
    return out


def _std_hour_index(ts: pd.DatetimeIndex, year: int, std_tz: str) -> np.ndarray:
    """Chronological hour-of-year for tz-aware instants; out-of-scope -> -1.

    Converts real instants to the ISO's fixed standard-time clock (``std_tz``)
    and maps (month, day, hour) onto the non-leap 8760 calendar — row ``k`` is
    the k-th UTC hour after local standard midnight Jan 1. Rows outside
    ``year`` (a boundary spill from a prevailing-year source file) and the
    local standard-time Feb 29 map to -1 for the caller to drop.
    """
    std = ts.tz_convert(std_tz)
    month = np.asarray(std.month)
    day = np.asarray(std.day)
    idx = (
        np.asarray([_MONTH_START_HOUR[m - 1] for m in month])
        + (day - 1) * 24
        + np.asarray(std.hour)
    )
    ok = (np.asarray(std.year) == year) & ~((month == 2) & (day == 29))
    return np.where(ok, idx, -1)


def _pct(values: np.ndarray) -> dict:
    """Duration-curve summary of an hourly price series (NaNs ignored)."""
    out = {"min": round(float(np.nanmin(values)), 2)}
    for p in _PCT_LEVELS:
        out[f"p{p}"] = round(float(np.nanpercentile(values, p)), 2)
    out["max"] = round(float(np.nanmax(values)), 2)
    return out


def _hub_mean_hourly(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Hub-mean hourly RT/DA series on the dense chronological 8760 calendar.

    The raw export is one row per hub per hour and carries the real instant
    (``datetime_beginning_utc``) alongside the prevailing EPT label; the UTC
    column indexes the chronological calendar directly, so the DST fall-back
    hour's two instances land in their own slots and no hour is missing.
    """
    utc = pd.DatetimeIndex(
        pd.to_datetime(
            df["datetime_beginning_utc"],
            format="%m/%d/%Y %I:%M:%S %p",
            errors="coerce",
            utc=True,
        )
    )
    g = (
        df.assign(hour=_std_hour_index(utc, year, _STD_TZ["PJM"]))
        .query("hour >= 0")
        .groupby("hour")[["total_lmp_rt", "total_lmp_da"]]
        .mean()
    )
    dense = g.reindex(range(_HOURS_PER_YEAR))
    return pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": dense["total_lmp_rt"].to_numpy(np.float32),
            "da": dense["total_lmp_da"].to_numpy(np.float32),
        }
    )


def _pjm(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for PJM, or ``None`` if the file is absent.

    ``record`` is the ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}`` JSON
    entry; ``hourly`` the dense hub-mean hourly frame for the parquet sidecar.
    """
    f = LMP_DIR / f"PJM_{year}_rt_da_monthly_lmps.csv"
    if not f.exists():
        return None
    df = pd.read_csv(
        f,
        usecols=[
            "datetime_beginning_utc",
            "datetime_beginning_ept",
            "total_lmp_rt",
            "total_lmp_da",
        ],
    )
    mon = pd.to_datetime(
        df["datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
    ).dt.month
    hourly = _hub_mean_hourly(df, year)
    rec = {
        "da": round(float(df["total_lmp_da"].mean()), 2),
        "rt": round(float(df["total_lmp_rt"].mean()), 2),
        "da_mon": _by_month(df["total_lmp_da"], mon),
        "rt_mon": _by_month(df["total_lmp_rt"], mon),
        "da_pct": _pct(hourly["da"].to_numpy(float)),
        "rt_pct": _pct(hourly["rt"].to_numpy(float)),
        "src": PJM_SRC,
    }
    return rec, hourly


def _caiso_system_series(name: str, year: int) -> pd.Series | None:
    """Load-weighted CAISO hub system price, indexed by local Pacific time.

    ``name`` is the aggregate stem (``dam`` or ``rtm``). The per-year hourly
    aggregate (``scripts/data/postprocess_oasis_downloads.py``) is pivoted to one
    column per hub, weighted by ``CAISO_HUB_WEIGHTS`` into a single system
    price, and reindexed onto the Pacific wall clock. Returns ``None`` when
    the aggregate is missing, lacks a hub, or carries fewer than
    ``CAISO_MIN_HOURS`` complete hours — ``CAISO_MIN_HOURS_PARTIAL`` for a
    year in ``CAISO_PARTIAL_YEARS``, whose window is short by publication
    rather than by a failed fetch — i.e. cannot stand for a year (the
    retention-aged 2023 DAM stub and the unfetched 2023 RTM).
    """
    path = LMP_DIR / "CAISO" / f"CAISO_{name}_hourly_{year}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["interval_start_gmt", "node", "LMP"])
    wide = df.pivot_table(
        index="interval_start_gmt", columns="node", values="LMP", aggfunc="mean"
    )
    if not set(CAISO_HUB_WEIGHTS) <= set(wide.columns):
        return None
    wide = wide[list(CAISO_HUB_WEIGHTS)].dropna()
    floor = (
        CAISO_MIN_HOURS_PARTIAL
        if year in CAISO_PARTIAL_YEARS | CAISO_RETENTION_PARTIAL_YEARS
        else CAISO_MIN_HOURS
    )
    if len(wide) < floor:
        return None
    w = np.array(list(CAISO_HUB_WEIGHTS.values()))
    price = wide.to_numpy() @ (w / w.sum())
    ts = pd.to_datetime(wide.index, utc=True).tz_convert(CAISO_TZ)
    return pd.Series(price, index=ts, name="price")


def _densify_std(ser: pd.Series, year: int, std_tz: str) -> np.ndarray:
    """Dense chronological-8760 array from a tz-aware-indexed price series.

    The index must carry real instants (any tz); each maps to its own
    standard-clock slot via :func:`_std_hour_index` — the same calendar as
    :func:`_hub_mean_hourly`. Sub-hourly rows and true duplicate instants
    average within their slot; slots with no source hour stay NaN.
    """
    hour = _std_hour_index(pd.DatetimeIndex(ser.index), year, std_tz)
    g = pd.Series(ser.to_numpy()).groupby(hour).mean()
    g = g[g.index >= 0]
    return g.reindex(range(_HOURS_PER_YEAR)).to_numpy(float)


def _caiso(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for CAISO, or ``None`` if no usable year.

    Mirrors :func:`_pjm`: the ``{da, rt, da_mon, rt_mon, da_pct, rt_pct,
    src}`` record uses the load-weighted hub system price, and ``hourly`` is
    the dense system series for the parquet sidecar. DA and RT are emitted
    independently, so a year present in DAM but not RTM still produces a
    record (as ERCOT 2025 does with RT only).
    """
    series = {
        "da": _caiso_system_series("dam", year),
        "rt": _caiso_system_series("rtm", year),
    }
    if series["da"] is None and series["rt"] is None:
        return None
    parts: dict = {}
    dense: dict[str, np.ndarray] = {}
    for key, ser in series.items():
        if ser is None:
            dense[key] = np.full(_HOURS_PER_YEAR, np.nan)
            continue
        d = _densify_std(ser, year, _STD_TZ["CAISO"])
        dense[key] = d
        parts[key] = round(float(ser.mean()), 2)
        parts[f"{key}_mon"] = _by_month(ser.to_numpy(), pd.Series(ser.index).dt.month)
        parts[f"{key}_pct"] = _pct(d)
        if year in CAISO_RETENTION_PARTIAL_YEARS:
            parts[f"{key}_cov"] = _coverage(d, _month_of_hour())
    rec = {
        k: parts[k]
        for k in (
            "da",
            "rt",
            "da_mon",
            "rt_mon",
            "da_pct",
            "rt_pct",
            "da_cov",
            "rt_cov",
        )
        if k in parts
    }
    rec["src"] = CAISO_SRC
    hourly = pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": dense["rt"].astype(np.float32),
            "da": dense["da"].astype(np.float32),
        }
    )
    return rec, hourly


def _month_of(v) -> int | None:
    """Month (1-12) from an ERCOT date cell (``MM/DD/YYYY`` or a datetime)."""
    if v is None:
        return None
    if hasattr(v, "month"):
        return int(v.month)
    try:
        return int(str(v).strip().split("/")[0])
    except (ValueError, IndexError):
        return None


def _month_day(v) -> tuple[int, int] | None:
    """``(month, day)`` from an ERCOT date cell (``MM/DD/YYYY`` or a datetime)."""
    if v is None:
        return None
    if hasattr(v, "month"):
        return int(v.month), int(v.day)
    try:
        p = str(v).strip().split("/")
        return int(p[0]), int(p[1])
    except (ValueError, IndexError):
        return None


class _PrevailingShift:
    """Memoized prevailing-label -> standard-clock hour shift for one year.

    ERCOT reports label hours on the Central *prevailing* clock plus a
    "Repeated Hour Flag" that marks the second (post-fall-back, CST) instance
    of the duplicated hour. The chronological slot of a labelled hour is its
    prevailing hour-of-year minus 1 while DST is in effect (CDT = CST + 1),
    minus 0 otherwise; the flag resolves the one ambiguous wall hour per year
    ("N" = first/CDT instance, "Y" = second/CST instance). Nonexistent wall
    times (the spring-forward hour) never appear in the reports.
    """

    def __init__(self, year: int, tz_name: str):
        self._year = year
        self._zi = ZoneInfo(tz_name)
        self._memo: dict[tuple[int, int, int, bool], int] = {}

    def __call__(self, month: int, day: int, hod: int, repeated: bool) -> int:
        key = (month, day, hod, repeated)
        got = self._memo.get(key)
        if got is None:
            naive = _dt.datetime(self._year, month, day, hod)
            first = naive.replace(tzinfo=self._zi)
            ambiguous = (
                first.utcoffset() != naive.replace(tzinfo=self._zi, fold=1).utcoffset()
            )
            dst = (not repeated) if ambiguous else bool(first.dst())
            got = self._memo[key] = 1 if dst else 0
        return got


def _ercot_hubavg(
    zip_glob: str,
    year: int,
    name_col: int,
    price_col: int,
    hod_col: int,
    flag_col: int,
    hod_kind: str,
) -> dict | None:
    """``HB_HUBAVG`` annual/monthly means + dense hourly series for a workbook.

    Args:
        zip_glob: Glob (under ``LMP_DIR``) selecting the report zip.
        year: Calendar year of the workbook (resolves the DST windows).
        name_col: Zero-based column index of the settlement-point name.
        price_col: Zero-based column index of the settlement-point price.
        hod_col: Zero-based column index of the hour-of-day field — the DAM
            "Hour Ending" (``HH:00``) string or the RTM "Delivery Hour" (1-24)
            integer; hour-of-day is the field minus one (hour-beginning, the
            PJM convention).
        flag_col: Zero-based column index of the "Repeated Hour Flag" column
            ("Y" marks the second, post-fall-back instance of the duplicated
            prevailing hour).
        hod_kind: ``"he"`` for the DAM ``HH:00`` string, ``"int"`` for the RTM
            1-24 integer.

    Returns:
        ``{"ann": annual_mean, "mon": [12 monthly means or None],
        "hourly": np.ndarray[8760]}`` over every HB_HUBAVG row (the report's
        date column, index 0, gives the month/day), or ``None`` when no
        matching zip is present. The annual/monthly means weight every raw row
        equally (15-minute intervals for RTM, including Feb 29 and the
        duplicated DST fall-back hour) — unchanged from the pre-hourly code.
        The ``hourly`` series lands on the chronological standard-clock
        calendar (:class:`_PrevailingShift`): Feb 29 is dropped, the RTM
        15-minute intervals average into their hour, and the fall-back hour's
        two instances occupy their own real slots — every real hour present.
    """
    # rglob, not glob: the 2023-2025 archives sit at the ``lmp-data/`` top
    # level (hand-downloaded, pre-dating the per-ISO split) while the
    # 2018-2022 + 2026 holdout intake landed under ``lmp-data/ERCOT/`` per the
    # directory's per-ISO convention. Searching recursively resolves either
    # layout without moving a committed byte.
    paths = sorted(LMP_DIR.rglob(zip_glob))
    if not paths:
        return None
    with zipfile.ZipFile(paths[0]) as z:
        inner = next(n for n in z.namelist() if n.endswith(".xlsx"))
        data = z.read(inner)
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    # ERCOT's 2018-2019 annual workbooks ship a bogus ``<dimension ref="A1:A1">``.
    # openpyxl's read-only reader trusts that header and truncates every row to
    # a single cell, so each sheet yields one 1-tuple and every HB_HUBAVG row
    # silently vanishes — the year produces no record at all rather than an
    # error. ``calculate_dimension(force=True)`` returns the cached A1:A1 too,
    # so the only fix is to re-open unsized workbooks in normal (non-read-only)
    # mode, where dimensions are computed from the cells themselves. 2020+
    # workbooks declare correct dimensions and keep the streaming read-only
    # path untouched, so the committed years re-derive bit-identically.
    if wb[wb.sheetnames[0]].max_column <= price_col:
        wb.close()
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    shift = _PrevailingShift(year, "America/Chicago")
    msum, mcnt = [0.0] * 12, [0] * 12
    hsum = np.zeros(_HOURS_PER_YEAR)
    hcnt = np.zeros(_HOURS_PER_YEAR, dtype=np.int64)
    for sheet in wb.sheetnames:
        rows = wb[sheet].iter_rows(values_only=True)
        next(rows, None)  # header
        for r in rows:
            if r is None or len(r) <= price_col:
                continue
            if r[name_col] == "HB_HUBAVG" and r[price_col] is not None:
                price = float(r[price_col])
                mo = _month_of(r[0])
                if mo is None:
                    continue
                msum[mo - 1] += price
                mcnt[mo - 1] += 1
                md = _month_day(r[0])
                if md is None:
                    continue
                m, d = md
                if m == 2 and d == 29:  # model calendar drops Feb 29
                    continue
                hod = (
                    int(str(r[hod_col]).split(":")[0]) - 1
                    if hod_kind == "he"
                    else int(r[hod_col]) - 1
                )
                hoy = (
                    _MONTH_START_HOUR[m - 1]
                    + (d - 1) * 24
                    + hod
                    - shift(m, d, hod, str(r[flag_col]).strip().upper() == "Y")
                )
                if 0 <= hoy < _HOURS_PER_YEAR:
                    hsum[hoy] += price
                    hcnt[hoy] += 1
    wb.close()
    n = sum(mcnt)
    if not n:
        return None
    mon = [round(msum[i] / mcnt[i], 2) if mcnt[i] else None for i in range(12)]
    hourly = np.where(hcnt > 0, hsum / np.where(hcnt > 0, hcnt, 1), np.nan)
    return {"ann": sum(msum) / n, "mon": mon, "hourly": hourly}


def _ercot(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for ERCOT, or ``None`` if no usable year.

    Mirrors :func:`_pjm`: the ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}``
    record uses the ``HB_HUBAVG`` hub-average price (itself the comparable ERCOT
    system price), and ``hourly`` is the dense series for the parquet sidecar.
    DA and RT are emitted independently, so a year with only one workbook
    staged still produces a record (the other column is all-NaN).
    """
    # DAM columns: Date, Hour Ending(1), Repeated(2), Settlement Point(3), Price(4).
    da = _ercot_hubavg(f"*DAMLZHBSPP_{year}*.zip", year, 3, 4, 1, 2, "he")
    # RTM columns: Date, Hour(1), Interval, Repeated(3), Name(4), Type, Price(6).
    rt = _ercot_hubavg(f"*RTMLZHBSPP_{year}*.zip", year, 4, 6, 1, 3, "int")
    if da is None and rt is None:
        return None
    out: dict = {"src": ERCOT_SRC}
    da_h = da["hourly"] if da is not None else np.full(_HOURS_PER_YEAR, np.nan)
    rt_h = rt["hourly"] if rt is not None else np.full(_HOURS_PER_YEAR, np.nan)
    if da is not None:
        out["da"], out["da_mon"] = round(da["ann"], 2), da["mon"]
        out["da_pct"] = _pct(da_h)
    if rt is not None:
        out["rt"], out["rt_mon"] = round(rt["ann"], 2), rt["mon"]
        out["rt_pct"] = _pct(rt_h)
    hourly = pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": rt_h.astype(np.float32),
            "da": da_h.astype(np.float32),
        }
    )
    return out, hourly


# ── NYISO / NEISO (zonal) ───────────────────────────────────────────────────
# NYISO publishes eleven load zones; the model folds them into five. The four
# external-proxy buses (H Q Hydro-Québec, NPX New England, O H Ontario, PJM)
# are excluded from the internal-zone system price — they are import nodes, not
# NY load zones (they can sanity-check the P9 import tie, out of scope here).
NYISO_INTERNAL = (
    "WEST",
    "GENESE",
    "CENTRL",
    "NORTH",
    "MHK VL",
    "CAPITL",
    "HUD VL",
    "MILLWD",
    "DUNWOD",
    "N.Y.C.",
    "LONGIL",
)
NYISO_ZONE_MAP: dict[str, list[str]] = {
    "Upstate_West": ["WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"],
    "Capital_Hudson": ["CAPITL"],
    "Lower_Hudson": ["HUD VL", "MILLWD", "DUNWOD"],
    "NYC": ["N.Y.C."],
    "Long_Island": ["LONGIL"],
}

# ISO-NE SMD per-zone sheets folded into the four model zones; the hub is the
# system "ISO NE CA" sheet (.H.INTERNAL_HUB). In every SMD sheet DA_LMP is
# column 4 and RT_LMP column 8 (0-based), and Hr_End ("01".."24") is
# hour-ending on the Eastern prevailing clock: the spring-forward day has 23
# rows (Hr_End "02" absent), the fall-back day 25 ("02X" marks the repeated
# hour). Leap years carry Feb 29.
NEISO_HUB_SHEET = "ISO NE CA"
NEISO_DA_COL, NEISO_RT_COL = 4, 8
NEISO_ZONE_MAP: dict[str, list[str]] = {
    "North": ["ME", "NH", "VT"],
    "Central": ["WCMA", "SEMA", "RI"],
    "Boston": ["NEMA"],
    "Connecticut": ["CT"],
}


def _read_nyiso_csv(data: bytes) -> pd.DataFrame:
    """Parse one NYISO daily zone CSV's timestamp / name / price columns."""
    return pd.read_csv(
        io.BytesIO(data), usecols=["Time Stamp", "Name", "LBMP ($/MWHr)"]
    ).rename(columns={"LBMP ($/MWHr)": "lmp"})


def _localize_ordered(ts: pd.Series, by: pd.Series, tz: str) -> pd.DatetimeIndex:
    """Real instants from prevailing wall-clock stamps, by row order.

    NYISO files carry no timezone column, so the duplicated fall-back hour is
    two identical wall-clock stamps; within each ``by`` group (zone) and local
    date the rows are chronological, so a stamp at or below the group's
    running maximum is the second (post-fall-back, EST) instance. That flag
    feeds ``tz_localize(ambiguous=...)`` (True = first/DST instance); the
    spring-forward hour never appears in the files, so nonexistent stamps
    raise rather than being silently repaired.
    """
    ns = ts.to_numpy("datetime64[ns]").astype("int64")
    prev_max = (
        pd.Series(ns)
        .groupby([by.to_numpy(), ts.dt.normalize().to_numpy()], sort=False)
        .transform(lambda x: x.cummax().shift(1))
    )
    second = ns <= prev_max.to_numpy()  # NaN compares False: first row stays first
    return pd.DatetimeIndex(ts).tz_localize(tz, ambiguous=~second, nonexistent="raise")


def _nyiso_wide(year: int, kind: str) -> pd.DataFrame | None:
    """Hourly per-internal-zone NYISO LBMP wide frame for ``year`` / ``kind``.

    ``kind`` is ``"da"`` — the day-ahead monthly ``damlbmp_zone`` zips inside
    ``NYISO_zonal_hourly.zip``, already hourly — or ``"rt"`` — the flat monthly
    ``realtime_zone`` zips, 5-minute, averaged to the hour. Columns are the
    eleven internal zones (external-proxy buses dropped); the index is the
    real (UTC) hour via :func:`_localize_ordered`, so the DST fall-back
    hour's two instances stay distinct and no hour is missing. ``None`` if no
    source.

    The two products label intervals differently and are binned accordingly:
    RT 5-minute stamps are interval-**ending**, DA hourly stamps
    interval-**beginning** (see the shift below).
    """
    frames: list[pd.DataFrame] = []
    if kind == "da":
        outer_path = LMP_DIR / "NYISO" / "NYISO_zonal_hourly.zip"
        if not outer_path.exists():
            return None
        fmt = "%m/%d/%Y %H:%M"
        with zipfile.ZipFile(outer_path) as outer:
            for name in outer.namelist():
                base = name.rsplit("/", 1)[-1]
                if not (base.startswith(str(year)) and "damlbmp_zone" in base):
                    continue
                with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                    frames += [
                        _read_nyiso_csv(inner.read(dn))
                        for dn in inner.namelist()
                        if dn.endswith(".csv")
                    ]
    else:
        fmt = "%m/%d/%Y %H:%M:%S"
        for path in sorted((LMP_DIR / "NYISO").glob(f"{year}*realtime_zone_csv.zip")):
            with zipfile.ZipFile(path) as z:
                frames += [
                    _read_nyiso_csv(z.read(dn))
                    for dn in z.namelist()
                    if dn.endswith(".csv")
                ]
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    df = df[df["Name"].isin(NYISO_INTERNAL)]
    ts = pd.to_datetime(df["Time Stamp"], format=fmt, errors="coerce")
    df = df[ts.notna()]
    ts = ts[ts.notna()]
    utc = _localize_ordered(ts, df["Name"], _EASTERN_TZ).tz_convert("UTC")
    # The 5-minute RT ("P-24A") stamps label an interval by its END; the hourly
    # DA stamps label theirs by its BEGINNING. Shifting RT back one second
    # before the floor maps each interval onto the hour it actually priced —
    # the same convention curate_lmp.parse_nyiso_zip already uses. Adjudicated
    # against NYISO's OWN time-weighted hourly product (P-4A) rather than
    # assumed: ENDING agrees within $0.005 on all 65,384 strict zone-hours
    # sampled over 2022-2025, BEGINNING is wrong on 62,598 of them by up to
    # $151.67 (scripts/probes/nyiso_rtd_clock_adjudication.py; Manual 12 p.136
    # and Manual 14 §4 publish that P-4A is built from these 5-minute prices).
    # Subtracting in UTC keeps _localize_ordered's fall-back disambiguation
    # untouched and is exact, UTC having no DST discontinuity to cross.
    shift = pd.Timedelta(0) if kind == "da" else pd.Timedelta(seconds=1)
    df = df.assign(ts=(pd.DatetimeIndex(utc) - shift).floor("h"))
    # pivot_table mean folds the RT 5-minute intervals into one value per zone
    # per real hour; the fall-back hour's two instances are distinct UTC hours.
    return df.pivot_table(index="ts", columns="Name", values="lmp", aggfunc="mean")


def nyiso_zone_hourly(year: int, kind: str = "da") -> pd.DataFrame | None:
    """Model-zone (+ ``hub``) hourly NYISO LBMP frame for ``year`` / ``kind``.

    Columns are the five model zones (each the simple mean of its constituent
    NYISO internal zones) plus ``hub`` (the simple mean of all eleven internal
    zones), indexed by the real (UTC) hour. Shared by the JSON builder and the
    zonal-sufficiency test. ``None`` when the source files are absent.
    """
    wide = _nyiso_wide(year, kind)
    if wide is None:
        return None
    cols = {
        z: wide[[c for c in members if c in wide.columns]].mean(axis=1)
        for z, members in NYISO_ZONE_MAP.items()
    }
    present = [z for z in NYISO_INTERNAL if z in wide.columns]
    cols["hub"] = wide[present].mean(axis=1)
    return pd.DataFrame(cols)


def _neiso_real_day_hours(date: pd.Timestamp) -> int:
    """Real length of ``date``'s local calendar day in hours (23, 24 or 25)."""
    start = date.tz_localize(_EASTERN_TZ)
    end = (date + pd.Timedelta(days=1)).tz_localize(_EASTERN_TZ)
    return int((end - start) / pd.Timedelta(hours=1))


def _neiso_sheet_series(wb, sheet: str) -> dict[str, pd.Series]:
    """``{"da": series, "rt": series}`` of hourly LMP for one SMD sheet.

    The SMD sheets label hours on the Eastern prevailing clock. The 2024+
    workbook vintage publishes the market's true row count: 23 rows on the
    spring-forward day, 25 on the fall-back day (``Hr_End`` "02X" marks the
    repeated hour, which the old integer parse silently dropped). Within each
    Date the rows are chronological, so the k-th row of a day begins exactly k
    real hours after that day's (never-ambiguous) local midnight — the index
    is those UTC instants. Leap-day Feb 29 rows stay in (dropped only when
    densified onto the 8760 calendar).

    DST-NAIVE 2018-2023 VINTAGE (audit row O8; neiso-96 finding, neiso-97
    repair). The older vintage publishes a FLAT 24 rows on every calendar day,
    so the positional clock above cannot hold on its DST days. The true
    structure, adjudicated against the market's own daily hourly-LMP reports
    on every truth day available (2019-2023 both transitions, 2018 fall; all
    9 sheets x both markets, 0 mismatches --
    ``scripts/probes/neiso97_smd_dst_defect_quantify.py``):

    * spring-forward (23 real hours, 24 rows): row 1 is a FABRICATED
      nonexistent-02:00 entry — the mean of its two neighbours, exact to the
      cent on every sheet — and every true value from 01:00 on sits one row
      late. Placement: row 0 -> position 0, rows 2..23 -> positions 1..22,
      the phantom dropped. This recovers every published hour of the day.
    * fall-back (25 real hours, 24 rows): row 1 is the repeated hour's two
      instances COLLAPSED TO THEIR MEAN, and rows 2..23 are the true values
      for positions 3..24. Placement: row 0 -> position 0, rows 2..23 ->
      positions 3..24; the mean is dropped rather than fabricated onto either
      instance, leaving positions 1-2 absent here — the daily-report overlay
      in :func:`neiso_zone_hourly` supplies the two measured instances.

    A day whose row count matches neither its real length nor the flat-24
    pattern keeps the legacy positional placement unchanged.
    """
    rows = wb[sheet].iter_rows(values_only=True)
    next(rows, None)  # header
    by_day: dict[pd.Timestamp, list] = {}
    for r in rows:
        if r is None or r[0] is None or r[1] is None:
            continue
        he = str(r[1]).strip()
        if not he[:2].isdigit():
            continue
        date = pd.Timestamp(r[0]).normalize()
        by_day.setdefault(date, []).append((r[NEISO_DA_COL], r[NEISO_RT_COL]))
    idx: list = []
    da: list = []
    rt: list = []
    for date, day_rows in by_day.items():
        day_start = date.tz_localize(_EASTERN_TZ).tz_convert("UTC")
        n, n_real = len(day_rows), _neiso_real_day_hours(date)
        if n == 24 and n_real == 23:  # flat-24 spring-forward: drop the phantom
            placed = [(0, day_rows[0])] + [(k - 1, day_rows[k]) for k in range(2, 24)]
        elif n == 24 and n_real == 25:  # flat-24 fall-back: drop the pair mean
            placed = [(0, day_rows[0])] + [(k + 1, day_rows[k]) for k in range(2, 24)]
        else:  # true-shape day (n == n_real), or unknown: legacy positional
            placed = list(enumerate(day_rows))
        for pos, (da_v, rt_v) in placed:
            idx.append(day_start + pd.Timedelta(hours=pos))
            da.append(da_v)
            rt.append(rt_v)
    index = pd.DatetimeIndex(idx)
    return {
        "da": pd.Series(pd.to_numeric(da, errors="coerce"), index=index),
        "rt": pd.Series(pd.to_numeric(rt, errors="coerce"), index=index),
    }


def _neiso_flat24_dst_days(wb) -> list[tuple[pd.Timestamp, pd.Timestamp, int]]:
    """DST days a flat-24 workbook cannot represent: ``(start_utc, end_utc, real_hours)``.

    Counted on the hub sheet (the vintage is a property of the whole workbook;
    every sheet publishes the same per-day row count). Empty for the 2024+
    true-shape vintage, whose DST days match their real length.
    """
    rows = wb[NEISO_HUB_SHEET].iter_rows(values_only=True)
    next(rows, None)  # header
    counts: dict[pd.Timestamp, int] = {}
    for r in rows:
        if r is None or r[0] is None or r[1] is None:
            continue
        if not str(r[1]).strip()[:2].isdigit():
            continue
        date = pd.Timestamp(r[0]).normalize()
        counts[date] = counts.get(date, 0) + 1
    out = []
    for date, n in counts.items():
        n_real = _neiso_real_day_hours(date)
        if n == 24 and n_real in (23, 25):
            out.append(
                (
                    date.tz_localize(_EASTERN_TZ).tz_convert("UTC"),
                    (date + pd.Timedelta(days=1))
                    .tz_localize(_EASTERN_TZ)
                    .tz_convert("UTC"),
                    n_real,
                )
            )
    return out


#: ISO-NE location id -> SMD sheet name, for the daily historical-report route
#: (see :mod:`scripts.data.fetch_neiso_smd_zonal_lmp`). Same nine pricing
#: locations the workbook's per-zone sheets carry.
NEISO_REPORT_LOCATIONS: dict[str, str] = {
    "4000": NEISO_HUB_SHEET,
    "4001": "ME",
    "4002": "NH",
    "4003": "VT",
    "4004": "CT",
    "4005": "RI",
    "4006": "SEMA",
    "4007": "WCMA",
    "4008": "NEMA",
}


def _neiso_report_series(year: int, kind: str) -> dict[str, pd.Series] | None:
    """Per-SMD-sheet hourly series from the daily historical-report route.

    Reads the reduced ``NEISO_smd_zonal_lmp_<year>.csv`` written by
    :mod:`scripts.data.fetch_neiso_smd_zonal_lmp`, the ungated ISO-NE channel
    for the same nine SMD pricing locations the workbook publishes. ``None``
    when that file is absent.

    The clock is the SAME positional construction the workbook path uses --
    within an operating day the k-th published row begins exactly k real hours
    after that day's (never ambiguous) local midnight -- so the two routes land
    on identical instants. ``seq`` carries k as published, which is what makes
    the DST days (23 rows in spring, 25 in autumn) need no special case.
    """
    path = NEISO_REPORT_DIR / f"NEISO_smd_zonal_lmp_{year}.csv"
    if not path.exists():
        return None
    col = f"{kind}_lmp"
    acc: dict[str, dict[pd.Timestamp, float]] = {}
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            sheet = NEISO_REPORT_LOCATIONS.get(r["location_id"])
            if sheet is None:
                continue
            day_start = (
                pd.Timestamp(r["date"]).tz_localize(_EASTERN_TZ).tz_convert("UTC")
            )
            ts = day_start + pd.Timedelta(hours=int(r["seq"]))
            acc.setdefault(sheet, {})[ts] = float(r[col])
    return {sheet: pd.Series(v).sort_index() for sheet, v in acc.items()} or None


def neiso_zone_hourly(year: int, kind: str = "da") -> pd.DataFrame | None:
    """Model-zone (+ ``hub``) hourly NEISO LMP frame for ``year`` / ``kind``.

    Columns are the four model zones (each the simple mean of its constituent
    SMD load-zone sheets) plus ``hub`` (the .H.INTERNAL_HUB "ISO NE CA"
    sheet), indexed by the real (UTC) hour. Shared by the JSON builder and the
    zonal-sufficiency test. ``None`` when neither source is present.

    TWO PUBLISHED PACKAGINGS OF ONE INPUT (neiso-96, 2026-08-15). ISO-NE ships
    these nine SMD pricing locations both as the annual SMD hourly workbook and,
    day by day, through the static historical-report tree. The workbook is the
    original source here and is read first, so every committed year reproduces
    byte-for-byte; the daily-report reduction supplies years the workbook route
    cannot reach, because the workbook is served only behind a CAPTCHA-gated
    form and so cannot be refreshed by any committed script.

    This is source AVAILABILITY, not a year gate: the rule applied is uniform
    across years (take the SMD zonal series from whichever published packaging
    is on disk), and the two packagings are measured to agree exactly at the
    float32 precision the parquet stores --
    ``scripts/probes/neiso96_smd_route_equivalence.py``, 2,640 cells over 11
    sampled days of the committed years, 0 mismatches. Rule 22 as amended
    2026-08-06 is therefore satisfied in substance, not merely in form.

    The one measured exception was not a route difference but a DEFECT IN THE
    2018-2023 WORKBOOK VINTAGE, which publishes a flat 24 rows on every calendar
    day: on a 23-hour or 25-hour operating day it cannot align with the market's
    own published hours, so the positional clock displaced the rest of that day
    by an hour. The 2024-2025 vintage publishes the true 23 / 25 and agrees with
    the daily reports exactly. REPAIRED (neiso-97, audit row O8, owner-signed):
    :func:`_neiso_sheet_series` re-places the flat-24 DST days value-preservingly,
    and the one thing a re-placement cannot recover -- the fall-back repeated
    hour's two instances, which that vintage collapses to their mean -- is
    overlaid here from the daily historical-report route (the same publisher
    series, measured route-equivalent by neiso-96), day-scoped: ONLY a day the
    workbook cannot represent is taken from the report, so every true-shape day
    still reproduces from the workbook byte-for-byte.
    """
    raw: dict[str, pd.Series] = {}
    path = LMP_DIR / "NEISO" / f"{year}_smd_hourly.xlsx"
    if path.exists():
        needed = {NEISO_HUB_SHEET, *(s for ss in NEISO_ZONE_MAP.values() for s in ss)}
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        raw = {
            sh: _neiso_sheet_series(wb, sh)[kind]
            for sh in wb.sheetnames
            if sh in needed
        }
        fix_days = _neiso_flat24_dst_days(wb)
        wb.close()
        if fix_days:
            rep = _neiso_report_series(year, kind) or {}
            for sh, ser in raw.items():
                rser = rep.get(sh)
                if rser is None:
                    continue
                for day_start, day_end, n_real in fix_days:
                    truth = rser[(rser.index >= day_start) & (rser.index < day_end)]
                    if len(truth) != n_real:
                        continue  # no (or partial) report day: keep re-placement
                    ser = pd.concat(
                        [ser[(ser.index < day_start) | (ser.index >= day_end)], truth]
                    ).sort_index()
                raw[sh] = ser
    else:
        raw = _neiso_report_series(year, kind) or {}
    if not raw:
        return None
    cols: dict[str, pd.Series] = {}
    for z, sheets in NEISO_ZONE_MAP.items():
        avail = [raw[s] for s in sheets if s in raw]
        if avail:
            cols[z] = pd.concat(avail, axis=1).mean(axis=1)
    if NEISO_HUB_SHEET in raw:
        cols["hub"] = raw[NEISO_HUB_SHEET]
    return pd.DataFrame(cols) if cols else None


def _assemble_zonal(
    frames: dict[str, pd.DataFrame | None], year: int, src: str, std_tz: str
) -> tuple[dict, pd.DataFrame]:
    """Build the JSON record + dense hourly frame from model-zone/hub frames.

    ``frames`` maps ``"da"`` / ``"rt"`` to a model-zone-plus-``hub`` frame (or
    ``None``) indexed by tz-aware real instants. The top-level
    ``da``/``rt``/``*_mon``/``*_pct`` mirror the ERCOT/PJM/CAISO schema and
    carry the hub (monthly labels stay on the Eastern prevailing wall clock,
    as the raw reports label them); a ``zones`` sub-dict adds each model
    zone's ``da``/``rt``/``da_mon``/``rt_mon``. The dense 8760 hub series
    feeds the parquet sidecar (chronological ``std_tz`` calendar, same as the
    other ISOs).
    """
    parts: dict = {}
    zones_out: dict[str, dict] = {}
    dense: dict[str, np.ndarray] = {}
    for kind in ("da", "rt"):
        fr = frames.get(kind)
        if fr is None or "hub" not in fr.columns or not fr["hub"].notna().any():
            dense[kind] = np.full(_HOURS_PER_YEAR, np.nan)
            continue
        months = pd.Series(np.asarray(fr.index.tz_convert(_EASTERN_TZ).month))
        hub = fr["hub"]
        parts[kind] = round(float(hub.mean()), 2)
        parts[f"{kind}_mon"] = _by_month(hub.to_numpy(), months)
        d = _densify_std(hub, year, std_tz)
        dense[kind] = d
        parts[f"{kind}_pct"] = _pct(d)
        for z in fr.columns:
            if z == "hub":
                continue
            ser = fr[z]
            entry = zones_out.setdefault(z, {})
            entry[kind] = round(float(ser.mean()), 2)
            entry[f"{kind}_mon"] = _by_month(ser.to_numpy(), months)
    rec = {
        k: parts[k]
        for k in ("da", "rt", "da_mon", "rt_mon", "da_pct", "rt_pct")
        if k in parts
    }
    order = ("da", "rt", "da_mon", "rt_mon")
    rec["zones"] = {z: {k: e[k] for k in order if k in e} for z, e in zones_out.items()}
    rec["src"] = src
    hourly = pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": dense["rt"].astype(np.float32),
            "da": dense["da"].astype(np.float32),
        }
    )
    return rec, hourly


def _nyiso(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for NYISO, or ``None`` if no source files."""
    frames = {k: nyiso_zone_hourly(year, k) for k in ("da", "rt")}
    if frames["da"] is None and frames["rt"] is None:
        return None
    return _assemble_zonal(frames, year, NYISO_SRC, _STD_TZ["NYISO"])


def _neiso(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for NEISO, or ``None`` if no workbook."""
    frames = {k: neiso_zone_hourly(year, k) for k in ("da", "rt")}
    if frames["da"] is None and frames["rt"] is None:
        return None
    return _assemble_zonal(frames, year, NEISO_SRC, _STD_TZ["NEISO"])


# ---------------------------------------------------------------------------
# SPP — reduced from the committed hourly parquets, not from raw exports
# ---------------------------------------------------------------------------
# SPP's raw market exports are not staged in the repo (the monthly
# settlement-location files are hundreds of MB per year and the archived years
# arrive as multi-GB zips). What IS committed is the reduced hourly series the
# other builders emit as a sidecar, produced by
# ``scripts/data/build_spp_lmp_reference.py`` against portal.spp.org:
# ``actual_lmp_hourly_SPP.parquet`` (system hub = the mean of the two trading
# hubs) and ``actual_lmp_hourly_zonal_SPP.parquet`` (the two hubs separately,
# lane SPP-14). This builder therefore READS those parquets and returns no
# hourly frame, so ``main`` never rewrites them — the committed series is the
# durable record and this path only reduces it to the JSON block. MISO is the
# same case and is reduced by its own script,
# ``scripts/data/build_miso_lmp_reference.py``.
SPP_HOURLY_PARQUET = "actual_lmp_hourly_SPP.parquet"
SPP_ZONAL_PARQUET = "actual_lmp_hourly_zonal_SPP.parquet"


def _month_of_hour() -> np.ndarray:
    """Month label (1-12) for each fixed non-leap hour-of-year (0..8759).

    The dense parquet calendar is the Feb-29-dropped clock every hourly sidecar
    is indexed on, so a searchsorted over :data:`_MONTH_START_HOUR` recovers the
    month for each hour and lets a parquet-sourced builder reuse
    :func:`_by_month` unchanged.
    """
    bounds = np.asarray(_MONTH_START_HOUR[1:])  # starts of Feb..Dec
    return np.searchsorted(bounds, np.arange(_HOURS_PER_YEAR), side="right") + 1


def _coverage(values: np.ndarray, months: np.ndarray) -> dict:
    """Return ``{"annual": f, "mon": [12 f]}`` — the priced share of each window.

    The means and percentiles beside it ignore NaN, so without this a month
    covered by a single hour would read as that hour's price. SPP's committed
    series carries a handful of unpriced hours a year (6-12), so the record says
    how much of the year its NaN-ignoring statistics actually saw.
    """
    ok = ~np.isnan(values)
    return {
        "annual": round(float(ok.mean()), 4),
        "mon": [round(float(ok[months == m].mean()), 4) for m in range(1, 13)],
    }


def _dense_year(g: pd.DataFrame, kind: str) -> np.ndarray:
    """One year's ``kind`` column reindexed onto the dense 8760-hour calendar."""
    s = g.set_index("hour")[kind].reindex(range(_HOURS_PER_YEAR))
    return s.to_numpy(dtype=float)


def _spp_zone_records(zdf: pd.DataFrame, months: np.ndarray) -> dict:
    """Build the per-TRADING-HUB ``zones`` sub-dict for one SPP year.

    Keyed by SPP hub name (``SPPNORTH_HUB`` / ``SPPSOUTH_HUB``), NOT by model
    zone — see :data:`SPP_HUB_COMMENT`. Record shape mirrors the NYISO / NEISO /
    MISO ``zones`` entries: ``{da, da_mon, rt, rt_mon}``.
    """
    zones: dict[str, dict] = {}
    for hub, g in zdf.groupby("zone"):
        g = g.sort_values("hour")
        rec: dict = {}
        for kind in ("da", "rt"):
            v = _dense_year(g, kind)
            rec[kind] = round(float(np.nanmean(v)), 2)
            rec[f"{kind}_mon"] = _by_month(v, months)
        zones[str(hub)] = {k: rec[k] for k in ("da", "da_mon", "rt", "rt_mon")}
    return zones


def _spp(year: int) -> tuple[dict, None] | None:
    """Return ``(record, None)`` for SPP, or ``None`` if the year is absent.

    Reduces the committed hourly parquets to the same
    ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}`` record the other ISOs
    emit, plus ``da_cov``/``rt_cov`` (:func:`_coverage`) and the per-hub
    ``zones`` sub-dict. The second tuple element is ``None`` because the hourly
    sidecar is an INPUT here, never an output of this run.
    """
    p = HOURLY_OUT / SPP_HOURLY_PARQUET
    if not p.exists():
        return None
    g = pd.read_parquet(p)
    g = g[g["year"] == int(year)].sort_values("hour")
    if g.empty:
        return None
    months = _month_of_hour()
    rec: dict = {}
    for kind in ("da", "rt"):
        v = _dense_year(g, kind)
        rec[kind] = round(float(np.nanmean(v)), 2)
        rec[f"{kind}_mon"] = _by_month(v, months)
        rec[f"{kind}_pct"] = _pct(v)
        rec[f"{kind}_cov"] = _coverage(v, months)
    rec = {
        k: rec[k]
        for k in (
            "da",
            "rt",
            "da_mon",
            "rt_mon",
            "da_pct",
            "rt_pct",
            "da_cov",
            "rt_cov",
        )
    }
    rec["src"] = SPP_SRC
    zp = HOURLY_OUT / SPP_ZONAL_PARQUET
    if zp.exists():
        z = pd.read_parquet(zp)
        z = z[z["year"] == int(year)]
        if not z.empty:
            rec["zones"] = _spp_zone_records(z, months)
            rec["zones_src"] = SPP_ZONAL_SRC
            rec["comment"] = SPP_HUB_COMMENT
    return rec, None


BUILDERS = {
    "ERCOT": _ercot,
    "PJM": _pjm,
    "CAISO": _caiso,
    "NYISO": _nyiso,
    "NEISO": _neiso,
    "SPP": _spp,
}


def build(years, isos=None) -> tuple[dict, dict]:
    """Build the JSON reference and per-ISO hourly frames for ``years``.

    Args:
        years: Calendar years to (re)derive.
        isos: Optional subset of ISO keys to build; ``None`` builds all. Use a
            subset to refresh one ISO without depending on the others' raws
            (ERCOT/NYISO DA source zips are staged out of the repo, so building
            them on a fresh checkout would otherwise drop or degrade them — the
            committed reference is the durable record, and ``main`` merges).

    Returns:
        ``(table, hourly)`` — the ``{iso: {year: record}}`` JSON table, and
        ``{iso: DataFrame}`` of concatenated hourly hub-mean series for the
        ISOs whose builder produces one.
    """
    table: dict[str, dict] = {}
    hourly: dict[str, list] = {}
    for iso, fn in BUILDERS.items():
        if isos is not None and iso not in isos:
            continue
        for year in years:
            got = fn(int(year))
            if got is None:
                continue
            rec, hr = got
            table.setdefault(iso, {})[str(year)] = rec
            if hr is not None:
                hourly.setdefault(iso, []).append(hr)
            means = ", ".join(f"{k} ${rec[k]}" for k in ("da", "rt") if k in rec)
            print(f"  {iso} {year}: {means}")
    return table, {
        iso: pd.concat(frames, ignore_index=True) for iso, frames in hourly.items()
    }


# ---------------------------------------------------------------------------
# Load-weighted (like-for-like) price basis — rubric v2.4
# ---------------------------------------------------------------------------
# The C3a/C3b scorer's model side is the system LOAD-WEIGHTED mean LMP
# (per-zone demand-weighted zonal means, zone-demand-weighted across zones),
# but the legacy ``rt``/``da`` fields above are EQUAL-HOUR means of a hub
# series — a mixed basis whose wedge grows with tail realism (a byte-perfect
# ERCOT 2023 model scores +33.5% against its own actual; see
# docs/handoffs/ercot-ordc-capdual-adder-2026-07.md §4). The ``*_lw`` fields
# below put the ACTUAL on the same basis as the model: each ISO's committed
# hourly actual series weighted by the MEASURED hourly load the model itself
# dispatches in a backcast (``eia_loader.load_demand`` — same series, so the
# two sides of C3a finally share weights). Where a committed ZONAL hourly
# archive exists (ERCOT), the construction mirrors the scorer zone-by-zone;
# elsewhere it weights the system hub series by system load. The legacy
# equal-hour fields stay untouched (display continuity + fallback basis).

# Model zone -> ERCOT settlement load zone(s). A model zone spanning several
# LZs takes their simple mean (South_Central = Austin Energy + CPS Energy +
# LCRA, the three municipal LZs it aggregates; Northeast = the Rayburn
# country LZ; Panhandle has no LZ of its own and carries ~0 model load — it
# rides with LZ_WEST). Documented in docs/rubric-v24-price-basis-memo-2026-07.md.
ERCOT_MODEL_ZONE_TO_LZ: dict[str, tuple[str, ...]] = {
    "Houston": ("LZ_HOUSTON",),
    "North": ("LZ_NORTH",),
    "Northeast": ("LZ_RAYBN",),
    "South": ("LZ_SOUTH",),
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Panhandle": ("LZ_WEST",),
}
ERCOT_ZONAL_PARQUET = "actual_lmp_zonal_ERCOT.parquet"


def _lw_stats(prices: np.ndarray, weights: np.ndarray) -> tuple[float, list]:
    """NaN-aware ``(annual, [12 monthly])`` load-weighted means of a series."""
    p = np.asarray(prices, dtype=float)[:_HOURS_PER_YEAR]
    w = np.asarray(weights, dtype=float)[: p.size]
    v = ~np.isnan(p) & (w > 0)
    annual = float((p[v] * w[v]).sum() / w[v].sum()) if v.any() else float("nan")
    mon: list = []
    for m in range(12):
        lo = _MONTH_START_HOUR[m]
        hi = lo + _DAYS_IN_MONTH[m] * 24
        pm, wm, vm = p[lo:hi], w[lo:hi], v[lo:hi]
        mon.append(
            round(float((pm[vm] * wm[vm]).sum() / wm[vm].sum()), 2)
            if vm.any()
            else None
        )
    return round(annual, 2), mon


def _measured_zone_demand(iso: str, year: int) -> np.ndarray | None:
    """Measured hourly zonal demand ``(n_zones, T)`` — the model's own series."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    try:
        return load_demand(iso, int(year), get_iso_config(iso))
    except Exception as exc:  # measured series absent for this iso-year
        print(f"  {iso} {year}: no measured demand ({exc}); lw fields skipped")
        return None


def _lw_fields(iso: str, year: int) -> dict | None:
    """Return the ``*_lw`` record fields for one ISO-year, or ``None``.

    ERCOT: zone-resolved — the scorer's exact formula mirrored on the actual
    (per-model-zone LZ hourly series weighted by that zone's measured demand,
    then zone-demand-weighted across zones). Other ISOs: the committed system
    hub series weighted by measured system load.
    """
    from market_sim.config.iso_configs import get_iso_config

    demand = _measured_zone_demand(iso, year)
    if demand is None:
        return None
    out: dict = {}
    if iso == "ERCOT":
        zp = HOURLY_OUT / ERCOT_ZONAL_PARQUET
        if not zp.exists():
            return None
        z = pd.read_parquet(zp)
        z = z[z["year"] == int(year)]
        series: dict[str, dict[str, np.ndarray]] = {}
        for sp, g in z.groupby("settlement_point"):
            g = g.sort_values("hour")
            for kind in ("rt", "da"):
                dense = np.full(_HOURS_PER_YEAR, np.nan)
                hr = g["hour"].to_numpy(int)
                ok = hr < _HOURS_PER_YEAR
                dense[hr[ok]] = g[kind].to_numpy(float)[ok]
                series.setdefault(str(sp), {})[kind] = dense
        zone_names = [zn.name for zn in get_iso_config(iso).zones]
        for kind in ("rt", "da"):
            pairs: list[tuple[float, list, float]] = []  # (annual, mon, weight)
            for zi, zone in enumerate(zone_names):
                lzs = ERCOT_MODEL_ZONE_TO_LZ.get(zone)
                w = demand[zi]
                if not lzs or float(w.sum()) <= 0.0:
                    continue
                have = [
                    series[lz][kind]
                    for lz in lzs
                    if lz in series and not np.isnan(series[lz][kind]).all()
                ]
                if not have:
                    continue
                p = np.nanmean(np.vstack(have), axis=0)
                annual, mon = _lw_stats(p, w)
                if np.isnan(annual):
                    continue
                pairs.append((annual, mon, float(w.sum())))
            if not pairs:
                continue
            wsum = sum(w for _, _, w in pairs)
            out[f"{kind}_lw"] = round(sum(a * w for a, _, w in pairs) / wsum, 2)
            out[f"{kind}_lw_mon"] = [
                (
                    round(
                        sum(m[i] * w for _, m, w in pairs if m[i] is not None)
                        / sum(w for _, m, w in pairs if m[i] is not None),
                        2,
                    )
                    if any(m[i] is not None for _, m, w in pairs)
                    else None
                )
                for i in range(12)
            ]
        if out:
            out["src_lw"] = (
                "zonal LZ settlement prices (RTM 15-min / DAM hourly) "
                "load-weighted by measured zonal demand (eia_loader.load_demand), "
                "model-zone crosswalk ERCOT_MODEL_ZONE_TO_LZ"
            )
    else:
        hp = HOURLY_OUT / f"actual_lmp_hourly_{iso}.parquet"
        if not hp.exists():
            return None
        h = pd.read_parquet(hp)
        h = h[h["year"] == int(year)].sort_values("hour")
        if h.empty:
            return None
        w = demand.sum(axis=0)
        for kind in ("rt", "da"):
            dense = np.full(_HOURS_PER_YEAR, np.nan)
            hr = h["hour"].to_numpy(int)
            ok = hr < _HOURS_PER_YEAR
            dense[hr[ok]] = h[kind].to_numpy(float)[ok]
            if np.isnan(dense).all():
                continue
            annual, mon = _lw_stats(dense, w)
            if not np.isnan(annual):
                out[f"{kind}_lw"] = annual
                out[f"{kind}_lw_mon"] = mon
        if out:
            out["src_lw"] = (
                "system hub hourly series load-weighted by measured system "
                "demand (eia_loader.load_demand)"
            )
    return out or None


def lw_retrofit(years: list[int], isos: list[str] | None = None) -> None:
    """Amend the committed reference with the ``*_lw`` fields in place.

    Reads ``actual_lmp.json``, adds ``rt_lw``/``rt_lw_mon``/``da_lw``/
    ``da_lw_mon``/``src_lw`` to each covered ISO-year from the committed
    hourly parquets × measured load, and rewrites the JSON. Legacy fields are
    never touched; ISO-years without a committed hourly series or measured
    demand keep their record unchanged (the scorer falls back to the legacy
    equal-hour basis with an explicit label). Rubric v2.4; re-derivation
    citation: methodology change (mixed-basis C3), not a residual.
    """
    table = json.loads(OUT.read_text())
    n = 0
    for iso, yrec in sorted(table.items()):
        if isos is not None and iso not in isos:
            continue
        for y in sorted(yrec):
            if int(y) not in years:
                continue
            fields = _lw_fields(iso, int(y))
            if fields:
                yrec[y].update(fields)
                n += 1
                print(
                    f"  {iso} {y}: rt_lw {fields.get('rt_lw')} "
                    f"da_lw {fields.get('da_lw')} "
                    f"(legacy rt {yrec[y].get('rt')} da {yrec[y].get('da')})"
                )
    OUT.write_text(json.dumps(table, indent=2) + "\n")
    print(f"wrote {OUT} (+lw fields on {n} iso-years)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    ap.add_argument(
        "--isos",
        nargs="+",
        default=None,
        help="Subset of ISOs to (re)derive; default all. Only the built ISOs "
        "are updated — others keep their committed entry/parquet (their raws "
        "may be staged out of the repo).",
    )
    ap.add_argument(
        "--lw-retrofit",
        action="store_true",
        help="Do not re-parse raw archives; amend the committed "
        "actual_lmp.json with the load-weighted (*_lw) price fields from the "
        "committed hourly parquets × measured demand (rubric v2.4 C3 basis).",
    )
    ap.add_argument(
        "--parquet-only",
        action="store_true",
        help="Rebuild the hourly parquets without rewriting actual_lmp.json "
        "(the JSON's raw-row means are clock-invariant; its *_pct dense-series "
        "completeness deltas land only at an authorized JSON re-derivation).",
    )
    args = ap.parse_args()
    if args.lw_retrofit:
        lw_retrofit(args.years, isos=args.isos)
        return
    table, hourly = build(args.years, isos=args.isos)
    if not args.parquet_only:
        # Merge into the committed reference rather than overwriting: ISOs not
        # built this run (or whose source raws are staged out) keep their entry.
        merged: dict[str, dict] = {}
        if OUT.exists():
            merged = json.loads(OUT.read_text())
        for iso, years in table.items():
            merged.setdefault(iso, {}).update(years)
        OUT.write_text(json.dumps(merged, indent=2) + "\n")
        print(f"wrote {OUT} ({sum(len(v) for v in merged.values())} iso-years)")
    # Only rewrite parquets for ISOs actually built this run, and only the
    # years built: rows for other years (e.g. the quarantined out-of-training
    # 2018-2022 / 2026 blocks landed by the holdout intakes, rule 22) are
    # preserved byte-for-byte from the committed file — MERGE, never replace.
    for iso, frame in hourly.items():
        p = HOURLY_OUT / f"actual_lmp_hourly_{iso}.parquet"
        if p.exists():
            old = pd.read_parquet(p)
            keep = old[~old["year"].isin(frame["year"].unique())]
            if not keep.empty:
                print(
                    f"  {iso}: preserving committed rows for years "
                    f"{sorted(keep['year'].unique().tolist())}"
                )
                frame = pd.concat([keep, frame], ignore_index=True).sort_values(
                    ["year", "hour"], ignore_index=True
                )
        frame.to_parquet(p, index=False)
        print(f"wrote {p} ({len(frame)} hours, {frame['year'].nunique()} years)")


if __name__ == "__main__":
    main()
