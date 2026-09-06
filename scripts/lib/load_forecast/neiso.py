"""NEISO load-forecast spec — ISO-NE 2026 CELT Report (published 2026-05-01).

The CELT workbook is machine-readable, so NEISO is parsed natively and a vintage
refresh is *drop in the new workbook and re-run*. Three sheets are consumed:

* **1.5.2 Energy** — annual net and gross energy for load (GWh), the 2025 actual
  plus the 2026-2035 forecast, with ISO-NE's own printed 2026-2035 CAGRs.
* **1.5.1 Peak Loads** — annual net and gross **summer** and **winter** peak
  (MW) on the same span. Winter rows are published on a season pair
  ("2035/2036") but sit under the same year columns as the summer rows, so they
  are keyed on the FIRST year of the pair, matching the schema's convention.
* **1.7 Electrification Forecast** — annual energy (GWh), summer peak (MW) and
  winter peak (MW) for **Transportation** and **Heating** electrification, by
  state and New England total, 2026-2035. These are the anchors the
  ``ELECTRIFICATION_LAYERS`` heat-pump and EV layers need, and they are already
  **incremental** to the base year (ISO-NE forecasts the added adoption, which
  is why the 2026 column is small rather than the region's total EV/HP load).

ISO-NE publishes **one** forecast, so every row is ``scenario="mid"`` apart from
the 2025 actual column (``scenario="actual"``). Sheet **1.6 Forecast
Distributions** is deliberately **not parsed**: its P90...P10 band is a
*weather* distribution around one growth path, not a demand-scenario band, and
mapping it onto the model's low/mid/high axis would be the basis mismatch rule
14 ``[R-ACCURATE]`` warns about.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from . import IsoSpec, empty_frame, finalize, register
from ._xlsx import sheet_rows

CELT_WORKBOOK = "2026_celt.xlsx"

# The six New England states as sheet 1.7 labels them, plus its own total row.
STATES: tuple[str, ...] = (
    "Connecticut",
    "Massachusetts",
    "Maine",
    "New Hampshire",
    "Rhode Island",
    "Vermont",
)

# Sheet 1.7's category label -> the datatype's component vocabulary.
CATEGORY_TO_COMPONENT: dict[str, str] = {
    "Heating": "heat_pump",
    "Transportation": "ev",
}

_DOC = "ISO-NE 2026 CELT Report (data/raw/load-forecast/neiso/2026_celt.xlsx)"


# A header year cell: a bare four-digit year, or a season pair the CELT writes
# as "2035/2036" or "2035-36". A CAGR-window label like "2026 to 2035" must NOT
# match — it sits in the same header row and would collide with the 2026 column.
_YEAR_CELL = re.compile(r"^(\d{4})(?:\s*[/-]\s*\d{2,4})?$")


def _year_columns(rows: list[tuple], row_idx: int) -> list[tuple[int, int]]:
    """``(column_index, year)`` for every year cell in a header row.

    A season pair is keyed on its FIRST year, matching the schema's convention
    so a winter row and the summer row published beside it share one key.
    """
    out: list[tuple[int, int]] = []
    for i, c in enumerate(rows[row_idx]):
        if isinstance(c, (int, float)) and not isinstance(c, bool) and 1990 < c < 2100:
            out.append((i, int(c)))
        elif isinstance(c, str):
            m = _YEAR_CELL.match(c.strip())
            if m and 1990 < int(m.group(1)) < 2100:
                out.append((i, int(m.group(1))))
    return out


def _annual_rows(
    rows: list[tuple], label_contains: str, metric: str, unit: str, actual_year: int
) -> list[dict]:
    """Rows for one 'Gross'/'Net' pair sitting under an annual-forecast header."""
    out: list[dict] = []
    header = None
    for i, row in enumerate(rows):
        text = " ".join(str(c) for c in row if c is not None)
        if label_contains in text and _year_columns(rows, i):
            header = i
            break
    if header is None:
        return out
    years = _year_columns(rows, header)
    # Sheet 1.5.1 stacks the summer Gross/Net pair directly above the winter
    # one under a SINGLE year header, so stop after the first pair — otherwise
    # the winter rows would be emitted a second time under the summer metric.
    seen: set[str] = set()
    for row in rows[header + 1 : header + 8]:
        tag = next((str(c) for c in row[:3] if isinstance(c, str) and c.strip()), "")
        if tag.lower().startswith("gross"):
            basis = "gross"
        elif tag.lower().startswith("net"):
            basis = "net"
        else:
            continue
        if basis in seen:
            break
        seen.add(basis)
        for i, year in years:
            value = row[i] if i < len(row) else None
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            out.append(
                dict(
                    scenario="actual" if year == actual_year else "mid",
                    published_case="2026 CELT actual"
                    if year == actual_year
                    else "2026 CELT",
                    area="NEISO",
                    area_type="iso",
                    component="total",
                    metric=metric,
                    year=year,
                    value=round(float(value), 3),
                    unit=unit,
                    basis=basis,
                    source_doc=_DOC,
                    source_page=f"sheet 1.5.x, {tag.strip()} — {metric}",
                )
            )
    return out


def _electrification(rows: list[tuple]) -> list[dict]:
    """Sheet 1.7's three tables: annual energy, summer peak, winter peak."""
    tables = [
        ("Annual Energy", "energy_gwh", "gwh"),
        ("Summer Peak", "summer_peak_mw", "mw"),
        ("Winter Peak", "winter_peak_mw", "mw"),
    ]
    out: list[dict] = []
    for title, metric, unit in tables:
        start = None
        for i, row in enumerate(rows):
            text = " ".join(str(c) for c in row if c is not None)
            if title in text:
                start = i
                break
        if start is None:
            continue
        header = next(
            (
                i
                for i in range(start, min(start + 4, len(rows)))
                if _year_columns(rows, i)
            ),
            None,
        )
        if header is None:
            continue
        years = _year_columns(rows, header)
        component = None
        for row in rows[header + 1 : header + 20]:
            labels = [
                str(c).strip() for c in row[:3] if isinstance(c, str) and c.strip()
            ]
            if not labels:
                break
            category = next((l for l in labels if l in CATEGORY_TO_COMPONENT), None)
            if category:
                component = CATEGORY_TO_COMPONENT[category]
            if component is None:
                continue
            area = next((l for l in labels if l in STATES or l == "Total"), None)
            if area is None:
                continue
            for i, year in years:
                value = row[i] if i < len(row) else None
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    continue
                out.append(
                    dict(
                        scenario="mid",
                        published_case="2026 CELT",
                        area="NEISO" if area == "Total" else area,
                        area_type="iso" if area == "Total" else "state",
                        component=component,
                        metric=metric,
                        year=year,
                        value=round(float(value), 3),
                        unit=unit,
                        basis="net",
                        source_doc=_DOC,
                        source_page=f"sheet 1.7 Electrification Forecast, {title}",
                    )
                )
    return out


