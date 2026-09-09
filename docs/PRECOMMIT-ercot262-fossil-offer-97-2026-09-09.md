# PRECOMMIT — ercot-262: the fossil offer bands ×0.97 across the board, with CC_REGULAR's duct/peaking band ×0.97 again

> Rule 29 `[R-SCREEN]` PRECOMMIT, written and committed **before any LP is spent**.
> This is the rule 1 `[R-STRUCT]` AUTHORIZED PRICE-TUNING CHANNEL (owner amendment
> 2026-09-05). Every condition (a)–(e) is addressed in §2.

## 1. What the owner instructed, and the values as declared

Owner, 2026-09-09, in two parts:

1. *"I want to adjust fossil offer curve down 3% across the board."*
2. *"And lower the duct burner multiplier slightly for cc reg."*

Part 2 was ambiguous between two objects and the owner ruled on it before any solve
(§2a). The declared factors, fixed here and **never swept**:

| factor | value | applies to |
|---|---|---|
| **across the board** | **0.97** | `committed` / `econ_low` / `econ_high` / `peak` on all 8 gas classes |
| **CC_REGULAR peak, total** | **0.9409** (= 0.97²) | the CC_REGULAR duct-fired / peaking band only |

The resolved arm curve for all three recipe legs is committed at
`results/calibration/_ercot262_fossil97_offer_curve.json`, generated before the solve.

## 2. Rule 1 `[R-STRUCT]` carve-out conditions, each discharged

**(a) The channel is the `offer_curve_by_group` band multipliers ONLY.** 32 bands per
leg — 8 gas classes × 4 bands. **Untouched:** every `phys_*` key (measured physics),
`econ_low_share` and `pct_peaking` (structural shares), and the `peak_ladder` **capacity
shares**. No adder, offset, haircut or proxy is introduced.

