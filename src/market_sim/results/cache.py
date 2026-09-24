"""Caching of intermediate and final simulation results.

A cached run lives in ``results/{iso}/{cache_key}/`` where ``cache_key`` is
the deterministic hash of the :class:`~market_sim.config.scenarios.ScenarioConfig`
that produced it. Each weather year's final dispatch is one
``year_{year}.parquet`` file, and the full config is written once as
``config.yaml`` alongside it.

When the two-pass commitment screen runs, the year also keeps a separate
``year_{year}_p1.parquet`` holding the Pass 1 (pre-commitment) dispatch, so
both the P1 and the final P2 datasets are available. ``year_{year}.parquet``
always holds the final result — P2 when commitment is enabled, P1 when it is
off — so every existing reader is unaffected by the extra P1 file.

Cache-key staleness (cache-epoch policy)
----------------------------------------
The cache directory is keyed on ``ScenarioConfig.cache_key()``, which hashes
``asdict(config)`` — so a change that alters a solve's *output* but is **not** a
``ScenarioConfig`` field (a bug fix in the LP builder, a new mechanism gated by
an env var, a change to a measured input basis) does NOT move the key, and a
pre-change ``results/{iso}/{key}/`` bundle would be silently re-used. The
project's cache-epoch policy (refactor-consolidation plan §7 H, compat clause 2)
governs this: a behavior-changing PR must either express the change as a
``ScenarioConfig`` field (so the key moves) or bump the documented cache epoch
and purge/segregate the affected caches. A pure byte-identical refactor needs
neither. This module never auto-invalidates on epoch; that is the operator's
responsibility per that policy.

Since 2026-09-01 the key is no longer the only thing standing between a config
and a bundle: :func:`cache_config_disagreements` compares the requesting config
against the ``config.yaml`` stored beside the bundle, and the runner treats a
disagreement as a cache MISS (capx D24 option (c′), owner ruling Q20). That
closes the *serving* half of the hazard described above — a bundle whose stored
config differs can no longer be handed to a run — but it closes only that half.
The ledger below stays load-bearing for everything the stored config cannot see
(a behavior change that is not a ``ScenarioConfig`` field at all), and it stays
the only surface on which a same-key invalidation is visible to a READER.

Since 2026-09-06 the key sees one more thing: **the SOLVE SURFACE** (capx D79,
owner ruling Q54). ``market_sim.config.solve_surface`` fingerprints the seven
registry modules' module-level values per name and per ISO, and ``cache_key()``
carries any row whose live hash differs from its FROZEN declaration in
``config/solve_surface_declared.py``. So the largest class of same-key
invalidation the ledger below exists for — *"a change to a measured input
basis"*, a re-derived ``DEMAND_GROWTH_RATES``, a repaired demand curve — now
moves the key by itself, scoped to the ISOs whose rows moved, and the bundle
records what it solved on in ``solve_surface.json`` beside its ``config.yaml``.
Landing declared every name at its live hash, so it moved ZERO keys and
invalidated nothing (`docs/handoffs/capxd79-solve-surface-no-op-record.json`).
**What it still cannot see is CODE** — the D55 class, a behaviour change with no
value and no field behind it — which is why everything below stands unchanged.

**The epoch is a dated ledger entry, not a code token.** There is deliberately
no ``CACHE_EPOCH`` constant: a constant that entered ``ScenarioConfig`` would
move the key of *every* config including the backcast keepers (a solve-affecting
change under rule 24 and a rule-28 matrix row for a non-mechanism), and one that
did not enter the key would be inert. A code-level invalidation may instead be
declared MECHANICALLY and in SCOPE as a ``solve_surface.SolveEpoch`` — the same
prose scope (mode, ISOs, "whose horizon reaches 2028") stated so the key carries
its id for exactly those configs. ``SOLVE_EPOCHS`` is EMPTY at D79's landing by
owner ruling Q54 row 4 (the 2026-09-06b entry below stays prose; the D65-B-R
batch is its re-solve), so an entry here is still written as prose first, and the
epoch is what makes it bite. The epoch is materialized on two surfaces, both
human-read:

* **Key advances** — when a change legitimately re-keys the DEFAULT config —
  are recorded at ``PINNED_DEFAULT_CACHE_KEY`` in
  ``tests/regression/test_persisted_identity.py``, with a dated cause block
  above the literal. A key movement caused by an unregistered new field is NOT
  an advance: the remedy is ``_CACHE_KEY_OPTIONAL_FIELDS`` registration
  (``scripts/check_cache_key_registration.py``), never re-pinning.
* **Same-key invalidations** — a behavior change that leaves every key
  unmoved — are recorded in the ledger below, because nothing else can see
  them. Each entry names its date, its cause, exactly what is invalidated, and
  what is NOT.

Cache-epoch ledger (same-key invalidations)
-------------------------------------------
**Epoch 2026-09-24 — R-NEISO: the gas sub-5-day outage scope
(``unit_outage_short_windows_gas``) is armable WITHOUT the coal scope
(``unit_outage_short_windows``).** Before, the gas flag was read only inside the
coal gate, so ``gas=True, coal=False`` solved exactly as both off. It now reads
the gas file alone. A same-key behaviour change for that ONE flag state only;
every other state is byte-identical (``coal_scope`` defaults ``True``). No
committed ``run_config*.json`` carries that state (checked 2026-09-24 over every
``results/calibration/*/run_config*.json``), so nothing cached or registered is
invalidated. **PROSE-ONLY** (no ``SolveEpoch``): there is nothing to re-key.
Record: ``docs/handoffs/r-neiso/PRECOMMIT-r-neiso-2026-09-24.md``.

**Epoch 2026-09-24 — F1 (owner instruction 2026-09-24): vintage-matched eGRID
heat rates in every EIA-860 table, and per-year measured heat-rate artifacts
for every ISO. A SAME-KEY INVALIDATION for every config whose key the
accompanying default flip does not move.** Record:
``docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md`` §5.1
and ``docs/handoffs/f1/``.

**WHAT CHANGED (data, not config).** (1) ``heat_rate`` is re-joined in
``vintage_2018``…``vintage_2024``/``eia860_generators.parquet`` (eGRID of the
same year; 2018/2019/2021/2022 carried no column and 2020 an all-null one), the
canonical snapshot (eGRID 2024, was 2023) and the within-window retiree parquet
(each unit's last operating year), with a nearest-vintage fallback. (2) The
retiree parquet gains the NWPP / SOCO balancing authorities it predated
(append-only). (3) Every ``campd_{ct,coal,st,cc}_heat_rates_<ISO>.csv`` and
``chp_power_only_heat_rates_<ISO>.csv`` is re-derived over 2019-2025 with
per-year rows, and the boundary repair reads the active table's own eGRID
vintage. None of these files is hashed, so no key moves on their account.

**WHAT IS INVALIDATED.** Every cached ``results/<ISO>/<key>/`` bundle solved
before this date whose fleet read any of those files: every backcast (all
years), every hindcast pinned to a ``vintage_<Y>`` (whose 2019-2022 fleets were
priced 95-100 % at the class table before), and every forecast (the canonical
snapshot's heat rates now come from eGRID 2024). Committed keeper bundles are
files, not cache lookups, and keep their numbers as pre-F1 evidence; the
R-<ISO> lanes re-solve them.

**WHAT IS NOT.** No LP code, no offer construction, no ``ScenarioConfig``
default outside ``mode == "backcast"`` (the six backcast-default flips are
KEY-moving and recorded at ``PINNED_BACKCAST_CACHE_KEY`` instead).

**PROSE-ONLY, deliberately (no ``SolveEpoch``).** Every backcast whose inputs
moved is re-solved by the R-<ISO> lanes the audit dispatches after F1 (one
shard per year, 2019-2025), and every bare backcast key already moves with the
default flip; a forecast re-solve is owed by each forecast lane on its own
cadence. A ``SolveEpoch`` would re-key hindcast / forecast bundles that no lane
is serving from cache today.

**Epoch 2026-09-08 — capx D88 / owner ruling Q62: fleet ``unit_id`` uniqueness —
a guard at the SoA seam and a vintage-stamped re-mint at CCS conversion. A TRUE
SAME-KEY INVALIDATION: behaviour moves and NOT ONE KEY DOES, which is exactly
what this ledger exists for.**

**Zero keys move, by both routes.** Ids are not hashed
(``scenarios.py:18691-18717``) and ``solve_surface.SURFACE_MODULES`` names seven
``config/`` + ``pipeline/offer_curve_base`` modules, excluding ``data/fleet`` and
``model/capacity_evolution`` entirely — so the three edited files
(``data/fleet/arrays.py``, ``model/capacity_evolution/ccs.py``, ``evolve.py``)
cannot reach the key. No ``ScenarioConfig`` field and no constant was added
(rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``). VERIFIED, not asserted: the D88
control bundle's recorded key ``0fc42cb56c24d544`` recomputes byte-identically at
HEAD + D88 from its own committed ``run_config.json``, with zero unknown config
keys dropped (the lane's G-DRIFT audit, ``PRECOMMIT-capx-d88-2026-09-08.md`` §3).

**WHAT IS INVALIDATED — the runs whose committed numbers were produced on a
fleet that addressed two generators as one.** A CCS-retrofitted legacy
representative kept its ``unit_id`` while its fuel became ``gas_cc_ccs``, so
``legacy_bins.aggregate_fleet`` re-minted that same id for the next unabated
``gas_cc`` build in the same zone. On a duplicate: ``retirements.py:3423``'s
``idx_of`` is last-write-wins (one twin's exit screen reads the other's
dispatch), one twin's exemption exempts both, retiring one twin drops BOTH from
the fleet, the ``loss_years`` exit clock is shared, and the D57 sell-offer stack
double-offers under one id. Measured over all 72 committed evolution bundles
(zero LP, this lane):

* **The nine NEISO T3 golden variants** — ``bau`` (conversion 2032, colliding
  2033+), ``bau-d46`` and its four ``fc6`` arms (``base``, ``carbon_plus25``,
  ``gaspm5``, ``gasup150``), ``bau-d60``, ``bau-d65br`` (conversion 2031,
  colliding **2037+**, not 2032), and ``bau-prera-2026-08-31`` (which converts
  the SAME id in 2031, 2040, 2042 and 2044 — four generators named
  ``gas_cc_h_class_Central`` by 2045). Cache keys ``706e7ba8e6582d42``,
  ``67678e58b2d0526c``, ``56019f3b0850e9f9``, ``e84079053b581a9e``,
  ``96984c538320d6d6``, ``f04fd06348e1623d``, ``0fc42cb56c24d544``,
  ``a4b11ef4aaa1be35``. **``f04fd06348e1623d`` is the bundle the registered
  ``neiso-t3`` FF-2D verdict is scored on**, including the FC-5 corridor years
  2035 and 2040 — flagged additively in ``frontend/data/forecast/ff-verdicts.json``
  under Q62's second half; the re-score is routed to the D63/D65-B batch.
* **ERCOT ``ff-t1f-d65br``** (``9b9e5a48e3ca5c8e``) — a duplicate in the **2030**
  solved fleet and its ``FleetContext``. 2030 is that run's terminal year, so no
  capacity screen reads it in-horizon.

**WHAT IS NOT INVALIDATED.**

* **Every backcast keeper, byte-identical.** A backcast rebuilds its base fleet
  every year and never enters ``evolve_fleet``. Proved rather than argued: an
  on-recipe ``run_year(fleet_only=True)`` rebuild of all seven keepers across
  every solved year (23 keeper-years, CAISO/ERCOT/MISO/NEISO/NYISO/PJM/SPP) fires
  the guard **zero** times.
* **Every hindcast and crossover year**: ``apply_ccs_retrofit`` returns before any
  pricing below ``ccs_retrofit_available_year`` (2028), so the trigger cannot
  fire; the census found no legacy-form retrofit in any ``results/hindcast/``
  ledger.
* **The 14 RENAME-ONLY forecast rows** (NYISO ``d45r``/``d60``/``d65br``, CAISO
  ``d46``/``d60``/``d65br``, MISO ``s123/verify``, PJM ``s6-pjm/ledger``, ERCOT
  ``d65br`` 2029, and two later NEISO T3 conversions) convert an id **no later
  entry collides with**. No decision can move there — and in all 26 census rows
  the renamed id appears in **no other decision row in any year** (no retirement,
  no floor retention, no thermal addition), so the only bytes that move are
  inside the ``ccs_retrofits`` row itself: ``unit_id`` unchanged, plus the
  additive ``to_unit_id``.
* **54 of the 72 committed evolution bundles** carry no legacy-form retrofit at
  all and are untouched by construction.

**Two ``unit_id`` EXACT-TIE tiebreaks are stated rather than left implicit**,
because a rename can move a unit across a bit-identical tie (both are
pre-existing properties of HEAD, neither introduced here):
``retirements.py:2864`` (entry-competition sort, ``(-depth, unit_id)``) and
``adequacy.py:726`` (the D57 clearing stack, ``(offer, unit_id)``, PJM-armed
only). ``interchange/miso.py:846`` parses ``int(uid.rsplit("#"))`` but filters on
``_ref{imp,exp}_`` first, which a renamed id never matches — safe by
construction; ``legacy_bins.py:599/679`` are coal-only; ``eia860.py:2925`` runs
at base-fleet build, before any conversion exists.

Evidence: the census and disposition ``DESIGN-capx-d87-d88-s19-read-2026-09-08.md``
§2; the pre-registered gates and the G-DRIFT audit
``PRECOMMIT-capx-d88-2026-09-08.md``; the phase-0 guard-silence result, the
independent re-census and the screen's STOP table
``FINDING-capx-d88-2026-09-08.md``.

**Epoch 2026-09-08 — capx D87 / SCN ruling S19 (D-15): the CCS RETROFIT screen
consumes the clean-tier seam. NO KEY MOVES, AND THAT IS THE HAZARD.** No
``ScenarioConfig`` field is added, removed, re-defaulted or re-registered — the
repair threads an existing RUNTIME value (``clean_attribute_price_by_fuel``, the
prior year's clean-row duals) into a screen that had no parameter for it — so
``cache_key()`` hashes the same bytes before and after. Measured on the same
tree: the NYISO ``CES-T80`` campaign recipe keys ``eb1b0e1df942db47`` at the
arm's parent commit and at the arm, and neither ``ccs.py`` nor ``evolve.py`` is
a ``config.solve_surface`` registry module, so the D79 fingerprint is unmoved
too. A pre-fix bundle therefore sits at EXACTLY the key a post-fix run computes
and will be served to it — the same pure same-key class as the 2026-09-06b
entry below.

What moved: ``capacity_evolution/ccs.py``'s retrofit screen priced each
continuation's certificate through ``effective_eac_price_for_unit`` alone, which
folds the legacy per-fuel scalar and the exogenous premium and nothing else. The
clean-tier dual reaches the OTHER two price-driven screens through
``clean_attribute_price_by_fuel`` (``retirements.py`` step 3,
``new_entry.py`` step 5) but ``evolve_fleet`` never handed it to step 2. Since a
federal CES TARGET row carries a ZERO premium by construction
(``__post_init__`` refuses the two together), ``attr_post`` collapsed to the
``eac_price_gas_cc_ccs`` default of 0.0 and the row's dual — the $50/MWh ACP in
the campaign's own legs — bought the retrofit screen nothing, while pricing the
LP's certificates and both sibling screens normally. The fix folds
``clean_credit_for_zone`` into BOTH continuations through the existing ``max()``
(one certificate, several buyers, never a sum; rule 19 [R-ONE-MECH]), with zero
new fields and zero free parameters (rules 21 [R-DOF] / 24 [R-REGISTRY]).

**INVALIDATED — purge or re-solve before quoting: TWELVE bundles, named.** Every
``results/<ISO>/<key>/`` FORECAST-lane bundle whose horizon reaches **2028**
(``ccs_retrofit_available_year``) AND whose config puts a live clean-row dual on
``gas_cc_ccs``. At this commit that set is exactly the campaign's target-row
legs — ``results/scn-campaign-policy-2026-09-06/<ISO>/{CES-T80, ALL-CLEAN}`` for
CAISO, ERCOT, MISO, NEISO, NYISO and PJM — whose 2028-2030 retrofit sets,
``gas_cc``/``gas_cc_ccs`` capacity splits and CO2 rows are mis-stated. The
reconstructed per-year duals and the direction and cap-bounded magnitude of each
leg's correction are tabulated in
``docs/handoffs/PRECOMMIT-capx-d87-2026-09-08.md`` §2.5; the measured NYISO
correction is in ``FINDING-capx-d87-2026-09-08.md``. D87 re-solves none of the
other eleven and re-states none of the six ISO policy FINDINGs' numbers: that
re-statement is ROUTED to the SCN desk.

**NOT invalidated, each for its own reason:** (a) every BACKCAST bundle in every
ISO, on three independent gates — ``__post_init__`` refuses a target row in
``mode="backcast"``, a backcast rebuilds its base fleet each year and never
enters ``evolve_fleet``, and ``apply_ccs_retrofit`` returns at its first
statement below ``ccs_retrofit_available_year``; (b) every ``ff-t1h`` hindcast
(2021-2025) and every crossover horizon ending before 2028, on that same year
gate; (c) every PREMIUM (``CES-P*``) and VOLUNTARY leg — no clean row credits
``gas_cc_ccs`` there, so ``by_fuel`` carries no entry and ``max(x, 0.0) == x``
(the committed voluntary configs all take
``VOLUNTARY_ELIGIBLE_FUELS_DEFAULT``, which is wind/solar/offshore/geothermal);
and (d) **THE WHOLE MISO CLEAN-TIER FAMILY, including every ``ff-t1f-*/miso``
bundle and every ``miso-…-t1h`` hindcast.** (d) is the one a reader would guess
wrong: MISO's MI row is the only state tier whose ``qualifying_fuels`` admit
``gas_cc_ccs``, but its first statutory knot is **2035** and
``policy.clean_tiers._clean_tier_target`` returns 0.0 strictly before a tier's
first knot, while every committed config with ``miso_clean_tier_rows`` armed
ends at **2030**. Its dual is structurally zero in every committed year —
corroborated by ``scn-campaign-policy-2026-09-06/MISO/{CES-T80,ALL-CLEAN}``'s own
``duals.json``, which print MI at ``-0.0`` in all five years. MN cannot
substitute: its first knot is 2030 and its qualifying set excludes
``gas_cc_ccs`` outright. A FUTURE MISO run whose horizon reaches 2035 with the
tier armed WOULD be in scope; none is committed.

No keeper, sidecar, determination or dashboard row moves — no FF-2D verdict is
keyed to a target-row run, and committed artifacts are files, not cache lookups.

Recorded 2026-09-08 by capx D87, the lane that made the change
(``docs/handoffs/PRECOMMIT-capx-d87-2026-09-08.md`` §4, pushed before its screen
solve). This entry changes no key and no default.


**Epoch 2026-09-07 — capx D76-ARM-B / owner ruling Q58: the capacity screens'
PEAK becomes the hindcast year's OWN MEASURED peak, armed as the default posture
for every ISO. A KEY ADVANCE, NOT A SAME-KEY INVALIDATION — for HINDCAST
recipes only, and for no backcast and no plain forecast run at all.**

``capacity_screen_peak_measured_hindcast`` flips ``False -> True`` on the shared
``ScenarioConfig`` default, declared by APPENDING to
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` (its FOURTH entry) while the frozen
entry in ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`` stays ``"False"`` — the D44 /
D60 / D65-B (b'-1) route. **It lands in TWO halves**, and the second is what
makes the first affordable: ``__post_init__`` coerces the field back to that
frozen declaration whenever ``not config.hindcast``, the seam's own branch
predicate with the year term dropped. Without half 2 the flip re-keys 93 of the
190 committed run configs — **ten of them BACKCAST KEEPERS** — for behaviour
that is byte-identical, because a config resolving the new default no longer
equals the drop value and enters the hash.

**Measured at the arm over all 190 committed** ``run_config.json``
(``scripts/probes/capxd76arm_default_flip_key_census.py --variant b``, records
under ``docs/handoffs/d76armb/``, run against BOTH the pre-edit and the
post-edit tree and agreeing to the config): **34 keys move and every one of them
is a hindcast bundle the gate governs** — PJM 10, MISO 9, NEISO 6, NYISO 5,
ERCOT 3, CAISO 1 — with **ZERO backcast moves and ZERO non-hindcast forecast
moves**. All seven ``*-plain-backcast`` keys are unmoved
(``406cb30ad62bc27b`` ERCOT, ``efebcc735768c122`` CAISO, ``b10d58628ba3a057``
MISO, ``3a566deac3a85682`` PJM, ``cadaba3d344e84b9`` NYISO, ``27e80d27acd995de``
NEISO, ``989da50bbf0f99d8`` SPP) and all seven ``*-t1h-bare`` recipe keys
advance, which is the intended effect and is listed rather than counted:
``46d013cbf1f35d27 -> f238df2e5b1ef838`` (ERCOT), ``8f1c3766703a90c4 ->
28f4f62b90e2f74b`` (CAISO), ``1f92943f84f42fd0 -> 71156d9eb2ea896d`` (MISO),
``fb16fda2ddb0a94a -> f736025631d0d27e`` (PJM), ``ee6a3e764324f28f ->
ee0d44e7d6f26397`` (NYISO), ``5b292e24dd752ea4 -> 806f31b59b10c911`` (NEISO),
``7d1c3f080475310e -> 8acea51fd756a867`` (SPP).
``--no-capacity-screen-peak-measured-hindcast`` reaches the pre-arm posture and
KEEPS the pre-flip key — a property one committed artifact already exercises,
``results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm``, which recorded
the field explicitly ``false`` because it solved after D76 phase 1 registered it.

**Because the key advances, nothing is silently re-interpreted.** The 34 hindcast
bundles solved at the pre-flip default carry the SUPERSEDED screen operand under
their own keys and are re-solved by their own ISO's lane on its natural cadence
(Q57's own words, kept by Q58); this lane re-ran nothing and registered nothing.
Backcast behaviour is byte-identical by construction, so no keeper, sidecar,
determination or dashboard row moves. **The pinned default and backcast
``cache_key`` literals in** ``tests/regression/test_persisted_identity.py`` **do
NOT advance**: both are non-hindcast configs, half 2 coerces the field to the
frozen declaration there, and ``cache_key()`` drops it — measured identical
against ``origin/main``'s own resolved payload, field by field.

**WHY THE ROUTE CHANGED.** Owner ruling Q57 had authorized the flip alone under a
STOP requiring ZERO key moves. ``FINDING-capx-d76-arm-2026-09-07.md`` verified
that route and it fails STRUCTURALLY: under (b'-1) a registered field is dropped
IFF it equals its frozen declaration, so arming necessarily moves the resolved
value off that declaration and the armed configs enter the hash BY DESIGN —
which is the mechanism that stops a post-flip armed run being served the pre-flip
unarmed bundle. "Arm the gate" and "move no key" are the same sentence with
opposite signs. Q58 voided Q57's route and ruled **variant B** on the standard
the two immediate arms in this family actually met (D75-R-ARM: *"21 of 153
configs move, ALL PJM FORECAST"*; D78-ARM: *"zero non-PJM moves, zero backcast
moves … PJM forecast moves and is listed"*): **zero OFF-TARGET moves, in-scope
moves listed**.

Evidence: ``FINDING-capx-d76-2026-09-06.md`` (§2 the -23.3 % to +15.4 % operand
error, §4.2 the rule-19 consumer enumeration, re-verified complete at this HEAD),
``-p2-``, ``-p3-``; the route measurement ``FINDING-capx-d76-arm-2026-09-07.md``;
execution and every pre-declared number
``PRECOMMIT-capx-d76-arm-b-2026-09-07.md``, graded in
``FINDING-capx-d76-arm-b-2026-09-07.md``.

**Epoch 2026-09-06h — capx D78-ARM / owner ruling Q56: the retirement-screen
SECTOR GATE is armed for PJM. A KEY ADVANCE, NOT A SAME-KEY INVALIDATION — for
PJM's forecast recipes only, and for no backcast and no other ISO at all.**

``retirement_sector_gate`` is armed ``True`` through
``config/iso_configs.py::_pjm_config`` ``default_scenario_overrides`` — the
D57/Q44 → D67-ARM → Q55 pattern — **not** a flip of the shared ``ScenarioConfig``
default, which stays ``False`` (MISO's D53 arm sits on MISO's own ISOConfig the
same way and is untouched). So there is no
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` entry, no other ISO's key moves, and
a PJM plain backcast coerces the field back to ``False`` with its key unmoved at
``3a566deac3a85682``. The bare PJM T1-H recipe advances ``b518f5fe7d02f961`` ->
``fb16fda2ddb0a94a``; an explicit ``--no-retirement-sector-gate`` reaches the
pre-arm (Q55) posture and KEEPS ``b518f5fe7d02f961``. Two of the moved legs land
on keys that already carry a measurement: ``--no-pjm-vre-accreditation-vintage``
now resolves ``bb6a60239d69508b``, which IS D78-R2's measured arm, and the
``--no-`` pair of both reaches ``a9c66d8ea25acb9d``, the D67-ARM / D78-R2 graded
control.

Because the key advances, **nothing is silently re-interpreted**: the D67-ARM
bundle that held the bare ``pjm-t1h`` id keeps its own key
(``a9c66d8ea25acb9d``) under its own id and is re-keyed in
``register_forecast_run.py`` to ``pjm-t1h-pre-d78arm`` **when the armed re-solve
is registered** — that re-key lands WITH the registration, never before it, so
``pjm-t1h`` never names a bundle that does not exist. Measured over every
committed run config at the arm
(``scripts/probes/capxd78arm_iso_override_no_op_check.py``, records under
``docs/handoffs/d78arm/``, re-measured at HEAD 2026-09-07): of **173** committed
configs, the **25 PJM forecast** configs move and **all 148 others — every
non-PJM config of every ISO, and every backcast config including PJM's two —
are byte-identical**. The probe
differences the field's PRE-arm resolution against its POST-arm resolution
(both off the shipped path) rather than the committed value against the armed
value, because the field is already armed for MISO: nine pre-D53 MISO bundles
re-keyed against D53, not against this arm, and are listed, not counted. THREE
explicit control legs change meaning and are re-pinned in
``tests/unit/model/test_capacity.py`` with their inverses beside them (the D57
three-``--no-`` leg ``f1a9881ed29df6cb``, arm B's two-``--no-`` leg
``944c89de0a74ca63``, and ``--no-pjm-vre-accreditation-vintage`` at
``bb6a60239d69508b``); adding ``--no-retirement-sector-gate`` to each restores
its pre-arm literal exactly, so every pre-arm recipe stays both reachable and
identified. Evidence: ``FINDING-capx-d78r2-2026-09-06.md`` §§3–8,
``FINDING-capx-d78r3-2026-09-06.md`` §§3–5; execution and every pre-declared
key ``PRECOMMIT-capx-d78arm-2026-09-06.md`` §2.

**Epoch 2026-09-06g — capx D75-R-ARM / owner ruling Q55: PJM's wind and solar
are accredited at each delivery year's OWN published ELCC class ratings. A KEY
ADVANCE, NOT A SAME-KEY INVALIDATION — for PJM's forecast recipes only, and for
no backcast and no other ISO at all.**

``pjm_vre_accreditation_vintage`` is armed ``True`` through
``config/iso_configs.py::_pjm_config`` ``default_scenario_overrides`` — the
D57/Q44 → D67-ARM pattern — **not** a flip of the shared ``ScenarioConfig``
default, which stays ``False``. So there is no
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` entry, no other ISO's key moves, and
a PJM plain backcast coerces the field back to ``False`` with its key unmoved at
``3a566deac3a85682``. The bare PJM T1-H recipe advances ``a9c66d8ea25acb9d`` ->
``b518f5fe7d02f961``; an explicit ``--no-pjm-vre-accreditation-vintage`` reaches
the pre-arm posture and KEEPS ``a9c66d8ea25acb9d``.

Because the key advances, **nothing is silently re-interpreted**: the D67-ARM
bundle that holds the bare ``pjm-t1h`` id keeps its own key
(``a9c66d8ea25acb9d``) under its own id. Measured over every committed run
config at the arm (``scripts/probes/capxd75rarm_iso_override_no_op_check.py``,
records under ``docs/handoffs/d75rarm/``): of **153** committed configs, the
**21 PJM forecast** configs move and **all 132 others — every non-PJM config of
every ISO, and every backcast config including PJM's two — are byte-identical**.
FOUR explicit control legs change meaning and are re-pinned in
``tests/unit/model/test_capacity.py`` rather than left ambiguous (the D57
three-``--no-`` control keys ``1785cb6086cd2b15``, its four-flag form
``d2fe4e2b32aef073``, arm B's two-``--no-`` leg ``ab0237198cff24ad``, its
four-flag form ``05cdf4af2b9adef8``); adding ``--no-pjm-vre-accreditation-
vintage`` to each restores its pre-arm literal exactly, so every pre-arm
recipe stays both reachable and identified. Evidence:
``FINDING-capx-d75r-2026-09-06.md`` §3 / §4 / §5 / §8; execution and every
pre-declared key ``PRECOMMIT-capx-d75r-arm-2026-09-06.md`` §2.

**Epoch 2026-09-06f — capx D67-ARM / owner ruling Q52: the PJM adequacy
requirement's OPERAND becomes PJM's own published whole-RTO Reliability
Requirement. A KEY ADVANCE, NOT A SAME-KEY INVALIDATION — for PJM's forecast
recipes only, and for no backcast and no other ISO at all.**

``capacity_adequacy_requirement_published_by_iso`` is armed ``{"PJM": True}``
through ``config/iso_configs.py::_pjm_config`` ``default_scenario_overrides``
— the D57/Q44 pattern — **not** a flip of the shared ``ScenarioConfig``
default, which stays ``None``. So there is no
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` entry, no other ISO's key moves,
and a PJM plain backcast coerces the field back to ``None`` with its key
unmoved. The bare PJM T1-H recipe advances ``15a723ba3b6dc856`` ->
``a9c66d8ea25acb9d``; an explicit ``--no-capacity-adequacy-requirement-
published`` reaches the pre-arm posture and KEEPS ``15a723ba3b6dc856``, so
every pre-arm bundle's recipe stays both reachable and identified.

Because the key advances, **nothing is silently re-interpreted**: the D57-era
bundle that held the bare ``pjm-t1h`` id keeps its own key
(``f0e050e820c1159a``) under the preserved id ``pjm-t1h-pre-d67``, with its own
verdict standing. Two explicit control legs DO change meaning and are re-pinned
rather than left ambiguous: the three-``--no-`` D57 control now carries the
requirement armed and keys ``61dfbc5c48af076b``, and arm B's two-``--no-`` leg
keys ``2d5bebd2bceed991``; adding the fourth ``--no-`` flag restores
``c5ec052057905966`` / ``6ba67a81ed4d2ed6`` exactly. Evidence:
``FINDING-capx-d67-2026-09-06.md`` §4 / §6.1 / §7.1; execution and every
pre-declared key ``PRECOMMIT-capx-d67arm-2026-09-06.md`` §2, graded in
``FINDING-capx-d67arm-2026-09-06.md``.

**Epoch 2026-09-06e — capx D81: the PENDING owner-filed dated block and the
this-year CCS retrofit no longer sit in the D57 stack's $0 price-taking block
either — the same SAME-KEY semantic change as epoch 2026-09-06d, extended to
the two remaining channels that reached the same residual, again with ZERO
committed bundles in its blast radius.** Owner ruling Q53 ruled the must-offer
reading for the sector gate; the director extended it to the channels
``DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md`` §4 enumerates, because
PJM's must-offer requirement keys on *existing and in the footprint* and its
three exceptions (Manual 18 Rev 62 §5.4.1) do not include a filed plan that has
not yet taken effect. ``evolve_fleet`` now routes ``_dated_exempt`` and
``_retrofitted_ids`` to ``exit_exempt_unit_ids``, so ``exempt_unit_ids`` has no
producer. No ``ScenarioConfig`` field is added or changed, so no key moves.
What is invalidated: any bundle solved in **forecast mode** on an ISO whose
``capacity_market_supply_clearing_by_iso`` row is on (PJM alone at this date)
with ``fossil_announced_exits_enabled`` on.

  **CORRECTED 2026-09-06 by capx D67-ARM (this entry's blast radius was
  understated).** This clause continued "— and no such bundle is committed or
  registered anywhere (capx D57/D58/D78's probes were all deleted before merge
  under rule 29(c))". The statement about the deleted probes is right; it
  missed the one REGISTERED bundle. ``frontend/data/hindcast/pjm-2021-2025-
  realized-t1h-d57-clearing.json`` — the run holding the bare ``pjm-t1h`` key
  when D81 landed — records ``capacity_market_supply_clearing_by_iso =
  {'PJM': True}`` AND ``fossil_announced_exits_enabled = True`` at cache key
  ``f0e050e820c1159a``, i.e. BOTH of this epoch's arming conditions. It was in
  the blast radius. Repaired rather than merely noted: capx D67-ARM re-solved
  the shipped PJM posture at a HEAD that carries D81, registered it as the bare
  ``pjm-t1h``, and preserved the D57-era record verbatim at ``pjm-t1h-pre-d67``
  (epoch 2026-09-06f above). Nothing was re-scored and no verdict, gate,
  determination, marker or freeze file moved — the correction is a records act.
  Record: ``PRECOMMIT-capx-d67arm-2026-09-06.md`` §3.3.

What is NOT invalidated: every backcast of every ISO (a
backcast reaches neither step 1b nor the clearing), every clearing-off ISO
(with the clearing off the routing is byte-identical, asserted by test), and
every year below ``ccs_retrofit_available_year`` = 2028 on the retrofit limb,
where the set is empty by construction. Record:
``docs/handoffs/PRECOMMIT-capx-d81-2026-09-06.md`` §2 and
``FINDING-capx-d81-2026-09-06.md``.

**Epoch 2026-09-06d — capx D78 / owner ruling Q53 (reading 1): the
retirement-screen sector gate no longer removes a unit from the D57
capacity sell-offer stack — a SAME-KEY semantic change for
``retirement_sector_gate=True`` on a clearing-armed ISO, with ZERO committed
bundles in its blast radius.** The gated set moved from the screen's
``exempt_unit_ids`` (out of the screen entirely, hence a $0 price taker in
``Q_0``) to ``exit_exempt_unit_ids`` (evaluated, OFFERED at its net-ACR cap,
then partitioned out of ``margins`` before the exit decision — PJM's
must-offer requirement, Manual 18 Rev 62 §1.2 / §5.4.1). No ``ScenarioConfig``
field is added or changed, so no key moves. What is invalidated: any bundle
solved with ``retirement_sector_gate=True`` on an ISO whose
``capacity_market_supply_clearing_by_iso`` row is on — at this date PJM
alone, and the only such bundles (capx D58's two screen probes) were deleted
before merge under rule 29(c) and never registered. What is NOT invalidated:
every MISO bundle with the gate on (the ``miso-t1h`` keeper family — the
clearing is off there, and the D78 construction is byte-identical with the
clearing off, asserted by test), every gate-off bundle of every ISO, and every
backcast (the gate is coerced to its default in a backcast). Record:
``docs/handoffs/DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md`` §3.4.

**Epoch 2026-09-06c — capx D65-B / owner ruling Q47: the CCS-retrofit
fixed-cost SHAPE gate arms as the default posture (Act A) COUPLED with the
capture-island VOM adder's RE-IDENTIFICATION (Act B). A KEY ADVANCE, NOT A
SAME-KEY INVALIDATION** — and, unlike the two flip entries below, that is true
for EVERY config including the explicit-``False`` control arms, because half of
this change is a plain value change.

``ScenarioConfig.ccs_retrofit_fixed_cost_co2_scaling`` flips default ``False``
-> ``True``: the retrofit's two fixed-cost legs (ΔFOM $/MW-yr and the capture
VOM adder $/MWh) are scaled by the SAME ``k = captured / captured_ref`` seam 1
already applies to the island's capex, because both are TPC fractions in their
own published sources (ATB 2024 fossil methodology; NETL Rev 4a B31A->B31B.90
at 95.5 % fixed / 100 % variable). Declared — the THIRD entry in
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS``, frozen declaration left at
``False`` — so the registration guard's check 3 passes on the declaration.

``ScenarioConfig.ccs_retrofit_vom_adder`` moves ``8.0`` -> ``2.95`` $/MWh
(2026$), read off the ATB 2024 v4.0.0 basis the screen's other two cost legs
already use: (4.8 - 2.1) x 1.090947 = 2.95. The shipped 8.0 was
``needs-citation``, stated no dollar-year, and cited NETL Rev 4a, which
publishes 2.23 for this increment. This field is NOT a
``_CACHE_KEY_OPTIONAL_FIELDS`` member, so it has no drop value and **re-keys
every config unconditionally** — which is why the two acts produce ONE re-key
event and why the "NOT invalidated (a)" carve-out of the 2026-09-05 entry below
does NOT recur here.

**BOTH DEFAULT KEYS MOVE:** forecast default ``e5ecd4105ada3e58`` ->
``547053bdfccd4264``, bare backcast ``6a2845e50951394e`` ->
``f61891696e671969``. Every per-ISO bare key moves too; the full pre-declared
table is ``docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md`` §3, written before
the solve.

**Act A's drop-value mechanic is nonetheless INTACT, measured by decomposition**
(PRECOMMIT §3.1): holding the VOM at its shipped 8.0, an explicit
``ccs_retrofit_fixed_cost_co2_scaling=False`` hashes to ``e5ecd4105ada3e58`` —
exactly the pre-flip forecast default. The movement above is Act B's.

**INVALIDATED — re-solve before quoting:** every ``results/<ISO>/<key>/``
forecast bundle at a pre-2026-09-06c key **whose horizon reaches 2028**. A
one-time cache MISS, never a wrong answer. **NOT invalidated:** every BACKCAST
and every hindcast/crossover horizon ending before 2028, whose behaviour is
byte-identical because ``capacity_evolution/ccs.py::apply_ccs_retrofit`` returns
at ``if year < config.ccs_retrofit_available_year`` (2028) before any read of
EITHER field, and that call site is the only consumer of both in the source
tree. Their keys move; their answers do not. No keeper, sidecar, determination
or dashboard row moves; committed artifacts are files, not cache lookups.

**A CONSTRUCTOR REPAIR RIDES WITH THIS EPOCH, and it moves no key.** Act A's
flip made the pair (seam 1 EXPLICIT ``False``, seam 4 at its default)
unconstructible, which would have made the D50/Q42 CONTROL ARM unreachable and
broken reconstruction of six committed bundles. The pair resolution moved from
``__post_init__`` to ``_scenario_config_init``
(``_resolve_ccs_retrofit_fixed_cost_pair``), where the caller's explicitness is
visible: an explicit ``seam 4 = True`` without seam 1 still raises, while seam 4
at its default with seam 1 off DEMOTES to ``False`` — inert by construction
(``k = 1.0``), truthfully recorded, and dropped from the hash. No armed config
reaches the demoting branch, so no key moves by it. PRECOMMIT §4.

**Epoch 2026-09-06b — capx D77: the CCS-retrofit emission-rate seam. NO KEY
MOVES, AND THAT IS THE HAZARD.** No ``ScenarioConfig`` field is added, removed,
re-defaulted or re-registered — the repair adds one ``Generator`` attribute
(``ccs_capture_fraction``, a physical property of a unit, not a tunable, rule 24
[R-REGISTRY]) — so ``cache_key()`` hashes the same bytes before and after.
Measured on the same tree with only ``src/market_sim`` stashed: default
``e5ecd4105ada3e58`` and bare backcast ``6a2845e50951394e`` are UNMOVED, as is
every bare per-ISO 2026-2030 forecast key (ERCOT ``78b01278f2eb64eb``, CAISO
``41367ccc55859d4c``, PJM ``577a950add853227``, MISO ``a6b9ed663987311b``, NYISO
``81af4882eeda50f5``, NEISO ``f1b2dc5e9f2a47e3``). A pre-fix bundle whose horizon
reaches 2028 therefore sits at EXACTLY the key a post-fix run computes and will
be served to it — the 2026-08-31 entry's predicted recurrence, in its pure form.

What moved: a unit converted by the CCS retrofit screen kept its captured CO2
rate only until the next dispatch build. ``capacity_evolution/ccs.py`` applies
``emission_rate_co2 *= (1 - ccs_retrofit_capture_rate)`` at the retrofit, and
``data/fleet/campd_bins.py::apply_plant_emission_rates{,_v2}`` -- reached from
``data/fleet/assembly.py::build_dispatch_fleet``, which ``runner.py`` calls AFTER
``evolve_fleet`` in EVERY forecast year -- re-booked the host plant's measured
CAMPD rate over it. The match key is ``(plant_code, coarse fuel class)`` and
``fuel_class("gas_cc_ccs") == "gas"``, so a converted unit still matched its own
uncaptured host row; and on the CAMPD path ``build_dispatch_fleet`` opens with
``dispatch_fleet = fleet + inline_imports`` (a concatenation, not a copy), so the
override mutated the PERSISTENT generators and the loss carried into every later
year and into the next year's retirement and CCS screens. The override now books
the measured host rate and the unit's own capture together --
``co2 * (1 - gen.ccs_capture_fraction)``, one composition point (rule 19
[R-ONE-MECH]) -- so the measured input still enters every year (rule 13
[R-MEASURED]) and a captured unit is never restored to its uncaptured rate.
Zero DOF: the fraction is always one of the two already-registered capture-rate
fields. Measured defect: one NEISO unit read 0.3745 -> 0.3745 t/MWh across its
own 2028 retrofit while its heat rate rose 7.5101 -> 8.4113, and the ISO's
47-unit / 9.0 GW ``gas_cc_ccs`` class dispatched, priced its RGGI carbon adder
(``emission_rate x carbon_price``) and was accounted at 0.4149 t/MWh against
unabated gas_cc's 0.4663. It is a DISPATCH defect as well as an accounting one.

**INVALIDATED — purge or re-solve before quoting:** every ``results/<ISO>/<key>/``
**FORECAST-lane** bundle solved before this epoch whose horizon reaches **2028**
(``ccs_retrofit_available_year``) AND whose fleet retrofits at least one unit.
The committed census is 45 bundles across all six ISOs
(``docs/handoffs/FINDING-capx-d77-2026-09-06.md`` §8), whose CO2 rows, CCS
generation and -- wherever a carbon price applies -- merit order are mis-stated.
D77 re-solves none of them: that batch belongs to capx D65-B, at one HEAD,
carrying this fix.

**NOT invalidated:** every BACKCAST bundle in every ISO, and every hindcast or
crossover horizon ending before 2028. ``apply_ccs_retrofit`` returns at its first
statement, ``if year < config.ccs_retrofit_available_year``, so no such fleet
ever contains a converted unit; ``ccs_capture_fraction`` is 0.0 on every
generator and ``co2 * (1.0 - 0.0)`` is the pre-fix expression exactly. Asserted
with the persisted-identity / fleet-golden / backcast-inertness regression tests,
not by argument. No keeper, sidecar, determination or dashboard row moves.

Recorded 2026-09-06 by capx D77, the lane that made the change
(``docs/handoffs/PRECOMMIT-capx-d77-2026-09-06.md`` §3, pushed before its screen
solve; ``FINDING-capx-d77-2026-09-06.md``). This entry changes no key and no
default.

**Epoch 2026-09-06 — SCN-WS1c / owner ruling S2 (card D-1): the federal carbon
FLOOR. NO KEY MOVES, BY CONSTRUCTION — and the INVALIDATED SET IS EMPTY at this
commit.** No ``ScenarioConfig`` field is added, removed, re-defaulted or
re-registered, so ``cache_key()`` hashes the same bytes before and after
(measured: the pinned default ``e5ecd4105ada3e58`` is unmoved, as is every
per-ISO/per-bundle key). This is the pure same-key class the ledger exists for.

What moved: ``policy.cap_and_trade.resolve_carbon_program``'s FORECAST branch
used to return a **zero** program adder whenever a non-default
``carbon_price_path`` was set — a named federal RFF path REPLACED the state
cap-and-trade program. Ruling S2 makes it a floor instead:
``policy.carbon.resolved_base_trajectory_price`` now returns
``max(program trajectory, RFF path)`` on a program ISO, the path alone
elsewhere. ``carbon_price`` (scalar) keeps its Q26 replace semantics and
``carbon_price_delta`` its additive stage; both are untouched.

**INVALIDATED — re-solve before quoting: cached FORECAST-mode bundles on
CAISO, NYISO or NEISO carrying a non-"zero" ``carbon_price_path`` (equivalently
``policy_bundle="tight"``) and ``state_carbon_pricing=True``, solved before this
commit.** Their carbon signal was the RFF path where it is now the program
trajectory — on ``mid``, an increase of $15.98/tCO2 (2030) to $102.29/tCO2
(2050) depending on ISO and year, in all 25 horizon years.

**THAT SET IS EMPTY.** Measured over every tracked ``run_config.json`` in the
repository (90 files, ``git ls-files '*run_config.json'``): 73 forecast + 17
backcast, **all 90 carrying ``carbon_price_path="zero"``,
``policy_bundle="current"``, ``state_carbon_pricing=True``**, and **zero**
carrying a non-``"zero"`` path. No committed bundle reaches the changed branch,
so this epoch creates no stale evidence, retires no citation, and moves no
determination or dashboard row. It is recorded because the ledger's job is to
make a same-key semantic change visible even when — especially when — nothing
is currently stale: the next non-``"zero"``-path bundle solved on either side of
this commit is not comparable to one solved on the other.

**NOT invalidated:** every BACKCAST bundle in every ISO, including all six
keepers (``caiso251_arm_nomargin``, ``ercot248_two_config_keeper``,
``miso217_intermphys_B``, ``neiso99_joint_B``, ``nyiso192_astoria_panel``,
``pjm_debugb_inputclock_A``) — the changed branch is the ``else`` arm of
``if config.mode == "backcast"`` and was never reachable from a backcast, at any
path; every ERCOT / MISO / PJM bundle — no program adder applies (ERCOT and MISO
carry no program; PJM's has no price series, so its forecast adder is $0.0
before and after), leaving the path to apply alone exactly as it did; and every
``policy_bundle="rollback"`` construction — both operands of the ``max`` are
0.0 there, so the floor cannot resurrect a program the bundle switched off.

Recorded 2026-09-06 by SCN-WS1c, the lane that made the change
(``docs/handoffs/PRECOMMIT-scn-ws1c-2026-09-06.md`` §3,
``FINDING-scn-ws1c-2026-09-06.md`` §4; desk ledger
``docs/handoffs/scenario-desk-ledger-2026-09.md`` §2 ruling S2). This entry
changes no key and no default.

**Epoch 2026-09-05b — SCN-WS4a populates ``DATACENTER_ZONE_SHARE["MISO"]``
from MISO's published 2026 LTLF regional data-center decomposition
(``0fc2cc58``, ``config/constants.py``). NO KEY MOVES, BY CONSTRUCTION — and
the stored ``config.yaml`` cannot see it either.** The table is a
``constants.py`` siting input, not a ``ScenarioConfig`` field, so
``cache_key()`` hashes the same bytes before and after the change and
:func:`cache_config_disagreements` compares two identical configs: this is
the pure same-key invalidation class this ledger exists for. What moved:
``data/datacenter.py::datacenter_zone_shares`` served MISO the ``load_share``
default (``_load_share_zone_shares``) before this commit and serves the
published override after it. The ISO-total block MW is unchanged; its zonal
allocation is not (MISO-South falls from its 0.271 ``load_share`` to the
published 0.183, the difference landing on the North/Central-region zones).

**INVALIDATED — re-solve before quoting:** MISO **forecast-mode** bundles
solved before ``0fc2cc58`` (2026-09-05 23:15Z) with
``datacenter_load_path != "off"`` (the default is ``"mid"`` since FF-1F) are
STALE at their unchanged key: zonal load, and with it zonal dispatch, flows
and prices, change while the ISO total block does not. Committed PRE-EPOCH
evidence, retained as the record of what the harness did on the
``load_share`` split and never re-quoted as a current number: the
``frontend/data/hindcast/`` sidecars ``miso-2026-2030-d45r-remeasure`` and
``miso-2026-2030-s123-verify`` (both ``b1964e71``, 2026-09-04) and
``miso-2026-2030-d60-arm`` (``e7412237``, 2026-09-05 20:38Z), each recording
``datacenter_load_path: "mid"``; the capx track decides when they re-run.
**NOT invalidated:** every BACKCAST bundle in every ISO — the block is
forecast-only, ``validate_datacenter_config`` refuses a non-``"off"`` path in
backcast mode and ``ScenarioConfig.__post_init__`` coerces it off in
backcast/hindcast; every OTHER ISO — ERCOT and PJM already carried published
overrides and are byte-identical, CAISO, NYISO and NEISO are untouched (and
NEISO's block is 0 MW regardless); and MISO's system-level energy, which is
unchanged. No keeper, determination or dashboard row moves.

Recorded 2026-09-06 by SCN-MX-R-r2 on the scenario desk's explicit grant of
this one entry, not by the lane that made the change: ``results/cache.py``
was outside SCN-WS4a's file region and the lane routed the entry rather than
write it (``docs/handoffs/FINDING-scn-ws4a-2026-09-05.md`` §6, whose scope
paragraph the INVALIDATED / NOT-invalidated block above reproduces; desk
ledger ``docs/handoffs/scenario-desk-ledger-2026-09.md`` §4). Derivation of
the shares: that FINDING §2. This entry changes no key and no default.

**Epoch 2026-09-05 — capx D60 / owner ruling Q42: the CCS-retrofit capex
construction repair ARMS AS THE DEFAULT POSTURE for all six ISOs. A KEY
ADVANCE, NOT A SAME-KEY INVALIDATION**, by construction, exactly as the
2026-09-03 entry below. ``ScenarioConfig.ccs_retrofit_capex_co2_scaling`` flips
default ``False`` -> ``True``: the capture island is sized to the CO2 the host
actually captures (against the ATB reference host, 0.32319 t/MWh — the same
host ``new_entry._emerging_lcoe`` charges the ATB increment against) and
cogeneration hosts (``plant_group`` CC_CHP) leave the candidate set. Owner
ruling Q42 of the director sitting r#37 (2026-09-05) on the measurement
``docs/handoffs/FINDING-capx-d50-2026-09-04.md`` §8; execution record
``docs/handoffs/FINDING-capx-d60-2026-09-05.md``.

**BOTH KEYS MOVE:** default ``4c6b03ae098b6e3e`` -> ``e5ecd4105ada3e58``, bare
backcast ``8211c72bb1960adc`` -> ``6a2845e50951394e``. The field IS a
``_CACHE_KEY_OPTIONAL_FIELDS`` member and the flip leaves its FROZEN
declaration in ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`` at ``False``, so the
armed default enters the hash and takes its own key. The flip is declared —
the SECOND entry in ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` — so the
registration guard's check 3 passes on the declaration, not on silence.

**INVALIDATED — re-solve before quoting:** every ``results/<ISO>/<key>/``
forecast bundle at a pre-2026-09-05 key **whose horizon reaches 2028**. A
one-time cache MISS, never a wrong answer. **NOT invalidated:** (a) any arm
that passed ``ccs_retrofit_capex_co2_scaling=False`` EXPLICITLY — still equal
to the frozen declaration, still dropped, still addressing its pre-flip bundle
(measured: explicit-False hashes ``4c6b03ae098b6e3e`` / ``8211c72bb1960adc``);
(b) every BACKCAST and every hindcast/crossover horizon ending before 2028,
whose behaviour is byte-identical because
``capacity_evolution/ccs.py::apply_ccs_retrofit`` returns at its first
statement, ``if year < config.ccs_retrofit_available_year`` (default 2028),
which precedes every read of the flag — and that call site is the field's only
consumer in the source tree. No keeper, sidecar, determination or dashboard row
moves; committed artifacts are files, not cache lookups.

**Epoch 2026-09-03 — capx D44 / owner ruling Q30: the fossil announced-date
channel ARMS AS THE DEFAULT POSTURE. A KEY ADVANCE, NOT A SAME-KEY
INVALIDATION** — and, unlike every earlier entry here, that is true BY
CONSTRUCTION rather than by luck. Recorded anyway because it re-keys every
config in the program and a reader asking "why did my bundle stop resolving on
2026-09-03" will look here first. ``ScenarioConfig.
fossil_announced_exits_enabled`` flips default ``False`` -> ``True``: an
owner's filed EIA-860 Schedule-3 fossil retirement date becomes an exogenous,
vintage-gated step-1 input (reversal registry armed), and the economic
retirement screen runs on the residual UNDATED fleet. Owner ruling Q30 of the
director sitting r#31 (2026-09-02) on the measurement
``docs/handoffs/FINDING-capx-d42-fossil-dates-ab-2026-09-02.md``; execution
record ``docs/handoffs/FINDING-capx-d44-fossil-dates-arm-2026-09-03.md``.

**BOTH KEYS MOVE:** default ``cedadc285f8603b9`` -> ``4c6b03ae098b6e3e``, bare
backcast ``e006dfd7cef8bedd`` -> ``8211c72bb1960adc``. The field IS a
``_CACHE_KEY_OPTIONAL_FIELDS`` member — which under the OLD live-default drop
rule would have been the silent-collision case this ledger's 2026-08-31 entry
records in its pure form. It is not, because capx D24-R option (b'-1) (owner
ruling Q20) now drops a registered field at its FROZEN declaration in
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS``, which the flip leaves at ``False``.
The armed default therefore enters the hash and takes its own key. The flip is
declared — the FIRST entry in
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` — so the registration guard's
check 3 passes on the declaration, not on silence. **This is (b'-1) doing the
exact job it was landed for.**

**INVALIDATED — re-solve before quoting:** every ``results/<ISO>/<key>/``
forecast bundle at a pre-2026-09-03 key. A one-time cache MISS, never a wrong
answer: the key moved, so nothing can be mis-served. **NOT invalidated:** any
arm that passed ``fossil_announced_exits_enabled=False`` EXPLICITLY — that
still equals the frozen declaration, is still dropped, and still addresses its
pre-flip bundle (measured this session: explicit-False hashes
``cedadc285f8603b9`` / ``e006dfd7cef8bedd``). The D42 A/B legs are in that
class or carry the armed value explicitly, so the A/B's own record stands
without re-solve. Committed dashboard artifacts — sidecars, bundles, keeper
shards, determinations — are files, not cache lookups, and none moves.

**BEHAVIOUR moves in FORECAST mode ONLY, and that is the arming.** The channel
is loaded under ``config.mode == "forecast"`` in ``runner.run_scenario_iso``,
so ``announced_fossil_exits`` is empty in every backcast and both consumption
sites (``capacity_evolution/evolve.py`` limb 1b and
``data/fleet/assembly.py``'s first-year backlog) are no-ops there: **BACKCAST
IS BYTE-IDENTICAL** — dispatch, scores and every other ``run_config.json``
value are unmoved, no keeper or determination is affected and nothing needs
re-scoring. Forecast/hindcast bundles solved at the pre-flip default record the
SUPERSEDED posture; per Q30 that staleness joins the director's batched
post-repair re-measure decision (D44 re-solved nothing).

**Epoch 2026-09-02 — capx D41 CCS-retrofit fixed-cost re-identification (both
lanes, every ISO). THIS ONE IS A KEY ADVANCE, NOT A SAME-KEY INVALIDATION** —
recorded here anyway because it re-keys *every* config in the program and a
reader looking for "why did my bundle stop resolving on 2026-09-02" will look
here first. ``ScenarioConfig.fixed_om_gas_cc_ccs`` 25.0 -> 65.0 $/kW-yr and
``ScenarioConfig.ccs_retrofit_capex_kw`` 900.0 -> 1521.4 $/kW, both onto the
model's own NREL ATB 2024 (2026$) basis, repairing the two legs
``docs/handoffs/FINDING-capx-d30-45q-pace-2026-09-02.md`` §5 rows 6-7
adjudicated DEFECT-CANDIDATE. Owner-authorized in the D41 session sitting.

**BOTH KEYS MOVE:** default ``603c2498bf71d21d`` -> ``cedadc285f8603b9``, bare
backcast ``e027bc248c93c835`` -> ``e006dfd7cef8bedd``. Neither field is a
``_CACHE_KEY_OPTIONAL_FIELDS`` member, so both are hashed at every value and a
value change moves the key unconditionally — registration is not an available
remedy, and re-pinning is the sanctioned route rather than the forbidden one
(the "do NOT re-pin" rule targets an unregistered NEW field that is cache-
neutral at its default). Same shape as G-32, which moved the pin when it
flipped ``fixed_om_gas_cc`` 12 -> 30.

**INVALIDATED — re-solve before quoting:** every ``results/<ISO>/<key>/`` bundle
at a pre-2026-09-02 key, in both lanes. This is a one-time cache MISS, never a
wrong answer: the key moved, so nothing can be mis-served.

**BEHAVIOUR moves in FORECAST years >= 2028 ONLY, and that is the repair.** The
two fields have exactly two consumers, both in forecast-mode capacity evolution:
``capacity_evolution/ccs.py::apply_ccs_retrofit`` (gated on
``ccs_retrofit_available_year`` = 2028) and the ``_THERMAL_FOM`` lookup in
``capacity_evolution/retirements.py``, which reaches ``fixed_om_gas_cc_ccs``
only for a ``gas_cc_ccs`` unit. **BACKCAST IS BYTE-IDENTICAL:** no measured
backcast fleet contains a ``gas_cc_ccs`` unit and no backcast year reaches 2028,
so dispatch, scores and every other ``run_config.json`` value are unmoved; no
keeper, sidecar, determination or dashboard row is affected and nothing needs
re-scoring (committed artifacts are files, not cache lookups). Screen-grain
before/after: ``docs/handoffs/FINDING-capx-d41-ccs-fixedcost-2026-09-02.md``.

**Epoch 2026-08-31 — owner ruling R-A, the T1-H storage-entry Leg A arming
(every ISO's forecast lane).** ``ScenarioConfig.storage_entry_availability_gate``
and ``ScenarioConfig.storage_entry_cost_normalized_rank`` flip default
``False`` -> ``True`` (director sitting 2026-08-31, "Arm both", on the A/B
record ``docs/FINDING-t1h-capentry-phase1-ab-2026-08-30.md`` §4: both
kill-gates PASS, zero new DOF). The armed storage entry screen admits a
technology only at/after its measured first-US-operating year and ranks
clearing technologies per unit capital cost, so the storage BUILD MIX differs
— **behavioral in every forecast year with a storage-entry decision**.

**FORECAST: NO KEY MOVES, AND THAT IS THE HAZARD.** Both fields are
``_CACHE_KEY_OPTIONAL_FIELDS`` members, so ``cache_key()`` drops them at
whichever value is the LIVE default — ``cache_key(ScenarioConfig())`` is
``603c2498bf71d21d`` on both sides of the flip, measured this session. A
pre-flip UNARMED bundle and a post-flip ARMED config are therefore the same
key, and the armed run will silently serve the unarmed bundle. This is the
D-1/D-2 / FFR-3A collision in its pure form — the recurrence that epoch's
closing note predicted ("it will silently recur on the next default flip").
The inverse still holds and stays useful: an EXPLICIT
``storage_entry_availability_gate=False`` is now non-default and hashes
distinctly, so disarmed control arms remain separable.

**INVALIDATED — purge or re-solve before quoting:** any ``results/<ISO>/<key>/``
FORECAST-lane bundle solved before this epoch at the shipped (unarmed) default
whose horizon reaches a storage-entry decision year. Concretely and by
construction, the A/B's own control arm
(``ercot-2021-2025-realized-t1h-capentry-control``) is such a bundle: it solved
at the bare default, so its key is exactly the key an armed default run now
computes.

**NOT invalidated:** the A/B's REPAIR arm
(``ercot-2021-2025-realized-t1h-capentry-repair``) — it solved with both fields
passed EXPLICITLY, which was non-default at the time and hashed distinctly, so
it sits at its own key and IS the armed posture's registered evidence (no
re-solve is owed for the arming; a T1-H refresh re-baseline is the forecast
program's charter, not this lane's). Nor is any committed dashboard artifact:
sidecars and bundles are files, not cache lookups.

**BACKCAST: the key MOVES, and behaviour does not.** Unlike every prior flip in
this ledger, these two fields are ALSO coerced off in ``__post_init__`` when
``mode == "backcast"``. Coerced ``False`` is now NON-default, so both fields
re-enter the hash and every backcast key shifts (bare backcast config
``35b6dc12f97968f1`` -> ``e027bc248c93c835``, measured). The coercion is
load-bearing and stays: the runner reaches the storage-entry screen on year 2+
of any multi-year run, so without it a multi-year backcast would inherit the
armed screen. Consequence is a one-time cache MISS per backcast config, never a
wrong answer — backcast dispatch, scores and ``run_config.json`` are
byte-identical across the flip (both fields serialize ``False`` either side).
No backcast keeper, sidecar or determination is affected; nothing needs
re-scoring.

**Epoch 2026-08-15 — nyiso-136 collapse of the NYISO market-solar in-service
DATE basis gate to unconditional (NYISO only, both lanes).** The nyiso-133 gate
``ScenarioConfig.nyiso_solar_registry_cod_dates`` is DELETED (rule 26
``[R-DELETE]``, owner ruling in session nyiso-136, 2026-08-15) and the basis it
selected is now the only basis: ``data.renewables`` always calls
``load_market_solar_monthly(..., cod_basis=True)``, so every NYISO run ramps
each registered market-solar plant on its EIA-860 ``Operating Month`` (metered
commercial start) instead of the Gold Book Table III-2a ``In-Service Date`` (a
registration / interconnection-service date that leads it). Promoted to keeper
at nyiso-135 as ``2026-08-08-nyiso-133-cod-arm``; this epoch is the DEFAULT
following the keeper.

**NO KEY MOVES, AND THAT IS THE HAZARD.** The field was registered in
``_CACHE_KEY_OPTIONAL_FIELDS`` and is retired into
``_CACHE_KEY_RETIRED_FIELDS`` at the same ``False`` it carried, so
``cache_key(ScenarioConfig())`` stays ``603c2498bf71d21d`` across the change by
construction — the D-13 / FFR-3A same-key collision in its pure form. A NYISO
bundle solved before this epoch under the Gold Book basis and one solved after
under the EIA-860 basis hash IDENTICALLY, and nothing in the path can tell them
apart.

**INVALIDATED — re-solve before quoting:** every ``results/NYISO/<key>/`` bundle
solved before 2026-08-15, in BOTH lanes. Concretely and declared by the owner
when the collapse was ruled: the NYISO forecast lane's **11 committed
``nyiso-*`` hindcast sidecars** under ``frontend/data/hindcast/`` are now stale
w.r.t. HEAD (rule 15's separate namespace — the forecast lane's own governance
decides when they are re-run; they stand as PRE-EPOCH evidence until then).

**NOT invalidated:** any other ISO — the mechanism reads a NYISO-only artifact
and the loader hard-errors on any other ISO (rule 25 ``[R-ISO-SCOPE]``); NEISO
carries the identical Tier-3 posture and is explicitly NOT covered. Nor is the
designated keeper ``2026-08-08-nyiso-133-cod-arm``, which already solved with
the flag ``True`` in its own ``run_config.json`` and is therefore ALREADY on the
post-epoch basis — its paired control ``2026-08-08-nyiso-133-cod-control`` is
pre-epoch by construction and is retained as the A/B's baseline, not as a
current-basis run. Registered bundles carrying an explicit
``"nyiso_solar_registry_cod_dates": false`` in their committed ``run_config``
are historical records of a basis that no longer exists; they are read, never
replayed, and their recorded flag is inert.

**Epoch 2026-08-14 — D-31 ERCOT solar queue-cap adoption (ERCOT forecast only).**
``capacity_market.QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"]`` is re-derived from
the post-2020 EIA-860 demonstrated-COD record, ``5.0 → 8.0`` GW/yr (owner
decision D-31, signed 2026-08-13; derivation
``docs/FINDING-rc-ercot-solar-queue-cap-2026-08-11.md``, prereg ``d938f29`` /
measurement ``6e6e50b``; adoption
``docs/handoffs/d31-adopt-2026-08-13.md``). A **constants-level** change with no
``ScenarioConfig`` field, so **no key moves** — measured: ``ScenarioConfig()``
hashes to ``603c2498bf71d21d`` after the change, identical to the pinned default
key, and the ERCOT forecast config hashes to the same value. **This is the
worst form of the D-13 hazard**: an ERCOT forecast solved at 8.0 collides with a
pre-change 5.0 bundle under a byte-identical key, and nothing in the path can
tell them apart.

*Invalidated:* cached **ERCOT forecast-mode** bundles — plain forecast,
``hindcast=True``, and the T1-X crossover / T1-FF full-forward legs — solved
before this commit, in every year the cap can bind. It **is** behavioral, not
cosmetic: FFR-9C §4.2 established this cap binds from into-2024 in both staged
arms, margin-independently across $51–$2,420, so it was the sole constraint
holding ERCOT forecast solar entry down. Pre-change ERCOT forward sidecars under
``frontend/data/forecast/`` are **historical record — the evidence of what the
harness did at 5.0 — and must never be used as the baseline for a post-change
comparison.** A re-based ERCOT forecast leg must be re-solved, not diffed
against them.

*NOT invalidated:* **every other ISO** (only the ERCOT solar cell moved; ERCOT
wind and the ISO-total ``QUEUE_CAP_GW`` are untouched), and **every backcast
bundle and every keeper in every ISO**. The backcast calibration lane does not
read this constant at all: ``scripts/run_calibration.py::run_year`` builds each
year's fleet with ``fleet.build_base_fleet`` and never calls ``evolve_fleet``
or ``capacity_evolution.new_entry``, so no keeper — ERCOT's included — can have
formed on the old value.

**Epoch 2026-08-09 — FFR-9A hindcast storage-fleet vintage seed. NO KEY MOVES
ANYWHERE; EVERY CAPACITY-HINDCAST BUNDLE IS INVALIDATED (AGAIN).** The
FFR-3V-FIX epoch below corrected the hindcast wind/solar pools; the storage
base fleet had the SAME leak one seam over: a capacity hindcast
(``mode="forecast"`` + ``hindcast=True``) failed the runner's
``mode == "backcast"`` test and seeded its storage base fleet from the
present-day forward scalar (``STORAGE_BASE_FLEET_MW``, ERCOT mid 17,000 MW)
even though ``set_eia860_vintage`` had already pointed every EIA-860 loader at
the run's vintage snapshot. ``run_scenario`` now resolves the seam through
``model.storage.measured_storage_base_fleet_active``: a hindcast with a
committed ``eia860_vintage_year`` seeds from the vintage EIA-860 measured
storage fleet (``load_eia860_storage`` at start_year, battery + pumped
storage), in every ISO. Vintage-2020 seed change (MW, battery + PS): ERCOT
17,000 → 223; CAISO 16,994 → 2,022; PJM 5,603 → 5,358; MISO 2,887 → 2,142;
NYISO 1,490 → 1,308; NEISO 2,569 → 1,924. **No ``ScenarioConfig`` field was
added, removed or re-defaulted** — the governing field is the existing
``storage_measured_base_fleet`` (default on, already
``_CACHE_KEY_OPTIONAL_FIELDS``-registered) and the switch is the existing
``hindcast`` × ``eia860_vintage_year`` pair — so no key moves and the pinned
default key is unchanged. See
``docs/handoffs/ffr-9a-storage-vintage-seed-2026-08-09.md``.

*Invalidated:* **every cached bundle with ``hindcast=True`` and a committed
``eia860_vintage_year``** — T1-H plain hindcasts, T1-X crossovers, T1-FF
full-forward legs, in every ISO — at any commit before this epoch. Their base
storage fleet, and therefore the storage-AS term of every ERCOT screen's E1
reserve quantity, the entry/retirement margins and every ledger row
downstream, were formed on the inflated seed (FFR-8B §3: +7.3–8.8 GW at p1 on
E1's reserve quantity; §2.3: ~30 GW of storage power by the 2024 solve vs
~10 GW actual). The committed ``frontend/data/hindcast/`` sidecars — the
FFR-8B re-base ``ercot-2021-2025-t1ff-armr-ffr8b-base`` included — are
pre-epoch evidence: the historical record of what the harness did, not
re-runnable results.

*NOT invalidated:* **every backcast bundle, every keeper, and every plain
forecast bundle.** The backcast leg of the seam is byte-identical (same field,
same frozenset scope, same loader call), and a plain forecast
(``hindcast=False``) keeps the scenario scalar even when an
``eia860_vintage_year`` is set, mirroring the runner's vintage-arming
predicate. All three no-op halves are pinned by test
(``tests/unit/model/test_storage.py::TestHindcastStorageVintageSeed``).

**Epoch 2026-08-08 — FFR-3V-FIX hindcast renewable-pool vintage seed. NO KEY
MOVES ANYWHERE; EVERY CAPACITY-HINDCAST BUNDLE IS INVALIDATED.** A capacity
hindcast is ``mode="forecast"`` + ``hindcast=True``, so ``data.renewables``
skipped its backcast branch and seeded the wind/solar pools from the
present-day ``RENEWABLE_INSTALLED_MW`` constant — post-vintage information in a
run whose whole premise is the vintage cutoff, and a base the evolution
channels then ADD to. ``load_renewable_profiles`` now seeds a hindcast from the
run's own ``eia860_vintage_year`` EIA-860 measured year-end fleet, read AT the
vintage year (so ``_add_proposed_capacity`` cannot graft the vintage's own
proposed pipeline onto the base pool) and with the intra-year commissioning
ramp off. **No ``ScenarioConfig`` field was added, removed or re-defaulted** —
the switch is the existing ``hindcast`` × ``eia860_vintage_year`` pair — so no
key moves and the pinned default key is unchanged. Vintage-2020 seed change
(MW, wind / solar): ERCOT 42,000/38,000 → 27,541/4,864; CAISO 6,330/24,920 →
5,776/14,615; PJM 11,000/14,000 → 10,154/4,550; MISO 32,000/7,000 →
26,050/2,048; NYISO 2,400/1,500 → 1,989/664; NEISO 1,400/2,700 → 1,500/1,519.
The direction is not uniform — at vintage 2023 MISO solar goes 7,000 → 7,348
and NEISO wind 1,400 → 1,538 — and it is adopted in both directions (rule 14
[R-ACCURATE]). See ``docs/handoffs/ffr-3v-fix-2026-08-08.md`` and the finding
it closes, ``ffr-3v-miso-entry-screen-2026-08-04.md`` §6.1.

*Invalidated:* **every cached bundle with ``hindcast=True`` and a committed
``eia860_vintage_year``** — the T1-H plain hindcasts, the T1-X crossovers and
the T1-FF full-forward legs, in every ISO — at any commit before this epoch.
Their base VRE pools, and therefore every price, entry/retirement margin and
ledger row downstream, were formed on the inflated seed. The 143 committed
``frontend/data/hindcast/`` sidecars are pre-epoch evidence; they stand as the
historical record of what the harness did, not as re-runnable results.
**Specifically flagged for the manager (FFR-8A-P3 coordination):** the ERCOT
control-arm numbers the FFR-8A prereg §1.3 reproduces from the FFR-5D-M record
go stale for any ERCOT hindcast RE-RUN at or after this commit.

*NOT invalidated:* **every backcast bundle, every keeper, and every plain
forecast bundle.** A backcast never reached the changed branch (it already
resolves its own year's EIA-860 month-end capacity), and a plain forecast has
``hindcast=False``, so it keeps ``RENEWABLE_INSTALLED_MW`` even when an
``eia860_vintage_year`` is set — the runner arms the vintage switch only for a
backcast or a hindcast, and the seed override is gated to match. Both halves
are pinned by test
(``tests/unit/data/test_renewables.py::test_plain_forecast_ignores_the_vintage_seed``
and the backcast/forward pair that predates this change).

**Epoch 2026-08-04d — FFR-4C §45 wind-PTC statutory window (owner decision
D-13). NO KEY MOVES AT THE DEFAULT.** The new-entry screen's wind LCOE now
levelizes the §45 PTC over ``min(10 statutory years, book life)`` instead of
crediting the full rate for the plant's whole 30-year book life
(``docs/handoffs/ffr-4c-wind-ptc-window-2026-08-04.md``; the defect and its
arithmetic: ``ffr-3v-miso-entry-screen-2026-08-04.md`` §6.2). The window is the
new ``ScenarioConfig.ira_ptc_credit_window_years`` (default 10, statutory —
26 U.S.C. §45(a)(2)(A)(ii)), registered in ``_CACHE_KEY_OPTIONAL_FIELDS``, so a
run at the statutory default hashes exactly as a pre-4C run did — measured:
the default key is byte-stable at ``603c2498bf71d21d``, and the registration
drops the field at its live default from EVERY config's hash, so no existing
key moves anywhere — while wind entry economics CHANGED (effective screened
PTC $26.00 → $13.63/MWh at the shipped wind cost record, factor
CRF(30)/CRF(10) = 0.5243). This is the deliberate same-key-invalidation form
the 2026-08-03 D-1/D-2 entry predicted would recur; per that entry's inverse
clause, an EXPLICIT ``ira_ptc_credit_window_years=None`` control arm is
non-default, hashes distinctly (``5da240df77d9a933`` on the otherwise-default
config) and reproduces the pre-4C unwindowed crediting exactly.

*Invalidated:* every cached bundle produced in **forecast mode**
(``mode="forecast"``, including ``hindcast=True`` capacity-hindcast and T1-X
crossover legs) at a commit before this epoch whose evolution reaches the
entry screen — its wind entry margins, decisions, and every ledger row
downstream of them carry the unwindowed credit. Purge exactly as the
2026-08-02 entry below directs (and heed its tracked-file warning).

*NOT invalidated:* **every backcast bundle and every keeper.** The screen-side
PTC sites (``compute_lcoe`` / ``apply_ira_credits_to_lcoe``, now both
delegating to ``wind_ptc_levelized_per_mwh``) are consumed only by
forecast-mode capacity evolution, which does not run in a backcast (the
2026-08-03 entry's clause). The DISPATCH-side PTC offer — the flat
``-ira_ptc_wind`` wind MC from ``compute_dispatch_credits`` and the
default-off ``wind_ptc_vintage_offers`` — is untouched on every path.

**Epoch 2026-08-04c — FFR-4D CAISO base-fleet re-vintage. NO KEY MOVES; CAISO
BUNDLES IN BOTH MODES ARE INVALIDATED.** Three CAISO-scoped changes
(``docs/handoffs/ffr-4d-caiso-fleet-vintage-2026-08-04.md``), all of which move
CAISO output under **unchanged cache keys**:

* **``STORAGE_BASE_FLEET_MW["CAISO"]`` re-vintaged** — ``low/mid/high``
  ``6,000 / 8,000 / 12,000`` → ``11,590 / 15,450 / 19,260`` MW, re-derived by
  the registry's OWN documented EIA-860 construction (the one that already
  reproduces PJM/MISO/NYISO/NEISO exactly) on the committed EIA-860 2025 Early
  Release. A **constants-level** change with no ``ScenarioConfig`` field, so no
  key moves. **Behavioral in CAISO forecast mode** (the base-year storage fleet
  nearly doubles).
* **``RENEWABLE_INSTALLED_MW["CAISO"]`` re-vintaged** — wind ``7,000 → 6,330``
  and solar ``22,000 → 24,920`` MW, from the same EIA-860 release. Also
  constants-level, also no key move. **Behavioral in CAISO FORECAST mode only**:
  ``data.renewables`` reads this registry only when ``mode != "backcast"``; a
  backcast already takes that year's EIA-860 month-end capacity.
* **``storage_measured_base_fleet`` added, default ``True``** — a CAISO backcast
  now resolves its storage base fleet as of its solve year from EIA-860
  (``model.storage.load_eia860_storage``) instead of the flat forecast scalar.
  Registered in ``_CACHE_KEY_OPTIONAL_FIELDS``, so the key does NOT move — this
  is the default-flip hazard the entry below describes, entered DELIBERATELY and
  recorded here because the ledger is the only surface that can see it.
  **Behavioral in CAISO backcast mode**: the fleet goes from a flat 8,000 MW to
  the measured 7,492 / 11,131 / 15,448 MW at year-end 2023 / 2024 / 2025.

**The same-key collision is MEASURED, not asserted.** FFR-4D solved both arms of
the CAISO 2026-2030 forecast at one head — control (pre-FFR-4D constants) and
treated — and **both resolve to the SAME key** ``35b0a89be0c07483`` while
producing materially different output: cumulative ``reserve_backstop`` additions
14,043.6 MW vs 8,186.3 MW, FC-2 row 4 65.48 % vs 52.51 %, and invariant ``I3``
FAIL vs PASS. The arms stayed clean only because each had its own ``--out-dir``;
sharing one would have made the second run silently re-use the first's bundle.
This is the first entry in this ledger whose collision is demonstrated by a
solved A/B rather than inferred from the registration mechanics.

*Invalidated:* **every cached CAISO bundle, in BOTH modes** — forecast bundles
(all three changes) and backcast bundles (the third). **The designated CAISO
keeper ``2026-08-04-caiso-172-measured-path15`` — and every CAISO keeper before
it — was solved on the flat 8,000 MW scalar, so its committed metrics are
PRE-EPOCH**; it needs a re-solve
and a re-gate in the CAISO lane before its numbers are quoted again. That is
stated as an open, owed item in the FFR-4D handoff §7, not as a completed one.

*NOT invalidated:* **every other ISO, in both modes.** All three changes are
CAISO-scoped by construction — two are CAISO rows of per-ISO registries, and the
third resolves through ``STORAGE_MEASURED_BASE_FLEET_ISOS``, which contains
CAISO alone. ERCOT/PJM/MISO/NYISO/NEISO keepers are untouched (rule 25
[R-ISO-SCOPE]); ERCOT's own hand-entered storage row is routed, not changed.

**Epoch 2026-08-04b — FFR-3U bridge-seam fix + the D-11 two-key quarantine. NO
KEY MOVES; TWO KEYS ARE PERMANENTLY REFUSED.** The seam fix
(``docs/handoffs/ffr-3u-bridge-seam-2026-08-04.md``) scopes the runner's
un-bridging clause to genuine T1-X crossover forward years, so a T1-FF window
whose boundary sits at its own base year again BRIDGES 2022 (and 2026) instead
of solving them. It is a guard change, not a mechanism: **no ``ScenarioConfig``
field was added, removed or re-defaulted, and all seven measured keys — the
default plus the six per-ISO 2023 backcast keys — are byte-identical before and
after** (default ``603c2498bf71d21d``; ERCOT ``df386bca96a1d288``, CAISO
``a9afddae291525c1``, PJM ``9834b2018b598423``, MISO ``2a1252c3acae89e9``,
NYISO ``fd15030b3ee60f11``, NEISO ``5b1633171fead559``).

*Invalidated:* **exactly two bundles**, ``b99600bceb8cb6b8`` and
``5c352508039513da`` — FFR-3Q's two ERCOT base-2021 T1-FF arms, which solved
2022 (a validation-tier holdout) under an active freeze. Because the fix moves
no key, the same config still hashes to them, so the refusal is mechanical
rather than documentary: see :data:`CONTAMINATED_CACHE_KEYS` and
:func:`assert_cache_key_uncontaminated`, enforced at ``get_cache_path``.
Owner decision D-11 condition 2.

*NOT invalidated:* everything else. No backcast bundle, no keeper, no T1-H,
T1-X or base-2023 T1-FF leg is touched — every one of those postures realizes
the identical solve-year set before and after (measured across seven postures in
``tests/scoring/test_full_forward_hindcast.py::TestBridgeSeam``). The only
behavioural change is that a posture which was *illegal to run at all* now
bridges instead of solving.

**Epoch 2026-08-04 — D-10 warm-start OFF for forecast bundles. THIS ONE IS A KEY
ADVANCE, NOT A SAME-KEY INVALIDATION — recorded here anyway because it is the
entry a reader looking for "why did every forecast key move on 2026-08-04" will
come to.** Owner decision D-10 (sitting ``ffr-owner-sitting-2026-08-02.md``
Addendum K.3, implemented by FFR-3T,
``docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md``): every shipped forecast
runner now passes ``forecast_xyear_warmstart=False`` explicitly, so a resumed
forecast solves its first post-kill year the same way its control does — cold —
and the kill-resume drill (FF-3E part c) is structurally passable.

*Cause:* the flag is a ``_CACHE_KEY_OPTIONAL_FIELDS`` member, so an EXPLICIT
non-default ``False`` enters the hash. **Measured, all six ISOs x four shipped
forecast configs (T1-F / T1-H / T1-X / golden-posture battery): 24 of 24 keys
MOVED** — e.g. ERCOT T1-F ``e8ce5b85cc254830 -> 02d559f6a00f24b7``, NEISO T1-H
``cee8181a253afd6a -> 688dd67264951c7e``. Because the keys move, **no purge is
required for correctness**: a cold post-D-10 run cannot be served a warm
pre-D-10 bundle — they are addressed differently. Pre-D-10 warm forecast
bundles simply become unreachable by the shipped runners; delete them to
reclaim disk, using the tracked-file warning below, or leave them.

*Why this is NOT expressed as a default flip, which is the form the signed
decision's coordination note anticipated.* Both halves of a default flip were
measured at implementation and both exceed the decision:

* **forecast keys would NOT have moved.** ``cache_key`` drops a registered
  field at the LIVE default, so a post-flip ``False`` default hashes exactly as
  the pre-flip ``True`` default did — all 24 keys byte-IDENTICAL across the
  simulated flip, i.e. a cold run silently re-using a warm bundle. That is the
  FFR-3A blocker-4 same-key invalidation this ledger's 2026-08-03 entry
  describes, recurring exactly as that entry predicted it would.
* **backcast keeper keys WOULD have moved.** Every keeper's ``run_config.json``
  carries an explicit ``true``, which becomes non-default after a flip: all six
  moved (ERCOT ``f95a5d2aab761873 -> 86cdfc027116b309``, PJM
  ``c20ec90ee9626b07 -> c562ac25bb545281``, and so on).

*NOT invalidated:* **every backcast bundle and every keeper.** The six keeper
cache keys are byte-identical before and after (ERCOT ``f95a5d2aab761873``,
PJM ``c20ec90ee9626b07``, CAISO ``df6220a243add2ad``, NYISO
``c3b175a9fcf4af8d``, NEISO ``6ff540e9a9ee3b2f``, MISO ``dfe9d5c68e15c54c``),
the pinned default key is unmoved at ``603c2498bf71d21d``, and the backcast
solve PATH is untouched: ``run_calibration_full.py`` passes no explicit
``xyear_warmstart``, so the calibration lane still resolves cross-year warm
start from ``MARKET_SIM_WARMSTART_XYEAR`` (default ON) exactly as before.

**Epoch 2026-08-03b — FFR-SC NYISO demand-anchor re-derive (NYISO forecast only).**
``constants.DEMAND_GROWTH_RATES["NYISO"]`` is re-derived from the 2026 Gold Book
(``docs/handoffs/ffr-sc-transmission-ab-2026-08-03.md`` §7): mid near
``0.018 → 0.0122``, long ``0.012 → 0.0127``, low ``0.008/0.006 → -0.0024/0.0028``,
high ``0.030/0.020 → 0.0263/0.0196``. A **constants-level** change with no
``ScenarioConfig`` field, so **no key moves** — measured: ``ScenarioConfig()``
hashes to ``973a0acdef818e91`` both with and without it (the move from the
ledger entry below's ``603c2498bf71d21d`` is upstream field additions, not this).

*Invalidated:* cached **NYISO forecast-mode** bundles (including ``hindcast=True``
and T1-X crossover legs) solved before this commit — their demand trajectory is
the superseded 2025-Gold-Book one. *NOT invalidated:* every other ISO (only the
NYISO row moved), and **every backcast bundle in every ISO** — the backcast path
takes measured load and never reads this table, so no keeper is touched. The
concurrent ATB pin move (v3.0.0 → v4.0.0) invalidates nothing at all: every
derived constant is byte-identical under both versions.

**Epoch 2026-08-03 — FFR Wave-2 constants + the D-1/D-2 owner default flips.**
Taken at FFR-3A step 0 (`docs/handoffs/ffr-t1-regate-2026-08-02.md`), clearing
the epoch debt the owner sitting recorded as outstanding
(`ffr-owner-sitting-2026-08-02.md` Addendum B.6, "FFR-3A must clear this debt
before its consolidated battery — it is now a concrete item, not a
hypothetical"). Three causes, all of which move forecast output under
**unchanged cache keys**:

* **FFR-2C net-CONE re-anchor** (`ffr-2c-net-cone-currency-2026-08-02.md`,
  commits `5dcba9c` PJM / `aaa6a25` NYISO) — a **constants-level** change that
  landed AFTER the single 2026-08-02 bump. Two forward net-CONE vintages are
  re-anchored from their published instruments: **PJM 2027/28 → 2028/29
  (88.520 → 118.877 $/kW-yr, +34.3 %)** and **NYISO 2025-26 → 2026-27
  (+14.1 %)**. No ``ScenarioConfig`` field changed, so no key moved.
  **Behavioral** in every forecast year the new vintage governs (PJM: solve
  year 2028+), through all three capacity screens, which price on the one
  ``capacity_price_per_firm_mw_yr`` seam. PJM additionally gains a published
  price floor that removes the curve's zero-cross from 2028.
* **Owner decision D-1** (this session) — ``retirement_rule`` default
  ``"legacy"`` → ``"pipeline"``. **Behavioral in every forecast year** (a
  different retirement decision rule).
* **Owner decision D-2** (this session) — ``entry_rate_limits`` and
  ``entry_commissioning_lag`` defaults ``False`` → ``True``. **Behavioral in
  every forecast year** (rate-limited entry, +2-year COD lag). The same commit
  fixed a latent ``TypeError`` in the growth-ladder seed that the arming made
  reachable (``runner.py``), so no pre-flip cache of an armed run can exist.

**Why D-1/D-2 are same-key invalidations and NOT key advances — correcting a
premise in the signed packet.** The sitting's D-1 section states the field is
"cache-key-registered at non-default, so the flip moves forecast cache keys by
construction — no silent reuse". **That is not how the registration behaves.**
``cache_key()`` drops a ``_CACHE_KEY_OPTIONAL_FIELDS`` member when it equals
``getattr(ScenarioConfig(), name)`` — the **LIVE** default, recomputed on every
call, not a frozen sentinel. Flipping such a field's default therefore drops the
NEW value from the hash and the key does **not** move: measured this session,
``cache_key(ScenarioConfig())`` is ``603c2498bf71d21d`` both before and after
all three flips. A pre-flip legacy-rule bundle and a post-flip pipeline-rule
config are the same key. The inverse also holds and is useful: an EXPLICIT
``retirement_rule="legacy"`` is now non-default and hashes distinctly
(``0e49083ebacb2612``), so control arms in the FFR-3A battery are safely
separable. **Structural note for any future default flip of an optional-
registered field: it will silently recur, and the ledger is the only thing that
can see it.**

*Invalidated:* every cached bundle produced in **forecast mode**
(``mode="forecast"``, including ``hindcast=True`` and T1-X crossover legs) at a
commit before this epoch — in particular every FC-3 citation in
``ff-t1-gate-2026-07.md`` §4.1, which FFR-2E already flagged as pre-epoch legs.
Purge exactly as the 2026-08-02 entry below directs.

.. warning::

   **Purge only what git does not track.** The ``find ... -delete`` loop below
   is safe for the directories it names, but ``results/`` also holds COMMITTED
   evidence bundles from earlier lanes (e.g. ``results/ff2b-after/``,
   ``results/ffr1c/`` — registered ``evolution_<year>.json`` and
   ``full_horizon_summary.json`` artifacts cited by their handoffs). Extending
   the loop to those directories deletes tracked files: FFR-3A did exactly that
   and had to ``git checkout -- results/`` to restore 410 of them. Check
   ``git status --short`` after any purge, and restore anything showing ``D``.
   The actual invalidated artifacts are the gitignored per-ISO cache roots and
   ``year_*.parquet`` files, which is all the loop below needs to reach.

*NOT invalidated:* **backcast** caches and every keeper bundle. The two
re-anchored vintages are forecast-only forward capacity parameters; ``retirement
_rule`` and both entry gates drive forecast-mode capacity evolution, which does
not run in a backcast. The six current keepers' cache keys are unmoved (the
default key is byte-stable at ``603c2498bf71d21d``, and no keeper sets any of
the three fields).

**Epoch 2026-08-02 — FFR Wave-1 forecast fixes (FR-1, FR-2, FR-7, FR-8).**
Taken once at the Wave-1 close (`docs/forecast-readiness-prompt-pack-2026-07.md`
§W1-X; `docs/handoffs/ffr-w1x-wave1-close-2026-08-02.md`). Four merged fixes
change forecast output under **unchanged cache keys** — none added, removed or
re-defaulted a ``ScenarioConfig`` field, so no key moved and a pre-Wave-1 bundle
would be silently re-used:

* **FR-1** (`ffr-1a-confirmed-exit-accounting-2026-07-31.md`) — confirmed-exit
  tranche derates are now written to the evolution ledger. Dispatch-inert
  (byte-identity attested), but every cached ``evolution_<year>.json`` from a
  forecast run predating it is missing its ``confirmed_derates`` rows and its
  ``confirmed``/``announced`` reason split.
* **FR-2** (same doc, arm 2) — partial-year confirmed exits now complete in
  year+1 instead of holding a fraction of their MW forever. **Behavioral:**
  fleet MW, dispatch and prices move from the exit year+1 onward.
* **FR-7** (`ffr-1b-solve-year-availability-2026-08-01.md`) — the age-based
  availability escalation keys on the SOLVE year, not ``weather_year``.
  **Behavioral in every forecast year**: the fleet ages, and model-built
  entrants no longer carry a negative age.
* **FR-8** (same doc) — the measured 2025 Martin Lake derate is gated to
  backcast, so it can no longer leak into a ``weather_year=2025``-pinned
  crossover leg. **Behavioral** for every T1-X leg, realized and forward.

*Invalidated:* every cached bundle produced in **forecast mode**
(``mode="forecast"``, including ``hindcast=True`` capacity-hindcast and T1-X
crossover legs) at a commit before the Wave-1 merges — any solve year, not only
2026+, because FR-8 reaches a crossover's realized 2023–2025 legs too. Purge or
move aside the per-ISO cache roots and the contents of every forecast
``--out-dir`` cache (the roots hold tracked ``.gitignore`` keep-files — clear
their contents, not the directories)::

    rm -rf results/{ERCOT,CAISO,PJM,MISO,NYISO,NEISO}
    for d in full-horizon ff-t1f-baseline ffr1a d9-ab probe-* verify-*; do
        [ -d "results/$d" ] && find "results/$d" -mindepth 1 ! -name .gitignore -delete
    done

Run it before any forecast solve on a checkout that predates 2026-08-02; a
container cloned fresh after that date has nothing to purge (verified empty at
the close: zero ``year_*.parquet`` anywhere under ``results/``).

*NOT invalidated:* **backcast** caches and every keeper bundle. FR-7/FR-8 are
mode-gated and FR-1/FR-2 run only under forecast-mode capacity evolution; the
six current keepers' input surfaces and cache keys were attested unchanged
across all three ``scenarios.py``-touching Wave-1 merges (§W1-X close doc §1).
"""

