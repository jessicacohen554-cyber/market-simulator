"""Multi-tranche offer curves for CAMPD per-plant binning.

Extracted from :mod:`market_sim.data.fleet` — functions that split thermal
generators into stepped supply-curve tranches (coal take-or-pay, gas
committed/economic/peaking) and build the per-plant offer-curve band
visualization for the calibration dashboard.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import numpy as np

from market_sim.config.constants import (
    CC_ECON_HR_OVERRIDE_DEFAULT,
    CC_PEAK_HR_OVERRIDE_DEFAULT,
    GAS_ST_ECON_HR_OVERRIDE_DEFAULT,
    GAS_ST_PEAK_HR_OVERRIDE_DEFAULT,
    GAS_TRANCHE_SHARES_BY_GROUP,
    MISO_OFFER_SPREAD_ANCHOR_RANK,
    MISO_OFFER_SPREAD_ARTIFACT_SHA256,
)
from market_sim.config.plant_taxonomy import COAL_ARTIFACT_FAMILY, is_coal_class
from market_sim.config.scenarios import ScenarioConfig

if TYPE_CHECKING:
    import pandas as pd

    from market_sim.data.fleet import FleetArrays

logger = logging.getLogger(__name__)

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
# DELETED 2026-08-12 (rule 26 [R-DELETE], ercot-188 G#3 owner ruling,
# docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md §G.3):
# split_coal_tranches (the legacy non-CAMPD coal take-or-pay split) and its
# six ScenarioConfig scalars coal_tranche_{1,2,3}_{frac,fuel_passthrough}.
# build_dispatch_fleet branches on `campd_bins is not None`; every registered
# bundle of all six ISOs carries use_campd_bins=True (proof:
# results/calibration/ercot188_g3_unreachability_proof.json), so the function
# lived only in a dead limb and the scalars reached nothing (miso-128 §4
# proved inertness dynamically). The non-CAMPD fallback now passes coal
# through unsplit at full fuel cost; the live coal offer machinery is the
# CAMPD tranche path (campd_tranche_fuel_frac, legacy_bins.apply_coal_tranches).
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

    Takes the caller's per-generator ``fuel_fracs`` (all 1.0 on the legacy
    non-CAMPD path since the split_coal_tranches deletion) and carries each
    non-gas generator through unchanged. Used for non-ERCOT calibration when
    ``config.gas_offer_curve`` is set; ERCOT's offer curve comes from its
    CAMPD bins, not this path.
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


#: Parent gas class -> the duty-split ``*_INTERMEDIATE`` curve it routes to.
#: The parent is the class whose registered ``phys_*`` keys the intermediate
#: cohort borrows under ``miso_intermediate_gas_offer_margin`` (miso-217).
_INTERMEDIATE_PHYS_PARENT: dict[str, str] = {
    "CT_INTERMEDIATE": "CT_PEAKER",
    "CC_INTERMEDIATE": "CC_REGULAR",
    "ST_GAS_INTERMEDIATE": "ST_GAS",
}

#: The ONLY bands whose physical basis is borrowed. Econ-only by design
#: (miso-217 PREREG §2): ``phys_peak`` would replace a deliberate fuel-scaled
#: scarcity wall with a fixed margin and LOWER the cohorts' peak offers by
#: $10-39/MWh in years where C3c is already the single ledgered caveat, and
#: ``phys_committed`` clips to 0 on two of the three cohorts anyway.
_INTERMEDIATE_PHYS_KEYS: tuple[str, ...] = ("phys_econ_low", "phys_econ_high")


def _with_intermediate_phys(
    inter: dict[str, float], inter_key: str, config: ScenarioConfig
) -> dict[str, float]:
    """Return ``inter`` with the PARENT class's ``phys_econ_*`` keys merged on.

    The ``gas_offer_net_revenue_margin`` coverage repair (miso-217; the gap
    measured at miso-215 §2). ``backcast_config`` merges ``phys_*`` onto exactly
    five gas classes, so a duty-split ``*_INTERMEDIATE`` curve carries none and
    :func:`gas_offer_margin_markup_mult` returns its rule-24 neutral 0.0 for
    every band — the mechanism skips the cohort and its offer stays in the fully
    fuel-scaled multiplier form the mechanism exists to replace.

    Gated on ``config.miso_intermediate_gas_offer_margin`` AND ``iso == "MISO"``
    (rule 25 [R-ISO-SCOPE] — PJM and CAISO share the gap in kind and it is their
    lanes' to adjudicate). No value is computed: the merged keys are the parent
    class's own already-registered, already-frozen p50s, so the repair carries
    ZERO free parameters (rule 21 [R-DOF]). A key the intermediate curve already
    carries is never overwritten, and a parent that carries none is a no-op.

    Returns a COPY whenever it merges — ``config.offer_curve_by_group`` is the
    recorded config and must never be mutated through this read path. Returns
    ``inter`` itself (same object) when the gate is off, so the flag-off path is
    byte-identical.
    """
    if not getattr(config, "miso_intermediate_gas_offer_margin", False):
        return inter
    if str(getattr(config, "iso", "ERCOT")) != "MISO":
        return inter
    parent = (getattr(config, "offer_curve_by_group", None) or {}).get(
        _INTERMEDIATE_PHYS_PARENT[inter_key]
    )
    if not parent:
        return inter
    add = {
        k: parent[k] for k in _INTERMEDIATE_PHYS_KEYS if k in parent and k not in inter
    }
    if not add:
        return inter
    return {**inter, **add}


#: Model offer-curve class -> the row it reads in the ISO's committed CAMPD
#: marginal-HR artifact (``<iso>_campd_marginal_hr_summary.csv``), for the
#: Route A REPLACE committed-band measured basis
#: (``ScenarioConfig.committed_band_measured_basis``). The artifact's class
#: vocabulary is the model's BASE classes, so:
#:
#: * every coal subclass reads the artifact's single coal-family row
#:   (:data:`~market_sim.config.plant_taxonomy.COAL_ARTIFACT_FAMILY`) -- the
#:   artifact carries exactly one (PJM n=65), which is why there is no
#:   per-supply value to select between (rule 21 [R-DOF]);
#: * a duty-split cohort reads its PARENT class's row, the same borrowing
#:   ``_INTERMEDIATE_PHYS_PARENT`` already registers for ``phys_*``.
#:
#: A class ABSENT from this map is NEUTRAL -- its registered ``committed``
#: multiplier is left untouched -- the rule-24 generic fallback, not a literal.
_COMMITTED_MEASURED_ROW: dict[str, str] = {
    "CC_REGULAR": "CC_REGULAR",
    "CC_INTERMEDIATE": "CC_REGULAR",
    "CC_CHP": "CC_CHP",
    "CT_CHP": "CT_CHP",
    "CT_PEAKER": "CT_PEAKER",
    "CT_INTERMEDIATE": "CT_PEAKER",
    "ST_GAS": "ST_GAS",
    "ST_GAS_INTERMEDIATE": "ST_GAS",
    # Model coal subclasses -> the artifact's coal-family row (COAL-SUB: the
    # bare ``COAL`` model class is deleted; the VALUE is the artifact's token).
    "COAL_BIT": COAL_ARTIFACT_FAMILY,
    "COAL_PRB": COAL_ARTIFACT_FAMILY,
    "COAL_LIGNITE": COAL_ARTIFACT_FAMILY,
    "COAL_WC": COAL_ARTIFACT_FAMILY,
}

#: The artifact column the ``committed`` band reads. Fixed by the convention
#: this repo already committed for this band (``pipeline/backcast_config``:
#: "committed -> avg_committed_p50"; every registered ``phys_committed`` key
#: reproduces this column byte for byte), so the operand is precedent, never a
#: choice made here.
_COMMITTED_MEASURED_COLUMN = "avg_committed_p50"


def committed_measured_basis(iso: str) -> dict[str, float]:
    """Return ``{model class: measured avg_committed_p50}`` for *iso*.

    Reads the committed CAMPD marginal-heat-rate summary
    (``data/raw/reference/<iso>_campd_marginal_hr_summary.csv``, written by
    ``scripts/data/derive_campd_marginal_hr.py``) and maps each row through
    :data:`_COMMITTED_MEASURED_ROW`.

    ``avg_committed_p50`` is the capacity-weighted median AVERAGE heat rate
    the class's units actually burn over their committed (min-load block)
    hours, as a multiple of the same class ``base_HR`` the offer curve
    multiplies against -- i.e. the measured physical basis of being on.

    Returns an empty dict when the ISO has no artifact, so the caller leaves
    every registered multiplier untouched.
    """
    import pandas as pd

    from market_sim.config.paths import REFERENCE_DIR

    path = REFERENCE_DIR / f"{iso.lower()}_campd_marginal_hr_summary.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if _COMMITTED_MEASURED_COLUMN not in df.columns:
        return {}
    by_row = {
        str(r["class"]).upper(): float(r[_COMMITTED_MEASURED_COLUMN])
        for _, r in df.iterrows()
        if not pd.isna(r[_COMMITTED_MEASURED_COLUMN])
    }
    return {
        cls: by_row[row]
        for cls, row in _COMMITTED_MEASURED_ROW.items()
        if row in by_row
    }


def apply_committed_band_measured_basis(
    offer_curve_by_group: dict[str, dict], iso: str
) -> tuple[dict[str, dict], list[tuple[str, float, float]]]:
    """Replace every covered class's ``committed`` multiplier with its measured basis.

    Half (a) of the Route A REPLACE mechanism
    (``ScenarioConfig.committed_band_measured_basis``; chartered by
    ``docs/PRECOMMIT-pjm-h5-coal-committed-charter-2026-09-13.md`` §4/§10a).
    Half (b) -- dropping the coal supply passthrough sigmoid from the same band
    (:func:`market_sim.data.fleet.campd_tranche_fuel_frac`) -- is not separable
    from this one: without it the effective basis becomes ``measured x
    passthrough`` and lands on the measurement in no year at all (charter §4),
    which is the stacking rule 19 ``[R-ONE-MECH]`` forbids.

    Applied to the RESOLVED curve -- after the base registry, any
    ``--offer-curve-json`` absolute override, any ``--offer-curve-delta-json``
    relative nudge and the ERCOT-111 econ floor -- so it replaces whatever the
    calibration path produced rather than a registry default, and the recorded
    ``run_config.json`` carries the value the LP actually solved on.

    NON-SELECTIVE by construction (rule 1 ``[R-STRUCT]``): every class the
    ISO's artifact covers is substituted, never the subset whose move helps a
    residual. A class outside :data:`_COMMITTED_MEASURED_ROW`, absent from the
    artifact, or whose ``committed`` band is missing or non-numeric is left
    untouched (the rule-24 neutral fallback); ``mustrun`` / ``econ*`` / ``peak``
    are never in scope.

    Args:
        offer_curve_by_group: The resolved ``{class: {band: multiplier}}`` curve.
        iso: ISO whose measured artifact supplies the basis.

    Returns:
        ``(curve, substituted)`` -- a new curve dict, and the list of
        ``(class, before, after)`` tuples actually replaced, for the caller to
        log. Returns the input object itself when the ISO has no artifact, so
        the no-artifact path is byte-identical.
    """
    measured = committed_measured_basis(iso)
    if not measured:
        return offer_curve_by_group, []
    out: dict[str, dict] = {}
    substituted: list[tuple[str, float, float]] = []
    for cls, bands in (offer_curve_by_group or {}).items():
        target = measured.get(str(cls).upper())
        if target is None or not isinstance(bands, dict) or "committed" not in bands:
            out[cls] = bands
            continue
        before = bands["committed"]
        if not isinstance(before, (int, float)) or isinstance(before, bool):
            out[cls] = bands
            continue
        out[cls] = {**bands, "committed": float(target)}
        if float(before) != float(target):
            substituted.append((str(cls), float(before), float(target)))
    return out, substituted


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

    Under ``config.miso_intermediate_gas_offer_margin`` (MISO-gated, default
    off) each of the three ``*_INTERMEDIATE`` curves comes back as a COPY
    carrying its PARENT class's registered ``phys_econ_low`` /
    ``phys_econ_high`` — see :func:`_with_intermediate_phys`. Without it those
    curves carry no ``phys_*`` keys at all, so
    :func:`gas_offer_margin_markup_mult` returns its rule-24 neutral 0.0 and
    ``gas_offer_net_revenue_margin`` silently skips the whole cohort.
    """
    from market_sim.data.fleet import (
        cc_intermediate_plants,
        ct_intermediate_plants,
        st_gas_intermediate_plants,
    )
    from market_sim.data.outages import ST_GAS_PEAKER_PLANTS

    curves = getattr(config, "offer_curve_by_group", None) or {}
    if is_coal_class(group):
        # COAL-SUB (2026-09-25): the coal bin's group IS its subclass, resolved
        # at load by the same coal_supply_class chain this lookup used to run
        # here, so the subclass curve is read directly. There is no generic
        # ``COAL`` curve to fall back to.
        return curves.get(group) or None
    if group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS:
        return None
    if group == "ST_GAS" and getattr(config, "st_gas_intermediate_split", False):
        iso = str(getattr(config, "iso", "ERCOT"))
        thr = float(getattr(config, "st_gas_intermediate_cf_threshold", 50.0))
        if int(plant_code) in st_gas_intermediate_plants(
            iso,
            thr,
            bool(getattr(config, "campd_per_unit_attribution", False)),
            bool(getattr(config, "campd_outage_merit_order_guard", False)),
        ):
            inter = curves.get("ST_GAS_INTERMEDIATE")
            if inter:
                return _with_intermediate_phys(inter, "ST_GAS_INTERMEDIATE", config)
    if group == "CT_PEAKER" and getattr(config, "ct_intermediate_split", False):
        iso = str(getattr(config, "iso", "ERCOT"))
        thr = float(getattr(config, "ct_intermediate_cf_threshold", 50.0))
        if int(plant_code) in ct_intermediate_plants(
            iso,
            thr,
            bool(getattr(config, "campd_per_unit_attribution", False)),
            bool(getattr(config, "campd_outage_merit_order_guard", False)),
        ):
            inter = curves.get("CT_INTERMEDIATE")
            if inter:
                return _with_intermediate_phys(inter, "CT_INTERMEDIATE", config)
    if group == "CC_REGULAR" and getattr(config, "cc_intermediate_split", False):
        iso = str(getattr(config, "iso", "ERCOT"))
        thr = float(getattr(config, "cc_intermediate_cf_threshold", 50.0))
        if int(plant_code) in cc_intermediate_plants(
            iso,
            thr,
            bool(getattr(config, "campd_per_unit_attribution", False)),
            bool(getattr(config, "campd_outage_merit_order_guard", False)),
        ):
            inter = curves.get("CC_INTERMEDIATE")
            if inter:
                return _with_intermediate_phys(inter, "CC_INTERMEDIATE", config)
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
    top_refine: bool = False,
) -> list[tuple[str, float, float, float, int, int, float]]:
    """Slice a rising economic ramp into flat sub-tranches.

    Returns ``(suffix, cap, heat_rate, vom_mult, min_run, min_down, startup)``
    tuples — by default ``n`` equal-capacity slices whose heat-rate multiplier
    rises from ``lo_mult`` toward ``pk_mult`` along
    ``mult(t) = lo + (pk - lo) * t**exp``, ``t = (k + 0.5)/n``. ``exp == 1`` is
    a straight (linear) ramp matching a thermal unit's gently-rising
    incremental heat rate; ``exp > 1`` is convex (cheap-bottom). When ``mid``
    is given it replaces the power shape with a two-segment piecewise-linear
    ramp anchored at the capacity midpoint: ``f(0) = 0``, ``f(0.5) = mid``,
    ``f(1) = 1`` (fraction of the lo->pk rise), so ``mid < 0.5`` keeps the
    middle of the curve cheap and concentrates the rise in the top slices — an
    independent shape control the single ``exp`` exponent cannot express. The
    slices carry no min-run or start cost — they are incremental output of an
    already-committed unit. Suffixes start with ``econ`` (``econc00`` …) so
    :func:`apply_commitment_with_coal_pin` couples them to the bin's
    committed tranche and shuts them down together.

    ``top_refine`` — SCHEME R1, the ercot-188 (c2) cliff-resolving refinement
    (``ScenarioConfig.ercot_econ_curve_top_refine``, default off and
    ERCOT-gated by its caller). ``mid`` shapes the ramp's PRICE axis; this
    refines its WIDTH axis. The equal-width form's finest expressible
    within-plant position is ``1/n`` of the ramp, so the model's supply-curve
    top is a 6-block approximation that CANNOT express a cliff — while
    reality's marginal price forms inside the top 0.24 % of the marginal
    resource's own submitted curve (``q_act`` p50 0.9976, ercot-180). Armed,
    the ramp's **top block is re-sliced ``n`` ways** and the body's ``n - 1``
    blocks are left expression-for-expression identical, giving ``2n - 1``
    slices and preserving total curve MW: at ``n = 6``, 11 slices whose top
    spans 2.778 % of the ramp.

    Rule 23 ``[R-DOF]``: the scheme adds **no numeric parameter**. Its split
    point is ``1 - 1/n``, the boundary the ramp is already sliced at, and its
    sub-slice count is the same ``n`` — both the registered
    ``offer_curve_smoothing_n``, so the shape follows ``n`` rather than
    carrying a free value of its own. Structural grounding, from measurements
    that predate the build and never from a residual
    (``docs/MEMO-ercot184-cliff-resolution-costing-2026-08-09.md`` §4.2/§4.3):
    the top block is the marginal one in 14 of the 33 econ-marginal object
    hours, more than any other slice, and is the ONLY block reaching the
    measured ladders' top decile — the econ ramp spans a median 61.8 % of its
    plant's stack, so its top slice reaches ladder position 0.9427 while every
    lower block sits below 0.9 by construction and can carry no cliff at all.

    **This is the one econ-curve control that moves P0**: the heat rates below
    are written into the BASE fleet, i.e. into the P0 objective, so a
    row-count change breaches the offer-surface family's P1-only
    ``mc_bid_adjust`` seam and forfeits its bit-identity proof. That cost was
    costed (memo §3.3) and accepted by the owner as the price of the
    structural fidelity; see
    ``docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md`` §3.
    """
    slice_cap = curve_cap / n
    # Slice geometry as (capacity, ramp-position midpoint) pairs. The default
    # branch reproduces the equal-width form expression for expression, so an
    # unarmed fleet is byte-identical rather than merely equal.
    if top_refine and n > 1:
        sub_cap = slice_cap / n
        geom = [(slice_cap, (k + 0.5) / n) for k in range(n - 1)]
        geom += [(sub_cap, (n - 1) / n + (j + 0.5) / (n * n)) for j in range(n)]
    else:
        geom = [(slice_cap, (k + 0.5) / n) for k in range(n)]
    steps: list[tuple[str, float, float, float, int, int, float]] = []
    for k, (cap, t) in enumerate(geom):
        if mid is not None:
            f = 2.0 * mid * t if t <= 0.5 else mid + (1.0 - mid) * (2.0 * t - 1.0)
        else:
            f = t**exp
        mult = lo_mult + (pk_mult - lo_mult) * f
        steps.append((f"econc{k:02d}", cap, base_hr * mult, 1.0, 0, 0, 0.0))
    return steps


