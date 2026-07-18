"""Curate the ``lmp`` clean datatype from the raw per-ISO LMP downloads.

Reconciles the divergent per-ISO source layouts under ``data/raw/lmp-data`` into
the single canonical contract declared by
``data/dictionary/schema/lmp.schema.yaml`` and writes one Parquet partition per
``iso`` / ``market`` / ``year`` through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Sources curated
---------------
* **CAISO** — ``CAISO/CAISO_{dam,rtm}_hourly_<year>.csv`` (already hourly,
  timestamps in UTC). ``LMP -> lmp_usd_per_mwh``; the component decomposition
  ``MCE/MCC/MCL/MGHG -> energy/congestion/loss/ghg``. ``dam``/``rtm`` filename
  -> ``market`` key (DAM/RTM).
* **PJM** — ``PJM_<year>_rt_da_monthly_lmps.csv`` (hourly nodal export; the
  "monthly" in the filename refers to the download batching, not the cadence).
  Each row carries both the day-ahead and real-time price + components, so one
  raw row fans out to a DAM and an RTM row. ``total_lmp_{da,rt} -> lmp``,
  ``system_energy_price -> energy``, ``congestion_price -> congestion``,
  ``marginal_loss_price -> loss``. ``datetime_beginning_utc`` is authoritative;
  ``datetime_beginning_ept`` is the local wall clock.
* **NYISO** — ``NYISO/*realtime_zone*.zip`` (real-time, 5-minute, by zone).
  ``LBMP -> lmp``, ``Marginal Cost Congestion -> congestion``,
  ``Marginal Cost Losses -> loss``. The 5-minute interval-*ending* stamps are
  collapsed to the hourly mean (hour-beginning) so the series matches the
  hourly contract. Real-time only -> ``market`` RTM.
* **NEISO** — ``NEISO/*_smd_hourly.xlsx`` (ISO-NE SMD workbooks; one sheet per
  zone/hub). Day-ahead and real-time columns fan out to DAM/RTM rows:
  ``{DA,RT}_LMP -> lmp``, ``_EC -> energy``, ``_CC -> congestion``,
  ``_MLC -> loss``. ``Hr_End`` (1..24, hour-ending) -> hour-beginning local.

Sources deliberately NOT curated here (see PR notes)
----------------------------------------------------
* **ERCOT** — ``data/raw/lmp-data/ERCOT`` holds only ``.gitkeep`` and the
  ERCOT settlement-point ZIPs that ``derive_ercot_zonal_lmp.py`` expects are
  absent from this checkout, so there is no ERCOT *raw* LMP to curate. The
  existing ``derive_*`` scripts produce a tiny *derived* validation reference
  (``data/raw/_validation-source/actual_lmp*``), not a node-level raw series;
  feeding that derived product into this datatype would mix raw and derived
  provenance, so it stays separate. ERCOT lands here once raw SPP archives do.
* The top-level ``dartmonthlylmpindex_*.csv`` (and the NYISO copies) are
  *monthly index reports*, not hourly nodal LMP, so they are out of scope.

Timezone & partitioning conventions
-----------------------------------
Every source's local stamp is reconciled to a tz-aware UTC
``interval_start_utc`` (authoritative) with the tz-naive wall clock carried in
``interval_start_local``. Partitions are keyed on the **local** calendar year
(``interval_start_local.dt.year``) so each ISO's rows land in the year its
yearly source file is named for.

The script reads only ``data/raw`` and is idempotent: re-running overwrites the
same partition files. Run with ``python -m scripts.data.curate_lmp`` (or
``uv run python scripts/data/curate_lmp.py``).
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from market_sim.config import paths
from scripts.lib.clean_io import validate_clean, write_clean

# Canonical lmp schema columns, in declaration order.
SCHEMA_COLS: tuple[str, ...] = (
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "market",
    "node",
    "zone",
    "lmp_usd_per_mwh",
    "energy_usd_per_mwh",
    "congestion_usd_per_mwh",
    "loss_usd_per_mwh",
    "ghg_usd_per_mwh",
)
_STRING_COLS = ("iso", "market", "node", "zone")
_FLOAT_COLS = (
    "lmp_usd_per_mwh",
    "energy_usd_per_mwh",
    "congestion_usd_per_mwh",
    "loss_usd_per_mwh",
    "ghg_usd_per_mwh",
)

_PACIFIC = ZoneInfo("America/Los_Angeles")
_EASTERN = ZoneInfo("America/New_York")

# Default raw root (the script reads ONLY from here).
DEFAULT_RAW_DIR: Path = paths.RAW_DIR / "lmp-data"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _rel_source(path: Path) -> str:
    """Repo-relative path string for provenance, falling back to the raw str."""
    try:
        return str(Path(path).resolve().relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _localize(naive: pd.Series, tz: ZoneInfo, ambiguous=True) -> pd.Series:
    """Localize tz-naive wall-clock stamps to ``tz`` then convert to UTC.

    DST transition hours are resolved deterministically: ``ambiguous`` (a scalar
    or a per-row bool array — ``True`` = DST/first occurrence) selects the
    fall-back hour, and ``nonexistent="shift_forward"`` shifts the skipped
    spring-forward hour forward.
    """
    s = pd.to_datetime(naive)
    return s.dt.tz_localize(
        tz, ambiguous=ambiguous, nonexistent="shift_forward"
    ).dt.tz_convert("UTC")


def _frame(source: Path, n: int, **cols) -> pd.DataFrame:
    """Build a partial lmp frame with every schema column present.

    Unsupplied string columns default to ``pd.NA``; unsupplied numeric
    components default to ``NaN``. ``_source_file`` carries provenance.
    """
    data: dict[str, object] = {}
    for c in SCHEMA_COLS:
        if c in cols:
            data[c] = cols[c]
        elif c in _STRING_COLS:
            data[c] = pd.array([pd.NA] * n, dtype="string")
        else:
            data[c] = np.full(n, np.nan)
    df = pd.DataFrame(data)
    df["_source_file"] = _rel_source(source)
    return df


# ---------------------------------------------------------------------------
# per-source parsers
# ---------------------------------------------------------------------------
def parse_caiso_file(path: Path) -> pd.DataFrame:
    """Parse one CAISO ``{dam,rtm}_hourly`` CSV into lmp rows."""
    raw = pd.read_csv(path, dtype=str)
    utc = pd.to_datetime(raw["interval_start_gmt"], utc=True, errors="coerce")
    keep = utc.notna()  # drops blank lines and any embedded repeated header row
    raw, utc = raw.loc[keep], utc.loc[keep]
    local = utc.dt.tz_convert(_PACIFIC).dt.tz_localize(None)
    market = "DAM" if "dam" in path.name.lower() else "RTM"

    def num(col: str) -> np.ndarray:
        return pd.to_numeric(raw[col], errors="coerce").to_numpy()

    return _frame(
        path,
        len(raw),
        interval_start_utc=utc.to_numpy(),
        interval_start_local=local.to_numpy(),
        iso="CAISO",
        market=market,
        node=raw["node"].to_numpy(),
        lmp_usd_per_mwh=num("LMP"),
        energy_usd_per_mwh=num("MCE"),
        congestion_usd_per_mwh=num("MCC"),
        loss_usd_per_mwh=num("MCL"),
        ghg_usd_per_mwh=num("MGHG"),
    )


def parse_pjm_file(path: Path) -> pd.DataFrame:
    """Parse one PJM ``rt_da`` hourly nodal CSV into DAM + RTM lmp rows."""
    raw = pd.read_csv(path)
    fmt = "%m/%d/%Y %I:%M:%S %p"
    utc = pd.to_datetime(raw["datetime_beginning_utc"], format=fmt, utc=True)
    local = pd.to_datetime(raw["datetime_beginning_ept"], format=fmt)
    node = raw["pnode_name"]
    zone = raw["zone"]

    frames = []
    for market, sfx in (("DAM", "da"), ("RTM", "rt")):
        frames.append(
            _frame(
                path,
                len(raw),
                interval_start_utc=utc.to_numpy(),
                interval_start_local=local.to_numpy(),
                iso="PJM",
                market=market,
                node=node.to_numpy(),
                zone=zone.to_numpy(),
                lmp_usd_per_mwh=raw[f"total_lmp_{sfx}"].to_numpy(),
                energy_usd_per_mwh=raw[f"system_energy_price_{sfx}"].to_numpy(),
                congestion_usd_per_mwh=raw[f"congestion_price_{sfx}"].to_numpy(),
                loss_usd_per_mwh=raw[f"marginal_loss_price_{sfx}"].to_numpy(),
            )
        )
    return pd.concat(frames, ignore_index=True)


def parse_nyiso_zip(path: Path) -> pd.DataFrame:
    """Parse one NYISO real-time-zone ZIP (5-min, by zone) to hourly RTM rows."""
    parts = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            d = pd.read_csv(io.BytesIO(zf.read(name)))
            ts_end = pd.to_datetime(d["Time Stamp"], format="%m/%d/%Y %H:%M:%S")
            # 5-min stamps are interval-ENDING; map each to its hour-beginning.
            hour_begin = (ts_end - pd.Timedelta(seconds=1)).dt.floor("h")
            parts.append(
                pd.DataFrame(
                    {
                        "node": d["Name"],
                        "hour_begin": hour_begin,
                        "lmp_usd_per_mwh": d["LBMP ($/MWHr)"],
                        "loss_usd_per_mwh": d["Marginal Cost Losses ($/MWHr)"],
                        "congestion_usd_per_mwh": d[
                            "Marginal Cost Congestion ($/MWHr)"
                        ],
                    }
                )
            )
    if not parts:
        return _frame(path, 0)
    allrows = pd.concat(parts, ignore_index=True)
    value_cols = ["lmp_usd_per_mwh", "loss_usd_per_mwh", "congestion_usd_per_mwh"]
    hourly = allrows.groupby(["node", "hour_begin"], as_index=False)[value_cols].mean()
    utc = _localize(hourly["hour_begin"], _EASTERN)
    return _frame(
        path,
        len(hourly),
        interval_start_utc=utc.to_numpy(),
        interval_start_local=hourly["hour_begin"].to_numpy(),
        iso="NYISO",
        market="RTM",
        node=hourly["node"].to_numpy(),
        zone=hourly["node"].to_numpy(),
        lmp_usd_per_mwh=hourly["lmp_usd_per_mwh"].to_numpy(),
        congestion_usd_per_mwh=hourly["congestion_usd_per_mwh"].to_numpy(),
        loss_usd_per_mwh=hourly["loss_usd_per_mwh"].to_numpy(),
    )


def parse_neiso_file(path: Path) -> pd.DataFrame:
    """Parse one ISO-NE SMD hourly workbook (one sheet per zone/hub)."""
    xl = pd.ExcelFile(path)
    needed = {"Date", "Hr_End", "DA_LMP", "RT_LMP"}
    frames = []
    for sheet in xl.sheet_names:
        if sheet == "Notes":
            continue
        d = pd.read_excel(xl, sheet_name=sheet)
        if not needed.issubset(d.columns):
            continue
        # Hr_End is hour-ending 1..24; the fall-back DST repeated hour is tagged
        # with a trailing "X" (e.g. "02X"). Strip it for the numeric hour and use
        # it to disambiguate: tagged rows are the second (standard-time) hour.
        hr_str = d["Hr_End"].astype(str).str.strip()
        is_dup = hr_str.str.upper().str.endswith("X")
        hr = pd.to_numeric(hr_str.str.replace(r"\D", "", regex=True), errors="coerce")
        local = pd.to_datetime(d["Date"]) + pd.to_timedelta(hr - 1, unit="h")
        utc = _localize(local, _EASTERN, ambiguous=(~is_dup).to_numpy())
        for market, prefix in (("DAM", "DA"), ("RTM", "RT")):
            frames.append(
                _frame(
                    path,
                    len(d),
                    interval_start_utc=utc.to_numpy(),
                    interval_start_local=local.to_numpy(),
                    iso="NEISO",
                    market=market,
                    node=sheet,
                    zone=sheet,
                    lmp_usd_per_mwh=pd.to_numeric(
                        d[f"{prefix}_LMP"], errors="coerce"
                    ).to_numpy(),
                    energy_usd_per_mwh=pd.to_numeric(
                        d[f"{prefix}_EC"], errors="coerce"
                    ).to_numpy(),
                    congestion_usd_per_mwh=pd.to_numeric(
                        d[f"{prefix}_CC"], errors="coerce"
                    ).to_numpy(),
                    loss_usd_per_mwh=pd.to_numeric(
                        d[f"{prefix}_MLC"], errors="coerce"
                    ).to_numpy(),
                )
            )
    if not frames:
        return _frame(path, 0)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# assembly + write
# ---------------------------------------------------------------------------
def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dtypes, drop unusable rows, and add the ``_year`` partition key.

    Casts string/float/timestamp columns to the schema dtypes, drops rows
    missing the non-nullable key/total (``interval_start_utc`` or
    ``lmp_usd_per_mwh``), and derives ``_year`` from the local wall clock.
    """
    df = df.copy()
    df["interval_start_utc"] = pd.to_datetime(
        df["interval_start_utc"], utc=True
    ).astype("datetime64[ns, UTC]")
    df["interval_start_local"] = pd.to_datetime(df["interval_start_local"]).astype(
        "datetime64[ns]"
    )
    for c in _STRING_COLS:
        df[c] = df[c].astype("string")
    for c in _FLOAT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df[df["interval_start_utc"].notna() & df["lmp_usd_per_mwh"].notna()].copy()
    df["_year"] = df["interval_start_local"].dt.year.astype(int)
    return df


