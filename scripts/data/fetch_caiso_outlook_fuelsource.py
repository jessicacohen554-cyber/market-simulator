#!/usr/bin/env python3
"""Fetch CAISO "Today's Outlook" historical fuel-mix (5-minute) for whole years.

CAISO publishes its own measured system generation by resource type at
5-minute grain for every past day at
``https://www.caiso.com/outlook/history/<YYYYMMDD>/fuelsource.csv``
(columns: Time, Solar, Wind, Geothermal, Biomass, Biogas, Small hydro, Coal,
Nuclear, Natural gas, Large hydro, Batteries, Imports, Other — MW, Pacific
prevailing clock). It is the ISO-native series EIA-930's CISO per-fuel cells
are reported from.

Why it is in the repo: EIA-930 CISO ``NG: WAT`` is MISSING (NaN, not zero) from
2019-10-01 through 2020-08-24, and ``Net generation`` in those hours is the sum
of the reported fuel cells, so it omits hydro too
(``docs/handoffs/i-caiso/INTAKE-i-caiso-2019-2021-2026-09-24.md`` §3). This
series is the measured source that repairs both — see
:mod:`market_sim.data.eia930.caiso_hydro_backfill`.

Output (raw, immutable once written): ``data/raw/caiso-outlook-fuelsource/
fuelsource_<year>.csv.gz`` — every 5-minute row of every day of the year as
published, with a ``date`` column prepended and the header normalised to lower
snake_case (the source's own header capitalisation varies by day:
"Natural gas" / "Natural Gas", "Large hydro" / "Large Hydro"). No value is
altered. ``SHA256SUMS.txt`` beside it is rewritten.

Usage::

    python scripts/data/fetch_caiso_outlook_fuelsource.py --years 2019 2020 2021
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CAISO_OUTLOOK_FUELSOURCE_DIR  # noqa: E402

URL_TMPL = "https://www.caiso.com/outlook/history/{d:%Y%m%d}/fuelsource.csv"
# Transport retries for a transient network failure (not a data parameter).
_RETRIES = 4


def _get(url: str) -> str:
    """Return the body of ``url``, retrying transient failures with backoff."""
    for attempt in range(_RETRIES):
        try:
            req = Request(url, headers={"User-Agent": "market-simulator data intake"})
            with urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8-sig")
        except (HTTPError, URLError, TimeoutError) as exc:
            if isinstance(exc, HTTPError) and exc.code == 404:
                raise
            time.sleep(2**attempt)
    raise RuntimeError(f"failed after {_RETRIES} attempts: {url}")


def _normalise(col: str) -> str:
    """Lower-snake-case a source header ("Large Hydro" -> "large_hydro")."""
    return col.strip().lower().replace(" ", "_")


def fetch_year(year: int) -> pd.DataFrame:
    """Fetch every day of ``year``; return the concatenated 5-minute frame."""
    frames = []
    day = dt.date(year, 1, 1)
    while day.year == year:
        body = _get(URL_TMPL.format(d=day))
        df = pd.read_csv(io.StringIO(body), dtype=str)
        df.columns = [_normalise(c) for c in df.columns]
        df.insert(0, "date", day.isoformat())
        frames.append(df)
        day += dt.timedelta(days=1)
    return pd.concat(frames, ignore_index=True)


def _write_sums(out_dir: Path) -> None:
    """Rewrite ``SHA256SUMS.txt`` over the directory's yearly payloads."""
    lines = []
    for p in sorted(out_dir.glob("fuelsource_*.csv.gz")):
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (out_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", required=True)
    args = ap.parse_args()
    out_dir = CAISO_OUTLOOK_FUELSOURCE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    for year in args.years:
        df = fetch_year(year)
        path = out_dir / f"fuelsource_{year}.csv.gz"
        buf = df.to_csv(index=False).encode()
        # mtime=0 so a re-fetch of unchanged data is byte-identical.
        path.write_bytes(gzip.compress(buf, compresslevel=9, mtime=0))
        print(f"wrote {path} ({len(df):,} rows, {df['date'].nunique()} days)")
    _write_sums(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
