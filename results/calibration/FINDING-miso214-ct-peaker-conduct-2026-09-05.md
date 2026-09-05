# FINDING miso-214 — THE MIDWEST CT_PEAKER FLEET AT ITS OWN DELIVERED COST: 62–70 % of the CT energy the model misses was produced by the real market BELOW the plant's own delivered cost, at the real market's own price — so most of the CT gap is not reachable by any price or offer mechanism; the pre-registered commitment-bridge guess is REFUTED by the B hours' own conduct; **NO A/B CHARTERED (K-d fires — MISO publishes no admissible measured input for it)**; and the census names a MEASURED, un-tested offer-form coverage gap for miso-215 (2026-09-05)

**Keeper UNCHANGED at `2026-09-05-miso-213-layering`** (bundle
`results/calibration/miso213_layering_B`), NOT-YET on C3a-2025 alone (−11.747 %), C3c
ledgered 3/3, C6 attested 41/2. **Zero solve. Nothing minted. No `ScenarioConfig` field
created, no matrix row added.** PREREG
`PREREG-miso214-ct-peaker-conduct-2026-09-05.md` pushed **BLIND** at `067a305a`, before
any adjudicating statistic and before any arm was designed. Probe
`scripts/probes/_miso214_ct_peaker_conduct_phase0.py` → record
`results/calibration/_miso214_ct_peaker_conduct.json`. Rule 22 `[R-HOLDOUT]`: 2023–2025
only.

---

## 0. Verdict in one paragraph

miso-213 left CT_PEAKER as the largest C1 mover on the board (−3.33 / −2.32 / −3.62 TWh)
and 5.1 TWh under actual in 2023. This session asked the pre-registered question — did the
market run peakers the model has out of merit because the model's PRICE is too low (the
C3a object), or because the market ran them for a non-energy reason (a conduct object)? The
answer is neither of the two shapes the charter expected, and it is emphatic. Over every
missed plant-hour — a model CT_PEAKER plant CAMPD shows running that the screen has out of
merit — **80.1 / 76.2 / 68.7 % of the missed MWh was produced at an ACTUAL market price
below the plant's own measured delivered cost**, and the reading survives every instrument
check that could soften it: 64.4 / 56.7 / 53.2 % on the plant's own measured INCREMENTAL
burn, 51.7 / 55.0 / 58.3 % when the fuel is re-priced at the Henry Hub commodity floor
instead of the plant's all-in delivered print, and 59.9 / 55.4 / 44.1 % when the unit is
paid the better of the day-ahead and real-time price. That energy is not reachable by any
offer or price mechanism, because the price itself is below the cost — it is the observable
footprint of a fleet whose energy cost is not recovered from the energy price. **K-a passes
in all three years, against my own P-2 prediction; K-b stays silent; K-e passes — and K-d
FIRES**: MISO publishes nothing that represents that conduct at class grain (its offer
corpus carries no technology attribute and its class bridge was REFUTED at miso-138; its
ASM series is region × product, never per unit), and the B hours' OWN signature refutes the
two mechanisms CAMPD alone could build — they sit mid-block at a 0.70–0.78 load factor, not
at min load, and their share in the region's reserve top decile is 0.105–0.124, i.e. the
unconditional 10 %. The P-5 commitment-bridge guess is refuted by data, not merely unbuilt.
Nothing is chartered. What the session hands forward instead is a **measured, un-tested
defect the census found**: `gas_offer_net_revenue_margin` is armed on MISO (cell K) and
structurally **cannot reach the intermediate-duty cohorts** — `CT_INTERMEDIATE`,
`CC_INTERMEDIATE` and `ST_GAS_INTERMEDIATE` carry no `phys_*` keys, so
`gas_offer_margin_markup_mult` returns 0 and those tranches stay in the fully fuel-scaled
multiplier form the mechanism exists to replace. On MISO's CT class that is 44 plants /
9,333 MW — 41.9 % of class capacity carrying 55–57 % of the class's measured energy — at a
cap-weighted econ offer heat rate of 12.465 with a markup of exactly **0.000**, against the
true-peaker cohort's 8.649 + 3.906. Its static reach is measured here and is mostly
**ADVERSE**; its two risks are named in advance. That is miso-215's head.

