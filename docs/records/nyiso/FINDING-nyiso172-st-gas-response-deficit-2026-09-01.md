# FINDING — nyiso-172: the ST_GAS deficit is NOT a price-conditional dropout — its SIGN FLIPS across the training window, it is a year-over-year RESPONSE deficit whose growth is 99 % downstate, and its counterpart is a one-sided-provable CC availability over-statement that reaches 13.8 % of 2025's hours

**Session:** nyiso-172 · **Date:** 2026-09-01 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Solves run: ZERO.**
**No parameter was touched, no band was swept, no run was registered.**

---

## 0. The result in one paragraph

The brief opened the ST_GAS level deficit — **9.7866 vs 13.7121 TWh in 2025,
−28.63 %**, the largest absolute class error in the failing year — as nyiso-170
§4's "third thing": a composition error that is not an hour-local swap. Its
premise was that the class "exits too readily as fuel rises", and the
pre-registered stop condition (S2) tested exactly that. **S2 fails, and it fails
by sign reversal rather than by weakness.** In 2023 the model **OVER**-runs
ST_GAS by **+40.9 %**, with a positive deficit in **all ten** implied-marginal-
heat-rate deciles and its dispatch threshold **left** of the market's; in 2025 it
under-runs by −28.6 %, negative in all ten, threshold right. A dropout story
cannot hold both. What the measurement finds instead is a **between-year
response deficit**: the same fleet ran **9.75 → 11.67 → 15.14 TWh
(+55.3 %)** on their own meters while the model ran them **11.47 → 9.32 → 9.79
TWh (−14.7 %)**, taking gas steam from 16.9 % → 22.5 % of measured gas burn while
the model took it from 18.3 % → 14.1 %. **The market leaned progressively onto
its gas-steam fleet; the model leaned progressively off it** — and the model's
behaviour is *correct isolated physics*, because at heat rates of ~10.9 (steam)
against ~7 (CC) the cost gap widens from ~$7.6 to ~$18.2/MWh as Transco Z6 goes
$1.95 → $4.66, so a pure-economic stack must push steam back. The missing driver
is therefore **not in the cost stack at all**. Four things locate it: the ST_GAS
population is clean (off-model volume < 0.7 %), capacity is ample (required CF
0.176 against 1,575 MW of headroom at the model's own 2025 peak), **99.2 % of the
measured growth is downstate** (NYC +2.354, Capital_Hudson +1.609, Long_Island
+1.382, Upstate_West **+0.004** TWh), and the counterpart class carries a
**one-sided-provable** defect: the model's CC output exceeds the measured CC
fleet's own **within-month maximum** — a strict lower bound on that fleet's
availability — in **1.06 / 8.82 / 13.82 %** of hours, growing monotonically with
the ST_GAS deficit and concentrated in winter (Jan 432 h, Feb 343 h, Dec 161 h of
2025). The brief's named trap is refused **twice over**: `gas_st_startup_cost`
cannot be grounded (its model-side instrument is degenerate) and, decisively,
**cannot help in principle** — the markup is non-negative and P1-only, so it
weakly *lowers* ST_GAS output and cannot address an under-run. **No lever, no
solve; one measured object handed forward with a proof attached.**

## 1. What was measured, and off what

Zero solve throughout. Every series is a committed artifact or a raw measured
record.

| instrument | source |
|---|---|
| model hourly MW by class | keeper `hourly/class_hourly_<year>.parquet`, pass **P1** |
| model hourly zonal price + demand | keeper `hourly/system_<year>.parquet`, pass **P1** |
| what already forces ST_GAS | keeper `legitimacy_diagnostics.json`, D-2 rows |
| measured hourly MW per unit | `data/raw/campd-unit-level/NY_<year>.parquet` |
| class construction | CAMPD `unitType` × EIA-860 CHP flag — the nyiso-169b/170/171 construction, unchanged |
| class volume reference | `frontend/data/backcast/bench/NYISO/<year>.json.gz` `classFull` |
| actual price | `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` |
| gas price | `data/raw/gas-prices/transco_z6_ny_daily.csv` (Transco Z6 NY) |
| model ST_GAS capacity + zone | `thermal_tranches_NYISO.csv` × `data.zone_assignment.assign_zone` |

**Anchoring.** The nyiso-170 construction — one scalar
`anchor = benchmark_TWh / CAMPD_TWh` per class-year (**0.835 / 0.850 / 0.906**
for ST_GAS). It preserves the annual level error exactly and therefore compares
**shape only**.

**Rule 13 `[R-MEASURED]` compliance.** CAMPD enters only as *conduct
identification*. Nothing is pinned to observed generation, and no statistic is
tuned to any residual.

**Rule 22 `[R-HOLDOUT]`.** Every year read is 2023, 2024 or 2025. NYISO's
`complete` marker was declared 2026-07-31 and **withdrawn 2026-08-30**
(`calibration-complete.json` `withdrawn.NYISO`; nothing was ever spent), and
NYISO has never appeared in `final`. Nothing out-of-training was read, solved,
scored or registered, and **no marker was requested**.

**Reproduction of the seven inherited probes.** All seven were re-run before
anything was measured, and all seven reproduce: nyiso-167 gain **0.703**, offset
**$11.03**, R² **0.910**; nyiso-168 deficit **−$6.59 = −$2.32 gradient + −$4.27
level**; nyiso-168 reserve ceiling **10.01×** thermal-only; nyiso-169b
`PEAK-BAND PROPOSAL SUPPORTED: False` with ST_GAS **−28.6 %** / all-months-
negative **True**; nyiso-170 `proceed_to_phase_2: false` with G3 alone true;
nyiso-171 coverage **0.253 / 0.502 / 0.313** and over-run **51.1 / 69.3 / 80.4 %**.
All three documented traps were hit and handled as prescribed: **(a)** the
reserve-slack JSON reproduced to float noise only (nine lines, e.g.
`30447.499999999996` → `30447.5`) and the churn was **reverted, not committed**;
**(b)** the container had **0 DA months** against 21 RT, so the congestion probe
would have degraded silently — repaired with
`fetch_nyiso_zonal_lmp.py --start 202301 --end 202512 --kind both` (36 DA months
staged) then `regenerate_clean.py nyiso-interface-flows`, after which DA coverage
reads **8760 h/year** (not the degraded 1,464) and the probe reproduces at
**≥99.2 %** of congestion forming off-limit — at least as strong as the recorded
≥98.3 %; **(c)** `STD_TZ = "Etc/GMT+5"` throughout.

## 2. The pre-registered gates and their outcomes

Registered in `results/calibration/PREREG-nyiso172-st-gas-level-deficit.md` and
committed **with the probe, before either was run** (`8c3e9b6c`).

| gate | PASS condition | outcome |
|---|---|---|
| **S1** | rule 19 attribution complete and unambiguous | **complete** — two mechanisms, §2.1 |
| **S2** | model T50 > measured T50 in all 3 years **and** spread ≥ 0.20× mean abs | **FAIL** — sign reversal, §2.2 |
| **S3** | model ST_GAS can reach the benchmark volume | **CONDUCT** (not an input defect), §2.3 |
| **S4** | measured start conduct supports arming | **NOT GROUNDED** — instrument degenerate, §2.4 |
| **S5** | `gas_st_startup_cost` can raise ST_GAS | **DIRECTION REFUSES**, §2.5 |
| **S6** | monthly deficit tracks gas price, same sign all years | **NOT SUPPORTED**, §2.6 |

### 2.1 S1 — what already forces ST_GAS (rule 19 `[R-ONE-MECH]`)

Exactly two mechanisms, from the committed D-2 rows:

| year | `reliability_floor` | `nyiso_gas_commitment_bridge` | total |
|---|---|---|---|
| 2023 | 2.2864 TWh (16.70 %) | 0.1124 TWh (0.82 %) | **17.52 %** |
| 2024 | 2.6110 TWh (22.67 %) | 0.1682 TWh (1.46 %) | **24.13 %** |
| 2025 | 2.2821 TWh (18.43 %) | 0.1495 TWh (1.21 %) | **19.64 %** |

**A recorded basis caveat.** D-2's `class_total_twh` (13.6894 / 11.5181 /
12.3843) is the LP dispatch frame summed over rows labelled ST_GAS; the P1
`class_hourly` sidecar reads 11.4707 / 9.3209 / 9.7866 for the same class-years.
The two are different bases and the ratio is not constant (1.19 / 1.24 / 1.27),
so the committed shares above are quoted on D-2's own denominator and **no
cross-basis share is computed here**. Either way the conclusion is unchanged and
is the same one nyiso-171 reached for CC_CHP: **this class is already among the
most heavily forced in NYISO, so the answer is not another floor.**

