"""Regression tripwires for the persisted-artifact surfaces every later
refactor depends on.

Four independent guards:

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
* **Repo-wide pin consistency.** The pin above is re-asserted in two dozen
  per-mechanism suites, so a re-key that advances only some of them leaves the
  rest stale — twice now that partial re-key reached ``main`` with this job
  green, because nothing here could see a literal in ``tests/unit/**``. An AST
  scan asserts every default-config cache key asserted anywhere under
  ``tests/`` is this one literal.
* **No module-level import cycles.** The package breaks would-be cycles with
  lazy (in-function) imports; a cycle introduced at module scope is an import-
  time crash waiting for the wrong import order. An AST walk asserts the
  module-level import graph of ``src/market_sim`` is acyclic.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import re
from pathlib import Path

import pytest

from market_sim.config import scenarios as scen
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
#
# ADVANCED 2026-09-06, e5ecd4105ada3e58 -> 547053bdfccd4264 — capx D65-B
# executing OWNER RULING Q47 (director sitting r#42 amendment 2, verbatim
# "Arm coupled, after D60-R3"). TWO acts in ONE PR and ONE re-key event, and
# the coupling is the point: the THIRD declared (b'-1) flip alone would have
# been mechanically identical to the two advances above, but it does not ship
# alone.
#
# CAUSE, ACT A. `ScenarioConfig.ccs_retrofit_fixed_cost_co2_scaling` flips
# default False -> True: the retrofit's two FIXED-COST legs — ΔFOM ($/MW-yr)
# and the capture VOM adder ($/MWh) — are scaled by the SAME
# `k = captured / captured_ref` seam 1 (the D60 advance above) applies to the
# island's capex, because both legs are TPC fractions in their own published
# sources (ATB 2024's fossil methodology page; NETL Rev 4a B31A->B31B.90 at
# 95.5 % fixed / 100 % variable). Zero DOF, no new constant, no new reference
# host. Evidence: `FINDING-capx-d64-2026-09-05.md` §1 (the zero-LP
# adjudication) and `FINDING-capx-d65-2026-09-05.md` §4 (the NEISO t1f arm:
# every host lost is k 1.55-1.71, every host gained k 0.95-1.06, MW-weighted
# er 0.575 -> 0.391 — the inverted ordering D49 §1.4 named, restored).
#
# CAUSE, ACT B. `ScenarioConfig.ccs_retrofit_vom_adder` 8.0 -> 2.95 $/MWh,
# 2026$, dollar-year now STATED. Read off the NREL ATB 2024 v4.0.0 basis the
# screen's other two cost legs already use (capx D41 §2.3: host and island on
# ONE basis): (4.8 - 2.1) x 1.090947 = 2.95. The shipped 8.0 was
# `needs-citation`, carried no dollar-year, and cited NETL Rev 4a — a document
# that publishes 2.23 for this increment. It could not previously be read off
# the pinned basis AT ALL, because the committed ATB extract carried no
# `Variable O&M` for `NaturalGas_FE`; D65-B item 1 widens the extract from the
# SAME source bytes (OEDI ATBe.csv v4.0.0, sha256 567dde9d…, a verified strict
# superset: 3,858 pre-existing rows value-identical, so NEW_ENTRY_COSTS and
# TECH_COST_MULTIPLIERS cannot move) and pins the derivation in
# `tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py`.
#
# WHY THE ACTS ARE COUPLED (D65 §8.1). Act A multiplies Act B's level by k, so
# arming the shape on an uncited 2.7x level compounds the error on exactly the
# high-emitting hosts the seam exists to re-price — and would commit the model
# to "no merchant NGCC retrofit ever clears on §45Q at carbon 0", a stronger
# claim than the evidence carries. Neither half was admissible alone.
#
# WHY THE KEY MOVES — AND WHY THIS ADVANCE IS NOT LIKE THE TWO ABOVE. Act A's
# half is the familiar one: the field IS a `_CACHE_KEY_OPTIONAL_FIELDS` member,
# dropped at its FROZEN "False" declaration (left untouched), so the armed
# default enters the hash; the flip is DECLARED — the third entry in
# `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` — so check 3 passes on the
# declaration. Act B's half is NOT: `ccs_retrofit_vom_adder` is a plain value
# field with no frozen declaration to drop at, so it re-keys UNCONDITIONALLY,
# including every explicit-control arm the D44 and D60 advances deliberately
# left on their pre-flip keys. That is a consequence of the coupling, declared
# in advance (D65 §9 item 3), not a regression.
#
# ACT A'S DROP-VALUE MECHANIC IS INTACT, and is measured by decomposition
# rather than asserted: holding the VOM at its shipped 8.0, an explicit
# `ccs_retrofit_fixed_cost_co2_scaling=False` hashes to e5ecd4105ada3e58 —
# exactly the pre-flip default pinned above. The movement is Act B's.
#
# WHAT THIS COSTS, EXACTLY. A one-time cache MISS per forecast config whose
# horizon REACHES 2028; every shorter horizon and every backcast is
# byte-identical in BEHAVIOUR, because `capacity_evolution/ccs.py::
# apply_ccs_retrofit` returns at `if year < config.ccs_retrofit_available_year`
# (2028) before any read of EITHER field, and that call site is the only
# consumer of both in the source tree. Their keys move; their answers do not.
# No keeper, sidecar, determination or dashboard row moves.
#
# Pre-declared BEFORE the solve — every key in this advance — in
# `docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md` §3; cache-epoch ledger
# entry 2026-09-06c in `src/market_sim/results/cache.py`; execution record
# `FINDING-capx-d65b-2026-09-06.md`.
PINNED_DEFAULT_CACHE_KEY = "547053bdfccd4264"

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
#
# ADVANCED 2026-09-06, 6a2845e50951394e -> f61891696e671969 — the SAME capx
# D65-B coupled arming (owner ruling Q47). See the forward-key block above for
# the two acts and the coupling. The backcast pin moves for the same reason it
# moved on 2026-09-03 and 2026-09-05: the cache key is computed over the whole
# config and is mode-agnostic, so a forecast-only mechanism still re-keys it.
#
# BACKCAST BEHAVIOUR IS UNCHANGED, and by a stronger argument than either
# earlier advance had, because it now covers BOTH fields at once: the sole
# consumer of `ccs_retrofit_fixed_cost_co2_scaling` AND of
# `ccs_retrofit_vom_adder` in the source tree is
# `capacity_evolution/ccs.py::apply_ccs_retrofit`, which returns at
# `if year < config.ccs_retrofit_available_year` (2028) before reading either.
# No backcast year reaches 2028 and no measured backcast fleet contains a
# `gas_cc_ccs` unit. The cost is a one-time cache MISS; no keeper, sidecar,
# determination or dashboard row moves, because committed artifacts are files,
# not cache lookups, and no backcast keeper is re-solved by this lane.
PINNED_BACKCAST_CACHE_KEY = "f61891696e671969"

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

# --------------------------------------------------------------------------- #
# The SOLVE SURFACE (capx D79, owner ruling Q54)
# --------------------------------------------------------------------------- #
# `surface_stamp(iso, ...)["fingerprint"]` per ISO: the digest over that ISO's
# WHOLE projected row set of the seven `solve_surface.SURFACE_MODULES`. The two
# config pins above cannot see this — a re-derived `DEMAND_GROWTH_RATES` or a
# repaired demand curve changes what every solve produces while `asdict(config)`
# is byte-identical, which is the SCN-LOAD incident (design memo §1, three
# tables, every T1-F peak moved, zero keys moved).
#
# WHAT A FAILURE HERE MEANS, AND THE ONE WRONG REMEDY. A registry VALUE moved.
# That is legitimate and routine — it is how a repair lands — and the fix is
# NEVER to re-declare the row in `config/solve_surface_declared.py` (which would
# restore the pre-change key and re-serve the pre-repair bundle; guard check 6
# fails an edit there). The remedy is to ADVANCE the pin below with a dated
# cause block naming what moved, why, which ISOs it reaches and what it costs —
# and that block IS the cache-epoch ledger entry the lane owes for a registry
# change, in the place the change is actually detectable.
#
# `python3 scripts/solve_surface_register.py --diff <base>` names the moved rows
# and the ISOs each reaches, which is what a cause block is written from.
#
# The ROW COUNT beside each digest is diagnostic, not load-bearing: it separates
# "a value moved" (count unchanged) from "a table was added or removed" (count
# moved) at a glance, and an addition moves no cache key at all.
#
# 2026-09-06 SET AT LANDING (capx D79 phase 1). Every name declared at its live
# hash, so `moved_rows(iso) == {}` for all six ISOs and no key moved; the no-op
# probe over every committed run config reads 0 moved
# (`docs/handoffs/capxd79-solve-surface-no-op-record.json`). 296 surface names,
# 76 of them by-ISO tables.
#
# 2026-09-06 ERCOT ADVANCED (ercot-253, the rule-22 validation ladder).
#   WHAT MOVED: `NUCLEAR_MONTHLY_CF_BY_YEAR["ERCOT"]` — one ADDED key, 2021,
#   derived by `scripts/data/derive_nuclear_monthly_cf.py --isos ERCOT --years
#   2021` from EIA-923 Page 1 monthly net generation, the same script and source
#   the 2022-2025 rows carry. The 2022 and 2023 rows were re-derived in the same
#   run as the producer re-proof and came back byte-identical, so NO EXISTING
#   YEAR'S VALUES MOVED.
#   WHICH ISOs: ERCOT only (`moved_rows` is `{}` for the other five — rule 25
#   [R-ISO-SCOPE]; the by-ISO table shape is what confines it).
#   WHY: rule 22 [R-HOLDOUT] — "what is held out is the SCORE, never the DATA".
#   The 2021 validation rung needs the same measured nuclear level anchor every
#   other year has; leaving the row absent would make the pre-2022 nuclear block
#   a timing series with an unreconciled level.
#   WHAT IT COSTS: every future ERCOT solve re-keys, so the keeper's cached
#   results are no longer served by key. It does NOT change any committed
#   number: a 2022-2025 solve reads only its own year's row and every one of
#   those is unchanged, so a re-solve reproduces the keeper bundle. The row
#   count moves 225 -> 226 for the SECOND, separate change in the same session
#   (below), not for this one.
#
#   ALSO IN THIS ADVANCE: the ADDED table
#   `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` (ERCOT's PUCT-ordered
#   system-wide offer cap and minimum contingency level by year, resolved onto
#   `ordc_voll` / `ordc_mcl_mw` in `pipeline/backcast_config.py`; owner ruling
#   2026-09-06 on the 2021 rung). That is an ADDITION, declared at its live
#   hash, so it moves NO key — it is why the row count goes 225 -> 226 while
#   `moved_rows("ERCOT")` still names `NUCLEAR_MONTHLY_CF_BY_YEAR` alone. It
#   changes no year's solve but 2019-2021, which the table alone reaches; 2022
#   onward are listed at exactly the shipped defaults.
#
# 2026-09-07 CAISO ADVANCED (caiso-262, the rule-22 2022 validation touchpoint).
#   WHAT MOVED: two by-ISO tables, both by ADDING a 2022 key and moving NO
#   existing year's value (hence the row count stays 202 — nothing was added
#   or removed from the surface, only two existing rows changed value).
#     1. `STATE_CARBON_PRICE_BY_ISO["CAISO"]` — 2022 = $28.45/t, the simple
#        mean of that year's four CA-Quebec joint-auction current-vintage
#        settlement prices (Feb $29.15, May $30.85, Aug $27.00, Nov $26.80),
#        the identical recipe and source the 2023-2025 rows carry, each price
#        attributed to its own CARB press release and cross-checked against
#        EDF Climate 411 before it was written.
#     2. `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"]` — the 2022 monthly CF vector
#        from `derive_nuclear_monthly_cf.py --isos CAISO --years 2022` over
#        EIA-923 Page 1. The 2023-2025 rows were re-derived in the SAME run as
#        the producer re-proof (`--check`) and came back byte-identical, so no
#        existing year's values moved.
#   WHICH ISOs: CAISO only — `moved_rows` is `{}` for MISO/PJM/NYISO/NEISO and
#   names only ERCOT's own pre-existing NUCLEAR_MONTHLY_CF_BY_YEAR entry for
#   ERCOT (rule 25 [R-ISO-SCOPE]; the by-ISO table shape is what confines it).
#   WHY: rule 22 [R-HOLDOUT] — "what is held out is the SCORE, never the DATA".
#   Both were SILENT fallbacks measured before they were fixed: without its row
#   `state_carbon_price` returns None and `resolve_carbon_price(CAISO, 2022)`
#   reads $0.00/tCO2 against 33.03/35.23/28.06 in the tuned years (~$11-12/MWh
#   on a gas CC, and merit-order distorting since the CC-to-steam rate spread
#   is ~2.9x) — the NYISO-134 D-1 defect, CAISO edition; and the nuclear CF
#   would fall back to the static seasonal pattern, losing Diablo Canyon's 2022
#   refuelling outages (Apr 0.54 / Oct 0.73 / Nov 0.58).
#   WHAT IT COSTS: every future CAISO solve re-keys, so the keeper's cached
#   results are no longer served by key. It does NOT change any committed
#   number — a 2023-2025 solve reads only its own year's row from each table
#   and every one of those is unchanged, so a re-solve reproduces the keeper
#   bundle. (The same session also added 2022 rows to the CAISO import-tranche
#   and DSW clean-depth tables, but those live in `model/interchange/spec.py`,
#   which design §2.3 puts OUT of phase 1 — they move no fingerprint here.)
# 2026-09-08 — SPP-49 (owner ruling P19): TWO NAMES ADDED to constants.py,
#   both unprojected (no ISO token), so every ISO's row count rises by two:
#   `EGRID_CT_HR_PHYSICAL_FLOOR` (an alias of HEAT_RATE_BINS["gas_ct"]["aero"],
#   the simple-cycle heat-rate floor `data/fleet/eia860.py::
#   _apply_simple_cycle_hr_floor` clamps to) and
#   `F923_GAS_PRICE_PLAUSIBILITY_BAND` ((0.5, 2.0), the EIA-923 own-month
#   plausibility band `data/fuel/plant_prices.py::screen_gas_plant_month_prices`
#   reads). Both DECLARED at their live hash by `solve_surface_register.py
#   --declare-missing` in the same commit, so NO VALUE MOVED and no key is
#   reached by a registry change (`solve_surface_register.py --diff 4e4ad90d`:
#   "302 names; 0 value(s) moved, 2 added"). The digests advance because the
#   fingerprint spans every row; the row counts advance by exactly two.
#   WHAT IT COSTS: nothing through this surface. What the two repairs DO cost
#   is recorded where each lands: seam 1 is a registered gate whose default
#   flip re-keys the 18 armed backcast configs by design (scenarios.py flips
#   ledger, 2026-09-08 entry); seam 2 is a construction — a same-key
#   invalidation for every ISO whose fleet carries a clamped simple-cycle row
#   (all seven, PRECOMMIT-spp-49-2026-09-08.md §3.2 / §4), routed to the
#   cache-epoch ledger.
#   PJM ALSO CARRIES ONE PRE-EXISTING ROW this block advances with it: at the
#   base 4e4ad90d PJM's live surface already read 212 rows against the 211
#   pinned here — `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO`, a PJM-keyed table
#   added (and declared, moving no key) between the last pin advance
#   (b654af81) and the base, whose own pin advance never landed. Named, not
#   absorbed silently; the +1 is that lane's, the +2 are this one's.
#
# 2026-09-10 ERCOT + NYISO ADVANCED (salvage lane) — A TRANSCRIPTION REPAIR,
#   NOT A SURFACE MOVE. NOTHING MOVED AND NOTHING IS RE-SERVED.
#   WHAT MOVED: nothing. `solve_surface_register.py --diff aa7a0440` — the
#   very commit that WROTE the literals below — reports "304 -> 304 names;
#   0 value(s) moved, 0 added, 0 removed / NO VALUE MOVED — no ISO's key is
#   reached by a registry change". Per-ISO row-NAME sets were also compared
#   set-wise between aa7a0440 and HEAD for all seven ISOs: identical, every
#   one. And `moved_rows` is `{}` for NYISO and names only the
#   already-ledgered `NUCLEAR_MONTHLY_CF_BY_YEAR` for ERCOT (the 2026-09-06
#   block above), so no row sits off its declaration un-ledgered.
#   WHY THE PINS WERE WRONG: they were stale the moment they were written.
#   Measured at aa7a0440 itself, ERCOT's live surface already read 229 rows
#   against the 228 pinned and NYISO's 209 against the 208 pinned; the same
#   229/209 holds at every earlier commit in this clone that touches a surface
#   module (back to 2962c842). This is the SAME defect the 2026-09-08 SPP-49
#   block above caught and named for PJM — "a PJM-keyed table added between
#   the last pin advance and the base, whose own pin advance never landed" —
#   except that it was left unfixed for the other two ISOs carrying it,
#   because that block derived the new counts arithmetically (+2 to every
#   ISO) instead of measuring each one. Named here rather than absorbed: the
#   +1 in each of ERCOT and NYISO is inherited, not this lane's.
#   WHICH ISOs: ERCOT and NYISO only. CAISO, MISO, PJM and NEISO already match
#   their pins exactly and are untouched.
#   WHAT IT COSTS: NOTHING. A digest that never described the live surface
#   cannot have been serving anything; no key moves, no cached bundle stops
#   being served, no committed number changes, and no run is re-solved. The
#   pins simply start telling the truth, which is what makes the guard able to
#   catch the NEXT real move.
PINNED_SURFACE_ROWS_BY_ISO: dict[str, tuple[str, int]] = {
    "ERCOT": ("5ab10cf3fa2f1447", 229),
    "CAISO": ("cba92d202f32f9fd", 204),
    "MISO": ("9f0845000dc8af6e", 210),
    "PJM": ("905116f13849914f", 214),
    "NYISO": ("1eefed492204fab7", 209),
    "NEISO": ("9d35c270c69e9eee", 197),
}


@pytest.fixture
def config_identity_only(monkeypatch):
    """Neutralize the solve surface, so a key pin measures the CONFIG alone.

    The two pinned literals above are statements about ``ScenarioConfig``'s
    field set and defaults. Since capx D79 ``cache_key()`` also carries any
    registry row that has moved off its declaration, so without this fixture a
    registry repair would fail the config pins too — pointing every reader at
    the wrong ledger. With it, a registry move fails
    :data:`PINNED_SURFACE_ROWS_BY_ISO` and nothing else, and a config move fails
    the config pins and nothing else.

    Both surface inputs are pinned to their landing values (no moved rows, no
    applicable epochs), which is what makes the literals above unchanged by D79.
    """
    monkeypatch.setattr(scen, "moved_rows", lambda iso: {})
    monkeypatch.setattr(scen, "applicable_epochs", lambda config: [])


@pytest.mark.parametrize("iso", sorted(PINNED_SURFACE_ROWS_BY_ISO))
def test_solve_surface_fingerprint_is_pinned(iso: str) -> None:
    """Each ISO's registry surface equals its pinned digest."""
    from market_sim.config.solve_surface import surface_rows, surface_stamp

    expected_digest, expected_rows = PINNED_SURFACE_ROWS_BY_ISO[iso]
    stamp = surface_stamp(iso, ScenarioConfig(iso=iso))
    rows = surface_rows(iso)
    assert stamp["fingerprint"] == expected_digest and len(rows) == expected_rows, (
        f"{iso}'s solve surface moved: {stamp['fingerprint']} "
        f"({len(rows)} rows) != {expected_digest} ({expected_rows} rows). A "
        "registry VALUE changed, so every future solve of this ISO produces "
        "different numbers than the bundles already on disk. Do NOT re-declare "
        "the row in config/solve_surface_declared.py — that restores the "
        "pre-change key and re-serves the pre-change bundle. Name what moved "
        "with `python3 scripts/solve_surface_register.py --diff <base>`, then "
        "advance the pin here with a dated cause block: which rows, which ISOs, "
        "what it costs. That block is the ledger entry this change owes."
    )


