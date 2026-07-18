"""Measured interconnection-throughput seeds for the FF-2A entry growth ladder.

Standalone data module (kept out of ``data/fleet.py`` deliberately — the fleet
module is a rule-27 core file): derives each entry technology's historical
maximum annual COD build (GW) by ISO from the EIA-860 record at the run's
vintage, the externally identified seed of ``ScenarioConfig.entry_rate_limits``
(``config.entry_config.ENTRY_GROWTH_LIMIT_MULTIPLE`` × prior-max, ReEDS
growth-constraint hard bound).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from market_sim.config.paths import active_eia860_dir
from market_sim.data.fleet import BA_CODE_TO_ISO, _map_fuel_type

logger = logging.getLogger(__name__)

# Entry-screen technologies whose measured build-throughput seed comes from
# the thermal generator sheet (via _map_fuel_type); wind/solar read their own
# EIA-860 technology sheets below. Storage is deliberately absent — its entry
# runs through the storage value-stack screen, not apply_economic_new_entry.
_THROUGHPUT_THERMAL_TECHS: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "nuclear", "coal", "oil"}
)


def max_annual_build_gw_by_tech(
    iso: str,
    through_year: int,
    window_years: int,
    data_dir: Path | None = None,
) -> dict[str, float]:
    """Measured prior-max annual build (GW) by entry tech for one ISO.

    The externally identified seed of the FF-2A entry growth ladder
    (``ScenarioConfig.entry_rate_limits``): for each entry-screen technology,
    the maximum nameplate MW that reached commercial operation in any single
    year of the trailing ``[through_year - window_years + 1, through_year]``
    window, from the EIA-860 record at ``data_dir`` (the run's vintage
    directory — a 2020-vintage hindcast reads ``vintage_2020/`` and therefore
    sees only what was knowable at the vintage cutoff; a forecast reads the
    canonical latest release). Plants map to ISOs by their EIA-860 balancing
    authority (:data:`market_sim.data.fleet.BA_CODE_TO_ISO`), the same
    crosswalk the fleet loaders use. Wind/solar come from their EIA-860
    technology sheets; dispatchable thermal from the generator sheet via
    :func:`market_sim.data.fleet._map_fuel_type`.

    Purely formulaic from source data (rule 13: regenerates for any forward
    vintage; rule 23: re-derives only when the EIA-860 data updates). A tech
    with no COD in the window is ABSENT from the result — the caller must
    treat a missing tech as "no ladder cap", never as a zero cap (rule 25:
    a missing measurement must not forbid entry).

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        through_year: Last COD year of the trailing window (the vintage year
            for a vintage-start run, else the year before the start year).
        window_years: Trailing window length
            (:data:`market_sim.config.entry_config.ENTRY_THROUGHPUT_WINDOW_YEARS`).
        data_dir: EIA-860 directory; defaults to :func:`active_eia860_dir`.

    Returns:
        ``{tech: max_annual_build_gw}`` over techs with at least one windowed
        COD. Empty when the sheets are missing (logged).
    """
    iso = iso.upper()
    if data_dir is None:
        data_dir = active_eia860_dir()
    data_dir = Path(data_dir)

    plant_path = data_dir / "eia860_plant.parquet"
    gen_path = data_dir / "eia860_generator_operable.parquet"
    if not plant_path.exists() or not gen_path.exists():
        logger.warning(
            "entry throughput seed unavailable for %s: missing %s",
            iso,
            plant_path.name if not plant_path.exists() else gen_path.name,
        )
        return {}
    plants = pd.read_parquet(plant_path)[
        ["Plant Code", "Balancing Authority Code"]
    ].drop_duplicates("Plant Code")

    frames: list[pd.DataFrame] = []
    gens = pd.read_parquet(gen_path)
    gens = gens.assign(
        tech=[
            _map_fuel_type(None, es, pm)
            for es, pm in zip(gens["Energy Source 1"], gens["Prime Mover"])
        ]
    )
    gens = gens[gens["tech"].isin(_THROUGHPUT_THERMAL_TECHS)]
    frames.append(
        gens[["Plant Code", "Nameplate Capacity (MW)", "Operating Year", "tech"]]
    )
    for sheet, tech in (
        ("eia860_solar_operable.parquet", "solar"),
        ("eia860_wind_operable.parquet", "wind"),
    ):
        path = data_dir / sheet
        if not path.exists():
            continue
        df = pd.read_parquet(path).assign(tech=tech)
        frames.append(
            df[["Plant Code", "Nameplate Capacity (MW)", "Operating Year", "tech"]]
        )

    all_units = pd.concat(frames, ignore_index=True)
    all_units = all_units.merge(plants, on="Plant Code", how="left")
    unit_iso = all_units["Balancing Authority Code"].map(BA_CODE_TO_ISO)
    year = pd.to_numeric(all_units["Operating Year"], errors="coerce")
    lo = through_year - window_years + 1
    windowed = all_units[(unit_iso == iso) & (year >= lo) & (year <= through_year)]
    if windowed.empty:
        return {}
    annual = (
        windowed.groupby(["tech", pd.to_numeric(windowed["Operating Year"])])[
            "Nameplate Capacity (MW)"
        ].sum()
        / 1000.0
    )
    return {
        str(tech): float(annual.loc[tech].max())
        for tech in annual.index.get_level_values(0).unique()
    }
