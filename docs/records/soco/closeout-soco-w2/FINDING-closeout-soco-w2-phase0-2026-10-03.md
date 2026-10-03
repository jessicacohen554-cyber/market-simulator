# FINDING closeout-SOCO-w2 phase 0 — coal at spot replacement price is NOT CHARTERED; §3.8 queue exhausted

Lane closeout-SOCO-w2, 2026-10-03. Zero LP throughout. Bars were fixed in
`PRECOMMIT-phase0-closeout-soco-w2-2026-10-03.md` and pushed at `930190fa` before any reach number was computed.

**Object.** Keeper `2026-10-03-closeout-soco-3-coalpile` (bundle `results/calibration/closeout_soco_3_span`), rubric v3.20.

**Probes.**

- `scripts/probes/_closeout_socow2_spot_reach.py` writes `spot_reach.csv`, `spot_validity.csv` and `spot_hr.csv`.
- `scripts/probes/_closeout_socow2_pool_scope.py` writes `pool_scope.csv`.

## Verdict

| §3.8 step | Reading | Status |
|---|---|---|
| 0: caveat-budget ruling | Exact question sent to the desk at lane start. It cannot change the determination today, because CC_REGULAR 2019 fails on its own. | owner-gated |
| 1: L1, coal econ/peak tranches at same-month Page-5 spot | C3a 2022 improves by only 0.4 pp (F1) or 1.0 pp (F2). The bar was ≥ 2.0 pp, so **K3 trips**. K1, K2 and K4 are clear. | **NOT CHARTERED** |
| 2: build `coal_marginal_replacement_pricing` | Falls with step 1. | not built |
| 3: pool-vs-BA benchmark-scope census | Done (§3 below). Writing the census into the ledger rows means editing `calibration_verdict.py`, so it is a rule-37 rubric amendment. It is proposed below, not landed. | census done; text proposed |
| 4: Georgia PSC / Alabama fuel-testimony pull | Needs an owner download (plan §4 item 17). The ask was sent to the desk. | owner-gated |

The plan §3.8 queue is **exhausted for this lane**: every remaining step is owner-gated. SOCO stays NOT-YET on C1
CC_REGULAR 2019 (+3.2 pp).

## 1. L1 reach (PRECOMMIT §3 method)

**Method validity gate.** The restack base reproduces the keeper's load-weighted price within ±5 %, with hourly
r 0.91–0.98, in 2019, 2020, 2022 and 2023. It misses narrowly in 2021 (+5.97 %), 2024 (+5.01 %) and 2025 (+5.07 %).
For those three years, as pre-registered:

- C3a and C3b are read on the same-setter greedy;
- C1 is not computed.

The restack energy deltas for those years are still printed in `spot_reach.csv`. All of them are ≤ 0.4 TWh.

| Year | Coal-setter hours (keeper) | Mean Δmc on spot cells, F1 / F2 ($/MWh) | C3a keeper → F1 / F2 | C3b keeper → F1 / F2 | CC_REGULAR share | COAL_BIT | COAL_PRB |
|---|---|---|---|---|---|---|---|
| 2019 | 15.4 % | +1.1 / +1.7 | +8.7 → +8.8 / +8.8 % | 0.112 → 0.113 / 0.113 | +3.2 → +3.2 / +3.2 pp | −7.82 → −7.83 / −7.79 | −0.40 → −0.42 / −0.51 |
| 2020 | 9.1 % | +0.1 / −1.2 | +8.4 → +8.4 / +8.4 % | 0.113 → 0.113 / 0.113 | +1.8 → +1.8 / +1.8 | −3.54 → −3.52 / −3.52 | −0.75 → −0.76 / −0.76 |
| 2021 | 5.6 % | +0.1 / +0.1 | −6.7 → −6.7 / −6.8 % | 0.125 → 0.125 / 0.126 | (not computed) | | |
| **2022** | **4.8 %** | **+16.2 / +22.6** | **−13.7 → −13.3 / −12.7 %** | 0.282 → 0.276 / 0.274 | +0.7 → +0.8 / +0.9 | +1.23 → +1.22 / +1.22 | +2.64 → +2.48 / +1.89 |
| 2023 | 5.9 % | +43.7 / +41.7 | −0.4 → −0.5 / −0.3 % | 0.091 → 0.091 / 0.092 | +2.4 → +2.4 / +2.5 | −3.16 → −3.16 / −3.16 | −1.07 → −1.06 / −1.14 |
| 2024 | 4.5 % | +21.9 / +35.5 | −6.0 → −6.0 / −5.9 % | 0.184 → 0.184 / 0.183 | (not computed) | | |
| 2025 | 4.8 % | +7.4 / +22.0 | −4.7 → −4.7 / −4.7 % | 0.184 → 0.184 / 0.184 | (not computed) | | |

Kills, against the bars:

- **K1** (no C1 PASS → FAIL): clear.
- **K2** (no passing C3a/C3b year leaves its band): clear.
- **K3** (target ≥ 2.0 pp): **trips** on both forms.
- **K4** (CC_REGULAR 2019 does not worsen by > 0.3 pp; COAL_BIT 2019 does not worsen by > 1.0 TWh): clear.

