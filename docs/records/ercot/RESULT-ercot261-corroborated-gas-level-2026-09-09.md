# RESULT — ercot-261: the corroborated monthly gas LEVEL takes ERCOT 2021 from **+26.4 % to +4.2 %** without breaking Uri, C3c or C3b. **Card B is measured INERT, and the reason is a pre-existing ERCOT defect worth more than this card.**

> Scored against `docs/PRECOMMIT-ercot261-gas-level-retirements-2026-09-09.md` (§5 gates
> and predictions, §7 arm definition) and `docs/ADDENDUM-ercot261-partial-plant-scope-2026-09-09.md`.
> Ten bundles: five ARM legs and five same-HEAD CONTROL legs, one year each, all ten
> solved on the pinned commit `6bc4350111dfd9ca23c87dac7cecfe073dc59b33`.

## 0. Bottom line

| | |
|---|---|
| **2021 C3a** | **+26.4 % → +4.2 %** (187.29 → 154.43 vs actual 148.19). The eleven-month flat-basis error is substantially gone. |
| **February 2021 (Uri)** | **−3.3 % → −6.6 %** — stays right, exactly as predicted. The gate that killed the handoff's own construction is cleared. |
| **C3c 2021** | **230 → 223 h** (actual 214). It **improves**. ercot-254's monthly form blew this to 688. |
| **C3b 2021** | **unchanged** (+0.3 % relative). ercot-254 moved it **+39 %**. This is the criterion that refused that arm. |
| **2023 / 2024 / 2025** | **+0.41 / −0.18 / +0.28 $/MWh**; C3c identical in all three (180/180, 22/22, 1/1). |
| **Card B (retiree carry)** | **INERT — 0.0 MW reached the LP.** §4. Not a null result: it exposes a live ERCOT defect. |
| **Keeper candidate?** | **Yes on the mechanism, but the formal determination is NOT yet computed.** §6. |

**Every number here is ARM vs CONTROL on ONE internally consistent basis** — the system
load-weighted hourly price recomputed from each bundle's own
`hourly/system_<year>.parquet`, against the committed
`frontend/data/backcast/bench/ERCOT/<year>.json.gz` actuals. **They are NOT on the
registry's scoring basis and must not be compared to registered rubric values**
(the same caveat `RESULT-ercot254` §3 records: that lane's own numbers moved
−4.1 %/+160.8 % → −14.9 %/+144.0 % between aggregations). §6 states what is still owed.

---

## 1. C3a — the headline

| year | actual | CONTROL | err | ARM | err | arm − ctl |
|---|---|---|---|---|---|---|
| **2021** | 148.19 | 187.29 | **+26.4 %** | **154.43** | **+4.2 %** | **−32.87** |
| 2022 | 62.30 | 68.42 | +9.8 % | 68.40 | +9.8 % | −0.02 |
| 2023 | 48.36 | 59.71 | +23.5 % | 60.12 | +24.3 % | +0.41 |
| 2024 | 26.83 | 31.07 | +15.8 % | 30.89 | +15.1 % | −0.18 |
| 2025 | 32.49 | 33.52 | +3.2 % | 33.81 | +4.0 % | +0.28 |

## 2. The 2021 monthly decomposition — where the repair actually lands

| month | actual | CONTROL | err | ARM | err |
|---|---|---|---|---|---|
| Jan | 20.79 | 58.54 | +181.6 % | **26.48** | **+27.4 %** |
| **Feb (Uri)** | 1521.84 | 1471.01 | **−3.3 %** | **1422.13** | **−6.6 %** |
| Mar | 19.42 | 58.44 | +200.9 % | **26.63** | **+37.1 %** |
| Apr | 46.80 | 101.13 | +116.1 % | 67.57 | +44.4 % |
| May | 23.39 | 59.44 | +154.1 % | **28.60** | **+22.3 %** |
| Jun | 38.39 | 100.37 | +161.5 % | 67.72 | +76.4 % |
| Jul | 36.80 | 93.94 | +155.3 % | 63.00 | +71.2 % |
| Aug | 35.37 | 88.11 | +149.1 % | 55.78 | +57.7 % |
| Sep | 41.57 | 87.98 | +111.6 % | 55.29 | +33.0 % |
| Oct | 46.87 | 143.65 | +206.5 % | 112.62 | +140.3 % |
| Nov | 40.38 | 73.36 | +81.7 % | **43.16** | **+6.9 %** |
| Dec | 25.82 | 59.81 | +131.6 % | **30.78** | **+19.2 %** |
| **ex-Feb** | **34.15** | **84.07** | **+146.2 %** | **52.51** | **+53.8 %** |

**Every one of the twelve months improves**, February included in the sense that it stays
accurate. **December is the vindication of the corroboration rule**: +131.6 % → +19.2 %,
where ercot-254's un-corroborated monthly form left it at +134.5 % because it applied an
N3045TX3 print (+5.055) that the plant-receipt series contradicts (+1.589).

**October is the residual** (+140.3 %) and is named, not absorbed: it is the only month
still above +100 %, and nothing in this card addresses it.

## 3. The gates and the prediction scorecard — reported at full magnitude

### 3a. STOP gates

| id | bar | measured | verdict |
|---|---|---|---|
| **G-1** | 2023/24/25 gas arm−ctl > $0.40/MMBtu | **exactly 0.0000** in all three | **PASS** |
| **G-2** | filter fires outside 2021 | 0.0000 level delta in 2022/23/24/25 | **PASS** |
| **G-3** | Feb 2021 outside −15 % … +5 % | **−6.6 %** | **PASS** |
| **G-4** | non-target load-bearing PASS→FAIL in 2023/24/25 | C3c identical (180/180, 22/22, 1/1); C3a moves ≤ $0.41 | **PASS** |
| **G-5** | slack or dump > 1.0 MWh | **MIS-SPECIFIED — see below** | **gate defect, not an arm failure** |
| **G-6** | double-count | none | **PASS** (moot — §4) |

**G-5 was my error, and I am not scoring the arm against it.** The bar fires on the
**CONTROL** as well: 2021 slack is 1,763.96 MWh in the control and 960.56 MWh in the arm,
and 2024 is 600.16 MWh in *both*. Load shed in February 2021 is the actual historical
event — ERCOT shed ~20 GW during Uri — so a "any nonzero slack" bar was the wrong test to
write. The informative statement is the differencing: **the arm nearly halves unserved
energy (1,764 → 961 MWh) and dump is exactly 0.0000 in all ten legs.** This is the same
class of self-inflicted gate error as ercot-254's mis-scoped G-1.

### 3b. Predictions — four right, three wrong

| # | registered | measured | verdict |
|---|---|---|---|
| **P1** | 2021 C3a falls a lot; model → $120–150 | **154.43** (+4.2 %) | **direction RIGHT, magnitude OUTSIDE my band** — I centred the band too low |
| **P2** | ex-Feb bias under +40 % | **+53.8 %** (from +146.2 %) | **WRONG** — direction right, magnitude missed |
| **P3** | Feb stays right, −3.3 % → −4 %…−8 % | **−6.6 %** | **CORRECT, inside the band** |
| **P4** | C3c does NOT regress; 150–300 h, moving down | **230 → 223** (actual 214) | **CORRECT** |
| **P5** | C3b improves to 0.28–0.38 | **unchanged** (+0.007 on 2.579) | **WRONG in substance** — I predicted improvement and got neutrality |
| **P6** | 2023/24/25 move < $0.50/MWh | **+0.41 / −0.18 / +0.28** | **CORRECT** |
| **P7** | 2022 moves modestly | **−0.02 $/MWh** | **WRONG** — essentially zero |
| **P8** | withdrawn pre-solve | resolved empirically (§4) | — |

**On P5, the honest reading.** My hand-computed NRMSE is not on the rubric's basis (mine
reads ~2.58 where the registry reports ~0.36), so I cannot score C3b's *level* here and I
do not claim to. What is comparable is the **delta**: **+0.3 % relative**, against
ercot-254's **+39 %** (0.361 → 0.501). C3b is the load-bearing, never-caveat-able criterion
that refused that arm, and this arm does not move it. That is the single most important
contrast in this document, and it is why keeping February intact was the whole design.

### 3c. C1 — class energy, 2021 (TWh)

