# PRECHECK — caiso-179: can the CELL-vs-SYSTEM cost split behind `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` be IDENTIFIED, and does it close `battery_dispatch_adder`?

**Session:** caiso-179 · branch `claude/caiso-179-degradation-split-dtqe4u` · 2026-08-07
**Keeper at session start:** `2026-08-06-caiso-175-tac-intake` — determination **NOT-YET** under
rubric v3.1 (C3a FAIL 2024 +11.7 % / 2025 +14.8 %; C3c the sole ledgered caveat; **8** criteria).
DOF ledger `n_entries` 11 / `n_residual` 8.
**CAISO ONLY.** No other ISO's keeper shard, registry entry or status part is touched.

**This document is written and pushed BEFORE any source value is read.** §0b is the exact
inventory of what has and has not been read at the time of writing.

---

## 0. What this session may not do (stated first, so nothing below can quietly override it)

* **The HOLDOUT SPEND FREEZE is ACTIVE** (`frontend/data/backcast/holdout-freeze.json`) and it
  **outranks any marker**. Solve years are **2023 / 2024 / 2025 only**, ONE bundle per arm
  (rule 16), years sequential, arms sequential (rule 12). `--holdout-authorized` is not used.
* **`holdout-freeze.json` and `calibration-complete.json` are OWNER ACTS.** This session writes
  neither.
* **CAISO does NOT hold `complete`.** It is carried under **`withdrawn`** (declared 2026-08-05,
  withdrawn 2026-08-06 by owner directive on the rubric-v3.1 amendment, because a marker cannot
  rest on a NOT-YET keeper). This was corrected at caiso-178 in three places and is **not
  re-broken here**. Nothing was ever spent under it; the locked test was never authorized.
* **Both walls stay walled.** C3a on non-public hourly pumped-storage water state
  (FINDING-caiso141); C3c on the SoCalGas OFO declaration record. `caiso_ps_charge_shape_anchor`
  stays **`G`**.
* **An N–S topology lever stays FORBIDDEN** (caiso-164 §0/§6).
* **No rule-22 authorization is required or taken.** Every year touched is inside the training
  window; under the 2026-08-06 owner clarification, data intake is not window-gated at all
  ("what is held out is the SCORE, never the DATA").

### 0a. The DO-NOT-REDO carried into this session, verbatim and binding

From caiso-176 §5 and caiso-178 §8. Every item below is **closed** and this session re-tests none
of them:

1. **Any value > \$15** — refuted twice: caiso-101's solved ±15 % battery-only throughput guard,
   and CAISO's own bid stack. The ATB route as previously constructed recomputes to **\$22.63** on
   today's constants; refused *a fortiori*.
2. **`caiso_storage_as_reservation` as this parameter's replacement** — INERT at caiso-74, the
   whole AS-award family refuted by arithmetic at caiso-127/129.
3. **Re-fetching or re-deriving `PUB_DAM_GRP`** for this parameter — SPENT AND CLOSED at
   caiso-178 at full coverage; the failure is structural, not a resolution problem.
4. **Adopting \$6.00, \$5.00, or any modal bin of the first-discharge-rung distribution** as a
   measured throughput cost.
5. **Reading the first discharge rung as a marginal cost at all** — it carries an hour-of-day
   shape (peaking 1.89/1.59/1.57× at h19 PT) and an 8–20 % mass at the \$1,000 soft cap.
6. **Treating caiso-176's ≤ \$15 as a STRICT UPPER BOUND on marginal cost.** It is a
   **revealed-conduct** statement: a quarter of the 2025 fleet offers to discharge at −\$32/MWh
   or below at some point in the year, because the shadow value of stored energy can be negative.
7. **Picking a value inside (0, 15] BECAUSE it sits inside the bound** — a fitted value wearing
   measured clothing.

