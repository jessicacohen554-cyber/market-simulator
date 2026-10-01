# FINDING — soco-85: CC incremental HR does not explain the off-peak λ gap; no free Southeast daily gas

Lane soco-85, 2026-09-28. **Zero LP.** Nothing built, nothing armed, no artifact committed. Keeper unchanged:
`2026-09-28-soco83-st-oom-floor` (`results/calibration/soco83_span`), NOT-YET.

Owner rulings implemented (soco-84 cards): **"Zero-LP census first"** (CC incremental HR) and **"Data scout, zero
LP"** (daily gas). Probe: `scripts/probes/_soco85_cc_incremental.py` (`derive`, `greedy --basis/--arm`). Scratch
outputs only (session scratchpad); none committed.

## 1. Headline

| question | answer |
|---|---|
| Is SOCO's CC incremental HR ~0.88 × average, as soco-84 inferred? | **No.** Across the econ range it is **≥ average**: econ_low 1.00, econ_high 1.21, linear econ slope 1.11 (pooled; every year 2019–2025 within ±0.05). |
| Is a CC-only incremental offer coherent (SOCO-63/64)? | **Yes on the frozen construction** (the committed block keeps the no-load), **no below the ramp bottom** (x = 0 is 0.81, and that is where the 29–32 % no-load share lives — the CT failure mode). |
| Does it close C3a? | **No, it moves the wrong way.** Every form raises the load-weighted price (+$0.17 to +$2.37/MWh). 2019/2020 get worse; 2022 improves but still fails. **Zero C3a status flips.** |
| Free daily Southeast gas hub 2019–2025? | **None.** Henry Hub daily is the only free daily series (already committed). Transco Z4/Z5, Sonat, FGT Z3 daily are NGI/Platts paywalled. |
| What does fit the off-peak gap? | The **fuel-cost basis**: model CC gas (EIA-923 delivered) runs 1.03–1.29 × Henry Hub; λ's low-load quintile implies gas at 0.74–0.90 × the model's. Southern's λ uses *replacement* fuel cost. Not built; routed as a card. |

## 2. Census — SOCO CC incremental / average HR (frozen `derive_campd_marginal_hr` construction)

- Scope: SOCO's own CC units (rule 25), only plants the CC derive flags `ok` (steam turbine in the meter): 16 plants,
  53 units, 724 TWh gross 2019–2025. McWilliams 533 and Wansley 7946 are excluded (`steam_not_metered`).
- Normalized to each unit's own measured average (`hr_gross`, the base the model's CC rates carry). Cap-weighted p50
  [p25, p75].

| basis | x (load position) | ratio to average |
|---|---|---|
| marg_committed | 0.0 (LSL) | 0.81 [0.73, 0.84] |
| **marg_econ_low** (frozen econlo point) | 0.5 | **1.00** [0.91, 1.05] |
| **marg_econ_high** (frozen econhi point) | 0.9 | **1.21** [1.06, 1.22] |
| linear slope, econ range (soco-75 check) | 0.2–1.0 | 1.11 [0.96, 1.16] |
| no-load share of full-load heat | P = 0 | 0.32 [0.26, 0.35] |
| LSL / HSL | — | 0.60 |

Per year the econ_low p50 runs 0.98–1.03 and econ_high 1.16–1.21. The CC input-output curve is **convex** (duct
firing at the top), so incremental rises through average mid-ramp. Only the ramp bottom is below average, and that
is the committed block, which is the no-load carrier.

**The model today**: every SOCO CC tranche (committed 9.0 GW, econlo 4.3, econhi 4.3, peak 1.1 GW in 2023) carries
**one flat HR (7.16) and one mc**. The soco-84 setter share is therefore the whole plant at average, not a specific
band.

## 3. Greedy reach (SOCO-63 §4 instrument, baseline-differenced, prices re-scored through the verdict)

Restack set: dispatchable thermal bands from the committed `class_band_hourly` (`mustrun` held); tranches from a
`fleet_only` rebuild on the soco83 recipe. Copper-plate, no floors: a first-order screen, not a solve.

C3a (±10 %) keeper → arm:

