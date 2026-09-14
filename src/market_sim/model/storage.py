"""Energy storage modeling.

Storage parameter structs and fleet construction. The state-of-charge
dynamics constraints themselves are built inside
:func:`market_sim.model.dispatch.build_constraints`; this module supplies the
data layer that feeds them -- per-unit attributes, their vectorized
struct-of-arrays form, and a default fleet builder.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel

from market_sim.config.constants import (
    CAISO_PS_PLANT_PARAMS,
    DEFAULT_MARKET_DESIGN,
    MARKET_DESIGN,
    PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO,
    PUMPED_STORAGE_DURATION_HOURS,
    PUMPED_STORAGE_RTE,
    STORAGE_ANNUAL_BUILD_CAP_MW,
    STORAGE_BASE_FLEET_MW,
    STORAGE_DEGRADATION_REPLACEMENT_FRACTION,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_ELCC_BY_DURATION,
    STORAGE_ELCC_BY_DURATION_BY_ISO,
    STORAGE_ELCC_SATURATION_EXPONENT,
    STORAGE_MEASURED_BASE_FLEET_ISOS,
    STORAGE_TECH_AVAILABLE_YEAR,
    STORAGE_TECH_BUILD_SHARE_CAP,
    STORAGE_TECH_POWER_SHARE,
    STORAGE_TECHS,
    STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.entry_config import ENTRY_EXHAUSTION_TRANCHE_MW
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.ancillary import as_revenue_per_mw_yr
from market_sim.model.capacity import CumulativeDeployment
from market_sim.policy.ira import ira_phaseout_fraction


class StorageUnit(BaseModel):
    """Attributes of a single energy-storage unit.

    ``eta_charge`` and ``eta_discharge`` are one-way efficiencies; their
    product is the round-trip efficiency. ``zone_idx`` is the integer code
    of ``zone`` within the enclosing ISO's zone ordering.
    """

    unit_id: str
    zone: str
    tech_name: str
    power_cap_mw: float
    energy_cap_mwh: float
    eta_charge: float = 1.0
    eta_discharge: float = 1.0
    zone_idx: int = 0
    # Dispatch cost per MWh discharged (added to the LP discharge slot).
    # Pumped storage carries the per-ISO calibrated throughput adder
    # (resolve_pumped_storage_dispatch_adder); grid batteries carry the
    # battery cycling/throughput adder
    # (ScenarioConfig.battery_dispatch_adder, default 0).
    vom: float = 0.0
    # Intra-year COD capacity ramp (backcast, ScenarioConfig.
    # storage_vintage_ramp): capacity online in each month Jan-Dec of the
    # backcast year, stepping up as the EIA-860 COD months pass. December
    # equals ``power_cap_mw`` / ``energy_cap_mwh``. ``None`` = online at
    # full capacity all year (the static default).
    monthly_power_mw: list[float] | None = None
    monthly_energy_mwh: list[float] | None = None
    # Cited pump-side (charge) power capability where it differs from the
    # generating rating (caiso_ps_plant_params, lane 5 — e.g. Helms 930 MW
    # pumping vs 1,212 MW generating). None = legacy symmetric caps. Applied
    # as a STATIC per-unit charge cap through the existing storage_charge_cap
    # LP channel (tighten-only vs power_cap_mw); never touches discharge.
    charge_power_cap_mw: float | None = None


@dataclass
class StorageArrays:
    """Vectorized storage attributes for dispatch computation.

    Every per-unit scalar attribute is stored as a ``(n_storage,)`` array,
    aligned across all fields by storage-unit index.
    """

    power_cap: np.ndarray
    energy_cap: np.ndarray
    eta_chg: np.ndarray
    eta_dis: np.ndarray
    zone_idx: np.ndarray
    tech_names: np.ndarray
    vom: np.ndarray

    @property
    def n_storage(self) -> int:
        """Return the number of storage units in the fleet."""
        return len(self.power_cap)


def storage_units_to_arrays(
    units: list[StorageUnit],
    zone_names: list[str],
) -> StorageArrays:
    """Convert a list of storage units into vectorized ``StorageArrays``.

    Each unit's ``zone`` is resolved to an integer index against
    ``zone_names`` so the result aligns with the dispatch zone ordering.
    """
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    return StorageArrays(
        power_cap=np.array([u.power_cap_mw for u in units], dtype=float),
        energy_cap=np.array([u.energy_cap_mwh for u in units], dtype=float),
        eta_chg=np.array([u.eta_charge for u in units], dtype=float),
        eta_dis=np.array([u.eta_discharge for u in units], dtype=float),
        zone_idx=np.array([zone_to_idx[u.zone] for u in units], dtype=int),
        tech_names=np.array([u.tech_name for u in units], dtype=str),
        vom=np.array([u.vom for u in units], dtype=float),
    )


def _distribute_storage(
    iso: ISOConfig,
    config: ScenarioConfig,
    total_mw: float,
) -> list[StorageUnit]:
    """Split ``total_mw`` of storage power across an ISO's zones and techs.

    Power is allocated to each load zone in proportion to its ``load_share``
    and across technologies by ``STORAGE_TECH_POWER_SHARE``. Each technology's
    duration and round-trip efficiency come from ``constants.STORAGE_TECHS``;
    the round-trip efficiency is split evenly into one-way charge and discharge
    efficiencies.

    Returns:
        One ``StorageUnit`` per (load zone, technology) pair with nonzero
        power capacity.
    """
    battery_adder = float(getattr(config, "battery_dispatch_adder", 0.0))
    units: list[StorageUnit] = []
    for z_idx, zone in enumerate(iso.zones):
        if zone.load_share <= 0.0:
            continue
        for tech_name, tech in STORAGE_TECHS.items():
            share = STORAGE_TECH_POWER_SHARE.get(tech_name, 0.0)
            power_mw = total_mw * zone.load_share * share
            if power_mw <= 0.0:
                continue
            rte = float(tech["rte"])
            if tech_name == "li_ion_4hr":
                rte = config.storage_rte_4hr
            elif tech_name == "li_ion_8hr":
                rte = config.storage_rte_8hr
            eta = rte**0.5
            units.append(
                StorageUnit(
                    unit_id=f"{zone.name}_{tech_name}",
                    zone=zone.name,
                    tech_name=tech_name,
                    power_cap_mw=power_mw,
                    energy_cap_mwh=power_mw * float(tech["duration_hr"]),
                    eta_charge=eta,
                    eta_discharge=eta,
                    zone_idx=z_idx,
                    vom=battery_adder,
                )
            )
    return units


def _resolve_pace(config: ScenarioConfig) -> str:
    """Return the validated ``storage_deployment`` pace from ``config``.

    Raises:
        ValueError: if ``config.iso`` or ``config.storage_deployment`` is not
            a known key of :data:`STORAGE_BASE_FLEET_MW`.
    """
    if config.iso not in STORAGE_BASE_FLEET_MW:
        supported = ", ".join(sorted(STORAGE_BASE_FLEET_MW))
        raise ValueError(f"Unknown iso '{config.iso}'. Supported: {supported}")
    paces = STORAGE_BASE_FLEET_MW[config.iso]
    pace = config.storage_deployment
    if pace not in paces:
        supported = ", ".join(sorted(paces))
        raise ValueError(f"Unknown storage_deployment '{pace}'. Supported: {supported}")
    return pace


def build_default_storage(
    iso: ISOConfig,
    config: ScenarioConfig,
) -> list[StorageUnit]:
    """Build a default storage fleet for an ISO and scenario.

    The total deployed power is the base-year capacity set by
    ``config.storage_deployment`` (see ``STORAGE_BASE_FLEET_MW``), split across
    load zones in proportion to each zone's ``load_share`` and across
    technologies by ``STORAGE_TECH_POWER_SHARE``.

    Args:
        iso: ISO topology supplying the zones and their load shares.
        config: Scenario config supplying the ``storage_deployment`` pace.

    Returns:
        One ``StorageUnit`` per (load zone, technology) pair with nonzero
        power capacity.

    Raises:
        ValueError: if ``config.storage_deployment`` is not a known pace.
    """
    pace = _resolve_pace(config)
    return _distribute_storage(iso, config, STORAGE_BASE_FLEET_MW[config.iso][pace])


def measured_storage_base_fleet_active(config: ScenarioConfig, iso: str) -> bool:
    """Return True when the storage base fleet seeds from measured EIA-860.

    ``STORAGE_BASE_FLEET_MW`` is a FORECAST object (its own docstring calls it
    "the base year (2026)"), so any run whose base year is historical must seed
    from the EIA-860 fleet that actually existed instead
    (:func:`load_eia860_storage`). Two legs, both governed by
    ``config.storage_measured_base_fleet`` (default on) and both resolving
    through the process-global EIA-860 vintage dir the runner arms
    (``config.paths.set_eia860_vintage``):

    * **Backcast** (FFR-4D): the fleet as of the solve year. Scoped to
      :data:`STORAGE_MEASURED_BASE_FLEET_ISOS` (CAISO only today) because
      enrolling an ISO moves that ISO's designated keeper, which must be
      re-solved and re-gated in its own lane (rule 25 [R-ISO-SCOPE]).
    * **Capacity hindcast** (FFR-9A; ``mode="forecast"`` + ``hindcast=True`` +
      ``eia860_vintage_year``): the run's own vintage EIA-860 measured fleet —
      the FFR-3V renewable-pool pattern's storage sibling. EVERY ISO,
      deliberately un-scoped: a hindcast is not a keeper, the vintage sheet is
      measured data rather than a tuned curve (rule 13 [R-MEASURED] — it is
      exactly what a run at that vintage cutoff may know, and it regenerates
      for any vintage), and rule 14 [R-ACCURATE] does not gate an accurate
      input behind a per-ISO enrollment where no keeper byte-identity is at
      stake. A hindcast without a vintage keeps the scenario scalar — nothing
      measured to seed from (the FFR-3V precedent). A plain forecast
      (``hindcast=False``) always keeps the scalar, even when an
      ``eia860_vintage_year`` is set, mirroring the runner's vintage-arming
      predicate.
    """
    if not config.storage_measured_base_fleet:
        return False
    if config.mode == "backcast":
        return iso in STORAGE_MEASURED_BASE_FLEET_ISOS
    return (
        bool(getattr(config, "hindcast", False))
        and config.eia860_vintage_year is not None
    )


# Duration (hours) assumed for an EIA-860 storage unit whose energy
# capacity is blank -- a rare gap; ERCOT's 2023 fleet reports it in full.
_EIA860_STORAGE_FALLBACK_DURATION_HR: float = 2.0


def _optional_numeric(df: pd.DataFrame, column: str) -> np.ndarray:
    """Return ``df[column]`` as a float array, or all-NaN if the column is absent.

    Column-safe access for optional EIA-860 fields (e.g. ``Planned Retirement
    Year`` / ``Month``): a storage/generator vintage that does not carry the
    column yields an all-NaN array, which the per-unit reduction reads as
    "no planned retirement".
    """
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").to_numpy()
    return np.full(len(df), np.nan)


def _unit_monthly_mask(
    operating_year: object,
    operating_month: object,
    retirement_year: object,
    retirement_month: object,
    year: int,
) -> np.ndarray:
    """Return a storage unit's ``(12,)`` float online mask (COD + retirement).

    Wraps :func:`market_sim.data.cod_ramp.monthly_online_mask` with the
    loaders' shared month conventions -- a missing online month falls back to
    :data:`market_sim.data.cod_ramp.COD_FALLBACK_MONTH` and a missing
    retirement month to December -- so the storage off-ramp matches the
    thermal/renewable COD ramp exactly. Inputs may be NaN floats (EIA-860
    numeric columns); element ``m`` is ``1.0`` when the unit is online in
    calendar month ``m + 1`` of ``year`` and ``0.0`` otherwise.
    """
    from market_sim.data.cod_ramp import COD_FALLBACK_MONTH, monthly_online_mask

    def _i(value: object) -> int | None:
        try:
            f = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return None if f != f else int(f)

    return monthly_online_mask(
        _i(operating_year),
        (_i(operating_month) or COD_FALLBACK_MONTH),
        _i(retirement_year),
        _i(retirement_month),
        year,
    ).astype(float)


def load_eia860_storage(
    iso: str, year: int, config: ScenarioConfig
) -> list[StorageUnit]:
    """Build a storage fleet from EIA-860 operable energy-storage data.

    Reads the EIA-860 operable energy-storage schedule, keeps units online
    by the end of ``year``, assigns each to a model zone via the eGRID
    ORIS->zone lookup (plant coordinates / FIPS county), and aggregates
    power and energy capacity per zone into one ``StorageUnit`` each.
    Pumped-storage hydro (reported on the generator schedule, not the
    energy-storage schedule) is appended via
    :func:`load_eia860_pumped_storage`. This grounds a calibration backcast
    in the historical storage fleet rather than the forward-looking
    ``STORAGE_BASE_FLEET_MW`` scenario constant.

    Co-located/hybrid batteries stay separate resources: the energy-storage
    schedule reports the battery half of a solar+storage plant on its own
    row (the PV half lives on the solar schedule feeding the renewables
    loader), so a Moss Landing-style hybrid contributes its full battery
    power/energy here without double-counting its PV.

    When ``config.storage_vintage_ramp`` is on, each unit contributes only to
    the months it actually operated -- capacity commissioned *during* ``year``
    enters from its EIA-860 Operating Month, and a unit with a planned
    retirement in ``year`` drops out from its Planned Retirement Month (the
    OFF-ramp mirroring the COD ON-ramp; the energy-storage operable vintage does
    not yet carry the retirement columns, so the off-ramp is a column-safe
    no-op there today). A zone aggregate whose capacity varies intra-year
    carries a Jan-Dec ``monthly_power_mw`` / ``monthly_energy_mwh`` profile
    (December = the year-end scalar caps) that :func:`storage_cap_profiles`
    expands into hour-varying dispatch bounds. This is the storage analogue of
    the renewables ``vintage_capacity_ramp`` and is first-order for CAISO, which
    added 3.0 GW mid-2023 and 3.6 GW mid-2024.

    EIA-860 does not report round-trip efficiency, so the 4-hour lithium-ion
    RTE is applied uniformly. It is read through :func:`_storage_rte`, so a
    calibration sweep of ``config.storage_rte_4hr`` reaches the backcast
    fleet exactly as it reaches the forward-entry path -- rather than being
    silently pinned to the :data:`STORAGE_TECHS` constant. Battery units bid
    ``config.battery_dispatch_adder`` per MWh discharged (default 0), the
    calibration knob that tames LP over-cycling vs the EIA-930 battery
    benchmark.

    Args:
        iso: ISO identifier; zones come from its topology config.
        year: Backcast year; units commissioned after it are excluded.
        config: Scenario config; supplies the ``storage_rte_4hr`` override,
            the ``storage_vintage_ramp`` COD-ramp toggle, and the
            ``battery_dispatch_adder`` throughput cost carried on each
            battery unit's ``vom``.

    Returns:
        One aggregated ``StorageUnit`` per zone with nonzero storage
        capacity. Empty when the EIA-860 file is missing or no operable
        units fall inside the ISO.
    """
    from market_sim.config.paths import active_eia860_dir
    from market_sim.data.zone_assignment import build_zone_lookup

    path = active_eia860_dir() / "eia860_energy_storage_operable.parquet"
    if not path.exists():
        return []
    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        return []
    if not zone_lookup:
        return []

    df = pd.read_parquet(path)
    df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
    # Compressed-air energy storage is NOT a battery and is not modelled as
    # storage: the same unit sits on the generator schedule (prime mover
    # ``CE``), where ``fleet.eia860._map_fuel_type`` carries it as a gas CT at
    # its net summer rating — owner card S7 (SOCO, McIntosh unit 1, EIA 7063:
    # 110 MW nameplate / 25 MW rating). Keeping it here too would represent
    # one physical unit twice (rule 19). It is the ONLY compressed-air row on
    # the national schedule, so every other ISO is byte-identical.
    if "Technology" in df.columns:
        df = df[
            ~df["Technology"].astype(str).str.contains("Compressed Air", case=False)
        ]
    power = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
    energy = pd.to_numeric(df["Nameplate Energy Capacity (MWh)"], errors="coerce")
    op_year = pd.to_numeric(df["Operating Year"], errors="coerce")
    op_month = pd.to_numeric(df["Operating Month"], errors="coerce")
    # Planned-retirement OFF-ramp inputs, mirroring the COD ON-ramp. The
    # EIA-860 energy-storage operable sheet does not currently carry these
    # columns (batteries rarely retire mid-backcast), so the column-safe .get
    # makes the off-ramp a no-op there while keeping ONE convention the day a
    # vintage gains them.
    ret_year = _optional_numeric(df, "Planned Retirement Year")
    ret_month = _optional_numeric(df, "Planned Retirement Month")

    # Capacity online per zone per month (12,); December is the year-end total.
    # Each unit contributes its nameplate only to the months it actually
    # operated -- the COD ON-ramp plus the planned-retirement OFF-ramp, via the
    # shared month-precise mask (month missing -> COD_FALLBACK_MONTH for online,
    # December for retirement).
    per_zone_power: dict[str, np.ndarray] = {}
    per_zone_energy: dict[str, np.ndarray] = {}
    for code, p_mw, e_mwh, oy, om, ry, rm in zip(
        df["Plant Code"], power, energy, op_year, op_month, ret_year, ret_month
    ):
        if p_mw != p_mw or p_mw <= 0.0:  # NaN or non-positive
            continue
        if oy == oy and oy > year:  # commissioned after the backcast year
            continue
        try:
            zone = zone_lookup.get(int(code))
        except (TypeError, ValueError):
            zone = None
        if zone is None:
            continue
        if e_mwh != e_mwh or e_mwh <= 0.0:  # blank energy capacity
            e_mwh = p_mw * _EIA860_STORAGE_FALLBACK_DURATION_HR
        mask = _unit_monthly_mask(oy, om, ry, rm, year)
        if not mask.any():  # retired before / built after the backcast year
            continue
        zone_p = per_zone_power.setdefault(zone, np.zeros(12))
        zone_e = per_zone_energy.setdefault(zone, np.zeros(12))
        zone_p += float(p_mw) * mask
        zone_e += float(e_mwh) * mask

    eta = _storage_rte("li_ion_4hr", config) ** 0.5
    # Throughput/cycling cost per MWh discharged (degradation + ancillary-
    # service opportunity cost) -- the battery analogue of the pumped-storage
    # adder below; see ScenarioConfig.battery_dispatch_adder.
    adder = float(getattr(config, "battery_dispatch_adder", 0.0))
    units: list[StorageUnit] = []
    for z_idx, zone in enumerate(get_iso_config(iso).zone_names):
        monthly_p = per_zone_power.get(zone)
        if monthly_p is None or monthly_p[-1] <= 0.0:
            continue
        monthly_e = per_zone_energy[zone]
        # A monthly profile is attached only when the ramp is enabled and the
        # zone's capacity actually varies intra-year -- a COD step up OR a
        # retirement step down; otherwise the unit stays static and the
        # dispatch bounds remain 1-D.
        ramped = config.storage_vintage_ramp and not np.allclose(
            monthly_p, monthly_p[-1]
        )
        units.append(
            StorageUnit(
                unit_id=f"{zone}_eia860_storage",
                zone=zone,
                tech_name="li_ion",
                power_cap_mw=float(monthly_p[-1]),
                energy_cap_mwh=float(monthly_e[-1]),
                eta_charge=eta,
                eta_discharge=eta,
                zone_idx=z_idx,
                vom=adder,
                monthly_power_mw=([float(x) for x in monthly_p] if ramped else None),
                monthly_energy_mwh=([float(x) for x in monthly_e] if ramped else None),
            )
        )
    units.extend(load_eia860_pumped_storage(iso, year, config))
    return units


def resolve_pumped_storage_dispatch_adder(
    iso: str, config: ScenarioConfig | None
) -> float:
    """Return the pumped-storage dispatch adder ($/MWh discharged) for an ISO.

    An explicit ``config.pumped_storage_dispatch_adder`` wins. ``None`` (the
    field default, or no config at all) falls back to the per-ISO calibrated
    default in :data:`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`. That map is
    currently empty -- PJM's former $10 adder was retired (it had been fitted to
    a mis-measured PS *net*-generation figure, not a real reserve cost; see the
    constant's comment and docs/multi-iso/pjm-ps-cycling-diagnosis-2026-06.md) --
    so every ISO without an explicit override resolves to 0.0, i.e. pumped
    storage arbitrages on its physical RTE like batteries.
    """
    explicit = (
        getattr(config, "pumped_storage_dispatch_adder", None)
        if config is not None
        else None
    )
    if explicit is not None:
        return float(explicit)
    return PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO.get(iso.upper(), 0.0)


def storage_cap_profiles(
    units: list[StorageUnit],
    arrays: StorageArrays,
    hours: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the dispatch power/energy cap bounds for a storage fleet.

    A fleet with no intra-year COD ramp passes through unchanged as the
    static ``(n_storage,)`` arrays. When any unit carries a monthly COD
    profile (``StorageUnit.monthly_power_mw``, set by
    :func:`load_eia860_storage` under ``config.storage_vintage_ramp``), both
    caps expand to ``(n_storage, hours)``: a ramped unit's charge/discharge
    and SOC bounds step up at each month boundary as capacity reaches
    commercial operation, so GWs commissioned mid-year cannot dispatch
    before their COD. ``units`` must be in the same order as ``arrays``
    (as built by :func:`storage_units_to_arrays`).

    Note: the LP's annual cyclic SOC constraint pins a ramped unit's
    year-end SOC back to its January level, which the January bound caps at
    zero -- the unit ends the year empty. That is a one-cycle artifact,
    negligible against fleet-scale annual throughput.
    """
    if not any(u.monthly_power_mw is not None for u in units):
        return arrays.power_cap, arrays.energy_cap
    from market_sim.data.fleet import _hour_to_month_index

    month_idx = _hour_to_month_index(hours)
    power = np.repeat(arrays.power_cap[:, np.newaxis], hours, axis=1)
    energy = np.repeat(arrays.energy_cap[:, np.newaxis], hours, axis=1)
    for s, unit in enumerate(units):  # s: storage-unit index
        if unit.monthly_power_mw is None:
            continue
        power[s] = np.asarray(unit.monthly_power_mw, dtype=float)[month_idx]
        energy[s] = np.asarray(unit.monthly_energy_mwh, dtype=float)[month_idx]
    return power, energy


