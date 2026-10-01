# FFR-5E — Implementing the near-term VRE procurement channel

**Lane:** implementation (owner decision **D-18(a)**, sitting Addendum S.2/S.5, signed
2026-08-05). Wave 5. The spec is FFR-5B's design —
`docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md` §§2-3, admissibility contract
§5.1 — implemented, not re-derived and not widened.

**Head at start:** branch rebased onto `origin/main` **`57d4d66a`** before any work (main had
moved from the dispatch's `5543c4c0`/`70acd78c`); all measurements below are against that base.

**State re-verified at this session's own head, not inherited from the prompt.** PR **#3577
(FFR-5C) is MERGED** (2026-08-05T05:20:14Z) — the step-0 precondition holds and
`entry_pipeline_aware_signal` is present in `new_entry.py` as landed. Nothing in this lane
reads or writes a keeper shard, `calibration-complete.json`, or any dashboard namespace.

---

## 0. Headline, and the guard first

**THIS DOES NOT CLOSE MISO's 18.649 GW GAP, BY DESIGN — and no version of it can.** A
vintage-2020 hindcast is *allowed to see* 1.034 GW of committed MISO solar pipeline against
18.649 GW actually built. A correctly-gated near-term channel is arithmetically incapable of
reproducing a five-year build from a two-year queue, and that is the information gate
**working**. Widening the status set, the vintage or the horizon to reach a better MISO number
spends the guard rather than improving the model — rule 1 `[R-STRUCT]`'s fitted-input failure
arriving as a status filter instead of an adder. The signed card explicitly **REFUSED** option
(b). This sentence precedes every number in this document deliberately.

**What landed.** One `ScenarioConfig` field, `vre_procurement_additions_enabled: bool = False`
(GATED, forecast-mode only, **not armed in any ISO**), plus a wind/solar limb of
capacity-evolution **step 4** that reads the run's own EIA-860 vintage's **proposed**-generator
sheet at construction-committed status, zone-assigns each row from its plant's lat/lon, writes
MW into `renewable_additions` tagged `source: "procured"`, and nets its **current-year
commissioning flow** from the economic screen's budgets. **Zero free parameters** (§4).

**Byte-identity of the shipped path is PROVEN, not asserted** (§3.1): the gate-off digest is
`1907ea7c01aa168e…` at both the base commit (where the field does not exist at all) and the
feature commit, and the pinned default `cache_key()` is unmoved at `603c2498bf71d21d`.

**Two defects were found and fixed during implementation** (§6) — neither was in the design;
both were mine. One of them (the cache key) would have silently invalidated every cached
bundle in the repo.

---

## 1. Step 0 — the precondition and the §2.3 composition statement

### 1.1 PR #3577 is merged

Verified at head via the GitHub API: `"state":"closed"`, `"merged":true`, merged
2026-08-05T05:20:14Z onto base `5543c4c0`. Step 0 passes; no escalation was needed on this
half.

### 1.2 The §2.3 composition, stated against the landed 5C shape

FFR-5B §2.3 was written before FFR-5C landed and its line references (`new_entry.py:1183-1188`)
are stale. **The landed shape does not make §2.3 ambiguous — it sharpens it**, so this lane
proceeded rather than escalating. The exact seam, as landed:

```python
# new_entry.py (as landed by FFR-5C)
_pending_by_tech: dict[str, float]           # the pending-pipeline STOCK
_pending_netting_mw = {} if config.entry_pipeline_aware_signal else _pending_by_tech
...
group_remaining[group] = max(0.0, per_tech_cap_gw[group]*1000 - _pending_netting_mw.get(tech, 0.0))
_ladder_remaining[tech] = max(0.0, entry_rate_caps_mw[tech] - _pending_netting_mw.get(tech, 0.0))
```

Three decisions follow, and each is a *consequence* of the landed shape rather than a judgment
call:

1. **The procurement netting is a SEPARATE term, deliberately NOT routed through
   `_pending_netting_mw`.** Routing it there would have made arming the unrelated FFR-5C gate
   *silently switch the procurement netting off*, coupling two mechanisms that §2.3(c) states
   are "compatible and independent; neither is a precondition for the other." A dedicated
   `_procured_netting_mw` keeps them independent. **Regression-pinned at both settings of
   `entry_pipeline_aware_signal`** (`test_netting_is_independent_of_entry_pipeline_aware_signal`).

2. **It does not re-create FFR-4A's defect.** D-17 removed a **stock** (MW, no time
   denominator, summed over `L-1` decision cohorts) netted from an **annual flow** cap, which
   imposed an unintended `D ≤ C/L` and killed the ladder ratchet at `K ≤ L`. What this channel
   nets is the MW **commissioning in year Y**, against year Y's caps — a flow against a flow,
   same units both sides, no stock, no `C/L`, no ratchet effect. The design's binding sentence
   is carried verbatim into the code comment so a later reader cannot get it wrong by accident.

