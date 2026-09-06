# FINDING — capx D76 phase 2: the measured screen peak across four ISOs. **Every STOP structurally clean; ONE of six consumers is live; PJM is now INERT; nothing arms.**

**Lane:** capx D76 phase 2 (director's release §0au.3). Branch
`claude/capx-d76-p2-full-span-4jkhit`, base `origin/main` **`e6a0402f`**.
Pre-registered in `PRECOMMIT-capx-d76-p2-2026-09-06.md` + Addendum 1, **pushed before the first
LP**. Phase 0/1 record: `FINDING-capx-d76-2026-09-06.md`.
Instruments (all committed): `docs/handoffs/d76/p2_predeclare.{py,json}` (the pre-solve
declaration), `p2_gate.py` + `p2_gate_{pjm,caiso,ercot,miso}.json` (the STOP grader and the
whole-ledger diff), `p2_consumer_probe.py`, `p2_accreditation_probe.py` (both zero-LP).
DATA PROFILE: `pjm`, then `caiso` / `ercot` / `miso`.

**NOTHING ARMS.** The director's release covers phase 2 and nothing past it. §9 drafts an arming
card **for** the director; drafting is not serving. **NEISO and NYISO are DEFERRED** by the
director's call and were not solved, screened or scored.

---

## 0. Result in one paragraph

**Eight legs, four ISOs, one solve-code state; all eight rc=0. The mechanism does exactly what its
arithmetic says and nothing else — but the lane's substantive finding is about the CONSUMERS, not
the arm.** STOP 2, the whole structural claim, lands to **0.000 MW in every year of every ISO**: the
arm's screen peak equals the pre-declared measured peak, and equals the LP's own `peak_demand_mw` in
every solved year. The whole-ledger diff (D81 rec 4) moves **1 to 8 fields of 30-39 per year**, every
one inside the pre-declared partition, **zero `UNCLASSIFIED` keys in any ISO**. STOPs 1, 2, 4, 5, 6
PASS in all four ISOs; **STOP 3 FAILS in PJM alone, on a `run_config` provenance key my own
mid-A/B commits moved** — my procedural error, reported at full magnitude in §5 and not
reclassified. The finding that matters for the director: **of the six seam-peak consumers phase 0
§4.2 enumerated, exactly ONE is live in every configuration tested — the adequacy requirement**
(and through it the CR-1 position and the reserve-margin backstop). The VRE accreditation census is
peak-INERT in all four ISOs, measured; the reliability floor never binds in any leg of any ISO; the
locality path is gated off. And because **D67-ARM landed between phase 1 and this lane**, PJM's
requirement is now peak-independent in all five delivery years, so **PJM is INERT end-to-end** — its
five-year A/B moves the seam field and *nothing else*, and phase 1's headline `gas_st` survival
(+7,333.7 / +9,464.5 MW) is **gone**, exactly as §2 of the PRECOMMIT pre-declared. Where the
requirement is still peak-dependent the effect is real and large: **CAISO builds 2,532.391 MW less
phantom gas CT** in 2023, and **MISO's admission cap saves 343.312 MW of coal** from a 2024 exit.

---

## 1. The legs, and the one solve-code state

| leg | ISO | window | cache key | wall | rc |
|---|---|---|---|---|---|
| 1-C | PJM | 2021-2025 | `a9c66d8ea25acb9d` | 14.6 min | 0 |
| 1-A | PJM | 2021-2025 | `fd07e2dba50cd32b` | 14.6 min | 0 |
| 2-C | CAISO | 2021-2023 | `2184fc9c85fafd06` | 5.1 min | 0 |
| 2-A | CAISO | 2021-2023 | `8a7ef53c812be4e1` | 5.1 min | 0 |
| 3-C | ERCOT | 2021-2023 | `e465ee243716c86d` | 3.5 min | 0 |
| 3-A | ERCOT | 2021-2023 | `681b733594f4cd6b` | 3.6 min | 0 |
| 4-C | MISO | 2021-2023 | `ad3af46ecefd8941` | 10.7 min | 0 |
| 4-A | MISO | 2021-2023 | `ff8ef4fcb278a76d` | 10.4 min | 0 |

Every key **reproduced its pre-registered value** (PRECOMMIT §3, machine-emitted before the first
LP) and every control key equals its bare recipe key. Independent corroboration: `a9c66d8ea25acb9d`
is the key the **D78-R** lane records as its own PJM 2021-2025 `control-P`, and this control's
economic `plant_release_precision` of **0.122** is D78-R's control-P figure to the digit — two
different lanes reproducing the shipped bare recipe.

**All eight legs ran SEQUENTIALLY at one base** (`e6a0402f`), one LP at a time; rule 12's
two-concurrent allowance was deliberately not taken (15 GB box; the D67 lane lost a leg to the
kernel that way). Addendum 1 records the mid-lane `main` move to `82a7742d` and its file-level
audit — `src/market_sim` untouched entirely — as **INERT**, which is why holding all eight legs at
one base was available and was taken.

## 2. STOP 2 — the identity. **0.000 MW, every year, every ISO.**

The whole structural claim of the gate, and it lands exactly.

| ISO | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| PJM | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| CAISO | 0.000 | 0.000 | 0.000 | — | — |
| ERCOT | 0.000 | 0.000 | 0.000 | — | — |
| MISO | 0.000 | 0.000 | 0.000 | — | — |

`|arm screen_peak_demand_mw − pre-declared measured peak|`, MW. And `|screen peak − the ledger's own
peak_demand_mw|` = 0.000 MW in every SOLVED year of every ISO. The 2022 rows are **bridge** years —
evolved, never solved — so the identity also proves the gate fires where the bridge evolves the
fleet against the seam peak.

**A reproduction note, against interest.** The runner's own seam peak differs from the zero-LP
pre-declaration by **0.004-0.007 MW** (e.g. PJM 2025: ledger 163,019.507 vs pre-declared
163,019.514; CAISO 2021: 43,228.159 vs 43,228.163) — 4x10^-8 relative, float accumulation order in
`add_load_layers`. It does **not** touch STOP 2, which tests the ARM's screen peak against the
MEASURED peak, and there the match is exact. Recorded because a pre-declaration that reproduces to
"about" a value should say so.

## 3. The whole-ledger diff (D81 rec 4) — every moved key, classed, with zero UNCLASSIFIED

| ISO | year | moved / total | keys (class) |
|---|---|---|---|
| PJM | 2021 | 1/36 | `screen_peak_demand_mw` (SEAM) |
| PJM | 2022 | 1/31 | `screen_peak_demand_mw` (SEAM) |
| PJM | 2023 | 1/39 | `screen_peak_demand_mw` (SEAM) |
| PJM | 2024 | **0/39** | — (the weather year: both paths are the same object) |
| PJM | 2025 | 1/39 | `screen_peak_demand_mw` (SEAM) |
| CAISO | 2021 | 1/36 | `screen_peak_demand_mw` (SEAM) |
| CAISO | 2022 | 3/30 | + `screen_adequacy_requirement_mw`, `screen_reserve_position` (SCREEN) |
| CAISO | 2023 | 8/38 | + `capacity_reserve_position` (SCREEN), `entry_decided_mw_by_tech`, `thermal_additions` (DECISION), `fleet_by_fuel_after`, `reserve_margin` (FLEET) |
| ERCOT | 2021 | 1/36 | `screen_peak_demand_mw` (SEAM) |
| ERCOT | 2022 | 3/31 | + `screen_adequacy_requirement_mw`, `screen_reserve_position` (SCREEN) |
| ERCOT | 2023 | 3/39 | + `screen_adequacy_requirement_mw`, `screen_reserve_position` (SCREEN) |
| MISO | 2021 | 1/36 | `screen_peak_demand_mw` (SEAM) |
| MISO | 2022 | 4/31 | + `screen_adequacy_requirement_mw`, `screen_reserve_position` (SCREEN), `pipeline_events` (DECISION) |
| MISO | 2023 | 5/39 | + `capacity_reserve_position` (SCREEN), `pipeline_events` (DECISION) |

**Every difference is explained in §4 and §6. No key moved that belongs to no declared class, in any
ISO.** The partition was fixed in the PRECOMMIT before the first LP and was not widened.

## 4. THE SUBSTANTIVE FINDING — one live consumer of six

Phase 0 §4.2 enumerated six direct consumers of the seam peak (plus five reached through
`evolve_fleet`). This lane measured which of them actually move. **Exactly one does.**

| consumer (phase 0 §4.2) | measured verdict, this lane |
|---|---|
| **3. adequacy requirement** | **LIVE** in CAISO / ERCOT / MISO; **INERT in PJM** (D67-ARM, published RR, ∂R/∂peak = 0 measured at both peaks in all five DYs) |
| **1. CR-1 reserve position** | LIVE **only as a function of the requirement** — it moves in exactly the ISO-years the requirement moves, never independently |
| **5d. reserve-margin backstop** | LIVE in **CAISO only** (the one ISO where it fires at all in-window) |
| **5a. retirement reliability floor** | **NEVER BINDS** — `floor_retained` is **empty in every year of every leg of all four ISOs** |
| **4 / 5c. accreditation census** | **PEAK-INERT in all four ISOs, measured** (§4.1) |
| **2. D59 locality peaks** | n/a — `locality_capacity_curves` default-off in every leg |

### 4.1 The accreditation census is peak-inert everywhere — measured, not assumed

`p2_accreditation_probe.py` evaluates the shipped resolvers at the seam peak and at the measured
peak, on each control leg's own committed VRE pools:

| ISO | wind credit (seam → measured) | solar credit | DR-as-supply |
|---|---|---|---|
| PJM | 0.41 → 0.41 (all 5 yrs) | 0.1064 → 0.1064 | 6,084.8-11,886.8 → identical |
| CAISO | 0.16 → 0.16 | 0.18 → 0.18 | n/a |
| ERCOT | 0.20 → 0.20 | 0.21 → 0.21 | n/a |
| MISO | 0.166 / 0.08 → identical | 0.3875 → 0.3875 | n/a |

Confirmed in the solve: `screen_entering_firm_mw` is **identical between control and arm in every
year of every ISO** — CAISO 48,148.76, ERCOT 86,607.368 / 86,606.167, MISO 130,958.761 /
127,973.621, PJM every year. The penetration-indexed ELCC curve is saturated or falls through to a
flat per-ISO credit across the whole hindcast window, and PJM's DR-as-supply is on rung 2 (absolute
published UCAP MW for an in-table delivery year), which has no peak term at all.