# ---------------------------------------------------------------------------
# Gas-offer net-revenue margin (markup compression)
# ---------------------------------------------------------------------------

# Gas fuel types in scope for the net-revenue margin form (CAMPD tranche
# path). Coal keeps its own gas-keyed supply sigmoid (rule 19 — one mechanism
# per phenomenon); oil/other fuels never carry gas-band markups.
GAS_OFFER_MARGIN_FUELS: frozenset[str] = frozenset(
    {"gas_cc", "gas_cc_ccs", "gas_ct", "gas_st"}
)


def gas_offer_margin_markup_mult(
    suffix: str, tranche_mult: float, offer: dict[str, float]
) -> float:
    """Return one tranche's markup multiplier above its physical basis.

    The ``gas_offer_net_revenue_margin`` decomposition (design doc
    ``docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md``): the
    tranche's offer multiplier ``tranche_mult`` (its heat rate over the
    plant's base HR) splits into the band's MEASURED physical basis — the
    ``phys_*`` keys carried on the resolved offer-curve band dict — plus a
    markup, ``max(0, tranche_mult − phys)``, which
    :func:`apply_gas_offer_margin` converts to a fuel-invariant $/MWh margin
    at the ISO's delivered-gas anchor.

    Band resolution by tranche suffix (the ``bins_to_fleet`` vocabulary):

    * ``mustrun`` / ``sync`` — never marked up (0.0).
    * ``committed*`` (incl. ``committed_ramp_spread`` slices) —
      ``phys_committed``, the measured min-load block-average burn. A
      registered committed bid at or below the block average (price-taker
      cogen/steam bands) clips to 0 — no compression, no negative margin.
    * ``econlo`` / ``econhi`` / ``econcNN`` — ``phys_econ_low`` /
      ``phys_econ_high`` (measured incremental burn at the ramp endpoints);
      smoothing slices interpolate the physical basis at the slice's own
      position along the registered ``econ_low → econ_high`` ramp, so the
      markup fraction is consistent across the whole ramp.
    * ``peak*`` (incl. measured ``peak_ladder`` rungs) — ``phys_peak``.

    A band whose ``phys_*`` key is absent is NEUTRAL: ``phys = tranche_mult``
    ⇒ markup 0 ⇒ the tranche's offer is byte-identical at every gas price.
    That identity default is the rule-24 generic fallback (ISOs without a
    measured phys registry are untouched even with the flag armed), not a
    tunable literal.
    """
    if suffix.startswith("committed"):
        phys = offer.get("phys_committed")
        return max(0.0, tranche_mult - float(phys)) if phys is not None else 0.0
    if suffix.startswith("econ"):
        phys_lo = offer.get("phys_econ_low")
        phys_hi = offer.get("phys_econ_high")
        if phys_lo is None or phys_hi is None:
            return 0.0
        lo_m = float(offer["econ_low"])
        hi_m = float(offer["econ_high"])
        if suffix == "econlo":
            phys = float(phys_lo)
        elif suffix == "econhi":
            phys = float(phys_hi)
        else:
            # Smoothing slice (econcNN) or single flat econ tranche: place the
            # slice on the registered lo→hi ramp by its own multiplier and
            # interpolate the physical basis at the same position (f in [0,1]).
            if hi_m > lo_m:
                f = min(1.0, max(0.0, (tranche_mult - lo_m) / (hi_m - lo_m)))
            else:
                f = 0.5  # degenerate flat ramp: midpoint basis
            phys = float(phys_lo) + (float(phys_hi) - float(phys_lo)) * f
        return max(0.0, tranche_mult - phys)
    if suffix.startswith("peak"):
        phys = offer.get("phys_peak")
        return max(0.0, tranche_mult - float(phys)) if phys is not None else 0.0
    return 0.0