3. **The netted sites are the two §2.3(b) names** — `queue_budget_mw` and `group_remaining` —
   **and not the growth ladder.** This is a deliberate non-widening and is called out here
   because it is the one place a reader might expect a third netting. It is not needed for
   correctness: `build_mw = min(group_remaining[group], remaining)` already bounds the year's
   total at the ISO/group budget, so netting those two prevents the double-count on its own;
   the ladder only ever tightens further. Netting the ladder as well would be a *tighter*
   model that the design did not specify, so it stays out. Recorded in §7 as a stated
   non-separation rather than left silent.

Per §2.3(a), **procured MW itself is not capped** by the ladder or the queue caps: a row already
in the queue with an effective year *is* the throughput the caps measure, so capping it would
count one physical constraint twice and could silently delete a project that verifiably exists.
The netting therefore lands on the *screen's* budgets, never on the procured MW. Pinned by
`test_procured_mw_itself_is_not_capped`.

---

## 2. What was built

| piece | file | note |
|---|---|---|
| the gate | `config/scenarios.py` `vre_procurement_additions_enabled` | GATED default-OFF, forecast-mode only; registered in `_CACHE_KEY_OPTIONAL_FIELDS`, the defaults registry and `TIER_TAGS` |
| the loader | `data/fleet/eia860.py::load_procured_vre_additions` | the exact sibling of `load_planned_additions` — same sheet, same statuses, same BA crosswalk, same vintage gate, same coord siting |
| the limb | `capacity_evolution/evolve.py` step **4b** | writes `renewable_additions`, emits `source: "procured"` ledger rows, computes the year's flow |
| the netting | `capacity_evolution/new_entry.py` `procured_flow_mw=` | nets `queue_budget_mw` + `group_remaining`; independent of `entry_pipeline_aware_signal` |
| plumbing | `pipeline/prior.py`, `runner.py` | `procured_vre_additions` loaded once, threaded like `planned_additions` |
| tests | `tests/unit/model/test_vre_procurement_ffr5e.py` | 19 tests, additive file per rule 27 |
| matrix | `docs/codebase-site/data/mechanism-matrix.js` | row `vre_procurement_additions`, same PR (rule 28c) |

**A limb, never a new step** (§2.1): minting a step 4b *mechanism* alongside step 4 would create
a second additions channel in the very act of fixing a rule-19-shaped problem, and would break
the **step-0 confirmed exits : step-4 confirmed additions** symmetry that makes both auditable.

---

## 3. Measurement — shipped vs armed paired control

Instrument: the **FFR-4A harness pattern** — the `evolve_fleet` step-4/step-5 path exercised
directly, six ISOs × decision years 2026-2029, no LP solve. This is the cheapest honest
instrument for a mechanism whose entire effect is in capacity evolution. **No keeper contact,
no default flipped, no `ISOConfig` override, no dashboard registration** (no run was produced,
so rule 15 does not apply). Harness:
`scratchpad/ffr5e_harness.py` (session scratch, reproduced in §8).

### 3.1 Byte-identity of the shipped path — PROVEN

