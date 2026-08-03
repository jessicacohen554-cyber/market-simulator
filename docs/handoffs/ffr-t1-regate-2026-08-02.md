# FFR-3A — owner decisions executed; T1-F battery run; **D-1/D-2 cause an adequacy collapse**

**Session.** FFR Wave 3, the owner-execution + consolidated-battery lane
(`docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-3A). Branch
`claude/ffr-3a-owner-decisions-t1-d0eh6p`, rebased onto `origin/main` **`f6d9a4b`**
(2026-08-03 — main moved twice mid-session; see §7.1).

**One-line result.** **Step 0 is complete and pushed**: every signed decision is executed,
and executing them surfaced **four defects, three of which would have silently invalidated
this session's own battery**. The T1-F half of the battery then **ran** (after clearing an
unanticipated `data/clean` prerequisite, §6.1) and returns a **headline finding the owner
needs before anything is promoted: the signed decisions D-1 + D-2 drive a severe
capacity-adequacy degradation across every ISO measured** — in ERCOT, attributed against a
paired control arm. **Nothing is tuned, nothing is unarmed, nothing is registered** (rules
1/14): the finding is written up in §6.4 as an open blocker for the owner, not acted on.

> **⚠ READ §6.4 BEFORE PROMOTING ANYTHING.** ERCOT's reserve margin reaches **−1.5 %** and
> CAISO's **−3.1 %**. The owner signed D-2 accepting a *disclosed adequacy change* (MISO's
> I12 going WARN→FAIL); what was measured is materially larger and broader than that
> disclosure. This is a finding, not a recommendation — the call is the owner's.

---

## 1. The signed decisions — what executed

| # | Decision | Signed | Status | Commit |
|---|---|---|---|---|
| D-1 | `retirement_rule` `legacy` → `pipeline` | FLIP | **EXECUTED** | `24b1602` |
| D-2 | `entry_rate_limits` + `entry_commissioning_lag` | ARM BOTH | **EXECUTED** | `3e33f15` |
| — | D-1/D-2 runner propagation (§3.3) | (execution of the above) | **EXECUTED** | `f5da701` |
| — | FFR-2C epoch debt (packet B.6) | (owed before the battery) | **CLEARED** | `89d0e54` |
| D-7(ii) | Weather-conditional label | (a) single draw + label | **EXECUTED** | `05a367e` |
| D-3b | Forward real escalation rate | 0.0 REAL CENTRAL | **VERIFIED NO-OP** | — |
| D-6 | FF-3D NYISO pair evidence | SCHEDULE via FFR-3A | **PARTLY — see §5** | — |

**D-3b is a no-op, confirmed.** `NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO`
(`capacity_market.py:1520`) already ships `0.0` for **all five** ISOs carrying a rate
(PJM, NYISO, NEISO, MISO, CAISO). The signature confirms the shipped value; no code changed.

### 1.1 Deliberately NOT executed

| Item | Why |
|---|---|
| **D-2′ `entry_vre_capacity_revenue`** | Signed **HOLD**. Verified still `False`. |
| **D-3a net-CONE forward-evolution mode** | **DEFERRED, never re-signed.** Verified still `"hold_last"`. Untouched. |
| **D-4 forward fuel path** | OPTION A = status quo. No change. |
| **D-7(i) golden reseed** | **NOT AUTHORIZED.** No reseed was run; `--full-solve-authorized` was never passed. The label in §4.4 is metadata-only, asserted band-identical. |
| **D-5(a)/(b)/(c), D-7(i) waiver** | Already executed by FFR-3B (`aaf6297`, `37d2ee7`, `e19986c`, `a26443b`). Confirmed on main; not redone. No marker file touched. |
| **C.4(a) B1 — runner posture default** | **UNSIGNED** new owner decision. Left as found; worked around per §4.3 without a code change. |
| **C.4(c) — harness `correlated_forced_outage` / `entry_lookahead_reprice` pins** | **UNSIGNED** new owner decision. Left as found; it **confounds** the T1-H legs (§6.2). |

---

## 2. Keeper integrity — the stop-the-line check

**No keeper moved as a result of any change in this session.** Verified without a solve:

1. **The flips are inert in backcast by construction.** `scripts/run_calibration_full.py`
   builds a *"pristine per-year config"* and solves each backcast year as its own
   single-year invocation, so `runner.py`'s `fleet` is `None` at every year start and
   `build_base_fleet` runs instead of `evolve_fleet`. The backcast therefore has **no
   capacity evolution**, and `retirement_rule` / both entry gates drive nothing but
   forecast-mode evolution.
2. **No keeper's cache key moves.** `cache_key(ScenarioConfig())` is `603c2498bf71d21d`
   before **and** after all three flips (§3.1), and no keeper sets any of the three fields.

**One caveat, flagged not fixed.** Keeper `run_config.json` files record all three fields
*explicitly* (`asdict` serialises every field), e.g. `neiso72_hy_window_B` carries
`retirement_rule: "legacy"`. Post-flip those values are **non-default**, so a keeper
**replayed from its `run_config.json`** now hashes to a different key and takes a cache
miss. The re-solved dispatch is identical (point 1), so this is a cache-efficiency and
provenance-reading issue, **not** a result change — but a successor replaying a keeper
should expect a cold solve and should not read the new key as evidence of drift.

---

## 3. Defects found while executing the decisions

Three of these four would have silently corrupted the battery this session exists to run.

### 3.1 The packet's D-1 cache-key premise is wrong (`89d0e54`)

The sitting states the field is *"cache-key-registered at non-default, so the flip moves
forecast cache keys by construction — no silent reuse."* **It does not.**
`cache_key()` drops a `_CACHE_KEY_OPTIONAL_FIELDS` member when it equals
`getattr(ScenarioConfig(), name)` — the **live** default, recomputed per call, not a frozen
sentinel (`scenarios.py:9875`). Flipping such a default drops the **new** value from the
hash, so the key does not move.

Measured:

| config | key |
|---|---|
| `ScenarioConfig()` — pre-flip (default `legacy`) | `603c2498bf71d21d` |
| `ScenarioConfig()` — post-flip (default `pipeline`) | `603c2498bf71d21d` |
| `ScenarioConfig(retirement_rule="legacy")` post-flip (now non-default) | `0e49083ebacb2612` |

So a pre-flip legacy bundle and a post-flip pipeline config **collide**. Handled as a
same-key invalidation in the cache-epoch ledger, which is the mechanism `cache.py` documents
for exactly this. The inverse is load-bearing and good: explicit-`legacy` **control arms**
hash distinctly, so battery arms remain separable. **This will silently recur on any future
default flip of an optional-registered field.**

### 3.2 Latent `TypeError` exposed by arming D-2 (`3e33f15`)

`ScenarioConfig.start_year` defaults to `None`, and the growth-ladder seed read
`config.eia860_vintage_year or (config.start_year - 1)` (`runner.py:799`) — unreachable
while `entry_rate_limits` was default-off, **live the moment D-2 armed it**. 26 tests across
`pipeline/runner`, `results/matrix` and `pipeline/api` hit
`TypeError: unsupported operand type(s) for -: 'NoneType' and 'int'`. Fixed by anchoring on
the horizon start the runner **already resolves** at `runner.py:505`; no new value invented,
and any config that sets `start_year` is bit-unaffected.

### 3.3 The T1 runners would have made both signed decisions INERT (`f5da701`)

`run_full_horizon.py` (T1-F) and `run_capacity_hindcast.py` (T1-H/T1-X) each carried their
**own** copies of the pre-flip defaults — `retirement_rule="legacy"`, `entry_*=False` — and
passed them to `ScenarioConfig` unconditionally. FFR-2B wrote those literals as deliberate
mirrors, noting *"the flips are the owner's, executed at FFR-3A step 0."* This is that step,
and the mirrors had inverted from harmless to actively wrong: **every T1-F/T1-H/T1-X leg
would have silently overridden D-1 and D-2 and re-measured the configuration the owner just
retired.**

Fixed with a `None` sentinel meaning *inherit*, plus `argparse.BooleanOptionalAction` so an
armed default stays falsifiable (`--no-entry-rate-limits`). This is the FFR-2E instrument
pattern ("reading the live default, never mirroring it") and keeps `ScenarioConfig` the
single source of truth (rule 24).

### 3.4 Second instance of a defect FFR-2E already fixed (`05a367e`)

`full_horizon_summary.json` recorded `capacity_market_clearing` from the **scalar** flag.
FFR-2E fixed precisely this in the sibling harness and gave the reason: `forecast_verdict.
_curve_on` reads that key, so a flag-sourced value *"would have mis-classified every
shipped-posture leg as curve-OFF."* The same defect was still live in the T1-F runner.
Measured: `reference_config("PJM", golden_posture=True)` → scalar `False`, **resolved
`True`**. Every curve-ON T1-F leg was recording itself curve-OFF, which would have
mis-scored this session's own battery. Now records the resolved per-ISO gate plus the full
by-ISO dict.

---

## 4. Evidence for the execution

### 4.1 Test lanes — zero net regressions

Every lane baselined on stashed/checked-out `origin/main`, then re-run. **The final failure
*set* is byte-identical to the baseline set in all three lanes** (`diff` empty).

| Stage | `tests/unit` + `tests/regression` | `tests/scoring` |
|---|---|---|
| `origin/main` baseline | **20 failed** / 3506 passed / 135 subtests | **4 failed** / 873 passed |
| after D-1 | 27 failed / 3499 passed | — |
| after D-1+D-2 (pre-fix) | 51 failed / 3480 passed | 14 failed / 863 passed |
| **after D-1+D-2+fixes** | **20 failed** / 3506 passed / 135 subtests | **4 failed** / 873 passed |

The 20 + 4 baseline failures are **pre-existing on `origin/main`** and untouched
(`test_soundness`, `test_export`, `test_measured_chp_heat_rates`, `test_outages`,
`test_constants_facade`, `test_fleet_arrays_golden`, `test_ff_readiness_battery`).
`test_integration::test_full_year` flaked once under full-suite load and passes in
isolation (23 s).

### 4.2 Test changes were fixtures, not model behaviour

All 45 touched assertions were fixtures that had silently inherited a default:
they either omitted the `year=` the **dated** pipeline requires, or asserted the **legacy
loss-year counter** / same-year deactivation. Each now pins `retirement_rule="legacy"`
explicitly and tests exactly what it always tested; `TestPipelineRetirementRule` covers the
pipeline side. Two were **strengthened**:

* `test_forecast_warmstart_tie_invariance` — **both** sites pinned. Unpinned, the loss
  counter is `{}` on both sides and the basis-independence assertion would have passed
  **vacuously**.
* `test_crossover_harness::test_entry_dampers_*` — renamed and rewritten to assert
  **inheritance from `ScenarioConfig()`** rather than a literal, so it now fails if a
  mirrored literal is reintroduced and survives any future owner flip.

### 4.3 The shipped curve arm, per ISO (binding citation, FFR-2E)

Resolved from `ScenarioConfig.capacity_market_clearing_by_iso` = `{PJM, MISO, CAISO, NEISO}`,
**not** from which leg exists:

| ISO | **SHIPPED** | T1-F default leg | `--golden-posture` |
|---|---|---|---|
| ERCOT | curve-OFF (energy-only) | OFF ✓ | OFF ✓ |
| PJM | **curve-ON** | OFF ✗ | ON ✓ |
| CAISO | **curve-ON** (provably inert — no published curve) | OFF ✗ | ON ✓ |
| NEISO | **curve-ON** | OFF ✗ | ON ✓ |
| MISO | **curve-ON** | OFF ✗ | ON ✓ |
| NYISO | **curve-OFF** | **OFF ✓** | ON ✗ |

**Neither available posture reproduces the shipped arm for all six.** `--golden-posture`
matches for five and diverges only on NYISO; the plain default diverges on four. The battery
is therefore specified as **`--golden-posture` for ERCOT/PJM/CAISO/NEISO/MISO and the plain
default for NYISO**, which reproduces the shipped arm for **all six using existing flags
only** — no code change, no unsigned decision executed. This is FFR-2E's B1 (C.4(a)),
recorded and worked around, **not** fixed.

### 4.4 D-7(ii) label

`WEATHER_POSTURE` quotes the standing disclosure list verbatim
(`forecast-readiness-peer-review-2026-07.md` §4 — the single wording authority) and now
travels **with the artifact**: emitted by `golden_forecast_bands.py seed`, emitted into every
`full_horizon_summary.json` alongside the run's actual `weather_year`, and stamped onto the
already-committed `tests/golden/ercot_2026_2040.json`. The stamp asserted in-place that
`bands`, `golden` and `scenario` are **byte-identical** after it. **No reseed was run.**

---

## 5. D-6 — NYISO pair

**Half done, half blocked.** The correction FFR-2E asked for is **already on main**: FFR-3B
corrected `ff-t1-gate-2026-07.md` §4.1, which now cites `nyiso-2021-2025-fixed` as the
corrected arm and strikes `nyiso-2021-2025-curve` as *"(force-ON probe, not the shipped
posture)"*. **Verified — no correction was needed from this session.**

**The regeneration itself did not happen**, because it is a solve and is blocked by §6.1.
Its specification is fixed and recorded here: NYISO's shipped posture is **curve-OFF**, so
the regenerated pair is the **plain-default** leg (per §4.3), not `--capacity-market-clearing`.

---

## 6. The battery — prerequisite, results, and the headline finding

### 6.1 THE PREREQUISITE (cleared) — `data/clean` is empty on a fresh container

The first T1-F pair (NEISO + NYISO) was launched and **failed within seconds**, correctly and
loudly:

```
RuntimeError: confirmed-retirements: clean partition for NEISO is absent while
confirmed_exits_enabled is on in forecast mode. data/clean is derived and gitignored,
so a fresh checkout has no registry; refusing to silently degrade to the economic
screen (W1-B B3: ERCOT's 2026 fleet gains 477 MW — V H Braunig backlog)
```

`data/clean` held **zero** datatypes. This is the same class of defect the CAISO keeper note
records (*"data/clean is gitignored and dies with the container"*) — here it blocks the
forecast path entirely. `confirmed-retirements` was curated out-of-band to unblock that
specific error (5 partitions; NYISO is a legitimate **researched zero** and degrades to a
warning once the registry exists), and `scripts/regenerate_clean.py` was run to completion.

**MEASURED COST OF THE PREREQUISITE (budget for it explicitly — it is a prerequisite, not a
step):**

| | |
|---|---|
| wall time | **≈55 min** (first parquet → last), sequential, on a 4-core / 15 GB container |
| datatypes | **50 regenerated, 0 failures** |
| output | **446 parquet files, 1.6 GB** |
| dominant cost | the CAMPD `emissions` extract — **≈26.5 M rows per year**, written year by year |

The heavy EIA-930-scale curations (`lmp`, `load`, `generation`, `emissions`, `renewables`)
account for most of the wall time; the ~40 remaining reference tables complete quickly.

> **A successor must run `scripts/regenerate_clean.py` to completion — and confirm the
> `regenerated N datatype(s)` line — before launching any leg.**

**Do not mistake the two summaries those failed legs left behind for results.** Both legs
wrote a `full_horizon_summary.json`. To the runner's credit these are **honest** — each
carries the full `error` string, `"n_solved_years": 0`, `"solved_years": []` and a null
`cache_key`. The one genuinely misleading surface is the **console** line, which prints
`invariants: 0 FAIL, 0 WARN`: invariant scoring over a zero-year run passes trivially, so a
hard failure reads as a clean gate at a glance. The summaries are vacuous, live under
`results/ffr3a/t1f/`, and are **not registered** anywhere. A successor should key on
`n_solved_years`, never on the invariant line.

### 6.2 Standing confound on the T1-H half (unsigned, do not fix silently)

`run_capacity_hindcast.py` still pins `correlated_forced_outage=False` and
`entry_lookahead_reprice=False` while production ships **both `True`** — sitting C.4(c).
FFR-2B's D-1 evidence carries the same caveat. It is an **unsigned** harness-default owner
decision, so it was left exactly as found; but any T1-H leg the successor runs inherits the
confound, and the re-gate cannot claim to measure the shipped configuration on that half
until it is signed either way.

### 6.3 T1-F measured results (2026–2030, shipped posture per §4.3)

Every leg cold-solved post-epoch, 5/5 years, `error: None`. **Read `n_solved_years`, never
the console `invariants:` line** (§6.1). `curve` is the RESOLVED per-ISO arm now recorded
correctly by the §3.4 fix — each matches its ISO's shipped arm, which is what the §4.3
posture split was built to achieve.

| leg | yrs | wall | peak RSS | curve | shipped? | cache key | FAIL | WARN |
|---|---|---|---|---|---|---|---|---|
| NEISO | 5/5 | 6.7 m | 3.32 GB | `True` | ✓ ON | `bc01afd6e7866422` | I7 | I12 |
| NYISO | 5/5 | 9.7 m | 3.84 GB | `False` | ✓ OFF | `2bd878d87848785c` | I7 | I12 |
| ERCOT | 5/5 | 8.6 m | 4.01 GB | `False` | ✓ energy-only | `ab1d074828bebabe` | I3, **I12** | I14 |
| CAISO | 5/5 | 18.1 m | 5.06 GB | `True` | ✓ ON | `862d176d609252f9` | I3, **I7**, **I12** | — |
| *ERCOT **control*** | *5/5* | *8.8 m* | *4.02 GB* | *`False`* | *pre-decision* | `e9e5e1c911c6424c` | *I3* | *I12, I14* |

PJM and MISO were still solving when this was written; §9 records what that leaves open.

### 6.4 ⚠ HEADLINE FINDING — D-1 + D-2 cause a capacity-adequacy collapse

**Every ISO measured fails an adequacy invariant** (I7 accredited-firm floor and/or I12
reserve-margin band). Two are severe:

* **ERCOT** — reserve margin declines monotonically **9.1 % → 3.8 % → 3.0 % → −1.5 %**
  (band [13.8 %, 28.7 %]) with unserved energy rising to **0.41 % of load**.
* **CAISO** — reserve margin **negative from 2027** (1.8 %, −3.1 %, −0.3 %, …; band
  [15.0 %, 30.0 %]) and accredited firm capacity short by **6.6 GW in 2026 widening to
  9.2 GW**.

**Attribution — ERCOT, against a paired control arm.** The control re-runs the identical
leg at the *pre-decision* defaults (`--retirement-rule legacy --no-entry-rate-limits
--no-entry-commissioning-lag`) and takes a distinct cache key, confirming it is genuinely a
different scenario (the §3.1 separability property doing its job):

| invariant | TREATMENT (D-1+D-2, shipped) | CONTROL (pre-decision) | |
|---|---|---|---|
| **I12** reserve margin | **FAIL** — 4-year decline to **−1.5 %** | **WARN** — one year only (2030: 12.4 %) | **MOVED** |
| **I3** unserved | FAIL — up to **0.41 %** of load | FAIL — flat **0.02–0.03 %** | ~**14×** worse |
| I14 price | WARN | WARN | unchanged |

So in ERCOT the signed decisions **cause** the collapse. I3 fails in *both* arms, so a small
slack is pre-existing on main — but its magnitude is D-1/D-2. Causal commits: **`24b1602`**
(D-1) and **`3e33f15`** (D-2), first reachable in a T1-F leg via **`f5da701`**.

**Mechanism (coherent, not a bug).** The pipeline rule screens
`net_revenue < going_forward_cost`; in energy-only ERCOT there is no capacity revenue to
offset it, so it retires readily, while `entry_rate_limits` caps how fast replacement can
arrive. Retirement accelerates and replacement is throttled — exactly the two halves the
owner armed together.

**Why this still needs the owner.** D-2 was signed accepting a *disclosed adequacy change* —
specifically **MISO's I12 going WARN→FAIL**. What was measured is materially larger
(negative reserve margins, ~14× unserved energy) and broader (every ISO measured). **CAISO
matters most for scope**: it *pays* a capacity price (the flat CPM proxy — FFR-2E proved its
curve arm inert for want of a published demand curve) and still goes negative, so this is
**not** confined to energy-only markets.

**Scope limit, stated plainly.** Only **ERCOT** is attributed. One control does not license a
causal claim about five other markets, and CAISO's capacity-market structure differs
materially. The cross-ISO pattern is an **observation**; MISO is the highest-value second
control, since the sitting predicted its I12 flip by name.

**Nothing was tuned, unarmed, or band-widened in response (rules 1/14).** A structurally
grounded mechanism does not get reverted because a metric moved; the correct output is this
finding, with its evidence, for the owner.

### 6.5 T1-F gate scorecard (`forecast_verdict --tier t1f`, rubric v1.0)

Scored from **committed artifacts only, no LP re-solve**. Artifacts:
`results/ffr3a/scorecard/<leg>.{json,txt}`.

| leg | ISO | **determination** | FC-1 | FC-2 | FC-3 | FC-5 | FC-6 | FC-7 | FC-8 |
|---|---|---|---|---|---|---|---|---|---|
| NEISO | NEISO | **HOLD** | FAIL | CAVEAT | n/a | SKIP | SKIP | FAIL | PASS |
| NYISO | NYISO | **HOLD** | FAIL | CAVEAT | n/a | SKIP | SKIP | FAIL | PASS |
| ERCOT | ERCOT | **HOLD** | FAIL | **FAIL** | n/a | SKIP | SKIP | FAIL | PASS |
| CAISO | CAISO | **HOLD** | FAIL | **FAIL** | n/a | SKIP | SKIP | FAIL | PASS |
| PJM | PJM | **HOLD** | FAIL | CAVEAT | n/a | SKIP | SKIP | FAIL | CAVEAT |
| *ERCOT **control*** | *ERCOT* | ***HOLD*** | *FAIL* | ***CAVEAT*** | *n/a* | *SKIP* | *SKIP* | *FAIL* | *PASS* |

**Every leg is HOLD. Nothing is promotable, and nothing is promoted.**

**FC-7 fails on EVERY leg for the same instrument reason, so it does not
differentiate anything.** `run_full_horizon.py` writes `config.yaml` into the cache dir but
never a `run_config.json`, which is the artifact FC-7 requires — so a T1-F bundle produced by
this runner **cannot** pass FC-7 by construction. This was left as found: authoring that file
now, *after* seeing the score, is precisely the "tuned into a band" move the rubric forbids
(§4). It is logged as open blocker §8.7 for a successor to fix in the instrument, not in a
bundle.

**FC-3 is `n/a` on every leg** because no T1-H hindcast was run (§9) — the four curve legs
D-1 re-opens are still unscored.

**⚠ The rubric-level attribution — ERCOT FC-2 moves CAVEAT → FAIL.** This is stronger evidence
than the raw invariants in §6.4, because it is the scorer's own category verdict changing
under the paired control:

| FC-2 row | TREATMENT (D-1+D-2) | CONTROL (pre-decision) |
|---|---|---|
| row1 reserve-margin band | **FAIL** — I12 FAIL, 4 years out, to −1.5 % | **CAVEAT** — I12 WARN, 2030 only (12.4 %) |
| row6 sustained-VOLL *(report)* | **FAIL** — `hours_ge_500` peaks **1,137 h/yr** > 800 | *row does not fire* |
| row4 backstop split | SKIPPED (instrument gap, both arms) | SKIPPED (same) |

The signed decisions do not merely widen an excursion — they introduce a **new** failure mode
the control never exhibits: sustained scarcity pricing at 1,137 hours/year ≥ $500/MWh, the
price signature of a structurally short system.

### 6.6 Nothing was registered, and nothing should be

No forecast run was registered; `frontend/data/forecast/` is untouched, `ff-verdicts.json`
and `program-status.json` are unchanged, and the FF-3E scorecard was not regenerated —
because there is no measurement to register. The backcast registry was never touched.

---

## 7. Other findings

### 7.1 The NYISO keeper moved mid-session (upstream, not this session)

The dispatch brief pinned NYISO at `2026-08-02-nyiso112-ramp-plus-peaker`, which matched
`keepers/NYISO.json` at session start (`5e934b8`). After rebasing onto the newer
`origin/main` `f6d9a4b`, the NYISO keeper reads **`2026-08-02-nyiso-113-li-locational`**.
This is upstream keeper churn, **not** a keeper moved by this session's changes (§2), but any
citation taken from the dispatch brief is already stale. `main` also moved twice during the
session (`5e934b8` → `276b221`-era → `f6d9a4b`).

### 7.2 The documented cache-purge command deletes tracked files

The purge loop in `cache.py`'s 2026-08-02 entry, extended to the obvious sibling directories,
deleted **410 tracked** evidence files (`results/ff2b-after/`, `results/ffr1c/` — registered
`evolution_<year>.json` and `full_horizon_summary.json` artifacts cited by their handoffs).
Restored with `git checkout -- results/`; a warning is now recorded in the ledger entry
(`89d0e54`). Check `git status --short` after any purge.

### 7.3 Push transport

The documented trap (`git remote prune origin`) was **not** the failure here. The real cause
was a **stale `origin/main`**: the remote's `main` had advanced to a commit this checkout did
not have, so git could not delta against the advertised tip and packed from scratch
(647 KB → HTTP 413). `git fetch origin main` + rebase reduced the thin pack to **21 KB** and
the push succeeded. **Fetch main before diagnosing a 413.**

### 7.4 Mechanism matrix (rule 28)

Both affected rows re-stamped in-session: `economic_retirement_screen` and
`entry_stack_ff2a` `def:` fields now carry the new defaults with corrected line refs
(the retirement row's `:900` was stale; the entry row's `:2197/:2214/:2184` were stale).
`check_mechanism_matrix.py` passes. **No cell *verdict* was changed** — no mechanism was
tested this session, so there is nothing to adjudicate.

---

## 8. Open blockers (not fixed, per rules 1/14)

0. **⚠ D-1 + D-2 cause a capacity-adequacy collapse (§6.4)** — ERCOT reserve margin to
   **−1.5 %**, CAISO to **−3.1 %**, unserved energy ~14× the control in ERCOT; every ISO
   measured fails an adequacy invariant. Attributed against a paired control **in ERCOT
   only**. Larger and broader than the adequacy change D-2 was signed against. **Owner
   decision — do not promote on these legs without reading §6.4.**
1. **`data/clean` is a hard, undocumented prerequisite** for every forecast leg; measured at
   **≈55 min / 50 datatypes / 1.6 GB** on a fresh container (§6.1).
2. **C.4(a) B1** — no flag combination expresses the shipped per-ISO posture for all six
   ISOs; `GOLDEN_CMC_BY_ISO` and the shipped dict disagree on NYISO (§4.3). Unsigned.
3. **C.4(c)** — the T1-H harness pins two fields against production (§6.2). Unsigned.
4. **The optional-field cache-key hazard** will silently recur on the next default flip
   (§3.1). Structural; needs a decision, not a patch.
5. **The T1-F console line reports `invariants: 0 FAIL, 0 WARN` on a zero-year run** (§6.1).
   The JSON summary is honest; the console line is what can make a hard failure read as a
   clean gate.
6. **20 + 4 pre-existing test failures on `origin/main`** (§4.1), untouched and unexplained
   by this session.
7. **`run_full_horizon.py` never writes `run_config.json`**, so **FC-7 fails on every T1-F
   leg by construction** (§6.5) and no bundle this runner produces can be promoted on
   provenance. Deliberately not fixed here — authoring the artifact after seeing the score is
   the move rubric §4 forbids. It is an instrument fix for a successor.
8. **FC-2 row4 is SKIPPED on every leg** — the backstop channel is armed but the trajectory
   carries no `reserve_backstop` split (needs `builds_thermal_backstop_mw` / `builds_by_source`
   from `run_full_horizon`). So the BLK-10 backstop-sizing evidence D-2 was supposed to
   re-open **cannot be scored at all** from these bundles.

---

## 9. What this session does NOT claim

**Measured and reported:** the T1-F half — NEISO, NYISO, ERCOT, CAISO at the shipped posture,
plus an ERCOT pre-decision control (§6.3/§6.4). PJM and MISO were still solving at write-up.

**NOT measured, and therefore not claimed:**

* **No T1-H re-scores.** The four curve legs D-1 re-opens were not re-solved, so **every
  FC-3 verdict in `ff-t1-gate-2026-07.md` §4.1 remains a pre-epoch citation** and none is
  refreshed here. The T1-H half also carries the unsigned C.4(c) confound (§6.2).
* **No T1-X fold, no FC-6 driver battery, no FF-3E readiness re-run.**
* **No per-ISO §2.1b gate scorecard, and no regression table against FF-2D.** Producing
  either needs `forecast_verdict` scoring over the full battery, which needs PJM/MISO and the
  T1-H legs.
* **No board regeneration and no registration** — `ff-verdicts.json`, `program-status.json`,
  the FF-3E scorecard and `frontend/data/forecast/` are all untouched (§6.5). The backcast
  registry was never touched.
* **No mechanism-matrix verdict change.** Only the two `def:` stamps were refreshed (§7.4);
  no cell was adjudicated, because the T1-F legs are one lane of a battery that did not
  complete.
* **No promotion recommendation.** §6.4 is a measured finding routed to the owner; the
  promotion and gate-open calls remain the owner's.
* **Cross-ISO causation is NOT claimed.** Only ERCOT is attributed against a control.
