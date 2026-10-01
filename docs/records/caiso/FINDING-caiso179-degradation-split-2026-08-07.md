# FINDING — caiso-179: the cell-vs-system split **IDENTIFIES**, and the value it produces is **REFUTED**. Exit 3 is SPENT. All three exits on `battery_dispatch_adder` are now closed.

**Outcome: BRANCH III-R of the pre-registered verdict rule — IDENTIFIED AND REFUTED.**
`battery_dispatch_adder = 5.0` stays exactly as it is, and
`STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` stays exactly as it is.

**NO LP, NO SOLVE, no arm, no bundle, nothing registered — because nothing was run.** DOF ledger
unchanged at `n_entries` 11 / `n_residual` 8. Keeper unchanged at
`2026-08-06-caiso-175-tac-intake` (**NOT-YET**, 8 criteria, C3a the sole FAIL).
`holdout-freeze.json` and `calibration-complete.json` UNTOUCHED. 2023–2025 only — and in fact no
year was solved at all.

Pre-registration: `PRECHECK-caiso179-degradation-split-2026-08-07.md` (pushed and blob-verified
**before any source value was read**; 457 lines, sha256 `0a3aa1c6…`).
Instrument: `scripts/probes/_caiso179_degradation_split.py`.
Record: `_caiso179_degradation_split.json`.
**Re-check cost:** `uv run python scripts/probes/_caiso179_degradation_split.py`, ~5 s, no network.

---

## 0. Headline

Four things, in the order they were found.

1. **The split IDENTIFIES — exactly, and better than expected.** φ, the share of installed
   $/kWh that is degrading, energy-scaling content, is **0.742426**. It is not a regression
   estimate: NREL's ATB *constructs* its storage duration classes as
   `Total ($/kWh) = Energy ($/kWh) + Power ($/kW) / Duration` (NREL/TP-6A40-85332 p. 3), so a
   two-parameter fit **inverts that construction** — max relative residual **5.5 × 10⁻¹⁶**,
   machine precision, on both on-disk file families.
2. **The other factor identifies too, from the one source that carries it** — PNNL-33283
   Table 4.2 (LFP), and its end-of-life **threshold cancels exactly** under PNNL's own
   linear-fade model, so no convention was chosen: `0.20/1,920 ≡ 0.40/3,840`.
3. **And the number it produces is REFUTED.** The pre-registered headline lands at
   **\$28.00 – \$35.00/MWh** against a \$15.00 admissibility screen. **12 of the 15 cells** in
   the full φ × depth-of-discharge grid fail; the incumbent \$22.63 that caiso-176 refuted
   *a fortiori* sits **below** the identified range. The identification makes the ATB route
   **worse**, not admissible.
4. **The exit's own named primary source refutes the FORMULA'S FORM, not just its value.**
   caiso-176 named "NREL ATB augmentation-cost tables" first. There is no such table. ATB 2024
   and its basis **explicitly decline** to charge degradation per MWh:
   > *"assume no variable O&M (VOM) costs. All operating costs are instead represented using
   > fixed O&M (FOM) costs. The FOM costs include battery augmentation costs, which enables the
   > system to operate at its rated capacity throughout its 15-year lifetime."*

   **So exit 3 is SPENT AND REFUTED, not walled** — and that is a stronger closure than a wall,
   because it means no later session should re-attempt this route at all.

---

## 1. What was asked, and what the pre-registration fixed before any number was read

`STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25`'s own constant block called it *"a modeling
simplification … **tunable**"*. caiso-176 §1a ruled that routing the LP through
`_degradation_cost_per_mwh` while that factor is a declared tunable is **DOF SUBSTITUTION, not
closure**, and named an *identified* cell-versus-system split as the repair. After caiso-178
spent and closed the public-bid exit, that was the only live exit left.

