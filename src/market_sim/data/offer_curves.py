"""Multi-tranche offer curves for CAMPD per-plant binning.

Extracted from :mod:`market_sim.data.fleet` — functions that split thermal
generators into stepped supply-curve tranches (coal take-or-pay, gas
committed/economic/peaking) and build the per-plant offer-curve band
visualization for the calibration dashboard.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from market_sim.config.constants import (
    CC_ECON_HR_OVERRIDE_DEFAULT,
    CC_PEAK_HR_OVERRIDE_DEFAULT,
    CT_ECON_HR_OVERRIDE_DEFAULT,
    CT_PEAK_HR_OVERRIDE_DEFAULT,
    GAS_ST_ECON_HR_OVERRIDE_DEFAULT,
    GAS_ST_PEAK_HR_OVERRIDE_DEFAULT,
    GAS_TRANCHE_SHARES_BY_GROUP,
)
from market_sim.config.scenarios import ScenarioConfig

if TYPE_CHECKING:
    import pandas as pd

# Gas peak-band classes the ERCOT condition-responsive offer surface prices
# (ScenarioConfig.ercot_offer_surface_conditional). Must match the groups the
# measured surface is derived over (scripts.data.derive_dam_offer_hrmults
# CONDBINNED_GROUPS). Coal (take-or-pay, own sigmoid) and CT_CHP (no measured DAM
# class) are excluded — the surface scopes to the gas energy stack (finding §3).
CONDITIONAL_SURFACE_GROUPS: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "ST_GAS",
)


def _hr_override(value: float | None, default: float) -> float:
    """Return the configured heat-rate-override multiplier, or its named default.

    The ``{cc,gas_st,ct}_*_hr_override`` fields default to ``None``; when a
    caller sets the ``*_committed_hr_override`` band but leaves the econ/peak
    bands unset, those bands fall back to the ERCOT-lineage default constant
    (``constants.*_HR_OVERRIDE_DEFAULT``) rather than an inline literal
    (audit rule #23 — no fallback literals in the offer path).
    """
    return default if value is None else float(value)


# ---------------------------------------------------------------------------
# Coal tranches (take-or-pay supply curve)
# ---------------------------------------------------------------------------


def _coal_tranches(config: ScenarioConfig) -> list[tuple[float, float]]:
    """Return the coal take-or-pay tranches as ``(cap_frac, fuel_frac)`` pairs.

    Reads the per-tranche capacity fraction and fuel-cost passthrough from
    the scenario config (``coal_tranche_{1,2,3}_{frac,fuel_passthrough}``,
    ``ScenarioConfig``) so calibration can override the defaults.
    """
    return [
        (config.coal_tranche_1_frac, config.coal_tranche_1_fuel_passthrough),
        (config.coal_tranche_2_frac, config.coal_tranche_2_fuel_passthrough),
        (config.coal_tranche_3_frac, config.coal_tranche_3_fuel_passthrough),
    ]


def split_coal_tranches(
    generators: list,
    config: ScenarioConfig,
    takeorpay_by_plant: "dict[int, float] | None" = None,
) -> tuple[list, list[float]]:
    """Split each coal generator into take-or-pay supply-curve tranches.

    Coal plants hold take-or-pay fuel contracts: the contracted volume bids
    at VOM only (its fuel is sunk) while volume above the contract bids at
    progressively more of full fuel cost. Each coal :class:`Generator` is
    therefore replaced by three sub-generators — one per tranche — that
    together reproduce its capacity but expose a stepped supply curve to the
    dispatch LP. Tranches carry ``pmin_mw = 0``: coal's baseload behavior
    emerges from tranche 1's near-zero (VOM-only) bid, not a hard minimum.

    Non-coal generators pass through unchanged.

    Args:
        generators: The fleet to expand.
        config: Scenario configuration supplying the ``coal_tranche_*`` fields.
        takeorpay_by_plant: Optional ``{plant_code: contract_share}`` from the
            measured EIA-923 Schedule-5 Purchase Type
            (:func:`coal_takeorpay_share`, set when
            ``ScenarioConfig.coal_takeorpay_from_data`` is on). When given, the
            **sunk** first tranche (tranche 1, the must-run / take-or-pay band)
            passes ``1 - contract_share`` of its fuel instead of the assumed
            ``coal_tranche_1_fuel_passthrough``: only the measured contracted
            tonnage is sunk, the spot remainder bids full delivered fuel. This
            is the split-fleet (non-CAMPD ISO) analogue of the must-run
            adjustment :func:`campd_tranche_fuel_frac` applies in the binned
            path. A plant absent from the map keeps the configured passthrough.

    Returns:
        A tuple ``(expanded_fleet, fuel_fracs)`` where ``fuel_fracs[g]`` is the
        fraction of fuel cost passed through to generator ``g``'s marginal
        cost. Non-coal generators have ``fuel_frac = 1.0``.
    """
    from market_sim.data.fleet import Generator

    tranches = _coal_tranches(config)
    expanded: list[Generator] = []
    fuel_fracs: list[float] = []
    for gen in generators:
        if gen.fuel_type != "coal":
            expanded.append(gen)
            fuel_fracs.append(1.0)
            continue
        for ti, (cap_frac, fuel_frac) in enumerate(tranches):
            # Measured take-or-pay (CLAUDE.md #11/#12): replace the assumed
            # 100%-sunk first tranche with the plant's measured contracted
            # share — only the sunk (tranche-1) band is adjusted, mirroring the
            # binned path's must-run treatment.
            if ti == 0 and takeorpay_by_plant is not None:
                share = takeorpay_by_plant.get(int(gen.plant_code))
                if share is not None:
                    fuel_frac = 1.0 - float(share)
            expanded.append(
                Generator(
                    unit_id=f"{gen.unit_id}_t{ti + 1}",
                    name=gen.name,
                    zone=gen.zone,
                    fuel_type="coal",
                    efficiency_bin=gen.efficiency_bin,
                    pmax_mw=gen.pmax_mw * cap_frac,
                    pmin_mw=0.0,
                    heat_rate=gen.heat_rate,
                    vom=gen.vom,
                    emission_rate_co2=gen.emission_rate_co2,
                    nox_rate=gen.nox_rate,
                    so2_rate=gen.so2_rate,
                    eford=gen.eford,
                    online_year=gen.online_year,
                    retirement_year=gen.retirement_year,
                    plant_code=gen.plant_code,
                    plant_group=gen.plant_group,
                    state=gen.state,
                    coal_supply=gen.coal_supply,
                )
            )
            fuel_fracs.append(fuel_frac)
    return expanded, fuel_fracs


# ---------------------------------------------------------------------------
# Gas tranches (committed / economic / peaking)
# ---------------------------------------------------------------------------

# Gas fuel types eligible for the generic offer-curve tranche split.
_GAS_OFFER_FUELS: frozenset[str] = frozenset(
    {"gas_cc", "gas_cc_ccs", "gas_ct", "gas_st"}
)

# Gas offer-curve tranche SHARES (committed / economic / peaking) of nameplate
# by group, for the generic (non-CAMPD) offer curve. Moved to
# constants.GAS_TRANCHE_SHARES_BY_GROUP (2026-07 scalar-remediation sweep,
# B-GOV-1, rule #24 — no hardcoded per-group dicts in ``data/`` modules; value
# unchanged) — see that constant's docstring-comment for the structural-share
# rationale and the D-9 cross-ISO-leakage guard.
_GAS_TRANCHE_SHARES = GAS_TRANCHE_SHARES_BY_GROUP


def split_gas_tranches(
    generators: list, fuel_fracs: list[float], config: ScenarioConfig
) -> tuple[list, list[float]]:
    """Split each gas generator into committed / economic / peaking tranches.

    Gives the generic (non-CAMPD) gas fleet a stepped offer curve instead of a
    single flat block: a part-load **committed** band priced at the unit's heat
    rate × the per-class committed multiplier (``cc_/ct_/gas_st_committed_hr_mult``,
    >1, less efficient), an efficient **economic** band at the base heat rate,
    and a small **peaking** top slice at × ``ct_peak_hr_penalty`` (duct firing).
    CTs carry no committed band (peakers). Capacity is conserved; every gas
    tranche bids full fuel cost (gas is not take-or-pay), so ``fuel_frac = 1.0``.

    Runs after :func:`split_coal_tranches`, so it takes that pass's
    ``fuel_fracs`` and carries each non-gas generator (incl. coal tranches with
    their take-or-pay passthrough) through unchanged. Used for non-ERCOT
    calibration when ``config.gas_offer_curve`` is set; ERCOT's offer curve
    comes from its CAMPD bins, not this path.
    """
    committed_mult = {
        "CC_REGULAR": config.cc_committed_hr_mult,
        "CC_CHP": config.cc_committed_hr_mult,
        "ST_GAS": config.gas_st_committed_hr_mult,
        "ST_CHP": config.gas_st_committed_hr_mult,
        "CT_PEAKER": config.ct_committed_hr_mult,
        "CT_CHP": config.ct_committed_hr_mult,
    }
    expanded: list = []
    out_fracs: list[float] = []
    for gen, ff in zip(generators, fuel_fracs):
        shares = _GAS_TRANCHE_SHARES.get(gen.plant_group)
        if gen.fuel_type not in _GAS_OFFER_FUELS or shares is None:
            expanded.append(gen)
            out_fracs.append(ff)
            continue
        c_share, e_share, p_share = shares
        bands = (
            ("committed", c_share, committed_mult[gen.plant_group]),
            ("economic", e_share, 1.0),
            ("peaking", p_share, config.ct_peak_hr_penalty),
        )
        for suffix, share, hr_mult in bands:
            if share <= 0.0:
                continue
            expanded.append(
                gen.model_copy(
                    update={
                        "unit_id": f"{gen.unit_id}_{suffix}",
                        "pmax_mw": gen.pmax_mw * share,
                        "pmin_mw": 0.0,
                        "heat_rate": gen.heat_rate * hr_mult,
                    }
                )
            )
            out_fracs.append(1.0)
    return expanded, out_fracs


# ---------------------------------------------------------------------------
# Offer-curve lookup and economic ramp
# ---------------------------------------------------------------------------


def _offer_curve_for_group(
    group: str, plant_code: int, config: ScenarioConfig
) -> dict[str, float] | None:
    """Return the offer-curve band multipliers for a group, or ``None``.

    Reads ``config.offer_curve_by_group[group]`` (see :class:`ScenarioConfig`).
    Returns ``None`` — the legacy override / CSV path — when no curve is
    configured for the group or for an ST_GAS peaker plant (those keep their
    CSV heat rates, matching the ``gas_st_*_hr_override`` scope). COAL plants
    resolve to a supply-specific entry by their fuel rank — ERCOT
    ``COAL_LIGNITE`` / ``COAL_PRB`` and the EIA-923-derived ``COAL_BIT`` /
    ``COAL_WC`` (bituminous / waste coal; sub-bituminous routes to
    ``COAL_PRB``) — falling back to the generic ``COAL`` entry.

    When ``config.ct_intermediate_split`` is set, a ``CT_PEAKER`` plant in the
    measured intermediate-duty cohort (:func:`ct_intermediate_plants`) resolves
    to the flatter ``CT_INTERMEDIATE`` curve when one is configured, so its
    always-on energy clears like the intermediate unit it is rather than
    carrying the true-peaker start-cost hurdle. Likewise, when
    ``config.cc_intermediate_split`` is set a ``CC_REGULAR`` plant in the
    measured baseload-duty cohort (:func:`cc_intermediate_plants`) resolves to
    the flatter ``CC_INTERMEDIATE`` curve, whose econ ramp matches a committed
    CC's near-flat full-load incremental cost (the duct-burner peak band is
    unchanged).
    """
    from market_sim.data.coal import coal_supply_class
    from market_sim.data.fleet import (
        _COAL_SUPPLY_TO_CURVE,
        cc_intermediate_plants,
        ct_intermediate_plants,
        st_gas_intermediate_plants,
    )
    from market_sim.data.outages import ST_GAS_PEAKER_PLANTS

    curves = getattr(config, "offer_curve_by_group", None) or {}
    if group == "COAL":
        key = _COAL_SUPPLY_TO_CURVE.get(coal_supply_class(int(plant_code)))
        return (
            curves.get(key) if key and curves.get(key) else curves.get("COAL")
        ) or None
    if group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS:
        return None
    if group == "ST_GAS" and getattr(config, "st_gas_intermediate_split", False):
        iso = str(getattr(config, "iso", "ERCOT"))
        thr = float(getattr(config, "st_gas_intermediate_cf_threshold", 50.0))
        if int(plant_code) in st_gas_intermediate_plants(iso, thr):
            inter = curves.get("ST_GAS_INTERMEDIATE")
            if inter:
                return inter
    if group == "CT_PEAKER" and getattr(config, "ct_intermediate_split", False):
        iso = str(getattr(config, "iso", "ERCOT"))
        thr = float(getattr(config, "ct_intermediate_cf_threshold", 50.0))
        if int(plant_code) in ct_intermediate_plants(iso, thr):
            inter = curves.get("CT_INTERMEDIATE")
            if inter:
                return inter
    if group == "CC_REGULAR" and getattr(config, "cc_intermediate_split", False):
        iso = str(getattr(config, "iso", "ERCOT"))
        thr = float(getattr(config, "cc_intermediate_cf_threshold", 50.0))
        if int(plant_code) in cc_intermediate_plants(iso, thr):
            inter = curves.get("CC_INTERMEDIATE")
            if inter:
                return inter
    return curves.get(group) or None


def _econ_split_for_group(
    group: str, plant_code: int, config: ScenarioConfig
) -> tuple[float, float, float] | None:
    """Return ``(split_frac, lo_hr_mult, hi_hr_mult)`` for the econ split, or ``None``.

    Reads ``config.econ_split_by_group[group] = [split_frac, lo_hr_mult,
    hi_hr_mult]`` (see :class:`ScenarioConfig`). Returns ``None`` — a single
    economic tranche, the default behavior — when no split is configured for
    the group or for an ST_GAS peaker plant (those dispatch on CSV heat rates,
    matching the ``gas_st_*_hr_override`` scope). ``split_frac`` is clamped to
    ``[0, 1]``.
    """
    from market_sim.data.outages import ST_GAS_PEAKER_PLANTS

    spec_map = getattr(config, "econ_split_by_group", None) or {}
    spec = spec_map.get(group)
    if not spec:
        return None
    if group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS:
        return None
    frac, lo_mult, hi_mult = float(spec[0]), float(spec[1]), float(spec[2])
    return max(0.0, min(1.0, frac)), lo_mult, hi_mult


def _econ_curve_steps(
    base_hr: float,
    lo_mult: float,
    pk_mult: float,
    curve_cap: float,
    n: int,
    exp: float,
    mid: float | None = None,
) -> list[tuple[str, float, float, float, int, int, float]]:
    """Slice a rising economic ramp into ``n`` flat sub-tranches.

    Returns ``(suffix, cap, heat_rate, vom_mult, min_run, min_down, startup)``
    tuples — ``n`` equal-capacity slices whose heat-rate multiplier rises from
    ``lo_mult`` toward ``pk_mult`` along ``mult(t) = lo + (pk - lo) * t**exp``,
    ``t = (k + 0.5)/n``. ``exp == 1`` is a straight (linear) ramp matching a
    thermal unit's gently-rising incremental heat rate; ``exp > 1`` is convex
    (cheap-bottom). When ``mid`` is given it replaces the power shape with a
    two-segment piecewise-linear ramp anchored at the capacity midpoint:
    ``f(0) = 0``, ``f(0.5) = mid``, ``f(1) = 1`` (fraction of the lo->pk
    rise), so ``mid < 0.5`` keeps the middle of the curve cheap and
    concentrates the rise in the top slices — an independent shape control
    the single ``exp`` exponent cannot express. The slices carry no min-run
    or start cost — they are incremental output of an already-committed
    unit. Suffixes start with ``econ`` (``econc00`` …) so
    :func:`apply_commitment_with_coal_pin` couples them to the bin's
    committed tranche and shuts them down together.
    """
    slice_cap = curve_cap / n
    steps: list[tuple[str, float, float, float, int, int, float]] = []
    for k in range(n):
        t = (k + 0.5) / n
        if mid is not None:
            f = 2.0 * mid * t if t <= 0.5 else mid + (1.0 - mid) * (2.0 * t - 1.0)
        else:
            f = t**exp
        mult = lo_mult + (pk_mult - lo_mult) * f
        steps.append((f"econc{k:02d}", slice_cap, base_hr * mult, 1.0, 0, 0, 0.0))
    return steps


# ---------------------------------------------------------------------------
# Dashboard band visualization
# ---------------------------------------------------------------------------


def _bands_from_shares(
    raw: list[tuple[str, float, float, bool]], is_coal: bool
) -> list[dict]:
    """Stack ``(name, pct_of_nameplate, hr_mult, vom)`` tranches into CF bands.

    Bands accumulate from CF 0 in dispatch fill order, dropping empty ones. The
    non-coal must-run share is host steam removed from the grid, so it is not
    shown and does not shift the grid bands (committed still starts at CF 0);
    the coal must-run band is the in-LP VOM-only floor and is shown from 0.
    """
    bands: list[dict] = []
    cursor = 0.0
    for name, pct, mult, vom in raw:
        if name == "must-run" and not is_coal:
            continue
        lo, hi = cursor, cursor + pct
        cursor = hi
        if pct <= 0.5:
            continue
        bands.append(
            {
                "name": name,
                "cf_lo": round(lo, 1),
                "cf_hi": round(hi, 1),
                "mult": round(mult, 3),
                "vom": vom,
            }
        )
    return bands


def plant_tranche_bands(b: "pd.Series | dict", config: ScenarioConfig) -> list[dict]:
    """Return one plant's offer-curve tranche bands on the capacity-factor axis.

    Mirrors the tranche capacity and per-band heat-rate resolution in
    :func:`bins_to_fleet` (same offer-curve lookup, per-plant committed %,
    peaking override, econ split and CC duct-burner peak) and converts the
    cumulative tranche capacities into capacity-factor edges (percent of
    nameplate). The bands stack in dispatch fill order — must-run, committed,
    econ-lo, econ-hi, peak — so the dashboard can mark where each band engages
    on the CF axis and label the heat-rate multiplier priced there.

    Args:
        b: One row of the :func:`load_campd_bins` frame (or an equivalent
            mapping) for a single plant.
        config: The run's scenario configuration (offer curves, per-plant
            committed flag, mustrun overrides).

    Returns:
        A list of ``{"name", "cf_lo", "cf_hi", "mult", "vom"}`` dicts — one per
        non-empty band, in increasing CF order. ``mult`` is the band heat rate
        over the plant's base HR; ``vom`` flags the must-run band, which bids
        VOM-only (its fuel is sunk) rather than at a heat-rate multiplier.
        Empty when the plant has no nameplate.
    """
    from market_sim.data.chp import chp_btm_pct
    from market_sim.data.coal import COAL_PLANT_SUPPLY, coal_supply_class
    from market_sim.data.fleet import (
        BIN_GROUP_TO_FUEL,
        CC_REGULAR_COMMITTED_PCT_BY_PLANT,
        COAL_MUSTRUN_BY_PLANT,
        PETRA_NOVA_PARASITIC_PCT,
        PETRA_NOVA_PLANT_CODE,
        cc_duct_burner_peak_mult,
        cc_duct_peaking_pct,
        load_plant_tranche_config,
    )
    from market_sim.data.outages import ST_GAS_PEAKER_PLANTS

    group = str(b["Plant_Group"])
    plant_code = int(b["Plant_Code"])
    nameplate = float(b["capacity_mw"])
    if nameplate <= 0.0:
        return []
    fuel = BIN_GROUP_TO_FUEL[group]

    # Per-plant tranche-config sheet wins (same precedence as bins_to_fleet):
    # build the bands straight from the sheet's shares + multipliers so the
    # dashboard markers track what the user edited.
    _ov_path = getattr(config, "plant_tranche_config_path", None)
    if _ov_path:
        ov = load_plant_tranche_config(_ov_path).get(plant_code)
        if ov is not None:
            return _bands_from_shares(
                [
                    ("must-run", ov["pct_mr"], ov["hr_mr"], True),
                    ("committed", ov["pct_mc"], ov["hr_mc"], False),
                    ("econ-lo", ov["pct_lo"], ov["hr_lo"], False),
                    ("econ-hi", ov["pct_hi"], ov["hr_hi"], False),
                    ("peak", ov["pct_pk"], ov["hr_pk"], False),
                ],
                is_coal=(fuel == "coal"),
            )

    # Petra Nova (own classification, see PETRA_NOVA_* constants): one band
    # forced to PETRA_NOVA_MIN_CF of net capacity whenever available.
    if (
        plant_code == PETRA_NOVA_PLANT_CODE
        and group == "CT_CHP"
        and getattr(config, "chp_steam_following", False)
    ):
        net_pct = 100.0 - PETRA_NOVA_PARASITIC_PCT
        return [
            {
                "name": "ccs must-run",
                "cf_lo": 0.0,
                "cf_hi": round(net_pct, 1),
                "mult": 1.0,
                "vom": False,
            }
        ]

    offer = _offer_curve_for_group(group, plant_code, config)

    # Resolve must-run / committed / peaking percentages exactly as
    # bins_to_fleet does (coal overrides, CHP host-steam, per-plant committed,
    # offer peaking override).
    pct_mr = float(b["pct_mr"])
    if fuel == "coal":
        _supply = COAL_PLANT_SUPPLY.get(plant_code, "")
        if config.coal_mustrun_per_plant and plant_code in COAL_MUSTRUN_BY_PLANT:
            pct_mr = COAL_MUSTRUN_BY_PLANT[plant_code]
        elif _supply == "lignite" and config.coal_lignite_mustrun_override is not None:
            pct_mr = config.coal_lignite_mustrun_override
        elif _supply == "prb" and config.coal_prb_mustrun_override is not None:
            pct_mr = config.coal_prb_mustrun_override
        # PJM bituminous spot-coal: fully dispatchable, no take-or-pay must-run
        # floor (mirrors bins_to_fleet so the dashboard CF bands match dispatch).
        if (
            getattr(config, "coal_bit_dispatchable", False)
            and coal_supply_class(plant_code) == "bituminous"
        ):
            pct_mr = 0.0
    if group in ("CC_CHP", "CT_CHP", "ST_CHP") and getattr(
        config, "chp_steam_following", False
    ):
        pct_mr = chp_btm_pct(plant_code, group, iso=getattr(config, "iso", "ERCOT"))
    pct_mc = float(b["pct_mc"])
    if offer is not None and "pct_committed" in offer:
        pct_mc = float(offer["pct_committed"])
    if (
        group == "CC_REGULAR"
        and getattr(config, "cc_committed_per_plant", False)
        and plant_code in CC_REGULAR_COMMITTED_PCT_BY_PLANT
    ):
        pct_mc = CC_REGULAR_COMMITTED_PCT_BY_PLANT[plant_code]
    pct_peak = float(b["pct_peak"])
    if offer is not None and "pct_peaking" in offer:
        pct_peak = float(offer["pct_peaking"])
    if group in ("CC_REGULAR", "CC_CHP") and getattr(config, "cc_duct_peaking", False):
        _dpk = cc_duct_peaking_pct().get(plant_code)
        if _dpk is not None:
            pct_peak = _dpk

    if fuel == "coal":
        mustrun_cap = nameplate * pct_mr / 100.0
        grid_cap = nameplate - mustrun_cap
    else:
        mustrun_cap = 0.0
        grid_cap = nameplate * (1.0 - pct_mr / 100.0)
    denom = 100.0 - pct_mr
    committed_cap = grid_cap * pct_mc / denom if denom > 0.0 else 0.0
    peak_cap = grid_cap * pct_peak / denom if denom > 0.0 else 0.0
    econ_cap = max(grid_cap - committed_cap - peak_cap, 0.0)

    # Per-band heat rates, mirroring bins_to_fleet (offer-curve multipliers,
    # CC duct-burner peak, or the legacy per-class overrides / CSV columns).
    base_hr = float(b["hr_weighted"])
    mustrun_hr = float(b["hr_mr"])
    committed_hr = float(b["hr_mc"])
    econ_hr = float(b["hr_econ"])
    peak_hr = float(b["hr_peak"])
    if offer is not None:
        committed_hr = base_hr * float(offer["committed"])
        if "peak" in offer:
            peak_hr = base_hr * float(offer["peak"])
        elif group in ("CC_REGULAR", "CC_CHP"):
            peak_hr = base_hr * cc_duct_burner_peak_mult(b.get("Turbine_Class"))
        else:
            peak_hr = base_hr * float(offer["peak"])
    else:
        cc_mc = config.cc_committed_hr_override
        if group in ("CC_REGULAR", "CC_CHP") and cc_mc is not None:
            committed_hr = base_hr * cc_mc
            econ_hr = base_hr * _hr_override(
                config.cc_econ_hr_override, CC_ECON_HR_OVERRIDE_DEFAULT
            )
            peak_hr = base_hr * _hr_override(
                config.cc_peak_hr_override, CC_PEAK_HR_OVERRIDE_DEFAULT
            )
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
        ct_mc = config.ct_committed_hr_override
        if group == "CT_CHP" and ct_mc is not None:
            committed_hr = base_hr * ct_mc
            econ_hr = base_hr * _hr_override(
                config.ct_econ_hr_override, CT_ECON_HR_OVERRIDE_DEFAULT
            )
            peak_hr = base_hr * _hr_override(
                config.ct_peak_hr_override, CT_PEAK_HR_OVERRIDE_DEFAULT
            )

    if offer is not None:
        share = float(offer["econ_low_share"])
        econ_steps = [
            ("econ-lo", econ_cap * share, base_hr * float(offer["econ_low"])),
            ("econ-hi", econ_cap * (1.0 - share), base_hr * float(offer["econ_high"])),
        ]
    elif (split := _econ_split_for_group(group, plant_code, config)) is not None:
        split_frac, lo_mult, hi_mult = split
        econ_steps = [
            ("econ-lo", econ_cap * split_frac, base_hr * lo_mult),
            ("econ-hi", econ_cap * (1.0 - split_frac), base_hr * hi_mult),
        ]
    else:
        econ_steps = [("econ", econ_cap, econ_hr)]

    # Peak band: mirrors bins_to_fleet — the measured ``peak_ladder`` splits
    # the band into equal-capacity quantile rungs; otherwise one flat tranche.
    ladder = offer.get("peak_ladder") if offer is not None else None
    if ladder:
        peak_steps = [
            (
                ("peak" if i == 0 else f"peak{i + 1}"),
                peak_cap * float(share),
                base_hr * float(mult),
                False,
            )
            for i, (share, mult) in enumerate(ladder)
        ]
    else:
        peak_steps = [("peak", peak_cap, peak_hr, False)]
    raw = [
        ("must-run", mustrun_cap, mustrun_hr, True),
        ("committed", committed_cap, committed_hr, False),
        *[(name, cap, hr, False) for name, cap, hr in econ_steps],
        *peak_steps,
    ]
    bands: list[dict] = []
    cursor = 0.0
    for name, cap, hr, vom_only in raw:
        lo, hi = cursor, cursor + cap
        cursor = hi
        if cap <= 0.5:  # dropped from the LP in bins_to_fleet
            continue
        bands.append(
            {
                "name": name,
                "cf_lo": round(lo / nameplate * 100.0, 1),
                "cf_hi": round(hi / nameplate * 100.0, 1),
                "mult": round(hr / base_hr, 3) if base_hr > 0.0 else None,
                "vom": vom_only,
            }
        )
    return bands