# ERCOT measured per-resource-type AS series (built by
# scripts/build_ercot_as_by_restype). The ``storage`` column is the hourly MW
# that batteries cleared as upward AS and therefore could not also offer as
# energy arbitrage.
_AS_RESTYPE_DIR = RAW_DATA_DIR / "ercot-AS"


def reserve_storage_as_power(
    power_cap: np.ndarray, year: int, hours: int
) -> np.ndarray:
    """Reserve ERCOT's measured hourly storage up-AS MW from the power cap.

    ERCOT batteries clear most of their value as ancillary services (RegUp +
    RRS + ECRS): that power is committed and cannot also serve energy. The
    energy-only LP otherwise dumps the full fleet into the few highest-price
    hours. This subtracts the measured hourly storage up-AS MW
    (``ercot_<year>_as_by_restype_hourly.parquet``, ``storage`` column) from
    the dispatch power cap, allocated across the fleet pro-rata by available
    power, so the discharge/charge bound in those hours reflects only the
    arbitrage-available power. Returns the (possibly broadcast) ``(n_storage,
    hours)`` cap; a missing file or empty fleet passes ``power_cap`` through.

    Note: this reserves *power*, not state of charge -- the first-order
    constraint that binds in the scarcity hours where the LP over-discharges.
    """
    pc = np.asarray(power_cap, dtype=float)
    if pc.size == 0:
        return power_cap
    path = _AS_RESTYPE_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    if not path.exists():
        return power_cap
    as_storage = pd.read_parquet(path)["storage"].to_numpy(dtype=float)
    if len(as_storage) < hours:
        as_storage = np.concatenate([as_storage, np.zeros(hours - len(as_storage))])
    as_storage = as_storage[:hours]
    pc2 = np.repeat(pc[:, np.newaxis], hours, axis=1) if pc.ndim == 1 else pc.copy()
    total = pc2.sum(axis=0)  # (hours,) fleet power available
    with np.errstate(divide="ignore", invalid="ignore"):
        weight = np.where(total[np.newaxis, :] > 0.0, pc2 / total[np.newaxis, :], 0.0)
    return np.clip(pc2 - weight * as_storage[np.newaxis, :], 0.0, None)


