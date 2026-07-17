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
    ISO_TO_BA_CODE,
    Generator,
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
    from market_sim.data.eia_loader import climatological_monthly_hydro

    base = climatological_monthly_hydro(iso, climatology_years)
    if base is None:
        return None
    return base * resolve_hydro_year_multiplier(hydro_year)


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
    subset = gen[(gen["prime_mover"] == HYDRO_PRIME_MOVER) & (gen["year"] == year)]
    if ba_code is not None and "ba_code" in subset.columns:
        subset = subset[subset["ba_code"] == ba_code]
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
    ba_code = ISO_TO_BA_CODE.get(iso.upper())
    if ba_code is None:
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

    sub = df[(df["prime_mover"] == HYDRO_PRIME_MOVER) & (df["ba_code"] == ba_code)]
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
        ba_code = ISO_TO_BA_CODE.get(iso.upper())
        mask = df["prime_mover"] == HYDRO_PRIME_MOVER
        if ba_code is not None and "balancing_authority_code" in df.columns:
            mask &= df["balancing_authority_code"] == ba_code
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


def load_hydro_budget(
    iso: str,
    year: int,
    min_flow_fraction: float = 0.0,
    backfill_year: int | None = None,
    per_plant_min_flow: dict[int, float] | None = None,
    monthly_target_mwh: np.ndarray | None = None,
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


def build_hydro_fleet(
    iso: str,
    year: int,
    zone_names: list[str],
    backfill_year: int | None = None,
    eia930_monthly: bool = False,
    forecast_budget: bool = False,
    hydro_year: str = "normal",
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
        from market_sim.data.eia_loader import measured_monthly_hydro

        target = measured_monthly_hydro(iso, year)
    elif forecast_budget:
        target = forecast_monthly_hydro(iso, hydro_year)
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
        from market_sim.data.eia923 import EIA923_LATEST_FINAL_VINTAGE

        shape_year = min(year, EIA923_LATEST_FINAL_VINTAGE)
    else:
        target = None
    try:
        budget = load_hydro_budget(
            iso, shape_year, backfill_year=backfill_year, monthly_target_mwh=target
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
    return units, np.vstack(monthly)