def apply_ercot_dam_hrmult_ep_rebasis(
    curve: dict[str, dict],
    year: int,
    offer_curve_deltas: dict | None,
    bands: "list[str] | None" = None,
) -> tuple[dict[str, dict], list[tuple[str, str, float, float]], float]:
    """Rebase the measured CC DAM band multipliers onto the EP dispatch basis.

    The ERCOT-118 mechanism (``ScenarioConfig.ercot_offer_hrmult_ep_rebasis``):
    the keeper's ``offer_curve_overrides`` bands (CC_REGULAR/CC_CHP
    committed/econ_low/econ_high/peak, the cconly lineage) were derived at
    ``HH_daily − 0.50`` pooled 2023-2025, while dispatch prices gas at the
    EP-anchored zonal level — the ERCOT-117-proven derivation⇄dispatch basis
    inconsistency. This replaces each of those bands with the PER-YEAR value
    of the committed EP-basis artifact
    (``offer_curve_dam_hrmults_ep_yearly.json``,
    ``derive_dam_offer_hrmults.py --ep-basis-yearly`` — rule-23 citation in
    its ``_provenance``) and re-applies the run's ``offer_curve_deltas`` for
    the named class/band on top, so the calibrated delta stays the markup and
    only the measured base under it moves. The conditional-surface
    ``peak_ladder`` rungs (uniform copies of the resolved peak, created by
    the ``ercot_offer_surface_conditional`` split before this runs) are
    rewritten to the rebased resolved peak; each rebased class additionally
    carries ``margin_anchor`` — the year's EP-anchored delivered annual mean
    from the artifact — so ``apply_gas_offer_margin`` prices ITS markups at
    the same basis its multipliers were identified on (the charter's
    anchor-consistency requirement; non-rebased classes keep the window
    anchor untouched).

    The ERCOT-119 leg-split (``ercot_offer_hrmult_ep_rebasis_bands``): with
    ``bands`` set, only the named artifact bands are rebased — every other
    band (above all the peak standing wall) keeps the run's resolved value,
    the ``peak_ladder`` re-stamp fires only when ``"peak"`` is in scope, and
    the anchor threading becomes band-scoped: each rebased band writes
    ``margin_anchor_<band>`` (resolved per tranche by
    :func:`band_margin_anchor`) instead of the class-wide ``margin_anchor``,
    so an un-rebased band's markup keeps the ISO window anchor its pooled
    multiplier was identified at. ``bands=None`` rebases every artifact band
    and writes the class-wide anchor — byte-identical to the ERCOT-118
    behaviour.

    Args:
        curve: The resolved ``offer_curve_by_group`` (post overrides, deltas
            and conditional split).
        year: Delivery year — selects the artifact's per-year table.
        offer_curve_deltas: The run's delta dict (may be ``None``); only the
            rebased class/band entries are re-applied here.
        bands: Band scope (``None`` = all artifact bands). Names must exist
            in the year's artifact tables.

    Returns:
        ``(new_curve, replaced, anchor)`` — the rebased curve, the
        ``(class, band, before, after)`` audit list, and the year's
        ``anchor_usd_mmbtu``.

    Raises:
        FileNotFoundError / KeyError: artifact or year table missing while
            the flag is armed (rule 25 — never a silent fallback).
        ValueError: a scoped band name absent from the year's artifact
            tables (rule 25 — a typo must never be a silent no-op).
    """
    import json as _json

    from market_sim.config import paths as _paths

    path = _paths.CALIBRATION_DIR / "offer_curve_dam_hrmults_ep_yearly.json"
    doc = _json.loads(path.read_text())
    try:
        table = doc[str(year)]
    except KeyError:
        raise KeyError(
            f"offer_curve_dam_hrmults_ep_yearly.json has no table for {year} "
            "— the EP rebasis is armed but underived for this year (rule 25: "
            "re-run derive_dam_offer_hrmults.py --ep-basis-yearly, never a "
            "silent fallback)"
        )
    anchor = float(table["anchor_usd_mmbtu"])
    if bands is not None:
        artifact_bands = {
            b
            for cls, cls_bands in table.items()
            if not cls.startswith("_") and cls != "anchor_usd_mmbtu"
            for b in cls_bands
        }
        unknown = sorted(set(bands) - artifact_bands)
        if unknown:
            raise ValueError(
                f"ercot_offer_hrmult_ep_rebasis_bands names {unknown} not in "
                f"the {year} artifact tables (have {sorted(artifact_bands)}) "
                "— a scoped band that matches nothing is a silent no-op "
                "(rule 25)"
            )
    deltas = offer_curve_deltas or {}
    merged = {cls: dict(cls_bands) for cls, cls_bands in curve.items()}
    replaced: list[tuple[str, str, float, float]] = []
    for cls, cls_bands in table.items():
        if cls.startswith("_") or cls == "anchor_usd_mmbtu":
            continue
        scoped = {b: v for b, v in cls_bands.items() if bands is None or b in bands}
        if not scoped:
            continue
        tgt = merged.setdefault(cls, {})
        cls_deltas = deltas.get(cls, {}) or {}
        for band, measured in scoped.items():
            before = float(tgt.get(band, float("nan")))
            after = float(measured) + float(cls_deltas.get(band, 0.0))
            tgt[band] = after
            replaced.append((cls, band, before, after))
        # The conditional split's uniform rungs carry the OLD resolved peak;
        # re-stamp them at the rebased one (shares untouched) — only when the
        # peak band itself is in scope (ERCOT-119: an out-of-scope peak keeps
        # its resolved rungs).
        if "peak_ladder" in tgt and "peak" in scoped:
            new_pk = float(tgt["peak"])
            tgt["peak_ladder"] = [[share, new_pk] for share, _ in tgt["peak_ladder"]]
        if bands is None:
            tgt["margin_anchor"] = anchor
        else:
            for band in scoped:
                tgt[f"margin_anchor_{band}"] = anchor
    return merged, replaced, anchor


