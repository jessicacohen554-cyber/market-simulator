"""Mechanism-id registry for minimum-generation floor attribution (audit D-2).

Every injector that raises ``FleetArrays.min_gen`` tags the unit-hours it
floors with a small integer mechanism id in the parallel ``(n_gen, T)`` int8
array ``FleetArrays.min_gen_mechanism``. Floors compose via ``np.maximum``
(the binding floor wins), so the tagging rule is *maximum-composition*: a
unit-hour keeps the id of whichever mechanism supplied the **binding**
(largest) floor — an injector overwrites the id only where it strictly raised
``min_gen``. Unit-hours with no positive floor carry :data:`MECH_NONE`.

This attribution exists so the legitimacy diagnostics
(``scripts/legitimacy_diagnostics.py``, audit
``docs/model-legitimacy-audit-2026-07.md`` §7 D-2/D-4) can report how much
energy each class dispatches *at* a binding floor, by mechanism — forced
energy is budgeted, not silently stacked. The array is diagnostic metadata
only: nothing in the LP build reads it, so threading it through cannot change
a solve.
"""

from __future__ import annotations

import numpy as np

# Mechanism ids (int8). 0 is reserved for "no floor / not floored".
MECH_NONE: int = 0
# Structural must-run floors (exempt from the D-2 merchant forced-share gates:
# nuclear cannot load-follow, CHP follows its steam host, take-or-pay coal is
# contract economics — audit §2 "min-gen floors" verdicts).
MECH_NUCLEAR: int = 1
MECH_CHP_STEAM: int = 2
MECH_COAL_MUSTRUN: int = 3
# Reliability commitment floors (DwC — legitimate class, windowing under audit).
MECH_RELIABILITY_FLOOR: int = (
    4  # registry engine (transmission.inject_reliability_floor)
)
MECH_CT_NETLOAD_DRAG: int = 5
MECH_ST_NETLOAD_DRAG: int = 6
MECH_RA_MUSTOFFER: int = 7  # CAISO RA must-offer physical/startup bridge (P2)
# Measured-outcome overlay probes (FIT-FORCING; default-off, quarantined by D-9).
MECH_CT_MUSTRUN_PER_PLANT: int = 8
MECH_CT_DEPLOYMENT_OVERLAY: int = 9
MECH_RELIABILITY_DEPLOYMENT_OVERLAY: int = 10
MECH_CAISO_GAS_COMMITMENT_FLOOR: int = 11
# Interchange / market-design floors on pseudo-units (import bands, pockets).
MECH_FIRM_IMPORT: int = 12
MECH_NYISO_SELFSUPPLY: int = 13
# NEISO winter fuel-security must-run (Component B): the fuel-secure steam fleet
# (COAL_BIT + oil-capable ST_GAS) postured on winter cold days under the ISO-NE
# winter-reliability program posture (WRP/IEP/OFSA). A merchant reliability
# commitment (NOT structural must-run) — subject to the D-2 forced-share gate and
# ablated in the zero-forcing twin.
MECH_WINTER_FUELSEC: int = 14
# Per-plant gas (CC_REGULAR) local-reliability commitment floor
# (ScenarioConfig.cc_mustrun_per_plant): the plant's CEMS-measured committed
# tranche forced on in its measured top-online_frac system-load hours — the
# out-of-market LDA/voltage reliability commitment (bid-cost recovery / RMR).
# CC-only: the CT_PEAKER leg was probed and dropped (overnight off-window
# binding against the class's own evidence, rule 12 — see the ScenarioConfig
# field docstring).
# A merchant reliability commitment (NOT structural must-run): parameter-based
# (committed share + online fraction, thermal_tranches_<ISO>.csv), unlike the
# quarantined MECH_CT_MUSTRUN_PER_PLANT above which pins observed net-generation
# MWh. Subject to the D-2 forced-share gate; ablated in the zero-forcing twin.
MECH_CC_MUSTRUN_PER_PLANT: int = 15
# The ST_GAS leg of the same per-plant local-reliability commitment floor
# (ScenarioConfig.st_gas_mustrun_per_plant): identical mechanics and artifact
# columns, separate gate + id so D-2/D-4 attribution and per-ISO arming stay
# independent of the CC leg. Driver: the Entergy MISO-South steam fleet's
# VLR/self-commitment (MISO SOM out-of-market voltage-and-local-reliability
# commitments; CEMS shows Nine Mile synchronized 98.2% of ALL hours 2023-2025,
# Sabine 85.6%, Lewis Creek 87.8%). A merchant reliability commitment —
# subject to the D-2 forced-share gate; ablated in the zero-forcing twin.
MECH_ST_GAS_MUSTRUN_PER_PLANT: int = 16
# ERCOT gas-CC commitment bridge (ScenarioConfig.ercot_gas_commitment_bridge):
# the P1-native committed-state floor promoted from the ERCOT-62b probe
# (docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md §5-6). The same
# ISO-neutral internals as the CAISO RA must-offer bridge
# (model.commitment.caiso_ra_mustoffer_min_gen — min-down physics + the
# startup-restart inequality on the model's OWN P0 run pattern and duals),
# routed onto the ERCOT merchant gas-CC fleet with min_load_frac = the
# MEASURED committed-CC LSL/HSL capacity-weighted p50 (60-Day DAM disclosure
# 2023-2025). Separate id from MECH_RA_MUSTOFFER so D-2/D-4 attribution and
# per-ISO arming stay independent (the MECH_ST_GAS_MUSTRUN_PER_PLANT
# precedent). A merchant commitment floor — subject to the D-2 forced-share
# gate; ablated in the zero-forcing twin.
MECH_GAS_COMMITMENT_BRIDGE: int = 17
# Conventional-hydro minimum-flow floor (ScenarioConfig.hydro_min_flow_floor):
# the month-constant sustained level below which the measured hydro fleet never
# runs — run-of-river inflow that cannot be stored plus the environmental /
# FERC-licence minimum releases the fleet must pass. The energy-budget LP has an
# energy CAP but no lower bound, so it is free to park the fleet at 0 MW; this is
# the lower half of the same measured two-sided capability envelope whose upper
# half is config.hydro_dispatch_envelope. NON-THERMAL forcing (water, not a
# commitment decision): it is reported by D-2 but excluded from the merchant
# thermal forced-share arithmetic, like the interchange pseudo-unit floors.
# Level: data.eia_loader.measured_hydro_min_flow_level (EIA-930 NG:WAT monthly
# Q95), allocated per plant by data.hydro.allocate_min_flow_floor.
MECH_HYDRO_MIN_FLOW: int = 18
# Conventional-hydro run-of-river flat dispatch (ScenarioConfig.hydro_ror_split,
# caiso-126): plants the external hydro-plant-modes classifier (ORNL EHA Mode +
# the documented HILARRI/Corps-dam completion — data/clean/hydro-plant-modes)
# marks NON-shapeable dispatch flat at their own measured monthly water,
# budget[g,m]/hours[m] — run-of-river/canal output follows inflow and cannot
# chase price. Implemented as min_gen == pmax x availability == the flat level,
# so the forced energy is fully visible to D-2/D-4 under this id. NON-THERMAL
# forcing (water physics, not a commitment decision), same class as
# MECH_HYDRO_MIN_FLOW. Rule 19: when hydro_min_flow_floor is also on, the
# reservoir class carries the fleet Q95 level MINUS the RoR flat base (the RoR
# base subsumes its own share of the floor's driver) — the two mechanisms are
# one reconciled family, never stacked on the same MWh.
MECH_HYDRO_ROR_FLAT: int = 19
# NYISO gas commitment bridge (ScenarioConfig.nyiso_gas_commitment_bridge,
# nyiso-87): the P1-native committed-state floor that REPLACES the h14-21
# peak-window reliability-floor limbs (owner directive 2026-07-27 — "the
# h14-21 peak-hour must-run is INACCURATE ... every floor we have added was a
# compensation for [the] missing commitment drag"). The same ISO-neutral
# detector as the CAISO RA must-offer / ERCOT gas-CC bridges
# (model.commitment.caiso_ra_mustoffer_min_gen) routed onto the NYISO merchant
# slow-start gas fleet (gas_cc + gas_st, both passing the rule-18 physics gate:
# min-down 4-12 h, $35-50/MW starts; the fast-start CT classes are excluded by
# their own 1 h min-down / $20 starts), with the MEASURED per-class min-load
# fractions and the minimum-run-duration extension. Separate id from
# MECH_GAS_COMMITMENT_BRIDGE (the ERCOT leg) so D-2/D-4 attribution and
# per-ISO arming stay independent — the MECH_ST_GAS_MUSTRUN_PER_PLANT
# precedent. A merchant commitment floor — subject to the D-2 forced-share gate.
MECH_NYISO_GAS_COMMITMENT_BRIDGE: int = 20

