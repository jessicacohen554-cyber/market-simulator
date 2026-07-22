"""Endogenous WECC-West neighbor fleet for the CAISO WECC_import zone (caiso-110).

Builds a REAL co-optimized WECC-West neighbor at the single ``WECC_import``
zone — its own measured hourly demand, renewable/hydro/nuclear availability
shaped to measured output, and a reduced dispatchable thermal fleet (coal,
gas-CC, gas-CT) — so the one ISO-agnostic LP co-dispatches CA + West and the
WECC->CAISO tie flow becomes a pure congestion outcome instead of a static
priced import capability. Gated by ``ScenarioConfig.caiso_endogenous_wecc_node``
(default off); see docs/handoffs/caiso-endogenous-wecc-node-design-2026-07-21.md.

Why this shape (all as ``fuel_type="import"`` pseudo-gens):
    The results/scoring pipeline is zone-blind and keys attribution off
    ``fuel_type``/``klass``. A WECC_import unit carrying a real fuel type
    (gas/coal/...) would be swept into CAISO's C1/C4/C5a and its demand into
    CAISO load. Modeling the whole West fleet as ``fuel_type="import"`` (a) keeps
    the fossil gates + eGRID-class CO2 blind to it (klass "import" draws no CO2
    intensity and is not a gas/coal class), while (b) its DISTINCT marginal cost
    rides in the ``vom`` field so the LP still co-optimizes a real West merit
    order. run_year additionally zone-excludes WECC_import from the committed
    dispatch/system frames and reports the CAISO net import from the tie flow
    (see scripts/run_calibration_full.py) — so West demand never inflates CAISO
    load and net import is the tie flow, not the West's total generation.

Rule-13 admissibility / DOF ledger: every parameter here is a MEASURED input
that regenerates for a forward year and responds to changed conditions —
    * demand + renewable/hydro/nuclear hourly shape: EIA-930 BALANCE Region
      NW+SW aggregate (``wecc-west-supply`` clean frame);
    * thermal nameplate capacities: EIA-860 operable, West states;
    * gas price: Henry Hub (the model's per-year gas benchmark);
    * coal price / heat rates / VOM: constants.COAL_PRICE_BASE,
      constants.HEAT_RATE_BINS, constants.VOM.
Zero free parameters are fitted to the CAISO residual (rule 1 / rule 25).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config import constants as C
from market_sim.data.campd import _hour_index_8760
from market_sim.data.fleet import Generator

# The endogenous node lives on the single WECC_import zone (no per-hub split).
WECC_WEST_ZONE = "WECC_import"

# All endogenous-West unit ids carry this prefix so run_year can find them for
# the availability override and the results zone-exclusion.
WECC_WEST_PREFIX = "WECCW_"

# EIA-860 operable nameplate (MW) for the WECC-West states covered by EIA-930
# Region NW+SW (AZ NV NM UT CO WY MT ID OR WA), aggregated by fuel
# (scripts/data/derive_wecc_west_supply.py provenance; EIA-860
# eia860_generator_operable.parquet). A capacity CEILING: the LP runs a West
# thermal unit only to the extent CA/West prices pull it, so an over-estimate
# is harmless (idle capacity prices at gas MC) while it guarantees the West can
# serve its own measured peak (max thermal residual ~56 GW << thermal 73.6 GW).
_WEST_NAMEPLATE_MW: dict[str, float] = {
    "solar": 23_800.0,
    "wind": 27_100.0,
    "hydro": 41_300.0,
    "nuclear": 5_400.0,
    "coal": 20_300.0,
    "gas_cc": 34_700.0,  # combined-cycle prime movers CA/CT/CS
    "gas_ct": 18_600.0,  # simple-cycle GT (13.9) + steam gas ST (4.7)
}

# Heat rates (MMBtu/MWh) and VOM ($/MWh) from the model's own cited constants
# (constants.HEAT_RATE_BINS / constants.VOM / constants.COAL_SIGMOID_REP_HR_COAL).
# The West CCGT/CT fleet is a vintage mix; the representative aggregate HR sits
# between the class bins.
_WEST_HR: dict[str, float] = {
    "coal": C.COAL_SIGMOID_REP_HR_COAL,  # 10.0 (subcritical rep)
    "gas_cc": 7.0,  # between HEAT_RATE_BINS['gas_cc'] f_class 6.7 and older 7.5
    "gas_ct": C.HEAT_RATE_BINS["gas_ct"]["frame"],  # 10.5 (frame CT rep)
}
_WEST_VOM: dict[str, float] = {
    "coal": C.VOM["coal"],  # 4.5
    "gas_cc": C.VOM["gas_cc"],  # 2.0
    "gas_ct": C.VOM["gas_ct"],  # 3.5
    "hydro": C.VOM["hydro"],  # 1.4 (run-of-river O&M; water opportunity is
    # irrelevant because hydro is capped at measured output and the West export
    # margin is set by the thermal unit that would backfill it)
    "nuclear": C.VOM["nuclear"],  # 2.5
}
# West delivered coal ($/MMBtu): PRB / subbituminous mine-mouth, the cheapest US
# coal — consistent with COAL_PRICE_BASE for the other PRB-burning ISOs
# (ERCOT 2.0 / MISO 1.9). Not tuned to the CAISO residual (rule 25).
_WEST_COAL_PRICE = C.COAL_PRICE_BASE.get("ERCOT", 2.0)
# Nuclear all-in short-run cost ($/MWh): fuel (~$0.75/MMBtu x HR ~10.4) + VOM.
# Must-run baseload — never the export margin, so precision is immaterial.
_WEST_NUCLEAR_MC = 9.0
# Renewable marginal cost ($/MWh): 0 (VOM['solar']/['wind']).
_WEST_VRE_MC = 0.0

HOURS_PER_YEAR = 8760

# Units whose hourly availability is SHAPED to measured output (intermittent or
# must-take); the rest (coal/gas) are economically dispatchable to nameplate.
_SHAPED_UNITS: tuple[tuple[str, str], ...] = (
    ("solar", "solar_mw"),
    ("wind", "wind_mw"),
    ("hydro", "hydro_mw"),
    ("nuclear", "nuclear_mw"),
)
_THERMAL_UNITS: tuple[str, ...] = ("coal", "gas_cc", "gas_ct")


def _align_to_model_clock(
    frame: pd.DataFrame, col: str, hours: int = HOURS_PER_YEAR
) -> np.ndarray:
    """Fold a UTC-keyed West column onto the model's fixed non-leap 8760 clock.

    The ``wecc-west-supply`` frame is keyed on ``interval_start_utc`` (tz-aware
    UTC). The model clock is Pacific *prevailing* wall time on a fixed non-leap
    8760 (Feb 29 dropped, ``campd._hour_index_8760`` — the same fold the EIA-930
    loaders use). We convert UTC -> US/Pacific (which applies PST/PDT) and fold
    directly (no lag), which empirically aligns the West solar hod-profile to the
    model's own CAISO solar at r=0.984 and demand at r=0.86 (the residual ~1h is
    the West's multi-timezone smear — it spans Mountain AZ/NM and Pacific PNW).
    We deliberately do NOT route through ``_caiso_interchange_model_clock``: that
    1-2 h lag corrects a specific *corrupted* CISO interchange file, not honest
    UTC (docs/handoffs design §7; envelopes.py:526-543).

    DST fall-back duplicates (two UTC hours -> one wall-clock slot) are averaged;
    the ~8 source-gap hours and the DST spring-forward gap are forward/backward
    filled from neighbours (negligible for annual energy and the belly/overnight
    split that drives C5a).
    """
    pac = frame["interval_start_utc"].dt.tz_convert("US/Pacific")
    idx = _hour_index_8760(
        pac.dt.month.to_numpy(), pac.dt.day.to_numpy(), pac.dt.hour.to_numpy()
    )
    vals = pd.to_numeric(frame[col], errors="coerce").to_numpy(dtype=float)
    keep = (idx >= 0) & np.isfinite(vals)
    idx, vals = idx[keep], vals[keep]
    hour_sum = np.zeros(hours)
    hour_cnt = np.zeros(hours)
    np.add.at(hour_sum, idx, vals)
    np.add.at(hour_cnt, idx, 1.0)
    out = np.full(hours, np.nan)
    seen = hour_cnt > 0
    out[seen] = hour_sum[seen] / hour_cnt[seen]
    # Backfill the handful of unseen slots (source gaps + DST spring gap).
    out = pd.Series(out).ffill().bfill().to_numpy()
    return out[:hours]


def _thermal_mc(fuel: str, henry_hub: float) -> float:
    """Marginal cost ($/MWh) of a West thermal tranche = HR x hub + VOM.

    Coal uses the West PRB delivered price; gas uses Henry Hub (the run's
    per-year benchmark). No carbon term: the West is out-of-CA (AZ/NV/... are
    uncarbonized; the West's own CO2 is not part of CAISO's inventory), so the
    unit carries ``emission_rate_co2=0`` and pays no CA allowance.
    """
    if fuel == "coal":
        return _WEST_HR["coal"] * _WEST_COAL_PRICE + _WEST_VOM["coal"]
    return _WEST_HR[fuel] * henry_hub + _WEST_VOM[fuel]


def build_wecc_west_fleet(
    year: int, henry_hub_price: float, hours: int = HOURS_PER_YEAR
) -> tuple[list[Generator], dict[str, np.ndarray], np.ndarray]:
    """Build the endogenous WECC-West neighbor fleet for one backcast year.

    Reads the ``wecc-west-supply`` clean frame (EIA-930 Region NW+SW aggregate),
    aligns every hourly series to the model's 8760 clock, and returns a reduced
    fleet of ``fuel_type="import"`` pseudo-generators at the ``WECC_import``
    zone, an availability-override map for the shaped (intermittent/must-take)
    units, and the West's own hourly demand.

    Args:
        year: backcast year (2023-2025).
        henry_hub_price: the run's Henry Hub gas price ($/MMBtu) for the West
            gas MC (the same ``_henry_hub_actual`` scalar the LP uses for CA).
        hours: LP horizon (8760).

    Returns:
        ``(generators, availability, demand_mw)`` where
        * ``generators`` — the West fleet (solar/wind/hydro/nuclear/coal/gas-CC/
          gas-CT), all ``zone="WECC_import"``, ``fuel_type="import"``,
          ``heat_rate=0``, MC in ``vom``, ``emission_rate_co2=0``;
        * ``availability`` — ``{unit_id: (hours,) array}`` for the shaped units
          (measured output / nameplate, clipped to [0, 1]); thermal units are
          absent (dispatchable to nameplate);
        * ``demand_mw`` — ``(hours,)`` West demand for the WECC_import balance.
    """
    from scripts.lib.clean_io import read_clean

    frame = read_clean("wecc-west-supply", iso="CAISO", year=year)
    demand_mw = _align_to_model_clock(frame, "demand_mw", hours)

    gens: list[Generator] = []
    availability: dict[str, np.ndarray] = {}

    def _uid(fuel: str) -> str:
        return f"{WECC_WEST_PREFIX}{fuel}"

    # Shaped units (VRE + must-take hydro/nuclear): availability = measured/cap.
    for fuel, col in _SHAPED_UNITS:
        cap = _WEST_NAMEPLATE_MW[fuel]
        meas = _align_to_model_clock(frame, col, hours)
        avail = np.clip(meas / cap, 0.0, 1.0)
        mc = (
            _WEST_NUCLEAR_MC
            if fuel == "nuclear"
            else (_WEST_VOM["hydro"] if fuel == "hydro" else _WEST_VRE_MC)
        )
        gens.append(
            Generator(
                unit_id=_uid(fuel),
                name=f"WECC_West_{fuel}",
                zone=WECC_WEST_ZONE,
                fuel_type="import",
                pmax_mw=cap,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=mc,
                emission_rate_co2=0.0,
                eford=0.0,
            )
        )
        availability[_uid(fuel)] = avail

    # Dispatchable thermal: full nameplate available, priced at HR x hub + VOM.
    for fuel in _THERMAL_UNITS:
        gens.append(
            Generator(
                unit_id=_uid(fuel),
                name=f"WECC_West_{fuel}",
                zone=WECC_WEST_ZONE,
                fuel_type="import",
                pmax_mw=_WEST_NAMEPLATE_MW[fuel],
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=_thermal_mc(fuel, henry_hub_price),
                emission_rate_co2=0.0,
                eford=0.0,
            )
        )

    return gens, availability, demand_mw


# Tie-capacity weights for the single-node West export hub blend (caiso-114). The
# aggregate WECC_import node exports over two corridors to two CA zones; its one
# LMP is priced at a tie-capacity-weighted blend of the two corridors' measured
# neighbor hubs. Rule-14 reconciled real data: the reduced network collapses two
# parallel paths into one node, so a single blended delivered price is preferred
# over a pure guess or an arbitrary single-hub pick. Source: _caiso_config
# TransferLinks / WECC Path Rating Catalog — Path 66/COI 4,800 MW -> MALIN (PNW),
# Path 46/WOR 10,623 MW -> PALOVRDE (desert-SW). (Both hubs' congestion/loss make
# them differ; the desert-SW WOR path is the larger, so the blend leans PALOVRDE.)
_WECC_EXPORT_TIE_MW: dict[str, float] = {"MALIN": 4800.0, "PALOVRDE": 10623.0}


def west_delivered_hub_blend(year: int, hours: int) -> np.ndarray | None:
    """Tie-capacity-weighted blend of the measured MALIN + PALOVRDE intertie LMPs.

    The single aggregate WECC_import node's delivered West energy price at the CA
    border: a tie-weighted blend (``_WECC_EXPORT_TIE_MW``) of the two corridor
    neighbor hubs' measured hourly LMP (energy+congestion+loss, GHG-excluded).
    Reuses :func:`market_sim.data.eia930.envelopes.measured_import_hub_prices`
    (which gap-fills the 2023 Jan-Feb OASIS-retention window with the sanctioned
    forward corridor reference price — rule 14) and picks one filled series per
    hub via :data:`CAISO_IMPORT_TRANCHE_HUB`.

    Returns ``(hours,)`` $/MWh, or ``None`` when the measured series is
    unavailable (forecast years / pre-OASIS-fetch) — in which case the caller
    keeps the Henry-Hub ``vom`` (the West thermal falls back to its bare gas MC).
    """
    from market_sim.config.interchange_config import CAISO_IMPORT_TRANCHE_HUB
    from market_sim.data.eia930.envelopes import measured_import_hub_prices

    tranche_series = measured_import_hub_prices("CAISO", year, hours)
    if not tranche_series:
        return None
    hub_series: dict[str, np.ndarray] = {}
    for tranche, series in tranche_series.items():
        hub = CAISO_IMPORT_TRANCHE_HUB.get(tranche)
        if hub in _WECC_EXPORT_TIE_MW and hub not in hub_series:
            hub_series[hub] = np.asarray(series, dtype=float)
    if not hub_series:
        return None
    weight = sum(_WECC_EXPORT_TIE_MW[h] for h in hub_series)
    blend = sum(_WECC_EXPORT_TIE_MW[h] * s for h, s in hub_series.items()) / weight
    return blend[:hours]


def build_wecc_west_thermal_mc(
    year: int,
    henry_hub_price: float,
    carbon_price: float,
    hours: int = HOURS_PER_YEAR,
) -> dict[str, np.ndarray]:
    """Hour-varying delivered-cost override for the West GAS export units (caiso-114).

    THE caiso-110 diagnostic fix: pricing the West thermal on bare Henry-Hub gas
    MC ($17-20 in 2024) under-prices the West by ~$15-25 vs its measured
    wholesale hub, so the tie floods (net import 57 TWh vs actual 32, pinned at
    the +7.5 GW export limit in 83% of hours). Re-anchor the West's GAS units to
    the MEASURED delivered West energy cost at the CA border, hour-varying:

        offer_f[t] = hub_blend[t]                      # delivered West energy
                     + (f_nominal - gas_cc_nominal)    # physical HR/VOM premium
                     + border_adder x (EF_f / EF_unspec)   # CARB border carbon

    where ``hub_blend`` is the tie-weighted measured intertie LMP
    (:func:`west_delivered_hub_blend`, GHG-excluded), the physical premium keeps
    the West gas merit order (gas_cc marginal, gas_ct the peaker above it), and
    the CARB border adder is the SAME statutory import wedge the static DSW_CCGT /
    DSW_CT tranches pay (``IMPORT_TRANCHE_EF`` 0.37 / 0.55 over the unspecified
    0.428, x ``wecc_border_carbon_adder``). The all-in result is the true
    delivered cost CA pays for a marginal West gas import — LOW in the belly
    (self-limiting the belly over-import) and HIGH in the evening ramp (CA runs
    its own gas). Every term is a MEASURED / statutory input that regenerates for
    a forward year (the forward corridor reference price is the hub's forward
    analogue; the EFs + allowance are policy inputs) — 0 params fitted to the
    CAISO residual (rule 1 / rule 13 / rule 25).

    Coal is deliberately NOT overridden: it is West baseload, ~never the marginal
    export unit (the West is gas-marginal in ~100% of export hours), so it keeps
    its physical PRB ``vom`` and its exact offer is immaterial.

    Args:
        year: backcast year (2023-2025).
        henry_hub_price: the run's Henry Hub gas price ($/MMBtu).
        carbon_price: the CA allowance price ($/t) for the border adder.
        hours: LP horizon (8760).

    Returns:
        ``{unit_id: (hours,) $/MWh}`` for the two West GAS units, or ``{}`` when
        the measured hub is unavailable (caller keeps the Henry-Hub ``vom``).
    """
    from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
    from market_sim.model.interchange import wecc_border_carbon_adder
    from market_sim.model.interchange.spec import IMPORT_TRANCHE_EF

    hub = west_delivered_hub_blend(year, hours)
    if hub is None:
        return {}
    border = wecc_border_carbon_adder(carbon_price)
    ef_map = IMPORT_TRANCHE_EF.get("CAISO", {})
    gas_cc_nom = _thermal_mc("gas_cc", henry_hub_price)
    gas_ct_nom = _thermal_mc("gas_ct", henry_hub_price)
    # CARB border carbon per unit (the West gas export pays the CA import wedge,
    # matching the static DSW_CCGT / DSW_CT tranches; EF over the unspecified base).
    carb_cc = border * (
        ef_map.get("DSW_CCGT", CARB_UNSPECIFIED_IMPORT_EF) / CARB_UNSPECIFIED_IMPORT_EF
    )
    carb_ct = border * (
        ef_map.get("DSW_CT", CARB_UNSPECIFIED_IMPORT_EF) / CARB_UNSPECIFIED_IMPORT_EF
    )
    return {
        f"{WECC_WEST_PREFIX}gas_cc": hub + carb_cc,
        f"{WECC_WEST_PREFIX}gas_ct": hub + (gas_ct_nom - gas_cc_nom) + carb_ct,
    }


def is_wecc_west_unit(unit_id: str) -> bool:
    """True for an endogenous-West pseudo-generator (by unit_id prefix)."""
    return str(unit_id).startswith(WECC_WEST_PREFIX)
