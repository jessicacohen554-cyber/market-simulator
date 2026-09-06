"""Content-addressed parquet mirror for eGRID workbook sheets.

The eGRID workbook is a 21 MB xlsx and openpyxl's read-only parser costs
~10 us per cell, so every ``pd.read_excel`` against it is a multi-second,
CPU-bound parse *on the solve path* — paid afresh in every process, for
sheet values that never change. :func:`read_egrid_sheet` keeps that parse but
pays it **once per workbook content**, mirroring the resulting frame to a
parquet file next to the workbook and serving every later call from the
mirror.

Design points, in the order they matter:

* **Content-addressed, hence self-invalidating.** The mirror file name carries
  a sha256 digest over the workbook's bytes together with the read parameters
  (sheet, ``skiprows``, requested columns). A re-released or repaired workbook
  hashes differently, so its mirrors simply do not exist yet and are rebuilt;
  a stale mirror can never be served for changed source bytes. Nothing needs to
  be invalidated by hand and there is no configuration flag.
* **The read parameters are in the digest, not just the sheet.** The two
  ``PLNT23`` call sites on the solve path ask for *different* column sets, and
  ``pd.read_excel`` returns columns in **sheet** order rather than in the order
  the caller listed them. Mirroring the exact frame each call site receives —
  rather than a single wide per-sheet mirror that callers then subset — is what
  makes the mirror read equal to the xlsx read by construction, column order
  and dtypes included, which is precisely what the landing gate asserts.
* **Parquet, never pickle.** The mirror is a pyarrow parquet file; no
  ``allow_pickle`` path, no executable payload, nothing that could deserialize
  into code.
* **Advisory, never authoritative.** Any failure anywhere in the mirror path —
  unhashable workbook, unwritable directory, corrupt or truncated parquet — is
  logged and falls back to ``pd.read_excel``. The mirror is a cache, so a
  degraded cache costs wall-clock and nothing else.

Wall-clock only: this module changes no value the LP ever sees.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Sequence

import pandas as pd

logger = logging.getLogger(__name__)

# Every eGRID sheet opens with a row of long descriptive headers above the
# short-code header row (ORISPL, LAT, LON, ...) that callers key on, so every
# read on the solve path skips exactly one row. Folded into the mirror digest
# so a future caller reading a sheet differently cannot collide with these.
_SKIPROWS: int = 1

# Bytes per chunk when digesting the workbook. 1 MiB keeps the 21 MB hash off
# the peak-RSS ledger entirely (rule 12's concurrency cap is memory-bound).
_HASH_CHUNK_BYTES: int = 1 << 20

# Characters of the hex digest kept in the mirror file name. 16 hex chars is
# 64 bits — collision-free for the handful of (workbook, sheet, usecols)
# combinations that exist, and short enough to keep the name readable.
_DIGEST_CHARS: int = 16


def _workbook_digest(path: Path, sheet: str, usecols: Sequence[str]) -> str:
    """Return the short hex digest identifying one (workbook, read) pair.

    Hashes the workbook's bytes followed by the read parameters, so the digest
    changes when *either* the source data or the requested projection changes.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_HASH_CHUNK_BYTES), b""):
            digest.update(chunk)
    # Length-prefixed so no two parameter tuples can serialize identically.
    for part in (sheet, str(_SKIPROWS), *usecols):
        digest.update(f"{len(part)}:{part}".encode())
    return digest.hexdigest()[:_DIGEST_CHARS]


def _mirror_path(path: Path, sheet: str, usecols: Sequence[str]) -> Path:
    """Return the parquet mirror path for one eGRID sheet read.

    ``<xlsx-stem>.<digest>.<sheet>.parquet``, alongside the workbook (the
    pattern ``.gitignore`` excludes, so a mirror is never committed).
    """
    return path.with_name(
        f"{path.stem}.{_workbook_digest(path, sheet, usecols)}.{sheet}.parquet"
    )


def _write_mirror(frame: pd.DataFrame, mirror: Path) -> None:
    """Write ``frame`` to ``mirror`` atomically; log and give up on failure.

    Written to a process-unique temporary name in the same directory and then
    ``os.replace``d into place, so a concurrent reader (rule 12 permits two
    simultaneous invocations) sees either no mirror or a complete one — never a
    half-written parquet.
    """
    tmp = mirror.with_name(f"{mirror.name}.{os.getpid()}.tmp")
    try:
        frame.to_parquet(tmp, index=False)
        os.replace(tmp, mirror)
    except (OSError, ValueError, ImportError) as exc:
        logger.warning("eGRID mirror write failed (%s): %s", mirror.name, exc)
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def read_egrid_sheet(path: Path, sheet: str, usecols: Sequence[str]) -> pd.DataFrame:
    """Read one eGRID sheet, via its parquet mirror when one is available.

    Equivalent in every observable way to::

        pd.read_excel(path, sheet_name=sheet, skiprows=1, usecols=usecols)

    including the resulting column order (eGRID **sheet** order, which is not
    generally the order ``usecols`` lists) and dtypes. On a mirror miss the
    workbook is parsed exactly as before and the frame is mirrored for the next
    process; on any mirror error the workbook parse is the answer.

    Args:
        path: The eGRID workbook (``.xlsx``).
        sheet: Sheet name, e.g. ``"PLNT23"`` or ``"UNT23"``.
        usecols: eGRID short-code column names to read.

    Returns:
        The requested sheet columns as a DataFrame.
    """
    cols = list(usecols)
    mirror: Path | None
    try:
        mirror = _mirror_path(path, sheet, cols)
    except OSError as exc:  # unreadable workbook — let read_excel report it
        logger.warning("eGRID mirror digest failed (%s): %s", path.name, exc)
        mirror = None

    if mirror is not None and mirror.exists():
        try:
            return pd.read_parquet(mirror)
        except Exception as exc:  # noqa: BLE001 - any unreadable mirror re-parses
            # Deliberately broad: a corrupt, truncated or pyarrow-version-shifted
            # mirror must degrade to the workbook rather than fail the solve.
            logger.warning("eGRID mirror read failed (%s): %s", mirror.name, exc)

    frame = pd.read_excel(path, sheet_name=sheet, skiprows=_SKIPROWS, usecols=cols)
    if mirror is not None:
        _write_mirror(frame, mirror)
    return frame
