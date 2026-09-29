# FINDING soco-89 — C3a price-setter census + benchmark audit (zero LP)

**Owner ruling (end of soco-88):** "Both, one lane". Zero LP. No solve, no registration, keeper unchanged
(`2026-09-29-soco87-gas-hh-monthly`, NOT-YET 7/4/0/1/2). No mechanism tested, so no matrix cell moves.

## Conclusion — (c): neither an admissible new lever nor a benchmark misalignment

1. **The benchmark is like-for-like on every axis that can be measured** (§3). Clock shifts of ±1 h move the
   load-weighted lambda by ≤ 0.4 %. There is no level break at the CSV→XBRL change (2020→2021). Weighting and units match.
2. **The C3a pattern comes from two errors that appear in every year, including the passing ones** (§2):
   - the model runs **+$1.9 to +$3.2/MWh high in the cheapest 40 % of lambda hours in all seven years**;
   - it runs **low in the top 20 % of lambda hours**, by an amount that grows with how spiky the year is
     (−$0.3 in 2019/2020, −$2 to −$4.5 in 2021/2023–2025, −$11.7 in 2022).
   2019 and 2020 fail because their lambda was flat, so nothing offsets the low-end error. 2022 fails because the
   tail error swamps it. **The four passing years pass by cancellation, not accuracy.**
3. **Every candidate lever for either error is already adjudicated** (§4): CC incremental HR (soco-85: SOCO's
   incremental HR is ≥ average above the ramp bottom; owner "Keep refused"), replacement fuel = hub commodity
   (not year-consistent), gas level (soco-88, R), SE daily gas basis (owner "Stay free-data only"), and CT start
   amortization (owner NO). A fix to only one error breaks passing years (§2.3).

## 1. Method

Probe: `scripts/probes/_soco89_price_setter_census.py`. For each year it does one `fleet_only` rebuild of the keeper
recipe (`replay_keeper.run_year_kwargs` + `derived_run_year_inputs`) to get `mc_base[g,t]`. It then reads the keeper's
committed `hourly/system_<y>.parquet` and the lambda on the bench builder's own dense CST 8760
(`derive_actual_lmp._soco`). The gap is `Σ D_zh (P_zh − λ_h) / Σ D_zh`. It reproduces the scored C3a exactly:

| year | model LW $/MWh | lambda LW $/MWh | C3a | status |
|---|---:|---:|---:|---|
| 2019 | 30.54 | 26.79 | +14.0 % | FAIL |
| 2020 | 25.02 | 21.87 | +14.4 % | FAIL |
| 2021 | 38.67 | 39.63 | −2.4 % | PASS |
| 2022 | 70.65 | 80.97 | −12.7 % | FAIL |
| 2023 | 31.64 | 30.93 | +2.3 % | PASS |
| 2024 | 29.11 | 30.20 | −3.6 % | PASS |
| 2025 | 40.21 | 40.84 | −1.5 % | PASS |

## 2. Where the gap comes from (part A)

### 2.1 By lambda quintile ($/MWh of the load-weighted mean; model − lambda)

Hours are binned by that year's lambda quintile (Q1 = cheapest 20 %).

| year | Q1 | Q2 | Q3 | Q4 | Q5 | **low 40 %** | **top 20 %** | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | +1.09 | +1.51 | +0.85 | +0.62 | −0.32 | **+2.60** | **−0.32** | +3.75 |
| 2020 | +1.10 | +0.84 | +1.01 | +0.48 | −0.28 | **+1.94** | **−0.28** | +3.15 |
| 2021 | +1.11 | +0.79 | +0.66 | −0.59 | −2.93 | **+1.90** | **−2.93** | −0.95 |
| 2022 | +1.61 | +1.60 | +0.55 | −2.37 | −11.71 | **+3.21** | **−11.71** | −10.32 |
| 2023 | +1.11 | +0.76 | +0.82 | +0.06 | −2.04 | **+1.87** | **−2.04** | +0.71 |
| 2024 | +1.25 | +0.78 | +0.61 | −0.12 | −3.60 | **+2.03** | **−3.60** | −1.09 |
| 2025 | +1.24 | +1.45 | +0.88 | +0.33 | −4.53 | **+2.69** | **−4.53** | −0.62 |

