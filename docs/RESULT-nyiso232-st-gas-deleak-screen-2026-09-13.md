# RESULT — nyiso-232: the ST_GAS econ bands **do** carry ERCOT's de-leaked 1.21, the de-leak is built and screened, and the screen **STOPS** on the gate the PRECOMMIT said it would

**Session** nyiso-232 · **ISO** NYISO · **Date** 2026-09-13 · **DATA PROFILE: nyiso**
**Pre-registration** `results/calibration/PRECOMMIT-nyiso232-st-gas-deleak.md`, pushed at
`77b47576` **before** the arm was launched; gate scorer
`scripts/probes/_nyiso232_screen_gates.py` committed at `4b2586da`, **before** the arm's numbers
existed. **Keeper `2026-09-13-nyiso231-anchor-span` UNCHANGED.**
**Rule 32 `[R-SHARD]` (a): the parent ran ZERO LP.**

---

## 1. HEADLINE

| | |
|---|---|
| **The defect** | **CONFIRMED at zero LP.** `_NYISO_OFFER_CURVE`'s ST_GAS econ bands carry ERCOT's rule-25-removed 1.21 **multiplicatively**. |
| **The screen** | **STOPS.** Four of five pre-registered gates PASS; **G-NONTARGET stops it**: C3a-2022 **−9.86 % → −11.61 %**, PASS → FAIL against ±10 %. |
| **Promotion** | **NOT promoted.** A screen may kill an arm; it may never promote one. The gate is not re-cut. |
| **Cost** | one 5m23s shard. No control solve (G-DRIFT all-INERT, §5). No span. |
| **Retrievability** | bundle **pushed**, 17 files incl. `dispatch/2022_P1.parquet`; `git checkout 451fa7f32ffacacbc85083aa30873842d06a19de -- results/calibration/nyiso232_arm_y2022`. A promotion costs **zero** re-solves for 2022. |

## 2. THE DEFECT — and the two questions the handoff made gating, both settled at zero LP

**It is a PROPAGATION MISS, not a rule 23 `[R-FROZEN-DERIVE]` re-derivation.** The ST_GAS source
data (`nyiso_campd_marginal_hr_summary.csv` p50s, n = 25) is untouched and the `phys_*` keys keep it
verbatim; what moves is a *borrowed multiplier on top of it*. Rule 23's trigger — "never because a
residual moved" — is not engaged: no residual moved, and the change pushes price the **wrong** way.
What it is instead is an **incomplete rule 25 `[R-ISO-SCOPE]` enforcement**: the de-leak removed
1.21 from the cell where it was *written* (`CC_REGULAR.econ_high`) and left it standing in the cell
where it had been *multiplied in*. Rule 26 `[R-DELETE]`, one derivation step removed.

**Of the block's two identifications, the CONSTRUCTION is load-bearing and the OUTCOME-based one
cannot rescue it.** The block's own words are *"validating the level a priori, **not**
residual-fitted"* — corroboration of a construction fixed beforehand. Promoting a corroboration to
*the* identification once the construction fails inverts the epistemics, is rule 13 `[R-MEASURED]`'s
forbidden move (an outcome fed back to select an input), and fails rule 13's forward test outright
(a forecast year has no measured volume to match).

**Correcting the handoff's precision.** It states the registered 1.08 matches the cited construction
"to 0.2 %". That is not any of the readings — the file records **two different** native-steam
triples, giving **0.531 % / 0.288 % / 0.075 %** (0.830 / 0.828 / 0.825 × 1.30811). All within 1 %,
which is what identifies the construction; on the **current** reach (1.00/0.925) the same
construction gives **0.8973**, **16.9 %** away, so the registered band is not reproducible from the
file's own inputs today.

## 3. THE CONSTRUCTION BUILT — narrower than the handoff proposed, and measurement is why

`ST_GAS.econ_low := 1.0`, `ST_GAS.econ_high := 1.0`, gated behind
`nyiso_st_gas_econ_bands_deleaked` (default off, NYISO-only, hard error off-ISO and hard error
without its `phys_*` basis, kwarg-**or**-field with a fail-loud `run_year` guard for the
`prb_overrides` no-op seam). **ZERO new literals, ZERO free parameters, no DOF entry** — 1.0 is the
neutral rules 24/25 prescribe, and it is the **identical remedy this file applied in this same
audit** to `CC_REGULAR.econ_high` and `CT_PEAKER`'s econ bands.

