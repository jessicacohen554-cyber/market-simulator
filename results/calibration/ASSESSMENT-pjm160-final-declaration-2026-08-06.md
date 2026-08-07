# ASSESSMENT (pjm-160, task 3): PJM is **still NOT ready** for `final`. Recommend **HOLD** — but the blocker set has changed shape: **two of four are CLOSED, one is NEW, and every survivor is an owner decision, not session work**

**Session:** pjm-160 (task 3 — re-run of the pjm-159 §9 checklist)
**Date:** 2026-08-06
**Branch:** `claude/pjm-bench-regen-f3-closure-bj7q6o`
**Supersedes:** the *status table* of
`ASSESSMENT-pjm159-final-declaration-2026-08-06.md`. That document's analysis
stands and is not re-litigated; this one re-runs its §9 checklist against what
tasks 1 and 2 landed, and adds one blocker it could not have seen.
**Standing:** `final` is an OWNER action. This document **recommends**; it
declares nothing, lifts nothing, and reads no metric as authorization.
**Scope:** zero LP solves; no out-of-training year solved, scored or registered.

---

## §0 — the recommendation

**HOLD.** Not for the same reasons, and the difference matters.

| # | blocker | pjm-159 | **pjm-160** | sufficient alone? | whose call |
|---|---|---|---|---|---|
| **B1** | neither locked-test year is solvable | BLOCKING | **CLOSED for 2019** | — | — |
| **B3** | locked-test C3a on a different statistic | BLOCKING | **CLOSED at the source** | — | — |
| **B2** | the frozen keeper recipe does not reproduce on 2019 | BLOCKING | **STANDS, unchanged** | **YES** | **owner** |
| **B4** | the DA-RT basis flips sign outside training | BLOCKING | **STANDS, sharpened** | **YES** | **owner** |
| **B5** | *(new)* the in-sample `rt_lw` the C3a gate scores against no longer re-derives | — | **NEW** | **NO — ~0.1-0.2 pp; a cheap parity fix to make before the spend, not a reason to hold by itself** | **owner** |
| — | holdout freeze ACTIVE, `final` EMPTY | standing | **unchanged** | **YES** | **owner** |

**Only B2 and B4 are independently disqualifying**, and both are exactly the two
the task brief named as owner decisions rather than session work. B5 is a
pre-spend hygiene item that costs PJM nothing and would be embarrassing to
discover afterwards on a tier that cannot be re-scored.

**The character of the HOLD has changed.** pjm-159's case rested substantially on
a data gap a session could close — and this session closed it. What is left is
three questions no session may answer for itself, plus a freeze the owner
re-affirmed on 2026-08-06. **That is a better position, not a worse one, and it
is the right moment to put the surviving questions to the owner rather than to
keep discovering more of them.**

---

## §1 — B1: CLOSED for 2019 (and the blocker was mis-stated)

`results/calibration/FINDING-pjm160-f3-demand-profile-closure-2026-08-06.md`.

The F3 gap was never the demand **driver**. `load_demand('PJM', 2019)` returns a
full `(8, 8760)` array today, and so does every other ISO for 2019 and 2020 —
PJM's per-BA EIA-930 extract covers 2018-2026 and the demand-profiles parquet
has been only a fallback since every ISO gained an adapter. The raise came from
`load_demand_**meta**`, one function away, which falls through to the legacy
`eia_demand_meta.parquet` summary. Closed at the curation seam
(`curate_demand_profile.curate_pre_window`, 12 partitions, six ISOs × 2019-2020).

```
calibration_reference.json isos.PJM : [2019, 2021, 2022, 2023, 2024, 2025]
PJM_<y>_renewable_capacity.csv      : [2019, 2021, 2022, 2023, 2024, 2025]
load_demand + _meta('PJM', 2019)    : OK
_pjm159_final_readiness.py          : 2019: SOLVABLE     (was BLOCKED)
```

