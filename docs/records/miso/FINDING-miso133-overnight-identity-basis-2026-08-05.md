# FINDING — miso-133: the `ST_GAS` "bench coverage gap" is a REPORTING-TRANSFORM DENOMINATOR CROSSING, the CHP row is a BASIS CROSSING, and the model's overnight non-coal CAPABILITY is not the binding constraint

**Session:** miso-133, 2026-08-05, branch `claude/miso-133-calibration-ugnvvp`,
off `origin/main` at `bb01b7e5`.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED.** MISO keeper unchanged at
**`2026-08-05-miso-132b-cc-committed`** (bundle `results/calibration/miso132_ccmin_B`,
**NOT-YET**, sole FAIL C7 `COAL_PRB` 2025 `cv_ratio` 0.338 vs 0.50, ledgered caveats
2/3 {C3a, C3c}). Rule 22 `[R-HOLDOUT]`: 2023–2025 only — MISO holds no `complete`
marker; no 2022 / 2019 / H1-2026 year was solved, scored or read.

**Pre-registration** `results/calibration/PREREG-miso133-overnight-supply-identity-basis-2026-08-05.md`,
committed and pushed at **`a2be76c6`** *before* any adjudicating statistic.
**Probe** `scripts/probes/_miso133_overnight_identity_basis.py`; **record**
`results/calibration/_miso133_overnight_identity_basis.json`.

**Lane:** charter option (b), restricted to the two un-adjudicated rows of
`FINDING-miso130-c7-night-regime-2026-08-05.md` §4. Option (a) was not taken; §7
records why, and the Michigan PSCR lead is left unspent.

---

## 1. Headline

miso-127-parallel §7a named three candidate causes for the `ST_GAS` bench-coverage
gap — sub-CEMS units, bench-vs-LP class assignment, model units with no bench entry
— and adjudicated none. **All three are wrong.** The cause is a fourth thing nobody
had looked for: the two sides of the ratio sit on **opposite sides of a documented
reporting transform**.

`fleet.eia860.apply_other_fossil_scoring` re-buckets a *genuinely mixed* gas-thermal
plant — no single gas-thermal class holds 60 % of its EIA-923 net generation, and its
two largest classes are both gas-thermal — into an `OTHER_FOSSIL` bucket **on both the
model and the actual side** of the reporting chain. It is deliberate, symmetric and
dispatch-neutral by construction ("a reporting/benchmark transform (NOT a dispatch
change)"). `hourly/class_hourly_<year>.parquet` is written **upstream** of it; the
bench/payload pair is built **downstream** of it. miso-127 divided a downstream
numerator by an upstream denominator.

At MISO the transform has essentially one member: **Ninemile Point (plant 1403,
Entergy Louisiana)** — the model carries `ST_GAS` 1,465.4 MW + `CC_REGULAR` 649.5 MW,
neither class dominant, so the whole plant is scored `OTHER_FOSSIL`. Its model energy
is **9.51 / 9.21 / 8.36 TWh** in 2023/24/25 against an `ST_GAS` raw-denominator
residual of **8.23 / 8.16 / 7.38 TWh**. One plant *is* the gap.

| `ST_GAS` coverage | 2023 | 2024 | 2025 |
|---|---|---|---|
| miso-127's basis (raw `class_hourly` denominator) | 0.605 | 0.612 | 0.629 |
| **transform-consistent (both sides downstream)** | **0.988** | **0.988** | **0.988** |

And the machines are not missing from the measured record at all: the bench carries
1403 with **8.26 / 9.13 / 8.62 TWh** of CAMPD, and at July night the model and the
measurement agree to **−50 / −3 / −86 MW**. `ST_GAS` has 18 / 17 / 18 matched plants
and **2 / 0 / 0** plants with no bench entry, totalling **6.5 / 0 / 0 MW**.

**Consequence:** the `ST_GAS` row of miso-130 §4's overnight supply identity is
**STRUCK as stated** ("size unknown") and **REPLACED with a measured number** (§4).
"No class-grain statement about MISO gas is determinable" — miso-127-parallel §7a's
blocker, which has gated the MISO gas lane since 2026-08-04 — **is lifted.**

---

## 2. Verdicts against the pre-registered bars