The pre-registration fixed, in advance: the arithmetic (read off the code's own comment, not
chosen here), the ranked candidate sources for each factor, the \$15 admissibility screen as a
**refutation test rather than a truth claim**, five gates, and **four** verdict branches —
including a separate IDENTIFIED-AND-REFUTED branch specifically so a refutation could not later
be relabelled as a wall. That branch is the one that fired.

### 1a. The arithmetic is the CODE'S

The committed block declares the fraction's intent in two clauses — *"only the cell stack
degrades, not the power electronics / BOS"* and *"warranties run to ~80% retention"* — i.e.
`F = φ × (1 − R)`. Over `N` rated cycles a battery of capacity `E` discharges `N × E` MWh (the
code's own convention, since it computes `capex_per_mwh / cycles`) and fades to `R × E`; holding
rated capacity by augmentation costs `(1 − R) × E × φ × capex_per_kwh`. `E` cancels:

```
$/MWh = capex_per_kwh × 1000 × φ × (1 − R) / N
```

Only **`(1 − R)/N`** enters. That matters in §4.

---

## 2. G1 — the ATB cell, and why its linearity is a CONSTRUCTION, not a fit

**PASS.** Fitting `CAPEX(d) = p + e·d` over ATB 2024 `Utility-Scale Battery Storage`, Moderate,
2026, across all five duration classes (2/4/6/8/10 Hr):

| | value |
|---|---:|
| power component `p` (raw ATB $) | **427.417586 \$/kW** |
| energy component `e` (raw ATB $) | **307.994138 \$/kWh** |
| max abs residual | **0.00000000** |
| max **relative** residual | **5.481 × 10⁻¹⁶** |

This is not luck. NREL/TP-6A40-85332 states the construction outright: *"To estimate the costs
for other storage durations … we assign separate energy costs and power costs such that
**Total Cost (\$/kWh) = Energy Cost (\$/kWh) + Power Cost (\$/kW) / Duration (hr)**"*. The fit
**recovers ATB's own two published parameters**, which is why the residual is zero to machine
precision. It also independently confirms the claim `capacity_market.py:337-341` already carried
("ATB's own EXACTLY-linear power/energy cost split … residual 0").

**G1(b) — one common deflator, checked against FOUR committed constants, not one.** A single
scalar `k = 1.090940` (the 2026\$ conversion) maps the raw fit onto the committed
`STORAGE_TECHS`:

| committed constant | ATB raw × k | committed | agreement |
|---|---:|---:|---|
| `li_ion_4hr.capex_per_kw` | 1810.30 | 1810.3 | exact by construction of `k` |
| `li_ion_8hr.capex_per_kw` | 3154.31 | 3154.3 | **k agrees to 4 × 10⁻⁶ relative** |
| `li_ion_4hr.fom_per_kw_yr` | 40.935 | 40.9 | 0.09 % |
| `li_ion_8hr.fom_per_kw_yr` | 73.351 | 73.4 | 0.07 % |

The FOM rows are an **out-of-construction** check: `k` was solved on CAPEX and reproduces FOM
anyway. So φ below is computed against exactly the denominator the LP formula divides. Both
on-disk file families (`atb_2024_*`, `atb_2024v4_*`) are identical for storage and agree to 12
decimal places.

---

## 3. G2 — φ IDENTIFIES, and the independent brackets sit where physics requires

**PASS.** φ = `e × 4 / CAPEX(4h)` = **0.742426**. Equivalently, the deflated ATB energy
component is **336.02 \$/kWh** of the committed 452.6 \$/kWh bundled cost.

The pre-registration declared φ_energy the **point estimate, not an upper bound**, and declared
*why*, before any number: augmentation does not install naked cells — it adds **modules in racks,
in enclosures, with thermal management, DC cabling and the labour to install them**, which is
precisely the content that scales with duration and precisely what the power block excludes. The
code's clause "not the power **electronics** / BOS" reads as *not the power-block electronics and
power-scaling BOS*, which is the `p` term.

**S2 brackets** — NREL/TP-7A40-83586 (Ramasamy et al., Q1 2022), utility-scale standalone
60 MW/240 MWh 4-hour system, Table 11 + Figure ES-2 narrative:

| | MSP (2021\$) | MMP (2021\$) |
|---|---:|---:|
| Li-ion battery price (bare pack) | \$137/kWh | \$165/kWh |
| Battery cabinet (packs + containers + thermal mgmt + fire suppression) | \$226/kWh | \$270/kWh |
| **Total installed** | **\$394/kWh** | **\$446/kWh** |
| ⇒ φ bare pack | **0.3477** | **0.3700** |
| ⇒ φ cabinet | **0.5736** | **0.6054** |

**The ordering is exactly what the physics demands and is a real test the reading could have
failed:** cells ⊂ cabinet ⊂ energy-scaling total (which adds the energy-proportional share of
EPC, developer overhead, contingency, sales tax and profit). `0.348 < 0.605 < 0.742`. The
consistency gate `φ_S2 ≤ φ_S1` **PASSES**. Two independently-built NREL products — a top-down
duration construction and a bottom-up component model — nest correctly.

---

## 4. G3 — the cycle-life/retention pair: THREE of the four ranked sources carry none

The pre-registration ranked four sources and required a **complete `(N, R)` pair from ONE
document**, never assembled across two.

### 4a. R1 and R2 — ATB 2024 and its own basis carry NEITHER, and say the opposite

**ATB 2024, Utility-Scale Battery Storage** (verbatim):

> *"(Cole and Karmakar, 2023) assume no variable O&M (VOM) costs. All operating costs are instead
> represented using fixed O&M (FOM) costs. **The FOM costs include battery augmentation costs,
> which enables the system to operate at its rated capacity throughout its 15-year lifetime.**
> FOM costs are estimated at 2.5% of the capital costs in \$/kW."*

**NREL/TP-6A40-85332** (its basis) is more explicit still:

> *"The VOM is often taken to be zero or near zero, and we have adopted **zero** for the VOM. This
> VOM is defined to coincide with an assumed **one cycle per day** … We have allocated **all**
> operating costs (at the one-cycle-per-day level) to the FOM. By putting the operations and
> maintenance costs in the FOM rather than the VOM **we in essence assume that battery performance
> has been guaranteed over the lifetime, such that operating the battery does not incur any costs
> to the battery operator.** … We have adopted a FOM value from the high end and assume that the
> FOM cost will counteract degradation such that the system will be able to perform at rated
> capacity throughout its lifetime. … If the battery is operating at a much higher rate of
> cycling, then this FOM value might not be sufficient to counteract degradation."*

The 2025 update (NREL/TP-6A40-93281) repeats it word for word. **No cycle life. No retention. No
per-MWh augmentation table at any vintage.** This is §0 headline 4: the exit's named primary
source refutes the *form* of the formula.

### 4b. R3 — no primary warranty document exists in the public record

Searched and not found. What is available is vendor and consultancy summaries quoting **ranges**
— 4,000–10,000 cycles, 70 % or 80 % end-of-life retention. A range is exactly the free parameter
this session exists to remove; adopting a point from it would be the caiso-176 DO-NOT-REDO item
in a new costume. **Recorded as a miss, not worked around.**

### 4c. R4 — PNNL-33283 carries the pair, and its EOL THRESHOLD CANCELS

**PASS on R4.** PNNL-33283 §6 item (v) and Table 4.2 footnote 11: *"End of life is when available
energy at full charge is **60 %** of rated energy."* Table 4.2, LFP:

| DOD provided | avg DOD | cycles to EOL | 100 %-DOD equiv | **corrected equiv (× avg DOD)** | (1−R)/N per full-E discharge |
|---:|---:|---:|---:|---:|---:|
| 100 % | 80 % | 4,800 | 4,800 | **3,840** | 1.0417 × 10⁻⁴ |
| 80 % | 70 % | 6,000 | 4,800 | **4,200** | 9.5238 × 10⁻⁵ |
| 60 % | 60 % | 8,000 | 4,800 | **4,800** | 8.3333 × 10⁻⁵ |
| 30 % | 30 % | 32,000 | 9,600 | 9,600 | — reported, outside the headline span |
| 5 % | 5 % | 192,000 | 9,600 | 9,600 | — reported, outside the headline span |

**The corrected column is the model's own unit, not a choice.** The code computes
`capex_per_mwh / cycles`, so one "cycle" must discharge one full `E`; PNNL's corrected column is
`cycles × average DOD`, i.e. cumulative discharge in units of rated energy. Exactly the same
object.

**And the end-of-life threshold cancels exactly.** PNNL's separate 80 %-retention reading of the
same row (Table 4.3: 2,400 cycles at 80 % average DOD, *"halfway"* to the 60 % EOL) gives
`0.20 / (2,400 × 0.80) = 1.0416667 × 10⁻⁴` — **bit-identical** to `0.40 / 3,840`. So the "60 % vs
80 % retention" question, which looks like it should dominate the answer, **has no effect on it**.
Verified in the record (`eol_threshold_invariance.identical = true`).

---

## 5. G4 — THE NUMBER, and it FAILS the screen on 12 of 15 cells

`adder = 452.6 × 1000 × φ × (1−R)/N`. The full grid, every φ variant × every headline DOD row:

| φ basis | DOD 100 % | DOD 80 % | DOD 60 % |
|---|---:|---:|---:|
| **S1 ATB energy-scaling — 0.742426 (PRE-REGISTERED HEADLINE)** | **\$35.00** | **\$32.00** | **\$28.00** |
| S2 cabinet MMP — 0.6054 | \$28.54 | \$26.09 | \$22.83 |
| S2 cabinet MSP — 0.5736 | \$27.04 | \$24.73 | \$21.63 |
| S2 bare pack MMP — 0.3700 | \$17.44 | \$15.95 | \$13.95 ✓ |
| S2 bare pack MSP — 0.3477 | \$16.39 | \$14.99 ✓ | \$13.11 ✓ |

Screen = \$15.00. **Headline span \$28.00 – \$35.00. G4 FAILS.**

For scale: the keeper carries **\$5.00**; caiso-101's *solved* ±15 % throughput guard rejected
**\$14.25**; caiso-176 refused **\$22.63** *a fortiori*. **The identified value is above every one
of them.** Re-expressed against the code's own committed `cycles = 5000`, the headline implies
`F = 0.309 – 0.387` — so the incumbent **0.25 is 19–35 % LOW, not high.**

**An independent corroboration of the magnitude, from the ATB's own numbers.** Converting ATB's
augmentation-inclusive FOM into a throughput charge at ATB's own assumed duty (one cycle/day,
4 h ⇒ 1.46 MWh per kW-yr) gives **\$28.04/MWh** on the deflated 4-hour FOM. That is the *whole*
FOM, so it bounds the augmentation part from above — but it lands squarely inside the identified
\$28–\$35 band. **However you slice ATB's cost structure, a per-MWh degradation charge built from
it is an order of magnitude above the keeper's \$5.00.** Reported as a contrast; it is emphatically
**not** used as an estimator, because ATB's whole point is that this cost is *not* per-MWh.

