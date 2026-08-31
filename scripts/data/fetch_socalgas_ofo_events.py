#!/usr/bin/env python3
"""Retrieve the SoCalGas Operational Flow Order event ledgers (CAISO).

Downloads the two public SoCalGas ENVOY event-history pages — the LOW OFO/EFO
ledger and the HIGH OFO ledger — and stores them **verbatim** under
``data/raw/gas-ofo-events/caiso/`` as immutable source snapshots, alongside a
``_snapshot.json`` recording each file's URL, retrieval timestamp, byte count
and SHA-256. Nothing is parsed here: the tidy frame is produced downstream by
``scripts/data/curate_gas_ofo_events.py``, which reads only these snapshots, so
curation never needs the network and every clean row traces to a hashed
document.

Both endpoints are public and unauthenticated; the pages carry the full
published span (low: 2015 onward; high: 1997 onward) in one response, so a
single GET per side retrieves everything — there is no date-range paging.

The endpoint list is NOT hardcoded here: it is read from the CAISO registry
spec in ``scripts/lib/gas_ofo_events/caiso.py``, so the fetcher and the parser
can never disagree about which file holds which ledger.

Usage:
    uv run python scripts/data/fetch_socalgas_ofo_events.py
    uv run python scripts/data/fetch_socalgas_ofo_events.py --out-dir /tmp/probe
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.lib import gas_ofo_events as ofo
from scripts.lib.clean_io import paths

ISO = "CAISO"

#: Read timeout (seconds) for one ENVOY page request.
REQUEST_TIMEOUT_S = 120

#: ENVOY serves the ledgers only to a browser-shaped request.
_USER_AGENT = "Mozilla/5.0 (compatible; market-sim data intake; +https://www.caiso.com)"

#: Smallest response we accept as a real ledger. The live pages are 130 KB
#: (low) and 440 KB (high); anything this small is an error page or a redirect
#: stub, and overwriting a good snapshot with one would be a silent data loss.
MIN_LEDGER_BYTES = 20_000


def _sha256(data: bytes) -> str:
    """Hex SHA-256 of a retrieved payload."""
    return hashlib.sha256(data).hexdigest()


def _get(url: str) -> bytes:
    """GET ``url`` and return its raw bytes, or raise with a readable message."""
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:
            return response.read()
    except (HTTPError, URLError) as exc:  # pragma: no cover - network path
        raise RuntimeError(f"fetch failed for {url}: {exc}") from exc


def fetch(out_dir: Path | None = None) -> list[Path]:
    """Download every CAISO OFO ledger snapshot; return the paths written.

    Parameters
    ----------
    out_dir:
        Destination directory (defaults to the registry's raw directory for
        CAISO under ``data/raw``); probes point it at a scratch dir.

    Returns
    -------
    list[Path]
        The snapshot files written, in registry order.
    """
    spec = ofo.load_registry()[ISO]
    target = (
        Path(out_dir)
        if out_dir is not None
        else ofo.raw_dir_for(spec.iso, paths.RAW_DIR)
    )
    target.mkdir(parents=True, exist_ok=True)

    retrieved = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    manifest: dict[str, dict] = {}
    written: list[Path] = []
    for source in spec.sources:
        payload = _get(source.url)
        if len(payload) < MIN_LEDGER_BYTES:
            raise RuntimeError(
                f"{source.url} returned only {len(payload)} bytes "
                f"(< {MIN_LEDGER_BYTES}); refusing to overwrite "
                f"{source.filename} with a probable error page"
            )
        path = target / source.filename
        path.write_bytes(payload)
        manifest[source.filename] = {
            "url": source.url,
            "utility": source.utility,
            "side": source.side,
            "retrieved_utc": retrieved,
            "bytes": len(payload),
            "sha256": _sha256(payload),
        }
        written.append(path)
        print(f"wrote {path}  ({len(payload):,} bytes)")

    (target / "_snapshot.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {target / '_snapshot.json'}")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default=None,
        help="destination directory (default: data/raw/gas-ofo-events/caiso)",
    )
    args = parser.parse_args(argv)
    written = fetch(out_dir=args.out_dir)
    print(f"\n{len(written)} snapshot(s) retrieved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
