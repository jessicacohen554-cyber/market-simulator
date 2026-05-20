"""Per-ISO hydro energy budgets and min/max MW.

Conventional hydro (EIA prime mover ``HY``, fuel ``WAT``) is not a flat
thermal block: it is energy-limited. A reservoir holds a finite amount of
water, so a plant can pick *when* within a month to generate but not *how
much* in total — its monthly energy is fixed by inflow. This module loads
that inter-temporal budget from EIA-923 monthly net generation and the
power envelope (max MW = nameplate, min MW = an optional run-of-river floor)
from EIA-860, returning arrays keyed to the hydro generator subset of an
ISO. Pumped storage (prime mover ``PS``) is excluded — it is a storage
resource, not energy-limited inflow hydro.

The returned :class:`HydroBudget` feeds the optional hydro constraint family
in :mod:`market_sim.model.dispatch`. With no budget loaded the dispatch LP
is unchanged, so the module is purely additive (default off).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.eia923 import (
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.data.fleet import (
    EIA_860_DIR,
    EIA_860_PARQUET_NAME,
    ISO_TO_BA_CODE,
)

logger = logging.getLogger(__name__)

# EIA prime-mover code for conventional (inflow) hydro. Pumped storage is
# ``PS`` and is deliberately excluded — it is a storage unit, not an
# energy-limited inflow resource, and is modeled via the storage block.
HYDRO_PRIME_MOVER: str = "HY"

# Number of calendar months — the budget is always twelve entries wide so a
# month with no reported generation simply carries a zero budget.
_MONTHS_PER_YEAR: int = 12


@dataclass(frozen=True)
class HydroBudget:
    """Monthly energy budget and MW envelope for an ISO's hydro fleet.

    All arrays are keyed row-for-row to the hydro generator subset, ordered
    by ascending EIA plant id. ``monthly_energy`` is the inter-temporal
    energy limit that the dispatch budget constraint enforces; ``min_mw`` and
    ``max_mw`` are the per-hour power bounds.

    Attributes:
        plant_ids: EIA plant ids of the hydro subset, shape ``(n_hydro,)``.
        plant_names: Plant names aligned to ``plant_ids``.
        zones: Model zone of each plant aligned to ``plant_ids`` (empty
            strings when no zone lookup was available).
        monthly_energy: Monthly net generation in MWh, shape
            ``(n_hydro, 12)`` with column 0 = January. The dispatch budget
            cap: ``sum_{t in month m} P[g,t] <= monthly_energy[g, m]``.
        min_mw: Run-of-river minimum flow in MW, shape ``(n_hydro,)``.
            Zero unless a ``min_flow_fraction`` was requested.
        max_mw: Nameplate capacity in MW, shape ``(n_hydro,)``.
    """

    plant_ids: np.ndarray
    plant_names: list[str]
    zones: list[str]
    monthly_energy: np.ndarray
    min_mw: np.ndarray
    max_mw: np.ndarray

    @property
    def n_hydro(self) -> int:
        """Return the number of hydro generators in the subset."""
        return len(self.plant_ids)

    def monthly_min_energy(self, hours_per_month: np.ndarray) -> np.ndarray:
        """Return the minimum monthly energy floor from the min-flow MW.

        The run-of-river ``min_mw`` floor sustained over a month is a
        minimum monthly *energy* ``min_mw * hours_in_month``; this is the
        lower-bound companion to ``monthly_energy`` consumed by the dispatch
        hydro constraint family (``hydro_monthly_min``).

        Args:
            hours_per_month: Number of hours in each of the twelve months,
                shape ``(12,)``.

        Returns:
            The ``(n_hydro, 12)`` minimum-energy floor in MWh.
        """
        hpm = np.asarray(hours_per_month, dtype=float)
        return self.min_mw[:, np.newaxis] * hpm[np.newaxis, :]

    def align_to(
        self, plant_codes: np.ndarray | list[int]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Reorder the budget arrays to a fleet's hydro generator order.

        Given the EIA plant codes of a fleet's hydro generators (in fleet
        order), return the subset of those generators that this budget
        covers and the budget arrays reindexed to match them. Generators
        whose plant code is absent from the budget are dropped, so the
        returned ``local_idx`` selects the covered generators within the
        input ``plant_codes``.

        Args:
            plant_codes: EIA plant code of each hydro generator, in fleet
                order, shape ``(n_fleet_hydro,)``.

        Returns:
            Tuple ``(local_idx, monthly_energy, min_mw, max_mw)`` where
            ``local_idx`` indexes into ``plant_codes`` (the covered
            generators) and the three arrays are reordered to that subset.
        """
        codes = np.asarray(plant_codes, dtype=int)
        budget_pos = {int(pid): i for i, pid in enumerate(self.plant_ids)}
        local_idx = np.array(
            [i for i, c in enumerate(codes) if int(c) in budget_pos], dtype=int
        )
        budget_rows = np.array(
            [budget_pos[int(codes[i])] for i in local_idx], dtype=int
        )
        return (
            local_idx,
            self.monthly_energy[budget_rows],
            self.min_mw[budget_rows],
            self.max_mw[budget_rows],
        )


def hours_per_month(hours: int = 8760) -> np.ndarray:
    """Return the number of hours in each of the twelve calendar months.

    Uses the same representative non-leap year (2023) as the dispatch
    hour-to-month mapping, so an hour horizon and its monthly budget share
    one calendar.

    Args:
        hours: Length of the hour horizon to partition. Defaults to 8760.

    Returns:
        A ``(12,)`` integer array of hours per month (index 0 = January).
    """
    from market_sim.data.fleet import _hour_to_month_index

    return np.bincount(
        _hour_to_month_index(hours), minlength=_MONTHS_PER_YEAR
    ).astype(int)


