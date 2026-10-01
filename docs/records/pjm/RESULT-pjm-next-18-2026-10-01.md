# RESULT — PJM-NEXT-18: who sets the low-end price, 2019–2025; the keeper's per-unit layer lands on `main`

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO (v3.13) all read **NOT-YET**. Same 10 failing cells.

**Records:** `PRECOMMIT-pjm-next-18-2026-10-01.md` (predictions fixed before any replay).

**Solves:** seven one-year diagnostic keeper replays, one shard per year (rule 36), pinned to `d9668d84`. They were never registered. Owner card: *"All 7 years"*.

## 1. G-REPRO: the replays ARE the keeper

Every class's P1 TWh matches the keeper's committed `class_hourly`, **Δ = 0.000000 TWh in all seven years**. The G-DRIFT audit (PRECOMMIT §3) is confirmed.

## 2. The keeper's per-unit layer (owner instruction, all ISOs)

- **Instruction:** *"Make sure this is captured in the keeper bundle moving forward"* / *"Moving forward for all ISOs. Add as rule or something to code"*.
- **The full `unit_hourly` is too big to commit:** PJM's runs 69–81 MB/yr, not the ~1–2 MB/yr measured on NYISO, and 65 of every 77 MB is raw `red_cost`.
- **Owner card *"Slim layer"*: `hourly/unit_marginal_<y>.parquet`.**
  - It is `unit_hourly` minus `red_cost`, plus an int8 `marginal` flag (interior and `|red_cost| ≤ $0.01`).
  - Built by `scripts/lib/unit_marginal.py`, which streams one row group at a time.
- **Every solve now writes it** (`run_calibration_full.py`). The full `unit_hourly` stays local and gitignored.
- **CLAUDE.md rule 15** requires the layer in every keeper bundle. **`check_promotion_completeness.py` leg (e)** fails a promoting PR that lacks it. The leg is prospective: it is armed only for a keeper that changed against `--base`.
- **PJM keeper:** the layer is attached for 2019–2025.
  - Size: 10.2–11.5 MB/yr, 76 MB in total.
  - Marginal sets are identical to the full frames (16,913 / 14,293 / 13,892 / 14,919 / 15,465 / 13,742 / 12,451 unit-hours).

## 3. Card 1 — the low-end census, all seven years

`low` = hours with actual RT below 6.5 × delivered gas. Script: `scripts/probes/_pjmnext18_lowend_census.py` → `results/phase0/pjm/_pjmnext18_lowend_census.json`.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| low hours | 3188 | 3934 | 3470 | 2380 | 2635 | 2310 | 2380 |
| median marginal offer ÷ gas (low) | 7.26 | 7.65 | 7.40 | 7.83 | 8.67 | 8.95 | 8.28 |
| median actual RT ÷ gas (low) | 5.70 | 5.45 | 5.52 | 5.70 | 5.36 | 5.27 | 5.43 |
| **gap** | 1.56 | 2.20 | 1.88 | 2.13 | **3.31** | **3.68** | 2.85 |
| low weight offered < 6.5 × gas | .086 | .131 | .091 | .046 | .044 | .042 | .041 |
| hours with a unit-marginal (low)\* | .837 | .807 | .819 | .845 | .738 | .713 | .698 |
| COAL_BIT econ share of low marginal weight | .218 | .194 | .167 | .089 | .046 | .062 | .112 |
| **all hours: model CC / coal / CT** (renormalized) | .44/.46/.11 | .46/.40/.14 | .59/.27/.14 | .55/.29/.16 | .51/.26/.23 | .45/.29/.26 | .50/.19/.31 |
| **IMM CC / coal / CT** (renormalized) | .67/.26/.07 | .73/.20/.07 | .71/.17/.12 | .74/.12/.14 | .77/.10/.12 | .75/.13/.12 | .78/.10/.12 |

\* Any LP unit, including hydro and the unlabelled seam/import rows (6–14 % of all-hours weight), not only thermal. The PRECOMMIT called it "thermal", which is wrong; corrected here.

**Predictions:**