---

## 6. G5 — FAILS, and it is an INDEPENDENT reason the exit does not close

Even setting the value aside, the identification is **not a clean DOF closure**, and this is
reported rather than glossed. PNNL's cycle life is a **function of depth of discharge**, and the
LP has no DOD dimension — `_degradation_cost_per_mwh` divides by a single scalar. Selecting a DOD
row is a residual free choice, i.e. **a new degree of freedom appears where the old one was
removed**. It spans \$28.00 – \$35.00 on the headline φ.

**The verdict does not depend on it** — every row fails the screen — which is why BRANCH III-R
fires cleanly. But it means that *even if the value had been admissible*, exit 3 would have
delivered a narrowed DOF rather than a closed one. Two independent reasons, either sufficient.

---

## 7. REPORTED AGAINST INTEREST — the three cells that DO clear, and why they are not the answer

Three of fifteen cells clear \$15: the **bare-pack** φ at the shallower DOD rows, \$13.11 / \$14.99
/ \$13.95. They are not adopted, and the reasons were fixed **before** the numbers were read, not
after:

1. **The pre-registration named S1 the headline and S2 a bracket**, explicitly "never substituted
   for the headline, **whichever way they land**". Switching to S2 now because S1 failed the screen
   is choosing an estimator by its answer — the exact failure mode the pre-registration exists to
   block.
