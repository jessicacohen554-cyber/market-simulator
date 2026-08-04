# PRECOMMIT — FFR-3N, attributing the FH-1 §3.3 I12 inversion

**Written and committed BEFORE either solve arm was launched.** Pattern: FFR-3C §3.0.
Branch `claude/fh1-i12-inversion-3njgo4`, off `origin/main` `1bc925eb`.

Nothing here is tuned toward the band. No `ScenarioConfig` default is changed, no damper
unarmed, no band widened, nothing promoted or registered. This is an attribution lane.

---

## 1. The number under attribution

FFR-3F §6 / §10.4: at the FH-1 §3.3 gate posture ERCOT records **40.2 %** reserve margin in
2025 (2024: 32.3 %) against an I12 ceiling of **28.7 %**, while executing **0.000 GW** of
economic retirement in every year and emitting **zero `pipeline_events` of any kind**.

Three candidate causes are named in the charter and none is separated.

## 2. Candidate 3 — band basis. Settled before the solves, no LP (§ reported in the deliverable)

Arithmetic only, from the registries. Recorded here so the solve-based arms are read against
the corrected residual rather than the as-scored one.

## 3. Candidate 1 — the pipeline rule. Pre-registered prediction

**Mechanical claim, established by reading the code before solving:** both retirement rules
consume the *same* `margins` list and apply the *identical* bar
`net_revenue < going_forward_cost` — `retirements.py:1425` (pipeline) and `:2029` (legacy).
They differ only in what happens *after* a unit fails:

* **legacy** — increments a per-fuel consecutive-loss counter; retires when the counter
  reaches `retirement_years_<fuel>` (gas_ct 2, coal/gas_cc 3), with **no execution lag**, so
  an exit lands in the screen year itself.
* **pipeline** — decides at D = 0 on the first failing year, executes at `decided_year + L_f`.

Legacy therefore has **strictly more** in-window execution capability in a 2023–2025 window
than pipeline does. The `decided` event fires on the first failing year under pipeline, so
FFR-3F's observation of zero `pipeline_events` **of any kind** implies zero units failed the
shared bar in any of the three years.

**Pre-registered prediction (falsifiable):**

> **Arm B (`--retirement-rule legacy`) will also execute 0.000 GW of economic retirement in
> every year, and its per-year `reserve_margin` will be identical to Arm A's.**

Read-out rule, fixed in advance:

| outcome | attribution |
|---|---|
| Arm B retires 0.000 GW, RM identical | Candidate 1 **REFUTED** as proximate cause. The under-retirement is not the decision/execution split; it is that **no unit fails the screen at all**. |
| Arm B retires > 0 GW | Candidate 1 **LIVE**. Magnitude bounded by `RM_A − RM_B` per year, reported as the rule's contribution. |

If the prediction fails, the failure is the finding and is reported as such.

## 4. Candidate 2 — the entry side. Pre-registered decomposition

Independently verified before solving: `resolve_reserve_margin_build_enabled(ERCOT) = False`
(the step-6 administrative backstop is OFF for ERCOT and ON for all five other ISOs), so
ERCOT's additions can only arrive through **step 4 (planned, EIA-860 proposed pipeline)** and
**step 5 (economic new entry)**.

Decomposition, from Arm A's `evolution_<year>.json`:

1. Per-year additions by channel and tech — `thermal_additions` carries a `source` field
   (`planned` / `economic`); `renewable_additions` and `storage_additions` **do not**, so the
   planned/economic split for those is reconstructed by calling the planned-additions loader
   directly (no LP, no code change). If that reconstruction is not clean it is reported as a
   non-separation, not guessed.
2. Year-over-year decomposition of the margin into: accredited MW added, accredited MW
   retired (expected 0), and the change in gross peak.

## 5. Arms

Both arms are the FH-1 §3.3 gate posture exactly, differing in **one field**:

```
--iso ERCOT --forward-from-base --vintage 2023 --start-year 2023 --end-year 2025 --arm realized
```

| arm | `--retirement-rule` |
|---|---|
| **A — shipped default** | omitted (inherits `pipeline`, the D-1 flip) |
| **B — legacy control** | `legacy` |

Cache keys are verified **distinct before either arm is read**. Rule 12: years sequential
within each invocation, 2 concurrent invocations, 3 solve-years each.

## 6. What this lane will not do

* Not tune anything toward the band; not widen the I12 band. If the band's basis is wrong
  that is a finding about the invariant's definition, written up, not patched.
* Not declare the FH-4/FH-5 block lifted (Addendum G.2); not pre-empt owner decisions G.5 or D-9.
* Not touch any out-of-training year. The window is 2023–2025 and the holdout freeze is not
  implicated.