def band_margin_anchor(suffix: str, offer: dict) -> float | None:
    """Resolve one tranche's margin anchor from its offer band dict.

    The ``apply_gas_offer_margin`` anchor override, band-scoped (ERCOT-119):
    a band rebased under a scope carries ``margin_anchor_<band>`` (its
    per-year EP identification anchor); a class rebased whole (ERCOT-118,
    ``bands=None``) carries the class-wide ``margin_anchor``. Band-scoped
    keys take precedence; the class-wide key is the fallback; ``None`` means
    the tranche prices its markup at the ISO window anchor (the un-rebased
    band's identification basis — ``constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO``).

    Suffix → band mapping mirrors :func:`gas_offer_margin_markup_mult`'s
    vocabulary: ``committed*`` → committed, ``econlo``/``econhi`` → the ramp
    endpoints, other ``econ*`` (smoothing slices / a flat econ tranche —
    whose physical basis interpolates along the lo→hi ramp) require BOTH
    endpoint anchors so the slice's (mult, anchor) pair never mixes bases,
    ``peak*`` (incl. ladder rungs) → peak.

    Args:
        suffix: The tranche suffix (``bins_to_fleet`` vocabulary).
        offer: The resolved offer-curve band dict for the tranche's class.

    Returns:
        The anchor ($/MMBtu) or ``None`` for the ISO window anchor.
    """
    if suffix.startswith("committed"):
        keyed = offer.get("margin_anchor_committed")
    elif suffix == "econlo":
        keyed = offer.get("margin_anchor_econ_low")
    elif suffix == "econhi":
        keyed = offer.get("margin_anchor_econ_high")
    elif suffix.startswith("econ"):
        lo = offer.get("margin_anchor_econ_low")
        hi = offer.get("margin_anchor_econ_high")
        keyed = lo if (lo is not None and hi is not None) else None
    elif suffix.startswith("peak"):
        keyed = offer.get("margin_anchor_peak")
    else:
        keyed = None
    if keyed is None:
        keyed = offer.get("margin_anchor")
    return float(keyed) if keyed is not None else None


def apply_gas_offer_margin(
    mc: "np.ndarray",
    generators: list,
    fuel_prices: "np.ndarray",
    config: ScenarioConfig,
) -> None:
    """Compress gas-band markups to fuel-invariant net-revenue margins.

    The mc-side half of ``gas_offer_net_revenue_margin`` (the tranche-side
    half is the ``offer_markup_hr`` computed in ``bins_to_fleet``): for every
    tranche carrying a positive markup heat rate, shift the assembled
    marginal cost from the fully fuel-scaled multiplier form to the
    anchored-margin form::

        mc[g, t] += offer_markup_hr[g] × (anchor − fuel_price[g, t])

    which is algebraically ``phys × HR_base × fuel(t) + markup_hr × anchor``
    — the physical burn keeps full delivered-fuel (and dual-fuel oil-parity
    switch) tracking while the markup becomes a fixed $/MWh margin identified
    at the training-window anchor. At ``fuel == anchor`` the adjustment is
    exactly zero (the registered multiplier form). Vectorized over the full
    ``(n_gen, T)`` block — no per-hour loop (rule 2). Applies to the BASE
    marginal cost, so P0 run discovery and the P1 bid see the same offer
    curve, exactly like the multiplier form it reprices.

    Must run AFTER ``apply_dual_fuel_pricing`` has finalized ``fuel_prices``
    (the compression keys on the post-switch delivered price) and after
    ``assemble_mc``. Mutates ``mc`` in place; no-op when the flag is off or
    no tranche carries a markup.

    Args:
        mc: ``(n_gen, T)`` marginal-cost array, modified in place.
        generators: Generator list aligned row-for-row with ``mc``
            (``offer_markup_hr`` per tranche, 0.0 outside the mechanism).
        fuel_prices: ``(n_gen, T)`` delivered fuel prices ($/MMBtu),
            post-overlay / post-dual-fuel.
        config: Scenario configuration supplying the gate
            (``gas_offer_net_revenue_margin``) and the anchor
            (``gas_offer_margin_anchor``).

    Raises:
        ValueError: flag armed without an anchor (rule 25 — the anchor must
            be resolved into the recorded config, never silently defaulted).
    """
    if not getattr(config, "gas_offer_net_revenue_margin", False):
        return
    anchor = getattr(config, "gas_offer_margin_anchor", None)
    if anchor is None:
        raise ValueError(
            "gas_offer_net_revenue_margin is armed but gas_offer_margin_anchor "
            "is unset; resolve it from constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO "
            "at config build (rule 25 — no silent fallback in the offer path)"
        )
    markup_hr = np.fromiter(
        (float(getattr(g, "offer_markup_hr", 0.0)) for g in generators),
        dtype=float,
        count=len(generators),
    )
    rows = np.nonzero(markup_hr > 0.0)[0]
    if rows.size == 0:
        return
    # Per-tranche anchor override (ERCOT-118 EP rebasis): a tranche whose
    # offer band carried ``margin_anchor`` (set on the rebased classes only)
    # prices its markup at ITS band's identification fuel — the year's
    # EP-anchored delivered mean the per-year multiplier was measured
    # against — instead of the ISO window anchor. Tranches without it keep
    # the config anchor bit-identically (the array holds the same float64).
    anchors = np.fromiter(
        (
            float(
                a
                if (a := getattr(g, "offer_margin_anchor", None)) is not None
                else anchor
            )
            for g in generators
        ),
        dtype=float,
        count=len(generators),
    )
    fp = np.asarray(fuel_prices, dtype=float)
    mc[rows, :] += markup_hr[rows, None] * (anchors[rows, None] - fp[rows, :])
    n_override = int(np.sum(anchors[rows] != float(anchor)))
    logger.info(
        "gas offer net-revenue margin: %d tranches compressed at anchor "
        "%.4f $/MMBtu (median fixed margin %.2f $/MWh, max %.2f)%s",
        rows.size,
        float(anchor),
        float(np.median(markup_hr[rows] * anchors[rows])),
        float((markup_hr[rows] * anchors[rows]).max()),
        (f"; {n_override} tranches on per-class EP anchors" if n_override else ""),
    )