**This narrows the blast radius phase 0 warned about.** Phase 0 stated, correctly on the code, that
the peak "reaches the floor, the backstop, the entry screen, the accreditation census and the CR-1
position in every ISO regardless" of any requirement-mooting gate. Measured, the reach is real but
the *response* is not: in the configurations the repository actually ships, mooting the requirement
moots the mechanism.

**Stated at the gate, because it cuts the other way too:** PJM's accreditation inertness rests on an
ELCC curve that **clamps** across the hindcast window — which is itself the defect **capx D75-R** is
chartered to repair. If `pjm_vre_accreditation_vintage` arms, PJM's census may become peak-sensitive
again and PJM's inertness here does not survive it. This lane's PJM verdict is a verdict **at this
HEAD**, not a property of the ISO.

## 5. STOP 3 in PJM — a LITERAL FAIL, caused by me, reported and not reclassified

The grader compares the pre-registered object (every GATE in `run_config.json`, i.e. the nested
`scenario_config`) plus the five per-leg bookkeeping keys the PRECOMMIT names. In PJM it found a
**sixth** differing top-level key: **`git`**.

```
control  sha aea30cd5   basis_sha e6a0402f…   dirty false
arm      sha b9262222   basis_sha b9262222…   dirty false
```

**Cause: my own procedural error.** I committed twice *between* the two legs of LEG 1's A/B (the
PRECOMMIT addendum, and a reported-block tweak to the grader), so the two legs recorded different
HEAD shas. The charter says *rebase* between legs, never during; I applied that to rebases and not
to my own commits, which is the same hazard wearing a different hat.

