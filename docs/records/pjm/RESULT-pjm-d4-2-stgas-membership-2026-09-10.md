# RESULT — PJM reads CALIBRATED: the ST_GAS defect was MEMBERSHIP, and the registry's own criterion closes it

**Session** `pjm-d4-2` · **ISO** PJM · **Date** 2026-09-10 · **Branch** `claude/pjm-d4-2-1xm7l3`
**PRECOMMIT** `docs/PRECOMMIT-pjm-d4-2-stgas-membership-2026-09-10.md` and its 2023-leg
`ADDENDUM`, both committed and pushed **before any shard solved**. Every gate bar, the criterion,
the control posture and the rule-1 non-gates below are quoted from them unchanged.
**Six years solved** (2020-2025), **one LP per rule-32 `[R-SHARD]` container**, all pinned to
`5f133fd595aeb8d6c88058b566fce4b4e8b56e19`; the parent ran no LP.
**Runs** `2026-09-10-pjm-d4-2-stgas` (2023-2025) + `2026-09-10-pjm-d4-2-touchpoint` (2020-2022,
folded to it under rule 30(a)).

---

## 1. RESULT

> **PJM's training span goes `NOT-YET` → `CALIBRATED`, with EXACTLY ONE criterion flip and ZERO
> caveats.** C8 forced-energy share, the single criterion PJM was NOT-YET on, moves **FAIL → PASS**;
> every other scored criterion is **unchanged at PASS**. The caveat budget is untouched (0 ledgered,
> 0 protective) and the determination basis is empty.
>
> **The object is MEMBERSHIP in an existing registry** — `data.outages.ST_GAS_PEAKER_PLANTS`, which
> exists to keep run-when-called steamers out of the reliability min-gen floor and which named six
> ERCOT plants, three CAISO plants and **no PJM plant**, while PJM's plant 3161 runs 1.8 % of hours
> and was floored ~7,885 h a year. **Zero new `ScenarioConfig` fields. Zero free parameters.**
>
> **The qualifying threshold could not have been fitted, and that is demonstrated rather than
> asserted.** It is read off the registry's own revealed membership in the two ISOs that authored it,
> with PJM never consulted; PJM's admitted set is then **invariant across a 17.8-point interval** that
> strictly contains the precedent-admissible window; and the competing pooling window — the one the
> registry's own comment cites — was **tested and falsified**.
>
> **What it does NOT do, said plainly: it does not resolve the holdout-year rubric failures.** On
> 2020-2022 the determination is `NOT-YET` both before and after, **criterion for criterion**. The
> ST_GAS forcing collapses there too, but C8 skips ST_GAS in those years as immaterial, so none of it
> reaches the verdict.

---

## 2. THE CRITERION — declared ex ante, and provably un-sweepable

