# FINDING — caiso-251: the CAISO gas offer was carrying **NEISO's** functional form. Removing it restores the fuel coupling CAISO's own OASIS record measures — armed, the fixed-margin form leaves **CT_PEAKER at 0.53 of its own physical fuel sensitivity** against a measured 0.9–1.0, and flattens CC and CT onto nearly one slope. **C3a (LOAD-BEARING) FAIL → PASS in all three years; C4 (SUPPORTING) PASS → FAIL on one cell.** Determination stays NOT-YET, but the outstanding failure drops a tier. **PROMOTED** on the basis registered before any measurement, with C3a excluded in both directions. **5 of 10 predictions FALSIFIED.**

**Session caiso-251, 2026-09-05.** Branch
`claude/caiso-251-backcast-calibration-7tci3e` off `main` `ee7754c1`; solve
basis `90b2ef51`. Keeper **`2026-09-05-caiso-246-b1-spot` →
`2026-09-05-caiso-251-b1-nomargin`** (bundle `caiso251_arm_nomargin`).
Pre-registration `PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md` +
Addenda A and B, each pushed to `origin` before the stage it governs.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no `complete`/`final` marker; holdout
freeze ACTIVE.

---

## §1 — THE OBJECT AND THE ARM

Queue item A (the CC-hot / CT-cold split) taken at its **functional form**.

The prior keeper armed `gas_offer_net_revenue_margin`, which prices every CAMPD
gas tranche carrying a measured physical basis as

```
offer = phys · HR_base · fuel(t)  +  (mult − phys) · HR_base · anchor
```

so the above-physical markup is a **fuel-INVARIANT $/MWh margin** identified at
a $4.7964/MMBtu anchor — 1,269 / 1,274 / 1,279 tranches at a median fixed
margin of $14.37/MWh. **That form's identification is NEISO's** (the 2022
holdout rotation, neiso-45/46/47). Two committed CAISO findings contradict it
for CAISO and neither had ever been charted:

* **caiso-242 §3.5** — on `caiso_offer_curve_measured.json`'s own per-year band
  multipliers, the measured multiplier is **FLAT across a 1.93× fuel swing**
  (CT_PEAKER `econ_low` range **0.013** against the **0.2775** the armed
  decomposition requires — **21.3×**). A multiplier flat in fuel is the
  signature of the **multiplicative** form.
* **caiso-229 §5** — the model CC floor couples to the CA citygate at Theil-Sen
  **2.18 / 2.18 / 4.34 MMBtu/MWh** against CAISO's **MEASURED DAM body coupling
  of 6.7–7.4**: **UNDER-coupled**, *"because the affine measured-marginal-HR +
  fixed-margin form is ALREADY armed"*. caiso-229 named the cause and did not
  pursue it.

**The arm is one flag: `--no-gas-offer-margin`.** Zero new parameters, zero new
fields; the anchor is **REMOVED** (rule 24 `[R-DELETE]`). Under the armed
`caiso_offer_surface_measured` the restored form is `mult · HR_base · fuel(t)`
with `mult` the **measured OASIS** multiplier — the form the record identifies.
Rule 14 `[R-ACCURATE]` (prefer the measured representation), rule 25
`[R-ISO-SCOPE]` (an out-of-ISO identification is not evidence for this ISO) and
rule 1 `[R-STRUCT]` carry the admissibility. **Per-year measured multipliers are
rule-13 inadmissible** (a same-year measured OUTCOME pin, PREREG-miso146 §9) and
were not proposed even though they sit in the same artifact.

---

## §2 — PHASE 0 (ZERO LP): THE STRUCTURAL RESULT

Two on-recipe `fleet_only` rebuilds differing in ONE kwarg.

**G-COUPLE — the load-bearing structural gate, whose failure would have spent
NO solve — PASSES in all three years**: the disarmed CC_REGULAR econ Theil-Sen
coupling is **6.719 MMBtu/MWh**, inside the pre-registered **[6.0, 8.0]** and
inside the measured **6.7–7.4**.

The sharper statement is per class, as a ratio to each class's **own** measured
base heat rate (CC 7.442, CT 10.862), against CAISO's measured DAM body
coupling of **0.9–1.0 × base HR**:

| coupling ÷ own base HR | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| CC_REGULAR armed → disarmed | 0.754 → **0.903** | 0.810 → **0.903** | 0.810 → **0.903** |
| CT_PEAKER armed → disarmed | **0.526** → 0.877 | **0.559** → 0.932 | **0.532** → 0.919 |

**Armed, the fixed-margin form leaves CT at roughly HALF its physical fuel
sensitivity and flattens CC and CT onto nearly the same absolute slope**
(5.6–6.1 MMBtu/MWh) despite base heat rates of 7.44 and 10.86. Disarmed, they
separate to 6.72 and 9.98 — each ≈ 0.88–0.93 × its own base HR. **That
asymmetry is the CC-hot / CT-cold split's mechanism, measured from CAISO's own
bid record rather than from the residual.**