**Item 6 is why §3's admissibility screen is written as a REFUTATION test and not as a truth
claim** (see §3), and **item 7 is why every factor in §2 must be a cited quantity and none may be
selected by this session** (see §4's G5).

### 0b. EXACTLY what has been read before this document was written

**Read — all of it committed repo content or categorical vocabulary, none of it a source value:**

* The committed constants `STORAGE_TECHS["li_ion_4hr"]` (`duration_hr` 4, `cycles` 5000,
  `capex_per_kw` 1810.3, `capex_per_kwh` 452.6) and
  `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25`, plus their surrounding comment blocks in
  `src/market_sim/config/capacity_market.py`. **All already published in
  FINDING-caiso176 §1a/§0** — nothing new is learned by reading them.
* `src/market_sim/model/storage.py::_degradation_cost_per_mwh` and its single call site
  (line 1609).
* The keeper's `run_config.json` fields `battery_dispatch_adder = 5.0`,
  `storage_degradation = True`, `storage_capacity_value = True`, `mode = "backcast"`, and the
  keeper attestation's `battery_dispatch_adder` DOF entry.
* `docs/parameter-citations.md` rows for `storage_techs.li_ion_4hr.*` (**citation strings only**,
  which are provenance, not measurements — the values in those rows are the committed constants
  already listed above).
* **The NREL ATB corpus's VOCABULARY ONLY** — the CSV header
  (`atb_year,technology,techdetail,display_name,core_metric_parameter,core_metric_case,tax_credit_case,scenario,default,core_metric_variable,value`),
  the distinct `technology` levels, the distinct `techdetail` levels under
  `Utility-Scale Battery Storage` (`2Hr / 4Hr / 6Hr / 8Hr / 10Hr Battery Storage`), the distinct
  `core_metric_parameter` levels (`CAPEX`, `Fixed O&M`) and `scenario` levels
  (`Advanced / Conservative / Moderate`).

**NOT read — nothing below has been looked at:**

* **Any `value` field of the ATB corpus.** Not one CAPEX number, not one FOM number.
* Any warranty, teardown, cost-benchmark or cycle-life number from any source, on disk or off.
* The intercept/slope of the power/energy split in `scripts/data/derive_cost_benchmark_envelope.py`
  or any artifact it writes.
* **Any CAISO price residual, keeper metric, or scored criterion value beyond the C3a/C3c figures
  already carried in the session handoff and the caiso-178 finding.** No residual enters the
  derivation at any point (rule 13 `[R-MEASURED]`).

---

## 1. The question, stated exactly

`battery_dispatch_adder = 5.0` is the CAISO keeper's last free parameter, DOF-ledgered
`identification: residual`. caiso-176 and caiso-178 closed two of the three named exits. **Exit 3
is the only one left:**

> replace `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` — which its own constant block calls
> *"a modeling simplification … **tunable**"* — with an **identified cell-versus-system cost
> split**, so that the ATB route becomes a genuine DOF **closure** instead of the **DOF
> SUBSTITUTION** caiso-176 §1a named it.

The question this session asks, and the only one:

> **Can that fraction be determined entirely from citable primary sources — NREL ATB augmentation
> / duration-sweep cost structure, LFP cell-vs-pack-vs-BOS teardowns, or warranty cycle-life
> documentation — so that the fraction stops being free?**

**A "no" is a result**, and it is the outcome this session must be equally willing to file (§5,
BRANCH II).

---

## 2. THE ARITHMETIC — declared in full, from source to fraction, before any number is read

### 2a. The formula is the CODE'S, not this session's

`storage.py::_degradation_cost_per_mwh` computes

```
adder [$/MWh discharged]  =  capex_per_kwh × 1000 / cycles × F
```

with `F = STORAGE_DEGRADATION_REPLACEMENT_FRACTION`. On the committed `li_ion_4hr` constants:

```
capex_per_kwh × 1000 / cycles  =  452.6 × 1000 / 5000  =  90.52  $/MWh per unit F
F = 0.25  ⇒  adder = $22.63/MWh          (reproduces FINDING-caiso176 §0.2 exactly)
```

### 2b. F's DECOMPOSITION IS ALSO THE CODE'S — this session does not choose a convention

The committed constant block states F's intent in two clauses, and they are two distinct physical
factors:

> *"(i) **only the cell stack degrades, not the power electronics / BOS**, and (ii) **warranties
> run to ~80 % retention**, so the full energy capex over rated cycles overstates the true
> marginal cost."*

That is, verbatim from the code:

```
F  =  φ  ×  (1 − R)
```

* **φ** — the share of installed $/kWh that is the **degrading, replaceable** content
  (clause i: everything except the power block).
* **(1 − R)** — the **capacity fraction actually lost** over the rated cycle life, where `R` is
  end-of-life retention (clause ii).

**Derivation, so the identity is checkable rather than asserted.** Over `N` rated cycles a
battery of energy capacity `E` discharges `Q = N × E` MWh (the code's own convention: one cycle =
one full `E`, which is why it divides by `cycles`). Over those cycles usable capacity fades to
`R × E`. To hold the asset at its rated `E` — what a market-participating BESS with a contracted
capacity does, by **augmentation** — the owner adds `ΔE = (1 − R) × E` of energy capacity at
`φ × capex_per_kwh` $/kWh. Therefore

```
$/MWh  =  (1 − R) × φ × capex_per_kwh × 1000 / N          ⇒  F = (1 − R) × φ.  ∎
```

`E` cancels; the identity is exact and matches the code's two clauses one-for-one.

**The competing convention is explicitly NOT taken.** One could instead assume the whole cell
stack is *replaced* at end of life (`F = φ`, no retention factor), giving a several-fold larger
adder. **The committed comment settles it against that reading** — clause (ii) enters retention as
a *reason the full capex overstates the cost*, i.e. as a reducing factor. This session takes the
code's convention as given and **will not switch conventions after seeing a number**. If the
retention leg cannot be sourced (§4, G3), the session **walls**; it does **not** fall back to the
replacement convention to obtain a value.

### 2c. φ — what it is, and why the ATB's ENERGY-SCALING share is the POINT ESTIMATE, not a bound

The ATB publishes `Utility-Scale Battery Storage` CAPEX ($/kW) for **five duration classes**
(2/4/6/8/10 Hr). This repo has **already established, committed and CI-tested** that the sweep is
**EXACTLY linear** in duration — `capacity_market.py:337-341` records ATB's structure as a fixed
$/kW power component plus a $/kWh energy slope with **residual 0**, derived by
`scripts/data/derive_cost_benchmark_envelope.py` and asserted by
`tests/test_cost_benchmark_envelope.py` (rule 23 `[R-FROZEN-DERIVE]` machinery). So

```
CAPEX(d)  =  p  +  e · d            p = power-scaling $/kW,  e = energy-scaling $/kWh
φ         =  e / capex_per_kwh(4hr) =  (e × 4) / CAPEX(4hr)
```

**φ so defined is the right object for this formula, not merely an upper bound on a bare-cell
share.** Augmentation does not install naked cells: adding energy capacity to a utility-scale BESS
means adding **modules in racks, in enclosures, with thermal management, DC cabling and the labour
to install them** — precisely the content that scales with duration, and precisely what is
excluded from the power block. The bare-cell price would **understate** augmentation cost. The
code's clause (i) — *"not the power **electronics** / BOS"* — reads correctly as *not the
**power-block** electronics and power-scaling BOS*, which is exactly the `p` term.

A cell-only teardown share is therefore reported as the **lower bracket**, never as the headline.

**One structural property, declared now because it matters:** φ is a **ratio inside a single ATB
year and scenario**, so any common deflator (the "2026$" conversion the committed constants carry)
**cancels exactly**. φ can be computed on raw ATB dollars without reproducing the deflation.

### 2d. Source ranking — FIXED NOW, so no source can be chosen after seeing its answer

**For φ:**

| rank | source | on disk? | what it gives |
|---|---|---|---|
| **S1 — PRIMARY** | **NREL ATB 2024 `Utility-Scale Battery Storage` duration sweep**, `data/raw/nrel-atb/` | **yes** | `e`, `p`, hence φ — the energy-scaling share, from the **same document** the model's `capex_per_kwh` denominator comes from |
| S2 | NREL / Ramasamy et al. *U.S. Solar PV and Energy Storage Cost Benchmark* component breakdown | no (fetch) | the bare **cell/module** share — the **lower bracket** |
| S3 | PNNL *Grid Energy Storage Technology Cost and Performance Assessment* (PNNL-33283) component split | no (fetch) | corroboration only |

**S1 is PRIMARY and the HEADLINE φ is S1's**, fixed here. Reasons, all independent of any value:
it is on disk; its linear structure is already validated and CI-asserted in this repo; it is the
same document family as `capex_per_kwh`, so the ratio is internally consistent; and it is the
object the augmentation physics actually calls for (§2c). **S2/S3 are REPORTED as brackets and
never substituted for the headline**, whichever way they land.

**For the `(N, R)` cycle-life / retention pair:**

| rank | source | what it must carry |
|---|---|---|
| **R1** | NREL ATB 2024 storage documentation / on-disk extract | a `(cycles, end-of-life retention)` **pair** |
| R2 | NREL *Cost Projections for Utility-Scale Battery Storage* (Cole & Karmakar) — ATB's own storage cost basis | same |
| R3 | A named public utility-scale LFP BESS **warranty** document | same |
| R4 | PNNL-33283 | same |

**Binding rule: the pair must come from ONE document, and this session uses that document's own
pair — `N*` AND `R*` together, never mixed across sources.** The highest-ranked source carrying a
**complete** pair is used. Mixing a cycle count from one document with a retention from another
would re-introduce exactly the free choice this session exists to remove.

**Consequence, declared now:** if `N*` differs from the committed `cycles = 5000`, the arithmetic
uses **`N*`** (self-consistency inside one document outranks agreement with a committed constant),
and the discrepancy against `cycles = 5000` is **reported as a separate rule-14 `[R-ACCURATE]`
finding**, not silently absorbed.

### 2e. The resulting number

```
F        =  (1 − R*) × φ
adder    =  capex_per_kwh × 1000 / N*  ×  F
         =  452.6 × 1000 / N*  ×  (1 − R*) × φ
```

with `capex_per_kwh = 452.6` re-verified against the on-disk ATB extract by gate **G1** (§4).
Every one of the three factors is a cited quantity. **None is chosen by this session.**

---

## 3. THE ADMISSIBILITY SCREEN — a REFUTATION test, not a truth claim

**Screen: the identified adder must land BELOW \$15.00/MWh.**

At the committed denominator this is `F < 15 / 90.52 = 0.16571`.

**What the screen is.** Two independent instruments in **this ISO** have refused a larger value:

* **caiso-101** — a *solved* A/B on this exact parameter family failed a pre-registered two-sided
  **±15 % battery-only throughput guard** (2024 charge 6.77 < 7.40 TWh; 2025 10.28 < 11.07;
  discharge under floor in all three years) at **\$14.25**, and the ATB route as then constructed
  now recomputes **higher**, to \$22.63.
* **caiso-176** — CAISO's own published `bid_stack`, model-free, put the fleet's revealed
  discharge reservation conduct at **≤ \$15/MWh** in all three years.

**What the screen is NOT.** Per DO-NOT-REDO item 6, **≤ \$15 is revealed conduct, not a strict
upper bound on marginal cost.** So the screen does **not** assert the true cost is below \$15. It
asserts only this, which is all it needs to assert:

> **A value at or above \$15 has been refuted twice in this ISO, and this session will not re-arm
> one.** If the identified arithmetic produces such a value, the correct report is that the
> identification SUCCEEDED and its result is REFUTED — not that the identification failed, and
> not that the arithmetic should be re-done until it clears.

That outcome has its own pre-registered branch (§5, **BRANCH III**) precisely so a refutation
cannot be quietly relabelled as a wall.

**And the screen is not a target.** Per DO-NOT-REDO item 7, no value may be selected *because* it
lands inside (0, 15]. The value is whatever §2e's three cited factors produce. **If it happens to
land near the incumbent 5.0, that is not confirmation of the incumbent** — the same refusal
caiso-178 §6 applied to the \$6.00/\$5.00 near-coincidence applies here, and will be stated in the
finding.

---

## 4. THE GATES — fixed before any number is read

**G1 — ATB CELL IDENTIFICATION + EXACT LINEARITY.**
Fit `CAPEX(d) = p + e·d` over the five duration classes for the ATB cell the committed constants
were derived from (`technology = Utility-Scale Battery Storage`, `core_metric_parameter = CAPEX`,
`scenario = Moderate`, `core_metric_variable = 2026`; both on-disk file families `atb_2024_*` and
`atb_2024v4_*` are tried and the one reproducing the committed constants is used).
**PASS** iff **(a)** `max |residual| ≤ 0.5 %` of the fitted 4-hr CAPEX — ATB's structure is
exactly linear, as `capacity_market.py:337-341` records — **and (b)** a **single common scalar**
`k` (the 2026$ deflator) maps the raw fit to the committed constants: `k × CAPEX_raw(4h)` = 1810.3
and `k × CAPEX_raw(8h)` = 3154.3, each within **0.5 %**, with the **same** `k`.
Gate (b) is what proves φ is computed against the same denominator the LP formula uses.
**FAIL ⇒ BRANCH III-N (no instrument).**

**G2 — φ IS CITED, NOT FITTED.**
φ = `e / capex_per_kwh(4hr)` from S1. **PASS** iff G1 passes. If S2 is reachable, its cell-only
share is reported as the lower bracket; **PASS additionally requires `φ_S2 ≤ φ_S1`** — a cell-only
share exceeding the energy-scaling share is physically impossible (cells ⊂ energy-scaling
content) and would prove the two are not measuring what this session thinks. **A violation
⇒ BRANCH III-N.** S2 being *unreachable* is **not** a failure: S1 is the declared primary.

**G3 — `(1 − R)` IS CITED, AT ITS OWN `N`.**
**PASS** iff a source in the §2d R-ranking carries a **complete `(N*, R*)` pair** in one document,
and that document is on disk or fetchable in this session. **No assumed 80 %. No "typical" value.
No pair assembled across two documents.**
**FAIL ⇒ BRANCH II (the third wall).**

**G4 — ADMISSIBILITY.** `adder < $15.00` (§3).
**FAIL ⇒ BRANCH III-R (identified-and-refuted).**

**G5 — NO NEW DOF.** Every factor entering §2e must be a cited quantity with a named source:
`capex_per_kwh` (re-verified by G1(b)), `N*` and `R*` (G3, one document), `φ` (G2). **PASS** iff
all four hold **and** none was selected by this session from a menu of candidates.
**FAIL ⇒ BRANCH II** — a fraction identified only by substituting a second free parameter is the
caiso-176 §1a DOF SUBSTITUTION again, and is reported as such.

---

## 5. THE VERDICT RULE — all branches fixed before the outcome is read

* **BRANCH I — IDENTIFIES.** G1 ∧ G2 ∧ G3 ∧ G4 ∧ G5 all PASS.
  ⇒ the identified adder is `452.6 × 1000 / N* × (1 − R*) × φ`, reported to the cent, and the A/B
  of §6 runs. The DOF ledger entry moves `identification: residual → derived` **only on
  promotion**.

* **BRANCH II — THE THIRD WALL.** G3 or G5 FAILS.
  ⇒ `battery_dispatch_adder` stays at **5.0**, unchanged. File the third wall with its instrument
  committed. **No arm, no solve, no bundle, nothing registered.** And state plainly, because it is
  the honest consequence: **all three of caiso-176's named exits are then closed, which makes
  `battery_dispatch_adder` a PERMANENT DECLARED-RESIDUAL DOF.** That is an **owner-level
  disclosure**, not a session failure, and it will be written as one.

* **BRANCH III-R — IDENTIFIED AND REFUTED.** G1 ∧ G2 ∧ G3 ∧ G5 PASS but **G4 FAILS**.
  ⇒ the split IS identified and the fraction stops being free — but the value it produces is
  refuted by caiso-101 and caiso-176. Report the number **at full magnitude**, do **not** arm it,
  do **not** re-derive to get under the screen, and record that the committed
  `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` is itself now contradicted by its own cited
  basis. No arm, nothing registered.

* **BRANCH III-N — NO INSTRUMENT.** G1 FAILS, or G2's S1-vs-S2 consistency check fails.
  ⇒ the ATB extract does not admit the decomposition the constant block claims for it. Report
  that, leave 5.0 unchanged, and record the corpus's cost so no later session re-spends it.

---

## 6. IF BRANCH I FIRES — the A/B, fixed now

* **Arm A — CONTROL.** The caiso-175 keeper recipe replayed unchanged **at this session's HEAD**.
  **MANDATORY, not optional**: caiso-175 measured incidental code drift at
  **+0.168 / +0.049 / +0.115 \$/MWh** on load-weighted mean LMP — **larger in every year than its
  own treatment** — so differencing Arm B against the keeper's *committed* metrics **would
  misattribute**. Reproduction is by **`scenario_config` identity, verified KEY-BY-KEY and
  FAIL-CLOSED** against `results/calibration/caiso175_tac_intake/run_config.json` (the
  `gen_caiso175_attestation.py` method) — **never** by trusting a remembered CLI string.
* **Arm B — TREATMENT.** Identical to Arm A but for **the one derived scalar**,
  `battery_dispatch_adder = <identified>`.
* **Arm B does NOT route the LP through `_degradation_cost_per_mwh`.** That remains forbidden
  (DO-NOT-REDO): it would couple the forecast entry screen into the dispatch objective, which are
  independent today. The identified value enters as **the single registered scalar** the keeper
  already carries.
* **Both arms: 2023 / 2024 / 2025 in ONE bundle** (rule 16), years sequential, arms sequential
  (rule 12), **both REGISTERED** (rule 15 — keeper and probe alike) with
  `legitimacy_diagnostics.json` generated **per bundle** so C8 stays SCORED.

### 6a. The caiso-101 throughput guard — REPORTED, and what it does and does not decide

The **two-sided ±15 % battery-only throughput guard** (model vs measured battery charge and
discharge TWh, each year, each leg) is **re-imposed as a REPORTED quantity** on every arm solved.
It is the gate that killed the last attempt on this parameter.

Pre-registered disposition, so it cannot be renegotiated afterwards:

* A breach does **not** revert the identified value. Rule 14 `[R-ACCURATE]` governs: a worse fit
  on an accurate input is a **discovered bug**, not grounds to restore an estimate that was
  silently compensating for it.
* **But a breach DOES escalate the promotion to the owner rather than the session taking it.**
  caiso-101 *rejected* on precisely this guard; reversing a prior session's pre-registered
  rejection is an owner-level act, not a session-level one. So: **if the guard breaches in any
  year on either leg, this session registers both arms, reports the identification as
  established, and escalates the promotion — it does not promote unilaterally.**
* If the guard does not breach, the session promotes on the rule-14 basis below.

### 6b. Promotion basis

* **Rule 14 `[R-ACCURATE]`** — a **DEGRADED criterion does NOT revert a correct measured input**.
* **C3a is a LIVE FAIL, so a C3a move is REPORTED, never the promotion's basis** (rule 1
  `[R-STRUCT]`). A measured input is not adopted because it moved the residual, and not rejected
  because it didn't. This is stated before any residual is seen.
