# FFR-3Q-3 — The FH-1 §3.3 gate re-probe, solved

**Session.** FFR Wave 3, the gate re-probe lane. Finishes **FFR-3Q Task 1**, which was
pre-registered in `docs/handoffs/ffr-3q-window-recut-2026-08-04.md` §2.1 and then never solved —
its first attempt hit the rule-22 bridge-seam breach recorded in that document's §2.2, which
**FFR-3U** (`docs/handoffs/ffr-3u-bridge-seam-2026-08-04.md`) has since fixed. Owner authorized
the dispatch 2026-08-04 (sitting **Addendum O**). Branch `claude/fh1-gate-reprobe-on6ylu`, off
`origin/main` **`68e7bfcd`** (the packet's stated HEAD `5eac75b0` was two commits stale at
session start; the two intervening commits are a MISO pre-registration doc and touch no `src/`
or `scripts/`, so every verification below stands at the rebased HEAD).

**Nothing is promoted, no default is flipped, no band is widened, no threshold is moved, no
marker is spent, and no window is widened to make anything legal.**

> ## THE FH-4/FH-5 LIFT IS A MANAGER BOX (Addendum I.1). I DID NOT LIFT IT.
>
> This lane was authorized to *run* the re-probe, not to adjudicate its consequence. Reporting
> the posture green does not lift the block, and — as §4 sets out — **this result is not green
> in the sense that would matter anyway.** The decision is the manager's.

---

## 0. Headline

1. **The FFR-3U fix HELD in a real run, and that is the first thing worth saying.** Both arms
   realized `solved [2021, 2023, 2024, 2025], bridged [2022]`. 2022 was evolved across, its LP
   never solved, **no `year_2022.parquet` written**, and **zero** 2022 measured demand / renewable
   CF / outage / hydro reads in either log. No parity failure. FFR-3Q's breach does not recur. §1.
2. **THE RE-CUT ACHIEVED ITS STATED PURPOSE: the retirement layer is OBSERVABLE for the first
   time.** Read 1 does **not** return the zero-event vacancy both prior probes returned. Arm A
   carries **1,205 `pipeline_events`** — a 29-unit / 8,218 MW coal cohort decided, re-confirmed
   and then reversed, plus 582/536 `entry_capped` rows. The headline-finding-by-vacancy branch of
   the pre-registration **does not fire**. §3.1.
3. **But ZERO units ever execute, so the EXIT half of the layer is still untested.** The cohort is
   **reversed by the soft latch at 2024 — its own `execute_year`**, one year after re-confirmation.
   `executed` events: **0**, in every year, in both arms. §3.1–§3.2.
4. **The two rules are NOT bit-identical here — they diverge violently and in OPPOSITE
   directions.** Against **1.534 GW** of actual ERCOT exits 2023-25: shipped `pipeline` retires
   **0.000 GW** (recall 0/3); `legacy` retires **17.309 GW** (97.1 % false). Both FAIL. This
   **breaks the FFR-3L null** for ERCOT and is a genuinely new measurement. §3.5.
5. **Invariants split with the rule.** Arm A **I6 PASS / I7 PASS / I12 FAIL**; Arm B **I6 FAIL /
   I7 FAIL / I12 WARN** — the FH-1 §3.3 triple reproduced **exactly** in the control. Unlike
   FFR-3F, the arms genuinely differ, so the I6/I7 flip **is** attributable to the retirement
   rule at this window. It is still not a pass: I12 degrades WARN → FAIL with **inverted sign**,
   *because* Arm A retires nothing. §3.3, §4.
6. **Read 4 remains a null, but a strictly stronger one.** `exit_rate_limits` stayed default-OFF
   and was OBSERVED. Its precondition — a non-empty `due` set — is **still never met in the
   pipeline arm**, now for a *different and sharper* reason: the pipeline is genuinely entered
   and the queue is still never departed. §3.4.

---

## 1. Rule 22 — the bridge contract, verified in both halves

FFR-3Q's breach violated the contract in both halves ("evolved across, never solved, data never
read"). Both are checked here, on the realized artifacts rather than on the banner.

| check | Arm A | Arm B |
|---|---|---|
| realized `solved_years` | `[2021, 2023, 2024, 2025]` | `[2021, 2023, 2024, 2025]` |
| realized `bridged_years` | `[2022]` | `[2022]` |
| `year_2022.parquet` written | **no** | **no** |
| `evolution_2022.json` written (evolved across) | yes | yes |
| 2022 measured demand / CF / outage / hydro reads in log | **none** | **none** |
| `leakage_violations` | `[]` | `[]` |
| solve-year parity assertion | passed | passed |
| `holdout_freeze_active_at_launch` | `true` | `true` |