Also recorded, because it bears directly on §2.7: the keeper explicitly
**disables** five downstate reliability-floor limbs —
`NYC:ST_GAS`, `NYC:CT_PEAKER`, `Long_Island:ST_GAS`, `Long_Island:CT_PEAKER`,
`Capital_Hudson:ST_GAS`, all on the `tmax` driver — under
`reliability_floor_overrides`. These are the h14-21 peak-window limbs the owner
directed be **replaced** by `nyiso_gas_commitment_bridge` (2026-07-27), and
re-arming them alongside the bridge would violate rule 19 by construction. They
are `tmax`-windowed, so they could not carry an all-twelve-months deficit in any
case.

### 2.2 S2 — THE STOP CONDITION: the sign flips, so no dropout story holds

Binned by the market's own implied marginal heat rate
`IMH = actual DA price ÷ Transco Z6` — exogenous to the model, which is what
makes it admissible for binning both series at once. Deficit = model − anchored
measured, MW:

| decile | IMH 2023 | deficit 2023 | IMH 2025 | deficit 2025 |
|---|---|---|---|---|
| d0 | 8.87 | **+167.7** | 8.10 | **−685.7** |
| d2 | 12.31 | +318.6 | 12.85 | −340.9 |
| d4 | 14.96 | +375.6 | 15.52 | −413.6 |
| d6 | 18.10 | +452.2 | 18.82 | −483.3 |
| d8 | 23.64 | +567.2 | 24.82 | −516.8 |
| d9 | 34.93 | +415.3 | 36.59 | −401.2 |