**The substantive check is clean.** `git diff aea30cd5 b9262222` over `src/market_sim`,
`scripts/run_capacity_hindcast.py`, `scripts/lib`, `data/raw/_validation-source` and
`data/raw/reference` is **EMPTY**. The entire delta between the two shas is **one file** —
`docs/handoffs/d76/p2_gate.py`, a zero-LP grader no solve imports. Both legs were `dirty: false`.
So no operand moved and the A/B is sound on the merits.

**It is still reported as a FAIL.** This is post-result, so the pre-registered text stands as
written, the grader is **not** relaxed, and `p2_gate_pjm.json` carries `verdict: FAIL` — the same
discipline phase 1 applied to its own 2021 literal miss and D67 applied before that. Two
corroborations that the finding is exactly what it says: **STOP 3 PASSES in CAISO, ERCOT and MISO**
(five bookkeeping keys, no `git` difference), because I stopped committing once the legs were
running; and the PJM `scenario_config` differs in **exactly one field, this lane's own gate**, in
PJM as in the other three.

**The lesson for the pack, and it generalizes past this lane:** an A/B's two legs must be solved
without *any* commit between them, not merely without a rebase — `run_config.json` records the HEAD
sha, so a docs-only commit is enough to make two otherwise-identical legs differ in a recorded
field. Either freeze the branch for the duration of an A/B, or enumerate `git` as per-leg
provenance in the pre-registration.

