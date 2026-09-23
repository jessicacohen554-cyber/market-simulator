# RESULT — SPP-74, THE BODY: where the rung's ordinary-hour / whole-month price error lives

**Zero LP. No shard, no solve, no bundle, no `ScenarioConfig` field, no cell verdict moved.**
Pre-registration: `docs/handoffs/PRECOMMIT-spp-74-price-body-2026-09-23.md`, pushed at `84833817`
before any decomposition number was read. Base `fbe00eb1`. Probes: `scripts/probes/_spp74_body_decomposition.py`
(part A + `low_side_dispatch`), `_spp74_marginal_fuel.py` (part B, one interpreter per year),
`_spp74_mo_jan2022.py`. Outputs: `results/calibration/_spp74_*.json`.

---

## 0. Headline

- **No body object is measured-and-admissible for the four price rows.** Each row is now
  localized, but every localization lands on an already-adjudicated family or on no measured input.
- **2020 is one compressed distribution.** The model is +$1–2/h too dear in *every* RT hour-type
  below the upper tercile, and too cheap above it. Removing either the low side *or* the ordinary
  hours alone passes both 2020 rows. Neither half, then, is "the" object.
- **The low side is thermal that stays online.** In the 936 h RT went negative in 2020, measured
  SPP ran **3.3 GW more thermal** and **3.7 GW less wind** than the model. The model backs thermal
  down to its floors and clears at **+$3.74** instead of **−$11.55**. This is SPP-64/66/68/71's R-bc
  object. The new fact is its split: **~half gas in 2020, ~70 % gas in 2022**. The armed coal
  floor can reach only the coal half.
- **Ordinary hours are a LEVEL error, not quantity or fuel price.** Holding the stack fixed, the
  model's marginal cost at the *measured* thermal quantity is +$3.6 to +7.5 above RT. The
  quantity term is ≈0 or negative. Model gas tracks the published EIA KS series within $0.1–0.7,
  and on the low side at that.
- **2022's C3b lives in the upper tercile** (excluding top-88): model $63.8 vs RT $93.7. The
  marginal unit is gas at HR 8–9, while RT implies HR 11–13. That is the offer-shape object, refused
  by construction in xiso §10.
