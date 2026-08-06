# FFR-3Q — Re-cut the FH-1 §3.3 gate and the T1-H window to five years

**Session.** FFR Wave 3, the window re-cut lane, chartered by **owner decision G.5(a) + D-9**
(`docs/handoffs/ffr-owner-sitting-2026-08-02.md` **Addendum I**, signed 2026-08-04). Branch
`claude/ffr-3q-window-recut-aolov4`, off `origin/main` **`fab72654`** (the packet's stated HEAD
`5055b1a5` was already stale at session start).

**Nothing is promoted, no default is flipped, no band is widened, no threshold is moved, and
FH-4/FH-5 is NOT declared unblocked.** All of those are owner or manager boxes and none was
opened. Addendum I.1 is explicit that signing G.5(a) authorized the re-cut and the re-probe,
not the result.

---

## 0. Headline

1. **Task 0 — VERIFIED.** The enumerated carve-out in `scripts/lib/holdout_policy.py` does cover a
   base-2021 T1-FF window; `--forward-from-base` routes through the same `_validate_window`.
   No carve-out added or widened. §1. *(Discharged Addendum I.2's escalation clause — but see
   item 3, which is the part that determination did not reach.)*
2. **Task 2 — D-9(i) is a NO-OP for T1-H, and the H.4 convergence was wrong on that side.** All
   **57** registered plain-hindcast sidecars already run `[2021, 2023, 2024, 2025]`; T1-H has
   always been at the five-year posture G.5(a) moves the T1-FF gate *to*. The censoring survives
   and **no window length can remove it** — forward is closed by rule 22, backward by the 2021
   demand floor. Only the unsigned D-9(ii) can recover it. Escalated, not implemented. §3.
   *(Accepted upstream: Addendum J re-opened D-9 on this finding.)*
3. **Task 1 — STOP-THE-LINE. The re-cut window SOLVED 2022, a validation-tier holdout year, under
   an ACTIVE freeze — and the harness printed a banner promising it would not.** Both arms:
   `solved [2021, 2022, 2023, 2024, 2025], bridged []`, with measured 2022 demand, renewable CF,
   outage and hydro read. Cause is a harness defect — `_validate_window` drops 2022 as a bridge and
   never policy-checks it, while `runner.is_bridge` un-bridges it because T1-FF sets
   `crossover_forward_year = base_year = 2021`. **Base 2021 is the first posture whose window
   contains a bridge year, so this lane is the first that could hit it.** Bundles quarantined,
   nothing registered. **No I6/I7/I12 re-probe is reported** — it would describe a different
   experiment. Escalated; not patched by this lane. §2.2.
4. **FH-4/FH-5 is NOT unblocked, and G.5(a)'s gate re-cut cannot proceed until the seam is
   fixed.** Nothing promoted, no default flipped, no band widened, no threshold moved, no marker
   spent.

---

## 1. Task 0 — the rule-22 legality determination

**DETERMINATION: VERIFIED. The existing carve-out covers a base-2021 T1-FF window. No
carve-out was added, widened, or edited, and no escalation is required.**

Addendum I.2 recorded this half as *unchecked by any lane* — the T1-FF gate runs the
`--forward-from-base` harness, and whether the enumerated capacity-hindcast carve-out reaches a
**base-2021** T1-FF window had never been verified. It does, and the verification is by
execution rather than by reading prose.

### 1.1 What the code says

`scripts/lib/holdout_policy.py` at this HEAD carries the carve-out exactly as Addendum I.2
quotes it:

| constant | value | meaning |
|---|---|---|
| `HINDCAST_SEED_YEARS` | `{2021}` | solvable, **never scored** |
| `HINDCAST_BRIDGE_YEARS` | `{2022, 2026}` | evolved across, **never solved, data never read** |
| `HINDCAST_SOLVE_YEARS` | `{2021, 2023, 2024, 2025}` | = `CALIBRATION_YEARS ∪ seed`; **four** solve-years, under the ≤5 cap |