## 1. Instrument, and what it can and cannot see (PREREG §2, restated with the measurements)

* **Plant- and zone-grain model merit is a PRICE-TAKING STATIC SCREEN**, not the LP: neither
  the keeper (`miso213_layering_B`) nor the control (`miso210_clock_B`) ships `unit_hourly/`
  or `dispatch/`, and `class_band_hourly` carries no zone. The screen prices the HEAD fleet
  chain (`build_year` under the keeper's own recorded config, `mc_base`, no P1 startup
  adder) against the keeper's own committed P1 zone prices. **It is loose in BOTH
  directions and the looseness is quantified**: the screen's class total is 1.430 / 1.410 /
  1.416 × the LP's own (17.05 / 25.87 / 22.80 vs 11.92 / 18.35 / 16.10 TWh), and it also
  runs plants CAMPD shows OFF in 163,978 / 232,484 / 242,957 plant-hours (9.74 / 16.24 /
  12.33 TWh). Because "missed" requires the screen to have the plant out of merit, the
  missed set is a CONSERVATIVE population: the LP misses at least as much.
* **Config footing.** The two bundles' recorded `scenario_config` blocks differ in **zero**
  of the 783 fields present in both; the arm carries six fields the control's record lacks,
  five of them added to `main` after the control solved and at their defaults, the sixth
  being miso-213's own `miso_zonal_gas_basis_skip_923_priced`.
* **CAMPD** is read from `data/raw/campd-unit-level/` directly (not through
  `load_campd_hourly`, which drops `opTime`), simple-cycle units only
  (`unitType` startswith "Combustion turbine"), on the model's fixed 8760 clock with **no
  timezone shift** — the established convention of every prior MISO CAMPD probe
  (miso-208/209/212), disclosed rather than corrected. CEMS covers **90.2 %** of the model's
  CT_PEAKER capacity (20,094.6 of 22,281.8 MW; 90 of 166 plants) in every year, clearing
  K-e's 60 % bar.
* **CAMPD GROSS vs the model's NET** tranches, unadjusted. The wedge (~1 % for a
  simple-cycle CT) makes the plant's own $/MWh cost slightly UNDERSTATED, i.e. it works
  AGAINST the B reading, not for it.
* **Three cost bases, all measured, all reported**: (i) all-in — the plant's own resolved
  delivered price × its own CAMPD average burn heat rate; (ii) incremental — the model's own
  physical leg `heat_rate − offer_markup_hr`, i.e. the plant's own measured base heat rate
  times the frozen class marginal multiplier (`miso_campd_marginal_hr_summary.csv`, n = 249,
  `marg_econ_low/high` 0.687 / 0.691); (iii) an independent per-unit input-output fit
  `heat = a + b·MW` over the unit's steady-state hours (`opTime ≥ 0.98`, inside its own
  p3–p97 load envelope), covering 78–80 % of cohort capacity. Cap-weighted these read
  **11.53 / 11.62 / 11.70** (average burn), **10.24** (the model's physical leg today) and
  **8.76 / 9.03 / 8.83** (I-O slope) MMBtu/MWh.
  **The 10.24 is a MIXTURE and is contaminated by the very defect §6 names**: under the
  coverage gap the intermediate cohort's "physical leg" IS its full offer heat rate (12.465,
  markup 0.000), against the true-peaker cohort's 8.649. So basis (ii) OVERSTATES the
  intermediate cohort's incremental cost and its B1 reading with it; basis (iii), the
  independent I-O fit, is the clean comparator and is reported beside it throughout.