# Coal MINIMUM ONLINE CONFIGURATION floor (ercot128-unit-grain,
# config.ercot_coal_min_config_floor): a multi-unit coal plant cannot be pushed
# below the registered minimum load of its SMALLEST online configuration,
# ``min over units u of MinLoad_u`` (EIA-860 ``Minimum Load (MW)``, derived by
# scripts/data/derive_eia860_coal_min_config.py). This is unit-grain
# commitment's LOWER ENVELOPE, and it needs no commitment state and no
# integrality: where the plant's exact unit-commitment feasible set is
# connected — 9 of 10 ERCOT coal plants, 97.8 % of coal capacity — the
# plant-grain interval represents it with zero error. Distinct from
# MECH_COAL_MUSTRUN (id 3), which is the step-3a synchronization floor on the
# _mustrun/_sync tranches: different driver, different level, separate id so
# D-2/D-4 attribution stays per-mechanism (rule 19 [R-ONE-MECH]). A merchant
# commitment floor — subject to the D-2 forced-share gate.
MECH_COAL_MIN_CONFIG: int = 21
# MISO regulated-coal WITHIN-RUN NIGHT floor (miso-113,
# config.miso_coal_night_floor): the P1-native committed-state floor on the
# regulated PRB/subbituminous fleet, sized at each plant's OWN measured
# within-run night level (night_p50 = p50 of load/HSL over online hours h0-5,
# pooled 2023-2025 — data/raw/_processed-legacy/coal_prb_committed_split_
# MISO.csv, frozen deriver scripts/data/derive_prb_committed_split.py), NET of
# that plant's _mustrun band so the plant's TOTAL floor is exactly
# night_p50 x nameplate and never mustrun + night (rule 19 [R-ONE-MECH]).
# Same ISO-neutral detector as the CAISO RA must-offer / ERCOT / NYISO gas
# bridges (model.commitment.caiso_ra_mustoffer_min_gen) on the model's own P0
# run pattern, with the ercot141 online-hours leg: the window is the detected
# committed run, not a clock-hour boxcar. Driver: regulated SELF-COMMITMENT
# (MISO SOM Table 7 — 53-56 % of coal starts are self-committed). Separate id
# from MECH_COAL_MUSTRUN (id 3, the step-3a synchronization floor) and from
# MECH_COAL_MIN_CONFIG (id 21, the unit-configuration lower envelope): three
# different drivers, three different levels, per-mechanism D-2/D-4
# attribution. A merchant-visible commitment floor — subject to the D-2
# forced-share gate.
MECH_MISO_COAL_NIGHT_FLOOR: int = 22