*One declared consequence:* the `peak_ladder` **heights** are scaled by the same factor as
their class's `peak`. The ladder **is** the peak band expressed as equal-capacity rungs, and
the conditional surface prices the rungs — leaving them at the old height would make the
peak cut **inert**, not conservative. Shares stay 0.2 each. (CAISO's ×0.92 got this for
free because its conditional split rebuilds the ladder from the post-override peak;
ERCOT's ladder is explicit, so it is done explicitly here.)

**(b) ONE config across EVERY scored year.** One multiplier, 0.97, applied to all five
years. The CC_REGULAR peak carries 0.97² in all five years. **No per-year value is used.**
ERCOT is a two-config keeper by owner ruling (2026-08-26), so the *pre-existing* band
levels already differ between the carve-out and forward legs — the ×0.97 does not create
that split, it rides it uniformly, and the multiplier itself is single-valued.

**(c) Set ex ante and declared before the solve; never swept.** 0.97 is the owner's own
figure, given as an instruction, not selected by me against any criterion. The 0.97² on
CC_REGULAR peak was chosen by the owner from options put before the first LP. This
document and the curve artifact are committed and pushed **before** the arm is solved.

**(d) Merit-order adjustment across classes is an INTENDED effect**, not a defect.

**(e) Declared in the attestation's `authorized_price_tuning` block** (C6 FAILS without it)
and carried in the DOF ledger (§5).

### 2a. The duct-burner ruling

"Duct burner multiplier for CC_REG" had two candidate objects and they differ in
governance:

* `cc_peak_hr_penalty = 1.15` — the literal *"CC duct-firing increment"*, a **heat-rate**
  multiplier. **Outside** the authorized channel: rule 1(a) names `offer_curve_by_group`
  bands only, and duct firing genuinely raises heat rate ~10–20 %, so cutting it on price
  would be tuning a measured physical quantity (rule 13 `[R-MEASURED]`).
* `offer_curve_by_group["CC_REGULAR"]["peak"]` — the duct-fired **peaking tranche's offer
  band**. **Inside** the channel.

**The owner selected the offer band.** `cc_peak_hr_penalty` is **NOT touched** by this arm.

## 3. Scope limit, stated at the gate: this reaches GAS, not COAL

The resolved ERCOT `offer_curve_by_group` carries **8 classes, all gas** — CC_REGULAR,
CC_CHP, CC_INTERMEDIATE, CT_CHP, CT_PEAKER, CT_INTERMEDIATE, ST_GAS, ST_GAS_INTERMEDIATE.
**There is no COAL class in it.** ERCOT coal's offer is set by the CAMPD bin sheet's
`HR_Mult_*` columns plus the coal supply / take-or-pay / passthrough-sigmoid stack
(`scenarios.py`, the note beside `cc_peak_hr_penalty`), which is **measured data outside
the authorized channel**.

So "fossil across the board" is delivered as **gas across the board**. Reaching coal would
require touching a measured artifact on a price residual, which rules 1/13 forbid absent a
separate explicit ruling. **Not done here, and flagged rather than silently scoped away.**

## 4. Forward-leg treatment (owner-ruled)

The forward years carry additive `offer_curve_deltas` alongside the multiplicative bands.
The owner ruled: **apply the 3 % to the effective post-delta band.** Implemented by taking
each leg's **resolved** `scenario_config.offer_curve_by_group` — which is the band the leg
actually solved, deltas already applied (verified: forward CC_REGULAR peak 4.576 = 4.326
override + 0.25 delta) — scaling it, and supplying the result as the absolute curve. The
delta rows are neither rewritten nor re-applied. `offer_curve_deltas["CC_CHP"]["pct_peaking"]
= −4.0` is a structural share and is untouched.

## 5. DOF LEDGER (rule 21 `[R-DOF]`)

| parameter | value | identification source |
|---|---|---|
| fossil offer-band scale | **0.97** | **price residual, authorized channel** (rules 1/13 amendment 2026-09-05) — owner instruction 2026-09-09. Not a measured input. |
| CC_REGULAR peak extra scale | **0.97** (0.9409 total) | same channel and ruling; owner-selected from options put before the first LP |

Per rule 20 `[R-DOF]`'s 2026-09-06 cross-reference (owner ruling R-AY): these ARE ledgered
free parameters whose identification source is the ruling itself, they are reported at full
magnitude, and their presence does **not** by itself make the residual they close an open
root-cause issue. No gate moves.

## 6. PRE-REGISTERED PREDICTIONS AND GATES

### 6a. STOP gates (may kill the arm; may never promote it)

| id | gate | STOP bar |
|---|---|---|
| **G-1** | any `phys_*`, `econ_low_share` or `pct_peaking` value differs from the keeper | any difference |
| **G-2** | any non-gas class appears in the arm's resolved curve | any |
| **G-3** | every scaled band equals keeper × its declared factor | any mismatch > 1e-6 |
| **G-4** | shed: dump MWh in any year | > 1.0 MWh |
| **G-5** | a load-bearing criterion PASS → FAIL in **2023/2024/2025** | any |

### 6b. Directional predictions (scored, not gates)

| # | prediction |
|---|---|
| **P1** | Every year's model LMP **falls**. All five years currently over-price (2021 +4.2 %, 2022 +9.8 %, 2023 +24.3 %, 2024 +15.1 %, 2025 +4.0 %), so a uniform band cut is directionally right everywhere. |
| **P2** | The move is **roughly proportional to the gas-marginal share**, not a flat 3 % of price: I predict −2 % to −6 % on annual LW LMP in each year, largest where gas sets price most hours. |
| **P3** | **2023 improves most in absolute terms** (+24.3 % is the largest residual) and **2025 risks over-shooting** (+4.0 % is nearly closed; a 3 % cut could take it negative). 2025 going negative is the most likely single regression and I am registering it now, not after. |
| **P4** | **C3b 2021 (0.238 vs a 0.20 gate) is the target of record.** A level cut mostly shifts the price distribution rather than reshaping it, so I predict C3b improves only **modestly — to 0.20–0.235 — and may not clear the gate.** If C3b clears, the five-year determination goes CALIBRATED; I am not predicting that. |
| **P5** | **C3c falls in every year** (fewer hours above $200 as the whole stack drops). 2021 is 223 h against 214 actual, so a fall moves it *through* the actual — I predict 195–220 h and a possible sign flip on that miss. |
| **P6** | **C1 shifts toward gas** — cheaper gas bands displace coal further. COAL_PRB 2021 is already −4.84 TWh light at 53.228 vs 58.064; I predict it goes lighter still, and C1 is the criterion most at risk of a PASS → FAIL. |

### 6c. Reported, never gated

C8 forced share, every C1 class bar at full magnitude, and the coal scope gap of §3.

## 7. Governance

Rule 31 `[R-RETAIN]`: bundles are gitignored and are **never deleted** until the owner
rules on promotion; the promotion question is put explicitly in the final report. Rule 12:
one year per container, shards pinned to an **immutable commit SHA**, never a branch name.
Rule 22: 2021/2022 are validation-tier spends under ERCOT's `complete` marker; no parameter
is identified on, fitted to, or selected against any year — both factors are owner-set and
registered above the solve.