def _load_hydro_generation(iso: str, year: int) -> pd.DataFrame:
    """Return one row per hydro plant with its twelve monthly netgen columns.

    Filters the EIA-923 monthly-generation table to conventional hydro
    (prime mover ``HY``) in the ISO's balancing authority for ``year`` and
    sums any multiple rows per plant. Negative monthly net generation
    (station-service draw on a low-inflow month) is clipped to zero so the
    budget is a non-negative energy cap.
    """
    ba_code = ISO_TO_BA_CODE.get(iso.upper())
    gen = load_monthly_generation()
    subset = gen[
        (gen["prime_mover"] == HYDRO_PRIME_MOVER)
        & (gen["year"] == year)
    ]
    if ba_code is not None and "ba_code" in subset.columns:
        subset = subset[subset["ba_code"] == ba_code]
    if subset.empty:
        return subset

    mcols = monthly_netgen_columns()
    agg = subset.groupby("plant_id", as_index=False).agg(
        {"plant_name": "first", **{c: "sum" for c in mcols}}
    )
    agg[mcols] = agg[mcols].clip(lower=0.0)
    return agg


def _load_hydro_nameplate(iso: str) -> dict[int, float]:
    """Return ``{plant_id: total nameplate MW}`` for the ISO's hydro plants.

    Reads the committed EIA-860 generator parquet, filters to conventional
    hydro (prime mover ``HY``) in the ISO's balancing authority, and sums
    nameplate capacity across a plant's hydro units. Pumped storage
    (``PS``) is excluded.
    """
    parquet_path = Path(EIA_860_DIR) / EIA_860_PARQUET_NAME
    if not parquet_path.exists():
        return {}
    df = pd.read_parquet(parquet_path)
    ba_code = ISO_TO_BA_CODE.get(iso.upper())
    mask = df["prime_mover"] == HYDRO_PRIME_MOVER
    if ba_code is not None and "balancing_authority_code" in df.columns:
        mask &= df["balancing_authority_code"] == ba_code
    hydro = df[mask]
    if hydro.empty:
        return {}
    totals = hydro.groupby("plant_id")["nameplate_capacity_mw"].sum()
    return {int(pid): float(mw) for pid, mw in totals.items()}


def _zone_lookup(iso: str) -> dict[int, str]:
    """Return ``{plant_id: zone}`` from eGRID geography, empty on failure.

    Mirrors the best-effort zone resolution used by the fleet loader; a
    missing or failed lookup yields an empty map and hydro plants get a
    blank zone label rather than aborting the budget load.
    """
    try:
        from market_sim.data.zone_assignment import build_zone_lookup

        return {int(k): v for k, v in build_zone_lookup(iso).items()}
    except Exception:
        logger.warning("hydro zone lookup failed for %s — zones left blank", iso)
        return {}


def load_hydro_budget(
    iso: str,
    year: int,
    min_flow_fraction: float = 0.0,
) -> HydroBudget:
    """Load an ISO's hydro monthly energy budget and MW envelope.

    Joins EIA-923 monthly hydro net generation (the energy budget) to
    EIA-860 hydro nameplate (the max-MW envelope) on EIA plant id. The
    subset is the hydro plants that reported generation in ``year``; a plant
    missing from EIA-860 falls back to its peak monthly average power as the
    nameplate estimate, so no generating hydro plant is dropped.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year of the monthly generation to load.
        min_flow_fraction: Run-of-river minimum flow as a fraction of
            nameplate. ``0.0`` (default) leaves ``min_mw`` at zero — no
            enforced minimum.

    Returns:
        A :class:`HydroBudget` keyed to the hydro generator subset, ordered
        by ascending plant id.

    Raises:
        FileNotFoundError: When the EIA-923 monthly-generation parquet is
            absent (see :func:`market_sim.data.eia923.load_monthly_generation`).
        ValueError: When no hydro generation is found for ``(iso, year)``.
    """
    gen = _load_hydro_generation(iso, year)
    if gen.empty:
        raise ValueError(f"No EIA-923 hydro generation for {iso} in {year}")

    nameplate = _load_hydro_nameplate(iso)
    zones = _zone_lookup(iso)
    mcols = monthly_netgen_columns()
    gen = gen.sort_values("plant_id").reset_index(drop=True)

    plant_ids = gen["plant_id"].to_numpy(dtype=int)
    plant_names = [str(n) for n in gen["plant_name"].tolist()]
    monthly_energy = gen[mcols].to_numpy(dtype=float)

    # Max MW: EIA-860 nameplate where available, else the plant's peak
    # monthly average power (peak monthly MWh / hours in that month) so an
    # off-register small hydro plant still gets a usable power cap.
    hpm = hours_per_month().astype(float)  # standard 8760-hour calendar
    peak_avg_mw = (monthly_energy / hpm[np.newaxis, :]).max(axis=1)
    max_mw = np.array(
        [nameplate.get(int(pid), float(peak_avg_mw[i])) for i, pid in enumerate(plant_ids)],
        dtype=float,
    )
    min_mw = float(min_flow_fraction) * max_mw
    plant_zones = [zones.get(int(pid), "") for pid in plant_ids]

    logger.info(
        "Loaded %s %d hydro budget: %d plants, %.1f GWh annual, %.0f MW nameplate",
        iso, year, len(plant_ids),
        monthly_energy.sum() / 1000.0, max_mw.sum(),
    )
    return HydroBudget(
        plant_ids=plant_ids,
        plant_names=plant_names,
        zones=plant_zones,
        monthly_energy=monthly_energy,
        min_mw=min_mw,
        max_mw=max_mw,
    )