**G-IDENT PASSES**: the delta *is* `(mult − phys)·HR_base·(fuel − anchor)` —
the implied per-tranche `(mult − phys)·HR_base` varies across hours by at most
**4e-12 MMBtu/MWh**. **G-FOOTPRINT**: zero non-gas tranches move.

Offer deltas (capacity-weighted, $/MWh): 2023 is **positive** (44.9 % of hours
sit above the anchor) at CC econ **+1.47**, CT econ **+4.18**; 2024 CC **−2.08**,
CT **−8.31**, CT_CHP **−10.44**; 2025 CC **−1.63**, CT **−6.21**.

---

## §3 — THE SOLVE

| criterion | tier | keeper | **arm** |
|---|---|---|---|
| `price_mean` (C3a) | **load-bearing** | FAIL | **PASS** |
| `fuelmix` (C1) | load-bearing | PASS (12/12, free 8/8) | PASS (12/12, free 8/8) |
| `sysvol` (C2) | load-bearing | PASS | PASS |
| `price_shape` (C3b) | load-bearing | PASS | PASS |
| `dispatch_corr` (C4) | **supporting** | PASS | **FAIL** |
| `price_tail` (C3c) | supporting | CAVEAT | CAVEAT |
| `governance` (C6) | protective | PASS | PASS |
| `forced_share` (C8) | protective | PASS | PASS |
| DOF ledger | — | 9 entries / 6 residual | 9 entries / 6 residual (**unchanged**) |
| **determination** | | **NOT-YET** (load-bearing) | **NOT-YET** (supporting) |

**C3a**, keeper → arm: **+3.91 / +12.33 / +11.45 % → +4.83 / +9.44 / +9.35 %**
(model LW 56.29/38.92/38.36 → 56.79/37.92/37.64 against actual
54.17/34.65/34.42). All three years inside ±10 %.

**C4 is the cost, and it is one cell**: 2025 gas fleet hourly **NRMSE
0.298 → 0.305** against a **≤ 0.30** tolerance, with **r 0.872 → 0.870**. 2023
(0.283 → 0.285) and 2024 (0.266 → 0.264) still PASS. The keeper sat 0.002 inside
the boundary; the arm sits 0.005 outside. **It fails, and the margin is not an
argument** — it is reported as a real supporting-tier regression.

**Dispatch** (arm − keeper, TWh): CT_PEAKER **+0.079 / +0.734 / +0.414**,
CC_REGULAR +0.184 / +0.947 / +0.740, import −0.213 / −1.393 / −1.083, ST_GAS
−0.055 / −0.336 / −0.095. The caiso-244 **CT_PEAKER volume miss narrows from
−3.582 to −2.848 TWh** in 2024 — a 20 % cut in the ISO's largest single
fuel-mix error, achieved by **removing** a parameter.

**G-REPRO**: the full arm's 2024 reproduces the (deleted) screen bundle's 2024
to **4e-5** on the load-weighted price, CT_PEAKER energy and all 13 class
energies — the replay path is deterministic and the screen was faithful.

---

## §4 — PREDICTIONS, SCORED AGAINST INTEREST

| # | registered | measured | verdict |
|---|---|---|---|
| P-1 | G-IDENT ≤ 1e-6 | 4e-12 | **HOLDS** |
| **P-2** | 1,285 compressed tranches in 2025 exactly; zero non-gas | **1,279** touched; zero non-gas ✓ | **FALSIFIED** on the count leg (§5.2) |
| **P-3** | CC econ capacity-weighted delta in **[−3.00, −9.00]** for 2024/2025 | **−2.08 / −1.63** | **FALSIFIED** — the arm is SMALLER on CC than I registered |
| P-4 | 2023 delta positive in ≥ 5 % of hours; ≥ $2 less negative than 2024 | 44.9 %; +1.47 vs −2.08 | **HOLDS**, and stronger |
| P-5 | G-COUPLE in [6.0, 8.0] all years | 6.719 | **HOLDS** |
| **P-6** | the solve **OVERSHOOTS** — 2024 or 2025 lands NEGATIVE | +9.44 / +9.35 | **FALSIFIED** — no overshoot at all |
| **P-7** | 2023 gets worse **AND FAILS** its band | worse (+3.91 → +4.83) but **PASSES** | **FALSIFIED** as the registered conjunction |
| **P-8** | CT_PEAKER 2025 rises ≥ 0.5 TWh | **+0.414** | **FALSIFIED** |
| P-9 | at least one non-C3a criterion regresses | `dispatch_corr` | **HOLDS** |
| P-10 | determination stays NOT-YET | NOT-YET | **HOLDS** |

