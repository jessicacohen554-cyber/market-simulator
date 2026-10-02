# FINDING — miso-299: per-year (vintaged) MISO gas variable transport from each year's own EIA-923 receipts — phase 0, zero LP

```
LANE    : miso-299 (owner ruling 2026-10-01, miso-298 decision card "What should miso-299 do?": "Per-year transport phase 0 (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), legs at 8f765fef — unchanged
LP      : none in this document. Fleet-only rebuilds (miso-297 census machinery) cleared at the keeper's own P1 thermal quantity
STATUS  : §0 committed at a5fb67f4 BEFORE any per-year table or census number existed; §§1–4 filled afterwards
VERDICT : FINDING ONLY — §0 clause (a) holds, clause (b) FAILS in 2023, 2024 and 2025. No PRECOMMIT, no shard. Keeper unchanged.
CELLS   : gas_marginal_commodity_pricing R, gas_variable_transport R — both STAY R (evidence added; the full-span test is not re-run)
PROBES  : scripts/data/derive_miso_gas_variable_transport_vintaged.py -> data/raw/reference/miso_gas_variable_transport_vintaged/<Y>.csv (+ .pool.csv),
          results/phase0/miso/_miso299_vintaged_tables.json; scripts/probes/_miso299_vintaged_census.py -> results/phase0/miso/_miso299_vintaged_census.json
```

## 0. Pre-stated reading (fixed before any number)

**The object.** `data/raw/reference/miso_gas_variable_transport.csv` is a frozen derive (rule 23) of each plant's
volume-invariant wedge over its zone's traded hub, `print − hub = v + F/burn`, burn-weighted WLS, pooled over the
**2023–2025** receipts (`derive_miso_gas_variable_transport.py::YEARS`). miso-298 solved the owner-ruled gas form with
that table over 2019–2025 and was killed by K-1; the RESULT (§3 item 2) attributes the early-year cost to the table's
level sitting ABOVE the 2019–2022 print-over-hub wedge, so the form RAISED CC_REGULAR fuel +$0.07–0.14/MMBtu there.

**What this lane measures, at zero LP.** The SAME estimator, bars (`MIN_MONTHS` 12, `MIN_BURN_SPREAD` 2.0) and ladder
(own → zone|group → group → MISO-wide), run on each receipt year 2019–2025 ALONE, written as a NEW companion
(`data/raw/reference/miso_gas_variable_transport_vintaged/<year>.csv` + `.pool.csv`); the frozen table is not touched.
Rule 23: a re-derive on NEW source years (2019–2022 receipts were never in the fit) is admissible and the commit cites
the data. Then the miso-297 census ("joint" leg, m = 1.00) is re-run for every year pointed at the per-year table.

**The reading, stated now:**

- **PROCEED to a PRECOMMIT + 7 shards only if BOTH hold:**
  (a) the per-year table moves static cap-weighted **CC_REGULAR fuel DOWN in each of 2019, 2020, 2021 and 2022** relative to
  the keeper print (the miso-298 kill mechanism reversed: the ruled form must lower, not raise, the CC margin in the
  years it was killed on); and
  (b) in **2023, 2024 and 2025** the per-year table's static cap-weighted CC_REGULAR fuel stays within **±$0.05/MMBtu** of the
  frozen table's value for that year (the training-tier form the owner ruled on is not moved by the re-derive).
- **Otherwise: FINDING only.** Both `R` cells stay `R`, no shard, no PRECOMMIT; the owner gets a decision card with the
  measured numbers.

Reported at full magnitude either way, per year: own-plant coverage (plants, capacity share, by class), `v` cap-weighted
on CC_REGULAR / CT_PEAKER / ST_GAS / all gas, the burn-weighted print-over-hub wedge the panel measures, the static
CC_REGULAR fuel move, static dispatch (coal / CC_REGULAR / all gas / seam, mean GW), static q1–q2 and all-hours
load-weighted price error, and the bid-stack coal marginal share. Nothing is selected on any of these.

**Structural note stated up front (rule 1 / 13).** The frozen derive's docstring calls one value per plant across every
scored year a rule-1(b) property. A per-year table is a per-year MEASURED input (like the per-year EIA-923 print it
replaces), not a tuned value: every row is whatever that year's receipts say, with zero chosen scalars; its forward
analogue is the latest year's table carried forward, exactly as the frozen table already is. The tension is recorded
here so the owner sees it before anything is solved. A PRECOMMIT, if one follows, carries it in §1.

## 1. Derive provenance and receipt availability

