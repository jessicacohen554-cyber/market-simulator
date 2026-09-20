# FINDING — SOCO-57 (2026-09-20): the model prices a 76 %-capacity-factor combined cycle on a heat rate eGRID measured in a 24 %-capacity-factor year

**Lane** SOCO-57 · **DATA PROFILE** soco · **Model** Opus 5 (rule 27 `[R-PUSH]` — scope writes
`src/market_sim/` and `scripts/`).
**Control of record** `2026-09-20-soco56-perunit-outage`
(`results/calibration/soco56_perunit_outage`), rule 29 `[R-SCREEN]` (b) **form 4**, no control solve.
**Arm** `measured_cc_heat_rates = True` — ONE new default-off `ScenarioConfig` field, one new derive,
one new per-ISO artifact.
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-57-2026-09-20.md`, pushed at
`7751541416ce0f5199ada9fcb508c6038de23ba1` **before any LP was solved**.

---

## 1. HEADLINE

**CC_REGULAR was the last thermal class in this footprint still priced off an unmeasured annual
average, and the defect that hid there is traced end-to-end to primary sources.**

### (1) THE HANDOFF'S SPREAD HYPOTHESIS IS REFUTED AS POSED — AND THE REAL OBJECT IS NARROWER

The handoff routed this lane at reading (1) with a specific test: *"If the model's spread is flatter
than the measured spread, that is a rule 14 `[R-ACCURATE]` data repair."* **It is not flatter.**

| | model | measured (16 applied plants) |
|---|---|---|
| CC heat-rate spread | **1.381** MMBtu/MWh | **1.403** MMBtu/MWh |
| capacity-weighted level | 7.217 | 7.040 |

Essentially identical. **The error is not in the spread; it is CONCENTRATED**, and where it sits is
the finding: the three plants the model prices too dear are, **in rank order, the three it most
under-dispatches**, and every other applied plant is inside ±0.24 MMBtu/MWh.

### (2) THE TRACED CASE, VERIFIED AGAINST eGRID AND EIA-860 THEMSELVES

> **Charles R Lowman (plant 56) is a combined cycle whose CT *and* steam generator both carry
> EIA-860 `Operating Year` 2023.** eGRID's 2023 vintage — the model's own heat-rate source — is
> therefore its **COMMISSIONING-year** average. eGRID's `PLHTRT` for it is **8104.7973 Btu/kWh =
> 8.1048 MMBtu/MWh**, which is byte-exact to the value the model carries, and its denominator
> `PLNGENAN` is **1,341,342 MWh on 639 MW = a capacity factor of 0.240** (EIA-923 confirms 2023 =
> 1.341 TWh). **The plant runs at CF 0.763 (2024) and 0.775 (2025), and its own meter reads 6.35 /
> 6.30 / 6.29 MMBtu/MWh net, stable to ±0.03.**
>
> **The model prices a machine that runs at 76 % on a heat rate measured in a year it ran at 24 % —
> 8.105 (42 % HHV, an F-class number) against a metered 6.30 (≈54 %, which is what a new H-class
> machine does). A $5.10/MWh error on a new machine.**

That is the `derive_campd_coal_heat_rates` docstring's stated defect — *"its LEVEL moves with the
plant's capacity factor in the vintage year: a low-CF vintage inflates the published rate, the model
then prices the plant out of merit, and its modelled CF falls further"* — in its sharpest possible
form, and this lane measured every term of it rather than asserting it.

### (3) THE ARM MOVES THE LANE'S OWN TARGET ROW THE WRONG WAY, AND THE PRECOMMIT SAID SO FIRST

2024 `CC_REGULAR` needs **−2.712 TWh**; a zero-LP greedy re-stack put the arm at **+0.356 TWh**, the
wrong way. `PRECOMMIT-soco-57` §4 states this in those words, and §5 P1 pre-registers the row still
failing both legs. The input is kept anyway, under rules 1 `[R-STRUCT]` and 14 `[R-ACCURATE]`.

---

## 2. THE MEASUREMENT (zero LP, on the control's own committed hourlies and the raw sources)

### 2.1 Model CC heat rate vs CAMPD-metered steady state (2024, net basis, pf = 0.975)

| plant | name | cap MW | model | measured | Δ MMBtu/MWh | Δ $/MWh | boundary | 2024 ratio | util_of_avail |
|---|---|---|---|---|---|---|---|---|---|
| **56** | **Charles R Lowman** | 639.0 | **8.105** | **6.303** | **+1.801** | **+5.10** | 1.116 ok | **0.602** | 0.620 |
| **3** | **Barry** | 1821.2 | **7.821** | **7.051** | **+0.770** | **+2.18** | 1.076 ok | **0.729** | 0.719 |
| **6073** | **Daniel** | 1132.4 | **7.553** | **6.852** | **+0.701** | **+1.98** | 1.060 ok | **0.843** | 0.873 |
| 55406 | Bobby C. Smith Jr. | 524.6 | 7.580 | 7.340 | +0.240 | +0.68 | 1.027 ok | 1.058 | 0.938 |
| 55411 | Hillabee | 752.7 | 7.345 | 7.174 | +0.170 | +0.48 | 1.039 ok | 1.063 | 0.992 |
| 55382 | Thomas A. Smith | 1192.0 | 7.279 | 7.178 | +0.101 | +0.28 | 1.037 ok | 1.031 | 1.000 |
| 55440 | Central Alabama | 917.0 | 7.452 | 7.390 | +0.062 | +0.18 | 1.033 ok | **1.455** | 0.968 |
| 7897 | E B Harris | 1304.0 | 6.941 | 6.977 | −0.036 | −0.10 | 1.023 ok | **1.404** | 1.000 |
| 7710 | H. Allen Franklin | 1901.8 | 6.878 | 6.914 | −0.036 | −0.10 | 1.026 ok | 1.126 | 1.000 |
| 55965 | Wansley CC | 1184.8 | 6.934 | 6.974 | −0.040 | −0.11 | 1.023 ok | 1.090 | 1.000 |
| 57037 | David M Ratcliffe | 840.0 | 7.374 | 7.417 | −0.043 | −0.12 | 1.024 ok | **1.431** | 0.982 |
| 7917 | Chattahoochee | 466.0 | 6.874 | 6.927 | −0.053 | −0.15 | 1.017 ok | 0.977 | 1.000 |
| 710 | Jack McDonough | 2471.0 | 6.724 | 6.799 | −0.075 | −0.21 | 1.014 ok | 0.966 | 1.000 |
| 56150 | McIntosh CC | 1315.6 | 7.077 | 7.171 | −0.094 | −0.27 | 1.014 ok | 1.116 | 1.000 |
| **55271** | **Tenaska Lindsay Hill** | 848.0 | 7.304 | 7.411 | −0.107 | −0.30 | 1.032 ok | **2.506** | 0.999 |
| 55241 | Hog Bayou | 230.0 | 7.555 | 7.697 | −0.143 | −0.40 | 1.017 ok | 0.949 | 0.945 |
| *533* | *McWilliams* | *650.0* | *8.041* | *10.776* | — | — | **0.719** | *1.070* | 0.790 |
| *7946* | *Wansley U9* | *462.8* | *7.175* | *10.938* | — | — | **0.675** | *1.016* | 1.000 |

**Applied: 16 of 18 plants, 17,540.1 of 18,652.9 MW = 94.0 %**, over 1,164,652 steady hours; the
least-supported applied plant still carries 17,151 (the screen's minimum is 200).

### 2.2 The model's heat-rate source, confirmed against eGRID itself

`PLHTRT` in `data/raw/fleet-egrid/egrid2023_…PLNT23.parquet`, Btu/kWh:

| plant | eGRID `PLHTRT` | model carries | source the model actually uses |
|---|---|---|---|
| 56 Lowman | **8104.797** | **8.1048** | eGRID PLANT average (single live family) |
| 7897 E B Harris | **6940.956** | **6.9410** | eGRID PLANT average |
| 55271 Tenaska Lindsay Hill | **7303.812** | **7.3038** | eGRID PLANT average |
| 3 Barry | 8994.965 | 7.8209 | eGRID CC **FAMILY** rate (`egrid_family_heat_rates`) |
| 6073 Daniel | 8399.472 | 7.5531 | eGRID CC **FAMILY** rate |

Every model value is accounted for by a named eGRID construction. Nothing is unexplained.

### 2.3 THE BOUNDARY GUARD — this deriver's own addition, and why the measurement is trustworthy

`heatInput / grossLoad` is a plant's **combined-cycle** heat rate only if CAMPD's gross load includes
the steam turbine. At some sites it does not: the combustion turbines report and the unfired steam
generator does not, so the ratio is the **CT** rate — about 1.5× the true CC rate, because the steam
tail is roughly a third of a CC's output for none of its fuel. Applying that would price a healthy
plant out of merit on a metering artifact.

The guard is an **identity test against an independent source**: pooled CAMPD CC gross over the same
year's EIA-923 CC net, read through the benchmark's own `_eia923_frame`, so the comparator is exactly
the series the run is scored on.

| cluster | plants | ratio |
|---|---|---|
| steam **metered** | 16 | **1.014 … 1.116** (median **1.0263**) |
| steam **NOT metered** | 533 McWilliams, 7946 Wansley U9 | **0.719 / 0.675** |

Separated by a factor of 1.4 with **nothing between 0.72 and 1.01**, so the band `[0.90, 1.25]` sits
inside an empty gap and **no value in [0.75, 1.00] would change the partition** — fixed on physics ex
ante, never swept (rules 1 / 23 `[R-FROZEN-DERIVE]`).

**A SECONDARY RESULT WORTH RECORDING.** For a plant whose steam IS metered, the boundary ratio and
the class parasitic factor are two independent estimates of one quantity. Their **median is 1.0263
against the class default's implied 1/0.975 = 1.0256 — agreement to 0.06 %**. That corroborates
SOCO's CC parasitic factor from a source that has nothing to do with it, and partially answers the
standing routed item that `derive_parasitic_load.py` has never been run for SOCO — *for the CC class
only*, and it is reported, not claimed as a closure.

### 2.4 Why this is a mechanism and not a fit

The correction is largest at the three plants the model most under-dispatches, **in rank order**;
~zero at the plants it already dispatches correctly (McDonough 0.966×, Chattahoochee 0.977×, Hog
Bayou 0.949×); **and ~zero at the plants it OVER-dispatches** — Tenaska Lindsay Hill, at 2.506× the
class's single largest outlier, measures **−0.107 MMBtu/MWh**, i.e. the model is $0.30/MWh *cheap*
there. `corr(Δ heat rate, dispatch ratio) = −0.505` over the 16 applied plants. **A lever that
repaired both tails would be a curve fit. This one repairs one and is provably silent on the other.**

### 2.5 The handoff's Lowman-vs-Tenaska question, answered before the solve

- **Lowman — ECONOMIC, and now NAMED.** `util_of_avail` 0.620: nothing physical stops it. It does not
  run because the model charges it **$5.10/MWh too much**. Readings (1) and (2) are one defect here.
- **Tenaska Lindsay Hill — NOT a heat-rate defect.** Model rate $0.30/MWh *cheap* against its own
  meter, at `util_of_avail` 0.999. Its 2.506× over-run needs a different mechanism and this lane does
  not have the input to name it. **ROUTED, §9.**

---

## 3. RULE 19 `[R-ONE-MECH]`, MACHINE-VERIFIED AT FOUR GRAINS BEFORE THE SOLVE

`fleet_only` rebuild off the keeper's own `meta.json`, arm vs control, **keys moved** reported and not
only max|Δ| (the SOCO-56 lesson):

| year | `fuel_prices` | `pmax` | `availability` | `mc_base` | `heat_rate` |
|---|---|---|---|---|---|
| 2023 | **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | 6.441073532230 · **59/327** | 1.801497324000 · **59/327** |
| 2024 | **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | 6.015920163766 · **59/327** | 1.801497324000 · **59/327** |
| 2025 | **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | 8.864447732474 · **59/290** | 1.801497324000 · **59/290** |

**Every moved row is `CC_REGULAR`**, at exactly the 16 applied plants. McWilliams and Wansley U9 are
**absent on every grain** — the boundary guard holds through to the LP. The `heat_rate` delta is
year-invariant (the artifact is pooled, by construction); `mc_base` scales with each year's gas level.

---

## 4. A WIRING DEFECT FOUND IN LANE — AND A SUCCESSOR MUST KNOW IT

This lane's **first** rule-19 run read all four grains at **exactly zero**. That is not an inert
mechanism; it is an arm that never armed. `scripts/run_calibration.py`'s `fleet_to_bins` call site
passes the other three measured-heat-rate flags and was missing the fourth, so `config.
measured_cc_heat_rates` never reached the fleet the LP prices.

**The diagnosis was a control toggle of a KNOWN-armed flag through the same channel** —
`measured_coal_heat_rates=false`, which moved 24 `mc_base` rows across 6 COAL plants and proved the
channel sound, isolating the fault to the new field.

> **A FIFTH SIBLING MUST PATCH FOUR CALL SITES, NOT THREE.**

The lasting guard is `soco57_compose_span.assert_delta`, which reads the **resolved**
`scenario_config` rather than the `prb_overrides` bag the CLI routed the flag through — verified in
both directions (it refuses a control offered as the arm, and accepts it offered as a control).
"max|Δ| == 0" is indistinguishable from "inert" unless something asserts the resolved value.

---

## 5. WHAT THE RUN DELIVERED

**Run `2026-09-20-soco57-measured-cc-heat`, bundle `results/calibration/soco57_measured_cc_hr`,
composed at zero LP from three per-year shards.** Solve cost ~94 s / 2.65 GiB per year; the 2025 leg
re-ran itself and reported all 14 artifacts byte-identical, i.e. deterministic.

### 5.1 THE HEADLINE: the class total gets WORSE while the per-plant allocation gets MUCH better

**Aggregate per-plant CC misallocation, Σ|model − actual| over CC plants:**

| year | keeper | **ARM** | |
|---|---|---|---|
| 2023 | 13.796 TWh | **11.316** | **−18.0 %** |
| 2024 | 19.331 TWh | **11.081** | **−42.7 %** |

**The 2024 per-plant misallocation falls by 42.7 % while the class TOTAL gets 0.876 TWh worse.** That
is the signature of an allocation repair whose compensating errors have been removed: the model was
getting the class total *less wrong* by being wrong at the plants in opposite directions, and pricing
the plants correctly exposes the class-level error at full size.

| plant | keeper | **ARM** | actual | ratio before | **ratio after** |
|---|---|---|---|---|---|
| **56 Lowman** | 2.568 | **4.140** | 4.269 | 0.602 | **0.970** |
| **3 Barry** | 9.597 | **13.348** | 13.173 | 0.729 | **1.013** |
| **6073 Daniel** | 6.766 | **7.752** | 8.029 | 0.843 | **0.965** |
| 55271 Tenaska Lindsay Hill | 4.391 | 3.610 | 1.752 | 2.506 | **2.060** |
| *533 McWilliams (refused)* | 3.100 | 2.497 | 2.898 | 1.070 | *0.861* |
| *7946 Wansley U9 (refused)* | 3.508 | 3.308 | 3.454 | 1.016 | *0.958* |

Barry lands at **1.013** of its own measured output and Lowman at **0.970** — from 0.729 and 0.602.
Tenaska Lindsay Hill improves 2.506 → 2.060 **without its heat rate changing at all**, purely because
the correctly-priced plants now out-compete it: the over-tail partially self-corrects. **The two
boundary-refused plants move AWAY** (1.070 → 0.861, 1.016 → 0.958) because everything around them got
cheaper and they did not — the declared cost of refusing an untrustworthy meter.

### 5.2 The scored C1 rows (bands 7.180 / 7.466 / 7.545 TWh; share cap ±3.00 pp)

| year | class | keeper Δ | **arm Δ** | keeper share | **arm share** | status |
|---|---|---|---|---|---|---|
| 2023 | `CC_REGULAR` | +5.75 | **+6.28** | +2.3 | **+2.5** | PASS |
| 2023 | `CT_PEAKER` | +6.06 | **+5.97** | +2.5 | +2.5 | PASS |
| 2023 | `ST_GAS` | −6.46 | **−6.47** | −2.7 | −2.7 | PASS |
| 2023 | `COAL_PRB` | −1.93 | **−2.33** | −0.8 | −1.0 | PASS |
| 2023 | `COAL_BIT` | −1.24 | −1.24 | −0.5 | −0.5 | PASS |
| **2024** | **`CC_REGULAR`** | **+10.18** | **+11.05** | **+3.9** | **+4.2** | **FAIL — both legs, worse on both** |
| 2024 | `CT_PEAKER` | +3.15 | **+2.97** | +1.3 | +1.2 | PASS |
| 2024 | `ST_GAS` | −5.75 | −5.75 | −2.3 | −2.3 | PASS |
| 2024 | `COAL_PRB` | −5.14 | **−5.78** | −2.1 | **−2.4** | PASS |
| 2024 | `COAL_BIT` | −0.69 | −0.71 | −0.3 | −0.3 | PASS |
| *2025 (SKIPPED)* | `CC_REGULAR` | *+0.39* | *+1.00* | | | *ungated* |

### 5.3 Class volumes, arm − keeper (TWh, P1)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CC_REGULAR` | **+0.5310** | **+0.8763** | **+0.6126** |
| `COAL_PRB` | −0.4059 | **−0.6383** | −0.3741 |
| `CT_PEAKER` | −0.0845 | −0.1786 | −0.1047 |
| `COAL_BIT` | 0.0000 | −0.0219 | −0.0958 |
| `ST_GAS` | −0.0095 | +0.0032 | −0.0079 |
| **nuclear, hydro, wind, solar, biomass, `CC_CHP`, oil** | **0.0000** | **0.0000** | **0.0000** |