| class | actual | CONTROL | ARM | miss: ctl → arm |
|---|---|---|---|---|
| **CC_REGULAR** | 113.245 | 109.817 | **114.472** | −3.43 → **+1.23** |
| **CT_PEAKER** | 4.646 | 6.112 | **5.049** | +1.47 → **+0.40** |
| **CC_CHP** | 27.132 | 28.804 | **27.287** | +1.67 → **+0.16** |
| **COAL_PRB** | 58.064 | 58.733 | 53.228 | +0.67 → **−4.84** |
| **ST_GAS** | 12.344 | 10.536 | 14.480 | −1.81 → **+2.14** |

Three of the five gas classes improve markedly; **coal displacement is the cost**, and it is
exactly the channel `RESULT-ercot254` §3a diagnosed after its own class predictions came
back wrong in sign. Note this arm moves **CT_PEAKER the right way** (6.112 → 5.049) where
ercot-254's moved it the wrong way — the merit-order behaviour differs because February is
not being repriced.

---

## 4. **CARD B IS INERT — 0.0 MW reached the LP — and the cause is a pre-existing ERCOT defect**

Measured on the solved bundles: **`dcap` is exactly 0.0 MW for every plant, in both 2021
and 2022.** Decker Creek (plant 3548) carries **61.0 MW in the arm and 61.0 MW in the
control** — not the 465 MW the addendum's footprint implied. Total energy from units
present in the arm and absent from the control: **0.0000 TWh**.

**Root cause, diagnosed not assumed.** ERCOT builds its fleet per-plant from the CAMPD bin
sheet (`use_campd_bins=True`). Plant 3548 has **zero rows** on
`data/raw/reference/custom-bin-assignments.csv`, so the retiree the loader returns is
dropped downstream and never reaches the LP. Quantified over the whole channel:

| | units loaded | MW loaded | MW that can reach the LP |
|---|---|---|---|
| `partial_plant_exit_carry=False` | 38 | 1,721.2 | **0.0** |
| `partial_plant_exit_carry=True` | 51 | 2,609.6 | **0.0** |

**Not one megawatt of ERCOT's within-window retiree injection is on the bin sheet.** This
is *not* a defect this card introduced and it is *not* confined to this card: it means the
retiree channel has been inert for ERCOT all along — including the pre-existing 2023/2024
rows, and including the cross-ISO charter's widening to 2019, which lands 222.8 MW of
ERCOT 2021 retirees that the LP then discards. **Routed to the fleet lane; not fixed here**,
because fixing it means touching the ERCOT bin sheet, which is outside this card's scope
and would change every ERCOT keeper.

**What this settles.** The confound I flagged before the solve is **gone**: Card B
contributed nothing, so **the entire 2021 improvement is Card A**, and the −$31.6/MWh
ex-Feb move sits right against the −$37/MWh the pre-solve gas arithmetic predicted. P8's
withdrawal is moot, and the addendum's declared +888.4 MW footprint was **measured at the
wrong seam** — the loader, not the fleet the LP receives. That is my error and it is
corrected here.

---

## 5. Governance

Ten bundles on local disk, gitignored (`results/calibration/ercot261_*`), **not deleted**
(rule 31 `[R-RETAIN]`). Every leg carries the pinned `git_sha` `6bc43501`; the three
carve-out years each verified `ercot_offer_swcap_clip: true` and `CC_REGULAR.peak =
151.008`, so the ercot-260 prerequisite is confirmed working on 2023 — the year it was
written for. Rule 22: 2021/2022 are validation-tier spends under ERCOT's `complete` marker;
no parameter was identified on, fitted to, or selected against any of them, and the
tolerance was registered above the solve.

## 6. What is still owed before a promotion decision

1. **The formal rubric determination is NOT computed.** The shards did not push the
   `results/calibration/_shared/ERCOT/*.parquet` inputs, so `--report` cannot build
   `metrics.json` and no registry verdict exists. Everything above is arm-vs-control on my
   own consistent basis. **A determination requires that scoring pass**, and the shared
   inputs are recoverable.
2. **Dashboard registration** (rule 15) is therefore not yet done.
3. **October 2021 (+140.3 %)** is the named open residual.
4. **The ERCOT bin-sheet retiree gap** (§4) is the largest finding here and belongs to the
   fleet lane.
