# FINDING — miso-300: lag-aware pooled MISO gas variable transport (one `v` per plant, seven receipt years, the print's lag as a regressor) — phase 0, zero LP

```
LANE    : miso-300 (owner ruling 2026-10-02, miso-299 decision card "What should miso-300 do?": "Lag-aware pooled estimator (phase 0)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), legs at 8f765fef — unchanged
LP      : none in this document. Fleet-only rebuilds (miso-297 census machinery) cleared at the keeper's own P1 thermal quantity
STATUS  : §0 committed at b3b56fde BEFORE any lag-aware table or census number existed (placeholders below it); §§1–4 filled afterwards
VERDICT : FINDING ONLY — §0 (a) FAILS in 2022 (+$0.065 vs the print), (b) holds, (c) FAILS on the cross-check (r 0.71 vs 0.90). No PRECOMMIT, no shard. Keeper unchanged.
CELLS   : gas_marginal_commodity_pricing R, gas_variable_transport R — both STAY R (evidence added; the full-span test is not re-run)
PROBES  : scripts/data/derive_miso_gas_variable_transport_lagaware.py -> data/raw/reference/miso_gas_variable_transport_lagaware.csv (+ .pool.csv),
          results/phase0/miso/_miso300_lagaware_table.json; scripts/probes/_miso300_lagaware_census.py -> results/phase0/miso/_miso300_lagaware_census.json
```

## 0. Pre-stated reading (fixed before any number)

**The ruling.** Owner, 2026-10-02 (miso-299 card *"What should miso-300 do?"*): **"Lag-aware pooled estimator (phase 0)"** — re-fit one
`v` per plant on all seven receipt years with the month's hub change as a regressor (the −0.69 lag slope the frozen derive measured
becomes a term, not a contaminant). An estimator change on a frozen derive is admissible only under an owner ruling (rule 23 admits
source-data updates alone); this card is that ruling. Zero LP; pre-stated reading first; shards only if it clears.

**The object.** The frozen table `data/raw/reference/miso_gas_variable_transport.csv` fits `print − hub = v[p] + F[p]/burn` on the
2023–2025 receipts pooled. miso-298 solved the ruled gas form with it over 2019–2025 and was killed by K-1 (the table's level sits above
the 2019–2022 print-over-hub wedge, so the form RAISED CC_REGULAR fuel there). miso-299 showed a per-year re-fit fails because the
single-year intercept absorbs the print's lag on the year's hub trajectory (monthly CC wedge vs Δhub r = −0.54 to −0.85). The lag-aware
estimator removes that term explicitly, so one pooled `v` per plant can be identified on all seven years at once.

**The estimator, declared now and never swept.**

```
wedge[p,m] = v[p] + F[p] / burn[p,m] + λ · Δhub[p,m]          burn-weighted WLS, receipt years 2019–2025 pooled
Δhub[p,m]  = hub_m − hub_{m−1}  on the plant's own hub kind (Chicago flow-day staircase monthly mean for the Chicago and MidCon
             zones, Henry Hub trade-day for MISO-South; `_hub_month_means` of the frozen derive). January takes the prior year's
             December from the prior year's staircase (both daily series carry 2018, so January 2019 is in the panel).
```

* **λ is ONE fleet-wide coefficient.** The lag is a reporting convention of the EIA-923 monthly print (an average over the month's
  takes, lagging the hub), common to the fleet; it is not a plant or class attribute. Per-class λ values are REPORTED as a diagnostic
  and used for nothing. Never per plant.
* **Two steps, both burn-weighted.** Step 1 estimates λ jointly with every plant's own `v[p]` and `F[p]` on the pooled panel (every
  gas plant with ≥ 3 admissible plant-months; a plant with fewer is fitted exactly by its own two terms and carries no information on λ).
  Step 2 forms the lag-cleaned wedge `wedge − λ·Δhub` and runs the FROZEN derive's own machinery on it unchanged: `_fit` (WLS on `1/burn`,
  weight = burn), the own-rung bars `MIN_MONTHS 12` and `MIN_BURN_SPREAD 2.0`, and the ladder own → zone|group → group → MISO-wide.
  So `v` is exactly the frozen estimator applied to a wedge with the lag term removed, and nothing else changes.
