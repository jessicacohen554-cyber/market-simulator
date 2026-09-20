"""CAMPD per-plant binning: registries, ramp groups, emission rates, tranche tables.

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd

from functools import lru_cache
from market_sim.config.paths import (
    PROCESSED_DIR,
    active_eia860_dir,
)
from market_sim.config.plant_taxonomy import COAL_SUPPLY_TO_CLASS
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.campd import (
    DEFAULT_PARASITIC_LOAD_PCT,
    _DEFAULT_PARASITIC_LOAD_PCT,
)
from pathlib import Path
from market_sim.data.fleet.models import (
    FleetArrays,
    Generator,
    ba_codes,
)
from market_sim.data.fleet.eia860 import (
    BIN_GROUP_HR_DEFAULT,
    BIN_GROUP_TO_FUEL,
    _GAS_BIN_GROUPS,
    eia923_dominant_class_by_plant,
)
from market_sim.data.fleet.models import _pkg_ns

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")


@lru_cache(maxsize=4)
def _load_plant_registry_cached(csv_path: str) -> pd.DataFrame:
    """Cached read of one master-plant-registry CSV path.

    Keyed on the path string so the (identical) registry is parsed once per
    fleet build instead of once per :func:`bins_to_fleet` call. Callers receive
    a defensive ``.copy()`` via :func:`load_plant_registry`, so this shared
    frame is never handed out directly.
    """
    return pd.read_csv(csv_path)


def load_plant_registry(csv_path: str | Path) -> pd.DataFrame:
    """Load the master plant registry CSV.

    The registry has one row per ERCOT thermal plant with EIA-860 / CAMPD
    attributes. It is not consumed by dispatch directly — the dispatch fleet
    comes from :func:`load_campd_bins` — but it is the reference for plant
    metadata and the "OTHER" (non-dispatchable) plant set.

    Args:
        csv_path: Path to ``master-plant-registry.csv``.

    Returns:
        The registry as a DataFrame (a fresh copy of the cached read, so the
        caller may mutate it freely).
    """
    return _load_plant_registry_cached(str(csv_path)).copy()


# EIA-860 "Technology" string that marks an oil/distillate-fired unit. The
# energy-source codes that back it (distillate / residual fuel oil) — used to
# keep the match robust if the technology label is blank but the fuel code is
# present.
_OIL_PRIMARY_TECHNOLOGY: str = "petroleum liquids"
_OIL_PRIMARY_FUEL_CODES: frozenset[str] = frozenset({"DFO", "RFO"})


@lru_cache(maxsize=4)
def _oil_primary_bin_plants(registry_path: str) -> frozenset[int]:
    """Cached oil-primary plant-code set from one registry CSV path."""
    reg = pd.read_csv(
        registry_path, usecols=lambda c: c in ("plantid", "fuel_type", "technology")
    )
    tech = reg["technology"].astype(str).str.strip().str.lower()
    fuel = reg["fuel_type"].astype(str).str.strip().str.upper()
    is_oil = tech.eq(_OIL_PRIMARY_TECHNOLOGY) | fuel.isin(_OIL_PRIMARY_FUEL_CODES)
    return frozenset(int(p) for p in reg.loc[is_oil, "plantid"])


def oil_primary_bin_plants(registry_path: str | Path) -> frozenset[int]:
    """Return EIA plant codes whose EIA-860 primary fuel is oil/distillate.

    A plant is oil-primary when its master-registry row (EIA-860 derived)
    is technology ``Petroleum Liquids`` or its primary energy source
    (``fuel_type``) is a distillate / residual fuel-oil code
    (:data:`_OIL_PRIMARY_FUEL_CODES`). These are the combustion-turbine /
    reciprocating peakers the CAMPD bin sheet routes through the gas
    ``CT_PEAKER`` class even though they physically burn distillate — e.g.
    Morgan Creek (3492). :func:`bins_to_fleet` reprices the gas-CT tranches
    of these plants on oil when ``config.oil_primary_bin_fuel`` is set, the
    structural counterpart of the oil-primary exclusion in
    :func:`dual_fuel_plant_groups`.

    The signal is a measured EIA-860 attribute that regenerates for any
    forward year, so the correction is forward-defensible rather than a
    fitted per-unit adder.
    """
    return _oil_primary_bin_plants(str(registry_path))


# Generator-level EIA-860 energy-source codes that mark an oil/kerosene-primary
# unit (Energy Source 1). Adds kerosene / jet fuel to the plant-registry DFO/RFO
# codes — the LI/NYC legacy frames are KER-listed at the generator level.
_OIL_PRIMARY_UNIT_FUEL_CODES: frozenset[str] = frozenset({"DFO", "RFO", "KER", "JF"})

# Simple-cycle prime movers for the generator-level oil-primary screen (GT/IC;
# EIA "CT" is a combined-cycle turbine part, never a simple-cycle peaker).
_OIL_PRIMARY_PRIME_MOVERS: frozenset[str] = frozenset({"GT", "IC"})


@lru_cache(maxsize=8)
def oil_primary_ct_plants_from_eia860(iso: str) -> frozenset[int]:
    """Return plant codes whose *generator-level* EIA-860 CT fleet is oil-primary.

    The generator-level companion to :func:`oil_primary_bin_plants`, which keys
    on the (ERCOT-only) master plant registry's PLANT primary fuel and so
    catches zero plants for the per-plant non-ERCOT ISOs. This reads the raw
    EIA-860 operable generator sheet directly: a plant is oil-primary when the
    majority (by nameplate capacity) of its operating simple-cycle units
    (GT/IC) carry an oil / kerosene Energy Source 1
    (:data:`_OIL_PRIMARY_UNIT_FUEL_CODES`), restricted to the ISO's balancing
    authority. Same measured-attribute admissibility as the registry screen
    (rule #12): the EIA-860 field regenerates for any forward vintage.

    Verification note (NYISO, 2026-07-04 session): the per-plant non-ERCOT
    fleet path already maps each unit's own EIA-860 energy source
    (:func:`_map_fuel_type`), so KER/DFO-primary units (Holtsville, Wading
    River, Glenwood 2514, Shoreham 2518, ...) load as raw ``oil`` units and
    never enter a gas CT bin — every NYISO gas-CT bin was confirmed
    NG-primary at the generator level. This screen therefore catches plants
    only where a minority NG unit creates a gas bin at a majority-oil plant,
    and its NYISO yield is empty; it is kept because it grounds the flag's
    semantics in the generator-level record for every ISO.
    """
    path = _pkg_ns().EIA_860_DIR / "eia860_generator_operable.parquet"
    if not path.exists():
        return frozenset()
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Prime Mover",
            "Energy Source 1",
            "Nameplate Capacity (MW)",
            "Status",
        ],
    )
    ba_map = pd.read_parquet(
        _pkg_ns().EIA_860_DIR / "eia860_generators.parquet",
        columns=["plant_id", "balancing_authority_code"],
    ).drop_duplicates("plant_id")
    codes = ba_codes(iso)
    if codes:
        # Membership over every BA the region comprises: the scalar-inverse
        # form returned an EMPTY screen for a pool region, indistinguishable
        # from "no oil-primary plants" (NWPP-10 §3).
        keep = set(
            ba_map.loc[
                ba_map["balancing_authority_code"].astype(str).str.strip().isin(codes),
                "plant_id",
            ].astype(int)
        )
        df = df[df["Plant Code"].astype("Int64").isin(keep)]
    df = df[
        (df["Status"].astype(str).str.strip().str.upper() == "OP")
        & df["Prime Mover"].astype(str).str.strip().isin(_OIL_PRIMARY_PRIME_MOVERS)
    ]
    if df.empty:
        return frozenset()
    df = df.assign(
        _oil=df["Energy Source 1"]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(_OIL_PRIMARY_UNIT_FUEL_CODES),
        _mw=pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0),
    )
    by_plant = df.groupby(df["Plant Code"].astype(int)).apply(
        lambda g: float(g.loc[g["_oil"], "_mw"].sum()) > 0.5 * float(g["_mw"].sum()),
        include_groups=False,
    )
    return frozenset(int(p) for p, is_oil in by_plant.items() if is_oil)


@lru_cache(maxsize=8)
def campd_ct_run_band_ratios(
    iso: str,
) -> "tuple[tuple[float, ...], tuple[float, ...]] | None":
    """Return the measured (band_edges, run-length ratios) for an ISO, or None.

    Reads the committed condition-banded CT run-length artifact
    (``scripts/data/derive_campd_ct_run_lengths.py --condition-bands`` →
    ``data/raw/_processed-legacy/campd_ct_run_bands_<ISO>.csv``): per
    net-load-percentile band, the class-pooled median start-to-stop run
    length as a RATIO to the all-runs pooled median — the v4
    condition-keyed amortization's shape factor
    (``ScenarioConfig.tranche_startup_conditional_runs``). ``edges`` are the
    interior percentile boundaries (``pct_hi`` of every band but the last),
    for ``np.searchsorted`` banding of model hours. ``None`` when the ISO
    has no artifact (the v4 flag is then a documented no-op — never a
    silent hand number, rule #23; per-ISO artifact, rule #25).
    """
    path = PROCESSED_DIR / f"campd_ct_run_bands_{iso.upper()}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path).sort_values("band")
    edges = tuple(float(x) for x in df["pct_hi"].to_numpy()[:-1])
    ratios = tuple(float(x) for x in df["ratio"].to_numpy())
    return edges, ratios


@lru_cache(maxsize=8)
def campd_ct_run_lengths(iso: str) -> dict[int, float]:
    """Return ``{plant_code: median CT run hours}`` for an ISO, ``0`` = fallback.

    Reads the committed CAMPD-measured simple-cycle CT run-length artifact
    (``scripts/data/derive_campd_ct_run_lengths.py`` →
    ``data/raw/_processed-legacy/campd_ct_run_lengths_<ISO>.csv``): per-plant
    median start-to-stop run lengths pooled 2023-2025, with the ISO-class
    pooled median under key ``0`` for CT plants without CEMS coverage. Empty
    dict when the ISO has no artifact (the v3 amortization then leaves every
    tranche on the v2 P0 basis — never a silent hand number, rule #23).
    """
    path = PROCESSED_DIR / f"campd_ct_run_lengths_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, usecols=["plant_code", "median_run_hours"])
    return {
        int(r.plant_code): float(r.median_run_hours)
        for r in df.itertuples(index=False)
        if float(r.median_run_hours) > 0.0
    }


@lru_cache(maxsize=8)
def measured_ct_heat_rates(iso: str) -> dict[int, float]:
    """Return ``{plant_code: measured loaded heat rate}`` for an ISO's CT_PEAKERs.

    Reads the committed CAMPD-measured artifact
    (``scripts/data/derive_campd_ct_heat_rates.py`` →
    ``data/raw/_processed-legacy/campd_ct_heat_rates_<ISO>.csv``): per-plant
    MMBtu per **net** MWh at load, pooled 2023-2025 over CAMPD ``unitType ==
    'Combustion turbine'`` units. It replaces the eGRID plant-average ANNUAL
    heat rate the fleet loader otherwise gives a peaker, which is neither a
    loaded rate nor — at a mixed steam/CT facility — the right technology's
    rate (CLAUDE.md rule 14 [R-ACCURATE]).

    Only ``flag == "ok"`` rows are returned: the derive marks any plant outside
    the physical simple-cycle band as a meter defect rather than applying it.
    Empty dict when the ISO has no artifact, which leaves every plant on its
    eGRID rate — never a silent hand number (rule 24 [R-FROZEN-DERIVE]).
    """
    path = PROCESSED_DIR / f"campd_ct_heat_rates_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, usecols=["plant_code", "heat_rate", "flag"])
    return {
        int(r.plant_code): float(r.heat_rate)
        for r in df.itertuples(index=False)
        if str(r.flag) == "ok" and float(r.heat_rate) > 0.0
    }


@lru_cache(maxsize=8)
def measured_coal_heat_rates(iso: str) -> dict[int, float]:
    """Return ``{plant_code: measured operating heat rate}`` for an ISO's COAL.

    Reads the committed CAMPD-measured artifact
    (``scripts/data/derive_campd_coal_heat_rates.py`` →
    ``data/raw/_processed-legacy/campd_coal_heat_rates_<ISO>.csv``): per-plant
    MMBtu per **net** MWh over the plant's own steady-state operating hours,
    pooled 2023-2025 over the CAMPD units whose ``primaryFuelInfo`` is a coal.
    It replaces the eGRID plant-average ANNUAL heat rate the fleet loader
    otherwise gives a coal generator, which folds startup fuel, shutdown tails
    and the offline hours' fuel into the number that sets the plant's offer and
    which moves with the plant's capacity factor in the vintage year
    (CLAUDE.md rule 14 [R-ACCURATE]).

    The coal sibling of :func:`measured_ct_heat_rates`, on the identical
    identification: a machine's operating heat rate is a physical
    characteristic that regenerates for a forward year and responds to changed
    conditions, so it is an INPUT under rule 13 [R-MEASURED], never a measured
    outcome fed back to close a residual, and it carries zero free parameters.

    Only ``flag == "ok"`` rows are returned: the derive marks any plant outside
    the physical coal-steam band as a meter defect rather than applying it.
    Empty dict when the ISO has no artifact, which leaves every plant on its
    eGRID rate — never a silent hand number (rule 23 [R-FROZEN-DERIVE]).
    """
    path = PROCESSED_DIR / f"campd_coal_heat_rates_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, usecols=["plant_code", "heat_rate", "flag"])
    return {
        int(r.plant_code): float(r.heat_rate)
        for r in df.itertuples(index=False)
        if str(r.flag) == "ok" and float(r.heat_rate) > 0.0
    }


@lru_cache(maxsize=8)
def measured_st_heat_rates(iso: str) -> dict[int, float]:
    """Return ``{plant_code: measured operating heat rate}`` for an ISO's ST_GAS.

    Reads the committed CAMPD-measured artifact
    (``scripts/data/derive_campd_gas_st_heat_rates.py`` →
    ``data/raw/_processed-legacy/campd_st_heat_rates_<ISO>.csv``): per-plant
    MMBtu per **net** MWh over the plant's own steady-state operating hours,
    pooled 2023-2025 over the CAMPD boiler units the derive pairs to that
    plant's model ``ST_GAS`` rows. It replaces the eGRID plant-average ANNUAL
    heat rate the fleet loader otherwise gives a gas-fired steam boiler
    (CLAUDE.md rule 14 [R-ACCURATE]).

    The gas-steam sibling of :func:`measured_ct_heat_rates` and
    :func:`measured_coal_heat_rates`, on the identical identification: a
    machine's operating heat rate is a physical characteristic that
    regenerates for a forward year and responds to changed conditions, so it
    is an INPUT under rule 13 [R-MEASURED], never a measured outcome fed back
    to close a residual, and it carries zero free parameters.

    What it reaches that the two mechanisms above it cannot: a southeastern
    steam station is routinely a coal boiler and a gas boiler behind one ORIS
    code, and BOTH the eGRID plant rate and the prime-mover-FAMILY rate
    (``ScenarioConfig.egrid_family_heat_rates``) blend them, because both
    machines are prime mover ``ST``. Only a per-unit meter separates them.
    Measured on SOCO: E C Gaston's ST family rate 11.5505 blends one 832 MW
    coal boiler with four ~255 MW gas boilers whose own metered rate is
    11.0744.

    Only ``flag == "ok"`` rows are returned: the derive marks any plant outside
    the physical gas-steam band, or whose capacity pairing is structurally
    mismatched, as a defect rather than applying it. Empty dict when the ISO
    has no artifact, which leaves every plant on its eGRID rate — never a
    silent hand number (rule 23 [R-FROZEN-DERIVE]).
    """
    path = PROCESSED_DIR / f"campd_st_heat_rates_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, usecols=["plant_code", "heat_rate", "flag"])
    return {
        int(r.plant_code): float(r.heat_rate)
        for r in df.itertuples(index=False)
        if str(r.flag) == "ok" and float(r.heat_rate) > 0.0
    }


@lru_cache(maxsize=8)
def measured_chp_heat_rates(iso: str) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, class): measured power-only heat rate}`` for CHP.

    Reads the committed measured artifact
    (``scripts/data/derive_chp_power_only_heat_rates.py`` →
    ``data/raw/_processed-legacy/chp_power_only_heat_rates_<ISO>.csv``): the
    plant's own ``(PLHTIAN + CHPCHTI) / PLNGENAN`` from the same eGRID vintage
    the model's incumbent ``heat_rate`` is joined from — that is, eGRID's
    published rate with eGRID's published CHP useful-thermal heat-input
    allocation added back, on the SAME net-generation denominator. It replaces
    the **steam-credited** rate a cogen otherwise carries, which is not the rate
    at which the machine turns fuel into power and which makes CHP the cheapest
    thermal on the system (CLAUDE.md rule 14 [R-ACCURATE]).

    Keyed on the ``(plant_code, plant_group)`` PAIR, not the plant: a mixed
    facility's out-of-scope rows (its ``ST_CHP`` boiler train, its merchant
    ``CC_REGULAR`` block) must keep the rate they have.

    Only ``flag == "ok"`` rows are returned — the derive writes every plant in
    the population, including the ones its topping-cycle and physical-band
    gates reject, and those keep the existing eGRID → hand-factor chain. Empty
    dict when the ISO has no artifact, which leaves every plant unchanged —
    never a silent hand number (rule 24 [R-REGISTRY]).
    """
    path = PROCESSED_DIR / f"chp_power_only_heat_rates_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, usecols=["plant_code", "plant_group", "heat_rate", "flag"])
    return {
        (int(r.plant_code), str(r.plant_group)): float(r.heat_rate)
        for r in df.itertuples(index=False)
        if str(r.flag) == "ok" and float(r.heat_rate) > 0.0
    }


# Model plant_group -> CAMPD ramp-envelope family bucket. Mirrors the derive
# script's unitType bucketing (scripts/data/derive_campd_ramp_envelopes.py) so a
# mixed facility (CC block + standalone peakers) is enveloped per family.
_RAMP_BUCKET_BY_GROUP: dict[str, str] = {
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "ST_GAS": "ST",
    "ST_CHP": "ST",
    "COAL": "ST",
    "CT_PEAKER": "CT",
    "CT_CHP": "CT",
}


@lru_cache(maxsize=1)
def _ramp_parasitic_factor_map() -> "dict[int, float]":
    """Return ``{plant_code: net/gross factor}`` for the ramp-envelope rebasis.

    Reads the pooled (``year == 0``) rows of the committed parasitic-load
    artifact (``scripts/data/derive_parasitic_factors.py`` →
    ``data/raw/_processed-legacy/parasitic_load_factors.parquet``,
    :func:`market_sim.data.campd.compute_parasitic_factors`) — annual EIA-923
    NET generation over annual CAMPD GROSS, per plant, with that derive's own
    class default already substituted for out-of-band/missing reconciliations.

    Empty when the artifact is absent; :func:`build_ramp_groups` then leaves
    the affected plants on the published gross basis (factor 1.0) and logs the
    count, rather than inventing a conversion (rule 5 ``[R-NO-MAGIC]``).
    """
    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    pooled = df[df["year"] == 0]
    return {
        int(p): float(f)
        for p, f in zip(pooled["plant_id"], pooled["parasitic_factor"])
        if float(f) > 0.0
    }


@lru_cache(maxsize=8)
def load_campd_ramp_envelopes(iso: str) -> "pd.DataFrame | None":
    """Return the ISO's CAMPD plant-level hourly ramp-envelope table, or None.

    Reads the committed measured artifact
    (``scripts/data/derive_campd_ramp_envelopes.py`` →
    ``data/raw/_processed-legacy/campd_ramp_envelopes_<ISO>.csv``): per
    (plant, CC/CT/ST bucket) max observed 1-h up/down gross-load deltas
    pooled 2023-2025 (``basis == "plant"``), sparse-coverage rows
    (``basis == "sparse"``, informational only) and the capacity-weighted
    class-median envelope FRACTIONS under ``plant_code == 0``
    (``basis == "class_fraction"``).

    The frame is returned exactly as published, on CAMPD's **GROSS** basis;
    :func:`build_ramp_groups` rebases the MW rows to the model's NET columns
    (the ``class_fraction`` rows need no rebasis — see its comment). ``None``
    when the ISO has no artifact —
    the ramp rows are then simply absent (never a silent hand number,
    rule #23). Cached per ISO; treat the returned frame as read-only.
    """
    path = PROCESSED_DIR / f"campd_ramp_envelopes_{iso.upper()}.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def build_ramp_groups(
    fleet: FleetArrays, iso: str
) -> "tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None":
    """Group thermal columns into ramp-enveloped plant groups for the LP.

    Members are grouped by ``(plant_code, family bucket)`` where the bucket
    collapses the model plant groups onto the CAMPD envelope families
    (CC_REGULAR/CC_CHP → CC; ST_GAS/ST_CHP/COAL → ST; CT_PEAKER/CT_CHP →
    CT) — the envelope is a plant property, tranche switching inside a plant
    stays free (design doc §1.2). Each group's envelope resolves from its
    measured ``basis == "plant"`` row (published MW, rebased from CAMPD gross
    to the model's NET basis by that plant's measured EIA-923-net /
    CAMPD-gross parasitic factor); groups without one
    fall back to the CC/ST class-median fraction × group pmax. CT groups get
    NO fallback — a CT without a well-observed CEMS trace simply has no row
    (bang-bang is the measured norm for the class).

    Pruning (rule 18 — physics by parameters, not class names): a group
    whose envelope can never bind (``RU >= cap`` AND ``RD >= cap``, with
    ``cap`` the group's summed pmax) gets no row — bang-bang CTs drop out
    naturally, as do import pseudo-generators (``plant_code == 0``, never
    grouped).

    Args:
        fleet: Vectorized fleet arrays (needs ``plant_code``, ``plant_group``
            and ``pmax``).
        iso: ISO identifier keying the committed envelope artifact.

    Returns:
        ``(gen_idx, group_col, ramp_up_mw, ramp_dn_mw)`` for
        :func:`market_sim.model.dispatch.build_constraints` — member thermal
        column indices, each member's group index, and the per-group
        envelopes — or ``None`` when the artifact is absent, the fleet
        carries no plant groups, or every group pruned out.
    """
    env = load_campd_ramp_envelopes(iso)
    if env is None or fleet.plant_group is None:
        return None
    plant_code = np.asarray(fleet.plant_code, dtype=int)
    pmax = np.asarray(fleet.pmax, dtype=float)
    buckets = np.array(
        [
            _RAMP_BUCKET_BY_GROUP.get(str(g), "")
            for g in np.asarray(fleet.plant_group, dtype=object)
        ],
        dtype=object,
    )

    # GROSS -> NET rebasis (ercot127 §1, repaired ercot132 leg A). The derive
    # measures CAMPD ``grossLoad`` deltas and the LP's P columns are NET, so
    # the published MW are ~10 % looser than the measured capability. The
    # conversion lives HERE, on the loader side, and NOT in the derive, for
    # three reasons (putting it in both would double-count):
    #   1. The artifact is a MEASUREMENT RECORD of what CAMPD reports, which is
    #      gross. A derive that silently wrote net would misrepresent its own
    #      source, and rule 23 [R-FROZEN-DERIVE] re-derives only on a source
    #      change -- a representation fix is not one.
    #   2. The basis change happens exactly where the measured plant MW meets
    #      the model's net columns, which is this seam.
    #   3. Only the ``basis == "plant"`` rows carry MW. The
    #      ``class_fraction`` fallback rows are ALREADY basis-neutral by
    #      construction -- the derive forms them as
    #      ``median(gross_delta / gross_pmax_obs)``, a gross-over-gross ratio,
    #      and this function applies them as ``frac x net pmax``, which yields
    #      a net delta with no conversion at all. A derive-side fix would have
    #      to convert one row family and not the other, i.e. write a
    #      mixed-basis file; converting here keeps that asymmetry explicit.
    # The factor is the per-plant MEASURED EIA-923-net / CAMPD-gross ratio
    # (rule 14 [R-ACCURATE]) -- never ERCOT's coal 0.897 class annual-energy
    # ratio, which is a single-class energy aggregate and has no business
    # rebasing a per-plant cross-class ramp envelope.
    # The factor is the plant's MEASURED EIA-923-net / CAMPD-gross ratio where
    # the committed artifact has one (rule 14 [R-ACCURATE]); where it does not,
    # the cited class default keyed by the group's OWN model ``plant_group``
    # (``campd.DEFAULT_PARASITIC_LOAD_PCT``, EPRI/EIA station-service typicals)
    # — the identical measured-else-class-default resolution
    # :func:`market_sim.data.campd.compute_parasitic_factors` applies for the
    # same reason, so the two paths cannot disagree. It is NEVER ERCOT's coal
    # 0.897 class annual-energy ratio, which is a single-class energy aggregate
    # and has no business rebasing a per-plant cross-class ramp envelope.
    parasitic = _ramp_parasitic_factor_map()
    measured = {
        (int(r.plant_code), str(r.bucket)): (
            float(r.ramp_up_mw),
            float(r.ramp_dn_mw),
        )
        for r in env[env.basis == "plant"].itertuples(index=False)
    }
    class_frac = {
        str(r.bucket): (float(r.ramp_up_mw), float(r.ramp_dn_mw))
        for r in env[env.basis == "class_fraction"].itertuples(index=False)
        # CT gets NO class fallback: only a measured plant row can envelope it.
        if str(r.bucket) in ("CC", "ST")
    }

    # Group member columns by (plant, bucket); insertion order is stable.
    members: dict[tuple[int, str], list[int]] = {}
    for i in np.flatnonzero((plant_code > 0) & (buckets != "")):
        members.setdefault((int(plant_code[i]), str(buckets[i])), []).append(int(i))

    plant_groups = np.asarray(fleet.plant_group, dtype=object)

    def _net_basis_factor(pk: int, m: list[int]) -> float:
        """Gross -> net factor for one measured plant group (see above)."""
        factor = parasitic.get(int(pk))
        if factor is not None:
            return factor
        # No measured reconciliation for this plant: fall back to the cited
        # class default, keyed by the group's capacity-dominant model
        # plant_group (finer than the artifact's CC/CT/ST bucket, which
        # collapses COAL and ST_GAS into one family with different typicals).
        by_group: dict[str, float] = {}
        for i in m:
            g = str(plant_groups[i])
            by_group[g] = by_group.get(g, 0.0) + float(pmax[i])
        dominant = max(by_group, key=by_group.get) if by_group else ""
        pct = DEFAULT_PARASITIC_LOAD_PCT.get(dominant, _DEFAULT_PARASITIC_LOAD_PCT)
        return 1.0 - pct

    gen_idx: list[int] = []
    group_col: list[int] = []
    ramp_up: list[float] = []
    ramp_dn: list[float] = []
    n_measured_factor = 0
    n_class_default = 0
    for (pk, bucket), m in members.items():
        cap = float(pmax[m].sum())
        if (pk, bucket) in measured:
            ru, rd = measured[(pk, bucket)]
            factor = _net_basis_factor(pk, m)
            if int(pk) in parasitic:
                n_measured_factor += 1
            else:
                n_class_default += 1
            ru, rd = ru * factor, rd * factor
        elif bucket in class_frac:
            fu, fd = class_frac[bucket]
            ru, rd = fu * cap, fd * cap
        else:
            continue
        if ru >= cap and rd >= cap:
            continue  # envelope can never bind (bang-bang) — prune, no row
        g = len(ramp_up)
        gen_idx.extend(m)
        group_col.extend([g] * len(m))
        ramp_up.append(ru)
        ramp_dn.append(rd)
    if not ramp_up:
        return None
    logger.info(
        "ramp envelopes (%s): %d group(s) — gross->net rebasis from %d "
        "measured parasitic factor(s) and %d class default(s)",
        iso.upper(),
        len(ramp_up),
        n_measured_factor,
        n_class_default,
    )
    return (
        np.asarray(gen_idx, dtype=int),
        np.asarray(group_col, dtype=int),
        np.asarray(ramp_up, dtype=float),
        np.asarray(ramp_dn, dtype=float),
    )


# Default location of the CAMPD-derived per-plant emission-rate artifact
# (scripts/data/derive_plant_emissions.py), resolved relative to the repo root.
PLANT_EMISSION_RATES_PATH: Path = PROCESSED_DIR / "plant_emission_rates.parquet"

# kg -> metric tonnes, the model's internal emission-rate mass unit.
_KG_PER_TONNE: float = 1000.0


@lru_cache(maxsize=4)
def _plant_emission_rate_map(
    path: str,
) -> dict[int, tuple[float, float, float]]:
    """Return ``{plant_id: (co2, nox, so2)}`` rates in tonnes/MWh net.

    Reads the pooled (``year == 0``) rows of the CAMPD emission-rate
    artifact and converts the per-MWh-net kg figures to the model's
    tonnes/MWh unit. Plants flagged ``mixed`` (coal and gas units sharing one
    facility CEMS record) are omitted — a single facility rate cannot be
    assigned to their separate coal and gas dispatch bins, so those bins keep
    fuel-class defaults. Cached by path so repeated yearly fleet builds in one
    run parse the parquet once.
    """
    df = pd.read_parquet(path)
    pooled = df[df["year"] == 0]
    if "mixed" in pooled.columns:
        pooled = pooled[~pooled["mixed"].astype(bool)]
    out: dict[int, tuple[float, float, float]] = {}
    # itertuples over the four columns actually read (name=None => positional,
    # so no attribute-name mangling): ~an order of magnitude cheaper than
    # iterrows, which materializes a dtype-upcast Series per row. Every value
    # still goes through int()/float(), so the result is identical.
    cols = [
        "plant_id",
        "co2_kg_per_mwh_net",
        "nox_kg_per_mwh_net",
        "so2_kg_per_mwh_net",
    ]
    for plant_id, co2, nox, so2 in pooled[cols].itertuples(index=False, name=None):
        out[int(plant_id)] = (
            float(co2) / _KG_PER_TONNE,
            float(nox) / _KG_PER_TONNE,
            float(so2) / _KG_PER_TONNE,
        )
    return out


@lru_cache(maxsize=8)
def _measured_plant_rate_map_v2(
    path: str,
    iso: str,
    year: int,
    mode: str,
    as_of_year: int | None = None,
    exclude_quarantined: bool = False,
) -> dict[tuple[int, str], tuple[float, float, float]]:
    """Cache the mode-aware ``{(plant_id, fuel_class): (tCO2, tNOx, tSO2)/MWh}`` map.

    All three pollutants share the identical mode/window/composition-mask policy
    (:func:`market_sim.data.emission_rates.measured_plant_rates`); NOx/SO2 simply
    read their own mass column (plan §5 R7). A plant/class missing a pollutant's
    measured mass gets 0.0 for that pollutant, so the caller can preserve the
    fuel-class default (CO2/NOx) rather than overwrite it with a spurious zero.
    ``as_of_year`` / ``exclude_quarantined`` are the FH-1 hindcast-lane as-of
    bound and T1-FF quarantine trim — part of the cache key so a bounded run
    never shares a map with a run that admits the later/quarantined rows.
    """
    from market_sim.data.emission_rates import measured_plant_rates

    df = pd.read_parquet(path)
    kw = {"as_of_year": as_of_year, "exclude_quarantined": exclude_quarantined}
    co2 = measured_plant_rates(df, iso, year, mode, pollutant="co2", **kw)
    nox = measured_plant_rates(df, iso, year, mode, pollutant="nox", **kw)
    so2 = measured_plant_rates(df, iso, year, mode, pollutant="so2", **kw)
    keys = set(co2) | set(nox) | set(so2)
    return {k: (co2.get(k, 0.0), nox.get(k, 0.0), so2.get(k, 0.0)) for k in keys}


def _apply_forward_control_retrofits(
    rates: dict[tuple[int, str], tuple[float, float, float]],
    config: object,
    year: int,
) -> dict[tuple[int, str], tuple[float, float, float]]:
    """Step measured ``(co2, nox, so2)`` rates for announced EIA-860 controls.

    The forward control-retrofit channel
    (``docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md``):
    splits the triple map into per-pollutant float maps, applies
    :func:`market_sim.data.emission_rates.apply_control_retrofits` to each with
    the forecast-year announced-control schedule (a control online by ``year``
    steps the covered plant's rate down), and recombines. Returns the input map
    unchanged when no control is announced. Forecast-only; the caller gates on
    the mode and the ``control_retrofit_forward`` flag.
    """
    from market_sim.config import constants
    from market_sim.data.emission_rates import (
        apply_control_retrofits,
        load_announced_controls,
    )

    controls = load_announced_controls(
        getattr(config, "control_retrofit_path", ""),
        min_install_year=constants.CONTROL_RETROFIT_HISTORY_END_YEAR + 1,
    )
    if not controls:
        return rates
    # One stepped float map per pollutant (index 0=co2, 1=nox, 2=so2), then zip
    # back into triples. Fresh dicts throughout — the cached input is untouched.
    stepped = [
        apply_control_retrofits(
            {k: v[i] for k, v in rates.items()}, controls, year, pollutant
        )
        for i, pollutant in enumerate(("co2", "nox", "so2"))
    ]
    return {k: (stepped[0][k], stepped[1][k], stepped[2][k]) for k in rates}


def apply_plant_emission_rates_v2(
    generators: list[Generator],
    path: str | Path,
    *,
    iso: str,
    year: int,
    mode: str,
    config: object | None = None,
) -> int:
    """Override per-generator CO2 rates from the v2 artifact (mode-aware).

    Uses :func:`market_sim.data.emission_rates.measured_plant_rates`: a backcast
    year books each plant's own measured rate, a forecast year books the
    gen-weighted trailing-average estimator base. Rates are matched to each
    generator by ``(plant_code, coarse fuel class)`` — the composition mask — so
    a Parish-style coal+gas facility's coal and gas bins get separate measured
    rates (this replaces the old ``mixed`` exclusion). Returns the override count.

    CO2, NOx and SO2 are all booked at the plant's measured tonnes/MWh-net rate
    (plan §5 R7 full-wiring wave). CO2/NOx are overridden only when the measured
    rate is positive (a zero means "no measured mass" — keep the fuel default);
    SO2 is always set, mirroring :func:`apply_plant_emission_rates`, because zero
    is a legitimate SO2 value for gas units. NOx/SO2 are secondary: this changes
    no CO2 rate and no merit order.

    **The measured rate is the HOST STACK's, so a unit with a capture island
    books it net of that unit's own capture** (capx D77): CO2 is set to
    ``measured × (1 - gen.ccs_capture_fraction)``. The fraction is 0.0 on every
    unabated unit, so this is an exact no-op outside a CCS cohort. It exists
    because this function runs EVERY forecast year, downstream of capacity
    evolution (``build_dispatch_fleet``), and matches on ``(plant_code, coarse
    fuel class)`` — and ``fuel_class("gas_cc_ccs") == "gas"``, so a retrofitted
    unit still matches its own host row. Without the factor the retrofit's
    capture was overwritten on the first dispatch build after conversion, in the
    dispatch fleet and (the CAMPD path concatenates rather than copies) in the
    persistent fleet, leaving the unit dispatching, pricing its carbon adder and
    accounting at its uncaptured intensity. NOx/SO2 are NOT scaled — the model
    carries no capture co-benefit parameter for them.
    docs/handoffs/FINDING-capx-d77-2026-09-06.md

    When ``config.control_retrofit_forward`` is set and this is a **forecast**
    year, each pollutant's measured map is stepped by any announced EIA-860
    control online by ``year`` (SCR/SNCR → NOx, FGD/DSI → SO2, from the
    committed-install pipeline; CO2 carries no default control — carbon capture
    is owned by the CCS retrofit screen, rule 15), via
    :func:`_apply_forward_control_retrofits`. OFF or backcast leaves the maps
    byte-identical.
    docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md
    """
    from market_sim.data.emission_rates import fuel_class

    resolved = Path(path)
    if not resolved.exists():
        return 0
    rates = _measured_plant_rate_map_v2(
        str(resolved),
        str(iso),
        int(year),
        str(mode),
        # FH-1 as-of bound, hindcast lane only: the estimator basis may not
        # contain CAMPD years after the target year. The plain forecast lane
        # (hindcast False) passes None and keeps its basis byte-identical.
        int(year) if bool(getattr(config, "hindcast", False)) else None,
        # T1-FF quarantine trim (FH-1): a full-forward hindcast's estimator
        # basis additionally drops the rule-22 quarantined artifact years
        # (2022, >=2026).
        bool(getattr(config, "is_full_forward_hindcast", False)),
    )
    if (
        str(mode).lower() != "backcast"
        and config is not None
        and getattr(config, "control_retrofit_forward", False)
    ):
        rates = _apply_forward_control_retrofits(rates, config, int(year))
    n = 0
    for gen in generators:
        triple = rates.get((int(gen.plant_code), fuel_class(gen.fuel_type)))
        if triple is None:
            continue
        co2, nox, so2 = triple
        touched = False
        if co2 > 0.0:
            # capx D77: the measured rate is the HOST STACK's intensity, so a
            # unit carrying a capture island emits that rate net of its own
            # capture. Booking the two together here is what keeps the measured
            # input entering every year (rule 13 [R-MEASURED]) while a CCS unit
            # is never silently restored to its uncaptured rate -- one
            # composition point, not a second capture mechanism (rule 19
            # [R-ONE-MECH]). ``ccs_capture_fraction`` is 0.0 on every unabated
            # unit, so this is an exact no-op for the whole fleet outside the
            # retrofit cohort and for every backcast (no measured backcast fleet
            # contains a converted unit). NOx/SO2 are deliberately NOT scaled:
            # the model carries no capture co-benefit parameter for them and
            # inventing one would be a new free parameter (rule 21 [R-DOF]).
            gen.emission_rate_co2 = co2 * (1.0 - float(gen.ccs_capture_fraction))
            touched = True
        if nox > 0.0:
            gen.nox_rate = nox
            touched = True
        gen.so2_rate = so2
        if touched or so2 > 0.0:
            n += 1
    return n


def apply_plant_emission_rates(
    generators: list[Generator],
    path: str | Path | None = None,
) -> int:
    """Override per-generator CO2/NOx/SO2 rates with CAMPD plant-specific ones.

    Each generator pinned to a single physical plant (``plant_code > 0``)
    that the CAMPD emission-rate artifact covers takes that plant's measured
    intensity per MWh **net** generation, so carbon / NOx / SO2 prices in the
    dispatch LP bite at the real plant rather than a fuel-class average.
    Generators without a plant code, or whose plant is absent from the
    artifact (multi-plant peaker bins, the legacy aggregated fleet), keep
    their fuel-default rates. CO2 and NOx are overridden only when the
    measured rate is positive; SO2 is always set (zero is a valid value for
    gas units, and the default is zero anyway). As in
    :func:`apply_plant_emission_rates_v2`, CO2 is booked net of the unit's own
    ``ccs_capture_fraction`` (capx D77) — 0.0, and so an exact no-op, on every
    unabated unit.

    Args:
        generators: The fleet to mutate in place.
        path: Override for the artifact location; ``None`` uses
            :data:`PLANT_EMISSION_RATES_PATH`.

    Returns:
        The number of generators whose rates were overridden.
    """
    resolved = Path(path) if path is not None else PLANT_EMISSION_RATES_PATH
    if not resolved.exists():
        return 0
    rates = _plant_emission_rate_map(str(resolved))
    n = 0
    for gen in generators:
        plant_rate = rates.get(int(gen.plant_code))
        if plant_rate is None:
            continue
        co2, nox, so2 = plant_rate
        if co2 > 0.0:
            # capx D77, identical to the v2 branch above: the measured rate is
            # the host stack's, so a unit with a capture island books it net of
            # its own capture. 0.0 on every unabated unit, so this branch is
            # byte-identical for every fleet that contains no converted unit.
            gen.emission_rate_co2 = co2 * (1.0 - float(gen.ccs_capture_fraction))
        if nox > 0.0:
            gen.nox_rate = nox
        gen.so2_rate = so2
        n += 1
    return n


def _fill_plant_hr(hr: float | None, plant_group: str) -> float:
    """Return a plant's heat rate, falling back to the plant-group default.

    Plants without a measured ``Plant_Avg_HR_MMBtu_MWh`` (typically tiny
    unmetered backup CTs in CT_unassigned) inherit the per-group default
    so the LP never sees a NaN heat rate.
    """
    if hr is not None and hr == hr and hr > 0.0:
        return float(hr)
    return BIN_GROUP_HR_DEFAULT.get(plant_group, 10.0)


def _fill_hr_multiplier(value: float | None, default: float) -> float:
    """Return a tranche HR multiplier, falling back to ``default`` if blank.

    Plants whose tranche capacity is zero leave the corresponding
    ``HR_Mult_<tranche>`` column blank; the per-fuel default keeps the
    arithmetic well-defined even when the resulting tranche is skipped.
    """
    if value is not None and value == value and value > 0.0:
        return float(value)
    return float(default)


# Per-plant-group default tranche HR multipliers, used when the CSV's
# ``HR_Mult_<tranche>`` cell is blank (a tranche with zero capacity for
# that plant). The values match the typical multipliers seen in the CSV
# for each group so a sensitivity run that turns on a zero-share tranche
# still produces a reasonable heat rate.
_DEFAULT_HR_MULT_BY_GROUP: dict[str, dict[str, float]] = {
    "CC_CHP": {"mr": 1.05, "mc": 1.05, "econ": 1.00, "peak": 1.45},
    "CC_REGULAR": {"mr": 1.10, "mc": 1.08, "econ": 1.00, "peak": 1.55},
    "CT_CHP": {"mr": 1.05, "mc": 1.10, "econ": 1.00, "peak": 1.15},
    "CT_PEAKER": {"mr": 1.05, "mc": 1.12, "econ": 1.00, "peak": 1.10},
    "ST_GAS": {"mr": 1.10, "mc": 1.15, "econ": 1.00, "peak": 1.10},
    "ST_CHP": {"mr": 1.05, "mc": 1.10, "econ": 1.00, "peak": 1.10},
    "COAL": {"mr": 1.00, "mc": 1.15, "econ": 1.00, "peak": 1.05},
}


def _override_bin_class_from_eia923(bins: pd.DataFrame, year: int) -> pd.DataFrame:
    """Override each gas bin's ``Plant_Group`` with its EIA-923 dominant class.

    For every bin whose curated class is one of the gas classes, replace it with
    the EIA-923 dominant class for that plant code when EIA-923 covers the year
    and resolves to a (different) gas class. The bin's ``fuel`` is re-derived
    from the new class; all other columns are preserved. Coal bins and plants
    EIA-923 doesn't cover keep their curated class — the durable single source
    of truth for ERCOT class assignment.
    """
    dominant = eia923_dominant_class_by_plant(year)
    if not dominant:
        return bins

    new_groups = bins["Plant_Group"].astype(str).tolist()
    changed: list[tuple[str, str, str]] = []
    for i, (code, curated) in enumerate(zip(bins["Plant_Code"], new_groups)):
        if curated not in _GAS_BIN_GROUPS:
            continue  # coal (and any non-gas bin) keeps its curated class
        derived = dominant.get(int(code))
        if derived and derived in _GAS_BIN_GROUPS and derived != curated:
            new_groups[i] = derived
            changed.append((str(bins["Plant_Name"].iloc[i]), curated, derived))

    if not changed:
        return bins

    bins = bins.copy()
    bins["Plant_Group"] = new_groups
    bins["fuel"] = bins["Plant_Group"].map(BIN_GROUP_TO_FUEL)
    for name, was, now in changed:
        logger.info(
            "EIA-923 %d: reclassified %s  %s -> %s (curated bin drifted)",
            year,
            name,
            was,
            now,
        )
    return bins


def _reconcile_cc_capacity(
    bins: pd.DataFrame, reconcile_path: str | Path
) -> pd.DataFrame:
    """Reconcile listed CC plants' ``capacity_mw`` to their demonstrated value.

    Reads the per-plant reconciliation table
    (``scripts/data/derive_cc_capacity_reconcile.py``) and applies each row per its
    ``mode`` column:

    * ``raise`` (or no ``mode`` column — the original ERCOT table, unchanged
      behaviour): lift ``capacity_mw`` to ``reconciled_mw`` where it exceeds
      the current value — the demonstrated CAMPD peak above nameplate (the
      cold-weather over-rating). A reconciled value at or below the current
      capacity is ignored, so a raise row can never shrink a plant.
    * ``cap``: lower ``capacity_mw`` to ``reconciled_mw`` where the current
      value exceeds it — the demonstrated-peak CAP for plants whose model
      nameplate exceeds anything the plant ever sustained in the CEMS record
      (measured capability, CLAUDE.md #13: the plant should not carry LP
      headroom above what it has ever delivered). A cap row at or above the
      current capacity is ignored, so a cap row can never grow a plant.

    A missing file is a no-op (the flag is on but the artifact was not
    generated). See :attr:`ScenarioConfig.cc_capacity_reconcile`.
    """
    path = Path(reconcile_path)
    if not path.exists():
        logger.warning(
            "cc_capacity_reconcile on but %s missing — no capacity change", path
        )
        return bins
    table = pd.read_csv(path)
    mode = (
        table["mode"].astype(str)
        if "mode" in table.columns
        else pd.Series("raise", index=table.index)
    )
    codes = table["plant_code"].astype(int)
    mw = table["reconciled_mw"].astype(float)
    recon_raise = dict(zip(codes[mode != "cap"], mw[mode != "cap"]))
    recon_cap = dict(zip(codes[mode == "cap"], mw[mode == "cap"]))
    old_cap = bins["capacity_mw"].astype(float).to_numpy()
    new_cap = np.array(
        [
            min(
                max(float(cur), recon_raise.get(int(code), 0.0)),
                recon_cap.get(int(code), np.inf),
            )
            for code, cur in zip(bins["Plant_Code"].astype(int), old_cap)
        ]
    )
    raised = int((new_cap > old_cap + 1e-6).sum())
    capped = int((new_cap < old_cap - 1e-6).sum())
    bins = bins.copy()
    bins["capacity_mw"] = new_cap
    logger.info(
        "CC capacity reconcile: raised %d / capped %d plant(s) to demonstrated "
        "peak (%+.0f MW total) from %s",
        raised,
        capped,
        float((new_cap - old_cap).sum()),
        path.name,
    )
    return bins


# Memoized per-(path, year, reconcile-path) bin frames. ``load_campd_bins`` is
# invoked repeatedly per fleet build (the dispatch path plus every outage
# overlay), and the CSV read + tranche arithmetic is pure w.r.t. its args, so
# the frame is computed once per key and callers receive a defensive copy.
_CAMPD_BINS_CACHE: dict[tuple[str, int | None, str | None], pd.DataFrame] = {}


def load_campd_bins(
    csv_path: str | Path,
    year: int | None = None,
    capacity_reconcile_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load the CAMPD bin assignments, one row per plant.

    The detail CSV has one row per plant; this normalises it into the
    one-bin-per-plant LP fleet schema. Every plant becomes its own
    operational bin: tranche percentages, commitment hours and the
    per-tranche HR multipliers come directly from the plant's CSV row,
    and per-tranche heat rates are derived from the plant's own
    ``Plant_Avg_HR_MMBtu_MWh`` rather than a zone-weighted average.

    When ``year`` is given, each bin's gas class (``Plant_Group``) is
    overridden with the EIA-923 dominant class for that plant code
    (:func:`eia923_dominant_class_by_plant`), so the curated bin can't drift
    from what the plant actually burned — e.g. a CC_CHP bin whose EIA-923
    netgen is dominated by merchant CC output is corrected to CC_REGULAR. Only
    the class (and the fuel it implies) changes; every other curated column
    (tranche %, HR multipliers, turbine class, config) is preserved, and the
    override only moves a plant among the gas classes. Plants EIA-923 doesn't
    cover for the year (or coal bins) keep their curated class. ``year=None``
    (the default, for tooling and forward scenarios) applies no override.

    Per-plant binning is the model spine for plant-specific monthly
    EIA-923 fuel costs and asset-level financial reporting — each LP bin
    is one EIA plant code, so dispatch and downstream P&L disaggregation
    share the same row identity.

    The ``Bin_Label`` / ``Bin_Number`` columns are a human-readable
    grouping only — they do NOT collapse plants into a shared LP generator
    and no bin-weighted heat rate is ever used in dispatch (each plant
    dispatches on its own ``Plant_Avg_HR_MMBtu_MWh``). Two CSV columns are
    read here but then commonly *overridden* downstream, so do not treat
    them as the dispatched values:

    * ``Pct_Committed`` / ``Pct_Peaking`` — replaced per-plant by the
      CAMPD-derived ``CC_REGULAR_COMMITTED_PCT_BY_PLANT`` (``config.
      cc_committed_per_plant``, the ERCOT calibration default) /
      :func:`thermal_tranche_peaking` or the EIA-860 ``cc_duct_peaking_pct``
      (``config.cc_peaking_per_plant`` / ``cc_duct_peaking`` — ERCOT's default
      is ``cc_duct_peaking``, since it carries no CAMPD thermal-tranche
      artifact of its own).
    * ``HR_Mult_Committed`` / ``HR_Mult_Economic`` / ``HR_Mult_Peaking`` —
      used only when no ``offer_curve_by_group`` covers the group. With an
      offer curve configured (the ERCOT default) the committed band uses
      ``base_hr × offer["committed"]``, the economic band is rendered as an
      N-slice rising ramp (``_econ_curve_steps``), and the CC peak band uses
      the turbine-class duct-burner multiplier — so the CSV ``HR_Mult_*``
      values are not the dispatched band heat rates. See ``bins_to_fleet``
      and ``docs/binning-methodology.md``.

    Args:
        csv_path: Path to ``custom-bin-assignments.csv``.

    Returns:
        One row per plant with columns: the original bin key columns,
        ``Plant_Code``, ``Plant_Name``, ``capacity_mw``, ``hr_weighted``
        (the plant's own HR), ``hr_mr`` / ``hr_mc`` / ``hr_econ`` /
        ``hr_peak`` (= ``Plant_Avg_HR × HR_Mult_<tranche>``),
        ``pct_mr`` / ``pct_mc`` / ``pct_econ`` / ``pct_peak``,
        ``min_run``, ``min_down``, ``plant_count`` (always 1),
        ``plant_codes`` (a one-element list with the plant code),
        ``fuel``.
    """
    cache_key = (
        str(csv_path),
        year,
        None if capacity_reconcile_path is None else str(capacity_reconcile_path),
    )
    cached = _CAMPD_BINS_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    detail = pd.read_csv(csv_path)
    fuel_series = detail["Plant_Group"].map(BIN_GROUP_TO_FUEL)
    unmapped = detail[fuel_series.isna()]
    if not unmapped.empty:
        groups = sorted(unmapped["Plant_Group"].unique())
        raise ValueError(
            f"CAMPD bins reference unknown plant groups: {groups}. "
            f"Add them to BIN_GROUP_TO_FUEL."
        )

    # Multi-tech CT correction: at mixed-facility plants (CC+CT, COAL+CT)
    # the plant-average HR is dominated by the efficient dominant technology,
    # making the CT bin 25-40% cheaper than a standalone CT. Clip multi-tech
    # CT heat rates to the standalone CT median for the ISO.
    if "Mixed_Facility" in detail.columns:
        ct_mask = detail["Plant_Group"] == "CT_PEAKER"
        mixed_mask = detail["Mixed_Facility"].notna() & (
            detail["Mixed_Facility"].astype(str).str.strip() != ""
        )
        multi_ct = ct_mask & mixed_mask
        if multi_ct.any():
            standalone_ct = ct_mask & ~mixed_mask
            median_ct_hr = (
                float(detail.loc[standalone_ct, "Plant_Avg_HR_MMBtu_MWh"].median())
                if standalone_ct.any()
                else 11.5
            )
            before = detail.loc[multi_ct, "Plant_Avg_HR_MMBtu_MWh"].copy()
            detail.loc[multi_ct, "Plant_Avg_HR_MMBtu_MWh"] = detail.loc[
                multi_ct, "Plant_Avg_HR_MMBtu_MWh"
            ].clip(lower=median_ct_hr)
            raised = (
                detail.loc[multi_ct, "Plant_Avg_HR_MMBtu_MWh"] > before + 1e-6
            ).sum()
            if raised:
                logger.info(
                    "Multi-tech CT HR correction: raised %d/%d CT(s) to "
                    "standalone median %.2f MMBtu/MWh",
                    int(raised),
                    int(multi_ct.sum()),
                    median_ct_hr,
                )

    # Each plant's tranche HR = Plant_Avg_HR × HR_Mult_<tranche>. We fill
    # missing plant heat rates with the per-group default and missing
    # multipliers with the group-typical value so the tranche arithmetic
    # is well-defined; tranches whose capacity is zero are skipped by
    # ``bins_to_fleet`` regardless of the resulting HR.
    plant_hr = [
        _fill_plant_hr(hr, grp)
        for hr, grp in zip(detail["Plant_Avg_HR_MMBtu_MWh"], detail["Plant_Group"])
    ]
    defaults_by_idx = [
        _DEFAULT_HR_MULT_BY_GROUP.get(grp, _DEFAULT_HR_MULT_BY_GROUP["CC_REGULAR"])
        for grp in detail["Plant_Group"]
    ]
    mult_columns = {
        "mr": "HR_Mult_Must_Run",
        "mc": "HR_Mult_Committed",
        "econ": "HR_Mult_Economic",
        "peak": "HR_Mult_Peaking",
    }
    bins = pd.DataFrame(
        {
            "Plant_Group": detail["Plant_Group"].astype(str),
            "ERCOT_Zone": detail["ERCOT_Zone"].astype(str),
            "Bin_Number": detail["Bin_Number"].astype(int),
            "Bin_Label": detail["Bin_Label"].astype(str),
            "Plant_Code": detail["Plant_Code"].astype(int),
            "Plant_Name": detail["Plant_Name"].astype(str),
            "Turbine_Class": detail["Turbine_Class"].astype(str),
            "capacity_mw": detail["Nameplate_MW"].astype(float),
            "hr_weighted": plant_hr,
            "pct_mr": detail["Pct_Must_Run"].astype(float),
            "pct_mc": detail["Pct_Committed"].astype(float),
            "pct_econ": detail["Pct_Economic"].astype(float),
            "pct_peak": detail["Pct_Peaking"].astype(float),
            "min_run": detail["Min_Run_Hours"].astype(int),
            "min_down": detail["Min_Down_Hours"].astype(int),
        }
    )
    for short, col in mult_columns.items():
        bins[f"hr_{short}"] = [
            hr * _fill_hr_multiplier(mult, defaults[short])
            for hr, mult, defaults in zip(plant_hr, detail[col], defaults_by_idx)
        ]
    bins["plant_count"] = 1
    bins["plant_codes"] = [[int(c)] for c in detail["Plant_Code"]]
    bins["fuel"] = fuel_series.values

    if year is not None:
        bins = _override_bin_class_from_eia923(bins, year)

    if capacity_reconcile_path is not None:
        bins = _reconcile_cc_capacity(bins, capacity_reconcile_path)

    bad = bins["pct_mr"] + bins["pct_mc"] + bins["pct_econ"] + bins["pct_peak"]
    if not (bad == 100).all():
        offending = bins.loc[bad != 100, "Plant_Name"].tolist()
        raise ValueError(
            f"CAMPD bin tranches must sum to 100%; offending plants: {offending}"
        )

    logger.info(
        "Loaded %d per-plant CAMPD bins from %s (%.1f GW)",
        len(bins),
        csv_path,
        bins["capacity_mw"].sum() / 1000.0,
    )
    _CAMPD_BINS_CACHE[cache_key] = bins
    return bins.copy()


# Default tranche split (% of nameplate) per group for the synthetic per-plant
# bins an ISO builds when it has no CAMPD bin sheet (see
# :func:`fleet_to_bins`): used only for plants absent from the CAMPD-derived
# thermal-tranche artifact (rarely-online units with no reliable observed
# floor). ``(must_run, committed, peaking)``; the economic band is the
# residual. Peakers carry no committed band; coal carries a baseload floor.
_DEFAULT_TRANCHE_PCT_BY_GROUP: dict[str, tuple[float, float, float]] = {
    "CC_REGULAR": (0.0, 45.0, 8.0),
    "CC_CHP": (0.0, 45.0, 8.0),  # must-run set to host steam in bins_to_fleet
    "CT_PEAKER": (0.0, 0.0, 7.0),
    "CT_CHP": (0.0, 30.0, 7.0),
    "ST_GAS": (0.0, 30.0, 15.0),
    "ST_CHP": (0.0, 30.0, 15.0),
    "COAL": (45.0, 5.0, 2.0),
}


def campd_attribution_selectors(config: object) -> tuple[bool, bool]:
    """Return the CAMPD artifact selector PAIR ``(per_unit, merit_guard)``.

    ONE accessor for both flags so a call site cannot pick up one without the
    other and silently mix two artifact vintages inside one LP (rule 19
    ``[R-ONE-MECH]``; nyiso-176 built the same guarantee for ``per_unit``
    alone, nyiso-177 extends it to the pair). ``merit_guard`` is forced False
    without ``per_unit``: the guarded companions exist only on the per-unit
    routing, so the flag has no meaning on its own.
    """
    per_unit = bool(getattr(config, "campd_per_unit_attribution", False))
    merit_guard = per_unit and bool(
        getattr(config, "campd_outage_merit_order_guard", False)
    )
    return per_unit, merit_guard


def thermal_tranche_csv_for_iso(
    iso: str, per_unit: bool = False, merit_guard: bool = False
) -> Path:
    """Return the CAMPD thermal-tranche artifact path for an ISO.

    The incumbent artifact is ``thermal_tranches_<ISO>.csv``, in which a mixed
    plant's FACILITY-SUMMED CAMPD net is attributed to "the group holding the
    most nameplate" (``derive_thermal_tranches._fleet_nameplate_and_group``) —
    a proxy that picks the wrong carrier wherever a plant's small bin does the
    running (nyiso-175 §4.4).

    ``per_unit`` (``ScenarioConfig.campd_per_unit_attribution``, GATED default
    False; nyiso-175b/176) selects the ``-perunit-`` companion that deriver
    writes under ``--per-unit-attribution``, in which each unit's gross is
    routed to the bin that CONTAINS it through the shared
    ``scripts/lib/campd_measured_classes`` crosswalk. A SEPARATE path, never an
    overwrite, so the off path is byte-inert; and the SAME
    ``ScenarioConfig`` field selects the matching unit-outage companion
    (:func:`market_sim.data.outages.unit_outage_csv_for_iso`), because a tranche
    row's online/committed statistics are computed over an outage-derated
    denominator and the two artifacts must not disagree about which bin a
    machine is in (rule 19 ``[R-ONE-MECH]``). Falls back to the incumbent
    artifact when the companion has not been derived for the ISO.

    ``merit_guard`` (``ScenarioConfig.campd_outage_merit_order_guard``, GATED
    default False; nyiso-177) selects the ``-perunitmerit-`` companion: the
    SAME per-unit attribution, re-derived against the merit-order-guarded
    unit-outage companion. It exists because a tranche row's ``online_hours``,
    ``committed_pct`` and ``median_cf`` are computed over an OUTAGE-DERATED
    denominator (``avail_cap = nameplate x avail_mult`` enters both the online
    test and the ``finite`` mask), so a solve reading the guarded outage
    extract against the UNGUARDED tranche artifact would carry two availability
    bases inside one LP. The same field therefore moves both artifacts, exactly
    as ``per_unit`` does (rule 19 ``[R-ONE-MECH]``); it has no meaning without
    ``per_unit`` and is ignored without it. Falls back the same way.
    """
    base = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if per_unit:
        if merit_guard:
            alt = base.with_name(f"thermal_tranches-perunitmerit-{iso.upper()}.csv")
            if alt.exists():
                return alt
        alt = base.with_name(f"thermal_tranches-perunit-{iso.upper()}.csv")
        if alt.exists():
            return alt
    return base


@lru_cache(maxsize=16)
def thermal_tranche_overrides(
    iso: str,
    coal_online_pmin: bool = False,
    per_unit: bool = False,
    merit_guard: bool = False,
) -> dict[tuple[int, str], tuple[float, float]]:
    """Return ``{(plant_code, group): (committed_pct, mustrun_pct)}`` for an ISO.

    Loads the per-plant CAMPD-derived committed and must-run tranche shares
    from ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (written by
    ``scripts/data/derive_thermal_tranches.py``). Empty when the ISO has no
    artifact, so the caller falls back to the group default. This is the
    general, ISO-agnostic replacement for the hardcoded ERCOT
    ``CC_REGULAR_COMMITTED_PCT_BY_PLANT`` / ``COAL_MUSTRUN_BY_PLANT`` maps.

    When ``coal_online_pmin`` is set (``ScenarioConfig.coal_mustrun_online_pmin``,
    rebuild step 2) a **coal** row's must-run is taken from the artifact's
    ``mustrun_online_pct`` column — the measured online-net-MW synchronization
    Pmin (~20-30% of nameplate) — instead of the all-hours available-CF
    ``mustrun_pct`` (which reads ~2x high for an always-online unit). Coal rows
    in an artifact that predates the column (or with a blank/NaN value) keep
    ``mustrun_pct``; non-coal rows are unaffected.
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    has_online = "mustrun_online_pct" in df.columns
    out: dict[tuple[int, str], tuple[float, float]] = {}
    for r in df.itertuples(index=False):
        if str(getattr(r, "status", "ok")) != "ok":
            continue
        mustrun = float(r.mustrun_pct)
        if coal_online_pmin and has_online and str(r.plant_group) == "COAL":
            online_v = getattr(r, "mustrun_online_pct", float("nan"))
            if online_v == online_v:  # not NaN
                mustrun = float(online_v)
        out[(int(r.plant_code), str(r.plant_group))] = (
            float(r.committed_pct),
            mustrun,
        )
    return out


@lru_cache(maxsize=8)
def thermal_tranche_peaking(
    iso: str, per_unit: bool = False, merit_guard: bool = False
) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, group): peaking_pct}`` for an ISO's CC plants.

    The CAMPD-derived duct-firing / scarcity share from
    ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (``peaking_pct``, written
    by ``scripts/data/derive_thermal_tranches.py`` for CC_REGULAR / CC_CHP): the
    share of the plant's demonstrated sustained maximum it clears in fewer
    than 5% of its online hours. Empty when the ISO has no artifact or it
    predates the column (ERCOT has none — its own per-plant binning path
    never produced one). Applied per plant in :func:`bins_to_fleet` under
    ``config.cc_peaking_per_plant`` (CAISO/PJM/NYISO/NEISO/MISO default) —
    supersedes the offer curve's class-wide ``pct_peaking``. (The prior
    ERCOT hand-set ``CC_REGULAR_PEAKING_PCT_BY_PLANT`` four-plant override
    was deleted 2026-07, rule 26/G-26/C-12: dead in every current keeper.
    ERCOT's default — and every current ERCOT keeper — instead runs
    ``cc_peaking_per_plant=False`` + ``cc_duct_peaking=True``: the measured
    EIA-860 mechanism below, generalized to every ERCOT CC plant rather than
    the four the deleted dict named, since ERCOT has no thermal-tranche
    artifact of its own to fall back to.)
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "peaking_pct" not in df.columns:
        return {}
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        if str(getattr(r, "status", "ok")) != "ok" or pd.isna(r.peaking_pct):
            continue
        out[(int(r.plant_code), str(r.plant_group))] = float(r.peaking_pct)
    return out


@lru_cache(maxsize=8)
def coal_min_config(iso: str) -> dict[int, float]:
    """Return ``{plant_code: min_config_mw}`` for an ISO's coal plants.

    The MINIMUM ONLINE CONFIGURATION — the least MW a coal plant can hold with
    at least one unit synchronised, ``min over units u of MinLoad_u`` from the
    EIA-860 registered ``Minimum Load (MW)`` — read from
    ``data/raw/_processed-legacy/coal_min_config_<ISO>.csv``, written by
    ``scripts/data/derive_eia860_coal_min_config.py``.

    This is unit-grain commitment's LOWER ENVELOPE expressed on the plant grain
    the LP actually carries: where a plant's exact unit-commitment feasible set
    is connected (9 of 10 ERCOT coal plants, 97.8 % of coal capacity) the
    plant-grain interval ``[min_config_mw, cap]`` represents it with zero error,
    so no commitment state and no integrality are needed. Consumed by
    ``config.ercot_coal_min_config_floor`` (lane ercot128-unit-grain).

    Keyed on plant code alone — a plant has ONE minimum online configuration,
    and the consuming site additionally gates on ``fuel == "coal"`` so a mixed
    plant's gas-steam rows (W A Parish 3470) never pick the floor up. Empty when
    the ISO has no artifact; rows whose ``status`` is not ``ok`` are skipped.
    """
    path = PROCESSED_DIR / f"coal_min_config_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "min_config_mw" not in df.columns:
        return {}
    out: dict[int, float] = {}
    for r in df.itertuples(index=False):
        if str(getattr(r, "status", "ok")) != "ok" or pd.isna(r.min_config_mw):
            continue
        mw = float(r.min_config_mw)
        if mw > 0.0:
            out[int(r.plant_code)] = mw
    return out


@lru_cache(maxsize=8)
def thermal_tranche_online_frac(
    iso: str, per_unit: bool = False, merit_guard: bool = False
) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, group): online_frac}`` for an ISO's gas plants.

    The CEMS-measured synchronization fraction from
    ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (``online_frac``,
    written by ``scripts/data/derive_thermal_tranches.py`` for the
    ``_ONLINE_FRAC_GROUPS``: COAL plus the merchant gas committed groups
    CC_REGULAR / CT_PEAKER): the share of the pooled window the plant has any
    unit synchronized (net MW > 1% of nameplate). Consumed by the per-plant
    gas local-reliability commitment floor (``config.cc_mustrun_per_plant``)
    to size each plant's committed window — the top ``online_frac`` fraction
    of hours ranked by system load in which its committed tranche is forced
    on. Empty when the ISO has no artifact or it predates the gas
    ``online_frac`` extension (coal rows are returned too, but their forcing
    rides ``coal_sync_online_frac``, not this map). Rows with a blank/NaN
    fraction are absent (no floor).
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "online_frac" not in df.columns:
        return {}
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        v = getattr(r, "online_frac", float("nan"))
        try:
            frac = float(v)
        except (TypeError, ValueError):
            continue
        if str(getattr(r, "status", "ok")) != "ok" or not frac == frac:
            continue
        out[(int(r.plant_code), str(r.plant_group))] = min(1.0, max(0.0, frac))
    return out


