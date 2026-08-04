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

*(pending)*

---

## 4. What this evidence does NOT separate

*(pending)*