* **The 923 print is an ALL-IN delivered cost** — commodity plus fixed firm-transport
  demand charges, which do not enter an hourly offer. The average-vs-marginal
  delivered-cost convention (miso-212 §8) is **OWNER-COURT and untouched**; §5 reports the
  size of its contribution as a bound and adjudicates nothing.
* **MISO's masked energy-offer corpus cannot carry this question at all** — no fuel or
  technology attribute, class bridge REFUTED at miso-138, payload gitignored and absent in
  this container. This is a property of the data, not a choice; it is what makes K-d bind
  in §4.

## 2. L-1 — where miso-213's 3.3 / 2.3 / 3.6 TWh went. **P-1 RIGHT on all three legs.**

**(a) Band** — from the LP's own `class_band_hourly`, control (`miso210_clock_B`) vs arm
(the keeper), TWh:

| band | 2023 Δ | 2024 Δ | 2025 Δ |
|---|---:|---:|---:|
| committed | −0.859 | −0.598 | −0.881 |
| **econ** | **−2.465** | **−1.713** | **−2.738** |
| peak | 0.000 | −0.001 | 0.000 |
| **class** | **−3.324** | **−2.312** | **−3.619** |

econ share of the class delta **0.742 / 0.741 / 0.757** against the pre-registered ≥ 0.70
(0.70). The mechanism held: the peak band sits at 4.0 × base HR and never clears; a floored
hour cannot lose energy.

**(b) Zone**, from the static screen (the sidecars carry no zone). The prediction was
sign-derived from miso-213's own increment table and is **year-specific**:

| year | increment removed (W/P, IIE, South) | loss share IIE | loss share W+P | pre-registered bar | verdict |
|---|---|---:|---:|---|---|
| 2023 | +0.307 / **−0.260** / +0.143 | **1.000** | 0.000 | IIE ≥ 0.60 | RIGHT |
| 2024 | +0.087 / **−0.150** / +0.118 | **1.000** | 0.000 | IIE ≥ 0.50 | RIGHT |
| 2025 | **−0.642** / −0.039 / +0.287 | 0.095 | **0.905** | W+P ≥ 0.50 | RIGHT |

A uniform or South-led loss would have falsified the mechanism outright. It did not: the
loss follows the zones whose discount was removed, and it switches hemisphere between 2024
and 2025 exactly as the sign of the increment does.

**(c) Diurnal** — share of the lost MWh OUTSIDE the reliability floor's own window
(HOD 15–21, the armed MISO CT_PEAKER `netload` limbs' `start_hour`/`end_hour`, applied by
`interchange/core.py` as `hod >= sh & hod <= eh`): **0.651 / 0.691 / 0.673** against the
pre-registered ≥ 0.60 (0.65). Energy cannot be lost where the floor holds the class up.

## 3. L-2 — THE DISCRIMINATOR. **P-2 WRONG in every year and in its ordering.**

Missed plant-hours: 64,777 / 62,969 / 64,457, carrying **8.60 / 8.31 / 8.09 TWh** of CAMPD
gross — **53.5 / 45.2 / 42.9 %** of the CT class's measured energy. MWh-weighted, on the
plant's own ALL-IN cost:

| bucket | 2023 | 2024 | 2025 | PREREG band |
|---|---:|---:|---:|---|
| **B** market-out-of-merit (cost > ACTUAL RT) | **0.801** | **0.762** | **0.687** | 0.20–0.40 |
| A price-reachable (cost ≤ actual, cost > model) | 0.131 | 0.130 | 0.215 | 0.45–0.65 |
| C model-internal (cost ≤ MODEL price, model idle) | 0.167 | 0.257 | 0.167 | 0.05–0.20 |
| *exclusive partition C → A → B* | 0.167 / 0.131 / **0.701** | 0.257 / 0.130 / **0.613** | 0.167 / 0.215 / **0.618** | A > B > C |

