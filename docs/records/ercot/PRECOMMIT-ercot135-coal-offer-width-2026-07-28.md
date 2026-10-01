# PRE-COMMIT — ERCOT-135 Phase 2: the coal offer-curve WIDTH arm on the un-pinned fleet

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot135-coal-merit-order ·
**Status** **PRE-REGISTERED, NOT EXECUTED — BLOCKED ON AN OWNER RULING (§0).**
Written and pushed **before any solve**, per the ERCOT-134 §10 charter. ·
**Phase 1** `docs/DIAGNOSIS-ercot135-coal-merit-order-2026-07-28.md` ·
**Keeper** `2026-07-28-ercot116-regate-base` — **not touched by this document.**

---

## 0. The blocking gate — read first

This arm **may not be solved** until the owner rules on **ERCOT-116 adoption**
(the measured coal availability envelope,
`ercot_thermal_dam_availability_coal`). The dependency is not procedural, it is
methodological: rule 14 `[R-ACCURATE]` requires the compensator to be measured
**against the accurate input**, not around the estimate. ERCOT-134 established
that the legacy statistical envelope silently absorbs precisely the merit bias
this arm targets; tuning the offer curve on the pinned fleet would re-bury the
error inside the inaccurate input — the exact move rule 14 forbids.

Concretely: on the pinned fleet ~31/33/45 % of online coal plant-hours sit at
the availability ceiling, so an offer-curve change cannot move them, and any
apparent gain would be measuring the estimate, not the mechanism.

**If the ruling is ADOPT** — proceed exactly as §§1–5 specify, with the envelope
ARMED in both arms.
**If the ruling is DO-NOT-ADOPT** — this arm is **withdrawn, not re-scoped to
the pinned fleet.** Say so and stop; a shape lever validated on a pinned block
is not evidence (`DIAGNOSIS-ercot134` §8).
**Additional input to that ruling** (new, from Phase 1 §7.2): under the measured
envelope the plant-grain water-fill saturates each plant at its **model** `pmax`,
so a plant whose `pmax` exceeds its declared maximum lands above its own
declaration — Martin Lake at **1.451×**, because its destroyed unit 1 is carried
by a `BIN_FORCED_DERATE_BY_YEAR` entry the redistribution overrides. The
envelope is therefore **not adoptable as-is** without deciding how the
redistribution and the forced-derate registry compose.

## 1. The hypothesis, stated so it can fail

**H.** ERCOT coal's band-uniform over-run is a coal offer-curve **SHAPE**
defect: the model prices ~30 % of coal capacity at **$4.50/MWh** (tranche-1
take-or-pay, VOM-only) against a real fleet whose *submitted* DAM curve is a
flat step at **~$20.5/MWh**, leaving **3,255 / 4,163 / 3,171 MW** offered below
the measured price with no min-load justification (Phase 1 §5).

**H is FALSE if** the unoffered 61–72 % of committed coal resource-hours turns
out to be **self-scheduled / price-taking**, in which case a near-zero bid is the
structurally faithful representation of that block and the defect lies elsewhere
(the gas side of the ranking, or reach). **Phase 1 could not settle this and
neither can this arm** — see §6.

## 2. The arm

**Single delta**, on the keeper recipe with the ERCOT-116 envelope ARMED in
BOTH arms:

* **BASE** = keeper recipe + `ercot_thermal_dam_availability_coal=true`
  (i.e. the registered `2026-07-28-ercot116-regate-arm` configuration, re-solved
  fresh at HEAD — it is the correct control because the comparison must be made
  on the un-pinned fleet).