import json
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

import numpy as np
import yaml

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.solve_surface import surface_stamp
from market_sim.model.dispatch import DispatchResult
from market_sim.results.outputs import FleetContext, read_fleet_context

# Root directory under which all cached results are stored. Sourced from the
# central path registry (:data:`market_sim.config.paths.RESULTS_ROOT`,
# ``DATA_ROOT/results``) rather than a cwd-relative ``Path("results")`` so the
# results tree does not silently fork when the process runs outside the repo
# root. Kept as a mutable module attribute: tests (and a handful of scripts)
# redirect it to a temporary directory — prefer the :func:`cache_root`
# contextmanager over hand-rolling a save/set/restore dance.
CACHE_ROOT = paths.RESULTS_ROOT

_CONFIG_FILENAME = "config.yaml"

#: The solve-surface stamp written beside every bundle's ``config.yaml`` (capx
#: D79): which registry rows this bundle was solved on, which of them had moved
#: off their declaration and so entered the key, and which epochs applied. With
#: ``config.yaml`` it makes ``key = f(config, moved rows, epochs)`` reproducible
#: from the bundle alone.
_SOLVE_SURFACE_FILENAME = "solve_surface.json"


@contextmanager
def cache_root(root: "Path | str"):
    """Temporarily redirect :data:`CACHE_ROOT` to ``root``, restoring on exit.

    Absorbs the save/set/restore dance repeated across the result-export and
    reference-solve scripts (``export_results``, ``run_full_horizon``,
    ``ff_readiness_battery``, ...): ``prior = cache.CACHE_ROOT; cache.CACHE_ROOT
    = tmp; try: ...; finally: cache.CACHE_ROOT = prior``. The restore runs even
    if the body raises, so a redirected cache never leaks into a later solve in
    the same process (which would read/write the wrong tree).

    Args:
        root: The directory to point the cache at for the duration of the block.

    Yields:
        The resolved :class:`~pathlib.Path` the cache now points at.
    """
    global CACHE_ROOT
    prior = CACHE_ROOT
    CACHE_ROOT = Path(root)
    try:
        yield CACHE_ROOT
    finally:
        CACHE_ROOT = prior