# ercot-227 F3 (PRECOMMIT-ercot226 §5.11 Amendment 3, owner waiver W-3):
# the measured RUC INSTRUCTION-STATE commitment floor — per class-hour, the
# NP3-965 ``Telemetered Resource Status == ONRUC`` units' summed LSL
# (derive_ercot_ruc_committed.py), distributed pro-rata over the class's
# available capacity. DRIVER: the operator's RUC instruction (an input of
# the outage-window family, rule 13 — never realized output, the D-9
# quarantined deployment-overlay shape, and never a per-unit crosswalk,
# Q-B). WINDOW: the measured instruction hours themselves — zero series ⇒
# zero floor by construction. A merchant-visible commitment floor — subject
# to the D-2 forced-share gate; rule-19 incumbents (the gas bridge on CC,
# the ST_GAS net-load drag) reconcile through maximum-composition with
# per-mechanism attribution (ties keep the incumbent id).
MECH_ERCOT_RUC_COMMITMENT: int = 23
# SPP gas commitment bridge (ScenarioConfig.spp_gas_commitment_bridge, SPP-44):
# the P1-native committed-state floor on SPP's merchant slow-start gas fleet
# (gas_cc + gas_st by the rule-18 physics gate: min-down 4-12 h, $35-50/MW
# starts on every committed tranche; the CT classes fail on their own 1 h
# min-down and are never named). The same ISO-neutral detector as the CAISO /
# ERCOT / NYISO legs (model.commitment.caiso_ra_mustoffer_min_gen via
# pipeline.commitment.build_spp_gas_bridge_p1_prep), at the MEASURED
# plant-basis minimum stable load (constants.SPP_GAS_BRIDGE_MIN_LOAD_FRAC) with
# the measured minimum-run extension (constants.SPP_GAS_BRIDGE_MIN_RUN_HOURS)
# and the commitment-real run screen. Its own id — the
# MECH_NYISO_GAS_COMMITMENT_BRIDGE precedent — so D-2/D-4 attribution and
# per-ISO arming stay independent (rule 25). Rule 19: SPP's gas classes carry
# NO other floor, bridge, drag or posture (keeper-2 D-2: 0.0 % forced on
# CC_REGULAR / ST_GAS / CT_PEAKER), so this stacks on nothing. A merchant
# commitment floor — subject to the D-2 forced-share gate.
MECH_SPP_GAS_COMMITMENT_BRIDGE: int = 24
# soco_gas_st_campaign_commitment (SOCO-53d,
# pipeline.commitment.build_soco_gas_st_campaign_p1_prep): the P1-native
# CAMPAIGN commitment floor on SOCO's gas-STEAM fleet. Same ISO-neutral
# detector as the CAISO / ERCOT / NYISO / SPP legs
# (model.commitment.caiso_ra_mustoffer_min_gen) but a DIFFERENT leg of it: the
# measured minimum-RUN extension plus the online-hours LSL state floor, with
# the gap-bridge legs deliberately NOT armed. SOCO's boilers do not two-shift
# — 98.6 % of their downtime-hours sit in gaps longer than 72 h, which is why
# the gap bridge is recorded `R` for this ISO (SOCO-53) — they synchronize for
# CAMPAIGNS: 5.0-9.7 starts a year and 64-192 h minimum campaigns at plant
# grain, against 10-349 model starts of 2-11 h median. Level and horizon are
# per-plant measured (data.gas_st_campaign; rule 25 [R-ISO-SCOPE] — SOCO's own
# plants only). Its own id, the MECH_SPP_GAS_COMMITMENT_BRIDGE precedent, so
# D-2/D-4 attribution and per-ISO arming stay independent. Rule 19
# [R-ONE-MECH]: SOCO's gas classes carry NO other floor, bridge, drag or
# posture (keeper D-2: 0.0 % forced on CC_REGULAR / ST_GAS / CT_PEAKER / COAL),
# so this stacks on nothing. A merchant commitment floor — subject to the D-2
# forced-share gate.
MECH_SOCO_GAS_ST_CAMPAIGN: int = 25