* **ARM** = BASE + the coal tranche-1 offer moved from VOM-only onto the
  **measured submitted DAM coal offer floor**, per plant per year, from the
  corpus Phase 1 §1 already reads (`Resource Type == CLLIG`, capacity-weighted
  p50 of the submitted curve's **bottom** price). **No fitted scalar**: the
  level is the measured value, transplanted as published, exactly the
  ERCOT-132-leg-B §5.3 discipline (write as `measured − base delta` so the
  RESOLVED band lands on the measured value, and verify in `run_config.json`).

**Explicitly NOT in the arm** (rule 19 `[R-ONE-MECH]`, and each already
adjudicated): the offer LEVEL rebasis (ercot132 leg B, CLOSED); the pooled
`econ_high` 2.856 (ercot122 §5.2, barred); the PRB/lignite passthrough sigmoid
floors 0.76/0.675; `coal_tranche_1_frac` itself (Phase 1 §4 measured the model's
0.30 as *smaller* than the measured 0.364–0.384 — moving both the share and the
price would be two mechanisms on one phenomenon); any availability lever.

## 3. Predictions — per band, written before the solve

Bands are `ercot127`'s fixed edges (`<15, 15-20, 20-25, 25-30, 30-35, 35-50,
>=50`), scored by `ercot128` section H (G1, fleet-aggregate loading vs RT price)
against the same actuals.

| # | prediction |
|---|---|
| **P1** | **Arming + bite.** `run_config.json` carries the resolved tranche-1 band at the measured floor in all 3 years; coal energy **falls** vs BASE by **4–10 TWh/yr** (the arm removes 3.2–4.2 GW of below-market offering). |
| **P2** | **G1 improves from BASE's 1/21, landing 8–16/21.** Direction is the load-bearing claim; the range is my honest uncertainty. |
| **P3** | **The improvement is concentrated in the LOW and MID bands** (`<15`, `15-20`, `20-25`) — those are where a $4.50 block clears that a $20.5 block does not. The `>=50` band moves **least** (< 3 pp), because at scarcity prices both bids clear. |
| **P4** | **C1 coal returns toward band**: BASE is +6.5/+9.6/+11.4 TWh; ARM lands within **±3.0 TWh** in all three years. |
| **P5** | **C3a improves** vs BASE (−35.3/−14.7/−13.2 %) by **≥ 4 pp** in every year — removing cheap coal lets gas set price more often. |
| **P6** | **The pin/impossible statistics are UNCHANGED** vs BASE (impossible plant-hours within ±10 %), because this arm touches price only. Scored by `ercot134_coal_availability_pin --bundle`. |
| **P7** | **The ERCOT-116 shape metrics do not regress**: matched-band excess and monthly-ratio spread within 2.0 pp / 0.05 of BASE. |

**Falsifier.** If G1 stays ≤ 3/21, or the improvement is *uniform* across bands
rather than low/mid-concentrated (P3), **H is refuted**: a shape lever that
moves every band equally is behaving like a level lever, which ERCOT-132 leg B
already refuted, and the real defect is then on the gas side of the ranking.

## 4. The decision rule — fixed now

**Adoption requires ALL of:**

| # | criterion |
|---|---|
| (a) | **P1** holds — armed, in `run_config.json`, and biting. |
| (b) | **G1 ≥ 8/21** AND strictly better than BASE. |
| (c) | **P3** holds — the low/mid bands carry the improvement. |
| (d) | **No new C-gate FAIL** vs BASE. |
| (e) | **LOYO** (rule 22): the G1 gain holds leaving out each of 2023/2024/2025 in turn — at most one year may regress. |
| (f) | **DOF ledger does not grow** (rule 21): the transplanted level is a measured input with `lineage_solves 0`, so entries may move measured-ward but the residual-identified count must not rise. |

A C1 or price-MAE gain **does not** license the mechanism if (b)/(c) fail — the
gates are fixed before the numbers exist precisely so a fit gain cannot be
retro-fitted into a justification (rule 1 `[R-STRUCT]`; the ercot132-leg-B §4
precedent, where C1 improved and the arm was still correctly rejected).

## 5. Execution constraints

Full span {2023, 2024, 2025} in ONE bundle per arm, years **sequential**, arms
sequential (rules 12/16). Both arms registered on the backcast dashboard with
hand-written sidecar definitions, rejection included (rule 15). Matrix cell
updated in the same session (rule 26b). Solves in-session, never CI. No holdout
year touched (rule 22). No keeper file touched without owner sign-off.

## 6. The honest limit of this arm — stated before it runs

This arm **cannot settle** whether the unoffered 61–72 % of committed coal
resource-hours is withheld, self-scheduled or telemetered down
(`DIAGNOSIS-ercot122` §4; `FINDING-ercot132-legB` §7). It tests one specific
reading — that the model's cheap block should be priced at the measured
*submitted* floor. If P3 fails, the correct next instrument is **not** another
offer probe but the **SCED TPO instrument** (`FINDING-ercot117` §E), which is
the only lane that can observe the unoffered block directly.

Recorded so that a pass is not over-claimed: **even full adoption would leave
the reach question open**, and the C6 governance attestation would remain
UNATTESTED while residual-identified DOF entries persist.