---

## 6. THIS LANE'S OWN PREDICTIONS — **13 CONFIRMED, 1 PARTIAL, 2 FALSIFIED**

| # | prediction | outcome |
|---|---|---|
| **P1** | 2024 `CC_REGULAR` worse, still fails BOTH legs; band +9.9…+11.6 TWh, +3.8…+4.4 pp | **CONFIRMED** — **+11.05 TWh, +4.2 pp** (above the +10.53 point estimate, inside the band) |
| **P2** | `NOT-YET`; C1 stays 13/14 all · 9/10 free; no C1 row changes status | **CONFIRMED** |
| **P3** | 2024 `CT_PEAKER` improves −0.05…−0.45 TWh → +2.70…+3.10 | **CONFIRMED** — −0.179 → **+2.97** |
| **P4** | 2024 `COAL_PRB` worsens by **< 0.45 TWh**, stays PASS | **FALSIFIED on magnitude** — moved **−0.638**. The PASS clause holds (−5.78 of ±7.47) |
| **P5** | 2023 `ST_GAS` (thinnest C1 row) moves < 0.15 TWh, stays PASS | **CONFIRMED** — −0.0095 |
| **P6** | 2023 `CT_PEAKER` (thinnest on share) moves < 0.15 TWh, flat-or-safer | **CONFIRMED** — −0.085, safer |
| **P7** | 2023 `CC_REGULAR` +5.80…+6.60 TWh | **CONFIRMED** — **+6.28** |
| **P8** | per-plant allocation improves at all three repriced plants (Lowman 0.70–0.95, Barry 0.74–0.88, Daniel 0.85–0.98) | **PARTIAL** — direction right at all three, but Lowman **0.970** and Barry **1.013** land ABOVE their bands. The greedy re-stack understated the move because it could not model re-commitment |
| **P9** | the two boundary-refused plants are not repriced | **CONFIRMED** — absent on every rule-19 grain |
| **P10** | 2025 (ungated) `CC_REGULAR` +0.6…+1.3 TWh | **CONFIRMED** — **+1.00** |
| **P11** | rule 17 `[R-FLOOR-WINDOW]` holds in every plant-year; direction unpredicted | **CONFIRMED** — all 15 plant-years, positive margin everywhere; plant 3 at 0.000 share, 0.0632 margin |
| **P12** | C8 under the 0.30 cap; direction unpredicted | **CONFIRMED** — `ST_GAS` 0.1290/0.1307/0.1468 → **0.1296/0.1304/0.1473** |
| **P13** | **C2 / C4 / C6 PASS** | **FALSIFIED — C4 FAILS.** See §7 |
| **P14** | zero free parameters; DOF 6 entries / 1 residual | **CONFIRMED** — identical to the keeper |
| **P15** | no peer ISO moves; `moved_rows("SOCO") == {}` | **CONFIRMED** |
| **P16** | exactly 2 boundary refusals; 94.0 % applied coverage | **CONFIRMED** |

