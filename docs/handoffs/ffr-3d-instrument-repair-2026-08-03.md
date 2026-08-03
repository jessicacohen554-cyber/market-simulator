# FFR-3D — the three signed instrument decisions, executed; the T1-F/T1-H instruments, repaired

**Session.** FFR-3D of the Forecast Finalization Program
(`docs/forecast-development-plan-2026-07.md`). Executes the three owner decisions signed
2026-08-03 in `docs/handoffs/ffr-owner-sitting-2026-08-02.md` **Addendum D.1**, and repairs the
measurement instruments FFR-3A left as blockers. **NO LP SOLVES.** Ran fully parallel with
FFR-3C, which owns the solve slots; `retirement_rule` and both entry dampers were left untouched
so FFR-3C's attribution runs on stable defaults.

**Base.** Branched off `origin/main` at `5057614` (the prompt named `195ff18`; the manager branch
carrying Addendum D had merged in the interim as PR #3352, so `5057614` is the same content plus
that merge). Keepers, markers and the holdout freeze unchanged and untouched.

---

## 1. Headline

| # | Item | Outcome | Commit |
|---|---|---|---|
| 1 | **C.4(c)** — un-pin the harness to production | **EXECUTED** | `36ef1a1` (+ `52435ad` sha stamp) |
| 2 | **C.4(a) B1** — one reader for the shipped capacity posture | **EXECUTED**; NYISO now resolves curve-OFF | `83efe6c` |
| 3 | **D-3a** — net-CONE forward mode → `reindex_gross` | **EXECUTED**; byte-identity **failed as shipped**, repaired, then **CONFIRMED exactly** | `e6f0cdb` |
| 4 | Blocker 4 — optional-field cache-key hazard | **REPAIRED, structurally** (guard, not a registration) | `0233913` |
| 5 | Blocker 5 — dishonest console line | **REPAIRED** | `34c2f25` |
| 6 | Blocker 7 — FC-7 fails on every T1-F leg | **REPAIRED** | `34c2f25` |
| 7 | Blocker 8 — FC-2 row 4 SKIPPED everywhere | **REPAIRED** — BLK-10 is now scorable | `34c2f25` |
| 8 | Blocker 1 — undocumented `data/clean` prerequisite | **DOCUMENTED** | `34c2f25` |
| 9 | Blocker 6 — pre-existing test failures | **TRIAGED** (§6); not fixed, as scoped |

**The one thing to read if you read nothing else:** the D-3a byte-identity claim in the signed
packet was **false as the code shipped** — `reindex_gross` was not byte-identical to `hold_last`
at 0.0. It is now, by construction. The decision stands; the code was brought up to the premise
it was signed on. §4 has the numbers.

---

## 2. C.4(c) — UN-PIN, MATCH PRODUCTION (`36ef1a1`)

**Signature.** *"`correlated_forced_outage` and `entry_lookahead_reprice` stop being forced
`False` against production `True`."*

`run_capacity_hindcast.build_config` passed harness-local `False` literals for both, so every
hindcast leg validated a posture the forecast does not ship — audit FR-14, which FFR-2E fixed for
the capacity posture and flagged for these two in its §6.2. Both now join the `None`-sentinel dict
the D-1/D-2 arms already use: **omit ⇒ inherit the shipped `ScenarioConfig` default**; `--no-*`
forces the control arm. The flags became `BooleanOptionalAction`, matching the damper flags.

Two things fixed alongside, because the un-pin would otherwise have created new defects:

- **The run meta was sourced from `args`.** With a tri-state flag, `bool(None)` stamps `false` on
  a leg that ran the shipped `true` — the FFR-1D "flag that armed nothing" defect inverted. Both
  keys now read the **solved config**, matching how the FF-2A dampers are already recorded.
- **The `--forward-from-base` refusal** now tests `args.entry_lookahead_reprice is True` — an
  *explicit* ask. The runner's `is_crossover_forward_year` branch already falls to the
  growth-scaled fallback instead of reading measured next-year demand in a full-forward leg
  (verified in `runner.py`), so inheriting the shipped `True` introduces **no measured read**
  (rule 22). Testing the resolved value would have refused every T1-FF leg.

Verified without a solve: `build_config("PJM", …)` now resolves `correlated_forced_outage=True`,
`entry_lookahead_reprice=True` — identical to `ScenarioConfig()` — and `--no-*` still yields
`False`.

### 2.1 The acknowledged cost — committed T1-H verdicts are LEGACY EVIDENCE

