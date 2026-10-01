# FINDING — pjm-h21 Card D: the CC volume defect is WHERE, not HOW MUCH (2026-09-24)

**Zero LP.** No PRECOMMIT, no shard. The lane stops at phase 0 because no admissible lever is ready
to solve (§5). Keeper unchanged: `2026-09-23-pjm-h19-dbs-span` + folded touchpoint.

**Owner ruling on pjm-h20, recorded first:** do not promote. `2026-09-24-pjm-h20-cardc-{span,touchpoint}`
were pruned (`prune_iso_runs.py --iso PJM --keep 2026-09-23-pjm-h19-dbs-touchpoint --force-uncite`).
`audit_keepers --iso PJM`: 0 failures.

Inputs: bench `frontend/data/backcast/bench/PJM/<y>.json.gz` (CAMPD hourly shape, EIA-923 net level);
keeper payloads; pjm-h20's six shard legs (`unit_hourly`, `floors`), read from shard SHAs
`30a0fcc5 196a2016 3ee80dfc e7cdb7ef 34e34286 61c3c77f` (provenance only); pjm-146's two payloads
from git at `25dd3b3d`. Probes: `scripts/probes/pjm_h21_cardd_phase0.py`,
`scripts/probes/pjm_h21_cardd_zonal_phase0.py`. Artifacts: `results/calibration/_pjm_h21_cardd_phase0.json`,
`_pjm_h21_cardd_zonal_phase0.json`, `_pjm_h21_cc_heat_rate_census.csv`.

## 1. Answer

**The keeper's CC class total is right because two zonal errors cancel.** EMAAC CCs run too much,
Dominion CCs run too little. The level form (pjm-h20) then removes the plant cost differences that
were partly holding EMAAC back, and the EMAAC error roughly doubles.

CC_REGULAR, model − actual, TWh (bench plants):

| zone | 2020 keeper → arm | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **EMAAC** | **+12.9 → +25.2** | +14.3 → +24.4 | +13.2 → +22.3 | +11.8 → +16.0 | +13.8 → +18.7 | +3.8 → +16.4 |
| SWMAAC | −2.7 → +3.5 | −1.9 → +3.3 | −3.8 → +3.0 | −0.5 → +4.0 | −3.1 → +4.6 | −6.4 → +4.6 |
| **Dominion** | **−10.5 → −1.5** | −4.4 → +1.4 | −1.7 → +2.7 | −13.7 → +1.1 | −12.3 → −2.5 | −4.0 → −0.3 |
| all other zones | +0.9 → +13.8 | +1.9 → +11.2 | +12.4 → +11.5 | +6.1 → +11.0 | +2.5 → +6.0 | +9.2 → +11.6 |

The same split by plant: ranked by actual capacity factor, the **high-CF third is within ±1 TWh of
actual in the arm every year**; the **low-CF third is +21 to +29 TWh over**. Even the keeper runs the
low-CF third +4.7 to +14.8 TWh over. Low-CF plants are concentrated in EMAAC (6.8–7.1 GW of that third).

## 2. Candidates killed (measured)

| candidate | result |
|---|---|
| Heat rate | Measured CAMPD operating rate vs model, by CF third: **0.99–1.01** everywhere; ordering preserved (fleet 7.165 model vs 7.149 measured; 62 of 69 plants pass the boundary guard). `measured_cc_heat_rates` would not move this. |
| Derate / capacity | Model summer p99 available CC capacity is **below** CEMS summer p99 every year (e.g. 47.0 vs 49.1 GW 2020; 53.8 vs 55.0 GW 2025). |
| Commitment floor count | `cc_mustrun_per_plant` floor hours (6,400–6,584 cap-wtd) are **fewer** than actual on-hours (6,857–7,245). Floor-while-actual-off is 3.2–6.0 TWh, and it is identical in keeper and arm, so it cannot explain the arm's move. |
| Seam exports | Model physical generation is within +3 to +15 TWh of EIA-930 net generation. Model net exports are **smaller** than EIA-930's in 2020–24 (e.g. 30.6 vs 39.9 TWh 2023). |
| Load-shape / trough | Arm CC surplus is flat across load deciles (+3 to +6 GW in each), ~40 % at night. Not a trough or peak object. |
| Winter gas spikes | Keeper EMAAC over-run is flat across months (~1 TWh/month). |

