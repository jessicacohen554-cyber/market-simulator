"""Regression tripwires for the persisted-artifact surfaces every later
refactor depends on.

Three independent guards:

* **Pickle-borne class identity.** The committed ``p2_state`` pickles bind a
  fixed set of classes to their exact module paths. Unpickling resolves a class
  by its ``__module__``/qualname, so if a split moves any of these classes to a
  different module (or a facade re-exports it without defining it physically at
  the frozen path, changing ``__module__``), every committed pickle silently
  fails to load. This test asserts each class both *resolves* at its frozen path
  and reports that path as its ``__module__``.
* **``ScenarioConfig`` cache-key stability.** ``cache_key()`` hashes
  ``asdict(self)``; any change to field names/defaults that reaches the hash
  orphans every on-disk cache and breaks keeper reproducibility. Pinned to a
  literal so a drift is caught here, not in a stale-cache mystery months later.
* **No module-level import cycles.** The package breaks would-be cycles with
  lazy (in-function) imports; a cycle introduced at module scope is an import-
  time crash waiting for the wrong import order. An AST walk asserts the
  module-level import graph of ``src/market_sim`` is acyclic.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path

import pytest

from market_sim.config.scenarios import ScenarioConfig
from tests.helpers import REPO_ROOT

# The classes bound by the committed p2_state pickles to their exact module
# paths (refactor-consolidation plan §1 "Pickle identity is frozen"). Kept in
# lockstep with docs/refactor-consolidation-plan-2026-07.md.
FROZEN_PICKLE_PATHS: dict[str, list[str]] = {
    "market_sim.data.fleet": ["Generator", "FleetArrays"],
    "market_sim.model.dispatch": ["DispatchResult"],
    "market_sim.config.scenarios": ["ScenarioConfig"],
    "market_sim.model.storage": ["StorageUnit"],
    "market_sim.results.outputs": ["FleetContext"],
    "market_sim.config.iso_configs": ["TransferLink"],
}

# ScenarioConfig().cache_key() with the current frozen field set/defaults.
# Recompute intentionally (never to "fix" a failure): a change here means a
# field that reaches asdict() moved, which orphans every on-disk cache.
#
# 2026-07-20 advance 2a1cb71048210ebf -> edbc1b103207170a. Investigated (field-set
# diff of ScenarioConfig between baseline 0ba2bb0 and HEAD) and every difference is
# traceable to four merged, attributed FF/calibration commits — no removed/renamed
# field, and the ONLY pre-existing-field default change is the intended, owner-
# signed-off FF-2C flip:
#   - 9752a64 (ERCOT-91): +gas_st_drag_seasonal (=False), +gas_st_drag_seasonal_path
#     (=None) — new default-off fields.
#   - 0cc47af (caiso-104): +caiso_charge_allocation_schedule (=False) — new
#     default-off field.
#   - 85c261f (ERCOT-89): +ercot_shoulder_online_span (=False),
#     +ercot_shoulder_online_span_path (=None) — new default-off fields.
#   - dbbae9c (FF-2C): capacity_market_clearing_by_iso default FLIPPED None ->
#     {"PJM","MISO","CAISO","NEISO": True} (NOT a new field — a pre-existing
#     field's default changed). It is not in _CACHE_KEY_OPTIONAL_FIELDS and the
#     default config is mode="forecast" (no __post_init__ backcast coercion), so
#     the dict enters the hash and is the dominant contributor to this change.
#
# 2026-07-23 gas-offer net-revenue margin mechanism (commit d536e7d,
# docs/handoffs/gas-offer-net-revenue-margin-design-2026-07.md) added two
# default-off fields, +gas_offer_net_revenue_margin (=False) and
# +gas_offer_margin_anchor (=None). Both are now registered in
# _CACHE_KEY_OPTIONAL_FIELDS (cache-neutral at their defaults), so the default
# cache_key stays pinned at edbc1b103207170a — no advance. An armed gas-offer run
# (flag True, or a set anchor) still gets a distinct key.
#
# 2026-07-27 CACHE-EPOCH BUMP edbc1b103207170a -> 603c2498bf71d21d. Authorized by
# the owner (session sign-off, cache-key path-portability task) — NOT a silenced
# failure. Cause: six fields default to checkout-ABSOLUTE paths
# (campd_bins_path, plant_registry_path, plant_emission_rates_path,
# plant_emission_rates_v2_path, control_retrofit_path, and
# cc_capacity_reconcile_path via __post_init__), so the old key encoded WHERE the
# checkout lived: /home/user/market-simulator hashed to edbc1b103207170a but
# /home/runner/work/market-simulator/market-simulator hashed to 329093815fa58f5b,
# failing this pin on EVERY GitHub-hosted run of every branch (and with it the
# blocking persisted-identity step of refactor-guards). cache_key() now folds
# repo-root/DATA_ROOT-relative paths to sentinels in the hashed payload only
# (scenarios.py::_normalize_cache_key_paths); no field value, name or default
# changed. The new key is byte-identical on a session container and a hosted
# runner. This bump orphans every on-disk results cache (a re-key, not a
# behavior change — the solve path is untouched).
#
# ADVANCED 2026-09-02, 603c2498bf71d21d -> cedadc285f8603b9 — owner-authorized
# in the capx D41 session sitting (the lane's charter said "STOP and report the
# blast radius first" if the repair re-keyed configs; it does, it was reported,
# and the owner answered "land it, advance the pins"). A genuine key ADVANCE,
# not a re-baseline to silence red.
#
# CAUSE. Two CCS-retrofit fixed-cost defaults are re-identified onto the model's
# own NREL ATB 2024 (2026$) basis, repairing the defect
# `docs/handoffs/FINDING-capx-d30-45q-pace-2026-09-02.md` §5 rows 6-7
# adjudicated:
#   * `fixed_om_gas_cc_ccs` 25.0 -> 65.0 $/kW-yr — a "host CC + capture island"
#     figure that had sat BELOW its own host (`fixed_om_gas_cc` 30.0) ever since
#     the G-32 ATB flip raised the host 12 -> 30 and left this field behind, so
#     the retrofit screen's dFOM was -$5,000/MW-yr (a saving) instead of the ATB
#     capture-island increment +$35,000/MW-yr.
#   * `ccs_retrofit_capex_kw` 900.0 -> 1521.4 $/kW — `needs-citation`, no stated
#     dollar-year, and 59 % of the capture-island increment the model's own
#     new-build CCS carries (3104.7 - 1583.3, ATB 2024 2026$).
# NEITHER field is in `_CACHE_KEY_OPTIONAL_FIELDS`, so both are hashed at every
# value and a value change moves the key unconditionally — registration is not
# an available remedy here and re-pinning IS the sanctioned route (the "do NOT
# re-pin" rule targets an unregistered NEW FIELD that is cache-neutral at its
# default, which this is not). Same shape as G-32 itself, which moved this pin
# when it flipped `fixed_om_gas_cc` 12 -> 30.
#
# WHAT THIS COSTS, EXACTLY. A one-time cache MISS per forecast config: every
# pre-2026-09-02 `results/<ISO>/<key>/` bundle at the old key is now unaddressed
# and the next run re-solves. Behaviour moves ONLY in forecast years >=
# `ccs_retrofit_available_year` (2028) — which is the repair, measured at screen
# grain in `docs/handoffs/FINDING-capx-d41-ccs-fixedcost-2026-09-02.md`. The two
# fields have exactly two consumers, both inside forecast-mode capacity
# evolution (`capacity_evolution/ccs.py::apply_ccs_retrofit` and the
# `_THERMAL_FOM` lookup in `capacity_evolution/retirements.py`, which reaches
# `fixed_om_gas_cc_ccs` only for a `gas_cc_ccs` unit). No committed keeper,
# sidecar, determination or dashboard row is a cache lookup, so none moves.
# Full record: the cache-epoch ledger in `src/market_sim/results/cache.py`,
# epoch 2026-09-02.
#
# ADVANCED 2026-09-03, cedadc285f8603b9 -> 4c6b03ae098b6e3e — capx D44
# executing OWNER RULING Q30 (director sitting r#31, 2026-09-02: "ARM AS
# DEFAULT"). A genuine, DECLARED advance, not a re-baseline to silence red.
#
# CAUSE. `ScenarioConfig.fossil_announced_exits_enabled` flips default
# False -> True: an owner's filed EIA-860 Schedule-3 fossil retirement date is
# now honored as an exogenous, vintage-gated step-1 input, with the economic
# screen running on the residual (undated) fleet. Evidence:
# `docs/handoffs/FINDING-capx-d42-fossil-dates-ab-2026-09-02.md` (MISO T1-H
# recall 5/19 -> 16/19, zero screen displacement, per-unit published deferral
# counters); execution record `FINDING-capx-d44-fossil-dates-arm-2026-09-03.md`.
#
# WHY THE KEY MOVES, AND WHY THAT IS THE DESIGN. The field IS a
# `_CACHE_KEY_OPTIONAL_FIELDS` member, so this looks at first glance like the
# "do NOT re-pin" case — it is the opposite. Since capx D24-R option (b'-1),
# `cache_key()` drops a registered field at its FROZEN declaration in
# `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` ("False", left untouched), never at the
# live default. A post-flip default config therefore no longer equals the drop
# value, ENTERS the hash and takes its own key — which is precisely what (b'-1)
# was landed to guarantee (D24 §4.1/§4.2: before it, the post-flip run silently
# re-used the pre-flip bundle at an unmoved key). The flip is DECLARED in
# `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` — its first entry — so the
# registration guard's check 3 passes on the declaration, not on silence.
#
# WHAT THIS COSTS, EXACTLY. A one-time cache MISS per forecast config: every
# pre-2026-09-03 `results/<ISO>/<key>/` forecast bundle at cedadc285f8603b9 (or
# any key derived from the unarmed default) is unaddressed by a default config
# and the next run re-solves. Nothing can be mis-served — the key moved. The
# useful inverse is intact and MEASURED this session: an explicit
# `fossil_announced_exits_enabled=False` still equals the frozen declaration,
# is still dropped, and still hashes cedadc285f8603b9, so a control arm pinned
# to the superseded posture keeps its pre-flip key and its bundle.
# Forecast bundles solved at the pre-flip default now record a SUPERSEDED
# posture; per ruling Q30 that staleness joins the director's batched
# post-repair re-measure decision (no re-solve was run or owed by D44).
#
# ADVANCED 2026-09-05, 4c6b03ae098b6e3e -> e5ecd4105ada3e58 — capx D60
# executing OWNER RULING Q42 (director sitting r#37, 2026-09-05: "ARM the CCS
# capex default"). The SECOND declared (b'-1) flip, mechanically identical to
# the D44 advance above.
#
# CAUSE. `ScenarioConfig.ccs_retrofit_capex_co2_scaling` flips default
# False -> True: the capture island is sized to the CO2 the host actually
# captures — `capex_kw x 1000 x captured / captured_ref`, `captured_ref` =
# 0.90 x 6.3 x 0.057 = 0.32319 t/MWh, the SAME reference host
# `new_entry._emerging_lcoe` charges the ATB 2024 gas_cc_ccs increment against
# — and cogeneration hosts (`plant_group` CC_CHP) leave the retrofit candidate
# set. Zero DOF: every term is an already-cited constant. Evidence:
# `docs/handoffs/FINDING-capx-d50-2026-09-04.md` §§1-5 and §8 (four A/B arms;
# at carbon 0 the repair closes the screen — ERCOT 3.79 GW -> 0, PJM 5.74 -> 0
# in 2028, MISO 4,631.1 MW -> 0 across the window — and under RGGI it does not,
# NEISO 12.79 -> 12.38 GW, which is the repair's signature rather than its
# level); execution record `FINDING-capx-d60-2026-09-05.md`.
#
# WHY THE KEY MOVES: identical to the D44 block above. The field IS a
# `_CACHE_KEY_OPTIONAL_FIELDS` member, `cache_key()` drops it at its FROZEN
# declaration ("False", left untouched), so the armed default enters the hash
# and takes its own key; the flip is DECLARED in
# `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` — its second entry — so check 3 of
# the registration guard passes on the declaration, not on silence.
#
# WHAT THIS COSTS, EXACTLY. A one-time cache MISS per forecast config whose
# horizon REACHES 2028; every shorter horizon is byte-identical because
# `capacity_evolution/ccs.py::apply_ccs_retrofit` returns at
# `if year < config.ccs_retrofit_available_year` (2028) before any read of the
# flag, and that call site is the field's only consumer in the source tree. An
# explicit `ccs_retrofit_capex_co2_scaling=False` still equals the frozen
# declaration, is still dropped, and still hashes 4c6b03ae098b6e3e — measured
# this session, and one committed artifact already relies on it
# (`results/hindcast/miso-2021-2025-realized-t1h-d55-keyfix`). D60 renamed the
# three t1f bare keys onto the D50 arms already solved AT the post-flip key
# (ERCOT / NEISO / PJM) and re-solved the four the arms could not cover.
PINNED_DEFAULT_CACHE_KEY = "e5ecd4105ada3e58"

# The BACKCAST default key, pinned by FFR-3D (2026-08-03) because the forecast
# pin above CANNOT see a whole class of re-key: `__post_init__` coerces several
# forecast-only fields in `mode="backcast"`, so a backcast config's payload is
# not the default config's payload, and the pin above is explicitly a
# mode="forecast" object ("no __post_init__ backcast coercion", see the FF-2C
# note). Every backcast keeper's on-disk bundle is addressed by THIS key.
#
# The gap was not hypothetical. Owner decision D-3a moved
# `net_cone_forward_escalation`'s default "hold_last" -> "reindex_gross" while
# `__post_init__` coerced backcasts to the LITERAL "hold_last". That literal had
# been the default (and so cache-neutral via _CACHE_KEY_OPTIONAL_FIELDS); the
# moment it stopped being the default it entered the hash, moving this key
# 35b6dc12f97968f1 -> 512c2fffbb61414e and ERCOT's 2023 backcast key
# df386bca96a1d288 -> f3ee0af68fa72303 — orphaning every keeper's cache, with
# NO test red. The repair coerces to the dataclass default rather than a
# literal, which is neutral by construction; this pin is what would have caught
# it, and what will catch the next one.
#
# Same discipline as the pin above: do NOT re-baseline this literal to silence a
# failure. A genuine advance is recorded here with a dated cause block.
#
# ADVANCED 2026-08-31, 35b6dc12f97968f1 -> e027bc248c93c835 — owner ruling R-A
# of the director sitting ("Arm both"), executed by the T1-H arming lane. This
# is the DELIBERATE second remedy the sibling property test names, taken with
# eyes open, not a re-baseline to silence red.
#
# CAUSE. `storage_entry_availability_gate` and
# `storage_entry_cost_normalized_rank` flip default False -> True. Both are
# `_CACHE_KEY_OPTIONAL_FIELDS` members AND both are coerced OFF in
# `mode="backcast"`, so coerced-False stopped being the default and both fields
# re-entered the backcast payload — structurally the same shape as the D-3a
# near-miss narrated above, and caught by exactly the pin written for it.
#
# WHY NOT THE D-3a REPAIR (coerce to the dataclass default). Because here that
# would ARM the mechanisms in a backcast rather than merely re-label them.
# `net_cone_forward_escalation` had no live consumer, so coerce-to-default was
# behaviour-neutral; these two feed `apply_storage_new_entry`, and
# `runner.run_scenario_iso` — which serves BOTH modes and takes its evolution
# branch on year 2+ of any multi-year span — would then run the armed screen in
# a multi-year backcast. The production backcast lane
# (`run_calibration_full.py` -> `pipeline.solve`, one config per year) never
# reaches it, so the exposure is latent rather than live; the coercion is what
# keeps it that way, and a default flip is not licence to spend that guarantee.
#
# WHAT THIS COSTS, EXACTLY. A one-time cache MISS per backcast config: every
# pre-2026-08-31 `results/<ISO>/<key>/` backcast bundle is now addressed by a
# key nothing computes, so the next backcast re-solves. It is NOT a behaviour
# change and NOT a scoring change — a backcast's dispatch, its scores and its
# `run_config.json` are byte-identical across the flip (both fields serialize
# False either side), so no keeper, sidecar, determination or dashboard row
# moves and nothing needs re-scoring. Full record: the cache-epoch ledger in
# `src/market_sim/results/cache.py`, epoch 2026-08-31.
#
# ADVANCED 2026-09-02, e027bc248c93c835 -> e006dfd7cef8bedd — the SAME
# owner-authorized capx D41 re-identification recorded in the forward pin's
# cause block above. Unregistered fields are hashed in both modes, so the
# backcast payload moves with the forward one.
#
# BEHAVIOUR IN BACKCAST IS BYTE-IDENTICAL. Neither field is reachable in a
# backcast: `apply_ccs_retrofit` is gated on `ccs_retrofit_available_year`
# (2028, past every backcast year) and `fixed_om_gas_cc_ccs` enters
# `_THERMAL_FOM` only for a `gas_cc_ccs` unit, which exists only after a
# retrofit or a CCS new build and so never appears in a measured backcast
# fleet. Cost is a one-time cache MISS per backcast config; dispatch, scores
# and `run_config.json` values other than these two are unmoved, no keeper or
# determination is affected, and nothing needs re-scoring.
#
# ADVANCED 2026-09-03, e006dfd7cef8bedd -> 8211c72bb1960adc — the SAME capx D44
# / owner-ruling-Q30 default flip recorded in the forward pin's cause block
# above. `fossil_announced_exits_enabled` is NOT coerced in `__post_init__`
# (nothing coerces it, before or after the flip), so the armed default enters
# the backcast payload exactly as it enters the forward one and this pin moves
# with it. It is therefore NOT a `_DECLARED_BACKCAST_COERCION_REKEYS` case: no
# coercion is knowingly off its default here.
#
# BEHAVIOUR IN BACKCAST IS BYTE-IDENTICAL. The channel is consumed only in
# forecast-mode capacity evolution — `data.announced_retirements.
# load_announced_fossil_exits` is reached from `evolve_fleet` / `build_base_
# fleet` under `mode == "forecast"`, and the production backcast lane
# (`run_calibration_full.py` -> `pipeline.solve`, one config per year) never
# evolves a fleet at all. Cost is a one-time cache MISS per backcast config;
# dispatch, scores and every other `run_config.json` value are unmoved, so no
# keeper, sidecar, determination or dashboard row is affected and nothing needs
# re-scoring (committed artifacts are files, not cache lookups). An explicit
# `fossil_announced_exits_enabled=False` still hashes e006dfd7cef8bedd.
#
# ADVANCED 2026-09-05, 8211c72bb1960adc -> 6a2845e50951394e — the SAME capx D60
# / owner-ruling-Q42 default flip recorded in the forward pin's cause block
# above. `ccs_retrofit_capex_co2_scaling` is NOT coerced in `__post_init__`
# (nothing coerces it, before or after the flip), so the armed default enters
# the backcast payload exactly as it enters the forward one and this pin moves
# with it. NOT a `_DECLARED_BACKCAST_COERCION_REKEYS` case: no coercion is
# knowingly off its default here.
#
# BEHAVIOUR IN BACKCAST IS BYTE-IDENTICAL, twice over: the production backcast
# lane never evolves a fleet at all, and even if it did, no backcast year
# reaches `ccs_retrofit_available_year` (2028) and no measured backcast fleet
# contains a `gas_cc_ccs` unit. Cost is a one-time cache MISS per backcast
# config; dispatch, scores and every other `run_config.json` value are unmoved,
# so no keeper, sidecar, determination or dashboard row is affected and nothing
# needs re-scoring. An explicit `ccs_retrofit_capex_co2_scaling=False` still
# hashes 8211c72bb1960adc.
PINNED_BACKCAST_CACHE_KEY = "6a2845e50951394e"

# Registered cache-key-optional fields whose backcast coercion is KNOWINGLY off
# their default, each having paid for its re-key in the block above. Only these
# are exempt from
# ``test_no_registered_optional_field_is_backcast_coerced_off_its_default``;
# an undeclared offender still fails it, and a declared entry that stops being
# coerced fails
# ``test_declared_backcast_rekeys_are_still_really_coerced_off``.
#
# ADD TO THIS LIST ONLY WITH the pin advance in the same commit. It is not a
# way to make the property test quiet — it is the record of a debt already paid.
_DECLARED_BACKCAST_COERCION_REKEYS: dict[str, str] = {
    "storage_entry_availability_gate": (
        "R-A arming 2026-08-31: forecast-only storage entry screen. Coercing to "
        "the dataclass default would ARM it in a multi-year backcast through "
        "runner.run_scenario_iso, so the coercion stays and the re-key was paid "
        "at the pin above"
    ),
    "storage_entry_cost_normalized_rank": (
        "R-A arming 2026-08-31: same posture, same reason — the two are armed "
        "as one mechanism pair and coerced off together"
    ),
}


@pytest.mark.parametrize(
    ("module_path", "class_name"),
    [(mod, cls) for mod, classes in FROZEN_PICKLE_PATHS.items() for cls in classes],
)
def test_pickle_class_resolves_at_frozen_path(
    module_path: str, class_name: str
) -> None:
    """Each pickle-borne class resolves at its frozen path AND ``__module__``
    equals that path (both directions of the unpickle contract)."""
    module = importlib.import_module(module_path)
    assert hasattr(module, class_name), (
        f"{class_name} no longer resolves at {module_path} — this breaks every "
        "committed p2_state pickle"
    )
    cls = getattr(module, class_name)
    assert cls.__module__ == module_path, (
        f"{module_path}.{class_name}.__module__ is {cls.__module__!r}, not "
        f"{module_path!r}. A facade re-export is not enough: unpickling keys on "
        "__module__, so the class must be DEFINED at the frozen path."
    )


def _fields_explaining_the_key_move() -> list[str]:
    """Name the unregistered field(s) whose presence moved the default key.

    Diagnostic only — runs solely on an already-failing pin. The recurring
    rule-24 defect is a solve-affecting field landing on main WITHOUT an entry
    in ``_CACHE_KEY_OPTIONAL_FIELDS``, so it enters the digest at its own
    default and orphans every on-disk cache (documented recurrences in that
    table: pjm_apsouth_interface_cut, pjm_external_net_position_cut, the four
    miso-101 temp_derate_* fields, coal_committed_takeorpay_sunk_fixed,
    pjm_zonal_loss_surface, nyiso_import_sil_retire). Isolating the culprit
    previously required hand-writing a bisect against the pre-pin commit; this
    reproduces that search in-process by dropping one candidate at a time and
    re-hashing. Returns the single-field explanation when there is one, else
    ``[]`` (a multi-field move needs the manual bisect the message describes).
    """
    import hashlib
    import json
    from dataclasses import asdict

    from market_sim.config import scenarios as scen

    payload = asdict(ScenarioConfig())
    defaults = ScenarioConfig()
    for name in scen._CACHE_KEY_OPTIONAL_FIELDS:
        if payload.get(name) == getattr(defaults, name):
            payload.pop(name, None)
    payload = scen._normalize_cache_key_paths(payload, scen._cache_key_path_roots())

    for candidate in sorted(payload):
        probe = {k: v for k, v in payload.items() if k != candidate}
        digest = hashlib.sha256(json.dumps(probe, sort_keys=True).encode()).hexdigest()[
            :16
        ]
        if digest == PINNED_DEFAULT_CACHE_KEY:
            return [candidate]
    return []


def test_default_scenario_config_cache_key_is_pinned() -> None:
    """``ScenarioConfig().cache_key()`` equals the pinned literal."""
    actual = ScenarioConfig().cache_key()
    if actual != PINNED_DEFAULT_CACHE_KEY:
        culprits = _fields_explaining_the_key_move()
        blame = (
            f"\n\nCULPRIT: {culprits[0]!r} — dropping it from the payload "
            f"restores {PINNED_DEFAULT_CACHE_KEY}. It is a solve-affecting "
            "field that landed WITHOUT an entry in "
            "scenarios.py::_CACHE_KEY_OPTIONAL_FIELDS, so it enters the digest "
            "at its own default (rule 24 [R-REGISTRY]). If it is "
            "byte-identical at that default — verify its consumer is gated on "
            "the flag — the one-line remedy is to register it there, which "
            "restores every orphaned cache key and leaves ARMED runs' keys "
            "untouched. Register it; do NOT re-baseline the literal."
            if culprits
            else (
                "\n\nNo SINGLE field explains the move (several landed at "
                "once, or a field's default value changed). Bisect against the "
                "commit that last set the pin: diff the payload key sets of "
                "that commit's ScenarioConfig and this one."
            )
        )
        raise AssertionError(
            f"The default ScenarioConfig cache_key changed: {actual} != "
            f"{PINNED_DEFAULT_CACHE_KEY}. A field that reaches asdict() moved "
            "or changed its default; this orphans every on-disk cache and "
            "breaks keeper reproducibility. Do not update the literal to "
            f"silence this — find what changed.{blame}"
        )


def test_backcast_scenario_config_cache_key_is_pinned() -> None:
    """``ScenarioConfig(mode="backcast").cache_key()`` equals the pinned literal.

    Every backcast keeper's bundle is addressed by this key, and the forecast
    pin above cannot see it (that object takes no ``__post_init__`` backcast
    coercion). See the ``PINNED_BACKCAST_CACHE_KEY`` block for the D-3a
    near-miss this exists to catch.
    """
    actual = ScenarioConfig(mode="backcast").cache_key()
    assert actual == PINNED_BACKCAST_CACHE_KEY, (
        f"The default BACKCAST ScenarioConfig cache_key changed: {actual} != "
        f"{PINNED_BACKCAST_CACHE_KEY}. This orphans every backcast keeper's "
        "on-disk cache. The usual cause is a field that __post_init__ coerces "
        "to a LITERAL in backcast, where that literal has stopped being the "
        "field's default and so stopped being cache-neutral — coerce to the "
        "dataclass default instead. Do not re-baseline the literal."
    )


def test_no_registered_optional_field_is_backcast_coerced_off_its_default() -> None:
    """Backcast coercion must land every registered field on its default.

    The general form of the invariant above. ``_CACHE_KEY_OPTIONAL_FIELDS`` is
    cache-neutral **at the default only**, so a backcast coercion that lands on
    anything else silently re-keys every backcast bundle. Checking the property
    (rather than only the digest) names the offending field directly.

    A field may leave the property ONLY through
    :data:`_DECLARED_BACKCAST_COERCION_REKEYS` — the second remedy this test's
    own message offers — which requires the re-key to have been paid for at
    ``PINNED_BACKCAST_CACHE_KEY`` with a dated cause block. An UNDECLARED
    offender still fails, so the silent-re-key hole stays closed.
    """
    from market_sim.config import scenarios as scen

    defaults = ScenarioConfig()
    backcast = ScenarioConfig(mode="backcast")
    offenders = {
        name: (getattr(defaults, name), getattr(backcast, name))
        for name in scen._CACHE_KEY_OPTIONAL_FIELDS
        if getattr(backcast, name) != getattr(defaults, name)
        and name not in _DECLARED_BACKCAST_COERCION_REKEYS
    }
    assert not offenders, (
        "registered cache-key-optional field(s) are coerced OFF their default "
        f"in backcast, so they enter the backcast hash: {offenders}. Coerce to "
        "the dataclass default (see net_cone_forward_escalation in "
        "scenarios.py::__post_init__), or accept the re-key deliberately and "
        "advance PINNED_BACKCAST_CACHE_KEY with a dated cause block, adding the "
        "field to _DECLARED_BACKCAST_COERCION_REKEYS with its reason."
    )


def test_declared_backcast_rekeys_are_still_really_coerced_off() -> None:
    """Every declared exemption must still BE one — no stale allowlist entries.

    The allowlist suppresses a real invariant, so it may only ever name fields
    that genuinely are coerced off their default today. A field that later
    stops being coerced (or whose default moves back) must leave the list, or
    it would silently license a future re-key nobody paid for.
    """
    from market_sim.config import scenarios as scen

    defaults = ScenarioConfig()
    backcast = ScenarioConfig(mode="backcast")
    stale = [
        name
        for name in _DECLARED_BACKCAST_COERCION_REKEYS
        if name not in scen._CACHE_KEY_OPTIONAL_FIELDS
        or getattr(backcast, name) == getattr(defaults, name)
    ]
    assert not stale, (
        f"stale _DECLARED_BACKCAST_COERCION_REKEYS entries: {stale}. Each is "
        "either no longer cache-key-registered or no longer coerced off its "
        "default, so its exemption is dead and must be removed."
    )


def test_default_cache_key_is_checkout_path_invariant(monkeypatch) -> None:
    """The default key is identical whatever directory the checkout lives in.

    Pins the PROPERTY behind the 2026-07-27 cache-epoch bump, not just its
    literal: before the fix, six absolute-path fields put the checkout
    directory into the hash, so the pin above failed on every GitHub-hosted
    run (/home/runner/work/... → 329093815fa58f5b) while passing on a session
    container. Simulates a relocated checkout by moving the path roots AND the
    stored path values together, exactly as a real clone elsewhere would.
    """
    import market_sim.config.paths as paths_mod

    elsewhere = "/home/runner/work/market-simulator/market-simulator"
    here = str(paths_mod.REPO_ROOT)
    base = ScenarioConfig()

    relocated_values = {
        f.name: getattr(base, f.name).replace(here, elsewhere)
        for f in dataclasses.fields(base)
        if isinstance(getattr(base, f.name), str)
        and getattr(base, f.name).startswith(here + "/")
    }
    assert relocated_values, (
        "No absolute repo-rooted path fields found — if the defaults became "
        "relative this test is obsolete, but do not delete it silently."
    )

    monkeypatch.setattr(paths_mod, "REPO_ROOT", Path(elsewhere))
    monkeypatch.setattr(paths_mod, "DATA_ROOT", Path(elsewhere))
    relocated = base.with_overrides(**relocated_values)

    assert relocated.cache_key() == PINNED_DEFAULT_CACHE_KEY, (
        "cache_key() is checkout-path-dependent again: a config identical up to "
        "the checkout directory hashed differently. A new absolute-path field "
        "must be folded by scenarios.py::_normalize_cache_key_paths."
    )


def test_cache_key_still_forks_on_a_genuinely_different_file() -> None:
    """Normalization must not collapse distinct data sources onto one key."""
    base = ScenarioConfig()
    for other in (
        base.with_overrides(campd_bins_path=base.campd_bins_path + ".alt"),
        base.with_overrides(campd_bins_path="/mnt/external/bins.csv"),
    ):
        assert other.cache_key() != base.cache_key()


# --------------------------------------------------------------------------
# Module-level import-cycle guard
# --------------------------------------------------------------------------

_SRC = REPO_ROOT / "src"
_PKG_ROOT = _SRC / "market_sim"


def _module_name(path: Path) -> str:
    """Dotted module name for a .py file under ``src/`` (``__init__`` → package)."""
    parts = list(path.relative_to(_SRC).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_type_checking(node: ast.If) -> bool:
    """True when an ``if`` guards a ``TYPE_CHECKING`` block (not run at import)."""
    test = node.test
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


def _module_level_imports(tree: ast.AST):
    """Yield Import/ImportFrom nodes that execute at import time.

    Descends into module-body compound statements (``if``/``try``/``with``/loops
    and class bodies — all run at import) but NOT into function bodies (lazy
    imports, the intentional cycle break) and NOT into ``TYPE_CHECKING`` guards.
    """

    def walk(node, in_func):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield from walk(child, True)
            elif isinstance(child, ast.If) and _is_type_checking(child):
                for sub in child.orelse:  # the else-branch still runs
                    yield from walk(sub, in_func)
            else:
                if not in_func and isinstance(child, (ast.Import, ast.ImportFrom)):
                    yield child
                yield from walk(child, in_func)

    yield from walk(tree, False)


def _resolve_targets(node, module_name: str, is_package: bool, known: set[str]):
    """Return the set of intra-package modules an import statement executes."""
    targets: set[str] = set()
    if isinstance(node, ast.Import):
        for alias in node.names:
            targets.add(alias.name)
    else:  # ImportFrom
        if node.level:
            # Relative import anchor: a package's own name, else its parent.
            anchor = module_name.split(".")
            if not is_package:
                anchor = anchor[:-1]
            if node.level > 1:
                anchor = anchor[: len(anchor) - (node.level - 1)]
            prefix = ".".join(anchor)
            full = f"{prefix}.{node.module}" if node.module else prefix
        else:
            full = node.module or ""
        if full:
            targets.add(full)
            for alias in node.names:
                targets.add(f"{full}.{alias.name}")
    return {t for t in targets if t in known and t != module_name}


def _import_graph() -> dict[str, set[str]]:
    files = sorted(_PKG_ROOT.rglob("*.py"))
    known = {_module_name(f) for f in files}
    graph: dict[str, set[str]] = {m: set() for m in known}
    for path in files:
        module_name = _module_name(path)
        is_package = path.name == "__init__.py"
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in _module_level_imports(tree):
            graph[module_name] |= _resolve_targets(node, module_name, is_package, known)
    return graph


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Return every non-trivial strongly-connected component (Tarjan)."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    stack: list[str] = []
    counter = [0]
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack[v] = True
        for w in graph[v]:
            if w not in index:
                strongconnect(w)
                low[v] = min(low[v], low[w])
            elif on_stack.get(w):
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in graph:
        if v not in index:
            strongconnect(v)
    cycles = [sorted(c) for c in sccs if len(c) > 1]
    cycles += [[v] for v in graph if v in graph[v]]  # self-loops
    return cycles


def test_no_module_level_import_cycles() -> None:
    """``src/market_sim`` has zero module-level (import-time) import cycles."""
    cycles = _find_cycles(_import_graph())
    assert not cycles, (
        "Module-level import cycle(s) introduced — break them with a lazy "
        "(in-function) import:\n" + "\n".join("  " + " <-> ".join(c) for c in cycles)
    )