MECH_NAMES: dict[int, str] = {
    MECH_NONE: "none",
    MECH_NUCLEAR: "nuclear_mustrun",
    MECH_CHP_STEAM: "chp_steam",
    MECH_COAL_MUSTRUN: "coal_mustrun",
    MECH_RELIABILITY_FLOOR: "reliability_floor",
    MECH_CT_NETLOAD_DRAG: "ct_netload_drag",
    MECH_ST_NETLOAD_DRAG: "st_netload_drag",
    MECH_RA_MUSTOFFER: "ra_mustoffer_bridge",
    MECH_CT_MUSTRUN_PER_PLANT: "ct_mustrun_per_plant",
    MECH_CT_DEPLOYMENT_OVERLAY: "ct_deployment_overlay",
    MECH_RELIABILITY_DEPLOYMENT_OVERLAY: "reliability_deployment_overlay",
    MECH_CAISO_GAS_COMMITMENT_FLOOR: "caiso_gas_commitment_floor",
    MECH_FIRM_IMPORT: "firm_import",
    MECH_NYISO_SELFSUPPLY: "nyiso_local_selfsupply",
    MECH_WINTER_FUELSEC: "winter_fuelsec_mustrun",
    MECH_CC_MUSTRUN_PER_PLANT: "cc_mustrun_per_plant",
    MECH_ST_GAS_MUSTRUN_PER_PLANT: "st_gas_mustrun_per_plant",
    MECH_GAS_COMMITMENT_BRIDGE: "gas_commitment_bridge",
    MECH_HYDRO_MIN_FLOW: "hydro_min_flow",
    MECH_HYDRO_ROR_FLAT: "hydro_ror_flat",
    MECH_NYISO_GAS_COMMITMENT_BRIDGE: "nyiso_gas_commitment_bridge",
    MECH_COAL_MIN_CONFIG: "coal_min_config",
    MECH_MISO_COAL_NIGHT_FLOOR: "miso_coal_night_floor",
    MECH_ERCOT_RUC_COMMITMENT: "ercot_ruc_commitment",
    MECH_SPP_GAS_COMMITMENT_BRIDGE: "spp_gas_commitment_bridge",
    MECH_SOCO_GAS_ST_CAMPAIGN: "soco_gas_st_campaign_commitment",
}