#: Rows deliberately moved off their declaration, each with the dated cause
#: block above that explains it. APPEND-ONLY, and an entry is only ever added by
#: the lane that moved the row, in the same commit as its cause block.
#:
#: A moved row is the D79 mechanism WORKING — the row enters the ISO's cache key
#: and the repaired value takes its own bundle — so the merge gate below cannot
#: be "nothing ever moves" once any repair has landed. What it must stay is a
#: gate on UNLEDGERED movement: a row that moved with no cause block is a
#: registry value that changed while every reader still believes the pin.
LEDGERED_SURFACE_MOVES_BY_ISO: dict[str, dict[str, str]] = {
    "ERCOT": {
        "RGGI_MEMBER_STATES_BY_YEAR": (
            "pjm-h22 2026-09-24: the 2020 and 2022 rows ADDED (NJ rejoined 2020; VA a member 2021-2023). Shared name, so every ISO re-keys; only PJM reads membership in any solve path armed today (per-generator mask, PJM-only; the mass-cap budget path has no 2020/2022 per-state budget, so it is None either way). No existing row moved, no committed number changes, cache miss only"
        ),
        "NUCLEAR_MONTHLY_CF_BY_YEAR": (
            "ercot-253 2026-09-06: the 2021 row ADDED for the rule-22 "
            "validation ladder (no existing year's values moved) — see the "
            "cause block on PINNED_SURFACE_ROWS_BY_ISO"
        ),
    },
    "CAISO": {
        "RGGI_MEMBER_STATES_BY_YEAR": (
            "pjm-h22 2026-09-24: the 2020 and 2022 rows ADDED (NJ rejoined 2020; VA a member 2021-2023). Shared name, so every ISO re-keys; only PJM reads membership in any solve path armed today (per-generator mask, PJM-only; the mass-cap budget path has no 2020/2022 per-state budget, so it is None either way). No existing row moved, no committed number changes, cache miss only"
        ),
        "STATE_CARBON_PRICE_BY_ISO": (
            "caiso-262 2026-09-07: the 2022 row ADDED for the rule-22 "
            "validation touchpoint — $28.45/t, the four CA-Quebec joint "
            "auctions' mean, same recipe as 2023-2025; without it the 2022 "
            "CARB allowance cost read $0/tCO2 (no existing year's values "
            "moved) — see the cause block on PINNED_SURFACE_ROWS_BY_ISO"
        ),
        "NUCLEAR_MONTHLY_CF_BY_YEAR": (
            "caiso-262 2026-09-07: the 2022 row ADDED for the rule-22 "
            "validation touchpoint, EIA-923 Page 1 via "
            "derive_nuclear_monthly_cf.py; the 2023-2025 rows re-derived in "
            "the same run came back byte-identical (no existing year's values "
            "moved) — see the cause block on PINNED_SURFACE_ROWS_BY_ISO"
        ),
    },
    "MISO": {
        "RGGI_MEMBER_STATES_BY_YEAR": (
            "pjm-h22 2026-09-24: the 2020 and 2022 rows ADDED (NJ rejoined 2020; VA a member 2021-2023). Shared name, so every ISO re-keys; only PJM reads membership in any solve path armed today (per-generator mask, PJM-only; the mass-cap budget path has no 2020/2022 per-state budget, so it is None either way). No existing row moved, no committed number changes, cache miss only"
        ),
    },
    "PJM": {
        "RGGI_MEMBER_STATES_BY_YEAR": (
            "pjm-h22 2026-09-24: the 2020 and 2022 rows ADDED (NJ rejoined 2020; VA a member 2021-2023). Shared name, so every ISO re-keys; only PJM reads membership in any solve path armed today (per-generator mask, PJM-only; the mass-cap budget path has no 2020/2022 per-state budget, so it is None either way). No existing row moved, no committed number changes, cache miss only"
        ),
        "PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE": (
            "pjm-h22 2026-09-24: 2020-2022 rows ADDED (7.07/10.44/14.84 $/t, the NEISO metric series, same recipe); read only under the default-off pjm_rggi_allowance_pricing gate"
        ),
        "PJM_RGGI_ZONE_SHARE": (
            "pjm-h22 2026-09-24: 2020-2022 rows ADDED via derive_pjm_rggi_zone_share.py, which reproduces 2023-2025 exactly; synthetic-row fallback only"
        ),
        "CAP_AND_TRADE_PROGRAMS": (
            "pjm-h22 2026-09-24: moves only because the PJM program embeds PJM_RGGI_ZONE_SHARE by value"
        ),
    },
    "NYISO": {
        "RGGI_MEMBER_STATES_BY_YEAR": (
            "pjm-h22 2026-09-24: the 2020 and 2022 rows ADDED (NJ rejoined 2020; VA a member 2021-2023). Shared name, so every ISO re-keys; only PJM reads membership in any solve path armed today (per-generator mask, PJM-only; the mass-cap budget path has no 2020/2022 per-state budget, so it is None either way). No existing row moved, no committed number changes, cache miss only"
        ),
    },
    "NEISO": {
        "RGGI_MEMBER_STATES_BY_YEAR": (
            "pjm-h22 2026-09-24: the 2020 and 2022 rows ADDED (NJ rejoined 2020; VA a member 2021-2023). Shared name, so every ISO re-keys; only PJM reads membership in any solve path armed today (per-generator mask, PJM-only; the mass-cap budget path has no 2020/2022 per-state budget, so it is None either way). No existing row moved, no committed number changes, cache miss only"
        ),
    },
}