> A PJM plant is admitted iff the CAMPD **meter-online share of its ST_GAS slice**, pooled over every
> bench year whose own `e_ann / c_ann ≤ 1.1` (the benchmark's own trust test), is **below 35 %**.
> A plant with no trusted bench year is **not** admitted (fail-closed).

**(a) The threshold is the registry's own, measured where it was authored.** Same statistic, same
code path, PJM not consulted:

| ISO | admitted (existing members), pooled duty | excluded | revealed gap |
|---|---|---|---|
| **ERCOT** | 4266 10.3 · 3576 13.3 · 3507 23.1 · 3490 32.2 · 3504 34.1 · **3453 34.7** | **3452 36.9** · 3491 39.4 · 3601 49.9 · 3628 54.1 · 3460 56.0 · 3611 66.8 · 6243 88.9 · 3612 94.5 | **(34.7, 36.9]** |
| **CAISO** | 350 6.6 · 335 11.3 · **315 31.0** | **356 45.1** | **(31.0, 45.1]** |

Both gaps are **empty**: the pre-existing registry is exactly threshold-separable on this statistic
in both authoring ISOs, and every `T ∈ (34.7, 36.9]` reproduces it.

**(b) It carries no leverage (rule 21 `[R-DOF]`).** PJM's own duty distribution has an **empty
interval from 30.8 % to 48.6 %** which strictly *contains* that window. The admitted set is identical
for every threshold across 17.8 points, so no value in it could have been chosen to change an
outcome. It adds **zero** DOF-ledger entries.

**(c) The competing window was falsified by a test it could have passed.** The docstring's CAISO
admission cites *"CAMPD 2024-25"* — a most-recent-two-years window. Under it, ERCOT's admitted set
**overlaps** its excluded set (3504 admitted at 46.3 % vs 3491 excluded at 31.2 %), so **no threshold
on that window reproduces the registry at all**. The two windows disagree about plant 3149, which
carries 1.585 TWh of the 2025 mandate, so this was not a formality.

**Eleven plants admitted:** 50279 (0.0 %), 874 (0.7), 3809 (1.6), 599 (1.6), 3161 (1.8), 3775 (13.2),
1571 (17.1), 384 (18.4), 593 (20.5), 3148 (22.8), 3149 (30.8). **Not admitted:** 3138 (48.6),
3131 (51.0), 1353 (59.8), 3140 (67.6).

**Rule 13 `[R-MEASURED]` forward test.** Peaker-vs-baseload character is a standing attribute of a
steam plant, so the identical census regenerates from any forward CAMPD vintage and re-classifies a
plant whose economics change. It is expressly **not** the `netload_drag_layup_window_mask` route,
which is `_BACKCAST_ONLY_OVERLAY_FIELDS`, has no forward analogue, and was refused by pjm-d4-1 under
rule 17(c) **even though it cleared the gate**.

---

## 3. THE DETERMINATION

### 3a. Training span 2023-2025 — the registered keeper candidate

| criterion | incumbent `2026-09-09-pjm-fuelvintage-ep-level` | **pjm-d4-2 arm** |
|---|---|---|
| **DETERMINATION** | **NOT-YET** | **CALIBRATED** |
| C1 fuel-mix | PASS | PASS |
| C2 system volume | PASS | PASS |
| C3a mean LMP | PASS | PASS |
| C3b price shape | PASS | PASS |
| C3c price tail | PASS | PASS |
| C4 dispatch correlation | PASS | PASS |
| C6 governance | PASS | PASS |
| **C8 forced share** | **FAIL** | **PASS** |
| caveats | — | **0 ledgered, 0 protective** |

**Exactly one criterion moves.** The incumbent's determination basis read *"undocumented
out-of-tolerance (FAIL) criteria: forced_share"*; the arm's is **empty**.

### 3b. Rule 17 leave-one-year-out — the flip is not carried by one year

| years scored | incumbent | **arm** |
|---|---|---|
| 2023 + 2024 | CALIBRATED | **CALIBRATED** |
| 2023 + 2025 | **NOT-YET** | **CALIBRATED** |
| 2024 + 2025 | **NOT-YET** | **CALIBRATED** |

The incumbent reads CALIBRATED only when 2025 is dropped — its failure is entirely 2025-driven. The
arm reads CALIBRATED in all three pairs.

### 3c. C8, all six years

| year | forced TWh C → A | class TWh C → A | **forced share C → A** | 30 % cap |
|---|---|---|---|---|
| 2020 | 5.5111 → 1.3066 | 10.1487 → 8.0950 | **54.3 % → 16.1 %** | under |
| 2021 | 6.5852 → 1.6359 | 10.2941 → 6.3984 | **64.0 % → 25.6 %** | under |
| 2022 | 6.0267 → 1.2555 | 12.9529 → 7.9797 | **46.5 % → 15.7 %** | under |
| 2023 | 4.7652 → 0.8738 | 12.1822 → 10.6250 | **39.1 % → 8.2 %** | under |
| 2024 | 4.4285 → 0.8522 | 12.0927 → 11.5823 | **36.6 % → 7.4 %** | under |
| **2025** | 7.1556 → 1.1072 | 17.3105 → 14.3157 | **41.3 % → 7.7 %** | under |

**C8 passes on the BUDGET, so the provenance escalation is never reached** — which is precisely why
the two plants that keep failing D-4 do not decide it. That was the pre-registered pass route
(PRECOMMIT §5 item 1); the pre-registered failure route (item 2) did not materialise.

---

## 4. D-4 PER-UNIT CONDUCT — and the two plants that survive

Unique convicted plants, strict committed `at_floor` basis:

| year | control | arm | surviving |
|---|---|---|---|
| 2020 | 10 | **3** | 3131, 3138, 3140 |
| 2021 | 8 | **2** | 3131, 3138 |
| 2022 | 8 | **2** | 3131, 3138 |
| 2023 | 6 | **1** | 3138 |
| 2024 | 4 | **2** | 3131, 3138 |
| 2025 | 5 | **2** | 3131, 3138 |

**29 of 41 convictions removed, and the survivors are in every year EXACTLY the non-admitted plants
— the prediction held plant-for-plant across six years with no surprises.** This was pre-registered
before any solve, including which plants would survive.

**3138 (48.6 % duty) and 3131 (51.0 %) remain an OPEN ROOT CAUSE, not a closed one.** Duty alone does
not explain a conviction at ~50 %, and no threshold in the precedent-admissible window reaches them.
They are routed, not absorbed.

---

## 5. EVERY CLASS, SIX YEARS, AT FULL MAGNITUDE — INCLUDING WHAT GOT WORSE

m/a = model ÷ actual; **1.00 is exact**.

| year | ST_GAS C → A | CT_PEAKER C → A | fossil surplus C → A (TWh) |
|---|---|---|---|
| 2020 | 1.74 → **1.29** | 0.98 → **1.00** | +35.208 → **+34.668** |
| 2021 | 3.15 → **1.77** | 0.68 → **0.73** | +26.975 → **+26.363** |
| 2022 | 2.55 → **1.42** | 0.75 → **0.83** | +34.555 → **+33.405** |
| 2023 | 1.52 → **1.23** | 0.89 → **0.91** | +7.991 → **+7.439** |
| 2024 | **1.00 → 0.90 (WORSE)** | 1.01 → **1.02 (worse)** | +0.528 → **+0.378** |
| 2025 | 1.29 → **0.99** | **1.19 → 1.23 (WORSE)** | +19.419 → **+18.658** |

**The three costs, named rather than netted out:**

1. **2024 ST_GAS was exact (1.00) and goes to 0.90.** This is pjm-d4-1 §4's point landing: 2024
   reached the right total *by mandating a third of it*, so removing the mandate necessarily moves it
   off. A residual-driven reading calls this a regression; rule 1 `[R-STRUCT]` calls it the mechanism
   becoming faithful. **Reported as a real cost either way.**
2. **CT_PEAKER moves AWAY from actual in 2024 and 2025** (1.01→1.02, 1.19→1.23), and toward it in
   2020-2023 (0.98→1.00, 0.68→0.73, 0.75→0.83, 0.89→0.91). The pattern is coherent, not random:
   releasing the ST_GAS displacement lets CT_PEAKER run more, which helps where CT was 25-32 % under
   actual and hurts where it was already over. **PRECOMMIT §5 item 5 predicted exactly this for 2025
   and pre-committed to accepting it.**
3. **Part of the released energy lands on classes already over actual** — CC_REGULAR and COAL_BIT
   rise in every year (e.g. 2022: +1.976 and +1.528 TWh). **The error is partly RELOCATED, not
   removed.** What is not in doubt: the **total fossil surplus improves in all six years**, and both
   classes this card is about move toward actual in the years they were furthest away.

---

## 6. THE HOLDOUT SPAN — ZERO CRITERION FLIPS, AND THAT IS THE HONEST ANSWER

| 2020-2022 | incumbent | arm |
|---|---|---|
| determination | NOT-YET | NOT-YET |
| C1 fuel-mix / C3a mean LMP / C3b price shape | FAIL | FAIL |
| C2 / C4 / C6 / C8 | PASS | PASS |
| C3c | CAVEAT (ledgered) | CAVEAT (ledgered) |

**Not one criterion moves.** The holdout-year failures are CC_REGULAR volume (+26.8 to +29.2 TWh),
mean LMP and price shape — **none of them is the ST_GAS forcing defect**. The forcing collapse there
is real (54.3/64.0/46.5 % → 16.1/25.6/15.7 %) but **ungated**: C8 skips ST_GAS in all three years as
immaterial (0.8-1.1 % of ISO load).

pjm-d4-1 §10 already measured why one mechanism was never going to own both: the 2020-22 fossil
surplus is **2-90× larger** than the training years' and its composition is not even stable across
them (2020 carried by COAL +21.25 TWh; 2021/2022 by CC_REGULAR +27.59/+24.84). **ST_GAS is 14-33 % of
it.** Rule 30(c): a held-out year never downgrades PJM, in either direction.

---

## 7. WHAT I ESCALATED RATHER THAN ABSORBED

1. **The blast radius is FOUR consumers, not the two the card assumed.** Beyond the floor, membership
   also drops each admitted plant's **offer curve** (losing the 3.024× ST_GAS peak band — re-pricing
   ~13 % of its capacity from ~$144 to ~$48/MWh at 2025 gas) and its **econ split** (4 tranches → 3).
   **Leg 3 cuts against the card**, and the seam was tested **whole** anyway: scoping the change to
   the floor alone would have kept only the leg that helps, which is the selection rule 1 forbids.
