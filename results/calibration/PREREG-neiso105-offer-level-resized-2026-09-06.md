# PREREG neiso-105 — the re-sized fossil offer-level correction (owner-directed)

**2026-09-06, session neiso-105 (continuing neiso-104's lane).** Written and committed **before
the solve**, per rule 1 `[R-STRUCT]` condition (c). Supersedes
`PREREG-neiso104-fossil-offer-level-2026-09-06.md` §3.3 on the VALUE only; §2.1 scope, §3.1
target and §6 risk register are carried forward unchanged.

## 1. The owner ruling that unblocks this

neiso-104 §6 left one question open and called it owner-court: *is re-deriving the cut from the
screen's MEASURED pass-through coefficient legitimate identification, or the first iteration of a
sweep?* **The owner has answered it by direction, twice, on 2026-09-06: shift the fossil offer
curves down, preserving the ratio.** Recorded as the owner's call, not as this lane's finding.

**Why it is identification and not a sweep, stated so a later reader can judge it:** the TARGET —
the in-sample 2023–2025 geometric-mean price bias, **+3.4678 %** — was fixed in the neiso-104
PREREG before any LP ran and **has not moved**. What moved is only the *coefficient* converting a
band cut into a price move, and that coefficient is a **measured physical response**
(dPrice/dMultiplier), not a criterion outcome. No gate was consulted to choose it. The distinction
condition (c) polices is selecting a factor *because it makes a criterion pass*; here the factor
is arithmetic from a declared target and a measured slope.

## 2. The declared value

| | neiso-104 | **neiso-105** |
|---|---:|---:|
| target: in-sample geometric-mean bias | 0.034678 | **0.034678** (unchanged) |
| pass-through coefficient | 0.765 (predicted, **refuted**) | **0.5247** (measured, neiso-104 screen) |
| **declared cut** | 4.53 % | **6.609 %** |
| **declared scalar** | 0.9547 | **0.93391** |

> **DECLARED: a single scalar `0.93391` on the SAME 12 markup bands** of neiso-104 PREREG §2.1 —
> `committed` / `econ_low` / `econ_high` of CC_REGULAR, CC_CHP, CT_PEAKER, ST_GAS. Bands in
> `results/calibration/_neiso105_arm_offer_curve.json`, committed with this file. Unchanged and
> still excluded: all four `peak` bands (three equal their `phys_peak`; CT_PEAKER's 4.0 is the
> ISO-NE offer cap), every `phys_*`, `econ_low_share`, `pct_peaking`, and the declared-neutral
> CT_CHP group. **This number does not move again.**

Headroom against measured physics at 6.609 %: CC_REGULAR econ_low 1.00→0.934 (phys 0.854) and
econ_high 1.15→1.074 (0.940); ST_GAS econ 0.85→0.794 / 0.89→0.831 (0.692/0.731); CT_PEAKER econ
1.00→0.934 (0.745/0.700). All still above their measured marginal. `CC_CHP.committed` and
`ST_GAS.committed` sit further below their `avg_committed_p50` — the pre-existing disclosure of
neiso-104 §2.1, deepened, not created.

## 3. Pre-registered landing, and the one way it can be wrong

By construction the predicted price move is 6.609 % × 0.5247 = **−3.468 %**:

| year | tier | now | predicted | predicted C3a |
|---|---|---:|---:|---|
| 2020 | validation | +13.71 % | **+9.76 %** | PASS by 0.24 pp |
| 2021 | validation | +9.08 % | +5.30 % | PASS |
| 2022 | validation | −0.60 % | −4.05 % | PASS |
| 2023 | train | +3.13 % | −0.45 % | PASS |
| 2024 | train | +5.66 % | +2.00 % | PASS |
| 2025 | train | +1.65 % | −1.88 % | PASS |

**The named failure mode: pass-through is measured at ONE point and assumed LINEAR.** 0.5247 was
measured at a 4.53 % cut; this arm applies 6.61 %. A deeper cut reorders more of the merit stack,
so the true coefficient may fall with depth and the arm may again under-deliver. **If it does, the
scalar is NOT raised a second time** — a third sizing iteration would be a sweep by accumulation,
whatever each single step's justification. It stops and the residual is reported.

## 4. Execution

- **Straight to the FULL SPAN**, one `--year 2023 2024 2025` invocation, one bundle (rule 16
  `[R-ALLYEARS]`). No new screen: rule 29's screen gate is **structural**, the mechanism is
  byte-identical in kind to the one neiso-104 already screened (G2 footprint PASS, G3 identity
  PASS on these same 12 bands), and only the magnitude differs. Re-screening would spend LP to
  re-confirm two gates that cannot change.
- **G-CTRL form 4: the keeper's committed bundle IS the control.** neiso-104 MEASURED this — a
  same-HEAD control replay reproduced the keeper to 4 dp on load-weighted price and 0.001 TWh on
  every class. No control solve.
- **Gates on the full span**: C1, C2, C3a, C3b, C3c, C4, C6, C8 scored by
  `scripts/calibration_verdict.py` after registration.
- **Rule 30(c) holds**: 2020 is reported, never chased; NEISO's determination is its train-tier
  verdict.

## 5. The risk that decides this, restated at full strength

**NEISO's `CALIBRATED` rests on C3c being the LONE failure** (rubric v3.3 guard (a)). The
incumbent scores 0 FAILs with C3c the single ledgered caveat. **If this arm flips any second
criterion — C3b price duration/shape is the live exposure, since the level shifts ~3.5 % while the
four physically-pinned `peak` bands stay put — the standing rule goes silent and BOTH failures
stand, taking NEISO to `NOT-YET`.** That is the price of this correction and it is accepted
knowingly, on the owner's direction, not discovered afterwards.

Promotion is a separate decision from this solve: the arm is registered whatever it does (rule 15),
and becomes the keeper only if its determination is not worse (rule 22 D-5(b), re-verified before
any re-key).
