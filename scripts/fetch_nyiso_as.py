"""Fetch NYISO ancillary-services clearing-price monthly zips (rtasp/damasp).

Downloads the monthly archives NYISO posts on its MIS public site straight
into ``data/raw/NYISO-AS/raw/`` — the ``RAW_DIR`` that
``scripts/process_nyiso_as.py`` folds into the per-year
``NYISO_as_{rt,da}_<year>.csv`` files. This is the fetch half of the pipeline
that script's README used to call broken: there was no automated path that
produced ``RAW_DIR`` at all (the script expected a hand-supplied
``NYISO-AS-Data.zip`` outer zip that does not exist anywhere in this repo).
This script is that missing path.

Two monthly report families, one row per NYISO zone per settlement interval:

* **Real-time** (5-minute) — ``rtasp``:
  ``<yyyymm01>rtasp_csv.zip``, columns ``Time Stamp, Time Zone, Name, PTID,
  10 Min Spinning Reserve ($/MWHr), 10 Min Non-Synchronous Reserve ($/MWHr),
  30 Min Operating Reserve ($/MWHr), NYCA Regulation Capacity ($/MWHr),
  NYCA Regulation Movement ($/MW)``.
* **Day-ahead** (hourly) — ``damasp``:
  ``<yyyymm01>damasp_csv.zip``, same columns minus Regulation Movement (a
  real-time-only quantity — the DAM does not clear movement).

Source URL pattern (no authentication; confirmed with live HTTP 200s across
2018-01 .. 2026-05, see the fetch script's own module test / the intake
workflow's validation step):
    http://mis.nyiso.com/public/csv/rtasp/<yyyymm01>rtasp_csv.zip
    http://mis.nyiso.com/public/csv/damasp/<yyyymm01>damasp_csv.zip

NYISO publishes clearing prices only — no cleared MW for these products.

Notes
-----
* The monthly zip is a zip-of-daily-CSVs (one member per calendar day); this
  script does not unzip or parse them — it only lands the zips under
  ``RAW_DIR`` byte-for-byte, exactly as ``process_nyiso_as.py`` (via its
  ``_canonical_zips``/``_read_zip`` helpers) already expects. Column parsing,
  zone filtering and hourly aggregation stay in that script; this one is
  fetch-only, mirroring the ``fetch_nyiso_operating_events.py`` /
  ``fetch_nyiso_interface_flows.py`` division of labor.
* Zip filenames are written verbatim as NYISO names them
  (``<yyyymm>01<report>_csv.zip``), which already satisfies
  ``process_nyiso_as.py``'s ``{year}*{token}asp_csv*.zip`` glob.
* Year range: 2018 through H1-2026. Out-of-training years (2018-2022, 2026)
  are intaken under the session-logged owner authorization of 2026-07-10
  (CLAUDE.md rule 22; itemized in docs/out-of-sample-results-2026-07.md §1).
  Nothing past 2026-06 is fetched: --end-month enforces the H1-2026 cap.
* Re-runs are idempotent and cheap: an already-downloaded zip (non-empty
  file already at the destination path) is left alone, so a partial run can
  always be resumed.

Run: ``python scripts/fetch_nyiso_as.py [--out-dir DIR] [--market rt da]``
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
AS_DIR = REPO_ROOT / "data" / "raw" / "NYISO-AS"
# Gitignored raw staging dir (data/raw/NYISO-AS/raw/, see .gitignore) — the
# exact RAW_DIR process_nyiso_as.py folds into the committed per-year CSVs.
RAW_DIR = AS_DIR / "raw"

MIS_BASE = "http://mis.nyiso.com/public/csv"

# CLI market token -> (MIS report directory name, MIS filename infix).
# process_nyiso_as.py's own _MARKET_TOKEN maps "rt"->"rt", "da"->"dam"; the
# MIS report directory names are lowercase "rtasp" / "damasp".
_MARKETS = {"rt": "rtasp", "da": "damasp"}

# Authorized acquisition window (rule 22; owner authorization 2026-07-10).
START_MONTH = "2018-01"
END_MONTH = "2026-06"  # H1-2026 hard cap — never extend without authorization


def _month_range(start: str, end: str) -> list[str]:
    """Inclusive list of YYYYMM month tokens between two YYYY-MM bounds."""
    return [p.strftime("%Y%m") for p in pd.period_range(start=start, end=end, freq="M")]


def _download(url: str, dest: Path, retries: int = 4) -> None:
    """Download ``url`` to ``dest`` unless already cached; simple retry loop.

    Mirrors ``fetch_nyiso_operating_events.py``/``fetch_nyiso_interface_flows.py``:
    a non-empty file already at ``dest`` short-circuits the request so a
    partial run resumes cheaply.
    """
    if dest.is_file() and dest.stat().st_size > 0:
        return
    last: Exception | None = None
    for _attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                dest.write_bytes(resp.read())
            return
        except OSError as exc:  # includes URLError / timeouts
            last = exc
    raise RuntimeError(f"failed to download {url}: {last}")


def fetch(
    out_dir: Path = RAW_DIR,
    markets: tuple[str, ...] = ("rt", "da"),
    start: str = START_MONTH,
    end: str = END_MONTH,
) -> list[Path]:
    """Download every monthly rtasp/damasp zip in ``[start, end]`` into ``out_dir``.

    Parameters
    ----------
    out_dir:
        Destination for the monthly zips — defaults to ``RAW_DIR``
        (``data/raw/NYISO-AS/raw/``), which ``process_nyiso_as.py`` reads
        directly. Gitignored; not committed.
    markets:
        Subset of ``("rt", "da")`` to fetch.
    start, end:
        YYYY-MM month bounds; ``end`` may never exceed the H1-2026
        authorization cap (enforced).

    Returns the list of zip paths written (or already present).
    """
    if end > END_MONTH:
        raise ValueError(
            f"end month {end} exceeds the authorized acquisition cap {END_MONTH} "
            "(CLAUDE.md rule 22 holdout quarantine)"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for market in markets:
        mis_name = _MARKETS[market]
        for month in _month_range(start, end):
            fname = f"{month}01{mis_name}_csv.zip"
            dest = out_dir / fname
            _download(f"{MIS_BASE}/{mis_name}/{fname}", dest)
            written.append(dest)
            print(f"fetched {dest.name} ({dest.stat().st_size:,} bytes)")
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: fetch the monthly AS-price zips into ``RAW_DIR``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=RAW_DIR,
        help="destination for the monthly zips (default: data/raw/NYISO-AS/raw/)",
    )
    parser.add_argument(
        "--market", nargs="+", default=["rt", "da"], choices=["rt", "da"]
    )
    parser.add_argument("--start-month", default=START_MONTH, help="YYYY-MM")
    parser.add_argument(
        "--end-month", default=END_MONTH, help="YYYY-MM (capped at H1-2026)"
    )
    args = parser.parse_args(argv)
    fetch(args.out_dir, tuple(args.market), args.start_month, args.end_month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