def test_no_unledgered_row_moved_off_its_declaration() -> None:
    """Every moved row is one the ledger above names — the D79 merge gate.

    A non-empty ``moved_rows`` is not itself a failure of the mechanism (it is
    the mechanism working: the repaired row enters the key and takes its own
    bundle). What fails here is an UNLEDGERED move — a registry value that
    changed while the pins above, and every reader of them, still say otherwise.
    """
    from market_sim.config.solve_surface import moved_rows

    unledgered = {
        iso: sorted(
            set(moved_rows(iso)) - set(LEDGERED_SURFACE_MOVES_BY_ISO.get(iso, {}))
        )
        for iso in PINNED_SURFACE_ROWS_BY_ISO
    }
    unledgered = {iso: rows for iso, rows in unledgered.items() if rows}
    assert not unledgered, (
        f"rows have moved off their declaration with no ledger entry: "
        f"{unledgered}. Advance PINNED_SURFACE_ROWS_BY_ISO with a dated cause "
        "block naming them, and add them to LEDGERED_SURFACE_MOVES_BY_ISO. Do "
        "NOT re-declare the row in config/solve_surface_declared.py — that "
        "restores the pre-change key and re-serves the pre-change bundle."
    )


def test_every_ledgered_move_is_still_a_real_move() -> None:
    """The ledger carries no stale entry (rule 26 [R-DELETE] in the other
    direction): a row listed as moved that is no longer moved would silently
    widen the gate above for a future, genuinely unledgered move."""
    from market_sim.config.solve_surface import moved_rows

    stale = {
        iso: sorted(set(rows) - set(moved_rows(iso)))
        for iso, rows in LEDGERED_SURFACE_MOVES_BY_ISO.items()
    }
    stale = {iso: rows for iso, rows in stale.items() if rows}
    assert not stale, (
        f"LEDGERED_SURFACE_MOVES_BY_ISO names rows that are no longer moved: "
        f"{stale}. Remove the entry — a stale allowance is a hole in the gate."
    )


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

    # REPAIRED 2026-09-09 by capx D91 (owner ruling Q64). This search only works
    # if its baseline is byte-identical to the payload ``cache_key`` hashes, and
    # it had drifted from that payload in TWO places -- EITHER of which alone is
    # enough to make it silent. Measured on the pre-repair tree, over the four
    # combinations (docs/handoffs/FINDING-capx-d91-2026-09-09.md section 3):
    #
    #     frozen drop  retired re-insert   baseline           culprit found
    #     no           no                  d3a7d2f0f38c1f73   []
    #     no           yes                 235aae47427a4422   []
    #     yes          no                  e8bc053241036d6f   []
    #     yes          yes                 080aed989d20cbda   ['pjm_seam_neighbour_hourly_ladder']
    #
    # Only the last row reproduces the digest the assertion itself reports, and
    # only it names the field. So on the f2a834de regression this diagnostic
    # returned [] and the failure printed "No SINGLE field explains the move ...
    # bisect against the commit that last set the pin" -- a hand-bisect
    # instruction -- when ONE field did explain it. The guard fired; only its
    # blame was wrong, and that is why the regression sat on main.
    #
    # (1) Registered fields drop at their FROZEN DECLARATION, which is what
    #     ``cache_key`` drops at since owner ruling Q20 / (b'-1) -- NOT at the
    #     LIVE default this loop used to read. For an ARMED field the two differ
    #     (``ccs_retrofit_capex_co2_scaling`` is True live, False frozen), so
    #     the old loop popped fields ``cache_key`` KEEPS.
    # (2) ``_CACHE_KEY_RETIRED_FIELDS`` must be re-inserted, as ``cache_key``
    #     does; the old baseline omitted all of them.
    payload = asdict(ScenarioConfig())
    drop_at = scen.cache_key_drop_defaults()
    for name in scen._CACHE_KEY_OPTIONAL_FIELDS:
        if name in drop_at and payload.get(name) == drop_at[name]:
            payload.pop(name, None)
    for name, retired_default in scen._CACHE_KEY_RETIRED_FIELDS.items():
        payload.setdefault(name, retired_default)
    payload = scen._normalize_cache_key_paths(payload, scen._cache_key_path_roots())

    for candidate in sorted(payload):
        probe = {k: v for k, v in payload.items() if k != candidate}
        digest = hashlib.sha256(json.dumps(probe, sort_keys=True).encode()).hexdigest()[
            :16
        ]
        if digest == PINNED_DEFAULT_CACHE_KEY:
            return [candidate]
    return []


