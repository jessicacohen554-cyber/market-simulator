"""Build the hourly ACTUAL storage dispatch + SOC reference for ERCOT and CAISO.

Report-only comparison data for the Run Explorer's storage panel
(``scripts/lib/storage_compare.py``). Nothing here reaches a solve, a scorer
or a gate: storage-dispatch accuracy is NOT a calibration criterion (C5b/C5c
were removed at rubric v2.7) and this module re-arms nothing. It exists so the
keeper's committed ``hourly/storage_<year>.parquet`` sidecar (model charge /
discharge / SOC per tech-hour) can be looked at against what the fleet really
did.

Sources (all public, all measured outcomes — used ONLY as the comparison
side, never fed to the model, so rule 13 ``[R-MEASURED]`` is not engaged):

* **CAISO dispatch** — Today's Outlook history, ``/outlook/history/<YYYYMMDD>/
  storage.csv``: 5-min "Total batteries" MW (positive = discharging; the
  2022 files carry one "Batteries" column, same quantity). This is the
  battery component of standalone AND hybrid resources, i.e. the same fleet
  the model's ``li_ion`` tech represents. Pumped storage is not in it (CAISO
  folds it into Large Hydro), so the comparison is ``li_ion`` only.
* **CAISO SOC** — Daily Energy Storage Report data files
  (``/documents/storage-report-{2023q1..2024q4}.xlsx`` and
  ``storage-report-q{1..4}-2025.xlsx``), sheet ``market_output``,
  ``MARKET == 'RTD'``, ``RES_TYPE == 'LESR'``, ``TYPE == 'SOC'``: 5-min
  real-time SOC (MWh) of **stand-alone** (LESR) batteries only. Hybrid
  resources publish no SOC, so this covers a subset of the fleet — the panel
  compares SOC SHAPE (% of each series' own annual max), never level.
* **ERCOT dispatch** — EIA-930 ``ERCO hourly``: ``NG: BAT`` + ``NG: UES``.
  ERCOT files battery output under BAT and the fleet's charging under UES
  (always <= 0); BAT also dips negative in some hours, so the NET injection
  is their SUM, and discharge / charge are the positive / negative parts of
  that net per hour. Reported from ~Oct-2024; earlier hours are NaN, never 0.
  ERCOT publishes no historical fleet SOC in a downloadable form, so ERCOT
  carries no SOC actual.

Clock: every series lands on the model's chronological, fixed-standard-time,
hour-beginning, non-leap 8760 (CAISO ``Etc/GMT+8``, ERCOT ``Etc/GMT+6``),
the same construction as ``data/neighbor_price._std_hour_of_year``. CAISO
stamps are Pacific PREVAILING time: the spring-forward hour is blank at the
source and the fall-back repeated hour is published once, so both become gap
hours and are interpolated. EIA-930 ``UTC time`` is hour-ENDING, so the
interval start is ``UTC time - 1 h`` (data/raw/eia-930-hourly/README.md).

Output: ``data/raw/storage-dispatch-actuals/<ISO>_storage_hourly.parquet``,
columns ``year, hour, net_mw, discharge_mw, charge_mw, soc_mwh, source``.
Hourly discharge/charge are the means of the 5-min positive/negative parts
(CAISO) — so a within-hour reversal keeps both legs instead of netting them.
Source downloads are cached under ``_source/`` (gitignored); their hashes are
written to ``SHA256SUMS.txt``.

Usage::

    python scripts/data/build_storage_dispatch_actuals.py --iso CAISO ERCOT \
        --years 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import io
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

OUT_DIR = RAW_DATA_DIR / "storage-dispatch-actuals"
SRC_DIR = OUT_DIR / "_source"

# Model clock per ISO: fixed standard time, POSIX sign (Etc/GMT+8 == UTC-8).
# Same zones as data/neighbor_price._HUB_SPECS (CAISO PST, ERCOT CST).
MODEL_TZ = {"CAISO": "Etc/GMT+8", "ERCOT": "Etc/GMT+6"}
# Prevailing zone the CAISO sources are stamped in.
CAISO_LOCAL_TZ = "America/Los_Angeles"

OUTLOOK_URL = "https://www.caiso.com/outlook/history/{d}/storage.csv"
DESR_URLS = {
    2023: [
        f"https://www.caiso.com/documents/storage-report-2023q{q}.xlsx"
        for q in range(1, 5)
    ],
    2024: [
        f"https://www.caiso.com/documents/storage-report-2024q{q}.xlsx"
        for q in range(1, 5)
    ],
    2025: [
        f"https://www.caiso.com/documents/storage-report-q{q}-2025.xlsx"
        for q in range(1, 5)
    ],
}
ERCO_930 = RAW_DATA_DIR / "eia-930-hourly" / "ERCO hourly.parquet"

HOURS = 8760
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum((0,) + tuple(d * 24 for d in _DAYS_IN_MONTH))


def std_hour_of_year(
    utc: pd.Series | pd.DatetimeIndex, year: int, std_tz: str
) -> np.ndarray:
    """Map tz-aware instants to the model's fixed-standard-time 8760 slot.

    Slot ``k`` is the k-th hour after local-standard midnight Jan 1; stamps
    outside ``year`` and on the standard-clock Feb 29 map to -1.
    """
    std = pd.DatetimeIndex(pd.to_datetime(utc, utc=True)).tz_convert(std_tz)
    month = np.asarray(std.month)
    day = np.asarray(std.day)
    idx = _MONTH_START_HOUR[month - 1] + (day - 1) * 24 + np.asarray(std.hour)
    ok = (np.asarray(std.year) == year) & ~((month == 2) & (day == 29))
    return np.where(ok, idx, -1)


def _fetch(url: str, dest: Path, retries: int = 4) -> Path:
    """Download ``url`` to ``dest`` once (cached), with exponential backoff."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = r.read()
            dest.write_bytes(data)
            return dest
        except Exception:  # noqa: BLE001 — network flake; retry then raise
            if attempt == retries - 1:
                raise
            time.sleep(2 ** (attempt + 1))
    return dest


