# FINDING — soco-82: the 2019 COAL_BIT gap is out-of-merit conduct by Southern's OWN dispatch cost; the perunitdark drift is F1's retiree append (zero LP)

Lane soco-82, 2026-09-27. Keeper at the time of writing: `2026-09-27-soco81-coal-incremental-hr`. Probe:
`scripts/probes/_soco82_dark_drift.py` (modes `drift`, `greedy`, `lambda`).

## 1. The perunitdark drift, attributed byte-exactly (rule 23)

- **What:** re-deriving `data/raw/campd-unit-outages-perunitdark-SOCO.csv` at HEAD adds 44 coal windows and drops none:
  Wansley 6052 (37, 2019–2022), Gorgas 8 (4, 2019) and Hammond 708 (3, 2019). All 44 rows are `capacity_source = observed_peak`.
- **Why:** F2 `5ff0cb9cb` derived the committed file at 2026-09-24 15:53 UTC. F1 `31e54d8a5` landed at 16:31 UTC and appended
  the SOCO BAs to `eia860_generator_retired_within_window.parquet`, which the deriver loads into its plant universe.
- **Proof:** HEAD's deriver, run with the pre-F1 retiree parquet swapped in, reproduces the committed CSV byte-for-byte.
- **Reach:** Gorgas and Hammond are in no SOCO LP fleet, so their windows are inert. Wansley is in the 2019–2021 fleets,
  where the keeper models it at 0.914 availability against a CEMS record showing it dark most of each year. The
  consequence is 2021: the keeper runs Wansley at **5.58 TWh against ~1.1 TWh actual**.
- **Action:** repaired in this lane (PRECOMMIT-soco-82). It does not help 2019 COAL_BIT (−3.99 → about −4.05 pp).

## 2. Southern Company's own system lambda (FERC-714 Part II Schedule 6)

- **Source:** PUDL raw FERC-714 archive, Zenodo record 21738524 (v32.0.0), `ferc714.zip`, sha256
  `a2797ab2fdc3900d14930ab2b6436d49a2522ededa9069208df75cc7fb9d2d67`. The CSV era covers 2006–2020; 2021+ is in the
  XBRL zips of the same record. `www.ferc.gov` returns 403 here.
- **Respondent:** 253, Southern Company, EIA utility 18195; hourly, CPT.
- **Status:** scratch only, not committed. This is a candidate intake; see §5.

| year | keeper P1 price mean / median | Southern lambda mean / median | hourly r |
|---|---|---|---|
| 2019 | $30.21 / $31.58 | $25.72 / $26.27 | 0.614 |
| 2020 | $25.07 / $26.03 | $20.90 / $18.75 | 0.539 |

- The model's price is **$4–5/MWh above** Southern's reported marginal cost. A missing price level therefore cannot
  explain the coal under-run: a higher price is what the model already has.
- SOCO's rubric treats price as unscored "because no measured reference exists" (owner card S2, rubric v3.8). This
  series *is* a measured reference for SOCO's marginal cost. It is not an LMP, and it is published hourly.

## 3. The 2019 cyclers against that lambda, in their own CEMS-synced hours

Southern's Schedule VI formula: `λ = [(2aP + b)(FC + EC) + VOM + FH] × TPF`. That is incremental heat rate × marginal
replacement fuel cost, plus VOM, in-plant fuel handling and transmission-loss penalty factors.

| plant (2019) | CEMS TWh | synced h | model offer (avg HR) | lambda < offer, share of synced h | at incremental HR (measured ratio) | TWh produced while lambda < incr. offer |
|---|---|---|---|---|---|---|
| Barry 4/5 | 4.63 | 8,312 | $37.3 | 97 % (median −$12.2) | $34.2 (0.904): 94 %, median −$9.0 | **4.33** |
| Wansley 1/2 | 2.27 | 3,781 | $36.9 | 93 % (median −$8.1) | $33.7 (0.900): 85 %, median −$4.8 | **1.81** |
| Gaston 5 | 3.35 | 4,741 | $47.1 | 99 % (median −$20.4) | — (already on a measured must-run floor) | — |

**The model's inputs are faithful:**
- Barry's fuel ($3.08/MMBtu) and Wansley's ($2.97) match their own 2019 EIA-923 receipts ($3.16 and $3.08).
- SOCO carries no offer-curve tuning: every band is 1.0.

**The measurable terms of Southern's formula do not close it:**
- *Replacement fuel cost is refuted on the data.* EIA-923 Page 5 gives Barry's 2019 spot coal at $3.48 against $3.03
  on contract (spot is dearer). Wansley bought only spot, at $3.08.
- *Incremental heat rate is not enough.* Even at each plant's measured 2019 ratio (~0.90), both plants stay $5–9/MWh
  above Southern's lambda in their median synced hour.

**Conclusion:** Barry and Wansley ran in 2019 at a variable cost Southern's own economic dispatch reports as out of
merit. The driver is non-economic, and this lane cannot identify it from public data. Candidates are fuel-contract
obligations (the take-floor carrier is G, soco-80), local reliability commitment, or unit-commitment effects: λ is the
marginal unit's cost, and committed units at minimum load are not marginal.

An offer lever would have to push these plants below a measured marginal cost to reproduce the conduct. That is the
fitted mechanism rule 1 forbids. The 2019 COAL_BIT row has **no admissible economic lever**, and the remaining routes
are governance decisions for the owner.

## 4. Lever queue status (§5.8)

- Every queue entry that reaches the cyclers is adjudicated (R/I/G) or owner-refused.
- This lane adds two zero-LP refusals, both recorded in PRECOMMIT-soco-82 §4:
  - replacement fuel cost: wrong sign;
  - incremental HR on cyclers: re-confirmed insufficient against a measured price, not only refused on physics.

## 5. Decisions for the owner (asked as decision cards in-session)

1. **How to carry 2019 COAL_BIT.** It is SOCO's only failing scored row, and §3 shows no admissible economic lever.
2. **Whether to intake FERC-714 system lambda** as SOCO's measured price reference (2019–2020 CSV now; 2021+ XBRL).
   Either reported-only, or scored under C3. If scored, the §2 bias implies C3a would currently read about +17 % (2019)
   and +20 % (2020).
