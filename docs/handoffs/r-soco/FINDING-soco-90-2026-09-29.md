# FINDING soco-90 — can a licensed SE daily gas series do the joint C3a repair? (zero LP)

**Owner rulings in force (soco-89 cards):** "Reopen joint repair"; "License SE daily gas". The licensed file
has **not** been supplied (owner card, this session: "Not yet"). So this lane did the prep and a zero-LP bound.
No solve, no registration. Keeper unchanged: `2026-09-29-soco87-gas-hh-monthly`, NOT-YET 7/4/0/1/2.
Branch base `origin/main` 3145578d; soco-89's PR #6877 was still open, so its commit is cited as
`3c8fde1e3daa19c53b1499682172d00e2d364e67`.

## Conclusion

**No daily fuel series, licensed or not, can perform the joint repair in 2023–2025.** The two C3a errors
from soco-89 are mostly *within the same day*: in 2023–25, 70–83 % of the top-20 % lambda hours fall on a
day that also has low-40 % hours. On those days, to match lambda, replacement gas would need to be about
**$0.2–0.5/MMBtu below Henry Hub at night** and **$1.0–1.6 above it in the afternoon**. A daily price has one
value per day, so it cannot do both. The residual is an intra-day offer-shape error, not a fuel error.

What a licensed series *could* still do is narrower: the winter spike tail (Elliott) and 2022, where only
13 % of top hours share a day with low hours. That would not clear 2023–25, and a level cut pulls those
years down (the HH reference arm below fails all three).

## 1. Method

Probe: `scripts/probes/_soco90_se_daily_replacement.py` (new). It extends the soco-85 greedy re-stack
instrument to `soco87_span`: `fleet_only` rebuild of the keeper recipe, every SOCO gas unit re-priced at a
daily replacement price `hub / (1 − retention) + usage` (calendar day → CST hours 0–23), merit order
re-stacked, and the price delta re-scored through `calibration_verdict` against the keeper's committed bench.
It also reports the soco-89 low-40 % / top-20 % decomposition, and the **required hub premium**: the
remaining gap in each gas-marginal hour divided by the greedy marginal unit's heat rate (first-order; no
re-ordering).

**Reference arm = Henry Hub daily** (committed, public). This is not a candidate: "replacement = HH commodity"
is already refused (FINDING-soco-85 §7). It is the SE-basis = 0 anchor, so the required premium reads
directly as "what (SE hub − HH) would have to be". No transport table is committed for SOCO, so usage and
retention are 0 here. Both are small and positive, so they would only raise the arm's prices slightly.
2019 reproduces soco-85's hub bound (C3a +7.1 vs +7.2, Δprice −1.85 vs −1.84).

## 2. Reference arm (replacement = HH daily, no transport)

| year | C3a keeper → arm | C3b keeper → arm | low 40 % $/MWh | top 20 % $/MWh |
|---|---|---|---|---|
| 2019 | +14.0 FAIL → +7.1 PASS | 0.166 → 0.117 | +2.60 → +2.07 | −0.32 → −0.80 |
| 2020 | +14.4 FAIL → +3.8 PASS | 0.177 → 0.104 | +1.95 → +1.32 | −0.28 → −0.96 |
| 2021 | −2.4 PASS → −5.3 PASS | 0.119 → 0.122 | +1.90 → +1.62 | −2.93 → −3.38 |
| 2022 | −12.7 FAIL → −25.0 FAIL | 0.275 → 0.357 | +3.21 → +1.11 | −11.71 → −15.78 |
| 2023 | +2.3 PASS → −11.1 FAIL | 0.094 → 0.142 | +1.88 → +0.81 | −2.03 → −3.39 |
| 2024 | −3.6 PASS → −19.0 FAIL | 0.180 → 0.239 FAIL | +2.03 → +0.64 | −3.60 → −5.08 |
| 2025 | −1.5 PASS → −12.6 FAIL | 0.189 → 0.203 FAIL | +2.70 → +1.49 | −4.54 → −6.07 |

C1 side-effects: 2019 COAL_BIT (the ledgered caveat) worsens −4.1 → −4.7 pp; 2021 CC_REGULAR flips PASS → FAIL
(+3.0 pp); every other scored row keeps its status. The low-end error shrinks but does not close even at HH.

## 3. What a replacement series would have to be ($/MMBtu over HH, load-weighted, gas-marginal hours)

| year | top 20 % all | top 20 % Dec–Feb | top 20 % Mar–Nov | low 40 % | top-20 % hours on a day with low-40 % hours |
|---|---:|---:|---:|---:|---:|
| 2019 | +0.28 | +0.62 | +0.26 | −0.61 | 95 % |
| 2020 | +0.37 | +0.46 | +0.35 | −0.37 | 68 % |
| 2021 | +1.47 | +3.55 | +1.24 | −0.54 | 31 % |
| 2022 | +5.78 | +36.06 | +4.09 | −0.34 | 13 % |
| 2023 | +1.20 | +3.00 | +1.05 | −0.21 | 83 % |
| 2024 | +1.68 | +2.58 | +1.44 | −0.17 | 74 % |
| 2025 | +2.09 | +3.05 | +1.63 | −0.46 | 70 % |

Read: the low-40 % column is negative in every year, and the top-20 % column is positive in every year. Where
those hours share a day (the last column), the two requirements conflict for any daily price. The Dec–Feb
column is the only part a winter cold-snap basis could supply. 2022's +36 is the Elliott days.

## 4. Pre-registered test for the file, if the owner still buys it

Fixed now, before the data is seen:

- **Series:** SNG daily (primary), zone-uniform, no blend weights; Transco Z4 reported as an alternate only.
  Transco Z5 is out of scope (Carolinas/Virginia delivery). Contract: `data/raw/gas-prices/licensed/README.md`.
- **Construction:** `hub / (1 − retention) + usage`, one config for all seven years, zero free parameters.
- **Prediction:** it reproduces §2's signature: 2019/2020 pass; 2023–2025 fail on C3a unless SNG − HH averages
  about ≥ +$1/MMBtu across Mar–Nov top-lambda days. If it did, the same days' night hours would rise too.
- **Bar:** all seven years pass C3a with no new C1 FAIL. Anything less is recorded as R.

## 5. Records

- Probe: `scripts/probes/_soco90_se_daily_replacement.py` (`--series hh|licensed`). Scratch outputs are not
  committed.
- Licensed-data contract and gitignore: `data/raw/gas-prices/licensed/README.md`, `.gitignore`.
- Matrix: note under SOCO `gas_daily_shape` (verdict unchanged, K). No ScenarioConfig field was added or tested.
- Retrievability: no bundle was produced.

## 6. Owner rulings on this FINDING (decision cards, 2026-09-29)

1. **Licence: "Don't buy (Recommended)"**. The fuel-price route for C3a is closed. The contract, gitignore
   entry and probe stay in the repo, inert.
2. **Next lane: "Zero-LP intra-day census (Recommended)"**. soco-91 measures, by hour of day, which unit sets
   price, at what offer and loading, against lambda. It checks for structure not already adjudicated and
   returns with a card. Zero LP.