The runner logged `year 2022: capacity-hindcast BRIDGE -- evolved, not solved` in both arms.

**Pre-solve, I verified the fix rather than trusting it** — the specific check FFR-3Q §2.2.2
identifies as the one it should have run and didn't:

```
is_bridge(2022) at base 2021, through the runner's own predicate ..... True
guard set  (window_solve_years)  ............................ [2021, 2023, 2024, 2025]
runner set (is_hindcast_bridge_year over the window) ........ [2021, 2023, 2024, 2025]  (equal)
tests/scoring/test_full_forward_hindcast.py::TestBridgeSeam .. 11 passed, 11 subtests
```

The harness's own launch banner — now *derived* from that predicate rather than static — printed
`this window SOLVES [2021, 2023, 2024, 2025] and BRIDGES [2022]`, and the completion assertion
compared it to the realized ledgers. Nothing was spent: `final` is EMPTY, `complete` =
{NEISO, NYISO, PJM} (**ERCOT is not in it**), and `holdout-freeze.json` is **ACTIVE** — all
re-read at this HEAD, none touched. The window is legal **by carve-out, not by marker**.

---

## 2. Posture, pairing and the cache keys

**Posture held verbatim from FFR-3Q §2.1**: ERCOT, Arm R (`hindcast_realized` gas +
per-solve-year weather), base 2021 / vintage 2020, window 2021-2025, shipped capacity-price
posture, D-1 and D-2 armed, `exit_rate_limits` default OFF, hindcast namespace,
`meta.kind="full_forward"`. Every optional flag was **omitted** so each arm inherits the shipped
`ScenarioConfig` default (the harness's flags default to `None` = inherit); confirmed on the
realized configs as `entry_rate_limits=True`, `entry_commissioning_lag=True`,
`exit_rate_limits=False`, `crossover_solve_year_weather=True`, `gas_price_path=hindcast_realized`.

| arm | `retirement_rule` | recorded cache key |
|---|---|---|
| **A — primary** (shipped default, owner D-1) | `pipeline` | **`6a824992b5fb1baf`** |
| **B — paired control** (explicitly labelled) | `legacy` | **`d065923f427349d1`** |

The `dataclasses.asdict` diff of the two configs contains **exactly one** entry —
`retirement_rule: pipeline → legacy`. `env | grep MARKET_SIM` is **empty** (FFR-3F §5 hazard does
not arise). Arm B is the one place Addendum D's *HOLD PROMOTION* permits unarming D-1: an
explicitly-labelled control. **Nothing else was unarmed anywhere.**

**Two notes on the keys, both of which mattered.**

* **They moved, as the packet predicted.** FFR-3Q measured `b99600bceb8cb6b8` /
  `5c352508039513da`; D-10's cache epoch has since moved every forecast key. Neither new key is
  on `results.cache.CONTAMINATED_CACHE_KEYS`, so **no refusal fired** — correct behaviour, since
  FFR-3U's D-11(b) denylist is scoped to the two *contaminated* keys and this re-probe solves on
  a clean tree. Both arms solved **cold** (`results/` is gitignored; a fresh container has no
  cache to hit).
* **The request-side key is NOT the recorded key, and here they genuinely differ** (FFR-3A-2
  §1.2). `runner.run_scenario_iso` hashes *after* `resolve_policy_bundle` and the ISO
  default-override merge. Request-side these configs hash to `1a1a6837237c3113` /
  `f68921649a940bf6` — **neither is the key the run is recorded under.** I computed the recorded
  keys by driving real argv through `build_config` and replicating that chain, and both matched
  the runtime `cache_key=` log line exactly.

---

## 3. The four pre-registered reads

Reads were fixed in FFR-3Q §2.1 **before** either arm solved and are reported in that order; none
was selected after the fact.

**Trap discharged first.** `load_ledgers_for_run` returns `{}` for a wrong path rather than
raising, and in *this* lane an empty read is indistinguishable from the primary finding. Ledgers
live at `<out-dir>/<ISO>/<cache_key>/`, **not** the out-dir root. The reader asserts the path
exists and enumerates the `evolution_*.json` files before interpreting any zero; both arms
returned all five ledgers (2021-2025).

### 3.1 Read 1 (PRIMARY) — `pipeline_events` per year: **NOT zero. The vacancy branch does not fire.**

Arm A (`retirement_rule=pipeline`):

| ledger year | event | `decided_year` | `execute_year` | n | MW |
|---|---|---|---|---:|---:|
| 2021 | *(none)* | | | 0 | 0 |
| 2022 *(bridge)* | `decided` | 2021 | **2024** | **29** | **8,218** |
| 2022 *(bridge)* | `entry_capped` | — | — | 582 | 58,684 |
| 2023 | `re_confirmed` | 2021 | 2024 | 29 | 8,218 |
| 2023 | `entry_capped` | — | — | 536 | 57,960 |
| 2024 | **`reversed`** | 2021 | **2024** | **29** | **8,218** |
| 2025 | *(none)* | | | 0 | 0 |
| | **`executed`, all years** | | | **0** | **0** |

**1,205 events total.** All 29 pipelined units are **coal**. Arm B carries **zero**
`pipeline_events` in every year — expected and not a finding: the legacy branch does not write
them (the schema says "`retirement_rule="pipeline"` only; empty under legacy").

So the re-cut **succeeded at the thing it was for.** Both prior probes were uninformative because
the layer never engaged; here it engages substantially. The pre-registration's instruction — *"if
this window also returns zero events, that is the headline finding and I6/I7/I12 are reported as
invariant-by-vacancy"* — **does not apply to Arm A**, and I am not invoking it.

**The decisive detail is `executed = 0`.** The cohort is **reversed at 2024, its own
`execute_year`**, by the soft latch (pipeline component 3,
`retirements.py:1449`): every pipelined unit is re-screened annually at the same bar and one that
re-clears leaves the pipeline. So the layer's *decision* machinery is now observable and its
*exit* machinery is still not.

### 3.2 Read 2 — candidates per screen year: the re-cut created the decision year, and it produced one cohort

The pre-registration's mechanical prediction was that `L_coal = 3` leaves **exactly two**
admissible exit-decision years — 2021 (→ execute 2024) and 2022 (→ execute 2025) — and that the
re-cut "succeeds or fails on whether the 2021/2022 screens produce candidates."

**Measured, by `decided_year` (the LOSS year, `year − 1` at screen time — not the ledger year):**

| decision loss-year | candidates | MW | `execute_year` | in-window? | outcome |
|---|---:|---:|---|---|---|
| **2021** | **29** (all coal) | **8,218** | **2024** | **yes** | **reversed at 2024** |
| **2022** | **0** | 0 | (2025) | — | no cohort formed |

One of the two admissible decision years produced candidates; the other produced none. **The
re-cut succeeded on its own stated test** — an in-window execution date was created and populated
— and then the exit was cancelled by the soft latch at the moment of execution.

A correction to my own first pass, worth recording because it is easy to get backwards: the
`decided` rows are *emitted* in the **2022** ledger but carry `decided_year = 2021`. Reading the
ledger year as the decision year would wrongly report a 2022 cohort executing in 2025.

### 3.3 Read 3 — I12 is MEASURED here, not attributed

Per the pre-registration, FFR-3N owns attributing the inversion (it attributed it to **storage
accreditation**, +11.34 pp, and measured the **retirement rule provably inert**, ΔRM = 0.0000 pp,
on a 677-field-clean pair at base 2023). This lane reports only whether the longer window moves
it.

| | I6 | I7 | I12 | 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|---:|---:|---:|---:|
| **Arm A** `pipeline` | **PASS** | **PASS** | **FAIL** | 48.5 % | 34.8 % | 40.9 % | 49.0 % |
| **Arm B** `legacy` | **FAIL** | **FAIL** | **WARN** | 48.5 % | 14.3 % | 20.7 % | 28.6 % |
| I12 scalar band | | | | \[13.8 %, 28.7 %\] | | | |

**The longer window DOES move it, and it moves it the wrong way.** I12 goes **WARN → FAIL**: Arm A
puts **all four** solved years above the ceiling, against Arm B's one. The **sign is INVERTED**,
exactly as the packet warned — the margin is too **high**, not too low, and the mechanism is
"over-retiring → retiring nothing."

Two things I am **not** claiming. (a) I am not attributing this to the retirement rule as a
general matter — FFR-3N's inertness result stands at *its* posture, and what this lane shows is
that the two postures differ, not that FFR-3N was wrong. (b) FFR-3N §1 records that I12's scalar
band is itself on the wrong basis (the model's own DR-netted floor is 7.15 %, not 13.75 %, making
the true ceiling 22.15 %). **Correcting it would make Arm A's excursion larger, not smaller** —
so this FAIL is robust to that known defect, and I am proposing no change to the band in either
direction.

### 3.4 Read 4 — the exit-throughput cap: OBSERVED, not armed; precondition still never met

`exit_rate_limits` remained at its shipped default **OFF** in both arms, exactly as
pre-registered. `_apply_exit_throughput_cap` fires only when a year's `due` set is non-empty
(`retirements.py:1516`), so the reportable precondition is whether `due` is *ever* non-empty.

| arm | any year with non-empty `due` | note |
|---|---|---|
| **A** `pipeline` | **NO** — empty in every year | the cap could act here, and has nothing to act on |
| **B** `legacy` | yes (2023: 308 retired + 79 floor-retained = **387** units wanted out) | **but the cap cannot fire in this branch at all** |

The Arm B "yes" is **not** evidence the precondition can be met. The cap's only call site is
inside `_apply_pipeline_retirements` (`retirements.py:1345`), so it exists **only** under
`retirement_rule=pipeline`; under `legacy` there is no queue for it to rate-limit. **The honest
read is that the precondition is still never met in the arm where the mechanism exists.**

This is nonetheless a **stronger null than FFR-3F's**, and it discharges the DO-NOT-REDO marker
that lane left ("a future ERCOT test of this cell needs a posture whose window actually produces
economic exits"). FFR-3F's null was "a 3-year window that never enters the pipeline" — a verdict
on the posture. Here the pipeline **is** genuinely entered (1,205 events, a real 8.2 GW cohort,
58.7 GW refused by the admission cap) and `due` is *still* always empty, because the cohort is
reversed before it can execute. The binding precondition for the next ERCOT test of this cell is
therefore no longer window length but **a decided cohort that survives the soft latch to its
execution year.**

### 3.5 Not a pre-registered read, but the largest measured difference: the two rules diverge

Reported because it is a direct, one-field-clean measurement this lane produced, and because it
**breaks a null another lane recorded**. Scored 2023-2025 (`SCORED_YEARS`, both bounds enforced):

| | actual | Arm A `pipeline` | Arm B `legacy` |
|---|---:|---:|---:|
| thermal retired, total | **1.534 GW** | **0.000 GW** (`err_frac` −1.0) | **17.309 GW** (`err_frac` +10.3) |
| unit recall (>300 MW) | 3 units | **0/3** (0.00) | 1/3 (0.333) |
| false-retire | — | 0.000 GW (PASS, trivially) | **16.807 GW = 97.1 % of model** |
| band verdict | | **FAIL** | **FAIL** |

**FFR-3L measured `legacy` and `pipeline` BIT-IDENTICAL on every scored T1-X metric and called it
"a NULL by construction."** That null was correct for its window and is broken here: at the
five-year re-cut the rule choice is the difference between retiring nothing and retiring eleven
times too much. Both fail; D-1 converts a gross over-retirement into a total non-retirement
rather than fixing it.

**One open root-cause item, flagged and deliberately NOT attributed** (attribution is not this
lane's charter, and I would rather hand over a clean question than a guess): the reversal runs
**counter to price direction.** The 2024 screen re-clears coal on 2023's dispatch
(**$15.77**/MWh system mean) that had failed on 2021's substantially richer **$23.40**/MWh — and
2024 is the *cheapest* year in the window ($13.62). Prices are near-identical across arms and
uniformly low (max $68.78/MWh in 2021, **no scarcity anywhere**), the signature of a
vintage-2020 fleet carrying a 48.5 % reserve margin. **The soft-latch bar, not the window, is now
the object to explain.** `screen_reserve_value_enabled` is on, so the reserve leg of the
attainable margin is the first place a successor should look.

---

## 4. How to read this result (Addendum G.2's three binds), stated explicitly

The packet requires me to say which of the three binds this result is. It is partly the third and
squarely the second, and it is **not** clean of the first.

**(a) "The earlier FH-1 green was NOT the fix's — a paired pre-fix control returned it
identically." — THIS LANE IS DIFFERENT, and that is a real (if narrow) advance.** In FFR-3F the
control returned an identical PASS/PASS/WARN, so the flip could not be the lane's. Here Arm B
returns **FAIL/FAIL/WARN** — reproducing the FH-1 §3.3 triple exactly — while Arm A returns
**PASS/PASS/FAIL**. The arms differ on a **one-field** diff. So the I6/I7 movement **is**
attributable to the retirement rule at this window. What that buys is smaller than it sounds: see
(c).

**(b) "I12's WARN had inverted sign." — CONFIRMED, and now worse.** It is no longer a WARN. Arm A
is a **FAIL** on all four solved years, all *above* the ceiling. The inversion is not incidental
to the I6/I7 green; it is the *same fact* seen from the other side. A fleet that retires nothing
keeps a 49 % reserve margin.

**(c) "Zero pipeline_events means the retirement layer was UNTESTED, not validated." — PARTIALLY
DISCHARGED, and I will not overstate which part.** The *decision* machinery is now genuinely
exercised: 1,205 events, a real cohort, an admission cap refusing 58.7 GW. That is no longer a
vacancy and I am not reporting it as one. **But `executed = 0`, so the exit machinery — the half
the gate is actually about — remains untested.** The I6 PASS and I7 PASS in Arm A are *produced
by* that vacancy: I6 bounds single-year economic retirement and I7 is a floor on retained
thermal, and **both are trivially satisfied by retiring nothing.** Against 1.534 GW of real
exits, Arm A retires 0.000 GW with 0/3 recall.

> **A GREEN ON A POSTURE THAT CANNOT EXERCISE THE MECHANISM IS NOT A PASS, and I am not rounding
> this vacancy up to one.** Arm A's I6/I7 PASS is the invariant equivalent of a division by zero.
> The correct summary is: **the gate did not pass**; the window re-cut succeeded at making the
> decision layer observable and thereby converted an uninformative null into a located,
> reproducible defect — the soft latch cancelling an 8.2 GW coal exit at its own execution year.

---

## 5. Governance position

* **No out-of-training year was solved, scored or registered.** 2022 bridged; scoring bounded to
  2023-2025 on both sides.
* **No marker spent, no marker file touched.** `final` EMPTY, `complete` unchanged,
  `holdout-freeze.json` unmodified. ERCOT holds **no** marker and needed none — the window is
  legal by the enumerated carve-out.
* **Nothing promoted, no default flipped, no band widened, no threshold moved.** In particular I
  propose **no** change to I12's band despite §3.3's known basis defect.
* **Both arms registered** to `frontend/data/hindcast/` with `meta.kind="full_forward"` —
  `ercot-2021-2025-t1ff-armr-ffr3q3-pipeline` and `-legacy`. **Never the backcast registry**;
  the backcast CI gates stay blind to this namespace. Slim bundle files only (zero parquets, per
  the `results/hindcast` convention).
* **Rule 28 discharged in this session** (§6).
* **FH-4/FH-5 is NOT unblocked. That is the manager's call under Addendum I.1 and I did not make
  it.**

---

## 6. Rule 28 — mechanism-matrix duties, discharged here

`scripts/check_mechanism_matrix.py` → **rc=0**, and the warning count is **223 before and 223
after** this diff (measured both ways by stashing) — the anchor-drift and NEISO keeper-stamp
warnings are pre-existing and untouched. `node --check` passes.

| row | cell | action |
|---|---|---|
| `t1ff_solve_year_weather` | ERCOT `fc` **stays O** | Posture ran mechanically clean again; gate did **not** pass. Evidence + the arms' invariant split recorded. |
| `economic_retirement_screen` | ERCOT `fc` **stays O** | The FFR-3L null is **broken** for ERCOT; both rules FAIL in opposite directions; mechanism (soft-latch reversal at `execute_year`) recorded. **Deliberately not R** — one posture on an over-supplied fleet is not a per-ISO rejection, and rule 28(d) forbids touching PJM/MISO where FFR-2B recorded the pipeline arm clearing its gate. |
| `exit_rate_limits` | ERCOT `fc` **stays O** | FFR-3F's DO-NOT-REDO discharged: the posture it asked for exists, and the precondition is *still* unmet for a sharper reason. New binding precondition recorded. |

No cell was flipped to a verdict this lane did not earn, and no other ISO's column was touched.

---

## 7. What the successor needs

1. **The open root-cause question is now specific: why does the soft latch re-clear 29 coal units
   at 2024, on a cheaper year's dispatch than the one that failed them?** (§3.5.) It runs counter
   to price direction. `screen_reserve_value_enabled` is on, so the reserve leg of the attainable
   inframarginal margin is the first suspect. This is the thing standing between the re-cut and an
   actually-exercised exit path.
2. **`exit_rate_limits` on ERCOT cannot be tested until a cohort survives to execution.** Window
   length is no longer the blocker. Do not re-run the cap probe on a longer window expecting a
   different answer.
3. **Do not quote Arm A's I6/I7 PASS as evidence of anything.** It is produced by retiring 0.000
   GW against 1.534 GW of real exits. §4(c).
4. **Do not quote either arm's dispatch-skill numbers as T1-FF skill.** Same reasoning FH-1 §7
   gave: the fleet trajectories are dominated by the retirement defect in both directions.
5. **The FH-4/FH-5 lift remains a manager box.** This lane's result does not open it, and reading
   §0 item 2 as "the gate is now informative, therefore proceed" would be exactly the misreading
   Addendum G.2 exists to prevent.
