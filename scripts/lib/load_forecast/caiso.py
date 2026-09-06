"""CAISO load-forecast spec — CEC California Energy Demand 2025-2045 (2025 IEPR).

The CEC's forms are machine-readable, so CAISO is parsed natively. Four forms
are consumed, across the statewide workbook and the three CAISO-footprint
planning-area workbooks:

* **Form 1.2** — Total Energy to Serve Load (GWh), 2000-2045(-2050).
* **Form 1.5** — Historical and Extreme Temperature Non-coincident Peak Demand
  (MW): the historical column (``scenario="actual"``) and the
  ``Forecasted_1.in.2_Peak`` planning column (``scenario="mid"``).
* **Form 1.1c** — Electricity Deliveries to End Users by Agency (GWh),
  **Data Centers Only**, in the CEC's TWO published data-centre scenarios: the
  *Planning Forecast* allocation (adopted central case -> ``scenario="mid"``)
  and the *Local Reliability Scenario* allocation (materially higher, the case
  CPUC resource-adequacy and CAISO local studies use -> ``scenario="high"``).
  This pair is what closes the ``DATACENTER_ADDITIONS_MW["CAISO"]``
  ``high := mid`` limitation the D-4 gap list records.

**Footprint caveat, carried in the data rather than hidden.** The CEC publishes
by *planning area*, and the CAISO balancing authority is approximately
``PGE + SCE + SDGE`` — LADWP, IID, SMUD, BUG and NCNC are outside it. All four
areas are curated (the three CAISO planning areas plus the statewide row) and
the consumer sums the three; the misalignment is rule 14 ``[R-ACCURATE]``'s
named exception (published on a different boundary than the model's), and Form
1.5 peaks are **non-coincident**, so their sum slightly exceeds a coincident
CAISO peak.

**Not published:** a low/mid/high demand-growth band. The CED's scenario axis is
over load *modifiers* (AAEE/AAFS/AATE, BTM PV and storage, known loads), not
over economic growth, so no growth band is invented here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import IsoSpec, empty_frame, finalize, register
from ._xlsx import header_index, numeric_records, sheet_rows

# CEC planning-area workbook -> the area label carried in the frame. The three
# CAISO-footprint areas plus the statewide row (kept for context, never summed
# into the CAISO total).
AREA_WORKBOOKS: dict[str, str] = {
    "CED2025-Baseline-PGE.xlsx": "PGE",
    "CED2025-Baseline-SCE.xlsx": "SCE",
    "CED2025-Baseline-SDGE.xlsx": "SDGE",
    "CED2025-Baseline-TotalState.xlsx": "Total State",
}

# The CEC planning areas whose sum approximates the CAISO balancing authority.
CAISO_PLANNING_AREAS: tuple[str, ...] = ("PGE", "SCE", "SDGE")

DATACENTER_WORKBOOK = "CED2025-Form-1-1c-DataCenters.xlsx"

# Form 1.1c sheet -> (published case label, canonical scenario).
DATACENTER_SHEETS: dict[str, tuple[str, str]] = {
    "Form 1.1c DC Planning": ("Planning Forecast", "mid"),
    "Form 1.1c DC Local Reliability": ("Local Reliability Scenario", "high"),
}

_DOC = (
    "CEC California Energy Demand 2025-2045 (2025 IEPR), data/raw/load-forecast/caiso/"
)


def _energy_and_peak(raw_dir: Path) -> list[dict]:
    """Form 1.2 energy and Form 1.5 peak, per CEC planning area."""
    out: list[dict] = []
    for filename, area in AREA_WORKBOOKS.items():
        path = raw_dir / filename
        if not path.is_file():
            continue
        rows = sheet_rows(path, "Form 1.2")
        hdr = header_index(rows, "Year", "Total_Energy_to_Serve_Load")
        for year, vals in numeric_records(rows, hdr):
            value = vals.get("Total_Energy_to_Serve_Load")
            if value is None:
                continue
            out.append(
                dict(
                    scenario="mid",
                    published_case="CED 2025 Baseline 'Mid' Forecast",
                    area=area,
                    area_type="planning_area",
                    component="total",
                    metric="energy_gwh",
                    year=year,
                    value=round(value, 3),
                    unit="gwh",
                    basis="net",
                    source_doc=_DOC + filename,
                    source_page="Form 1.2 Total Energy to Serve Load (GWh)",
                )
            )
        try:
            peak_rows = sheet_rows(path, "Form 1.5")
        except KeyError:
            continue  # the statewide workbook carries no peak form
        hdr = header_index(peak_rows, "Year", "Forecasted_1.in.2_Peak")
        for year, vals in numeric_records(peak_rows, hdr):
            for label, scenario, case in (
                ("Historical_Net_Peak", "actual", "CED 2025 historical"),
                ("Forecasted_1.in.2_Peak", "mid", "CED 2025 Baseline 1-in-2"),
            ):
                value = vals.get(label)
                if value is None:
                    continue
                out.append(
                    dict(
                        scenario=scenario,
                        published_case=case,
                        area=area,
                        area_type="planning_area",
                        component="total",
                        metric="annual_peak_mw",
                        year=year,
                        value=round(value, 3),
                        unit="mw",
                        basis="net",
                        source_doc=_DOC + filename,
                        source_page=f"Form 1.5 {label} (non-coincident)",
                    )
                )
    return out


# Form 1.1c publishes a "<AREA> Total" row at the end of each planning area's
# agency block. Those published totals are what is emitted (the agency rows are
# summed only to VALIDATE them), normalized onto the same area labels Forms 1.2
# and 1.5 use so the three forms join.
_DC_AREA_LABELS: dict[str, str] = {
    "PG&E Total": "PGE",
    "SCE Total": "SCE",
    "SDG&E Total": "SDGE",
    "STATEWIDE Total": "Total State",
}


def _norm(label: object) -> str:
    """Collapse a Form 1.1c label's embedded newlines and padding."""
    return " ".join(str(label).split())


