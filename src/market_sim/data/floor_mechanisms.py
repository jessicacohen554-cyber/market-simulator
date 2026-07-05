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
# Zero-forcing ablation registry (audit §7 D-3, CLAUDE.md rule 21)
# ---------------------------------------------------------------------------
# The D-3 zero-forcing ablation twin re-solves a keeper with every *merchant*
# floor/bridge disabled, while KEEPING the structural protected set
# (:data:`D2_EXEMPT_MECHS`: nuclear must-run, CHP steam-following, coal
# take-or-pay). It answers "what does each floor buy?" — the keeper-vs-twin
# per-class delta is the forced energy each merchant mechanism supplies.
#
# "Merchant" is defined NEGATIVELY off this registry: every mechanism id that is
# neither a structural protected must-run nor a pure market-design boundary
# floor (:data:`ABLATION_KEEP_MECHS`). Deriving the off-list this way — instead
# of a hand-maintained class/toggle tuple in the config layer — means a
# newly-registered floor is ablated BY DEFAULT the moment it is assigned a
# ``MECH_*`` id: whoever adds a mechanism must consciously place it in
# ``ABLATION_KEEP_MECHS`` to exempt it from the twin (rule 21).
#
# NYISO local self-supply (:data:`MECH_NYISO_SELFSUPPLY`) rides a pseudo-unit
# like the firm-import band, but it is a merchant / outcome-anchored floor
# (audit L2, §2 "DwC" — the 0.45 fraction is set below the realized share), so
# it is ABLATED. Only firm interchange imports (:data:`MECH_FIRM_IMPORT`) — a
# market-design boundary condition, not a merchant thermal floor — are kept.
ABLATION_KEEP_MECHS: frozenset[int] = D2_EXEMPT_MECHS | frozenset({MECH_FIRM_IMPORT})

# Merchant mechanisms whose disabling ScenarioConfig field is NOT simply the
# bool named by ``MECH_NAMES[id]``, or that need several knobs cleared together.
# Every other merchant mechanism disables the bool field == ``MECH_NAMES[id]``.
_MERCHANT_ABLATION_OVERRIDES: dict[int, tuple[tuple[str, object], ...]] = {
    # MECH_NAMES value is "st_netload_drag"; the ScenarioConfig field is
    # "gas_st_netload_drag".
    MECH_ST_NETLOAD_DRAG: (("gas_st_netload_drag", False),),
    # The CAISO RA must-offer bridge is one phenomenon spread over three
    # toggles: the base physical bridge plus its startup-cost-aware extension
    # and the solar-proportional decommit control. All off together.
    MECH_RA_MUSTOFFER: (
        ("caiso_ra_mustoffer", False),
        ("caiso_ra_startup_bridge", False),
        ("caiso_ra_bridge_decommit", False),
    ),
}


def merchant_mechanism_ids() -> frozenset[int]:
    """Return the merchant floor-mechanism ids ablated by the D-3 twin.

    Every registered mechanism except :data:`MECH_NONE`, the structural
    protected set, and the market-design boundary floors
    (:data:`ABLATION_KEEP_MECHS`). A new id added to :data:`MECH_NAMES` is
    merchant — hence ablated — by default.
    """
    return frozenset(
        m for m in MECH_NAMES if m != MECH_NONE and m not in ABLATION_KEEP_MECHS
    )


def merchant_ablation_fields() -> dict[str, object]:
    """Return ``{ScenarioConfig field: neutral value}`` disabling every merchant floor.

    Derived from the mechanism registry so the zero-forcing ablation
    (``ScenarioConfig.as_zero_forcing_ablation``) never hand-maintains a class
    tuple. A merchant mechanism without an entry in
    :data:`_MERCHANT_ABLATION_OVERRIDES` disables the bool ScenarioConfig field
    whose name equals ``MECH_NAMES[id]``; the overrides handle the few fields
    whose name differs or that need several knobs cleared at once.
    """
    out: dict[str, object] = {}
    for m in merchant_mechanism_ids():
        overrides = _MERCHANT_ABLATION_OVERRIDES.get(m)
        if overrides is None:
            out[MECH_NAMES[m]] = False
        else:
            for field_name, neutral in overrides:
                out[field_name] = neutral
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
