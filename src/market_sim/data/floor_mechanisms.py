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
}

# Mechanisms whose forced energy is exempt from the D-2 merchant-class gates
# (audit §7 D-2: "nuclear/CHP-steam/coal-take-or-pay exempt"). Interchange
# pseudo-unit floors are market-design boundary conditions, not thermal
# forcing, and are excluded from class forced-share arithmetic entirely.
D2_EXEMPT_MECHS: frozenset[int] = frozenset(
    {MECH_NUCLEAR, MECH_CHP_STEAM, MECH_COAL_MUSTRUN}
)
NON_THERMAL_MECHS: frozenset[int] = frozenset({MECH_FIRM_IMPORT, MECH_NYISO_SELFSUPPLY})


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


def tag_raised(
    mech: np.ndarray,
    rows,
    before: np.ndarray,
    after: np.ndarray,
    mech_id: int,
) -> None:
    """Tag ``mech[rows]`` with ``mech_id`` wherever ``after`` > ``before``.

    ``before``/``after`` are the floor values for the same ``rows`` slice,
    captured around a ``np.maximum`` (or assignment) composition. Strict
    inequality implements maximum-composition: ties keep the incumbent
    mechanism's id.
    """
    raised = after > before
    if not np.any(raised):
        return
    sub = mech[rows]
    sub[raised] = mech_id
    mech[rows] = sub


def clear_where_unfloored(mech: np.ndarray, min_gen: np.ndarray) -> None:
    """Zero mechanism ids wherever the composed floor is not positive.

    Called after downstream caps (availability clamp, COD ramp) shrink the
    floor: a unit-hour whose floor collapsed to <= 0 is no longer forced by
    anything, whatever raised it earlier.
    """
    mech[min_gen <= 0.0] = MECH_NONE