**Two things this does NOT mean.** (a) It is not authorization: rule 22's whole
point is that preparing an input and spending the year are different acts, and
*"no session lifts the freeze by inference from a passing metric."* (b)
**H1-2026 is unchanged** — still blocked by construction (a partial year cannot
satisfy the 8760 demand contract; CAMPD Q2-2026 and EIA gas May-2026+ unposted).
Since `final` as written grants **both** locked years, the owner may want to
grant 2019 alone rather than issue a two-year grant of which one year is
structurally unspendable.

**A residual step, now smaller than pjm-159 §9 item 4 thought.** The
`pjm-da-virtuals` corpus the keeper's armed layer requires is **gitignored**, so
it must be fetched in whatever container runs *any* PJM solve — including
2023-2025. It is a runtime step, not a data-readiness gap, and the owner's
2026-08-06 clarification (*"data intake needs NO per-ISO/per-window
authorization"*) removes the authorization question the assessment raised. This
session fetched 2023-2025 (in-sample, unrestricted) to run the D-2 half of task 1.

---

## §2 — B3: CLOSED at the source

`actual_lmp.json` PJM 2019 now carries `rt_lw 26.54 / da_lw 26.56` against the
legacy equal-hour `rt 25.44 / da 25.54`. So a 2019 bench part will render with
the load-weighted basis and its C3a will be scored on the same **statistic** as
every in-sample number. That was B3's entire demand — and see B5 for the part of
it that is *not* closed.

---

## §3 — B2: STANDS, unchanged, and it is an owner decision

Nothing in this session bears on it, and the readiness probe re-confirms every
element at HEAD:

```
keeper armed flags        : pjm_seam_measured_ladder, measured_ramp_capability,
                            measured_ct_heat_rates, pjm_da_virtual_bids  (all True)
PJM_SEAM_LADDER_BY_YEAR   : [2023, 2024, 2025]
ladder gated on `year in` : True
rule-19 firm-export floor : FIRES  <- a DIFFERENT mechanism outside the ladder years
ramp_capability POOLED    : [2023, 2024, 2025]
measured_ct_heat_rates    : ['2023-2024-2025']
```

> **CORRECTED BY §11.2 — read that first.** The probe's `rule-19 firm-export
> floor: FIRES` line is a **source-text check that the branch exists**, not a
> year-aware test, and the floor has no entry outside 2023-2025 either. What
> actually runs on 2019/2021/2022 is the **forecast track** — the gas-elastic
> reference-price formula — not the rule-19 alternative. §3's conclusion (a
> touchpoint or locked year does not run the keeper's own seam representation)
> stands; its mechanism attribution does not.

The decision is pjm-159 §9 item 3 verbatim and I do not improve on it: either
(a) derive `PJM_SEAM_LADDER_BY_YEAR[2019]` from the 2019 tie file with the frozen
formula — rule 23 permits re-derivation when the *source data extends*, which is
exactly this case, and the 2019 tie file is already landed EQUIVALENT at 192,708
rows — or (b) declare explicitly that the locked test runs the rule-19
alternative on 2019 and record that in the declaration. **Silence remains the one
unacceptable option**, because it would certify "the frozen keeper config" on a
year where a load-bearing armed mechanism silently swaps for another.

---

## §4 — B4: STANDS, and this session **sharpened** it rather than softening it

pjm-159 sized the regime flip on the equal-hour spread. The C3a gate uses the
**load-weighted** basis, which 2019 now carries:

| year | DA−RT | **DA−RT load-weighted** | tier |
|---|---:|---:|---|
| **2019** | +0.10 | **+0.02** | **LOCKED TEST** |
| 2020 | −0.25 | −0.29 | outside grant |
| 2022 | −1.49 | — | validation (spent) |
| 2023 | +0.89 | **+0.96** | train |
| 2024 | +0.25 | **+0.29** | train |
| 2025 | +0.82 | **+0.78** | train |

**On the gate's own basis, 2019's spread is +0.02 — an order of magnitude below
the smallest training year, and effectively zero.** The `pjm_da_virtual_bids`
layer's C1 contribution is `≈ −(DA−RT) × dNet/dλ × 8760`, so on 2019 the basis
term all but vanishes and the model's own price error stands uncancelled. The
in-sample near-cancellation pjm-158 identified is confirmed to be a property of
the 2023-2025 regime, not of the mechanism.

**Closing B1 and B3 therefore does not weaken B4 — it measures it more
precisely, and it points the same way.** pjm-159 §5's disposition is unchanged
and is the owner's: either the architecture question is resolved (pjm-159 task B
closed it as a **measured, closed representation boundary** with a falsification
bar, so "resolved" here can only mean the no-MIP mandate changes), **or** the
declaration records the regime dependence as a stated limitation of the
certified number.

---

## §5 — B5 (NEW): the in-sample `rt_lw` the C3a gate scores against no longer re-derives

**This is the one blocker pjm-159 could not have seen, and it is the direct
result of its own §9 item 2** — *"verify the committed 2023-2025 rows re-derive
byte-identically."* **They do not.**

| PJM | committed `rt_lw` | re-derived at HEAD | Δ |
|---|---:|---:|---:|
| 2023 | 29.55 | **29.58** | +0.03 |
| 2024 | 31.31 | **31.36** | +0.05 |
| 2025 | 45.80 | **45.89** | +0.09 |

NYISO and NEISO reproduce **exactly**; ERCOT's difference is an environment
artifact (its `ERCOT_Native_Load_*.xlsx` zonal files are absent in this
container). PJM's is structural: `_lw_fields` weights by `load_demand`, and
PJM's `load_demand` switched from the legacy demand-profiles series to the per-BA
extract and gained the dropout/spike screens **after** those rows were derived.
The committed values are on the **old weight basis**.

**Why it belongs on the pre-spend list — and why it is NOT independently
disqualifying.** The 2019 `rt_lw` this
session built (26.54) is on the **current** weight basis; the training years'
committed `rt_lw` are on the **old** one. A locked-test C3a would therefore be
compared — in the declaration, in any table, in every later citation — against
in-sample numbers computed with a different weighting. That is the same *class*
of non-parity B3 was about, one level deeper: B3 asked whether the locked year
used the same **statistic**; B5 asks whether it uses the same **vintage of that
statistic**. On an iterable tier this is a footnote. On a touch-once tier it
cannot be re-scored once spent — but the effect is **0.1-0.2 pp on a ±10 % band**,
so it is a defect to close cheaply *before* the spend, **not a reason to hold on
its own**. Stated plainly so it is not read as heavier than it is.

**Deliberately not fixed here, and the reason is that it is a gate input.**
`calibration_verdict.score_price_mean` reads `rt_lw` off the **bench part**,
which re-renders from `actual_lmp.json` on the next registration — so refreshing
the file would silently move C3a for **six ISOs** at whatever moment each next
registered. `actual_lmp.json` was restored to its committed bytes and the
retrofit re-run for 2019/2020 only (verified: lw fields *added* to ERCOT and PJM
2019-2020, zero existing fields changed).

**Sizing it for the decision — for PJM the fix is free.** Against the keeper's
model levels (31.43 / 31.18 / 42.35), C3a moves from **+6.36 / −0.42 / −7.53 %**
to **+6.25 / −0.57 / −7.71 %**: every year stays comfortably inside ±10 % and no
verdict changes. The cost is not PJM's; it is that the same refresh touches five
other ISOs whose margins this session has not measured. **Recommended disposition:
refresh `rt_lw` cross-ISO in a session that can own all six lanes' C3a, before
any locked test is spent anywhere** — not as a PJM side effect.

---

## §6 — what task 1 changed, and what it says about readiness

The pjm-159 bench nameplate fix now sits in PJM's committed bench parts
(`FINDING-pjm160-bench-nameplate-blast-radius-2026-08-06.md`). **3 of 26 D-1 rows
moved, all in the improving direction, no gate flipped, and the keeper
re-verifies CALIBRATED with zero fails and zero caveats.** `audit_keepers.py
--iso PJM` remains **0 failures, 0 warnings**.

Two readings matter here.

**For the HOLD:** this is *not* another "material finding at a high discovery
rate" of the kind pjm-159 §8 counted against readiness. It is a known defect,
fixed, measured, and bounded — its D-1 movement is ≤0.004 and fully attributed to
the plants repaired. It argues mildly **for** readiness.

**Against:** the same fix revealed the defect is **two-sided** — the model half of
the payload is encoded through the same nameplate and stays saturated until PJM
next registers a solve. It costs nothing in-sample (measured), but a locked-test
run would render both halves correctly for the first time, so its D-1 rows would
not be strictly comparable to the keeper's committed ones. Worth one sentence in
any declaration; not a blocker.

---

## §7 — the pjm-159 §9 checklist, re-run

| § 9 item | status |
|---|---|
| 1. Close the F3 demand-profile gap for 2019 | **DONE** — B1 closed; the blocker was `load_demand_meta`, not `load_demand` |
| 2. Build PJM 2019 `rt_lw`/`da_lw`; verify 2023-2025 re-derive byte-identically | **HALF DONE** — 2019 built (B3 closed); **the verification FAILED** → B5 |
| 3. Resolve the year-keyed-recipe question (B2) | **OPEN — owner** |
| 4. Authorize the `pjm-da-virtuals` 2019 intake | **DISSOLVED** — intake needs no authorization (owner 2026-08-06); the corpus is gitignored, so fetching it is a runtime step for *any* PJM solve |
| 5. Dispose of B4 | **OPEN — owner.** pjm-159 task B closed the architecture question as a measured boundary, so only the "record it as a stated limitation" branch remains open |
| 6. Lift the freeze for PJM | **OPEN — owner.** ACTIVE, re-armed 2026-08-06; the owner declined the charter's own recommendation to lift fully that same day |
| — | **NEW: 7. dispose of B5** (§5) — **owner**, cross-ISO |
| 8. Then declare `final` and spend once | **NOT YET** |

---

## §8 — the recommendation, stated for the owner

**Do not declare `final` today.** But the question in front of the owner is now
small and well-posed, which it was not yesterday:

1. **B2** — for 2019, derive the seam ladder from the 2019 tie file, or declare
   that the rule-19 alternative runs and record it? *(Either is defensible;
   silence is not.)*
2. **B4** — spend with the DA−RT regime dependence recorded as a stated
   limitation of the certified number, or wait? *(The architecture route is
   closed by measurement; this is now purely a disclosure choice.)*
3. **B5** — refresh `rt_lw` cross-ISO first, so the locked-test C3a and the
   in-sample C3a share a weight vintage? *(For PJM the refresh is free; the cost
   is five other lanes' unmeasured margins.)*
4. **The freeze** — and whether `final` should grant 2019 alone rather than both
   locked years, given H1-2026 is unspendable by construction.

**Answer 1-3 and lift, and PJM is spendable.** No further session work is
required to make it so — that is the substantive change this session produces,
and it is the reason the HOLD is now a decision point rather than a backlog.

---

## §9 — governance

- **Rule 22.** Freeze respected absolutely: ACTIVE, read, not touched, not
  interpreted as lifted. `final` EMPTY. No out-of-training year solved, scored or
  registered. The 2019/2020 numbers here are reads of **measured** artifacts
  (committed bench, `actual_lmp.json`, the per-BA extract) with **no model output
  on either side** — the class of read pjm-157/158/159 performed, and the reason
  they are here is to size a governance risk *without* spending the year. Data
  preparation is not a grant and a passing readiness check is not authorization.
- **Rule 14 `[R-ACCURATE]`.** Two defects surfaced this session (PJM 2020's
  `peak_mw` artifact; the `rt_lw` non-reproducibility). Neither is buried and
  neither is silently landed: one has its year withheld from the reference with
  its root cause named, the other is restored and escalated as B5.
- **Rule 16 / rule 12.** No bundle registered, no solve run.
- **Rule 15.** No run produced, so nothing is owed to either dashboard; the
  changed bench parts ship with their finding.
- **Rule 25 / rule 28.** No mechanism proposed or tested; PJM's lever queue is
  untouched and still clear, and no matrix cell moves.
- **Rule 27 `[R-PUSH]`.** Opus. No existing source file ≥300 lines rewritten from
  regenerated content; every push verified blob-identical to local.
- **Keeper UNCHANGED** at `2026-08-04-pjm-152-collapse`; no marker re-keyed.
- **`final` is not declared and cannot be by this session.**

**Next shorthand: pjm-161.**

---

## §10 — ADDENDUM: the owner's answers, a correction to B2, and the new sequencing (2026-08-06, same session)

### §10.1 — the four decisions, as answered

| # | question | answer | vs recommendation |
|---|---|---|---|
| **B2** | seam mechanism outside 2023–2025 | **Derive the ladder** | as recommended |
| **B4** | DA−RT regime dependence | **Wait for the price lane** | **against** — recorded as decided |
| **B5** | `rt_lw` weight vintage | **Refresh cross-ISO first** | as recommended |
| **Freeze** | lift for PJM, at what scope | **Hold** | **against** — recorded as decided |

**Net: `final` stays undeclared, the freeze stays ACTIVE on its 2026-07-25 basis, and no
year is spent.** `holdout-freeze.json` is untouched — "hold" is the status quo, so there
is nothing to write. Two prep workstreams are authorized (§10.4 step 0), and prep is
explicitly unrestricted: what is held out is the score, never the data or the config.

### §10.2 — CORRECTION: B2 is worse than §3.1 stated, and pjm-160 propagated the error

**pjm-159 §3.1 wrote** that outside the ladder years *"the ladder no-ops AND
`inject_reference_price_firm_export` fires — the firm scheduled-export floor that the
ladder displaces under rule 19"*, and concluded the 2019 run *"would be the keeper's
**rule-19 alternative**"*. **The second half is wrong**, and this assessment's §0/§3
repeated it.

`inject_reference_price_firm_export` applies a floor only *"for each neighbor carrying a
`firm_export_floor_by_year` entry for `year`"* and returns `False` — byte-identical, nothing
applied — otherwise. Both PJM neighbour specs (`spec.py:903, 915`) carry
`firm_export_floor_by_year={2023: …, 2024: …, 2025: …}` and nothing else. The gate site's
own comment states the consequence outright:

> *"Forecast years have no ladder entry AND no floor entry, so both paths no-op
> identically there."*

**So outside 2023–2025 the keeper's seam runs with NEITHER mechanism** — not with an
alternative — leaving only the bare economic tranches. That is a stronger form of B2, not a
weaker one: the question is not *which* seam representation the locked year gets, it is that
the keeper's entire measured seam pricing is **absent**.

**How the error survived three sessions:** `_pjm159_final_readiness.py::check_recipe_reproducibility`
reports `rule-19 firm scheduled-export floor fires: True` from
`alternative = "if not _pjm_ladder_active and inject_reference_price_firm_export" in nodes`
— a **source-text check that the branch exists**, not a test that a floor applies in any
year. It was read as the latter. (The probe is not edited here; the correction is recorded
and the probe line should be re-worded or made year-aware by whoever next touches it.)

### §10.3 — the correction reaches BACKWARD: the spent 2022 touchpoint ran with no seam pricing

`results/calibration/pjm2022_touchpoint/run_config.json` carries
`pjm_seam_measured_ladder: true`, and `2022 ∉ PJM_SEAM_LADDER_BY_YEAR`. By §10.2 the floor
has no 2022 entry either. **So `2026-08-05-pjm-2022-touchpoint` was solved with PJM's
measured seam pricing entirely absent** — in the channel carrying the keeper's largest
single-signed volume error (net export −9.57 / −9.17 / −5.40 TWh in-sample, one-signed
under-export in all three years).

Its determination is **NOT-YET on exactly two criteria: C1** (driven by `CC_REGULAR`
+18.28 TWh, per pjm-159 §1) **and C3b** (NRMSE 0.206). **Net-export error lands in
`CC_REGULAR` volume.**

**This is a hypothesis, not a finding.** Nothing here re-scores 2022 — every number above is
a read of a committed artifact (the bundle's `run_config.json`, the registry sidecar, the
pjm-159 record), with no model output produced. But it is a *testable* hypothesis, and
deriving the 2022 ladder is the direct test of it. It also means the 2022 result should not
be read as evidence about the keeper's seam representation, because that representation was
not in the run.

**Consequence for the B2 work you authorized: extend its scope to 2019, 2021 AND 2022** —
the same frozen formula, wherever the tie file exists. Derived only for 2019, it serves a
year that is now four steps away; derived for 2022 it tests the step that is next.

### §10.4 — the sequencing (owner directive, 2026-08-06)

> *"After 2022 passes we will run a 2022-2035 forecast test on the keeper formula before
> testing any further holdout years and then 2021 will be the next touchpoint testing year."*

| step | what | gate |
|---|---|---|
| **0** | Derive `PJM_SEAM_LADDER_BY_YEAR` for 2019/2021/2022; cross-ISO `rt_lw` refresh | **none** — prep, no solve/score/registration. Rule 23 covers the derive: the *source data extends* |
| **1** | **2022 passes** — touchpoint loop (run → diagnose → re-train on 2023–2025 → re-test) | **BLOCKED by the held freeze** — see §10.5 |
| **2** | **2022–2035 forecast test** on the keeper formula | running it is **unrestricted** (forecast mode uses no measured overlays); registers on the **separate** forecast dashboard via `scripts/register_forecast_run.py`, **never** the backcast registry (rule 15). Scoring its 2022 leg against measured 2022 actuals is still a holdout score and stays gated |
| **3** | **2021 touchpoint** | validation tier — needs a lift, same pattern as 2022. Its inputs are prepared: the pre-window demand partition landed this session |
| **4** | **2019** — the one-touch year | `final` marker (EMPTY) **and** the freeze. *(2020, if ever wanted, additionally needs the PJM peak-artifact fix — F3 finding §2.1)* |

This reordering is **coherent with B4 = wait**: the locked year moves far enough out that
waiting costs nothing near-term. It also **raises B5's priority** rather than lowering it —
2022 and 2021 are scored on `rt_lw` too, so the weight vintage should be settled before
either is re-run, not after.

### §10.5 — the one scheduling conflict, stated plainly

**Step 1 cannot start under the answer given to the freeze.** "After 2022 passes" presumes
2022 can be solved and scored; `holdout-freeze.json`'s `frozen_operations` are exactly
`solve` / `score` / `dashboard registration`, for every out-of-training year including the
validation tier.

The established remedy is a **narrow 2022-only lift with a same-session re-arm** — used
twice already (2026-08-05, PJM + NEISO; 2026-08-06, NEISO on the corrected gas basis). It
leaves 2021, 2020, 2019 and H1-2026 fully protected, and it is the disposition the
validation tier exists for: 2022 is *iterable* by design, re-spendable, and never a
certified out-of-sample number.

**Not requested and not taken here.** The freeze answer recorded in §10.1 is HOLD, and it
stands until the owner says otherwise. This section records the conflict so the sequence is
not started against a gate that will refuse it.

### §10.6 — B4's exit condition, still unnamed

"Wait" needs something to wait for. The architecture route is closed by measurement
(pjm-159 task B: adj R² 0.038 / 0.047 / 0.054 against a 0.25 bar, plus the no-MIP mandate),
and PJM's price lane is at an owner-declared frontier whose known trajectory moves this
mechanism *against* the number. Three candidates: the no-MIP mandate changes; a proposal
clears the 0.25 falsification bar (FINDING-pjm159 §4); or **the step-2 forecast test supplies
the evidence**. The third is plausible and would fold B4 into the sequence instead of leaving
it open-ended — worth naming now rather than rediscovering at step 4.

**Next shorthand: pjm-161.**

---

## §11 — Is the seam ladder forecastable? **No — and that is by design, as a two-track mechanism.** (Owner question, 2026-08-06)

### §11.1 — the answer, from the code

`inject_pjm_seam_ladder_prices` states it in its own docstring:

> *"Returns `True` when at least one band row was repriced, `False` when `iso`/`year`
> has no ladder entry … (byte-identical no-op — **forecast years fall through to the
> gas-elastic reference-price formula, the `hr_by_year` two-track design**)."*

So PJM's seam is priced by **one of two mechanisms**, selected by year:

| track | years | what prices the seam bands | forecastable? |
|---|---|---|---|
| **measured ladder** | **2023–2025 only** | Q-Q duration coupling of PJM's settlement-grade tie-line flows against the measured DA system LMP (`derive_pjm_seam_ladders.py`) | **NO** — it needs that year's *realized* flows and that year's *realized* prices. There is no forward construction. |
| **gas-elastic reference price** | every other year, backcast **and** forecast | the hurdle-gated `gas × heat-rate × load-shape` reference-price formula | **YES** — its drivers are gas price, heat rate and load, all forward quantities that respond to changed conditions |

Under rule 13's own test — *"could this same quantity be produced for a forward year from
forward drivers, and would it respond to changed conditions?"* — the **measured ladder
fails and the fallback passes.** That is exactly why the repo built it as two tracks rather
than one, and why `PJM_SEAM_LADDER_BY_YEAR`'s preamble says *"backcast years below only."*

### §11.2 — CORRECTION to §10.2: "neither mechanism" was too strong

§10.2 concluded that outside 2023–2025 the keeper's seam runs with *"NEITHER mechanism …
leaving only the bare economic tranches."* **The first half is right and the second is
wrong.** What is absent outside the ladder years is the **measured ladder** and the
**firm-export floor** — but the seam's reference-price bands are still priced, by the
gas-elastic formula. `_inject_seam_ladder` *overwrites* the band `mc`; returning `False`
leaves the reference-price formula's values in place, it does not zero them.

So the accurate statement is: **outside 2023–2025 PJM's seam runs the FORECAST track.**
That is a defined, forecastable mechanism — not a void. §10.2's substance survives (a
locked-test or touchpoint year does **not** run the keeper's own seam representation) but
its severity was overstated, and the 2022 hypothesis in §10.3 should be read as *"ran the
forecast-track seam"*, not *"ran with no seam pricing."*

### §11.3 — what this means for the decisions already taken

**B4 (owner answer: the 2022–2035 forecast test decides it).** The test will run on the
**gas-elastic track**, because forecast years have no ladder entry by construction. So it
will characterise the seam representation the *forecast* actually uses — which is precisely
what a forecast test should do — but it will **not** validate the measured ladder, and it
cannot. Worth stating in the test's own charter so nobody later reads a clean forecast
result as evidence for the backcast mechanism.

**The larger point, which is the strongest argument for the owner's sequencing.** The keeper
is calibrated *with* the measured ladder; the forecast runs *without* it. That is a genuine
backcast→forecast representation gap sitting in PJM's largest single-signed volume channel —
exactly the class of thing rule 22's crossover window exists to measure. Running a
forecast test before spending further holdout years is therefore well-aimed, and this is a
concrete object for it to measure rather than a general readiness check.

**The 2022 question now has two defensible answers, not one.** Deriving a 2022 ladder is
legitimate (rule 23: the source data extends — the 2022 tie file and 2022 DA LMP both
exist) and would make the touchpoint test *the keeper's own model*. But it would also make
2022 test a mechanism **the forecast does not use**. Those are different questions:

- *"Does the keeper reproduce 2022?"* → derive the 2022 ladder first.
- *"Does the thing we will actually forecast with reproduce 2022?"* → leave 2022 on the
  forecast track, and read its C1/C3b miss as information about the **forecast** seam.

The second reading makes the existing, already-spent 2022 result more valuable than §10.3
implied: it is a measurement of the forecast-track seam against a real year. **Not
adjudicated here** — it is an owner choice, and it is the open item this session ends on.

**Next shorthand: pjm-161.**