# Mechanisms whose forced energy is exempt from the D-2 merchant-class gates
# (audit §7 D-2: "nuclear/CHP-steam/coal-take-or-pay exempt"). Interchange
# pseudo-unit floors are market-design boundary conditions, not thermal
# forcing, and are excluded from class forced-share arithmetic entirely.
D2_EXEMPT_MECHS: frozenset[int] = frozenset(
    {MECH_NUCLEAR, MECH_CHP_STEAM, MECH_COAL_MUSTRUN}
)
# Non-thermal floors: reported by D-2 but excluded from the merchant thermal
# forced-share arithmetic. Interchange pseudo-units are a network boundary
# condition; the hydro min-flow floor is a hydrological/licence obligation on
# water, not a commitment decision on a thermal merchant unit.
NON_THERMAL_MECHS: frozenset[int] = frozenset(
    {MECH_FIRM_IMPORT, MECH_NYISO_SELFSUPPLY, MECH_HYDRO_MIN_FLOW, MECH_HYDRO_ROR_FLAT}
)


# ---------------------------------------------------------------------------
# D-3 zero-forcing ablation registry (audit §7 D-3 / CLAUDE.md rule 20)
# ---------------------------------------------------------------------------
# Maps each MERCHANT floor/bridge mechanism id to the ``ScenarioConfig`` field(s)
# that arm it and the NEUTRAL (no-op) value each takes in a zero-forcing ablation
# twin. The twin is a reference solve with every merchant floor OFF, KEEPING only
# the structural must-run set (nuclear must-run, CHP steam-following, coal
# take-or-pay) so the keeper-vs-twin per-class delta quantifies what each floor
# buys (a delta explainable only as "the floor buys the residual" is an open
# root-cause item, not a calibrated parameter).
#
# This is THE D-2 mechanism registry the ablation off-list is derived from: the
# off-list is NOT a hand-maintained tuple. :func:`assert_ablation_coverage`
# (exercised by tests/test_floor_mechanisms_ablation.py) requires every mechanism
# id to be EITHER kept (:data:`MECH_ABLATION_KEPT`) or carry an ablation entry —
# so a newly added merchant floor mechanism is ablated by default, or the
# coverage test fails until it is classified.
MECH_ABLATION_FIELDS: dict[int, dict[str, object]] = {
    MECH_RELIABILITY_FLOOR: {"reliability_floor": False},
    MECH_CT_NETLOAD_DRAG: {"ct_netload_drag": False},
    MECH_ST_NETLOAD_DRAG: {"gas_st_netload_drag": False},
    MECH_RA_MUSTOFFER: {
        "caiso_ra_mustoffer": False,
        "caiso_ra_startup_bridge": False,
        "caiso_ra_bridge_decommit": False,
    },
    MECH_CT_MUSTRUN_PER_PLANT: {"ct_mustrun_per_plant": False},
    MECH_CT_DEPLOYMENT_OVERLAY: {"ct_deployment_overlay": False},
    MECH_RELIABILITY_DEPLOYMENT_OVERLAY: {"reliability_deployment_overlay": False},
    MECH_CAISO_GAS_COMMITMENT_FLOOR: {"caiso_gas_commitment_floor": False},
    MECH_NYISO_SELFSUPPLY: {"nyiso_local_selfsupply": False},
    MECH_WINTER_FUELSEC: {"neiso_winter_fuel_mustrun": False},
    MECH_CC_MUSTRUN_PER_PLANT: {"cc_mustrun_per_plant": False},
    MECH_ST_GAS_MUSTRUN_PER_PLANT: {"st_gas_mustrun_per_plant": False},
    MECH_GAS_COMMITMENT_BRIDGE: {"ercot_gas_commitment_bridge": False},
    MECH_NYISO_GAS_COMMITMENT_BRIDGE: {"nyiso_gas_commitment_bridge": False},
    MECH_COAL_MIN_CONFIG: {"ercot_coal_min_config_floor": False},
    MECH_MISO_COAL_NIGHT_FLOOR: {"miso_coal_night_floor": False},
    # Classified ABLATED, not kept: the min-flow floor is a real physical
    # obligation, but it is a NEW mechanism whose forcing must stay visible and
    # switchable rather than joining the protected structural must-run set.
    MECH_HYDRO_MIN_FLOW: {"hydro_min_flow_floor": False},
    # Same classification and rationale as MECH_HYDRO_MIN_FLOW (the reconciled
    # family's other half): real water physics, but new and switchable.
    MECH_HYDRO_ROR_FLAT: {"hydro_ror_split": False},
    # ercot-227 F3: ABLATED (visible, switchable merchant commitment floor).
    MECH_ERCOT_RUC_COMMITMENT: {"ercot_ruc_commitment_floor": False},
    # SPP-44: the SPP leg of the gas commitment bridge family, ABLATED like
    # the ERCOT and NYISO legs (a visible, switchable merchant floor).
    MECH_SPP_GAS_COMMITMENT_BRIDGE: {"spp_gas_commitment_bridge": False},
    # SOCO-53d: the SOCO gas-steam CAMPAIGN commitment floor, ABLATED like
    # every other leg of the family (a visible, switchable merchant floor).
    MECH_SOCO_GAS_ST_CAMPAIGN: {"soco_gas_st_campaign_commitment": False},
}