* Promotion requires the keeper-lane duties: `frontend/data/backcast/keepers/CAISO.json` +
  `build_status.py --iso CAISO`, and the `calibration-keeper-auditor` on the shard edit. **No
  `calibration-complete.json` re-key duty arises** — CAISO does not hold `complete` (§0).

### 6c. `STORAGE_DEGRADATION_REPLACEMENT_FRACTION` itself — the scope rule, fixed now

The constant feeds **only** `storage.py:1609`, inside the **forecast-mode storage new-entry
screen**; it never enters the LP objective and never a backcast solve. Therefore:

* The shared constant is updated to the identified `F` **iff** BRANCH I fires **and** it is
  verified **inert for every backcast solve** (so neither arm's LP changes and the A/B stays
  isolating). Verification is performed and reported, not assumed.
* If it is **not** provably backcast-inert, it is **not touched in this session** — changing it
  would contaminate the A/B.
* Either way the change is **disclosed as a cross-ISO FORECAST-LANE effect** with a named
  follow-up for the forecast program. A CAISO calibration session does not silently re-price six
  ISOs' entry screens.

---

## 7. Governance fixed in advance

* **Rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]`** — **no price residual enters the derivation at
  any point.** Every gate in §4 is a property of published cost/warranty documentation. The
  identified value is adopted or refused on its provenance and the §3 screen, never on where it
  moves the residual.
* **Rule 5 `[R-NO-MAGIC]`** — the deliverable is exactly a citation for a value that has none.
* **Rule 14 `[R-ACCURATE]`** — §6a/§6b.
* **Rule 20 `[R-DOF]`** — the ledger entry is edited **only** on promotion. Under BRANCH II /
  III-R / III-N it stays `identification: residual`, 11 / 8, with the finding carrying the result
  rather than the attestation being silently rewritten.
* **Rule 21 `[R-FROZEN-DERIVE]`** — this is a **source-side** identification, not a residual-driven
  re-derivation. No parameter here re-derives because a residual moved.
* **Rule 24 `[R-REGISTRY]`** — the identified value enters through the existing registered
  `ScenarioConfig.battery_dispatch_adder` field and appears in `run_config.json`. No env knob, no
  per-plant dict, no `getattr` fallback.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing is transferred between ISOs. `battery_dispatch_adder` is
  per-ISO and only CAISO's is touched. §6c fences the one shared constant.
* **Rule 15** — any completed run is registered, keeper and probe alike. Under BRANCH II / III
  there is nothing to register because nothing is run.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025 in one bundle per arm. No single-year keeper.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only. Freeze untouched, no marker read or written.
* **Rule 27 `[R-PUSH]`** — this session is **Opus**. Any push touching a file ≥ 300 lines is
  blob-verified immediately after (fetch back, compare line count + hash).
* **Rule 28 `[R-MECH-MATRIX]` duties (b) + (e)** — the `battery_dispatch_adder` cell and the §5.2
  CAISO header are updated in **this same session**, whatever the branch.

## 8. Known-open, carried forward untouched

1. **The N–S congestion majority** — the model reproduces 5.2 / 2.4 / 2.9 % of the measured
   NP15−ZP26 basis. Named; no lever chartered; the N–S topology lever stays **FORBIDDEN**
   (caiso-164 §0/§6).
2. **C3a is an OPEN root-cause issue** (2024 +11.7 %, 2025 +14.8 %), not an accepted limitation.
   Its closure route is the **walled** hourly pumped-storage water state — an owner-level data
   question, not a session lever.
3. **ESCALATED TO THE OWNER, AGAIN — the CAISO outage re-audit is STILL OUTSTANDING.** CAISO's
   2023–2025 outage windows were regenerated on the current CAMPD detector (`intake_log`
   2026-07-24) and the re-audit that entry flagged has **still not been done**. It is a
   **precondition for spending 2022** and is on the path back to any `complete` re-declaration.
   This session does not work around it.
4. **`scripts/data/curate_dam_public_bids.py` cannot process a full CAISO year** (~14.3 GB
   extrapolated peak vs ~15 GB RAM; measured at caiso-178). Filed, unfixed; it needs a
   data-contract session because it touches the frozen `clean_io.write_clean` seam. Nothing in
   this session depends on it.
