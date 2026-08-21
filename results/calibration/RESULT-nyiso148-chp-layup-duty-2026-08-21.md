# RESULT nyiso-148 — the CHP lay-up duty split is REJECTED-AS-ARMED, and it PROVES the 2025 level is not a CHP object

Session nyiso-148. Prereg `PREREG-nyiso148-chp-layup-duty-2026-08-21.md`
committed and pushed before any arm solved (plus §9, the inert-solve disclosure,
appended before the corrected solve); phase-0 identification
`_nyiso148_chp_conduct_phase0.json`; gates record `_nyiso148_ab_gates.json`.
Frontier statement this session updates: `ASSESSMENT-nyiso148-frontier-2026-08-21.md`.
Years 2023/2024/2025, one bundle per arm; holdout freeze ACTIVE and untouched.
**The keeper `2026-08-19-nyiso-146c-state-scoped` is unchanged.**

Two runs registered (rule 15): **`2026-08-21-nyiso-148-chp-layup`** (ARM D) and
**`2026-08-21-nyiso-148-inert-plumbing`** (ARM D's first, half-inert solve, kept
as the seam-defect record). The BASE — the nyiso-147 arm-A recipe re-solved at
this HEAD — reproduces the already-registered `2026-08-20-nyiso-147a-chp-btm`
**bit-exactly** (max |Δprice| = 0.0 across every zone and hour of all three
years), so it is deliberately not double-registered: its results are already on
the dashboard and a twin would spend a retention slot for no information. That
identity doubles as the end-to-end proof that the whole nyiso-148 code change is
byte-inert at its default.

---

## 1. THE SCORECARD

| gate | verdict | |
|---|---|---|
| **D-K1** exactness | **PASS** | exactly one field differs BASE → ARM: `chp_layup_duty_split` |
| **D-K2** liveness | **PASS** | all 7 census plants collapse to a peak-ONLY band; **zero** non-census CHP plants move |
| **D-K3** the object | **FAIL** | cohort phantom −80.8 % ✓, Selkirk ≤ 2.0× ✓, **but 9 plant-years fall below 0.25× their own meter** ✗ |
| **D-K4** conduct | **PASS** | zero new D-1/D-2/D-4 rows; the base's D-2 `ST_GAS` 2024 failure is **CLEARED** |
| **D-K5** criteria | **FAIL** | C1-2024 `CC_REGULAR` PASS → FAIL vs the keeper (share **+3.04 pp** against ±3 pp) |
| **D-K6** 2025 recovery | **FAIL** | −12.2 % → **−9.9 %**, a fall of **18.9 %** against the ≥ 40 % bar (2023 leg passes, in band at +3.4 %) |

**Verdict: REJECTED-AS-ARMED.** The mechanism, its census and its wiring SHIP
default-off (rule 14; the pjm-146 / nyiso-147 disposition) — built, gated, and
held with a named successor.

## 2. WHAT THE ARM ACTUALLY DID

| system lw ($/MWh) | actual | keeper | BASE | ARM D |
|---|---|---|---|---|
| 2023 | 32.25 | 35.06 **(+8.7 %)** | 32.73 (+1.5 %) | 33.36 **(+3.4 %)** |
| 2024 | 38.12 | 38.74 (+1.6 %) | 35.84 (−6.0 %) | 36.63 **(−3.9 %)** |
| 2025 | 66.43 | 64.96 (−2.2 %) | 58.36 **(−12.2 %)** | 59.86 **(−9.9 %)** |

| C1 (grid-delivered TWh) | actual | BASE | ARM D |
|---|---|---|---|
| CC_CHP 2023 | 14.802 | 16.321 (+1.52) | **15.031 (+0.23)** |
| CC_CHP 2024 | 17.017 | 18.548 (+1.53) | **17.044 (+0.03)** |
| CC_REGULAR 2023 | 33.012 | 31.336 (−1.68, −0.5 pp) | **31.932 (−1.08, −0.0 pp)** |
| CC_REGULAR 2024 | 34.060 | 36.520 (+2.46, +2.4 pp) | **37.283 (+3.22, +3.04 pp — FAIL)** |