| bar | result |
|---|---|
| **S-1 `ST_GAS`** (M/X/N/U on payload energy) | **NO VERDICT — KILL-5 fired.** `ρ` = −0.394 / −0.383 / −0.364, far outside the ±0.05 construction gate, in all three years. The pre-registered basis cannot carry a verdict, exactly as declared. §3 is the disclosed repair. |
| **S-1 `CT_PEAKER`** | **H-U — NO BENCH COUNTERPART**, 3 of 3 years (`ρ` −0.018/−0.017/−0.038, gated; `split_U` 0.999/0.998/0.994). |
| **S-1b `CT_PEAKER`** (pre-registered, plant grain) | **SUB-CEMS FAILS** — 0.192 of the 1,759 MW below 25 MW. |
| **S-1b `CT_PEAKER`** (disclosed refinement, unit grain) | **SUB-CEMS SUPPORTED** — **0.799** of 1,886.4 MW across **154 generators** at 46 plants is below 25 MW. See §5; the two grains disagree and the unit grain is the one 40 CFR Part 75 is written at (rule 14 `[R-ACCURATE]`). |
| **S-2 `CC_CHP`** | **RESOLVED** — grid-delivered coverage 1.088 / **0.986** / 1.194; in band in 2 of 3 years. |
| **S-2 `CT_CHP` / `ST_CHP`** | **PARTIALLY RESOLVED**, residual named in §3b. |
| **S-3** | delivered — the restated identity, §4. |
| **S-4** | delivered, **uncontaminated in all three years** (no class's keeper night dispatch exceeds its assembled capacity) — §6. |

KILL-1 honoured: nothing below is sized on any Δ; no field, no arm, no run, no keeper
move. KILL-2: no adjudicated cell re-opened. KILL-6: the CHP `grid_frac` is the
committed bench `btm`/`e_ann` as-is; no alternative add-back was searched for.

---

## 3. The two crossings, stated exactly

### 3a. `ST_GAS` — a DENOMINATOR crossing (the transform)

The MISO `mixed_fossil_plants` roster inside the model fleet, all years:

| year | plants | model TWh | bench group | bench measured TWh |
|---|---|---|---|---|
| 2023 | **1403 Ninemile Point** (`ST_GAS` 1,465.4 + `CC_REGULAR` 649.5 MW) | 9.467 | `OTHER_FOSSIL` | 8.262 |
| 2023 | 1464 Big Cajun 1 (`ST_GAS` 174.5 + `CT_PEAKER` 199.5 MW) | 0.044 | `OTHER_FOSSIL` | 0.283 |
| 2023 | 50846, 50969 (CHP pairs, sub-25 MW) | 0.286 | *not benched* | — |
| 2024 | 1403 / 1464 / 50846 / 50969 | 9.174 / 0.034 / 0.289 | `OTHER_FOSSIL` ×2 | 9.134 / 0.160 |
| 2025 | 1403 / 50969 / 54321 | 8.365 / 0.146 / 0.073 | `OTHER_FOSSIL` | 8.621 |

Payload `OTHER_FOSSIL` total **9.511 / 9.207 / 8.365 TWh** against `ST_GAS`
raw-minus-payload residual **8.229 / 8.160 / 7.379 TWh** — the remainder is 1403's
`CC_REGULAR` limb, which is why `CC_REGULAR`'s coverage also moves (0.926/0.929/0.948
→ **0.960/0.962/0.956**). `COAL_PRB` moves 0.859/0.855/0.853 → 0.874/0.871/0.865 and
`CT_PEAKER` 0.837/0.858/0.799 → 0.846/0.867/0.813 — i.e. **the transform is the whole
story for `ST_GAS` and almost none of the story for the other classes**, which is what
makes `ST_GAS` the outlier §7a saw.

### 3b. CHP — a BASIS crossing, and it is exactly invertible

§7b is right that the bench CHP series carry the whole plant. What it did not have is
that **the payload's model series carries the same add-back**:
`render_calibration_html.py` adds the behind-the-meter host block back **flat**
("CHP add-back (report only, NOT in the LP) … A flat add is correlation-invariant"),
in the amount the bench's own `btm` field records. The payload/bench pair is therefore
*internally consistent on a whole-plant basis*; what is not comparable is either of
them against `class_hourly`, which is grid-only. And because the add-back is a flat
`btm × 10⁶ / 8760` MW block, **removing it is exact, not an estimate.**

Coverage on the crossed basis and on both clean pairs (matched machines):