# Cache keys whose on-disk bundles are CONTAMINATED and may never be served
# (owner decision D-11 condition 2, ``docs/handoffs/ffr-owner-sitting-2026-08-02.md``
# Addendum L.2; discharged by FFR-3U, ``docs/handoffs/ffr-3u-bridge-seam-2026-08-04.md``).
#
# Why a denylist and not an epoch bump: the epoch ledger above is human-read and
# never auto-invalidates, and the FFR-3U seam fix deliberately moves NO cache key
# (it is a guard fix, not a mechanism — every key is byte-identical before and
# after). So the very config that solved 2022 still hashes to these keys: without
# a mechanical refusal, a later run would silently CACHE-HIT the contaminated
# 2022 solve and inherit the rule-22 breach with no banner at all.
#
# The refusal is scoped to what protects the tier: a bundle DIRECTORY existing at
# one of these keys is a hard error, naming the key and telling the operator to
# delete it. An absent directory is fine — a re-probe on a clean tree re-solves
# normally, and under the fixed seam bridges 2022. This closes the reuse channel
# without blocking the legitimate re-probe (a later lane).
CONTAMINATED_CACHE_KEYS: dict[str, str] = {
    "b99600bceb8cb6b8": (
        "FFR-3Q arm A (ERCOT T1-FF base 2021, retirement_rule=pipeline) — SOLVED "
        "2022, a validation-tier holdout year, under an active holdout freeze"
    ),
    "5c352508039513da": (
        "FFR-3Q arm B (ERCOT T1-FF base 2021, retirement_rule=legacy) — SOLVED "
        "2022, a validation-tier holdout year, under an active holdout freeze"
    ),
}