- **The frozen table** `data/raw/reference/miso_gas_variable_transport.csv` (+ `.pool.csv`) is written by
  `scripts/data/derive_miso_gas_variable_transport.py` from `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`
  (EIA-923 plant × month gas receipts) against the same daily hub staircases the applier prices from (Chicago Citygate
  flow-day; Henry Hub trade-day for MISO-South). `YEARS = (2023, 2024, 2025)`, pooled: one `v` per plant. Estimator:
  burn-weighted WLS of `print − hub` on `1/burn`; own rung needs `MIN_MONTHS = 12` admissible plant-months and
  `MIN_BURN_SPREAD = 2.0`; ladder own → zone|group → group → MISO-wide. 102 plants, 98 on the own rung.
- **2019–2022 receipts are on disk and were never in the fit.** The parquet carries 2018–2026; MISO gas plants with
  admissible receipts (`quantity > 0`, `price > 0`): 90 / 92 / 96 / 99 plants and 1,041 / 1,033 / 1,052 / 1,107
  plant-months in 2019–2022 (102 / 99 / 98 and 1,128 / 1,116 / 1,119 in 2023–2025). Both daily hub series carry all
  twelve months of every year 2019–2025. Rule 23: the per-year derive is a re-derive on new source years; the commit
  (`5c0491ec`) cites the data.

## 2. The per-year tables (`_miso299_vintaged_tables.json`; `v` nameplate-weighted over the TABLE's plants)

| receipt year | plants / own rung | own-rung cap share of table | `v` CC_REGULAR | `v` CT_PEAKER | `v` ST_GAS | `v` all gas | burn-wtd wedge CC / all | own-plant corr with frozen own |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| frozen 2023–25 | 102 / 98 | — | 0.209 | 1.441 | 1.288 | 0.744 | — | — |
| 2019 | 90 / 50 | 0.52 | 0.203 | 1.691 | 0.750 | 0.781 | 0.177 / 0.240 | 0.85 (48) |
| 2020 | 92 / 51 | 0.59 | 0.093 | 1.345 | 0.258 | 0.512 | 0.255 / 0.301 | 0.77 (50) |
| 2021 | 96 / 51 | 0.59 | 0.341 | 0.159 | −0.499 | 0.156 | 0.067 / 0.136 | **0.13** (50) |
| 2022 | 99 / 66 | 0.68 | **−0.271** | 0.812 | 0.145 | 0.134 | 0.017 / 0.101 | 0.81 (65) |
| 2023 | 102 / 60 | 0.59 | **0.434** | 2.738 | 0.138 | 1.112 | 0.655 / 0.635 | 0.89 (60) |
| 2024 | 99 / 57 | 0.55 | 0.190 | 1.435 | 0.185 | 0.566 | 0.390 / 0.467 | 0.95 (57) |
| 2025 | 98 / 61 | 0.61 | 0.100 | 1.986 | 0.358 | 0.718 | 0.338 / 0.418 | 0.97 (61) |

Three things the tables say before any census:

1. **A single receipt year identifies half the fleet.** With twelve months at most, a plant carries its own rung only when
   every month has an admissible receipt: 50–66 plants against the pooled table's 98. The rest resolve down the ladder to
   that year's own zone|group pool (33–43 plants), so the per-year table is mostly a per-year POOL on the pooled-rung plants.
2. **The per-year intercept is not a stable plant attribute.** CC_REGULAR `v` runs 0.20 / 0.09 / 0.34 / **−0.27** / **0.43** /
   0.19 / 0.10 across 2019–2025; CT_PEAKER 0.16–2.74; ST_GAS −0.50 to 0.75. Plant-level agreement with the frozen own rung is
   0.77–0.97 in six years and **0.13 in 2021**.
3. **What moves it is the year's hub trajectory, not transport.** The frozen derive measured the print as a LAGGED AVERAGE
   (month-over-month slope of the wedge on the hub −0.69 fleet-wide, −0.76 CC_REGULAR). Within each single year the monthly
   CC_REGULAR wedge is anti-correlated with that month's hub change: r = −0.54 / −0.74 / −0.75 / −0.79 / −0.85 / −0.81 / −0.01
   (2019–2025). A year whose hub rises (2022: Chicago $4.15 Jan → $9.31 Dec) prints a wedge that trends negative
   (−0.78 in Dec) and fits `v` = −0.27; a year whose hub falls from a January spike (2023: $3.25 → $2.0–2.4; 2024: $5.53
   Jan → $1.4–2.0) fits +0.43 / +0.19. The single-year intercept absorbs the lag term the pooled fit averages out; it is a
   per-year lag correction wearing the transport's name.

## 3. Census per year (zero LP; `_miso299_vintaged_census.json`; FLEET capacity-weighted, every leg at the keeper's own P1 thermal quantity)

