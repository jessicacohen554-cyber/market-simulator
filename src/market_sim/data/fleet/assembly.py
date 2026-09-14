"""Fleet assembly: ``bins_to_fleet``, ``build_base_fleet``, ``build_dispatch_fleet``.

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

from market_sim.config.constants import (
    CAMPD_BINNING_ISOS,
    CC_ECON_HR_OVERRIDE_DEFAULT,
    CC_PEAK_HR_OVERRIDE_DEFAULT,
    CHP_BTM_PCT_BY_SECTOR,
    GAS_ST_ECON_HR_OVERRIDE_DEFAULT,
    GAS_ST_PEAK_HR_OVERRIDE_DEFAULT,
    HOURS_PER_YEAR,
    ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO,
    ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO,
    START_YEAR,
)
from market_sim.config.iso_configs import ISOConfig
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.chp import (
    chp_btm_pct,
    chp_class_netgen_mwh,
    chp_pmin_cf,
)
from market_sim.data.coal import (
    COAL_PLANT_SUPPLY,
    _COAL_CHP_FLOOR_CAP_PCT,
    _COAL_CHP_FLOOR_FACTOR,
    coal_chp_overrides,
    coal_supply_class,
    coal_sync_online_frac,
    coal_takeorpay_share,
)
from market_sim.data.offer_curves import (
    GAS_OFFER_MARGIN_FUELS,
    _econ_curve_steps,
    _econ_split_for_group,
    _hr_override,
    _offer_curve_for_group,
    band_margin_anchor,
    gas_offer_margin_markup_mult,
    split_gas_tranches,
)
from market_sim.data.outages import ST_GAS_PEAKER_PLANTS
from pathlib import Path
from market_sim.data.fleet.models import (
    FleetArrays,
    Generator,
)
from market_sim.data.fleet.eia860 import (
    eia860_plant_states,
    BIN_GROUP_TO_FUEL,
    BIN_STARTUP_COST_PER_MW,
    CC_REGULAR_COMMITTED_PCT_BY_PLANT,
    COAL_BIN_MIN_DOWN_HOURS,
    COAL_BIN_MIN_RUN_HOURS,
    COAL_PLANT_COMMISSION_YEAR,
    PETRA_NOVA_MIN_CF,
    PETRA_NOVA_PARASITIC_PCT,
    PETRA_NOVA_PLANT_CODE,
    eia860_selfcommit_scope_plants,
    get_eford,
    get_emission_rate,
    get_nox_rate,
    get_vom,
)
from market_sim.data.fleet.campd_bins import (
    assert_thermal_tranche_coverage,
    campd_ct_run_lengths,
    cc_duct_burner_peak_mult,
    cc_duct_peaking_pct,
    coal_prb_committed_split_night,
    load_plant_registry,
    load_plant_tranche_config,
    oil_primary_bin_plants,
    oil_primary_ct_plants_from_eia860,
    thermal_tranche_chp_steam_level,
    thermal_tranche_peaking,
)
from market_sim.data.fleet.arrays import generators_to_fleet_arrays
from market_sim.data.fleet.legacy_bins import _AGGREGATABLE_FUELS
from market_sim.data.fleet.models import _pkg_ns

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")

#: Minimum capacity (MW) a stepped tranche must carry to become an LP row.
#: Long-standing assembly behaviour — a tranche at or below this is DROPPED, so
#: rounding dust never becomes a generator. Named at ercot-188 (rule 5
#: ``[R-NO-MAGIC]``) because the ercot-188 top-refinement has to reason about it
#: rather than trip over it: re-slicing the econ ramp's top block ``n`` ways
#: makes each sub-slice ``curve_cap / n**2``, which falls under this floor for a
#: small enough plant and would then delete real capacity instead of refining
#: it. See :func:`_top_refine_ok`.
MIN_TRANCHE_CAPACITY_MW = 0.5


def _top_refine_ok(curve_cap: float, n: int, enabled: bool) -> bool:
    """Return whether SCHEME R1 can be applied to a ramp of ``curve_cap`` MW.

    ercot-188 Amendment 1, a **feasibility precondition, not a scheme variant**
    (``docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md``
    Amendment 1). ``_econ_curve_steps(top_refine=True)`` cuts the ramp's top
    block into ``n`` sub-slices of ``curve_cap / n**2`` each. Where that lands
    at or below :data:`MIN_TRANCHE_CAPACITY_MW` the assembly's own tranche
    filter drops **every one of them**, so the plant silently loses the whole
    top sixth of its econ ramp — measured on the real ERCOT fleet before this
    guard existed: 36 of 144 plant-groups truncated (``slice_counts`` ``[5, 11]``,
    max per-group deviation exactly 1/6) and **40.27 MW of capacity deleted** in
    every year. Refining a curve must never delete capacity from it.

    The guard adds **no free parameter** (rule 23 ``[R-DOF]``): the threshold is
    the assembly's own pre-existing minimum-tranche capacity, and the scheme
    itself is untouched — a plant either carries R1 exactly, or keeps the coarse
    equal-width form byte-identically.

    Args:
        curve_cap: The econ ramp's total capacity for this plant (MW).
        n: ``offer_curve_smoothing_n``, the coarse slice count.
        enabled: The resolved ERCOT-gated ``ercot_econ_curve_top_refine``.

    Returns:
        True when every R1 sub-slice would clear the minimum tranche capacity.
    """
    if not enabled or n <= 1:
        return False
    return curve_cap / float(n * n) > MIN_TRANCHE_CAPACITY_MW


def bins_to_fleet(
    bins: pd.DataFrame,
    zone_names: list[str],
    config: ScenarioConfig,
) -> tuple[list[Generator], FleetArrays]:
    """Convert per-plant CAMPD bins into LP generators -- stepped tranches.

    Each input row is one EIA plant ("one bin per plant"); its
    grid-facing capacity is split into LP-dispatchable tranches keyed to
    the CSV percentages and per-tranche heat rates. A bin only gets
    tranches whose capacity is non-zero:

      - ``_mustrun`` -- COAL ONLY. The unit's minimum operating floor:
        mine-mouth take-or-pay, start/stop and cycling damage avoidance,
        environmental minimum-gen / CEMS compliance and ERCOT RUC. Bids
        at VOM + carbon + NOx only (the fuel cost is sunk) via fuel_fracs
        in the runner, so it is always in merit without a Pmin floor.
        Non-coal bins' must-run share is host-steam (CHP) cogen and is
        removed from LP capacity -- it serves industrial process steam,
        not the grid; its generation and emissions are added back by
        post-processing (see
        :func:`market_sim.results.emissions.compute_must_run_emissions`).
      - ``_committed`` -- the part-load range when started. Carries the
        bin's start cost and min-run window -- starting this tranche is
        starting the plant.
      - ``_econ`` -- incremental dispatch above the part-load range, the
        most efficient slice of the unit.
      - ``_peak`` -- duct-firing / overfire tranche, heat rate scaled by
        the CSV's ``HR_Mult_Peaking`` so scarcity output bids highest.

    Per-tranche heat rates are the plant's own ``Plant_Avg_HR`` scaled by
    the CSV ``HR_Mult_<tranche>`` columns — assembled in
    :func:`load_campd_bins` — so each plant brings its measured heat rate
    and OEM-typical part-load / peaking penalties into the LP. No tranche
    carries a Pmin floor; the Committed and Economic tranches are the
    same physical unit, so the P2 commitment screen starts and stops them
    together (see
    :func:`market_sim.model.commitment.apply_commitment_with_coal_pin`).
    Economic and Peaking are incremental loading of a running unit, so
    they carry neither a start cost nor a min-run window.

    Args:
        bins: The per-plant frame from :func:`load_campd_bins` (one row
            per plant).
        zone_names: The ISO's ordered zone names.
        config: Scenario configuration (unknown-zone default, registry
            path, horizon length).

    Returns:
        A tuple ``(generators, fleet_arrays)``: the bin-derived generator
        list and its vectorized form.
    """
    valid_zones = set(zone_names)
    fleet: list[Generator] = []

    # Arm-over-gap preflight (xiso-6): a per-plant tranche gate armed at an
    # ISO whose committed thermal_tranches_<ISO>.csv predates the consumed
    # column's emitting vintage would engage on nothing — the loaders skip
    # blank rows silently — and read as inert on the merits. Hard error here,
    # at the one seam every CAMPD-binned fleet build passes through, before
    # any tranche is assembled. No-op unless a guarded gate is armed (all
    # default off; measured a no-op at all six current keepers).
    assert_thermal_tranche_coverage(getattr(config, "iso", "ERCOT") or "ERCOT", config)

    # nyiso-109 zone-resolved gas-offer margin anchors. Empty (and byte-
    # identical) unless the gate is armed; armed without the resolved map is a
    # hard error, never a silent fallback to the ISO window anchor (rule 24).
    _zonal_margin_anchors: dict[str, float] = {}
    if getattr(config, "gas_offer_margin_zonal_anchor", False):
        if not getattr(config, "gas_offer_net_revenue_margin", False):
            raise ValueError(
                "gas_offer_margin_zonal_anchor is armed without "
                "gas_offer_net_revenue_margin: the zonal anchor resolves the "
                "SAME mechanism's identification point, it is not a mechanism "
                "of its own (rule 19 [R-ONE-MECH])"
            )
        _by_zone = getattr(config, "gas_offer_margin_anchor_by_zone", None)
        if not _by_zone:
            raise ValueError(
                "gas_offer_margin_zonal_anchor is armed but "
                "gas_offer_margin_anchor_by_zone is unset; resolve it from "
                "constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE at config build "
                "(rule 24 — no silent fallback in the offer path)"
            )
        _zonal_margin_anchors = {str(z): float(a) for z, a in _by_zone.items()}

    # Per-plant commission years drive the age-based thermal availability
    # model. Coal uses the curated COAL_PLANT_COMMISSION_YEAR (accurate
    # coal-unit years); every other plant takes its EIA-860 ``year_built``
    # from the master plant registry. Plants absent from the registry fall
    # back to 2010 — a recent-but-not-modern vintage.
    registry = load_plant_registry(config.plant_registry_path)
    _reg_year = dict(zip(registry["plantid"], registry["year_built"]))

    # Oil-primary fuel correction: EIA-860 Petroleum-Liquids combustion-turbine
    # peakers (e.g. Morgan Creek 3492) sit in the gas CT_PEAKER class on the bin
    # sheet but physically burn distillate, so the LP otherwise prices them on
    # cheap Waha gas and floats them baseload. When enabled, their gas-CT fuel
    # is overridden to ``oil`` (priced at OIL_PRICE_PER_MMBTU) — a measured
    # EIA-860 correction, not a residual adder. Restricted to gas_ct so legacy
    # gas steam/CC bins are never reclassified. See oil_primary_bin_plants.
    # Two measured EIA-860 layers: ERCOT keeps its curated master-registry
    # plant-primary screen exactly (its keepers were solved on it — a silent
    # set change here would break their reproducibility, the 0c6c833 failure
    # mode); the per-plant non-ERCOT ISOs, which the registry cannot cover,
    # use the generator-level Energy-Source-1 majority screen
    # (oil_primary_ct_plants_from_eia860) instead.
    _oil_primary_iso = getattr(config, "iso", "ERCOT") or "ERCOT"
    _oil_primary = (
        (
            oil_primary_bin_plants(config.plant_registry_path)
            if _oil_primary_iso == "ERCOT"
            else oil_primary_ct_plants_from_eia860(_oil_primary_iso)
        )
        if getattr(config, "oil_primary_bin_fuel", False)
        else frozenset()
    )

    # Fast-start amortization v3 (tranche_startup_measured_runs): per-plant
    # CAMPD-measured median CT start-to-stop run lengths, the measured
    # amortization-horizon ceiling for the fast-start CT tranches. Empty when
    # the flag is off or the ISO has no committed artifact (v2 P0 basis).
    _fsp_run_lengths: dict[int, float] = (
        campd_ct_run_lengths(getattr(config, "iso", "ERCOT"))
        if (
            getattr(config, "tranche_startup_amortization", False)
            and getattr(config, "tranche_startup_measured_runs", False)
        )
        else {}
    )

    # Optional per-plant tranche-config override sheet: when set, each listed
    # plant's tranche shares + per-band HR multipliers come straight from the
    # sheet, bypassing the offer curve and the per-plant committed/peaking dicts.
    tranche_ov: dict[int, dict[str, float]] = {}
    _ov_path = getattr(config, "plant_tranche_config_path", None)
    if _ov_path:
        tranche_ov = load_plant_tranche_config(_ov_path)

    # ScenarioConfig.coal_prb_committed_split (miso-112): per-plant measured
    # within-run night loading levels for the regulated-PRB committed-band
    # split. Per-ISO artifact ⇒ self-scoping (rule 25); the regulated set is
    # the same one that scopes the committed-band take-or-pay discount.
    _prb_split_night: dict[int, float] = (
        coal_prb_committed_split_night(getattr(config, "iso", "ERCOT") or "ERCOT")
        if getattr(config, "coal_prb_committed_split", False)
        else {}
    )
    _prb_split_reg: frozenset[int] = (
        eia860_selfcommit_scope_plants() if _prb_split_night else frozenset()
    )

    # commission_year_cod_fallback (miso-159, rules 5 [R-NO-MAGIC] / 14
    # [R-ACCURATE]): the master registry above is ERCOT-only (833 rows, all
    # ba_code='ERCO'), so on every other per-plant ISO the 2010 fall-through
    # below is TOTAL and the whole fleet is stamped one vintage — which makes
    # the age-escalation limb of THERMAL_AVAILABILITY identically inert
    # (miso-157 §7: MISO 108.70 GW / 7 classes all at online_year=2010 against
    # true cap-weighted vintages 1976.8–2006.5). When armed, a registry-missed
    # plant takes its capacity-weighted EIA-860 COD year from load_cod_map() —
    # the same single COD source that already drives the backcast monthly
    # online mask, so mask and age model finally read one measured record
    # (rule 19 [R-ONE-MECH]). Registry hits keep precedence; 2010 remains only
    # for plants absent from both sources (0.0–0.6% of capacity, miso-158).
    _cod_years: dict[int, int] = {}
    if config.commission_year_cod_fallback:
        from market_sim.data.cod_ramp import load_cod_map

        _cod_years = {code: int(entry[0]) for code, entry in load_cod_map().items()}

    def _commission_year(plant_code: int) -> int:
        """Return the EIA-860 commission year for ``plant_code``."""
        year = _reg_year.get(plant_code)
        if year and not pd.isna(year):
            return int(year)
        cod_year = _cod_years.get(plant_code)
        if cod_year is not None:
            return cod_year
        return 2010

    # Coal cogens (PJM): a coal plant whose EIA-860 sector is a CHP host follows
    # its host steam contract, not the LMP, so its coal bin is routed through the
    # same behind-the-meter / steam-following holdout as the gas cogens — host
    # self-supply removed from the LP, the grid remainder a must-run floor —
    # rather than dispatched as an economic COAL_BIT/WC tranche. Keyed by plant
    # code -> (measured min-month avg MW floor, sector class). Empty unless the
    # CHP machinery is on and the ISO is PJM.
    coal_chp = (
        coal_chp_overrides(
            getattr(config, "iso", "ERCOT"),
            int(getattr(config, "weather_year", 0) or 0),
        )
        if getattr(config, "chp_steam_following", False)
        else {}
    )

    # Measured steam-following export level (backcast overlay,
    # config.chp_export_floor_measured): the year's per-(plant, class) EIA-923
    # net generation, which replaces the pooled CAMPD p2 minimum as the CHP
    # total must-run CF below — see the ScenarioConfig field for the physics
    # and the rule-#13 admissibility argument. Empty (no override) in forecast
    # mode or when the flag is off.
    chp_measured_netgen: dict[tuple[int, str], float] = {}
    if (
        getattr(config, "chp_steam_following", False)
        and getattr(config, "chp_export_floor_measured", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and int(getattr(config, "weather_year", 0) or 0) > 0
    ):
        chp_measured_netgen = chp_class_netgen_mwh(
            int(getattr(config, "weather_year", 0) or 0)
        )

    # Iterate as record dicts rather than ``iterrows()``: the per-row ``b["col"]``
    # / ``b.get(col, default)`` access below is unchanged, but ``to_dict`` skips
    # building a fresh per-row Series (and the object-dtype upcast) hundreds of
    # times per fleet build. Every cell is coerced via ``int``/``float``/``str``
    # at point of use, and pandas 3.0 ``to_dict("records")`` preserves NaN (not
    # None), so the ``... or label`` fallbacks resolve identically — byte-neutral.
    # caiso-243 (repair form (c), defect D1): the plant's USPS state from the
    # EIA-860 plant table, stamped on every tranche row so the F923 fallback's
    # documented state-first donor tier is reachable. Before this gate no
    # generator built here carried a state at all (the field defaulted to "")
    # and the tier — the only one with a donor-count guard — was skipped on
    # every plant-level fleet. Off by default: byte-identical fleets.
    _plant_states = (
        eia860_plant_states()
        if bool(getattr(config, "fleet_state_from_eia860", False))
        else {}
    )
    for b in bins.to_dict("records"):
        pct_mr = float(b["pct_mr"])
        nameplate = float(b["capacity_mw"])
        fuel = BIN_GROUP_TO_FUEL[b["Plant_Group"]]
        # Reprice EIA-860 oil-primary combustion-turbine peakers on distillate
        # (only gas_ct bins, so gas steam/CC are untouched and coal can never
        # flip). plant_group stays CT_PEAKER, so reserve/offer-curve logic is
        # unchanged — only the burned fuel changes.
        if fuel == "gas_ct" and int(b["Plant_Code"]) in _oil_primary:
            fuel = "oil"
        ov = tranche_ov.get(int(b["Plant_Code"]))
        # Coal must-run override (calibration): per-plant CAMPD-derived floor
        # (config.coal_mustrun_per_plant) takes precedence; otherwise the
        # uniform lignite/PRB supply override (sweep). The grid tranches
        # rescale via `denom`.
        if fuel == "coal":
            _pc = int(b["Plant_Code"])
            _supply = COAL_PLANT_SUPPLY.get(_pc, "")
            if config.coal_mustrun_per_plant and _pc in _pkg_ns().COAL_MUSTRUN_BY_PLANT:
                pct_mr = _pkg_ns().COAL_MUSTRUN_BY_PLANT[_pc]
            elif (
                _supply == "lignite"
                and config.coal_lignite_mustrun_override is not None
            ):
                pct_mr = config.coal_lignite_mustrun_override
            elif _supply == "prb" and config.coal_prb_mustrun_override is not None:
                pct_mr = config.coal_prb_mustrun_override
            # PJM bituminous spot-coal: NOT mine-mouth take-or-pay, so it is the
            # marginal/price-responsive swing fuel rather than held-flat
            # baseload. Zeroing its must-run floor moves all of its capacity into
            # the rising offer-curve tranches (committed/econ/peak, Pmin=0),
            # which bid full delivered cost (coal_bit_passthrough_floor=1.0) and
            # back down when gas undercuts them. Faithful to the contract physics
            # (CLAUDE.md #1/#11), not tuned to a coal-MWh residual; PRB/lignite/
            # waste keep their take-or-pay floors above.
            if (
                getattr(config, "coal_bit_dispatchable", False)
                and coal_supply_class(_pc) == "bituminous"
            ):
                pct_mr = 0.0
        # Coal cogen: a coal bin at a CHP-host plant (Eastman, St Nicholas, John
        # B Rich, ...) is held out at its sector behind-the-meter share and
        # carries a measured steam-following grid floor instead of staying in the
        # LP as economic coal. ``coal_chp_floor_mw`` (measured min-month avg MW)
        # sizes the floor below; the merchant CFB / culm fleet (sector 1/2) is
        # absent from ``coal_chp`` and keeps its in-LP coal must-run tranche.
        coal_chp_floor_mw: float | None = None
        coal_chp_sector: str | None = None
        if fuel == "coal" and int(b["Plant_Code"]) in coal_chp:
            coal_chp_floor_mw, coal_chp_sector = coal_chp[int(b["Plant_Code"])]
            pct_mr = CHP_BTM_PCT_BY_SECTOR.get(
                coal_chp_sector, CHP_BTM_PCT_BY_SECTOR["merchant"]
            )
        # Steam-following cogen treatment: a CC_CHP bin's behind-the-meter host
        # self-supply (removed from the grid, added back in the report) is
        # chp_btm_floor_pct of nameplate, not the CSV Pct_Must_Run merchant
        # split. Overriding pct_mr here shrinks the removed share and grows the
        # grid-facing capacity, which the steam floor + expensive load-following
        # below then shape into base + dispatchable rather than a flat slab.
        chp_following = str(b["Plant_Group"]) in (
            "CC_CHP",
            "CT_CHP",
            "ST_CHP",
        ) and getattr(config, "chp_steam_following", False)
        if chp_following:
            pct_mr = chp_btm_pct(
                int(b["Plant_Code"]),
                str(b["Plant_Group"]),
                iso=getattr(config, "iso", "ERCOT"),
                per_unit=bool(getattr(config, "campd_per_unit_attribution", False)),
                merit_guard=bool(
                    getattr(config, "campd_outage_merit_order_guard", False)
                ),
            )
            # nyiso-147: replace the sector-keyed default with the plant's
            # own measured Gold-Book/EIA-923 grid-delivery share where the
            # rule-23 artifact carries it (rule 14 [R-ACCURATE] — the
            # "merchant" 35% default is refuted by the market meter for the
            # large NYISO merchant cogens; Sithe Independence measured ~0).
            if (
                getattr(config, "nyiso_chp_btm_measured", False)
                and getattr(config, "iso", "ERCOT") == "NYISO"
            ):
                from market_sim.data.chp import measured_chp_btm_pct_nyiso

                _measured = measured_chp_btm_pct_nyiso()
                if int(b["Plant_Code"]) in _measured:
                    pct_mr = _measured[int(b["Plant_Code"])]
        # Petra Nova runs on its own classification (see PETRA_NOVA_* above):
        # one tranche at the capture train's net capacity, forced to
        # PETRA_NOVA_MIN_CF whenever the outage overlay says it is up. No
        # offer-curve bands — the 45Q credit makes it insensitive to price.
        if chp_following and int(b["Plant_Code"]) == PETRA_NOVA_PLANT_CODE:
            _pn_zone = str(b["ERCOT_Zone"])
            if _pn_zone == "Unknown" or _pn_zone not in valid_zones:
                _pn_zone = config.unknown_zone_default
            _pn_cap = nameplate * (1.0 - PETRA_NOVA_PARASITIC_PCT / 100.0)
            _pn_hr = float(b["hr_weighted"])
            fleet.append(
                Generator(
                    unit_id=f"CT_CHP_{_pn_zone}_p{PETRA_NOVA_PLANT_CODE}_ccs",
                    name=f"{b.get('Plant_Name', 'Petra Nova')} ccs",
                    zone=_pn_zone,
                    fuel_type=BIN_GROUP_TO_FUEL["CT_CHP"],
                    efficiency_bin="CT_CHP",
                    pmax_mw=_pn_cap,
                    pmin_mw=0.0,
                    heat_rate=_pn_hr,
                    vom=get_vom(BIN_GROUP_TO_FUEL["CT_CHP"]),
                    emission_rate_co2=get_emission_rate(
                        BIN_GROUP_TO_FUEL["CT_CHP"], _pn_hr
                    ),
                    nox_rate=get_nox_rate(BIN_GROUP_TO_FUEL["CT_CHP"]),
                    eford=get_eford(BIN_GROUP_TO_FUEL["CT_CHP"]),
                    online_year=_commission_year(PETRA_NOVA_PLANT_CODE),
                    is_campd_bin=True,
                    plant_group="CT_CHP",
                    bin_label=str(b["Bin_Label"]),
                    plant_code=PETRA_NOVA_PLANT_CODE,
                    state=_plant_states.get(PETRA_NOVA_PLANT_CODE, ""),
                    chp_grid_pmin_mw=PETRA_NOVA_MIN_CF * _pn_cap,
                )
            )
            continue
        if ov is not None:
            pct_mr = ov["pct_mr"]
        # Coal must-run capacity stays IN the LP as a ``_mustrun`` tranche
        # (its fuel is sunk under take-or-pay; bids at VOM + carbon + NOx
        # only via the runner). Non-coal bins' must-run share — and a coal
        # cogen's host self-supply — is removed from LP capacity; its generation
        # and emissions are added back by post-processing (the coal cogen via
        # _btm_frame, the gas CHP via compute_must_run_emissions).
        if fuel == "coal" and coal_chp_sector is None:
            mustrun_cap = nameplate * pct_mr / 100.0
            grid_cap = nameplate - mustrun_cap
        else:
            mustrun_cap = 0.0
            grid_cap = nameplate * (1.0 - pct_mr / 100.0)
        if grid_cap + mustrun_cap <= 0.0:
            continue

        # SRMC-priced synchronization split (rebuild step 3a,
        # config.coal_sync_srmc_tranche). The coal min-load band (sized to the
        # measured online Pmin under coal_mustrun_online_pmin) is split by the
        # measured contract share into a fuel-free contracted floor (_mustrun)
        # and a spot remainder priced at full SRMC (_sync). BOTH are forced on
        # below (coal_sync_pmin_mw -> min_gen) so the unit holds synchronized at
        # min-load instead of price-following to zero, while the dispatchable
        # tranches above still back down in cheap hours. The split preserves the
        # total min-load (mr + sync = original mustrun_cap), so grid_cap and the
        # tranches above are unchanged. Plants absent from the take-or-pay map
        # are treated as fully contracted (share=1.0): all min-load fuel-free,
        # no _sync band — the step-2 sizing, now forced on.
        coal_sync = (
            fuel == "coal"
            and coal_chp_sector is None
            and mustrun_cap > 0.0
            and getattr(config, "coal_sync_srmc_tranche", False)
            and getattr(config, "coal_mustrun_online_pmin", False)
        )
        sync_cap = 0.0
        sync_online_frac = 1.0
        if coal_sync:
            _share = coal_takeorpay_share(int(b["Plant_Code"]))
            _share = 1.0 if _share is None else min(1.0, max(0.0, float(_share)))
            sync_cap = mustrun_cap * (1.0 - _share)  # spot, full SRMC
            mustrun_cap = mustrun_cap * _share  # contracted, fuel-free
            # Online%-scaled forcing: the measured share of the year the plant is
            # synchronized. ~1.0 (supercritical) -> floor held all 8760 h; a
            # cycler -> floor held only in its top-load online hours. Plants
            # absent from the artifact keep the force-all default (1.0).
            sync_online_frac = coal_sync_online_frac(
                getattr(config, "iso", "ERCOT") or "ERCOT",
                bool(getattr(config, "campd_per_unit_attribution", False)),
                bool(getattr(config, "campd_outage_merit_order_guard", False)),
            ).get(int(b["Plant_Code"]), 1.0)

        group = str(b["Plant_Group"])
        plant_code = int(b["Plant_Code"])
        offer = _offer_curve_for_group(group, plant_code, config)
        # Committed-tranche % (minimum stable load once started). The CSV
        # Pct_Committed is a coarse assumed value; for CC_REGULAR plants with
        # CAMPD-observed minimum stable load it is replaced by the per-plant
        # grounded value (CC_REGULAR_COMMITTED_PCT_BY_PLANT) — the economic
        # tranche below absorbs the difference. Off unless the calibration
        # config sets cc_committed_per_plant.
        pct_mc = float(b["pct_mc"])
        if offer is not None and "pct_committed" in offer:
            pct_mc = float(offer["pct_committed"])
        if (
            group == "CC_REGULAR"
            and getattr(config, "cc_committed_per_plant", False)
            and plant_code in CC_REGULAR_COMMITTED_PCT_BY_PLANT
        ):
            pct_mc = CC_REGULAR_COMMITTED_PCT_BY_PLANT[plant_code]
        # Peaking %: the offer curve may override the CSV value before the
        # residual is split into the two economic steps (residual = 100 -
        # must_run - committed - peaking).
        pct_peak = float(b["pct_peak"])
        if offer is not None and "pct_peaking" in offer:
            pct_peak = float(offer["pct_peaking"])
        if group in ("CC_REGULAR", "CC_CHP") and getattr(
            config, "cc_peaking_per_plant", False
        ):
            # Per-plant CAMPD-derived duct-firing share from the ISO's
            # thermal-tranche artifact (thermal_tranche_peaking), superseding
            # the offer curve's class-wide pct_peaking; the hand-set ERCOT
            # map below stays the final word for its four plants.
            _pk = thermal_tranche_peaking(
                (getattr(config, "iso", "ERCOT") or "ERCOT"),
                bool(getattr(config, "campd_per_unit_attribution", False)),
                bool(getattr(config, "campd_outage_merit_order_guard", False)),
            ).get((plant_code, group))
            if _pk is not None:
                pct_peak = _pk
        if group in ("CC_REGULAR", "CC_CHP") and getattr(
            config, "cc_duct_peaking", False
        ):
            # Per-plant EIA-860 duct-burner peaking share: duct-fired plants
            # get their capability gap, non-duct CCs get 0 (no phantom
            # scarcity band). Supersedes the class-wide pct_peaking and the
            # tranche artifact above.
            _dpk = cc_duct_peaking_pct(
                bool(getattr(config, "cc_duct_peaking_row_scoped", False))
            ).get(plant_code)
            if _dpk is not None:
                # Cap the band at the F-class supplementary-firing physical
                # maximum: the raw nameplate-vs-net-summer gap folds the ambient
                # summer derate into the duct band, oversizing it for high-gap
                # plants and dropping the price wall below the real duct point.
                _cap = getattr(config, "cc_duct_peaking_cap_pct", None)
                pct_peak = min(_dpk, float(_cap)) if _cap is not None else _dpk
        if ov is not None:
            pct_mc, pct_peak = ov["pct_mc"], ov["pct_pk"]
        # RESERVE-DUTY split (cc_reserve_duty_split, nyiso-146): a CC plant in
        # the measured capacity-only cohort offers its WHOLE dispatchable
        # capacity at the class peak band. Applied LAST so it supersedes the
        # offer curve's class-wide pct_peaking, the per-plant peaking artifact
        # and the duct-burner map — the first solve of the arm measured all
        # three clobbering the fleet_to_bins frame values back to a normal
        # split (pct_peak 100 -> 8 -> duct 0.0), leaving the mechanism inert;
        # the frame-side seam stays for the synthesized-bins schema but THIS
        # is the load-bearing override. The peak band's heat rate resolves
        # exactly as the class's peak band does in this recipe (offer "peak"
        # mult or the duct-burner class multiplier) — an existing identified
        # constant either way, zero new scalars.
        if (
            group == "CC_REGULAR"
            and getattr(config, "cc_reserve_duty_split", False)
            and plant_code
            in _pkg_ns()._reserve_duty_cohort(str(getattr(config, "iso", "") or ""))
        ):
            pct_mc = 0.0
            pct_peak = 100.0 - pct_mr
        # CHP LAY-UP split (chp_layup_duty_split, nyiso-148): the cogeneration
        # sibling of the block directly above, and applied LAST for the SAME
        # reason — measured on this arm's first solve, the offer-curve mirror
        # alone left the mechanism HALF-applied: pct_mc reached 0 but pct_peak
        # was clobbered back by the tranche artifact / duct-burner map, so the
        # cohort kept a full econ band and its energy moved by < 3 % (the
        # nyiso-146b inert-solve defect, reproduced in a second leg and caught
        # by this arm's own D-K2 anti-inert gate). The frame-side seam in
        # fleet_to_bins stays for the synthesized-bins schema; THIS is the
        # load-bearing override. Zero new scalars — the peak band's heat rate
        # resolves exactly as the class's own peak band does in this recipe.
        if (
            group in _pkg_ns()._CHP_GROUPS
            and getattr(config, "chp_layup_duty_split", False)
            and plant_code
            in _pkg_ns()._chp_layup_cohort(str(getattr(config, "iso", "") or ""))
        ):
            pct_mc = 0.0
            pct_peak = 100.0 - pct_mr
        denom = 100.0 - pct_mr
        committed_cap = grid_cap * pct_mc / denom if denom > 0.0 else 0.0
        peak_cap = grid_cap * pct_peak / denom if denom > 0.0 else 0.0
        # The steam-following BTM substitution above can leave committed +
        # peaking exceeding the grid share (a cogen whose measured committed
        # floor is ~70% of nameplate against a 35% BTM pull-out, e.g. Elk
        # Hills / Marcus Hook); clamp into grid_cap — committed keeps its
        # measured level, the scarcity peak gives way — so the LP never
        # carries more capacity than the grid-facing share.
        if committed_cap + peak_cap > grid_cap:
            committed_cap = min(committed_cap, grid_cap)
            peak_cap = max(0.0, min(peak_cap, grid_cap - committed_cap))
        econ_cap = max(grid_cap - committed_cap - peak_cap, 0.0)
        # CHP LAY-UP duty CURVE (chp_layup_duty_curve, nyiso-149): the GRADED
        # successor to the single-band split above, applied LAST — and at the
        # CAP level, not the pct level, because the econ residual would
        # otherwise re-absorb the withheld share. A census plant offers its
        # measured price-conditional duty (chp_duty_curve_<ISO>.csv: pct_econ
        # of nameplate at the class econ band, pct_peak at the class peak
        # band — both derived from CAMPD on-share x loading conditional on
        # envelope-live hours, so the availability envelope and this offer
        # never double-count the same mothball spells, rule 19) and the
        # REMAINDER LEAVES THE OFFER ENTIRELY — energy and reserves: grid_cap
        # shrinks to the offered total, so the withheld trains back no
        # product (a mothballed train does not return for a price spike).
        # Zero new price constants: band heat rates resolve exactly as the
        # class's own bands do in this recipe (rule 21).
        if group in _pkg_ns()._CHP_GROUPS and getattr(
            config, "chp_layup_duty_curve", False
        ):
            _duty = (
                _pkg_ns()
                ._chp_duty_curve(str(getattr(config, "iso", "") or ""))
                .get(plant_code)
            )
            if _duty is not None and plant_code in _pkg_ns()._chp_layup_cohort(
                str(getattr(config, "iso", "") or "")
            ):
                # The duty is a MW quantity (s·L·HSL — basis-free), clamped
                # into the grid-facing share so the BTM hold-out is honored.
                # (The first solve applied pct-of-census-pmax fractions to
                # the BIN nameplate and over-offered by the basis ratio —
                # caught by gate F-K2, PREREG-nyiso149 §7.)
                committed_cap = 0.0
                peak_cap = min(_duty[1], grid_cap)
                econ_cap = min(_duty[0], grid_cap - peak_cap)
                grid_cap = committed_cap + peak_cap + econ_cap

        zone = str(b["ERCOT_Zone"])
        if zone == "Unknown" or zone not in valid_zones:
            zone = config.unknown_zone_default

        label = str(b["Bin_Label"])
        plant_name = str(b.get("Plant_Name") or label)
        # One bin = one plant, so the unit id is anchored on the plant
        # code; the tranche suffix keeps the four sub-generators distinct.
        bin_id = f"{group}_{zone}_p{plant_code}"
        # Exit-cohort bin (miso-191, PREREG-miso191 §1-§2): a synthesized bin
        # carrying its own retirement (fleet_to_bins' date-scoped cohort of
        # leg-1 partial-exit units) keeps the `_p{plant}_` token — every
        # plant-grain consumer still resolves the plant — and appends an
        # `_r{yyyy}{mm}` tag so its tranches never collide with the surviving
        # plant's. The retirement is stamped on each tranche Generator below;
        # cod_ramp.effective_cod prefers it over the plant-collapsed date, so
        # the cohort ages out on its real EIA-860 month. Absent (None/NaN)
        # on every ordinary row and on the ERCOT curated-CSV path.
        _b_ry = b.get("Retirement_Year")
        _b_rm = b.get("Retirement_Month")
        cohort_ry: int | None = (
            int(_b_ry) if _b_ry is not None and not pd.isna(_b_ry) else None
        )
        cohort_rm: int | None = (
            int(_b_rm) if _b_rm is not None and not pd.isna(_b_rm) else None
        )
        if cohort_ry is not None:
            bin_id = f"{bin_id}_r{cohort_ry}{(cohort_rm or 12):02d}"

        coal_supply = ""
        if fuel == "coal":
            coal_supply = coal_supply_class(plant_code)
            commission_year = COAL_PLANT_COMMISSION_YEAR.get(
                plant_code, _commission_year(plant_code)
            )
        else:
            commission_year = _commission_year(plant_code)
        startup = BIN_STARTUP_COST_PER_MW.get(group, 0.0)

        base_hr = float(b["hr_weighted"])
        mustrun_hr = float(b["hr_mr"])
        committed_hr = float(b["hr_mc"])
        econ_hr = float(b["hr_econ"])
        peak_hr = float(b["hr_peak"])
        if offer is not None:
            # Unified offer curve: committed and peaking band heat rates from
            # the multipliers (econ_low / econ_high are set in the econ split
            # below). The peak band is a separate flat tranche; its height is
            # the curve's "peak" multiplier when given, else (CC only) the
            # per-plant duct-burner multiplier by turbine class. VOM is held
            # constant across bands (the peak band's VOM markup is dropped).
            committed_hr = base_hr * float(offer["committed"])
            if "peak" in offer:
                peak_hr = base_hr * float(offer["peak"])
            elif group in ("CC_REGULAR", "CC_CHP"):
                peak_hr = base_hr * cc_duct_burner_peak_mult(b.get("Turbine_Class"))
            else:
                peak_hr = base_hr * float(offer["peak"])
        else:
            # Legacy per-class supply-curve overrides (relative to base HR),
            # used when no offer curve covers the group: CC committed/econ/peak,
            # reliability ST_GAS (peakers keep CSV heat rates), and CT_CHP.
            cc_mc = config.cc_committed_hr_override
            if group in ("CC_REGULAR", "CC_CHP") and cc_mc is not None:
                committed_hr = base_hr * cc_mc
                econ_hr = base_hr * _hr_override(
                    config.cc_econ_hr_override, CC_ECON_HR_OVERRIDE_DEFAULT
                )
                peak_hr = base_hr * _hr_override(
                    config.cc_peak_hr_override, CC_PEAK_HR_OVERRIDE_DEFAULT
                )
            # caiso-239 (ScenarioConfig.caiso_st_gas_committed_measured):
            # control reaches this `else` for an ST_GAS plant ONLY because
            # `_offer_curve_for_group` bypasses `offer_curve_by_group` for
            # every `ST_GAS_PEAKER_PLANTS` member, so its committed band falls
            # through to the UNCITED ERCOT-lineage class default
            # `campd_bins._DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"] = 1.15` —
            # an off-registry channel (rule 24 [R-REGISTRY]) carrying an
            # out-of-ISO fitted value (rule 25 [R-ISO-SCOPE]) on CAISO's whole
            # 2,858.8 MW OTC steam fleet (plants 315 / 335 / 350). Armed, the
            # band takes the ISO's own MEASURED min-load block-average burn
            # ratio instead — for CAISO `avg_committed_p50` = 1.683 over the
            # ten CAMPD units of exactly those three plants, so the statistic's
            # population and the band's population coincide (rule 14
            # [R-ACCURATE], zero free parameters, rule 21 [R-DOF]).
            #
            # EXACTLY ONE BAND: `mustrun_hr`, `econ_hr` and `peak_hr` keep
            # their class defaults, and the limb is unreachable for any plant
            # that resolves an offer curve. An ISO with no registry entry is a
            # HARD ERROR, never a silent fallback (rule 25).
            if group == "ST_GAS" and getattr(
                config, "caiso_st_gas_committed_measured", False
            ):
                _iso = str(getattr(config, "iso", "") or "").upper()
                _mult = ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO.get(_iso)
                if _mult is None:
                    raise ValueError(
                        "caiso_st_gas_committed_measured is armed for "
                        f"{_iso or '<unset>'}, which has no measured entry in "
                        "constants.ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO; "
                        "derive the ISO's own avg_committed_p50 first (rule 25 "
                        "[R-ISO-SCOPE] — no cross-ISO transfer, and no silent "
                        "fallback to the class default)"
                    )
                committed_hr = base_hr * float(_mult)
            # caiso-240 (ScenarioConfig.caiso_st_gas_peak_measured): the PEAK
            # sibling of the limb directly above, DISJOINT FROM IT BY BAND
            # (rule 19 [R-ONE-MECH]) -- that one moves `committed_hr` and this
            # one `peak_hr`, and neither touches the other's band. The caiso-240
            # census measured that after caiso-239 exactly two
            # `_DEFAULT_HR_MULT_BY_GROUP` cells stay live on the CAISO keeper,
            # `ST_GAS["econ"]` and `ST_GAS["peak"]`, both on the same three
            # bypassed steamers; `peak` is the one whose measured counterpart is
            # at the model's own grain (one flat multiplier against one measured
            # number), so it is the one repaired here.
            #
            # The value is the ISO's OWN measured peak-band offer multiplier --
            # for CAISO 1.166 = `CT_PEAKER.bands.peak` in the committed
            # caiso_offer_curve_measured.json, which is ALREADY the value the
            # CAISO ST_GAS class band carries on the keeper (armed at caiso-231
            # by caiso_offer_surface_measured_ungrounded). The class band simply
            # never reaches these plants, because `_offer_curve_for_group`
            # bypasses every ST_GAS_PEAKER_PLANTS member -- so the measurement
            # taken on a bucket that CONTAINS the steamers is withheld from the
            # steamers and applied instead to two retired-window units. Zero new
            # measurement, zero free parameters (rule 21 [R-DOF]).
            #
            # An ISO with no registry entry is a HARD ERROR, never a silent
            # fallback (rule 25 [R-ISO-SCOPE]).
            if group == "ST_GAS" and getattr(
                config, "caiso_st_gas_peak_measured", False
            ):
                _iso_pk = str(getattr(config, "iso", "") or "").upper()
                _pk_mult = ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO.get(_iso_pk)
                if _pk_mult is None:
                    raise ValueError(
                        "caiso_st_gas_peak_measured is armed for "
                        f"{_iso_pk or '<unset>'}, which has no measured entry "
                        "in constants.ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO; "
                        "derive the ISO's own measured peak band first (rule 25 "
                        "[R-ISO-SCOPE] — no cross-ISO transfer, and no silent "
                        "fallback to the class default)"
                    )
                peak_hr = base_hr * float(_pk_mult)
            st_mc = config.gas_st_committed_hr_override
            if (
                group == "ST_GAS"
                and plant_code not in ST_GAS_PEAKER_PLANTS
                and st_mc is not None
            ):
                committed_hr = base_hr * st_mc
                econ_hr = base_hr * _hr_override(
                    config.gas_st_econ_hr_override, GAS_ST_ECON_HR_OVERRIDE_DEFAULT
                )
                peak_hr = base_hr * _hr_override(
                    config.gas_st_peak_hr_override, GAS_ST_PEAK_HR_OVERRIDE_DEFAULT
                )
            # (A CT_CHP limb stood here on the ct_*_hr_override triple. Deleted
            # 2026-08-03, rule 26 [R-DELETE], nyiso-114: unreachable on every
            # committed bundle in every ISO — CT_CHP always resolves an offer
            # curve, so control never reaches this ``else``.)
        if ov is not None:
            # Per-plant sheet wins: all band heat rates are base_HR x the sheet's
            # multipliers (econ-low/-high set in the econ split below).
            mustrun_hr = base_hr * ov["hr_mr"]
            committed_hr = base_hr * ov["hr_mc"]
            peak_hr = base_hr * ov["hr_pk"]
        # CHP steam-following grid floor pinned onto the econ tranche: the
        # plant's total must-run (p2 CAMPD gross CF) net of its BTM share, i.e.
        # the steady export delivered to the grid above host self-supply. The
        # BTM share is a fraction of the plant's *generation* (host self-supply
        # scales with output, same basis the report add-back uses), so the
        # grid-delivered floor is pmin_cf * (1 - btm). Subtracting the BTM as
        # raw nameplate-percentage points zeroed the floor whenever a plant's
        # observed must-run ran below its BTM share (e.g. San Jacinto: pmin
        # 34.6 < BTM 40), leaving inefficient CT_CHP cogens to idle instead of
        # delivering their steady steam-following export. The floor comes from
        # the ISO's derived artifact (CAMPD p2, EIA-923 CF fallback) with the
        # hardcoded ERCOT CAMPD map behind it; plants with neither export
        # surplus only.
        chp_pmin_mw = 0.0
        pmin_cf = None
        if chp_following:
            pmin_cf = chp_pmin_cf(
                plant_code,
                iso=getattr(config, "iso", "ERCOT"),
                per_unit=bool(getattr(config, "campd_per_unit_attribution", False)),
                merit_guard=bool(
                    getattr(config, "campd_outage_merit_order_guard", False)
                ),
            )
            # Multi-year steam-host operating level (chp_steam_floor_p25):
            # the artifact's measured steam level supersedes the p2
            # never-below minimum wherever it is higher — since WP-3
            # (owner-ruled 2026-07-19) the loading-when-on construction for
            # CAMPD-visible cogens plus the EIA-923 delivery-implied level
            # for CEMS-invisible ones (see thermal_tranche_chp_steam_level
            # and the ScenarioConfig field for the rule-13/17 grounding).
            # The statistic self-targets: cycling cogens measure ~0 and keep
            # their p2/eia923_cf floor from above. Same grid formula and
            # MECH_CHP_STEAM attribution — a level source swap (rule 19),
            # not a second floor.
            if getattr(config, "chp_steam_floor_p25", False):
                _level = thermal_tranche_chp_steam_level(
                    getattr(config, "iso", "ERCOT") or "ERCOT",
                    bool(getattr(config, "campd_per_unit_attribution", False)),
                    bool(getattr(config, "campd_outage_merit_order_guard", False)),
                ).get((plant_code, group))
                if _level is not None and _level > (pmin_cf or 0.0):
                    pmin_cf = _level
            # Measured steam-following level (chp_export_floor_measured): the
            # plant's EIA-923 class CF for the solved year supersedes the
            # pooled CAMPD p2 minimum — the host-driven operating level the
            # steam contract sustains, not the never-below floor. The grid
            # floor formula below is unchanged (x (1 - btm share)), so the
            # forced export is exactly the measured total times the measured
            # sector grid-delivery share. Plants missing from the year's
            # 923 vintage keep the p2/artifact floor from above.
            _mtot = chp_measured_netgen.get((plant_code, group))
            if _mtot is not None and nameplate > 0.0:
                pmin_cf = min(100.0, 100.0 * _mtot / (nameplate * HOURS_PER_YEAR))
        elif coal_chp_sector is not None and coal_chp_floor_mw and nameplate > 0.0:
            # Coal cogen: the measured min-month average MW as a % of the coal
            # bin nameplate, scaled and capped the same way derive_thermal_tranches
            # sizes a CEMS-invisible cogen's EIA-923-CF floor.
            pmin_cf = min(
                _COAL_CHP_FLOOR_CAP_PCT,
                coal_chp_floor_mw / nameplate * 100.0 * _COAL_CHP_FLOOR_FACTOR,
            )
        if pmin_cf is not None:
            grid_mr_cf = max(0.0, pmin_cf * (1.0 - pct_mr / 100.0))
            floor_mw = grid_mr_cf / 100.0 * nameplate
            # The floor is carried by the econ slices, so it can be no
            # larger than the econ band. When the committed tranche leaves
            # too little econ room (CAMPD-grounded committed shares run
            # 45-65% on cogens), shift the shortfall from committed into
            # econ — total grid capacity is unchanged, and the always-on
            # steam base takes priority over how the dispatchable
            # remainder is banded.
            shift = min(max(0.0, floor_mw - econ_cap), committed_cap)
            committed_cap -= shift
            econ_cap += shift
            chp_pmin_mw = min(floor_mw, econ_cap)

        # Economic tranche(s). By default one tranche at econ_hr; the offer
        # curve (or the standalone econ split) replaces it with a rising
        # marginal-cost curve that spans ``econ_low -> econ_high`` only. When
        # ``offer_curve_smoothing_n`` is positive the curve is rendered as an
        # N-slice rising ramp (``_econ_curve_steps``) so the LP fills it
        # gradually as hourly price crosses MC, rather than snapping between two
        # wide flat blocks; when it is zero the curve stays two flat steps
        # (econ-low / econ-high). Every group spans econ-low to econ-high and
        # keeps the duct-firing / scarcity peak as a separate flat tranche
        # above the ramp. The first econ step carries any CHP steam-following
        # floor.
        n_curve = int(getattr(config, "offer_curve_smoothing_n", 0) or 0)
        curve_exp = float(getattr(config, "offer_curve_smoothing_exp", 1.0))
        _mid = getattr(config, "offer_curve_smoothing_mid", None)
        curve_mid = float(_mid) if _mid is not None else None
        # ercot-188 (c2) SCHEME R1: re-slice the econ ramp's TOP block n ways so
        # the supply curve can express a cliff (docs/PRECOMMIT-ercot188-cliff-
        # offer-curve-refinement-2026-08-11.md §2). GATED HERE, not inside
        # _econ_curve_steps, because that slicer is ISO-AGNOSTIC and every one of
        # the six keepers runs n = 6 — an ungated arm would silently re-slice all
        # six fleets at once (rule 25 [R-ISO-SCOPE]; MEMO-ercot184 §6). The
        # committed-band call site below deliberately does NOT read this.
        curve_top_refine = (
            bool(getattr(config, "ercot_econ_curve_top_refine", False))
            and getattr(config, "iso", None) == "ERCOT"
        )
        if ov is not None:
            # Per-plant sheet: the econ ramp spans econ-low to econ-high; the
            # sheet's peaking band stays a separate tranche below.
            lo_m, pk_m = ov["hr_lo"], ov["hr_hi"]
            curve_pct = ov["pct_lo"] + ov["pct_hi"]
            if n_curve > 0 and curve_pct > 0.0 and pk_m > lo_m:
                econ_steps = _econ_curve_steps(
                    base_hr,
                    lo_m,
                    pk_m,
                    nameplate * curve_pct / 100.0,
                    n_curve,
                    curve_exp,
                    curve_mid,
                    top_refine=_top_refine_ok(
                        nameplate * curve_pct / 100.0, n_curve, curve_top_refine
                    ),
                )
            else:
                econ_steps = [
                    (
                        "econlo",
                        nameplate * ov["pct_lo"] / 100.0,
                        base_hr * ov["hr_lo"],
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                    (
                        "econhi",
                        nameplate * ov["pct_hi"] / 100.0,
                        base_hr * ov["hr_hi"],
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                ]
        elif offer is not None:
            lo_m = float(offer["econ_low"])
            pk_m = float(offer["econ_high"])
            if n_curve > 0 and econ_cap > 0.0 and pk_m > lo_m:
                econ_steps = _econ_curve_steps(
                    base_hr,
                    lo_m,
                    pk_m,
                    econ_cap,
                    n_curve,
                    curve_exp,
                    curve_mid,
                    top_refine=_top_refine_ok(econ_cap, n_curve, curve_top_refine),
                )
            else:
                share = float(offer["econ_low_share"])
                econ_steps = [
                    ("econlo", econ_cap * share, base_hr * lo_m, 1.0, 0, 0, 0.0),
                    (
                        "econhi",
                        econ_cap * (1.0 - share),
                        base_hr * float(offer["econ_high"]),
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                ]
        elif (split := _econ_split_for_group(group, plant_code, config)) is not None:
            split_frac, lo_mult, hi_mult = split
            if n_curve > 0 and econ_cap > 0.0 and hi_mult > lo_mult:
                econ_steps = _econ_curve_steps(
                    base_hr,
                    lo_mult,
                    hi_mult,
                    econ_cap,
                    n_curve,
                    curve_exp,
                    curve_mid,
                    top_refine=_top_refine_ok(econ_cap, n_curve, curve_top_refine),
                )
            else:
                econ_steps = [
                    (
                        "econlo",
                        econ_cap * split_frac,
                        base_hr * lo_mult,
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                    (
                        "econhi",
                        econ_cap * (1.0 - split_frac),
                        base_hr * hi_mult,
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                ]
        else:
            econ_steps = [("econ", econ_cap, econ_hr, 1.0, 0, 0, 0.0)]
        # Spread the CHP steam-following grid floor across the econ slices in
        # fill order. Pinning it all on the first slice clips the floor to
        # that slice's capacity in generators_to_fleet_arrays (min_gen <=
        # pmax x availability): with the n=6 smoothing ramp a 185 MW floor
        # (Sweeny) collapsed to one ~57 MW slice, idling the steady steam-host
        # export the floor exists to force.
        chp_floor_by_suffix: dict[str, float] = {}
        _floor_rem = chp_pmin_mw
        for _suffix, _cap, *_rest in econ_steps:
            if _floor_rem <= 0.0:
                break
            _take = min(_floor_rem, _cap)
            chp_floor_by_suffix[_suffix] = _take
            _floor_rem -= _take

        # Stepped tranches: (suffix, capacity, heat rate, VOM multiplier,
        # min-run, min-down, start cost). Only the Committed tranche is
        # screened and carries the start cost; Must-Run, Economic and Peaking
        # are incremental output of an already-running plant. No tranche
        # carries a Pmin floor — the Must-Run tranche is forced on by bidding
        # at VOM only (fuel_fracs in the runner).
        # Peak-band VOM multiplier: the offer curve holds VOM constant across
        # bands (band MC = VOM + (AHR x fuel) x mult); the legacy path keeps
        # the 1.5x peak VOM markup. The peak is always a separate flat tranche
        # that jumps up above the econ-low -> econ-high ramp.
        peak_vom_mult = 1.0 if offer is not None else 1.5
        # Committed band: a single flat block by default. With
        # ``committed_ramp_spread`` > 0 it is rendered as an n-slice rising
        # ramp spanning committed_mult x (1 +/- spread), so the plant clears
        # its committed capacity progressively as price rises rather than
        # snapping from 0 to the full committed share in one step (the
        # bimodal-dispatch / under-populated mid-CF-band artifact). The mean
        # bid is unchanged, so class volume is ~preserved; only the operating
        # -level distribution smooths. The first slice stays the screened
        # anchor — it carries the min-run / min-down / start cost and (below)
        # the must_run_pct / bin_nameplate tags — so commitment coupling and
        # the BTM add-back are unaffected.
        # Min-run / min-down for the commitment screen: the bin's measured value
        # when present (ERCOT carries 36/16 per-plant), else the physical coal-
        # boiler default for coal on ISOs whose bin sheet has no Min_Run column.
        # Non-coal keeps the bin value (0 when absent → screened on start cost
        # alone, no duration hysteresis). Only the first committed slice carries
        # it (the screened anchor).
        _bm = b["min_run"]
        _bd = b["min_down"]
        bin_min_run = 0 if pd.isna(_bm) else int(_bm)
        bin_min_down = 0 if pd.isna(_bd) else int(_bd)
        if fuel == "coal":
            if bin_min_run <= 0:
                bin_min_run = COAL_BIN_MIN_RUN_HOURS
            if bin_min_down <= 0:
                bin_min_down = COAL_BIN_MIN_DOWN_HOURS
        cr_spread = float(getattr(config, "committed_ramp_spread", 0.0) or 0.0)
        if cr_spread > 0.0 and committed_cap > 0.5 and n_curve > 0 and base_hr > 0.0:
            cmt_mult = committed_hr / base_hr
            cmt_steps = _econ_curve_steps(
                base_hr,
                cmt_mult * (1.0 - cr_spread),
                cmt_mult * (1.0 + cr_spread),
                committed_cap,
                n_curve,
                curve_exp,
                curve_mid,
                # NEVER curve_top_refine: the ercot-188 refinement is scoped to
                # the ECON ramp. This is the same slicer re-used for the
                # committed band, and MEMO-ercot184 §6 item 3 named the coupling
                # as a dormant hazard — every keeper runs committed_ramp_spread
                # 0.0 today, so an ISO that later arms it must not silently
                # inherit a slice count identified for a different band.
                top_refine=False,
            )
            committed_tranches = [
                (
                    ("committed" if i == 0 else f"committed{i:02d}"),
                    _cap,
                    _hr,
                    1.0,
                    bin_min_run if i == 0 else 0,
                    bin_min_down if i == 0 else 0,
                    startup if i == 0 else 0.0,
                )
                for i, (_s, _cap, _hr, *_r) in enumerate(cmt_steps)
            ]
        else:
            committed_tranches = [
                (
                    "committed",
                    committed_cap,
                    committed_hr,
                    1.0,
                    bin_min_run,
                    bin_min_down,
                    startup,
                ),
            ]
            # ScenarioConfig.coal_prb_committed_split (miso-112, PREREG
            # §3): a regulated PRB plant's committed band splits at its
            # MEASURED within-run night level. The hold-through slice
            # (the part reality keeps loaded through cheap nights) keeps
            # the `_committed` suffix — anchor tags and the regulated
            # take-or-pay discount — while the cycling remainder becomes
            # `_commitcyc`, bidding full delivered cost under its supply
            # passthrough (campd_tranche_fuel_frac; startup 0 / min-run 0,
            # the same already-started physical unit, mirroring the
            # committed{i:02d} ramp-slice precedent). Flat-band branch
            # only: a ramp-rendered band (committed_ramp_spread > 0) is
            # already a rising price ladder and skips the split. A plant
            # whose measured night level covers the whole band keeps the
            # keeper form (cyc_cap ≤ 0.5 → no split); one whose night
            # level sits below its mustrun band cycles the whole band
            # (hold_cap 0 → the ≤0.5 MW anchor row is dropped by the
            # capacity guard below — inert in the scored P1 path: the
            # warm-boiler exemption already zeroes coal committed-band
            # startup markups, and min-run coupling is the archived P2's).
            _split_night = (
                _prb_split_night.get(plant_code)
                if (
                    fuel == "coal"
                    and coal_chp_sector is None
                    and coal_supply in ("prb", "subbituminous")
                    and plant_code in _prb_split_reg
                    and committed_cap > 0.5
                )
                else None
            )
            if _split_night is not None:
                _hold_cap = min(
                    committed_cap,
                    max(0.0, _split_night - pct_mr / 100.0) * nameplate,
                )
                _cyc_cap = committed_cap - _hold_cap
                if _cyc_cap > 0.5:
                    committed_tranches = [
                        (
                            "committed",
                            _hold_cap,
                            committed_hr,
                            1.0,
                            bin_min_run,
                            bin_min_down,
                            startup,
                        ),
                        ("commitcyc", _cyc_cap, committed_hr, 1.0, 0, 0, 0.0),
                    ]
        # The _sync (synchronization) tranche bids full SRMC (fuel_frac=1.0 in
        # campd_tranche_fuel_frac), so it carries no fuel discount; it shares the
        # min-load heat rate with _mustrun. Only present in step-3a sync mode and
        # only for plants with a spot (non-contracted) share.
        sync_tranches = (
            [("sync", sync_cap, mustrun_hr, 1.0, 0, 0, 0.0)] if sync_cap > 0.5 else []
        )
        # Fast-start tranche pricing (Order 825 analogue,
        # ScenarioConfig.tranche_startup_amortization): the FAST-START-capable
        # tranches carry the same NREL start cost as the committed anchor, so
        # compute_monthly_markup amortizes each tranche's own P0 run lengths
        # into its P1 bid — the fuel-price-invariant commitment-cost component
        # of the real offer stack. Scope follows ISO-NE's fast-start pricing
        # eligibility (start + notification <= ~30 min): simple-cycle CT
        # tranches (a peaker's econ blocks ARE additional quick-start units)
        # and the CC duct-burner/quick-response PEAK band. A big CC's econ
        # blocks are deliberately EXCLUDED — block-loading a committed CC is
        # not a fast start, and its start costs settle as NCPC uplift, not in
        # the LMP (v1 of this lever marked up CC econ slices and inflated the
        # mild-winter bulk price ~$4 the actual does not show). Min-run /
        # min-down stay 0 (bid markup only, no new UC coupling).
        _fsp_on = getattr(config, "tranche_startup_amortization", False)
        _fsp_econ = startup if (_fsp_on and group in ("CT_PEAKER", "CT_CHP")) else 0.0
        _fsp_peak = (
            startup
            if (_fsp_on and group in ("CT_PEAKER", "CT_CHP", "CC_REGULAR", "CC_CHP"))
            else 0.0
        )
        if _fsp_econ > 0.0:
            econ_steps = [
                (sfx, cap_, hr_, vm_, mr_, md_, _fsp_econ)
                for sfx, cap_, hr_, vm_, mr_, md_, _su in econ_steps
            ]
        # v3 measured-run-length basis (tranche_startup_measured_runs): the
        # simple-cycle CT tranches carry the plant's CAMPD-measured median
        # start-to-stop run length (ISO-class fallback under key 0), which
        # compute_monthly_markup uses as the amortization-horizon ceiling —
        # P0 runs may only shorten it. CC peak (duct) bands keep the v2 P0
        # basis: a duct burner's run is not a CEMS start-to-stop block.
        _fsp_measured_h = (
            _fsp_run_lengths.get(plant_code, _fsp_run_lengths.get(0, 0.0))
            if (_fsp_econ > 0.0 and _fsp_run_lengths)
            else 0.0
        )
        # Peak band: one flat tranche at the offer curve's "peak" multiplier by
        # default. When the offer carries a measured ``peak_ladder``
        # (``[[capacity_share, multiplier], ...]``, derive_dam_offer_hrmults
        # --peak-ladder), the band is split into equal-capacity rungs at the
        # capacity-weighted quantiles of the per-resource top-of-curve offer
        # distribution — representing the measured across-resource dispersion
        # (the upper rungs are the real market's always-posted scarcity wall)
        # instead of collapsing it to the class median
        # (docs/FINDING-ercot-priceshape-2026-07.md §4). Suffixes beyond the
        # first are ``peak2..peakN`` — every consumer that scopes by tranche
        # matches the ``peak`` prefix, not the exact suffix.
        # The per-plant tranche sheet (``ov``) wins over the class ladder, as it
        # does for every other band height.
        ladder = (
            offer.get("peak_ladder") if (offer is not None and ov is None) else None
        )
        if ladder:
            peak_tranches = [
                (
                    ("peak" if i == 0 else f"peak{i + 1}"),
                    peak_cap * float(share),
                    base_hr * float(mult),
                    peak_vom_mult,
                    0,
                    0,
                    _fsp_peak,
                )
                for i, (share, mult) in enumerate(ladder)
            ]
        else:
            peak_tranches = [
                ("peak", peak_cap, peak_hr, peak_vom_mult, 0, 0, _fsp_peak)
            ]
        # Per-plant gas local-reliability commitment floor
        # (config.cc_mustrun_per_plant): the merchant CC_REGULAR committed
        # tranche — already sized to the plant's CEMS minimum stable
        # load — is forced on in the plant's measured committed window (its top
        # online_frac fraction of hours by system load; see the ScenarioConfig
        # field for the rule-12/13 grounding). Self-targeting by the
        # measurement (rule 18): only plants with a CEMS-measured online_frac
        # in the ISO's thermal-tranche artifact carry the floor, and a plant
        # that already runs above its committed level sees a non-binding
        # bound. CHP groups are excluded — their floor is the steam host
        # (chp_grid_pmin_mw), one mechanism per phenomenon (rule 19).
        # CT_PEAKER is deliberately EXCLUDED (G-20 probe, 2026-07-11): the CT
        # leg bound 12.8% of its floored MWh overnight (h23-6) against the
        # class's own overnight-offline evidence — a rule-12 bug — while
        # buying almost none of the eastern CT under-run (Dominion CT
        # 0.9→1.5 vs 8.9 TWh actual), which is an offer/capture residual,
        # not a commitment-share one.
        # ST_GAS carries the same floor under its OWN gate
        # (config.st_gas_mustrun_per_plant — the Entergy MISO-South VLR/self-
        # commitment trace; see that field's docstring): the CT rejection does
        # not transfer because the steamers' measured evidence is the opposite
        # of a CT's (synchronized a supermajority of ALL hours, Nine Mile
        # 98.2%), and the mechanism id is separate so D-2/D-4 attribution
        # stays per-leg.
        cc_mustrun_frac = 0.0
        if (
            group == "CC_REGULAR" and getattr(config, "cc_mustrun_per_plant", False)
        ) or (group == "ST_GAS" and getattr(config, "st_gas_mustrun_per_plant", False)):
            cc_mustrun_frac = (
                _pkg_ns()
                .thermal_tranche_online_frac(
                    getattr(config, "iso", "ERCOT") or "ERCOT",
                    bool(getattr(config, "campd_per_unit_attribution", False)),
                    bool(getattr(config, "campd_outage_merit_order_guard", False)),
                )
                .get((plant_code, group), 0.0)
            )
        tranches = [
            ("mustrun", mustrun_cap, mustrun_hr, 1.0, 0, 0, 0.0),
            *sync_tranches,
            *committed_tranches,
            *econ_steps,
            *peak_tranches,
        ]
        # Coal MINIMUM ONLINE CONFIGURATION floor (ercot128-unit-grain,
        # config.ercot_coal_min_config_floor). A multi-unit coal plant cannot be
        # pushed below the registered minimum load of its SMALLEST online
        # configuration, min_u MinLoad_u (EIA-860, derived by
        # scripts/data/derive_eia860_coal_min_config.py). This is unit-grain
        # commitment's LOWER ENVELOPE, and it needs no commitment state and no
        # integrality: where the plant's exact unit-commitment feasible set is
        # connected — 9 of 10 ERCOT coal plants, 97.8 % of capacity — the
        # plant-grain interval represents it with zero error (the artifact's
        # ``connected`` column records the test per plant).
        #
        # Spread across the tranches in FILL order (mustrun -> sync -> committed
        # -> econ -> peak, i.e. cheapest first, the order the plant actually
        # loads), for the same reason the CHP steam floor is spread: min_gen is
        # clipped to the TRANCHE's pmax x availability in
        # generators_to_fleet_arrays, so pinning a 300 MW plant floor on one
        # ~50 MW slice would silently collapse it. Rule 25 [R-ISO-SCOPE]: the
        # parameter is derived from ERCOT-registered plants, so the gate is
        # ERCOT-only and another ISO would derive its own artifact in its own
        # lane. The ``fuel == "coal"`` gate keeps a mixed plant's gas-steam rows
        # (W A Parish 3470) out.
        min_config_by_suffix: dict[str, float] = {}
        if (
            fuel == "coal"
            and getattr(config, "ercot_coal_min_config_floor", False)
            and (getattr(config, "iso", "ERCOT") or "ERCOT").upper() == "ERCOT"
        ):
            _mc_rem = _pkg_ns().coal_min_config("ERCOT").get(plant_code, 0.0)
            for _suffix, _cap, *_rest in tranches:
                if _mc_rem <= 0.0:
                    break
                if _cap <= 0.5:
                    continue
                _take = min(_mc_rem, _cap)
                min_config_by_suffix[_suffix] = _take
                _mc_rem -= _take
        for suffix, cap, tr_hr, vom_mult, min_run, min_down, tr_startup in tranches:
            # Value unchanged; named at ercot-188 so the econ ramp's slicing can
            # reason about the floor it must clear (see _top_refine_ok).
            if cap <= MIN_TRANCHE_CAPACITY_MW:
                continue
            # Gas-offer net-revenue margin (config.gas_offer_net_revenue_margin):
            # the tranche's markup heat rate ABOVE its measured physical basis
            # (the offer band's phys_* keys), base_HR × max(0, mult − phys).
            # apply_gas_offer_margin later converts it to a fuel-invariant
            # $/MWh margin at the ISO anchor. Scope: CAMPD gas tranches priced
            # by a resolved offer-curve band (the per-plant tranche sheet `ov`
            # bypasses the band decomposition → neutral); bands without phys_*
            # keys resolve to markup 0 (rule 24 neutral fallback).
            _margin_markup_hr = 0.0
            _margin_anchor = None
            if (
                getattr(config, "gas_offer_net_revenue_margin", False)
                and offer is not None
                and ov is None
                and fuel in GAS_OFFER_MARGIN_FUELS
                and base_hr > 0.0
            ):
                _margin_markup_hr = base_hr * gas_offer_margin_markup_mult(
                    suffix, tr_hr / base_hr, offer
                )
                # ERCOT-118 EP rebasis: a rebased class's band dict carries
                # ``margin_anchor`` (the year's EP-anchored delivered mean its
                # per-year multipliers were identified at); thread it onto the
                # tranche so apply_gas_offer_margin prices THIS markup at that
                # basis. Band-scoped rebasis (ERCOT-119) writes
                # ``margin_anchor_<band>`` keys instead, so only the REBASED
                # bands' markups move off the window anchor —
                # band_margin_anchor resolves the tranche's suffix against
                # both forms. Absent keys -> None -> the ISO window anchor.
                if _margin_markup_hr > 0.0:
                    _margin_anchor = band_margin_anchor(suffix, offer)
                    # nyiso-109 zone-resolved anchor: on an ISO whose fuel
                    # carries a per-zone basis, the ISO window anchor is the
                    # REFERENCE zone's level, so a tranche outside that zone
                    # would price its markup at a fuel level it never pays.
                    # Resolve it at THIS tranche's zone instead. A band-scoped
                    # rebasis anchor keeps precedence (rule 19 [R-ONE-MECH] —
                    # the two identification channels never stack); a zone
                    # absent from the map keeps the window anchor.
                    if _margin_anchor is None and _zonal_margin_anchors:
                        _margin_anchor = _zonal_margin_anchors.get(zone)
            # Step-3a synchronization forcing: the _mustrun (contracted, fuel-
            # free) and _sync (spot, SRMC) coal min-load tranches are held on at
            # their full capacity via min_gen, so the unit stays synchronized at
            # the measured online Pmin. Other tranches (and non-sync runs) keep
            # the Pmin=0 economic behaviour.
            sync_floor = cap if (coal_sync and suffix in ("mustrun", "sync")) else 0.0
            # Gas local-reliability commitment forcing: the committed tranche
            # (every slice under committed_ramp_spread) is held on at its full
            # capacity via min_gen within the plant's measured committed
            # window; the offer price is unchanged (the floor makes the
            # EXISTING committed tranche a forced quantity, no second floor).
            cc_floor = (
                cap
                if (cc_mustrun_frac > 0.0 and suffix.startswith("committed"))
                else 0.0
            )
            fleet.append(
                Generator(
                    unit_id=f"{bin_id}_{suffix}",
                    name=f"{plant_name} {suffix}",
                    zone=zone,
                    fuel_type=fuel,
                    efficiency_bin=group,
                    pmax_mw=cap,
                    pmin_mw=0.0,
                    heat_rate=tr_hr,
                    vom=get_vom(fuel) * vom_mult,
                    # R2/EM-4: book CO2 at the plant's PHYSICAL heat rate
                    # (``base_hr``), never the bid-tranche heat rate ``tr_hr``.
                    # ``tr_hr`` carries the offer-curve pricing multipliers
                    # (peak ×2.0-2.5, committed ×0.92 — docs/binning-methodology.md
                    # §pricing) that shape the bid stack; a plant's CO2/MWh does
                    # not change because a block is offered at a scarcity price.
                    # CEMS-covered plants get their measured rate later via
                    # apply_plant_emission_rates; this base_hr value is the
                    # physical default for uncovered plants and entrants.
                    emission_rate_co2=get_emission_rate(fuel, base_hr),
                    nox_rate=get_nox_rate(fuel),
                    eford=get_eford(fuel),
                    online_year=commission_year,
                    # Exit-cohort timing (miso-191): None on ordinary bins;
                    # on a cohort bin the unit's own EIA-860 retirement, which
                    # effective_cod prefers over the plant-collapsed date.
                    retirement_year=cohort_ry,
                    retirement_month=cohort_rm,
                    is_campd_bin=True,
                    plant_group=group,
                    bin_label=label,
                    min_run_hours=min_run,
                    min_down_hours=min_down,
                    # ercot-186 rule-18 [R-PHYSICS] GRAIN REPAIR. The two tags
                    # above are per-TRANCHE and, by the deliberate design
                    # recorded above, are non-zero on the committed anchor
                    # slice ONLY — a bid tranche must acquire no UC coupling.
                    # The consequence was that a licensing gate reading
                    # ``min_down_hours`` on an econ*/peak* row read 0 for every
                    # row it could ever reach, so the test was vacuous in both
                    # directions (``<= 2`` admitted everything, ``>= 4``
                    # rejected everything) and its effective scope collapsed
                    # onto the caller's class map — the hard-coded class tuple
                    # rule 18 forbids. Stamp the PLANT's own assembled physics
                    # on every one of its rows so the gate can be evaluated at
                    # the grain the physics actually lives at. Same values, one
                    # grain coarser; nothing in the LP, FleetArrays or the
                    # commitment path reads these fields.
                    plant_min_run_hours=bin_min_run,
                    plant_min_down_hours=bin_min_down,
                    startup_cost_per_mw=tr_startup,
                    must_run_pct=pct_mr if suffix == "committed" else 0.0,
                    bin_nameplate_mw=(nameplate if suffix == "committed" else 0.0),
                    coal_supply=coal_supply,
                    plant_code=plant_code,
                    state=_plant_states.get(plant_code, ""),
                    chp_grid_pmin_mw=chp_floor_by_suffix.get(suffix, 0.0),
                    coal_sync_pmin_mw=sync_floor,
                    coal_sync_online_frac=(
                        sync_online_frac if sync_floor > 0.0 else 1.0
                    ),
                    coal_min_config_pmin_mw=min_config_by_suffix.get(suffix, 0.0),
                    cc_mustrun_pmin_mw=cc_floor,
                    cc_mustrun_online_frac=(cc_mustrun_frac if cc_floor > 0.0 else 0.0),
                    # Measured amortization horizon only on the fast-start CT
                    # tranches that carry the fsp startup cost (econ + peak of
                    # CT groups); the committed anchor keeps the P0 basis.
                    fast_start_run_hours=(
                        _fsp_measured_h
                        if (tr_startup > 0.0 and suffix.startswith(("econ", "peak")))
                        else 0.0
                    ),
                    offer_markup_hr=_margin_markup_hr,
                    offer_margin_anchor=_margin_anchor,
                )
            )

    # v2 measured plant CO2/NOx/SO2 rates on the CAMPD-bins path (G-39 §9.6
    # backcast-reachability fix, 2026-07-06): `apply_plant_emission_rates_v2`
    # was previously called only from `build_dispatch_fleet` (the forecast/
    # runner path), so `use_plant_emission_rates_v2=True` in a backcast
    # run_config was silently unreachable for every CAMPD-binned ISO — proven
    # byte-identical by the nyiso-53 v2-on/off twin pair before this call was
    # added (the same production-wiring-gap class as gap-register G-29).
    # Applying here — before the array conversion, on the same (plant_code,
    # coarse fuel class) match the dispatch-fleet path uses — makes the flag's
    # recorded state true on both paths. Default off: byte-identical unless a
    # config explicitly opts in.
    if getattr(config, "use_plant_emission_rates_v2", False):
        _pkg_ns().apply_plant_emission_rates_v2(
            fleet,
            config.plant_emission_rates_v2_path,
            iso=config.iso,
            year=int(config.weather_year),
            mode=str(getattr(config, "mode", "forecast")),
            config=config,
        )

    fleet_arrays = generators_to_fleet_arrays(
        fleet,
        zone_names,
        hours=config.hours,
        iso=config.iso,
        config=config,
        year=config.weather_year,
    )
    return fleet, fleet_arrays


def load_or_synthesize_bins(
    config: ScenarioConfig,
    iso: str,
    iso_config: ISOConfig,
    retired_within_window: list[Generator],
) -> pd.DataFrame | None:
    """Resolve the per-plant bin frame driving the offer-curve fleet path.

    ERCOT reads its curated per-plant bin sheet (``config.campd_bins_path``)
    directly via :func:`load_campd_bins`. Every other ISO in
    :data:`~market_sim.config.constants.CAMPD_BINNING_ISOS` synthesizes the
    same per-plant bin schema from its EIA-860 fleet plus the CAMPD-derived
    thermal-tranche artifact via :func:`fleet_to_bins`. Returns ``None`` --
    the signal to fall back to the legacy :func:`aggregate_fleet` path --
    when ``use_campd_bins`` is off, the ISO has no CAMPD artifact, the
    curated CSV is missing, or the synthesis yields no thermal bins.
    """
    if not (config.use_campd_bins and iso in CAMPD_BINNING_ISOS):
        return None
    if iso == "ERCOT":
        if not Path(config.campd_bins_path).exists():
            logger.info(
                "%s: use_campd_bins=True but %s does not exist; falling back "
                "to the legacy aggregate_fleet path",
                iso,
                config.campd_bins_path,
            )
            return None
        return _pkg_ns().load_campd_bins(
            config.campd_bins_path,
            year=START_YEAR,
            capacity_reconcile_path=(
                config.cc_capacity_reconcile_path
                if config.cc_capacity_reconcile
                else None
            ),
        )
    bins = _pkg_ns().fleet_to_bins(
        _pkg_ns().load_fleet_from_csv(
            iso,
            iso_config,
            measured_ct_heat_rates=config.measured_ct_heat_rates,
            measured_chp_heat_rates=config.measured_chp_heat_rates,
            egrid_identity_heat_rates=config.egrid_identity_heat_rates,
            egrid_family_heat_rates=config.egrid_family_heat_rates,
            egrid_steam_collapse_heat_rates=config.egrid_steam_collapse_heat_rates,
            cc_steam_part_capacity=config.cc_steam_part_capacity,
            cc_steam_part_reclass=config.cc_steam_part_reclass,
        )
        + retired_within_window,
        iso,
        config,
    )
    if bins.empty:
        logger.info(
            "%s: use_campd_bins=True but fleet_to_bins synthesized no "
            "thermal bins (no CAMPD-derived thermal_tranches artifact); "
            "falling back to the legacy aggregate_fleet path",
            iso,
        )
        return None
    return bins


def build_base_fleet(
    campd_bins: pd.DataFrame | None,
    iso: str,
    iso_config: ISOConfig,
    zone_names: list[str],
    config: ScenarioConfig,
    retired_within_window: list[Generator],
    planned_additions: list[Generator],
    year: int,
    confirmed_exits: list | None = None,
    *,
    announced_fossil_exits: list | None = None,
    vintage_year: int | None = None,
    nonthermal_exclude: frozenset[str] | None = None,
    legacy_n_bins: int | None = None,
) -> list[Generator]:
    """Build the first simulated year's persistent generation fleet.

    Takes the per-plant bin choice already resolved by
    :func:`load_or_synthesize_bins`: per-plant tranche generators
    (:func:`bins_to_fleet`) when bins were found, else the legacy
    equal-width heat-rate-bin aggregation (:func:`aggregate_fleet`). Either
    way the collapse happens once, here, before the per-year dispatch loop.
    Planned EIA-860 additions already due by ``year`` are appended; later
    years instead evolve this fleet via
    :func:`~market_sim.model.capacity.evolve_fleet`.

    Confirmed (binding-instrument) exits already effective by ``year`` are
    applied last (:func:`~market_sim.model.capacity.apply_confirmed_exits`,
    ``apply_backlog=True``), so a unit confirmed to close in the first
    simulated year is not mis-carried for a full year — the "a 2026 exit can
    never happen in 2026" hole the economic screen (which needs prior-year
    dispatch) cannot close. ``apply_backlog=True`` collapses every exit with
    ``effective_year <= year`` (the pre-start backlog) into a single
    application here; :func:`~market_sim.model.capacity.evolve_fleet` then
    only ever selects a row newly effective in its own year, so no row is
    ever applied twice. GATED on ``config.confirmed_exits_enabled``; a no-op
    when off or ``confirmed_exits`` is empty.

    ``announced_fossil_exits`` (capx D42, GATED
    ``config.fossil_announced_exits_enabled`` — DEFAULT ON since 2026-09-03,
    owner ruling Q30; an explicit ``False`` makes it a no-op): the
    owner-filed fossil retirement rows get the SAME first-year backlog
    treatment through the same call — a date at or before the first
    simulated year is applied up front, and later years' rows are selected by
    :func:`~market_sim.model.capacity.evolve_fleet` step 1 exactly once.

    Backcast parameterization (orchestrator-unification Stage 6 -- the
    backcast rebuilds this base fleet every solved year instead of evolving
    a persistent one):

    - ``vintage_year``: EIA-860 vintage passed to
      :func:`load_fleet_from_csv` (the backcast's year-matched snapshot);
      ``None`` keeps the runner's default vintage resolution.
    - ``nonthermal_exclude``: the fuel set removed from the raw EIA-860
      units on the ERCOT curated-bins branch; ``None`` uses
      :data:`_AGGREGATABLE_FUELS`. The backcast passes a set WITHOUT
      ``oil`` (its ERCOT oil units stay raw LP scarcity peakers, while the
      forecast path drops them) -- a pre-existing divergence preserved
      through the migration, not a new choice; reconciling it is an open
      root-cause item (CLAUDE.md #14), not a refactor decision.
    - ``legacy_n_bins``: heat-rate bin count on the no-bins fallback path;
      ``None`` reads ``config.heat_rate_bin_count``. The backcast passes 0
      (per-plant, identity-preserving) when ``plant_level_fleet`` is set.
    """
    if campd_bins is not None:
        campd_fleet, _ = _pkg_ns().bins_to_fleet(campd_bins, zone_names, config)
        all_gens = (
            _pkg_ns().load_fleet_from_csv(
                iso,
                iso_config,
                year=vintage_year,
                measured_ct_heat_rates=config.measured_ct_heat_rates,
                measured_chp_heat_rates=config.measured_chp_heat_rates,
                egrid_identity_heat_rates=config.egrid_identity_heat_rates,
                egrid_family_heat_rates=config.egrid_family_heat_rates,
                egrid_steam_collapse_heat_rates=config.egrid_steam_collapse_heat_rates,
                cc_steam_part_capacity=config.cc_steam_part_capacity,
                cc_steam_part_reclass=config.cc_steam_part_reclass,
            )
            + retired_within_window
        )
        if iso == "ERCOT":
            # ERCOT's curated sheet covers the full gas/coal thermal fleet;
            # nuclear (and any other non-aggregatable unit) still comes from
            # EIA-860 so it stays in the dispatch LP.
            _exclude = (
                _AGGREGATABLE_FUELS
                if nonthermal_exclude is None
                else nonthermal_exclude
            )
            non_thermal = [g for g in all_gens if g.fuel_type not in _exclude]
        else:
            # The synthesized bins cover exactly the thermal (plant_code,
            # plant_group) pairs in ``campd_bins``; every other unit
            # (nuclear, oil, biomass, and any thermal plant the synthesis
            # didn't bin) stays a raw LP unit. Filtering on the exact binned
            # set -- rather than a fuel allow-list -- avoids dropping or
            # double-counting any plant (the bin groups include gas_st,
            # which is not an aggregatable fuel).
            binned = set(
                zip(
                    campd_bins["Plant_Code"].astype(int),
                    campd_bins["Plant_Group"],
                )
            )
            non_thermal = [
                g for g in all_gens if (int(g.plant_code), g.plant_group) not in binned
            ]
        fleet = non_thermal + campd_fleet
    else:
        fleet = _pkg_ns().aggregate_fleet(
            _pkg_ns().load_fleet_from_csv(
                iso,
                iso_config,
                year=vintage_year,
                measured_ct_heat_rates=config.measured_ct_heat_rates,
                measured_chp_heat_rates=config.measured_chp_heat_rates,
                egrid_identity_heat_rates=config.egrid_identity_heat_rates,
                egrid_family_heat_rates=config.egrid_family_heat_rates,
                egrid_steam_collapse_heat_rates=config.egrid_steam_collapse_heat_rates,
                cc_steam_part_capacity=config.cc_steam_part_capacity,
                cc_steam_part_reclass=config.cc_steam_part_reclass,
            )
            + retired_within_window,
            n_bins=(
                config.heat_rate_bin_count if legacy_n_bins is None else legacy_n_bins
            ),
        )
    # Planned units already due by the first simulated year (their EIA-860
    # effective year falls after the operable snapshot but at or before
    # ``year``) join the base fleet now; evolve_fleet only runs from the
    # second year on.
    due = [g for g in planned_additions if g.online_year <= year]
    if due:
        logger.info(
            "year %d: %d planned additions already due (%.0f MW)",
            year,
            len(due),
            sum(g.pmax_mw for g in due),
        )
        fleet = fleet + due

    # Confirmed exits already effective by the first simulated year (their
    # instrument date is at or before ``year``): a unit confirmed to close now is
    # excluded up front, since the economic screen (needing prior-year dispatch)
    # cannot retire it in the first year. Local import avoids the fleet<->capacity
    # import cycle; a no-op unless the confirmed channel is enabled.
    if getattr(config, "confirmed_exits_enabled", False) and confirmed_exits:
        from market_sim.model.capacity import apply_confirmed_exits

        before = len(fleet)
        fleet = apply_confirmed_exits(fleet, year, confirmed_exits, apply_backlog=True)
        if len(fleet) != before:
            logger.info(
                "year %d: confirmed exits removed/derated %d base-fleet unit(s)",
                year,
                before - len(fleet),
            )
    if (
        getattr(config, "fossil_announced_exits_enabled", False)
        and announced_fossil_exits
    ):
        from market_sim.model.capacity import apply_confirmed_exits

        before_mw = sum(g.pmax_mw for g in fleet)
        fleet = apply_confirmed_exits(
            fleet, year, announced_fossil_exits, apply_backlog=True
        )
        logger.info(
            "year %d: announced fossil dates (capx D42) removed/derated %.0f MW "
            "of base-fleet capacity in the pre-start backlog",
            year,
            before_mw - sum(g.pmax_mw for g in fleet),
        )
    return fleet


def _drop_biomass_units(
    fleet: list[Generator], fuel_fracs: list
) -> tuple[list[Generator], list]:
    """Remove biomass LP units (and their parallel fuel fractions) from a fleet.

    Used when biomass is injected as a measured EIA-923 must-run profile (the
    caller nets it out of demand and re-adds it as a fixed pseudo-unit), so the
    raw biomass generators must not also clear the merit order -- else biomass
    is served twice. Returns the filtered ``(fleet, fuel_fracs)`` pair (order-
    and length-preserving). A no-op for a fleet with no biomass units (e.g.
    ERCOT, whose CAMPD path already excludes them). Moved verbatim from
    ``scripts/run_calibration.py`` (orchestrator-unification Stage 6).
    """
    kept = [(g, ff) for g, ff in zip(fleet, fuel_fracs) if g.fuel_type != "biomass"]
    return [g for g, _ in kept], [ff for _, ff in kept]


def build_dispatch_fleet(
    fleet: list[Generator],
    campd_bins: pd.DataFrame | None,
    import_generators: list[Generator],
    iso: str,
    year: int,
    zone_names: list[str],
    config: ScenarioConfig,
    *,
    hydro_backfill_year: int | None = None,
    hydro_eia930_monthly: bool = False,
    hydro_forecast_budget: bool = True,
    hydro_year: str | None = None,
    drop_biomass_units: bool = False,
    imports_after_hydro: bool = False,
    apply_emission_overrides: bool = True,
) -> tuple[list[Generator], list[float], np.ndarray | None, np.ndarray | None]:
    """Assemble this year's LP-ready dispatch fleet from the persistent fleet.

    Prices coal take-or-pay / SRMC tranches via the CAMPD per-plant fuel
    fractions (:func:`campd_tranche_fuel_frac`) when ``campd_bins`` is
    active; the non-CAMPD fallback passes coal through unsplit at full fuel
    cost (optionally splitting gas via the legacy
    :func:`split_gas_tranches`), then appends energy-limited hydro plants
    and overrides plant-specific CAMPD emission rates. Both branches start
    from the same ``fleet`` and end at the same shape: a list of
    :class:`Generator` ready for :func:`generators_to_fleet_arrays`.

    THE shared per-year fleet-assembly body for both orchestrators
    (orchestrator-unification Stage 6): the forecast runner calls it with the
    keyword defaults; the backcast orchestrator passes its measured hydro
    budgets, biomass-injection drop, import placement, and the emission-
    override seam explicitly. The coal-passthrough machinery (per-supply
    gas-keyed sigmoids, tiered PRB follower) is resolved here from ``config``
    for both callers, so a supply curve a config enables is reachable from
    either path -- flat full-cost passthrough at the field defaults.

    Args:
        (The conventional-hydro min-flow floor is NOT a kwarg here: it rides the
        registered ``config.hydro_min_flow_floor`` gate, read at the
        ``build_hydro_fleet`` call below so both orchestrators share one switch.)

        hydro_backfill_year / hydro_eia930_monthly / hydro_forecast_budget:
            threaded to :func:`market_sim.data.hydro.build_hydro_fleet`. The
            defaults (no backfill, climatology forecast budget) reproduce the
            runner's historical call; a backcast passes its measured
            monthly-budget switches.
        hydro_year: water-year selector; ``None`` reads ``config.hydro_year``.
        drop_biomass_units: drop raw biomass LP units (and their parallel
            fuel fractions) after the tranche split -- set by the backcast
            when biomass is injected as a measured must-run profile
            (``inject_biomass_mustrun``) so biomass is never served twice.
        imports_after_hydro: append ``import_generators`` after the hydro
            block (the backcast's historical LP column order) instead of
            merging them into the tranche split (the runner's). Both orders
            price imports identically (fuel fraction 1.0 either way); the
            switch exists purely to preserve each orchestrator's established
            column order across the Stage-6 migration (golden byte-identity,
            output-frame stability), not because the orders differ
            economically.
        apply_emission_overrides: run the plant-specific CAMPD emission-rate
            override block (v2 mode-aware artifact, else the v1 parquet when
            ``config.use_plant_emission_rates``). The backcast passes False:
            its per-plant rates enter via the bin artifacts and the v2 hook
            inside :func:`bins_to_fleet` (G-39 §9.6), and it has never
            applied the v1 overwrite -- folding v1 in would move keeper
            emission costs (an open reconciliation item, not a refactor
            decision).

    Returns:
        ``(dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy)``.
        ``hydro_gen_idx`` / ``hydro_monthly_energy`` are ``None`` when the
        ISO has no hydro plants.
    """
    # Local import: data.fuel imports from data.fleet at module level, so the
    # passthrough helpers must be imported lazily here (same pattern as the
    # hydro builder below).
    from market_sim.data.fuel import (
        coal_passthrough_by_supply,
        prb_follower_passthrough_series,
    )

    inline_imports = [] if imports_after_hydro else import_generators
    if campd_bins is not None:
        dispatch_fleet = fleet + inline_imports
        # Must-run tranches bid at VOM + carbon + NOx only -- the fuel is
        # sunk under take-or-pay coal contracts, CHP host steam obligations
        # or ERCOT RUC. In step-3a sync mode the contract share is consumed
        # in bins_to_fleet to SIZE the fuel-free _mustrun band vs the SRMC
        # _sync band, so it must NOT be re-applied here (that would
        # double-discount).
        takeorpay = None
        if getattr(config, "coal_takeorpay_from_data", False) and not getattr(
            config, "coal_sync_srmc_tranche", False
        ):
            takeorpay = {
                int(g.plant_code): coal_takeorpay_share(int(g.plant_code))
                for g in dispatch_fleet
                if g.fuel_type == "coal"
                and coal_takeorpay_share(int(g.plant_code)) is not None
            }
        # Above must-run, each coal tranche passes its own supply chain's
        # passthrough -- flat scalar, or a (T,) gas-keyed sigmoid resolved
        # per (ISO, supply) -- so baseloaded coal clears the merit order
        # instead of being priced out by cheap gas. At the field defaults
        # (all sigmoid toggles off, coal_prb_passthrough = 1.0) every supply
        # passes full fuel cost, value-identical to the pre-Stage-6 inline
        # {"prb": p, "subbituminous": p} dict this replaces (a missing tag
        # and a 1.0 tag both mean full cost). The one semantic tightening:
        # with sigmoids off, a non-default coal_prb_passthrough now discounts
        # only prb-tagged coal (subbituminous keeps full cost unless its own
        # curve is enabled) -- the backcast's calibrated per-supply routing,
        # which no forecast config relied on (nothing in src/ sets the field).
        pt_by_supply = coal_passthrough_by_supply(config, year, config.hours)
        if config.coal_prb_passthrough_sigmoid and config.coal_prb_passthrough_tiered:
            # Tiered PRB: low-must-run "prb" load-followers swap the baseload
            # prb curve for the follower-tier one. The tier split is specific
            # to the curated ERCOT prb supply; ISOs without a characterized
            # follower curve fall back to the baseload prb series
            # (value-identical routing).
            foll = {
                **pt_by_supply,
                "prb": prb_follower_passthrough_series(config, year, config.hours),
            }
            thr = config.coal_prb_follower_mustrun_max

            def _pt_for(g: Generator):
                if (
                    g.fuel_type == "coal"
                    and getattr(g, "coal_supply", "") == "prb"
                    and _pkg_ns().COAL_MUSTRUN_BY_PLANT.get(g.plant_code, 100.0) <= thr
                ):
                    return foll
                return pt_by_supply

        else:

            def _pt_for(g: Generator):
                return pt_by_supply

        _reg_gate = getattr(config, "coal_committed_takeorpay_regulated", False)
        # ScenarioConfig.coal_prb_committed_dispatchable: PRB/subbituminous
        # (the COAL_PRB class) committed bands bid full delivered cost — the
        # measured conduct scope (miso-111), see campd_tranche_fuel_frac.
        _prb_dispatchable = (
            frozenset({"prb", "subbituminous"})
            if getattr(config, "coal_prb_committed_dispatchable", False)
            else None
        )
        fuel_fracs = [
            _pkg_ns().campd_tranche_fuel_frac(
                g,
                _pt_for(g),
                takeorpay,
                econ_srmc_bound=getattr(config, "coal_econ_srmc_bound", False),
                committed_takeorpay_bit=getattr(
                    config, "coal_bit_committed_takeorpay", False
                ),
                committed_takeorpay_all=getattr(
                    config, "coal_committed_takeorpay_all", False
                ),
                committed_takeorpay_regulated=_reg_gate,
                regulated_plants=(
                    eia860_selfcommit_scope_plants() if _reg_gate else None
                ),
                committed_takeorpay_sunk_fixed=getattr(
                    config, "coal_committed_takeorpay_sunk_fixed", False
                ),
                committed_dispatchable_supplies=_prb_dispatchable,
                # ScenarioConfig.committed_band_measured_basis — Route A
                # REPLACE half (b): the coal `_committed` band drops its
                # supply passthrough entirely, so its effective basis is the
                # measured `avg_committed_p50` multiplier half (a) installs
                # (offer_curves.apply_committed_band_measured_basis). The two
                # halves are one mechanism (rule 19 [R-ONE-MECH]).
                committed_measured_basis=getattr(
                    config, "committed_band_measured_basis", False
                ),
            )
            for g in dispatch_fleet
        ]
    else:
        # Non-CAMPD fallback (use_campd_bins off / no bin artifact): coal
        # passes through unsplit at full fuel cost. The legacy coal
        # take-or-pay split (split_coal_tranches + the six coal_tranche_*
        # scalars) was DELETED 2026-08-12 (rule 26 [R-DELETE], ercot-188 G#3
        # owner ruling) — every registered bundle of all six ISOs takes the
        # CAMPD limb above, so this limb produced no registered result
        # (proof: results/calibration/ercot188_g3_unreachability_proof.json).
        dispatch_fleet = fleet + inline_imports
        fuel_fracs = [1.0] * len(dispatch_fleet)
        if getattr(config, "gas_offer_curve", False):
            dispatch_fleet, fuel_fracs = split_gas_tranches(
                dispatch_fleet, fuel_fracs, config
            )

    # Biomass injected as a measured EIA-923 must-run profile (the caller nets
    # it out of demand and re-adds it as a fixed pseudo-unit), so drop the raw
    # biomass LP units to avoid double-serving -- and to make biomass output
    # the fuel/contract-limited, price-insensitive quantity it is in reality
    # instead of a dispatchable unit the LP runs to max when gas rises.
    # Backcast-only today (inject_biomass_mustrun); default off, so callers
    # that do NOT inject biomass keep it as an LP unit and never lose it.
    if drop_biomass_units:
        dispatch_fleet, fuel_fracs = _drop_biomass_units(dispatch_fleet, fuel_fracs)

    # Energy-limited conventional hydro (every ISO with hydro plants): one LP
    # unit per EIA-923-reporting hydro plant, capped per hour by its EIA-860
    # nameplate and per month by its energy budget via the dispatch LP's
    # hydro budget rows. Appended after the coal/gas split so it flows
    # through assemble_mc and the dispatch like any other generator.
    from market_sim.data.hydro import build_hydro_fleet

    hydro_units, hydro_monthly_energy = build_hydro_fleet(
        iso,
        year,
        zone_names,
        backfill_year=hydro_backfill_year,
        eia930_monthly=hydro_eia930_monthly,
        forecast_budget=hydro_forecast_budget,
        # Registered ScenarioConfig gates (rule 24), default off — read from the
        # config rather than threaded as kwargs so BOTH orchestrators pick the
        # floor / RoR split up from the same single switches.
        min_flow_floor=bool(getattr(config, "hydro_min_flow_floor", False)),
        ror_split=bool(getattr(config, "hydro_ror_split", False)),
        nameplate_aware_target=bool(
            getattr(config, "hydro_budget_nameplate_aware", False)
        ),
        hydro_year=config.hydro_year if hydro_year is None else hydro_year,
        # T1-FF information cutoff (FH-1): a full-forward hindcast trims the
        # hydro climatology and shape year to its base year
        # (crossover_forward_year == the base). None for every other run —
        # plain hindcast, T1-X, forecast, backcast — byte-identical.
        as_of_year=(
            int(config.crossover_forward_year)
            if getattr(config, "is_full_forward_hindcast", False)
            else None
        ),
    )
    hydro_gen_idx = None
    if hydro_units:
        hydro_gen_idx = np.arange(
            len(dispatch_fleet),
            len(dispatch_fleet) + len(hydro_units),
            dtype=int,
        )
        dispatch_fleet = dispatch_fleet + hydro_units
        fuel_fracs = list(fuel_fracs) + [1.0] * len(hydro_units)
        logger.info(
            "%s %d: %d hydro plants in LP (%.0f MW, %.2f TWh monthly budget)",
            iso,
            year,
            len(hydro_units),
            sum(g.pmax_mw for g in hydro_units),
            hydro_monthly_energy.sum() / 1e6,
        )

    # Backcast import placement: the priced import/export node's tranches join
    # the LP after hydro (the backcast's historical column order -- see the
    # imports_after_hydro docstring note).
    if imports_after_hydro and import_generators:
        dispatch_fleet = dispatch_fleet + import_generators
        fuel_fracs = list(fuel_fracs) + [1.0] * len(import_generators)
        logger.info(
            "%s %d: priced import/export node — %d import tranches "
            "(%.0f MW), %d export sinks (%.0f MW)",
            iso,
            year,
            sum(1 for g in import_generators if g.pmax_mw > 0),
            sum(g.pmax_mw for g in import_generators),
            sum(1 for g in import_generators if g.pmin_mw < 0),
            -sum(g.pmin_mw for g in import_generators),
        )

    # Override fuel-class CO2/NOx/SO2 rates with CAMPD plant-specific ones
    # for generators pinned to a single plant, so emission prices bite at
    # each plant's measured per-MWh-net intensity. Gated off by the backcast
    # (see the apply_emission_overrides docstring note).
    if apply_emission_overrides:
        if getattr(config, "use_plant_emission_rates_v2", False):
            # Mode-aware v2 source: backcast books the target year's measured
            # rate, forecast the estimator base; composition mask splits
            # Parish coal/gas.
            _pkg_ns().apply_plant_emission_rates_v2(
                dispatch_fleet,
                config.plant_emission_rates_v2_path,
                iso=iso,
                year=int(year),
                mode=str(getattr(config, "mode", "forecast")),
                config=config,
            )
        elif config.use_plant_emission_rates:
            _pkg_ns().apply_plant_emission_rates(
                dispatch_fleet, config.plant_emission_rates_path
            )

    return dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy
