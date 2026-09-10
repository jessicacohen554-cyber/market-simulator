# RESULT — SPP-63: the curtailment ceiling reproduces measured wind almost exactly, and the SCREEN KILLS IT on two pre-registered gates

**Lane** SPP-63 · **PRECOMMIT** `docs/handoffs/PRECOMMIT-spp-63-curtailment-ceiling-2026-09-10.md`,
pushed at `efd60202` **before any solve** · **Screen shard** pinned to `92b59c7335b9ab44e095819060b1bcbae998b461`,
branch `claude/spp63-screen-2025` · **LP spent: ONE year (~150 s).** Rule 32 `[R-SHARD]`: the parent
ran no LP. **The span was NOT spent.** · **Keeper UNCHANGED** `2026-09-10-spp-62-vintage-census`.

**RESULT IN ONE LINE.** Arming `spp_curtailment_ceiling` does exactly what its own arithmetic says —
2025 wind falls **122.0430 → 110.2248 TWh**, landing **within 0.232 TWh of the EIA-930 actual
110.457** — but the model cannot yet absorb it: **C3b price-shape NRMSE goes 0.167 → 0.253 (band
≤0.20), a load-bearing PASS → FAIL**, and slack rises **0 → 211.208 MWh** against a pre-registered
ceiling of 100. **Two of five gates fail, so the screen STOPS and the 2023–2025 span is not spent.**
And the energy does not go where the C1 failure is: **ST_GAS FALLS 0.693 TWh** while **COAL_PRB rises
7.099**, pushing the coal family from **+0.72 to +8.69 TWh** against actual.

---

## 1. THE GATE BOARD

Every gate was pre-registered in the PRECOMMIT §5 before the solve; none reads C1.

| gate | asks | measured | verdict |
|---|---|---|---|
| **G-1** | config identity & liveness | `spp_curtailment_ceiling: true`, `spp_curtail_depth_wind: 0.288137`, ten fossil classes at 0.93 × 4 bands, census 32 lines / `6193,prb` present | **PASS** |
| **G-2** | reach — the dispatch response has the direction and order of magnitude the pre-solve delta implies | wind **122.0430 → 110.2248**, fall **11.818 TWh**, band 9.0–15.0 | **PASS** |
| **G-3** | the allocation identity it asserts | decile-0 carries **26.049 %** of the removal vs a **10.000 %** flat reference — **2.6049 ×**, gate > 1.15 | **PASS** |
| **G-4** | no new forcing | dump **0.000 MWh** ✓, slack **211.208 MWh** against the pre-registered **≤ 100.0** (control 0.0000) | **FAIL** |
| **G-5** | no non-target load-bearing regression | **C3b NRMSE 0.167 → 0.253** (band ≤0.20) — **PASS → FAIL**. C3a survives at **+9.9 %** against ±10 %, from +2.2 % | **FAIL** |

**The gates are not re-cut.** G-4's bound and G-5's criterion set were fixed in the PRECOMMIT before
this solve existed; re-reading either now against the result it would decide is the fitted-mechanism
selection rule 1 `[R-STRUCT]` condition (c) forbids, and this lane does not do it. The screen is a
STOP gate and it stopped the arm.

**G-5 bit exactly where the PRECOMMIT said it would.** §5 declared it "the gate with real bite" and
named C3b's headroom as **0.033**; the arm blew through it by **0.053**.

## 2. WHAT THE MECHANISM ACTUALLY DID — reported at full magnitude