# Arm-over-gap guard table (xiso-6). One row per ScenarioConfig gate that reads
# a per-plant column of ``thermal_tranches_<ISO>.csv``:
# ``(gate, candidate columns, plant groups the mechanism engages on)``.
# Candidate columns are tried in order and the first present is the one the
# runtime loader reads (the two-entry ``chp_steam_floor_p25`` row mirrors
# :func:`thermal_tranche_chp_steam_level`'s pre-WP-3 ``p25_allhr_cf`` fallback).
# The target groups are EXACTLY the groups the consumer gates on — e.g. the
# ``online_frac`` gates never list a CHP group, so the by-design CHP blanks
# ("their floor is the steam host", rule 19 [R-ONE-MECH]) can never be flagged.
# ``coal_sync_srmc_tranche`` engages only when ``coal_mustrun_online_pmin`` is
# also armed (mirrored from the assembly consumer), handled in the guard body.
_TRANCHE_GATE_COLUMNS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("cc_mustrun_per_plant", ("online_frac",), ("CC_REGULAR",)),
    ("st_gas_mustrun_per_plant", ("online_frac",), ("ST_GAS",)),
    ("coal_sync_srmc_tranche", ("online_frac",), ("COAL",)),
    ("coal_mustrun_online_pmin", ("mustrun_online_pct",), ("COAL",)),
    ("st_gas_mustrun_p25_level", ("p25_cf",), ("ST_GAS",)),
    ("cc_peaking_per_plant", ("peaking_pct",), ("CC_REGULAR", "CC_CHP")),
    (
        "chp_steam_floor_p25",
        ("steam_level_cf", "p25_allhr_cf"),
        ("CC_CHP", "CT_CHP", "ST_CHP"),
    ),
)