| arm | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Δprice lw $/MWh |
|---|---|---|---|---|---|---|---|---|
| **frozen** (econlo ×1.00, econhi ×1.21) | +14.0→**+15.4** | +15.6→**+17.3** | −6.1→−2.9 | −16.1→**−13.2** | +1.8→+3.7 | −4.4→−2.4 | −1.9→+0.4 | +0.36…+2.37 |
| linear slope (both ×1.11) | →+14.9 | →+16.6 | →−3.9 | →−13.7 | →+2.8 | →−3.0 | →−0.2 | +0.21…+1.91 |
| integrated ramp (sensitivity, not frozen) | →+14.7 | →+16.4 | →−4.5 | →−14.6 | →+2.6 | →−3.4 | →−0.8 | +0.17…+1.19 |
| + committed at x = 0 (incoherent bound) | →+15.4 | →+17.3 | →−3.0 | →−13.4 | →+3.7 | →−2.4 | →+0.2 | +0.35…+2.21 |

- The committed-block variant barely differs: at every load the fleet's committed blocks are inframarginal, so the
  marginal MW is on the econ ramp.
- C3b: 2019 0.179→0.194, 2020 0.226→0.239; others within ±0.01. No C3b status flips.
- **C1 (frozen arm): no status moves.** CC_REGULAR share error shrinks every year (2021 +2.7 → +1.6 pp; 2023
  +1.9 → +1.4; 2024 +1.9 → +1.3); COAL_PRB rises 0.3–1.2 TWh; CT/ST unchanged; 2019 COAL_BIT stays −4.1 pp (ledgered).

## 4. Daily gas scout

| source | free | daily | 2019–25 | SE hub |
|---|---|---|---|---|
| EIA Henry Hub RNGWHHD (committed `henry_hub_daily.csv`) | yes | yes | yes | no (national) |
| EIA wholesale ICE gas files | yes | yes | **no, stop at 2017** | no |
| EIA NG Weekly / "Select spot prices" | yes | yes | yes | no SE row (SOCO-12) |
| FERC Form 552 / CFTC | yes | no | — | — |
| Pipeline EBBs (Transco 1Line, SNG DART, FGT) | yes | no prices (FGT: monthly cash-out, Platts-derived) | — | — |
| NGI Daily GPI / Platts Gas Daily / ICE EOD | **paywalled** | yes | yes | Transco Z4/Z5, Sonat, FGT Z3 |

**Cold-snap windows** (load-weighted $/MWh; HH factor = daily ÷ month mean):

| window | h | λ | model | HH factor | model × HH factor (bound) | share of annual gap |
|---|---:|---:|---:|---:|---:|---:|
| Uri 2021-02-14..19 | 144 | 85.3 | 39.6 | 2.00 | 84.8 | −0.87 |
| Elliott 2022-12-23..26 | 96 | **406.8** (max 1,657) | 92.6 | 1.27 | 117.8 | **−4.52** |
| Jan 2024-01-14..17 | 96 | 133.4 | 36.2 | 2.02 | 63.2 | −1.28 |
| Jan 2025-01-20..23 | 96 | 183.8 | 56.0 | 1.20 | 66.3 | −1.96 |

Henry Hub carries Uri and half of Jan 2024. It does not carry Elliott or Jan 2025: that is the Southeast basis
blowout, which only a paywalled index records.

**Greedy of the existing `gas_daily_shape` mechanism** (Henry Hub within-month shape on the monthly F923 level,
mean-preserving; default off; SOCO cell U): C3a 2021 −6.1 → −4.8, 2022 −16.1 → −15.7, 2024 −4.4 → −4.9, others
±0.2 pp; no status flips. The LP response to a price spike is typically larger than this greedy's.

