"""ERCOT load-forecast spec — 2025 Long-Term Load Forecast (posted 2025-04-08).

ERCOT is the one publisher whose sources use **both** intake routes:

* **Native** — ``2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx``
  (monthly peak MW and monthly energy MWh, 2025-2044, side by side for both
  published cases) and ``Summer-and-Winter-Peaks.xlsx`` (net coincident summer
  and winter peak MW **by weather zone**, 2025-2031, for both cases).
* **Transcription** — ``ercot.csv``, holding the two quantities that live only
  in the 48.4 MB ``ErcotAdjustedForecast.xlsb`` hourly workbook (a gitignored
  corpus payload): annual per-weather-zone large-load peak MW
  (``<zone>_contracts + <zone>_officer_letters``) and annual per-zone EV energy
  (``<zone>_ev``). The package's default CSV reader picks those up; nothing here
  needs an ``.xlsb`` parser.

**Two published cases, and they are NOT a low/mid/high band.** *ERCOT Adjusted*
is ERCOT's own vetted/derated forecast, mapped to ``scenario="mid"``; *TSP
Provided* is the un-derated forecast as the transmission service providers
reported it, mapped to ``scenario="high"`` because it is a genuine published
upper case. ERCOT publishes **no low case**, and none is invented here.

``ERCOT-Peak-Demand-Scenarios.xlsx`` is held in the raw directory as provenance
but is deliberately **not parsed**: it is the same peak forecast re-run over
thirteen historical **weather** years, i.e. a weather distribution around one
growth path, which is not the model's low/mid/high growth axis (using it as one
would be the basis mismatch rule 14 ``[R-ACCURATE]`` warns about).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import IsoSpec, empty_frame, finalize, register
from ._xlsx import sheet_rows

MONTHLY_WORKBOOK = "2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx"
ZONE_PEAK_WORKBOOK = "Summer-and-Winter-Peaks.xlsx"

# ERCOT's eight weather zones as the LTLF workbooks label them. The
# weather-zone -> model-transmission-zone crosswalk is the consumer's
# (config/iso_configs.py), never this datatype's.
WEATHER_ZONES: tuple[str, ...] = (
    "COAST",
    "EAST",
    "FWEST",
    "NCENT",
    "NORTH",
    "SCENT",
    "SOUTH",
    "WEST",
)

# The publisher's own case label -> the model's canonical scenario axis.
CASE_TO_SCENARIO: dict[str, str] = {
    "ERCOT Adjusted": "mid",
    "TSP Provided": "high",
}

_DOC_MONTHLY = (
    "ERCOT 2025 Long-Term Load Forecast, Monthly Peak Demand and Energy Forecast "
    "(data/raw/load-forecast/ercot/"
    "2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx)"
)
_DOC_ZONES = (
    "ERCOT 2025 Long-Term Load Forecast, Summer and Winter Peaks "
    "(data/raw/load-forecast/ercot/Summer-and-Winter-Peaks.xlsx)"
)


def _monthly(raw_dir: Path, spec: IsoSpec) -> list[dict]:
    """Annual energy + annual peak for both published cases, 2025-2044.

    The sheet lays the two cases side by side: columns 0-3 are the ERCOT
    Adjusted forecast (year, month, monthly peak MW, monthly energy MWh) and
    columns 5-8 the TSP Provided one. Energy is summed and peak maxed over each
    year's months.
    """
    path = raw_dir / MONTHLY_WORKBOOK
    if not path.is_file():
        return []
    blocks = {"ERCOT Adjusted": (0, 2, 3), "TSP Provided": (5, 7, 8)}
    out: list[dict] = []
    rows = sheet_rows(path, "Sheet1")
    for case, (ycol, pcol, ecol) in blocks.items():
        energy: dict[int, float] = {}
        peak: dict[int, float] = {}
        for row in rows:
            if ycol >= len(row) or pcol >= len(row):
                continue
            y, p = row[ycol], row[pcol]
            if not isinstance(y, (int, float)) or isinstance(y, bool):
                continue
            if not isinstance(p, (int, float)) or isinstance(p, bool):
                continue
            year = int(y)
            peak[year] = max(peak.get(year, 0.0), float(p))
            e = row[ecol] if ecol < len(row) else None
            if isinstance(e, (int, float)) and not isinstance(e, bool):
                energy[year] = energy.get(year, 0.0) + float(e)
        for year in sorted(peak):
            out.append(
                dict(
                    scenario=CASE_TO_SCENARIO[case],
                    published_case=case,
                    area="ERCOT",
                    area_type="iso",
                    component="total",
                    metric="annual_peak_mw",
                    year=year,
                    value=round(peak[year], 3),
                    unit="mw",
                    source_doc=_DOC_MONTHLY,
                    source_page=f"Sheet1, {case} monthly peaks (annual max)",
                )
            )
            if year in energy:
                out.append(
                    dict(
                        scenario=CASE_TO_SCENARIO[case],
                        published_case=case,
                        area="ERCOT",
                        area_type="iso",
                        component="total",
                        metric="energy_gwh",
                        year=year,
                        # The workbook's "Annual Energy" column is MONTHLY energy
                        # in MWh (its 2025 rows sum to ERCOT's ~486 TWh year);
                        # summed over months and converted to GWh here.
                        value=round(energy[year] / 1000.0, 3),
                        unit="gwh",
                        source_doc=_DOC_MONTHLY,
                        source_page=f"Sheet1, {case} monthly energy MWh (annual sum)",
                    )
                )
    return out


def _zone_peaks(raw_dir: Path, spec: IsoSpec) -> list[dict]:
    """Per-weather-zone net coincident summer and winter peaks, both cases."""
    path = raw_dir / ZONE_PEAK_WORKBOOK
    if not path.is_file():
        return []
    out: list[dict] = []
    for sheet, metric in (("Summer", "summer_peak_mw"), ("Winter", "winter_peak_mw")):
        rows = sheet_rows(path, sheet)
        case = None
        cols: dict[str, int] = {}
        for row in rows:
            head = str(row[0]).strip() if row and row[0] is not None else ""
            if "Forecast" in head and ("TSP" in head or "Adjusted" in head):
                case = "TSP Provided" if "TSP" in head else "ERCOT Adjusted"
                cols = {}
                continue
            labels = [str(c).strip().upper() if c is not None else "" for c in row]
            if "ERCOT" in labels and any(z in labels for z in WEATHER_ZONES):
                cols = {lab: i for i, lab in enumerate(labels) if lab}
                continue
            if case is None or not cols or row[0] is None:
                continue
            # Summer rows key on a plain year; winter rows on a "2025-2026" pair,
            # keyed here on the FIRST year so the two seasons share one key.
            label = str(row[0]).strip()
            year_txt = label.split("-")[0]
            if not year_txt.isdigit():
                continue
            year = int(year_txt)
            for area, i in cols.items():
                value = row[i] if i < len(row) else None
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    continue
                out.append(
                    dict(
                        scenario=CASE_TO_SCENARIO[case],
                        published_case=case,
                        area=area,
                        area_type="iso" if area == "ERCOT" else "source_zone",
                        component="total",
                        metric=metric,
                        year=year,
                        value=round(float(value), 3),
                        unit="mw",
                        source_doc=_DOC_ZONES,
                        source_page=f"sheet {sheet}, {case} net coincident peak",
                    )
                )
    return out


def parse(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Parse ERCOT's two published workbooks into the canonical tidy frame."""
    records = _monthly(raw_dir, spec) + _zone_peaks(raw_dir, spec)
    if not records:
        return empty_frame()
    df = pd.DataFrame.from_records(records)
    df["iso"] = spec.iso
    df["edition"] = spec.edition
    df["vintage"] = spec.vintage
    df["basis"] = spec.default_basis
    return finalize(df)


SPEC = register(
    IsoSpec(
        iso="ERCOT",
        edition="2025 LTLF",
        vintage=2025,
        default_basis="net",
        parse=parse,
    )
)
