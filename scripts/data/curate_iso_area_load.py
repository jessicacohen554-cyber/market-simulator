"""Curate the ``iso-area-load`` clean datatype.

An ISO's own published hourly metered load by area (SPP HOURLY_LOAD first;
lane UC-SPP-DATAFIX, owner ruling R22), reconciled onto
``data/dictionary/schema/iso-area-load.schema.yaml`` and written through
:func:`scripts.lib.clean_io.write_clean`, one partition per ISO and local
year. Per-ISO parsing lives in ``scripts/lib/iso_area_load/<iso>.py``; this
script is a thin dispatcher over the registry. Reads only ``data/raw``;
idempotent. Run ``python scripts/data/curate_iso_area_load.py [--isos SPP]``.
"""

from __future__ import annotations

from scripts.lib import iso_area_load as lib
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