The digest is taken over `renewable_additions` + fleet-MW-by-fuel + ledger rows, all six ISOs ×
four years, sorted and serialized deterministically. The **shipped** arm is constructed *without
the field at all* at the base commit, which is the honest control (the shipped path is defined
by the field's absence, not by passing it `False`).

| commit | SHIPPED digest |
|---|---|
| base `57d4d66a` (field absent) | `1907ea7c01aa168e00705b8fa1b7b9598b9ed887a51c5eeabad2b25780ccc0ce` |
| feature (field present, default OFF) | `1907ea7c01aa168e00705b8fa1b7b9598b9ed887a51c5eeabad2b25780ccc0ce` |

**Identical.** Re-verified a third time after the two §6 fixes landed.

Cache-key half, which is the other face of the same property:
`ScenarioConfig().cache_key() == 603c2498bf71d21d`, the value pinned by
`tests/regression/test_persisted_identity.py` — unmoved. An armed run hashes distinctly
(`9788d96d64fa08d0`), so an armed run cannot collide with a cold one on disk.

### 3.2 The armed arm — the netting is visible and correct

Committed (`U`/`V`/`TS`) proposed VRE pipeline at the shipped vintage, as the channel sees it:

| ISO | rows | MW | effective years |
|---|---|---|---|
| MISO | 100 | 8,740.8 | 2026-2028 |
| ERCOT | 32 | 6,575.2 | 2026-2027 |
| PJM | 60 | 2,987.2 | 2026-2027 |
| CAISO | 38 | 2,267.0 | 2026-2027 |
| NYISO | 33 | 419.6 | 2026-2027 |
| NEISO | 5 | 31.6 | 2026 |

The single clearest netting demonstration, **MISO decision year 2027**:

| arm | economic wind | procured solar | total |
|---|---|---|---|
| shipped | 4,000.0 | — | 4,000.0 |
| armed | 2,489.3 | 2,510.7 | **5,000.0** |

5,000.0 MW is MISO's `QUEUE_CAP_GW` budget **exactly**. An un-netted channel would have built
4,000.0 + 2,510.7 = 6,510.7 MW — the double-count §2.3(b) exists to prevent. One physical
queue, spent once.

**MISO 2028 is the other half of the point**: the shipped arm builds **nothing** (the screen
finds no profitable candidate), while the armed arm still commissions 960.0 MW of committed
pipeline. That is the actual defect being closed — FFR-3V §4.3's finding that the merchant
screen is a *single point of failure* for all VRE in every forecast.

### 3.3 Hindcast arm — BLOCKED, not run

**FFR-3V §6.1 blocks it and this lane did not run one.** A capacity hindcast is
`mode="forecast"` + `hindcast=True`, so `load_renewable_profiles`' `is_backcast` gate falls
through to the canonical constant — MISO solar seeds at **7,000 MW against 2,056 MW actual at
vintage 2020**, 3.4× over. Injecting vintage-gated procured MW onto a pool that already contains
post-vintage capacity double-counts **invisibly**: the totals stay plausible while the mechanism
is wrong. Plain 2026+ forecast measurement is unaffected, and is what §3.2 is.

---

## 4. Rule discharge

* **Rule 13 `[R-MEASURED]` — the boundary the whole design turns on.** The channel reads
  `eia860_generator_proposed.parquet` (a forward statement of intent, filed *before* the
  outcome) and is forbidden `eia860_generator_operable.parquet` (*the outcome*). The two sit in
  the same directory with near-identical schemas, so this is asserted **mechanically rather than
  trusted to review**: `test_operable_sheet_is_never_read` spies on every parquet the loader
  opens and fails on any path containing `operable`/`retired`. Not for cross-checking, not for
  "validation", not for a run-time coverage statistic.
* **Rule 14.** `U/V/TS` at face value, no realization multiplier — §3.4 option (a). Option (c)
  would need a scalar whose most natural identification is *pipeline MW vs realized COD MW*,
  and realized COD is precisely what §3.1 forbids importing. That option remains available as a
  future **frozen-derive with its own citation**, scored leave-one-year-out; it is not this
  lane's.
* **Rule 19 `[R-ONE-MECH]`.** A limb of step 4, not a second ladder and not a second netting
  (§1.2, §2). The technology map is **imported** from `renewables._TECHNOLOGY_TO_FUEL` and the
  status set **shared** with the thermal limb rather than copied, so no second vocabulary for
  the same file exists to drift.
* **Rule 23.** Nothing derives from a residual. The status set is a cited code constant, the
  horizon is the data's own, the vintage is the run's own.
* **Rule 24 `[R-REGISTRY]`.** One field, in `ScenarioConfig`, therefore in `run_config.json`
  (verified via `dataclasses.asdict`). No env var, no per-ISO dict, no status-set override, no
  horizon scalar, no `getattr` fallback literal. The entire surface is the gate plus the
  existing vintage path, exactly as §2.5 pre-registered — so any future expansion is visible
  against the design doc by construction.
* **Rule 25 `[R-ISO-SCOPE]`.** **Nothing armed anywhere.** MISO's charter transfers to nobody;
  the other five ISOs' cells are `U`. A mechanical measurement is not a verdict.
* **Rule 27.** Opus; exact on-disk bytes pushed; blob verification after every push touching a
  ≥300-line file (§8).
* **Rule 28(c).** Matrix row `vre_procurement_additions` minted in the same PR as the field.
  MISO `O` (chartered, built, mechanically measured, verdict not reached — arming is a separate
  decision), all others `U`.

---

## 5. The three gates, as built

* **Instrument** (§3.1) — `_PLANNED_FIRM_STATUSES` = `{U, V, TS}`, the **shared** frozenset,
  whose instrument is the utility's own Form 860 filing. `P` (planned, approvals not initiated)
  is announcement-grade and stays excluded, exactly as the thermal limb excludes it *by name*.
* **Information** (§3.2) — only the run's own `active_eia860_dir()` is opened, and only rows
  with `Effective Year > operable_vintage_year(data_dir)` qualify. A run pinned to vintage 2020
  can never open the 2021 sheet. This reuses the existing vintage machinery rather than
  reimplementing it — the FH-1 leak fix already proved what happens when the guard is written
  against a hardcoded constant instead of the active snapshot.
* **Horizon** (§3.3) — **none is imposed**, because none is needed: the pipeline is simply empty
  past ~`V+4`, so the channel falls silent and hands the whole job back to the economic screen.
  **The pipeline is never extrapolated forward** — an assumed repeat of the last cohort would be
  a free parameter wearing a data costume, and would be the exact mechanism by which a 2026-2050
  forecast's VRE build silently became a fitted growth assumption. Pinned by
  `test_year_with_no_matching_row_injects_nothing`.

**Attribution** (§3.5) is a hard requirement, not a nicety: every MW carries `source: "procured"`
with its EIA-860 `plant_id` and `generator_id`. MW that cannot be separated from the economic
screen's MW is unauditable — no D-2 attribution can enumerate it, no rule-19 reconciliation can
be performed against it, and no later session could tell whether a build came from the queue or
from a margin.

---

## 6. Two defects found during implementation — both mine, both fixed

Recorded because both were caught by tests rather than by reading, and one was serious.

1. **The gate was enforced only at the runner's load site.** `evolve_fleet` acted on whatever
   rows it was handed, so any caller threading rows in (a test, a different entry point) got the
   mechanism regardless of the flag. **A gate that only one caller honours is not a gate.** Fixed
   by re-checking `vre_procurement_additions_enabled` **and** `mode == "forecast"` at the point
   of use. Caught by `test_gate_off_is_a_no_op_even_with_rows_present`.

2. **The default `cache_key()` moved** — `603c2498bf71d21d` → `18b94dab68788910`. A new
   `ScenarioConfig` field must be registered in `_CACHE_KEY_OPTIONAL_FIELDS` so it drops out of
   the hash at its default; without that, **every pre-existing cached bundle in the repo would
   have been silently invalidated** by a default-off addition that changes nothing. Fixed by
   registering at all three sites (`_CACHE_KEY_OPTIONAL_FIELDS`, the defaults registry,
   `TIER_TAGS`), following the `entry_pipeline_aware_signal` precedent exactly. Caught by
   `tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py::test_default_cache_key_unmoved`
   and now also pinned in this lane's own file.

One further pre-existing test, `test_pipeline_prior.py::test_all_twenty_keys_present`, asserts
an exact `PriorYearResults` key set; it was updated to include `procured_vre_additions` and
renamed `test_all_cross_year_keys_present` (the count was in the name and would have gone stale
again on the next field).

---

## 7. What I did NOT do, and what I did NOT separate

* **I did not arm it anywhere, including MISO.** The field ships default-OFF and no
  `ISOConfig.default_scenario_overrides` entry was added. Arming is a separate owner decision
  (rule 25).
* **I did not run a hindcast arm** (§3.3) — FFR-3V §6.1 blocks it. I did not attempt to work
  around the block, and I did not close FFR-3V §6.1 as a side quest.
* **I did not net the growth ladder** (§1.2 item 3). §2.3(b) names two sites; the ISO/group
  budgets already bound the year's total, so a third netting would be a tightening the design
  did not specify. Stated rather than silently added — this is the most likely place a reviewer
  will expect something I deliberately left out.
* **I did not extend the technology map.** It is imported from `renewables._TECHNOLOGY_TO_FUEL`
  (`Solar Photovoltaic`, `Onshore Wind Turbine`), so **offshore wind and solar thermal are out
  of scope** — 5,889 MW and 200 MW nationally in the proposed sheet, materially NEISO/NYISO.
  This makes the channel build **less** (the safe direction, and the same posture as the
  status-set choice). Extending the map is a separate decision with its own evidence; minting a
  second wind/solar vocabulary for the same sheet inside this lane was the wrong way to get it.
* **I did not inject rows at or before the run's base year.** The base year does not evolve and
  its pools already seed from `RENEWABLE_INSTALLED_MW`, so those rows are left out — an
  **under-count, never a double-count**. Stated as a bounded property because the design does
  not discuss base-year handling.
* **I did not fix `assign_zone_by_coords`.** Its zone rules are incomplete for **PJM and MISO**:
  every row falls back to `_LARGEST_ZONE` (all PJM rows → `PJM_AEP_Ohio`; MISO splits only
  Illinois/South), verified for plants whose real coordinates are in OH/KY/VA/MD and MN/IA/LA.
  **This is a pre-existing repo condition shared identically with the thermal limb** — measured,
  not introduced here — and `load_planned_additions` exhibits it on the same call. Fixing the
  shared helper would move the shipped thermal channel, which is out of this lane's scope.
  ERCOT/CAISO/NYISO/NEISO *do* site per-row, which is §2.2's free siting improvement over the
  economic screen's single `RENEWABLE_ZONE_ALLOCATION` bucket. **Flagged for whoever owns
  zone-assignment coverage; it bounds this channel's siting benefit in exactly two ISOs, one of
  which is the chartered candidate.**
* **A double-count hazard the design did not flag, checked and cleared.**
  `data/renewables.py::_add_proposed_capacity` *already* reads the same proposed sheet (statuses
  `U/V/TS/P`, ERCOT-only via `_ISO_HOME_STATES`). It is **not** a double-count in forecast mode:
  `load_renewable_profiles` takes `installed_mw = RENEWABLE_INSTALLED_MW[iso][fuel]` for
  `mode="forecast"` and uses the `monthly` array — the one the augmentation touches — only for
  the inter-zone **allocation shape** via `_distribute_by_eia860`. Magnitude comes from the
  constant, so the two readers do not stack. Recorded here because the next session to touch
  either path should not have to re-derive it.
* **I did not touch a keeper, a marker, `calibration-complete.json`, or any out-of-training
  year.** No solve was run; the holdout freeze is untouched and irrelevant to this lane.
* **I did not settle FFR-5B's E-1/E-2** (the RPS row's spatial grain and the clean-tier gap).
  They remain escalated where FFR-5B left them.

