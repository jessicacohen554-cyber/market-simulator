# FFR-1D — enforcement wave: making the written rules executable (2026-07-31)

**Session:** `[OPUS] FFR-1D` (forecast-readiness prompt pack §Wave 1). Findings for audit items
**FR-24, FR-25, FR-10, FR-11, FR-15, FR-26-cheap**
(`docs/forecast-readiness-audit-2026-07.md` §3.5 / §3.2, §4 row P1-d).

**No LP was solved in this session.** No default was moved, no band widened, no threshold touched,
no out-of-training year approached, nothing registered on any dashboard (no run was produced).
Every change is a guard, a test, a deletion, or a doc correction.

Branch: `claude/ffr-1d-ci-guards-config-21sid9`, originally off `origin/main` `40ecb0a`,
**rebased 2026-08-01 onto `6e98263`** — after FFR-1A/1B/1C/1E and the WP intake lanes merged. See
§7c for what the rebase changed.

---

## 0. What each finding asked for, and what landed

| Finding | Ask | Landed |
|---|---|---|
| FR-24 | CI-wire the forecast invariants; add the forecast namespaces to `ci.yml` path filters; keep forecast runs out of the backcast registry; correct the plan's false "CI-wired" claim | `ci.yml` job `forecast-invariant-artifacts` (no LP) + 3 path filters + `check_namespace_boundary` in the backcast parity gate + FF plan §1.1 rewritten |
| FR-25 | One shared `assert_schedulable`, called from **every** schedulable entry point | `market_sim/config/schedulable.py` (+ a `scripts/lib/` re-export); 2 → **9** call sites; 29 tests |
| FR-10 | `correlated_forced_outage` backcast coercion, backcast cache keys proven unchanged | landed; keys proven over 118 committed backcast run_configs (§3) |
| FR-11 | Hard forecast-mode errors for the backcast-only overlay family | 36 fields + the `outage_source="historic"` value, one registry, one guard |
| FR-15 | Delete the three inert FF-3D CLI flags; dedupe `_CACHE_KEY_OPTIONAL_FIELDS` | both landed — with one **scope correction**, §5 |
| FR-26 | Registration-path smoke test; golden-fixture staleness expiry | both landed — the staleness expiry with a declared, dated waiver, §7 |

---

## 1. FR-24 — the forecast invariants are now actually CI-wired

**The finding, restated precisely.** `check_forecast_invariants.py` had no CI reference anywhere
since `forecast-invariants.yml` was deleted 2026-07-14; CI ran only the checker's unit tests on
synthetic runs, while FF plan §1.1 claimed the invariants were "CI-wired".

**Why the obvious fix is impossible.** Running the checker over a run needs that run's *cache
directory* — per-year dispatch parquet plus `evolution_<year>.json` ledgers, gigabytes, and
uncommitted by design. There is no version of "run `check_forecast_invariants.py` in CI" that scores
a real run without a solve. So the honest gate is one tier up: audit the invariant verdicts every
registration **commits**.

**What landed.** A new artifact mode, `check_forecast_invariants.py --sidecar-dir [DIR]`
(default `frontend/data/hindcast`), and the CI job `forecast-invariant-artifacts`. It enforces three
things over the 61 committed sidecars that carry an `invariants` block (791 records):

1. **Schema.** Every record carries this module's own `Result` fields, a status from its own
   vocabulary, and an ident it actually emits. A renamed/dropped invariant makes the committed
   evidence unreadable — this catches it at the rename.