- **One genuine measured-input defect was found, and it moves no row.** The committed EIA table
  prints **N3045MO3 Jan 2022 = $152.45/Mcf** (23.8× the US series; MO's other months are $4.31–7.27).
  The SPP-49 plausibility screen *trusts that reference*. It therefore overwrites every correct MO
  print with $147.15/MMBtu, and the nearby pool spreads it. The result is **5,590 MW of SPP gas
  priced at $48–147/MMBtu for all of January 2022**. Price effect: −$0.38 on January. C3b 2022
  moves 0.2083 → 0.2075 and **still FAILS**. Routed (§6).

## 1. Rows re-verified. The keeper moved after the brief was written.

`keepers/SPP.json` now designates **`2026-09-22-hydro-5-spp-floor`**, with rung
`2026-09-22-hydro-5-spp-rung` stamped to it. The delta on SPP-71 is `hydro_min_flow_floor=true`.
This lane measured that rung.

| row | brief (spp71 rung) | **hydro-5 rung (scorer)** | this instrument | owning object (§5) |
|---|---:|---:|---:|---|
| C3a 2020 | +17.3 % | **+15.5 %** (19.08 vs 16.52) | +15.52 % | 2020 body compression: low side (R-bc family) + ordinary level |
| C3b 2020 | 0.267 | **0.257** | 0.257 | same |
| C3b 2021 | 0.243 | **0.234** | 0.234 | Feb 2021 (Uri): the ledgered wedge |
| C3b 2022 | 0.208 | **0.208** | 0.208 | upper tercile: offer shape (xiso-refused) |
| C1 COAL_PRB 2022 | — | **+9.60 TWh** (band ±8.00) | — | SPP-69 §4 coal/gas crossover (not in brief; new on hydro-5 rung) |
| C2 gas 2022 | — | **NRMSE 0.321** (band 0.30) | — | same object, mirrored |

## 2. The split (PRECOMMIT §1). Annual equal-hour gap, $/MWh, and the §2 ownership test

| year | NEG (a≤0) | LOW (0–10) | MID1 | MID2 | HIGH | TOP-88 | total | basis (dw−eq) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020 | **+1.64** (936 h) | +0.91 (1,074) | +1.32 | +1.11 | −1.58 | −1.51 | +1.88 | +0.68 |
| 2022 | +1.70 (995) | +0.81 (685) | +2.89 | +0.40 | **−7.76** | −2.86 | −4.82 | +2.66 |

Removing one object's hourly error at a time (diagnostic only, never an input):

| object removed | C3a 2020 | C3b 2020 | C3b 2022 |
|---|---|---|---|
| NEG ∪ LOW | 1.0 % **OWNS** | 0.165 **OWNS** | 0.207 MINOR |
| NEG alone | 6.4 % OWNS | 0.180 OWNS | 0.206 MINOR |
| MID1 ∪ MID2 | 0.8 % **OWNS** | 0.199 **OWNS** | 0.212 OPPOSES |
| HIGH (ex-top) | 25.6 % OPPOSES | 0.288 OPPOSES | 0.170 **OWNS** |
| TOP-88 | 25.3 % OPPOSES | 0.274 OPPOSES | 0.174 OWNS (ledgered wedge) |

C3b 2021: removing February's month error alone → **0.071**. Uri owns it.

## 3. The four measurements

**(a) Low side (R-be).** Hours per year:

| | RT < 0 | RT < −26 | model ≤ 0 | model at −26 clamp |
|---|---:|---:|---:|---:|
| 2020 | **936** | 96 | **391** | 373 |
| 2022 | 995 | 69 | 623 | 594 |

When the model does go negative, it is at the clamp (95 %+ of such hours). RT's negative hours
average **−$11.55**. The clamp is too deep *and* too rare. Dispatch inside those hours (GW, model / EIA-930):

| RT hour-type | price model / RT | coal | gas | wind |
|---|---|---|---|---|
| 2020 NEG | 3.74 / −11.55 | 3.79 / 5.37 | 2.33 / 4.08 | **17.96 / 14.25** |
| 2020 LOW | 13.35 / 5.94 | 4.78 / 6.41 | 4.78 / 5.12 | 15.37 / 13.05 |
| 2020 MID2 | 21.47 / 17.14 | 8.86 / 10.63 | 10.26 / 8.96 | 7.56 / 7.41 |
| 2022 NEG | 2.61 / −12.36 | 4.59 / 5.71 | **0.56 / 3.01** | **21.55 / 17.70** |

The wind gap exists only on the low side. Above LOW, wind matches within 0.7 GW. So the price
gap is not a wind *offer* question. That confirms the SPP-51b `I` verdicts on
`negative_renewable_offers` / `wind_ptc_vintage_offers`: making wind's bid less negative would
move the clamp hours *up* and worsen C3a 2020. It is the R-bc "supply pushed up from below"
object (SPP-71 §0). **New evidence vs the prior verdicts:** of the 3.3 GW thermal deficit in
2020's RT-negative hours, **1.58 GW is coal and 1.75 GW gas**. In 2022 it is 1.12 coal / **2.45 gas**.
`coal_sync_ensemble_level` (K, armed) addresses only coal. The gas half is the object that
`spp_gas_commitment_bridge` (R, SPP-44) and `commitment_floor_window_netload` (R, SPP-66) were
rejected on. This lane does not re-open them. A successor needs a measured, forward-reproducible
gas min-gen driver that neither lane had.

**(b) Marginal fuel, 2020 (reconstruction r 0.70, mean err +$0.99: inside the $1.5 gate).**
Ordinary hours (MID1 ∪ MID2):

| month | e_m | RT | mc at Q_model | mc at Q_measured | **quantity** | **level** | marginal coal / gas / CT |
|---|---:|---:|---:|---:|---:|---:|---|
| Jan | +2.99 | 15.46 | 18.90 | 19.02 | −0.12 | **+3.56** | .58/.31/.11 |
| Apr | +2.85 | 14.72 | 17.84 | 18.46 | −0.62 | +3.74 | .29/.26/.45 |
| Oct | −6.67 | 14.89 | 19.96 | 20.69 | −0.72 | +5.80 | .49/.24/.27 |
| **Nov** | **+8.17** | 15.50 | 21.96 | 23.00 | −1.03 | **+7.50** | .35/.56/.09 |
| **Dec** | +6.26 | 15.57 | 21.14 | 21.29 | −0.15 | +5.72 | .44/.52/.04 |

The model serves *less* thermal than measured (EIA-930 COL+NG), so the quantity term is ≤ 0 in
11/12 months. **Nov/Dec 2020 is "marginal mc too high", not "gas marginal where cheaper supply
was".** The stack at the measured quantity sits $4–7.5 above RT. Coal PRB is marginal in ~43 % of
ordinary hours at a band mc of ~$19 (fuel ≈ $14.3 + VOM $4.50). RT sits at ~$15. No measured SPP
input names the $4: coal delivered price is F923 plant-month already, and gas matches (c). Coal
VOM has no SPP-measured source, and the offer-level family is refused (xiso §10). **2022's
reconstruction fails the gate** (mean err +$2.92), so no 2022 (b) split is quoted.

**(c) Fuel-price input.** The model's capacity-weighted delivered gas vs EIA N3045 (converted at 1.036 MMBtu/Mcf):

| | model | KS | OK | predicted price effect ÷ e_m |
|---|---:|---:|---:|---|
| 2020 Oct | 2.30 | 2.40 | n/p | −0.8 / −6.67 = 12 % |
| 2020 Nov | 3.12 | 3.19 | n/p | −0.5 / **+8.17** (opposite sign) |
| 2022 Jun | 7.60 | 7.73 | 7.97 | −2.0 / −10.64 = 19 % |
| 2022 Jul | 6.89 | 7.23 | 7.66 | −5.2 / −13.56 = 38 % |
| 2022 Aug | 8.20 | 8.33 | 9.14 | −4.8 / −15.15 = 32 % |
| **2022 Jan** | **21.39** | 5.96 | 5.40 | the MO defect, §6 |

(Δ vs mean(KS, OK), × the HR of marginal gas in HIGH hours: 8.0 / 9.3 / 9.0.) The model's gas is
not flatter than published; it tracks it. **(c) explains no month ≥ 50 %.** Both series derive
from EIA-923 receipts, so the small gap is aggregation (plant-month vs state), not a defect.

**(d) CT overrun.** 2020 model CT_PEAKER 1,812 MW vs CAMPD 1,230 MW. The overrun sits in Jan–Jun
(+0.4 to +1.2 GW), not in the penalised months. corr(overrun, e_m) = **−0.13**. Nov and Oct, the
two largest |e_m|, both have overruns *below* the year's median. 2022 runs the other way (CT
**under** by 263 MW, corr +0.55). CT is a C1/dispatch fact, not the body's owner.