2. **The outage-overlay leg measured 0.000000 and is DEFERRED, not fixed.** The exclusion lives in
   `derive_campd_unit_outages.py`; a solve reads the committed artifact, and rule 23
   `[R-FROZEN-DERIVE]` says a derive re-runs when its **source data** updates. The admitted plants
   keep their existing derates. Declared, not discovered.
3. **`ST_GAS_PEAKER_PLANTS` is solve-affecting but INVISIBLE to `cache_key()`.** It is not in
   `solve_surface.SURFACE_MODULES` and `SOLVE_EPOCHS` is empty, so two runs with identical
   `run_config.json` can now differ. `data/outages.py` imports numpy/pandas and so cannot join the
   stdlib-only surface — a `SolveEpoch` is the available route. **This predates the card** (it has
   been true for ERCOT and CAISO since the registry existed) but this card makes it materially larger
   for PJM. **Routed as a follow-up, not silently fixed mid-flight** — the shards were pinned to a
   commit without it, and adding it would have desynchronised them.
4. **A registration slug collision, caught and fixed.** `--label "…stgas membership A"` and
   `"…stgas membership TP"` both slug to `pjm-d4-2-stgas` (4-word cap), so the second registration
   **overwrote the first** — the exact pjm-97 failure `render_backcast._slug`'s own docstring warns
   about. Caught by re-reading the sidecar rather than trusting the exit code; the touchpoint was
   re-registered as `2026-09-10-pjm-d4-2-touchpoint`.