* **The offer is still `hub + v[p]`.** λ never enters the offer; it only cleans the identification. Rule 13: `v` stays a contractual
  attribute of the delivery path; the forward analogue is `v` carried forward and re-identified by this same formula on each new
  EIA-923 vintage. The frozen table is NEVER overwritten: the output is the companion `miso_gas_variable_transport_lagaware.csv`
  (+ `.pool.csv`) in the frozen table's exact format, read by the unchanged consumer `_load_miso_gas_variable_transport`.
* **Admissible months** are the frozen derive's (`quantity > 0`, `price_per_mmbtu > 0`, Natural Gas, a hub mean for that month).

**The reading, stated now.** PROCEED to a PRECOMMIT + 7 shards only if ALL THREE hold; otherwise FINDING only, both R cells stay R,
no field, no shard, and the owner gets a decision card with the measured numbers.

- **(a) Early years reversed.** The lag-aware table moves static fleet cap-weighted **CC_REGULAR fuel DOWN in each of 2019, 2020,
  2021 and 2022** against the keeper print (Δ < −$0.005/MMBtu, i.e. beyond the census identity tolerance), the miso-298 kill mechanism
  reversed.
- **(b) Training-tier gain kept.** It still moves CC_REGULAR fuel **DOWN in 2023 and in 2024** against the print (Δ < −$0.005/MMBtu),
  the direction the miso-298 K-4 gain came from. 2025 is reported, not gated (the IMM share is not published for it and K-4 did not
  gate it).
- **(c) Identification holds**, both halves:
  - the fitted fleet-wide λ has the measured sign and magnitude class: **−1.0 ≤ λ ≤ −0.4** (a one-month lagged average implies −1,
    a hub-tracking marginal cost implies 0; the frozen derive measured the month-over-month slope at −0.69 fleet-wide, −0.76 CC_REGULAR);
  - the regression-free cross-check agrees with `v` at **Pearson r ≥ 0.90** across own-rung plants (the frozen derive's two estimators
    agreed at 0.975). The cross-check is the plant's burn-weighted wedge over its top burn quartile **restricted to flat-hub months**:
    months whose |Δhub| is at or below the median |Δhub| of the whole pooled panel (one threshold for every plant, fixed by the data,
    not chosen), top quartile taken within those months. In a flat-hub month the lag term is ~0 by construction, so the cross-check
    sees `v` plus the plant's own residual fixed leg, exactly as the frozen check did.

Reported at full magnitude either way, per year: own-plant coverage (plants, capacity share, by class), `v` cap-weighted on CC_REGULAR /
CT_PEAKER / ST_GAS / all gas (table-weighted and fleet-weighted), λ fleet-wide with its standard error and the per-class diagnostic
values, the cross-check r, the static CC_REGULAR fuel move against the print and against the frozen table, static dispatch (coal /
CC_REGULAR / all gas / seam, mean GW), static q1–q2 and all-hours load-weighted price error, and the bid-stack coal marginal share (all
hours, quintile 1). Nothing is selected on any of these.

**If it proceeds (declared now).** A ScenarioConfig field `miso_gas_variable_transport_lagaware` (default off, MISO-gated, requires
`miso_gas_marginal_commodity_pricing` + `miso_gas_variable_transport`; registered in `_CACHE_KEY_OPTIONAL_FIELDS` in the same commit;
a row in `mechanism-matrix.js` and a cell in every shard, rule 28; forward analogue = this table carried forward) selecting the
lag-aware table in place of the frozen one. A PRECOMMIT in the miso-298 form (K-1 no C1 PASS→FAIL; K-2 COAL_*/CC_REGULAR in band or toward
actual; K-4 q1–q2 error shrinks in 2023/2024 AND does not grow in 2019/2020), pinned before any shard; seven shards (2022 first).