def test_default_scenario_config_cache_key_is_pinned(config_identity_only) -> None:
    """``ScenarioConfig().cache_key()`` equals the pinned literal.

    Measured with the solve surface neutralized (see ``config_identity_only``),
    so this literal keeps meaning exactly what it has always meant: the identity
    of ``ScenarioConfig``'s field set and defaults.
    """
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


def test_backcast_scenario_config_cache_key_is_pinned(config_identity_only) -> None:
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


def test_solve_surface_is_checkout_path_invariant(monkeypatch) -> None:
    """A relocated checkout hashes the SAME surface (capx D79).

    The surface has no paths in it by construction — it hashes registry VALUES,
    and the seven modules read no file at import. This pins that property rather
    than trusting it: a table that ever came to hold a checkout-absolute path
    would put the checkout directory into every cache key, which is exactly the
    2026-07-27 defect the block above records, one layer down.
    """
    import market_sim.config.paths as paths_mod
    from market_sim.config.solve_surface import reset_caches, surface_rows

    before = {iso: surface_rows(iso) for iso in PINNED_SURFACE_ROWS_BY_ISO}
    elsewhere = Path("/home/runner/work/market-simulator/market-simulator")
    monkeypatch.setattr(paths_mod, "REPO_ROOT", elsewhere)
    monkeypatch.setattr(paths_mod, "DATA_ROOT", elsewhere)
    reset_caches()
    try:
        for iso, rows in before.items():
            assert surface_rows(iso) == rows, (
                f"{iso}'s solve surface is checkout-path-dependent: a registry "
                "value moved when the path roots did. Some surface table now "
                "holds an absolute path; make it relative or move it off the "
                "surface, or every cache key encodes where the checkout lives."
            )
    finally:
        reset_caches()