### Why the lever cannot reach 2022

**Coal is not on the margin in 2022.** Coal sets the keeper's price in 4.8 % of 2022 hours. Spot lots raise
coal econ/peak offers by about $16–23/MWh, but that still leaves coal below the $7–9/MMBtu gas CC that sets the
2022 price. So the price barely moves.

**The 2022 coal over-run the plan cited no longer exists.**

- The plan's "+7.5 TWh coal surge" was measured on an older keeper. The current keeper sits +3.9 TWh above the
  45.5 TWh bench (BIT +1.23, PRB +2.64), because the pile ceiling already binds on PRB.
- The arm removes at most 0.8 TWh of PRB (F2).

**Spot lots are a minority of receipts.** Page-5 spot (`Purchase Type S`) share of receipt MMBtu per plant-year:

| Plant | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Barry (3) | 29 % | 0 | 1 % | 0 | 0 | 0 | — |
| Gaston (26) | 9 % | 8 % | 7 % | 31 % | 20 % | 13 % | 0 |
| Bowen (703) | 33 % | 21 % | 43 % | 15 % | 4 % | 0 | 7 % |
| Miller (6002) | 0 | 0 | 30 % | 20 % | 8 % | 0 | 0 |
| Wansley (6052) | 100 % | — | 0 | 0 | — | — | — |
| Daniel (6073) | 8 % | 0 | 69 % | 7 % | 7 % | 13 % | 4 % |
| Scherer (6257) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### What the λ peak premium is not

The live C3a/C3b 2022 ledger reason names replacement fuel as the only Sch. 6 term left in λ's peak premium.

- **Replacement coal is now measured.** At plant-month Page-5 spot it closes ≤ 1.0 pp of the −13.7 %.
- **So the premium is not replacement coal.** Any replacement-fuel component would have to be gas. That is the
  licensed-SE-daily-gas question already recorded in the `gas_daily_shape` cell (soco-90).

### Rule 19 and the captive sibling

L1 would have lived inside the `coal_plant_monthly_pricing` seam as a sibling selection to
`coal_captive_marginal_fuel_price`. The census of that field's object:

- On Page 5, 2019–25, no SOCO coal plant-year mixes captive (TC/TR, in-state, non-spot) and non-captive receipts,
  except Gorgas (plant 8) in 2019, at 4.5 % captive MMBtu.
- The field is therefore near-inert in SOCO. It stays `U` and was not armed.

## 2. G-DRIFT, shards, promotion

None. No field was built and nothing was solved.

## 3. Step 3: benchmark scope (pool vs BA)

**The scope mismatch.** The C3a/C3b benchmark is the Southern Company Services FERC-714 Sch. 6 system λ. The model
dispatches the whole SOCO balancing authority.

**How ownership was split.** SOCO-BA EIA-923 net generation, split by EIA-860 owner. The owner schedule is taken
from the solve-year vintage, capacity-weighted per plant. A plant with no owner row is assigned to its operator.

| Year | BA net gen TWh | Southern operating cos | Southern Power | Non-Southern owners |
|---|---|---|---|---|
| 2019 | 253.2 | 58.4 % | 10.8 % | 30.5 % |
| 2020 | 238.9 | 59.4 % | 11.0 % | 29.6 % |
| 2021 | 246.8 | 59.9 % | 9.8 % | 30.3 % |
| 2022 | 255.4 | 54.6 % | 11.0 % | 34.1 % |
| 2023 | 250.5 | 53.4 % | 11.8 % | 34.7 % |
| 2024 | 258.5 | 55.9 % | 9.7 % | 34.3 % |
| 2025 | 262.2 | 55.9 % | 9.7 % | 34.3 % |

The non-Southern owners are the co-owners of Vogtle, Scherer, Hatch and Wansley (Oglethorpe, MEAG, Dalton) plus IPPs.

**The split is unweighted by price.**

- 30–35 % of the energy the model prices sits outside the Southern companies whose incremental cost λ reports.
- The share rises in 2022–25.
- Whether Southern Power's units sit inside the IIC dispatch is not established here. That needs the IIC text, which
  is not on disk.

This is ledger quality only. No gate moves.

### Proposed ledger-text amendment (rule 37: owner ruling, separate PR, no keeper change in the same PR)

The proposal adds one sentence to the `_C3A_REASON` text and to the C3b 2022 row reason in
`scripts/calibration_verdict.py`.

**The sentence:** *"Scope: λ is the Southern Company Services pool's incremental cost (IIC §3.1/§3.6: replacement
fuel, VOM, losses, purchases at energy cost); 30–35 % of SOCO-BA net generation 2019–25 is owned outside the Southern
companies (closeout-SOCO-w2 §3), and replacement coal at Page-5 spot closes ≤ 1.0 pp of C3a 2022
(closeout-SOCO-w2 §1)."*

**Effect.** Text only: no threshold, budget or admissibility set changes. The zero-LP before/after determination is
identical for every ISO by construction, so the amendment is a ruling on wording.