## 6. What the mechanism DID, per ISO — reported, never gated (PRECOMMIT §5)

The pre-solve arithmetic reproduces through the LP in every ISO-year where the requirement is live:

| ISO | year | requirement, control → arm | Δ measured | Δ pre-declared | miss |
|---|---|---|---|---|---|
| CAISO | 2022 | 51,324.307 → 58,769.600 | **+7,445.293** | +7,445.274 | 0.019 |
| CAISO | 2023 | 52,988.498 → 50,608.050 | **−2,380.448** | −2,380.400 | 0.048 |
| ERCOT | 2022 | 70,724.947 → 85,086.586 | **+14,361.639** | +14,361.615 | 0.024 |
| ERCOT | 2023 | 80,259.589 → 90,669.231 | **+10,409.642** | +10,409.610 | 0.032 |
| MISO | 2022 | 110,034.611 → 117,223.631 | **+7,189.020** | +7,189.020 | 0.000 |
| MISO | 2023 | 116,066.268 → 121,643.990 | **+5,577.722** | +5,577.671 | 0.051 |
| PJM | all 5 | identical, every year | **0.000** | 0.000 | 0.000 |

**Both pre-declared sign cells HIT, including both reversals.** The PRECOMMIT §5 sign table fixed
`arm − control = −Δ`, predicting a HIGHER bar (fewer exits / longer fleet) in ten ISO-years and a
LOWER bar (more exits / shorter fleet) in exactly two — **CAISO 2023** and **PJM 2025**. CAISO 2023
fires and is the lane's largest decision effect; PJM 2025 is inert for the §4 reason. The reversal
cells are the lane's own falsifiability: a mechanism that only ever lengthened the fleet would be
indistinguishable from a one-way retention adder, and this one does not.

### 6.1 CAISO — 2,532.391 MW of phantom gas CT the measured peak says was never needed

2023, the reversal year. Seam peak 46,077 vs measured 44,007, so the arm's bar is **lower**:

| | control | arm |
|---|---:|---:|
| `screen_adequacy_requirement_mw` | 52,988.498 | 50,608.050 |
| `screen_entering_firm_mw` | 48,148.760 | **48,148.760 (identical)** |
| `screen_reserve_position` | 0.908664 | 0.951405 |
| `thermal_additions` (`source: reserve_backstop`) | 5,046.985 MW | **2,514.593 MW** |
| `entry_decided_mw_by_tech.gas_cc` | 1,000.0 | **1,000.0 (identical)** |
| `reserve_margin` | 0.205239 | 0.150571 |