**The handoff's arithmetic was refused**: propagating the *current* reach uses CC `econ_high` 1.00,
which the de-leak declares a **neutrality placeholder**, not a measurement — that dresses a
placeholder as a derivation and invents three new literals where the chartered remedy invents none.

**`committed` was excluded because the probe caught it, not because it was assumed.** Its markup
clips to 0 in both legs, so at markup 0 the multiplier only scales **fuel** — moving it to 1.0 would
price the steam min-load block **9.4 % below its own measured burn** (measured **−$4.09/MWh**,
2022). `peak` 4.20 excluded as the $-cap scarcity wall. Both exclusions match nyiso-199's.

## 4. PHASE 0 — exact, zero LP, four years

Non-ST_GAS offer max\|Δ\| **$0.0000000000/MWh** over 665–671 matched rows; non-ST_GAS `pmax`
max\|Δ\| **0.0**; ST_GAS `pmax` total **8902.4000 → 8902.4000 MW**; `committed` and `peak` bands
byte-identical. Econ offer **−$8.61 / −$3.17 / −$2.80 / −$5.41** per MWh (2022/23/24/25),
year-varying because `gas_offer_net_revenue_margin` prices the removed markup at the solve year's
own zonal anchor. The real field reproduces the probe's arm array to **max\|Δ\| 0.000000000000**.

**Declared before the solve, not discovered:** the flat econ ramp collapses the 6-slice
`econc00..05` smoothing ladder to `econlo`/`econhi` — **ST_GAS 88 → 44 LP rows**. Predicted at zero
LP; the solved arm reads **exactly 44** (gate G-ROWS).

**Screen year 2022, named in the PRECOMMIT on FOOTPRINT** (|Δ econ offer| × ST_GAS econ energy =
**38.1** / 20.1 / 16.0 / 31.2), never on the residual.

## 5. G-DRIFT — recorded before the arm, so form 4 held and no control solve was spent

Six changed paths since the keeper's `0acedb7e`, **all INERT for NYISO**: three files from
`760012f7` (an EIA-860 cache-**keying** repair reachable only under
`eia860_vintage_tracks_solve_year`, which the keeper records **`False`** — verified on the keeper's
own `run_config.json`, not on the commit message); `actual_lmp.json` (benchmark, **0** of +640 added
lines contain "NYISO"); two MISO benchmark parquets. **Corroborated empirically**: re-scoring the
committed keeper at this HEAD reproduces the nyiso-231 log exactly (C3a-2022 −9.9 %, C1-2022
`CC_REGULAR` +5.20 TWh, C3b 0.209).

## 6. THE GATES

| gate | verdict | measured |
|---|---|---|
| **G-CONFINE** | **PASS** | worst non-ST_GAS class move **CT_PEAKER −0.416 TWh** against a 0.763 TWh budget |
| **G-DEMAND** | **PASS** | served **152.68167 → 152.68167 TWh**, Δ **0.0**; dump **0.0**; slack **0.0** |
| **G-MAGNITUDE** | **PASS** | ST_GAS **6.6384 → 7.3090 TWh**, **+0.6706**, inside the pre-solve ceiling **1.574** |
| **G-ROWS** | **PASS** | **44** rows, bands `committed/econlo/econhi/peak` — the predicted collapse |
| **G-NONTARGET** | **STOP** | **C3a-2022 −9.86 % → −11.61 %, PASS → FAIL** |

**The arm is not promoted.** I wrote the gate; it stopped the arm; I am not overriding it.

**What the arm did on the merits, reported in full because it is the case FOR it.** Load-weighted
price **$73.1275 → $71.7079**, a cost of **$1.42/MWh (−1.94 %)** — materially smaller than the
PRECOMMIT's own worry. Class moves, against the scorer's 2022 actuals:

| class | control | arm | vs actual | |
|---|---:|---:|---:|---|
| **ST_GAS** | 6.551 | **7.222** | −1.148 → **−0.477 TWh** | **58 % of the gap closed** |
| **CC_REGULAR** (the failing C1 cell) | 36.782 | **36.624** | +5.196 → **+5.038 TWh**, share 3.93 → **3.83 pp** | improves, still FAIL |
| CT_PEAKER | 2.764 | 2.348 | +0.077 → −0.339 TWh | **worse**, well in band |
| CC_CHP | 13.958 | 13.875 | −0.225 → −0.308 TWh | **worse**, well in band |
| C2 gas family | 61.65 | 61.62 | **−0.029 TWh** | conserved; PASS → PASS |