**Two falsifications and one partial are reported as misses, not re-read as successes.** All three
share one root cause: **the zero-LP greedy re-stack systematically understated the movement**, because
it could only displace above-floor MW hour-by-hour and could not model the LP re-committing units. A
successor using that bound should widen its bands by roughly 2× in the direction of the correction.

---

## 7. THE NEW FAILING CRITERION, AND THE THINNEST-ROW MISS BEHIND IT

**C4 fleet hourly dispatch correlation goes PASS → FAIL on ONE row.**

| year | fuel | keeper | **arm** | tol |
|---|---|---|---|---|
| 2023 | gas | r=0.950, NRMSE=0.100 | r=0.951, NRMSE=0.102 | PASS |
| 2023 | coal | r=0.867, NRMSE=0.259 | **r=0.882**, NRMSE=0.258 | PASS — *r improves* |
| 2024 | gas | r=0.953, NRMSE=0.126 | r=0.950, NRMSE=0.132 | PASS |
| **2024** | **coal** | r=0.832, **NRMSE=0.296** | r=0.829, **NRMSE=0.309** | **FAIL** (≤ 0.30) |
| 2025 | gas | r=0.956, NRMSE=0.086 | r=0.955, NRMSE=0.088 | PASS |
| 2025 | coal | r=0.882, NRMSE=0.170 | r=0.882, **NRMSE=0.167** | PASS — *improves* |