### 3.1 CC_REGULAR fuel ($/MMBtu). Identity: non-gas rows byte-identical across legs; the bare hub agrees between the two joint legs to ≤ $0.002

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| keeper print | 2.686 | 2.238 | 4.529 | 6.670 | 2.920 | 2.606 | 3.674 |
| bare hub | 2.449 | 1.950 | 4.334 | 6.552 | 2.426 | 2.217 | 3.385 |
| print-over-hub wedge | 0.237 | 0.288 | 0.195 | 0.118 | 0.494 | 0.389 | 0.289 |
| ruled form, frozen table (`v`) | 2.796 (0.347) | 2.306 (0.356) | 4.616 (0.282) | 6.809 (0.257) | 2.675 (0.248) | 2.477 (0.260) | 3.626 (0.240) |
| ruled form, per-year table (`v`) | 2.672 (0.223) | 2.074 (0.124) | 4.367 (−0.006) | 6.329 (−0.223) | 2.928 (0.502) | 2.412 (0.194) | 3.508 (0.122) |
| **Δ per-year − print** (§0 (a)) | **−0.014** | **−0.164** | **−0.162** | **−0.341** | +0.008 | −0.194 | −0.166 |
| **Δ per-year − frozen** (§0 (b), ±0.05) | −0.124 | −0.232 | −0.249 | −0.480 | **+0.253** | **−0.065** | **−0.118** |

Other classes, Δ per-year − print: CT_PEAKER +0.61 / +0.63 / −0.73 / −0.09 / +1.32 / +0.39 / +0.73; ST_GAS +0.13 / −0.25 /
−0.74 / −0.37 / −0.36 / −0.25 / −0.24; all gas +0.25 / +0.14 / −0.47 / −0.23 / +0.45 / +0.02 / +0.17. In-table share of gas
capacity 67–73 % (CC_REGULAR 86–91 %) — the same plants as the frozen table, on a different rung mix (§2 item 1).

### 3.2 Static census and dispatch (P1 bid stack; mean GW; coal share all hours / quintile 1)

| year | leg | coal share all / q1 | coal | CC_REGULAR | all gas | seam |
|---|---|---:|---:|---:|---:|---:|
| 2019 (IMM 0.47) | keeper / frozen / per-year | 0.432 / 0.158 · 0.462 / 0.197 · 0.421 / 0.125 | 29.08 · 29.45 · 28.79 | 11.78 · 11.32 · 12.22 | 17.03 · 16.48 · 17.47 | 16.84 · 17.03 · 16.69 |
| 2020 (0.40) | | 0.254 / 0.075 · 0.275 / 0.080 · 0.246 / 0.059 | 23.49 · 23.71 · 23.24 | 11.71 · 11.31 · 12.34 | 17.12 · 16.72 · 17.67 | 17.64 · 17.83 · 17.35 |
| 2021 (0.35) | | 0.371 / 0.382 · 0.384 / 0.415 · 0.425 / 0.386 | 31.63 · 31.88 · 30.69 | 9.02 · 8.75 · 8.93 | 13.48 · 13.16 · 14.71 | 14.10 · 14.17 · 13.82 |
| 2022 (0.24) | | 0.177 / 0.320 · 0.161 / 0.291 · 0.206 / 0.344 | 34.03 · 34.10 · 33.68 | 8.53 · 8.38 · 9.09 | 12.75 · 12.54 · 13.32 | 11.07 · 11.21 · 10.85 |
| 2023 (0.36) | | 0.215 / 0.108 · 0.221 / 0.100 · 0.225 / 0.119 | 20.90 · 20.75 · 21.00 | 16.38 · 16.86 · 15.79 | 22.84 · 23.23 · 22.57 | 13.89 · 13.65 · 14.06 |
| 2024 (0.36) | | 0.197 / 0.074 · 0.204 / 0.084 · 0.199 / 0.066 | 20.03 · 20.01 · 19.83 | 17.01 · 17.06 · 17.51 | 24.21 · 24.30 · 24.79 | 12.51 · 12.44 · 12.13 |
| 2025 (n/a) | | 0.277 / 0.221 · 0.282 / 0.251 · 0.287 / 0.228 | 24.52 · 24.54 · 24.33 | 15.49 · 15.49 · 15.86 | 21.45 · 21.43 · 21.78 | 11.90 · 11.91 · 11.77 |

### 3.3 Static price (bid stack vs the zone-resolved actual, load-weighted; startup markup at the q1–q2 margin 0.00 in every leg and year)

