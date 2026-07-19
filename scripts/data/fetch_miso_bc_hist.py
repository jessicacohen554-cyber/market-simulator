"""Fetch MISO's annual consolidated binding-constraints histories (bc_HIST).

Downloads the public annual consolidations of every Day-Ahead / Real-Time
binding transmission constraint (constraint name, interval, preliminary
shadow price, TCDC demand-curve breakpoints):

    https://docs.misoenergy.org/marketreports/YYYY_da_bc_HIST.csv
    https://docs.misoenergy.org/marketreports/YYYY_rt_bc_HIST.csv

into gzip source mirrors under ``data/raw/transfer-constraint-binding/MISO/``
(``YYYY_<market>_bc_HIST.csv.gz`` — verbatim bytes, gzipped at rest). The
mirrors are the reproducible local copy behind the miso-76 congestion
*validation* layer (charter
``docs/handoffs/miso-nc-price-separation-design-2026-07.md`` §2a/§7 A2(ii);
first consumer: ``scripts/probes/_miso76_bc_boundary_rank.py``).

RULE 13 (CLAUDE.md): binding shadow prices are the ANSWER class — when/how
hard a constraint binds is a dispatch outcome. This record exists to LOCATE
and RANK measured congestion for validation targets and is NEVER an LP or
derive input. It deliberately gets no clean-datatype extension: the
``transfer-constraint-binding`` clean schema stays RDT-specific, and
validation consumers read these mirrors directly (see the raw README).

The bulk mirrors are gitignored (~20-70 MB each raw; precedent:
``data/raw/caiso-public-bids``) — this script is the reproducibility path,
and the raw README records each mirror's sha256/size/rows at fetch time.

Quarantine (CLAUDE.md rule 22): defaults to the 2023-2025 train window;
any other year requires ``--allow-out-of-train`` and session-logged owner
authorization.

Usage:
    python scripts/data/fetch_miso_bc_hist.py
    python scripts/data/fetch_miso_bc_hist.py --years 2024 --markets rt
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
log = logging.getLogger("fetch_miso_bc_hist")

OUT_DIR = RAW_DIR / "transfer-constraint-binding" / "MISO"

_URL = "https://docs.misoenergy.org/marketreports/{year}_{market}_bc_HIST.csv"

# Calibration train window (CLAUDE.md rule 22).
TRAIN_YEARS: tuple[int, ...] = (2023, 2024, 2025)
MARKETS: tuple[str, ...] = ("da", "rt")

_RETRIES = 3
_TIMEOUT_S = 300  # the RT consolidations run to ~70 MB


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


def fetch_year(year: int, market: str, force: bool = False) -> Path:
    """Mirror one (year, market) consolidation; skip if already on disk.

    Returns the mirror path. Logs the verbatim payload's sha256, byte size
    and line count for the raw README's provenance table.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{year}_{market}_bc_HIST.csv.gz"
    if out.is_file() and not force:
        log.info("%s already mirrored (use --force to refetch)", out.name)
        return out
    body = _fetch(_URL.format(year=year, market=market))
    digest = hashlib.sha256(body).hexdigest()
    n_lines = body.count(b"\n")
    with gzip.open(out, "wb", compresslevel=9) as fh:
        fh.write(body)
    log.info(
        "%s: %d bytes raw (%d lines) sha256=%s -> %s",
        _URL.format(year=year, market=market),
        len(body),
        n_lines,
        digest,
        out.name,
    )
    return out


def main() -> None:
    """CLI: mirror the requested (year, market) consolidations."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(TRAIN_YEARS))
    ap.add_argument("--markets", nargs="+", choices=MARKETS, default=list(MARKETS))
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
        for market in args.markets:
            fetch_year(year, market, force=args.force)


if __name__ == "__main__":
    main()