2. **A bare-pack φ is physically wrong for augmentation.** Cells do not install themselves. The
   augmentation cost is a delivered, racked, thermally-managed, commissioned module — PNNL's own
   §6.1.5 augmentation methodology costs *"DC SB rack augmentation"*, not cell purchase. The pack
   share of the cabinet alone is 0.606/0.611 (MSP/MMP), so the non-cell energy-scaling content is
   ~40 % of the hardware before any soft cost.
3. **They still refute the incumbent anyway.** The most favourable cell in the entire grid is
   **\$13.11**, which is **2.6 ×** the keeper's \$5.00 and above caiso-101's rejected \$14.25 only
   by a hair. There is no reading of these sources — none — that lands anywhere near 5.0.

That last point is the honest summary of the whole grid: **the sources do not support the
incumbent either.** They are consistent only with a value the model has already measured to be
unusable.

---

## 8. What this establishes, and what it does not

**ESTABLISHED — from primary sources, with no model in the loop:**

* The **cell-versus-system split is identified**: φ = **0.742426** (ATB's own energy share,
  recovered exactly), bracketed below by Ramasamy's cabinet (0.574/0.605) and bare-pack
  (0.348/0.370) shares, all nesting correctly.
* The **degradation rate is identified** and is **end-of-life-threshold invariant**:
  1.0417 × 10⁻⁴ of rated capacity per full-energy discharge at 100 % DOD (PNNL-33283 LFP).
