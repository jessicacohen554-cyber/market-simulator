"""Fetch MISO's masked submitted energy-offer corpus (``*_da_co`` / ``*_rt_co``).

MISO publishes, daily and at a ~90-day lag, every market participant's
**submitted** energy offer curve at masked-unit × hour grain:

    https://docs.misoenergy.org/marketreports/YYYYMMDD_da_co.zip   (Day-Ahead)
    https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_co.zip   (Real-Time)

Each zip holds one CSV: one row per (masked ``Unit Code`` × operating hour)
carrying the full ten-segment price/MW offer curve, economic and emergency
limits, the economic / emergency / must-run / unit-available declarations,
self-scheduled MW, the curtailment offer price, the slope flag, and (for
storage) energy-level bounds.  Region is published as North / Central / South.
**No fuel or technology attribute is published** — the corpus is a conduct
transparency publication and unit identity is deliberately masked
(``FINDING-miso136-ct-offer-conduct-corpus-exists-2026-08-06.md``).

This fetcher writes **verbatim source bytes** into the immutable raw mirror

    data/raw/miso-energy-offers/<market>/<YYYYMMDD>_<market>_co.zip

and maintains ``manifest.json`` beside them recording per-file sha256, byte
size and fetch timestamp, so the corpus is reproducible without re-deriving
anything.  The zips themselves are gitignored (the ``pjm-energy-offers`` /
``caiso-public-bids`` precedent — the JJA 2023-2025 corpus is ~470 MB); the
README and this script are the reproducibility path.

RULE 13 ``[R-MEASURED]``: the corpus's **offer** columns are participant
declarations recorded ex ante and are admissible measured inputs.  Its
**award** columns (RT ``Cleared MW1``-``Cleared MW12``, DA ``MW``) are dispatch
OUTCOMES — the answer class — and are dropped at curation and never written to
the clean datatype (``scripts/data/curate_miso_energy_offers.py``).

RULE 22 ``[R-HOLDOUT]``: MISO holds no ``calibration-complete`` marker, so the
default span is the 2023-2025 training window.  Any other year requires
``--allow-out-of-train`` **and** session-logged owner authorization.

Usage::

    python scripts/data/fetch_miso_energy_offers.py                 # JJA 2023-2025, both markets
    python scripts/data/fetch_miso_energy_offers.py --markets rt
    python scripts/data/fetch_miso_energy_offers.py --years 2025 --months 6 7 8
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import json
import logging
import sys
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_miso_energy_offers")

BASE_URL = "https://docs.misoenergy.org/marketreports"

#: Calibration training window (CLAUDE.md rule 22 ``[R-HOLDOUT]``).
TRAIN_YEARS: tuple[int, ...] = (2023, 2024, 2025)
#: The summer window the miso-145 offer-conduct lane is defined on.
DEFAULT_MONTHS: tuple[int, ...] = (6, 7, 8)
MARKETS: tuple[str, ...] = ("da", "rt")

_RETRIES = 4
_TIMEOUT_S = 180
_WORKERS = 8


def out_dir(market: str) -> Path:
    """Return the immutable raw mirror directory for ``market`` (``da``/``rt``)."""
    return paths.MISO_ENERGY_OFFERS_DIR / market


def operating_days(years: tuple[int, ...], months: tuple[int, ...]) -> list[str]:
    """Return ``YYYYMMDD`` strings for every day in ``years`` x ``months``."""
    days: list[str] = []
    for year in years:
        for month in months:
            n = calendar.monthrange(year, month)[1]
            days += [f"{year:04d}{month:02d}{d:02d}" for d in range(1, n + 1)]
    return days


def _fetch(url: str) -> bytes:
    """Return the response body for ``url``, retrying transient failures."""
    last: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as resp:  # noqa: S310
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:  # a genuinely absent operating day, not transient
                raise
            last = exc
        except Exception as exc:  # noqa: BLE001 - retry then re-raise
            last = exc
        log.debug("retry %d for %s (%s)", attempt + 1, url, last)
    raise RuntimeError(f"fetch failed after {_RETRIES} attempts: {url}") from last


def fetch_one(day: str, market: str, *, force: bool = False) -> dict:
    """Download one ``<day>_<market>_co.zip`` into the raw mirror.

    Returns a manifest row ``{day, market, status, bytes, sha256, member}``.
    An already-present, structurally-valid zip is left untouched (``cached``):
    ``data/raw`` is immutable once landed.
    """
    dest = out_dir(market) / f"{day}_{market}_co.zip"
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        body = dest.read_bytes()
        status = "cached"
    else:
        url = f"{BASE_URL}/{day}_{market}_co.zip"
        try:
            body = _fetch(url)
        except urllib.error.HTTPError as exc:
            return {"day": day, "market": market, "status": f"http_{exc.code}"}
        except Exception as exc:  # noqa: BLE001 - recorded, never silently dropped
            return {"day": day, "market": market, "status": f"error:{exc}"}
        status = "fetched"

    # Structural check before the bytes are trusted as a landed mirror.
    try:
        with zipfile.ZipFile(dest if status == "cached" else _stage(dest, body)) as z:
            members = z.namelist()
    except Exception as exc:  # noqa: BLE001
        dest.unlink(missing_ok=True)
        return {"day": day, "market": market, "status": f"bad_zip:{exc}"}

    return {
        "day": day,
        "market": market,
        "status": status,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "member": members[0] if members else None,
        "n_members": len(members),
    }


def _stage(dest: Path, body: bytes) -> Path:
    """Write ``body`` to ``dest`` and return it (separated for readability)."""
    dest.write_bytes(body)
    return dest


def write_manifest(rows: list[dict]) -> Path:
    """Merge ``rows`` into the raw mirror's ``manifest.json`` and return its path."""
    path = paths.MISO_ENERGY_OFFERS_DIR / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    prior: dict[str, dict] = {}
    if path.exists():
        prior = {
            f"{r['market']}|{r['day']}": r
            for r in json.loads(path.read_text())["files"]
        }
    for r in rows:
        prior[f"{r['market']}|{r['day']}"] = r
    payload = {
        "source": f"{BASE_URL}/YYYYMMDD_<market>_co.zip",
        "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "n_files": len(prior),
        "files": [prior[k] for k in sorted(prior)],
    }
    path.write_text(json.dumps(payload, indent=1))
    return path