## 3. Why the level form makes it worse (code, not inference)

`offer_surfaces._pjm_midcurve_context` builds the target as
`implied_HR(bin, share) × (Henry Hub daily + one PJM-wide basis)`. Every CC econ rung gets the same
curve. The keeper's plant-level EIA-923 delivered gas (`gas_plant_monthly_fuel_pricing`), zonal basis
(`pjm_zonal_gas_basis`) and heat-rate spread no longer reach those rungs. Mean econ bid by CF third in
the arm: low-CF $14.96, high-CF $16.23 (2020) — the least-used plants bid **cheapest**.

**Consequence for any future level form:** as built it cannot be structurally correct. PJM's offer
corpus is masked, so it cannot identify plant-level differences. A re-test would first need a
construction that keeps each plant's own fuel cost (e.g. apply the measured curve's *shape* to the
plant's own cost). That is a design choice for the owner, not a lane default.

## 4. The two halves of the keeper's locational error

**Dominion (under):** already located by pjm-137. Dominion's real price carries sub-zonal congestion
($9–28/MWh in CT hours) that an 8-zone network cannot reach. Model zonal prices are almost flat
(max spread < $1.30/MWh in 2020 and 2023). Route **closed by measurement**; not re-opened.

**EMAAC (over): one measured candidate — RGGI.** The keeper does not charge RGGI allowances
(`pjm_rggi_allowance_pricing=false`; `state_carbon_pricing` cell `O`). NJ, DE (EMAAC) and MD (SWMAAC)
are RGGI members; VA was in 2021–23. pjm-146 tested it only at class level. Per zone, from its own
payloads (on the older pjm-143b keeper):

| EMAAC CC, model − actual | 2023 | 2024 | 2025 |
|---|---|---|---|
| pjm-146 control | +6.5 | +11.5 | +1.6 |
| pjm-146 RGGI arm | −5.2 | −6.1 | −9.5 |
| RGGI effect on EMAAC | −11.7 | −17.6 | −11.1 |

So RGGI hits the right zone, at about the right size for 2023–24, but overshoots (EMAAC ends short),
and it leaves Dominion's under-run in place. That is why pjm-146's class-level CC fell 10–15 TWh.
"Too elastic" was really "right zone, but the offsetting Dominion error is still there".

## 5. Why the lane stops here (rules 1/13/14)

- **No lever is ready to solve.** RGGI inputs cover membership for 2021 and 2023–25 and prices for
  2023–25 only (`capacity_market.RGGI_MEMBER_STATES_BY_YEAR`, `fuel_trajectories.PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE`).
  A six-year arm (rules 16/34(c)) needs 2020 and 2022 membership rows and 2020–22 auction prices
  first. That is a data build, not a solve.
- **Predicted outcome, stated ex ante:** RGGI on the current keeper cuts EMAAC+SWMAAC CC by roughly
  11–18 TWh while Dominion stays −4 to −14. Class CC_REGULAR would land roughly 8–15 TWh under actual
  in 2023–24 and likely FAIL C1, as pjm-146 did. It is structurally right and would still regress.
- **Level form:** do not re-test until (a) the construction keeps plant fuel cost (§3) and (b) the
  zonal split is addressed.
- `pjm_ct_measured_max_reprice`: not touched (pjm-123 still open).

## 6. Owner decisions needed

1. **RGGI, full span?** Build the 2020–22 RGGI inputs (zero LP), then run six shards of the current
   keeper + `pjm_rggi_allowance_pricing`, knowing C1 CC will likely fail. Structurally faithful;
   expected to cost CALIBRATED.
2. **Level form redesign?** Whether a plant-cost-preserving level form is worth building.
3. **Dominion** stays parked under pjm-137 unless you want sub-zonal congestion revisited.

## 7. Retrievability

No bundles produced. The pjm-h20 per-year legs used here were read from shard branches
`claude/pjm-h20-cardc-2020 … -2025` (still present; a session cannot delete them — HTTP 403).
pjm-h19's shard branches are already gone.
