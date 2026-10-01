# FINDING — pjm-176: the EMAAC CC availability card does NOT survive phase 0. The trough object is a MIX defect, not an availability defect.

**Session** pjm-176 · **ISO** PJM · **Date** 2026-09-09 · **ZERO LP SOLVED — the arm never reached a solve**
**Keeper UNCHANGED** `2026-08-15-pjm-162-inputclock`. PJM headline stays **CALIBRATED** (rule 30(c)).
**Nothing armed, nothing registered, no holdout year touched.** Every number below is read from
COMMITTED artifacts: the keeper's `hourly/` sidecars, its run payload, and `bench/PJM/*.json.gz`.

**Charter** `ADDENDUM-pjm171-emaac-availability-census-2026-09-07.md` §5, under rule 29
`[R-SCREEN]` step 0: *"an arm with no computable pre-solve gap does not reach a solve."*
**The gap was computed. It has the wrong sign.**

---

## 1. RESULT

> **The chartered hypothesis is FALSIFIED, and it is falsified in the direction that matters.**
> The card was: phantom CC availability puts excess cheap CC in the overnight stack, which is why
> the model's trough implied heat rate is 7.9–9.3 against a measured 5.9–7.0 (pjm-171 §3). The
> hypothesis requires the model to be carrying **too much** CC in the trough. **It is not.** In the
> bottom load decile — pjm-171's own basis — model CC_REGULAR is within **1 % of the measured
> fleet in all three training years** (−1.0 % / +0.7 % / +0.8 %), and total model fossil in those
> hours is **2.4–5.0 % BELOW** measured. Removing phantom CC MW therefore *tightens* an already-short
> trough and moves the price the wrong way: **+$0.37 to +$1.51/MWh**, making the +$7.92 / +$7.36 /
> +$7.43 trough overprice **5–19 % worse** at the keeper's own local stack slope.
>
> **The 12.2 / 11.7 / 9.4 TWh of CC phantom is real — and it is REDISTRIBUTION, not over-availability.**
> It nets to ≈0 at the class the LP actually prices. The census is clean: **zero** CC_REGULAR plants
> carry `nodata`, and the bench-matched CC fleet reproduces the LP's own `class_hourly` CC_REGULAR
> to **0.002 %**, so there is no unmeasured CC dispatch hiding outside it.
>
> **What the same measurement DID find, and it is the better object:** the trough's class **mix** is
> wrong in a year-invariant, structural way. The model runs **414 / 164 / 471 MW** of ST_GAS in the
> bottom price decile against a measured **646 / 724 / 1,077 MW**, and the deficit closes monotonically
> with price and reverses by decile 10. The model's ST_GAS is **2.5–4.8× more price-elastic** than the
> measured fleet: it treats steam gas as a peaker where PJM runs it as a committed overnight block.
> **Reported, not armed** (§6) — it is a different card and needs its own charter.

---

## 2. THE CENSUS — training years, and it is NOT 2021

pjm-171's census was taken on 2021. The training window does not reproduce its severity, which is
itself part of the answer. Model vs CEMS, bench-matched plants, annual TWh:

| class | 2023 model / CEMS / phantom | 2024 | 2025 | phantom as % of own model energy |
|---|---|---|---|---|
| **CC_REGULAR** | 322.3 / 318.9 / **12.2** | 335.7 / 329.1 / **11.7** | 334.4 / 323.6 / **9.4** | **3.8 / 3.5 / 2.8 %** |
| CT_PEAKER | 19.2 / 19.9 / 9.8 | 20.3 / 21.5 / 9.4 | 27.0 / 24.4 / 11.1 | 51 / 46 / 41 % |
| ST_GAS | 10.8 / 9.4 / 5.1 | 10.8 / 13.7 / 2.9 | 17.0 / 16.4 / 5.1 | 47 / 27 / 30 % |
| COAL_BIT | 103.3 / 103.2 / 3.1 | 104.2 / 104.5 / 1.6 | 130.5 / 123.1 / 2.1 | 3.0 / 1.5 / 1.6 % |

**CC_REGULAR is the class with the LOWEST relative phantom of the merchant gas classes**, and its
class total is right. Bergen — the owner's original 2021 exhibit at 45.6 % model CF vs 9.0 %
measured — reads **30.2 % vs 21.3 %** in 2023. The 3.2× over-run does not reproduce in the tuned
window.

**On the C1 gate's own `classFull` basis** the annual CC_REGULAR error is **−1.0 % / +0.2 % / +1.2 %**
and it *changes sign* across the three training years. There is no annual CC over-run to remove either.

### 2a. The census is uncontaminated — three checks, all passed

1. **`nodata`**: 15 / 14 / 20 bench plants carry `nodata=True`; **none of them is CC_REGULAR**. A
   CEMS-missing plant cannot manufacture CC phantom here.
2. **Coverage**: bench-matched CC_REGULAR model energy is 322.296 / 335.731 / 334.400 TWh against the
   LP's own `class_hourly` P1 total of 322.289 / 335.649 / 334.330 — agreement to **0.002 / 0.02 / 0.02 %**.
   The 101–110 run-only plants carry no CC_REGULAR.