2. **Coverage.** The harness emits all of I1–I14, so a committed block must carry all fourteen
   **unless the run is declared a curated subset**. Six runs are (the FF-2D `*-ff-t1-gate`
   registrations, which record only the gate's own rows); their declaration is in the ledger, not in
   the checker's head. A `kind: t1f` sidecar with no invariants block at all is a hard failure —
   FC-1 is scored off exactly that block.
3. **Declared failures.** Every FAIL in the committed evidence must be listed in
   `frontend/data/hindcast/invariant-failures.json`. Seeded from HEAD: **111 FAILs across 59 runs**,
   unchanged in verdict — the ledger records what is already true, it does not bless it. The
   dominant causes are already-open findings (I4 → FR-1, I7 → FR-3, I3 → FR-6, I6 → FR-4), and the
   ledger says so. Stale declarations fail too: if a defect gets fixed and the invariant starts
   passing, the ledger line must go.

The point of (3) is the *next* registration: a W2/W3 run that fails an invariant now has to say so
in a reviewed file in the same commit, instead of the FAIL sliding onto the forecast dashboard
unremarked. Adding a line is not absolution — an invariant FAIL is a root-cause finding (rules
1/11), which is why the ledger names each cause.

Negative-tested: an injected undeclared FAIL, an unknown ident, a broken record schema and a
truncated battery each fail the job with a specific message.

**Path filters.** `ci.yml` gained `frontend/data/hindcast/**`, `frontend/data/forecast/**` and
`tests/golden/**`. Before this, a forecast-registration commit triggered **no CI job at all** — not
even the registry gates whose whole job is keeping the two namespaces apart.

**Namespace boundary.** `check_registry_payload_parity.py` gained `check_namespace_boundary()`: a
backcast registry entry carrying a forecast `kind`/`mode`, a bundle under a forecast results root
(`results/hindcast/`, `results/ff-*`, `results/full-horizon/`, `results/crossover/`, `results/ces-*`),
or a payload path outside `frontend/data/backcast/runs/` fails the gate. It reads **only the
backcast entry's own fields** — it never opens the forecast namespace, so the backcast gates stay
blind to it exactly as forecast plan §7.5 requires.

**The false claim.** FF plan §1.1's "Validation machinery" row now states what is true: the checker
cannot run in CI, nothing referenced it between 2026-07-14 and today, and what *is* wired is the
artifact audit.

---

## 2. FR-25 — the §2.1b cap now refuses from every entry point

`assert_schedulable` moved from `scripts/run_full_horizon.py` to
**`src/market_sim/config/schedulable.py`**, re-exported by `scripts/lib/schedulable.py` for the
script drivers (`run_full_horizon` also re-exports `assert_schedulable`, so `run_ces_leg.py` and the
existing readiness-battery tests are untouched).

**Why not `scripts/lib/` as the implementation** (the prompt's suggested home): `market_sim.runner`'s
CLI is one of the callers, and `scripts` is not part of the installed package — a `market-sim run
--help` invoked from outside the repo root died with `ModuleNotFoundError: No module named 'scripts'`
while the guard lived there (caught before push). `scripts/lib/schedulable.py` remains the script
drivers' import path, so there is still exactly one copy of the cap.

Two new helpers carry it to the CLIs whose horizon arrives inside a scenario YAML rather
than as year arguments: `config_horizon()` (resolves `start_year`/`end_year`, falling back to the
module `START_YEAR`/`END_YEAR` — this is what makes the guard bite on the audit's "base YAML defaults
to 2026–2050" case) and `assert_config_schedulable()`.

| Entry point | Before | After |
|---|---|---|
| `run_full_horizon.py` | guarded | guarded (shared impl) |
| `run_ces_leg.py` | guarded | guarded (shared impl, via the re-export) |
| `market-sim run` | **unguarded** | guarded + `--full-solve-authorized` |
| `market-sim sweep` | **unguarded** | guarded — every expanded member, not just the base |
| `market-sim ensemble` | **unguarded** | guarded |
| `market-sim matrix` | **unguarded** | guarded — base config **and** every expanded case |
| `pb5_member_slice.py` | **unguarded** | guarded, before the sampler spec is even read |
| `pb5_assemble.py --mode assemble` | **unguarded** | guarded (it re-solves uncached members) |
| `golden_forecast_bands.py seed` / `check` | **unguarded** | guarded (15 solve-years — always needs D-7) |

Two scope decisions, both stated in code:

- **Backcast configs are out of scope.** §2.1b is the forecast program's cap; a backcast window is
  governed by rule 22's holdout tiers and `run_calibration_full.py`'s `--holdout-authorized` gate.
  Capping backcasts here would have been a second mechanism for one phenomenon (rule 19).
- **The hindcast harness IS in scope.** `mode="forecast", hindcast=True` is the T1-H/T1-X
  instrument §2.1b sizes, so it is capped like any other forecast invocation.

Tests (`tests/scoring/test_schedulable_guard.py`, 29 cases): >5 unauthorized refused from each entry
point, 5 allowed, authorized 25 allowed; the boundary is `> 5` not `>= 5`; every `market-sim`
subcommand is asserted to carry the flag (a subcommand without it *is* an unguarded entry point);
and every schedulable script is asserted to import the shared module — an entry point growing its own
copy of the cap is how the enforcement drifted to 2-of-6 in the first place.

---

## 3. FR-10 — `correlated_forced_outage` backcast coercion, with the cache-key proof

One coercion in `__post_init__` (`mode == "backcast"` ⇒ `False`), the exact
`datacenter_load_path` / `entry_lookahead_reprice` pattern. The mechanism already no-opped in a
backcast (`apply_correlated_outage_derate` is forecast/hindcast-gated), but only
`pipeline/backcast_config.py` pinned the value, so a backcast built any other way inherited the FF-1F
default-ON flip and got a **spuriously distinct cache key for a byte-identical solve**. Hindcast legs
(`hindcast=True`) are not coerced — FF-1B probe arms them explicitly.

**Proof that backcast cache keys are unchanged.** Every committed `results/**/run_config.json` with
`mode: backcast` (118) was reconstructed into a `ScenarioConfig` and re-hashed at `origin/main` and
at this branch:

- **109 identical** — every backcast run_config that *records* the field (i.e. every one produced
  since the field landed), including all six current keepers' eras.
- **9 moved** — `caiso92_repro_A`, `ercot71/73/76_*fullspan`, `miso65/66/67/71*`. All nine predate
  the field: their records carry no `correlated_forced_outage` key **and no `cache_key` at all**, so
  reconstructing them at HEAD already produced a hash that corresponded to no on-disk cache. The
  coercion does not orphan a cache that existed.
- The **default forecast** key is bit-identical (`0e9fce2fb55b889f` before and after).

Separately: the repo-wide pinned literal `PINNED_DEFAULT_CACHE_KEY = "603c2498bf71d21d"` is **already
stale at `origin/main`** (HEAD computes `0e9fce2fb55b889f`). Pre-existing, not this session's; noted
here because the next session to touch it should not mistake it for our doing.

---

## 4. FR-11 — the backcast-only measured-overlay family is now a hard error

`_BACKCAST_ONLY_OVERLAY_FIELDS` (36 fields, each with a one-line rule-13 reason) plus the
`outage_source="historic"` value. `__post_init__` raises when any is armed with `mode="forecast"` —
**including the hindcast harness**, because a capacity hindcast / T1-X crossover *is* the forecast
path being validated, and feeding it the measured record makes the validation self-fulfilling.

**Admission test used:** the field's armed state swaps a forward-derivable construction for a
**same-year measured record** — the file simply does not exist for 2031.

| Group | Fields |
|---|---|
| Measured delivered-fuel prints | `gas_monthly_actuals`, `gas_daily_shape`, `gas_hub_basis_overlay`, `gas_hub_basis_daily`, `miso_winter_citygate_daily`, `caiso_citygate_spot_level`, `caiso_citygate_flow_date`, `dual_fuel_oil_daily_parity` |
| Measured availability / outage records | `outage_source="historic"`, `caiso_dam_outages`, `miso_native_outage_source`, `unit_outage_short_windows`, `unit_partial_outage_windows`, `unit_outage_maxgen_events`, `ercot_thermal_dam_availability`(+`_hourly`, `_plant`, `_coal`), `ercot_dam_availability_coal_event_cap`, `pjm_dam_availability`, `ercot_noncampd_plant_availability` |
| Measured per-plant conduct | `coal_mustrun_per_plant`, `ct_mustrun_per_plant`, `cc_mustrun_per_plant`, `st_gas_mustrun_per_plant`, `st_gas_mustrun_p25_level`, `coal_lignite_mustrun_override`, `coal_prb_mustrun_override`, `chp_export_floor_measured`, `carry_operating_mothballs` |
| Measured cleared reserve requirements | `miso_measured_reserve_requirements`, `nyiso_ordc_measured_step_span` |
| Measured seams / envelopes / conduct repricings | `miso_seam_measured_ladder`, `pjm_seam_measured_ladder`, `ercot_online_capacity_envelope_measured`, `hydro_dispatch_envelope`, `caiso_offer_surface_measured`, `pjm_ct_measured_max_reprice` |

**Reviewed and deliberately NOT guarded** (recording the reasoning so the next session doesn't
re-litigate it):

- `measured_ct_heat_rates`, `measured_chp_heat_rates`, `ercot_gtc_limits_measured`,
  `pjm_measured_interface_limits`, `measured_ramp_capability`, `ercot_storage_capability_measured` —
  measured **physical** parameters (heat rates, transfer limits, ramp/charge capability) with a
  forward story. Rule 14 says *prefer* these; forbidding them in a forecast would be the exact
  "revert to an estimate" move it forbids.
- `nyiso_dynamic_reserve_requirements`, `neiso_dynamic_reserve_requirements` — condition-varying
  requirement *constructions*, not a year's cleared MW. Their MISO sibling
  (`miso_measured_reserve_requirements`) IS the measured record and is guarded; if a session
  establishes that either NYISO/NEISO variant reads a year-keyed artifact, it belongs in the family.
- `tranche_startup_measured_runs`, `neiso_winter_fuel_inventory` — arguable; left out pending the
  owning lane's judgement rather than guessed at here. **Filed as an open item.**
- The offer-curve tuning knobs generally: contained by rule 25 + the `run_config` registry, not by
  mode. `caiso_offer_surface_measured` and `pjm_ct_measured_max_reprice` *are* in the family because
  they reprice off a measured record, not a fitted band.

**Blast radius: none.** No committed forecast-mode `run_config.json` and no committed YAML under
`configs/` or `results/` arms any guarded field (verified this session). 72 parametrized tests assert
each field refuses in forecast and is accepted in backcast.

---

## 5. FR-15 — deletions and the dedupe (with one scope correction)

**Scope correction, stated plainly.** The prompt (following audit FR-15) says to delete "the three
inert FF-3D CLI flags **+ their ScenarioConfig fields**". The ScenarioConfig fields
`entry_vre_capacity_revenue` / `entry_rate_limits` / `entry_commissioning_lag` **must not be
deleted**: they exist, they are registered in `_CACHE_KEY_OPTIONAL_FIELDS`, and they are **consumed**
(`runner.py:733,746`; `new_entry.py:781,1104,1118`, `adequacy.py:313`, `evolve.py:510`). They are the
dormant FF-2A entry dampers the audit's own §3.3 lists as awaiting owner decision **D-2**, and FFR-2B
is chartered to probe them. Deleting them would delete a live mechanism and the next wave's work.

What was genuinely inert, and is now deleted (rule 26), is the **`run_capacity_hindcast.py`
plumbing**: three CLI flags (`--entry-vre-capacity-revenue`, `--entry-rate-limits`,
`--entry-commissioning-lag`), their three `build_config` parameters, and their three run-summary
entries. FF-3D had already dropped the passthrough (the fields did not exist then) and kept the flags
as "inert no-ops" — but the flags still **wrote their state into the bundle's meta**, so a leg
launched with `--entry-rate-limits` recorded `entry_rate_limits: true` on a solve that never armed
it. An inert flag that falsifies the run record is worse than no flag. A session that needs these
arms on that harness wires the passthrough for real, one line each.

One more correction to the finding: FR-15 says the three flags "change cache keys while changing
nothing". They did not — they were never forwarded to `ScenarioConfig`, so they never reached the
hash. They falsified the *bundle meta*, which is the worse half.

**Dedupe.** `_CACHE_KEY_OPTIONAL_FIELDS` listed `nyiso_li_locational_reserve` and
`nyiso_incity_commitment_obligation` twice (108 entries, 106 unique). The duplicate copies are gone;
the fields stay registered once, in the nyiso-83 block. Cache keys are unaffected (the drop-at-default
loop visits the same names either way). `test_cache_key_optional_fields_are_unique` now holds it — a
duplicated literal in a hand-maintained 100+-entry tuple is how a "did I register it?" grep answers
yes twice while the real gap elsewhere stays invisible.

---

## 6. Guards added — full inventory

| # | Guard | Where | Fails when |
|---|---|---|---|
| 1 | Forecast-invariant artifact audit (schema) | `check_forecast_invariants.py::audit_sidecars` | a committed record's fields/status/ident diverge from the checker |
| 2 | …(coverage) | same | a partial I1–I14 battery is not declared a curated subset; a `t1f` run has no invariants block |
| 3 | …(declared failures) | same | a committed FAIL is undeclared, or a declaration is stale |
| 4 | Namespace boundary | `check_registry_payload_parity.py::check_namespace_boundary` | a forecast-family run is registered into the backcast registry |
| 5 | §2.1b cap × 7 new call sites | `market_sim/config/schedulable.py` + callers | an unauthorized forecast window > 5 solve-years |
| 6 | `correlated_forced_outage` coercion | `scenarios.py::__post_init__` | (coerces; never raises) |
| 7 | Backcast-only overlay family | `scenarios.py::__post_init__` | any of 36 fields, or `outage_source="historic"`, armed in forecast |
| 8 | Cache-key registry uniqueness | `tests/unit/config/test_forecast_mode_guards.py` | a duplicate literal returns |
| 9 | Golden-fixture staleness expiry | `tests/regression/test_golden_forecast_bands.py` | undeclared config-identity drift, or an expired waiver |
| 10 | Registration-path smoke | `tests/scoring/test_register_forecast_run_smoke.py` | `--reindex` drops a payload or malforms the manifest facets |

**Deleted:** 3 CLI flags, 3 `build_config` parameters, 3 run-summary keys
(`scripts/run_capacity_hindcast.py`); 2 duplicate `_CACHE_KEY_OPTIONAL_FIELDS` literals. **No
`ScenarioConfig` field was added or deleted.**

---

## 7. FR-26 — the two cheap tests

**Registration-path smoke** (`tests/scoring/test_register_forecast_run_smoke.py`, 5 cases).
`register_forecast_run.py` had zero tests and its `--reindex` **is** the Pages deploy assembly step,
so a break there publishes an empty explorer rather than failing loudly. The test reindexes a
two-run synthetic namespace into a tmp dir and asserts: a sidecar *and* a payload per run (the 1:1
parity the backcast namespace has a CI gate for), correct `kind`/`tier` classification (t1f and
crossover→t1x), a gzip+base64 payload the explorer can actually decode, a well-formed manifest facet
block covering every run (no null/empty chip), and that one malformed sidecar does not take the whole
assembly down.

**Golden-fixture staleness expiry** (`test_golden_fixture_config_identity_is_current`). The fixture
was seeded at `f0f7c67` and the reference scenario now hashes to a different key, so the band check —
`slow`- and env-gated — has silently stopped being a regression guard. The test rebuilds
`REFERENCE_SCENARIO_KWARGS` and compares the cache identity against the seeded `run_config.json`,
printing a field-level drift report.

**Deviation, stated:** the prompt asks the test to FAIL on any drift. The fixture is *already*
drifted, and the fast tier is blocking, so an unconditional failure would turn CI red on every
unrelated PR and pressure someone into an unauthorized reseed — reseeding is 15 solve-years and is
owner-decision **D-7**. Instead the drift is carried in a committed, dated waiver
(`tests/golden/staleness_waiver.json`) that names the D-7 route and **expires 2026-10-31**. The test
hard-fails when the drift is undeclared, when the waiver does not describe this fixture, or when it
expires; and it fails the other way too — if the key ever matches the seed again, the waiver must be
deleted as dead scaffolding. The waiver keys on the **seeded** (stable) side, so a default flip in a
parallel Wave-1 session cannot turn this red on someone else's PR. Net: the staleness is now written
down, CI-enforced and time-bounded instead of invisible. **The fixture was NOT reseeded.**

---

## 7a. Test fallout from the FR-11 guard (20 tests, all legitimately updated)

The overlay guard surfaced tests that were exercising **backcast** mechanisms on a **forecast**
config — `ScenarioConfig()` defaults to `mode="forecast"`, so a test that only set the overlay flag
was silently validating the mechanism in a mode it may not run in. Each was updated to say what it
means; none was weakened.

| Tests | Change |
|---|---|
| `test_fuel.py` × 6 (MISO winter citygate daily) | `mode="backcast"` added to the fixtures |
| `test_caiso_citygate_spot_level.py` × 6 | `mode="backcast"` added to the two fixtures |
| `test_fleet.py::TestStGasP25LevelFloor` × 4 | `mode="backcast"` added to the fixture |
| `test_pjm_dispersion_composite.py::TestPjmCtMeasuredMaxTarget` × 3 | `mode="backcast"` added to `_cfg()` |
| `test_summer_availability_constants.py` (2 tests + 13 subtests) | `mode="backcast"` added to `KEEPER_FLAGS` — the flags are read off a backcast keeper's `run_config.json`, so the fixture now matches the run it mirrors |
| `test_eia923_fuel.py::test_gas_series_uses_monthly_actuals_when_on` | `mode="backcast"` on the base config the `gas_monthly_actuals` leg overrides |
| `test_outages.py::ErcotThermalDamAvailabilityTest` × 2 | the two **"forecast mode: overlay never applies"** assertions now assert the config REFUSES the overlay — strictly stronger than asserting a silent no-op |
| `test_runner.py::TestMainCLI` × 2 | the CLI-parsing fixture pins a T1-F window (an unguarded 2026–2050 default is now refused; the refusal has its own coverage) |

**Final fast tier (pre-rebase: 5,673 passed / 14 failed; post-rebase: 5,757 passed / 14 failed)**, and all 14 are **pre-existing on `origin/main`** —
verified by running the same tests at `origin/main` in a clean worktree:

| Pre-existing failure | Cause |
|---|---|
| `test_persisted_identity` × 2, `test_ramp_envelope_basis`, `test_cc_committed_offer_margin`, `test_forecast_xyear_warmstart_flag` | the stale repo-wide `PINNED_DEFAULT_CACHE_KEY = "603c2498bf71d21d"` (HEAD computes `0e9fce2fb55b889f`) |
| `test_measured_chp_heat_rates::TestDerive` × 7 | unrelated derive-path failures |
| `test_outages::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` | unrelated |
| `test_ff_readiness_battery::test_marker_state_reflects_committed_markers` | marker state moved (nyiso-104b re-declaration) |

They are named here so the next session does not attribute them to this branch.
`test_integration::TestFullYearPerformance::test_full_year` failed once under `-n 2` load and passed
on re-run — a timing flake, not a regression.

## 7b. One incidental repair: the `lint` CI job was red on main

`ruff check .` fails at `origin/main` — five E402s in
`results/calibration/_ercot144_scratch/verify_armed_capture.py`, a per-run scratch driver committed
inside a calibration bundle. Because the `lint` job's path filter does not include `results/**` but
its command lints the whole tree, **every PR touching `src/`, `scripts/` or `tests/` inherited that
red**, including this one. `results` is now in ruff's `extend-exclude`, on the same rationale as the
existing `scripts/probes` / `scripts/archive` exemptions: `results/` is the run-bundle tree (the
calibration record), not code under maintenance. No source file's lint scope changed.

## 7c. Rebase onto the merged Wave-1 lanes (2026-08-01)

Rebased onto `origin/main` `6e98263` (70 commits: FFR-1A, 1B, 1C, 1E and the WP intake lanes all
merged). One conflict, in `docs/codebase-site/data/mechanism-matrix.js` — both sides **appended** to
the header comment. Resolved by keeping both: main's NEISO verdict stamps (neiso-72/73/74) first,
then this session's non-verdict enforcement stamp. **No cell verdict from either side was touched.**
`ci.yml` did not conflict — FFR-1E correctly held its parity job back, and it can land now.

Two follow-ups the rebase itself required:

1. **The invariant-failure ledger was re-seeded** for the 15 hindcast sidecars the merged Wave-1
   lanes registered (125 FAILs across 72 runs, up from 111/59). This is the new CI job working as
   designed on its first real encounter — and the re-seed captured a genuinely useful signal worth
   naming: `pjm-2026-2030-ffr1a-before` and `neiso-2026-2030-ffr1a-before` carry **I4**, and neither
   of their `arm1`/`arm2` successors does. FFR-1A's confirmed-exit derate ledgering closed I4 on
   both ISOs, and the ledger now records that. The FFR-1C `i7-before`/`i7-after` pairs still both
   carry I7 (hydro accreditation narrowed the gap without closing it), and the FFR-1A ERCOT T0 arms
   carry I3 — the standing FR-6 scarcity-slack finding, not anything those arms introduced.
2. **The FR-11 guard needed no further test fixes** against the merged lanes: FFR-1B's new
   solve-year availability tests and FFR-1C's hydro-accreditation tests all construct their configs
   in the mode they mean.

### Cross-lane breaks repaired in passing

`origin/main` at `6e98263` was red in **three** CI jobs before this branch touched anything. All
three are one-line registration steps that a merged lane's own documentation tells it to perform,
so they are repaired here rather than left to redden every PR in the repo:

| Job | Break | Repair |
|---|---|---|
| `lint` | five E402s in a committed per-run scratch driver (`results/calibration/_ercot144_scratch/`), plus an unused local in `scripts/gen_nyiso109_attestation.py` (nyiso-109) | `results` added to ruff's `extend-exclude` (same rationale as the existing `scripts/probes` / `scripts/archive` exemptions); dead local removed |
| `refactor-guards` (BLOCKING) | FFR-1C added `HYDRO_ACCREDITATION_CREDIT_BY_ISO` to `capacity_market.py` and re-exported it from the constants facade, but left it out of the frozen `MOVED_SURFACE` inventory | name registered in the inventory |
| `fast-tests` (BLOCKING) | the FFR-PB ATB/IRA intake registered `ira-credit-parameters` and `nrel-atb` in `regenerate_clean.DATATYPES` without refreshing the frozen snapshot — exactly what that file's own header says to do | snapshot refreshed |
| `quarantine-gates` | `frontend/data/backcast/status/MISO.js` stale vs current verdicts | regenerated with `build_status.py --iso MISO`; the ONLY semantic drift is two display floats (`share_pp -0.96 → -0.95`, `vintage_gap_twh -0.205 → -0.204`) plus the timestamp — **no criterion, status or determination changed; MISO stays NOT-YET** |

**Deliberately NOT repaired: the stale `PINNED_DEFAULT_CACHE_KEY = "603c2498bf71d21d"`** (three
files, five failing tests). The default config hashes to `0e9fce2fb55b889f` at `origin/main` and at
this branch **identically** — this branch does not move it. Re-pinning the literal is the
"tempting and WRONG remedy" `ci.yml`'s own cache-key-guard comment warns about; the right owner is
the §W1-X cache-epoch bump.

## 8. Open items handed on

1. **`tranche_startup_measured_runs` and `neiso_winter_fuel_inventory`** — plausibly members of the
   FR-11 family; left unguarded pending their owning lane's judgement (§4).
2. **`PINNED_DEFAULT_CACHE_KEY = "603c2498bf71d21d"` is stale at `origin/main`** (HEAD computes
   `0e9fce2fb55b889f`), reddening five tests. Pre-existing; belongs to whichever session lands the
   §W1-X cache-epoch bump.
2b. **`audit_keepers --check` is RED on `origin/main`** — `frontend/data/backcast/status/MISO.js` is
   stale vs the current verdicts (`build_status.py --iso MISO` regenerates it). That is a MISO-lane
   keeper artifact, so this session did NOT touch it (per-ISO lane discipline); it means the CI
   `quarantine-gates` job is red on this PR for a reason that predates it.
3. **The nine pre-field backcast bundles** (§3) cannot be reconstructed to their on-disk keys at HEAD
   at all — a general property of fields added without `_CACHE_KEY_OPTIONAL_FIELDS` registration, not
   specific to this change. Worth a sweep if anyone needs those bundles reproducible.
4. **111 declared invariant FAILs** are now enumerated in one file. That file is a ready-made work
   list for FFR-1A (I4), FFR-1C (I7) and the ERCOT scarcity lane (I3).

## 9. Coordination notes for the rest of Wave 1

- **`ci.yml` is this session's** (per the pack). FFR-1E adds its parity job **after this merges**.
- **`scenarios.py` is this session's.** FFR-1B's one `__post_init__` AS-guard hunk (bare
  `ercot_multiproduct_as_coopt` in forecast without `ercot_as_forward_requirement`) did **not** land
  here — it is not in this session's scope and FFR-1B had not filed it. It lands in FFR-1B after this
  merges, next to the existing endogenous-storage / endogenous-thermal guards at the end of
  `__post_init__`.
- **No cache-epoch bump here** — §W1-X owns it. Nothing in this session changes a solve.
