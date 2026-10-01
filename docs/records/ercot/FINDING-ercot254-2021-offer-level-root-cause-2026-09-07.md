# FINDING — the 2021 C1/C3a root cause is ONE object: the ERCOT delivered-gas **level anchor is an annual mean of a monthly series whose February 2021 value is a 31σ outlier** (ercot-254)

> **Phase 0, zero LP** (rule 29 clause 0). Every number below is a read-only
> reconstruction of the three committed bundles
> (`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` on
> `ercot253_2021_touchpoint` / `ercot252_2022_touchpoint_repair` /
> `ercot248_two_config_keeper`) or a direct read of the committed measured input
> files. **No solve was run, no parameter was tuned, and nothing here was
> identified on a held-out year** — the object is a *construction* defect in how a
> measured series is aggregated, which is answerable from the input file alone
> (rule 22 step 3). Answers the census `docs/ADDENDUM-ercot253-c1-c3a-root-cause-2026-09-07.md`
> §4 ordered; the answer is its **candidate 1**, and the search ends there.

## 1. The object

`market_sim.data.fuel.basis.ercot.ercot_electric_power_gas_basis(year)` reduces the
monthly EIA series N3045TX3 (TX gas delivered to electric-power consumers,
`data/raw/ercot_electric_power_gas_price.csv`) to a **single annual mean**, and
`apply_ercot_zonal_gas_basis` adds the resulting scalar to **every ERCOT gas unit
in all 8,760 hours**:

```python
ep_mmbtu   = float((sub["price_usd_mcf"] / _MCF_TO_MMBTU).mean())   # ANNUAL MEAN
...
level_corr = ep_basis - GAS_BASIS_DIFFERENTIAL["ERCOT"]             # one scalar
gen_offset = level_corr + zone_spread
fuel_prices[gas_rows, :] += gen_offset[:, np.newaxis]               # ALL HOURS
```

The 2021 rows of that series:

| month | 1 | **2** | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $/Mcf | 2.90 | **61.88** | 3.06 | 3.25 | 3.42 | 3.73 | 4.49 | 4.74 | 5.56 | 6.22 | 5.84 | 9.13 |

February 2021 is Winter Storm Uri. It is **13.8× the other eleven months' median**
and **30.7 standard deviations** above their mean. An arithmetic annual mean of
twelve numbers, one of which is that, is not a measure of the typical hour's
delivered basis — it is a measure of February. The resulting flat level correction,
per year:

| year | 2019 | 2020 | **2021** | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| `level_corr` $/MMBtu | +0.282 | +0.544 | **+5.778** | +0.199 | +0.504 | +0.414 | +0.037 |
| ex-February | +0.253 | +0.570 | **+1.183** | +0.267 | +0.503 | +0.436 | −0.008 |

**2021 is 11×–150× every other year in the record, and 4.6 points of the 5.8 are
February alone.** The bundles' own solve logs confirm it fired:

```
ERCOT zonal gas basis (2021): 1824 gas units; level -0.50 -> measured EP +5.28 (corr +5.78), zonal spread -4.04..2.41
ERCOT zonal gas basis (2022): 1824 gas units; level -0.50 -> measured EP -0.30 (corr +0.20), zonal spread -1.47..0.96
ERCOT zonal gas basis (2023): 1824 gas units; level -0.50 -> measured EP +0.00 (corr +0.50), zonal spread -0.92..1.03
```

### 1a. The SAME contamination is in the second input, and it is what breaks the merit order

`data/raw/ercot_zonal_gas_hub.csv` carries one **annual** EIA-923 receipt basis per
zone-year. Its 2021 rows are contaminated the same way — and the two zones that
escape are the two that decide the CT/CC merit order:

