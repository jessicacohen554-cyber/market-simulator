"""Measured deactivation-throughput seed for the FFR-3F exit-rate cap.

Standalone data module and the deliberate mirror of ``build_throughput.py``,
its entry-side analogue (kept out of ``data/fleet.py`` for the same reason —
the fleet module is a rule-27 core file): derives each ISO's measured maximum
single-year thermal DEACTIVATION (GW) from the EIA-860 retired sheet at the
run's vintage, the externally identified seed of
``ScenarioConfig.exit_rate_limits``
(``config.retirement_config.EXIT_THROUGHPUT_LIMIT_MULTIPLE`` x prior-max).

Identification source, named by owner decision D-8 verbatim
(``docs/handoffs/ffr-owner-sitting-2026-08-02.md`` Addendum F.1, from the
FF-1A redesign memo §3.3): *"max observed single-year per-ISO thermal
deactivation from the EIA-860 retired sheet — measurable"*. Rule 13
``[R-MEASURED]`` admissible: it is a physical/market throughput input that
regenerates for any forward vintage from source data and responds to changed
conditions (a future EIA-860 recording a larger deactivation year raises the
seed automatically), never a measured OUTCOME fed back to close a residual.

**Rule 23 ``[R-FROZEN-DERIVE]``: this module re-derives ONLY when the EIA-860
retired sheet updates — never because a residual moved.** A commit that
changes what this returns must cite the EIA-860 data change that caused it.
There is no residual channel into this file by construction: nothing here
reads a model result, a price, or a score.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from market_sim.config.paths import active_eia860_dir
from market_sim.data.fleet import BA_CODE_TO_ISO, _map_fuel_type

logger = logging.getLogger(__name__)

# Dispatchable-thermal fuel classes whose deactivation counts against the
# exit-throughput seed. Deliberately the SAME set as the entry side's
# ``build_throughput._THROUGHPUT_THERMAL_TECHS``, resolved through the SAME
# ``_map_fuel_type`` crosswalk, so the two halves of one queue are measured on
# one basis and their envelopes are comparable (which is the whole point of
# FFR-3C §1.4's asymmetry finding). Wind/solar/storage are absent: the exit
# cap bounds the retirement screen, which screens dispatchable thermal only.
_EXIT_THERMAL_TECHS: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "nuclear", "coal", "oil"}
)

# EIA-860 retired-sheet status code for a generator that actually retired.
# The sheet also carries "CN" (cancelled — never built, so never deactivated)
# and "IP" (indefinitely postponed); neither is a deactivation event and both
# would inflate the seed.
_RETIRED_STATUS: str = "RE"


def max_annual_exit_gw(
    iso: str,
    through_year: int,
    window_years: int,
    data_dir: Path | None = None,
) -> float | None:
    """Measured maximum single-year thermal deactivation (GW) for one ISO.

    The externally identified seed of the FFR-3F exit-rate cap: the largest
    nameplate MW of dispatchable thermal capacity that retired in any single
    year of the trailing ``[through_year - window_years + 1, through_year]``
    window, from the EIA-860 retired sheet at ``data_dir`` (the run's vintage
    directory — a 2023-vintage hindcast reads ``vintage_2023/`` and therefore
    sees only deactivations knowable at the vintage cutoff; a forecast reads
    the canonical latest release). Plants map to ISOs by their EIA-860
    balancing authority (:data:`market_sim.data.fleet.BA_CODE_TO_ISO`), the
    same crosswalk the fleet loaders and the entry-side seed use.

    Purely formulaic from source data (rule 13: regenerates for any forward
    vintage; rule 23: re-derives only when the EIA-860 data updates). An ISO
    with no thermal deactivation in the window returns ``None`` — the caller
    must treat that as "NO CAP", never as a zero cap (rule 25
    ``[R-ISO-SCOPE]``: a missing measurement must not forbid exit, exactly as
    a missing entry measurement must not forbid entry). ``None`` is likewise
    returned when the sheets are absent, logged.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        through_year: Last retirement year of the trailing window (the run's
            EIA-860 vintage year, else the year before the start year).
        window_years: Trailing window length
            (:data:`market_sim.config.retirement_config.EXIT_THROUGHPUT_WINDOW_YEARS`).
        data_dir: EIA-860 directory; defaults to :func:`active_eia860_dir`.

    Returns:
        The maximum single-year deactivation in GW, or ``None`` when the ISO
        has no measured thermal deactivation in the window.
    """
    iso = iso.upper()
    if data_dir is None:
        data_dir = active_eia860_dir()
    data_dir = Path(data_dir)

    plant_path = data_dir / "eia860_plant.parquet"
    retired_path = data_dir / "eia860_generator_retired_and_canceled.parquet"
    if not plant_path.exists() or not retired_path.exists():
        logger.warning(
            "exit throughput seed unavailable for %s: missing %s",
            iso,
            plant_path.name if not plant_path.exists() else retired_path.name,
        )
        return None
    plants = pd.read_parquet(plant_path)[
        ["Plant Code", "Balancing Authority Code"]
    ].drop_duplicates("Plant Code")

    units = pd.read_parquet(retired_path)
    units = units[units["Status"].astype(str).str.strip() == _RETIRED_STATUS]
    units = units.assign(
        tech=[
            _map_fuel_type(None, es, pm)
            for es, pm in zip(units["Energy Source 1"], units["Prime Mover"])
        ]
    )
    units = units[units["tech"].isin(_EXIT_THERMAL_TECHS)]
    units = units.merge(plants, on="Plant Code", how="left")
    unit_iso = units["Balancing Authority Code"].map(BA_CODE_TO_ISO)
    year = pd.to_numeric(units["Retirement Year"], errors="coerce")
    lo = through_year - window_years + 1
    windowed = units[(unit_iso == iso) & (year >= lo) & (year <= through_year)]
    if windowed.empty:
        return None
    annual = (
        windowed.groupby(pd.to_numeric(windowed["Retirement Year"]))[
            "Nameplate Capacity (MW)"
        ].sum()
        / 1000.0
    )
    return float(annual.max())
