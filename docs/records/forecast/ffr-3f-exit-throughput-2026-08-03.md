# FFR-3F — The G-31 exit-throughput fix lane: cap grain first, then the measured throughput term

**Session.** FFR Wave 3, the G-31 fix lane, chartered by **owner decision D-8**
(`docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum F.1, signed 2026-08-03) to
FFR-3C §6's specification. Branch `claude/g31-exit-throughput-fix-gsy4md`, off `origin/main`
**`edf5c5a`** (the packet's stated HEAD `01b6a6a` was already stale at session start; `98ad9c1`
at first fetch, `edf5c5a` by the time the first commit was pushed).

**Nothing is promoted and no default is flipped.** Both are owner boxes. `exit_rate_limits`
ships **default-OFF**; D-1 and D-2 stay armed exactly as Addendum D left them; no band was
widened and no threshold moved.

---

## 0. Headline

1. **The G3 cap-grain defect is fixed and landed** (commit `2adfb49`). The pipeline's admission
   cap now resolves its adequacy requirement at the schedule's **execution horizon** rather than
   the decision year. No new parameter. Verified to change the admitted exit set in a
   discriminating unit test (the old grain admits 1 unit where the corrected grain retains 2).
2. **The exit-throughput term is built, measured, registered and default-off** (commit
   `db5ff91`). Identification is external — the EIA-860 retired sheet — and reproduces the
   values D-8 cites for the two test ISOs exactly (ERCOT 4.42 GW/yr, PJM 5.24). The synthetic
   demonstration is decisive: FFR-3C's 12-unit cohort exits in **one** year uncapped and over
   **three** capped, with the **total identical** — the cap moves the calendar and does not
   touch the level.
3. **The ERCOT measurement is a NULL, not a pass, and the pairing is what proves it.** All three
   ERCOT arms — pre-fix control, cap-fix control, throughput-armed — are identical to the
   megawatt across all three years, identical on dispatch skill, with **zero `pipeline_events` in
   any year**. No ERCOT unit fails the going-forward bar in the T1-FF window, so neither
   mechanism has any work to do there.
4. **The FH-1 §3.3 re-probe reads I6 PASS / I7 PASS / I12 WARN** against the recorded FAIL /
   FAIL / WARN — but the pre-fix control returns the identical PASS/PASS/WARN, so **the flip is
   measured NOT to be this lane's**, and I12's WARN has *inverted* (the margin is now too high,
   40.2 % against a 28.7 % ceiling, where FH-1's was too low). **FH-4/FH-5 is NOT declared
   unblocked.** §6.
5. **PJM is where the cap-grain fix actually bites, and it bites hard.** Against a pre-fix
   control at the identical peak and reserve margin, the corrected grain cuts exits admitted to
   the retirement pipeline from **14.766 GW to 1.056 GW — a 93 % reduction (−13.71 GW)** in PJM's
   2024 screen. The fix is not inert; ERCOT simply had no candidates for it to act on. §5.3–§5.4.

---

## 1. Task 1 — the G3 cap-grain fix

### 1.1 What was wrong

FFR-3C §1.2 G3: the R-NEW pipeline's admission cap screens **one counterfactual fleet** — the
current fleet with the whole scheduled exit set removed at once — but resolved the adequacy
requirement that fleet is tested against at the **decision** year, while the exits it admits
execute at `decided_year + L_f`, one to three years later. In FFR-3C's synthetic the cap tested
a 2026 requirement of 21,990 MW against exits landing on 2028's 24,244 MW: **+10.3 % of
requirement the cap never saw.**

### 1.2 The fix

`_admission_cap_horizon` (`src/market_sim/model/capacity_evolution/retirements.py`) returns the
year at which the counterfactual fleet actually exists — `max(decided_year + L_f)` over the
scheduled set — and the peak projected to it. **Both** year-dependent inputs to
`resolve_adequacy_requirement_mw` move there, because both matter:

* the **year**, which selects the ISO's published-FPR delivery year; and
* the **peak** the requirement is a fraction of, compounded on the run's own demand-growth path
  (`resolve_demand_growth_rate` — the identical per-year rate `runner._scale_demand` uses).

No new `ScenarioConfig` field and no identification work: the horizon is a function of the
already-identified per-fuel execution lags and the growth path already driving demand, so it
regenerates for any forward year and responds to changed conditions (rule 13 `[R-MEASURED]`).

**Inert where the grain was already right**, byte-identically: a lag-1 fuel executes in the
screen year itself, and an empty schedule has nothing to project — both return
`(year, peak_demand)` unchanged. The realized-year execution floor is untouched; it was always
evaluated at the year its exits land.

### 1.3 Verification

| check | result |
|---|---|
| Horizon reproduces FFR-3C's synthetic | coal cohort decided at the 2031 screen (loss year 2030) + `L_coal` 3 → cap tested at **2033**, peak × 1.025² — the same 2-year offset G3 measured |
| Discriminating behavioural test | ERCOT, peak 3,095.5 MW: decision-year requirement 3,316.91 MW ⇒ **1** unit retained; execution-year requirement 3,484.82 MW ⇒ **2**. Reverting the call to the decision-year grain **fails the test (1 != 2)**, verified by patching it out and re-running |
| Inert cases | lag-1 fuel and empty schedule both `(year, peak_demand)` |
| Existing pipeline suite | 209 pre-existing tests still pass; the one existing test that exercises the admission cap is grain-invariant by construction (retaining gas_st alone clears both requirements) and its stale arithmetic comment was corrected rather than left to mislead |

### 1.4 What the fix does NOT do

The **fleet** side of the cap stays at the decision year — entry commissioning between decision
and execution is not credited. That is the cap's pre-existing grain, out of this correction's
scope, and it biases the cap conservative (toward retaining). Recorded as open, not silently
closed.

---

## 2. Task 2 — the exit-throughput term

### 2.1 The rule-19 seam, stated explicitly

D-8 ruled queue **latency** and queue **throughput** two mechanisms. The seam:

| | owns | operator |
|---|---|---|
| `retirement_execution_lag_*` (latency, **unchanged**) | **WHEN** a decided unit becomes eligible to leave | rigid per-fuel time shift, `decided_year + L_f` |
| `exit_rate_limits` (throughput, **new**) | **HOW MANY MW** may actually leave in one year | FIFO budget over the year's due set |

They cannot double-count because they act on **different quantities in sequence**: the lag sets
*membership* of the year's DUE set; the cap sets *how much of that due set is processed*. A unit
the cap defers **stays pipelined** and re-presents at the head of next year's queue through the
identical "execution deferred, re-latched next year" path the reliability floor already uses
(pipeline component 5) — so no second deferral mechanism is introduced either.

`staged_oversupply_thinning` stays **deleted** (rule 26 `[R-DELETE]`). This is a new, externally
identified, default-off gate, not a revival of the fitted knob.

### 2.2 Identification — every value cited to EIA-860

Reader: `src/market_sim/data/build_exit_throughput.py` (`max_annual_exit_gw`), the mirror of
`build_throughput.py` — same fuel classes, same `_map_fuel_type` crosswalk, same BA→ISO map, so
the two halves of one queue are measured on one basis. Source: EIA-860
`eia860_generator_retired_and_canceled`, `Status == "RE"` (excluding `CN` cancelled and `IP`
indefinitely-postponed, neither of which is a deactivation).

**Measured maximum single-year thermal deactivation, 11-year window:**

| ISO | seed through 2023 (GW) | max year | seed through 2025 (GW) | cap at 2.0× through 2023 (MW/yr) | D-8's cited value |
|---|--:|--:|--:|--:|--:|
| **MISO** | 7.46 | 2016 | 7.46 | 14,920 | 7.57 |
| **PJM** | **5.24** | 2015 | 5.24 | **10,485** | **5.24** ✓ |
| **ERCOT** | **4.42** | 2018 | 4.42 | **8,840** | **4.42** ✓ |
| CAISO | 2.39 | — | 1.48 | 4,774 | 1.48 |
| NEISO | 0.98 | — | 0.45 | 1,950 | 0.45 |
| NYISO | 0.31 | 2021 | 0.31 | 625 | 0.31 |

**Both test ISOs reproduce D-8's cited identification exactly.** MISO differs by 1.5 %
(7.46 vs 7.57) and CAISO/NEISO differ on the pre-2015 window — FFR-3C's reader was session
scratch and is not committed, so its exact construction cannot be diffed. The shipped
construction is the defensible one because it is the entry side's, verbatim; the deltas are
recorded rather than reconciled to an unavailable script, and **neither affects a tested ISO**.

**The windowing choice carries no DOF for the tested ISOs — measured, not assumed.** ERCOT, PJM
and MISO return the identical maximum under the 11-year window, the entry side's 10-year window,
and the **unwindowed** full EIA-860 retired record back to 1978, at both the 2023 and 2025
vintages. Only CAISO/NEISO/NYISO are window-sensitive, and none is a test ISO here.

**The 2.0 multiplier is not a chosen number.** It is the entry side's own
`ENTRY_GROWTH_LIMIT_MULTIPLE` (the ReEDS growth-constraint hard bound, "not allowed to exceed
200 % of the prior maximum"), transferred unchanged. FFR-3C §1.4's finding *is* the asymmetry —
exit uncapped while entry is capped at 2× its measured record — so holding one queue to **one**
envelope is the structurally faithful repair (rule 1 `[R-STRUCT]`), and it leaves no exit-side
multiplier to fit. There is no residual channel into any of this (rule 23
`[R-FROZEN-DERIVE]`): nothing in the reader can see a model result, a price, or a score.

### 2.3 The window, the driver, the forward story (rule 17 `[R-FLOOR-WINDOW]` analogue)

* **Driver.** RTO/ISO deactivation-queue processing capacity — deactivation studies, RMR
  determinations, decommissioning logistics — externally identified by the largest single-year
  deactivation each ISO has actually achieved.
* **When it may bind.** Only in a year whose decided-and-due exit volume exceeds **2× the ISO's
  historical single-year record**. Over the historical window it is inert by construction: the
  seed *is* that record.
* **Forward regeneration.** Re-derives from the EIA-860 retired sheet at the run's vintage; a
  future edition recording a larger deactivation year raises the cap automatically. An ISO with
  no measured deactivation carries **no cap** (rule 25 `[R-ISO-SCOPE]` neutral fallback — a
  missing measurement must never invent a zero that forbids exit).

### 2.4 A vintage-directory defect found and closed

The first armed leg ran **inert** and said so loudly: the committed `vintage_2023/` directory is
a **reduced 10-sheet set** and does not contain the retired sheet at all, so the seed resolved to
`None` and no cap was applied. The reader now falls back to the canonical release **with a
WARNING**, which is as-of-safe *here and only here* because the window bound is on **retirement
year**, not publication vintage: `through_year` already excludes every deactivation after the
cutoff, so the canonical sheet contributes no post-vintage event.

The residual exposure is reporting **completeness** at the boundary year, and it is measured to
be immaterial for every ISO this cap is armed on — the binding maximum predates the 2023 boundary
by 5–8 years in every case (ERCOT 2018, PJM 2015, MISO 2016), so no boundary-year revision can
move the seed:

| ISO | annual thermal deactivation (GW), 2013→2023 | max |
|---|---|--:|
| ERCOT | 1.44 · 0.63 · 0.15 · 0.67 · 0.98 · **4.42** · 0.38 · 0.32 · 0.03 · 0.41 · 1.01 | 2018 |
| PJM | 1.01 · 2.40 · **5.24** · 0.32 · 0.48 · 1.32 · 1.95 · 1.92 · 1.07 · 2.95 · 5.05 | 2015 |
| MISO | 2.74 · 0.29 · 2.31 · **7.46** · 1.52 · 5.44 · 3.54 · 2.15 · 3.67 · 3.08 · 3.63 | 2016 |

The runner's log line for an unresolved seed was also corrected: it said "no measured thermal
deactivation" when the real cause was a missing sheet, and now names both possibilities and
states plainly that **the arm is inert this run**.

### 2.5 Mechanics

Strict **FIFO by decided year** — a deactivation queue is processed oldest-request-first. The
year stops at the first request that does not fit, and remaining headroom is **not** backfilled
with a smaller later unit: reordering by size is not something a real queue does, and it would
make exit composition depend on unit size rather than request date. The head of the queue is
**always** admitted even when it alone exceeds the cap, otherwise the cap would silently become
an immortality rule for large units rather than a rate limit.

Deferrals are recorded as their own ledger event kind (`throughput_deferred`), never folded into
`floor_retained`, so D-2 mechanism attribution stays readable.

### 2.6 Registration (rules 5 / 24 / 28)

| duty | done |
|---|---|
| `ScenarioConfig.exit_rate_limits`, default-off | ✓ |
| Cache-key registered; default key **`973a0acdef818e91` verified UNMOVED** before/after | ✓ |
| `docs/parameter-citations.md` + `frontend/data/parameters.json` cited entry (not `needs-citation`) | ✓ |
| Constants in their own per-domain module `config/retirement_config.py` with citations | ✓ |
| CLI arm `--exit-rate-limits` / `--no-exit-rate-limits`, recorded in `meta` **from the config object the solve ran on** | ✓ |
| Rule-28 matrix row in the **same PR** (duty c) | ✓ |
| No env knob, no per-ISO hardcoded dict, no `getattr` fallback literal | ✓ |

The stale rule-19 comment in `scenarios.py` that asserted the argument D-8 overturned was
amended in place rather than left to mislead the next reader.

---

## 3. Synthetic demonstration — the property that was missing

FFR-3C §1.2 G2: *"with only the latency term, exit-wave width is invariant at exactly one year
no matter how many units fail."* Driving the shipped screen over a 12 × 500 MW all-failing coal
cohort (6 GW, `L_coal` = 3), floor inert:

| year | uncapped (shipped) | capped at 2 GW/yr |
|---|--:|--:|
| 2028 | **12 units = 6.0 GW** | 4 units = 2.0 GW (8 deferred) |
| 2029 | — | 4 units = 2.0 GW (4 deferred) |
| 2030 | — | 4 units = 2.0 GW |
| **wave width** | **1 yr** | **3 yr** |
| **total exited** | **6.0 GW** | **6.0 GW** |

The total is identical. That invariant is the point: a throughput cap adjudicates the
**calendar**, never the **level** — the level remains the revenue lane's (BLK-6/BLK-9), exactly
as FFR-3C §1.4 scoped it.

---

## 4. Prerequisites and blockers found

1. **The container had NO project dependencies at all** — not merely `data/clean`. `python -c
   "import pandas"` failed; `regenerate_clean.py` reported **50/50 datatypes failed** with
   `ModuleNotFoundError: No module named 'pandas'` within seconds. `pip install -r
   requirements.txt --ignore-installed PyYAML` (the debian-owned PyYAML blocks a plain install)
   plus `pip install highspy==1.14.0` (the resolver silently takes 1.15.1 otherwise, and the
   HiGHS version moves LP results) is the recipe. **This belongs with FFR-3A blocker 1 and is
   strictly larger than it.**
2. **`tzdata` is still not in `pyproject.toml`** even though `requirements.txt`'s own comment
   claims *"pyproject pins it unconditionally"*. It does not. `pip install tzdata` is still
   required by hand (FFR-3C blocker 9). Not fixed here — out of lane — but the drift is between
   two committed files and is a one-line repair for whoever owns the dependency manifest.
3. **`data/clean` regeneration: 49/50 clean.** `egrid` exits `-6` (`terminate called without an
   active exception`) — but **after** writing all seven year files, so the partition is
   complete and the abort is an interpreter-teardown crash, not a data failure. Total ≈ 65 min,
   1.6 GB, 54 datatype directories.
4. **A broad pre-existing cache-key pin drift at HEAD.** `ScenarioConfig().cache_key()` is
   `973a0acdef818e91` while `PINNED_DEFAULT_CACHE_KEY` is `603c2498bf71d21d`. The test's own
   message says *"Do not update the literal to silence this — find what changed."* Not mine (my
   change leaves the key untouched, verified both directions) and not fixed here, but it means
   **every on-disk cache is already orphaned relative to the pins at this HEAD**, which any
   keeper-reproducibility claim needs to account for.
5. **Pre-existing test failures, itemized** (FFR-3C blocker 6, now enumerated). All verified to
   fail identically at `origin/main` with my branch stashed; **my changes introduce none**:
   `test_persisted_identity` (×3), `test_fh2_as_of_channels` cache-key neutrality,
   `test_fleet_arrays_golden`, `test_cc_committed_offer_margin` + `test_ramp_envelope_basis`
   byte-stable keys, `test_outages::test_unknown_iso_degrades_to_empty`,
   `test_ercot_thermal_as_endogenous::TestScreenMutualExclusion` (×2). Separately,
   `test_integration::test_full_year` fails **only under `-n 4`** and passes serially — it is a
   wall-clock performance assertion, not a correctness failure.
6. **413 on first push, both documented causes present.** A stale tracking ref
   (`origin/claude/g31-exit-throughput-fix-gsy4md`, pruned) *and* a stale `origin/main`. `git
   remote prune origin` + `git fetch origin main` + rebase reduced the push to 11 objects and it
   went through. No PR had ever existed for the branch (`search_pull_requests` → 0), so no
   merged-branch restart was needed.

---

## 5. Task 3 — paired measurement, ERCOT

All arms are **T1-FF full-forward hindcast, ERCOT, base 2023, vintage 2023, 2023–2025, Arm R,
3 solve years** — the FH-1 §3.3 gate posture exactly. Cache keys verified **distinct before any
arm was read**, and the paired configs verified to differ in **exactly one field**.

| arm | code | `exit_rate_limits` | cache key |
|---|---|---|---|
| **PRE-FIX control** | `origin/main` `edf5c5a` (no cap-grain fix) | absent | `418b7bc4ead77d09` |
| **cap-fix control** | this branch | off (shipped default) | `5de5e8b320b525eb` |
| **throughput armed** | this branch | **on**, cap 8,840 MW/yr | `2fe6094ebc317548` |

> **Pairing check.** The pre-fix arm runs in a `git worktree` at `edf5c5a` with
> `MARKET_SIM_DATA_ROOT` pointed at the main tree, so both arms read byte-identical data. Its
> cache key differs for a reason that is **not** a config difference: `MARKET_SIM_DATA_ROOT`
> pointing outside `REPO_ROOT` changes the key (the worktree at `edf5c5a` with `DATA_ROOT` unset
> returns `973a0acdef818e91`, identical to this branch's). A diff of the two logged config dicts
> shows **exactly one** differing entry — `exit_rate_limits` present vs absent — and that field
> is dropped from the hash at its default, verified by swapping `edf5c5a`'s `scenarios.py` into
> this tree and getting the identical default key. **That `DATA_ROOT`-outside-`REPO_ROOT` shifts
> the cache key is a latent hazard of the data-root seam and is reported as a new finding.**

### 5.1 The result: both mechanisms are PROVABLY INERT in ERCOT's T1-FF window

| year | thermal before | econ retired | I6 | reserve margin |
|---|--:|--:|--:|--:|
| 2023 | 78.171 GW | **0.000 GW** | 0.0 % | 26.84 % |
| 2024 | 78.171 GW | **0.000 GW** | 0.0 % | 32.26 % |
| 2025 | 78.527 GW | **0.000 GW** | 0.0 % | 40.19 % |

**The cap-fix control and the throughput-armed arm are identical to the megawatt in every year,
with ZERO throughput deferrals** — the cap resolved and logged correctly (8,840 MW/yr) and never
bound. The reason is stronger than "small": the ledgers carry **no `pipeline_events` at all** in
any year of either arm — not one `decided`, `entry_capped`, or `executed` row. **No ERCOT unit
fails the going-forward bar anywhere in the window, so the retirement pipeline is never
entered.** An admission cap that is never consulted with a non-empty candidate set, and a
throughput cap with nothing due, cannot do anything.

This is FFR-3C §3.2's structure — *"an ISO can be structurally incapable of exercising the
mechanism under test"* — now measured for **ERCOT**, the ISO that lane nominated *because* it was
the failing I6 case. **Per this lane's own charter, that is a NULL and must not be read as a
pass.** The pairing is what makes it legible: without the control arm, "0.000 GW, I6 PASS" would
look like the fix working.

There is also a mechanical reason no `pipeline` exit can land in this window at all: a unit
decided at the 2024 screen (loss year 2023) with `L_coal` = 3 executes in **2027**, and one
decided at the 2025 screen executes in 2028 — both outside a 2023–2025 window. Even if units had
failed the bar, the pipeline rule cannot produce an execution inside a 3-year T1-FF window.

### 5.2 Attribution: the cap-grain fix is INERT here, and the gate flip is NOT this lane's

The pre-fix control settles it. Against `origin/main` `edf5c5a` — the identical posture, the
identical data, the cap-grain fix absent:

| arm | 2023 | 2024 | 2025 | pipeline events | I6 | I7 | I12 |
|---|--:|--:|--:|---|---|---|---|
| **FH-1 recorded** (legacy rule, 2026-08-02) | 0.00 GW | 0.00 GW | **21.05 GW (26.8 %)** | n/a | **FAIL** | **FAIL** | WARN |
| **PRE-FIX control** (`edf5c5a`) | 0.000 | 0.000 | **0.000** | **NONE** | PASS | PASS | WARN |
| **cap-fix control** (this branch) | 0.000 | 0.000 | **0.000** | **NONE** | PASS | PASS | WARN |
| **throughput armed** (cap 8,840 MW/yr) | 0.000 | 0.000 | **0.000** | **NONE** | PASS | PASS | WARN |

All three of my arms are **identical to the megawatt**, including reserve margin to six decimal
places (0.2684 / 0.322638 / 0.401939). So:

* **The cap-grain fix changes nothing at this posture — measured against a control, not
  inferred.** It is correct by construction and pinned by a discriminating test, and it is inert
  here for a specific, checkable reason: the screen never produces a candidate, so the admission
  cap is never consulted.
* **The I6/I7 FAIL → PASS flip versus the recorded gate is NOT this lane's doing**, and I am not
  claiming it. It is already present in the pre-fix control, so it was produced by something that
  landed between FH-1's probe and `edf5c5a`. The overwhelmingly likely cause is **owner decision
  D-1's `legacy` → `pipeline` default flip, signed 2026-08-02 — after FH-1's gate ran.** FH-1's
  own §7 reading names the legacy machinery explicitly (*"once the two-consecutive-loss counters
  mature"*), and the pipeline rule cannot reproduce that behaviour. **I did not isolate D-1
  itself** (that would need a `--retirement-rule legacy` arm, which is FFR-2B's territory and not
  this charter's), so this is attribution by elimination plus mechanism, not a measured D-1 arm.

### 5.3 PJM — the ISO that DOES exercise the admission cap

Same posture (T1-FF, base 2023, vintage 2023, 2023–2025, Arm R), PJM's shipped curve-ON capacity
posture (the harness default).

| year | thermal before | econ retired | pipeline events | reserve margin |
|---|--:|--:|---|--:|
| 2023 | 168.540 GW | 0.000 GW | none | −1.29 % |
| 2024 | 168.540 GW | 0.000 GW | **9 decided (1.056 GW)**, **1,190 `entry_capped` (108.207 GW)** | −4.88 % |
| 2025 | 168.547 GW | 0.000 GW | 9 `reversed` (1.056 GW) | −9.28 % |

Invariants: **0 FAIL, 0 WARN — all 14 PASS**, including I12 in-band on the requirement-implied
floor `[−12.9 %, 2.1 %]`.

**This is the arm where the cap-grain fix actually operates.** 1,199 PJM units fail the
going-forward bar in the 2024 screen, and the admission cap admits **9 of them (1.056 GW)** while
un-admitting **1,190 (108.2 GW)**. The cap is the binding constraint on PJM's exit membership by
two orders of magnitude — which is precisely the quantity FFR-3C §1.2 G3 said was being evaluated
against the wrong year's requirement. (The 9 admitted units then *recover* and leave the pipeline
in 2025 through the soft latch, so PJM's realized economic exits are 0.000 GW as well.)

So the ERCOT null does **not** generalise: the cap-grain fix has a live, heavily-loaded seam in
PJM. What that seam does under the corrected grain versus the old one is the pre-fix pair below.

### 5.4 PJM pre-fix pair — the cap-grain fix cuts admitted exits by 93 %

The decisive measurement of this lane. Same posture, same data, PJM's shipped posture; the arms
differ only in whether `_admission_cap_horizon` exists. **The 2024 screen is where the cap binds**
(the 2023 screen has no candidates, and by 2025 the survivors have recovered):

| PJM 2024 screen | PRE-FIX (`edf5c5a`, decision-year grain) | CAP-FIX (this branch, execution horizon) | delta |
|---|--:|--:|--:|
| units failing the bar | 1,199 | 1,199 | — |
| **admitted to the pipeline (`decided`)** | **83 units / 14.766 GW** | **9 units / 1.056 GW** | **−74 units / −13.710 GW (−93 %)** |
| un-admitted (`entry_capped`) | 1,116 / 94.496 GW | 1,190 / 108.207 GW | +74 / +13.710 GW |
| peak demand | 153,121 MW | 153,121 MW | identical |
| reserve margin | −4.8754 % | −4.8754 % | identical |
| 2025 `reversed` (soft latch) | 83 / 14.766 GW | 9 / 1.056 GW | the admitted set, recovering |
| **executed economic exits, 2023–2025** | **0.000 GW** | **0.000 GW** | **identical** |

**The cap-grain fix is emphatically NOT inert — ERCOT simply had nothing for it to act on.** In
PJM it changes the admitted exit set by an order of magnitude, and in exactly the direction
FFR-3C §1.2 G3 predicted: the old grain tested the schedule against a requirement **~10 % too
low**, so it over-admitted; resolving the requirement at the year the exits actually land retains
13.7 GW more capacity in the pipeline screen.

Two things this does **not** yet mean, both stated because they are easy to overread:

* **It does not change realized exits inside this window.** Both arms execute **0.000 GW** of
  economic retirement in 2023–2025. The 2025 screen shows why, and it is the soft latch rather
  than the lag: **every** admitted unit re-clears the bar and leaves the pipeline — 83 `reversed`
  / 14.766 GW in the pre-fix arm against 9 `reversed` / 1.056 GW in the cap-fix arm, exactly the
  sets each admitted the year before. So within this window the corrected grain changes *who is
  in the pipeline*, and the pipeline then empties itself either way. The membership change would
  first become visible as executions in **2026+**, outside a 3-year T1-FF window.
* **In-window dispatch skill is untouched.** Both PJM arms score identically (C1 fuel-mix
  12.230 / 18.843, C3a price 0.318 / 49.688 / 2.564), which follows from the exits never
  executing — nothing the corrected grain changes reaches the LP inside this window.
* **It is not validated against actuals.** A 93 % swing in pipeline membership is a large,
  correct-by-construction mechanism change; whether the corrected level is *closer to what PJM
  actually retired* is a scoring question on a posture where the exits execute, and this posture
  is not that. It is exactly the kind of change that must be scored leave-one-year-out before
  anyone promotes anything (§5.5), and it is why nothing here is promoted.

### 5.4b PJM throughput-armed pair — a measured null, and why

The second half of PJM's pairing, and the last arm the charter asked for. Armed at the measured
cap of **10,485 MW/yr** (5.243 GW × 2.0), cache key `cf02ef1bdccb4b1b` distinct from the
control's `d9c20dd23ee81f0a`, `meta.json` recording `exit_rate_limits: true` from the config the
solve ran on.

| PJM 2024 screen | control (cap off) | armed (cap 10,485 MW/yr) |
|---|--:|--:|
| `decided` | 9 / 1.056 GW | **9 / 1.056 GW** |
| `entry_capped` | 1,190 / 108.207 GW | **1,190 / 108.207 GW** |
| **`throughput_deferred`** | 0 | **0** |
| 2025 `reversed` | 9 / 1.056 GW | 9 / 1.056 GW |
| executed economic exits | 0.000 GW | 0.000 GW |
| reserve margin (2023/24/25) | −1.29 / −4.88 / −9.28 % | −1.29 / −4.88 / −9.28 % |
| invariants | 0 FAIL, 0 WARN | **0 FAIL, 0 WARN** |
| dispatch skill (C1 / C3a) | 12.230 / 18.843 · 0.318 / 49.688 / 2.564 | identical |

**Identical, and the reason is a code path rather than a coincidence:** the cap acts on the
year's **`due`** set — units that have reached `decided_year + L_f` — and
`_apply_exit_throughput_cap` is only invoked `if exit_rate_cap_mw is not None and due`. PJM
executes **0.000 GW** in every window year, so `due` is empty every year and the cap is never
called. This was predictable from the code before the run; it is reported here because
**predicted-inert and measured-inert are different claims**, and the charter asked for the
measurement.

**So the throughput cap is a measured NULL in BOTH test ISOs** — for the same underlying reason
in each (nothing executes), reached by different routes (ERCOT never decides anything; PJM
decides, then reverses). It has still never bound in a full solve. That is the honest state of
Task 2's validation, and it is why §10.2 says its first real test needs a posture with
executions.

### 5.5 Leave-one-year-out (rule 22)

LOYO is **degenerate on this evidence, and that is the honest report rather than a fold table.**
Rule 22's LOYO is scorer-side within 2023–2025 (FFR-2B §, "no re-solve"): each fold drops one
year from the *scored* capacity-event set and re-computes recall / false-retire / the T-R10
bands. Every arm measured here produces **0.000 GW of economic retirement in every year of both
ISOs**, so every fold's model-exit set is empty and every fold returns the identical degenerate
result — recall 0, false-retire 0 — regardless of which year is held out. A fold table would be
three identical rows of zeros and would imply a robustness check that was never actually
exercised.

**This does not clear the rule-22 bar; it means the bar cannot be evaluated from these runs.**
That is a statement about the posture, not about the mechanisms. Neither mechanism is being
recommended for promotion, so no LOYO-gated decision is pending — and if either is proposed for
promotion later, LOYO must be run on a posture that actually produces economic exits, which the
3-year T1-FF window does not.

## 6. Task 4 — the FH-1 §3.3 acceptance re-probe, stated plainly

**Posture:** ERCOT, base 2023, vintage 2023, 2023–2025, Arm R, 3 solve years, hindcast namespace,
`kind="full_forward"` — FH-1 §3.3's gate posture exactly, re-run at this branch's HEAD.

| invariant | recorded (FH-1 §3.3) | this re-probe | verdict |
|---|---|---|---|
| **I6** single-year econ retirement | **FAIL** — 21.05 GW = 26.8 % in 2025 | **PASS** — 0.00 GW, 0.0 % every year | **flipped to PASS** |
| **I7** reliability floor / accredited firm | **FAIL** — 2025 thermal 57.5 GW < floor 78.5 GW | **PASS** — held every year | **flipped to PASS** |
| **I12** reserve-margin band | **WARN** — band exits | **WARN** — band exits | **unchanged, but INVERTED** |

**Does it pass? On the letter of the gate, yes — and I do not think that should be read as the
gate being satisfied.** Three reasons, stated because the charter asked for the finding rather
than the verdict:

1. **The pass is not this lane's.** The pre-fix control returns the identical PASS/PASS/WARN
   (§5.2). Nothing FFR-3F built moved I6 or I7.
2. **I12's WARN has inverted sign, which is a new problem wearing the old problem's label.** FH-1
   exited the band *downward* (an over-retiring harness). This re-probe exits it *upward* —
   2024 at 32.3 % and 2025 at **40.2 %** against a ceiling of 28.7 %. The harness has swung from
   retiring 26.8 % of its thermal fleet in one year to retiring **nothing at all** while capacity
   keeps being added. An I12 WARN that used to mean "too short" now means "far too long", and the
   gate's own wording — *"an over-retiring harness would make every downstream metric
   uninterpretable"* — applies with equal force to a harness that cannot retire anything.
3. **The gate cannot exercise what it was re-probed to test.** Zero `pipeline_events` in any year
   means the retirement layer is untested at this posture, not validated by it.

**I therefore do NOT declare FH-4/FH-5 unblocked, and no part of this report should be read as
doing so.** The lift is the manager's, on a landed fix plus a green re-probe; what I can report
is that the fix landed, the re-probe's I6/I7 are green, and the greenness is attributable to a
decision taken before this lane started rather than to the fix. **Nothing was tuned toward the
gate** — the arms differ only in code version and one boolean.

## 7. What this evidence does NOT separate — stated plainly

Mirrors FFR-3C §5, because the same discipline applies to a fix lane as to an attribution lane.

1. **It does not quantify the calendar artifact as a fraction of the ERCOT/CAISO trough.**
   FFR-3C §5.1 said the only thing that would settle that is *"solving ERCOT with the exit wave
   spread and everything else held fixed."* **I did not do that, and I say so rather than
   implying otherwise.** The arm that would have done it — ERCOT with the throughput cap armed —
   is a measured **null**: there is no exit wave to spread at the FH-1 gate posture, because no
   ERCOT unit enters the retirement pipeline at all. The question FFR-3C left open is still open.
2. **It does not validate either mechanism against actuals.** The cap-grain fix now has a
   measured, live effect in PJM (−93 % of admitted exit MW, §5.4) — but a large correct-by-
   construction change is not evidence of improved *skill*. Neither mechanism has been shown to
   move any ISO closer to what it actually retired, because in both test ISOs the window executes
   **0.000 GW** of economic exits, so there is nothing to score against. The throughput cap in
   particular has still never bound in a full solve.
3. **It does not re-measure CAISO, MISO, NYISO or NEISO.** Their seeds are computed and tabled
   (§2.2) but no arm was run for any of them. MISO is excluded by evidence per D-8 bound 3;
   the other three were never in scope. Rule 25 `[R-ISO-SCOPE]`: nothing measured here transfers
   to any of them.
4. **It does not establish the 2.0 multiplier as correct for the exit side** — only as the
   *same* discipline already armed on the entry side, which is what makes the pair symmetric.
   Whether a real deactivation queue's throughput ceiling is 2× its historical maximum is not
   something this lane measured, and the value must not be moved to close a residual if it later
   proves loose (rules 11/23).
5. **It does not touch the FH-4/FH-5 block.** Lifting that is the manager's, on a landed fix
   **plus** a green re-probe. §6 reports the re-probe honestly; it does not claim the lift.

## 8. Mechanism matrix (rule 28)

Two cells exercised, **neither verdict status changed**, both notes and citations updated
in-session per duty (b); the new field's row added in the same PR per duty (c).
`scripts/check_mechanism_matrix.py` passes.

| row | cell | action |
|---|---|---|
| `exit_rate_limits` (**NEW ROW**, duty c) | ERCOT **O**, PJM **O**, others **U**; `fc` all-**U** | Row added with the new `ScenarioConfig` field in the same PR. ERCOT note records the measured **null** — armed and control identical to the megawatt, zero deferrals, no `pipeline_events` at all — and says explicitly that a null is not a pass. Cell stays **O** because a 3-year window that never enters the pipeline is a verdict on the *posture*, not the mechanism. DO-NOT-REDO marker left for the next session. |
| `economic_retirement_screen` | **unchanged** | Note records the landed G3 cap-grain correction, that it is provably inert at the FH-1 gate posture, and that the recorded I6/I7 FAIL does not reproduce at this HEAD — with the attribution split into what is *measured* (not FFR-3F's, via the pre-fix control) and what is *inferred* (D-1, by elimination). |

Rule 25 `[R-ISO-SCOPE]` observed throughout: no verdict transferred between ISOs, and each ISO's
cap is derived from its own market's EIA-860 record.

## 9. What this session does NOT claim

* **No promotion, no default flipped.** `exit_rate_limits` ships **default-OFF**;
  `retirement_rule` is still `pipeline`; both entry dampers stay armed exactly as Addendum D
  left them. Nothing here is a keeper or a candidate. Both are owner boxes and neither was
  opened.
* **No band widened, no threshold moved, no damper unarmed.** Addendum D's *HOLD PROMOTION, FIND
  ROOT CAUSE* stands untouched.
* **Nothing tuned to a residual.** The cap-grain fix introduces no parameter at all. The
  throughput cap's two constants are the entry side's own multiple and a declared window whose
  choice is measured to carry no DOF for the tested ISOs. Neither was chosen by looking at an
  output.
* **Nothing registered to the backcast registry.** `frontend/data/backcast/` is untouched; no
  keeper shard, `calibration-complete.json` entry, or `holdout-freeze.json` was read for writing
  or modified.
* **No holdout year touched.** Every arm is forecast-mode T1-FF over **2023–2025** — the rule-22
  training window — which the freeze explicitly does not restrict. Each leg printed its own
  governance line at launch confirming legality. No out-of-training year (2022, 2019, ≤2021,
  H1-2026) was solved, scored, or read, and no marker was spent.
* **The FH-4/FH-5 block is NOT lifted.** That is the manager's call on a landed fix plus a green
  re-probe, and §6 is deliberately written so the re-probe can be read either way without me
  having pre-judged it.
* **No ISO's verdict transferred to another** (rule 25). ERCOT's null says nothing about PJM, and
  neither says anything about the four ISOs not tested.

---

## 10. What would actually settle this — for the successor charter

Written as observations, not as a recommendation to arm or promote anything.

1. **The T1-FF 3-year window is the wrong instrument for testing exit mechanisms, and that is
   now measured rather than suspected.** Both test ISOs execute **0.000 GW** of economic
   retirement across 2023–2025. The reasons differ and both are structural: ERCOT never enters
   the pipeline at all, and PJM enters it but every admitted unit re-clears the bar and reverses
   before its execution year. Any successor that wants to measure an exit mechanism against
   actuals needs a posture whose window actually produces executions — the T1-H 2021–2025
   vintage-2020 posture FFR-2B used (where PJM's pipeline coal wave was 14.756 GW) is the
   obvious candidate, because a 5-year window clears `L_coal` = 3 with room to spare.
2. **The throughput cap has still never bound in a full solve.** It is correct against a
   synthetic cohort and inert in both measured ISOs, for the same reason: the cap acts on the
   *due* set, and the due set is empty everywhere in this window. Its first real test needs
   executions, i.e. the same posture change as (1).
3. **The cap-grain fix's 93 % PJM effect deserves a scoring pass, not a promotion.** It is a
   large, structurally-motivated change to pipeline membership with no measured skill
   consequence yet. Under rule 22 it needs leave-one-year-out on a posture where the exits
   execute; under rule 1 it stays in regardless of whether the residual moves, because the grain
   it corrects is a defect either way.
4. **The FH-1 §3.3 gate's I12 inversion is a live question this lane did not own.** The harness
   now runs 40.2 % reserve margin against a 28.7 % ceiling in ERCOT while retiring nothing.
   Whether that is the pipeline rule under-retiring, the entry side over-building, or the ERCOT
   band's known 6.65 pp basis mismatch (FFR-3C §2.1) is unattributed here.