3. **Same check for ST_GAS** (0.4 %) and CT_PEAKER (0.9 %) — both clean, so §6 rests on a sound basis.

---

## 3. THE DECISIVE TEST — the trough hours themselves

Deciles of the keeper's own load-weighted P1 price, mean MW. `CC Δ%` is model-minus-CEMS on the
matched fleet; `ph%` is phantom as a share of the model's own CC dispatch.

**2023**

| decile | $/MWh | CC model | CC CEMS | **CC Δ%** | CC phantom | ph% | ST_GAS model | ST_GAS CEMS |
|---|---|---|---|---|---|---|---|---|
| 1 | 22.50 | 34,436 | 33,372 | **+3.2 %** | 2,025 | 5.9 % | **414** | **646** |
| 2 | 25.32 | 35,125 | 34,831 | +0.8 % | 1,567 | 4.5 % | 634 | 817 |
| 5 | 29.56 | 38,011 | 37,325 | +1.8 % | 1,389 | 3.7 % | 1,247 | 1,106 |
| 9 | 36.57 | 37,484 | 37,654 | −0.5 % | 1,284 | 3.4 % | 1,775 | 1,201 |
| 10 | 43.54 | 39,115 | 39,881 | −1.9 % | 900 | 2.3 % | 2,215 | 1,257 |

**2024 / 2025, decile 1 only** — 2024: CC 30,910 vs 31,395 (**−1.5 %**), phantom 2,100 (6.8 %),
ST_GAS 164 vs 724. 2025: CC 34,284 vs 34,129 (**+0.5 %**), phantom 1,228 (3.6 %), ST_GAS 471 vs 1,077.

**Two facts, and together they end the card:**
- **CC phantom IS trough-weighted** — 5.9 / 6.8 / 3.6 % in decile 1 falling monotonically to
  2.3 / 2.4 / 1.5 % in decile 10. The charter was right that the phantom lives overnight.
- **But the CC AGGREGATE in those same hours is right** (+3.2 / −1.5 / +0.5 %), and **total model
  fossil is 3.2 / 5.0 / 2.4 % BELOW measured**. The LP prices the class, not the plant. A per-plant
  phantom inside a correctly-sized class has no price channel.

**CC_REGULAR *is* a marginal class in the trough** (charter question (a)(i): **yes** — decile 1→2 it
is the largest or second-largest swing class in all three years, +683 / +2,508 / +1,179 MW). That is
precisely why the aggregate, not the per-plant allocation, is what governs.

### 3a. First-order price effect — the arm's own arithmetic, before any solve

Local stack slope taken from the keeper's own solved decile 1→2, applied to the decile-1 CC phantom:

| basis | year | trough model $ | actual $ | **miss** | slope $/GW | phantom GW | **Δ$ est** | **miss gets worse by** |
|---|---|---|---|---|---|---|---|---|
| load decile (pjm-171 §3) | 2023 | 25.64 | 17.72 | +7.92 | 0.33 | 1.809 | **+0.59** | **7 %** |
| | 2024 | 23.34 | 15.98 | +7.36 | 0.20 | 1.829 | **+0.37** | **5 %** |
| | 2025 | 31.49 | 24.06 | +7.43 | 0.39 | 1.441 | **+0.56** | **7 %** |
| price decile | 2023 | — | — | +7.92 | 0.75 | 2.025 | +1.51 | 19 % |
| | 2024 | — | — | +7.36 | 0.48 | 2.100 | +1.01 | 14 % |
| | 2025 | — | — | +7.43 | 0.88 | 1.228 | +1.08 | 14 % |

Both bases are reported rather than the larger one chosen. **The magnitude is basis-dependent
(5–19 %); the SIGN is not.** The kill does not rest on the magnitude — it rests on CC in the trough
being within 1 % of measured on pjm-171's own basis, which leaves nothing to remove.

---

## 4. THE STRONGEST SURVIVING FORM — the zonal/EMAAC channel — also fails, twice over

Even with the RTO aggregate right, a zonal over-supply could in principle mis-set EMAAC's own price.
Decile-1 CC_REGULAR by zone:

| zone | 2023 Δ% (phantom MW) | 2024 Δ% | 2025 Δ% |
|---|---|---|---|
| **EMAAC** | **+44.6 %** (837) | **+62.8 %** (1,084) | **−19.8 %** (312) |
| Dominion | **−43.7 %** | **−48.9 %** | −14.9 % |
| ComEd | +15.8 % | +5.5 % | +26.3 % |
| SWMAAC | +25.4 % | −50.0 % | −69.0 % |

1. **It is a zone-to-zone reallocation, not a system surplus** — EMAAC's +1,480 / +1,487 MW is offset
   by Dominion's −2,080 / −2,596 MW.
2. **It is NOT SIGN-STABLE across the training years.** EMAAC goes +44.6 % → +62.8 % → **−19.8 %**.
   A mechanism sized on 2023/2024's sign hurts 2025. Under rules 1 `[R-STRUCT]` and 29 `[R-SCREEN]`
   that is unidentifiable, not a lever.