**Every leg of P-2 is wrong, and the ordering is inverted**: I predicted A > B > C at
45–65 / 20–40 / 5–20 % and pre-registered the C3a tail as the likely object. B is the
largest bucket by a wide margin in all three years and A the smallest in two of three.

**B survives every instrument check that could soften it** (each measured, each reported):

| basis | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| all-in cost vs RT (headline) | 0.801 | 0.762 | 0.687 |
| **measured INCREMENTAL** cost vs RT (B1) | 0.644 | 0.567 | 0.532 |
| independent I-O-fit incremental vs RT | 0.544 | 0.529 | 0.444 |
| all-in cost at **Henry Hub** commodity vs RT | 0.517 | 0.550 | 0.583 |
| incremental at Henry Hub vs RT | 0.436 | 0.406 | 0.488 |
| all-in vs **day-ahead** price | 0.662 | 0.622 | 0.507 |
| all-in vs **max(DA, RT)** | 0.599 | 0.554 | 0.441 |

The strictest SINGLE substitution on the board — Henry Hub commodity fuel on the
incremental burn — still leaves **41–49 %** of the missed CT energy produced below the
plant's own cost at the price the market actually paid, and the day-ahead settlement leg
independently leaves 44–60 %. The combined substitution (commodity fuel **and** incremental
burn **and** max(DA, RT)) was not computed and is not claimed. B2 — above
incremental but below all-in, the make-whole/commitment band — is only 0.157 / 0.195 /
0.154, so B is not a cost-recovery artefact: it is out of merit on the incremental burn too.

Levels, MWh-weighted over the missed hours ($/MWh): actual RT **39.30 / 36.11 / 52.52**,
model P1 35.33 / 32.37 / 42.34 (gap +3.96 / +3.73 / **+10.17** — the C3a object, and it is
real but small against the cost), all-in cost 46.87 / 41.79 / 49.67, incremental cost 43.92
/ 38.70 / 46.92. The median missed MWh is **−$9.13 / −$7.46 / −$7.77** under water on
all-in cost against the RT price it was paid.

**K-b (the offer-level trap) stays silent.** Removing the CT econ residual margin entirely
— the miso-134 full measured swap, $7.32/MWh cap-weighted, band-scoped to econ — flips
**0.343 / 0.489 / 0.460** of bucket A in-merit, under the frozen 0.60 kill. The offer level
adjudicated `R` at miso-134/179 does not explain bucket A, and it cannot explain B at all.

## 4. Why nothing is chartered — **K-d fires, and the data refutes the pre-registered guess**

PREREG §4 charters an A/B only if all of K-a…K-e hold. K-a passes 3/3 (bar 0.40, and 3/3 on
the incremental basis too), K-b is silent, K-e passes at 0.902. **K-d fires.** The input
that would represent bucket B must be a reproducible physical/market quantity that
regenerates for a forward year (rule 13 `[R-MEASURED]`). At MISO there is none:

* the **masked energy-offer corpus** has no fuel or technology attribute and its class
  bridge was built and REFUTED at miso-138 — it cannot be resolved to CT_PEAKER at any
  price;
* the **ASM series** (`asm_rt_cleared_mw_*`) is Region × product hourly, never per unit, so
  attributing reserve duty to the CT class requires an assumption, not a measurement;
* **CAMPD** records that the units ran, never why.

And the B hours' own conduct refutes the two mechanisms CAMPD alone could build — the
`nyiso_gas_commitment_bridge` min-run/min-load construction P-5 named:

| statistic, MWh-weighted | all running | missed | **B hours** |
|---|---:|---:|---:|
| unit load factor (own max), 2023 / 2024 / 2025 | 0.792 / 0.786 / 0.758 | 0.776 / 0.757 / 0.726 | **0.769 / 0.746 / 0.703** |
| share in the plant region's reserve top decile | 0.124 / 0.130 / 0.105 | 0.124 / 0.120 / 0.101 | **0.120 / 0.123 / 0.105** |

