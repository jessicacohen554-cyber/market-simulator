"""AEO2025 source for the ``benchmark-corridor`` datatype (the one fetchable one).

EIA Annual Energy Outlook 2025 regional electricity projections — capacity mix,
generation (energy) mix, and power-sector CO2 by Electricity Market Module (EMM)
region — pulled from the EIA Open Data API v2 ``aeo`` route (the same route the
fuel-price fetch ``scripts/data/fetch_eia_aeo.py`` already uses), NOT a table-browser
scrape. Two tables carry everything FC-5 needs:

  * **Table 54 — Electric Power Projections by Electricity Market Module Region**
    (API ``tableId=62``): capacity and generation by fuel and power-sector CO2.
  * **Table 56 — Renewable Energy Generation by Fuel** (API ``tableId=67``): the
    renewable *capacity* split (solar / wind / offshore wind / geothermal /
    hydro / biomass / municipal waste) the aggregate "Renewable Sources" line in
    Table 54 lacks.

Every value is read verbatim from the API (rule 5); the parser maps the AEO
series **name** (stable across editions) to the canonical (quantity, tech) and
asserts the API's native unit, so a silent AEO unit/label change fails loud.

EMM region → ISO is a documented crosswalk (:data:`AEO_EMM_TO_ISO`). AEO's EMM
regions approximate but do NOT exactly equal the ISO footprints; that boundary
caveat rides in every row's ``note`` (rule 11 — real data, misalignment stated,
never a guessed ISO-exact number). An ISO total is the sum over its region rows.

Raw fetch (immutable) lands at
``data/raw/benchmark-corridor/aeo2025/aeo2025_electricity_corridor.csv``.
Re-fetch with ``python scripts/data/fetch_aeo_electricity.py``.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from scripts.lib import benchmark_corridor as bc
from scripts.lib.clean_io import paths
from scripts.lib.env_keys import get_api_key

SOURCE = "AEO2025"
RAW_SUBDIR = "aeo2025"
RAW_FILENAME = "aeo2025_electricity_corridor.csv"
VINTAGE = "2025-04"  # AEO2025 released April 2025.
API_BASE = "https://api.eia.gov/v2/aeo"
_DEMO_KEY = "DEMO_KEY"

# EMM region id (API regionId) -> ISO the region crosswalks onto, with the
# region's published name. Multi-region ISOs (PJM/MISO/NYISO/CAISO) sum over
# their region rows. AEO EMM footprints ~ ISO footprints (see module note).
AEO_EMM_TO_ISO: dict[str, tuple[str, str]] = {
    "5-1": ("ERCOT", "Texas Reliability Entity"),
    "5-7": ("NEISO", "Northeast Power Coordinating Council / New England"),
    "5-8": (
        "NYISO",
        "Northeast Power Coordinating Council / New York City and Long Island",
    ),
    "5-9": ("NYISO", "Northeast Power Coordinating Council / Upstate New York"),
    "5-10": ("PJM", "PJM / East"),
    "5-11": ("PJM", "PJM / West"),
    "5-12": ("PJM", "PJM / Commonwealth Edison"),
    "5-13": ("PJM", "PJM / Dominion"),
    "5-3": ("MISO", "Midcontinent / West"),
    "5-4": ("MISO", "Midcontinent / Central"),
    "5-5": ("MISO", "Midcontinent / East"),
    "5-6": ("MISO", "Midcontinent / South"),
    "5-21": ("CAISO", "Western Electricity Coordinating Council / California North"),
    "5-22": ("CAISO", "Western Electricity Coordinating Council / California South"),
}

# AEO scenario id -> canonical `scenario` token. Reference case only for the
# corridor anchor (matching docs/handoffs/cross-model-corridor-2026-07-13.md);
# side cases are an available extension (add ids here + re-fetch with --scenario).
AEO_SCENARIOS: dict[str, str] = {"ref2025": "reference"}

# AEO Tables carrying the corridor quantities (API tableId).
AEO_TABLES: tuple[str, ...] = ("62", "67")  # Table 54, Table 56

# AEO corridor target years.
CORRIDOR_YEARS: tuple[int, ...] = (2030, 2035, 2040)

# Series NAME (exact, stable) -> (quantity, tech, canonical_unit, expected_api_unit).
# Table 54 thermal capacity + generation + CO2; Table 56 renewable capacity split.
# Generation is only available in the AEO regional tables at the renewable
# AGGREGATE grain (no per-renewable-fuel TWh regionally) — a documented limit.
AEO_SERIESNAME_MAP: dict[str, tuple[str, str, str, str]] = {
    # --- Table 54: Electric Power Sector capacity (GW) ---
    "Electricity : Electric Power Sector : Capacity : Coal": (
        "capacity",
        "coal",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Combined Cycle": (
        "capacity",
        "gas_cc",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Combustion Turbine/Diesel": (
        "capacity",
        "gas_ct",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Fossil Steam": (
        "capacity",
        "gas_st",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Nuclear": (
        "capacity",
        "nuclear",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Diurnal Storage": (
        "capacity",
        "storage",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Pumped Storage": (
        "capacity",
        "pumped_storage",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Renewable Sources": (
        "capacity",
        "renewables",
        "GW",
        "GW",
    ),
    "Electricity : Electric Power Sector : Capacity : Total Capacity": (
        "capacity",
        "total",
        "GW",
        "GW",
    ),
    # --- Table 54: Electric Power Sector generation (TWh; AEO native BkWh) ---
    "Electricity : Electric Power Sector : Generation : Coal": (
        "generation",
        "coal",
        "TWh",
        "BkWh",
    ),
    "Electricity : Electric Power Sector : Generation : Natural Gas": (
        "generation",
        "gas",
        "TWh",
        "BkWh",
    ),
    "Electricity : Electric Power Sector : Generation : Nuclear": (
        "generation",
        "nuclear",
        "TWh",
        "BkWh",
    ),
    "Electricity : Electric Power Sector : Generation : Petroleum": (
        "generation",
        "oil",
        "TWh",
        "BkWh",
    ),
    "Electricity : Electric Power Sector : Generation : Renewable Sources": (
        "generation",
        "renewables",
        "TWh",
        "BkWh",
    ),
    "Electricity : Electric Power Sector : Generation : Total Generation": (
        "generation",
        "total",
        "TWh",
        "BkWh",
    ),
    # --- Table 54: power-sector CO2 (million short tons) ---
    "Electricity : Emissions : Carbon Dioxide": ("co2", "total", "MMst_co2", "MMst"),
    # --- Table 56: Electric Power Sector renewable capacity split (GW) ---
    "Renewable Energy : Electric Power Sector : Generating Capacity : Solar Photovoltaic": (
        "capacity",
        "solar",
        "GW",
        "GW",
    ),
    "Renewable Energy : Electric Power Sector : Generating Capacity : Solar Thermal": (
        "capacity",
        "solar_thermal",
        "GW",
        "GW",
    ),
    "Renewable Energy : Electric Power Sector : Generating Capacity : Onshore Wind": (
        "capacity",
        "wind",
        "GW",
        "GW",
    ),
    "Renewable Energy : Electric Power Sector : Generating Capacity : Offshore Wind": (
        "capacity",
        "offshore_wind",
        "GW",
        "GW",
    ),
    "Renewable Energy : Electric Power Sector : Generating Capacity : Geothermal": (
        "capacity",
        "geothermal",
        "GW",
        "GW",
    ),
    "Renewable Energy : Electric Power Sector : Generating Capacity : Hydropower": (
        "capacity",
        "hydro",
        "GW",
        "GW",
    ),
    "Renewable Energy : Electric Power Sector : Generating Capacity : Wood and Other Biomass": (
        "capacity",
        "biomass",
        "GW",
        "GW",
    ),
    "Renewable Energy : Electric Power Sector : Generating Capacity : Municipal Waste": (
        "capacity",
        "municipal_waste",
        "GW",
        "GW",
    ),
}

RAW_COLUMNS: tuple[str, ...] = (
    "source_release",
    "table_id",
    "region_id",
    "region_name",
    "scenario",
    "series_id",
    "series_name",
    "period",
    "value",
    "unit",
)

_BOUNDARY_NOTE = (
    "AEO EMM region ~ ISO footprint (approximate, not exact); FC-5 context only "
    "(rule 13, never a fit target)."
)


# ---------------------------------------------------------------------------
# Fetch (immutable raw)
# ---------------------------------------------------------------------------
def load_api_key() -> str:
    """Resolve the EIA API key: ``EIA_API_KEY`` env, repo ``.env``, then DEMO_KEY."""
    return get_api_key("EIA_API_KEY", required=False) or _DEMO_KEY


def _fetch_json(
    aeo_year: int,
    table_id: str,
    region_id: str,
    scenario: str,
    key: str,
    start: int,
    end: int,
    sleep_s: float,
) -> list[dict]:
    """Fetch every series row for one (table, region, scenario) over [start, end]."""
    q = {
        "api_key": key,
        "frequency": "annual",
        "facets[tableId][]": table_id,
        "facets[regionId][]": region_id,
        "facets[scenario][]": scenario,
        "data[0]": "value",
        "start": str(start),
        "end": str(end),
        "length": 5000,
    }
    url = f"{API_BASE}/{aeo_year}/data/?{urlencode(q, doseq=True)}"
    payload = None
    last: Exception | None = None
    for attempt, wait in enumerate((0, 5, 10, 20, 40, 60)):
        if wait:
            print(f"    transient error — backoff {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
        try:
            with urlopen(url, timeout=90) as fh:
                payload = json.loads(fh.read().decode())
            break
        except (HTTPError, URLError) as exc:
            last = exc
            continue
    if payload is None:
        raise RuntimeError(
            f"AEO fetch failed (table {table_id}, region {region_id}): {last}"
        )
    time.sleep(sleep_s)
    return payload.get("response", {}).get("data", [])


def fetch_raw(
    raw_root: Path | None = None,
    *,
    aeo_year: int = 2025,
    scenarios: tuple[str, ...] = ("ref2025",),
    years: tuple[int, ...] = CORRIDOR_YEARS,
    sleep_s: float = 0.3,
    key: str | None = None,
) -> Path:
    """Fetch the AEO2025 electricity-corridor tables into the immutable raw CSV.

    Pulls Tables 54 + 56 for every EMM region in :data:`AEO_EMM_TO_ISO`, each
    requested scenario, filtered to ``years`` and to the corridor series the
    parser maps (:data:`AEO_SERIESNAME_MAP`). Writes a deterministic (sorted)
    raw CSV with the API-native columns. Returns the path written.
    """
    root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    out_dir = root / bc.DATATYPE / RAW_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / RAW_FILENAME
    key = key or load_api_key()
    yrs = set(int(y) for y in years)
    start, end = min(yrs), max(yrs)
    rows: list[dict] = []
    for scenario in scenarios:
        for region_id in AEO_EMM_TO_ISO:
            for table_id in AEO_TABLES:
                print(
                    f"  AEO2025 table {table_id} region {region_id} scenario {scenario} …"
                )
                for r in _fetch_json(
                    aeo_year, table_id, region_id, scenario, key, start, end, sleep_s
                ):
                    period = r.get("period")
                    if period in (None, "") or int(period) not in yrs:
                        continue
                    if r.get("value") in (None, "", "NA"):
                        continue
                    # Scope raw to the corridor series the parser maps (the fetch
                    # already scopes regions/years/tables) — keeps raw lean and
                    # purposeful; the fetch and parser share AEO_SERIESNAME_MAP so
                    # they cannot drift. A new mapped series is a cheap re-fetch.
                    if str(r.get("seriesName", "")).strip() not in AEO_SERIESNAME_MAP:
                        continue
                    rows.append(
                        {
                            "source_release": f"aeo{aeo_year}",
                            "table_id": table_id,
                            "region_id": region_id,
                            "region_name": r.get(
                                "regionName", AEO_EMM_TO_ISO[region_id][1]
                            ),
                            "scenario": scenario,
                            "series_id": r.get("seriesId", ""),
                            "series_name": r.get("seriesName", ""),
                            "period": int(period),
                            "value": round(float(r["value"]), 6),
                            "unit": r.get("unit", ""),
                        }
                    )
    rows.sort(
        key=lambda d: (
            d["scenario"],
            d["region_id"],
            d["table_id"],
            d["series_id"],
            d["period"],
        )
    )
    with out_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(RAW_COLUMNS))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} raw AEO rows -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Parse (raw -> canonical)
# ---------------------------------------------------------------------------
def parse(raw_dir: Path) -> pd.DataFrame:
    """Map the AEO raw CSV onto canonical benchmark-corridor rows.

    Reads only the immutable raw fetch; skips any series not in
    :data:`AEO_SERIESNAME_MAP`; asserts each mapped row's native API unit
    (fail-loud on an AEO label/unit change). Returns an empty frame if the raw
    file has not landed.
    """
    raw_dir = Path(raw_dir)
    path = raw_dir / RAW_FILENAME
    if not path.is_file():
        return pd.DataFrame(columns=list(bc.CANONICAL_COLUMNS))
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    if raw.empty:
        return pd.DataFrame(columns=list(bc.CANONICAL_COLUMNS))

    out: list[dict] = []
    for _, r in raw.iterrows():
        name = str(r["series_name"]).strip()
        mapped = AEO_SERIESNAME_MAP.get(name)
        if mapped is None:
            continue  # a series outside the corridor subset
        quantity, tech, unit, expected_api_unit = mapped
        api_unit = str(r["unit"]).strip()
        if api_unit != expected_api_unit:
            raise ValueError(
                f"AEO unit drift for {name!r}: expected API unit {expected_api_unit!r}, "
                f"got {api_unit!r} (series {r['series_id']}) — refusing to guess"
            )
        region_id = str(r["region_id"]).strip()
        if region_id not in AEO_EMM_TO_ISO:
            continue  # a region outside our ISO crosswalk
        iso, _region_name = AEO_EMM_TO_ISO[region_id]
        scenario = AEO_SCENARIOS.get(
            str(r["scenario"]).strip(), str(r["scenario"]).strip()
        )
        out.append(
            {
                "source": SOURCE,
                "iso": iso,
                "region": str(r["region_name"]).strip(),
                "vintage": VINTAGE,
                "scenario": scenario,
                "target_year": int(r["period"]),
                "quantity": quantity,
                "tech": tech,
                "value": float(r["value"]),
                "unit": unit,
                "source_doc": (
                    "EIA Annual Energy Outlook 2025, Open Data API v2 aeo route "
                    "(Table 54 Electric Power Projections by EMM Region; "
                    "Table 56 Renewable Energy Generation by Fuel)"
                ),
                "source_page": f"seriesId={r['series_id']} (tableId={r['table_id']}, regionId={region_id})",
                "note": _BOUNDARY_NOTE,
            }
        )
    if not out:
        return pd.DataFrame(columns=list(bc.CANONICAL_COLUMNS))
    return pd.DataFrame(out)


bc.register(
    bc.SourceSpec(
        source=SOURCE,
        raw_subdir=RAW_SUBDIR,
        isos=("ERCOT", "PJM", "MISO", "NYISO", "NEISO", "CAISO"),
        vintage=VINTAGE,
        description=(
            "EIA AEO2025 regional electricity projections (Table 54 + Table 56): "
            "capacity mix, energy mix, power-sector CO2 by EMM region, 2030/2035/2040."
        ),
        fetchable=True,
        parse=parse,
        citation="https://www.eia.gov/outlooks/aeo/ (Open Data API v2 aeo route, AEO2025)",
    )
)