The decisive point for T1-FF is **`scripts/run_capacity_hindcast.py::_validate_window`**, which
`--forward-from-base` routes through unchanged. Its non-crossover branch applies the **plain**
window rules to a full-forward run — the 2021 floor, the `end <= 2025` cap, the `{2021}` seed
allowance and the 2022 bridge — and its docstring says so in terms:

> *A full-forward hindcast (`forward_from_base`, FH-1) keeps the PLAIN window rules exactly …
> because pointing the input boundary at the base year changes which STACK a year solves on,
> never which years may be solved.*

It then re-checks the surviving solve years against `holdout_policy.hindcast_solve_year_violations`,
which **fails closed** (`tier_for_year` treats any unenumerated year as locked-test, the
strictest tier). So the T1-FF window is gated by the *same* carve-out as T1-H, not by a
separate, unwritten one.

### 1.2 The verification, executed

```
_validate_window(2021, 2025, crossover=False, forward_from_base=True)  → OK (no raise)
_validate_window(2023, 2025, crossover=False, forward_from_base=True)  → OK  (the FH-1 posture)
ALLOWED_SOLVE_YEARS = [2021, 2023, 2024, 2025]
ALLOWED_VINTAGES    = (2020, 2023)
```

Vintage 2020 is enumerated and satisfies the `--forward-from-base` requirement `vintage <= base`
(2020 ≤ 2021). The harness's own `--help` already names this posture — *"Phase A: base 2023 /
vintage 2023; **Phase B: base 2021 / vintage 2020**"* — so the window is not merely tolerated by
the guard, it is the anticipated second phase.

### 1.3 What is spent: nothing

* Solve years `{2021, 2023, 2024, 2025}`; 2022 bridged (evolved, never solved, data never read).
* Scoring bounded to 2023–2025 on **both** sides (`score_crossover._scored_year`, the symmetric
  FH-1 lower bound).
* `final` is EMPTY, `complete` = `{NEISO, NYISO, PJM}`, and `holdout-freeze.json` is **ACTIVE** —
  all three re-read at this HEAD and none of them touched. The window is legal **by carve-out,
  not by marker**, exactly as Addendum I.1 requires.

---

## 2. Task 1 — the re-cut FH-1 §3.3 gate

### 2.1 Posture, pairing and pre-registration (recorded BEFORE any arm was solved)

**The window moves; nothing else does.** Every other element of FH-1 §3.3's posture is held
identical — ERCOT, Arm R (`hindcast_realized` gas + per-solve-year weather), the shipped
capacity-price posture, D-1 and D-2 armed, `exit_rate_limits` at its default OFF, hindcast
namespace, `kind="full_forward"`.

| | FH-1 §3.3 (recorded) | FFR-3F re-probe | **FFR-3Q (this lane)** |
|---|---|---|---|
| base / vintage | 2023 / 2023 | 2023 / 2023 | **2021 / 2020** |
| window | 2023–2025 | 2023–2025 | **2021–2025** |
| solve years | 3 | 3 | **4** (2021 seed + 2023/24/25; 2022 bridged) |
| arm | R | R | R |
| ISO | ERCOT | ERCOT (+PJM) | ERCOT |

**The pairing, verified before either arm was read** (charter Task 1.4). Both configs built
from `build_config` at this HEAD and diffed field-by-field:

| arm | `retirement_rule` | cache key |
|---|---|---|
| **A — primary** (shipped default, owner D-1) | `pipeline` | `b99600bceb8cb6b8` |
| **B — paired control** (explicitly labelled) | `legacy` | `5c352508039513da` |

Keys **distinct**; the `dataclasses.asdict` diff of the two configs contains **exactly one**
entry — `retirement_rule: pipeline → legacy`. `MARKET_SIM_DATA_ROOT` is **unset** in this
session (`env | grep MARKET_SIM` returns nothing), so the FFR-3F §5 hazard — a data root outside
`REPO_ROOT` shifting the cache key for a reason that is not a config difference — does not arise
and both arms read the same tree. D-1's `pipeline` default and D-2's `entry_commissioning_lag` /
`entry_rate_limits` are **armed** in arm A (`entry_commissioning_lag=True`,
`entry_rate_limits=True`); arm B unarms D-1 **only** inside the explicitly-labelled control,
which is the one place Addendum D's *HOLD PROMOTION* permits it.