## 4. Predictions, scored

| # | prediction | outcome |
|---|---|---|
| P1 | instrument reproduces the four rows | **HIT** (+15.52 %, 0.257, 0.234, 0.208) |
| P2 | RT ≥ 300 h < 0; model < 50 h ≤ 0 (2020) | **half**: RT 936 HIT; model 391 MISS |
| P3 | (a) contributes to or owns C3a 2020 | **HIT**: OWNS (NEG∪LOW = 136 % of the gap) |
| P4 | (a) does not own C3b 2022 | **HIT** (MINOR) |
| P5 | Nov/Dec 2020 ordinary error mostly LEVEL | **HIT** (level +7.50 / +5.72; quantity −1.03 / −0.15) |
| P6 | model gas flatter in 2022 and explains ≥ 50 % of Jul–Aug; < 50 % of Oct/Nov 2020 | **MISS** on 2022 (not flatter; 38 % / 32 %); HIT on 2020 |
| P7 | CT overrun positive in Nov/Dec 2020, corr > 0 | **MISS** (+0.10 / +0.05 GW; corr −0.13) |
| P8 | C3b 2021 owned by Feb (Uri) | **HIT** (0.234 → 0.071) |
| P9 | no object admissible for C3a 2020; if any, (c) for C3b 2022 | **HIT** (none admissible) |

## 5. Verdict (PRECOMMIT §4)

