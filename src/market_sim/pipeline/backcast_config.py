"""Backcast ScenarioConfig builder (orchestrator-unification Stage 7).

:func:`backcast_config` builds the per-year backcast :class:`ScenarioConfig`
from a small set of explicit parameters plus a large set of calibrated,
ISO-conditioned defaults (offer curves, gas-basis mechanisms, reliability
overlays, storage vintage ramps, ...). Moved here verbatim from
``scripts/run_calibration.py``'s ``_calibration_config`` — pure code motion,
byte-identical output for every existing caller.

The env-var ERCOT gas knobs (``ERCOT_ZONAL_GAS``, ``ERCOT_GAS_FLOOR``, etc.)
are a known, tracked rule-24 exception (default-off diagnostic probes no
keeper enables) — out of this stage's scope; see
``docs/handoffs/orchestrator-unification-plan-2026-07.md`` §4.
"""

from __future__ import annotations

import logging
import os
from dataclasses import fields

from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
from market_sim.config.scenarios import ScenarioConfig

logger = logging.getLogger(__name__)


def _deep_merge_offer_curve(
    base: dict[str, dict[str, float]],
    overrides: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Deep-merge ``overrides`` onto the default ``offer_curve_by_group``.

    Each top-level key is a fleet class (CC_REGULAR, CT_PEAKER, ...); the
    nested dict holds the band multipliers (committed, econ_low, econ_high,
    peak, econ_low_share, pct_peaking). Only the bands named in ``overrides``
    are replaced; every unspecified band keeps its calibrated default, so a
    caller can tune one knob on one class without restating the whole curve.
    Unknown classes/bands are passed through unchanged (the dispatch code
    ignores keys it does not consume) so a typo fails loudly downstream
    rather than being silently dropped here.
    """
    merged = {cls: dict(bands) for cls, bands in base.items()}
    for cls, bands in overrides.items():
        if not isinstance(bands, dict):
            raise ValueError(
                f"offer-curve override for {cls!r} must be an object of "
                f"band->multiplier, got {type(bands).__name__}"
            )
        merged.setdefault(cls, {}).update(bands)
    return merged


def _apply_offer_curve_deltas(
    base: dict[str, dict[str, float]],
    deltas: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Return ``base`` with each ``deltas`` value ADDED to the current band.

    Unlike :func:`_deep_merge_offer_curve` (absolute replacement), this nudges
    a band relative to whatever it already is: ``{"CT_PEAKER":{"committed":0.05}}``
    turns a 1.40 committed multiplier into 1.45, and ``-0.05`` into 1.35 — so a
    re-tune does not have to restate the absolute value. The class/band must
    already exist in ``base`` (you can only nudge a band the offer curve
    actually has); an unknown one raises with the valid options listed.
    """
    merged = {cls: dict(bands) for cls, bands in base.items()}
    for cls, bands in deltas.items():
        if cls not in merged:
            raise ValueError(
                f"offer-curve delta for unknown class {cls!r}; valid classes: "
                f"{', '.join(sorted(merged))}"
            )
        if not isinstance(bands, dict):
            raise ValueError(
                f"offer-curve delta for {cls!r} must be an object of "
                f"band->delta, got {type(bands).__name__}"
            )
        for band, delta in bands.items():
            if band not in merged[cls]:
                raise ValueError(
                    f"offer-curve delta for unknown band {cls}.{band!r}; "
                    f"{cls} bands: {', '.join(sorted(merged[cls]))}"
                )
            merged[cls][band] = merged[cls][band] + delta
    return merged


# The core gas classes whose generic band multipliers are ERCOT-lineage and must
# NOT silently cross ISO boundaries (audit C-11/C-13, rule #24). The
# ``*_INTERMEDIATE`` classes are a measured-duty-shape mechanism (not
# ERCOT-residual-fitted) and coal classes route by EIA-923 fuel rank, so both are
# left generic — only these five gas classes are neutralized.
_GENERIC_NEUTRAL_GAS_CLASSES: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_CHP",
    "CT_PEAKER",
    "ST_GAS",
)