**Rule 13.** Daily spot gas is a measured input that regenerates for a forecast year (a forward monthly level × a
representative daily shape — `gas_daily_shape_factors`' own docstring). It is admissible. For SOCO it would enter
through that existing seam: no new field, no new DOF. A Southeast daily basis would need a licensed source and could
not be committed (`docs/data-licensing.md` §5).

## 5. What the off-peak gap does fit (measured, not built)

| year | model CC gas $/MMBtu | HH | model/HH | λ q1 median | gas implied at model CC HR 7.06 + vom $2.00 | implied/model |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 2.84 | 2.56 | 1.11 | 18.48 | 2.33 | 0.82 |
| 2020 | 2.35 | 2.03 | 1.16 | 14.65 | 1.79 | 0.76 |
| 2021 | 4.02 | 3.89 | 1.03 | 23.03 | 2.98 | 0.74 |
| 2022 | 7.65 | 6.45 | 1.19 | 43.14 | 5.82 | 0.76 |
| 2023 | 3.03 | 2.53 | 1.20 | 21.33 | 2.73 | 0.90 |
| 2024 | 2.83 | 2.19 | 1.29 | 18.30 | 2.31 | 0.82 |
| 2025 | 4.17 | 3.52 | 1.18 | 25.13 | 3.28 | 0.79 |

- The model prices CC fuel at EIA-923 **delivered** cost. Southern's Sch. 6 formula uses **replacement** fuel cost
  (FINDING-soco-82 §3). Delivered cost carries fixed firm-transport reservation charges that are not incremental.
- This is a **structural** candidate (rule 1), not a fitted one, and it needs a measured, admissible replacement
  basis. A zero-LP census of EIA-923 receipts split by purchase/contract type is the next step. Not built.
- Caveat: the implied-gas column assumes CC is marginal at q1 at its average HR. Where coal is marginal, the
  inference does not hold.

## 6. Retrievability

No solve, no bundle. The probe and this doc land on `main` with the lane PR.

## 7. Addendum — fuel-basis census (owner ruling "Zero-LP fuel-basis census", same session)

**Data.** EIA-923 Page 5 (Fuel Receipts and Costs) 2019–2024, `FUEL_GROUP == "Natural Gas"`, `Balancing Authority
Code == "SOCO"`, fetched keyless to scratch (`f923_<Y>.zip`, EIA archive). Not committed. MMBtu-weighted
`FUEL_COST` vs the Henry Hub monthly mean of the same months:

| year | contract share | contract ×HH | spot ×HH | all ×HH |
|---|---:|---:|---:|---:|
| 2019 | 0.17 | 1.04 | 1.14 | 1.12 |
| 2020 | 0.19 | 0.96 | 1.21 | 1.16 |
| 2021 | 0.21 | 1.03 | 1.09 | 1.08 |
| 2022 | 0.31 | 1.22 | 1.13 | 1.16 |
| 2023 | 0.30 | 1.20 | 1.25 | 1.23 |
| 2024 | 0.26 | 1.23 | 1.30 | 1.28 |

- 100 % of SOCO gas receipts are **firm** supply and **firm** delivery. **Spot is not cheaper than contract**, so
  EIA-923 cannot supply a measured "replacement cost" below delivered cost. The premium over Henry Hub is transport
  plus Southeast basis, and public data does not split the two.

**Upper-bound greedy — every gas unit at the Henry Hub monthly mean** (`--arm hub`; not a candidate mechanism):

| year | C3a keeper → bound | C3b keeper → bound | Δprice lw |
|---|---|---|---:|
| 2019 | +14.0 → **+7.2** | 0.179 → 0.119 | −1.84 |
| 2020 | +15.6 → **+3.7** | 0.226 → **0.105** | −2.63 |
| 2021 | −6.1 → −5.8 | 0.261 → **0.120** | +0.32 |
| 2022 | −16.1 → **−25.1** | 0.391 → 0.361 | −6.89 |
| 2023 | +1.8 → **−10.9** | 0.153 → 0.142 | −3.94 |
| 2024 | −4.4 → **−18.8** | 0.271 → 0.241 | −4.24 |
| 2025 | −1.9 → **−13.4** | 0.171 → 0.205 | −4.76 |

C1: 2019 CT_PEAKER flips PASS → FAIL (+3.0 pp) and 2019 COAL_BIT worsens (−4.1 → −4.7 pp).

**Verdict.** The hub reading fixes 2019–2020 and breaks 2022–2025. It is **not year-consistent**, the same signature
as soco-84's coal-conduct counterfactual. The off-peak premium is not a single fuel-basis object. **No build is
recommended.** The remaining explanation that is consistent across years is λ's own construction (incremental cost
at the unit's actual loading, plus Southern's coal conduct), which public data does not identify further.
