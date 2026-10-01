# FINDING — ERCOT-110: coal is not capability-constrained; the model's coal derate was hiding a merit-order error

**Date** 2026-07-24 · **ISO** ERCOT · **Year** 2023 · **Run**
`2026-07-24-ercot110-coal-dam-availability` (PROBE) ·
**Bundle** `results/calibration/ercot110_coal_dam_avail`
**Gate** `ScenarioConfig.ercot_thermal_dam_availability_coal` (default **off**; keeper unchanged)

## 1. What was tested

ERCOT-109 measured the 2023 summer scarcity gap: at the 122 true scarcity hours of
Jul–Sep the model serves the same load with **1.7 GW less gas**, backfilled by cheap
resource (coal +424 MW among it), and coal is 0.0 % forced (D-2), so the coal error is
merit-order elasticity rather than a floor. The ERCOT-110 charter hypothesised the
missing structure was a **summer capability ceiling**: the 60-Day DAM disclosure had
been extended to every gas class (ERCOT-96 class-hour, ERCOT-97 plant-hour) but coal was
never mapped, so coal alone still ran on the statistical/CAMPD availability stack.

That gap was real and is now closed. The hypothesis about its *direction* was wrong.

## 2. Pre-committed adjudication (set before any result was read)

> **PRIMARY** — the Jun–Sep coal ratio moves toward 1.0 from 1.15–1.18, and Mar–Apr does
> not degrade further.
> **EXPECT** — annual coal gets worse before better; adding a summer ceiling without the
> shoulder-month floor pushes annual *below* actual.
> **FAIL SIGNATURE** — the ercot41/43 over-fire: tail hours priced > $200 blow past ~181.

**Verdict: PRIMARY FAILS.** Jun–Sep mean model/actual moved **away** from 1.0,
1.170 → 1.206. Mar–Apr did not degrade — it improved sharply (0.775 → 1.067). Annual moved
*above* actual (1.028 → 1.161), the opposite of the pre-committed expectation, because the
mechanism turned out to be a restore rather than a cap. The fail signature is **absent**:
the model under-fires *more*, not less (tail hours caught 76 → 50).

## 3. What the disclosure actually says

Measured ERCOT coal availability, 2023: **mean 0.805, median 0.824**, p5/p95 0.617/0.921,
100 % hourly coverage on the 335 covered days (the Oct-2023 publication hole is the only
gap). That is **higher** than the model's statistical + CAMPD stack assumed. The
bidirectional water-fill therefore **restores** coal capability rather than capping it:

| | keeper | ercot110 |
|---|---|---|
| hours coal < 4,000 MW | 1,542 | **351** |
| hours coal < 6,000 MW | 3,504 | **1,853** |
| annual coal | 64.0 TWh | **72.3 TWh** |

The dominant effect is removal of **phantom full-stops**: the CAMPD detector is a ≥5-day
full-stop rule, so it both zeroes units the DAM shows as available and misses partial
derates. W A Parish G8 is the cleanest single case — it reads OUT or zero HSL for ~96 % of
2023 (852 live resource-hours) while the model carried its 610 MW as available all year.

## 4. Results

Model/actual coal, monthly (keeper → ercot110):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **yr** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| keeper | 0.84 | 0.83 | 0.73 | 0.82 | 1.06 | 1.15 | 1.18 | 1.17 | 1.18 | 1.04 | 1.01 | 0.92 | **1.028** |
| ercot110 | 1.28 | 1.24 | 1.05 | 1.08 | 1.17 | 1.20 | 1.21 | 1.20 | 1.21 | 1.04 | 1.13 | 1.08 | **1.161** |

Secondary (reported, not optimised):

| metric | keeper | ercot110 |
|---|---|---|
| C3a 2023 | −27.3 % | −25.2 % |
| C3c settle | 76/181 | 50/181 |
| coal over-run @ 122 scarcity hours | +424 MW | +922 MW |
| cheap-stack surplus | 118/122 h, median +871 MW | 122/122 h, median +1,399 MW |
| gas deficit | −1.7 GW | −2.2 GW |
| corr(cheap surplus, gas deficit) | −0.77 | −0.79 |

