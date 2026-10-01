# FINDING — PJM-NEXT-14: who prices the low end, where CCs buy gas, what the mid-curve floor does (zero LP + one diagnostic replay)

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`), unchanged. Nothing registered or promoted.

**Solves:** one byte-faithful keeper replay of 2020 in one shard, used only to read the LP's own marginal units.
- **Reproduces the keeper exactly.** Every class's P1 TWh differs by 0.000 (`results/calibration/_pjmnext14_replay_2020_repro.json`).
- **Pre-registration:** `docs/PRECOMMIT-pjm-next-14-lowend-replay-2026-09-30.md`, P1–P4, all held.
- **Owner ruling on the result:** *"Record, hand off"*.

## Card 1 — the keeper's low-end price-setters (2020, LP primal + reduced costs)

- **Source.** `hourly/unit_hourly_2020.parquet` from the replay carries per unit-hour `mw`, `cap_mw`, the P1 offer `mc` and HiGHS `red_cost`.
- **Marginal unit.** An interior unit with `|red_cost| ≤ 0.01`.
- **Grain.** Zonal P1 prices differ by more than $1 in 97 % of hours, so most zones import their price. The marginal set is therefore pooled per hour (`scripts/probes/_pjmnext14_lowend_lp_system.py`); the zone grain (`_pjmnext14_lowend_lp.py`) is kept only as a record.

| 2020 | all hours | low-end hours (RT < 6.5 × delivered gas; 45 %) |
|---|---|---|
| hours with a thermal marginal unit | 0.83 | 0.82 |
| CC_REGULAR (econ / committed) | 0.24 (0.18 / 0.06) | **0.32 (0.21 / 0.11)** |
| COAL_BIT econ | 0.16 | **0.18** |
| ST_CHP committed | 0.07 | 0.09 |
| CT_PEAKER / ST_GAS | 0.09 / 0.08 | 0.04 / 0.03 |
| median marginal offer ÷ delivered gas | 8.34 | **7.78** |
| median actual RT ÷ delivered gas | 6.73 | **5.45** |
| median price, model LW / actual RT ($/MWh) | 22.84 / 18.08 | 20.33 / 14.50 |

- The low end is priced by **CC econ and min-load rungs plus coal econ**, at about 7.8 × delivered gas, where the real price sits at 5.5 ×.
- Only 1.1 % of low-end marginal weight offers below 6.5 × delivered gas.
- Marginal CCs on production-area supply offer at about 15 × production gas (P3).
- The zero-LP payload detector (`_pjmnext14_lowend_marginal.py`) is **not reliable**: host-steam CHP holds partial load in every hour, so CHP gets mislabelled as marginal. It is not used as evidence.

## Card 2 — plant-level gas supply point: CLOSED

- **Source, no new intake.** EIA-860's own per-plant `Natural Gas Pipeline Name 1–3` / `LDC Name` / `Pipeline Notes` cover 99.5 % of PJM CC MW (81 % name a pipeline).
- **Map.** Each pipeline is mapped to a pricing area by the IMM's own production-gas definition: Dominion South, TGP Z4 and Transco Leidy, plus other Appalachian receipt supply. It is a fixed pipeline × state (× county for TETCO/Transco in PA) table, `scripts/probes/_pjmnext14_supply_point.py`.

| year | production-area share of CC MW | keeper fuel, production tier | IMM production | keeper − production | measured EIA-923 premium (the 2 production-area CCs with prints) |
|---|---|---|---|---|---|
| 2019 | 0.275 | 2.59 | 2.08 | +0.51 | +0.37 |
| 2020 | 0.291 | 1.90 | 1.36 | +0.54 | +0.41 |
| 2021 | 0.324 | 3.68 | 2.99 | +0.70 | +0.62 |
| 2022 | 0.311 | 6.33 | 5.51 | +0.82 | +0.75 |
| 2023 | 0.327 | 2.50 | 1.62 | +0.87 | +0.86 |
| 2024 | 0.327 | 2.28 | 1.67 | +0.61 | +0.74 |
| 2025 | 0.319 | 3.39 | 2.82 | +0.57 | +0.40 |

- **The keeper already prices production-area CCs at their measured delivered cost.** Its premium over production spot follows the only two measured production-area prints (Dresden 55350 and Fremont 55701, both on Dominion Transmission) year by year, to within about $0.15, including the 2023 peak.
- **What remains is not measurable plant by plant.** It is the average-vs-marginal wedge (reservation charges inside a delivered print). It is largest in 2023, a fit year, so it is **not year-discriminating** — NEXT-13's conclusion, now at plant grain.

## Card 3 — the mid-curve floor at the low end

- **(a) The normalizer is inert.**
  - 100 % of CC econ MW is priced in the keeper's SHAPE form: own committed-rung cost × measured ratio, so the gas normalizer cancels.
  - For LONG_RUN, the floor is built and applied with the same gas-day series, so it returns the measured offer level in $/MWh.
  - Rebuilding with a regional normalizer cannot move either.
- **(b) The median aggregation does not lift the low end.**
  - The full measured distribution comes from the offers corpus (`scripts/probes/_pjmnext14_midcurve_dist.py`, the derive's own segmentation and share sampling). Its median reproduces the keeper's floored share (0.584 vs 0.582 for COAL_BIT 2020).
  - A rank-matched floor would **raise** coal econ bids: COAL_BIT +2.3 (2020) / +9.6 (2023) $/MWh.
  - A rank-matched CC level also **raises** the marginal CC offer: +2.7 $/MWh in low-end hours, +4.75 in all hours.
  - The measured CC distribution is much wider than the model's. Cheap CCs get cheaper but were already running; the model's marginal CCs sit in its upper ranks.
- **What the distribution does show.** A quarter of PJM's CC_LIKE offer capacity at mid-curve (shares 0.25–0.65) is priced at **≤ 3.3–4.0 × delivered gas** (p10 1.4–3.3): below any CC's fuel cost, i.e. price-taking blocks.

| CC_LIKE share 0.45 | p10 | p25 | p50 |
|---|---|---|---|
| 2020 | 2.6 | 3.5 | 5.1 |
| 2023 | 1.8 | 3.3 | 4.9 |

  The model's CC committed rung bids at 6.4–7.1 × delivered gas in every year. The cheap block is **present in both a fit year and a miss year**, so as measured here it is not year-discriminating either.

## Verdict

| object | status | next test |
|---|---|---|
| C3a 2019/2020 and the all-year floor | **OPEN.** The low-end price-setters are named (CC econ/committed + coal econ at 7.8 × delivered gas). Gas supply point, normalizer and median aggregation are each refuted as the cause. | PJM-NEXT-15: the cheap (price-taking) quarter of PJM CC offer capacity, by year for all seven years, against a model CC fleet that has no such block — and jointly with the CC volume over-run (pjm-h20/h21) that pricing it would worsen. |
| COAL_BIT 2019/2021, CT_PEAKER 2021 | OPEN, unchanged | as NEXT-13 |

Nothing here is called a model-class limit.

**Retrievability.** The replay bundle, a keeper duplicate that is never promotable, is on shard branch `claude/pjm-next-14-replay-2020` (commit `a3dfb0b1…`, provenance only; that branch is transport and will be cut). Every number above is in the committed JSON: `_pjmnext14_lowend_lp_2020{,_system}.json`, `_pjmnext14_replay_2020_repro.json`, `_pjmnext14_supply_point.json`, `_pjmnext14_midcurve_dist.json`. Reproducing the replay costs one ~40-minute shard.