5. **The materiality denominator comes from the REGISTERED sidecar.** A first diagnostics pass on an
   unregistered composite computed `load_share: None`, which disables the guard and gates every class
   fail-closed — briefly showing a CT_PEAKER "failure" that does not exist. Order is: register, then
   score. Caught by comparing against the control's summary rather than believing the failure list.
6. **CT_PEAKER carries a PRE-EXISTING D-2 breach in 2021/2022** (21.7 %/22.8 % against a 15 % peaker
   cap). **This card does not cause it and slightly improves it** (21.6 %/21.8 %); the scorer reads
   both as *"grounded above budget"* — they clear D-4 and D-1 — so they are a clean PASS.
7. **The 2024 shard finished its LP (1216.6 s) and went idle without pushing.** Recovered by firing a
   push-only prompt into that same session through a bound trigger, rather than spending a second
   25-minute solve.

---

## 8. WHAT IS NOT CLAIMED

- **No year here is a certified out-of-sample number.** `[R-HOLDOUT]` was removed 2026-09-09, so no
  year is protected from being iterated against. These are model-**selection** evidence.
- **Membership is not proven sufficient.** 3138 and 3131 still convict (§4). They do not decide C8
  only because the budget now clears.
- **The holdout-year failures are untouched** (§6), and the PJM hydro deficit (m/a ≈ 0.56) is a
  separate lane this card does not enter.
- **Rule 25 `[R-ISO-SCOPE]`: nothing was transferred.** No ERCOT or CAISO plant code is touched and no
  verdict was carried across. What was taken from them is a **criterion read off their membership**,
  applied to PJM's own meter; every admitted ORIS code was checked and none appears under another ISO.
- **G-CTRL form 4, DECLARED IMPAIRED** (G-DRIFT is not runnable for PJM — three sessions establish
  it). Bands ±0.25 % / ±2.4 % CT_PEAKER, fixed before any solve. **No control solve was spent**
  (rule 29(b)); the committed keeper bundles are the control.

---

## 9. DISPOSITION AND THE RULE-31 `[R-RETAIN]` PROMOTION QUESTION

**Registered (rule 15 `[R-DASHBOARD]`), both of them, in the session that produced them:**
`2026-09-10-pjm-d4-2-stgas` (2023-2025, **CALIBRATED**) and `2026-09-10-pjm-d4-2-touchpoint`
(2020-2022, NOT-YET), the latter **stamped and folded** to the former under rule 30(a).

**Nothing was deleted.** The six per-year shard bundles are on local disk and `.gitignore`d — which
is what discharges rule 29(c) in full, and is not `rm` (rule 31, the ercot-255 incident).

> **THE QUESTION FOR THE OWNER: should `2026-09-10-pjm-d4-2-stgas` be promoted to PJM's keeper,
> replacing `2026-09-09-pjm-fuelvintage-ep-level`?**
>
> The case for: it is the **first PJM run to read CALIBRATED with no caveats**, it flips exactly one
> criterion (the one PJM was blocked on), it regresses no scored criterion, it survives
> leave-one-year-out in all three pairs, and it adds zero free parameters through the registry's own
> existing seam.
>
> The case against, stated so the decision is informed rather than sold: **2024 ST_GAS moves off an
> exact 1.00 to 0.90 and 2025 CT_PEAKER moves further over actual (1.19 → 1.23)**; part of the
> released energy relocates onto CC_REGULAR and COAL_BIT, which were already high; and **two plants
> (3138, 3131) still fail D-4 conduct in nearly every year** — the defect is reduced, not eliminated.
>
> **This container is ephemeral.** The shard bundles do not survive its reclamation, though the two
> composed bundles are committed and the numbers above are all in this document.