* `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` is **not merely uncited — its stated citation
  does not exist.** Neither half ("NREL ATB augmentation costs" / "LFP warranty cycle life")
  names a document that carries the quantity. **Corrected in the constant block this session**;
  the value is left at 0.25 (see below).
* **A rule-14 `[R-ACCURATE]` finding on `cycles = 5000` itself.** The committed constant is
  attributed to "NREL Annual Technology Baseline 2024" in `docs/parameter-citations.md`, but ATB
  publishes no cycle life at all. Against the only primary pair, 5,000 is **2.6 ×** PNNL's 1,920
  full-energy-equivalent discharges to 80 % retention. Named here; **not changed**, because it is
  a forecast-lane entry-screen constant (see §9a) and changing it belongs to that lane.

**NOT ESTABLISHED, and this is why nothing moves:**

* **That any of these numbers belongs in the LP.** The identified value is refuted twice over in
  this ISO, and the source that defines the object says it should not be a per-MWh charge at all.
* **That the incumbent \$5.00 is right.** It is not corroborated by this session — it is simply
  **not refuted by it**, and it remains `identification: residual` in the DOF ledger.

---

## 9. EXIT 3 IS SPENT — and `battery_dispatch_adder` is now a PERMANENT DECLARED-RESIDUAL DOF

**This is the owner-level disclosure this session owes, stated plainly rather than buried.**

caiso-176's three named exits, final state:

| exit | status |
|---|---|
| 1. Per-resource CAISO Storage-DEB cycle-cost (`CD`) filings | **CLOSED — confidential by tariff construction.** A disclosure wall, not a fetch task. Unchanged since caiso-176. |
| 2. A finer public bid-price grain (OASIS `PUB_DAM_GRP`) | **SPENT AND CLOSED at caiso-178.** Fetched at full coverage; fails structurally — a storage discharge bid encodes dispatch intent, not cost. |
| 3. An identified cell-vs-system split replacing the 0.25 fraction | **SPENT AND REFUTED at caiso-179 (here).** The split identifies; the value it produces is \$28–\$35/MWh, refuted; and the ATB refutes the formula's form. |

**All three are closed. There is no fourth exit named, and this session does not invent one.**
The consequence, stated without hedging: **`battery_dispatch_adder = 5.0` is a permanent
declared-residual degree of freedom.** It cannot be identified from any instrument this program
can reach — CAISO publishes the object only in confidential per-resource filings; the public bid
channel measures a different object; and the engineering-cost channel, now derived end to end,
produces a value the model has already measured to be unusable.

**That is an owner-level disclosure, not a session failure.** What it changes: the keeper's DOF
ledger entry keeps `identification: residual` **permanently**, and its `root_cause` text
(*"open item to re-derive from those"*) is now known to be unachievable by **every** route it
named. The ledger is the keeper's attestation, so it is recorded here rather than silently
rewritten — but a future keeper-lane session should re-word that entry to say *permanent declared
residual*, not *open item*.

### 9a. Why the shared constant was NOT re-priced here

`STORAGE_DEGRADATION_REPLACEMENT_FRACTION` feeds **only** `storage.py:1609`
(`estimate_storage_revenue` inside the new-entry build loop). It never enters the LP objective
and never a backcast solve — so it is **byte-inert for every CAISO backcast**, and equally, no
backcast could validate a change to it. Re-pricing it from 0.25 to the identified 0.309–0.387 is
a **FORECAST-lane act with six-ISO reach**, and the identification still carries the §6 DOD
selection, so it is not a clean drop-in. **Chartered for the forecast lane with the numbers ready;
not taken by a CAISO backcast session.** The block's *citation* is corrected in place (the value
is untouched), because leaving an attribution we have just demonstrated does not exist is what
rule 5 `[R-NO-MAGIC]` forbids.

---

## 10. DO-NOT-REDO — carried forward, plus this session's

**Carried unchanged from caiso-176 §5 and caiso-178 §8:** any value **> \$15**;
`caiso_storage_as_reservation` as this parameter's replacement (INERT at caiso-74, family refuted
at caiso-127/129); re-fetching or re-deriving `PUB_DAM_GRP` for this parameter; adopting \$6.00 /
\$5.00 or any modal bin of the first-discharge-rung distribution; reading the first discharge rung
as a marginal cost at all; treating ≤ \$15 as a strict upper bound on marginal cost (it is
revealed conduct); and picking a value inside (0, 15] **because** it sits inside the bound.

**Added here:**

* **Re-deriving the degradation adder from NREL ATB, NREL cost benchmarks, PNNL-33283, or LFP
  warranty documentation.** Done end to end, at machine precision, with the gates pre-registered.
  The answer is \$28–\$35/MWh and it is refuted. New evidence would have to be a *different
  object*, not a better derivation of this one.
* **Reading the ATB as a source of per-MWh augmentation cost.** It publishes none, by an
  explicit and repeated methodological choice (VOM = 0, all augmentation in FOM). Quoting "NREL
  ATB augmentation costs" as the basis for a \$/MWh number is citing a document that says the
  opposite.
* **Adopting the bare-pack φ (0.348/0.370) to get under the screen** (§7). It is the
  post-hoc-estimator-selection failure mode, and it is physically wrong for augmentation.
* **Re-arming `_degradation_cost_per_mwh` in the LP.** Still forbidden, now for a second and
  stronger reason: the fraction is no longer merely a declared tunable, it is a **measured**
  factor whose measured value produces a refuted adder.
