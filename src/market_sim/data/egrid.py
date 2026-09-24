"""eGRID plant-level fossil CO2 emission rates (kg CO2 per net MWh).

EPA's eGRID workbook reports, for every U.S. plant, annual CO2 mass and annual
net generation. The ratio is a per-plant CO2 emission rate (kg CO2 / net MWh)
that — unlike CAMPD CEMS, which only covers the larger stack-monitored plants —
spans the *whole* fossil fleet, including the small gas/oil units CEMS omits.
For the larger plants eGRID's CO2 is itself CEMS-derived, so the two sources are
consistent; this module therefore uses eGRID as the fleet-wide base and lets the
CAMPD-measured intensities (``plant_emission_rates.parquet``) override it where
they exist.

The headline product is :func:`fossil_co2_rate_map` — ``{plant_id: kg CO2 /
net MWh}`` for every fossil plant in a year — and :func:`class_co2_intensity`,
which collapses that per-plant map to a net-generation-weighted CO2 intensity
(metric tonnes / MWh) per dispatch class. Multiplying a class's generation (MWh)
by its intensity gives metric tonnes of CO2, the calibration-page emissions
metric.

Vintages: every released workbook anchors its own year (2018-2024); eGRID 2024
(the latest released vintage) anchors 2025 and any later year (a plant's CO2
intensity is a stable physical property, so the prior vintage is a sound forward
stand-in until the next eGRID lands). The admissibility test of Non-Negotiable
Rule #11 holds: an emission rate is a reproducible physical input that would
regenerate for a forward year.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from market_sim.config.paths import FLEET_DIR, PROCESSED_DIR
from market_sim.data.clean_access import use_clean
from market_sim.data.campd import KG_PER_TONNE, SHORT_TON_TO_KG

logger = logging.getLogger(__name__)

# Opt-in clean-data read path. When the ``MARKET_SIM_USE_CLEAN`` environment
# flag is truthy, the eGRID plant sheet is sourced from the curated
# ``data/clean/egrid`` tree (written by ``scripts/data/curate_egrid.py``) instead of
# parsing the 21 MB workbook. OFF by default; falls back to raw when the clean
# partition for the vintage is absent.
_USE_CLEAN_ENV = "MARKET_SIM_USE_CLEAN"
_USE_CLEAN_TRUTHY = frozenset({"1", "true", "yes", "on"})


# The clean-data read gate is centralised in data.clean_access; aliased here so
# call sites do not churn (behaviour byte-identical, default OFF).
_use_clean = use_clean


# eGRID plant-sheet workbooks by vintage year. The plant sheet (``PLNT<YY>``)
# carries one row per plant; its first row holds long descriptive headers, so
# ``skiprows=1`` promotes the short-code header row (ORISPL, PLCO2AN, ...).
_EGRID_FILES: dict[int, str] = {
    # eGRID2018-2021: epa.gov/egrid "historical eGRID data" archive, retrieved
    # 2026-07-31 for the 2018-2021 holdout-ladder intake (before it, those years
    # rode the latest vintage; rule 14 [R-ACCURATE] prefers the true vintage).
    # v2 revisions are EPA's own corrected releases — the latest revision of each
    # vintage, matching the egrid2023_data_rev2 precedent.
    2018: "egrid2018_data_v2.xlsx",
    2019: "egrid2019_data.xlsx",
    2020: "eGRID2020_Data_v2.xlsx",
    2021: "eGRID2021_data.xlsx",
    # eGRID2022: epa.gov/egrid published workbook, retrieved 2026-07-04 for
    # the 2022 holdout-year intake (before it, 2022 rode the latest vintage).
    2022: "egrid2022_data.xlsx",
    2023: "egrid2023_data_rev2.xlsx",
    2024: "egrid2024_data.xlsx",
}
_LATEST_EGRID_VINTAGE: int = max(_EGRID_FILES)

# eGRID plant-sheet short-code columns we read.
#   ORISPL   — ORIS plant code (== EIA plant_id == CAMPD facilityId).
#   PLFUELCT — plant primary fuel category (COAL / GAS / OIL / OFSL / ...).
#   PLNGENAN — plant annual net generation, MWh.
#   PLCO2AN  — plant annual CO2 mass, **short tons**.
_EGRID_COLS: tuple[str, ...] = ("ORISPL", "PLFUELCT", "PLNGENAN", "PLCO2AN")

# eGRID ``PLFUELCT`` categories treated as fossil (combustion CO2 emitters).
# OFSL is eGRID's "other fossil" (petroleum coke, waste gases, tyre-derived
# fuel, ...). Renewables, nuclear, hydro and biomass are excluded — biomass CO2
# is reported by eGRID but is biogenic, not part of the fossil dispatch the
# emissions metric calibrates.
FOSSIL_FUEL_CATEGORIES: frozenset[str] = frozenset({"COAL", "GAS", "OIL", "OFSL"})

# Pooled CAMPD-measured per-plant CO2 rates (kg / net MWh), the override layer.
_CAMPD_RATES_PATH: Path = PROCESSED_DIR / "plant_emission_rates.parquet"
# Pre-derived fleet-wide fossil rate artifact (scripts/data/derive_fossil_co2_rates.py).
# Read in preference to parsing the 21 MB eGRID workbook when present.
FOSSIL_CO2_RATES_PATH: Path = PROCESSED_DIR / "fossil_co2_rates.parquet"

# Process-level caches so the workbook / parquet is read at most once per year.
_EGRID_RATE_CACHE: dict[int, dict[int, float]] = {}
_CAMPD_RATE_CACHE: dict[int, float] | None = None


def egrid_vintage_for_year(year: int) -> int:
    """Return the eGRID vintage that anchors ``year``.

    A year with its own released workbook (2018-2024) maps to itself; any
    other year maps to the latest released vintage (currently 2024), whose
    intensities stand in until the next eGRID lands.
    """
    return int(year) if int(year) in _EGRID_FILES else _LATEST_EGRID_VINTAGE


def _egrid_path(vintage: int) -> Path:
    """Return the eGRID workbook path for a vintage year."""
    return FLEET_DIR / _EGRID_FILES[vintage]


# ---------------------------------------------------------------------------
# Plant heat rates by eGRID vintage — the ONE resolver (rule 19 [R-ONE-MECH])
# ---------------------------------------------------------------------------
#
# F1 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md
# §1 D1/D2). Before it, the EIA-860 build joined eGRID 2023's ``PLHTRT`` into
# every generator table it wrote — the canonical snapshot, the within-window
# retiree parquet — and the year-matched ``vintage_<Y>/`` tables it had
# rescoped carried NO heat rate at all, so a 2019-2022 backcast priced 95-100 %
# of every ISO's thermal MW at the ``HEAT_RATE_BINS`` asset-class table. The
# join, the boundary repair and the retiree join now all resolve the eGRID
# vintage through this block, so no solve-path caller names a workbook.

# Physical window for an eGRID plant heat rate, Btu/kWh: below it a plant with
# near-zero net generation reports a negative or absurd ``PLHTRT``, above it
# the same. The plant-grain join and the prime-mover-family derive
# (``scripts/data/derive_egrid_family_heat_rates``) share this ONE window so a
# family rate is admitted on exactly the plant rate's terms. (Moved here from
# ``scripts/data/process_eia860`` by F1, which re-exports it unchanged.)
EGRID_HR_WINDOW_BTU_KWH: tuple[int, int] = (3_000, 30_000)


def egrid_workbook_path(vintage: int) -> Path:
    """Return the committed eGRID workbook for ``vintage`` (2018 ... 2024).

    Raises:
        KeyError: ``vintage`` has no committed workbook; resolve a calendar
            year through :func:`egrid_vintage_for_year` first.
    """
    return _egrid_path(int(vintage))


def egrid_sheet_name(kind: str, vintage: int) -> str:
    """Return eGRID's sheet name for a sheet family and vintage.

    eGRID names every sheet ``<KIND><YY>`` (``PLNT24``, ``UNT21``, ``GEN19``),
    so the two-digit suffix is the vintage's — never a literal ``23``.

    Args:
        kind: The sheet family, e.g. ``"PLNT"``, ``"UNT"``, ``"GEN"``.
        vintage: The eGRID vintage year.
    """
    return f"{kind.upper()}{int(vintage) % 100:02d}"


def egrid_vintage_for_eia860_dir(eia860_dir: Path) -> int:
    """Return the eGRID vintage that matches an EIA-860 source directory.

    A year-matched ``vintage_<Y>/`` directory joins eGRID ``Y`` (through
    :func:`egrid_vintage_for_year`, so a year past the latest workbook takes the
    latest). Every other directory — the canonical 2025 Early Release snapshot
    — joins the LATEST released vintage (currently eGRID 2024): the snapshot
    describes the fleet as of the 2025 release, and eGRID 2024 is the most
    recent measured year of that fleet's operation. There is no eGRID 2025.

    Args:
        eia860_dir: An EIA-860 directory (canonical or ``vintage_<Y>``).
    """
    name = Path(eia860_dir).name
    if name.startswith("vintage_"):
        try:
            return egrid_vintage_for_year(int(name.split("_", 1)[1]))
        except ValueError:
            pass
    return _LATEST_EGRID_VINTAGE


def _plant_heat_rate_sheet(vintage: int) -> pd.Series:
    """Return ``{ORISPL: PLHTRT in MMBtu/MWh}`` for one vintage, windowed.

    Read through :func:`market_sim.data.egrid_sheets.read_egrid_sheet`, so the
    workbook is parsed once per content and served from its parquet mirror
    after that. Rows outside :data:`EGRID_HR_WINDOW_BTU_KWH` are dropped.
    """
    from market_sim.data.egrid_sheets import read_egrid_sheet

    raw = read_egrid_sheet(
        egrid_workbook_path(vintage),
        egrid_sheet_name("PLNT", vintage),
        ["ORISPL", "PLHTRT"],
    )
    hr = pd.to_numeric(raw["PLHTRT"], errors="coerce")
    code = pd.to_numeric(raw["ORISPL"], errors="coerce")
    lo, hi = EGRID_HR_WINDOW_BTU_KWH
    keep = code.notna() & hr.notna() & (hr >= lo) & (hr <= hi)
    out = pd.Series(
        hr[keep].to_numpy(dtype=float) / 1000.0,
        index=code[keep].astype("int64").to_numpy(),
        name=int(vintage),
    )
    return out[~out.index.duplicated(keep="first")]


_PLANT_HR_TABLE: pd.DataFrame | None = None


def plant_heat_rate_table() -> pd.DataFrame:
    """Return every committed vintage's plant heat rate, plant x vintage.

    Index ``plant_id`` (eGRID ``ORISPL`` == EIA plant code), one column per
    eGRID vintage in :data:`_EGRID_FILES`, values MMBtu per net MWh
    (``PLHTRT / 1000``), NaN where the vintage publishes no in-window rate.
    A vintage whose workbook is absent contributes an all-NaN column. Cached
    for the process.
    """
    global _PLANT_HR_TABLE
    if _PLANT_HR_TABLE is None:
        cols = []
        for vintage in sorted(_EGRID_FILES):
            if not _egrid_path(vintage).exists():
                logger.warning(
                    "eGRID %d workbook absent; that vintage contributes no heat rates",
                    vintage,
                )
                cols.append(pd.Series(dtype=float, name=vintage))
                continue
            cols.append(_plant_heat_rate_sheet(vintage))
        table = pd.concat(cols, axis=1)
        table.index.name = "plant_id"
        _PLANT_HR_TABLE = table
    return _PLANT_HR_TABLE


def resolve_plant_heat_rates(
    plant_ids: pd.Series,
    target_vintage: int | pd.Series,
    table: pd.DataFrame | None = None,
) -> tuple[pd.Series, pd.Series]:
    """Return each plant's eGRID heat rate at a target vintage, with fallback.

    The fallback order is fixed and carries ZERO free parameters:

    1. the target vintage's own in-window ``PLHTRT``;
    2. else the plant's NEAREST vintage that publishes one, by absolute year
       distance, a tie going to the EARLIER vintage (the rate that was on file
       first — it cannot carry information from after the earlier year);
    3. else NaN, and only then does the fleet loader reach the
       ``HEAT_RATE_BINS`` asset-class table.

    Rule 13 [R-MEASURED]: every value is a published measured plant rate, and
    the vintage is selected by calendar year alone — never by a residual.

    Args:
        plant_ids: EIA plant codes (any numeric-coercible dtype).
        target_vintage: One eGRID vintage for every row, or a per-row Series
            aligned to ``plant_ids`` (the retiree join passes each unit's own
            last operating year, already resolved to a vintage).
        table: Override for :func:`plant_heat_rate_table` (tests).

    Returns:
        ``(heat_rate, source_vintage)`` — both aligned to ``plant_ids``;
        ``heat_rate`` in MMBtu/MWh (NaN where no vintage covers the plant) and
        ``source_vintage`` the eGRID vintage that supplied it (``<NA>`` where
        none did).
    """
    table = plant_heat_rate_table() if table is None else table
    codes = pd.to_numeric(plant_ids, errors="coerce")
    if isinstance(target_vintage, pd.Series):
        targets = pd.to_numeric(target_vintage, errors="coerce").reindex(codes.index)
    else:
        targets = pd.Series(int(target_vintage), index=codes.index)
    hr = pd.Series(float("nan"), index=codes.index, dtype=float)
    src = pd.Series(pd.NA, index=codes.index, dtype="Int64")
    vintages = [int(v) for v in table.columns]
    for target in sorted(targets.dropna().unique()):
        rows = targets == target
        order = sorted(vintages, key=lambda v: (abs(v - int(target)), v))
        for vintage in order:
            need = rows & hr.isna() & codes.notna()
            if not need.any():
                break
            got = codes[need].map(table[vintage])
            hit = got.notna()
            if hit.any():
                idx = got.index[hit]
                hr.loc[idx] = got[hit].astype(float)
                src.loc[idx] = vintage
    return hr, src


def _load_egrid_plant_co2_raw(vintage: int) -> pd.DataFrame:
    """Parse the eGRID workbook's plant sheet for a vintage (the raw path)."""
    sheet = f"PLNT{vintage % 100:02d}"
    raw = pd.read_excel(
        _egrid_path(vintage), sheet_name=sheet, skiprows=1, usecols=list(_EGRID_COLS)
    )
    return pd.DataFrame(
        {
            "plant_id": pd.to_numeric(raw["ORISPL"], errors="coerce"),
            "fuel_cat": raw["PLFUELCT"].astype(str).str.upper(),
            "net_mwh": pd.to_numeric(raw["PLNGENAN"], errors="coerce"),
            "co2_tons": pd.to_numeric(raw["PLCO2AN"], errors="coerce"),
        }
    )


