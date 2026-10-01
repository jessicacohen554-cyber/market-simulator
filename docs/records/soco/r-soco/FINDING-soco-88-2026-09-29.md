# FINDING soco-88 — `gas_electric_power_monthly_level` on SOCO (zero LP)

**Owner ruling (end of soco-87):** "Gas-level derive, zero LP (Recommended)". No solve, no registration, keeper
unchanged (`2026-09-29-soco87-gas-hh-monthly`, NOT-YET 7/4/0/1/2).

## Conclusion — (b): the measured delivered-gas level does NOT move the failing C3a years

It moves 2019 and 2022 the **wrong way**, and 2020 by 0.9 pp against a 4.4 pp gap. It is inert in 2021 and 2025.
No status flips, C3a or C3b. SOCO's C3a misses (+14 % / +14 % / −13 %) are an order of magnitude larger than any
disagreement between the two measured gas levels (≤ 1.6 %, and 4.7 % in 2022). **Gas level is not the C3a lever.**
Matrix cell: `R` (zero-LP greedy).

## 1. Weights (data change, inert until armed)

`scripts/data/derive_iso_gas_state_weights.py` was re-run unchanged. It reproduces all 51 committed rows
byte-for-byte and adds SOCO, which `BA_CODE_TO_ISO` registered (SOCO-20) after the table was written. Only the
SOCO rows are committed. NWPP's rows (same run) are left to the NWPP lane (rule 25).

| state | gas MW (EIA-860, NG-primary, BA=SOCO) | weight |
|---|---:|---:|
| GA | 18,593.5 | 0.5117 |
| AL | 14,529.4 | 0.3999 |
| MS | 3,111.1 | 0.0856 |
| FL | 102.0 | 0.0028 |

## 2. Admissibility per year (all 12 months printed AND basket > 50 %)

N3045 coverage, identical in the committed all-state CSV and the three 2026-09-13 workbooks:

| year | GA | AL | MS | FL | basket | status |
|---|---:|---:|---:|---:|---:|---|
| 2019 | 12 | 0 | 0 | 10 | 0.512 (GA only) | admissible, by 1.2 pp |
| 2020 | 12 | 0 | 0 | 0 | 0.512 (GA only) | admissible, by 1.2 pp |
| 2021 | 3 | 0 | 0 | 2 | 0.000 | **inert** |
| 2022 | 12 | 12 | 12 | 12 | 1.000 | admissible |
| 2023 | 12 | 12 | 12 | 12 | 1.000 | admissible |
| 2024 | 12 | 12 | 12 | 12 | 1.000 | admissible |
| 2025 | 0 | 12 | 0 | 0 | 0.400 | **inert** |

The input is not year-consistent. Two years fall back to the keeper construction, and 2019–2020 price SOCO from
Georgia alone.

## 3. Interplay with the keeper gas stack (rule 19)

Keeper gas price = (`gas_price_override`_y [HH] + `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR`_y) × HH monthly shape
× HH daily shape. Code path: `resolve.py` / `trajectories._gas_series`.

| component | armed, admissible year |
|---|---|
| annual HH override | **replaced** |
| soco-72 measured basis (F923 receipts − HH) | **replaced** — N3045 is already a delivered price; no double count |
| `gas_hh_monthly_shape` | **replaced** — N3045 carries its own monthly shape |
| `gas_daily_shape` | **survives** (multiplied after, mean-preserving per month) |
| coal passthrough sigmoid reference (`_gas_series`) | moves with it (same series) |
| inadmissible year | keeper construction unchanged, byte-identical |

The level swaps one delivered-gas measurement (SOCO's own EIA-923 plant receipts) for another (the state average
across every electric-power buyer). The two agree to within 1.6 % except in 2022:

| year | keeper annual $/MMBtu | N3045 blend | Δ |
|---|---:|---:|---:|
| 2019 | 2.840 | 2.885 | +1.6 % |
| 2020 | 2.350 | 2.318 | −1.4 % |
| 2022 | 7.650 | 7.287 | −4.7 % |
| 2023 | 3.030 | 3.033 | +0.1 % |
| 2024 | 2.830 | 2.794 | −1.3 % |

## 4. Greedy result (`scripts/probes/_soco88_ep_level.py`)

`fleet_only` rebuild with the flag off and on. Same-marginal-unit re-pricing of `soco87_span/hourly/system_<y>`.
Units moved: gas and coal fuel types only (225 / 225 / 0 / 232 / 220 / 220 / 0).

| year | C3a keeper | C3a arm | C3b keeper | C3b arm | flip? |
|---|---:|---:|---:|---:|---|
| 2019 | +14.0 FAIL | +14.3 FAIL | 0.166 | 0.178 | none (wrong way) |
| 2020 | +14.4 FAIL | +13.5 FAIL | 0.177 | 0.182 | none |
| 2021 | −2.4 | −2.4 | 0.119 | 0.119 | inert |
| 2022 | −12.7 FAIL | −15.4 FAIL | 0.275 FAIL | 0.263 FAIL | none (C3a wrong way) |
| 2023 | +2.3 | +2.4 | 0.094 | 0.089 | none |
| 2024 | −3.6 | −4.3 | 0.180 | 0.153 | none |
| 2025 | −1.5 | −1.5 | 0.189 | 0.189 | inert |

C3a arm = keeper C3a scaled by the re-priced/keeper load-weighted mean ratio. Matched price-setter share is 81–94 %.
soco-87 showed this greedy under-states LP movement (it was conservative on C3b). Even doubling every move leaves all
three failing years failing, and 2019/2022 get worse.

## 5. What this rules out, and where C3a points

Every admissible gas-level measurement is within a few percent of the keeper's. A 13–14 % C3a gap therefore cannot
be a gas-price level error. The remaining candidates are not fuel-price inputs: which class and unit set the price
in the over/under-priced hours (2019–2020 over, 2022 under), and whether FERC-714 system lambda is a like-for-like
benchmark for the model's load-weighted dual in those years. Both are zero-LP questions. Neither has been run.