| $/MWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| q1–q2 LW error: keeper → frozen → per-year | +2.87 → +3.41 → **+2.57** | +3.33 → +3.81 → **+2.59** | −0.48 → −0.13 → **−2.27** | −1.72 → −0.54 → **−2.81** | +4.82 → +4.06 → **+5.34** | +3.56 → +3.17 → +2.26 | +3.19 → +3.18 → +2.66 |
| all-hours LW error | +1.38 → +1.84 → +1.09 | +1.80 → +2.24 → +1.12 | −4.77 → −4.36 → −6.21 | −12.43 → −11.62 → −13.60 | +1.69 → +1.22 → +2.05 | +0.56 → +0.45 → −0.30 | −2.74 → −2.60 → −3.23 |
| q1 / q2 median, per-year leg (actual) | 22.4 / 25.1 (19.2 / 21.2) | 17.8 / 20.3 (15.1 / 17.1) | 26.3 / 28.9 (23.3 / 25.8) | 39.6 / 44.6 (40.2 / 48.4) | 26.0 / 29.5 (19.6 / 23.1) | 20.0 / 23.8 (16.9 / 20.4) | 29.9 / 33.0 (24.2 / 27.7) |

## 4. Reading against §0, and what happens next

**§0 (a) HOLDS:** the per-year table moves static CC_REGULAR fuel down in 2019, 2020, 2021 and 2022 (−0.01 / −0.16 / −0.16 /
−0.34 $/MMBtu against the print; −0.12 to −0.48 against the frozen table). **§0 (b) FAILS in all three training years:** the
per-year table moves 2023 by **+0.25**, 2024 by **−0.07** and 2025 by **−0.12** $/MMBtu against the frozen table (bar ±0.05).
In 2023 it puts CC fuel back at the keeper print (+0.008) and erases the one gain miso-298's K-4 recorded there
(static q1–q2 error +4.06 → +5.34, worse than the keeper's +4.82). **The lane does not proceed.** No PRECOMMIT, no shard,
no ScenarioConfig field; both R cells stay R with this evidence; the keeper is unchanged.

**Why the rule failed, structurally (rules 1 / 13 / 14).** The variable transport is a contractual attribute of the delivery
path — one value per plant is the right object, and the frozen derive's docstring says so. A per-year re-fit does not measure
that attribute more locally; it measures the year's hub trajectory through the print's lag (§2 item 3): negative where the
hub rose through the year (2022), large where it fell from a January spike (2023, 2024). The directions the owner's
hypothesis predicted for 2019–2022 do appear (the per-year `v` is below the frozen `v` there), but for the lag reason, not
because transport was cheaper in those years — and the same mechanism moves 2023–2025 off the ruled form by more than the
bar in the other direction. Solving it would trade the training-tier form the owner ruled on for a per-year lag correction.

**What the census says the early years would have done (reported, not a gate).** CC_REGULAR static dispatch +0.45 / +0.63 /
−0.09 / +0.56 GW vs the keeper in 2019–2022 (coal the mirror; the miso-298 kill mechanism reversed in 2019 / 2020 / 2022),
q1–q2 error 2019 / 2020 improves by $0.3 / $0.7 against the keeper, but 2021 / 2022 all-hours error deepens by $1.4 / $1.2
(already −4.8 / −12.4 static; C3a 2022 is a routed miss). The structural question the miso-298 kill left open — why the
ruled form's fuel correction in 2021 pushes CC_REGULAR out of band when the fuel it corrects to is the measured marginal
cost — is not a transport-table question (rule 14: a worse fit after real data is a bug elsewhere). It stays open.

**Owner card (session final message):**

- (A) **Record the finding; keeper unchanged** (recommended). The three open full-span failures remain routed (C1 ST_GAS
  2019, C3b 2021) or without an admissible identified lever (C3a 2020). The chain picks the next zero-LP object.
- (B) **Phase 0 on a lag-aware pooled estimator** — regress `print − hub` on `1/burn` AND the month's hub change, pooled over
  all seven receipt years, one `v` per plant (the lag slope the frozen derive already measured becomes a regressor instead
  of a contaminant). An estimator change on a frozen derive: needs an owner ruling (rule 23 admits only source-data
  updates). Zero LP; the §0 form of reading, pre-stated again.
- (C) **Solve the per-year table anyway** (7 shards; a field minted; forward analogue = latest year's table). The census
  predicts 2019 / 2020 / 2022 move toward actual on CC/coal, 2021 / 2022 prices further negative, 2023 loses the K-4 gain.
  Not recommended.
- (D) Something else.

Full span NOT-YET on C1 ST_GAS 2019 (routed), C3a 2020, C3b 2021 (routed). Train 2023–2025 CALIBRATED (C3c ledgered).
**No frontier** (owner, 2026-09-28).

## Retrievability

No solve. The pre-stated reading is verifiable at `a5fb67f4` (§0 only, placeholders below it), pushed before the per-year
derive (`5c0491ec`) and the census (`01b5ab73`) existed. The per-year tables are a committed companion directory; nothing
reads them but the probe shim (`_miso299_vintaged_census.rebuild_with_table`), and no ScenarioConfig field points at them.