def test_default_cache_key_is_checkout_path_invariant(
    monkeypatch, config_identity_only
) -> None:
    """The default key is identical whatever directory the checkout lives in.

    Takes ``config_identity_only`` for the reason that fixture exists: this is a
    statement about the CONFIG's path handling, so it must not also carry the
    solve surface. Without it the first legitimate registry move fails here too
    — pointing the reader at "cache_key() is checkout-path-dependent again" when
    nothing about paths changed — and the fixture's own contract ("a registry
    move fails PINNED_SURFACE_ROWS_BY_ISO and nothing else") would not hold.
    Added ercot-253 2026-09-06, on the first such move.

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


# ---------------------------------------------------------------------------
# The repo-wide pin-consistency guard (capx D65-B-R).
#
# WHY THIS EXISTS. The pinned default cache key is asserted in ~two dozen test
# files, not just the one above: every registered-field suite re-asserts it so
# that suite fails loudly if its own field ever enters the default hash. A
# re-key therefore has to touch all of them, and TWICE now a re-key touched
# only some:
#
#   * Y-11 (d2e8dc7a) — the capx D44 fossil_announced_exits_enabled flip, which
#     advanced the pin here and left the per-mechanism suites on the old value;
#   * capx D65-B (fb93b76e, PR #5112) — advanced e5ecd4105ada3e58 ->
#     547053bdfccd4264 and re-pinned 11 files, leaving 13 live assertions on
#     the stale value (15 fast-tier failures) that reached main anyway.
#
# Both times the "Pinned default cache key" job was GREEN, because that job
# runs only this file and the flip guard — neither of which can see a stale
# literal in tests/unit/**. This guard closes that: it makes a PARTIAL re-key
# visible to the one job whose verdict is unambiguous, at zero solve cost.
#
# WHAT IT ASSERTS. Every 16-hex literal that any test asserts EQUAL to a
# default ``ScenarioConfig()``'s ``cache_key()`` is the same literal, and that
# literal is ``PINNED_DEFAULT_CACHE_KEY``. It is deliberately narrow:
#
#   * only a DEFAULT config counts — ``ScenarioConfig()`` with no arguments, or
#     a local name every one of whose assignments is exactly that. A key
#     asserted for an ARMED or ``mode="backcast"`` config, or for one built by
#     ``with_overrides`` / ``dataclasses.replace``, is a different object with
#     its own pin and is not scanned. That is what keeps the deliberate
#     explicit-False decomposition in tests/unit/model/test_ccs_retrofit.py
#     (``ScenarioConfig(ccs_retrofit_fixed_cost_co2_scaling=False,
#     ccs_retrofit_vom_adder=8.0).cache_key() == "e5ecd4105ada3e58"``) out of
#     scope: it is measuring Act A's drop-value mechanic, not the default;
#   * only EQUALITY counts (``assertEqual`` / ``==``); the ``assertNotEqual`` /
#     ``!=`` armed-run assertions beside almost every pin are ignored;
#   * comments and docstrings are invisible to an AST walk, so the ledger
#     narratives that legitimately name superseded keys are never flagged.
# ---------------------------------------------------------------------------

_HEX16 = re.compile(r"\A[0-9a-f]{16}\Z")

# Scanner-liveness floor. The scan finds 25 sites across 24 files today; if a
# refactor breaks the matcher the count collapses and the guard would pass
# vacuously. Raise this only alongside a measurement, never to clear a red.
_MIN_EXPECTED_PIN_SITES = 10


_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def _scope_assignments(scope: ast.AST) -> dict[str, ast.expr]:
    """Map each plain ``name = <expr>`` belonging to ``scope`` to its value.

    Nested function/class/lambda bodies are their own scopes and are skipped,
    so an inner name never leaks outward. A name assigned more than once is
    dropped: it is not safely resolvable, and the guard treats what it cannot
    resolve as unknown rather than guessing.
    """
    values: dict[str, ast.expr | None] = {}

    def descend(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        values[target.id] = None if target.id in values else child.value
            if not isinstance(child, _SCOPE_NODES):
                descend(child)

    descend(scope)
    return {name: value for name, value in values.items() if value is not None}


def _is_bare_scenario_config(node: ast.expr) -> bool:
    """``ScenarioConfig()`` — the constructor, called with no arguments."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "ScenarioConfig"
        and not node.args
        and not node.keywords
    )