def assert_thermal_tranche_coverage(iso: str, config: ScenarioConfig) -> None:
    """Fail loudly when an ARMED tranche gate reads a vintage gap (xiso-6).

    The per-plant tranche loaders above are deliberately self-targeting: a row
    with a blank cell is silently skipped (no floor), so a mechanism armed at
    an ISO whose committed artifact predates the column's emitting vintage
    engages on NOTHING and reads as inert on the merits — a false negative the
    matrix would then mint as a DO-NOT-REDO ``I`` verdict (rule 26
    [R-MECH-MATRIX]). That is the trap
    ``results/calibration/FINDING-xiso5-thermal-tranche-coverage-2026-08-04.md``
    §4.3 documents (166 ``status="ok"`` rows blank in groups a HEAD
    re-derivation would populate, across CAISO/PJM/NYISO/NEISO).

    For every gate in :data:`_TRANCHE_GATE_COLUMNS` the running ``config``
    arms, this preflight reads the ISO's artifact bytes directly (never the
    cached loaders) and raises ``ValueError`` when, in any target group with
    at least one ``status="ok"`` row, the consumed column is absent from the
    file or blank in any of those rows — at HEAD the emit path cannot produce
    such a blank, so it is an artifact-vintage defect, never a measurement.
    Scoped strictly to the arm-over-a-gap case: unarmed gates are never
    checked, groups with no ``ok`` rows are skipped (a class the CEMS extracts
    cannot see is the self-targeting design, not a gap), and the by-design
    blanks (CHP ``online_frac``, non-CC ``peaking_pct``, …) are unreachable
    because the target groups mirror each consumer's own group gate.

    Measured a no-op at all six current keepers (every armed gate sits over a
    fully populated column — xiso-5 §4.3(i), re-verified in
    ``tests/unit/data/test_thermal_tranche_guard.py``); the remedy for a hit
    is that ISO's own pre-registered keeper-grade re-derivation (rule 23
    [R-FROZEN-DERIVE]), never a silent skip. Rule-24 precedent: armed without
    the resolved map is a hard error, never a silent fallback.
    """
    armed: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
    for gate, columns, groups in _TRANCHE_GATE_COLUMNS:
        if not getattr(config, gate, False):
            continue
        if gate == "coal_sync_srmc_tranche" and not getattr(
            config, "coal_mustrun_online_pmin", False
        ):
            # The sync split engages only under the online-Pmin sizing
            # (assembly consumer's own conjunction); armed alone it is inert
            # by construction, not an arm-over-a-gap.
            continue
        armed.append((gate, columns, groups))
    if not armed:
        return
    path = thermal_tranche_csv_for_iso(iso, *campd_attribution_selectors(config))
    if not path.exists():
        raise ValueError(
            f"thermal-tranche coverage guard: ISO {iso!r} arms "
            f"{sorted(g for g, _, _ in armed)} but has no per-plant tranche "
            f"artifact at {path}. The mechanism(s) would engage on NOTHING "
            "and read as inert on the merits (FINDING-xiso5 §4.3). ERCOT has "
            "no artifact BY DESIGN (custom-bin-assignments.csv + hardcoded "
            "fleet maps) and cannot arm these per-plant artifact gates; any "
            "other ISO needs its artifact derived in its own lane first."
        )
    df = pd.read_csv(path)
    ok = df[df["status"] == "ok"] if "status" in df.columns else df
    problems: list[str] = []
    for gate, columns, groups in armed:
        col = next((c for c in columns if c in df.columns), None)
        for group in groups:
            sub = ok[ok["plant_group"] == group]
            if sub.empty:
                continue
            if col is None:
                problems.append(
                    f"  - {gate} reads {'/'.join(columns)!r} for {group}: "
                    f"COLUMN ABSENT ({len(sub)} status='ok' rows would be "
                    "silently skipped)"
                )
                continue
            filled = sub[col].notna() & (sub[col].astype(str).str.strip() != "")
            blank = int((~filled).sum())
            if blank:
                problems.append(
                    f"  - {gate} reads {col!r} for {group}: {blank} of "
                    f"{len(sub)} status='ok' rows are BLANK and would be "
                    "silently skipped"
                )
    if problems:
        raise ValueError(
            f"thermal-tranche coverage guard: ISO {iso!r} arms mechanism "
            f"gate(s) over vintage gaps in {path.name}:\n"
            + "\n".join(problems)
            + "\nAt HEAD the deriver cannot emit a blank status='ok' row in "
            "an emitting group, so these are artifact-VINTAGE gaps "
            "(FINDING-xiso5 §3; see the artifact's .meta.json sidecar). The "
            "mechanism would engage on nothing and read as inert on the "
            "merits. Remedy: this ISO's own pre-registered keeper-grade "
            "re-derivation under rule 23 [R-FROZEN-DERIVE] — never a silent "
            "skip, never another ISO's artifact (rule 25 [R-ISO-SCOPE])."
        )


