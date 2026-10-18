"""Shared dispatcher for registry datatypes partitioned by ISO-local year.

``iso-area-load``, ``counterparty-interchange`` and ``iso-genmix`` (lane
UC-SPP-DATAFIX) share one curation shape: a registry package exposing
``DATATYPE``, ``load_registry``, ``raw_dir_for`` and ``parse_iso`` returning
``{local year: tidy frame}``. This writes each partition through
:func:`scripts.lib.clean_io.write_clean` and round-trips it with
:func:`~scripts.lib.clean_io.validate_clean`.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

from scripts.lib import clean_io
from scripts.lib.clean_io import paths


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def curate_registry(
    lib: ModuleType, raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Write every requested ISO's local-year partitions of ``lib.DATATYPE``.

    ``raw_root`` defaults to ``paths.RAW_DIR`` (tests point it at a fixture);
    ``isos`` defaults to every registered ISO. An ISO whose parser yields no
    rows is skipped. Returns the paths written.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = lib.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)
    written: list[Path] = []
    for iso in wanted:
        source = _rel(lib.raw_dir_for(iso, raw_root))
        parts = lib.parse_iso(iso, raw_root)
        if not parts:
            print(f"[skip] {iso}: no raw rows under {source}")
            continue
        for year, df in sorted(parts.items()):
            path = clean_io.write_clean(
                df, lib.DATATYPE, iso=iso, year=year, source=source
            )
            clean_io.validate_clean(path)
            written.append(path)
            print(f"wrote {path}  ({len(df)} rows)")
    return written