**One mechanism, one phenomenon (rule 19).** The entering firm census is identical to the cent, so
the entire effect is the requirement feeding the **reserve-margin adequacy backstop**
(`unit_id: gas_ct_adequacy_2023`); the economic entry pipeline (`gas_cc: 1,000.0`) does not move at
all. And the arithmetic closes: **Δbuild / Δrequirement = 2,532.391 / 2,380.448 = 0.94000018**,
i.e. the build is exactly the requirement delta grossed up by the CT accreditation credit. In 2022
nothing downstream moves — CAISO's only retirement rows are 3 `announced` (7.0 MW), identical in
both legs, so a higher bar has nothing to save.

### 6.2 MISO — 343.312 MW of coal saved from a 2024 exit, invisible at fleet level

MISO's requirement and position move in both binding years, its `screen_entering_firm_mw`,
`retirements` (35 / 25 `announced` rows, 2,877.158 / 2,178.300 MW) and `fleet_by_fuel_after` are
**identical**, and its `pipeline_events` count is identical (410 / 390). The decision change is
inside those rows:

| tranche | control | arm |
|---|---|---|
| `COAL_MISO-Indiana_p6705_committed` 328.282 MW | `decided` (2022) → `re_confirmed` (2023), execute 2024 | **`entry_capped`** both years |
| `COAL_MISO-Indiana_p6705_peak` 14.430 MW | same | **`entry_capped`** |
| `COAL_MISO-East_p54098_committed` 0.600 MW | same | **`entry_capped`** |

**343.312 MW** of coal that the control decides for a **2024** economic retirement is blocked by the
arm's admission cap — which is sized off the requirement. Because `execute_year = 2024` is
**outside** the 2021-2023 window, the in-window fleet, `retirements` and every scored metric are
byte-identical.

**This is the D81 rec 4 lesson firing on its first outing.** A gate table asserting "the fleet and
the retirement rows must not move" would have PASSED and reported "nothing happened". Only
differencing *every* committed block found a real decision change. The recommendation earns its
keep.

### 6.3 ERCOT — the adequacy reading changes materially; nothing consumes it

Requirement +14,361.639 / +10,409.642 MW; position **1.224566 → 1.017873** (2022) and
**1.079076 → 0.955188** (2023) — the arm crosses **below 1.0**, reading ERCOT as *short* in 2023
where the control reads it *long*. But zero retirements, zero floor rows and zero additions in both
legs: ERCOT is energy-only, so no capacity payment reads the position and the backstop is off. The
signal changes; in this window nothing consumes it.

### 6.4 PJM — INERT end-to-end, and phase 1's headline is gone

The five-year A/B moves `screen_peak_demand_mw` and **nothing else**, in any year. Requirement
identical (published RR: 166,355.1 / 163,268.9 / 163,166.2 / 164,107.6 / 144,450.0), entering firm
identical, position identical, retirements identical, fleet identical, `floor_retained` empty
throughout.

**Phase 1 measured the arm retaining +7,333.7 MW (2022) and +9,464.5 MW (2023) of `gas_st`. At this
HEAD the arm retains exactly 0 MW more than the control.** Both legs still exit the entire
**10.297 GW** steam fleet against **2.702 GW** actual. That is the PRECOMMIT §2 pre-declaration
confirmed at full magnitude: phase 1's survival channel was the peak-dependent requirement, and
D67-ARM removed it. **D76 does not touch PJM's steam over-exit at this HEAD** — the over-exit
remains D74's object entirely, and phase 1's §8(a) routing to the D74 successor stands, with this
lane's contribution now reduced to "not a contributing cause, at this HEAD".

## 7. STOP 5 — PASS in all four ISOs, and MORE than was pre-registered