# Mechanisms KEPT in the ablation twin (carry NO ablation entry): the structural
# must-run set plus the market-design import boundary (import bands are a network
# boundary condition, not merchant thermal forcing) and MECH_NONE.
MECH_ABLATION_KEPT: frozenset[int] = D2_EXEMPT_MECHS | {MECH_FIRM_IMPORT, MECH_NONE}

# Non-mechanism merchant biases the twin also neutralizes. The WEFOR haircuts are
# a class-wide availability lightening rather than a per-unit ``min_gen`` floor,
# so they carry no mechanism id — but they are a merchant-side calibration lever
# the D-3 protected-set spec turns off (keep nuclear / CHP-steam / coal only).
EXTRA_ZERO_FORCING_FIELDS: dict[str, object] = {
    "wefor_residual": None,
    "wefor_residual_groups": None,
    "wefor_multiplier": 1.0,
}


def assert_ablation_coverage() -> None:
    """Raise if any mechanism id is neither kept nor given an ablation entry.

    The guard that keeps the D-3 off-list from silently going stale: every id in
    :data:`MECH_NAMES` must be classified as KEPT (:data:`MECH_ABLATION_KEPT`) or
    ABLATED (:data:`MECH_ABLATION_FIELDS`). A new floor mechanism added to the
    registry without an ablation decision fails this check, so it cannot escape
    the twin unnoticed.
    """
    classified = set(MECH_ABLATION_KEPT) | set(MECH_ABLATION_FIELDS)
    missing = sorted(set(MECH_NAMES) - classified)
    if missing:
        names = [MECH_NAMES.get(m, str(m)) for m in missing]
        raise AssertionError(
            "floor mechanism(s) missing a D-3 ablation decision (add to "
            f"MECH_ABLATION_FIELDS or MECH_ABLATION_KEPT): {names}"
        )
    overlap = sorted(set(MECH_ABLATION_KEPT) & set(MECH_ABLATION_FIELDS))
    if overlap:
        raise AssertionError(
            "floor mechanism(s) both kept and ablated (contradiction): "
            f"{[MECH_NAMES.get(m, str(m)) for m in overlap]}"
        )