A min-load AS reservation would put the B hours AT min load; they sit at ~0.70–0.78 of the
unit's own maximum. A reserve-duty driver would concentrate them in reserve-tight hours;
their share of the region's reserve top decile is the unconditional 10 %. And the unit-grain
run-block anatomy puts the B energy mid-block, not in start/stop tails. **P-5's mechanism
guess is refuted by measurement, not merely unbuilt** — which is the cleaner outcome, and
it is why an A/B on B would have had no admissible driver to key on.

**K-c is not reached** (nothing is proposed), but the census records the live constraint for
any future CT floor: `reliability_floor` is the ONLY D-2 mechanism touching MISO CT_PEAKER,
and its forced share is **0.204 / 0.122 / 0.142** — **2023 FAILS the 15 % peaker budget**
(2.195 of 10.740 TWh) and reads PASS only on rule 20's conditional provenance+shape route
(D-4 `reliability_floor × CT_PEAKER`, declared window h14–21, off-window share 0.0000 in
all three years; D-1 `profile_r` 0.962 / 0.973 / 0.986 and `cv_ratio` 1.193 / 0.991 / 1.289,
PASS all years). **P-4's magnitude leg is WRONG in 2023.** Any new CT floor would land on a
class already over its budget in the year with the largest gap.

## 5. L-3 — the 2023 question. **P-3 RIGHT in all three years.**

CAMPD (covered plants) minus the LP's own class series, on the 8760 clock:

| year | CAMPD TWh | LP TWh | net gap | under-dispatch MWh | JJA share of the under-dispatch | h15–21 share |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 16.076 | 11.920 | **+4.156** | 5.87 M | **0.434** | 0.314 |
| 2024 | 18.381 | 18.351 | +0.030 | 4.65 M | **0.436** | 0.310 |
| 2025 | 18.852 | 16.097 | **+2.755** | 5.25 M | **0.522** | 0.309 |

Against the pre-registered ≤ 0.55 (JJA is 25.2 % of hours; a tail phenomenon would be
≥ 0.70). **The 2023 CT under-dispatch is an all-hours phenomenon with a summer tilt, not a
summer tail** — which is what the mechanism predicted, because 2023's C3a is +0.91 % (the
model's mean price is ABOVE actual) and the tail story is least available there. 2025 is the
closest to the bar at 0.522, consistent with its much larger price gap in the missed hours
(+$10.17 vs +$3.96 / +$3.73). Note 2024's net gap is +0.03 TWh — the class total matches
almost exactly while 4.65 TWh of hour-level under-dispatch and a comparable over-dispatch
cancel: **the CT problem is a placement problem in 2024, not a level problem.**

## 6. What the census found, and what it hands to miso-215

`ct_intermediate_split` (armed, keeper) routes a CT_PEAKER plant whose measured median CF
≥ 50 to the flatter `CT_INTERMEDIATE` offer curve. **That curve carries no `phys_*` keys.**
`gas_offer_margin_markup_mult` returns 0.0 for a band whose `phys_*` key is absent — the
documented rule-24 neutral fallback — so `apply_gas_offer_margin` skips the whole cohort and
its offer stays in the fully fuel-scaled multiplier form that `gas_offer_net_revenue_margin`
(MISO cell **K**) exists to replace. Measured off the assembled fleet:

| | CT_INTERMEDIATE cohort | true-peaker cohort |
|---|---:|---:|
| plants / capacity | **44 / 9,333.2 MW (41.9 %)** | 122 / 12,948.6 MW |
| econ tranches | 264 | 243 |
| cap-w econ **offer** HR | 12.465 | 12.555 |
| cap-w econ **physical leg** HR | **12.465** | 8.649 |
| cap-w econ **markup** HR | **0.000** | 3.906 |
| CAMPD energy 2023 / 24 / 25 (TWh) | 9.23 / 10.15 / 10.83 (**55–57 % of the class**) | 6.85 / 8.23 / 8.02 |
| CAMPD average burn HR (cap-w) | 11.07 / 11.01 / 11.11 | 11.94 / 12.15 / 12.22 |

