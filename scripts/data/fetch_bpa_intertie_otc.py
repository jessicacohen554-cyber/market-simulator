"""Fetch BPA OPI intertie loadings and operating limits (COI and the BC Intertie).

BPA Transmission's Operations Information page ("BPA Paths - OPI Interties &
Flowgates", https://transmission.bpa.gov/Business/Operations/Paths/) archives,
per intertie and calendar month, one spreadsheet of 15-minute rows, each the
15-minute average of 2-second SCADA data:

=========================  ===================================================
``AC`` (AC Intertie, COI)  Actual loading (+ = to California), N-S TTC, S-N
                           TTC (published negative), loop flow (COI + Path 66)
``BC`` (BC Intertie,       Actual loading (+ = south-to-north, to BC), S-N
Path 3, West + East)       TTC, N-S TTC (published negative)
=========================  ===================================================

Each file's Notes sheet defines the TTC columns as the intertie's *operating
limit* (the SOL BPA monitors against, "not considering Intertie Ownership"),
which moves hour to hour with outages and system conditions. The archive
reaches back to 1996, so it covers every NWPP backcast year (2019-2025). CAISO's
OASIS ``TRNS_USAGE`` (``data/raw/caiso-trns-usage``) covers only 2023-06-19
onwards.

Two stages, both idempotent:

* fetch: reads the per-intertie ``Monthly.aspx`` history index, downloads
  every monthly file for ``--years`` into ``data/raw/nwpp-intertie-otc/windows/``
  (gitignored staging; an existing file is skipped, so reruns resume).
* ``--fold``: parses the staged files into one committed parquet per calendar
  year, ``bpa_intertie_otc_<year>.parquet`` (long: ``path``, ``ts_end_local``,
  ``actual_mw``, ``ns_ttc_mw``, ``sn_ttc_mw``, ``loop_mw``), and rewrites
  ``SHA256SUMS.txt``.

The fold is lossless for the Data sheet. Values and signs are kept exactly as
published, and ``ts_end_local`` is the published "Date/Period Ending" stamp in
Pacific prevailing time. The fold asserts the header row of every file
against :data:`COLUMN_MAP` and stops if a column it would drop or rename
changes.

Run::

    python scripts/data/fetch_bpa_intertie_otc.py --years 2019 2020 2021 2022 2023 2024 2025
    python scripts/data/fetch_bpa_intertie_otc.py --fold
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.paths import RAW_DIR  # noqa: E402

OUT_DIR = RAW_DIR / "nwpp-intertie-otc"
STAGE_DIR = OUT_DIR / "windows"
INDEX_URL = (
    "https://transmission.bpa.gov/Business/Operations/Paths/Monthly.aspx"
    "?Type=Intertie&ReportID={path}&ReportName={path}"
)

#: Published Data-sheet header prefix -> folded column, per intertie. The
#: header carries the SCADA point id in parentheses; the fold matches the text
#: before it so a re-pointed SCADA id does not break the fold silently: the
#: point ids are recorded in the README instead.
COLUMN_MAP: dict[str, dict[str, str]] = {
    "AC": {
        "AC Intertie: Actual": "actual_mw",
        "AC Intertie: N-S TTC": "ns_ttc_mw",
        "AC Intertie: S-N TTC": "sn_ttc_mw",
        "Loop Flow Intertie": "loop_mw",
    },
    "BC": {
        "BC Intertie: Actual": "actual_mw",
        "BC Intertie: S-N TTC": "sn_ttc_mw",
        "BC Intertie: N-S TTC": "ns_ttc_mw",
    },
}
FOLDED_COLUMNS: tuple[str, ...] = (
    "path",
    "ts_end_local",
    "actual_mw",
    "ns_ttc_mw",
    "sn_ttc_mw",
    "loop_mw",
)


def month_urls(path: str, years: list[int]) -> list[str]:
    """Return the monthly file URLs for ``path`` in ``years`` from BPA's index page."""
    with urllib.request.urlopen(INDEX_URL.format(path=path), timeout=120) as resp:
        html = resp.read().decode("utf-8", "replace")
    pat = re.compile(
        rf"https://[^\"']*/Interties/monthly/{path}/(\d{{4}})/{path}_\d{{4}}-\d{{2}}\.xlsx?",
        re.IGNORECASE,
    )
    urls = sorted({m.group(0) for m in pat.finditer(html) if int(m.group(1)) in years})
    if not urls:
        raise RuntimeError(f"{path}: no monthly files listed for {years}")
    return urls


