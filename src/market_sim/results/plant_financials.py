"""Plant-level financial reporting from bin-level dispatch results.

The market simulator dispatches generators at heat-rate-bin granularity
(e.g. ``gas_cc_h_class``), not at individual EIA plant codes. This module
bridges that gap: it disaggregates bin-level dispatch back to individual
plants, computes plant-specific hourly and annual financials using each
plant's *own* heat rate, and rolls the result up to parent companies via
the ownership mapping in :mod:`market_sim.data.ownership`.

Per methodology spec §5.2, no capital costs enter the P&L -- capital is a
sunk cost. Going-forward economics use only fixed O&M plus variable costs.

All financial calculations are vectorized pandas/numpy operations: there
are no ``iterrows`` calls, no per-row ``apply`` lambdas, and no Python
loops over hours or plants.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, fields
from types import SimpleNamespace

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    DEFAULT_MARKET_DESIGN,
    EFORD,
    HEAT_RATE_BINS,
    HOURS_PER_YEAR,
    MARKET_DESIGN,
    resolve_capacity_market_clearing,
)
from market_sim.data.fleet import FUEL_TYPE_MAP
from market_sim.policy.federal_ces import effective_unit_eac_prices

logger = logging.getLogger(__name__)

# Heat-rate unit conversion. The model stores heat rates as MMBtu/MWh
# (see config/constants.py HEAT_RATE_BINS); plant financials work in
# BTU/kWh, the EIA-860 convention. 1 MMBtu/MWh = 1000 BTU/kWh.
BTU_KWH_PER_MMBTU_MWH: float = 1000.0

# MWh × (BTU/kWh) ÷ this = MMBtu. Derivation: 1 MWh = 1000 kWh, and
# 1 MMBtu = 1e6 BTU, so MWh·(BTU/kWh) = 1000·BTU = 1e-3 MMBtu.
MMBTU_PER_MWH_BTU_KWH: float = 1000.0

# Pounds per metric tonne (1 tonne = 1000 kg; 1 lb = 0.45359237 kg). R7/EM-2:
# the model's canonical NOx rate unit is tonnes/MWh (as written by
# fleet.apply_plant_emission_rates), while the NOx price arrives in $/lb; the
# rate is converted to lb/MWh at this boundary before costing.
LB_PER_TONNE: float = 1000.0 / 0.45359237


@dataclass
class PlantBinAssignment:
    """Maps an individual EIA plant/unit to its heat-rate dispatch bin.

    Attributes:
        plant_code: EIA plant code (ORIS code).
        generator_id: EIA generator/unit identifier within the plant.
        unit_id: The market-sim internal generator label -- the aggregated
            bin's ``unit_id``, formatted ``{fuel}_{efficiency_bin}_{zone}``.
        bin_label: Heat-rate bin label, ``{fuel}_{efficiency_bin}``.
        nameplate_mw: Plant/unit nameplate capacity, in MW.
        heat_rate_btu_kwh: Plant-specific heat rate, in BTU/kWh -- *not* the
            bin average. This is the whole point of disaggregation.
        zone: Dispatch zone the plant sits in.
        fuel_type: Model fuel type (``gas_cc``, ``gas_ct``, ``coal``, …).
        vom_per_mwh: Variable O&M, in $/MWh.
        fom_per_kw_yr: Fixed O&M, in $/kW-year.
        emission_rate_tco2_mwh: CO2 emission rate, in tCO2/MWh.
        nox_rate_tonnes_mwh: NOx emission rate, in **tonnes/MWh** -- the model's
            canonical unit (``Generator.nox_rate``). Converted to lb/MWh at the
            costing boundary via :data:`LB_PER_TONNE` (R7/EM-2 unit-contract fix).
    """

    plant_code: int
    generator_id: str
    unit_id: str
    bin_label: str
    nameplate_mw: float
    heat_rate_btu_kwh: float
    zone: str
    fuel_type: str
    vom_per_mwh: float
    fom_per_kw_yr: float
    emission_rate_tco2_mwh: float
    nox_rate_tonnes_mwh: float


def _plant_map_frame(plant_map: list[PlantBinAssignment]) -> pd.DataFrame:
    """Return a :class:`PlantBinAssignment` list as a DataFrame."""
    return pd.DataFrame(
        [
            {f.name: getattr(p, f.name) for f in fields(PlantBinAssignment)}
            for p in plant_map
        ]
    )


def _heat_rate_bin(
    fuel_type: str, heat_rate_btu_kwh: float, bin_definitions: dict
) -> str:
    """Return the efficiency-bin name for a plant given its heat rate.

    The plant is placed in whichever bin of ``bin_definitions[fuel_type]``
    its heat rate is closest to, using the midpoints between adjacent bin
    reference heat rates as boundaries. Fuels absent from the bin
    definitions (e.g. nuclear) fall back to ``"default"``.
    """
    bins = bin_definitions.get(fuel_type)
    if not bins:
        return "default"
    # bin_definitions stores reference heat rates in MMBtu/MWh.
    hr_mmbtu_mwh = heat_rate_btu_kwh / BTU_KWH_PER_MMBTU_MWH
    names = list(bins.keys())
    refs = np.array([bins[n] for n in names], dtype=float)
    return names[int(np.argmin(np.abs(refs - hr_mmbtu_mwh)))]


def build_plant_bin_map(
    fleet_path,
    bin_definitions: dict | None = None,
) -> list[PlantBinAssignment]:
    """Assign each EIA-860 plant/unit to its heat-rate dispatch bin.

    Loads the binned-fleet parquet (one row per physical generator, written
    by :func:`market_sim.data.fleet.load_fleet_from_csv`) and assigns each
    unit a heat-rate bin using the same bin reference heat rates as the
    dispatch model (``config.constants.HEAT_RATE_BINS``).

    Args:
        fleet_path: Path to a plant-level fleet parquet with columns
            ``plant_id``, ``fuel_type``, ``zone``, ``pmax_mw``,
            ``heat_rate``, ``vom``, ``emission_rate_co2`` and ``nox_rate``.
            An ``efficiency_bin`` and ``generator_id`` column are used when
            present.
        bin_definitions: Heat-rate bin reference table, keyed by fuel class
            then bin name. Defaults to :data:`HEAT_RATE_BINS`.

    Returns:
        One :class:`PlantBinAssignment` per physical generator.
    """
    bin_definitions = HEAT_RATE_BINS if bin_definitions is None else bin_definitions
    df = pd.read_parquet(fleet_path)

    assignments: list[PlantBinAssignment] = []
    # itertuples is a row iterator over a static fleet table, not a
    # financial calculation -- the vectorization rule applies to dispatch
    # and money math, not to this one-off fleet ingest.
    for row in df.itertuples(index=False):
        data = row._asdict()
        fuel_type = str(data["fuel_type"])
        heat_rate = float(data.get("heat_rate") or 0.0)
        heat_rate_btu_kwh = heat_rate * BTU_KWH_PER_MMBTU_MWH

        ebin = data.get("efficiency_bin")
        if not ebin or str(ebin) == "default":
            ebin = _heat_rate_bin(fuel_type, heat_rate_btu_kwh, bin_definitions)
        ebin = str(ebin)

        zone = str(data["zone"])
        generator_id = str(data.get("generator_id") or "1")
        bin_label = f"{fuel_type}_{ebin}"
        assignments.append(
            PlantBinAssignment(
                plant_code=int(data["plant_id"]),
                generator_id=generator_id,
                unit_id=f"{fuel_type}_{ebin}_{zone}",
                bin_label=bin_label,
                nameplate_mw=float(data["pmax_mw"]),
                heat_rate_btu_kwh=heat_rate_btu_kwh,
                zone=zone,
                fuel_type=fuel_type,
                vom_per_mwh=float(data.get("vom") or 0.0),
                fom_per_kw_yr=float(data.get("fom_per_kw_yr") or 0.0),
                emission_rate_tco2_mwh=float(data.get("emission_rate_co2") or 0.0),
                # Generator.nox_rate is tonnes/MWh (fleet.apply_plant_emission_rates
                # writes kg/MWh ÷ 1000); carried canonical and converted to lb at
                # the costing boundary (R7/EM-2).
                nox_rate_tonnes_mwh=float(data.get("nox_rate") or 0.0),
            )
        )
    logger.info("Built plant-bin map for %d generators", len(assignments))
    return assignments


def disaggregate_dispatch(
    bin_dispatch: pd.DataFrame,
    plant_map: list[PlantBinAssignment],
    method: str = "pro_rata_capacity",
) -> pd.DataFrame:
    """Allocate multi-plant bin dispatch to individual plants (legacy path).

    NOTE: the ERCOT CAMPD fleet dispatches one LP generator *per plant*
    (see ``fleet.bins_to_fleet`` -- "one bin per plant"), so each
    ``(bin_label, zone)`` group already contains a single plant and this
    split is an identity (``cap_share == 1``). This disaggregation only does
    real work for the legacy multi-plant aggregation path
    (``use_campd_bins=False`` / ``aggregate_fleet``); it is NOT how the
    per-plant model maps dispatch to plants. Do not read a pro-rata bin
    split into the per-plant calibration/heatmap results.

    Methods:

    * ``"pro_rata_capacity"`` (default) -- within each ``(bin_label, zone)``
      the bin's hourly dispatch is split across plants in proportion to
      nameplate MW::

          plant_dispatch[p,t] = bin_dispatch[b,t]
                                * plant_mw[p] / sum(plant_mw in b, z)

      The most defensible choice for an LP without unit commitment.

    * ``"merit_order_within_bin"`` -- within each bin, plants are filled in
      ascending plant-specific heat rate (most efficient first). More
      realistic but introduces sub-bin ordering the LP never solved for.

    Args:
        bin_dispatch: Columns ``bin_label``, ``zone``, ``hour`` and
            ``dispatch_mw``.
        plant_map: The plant-to-bin assignment from :func:`build_plant_bin_map`.
        method: Disaggregation method, as above.

    Returns:
        Columns ``plant_code``, ``generator_id``, ``hour``, ``dispatch_mw``,
        ``bin_label`` and ``zone`` -- one row per plant-hour.

    Raises:
        ValueError: When ``method`` is not a recognized disaggregation method.
    """
    plants = _plant_map_frame(plant_map)[
        [
            "plant_code",
            "generator_id",
            "bin_label",
            "zone",
            "nameplate_mw",
            "heat_rate_btu_kwh",
        ]
    ]
    if method == "pro_rata_capacity":
        out = _disaggregate_pro_rata(bin_dispatch, plants)
    elif method == "merit_order_within_bin":
        out = _disaggregate_merit_order(bin_dispatch, plants)
    else:
        raise ValueError(f"unknown disaggregation method: {method!r}")
    return out[
        ["plant_code", "generator_id", "hour", "dispatch_mw", "bin_label", "zone"]
    ].reset_index(drop=True)


def _disaggregate_pro_rata(
    bin_dispatch: pd.DataFrame, plants: pd.DataFrame
) -> pd.DataFrame:
    """Split bin dispatch across plants pro rata to nameplate capacity."""
    group = ["bin_label", "zone"]
    cap_total = plants.groupby(group)["nameplate_mw"].transform("sum")
    plants = plants.assign(
        cap_share=np.where(cap_total > 0.0, plants["nameplate_mw"] / cap_total, 0.0)
    )
    merged = plants.merge(bin_dispatch, on=group, how="inner")
    merged["dispatch_mw"] = merged["dispatch_mw"] * merged["cap_share"]
    return merged


def _disaggregate_merit_order(
    bin_dispatch: pd.DataFrame, plants: pd.DataFrame
) -> pd.DataFrame:
    """Fill plants within each bin in ascending heat-rate (merit) order.

    For each ``(bin_label, zone)`` the bin's hourly dispatch is poured into
    plants cheapest-first::

        plant_dispatch[p,t] = clip(bin_dispatch[t] - cumcap_before[p],
                                   0, nameplate_mw[p])

    The clip is fully vectorized across all hours of a group at once; the
    only loop is over ``(bin_label, zone)`` groups, never over hours or
    plants.
    """
    group = ["bin_label", "zone"]
    results: list[pd.DataFrame] = []
    bin_by_group = dict(tuple(bin_dispatch.groupby(group)))

    for keys, grp in plants.groupby(group):
        bd = bin_by_group.get(keys)
        if bd is None:
            continue
        grp = grp.sort_values("heat_rate_btu_kwh").reset_index(drop=True)
        cap = grp["nameplate_mw"].to_numpy(dtype=float)
        cumcap_before = np.concatenate([[0.0], np.cumsum(cap)[:-1]])

        bd = bd.sort_values("hour")
        hours = bd["hour"].to_numpy()
        bin_mw = bd["dispatch_mw"].to_numpy(dtype=float)

        # (n_plant, n_hour): each plant's headroom-clipped fill.
        filled = np.clip(bin_mw[None, :] - cumcap_before[:, None], 0.0, cap[:, None])
        block = grp[["plant_code", "generator_id", "bin_label", "zone"]].copy()
        block = block.loc[block.index.repeat(len(hours))].reset_index(drop=True)
        block["hour"] = np.tile(hours, len(grp))
        block["dispatch_mw"] = filled.ravel()
        results.append(block)

    if not results:
        return pd.DataFrame(
            columns=[
                "plant_code",
                "generator_id",
                "bin_label",
                "zone",
                "hour",
                "dispatch_mw",
            ]
        )
    return pd.concat(results, ignore_index=True)


def _broadcast_hourly_price(price: "np.ndarray | float", hours: pd.Series) -> pd.Series:
    """Map a scalar or ``(8760,)`` price array onto a Series of hour indices."""
    arr = np.asarray(price, dtype=float)
    if arr.ndim == 0:
        return pd.Series(float(arr), index=hours.index)
    return pd.Series(arr[hours.to_numpy()], index=hours.index)


def compute_plant_hourly_financials(
    plant_dispatch: pd.DataFrame,
    zonal_prices: pd.DataFrame,
    fuel_prices: pd.DataFrame,
    carbon_price: "np.ndarray | float",
    nox_price: "np.ndarray | float",
    plant_map: list[PlantBinAssignment],
    discount_rate: float = 0.08,
    year: int = 2026,
    base_year: int = 2026,
) -> pd.DataFrame:
    """Compute per-plant, per-hour financials from disaggregated dispatch.

    Uses each plant's own heat rate -- a less efficient plant in the same
    bin burns more fuel and earns a lower margin at the same dispatch.

    Args:
        plant_dispatch: Output of :func:`disaggregate_dispatch`.
        zonal_prices: Columns ``zone``, ``hour``, ``price_per_mwh`` (LP duals).
        fuel_prices: Columns ``fuel_type``, ``hour``, ``price_per_mmbtu``.
        carbon_price: $/tCO2, scalar or ``(8760,)`` hourly array.
        nox_price: $/lb NOx, scalar or ``(8760,)`` hourly array.
        plant_map: The plant-to-bin assignment from :func:`build_plant_bin_map`.
        discount_rate: Discount rate from ``ScenarioConfig``; unused at the
            hourly level but kept for signature symmetry with the annual call.
        year: Calendar year of the dispatch.
        base_year: NPV reference year.

    Returns:
        Columns ``plant_code``, ``generator_id``, ``zone``, ``hour`` and the
        full set of hourly financial quantities (revenue, fuel/vom/carbon/
        nox costs, gross margin, emissions).
    """
    del discount_rate, year, base_year  # not needed for hourly quantities

    attr_cols = [
        "plant_code",
        "generator_id",
        "fuel_type",
        "heat_rate_btu_kwh",
        "vom_per_mwh",
        "emission_rate_tco2_mwh",
        "nox_rate_tonnes_mwh",
    ]
    attrs = _plant_map_frame(plant_map)[attr_cols]

    df = plant_dispatch.merge(attrs, on=["plant_code", "generator_id"], how="left")
    df = df.merge(zonal_prices, on=["zone", "hour"], how="left")
    df = df.merge(fuel_prices, on=["fuel_type", "hour"], how="left")

    carbon = _broadcast_hourly_price(carbon_price, df["hour"])
    nox = _broadcast_hourly_price(nox_price, df["hour"])

    df["generation_mwh"] = df["dispatch_mw"]  # hourly resolution: 1 h slots
    df["revenue"] = df["generation_mwh"] * df["price_per_mwh"]
    df["fuel_mmbtu"] = (
        df["generation_mwh"] * df["heat_rate_btu_kwh"] / MMBTU_PER_MWH_BTU_KWH
    )
    df["fuel_cost"] = df["fuel_mmbtu"] * df["price_per_mmbtu"]
    df["vom_cost"] = df["generation_mwh"] * df["vom_per_mwh"]
    df["carbon_cost"] = df["generation_mwh"] * df["emission_rate_tco2_mwh"] * carbon
    # R7/EM-2: convert the canonical tonnes/MWh NOx rate to lb/MWh before
    # applying the $/lb NOx price (previously multiplied tonnes/MWh by $/lb -- a
    # ~2205× under-count).
    df["nox_rate_lb_mwh"] = df["nox_rate_tonnes_mwh"] * LB_PER_TONNE
    df["nox_cost"] = df["generation_mwh"] * df["nox_rate_lb_mwh"] * nox
    df["total_variable_cost"] = (
        df["fuel_cost"] + df["vom_cost"] + df["carbon_cost"] + df["nox_cost"]
    )
    df["gross_margin"] = df["revenue"] - df["total_variable_cost"]
    df["co2_emissions_tons"] = df["generation_mwh"] * df["emission_rate_tco2_mwh"]
    df["nox_emissions_lbs"] = df["generation_mwh"] * df["nox_rate_lb_mwh"]

    return df[
        [
            "plant_code",
            "generator_id",
            "zone",
            "hour",
            "generation_mwh",
            "revenue",
            "fuel_mmbtu",
            "fuel_cost",
            "vom_cost",
            "carbon_cost",
            "nox_cost",
            "total_variable_cost",
            "gross_margin",
            "co2_emissions_tons",
            "nox_emissions_lbs",
        ]
    ]


def compute_plant_annual_summary(
    hourly: pd.DataFrame,
    plant_map: list[PlantBinAssignment],
    discount_rate: float = 0.08,
    year: int = 2026,
    base_year: int = 2026,
    iso: str | None = None,
    config: "object | None" = None,
    reserve_position: float | None = None,
) -> pd.DataFrame:
    """Aggregate hourly plant financials into an annual per-plant summary.

    Args:
        hourly: Output of :func:`compute_plant_hourly_financials`.
        plant_map: The plant-to-bin assignment from :func:`build_plant_bin_map`.
        discount_rate: Discount rate from ``ScenarioConfig``.
        year: Calendar year of the dispatch.
        base_year: NPV reference year -- ``discount_factor`` is 1.0 here.
        iso: ISO whose :data:`MARKET_DESIGN` capacity payment to credit. When
            given (and the ISO has a capacity market), each plant earns a
            ``capacity_revenue`` on its UCAP (``nameplate × (1 − EFORd_fuel)``)
            at the shared per-firm-MW capacity price
            (:meth:`MarketDesign.capacity_price_per_firm_mw_yr` -- the SAME seam
            the capacity screens price through). ``None`` (default) credits no
            capacity revenue, so every existing metric is byte-identical.
        config: Scenario config. The capacity-revenue path reads only its
            ``capacity_market_clearing`` flag (duck-typed); the
            attribute-revenue line additionally resolves the run's
            ``eac_price_*`` / ``federal_ces_*`` fields through
            :func:`market_sim.policy.federal_ces.effective_unit_eac_prices`,
            so pass the run's real
            :class:`~market_sim.config.scenarios.ScenarioConfig` (or ``None``
            to leave both revenue lines at zero).
        reserve_position: System accredited reserve position for the CR-1 curve
            (see :func:`market_sim.model.capacity.capacity_reserve_position`).
            ``None`` keeps the fixed net-CONE capacity price.

    Returns:
        One row per plant-generator with annual sums, capacity factor,
        spark spread, fixed O&M, net operating income, intensities and the
        NPV of net operating income. Per-MWh metrics are ``NaN`` for plants
        with zero annual generation (no division by zero). ``capacity_revenue``
        ($/yr, 0.0 unless ``iso`` credits a capacity market),
        ``capacity_revenue_source`` (``"curve"`` | ``"fixed"`` | ``"none"``)
        and ``net_operating_income_with_capacity`` (energy NOI + capacity
        revenue) are always present; the energy-only ``net_operating_income``
        and its NPV are unchanged. ``attribute_price_usd_per_mwh`` (the
        plant's effective EAC/CES certificate price in real 2026$/MWh —
        ``max(legacy eac_price_*, federal premium × credit fraction)``) and
        ``attribute_revenue`` (that price × generation, $/yr) are always
        present, 0.0 unless ``config`` is given; PTC/ITC/45U/45Q are
        deliberately excluded from this line (tax credits, not certificates),
        and it is NOT folded into any net-operating-income column.
    """
    sum_cols = [
        "generation_mwh",
        "revenue",
        "fuel_mmbtu",
        "fuel_cost",
        "vom_cost",
        "carbon_cost",
        "nox_cost",
        "total_variable_cost",
        "gross_margin",
        "co2_emissions_tons",
        "nox_emissions_lbs",
    ]
    annual = (
        hourly.groupby(["plant_code", "generator_id"], dropna=False)[sum_cols]
        .sum()
        .reset_index()
    )

    attrs = _plant_map_frame(plant_map)[
        [
            "plant_code",
            "generator_id",
            "zone",
            "fuel_type",
            "bin_label",
            "nameplate_mw",
            "heat_rate_btu_kwh",
            "fom_per_kw_yr",
            # Plant CO2 rate (tCO2/MWh): the cesa_ci crediting input for the
            # attribute-revenue line; internal only, not an output column.
            "emission_rate_tco2_mwh",
        ]
    ]
    annual = annual.merge(attrs, on=["plant_code", "generator_id"], how="left")

    gen = annual["generation_mwh"]
    # Mask zero-generation plants so per-MWh metrics become NaN, not ±inf.
    gen_nz = gen.where(gen > 0.0)

    annual["capacity_factor"] = gen / (annual["nameplate_mw"] * HOURS_PER_YEAR)
    annual["fom_cost"] = annual["nameplate_mw"] * 1000.0 * annual["fom_per_kw_yr"]
    annual["net_operating_income"] = annual["gross_margin"] - annual["fom_cost"]
    annual["avg_price_captured"] = annual["revenue"] / gen_nz
    annual["avg_marginal_cost"] = annual["total_variable_cost"] / gen_nz

    # Resource-adequacy capacity revenue (labeled by source). Priced off the
    # shared per-firm-MW seam (rule 19 -- the same MarketDesign price the
    # capacity screens use), credited on each plant's UCAP (nameplate ×
    # (1 − EFORd_fuel)). Zero and source "none" unless an ``iso`` with a
    # capacity market is supplied, so the default report is byte-identical.
    annual["capacity_revenue"] = 0.0
    annual["capacity_revenue_source"] = "none"
    if iso is not None:
        design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
        # Pass ``iso`` so the per-ISO clearing gate (RC-1B item 1) resolves
        # through the shared seam; no ``year`` (this report prices on the
        # registry default curve, not a per-delivery-year vintage). Default
        # (mapping unset) is byte-identical.
        price_per_firm_mw_yr = design.capacity_price_per_firm_mw_yr(
            config, reserve_position, iso=iso
        )
        if design.capacity_market and price_per_firm_mw_yr > 0.0:
            ucap = (1.0 - annual["fuel_type"].map(EFORD).fillna(0.0)).clip(lower=0.0)
            annual["capacity_revenue"] = (
                annual["nameplate_mw"] * ucap * price_per_firm_mw_yr
            )
            uses_curve = (
                resolve_capacity_market_clearing(config, iso)
                and bool(design.demand_curve)
                and reserve_position is not None
            )
            annual["capacity_revenue_source"] = "curve" if uses_curve else "fixed"
    annual["net_operating_income_with_capacity"] = (
        annual["net_operating_income"] + annual["capacity_revenue"]
    )

    # Attribute (certificate) revenue (W2-B, national-ces-eac-premium plan
    # §5.4): each plant's delivered MWh × its effective EAC price — the
    # element-wise max of the legacy per-fuel ``eac_price_*`` scalar and the
    # federal CES premium × credit fraction, resolved through the SAME
    # resolver the dispatch offers and capacity screens use
    # (policy/federal_ces.py::effective_unit_eac_prices; one certificate per
    # MWh, sold once). Real 2026$/MWh. Tax credits (PTC/ITC/45U/45Q) are
    # deliberately NOT in this line — they are tax instruments, not
    # certificates, and keep their existing conventions elsewhere.
    # ``attribute_revenue`` is reported as its own line item and is NOT
    # folded into net_operating_income (existing metrics stay byte-identical
    # for every pre-W2-B caller). Zero (price and revenue) when ``config``
    # is None — resolution needs the run's real ScenarioConfig.
    annual["attribute_price_usd_per_mwh"] = 0.0
    annual["attribute_revenue"] = 0.0
    if config is not None:
        # Adapt the plant frame to the resolver's FleetArrays seam: fuel
        # names -> FUEL_TYPE_MAP codes (a name outside the map gets -1, a
        # code no fuel carries -> legacy 0 and credit 0), CO2 rates in
        # tCO2/MWh at the LP boundary.
        plant_fleet = SimpleNamespace(
            fuel_type_idx=annual["fuel_type"]
            .map(FUEL_TYPE_MAP)
            .fillna(-1)
            .astype(int)
            .to_numpy(),
            emission_rate=annual["emission_rate_tco2_mwh"]
            .fillna(0.0)
            .to_numpy(dtype=float),
        )
        annual["attribute_price_usd_per_mwh"] = effective_unit_eac_prices(
            config, plant_fleet, year
        )
        annual["attribute_revenue"] = (
            annual["attribute_price_usd_per_mwh"] * annual["generation_mwh"]
        )

    avg_fuel_price = annual["fuel_cost"] / annual["fuel_mmbtu"].where(
        annual["fuel_mmbtu"] > 0.0
    )
    # heat_rate_btu_kwh / 1000 = MMBtu/MWh; × $/MMBtu = $/MWh fuel cost.
    annual["spark_spread"] = annual["avg_price_captured"] - (
        annual["heat_rate_btu_kwh"] * avg_fuel_price / BTU_KWH_PER_MMBTU_MWH
    )
    annual["co2_intensity"] = annual["co2_emissions_tons"] / gen_nz

    # discount_factor = 1 / (1 + r) ** (year - base_year); 1.0 at base_year.
    annual["discount_factor"] = 1.0 / (1.0 + discount_rate) ** (year - base_year)
    annual["npv_net_operating_income"] = (
        annual["net_operating_income"] * annual["discount_factor"]
    )
    annual["year"] = year

    return annual[
        [
            "plant_code",
            "generator_id",
            "zone",
            "fuel_type",
            "bin_label",
            "year",
            "nameplate_mw",
            "generation_mwh",
            "capacity_factor",
            "revenue",
            "fuel_mmbtu",
            "fuel_cost",
            "vom_cost",
            "carbon_cost",
            "nox_cost",
            "total_variable_cost",
            "gross_margin",
            "fom_cost",
            "net_operating_income",
            "capacity_revenue",
            "capacity_revenue_source",
            "net_operating_income_with_capacity",
            "attribute_price_usd_per_mwh",
            "attribute_revenue",
            "avg_price_captured",
            "avg_marginal_cost",
            "spark_spread",
            "co2_emissions_tons",
            "co2_intensity",
            "nox_emissions_lbs",
            "discount_factor",
            "npv_net_operating_income",
        ]
    ]


# Plant-level money/energy columns scaled by ``percent_owned`` before any
# company aggregation. Every dollar and MWh quantity that touches ownership
# must be scaled (build-prompt rule).
_OWNED_SCALE_COLUMNS: tuple[str, ...] = (
    "nameplate_mw",
    "generation_mwh",
    "revenue",
    "fuel_mmbtu",
    "fuel_cost",
    "vom_cost",
    "carbon_cost",
    "nox_cost",
    "total_variable_cost",
    "gross_margin",
    "fom_cost",
    "net_operating_income",
    "co2_emissions_tons",
    "nox_emissions_lbs",
    "npv_net_operating_income",
)

# Ownership-scaled columns that may be absent from a plant summary: the W2-B
# attribute-revenue line exists only in frames written after it landed, and
# company rollups must keep reading pre-W2-B parquets unchanged. Scaled and
# aggregated exactly like _OWNED_SCALE_COLUMNS when present, skipped when not.
_OWNED_OPTIONAL_SCALE_COLUMNS: tuple[str, ...] = ("attribute_revenue",)


def compute_company_summary(
    plant_annual: pd.DataFrame,
    ownership_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Roll plant-level annual financials up to parent companies.

    The plant-level summary is joined to the generator-level ownership
    mapping; every money and MWh quantity is scaled by ``percent_owned``
    (producing ``owned_*`` columns) *before* aggregation, so jointly owned
    plants split correctly between co-owners.

    Args:
        plant_annual: Output of :func:`compute_plant_annual_summary`.
        ownership_df: Output of
            :func:`market_sim.data.ownership.build_parent_mapping`, carrying
            ``plant_code``, ``generator_id``, ``parent_company`` and
            ``percent_owned``.

    Returns:
        A ``(company_total, company_by_fuel)`` tuple:

        * ``company_total`` -- one row per ``parent_company`` with portfolio
          metrics.
        * ``company_by_fuel`` -- one row per ``(parent_company, fuel_type)``.
    """
    owners = ownership_df[
        ["plant_code", "generator_id", "parent_company", "percent_owned"]
    ].copy()
    owners["plant_code"] = owners["plant_code"].astype("int64")
    owners["generator_id"] = owners["generator_id"].astype("string").str.strip()

    plant_annual = plant_annual.copy()
    plant_annual["plant_code"] = plant_annual["plant_code"].astype("int64")
    plant_annual["generator_id"] = (
        plant_annual["generator_id"].astype("string").str.strip()
    )

    merged = plant_annual.merge(owners, on=["plant_code", "generator_id"], how="left")
    merged["parent_company"] = merged["parent_company"].fillna("Other/Unknown")
    merged["percent_owned"] = merged["percent_owned"].fillna(1.0)

    scale_cols = _OWNED_SCALE_COLUMNS + tuple(
        c for c in _OWNED_OPTIONAL_SCALE_COLUMNS if c in merged.columns
    )
    for col in scale_cols:
        merged[f"owned_{col}"] = merged[col] * merged["percent_owned"]

    company_total = _aggregate_company(merged, ["parent_company"])
    company_by_fuel = _aggregate_company(merged, ["parent_company", "fuel_type"])
    return company_total, company_by_fuel