The low-end error is stable across years (+1.9 to +3.2). The top-quintile error is not, and that is what decides pass or fail.

### 2.2 Distribution (system load-weighted model price vs lambda, $/MWh)

| year | p10 model / λ | p25 | p50 | p90 | p99 |
|---|---|---|---|---|---|
| 2019 | 22.2 / 17.3 | 26.3 / 19.0 | 31.5 / 26.3 | 34.9 / 33.1 | 38.8 / 49.7 |
| 2020 | 18.7 / 12.8 | 21.6 / 17.0 | 24.2 / 18.8 | 31.1 / 29.3 | 34.5 / 43.8 |
| 2021 | 24.5 / 19.4 | 30.2 / 25.3 | 34.4 / 32.8 | 51.0 / 60.6 | 69.5 / 105.5 |
| 2022 | 42.8 / 35.1 | 49.7 / 42.0 | 62.6 / 60.8 | 104.8 / 123.6 | 120.7 / 223.1 |
| 2023 | 24.4 / 18.9 | 26.6 / 22.9 | 30.3 / 25.8 | 39.0 / 40.2 | 43.5 / 60.5 |
| 2024 | 18.8 / 13.7 | 22.7 / 20.0 | 26.4 / 23.8 | 36.6 / 39.3 | 95.3 / 86.1 |
| 2025 | 28.4 / 24.0 | 32.2 / 25.7 | 37.8 / 34.8 | 50.0 / 55.0 | 74.6 / 123.8 |

The model's p10 is $4–6 above lambda in every year. Its spread is narrower than lambda's in every year.

### 2.3 Why a one-sided fix fails (accounting illustration, not a mechanism)

This removes each error's contribution from the §2.1 total. It is not a model run.

| year | as scored | remove low-40 % error only | remove top-20 % error only | remove both |
|---|---:|---:|---:|---:|
| 2019 | +14.0 | +4.3 | +15.2 | +5.5 |
| 2020 | +14.4 | +5.5 | +15.7 | +6.8 |
| 2021 | −2.4 | −7.2 | +5.0 | +0.2 |
| 2022 | −12.7 | −16.7 | +1.7 | −2.2 |
| 2023 | +2.3 | −3.7 | +8.9 | +2.8 |
| 2024 | −3.6 | **−10.3** | +8.3 | +1.6 |
| 2025 | −1.5 | −8.1 | +9.6 | +3.0 |

A low-end-only lever passes 2019/2020, fails 2024, and makes 2022 worse. A tail-only lever passes 2022 but leaves
2019/2020 failing. Only a joint repair clears all seven years.

### 2.4 By month and hour band

2019/2020: the gap is positive in every month (+1.0 to +7.3 $/MWh) and every hour band. It is largest overnight
(2019 night 26.4 vs 21.1). 2022: the gap is −18 to −33 $/MWh in Jun–Aug and −61.5 in December (Elliott), while
Jan–Mar is +6. Full per-month tables are in the probe's JSON output.

### 2.5 Price-setting class and offers

Attribution by `mc_base` match (±$0.50) is **ambiguous**: in 2019 SOCO_GA, 2–4 classes have a unit within tolerance
in 90 % of hours. So the class split is indicative only. 2019 load-weighted setter shares: CT_PEAKER 0.32, COAL_PRB 0.23,
COAL_BIT 0.16, CC_REGULAR 0.09, ST_GAS 0.06, unmatched 0.06. In 2022, CT_PEAKER hours carry −6.40 of the −10.32 gap.

Capacity-weighted class offers (`mc_base` $/MWh / fuel $/MMBtu):

