"""Curate the ``load`` clean datatype from the per-ISO raw demand feeds.

Reconciles three raw demand layouts into the canonical ``load`` schema
(``data/dictionary/schema/load.schema.yaml``) and writes one Parquet per
``(iso, year)`` through the frozen ``scripts/lib/clean_io.write_clean`` seam:

  CAISO    data/raw/zone-specific-demand/CAISO/CAISO_tac_load_hourly_*.csv
           (per-TAC-area actual load) + the SLD_FCST_ACTUAL_*.csv day-ahead
           forecast (MARKET_RUN_ID == "DAM").
  NYISO    data/raw/zone-specific-demand/NYISO/NYISO_load_actuals_*.csv
           (per-zone actual load; "Time Stamp" is local wall-clock).
  EIA-930  data/raw/eia-930-hourly/<BA> hourly.parquet, for the ISOs that have
           no native feed wired up here (ERCOT, NEISO, MISO, PJM). CAISO and
           NYISO are skipped (native feeds above); FLA/SOCO are not ISOs.

Reconciliation onto the canonical columns:

  tac_area / NYISO ``Name`` / EIA BA  -> ``zone``
  actual load (CAISO mw, NYISO Load, EIA Demand)         -> ``load_mw``
  forecast (CAISO DAM, EIA "Demand forecast")            -> ``load_forecast_mw``
  load minus wind + solar, only where both are co-available (EIA-930) ->
  ``net_load_mw`` (left null otherwise — CAISO/NYISO feeds carry no renewables).

NYISO "Time Stamp" is local Eastern wall-clock: it is converted to tz-aware UTC
``interval_start_utc`` with the naive wall-clock carried alongside in
``interval_start_local``. CAISO/EIA timestamps are already UTC.

The script is idempotent and reads only ``data/raw``: every source is
re-partitioned by the UTC year of each hour and the clean Parquet is overwritten
on each run. Nothing is written outside ``clean_io.write_clean``.
"""

from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

from market_sim.config import paths
from scripts.lib.clean_io import validate_clean, write_clean

# --- raw input locations (module-level so tests can redirect them) ----------
CAISO_DIR: Path = paths.ZONE_DEMAND_DIR / "CAISO"
NYISO_DIR: Path = paths.ZONE_DEMAND_DIR / "NYISO"
EIA_DIR: Path = paths.EIA_HOURLY_DIR

# EIA-930 balancing authority -> ISO, restricted to ISOs without a native feed
# curated above. CISO/NYIS are dropped (CAISO/NYISO have native sources here);
# FLA/SOCO are dropped (Florida / Southern Co are not ISOs/RTOs).
EIA_BA_TO_ISO: dict[str, str] = {
    "ERCO": "ERCOT",
    "ISNE": "NEISO",
    "MISO": "MISO",
    "PJM": "PJM",
}

# NYISO reports in Eastern prevailing (wall-clock) time.
NYISO_TZ = "America/New_York"

# Canonical column order (a subset of the load schema; nullable columns are
# emitted only when a source actually populates them).
_CANONICAL = [
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "zone",
    "load_mw",
    "load_forecast_mw",
    "net_load_mw",
]