def load_egrid_plant_co2(vintage: int) -> pd.DataFrame:
    """Return the eGRID plant sheet's fossil CO2 columns for a vintage year.

    Args:
        vintage: An eGRID vintage present in :data:`_EGRID_FILES`
            (2018 ... 2024).

    Returns:
        One row per fossil plant with positive net generation: ``plant_id``,
        ``fuel_cat`` (eGRID ``PLFUELCT``), ``net_mwh``, ``co2_tons`` (short
        tons) and ``co2_kg_per_mwh_net`` (CO2 kg per net MWh).

    When ``MARKET_SIM_USE_CLEAN`` is set (default OFF) and the curated
    ``data/clean/egrid`` partition for this vintage exists (written by
    ``scripts/data/curate_egrid.py``), the plant sheet is read from there instead
    of the 21 MB workbook; otherwise it falls back to the raw parse.
    """
    if _use_clean():
        from scripts.lib.clean_io import clean_exists, read_clean

        if clean_exists("egrid", year=vintage):
            df = read_clean(
                "egrid",
                year=vintage,
                columns=["plant_id", "fuel_cat", "net_mwh", "co2_tons"],
            )
            return _fossil_co2_from_plant_frame(df)
    df = _load_egrid_plant_co2_raw(vintage)
    return _fossil_co2_from_plant_frame(df)