**On the class it targets the arm is close to exact.** CC_CHP lands at +0.23 TWh
(2023) and **+0.03 TWh** (2024) against a base of +1.52 / +1.53, and CC_REGULAR
2023 goes to −0.0 pp of share. Against the base it turns **C3a-2025 FAIL → PASS,
C3b-2025 FAIL → PASS and C8 FAIL → PASS**, and it clears the base's D-2
`ST_GAS`-2024 30.4 % forced-share failure outright. On C3a it beats the keeper in
2023 (+3.4 % against +8.7 %) — the nyiso-147 upstate repair, carried.

**It fails on one marginal share crossing and on two structural facts.** The
C1 crossing is **0.04 pp** (share +3.04 against ±3 pp; the TWh leg still passes
at +3.22 of ±3.98). The two structural facts are §3 and §4, and they are the
result.

## 3. THE FINDING THAT MATTERS — energy is CONSERVED, so the 2025 level is NOT a CHP object

The arm removes **1.29 / 1.50 / 1.68 TWh** of CC_CHP energy. Almost all of it
comes straight back in the next-cheapest gas:

| Δ TWh (ARM − BASE) | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_CHP | **−1.29** | **−1.50** | **−1.68** |
| CC_REGULAR | +0.60 | +0.76 | +0.76 |
| ST_GAS | +0.46 | +0.48 | +0.61 |
| CT_PEAKER | +0.03 | +0.03 | +0.16 |
| CT_CHP + ST_CHP | +0.09 | +0.11 | +0.14 |
| import | +0.12 | +0.12 | +0.02 |
| **gas total** | **−0.01** | **−0.11** | **−0.02** |

So the price moves only **+$0.63 / +$0.79 / +$1.50**. **The 2025 −12.2 % survives
the removal of the entire CHP phantom**, because the marginal offer barely
changes when the load is re-served by a unit priced almost the same.

This settles, on evidence, a question the nyiso-147 successor list left open:
**the 2025 dear-gas level is an OFFER-LEVEL object, not a capacity or membership
one.** Of the base's $8.07/MWh gap to actual, the whole CHP capacity+conduct
repair recovers **$1.50 (18.6 %)**; **$6.57 is a different object.** No future
CHP membership work should be scoped against the 2025 level.

## 4. WHY THE CONSTRUCTION IS WRONG FOR THIS POPULATION — one band cannot make a graded response

The pre-registered **overkill** leg is what fails, and it fails informatively.
Model energy as a multiple of each plant's own metered CAMPD gross:

| plant | 2023 base → arm | 2024 base → arm | 2025 base → arm |
|---|---|---|---|
| 10725 Selkirk | 2.01× → **0.03×** | 6.78× → **0.04×** | 3.18× → **0.05×** |
| 54041 Lockport | 14.28× → **0.89×** | 6.78× → **0.24×** | 6.39× → **3.96×** |
| 50450 Oswego | 3.91× → 0.62× | 3.35× → 0.60× | 2.52× → **1.92×** |
| 50451 Yerkes | 2.76× → 0.27× | 3.14× → 0.20× | 2.87× → **2.15×** |
| 50449 Silver Springs | 1.60× → 0.19× | 1.50× → 0.21× | 1.56× → 1.16× |
| 54076 Olean | 1.53× → 0.25× | 1.76× → 0.75× | 1.99× → 1.68× |
| 10617 Beaver Falls | 0.35× → 0.00× | 0.99× → 0.05× | 1.26× → 1.25× |

The response is **bang-bang**: at one high band the cohort is essentially OFF in
the cheap years and **STILL OVER** in the dear year. The real plants do neither —
they run 1.6–18.6 % of hours in short runs (10–43 h medians, 39–187 starts a
year) and scale *with* price, as Selkirk's own meter shows: 156.9 → 107.7 →
**384.8 GWh** across 2023/2024/2025.

**The identification the successor needs is therefore a price-conditional
on-share, not a band level.** The census membership is right (D-K2 clean, D-K4
clean, CC_CHP volume near-exact); it is the OFFER SHAPE that is too coarse. A
single peak multiplier encodes "never, unless scarce"; the measured conduct is a
duty *curve*. That statistic — each census plant's metered on-share as a
function of its own zone's realized price, which regenerates from CEMS + LMP for
any vintage and responds to changed conditions exactly as rule 13 requires — is
the pre-registration a successor session should file. It is **not** attempted
here: it is a new construction, not a re-arm.

## 5. WHAT WAS *NOT* WRONG, AND MUST NOT BE RE-LITIGATED