def thermal_tranche_p25_level(
    iso: str, per_unit: bool = False, merit_guard: bool = False
) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, group): p25_level_mw}`` for an ISO's gas plants.

    The measured 25th-percentile-of-online available-CF from
    ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (``p25_cf``, a
    percent, written by the SAME frozen ``scripts/data/derive_thermal_tranches.py``
    estimator that produces ``committed_pct`` = P5-of-online and ``online_frac``
    — rule 23, no deriver touch) times the plant's ``nameplate_mw``, i.e. the
    plant's 25th-percentile dispatch level when synchronized. Because ``p25_cf``
    is a fraction of *available* capacity (``series / (nameplate x avail_mult)``
    in the deriver), ``p25_cf x nameplate`` reconstructs the measured p25 output
    level; the runtime ``availability`` derate then enters only through the
    per-tranche ``pmax x availability`` clip in the application block, matching
    the committed floor's "clipped to pmax*availability as today". Consumed by
    the per-plant ST_GAS local-reliability commitment floor when
    ``config.st_gas_mustrun_p25_level`` is armed (miso-67): the p25 level
    REPLACES the committed-tranche level (P5-of-online = LSL) for gate-armed
    ST_GAS plants, distributed cheapest-first across the plant's tranches. Empty
    when the ISO has no artifact or it predates the ``p25_cf`` column. Rows with
    a blank/NaN ``p25_cf`` or ``nameplate_mw`` are absent (no floor).
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "p25_cf" not in df.columns or "nameplate_mw" not in df.columns:
        return {}
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        try:
            p25 = float(getattr(r, "p25_cf", float("nan")))
            nameplate = float(getattr(r, "nameplate_mw", float("nan")))
        except (TypeError, ValueError):
            continue
        if str(getattr(r, "status", "ok")) != "ok":
            continue
        if not (p25 == p25) or not (nameplate == nameplate):
            continue  # NaN guard (blank cell)
        # Clamp to nameplate. `p25_cf` inherits the deriver's
        # `np.clip(acf, 0.0, 1.5)` CEMS-noise guard, so a unit whose CEMS gross
        # exceeds its EIA nameplate can carry p25_cf up to 150 % — and every
        # committed artifact has such rows (MISO 17, NEISO 3, NYISO 2, PJM 3).
        # Unclamped, that asks for a commitment floor ABOVE nameplate: the
        # per-hour `min(target, pmax x availability)` clip stops it crashing but
        # pins the plant flat at full available capacity across its whole
        # window. `committed_pct` / `mustrun_pct` have carried a ceiling since
        # they were derived (`_COMMITTED_CAP` 0.70 / `_MUSTRUN_CAP` 0.60); this
        # is the same guard for the same statistic family, at the physical
        # ceiling rather than a share cap. Clamped here as well as in the
        # deriver (`_P25_CAP`) so a STALE artifact — every committed one today —
        # cannot inject an impossible floor without a re-derivation.
        # Measured inert on every live keeper when it landed (nyiso-106).
        level = min(max(0.0, p25 / 100.0), 1.0) * max(0.0, nameplate)
        if level > 0.0:
            out[(int(r.plant_code), str(r.plant_group))] = level
    return out