3. **And there is no price channel anyway: the model's trough is essentially uncongested.** The
   spread across all eight zonal prices in decile 1 is **$0.95 / $1.79 / $1.81**. Moving CC MW
   between zones that clear within a dollar of each other cannot move the trough price.

---

## 5. INDEPENDENT CORROBORATION FROM THE RECORD — and the reconciliation

The matrix already carries two measurements that point the same way, and this census reconciles them:

- `pjm_measured_outage_event_cap` (**R**, pjm-161): *"the model already asserts MORE fossil-thermal
  outage (41.7 / 43.2 / 41.2 GW annual mean) than PJM publishes for its ENTIRE fleet (33.3 / 33.0 /
  35.9 GW)."*
- `dam_availability_rebasis` (**G**, closed at pjm-162): *"19.2–20.4 % of model fossil nameplate sits
  at HARD ZERO every day"*, and the restore form is **ANTI-TARGETED**.

**Reconciliation:** the model asserts too MUCH outage in aggregate while placing it in the wrong
hours and on the wrong plants. That is exactly the signature this census reads — a large per-plant
phantom sitting inside a class whose total is right and whose trough position is 1–5 % SHORT. A card
that removes still more availability pushes further in the direction the aggregate envelope already
overshoots. **This is why the charter's card is not merely unsupported but counter-indicated.**

---

## 6. THE SUCCESSOR THE MEASUREMENT NAMES — reported, NOT armed

The trough deficit is not CC. It is **ST_GAS**, and the signature is year-invariant:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| decile-1 ST_GAS model / measured MW | 414 / 646 | 164 / 724 | 471 / 1,077 |
| decile-10 ST_GAS model / measured MW | 2,215 / 1,257 | 3,069 / 2,796 | 3,955 / 3,595 |
| **d10 ÷ d1 — model** | **5.35×** | **18.7×** | **8.40×** |
| **d10 ÷ d1 — measured** | **1.95×** | **3.86×** | **3.34×** |

**The model's ST_GAS is 2.5–4.8× more price-elastic than the measured fleet.** The capacity is
present (12.3 GW nameplate 2023, annual CFs broadly right), so this is a **dispatch-timing** defect,
not a capacity one. And it is the right SHAPE for the trough IHR object: PJM's overnight clears at
IHR 5.9–7.0 — **below steam gas's own cost** — so the measured overnight ST_GAS block is running
*committed at a loss*, not economically. The model, letting it cycle off, prices the trough on its
economic merit order alone.

**Why this is a SUCCESSOR and not a lever taken here.** `gas_st_netload_drag` is already armed on the
keeper and already forces **49 / 49 / 40 %** of ST_GAS energy (D-2). Its D-4 row **passes** — but its
declared window is **`h0-23`**, i.e. all hours, so it cannot fail an off-window test by construction;
that PASS carries less information than it appears to. More to the point, a **net-load-shaped** drag
binds when net load is HIGH, which is the opposite of where the measured block sits. The successor's
question is therefore not "add more ST_GAS forcing" but **"is the existing forcing's SHAPE wrong?"** —
and per the charter's own lesson (d) from pjm-174, the instrument that would confirm it is
**"is ST_GAS online in the hours CEMS says it is online"**, not "did the trough price improve".
That needs its own charter, its own PRECOMMIT and its own screen year.

---

## 7. WHAT IS NOT CLAIMED

- **Phantom is an upper bound** (pjm-171 §4). A CEMS zero can mean *available but out of merit*, and
  the uint8 payload codec reads any CF below 0.5 % of nameplate as zero. Neither weakens the kill,
  which turns on the class **aggregate**, not on the phantom's size.
- **The CHP over-run seen in the trough is NOT reported as a finding.** The bench group labels and
  the LP's own class labels disagree for the CHP classes (bench-labelled CC_CHP 12.038 TWh against
  `class_hourly` 8.577 TWh, 2023), so that comparison is contaminated. Flagged as unresolved.
- **No rule-14 `[R-ACCURATE]` question is closed here.** Whether a detected per-unit outage event
  correctly reaches a per-plant LP row (`unit_outage_lp_capacity_basis`, **U**, `null` on the keeper)
  is a live correctness question and this finding does not answer it. What is refuted is only that it
  is **the source of the trough IHR defect** — i.e. its priority as a *price* card, not its merit as
  a *correctness* card.
- **Nothing was solved, so nothing is promotable and no bundle exists.** No screen year was spent, no
  holdout year was touched, `--holdout-authorized` was never invoked.

---

## 8. DISPOSITION

Keeper `2026-08-15-pjm-162-inputclock` and PJM's **CALIBRATED** headline are **UNCHANGED**. No
mechanism armed, no run registered, no bundle written. The charter's condition (b) — *"only if (a)
shows a real gap"* — **is not met**, so the session stops at phase 0 exactly as rule 29 `[R-SCREEN]`
step 0 directs. Matrix duty (rule 32 `[R-MECH-MATRIX]` (b)) discharged against
`unit_outage_lp_capacity_basis` in `docs/codebase-site/data/mechanism-matrix/PJM.js`; the cell stays
**U**, because this session refuted a *hypothesis about the cell*, not the mechanism itself.