`grade_summary` `target_grade` drops **4 → 3** and `fails` **1 → 2**.

**THE MISS IS THIS LANE'S AND IS NAMED.** The handoff's check D required naming the thinnest passing
row ex ante. §5 of the PRECOMMIT named 2024 `COAL_PRB` and 2023 `ST_GAS` — **both C1 rows**, because
the analysis enumerated C1 only. **The actual thinnest row on the whole run was C4 2024 coal, passing
by 0.004 of NRMSE**, and this lane never looked at it. *A successor's check D must enumerate every
scored criterion's margin, not C1's.*

**What the number is, and is not.** Two of three coal years IMPROVE (2023 r 0.867 → 0.882; 2025 NRMSE
0.170 → 0.167) and one crosses a gate the control held by 0.004, with `r` essentially unchanged
(0.832 → 0.829). It is **not** dismissed on that basis: C4 fails, it is supporting-tier with no
standing-rule relief (rule 22 `[R-C3C]` covers C3c only), and it costs a grade point.

**Its mechanism is understood and it is a real cost.** Repricing three CC plants cheaper displaces
coal — 2024 `COAL_PRB` −0.638 TWh — **from a class already 5.143 TWh SHORT of its actual**. The arm
takes energy from a short class and gives it to a long one, and perturbs coal's hourly shape doing it.
Under rule 14 `[R-ACCURATE]` that is the **discovered-bug signal**, not a reason to revert: SOCO's
coal is under-dispatched for a reason this lane has not found, and the CC heat-rate error was
partially masking it. **THE NAMED SUCCESSOR IS SOCO'S COAL UNDER-DISPATCH, not this input.**