| zone | 2019 | 2020 | **2021** | 2022 | 2023 | 2024 | basis of the 2021 value |
|---|---|---|---|---|---|---|---|
| North / Northeast | −0.07 | 0.03 | **+6.12** | 0.41 | 0.13 | 0.21 | measured annual receipts — **contaminated** |
| South_Central | −0.05 | 0.64 | **+6.30** | 0.36 | 0.56 | 0.45 | measured annual receipts — **contaminated** |
| South | 1.19 | 3.53 | **+4.36** | 1.20 | 1.23 | 0.63 | measured annual receipts — **contaminated** |
| **Houston** | −0.15 | −0.15 | **−0.15** | −0.15 | −0.15 | −0.15 | a flat cited constant, **never re-measured — escapes** |
| **West / Panhandle** | — | — | **absent** | −1.23 | −0.72 | −2.19 | **no 2021 row at all — escapes** (falls to spread 0, then the net-load step) |

The spread is capacity-weighted mean-zero, so this does not move the level — it
moves the **cross-zonal dispersion**, from a 1.95 $/MMBtu range in 2023 to
**6.45 $/MMBtu** in 2021.

## 2. What the fleet actually pays — measured on the bundles' own `fuel_prices`

Capacity-weighted p50 of each unit's hourly-median delivered gas price, from the
reconstruction of each bundle's own arrays:

| class | year | MW | hr p50 | **delivered $/MMBtu** | Henry Hub | **Δ vs hub** | mc p50 $/MWh |
|---|---|---|---|---|---|---|---|
| CC_REGULAR | 2023 | 33,120 | 7.29 | 2.459 | 2.54 | **−0.081** | 18.89 |
| CC_REGULAR | 2022 | 33,120 | 7.29 | 6.321 | 6.45 | **−0.129** | 42.88 |
| **CC_REGULAR** | **2021** | **33,120** | **7.29** | **11.050** | **3.72** | **+7.330** | **72.78** |
| ST_GAS | 2023 | 12,300 | 11.83 | 2.459 | 2.54 | −0.081 | 33.09 |
| ST_GAS | 2022 | 12,597 | 11.83 | 6.271 | 6.45 | −0.179 | 71.82 |
| **ST_GAS** | **2021** | **12,597** | **11.83** | **11.050** | **3.72** | **+7.330** | **119.17** |
| CT_PEAKER | 2023 | 8,469 | 14.82 | 2.179 | 2.54 | −0.361 | 42.01 |
| CT_PEAKER | 2022 | 8,172 | 14.59 | 5.919 | 6.45 | −0.531 | 73.61 |
| **CT_PEAKER** | **2021** | **8,172** | **14.59** | **4.780** | **3.72** | **+1.060** | **77.56** |

2022 and 2023 price the fleet within **±$0.54/MMBtu of the hub**. 2021 prices
CC_REGULAR and ST_GAS **+$7.33/MMBtu above it** — and CT_PEAKER only +$1.06.

By zone, 2021 vs 2023 (capacity-weighted delivered $/MMBtu):

| zone | CC_REGULAR 2021 | CT_PEAKER 2021 | ST_GAS 2021 | | CC 2023 | CT 2023 | ST 2023 |
|---|---|---|---|---|---|---|---|
| North | 11.050 | 11.082 | 11.050 | | 2.459 | 2.565 | 2.459 |
| Northeast | 11.050 | — | 11.050 | | 2.459 | — | 2.459 |
| South_Central | 11.230 | 11.230 | 11.230 | | 2.889 | 2.889 | 2.889 |
| South | 9.290 | 9.666 | 9.290 | | 3.559 | 4.182 | 3.559 |
| **Houston** | **4.780** | **4.936** | **4.780** | | 2.179 | 2.365 | 2.179 |
| **West** | **3.410** | 9.554 | — | | 2.036 | 8.758 | — |

The decomposition closes exactly. For any zone,
`delivered = HH + GAS_BASIS_DIFFERENTIAL(−0.50) + level_corr + zone_spread`:

| zone | 2021 predicted | 2021 measured | 2023 predicted | 2023 measured |
|---|---|---|---|---|
| North | 3.72 − 0.50 + 5.778 + 1.859 = **10.86** | 11.05 | 2.54 − 0.50 + 0.504 − 0.083 = **2.46** | 2.459 |
| Houston | 3.72 − 0.50 + 5.778 − 4.411 = **4.59** | 4.78 | 2.54 − 0.50 + 0.504 − 0.363 = **2.18** | 2.179 |
| South_Central | 3.72 − 0.50 + 5.778 + 2.039 = **11.04** | 11.23 | — | 2.889 |