@lru_cache(maxsize=8)
def thermal_tranche_online_frac_by_year(
    iso: str,
) -> dict[tuple[int, str, int], float]:
    """Return ``{(plant_code, group, year): online_frac}`` — the PER-YEAR window.

    The same CEMS synchronization fraction :func:`thermal_tranche_online_frac`
    returns, at the grain the runtime actually applies it: one value per SOLVE
    YEAR instead of one value per plant pooled over the whole derive window.
    Read from ``data/raw/_processed-legacy/thermal_tranches_online_frac_by_year_<ISO>.csv``
    (``scripts/data/derive_thermal_tranche_online_frac_by_year.py``, which
    IMPORTS the frozen estimator rather than restating it — summing that file's
    ``sync_hours`` / ``total_hours`` over the pooled years reproduces the pooled
    column exactly).

    The pooled column is a multi-year average applied as a SINGLE year's
    commitment window, so a plant whose synchronization share moves across the
    window is over-committed in its light years and under-committed in its heavy
    ones. MISO plant 1402 (Little Gypsy) is the measured case: pooled 0.508
    against 0.251 / 0.615 / 0.658 — a ~2.3x 2023 over-commitment that the C8 D-4
    per-unit conduct rider convicts (rule 17 ``[R-FLOOR-WINDOW]``: a floor
    binding in hours its own driver evidence says the unit is offline).

    Consumed under ``config.mustrun_online_frac_per_year`` (BACKCAST only — the
    same-year meter has no forward analogue; a forecast year keeps the pooled
    multi-year fraction, which is the estimator's own forward form). Empty when
    the ISO has no per-year artifact, which leaves the pooled behaviour
    byte-identical. Rows with a blank/NaN fraction are absent.
    """
    path = PROCESSED_DIR / f"thermal_tranches_online_frac_by_year_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "online_frac" not in df.columns or "year" not in df.columns:
        return {}
    out: dict[tuple[int, str, int], float] = {}
    for r in df.itertuples(index=False):
        try:
            frac = float(getattr(r, "online_frac", float("nan")))
            year = int(getattr(r, "year"))
        except (TypeError, ValueError):
            continue
        if not frac == frac:  # NaN guard (blank cell)
            continue
        out[(int(r.plant_code), str(r.plant_group), year)] = min(1.0, max(0.0, frac))
    return out


@lru_cache(maxsize=8)
def thermal_tranche_p25_measured_level(iso: str) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, group): p25_level_mw}`` measured DIRECTLY in MW.

    The same 25th-percentile-of-online statistic :func:`thermal_tranche_p25_level`
    reconstructs from ``p25_cf``, taken over the plant's online net-MW sample
    instead — read from
    ``data/raw/_processed-legacy/thermal_tranches_p25_level_mw_<ISO>.csv``
    (``scripts/data/derive_thermal_tranche_p25_level_mw.py``, which imports the
    frozen deriver's online mask, net construction, derate source and pooled
    window).

    Why the MW basis exists: ``p25_cf`` is a percentile of ``net_MW /
    (nameplate x avail_mult)`` — a fraction of AVAILABLE capacity — and the
    reconstruction ``p25_cf x nameplate`` drops the ``avail_mult`` it was divided
    by, so a plant carrying a deep availability derate gets a floor ``1 /
    avail_mult`` too high. MISO plant 1122 (Ames) is the measured case: ``p25_cf``
    0.674 x 108.7 MW nameplate = 73.3 MW against a measured p25-of-online of
    33 MW, and 0.674 x its ~49 MW available base = 33.0 MW exactly. The runtime
    then held the plant ~90 % floor-forced at +65-93 % of its own metered energy.
    Measuring the level in MW removes the reconstruction, so no basis can be
    dropped (rule 14 ``[R-ACCURATE]``).

    Consumed under ``config.st_gas_mustrun_p25_measured_level``, which REPLACES
    the level source — it never stacks a second floor (rule 19 ``[R-ONE-MECH]``).
    Empty when the ISO has no artifact, leaving today's behaviour byte-identical.
    """
    path = PROCESSED_DIR / f"thermal_tranches_p25_level_mw_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "p25_level_mw" not in df.columns:
        return {}
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        try:
            level = float(getattr(r, "p25_level_mw", float("nan")))
        except (TypeError, ValueError):
            continue
        if not level == level or level <= 0.0:  # NaN / no floor
            continue
        out[(int(r.plant_code), str(r.plant_group))] = level
    return out


@lru_cache(maxsize=8)
def thermal_tranche_oom_level(iso: str) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, group): oom_level_mw}`` — the OUT-OF-MERIT level.

    The same measured-MW percentile family as
    :func:`thermal_tranche_p25_measured_level`, taken over a RE-CONDITIONED
    sample: the plant's online hours **in which the class's economic signal
    says off** (the miso-197 W3b set — hours the measured CC_REGULAR fleet ran
    below 0.90 of its own p99.5, i.e. cheaper CC capability was demonstrably
    idle), instead of all hours the plant happened to be on. Read from
    ``data/raw/_processed-legacy/thermal_tranches_oom_level_mw_<ISO>.csv``
    (``scripts/data/derive_thermal_tranche_oom_level_mw.py``, which imports the
    frozen deriver's online mask, net construction, derate source, nameplate
    clamp and pooled window rather than restating them — rule 23
    ``[R-FROZEN-DERIVE]``).

    Why the re-conditioned sample exists: the miso-198 census partitioned the
    ST_GAS gap between the measured out-of-merit conduct and the keeper's own
    armed floor EXACTLY into population / window / LEVEL and found LEVEL
    dominant in every year (0.640 / 0.699 / 0.665 of a 7.85 / 10.62 / 8.91 TWh
    gap, 3 of 3 over the 0.45 line; the population channel did not clear the
    census's operating test and the window channel never reached dominance).
    The incumbent statistic is a low percentile of "every hour the plant was
    on", which measures the plant's *operating range*; the phenomenon being
    represented is that these VLR/self-committed steamers **hold their normal
    load in the hours merit says shut down**, and the statistic that measures
    THAT conditions on those hours. The percentile family and the floor's
    membership, window, mechanism id and ``pmax x availability`` clip are all
    unchanged — only the sample the percentile is taken over.

    Consumed under ``config.st_gas_mustrun_oom_level``, which REPLACES the
    level source and never stacks a second floor (rule 19 ``[R-ONE-MECH]``).
    Empty when the ISO has no artifact, leaving today's behaviour
    byte-identical.
    """
    path = PROCESSED_DIR / f"thermal_tranches_oom_level_mw_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "oom_level_mw" not in df.columns:
        return {}
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        try:
            level = float(getattr(r, "oom_level_mw", float("nan")))
        except (TypeError, ValueError):
            continue
        if not level == level or level <= 0.0:  # NaN / no floor
            continue
        out[(int(r.plant_code), str(r.plant_group))] = level
    return out


@lru_cache(maxsize=8)
def coal_prb_committed_split_night(iso: str) -> dict[int, float]:
    """Return ``{plant_code: night_p50}`` from the PRB committed-split artifact.

    The measured within-run NIGHT loading level (p50 of plant load / HSL over
    ONLINE hours h0-5, pooled 2023-2025, WP-3 loading-when-on construction)
    from ``data/raw/_processed-legacy/coal_prb_committed_split_<ISO>.csv``,
    written by the frozen ``scripts/data/derive_prb_committed_split.py``
    (rule 23 [R-FROZEN-DERIVE]: re-derives only on CAMPD source updates).
    Consumed by ``bins_to_fleet`` when ``config.coal_prb_committed_split`` is
    armed (miso-112, PREREG-miso112-prb-committed-split-2026-07-31.md §3): a
    regulated PRB plant's ``_committed`` band splits at this level into a
    hold-through slice (keeps the take-or-pay discount) and a full-cost
    cycling slice (``_commitcyc``). Both REG and MER legs are returned; the
    consumer gates on the regulated scope set. Empty when the ISO has no
    artifact — the artifact is per-ISO by construction, so the mechanism
    self-scopes (rule 25 [R-ISO-SCOPE]).
    """
    path = PROCESSED_DIR / f"coal_prb_committed_split_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out: dict[int, float] = {}
    for r in df.itertuples(index=False):
        night = float(getattr(r, "night_p50", float("nan")))
        if night == night:  # NaN guard
            out[int(r.plant_code)] = night
    return out