**Elsewhere legitimacy IMPROVES.** D-1 failing rows fall **3 → 2** (2025 `COAL_BIT` repaired; 2023
`COAL_BIT` and 2024 `COAL_PRB` inherited). D-2 / D-4 / D-5 / D-9 / D-10 **PASS both sides**. Rule 17
holds in all fifteen plant-years. C8 `ST_GAS` forced share 0.1296 / 0.1304 / 0.1473 against the 0.30
merchant cap.

---

## 8. GATES

| gate | keeper | **arm** |
|---|---|---|
| **determination** | `NOT-YET` (rubric v3.8, PRICE UNSCORED) | **`NOT-YET`** |
| **C1 fuel-mix** | FAIL · 13/14 all · 9/10 free | **FAIL · 13/14 all · 9/10 free** |
| **C2 system volume** | PASS | **PASS** |
| **C3a / C3b / C3c** | SKIPPED — UNSCORABLE | **SKIPPED — UNSCORABLE** |
| **C4 dispatch correlation** | **PASS** | **FAIL** (2024 coal) |
| **C6 governance** | PASS | **PASS** |
| **C8 forced share** | PASS | **PASS** |
| caveats | 0 ledgered · 0 protective | **0 ledgered · 0 protective** |
| `grade_summary` | scored 5 · target **4** · fails **1** | scored 5 · target **3** · fails **2** |
| DOF | 6 entries / 1 residual | **6 entries / 1 residual** |
| `solve_surface` | — | `moved_rows("SOCO") == {}` |