def ercot_storage_as_soc_min(
    energy_cap: np.ndarray,
    year: int,
    hours: int,
    deploy_mw: np.ndarray | None = None,
    charge_cap: np.ndarray | None = None,
    discharge_min: np.ndarray | None = None,
    eta_chg: np.ndarray | float = 1.0,
    eta_dis: np.ndarray | float = 1.0,
    daily_pin: bool = False,
) -> np.ndarray:
    """SOC floor backing ERCOT's measured battery AS awards (per-product duration).

    The measured-award power reservation (:func:`reserve_storage_as_power`,
    ``storage_as_commitment``) reserves *power*, not state of charge — its own
    docstring names that as "the first-order constraint that binds in the
    scarcity hours where the LP over-discharges". ERCOT Nodal Protocols
    §3.17.3 requires an ESR to hold SOC backing each award for the product's
    duration (RegUp/RRS 1 h, ECRS 2 h, Non-Spin 4 h —
    :data:`market_sim.model.reserves.spec.ERCOT_AS_PRODUCT_DURATION_H`, the
    co-opt's own published constants, no new number), so an awarded battery
    holds ``Σ_p award_p(t) × duration_p`` MWh it cannot arbitrage away. This
    is the ercot-167 mechanism (``ercot_storage_as_soc_reserve``, matrix §5.1
    item 10 — the ercot-162 §2 named successor): measured at the 2023 actual
    >$1000 hours the fleet held 2,125 MW of awards = 2,705 MWh frozen of its
    ~4.1 GWh, leaving ~350–470 MW sustainable vs the 423 MW the SCED corpus
    shows it actually discharged (the keeper's LP discharges 666 MW there).

    Product split: measured per-product PWRSTR awards
    (``ercot_<year>_storage_as_products_hourly.parquet``,
    ``scripts/data/derive_ercot_storage_as_products.py``), consumed as SHARES
    of the same committed total series the power reservation subtracts
    (rule 19: one measured award basis for both sides; the shares file can
    never move the armed total).

    Deployment reconciliation (rule 19 — measured by the first 2023 probe,
    which went INFEASIBLE without it): ``ercot_storage_as_deployment``
    force-discharges the measured award draw-down at the evening ramp, and
    every deployed MWh is AS energy leaving the tank — the backing behind it
    is spent, not still owed. ``deploy_mw`` (the same
    :func:`~market_sim.results.scarcity.ercot_storage_as_deployment_mw`
    series the discharge floor forces, when that flag is armed) is therefore
    subtracted from the freeze as an INTRA-DAY CUMULATIVE:
    ``floor(t) = max(0, freeze(t) − Σ_{same day, ≤t} deploy)``. Per hour the
    floor then releases at least the forced discharge (feasible by
    construction against the deployment floor), the backing rebuilds with the
    next day's procurement, and with deployment unarmed (``None``) the plain
    freeze applies. Allocated across units pro-rata by ENERGY
    cap — the stable basis for an energy floor (the power cap at the call
    site is already award-docked by :func:`reserve_storage_as_power`, so
    power weights would be degenerate exactly in the high-award hours) — and
    clipped at each unit's energy cap. Missing either file → all-zero floor
    (inert), the family convention. Zero fitted parameters (rule 23); forward runs
    price the split endogenously (``ercot_storage_as_endogenous``), so this
    measured record is backcast-only, a capability input, never a pinned
    outcome (rule 13).

    Returns the ``(n_storage, hours)`` SOC lower bound for
    ``dispatch.build_variable_bounds(storage_soc_min=...)``.
    """
    ec = np.asarray(energy_cap, dtype=float)
    ec2 = np.repeat(ec[:, np.newaxis], hours, axis=1) if ec.ndim == 1 else ec.copy()
    soc_min = np.zeros_like(ec2)
    if ec.size == 0:
        return soc_min
    total_path = _AS_RESTYPE_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    prod_path = _AS_RESTYPE_DIR / f"ercot_{year}_storage_as_products_hourly.parquet"
    if not (total_path.exists() and prod_path.exists()):
        return soc_min
    from market_sim.model.reserves.spec import (
        ERCOT_AS_PRODUCT_DURATION_H,
        ERCOT_AS_PRODUCTS,
    )

    def _series(frame: "pd.DataFrame", col: str) -> np.ndarray:
        v = frame[col].to_numpy(dtype=float)
        if len(v) < hours:
            v = np.concatenate([v, np.zeros(hours - len(v))])
        return v[:hours]

    committed = _series(pd.read_parquet(total_path), "storage")
    prods = pd.read_parquet(prod_path)
    # Column names follow the product order of ERCOT_AS_PRODUCTS
    # (RegUp, RRS, ECRS, NonSpin) — asserted so a spec reorder cannot silently
    # mispair a duration with a product column.
    names = tuple(n.lower() for n, _c, _t in ERCOT_AS_PRODUCTS)
    assert names == ("regup", "rrs", "ecrs", "nonspin"), names
    per = np.stack([_series(prods, n) for n in names])  # (4, hours)
    tot = per.sum(axis=0)
    dur = np.asarray(ERCOT_AS_PRODUCT_DURATION_H, dtype=float)[:, np.newaxis]
    with np.errstate(divide="ignore", invalid="ignore"):
        share = np.where(tot[np.newaxis, :] > 0.0, per / tot[np.newaxis, :], 0.0)
    # (hours,) fleet MWh floor: committed total split by measured product
    # shares, weighted by the published per-product SOC durations.
    freeze = (share * dur).sum(axis=0) * committed
    if deploy_mw is not None:
        # Intra-day cumulative deployed AS energy (MWh; hourly MW × 1 h) —
        # backing already spent through the armed deployment discharge floor.
        dep = np.asarray(deploy_mw, dtype=float)[:hours]
        if dep.shape[0] < hours:
            dep = np.concatenate([dep, np.zeros(hours - dep.shape[0])])
        n_days = hours // 24
        cum = dep[: n_days * 24].reshape(n_days, 24).cumsum(axis=1).reshape(-1)
        if hours % 24:  # ragged tail (never on the 8760 clock; guard anyway)
            tail = dep[n_days * 24 :].cumsum()
            cum = np.concatenate([cum, tail])
        freeze = np.maximum(freeze - cum, 0.0)
    fleet_e = ec2.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        weight = np.where(
            fleet_e[np.newaxis, :] > 0.0, ec2 / fleet_e[np.newaxis, :], 0.0
        )
    soc_min = np.minimum(weight * freeze[np.newaxis, :], ec2)
    if charge_cap is not None and daily_pin:
        soc_min = _pin_reachability_clip(
            soc_min, ec2, charge_cap, discharge_min, eta_chg, eta_dis
        )
    return soc_min


def _pin_reachability_clip(
    soc_min: np.ndarray,
    soc_ub: np.ndarray,
    chg_ub: np.ndarray,
    dis_lb: np.ndarray | None,
    eta_chg: np.ndarray | float,
    eta_dis: np.ndarray | float,
) -> np.ndarray:
    """Clip a SOC floor to what the daily-pinned scaffold can physically hold.

    ``storage_daily_cycle_hours`` pins every day-start SOC of a unit to ONE
    shared level S0, so the floor must admit an S0 satisfying every pin hour
    at once: the 2023 probe measured the raw award-backing floor infeasible
    by exactly this coupling — the floor at high-award midnights (889 MWh on
    the West unit) exceeded the unit's energy cap at capability-dip midnights
    elsewhere in the year (546 MWh), leaving no valid shared S0 (max feasible
    uniform floor scale 0.997; the conflict enters at the Oct-2023 capability
    hole boundary). This clips the floor by the unit's max-reachable SOC path
    under the model's own scaffolding — S0 capped at the tightest pin-hour
    energy cap, then a within-day forward pass at the award-docked charge
    power net of the forced deployment discharge, and a backward pass bounding
    late-day SOC by what the docked discharge power can return to S0 by the
    day boundary. Every input is a measured array already in the LP (caps,
    docked power, forced floor, efficiencies); no parameter is introduced —
    the clip removes only backing the pinned model could not have carried
    (~0.3 % of the 2023 floor at its worst hours), and is a no-op when the
    plain floor is already reachable.
    """
    nS, hours = soc_min.shape
    n_days = hours // 24
    if n_days < 2 or hours % 24:
        return soc_min
    ec = eta_chg if np.ndim(eta_chg) else np.full(nS, float(eta_chg))
    ed = eta_dis if np.ndim(eta_dis) else np.full(nS, float(eta_dis))
    ec = np.asarray(ec, dtype=float)[:, np.newaxis, np.newaxis]
    ed = np.asarray(ed, dtype=float)[:, np.newaxis, np.newaxis]
    ub = soc_ub[:, : n_days * 24].reshape(nS, n_days, 24)
    chg = chg_ub[:, : n_days * 24].reshape(nS, n_days, 24)
    forced = (
        dis_lb[:, : n_days * 24].reshape(nS, n_days, 24)
        if dis_lb is not None
        else np.zeros_like(ub)
    )
    # Shared pin level: S0 must fit under every day-start energy cap.
    s0_cap = ub[:, :, 0].min(axis=1)[:, np.newaxis, np.newaxis]  # (nS,1,1)
    # Forward pass: max SOC reachable from S0 given docked charging net of the
    # forced deployment discharge. reach[d,h] = s0 + Σ_{j<=h}(η·chg − forced/η)
    # capped by the running energy-cap minimum (a cap dip caps everything after
    # it until recharge — the running-min is a safe lower envelope of the true
    # hourly-capped recursion and keeps the pass a pure cumsum).
    gain = (ec * chg - forced / ed).cumsum(axis=2)
    # SOC at the pin hour (local h=0) is EXACTLY S0, so gains accumulate from
    # h=1 (subtract the h=0 term). Exact unconstrained max path is then
    # S0 + Σ_{j=1..h} gain_j (charge max every hour, only the forced discharge
    # drains); the running-min energy cap is a safe (over-clipping only after a
    # dip) envelope that keeps the pass a pure cumsum.
    gain = gain - gain[:, :, 0:1]
    fwd = np.minimum(s0_cap + gain, np.minimum.accumulate(ub, axis=2))
    # Backward pass: SOC at hour h must be dischargeable back to S0 by the day
    # boundary at the docked discharge power (dis_ub == chg_ub basis here: the
    # docked power cap bounds both directions in the LP bounds builder).
    drop = (chg / ed)[:, :, ::-1].cumsum(axis=2)[:, :, ::-1]
    bwd = s0_cap + np.concatenate([drop[:, :, 1:], np.zeros((nS, n_days, 1))], axis=2)
    env = np.minimum(fwd, bwd).reshape(nS, n_days * 24)
    if hours > n_days * 24:
        env = np.concatenate([env, soc_ub[:, n_days * 24 :]], axis=1)
    return np.minimum(soc_min, np.maximum(env, 0.0))


# Measured ERCOT hourly battery-fleet capability (60-Day DAM disclosure
# non-OUT PWRSTR/ESR HSL), derived by scripts/data/derive_ercot_storage_capability.py
# (provenance, basis decision and the FROZEN-AGAINST-RESIDUALS contract live
# in that script's docstring).
_STORAGE_CAPABILITY_PATH = RAW_DATA_DIR / "ercot-storage-capability.csv"