(residual ≈ +0.19 in 2021 = the monthly Henry Hub shape, which the p50 hour carries).

## 3. Both load-bearing failures fall out of this one term

**C1 — the merit order.** Strip the excess at each class's own heat rate. The
counterfactual basis is a single number for every class — CC_REGULAR's own 2023
Δ of **+0.069 $/MMBtu**, i.e. `excess = delivered_2021 − (3.72 + 0.069)` — so the
same yardstick is applied to all three. For CT_PEAKER this is deliberately
conservative: its own 2023 Δ is **−0.361**, which would make its excess larger by
0.43 $/MMBtu (a further −$6.3/MWh) and widen the repaired spread, not narrow it.

| class | 2021 mc p50 | excess fuel $/MMBtu | × hr | = $/MWh | **mc without it** |
|---|---|---|---|---|---|
| CC_REGULAR | 72.78 | +7.261 | 7.29 | **+52.96** | **19.82** |
| ST_GAS | 119.17 | +7.261 | 11.83 | **+85.89** | **33.27** |
| CT_PEAKER | 77.56 | +0.991 | 14.59 | **+14.46** | **63.11** |

**The CT−CC spread goes $77.56 − $72.78 = $4.78 → $63.11 − $19.82 = $43.29**, against
$23.12 in 2023 and $30.73 in 2022. The collapsed spread that `RESULT §4` measured as
CT_PEAKER +115.5 % / ST_GAS +38.6 % / CC_REGULAR −14.0 % (−16.02 TWh) is this term
and nothing else: CC and ST_GAS sit in the contaminated zones, CT_PEAKER's capacity
is disproportionately in the two zones the contamination misses.

> **CORRECTION, added 2026-09-07 after the 2021 re-test
> (`docs/RESULT-ercot254-monthly-ep-basis-2026-09-07.md` §4).** The **price half of
> §3 is confirmed by solve** — repairing the level moves the eleven non-Uri months
> from +160.8 % to +79.1 %, every month improving. **The merit-order half is NOT.**
> Removing the level term moves CC_REGULAR by only **+0.87 TWh** of the 16 TWh miss,
> and CT_PEAKER and ST_GAS both **RISE** rather than fall, because cheaper gas
> displaces **coal** (COAL_PRB −3.65 TWh) and that energy spreads across the whole
> gas fleet. The C1 claim below therefore **overclaims**: the level term is not
> shown to be the C1 driver, and the likelier driver is the **zonal SPREAD's** own
> 2021 contamination (§1a), which the level repair does not touch. §§1, 1a, 2, 5
> and 6 stand as measured; this paragraph and the sentence closing §3 do not.

**C3a — the level.** A fleet whose CC baseload offers at $73/MWh and whose gas steam
offers at $119/MWh sets non-scarcity prices at exactly the +144.0 % `RESULT §2a`
measured across the eleven non-Uri months.

**And the sign of the February error is the same defect's other half.** The model
prices a North CC's February 2021 gas at **$12.43/MMBtu** (bundle-measured monthly
mean) when the measured TX electric-power delivered price that month was
**$59.73/MMBtu**. February's fuel cost was taken *out* of February and spread over
the year. That is why the model **undershoots Uri by 14.9 %** while overshooting
every other month by +89 % to +221 % — one term, two errors, opposite signs, both
predicted by the smearing.

## 4. What this is NOT

* **Not capacity** — settled by the addendum §1 and re-confirmed here: CC_REGULAR is
  33,120 MW / 643 units, byte-identical in all three bundles.
* **Not `gas_offer_margin_anchor_vintage`** — correctly withdrawn by the addendum §3,
  and this measurement explains why the withdrawal reasoning nonetheless read the
  wrong operand: the anchor term is `markup_hr × (anchor − fuel)` on **delivered**
  fuel, and 2021's delivered fuel is **$9.9–11.1**, not the $3.72 hub the withdrawal
  compared. 2021 *is* the most-negative year on the delivered basis. That
  compression is a **downstream consequence** of the defect in §1, not a second
  defect: it is the mechanism by which an inflated delivered price additionally
  squeezes the top of the gas stack toward the bottom. Nothing about the anchor
  needs to change.
