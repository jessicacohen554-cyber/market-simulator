"""Fetch MISO's annual M2M/CMP flowgate settlement consolidations.

Downloads the public annual Market-to-Market settlement files — the hourly
per-flowgate Congestion Management Process record for MISO's two M2M seams
(MISO–PJM, MISO–SPP): both parties' RT shadow prices, market flows and Firm
Flow Entitlements plus settlement credits:

    https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_YYYY.csv

into gzip source mirrors under ``data/raw/miso-m2m-flowgates/``
(``M2M_Settlement_srw_YYYY.csv.gz`` — verbatim bytes, gzipped at rest). Same
no-auth channel as the miso-76 bc_HIST intake; fetchability, coverage and
the seam-class scoping were established by
``docs/handoffs/miso-77-m4-afc-feasibility-2026-07.md`` §2a and the intake
was chartered by the miso-176 session (miso-174 §7 item 3).

RULE 13 (CLAUDE.md): the shadow-price / market-flow / credit columns are the
ANSWER class — when a coordinated flowgate binds and what actually flowed
are dispatch outcomes; they exist to name what bound in reality (validation/
diagnosis) and are NEVER an LP or derive input. The FFE columns are a CMP
market-design quantity, admissible in kind subject to rule 17's forward
story in whatever mechanism would consume them.

The mirrors are TRACKED in git (~1.5-2.1 MB gzipped each; owner ruling
2026-08-30 — ``scripts/regenerate_clean.py`` must rebuild all 51 datatypes
from a fresh clone, and this was the one datatype whose raw mirror was
absent). This script is the re-fetch/verification path: the gzip container
is written deterministically (mtime=0, no filename field), so refetching an
unchanged source reproduces the committed mirror byte-for-byte and
``data/raw/miso-m2m-flowgates/SHA256SUMS.txt`` verifies either direction.
The raw README records each mirror's raw-csv sha256/size/rows at fetch time.

Quarantine (CLAUDE.md rule 22): defaults to the 2023-2025 train window;
any other year requires ``--allow-out-of-train`` and session-logged owner
authorization.

Usage:
    python scripts/data/fetch_miso_m2m_flowgates.py
    python scripts/data/fetch_miso_m2m_flowgates.py --years 2025
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import logging
import urllib.request
from pathlib import Path

from market_sim.config.paths import RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_miso_m2m_flowgates")

OUT_DIR = RAW_DIR / "miso-m2m-flowgates"

_URL = "https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_{year}.csv"

# Calibration train window (CLAUDE.md rule 22).
TRAIN_YEARS: tuple[int, ...] = (2023, 2024, 2025)

_RETRIES = 3
_TIMEOUT_S = 300  # annual consolidations run to ~20 MB


def _fetch(url: str) -> bytes:
    """Return the response body for ``url``, retrying transient failures."""
    last: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - retry then re-raise
            last = exc
            log.warning("retry %d/%d %s (%s)", attempt + 1, _RETRIES, url, exc)
    raise RuntimeError(f"failed after {_RETRIES} attempts: {url}") from last


def fetch_year(year: int, force: bool = False) -> Path:
    """Mirror one year's M2M settlement consolidation; skip if on disk.

    Returns the mirror path. Logs the verbatim payload's sha256, byte size
    and line count for the raw README's provenance table.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"M2M_Settlement_srw_{year}.csv.gz"
    if out.is_file() and not force:
        log.info("%s already mirrored (use --force to refetch)", out.name)
        return out
    body = _fetch(_URL.format(year=year))
    digest = hashlib.sha256(body).hexdigest()
    n_lines = body.count(b"\n")
    # Deterministic gzip container (mtime=0, empty filename field): the
    # mirrors are tracked, so an unchanged source must refetch byte-identical
    # to the committed file (SHA256SUMS.txt / git diff verify it directly).
    with out.open("wb") as raw_fh:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw_fh, compresslevel=9, mtime=0
        ) as fh:
            fh.write(body)
    log.info(
        "%s: %d bytes raw (%d lines) sha256=%s -> %s",
        _URL.format(year=year),
        len(body),
        n_lines,
        digest,
        out.name,
    )
    return out


def main() -> None:
    """CLI: mirror the requested annual settlement consolidations."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(TRAIN_YEARS))
    ap.add_argument("--force", action="store_true", help="refetch existing mirrors")
    ap.add_argument(
        "--allow-out-of-train",
        action="store_true",
        help="permit out-of-train years (owner-authorized intake only, rule 22)",
    )
    args = ap.parse_args()
    bad = sorted(set(args.years) - set(TRAIN_YEARS))
    if bad and not args.allow_out_of_train:
        raise SystemExit(
            f"years {bad} are outside the train window {TRAIN_YEARS} — pass "
            "--allow-out-of-train only with session-logged owner "
            "authorization (CLAUDE.md rule 22)"
        )
    for year in args.years:
        fetch_year(year, force=args.force)


if __name__ == "__main__":
    main()