def _default_config_names(scope: ast.AST) -> set[str]:
    """Names in ``scope`` bound, only ever, to a bare ``ScenarioConfig()``."""
    return {
        name
        for name, value in _scope_assignments(scope).items()
        if _is_bare_scenario_config(value)
    }


def _is_default_cache_key_expr(node: ast.expr, defaults: set[str]) -> bool:
    """``<default>.cache_key()``, optionally sliced (the ``[:16]`` idiom)."""
    if isinstance(node, ast.Subscript):
        node = node.value
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "cache_key"
        and not node.args
        and not node.keywords
    ):
        return False
    receiver = node.func.value
    if _is_bare_scenario_config(receiver):
        return True
    return isinstance(receiver, ast.Name) and receiver.id in defaults


def _hex16_literal(node: ast.expr, constants: dict[str, str]) -> "str | None":
    """The 16-hex value ``node`` denotes — directly, or via a constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value if _HEX16.match(node.value) else None
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def _equality_operands(node: ast.AST) -> "tuple[ast.expr, ast.expr] | None":
    """The two sides of an ``==`` compare or an ``assertEqual`` call."""
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.Eq)
    ):
        return node.left, node.comparators[0]
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "assertEqual"
        and len(node.args) == 2
    ):
        return node.args[0], node.args[1]
    return None


def _pinned_default_key_assertions(tree: ast.Module) -> "list[tuple[int, str]]":
    """Every ``(lineno, literal)`` this module asserts as THE default key."""
    constants = {
        name: value.value
        for name, value in _scope_assignments(tree).items()
        if isinstance(value, ast.Constant)
        and isinstance(value.value, str)
        and _HEX16.match(value.value)
    }
    found: list[tuple[int, str]] = []

    def collect(node: ast.AST, defaults: set[str]) -> None:
        """Walk ``node``'s children, each under its INNERMOST function scope."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                collect(child, defaults | _default_config_names(child))
                continue
            operands = _equality_operands(child)
            if operands is not None:
                for key_side, value_side in (operands, operands[::-1]):
                    if not _is_default_cache_key_expr(key_side, defaults):
                        continue
                    literal = _hex16_literal(value_side, constants)
                    if literal is not None:
                        found.append((child.lineno, literal))
                    break
            collect(child, defaults)

    collect(tree, _default_config_names(tree))
    return found