**Structural note (rules 1 / 13 / 14).** One `v` per plant across every scored year is the object the frozen derive's docstring names
and the one this estimator keeps; the change is to the identification, not to the object. The number is whatever the receipts say with
the reporting lag taken out; zero chosen scalars. The tension miso-299 recorded (a per-year value is a per-year fit) does not arise here.

## 1. Derive provenance (`_miso300_lagaware_table.json`)

- **Source.** `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` (EIA-923 plant × month gas receipts, 2018–2026 on disk;
  2019–2025 used, 2026 partial and excluded) against the same daily hub staircases the applier prices from (Chicago Citygate flow-day;
  Henry Hub trade-day for MISO-South). Both daily series carry 2018, so January 2019's hub change uses December 2018: **0 rows dropped**
  for a missing Δhub. Panel: **8,446 plant-months, 103 plants**, 2019–2025. The commit (`4ccb8e6b`) cites the ruling and the source
  years (rule 23).
- **The script** `scripts/data/derive_miso_gas_variable_transport_lagaware.py` imports `build_panel`, `_fit`, `_hub_month_means`,
  `_top_quartile`, `MIN_MONTHS`, `MIN_BURN_SPREAD` from the frozen derive; its ladder body mirrors the frozen `derive` line for line on
  the lag-cleaned wedge. Output: `data/raw/reference/miso_gas_variable_transport_lagaware.csv` + `.pool.csv`, the frozen table's exact
  column set and header form; the frozen table is untouched (the script refuses `--out` = the frozen path).