2025, arm minus control (keeper 7's committed sidecars), TWh:

| class | control | arm | Δ |
|---|---|---|---|
| **wind** | 122.043 | **110.225** | **−11.818** |
| **COAL_PRB** | 81.438 | **88.537** | **+7.099** |
| CC_REGULAR | 35.824 | 39.504 | +3.680 |
| COAL_LIGNITE | 6.986 | 7.857 | +0.871 |
| CT_PEAKER | 14.883 | 15.524 | +0.641 |
| **ST_GAS** | 9.206 | **8.513** | **−0.693** |
| CC_CHP · CT_CHP · solar · ST_CHP · hydro | — | — | +0.127 / +0.047 / +0.022 / +0.003 / +0.003 |

**Family volumes against EIA-930 actual (2025):**

| family | control | arm | actual |
|---|---|---|---|
| wind | +11.586 | **−0.232** | 110.457 |
| gas | −12.755 | **−8.950** | 75.948 |
| coal | **+0.721** | **+8.691** | 87.703 |

**Prices:** load-weighted **$29.2249 → $30.9944** (+6.1 %); **negative-price hours 167 → 0**;
hours > $200 **0 → 2** (against 68 actual — C3c still fails by two orders of magnitude).

## 3. THE THREE THINGS THIS MEASURES, STATED PLAINLY

**(a) The wind repair itself is essentially exact, and that is a real result.** The ceiling takes the
model from **+11.586 TWh of wind** to **−0.232**, at a depth set ex ante from SPP's published
curtailment series and never swept. G-2 and G-3 both pass — the mechanism reaches its target and
binds where its own measured driver says it should, 2.6 × concentrated on the lowest-net-load decile.
Nothing in this result impeaches the mechanism's construction.

**(b) The model cannot yet absorb it, and C3b is where that shows.** Removing 11.8 TWh of zero-cost
wind removes SPP's entire negative-price regime (167 hours → 0) and lifts the level 6.1 %. The
monthly load-weighted price NRMSE more than doubles the distance to its band. This is a **real
structural finding about the price formation**, not a fit complaint: the model was reproducing SPP's
monthly price shape *while carrying 11.8 TWh of wind that should not have been dispatched*, which
means the shape was right for the wrong reason and something else is now exposed.

**(c) The recovered energy goes to COAL, not to gas steam — which corroborates this lane's own
FINDING §6.** The C1 failure this program is trying to close is `ST_GAS`, and the ceiling makes
`ST_GAS` **worse** in 2025 (−0.693 TWh) while handing **7.099 TWh to COAL_PRB** and converting a
nearly-exact coal family (**+0.72**) into a badly out-of-band one (**+8.69**). That is the
merit-order inversion `FINDING-spp-63-2026-09-10.md` §6 measured — SPP gas steam runs at 0.47–0.52 ×
its measured capacity factor while the model offers it *above* CT_PEAKER at every stack depth to
6 GW — operating on a correctly-sized stack for the first time. **The wind repair does not reach the
ST_GAS rows; it re-routes the error into coal.**

## 4. WHY THE SPAN WAS NOT SPENT

Rule 29 `[R-SCREEN]` (2): the full span runs only if the screen clears its pre-registered gate. It
did not clear two. **~440 s of LP and a three-year bundle were not spent**, which is the entire
purpose of the screen and is reported as this lane's result rather than as a shortfall.

**What a G-4/G-5 stop does NOT mean, quoting the PRECOMMIT §5 rather than deciding it now:** *"Under
rule 1 `[R-STRUCT]` a structurally-correct mechanism is never rejected because the fit moved. A G-5
stop is a **spend decision** — it says the root cause behind the regression must be found before
three years of LP are committed — and it is **not** a verdict of `R` on the mechanism. The matrix
cell would go to `O`, not `R`."* That is what this lane does.

## 5. THE SUCCESSOR CARDS

> **R-bb — SPP price formation without the phantom wind.** C3b NRMSE 0.167 → 0.253 and the loss of
> all 167 negative-price hours say the keeper's monthly price shape depends on dispatching 11.8 TWh
> of wind the market curtailed. Root-cause that before the ceiling is re-screened; a ceiling that
> passes G-5 is a ceiling landing on a stack whose price formation does not need the phantom energy.
> **Do NOT re-cut `spp_curtail_depth_wind` to make G-5 pass** — the depth is measured, one config
> across all years, and re-cutting it against a gate is exactly what rule 1 condition (c) forbids.

> **R-ba (unchanged, and now corroborated on a corrected stack) — the ST_GAS / CT_PEAKER merit-order
> inversion.** This screen is the evidence that the wind repair alone does not reach the C1 rows: the
> energy went to COAL_PRB. Whatever finally closes ST_GAS has to fix the *order*, and this arm shows
> the order is wrong independently of the wind level.

## 6. GOVERNANCE

- **Rule 29 `[R-SCREEN]`:** screen year **2025** named in the PRECOMMIT on the mechanism's own
  **measured footprint** (12.3556 TWh, largest of the three) and deliberately not a failing-residual
  year. Gates STOP-only, none reading C1. The screen bundle is **never registered** and its numbers
  are **never quoted as keeper numbers**; this document is the record (rule 29(c)).
- **Rule 15 `[R-DASHBOARD]`:** nothing to register — no span bundle exists. A screen is not a run.
- **Rule 31 `[R-RETAIN]`:** **nothing deleted.** `results/calibration/spp63_screen_2025/` is
  gitignored (`results/calibration/spp63_*/`), which is what discharges rule 29(c); it lives on the
  shard's own container and the slim artifacts are committed under
  `results/shard-staging/spp63/2025/` so the parent could score G-5 at all.
- **Rule 28 `[R-MECH-MATRIX]`:** `spp_curtailment_ceiling` **`U` → `O`**, exactly as pre-registered —
  **not `R`**: G-1/G-2/G-3 pass exactly, the mechanism is a rule-14-owed repair, and marking it `R`
  would trip rule 28(a)'s do-not-redo discipline against something the model actually owes.
- **Rule 21 `[R-DOF]`:** no ledger change — the span that would have carried the added entry was not
  solved. `scripts/gen_spp63_attestation.py` is committed and ready if the span is ever spent.
- **G-5 instrument:** `scripts/lib/spp63_g5.py`, **validated against the scorer on keeper 7 before
  use** (C3a 25.65 / 25.79 / 29.23 and C3b 0.172 / 0.172 / 0.167, reproduced exactly). It closes the
  gap lane SPP-58 had to report as "G-5 unavailable" — `calibration_verdict.py` can only score a
  registered run, and rule 29(2) forbids registering a screen.
- **`[R-HOLDOUT]` removed 2026-09-09:** no year is protected from being iterated against, so every
  number here is model-**SELECTION** evidence, not a certified out-of-sample skill claim.
- **SPP remains NOT-YET and is not calibrated.** Two criteria still fail on the keeper, so rule 22
  `[R-C3C]` still cannot fire.