def _neutralize_generic_gas_bands(
    base: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Return ``base`` with the generic gas band MULTIPLIERS set to neutral 1.0.

    Rule #24 / audit C-11/C-13: the generic (non-ERCOT/non-PJM) offer-curve
    fallback must carry neutral bands, so an ISO without an explicit grounded
    value inherits ``1.0`` (offer at the plant's own base heat rate) rather than
    a value fitted on ERCOT's residual. Only the four heat-rate MULTIPLIER bands
    (``committed``, ``econ_low``, ``econ_high``, ``peak``) of the five core gas
    classes are reset; the STRUCTURAL tranche shares (``econ_low_share``,
    ``pct_peaking``) and every other class (coal, ``*_INTERMEDIATE``) are kept.
    Each non-ERCOT/non-PJM ISO then deep-merges its own grounded per-ISO curve on
    top; any band it does not restore stays neutral (a legible, non-inherited
    default), which is the de-leaked state.
    """
    out = {cls: dict(bands) for cls, bands in base.items()}
    for cls in _GENERIC_NEUTRAL_GAS_CLASSES:
        bands = out.get(cls)
        if not bands:
            continue
        for band in ("committed", "econ_low", "econ_high", "peak"):
            if band in bands:
                bands[band] = 1.0
    return out


# Calibrated PJM thermal offer curve (per-class band heat-rate multipliers on
# AHR x delivered fuel price). Price-calibrated multipliers, not literal heat
# rates. COAL_LIGNITE / COAL_PRB are carried for completeness but unused by
# PJM (its coal is bituminous / sub-bituminous / waste -> BIT/SUB/WC).
#
# CC_REGULAR: committed 0.87 (Manual 15 min-load SRMC floor, ERCOT keeper
# run-157 0.998; raised from 0.6624 which cleared overnight PJM LMP → CC
# over-generation miss #1), econ_high 1.50 (steepen upper ramp for miss #2,
# the 95-100% CF pile). CT_PEAKER: committed 1.25, econ_low 1.05 (pjm-59/61
# dispatch fix so CTs price as peakers not baseload; missing from pjm-58
# keeper). See docs/handoffs/pjm-cc-overgen-recommendation-2026-06.md.
_PJM_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 0.87,  # raised from 0.6624: Manual 15 min-load SRMC floor
        "econ_low": 0.92,  # raised from 0.7344: pjm-58 level
        "econ_high": 1.50,  # raised from 0.8928: steepen upper ramp (miss #2)
        "peak": 5.0,  # raised from 1.62: duct-firing scarcity (pjm-61)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CC_CHP": {
        "committed": 0.6624,
        "econ_low": 0.684,
        "econ_high": 0.8208,
        "peak": 1.62,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 0.864,
        "econ_low": 0.864,
        "econ_high": 0.864,
        "peak": 1.008,
        "econ_low_share": 0.50,
    },
    "CT_PEAKER": {
        "committed": 1.25,  # raised from 0.8784: peaker part-load penalty (pjm-59/61)
        "econ_low": 1.05,  # raised from 0.9792: base dispatch above HR (pjm-59/61)
        "econ_high": 1.40,  # from pjm-61 economic ramp
        "peak": 4.0,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,  # pjm-61: wider peaking band
    },
    "ST_GAS": {
        "committed": 0.4752,
        "econ_low": 0.6552,
        "econ_high": 0.90,
        "peak": 3.024,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
    "COAL_LIGNITE": {
        "committed": 0.684,
        "econ_low": 0.8208,
        "econ_high": 0.828,
        "peak": 1.116,
        "econ_low_share": 0.556,
    },
    "COAL_PRB": {
        "committed": 0.684,
        "econ_low": 0.5544,
        "econ_high": 0.8568,
        "peak": 1.0656,
        "econ_low_share": 0.556,
    },
    "COAL_BIT": {
        "committed": 0.648,
        "econ_low": 0.7056,
        # econ_high raised 0.8064 -> 0.90 (2026-07-07): PJM bituminous coal was
        # clearing too deep into the mid-merit economic band (over-running vs
        # EIA-923), so the top economic tranche now offers nearer the plant's own
        # base heat rate, steepening the coal supply curve above the committed
        # block while staying below the 1.044 peak/scarcity tranche. Offer-level
        # calibration on the registered offer_curve_by_group surface (rule #1
        # step 2), validated in the PJM re-solve — not a residual-fitted adder.
        "econ_high": 0.90,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
    "COAL_WC": {
        "committed": 0.612,
        "econ_low": 0.648,
        "econ_high": 0.7344,
        "peak": 0.864,
        "econ_low_share": 0.55,
    },
    "COAL": {
        "committed": 0.648,
        "econ_low": 0.684,
        "econ_high": 0.792,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
}


# NYISO gas offer curves, grounded in the Potomac Economics NYISO State-of-the-
# Market (SOM) reports and the measured per-plant CAMPD heat rates, NOT fitted to
# the backcast residual. Until now NYISO fell through to the generic non-PJM/non-
# ERCOT branch in offer_curve_by_group{} below, which carried ERCOT-fitted band
# multipliers that were never validated for NYISO — the root cause of the gas-
# class merit-order substitution error (CC_REGULAR under-runs while legacy gas
# steam over-runs). These are merged on top of that branch (_deep_merge_offer_
# curve), so only the named gas classes change; coal/CT_CHP/ST_CHP keep the
# generic defaults. Per-plant committed % and duct-firing peaking % still come
# from CAMPD (cc_committed_per_plant / cc_peaking_per_plant via
# thermal_tranches_NYISO.csv) and supersede the class-wide values here.
#
# Grounding (all band multipliers scale each plant's own measured base heat rate,
# bin_assignments_NYISO.csv Plant_Avg_HR; cap-weighted class HRs: CC_CHP 6.99,
# CC_REGULAR 7.76, CT_CHP 7.58, ST_GAS 10.61, CT_PEAKER 11.95 MMBtu/MWh):
#  - NYISO is a competitive energy market: suppliers offer close to short-run
#    marginal cost (2023 SOM §VI.A "output gap" 0.05% at the mitigation
#    threshold, 1.9% at ref+25%). So the multipliers encode a near-marginal-cost
#    SHAPE around each unit's real heat rate, not a strategic markup. The
#    physically-correct merit order is CC (efficient) < ST_GAS (legacy steam,
#    high HR) < CT_PEAKER.
#  - ST_GAS: 2023 & 2024 SOM Figure 2 / §I.B — "Steam turbine units appear to be
#    the most economically challenged... their high operating costs and physical
#    constraints... usually prevent steam units from earning much energy or
#    reserve revenue, except in Long Island [reliability contracts]." The generic
#    committed 0.81x put the legacy-steam min-load slice (0.81*10.61 = 8.6 eff
#    HR) BELOW the top of CC_REGULAR's econ ramp (1.27*7.76 = 9.9 eff HR), so an
#    inefficient steam unit undercut an efficient CC — physically backwards.
#    Raising committed to 0.97 (min-load eff HR ~= avg, steam part-load HR is no
#    better than full-load) puts steam back above CC across its whole econ range,
#    so it only runs in genuinely high-load hours / on the LI floor, matching the
#    SOM. NOTE the offer SHAPE only works if each plant's *base* heat rate is
#    right: Ravenswood (plant 2500) is a mixed CC+ST facility, and its 1,725 MW
#    ST_GAS row had inherited the 8.8 MMBtu/MWh *facility-blended* heat rate (the
#    CC efficiency leaking into the steam row), so 0.97x8.8 = 8.5 eff HR put the
#    big NYC steam unit BELOW CC's econ ramp (1.12x7.76 = 8.7) and it cleared
#    ahead of idle NYC CC in ~8.5k hr/yr (the 2023 CC_REGULAR -4 TWh / ST_GAS
#    +3.5 TWh merit inversion). Corrected the Ravenswood ST_GAS base HR to 9.5
#    (data.fleet.MIXED_FACILITY_STEAM_HR) — the steam units' own HR recovered by
#    backing the efficient CC out of the 8.8 generation-weighted CC+ST plant
#    blend (CC ~0.6 / steam ~0.15 CF -> steam ~9.5), modestly above the blend and
#    below the older NYC peers (Arthur Kill 11.27, Astoria 11.95). A measured-data
#    correction (CLAUDE.md rule #11: the blended HR was silently masking the
#    inversion), forward-reproducible, not fitted to the price/volume residual.
#  - CC_REGULAR / CC_CHP: the efficient gas workhorses. CC marginal HR is ~flat
#    and ~0.95x average across the bulk of the operating range (CAMPD CC fit,
#    also cited on the ERCOT curve), with the incremental HR rising toward full
#    load as the unit pushes against its rating (the approach to duct firing).
#    The CAMPD CC marginal-HR SRMC *reach* at the top of the econ ramp is
#    ~1.21x base_hr -- the SAME fit ERCOT's keeper uses (committed 0.87 /
#    econ_low 0.92 / econ_high 1.21). So the rising econ ramp now spans
#    econ_low 0.95 -> econ_high 1.21 (run 27 re-level; econ_high was 1.12).
#    WHY 1.12 was wrong: it compressed the upper econ slices BELOW the CAMPD CC
#    marginal HR, pricing the top of each CC's body too cheap. While the old
#    75% CC capacity wall was in place that compression was masked; once run 26
#    removed the wall (cc_nameplate_summer_derate -> full EIA-860 nameplate) the
#    un-walled CC fleet cleared its now-exposed top slices too cheap and mildly
#    over-ran on energy (CC_REGULAR ~+2 TWh/yr) while DEPRESSING the marginal
#    LMP (C3a 2023 -8.9% / 2024 -11.0%). Raising econ_high to the ERCOT/CAMPD
#    1.21 reach prices those marginal slices out, so CC stops over-running and
#    stops setting too-low a clearing price -- a grounded offer-LEVEL
#    calibration (CLAUDE.md rule #1 second step: right structure in run 26,
#    offer level here), grounded in the CAMPD CC marginal heat rate, NOT a
#    re-walled capacity nor a residual-fitted adder (rules #11/#12). econ_low
#    stays 0.95 (already above ERCOT's 0.92; the cheap baseload body is correct
#    -- the miss was only the compressed top). CC_CHP (most efficient, 6.99)
#    stays nudged a touch higher (econ_high 1.24, +0.03 over CC_REGULAR) to trim
#    its small over-run. The duct-firing peak stays a separate inflexible flat
#    tranche (2023 SOM §VI.A: "Some combined cycles offer inflexibly... to
#    manage physical operating constraints on the duct-fired portion"; duct
#    burners are not flexible enough for AGC/10-min reserves).
#  - CT_PEAKER: offers near marginal cost in NYISO's competitive market; the
#    generic committed 1.55 was an ERCOT P1 startup-cost hurdle never validated
#    here that parked the peakers idle. Lowered to 1.35 so peakers pick up the
#    high-load tail (SOM: NYC GTs run for peak/reliability), econ/peak unchanged.
#
# RUN-28 PROBE (rejected, 2026-06-25): re-grounding ALL of CC_REGULAR / CC_CHP /
# ST_GAS committed/econ_low/econ_high to NYISO's OWN CAMPD incremental-HR medians
# (scripts/derive_campd_marginal_hr.py: CC_REGULAR 0.632/0.784/0.925, CC_CHP
# 0.809/0.989/1.103, ST_GAS 0.818/0.825/0.830) was tried to remove the borrowed
# ERCOT reach. It CRATERED C3a mean LMP to -24/-26.5/-23.5% across 2023-25: the
# bare CEMS marginal heat rate is the marginal COST, not the OFFER — it omits the
# competitive offer markup (no-load/start/AS cost recovery + inframarginal rent)
# that NYISO has no offer disclosure to measure, so the borrowed 1.21 reach was
# proxying that real markup. Keeper stays this run-27 curve; the run-28 bundle
# (results/calibration/nyiso_28_native-hr) keeps the rejected curve + finding.
# The steam-side re-level WAS directionally right (it nearly halved the 2024
# ST_GAS under-run), so the run-29 path is a NYISO-grounded markup ON TOP of the
# native marginal HR, not a restored cross-ISO borrow. See the run-28 attestation
# and docs/calibration-best-so-far-nyiso.md.
#
# RUN-32 KEEPER (2026-06-26): the run-29 path executed on ST_GAS only. The legacy
# gas-steam offer is re-levelled to the native steam marginal HR x the CC-grounded
# competitive markup (1.31x): committed 0.97/econ_low 1.10/econ_high 1.45 ->
# 1.05/1.08/1.13 (see the ST_GAS inline comment). CC stays at the run-27 reach
# (the markup that holds the clearing price -- NOT stripped, unlike run-28). HARD
# C1 improves across the board (2023 ST_GAS -1.26 -> -0.01 TWh PASS, CC_REGULAR
# +1.70 -> +0.99 PASS; 2024 ST_GAS -4.14 -> -3.28, CC_REGULAR +2.09 -> +1.74); the
# flat measured band reproduces measured steam VOLUME almost exactly, validating
# the offer level a priori. SOFT C3a regresses to a documented CAVEAT (the keeper-27
# steep ramp was a compensating over-pricing propping up the mid-merit price;
# removing it exposes the ledgered reserve-scarcity tail) -- kept per rule #1.
# Keeper since it is the most structurally faithful NYISO config: measured-grounded
# steam offer + grounded CC reach. See the run-32 attestation.
_NYISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 0.90,
        "econ_low": 0.95,
        # DE-LEAKED (audit C-13, rule #25, B-NYI-1): econ_high was 1.21 — a CAMPD
        # CC marginal-HR reach value grounded on ERCOT's CC analysis and
        # cross-borrowed to NYISO, i.e. a rule-25 cross-ISO leak. It was retained
        # only because removing it craters C3a ≈ −24%, which is a residual
        # justification, not a NYISO-identified value — so it neutralizes to the
        # neutral 1.0 band (CC offers at its own econ heat rate, no borrowed
        # markup). The C3a hole this exposes is an OPEN ROOT CAUSE (rule #1):
        # the real missing mechanism is NYISO scarcity/reserve (RCPF/AS) price
        # formation, NOT a CC energy markup — see GitHub issue #1344. Do NOT
        # re-arm this markup to close C3a (rule #26, rule #1).
        "econ_high": 1.0,
        "peak": 2.25,  # physical F-class duct-burner ratio (not ERCOT-fitted)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CC_CHP": {
        # NYISO's own run-27 CHP curve (+0.03 over CC_REGULAR to trim CHP
        # over-run) — NYISO-identified, not the generic ERCOT fallback (else-arm
        # CC_CHP is 0.92/0.96/1.12). Left as-is; the residual-fit +0.03 is a DOF
        # item for the later NYISO calibration phase.
        "committed": 0.90,
        "econ_low": 0.98,
        "econ_high": 1.24,
        "peak": 2.25,  # physical F-class duct-burner ratio
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_PEAKER": {
        "committed": 1.35,  # NYISO/CAISO-grounded evening-ramp start hurdle
        #   (NYISO/ISO-NE CTs serve the ramp, not the ERCOT 1.55 idle-park).
        # econ bands DE-LEAKED from the ERCOT generic fallback (was econ_low 1.27
        # / econ_high 1.98) to neutral 1.0 (offer at the CT's own base heat rate):
        # NYISO carries no independent CT part-load heat-rate spread yet. OPEN
        # ROOT CAUSE (rule #1): a NYISO-grounded CT econ ramp (CAMPD CT heat-rate
        # spread) is a later disciplined-calibration item — NOT re-tuned here.
        "econ_low": 1.0,
        "econ_high": 1.0,
        # peak DE-LEAKED from the inherited ERCOT 13.15x $5,000-ORDC scarcity wall
        # (audit C-13) to 4.0 — NYISO's energy offer cap is $1,000 ($2,000
        # cost-based under scarcity), NOT ERCOT's $5,000 ORDC. This promotes the
        # NEISO-42 precedent (capped 13.15 -> 4.0 but never promoted). Same cap
        # and reasoning as PJM/CAISO/MISO/NEISO.
        "peak": 4.0,
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    # CT_CHP: DE-LEAKED from the generic ERCOT-lineage `else` branch (was
    # 1.10/1.20/1.20/1.40) to neutral 1.0 — NYISO carries no independent CT_CHP
    # heat-rate spread yet (later disciplined-calibration item, rule #1).
    "CT_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
    },
    "ST_GAS": {
        # run 32: re-levelled from the ERCOT-shaped rising ramp (0.97/1.10/1.45)
        # to NYISO's OWN measured CAMPD steam marginal HR x a grounded competitive
        # markup. Native steam marginal HR (NY+NJ CAMPD pooled,
        # nyiso_campd_marginal_hr_summary.csv) is committed 0.818 / econ_low 0.830
        # / econ_high 0.828 -- essentially FLAT (legacy steam part-load HR is no
        # better than full-load, matching the 2023/24 SOM). The bare marginal HR is
        # the marginal COST not the OFFER (run-28 finding: it craters C3a), so a
        # competitive markup is applied ON TOP: the CC class's own defensible reach
        # ratio (CC econ_high 1.21 / native CC marginal 0.925 = 1.31x) x the steam
        # native marginal (~0.82-0.83 x 1.31 ~= 1.08), with a thin monotone spread
        # 1.05 -> 1.13 to keep a valid rising offer and a modest scarcity reach
        # below the inflexible peak tranche. Effective HR 11.1-12.0 stays ABOVE CC
        # econ_high 9.4 and BELOW CT_PEAKER 16.1 (merit preserved, no inversion).
        # Recovers the legacy-steam under-run (2023 ST_GAS -1.26 -> -0.01 TWh,
        # near-EXACT -> the flat measured band reproduces measured steam volume,
        # validating the level a priori, not residual-fitted). The C3a depression
        # this exposes is the missing reserve-scarcity tail (ledgered, rule #1).
        "committed": 1.05,
        "econ_low": 1.08,
        "econ_high": 1.13,
        "peak": 4.20,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
}


# CAISO gas offer curves, grounded in the CAISO DMM (Department of Market
# Monitoring) State-of-the-Market reports and the measured per-plant CAMPD heat
# rates, NOT fitted to the price residual (CLAUDE.md rules #1/#11). Until now
# CAISO fell through every per-band ternary to the generic non-PJM/non-ERCOT
# `else` branch in offer_curve_by_group{} below, whose values were "fit to
# Colorado Bend II / Wolf Hollow II" — ERCOT plants — and carried the ERCOT
# CT_PEAKER `peak` 13.15x scarcity wall. That wall encodes ERCOT's $5,000 ORDC
# scarcity, which has no CAISO analogue (CAISO's energy offer cap is the $1,000
# soft cap, raised to $2,000 only with cost verification under extreme
# scarcity), so it inflated the 2023 high-price tail (744 h > $200 vs 21
# actual), while the ERCOT-fitted CC econ band (econ_low 1.06 / econ_high 1.27)
# over-priced the midday CC body (the domestic source of the CA-zone LMP
# over-price diagnosed in DIAGNOSIS-caiso36-body-overprice-domestic-2026-06-28).
# These are merged on top of that generic branch (_deep_merge_offer_curve), so
# only the named GAS classes (CC_REGULAR, CT_PEAKER) change; CC_CHP / CT_CHP /
# ST_GAS / coal keep the generic defaults. Per-plant committed % and duct-firing
# peaking % still come from CAMPD (cc_committed_per_plant / cc_peaking_per_plant
# via thermal_tranches_CAISO.csv) and supersede the class-wide values here.
#
# Grounding (band multipliers scale each plant's own measured base heat rate,
# bin_assignments_CAISO.csv Plant_Avg_HR; cap-weighted class base HRs:
# CC_REGULAR 7.44, CT_PEAKER 10.86 MMBtu/MWh):
#  - CAISO is a structurally competitive energy market (DMM 2023/2024 SOM): the
#    market-power mitigation Default Energy Bid (DEB) for a gas unit is
#    cost-based — gas x measured heat rate + variable O&M + a ~10% competitive
#    adder — so suppliers offer close to short-run marginal cost. The
#    multipliers therefore encode a near-SRMC SHAPE around each unit's real heat
#    rate, NOT a strategic markup or a residual-tuned level.
#  - CC_REGULAR: the efficient gas workhorse and the midday marginal class (the
#    diagnosis shows CA midday needs ~6.5 GW of economic gas_cc whose bid sets
#    the body price). The CAMPD CC marginal-HR fit is ~flat at ~0.95x average
#    across the body, rising to ~1.21x average at the top of the economic range
#    (the approach to duct firing) — the SAME fit ERCOT's and NYISO's keepers
#    use (committed 0.90 / econ_low 0.95 / econ_high 1.21). The generic
#    ERCOT-fitted econ_low 1.06 / econ_high 1.27 priced the CC body ~10% above
#    that measured incremental cost, the domestic driver of the midday over-
#    price; re-grounding to 0.95 -> 1.21 removes that ERCOT level premium. The
#    duct-firing `peak` stays the physical F-class duct-burner multiplier (2.25),
#    NOT capped — capping a real physical band to move price would be an
#    unphysical fit (rule #11).
#  - CT_PEAKER: offers near its DEB cost in CAISO's competitive market. The
#    `peak` band is capped at 4.0 (cap-weighted eff HR ~43, ~$150/MWh at 2023-25
#    gas — a defensible CAISO scarcity offer well inside the $1,000-2,000 soft
#    cap), the SAME cap and reasoning PJM adopted ("an ERCOT-style 13x wall is
#    far too high ... inflating the high-price tail"); it replaces the ERCOT
#    13.15x $5,000-ORDC wall that drove the 2023 > $200 tail. The econ band is
#    re-grounded to the DEB cost-plus-adder shape (econ_low 1.10 ~= HR x 1.1 at
#    the bottom of the range, econ_high 1.50 the rising part-load/hot-day reach)
#    in place of the ERCOT-fitted 1.27 / 1.98. The committed min-load start-cost
#    hurdle is lowered from the ERCOT 1.55 (which parks peakers idle) to 1.35
#    (NYISO-grounded): CAISO's fast-start CTs and aeroderivatives serve the steep
#    net-load evening ramp and should clear on the ramp rather than forcing the
#    CC duct-fire + startup tranches to set the evening price.
_CAISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        # LEVER A (2026-07-04, FINDING-caiso-evening-merit): raised 0.90 -> 1.00.
        #   The committed band is the min-STABLE-load (at/below-LSL) tranche
        #   (derive_campd_marginal_hr.py: "committed" = at/below LSL min-gen),
        #   whose true incremental heat rate is ABOVE the plant average (min-load
        #   is thermally inefficient). Multipliers scale Plant_Avg_HR, so 0.90x
        #   avg priced the min-load block ~$1.2/MWh BELOW true marginal cost AND
        #   below econ_low (0.95) — an INVERTED merit order (min-load block
        #   cheaper than the efficient incremental band). This borrowed
        #   (NYISO-aligned, not CAISO-measured) sub-cost offer emulated
        #   commitment and flooded cheap CC around the clock (+3.2 GW overnight
        #   over-run, LMP pinned ~$42, physically-backwards evening EXPORT to
        #   Malin/Palo Verde). 1.00x avg HR restores committed >= econ_low
        #   ordering and is still CONSERVATIVE vs the true (>avg) min-load HR; any
        #   avoided-startup credit belongs in an explicit UC layer, not the P1
        #   offer (rule #1; DOF ledger E8). econ_low is NOT raised — it is the
        #   measured CAMPD marginal SRMC (below), and lifting it would over-price
        #   incremental energy above marginal cost (reintroducing the caiso-36
        #   midday over-price).
        "committed": 1.00,
        "econ_low": 0.95,  # CAMPD CC flat body marginal HR ~0.95x avg = true
        #   incremental SRMC (generic ERCOT-fit 1.06 over-priced the midday body;
        #   held here — raising to 1.0 would over-price the incremental band).
        "econ_high": 1.21,  # CAMPD CC marginal-HR SRMC reach (ERCOT/NYISO fit;
        #   generic 1.27).
        "peak": 2.25,  # physical F-class duct-burner band, unchanged.
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_PEAKER": {
        "committed": 1.35,  # NYISO-grounded start hurdle; CAISO CTs serve the
        #   evening ramp (generic ERCOT idle-park hurdle was 1.55).
        "econ_low": 1.10,  # DEB cost + ~10% adder (generic ERCOT-fit 1.27).
        "econ_high": 1.50,  # rising part-load/hot-day reach (generic 1.98).
        "peak": 4.0,  # CAISO $1,000-2,000 soft-cap scarcity, capped far below
        #   the ERCOT $5,000-ORDC 13.15x wall (PJM's reasoning/value).
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    # CC_CHP / CT_CHP / ST_GAS below are PINNED to the values CAISO previously
    # inherited from the generic ERCOT-lineage `else` branch. They are NOT
    # CAISO-grounded — they are preserved verbatim ONLY so the neutral generic
    # fallback (rule #24, added by the 2026-07 cross-ISO-bands scrub) does not
    # silently change the caiso-51 keeper, which this scrub does not re-solve
    # (scope: MISO/NEISO/NYISO). Re-grounding these on CAISO's own DMM/CAMPD data
    # is a separate, out-of-scope CAISO item (audit §5.1 lists CAISO's tuned
    # surface elsewhere). Making the inheritance explicit here is what lets the
    # shared fallback go neutral without touching CAISO's dispatch.
    "CC_CHP": {
        # LEVER A (2026-07-04): committed 0.92 -> 1.00, same min-load-block
        #   physics as CC_REGULAR above (the borrowed sub-cost committed offer
        #   inverted committed<econ_low and flooded cheap CC). econ_low/econ_high
        #   held (marginal-SRMC / duct band); the steam-host floor
        #   (chp_steam_following) still governs the price-inelastic min-gen.
        "committed": 1.00,
        "econ_low": 0.96,
        "econ_high": 1.12,
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 1.10,
        "econ_low": 1.20,
        "econ_high": 1.20,
        "peak": 1.40,
        "econ_low_share": 0.50,
    },
    "ST_GAS": {
        "committed": 0.81,
        "econ_low": 1.05,
        "econ_high": 1.40,
        "peak": 4.20,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
}


# MISO gas offer curves, grounded in the measured per-plant CAMPD heat rates
# (bin_assignments_MISO.csv Plant_Avg_HR_MMBtu_MWh; cap-weighted class HRs:
# CC_CHP 6.76, CC_REGULAR 7.44, ST_GAS 11.27, CT_PEAKER 12.37 MMBtu/MWh) and the
# MISO market structure, NOT fitted to the backcast residual. Until now MISO was
# the only large multi-zone ISO with no branch: it fell through EVERY
# offer_curve_by_group ternary to the generic non-PJM/non-ERCOT/non-NEISO `else`,
# whose band multipliers were fit to ERCOT plants (Colorado Bend II / Wolf Hollow
# II) and never validated for MISO — including the 13.15x ERCOT-CT "peak" wall
# that PJM and CAISO already discarded. These are merged on top of that branch
# (_deep_merge_offer_curve), so ONLY the named gas classes change; coal / CC_CHP /
# CT_CHP / ST_GAS keep the generic defaults (they sit correctly in merit for MISO
# — see below). Per-plant committed % and duct-firing peaking % still come from
# CAMPD (cc_committed_per_plant / cc_peaking_per_plant via thermal_tranches_
# MISO.csv) and supersede the class-wide values here.
#
# Grounding (band multipliers scale each plant's own measured base heat rate):
#  - CC_REGULAR: MISO's entire CC fleet runs intermediate/baseload (thermal_
#    tranches_MISO.csv: all 44 CC_REGULAR plants measure median CF 50-150%, mean
#    ~90% — near-100% CF). The generic curve was fit to ERCOT's duct-fire-heavy
#    2x1 peaker CCs and carries a rising start-cost-amortized econ ramp (econ_low
#    1.06 / econ_high 1.27) that over-prices the upper operating range of an
#    already-committed baseload CC, whose incremental energy is ~flat at ~0.93x
#    its own average heat rate (the measured CAMPD CC shape, negligible routine
#    duct-firing). That over-pricing pushes the CC's upper econ tranches above the
#    clearing price -> the model under-runs the CC fleet (the 2023/2024 gas-CC
#    under-run, ~-23/-20 TWh vs EIA-923). Flatten the econ ramp to the measured
#    near-baseload incremental cost (econ 0.95 -> 1.08, straddling the full-load
#    0.93x and the average 1.0x) while KEEPING the physically-real F-class duct-
#    burner scarcity peak (2.25). This is the same flat curve validated via the
#    cc_intermediate_split CC_INTERMEDIATE cohort routing; promoting it to the
#    MISO CC_REGULAR BASE makes MISO's CC correct even on a non-split run, and
#    renders the split a near-no-op for MISO's all-baseload fleet (it stays
#    available for genuinely MIXED CC duty — a future MISO peaker CC, or another
#    ISO).
#    The committed (min-stable-load) band was separately raised 0.92 -> 1.20 to
#    the measured part-load premium: a CC's min-load $/MWh is ~30-40% above its
#    full-load SRMC (CAMPD part-load shape), so the min-load tranche MUST price
#    above the full-load body. The old 0.92 (6.84 eff HR) sat BELOW econ_low
#    (0.95*7.44 = 7.07) — the inverse of the real part-load curve — an unphysical,
#    artificially-cheap min-load block. Lifting committed to 1.20 (8.93 eff HR)
#    restores the correct part-load ordering (committed > econ_high > econ_low).
#    This is a pure offer-SHAPE faithfulness fix and is METRIC-NEUTRAL: vs the
#    miso22 base (committed 0.92), gmModel CC_REGULAR moves only -1.5/-0.8/-0.9
#    TWh (2023/24/25, right direction) and ST_GAS / CT_PEAKER / coal / prices all
#    move <0.5 TWh and <$0.1/MWh. It does NOT close the ST_GAS under-run
#    (gmModel ST_GAS stays -7.2/-9.5/-8.1 vs EIA-923) — the committed band is a
#    must-run min-load PRICE block whose VOLUME is set by commitment, not by its
#    own offer, so raising its price corrects the merit ORDER without moving
#    volume. 1.20 is capped just under the ST_GAS non-inversion ceiling
#    (9.13/7.44 = 1.227). Merit preserved: CC econ_high 1.08*7.44 = 8.0 and CC
#    committed 1.20*7.44 = 8.93 eff HR both stay below ST_GAS's min-load (generic
#    committed 0.81*11.27 = 9.1) and CT_PEAKER.
#    NOTE the residual CC_REGULAR over-run (+24/+25/+13) and CT_PEAKER under-run
#    (-19.6/-15.1/-16.6) are NOT offer-curve-addressable: CC's excess is in its
#    measured-flat econ body (must not be steepened — rule #11) and CT's deficit
#    is gated by the missing scarcity mechanism (0 model >$200 hours; RDC/ELMP
#    co-optimization is a separate future lever) plus the 2024/2025 import
#    under-run (-17.0/-5.9 vs actual -23.1/-19.0 TWh). Both are flagged as
#    discovered root causes (rules #1/#11), not papered over here.
#  - CT_PEAKER: CAP the peak band well below the inherited 13.15x ERCOT wall.
#    MISO's energy offer cap is ~$1000-2000/MWh (the ELMP shadow price plus the
#    Reserve Demand Curve / RDT scarcity adder), NOT ERCOT's $5000 ORDC, so a
#    13x heat-rate wall is far too high and inflates the high-price tail — the
#    same reasoning PJM used to cap its CT_PEAKER at 4.0. Drop the peak to 4.0
#    (~$1500/MWh at a 12.4 base HR and typical MISO gas), the MISO-cap-consistent
#    ballpark. The committed start-cost hurdle (1.55) and the econ ramp
#    (1.27 -> 1.98) are left at the generic shape (they are not the ERCOT-specific
#    artifact; only the $5000-ORDC peak is). MISO currently shows 0 scarcity
#    (>$200) hours, so this is forward-correctness — removing an inherited tail
#    that would mis-fire in a forecast — not a live price change.
#  - CC_CHP / CT_CHP / ST_GAS: NOT overridden. The generic CC_CHP (econ
#    0.96 -> 1.12) is already flat and the efficient cogen CCs (measured HR 6.76)
#    sit correctly below CC_REGULAR. The generic ST_GAS committed 0.81*11.27 =
#    9.1 eff HR sits ABOVE the new flat CC_REGULAR (max 8.0), so there is no merit
#    inversion for MISO — and MISO's baseload steam is separately handled by the
#    st_gas_intermediate split (ST_GAS_INTERMEDIATE), so the base ST_GAS curve
#    only prices true-peaker steam. Leaving these generic keeps the change tight
#    and grounded (rule #11: merge only the named bands that diverge).
#
# LEVEL sanity-checked against Potomac Economics, "State of the Market Report for
# the MISO Electricity Markets" (the MISO IMM). A worse interchange / energy
# balance from this curve is a discovered bug to root-cause, not a reason to
# refit (rules #1/#11).
_MISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        # Min-stable-load premium: a CC's part-load $/MWh is ~30-40% above its
        # full-load SRMC (measured CAMPD part-load shape), so the committed
        # (min-load) tranche must price ABOVE the full-load body, not below it.
        # Held at 1.20 (run 30): the committed tranche is a merit-order lever,
        # NOT a volume lever — even at 1.38 (tested), the committed band at
        # ~$26/MWh still clears below $32/MWh system price, so CC volume is
        # unchanged while the price lift draws excess imports (-17 TWh energy
        # balance). CC over-dispatch vs CAMPD requires a different mechanism.
        "committed": 1.20,
        "econ_low": 0.95,  # flat baseload incremental (straddles full-load 0.93x)
        "econ_high": 1.08,  # measured near-flat full-load HR, NOT the ERCOT 1.27 ramp
        "peak": 2.25,  # physically-real F-class duct-burner scarcity band (kept)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_PEAKER": {
        # committed / econ bands DE-LEAKED from the ERCOT generic fallback (was
        # committed 1.55 / econ_low 1.27 / econ_high 1.98 — the "generic shape"
        # prior comments retained is exactly the ERCOT else-arm) to neutral 1.0:
        # MISO carries no independent CT part-load heat-rate spread yet. OPEN ROOT
        # CAUSE (rule #1): a MISO-grounded CT committed hurdle + econ ramp (CAMPD
        # CT heat-rate spread, base HR ~12.37) is a later disciplined-calibration
        # item — NOT re-tuned here. Expect CT over-run vs the prior 1.55 hurdle.
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 4.00,  # MISO offer cap ~$1-2k/MWh -> caps the 13.15x ERCOT-ORDC wall
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    # CC_CHP / CT_CHP / ST_GAS: DE-LEAKED from the generic ERCOT-lineage `else`
    # branch to neutral 1.0 multipliers (offer at each unit's own base heat rate),
    # keeping structural tranche shares and the physical F-class CC duct-burner
    # peak (2.25). MISO carries no independent per-class heat-rate spread for
    # these yet; grounding them on MISO CAMPD spreads (CC_CHP base HR ~6.76,
    # ST_GAS ~11.27) is a later disciplined-calibration item (rule #1), not
    # re-tuned here. Base ST_GAS prices only true-peaker steam (baseload steam
    # routes to ST_GAS_INTERMEDIATE, untouched).
    "CC_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 2.25,  # physical F-class duct-burner ratio (not ERCOT-fitted)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
    },
    "ST_GAS": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
}


# NEISO gas offer curve — ISO-NE-grounded gas-class band multipliers, at parity
# with _PJM_OFFER_CURVE / _NYISO_OFFER_CURVE / _CAISO_OFFER_CURVE / _MISO_OFFER_CURVE.
# Deep-merged on top of the generic non-PJM/non-ERCOT branch so only the named
# GAS classes change; coal / *_INTERMEDIATE keep the generic defaults, and the
# per-plant committed/peaking % from NEISO's CAMPD sheet still supersede the
# class-wide values.
#
# Grounding (band multipliers scale each plant's own measured base heat rate,
# bin_assignments_NEISO.csv Plant_Avg_HR; cap-weighted class base HRs:
# CC_REGULAR ~7.2, CC_CHP ~7.0, CT_PEAKER ~12.0, ST_GAS ~10.6 MMBtu/MWh):
#
#  - CC_REGULAR: committed 1.27 — NEISO min-stable-load offer anchored to the
#    measured CAMPD CC heat-rate shape (min-load 40-55% of nameplate runs ~1.30x
#    the fleet-average HR; raising committed to the full-load offer level (=
#    econ_high 1.27) removes the artificially-cheap min-load block the removed
#    net-summer CC "wall" was masking — ISO-NE Market Rule 1 incremental-energy
#    shape, a conservative floor, not residual-fitted). econ_low 1.06 / econ_high
#    1.27 / peak 2.25 (F-class duct-burner mult) carried from the generic curve.
#  - CC_CHP / CT_CHP / ST_GAS: the generic gas-class values, unchanged.
#  - CT_PEAKER: CAP the peak band at 4.0, down from the inherited 13.15x ERCOT
#    scarcity wall. ISO-NE's energy offer cap is $1,000 ($2,000 cost-based under
#    extreme scarcity per Market Rule 1 §III.1.10.1A); the RCPF reserve scarcity
#    adder tops near $1,500-2,000 (FERC Order 831). That is NOT ERCOT's $5,000
#    ORDC. A 13.15x peak wall creates CT offers ~$550/MWh (12 HR × 13.15 × $3.50
#    gas) that NEVER clear in normal operations — effectively parking the entire
#    CT fleet idle except under extreme scarcity the model can't produce without
#    reserve co-optimization. Cap to 4.0 (~$168/MWh eff offer at typical gas), the
#    SAME cap and reasoning PJM/CAISO/MISO adopted ("an ERCOT-style 13x wall is
#    structurally wrong in a $1,000-2,000 offer-cap market"). The committed hurdle
#    is lowered from 1.55 (ERCOT startup-cost idle-park) to 1.35 (matching
#    NYISO/CAISO's grounded start hurdle — ISO-NE CTs serve the evening ramp and
#    cold-snap reliability, per ISO-NE IMM 2023/2024 SOM). The econ ramp
#    (1.27 → 1.98) is left at the generic shape (not the ERCOT-specific artifact;
#    only the $5,000-ORDC peak and idle-park committed are).
_NEISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 1.27,
        # econ band re-anchored (2026-07-03, neiso-45/46/47 probe chain). The
        # generic 1.06->1.27 band was inherited from the ERCOT-shaped curve and
        # expresses the above-SRMC offer component as a HEAT-RATE MULTIPLIER,
        # i.e. proportional to the fuel price. The month/hour decomposition of
        # the 2024 C3b failure showed the signature that parameterization
        # forces: a flat all-hours winter over-shoot (Jan/Feb 2024 +$9-10 at
        # $3.5-7.7 AGT hub gas; model marginal implied HR ~10.5 vs the actual
        # mild-winter margin ~8.2) alongside a summer-evening under-shoot
        # (Jul/Aug 2024 -$10-11 at $1.8 gas, when the same multipliers collapse
        # the whole stack to ~$33). Physics bound: the econ band is the
        # incremental output of an already-committed CC, whose incremental heat
        # rate sits near the plant-average and rises gently toward the duct
        # margin. Level calibration (rule #1 second step — offer-curve tuning
        # AFTER the structure is right): the high-gas winter months make the
        # marginal implied HR directly observable — the actual mild-winter
        # margin ~8.2 MMBtu/MWh lands on the model's marginal winter plant
        # (Salem Harbor, base HR 7.38) at a mid-band of ~1.08x, so the ramp is
        # 1.00 -> 1.15 (the 0.95->1.05 probe, neiso-45, left the winter floor
        # low across the board: C3a 2023 -6.2%). The fuel-price-INVARIANT part
        # of the real offer component (fast-start start/no-load amortization)
        # is priced by --tranche-startup-amortization on the fast-start-capable
        # tranches, not by inflating the HR band.
        "econ_low": 1.00,
        "econ_high": 1.15,
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    # CC_CHP / ST_GAS: grounded 2026-07-06 on NEISO's OWN measured CAMPD
    # marginal heat rates (scripts/derive_campd_marginal_hr.py --iso NEISO ->
    # data/raw/reference/neiso_campd_marginal_hr_summary.csv), closing the
    # "later disciplined-calibration item" the 0c6c833 de-leak ledgered. The
    # NYISO run-32 convention: the bare measured MARGINAL heat rate is the
    # marginal COST, not the OFFER, so a competitive markup is applied on top —
    # NEISO's own CC reach ratio (CC_REGULAR econ_high band 1.15 / native CC
    # marginal econ_high 0.940 = 1.223x), never a cross-ISO value (rule #26).
    "CC_CHP": {
        # Native CC_CHP marginal (n=5 units, cap-weighted median): committed
        # 0.942 / econ_low 0.973 / econ_high 0.940 — essentially FLAT (wide
        # p25-p75, thin fleet). x1.223 reach ≈ 1.15-1.19; a thin monotone
        # spread keeps a valid rising offer (the NYISO ST_GAS convention).
        "committed": 1.15,
        "econ_low": 1.17,
        "econ_high": 1.19,
        "peak": 2.25,  # physical F-class duct-burner ratio (not ERCOT-fitted)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    # CT_CHP: stays neutral — the NEISO CAMPD sample is a SINGLE unit (n=1;
    # marginal 1.32/1.41/1.49), not identifiable as a class spread. Open item.
    "CT_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
    },
    "CT_PEAKER": {
        "committed": 1.35,  # NYISO/CAISO-grounded start hurdle (ISO-NE CTs serve
        #   evening ramp + cold-snap reliability, not ERCOT idle-park)
        # econ bands stay neutral 1.0 — now AFFIRMED by measurement, not just
        # de-leaked: NEISO's own CAMPD CT marginal HR is flat-to-FALLING with
        # load (committed 0.808 / econ_low 0.745 / econ_high 0.700, n=18), so
        # the removed ERCOT 1.27->1.98 ramp had no NEISO physical basis. The
        # real above-cost CT offer component is start/no-load amortization,
        # priced by --tranche-startup-amortization (fuel-price-invariant),
        # never an HR multiplier.
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 4.0,  # ISO-NE offer cap $1,000-2,000 (not ERCOT $5,000 ORDC)
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    "ST_GAS": {
        # Native steam marginal HR (Montville, base_HR 12.755): committed 0.642
        # / econ_low 0.692 / econ_high 0.731 — a genuinely RISING measured ramp
        # (unlike NYISO's flat 0.82-0.83). x1.223 reach markup -> 0.79/0.85/0.89.
        # Effective HR 10.1 -> 11.4 MMBtu/MWh: above CC_REGULAR econ_high
        # (7.48 x 1.15 = 8.6) and interleaved with the CT_PEAKER base (10.6) —
        # a legacy steamer's committed increment IS cheaper than a peaker's
        # energy while its upper range is dearer (merit preserved, no class
        # inversion). This prices the committed unit's daytime load-following
        # the all-1.0 bands left out of merit (the D-1 ST_GAS profile failure's
        # economic half; the commitment half is the Connecticut ST_GAS netload
        # reliability limb, reliability_floor_coeffs_NEISO.csv 2026-07-06).
        "committed": 0.79,
        "econ_low": 0.85,
        "econ_high": 0.89,
        "peak": 1.0,
        "econ_low_share": 0.500,
        "pct_peaking": 15.0,
    },
}


# MISO round-2 CC_REGULAR / COAL_BIT offer-curve rebalance (deep-merged onto the
# calibrated MISO base curve when --miso-cc-coal-rebalance is set; ISO-gated, so
# only the named bands change and every other class/band keeps its default).
# Structural correction for the conservation-of-energy miss: with imports too low
# the cheap domestic CC_REGULAR and COAL_BIT over-run and price out the
# under-running CT_PEAKER / ST_GAS. The marginal (top-tranche) MWh of a baseload
# CC/coal unit is NOT the cheapest available supply once priced imports and the
# reliability-floored gas-steam/CT are on the bar, so its committed + econ-high
# bands are raised to clear ABOVE the import hurdle (MISO seam reference ~$36;
# the all-MISO LMP sits above the neighbors most hours). An offer-SHAPE
# correction, NOT a residual-tuned adder — validated by the import↑ / CC↓ / coal↓
# / CT↑ / ST↑ response, not by MAE. Base MISO bands: CC_REGULAR committed 0.92 /
# econ_high 1.27; COAL_BIT econ_high 1.10.
_MISO_CC_COAL_REBALANCE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        # Lift the min-load committed tranche off the artificially-cheap 0.92 (a
        # CC's min-stable-load $/MWh is ~30-40% above its full-load SRMC, the
        # measured CAMPD shape) and steepen the econ ramp so the marginal CC MWh
        # clears above the priced-import hurdle and the gas-steam/CT it displaces.
        "committed": 1.00,
        "econ_high": 1.42,
    },
    "COAL_BIT": {
        # Raise the bituminous-coal econ-high so the marginal coal-bit MWh is no
        # longer the cheapest top-of-merit fill (2025 coal 232 vs EIA-923 201 TWh).
        "econ_high": 1.22,
    },
}


def backcast_config(
    year: int,
    iso: str,
    hours: int,
    gas_price: float,
    coal_passthrough: float | None = None,
    commitment_enabled: bool = False,
    commitment_screen_coal: bool = True,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    retiree_cems_cap: bool = False,
    ct_mustrun_per_plant: bool = False,
    ct_mustrun_floor_frac: float = 1.0,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
):
    """Build the ScenarioConfig for one calibration year.

    The calibration configuration fixes the structural and policy levers to
    their backcast values: the weather year is the calibration year, the
    EIA-860 vintage capacity ramp is on, the EIA-930 generation-side demand
    is used without a T&D gross-up, gas seasonality is on, and the RPS
    constraint is off. The federal carbon price is zero, which lets the
    state carbon program through: CAISO years charge the measured CARB
    cap-and-trade allowance price, and NYISO/NEISO years the measured RGGI
    auction clearing average (see policy.carbon.state_carbon_price); other
    ISOs see no carbon cost.

    The measured Henry Hub price is applied through ``gas_price_override``
    when that field exists on :class:`ScenarioConfig`; otherwise the run
    falls back to the configured ``gas_price_path`` trajectory.

    Args:
        year: Calibration year.
        iso: ISO identifier.
        hours: Dispatch horizon in hours.
        gas_price: Measured Henry Hub annual price ($/MMBtu).

    Returns:
        The calibration :class:`ScenarioConfig`.
    """
    config = ScenarioConfig(
        weather_year=year,
        iso=iso,
        mode="backcast",  # explicit mode signal: historical-actuals
        #   renewable capacity and measured hourly profiles. Never inferred
        #   from gas_price_override.
        hours=hours,
        vintage_capacity_ramp=True,
        td_loss_factor=0.0,  # EIA-930 demand is generation-side
        #   (Demand + Interchange = Net Generation); no gross-up so the grid
        #   demand target equals actual grid net generation and BTM CHP
        #   self-supply stays off-grid. See ScenarioConfig.td_loss_factor.
        gas_seasonality=True,
        carbon_price=0.0,  # no *federal* carbon price in the backcast years;
        #   carbon_price=0 falls through to the state carbon program in
        #   resolve_carbon_price, so CAISO charges the measured CARB
        #   cap-and-trade allowance price and NYISO/NEISO the measured RGGI
        #   auction clearing average (2023-25) on in-state fossil MC.
        #   ERCOT/PJM have no state program and stay at 0.
        rps_enabled=False,
        gas_monthly_actuals=(iso.upper() in ("CAISO", "NYISO", "NEISO")),
        # NYISO prices gas off different pipeline hubs by region (cheap Tenn Z4
        # 200L / Niagara upstate, dearer Iroquois Z2 / Tenn Z6 in the east,
        # Transco Z6 NY in the city), so the east marginal gas is persistently
        # dearer than the west — the structural source of the upstate-cheap /
        # east-dear LMP gradient the ISO-month average flattens. Measured from
        # the NYISO State-of-the-Market reports (data/raw/
        # nyiso_zonal_gas_hub.csv); see fuel.apply_nyiso_zonal_gas_basis.
        nyiso_zonal_gas_basis=(iso.upper() == "NYISO"),
        # ERCOT prices gas off structurally different regional hubs by zone
        # (deeply-discounted Waha in the West/Permian, ~Henry-Hub North/East
        # Texas and Houston Ship Channel, a South-Texas premium), so the flat
        # fleet-wide Waha scalar over-runs DFW/North CCs and under-runs
        # West/Permian and South CCs. Measured per-zone basis from EIA-923
        # Schedule-5 receipts + published Waha/HSC annual averages
        # (data/raw/ercot_zonal_gas_hub.csv), mean-zero anchored so the
        # aggregate gas level is unchanged. DEFAULT-OFF DIAGNOSTIC: enabling it
        # confirms the gas-basis mechanism (shrinks the North CC over-run) but
        # relocates the residual onto West/Permian CT peakers the zonal LP can't
        # trap (see the docstring on ScenarioConfig.ercot_zonal_gas_basis), so
        # it is kept off in the keeper. Gated on the ERCOT_ZONAL_GAS env flag.
        # See market_sim.data.fuel.apply_ercot_zonal_gas_basis.
        ercot_zonal_gas_basis=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_ZONAL_GAS", "").lower() in ("1", "true", "on")
        ),
        # Delivered-gas floor on the zonal basis above: the West/Panhandle Waha
        # basis is a *hub* (wellhead) basis that goes deeply negative, but a power
        # plant pays *delivered* gas (transport + commodity on top) so its discount
        # has a transport-grounded floor. Without it the West/Permian gas units
        # offer ~$0/MWh and run baseload (the CT_PEAKER over-run); the measured TX
        # delivered-to-electric-power level ($2.11/MMBtu, 2024) shows no TX plant
        # paid near $0 delivered. ERCOT_GAS_FLOOR=1 floors the per-zone delivered
        # discount at the cited measured Waha delivered basis (-0.50);
        # ERCOT_GAS_FLOOR_BASIS=<float> overrides the floor depth. ERCOT only, and
        # only meaningful with ERCOT_ZONAL_GAS on. See
        # market_sim.data.fuel.apply_ercot_zonal_gas_basis.
        ercot_gas_delivered_floor_basis=(
            (
                float(os.environ["ERCOT_GAS_FLOOR_BASIS"])
                if os.environ.get("ERCOT_GAS_FLOOR_BASIS")
                else GAS_BASIS_DIFFERENTIAL.get("ERCOT", -0.50)
            )
            if (
                iso.upper() == "ERCOT"
                and (
                    os.environ.get("ERCOT_GAS_FLOOR", "").lower() in ("1", "true", "on")
                    or os.environ.get("ERCOT_GAS_FLOOR_BASIS")
                )
            )
            else None
        ),
        # Measured re-grounding of the floor depth: scale each zone's Waha hub
        # basis by its EIA-923-measured gas SPOT share (only the spot fraction
        # sees the hub collapse; firm-contracted gas is insulated), so the West
        # delivered discount is a measured haircut, not the cited -0.50 scalar.
        # ERCOT_GAS_HAIRCUT=1 enables it; no-op unless the receipt-derived share
        # (scripts/derive_gas_takeorpay.py) is on disk. ERCOT only. See
        # market_sim.data.fuel.apply_ercot_zonal_gas_basis.
        ercot_gas_contract_haircut=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_GAS_HAIRCUT", "").lower() in ("1", "true", "on")
        ),
        # MEASURED per-unit fuel correction: EIA-860 Petroleum-Liquids (DFO)
        # combustion-turbine peakers (e.g. Morgan Creek 3492) sit in the gas
        # CT_PEAKER class on the bin sheet and otherwise burn cheap Waha gas at
        # baseload. ERCOT_OIL_PRIMARY=1 reprices their gas_ct tranches on
        # distillate (OIL_PRICE_PER_MMBTU), keeping their CT_PEAKER group — a
        # structural data-correctness fix from the EIA-860 energy source, not a
        # residual adder. See market_sim.data.fleet.oil_primary_bin_plants.
        oil_primary_bin_fuel=(
            os.environ.get("ERCOT_OIL_PRIMARY", "").lower() in ("1", "true", "on")
        ),
        # STRUCTURAL net-load-indexed West/Panhandle Waha gas basis: the Waha hub
        # collapses negative at low demand and firms at high demand, so the basis
        # is indexed to system net-load (load - wind - solar) instead of a flat
        # annual scalar. A West peaker (burns only in high-net-load scarcity
        # hours) then sees firm Waha and idles; a West CC (burns all hours) sees
        # the blended-cheap annual mean and stays baseload — the peaker/CC split
        # falls out of WHEN each runs, not a chosen floor. Mean-zero so the
        # measured annual Waha basis is preserved. ERCOT_WEST_NETLOAD_GAS=1 enables
        # it (no-op unless ERCOT_ZONAL_GAS is also on, ERCOT only);
        # ERCOT_WEST_GAS_FIRM_BASIS=<float> overrides the firm (high-demand) Waha
        # delivered basis the top net-load hours reach (default the cited normal
        # Waha discount). See market_sim.data.fuel.apply_ercot_west_netload_gas_shape.
        ercot_west_netload_gas_shape=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_WEST_NETLOAD_GAS", "").lower()
            in ("1", "true", "on")
        ),
        ercot_west_gas_firm_basis=(
            float(os.environ["ERCOT_WEST_GAS_FIRM_BASIS"])
            if os.environ.get("ERCOT_WEST_GAS_FIRM_BASIS")
            else None
        ),
        # Diagnostic override of the measured Waha negative-day frequency that
        # splits the two-regime step (default: per-year neg_day_freq from the
        # zonal-gas CSV). Probe-only — never set to chase the CT residual.
        ercot_west_gas_collapse_freq=(
            float(os.environ["ERCOT_WEST_GAS_COLLAPSE_FREQ"])
            if os.environ.get("ERCOT_WEST_GAS_COLLAPSE_FREQ")
            else None
        ),
        # ENDOGENOUS collapse frequency (gap G6): derive the two-regime split from
        # forecast West/Panhandle oversupply (VRE > local load + export TTC)
        # instead of the measured neg_day_freq, closing the last measured input of
        # the West net-load gas shape. ERCOT_WEST_ENDOGENOUS_COLLAPSE=1 enables it
        # (no-op unless ERCOT_WEST_NETLOAD_GAS is also on, ERCOT only); the
        # measured neg_day_freq stays logged as the backcast realization to
        # validate against. See fuel.ercot_west_oversupply_collapse_freq.
        ercot_west_gas_endogenous_collapse=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_WEST_ENDOGENOUS_COLLAPSE", "").lower()
            in ("1", "true", "on")
        ),
        # Burner-tip delivered floor for the collapse regime (kills the cheap-hour
        # magnet that pulls low-HR West CTs into low-demand hours). Physical
        # transport-bound input; default off keeps the generic gas floor.
        ercot_west_gas_delivered_floor=(
            float(os.environ["ERCOT_WEST_GAS_DELIVERED_FLOOR"])
            if os.environ.get("ERCOT_WEST_GAS_DELIVERED_FLOOR")
            else None
        ),
        # Daily Henry Hub within-month shape on top of the measured monthly
        # level: physics-input correctness (the merit order sees the real
        # day-to-day gas swing), mean-preserving so the annual mix is
        # unchanged. On wherever the monthly-actuals level is.
        gas_daily_shape=(iso.upper() in ("CAISO", "NYISO", "NEISO")),
        #   Default-on: the +1.20 SoCal basis seed misses the measured
        #   delivered-gas reality badly in stressed years (EIA-923 implied
        #   basis +7.06 in 2023 — Jan-23 delivered $38.7/MMBtu — +2.26 in
        #   2024, +1.12 in 2025), so CAISO backcasts price gas at the
        #   measured ISO-month series. NYISO is the same story (P7): the
        #   flat +0.55 basis seed misses the Transco Z6 winter blowout the
        #   measured 923 series carries (Jan-2023 delivered $10.02/MMBtu vs
        #   HH $3.27; Dec-2025 $8.20), so NYISO backcasts price gas at the
        #   measured ISO-month series too. NEISO default-on for the same
        #   reason (the +1.10 seed is a normal-year scalar), though its
        #   ISO-month 923 series rests on two reporting plants — the AGT hub
        #   overlay below supersedes it in covered months. PJM keeps the
        #   --gas-monthly-actuals flag (its keeper runs pass it explicitly);
        #   ERCOT stays on annual + shape (E1).
        gas_hub_basis_overlay=(iso.upper() in ("NEISO", "CAISO")),
        #   Doc-08 NEISO design decision 1: the marginal gas unit prices off
        #   its constrained trading hub's spot (the opportunity cost of gas in
        #   hand is the spot price it could be resold at), NOT the contract-
        #   laden plant-average EIA-923 delivered cost. The overlay replaces
        #   the gas price with HH-month + the measured hub basis in covered
        #   months (data/raw/gas_basis_by_iso_month.csv).
        #     - NEISO: Algonquin Citygate, whose Dec-Feb basis blows out to
        #       +$4-13/MMBtu (measured ISO-NE MA gas index 2023-2025) — THE
        #       ISO-NE winter price driver and the dual-fuel switch trigger (P13).
        #     - CAISO (caiso 38): the SoCal / PG&E Citygate (EIA N3050CA3
        #       citygate - Henry Hub). The default ISO-month EIA-923 series for
        #       CAISO is volume-weighted across only ~7 reporting plants
        #       (Gateway/Colusa/Lodi PG&E + SDGE Palomar — NorCal/SDGE-skewed),
        #       running ~$0.6/MMBtu above the full-census CA electric-power
        #       delivered gas (EIA N3045CA3 2024 = $3.98/Mcf = $3.84/MMBtu) and
        #       missing the cheap SoCal-border gas the SP15-dominated marginal
        #       CC actually burns (SoCal border fell to a discount to Henry Hub
        #       in summer 2024). The citygate overlay is the measured CA trading
        #       hub the marginal CC prices off — captures both the Jan-2023
        #       western gas crisis (+$24/MMBtu basis) and the summer-2024 SoCal
        #       discount — and supersedes the skewed 7-plant sample (rule #11:
        #       prefer accurate measured data; reconcile a misaligned sample to
        #       the representative hub). NYISO's Transco Z6 leg is still
        #       unsourced, so it keeps the ISO-month 923 series.
        gas_hub_basis_daily=False,
        #   Daily resolution for the AGT overlay (opt in with
        #   --gas-hub-basis-daily). It replaces the flat monthly hub price with a
        #   MEASURED daily series — measured Henry Hub daily + measured Algonquin
        #   Citygate daily spot prints (EIA Weekly Update), Transco Z6 NY daily
        #   basis as the sparse-print shape fallback — MEAN-PRESERVING to the
        #   measured monthly basis, so the annual gas burn and fuel mix are
        #   unchanged and only the within-month winter shape is added. (The old
        #   demand^AGT_DAILY_BASIS_CONVEXITY exponent, which WAS fitted to the oil
        #   burn, was RETIRED 2026-06; the daily leg is now all measured gas-market
        #   data — forward-reproducible and condition-responsive, CLAUDE.md #10.)
        #   The cold-day spikes it builds trip the physical dual-fuel gas->oil
        #   switch, so it is what restores the measured ~1.5 TWh winter oil burn
        #   (and trims the gas the flat monthly overlay leaves over-counted); the
        #   NEISO keepers run it (neiso-33 onward). See
        #   market_sim.data.fuel.iso_hub_daily_gas_prices and
        #   docs/multi-iso/neiso-data-audit.md.
        commitment_enabled=commitment_enabled,  # P1-only by default: the
        #   3-tranche, no-Pmin bin structure dispatches correctly without the
        #   P2 screen. Opt in with --commitment to add the unit-commitment pass.
        commitment_screen_coal=commitment_screen_coal,
        wefor_multiplier=(1.0 if iso.upper() == "MISO" else 0.7),
        #   MISO: neutralised to 1.0 (miso-44) — residual-identified DOF (audit
        #   C-15) with no measured physical basis; the miso-42 ablation twin
        #   showed the 0.7 haircut was the driver of the base-vs-twin score delta
        #   (not the reliability floors, which force <0.6 TWh total). Other ISOs:
        #   0.7 retained pending their own root-cause investigations.
        coal_prb_passthrough=coal_prb_passthrough,  # default 1.0 = OFF (it is
        #   gas-price fragile; coal level set by the must-run floor). Set via
        #   --coal-prb-passthrough to re-test the price-taking discount.
        coal_lignite_mustrun_override=coal_lignite_mustrun,
        coal_prb_mustrun_override=coal_prb_mustrun,
        outage_source=outage_source,  # backcast pins actual coal/CC outages;
        #   "statistical" reverts to the WEFOR/POF availability model.
        caiso_gas_commitment_floor=False,  # Step-1 overhaul: DEFAULT OFF. The
        #   measured-NG:NG midday slab pinned the gas fleet to 0.80 x its measured
        #   EIA-930 output (a measured-OUTCOME overlay, None for forecast years) —
        #   it held CC_REGULAR ~2x above the real midday duck-belly and
        #   manufactured the $0 midday price by forcing gas LONG, failing CLAUDE.md
        #   #1/#11 (docs/caiso-lever-audit-2026-06.md, Lever A). Replaced by the
        #   forward-derivable RA must-offer COMMITMENT below (caiso_ra_mustoffer):
        #   units online at min-load, free to dispatch down to it. The inject fn
        #   is kept (transmission.inject_caiso_gas_commitment_floor) and re-armable
        #   via --caiso-gas-commitment-floor for the baseline A/B. Other ISOs were
        #   already off (byte-identical).
        caiso_gas_floor_frac=(0.80 if iso.upper() == "CAISO" else 1.0),  # 0.80 =
        #   EIA-923 gas / EIA-930 NG: NG, stripping the ~21% geo+bio the CISO
        #   NG: NG silently absorbs (CISO reports neither) — targets the true
        #   must-offer gas without padding the mix. Only used when the (now
        #   default-off) caiso_gas_commitment_floor is re-armed.
        caiso_ra_mustoffer=(iso.upper() == "CAISO"),  # CAISO Step-1 default-ON:
        #   the forward-derivable RA must-offer COMMITMENT replacing the measured
        #   gas slab above. Through the P2 pass it holds each merchant gas CC/CT
        #   unit that the economic P1 dispatch runs before AND after a midday idle
        #   gap shorter than its physical min-down time at min-load across the gap
        #   (it cannot cycle off and restart for the evening ramp). Detected from
        #   the model's own run pattern + min-down (model.commitment.
        #   caiso_ra_mustoffer_min_gen) — no measured-outcome pin. The LP
        #   dispatches economically above it, so it only binds when oversupply
        #   would drive a committed unit cold; the midday ~$0 must come from real
        #   oversupply (Lever D), not the floor. Other ISOs stay off (byte-
        #   identical). Toggle with --no-caiso-ra-mustoffer.
        caiso_ra_min_load_frac=0.26,  # min stable load of a committed gas unit
        #   (fraction of available capacity) for the RA bridge above. Grounded in
        #   the CAMPD/CEMS-measured CAISO combined-cycle minimum stable load
        #   (P5 of net CF over online hours, scripts/derive_thermal_tranches.py;
        #   data/raw/_processed-legacy/thermal_tranches_CAISO.csv committed_pct):
        #   capacity-weighted 0.259 over the 23-plant, 12.7 GW CA CC fleet
        #   (range 0.10-0.63, median 0.25). Supersedes the generic 0.40 NREL/
        #   Master-File textbook turn-down (~14pp too high for this fleet) per
        #   CLAUDE.md #11 — a measured, forward-reproducible physical limit that
        #   responds to fleet composition, NOT a price/volume fit. The flat
        #   fraction multiplies each tranche row's pmax, so it sums to ~0.26 of
        #   plant pmax across a plant's tranches.
        reliability_floor=(
            iso.upper() in ("ERCOT", "CAISO", "NYISO", "NEISO", "MISO")
        ),  # Registry-driven temperature/net-load reliability floor: ON for the
        #   five calibrated ISOs. Every enabled (zone, class, driver) limb in
        #   RELIABILITY_FLOOR_REGISTRY[iso] (seeded from the derived
        #   reliability_floor_coeffs_<ISO>.csv) is applied by the single engine.
        #   The registry is empty until Phase 2 fills the coefficient CSVs, so
        #   this is a no-op today; per-limb tuning is via
        #   reliability_floor_overrides. New ISOs need ONLY this flag + a registry
        #   row + a weather file.
        neiso_oil_burn_budget=(iso.upper() == "NEISO"),  # NEISO keeper
        #   default-ON: inventory-limited oil-burn monthly budget. Oil/dual-fuel
        #   peakers ration limited on-site distillate over multi-day cold snaps;
        #   the LP shadow price when the budget binds IS the scarcity rent that
        #   lifts the cleared LMP above the flat dual-fuel oil-parity cap (~$258)
        #   and produces >$300 hours endogenously. Budget from measured EIA-923
        #   Schedule 5 monthly Petroleum receipts (MMBtu -> MWh); a reproducible
        #   physical deliverability input (CLAUDE.md #10). NEISO-only, no-op for
        #   other ISOs (byte-identical).
        ercot_wtx_curtailment_driver=(iso.upper() == "ERCOT"),  # ERCOT keeper
        #   default-ON (owner GO 2026-07-07, ercot42 promotion): the WP-B West
        #   Texas Export corridor VRE curtailment-share driver — a per-(zone,
        #   hour) ceiling on West/Panhandle wind & solar, SHAPE = measured
        #   NP6-86 SCED West-corridor binding frequency by net-load decile x
        #   hour x season (data.curtailment_share), LEVEL = the per-tech depth
        #   pair. Structural stand-in for the sub-zonal Permian/CREZ nodal
        #   congestion the 8-zone reduction cannot resolve (docs/handoffs/
        #   ercot-vre-curtailment-wpb-driver-2026-07.md). Tri-state at the
        #   orchestrator seam: explicit False scrubs it (ablation arms);
        #   pre-driver bundle replays are backstopped to False in
        #   replay_keeper.build_kwargs. Non-ERCOT ISOs default off (rule 25).
        ct_netload_drag=(iso.upper() == "CAISO"),  # CAISO keeper default-ON: the
        #   forward-native CT_PEAKER reliability-drag floor that REPLACES the flat
        #   TMAX floor above (audit Lever B). Same mechanism validated on ERCOT —
        #   a min-gen floor clip(slope*netGW + intercept, 0, cap) x available
        #   CT_PEAKER capacity gated to the afternoon-evening ramp window — but
        #   keyed to system NET-LOAD (load - wind - solar) instead of TMAX, so it
        #   RISES with the duck-curve neck and naturally PEAKS in the evening ramp
        #   (h18-21) rather than holding a flat rectangle. Both the trigger
        #   (net-load) and the magnitude (physical min-gen) are forward-derivable
        #   and condition-responsive, admissible in backcast AND forecast (#10/#11)
        #   — explicitly NOT the measured-actuals ct_mustrun_per_plant crutch. See
        #   fleet.apply_ct_netload_drag_floor. Other ISOs use the CLI flag.
        #   CAISO-specific curve coefficients (do NOT reuse ERCOT's 0.00703 /
        #   -0.1427 / 0.47): regressed from measured CAMPD CT_PEAKER evening
        #   (h15-22 local-std) capacity factor on EIA-930 CISO net-load, 2023-2025
        #   (scripts/derive_caiso_ct_reliability_floor.py). Non-CAISO ISOs fall
        #   back to the ScenarioConfig ERCOT defaults (byte-identical).
        ct_drag_slope_per_gw=(0.00901 if iso.upper() == "CAISO" else 0.00703),
        ct_drag_intercept=(-0.1124 if iso.upper() == "CAISO" else -0.1427),
        ct_drag_cap=(0.36 if iso.upper() == "CAISO" else 0.47),
        negative_renewable_offers=(iso.upper() == "CAISO"),  # CAISO keeper
        #   default-ON: CA solar/wind bid below $0 (RPS/REC/PTC keep-running
        #   value) in oversupply, so the curtailable renewable tier sets a sub-$0
        #   marginal price once the model is long past the $0 export sink — the
        #   negative midday tail. Byte-identical when not binding (current floor
        #   frac reaches $0, not yet negative; bites with export shaping / a
        #   higher floor). See policy.eac.apply_negative_renewable_offer_floor
        #   and results/calibration/NEGRENEW-caiso-findings.md.
        caiso_solar_deliverability=(iso.upper() == "CAISO"),  # CAISO Lever-D
        #   default-ON: re-curtail the uncurtailed HSL solar potential for the
        #   local / sub-area congestion the reduced 3-zone topology can't see
        #   (~70% of real CAISO curtailment). Caps the per-zone solar CF upper
        #   bound at clip(1 − k × solar_frac, floor, 1) — the solar analogue of
        #   the accepted WECC corridor ATC derate, driven by the FORWARD solar-
        #   penetration signal so the curtailed VOLUME emerges per-year from that
        #   year's own build, not a pin to actuals (CLAUDE.md #1/#11). See
        #   transmission.caiso_solar_deliverability_derate and docs/caiso-lever-
        #   audit-2026-06.md (Lever D). Other ISOs stay off (byte-identical);
        #   --no-caiso-solar-deliverability forces it off (the over-run baseline).
        caiso_solar_endogenous_spill=(iso.upper() == "CAISO"),  # CAISO midday
        #   price fix: skip the pre-LP solar CF derate and pass the full solar
        #   potential to the LP. The LP endogenously curtails in oversupply hours
        #   (solar not fully dispatched → solar marginal → dual = solar_mc ≈ $0
        #   or negative via the keep-running value). Overrides the pre-LP CF
        #   derate from caiso_solar_deliverability while leaving the flag on for
        #   the derate profile computation (used in diagnostics/logging).
        storage_vintage_ramp=(iso.upper() in ("CAISO", "ERCOT", "NEISO")),  # CAISO,
        #   ERCOT and NEISO commissioned batteries mid-backcast (CAISO 3.0 GW
        #   in 2023 + 3.6 GW in 2024; ERCOT ramped ~3.5 -> 6.5 -> 10 GW across
        #   2023-25; NEISO's grid-battery fleet stepped up across 2023-25 as its
        #   EIA-860 COD months landed), so a flat year-end fleet overstates
        #   spring/summer battery capability — measured ERCOT model power
        #   3.9/8.1/13.7 GW vs reality ~3.5/6.5/10. The dispatch caps now ramp
        #   month-by-month from each unit's COD (EIA-860 Operating Month/Year),
        #   and out again on its Planned Retirement Month, for all three. PJM
        #   stays flat until its own recalibration pass. The --storage-vintage-
        #   ramp CLI flag can force it on for any other ISO.
        nearby_fuel_price_fallback=(iso.upper() != "ERCOT"),  # merchant-heavy
        #   ISOs (PJM) have many plants that file no EIA-923 delivered cost;
        #   fill those months from state/zone neighbours before the Henry Hub
        #   curve. Off for ERCOT, whose plants overwhelmingly report.
        plant_level_fleet=(iso.upper() != "ERCOT"),  # non-ERCOT ISOs run the
        #   per-plant EIA-860 fleet (no efficiency-bin aggregation) so the
        #   per-plant fuel cost and CAMPD outage overlay bind to real plants.
        #   ERCOT builds its fleet from CAMPD bins, so this path is unused.
        coal_plant_monthly_pricing=True,  # plant-specific EIA-923 monthly coal
        #   cost where reported (Fayette/San Miguel/J K Spruce); the rest fall
        #   back to the flat lignite/PRB average.
        coal_takeorpay_from_data=(iso.upper() == "MISO"),  # MISO is split-fleet
        #   (not in CAMPD_BINNING_ISOS), so its coal take-or-pay depth comes from
        #   split_coal_tranches, not offer_curve_by_group. Replace the uniform
        #   assumed 100%-sunk first tranche with each plant's MEASURED EIA-923
        #   Schedule-5 contracted share (coal_takeorpay_MISO.csv; CLAUDE.md
        #   #11/#12 — measured > estimate, forward-reproducible). The measured
        #   data shows MISO coal is ~97% contract (tonnage-wtd) — MORE take-or-
        #   pay than ERCOT (~71%), refuting the "market-bought, less depth"
        #   premise: the deep sunk tranche is correct for MISO, so coal offers
        #   are not the LMP/seam lever. Only the few spot-heavy plants (e.g.
        #   1167 S:100%, 6213 S:47%) bid their first tranche fuller. ERCOT and
        #   the CAMPD-binned ISOs are untouched (flag off).
        coal_prb_passthrough_sigmoid=coal_prb_passthrough_sigmoid,  # gas-keyed
        #   PRB passthrough when set; else the flat coal_prb_passthrough.
        coal_mustrun_per_plant=coal_mustrun_per_plant,  # per-plant CAMPD coal
        #   must-run floors when set; else the uniform lignite/PRB overrides.
        retiree_cems_cap=retiree_cems_cap,  # cap within-window retirees to their
        #   measured monthly CAMPD CEMS envelope (backcast) when set.
        ct_mustrun_per_plant=ct_mustrun_per_plant,  # per-plant EIA-923 CT_PEAKER
        #   reliability must-run floor (WEFOR/POF exempt) when set.
        ct_mustrun_floor_frac=ct_mustrun_floor_frac,
        coal_drop_pof=coal_drop_pof,  # drop statistical POF on coal (planned
        #   maintenance now comes from the historic outage overlay).
        coal_prb_passthrough_tiered=coal_prb_passthrough_tiered,  # separate
        #   follower-tier PRB sigmoid for low-must-run load-followers.
        gas_st_startup_spread=True,  # amortize ST_GAS startup over the whole
        #   May-Sep season (one seasonal start), not per calendar month.
        # CC and ST_GAS supply curves now come from the unified offer curve
        # below (offer_curve_by_group), so their legacy override triples are
        # left unset. CT_CHP keeps its legacy override (not in the offer curve).
        cc_committed_per_plant=True,  # ground each CC_REGULAR committed % in
        #   CAMPD-observed minimum stable load (fleet.CC_REGULAR_COMMITTED_PCT_
        #   BY_PLANT) instead of the coarse assumed CSV Pct_Committed.
        cc_peaking_per_plant=(iso.upper() != "ERCOT"),  # per-plant CAMPD-
        #   derived duct-firing/scarcity share (fleet.thermal_tranche_peaking)
        #   for CAISO/PJM/NYISO/NEISO/MISO — restores the pre-2026-07 default
        #   these keepers actually solved with (a bug introduced and then
        #   caught in the same G-26/C-12 sweep: an earlier pass at this file
        #   flipped this to an unconditional False, which would have silently
        #   dropped every non-ERCOT ISO's measured CAMPD peaking mechanism on
        #   the next default-config run). ERCOT has no thermal-tranche
        #   artifact (no CAMPD-native per-plant peaking-tranche derive exists
        #   for its own binning path), so this is a no-op there regardless;
        #   set False explicitly for clarity now that cc_duct_peaking below
        #   is ERCOT's real default mechanism.
        cc_duct_peaking=True,  # per-plant EIA-860 duct-burner peaking shares
        #   for CC_REGULAR/CC_CHP, every ISO (2026-07, G-26/C-12): duct-fired
        #   plants get their nameplate-vs-summer capability gap as the peak
        #   band, non-duct plants get 0 — replacing the class-uniform
        #   pct_peaking that hands every CC the same phantom duct band
        #   (fleet.cc_duct_peaking_pct; PJM: 65 of 84 CCs duct-fired, ~50 GW).
        #   The underlying EIA-860 query is national/ISO-agnostic (no ISO
        #   filter in cc_duct_peaking_pct itself) — was PJM/ERCOT-only,
        #   generalized to CAISO/NYISO/NEISO/MISO going forward: measured
        #   physical data (EIA-860 nameplate/summer-capacity/duct-burner-flag)
        #   beats the CAMPD statistical proxy (thermal_tranche_peaking) or
        #   the deleted ERCOT four-plant hardcode wherever it has coverage
        #   (rule 12 — prefer accurate/measured data). For CAISO/NYISO/NEISO/
        #   MISO this coexists with cc_peaking_per_plant=True (the PJM
        #   pattern, already keeper-validated there): EIA-860 wins per plant
        #   wherever it has data (incl. an explicit 0 for a non-duct CC,
        #   correctly zeroing a phantom CAMPD-derived peak band), and the
        #   CAMPD thermal-tranche artifact (fleet.thermal_tranche_peaking)
        #   stays the fallback for any plant EIA-860 doesn't cover. Applies
        #   to NEW runs going forward only — no existing keeper's frozen
        #   run_config.json changes; each new run records which mechanism(s)
        #   fired via its own cc_duct_peaking/cc_peaking_per_plant fields
        #   (rule 20 — no off-registry channel, always visible in
        #   run_config.json and the DOF ledger).
        cc_duct_peaking_cap_pct=(8.0 if iso.upper() == "PJM" else None),  # cap
        #   the per-plant duct band at the F-class supplementary-firing physical
        #   max. The raw nameplate-vs-net-summer gap folds the ambient summer
        #   derate into the duct band (median 6.6%, but up to 28% for high-derate
        #   plants), oversizing it and dropping the price wall to ~76% of
        #   nameplate (Guernsey 13% gap). Capping at 8% keeps the per-plant duct
        #   flag (non-duct CCs still 0) but positions the wall at the real ~92%
        #   duct-firing point. ERCOT uses a flat class pct_peaking (no cap).
        cc_nameplate_summer_derate=(
            iso.upper() in ("PJM", "NYISO", "NEISO", "CAISO")
        ),  # CC_REGULAR/CC_CHP carry full EIA-860 nameplate in the LP and are
        #   derated to the measured net-summer rating in summer only (the correct
        #   seasonal shape: full cold-weather capability in winter, ambient-
        #   derated in summer). Replaces pinning the LP capacity at net-summer
        #   year-round (which under-modelled winter AND, with the flat 10%
        #   _SUMMER_CLASS_DERATE on top, derated summer twice) with the per-plant
        #   measured derate (fleet.cc_summer_capacity). In backcast the
        #   statistical WEFOR/POF/age derate are also dropped for CC — the CAMPD
        #   overlay already supplies the real outages. The duct-firing peak band
        #   then sits at the top of nameplate (its physical location) instead of
        #   inside a net-summer-capped range. ERCOT (CAMPD-bin nameplate) and
        #   CAISO/MISO/SPP keep their prior behaviour. Wired for the winter-
        #   fidelity CC ISOs (PJM first; NYISO/NEISO share the per-plant path).
        ct_committed_hr_override=1.1,  # CT_CHP supply curve above its must-run
        ct_econ_hr_override=1.2,  # BTM + steam-following floor; raised in
        ct_peak_hr_override=1.4,  # run9 (CT_CHP was running too much). NOTE:
        #   these are INERT for CT_CHP now — its offer is the offer_curve_by_group
        #   ["CT_CHP"] curve below (the CAISO EOR power-only-HR multipliers).
        # Unified thermal offer curve (operator-supplied band multipliers on
        # AHR x fuel_price; VOM constant across bands). The economic block is a
        # rising ramp from econ_low to econ_high (its slope set by those two
        # endpoints); the duct-firing peak is a separate band above it. CC peak
        # is a tweakable "peak" key (2.25 = the F-class duct-burner multiplier,
        # the modal CC class) instead of the per-turbine-class default, so it
        # can be tuned like every other group's peak. Gas Steam committed kept
        # at the current 0.65x reliability
        # value (per operator); CC and Coal keep their CSV peaking %, while
        # Gas CT -> 7% and Gas Steam -> 15%.
        offer_curve_by_group={
            # CC offer curve fit to Colorado Bend II / Wolf Hollow II observed
            # CAMPD heat-rate curves: marginal HR ~0.95x avg and flat across
            # the operating range, negligible duct-firing. committed/econ are a
            # flat cheap band; peak 2.25 = F-class duct-burner mult (tweakable);
            # pct_peaking 8% = observed duct-fire headroom. committed % per-plant
            # grounded (cc_committed_per_plant).
            # PJM CC econ raised moderately (econ_low 1.06->1.20, econ_high
            # 1.27->1.49) to trim a residual CC_REGULAR overrun. The bulk of
            # the gas-level correction is done by the EIA-923-derived gas basis
            # (+0.67, constants.GAS_BASIS_DIFFERENTIAL) + per-plant gas pricing,
            # not the offer curve; this only rebalances the CC-vs-CT split that
            # economic dispatch (no commitment) leaves CC-heavy. ERCOT keeps the
            # fitted values.
            # ERCOT econ bands fold in the run57 baseline (econ_low 1.06->1.16,
            # econ_high 1.27->1.41) so a no-tweak ERCOT run reproduces run57 and
            # workflow tweaks are +/- relative to it. PJM / other ISOs unchanged.
            "CC_REGULAR": {
                # Generic CC_REGULAR min-stable-load committed band. NEISO's
                # ISO-specific committed lift (1.27, anchored to its measured
                # CAMPD CC heat-rate shape — min-load ~1.30x the fleet-average HR,
                # removing the artificially-cheap min-load block the removed
                # net-summer CC "wall" was masking) now lives in _NEISO_OFFER_CURVE
                # and is deep-merged on top below, so this stays the generic 0.92.
                "committed": 0.92,
                "econ_low": 1.20
                if iso == "PJM"
                else (1.16 if iso == "ERCOT" else 1.06),
                "econ_high": 1.49
                if iso == "PJM"
                else (1.41 if iso == "ERCOT" else 1.27),
                "peak": 2.25,
                "econ_low_share": 0.50,
                "pct_peaking": 8.0,
            },
            # Flatter curve for the measured baseload-duty MISO CC cohort
            # (fleet.cc_intermediate_plants, median CF >= threshold), routed here
            # only when cc_intermediate_split is set (--cc-intermediate-split;
            # default OFF, so every prior keeper / other ISO is byte-identical and
            # the CC_REGULAR curve above is untouched). MISO's entire CC fleet runs
            # intermediate/baseload (median CF 50-150%, mean ~90%), but the
            # CC_REGULAR curve was fit to ERCOT's duct-fire-heavy 2x1 peaker CCs:
            # its rising start-cost-amortized econ ramp (econ_high 1.27) over-prices
            # the upper operating range of an already-committed baseload CC, whose
            # incremental energy is near its flat full-load heat rate (~0.93x its
            # own average, the documented CC measured shape), so the upper econ
            # tranches sit above the clearing price and the model under-runs the CC
            # fleet (the 2023/2024 gas-CC under-run, -24 to -28 TWh vs EIA-923).
            # This flattens the econ ramp to that measured near-baseload
            # incremental cost (econ 0.95->1.08, straddling the full-load 0.93x and
            # average 1.0x) while KEEPING the physically-real F-class duct-burner
            # peak (2.25) — only the operating-range ramp is corrected, never the
            # duct-fire peak (which would be an unphysical fit to volume; rule #11).
            # The committed band stays 0.92 (the cheap min-stable-load base) and
            # the peaking band stays per-plant via cc_peaking_per_plant. Mirrors
            # ST_GAS_INTERMEDIATE / CT_INTERMEDIATE.
            "CC_INTERMEDIATE": {
                "committed": 0.92,
                "econ_low": 0.95,
                "econ_high": 1.08,
                "peak": 2.25,
                "econ_low_share": 0.50,
                "pct_peaking": 8.0,
            },
            "CC_CHP": {
                "committed": 0.92,
                "econ_low": 0.95 if iso == "PJM" else 0.96,
                "econ_high": 1.14 if iso == "PJM" else 1.12,
                "peak": 2.25,
                "econ_low_share": 0.50,
                "pct_peaking": 8.0,
            },
            # CT_CHP cogens: previously driven by the legacy ct_*_hr_override
            # triple (committed 1.10 / econ 1.20 / peak 1.40). Now expressed as
            # an offer curve so the econ ramp and peak are tweakable like every
            # other group. econ_low == econ_high keeps the default a flat 1.20
            # economic block (no dispatch change vs the old single econ value);
            # pull them apart to create a slope. Peaking % stays the CSV value
            # (no pct_peaking key). The ct_*_hr_override fields above are now
            # inert for CT_CHP.
            # NOTE (CAISO CT_CHP — EOR cogen over-dispatch, FIXED at the fleet
            # heat-rate layer, not here): the CAISO CT_CHP fleet's three big
            # Kern-County enhanced-oil-recovery cogens (Kern River 10496,
            # Sycamore 50134, Midway Sunset 52169) report a steam-credited
            # (artificially efficient ~5-6 MMBtu/MWh) EIA-923 heat rate, so this
            # offer curve's 1.10 committed multiplier priced them as cheap
            # baseload and the LP ran the three flat at ~88% CF (3.7 TWh in 2024)
            # vs ~0.8 measured. The fix is the POWER-ONLY heat-rate correction in
            # chp._correct_chp_steam_credit_hr, which
            # lifts those three units to the simple-cycle band (~9-11) so they
            # clear on price like peakers — CT_CHP 6.95 -> 3.54 TWh (2024),
            # FAIL -> PASS. It is grounded in topping-cycle physics (steam-credit
            # ratio), NOT this residual-tunable offer curve, so the offer curve
            # stays the validated compact-cogen 1.10/1.20/1.40 for the rest of
            # CT_CHP. (The freed energy backfills onto CC_REGULAR via the
            # evening-ramp import-under / domestic-gas-over root cause, which is
            # the open C1/C3 item — see docs/caiso-eor-power-hr-2026-06.md.)
            "CT_CHP": {
                "committed": 1.20 if iso == "PJM" else 1.10,
                "econ_low": 1.20,
                "econ_high": 1.20,
                "peak": 1.40,
                "econ_low_share": 0.50,
            },
            # CT/ST committed band raised as a P1 startup-cost proxy: the
            # part-load committed slice only clears when price is high, so
            # peakers stop parking at ~20% CF for hundreds of hours. CT hurdle
            # is committed 1.55 (peak HR mult 13.15); ST hurdle committed 0.81
            # with a slightly lower econ-high / peak top. The CT committed
            # hurdle / econ-low / peak are an ERCOT calibration tune; PJM keeps
            # its own validated CT curve (committed 1.10, econ_low 1.32,
            # peak 13.0).
            # ERCOT committed folds in the run57 baseline (1.55 -> 1.48).
            "CT_PEAKER": {
                "committed": 1.10
                if iso == "PJM"
                else (1.48 if iso == "ERCOT" else 1.55),
                "econ_low": 1.20 if iso == "PJM" else 1.27,
                "econ_high": 1.98,
                "peak": 13.0 if iso == "PJM" else 13.15,
                "econ_low_share": 0.526,
                "pct_peaking": 7.0,
            },
            # Intermediate-duty simple-cycle CTs (MISO). EIA-860 confirms these
            # are genuine GT/IC units, not mislabeled CCs — but their measured
            # CAMPD median CF (>= ct_intermediate_cf_threshold) shows they run
            # intermediate/near-baseload, not as true peakers. Routed here only
            # when config.ct_intermediate_split is set (fleet._offer_curve_for_group
            # + fleet.ct_intermediate_plants); the rest of CT_PEAKER keeps the
            # steep true-peaker curve above. The committed-band start-cost hurdle
            # (CT_PEAKER 1.55) is dropped — an always-running unit amortizes its
            # one start over thousands of hours, so its committed energy is priced
            # at its own delivered marginal cost (base_HR x ~1.0-1.2) with a thin
            # rising ramp, overlapping the CC fleet so it clears at intermediate
            # load. A modest scarcity peak (3.0) is kept above the ramp. Inert for
            # every ISO/run with the split off (keepers unchanged).
            "CT_INTERMEDIATE": {
                "committed": 1.00,
                "econ_low": 1.00,
                "econ_high": 1.20,
                "peak": 3.00,
                "econ_low_share": 0.50,
                "pct_peaking": 5.0,
            },
            # ERCOT bands fold in the run57 baseline (committed 0.81->0.91,
            # econ_low 1.05->1.15, econ_high 1.40->1.55). Other ISOs unchanged.
            "ST_GAS": {
                "committed": 0.91 if iso == "ERCOT" else 0.81,
                "econ_low": 1.15 if iso == "ERCOT" else 1.05,
                "econ_high": 1.55 if iso == "ERCOT" else 1.40,
                "peak": 4.20,
                "econ_low_share": 0.500,
                "pct_peaking": 15.0,
            },
            # Flatter curve for the measured intermediate-duty MISO steam cohort
            # (fleet.st_gas_intermediate_plants, median CF >= threshold), routed
            # here only when st_gas_intermediate_split is set (--st-gas-intermediate;
            # default OFF, so every prior keeper / other ISO is byte-identical and
            # the base ST_GAS curve above is untouched). These near-baseload
            # boilers (Harding Street, Ames, Nine Mile Pt, Lewis Creek, Sabine)
            # carry almost no peaking band — their energy is sustained, not
            # scarcity — so the steep peaker-shaped ST_GAS curve mis-prices them
            # above merit and the model under-runs them. Mirrors CT_INTERMEDIATE.
            "ST_GAS_INTERMEDIATE": {
                "committed": 0.85,
                "econ_low": 1.00,
                "econ_high": 1.15,
                "peak": 2.20,
                "econ_low_share": 0.500,
                "pct_peaking": 6.0,
            },
            # Coal split by supply: lignite (mine-mouth) raised +0.05 across the
            # board; PRB uses a pure offer curve (sigmoid off) -- higher commit,
            # lower econ-low start, slightly higher econ-high.
            "COAL_LIGNITE": {
                "committed": 0.95,
                "econ_low": 1.14,
                "econ_high": 1.15,
                "peak": 1.55,
                "econ_low_share": 0.556,
            },
            # ERCOT econ bands fold in the run57 baseline (econ_low 0.77->0.70,
            # econ_high 1.19->0.94). Other ISOs keep the prior PRB curve.
            # PRB committed-band tuning is applied per-run as an offer-curve
            # delta (e.g. Run-60 -0.05, Run-61 -0.20), not baked in here, so the
            # baseline stays at run57 and every run's tweak is delta-from-run57.
            "COAL_PRB": {
                "committed": 0.95,
                "econ_low": 0.70 if iso == "ERCOT" else 0.77,
                "econ_high": 0.94 if iso == "ERCOT" else 1.19,
                "peak": 1.48,
                "econ_low_share": 0.556,
            },
            # Non-ERCOT coal by EIA-923 fuel rank (scripts/derive_coal_supply.py;
            # routes via fleet._COAL_SUPPLY_TO_CURVE). PJM 2024: 25 bituminous,
            # 8 waste, 2 sub-bituminous plants. Per-plant delivered fuel cost
            # already comes from EIA-923, so these shape the dispatch curve:
            #  - COAL_BIT: Appalachian/Illinois-Basin bituminous — the baseload
            #    workhorse; keeps the validated generic-coal curve.
            #  - Sub-bituminous (Powder River by rail) routes to COAL_PRB —
            #    one PRB name across ISOs (plant_taxonomy COAL_SUPPLY_TO_CLASS);
            #    its non-ERCOT band variants live on the COAL_PRB entry above.
            #  - COAL_WC: waste coal/culm (subsidised remediation fluidised-bed)
            #    — runs flat baseload, almost never peaks (low peak band).
            "COAL_BIT": {
                "committed": 0.90,
                "econ_low": 0.95,
                "econ_high": 1.10,
                "peak": 1.45,
                "econ_low_share": 0.55,
            },
            "COAL_WC": {
                "committed": 0.85,
                "econ_low": 0.90,
                "econ_high": 1.02,
                "peak": 1.20,
                "econ_low_share": 0.55,
            },
            # Generic fallback for coal plants with no EIA-923 receipts / rank
            # (and ISOs not yet derived). Flat baseload curve.
            "COAL": {
                "committed": 0.90,
                "econ_low": 0.95,
                "econ_high": 1.10,
                "peak": 1.45,
                "econ_low_share": 0.55,
            },
        },
        chp_steam_following=True,  # model CC/CT/ST_CHP as steam-host cogens:
        #   a per-plant sector-keyed BTM pull-out (fleet.chp_btm_pct) plus a
        #   grid-delivered steam-following min-gen (CHP_PMIN_CF_BY_PLANT - BTM).
        chp_btm_floor_pct=40.0,  # flat fallback only (sector BTM supersedes it).
        # ERCOT's unit-level derate only supplements the facility overlay, so it
        # keeps both. Other ISOs (PJM) derive their unit-level file from ALL
        # CAMPD unit data — the complete outage source — so they drop the
        # redundant facility overlay to avoid double-counting (which crushed
        # coal availability and spiked prices).
        historic_outage_overlay=(iso == "ERCOT"),
        # Uniform gas pricing is the default because ERCOT's EIA-923 gas
        # reporting is sparse (~12% of CC capacity), so per-plant pricing
        # penalises the few reporting plants. Non-ERCOT ISOs (PJM) have good
        # gas reporting coverage, and uniform Henry-Hub+basis underprices their
        # delivered gas — CC overran +25 TWh and displaced coal. Re-enable
        # per-plant EIA-923 monthly gas costs for them.
        gas_plant_monthly_fuel_pricing=(iso != "ERCOT"),
        # Dual-fuel switching (doc 03 Pack G; doc-07 design decision 3): EIA-860
        # oil/gas switch-capable gas units price fuel at min(gas, oil) per hour,
        # so winter delivered-gas spikes past oil parity no longer price them out
        # of the merit order. Gated to the winter-fidelity cluster — PJM plus the
        # NE/NY ISOs (doc-07 P13: NYISO downstate Ravenswood/Astoria/Bowline/
        # Roseton/Northport CT/ST units carry ~17 GW of oil backup; doc-08:
        # NEISO's Algonquin-spot marginal gas unit). Default-off for every other
        # ISO (ERCOT/CAISO/MISO/SPP) — their fleets carry no meaningful dual-fuel
        # behaviour — so they stay byte-identical. NOTE (NYISO U4 caveat): without
        # the Transco Z6 winter-basis upload, the gas leg is the ISO-average
        # measured 923 series, whose Jan-2023 $10.02/MMBtu stays below distillate
        # parity (~$16-20), so the switch is correctly wired but rarely binds on
        # the ISO-average; the downstate Z6 blowout (U4) is what crosses parity.
        dual_fuel_switching=(iso.upper() in ("PJM", "NYISO", "NEISO")),
        # Re-attribute switched dual-fuel MWh to oil (doc-08 §2d) — OFF by
        # default (opt in with --gas-hub-basis-daily, which it rides with):
        # it only bites once the daily overlay pushes winter gas past oil
        # parity. The NEISO keepers run the measured daily overlay (neiso-33
        # onward), so the switch trips on the real cold-day AGT spikes and the
        # ~1.5 TWh measured winter oil burn is relabeled out of gas. Without the
        # daily overlay (flat monthly hub) modeled oil collapses to ~zero and the
        # gas family is over-counted by that ~1.5 TWh — the regression that broke
        # neiso-36's C2 before the daily overlay was restored.
        dual_fuel_oil_reattribution=False,
    )
    if any(f.name == "gas_price_override" for f in fields(ScenarioConfig)):
        config = config.with_overrides(gas_price_override=gas_price)
    else:
        logger.warning(
            "ScenarioConfig has no gas_price_override field; "
            "year %d falls back to the '%s' gas-price trajectory",
            year,
            config.gas_price_path,
        )
    if coal_passthrough is not None:
        config = config.with_overrides(coal_prb_contract_passthrough=coal_passthrough)
    # PJM uses its own price-calibrated offer curve (the per-class block above
    # carries ERCOT-fitted values for the shared classes). Replacing the whole
    # dict keeps the calibrated PJM curve in one place (_PJM_OFFER_CURVE) and
    # out of the per-band `if iso == "PJM"` ternaries. Operator --offer-curve
    # overrides/deltas below still merge on top, so a sweep starts from the
    # calibrated PJM curve.
    if iso.upper() == "PJM":
        config = config.with_overrides(
            offer_curve_by_group={k: dict(v) for k, v in _PJM_OFFER_CURVE.items()}
        )
    # Neutralize the generic gas band multipliers for every non-ERCOT/non-PJM ISO
    # BEFORE its grounded per-ISO curve is deep-merged on top (rule #24, audit
    # C-11/C-13): the shared fallback carries 1.0 multipliers, so a band an ISO
    # does not explicitly ground resolves to its own base heat rate instead of a
    # silently-inherited ERCOT-fitted value. ERCOT keeps the calibrated base; PJM
    # is fully replaced above. CAISO/MISO/NEISO/NYISO each restore their grounded
    # bands via the per-ISO curves below.
    elif iso.upper() not in ("ERCOT",):
        config = config.with_overrides(
            offer_curve_by_group=_neutralize_generic_gas_bands(
                config.offer_curve_by_group
            )
        )
    # NYISO gas offer curves (SOM-grounded; see _NYISO_OFFER_CURVE). Merged on
    # top of the generic non-PJM/non-ERCOT branch so only the gas classes change
    # and coal/CT_CHP/ST_CHP keep their defaults. Operator --offer-curve
    # overrides/deltas below still merge on top.
    if iso.upper() == "NYISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _NYISO_OFFER_CURVE
            )
        )
    # CAISO gas offer curves (DMM-grounded near-SRMC shape + the $1,000-2,000
    # soft-cap CT scarcity band; see _CAISO_OFFER_CURVE). Merged on top of the
    # generic non-PJM/non-ERCOT branch so only the named gas classes change and
    # CC_CHP / CT_CHP / ST_GAS / coal keep their generic defaults. Replaces the
    # silently-inherited ERCOT offer multipliers (and the ERCOT 13.15x CT wall)
    # that were the domestic source of the CA-zone midday/body LMP over-price.
    # Operator --offer-curve overrides/deltas below still merge on top.
    if iso.upper() == "CAISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _CAISO_OFFER_CURVE
            )
        )
    # MISO gas offer curves (CAMPD-/structure-grounded; see _MISO_OFFER_CURVE).
    # Merged on top of the generic non-PJM/non-ERCOT branch so only the named gas
    # classes change (CC_REGULAR flattened to MISO's measured baseload shape;
    # CT_PEAKER peak capped off the inherited ERCOT 13.15x ORDC wall) and coal /
    # CC_CHP / CT_CHP / ST_GAS keep their generic defaults. Replaces MISO's silent
    # inheritance of the ERCOT-fitted `else` values. Operator --offer-curve
    # overrides/deltas below still merge on top.
    if iso.upper() == "MISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _MISO_OFFER_CURVE
            )
        )
    # NEISO gas offer curve (see _NEISO_OFFER_CURVE). Consolidates NEISO's
    # effective gas curve — previously a scattered inline CC_REGULAR committed
    # override plus a silent fall-through to the generic ERCOT-derived else — into
    # one grounded, commented place at parity with PJM/NYISO. Merged on top of the
    # generic branch so only the named gas classes change and coal / *_INTERMEDIATE
    # keep their defaults; per-plant committed/peaking % from CAMPD still supersede.
    # Operator --offer-curve overrides/deltas below still merge on top.
    if iso.upper() == "NEISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _NEISO_OFFER_CURVE
            )
        )
    # Operator-supplied per-class/per-band heat-rate multiplier overrides
    # (run_calibration_full --offer-curve-json) deep-merged onto the calibrated
    # defaults above. Only the named bands change; the merged curve is recorded
    # verbatim in the bundle's run_config.json (scenario_config.offer_curve_by_group).
    if offer_curve_overrides:
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, offer_curve_overrides
            )
        )
    # Relative nudges (run_calibration_full --offer-curve-delta-json): added on
    # top of the (possibly absolute-overridden) curve, so the operator can tweak
    # by +/-0.05 without restating the prior value. The resolved absolute curve
    # is still recorded in run_config.json.
    if offer_curve_deltas:
        config = config.with_overrides(
            offer_curve_by_group=_apply_offer_curve_deltas(
                config.offer_curve_by_group, offer_curve_deltas
            )
        )
    return config