def assert_cache_key_uncontaminated(iso: str, cache_key: str) -> None:
    """Refuse a cache key whose bundle is quarantined under rule 22.

    Called from :func:`get_cache_path`, the single seam every cache read and
    write routes through, so no reader can bypass it. A no-op unless the key is
    in :data:`CONTAMINATED_CACHE_KEYS` **and** a directory for it exists.

    Raises:
        RuntimeError: A bundle directory exists at a contaminated key.
    """
    reason = CONTAMINATED_CACHE_KEYS.get(cache_key)
    if reason is None:
        return
    bundle = CACHE_ROOT / iso / cache_key
    if not bundle.exists():
        return
    raise RuntimeError(
        f"cache key {cache_key} is QUARANTINED and its bundle must not be read "
        f"or extended: {reason}. Owner decision D-11 condition 2 requires this "
        f"key to be uncacheable. Delete {bundle} and re-solve; the FFR-3U seam "
        "fix makes the same window bridge 2022 rather than solve it."
    )


def get_cache_path(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> Path:
    """Return the Parquet path for one cached scenario-year.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag. ``None`` is the final-result file
            ``year_{year}.parquet``; ``"p1"`` is the Pass 1 dataset
            ``year_{year}_p1.parquet`` kept when the commitment screen runs.

    Returns:
        Path ``results/{iso}/{cache_key}/year_{year}[_{pass_label}].parquet``.
    """
    assert_cache_key_uncontaminated(iso, cache_key)
    suffix = "" if pass_label is None else f"_{pass_label}"
    return CACHE_ROOT / iso / cache_key / f"year_{year}{suffix}.parquet"


def get_config_path(iso: str, cache_key: str, year: int) -> Path:
    """Return the ``config.yaml`` path sitting beside a cached scenario."""
    return get_cache_path(iso, cache_key, year).parent / _CONFIG_FILENAME


def is_cached(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> bool:
    """Return whether a cached result exists for this scenario-year.

    ``pass_label`` selects which solve pass to check; ``None`` is the
    final-result file (see :func:`get_cache_path`).

    Presence only. Whether the bundle may be SERVED to a given config is the
    separate question :func:`cache_config_disagreements` answers.
    """
    return get_cache_path(iso, cache_key, year, pass_label).exists()


def _comparable(value):
    """Normalize a config value for cross-serialization comparison.

    ``config.yaml`` is a ``yaml.safe_dump(asdict(config))`` round-trip, which
    renders tuples as sequences and reloads them as lists, so a raw ``==``
    against a live ``asdict`` payload reports every tuple-valued field as
    differing. Tuples are folded to lists (recursively, through dicts and
    sequences) and ``Path`` objects to strings; everything else is returned
    unchanged.
    """
    if isinstance(value, dict):
        return {k: _comparable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_comparable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


def cache_config_disagreements(
    iso: str, cache_key: str, year: int, config: ScenarioConfig
) -> list[str]:
    """Return the fields on which a cached bundle's config disagrees with *config*.

    **Why a cache HIT is not enough (capx D24 option (c′), owner ruling Q20).**
    ``cache_key`` DROPS every ``_CACHE_KEY_OPTIONAL_FIELDS`` member sitting at
    its default, so the key names a config largely by omission — a run's key
    drops 115–215 of its registered fields
    (``docs/handoffs/FINDING-capx-d24-cache-key-defect-2026-09-01.md`` §3). Two
    materially different postures can therefore address one bundle, and D24
    demonstrated both forms among the committed runs:

    * **§4.1, differing common field** — the two configs disagree on a field
      that is present in both and dropped from the key at whichever value was
      the default on the day each was hashed;
    * **§4.2, absent vs armed default** — the stored config predates the field
      entirely, and the requester carries it at a default that has since been
      ARMED, so neither side's value is in the key and nothing in the pair of
      ``run_config.json`` files looks like more than ordinary schema growth.

    This function is the mechanical refusal for both, at the one seam where a
    bundle is served, and it is deliberately (c′) rather than strict (c): a
    field ABSENT from the stored config is a disagreement only when the
    requester's value is not that field's registration-time default. Strict
    equality would refuse a bundle the moment the schema grew at all — 14 of
    D24's 14 shared-key groups, against 2 true positives.

    Follows the :func:`assert_cache_key_uncontaminated` precedent (owner
    decision D-11) in placement and tone, with one deliberate difference: this
    is NOT an exception. A disagreement is a cache MISS, which the caller logs
    and re-solves — a wrong bundle must never be served, and a run must never
    die because one was on disk.

    Three cases are deliberately NOT disagreements, each because refusing would
    cost re-solves without protecting anything:

    * **No stored ``config.yaml``** (a hand-assembled or truncated bundle):
      nothing to compare, so the pre-existing behaviour stands. Every bundle
      :func:`save_result` writes carries one.
    * **A field present in the STORED config and absent from the requester** —
      a field deleted under rule 26 ``[R-DELETE]``, whose value
      ``_CACHE_KEY_RETIRED_FIELDS`` already re-inserts into the key.
    * **Checkout-absolute paths**, folded to sentinels on both sides exactly as
      the key folds them, so a bundle stays reachable from a differently-rooted
      checkout. A path that survives that folding and still differs IS a
      disagreement: it is a different data source.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: The key the bundle is addressed at.
        year: Weather/simulation year (selects the bundle directory).
        config: The config requesting the bundle.

    Returns:
        Sorted field names on which the stored config disagrees; empty when the
        bundle may be served.
    """
    stored_path = get_config_path(iso, cache_key, year)
    if not stored_path.exists():
        return []
    stored_raw = yaml.safe_load(stored_path.read_text()) or {}
    if not isinstance(stored_raw, dict):
        return []
    return config_disagreements(stored_raw, asdict(config))


def config_disagreements(stored: dict, wanted: dict) -> list[str]:
    """Return the fields on which a stored config disagrees with a wanted one.

    The pure half of :func:`cache_config_disagreements` — no filesystem — so the
    rule can be exercised directly against the committed ``run_config.json``
    population that capx D24 measured.

    Args:
        stored: The config a bundle was solved under (a ``config.yaml`` load or
            a committed ``run_config.json``'s ``scenario_config``).
        wanted: The config asking for that bundle (an ``asdict`` payload).

    Returns:
        Sorted field names on which the two disagree; empty when the stored
        bundle may be served to *wanted*.
    """
    from market_sim.config.scenarios import (
        _cache_key_path_roots,
        _normalize_cache_key_paths,
        registration_time_default,
    )

    roots = _cache_key_path_roots()
    stored = _normalize_cache_key_paths(_comparable(stored), roots)
    wanted = _normalize_cache_key_paths(_comparable(wanted), roots)

    differing: list[str] = []
    for name, value in wanted.items():
        if name in stored:
            if stored[name] != value:
                differing.append(name)
            continue
        # Absent from the stored config: ordinary schema growth UNLESS the
        # requester has moved it off the value its absence is equivalent to.
        try:
            absent_equivalent = registration_time_default(name)
        except KeyError:
            differing.append(name)
            continue
        if _normalize_cache_key_paths(_comparable(absent_equivalent), roots) != value:
            differing.append(name)
    return sorted(differing)


def save_result(
    result: DispatchResult,
    config: ScenarioConfig,
    iso: str,
    year: int,
    context: FleetContext | None = None,
    pass_label: str | None = None,
    demand: "np.ndarray | None" = None,
) -> Path:
    """Persist a dispatch result and its config to the cache.

    Writes the result as Parquet and, if not already present, the full
    config as ``config.yaml`` in the same directory, plus the solve-surface
    stamp ``solve_surface.json`` (capx D79) recording which registry rows the
    bundle was solved on.

    Args:
        result: The solved dispatch result to cache.
        config: The scenario config that produced ``result``; its
            ``cache_key`` selects the cache directory.
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Weather/simulation year.
        context: Optional fleet context stored in the Parquet metadata so
            the result can be aggregated without re-deriving the fleet.
        pass_label: Solve-pass tag (see :func:`get_cache_path`). ``None``
            writes the final-result file; ``"p1"`` writes the Pass 1
            dataset.
        demand: Optional ``(n_zones, T)`` served demand, stored so the
            forecast-invariant checker can verify the energy balance.

    Returns:
        The Parquet path written.
    """
    cache_key = config.cache_key()
    path = get_cache_path(iso, cache_key, year, pass_label)
    path.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(path, context=context, demand=demand)
    config.to_yaml_full(path.parent / _CONFIG_FILENAME)
    # Rewritten on every save (never `if not exists`): the surface can move
    # between two years of one run, and the stamp must date the bytes on disk.
    (path.parent / _SOLVE_SURFACE_FILENAME).write_text(
        json.dumps(surface_stamp(iso, config), indent=2, sort_keys=True) + "\n"
    )
    return path


def load_result(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> DispatchResult:
    """Load a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag (see :func:`get_cache_path`). ``None``
            loads the final-result file; ``"p1"`` loads the Pass 1 dataset.

    Returns:
        The cached :class:`DispatchResult`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
    """
    path = get_cache_path(iso, cache_key, year, pass_label)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} pass={pass_label} (expected {path})"
        )
    return DispatchResult.from_parquet(path)


def load_fleet_context(
    iso: str, cache_key: str, year: int, pass_label: str | None = None
) -> FleetContext:
    """Load the fleet context stored alongside a cached dispatch result.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        cache_key: Deterministic config hash from ``ScenarioConfig.cache_key``.
        year: Weather/simulation year.
        pass_label: Solve-pass tag (see :func:`get_cache_path`).

    Returns:
        The cached :class:`~market_sim.results.outputs.FleetContext`.

    Raises:
        FileNotFoundError: When no cached result exists for this scenario-year.
        ValueError: When the cached result carries no fleet context.
    """
    path = get_cache_path(iso, cache_key, year, pass_label)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached result for iso={iso} cache_key={cache_key} "
            f"year={year} (expected {path})"
        )
    return read_fleet_context(path)