def thermal_tranche_chp_steam_level(
    iso: str, per_unit: bool = False, merit_guard: bool = False
) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, group): steam_level_cf_pct}`` for an ISO's CHP cogens.

    The measured multi-year steam-host operating LEVEL (percent of nameplate)
    from ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv``
    (``steam_level_cf``, WP-3 rule-23 re-derivation, owner-ruled 2026-07-19 —
    `docs/handoffs/caiso-wp3-ctchp-steam-floor-ask-2026-07-18.md`). Two lenses
    emit the one statistic family:

    - ``status == "ok"`` (CAMPD-visible): the loading-when-on construction —
      on-hour frequency x p50 available-CF conditional on online, same sample
      and masks as the p2 ``chp_pmin_cf`` floor. Replaces the pre-WP-3
      p25-of-all-hours statistic, which mixed economic/host-driven offline
      zeros into the level and under-measured a high-baseload host that takes
      offline stretches (FINDING-caiso95 §5: measured >=70 % loading in
      79-88 % of on-hours vs the p25's 12-14 % trickle).
    - ``status == "eia923_cf"`` (CEMS-invisible, below the Part 75 reporting
      threshold): the pooled EIA-923 delivery-implied level — measured class
      net generation over nameplate-hours of the reported window (WP-3 scope
      (b); these plants never enter the CAMPD sample, so no CEMS percentile
      can reach them).

    Both self-target with no threshold parameter (a cycler's on-frequency or
    delivered energy collapses its level). Consumed by the CHP grid
    steam-floor level swap when ``config.chp_steam_floor_p25`` is armed (field
    name kept for run-config lineage; same formula
    ``pmin_cf x (1 - btm_share)`` and the same MECH_CHP_STEAM attribution as
    the p2 floor — a level source swap, rule 19). Rows with a blank/NaN level
    are absent; explicit 0.0 rows are carried (measured-and-collapsed, still
    no floor). Pre-WP-3 artifacts that only carry ``p25_allhr_cf`` fall back
    to it (their committed derivation, rule 23 — re-derive moves with the
    artifact, not the loader). Empty when the ISO has no artifact or it
    predates both columns.
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    col = "steam_level_cf" if "steam_level_cf" in df.columns else "p25_allhr_cf"
    if col not in df.columns:
        return {}
    # The eia923_cf lens exists only in the WP-3 column; pre-WP-3 artifacts
    # carry a level for CAMPD-visible ("ok") rows only.
    statuses = {"ok", "eia923_cf"} if col == "steam_level_cf" else {"ok"}
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        try:
            level = float(getattr(r, col, float("nan")))
        except (TypeError, ValueError):
            continue
        if str(getattr(r, "status", "ok")) not in statuses:
            continue
        if not (level == level):
            continue  # NaN guard (blank cell — no measured level)
        out[(int(r.plant_code), str(r.plant_group))] = max(0.0, level)
    return out


def cc_duct_peaking_pct(row_scoped: bool = False) -> dict[int, float]:
    """Vintage-keyed shim over :func:`_cc_duct_peaking_pct_cached`.

    See that function for the contract. The active EIA-860 directory enters the
    cache key here because this map sets the CC_REGULAR / CC_CHP **peak offer
    band** and is read off a vintage-dependent sheet: under
    ``eia860_vintage_tracks_solve_year`` a span run re-points
    :data:`~market_sim.config.paths._ACTIVE_EIA_860_DIR` every year, and a
    vintage-blind key served year 1's bands to years 2+ (rule 14
    ``[R-ACCURATE]``; ``docs/handoffs/FINDING-spp-37-order-sensitivity-2026-09-12.md``,
    repaired by SPP-38).
    """
    return _cc_duct_peaking_pct_cached(str(active_eia860_dir()), row_scoped)


@lru_cache(maxsize=2)
def _cc_duct_peaking_pct_cached(
    eia860_dir: str, row_scoped: bool = False
) -> dict[int, float]:
    """Return ``{plant_code: peaking_pct}`` for every EIA-860 CC plant.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the :func:`cc_duct_peaking_pct` shim,
    which supplies the active vintage.

    Built from the raw EIA-860 Generator_Y Operable sheet parquet
    (``eia860_generator_operable.parquet``): a plant is duct-fired when any
    of its combined-cycle generators carries the "Duct Burners" = Y flag
    (reported on the steam/CA rows). Duct-fired plants get the
    nameplate-vs-net-summer capability gap as their peaking share,
    ``100 x max(0, nameplate - net_summer) / nameplate`` summed over the
    plant's CC generators; non-duct CC plants get 0.0 — they have no
    duct-firing increment, so a class-uniform peak band hands them phantom
    scarcity capacity. (The EIA-860 release carries no separate duct-burner
    MW increment, so the capability gap is the proxy; for non-duct plants
    that same gap is ambient derate, already modeled by
    ``_SUMMER_CLASS_DERATE``.) Applied per plant under
    ``config.cc_duct_peaking``, superseding the offer curve's class-wide
    ``pct_peaking``. Plants absent from the sheet are absent from the map
    (callers keep their class default).

    ``row_scoped`` (``ScenarioConfig.cc_duct_peaking_row_scoped``, nyiso-198)
    takes the numerator over the rows the filing FLAGS instead of over every
    combined-cycle row of the plant. A duct burner fires into the HRSG and
    raises the STEAM turbine's output, and EIA-860 reports the attribute at
    that grain: in the whole operable CC population the column reads Y/N only
    on CA and CS rows and ``X`` (not applicable) on **every** CT row, so a CT
    row's gap is site/ambient derate by construction and the plant-level sum
    books it as duct capability. The denominator (plant nameplate), the clip,
    the duct-fired plant selection rule and every consumer are unchanged, so
    the two forms differ only in which rows enter the numerator. Off by
    default and byte-inert while off.

    Args:
        row_scoped: Take the capability gap over the ``Duct Burners == Y``
            rows alone rather than over all of the plant's CC rows.

    Returns:
        ``{plant_code: peaking_pct}`` for every EIA-860 combined-cycle plant.
    """
    path = Path(eia860_dir) / "eia860_generator_operable.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Technology",
            "Duct Burners",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
        ],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    if cc.empty:
        return {}
    cc["plant_code"] = cc["Plant Code"].astype(float).astype(int)
    cc["np"] = pd.to_numeric(cc["Nameplate Capacity (MW)"], errors="coerce")
    cc["ns"] = pd.to_numeric(cc["Summer Capacity (MW)"], errors="coerce")
    out: dict[int, float] = {}
    for code, grp in cc.groupby("plant_code"):
        np_sum = float(grp["np"].sum())
        if np_sum <= 0.0:
            continue
        flagged = grp["Duct Burners"].astype(str).str.strip() == "Y"
        if flagged.any():
            # The gap is taken over the rows that can carry a duct burner
            # (row_scoped) or over every CC row of the plant (the prior form).
            src = grp[flagged] if row_scoped else grp
            gap = float(src["np"].sum()) - float(src["ns"].sum())
            out[int(code)] = round(100.0 * max(0.0, gap) / np_sum, 1)
        else:
            out[int(code)] = 0.0
    return out


def cc_summer_capacity() -> dict[int, tuple[float, float]]:
    """Vintage-keyed shim over :func:`_cc_summer_capacity_cached` (SPP-38).

    See that function for the contract; the active EIA-860 directory enters the
    cache key so a span run that moves the vintage between years cannot serve
    year 1's capabilities to years 2+ (rule 14 ``[R-ACCURATE]``).
    """
    return _cc_summer_capacity_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _cc_summer_capacity_cached(eia860_dir: str) -> dict[int, tuple[float, float]]:
    """Return ``{plant_code: (nameplate_mw, net_summer_mw)}`` for every CC plant.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the :func:`cc_summer_capacity` shim,
    which supplies the active vintage.

    Summed over each plant's combined-cycle generators from the EIA-860
    Generator_Y Operable sheet. Consumed under
    ``config.cc_nameplate_summer_derate`` to (a) raise a CC plant's LP capacity
    from its net-summer rating to full nameplate and (b) derive the per-plant
    MEASURED summer derate ``net_summer / nameplate`` applied in the summer
    months — the correct seasonal capacity shape (full nameplate in winter,
    ambient-derated to net-summer in summer). Plants absent from the sheet are
    absent from the map (callers keep net-summer / the flat class derate).
    """
    path = Path(eia860_dir) / "eia860_generator_operable.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Technology",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
        ],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    if cc.empty:
        return {}
    cc["plant_code"] = cc["Plant Code"].astype(float).astype(int)
    cc["np"] = pd.to_numeric(cc["Nameplate Capacity (MW)"], errors="coerce")
    cc["ns"] = pd.to_numeric(cc["Summer Capacity (MW)"], errors="coerce")
    out: dict[int, tuple[float, float]] = {}
    for code, grp in cc.groupby("plant_code"):
        np_sum = float(grp["np"].sum())
        ns_sum = float(grp["ns"].sum())
        # Consistency guard (EIA-860 schema: summer capability <= nameplate).
        # A summed net-summer above the summed nameplate is component/total
        # double-filing; clamp it to nameplate so the derived summer-derate
        # ratio and any nameplate rescale never carry the phantom. The
        # derate ratio min(1, ns/np) already clamped these plants to 1.0, so
        # this is inert to that consumer but corrects the returned figure for
        # every other reader (diagnosis §3b, probe block 3).
        ns_sum = min(ns_sum, np_sum)
        if np_sum > 0.0 and ns_sum > 0.0:
            out[int(code)] = (np_sum, ns_sum)
    return out


def summer_basis_measured_plants(iso: str) -> frozenset[int]:
    """Plant codes whose LP capacity already IS a measured summer capability.

    Consumed under ``config.summer_derate_basis_aware`` (miso-148) to decide,
    per plant, whether the flat class ambient haircut
    ``_SUMMER_CLASS_DERATE`` may be applied on top of the carried capacity.

    **Why the question is per-plant.** The flat derate represents the
    *nameplate -> summer-peak ambient* loss. On the per-plant EIA-860 path
    (``plant_level_fleet``) a generator's ``pmax`` is the published NET SUMMER
    rating (``eia860.py`` ``pmax = net_summer_capacity_mw``), which already
    embeds that loss — so applying the flat derate again is a double count
    (miso-141 measured it: the flat 10 % / 12.5 % against a measured
    nameplate->net-summer gap of 11.40 / 14.34 / 16.35 / 15.25 % by class).
    But NOT every plant is carried on that basis: a plant filing a summed
    net-summer ABOVE its summed nameplate (EIA-860's schema forbids it —
    component/total double-filing) is clipped by
    :func:`~market_sim.data.fleet.eia860._reconcile_cc_pmax_to_nameplate` to
    ``max(nameplate, demonstrated_peak)``, i.e. onto a NAMEPLATE-like basis,
    where the ambient derate is legitimate and must be kept.

    The predicate is therefore: **present in EIA-860 Operable, and NOT clipped
    by the CC guard** — read from the guard's own recorded decision
    (:func:`~market_sim.data.fleet.eia860.cc_pmax_reconciled_plants`), never
    re-derived from the raw sheet. That distinction is load-bearing, not
    stylistic: the plant-total-on-one-row pattern hides behind NaN component
    rows the loader nameplate-fills, so a raw ``net_summer`` vs ``nameplate``
    audit does NOT see the corrupt plants (55380 and 55467 both read "clean" on
    the raw sheet while the loader clips them by 1,028.6 and 353.3 MW). Plants
    absent from EIA-860 are absent from the set, so callers KEEP the flat
    derate — absence of evidence for a measured basis is not evidence of one.

    Class-agnostic by construction (all technologies, not just combined cycle),
    because the flat derate covers CC_REGULAR, CC_CHP, CT_PEAKER and CT_CHP and
    a repair reaching only the CC half would leave two classes competing on the
    same margin with inconsistent capacity bases (miso-141 §9/§11.2(a)).

    Rule 13/14 basis: derived entirely from published EIA-860 ratings and the
    ISO's committed CAMPD demonstrated-peak table — it regenerates for any
    forward vintage and responds to re-rates. No residual is consulted.

    Deliberately NOT ``lru_cache``d: both inputs are vintage-dependent
    (``active_eia860_dir()`` is re-pointed per solve year by
    ``set_eia860_vintage``, and the clip set is rewritten on every fleet load),
    so a cache keyed on ``iso`` alone would freeze year 1's answer onto year 2.
    """
    from market_sim.data.fleet.eia860 import cc_pmax_reconciled_plants

    path = active_eia860_dir() / "eia860_generator_operable.parquet"
    if not path.exists():
        return frozenset()
    df = pd.read_parquet(path, columns=["Plant Code", "Summer Capacity (MW)"])
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()].copy()
    if df.empty:
        return frozenset()
    df["plant_code"] = df["Plant Code"].astype(float).astype(int)
    df["ns"] = pd.to_numeric(df["Summer Capacity (MW)"], errors="coerce")
    rated = df.groupby("plant_code")["ns"].sum()
    clipped = cc_pmax_reconciled_plants(iso)
    return frozenset(
        int(code)
        for code, ns_sum in rated.items()
        if float(ns_sum) > 0.0 and int(code) not in clipped
    )


def cc_summer_derate_ratio(plant_code: int) -> float | None:
    """Return a CC plant's measured summer availability multiplier.

    ``net_summer / nameplate`` from :func:`cc_summer_capacity`, clamped to
    ``(0, 1]`` (a plant whose summer rating meets or exceeds nameplate gets no
    derate). ``None`` when the plant is absent from the EIA-860 CC sheet.
    """
    cap = cc_summer_capacity().get(int(plant_code))
    if cap is None:
        return None
    nameplate, net_summer = cap
    if nameplate <= 0.0:
        return None
    return min(1.0, net_summer / nameplate)


def cc_winter_capacity() -> dict[int, float]:
    """Vintage-keyed shim over :func:`_cc_winter_capacity_cached` (SPP-38).

    See that function for the contract; the active EIA-860 directory enters the
    cache key so a span run that moves the vintage between years cannot serve
    year 1's capabilities to years 2+ (rule 14 ``[R-ACCURATE]``).
    """
    return _cc_winter_capacity_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _cc_winter_capacity_cached(eia860_dir: str) -> dict[int, float]:
    """Return ``{plant_code: winter_mw}`` for every CC plant.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the :func:`cc_winter_capacity` shim,
    which supplies the active vintage.

    EIA-860 Generator_Y Operable ``Winter Capacity (MW)``, summed over each
    plant's combined-cycle generators — the exact companion of the nameplate /
    net-summer pair :func:`cc_summer_capacity` returns, read from the same sheet,
    the same technology filter and the same per-plant grouping.

    **Deliberately NOT clamped to nameplate.** The net-summer clamp in
    :func:`cc_summer_capacity` exists because a summed summer capability above
    the summed nameplate is component/total double-filing (EIA-860's schema
    caps summer capability at nameplate). No such schema bound exists for
    winter: a combustion turbine makes MORE than its plate rating in dense cold
    air, so a published winter capability above nameplate is a physical fact,
    not a filing error — 8 of the 67 California CC plants file one (plant 358
    Mountainview 1110.0 MW winter against 1036.8 MW nameplate, whose demonstrated
    off-summer peak is 1111.0 MW). Clamping here would silently delete the
    upward half of the seasonal basis (caiso-186).
    """
    path = Path(eia860_dir) / "eia860_generator_operable.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(
        path,
        columns=["Plant Code", "Technology", "Winter Capacity (MW)"],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    if cc.empty:
        return {}
    cc["plant_code"] = cc["Plant Code"].astype(float).astype(int)
    cc["win"] = pd.to_numeric(cc["Winter Capacity (MW)"], errors="coerce")
    out: dict[int, float] = {}
    for code, grp in cc.groupby("plant_code"):
        win_sum = float(grp["win"].sum())
        if win_sum > 0.0:
            out[int(code)] = win_sum
    return out


def cc_seasonal_capability_ratios(plant_code: int) -> tuple[float, float] | None:
    """Return a CC plant's ``(summer_ratio, winter_ratio)`` on the PUBLISHED basis.

    ``ScenarioConfig.cc_winter_capability_basis`` (caiso-186). The incumbent
    ``cc_nameplate_summer_derate`` carries the LP capacity at EIA-860
    **nameplate** and derates the summer months to the published net-summer
    rating, which leaves the OFF-summer capability resting on nameplate — a
    premise EIA-860 never publishes and the CEMS record refutes (off-summer p999
    is 0.73-0.89 of nameplate but 0.906-1.001 of the published WINTER rating,
    FINDING-caiso185 §5). This puts the capacity basis on the published seasonal
    envelope instead::

        B             = max(net_summer, winter)      # both EIA-860-published
        summer_ratio  = net_summer / B
        winter_ratio  = winter      / B

    so a bin carried at ``B`` reproduces the published summer rating in the
    summer months and the published **winter** rating off-summer. Nameplate — the
    one rating no season's capability equals — leaves the capacity basis
    entirely. **ZERO fitted scalars:** every quantity is an EIA-860 published
    rating or the ratio of two of them, and both are availability-EXCLUSIVE (a
    rating states what the machine does when it is available), which is what
    makes them admissible in the ``capacity_mw`` slot where a realized CEMS
    output is not (caiso-185 §4a; PRECHECK-caiso186 §2).

    ``net_summer`` carries :func:`cc_summer_capacity`'s double-file clamp
    unchanged; ``winter`` is deliberately unclamped (see
    :func:`cc_winter_capacity`). Both ratios are in ``(0, 1]`` by construction
    since ``B`` is the max of the pair. ``None`` when the plant is absent from
    either EIA-860 map, so callers fall back to the incumbent treatment exactly
    as they already do for an absent ``cc_summer_derate_ratio``.
    """
    cap = cc_summer_capacity().get(int(plant_code))
    winter = cc_winter_capacity().get(int(plant_code))
    if cap is None or winter is None or winter <= 0.0:
        return None
    _nameplate, net_summer = cap
    if net_summer <= 0.0:
        return None
    basis = max(net_summer, winter)
    if basis <= 0.0:
        return None
    return (net_summer / basis, winter / basis)