## 5. The finding

**Coal was not capability-constrained in reality.**

| | coal energy | share of measured-available capability |
|---|---|---|
| measured available (0.805 × 13.6 GW × 8760) | 95.9 TWh | 100 % |
| **actual** | 62.3 TWh | **65 %** |
| keeper model | 64.0 TWh | 67 % |
| ercot110 model | 72.3 TWh | 75 % |

Real ERCOT coal left ~34 TWh of *available* capability undispatched in 2023. The summer
over-run is therefore a **merit-order / commitment error, not a missing ceiling** — and
the model's statistical coal derate was silently substituting for the missing coal-side
economics. Giving coal its true availability removes the substitute and exposes the
underlying error at full size.

This is exactly the **rule-11 signature**: swapping an estimate for real data made the
backcast worse *because the estimate was compensating for something else miscalibrated*.
Per rules 1/11/13 the measured input is structurally correct and **stays in the codebase**
behind its gate — it is not reverted because the residual moved. It must not be promoted
until the root cause it exposes is fixed.

## 6. Consequences for the next lane

1. **ERCOT-111 should be re-chartered.** The charter assigned the shoulder months to a
   "coal commitment bridge" (a floor). Measured availability **alone** largely closes
   them — Mar 0.73 → 1.05, Apr 0.82 → 1.08 — so a shoulder-month floor would now be a
   second mechanism on an already-explained residual (rule 19). The open question is the
   opposite one: **why does the model dispatch coal that the real market left idle?**
   Candidates: coal offer level/shape vs the measured DAM stack, take-or-pay and PRB
   passthrough interacting with the restored capability (frozen against residuals — rule
   23 — so they move only if their source data moves), and coal min-down/commitment
   economics. Any ERCOT-111 work should be run **with this gate armed**, since it is the
   structurally-correct availability basis.
2. **The reserve-side closure (ERCOT-107/108) is unaffected.** This is a quantity-side
   result and does not reopen the bistable on-line-capacity envelope.
3. **No full-span or leave-one-year-out run was made.** The pre-committed gate for those
   was "IF IT HOLDS", and it did not.

## 7. What landed regardless of the verdict

The coal scope extension is permanent infrastructure, gated off:

* `scripts/data/derive_ercot_thermal_dam_availability.py` maps `CLLIG` → the single class
  `COAL`. One class, because that is the grain **both** sides carry: the disclosure has no
  fuel basin, and the ERCOT LP assigns the whole coal fleet `Plant_Group = COAL` (the
  COAL_PRB / COAL_LIGNITE split is applied only at *reporting* time). Keying the
  supply-rank split would match no generator at the apply seam and leave the overlay
  **silently inert** — a trap this session fell into and caught before scoring.
* `data/raw/reference/ercot-dam-coal-site-seeds.csv` — a new reviewed adjudication of all
  26 DAM coal sites onto the 10 modelled coal plants (ERCOT coal mnemonics are substation
  codes with no lexical bridge to the EIA name: LEG = Limestone, OGSES = Oak Grove,
  MLSES = Martin Lake, CALAVERS = J K Spruce, TNP_ONE = Major Oak). Its own file, so the
  frozen ERCOT-71 non-CAMPD derive that reads every row of
  `ercot_noncampd_dam_crosswalk.csv` keeps its exact plant scope. Plant-grain coverage is
  complete: **10 crosswalked plants, 0 unmapped tranches.**
* `ScenarioConfig.ercot_thermal_dam_availability_coal` (requires `_hourly`), registered in
  the cache-key optional-field list. With the gate off the `COAL` class is dropped at the
  apply seam, so an armed-gas keeper is byte-identical to its pre-ERCOT-110 self even
  though the artifacts now carry coal — a re-derive cannot silently move a keeper.
* Verified: the 262 non-coal crosswalk rows, 3,198 non-coal class-day rows, 3,198
  non-coal class-hour rows and 7,504,090 non-coal site-hour rows are **byte-identical** to
  the previous artifacts. `tests/test_outages.py::test_coal_scope_gate` pins both sides of
  the gate. Zero test regressions against `origin/main`.
