"""Fetch the PJM real-time Marginal Fuel Postings (IMM / Monitoring Analytics).

Downloads the monthly ``<YYYYMM>_Marginal_Fuel_Postings.csv`` files the PJM
Independent Market Monitor publishes, writes them unmodified to
``data/raw/pjm-marginal-fuel/monthly/`` (the immutable raw pull), records their
sha256 in ``data/raw/pjm-marginal-fuel/SHA256SUMS.txt``, and derives tidy
per-year CSVs ``data/raw/pjm-marginal-fuel/by-year/pjm_marginal_fuel_<YEAR>.csv``
with the ``pjm-marginal-fuel`` schema
(``data/dictionary/schema/pjm-marginal-fuel.schema.yaml``).

Source / provenance
-------------------
* Page   : https://www.monitoringanalytics.com/data/marginal_fuel.shtml
  ("Marginal Fuel Posting"). PJM's own page
  (https://www.pjm.com/markets-and-operations/energy/real-time/historical-bid-data/marg-fuel-type-data.aspx)
  embeds an archive that stops at 2008-12; the IMM page carries 2009 onward.
  Data Miner 2 has no marginal-fuel feed (feed list checked 2026-10-02).
* Files  : https://www.monitoringanalytics.com/data/marginal_fuel_type/<YYYYMM>_Marginal_Fuel_Postings.csv
* Layout : ``HOUR, MMS_TIMEZONE, FUEL_TYPE, PERCENT_MARGINAL`` — one row per
  (hour, fuel); within an hour the fuel shares sum to 1. Per the page: "The
  share of each fuel in each hour is calculated based on the number of five
  minute intervals that a unit burning each fuel type is marginal or jointly
  marginal" (several marginal units per interval under congestion).
* Licence: Monitoring Analytics, "(c) All rights reserved"; its legal page says
  access "does not confer any license". Redistribution terms are unverified, so
  the raw pull and the derived per-year CSVs are gitignored (as
  ``data/raw/NYISO/atc-ttc/``); this script regenerates both from a bare
  checkout.

Rule-13 class: an observed market OUTCOME used only as a diagnostic comparator
(which fuel sets price), never a model input.

Usage::

    python scripts/data/fetch_pjm_marginal_fuel.py [--start 2019-01] [--end 2025-12]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import sys
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DIR  # noqa: E402

#: Raw home of the datatype (a ``config/paths.py`` constant is the src follow-up).
OUT_DIR: Path = RAW_DIR / "pjm-marginal-fuel"
BASE_URL = "https://www.monitoringanalytics.com/data/marginal_fuel_type"
FILE_FMT = "{ym}_Marginal_Fuel_Postings.csv"
USER_AGENT = "Mozilla/5.0 (market-sim data intake)"


def month_range(start: str, end: str) -> list[str]:
    """Return the ``YYYYMM`` strings from ``start`` to ``end`` inclusive (``YYYY-MM``)."""
    return [p.strftime("%Y%m") for p in pd.period_range(start, end, freq="M")]


def download(ym: str, dest: Path, retries: int = 4) -> Path:
    """Download one monthly file to ``dest`` (skipped when already present).

    Args:
        ym: Month as ``YYYYMM``.
        dest: Directory to write into.
        retries: Attempts before giving up.

    Returns:
        The written path.
    """
    name = FILE_FMT.format(ym=ym)
    out = dest / name
    if out.is_file() and out.stat().st_size > 0:
        return out
    url = f"{BASE_URL}/{name}"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)
            return out
        except requests.RequestException:  # pragma: no cover - network
            if attempt == retries - 1:
                raise
            time.sleep(2**attempt)
    return out


def parse_month(path: Path) -> pd.DataFrame:
    """Parse one raw monthly file into the ``pjm-marginal-fuel`` schema.

    Args:
        path: A raw ``<YYYYMM>_Marginal_Fuel_Postings.csv``.

    Returns:
        Columns ``hour_beginning_ept`` (``YYYY-MM-DD HH:00``), ``mms_timezone``,
        ``fuel_type``, ``percent_marginal`` (fraction), ``source_file``.
    """
    raw = pd.read_csv(io.BytesIO(path.read_bytes()))
    raw.columns = [c.strip().upper() for c in raw.columns]
    hour_col = "HOUR" if "HOUR" in raw.columns else "MMS_DATETIME"
    ts = pd.to_datetime(raw[hour_col].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S")
    pct = raw["PERCENT_MARGINAL"].astype(str).str.strip()
    is_pct = pct.str.endswith("%")
    val = pd.to_numeric(pct.str.rstrip("%"), errors="raise")
    val = val.where(~is_pct, val / 100.0)
    return pd.DataFrame(
        {
            "hour_beginning_ept": ts.dt.strftime("%Y-%m-%d %H:00"),
            "mms_timezone": raw["MMS_TIMEZONE"].astype(str).str.strip(),
            "fuel_type": raw["FUEL_TYPE"].astype(str).str.strip(),
            "percent_marginal": val.astype(float),
            "source_file": path.name,
        }
    )


def write_sha256sums(directory: Path, out: Path) -> None:
    """Write ``sha256  relative/path`` lines for every CSV under ``directory``."""
    lines = []
    for p in sorted(directory.glob("*.csv")):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{h}  {p.relative_to(out.parent).as_posix()}")
    out.write_text("\n".join(lines) + "\n")


def derive_by_year(monthly: list[Path], out_dir: Path) -> list[Path]:
    """Concatenate the monthly files into one tidy CSV per calendar year.

    Args:
        monthly: Raw monthly paths.
        out_dir: ``by-year/`` directory.

    Returns:
        The per-year paths written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.concat([parse_month(p) for p in monthly], ignore_index=True)
    df["year"] = df["hour_beginning_ept"].str[:4].astype(int)
    written = []
    for y, g in df.groupby("year"):
        p = out_dir / f"pjm_marginal_fuel_{y}.csv"
        g.drop(columns="year").sort_values(
            ["hour_beginning_ept", "mms_timezone", "fuel_type"]
        ).to_csv(p, index=False)
        written.append(p)
    return written


def main() -> None:
    """CLI entry point: download, checksum, derive."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", default="2019-01", help="first month YYYY-MM")
    ap.add_argument("--end", default="2025-12", help="last month YYYY-MM")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    monthly_dir = args.out_dir / "monthly"
    monthly_dir.mkdir(parents=True, exist_ok=True)
    paths = [download(ym, monthly_dir) for ym in month_range(args.start, args.end)]
    write_sha256sums(monthly_dir, args.out_dir / "SHA256SUMS.txt")
    for p in derive_by_year(paths, args.out_dir / "by-year"):
        print(p, p.stat().st_size)


if __name__ == "__main__":
    main()
