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
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.eia923 import (
    load_monthly_generation,
    monthly_netgen_columns,
)
from market_sim.config.constants import VOM
from market_sim.data.fleet import (
    EIA_860_DIR,
    EIA_860_PARQUET_NAME,
    Generator,
    ba_codes,
)

logger = logging.getLogger(__name__)


def _use_clean() -> bool:
    """Whether to read curated clean parquet instead of the raw inputs.

    Gated by the ``MARKET_SIM_USE_CLEAN`` environment variable, **default OFF**.
    When unset or falsey the module reads raw inputs exactly as before; when
    truthy the plant-registry reference lookup is read through the frozen clean
    seam (:func:`scripts.lib.clean_io.read_clean`). The flag only chooses the
    data *source* — the clean table is curated from the same raw file, so the
    resolved lookup is identical either way.
    """
    return os.environ.get("MARKET_SIM_USE_CLEAN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


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
        hydro constraint family (``hydro_monthly_min``). The floor is clipped
        to ``monthly_energy`` so the two-sided dispatch row stays feasible
        (lower <= upper) in low-inflow months, where a nameplate-fraction
        floor can exceed the measured budget (CAISO small hydro runs dry
        autumns at a few percent of nameplate-hours).

        Args:
            hours_per_month: Number of hours in each of the twelve months,
                shape ``(12,)``.

        Returns:
            The ``(n_hydro, 12)`` minimum-energy floor in MWh.
        """
        hpm = np.asarray(hours_per_month, dtype=float)
        floor = self.min_mw[:, np.newaxis] * hpm[np.newaxis, :]
        return np.minimum(floor, self.monthly_energy)

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

    return np.bincount(_hour_to_month_index(hours), minlength=_MONTHS_PER_YEAR).astype(
        int
    )


def hydro_budget_period_hours(
    iso: str, plant_ids: np.ndarray | list[int], config: object
) -> np.ndarray | None:
    """Return each hydro generator's budget period in hours, or ``None``.

    Reads :data:`~market_sim.config.constants.HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`
    — the per-project registry whose every entry carries the published governing
    instrument it comes from — and maps it onto a fleet's hydro generators.

    A plant **absent from the registry** is returned as ``0``, the sentinel for
    "keep the calendar month", so the refinement is strictly opt-in: an ISO with
    no registry entry, or the flag off, yields ``None`` and the caller builds the
    unchanged monthly rows. This is what makes the mechanism a byte-identical
    no-op everywhere it is not explicitly grounded (rule 14 ``[R-ACCURATE]``:
    never invent an instrument we have not read).

    Args:
        iso: ISO code, e.g. ``"NYISO"``.
        plant_ids: EIA plant code of each hydro generator, in fleet order.
        config: Scenario config; the mechanism is gated on its
            ``hydro_budget_period_by_instrument`` flag.

    Returns:
        An ``(n_hydro,)`` integer array of period lengths in hours (``0`` =
        monthly), or ``None`` when the flag is off, the ISO has no registry
        entry, or no generator in this fleet matches one — in all of which cases
        the LP is unchanged.
    """
    if not getattr(config, "hydro_budget_period_by_instrument", False):
        return None
    from market_sim.config.constants import HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT

    registry = HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT.get(str(iso).upper())
    if not registry:
        return None
    codes = np.asarray(plant_ids, dtype=int)
    periods = np.array([int(registry.get(int(c), 0)) for c in codes], dtype=int)
    if not periods.any():
        return None
    return periods


def allocate_period_energy(
    monthly_energy: np.ndarray, period_hours: int, hours: int = 8760
) -> tuple[np.ndarray, np.ndarray]:
    """Split a monthly energy budget into fixed-length sub-monthly periods.

    A shortened budget period conserves each **month's** measured total — which
    stays the source of truth — but forbids moving that energy between periods
    inside the month. Energy is allocated to a period in proportion to how many
    of the period's hours fall in each month, so a period straddling a month
    boundary is budgeted correctly and the monthly totals are preserved exactly.

    The allocation within a month is **flat**, and for the projects this is
    applied to that is the measured-inflow-consistent choice rather than an
    assumption: nyiso-219 measured Robert Moses Niagara's and St. Lawrence's own
    basin discharge carrying essentially no day-to-day signal (within-month daily
    r **0.079** and **0.080**), because both sit on regulated Great-Lakes
    outflow. **Zero fitted scalars**, and nothing here is pinned to a measured
    *outcome* — the monthly level is the same measured budget the LP already
    uses, only re-partitioned in time.

    **Periods are aligned WITHIN months** — the period counter restarts at each
    month boundary, so the final period of a month may be short (1-7 days for a
    weekly period). This is deliberate and load-bearing: a period straddling a
    month boundary would let energy move ACROSS that boundary, which breaks the
    exact conservation of each month's measured total (measured here at up to
    82,696 MWh of drift for a 168 h period before the alignment was added). The
    monthly measured total is the calibration anchor the keeper already matches
    at month-energy r ~ 1.000, and this mechanism must not disturb it — it
    constrains *when within a month* energy is used, never *how much*. The cost
    is that a month-aligned week is not exactly the instrument's calendar week;
    that is immaterial to a constraint whose content is "no banking beyond about
    a week", whereas losing the monthly anchor would not be.

    Args:
        monthly_energy: ``(n_hydro, 12)`` monthly energy caps in MWh.
        period_hours: Length of each period in hours (e.g. 24 or 168).
        hours: Length of the hour horizon. Defaults to 8760.

    Returns:
        Tuple ``(period_energy, period_index)`` where ``period_energy`` has
        shape ``(n_hydro, n_periods)`` in MWh and ``period_index`` is the
        ``(T,)`` period of each hour.

    Raises:
        ValueError: If ``period_hours`` is not a positive number of hours.
    """
    if period_hours <= 0:
        raise ValueError(f"period_hours must be positive, got {period_hours}")
    from market_sim.data.fleet import _hour_to_month_index

    month_of_hour = np.asarray(_hour_to_month_index(hours), dtype=int)  # (T,)
    ph = int(period_hours)

    # Month-aligned periods (see docstring): the period counter restarts each
    # month, so no period straddles a month boundary and monthly totals are
    # conserved exactly. Built vectorised -- no Python loop over hours (rule 2).
    hpm = np.bincount(month_of_hour, minlength=_MONTHS_PER_YEAR)  # (12,)
    first_hour = np.concatenate(([0], np.cumsum(hpm)[:-1]))  # (12,) month start
    hour_in_month = np.arange(hours, dtype=int) - first_hour[month_of_hour]
    local_period = hour_in_month // ph  # period within its month
    periods_per_month = -(-hpm // ph)  # ceil division: periods each month holds
    month_offset = np.concatenate(([0], np.cumsum(periods_per_month)[:-1]))
    period_index = month_offset[month_of_hour] + local_period  # (T,)
    n_periods = int(periods_per_month.sum())

    # (n_periods, 12) count of each period's hours falling in each month, and the
    # (12,) total hours per month -- both by one vectorised bincount over the
    # flat (period, month) pair index. No Python loop over hours (rule 2).
    pair = period_index * _MONTHS_PER_YEAR + month_of_hour
    counts = np.bincount(pair, minlength=n_periods * _MONTHS_PER_YEAR).reshape(
        n_periods, _MONTHS_PER_YEAR
    )
    hpm = np.bincount(month_of_hour, minlength=_MONTHS_PER_YEAR).astype(float)
    share = counts / np.where(hpm > 0, hpm, 1.0)  # (n_periods, 12)

    energy = np.asarray(monthly_energy, dtype=float)  # (n_hydro, 12)
    period_energy = energy @ share.T  # (n_hydro, n_periods)
    return period_energy, period_index


def resolve_hydro_year_multiplier(hydro_year: str) -> float:
    """Return the budget multiplier for a ``hydro_year`` scenario lever.

    Maps the forecast wet/dry water-year lever (``"dry"`` / ``"normal"`` /
    ``"wet"``) to its level multiplier via
    :data:`market_sim.config.constants.HYDRO_YEAR_MULTIPLIER`. ``"normal"``
    (the default) returns ``1.0``.

    Args:
        hydro_year: The scenario lever, one of the keys of
            ``HYDRO_YEAR_MULTIPLIER``.

    Returns:
        The multiplier to apply to the normal-water-year hydro budget.

    Raises:
        ValueError: When ``hydro_year`` is not a recognised lever.
    """
    from market_sim.config.constants import HYDRO_YEAR_MULTIPLIER

    try:
        return float(HYDRO_YEAR_MULTIPLIER[hydro_year])
    except KeyError as exc:
        raise ValueError(
            f"hydro_year must be one of {sorted(HYDRO_YEAR_MULTIPLIER)}, "
            f"got {hydro_year!r}"
        ) from exc


def eia930_wat_level_folded(iso: str, year: int) -> bool:
    """Return True when ``(iso, year)``'s EIA-930 ``NG: WAT`` folds pumped storage.

    True for a BA in
    :data:`~market_sim.config.constants.EIA930_PS_FOLDED_INTO_WAT` (no
    ``NG: PS`` column at all, so every year is folded), and for a BA in
    :data:`~market_sim.config.constants.EIA930_PS_SPLIT_COMPLETE_FROM` in any
    year before its first wholly-split calendar year (the seam year itself
    counts as folded: a year is admissible on one source basis only, never
    spliced mid-year). A True year's ``NG: WAT`` is a conventional-hydro PLUS
    pumped-storage-discharge series and is not an admissible LEVEL for the
    conventional-only (EIA-923 ``HY``) unit population — rule 14
    ``[R-ACCURATE]``; miso-109 (standing fold) / neiso-72 (time split).
    """
    from market_sim.config.constants import (
        EIA930_PS_FOLDED_INTO_WAT,
        EIA930_PS_SPLIT_COMPLETE_FROM,
    )

    iso_u = iso.upper()
    if iso_u in EIA930_PS_FOLDED_INTO_WAT:
        return True
    first_clean = EIA930_PS_SPLIT_COMPLETE_FROM.get(iso_u)
    return first_clean is not None and int(year) < int(first_clean)


def full_forward_climatology_years(as_of_year: int) -> tuple[int, ...]:
    """Return the T1-FF as-of hydro climatology window (FH-1, plan §4 row 11).

    A full-forward hindcast standing at ``as_of_year`` may build its
    normal-water-year climatology only from :data:`HYDRO_CLIMATOLOGY_YEARS`
    members **at or before** that year — the fixed constant would otherwise
    average future water years into a historic base (a 2021-base run drew four
    of its five years from its own future) — and never from quarantined 2022
    (rule 22; the hindcast bridge year's data is never read). A base-2023
    window is therefore ``(2021, 2023)`` and a base-2021 window ``(2021,)`` —
    a single water year, which is a *disclosed thinness finding*, never a
    reason to widen the window (rule 13: the window regenerates from the
    as-of date, it is not tuned).

    Args:
        as_of_year: The information cutoff (the T1-FF base year /
            ``crossover_forward_year``).

    Returns:
        The trimmed climatology years, ascending (possibly a single year).
    """
    from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS

    return tuple(
        y
        for y in HYDRO_CLIMATOLOGY_YEARS
        if y <= int(as_of_year) and y not in _HYDRO_QUARANTINED_YEARS
    )


# Rule-22 quarantined years excluded from any as-of hydro climatology (FH-1):
# 2022 is the hindcast bridge year — evolved, never solved, its data never
# read. (2026+ never enters a trimmed window because every T1-FF as-of year is
# <= 2023 by the harness's window validation; membership here is belt-and-
# braces symmetry with the emission-rate trim.)
_HYDRO_QUARANTINED_YEARS: frozenset[int] = frozenset({2022, 2026})


def forecast_monthly_hydro(
    iso: str,
    hydro_year: str = "normal",
    climatology_years: "tuple[int, ...] | list[int] | None" = None,
) -> np.ndarray | None:
    """Return a forecast hydro monthly-energy budget level (MWh).

    The forward analogue of the measured EIA-930 ``NG: WAT`` backcast level:
    the normal-water-year climatology
    (:func:`market_sim.data.eia_loader.climatological_monthly_hydro`) scaled
    by the wet/dry ``hydro_year`` lever
    (:func:`resolve_hydro_year_multiplier`). This is a *level* input — it is
    passed as ``monthly_target_mwh`` to :func:`load_hydro_budget`, which
    rescales each month's per-plant budget to it while preserving the
    within-month per-plant shares; the inter-temporal dispatch mechanism is
    unchanged. Returns ``None`` when the ISO has no measured hydro to build a
    climatology from, in which case the caller leaves the budget at its
    EIA-923 level.

    Args:
        iso: ISO identifier, e.g. ``"CAISO"``.
        hydro_year: Wet/dry water-year scenario lever (``"dry"`` /
            ``"normal"`` / ``"wet"``). ``"normal"`` leaves the climatology
            unscaled.
        climatology_years: Historical years to average for the normal
            water year. ``None`` (default) uses
            :data:`market_sim.config.constants.HYDRO_CLIMATOLOGY_YEARS`.

    Returns:
        The ``(12,)`` forecast monthly hydro budget in MWh, or ``None`` when
        no climatology is available for ``iso``.
    """
    from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS
    from market_sim.data.eia_loader import climatological_monthly_hydro

    window = (
        tuple(int(y) for y in climatology_years)
        if climatology_years is not None
        else HYDRO_CLIMATOLOGY_YEARS
    )
    if any(eia930_wat_level_folded(iso, y) for y in window):
        # Rule 14 [R-ACCURATE] — the FORWARD half of the level fix. A window
        # year whose `NG: WAT` folds pumped-storage gross discharge (a
        # flat-registry BA in every year, miso-110; a time-split BA in the
        # years before its first wholly-split year, neiso-72) would
        # contaminate the climatology mean exactly as it contaminated the
        # backcast pin, so the whole climatology stays on ONE basis and the
        # forward level comes from EIA-923 `HY` — the same series, and the
        # same plant population, that the per-plant budget and the corrected
        # backcast level already use. Same window constant, same 12-vector
        # MWh contract, same wet/dry lever below; zero free parameters, and
        # no reconciliation factor between the two series (miso-109 §2 /
        # neiso-72 §4a measured that none is identifiable — rules 5/13/22).
        # For a time-split BA this branch un-arms ITSELF once the window
        # holds only wholly-split years — the guard regenerates from the
        # data, no retuning (rule 13's forward story).
        base = climatological_monthly_hydro_923(iso, climatology_years)
    else:
        base = climatological_monthly_hydro(iso, climatology_years)
    if base is None:
        return None
    return base * resolve_hydro_year_multiplier(hydro_year)


def complete_923_hydro_years(
    iso: str,
    years: "tuple[int, ...] | list[int] | None" = None,
) -> tuple[int, ...]:
    """Return the ``years`` whose EIA-923 ``HY`` filing is a COMPLETE census.

    The coverage gate behind :func:`climatological_monthly_hydro_923`. A year
    is admitted only when both hold:

    * it is no newer than
      :data:`market_sim.data.eia923.EIA923_LATEST_FINAL_VINTAGE` — vintages past
      the latest final release are monthly early releases by construction; and
    * its ``HY`` plant census is at least
      :data:`~market_sim.config.constants.EIA923_COMPLETE_FILING_CENSUS_FRACTION`
      of the ISO's modal census over ``years`` — a per-ISO check that also
      catches a partial filing *inside* a nominally final vintage.

    Averaging an early release into a climatology would measure source coverage
    rather than hydrology (miso-109's "2025 trap"), so this is a data-quality
    filter, never a tuned window: it can only ever *remove* an incomplete year.

    Args:
        iso: ISO identifier, e.g. ``"MISO"``.
        years: Candidate years. ``None`` (default) uses
            :data:`market_sim.config.constants.HYDRO_CLIMATOLOGY_YEARS`.

    Returns:
        The admitted years, ascending. Empty when the ISO has no complete
        ``HY`` filing in the window.
    """
    from market_sim.config.constants import (
        EIA923_COMPLETE_FILING_CENSUS_FRACTION,
        HYDRO_CLIMATOLOGY_YEARS,
    )
    from market_sim.data.eia923 import EIA923_LATEST_FINAL_VINTAGE

    if years is None:
        years = HYDRO_CLIMATOLOGY_YEARS
    candidates = sorted({int(y) for y in years})
    gen = load_monthly_generation()
    census = {y: _load_hydro_generation(iso, y, gen=gen).shape[0] for y in candidates}
    present = [n for n in census.values() if n]
    if not present:
        return ()
    modal = float(np.median(present))
    floor = EIA923_COMPLETE_FILING_CENSUS_FRACTION * modal
    return tuple(
        y
        for y in candidates
        if y <= EIA923_LATEST_FINAL_VINTAGE and census[y] and census[y] >= floor
    )


def climatological_monthly_hydro_923(
    iso: str,
    years: "tuple[int, ...] | list[int] | None" = None,
) -> np.ndarray | None:
    """Return the normal-water-year monthly hydro climatology from EIA-923 (MWh).

    The EIA-923 ``HY`` analogue of
    :func:`market_sim.data.eia_loader.climatological_monthly_hydro`, and the
    forward level for the BAs in
    :data:`~market_sim.config.constants.EIA930_PS_FOLDED_INTO_WAT`, whose
    EIA-930 ``NG: WAT`` series folds in pumped-storage discharge and so is not
    an admissible level for a conventional-hydro-only unit population (rule 14
    ``[R-ACCURATE]``; miso-109 for the backcast half, miso-110 for this one).

    Same contract as the EIA-930 version — a ``(12,)`` MWh vector, index 0 =
    January, built over the shared
    :data:`~market_sim.config.constants.HYDRO_CLIMATOLOGY_YEARS` window and
    scaled afterwards by the wet/dry lever in :func:`forecast_monthly_hydro`.
    The plant population is exactly :func:`_load_hydro_generation`'s, i.e. the
    one :func:`load_hydro_budget` builds the per-plant shares from, so the
    level and the units are the same population.

    Only years whose filing carries a complete plant census are averaged
    (:func:`complete_923_hydro_years`), and the REALISED window is logged
    because it will not in general equal the window constant — the two sources
    supply different years (miso-110: MISO realises 2021-2024 here against
    2021+2023-2025 on the EIA-930 side). A climatology delta between the two
    therefore mixes the pumped-storage fold with a WINDOW MISMATCH and is never
    on its own evidence of a fold.

    Args:
        iso: ISO identifier, e.g. ``"MISO"``.
        years: Historical years to average. ``None`` (default) uses
            :data:`market_sim.config.constants.HYDRO_CLIMATOLOGY_YEARS`.

    Returns:
        The ``(12,)`` mean monthly conventional-hydro net generation in MWh, or
        ``None`` when no year in the window has a complete EIA-923 ``HY``
        filing for ``iso``.
    """
    from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS

    window = complete_923_hydro_years(iso, years)
    requested = (
        HYDRO_CLIMATOLOGY_YEARS if years is None else tuple(int(y) for y in years)
    )
    if not window:
        logger.warning(
            "%s: no complete EIA-923 HY filing in the climatology window %s — "
            "no EIA-923 hydro climatology available",
            iso,
            list(requested),
        )
        return None
    gen = load_monthly_generation()
    mcols = monthly_netgen_columns()
    rows = [
        _load_hydro_generation(iso, y, gen=gen)[mcols].to_numpy(dtype=float).sum(axis=0)
        for y in window
    ]
    out = np.vstack(rows).mean(axis=0)
    logger.info(
        "%s: EIA-923 HY hydro climatology over REALISED window %s "
        "(requested %s; incomplete filings gated out) — %.4f TWh/yr",
        iso,
        list(window),
        list(requested),
        out.sum() / 1e6,
    )
    return out


def _load_hydro_generation(
    iso: str, year: int, gen: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Return one row per hydro plant with its twelve monthly netgen columns.

    Filters the EIA-923 monthly-generation table to conventional hydro
    (prime mover ``HY``) in the ISO's balancing authority for ``year`` and
    sums any multiple rows per plant. Negative monthly net generation
    (station-service draw on a low-inflow month) is clipped to zero so the
    budget is a non-negative energy cap.

    Args:
        iso: ISO identifier, e.g. ``"MISO"``.
        year: Calendar year to filter to.
        gen: Optional pre-loaded monthly-generation table, so a multi-year
            caller (the EIA-923 climatology) reads the ~10 MB parquet once
            instead of once per year. ``None`` (default) loads it.
    """
    # Membership over every BA the region comprises (NWPP is 17; the 1:1
    # regions are a one-element tuple, so ``isin`` selects the rows ``==``
    # did) — the NWPP-10 §3 repair of the scalar-inverse silent failure.
    codes = ba_codes(iso)
    if gen is None:
        gen = load_monthly_generation()
    subset = gen[(gen["prime_mover"] == HYDRO_PRIME_MOVER) & (gen["year"] == year)]
    if codes and "ba_code" in subset.columns:
        subset = subset[subset["ba_code"].isin(codes)]
    if subset.empty:
        return subset

    mcols = monthly_netgen_columns()
    agg = subset.groupby("plant_id", as_index=False).agg(
        {"plant_name": "first", **{c: "sum" for c in mcols}}
    )
    agg[mcols] = agg[mcols].clip(lower=0.0)
    # Drop plants with no net generation in the year: they carry a zero
    # budget (and, when also absent from EIA-860, a zero nameplate fallback),
    # i.e. a degenerate all-zero unit.
    return agg[agg[mcols].sum(axis=1) > 0.0].reset_index(drop=True)


def load_reference_hydro_nameplate(iso: str) -> dict[int, float]:
    """Return ``{plant_id: nameplate_mw}`` for the ISO's conventional-hydro
    plants from the plant-registry reference table.

    Reads the curated clean parquet when ``MARKET_SIM_USE_CLEAN`` is set
    (``read_clean("reference", market="plant-registry")``) and the raw
    ``master-plant-registry.csv`` otherwise; both backends yield the same map
    (the clean table is curated from that CSV). The rows are filtered to the
    ISO's balancing authority and prime mover ``HY`` — pumped storage (``PS``)
    is excluded, mirroring :func:`_load_hydro_nameplate`. Returns an empty dict
    when the source is absent or the ISO has no balancing-authority code.
    """
    codes = ba_codes(iso)
    if not codes:
        return {}

    cols = ["plant_id", "ba_code", "prime_mover", "nameplate_capacity_mw"]
    if _use_clean():
        from scripts.lib.clean_io import read_clean

        df = read_clean("reference", market="plant-registry", columns=cols)
    else:
        from market_sim.config.paths import PLANT_REGISTRY_CSV

        if not PLANT_REGISTRY_CSV.exists():
            return {}
        df = pd.read_csv(
            PLANT_REGISTRY_CSV,
            usecols=["plantid", "ba_code", "prime_mover", "nameplate_capacity_mw"],
        ).rename(columns={"plantid": "plant_id"})

    sub = df[(df["prime_mover"] == HYDRO_PRIME_MOVER) & (df["ba_code"].isin(codes))]
    out: dict[int, float] = {}
    for pid, mw in zip(sub["plant_id"], sub["nameplate_capacity_mw"]):
        if pid != pid or mw != mw:  # NaN plant_id / nameplate
            continue
        out[int(pid)] = float(mw)
    return out


def _load_hydro_nameplate(iso: str) -> dict[int, float]:
    """Return ``{plant_id: total nameplate MW}`` for the ISO's hydro plants.

    Reads the committed EIA-860 generator parquet, filters to conventional
    hydro (prime mover ``HY``) in the ISO's balancing authority, and sums
    nameplate capacity across a plant's hydro units. Pumped storage
    (``PS``) is excluded.

    When ``MARKET_SIM_USE_CLEAN`` is set (default OFF), the plant-registry
    reference table supplements any plant the EIA-860 file missed; EIA-860
    stays authoritative (``setdefault``). With the flag off the supplement is
    skipped, so the default raw behaviour is unchanged.
    """
    parquet_path = Path(EIA_860_DIR) / EIA_860_PARQUET_NAME
    out: dict[int, float] = {}
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        codes = ba_codes(iso)
        mask = df["prime_mover"] == HYDRO_PRIME_MOVER
        if codes and "balancing_authority_code" in df.columns:
            mask &= df["balancing_authority_code"].isin(codes)
        hydro = df[mask]
        if not hydro.empty:
            totals = hydro.groupby("plant_id")["nameplate_capacity_mw"].sum()
            out = {int(pid): float(mw) for pid, mw in totals.items()}

    if _use_clean():
        for pid, mw in load_reference_hydro_nameplate(iso).items():
            out.setdefault(pid, mw)
    return out


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


def _nameplate_aware_scale(
    monthly_energy: np.ndarray,
    bound: np.ndarray,
    target: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    """Rescale each month's per-plant budget to ``target`` without exceeding ``bound``.

    The uniform monthly scale factor (the pre-existing behaviour) multiplies
    every plant's month by ``target / column_sum``, which can push a small
    plant's monthly budget above ``nameplate x hours-in-month`` — energy the LP
    can never deliver, because ``P[g,t] <= pmax x availability`` bounds it. The
    clip is silent: the fleet simply under-delivers the target by the excess
    (FINDING-caiso126 K4 measured 1.335/1.269/0.169 % of the CAISO RoR class
    budget lost this way in 2023/24/25, over 30/28/15 plant-months).

    This is the physical water-filling version: cap each plant-month at its own
    ``bound`` and re-allocate the excess pro-rata over the plant-months that
    still have headroom, repeating until nothing new overflows. The month total
    is preserved exactly whenever it is physically attainable
    (``target <= bound.sum()``); where it is not, every plant is left at its
    bound and the shortfall is reported rather than hidden. Rule 14
    ``[R-ACCURATE]``: the nameplate is the accurate datum and the uniform scale
    was silently compensating against it.

    **Byte-identical below the bound**: when the first pass overflows nothing,
    the returned array is exactly ``monthly_energy * (target / column_sum)`` —
    the same expression, same order of operations, as the uniform path.

    Args:
        monthly_energy: ``(n_plants, 12)`` per-plant monthly MWh shares.
        bound: ``(n_plants, 12)`` per-plant-month deliverable MWh ceiling
            (``max_mw x hours_in_month``).
        target: ``(12,)`` monthly MWh totals to hit.

    Returns:
        ``(scaled, stats)`` — the rescaled ``(n_plants, 12)`` budget and a
        summary dict with the number of clipped plant-months, the MWh
        re-allocated and the residual shortfall.
    """
    out = np.array(monthly_energy, dtype=float)
    clipped = 0
    moved = 0.0
    short = 0.0
    for m in range(out.shape[1]):
        col = out[:, m]
        col_sum = col.sum()
        if col_sum <= 0.0:
            continue
        want = float(target[m])
        cap = bound[:, m]
        if want > cap.sum():
            # Physically unattainable this month: every plant at its ceiling.
            short += want - float(cap.sum())
            clipped += int((col > 0).sum())
            out[:, m] = cap
            continue
        scaled = col * (want / col_sum)
        free = np.ones(len(col), dtype=bool)
        while True:
            over = free & (scaled > cap)
            if not over.any():
                break
            moved += float((scaled[over] - cap[over]).sum())
            clipped += int(over.sum())
            scaled[over] = cap[over]
            free &= ~over
            rest = float(want - scaled[~free].sum())
            base = float(scaled[free].sum())
            if not free.any() or base <= 0.0:
                break
            scaled[free] *= rest / base
        out[:, m] = scaled
    return out, {"clipped": float(clipped), "moved_mwh": moved, "short_mwh": short}


def load_hydro_budget(
    iso: str,
    year: int,
    min_flow_fraction: float = 0.0,
    backfill_year: int | None = None,
    per_plant_min_flow: dict[int, float] | None = None,
    monthly_target_mwh: np.ndarray | None = None,
    nameplate_aware_target: bool = False,
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
        backfill_year: When set, plants that reported in ``backfill_year``
            but not in ``year`` are carried in at their ``backfill_year``
            monthly generation. The most recent EIA-923 vintage is an early
            release covering only the monthly-survey (large) reporters —
            CAISO 2025 carries 26 of ~185 plants, 12.3 of ~21 TWh (EIA-930)
            — so a backcast of that year passes the prior year here until
            the final annual file lands. ``None`` (default) loads ``year``
            exactly as reported.
        per_plant_min_flow: Optional ``{plant_id: fraction}`` overrides
            for specific plants. A plant's min-flow fraction is the maximum
            of ``min_flow_fraction`` and its per-plant entry (if any), so
            treaty-mandated floors on large plants are honoured even when
            the global floor is zero. Plants absent from the dict fall back
            to ``min_flow_fraction``. Intended for treaty-mandated minimum
            flows such as NYISO's Niagara/St-Lawrence obligations (see
            :data:`market_sim.config.constants.NYISO_HYDRO_TREATY_MIN_FLOW`).
        monthly_target_mwh: Optional twelve-entry vector of monthly hydro net
            generation to pin the budget level to. When set, each month's
            per-plant energy budget is scaled so its total matches the target,
            preserving the within-month per-plant shares. The target is either
            a *measured* realization for a backcast (EIA-930 ``NG: WAT``, e.g.
            to repin an incomplete EIA-923 early release: NEISO 2025's 2024
            backfill yields 6.65 TWh, mostly flat, vs the measured 5.12 TWh
            concentrated away from the dry late-summer) or a *forecast*
            normal-water-year climatology scaled by a wet/dry lever
            (:func:`forecast_monthly_hydro`). The MW envelope is left at its
            physical (unscaled) capability; only the energy budget is repinned.
            ``None`` (default) changes no existing run.
        nameplate_aware_target: When ``True``, apply ``monthly_target_mwh`` with
            :func:`_nameplate_aware_scale` — each plant-month capped at its own
            ``nameplate x hours-in-month`` and the excess re-allocated to the
            plants that can still deliver it — instead of the uniform fleet-wide
            monthly scale factor. Byte-identical to the uniform path whenever no
            plant-month exceeds its bound; fixes the FINDING-caiso126 K4 silent
            clip otherwise. Ignored when ``monthly_target_mwh`` is ``None``.
            ``False`` (default) changes no existing run.

    Returns:
        A :class:`HydroBudget` keyed to the hydro generator subset, ordered
        by ascending plant id.

    Raises:
        FileNotFoundError: When the EIA-923 monthly-generation parquet is
            absent (see :func:`market_sim.data.eia923.load_monthly_generation`).
        ValueError: When no hydro generation is found for ``(iso, year)``.
    """
    gen = _load_hydro_generation(iso, year)
    if backfill_year is not None:
        prior = _load_hydro_generation(iso, backfill_year)
        fill = prior[~prior["plant_id"].isin(set(gen["plant_id"]))]
        if not fill.empty:
            mcols = monthly_netgen_columns()
            logger.info(
                "%s %d hydro budget: backfilled %d non-reporting plants "
                "(%.1f GWh) from %d",
                iso,
                year,
                len(fill),
                fill[mcols].sum().sum() / 1000.0,
                backfill_year,
            )
            gen = pd.concat([gen, fill], ignore_index=True)
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
        [
            nameplate.get(int(pid), float(peak_avg_mw[i]))
            for i, pid in enumerate(plant_ids)
        ],
        dtype=float,
    )
    # Per-plant min-flow: take the max of the global floor and any
    # per-plant treaty override so treaty floors override without lowering
    # a higher global floor set by the caller.
    if per_plant_min_flow:
        fracs = np.array(
            [
                max(float(min_flow_fraction), per_plant_min_flow.get(int(pid), 0.0))
                for pid in plant_ids
            ],
            dtype=float,
        )
        min_mw = fracs * max_mw
    else:
        min_mw = float(min_flow_fraction) * max_mw
    plant_zones = [zones.get(int(pid), "") for pid in plant_ids]

    # Pin the monthly energy budget to a monthly hydro target total (a measured
    # EIA-930 NG: WAT realization for a backcast, or a forecast normal-water-year
    # climatology), preserving each month's per-plant shares. Done after the MW
    # envelope above so the power caps stay at physical capability and only the
    # inter-temporal energy limit is repinned.
    if monthly_target_mwh is not None:
        target = np.asarray(monthly_target_mwh, dtype=float)
        if target.shape != (_MONTHS_PER_YEAR,):
            raise ValueError(
                f"monthly_target_mwh must have {_MONTHS_PER_YEAR} entries, "
                f"got shape {target.shape}"
            )
        col_sums = monthly_energy.sum(axis=0)
        if nameplate_aware_target:
            # Rule 14: respect each plant-month's physical nameplate-hours
            # ceiling instead of letting the LP silently clip the overflow.
            monthly_energy, _stats = _nameplate_aware_scale(
                monthly_energy, max_mw[:, np.newaxis] * hpm[np.newaxis, :], target
            )
            if _stats["clipped"] or _stats["short_mwh"]:
                logger.info(
                    "%s %d hydro budget: nameplate-aware rescale re-allocated "
                    "%.1f GWh over %d clipped plant-months (%.1f GWh physically "
                    "unattainable)",
                    iso,
                    year,
                    _stats["moved_mwh"] / 1000.0,
                    int(_stats["clipped"]),
                    _stats["short_mwh"] / 1000.0,
                )
        else:
            scale = np.divide(
                target, col_sums, out=np.ones_like(target), where=col_sums > 0.0
            )
            monthly_energy = monthly_energy * scale[np.newaxis, :]
        logger.info(
            "%s %d hydro budget pinned to monthly target total %.1f GWh (was %.1f GWh)",
            iso,
            year,
            target.sum() / 1000.0,
            col_sums.sum() / 1000.0,
        )

    logger.info(
        "Loaded %s %d hydro budget: %d plants, %.1f GWh annual, %.0f MW nameplate",
        iso,
        year,
        len(plant_ids),
        monthly_energy.sum() / 1000.0,
        max_mw.sum(),
    )
    return HydroBudget(
        plant_ids=plant_ids,
        plant_names=plant_names,
        zones=plant_zones,
        monthly_energy=monthly_energy,
        min_mw=min_mw,
        max_mw=max_mw,
    )


def allocate_min_flow_floor(
    monthly_level_mw: np.ndarray,
    monthly_energy: np.ndarray,
    hours_per_month_arr: np.ndarray,
) -> np.ndarray:
    """Allocate a fleet monthly min-flow level onto plants, pro-rata by budget.

    The measured minimum-flow evidence exists only at fleet resolution (EIA-930
    ``NG: WAT`` is a balancing-authority aggregate; there is no per-plant hourly
    hydro series), so the per-plant split must not invent structure. Each plant
    carries the share of the fleet floor equal to **its own share of that
    month's energy budget** — a measured quantity already in the LP, no free
    parameter::

        floor[g, m] = level[m] * monthly_energy[g, m] / sum_g monthly_energy[g, m]

    Two properties follow. (a) *Feasibility is exact*: summed over the month the
    per-plant floor energy is ``level[m] * hours[m] * share[g, m]``, so it fits
    inside the plant's own budget row iff the fleet level fits inside the fleet
    budget — which the level is clipped to here (never above the month's average
    power), making the two-sided hydro budget row feasible per plant by
    construction. (b) The floor keeps the *geography* of the water: a zone's
    share of the floor is its share of the month's inflow, so the floor cannot
    silently relocate hydro between CAISO zones the way a fleet-aggregate LP row
    would (which would also add LP degeneracy across equal-cost hydro units).

    Args:
        monthly_level_mw: Fleet minimum-flow level per calendar month, shape
            ``(12,)`` MW.
        monthly_energy: Per-plant monthly energy budget, shape ``(n, 12)`` MWh,
            for the plants that are actually in the LP.
        hours_per_month_arr: Hours in each calendar month, shape ``(12,)``.

    Returns:
        The ``(n, 12)`` per-plant per-month minimum-flow floor in MW.
    """
    level = np.asarray(monthly_level_mw, dtype=float).copy()
    energy = np.asarray(monthly_energy, dtype=float)
    hpm = np.asarray(hours_per_month_arr, dtype=float)
    fleet_energy = energy.sum(axis=0)  # (12,)
    # Feasibility clip: the floor's monthly energy can never exceed the month's
    # budget, else the two-sided hydro row (min <= sum <= cap) is infeasible.
    # Measured CAISO 2023-25 sits at 0.47-0.59 of this bound, so the clip is a
    # guard, not a tuning surface.
    with np.errstate(divide="ignore", invalid="ignore"):
        cap = np.divide(
            fleet_energy, hpm, out=np.zeros_like(fleet_energy), where=hpm > 0.0
        )
    level = np.minimum(level, cap)
    share = np.divide(
        energy,
        fleet_energy[np.newaxis, :],
        out=np.zeros_like(energy),
        where=fleet_energy[np.newaxis, :] > 0.0,
    )
    return share * level[np.newaxis, :]


def build_hydro_fleet(
    iso: str,
    year: int,
    zone_names: list[str],
    backfill_year: int | None = None,
    eia930_monthly: bool = False,
    forecast_budget: bool = False,
    hydro_year: str = "normal",
    min_flow_floor: bool = False,
    ror_split: bool = False,
    nameplate_aware_target: bool = False,
    as_of_year: int | None = None,
) -> tuple[list[Generator], np.ndarray | None]:
    """Return the ISO's conventional-hydro LP units and their monthly budgets.

    Each EIA-923-reporting conventional hydro plant (prime mover ``HY``;
    pumped storage is a storage resource, not inflow hydro) becomes one LP
    unit at its EIA-860 nameplate, paired row-for-row with its EIA-923
    monthly net-generation energy budget. The dispatch LP's hydro budget
    family then lets each plant choose *when* within a month to generate
    (peak shaving) while its monthly energy stays pinned to the budget level
    — strictly better than the flat-monthly must-run injection it replaces,
    which couldn't shave peaks at all.

    Plants that resolve to no model zone are dropped. Returns
    ``([], None)`` when the ISO has no usable hydro for ``year``.

    ``backfill_year`` carries plants that reported hydro in that prior year
    but not in ``year`` at their prior-year monthly generation — the
    :func:`load_hydro_budget` early-release path. The most recent EIA-923
    vintage is a monthly-survey-only release covering the large reporters, so
    a current-year backcast under-counts conventional hydro until the final
    annual file lands (NEISO 2025: 5 of ~166 plants, 0.09 of ~6 TWh); the
    missing inflow is otherwise served by gas, inflating the modeled gas
    level. ``None`` (default) loads ``year`` exactly as reported and changes
    no existing run. **Backcast-only** — do not use on the forecast path.

    ``eia930_monthly`` repins the assembled budget's monthly energy to the
    measured EIA-930 ``NG: WAT`` monthly total for ``(iso, year)`` (preserving
    per-plant within-month shares), correcting both the level and the monthly
    shape when the backfilled early-release vintage misstates an off-year
    (NEISO 2025: 2024 backfill 6.65 TWh, flat, vs measured 5.12 TWh). No-op
    when EIA-930 hydro for the ISO/year is unavailable. ``False`` (default)
    changes no existing run. **Backcast-only** — a measured realization, never
    on the forecast path.

    The pin is also a no-op — REFUSED, and logged — for an ISO listed in
    :data:`~market_sim.config.constants.EIA930_PS_FOLDED_INTO_WAT`, i.e. one
    whose balancing authority operates pumped storage but files no ``NG: PS``
    column, so its ``NG: WAT`` is a conventional-hydro **plus** pumped-storage
    -discharge series. Those units are conventional hydro alone, so the pin
    would apply one population's energy to another's units (rule 14
    ``[R-ACCURATE]``, miso-108/109: MISO's ``NG: WAT`` runs +13.5 % / +18.5 %
    above EIA-923 ``HY`` in 2023 / 2024 and exceeds the whole conventional
    nameplate in 580 / 826 hours). Their level stays on EIA-923 ``HY``, the same
    series and the same plants the budget itself is built from. Note this makes
    ``nameplate_aware_target`` inert for those ISOs by construction — with no
    level target there is nothing to re-allocate.

    The refusal is PER-YEAR for a BA in
    :data:`~market_sim.config.constants.EIA930_PS_SPLIT_COMPLETE_FROM`, whose
    ``NG: PS`` column starts mid-series (NEISO: first filed hour 2024-11-07):
    a year before the first wholly-split calendar year is folded and refuses
    the pin exactly as above, while the first wholly-split year onward keeps
    it — that window is measured clean (zero nameplate-breach hours in 2025
    against 63-276/yr before the split). One source basis per year, never a
    mid-year splice (neiso-72; see :func:`eia930_wat_level_folded`).

    ``forecast_budget`` is the forward analogue of ``eia930_monthly``: instead
    of pinning the budget to a measured year, it sets the monthly *level* to a
    normal-water-year climatology (the multi-year mean of measured EIA-930
    ``NG: WAT``) scaled by the wet/dry ``hydro_year`` lever — see
    :func:`forecast_monthly_hydro`. The per-plant within-month shares (the
    budget shape) come from EIA-923 at ``min(year,
    EIA923_LATEST_FINAL_VINTAGE)`` — the requested year, clamped to the
    newest vintage with a complete (final-release) plant census, so a
    forecast year past the data horizon reuses the newest real census
    instead of silently degrading to an early-release partial or emptying
    the fleet outright. Only the level is the forecast climatology, so the
    same when-to-generate dispatch mechanism runs against a
    forward-reproducible level rather than a realized one. Mutually
    exclusive with ``eia930_monthly`` (a run is either a backcast realization
    or a forecast). No-op when no climatology exists for the ISO. ``False``
    (default) changes no existing run. This is the forecast-path entry point.

    ``ror_split`` (``config.hydro_ror_split``, caiso-126) splits the fleet by
    the external per-plant operational-mode classifier
    (:func:`market_sim.data.hydro_modes.load_hydro_shapeable`, curated from
    ORNL EHA FY2024 ``Mode`` + the documented HILARRI/Corps-dam completion):
    plants classified NON-shapeable (run-of-river / canal-conduit / Corps-dam
    release-takers / no inventoried reservoir) dispatch FLAT at their own
    measured monthly water — ``budget[g, m] / hours[m]`` — while
    reservoir-class plants keep the full envelope/budget shaping machinery.
    Driver (rule 17a): a run-of-river or conduit plant's output follows
    inflow/deliveries; it physically cannot chase price, but the budget LP
    gives every plant full within-month shaping freedom, so the fleet moves
    as one bang-bang block riding the envelope ceiling (caiso-125 §1/§4c).
    Window (rule 17b): ALL 24 hours — inflow is around-the-clock; the flat
    level is month-constant so no diurnal shape is pinned (rule 13). Forward
    story (rule 17c): the classification is a static plant attribute
    (re-curated when EHA/HILARRI update); the flat level re-derives from the
    same per-plant monthly budget every path already loads, so it scales
    with the water year automatically. Adds no free parameter: the
    classifier is categorical-external and the level is the plant's own
    budget. Implemented by stamping ``hydro_ror_flat_monthly_mw`` (consumed
    by ``generators_to_fleet_arrays`` as BOTH the availability cap and the
    ``min_gen`` floor, mechanism id ``MECH_HYDRO_ROR_FLAT``). Plants the
    classifier does not cover stay shapeable (logged). ``False`` (default)
    changes no existing run.

    **Rule 19 reconciliation with ``min_flow_floor``** (the two mechanisms
    share the run-of-river-inflow driver and are ONE family, never stacked):
    with ``ror_split`` armed, the RoR class's flat base IS its floor
    (subsumed — its dispatch is fixed at its own water), and the fleet Q95
    floor level is reduced by the RoR flat base before being allocated over
    the RESERVOIR class only, so the total forced sustained base equals the
    frozen measured Q95 level exactly — the reservoir class carries the
    licence-minimum-release share of the evidence the RoR base does not
    already serve. With ``ror_split`` off the floor behaves exactly as
    before (caiso-124).

    ``min_flow_floor`` adds the **lower** half of the measured hydro capability
    envelope (``config.hydro_min_flow_floor``): each plant carries a
    month-constant minimum-generation floor, allocated from the fleet's measured
    monthly Q95 sustained level
    (:func:`market_sim.data.eia_loader.measured_hydro_min_flow_level`) pro-rata
    by its own share of the month's energy budget
    (:func:`allocate_min_flow_floor`). Driver: run-of-river inflow that cannot be
    stored plus environmental / FERC-licence minimum releases — the pure energy-
    budget LP has no representation of either, so it is free to park the fleet at
    0 MW (CAISO keeper: 268/688/592 hours below 10 MW in 2023/24/25) where the
    measured fleet never goes near zero. Window: ALL hours (inflow is
    around-the-clock), binding where the economic solution would otherwise go
    below the sustained level — the off-peak/solar-belly hours. Forward story:
    the level re-derives from the same EIA-930 history the ceiling uses, falling
    back to the pooled climatology for a year the extract does not cover, and
    scales with the water year through the budget it is clipped against. Applied
    via ``FleetArrays.min_gen`` (mechanism id ``MECH_HYDRO_MIN_FLOW``), so the
    floor is visible to the D-2/D-4 forced-energy diagnostics. ``False``
    (default) changes no existing run.

    Args:
        iso: ISO identifier, e.g. ``"NEISO"``.
        year: Calendar year of the EIA-923 monthly generation to load (the
            budget shape on the forecast path; the realized level on a
            backcast).
        zone_names: Model zone names of the ISO; plants outside these zones
            are dropped.
        backfill_year: Backcast early-release backfill (see above). Leave
            ``None`` on the forecast path.
        eia930_monthly: Pin to the measured EIA-930 monthly total (backcast
            only). Leave ``False`` on the forecast path.
        forecast_budget: Set the level to the normal-water-year climatology
            scaled by ``hydro_year`` (the forecast path).
        hydro_year: Wet/dry water-year scenario lever applied when
            ``forecast_budget`` is set; ``"normal"`` (default) leaves the
            climatology unscaled.
        min_flow_floor: Stamp the measured monthly minimum-flow floor onto the
            units (see above). ``False`` (default) leaves every unit unfloored.
        ror_split: Split the fleet into run-of-river and reservoir classes from
            the external operational-mode classifier (see above).
        nameplate_aware_target: Apply the monthly level target under each
            plant-month's physical ``nameplate x hours`` ceiling rather than a
            uniform fleet-wide scale factor (rule 14; FINDING-caiso126 K4).
            Byte-identical below the bound. ``False`` (default) changes no
            existing run.
        as_of_year: T1-FF information cutoff (FH-1, hindcast-forward plan §4
            row 11) — set by the full-forward hindcast to its base year. On
            the ``forecast_budget`` path it (a) trims the normal-water-year
            climatology to :func:`full_forward_climatology_years` (years at/
            before the cutoff, quarantined 2022 excluded), and (b) clamps the
            budget *shape* year to the cutoff, so neither the level nor the
            per-plant within-month shares read water data from after the
            base year. ``None`` (default) keeps the full
            ``HYDRO_CLIMATOLOGY_YEARS`` window and the existing shape clamp —
            byte-identical for every other run.

    Returns:
        Tuple ``(units, monthly_energy)`` where ``units`` is the list of
        conventional-hydro :class:`~market_sim.data.fleet.Generator` units and
        ``monthly_energy`` is the ``(n_hydro, 12)`` MWh budget array aligned
        row-for-row to ``units``. ``([], None)`` when the ISO has no usable
        hydro for ``year``.

    Raises:
        ValueError: When both ``eia930_monthly`` and ``forecast_budget`` are
            set (a run is either a backcast realization or a forecast).
    """
    if eia930_monthly and forecast_budget:
        raise ValueError(
            "eia930_monthly (measured backcast level) and forecast_budget "
            "(normal-water-year forecast level) are mutually exclusive"
        )
    shape_year = year
    if eia930_monthly:
        from market_sim.config.constants import EIA930_PS_FOLDED_INTO_WAT
        from market_sim.data.eia_loader import measured_monthly_hydro

        if iso.upper() in EIA930_PS_FOLDED_INTO_WAT:
            # Rule 14 [R-ACCURATE], miso-109: this BA files no `NG: PS`, so its
            # `NG: WAT` is a conventional-hydro PLUS pumped-storage-discharge
            # series — not an admissible LEVEL for a conventional-hydro-only
            # unit population. The accurate level for these units is the
            # EIA-923 `HY` series the per-plant budget already carries, which
            # is exactly what `target = None` leaves in place, so the level and
            # the units become the same population. Never a fitted correction:
            # no reconciliation factor is identifiable from the source data
            # (see the constant's citation, rules 13/23).
            logger.info(
                "%s %d: EIA-930 NG: WAT level pin REFUSED — this BA folds "
                "pumped storage into NG: WAT (no NG: PS column); the monthly "
                "hydro level stays on EIA-923 HY, the same population as the "
                "LP units (rule 14)",
                iso,
                year,
            )
            target = None
        elif eia930_wat_level_folded(iso, year):
            # Rule 14 [R-ACCURATE], neiso-72 — the TIME-SPLIT case: this BA
            # files `NG: PS` only from a mid-series first-filing hour (NEISO:
            # 2024-11-07 00:00), so THIS year's `NG: WAT` still folds
            # pumped-storage discharge and the pin is refused per-year — the
            # level stays on EIA-923 `HY` exactly as in the flat-registry
            # case above. Years at/after the first wholly-split year keep
            # the pin: their `NG: WAT` is measured clean (0 nameplate-breach
            # hours in 2025 against 63-276/yr before the split). One basis
            # per year, never a mid-year splice — see the
            # EIA930_PS_SPLIT_COMPLETE_FROM citation for the seam
            # measurement and the design adjudication.
            logger.info(
                "%s %d: EIA-930 NG: WAT level pin REFUSED for this year — "
                "the BA's NG: PS column starts mid-series (time split) and "
                "this year predates its first wholly-split year, so its "
                "NG: WAT still folds pumped-storage discharge; the monthly "
                "hydro level stays on EIA-923 HY (rule 14, neiso-72)",
                iso,
                year,
            )
            target = None
        else:
            target = measured_monthly_hydro(iso, year)
    elif forecast_budget:
        from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS

        # T1-FF as-of trim (FH-1): a full-forward hindcast's climatology may
        # not average water years after its base year, nor quarantined 2022.
        # None (every other run) keeps the full constant window.
        _clim_years: "tuple[int, ...] | None" = None
        if as_of_year is not None:
            _clim_years = full_forward_climatology_years(as_of_year)
        _clim_window = (
            _clim_years if _clim_years is not None else HYDRO_CLIMATOLOGY_YEARS
        )
        target = forecast_monthly_hydro(iso, hydro_year, _clim_years)
        if any(eia930_wat_level_folded(iso, y) for y in _clim_window):
            # miso-110 (flat) / neiso-72 (time split): this BA's forward level
            # comes from the EIA-923 `HY` climatology, not the PS-folded
            # `NG: WAT` one (see forecast_monthly_hydro — the SAME window
            # predicate selects there, so this logging branch mirrors the
            # selection exactly). `climatological_monthly_hydro_923` logs the
            # realised window; what is logged here is the level actually
            # applied, and — on the fallback — that the wet/dry lever went
            # inert with it.
            if target is None:
                logger.warning(
                    "%s %d: no complete EIA-923 HY filing in the climatology "
                    "window — the forecast hydro LEVEL falls back to the "
                    "shape year's own EIA-923 level (a single water year, not "
                    "a climatology) and the hydro_year=%r wet/dry lever has "
                    "nothing to scale",
                    iso,
                    year,
                    hydro_year,
                )
            else:
                logger.info(
                    "%s %d: forecast hydro LEVEL from the EIA-923 HY "
                    "climatology (hydro_year=%r) — %.4f TWh; the EIA-930 "
                    "NG: WAT climatology is REFUSED for this BA, which folds "
                    "pumped storage into it (rule 14)",
                    iso,
                    year,
                    hydro_year,
                    target.sum() / 1e6,
                )
        # Forecast branch only: the budget *shape* (per-plant within-month
        # shares) must come from a complete plant census. EIA-923 vintages
        # after the latest final release are monthly early releases carrying
        # only the monthly-survey (large) reporters, and years past the
        # newest vintage have no rows at all — an unclamped forecast year
        # silently emptied the hydro fleet in every year past the last
        # vintage (nyiso-forecast-2035-2026-07-13.md finding 1). The *level*
        # is already the climatology `target`, so clamping only the shape
        # year keeps the forward methodology intact while restoring the real
        # plant set. Backcast paths (eia930_monthly / bare) are untouched.
        # T1-FF (as_of_year set): the shape year is additionally clamped to
        # the base year — a base-2023 run solving 2024/2025 keeps the 2023
        # within-month shares, exactly as a real 2023-vintage forecast would
        # (its latest final vintage is <= its base). Same information cutoff
        # as the climatology trim above, one seam (rule 19).
        from market_sim.data.eia923 import EIA923_LATEST_FINAL_VINTAGE

        shape_year = min(year, EIA923_LATEST_FINAL_VINTAGE)
        if as_of_year is not None:
            shape_year = min(shape_year, int(as_of_year))
    else:
        target = None
    try:
        budget = load_hydro_budget(
            iso,
            shape_year,
            backfill_year=backfill_year,
            monthly_target_mwh=target,
            nameplate_aware_target=nameplate_aware_target,
        )
    except (FileNotFoundError, ValueError):
        if forecast_budget:
            logger.warning(
                "%s %d: no EIA-923 hydro budget shape available "
                "(shape year %d) — hydro fleet is empty for this year",
                iso,
                year,
                shape_year,
            )
        return [], None
    units: list[Generator] = []
    monthly: list[np.ndarray] = []
    for i, pid in enumerate(budget.plant_ids):
        zone = budget.zones[i]
        cap = float(budget.max_mw[i])
        energy = np.asarray(budget.monthly_energy[i], dtype=float)
        if zone not in zone_names or cap <= 0.0 or energy.sum() <= 0.0:
            continue
        units.append(
            Generator(
                unit_id=f"{int(pid)}_hydro",
                name=budget.plant_names[i],
                zone=zone,
                fuel_type="hydro",
                pmax_mw=cap,
                vom=VOM["hydro"],
                eford=0.0,  # availability is captured by the energy budget
                plant_group="hydro",
                plant_code=int(pid),
            )
        )
        monthly.append(energy)
    if not units:
        return [], None
    monthly_energy = np.vstack(monthly)
    hpm = hours_per_month().astype(float)

    # Run-of-river split (config.hydro_ror_split, caiso-126): stamp the flat
    # dispatch level budget[g, m] / hours[m] on every unit the external
    # classifier marks NON-shapeable. Clipped to nameplate (a monthly average
    # above nameplate is a source-data inconsistency, logged loudly — the
    # peak-monthly-average nameplate fallback can never trip it).
    ror_rows = np.zeros(len(units), dtype=bool)
    ror_flat_base = np.zeros(_MONTHS_PER_YEAR, dtype=float)  # stamped fleet base
    if ror_split:
        from market_sim.data.hydro_modes import load_hydro_shapeable

        modes = load_hydro_shapeable(iso)
        if modes is None:
            logger.warning(
                "%s %d: hydro_ror_split armed but no hydro-plant-modes "
                "classifier partition — fleet left fully shapeable",
                iso,
                year,
            )
        else:
            unclassified = 0
            for i, unit in enumerate(units):
                shapeable = modes.get(int(unit.plant_code))
                if shapeable is None:
                    unclassified += 1  # absent from the classifier: shapeable
                elif not shapeable:
                    ror_rows[i] = True
            flat = monthly_energy[ror_rows] / hpm[np.newaxis, :]
            caps = np.array([units[i].pmax_mw for i in np.where(ror_rows)[0]])
            over = flat > caps[:, np.newaxis]
            if np.any(over):
                logger.warning(
                    "%s %d: RoR flat level exceeds nameplate on %d "
                    "plant-month(s) — clipped to nameplate (source-data "
                    "inconsistency: monthly budget above nameplate-hours)",
                    iso,
                    year,
                    int(over.sum()),
                )
                flat = np.minimum(flat, caps[:, np.newaxis])
            for row, i in enumerate(np.where(ror_rows)[0]):
                units[i].hydro_ror_flat_monthly_mw = tuple(float(v) for v in flat[row])
            if ror_rows.any():
                ror_flat_base = flat.sum(axis=0)
            logger.info(
                "%s %d: RoR split — %d/%d plants flat at their monthly water "
                "(%.1f%% of the %.2f TWh budget; fleet flat base %.0f-%.0f MW "
                "by month; %d plants unclassified -> shapeable)",
                iso,
                year,
                int(ror_rows.sum()),
                len(units),
                100.0 * monthly_energy[ror_rows].sum() / max(monthly_energy.sum(), 1.0),
                monthly_energy.sum() / 1e6,
                flat.sum(axis=0).min() if ror_rows.any() else 0.0,
                flat.sum(axis=0).max() if ror_rows.any() else 0.0,
                unclassified,
            )

    # Lower half of the measured hydro capability envelope: the month-constant
    # minimum-flow floor, allocated pro-rata by each plant's share of the
    # month's budget. Computed on the units that are actually IN the LP (the
    # zone/capacity filter above already ran), so the allocated floor sums to
    # the fleet level over exactly the plants that can serve it. Rule-19
    # reconciliation with the RoR split (see the docstring): the RoR class's
    # flat base subsumes its share of the floor's driver, so the fleet level
    # is reduced by that base and allocated over the RESERVOIR class only —
    # the total forced sustained base stays exactly the frozen Q95 level.
    if min_flow_floor:
        from market_sim.data.eia_loader import measured_hydro_min_flow_level

        level = measured_hydro_min_flow_level(iso, year)
        if level is None:
            logger.info(
                "%s %d: no measured hydro min-flow level available — hydro "
                "fleet left unfloored",
                iso,
                year,
            )
        else:
            if ror_rows.any():
                # Subtract the STAMPED (nameplate-clipped) base — the level the
                # RoR class actually delivers — so base + reservoir floor
                # reproduces the frozen Q95 evidence exactly.
                ror_base = ror_flat_base
                level = np.clip(np.asarray(level, dtype=float) - ror_base, 0.0, None)
                logger.info(
                    "%s %d: min-flow floor reconciled with the RoR split — "
                    "fleet Q95 level reduced by the RoR flat base "
                    "(%.0f-%.0f MW by month) and allocated over the "
                    "reservoir class only",
                    iso,
                    year,
                    ror_base.min(),
                    ror_base.max(),
                )
            floor_rows = ~ror_rows
            floors = allocate_min_flow_floor(level, monthly_energy[floor_rows], hpm)
            for row, i in enumerate(np.where(floor_rows)[0]):
                units[i].hydro_min_flow_monthly_mw = tuple(
                    float(v) for v in floors[row]
                )
            logger.info(
                "%s %d: hydro min-flow floor on %d units — fleet level "
                "%.0f-%.0f MW by month (%.2f TWh, %.0f%% of the %.2f TWh "
                "budget)",
                iso,
                year,
                int(floor_rows.sum()),
                floors.sum(axis=0).min(),
                floors.sum(axis=0).max(),
                float((floors.sum(axis=0) * hpm).sum()) / 1e6,
                100.0
                * float((floors.sum(axis=0) * hpm).sum())
                / max(monthly_energy.sum(), 1.0),
                monthly_energy.sum() / 1e6,
            )
    return units, monthly_energy