* **Treating the DOF ledger's `battery_dispatch_adder` entry as an open item.** It is a
  permanent declared residual (§9).

---

## 11. Governance

* **Rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]`** — **no price residual, keeper metric or model
  output entered the derivation at any point.** Every gate is a property of published cost and
  cycle-life documentation. Nothing was adopted because it moved a residual, and nothing was
  rejected because it did not.
* **Rule 5 `[R-NO-MAGIC]`** — the session's one code change is a **citation correction** on a
  constant whose stated source does not carry the quantity. Value byte-unchanged.
* **Rule 14 `[R-ACCURATE]`** — reached, and it does **not** command an input swap here: the
  accurate derivation produces a value refuted by two prior CAISO instruments, and the
  pre-registered BRANCH III-R disposition (fixed before the number was read) is to report at full
  magnitude and change nothing. The `cycles = 5000` discrepancy is named, not buried.
* **Rule 15** — **nothing to register.** No run was produced, so no bundle, no sidecar, no
  dashboard entry. Same disposition as caiso-176 and caiso-178.
* **Rule 16 `[R-ALLYEARS]` / rule 22 `[R-HOLDOUT]`** — no year was solved at all. The freeze and
  both markers are untouched; no authorization was needed or taken. **CAISO does not hold
  `complete`** (`withdrawn` 2026-08-06) and this session does not re-break that.
* **Rule 20 `[R-DOF]`** — ledger unchanged at 11 / 8, `identification: residual`. §9 records the
  re-wording a future keeper-lane session owes it.
* **Rule 21 `[R-FROZEN-DERIVE]`** — source-side identification, not residual-driven
  re-derivation. No parameter re-derived because a residual moved.
* **Rule 24 `[R-REGISTRY]` / rule 25 `[R-ISO-SCOPE]`** — no new tunable, no ISO crossing. The one
  shared constant that could cross was deliberately **not** re-priced (§9a).
* **Rule 27 `[R-PUSH]`** — Opus. Every push touching a file ≥ 300 lines blob-verified immediately.
* **Rule 28 `[R-MECH-MATRIX]` duty (b)** — the `battery_dispatch_adder` cell and the §5.2 CAISO
  header are updated in this same session.

---

## 12. Known-open, carried forward

1. **The N–S congestion majority** — the model reproduces 5.2 / 2.4 / 2.9 % of the measured
   NP15−ZP26 basis. Named; no lever chartered; the N–S topology lever stays **FORBIDDEN**
   (caiso-164 §0/§6).
2. **C3a is an OPEN root-cause issue** (2024 +11.7 %, 2025 +14.8 %), not an accepted limitation.
   Its driver is the model's unrestrained pumped-storage pumping (FINDING-caiso140 §B) and its
   closure route is the **walled** hourly PS water state — an owner-level data question, not a
   session lever. `caiso_ps_charge_shape_anchor` stays `G`.
3. **ESCALATED TO THE OWNER FOR THE SECOND SESSION RUNNING — the CAISO outage re-audit is STILL
   OUTSTANDING.** CAISO's 2023–2025 outage windows were regenerated on the current CAMPD detector
   (`intake_log` 2026-07-24) and the re-audit that entry flagged has still not been done. It is a
   **precondition for spending 2022** and is on the path back to any `complete` re-declaration.
   This session did not touch it and did not work around it.
4. **`scripts/data/curate_dam_public_bids.py` cannot process a full CAISO year** (~14.3 GB
   extrapolated peak vs ~15 GB RAM; measured at caiso-178). Filed, unfixed; needs a data-contract
   session because it touches the frozen `clean_io.write_clean` seam.

**CAISO's in-model lever queue remains EMPTY, its one FAIL remains walled, and its last free
parameter is now permanently residual.** The next CAISO move is an owner-level data question —
the hourly pumped-storage water state for C3a, and the outage re-audit — not a session lever.
Stated plainly rather than dressed up as a queue entry.