| year | T50 model | T50 measured | model right of measured? | Spearman |
|---|---|---|---|---|
| 2023 | 16.20 | 17.67 | **False** | +0.927 |
| 2024 | 21.21 | 20.47 | True | +0.455 |
| 2025 | 18.66 | 17.03 | True | −0.248 |

The gate required "model turn-on threshold right of the market's in **all
three** years". It is **left** in 2023, and the deficit is **positive in every
single decile** that year. This is not a marginal miss: the object's sign is
opposite in the first training year. **The brief's premise — that the model's
steamers exit too readily as fuel rises — is not supported as a within-year
price-conditional dropout, and the spread leg passing (1.05 / 3.21 / 0.80×) does
not rescue it**, because a conjunction gate fails on either leg.

### 2.3 S3 — capacity is ample; this is conduct

| year | nameplate | required CF | model CF | model peak | peak/nameplate | headroom at peak |
|---|---|---|---|---|---|---|
| 2023 | 8,902 MW | 0.1044 | 0.1471 | 6,255 MW | 70.3 % | 2,647 MW |
| 2024 | 8,902 MW | 0.1271 | 0.1195 | 6,776 MW | 76.1 % | 2,126 MW |
| 2025 | 8,902 MW | **0.1758** | 0.1255 | 7,327 MW | 82.3 % | **1,575 MW** |

A 17.6 % annual capacity factor is not a capacity constraint, and the model never
approaches its own ST_GAS ceiling. **Not an input defect on the ST_GAS side.**
(The measured fleet's gross peak — 7,240 / 7,770 / **9,242** MW — exceeds the
model's *nameplate* in 2025, but that is the gross-vs-delivered basis difference
plus unit-level coincidence, not a missing plant: see §2.7.)

### 2.4 S4 — the `gas_st_startup_cost` grounding cannot be made: the instrument is degenerate

The measured side is well behaved. Across 29 CEMS units:

| year | median-of-median run | median starts/unit | total starts | units with median run ≥ 24 h |
|---|---|---|---|---|
| 2023 | 42 h | 12 | 376 | 17 / 29 |
| 2024 | 61 h | 13 | 352 | 21 / 29 |
| 2025 | 63 h | 12 | 393 | 23 / 29 |

