# FINDING — SPP-68: the `[R-HOLDOUT]` footprint sweep. Five live instances, one of them a HARD GATE

**Zero LP.** Second deliverable of lane SPP-68, taken independently of what the curtailment
ceiling does. Base `05b2231da6e2e70bf9a122cece864a7673e2b2f7`.

## Why this sweep exists

SPP-67's defect was **not** a modelling error. `_SPP_REFERENCE_RATE_YEARS` was frozen at
`{2023, 2024, 2025}` for one stated reason — *"the structural rate must never read a validation
or locked-test year"* — and rule 22 `[R-HOLDOUT]`, the rule that made a year "validation" or
"locked-test", was **REMOVED by owner instruction on 2026-09-09**. A removed rule's footprint was
still narrowing what a measured input was allowed to read, and it cost SPP a factor of **6.1** on
2019's curtailment rate (published 1.591 % against 9.650 % applied).

That is a *class* of defect, not an incident. This sweep looks for the rest of it.

**Method.** `grep -rn "R-HOLDOUT\|holdout\|training-window\|training window\|#22" src/ --include=*.py`
plus the same over `scripts/`, then **every hit read in source** and classified against the one
question rule 14 `[R-ACCURATE]` asks: *is an accurate, available measurement being passed over for
an estimate — or refused outright — because a rule that no longer exists said it must be?*

Dead-comment hits (≈ 40 of them: "the 2023-2025 training-window mean", "rule 22" as a historical
citation, derive-provenance notes) are **not** instances. A comment recording how a value was
identified is the audit trail rule 24 `[R-REGISTRY]` wants; it narrows nothing. Only constructions
that still **change what the model reads or may solve** are listed below.

---

## THE FIVE LIVE INSTANCES

| # | site | what it still does | owner | verdict |
|---|---|---|---|---|
| **A** | `scripts/lib/holdout_policy.hindcast_solve_year_violations`, enforced at `scripts/run_capacity_hindcast.py:364` | **HARD-REFUSES** any hindcast solve year outside `{2021, 2023, 2024, 2025}`, by tier | forecast program | **CARD — the largest find** |
| **B** | `src/market_sim/runner.py:241` `HINDCAST_BRIDGE_YEARS = {2022, 2026}` | 2022/2026 are evolved across but **never solved and their data never read** in a hindcast window | forecast program | CARD (downstream of A) |
| **C** | `src/market_sim/data/emission_rates.py:269` `QUARANTINED_RATE_BASIS_YEARS = {2022}` | drops 2022's **measured CEMS rows** from the T1-FF estimator basis | forecast program | CARD |
| **D** | `src/market_sim/data/hydro.py:598` `_HYDRO_QUARANTINED_YEARS = {2022, 2026}` | drops 2022 from the as-of hydro **climatology** | forecast program | CARD (downstream of B) |
| **E** | `src/market_sim/data/renewables.py:772` `_MISO_REFERENCE_RATE_YEARS = {2023, 2024, 2025}` | MISO's reference curtailment rate reads three years only | **MISO's lane** | **REPORTED, NOT ACTED ON** (rule 25) |

And one that is **NOT** an instance, examined and cleared: `_SPP_REFERENCE_RATE_YEARS` — §3.

---

## 1. INSTANCE A — a removed rule is still REFUSING SOLVES, in code, by name

`scripts/run_capacity_hindcast.py:364`:

```python
violations = holdout_policy.hindcast_solve_year_violations(_policy_years)
if violations:
    raise SystemExit(
        "rule-22 holdout policy refuses this window:\n  - " + "\n  - ".join(violations)
    )
```

and the check it calls (`scripts/lib/holdout_policy.py`):

```python
for y in sorted({int(y) for y in years}):
    if y in HINDCAST_SOLVE_YEARS:      # = CALIBRATION_YEARS {2023,2024,2025} | {2021}
        continue
    tier = tier_for_year(y)            # train / validation / locked_test
    out.append(f"year {y} is not a hindcast-solvable year (tier: {tier}; ...)")
```

**So the capacity-hindcast harness still hard-refuses 2019, 2020, 2022 and every pre-2021 year,
and the refusal string names rule 22.** CLAUDE.md's rule-22 coda is unambiguous — *"Any year may
now be solved, scored and registered with no authorization, no marker and no one-shot"* — and it
enumerates what was removed: the markers, `holdout-freeze.json`, `--holdout-authorized`, the
`run_calibration_full` year gate, the `dashboard_add_run` marker gate, D-6, the `audit_keepers` M1
check, the CI `quarantine-gates` job. **`run_capacity_hindcast.py`'s gate is not on that list, and
it survived.**

**The module's own docstring asserts it is fine, and the implementation contradicts the
docstring.** `holdout_policy.py` says the hindcast helpers *"are a SEPARATE forecast-program
concern and are untouched by the removal."* But the gate refuses by **`tier_for_year`**, whose
tiers are `[R-HOLDOUT]`'s own three; `VALIDATION_YEARS` and `LOCKED_TEST_YEARS` are introduced in
source as *"Rule 22's validation ladder"* and *"Rule 22's locked test, verbatim"*; and the refusal
message says *"rule-22 holdout policy refuses this window"*. CLAUDE.md permits `tier_for_year` to
survive **as a pure classifier "carrying no authorization meaning"** — here it is the sole operand
of a `SystemExit`, which is authorization meaning and nothing else.