The PRECOMMIT pre-registered STOP 5 as testable for LEG 1 only, on phase 1's finding that "a
truncated 2021-2023 window produces no scorer output at all". **That is not so, and it is corrected
here in the direction of more testing, never less:** phase 1 had looked for a `forecast_verdict.json`
that is only produced by running `scripts/forecast_verdict.py`, which it never ran.
`score_capacity_hindcast.py` scores a 2021-2023 bundle fine. So all four ISOs were scored and
graded, not one.

| ISO | control determination | arm determination | verdict rows | score.json metric paths differing |
|---|---|---|---|---|
| PJM | HOLD (FC-3 FAIL, FC-7 CAVEAT) | HOLD (same) | **identical** | **0** (only `generated_utc`, 3 s apart) |
| CAISO | HOLD (FC-3 FAIL) | HOLD (same) | **identical** | 15, all `additions.*` — §7.1 |
| ERCOT | HOLD | HOLD | **identical** | **0** |
| MISO | HOLD | HOLD | **identical** | **0** |

**No non-target load-bearing criterion flips PASS → FAIL anywhere. STOP 5 PASS, four of four.**

### 7.1 CAISO's FC-3 moves toward the actuals — REPORTED, and NOT the reason for anything

| FC-3 row | control → arm | direction vs actual |
|---|---|---|
| `additions.by_tech.gas_ct.err_frac` | 68.684 → **50.009** | toward |
| `additions.by_tech.gas_ct.model_gw` | 9.449 → **6.917** GW | toward |
| `additions.model_total_gw` | 18.449 → **15.917** | toward |
| `additions.shares.gas_ct.delta_pp` | 0.507 → **0.429** | toward |
| `additions.shares.solar.delta_pp` | −0.178 → **−0.143** | toward |
| `additions.shares.wind.delta_pp` | 0.136 → 0.162 | **away** |

Five of six move toward the actuals and one moves away; FC-3 still FAILs in both legs and the
determination is HOLD either way. **Rule 1 `[R-STRUCT]` governs how this is used: it is reported and
it is not an argument.** The mechanism was selected on structure — rule 14 `[R-ACCURATE]`, a
measured input replacing a synthesized estimate — before any of it was solved, and a screen may kill
an arm and may never promote one. Had these rows moved the other way the mechanism would be no less
correct.

## 8. PJM FC-3 at full magnitude (charter: report, never gate)

Identical in both legs, so this is the control's and the arm's number alike:

| row | value | band |
|---|---|---|
| `retire.total_gw` | actual 15.062 / model 18.058, err_frac +0.199 | **FAIL** |
| `retire.unit_recall_gt300` | 0.650 (13/20); plant 0.700 (14/20) | **FAIL** |
| `retire.false_retire` | 8.065 GW, 44.7 % of model | **FAIL** |
| `retire.plant_release_precision` (economic, window) | 0.122 | reported-only |

Per fuel (actual GW / model GW / err_frac): `gas_st` **2.702 / 10.297 / +2.811**;
`coal` 10.299 / 6.797 / −0.340; `oil` 0.613 / 0.051 / −0.916; `gas_ct` 0.808 / 0.000 / −1.000;
`gas_cc` 0.434 / 0.903 / +1.081; `biomass` 0.207 / 0.009 / −0.955.

## 9. THE ARMING CARD — **drafted for the director, NOT served by this lane**