def fetch(years: list[int]) -> None:
    """Download every monthly AC/BC file for ``years`` into the staging dir."""
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    for path in COLUMN_MAP:
        for url in month_urls(path, years):
            dest = STAGE_DIR / url.rsplit("/", 1)[1]
            if dest.exists() and dest.stat().st_size > 1024:
                continue
            for attempt in range(4):
                try:
                    urllib.request.urlretrieve(url, dest)
                    break
                except OSError:
                    time.sleep(2 ** (attempt + 1))
            else:
                raise RuntimeError(f"failed to fetch {url}")
            print(f"fetched {dest.name}")


def parse_month(file: Path) -> pd.DataFrame:
    """Parse one staged monthly file's Data sheet into the folded long columns."""
    path = file.name.split("_", 1)[0].upper()
    sheets = pd.read_excel(file, sheet_name=None, header=None)
    data = next(v for k, v in sheets.items() if "data" in str(k).lower())
    header = [str(h) for h in data.iloc[2].tolist()]
    if not header[0].lower().startswith("date/period ending"):
        raise ValueError(f"{file.name}: unexpected first header {header[0]!r}")
    body = data.iloc[3:].reset_index(drop=True)
    out = pd.DataFrame(
        {
            "path": path,
            "ts_end_local": pd.to_datetime(body.iloc[:, 0]),
        }
    )
    mapping = COLUMN_MAP[path]
    seen: set[str] = set()
    for i, h in enumerate(header[1:], start=1):
        key = next((k for k in mapping if h.startswith(k)), None)
        if key is None:
            raise ValueError(f"{file.name}: unmapped column {h!r}")
        out[mapping[key]] = pd.to_numeric(body.iloc[:, i], errors="coerce")
        seen.add(key)
    if seen != set(mapping):
        raise ValueError(f"{file.name}: missing columns {set(mapping) - seen}")
    for col in FOLDED_COLUMNS:
        if col not in out:
            out[col] = float("nan")
    return out[list(FOLDED_COLUMNS)].dropna(subset=["ts_end_local"])


def fold() -> list[Path]:
    """Fold the staged monthly files into one committed parquet per calendar year."""
    files = sorted(STAGE_DIR.glob("*_*.xls*"))
    if not files:
        raise RuntimeError(f"nothing staged in {STAGE_DIR}")
    frame = pd.concat([parse_month(f) for f in files], ignore_index=True)
    frame["path"] = frame["path"].astype("string")
    frame = frame.drop_duplicates(subset=["path", "ts_end_local"], keep="first")
    frame = frame.sort_values(["path", "ts_end_local"]).reset_index(drop=True)
    written: list[Path] = []
    for year, part in frame.groupby(frame["ts_end_local"].dt.year):
        dest = OUT_DIR / f"bpa_intertie_otc_{year}.parquet"
        part.reset_index(drop=True).to_parquet(dest, index=False)
        written.append(dest)
        print(f"wrote {dest.name}: {len(part)} rows")
    lines = []
    for p in sorted(OUT_DIR.glob("bpa_intertie_otc_*.parquet")):
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    return written


def main() -> None:
    """CLI: fetch the monthly files for ``--years``, or ``--fold`` the staging dir."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--fold", action="store_true", help="fold staged files")
    args = ap.parse_args()
    if args.fold:
        fold()
    else:
        fetch(args.years)


if __name__ == "__main__":
    main()