So NYISO's steamers genuinely do hold long runs, and the
`ST_GAS_COMMITMENT_PARAMS` min-run constants (**24 / 48 h**) are **not absurd**
for this fleet — 23 of 29 units clear the 24 h leg in 2025.

**But the comparison that would justify arming cannot be made.** The only
direction-safe model/measured comparison available from committed artifacts is
the **class aggregate** (a class-aggregate start requires ≥ 1 unit start; a
class-aggregate zero implies every unit is off — the two inferences nyiso-171's
portfolio-artifact caveat leaves intact). That instrument is **degenerate**: in
every year **both** the model's and the measured ST_GAS class aggregate are on
in **all 8,760 hours**, one run each, `model_starts = measured_starts = 1`. It
cannot discriminate at all. Per-unit model dispatch is not in the sidecar, so
**"does the model cycle its steamers more than NYISO does" is unanswerable
without a re-solve.** Verdict: **NOT GROUNDED** — and per the brief, arming it
because ST_GAS under-runs would be exactly the residual-driven choice rule 1
`[R-STRUCT]` forbids.

### 2.5 S5 — and it could not help anyway: the direction refuses it, on the code

This is the decisive half, and it needs no measurement at all:

* `model/commitment.py::_amortized` returns `startup / max(avg_run, 1.0)` —
  **non-negative by construction** (`commitment.py:280`).
* `pipeline/solve.py::run_energy_solve` forms **`mc_bid = mc_base + markup`**
  (`solve.py:308`), and the markup is **P1-only** — P0 run lengths, and therefore
  every `min_gen` floor injected at the P0→P1 seam, are **unchanged**.
* P1 is a pure LP with those floors fixed. Raising a generator's own bid cost can
  only weakly **decrease** its cleared output.

**So `gas_st_startup_cost=True` weakly LOWERS ST_GAS output. It cannot address a
−28.63 % under-run; it deepens it.** The lever the brief flagged as
"obvious-looking" is not merely un-grounded — it points the wrong way.

Sized, for completeness: at the model's class-aggregate run length the markup is
**$0.006–0.009/MWh** against a reference ST_GAS marginal cost of $23.51 (2024) /
$50.77 (2025) — negligible on the aggregate basis, though the *per-unit* markup
that would actually apply is larger and unobservable here (§2.4). Either way the
sign is fixed.

**One route is worth naming and refusing explicitly**, because it is the reading
that could survive §2.5: the markup would *raise* clearing prices in hours where
ST_GAS is marginal, which is the direction C3a-2025 wants. That route is refused
on nyiso-168 §4's measurement — the model already prices **+55 %** supply-curve
curvature against **+22 %** physical, so adding more markup adds more
**non-physical** steepness — and on rule 1 `[R-STRUCT]`, since the mechanism
would then be adopted for its price residual while making its own volume gate
worse.

### 2.6 S6 — the annual gas-price association does not survive at monthly grain

The brief's fact 3 (+40.9 / −6.0 / −28.6 % against gas $2.54 / $2.19 / $3.52) is
n=3. At monthly grain over all 36 training months the pooled slope is
**−0.0465 per $/MMBtu** (R² 0.114), but the per-year slopes are
**+0.116 / −0.0695 / −0.0138** — **not one sign**. The pooled negative is carried
by the *between-year* level difference, not by within-year response. **NOT
SUPPORTED**: the annual pattern must not be quoted as a mechanism.

## 3. What the object actually is — measured after the S2 failure

S7–S10 are **not** pre-registered gates. They were measured *because* S2 failed,
and are reported **in addition to** the registered gates, never in place of them
— the nyiso-171 A5b discipline.

### 3.1 S7 — the population is clean, so the deficit is real conduct

The model's eleven ST_GAS plants **are** the measured fleet. Off-model measured
volume is **0.63 % / 0.49 % / 0.68 %** — a single trivial plant (2594, 0.06–0.10
TWh); every other CAMPD non-CHP steam plant outside the model's list reports
**0.0000 TWh**. **There is no missing-plant input defect**, which is what makes
every statistic below meaningful.