def ercot_storage_capability_caps(
    power_cap: np.ndarray,
    energy_cap: np.ndarray,
    units: list["StorageUnit"],
    year: int,
    hours: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Re-base ERCOT battery caps on the measured disclosure capability.

    Backcast overlay (``config.ercot_storage_capability_measured``): the
    hourly ISO-wide battery power capability follows ERCOT's 60-Day DAM
    disclosure registered non-OUT HSL (``data/raw/ercot-storage-capability.csv``)
    instead of the EIA-860 COD-ramped schedule, which the summer-availability
    audit measured ~2 GW low in both summers (5.8 vs 7.7 GW Aug-2024, 10.6 vs
    12.5 GW Jul-2025 -- docs/DIAGNOSIS-ercot-summer-availability-audit-2026-07.md
    §1c). The measured series embeds real COD energization timing, hybrid
    halves, and real storage outages, so it replaces both the EIA-860 MW ramp
    and the (absent) storage outage model.

    EIA-860 stays the ZONE and DURATION basis: the ISO-wide measured MW is
    allocated across battery units (one per zone) by their EIA-860 power
    shares hour-by-hour, and each unit's energy cap is the re-based power
    times its EIA-860 fleet duration (energy/power) -- the disclosure is
    resource-keyed with no plant crosswalk, and the audit found the EIA-860
    energy envelope feasible (§1a), so only the power basis is measured.

    Uncovered hours (NaN in the CSV -- the Oct-2023 publication hole) keep the
    EIA-860 caps unchanged. Pumped storage is untouched (not a PWRSTR/ESR).
    A missing CSV or an empty battery fleet passes both caps through. Returns
    ``(power_cap, energy_cap)`` broadcast to ``(n_storage, hours)``.
    """
    pc = np.asarray(power_cap, dtype=float)
    ec = np.asarray(energy_cap, dtype=float)
    if pc.size == 0 or not units or not _STORAGE_CAPABILITY_PATH.exists():
        return power_cap, energy_cap
    df = pd.read_csv(_STORAGE_CAPABILITY_PATH)
    df = df[df["year"] == int(year)]
    if df.empty:
        return power_cap, energy_cap
    sys_mw = (
        df.set_index("hour")["capability_mw"]
        .reindex(range(int(hours)))
        .to_numpy(dtype=float)
    )
    batt = _battery_mask(units)
    if not batt.any() or not np.isfinite(sys_mw).any():
        return power_cap, energy_cap

    pc2 = np.repeat(pc[:, np.newaxis], hours, axis=1) if pc.ndim == 1 else pc.copy()
    ec2 = np.repeat(ec[:, np.newaxis], hours, axis=1) if ec.ndim == 1 else ec.copy()
    bp = pc2[batt]  # (n_batt, hours) EIA-860 battery power
    be = ec2[batt]
    total = bp.sum(axis=0)  # (hours,)
    # Zone shares / durations from EIA-860; hours where the ramped EIA-860
    # fleet is zero fall back to the year-end (December) mix so early-year
    # measured MW can still be placed.
    total_end = float(bp[:, -1].sum())
    if total_end <= 0.0:
        return power_cap, energy_cap
    share_end = bp[:, -1] / total_end
    with np.errstate(divide="ignore", invalid="ignore"):
        share = np.where(
            total > 0.0,
            bp / np.where(total > 0.0, total, 1.0),
            share_end[:, np.newaxis],
        )
        duration = np.where(
            bp > 0.0,
            be / np.where(bp > 0.0, bp, 1.0),
            (be[:, -1] / np.where(bp[:, -1] > 0.0, bp[:, -1], 1.0))[:, np.newaxis],
        )
    covered = np.isfinite(sys_mw)
    new_p = np.where(covered[np.newaxis, :], share * np.nan_to_num(sys_mw), bp)
    new_e = np.where(covered[np.newaxis, :], new_p * duration, be)
    pc2[batt] = new_p
    ec2[batt] = new_e
    return pc2, ec2


def _battery_mask(units: list["StorageUnit"]) -> np.ndarray:
    """Boolean (n_storage,) mask of battery units (pumped storage excluded).

    CAISO's LESR award series covers batteries (standalone + co-located);
    pumped-storage hydro is not an LESR and holds none of that award.
    """
    return np.array([u.tech_name != "pumped_storage" for u in units], dtype=bool)


# ERCOT measured storage RT discharge-offer surface (ercot-162), derived by
# scripts/data/derive_ercot_storage_rt_offer_surface.py. Per (delivery year ×
# net-load-percentile bin), the MW-weighted absolute-$ quantile ladder of the
# battery fleet's above-LSL, HASL-capped SCED discharge offers, plus the
# a-priori K-tranche (width, price) construction the LP consumes.
_STORAGE_RT_OFFER_PATH = (
    RAW_DATA_DIR / "_validation-source" / "ercot_storage_rt_offer_condbinned.json"
)


def ercot_storage_rt_offer_tranches(
    units: list["StorageUnit"],
    year: int,
    net_load_mw: np.ndarray,
    hours: int,
    surface_path: "str | None" = None,
) -> "tuple[np.ndarray, np.ndarray, np.ndarray] | None":
    """Build the ERCOT battery RT discharge-offer tranche parameters.

    The apply side of ``config.ercot_storage_rt_offer_surface`` (ercot-162):
    split each ERCOT battery unit's discharge into K priced tranches at the
    measured per-net-load-bin absolute-$ ladder
    (:data:`_STORAGE_RT_OFFER_PATH`), REPLACING the flat
    ``battery_dispatch_adder`` on ERCOT battery discharge (rule 19; pumped
    storage and other ISOs untouched — pumped storage is excluded by
    :func:`_battery_mask`).

    Binning matches the RT/DAM offer walls' apply convention exactly: the
    apply-time hour's bin is the searchsorted rank of the SOLVE's own net load
    (``net_load_mw``) against the artifact's ``netload_pct_edges`` — so the
    surface is forward-native (a forecast year bins by its own assembled net
    load). The ladder itself is standing (measured flat across bins), so the
    gap/ordinary discrimination is the LP's own crossing depth (FINDING §4).

    Year scope (rule 13): the artifact is year-scoped with no cross-year pooled
    fallback. A solve year absent from the artifact returns ``None`` (the arm is
    a no-op that year — the flat adder is retained). An apply-time net-load bin
    absent from the year's block borrows that year's within-year pooled ladder
    (same instrument, same year), the derive's disclosed backfill.

    Args:
        units: The storage fleet (battery + pumped-storage units).
        year: Solve/weather year — selects the artifact's year block.
        net_load_mw: ``(hours,)`` system net load (demand − wind − solar) of the
            solve, for the apply-time bin assignment.
        hours: Horizon length.
        surface_path: Optional artifact path override (defaults to
            :data:`_STORAGE_RT_OFFER_PATH`).

    Returns:
        ``(arm_batt_idx, width_frac, price_KT)`` where ``arm_batt_idx`` is the
        ``(n_arm,)`` int array of armed battery storage-unit indices,
        ``width_frac`` is the ``(K,)`` tranche width fractions of the hourly
        power cap (Σ ≤ 1), and ``price_KT`` is the ``(K, hours)`` tranche price
        in $/MWh for each hour's net-load bin. ``None`` when the fleet has no
        battery, the artifact is missing, or the year is absent (arm inert).
    """
    import json
    from pathlib import Path

    path = Path(surface_path) if surface_path else _STORAGE_RT_OFFER_PATH
    if not path.exists():
        return None
    batt = _battery_mask(units)
    arm_batt_idx = np.flatnonzero(batt)
    if arm_batt_idx.size == 0:
        return None

    surface = json.loads(path.read_text())
    prov = surface.get("_provenance", {})
    edges = np.asarray(prov.get("netload_pct_edges", ()), dtype=float)
    widths = np.asarray(
        prov.get("tranche_construction", {}).get("widths", ()), dtype=float
    )
    yblock = surface.get("years", {}).get(str(int(year)))
    if yblock is None or edges.size == 0 or widths.size == 0:
        return None  # year-scoped: an absent year gets NO surface (rule 13)
    n_bins = int(edges.size) + 1
    k = int(widths.size)

    bins = yblock.get("bins", {})
    pool_tr = yblock.get("_coverage", {}).get("within_year_pool_tranches", [])
    pool_prices = [float(t["price"]) for t in pool_tr] if pool_tr else None

    # Per-bin tranche price vector (n_bins, K); a bin absent from the year's
    # block borrows the within-year pool (the derive's disclosed backfill).
    price_by_bin = np.full((n_bins, k), np.nan, dtype=float)
    for b in range(n_bins):
        entry = bins.get(f"bin{b}")
        if entry and entry.get("tranches"):
            price_by_bin[b] = [float(t["price"]) for t in entry["tranches"]]
        elif pool_prices is not None:
            price_by_bin[b] = pool_prices
    if not np.isfinite(price_by_bin).all():
        return None  # no admissible ladder for some bin -> arm inert this year

    net = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net, edges)
    hour_bin = np.searchsorted(thresholds, net, side="right")  # (hours,)
    hour_bin = np.clip(hour_bin, 0, n_bins - 1)
    price_KT = price_by_bin[hour_bin].T  # (K, hours)
    return arm_batt_idx.astype(int), widths.astype(float), price_KT


def reserve_caiso_storage_as_power(
    power_cap: np.ndarray,
    units: list["StorageUnit"],
    year: int,
    hours: int,
) -> np.ndarray:
    """Reserve CAISO's measured hourly battery upward-AS award from the power cap.

    The measured CAISO battery fleet holds 1.0-1.7 GW average (DA) of AS
    awards (Daily Energy Storage Report quarterly data, curated to the
    ``storage-as-awards`` clean datatype); the upward products (reg-up + spin
    + non-spin, peaking 1.2-1.5 GW midday-to-afternoon in 2024/25) are power
    committed to reserve that cannot simultaneously arbitrage energy. This
    subtracts that measured hourly MW from the BATTERY units' dispatch power
    cap, allocated pro-rata by available battery power -- the exact ERCOT
    :func:`reserve_storage_as_power` pattern (``storage_as_commitment``),
    scoped to batteries because pumped storage is not an LESR.

    Rule-13 admissibility: the AS requirement regenerates for a forward year
    from forward drivers (load/VRE growth) and the storage share responds to
    fleet growth and AS saturation -- forward runs price the energy-vs-AS split
    endogenously (the ``ercot_storage_as_endogenous`` pattern); the measured
    award enters the backcast only as a capability input the LP dispatches
    beneath, never a pinned outcome. Zero fitted parameters (rule 23).

    Returns the ``(n_storage, hours)`` cap; an empty fleet passes through.
    """
    from market_sim.data.storage_as_awards import upward_award_mw

    pc = np.asarray(power_cap, dtype=float)
    if pc.size == 0 or not units:
        return power_cap
    up = upward_award_mw("CAISO", year, hours)
    pc2 = np.repeat(pc[:, np.newaxis], hours, axis=1) if pc.ndim == 1 else pc.copy()
    mask = _battery_mask(units)
    batt = pc2[mask]
    total = batt.sum(axis=0)  # (hours,) battery power available
    with np.errstate(divide="ignore", invalid="ignore"):
        weight = np.where(total[np.newaxis, :] > 0.0, batt / total[np.newaxis, :], 0.0)
    pc2[mask] = np.clip(batt - weight * up[np.newaxis, :], 0.0, None)
    return pc2


def caiso_storage_as_soc_min(
    power_cap: np.ndarray,
    energy_cap: np.ndarray,
    units: list["StorageUnit"],
    year: int,
    hours: int,
) -> np.ndarray:
    """SOC sustain floor for CAISO's measured battery contingency-AS awards.

    CAISO AS certification requires spin/non-spin awards to be sustainable for
    30 minutes from available state of charge
    (:data:`market_sim.config.reserve_config.CAISO_AS_SUSTAIN_DURATION_H`,
    CAISO Tariff §8.4 / App. K, ASSOC initiative -- the reserve co-opt's own
    sustain constant, no new number), so an awarded battery must hold
    ``0.5 h × (spin + nonspin)`` MWh it cannot arbitrage away. Allocated across
    battery units by the same pro-rata power weights as the power reservation
    and clipped at each unit's energy cap; pumped-storage rows are 0.

    Returns the ``(n_storage, hours)`` SOC lower bound for
    ``dispatch.build_variable_bounds(storage_soc_min=...)``.
    """
    from market_sim.data.storage_as_awards import sustain_energy_mwh

    pc = np.asarray(power_cap, dtype=float)
    ec = np.asarray(energy_cap, dtype=float)
    pc2 = np.repeat(pc[:, np.newaxis], hours, axis=1) if pc.ndim == 1 else pc.copy()
    ec2 = np.repeat(ec[:, np.newaxis], hours, axis=1) if ec.ndim == 1 else ec.copy()
    soc_min = np.zeros_like(pc2)
    mask = _battery_mask(units)
    if not mask.any():
        return soc_min
    sustain = sustain_energy_mwh("CAISO", year, hours)
    batt = pc2[mask]
    total = batt.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        weight = np.where(total[np.newaxis, :] > 0.0, batt / total[np.newaxis, :], 0.0)
    soc_min[mask] = np.minimum(weight * sustain[np.newaxis, :], ec2[mask])
    return soc_min


def caiso_storage_shape_caps(
    power_cap: np.ndarray,
    units: list["StorageUnit"],
    year: int,
    hours: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Measured diurnal charge/discharge capability caps for CAISO batteries.

    The energy-only LP arbitrages the battery fleet at up to its full
    nameplate power in any hour; the measured CAISO fleet never operates
    fleet-wide near nameplate -- AS holdback, DA-bid conservatism and
    commissioning ramps hold its p95 hour-of-day rate to ~0.43-0.55 of fleet
    MW charging and ~0.48-0.66 discharging (EIA-930 CISO ``NG: OTH`` ÷
    EIA-860 monthly fleet; caiso-99 Mechanism B, FINDING-caiso98 §7B). This
    returns per-unit-hour Chg/Dis upper bounds: battery rows are
    ``env_p95[year, hod] × power_cap[s, t]`` (composing with the COD vintage
    ramp already inside ``power_cap``); pumped-storage rows pass the power
    cap through unchanged (not an LESR, absent from the OTH series).

    The envelope is the committed rule-23 derivation
    ``data/raw/reference/caiso-storage-shape-envelope.csv``
    (:mod:`scripts.derive_caiso_storage_shape`); a solve year beyond the
    derived span reuses the latest measured year's shape (the forward story:
    per-MW behavior shape × that year's fleet). A missing envelope file
    raises -- a gated mechanism must never silently no-op (the caiso-98
    dead-flag lesson).

    Returns ``(charge_cap, discharge_cap)`` of shape ``(n_storage, hours)``
    for ``dispatch.solve_dispatch(storage_charge_cap=...,
    storage_discharge_cap=...)``.
    """
    from market_sim.config.paths import RAW_DIR

    path = RAW_DIR / "reference" / "caiso-storage-shape-envelope.csv"
    if not path.exists():
        raise FileNotFoundError(
            "caiso_storage_shape_anchor is enabled but the derived envelope "
            f"{path} is missing -- run scripts/derive_caiso_storage_shape.py"
        )
    env = pd.read_csv(path)
    env_years = sorted(env["year"].unique())
    use_year = max((y for y in env_years if y <= year), default=env_years[0])
    ey = env[env["year"] == use_year].sort_values("hod")
    chg_frac = ey["chg_frac_p95"].to_numpy(dtype=float)  # (24,)
    dis_frac = ey["dis_frac_p95"].to_numpy(dtype=float)
    hod = np.arange(hours) % 24

    pc = np.asarray(power_cap, dtype=float)
    pc2 = np.repeat(pc[:, np.newaxis], hours, axis=1) if pc.ndim == 1 else pc.copy()
    chg_cap = pc2.copy()
    dis_cap = pc2.copy()
    mask = _battery_mask(units)
    if mask.any():
        chg_cap[mask] = pc2[mask] * chg_frac[hod][np.newaxis, :]
        dis_cap[mask] = pc2[mask] * dis_frac[hod][np.newaxis, :]
    return chg_cap, dis_cap


def caiso_ps_charge_caps(
    power_cap: np.ndarray,
    units: list["StorageUnit"],
    hours: int,
    existing_charge_cap: np.ndarray | None,
) -> np.ndarray | None:
    """Static cited pump-power charge caps for per-plant CAISO pumped storage.

    ``caiso_ps_plant_params`` (lane 5, GATESPEC-caiso195): a per-plant
    :class:`StorageUnit` built by :func:`load_eia860_pumped_storage` carries
    its cited pump-side rating in ``charge_power_cap_mw`` (e.g. Helms 930 MW
    pumping vs 1,212 MW generating — PG&E; Gianelli 375.8 MW vs 424 MW — DWR
    B132-22 motor ratings). This composes those STATIC bounds into the
    existing ``storage_charge_cap`` LP channel:

    * rows for units with a cited pump rating take
      ``min(power_cap[s, t], charge_power_cap_mw)`` — the LP bound layer
      clips at the power cap anyway (tighten-only), so a cited rating ABOVE
      the unit's EIA-860 nameplate (Hyatt/Thermalito/O'Neill motor ratings)
      is a disclosed no-op, never a loosening;
    * every other row passes through ``existing_charge_cap`` (the battery
      shape anchor's measured envelope) or the plain power cap when no other
      contributor is armed — the two mechanisms govern DISJOINT unit sets on
      one channel (rule 19: one phenomenon, one bound per unit).

    Returns the composed ``(n_storage, hours)`` array, or ``None`` when no
    unit carries a cited pump rating (nothing to compose — the caller keeps
    whatever ``existing_charge_cap`` it had, including ``None``).
    """
    pump = np.array(
        [
            float(u.charge_power_cap_mw)
            if getattr(u, "charge_power_cap_mw", None) is not None
            else np.nan
            for u in units
        ],
        dtype=float,
    )
    has_pump = ~np.isnan(pump)
    if not has_pump.any():
        return None
    pc = np.asarray(power_cap, dtype=float)
    pc2 = np.repeat(pc[:, np.newaxis], hours, axis=1) if pc.ndim == 1 else pc.copy()
    base = (
        np.asarray(existing_charge_cap, dtype=float).copy()
        if existing_charge_cap is not None
        else pc2.copy()
    )
    base[has_pump] = np.minimum(pc2[has_pump], pump[has_pump, np.newaxis])
    return base


def caiso_charge_allocation_params(
    units: list["StorageUnit"],
    year: int,
    hours: int,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Measured DA charge-allocation schedule parameters for CAISO batteries.

    The M1 belly allocation mechanism (``caiso_charge_allocation_schedule``,
    owner-granted caiso-103 ask executed caiso-104): the measured CAISO fleet's
    intra-day charge allocation is set in the DAM (IFM schedules 76-84 % of
    realized charge) on a fleet-size-invariant hod shape (cross-year r >= 0.994
    across a 3.5x fleet, FINDING-caiso103 §1A), while the single-market LP
    re-times the whole charge volume at the RT margin. This returns the
    committed rule-23 statistics the per-day allocation rows consume
    (:func:`market_sim.model.dispatch._build_storage_alloc_rows` via the
    backcast orchestrator):

    * ``batt_idx`` — indices of the battery storage units (pumped storage
      exempt: not an LESR, absent from the storage-report basis);
    * ``share`` — ``(hours,)`` hod-mapped ``alloc_share`` (the year's hod
      share of annual IFM charge, Σ over a day = 1);
    * ``da_frac`` — the year's DA-share of realized charge (the bounded free
      RT-margin slice is ``1 - da_frac``).

    Source: ``data/raw/reference/caiso-charge-allocation-profile.csv``
    (:mod:`scripts.data.derive_caiso_charge_allocation`, from the CAISO Daily
    Energy Storage Report IFM layer). A solve year beyond the derived span
    uses the LATEST measured year's row — the caiso-99 envelope precedent
    (latest-year carry; owner sub-ruling caiso-104) — so the mechanism
    regenerates forward as shape x that year's endogenous charge volume. A
    missing artifact raises — a gated mechanism must never silently no-op
    (the caiso-98 dead-flag lesson).

    Returns ``(batt_idx, share, da_frac)``; ``batt_idx`` may be empty (no
    batteries), which the caller treats as a no-op.
    """
    from market_sim.config.paths import RAW_DIR

    path = RAW_DIR / "reference" / "caiso-charge-allocation-profile.csv"
    if not path.exists():
        raise FileNotFoundError(
            "caiso_charge_allocation_schedule is enabled but the derived "
            f"allocation profile {path} is missing -- run "
            "scripts/data/derive_caiso_charge_allocation.py"
        )
    prof = pd.read_csv(path)
    prof_years = sorted(prof["year"].unique())
    use_year = max((y for y in prof_years if y <= year), default=prof_years[0])
    py = prof[prof["year"] == use_year].sort_values("hod")
    share24 = py["alloc_share"].to_numpy(dtype=float)  # (24,)
    da_frac = float(py["da_frac"].iloc[0])
    hod = np.arange(hours) % 24
    share = share24[hod]  # (hours,)
    batt_idx = np.flatnonzero(_battery_mask(units))
    return batt_idx, share, da_frac


def load_eia860_pumped_storage(
    iso: str, year: int, config: ScenarioConfig | None = None
) -> list[StorageUnit]:
    """Build the pumped-storage hydro fleet from the EIA-860 generator data.

    Pumped storage is reported on the EIA-860 *generator* schedule (prime
    mover ``PS``), not the battery energy-storage schedule, so the battery
    loader alone misses it entirely -- e.g. PJM's ~5 GW (Bath County, Muddy
    Run, Yards Creek, Seneca, Smith Mountain) and CAISO's ~2.1 GW (Helms,
    W. R. Gianelli, Edward C Hyatt, J S Eastwood, Thermalito, O'Neill), the
    fleets' largest peak-shaving resources. Each operating PS unit online by
    the end of ``year`` is aggregated per zone into one ``StorageUnit``.
    EIA-860 carries no energy capacity or RTE for PS, so the cited
    fleet-average duration (:data:`PUMPED_STORAGE_DURATION_HOURS`) and
    round-trip efficiency (:data:`PUMPED_STORAGE_RTE`) constants are applied.
    The discharge ``vom`` is the per-ISO dispatch adder
    (:func:`resolve_pumped_storage_dispatch_adder`).

    Each PS unit respects the same month-precise COD ON-ramp and planned-
    retirement OFF-ramp as the battery and renewable loaders, year-precise here
    because the lowercase generator parquet carries no operating/retirement
    month. When ``config.storage_vintage_ramp`` is on and a zone's PS capacity
    varies intra-year, its aggregate carries a Jan-Dec monthly profile; old PS
    fleets are flat and stay static.

    Returns one ``StorageUnit`` per zone with nonzero PS capacity; empty when
    the generator parquet is missing or the ISO has no pumped storage.
    """
    from market_sim.config.paths import active_eia860_dir
    from market_sim.data.fleet import EIA_860_PARQUET_NAME
    from market_sim.data.zone_assignment import build_zone_lookup

    path = active_eia860_dir() / EIA_860_PARQUET_NAME
    if not path.exists():
        return []
    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        return []
    if not zone_lookup:
        return []

    df = pd.read_parquet(path)
    df = df[
        (df["prime_mover"].astype(str).str.strip().str.upper() == "PS")
        & (df["status"].astype(str).str.strip().str.upper() == "OP")
    ]
    # Planned-retirement OFF-ramp, mirroring the battery/renewable COD ramp. The
    # lowercase generator parquet carries ``planned_retirement_year`` but no
    # month (and no operating month), so the PS ramp is year-precise: a missing
    # online month resolves to COD_FALLBACK_MONTH and a missing retirement month
    # to December via the shared mask.
    ret_year = _optional_numeric(df, "planned_retirement_year")
    per_zone_power: dict[str, np.ndarray] = {}
    for code, p_mw, oy, ry in zip(
        df["plant_id"],
        pd.to_numeric(df["nameplate_capacity_mw"], errors="coerce"),
        pd.to_numeric(df["operating_year"], errors="coerce"),
        ret_year,
    ):
        if p_mw != p_mw or p_mw <= 0.0:  # NaN or non-positive
            continue
        if oy == oy and oy > year:  # commissioned after the backcast year
            continue
        try:
            zone = zone_lookup.get(int(code))
        except (TypeError, ValueError):
            zone = None
        if zone is None:
            continue
        mask = _unit_monthly_mask(oy, None, ry, None, year)
        if not mask.any():  # retired before / built after the backcast year
            continue
        per_zone_power.setdefault(zone, np.zeros(12))
        per_zone_power[zone] += float(p_mw) * mask

    eta = PUMPED_STORAGE_RTE**0.5
    adder = resolve_pumped_storage_dispatch_adder(iso, config)
    ramp_on = bool(getattr(config, "storage_vintage_ramp", False))
    units: list[StorageUnit] = []

    # Per-plant cited-physical parameterization (caiso_ps_plant_params, lane 5
    # — GATESPEC-caiso195): armed, CAISO's PS plants leave the zone aggregate
    # and enter one StorageUnit each. power_cap stays the plant's own EIA-860
    # nameplate rows exactly as accumulated above (G-AGG: the split re-sums to
    # the aggregate bit-for-bit at every month of the mask); energy_cap takes
    # the plant's cited reservoir-derived bound and the cited pump rating
    # rides StorageUnit.charge_power_cap_mw into the storage_charge_cap LP
    # channel. An uncited component parameter (Eastwood) keeps the incumbent
    # constant, disclosed in the PRECHECK. Zones stay build_zone_lookup's own
    # geography. Plants NOT in the table (none today — the six ARE CAISO's PS
    # fleet) would stay in the aggregate, fail-safe.
    ps_params = (
        CAISO_PS_PLANT_PARAMS
        if (
            iso.upper() == "CAISO"
            and bool(getattr(config, "caiso_ps_plant_params", False))
        )
        else {}
    )
    if ps_params:
        per_plant_power: dict[int, np.ndarray] = {}
        plant_zone: dict[int, str] = {}
        for code, p_mw, oy, ry in zip(
            df["plant_id"],
            pd.to_numeric(df["nameplate_capacity_mw"], errors="coerce"),
            pd.to_numeric(df["operating_year"], errors="coerce"),
            ret_year,
        ):
            if p_mw != p_mw or p_mw <= 0.0:
                continue
            if oy == oy and oy > year:
                continue
            try:
                icode = int(code)
            except (TypeError, ValueError):
                continue
            if icode not in ps_params:
                continue
            zone = zone_lookup.get(icode)
            if zone is None:
                continue
            mask = _unit_monthly_mask(oy, None, ry, None, year)
            if not mask.any():
                continue
            per_plant_power.setdefault(icode, np.zeros(12))
            per_plant_power[icode] += float(p_mw) * mask
            plant_zone[icode] = zone
        zone_order = {z: i for i, z in enumerate(get_iso_config(iso).zone_names)}
        for icode in sorted(per_plant_power):
            monthly_p = per_plant_power[icode]
            if monthly_p[-1] <= 0.0:
                continue
            spec = ps_params[icode]
            cited_e = spec.get("energy_mwh")
            monthly_e = (
                monthly_p * (float(cited_e) / float(monthly_p[-1]))
                if cited_e is not None
                else monthly_p * PUMPED_STORAGE_DURATION_HOURS
            )
            zone = plant_zone[icode]
            ramped = ramp_on and not np.allclose(monthly_p, monthly_p[-1])
            pump = spec.get("pump_mw")
            units.append(
                StorageUnit(
                    unit_id=f"{zone}_ps_{icode}",
                    zone=zone,
                    tech_name="pumped_storage",
                    power_cap_mw=float(monthly_p[-1]),
                    energy_cap_mwh=float(monthly_e[-1]),
                    eta_charge=eta,
                    eta_discharge=eta,
                    zone_idx=zone_order[zone],
                    vom=adder,
                    monthly_power_mw=(
                        [float(x) for x in monthly_p] if ramped else None
                    ),
                    monthly_energy_mwh=(
                        [float(x) for x in monthly_e] if ramped else None
                    ),
                    charge_power_cap_mw=(float(pump) if pump is not None else None),
                )
            )
        # Remove the split plants' capacity from the zone aggregates so the
        # armed fleet re-sums to the EIA-860 total exactly (zero MW added).
        for icode, monthly_p in per_plant_power.items():
            zone = plant_zone[icode]
            per_zone_power[zone] = per_zone_power[zone] - monthly_p
    for z_idx, zone in enumerate(get_iso_config(iso).zone_names):
        monthly_p = per_zone_power.get(zone)
        if monthly_p is None or monthly_p[-1] <= 1e-9:
            continue
        monthly_e = monthly_p * PUMPED_STORAGE_DURATION_HOURS
        # Attach a monthly profile only when the ramp is on and the zone's PS
        # capacity actually varies intra-year (a COD step up or a retirement
        # step down); old PS fleets are flat and stay 1-D.
        ramped = ramp_on and not np.allclose(monthly_p, monthly_p[-1])
        units.append(
            StorageUnit(
                unit_id=f"{zone}_eia860_pumped_storage",
                zone=zone,
                tech_name="pumped_storage",
                power_cap_mw=float(monthly_p[-1]),
                energy_cap_mwh=float(monthly_e[-1]),
                eta_charge=eta,
                eta_discharge=eta,
                zone_idx=z_idx,
                vom=adder,
                monthly_power_mw=([float(x) for x in monthly_p] if ramped else None),
                monthly_energy_mwh=([float(x) for x in monthly_e] if ramped else None),
            )
        )
    return units


# Economic life (years) over which storage capital cost is annualized.
_STORAGE_ECONOMIC_LIFE_YR: int = 20


def _capital_recovery_factor(rate: float, lifetime_yr: float) -> float:
    """Return the capital recovery factor for a given rate and lifetime."""
    if rate <= 0.0:
        return 1.0 / lifetime_yr
    growth = (1.0 + rate) ** lifetime_yr
    return rate * growth / (growth - 1.0)


def _storage_rte(tech_name: str, config: ScenarioConfig) -> float:
    """Return a tech's round-trip efficiency, honoring ``config`` overrides."""
    if tech_name == "li_ion_4hr":
        return config.storage_rte_4hr
    if tech_name == "li_ion_8hr":
        return config.storage_rte_8hr
    return float(STORAGE_TECHS[tech_name]["rte"])