def curate(raw_dir: Path = DEFAULT_RAW_DIR) -> pd.DataFrame:
    """Read every supported raw LMP source under ``raw_dir`` into one frame."""
    raw_dir = Path(raw_dir)
    frames: list[pd.DataFrame] = []
    for f in sorted((raw_dir / "CAISO").glob("*.csv")):
        frames.append(parse_caiso_file(f))
    for f in sorted(raw_dir.glob("PJM_*_rt_da_monthly_lmps.csv")):
        frames.append(parse_pjm_file(f))
    for f in sorted((raw_dir / "NYISO").glob("*realtime_zone*.zip")):
        frames.append(parse_nyiso_zip(f))
    for f in sorted((raw_dir / "NEISO").glob("*_smd_hourly.xlsx")):
        frames.append(parse_neiso_file(f))
    if not frames:
        raise FileNotFoundError(f"no raw LMP sources found under {raw_dir}")
    return finalize(pd.concat(frames, ignore_index=True))


def write_all(df: pd.DataFrame) -> list[Path]:
    """Write one validated Parquet partition per (iso, market, year)."""
    written: list[Path] = []
    for (iso, market, year), grp in df.groupby(["iso", "market", "_year"], sort=True):
        source = ", ".join(sorted(set(grp["_source_file"])))
        out_df = grp.drop(columns=["_source_file", "_year"]).reset_index(drop=True)
        out_df = out_df[list(SCHEMA_COLS)]
        path = write_clean(
            out_df,
            "lmp",
            iso=str(iso),
            market=str(market),
            year=int(year),
            source=source,
        )
        validate_clean(path)
        written.append(path)
    return written


def main(raw_dir: Path = DEFAULT_RAW_DIR) -> list[Path]:
    df = curate(raw_dir)
    written = write_all(df)
    for path in written:
        print(f"wrote {path}")
    print(f"{len(written)} lmp partition(s) written from {raw_dir}")
    return written


if __name__ == "__main__":
    main()