def test_the_pinned_default_key_is_pinned_to_ONE_value_repo_wide() -> None:
    """No test anywhere asserts a default cache key other than the pin."""
    sites: dict[str, list[tuple[int, str]]] = {}
    for path in sorted((REPO_ROOT / "tests").rglob("*.py")):
        hits = _pinned_default_key_assertions(ast.parse(path.read_text()))
        if hits:
            sites[str(path.relative_to(REPO_ROOT))] = hits

    total = sum(len(hits) for hits in sites.values())
    assert total >= _MIN_EXPECTED_PIN_SITES, (
        f"Only {total} default-cache-key assertion(s) found across tests/, "
        f"below the liveness floor of {_MIN_EXPECTED_PIN_SITES}. The scanner "
        "above has almost certainly stopped matching the idiom it targets — "
        "repair the matcher; do NOT lower the floor to make this pass."
    )

    by_value: dict[str, list[str]] = {}
    for path, hits in sites.items():
        for lineno, literal in hits:
            by_value.setdefault(literal, []).append(f"{path}:{lineno}")

    if set(by_value) != {PINNED_DEFAULT_CACHE_KEY}:
        report = "\n".join(
            f"  {literal}  ({len(where)} site(s))\n"
            + "\n".join(f"    {w}" for w in sorted(where))
            for literal, where in sorted(by_value.items())
        )
        raise AssertionError(
            "The default ScenarioConfig cache key is asserted with more than "
            f"one value across tests/ (pin here: {PINNED_DEFAULT_CACHE_KEY}):\n"
            f"{report}\n\n"
            "This is a PARTIAL RE-KEY — the failure mode Y-11 (d2e8dc7a) and "
            "capx D65-B (fb93b76e) both shipped to main with this job green. "
            "The live key is whatever ScenarioConfig().cache_key() returns and "
            "the test literals are what go stale, so the repair is to advance "
            "EVERY live assertion to the pin above (ledger comments and "
            "non-default configs' own pins are out of scope and untouched) — "
            "never to change ScenarioConfig or results/cache.py to match a "
            "stale literal."
        )