def _to_hourly(slot: np.ndarray, values: np.ndarray, how: str) -> np.ndarray:
    """Average 5-min samples into their 8760 slot; ``how`` picks the leg."""
    keep = (slot >= 0) & np.isfinite(values)
    v = values[keep]
    if how == "discharge":
        v = np.clip(v, 0.0, None)
    elif how == "charge":
        v = np.clip(-v, 0.0, None)
    s = np.bincount(slot[keep], weights=v, minlength=HOURS)
    n = np.bincount(slot[keep], minlength=HOURS)
    out = np.full(HOURS, np.nan)
    out[n > 0] = s[n > 0] / n[n > 0]
    return out


def _fill_gaps(a: np.ndarray, max_gap: int = 3) -> np.ndarray:
    """Interpolate isolated gap hours (DST, a missing file) up to ``max_gap``."""
    return pd.Series(a).interpolate(limit=max_gap, limit_area="inside").to_numpy()


def caiso_outlook_year(year: int) -> pd.DataFrame:
    """Return CAISO 5-min Total batteries MW for ``year`` with UTC instants."""
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    # Pull one day either side so the fixed-standard clock's year edge (PST
    # is 1 h behind PDT, never ahead of PST itself) is complete.
    days = days.union(pd.DatetimeIndex([days[-1] + pd.Timedelta(days=1)]))

    def one(d: pd.Timestamp) -> pd.DataFrame | None:
        key = d.strftime("%Y%m%d")
        p = _fetch(
            OUTLOOK_URL.format(d=key), SRC_DIR / "caiso-outlook" / f"{key}_storage.csv"
        )
        df = pd.read_csv(p)
        col = "Total batteries" if "Total batteries" in df.columns else "Batteries"
        if col not in df.columns:
            return None
        t = pd.to_datetime(key + " " + df["Time"].astype(str), format="%Y%m%d %H:%M")
        return pd.DataFrame({"local": t, "mw": pd.to_numeric(df[col], errors="coerce")})

    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        parts = [p for p in ex.map(one, days) if p is not None]
    df = pd.concat(parts, ignore_index=True).dropna(subset=["mw"])
    loc = df["local"].dt.tz_localize(CAISO_LOCAL_TZ, ambiguous="NaT", nonexistent="NaT")
    df = df.assign(utc=loc.dt.tz_convert("UTC")).dropna(subset=["utc"])
    return df