def _arbitrage_block_days(duration_hr: int) -> int:
    """Length (days) of the arbitrage cycle window for a given duration.

    Storage completes one charge/discharge cycle per window. Short-duration
    storage cycles daily; long-duration storage shifts energy across multiple
    days, so its window widens with duration. The window is sized so a full
    ``duration_hr`` charge and a full ``duration_hr`` discharge never overlap
    (``2 × duration_hr <= 24 × block_days``), which both prevents
    double-counting and lets a 100-hour asset realize the multi-day value a
    fixed 24-hour window structurally hides.
    """
    return max(1, math.ceil(duration_hr / 12.0))


def estimate_storage_revenue(
    prices: np.ndarray,
    duration_hr: int,
    rte: float,
    degradation_cost_per_mwh: float = 0.0,
) -> float:
    """Annual arbitrage revenue per MW from prior year's price profile.

    The year is split into windows of :func:`_arbitrage_block_days` days. For
    each window: sort its prices, charge during the cheapest ``duration_hr``
    hours, discharge during the most expensive ``duration_hr`` hours, for one
    cycle per window. Margin per MWh discharged =
    ``avg_discharge_price - avg_charge_price / rte - degradation_cost_per_mwh``.
    Positive margins are summed × duration across all windows.

    Sizing the window to duration is what lets long-duration storage capture
    multi-day arbitrage: a fixed 24-hour window collapses the spread to zero
    for any duration at or beyond a day (the cheap and expensive hour-sets
    overlap), so iron-air and other LDES would screen as worthless.

    prices: (n_zones, T) or (T,). If multi-zone, uses the zone with the
    highest spread in each window. Returns $/MW-yr.

    Fully vectorized -- no Python loop over windows.
    """
    price_arr = np.asarray(prices, dtype=float)
    if price_arr.ndim == 1:
        price_arr = price_arr[None, :]
    n_zones, total_hours = price_arr.shape
    d = int(duration_hr)
    if d <= 0:
        return 0.0

    block_hours = _arbitrage_block_days(d) * 24
    n_blocks = total_hours // block_hours
    if n_blocks == 0:
        return 0.0

    # Reshape to (n_zones, n_blocks, block_hours) and sort each window.
    block = price_arr[:, : n_blocks * block_hours].reshape(
        n_zones, n_blocks, block_hours
    )
    ordered = np.sort(block, axis=2)

    # Cheapest d hours (charge) and most expensive d hours (discharge).
    charge_avg = ordered[:, :, :d].mean(axis=2)  # (n_zones, n_blocks)
    discharge_avg = ordered[:, :, -d:].mean(axis=2)  # (n_zones, n_blocks)

    # For each window, pick the zone with the widest spread.
    spread = discharge_avg - charge_avg  # (n_zones, n_blocks)
    best_zone = np.argmax(spread, axis=0)  # (n_blocks,)
    blocks_idx = np.arange(n_blocks)

    margin = (
        discharge_avg[best_zone, blocks_idx]
        - charge_avg[best_zone, blocks_idx] / rte
        - degradation_cost_per_mwh
    )
    margin = np.maximum(margin, 0.0)
    return float(margin.sum() * d)


