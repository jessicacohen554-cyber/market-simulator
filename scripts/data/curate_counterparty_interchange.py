"""Curate the ``counterparty-interchange`` clean datatype.

Every measured leg of an ISO BA's interchange from both reporting sides (SPP first;
lane UC-SPP-DATAFIX, owner ruling R22), reconciled onto
``data/dictionary/schema/counterparty-interchange.schema.yaml`` and written through
:func:`scripts.lib.clean_io.write_clean`, one partition per ISO and local
year. Per-ISO parsing lives in ``scripts/lib/counterparty_interchange/<iso>.py``; this
script is a thin dispatcher over the registry. Reads only ``data/raw``;
idempotent. Run ``python scripts/data/curate_counterparty_interchange.py [--isos SPP]``.
"""

from __future__ import annotations

from scripts.lib import counterparty_interchange as lib
import argparse

from scripts.lib.curate_local_year import curate_registry

DATATYPE = lib.DATATYPE


def curate(raw_root=None, isos=None):
    """Curate and write every requested ISO's local-year partitions; return the paths."""
    return curate_registry(lib, raw_root=raw_root, isos=isos)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos", nargs="*", default=None, help="subset of ISOs (default: all)"
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
