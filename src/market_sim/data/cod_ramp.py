"""Commercial-operation-date (COD) ramp for the dispatch fleet.

A backcast solves a single historical year, but the thermal fleet snapshot
(the curated ERCOT CAMPD bins / the EIA-860 generator parquet) is a *recent*
vintage that includes units commissioned **after** the year being solved. Left
unfiltered, a 2023 backcast dispatches GWs of capacity that were not yet built —
inflating reserve headroom and suppressing the scarcity prices the LP can set.

Renewables and storage already respect their commercial-operation dates
(:func:`market_sim.data.renewables` ramps wind/solar by ``Operating Month`` /
``Operating Year``; storage enters by vintage). This module extends the **same
rule to every generator** — thermal, nuclear, oil — so the default backcast
fleet reflects only what was actually online in the solved year:

* ``cod_year  < run_year``  → fully online (fraction 1.0);
* ``cod_year == run_year``  → online part of the year; pro-rated by
  :data:`COD_YEAR_DEFAULT_SHARE` (a half-year default, because EIA-860 / the
  master registry record the commissioning *year* but not the month — a
  month-precise hourly mask is the future refinement);
* ``cod_year  > run_year``  → not yet built; **dropped** (fraction 0.0).

The commissioning year is keyed by EIA plant code, sourced from the curated
master plant registry (``year_built``) and back-filled from the EIA-860
generator parquet (``operating_year``). The ramp is applied two ways so it
covers both fleet-assembly paths:

* :func:`ramp_bins` scales the per-plant CAMPD bin capacities **before** they are
  aggregated into LP generators (ERCOT's path — the bins carry no build year, so
  the plant-code map is required);
* :func:`ramp_fleet` scales / drops raw :class:`Generator` objects by their own
  ``online_year`` (the EIA-860 path — nuclear, oil, and every non-ERCOT ISO),
  with the plant-code map as a fallback for units whose ``online_year`` is unset.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Fraction of the year a unit commissioned *during* the solved year is treated
# as online. EIA-860 / the registry give the commissioning year but not the
# month, so a half-year mid-point is the neutral default.
COD_YEAR_DEFAULT_SHARE = 0.5

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY = _REPO_ROOT / "inputs" / "master-plant-registry.csv"
_EIA860 = _REPO_ROOT / "inputs" / "raw-data" / "eia-860" / "eia860_generators.parquet"


def online_fraction(
    cod_year: int | None,
    run_year: int,
    cod_year_share: float = COD_YEAR_DEFAULT_SHARE,
) -> float:
    """Fraction of ``run_year`` a unit with commissioning year ``cod_year`` is online."""
    if cod_year is None:
        return 1.0
    if cod_year > run_year:
        return 0.0
    if cod_year == run_year:
        return cod_year_share
    return 1.0


def load_cod_year_map(data_dir: Path | None = None) -> dict[int, int]:
    """Build a ``{plant_code: commissioning_year}`` map.

    The curated master registry (``year_built``) is authoritative; the EIA-860
    generator parquet (``operating_year``, the earliest unit per plant) fills in
    any plant code the registry does not carry.
    """
    cod: dict[int, int] = {}

    if _EIA860.exists():
        df = pd.read_parquet(_EIA860, columns=["plant_id", "operating_year"])
        oy = pd.to_numeric(df["operating_year"], errors="coerce")
        pc = pd.to_numeric(df["plant_id"], errors="coerce")
        per_plant = (
            pd.DataFrame({"pc": pc, "oy": oy}).dropna()
            .groupby("pc")["oy"].min()
        )
        for code, year in per_plant.items():
            cod[int(code)] = int(year)

    # Registry wins where it has a value (curated, ERCOT-complete).
    if _REGISTRY.exists():
        reg = pd.read_csv(_REGISTRY, usecols=["plantid", "year_built"])
        reg = reg.dropna(subset=["plantid", "year_built"])
        for code, year in zip(reg["plantid"], reg["year_built"]):
            cod[int(code)] = int(year)

    return cod


def ramp_bins(
    bins: pd.DataFrame,
    run_year: int,
    cod_map: dict[int, int],
    cod_year_share: float = COD_YEAR_DEFAULT_SHARE,
    capacity_col: str = "capacity_mw",
    code_col: str = "Plant_Code",
) -> pd.DataFrame:
    """Scale / drop per-plant bin capacities by commissioning year.

    Returns a new DataFrame with ``capacity_col`` ramped and rows for not-yet-
    built plants removed. Logs the capacity dropped and pro-rated.
    """
    if bins is None or bins.empty or code_col not in bins.columns:
        return bins
    out = bins.copy()
    codes = pd.to_numeric(out[code_col], errors="coerce")
    frac = codes.map(
        lambda c: online_fraction(
            cod_map.get(int(c)) if pd.notna(c) else None, run_year, cod_year_share
        )
    )
    before = float(out[capacity_col].sum())
    dropped = float(out.loc[frac == 0.0, capacity_col].sum())
    prorated = float(
        (out.loc[(frac > 0.0) & (frac < 1.0), capacity_col]
         * (1.0 - frac[(frac > 0.0) & (frac < 1.0)])).sum()
    )
    out[capacity_col] = out[capacity_col] * frac
    out = out[frac > 0.0].reset_index(drop=True)
    if dropped or prorated:
        logger.info(
            "COD ramp (bins, %d): dropped %.0f MW (built > %d), pro-rated "
            "%.0f MW of COD-year capacity; fleet %.0f -> %.0f MW",
            run_year, dropped, run_year, prorated, before, float(out[capacity_col].sum()),
        )
    return out


def ramp_fleet(
    gens: list,
    run_year: int,
    cod_map: dict[int, int] | None = None,
    cod_year_share: float = COD_YEAR_DEFAULT_SHARE,
) -> list:
    """Scale / drop :class:`Generator` objects by commissioning year.

    Each generator's commissioning year is taken from ``cod_map`` (by
    ``plant_code``) when present, else from its own ``online_year``. Units built
    after ``run_year`` are dropped; COD-year units have ``pmax_mw`` / ``pmin_mw``
    pro-rated.
    """
    out = []
    dropped_mw = 0.0
    prorated_mw = 0.0
    for g in gens:
        cod_year = None
        code = int(getattr(g, "plant_code", 0) or 0)
        if cod_map and code in cod_map:
            cod_year = cod_map[code]
        elif getattr(g, "online_year", None):
            # online_year defaults to 2000 for unset fleets; treat that sentinel
            # as "vintage unknown" so a real pre-run-year unit is not dropped.
            oy = int(g.online_year)
            cod_year = oy if oy > 2000 else None
        frac = online_fraction(cod_year, run_year, cod_year_share)
        if frac <= 0.0:
            dropped_mw += float(getattr(g, "pmax_mw", 0.0))
            continue
        if frac < 1.0:
            prorated_mw += float(getattr(g, "pmax_mw", 0.0)) * (1.0 - frac)
            out.append(g.model_copy(update={
                "pmax_mw": g.pmax_mw * frac,
                "pmin_mw": g.pmin_mw * frac,
            }))
        else:
            out.append(g)
    if dropped_mw or prorated_mw:
        logger.info(
            "COD ramp (fleet, %d): dropped %.0f MW (built > %d), pro-rated "
            "%.0f MW of COD-year capacity",
            run_year, dropped_mw, run_year, prorated_mw,
        )
    return out