So: the target class and the failing cell both improve, two smaller classes degrade modestly inside
band, the gas family total is conserved, and the whole cost lands on C3a. C3b-2022 (0.209) and
C1-2022 `CC_REGULAR` were already FAILING and cannot flip; C3c-2022 is an auto-ledgered caveat on an
out-of-training year (rubric v3.6) and is not a gate.

*(Method note, stated because it is a limitation: a screen bundle is unregistered, so
`calibration_verdict.py` cannot read it. G-NONTARGET was scored by applying the arm's **exact**
model-side deltas to the scorer's **own** control values, with the actuals, bands and tiers
unchanged. The model deltas are exact; nothing on the actual side was recomputed.)*

## 7. AN UNRESOLVED FLAG I AM NOT RESOLVING IN MY OWN FAVOUR — D-2 / C8

The arm's `legitimacy_diagnostics.json` reads **`D2.passed: false`**, one failure:
*"2022 ST_GAS: forced share 33.6 % > 30 % (1.92 of 5.70 TWh at binding non-exempt floors)"*.
C8 is **PROTECTIVE** tier — a harder stop than C3a. It was **not** among my pre-registered gates
(G-NONTARGET covers load-bearing criteria only), and **that is a gap in my gate set, stated as such
rather than used as an exemption.**

**What is measured, and what is not.** The flip is driven **entirely by the denominator**: forced
energy moves **1.9803 → 1.9187 TWh (−3 %)** while D-2's ST_GAS `class_total_twh` moves
**8.571 → 5.705 TWh (−33 %)**. That denominator reconciles with **no** dispatch-side measurement in
either leg:

| ST_GAS 2022 energy, TWh | control | arm | direction |
|---|---:|---:|---|
| `class_hourly` (P1) | 6.6384 | **7.3090** | **rises** |
| `class_band_hourly` (P1) | 6.7047 | **7.3845** | **rises** |
| `dispatch/2022_P1.parquet`, `klass` | 6.6384 | **7.3090** | **rises** |
| dispatch joined by `unit_id` to the rebuilt fleet's `plant_group` | 6.7047 | **7.3845** | **rises** |
| **D-2 `class_total_twh`** | **8.571** | **5.705** | **falls** |

D-2's basis is **internally consistent on the control across all four years** (ST_GAS ×1.29 / 1.20 /
1.24 / 1.27 of the dispatch-side total, CC_REGULAR ×0.95–0.97), so it is a real alternative
classifier, not noise — and on the arm that stable relationship **inverts to ×0.78**. On every basis
that does reconcile, the arm's forced share **falls** (1.92 / 7.31 = **26.3 %** against the control's
1.98 / 6.64 = **29.8 %**).

**I did not diagnose it and I do not claim it is a bug.** What I claim is bounded: the C8 flip is
**uncorroborated by any dispatch-side measurement**, and D-2's denominator behaves anomalously under
a change to a class's **tranche structure** — which is exactly what the declared ladder collapse
(88 → 44 rows) is. That generalises beyond this arm: **any** mechanism that collapses or expands a
smoothing ladder would meet it. Handed forward as an open object, and it does **not** change this
session's verdict, which is already STOP on G-NONTARGET.

## 8. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`, pre-committed in PRECOMMIT §8)

The container is ephemeral; the bundle is pushed and retrievable (§1), so this question can be
answered later at zero re-solve cost for 2022 — but it should be answered.

> **A structurally-correct de-leak removes a rule-25-prohibited ERCOT value from NYISO's ST_GAS
> offer. Every structural gate passes. It closes 58 % of ST_GAS's 2022 volume gap and improves the
> failing C1 cell. It costs $1.42/MWh, which lands C3a-2022 at −11.61 % against a ±10 % band.
> Do you want it armed?**

Rule 1 `[R-STRUCT]` says a real market behaviour stays in even when it makes the fit worse. The
owner's standing formula says *"if structural integrity improves but gates regress that may still be
a keeper."* Both point one way, and neither is mine to decide — so the screen stopped the arm and
the question is put rather than pre-empted.

**If the answer is yes**, the work is: re-solve the full span `--years 2022 2023 2024 2025` as ONE
invocation and ONE bundle (rules 16 / 32(b)), ~25 min, covering the union of NYISO's registered
years; 2022 itself needs no re-solve to inspect. **If the answer is no**, the field stays default-off
and the matrix cell stays `R` with the re-test condition in §9.