* The **census membership** is sound: 7 plants, clean 18/18-vs-13/18 separation,
  zero non-cohort movement, zero new conduct failures, and CC_CHP volume landing
  within 0.03 TWh of its own corrected bench in 2024. **Do not re-derive it
  against a residual** (rule 23).
* The **CAMPD-degeneracy guard** earned its place before any solve: three plants
  (RED-Rochester 10025, Ticonderoga 54099, Cornell 50368) would have been
  convicted by a naive extension of the criterion while EIA-923 reports
  439–950 GWh of real generation from them.
* The **measured BTM shares** (nyiso-147, frozen) are untouched and remain
  correct; nothing here weakens the proof that the 2023 upstate level is bought
  by the 35 % carve.
* The **availability envelope** is not the missing piece either: it already
  derates five of the seven cohort plants, and the two it misses (Selkirk at
  28.1 %, Lockport reading **96.8 % available** against a 3.6 % metered CF) are
  exactly the two the offer shape has to handle.

## 6. THE INERT FIRST SOLVE (registered, and a lesson that has now cost two lanes)

ARM D's first solve armed its census correctly and was still **inert by half**:
`pct_mc` reached 0 but `pct_peak` was clobbered straight back by the
thermal-tranche artifact and the duct-burner map, because the leg was wired at
`fleet_to_bins` and mirrored in `offer_curves` but **not** at
`assembly.py::bins_to_fleet` — the load-bearing override whenever a run reads a
cached binned-fleet frame, which the NYISO keeper does. Cohort energy moved < 3 %
and system lw 2025 moved **$0.04**.

This is verbatim the defect `cc_reserve_duty_split`'s own in-code comment records
from nyiso-146b. It recurred because that sibling's frame-side seam was mirrored
and its load-bearing one was not. **It was caught by this arm's own D-K2
anti-inert gate** — which is why that gate tests band COMPOSITION rather than a
price delta: on prices alone the inert solve reads as a clean near-null result.
Disclosed in PREREG §9 before the corrected solve, registered as
`2026-08-21-nyiso-148-inert-plumbing`, and the repair is verified in both
directions (armed: Selkirk enters the LP as peak 754 MW @ $64.69, Lockport as
peak 221 MW @ $49.55, single-band; flag-off: the base recipe's 149 CHP tranches
reproduce **identically** post-fix).

**Standing note for any future duty-split leg in any ISO: wire
`assembly.py::bins_to_fleet` FIRST, and prove liveness on band composition
before reading a single price.**

## 7. DISPOSITIONS TAKEN (all pre-declared in PREREG §7)

1. **D-K3 fails → verdict `R` for the cell**, with §4 stating which conduct
   statistic would reproduce the measured behaviour. The NYISO matrix shard is
   stamped in this session (rule 28b).
2. **D-K5 clears? No → ARM E is NOT solved.** `cc_reserve_duty_split`'s re-arm
   was conditioned on ARM D clearing its gates; its standing prereg
   (`PREREG-nyiso146b §ARM C`) is untouched and its bars are not re-litigated.
3. **The recovered share of the −12.2 % is quantified and the owner decision
   card written** for the remainder:
   `docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`.

## 8. GOVERNANCE

* Holdout freeze **ACTIVE**; 2023–2025 only; no out-of-training year solved,
  scored, registered or read.
* Rule 15: both completed solves registered in this session; the base is the
  registered `2026-08-20-nyiso-147a-chp-btm` and its identity is proved above.
* Rule 21 `[R-DOF]`: the leg carries **zero** free parameters — the level is the
  class's existing peak multiplier and the membership is a plant-code set from a
  degeneracy-guarded conduct test.
* Rule 19 `[R-ONE-MECH]`: cohorts disjoint by class scope, pinned by a test.
* DO-NOT-REDO honoured throughout; Flynn's start-count excess untouched by
  design; RHO_CLIP, the Iroquois winter spread, the D-4 vintage-guard charter
  and the Astoria attribution all out of lane and untouched.

## 9. REPRODUCTION

```
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso147_armA_recipe --out-dir results/calibration/nyiso148_base
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso148_armD_recipe --out-dir results/calibration/nyiso148_armD
python scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso148_armD --iso NYISO --years 2023 2024 2025 --json-out results/calibration/nyiso148_armD/legitimacy_diagnostics.json
PYTHONPATH=.:src python scripts/probes/_nyiso148_ab_gates.py
python scripts/calibration_verdict.py --run-id 2026-08-21-nyiso-148-chp-layup
```