def _elcc_for_duration(duration_hr: float, iso: str | None = None) -> float:
    """Interpolate the storage capacity credit (ELCC) for a duration.

    Linear interpolation over the ISO's published storage class-rating table
    (:data:`STORAGE_ELCC_BY_DURATION_BY_ISO` -- e.g. PJM's 2025/26 CIFP-reform
    class ratings, R3) when the ISO publishes one, else the generic
    :data:`STORAGE_ELCC_BY_DURATION`; clamped at the table's endpoints.
    ``iso=None`` (or an ISO absent from the override registry) keeps the generic
    table byte-identically. One storage-accreditation mechanism per ISO
    (rule 19); the marginal-ELCC saturation derate applies on top of this in
    :func:`estimate_capacity_value` for every ISO.
    """
    table = STORAGE_ELCC_BY_DURATION_BY_ISO.get(iso or "", STORAGE_ELCC_BY_DURATION)
    durations = [d for d, _ in table]
    credits = [c for _, c in table]
    return float(np.interp(duration_hr, durations, credits))


def storage_accreditation_credit(
    duration_hr: float,
    iso: str | None,
    config: ScenarioConfig,
    tech_name: str | None = None,
) -> float:
    """Return the storage capacity credit for a unit, on the ISO's own basis.

    The ONE storage-accreditation resolver (rule 19 [R-ONE-MECH]) -- every
    consumer of a storage capacity credit calls this, so an ISO's basis can
    never be applied on one path and not another. Two rungs, in preference
    order, and the first REPLACES the second rather than multiplying it:

    1. **Published whole-class accreditation** --
       :data:`STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO`, for an ISO that
       accredits storage without publishing a duration -> credit table (CAISO
       accredits dispatchable resources at demonstrated capability). Consulted
       ONLY behind that ISO's own default-OFF gate, so an unarmed run never
       reaches the registry and is byte-identical to the pre-FFR-4E path.
       Duration-independent by construction: this is a whole-class ratio and
       applying it per-unit is what makes the class total come out at CAISO's
       published number.
    2. **By-duration ELCC** -- :func:`_elcc_for_duration`, the ISO's published
       class-rating table when it has one, else the generic NREL/E3 curve.

    ``tech_name`` carries the unit's technology so rung 1 is applied on the
    SAME class boundary its published row is drawn on. CAISO's whole-class ratio
    is Table 1.1's **Battery** row, and CAISO books pumped storage on the Hydro
    row instead (FFR-4D §2 proved this two independent ways), so a
    ``pumped_storage`` unit must NOT take the battery ratio -- it stays on rung
    2, where the by-duration table already credits its long duration correctly.
    ``tech_name=None`` (a caller with no unit in hand, e.g. the technology-level
    entry screen) is treated as battery, which is what every rung-1 ISO's
    registry row describes.

    The marginal-ELCC saturation derate in :func:`estimate_capacity_value` and
    the portfolio dilution in ``capacity_evolution`` apply on top of whichever
    rung returns, exactly as they did before -- with the caveat that no ISO on
    rung 1 currently carries a dilution entry (see that registry's comment).
    """
    if tech_name != "pumped_storage" and _whole_class_accreditation_armed(iso, config):
        return float(STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO[str(iso)])
    return _elcc_for_duration(duration_hr, iso)