### 3.2 S8 — a between-year RESPONSE deficit, in opposite directions

| | 2023 | 2024 | 2025 | 2023→2025 |
|---|---|---|---|---|
| measured ST_GAS (CAMPD gross, TWh) | 9.748 | 11.674 | 15.138 | **+55.3 %** |
| model ST_GAS (P1, TWh) | 11.471 | 9.321 | 9.787 | **−14.7 %** |
| measured ST_GAS share of gas | 0.169 | 0.179 | **0.225** | rising |
| model ST_GAS share of gas | 0.183 | 0.138 | **0.141** | falling |

Measured total gas grew +16.5 % (57.8 → 67.4 TWh) and the model's +10.8 %
(62.8 → 69.6): **the envelope is roughly right and the split inside it moves
opposite ways.** The market's incremental gas went to steam; the model's went to
CC. Measured CC_REGULAR was essentially flat (+1.5 %) while the model's grew
+8.6 %.

**And the model is doing correct isolated physics.** At ~10.9 heat rate for steam
against ~7 for CC, the ST−CC marginal-cost gap scales with fuel: ~$7.6/MWh at
$1.95 gas, ~$18.2/MWh at $4.66. A pure-economic stack *must* push steam back as
gas rises, and the model does. **The market did the opposite — so the missing
driver is not a cost-stack quantity, and no offer-level or startup-cost change
can supply it.** This is the sense in which the object is nyiso-170 §4's "third
thing": not an hour-local swap, but a trend divergence in what the two stacks
reach for.

### 3.3 S9 — 99.2 % of the growth is downstate

Measured ST_GAS growth 2023 → 2025, by the model's own zone assignment:

| zone | nameplate | 2023 | 2025 | growth | share of growth |
|---|---|---|---|---|---|
| NYC | 3,525 MW | 3.547 | 5.901 | **+2.354** | 43.7 % |
| Capital_Hudson | 2,879 MW | 1.205 | 2.814 | **+1.609** | 29.9 % |
| Long_Island | 2,349 MW | 4.269 | 5.651 | **+1.382** | 25.6 % |
| Upstate_West | 150 MW | 0.666 | 0.669 | **+0.004** | 0.07 % |

**99.2 % of the growth is in the three downstate / Hudson-corridor zones**;
Upstate_West contributes 0.07 % and the off-model plant 0.8 %. **Instrument limit, stated rather than worked around:** `class_hourly`
carries no zone column, so **the model's zonal ST_GAS dispatch is not observable
without a re-solve** — only the measured side is split here.

### 3.4 S10 — the counterpart, and the one result with a one-sided proof

The measured CC fleet's maximum output **within a month** is a strict lower bound
on what that fleet could have produced that month. Any hour in which the model's
CC exceeds it is a **proven over-statement of CC availability** — not an
inference, a bound.

| year | hours model CC > measured within-month max | share | CC mean gap | model CC peak / measured CC peak |
|---|---|---|---|---|
| 2023 | 93 | 1.06 % | +224 MW | 1.026 |
| 2024 | 773 | 8.82 % | +495 MW | 0.988 |
| 2025 | **1,211** | **13.82 %** | **+636 MW** | 0.994 |

The bound is **conservative twice over**: CAMPD `grossLoad` is gross while the
model's `class_hourly` is on the delivered basis (gross ≥ net), and a monthly
maximum is the loosest within-month bound available. The violation nevertheless
**grows monotonically with the ST_GAS deficit** (+40.9 → −6.0 → −28.6 %), and
**+636 MW × 8,760 h = 5.57 TWh** is close to the 2025 ST_GAS (−3.93) plus
CT_PEAKER (−1.82) = **−5.75 TWh** under-run.

Note the shape: the model matches the measured CC **peak** (0.99–1.03×) and
misses in the **middle** of the distribution — p95 8,471 vs 7,918 MW in 2025. The
excess is concentrated in winter — 2025 **Jan 432, Feb 343, Dec 161** hours, with
Oct 84 and Nov 39 — but is present in Mar/Apr/May too (45/44/33), so it is **not
a winter-only lane**, consistent with the brief's warning and with the deficit
being negative in all twelve months. ST_GAS itself violates the same bound in
**100 / 0 / 0** hours, i.e. essentially never: **the availability over-statement
is on the CC side, not the steam side.**