# EIA-860 Operable technology strings for a coal steam unit (the coal analogue
# of the CC "Natural Gas Fired Combined Cycle" filter above).
_COAL_SUMMER_TECH: frozenset[str] = frozenset(
    {"Conventional Steam Coal", "Coal Integrated Gasification Combined Cycle"}
)


def coal_summer_capacity() -> dict[int, tuple[float, float]]:
    """Vintage-keyed shim over :func:`_coal_summer_capacity_cached` (SPP-38).

    See that function for the contract; the active EIA-860 directory enters the
    cache key so a span run that moves the vintage between years cannot serve
    year 1's capabilities to years 2+ (rule 14 ``[R-ACCURATE]``).
    """
    return _coal_summer_capacity_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _coal_summer_capacity_cached(eia860_dir: str) -> dict[int, tuple[float, float]]:
    """Return ``{plant_code: (nameplate_mw, net_summer_mw)}`` for every coal plant.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the :func:`coal_summer_capacity` shim,
    which supplies the active vintage.

    Summed over each plant's coal-steam generators from the EIA-860 Generator_Y
    Operable sheet (:data:`_COAL_SUMMER_TECH`). The coal analogue of
    :func:`cc_summer_capacity`, consumed under
    ``config.coal_nameplate_summer_derate`` to derive the per-plant MEASURED
    summer derate ``net_summer / nameplate`` applied to coal in the summer
    months. Unlike CC, coal already carries its nameplate capacity in the LP
    (the CAMPD-bin / EIA-860 pmax), so this only supplies the summer multiplier;
    no capacity is raised. Plants absent from the sheet are absent from the map
    (callers keep full nameplate, as today).
    """
    path = Path(eia860_dir) / "eia860_generator_operable.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Technology",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
        ],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    coal = df[df["Technology"].isin(_COAL_SUMMER_TECH)].copy()
    if coal.empty:
        return {}
    coal["plant_code"] = coal["Plant Code"].astype(float).astype(int)
    coal["np"] = pd.to_numeric(coal["Nameplate Capacity (MW)"], errors="coerce")
    coal["ns"] = pd.to_numeric(coal["Summer Capacity (MW)"], errors="coerce")
    out: dict[int, tuple[float, float]] = {}
    for code, grp in coal.groupby("plant_code"):
        np_sum = float(grp["np"].sum())
        ns_sum = float(grp["ns"].sum())
        if np_sum > 0.0 and ns_sum > 0.0:
            out[int(code)] = (np_sum, ns_sum)
    return out


def coal_summer_derate_ratio(plant_code: int) -> float | None:
    """Return a coal plant's measured summer availability multiplier.

    ``net_summer / nameplate`` from :func:`coal_summer_capacity`, clamped to
    ``(0, 1]`` (a plant whose summer rating meets or exceeds nameplate gets no
    derate). ``None`` when the plant is absent from the EIA-860 coal sheet.
    """
    cap = coal_summer_capacity().get(int(plant_code))
    if cap is None:
        return None
    nameplate, net_summer = cap
    if nameplate <= 0.0:
        return None
    return min(1.0, net_summer / nameplate)


def fleet_to_bins(
    generators: list[Generator], iso: str, config: ScenarioConfig
) -> pd.DataFrame:
    """Build a per-plant CAMPD-style bins frame from an ISO's EIA-860 fleet.

    The non-ERCOT analogue of the CAMPD bin sheet: each thermal
    ``(plant_code, plant_group)`` becomes one bin row in the schema
    :func:`bins_to_fleet` consumes, so a per-plant ISO (PJM, MISO, ...) gets
    the *same* smoothed rising offer curve and per-plant committed / must-run
    tranches ERCOT gets from its bins. Committed % and (coal) must-run % come
    from the CAMPD-derived artifact (:func:`thermal_tranche_overrides`; under
    ``config.coal_mustrun_online_pmin`` the coal must-run uses the artifact's
    online-Pmin floor, rebuild step 2); plants absent from it fall back to
    :data:`_DEFAULT_TRANCHE_PCT_BY_GROUP`. Per-band
    heat rates are the plant's capacity-weighted heat rate times the group
    default multipliers (the offer curve overrides these in ``bins_to_fleet``).
    Non-thermal generators (nuclear, oil, biomass, ...) are not binned — the
    caller keeps them as raw LP units.

    Returns one row per thermal ``(plant_code, plant_group)``; empty frame when
    the fleet has no thermal plants.
    """
    _pu, _mg = campd_attribution_selectors(config)
    overrides = thermal_tranche_overrides(
        iso, getattr(config, "coal_mustrun_online_pmin", False), _pu
    )
    peaking = thermal_tranche_peaking(iso, _pu, _mg)
    if getattr(config, "cc_reserve_duty_split", False):
        _cohort = _reserve_duty_cohort(iso)
        logger.info(
            "cc_reserve_duty_split armed: %d measured reserve-duty CC "
            "plant(s) route to the class peak band — %s",
            len(_cohort),
            sorted(_cohort),
        )
    if getattr(config, "chp_layup_duty_split", False):
        _chp_cohort = _chp_layup_cohort(iso)
        logger.info(
            "chp_layup_duty_split armed: %d measured laid-up CHP plant(s) "
            "route to the class peak band — %s",
            len(_chp_cohort),
            sorted(_chp_cohort),
        )
    if getattr(config, "chp_layup_duty_curve", False):
        # Rule 19 [R-ONE-MECH]: one mechanism per phenomenon — the graded
        # curve REPLACES the single-band split, never stacks on it.
        if getattr(config, "chp_layup_duty_split", False):
            raise ValueError(
                "chp_layup_duty_curve and chp_layup_duty_split are mutually "
                "exclusive (rule 19 [R-ONE-MECH]): the curve is the split's "
                "graded successor — arm exactly one"
            )
        _duty = _chp_duty_curve(iso)
        logger.info(
            "chp_layup_duty_curve armed: %d measured laid-up CHP plant(s) "
            "offer their price-conditional duty (econ/peak %% of pmax), "
            "remainder withheld — %s",
            len(_duty),
            {c: _duty[c] for c in sorted(_duty)},
        )
    # Aggregate the per-generator fleet to one row per (plant, group): capacity
    # sums, heat rate is capacity-weighted. Under partial_plant_exit_carry
    # (miso-191, PREREG-miso191 §1-§2), a leg-1 partial-exit unit (loader-
    # stamped provenance + its own EIA-860 retirement) instead aggregates into
    # a date-scoped EXIT-COHORT bin keyed (plant, group, retirement year,
    # retirement month): the injected rows form their own bins, so the
    # per-unit retirement survives plant binning and the existing
    # cod_ramp.effective_cod per-unit preference (the Homer City seam) times
    # each cohort out at unit grain while the surviving plant's bin — now
    # aggregating only surviving units — keeps running. The whole-plant
    # retiree channel and leg-2 re-carries are deliberately NOT routed (they
    # keep today's timing; PREREG-miso191 §1 frozen scope).
    _ppx_cohort = bool(getattr(config, "partial_plant_exit_carry", False))
    # SPP-48: the SAME routing for the mid-vintage-year whole-plant exit
    # channel's units. A plant that retired DURING a year-matched native
    # vintage is injected carrying its own EIA-860 retirement month, and
    # without a date-scoped bin that month is discarded here exactly as
    # miso-191 measured for the partial-exit units — Oklaunion (plant 127,
    # retirement 9/2020) came back online in all twelve months of 2020, three
    # of them after it had retired. One mechanism, two memberships (rule 19
    # [R-ONE-MECH]); each stays behind its OWN flag, so neither arms the other.
    _mvx_cohort = bool(getattr(config, "mid_vintage_exit_carry", False))
    agg: dict[tuple, dict] = {}
    for g in generators:
        if g.plant_group not in BIN_GROUP_TO_FUEL:
            continue  # non-thermal (nuclear / oil / biomass) stays a raw unit
        code = int(g.plant_code)
        if code <= 0:
            continue
        _ry: int | None = None
        _rm: int | None = None
        if (
            (_ppx_cohort and getattr(g, "partial_exit_unit", False))
            or (_mvx_cohort and getattr(g, "mid_vintage_exit_unit", False))
        ) and g.retirement_year is not None:
            _ry = int(g.retirement_year)
            _rm = int(g.retirement_month) if g.retirement_month is not None else 12
            key: tuple = (code, g.plant_group, _ry, _rm)
        else:
            key = (code, g.plant_group)
        a = agg.setdefault(
            key,
            {
                "cap": 0.0,
                "hr_cap": 0.0,
                "name": g.name,
                "zone": g.zone,
                "ry": _ry,
                "rm": _rm,
            },
        )
        a["cap"] += float(g.pmax_mw)
        a["hr_cap"] += float(g.pmax_mw) * float(g.heat_rate)

    rows: list[dict] = []
    for key, a in agg.items():
        code, group = key[0], key[1]
        cap = a["cap"]
        if cap <= 0.0:
            continue
        # Heat rate is an intensive property: divide the accumulated
        # capacity-weighted sum by the SAME capacity basis the weights were
        # accumulated on (the net-summer ratings above), BEFORE any nameplate
        # rescale. Dividing by the rescaled capacity deflated every CC plant's
        # base heat rate — and every offer band built on it — by its own
        # net-summer/nameplate ratio (differentially, up to −27 % for Moss
        # Landing), scrambling the within-class merit order
        # (FINDING-caiso78-cc-hr-basis-2026-07-12.md §3).
        base_hr = a["hr_cap"] / cap
        # CC nameplate capacity (config.cc_nameplate_summer_derate): the fleet
        # carries each unit's net-summer rating, so a CC plant's summed cap is
        # net-summer. Rescale it up to full nameplate (cap / (net_summer /
        # nameplate)); the availability builder reapplies the per-plant summer
        # derate seasonally. Robust to fleet-vs-EIA membership differences (uses
        # the ratio, not the absolute nameplate). ERCOT/other groups unchanged.
        if group in ("CC_REGULAR", "CC_CHP") and getattr(
            config, "cc_nameplate_summer_derate", False
        ):
            # config.cc_winter_capability_basis (caiso-186) replaces the
            # nameplate target with the PUBLISHED seasonal envelope
            # B = max(net_summer, winter), so the rescale lands on B and the
            # availability builder carries each season's own published rating
            # (net_summer/B in summer, winter/B off-summer) instead of leaving
            # off-summer on an unpublished nameplate premise. A basis swap, not
            # a second derate (rule 19 [R-ONE-MECH]); the two ratios are read
            # from ONE helper so this rescale and the availability legs can
            # never drift apart. Absent-plant fallback is identical on both
            # paths (the plant keeps net-summer).
            _ratio = None
            if getattr(config, "cc_winter_capability_basis", False):
                _pair = _pkg_ns().cc_seasonal_capability_ratios(code)
                if _pair is not None:
                    _ratio = _pair[0]
            if _ratio is None:
                _ratio = _pkg_ns().cc_summer_derate_ratio(code)
            if _ratio is not None and _ratio > 0.0:
                cap = cap / _ratio
        d_mr, d_mc, d_peak = _DEFAULT_TRANCHE_PCT_BY_GROUP.get(group, (0.0, 30.0, 8.0))
        _measured_row = (code, group) in overrides
        committed, mustrun = overrides.get((code, group), (d_mc, d_mr))
        pct_mc = committed
        pct_mr = mustrun if group == "COAL" else d_mr
        # COAL MUST-RUN REQUIRES A MEASURED ROW (config.coal_mustrun_requires_
        # measured_row, pjm-h14). Rule 17 [R-FLOOR-WINDOW]: a min-gen floor owes
        # (a) an external driver, (b) the hours it may bind, (c) a forward story.
        # A coal plant ABSENT from the ISO's CAMPD thermal-tranche artifact has
        # none of the three, and TWO unmeasured defaults then compound on it:
        # :data:`_DEFAULT_TRANCHE_PCT_BY_GROUP` hands it a 45 %-of-nameplate
        # must-run tranche (its own comment calls the fallback population
        # "rarely-online units with no reliable observed floor"), and
        # ``assembly.py``'s ``coal_sync_online_frac(...).get(code, 1.0)`` then
        # holds that tranche in ALL 8760 hours because the online%-scaled
        # window also defaults to force-all when there is no measured share.
        # The plants with the LEAST evidence therefore carry the STRONGEST and
        # WIDEST floor — the opposite of both defaults' stated intent.
        #
        # Armed, an unmeasured coal plant carries NO must-run tranche; that
        # capacity falls to the economic band, so the plant keeps every MW and
        # the LP decides it on price. Removing the synchronization floor is a
        # CONSEQUENCE, not a second mechanism (rule 19 [R-ONE-MECH]):
        # ``assembly.py`` sets ``coal_sync_pmin_mw`` from the ``mustrun``/
        # ``sync`` tranche capacity, so a zero must-run leaves nothing to floor.
        # ZERO free parameters (rule 21 [R-DOF]) — the arm asserts no level, it
        # withdraws an assertion that has no measurement behind it. Gated
        # default off, so every other ISO's keeper is byte-identical
        # (rule 25 [R-ISO-SCOPE]).
        if (
            group == "COAL"
            and not _measured_row
            and getattr(config, "coal_mustrun_requires_measured_row", False)
        ):
            pct_mr = 0.0
        pct_peak = peaking.get((code, group), d_peak)
        # Keep the split feasible: clip committed + peaking to leave room for an
        # economic band above the must-run floor.
        room = max(0.0, 100.0 - pct_mr)
        if pct_mc + pct_peak > room:
            pct_mc = max(0.0, min(pct_mc, room - pct_peak))
        # RESERVE-DUTY split (cc_reserve_duty_split, nyiso-146): a CC plant in
        # the measured capacity-only cohort (reserve_duty_cc_<ISO>.csv —
        # on-share/CF <= the population-gap ceiling; NYISO's Seneca fleet)
        # offers its WHOLE dispatchable capacity at the class curve's PEAK
        # band, the duty-role mirror of cc_intermediate_split: the LP,
        # seeing only the (competitive) heat rate, runs these plants
        # 87-99 % of hours against 1-6 % metered (the nyiso-145 defect-B
        # merit-order inversion). An offer SHAPE from a measured duty-role
        # signal, never a pin (rule 13); the level is the class's existing
        # identified peak multiplier — zero new scalars (rule 21). Gated
        # default off so a control run is byte-identical.
        if (
            group == "CC_REGULAR"
            and getattr(config, "cc_reserve_duty_split", False)
            and code in _reserve_duty_cohort(iso)
        ):
            pct_mc = 0.0
            pct_peak = room
        # CHP LAY-UP duty split (chp_layup_duty_split, nyiso-148): the
        # cogeneration sibling of the block directly above, DISJOINT from it by
        # class scope (rule 19 [R-ONE-MECH]) — a semi-mothballed cogen whose
        # own meter reads a zero median in every (year, 4-hour block) cell
        # (chp_layup_census_<ISO>.csv) offers its WHOLE dispatchable capacity
        # at the class curve's PEAK band. Exposed by nyiso-147: with the
        # measured grid capacity restored the LP runs Selkirk (10725) at 7.9x
        # its meter, with ZERO floor involved. Offer SHAPE from a measured
        # duty-role signal, never a pin (rule 13); the level is the class's
        # existing identified peak multiplier — zero new scalars (rule 21).
        # Gated default off so a control run is byte-identical.
        if (
            group in _CHP_GROUPS
            and getattr(config, "chp_layup_duty_split", False)
            and code in _chp_layup_cohort(iso)
        ):
            pct_mc = 0.0
            pct_peak = room
        pct_econ = max(0.0, 100.0 - pct_mr - pct_mc - pct_peak)
        # CHP LAY-UP duty CURVE (chp_layup_duty_curve, nyiso-149): the GRADED
        # successor to the single-band split above (rejected nyiso-148 —
        # bang-bang where the meters are graded). A census plant offers only
        # its measured price-conditional duty: pct_econ at the class econ
        # band, pct_peak at the class peak band (chp_duty_curve_<ISO>.csv),
        # and the remainder is WITHHELD (neither energy nor reserves). Frame
        # values here keep the synthesized-bins schema coherent; the
        # load-bearing override is assembly.py::bins_to_fleet (the nyiso-146b
        # / nyiso-148 inert-solve lesson, twice paid).
        if (
            group in _CHP_GROUPS
            and getattr(config, "chp_layup_duty_curve", False)
            and code in _chp_layup_cohort(iso)
        ):
            _duty = _chp_duty_curve(iso).get(code)
            if _duty is not None and cap > 0.0:
                # MW contract (PREREG-nyiso149 §7): the duty tuple is MW;
                # the frame's pct columns express it against THIS bin's own
                # capacity, so the two seams can never disagree on basis.
                pct_mc = 0.0
                pct_econ = min(100.0 * _duty[0] / cap, max(0.0, room))
                pct_peak = min(100.0 * _duty[1] / cap, max(0.0, room - pct_econ))
        mults = _DEFAULT_HR_MULT_BY_GROUP.get(
            group, _DEFAULT_HR_MULT_BY_GROUP["CC_REGULAR"]
        )
        rows.append(
            {
                "Plant_Group": group,
                "ERCOT_Zone": a["zone"],
                "Bin_Number": 1,
                "Bin_Label": a["name"],
                "Plant_Code": code,
                "Plant_Name": a["name"],
                "Turbine_Class": "",
                "capacity_mw": cap,
                "hr_weighted": base_hr,
                "pct_mr": pct_mr,
                "pct_mc": pct_mc,
                "pct_econ": pct_econ,
                "pct_peak": pct_peak,
                "min_run": 0,
                "min_down": 0,
                "hr_mr": base_hr * mults["mr"],
                "hr_mc": base_hr * mults["mc"],
                "hr_econ": base_hr * mults["econ"],
                "hr_peak": base_hr * mults["peak"],
                "plant_count": 1,
                "plant_codes": [code],
                "fuel": BIN_GROUP_TO_FUEL[group],
                # Exit-cohort timing (miso-191): None on every ordinary plant
                # row; set only on a date-scoped exit-cohort bin, and stamped
                # onto its tranche generators by bins_to_fleet so the COD
                # ramp's per-unit retirement preference applies.
                "Retirement_Year": a["ry"],
                "Retirement_Month": a["rm"],
            }
        )
    bins = pd.DataFrame(
        rows,
        columns=[
            "Plant_Group",
            "ERCOT_Zone",
            "Bin_Number",
            "Bin_Label",
            "Plant_Code",
            "Plant_Name",
            "Turbine_Class",
            "capacity_mw",
            "hr_weighted",
            "pct_mr",
            "pct_mc",
            "pct_econ",
            "pct_peak",
            "min_run",
            "min_down",
            "hr_mr",
            "hr_mc",
            "hr_econ",
            "hr_peak",
            "plant_count",
            "plant_codes",
            "fuel",
            "Retirement_Year",
            "Retirement_Month",
        ],
    )
    # Per-plant CC capacity reconciliation (ScenarioConfig.cc_capacity_reconcile)
    # for the synthesized-bins ISOs — the same hook the ERCOT curated-CSV path
    # gets via load_campd_bins. Applied after the summer-derate nameplate
    # rescale above, so a demonstrated-peak CAP row (mode="cap",
    # scripts/data/derive_cc_capacity_reconcile.py --mode cap) bounds the final LP
    # capacity at the plant's measured CAMPD sustained maximum.
    if not bins.empty and getattr(config, "cc_capacity_reconcile", False):
        bins = _reconcile_cc_capacity(
            bins, getattr(config, "cc_capacity_reconcile_path", "")
        )
    return bins