## 9. THE RE-TEST CONDITION — and it is a real pairing, not a formality

Matrix cell `nyiso_st_gas_econ_bands_deleaked` → **`R`**, re-test condition stated:
**pair it with a mechanism that restores the scarcity tail (issue #1344), and re-screen.**

That is not a stalling device; this session's companion finding
(`docs/FINDING-nyiso232-c3a-is-two-objects-2026-09-13.md`) measured why the two belong together.
With each year's top 5 % of actual-price hours removed, the model is **over**-priced by **+4.1 to
+14.2 %** in every one of 2022–2025. The headline C3a is a **difference of two large errors of
opposite sign**: a missing scarcity tail pulling it down, and an over-priced ordinary-hour level
holding it up. The de-leak moves the **ordinary-hour level in the right direction** and is charged
for it only because the tail is absent. Close #1344 and the headroom this arm needs appears as a
by-product.

**Stated against my own arm**, to be clear: that is an argument for the *pairing*, not a reason to
re-read this screen. The gate stopped it and the gate stands.

## 10. RULES

1 `[R-STRUCT]` — the arm is argued on structure; the direction was disclosed as a hazard and
pre-registered as an expected stop; nothing was swept against a gate.
13/14 — the outcome-based identification is refused; the measured basis is preserved.
19 `[R-ONE-MECH]` — `committed`/`peak` excluded; C3a's slope and C3c shown to be one object.
21/24 — zero free parameters, zero new literals; a `prb_overrides`-only arming raises.
23 — settled as not engaged (§2). 25 — this is the rule being enforced; no verdict transfers, every
other ISO's cell is `U`. 26 — the removed value is removed, not re-levelled.
28 `[R-MECH-MATRIX]` — base row + cells in all seven shards, and the NYISO cell updated to `R` in
this session. 29 `[R-SCREEN]` — phase 0 first, one screen year on footprint, gates fixed before the
solve and not re-cut after it, G-DRIFT recorded before the arm.
31 `[R-RETAIN]` — nothing deleted; the bundle is gitignored, not removed, and the promotion question
is asked. 32 `[R-SHARD]` — the parent ran zero LP. 33 `[R-SHARD-ARCHIVE]` — the shard was archived
only after fetch + checkout + signature verification; its branch is **kept**, because it carries a
bundle a promotion would register (33(f)(3)). 34 `[R-SHARD-PROMOTABLE]` — the screen shard pushed
its bundle, `dispatch/` included, and retrievability was verified by `git ls-tree` before archiving.

---

# §11 — THE OWNER RULED "ARM IT". PROMOTED, AND THE DETERMINATION MOVED IN A WAY THE RULING DID NOT COVER

Appended after the span solved and the promotion completed. §8 put the question; the owner answered
**"Arm it"**; Addendum A recorded the ruling and pre-registered the span **before** it ran.

## 11.1 The span, against what Addendum A predicted before the numbers existed

| | pre-registered in Addendum A §A.4 | measured |
|---|---|---|
| C3a-2022 | "FAILS at ≈ −11.6 %… the accepted cost" | **−11.61 % FAIL** |
| C3a-2025 (named at risk, **unmeasured**) | "a proportional move would land it near **−7 to −8 %**… but 2025 could also fail" | **−7.99 % PASS** |
| C3a-2023 / 2024 | "expected to move *toward* zero and stay PASS" | **−1.26 % / −0.75 %**, both PASS; 2024 improves |
| C1 | "should improve… **2023 is the exception** — ST_GAS over-runs there and the arm makes that worse" | ST_GAS better in 2022/2024/2025, **worse in 2023 (+1.989 → +3.326 TWh)**, in band |
| C8/D-2 | "the open flag" | **FAILS 2022/2023/2024** — §11.3 |

Served demand is **identical to 5 dp in all four years**, dump and slack **0.000** throughout.
Solved on-pin, one invocation, one bundle, 2022–2025.

## 11.2 The determination, stated first and not softened

**Registered full span: NOT-YET. ISO tier (2023–2025, rule 30(c)): NOT-YET — a DOWNGRADE from the
superseded keeper's CALIBRATED.**

**Every load-bearing criterion passes on the ISO tier: C1, C2, C3a, C3b, C4, C6.** The downgrade is
**C8 alone**, and there is a second-order effect worth stating explicitly because it doubles the
damage: **C8 failing is also what strips C3c of its lone-failure status** under rule 22 `[R-C3C]`
guard (a), reverting it from a ledgered CAVEAT to a FAIL. Remove C8 and **both** resolve, and the
ISO tier reads CALIBRATED with C3c as the single ledgered caveat — the same headline as the
incumbent, reached with C1/C3a/C3b all passing.

## 11.3 C8's failure is the D-2 artifact, measured in all four years

| ST_GAS forced share | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| superseded keeper | 23.1 % pass | 16.5 % pass | 21.4 % pass | 19.0 % pass |
| **this run, scorer (row-count vote)** | **33.6 % FAIL** | **34.3 % FAIL** | **36.6 % FAIL** | 28.5 % pass |
| this run, capacity-weighted (stable) | **20.8 % pass** | **14.8 % pass** | **20.6 % pass** | **18.1 % pass** |

The **numerator** — actual forced energy — moves within **±2 %** in every year. The **denominator**
collapses **33–52 %**. Every dispatch-side measure of ST_GAS energy **rises**. On a
band-structure-stable vote the forced share is **lower than the superseded keeper's in every single
year**, which is what physics demands: the same floors are a smaller share of a class that now runs
more. The D-4 provenance failures C8 escalates to are **pre-existing and unchanged** — 9
unit-conduct rows on **both** legs, same plants.

Mechanism and proof: `docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md`. Ravenswood
(plant 2500) was labelled `ST_GAS` on an **8–7 tranche-count vote**; this mechanism's declared,
pre-registered ladder collapse takes ST_GAS to 4 rows and the label flips to `CC_REGULAR`, moving a
~2.5 GW site's whole dispatch between denominators.

**The scorer's number is the official one and is carried as a FAIL everywhere.** Nothing is
re-scored on this lane's corrected basis, and the one-line shared-scorer fix is **not** landed here:
the census shows SPP/SOCO is the most exposed ISO (23–25 flippable plants), and a NYISO lane can
neither measure nor authorise another ISO's verdict change (rule 25).

## 11.4 What was actually bought, and what it cost

**Bought:** a rule-25-prohibited ERCOT value is gone from NYISO's ST_GAS offer, verified
arithmetically in the attestation rather than asserted; zero free parameters; zero new literals; C1
improves in 3 of 4 years and CC_REGULAR in all 4; C3a-2024 crosses from +1.05 % to −0.75 %.

**Cost, at full magnitude:** C3a-2022 fails at −11.6 % (pre-registered, accepted). C3b-2022 worsens
0.209 → 0.218 (already failing). 2023 ST_GAS moves away from its actual. **CT_PEAKER worsens in all
four years** — a consistent adverse move, well inside band, and not buried here. And the ISO tier
reads NOT-YET, on the artifact above.

## 11.5 THE QUESTION THIS RAISES, which the owner's ruling did not answer

> The ruling "Arm it" answered a question framed on **C3a-2022 at −11.61 %**. It did not cover
> **NYISO's headline going CALIBRATED → NOT-YET on a scorer defect**. Two routes:
> **(a)** leave it — the record is honest and fully documented, but the status page under-reports
> NYISO until someone fixes D-2; or **(b)** authorise the D-2 capacity-weighted vote as a
> cross-ISO change, measured across SPP/SOCO/CAISO first. (b) is a one-line fix plus a blast-radius
> measurement; it is not this lane's to authorise.

## 11.6 Promotion mechanics (rule 35 `[R-PROMOTE]`)

Year union enumerated from the registry **before** the prune (35(b)) — `{2022, 2023, 2024, 2025}` —
and covered exactly by the one bundle, so 35(c) needs no stamped companion. Promote → verify →
delete order (35(e)): `audit_keepers --iso NYISO` run between, E11 cleared by declaring **both**
moved recipe keys in the shard prose (`coal_prb_sigmoid_overrides` and `offer_curve_by_group`, both
this one field's expression), then the superseded keeper pruned via `--force-uncite`, which 35(d)
names as the **intended** route. Post-prune `audit_keepers`: **PASS, 0 failures**. Rule 31
`[R-RETAIN]` trigger (i) is met — the owner ruled — and git history is the record for the bytes.
Shard archived after fetch + checkout + signature verification; bundle retrievable at
`git checkout fc545728636b40d402f5fcba4cae4f6edc42c19e -- results/calibration/nyiso232_deleak_span`.