| id | result |
|---|---|
| P1 (≤ 5 % of low weight offered < 6.5 × gas, every year) | **FALSIFIED** in 2019 / 2020 / 2021 (.086 / .131 / .091); holds 2022–2025 |
| P2 (gap ≥ 1.5, every year) | holds (1.56–3.68) |
| P3 (gap not year-discriminating: 2019–21 mean minus 2023–24 mean < 0.5) | holds, and **inverted**: 1.88 vs 3.50. The low-end price-floor gap is *larger* in the fit years |
| P4 (unit-marginal share in low hours ≥ 0.75) | **FALSIFIED** in 2023 / 2024 / 2025 (.738 / .713 / .698) |
| P5 (model CC share below IMM's, every year) | holds: .44–.59 vs .67–.78 |
| P6 (COAL_BIT econ share of low-end marginal weight higher in 2019–21 than in 2023–24) | holds: .193 vs .054 |

**Readings.**
1. **The low-end level gap is not the year lever.** Per P3, it is largest in 2023/24, where C1 and C3a pass. It is an all-year level object.
2. **Model coal sets the price about twice as often as the IMM reports, in every year** (×1.7–2.6), and CC too rarely. The ratio is roughly constant across years. What varies by year is how often coal is near the margin at all.
3. **In the miss years, real PJM clears model-coal-set hours at an efficient CC's fuel cost.** `scripts/probes/_pjmnext18_coal_marginal_hours.py` reads the committed layer. A "coal-set hour" carries ≥ 0.5 of its marginal weight on coal.

| coal-set hours | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| share of year | .306 | .259 | .175 | .190 | .136 | .175 | .118 |
| model coal marginal offer, $/MWh | 24.57 | 22.16 | 32.68 | 58.14 | 30.87 | 28.43 | 34.58 |
| actual RT, $/MWh | 21.35 | 17.97 | 26.92 | 52.19 | 25.88 | 25.20 | 30.10 |
| efficient-CC fuel cost (6.5 × delivered gas) | 20.80 | 16.84 | 27.50 | 41.34 | 20.47 | 18.14 | 25.48 |
| **actual ÷ efficient-CC cost** | **1.03** | **1.07** | **0.98** | 1.26 | 1.26 | 1.39 | 1.18 |
| actual below the model coal offer | .854 | .881 | .805 | .671 | .718 | .686 | .738 |

- In 2019–2021, real prices in these hours sit **at** an efficient CC's delivered fuel cost. Real PJM cleared them on efficient CCs, below the model's coal.
- In 2022–2025, real prices sit 18–39 % above that cost.
- This separates the COAL_BIT miss years cleanly. It is the year-discriminating face of the coal over-run.
4. **The model's cheap CC block is not what moves.**
   - In coal-set hours the model offers about 19 GW of CC_REGULAR tranche capacity at or below 6.5 × gas in 2019, 2020, 2021 and 2023 alike (14–23 GW across all seven years). The LP loads all of it.
   - The capacity-weighted median CC offer is 6.5–7.2 × gas.
   - So the gap is in **how much CC capacity real PJM offers below the coal offer**, not in the model's cheapest units.

**Verdict, card 1:** measured and located. No admissible, year-discriminating, zero-DOF mechanism is identified yet, so card 3 is **not reached**. Readings 3–4 name the next measurement. **This is not a model-class limit.**

## 4. Card 2 — CC_REGULAR 2023 (zero LP)

`scripts/probes/_pjmnext18_cc_night_band.py` → `results/phase0/pjm/_pjmnext18_cc_night_band.json`, with a plant census.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CC night, model / actual | 83.6 / 79.4 | 90.3 / 84.3 | 84.0 / 81.9 | 94.9 / 89.2 | **105.3 / 100.2** | **105.5 / 104.6** | 102.8 / 105.1 |
| CC day, model / actual | 191.6 / 189.1 | 203.0 / 199.0 | 196.6 / 197.3 | 214.0 / 208.5 | **228.9 / 225.7** | **229.3 / 230.8** | 220.0 / 225.6 |
| night median price, model / actual | 23.4 / 18.9 | 20.0 / 15.0 | 31.5 / 25.0 | 56.9 / 47.5 | 27.1 / 19.7 | 25.2 / 18.8 | 35.0 / 28.6 |

- **The 2023 miss is the model not tracking 2023 → 2024.** Real CC output rose 4.4 TWh at night and 5.1 TWh by day. The model's is flat (+0.2 / +0.4).
- **The excess is diffuse.** It is spread over about 70 plants, roughly in proportion to output (Kendall +2.6, Linden +2.3, York +1.5 TWh, …). No plant comes online mid-year and no outage month carries it.
- It sits in both the floor (66 TWh) and the econ (39 TWh) bands.
- The night price excess (+$6–7) is the same in 2023 and 2024, so it does not discriminate either.
- **Verdict:** no lever. **OPEN, not a limit.**

## 5. Next

1. Decompose real PJM's CC offer stack against coal in the 2019–2021 coal-set hours:
   - from the offers corpus, the CC_LIKE MW offered below the hour's coal offer, against the model's per-unit `mc` (now committed);
   - by heat-rate tier, against EIA-923 / CAMPD full-load heat rates.
   This tests whether real efficient CCs offer near full-load heat rate × delivered gas while the model prices them higher, with zero DOF, before any design.
2. CC_REGULAR 2023: why the model's CC is flat 2023 → 2024 while real CC output rises, given fleet, outages and gas.

**Retrievability (rule 34(e)).** The replays are keeper duplicates and never promotable. Their durable output is the keeper's `unit_marginal_<y>.parquet` (on `main` with this PR) plus the JSONs above. The leg SHAs (provenance only) are:

| year | SHA |
|---|---|
| 2019 | `e290941b9ecbd5f87ef6233893822a15987c36d5` |
| 2020 | `141182dfb173b8d9fdcbda2447c0feab73693762` |
| 2021 | `8b180fa0490ca750940213d274ba90b7aa501ed3` |
| 2022 | `2e16e5794e37e4a322354c7d279a44df59606543` |
| 2023 | `ac26a2c829710aab7200197b9108ec638428eddc` |
| 2024 | `93c4875f01a0b85a1ffdb41c659dd5ee3a10334b` |
| 2025 | `bf7d6066139caf9fb0dd1559ca0afc50f17293b2` |

The shard branches `claude/pjm-next-18-rp-2019` … `-2025` are left for the owner to delete; sessions cannot delete refs.