def caiso_desr_soc_year(year: int) -> np.ndarray | None:
    """Return the CAISO stand-alone (LESR) RTD SOC, hourly mean MWh, or None."""
    urls = DESR_URLS.get(year)
    if not urls:
        return None
    frames = []
    for url in urls:
        p = _fetch(url, SRC_DIR / "caiso-desr" / url.rsplit("/", 1)[1])
        d = pd.read_excel(io.BytesIO(p.read_bytes()), sheet_name="market_output")
        d = d[(d["MARKET"] == "RTD") & (d["RES_TYPE"] == "LESR") & (d["TYPE"] == "SOC")]
        frames.append(d[["TRADE_DATE", "HOUR", "INTERVAL", "VALUE"]])
    d = pd.concat(frames, ignore_index=True)
    # HOUR is hour-ending 1..24 prevailing; INTERVAL is the 5-min index 1..12.
    local = (
        pd.to_datetime(d["TRADE_DATE"])
        + pd.to_timedelta(d["HOUR"].astype(int) - 1, unit="h")
        + pd.to_timedelta((d["INTERVAL"].astype(int) - 1) * 5, unit="min")
    )
    loc = local.dt.tz_localize(CAISO_LOCAL_TZ, ambiguous="NaT", nonexistent="NaT")
    ok = loc.notna().to_numpy()
    slot = std_hour_of_year(loc[ok].dt.tz_convert("UTC"), year, MODEL_TZ["CAISO"])
    soc = _to_hourly(
        slot, pd.to_numeric(d["VALUE"], errors="coerce").to_numpy()[ok], "net"
    )
    return _fill_gaps(soc)


def build_caiso(year: int) -> pd.DataFrame:
    """Assemble one CAISO year on the model clock."""
    df = caiso_outlook_year(year)
    slot = std_hour_of_year(df["utc"], year, MODEL_TZ["CAISO"])
    mw = df["mw"].to_numpy(dtype=float)
    net = _fill_gaps(_to_hourly(slot, mw, "net"))
    dis = _fill_gaps(_to_hourly(slot, mw, "discharge"))
    chg = _fill_gaps(_to_hourly(slot, mw, "charge"))
    soc = caiso_desr_soc_year(year)
    return pd.DataFrame(
        {
            "year": year,
            "hour": np.arange(HOURS, dtype=np.int32),
            "net_mw": net,
            "discharge_mw": dis,
            "charge_mw": chg,
            "soc_mwh": soc if soc is not None else np.full(HOURS, np.nan),
            "source": "caiso_outlook_total_batteries"
            + ("+desr_lesr_rtd_soc" if soc is not None else ""),
        }
    )


def build_ercot(year: int) -> pd.DataFrame:
    """Assemble one ERCOT year (EIA-930 BAT + UES) on the model clock."""
    d = pd.read_parquet(ERCO_930, columns=["UTC time", "NG: BAT", "NG: UES"])
    start = pd.to_datetime(d["UTC time"]).dt.tz_localize("UTC") - pd.Timedelta(hours=1)
    slot = std_hour_of_year(start, year, MODEL_TZ["ERCOT"])
    bat = pd.to_numeric(d["NG: BAT"], errors="coerce").to_numpy(dtype=float)
    ues = pd.to_numeric(d["NG: UES"], errors="coerce").to_numpy(dtype=float)
    # An hour is observed when BAT is reported; UES missing there means no
    # separately-filed charging that hour (it is always <= 0 when present).
    net_raw = np.where(np.isfinite(bat), bat + np.nan_to_num(ues), np.nan)
    net = _to_hourly(slot, net_raw, "net")
    dis = _to_hourly(slot, net_raw, "discharge")
    chg = _to_hourly(slot, net_raw, "charge")
    return pd.DataFrame(
        {
            "year": year,
            "hour": np.arange(HOURS, dtype=np.int32),
            "net_mw": net,
            "discharge_mw": dis,
            "charge_mw": chg,
            "soc_mwh": np.full(HOURS, np.nan),
            "source": "eia930_erco_bat_plus_ues",
        }
    )


BUILDERS = {"CAISO": build_caiso, "ERCOT": build_ercot}


def write_sha256sums() -> None:
    """Record the identity of every cached source download."""
    lines = []
    for p in sorted(SRC_DIR.rglob("*")):
        if p.is_file():
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            lines.append(f"{h}  {p.relative_to(OUT_DIR).as_posix()}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--iso", nargs="+", default=["CAISO", "ERCOT"], choices=sorted(BUILDERS)
    )
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023, 2024, 2025])
    args = ap.parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for iso in args.iso:
        frames = []
        for y in args.years:
            f = BUILDERS[iso](y)
            obs = int(np.isfinite(f["net_mw"]).sum())
            if obs == 0:
                print(f"{iso} {y}: no observed hours — skipped")
                continue
            frames.append(f)
            print(
                f"{iso} {y}: {obs} h observed, discharge "
                f"{np.nansum(f['discharge_mw']) / 1e6:.3f} TWh, charge "
                f"{np.nansum(f['charge_mw']) / 1e6:.3f} TWh, SOC hours "
                f"{int(np.isfinite(f['soc_mwh']).sum())}"
            )
        out = OUT_DIR / f"{iso}_storage_hourly.parquet"
        pd.concat(frames, ignore_index=True).to_parquet(out, index=False)
        print(f"wrote {out.relative_to(REPO)}")
    write_sha256sums()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