#: Model plant group whose ``_committed`` tranche carries the measured CC
#: committed-block level. ERCOT-138's ``MODEL_CC_GROUPS`` is ``("CC_REGULAR",)``
#: — CC_CHP is reported there as a sensitivity and never pooled into the
#: measured CC control (its committed state is owned by its steam host, rule
#: 19), so this scope is exactly the measurement's population (rule 18: the
#: exclusion is the steam-host physics gate the gas commitment bridge uses, not
#: a class-name convenience).
CC_COMMITTED_OFFER_GROUPS: frozenset[str] = frozenset({"CC_REGULAR"})


def apply_cc_committed_offer_margin(
    mc: "np.ndarray",
    generators: list,
    fleet_arrays: "FleetArrays",
    config: ScenarioConfig,
) -> None:
    """Reprice the CC committed block to its MEASURED net-revenue offer level.

    The ERCOT-139 mechanism (``config.cc_committed_offer_margin``) — the gas-CC
    analogue of the coal min-load form
    (:func:`market_sim.data.fleet.legacy_bins.apply_coal_tranches`'s ERCOT-137
    branch), chartered by
    ``docs/DIAGNOSIS-ercot138-coal-gas-ranking-2026-07-29.md`` §6.

    ERCOT-138 measured the defect against ERCOT's own SCED TPO conduct: the
    model's CC committed/econ bands bid **+$2.8–6.6/MWh too DEAR** through the
    crossing band (coal's sit at −1.6..+3.9 and are exonerated), and §2.5
    located the residual in a **missing below-cost committed-CC block** — the
    model's cheapest CC band bottoms at $13.3 while the real fleet's median
    incremental MW is offered at $12.10 and its p25 at $8.38, below its own fuel
    cost. Each CC_REGULAR ``_committed*`` tranche is shifted from its band
    multiplier to the measured form::

        mc[g, t] = heat_rate[g] × (fuel(t) − anchor) + emis(t) + level

    implemented as ``mc[g, :] += level − heat_rate[g] × anchor − vom[g]`` on the
    assembled cost — the VOM already inside ``mc`` is folded into the measured
    all-in level, never double-counted. The block keeps FULL delivered-fuel
    tracking (physical burn at the tranche's own heat rate) while everything
    above fuel is the fuel-invariant measured margin; at ``fuel == anchor`` the
    bid is exactly ``level``, the measured RT curve bottom.

    The **anchor is the SHARED gas anchor** (``gas_offer_margin_anchor`` /
    ``constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO``), never a second constant, so
    the whole gas offer surface keeps one identification point that cannot
    drift against itself (rule 19 ``[R-ONE-MECH]`` bookkeeping). The margin is
    DERIVED, never fitted (rule 13)::

        margin = level − HR_tranche × anchor

    (``scripts/data/derive_cc_committed_offer_margin.py``, rule-23 frozen:
    level 10.354 $/MWh at anchor 2.2494 $/MMBtu, identified by removing the
    disclosure corpus's own measured fuel response; cross-subset dispersion
    ±42.98 % raw → ±6.47 % anchored, independent Min-Gen-Cost instrument 3.02 %
    away at 70–82 % coverage).

    **Rule 19 — this REPLACES, it does not stack.** The band multiplier
    (``offer_curve_by_group['CC_REGULAR']['committed']`` = 0.998 × base HR) is
    the sole owner of this row's price in the ERCOT-137 keeper:
    ``gas_offer_net_revenue_margin`` is provably inert on it (its markup is
    ``max(0, 0.998 − phys_committed 1.006)`` = 0; ERCOT-138 §J measures the
    delta at $0.00 at p25/p50), ``ercot_offer_surface_cleared_share`` scopes
    itself to ``econ*`` and cedes the committed block, and
    ``ercot_offer_surface_conditional`` owns ``peak*`` only. The
    ``econ_low``/``econ_high``/``peak`` bands and every other class are
    untouched — this is a bottom-of-curve mechanism, and ERCOT-138 §5.6's
    opposite-sign p90 finding is explicitly NOT its target.

    Applies to the BASE marginal cost, so P0 run discovery and the P1 bid see
    the same offer curve — exactly like the two margin forms it mirrors, and
    unlike the P1-only offer surfaces. Vectorized per row over the full hour
    block; no per-hour loop (rule 2). Mutates ``mc`` in place; no-op when the
    flag is off or no row is in scope.

    Args:
        mc: ``(n_gen, T)`` marginal-cost array, modified in place.
        generators: Generator list aligned row-for-row with ``mc``.
        fleet_arrays: The vectorized fleet, for per-tranche heat rate and VOM.
        config: Scenario configuration supplying the gate
            (``cc_committed_offer_margin``), the measured level
            (``cc_committed_offer_level``) and the shared delivered-gas anchor
            (``gas_offer_margin_anchor``).

    Raises:
        ValueError: flag armed without a resolved level or anchor (rule 25 —
            both must be resolved into the recorded config, never silently
            defaulted in the offer path).
    """
    if not getattr(config, "cc_committed_offer_margin", False):
        return
    level = getattr(config, "cc_committed_offer_level", None)
    anchor = getattr(config, "gas_offer_margin_anchor", None)
    if level is None or anchor is None:
        raise ValueError(
            "cc_committed_offer_margin is armed but cc_committed_offer_level / "
            "gas_offer_margin_anchor is unset; resolve them from "
            "constants.CC_COMMITTED_OFFER_LEVEL_BY_ISO / "
            "GAS_OFFER_MARGIN_ANCHOR_BY_ISO at config build (rule 25 — no "
            "silent fallback in the offer path). The anchor is SHARED with "
            "gas_offer_net_revenue_margin by design (rule 19): one "
            "identification point for the whole gas offer surface."
        )
    level, anchor = float(level), float(anchor)
    n_repriced = 0
    for g, gen in enumerate(generators):
        # Suffix vocabulary matches gas_offer_margin_markup_mult's
        # ``committed*``: the plain ``committed`` block plus the ``committedNN``
        # rising slices a non-zero ``committed_ramp_spread`` renders it as — all
        # of which are the measured block this level replaces.
        if not (
            getattr(gen, "is_campd_bin", False)
            and getattr(gen, "plant_group", None) in CC_COMMITTED_OFFER_GROUPS
            and str(gen.unit_id).rpartition("_")[2].startswith("committed")
        ):
            continue
        mc[g, :] += level - fleet_arrays.heat_rate[g] * anchor - fleet_arrays.vom[g]
        n_repriced += 1
    if n_repriced:
        logger.info(
            "CC committed-block offer margin: %d _committed tranche(s) repriced "
            "at level %.4f $/MWh / shared gas anchor %.4f $/MMBtu "
            "(fuel-invariant margin, full delivered-fuel tracking)",
            n_repriced,
            level,
            anchor,
        )


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
        pct_mr = chp_btm_pct(
            plant_code,
            group,
            iso=getattr(config, "iso", "ERCOT"),
            per_unit=bool(getattr(config, "campd_per_unit_attribution", False)),
            merit_guard=bool(getattr(config, "campd_outage_merit_order_guard", False)),
        )
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
        _dpk = cc_duct_peaking_pct(
            bool(getattr(config, "cc_duct_peaking_row_scoped", False))
        ).get(plant_code)
        if _dpk is not None:
            pct_peak = _dpk
    # RESERVE-DUTY split (cc_reserve_duty_split, nyiso-146): mirror of the
    # load-bearing bins_to_fleet override so the dashboard bands track the
    # dispatch — applied LAST, superseding every pct override above.
    if group == "CC_REGULAR" and getattr(config, "cc_reserve_duty_split", False):
        from market_sim.data.fleet import _reserve_duty_cohort

        if plant_code in _reserve_duty_cohort(str(getattr(config, "iso", "") or "")):
            pct_mc = 0.0
            pct_peak = 100.0 - pct_mr
    # CHP LAY-UP duty split (chp_layup_duty_split, nyiso-148): mirror of the
    # load-bearing bins_to_fleet override so the dashboard bands track the
    # dispatch — applied LAST, superseding every pct override above. Same
    # placement discipline as the reserve-duty block: nyiso-146b's first solve
    # was INERT because the frame seam was clobbered by pct_peaking /
    # cc_duct_peaking, and applying last is the fix.
    if getattr(config, "chp_layup_duty_split", False):
        from market_sim.data.fleet.campd_bins import _CHP_GROUPS, _chp_layup_cohort

        if group in _CHP_GROUPS and plant_code in _chp_layup_cohort(
            str(getattr(config, "iso", "") or "")
        ):
            pct_mc = 0.0
            pct_peak = 100.0 - pct_mr

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
    # CHP LAY-UP duty CURVE (chp_layup_duty_curve, nyiso-149): mirror of the
    # load-bearing bins_to_fleet CAP override so the dashboard bands track the
    # dispatch — at the cap level, after the residual, because the econ
    # residual would otherwise re-absorb the withheld share (same placement
    # discipline as the duty-split mirror above).
    if getattr(config, "chp_layup_duty_curve", False):
        from market_sim.data.fleet.campd_bins import (
            _CHP_GROUPS,
            _chp_duty_curve,
            _chp_layup_cohort,
        )

        _iso = str(getattr(config, "iso", "") or "")
        if group in _CHP_GROUPS and plant_code in _chp_layup_cohort(_iso):
            _duty = _chp_duty_curve(_iso).get(plant_code)
            if _duty is not None:
                # MW contract (PREREG-nyiso149 §7): the duty tuple IS the MW.
                committed_cap = 0.0
                peak_cap = min(_duty[1], grid_cap)
                econ_cap = min(_duty[0], grid_cap - peak_cap)
                grid_cap = committed_cap + peak_cap + econ_cap

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
        # (A CT_CHP limb stood here on the ct_*_hr_override triple. Deleted
        # 2026-08-03, rule 26 [R-DELETE], nyiso-114: it was unreachable on every
        # committed bundle in every ISO, because CT_CHP always resolves an offer
        # curve and so never enters this ``else``.)

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


