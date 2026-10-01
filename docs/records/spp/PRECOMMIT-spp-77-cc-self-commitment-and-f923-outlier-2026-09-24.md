# PRECOMMIT — SPP-77: is SPP gas CC self-committed (measured), and why do $147/MMBtu fuel rows reach the 2022 offers?

**Zero LP. Pushed before any new number below is read.** Base `f68160020fa0799eff408e1bd4b80f0cd7f5a017`.
Keeper `2026-09-22-hydro-5-spp-floor` (`hydro5_spp_floor_span`, 2023–25); rung
`2026-09-22-hydro-5-spp-rung` (`hydro5_spp_floor_rung`, 2019–22, stamped). Predecessors:
`RESULT-spp-76` §3–§6, `RESULT-spp-75` §2, `RESULT-spp-74` §6 (which already localized the MO
reference defect — this lane re-verifies it, it does not take it on trust).

## A. The fuel outlier

1. **Reproduce.** `fleet_only` rebuild of the rung's 2022 (`reconstruct_bundle_fleet`, one
   interpreter per year); monthly capacity-weighted CC fuel by plant; must show 2079 / 7296 at
   $147.15 and 55178 at $47.94 in Jan 2022.
2. **Root cause, three candidates, decided by the raw rows:** (i) the state reference is inflated
   (`N3045MO3` 2022-01); (ii) a post-screen nearby-pool fill from a bad donor; (iii) a real
   booked cost (Uri true-up) in the plant's own F923 print. Decided by reading the plants' own
   F923 Schedule-5 prints for Jan 2022 and the EIA state table row. If the plant's own print is
   ~$5–7 and the reference is ~$147, it is (i).
3. **Scan.** Every SPP year 2019–2025, every class: plant-month offer fuel > 3× that month's class
   median. Also every state reference cell in the EIA table, 2019–2025, as a ratio to (a) the US
   series and (b) the median of the other states in its Census division that month.
   **Discriminator, declared now:** a data error is a reference that is out of line with its
   *peers in the same month* (division median) AND contradicted by the plants reporting under it;
   a real event (Uri Feb 2021; New England winter; West Dec-22/Jan-23) moves the whole division
   together, so the ratio to the division median stays inside the band even when the ratio to US
   does not. The band reused is the declared `F923_GAS_PRICE_PLAUSIBILITY_BAND` (0.5, 2.0) — no
   new constant. If the scan shows that this discriminator catches a real regional event, or
   misses the MO cell, it is reported and the repair is NOT built.
4. **Admissibility.** A repair is admissible only as a change to the screen's construction
   (screen the reference against its division peers, fall back to the division median / US series),
   never a per-plant or per-cell override. It is shared infrastructure (`data/fuel/plant_prices.py`):
   every ISO whose recipe arms `gas_plant_monthly_fuel_pricing` + the screen is enumerated, and the
   fuel arrays of every ISO-year with **no** flagged reference cell must be byte-identical before any
   solve is considered.

**Prediction A:** (i) — the reference. The fixed screen moves 2022 CC_REGULAR up by **< 1 TWh**
(one month; January), so C1 COAL_PRB 2022 (+9.60, band ±8) stays out of band on its own. C4 gas
2022 moves < 0.02. **The fix is a real defect repair but does not move a failing row.**

## B. The missing driver

1. Search SPP MMU State of the Market reports (the committed `data/raw/spp-planning/transcriptions/
   ASOM_{2023,2024,2025}.txt`; earlier years from spp.org if reachable) for a **per-year** measure of
   gas CC self-commitment (MW, share of commitments, or share of CC energy self-committed /
   self-scheduled). Record report, page/figure/table.
2. If found, size it against the RT≤0 gap (SPP-75 §2: model CC+ST 3,548/1,767/426/277 MW vs measured
   3,507/3,229/2,070/2,176, 2019–22) and the C1 CC shortfall (−6.63 / −7.55 TWh in 2021/22).
   **Pass condition (declared):** the published measure must (a) exist for ≥ 3 of 2019–2022 at the
   same construction, (b) be gas-CC specific or separable to gas, and (c) be large enough that the
   self-committed CC MW at the SOM's own measure covers ≥ 50 % of the 2021–22 RT≤0 gap
   (≈ 1,800 / 1,900 MW). Fewer years, fuel-pooled only, or a share that cannot be converted to MW
   without a fitted scalar → **no admissible driver**.
3. If none: say so plainly, route, stop. The gas-commitment family stays dead (rules 1/17/19).

**Prediction B:** a published self-commitment measure exists but is **fuel-pooled or coal-dominated**
(the MMU's self-commit discussion is historically about coal), so it fails (b) or (c); if a gas figure
exists it is **flatter across 2019–22 than the model's CC commitment** (model CC+ST in RT≤0 falls
~13× from 2019 to 2022). Prior: no admissible driver → no shard.

## C. Build gate

Only if A.4 or B.2 passes: rule 19 enumeration, rule 21 DOF `--check`, rule 25, then seven
year-isolated shards (rule 36). Otherwise zero LP and nothing to promote.