| class | crossed (§7b's number) | whole-plant | **grid-delivered** |
|---|---|---|---|
| `CC_CHP` | 2.197 / 1.976 / 2.282 | 1.080 / 1.039 / 1.134 | **1.088 / 0.986 / 1.194** |
| `CT_CHP` | 4.369 / 4.605 / 4.276 | 1.264 / 1.379 / 1.393 | **1.654 / 1.756 / 1.767** |
| `ST_CHP` | 2.902 / 2.686 / 2.582 | 0.953 / 1.130 / 1.113 | **0.822 / 0.803 / 0.773** |

`CC_CHP` lands in the pre-registered band → **RESOLVED**. `CT_CHP` and `ST_CHP` do
not, and the residual is named rather than hidden: on the grid basis the model runs
**1.72 / 2.04 / 2.04 TWh/yr too little** `CT_CHP` and **0.06 / 0.06 / 0.07 TWh/yr too
much** `ST_CHP`. Those are real level residuals on a 6-plant and a 3-plant class, not
basis artifacts — they belong to whoever next charters MISO CHP, and they are small.

---

## 4. §4 of miso-130, RESTATED — grid-delivered on both sides, July night (h0–5)

Model − measured MW over the matched machines, both sides grid-delivered:

| class | 2023 | 2024 | 2025 | transform-consistent coverage (2025) |
|---|---:|---:|---:|---:|
| `COAL_PRB` | **+1,968** | **+1,736** | **+3,103** | 0.865 |
| `COAL_BIT` | +145 | +445 | +970 | — |
| `COAL_LIGNITE` | −124 | −59 | −80 | — |
| `CC_REGULAR` | −1,367 | −779 | −1,357 | 0.956 |
| `CT_PEAKER` | −854 | −691 | −666 | 0.813 |
| `ST_GAS` | **−384** | **−234** | **−673** | **0.988** |
| `CT_CHP` | −189 | −218 | −298 | — |
| `CC_CHP` | −134 | +75 | −156 | — |
| `ST_CHP` | +9 | +12 | +10 | — |
| `OTHER_FOSSIL` (Ninemile Pt) | −50 | −3 | −86 | — |
| **coal total** | **+1,989** | **+2,122** | **+3,993** | |
| **non-coal total** | **−2,969** | **−1,838** | **−3,227** | |

The two rows this session was chartered to resolve:

* **`ST_GAS`: −384 / −234 / −673 MW** (model short), on **98.8 %** coverage. It was
  "size unknown"; it is now measured, and it is *small* — a fifth of the 2025 coal
  surplus, not the hole.
* **CHP: −314 / −131 / −444 MW** (sum of the three CHP classes, grid-delivered). The
  identity carried **"nominal −1.7 GW flat"**; the true grid-delivered shortfall is
  **~a quarter of that**, and the difference was the basis crossing. The −1.7 GW row
  **overstated the CHP hole by roughly 1.3 GW.**

**And a row the identity did not have: `CT_PEAKER`, −854 / −691 / −666 MW** — the
largest single non-coal shortfall after `CC_REGULAR`, on a class whose coverage is
only 0.81–0.87 even transform-consistent, so the class-wide number is **larger** than
the matched-set figure shown. It was invisible before because §7a's coverage failure
had blocked every class-grain gas statement.

Net effect on miso-130's root cause: **it survives, re-weighted.** The overnight
non-coal deficit is real and is ~3.2 GW in 2025 — but it is `CC_REGULAR` (−1.36) +
`CT_PEAKER` (−0.67) + `ST_GAS` (−0.67) + CHP (−0.44), not the CHP-heavy composition
the disputed row implied. The 2025 coal surplus (+3.99 GW) still exceeds it.

---

## 5. The grain disagreement in S-1b, recorded rather than buried

The pre-registered S-1b statistic is plant-grain assembled capacity, and the PREREG
declared that grain **conservative** in advance ("it can only make sub-threshold look
LESS likely"). It returns **0.192 → SUB-CEMS FAILS**. At the grain 40 CFR Part 75 is
actually written — the **unit** — the same 46 plants carry **154 EIA-860 generators,
1,886.4 MW, of which 1,508.0 MW (79.9 %) is below 25 MW → SUB-CEMS SUPPORTED.**

The plant identities say the same thing: **Weston RICE (131.6 MW)** and **F.D. Kuester
Generating Station (131.6 MW)** are reciprocating-engine banks, and A.J. Mihm (56.4),
Marquette Energy Center (51.3), Westside Energy Station (46.5), D G Hunter (65.1) and
Coldwater Peaking Plant (12.9) are small peaking facilities. A 131.6 MW plant of
~15 MW engines is genuinely not a CEMS reporter.

**Both numbers are reported; the pre-registered one is the one that fired, and it is
superseded on rule 14 grounds by the unit-grain measurement, disclosed here rather
than silently substituted.** The operative conclusion: `CT_PEAKER`'s residual coverage
gap is **real machines the measured record cannot see**, not a roster/crosswalk defect
— so its −0.67 to −0.85 GW July-night shortfall is a *lower* bound on the class, and
**no bench-repair charter is owed.**

---

## 6. THE SLACK MEASUREMENT — and the DO-NOT it produces

The miso-132(a) lesson applied before anything is proposed. July-night headroom on the
keeper's own dispatch, **uncontaminated in all three years**:

| class | 2023 headroom | 2024 | 2025 | 2025 share idle |
|---|---:|---:|---:|---:|
| `CT_PEAKER` | 21,961 MW | 21,024 | **20,932** | **0.939** |
| `ST_GAS` | 9,126 | 8,928 | **9,132** | **0.831** |
| `CC_REGULAR` | 9,215 | 7,620 | **9,165** | **0.334** |
| `CC_CHP` / `CT_CHP` / `ST_CHP` | 1,383 / 301 / 438 | 1,158 / 302 / 305 | 1,476 / 280 / 394 | 0.408 / 0.312 / 0.564 |

At July night 2025 the model dispatches **6.1 %** of its assembled `CT_PEAKER` and
**16.9 %** of its `ST_GAS`. Against a **3.2 GW** total non-coal shortfall there is
**~41 GW** of idle non-coal gas capability in the fleet — an order of magnitude more,
and that is before noting the number is a capacity-basis upper bound (it is not
hour-by-hour availability-scaled, so the true idle figure is lower). The margin is
not close: `CT_PEAKER` availability would have to fall to **~20 %** — 4.5 GW of
22.3 GW — before its idle block *alone* stopped covering the entire 3.2 GW shortfall,
and that is one class of six.

> **DO-NOT (the third instance of the miso-132(a) family): do not charter a MISO
> lever whose mechanism is to make more overnight non-coal capability AVAILABLE.**
> Availability, must-offer, commitment-bridge, reserve-gating and RA-style levers all
> add or unlock *capability*, and MISO's overnight capability is already ~10× the
> shortfall and idle. **A constraint changes an optimum only where it binds.** What
> holds the model's overnight gas down is the merit **ORDER** — coal's July-night
> offers sit below gas — which is precisely miso-130's freeze statistic seen from the
> quantity side. The two constructions now agree from both directions.

This also disposes of the `gas_commitment_bridge` census question miso-130 §5 left
open for a future charter: the pool is not merely empty, the mechanism could not bind
if it were full.

---

## 7. Why charter option (a) was not taken

`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` §9 (xiso-4, 2026-08-04)
had already established that the §8 Form 580 count is **not producible from a standard
session**. This session re-probed the one cheap discriminator rather than re-deriving
the whole assessment (rule 28(a) DO-NOT-REDO):
`elibrary.ferc.gov/eLibrary/docketsheet?docket=IN79-6` returns the **same 22,464-byte
SPA shell** — §9 confirmed, not re-litigated. §9's scheduling point is independent and
decisive: the 2026 Form 580 covering CY2024–2025 is not due until **2026-10-30**, so
the ask's §2C bar cannot clear before late 2026 *whatever the count returns*.

**The Michigan PSCR lead is UNSPENT and untouched** — no coverage, floor or ΔR² test
was run against it, so a future session inherits it exactly as the ask left it.

---

## 8. Consequences for the queue

1. **miso-127-parallel §7a is CLOSED.** Its three candidates are refuted; the cause is
   the `OTHER_FOSSIL` denominator crossing; `ST_GAS` coverage is 0.988. The
   class-grain-gas blocker it imposed is **lifted**, and miso-114's original question
   is answerable — miso-127's matched-machine result (model short overnight gas in
   3/3 years) now has a class-grain identity behind it (§4).
2. **miso-130 §4's identity is superseded by §4 above.** The `ST_GAS` row is measured;
   the CHP row is corrected from −1.7 GW to −0.31/−0.13/−0.44 GW; a `CT_PEAKER` row is
   added. The seam and `CC_REGULAR` rows are untouched and keep their adjudications
   (SPENT / miso-115 REFUSED).
3. **An entire successor family is closed by §6** — no capability-side overnight lever
   at MISO. This is a *shrinking* of the admissible lane, and it is the honest result:
   with capability-side levers out, granularity inert (miso-131), online-gating slack
   (miso-132(a)), the seam classes spent and the take-or-pay family dead by proof, the
   remaining admissible route to C7-2025 continues to run through the **coal offer
   level**, i.e. the ex-ante contract-tonnage data ask.
4. **A bench-chain hygiene item, NAMED not chartered:** any coverage or level statistic
   that divides a bench/payload quantity by a `class_hourly` quantity is crossing the
   `apply_other_fossil_scoring` seam and will mis-state any ISO with a mixed
   gas-thermal plant. This is a *cross-ISO* construction hazard (the transform is not
   MISO-specific), but under rule 25 `[R-ISO-SCOPE]` **no other ISO's number is
   corrected here** — each ISO's own session must measure its own roster. Nothing in
   this finding transfers a verdict.

**DO-NOT list carried forward, unchanged:** no fitted trough adder; no 2025-specific
lane (miso-128); no re-opening of offer granularity (miso-131), reserve online-gating
(miso-132(a)), the seam price/ceiling/floor classes (miso-114/123), take-or-pay /
period-budget / minimum-take (miso-127b), within-band slope (miso-129),
self-commitment forcing removal (miso-102), or the CC committed band (miso-132(b),
now measured-grounded at 1.005 — never re-swept against the C7 residual); do not
re-tune `coal_mustrun_online_pmin` (miso-127).