#: Tranche-name prefixes that constitute a plant's BASE band — the block whose
#: offer level is set by the plant's own physical basis and is therefore NOT
#: repriced by the measured surface (:func:`apply_miso_offer_surface`). Every
#: other tranche of the same plant sits ABOVE the base in fill order.
_MISO_SURFACE_BASE_PREFIXES: tuple[str, ...] = (
    "committed",
    "commitcyc",
    "mustrun",
    "sync",
)

#: Parsed surface artifacts, keyed by resolved path (a solve reads one file).
_MISO_SURFACE_CACHE: dict[str, dict] = {}


def _load_miso_offer_surface(config: ScenarioConfig) -> dict:
    """Load and cache the derived MISO position-conditioned offer surface.

    Raises:
        ValueError: the gate is armed but the artifact is missing or malformed
            (rule 21 — no silent fallback in the offer path).
    """
    import json
    from pathlib import Path

    from market_sim.config import paths

    raw = getattr(config, "miso_offer_surface_path", None)
    path = (
        Path(raw)
        if raw
        else paths.REPO_ROOT
        / "data"
        / "raw"
        / "_validation-source"
        / "miso_offer_surface_positioned.json"
    )
    key = str(path)
    if key in _MISO_SURFACE_CACHE:
        return _MISO_SURFACE_CACHE[key]
    if not path.is_file():
        raise ValueError(
            f"miso_offer_surface_measured is armed but no artifact at {path} — "
            "derive it with scripts/data/derive_miso_offer_surface.py (rule 21: "
            "the offer path never falls back silently)"
        )
    art = json.loads(path.read_text())
    if "markets" not in art or "DA" not in art.get("markets", {}):
        raise ValueError(f"{path} is not a MISO offer-surface artifact")
    _MISO_SURFACE_CACHE[key] = art
    return art


def miso_surface_positions(generators: list) -> "np.ndarray":
    """Return each tranche's OWN-CURVE position midpoint, ``(n_gen,)`` in (0, 1].

    A plant's tranche rows are appended in FILL order (mustrun -> sync ->
    committed -> econ -> peak, ``data.fleet.assembly``), which is exactly the
    order they stack in that plant's own offer curve.  Position is the midpoint
    of each tranche's own MW span over the plant's total, so it is the same
    unit-relative coordinate the corpus side measures
    (``step_mw / ecomax_mw``) and it needs no class attribute — which is what
    makes a class-free surface constructible at MISO at all (miso-138 refuted
    the offer-side class bridge).

    Rows that carry no plant identity return 0.0 and are never repriced.
    """
    n = len(generators)
    pos = np.zeros(n, dtype=float)
    groups: dict[tuple, list[int]] = {}
    for i, g in enumerate(generators):
        code = getattr(g, "plant_code", None)
        if code is None:
            continue
        groups.setdefault((code, getattr(g, "plant_group", "")), []).append(i)
    for idx in groups.values():
        # NO SILENT DEFAULT (rule 21 [R-REGISTRY]). The tranche capacity field
        # is ``pmax_mw``; an earlier revision read ``pmax`` with a 0.0 fallback,
        # which made EVERY position 0.0 and silently collapsed the whole surface
        # onto its lowest position bin. A missing attribute is a wiring error
        # and must say so.
        caps = np.array(
            [float(getattr(generators[i], "pmax_mw")) for i in idx], dtype=float
        )
        total = float(caps.sum())
        if total <= 0.0:
            continue
        cum_before = np.concatenate(([0.0], np.cumsum(caps)[:-1]))
        pos[idx] = (cum_before + 0.5 * caps) / total
    return np.clip(pos, 0.0, 1.0)


def _miso_plant_base_row(generators: list) -> dict[int, int]:
    """Map each tranche row index -> its plant's BASE row index.

    The base row is the plant's FIRST tranche in fill order (``mustrun`` ->
    ``sync`` -> ``committed`` -> ...), which is the model-side analogue of the
    corpus's ``price_1``: the price at the bottom of that unit's own submitted
    curve.  Rows whose plant has no identifiable base are absent from the map
    and are never repriced.
    """
    order: dict[tuple, int] = {}
    out: dict[int, int] = {}
    for i, g in enumerate(generators):
        code = getattr(g, "plant_code", None)
        if code is None:
            continue
        key = (code, getattr(g, "plant_group", ""))
        if key not in order:
            order[key] = i
        out[i] = order[key]
    return out