def _rel(path: str | Path) -> str:
    """Path relative to the repo root for compact provenance strings."""
    try:
        return str(Path(path).resolve().relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# CAISO
# ---------------------------------------------------------------------------
def _caiso_forecast(zones: set[str]) -> pd.DataFrame:
    """Day-ahead forecast (MARKET_RUN_ID == "DAM") from the SLD_FCST_ACTUAL CSVs.

    Returns a frame keyed (zone, interval_start_utc) with ``load_forecast_mw``,
    restricted to ``zones`` (the TAC areas that have an actual). The shipped
    download carries only ACTUAL rows, so this is typically empty; the logic is
    here so a download that includes DAM rows populates the forecast column.
    """
    frames: list[pd.DataFrame] = []
    for f in sorted(glob.glob(str(CAISO_DIR / "*SLD_FCST_ACTUAL*.csv"))):
        d = pd.read_csv(
            f,
            usecols=["INTERVALSTARTTIME_GMT", "MARKET_RUN_ID", "TAC_AREA_NAME", "MW"],
        )
        d = d[(d["MARKET_RUN_ID"] == "DAM") & (d["TAC_AREA_NAME"].isin(zones))]
        if d.empty:
            continue
        frames.append(
            pd.DataFrame(
                {
                    "interval_start_utc": pd.to_datetime(
                        d["INTERVALSTARTTIME_GMT"], utc=True
                    ),
                    "zone": d["TAC_AREA_NAME"].astype("string"),
                    "load_forecast_mw": d["MW"].astype("float64"),
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=["interval_start_utc", "zone", "load_forecast_mw"])
    out = pd.concat(frames, ignore_index=True)
    # Collapse any duplicate (zone, hour) DAM rows to a single forecast value.
    return out.groupby(["zone", "interval_start_utc"], as_index=False)[
        "load_forecast_mw"
    ].mean()


def build_caiso() -> tuple[pd.DataFrame, str]:
    """Build the CAISO load frame: per-TAC-area actuals + DAM forecast."""
    tac_files = sorted(glob.glob(str(CAISO_DIR / "CAISO_tac_load_hourly_*.csv")))
    frames: list[pd.DataFrame] = []
    for f in tac_files:
        d = pd.read_csv(f)
        frames.append(
            pd.DataFrame(
                {
                    "interval_start_utc": pd.to_datetime(
                        d["interval_start_gmt"], utc=True
                    ),
                    "zone": d["tac_area"].astype("string"),
                    "load_mw": d["mw"].astype("float64"),
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=_CANONICAL), ""
    df = pd.concat(frames, ignore_index=True)
    df["iso"] = "CAISO"

    fc = _caiso_forecast(set(df["zone"].dropna().unique()))
    df = df.merge(fc, on=["zone", "interval_start_utc"], how="left")
    if "load_forecast_mw" not in df.columns:
        df["load_forecast_mw"] = pd.NA
    df["net_load_mw"] = pd.NA  # no co-available wind/solar in the CAISO feeds

    sources = tac_files + sorted(glob.glob(str(CAISO_DIR / "*SLD_FCST_ACTUAL*.csv")))
    return df, ", ".join(_rel(p) for p in sources)


# ---------------------------------------------------------------------------
# NYISO
# ---------------------------------------------------------------------------
def build_nyiso() -> tuple[pd.DataFrame, str]:
    """Build the NYISO load frame, converting local wall-clock to tz-aware UTC."""
    files = sorted(glob.glob(str(NYISO_DIR / "NYISO_load_actuals_*.csv")))
    frames: list[pd.DataFrame] = []
    for f in files:
        d = pd.read_csv(f)
        local = pd.to_datetime(d["Time Stamp"])  # naive Eastern wall-clock
        frames.append(
            pd.DataFrame(
                {
                    "interval_start_local": local,
                    "zone": d["Name"].astype("string"),
                    "load_mw": d["Load"].astype("float64"),
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=_CANONICAL), ""
    df = pd.concat(frames, ignore_index=True)
    # Localize the Eastern wall-clock to UTC. The fall-back hour appears once
    # (treated as DST/EDT); the spring-forward hour is simply absent from the
    # feed (nothing to shift), but shift_forward keeps the call total.
    utc = df["interval_start_local"].dt.tz_localize(
        NYISO_TZ, ambiguous=True, nonexistent="shift_forward"
    )
    df["interval_start_utc"] = utc.dt.tz_convert("UTC")
    df["iso"] = "NYISO"
    df["load_forecast_mw"] = pd.NA  # NYISO actuals carry no forecast
    df["net_load_mw"] = pd.NA
    return df, ", ".join(_rel(p) for p in files)


# ---------------------------------------------------------------------------
# EIA-930
# ---------------------------------------------------------------------------
def build_eia() -> list[tuple[str, pd.DataFrame, str]]:
    """Build one (iso, frame, source) per EIA-930 BA mapped to an ISO."""
    import pyarrow.parquet as pq

    out: list[tuple[str, pd.DataFrame, str]] = []
    for ba, iso in EIA_BA_TO_ISO.items():
        f = EIA_DIR / f"{ba} hourly.parquet"
        if not f.is_file():
            continue
        names = set(pq.ParquetFile(f).schema_arrow.names)
        cols = ["UTC time", "Demand", "Demand forecast"]
        has_wind = "NG: WND" in names
        has_solar = "NG: SUN" in names
        if has_wind:
            cols.append("NG: WND")
        if has_solar:
            cols.append("NG: SUN")
        d = pd.read_parquet(f, columns=cols)
        d = d.dropna(subset=["Demand"])
        if d.empty:
            continue

        utc = pd.to_datetime(d["UTC time"]).dt.tz_localize("UTC")
        frame = pd.DataFrame(
            {
                "interval_start_utc": utc,
                "iso": iso,
                "zone": ba,
                "load_mw": d["Demand"].astype("float64"),
                "load_forecast_mw": d["Demand forecast"].astype("float64"),
            }
        )
        # Net load only where wind AND solar are co-available for the hour.
        if has_wind and has_solar:
            wind = d["NG: WND"].astype("float64")
            solar = d["NG: SUN"].astype("float64")
            net = frame["load_mw"] - wind.to_numpy() - solar.to_numpy()
            both = wind.notna().to_numpy() & solar.notna().to_numpy()
            frame["net_load_mw"] = net.where(both)
        else:
            frame["net_load_mw"] = pd.NA
        out.append((iso, frame, _rel(f)))
    return out


# ---------------------------------------------------------------------------
# Emit (validate + write per iso/year through the frozen seam)
# ---------------------------------------------------------------------------
def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    """Select canonical columns present and coerce them to schema dtypes."""
    cols = [c for c in _CANONICAL if c in df.columns]
    out = df[cols].copy()
    if "interval_start_local" in out:
        out["interval_start_local"] = pd.to_datetime(out["interval_start_local"])
    for c in ("iso", "zone"):
        if c in out:
            out[c] = out[c].astype("string")
    for c in ("load_mw", "load_forecast_mw", "net_load_mw"):
        if c in out:
            out[c] = pd.to_numeric(out[c], errors="coerce").astype("float64")
    return out


def emit(df: pd.DataFrame, iso: str, source: str) -> list[Path]:
    """Validate + write one clean Parquet per UTC year for a single ISO."""
    written: list[Path] = []
    df = df.dropna(subset=["interval_start_utc", "load_mw"])
    if df.empty:
        return written
    for year, group in df.groupby(df["interval_start_utc"].dt.year):
        clean = _coerce(group)
        path = write_clean(clean, "load", iso=iso, year=int(year), source=source)
        validate_clean(path)
        written.append(path)
        print(f"  wrote {iso} {int(year)}: {len(clean):>7,} rows -> {path}")
    return written


def curate_all() -> list[Path]:
    """Curate every source and return the list of clean Parquet paths written."""
    written: list[Path] = []

    caiso, caiso_src = build_caiso()
    if not caiso.empty:
        print("CAISO:")
        written += emit(caiso, "CAISO", caiso_src)

    nyiso, nyiso_src = build_nyiso()
    if not nyiso.empty:
        print("NYISO:")
        written += emit(nyiso, "NYISO", nyiso_src)

    eia = build_eia()
    if eia:
        print("EIA-930:")
        for iso, frame, src in eia:
            written += emit(frame, iso, src)

    return written


def main() -> None:
    paths_written = curate_all()
    print(f"\nload curation complete: {len(paths_written)} clean file(s) written.")


if __name__ == "__main__":
    main()