def parse(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Parse the CELT workbook's three consumed sheets into the canonical frame."""
    path = raw_dir / CELT_WORKBOOK
    if not path.is_file():
        return empty_frame()
    energy_rows = sheet_rows(path, "1.5.2 Energy")
    peak_rows = sheet_rows(path, "1.5.1 Peak Loads")
    records = (
        _annual_rows(
            energy_rows, "Annual net energy for load", "energy_gwh", "gwh", 2025
        )
        + _annual_rows(peak_rows, "Summer peak (MW)", "summer_peak_mw", "mw", 2025)
        + _winter(peak_rows)
        + _electrification(sheet_rows(path, "1.7 Electrification Forecast"))
    )
    if not records:
        return empty_frame()
    df = pd.DataFrame.from_records(records)
    df["iso"] = spec.iso
    df["edition"] = spec.edition
    df["vintage"] = spec.vintage
    return finalize(df)


def _winter(rows: list[tuple]) -> list[dict]:
    """Sheet 1.5.1's winter Gross/Net pair, which sits below the summer pair.

    The winter rows reuse the summer block's year columns, so the label row is
    located first and the pair beneath it read against the same header.
    """
    header = next(
        (
            i
            for i, r in enumerate(rows)
            if "Summer peak (MW)" in " ".join(str(c) for c in r if c is not None)
        ),
        None,
    )
    label = next(
        (
            i
            for i, r in enumerate(rows)
            if "Winter peak (MW)" in " ".join(str(c) for c in r if c is not None)
        ),
        None,
    )
    if header is None or label is None:
        return []
    years = _year_columns(rows, header)
    out: list[dict] = []
    for row in rows[label : label + 4]:
        tag = next((str(c) for c in row[:3] if isinstance(c, str) and c.strip()), "")
        if tag.lower().startswith("gross"):
            basis = "gross"
        elif tag.lower().startswith("net"):
            basis = "net"
        else:
            continue
        for i, year in years:
            value = row[i] if i < len(row) else None
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            out.append(
                dict(
                    scenario="actual" if year == 2025 else "mid",
                    published_case="2026 CELT actual" if year == 2025 else "2026 CELT",
                    area="NEISO",
                    area_type="iso",
                    component="total",
                    metric="winter_peak_mw",
                    year=year,
                    value=round(float(value), 3),
                    unit="mw",
                    basis=basis,
                    source_doc=_DOC,
                    source_page=f"sheet 1.5.1, {tag.strip()} — winter peak",
                )
            )
    return out


SPEC = register(
    IsoSpec(
        iso="NEISO",
        edition="CELT 2026",
        vintage=2026,
        default_basis="net",
        parse=parse,
    )
)