def _whole_class_accreditation_armed(iso: str | None, config: ScenarioConfig) -> bool:
    """Return whether ``iso``'s published whole-class storage credit is armed.

    Per-ISO gate resolution (rule 25 [R-ISO-SCOPE]): each ISO's whole-class
    entry is admitted by its OWN ``ScenarioConfig`` field, so arming one ISO
    can never move another. An ISO absent from
    :data:`STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO`, or whose gate is off,
    returns False and keeps the by-duration path byte-identically.
    """
    if iso not in STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO:
        return False
    if iso == "CAISO":
        return bool(getattr(config, "caiso_storage_nqc_accreditation", False))
    return False


def _degradation_cost_per_mwh(tech_name: str, config: ScenarioConfig) -> float:
    """Per-MWh-discharged cycling-degradation cost for a storage tech.

    Returns ``0.0`` when ``config.storage_degradation`` is off. Otherwise a
    slice of the energy-capacity capex amortized over the tech's rated cycle
    life (see :data:`STORAGE_DEGRADATION_REPLACEMENT_FRACTION`). High-cycling
    short-duration storage pays this on every arbitraged MWh; long-life flow /
    CAES / iron-air pay far less, reflecting their cycle-life advantage.
    """
    if not config.storage_degradation:
        return 0.0
    tech = STORAGE_TECHS[tech_name]
    cycles = float(tech.get("cycles", 0.0))
    if cycles <= 0.0:
        return 0.0
    capex_per_mwh = float(tech["capex_per_kwh"]) * 1000.0
    return capex_per_mwh / cycles * STORAGE_DEGRADATION_REPLACEMENT_FRACTION


def estimate_capacity_value(
    tech_name: str,
    existing_mw: float,
    config: ScenarioConfig,
    iso: str,
    reserve_position: float | None = None,
    year: int | None = None,
    locality_prices_by_zone: dict[str, float] | None = None,
) -> float:
    """Resource-adequacy capacity value per MW-yr for the next unit built.

    Zero unless the ISO's :data:`MARKET_DESIGN` has a capacity market and
    ``config.storage_capacity_value`` is on. Otherwise:

        capacity_price × ELCC(duration) × (1 - penetration)^exponent

    where ``capacity_price`` is the shared per-firm-MW capacity price
    (:meth:`MarketDesign.capacity_price_per_firm_mw_yr` -- rule 19, the SAME
    seam the thermal retirement and new-entry screens price through, so storage
    entry rides the ISO's one demand curve with no screen-specific curve). It
    is the flat ``net_cone × 1000`` by default and -- when
    ``config.capacity_market_clearing`` is on, the ISO has a published curve,
    and ``reserve_position`` is supplied -- the CR-1 sloped-curve price
    ``VRR(reserve_position) × net_cone_curve × 1000``. Storage's own
    accreditation (ELCC × saturation derate) multiplies it afterwards, distinct
    from the thermal UCAP.

    The ELCC credit rises with duration; the saturation derate falls as
    existing storage approaches the deployment ceiling. Together they make
    short-duration capacity value collapse at high penetration while
    long-duration storage retains its firm-capacity credit -- the mechanism
    that tilts new entry toward longer durations as storage saturates.

    ``iso``/``year`` are threaded into the pricing seam (RC-1A completion of
    RC-1B items 1/2): the per-ISO clearing gate and the per-delivery-year
    vintage anchor are consulted ONLY inside the seam's curve branch, so every
    gate-off path stays byte-identical to the pre-RC-1B behavior.
    """
    if not config.storage_capacity_value:
        return 0.0
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    base_price = design.capacity_price_per_firm_mw_yr(
        config, reserve_position, iso=iso, year=year
    )
    # capx D59 (locality_capacity_curves): storage entry is distributed across
    # zones by load_share, so the marginal build's expected capacity price is
    # the load-share-weighted max(NYCA, locality) over zones (ICAP Manual
    # §5.15.2 per zone; the _deliverability_capacity_factor shape). None /
    # empty ⇒ byte-identical.
    if locality_prices_by_zone and design.capacity_market:
        _iso_cfg = get_iso_config(iso)
        _num = 0.0
        _den = 0.0
        for _z in _iso_cfg.zones:
            if _z.load_share <= 0.0:
                continue
            _den += _z.load_share
            _num += _z.load_share * max(
                base_price, float(locality_prices_by_zone.get(_z.name, 0.0))
            )
        if _den > 0.0:
            base_price = _num / _den
    if base_price <= 0.0:
        return 0.0

    duration_hr = float(STORAGE_TECHS[tech_name]["duration_hr"])
    elcc = storage_accreditation_credit(duration_hr, iso, config, tech_name)

    ceiling = STORAGE_DEPLOYMENT_CEILING_MW.get(iso, 0.0)
    penetration = 0.0 if ceiling <= 0.0 else min(1.0, existing_mw / ceiling)
    derate = (1.0 - penetration) ** STORAGE_ELCC_SATURATION_EXPONENT

    return base_price * elcc * derate


def compute_storage_annual_cost(
    tech_name: str,
    year: int,
    config: ScenarioConfig,
    cumulative_gw: float | None = None,
) -> float:
    """Annualized storage cost per MW-yr.

    cost = capex_per_kw * CRF + fom_per_kw_yr, converted to $/MW-yr.
    Capex is first discounted along a Wright's-Law learning curve when
    ``cumulative_gw`` is supplied, then the IRA ITC is applied along the
    graduated phaseout schedule for non-wind/solar clean tech. Uses a
    20-year economic life for CRF.
    """
    tech = STORAGE_TECHS[tech_name]
    capex_per_kw = float(tech["capex_per_kw"])

    # Wright's Law learning curve. Both li-ion durations share the "li_ion"
    # manufacturing learning curve; iron-air maps to its own reference.
    if cumulative_gw is not None:
        ref_key = "li_ion" if "li_ion" in tech_name else tech_name
        reference_gw = WRIGHT_REFERENCE_GW.get(ref_key)
        if reference_gw is not None and cumulative_gw > 0:
            lr = float(tech["learning_rate"])
            capex_per_kw = capex_per_kw * (cumulative_gw / reference_gw) ** (-lr)

    frac = ira_phaseout_fraction(year, config)
    if frac > 0.0:
        capex_per_kw *= 1.0 - config.ira_itc_storage * frac
    crf = _capital_recovery_factor(config.real_discount_rate, _STORAGE_ECONOMIC_LIFE_YR)
    annual_cost_per_kw = capex_per_kw * crf + float(tech["fom_per_kw_yr"])
    return annual_cost_per_kw * 1000.0


def _build_new_storage_units(
    iso: ISOConfig,
    tech_name: str,
    config: ScenarioConfig,
    total_mw: float,
    year: int,
    seq: int,
) -> list[StorageUnit]:
    """Distribute a single tech's new build across an ISO's load zones.

    Power is split by ``load_share``; zero-load zones get nothing.
    """
    tech = STORAGE_TECHS[tech_name]
    duration_hr = float(tech["duration_hr"])
    eta = _storage_rte(tech_name, config) ** 0.5
    units: list[StorageUnit] = []
    for z_idx, zone in enumerate(iso.zones):
        if zone.load_share <= 0.0:
            continue
        power_mw = total_mw * zone.load_share
        if power_mw <= 0.0:
            continue
        units.append(
            StorageUnit(
                unit_id=f"{zone.name}_{tech_name}_new_{year}_{seq}",
                zone=zone.name,
                tech_name=tech_name,
                power_cap_mw=power_mw,
                energy_cap_mwh=power_mw * duration_hr,
                eta_charge=eta,
                eta_discharge=eta,
                zone_idx=z_idx,
            )
        )
    return units


def _deliverability_capacity_factor(
    iso_config: ISOConfig,
    deliverability_headroom: dict[str, float] | None,
) -> float:
    """Return the load-share-weighted short-zone fraction for storage RA value.

    Storage new entry distributes across load zones by ``load_share``, so the
    marginal build's expected capacity value should reflect only the share of it
    landing in zones still *short* on deliverable firm capacity (headroom < 0).
    Returns ``1.0`` (no-op) when ``deliverability_headroom`` is empty (flag off /
    no data) or names no zone; otherwise the sum of ``load_share`` over the
    short, requirement-carrying zones divided by the total load_share of all
    zones that carry a requirement. Zones with no requirement are treated as
    fully creditable (unconstrained), so an ISO with data for only some zones is
    not penalised on its unmodelled zones.
    """
    if not deliverability_headroom:
        return 1.0
    priced = 0.0
    total = 0.0
    for zone in iso_config.zones:
        if zone.load_share <= 0.0:
            continue
        headroom = deliverability_headroom.get(zone.name)
        total += zone.load_share
        # No requirement for this zone → unconstrained, fully creditable.
        if headroom is None or headroom < 0.0:
            priced += zone.load_share
    if total <= 0.0:
        return 1.0
    return priced / total


def _storage_entry_candidates(
    year: int, config: ScenarioConfig
) -> list[tuple[str, dict]]:
    """Return the ``STORAGE_TECHS`` items admissible for new entry in ``year``.

    THE ONE eligibility gate both storage allocation rules consume (rule 19
    [R-ONE-MECH]): the bang-bang split and the D11-R margin-exhaustion walk
    each iterate exactly this list, so a technology is either admissible on
    both paths or on neither.

    Gated by ``config.storage_entry_availability_gate`` (GATED default OFF —
    the D-2 repair, docs/FINDING-entry-screen-t1h-2026-08.md §6 /
    docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md Phase-1 Leg A). Off, the
    full ``STORAGE_TECHS`` pool is returned in registry order — byte-identical
    to the ungated legacy behaviour. On, a technology is admissible only from
    its measured first-US-operating year (``STORAGE_TECH_AVAILABLE_YEAR``,
    derived from the EIA-860 energy-storage schedule — see the constant's
    derivation note), the storage analogue of the thermal path's
    ``_EMERGING_AVAILABLE_YEAR`` gate. FAIL-CLOSED: a technology whose mapping
    entry is ``None`` (zero national operating base ever) or that is missing
    from the mapping entirely is never admissible.
    """
    if not getattr(config, "storage_entry_availability_gate", False):
        return list(STORAGE_TECHS.items())
    admitted: list[tuple[str, dict]] = []
    for tech_name, tech in STORAGE_TECHS.items():
        available_year = STORAGE_TECH_AVAILABLE_YEAR.get(tech_name)
        if available_year is None or year < available_year:
            continue
        admitted.append((tech_name, tech))
    return admitted


def _storage_entry_rank_score(
    tech_name: str, margin: float, config: ScenarioConfig
) -> float:
    """Return the ranking score for one storage entry candidate's margin.

    THE ONE ranking object both storage allocation rules consume (rule 19
    [R-ONE-MECH]). Gated by ``config.storage_entry_cost_normalized_rank``
    (GATED default OFF — the D-3 repair): off, the score IS the absolute
    ``$/MW-yr`` margin, byte-identical to the shipped ranking. On, the score
    is margin per unit capital cost — ``margin /
    STORAGE_TECHS[tech]["capex_per_kw"]`` — the developer's actual ranking
    object (return per dollar deployed), which removes the shipped metric's
    structural bias toward the most capital-intensive machine (a bigger
    machine earns a bigger absolute margin; Phase-0 measured flow_battery 2nd
    of 6 absolute and LAST per $/kW,
    docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md §3.2). Rule 21
    [R-DOF]: a ratio of two quantities the screen already holds — no new
    parameter; the Phase-0 §3.2 sensitivity shows the build mix is invariant
    to the cost denominator (capital vs annualized). Sign-preserving
    (``capex_per_kw`` > 0), so a technology clears (score > 0) iff its margin
    clears — the flag changes the ORDER among clearing technologies, never
    which technologies clear.
    """
    if not getattr(config, "storage_entry_cost_normalized_rank", False):
        return margin
    return margin / float(STORAGE_TECHS[tech_name]["capex_per_kw"])