def _aggregate_company(merged: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Aggregate ownership-scaled plant rows and derive portfolio metrics."""
    agg_cols = _OWNED_SCALE_COLUMNS + tuple(
        c for c in _OWNED_OPTIONAL_SCALE_COLUMNS if f"owned_{c}" in merged.columns
    )
    agg = (
        merged.groupby(keys, dropna=False)
        .agg(**{f"owned_{c}": (f"owned_{c}", "sum") for c in agg_cols})
        .reset_index()
    )

    gen = agg["owned_generation_mwh"]
    gen_nz = gen.where(gen > 0.0)
    nameplate_nz = agg["owned_nameplate_mw"].where(agg["owned_nameplate_mw"] > 0.0)

    # Portfolio metrics -- computed only after aggregation.
    agg["portfolio_avg_price_captured"] = agg["owned_revenue"] / gen_nz
    agg["portfolio_emissions_intensity"] = agg["owned_co2_emissions_tons"] / gen_nz
    agg["portfolio_capacity_factor"] = gen / (nameplate_nz * HOURS_PER_YEAR)
    agg["portfolio_gross_margin_per_mwh"] = agg["owned_gross_margin"] / gen_nz
    agg["total_npv_net_operating_income"] = agg["owned_npv_net_operating_income"]

    return agg.sort_values("owned_generation_mwh", ascending=False).reset_index(
        drop=True
    )


def compute_trajectory_npv(
    annual_summaries: list[pd.DataFrame],
    years: list[int],
    discount_rate: float = 0.08,
    base_year: int = 2026,
) -> pd.DataFrame:
    """Stack multi-year annual summaries and accumulate NPV across the run.

    Works for either plant-level summaries (from
    :func:`compute_plant_annual_summary`) or company-level summaries (the
    ``company_total`` frame from :func:`compute_company_summary`): the key
    columns are auto-detected.

    Args:
        annual_summaries: One annual summary DataFrame per year.
        years: The calendar year of each summary, aligned with
            ``annual_summaries``.
        discount_rate: Discount rate from ``ScenarioConfig``.
        base_year: NPV reference year.

    Returns:
        One row per plant (or per company) with ``cumulative_npv_noi``,
        ``cumulative_generation_mwh``, ``cumulative_co2_tons`` and
        ``avg_annual_margin``.

    Raises:
        ValueError: When ``annual_summaries`` and ``years`` differ in length.
    """
    if len(annual_summaries) != len(years):
        raise ValueError(
            "annual_summaries and years must be the same length "
            f"({len(annual_summaries)} vs {len(years)})"
        )
    if not annual_summaries:
        return pd.DataFrame(
            columns=[
                "cumulative_npv_noi",
                "cumulative_generation_mwh",
                "cumulative_co2_tons",
                "avg_annual_margin",
            ]
        )

    sample = annual_summaries[0]
    is_company = "parent_company" in sample.columns
    keys = ["parent_company"] if is_company else ["plant_code", "generator_id"]
    # Company summaries carry ``owned_*`` columns; plant summaries do not.
    noi_col = (
        "total_npv_net_operating_income" if is_company else "npv_net_operating_income"
    )
    gen_col = "owned_generation_mwh" if is_company else "generation_mwh"
    co2_col = "owned_co2_emissions_tons" if is_company else "co2_emissions_tons"
    margin_col = "owned_gross_margin" if is_company else "gross_margin"

    stacked = []
    for summary, yr in zip(annual_summaries, years, strict=True):
        block = summary.copy()
        # Re-discount NPV to the trajectory base year if not already done.
        if noi_col not in block.columns:
            raise ValueError(f"summary for {yr} lacks column {noi_col!r}")
        stacked.append(block.assign(_year=yr))
    full = pd.concat(stacked, ignore_index=True)

    out = (
        full.groupby(keys, dropna=False)
        .agg(
            cumulative_npv_noi=(noi_col, "sum"),
            cumulative_generation_mwh=(gen_col, "sum"),
            cumulative_co2_tons=(co2_col, "sum"),
            _total_margin=(margin_col, "sum"),
        )
        .reset_index()
    )
    out["avg_annual_margin"] = out["_total_margin"] / len(years)
    out = out.drop(columns="_total_margin")
    del discount_rate, base_year  # discounting already applied per-year
    return out.sort_values("cumulative_npv_noi", ascending=False).reset_index(drop=True)