def apply_miso_offer_surface(
    mc: "np.ndarray",
    generators: list,
    net_load: "np.ndarray",
    gas_series: "np.ndarray",
    config: ScenarioConfig,
) -> None:
    """Reprice MISO above-base gas tranches to the MEASURED own-curve rise.

    The miso-151 mechanism (``config.miso_offer_surface_measured``), chartered
    by the owner as queue item 9 and pre-registered in
    ``results/calibration/PREREG-miso151-measured-offer-surface-2026-08-11.md``.

    **SUBSUMES, never stacks** (rule 19 ``[R-ONE-MECH]``).  The rows it touches
    are exactly the rows :func:`apply_gas_offer_margin` gives a margin to —
    ``offer_markup_hr > 0`` — minus each plant's base band.  Each such tranche
    is re-priced onto its OWN plant's base row plus the measured rise::

        mc[g, t]  :=  mc[base(g), t]  +  Δ(p̄_g, state_bin(t), gas_bin(t))

    so a tranche is never priced by both mechanisms.  The row gate is the
    incumbent mechanism's own tag, not a class tuple (rule 18 ``[R-PHYSICS]``).

    **Why the whole rise is replaced, not just the fitted margin.**  The
    PREREG's first formula was ``mc += Δ − offer_markup_hr × anchor``, which
    removes only the CONDUCT half of the model's own rise over its base band
    while adding the real book's TOTAL rise — double-counting the model's
    physical heat-rate rise.  The corpus cannot separate a real unit's physical
    rise from its conduct rise (it publishes no heat rates), so the identifiable
    quantity is the total OFFER rise, and the like-for-like transfer is
    offer-rise onto offer-rise.  Both sides' physical component sits inside
    their own rise, and the model's base level — the part that carries its
    physical/fuel basis — is untouched.  Corrected before any adjudicating
    statistic; see the PREREG's dated §4.2 amendment.

    **SHAPE, never LEVEL.**  Δ is a within-unit, within-hour price DIFFERENCE
    measured on MISO's submitted book, so a constant shift of a real unit's
    whole curve cancels exactly; the model's price LEVEL stays on its own
    physical/fuel basis.  This is load-bearing: miso-145 measured MISO's real
    book as $8–15/MWh CHEAPER than the model at matched position, so a level
    transfer would move C3a the WRONG WAY.

    **Conditioning.**  The hour's state bin is the percentile rank of ``net_load``
    WITHIN THE SOLVE'S OWN YEAR at the artifact's percentile cut points — a
    relative, unit-free coordinate, so it transfers to a forecast year whose
    load level differs from the training window.  The gas bin uses the
    artifact's ABSOLUTE $/MMBtu edges, because a delivered gas price is directly
    comparable across years in a way a load level is not.

    Vectorized over the whole ``(n_gen, T)`` block (rule 2 ``[R-VECTOR]``);
    applied to the BASE marginal cost so P0 and P1 see the same curve, exactly
    like the mechanism it replaces.  Mutates ``mc`` in place; no-op when the
    gate is off or no row qualifies.

    Args:
        mc: ``(n_gen, T)`` marginal-cost array, modified in place.
        generators: Generator list aligned row-for-row with ``mc``.
        net_load: ``(T,)`` LP-served net load (demand − wind − solar), MW.
        gas_series: ``(T,)`` delivered gas price, $/MMBtu.
        config: Scenario configuration supplying the gate, the artifact path
            and the frozen bin geometries.

    Raises:
        ValueError: gate armed with a missing/malformed artifact, or with an
            anchor unset while a repriced row still carries a markup.
    """
    if not getattr(config, "miso_offer_surface_measured", False):
        return
    if str(getattr(config, "iso", "")).upper() != "MISO":
        return  # rule 25 [R-ISO-SCOPE]: this surface is MISO's and never transfers

    art = _load_miso_offer_surface(config)
    ladder = np.asarray(
        art["markets"]["DA"]["ladder"], dtype=float
    )  # (gas, state, pos, 3)
    delta_grid = ladder[..., 1]
    gas_edges = np.asarray(
        art["_provenance"]["gas_bin_edges_usd_per_mmbtu"], dtype=float
    )
    pcts = np.asarray(config.miso_offer_surface_netload_pcts, dtype=float)
    pos_edges = np.asarray(config.miso_offer_surface_position_bins, dtype=float)
    if delta_grid.shape != (gas_edges.size + 1, pcts.size + 1, pos_edges.size - 1):
        raise ValueError(
            f"MISO offer surface geometry {delta_grid.shape} does not match the "
            f"configured bins (gas {gas_edges.size + 1}, state {pcts.size + 1}, "
            f"position {pos_edges.size - 1}) — re-derive the artifact"
        )

    markup_hr = np.fromiter(
        (float(getattr(g, "offer_markup_hr", 0.0)) for g in generators),
        dtype=float,
        count=len(generators),
    )
    is_base = np.fromiter(
        (
            str(getattr(g, "bin_label", ""))
            .rsplit("_", 1)[-1]
            .startswith(_MISO_SURFACE_BASE_PREFIXES)
            for g in generators
        ),
        dtype=bool,
        count=len(generators),
    )
    rows = np.nonzero((markup_hr > 0.0) & (~is_base))[0]
    if rows.size == 0:
        logger.info("MISO measured offer surface: no above-base markup rows; inert")
        return

    # The surface SUBSUMES gas_offer_net_revenue_margin, so that mechanism must
    # actually be the one setting these rows' margins — otherwise "replace" has
    # no defined referent and the two could silently be describing different
    # scopes (rule 19 [R-ONE-MECH], rule 21 [R-REGISTRY]: no silent fallback).
    if getattr(config, "gas_offer_margin_anchor", None) is None:
        raise ValueError(
            "miso_offer_surface_measured is armed but gas_offer_margin_anchor is "
            "unset; the surface REPLACES that mechanism's margin on exactly the "
            "rows it tags, so it must be armed (rule 19 — replace, never stack)"
        )

    # Each target's own plant base row (the plant's FIRST tranche in fill
    # order) — the model-side analogue of the corpus's ``price_1``.
    base_of = _miso_plant_base_row(generators)
    base_rows = np.array([base_of.get(int(i), -1) for i in rows], dtype=int)
    ok = base_rows >= 0
    rows, base_rows = rows[ok], base_rows[ok]
    if rows.size == 0:
        logger.info("MISO measured offer surface: no target has a base row; inert")
        return

    pos = miso_surface_positions(generators)[rows]
    # A POSITION-conditioned surface whose positions are all identical is not
    # position-conditioned at all — it silently collapses onto one bin and
    # reprices the whole fleet at that bin's value. That is exactly what a
    # wrong capacity-attribute name did before this guard existed, and the run
    # LOOKED healthy: 552 tranches repriced, plausible $/MWh in the log, and
    # only ``position p50 0.000`` betrayed it. Fail loudly instead.
    if float(np.ptp(pos)) <= 0.0:
        raise ValueError(
            f"MISO offer surface: all {rows.size} target tranches resolved to "
            f"position {float(pos[0]):.4f} — the position coordinate is not "
            "varying, so the surface would apply one bin to the whole fleet. "
            "This is a wiring error, not a degenerate fleet."
        )
    pos_bin = np.clip(
        np.searchsorted(pos_edges[1:-1], pos, side="right"), 0, pos_edges.size - 2
    )

    nl = np.asarray(net_load, dtype=float)
    state_edges = np.quantile(nl, pcts)
    state_bin = np.searchsorted(state_edges, nl, side="right")
    gas_bin = np.searchsorted(
        gas_edges, np.asarray(gas_series, dtype=float), side="right"
    )

    # (n_rows, T) measured own-curve rise.
    measured = delta_grid[gas_bin[None, :], state_bin[None, :], pos_bin[:, None]]
    # RHS fancy-indexing copies before the write, and no base row is ever a
    # target, so this cannot read a partially-updated column.
    was = mc[rows, :]
    mc[rows, :] = mc[base_rows, :] + measured

    logger.info(
        "MISO measured offer surface: %d above-base tranches repriced onto their "
        "own plant base (median measured rise %.2f $/MWh; median model rise "
        "replaced %.2f; median net mc move %+.2f; position p50 %.3f)",
        rows.size,
        float(np.median(measured)),
        float(np.median(was - mc[base_rows, :])),
        float(np.median(mc[rows, :] - was)),
        float(np.median(pos)),
    )


#: Parsed miso-180 spread artifact, keyed by resolved path (a solve reads one).
_MISO_SPREAD_CACHE: dict[str, dict] = {}

#: The miso-180 affected-stack selectors — VERBATIM the frozen probe scope
#: (PREREG-miso180 §3 / PREREG-miso179 §2: econ/peak tranches of the
#: offer-curve classes; committed/mustrun/sync bands are the model's analogue
#: of the book's self-scheduled/must-run mass and are never repriced).
_MISO_SPREAD_SUFFIX = re.compile(r"_(econ\w*|peak\w*)$")
_MISO_SPREAD_CLASS = re.compile(r"^(CC_|CT_|ST_GAS|COAL)")