**5 hold, 5 falsified** — and **three of the five falsifications (P-6, P-7, P-8)
ran in the ARM'S FAVOUR**: I registered that overshoot was the live risk and that
a currently-passing 2023 would break, and neither happened. That is reported as a
**hazard, not a credit** (§5.1).

---

## §5 — DISCLOSURES AGAINST INTEREST

### §5.1 — My registered predictions were pessimistic, and the arm beat them. That is a hazard.

P-3, P-6 and P-7 all said this arm would be *bigger and more damaging* than it
was. They were wrong in the direction that flatters the arm. A pre-registration
whose uncomfortable predictions all fail in the favourable direction is weaker
evidence than one whose predictions bind, because it means my prior was
mis-calibrated rather than that the arm was tested hard. The **binding** evidence
here is G-COUPLE and G-IDENT — both computed before any solve, both with
falsifiers that would have killed the session — and P-9, which predicted a
collateral regression and got one.

### §5.2 — P-2 is falsified and I do not fully know why

The keeper's own 2025 solve log says **1,285 tranches compressed**; the rebuild
finds **1,279** with a non-zero delta. The 6-tranche gap is consistent with
tranches whose `mult == phys` exactly (a neutral band compresses to a zero
markup), but **I did not verify that** and it is recorded as unexplained rather
than asserted. The load-bearing check is G-IDENT, which passes on all 1,279.

### §5.3 — G-SCREEN-C was NOT EVALUABLE as I wrote it

Addendum A's third screen leg — "no non-C3a **scored** criterion for 2024 flips
PASS → FAIL" — cannot be evaluated on a screen bundle, because
`calibration_verdict.py` resolves only **registered** runs and the same addendum
forbids registering a screen (rule 16). That is a defect in my own gate, filed
as such and not silently swapped for the proxy I ran instead (a C1 fuel-mix
error comparison: net |error| improved 0.511 TWh with CC_REGULAR the one class
that worsened). The scored question was answered on the full bundle — where it
returned the C4 regression the screen could not have seen.

### §5.4 — The CC-hot half of the split is UNCLOSED, and this arm makes it worse

The object was CC-hot / CT-cold. This arm addresses **CT**: its coupling is
restored and its volume miss narrows. **CC now over-generates** — the 2024
CC_REGULAR fuel-mix error moves **−0.190 → +0.756 TWh** as CC absorbs the
displaced import energy, and that is the most likely carrier of the C4
regression. Half the object is closed; the other half is worse than before.

### §5.5 — The direction hazard fired as declared

This is the **sixth consecutive favourable direction** for the CAISO lane. It
was declared in PRECOMMIT §0.2 **before any measurement**, and C3a was excluded
from the promotion basis **in both directions** — the promotion below rests on
G-COUPLE, the tier of the outstanding failure and the governance gates, and on
nothing about C3a. A reader who removes C3a from the argument entirely should
still be able to check the promotion.

### §5.6 — I published a WRONG DOF count and the keeper auditor caught it

My verification read `len(attestation["free_parameters"])` — but that field is a
**dict**, so the check counted its 5 top-level keys instead of reading
`n_entries`. I wrote "DOF 5 → 5" into the finding, the keeper shard, the matrix
shard's `gates` stamp and the cell evidence. **The true figure is 9 entries / 6
residual, UNCHANGED**, and the `calibration-keeper-auditor` agent found it and
repaired the three published places; this finding and the calibration-log entry
are repaired here.

**The correction also retires a claim I made for the arm.** I said the arm
"removes a free parameter". It does not: `gas_offer_margin_anchor` is DERIVED
(`scripts/data/derive_gas_offer_margin_anchor.py`), so it was never a ledgered
DOF row — the ledger's nine entries are unchanged and none of them is the
anchor. What the arm removes is a **mechanism and its anchor from the recipe**,
which is a rule-24 `[R-DELETE]` simplification but **not** a reduction in
identified degrees of freedom. Promotion condition (c) as registered was that
the residual count must not RISE; 6 → 6 satisfies it, so the promotion is
unaffected — but one strand of the argument I gave for it was wrong and is
withdrawn.

### §5.7 — The G-DRIFT audit is a reading of code, and inherits my reading

Addendum B classifies all 22 changed files between `900402b` and HEAD as
CAISO-backcast-inert. Each classification cites the gate, default, artifact or
docstring that makes the hunk unreachable, and no hunk is waved through as
"looks unrelated" — but it is an audit, not a proof, and it is falsifiable by
re-running the same diff.

---

## §6 — THE PROMOTION

Against the rule registered in PRECOMMIT §0.2 **before any measurement**:

| condition | result |
|---|---|
| (a) **G-COUPLE passes** | ✓ 6.719, inside the registered band and the measured band |
| (b) **no LOAD-BEARING criterion regresses to a NEW failure** | ✓ `fuelmix` / `sysvol` / `price_shape` PASS → PASS; `price_mean` FAIL → PASS. The one regression, `dispatch_corr`, is **supporting** tier |
| (c) **governance holds** | ✓ C6 attested PASS, C8 PASS, DOF ledger **UNCHANGED at 9 entries / 6 residual** — the registered test was that the residual count must not RISE, and 6 → 6 satisfies it |

**PROMOTED.** Both runs read NOT-YET, but the prior keeper's outstanding failure
is **load-bearing** and this one's is **supporting**, C3a passes in all three
years, and the fuel coupling matches CAISO's own measured record. The registered rule permitted promotion on a supporting-tier
regression; it would **not** have permitted it on a load-bearing one, and it
would have **refused** the run had G-COUPLE failed even with C3a improving.

---

## §7 — THE QUEUE

1. **NEW, ranked first: C4 `dispatch_corr` 2025** — gas fleet hourly NRMSE
   0.305 against ≤ 0.30. One cell, one year. The prime suspect is §5.4's
   CC_REGULAR over-generation; a phase 0 should decompose the gas NRMSE by class
   and hour-of-day before anything is armed.
2. **The CC-hot half of the CC/CT split** (§5.4) — now the larger half, and this
   arm moved it the wrong way. Still needs a functional-form charter of its own;
   the CT half is closed by this promotion.
3. **The fuel-invariant-margin flatness object (caiso-242 §3.5) is CLOSED** by
   this promotion — it was this session's object and it is adjudicated.
4. **Demoted, unchanged:** the north-corridor firm block and the two fitted firm
   prices; the transport adder on a spot-indexed marginal offer (caiso-244 ask E).
5. **Carried:** the residual CT_PEAKER volume miss (still −2.848 TWh in 2024,
   narrowed not closed); the C3a weight-basis owner ask (caiso-247 §4.5);
   caiso-250's own queue (the Pacific 07–08 morning-ramp slab and its missing
   matched control; the per-zone storage/class sidecar instrument ask).

---

## §8 — DO-NOT-REDO ADDS

1. **Never re-arm `gas_offer_net_revenue_margin` on CAISO.** Its fuel-invariant
   form is refuted on CAISO's own OASIS record (caiso-242 §3.5) and measured to
   halve CT's physical fuel sensitivity (§2). The cell is `R` for CAISO.
2. **This is NOT a verdict on any other ISO** (rule 25). NEISO identified the
   form on its own 2022 holdout rotation; that evidence is untouched here, and a
   transfer of this refusal to another ISO would be the same error in reverse.
3. **Per-year measured band multipliers stay rule-13 inadmissible** — a
   same-year measured outcome pin (PREREG-miso146 §9) — even though they sit in
   the same committed artifact and would have been the "obvious" lever.
4. **Never read the C4 margin (0.305 vs 0.30) as a reason to promote or
   discount it.** It failed; the promotion rests on the tier, not the margin.
5. **caiso-229 §5's REFUTED "the marginal rung over-propagates fuel" stays
   refuted** — this session moved coupling in the OPPOSITE direction (up, toward
   the measured band), which is consistent with it, not a re-opening.
6. caiso-250 §7, caiso-249 §7, caiso-248 §8, caiso-247 §8, caiso-246 §8,
   caiso-245 §7, caiso-244 §7, caiso-243 §10, caiso-242 §9, caiso-241 §10,
   caiso-240 §7, caiso-239 §8, caiso-230 §9, caiso-169, caiso-168 §8 stand in
   full.

---

## §9 — DELIVERABLES

`PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md` + Addenda A and B (each
pushed before the stage it governs); `scripts/probes/_caiso251_fuel_coupling_form.py`
+ `_caiso251_fuel_coupling_form.json`; `_caiso251_screen2024.json`;
`scripts/probes/_caiso251_arm_vs_control.py` + `_caiso251_arm_vs_control.json`;
`scripts/gen_caiso251_attestation.py`; the `gas_offer_margin` replay override in
`scripts/run_calibration_full.py`; **rule 29 `[R-SCREEN]`** in `CLAUDE.md` with
its genealogy in `docs/governance/rule-history.md` §8/§8.1; run
**`2026-09-05-caiso-251-b1-nomargin`** (**KEEPER**) with its bundle, sidecars,
legitimacy diagnostics, attestation, DOF ledger and verdict; the CAISO keeper
shard + `status/CAISO.js`; the matrix cell `gas_offer_net_revenue_margin`
**K → R** with the CAISO shard re-stamped; the §5.2 prose header; the forecast
board's gate-(a) stamp re-keyed in the same PR; this finding; the
calibration-log entry.

**Next number: caiso-252.**