**Pre-registered reads.** Written down before solving so no read is selected after the fact:

1. **The purpose of the re-cut is that the retirement layer becomes observable.** The primary
   read is `pipeline_events` per year. Both prior probes returned **zero events of any kind in
   every arm**, which is why both were uninformative. If this window also returns zero events,
   **that is the headline finding** and the I6/I7/I12 verdicts are reported as invariant-by-
   vacancy, not as a pass.
2. **The mechanical prediction that motivated G.5(a):** `L_coal` = 3 means a unit decided at the
   2023 screen executes in 2026 and one decided at 2024 executes in 2027 — both still outside a
   window ending 2025. Only a **2021 or 2022** decision can execute in-window (2024 / 2025). So
   the five-year window creates *exactly two* admissible exit-decision years, and the re-cut
   succeeds or fails on whether the 2021/2022 screens produce candidates.
3. **I12 is measured, not attributed.** FFR-3N owns attributing the inversion (40.2 % margin
   against a 28.7 % ceiling); this lane reports whether the longer window changes it.
4. **The exit-throughput cap is observed, not armed.** `exit_rate_limits` ships default-OFF and
   stays off. `_apply_exit_throughput_cap` is only invoked when the year's `due` set is
   non-empty, so the reportable precondition is whether `due` is ever non-empty in this window —
   that is what "could it bind" means here, and it is readable from the default-off arm.

### 2.2 Result — **STOP-THE-LINE. The re-cut window SOLVED 2022. No re-probe is reported.**

**Both arms solved a validation-tier holdout year under an ACTIVE holdout spend freeze.** The
arms ran to completion (ERCOT, base 2021, vintage 2020, Arm R, ~25 min each, 2 concurrent) and
both printed:

```
[full_forward] done. solved [2021, 2022, 2023, 2024, 2025], bridged []
```

`meta.json`, both arms: `solved_years: [2021, 2022, 2023, 2024, 2025]`, `bridged_years: []`,
`leakage_violations: []`, `holdout_freeze_active_at_launch: true`.

**2022 data was READ, not merely stepped over.** From the arm-A log:

```
year 2022: T1-FF Arm R given-weather rebind -- demand profile and renewable CF
           re-seeded from weather year 2022
ERCOT 2022: correlated forced-outage derate (weather year 2022, era post) ...
Loaded ERCOT 2022 hydro budget: 15 plants, 350.8 GWh annual, 554 MW nameplate
```

Measured 2022 demand, renewable CF, outage and hydro all entered the solve, and a
`year_2022.parquet` was written in each bundle.

**I am not reporting an I6/I7/I12 re-probe, and the three-point comparison the charter asked for
is NOT delivered.** It would be invalid: the fleet these invariants describe evolved *through* a
measured-2022 solve, which is not the posture the FH-1 §3.3 gate tests. Quoting those numbers as
the re-cut gate's result — in either direction — would be reporting a different experiment under
the gate's name. Both bundles carry a `QUARANTINE-DO-NOT-REGISTER.txt`, neither is registered,
and `frontend/data/hindcast/` is untouched.

#### 2.2.1 Root cause: the guard and the runner disagree about what a "forward year" is

This is a **harness defect**, not an operator choice, and it is in code both prior probes ran
without ever exercising.

`runner.py` decides bridging as:

```python
is_bridge = (config.hindcast and year in HINDCAST_BRIDGE_YEARS
             and not config.is_crossover_forward_year(year))
```

T1-FF's whole construction is to point the crossover boundary at the window's **own base year**
(`crossover_forward_year = start_year`). At base 2021 that makes **every** year ≥ 2021 a
"crossover forward year" — including the bridge years. Measured at this HEAD:

| year | in `HINDCAST_BRIDGE_YEARS` | `is_crossover_forward_year` | ⇒ `is_bridge` |
|---|---|---|---|
| 2022 | ✅ | ✅ (≥ 2021) | **False — SOLVED** |
| 2026 | ✅ | ✅ (≥ 2021) | **False — would also be solved** if a window reached it |

Meanwhile `_validate_window` computes its solve-year set with the **`--crossover` flag**, which is
`False` for a T1-FF run — so it excluded 2022 as a bridge and **never policy-checked it**:

```
_validate_window solve-year set (what the guard checked): [2021, 2023, 2024, 2025]
```

The un-bridging clause is correct *for its original purpose*: a T1-X crossover's forward years are
2026/2027, solved in forecast mode reading no measured actuals, which rule 22 explicitly permits.
Re-pointing the boundary at 2021 silently extends that permission to a year for which it was never
true. **The fail-closed policy check never sees 2022, because the guard removed it before the
check ran.**

#### 2.2.2 Why no earlier lane hit this, and why my Task 0 verification did not catch it

Every prior T1-FF run — FH-1's gate, all three FFR-3F ERCOT arms, all three PJM arms — was **base
2023, window 2023–2025**. 2022 is not in that window, so the defect could not fire. **Base 2021 is
the first posture whose window contains a bridge year, and that posture is precisely what G.5(a)
authorized.** This lane is the first that could have hit it, and did, on its first solve.

**My Task 0 determination in §1 was correct about what it checked and wrong about what it
implied, and that is my error to own.** Addendum I.2 asked whether the carve-out *enumerates* a
base-2021 T1-FF window; it does, and `_validate_window` passes. But I reported that as "no
out-of-training year is solved" (§1.3), which is a claim about **runtime behaviour** that I
verified only against the **guard**. The guard is not what decides which years get solved. The
check I should have run — and did not — was the runner's `is_bridge` predicate at base 2021,
which takes about a minute and would have caught this before burning two solves. I verified the
gate, not the behaviour behind it.

#### 2.2.3 Governance position, stated plainly

* **A validation-tier year (2022) was solved and its measured data read, under an ACTIVE freeze.**
  Rule 22's bridge contract — *"evolved across, never solved, data never read"* — is violated in
  both halves.
* **Nothing was scored outside 2023–2025.** Scoring is independently bounded on both sides
  (`score_crossover._scored_year`, `score_capacity_hindcast.SCORED_YEARS`), and no scorer ran.
* **No marker was spent and no marker file was touched.** `final` is still EMPTY, `complete` is
  unchanged, `holdout-freeze.json` is unmodified.
* **Nothing is registered.** No sidecar, no dashboard entry, no matrix verdict claimed from these
  arms.
* **The harness asserted the opposite at launch.** Its governance banner printed *"bridges
  [2022, 2026] are never solved or read"* — a guarantee it then broke. That the false assurance is
  printed by the same script that breaks it is the most dangerous property here: a future lane
  reading the banner would have no reason to doubt it.

**This is escalated to the owner, not worked around.** I did not patch `is_bridge` to make my own
window legal — that is the rule-22-adjacent move this policy exists to prevent, and it is the
same class of act Addendum I.1 refused to authorize for the carve-out. The fix is a real code
change to a solve-affecting guard, it needs its own charter and its own review, and G.5(a)'s
gate re-cut **cannot proceed until it lands**.

#### 2.2.4 What the successor needs

1. **Fix the seam, under its own charter.** `is_bridge` must not treat a bridge year as
   un-bridged merely because it sits above a T1-FF base-year boundary. The un-bridging clause
   should be scoped to genuine crossover forward years (`crossover=True`, year ≥ 2026), not to any
   year above `crossover_forward_year`. `_validate_window` must additionally policy-check every
   year the runner will actually solve, rather than a set it computes from a different predicate —
   the two must share one definition (rule 19 `[R-ONE-MECH]` applied to the guard itself).