def _load_miso_spread_vector() -> "tuple[np.ndarray, np.ndarray]":
    """Load (grid, pooled vector) from the committed miso-179 artifact.

    Hard-errors when the artifact is absent or its sha256 differs from the
    pinned ``MISO_OFFER_SPREAD_ARTIFACT_SHA256`` — the graft must never
    consume a drifted vector (rules 21/24: the offer path never falls back
    silently and the parameter surface is pinned, not merely pathed).
    """
    import hashlib
    import json

    from market_sim.config import paths

    path = (
        paths.REPO_ROOT
        / "data"
        / "raw"
        / "_validation-source"
        / "miso_offer_level_dispersion.json"
    )
    key = str(path)
    if key in _MISO_SPREAD_CACHE:
        c = _MISO_SPREAD_CACHE[key]
        return c["grid"], c["vec"]
    if not path.is_file():
        raise ValueError(
            f"miso_offer_spread_anchored is armed but no artifact at {path} — "
            "the committed miso-179 identification vector is required (rule 21: "
            "the offer path never falls back silently)"
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != MISO_OFFER_SPREAD_ARTIFACT_SHA256:
        raise ValueError(
            f"miso_offer_spread_anchored: artifact sha256 {digest} != pinned "
            f"{MISO_OFFER_SPREAD_ARTIFACT_SHA256} — the vector drifted; "
            "re-identify the anchor and re-pin deliberately (rule 23: a "
            "re-derive commit cites the data change), never consume silently"
        )
    art = json.loads(raw)
    grid = np.asarray(art["quantile_grid"], dtype=float)
    vec = np.asarray(art["pooled"]["quantiles_mmbtu_per_mwh"], dtype=float)
    if grid.size != vec.size or not np.all(np.diff(grid) > 0):
        raise ValueError(f"{path} is not a valid miso-179 dispersion artifact")
    _MISO_SPREAD_CACHE[key] = {"grid": grid, "vec": vec}
    return grid, vec


def _miso_spread_gref_monthly(year: int) -> "np.ndarray":
    """(12,) delivered-gas reference: Henry Hub monthly + measured MISO basis.

    The miso-156 PRIMARY construction the identification normalized by
    (PREREG-miso180 §3: using a different reference at apply time would
    smuggle in a level adder). Hard-errors on a missing month — a silent gap
    would move offers without a cited data change (rule 23). A forecast year
    with no measured rows errors here by design: wiring the forward gas
    trajectory through this seam is a deliberate future change, never a
    silent fallback.
    """
    import pandas as pd

    from market_sim.config import paths

    hh = pd.read_csv(paths.REPO_ROOT / "data/raw/gas-prices/henry_hub_monthly.csv")
    hh = hh[hh["year"] == year].set_index("month")["price_usd_mmbtu"]
    bs = pd.read_csv(paths.REPO_ROOT / "data/raw/gas_basis_by_iso_month.csv")
    bs = bs[(bs["iso"] == "MISO") & (bs["year"] == year)].set_index("month")
    out = np.full(12, np.nan)
    for m in range(1, 13):
        if m in hh.index and m in bs.index:
            out[m - 1] = float(hh.loc[m]) + float(bs.loc[m, "basis_usd_mmbtu"])
    if not np.all(np.isfinite(out)):
        missing = [m + 1 for m in range(12) if not np.isfinite(out[m])]
        raise ValueError(
            f"miso_offer_spread_anchored: G_ref missing for {year} months "
            f"{missing} (Henry Hub monthly + measured MISO hub basis)"
        )
    return out


def apply_miso_offer_spread_anchored(
    mc: "np.ndarray",
    generators: list,
    fleet_arrays: "FleetArrays",
    config: ScenarioConfig,
    year: int,
) -> None:
    """Graft the measured above-anchor offer rise onto MISO's affected stack.

    The miso-180 mechanism (``config.miso_offer_spread_anchored``), the
    owner-chartered D-1b successor of the miso-179 REFUTED level-replacement
    form, pre-registered in
    ``results/calibration/PREREG-miso180-anchored-spread-2026-08-23.md``.

    **SPREAD only, never LEVEL.** miso-179 measured the model +$15/MWh OVER
    the eligible book at the median rank and UNDER only in the top decile
    (p95 −$42, p99 −$108 on the binding H\\* window) — a top-decile tail
    steepening, not an across-the-board dispersion deficit. The graft
    therefore transfers ONLY the measured above-anchor RISE ``Q(r) − Q(a)``
    of the committed pooled BOOK-ELIG vector, pinned to the model's OWN
    anchor level, so the body the model already over-prices is untouched by
    construction (the miso-151 shape-only admissibility pattern at
    across-unit grain).

    **The rule, verbatim from the PREREG (§3).** Within each calendar month
    ``m``, the affected tranches (econ/peak tranches of the offer-curve
    classes — the ``_MISO_SPREAD_*`` selectors) are ranked by their
    month-mean base marginal cost, capacity-weighted (``pmax``), stable
    sort, each tranche at its mass MIDPOINT rank ``r_g``. With ``a`` the
    ex-ante-identified anchor rank (``MISO_OFFER_SPREAD_ANCHOR_RANK``),
    ``A_m`` the stack's own capacity-weighted a-quantile of month-m mc (the
    miso-151/179 step-function estimator), ``Q̂`` monotone interpolation of
    the committed vector, and ``G_ref(m)`` the delivered-gas monthly
    reference, every tranche with ``r_g > a`` is floored RAISE-ONLY::

        mc[g, t in m] = max(mc[g, t], A_m + (Q̂(r_g) − Q̂(a)) × G_ref(m))

    and tranches at or below the anchor are untouched. The graft is
    rank-preserving inside the affected stack (the max of two
    monotone-in-rank curves) and applies to the BASE cost so P0 run
    discovery and the P1 bid see the same curve; the P1 startup-amortization
    markup stays on top unchanged (the measured levels are ENERGY offers —
    MISO clears startup/no-load as separate components, rule 19).

    Rule 13: the vector and anchor are frozen measured conduct parameters
    (identified with zero LMP/residual anywhere in the path); the ranks,
    the anchor level ``A_m`` and ``G_ref`` regenerate for a forward year
    from the model's own fleet and gas trajectory. Rule 25: MISO-only, the
    verdict never transfers. Mutates ``mc`` in place; no-op when the gate is
    off or the ISO is not MISO.

    Args:
        mc: ``(n_gen, T)`` base marginal-cost array, modified in place.
        generators: Generator list aligned row-for-row with ``mc``.
        fleet_arrays: Vectorized fleet (``pmax`` supplies the rank weights —
            the identification's own weighting).
        config: Scenario configuration supplying the gate and ISO.
        year: Delivery year (calendar for the month index and ``G_ref``).

    Raises:
        ValueError: armed with a missing/drifted artifact, a missing G_ref
            month, or zero affected tranches (a wiring error, never inert).
    """
    if not getattr(config, "miso_offer_spread_anchored", False):
        return
    if str(getattr(config, "iso", "")).upper() != "MISO":
        return  # rule 25 [R-ISO-SCOPE]: this graft is MISO's and never transfers

    a = float(MISO_OFFER_SPREAD_ANCHOR_RANK)
    grid, vec = _load_miso_spread_vector()
    q_a = float(np.interp(a, grid, vec))

    ids = np.array([str(getattr(g, "unit_id", "")) for g in generators])
    cls = np.array(
        [
            str(
                getattr(g, "plant_group", None)
                or getattr(g, "efficiency_bin", None)
                or ""
            )
            for g in generators
        ]
    )
    aff = np.nonzero(
        np.array([bool(_MISO_SPREAD_SUFFIX.search(u)) for u in ids])
        & np.array([bool(_MISO_SPREAD_CLASS.match(c)) for c in cls])
    )[0]
    if aff.size == 0:
        raise ValueError(
            "miso_offer_spread_anchored is armed but the fleet carries zero "
            "affected econ/peak tranches — a wiring error, never a silent no-op"
        )

    import pandas as pd

    T = int(mc.shape[1])
    months = pd.date_range(f"{year}-01-01", periods=T, freq="h").month.to_numpy()
    pmax_aff = np.asarray(fleet_arrays.pmax, dtype=float)[aff]
    if float(pmax_aff.sum()) <= 0.0:
        raise ValueError(
            "miso_offer_spread_anchored: affected tranches carry zero pmax mass"
        )
    gref = _miso_spread_gref_monthly(year)

    n_raised = 0
    max_target = 0.0
    for m in np.unique(months):
        hrs = np.nonzero(months == m)[0]
        mc_m = mc[np.ix_(aff, hrs)].mean(axis=1)
        order = np.argsort(mc_m, kind="stable")
        w_sorted = pmax_aff[order]
        cum = np.cumsum(w_sorted)
        w_total = float(cum[-1])
        # Mass-midpoint rank per tranche (PREREG §3 — declared deliberately:
        # the spread form needs a threshold trigger, and the mass centroid is
        # the estimator-consistent inversion point).
        mid_sorted = (cum - 0.5 * w_sorted) / w_total
        r_g = np.empty_like(mid_sorted)
        r_g[order] = mid_sorted
        # A_m: the stack's own a-quantile, the miso-151/179 step-function
        # estimator (sort, cumulative weight, searchsorted).
        idx = int(np.clip(np.searchsorted(cum / w_total, a), 0, mc_m.size - 1))
        a_m = float(mc_m[order][idx])
        above = r_g > a
        if not above.any():
            continue
        rise = (np.interp(r_g[above], grid, vec) - q_a) * float(gref[int(m) - 1])
        target = a_m + np.clip(rise, 0.0, None)  # raise-only by construction
        rows = aff[above]
        block = mc[np.ix_(rows, hrs)]
        raised = np.maximum(block, target[:, None])
        n_raised += int(np.any(raised > block, axis=1).sum())
        mc[np.ix_(rows, hrs)] = raised
        max_target = max(max_target, float(target.max()))

    logger.info(
        "MISO anchored spread graft (miso-180): %d affected tranches, anchor "
        "r=%.3f (Q_a %.3f MMBtu/MWh), %d tranche-months raised, max graft "
        "target %.2f $/MWh, year %d",
        aff.size,
        a,
        q_a,
        n_raised,
        max_target,
        year,
    )