def apply_storage_new_entry(
    existing_storage: list[StorageUnit],
    prices: np.ndarray,
    year: int,
    config: ScenarioConfig,
    iso: str,
    cumulative: CumulativeDeployment | None = None,
    deliverability_headroom: dict[str, float] | None = None,
    endogenous_as_revenue_per_mw_yr: float | None = None,
    reserve_position: float | None = None,
    locality_prices_by_zone: dict[str, float] | None = None,
    entry_reprice=None,
) -> list[StorageUnit]:
    """Add storage whose stacked value beats its annualized cost.

    ``entry_reprice`` (D11-R, GATED ``entry_margin_exhaustion``;
    ``runner._EntryRepriceWalk``) replaces the winner-take-share split below
    with the margin-exhaustion walk: tranches to the best-margin tech, the
    signal repriced through the walk's shave/AS-share terms after every
    tranche, the same caps binding — sharing ONE walk state with the thermal
    screen that ran before this call. ``None`` (default) keeps the split
    byte-identically.

    Each tech in STORAGE_TECHS is screened on a value stack:
    - **Energy arbitrage** over duration-sized windows (so long-duration
      storage captures multi-day value), net of cycling degradation.
    - **Capacity value** -- resource-adequacy revenue, paid only in ISOs whose
      MARKET_DESIGN has a capacity market and when
      ``config.storage_capacity_value`` is on. Its duration-rising ELCC credit
      and penetration-falling saturation derate tilt entry toward longer
      durations as storage saturates the peak. The per-firm-MW capacity price
      it scales is the shared seam (rule 19): fixed net-CONE by default, or the
      CR-1 sloped-curve price when ``config.capacity_market_clearing`` is on and
      the runner supplies ``reserve_position`` (accredited firm ÷ requirement).

    Profitable techs are ranked by margin and built in merit order, but no
    single tech may take more than ``STORAGE_TECH_BUILD_SHARE_CAP`` of one
    year's budget, so the build diversifies across durations rather than the
    top-margin tech monopolizing it.

    Two GATED default-OFF repairs, each shared by BOTH allocation rules
    through one helper (rule 19; charter
    ``docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md`` Phase-1 Leg A):
    ``config.storage_entry_availability_gate`` (D-2) restricts the candidate
    pool to technologies at/after their measured first-US-operating year
    (:func:`_storage_entry_candidates` over ``STORAGE_TECH_AVAILABLE_YEAR``,
    fail-closed), and ``config.storage_entry_cost_normalized_rank`` (D-3)
    ranks clearing candidates on margin per unit capital cost instead of
    absolute $/MW-yr (:func:`_storage_entry_rank_score`). Two caps bind independently:
    - STORAGE_ANNUAL_BUILD_CAP_MW per ISO per year
    - STORAGE_DEPLOYMENT_CEILING_MW cumulative per ISO

    New units distributed across load zones by load_share. Uses
    config.storage_rte_4hr / storage_rte_8hr overrides when applicable.
    When ``cumulative`` is supplied, each tech's capex follows a
    Wright's-Law learning curve. Returns the full storage fleet
    (existing + new).

    Locational deliverability gate (``config.capacity_deliverability_limits``):
    when ``deliverability_headroom`` (``{zone: deliverable_firm - requirement}``)
    is supplied, each tech's capacity value is scaled by the load-share-weighted
    fraction of zones that are still *short* (headroom < 0). Storage builds
    distribute by load_share, so this credits capacity value only for the share
    of the build landing where the RA requirement is not yet met -- the same
    locational logic as the thermal screens. A no-op (factor 1.0) when the flag
    is off or no zone is long.

    Storage AS credit (one mechanism per phenomenon, CLAUDE.md rule 19).
    ~85% of 2023 ERCOT battery revenue was ancillary services, absent from the
    energy-arbitrage + capacity stack above. Exactly one mechanism supplies it:

    * ``config.ercot_storage_as_endogenous`` **on** → the AS duty is priced
      inside the dispatch reserve co-optimization (storage headroom backs
      upward reserve and the AS-widened spreads flow into the arbitrage term).
      The AS credit is then the value **derived from that solved co-opt's own
      reserve duals**, passed as ``endogenous_as_revenue_per_mw_yr``
      (``ancillary.realized_storage_as_revenue_per_mw_yr``); the exogenous
      saturation rate is **not** added -- that would double-count.
    * endogenous **off** → the legacy/backcast-validation path: the calibrated
      exogenous ``ancillary.as_revenue_per_mw_yr("storage", …)`` is the sole AS
      credit.
    """
    iso = iso.upper()
    iso_config = get_iso_config(iso)
    fleet = list(existing_storage)

    # Fail loudly when a registered ISO lacks storage-entry registry data: a
    # silent default of zero would suppress ALL storage entry and quietly break
    # that ISO's forecast (the trap MISO fell into). Mirrors the thermal
    # screen's QUEUE_CAP_GW guard (capacity.apply_economic_new_entry) so any new
    # ISO must be registered in both dicts before its forecast can build storage.
    if iso not in STORAGE_DEPLOYMENT_CEILING_MW:
        raise KeyError(
            f"STORAGE_DEPLOYMENT_CEILING_MW has no entry for {iso!r}; storage "
            "new entry cannot run. Add the ISO's deployment ceiling (~50% of "
            "coincident peak) to config/constants.py."
        )
    if iso not in STORAGE_ANNUAL_BUILD_CAP_MW:
        raise KeyError(
            f"STORAGE_ANNUAL_BUILD_CAP_MW has no entry for {iso!r}; storage "
            "new entry cannot run. Add the ISO's annual build cap "
            "(interconnection-queue throughput) to config/constants.py."
        )

    existing_mw = sum(u.power_cap_mw for u in existing_storage)
    ceiling = STORAGE_DEPLOYMENT_CEILING_MW[iso]
    annual_cap = STORAGE_ANNUAL_BUILD_CAP_MW[iso]
    budget = min(annual_cap, max(0.0, ceiling - existing_mw))
    if budget <= 0.0:
        return fleet

    # Load-share-weighted fraction of the build landing in short (RA-deficient)
    # zones. 1.0 when the gate is off, no data, or every requirement-carrying
    # zone is short; < 1.0 when some load-weighted share sits in long zones.
    deliverability_factor = _deliverability_capacity_factor(
        iso_config, deliverability_headroom
    )

    def _stack_margin(tech_name: str, tech: dict, price_arr, fleet_mw: float) -> float:
        """One tech's full value-stack margin at the given prices/fleet state.

        The single margin construction both allocation rules evaluate: the
        bang-bang path calls it once per tech at the screened prices and the
        start-of-year fleet; the margin-exhaustion walk re-calls it per
        tranche at the repriced walk signal and the walk-grown fleet MW (the
        AS-saturation and ELCC-saturation curves are the model's own
        responses to added storage, so the walk evaluates them at its own
        state — rule 21 [R-DOF]: existing response curves, no new
        coefficient).
        """
        revenue = estimate_storage_revenue(
            price_arr,
            int(tech["duration_hr"]),
            _storage_rte(tech_name, config),
            degradation_cost_per_mwh=_degradation_cost_per_mwh(tech_name, config),
        )
        capacity_value = (
            estimate_capacity_value(
                tech_name,
                fleet_mw,
                config,
                iso,
                reserve_position,
                year=year,
                locality_prices_by_zone=locality_prices_by_zone,
            )
            * deliverability_factor
        )
        # ERCOT ancillary-service revenue (Reg/RRS/ECRS/Non-Spin) -- ~85% of
        # 2023 battery revenue and absent from the energy-arbitrage + capacity
        # value stack above. Under the endogenous co-opt the AS duty is already
        # priced in dispatch, so the credit is DERIVED from that solve's reserve
        # duals (mutually exclusive with the exogenous rate, rule 19); otherwise
        # it is the exogenous rate, saturating on the storage fleet so each
        # marginal build sees the AS rate at the current penetration.
        if getattr(config, "ercot_storage_as_endogenous", False):
            as_revenue = float(endogenous_as_revenue_per_mw_yr or 0.0)
        else:
            as_revenue = as_revenue_per_mw_yr("storage", fleet_mw, config)
        ref_key = "li_ion" if "li_ion" in tech_name else tech_name
        cum_gw = cumulative.get(ref_key) if cumulative else None
        cost = compute_storage_annual_cost(
            tech_name, year, config, cumulative_gw=cum_gw
        )
        return revenue + capacity_value + as_revenue - cost

    if entry_reprice is not None:
        # ------------------------------------------------------------------
        # D11-R margin-exhaustion walk (GATED entry_margin_exhaustion): the
        # storage half of the L-1b closure, sharing ONE walk state with the
        # thermal screen that ran before this call (rule 19 [R-ONE-MECH]) —
        # its thermal tranches are already in the repriced signal this walk
        # starts from. Tranches go to the best-margin tech under the SAME
        # caps (annual budget, per-tech share cap, deployment ceiling via
        # ``budget``); each tranche's shave + AS-share terms re-price the
        # signal and grow the saturation state before the next margin is
        # read. Stops when no tech's repriced margin clears zero or the
        # budget binds. The final tranche may be partial so a cap binds
        # exactly where the bang-bang split's would.
        # ------------------------------------------------------------------
        _prices0 = np.asarray(prices, dtype=float)
        sig_walk = entry_reprice.signal(_prices0)
        per_tech_cap = budget * STORAGE_TECH_BUILD_SHARE_CAP
        remaining = budget
        built: dict[str, float] = {}
        order_first: list[str] = []
        fleet_walk_mw = existing_mw
        # Shared eligibility gate (D-2, rule 19): the walk iterates the SAME
        # admitted pool as the bang-bang split below. Ungated = the full
        # STORAGE_TECHS pool, byte-identical.
        candidates = _storage_entry_candidates(year, config)
        _max_steps = (
            int(budget // ENTRY_EXHAUSTION_TRANCHE_MW) + 2 * len(STORAGE_TECHS) + 4
        )
        for _ in range(_max_steps):
            if remaining <= 0.0:
                break
            best_tech: str | None = None
            best_score = 0.0
            for tech_name, tech in candidates:
                room = min(per_tech_cap - built.get(tech_name, 0.0), remaining)
                # 1e-6 MW: numerical guard against float-residue room.
                if room <= 1e-6:
                    continue
                m = _stack_margin(tech_name, tech, sig_walk, fleet_walk_mw)
                # Shared ranking object (D-3, rule 19): identical to the
                # bang-bang sort key below. Sign-preserving, so the
                # exhaustion condition (clear zero) is unchanged; ungated
                # the score IS the margin, byte-identical.
                score = _storage_entry_rank_score(tech_name, m, config)
                if score > best_score:
                    best_score, best_tech = score, tech_name
            if best_tech is None:
                break
            tech = STORAGE_TECHS[best_tech]
            room = min(per_tech_cap - built.get(best_tech, 0.0), remaining)
            tranche = min(ENTRY_EXHAUSTION_TRANCHE_MW, room)
            built[best_tech] = built.get(best_tech, 0.0) + tranche
            remaining -= tranche
            fleet_walk_mw += tranche
            if best_tech not in order_first:
                order_first.append(best_tech)
            entry_reprice.add_storage(
                tranche, float(tech["duration_hr"]), _storage_rte(best_tech, config)
            )
            sig_walk = entry_reprice.signal(_prices0)
        for seq, tech_name in enumerate(order_first):
            fleet.extend(
                _build_new_storage_units(
                    iso_config, tech_name, config, built[tech_name], year, seq
                )
            )
        return fleet

    # Shared eligibility gate (D-2) + shared ranking object (D-3) — the same
    # two seams the D11-R walk above consumes (rule 19 [R-ONE-MECH]). Both
    # GATED default OFF: ungated, the pool is the full STORAGE_TECHS registry
    # and the sort key is the absolute margin — byte-identical to the shipped
    # winner-take-share split.
    margins: list[tuple[float, str]] = []
    for tech_name, tech in _storage_entry_candidates(year, config):
        margin = _stack_margin(tech_name, tech, prices, existing_mw)
        if margin > 0.0:
            margins.append(
                (_storage_entry_rank_score(tech_name, margin, config), tech_name)
            )

    margins.sort(key=lambda m: m[0], reverse=True)

    # No single tech may take more than the share cap of the year's budget, so
    # a diverse build spreads across the profitable durations.
    per_tech_cap = budget * STORAGE_TECH_BUILD_SHARE_CAP
    remaining = budget
    for seq, (_, tech_name) in enumerate(margins):
        if remaining <= 0.0:
            break
        build_mw = min(remaining, per_tech_cap)
        remaining -= build_mw
        fleet.extend(
            _build_new_storage_units(iso_config, tech_name, config, build_mw, year, seq)
        )
    return fleet
