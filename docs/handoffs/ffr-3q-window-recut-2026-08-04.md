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

*(pending — filled after the arms land)*

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

### 2.2 Result

*(pending)*

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

## 4. What this evidence does NOT separate

*(pending)*