| year | CC_REGULAR | COAL_PRB | COAL_BIT | CT_PEAKER | ST_GAS |
|---|---|---|---|---|---|
| 2019 | 22.1 / 2.84 | 19.6 / 2.25 | 27.1 / 3.03 | 36.1 / 2.84 | 35.1 / 2.84 |
| 2020 | 18.6 / 2.35 | 19.6 / 2.23 | 26.3 / 2.95 | 30.5 / 2.35 | 29.7 / 2.35 |
| 2021 | 30.4 / 4.02 | 20.1 / 2.33 | 26.4 / 3.07 | 50.0 / 4.02 | 49.1 / 4.02 |
| 2022 | 56.0 / 7.65 | 23.2 / 2.89 | 31.8 / 4.81 | 91.8 / 7.65 | 89.9 / 7.65 |
| 2023 | 23.4 / 3.03 | 23.9 / 2.94 | 37.5 / 5.71 | 38.2 / 3.03 | 36.3 / 3.03 |
| 2024 | 22.0 / 2.83 | 22.5 / 2.76 | 30.4 / 4.92 | 35.9 / 2.83 | 35.0 / 2.83 |
| 2025 | 31.4 / 4.17 | 21.6 / 2.66 | 32.8 / 3.68 | 52.1 / 4.17 | 50.4 / 4.17 |

In 2019/2020, lambda's p10 (17.3 / 12.8) sits **below every fossil class offer** in the model, including PRB coal.
In 2019/2020 coal and CC offers overlap at $19–27, so small offer differences reorder the setter without moving the level.

## 3. Benchmark audit (part B)

Sources: `scripts/data/derive_actual_lmp.py::_soco`, `scripts/calibration_verdict.py::score_price_mean`, and
`data/raw/ferc-714/README.md`.

| check | finding | effect on C3a |
|---|---|---|
| Hour weighting | `rt_lw` weights lambda by the **same model demand** the model's mean uses. Like-for-like (v2.4). | none |
| Time zone / DST | Southern files 24 values every day in all 7 years, which only a fixed UTC−6 clock can produce. The bench shifts UTC→CST by −6 h, the same clock the model uses. Feb 29 is dropped on both sides. | ±1 h shift moves the LW lambda by −0.39 % to +0.10 % |
| Gaps / fills | 0 NaN, 0 missing hours in every year. No fill. | none |
| Units | $/MWh as filed, both eras. | none |
| Construction break (CSV 2019–20 → XBRL 2021–25; CPT → CST label 2023) | No break in lambda relative to the model's own fuel costs. Median λ / CC offer: 1.19, 1.01, 1.08, 1.09, 1.10, 1.08, 1.11. p10 λ / CC offer: 0.78, 0.69, 0.64, 0.63, 0.81, 0.62, 0.76. Failing and passing years interleave. | none found |
| Which fleet | Lambda is Southern Company Services' pool dispatch (Alabama, Georgia, Mississippi Power, Southern Power). The model dispatches the whole SOCO BA, which also includes MEAG, Oglethorpe, GTC and Dalton. | **not measurable** from committed data |
| Construction of lambda | Per soco-84, it is incremental HR × **replacement** fuel. The model uses average-HR tranches × delivered (F923) fuel. | the definitional difference behind §4's adjudicated levers |

No rule-14 misalignment is established. The one unmeasurable item, fleet scope, cannot be quantified without a
pool-level load or dispatch series, and none is committed or freely published.

## 4. Levers against the two errors (all already adjudicated)

| error | candidate | status |
|---|---|---|
| low-end (+$2–3, every year) | CC incremental-HR offers | soco-85: SOCO incremental ≥ average above the ramp bottom (econ_low 1.00, econ_high 1.21); greedy raised prices. Owner "Keep refused". |
| low-end | replacement fuel = hub commodity | refused, not year-consistent |
| low-end | gas level (N3045) | soco-88: R |
| low-end | out-of-merit coal counterfactual | refused, not year-consistent |
| top-quintile | SE daily gas basis (Transco/Sonat daily) | owner "Stay free-data only"; no free daily SE hub exists 2019–2025 (soco-85) |
| top-quintile | CT start / tranche_startup_amortization | owner NO |
| top-quintile | HH daily shape | armed (soco-85); HH does not carry Elliott (117.8 vs 406.8) |

The census is new evidence about **structure**. The passing years hide the same low-end error, so C3a passing there
is not evidence of skill. It is not new evidence for any refused lever, and §2.3 shows no single lever can clear C3a.

## 5. Records

- Probe: `scripts/probes/_soco89_price_setter_census.py` (`--out DIR` writes `census_<y>.json` + cached `fleet_<y>.npz`).
- Keeper unchanged; NOT-YET 7/4/0/1/2. SOCO is not frontier.
