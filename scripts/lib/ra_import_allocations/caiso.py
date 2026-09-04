"""CAISO RA-import-capability holdings: the annual "Holders of Import Capability" workbooks.

Source: CAISO Import Capability Allocation library pages
(``https://www.caiso.com/library/<year>-import-allocations``), document
``<year>-holders-of-import-capability.xlsx`` — the assigned RA import
capability by LSE and intertie branch group after every allocation step and
the registered bilateral transfers (posted 2025-04-11 for 2023 and 2024,
2024-08-23 for 2025). One sheet, columns::

    LSE | BRANCHGROUP | ALLOCATION (MW) | START_DT | END_DT

``START_DT`` / ``END_DT`` are Pacific wall-clock stamps, published as text
(``MM/DD/YYYY HH:MM:SS``) in the 2023 and 2025 workbooks and as Excel
datetimes in 2024; both are parsed. Every 2023–2025 row spans its whole RA
year (verified at intake: 0 partial-year rows), but the window is kept so a
future mid-year transfer is representable.

The companion workbooks in the same raw drop — "Import Capability Used on
Annual Resource Adequacy Plans" (May–Sep Yes/No flag per SCID or branch
group, ambiguous grain) and "Step 6 Contractual Data" (pre-RA / ETC / TOR
locks, a subset of the holdings) — are retained raw and NOT curated; see the
corpus README.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from . import CANONICAL_COLUMNS, IsoSpec, register

#: Raw drop under the shared raw root (immutable, never edited).
RAW_SUBDIR = Path("ra-import-allocations") / "CAISO"

#: ``<year>-holders-of-import-capability.xlsx``
_GLOB = "*-holders-of-import-capability.xlsx"
_YEAR_RE = re.compile(r"^(\d{4})-holders-of-import-capability\.xlsx$")

_SOURCE_URL = "https://www.caiso.com/documents/{name}"


def _files(raw_root: Path) -> list[Path]:
    """The holders workbooks present under the raw drop (sorted by year)."""
    return sorted(
        f for f in (raw_root / RAW_SUBDIR).glob(_GLOB) if _YEAR_RE.match(f.name)
    )


def years(raw_root: Path) -> list[int]:
    """RA years covered by the raw drop, parsed from the filenames."""
    return sorted(int(_YEAR_RE.match(f.name).group(1)) for f in _files(raw_root))


def _parse_file(path: Path) -> pd.DataFrame:
    """Parse one holders workbook into the canonical tidy frame."""
    year = _YEAR_RE.match(path.name).group(1)
    raw = pd.read_excel(path)
    raw.columns = [str(c).strip().upper() for c in raw.columns]
    out = pd.DataFrame(
        {
            "iso": "CAISO",
            "delivery_year": year,
            "lse": raw["LSE"].astype(str).str.strip(),
            "branch_group": raw["BRANCHGROUP"].astype(str).str.strip(),
            "allocation_mw": pd.to_numeric(raw["ALLOCATION"], errors="raise").astype(
                float
            ),
            # Text in 2023/2025 ("01/01/2023 00:00:00"), Excel datetimes in 2024.
            "start_date": pd.to_datetime(raw["START_DT"], format="mixed"),
            "end_date": pd.to_datetime(raw["END_DT"], format="mixed"),
            "source_doc": _SOURCE_URL.format(name=path.name),
        }
    )
    return out[list(CANONICAL_COLUMNS)]


def parse(raw_root: Path) -> pd.DataFrame:
    """Parse every holders workbook into the canonical tidy frame."""
    frames = [_parse_file(f) for f in _files(raw_root)]
    if not frames:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    return pd.concat(frames, ignore_index=True)


register(
    IsoSpec(
        iso="CAISO",
        parse=parse,
        years=years,
        source=(
            "CAISO Import Capability Allocation library, "
            "<year>-holders-of-import-capability.xlsx "
            "(https://www.caiso.com/library/<year>-import-allocations)"
        ),
    )
)
