"""Download NYISO's public masked generator bid data (MIS report P-27).

**Why this source exists in the repo.** The nyiso-242 intake charter
(`docs/RESULT-nyiso242-cc-winter-refused-and-the-intake-charter-2026-09-20.md`
§2.5) refuted the CAMPD cold-hour availability census on its own discriminator:
CAMPD meters what **ran**, and every route from "what ran" to "what could have
run" passes through dispatch, commitment and reserve holding. The charter's
binding requirement for a successor intake is therefore a source that states
**AVAILABILITY DIRECTLY**.

NYISO's P-27 bid archive does exactly that. Each row is one masked generator ×
one hour × one market, and it carries the resource's own declared

    Upper Oper Limit   — the MW the unit told the ISO it could produce,
    Emer Oper Limit    — its emergency ceiling,
    Fixed Min Gen MW   — its declared minimum,

plus the full 12-block economic bid curve, start-up/min-gen costs, self-commit
schedule, and — decisive for the charter's confounder (3) — the unit's own
**ancillary-service offers** (10-min non-synch / spin, 30-min non-synch / spin,
regulation). A CT metering zero in CAMPD *because it is being held as reserve*
is visible here as a positive reserve offer, so "available but not dispatched"
and "not available" separate cleanly for the first time in this lane.

Two markets are published in the same file and they answer different questions:

    DAM — the day-ahead bid, submitted before the 05:00 ET DAM close;
    HAM — the hour-ahead (RTC/RTD) bid, resubmittable ~75 min ahead, so it is
          the one that carries a forced outage or a cold derate that appeared
          AFTER the day-ahead market closed.

Masking: ``Masked Gen ID`` / ``Masked Bidder ID`` are stable surrogate keys with
no published crosswalk to a PTID or a plant. **This source can therefore key a
fleet- or cohort-level availability measurement; it cannot key a per-unit
derate**, and nothing here should be read as claiming otherwise. (It is also
the reason CLAUDE.md's "NYISO publishes no 60-Day-DAM equivalent" — the
identification note on `nyiso_gas_commitment_bridge` — stands as written: what
is missing at NYISO is the *unit identity*, not the offer data.)

Source URL pattern (no authentication, monthly archives back to 1999-11)::

    https://mis.nyiso.com/public/csv/biddata/<YYYYMM01>biddata_genbids_csv.zip

Layout produced (payload gitignored — the corpus-conversion class of
`docs/bloat-removal-plan-2026-08.md` §4; this committed downloader plus
``SHA256SUMS.txt`` is the recovery route)::

    data/raw/nyiso-bid-data/genbids/<YYYYMM01>biddata_genbids_csv.zip

The upstream zip is stored **verbatim** — raw is immutable, and re-serializing
would break the SHA256 identity record.

Rule 13 `[R-MEASURED]` admissibility: an offered upper operating limit is a
measured physical/market availability statement that regenerates for any year
from the same public archive and responds to changed conditions. It is a
legitimate input. What it must never become is a channel for pinning the model
to a price residual (rules 1 / 13).

Usage::

    python3 scripts/data/fetch_nyiso_bid_data.py --years 2022 2025
    python3 scripts/data/fetch_nyiso_bid_data.py --years 2022 --months 1 2 12
    python3 scripts/data/fetch_nyiso_bid_data.py --years 2022 --checksums
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

#: Root of the P-27 corpus. Payload gitignored; README + SHA256SUMS tracked.
BID_DATA_DIR: Path = RAW_DATA_DIR / "nyiso-bid-data"
GENBIDS_DIR: Path = BID_DATA_DIR / "genbids"

URL_TEMPLATE = "https://mis.nyiso.com/public/csv/biddata/{stamp}biddata_genbids_csv.zip"

_UA = "market-sim/1.0 (calibration data intake; contact via repository owner)"
_TIMEOUT_S = 300


def _url(year: int, month: int) -> str:
    return URL_TEMPLATE.format(stamp=f"{year:04d}{month:02d}01")


def _target(year: int, month: int) -> Path:
    return GENBIDS_DIR / f"{year:04d}{month:02d}01biddata_genbids_csv.zip"


def fetch_month(year: int, month: int, *, force: bool = False) -> Path | None:
    """Download one monthly archive; return its path, or ``None`` on failure.

    Existing files are left alone unless ``force`` is set — raw downloads are
    immutable and re-fetching costs the upstream server for no benefit.
    """
    dest = _target(year, month)
    if dest.exists() and not force:
        print(f"  {dest.name}: present ({dest.stat().st_size:,} B) — skipped")
        return dest

    url = _url(year, month)
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            payload = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover - network
        print(f"  {dest.name}: FAILED ({exc})")
        return None

    # Validate before writing: a proxy error page is not a zip, and a truncated
    # archive must never land in data/raw looking like a good download.
    try:
        with zipfile.ZipFile(__import__("io").BytesIO(payload)) as zf:
            names = zf.namelist()
            bad = zf.testzip()
    except zipfile.BadZipFile:
        print(f"  {dest.name}: FAILED (not a zip; {len(payload):,} B received)")
        return None
    if bad is not None or not names:
        print(f"  {dest.name}: FAILED (corrupt member {bad!r})")
        return None

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    print(f"  {dest.name}: {len(payload):,} B, {len(names)} member(s)")
    return dest


def write_checksums(directory: Path = GENBIDS_DIR) -> Path:
    """Write ``SHA256SUMS.txt`` over the corpus — the tracked identity record."""
    lines = []
    for path in sorted(directory.glob("*.zip")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    out = directory / "SHA256SUMS.txt"
    out.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(f"SHA256SUMS.txt: {len(lines)} entries")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--years", type=int, nargs="+", required=True)
    parser.add_argument(
        "--months",
        type=int,
        nargs="+",
        default=list(range(1, 13)),
        help="Calendar months to fetch (default: all twelve).",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-download existing files."
    )
    parser.add_argument(
        "--checksums",
        action="store_true",
        help="Only (re)write SHA256SUMS.txt over what is already on disk.",
    )
    args = parser.parse_args(argv)

    if args.checksums:
        write_checksums()
        return 0

    ok = 0
    failed: list[str] = []
    for year in args.years:
        print(f"{year}:")
        for month in args.months:
            if fetch_month(year, month, force=args.force) is not None:
                ok += 1
            else:
                failed.append(f"{year}-{month:02d}")

    write_checksums()
    print(f"\n{ok} archive(s) on disk; {len(failed)} failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