A plausible and checkable mechanism exists but **is not established here**: the
main historic overlay requires an outage of at least
`UNIT_OUTAGE_MIN_DAYS = 5` days (`data/outages.py:239`), so sub-5-day derates —
the duration class that downstate winter gas curtailment falls in — are invisible
to it, and the companion partial-plateau overlay is likewise a sustained-ceiling
construction. **That is a hypothesis for a successor, not a result of this
session**, and it is stated as such.

## 4. Lines this session closes

* **CLOSED — the ST_GAS deficit as a price-conditional dropout.** Failed its own
  pre-registered gate by **sign reversal**: +40.9 % over-run in 2023, positive in
  all ten IMH deciles, model threshold *left* of the market's. Do not re-open the
  "exits too readily as fuel rises" framing without an instrument that survives
  2023.
* **CLOSED — `gas_st_startup_cost` as a NYISO ST_GAS volume lever.** Refused two
  independent ways: **direction** (markup ≥ 0, P1-only ⇒ ST_GAS weakly decreases;
  it deepens the deficit) and **grounding** (the model-side instrument is
  degenerate — both class aggregates on in all 8,760 hours). The price-side
  reading is refused separately on nyiso-168 §4 (55 % modelled vs 22 % physical
  curvature) and rule 1 `[R-STRUCT]`.
* **CLOSED — a missing-plant / capacity input defect on ST_GAS.** Population
  clean (off-model < 0.7 %); required CF 0.176 against 1,575 MW of headroom at
  the model's own 2025 peak.
* **CLOSED — the annual gas-price association as a mechanism.** Per-year monthly
  slopes +0.116 / −0.0695 / −0.0138 do not share a sign; the pooled negative is a
  between-year level artifact.
* **NOT OPENED — any floor mechanism for ST_GAS.** The class already carries
  16.70/22.67/18.43 % `reliability_floor` plus the bridge, and the five downstate
  `tmax` limbs are deliberately disabled as the bridge's **replacement** (owner,
  2026-07-27) — re-arming them alongside it violates rule 19 `[R-ONE-MECH]` by
  construction, and a `tmax` window cannot carry an all-twelve-months deficit.
  Independently, a floor is a lower bound and the model **over**-runs ST_GAS by
  +40.9 % in 2023, so no static floor can serve both ends of the window.
* **NOT OPENED — an offer-level change.** nyiso-167 §5 already bounded
  `gas_offer_net_revenue_margin` and declined to re-open it; §3.2 adds that the
  model's cost stack is behaving correctly, so the missing driver is not a
  cost-stack quantity.
* **NOT RE-TESTED — the eighteen closed lines** of the brief, and **no C3c lever
  was opened.**

## 5. What is handed forward

**One named object with a one-sided proof: the CC availability over-statement.**
It is measured (§3.4), it grows with the failing year, its magnitude
(5.57 TWh-equivalent) matches the ST_GAS + CT_PEAKER under-run (5.75 TWh), and it
is on the **input** side rather than the offer side — which makes it a rule 14
`[R-ACCURATE]` question ("prefer accurate measured data") rather than a tuning
one. A successor opening it should note three things this session established:
the bound is conservative and one-sided, so the true over-statement is at least
this large; the shape is **mid-distribution, not peak**, so a flat capacity
haircut is the wrong instrument; and the `UNIT_OUTAGE_MIN_DAYS = 5` floor is a
**hypothesis for its cause, not a demonstrated one**.

Two instrument limits travel with it. **Model-side zonal dispatch is not
observable** from `class_hourly` (§3.3), so confirming the downstate reading
needs either a zone-resolved sidecar or a re-solve. And **per-unit model dispatch
is not observable either** (§2.4), which is what makes the cycling question
unanswerable from committed artifacts.

**Also carried forward, unrepaired, from nyiso-171:** East River (2493) is
`ST_CHP` in the model artifact but lands in `CC_CHP` under the shared CAMPD
`unitType` construction. This session used that same construction, so its CC_CHP
figures inherit the same basis; the ST_GAS series is unaffected (East River is
not in it), and every ST_GAS result above is independent of that defect.