- **Flat-hub threshold** (the cross-check's one data-fixed scalar): median |Δhub| over the pooled panel = **$0.280/MMBtu**; exactly half the
  plant-months are flat; the median plant has 41 flat months, so its flat top quartile is ~11 months.

## 2. The lag-aware table

| | fleet-wide λ | se | rows / plants | per-class λ (diagnostic only) |
|---|---:|---:|---:|---|
| step 1, 2019–2025 pooled | **−0.420** | 0.009 | 8,446 / 103 | CC_REGULAR −0.377 (se 0.014) · CT_PEAKER −0.572 (0.010) · ST_GAS −0.415 (0.060) |
| same spec, 2023–2025 only (reported) | −0.188 | 0.013 | | |
| first-difference slope d(wedge)/d(hub), the frozen docstring's statistic (reported) | 2019–2025: −0.72 fleet / −0.71 CC (burn-wtd); 2023–2025: −0.56 / −0.46 | | | |

| table | plants / own | own cap share | `v` CC_REGULAR | `v` CT_PEAKER | `v` ST_GAS | `v` all gas | MISO-wide pool |
|---|---:|---:|---:|---:|---:|---:|---:|
| frozen 2023–25 | 102 / 98 | — | 0.209 | 1.441 | 1.288 | 0.744 | 0.504 |
| **lag-aware 2019–25** | **103 / 101** | 0.99 | **0.200** | **0.911** | **1.657** | **0.624** | 0.366 |
| seven-year panel, λ = 0 (diagnostic: the frozen estimator on the same rows) | own-plant cap-wtd | | 0.157 | 0.810 | 1.628 | 0.551 | |

(`v` nameplate-weighted over the table's plants; the λ = 0 row over the 98 plants own-rung in both tables.)

**Cross-check (§0 (c), second half).** Pearson r between `v` and the plant's top-burn-quartile raw wedge in flat-hub months, across the
101 own-rung plants: **0.706** (CC_REGULAR 0.848 on 37 plants, CT_PEAKER 0.794 on 50, ST_GAS 0.981 on 10); the flat top-quartile wedge
sits +$0.099/MMBtu cap-weighted above `v`. The all-months top quartile (the frozen derive's own check, NOT the one declared here) reads
0.905 on the raw wedge and 0.911 on the lag-cleaned wedge. The declared check fails on peakers whose burn in flat months is too small to
amortize the fixed leg (Raccoon Creek: `v` 6.77, flat top-quartile 16.25; R M Heskett 5.23 / 1.51) — halving the months leaves the
top quartile of a peaker's flat months with almost no burn in it.

**What moved against the frozen table, and why (diagnostic).** On the 98 plants own-rung in both tables the lag-aware `v` agrees with the
frozen `v` at only **r = 0.579** (cap-weighted mean −$0.123/MMBtu) — but it agrees with the SAME seven-year panel fitted at λ = 0 at
**r = 0.997**. The change against the frozen table is the year set (seven receipt years instead of three), not the lag term; λ itself
shifts the own-plant CC_REGULAR `v` from 0.157 to 0.200 and CT_PEAKER from 0.810 to 0.905. The lag-aware CC_REGULAR level therefore
lands within $0.01 of the frozen table's (0.200 vs 0.209) on the table's own weights.

## 3. Census per year (zero LP; `_miso300_lagaware_census.json`; FLEET capacity-weighted, every leg at the keeper's own P1 thermal quantity)

### 3.1 CC_REGULAR fuel ($/MMBtu). Identity: non-gas rows byte-identical across legs every year; the bare hub agrees between the two joint legs to ≤ $0.01 (CC_REGULAR 0.000; the gas-price floor binds on a few negative-`v` peaker rows)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| keeper print | 2.686 | 2.238 | 4.529 | 6.670 | 2.920 | 2.606 | 3.674 |
| bare hub | 2.449 | 1.950 | 4.334 | 6.552 | 2.426 | 2.217 | 3.385 |
| print-over-hub wedge | 0.237 | 0.288 | 0.195 | 0.118 | 0.494 | 0.389 | 0.289 |
| ruled form, frozen table (`v`) | 2.796 (0.347) | 2.306 (0.356) | 4.616 (0.282) | 6.809 (0.257) | 2.675 (0.248) | 2.477 (0.260) | 3.626 (0.240) |
| ruled form, lag-aware table (`v`) | 2.678 (0.229) | 2.183 (0.233) | 4.513 (0.179) | 6.735 (0.183) | 2.599 (0.173) | 2.412 (0.195) | 3.573 (0.187) |
| **Δ lag-aware − print** (§0 (a) 2019–22, (b) 2023–24) | **−0.008** | **−0.055** | **−0.016** | **+0.065** | **−0.321** | **−0.194** | −0.101 |
| Δ lag-aware − frozen | −0.118 | −0.123 | −0.103 | −0.074 | −0.076 | −0.065 | −0.053 |

Other classes, Δ lag-aware − print: CT_PEAKER +0.06 / +0.11 / −0.06 / +0.02 / −0.13 / +0.02 / +0.12; ST_GAS +0.64 / +0.34 / +0.04 / +0.67 /
+0.07 / +0.08 / +0.36; all gas +0.14 / +0.08 / −0.01 / +0.15 / −0.20 / −0.08 / +0.05. Fleet cap-weighted `v`: CT_PEAKER 0.83–0.87 (frozen
1.26–1.33), ST_GAS 0.54–1.17 (frozen 0.55–1.03). Coverage: own-plant 72.4 % of gas capacity (frozen 72.1 %), CC_REGULAR 89.2 % in both.

### 3.2 Static census and dispatch (P1 bid stack; mean GW; coal marginal share all hours / quintile 1; legs keeper · frozen · lag-aware)

| year (IMM coal SMP share) | coal share all / q1 | coal | CC_REGULAR | all gas | seam |
|---|---|---:|---:|---:|---:|
| 2019 (0.47) | 0.432 / 0.158 · 0.462 / 0.197 · 0.437 / 0.186 | 29.08 · 29.45 · 29.07 | 11.78 · 11.32 · 11.85 | 17.03 · 16.48 · 17.01 | 16.84 · 17.03 · 16.88 |
| 2020 (0.40) | 0.254 / 0.075 · 0.275 / 0.080 · 0.252 / 0.058 | 23.49 · 23.71 · 23.45 | 11.71 · 11.31 · 11.87 | 17.12 · 16.72 · 17.20 | 17.64 · 17.83 · 17.61 |
| 2021 (0.35) | 0.371 / 0.382 · 0.384 / 0.415 · 0.384 / 0.389 | 31.63 · 31.88 · 31.62 | 9.02 · 8.75 · 9.14 | 13.48 · 13.16 · 13.49 | 14.10 · 14.17 · 14.11 |
| 2022 (0.24) | 0.177 / 0.320 · 0.161 / 0.291 · 0.167 / 0.304 | 34.03 · 34.10 · 34.04 | 8.53 · 8.38 · 8.54 | 12.75 · 12.54 · 12.69 | 11.07 · 11.21 · 11.12 |
| 2023 (0.36) | 0.215 / 0.109 · 0.221 / 0.101 · 0.227 / 0.093 | 20.90 · 20.75 · 20.64 | 16.38 · 16.86 · 17.08 | 22.84 · 23.23 · 23.53 | 13.89 · 13.65 · 13.46 |
| 2024 (0.36) | 0.197 / 0.072 · 0.204 / 0.084 · 0.196 / 0.071 | 20.03 · 20.01 · 19.96 | 17.01 · 17.06 · 17.25 | 24.21 · 24.30 · 24.49 | 12.51 · 12.44 · 12.30 |
| 2025 (n/a) | 0.277 / 0.221 · 0.282 / 0.251 · 0.293 / 0.247 | 24.52 · 24.54 · 24.40 | 15.49 · 15.49 · 15.59 | 21.45 · 21.43 · 21.64 | 11.90 · 11.91 · 11.84 |

### 3.3 Static price (bid stack vs the zone-resolved actual, load-weighted; startup markup at the q1–q2 margin 0.00 in every leg and year)

| $/MWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| q1–q2 LW error: keeper → frozen → lag-aware | +2.87 → +3.41 → +3.01 | +3.33 → +3.81 → **+3.25** | −0.48 → −0.13 → −0.47 | −1.72 → −0.54 → −0.97 | +4.82 → +4.06 → **+3.51** | +3.56 → +3.17 → **+2.63** | +3.19 → +3.18 → **+2.75** |
| all-hours LW error | +1.38 → +1.84 → +1.46 | +1.80 → +2.24 → +1.69 | −4.77 → −4.36 → −4.74 | −12.43 → −11.62 → −12.08 | +1.69 → +1.22 → +0.83 | +0.56 → +0.45 → +0.14 | −2.74 → −2.60 → −2.88 |
| q1 / q2 median, lag-aware leg (actual) | 22.7 / 25.1 (19.2 / 21.2) | 18.1 / 20.9 (15.1 / 17.1) | 27.5 / 29.9 (23.3 / 25.8) | 41.5 / 46.3 (40.2 / 48.4) | 23.8 / 27.0 (19.6 / 23.1) | 20.2 / 24.2 (16.9 / 20.4) | 30.1 / 33.2 (24.2 / 27.7) |

## 4. Reading against §0, and what happens next

**§0 (a) FAILS in 2022:** the lag-aware table moves static CC_REGULAR fuel down in 2019, 2020 and 2021 (−0.008 / −0.055 / −0.016 $/MMBtu
against the print) but **UP by +0.065 in 2022**. **§0 (b) HOLDS:** −0.321 in 2023, −0.194 in 2024 (2025 −0.101, reported). **§0 (c)
FAILS on its second half:** λ = −0.420 is inside the declared −1.0 … −0.4 band (at its edge), but the declared flat-hub cross-check
agrees with `v` at r = 0.706 against the 0.90 bar. **The lane does not proceed.** No PRECOMMIT, no shard, no ScenarioConfig field;
both R cells stay R with this evidence; the keeper is unchanged.

**What the table is, structurally.** The lag term is real and has the measured sign, but it is small in the level specification
(−0.42; the frozen docstring's −0.69 is a first-difference slope, which this panel reproduces at −0.72) and it barely re-ranks plants
(r = 0.997 against the same panel at λ = 0). What the ruling's estimator actually delivers is a SEVEN-YEAR pooled `v`, whose CC_REGULAR
level (0.17–0.23 fleet cap-weighted) sits $0.07–0.12 under the frozen three-year table's (0.25–0.36) in every year — the frozen table
was high in 2019–2022 mainly because 2023–2025 were high-wedge years (print-over-hub 0.49 / 0.39 / 0.29 against 0.12–0.29 before),
not because of the lag. One `v` per plant, pooled over every year on disk, is the most defensible version of the ruled object this
chain has produced, and it lands within ±$0.06 of the print in 2019–2021.

**Why 2022 cannot clear clause (a) with any pooled `v`.** The 2022 print-over-hub wedge is the smallest of the seven years (0.118)
because the hub rose through the year ($4.15 Jan → $9.31 Dec, Chicago) and the lagged print trailed it; a pooled `v` of 0.18 therefore
sits above the print there by construction. Clause (a) in 2022 asked the table to reproduce a lag artifact of the print; the offer
must track the hub, not the lag. That is a reading of why the clause failed, not a reason to relax it — the clause was fixed ex ante
and is read as written.

**What the census says the span would have done (reported, not a gate).** In 2019–2021 the ruled form with this table is within
±0.16 GW of the keeper on CC_REGULAR and coal (the miso-298 kill mechanism — CC fuel +0.07–0.14 above the print — is gone), q1–q2
error +0.14 / −0.09 / +0.01 against the keeper. 2022: CC fuel +0.065, q1–q2 error −0.97 (keeper −1.72, frozen −0.54), all-hours
−12.08 (keeper −12.43), coal marginal share 0.167 (keeper 0.177; IMM 0.24). In 2023–2025 the K-4 direction is stronger than
miso-298's: q1–q2 error +4.82 → +3.51, +3.56 → +2.63, +3.19 → +2.75; all-hours 2023 / 2024 +1.69 → +0.83, +0.55 → +0.14; 2025
−2.74 → −2.88. CC_REGULAR static dispatch +0.7 / +0.2 / +0.1 GW in 2023–2025, coal −0.26 / −0.07 / −0.13 GW.

**Owner card (session final message):**

- (A) **Record the finding; keeper unchanged** (recommended under the rule as written). Both R cells stay R. The three full-span
  failures remain routed (C1 ST_GAS 2019, C3b 2021) or without an admissible identified lever (C3a 2020). The chain picks the next
  zero-LP object.
- (B) **Solve the lag-aware table anyway** (7 shards; `miso_gas_variable_transport_lagaware` minted; PRECOMMIT with miso-298's kill
  rules). The census predicts the miso-298 K-1 mechanism removed in 2019–2021, 2022 CC fuel +0.065 (half the frozen table's +0.139,
  which did not flip C1 CC_REGULAR 2022), and a larger training-tier price gain. It is a solve against a pre-stated rule that failed
  on two clauses; the owner, not the lane, makes that call.
- (C) Something else.

Full span NOT-YET on C1 ST_GAS 2019 (routed), C3a 2020, C3b 2021 (routed). Train 2023–2025 CALIBRATED (C3c ledgered).
**No frontier** (owner, 2026-09-28).

## Retrievability

No solve. The pre-stated reading is verifiable at `b3b56fde` (§0 only, placeholders below it), pushed before the lag-aware derive and
table (`4ccb8e6b`) and the census existed. The table is a committed companion file; nothing reads it but the probe shim
(`_miso300_lagaware_census.rebuild_with_table`), and no ScenarioConfig field points at it. Diagnostics (first-difference slopes, the
λ = 0 seven-year comparison): `results/phase0/miso/_miso300_lagaware_diagnostics.json`.