**What it costs, stated as a question rather than an answer.** Whether the forecast program
*should* hindcast 2019/2020/2022 is a programme design call — a bridge year may have perfectly
good independent reasons (data readiness, the T1-FF window construction). **What this finding
establishes is only that the reason now encoded in the code is a deleted rule.** The forecast
program should either re-state the restriction on its own merits or lift it. Not SPP's to decide.

## 2. INSTANCES B–D — the same rule, narrowing measured inputs

* **B** (`runner.py:241`): *"Capacity-hindcast bridge years (plan §1.1): quarantined years
  (rule 22) that a hindcast window spans but must never solve, read data for, or score."* A
  measured year the model is forbidden to read, on a removed rule's authority. A is the gate; B is
  what the gate protects.
* **C** (`emission_rates.py:269`): *"Rule-22 quarantined years a T1-FF full-forward hindcast's
  estimator basis must never touch."* This drops **real measured CEMS rows** from the estimator —
  the closest structural analogue to SPP-67's defect anywhere in the tree. Scoped behind
  `exclude_quarantined`, so every non-T1-FF run is byte-identical and the blast radius is the
  forecast program only.
* **D** (`hydro.py:598`): drops 2022 from the as-of hydro climatology, self-describedly *because*
  of B (*"2022 is the hindcast bridge year — evolved, never solved, its data never read"*). It
  resolves when B does.

All three are **filed as cards, not acted on**: they are forecast-program constructions, this is a
backcast calibration lane, and rule 19 `[R-ONE-MECH]` plus ordinary scope discipline say the lane
that owns the mechanism mints the verdict (rule 28(b)).

## 3. INSTANCE E, AND THE ONE THAT IS **NOT** AN INSTANCE — the distinction matters

**E — `_MISO_REFERENCE_RATE_YEARS = frozenset({2023, 2024, 2025})`** is a confirmed second copy of
SPP-67's exact defect: identical construction, identical freeze, identical stated reason. **It is
MISO's lane's call under rule 25 `[R-ISO-SCOPE]` and is reported here, not acted on** — exactly as
SPP-67 reported it. A successor should check whether MISO's own curtailment table carries rows
outside 2023-2025 before assuming the freeze costs anything.

**NOT an instance: `_SPP_REFERENCE_RATE_YEARS`, SPP's own — examined, and the widening is
correctly REFUSED.** This is the one the sweep was most likely to get wrong, so it is worked
through in full.

SPP-67 armed `vre_reference_rate_year_own`, which reads each year's **own** published rate where
SPP published one. Five of SPP's seven registered years now do. **Two do not** — 2020 and 2021,
which SPP never published — and those two still fall through to a mean frozen over
`{2023, 2024, 2025}`. So the narrowed set *is* still live for SPP.

| basis | years | mean rate | gross-up factor |
|---|---|---:|---:|
| `_SPP_REFERENCE_RATE_YEARS` (in force) | 2023, 2024, 2025 | **9.6501 %** | 1.106808 |
| every year SPP published | 2019, 2022, 2023, 2024, 2025 | **7.9796 %** | 1.086716 |

Published annual rates: 2019 **1.5908 %**, 2022 **9.3568 %**, 2023 **8.4934 %**, 2024 **10.5612 %**,
2025 **9.8958 %**.

**And widening it is still refused — on a reason that is NOT "SPP-67 already said no".** SPP-67
refused the five-year mean under rule 1 `[R-STRUCT]` because it moved every year favourably
(`RESULT-spp-67` §147-149). This sweep adds the structural reason, which is the one that
generalises:

> **SPP-67's repair replaced an estimate with a MEASUREMENT OF THAT VERY YEAR. Widening the mean
> would replace one estimate with a different estimate, for two years that have no measurement at
> all.** Rule 14 `[R-ACCURATE]` governs the first and is silent on the second — it says prefer
> *accurate/measured* data over an estimate, not prefer a wider-window estimate over a narrower
> one.

And the wider mean is not even obviously closer. SPP's curtailment ramps **monotonically**
(137 → 1,260 → 1,097 → 1,483 MW), so 2020's and 2021's true rates lie on the climb between 2019's
1.59 % and 2022's 9.36 % — and **both** candidate means (9.65 % and 7.98 %) sit above that
interval's midpoint. Picking the one that scores better is selecting on the residual; picking the
true interpolant is a free parameter (rule 21 `[R-DOF]`), which SPP-67 also refused. **The honest
statement is that SPP did not publish 2020 or 2021 and the model should not pretend otherwise.**

This is why "a `[R-HOLDOUT]` comment is present" is not itself a finding: **A–D narrow what the
model may READ or SOLVE; SPP's remaining freeze narrows only which estimate stands in where
nothing was ever measured.** Only the first is a rule-14 defect.

---

## 4. WHAT THIS LANE DID AND DID NOT CHANGE

**Changed: nothing.** No code in this finding is edited by lane SPP-68. A is the forecast
program's, B–D are the forecast program's, E is MISO's, and SPP's own is correctly left frozen.
Filed as cards so the owning lanes can act, per rule 28(b) (only the session that tests a
mechanism mints its verdict).

**The one recommendation, and it is about wording rather than behaviour.** `holdout_policy.py`'s
docstring currently tells a reader the hindcast helpers are untouched by the removal, while the
code refuses solves by tier and says "rule-22" while doing it. Whichever way the forecast program
rules on A, that docstring should stop asserting the opposite of what the code does — a future
lane reading it will conclude there is nothing to look at, which is how this survived eleven days.