## 6. Honest expected value

**What is delivered.** A reproducible, zero-solve identification that (a) **kills
the brief's own premise on its own pre-registered gate**, by sign reversal rather
than by weakness, (b) relocates the object from within-year price response to a
**between-year response divergence**, sized at +55.3 % measured against −14.7 %
modelled, (c) shows the model's cost stack is doing *correct* physics, which is
what rules out the whole offer/startup family rather than merely declining it,
(d) refuses the brief's named trap on the **code**, ex ante, in the one direction
that matters, (e) locates 99.2 % of the measured growth downstate, and (f) hands
forward a counterpart defect with a **one-sided proof** rather than an
association.

**What is NOT delivered. No gate moves.** C3a-2025 is still −11.5 %, C3c still
fails, the determination is still **NOT-YET on {C3a-2025, C3c}**, and NYISO still
does not read CALIBRATED. **No solve ran**, so rule 15 registers nothing — the
dashboard is untouched by design, not by omission. **No lever was armed**, and
the 0.70 gain is unmeasured against any arm because no arm was built. The CC
availability object is *identified*, not *repaired*; repairing it is a measured-
input intake, which is a different lane and a larger one.

**What could still be wrong.** The S10 bound is one-sided and therefore
conclusive only in one direction: it proves the model's CC availability is *too
high* in those hours, and says nothing about hours where it may be too low. The
monthly maximum is a loose bound, so the hour counts are lower bounds on the
violation, but the *mean gap* (+636 MW) is a two-sided statistic and could in
principle be produced by a shape difference rather than an availability one —
the two are not separated here. The gross-vs-delivered basis difference between
CAMPD and `class_hourly` is handled by the anchor for level comparisons and by
conservatism for the S10 bound, but it is not eliminated, and the ST_GAS T50
statistic in §2.2 inherits it. S9's zonal attribution is **measured-side only**,
so "the model puts this energy in the wrong zone" is *consistent with* the
evidence but not demonstrated by it. And the 5-day outage-window hypothesis in
§3.4 is exactly that — the correlation between the winter concentration and the
downstate gas-curtailment duration class is suggestive, not established.

**The honest read on the object.** After nyiso-167/168/169/170/171 and this
session, NYISO's C3a-2025 miss has been narrowed to "the model is short about
half the market's non-physical supply-curve steepness in ordinary daytime hours",
and the composition half of that now has a named carrier: **the model keeps its
CC fleet available in the middle of the load distribution in hours the real CC
fleet demonstrably could not, and meets load there with CC instead of the
downstate steam and peakers the market actually ran.** That is an input-side
object with a one-sided proof, which is a better place to be than the
association nyiso-170 could hand forward — but it is **not yet a lever**, and a
successor should not expect the current data set to close C3a-2025 without the
availability intake.

## 7. Evidence

* `results/calibration/PREREG-nyiso172-st-gas-level-deficit.md` — the gates,
  committed with the probe before either ran (`8c3e9b6c`)
* `scripts/probes/nyiso172_st_gas_level_deficit.py` — the probe
* `results/calibration/_nyiso172_st_gas_level_deficit.json` — every number above
* keeper `results/calibration/nyiso159_lossarm_B/` — `legitimacy_diagnostics.json`
  (D-2), `run_config.json`, `hourly/class_hourly_<year>.parquet`
* `src/market_sim/model/commitment.py:280` (`_amortized`), `:312` (the `gas_st`
  gate); `src/market_sim/pipeline/solve.py:308` (`mc_bid = mc_base + markup`);
  `src/market_sim/data/outages.py:239` (`UNIT_OUTAGE_MIN_DAYS = 5`)
* predecessors: `docs/FINDING-nyiso167-c3a-price-response-gain-2026-09-01.md`,
  `-nyiso168-supply-curve-slope-anatomy-`, `-nyiso169-congestion-gradient-anatomy-`,
  `-nyiso170-merit-order-displacement-`, `-nyiso171-chp-floor-portfolio-artifact-`