def _fossil_co2_from_plant_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the fossil/positive-generation filter shared by both read paths."""
    df = df.dropna(subset=["plant_id"]).copy()
    df["plant_id"] = df["plant_id"].astype(int)
    df["fuel_cat"] = df["fuel_cat"].astype(str).str.upper()
    df = df[
        df["fuel_cat"].isin(FOSSIL_FUEL_CATEGORIES)
        & (df["net_mwh"] > 0.0)
        & (df["co2_tons"] > 0.0)
    ].copy()
    # kg CO2 / net MWh: short tons -> kg, divided by net MWh.
    df["co2_kg_per_mwh_net"] = df["co2_tons"] * SHORT_TON_TO_KG / df["net_mwh"]
    return df.reset_index(drop=True)


def _egrid_rate_map(year: int) -> dict[int, float]:
    """Return ``{plant_id: kg CO2 / net MWh}`` from eGRID, cached per year."""
    vintage = egrid_vintage_for_year(year)
    if vintage not in _EGRID_RATE_CACHE:
        df = load_egrid_plant_co2(vintage)
        _EGRID_RATE_CACHE[vintage] = dict(zip(df["plant_id"], df["co2_kg_per_mwh_net"]))
    return _EGRID_RATE_CACHE[vintage]


def _campd_rate_map() -> dict[int, float]:
    """Return ``{plant_id: kg CO2 / net MWh}`` from pooled CAMPD CEMS rates.

    Reads the pooled (``year == 0``) rows of ``plant_emission_rates.parquet``;
    empty when the artifact is absent. Cached for the process.
    """
    global _CAMPD_RATE_CACHE
    if _CAMPD_RATE_CACHE is None:
        if not _CAMPD_RATES_PATH.exists():
            _CAMPD_RATE_CACHE = {}
        else:
            r = pd.read_parquet(_CAMPD_RATES_PATH)
            pooled = r[(r["year"] == 0) & (r["co2_kg_per_mwh_net"] > 0.0)]
            _CAMPD_RATE_CACHE = {
                int(p): float(v)
                for p, v in zip(pooled["plant_id"], pooled["co2_kg_per_mwh_net"])
            }
    return _CAMPD_RATE_CACHE


def fossil_co2_rate_map(year: int) -> dict[int, float]:
    """Return ``{plant_id: kg CO2 / net MWh}`` for every fossil plant in a year.

    eGRID supplies the fleet-wide base (the only source that covers the small,
    non-CEMS units); the CAMPD-measured pooled intensities override it for the
    larger stack-monitored plants. When the pre-derived
    ``fossil_co2_rates.parquet`` artifact exists it is read directly (fast path,
    no 21 MB workbook parse); otherwise the map is assembled from the eGRID
    workbook and the CAMPD parquet on the fly.

    Args:
        year: Calendar year. eGRID 2023 anchors 2023; 2024 anchors 2024+.

    Returns:
        ``{plant_id: kg CO2 / net MWh}`` over the fossil fleet.
    """
    if FOSSIL_CO2_RATES_PATH.exists():
        art = pd.read_parquet(FOSSIL_CO2_RATES_PATH)
        sub = art[art["year"] == int(year)]
        if not sub.empty:
            return {
                int(p): float(v)
                for p, v in zip(sub["plant_id"], sub["co2_kg_per_mwh_net"])
            }
    # eGRID base, CAMPD override (CAMPD second so it wins on overlap).
    return {**_egrid_rate_map(year), **_campd_rate_map()}


def build_fossil_co2_rates(years: list[int] | tuple[int, ...]) -> pd.DataFrame:
    """Assemble the fleet-wide fossil CO2 rate table for one or more years.

    One row per ``(plant_id, year)``: ``co2_kg_per_mwh_net`` (CAMPD-measured
    where available, else eGRID-derived), ``source`` (``"campd"`` /
    ``"egrid"``), the ``net_mwh`` and ``fuel_cat`` that anchored the eGRID rate,
    and the eGRID ``vintage`` used. This is what
    ``scripts/data/derive_fossil_co2_rates.py`` writes to
    :data:`FOSSIL_CO2_RATES_PATH`.

    Args:
        years: Calendar years to assemble.

    Returns:
        The per-(plant, year) rate table.
    """
    campd = _campd_rate_map()
    rows: list[dict] = []
    for year in years:
        year = int(year)
        vintage = egrid_vintage_for_year(year)
        egrid = load_egrid_plant_co2(vintage)
        egrid_rate = dict(zip(egrid["plant_id"], egrid["co2_kg_per_mwh_net"]))
        egrid_fuel = dict(zip(egrid["plant_id"], egrid["fuel_cat"]))
        egrid_gen = dict(zip(egrid["plant_id"], egrid["net_mwh"]))
        for plant_id in sorted(set(egrid_rate) | set(campd)):
            if plant_id in campd:
                rate, source = campd[plant_id], "campd"
            else:
                rate, source = egrid_rate[plant_id], "egrid"
            rows.append(
                {
                    "plant_id": int(plant_id),
                    "year": year,
                    "co2_kg_per_mwh_net": round(float(rate), 6),
                    "source": source,
                    "fuel_cat": egrid_fuel.get(plant_id, ""),
                    "net_mwh": round(float(egrid_gen.get(plant_id, 0.0)), 3),
                    "vintage": vintage,
                }
            )
    return pd.DataFrame(rows)


def class_co2_intensity(
    generation: pd.DataFrame,
    rate_map: dict[int, float],
    *,
    plant_col: str = "plant_id",
    klass_col: str = "klass",
    gen_col: str = "annual_mwh",
) -> dict[str, float]:
    """Return net-generation-weighted CO2 intensity (tonnes/MWh) per class.

    For each dispatch class, the intensity is the generation-weighted mean of
    its plants' per-MWh CO2 rates — i.e. ``Σ(rate·gen) / Σ(gen)`` over the
    class's plants that carry a rate in ``rate_map`` — converted from kg to
    metric tonnes. Multiplying a class's generation (MWh) by this intensity
    yields metric tonnes of CO2. Plants absent from ``rate_map`` (no eGRID or
    CAMPD rate) are excluded from the weighting but the resulting intensity is
    still the class's best per-MWh estimate for the plants that do report.

    Args:
        generation: A per-plant generation frame (e.g. the bundle's EIA-923
            fossil benchmark), with plant id, dispatch class and net-MWh columns.
        rate_map: ``{plant_id: kg CO2 / net MWh}`` from :func:`fossil_co2_rate_map`.
        plant_col: Plant-id column name.
        klass_col: Dispatch-class column name.
        gen_col: Net-generation (MWh) column name.

    Returns:
        ``{klass: metric tonnes CO2 / MWh}`` for every class with weighted
        generation.
    """
    if generation.empty:
        return {}
    df = generation[[plant_col, klass_col, gen_col]].copy()
    df["rate"] = df[plant_col].astype(int).map(rate_map)
    df = df[df["rate"].notna() & (df[gen_col] > 0.0)]
    out: dict[str, float] = {}
    for klass, g in df.groupby(klass_col, observed=True):
        gen = float(g[gen_col].sum())
        if gen <= 0.0:
            continue
        co2_kg = float((g["rate"] * g[gen_col]).sum())
        out[str(klass)] = co2_kg / gen / KG_PER_TONNE
    return out