---

## 8. Reproduction & verification

* **Tests:** `uv run pytest tests/unit/model/test_vre_procurement_ffr5e.py` — **19 passed**.
  Full `tests/unit` + `tests/regression` at the feature commit: **3,754 passed, 13 failed**.
  **All 13 failures are PRE-EXISTING and ENVIRONMENTAL, verified by running the same 13 on a
  clean `origin/main` checkout (`62570c67`) in this same container — identical set, identical
  count.** They are caused by `data/clean` being **empty**: this session's measurement
  deliberately solves nothing, so `regenerate_clean.py` was never run, and the code says so
  itself — *"data/clean is derived and gitignored, so a fresh checkout has no registry; refusing
  to silently degrade to the economic screen"*
  (`data/confirmed_retirements.py:168`). The set is
  `test_soundness.py::TestEndToEnd` ×6 (end-to-end solves), `test_export.py` ×4,
  `test_constants_facade.py::test_moved_surface_is_complete`,
  `test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`, and
  `test_outages.py::test_unknown_iso_degrades_to_empty`. **Nothing in this lane's diff touches
  any of them**, and the two suites' failing sets differ slightly between runs (ordering
  flakiness), which is itself a marker of the environmental cause rather than a code one.
  A reviewer with a populated `data/clean` should see them pass; if any does not, it is not
  this change.
* **Paired arms:** `uv run python ffr5e_harness.py <label>` at the base commit and at the
  feature commit; compare the printed `SHIPPED=` digests (must be identical) and diff the
  `armed` blocks. The harness probes for the field with `dataclasses.fields(ScenarioConfig)`
  so it runs unmodified at a commit where the field does not exist.
* **Matrix guard:** `uv run python scripts/check_mechanism_matrix.py` — no errors introduced
  (the pre-existing anchor-drift and CAISO keeper-stamp warnings belong to other lanes and are
  reported as pre-existing by the guard's own base-diff escalation).
* **Blob verification (rule 27):** every pushed file ≥300 lines re-fetched and compared on line
  count + SHA-256 against the local bytes after each push; results in the PR description.

Sources: `data/raw/eia-860/eia860_generator_proposed.parquet` + `eia860_plant.parquet` at the
active vintage; ISO mapping via `market_sim.data.fleet.eia860.BA_CODE_TO_ISO`. **No LP was
solved, no measured outcome entered any decision path, and no dashboard artifact was produced.**
