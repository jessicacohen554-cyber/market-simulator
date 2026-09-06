"""PJM load-forecast spec — 2026 Load Forecast Report (posted 2026-01-14).

Both sources are machine-readable workbooks, so PJM is parsed natively and a
vintage refresh is *drop in the new workbooks and re-run*:

* ``2026-load-report-data.xlsx`` — monthly ``PEAK_MW`` + ``ENERGY_GWH`` per PJM
  zone and for ``PJM_RTO``, 2026-2046. Annualized here: energy is the sum over
  the year's months, peak the max over them (PJM's annual peak is a summer peak
  in every year of the series).
* ``total-load-adjustments-breakdown.xlsx`` — **Table B-9b**, *"Total
  Adjustments to Summer Peak Load (MW) for Each PJM Zone and RTO (2026-2046)"*.
  This is the table the D-4 gap list records as never read
  (``docs/handoffs/FINDING-scn-ws4a-2026-09-05.md`` §4, G-D4-3). Per the
  report's own "Load Adjustments" section every adjusted zone is adjusted for
  *growth in data center load*, with DOM additionally carrying a
  voltage-optimization program, PS additionally port electrification, and EKPC a
  peak-shaving program — so the rows are carried as ``large_load``, and the
  data-centre share of them stays the consumer's declared assumption.

PJM publishes ONE forecast, so every row is ``scenario="mid"``; no band is
invented.

Zone labels are PJM's own (``AEP``, ``COMED``, ``DOM``, ...). Table B-9b also
carries sub-area rows (``AEP``/``AEPOHIO``, ``DOM``/``NVEC``, ...) which are a
decomposition of their parent zone; only the **parent-zone** rows are taken, so
the frame never double-counts, and ``PJM RTO`` is carried as the ``iso`` row.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import IsoSpec, empty_frame, finalize, register
from ._xlsx import header_index, numeric_records, sheet_rows

DATA_WORKBOOK = "2026-load-report-data.xlsx"
ADJUSTMENTS_WORKBOOK = "total-load-adjustments-breakdown.xlsx"

# Sheets in the data workbook that are NOT PJM zones: the RTO/sub-RTO
# aggregates and the four Massachusetts sub-areas PJM reports for a neighbour.
_AGGREGATE_SHEETS = {"PJM_RTO", "PJM_WEST", "PJM_MA"}
_NON_PJM_SHEETS = {"CENTRALMA", "WESTERNMA", "EASTERNMA", "SOUTHERNMA"}

_DOC_DATA = (
    "PJM 2026 Load Forecast Report data workbook "
    "(data/raw/load-forecast/pjm/2026-load-report-data.xlsx)"
)
_DOC_ADJ = (
    "PJM 2026 Load Forecast Report, Table B-9b "
    "(data/raw/load-forecast/pjm/total-load-adjustments-breakdown.xlsx)"
)


def _zone_series(raw_dir: Path, spec: IsoSpec) -> list[dict]:
    """Annual energy and peak per PJM zone from the load-report data workbook."""
    path = raw_dir / DATA_WORKBOOK
    if not path.is_file():
        return []
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out: list[dict] = []
    try:
        for sheet in wb.sheetnames:
            if sheet in _NON_PJM_SHEETS:
                continue
            is_iso = sheet == "PJM_RTO"
            if sheet in _AGGREGATE_SHEETS and not is_iso:
                continue
            energy: dict[int, float] = {}
            peak: dict[int, float] = {}
            for row in wb[sheet].iter_rows(min_row=2, values_only=True):
                if row[0] is None:
                    break
                year = int(row[1])
                peak[year] = max(peak.get(year, 0.0), float(row[3] or 0.0))
                energy[year] = energy.get(year, 0.0) + float(row[4] or 0.0)
            for year in sorted(energy):
                for metric, unit, value in (
                    ("energy_gwh", "gwh", energy[year]),
                    ("annual_peak_mw", "mw", peak[year]),
                ):
                    out.append(
                        dict(
                            area="PJM" if is_iso else sheet,
                            area_type="iso" if is_iso else "source_zone",
                            component="total",
                            metric=metric,
                            year=year,
                            value=round(value, 3),
                            unit=unit,
                            published_case="2026 Load Forecast",
                            source_doc=_DOC_DATA,
                            source_page=f"sheet {sheet} (monthly PEAK_MW / ENERGY_GWH, annualized)",
                        )
                    )
    finally:
        wb.close()
    return out


def _large_load(raw_dir: Path, spec: IsoSpec) -> list[dict]:
    """Table B-9b: summer-peak load adjustments per zone, 2026-2046."""
    path = raw_dir / ADJUSTMENTS_WORKBOOK
    if not path.is_file():
        return []
    rows = sheet_rows(path, "Total LargeLoad Breakdown")
    hdr = header_index(rows, "ZONENAME", "AREANAME")
    years = [
        (i, int(c))
        for i, c in enumerate(rows[hdr])
        if isinstance(c, (int, float)) and not isinstance(c, bool)
    ]
    out: list[dict] = []
    for row in rows[hdr + 1 :]:
        label = row[0]
        if not isinstance(label, str) or not label.strip():
            continue  # sub-area rows carry a blank first cell — the parent's decomposition
        zone = label.strip()
        is_iso = zone.upper().replace(" ", "_") in {"PJM_RTO", "PJMRTO"}
        for i, year in years:
            value = row[i] if i < len(row) else None
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            out.append(
                dict(
                    area="PJM" if is_iso else zone,
                    area_type="iso" if is_iso else "source_zone",
                    component="large_load",
                    metric="summer_peak_mw",
                    year=year,
                    value=round(float(value), 3),
                    unit="mw",
                    published_case="2026 Load Forecast",
                    source_doc=_DOC_ADJ,
                    source_page="Table B-9b (Total Adjustments to Summer Peak Load, MW)",
                )
            )
    return out


def parse(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Parse PJM's two published workbooks into the canonical tidy frame."""
    records = _zone_series(raw_dir, spec) + _large_load(raw_dir, spec)
    if not records:
        return empty_frame()
    df = pd.DataFrame.from_records(records)
    df["iso"] = spec.iso
    df["edition"] = spec.edition
    df["vintage"] = spec.vintage
    df["scenario"] = "mid"
    df["basis"] = spec.default_basis
    return finalize(df)


SPEC = register(
    IsoSpec(
        iso="PJM",
        edition="2026 LTLF",
        vintage=2026,
        default_basis="net",
        parse=parse,
    )
)