Addendum **D.3** priced this at signature: *"Those verdicts become legacy evidence scored on a
superseded posture — they are not silently reinterpreted and not deleted. Any FC-3 citation
resting on them says so."*

**Marked, not applied.** `docs/handoffs/ff-t1-gate-2026-07.md` §4.1 — the table that carries the
FC-3 citations — now opens with a marker naming commit `36ef1a1`, stating that every bundle in it
(including the corrected `nyiso-2021-2025-fixed` row) was solved with both mechanisms OFF. The
verdicts stand exactly as scored. **Nothing was re-scored, re-interpreted or deleted**, and no
re-score is implied — re-scoring needs solves this lane did not run.

Note this is the **second, independent** invalidation on those same rows: the §4.1 "STILL OPEN"
block already records them as **pre-cache-epoch**. A replacement leg must clear both — post-epoch
**and** shipped-posture.

**Not in scope, flagged for whoever owns it:** `scripts/register_forecast_baseline.py:115-116`
hardcodes `"datacenter_load_path": "mid"` and `"correlated_forced_outage": True` into the run
*meta*. Those are mirrored literals of shipped defaults in a run record — the same class of
divergence, one layer out. It is a board-registration path (out of this lane's remit) and the
literals happen to be correct today, so it was left alone. With blocker 7 landed, the resolved
config is now available in the run's own `run_config.json` and this can be sourced rather than
mirrored.

---

## 3. C.4(a) B1 — SINGLE SOURCE OF TRUTH (`83efe6c`)

**Signature.** *"Every runner reads the shipped `ScenarioConfig` capacity-price posture field
directly; the parallel `GOLDEN_CMC_BY_ISO` constant stops being a second answer. NYISO must
resolve curve-OFF, matching production."*

Three surfaces answered "what posture does production ship?" independently:

| Surface | Before | After |
|---|---|---|
| `run_capacity_hindcast.production_capacity_clearing_default` | read the live dataclass field (FFR-2E — the correct pattern) | thin alias over the one reader |
| `ff_readiness_battery.GOLDEN_CMC_BY_ISO` | hand-maintained parallel dict | **DELETED** |
| `run_full_horizon.reference_config` (`:153`, the live instance) | imported that dict | reads the one reader |

The two answers had **already diverged on NYISO**: the shipped field deliberately omits it
("excluded pending re-calibration" ⇒ gate OFF) while the constant carried `NYISO: True`. So every
`--golden-posture` T1-F leg solved NYISO **curve-ON against a production path that runs it
curve-OFF** — audit FR-14 in the T1-F lane, exactly the divergence FFR-2E measured in the
hindcast lane.

`scripts/lib/forecast_posture.py` is now the one reader. It **extends the FFR-2E pattern** rather
than inventing another, as the prompt required. The constant is **deleted, not corrected** (rule
26 `[R-DELETE]`: a second answer that still parses is a re-armable second answer).

**Effect:** NYISO's `--golden-posture` gate resolves curve-OFF, per the signature. Every other
ISO is unchanged, and passing the shipped mapping explicitly is value-identical to inheriting it,
so **no cache key moves**.

**The battery's own posture check was green on the divergence** — it compared the constant
against itself. It now asserts parity with the shipped field, with NYISO and ERCOT pinned OFF by
hand so a silent re-add is a visible test change.

---

## 4. D-3a — `reindex_gross` (`e6f0cdb`), and the byte-identity assertion

**Signature.** *"(a) `reindex_gross` … **Byte-identical to `hold_last` at the signed 0.0 real
rate**, so it changes no output until a non-zero rate is ever set."*

### 4.1 The rate is 0.0 — confirmed

`NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO` ships `0.0` for **all five** ISOs that carry a rate
(PJM, NYISO, NEISO, MISO, CAISO). Asserted, not assumed.

### 4.2 The byte-identity FAILED as shipped

Asserting it rather than assuming it is what the prompt asked for, and the assertion **failed**:

```
reindex_gross vs hold_last at the signed 0.0 rate:
  233 EXACT mismatches over 4 ISOs x 25 years x 7 offsets
  first: PJM 2029 eas=12.5  hold=118.87685  gross=118.87684999999999  delta=-1.42e-14
```

`(base + eas) * (1+0)**n − eas` cancels in real arithmetic but **not in IEEE 754**. The
docstring promised the identity; the arithmetic did not deliver it. The pre-existing test used
`assertAlmostEqual(places=12)` at **one** year and **one** offset, which is exactly what hid it.

A second, related defect: `reindex_gross` **raised `ValueError`** when `eas_offset_per_kw_yr` was
`None` — and no caller supplies one (FF-2C owns the wiring). Flipping the default without
touching this would have armed a raise for the moment that seam is wired.

### 4.3 Repaired first, flipped second — and then CONFIRMED

`forward_net_cone_anchor` now short-circuits at `r == 0`: `(1+0)**n` is exactly `1`, so both
reindex modes are `base`, and returning it directly removes round-off from a cancellation.
**No mathematics changes** — this implements the identity the docstring already promised. It also
drops the offset requirement at `r == 0`, where the offset provably cancels; a non-zero rate
still demands it.

```
D-3a BYTE-IDENTITY at the signed 0.0 rate: 0 exact mismatches
over 4 ISOs x 31 years x 8 offsets x 2 modes (1,984 comparisons)
```

**CONFIRMED — exact (`assertEqual`), not almost-equal.** The test now sweeps the whole horizon
and includes `eas=None`. Independently, the field has **no live consumer** (the anchor function is
not wired into `capacity_price_per_firm_mw_yr`), so the flip moves no solve output on either
ground.

### 4.4 A SECOND hazard the flip exposed — caught here, not in a later session

`__post_init__` coerced backcasts to the **literal** `"hold_last"`. That literal *was* the
default, and the field is cache-key-optional — which is neutral **at the default only**. The
moment it stopped being the default it entered the hash:

| Key | Pre-flip | Naive flip | After repair |
|---|---|---|---|
| default **backcast** | `35b6dc12f97968f1` | **`512c2fffbb61414e`** | `35b6dc12f97968f1` ✅ |
| ERCOT 2023 backcast | `df386bca96a1d288` | **`f3ee0af68fa72303`** | `df386bca96a1d288` ✅ |
| default forecast | `603c2498bf71d21d` | `603c2498bf71d21d` | `603c2498bf71d21d` ✅ |

That would have **orphaned every backcast keeper's on-disk cache**, with **no test red** — the
pinned key is explicitly a `mode="forecast"` object that takes no backcast coercion, so nothing
was watching. The coercion now targets the **dataclass default**, neutral by construction and
immune to the next flip. Two new guards close the hole: `PINNED_BACKCAST_CACHE_KEY`, and the
general property that **no registered optional field may be backcast-coerced off its default**.

### 4.5 Cache classification

Declared in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` — **the blocker-4 guard caught this flip and
refused it until it was declared**, which is the channel working on its first real use.
Classified **BYTE-IDENTICAL**, so **no cache-epoch entry is owed**: the field has no live consumer
*and* the mode is exactly `hold_last` at 0.0, so the same-key collision is between two runs with
identical output. An explicit `hold_last` is now non-default and hashes distinctly, so the
status-quo control arm stays separable.

**Parity-registry consequence.** The flip made every keeper's *committed* `run_config.json` read
as "armed" (they record the pre-flip coerced `hold_last`), failing `check_forecast_parity` in all
six ISOs at once. Declared `SCENARIO_INPUT` — a forecast-only axis a backcast never chooses —
with an explicit **re-check trigger for when FF-2C wires the seam** and it becomes a real
forecast mechanism.

---

## 5. Blocker repairs

### 5.1 Blocker 4 — the cache-key hazard, handled structurally (`0233913`)

FFR-3A: *"will silently recur on the next default flip; structural, needs a decision not a
patch."* D-3a **is** that next flip, so it was live rather than hypothetical.

**The hazard.** `cache_key()` drops a `_CACHE_KEY_OPTIONAL_FIELDS` member when it equals
`getattr(ScenarioConfig(), name)` — the **LIVE** default, recomputed on every call. Move that
default and a new-default run hashes **identically** to the old-default run it supersedes: a
silent same-key collision in which the flipped config re-uses the pre-flip bundle. It has already
happened — the D-1/D-2 flips left `cache_key(ScenarioConfig())` at `603c2498bf71d21d` across a
behavioral change, against a signed packet that asserted the opposite.

**The repair is a guard, not a registration**, per the prompt. `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`
records the default each registered field is registered at (as source text, `ast.unparse`d, so
reformatting is invisible and any default form is expressible), and
`check_cache_key_registration.py` grows **check 3**: every registered field's live default must
match its declaration, and registry and ledger must cover each other. **Check 3 takes no
`--base`** — a HEAD-only invariant, so unlike the new-field check it fires on every CI run and
every local run. That is precisely the §0c-4 gap FFR-3A named: a lane cannot rely on a later
session noticing.

A flip therefore cannot land silently. The guard stops it until **declared**, and the declaring
commit is where the operator must classify the collision — byte-identical (say so) or behavioral
(cache-epoch entry + purge). The failure message states both branches inline and states that
deregistering the field is **not** the fix. Verified twice: on a simulated flip, and on the real
D-3a flip, which it refused until declared.

**Deliberately NOT changed: `cache_key()` semantics.** Freezing the comparison against the
declared values rather than the live default is the deeper fix — it would make a flip re-key
correctly instead of colliding. But it re-keys every config whose default has already moved (at
minimum `retirement_rule`, `entry_rate_limits`, `entry_commissioning_lag`), a cache-invalidating
change that needs solves to validate. **Open follow-up; needs a solve.**

### 5.2 Blocker 7 — FC-7 (`34c2f25`)

`run_full_horizon.py` wrote `config.yaml` but never `run_config.json`, the artifact FC-7 row 1
requires, so **no bundle it produced could pass provenance** — for reasons having nothing to do
with the run. (FF-2D worked around it with a scoring-time helper,
`scripts/_ff2d_emit_run_config.py`, which keeps the producer broken and puts artifact authorship
next to the score.)

**Written from the run's ACTUAL resolved config**, never from a target: the payload's
`scenario_config` is the cache directory's `config.yaml` read **verbatim** — the dump
`results.cache.save_result` wrote from the config the solve actually ran. That is deliberately
**not** the object handed to `solve_and_summarize`: `runner.run_scenario_iso` re-binds the ISO,
applies `resolve_policy_bundle`, and may apply per-ISO overrides, so the pre-solve object is a
**request** and the on-disk dump is the **resolution**. Recording the request would be the exact
rule-24 divergence FC-7 exists to detect. Nothing is reconstructed, normalized or defaulted, and
`scenario_config_source` names the file so a reader can re-verify rather than trust.

**When there is no resolved dump, nothing is written.** A zero-year run has no provenance, and
FC-7 FAILing on it is the truthful verdict; fabricating a config from the request would
manufacture a pass.

**Why the timing makes this admissible.** Rubric §4 forbids authoring an artifact to move a
score. FFR-3A deliberately did not author it *after seeing the score*. This lands **before** the
next battery, is written from the resolved config, and **no value in it was chosen to clear a
band** — the artifact either exists because the run produced one, or does not exist and FC-7
FAILs. Fixing a producer that fails by construction is instrument repair; choosing a value to
clear a band would not have been, and no such choice arose.

### 5.3 Blocker 8 — FC-2 row 4, so BLK-10 becomes scorable (`34c2f25`)

The evolution ledger has **always** tagged every `thermal_additions` row with its `source`
(`planned` | `economic` | `reserve_backstop`), but `extract_trajectory` summed them into one
`builds_thermal_mw`, so the split never reached an artifact. FC-2 row 4 reads exactly
`builds_thermal_backstop_mw` / `builds_by_source["reserve_backstop"]`, so with the channel armed
it **SKIPped on every run** with its own actionable message. **BLK-10 backstop sizing — the
evidence D-2 was meant to re-open — could not be scored at all.**

Both keys are now emitted: the scalar the scorer keys on, plus the full channel map so the share
is auditable rather than asserted. An untagged legacy row surfaces as `"unattributed"`, never
folded into a real channel. Asserted end-to-end against the real scorer: **without the split →
`SKIPPED`; with it → scores** (`backstop_share` computed from either key).

### 5.4 Blocker 5 — the console line (`34c2f25`)

An empty `invariants` list means the gate was **not evaluated**, but the counts of an empty list
are 0 and 0 — so a zero-year run printed `invariants: 0 FAIL, 0 WARN`, a hard failure rendered as
a clean gate. The JSON summary was always honest; only the console lied, which is the surface an
operator reads first. It now prints `NOT SCORED — <why>. The gate was not evaluated.`, and
reports whether `run_config.json` was written.

### 5.5 Blocker 1 — the `data/clean` prerequisite (`34c2f25`)

`data/clean` is a **hard** prerequisite for every forecast leg — the confirmed-exits loader
*refuses* rather than degrading — and is gitignored, so a fresh container has none of it.
Measured at **≈55 min / 50 datatypes / ≈1.6 GB**, and absent from every wall-clock anchor.
Documented in **`forecast-development-plan-2026-07.md` §2.4, directly above the budget table** a
dispatching session reads before budgeting, and in `run_full_horizon.py`'s own module docstring.
The note flags the partial-tree trap: "the directory exists" is not the check.

---

## 6. Blocker 6 — triage of the pre-existing test failures

**Scope: triage only.** Nothing here was fixed; that is scope this lane cannot bound.

**Measured at this HEAD: 19 failures** (FFR-3A reported 24 = 20 + 4; the delta is not
reconciled — some may have been fixed since, or counted per-file). Fast tier: 3. Slow /
integration / fulldata tiers: 16. All 19 were confirmed against `origin/main`, not caused by this
lane's changes.

| # | Test(s) | Lane | Route |
|---|---|---|---|
| 6 | `tests/regression/test_soundness.py::TestEndToEnd::*` | **DATA** | `RuntimeError: confirmed-retirements: clean partition for {ERCOT,CAISO} is absent`. Build `data/clean` (blocker 1). Not a code defect. |
| 4 | `tests/unit/results/test_export.py::TestExportScenarioJson::*` | **DATA** | Same `RuntimeError`. |
| 4 | `tests/scoring/test_ff_readiness_battery.py` (`integration`) | **DATA** | `ERCOT:confirmed_retirements [MISSING] clean partition unbuilt (data/clean is gitignored)`. |
| 1 | `tests/curation/test_consume_phase3d.py::EgridZoneAssignmentParity` | **DATA** | Clean-vs-raw parity test; needs the built tree by construction. |
| 1 | `tests/regression/test_fleet_arrays_golden.py` (`fulldata`, `golden`) | **DATA (probable, UNCONFIRMED)** | "FleetArrays drift vs the pre-split golden; fields differing: `['availability', 'min_gen']`". Both derive from outage inputs, and this container's `data/clean` has only 4 partitions — but distinguishing data-lane from genuine golden drift **requires a provisioned `data/clean`**, which this lane did not build. Do not close it as data-lane without that check. |
| 2 | `tests/iso/ercot/test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion::*` | **REAL — D-1 fallout** | `ValueError: retirement_rule='pipeline' requires a simulation year`. The tests call the screen with `year=None`, legal under `legacy` and a hard error under the signed D-1 default. A test not updated for the flip. → **retirement lane** (FFR-3C owns `retirement_rule`; untouched here by instruction). Small and well-bounded. |
| 1 | `tests/unit/data/test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` | **REAL — stale expectation** | Asserts `nuclear_unit_availability_series("NEISO", 2024) == {}`; NEISO now returns 3 units. The expectation predates NEISO nuclear data landing. → **nuclear-registry lane** (FFR-SB). |

**Summary: 15 data-lane confirmed, 1 data-lane probable-unconfirmed, 3 real.** None is a
governance-lane failure. The single largest fix available is **building `data/clean`** — which is
blocker 1, and is why the two were routed together.

---

## 7. What still needs a solve

| Item | Why |
|---|---|
| **Re-scoring the T1-H verdicts** on the un-pinned posture | Needs four curve legs re-solved. §2.1's marker records the supersession; it does not repair it. |
| **`cache_key()` semantics** — comparing against declared defaults instead of the live default | The deeper blocker-4 fix. Re-keys every config whose default has already moved; cache-invalidating, needs measurement. §5.1. |
| **Confirming FC-2 row 4's verdict** | The split now *emits*, asserted against the real scorer on synthetic trajectories. A **real** BLK-10 number needs a T1-F leg. |
| **Confirming FC-7 passes on a real bundle** | Asserted against `score_fc7` on a synthetic resolved config; a real leg confirms end to end. |
| **`test_fleet_arrays_golden`** | Data-lane vs real golden drift is undecidable without a provisioned `data/clean`. |

## 8. Verification run in this session (no LP)

- Targeted suites green: **1,369 passed, 3 skipped** (`tests/scoring/`, `tests/unit/config/`,
  `test_net_cone_forward`, `test_persisted_identity`).
- Fast tier: only the 3 pre-existing failures triaged in §6 (the 2 parity failures D-3a
  transiently introduced were resolved by the registry declaration in §4.5).
- `ruff check` / `ruff format --check` clean across `scripts/`, `src/`, `tests/`.
- `check_cache_key_registration.py` → ok (117 registered, 117 declared, all match).
- `check_mechanism_matrix.py` → integrity OK; keeper stamps match. **No cell verdict changed** —
  no mechanism was tested here (rule 28); the `net_cone_forward_vintages` row's `def` text was
  restamped for the new default, header/def hygiene only.
- Cache keys: forecast default `603c2498bf71d21d` and every backcast key **unchanged**.