2. **Add the regression test that would have caught it:** at base 2021, assert the runner's
   `is_bridge(2022)` is True and that `solved_years` excludes 2022. A parity test between
   `_validate_window`'s solve set and the runner's realized `solved_years` would catch the whole
   class.
3. **Re-run the gate only after (1) lands.** The re-probe is unexecuted; §2.1's pre-registration
   stands and can be reused verbatim.
4. **Check whether any committed artifact is affected.** These two bundles are quarantined and
   unregistered. I did **not** audit whether any previously-registered run hit the same seam — no
   prior T1-FF window contains a bridge year, so the exposure looks nil, but that is reasoning
   from the window list, not an audit, and it should be confirmed rather than assumed.

---

## 3. Task 2 — the T1-H window (D-9)

### 3.1 The determination: **D-9(i) is a no-op for T1-H, because the T1-H window has ALWAYS been the five-year 2021–2025 window**

This is the finding, and it is checkable in one line: `run_capacity_hindcast.py`'s plain-hindcast
mode defaults to `start_year = 2021`, `end_year = 2025`, and **every T1-H leg ever registered ran
that window.** All **57** registered plain-hindcast sidecars in `frontend/data/hindcast/` are
named `<iso>-2021-2025-*`; **zero** non-crossover, non-full-forward legs start anywhere else, and
**zero** carry a `solved_years` other than `[2021, 2023, 2024, 2025]`. Each records:

```
"solved_years": [2021, 2023, 2024, 2025],  "bridged_years": [2022],
"start_year": 2021, "end_year": 2025, "vintage_year": 2020
```

That is the same five-year, vintage-2020, four-solve-year posture G.5(a) moves the **T1-FF gate**
to. T1-H was already there — going back to the earliest `*-realized` legs, before the FF program
existed.

**So there is no shorter T1-H window to lengthen, and no additions band becomes newly visible.**
The charter's Task 2.2 asks which verdicts changed because the model got better and which changed
because the metric can now see them. The honest answer is **neither, because nothing changed** —
and stating that is the whole point, because reporting a re-measurement here would manufacture
exactly the improvement FFR-3A-3 correctly refused to manufacture on FC-2 row 4.

### 3.2 Why the censoring survives a five-year window — and why no window length removes it

H.4's diagnosis is correct; only its proposed remedy does not reach. The mechanism, stated on the
code:

`evolve_fleet` books an entry decision at year `Y` into `entry_pipeline` with
`cod_year = Y + ENTRY_COD_LAG_YEARS[tech]` (= `Y + 2` for wind/solar/gas_cc/gas_ct), and
`score_capacity_hindcast.model_additions` reads additions **by the ledger year they commission
in**. The decision years available in a 2021–2025 window, and where each commissions:

| decision year | COD year | observable? |
|---|---|---|
| 2021 (seed) | 2023 | ✅ scored |
| 2022 (bridge — evolved, not solved) | 2024 | ✅ scored |
| 2023 | 2025 | ✅ scored |
| **2024** | **2026** | ❌ outside the window |
| **2025** | **2027** | ❌ outside the window |

Three of five decision cohorts land in the scored window — so the additions band compares three
model decision cohorts against three actual COD years, but **shifted two years earlier**, and the
last two decision years produce nothing observable at all. That is H.4's "half the solved decision
years cannot score."

**Both directions of lengthening are closed, and neither is closed by choice:**

* **Forward is closed by rule 22, absolutely.** Making the 2024/2025 decisions observable requires
  *scoring* 2026 and 2027. 2026 is a **locked-test** year (`LOCKED_TEST_YEARS = {2019, 2026}`);
  `final` is EMPTY; the holdout spend freeze is ACTIVE; and 2027 has no actuals to score against
  at all. `_validate_window` hard-caps a non-crossover window at `end <= 2025`, and
  `score_crossover`/`score_capacity_hindcast` refuse both bounds independently. Lengthening
  forward is not a code change — it is a marker spend the owner explicitly did not make.