| object | (i) owns / contributes | (ii) measured input the model gets wrong | (iii) not dead | admissible |
|---|---|---|---|---|
| (a) low side | OWNS C3a/C3b 2020 | thermal online in RT<0 hours: a measured *quantity*, but no measured forward driver for the gas half | coal half = armed K; gas half = R (SPP-44 / SPP-66); wind side = R/I | **no** |
| (b) ordinary level | OWNS C3a/C3b 2020 | **none found** (gas ✓, coal fuel ✓, quantity ✓) | level = offer family (xiso-refused) | **no** |
| (c) fuel price | explains < 50 % in every month | MO Jan-2022 reference: real, but moves no row | — | **no for the rows**; defect routed |
| (d) CT overrun | not in penalised months | yes (CT +47 % 2020), but no price ownership | — | **no** |
| upper tercile 2022 | OWNS C3b 2022 | none; gas marginal at HR 8–9 vs RT-implied 11–13 | offer shape (xiso §10) | **no** |

**So the rung's C3a 2020 and C3b 2020 / 2022 remain an unidentified body-level pricing error,
routed and not absorbed.** It is now localized:
1. thermal (half gas) staying online in the negative-price hours;
2. a +$4–7.5 stack level in ordinary hours with no measured driver;
3. a flat upper stack in 2022.

C3b 2021 is Uri, and it is the ledgered wedge.

## 6. The MO defect: routed, not built

- **Fact:** `data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv`,
  MO 2022-01 = **152.45 $/Mcf**. It is MO's first published month; the rest of 2022 runs 4.31–7.27;
  US = 6.41; neighbours KS 6.17, OK 5.59, NE 7.09. Across all states and 2019–2025 the next-largest
  state/US ratio is 7.4× (NH Feb 2022). Every other > 3× cell is a known regional event.
- **Mechanism:** `screen_gas_plant_month_prices` checks each plant print against the state
  reference but never checks the reference itself. A correct ~$6 MO print reads "low" (< 0.5 ×
  147) and is replaced *by* $147. The nearby pool is built from screened months, so the value
  spreads further. In the SPP rung's 2022 LP: **31 rows / 1,650 MW** carry exactly $147.15, and
  **314 rows / 5,590 MW** carry $48–147 (97 plants, mostly CT_PEAKER / ST_GAS), January only.
- **Size (first-order, served quantity held):** January price −$0.38 (78 of 744 hours move).
  C3a 2022 −4.89 → −4.96 %. **C3b 2022 0.2083 → 0.2075, still FAIL.** The effect on C1 COAL_PRB
  2022 and C2 gas 2022 needs a re-dispatch. The rows priced out are mostly peakers, so the effect
  is expected to be small; it is not estimated here.
- **Repair shape (rule 14, zero DOF):** screen the *reference* against the US series with the
  same declared (0.5, 2.0) band; fall to the US series when it fails. It is a shared seam
  (`data/fuel/plant_prices.py`). **Exposure is cross-ISO:** MISO's 2022 keeper arms both
  `gas_plant_monthly_fuel_pricing` and the screen, and carries Missouri plants. **Routed to the
  shared-data owner and the MISO lane (rule 25), not built here.**
- **Scope note:** NE 2024-01/03/11 (2.4–3.4× US) and WY 2023-01 (4.9×) sit in the keeper span and
  are *not* touched here. They are listed so a successor can check them.

## 7. Rules and state

- Rules 1/13/14: no mechanism proposed. The measured DA, EIA-930 and CAMPD series are diagnostics
  only. Rule 19/21/25: not engaged; §4 did not fire.
- Rule 28: no cell verdict changed. Evidence notes were added to SPP's `gas_plant_monthly_pricing`
  (the MO defect) and `coal_sync_ensemble_level` (the gas half of the low-side deficit), plus a
  DO-NOT-REDO block in §5.7.
- **Keeper untouched.** `audit_keepers --iso SPP` re-run at the end (see commit message).
- Every number is model-SELECTION evidence.

## 8. Cost and retrievability

0 LP minutes. No shards, no bundles, nothing to promote, archive or retain. Everything reproduces
from `main` with the three probes.