def zero_forcing_field_overrides() -> dict[str, object]:
    """Return the merged ``ScenarioConfig`` no-op overrides for a zero-forcing twin.

    Union of every :data:`MECH_ABLATION_FIELDS` entry (the merchant floor
    mechanisms, derived from the D-2 mechanism registry so a new floor is ablated
    by default) plus :data:`EXTRA_ZERO_FORCING_FIELDS` (the WEFOR haircuts, which
    are merchant availability levers without a mechanism id). Structural must-run
    (nuclear / CHP-steam / coal take-or-pay) and the import boundary carry no
    entry, so they are preserved. Raises via :func:`assert_ablation_coverage`
    if the registry is incomplete.
    """
    assert_ablation_coverage()
    out: dict[str, object] = {}
    for fields_map in MECH_ABLATION_FIELDS.values():
        out.update(fields_map)
    out.update(EXTRA_ZERO_FORCING_FIELDS)
    return out


def ensure_mechanism(fleet_arrays) -> np.ndarray:
    """Return ``fleet_arrays.min_gen_mechanism``, allocating it if absent.

    Allocated as int8 zeros shaped like ``fleet_arrays.min_gen`` (which must
    already exist — mechanism ids only make sense once a floor matrix does).
    """
    if fleet_arrays.min_gen is None:
        raise ValueError("min_gen must be allocated before its mechanism array")
    mech = getattr(fleet_arrays, "min_gen_mechanism", None)
    if mech is None or mech.shape != fleet_arrays.min_gen.shape:
        mech = np.zeros(fleet_arrays.min_gen.shape, dtype=np.int8)
        fleet_arrays.min_gen_mechanism = mech
    return mech


def clear_where_unfloored(mech: np.ndarray, min_gen: np.ndarray) -> None:
    """Zero mechanism ids wherever the composed floor is not positive.

    Called after downstream caps (availability clamp, COD ramp) shrink the
    floor: a unit-hour whose floor collapsed to <= 0 is no longer forced by
    anything, whatever raised it earlier.
    """
    mech[min_gen <= 0.0] = MECH_NONE