def _datacenters(raw_dir: Path) -> list[dict]:
    """Form 1.1c data-centre deliveries: the published planning-area totals.

    Emits the workbook's own ``"<AREA> Total"`` rows and asserts each equals the
    sum of that area's agency rows, so a layout change is caught rather than
    silently mis-aggregated.
    """
    path = raw_dir / DATACENTER_WORKBOOK
    if not path.is_file():
        return []
    out: list[dict] = []
    for sheet, (case, scenario) in DATACENTER_SHEETS.items():
        rows = sheet_rows(path, sheet)
        hdr = header_index(rows, "Planning Area", "Agency")
        years = [
            (i, int(c))
            for i, c in enumerate(rows[hdr])
            if isinstance(c, (int, float)) and not isinstance(c, bool)
        ]
        current: str | None = None
        running: dict[int, float] = {}
        for row in rows[hdr + 1 :]:
            label = _norm(row[0]) if row and row[0] is not None else ""
            values = {
                year: float(row[i])
                for i, year in years
                if i < len(row)
                and isinstance(row[i], (int, float))
                and not isinstance(row[i], bool)
            }
            if label in _DC_AREA_LABELS:
                area = _DC_AREA_LABELS[label]
                if current is not None and area != "Total State":
                    for year, total in values.items():
                        got = running.get(year, 0.0)
                        if abs(got - total) > max(1.0, 1e-6 * abs(total)):
                            raise ValueError(
                                f"{sheet}: {label} {year} published {total} but its "
                                f"agency rows sum to {got}"
                            )
                for year, total in values.items():
                    out.append(
                        dict(
                            scenario=scenario,
                            published_case=case,
                            area=area,
                            area_type="planning_area",
                            component="data_center",
                            metric="energy_gwh",
                            year=year,
                            value=round(total, 3),
                            unit="gwh",
                            basis="net",
                            source_doc=_DOC + DATACENTER_WORKBOOK,
                            source_page=f"{sheet}, published {label} row",
                        )
                    )
                running = {}
                current = None
                continue
            if label and not label.endswith("Total"):
                current = label  # a new planning area's first agency row
                running = {}
            if current is not None:
                for year, value in values.items():
                    running[year] = running.get(year, 0.0) + value
    return out


def parse(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Parse the CEC CED 2025 forms into the canonical tidy frame."""
    records = _energy_and_peak(raw_dir) + _datacenters(raw_dir)
    if not records:
        return empty_frame()
    df = pd.DataFrame.from_records(records)
    df["iso"] = spec.iso
    df["edition"] = spec.edition
    df["vintage"] = spec.vintage
    return finalize(df)


SPEC = register(
    IsoSpec(
        iso="CAISO",
        edition="CED 2025-2045",
        vintage=2026,
        default_basis="net",
        parse=parse,
    )
)