**C5a CO2 (REPORTED-ONLY, contributes no status)**: −7.5 / −11.8 / +2.7 % → **−7.7 / −12.3 / +2.3 %**.

### 8.1 An independent corroboration of the boundary guard, found at registration

`dashboard_add_run` prints the benchmark's own **CT-only CEMS flag** (`923 net > 1.1× CAMPD gross`)
and it names **7946 Wansley Unit 9 (1.44×) and 533 McWilliams (1.39×)** — *exactly the two plants the
boundary guard refuses*, at exactly the reciprocals of their measured ratios (1/0.675 = 1.481,
1/0.719 = 1.391). **The repo's own benchmark machinery independently identifies the same two
unmetered-steam plants**, by a different route, and had been flagging them all along.

---

## 9. ROUTED

1. **THE OVER-DISPATCHED CC TAIL IS UNEXPLAINED AND THIS LANE DOES NOT EXPLAIN IT.** Tenaska Lindsay
   Hill (2.506×), Central Alabama (1.455×), Ratcliffe (1.431×) and E B Harris (1.404×) all run at
   0.97–1.00 of model availability on heat rates that are **correct to within ±$0.30/MWh of their own
   meters**. Heat rate is now *excluded* as their cause — which is this lane's contribution to the
   question, not its answer. The remaining candidates are availability, a tolling/contractual
   dispatch the model does not represent, and gas deliverability; none has an admissible input in
   this repo today.
