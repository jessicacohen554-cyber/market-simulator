"""Transient fetcher for the miso-138 ``da_co`` sample (scratch only, NEVER ``data/raw/``).

miso-138 charter DATA GATE: the MISO submitted-offer corpus is public and
2023-2025 verified live (miso-136), but nothing lands under ``data/raw/``
without explicit intake authorization via the ``data-intake`` contract. A
bridge demonstration on transient fetches is in scope; committing the corpus
is not. This module therefore downloads to a caller-supplied scratch
directory and is never wired into ``config/paths.py``.

Rule 22 ``[R-HOLDOUT]``: the day list is fixed by
``PREREG-miso138-da-co-class-bridge-2026-08-06.md`` section 4 and contains only
2023-, 2024- and 2025-dated operating days. MISO holds no
``calibration-complete`` marker.
"""

from __future__ import annotations

import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_URL = "https://docs.misoenergy.org/marketreports"

# PREREG section 4 sampling plan: 4 days per season per year, fixed before any fetch.
SAMPLE_DAYS: dict[int, dict[str, tuple[str, ...]]] = {
    2023: {
        "summer": ("20230718", "20230719", "20230815", "20230816"),
        "winter": ("20230117", "20230118", "20230214", "20230215"),
    },
    2024: {
        "summer": ("20240716", "20240717", "20240813", "20240814"),
        "winter": ("20240116", "20240117", "20240213", "20240214"),
    },
    2025: {
        "summer": ("20250715", "20250716", "20250812", "20250813"),
        "winter": ("20250114", "20250115", "20250211", "20250212"),
    },
}


def all_days() -> list[tuple[int, str, str]]:
    """Return ``(year, season, YYYYMMDD)`` for every pre-registered sample day."""
    out: list[tuple[int, str, str]] = []
    for year, seasons in SAMPLE_DAYS.items():
        for season, days in seasons.items():
            for day in days:
                out.append((year, season, day))
    return out


def fetch_one(day: str, dest_dir: Path) -> tuple[str, str]:
    """Download one ``YYYYMMDD_da_co.zip`` into ``dest_dir``; return (day, status)."""
    dest = dest_dir / f"{day}_da_co.zip"
    if dest.exists() and dest.stat().st_size > 1000:
        return day, f"cached {dest.stat().st_size}"
    url = f"{BASE_URL}/{day}_da_co.zip"
    try:
        with urllib.request.urlopen(url, timeout=180) as resp:  # noqa: S310 (fixed host)
            body = resp.read()
    except Exception as exc:  # noqa: BLE001 - status is the payload here
        return day, f"ERROR {exc}"
    dest.write_bytes(body)
    return day, f"ok {len(body)}"


def main() -> int:
    """Fetch every pre-registered sample day into ``sys.argv[1]``."""
    dest_dir = Path(sys.argv[1])
    dest_dir.mkdir(parents=True, exist_ok=True)
    days = [d for _, _, d in all_days()]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for day, status in pool.map(lambda d: fetch_one(d, dest_dir), days):
            print(f"{day} {status}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