* **Not the ST_GAS net-load drag** (addendum §4 item 4). ST_GAS is expensive in 2021
  because its delivered gas is $11.05, not because the drag floor is mis-shaped;
  strip the fuel defect and its mc p50 is **$33.27**, three dollars above 2023's
  $33.09 on a hub that is $1.18 higher. There is nothing left for the drag to explain.
* **Not the protocol-cap clamp** (`RESULT §3`) — real, still open, still worth ~31
  Uri-window hours, and still not the C3a cause.

## 5. Two provenance defects found in passing (reported, not fixed here)

1. **`meta.json` misreports these two gates.** All three bundles record
   `ercot_zonal_gas_basis: false` and `ercot_west_netload_gas_shape: false` at top
   level, while their `run_config.json` — and their solve logs — record both **true**.
   The flags reach the solve through the generic `prb_overrides` channel;
   `run_calibration_full.py:6332` writes `first_year_cfg.<field>`, which is the
   pre-override dataclass value. Consequence: `replay_keeper._ENV_GATED_INERT`'s
   hard-fail ("bundle armed the env-gated probe … re-run with the original env var")
   reads the top-level key, so it **cannot fire for any ERCOT bundle that armed the
   mechanism this way** — the guard is blind exactly where it was written to bite.
2. **The 2021 West/Panhandle `neg_day_freq` is absent**, so the West net-load step
   falls back to `_WEST_GAS_COLLAPSE_FREQ_DEFAULT = 0.42`, a **2024** measurement, and
   the resulting 2021 regimes are **inverted** — the log reads
   `firm $3.41, deep $7.45`, i.e. the "collapse" regime priced $4.04 *above* the firm
   regime, on 42 % of hours. A mechanism whose two regimes come out the wrong way
   round is not measuring what it claims. Also 2021-only; named, not fixed here.

## 6. The repair this points to, and where it must be identified

The defect is a **resolution mismatch**, not a missing input: the model's underlying
gas price is already monthly (it tracks measured monthly Henry Hub — a North CC's
2023 delivered price runs 3.06 → 2.16 → 2.61 across the year), and the basis added
on top of it is an annual scalar. The correct construction uses the **same measured
series at its native monthly resolution**:

```
ep_basis[m] = EP[m] / 1.036 − HH[m]        applied month by month
```

Zero new data, zero free parameters, same source, and identical forward behaviour
(a forecast year has no EP rows, so both forms return `None` and both degrade to the
mean-zero spread). It is **more accurate use of data already on disk**, which
rule 14 `[R-ACCURATE]` requires and rule 13 `[R-MEASURED]` admits — a monthly basis
regenerates for a forward year from forward drivers exactly as the annual one does.

**Identification stays in-sample.** Nothing above was identified on 2021: the choice
between "annual mean" and "monthly" is settled by the input file's own within-year
distribution, and the repair carries no value to fit. Its own footprint in the
training window, measured **before any solve** so it cannot be chosen on a residual:

| screen candidate | hour-weighted mean \|monthly − annual\| $/MMBtu | = $/MWh at CC hr 7.29 | max month \|Δ\| |
|---|---|---|---|
| 2023 | 0.1243 | 0.906 | 0.351 |
| 2024 | 0.2064 | 1.505 | 0.848 |
| **2025** | **0.2412** | **1.759** | 0.615 |
| *(2021, for scale)* | *8.183* | *59.7* | *49.098* |

**The rule 29 screen year is 2025** — the training year in which this mechanism's own
measured footprint is largest. It is named here, ex ante, on the mechanism's
footprint and never on a residual.

## 7. Governance

Zero-LP, read-only. No registered number changes, no bundle was written, no
dashboard entry moves, and ERCOT's determination is untouched (train-tier
CALIBRATED; rule 30(c)). The 2021 rung stays NOT-YET and stays a rule-22
model-selection observation, never a skill number. The repair, its screen and its
gates are pre-registered separately in
`docs/PRECOMMIT-ercot254-monthly-ep-basis-2026-09-07.md` before any solve.