2. **THE TWO BOUNDARY-REFUSED PLANTS.** McWilliams (533) and Wansley U9 (7946) have no trustworthy
   measured CC rate, because CAMPD does not meter their steam turbines. They keep their eGRID rates.
   A successor wanting them needs either a CAMPD re-publication or a different measurement route.
3. **THE ST_GAS DENOMINATOR** — SOCO-56 §9 item 3, untouched here. `unit_outage_extract_basis_share`
   (nyiso-196) or `unit_outage_st_capacity_basis`, behind its own A/B. Bounded at ≤ 0.0071 TWh.
4. **THE TRANCHE HALF OF `campd_per_unit_attribution`** — SOCO-56 §4.2, untouched here and still a
   live landmine: the flag is ON for SOCO and deriving `thermal_tranches-perunit-SOCO.csv` would arm
   a second mechanism silently.
5. **BARRY UNIT 4'S FLEET ROW** — EIA-860 files it Conventional Steam Coal (`BIT`); CAMPD measures it
   burning Pipeline Natural Gas. SOCO-56 fixed the outage routing; the fleet row still follows the
   stale 860. Untouched here.
6. **`derive_parasitic_load.py` has never been run for SOCO.** §2.3 corroborates the CC class default
   to 0.06 % from an independent source, which narrows this item but does not close it — coal and
   gas-steam are untouched, and the coal sign is still wrong for a `COAL_PRB` that is short.
7. **SOCO-53b, the 2025 hydro hole** — 0.327 TWh modelled against 6.012 measured. Untouched.
8. **The within-footprint gas dispersion** (SOCO-12 §4). Inherited, unmodelled, no free public index.

---

## 10. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** Phase 0, the `fleet_only` rebuilds, the artifact derivation, the greedy
  re-stack, the composition, `--rebuild-benchmark` and all scoring are zero-LP (rule 32 `[R-SHARD]` (a)).
- **Three shards, ONE YEAR EACH** (rule 36 `[R-YEAR-ISOLATION]` (a)), all pinned to
  `7751541416ce0f5199ada9fcb508c6038de23ba1`, each pushing a **full 16-file bundle** including
  `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet` (rule 34 `[R-SHARD-PROMOTABLE]` (a)).
- **THE CONTROL'S PER-PLANT LAYER WAS RECOVERED AT ZERO LP FOR THE THIRD CONSECUTIVE LANE.**
  `git fetch origin <40-char-sha>` on the SOCO-56 leg SHAs returned 16 files each, and **all twelve
  committed hourly sidecars verified byte-identical** to the registered keeper. *The retention window
  is still undocumented, so this is not a durability claim (rule 33(d)).*