def main() -> None:
    """CLI entry point — fetch the requested market/year/month span."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=list(TRAIN_YEARS))
    ap.add_argument("--months", type=int, nargs="+", default=list(DEFAULT_MONTHS))
    ap.add_argument("--markets", nargs="+", default=list(MARKETS), choices=MARKETS)
    ap.add_argument("--force", action="store_true", help="re-download cached files")
    ap.add_argument(
        "--allow-out-of-train",
        action="store_true",
        help="permit years outside 2023-2025 (rule 22: needs owner authorization)",
    )
    args = ap.parse_args()

    bad = [y for y in args.years if y not in TRAIN_YEARS]
    if bad and not args.allow_out_of_train:
        raise SystemExit(
            f"rule 22 [R-HOLDOUT]: MISO holds no calibration-complete marker; "
            f"years {bad} are outside the 2023-2025 training window. "
            f"Pass --allow-out-of-train only with session-logged owner authorization."
        )

    days = operating_days(tuple(args.years), tuple(args.months))
    jobs = [(d, m) for m in args.markets for d in days]
    log.info(
        "fetching %d files (%d days x %d markets)",
        len(jobs),
        len(days),
        len(args.markets),
    )

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        for row in pool.map(lambda j: fetch_one(j[0], j[1], force=args.force), jobs):
            rows.append(row)
            if row["status"] not in ("fetched", "cached"):
                log.warning("%s %s -> %s", row["market"], row["day"], row["status"])

    ok = sum(1 for r in rows if r["status"] in ("fetched", "cached"))
    total_mb = sum(r.get("bytes", 0) for r in rows) / 1e6
    log.info("%d/%d ok, %.1f MB", ok, len(rows), total_mb)
    log.info("manifest -> %s", write_manifest(rows))


if __name__ == "__main__":
    main()