* **Backward is closed by data and by tier.** `_validate_window` floors the start at 2021
  ("demand profiles start 2021"), and 2020 is a **validation-tier** year, gated behind `complete`
  *and* the active freeze.

**Therefore: G.5(a) and D-9(i) are NOT the same action, and the convergence recorded in H.4 holds
on the exit side only.** G.5(a) lengthens the T1-FF *solve* window from three years to five —
legal, executable, and done in §2. D-9(i) would have to lengthen the T1-H *scoring* window past
2025, which rule 22 forbids outright. The two blockers really are symmetric in *diagnosis*
(`L_coal` = 3 and `ENTRY_COD_LAG_YEARS` = 2 both exceed a three-year window) but not in *remedy*,
because the exit side's window was genuinely three years and the entry side's was already five.

**This is escalated, not worked around.** The only remedy that can recover the censored half is
**D-9(ii) — score COD-shifted additions, attributing an addition to its decision year rather than
its COD year** — which is a scorer-side change needing no out-of-training year, and which the
owner did **not** sign (H.4's sign-off took (i) via "take with G.5(a)"). This lane did not
implement it: (ii) is a different decision from the one signed, and changing how a band is
computed in order to move a verdict is precisely what rules 1/11/14 forbid a lane from doing on
its own initiative.

### 3.3 What the censored mass actually costs — measured from committed artifacts

No solve was needed for this. Model cumulative additions across every registered T1-H leg, with
the D-2 commissioning lag off and on:

| ISO | lag OFF (shipped-posture FF-2E leg) | lag ON (FF-2D battery leg, `*-ffr3a2`) | actual |
|---|--:|--:|--:|
| PJM | 44.155 GW (`pjm-2021-2025-shipped-ffr2e`) | **11.602 GW** | 24.092 GW |
| MISO | 16.546 GW (`miso-2021-2025-shipped-ffr2e`) | **9.146 GW** | 31.981 GW |
| NEISO | 14.720 GW (`neiso-2021-2025-shipped-ffr2e`) | **3.028 GW** | 2.981 GW |
| NYISO | 14.000 GW (`nyiso-2021-2025-curve`) | **3.342 GW** | 3.375 GW |

> ⚠ **NOT like-for-like, and it must not be read as an effect size for the lag.** These pairs
> differ in **three** fields, not one: `entry_commissioning_lag` False→True, `entry_rate_limits`
> False→True, and `retirement_rule` `legacy`→shipped `pipeline`. NYISO's pair also crosses a
> capacity-clearing posture (`curve` vs `shipped`; NYISO ships curve-OFF). H.4 said a
> cross-boundary additions comparison is not like-for-like and that stands — this table shows the
> **direction and rough magnitude** of the suppression, nothing sharper. Isolating the lag needs a
> paired control that this lane's charter did not include and that no committed leg provides.

Two observations that are worth more than the magnitude:

1. **The suppression is not uniformly harmful — in two ISOs it is the thing that fixed the total.**
   NEISO 3.028 GW against an actual 2.981, and NYISO 3.342 against 3.375, are both within ~2 % on
   cumulative additions, against lag-off legs that over-built by ~5×. Reading the censoring as a
   pure metric defect would miss that. Where it clearly bites is PJM (−52 % vs actual) and MISO
   (−71 %).
2. **The bands still FAIL in all four, and on tech mix rather than level.** NEISO and NYISO hit
   the total almost exactly and still fail `solar`, `gas_ct` and `storage` — so at least in those
   two ISOs the censored half is **not** what FC-3 is failing on. Attributing FC-3's failure to
   the censoring alone would be wrong for them.

### 3.4 MISO's FC-3 (charter Task 2.3)

**Unchanged: FAIL, and it does still fail on the additions half alone.** Read from the committed
`miso-2021-2025-ffr3a2` sidecar and `frontend/data/forecast/ff-verdicts.json` at this HEAD — no
re-solve, no re-score:

| family | bands |
|---|---|
| retirements | `total_gw` PASS (−9.8 %), `unit_recall_gt300` PASS (0.765), `false_retire` PASS (0.147) — **zero FAIL** |
| additions | wind, solar, gas_cc, gas_ct, storage — **all five FAIL** |

MISO is the **only** registered T1-H leg of any ISO with an empty retirement-FAIL set, which is
what makes H.4's "fails on the censored half alone" literally true for it. Its FC-3 determination
is `FAIL` and its rubric determination `HOLD`, identical to FF-2D. **Nothing about that moved in
this session, and nothing could have** — §3.1.

For completeness, its additions detail: solar 0.0 GW model vs 18.649 actual (the single largest
term), wind 4.0 vs 7.2, gas_cc 1.146 vs 3.867, gas_ct 0.0 vs 1.379, storage 4.0 vs 0.744. A
2-year COD shift cannot explain a **zero** solar build against an 18.6 GW actual; that is an entry
screen finding, not a window finding, and it is not this lane's to attribute.

### 3.5 A separate defect this lane did not fix: FC-7 still fails on every T1-H and T1-X leg

H.5 item 3 — `run_capacity_hindcast.py` writes `run_config.yaml` where FC-7 reads `.json`. **Not
fixed at this HEAD:** line 1303 is still `config.to_yaml_full(args.out_dir / "run_config.yaml")`,
and every `*-t1h` / `*-t1x` entry in `ff-verdicts.json` reads FC-7 `FAIL`. **FFR-3K had not landed
when this lane's arms were solved, so this lane's legs sit on the pre-fix side of it** and will
carry the same FC-7 FAIL. Recorded so the successor knows which side of FFR-3K these bundles are
on; not fixed here, because it is FFR-3K's charter and not this one's.

---

## 4. What this evidence does NOT separate — stated plainly

Mirrors FFR-3C §5 / FFR-3F §7.

1. **It does not tell you whether the re-cut gate passes or fails.** That is the deliverable
   G.5(a) authorized and it is **not delivered**. The arms produced numbers; those numbers
   describe a run that solved 2022 on measured data, which is not the gate's posture. Reporting
   them as the re-probe — green *or* red — would be substituting a different experiment. The
   charter's three-point I6/I7/I12 comparison against FH-1's FAIL/FAIL/WARN and FFR-3F's
   PASS/PASS/WARN remains **open**.
2. **It does not measure whether a five-year window makes the retirement layer observable.** The
   pre-registered primary read — `pipeline_events` per year, and whether a 2021/2022 decision can
   execute in-window under `L_coal` = 3 — is unmeasured. The mechanical argument in §2.1 that only
   a 2021 or 2022 decision *could* execute inside a window ending 2025 stands as **reasoning, not
   measurement**, and must not be cited as a result.
3. **It does not establish whether the exit-throughput cap can bind.** Whether the `due` set is
   ever non-empty in a five-year window is still the open question FFR-3F §10.2 left. `due` was
   not read from these bundles, because reading anything from them as evidence is the thing this
   section refuses.
4. **It does not attribute the I12 inversion, and did not try to.** That is FFR-3N's lane. Its
   band-basis half has landed and is worth carrying: the exact basis gap is **6.5975 pp**
   (`0.942 × 1.1375 − 1 = 7.1525 %` enforced vs **13.75 %** scored), which **corrects FFR-3C §2.1's
   6.65 pp** — that figure was taken off a rendered `13.8%` rather than the `0.1375` scalar.
   FFR-3N's attribution arms were still open at this HEAD.
5. **It does not audit prior runs for the same seam.** No previously-registered T1-FF window
   contains a bridge year, so the exposure *looks* nil — but that is inference from the window
   list, not an audit, and §2.2.4 item 4 asks for it to be confirmed.
6. **On Task 2, it does not isolate the commissioning lag's effect on additions.** §3.3's
   lag-off/lag-on table crosses **three** changed fields, not one. It shows direction and rough
   magnitude only; an effect size needs a paired control no committed leg provides.
7. **It does not re-validate anything scored on the three-year window.** Every committed T1-H
   additions verdict was produced under the H.4 censoring and stays interpreted that way — which,
   per §3, is now permanent rather than pending a re-measurement.

---

## 5. What this session does NOT claim

* **FH-4/FH-5 is NOT unblocked.** The lift is the manager's, on a landed fix plus a green
  re-probe. There is no re-probe. Addendum I.1 is explicit that G.5(a) authorized the re-cut and
  the re-probe, not the result.
* **No default flipped, nothing promoted, no band widened, no threshold moved, no damper
  unarmed** outside the explicitly-labelled `--retirement-rule legacy` control arm. `exit_rate_limits`
  stays default-OFF and was never armed. D-1 and D-2 stay armed exactly as Addendum D left them.
* **No holdout marker spent and no marker file modified.** `final` EMPTY, `complete` unchanged,
  `holdout-freeze.json` unmodified, NEISO's locked test still unspent. *[Corrected
  2026-08-06, D-23: this read "still SPENT"; NEISO's locked test was never granted or
  spent. This session's no-spend attestation is unaffected.]*
* **Nothing registered anywhere.** No backcast registry, no `frontend/data/hindcast/` sidecar, no
  forecast namespace, no dashboard entry. Both bundles carry a `QUARANTINE-DO-NOT-REGISTER.txt`.
* **No mechanism-matrix verdict was claimed from the quarantined arms.** A run that solved a
  holdout year cannot adjudicate a cell in either direction, so `exit_rate_limits` and
  `economic_retirement_screen` keep their existing ERCOT `O`. The rule-28(b) duty is discharged by
  recording the DO-NOT-REDO fact — *the base-2021 T1-FF posture is blocked on a harness defect* —
  rather than by inventing a verdict.
* **The harness defect was NOT patched by this lane.** Editing a solve-affecting guard to make my
  own window legal is precisely the move rule 22 exists to prevent; it needs its own charter.

---

## Addendum (2026-08-04) — Task 1 has since been SOLVED by FFR-3Q-3

**This document is unchanged above this line.** §2.1's pre-registration was reused **verbatim**,
as §2.2.4 item 3 said it could be, and §2.2 stands as the permanent stop-the-line record.

The seam fix landed as **FFR-3U** (`docs/handoffs/ffr-3u-bridge-seam-2026-08-04.md`), and the
owner authorized the re-probe on 2026-08-04 (sitting **Addendum O**). The result is reported in
full at:

> **`docs/handoffs/ffr-3q3-gate-reprobe-2026-08-04.md`**

Three things from it that a reader of §2.2 will want immediately:

1. **The breach does not recur.** Both arms realized `solved [2021, 2023, 2024, 2025], bridged
   [2022]` — no `year_2022.parquet`, no 2022 measured data read, no parity failure. The
   `is_bridge(2022)` check §2.2.2 identifies as the one this lane should have run *was* run
   before solving, and passed.
2. **The re-cut achieved its purpose: the retirement layer is OBSERVABLE.** §2.1 read 1's
   zero-event vacancy branch **does not fire** — Arm A carries 1,205 `pipeline_events`. But
   `executed = 0`: a 29-unit / 8,218 MW coal cohort decided at loss-year 2021 is reversed by the
   soft latch at 2024, its own `execute_year`. The decision half is now tested; the exit half is
   not.
3. **It is not a gate pass.** Arm A reads I6 PASS / I7 PASS / I12 FAIL and Arm B reproduces the
   FH-1 §3.3 triple exactly (FAIL/FAIL/WARN) — so the flip *is* the retirement rule's here,
   unlike FFR-3F. But Arm A's green is bought by retiring **0.000 GW** against **1.534 GW** of
   actual exits, and I12 inverts to FAIL on all four solved years. **FH-4/FH-5 remains a manager
   box and was not lifted.**