`CC_INTERMEDIATE` and `ST_GAS_INTERMEDIATE` carry no `phys_*` keys either; `CT_PEAKER`,
`CC_REGULAR` and `ST_GAS` carry all four. **The cohort offers its energy at 12.465
MMBtu/MWh against its own measured average burn of 11.07** — above its own ALL-IN burn, and
**+60 %** above the measured incremental its own offer would decompose to (7.81 MMBtu/MWh,
implied by the $14.20/MWh fixed margin at the anchor below).

**Static reach, measured (the miso-213 L-3 instrument; NOT an arm, nothing built).**
Repricing only the cohort's 264 econ tranches into the margin form at the frozen class p50s
(0.687 / 0.691) — zero free parameters, byte-identical at fuel = anchor — moves the screen
by **−1.475 / −5.285 / +1.457 TWh** and flips **1.1 / 0.8 / 8.0 %** of the missed MWh in
(33.0 % of bucket C in 2025). **The direction is year-dependent and mostly ADVERSE**, and
the reason is measurable: the fixed margin is priced at
`gas_offer_margin_anchor = 3.0492 $/MMBtu` while the cohort's own resolved delivered fuel is
**4.424 / 3.494 / 4.156**, with only **0.606 / 0.435 / 0.840** of its econ capacity-hours
above the anchor. Below the anchor the margin form RAISES the offer.

**Two risks, named in advance for miso-215's prereg**: (1) **K-1** — the C1 band's tightest
MISO cell is CC_REGULAR-2024 at +7.419 against ±8.00 (0.58 TWh of headroom), and a −5.3 TWh
screen-bound reduction in CT-2024 backfills to CC; (2) **C8** — CT_PEAKER-2023 is already
over the 15 % peaker budget at 20.4 %, and less CT energy raises the forced share further.
A miso-215 prereg must state both before it solves.

## 7. My prior, scored against interest

* **P-1 RIGHT on all three legs** (band 0.742/0.741/0.757 ≥ 0.70; zone IIE 1.00/1.00 and
  W+P 0.905, the sign-derived year-specific bars; diurnal 0.651/0.691/0.673 ≥ 0.60).
* **P-2 WRONG in every year and in its ordering** — I predicted A > B > C with A 45–65 %
  and B 20–40 %; the measurement is B 0.70/0.61/0.62 exclusive and A 0.13/0.13/0.22. I
  pre-registered the C3a tail as the likely object and it is the smallest bucket in two of
  three years.
* **P-3 RIGHT** (0.434 / 0.436 / 0.522 ≤ 0.55).
* **P-4 mixed**: the mechanism list is RIGHT (five, no more; `reliability_floor` the only
  D-2 row) and the magnitude leg is **WRONG in 2023** — 0.204 is a real D-2 FAIL, passing
  only on rule 20's conditional route.
* **P-5**: I put P(charter) at 0.35 and expected a commitment object if B cleared. B cleared
  emphatically and **no A/B is chartered anyway** — and the mechanism I named is REFUTED by
  the B hours' own load factor, reserve state and block position, not merely unbuilt.

## 8. Reported against interest

1. **The static screen is loose in both directions and the numbers depend on it.** It runs
   1.41–1.43 × the LP's own class energy and puts plants in merit that CAMPD shows off in
   9.7–16.2 TWh of plant-hours. The missed set is conservative by construction, but every
   bucket share is a share of a population the bound defines.
2. **Bucket B is a residual category.** "Out of merit at the market's own price" is
   consistent with reserve duty, local-reliability/VLR commitment, a self-schedule, a
   bilateral or hedge obligation — and with cost measurement error. It does not identify a
   mechanism; §4 is a statement that MISO's public data cannot identify one, not that one
   does not exist.