# Combined-cycle duct-burner (peaking) heat-rate multiplier by turbine class,
# on (AHR x fuel_price). Operator ranges: advanced G/H-class 2.3-2.5, F-class
# 2.0-2.3, older E-class / legacy 1.8-2.0 — a lower base AHR makes the
# duct-fire/base ratio steeper, so the most efficient classes carry the highest
# multiplier. Set 0.1 below the range midpoints per the operator's CC peaking
# tune.
CC_DUCT_BURNER_PEAK_MULT: dict[str, float] = {
    "advanced": 2.50,  # G/H-class
    "f": 2.25,  # F-class incl. E/F
    "older": 2.00,  # E-class, legacy
}


#: The cogeneration plant groups ``chp_layup_duty_split`` may re-band. Held as
#: a module constant rather than inline so the load-bearing seam and the
#: offer-curve mirror can never drift apart.
_CHP_GROUPS: tuple[str, ...] = ("CC_CHP", "CT_CHP", "ST_CHP")


@lru_cache(maxsize=8)
def _chp_layup_cohort(iso: str) -> frozenset[int]:
    """The measured laid-up CHP cohort for *iso*.

    Thin cached wrapper over
    :func:`market_sim.data.chp_layup.load_chp_layup_census` so the
    ``fleet_to_bins`` per-plant loop reads the artifact once per process.
    """
    from market_sim.data.chp_layup import load_chp_layup_census

    return load_chp_layup_census(iso)


@lru_cache(maxsize=8)
def _chp_duty_curve(iso: str) -> dict[int, tuple[float, float]]:
    """The measured duty-curve offer fractions for *iso*'s lay-up cohort.

    Thin cached wrapper over
    :func:`market_sim.data.chp_layup.load_chp_duty_curve` (nyiso-149); the
    census (:func:`_chp_layup_cohort`) stays the membership authority — a
    plant in the artifact but not the census is never re-banded.
    """
    from market_sim.data.chp_layup import load_chp_duty_curve

    return load_chp_duty_curve(iso)


@lru_cache(maxsize=8)
def _reserve_duty_cohort(iso: str) -> frozenset[int]:
    """The measured reserve-duty (capacity-only) CC cohort for *iso*.

    Thin cached wrapper over
    :func:`market_sim.data.reserve_duty.load_reserve_duty_cc` so the
    ``fleet_to_bins`` per-plant loop reads the artifact once per process.
    """
    from market_sim.data.reserve_duty import load_reserve_duty_cc

    return load_reserve_duty_cc(iso)


def cc_duct_burner_peak_mult(turbine_class: object) -> float:
    """Return the CC duct-burner peaking HR multiplier for a turbine class.

    Maps the CSV ``Turbine_Class`` string onto the operator's three duct-burner
    buckets (see :data:`CC_DUCT_BURNER_PEAK_MULT`). Unknown / blank classes
    fall back to the F-class midpoint (the modal CC class).
    """
    s = str(turbine_class)
    if "G-class" in s or "H-class" in s:
        return CC_DUCT_BURNER_PEAK_MULT["advanced"]
    if "F-class" in s:  # also catches "E/F-class"
        return CC_DUCT_BURNER_PEAK_MULT["f"]
    if "E-class" in s or "Legacy" in s:
        return CC_DUCT_BURNER_PEAK_MULT["older"]
    return CC_DUCT_BURNER_PEAK_MULT["f"]


# Coal supply class -> offer_curve_by_group key (COAL_LIGNITE / COAL_PRB /
# COAL_BIT / COAL_WC; sub-bituminous routes to COAL_PRB), from the canonical
# taxonomy; unclassified coal uses the generic COAL curve. Kept under the
# local name for back-compat.
_COAL_SUPPLY_TO_CURVE = COAL_SUPPLY_TO_CLASS


@lru_cache(maxsize=8)
def ct_intermediate_plants(
    iso: str, threshold: float, per_unit: bool = False, merit_guard: bool = False
) -> frozenset[int]:
    """EIA plant codes of intermediate-duty ``CT_PEAKER`` units for an ISO.

    A simple-cycle combustion turbine whose measured CAMPD median capacity
    factor (``thermal_tranches_<ISO>.csv`` ``median_cf``) is at or above
    ``threshold`` runs intermediate / near-baseload duty, not as a true
    peaker. EIA-860 confirms these are genuine GT / IC simple-cycle units (not
    mislabeled combined cycle or cogen), so their prime-mover *classification*
    is correct — what differs is their *duty cycle*. The single steep
    ``CT_PEAKER`` offer curve (a committed-band start-cost hurdle that holds
    true peakers idle) mis-prices these always-on units above the CC fleet, so
    they never clear and CC over-runs. The cohort is routed to the flatter
    ``CT_INTERMEDIATE`` offer curve instead.

    The median CF is a durable, forward-reproducible duty-role signal — it
    regenerates per unit and year from CAMPD and responds to changed
    conditions (a unit that stops running intermediate falls out of the
    cohort) — and assigns an offer *shape*, never pins measured output, so it
    is admissible under CLAUDE.md #11/#12 on the same basis as
    :data:`market_sim.data.outages.ST_GAS_PEAKER_PLANTS`. Returns an empty set
    when the ISO has no tranche file (e.g. ERCOT's hand-set bins).
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path)
    if "median_cf" not in df.columns or "plant_group" not in df.columns:
        return frozenset()
    ct = df[(df["plant_group"] == "CT_PEAKER") & (df["median_cf"] >= threshold)]
    codes = set(int(c) for c in ct["plant_code"].dropna())

    # Exclude CTs at multi-technology sites (COAL+CT, CC+CT, etc.): the CT
    # at such a plant is a supplemental peaker, not an intermediate-duty
    # unit, so it keeps the steep CT_PEAKER curve.
    bin_path = PROCESSED_DIR / f"bin_assignments_{iso.upper()}.csv"
    if bin_path.exists() and codes:
        bins_df = pd.read_csv(
            bin_path, usecols=["Plant_Code", "Plant_Group", "Mixed_Facility"]
        )
        ct_bins = bins_df[bins_df["Plant_Group"] == "CT_PEAKER"]
        mixed = set(
            int(c)
            for c in ct_bins.loc[
                ct_bins["Mixed_Facility"].notna()
                & (ct_bins["Mixed_Facility"].astype(str).str.strip() != ""),
                "Plant_Code",
            ].dropna()
        )
        codes -= mixed

    return frozenset(codes)


@lru_cache(maxsize=8)
def st_gas_intermediate_plants(
    iso: str, threshold: float, per_unit: bool = False, merit_guard: bool = False
) -> frozenset[int]:
    """EIA plant codes of intermediate-duty ``ST_GAS`` units for an ISO.

    The gas-steam analogue of :func:`ct_intermediate_plants`. A legacy gas-steam
    plant whose measured CAMPD median capacity factor
    (``thermal_tranches_<ISO>.csv`` ``median_cf``) is at or above ``threshold``
    runs intermediate / near-baseload duty (MISO's Harding Street, Ames, Nine
    Mile Point, Lewis Creek, Sabine, ...), not as a peaker. The ERCOT-fitted
    ST_GAS offer curve (steep econ_high ramp + a 15% peaking band) prices most of
    each such unit above the CC fleet, so it never clears and the model
    under-runs it (the Moselle / Lewis Creek under-run). The cohort is routed to
    the flatter ``ST_GAS_INTERMEDIATE`` offer curve instead.

    The median CF is a durable, forward-reproducible duty-role signal — it
    regenerates per unit and year from CAMPD and responds to changed conditions
    — and assigns an offer *shape*, never pins measured output, so it is
    admissible under CLAUDE.md #11/#12 on the same basis as
    :func:`ct_intermediate_plants` and :data:`outages.ST_GAS_PEAKER_PLANTS`.
    Returns an empty set when the ISO has no tranche file (e.g. ERCOT's hand-set
    bins).
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path)
    if "median_cf" not in df.columns or "plant_group" not in df.columns:
        return frozenset()
    st = df[(df["plant_group"] == "ST_GAS") & (df["median_cf"] >= threshold)]
    return frozenset(int(c) for c in st["plant_code"].dropna())


@lru_cache(maxsize=8)
def cc_intermediate_plants(
    iso: str, threshold: float, per_unit: bool = False, merit_guard: bool = False
) -> frozenset[int]:
    """EIA plant codes of intermediate-duty ``CC_REGULAR`` units for an ISO.

    The combined-cycle analogue of :func:`ct_intermediate_plants` /
    :func:`st_gas_intermediate_plants`. A combined-cycle plant whose measured
    CAMPD median capacity factor (``thermal_tranches_<ISO>.csv`` ``median_cf``)
    is at or above ``threshold`` runs intermediate / baseload duty, not as a
    flexible mid-merit peaker. The ``CC_REGULAR`` offer curve was fit to ERCOT's
    duct-fire-heavy 2x1 CCs (Colorado Bend II / Wolf Hollow II): a rising econ
    ramp (start-cost-amortized) topped by a duct-burner peak band. For a fleet of
    already-committed, high-CF baseload CCs (MISO's entire CC fleet measures a
    median CF of 50-150 %, mean ~90 %) that rising ramp over-prices the upper
    operating range — the incremental energy of a committed CC is near its
    full-load heat rate (~0.93x its own average), flat across load, not a
    start-cost-amortized peaker bid — so the upper econ tranches sit above the
    clearing price and the model under-runs the CC fleet (the MISO gas under-run).
    The cohort is routed to the flatter ``CC_INTERMEDIATE`` offer curve, which
    flattens the econ ramp to the measured near-baseload incremental cost while
    **keeping** the physically-real duct-burner peak band (the duct-fire reach is
    still priced at its true ~2.25x heat rate — only the operating-range ramp is
    corrected, never the peak).

    The median CF is a durable, forward-reproducible duty-role signal — it
    regenerates per unit and year from CAMPD and responds to changed conditions
    (a CC that stops running baseload falls out of the cohort) — and assigns an
    offer *shape*, never pins measured output, so it is admissible under
    CLAUDE.md #11/#12 on the same basis as :func:`ct_intermediate_plants` and
    :func:`st_gas_intermediate_plants`. Returns an empty set when the ISO has no
    tranche file (e.g. ERCOT's hand-set bins).
    """
    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path)
    if "median_cf" not in df.columns or "plant_group" not in df.columns:
        return frozenset()
    cc = df[(df["plant_group"] == "CC_REGULAR") & (df["median_cf"] >= threshold)]
    return frozenset(int(c) for c in cc["plant_code"].dropna())


# five ``HR_Mult_*`` are per-tranche multipliers on the plant's base HR. Other
# columns in the sheet (names, group, config, turbine class …) are reference
# only and ignored by the loader.
PLANT_TRANCHE_OVERRIDE_FIELDS: dict[str, str] = {
    "pct_mr": "Pct_Must_Run",
    "pct_mc": "Pct_Committed",
    "pct_lo": "Pct_Econ_Low",
    "pct_hi": "Pct_Econ_High",
    "pct_pk": "Pct_Peaking",
    "hr_mr": "HR_Mult_Must_Run",
    "hr_mc": "HR_Mult_Committed",
    "hr_lo": "HR_Mult_Econ_Low",
    "hr_hi": "HR_Mult_Econ_High",
    "hr_pk": "HR_Mult_Peaking",
}


@lru_cache(maxsize=8)
def load_plant_tranche_config(path: str | Path) -> dict[int, dict[str, float]]:
    """Load the per-plant tranche-config override sheet, keyed by plant code.

    Each row gives one plant's five tranche shares of nameplate and five
    per-tranche heat-rate multipliers (see :data:`PLANT_TRANCHE_OVERRIDE_FIELDS`).
    Returned as ``{plant_code: {pct_mr, pct_mc, pct_lo, pct_hi, pct_pk, hr_mr,
    hr_mc, hr_lo, hr_hi, hr_pk}}`` for :func:`bins_to_fleet` to apply in place of
    the offer curve / per-plant dicts. Rows with a blank or non-numeric value in
    any required column are skipped (so a partially edited sheet still loads).
    """
    df = pd.read_csv(path)
    missing = [c for c in PLANT_TRANCHE_OVERRIDE_FIELDS.values() if c not in df.columns]
    if "Plant_Code" not in df.columns or missing:
        raise ValueError(
            f"tranche-config sheet {path} missing columns: "
            f"{(['Plant_Code'] if 'Plant_Code' not in df.columns else []) + missing}"
        )
    out: dict[int, dict[str, float]] = {}
    # itertuples over the read columns only, positionally (name=None): the
    # sheet's headers are not all valid Python identifiers-by-construction, and
    # positional tuples sidestep itertuples' name mangling entirely. Values
    # arrive as the column's own scalars rather than a dtype-upcast Series
    # element, and still pass through float()/int(), so a blank cell (NaN), a
    # non-numeric cell (ValueError) and a clean row all resolve exactly as
    # before.
    keys = list(PLANT_TRANCHE_OVERRIDE_FIELDS)
    cols = ["Plant_Code"] + [PLANT_TRANCHE_OVERRIDE_FIELDS[k] for k in keys]
    for row in df[cols].itertuples(index=False, name=None):
        try:
            rec = {key: float(value) for key, value in zip(keys, row[1:])}
            code = int(row[0])
        except (TypeError, ValueError):
            continue
        if any(v != v for v in rec.values()):  # NaN in a required cell
            continue
        out[code] = rec
    return out