> **Card: arm `capacity_screen_peak_measured_hindcast`?**
>
> **What it is.** One gate, one seam, **zero scalar fields, zero free parameters** (rules 21/24).
> Armed, the capacity screens test the solve year's **own measured load** — the identical array the
> LP dispatches — instead of the weather year's load de-grown across the span by `_scale_demand`.
> Rule 14 `[R-ACCURATE]` in its plainest form: the measured input replaces an estimate. Rule 13's
> forward test is met by construction — a forecast year has no measured load, so the growth path
> remains THE forecast methodology and the gate is inert in every forecast year, every crossover
> forward year and every backcast.
>
> **What arming would actually change, measured rather than enumerated.**
>
> | ISO | requirement | decisions in the tested window |
> |---|---|---|
> | PJM | **no change** (D67-ARM) | **none** — byte-identical across 2021-2025 |
> | CAISO | +7,445 / −2,380 MW | **−2,532.391 MW** backstop gas CT (2023) |
> | ERCOT | +14,362 / +10,410 MW | none in-window (energy-only; position crosses below 1.0) |
> | MISO | +7,189 / +5,578 MW | **343.312 MW** coal saved from a 2024 exit |
> | NEISO / NYISO | not tested | not tested — DEFERRED |
>
> **The case FOR.** The defect is a construction error on its own terms: the screens test a
> synthesized historical peak against which the same year's LP dispatches a different, measured
> load, and it is wrong by −23.3 % to +15.4 % across the six ISOs. Every STOP is structurally clean,
> the identity lands to 0.000 MW everywhere, the footprint is confined to the pre-declared
> partition with zero unclassified movement, and no determination flips in any ISO. Where it bites,
> it removes phantom capacity: CAISO stops building 2.5 GW of CT it does not need.
>
> **The case AGAINST, stated at the same strength.** (a) The **blast radius is real** — it changes
> the screen operand of every hindcast bundle in the repository and every FC-3 T1-H row on the
> forecast board, and every affected ISO's frontier bundle would need re-solving. (b) The measured
> benefit is **narrow at this HEAD**: PJM inert, ERCOT decision-inert in-window, MISO's effect
> outside the scored window, CAISO the only ISO where a scored metric moves. (c) **NEISO and NYISO
> are untested** — NYISO is requirement-moot at HEAD (D52) and so likely inert like PJM, but that
> is inference, not measurement.
>
> **The dependency the director should weigh.** PJM's inertness is **conditional on the ELCC clamp**
> that capx D75-R is chartered to repair (§4.1). Arming D76 before D75-R lands buys nothing in PJM;
> arming after may buy something. The two lanes interact and their order matters.
>
> **What this lane recommends.** Nothing — a rule-29 screen may kill an arm and may never promote
> one, and the charter's precondition is a STOP. The measured basis for a decision is above; the
> decision is the director's.

## 10. Matrix (rule 28) and retention (rule 29(c))

Cell verdicts updated in **each tested ISO's own shard only** — `PJM.js`, `CAISO.js`, `ERCOT.js`,
`MISO.js` (rule 25 `[R-ISO-SCOPE]`: each ISO gets its own letter from its own market's evidence).
NEISO's and NYISO's cells are untouched, because this lane did not test them. The `fc` letter stays
**`O`** in all four: the mechanism is measured but not adjudicated — arming is an owner card.

**All eight bundles are DELETED from `results/hindcast/` before this PR merges** (rule 29(c)). This
FINDING, the PRECOMMIT and `docs/handoffs/d76/p2_gate_{pjm,caiso,ercot,miso}.json` +
`p2_predeclare.json` carry every number the lane will ever cite; git history is the record for the
bytes. Nothing is registered on any dashboard — a screen bundle is never registered, and
`KEEP_REQUIRED_UNMAPPED_BUNDLES` is not the route for one.

## 11. Reproduction

```bash
.venv/bin/python docs/handoffs/d76/p2_predeclare.py          # the pre-solve declaration, zero LP
# eight legs, sequential, one at a time (see §1 for flags):
#   scripts/run_capacity_hindcast.py --iso <ISO> --start-year 2021 --end-year <2023|2025> \
#     --vintage 2020 --entry-screen-diagnostics [--no-]capacity-screen-peak-measured-hindcast \
#     --out-dir results/hindcast/d76p2-<iso>-<control|arm>
.venv/bin/python docs/handoffs/d76/p2_gate.py --iso <ISO> \
    --control results/hindcast/d76p2-<iso>-control --arm results/hindcast/d76p2-<iso>-arm
.venv/bin/python docs/handoffs/d76/p2_accreditation_probe.py   # §4.1, zero LP
.venv/bin/python docs/handoffs/d76/p2_consumer_probe.py        # §4, zero LP
```