3. **The delivered-cost convention is the largest single quantified lever on this class and
   it is OWNER-COURT.** The model's resolved delivered price for the CT cohorts sits
   **+1.89 / +1.30 / +0.64** (intermediate) and **+3.81 / +2.48 / +2.10** (true peaker)
   $/MMBtu over Henry Hub daily — at 11–12 MMBtu/MWh that is $7–45/MWh of offer. Re-pricing
   at the commodity floor cuts B from 0.80/0.76/0.69 to 0.52/0.55/0.58. Two caveats that
   cut against reading too much into it: the per-plant excess is **concentrated** (miso-213
   L-2 measured the same population at Midwest p50 +0.60/+0.38/+0.17 against a cap-weighted
   mean of +1.70/+1.12/+0.86), and this session's excess is computed on the model's
   **resolved** delivered price, which includes the dual-fuel oil-parity step where it binds
   — so part of it is oil pricing, not a gas print. Nothing here adjudicates the convention.
4. **The 2025 face is the weakest year's actuals** (preliminary EIA-923 vintage, C1
   SKIPPED) and it is also the year with the largest price gap in the missed hours. The
   headline B reading is at its LOWEST in 2025 (0.687) — the year the C3a story is
   strongest — and at its highest in 2023 (0.801), the year the model's mean price is too
   HIGH. That ordering is the right way round for the conclusion and is stated so a reader
   can check it.
5. **The candidate named in §6 was found by the L-4 census, not by the pre-registered
   discriminator**, and it is NOT chartered here for that reason. It gets its own prereg,
   with its own predictions, pushed blind — including the fact, measured above, that its
   direction is set by where delivered fuel sits against a $3.0492 anchor and is adverse in
   two of three years.

## 9. Governance

Rule 15 `[R-DASHBOARD]`: zero-solve session — no run produced, none registered; the
deliverables are this finding, the PREREG, the probe and its JSON record. Rule 22: 2023–2025
only (the probe hard-asserts it). Rule 25 `[R-ISO-SCOPE]`: only
`docs/codebase-site/data/mechanism-matrix/MISO.js` is edited; no field added, so no base row
and no other shard is touched (rule 28c not engaged). Rule 28(b): the two cells this session
produced evidence about — `gas_offer_net_revenue_margin` (the coverage gap; cell UNCHANGED
at K, it is evidence about the mechanism's REACH) and `reliability_floor` (the CT_PEAKER
D-2 2023 over-budget conditional pass; cell UNCHANGED at K) — are updated in this session.
Rule 13: CAMPD conduct, the EIA-923 print path, the measured zonal LMP and the ASM cleared-MW
series are read as DIAGNOSTICS only; no measured outcome is fed back as an input. Rule 23:
no derive script touched — the marginal-HR table is read, never re-derived. Rule 24: no new
tunable. Rule 27 `[R-PUSH]`: every file edited locally and blob-verified after push.
DO-NOT-REDO honoured: `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
`miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
`miso_south_gas_delivered_cost_basis` (R) are neither re-tested nor re-opened; the
average-vs-marginal convention and the D-2 5(i) seam-response object stay OWNER-COURT; the
South price separation (miso-211 D-3) is untouched.

**One instrument defect found and fixed mid-session, disclosed**: the probe's first
three-year launch ran on the CONTROL config. `_miso212_south_gas_cost_basis` transitively
imports `_miso211_rdt_binding_state`, which re-points `_miso134.BUNDLE` to `miso210_clock_B`
at module scope — so the T-1 re-pointing block, placed before that import, was silently
overwritten. The block now sits AFTER the last import and carries a hard assert on
`miso_zonal_gas_basis_skip_923_priced`; the run that produced this record is the re-run. No
number in this finding comes from the bad run.

Next shorthand: **miso-215**.
