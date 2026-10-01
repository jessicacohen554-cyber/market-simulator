# FINDING — PJM-NEXT-3 phase 0: cards 1, 3 and 4 (zero LP) (2026-09-26)

Keeper `2026-09-25-pjm-next-2-joint` (bundle `results/calibration/pjmnext2_joint_span`). **Zero LP** — committed
payload/bench/hourly sidecars and fleet-only rebuilds of the keeper recipe (`replay_keeper.run_year_kwargs`,
`pjm_da_virtual_bids` off: a demand-side overlay, inert for fleet, fuel and offers). None of the three cards reaches a
solve: no admissible lever is ready. Card 2 (Montour/Brunner Island routing) is the session's solve —
`docs/PRECOMMIT-pjm-next-3-card2-unit-fuel-routing-2026-09-26.md`.

## Card 1 — CC_REGULAR 2024 −10.07 TWh: the east cost stack against a compressed W→E price gradient

**Where (bench plants, model − EIA-923, TWh, 2024):** EMAAC −5.53, SWMAAC −5.11, Dominion −4.82, AEP −2.08 against
Central PA +3.78, ComEd +3.53. Every named EMAAC/SWMAAC under-runner is in a RGGI state (NJ: Linden, Red Oak, Bergen,
Sewaren, Woodbridge, Newark, West Deptford; DE: Hay Road, Garrison; MD: Key −2.78, CPV St Charles −1.52, Wildcat
Point −0.81), while the PA plants inside the same zones over-run (Fairless +0.96, York +0.85, Bethlehem +0.72,
Ironwood +1.08) and so do ComEd's (Kendall +1.38, CPV Three Rivers +1.12).

**How (hourly, model vs CAMPD):** the under-runners are ON most hours but part-loaded — CF when on 33 vs 72 % (Key),
40 vs 68 (CPV St Charles), 54 vs 76 (Red Oak), 56 vs 72 (Doswell). Commitment is not the defect; the econ tranches
sit above the clearing price.

**Why (fleet-only offer decomposition, 2024 CC_REGULAR econ tranches, cap-weighted):**

| zone | gas $/MMBtu | econ HR | mc $/MWh | mc − gas×HR − VOM | model zone price |
|---|---|---|---|---|---|
| Central PA | 2.08 | 8.45 | 21.8 | 2.2 | 29.3 |
| ComEd | 2.34 | 8.35 | 23.3 | 1.7 | 28.0 |
| Dominion | 3.11 | 8.50 | 28.8 | 0.4 | 30.1 |
| **EMAAC** | 2.34 | 9.33 | **34.5** | **10.6** | 30.5 |
| **SWMAAC** | **3.19** | 8.53 | **38.2** | **9.1** | 30.6 |

- The EMAAC/SWMAAC residual is the RGGI allowance adder (0.43 t × $22.83 = $9.7/MWh; `pjm_rggi_allowance_pricing`,
  cell `K`, per-generator state membership — structurally correct).
- SWMAAC and Dominion gas is the **EIA N3045 state-average delivered-to-electric-power** basis (MD +$0.95, VA +$0.63
  over HH in 2024, vs PA −$0.14; `data/raw/pjm_zonal_gas_hub.csv`) — an average that includes firm-transport
  reservation charges, not a commodity marginal price. Keys/CPV St Charles/Wildcat Point all read exactly $3.19.
- The armed mid-curve surface is **not** the cause: its floor binds on 0–42 % of CC econ hours and lifts the
  cap-weighted bid by < $1 except the top rung (+$3.2).
- Actual hub spreads (DA, 2024): N. Illinois $25.5, Western $33.8, Dominion $34.1, NJ $27.7 — the model's ComEd →
  Dominion spread is $2.1 (≈ ¼ of actual). The east plants pay a real $10–16/MWh cost premium the model's east
  prices do not carry.

**Killed:** availability (units on the right hours), heat rate (`measured_cc_heat_rates` `K`), mid-curve floor
(above), seam price level (card 4). **Closed routes, not re-tested:** AP South cut (`I`, pjm-134), Dominion sub-zonal
congestion (pjm-137), RGGI (`K`), measured interface limits (`K`).

**No lever is ready.** Two named candidates, both for the owner:
1. **Marginal vs average gas in MD/VA** (rule 14 misalignment argument): replacing the state delivered average with a
   hub commodity series (Transco Z5/Z6, Cove Point/Dominion South). **Data-blocked** — the repo carries no daily
   PJM-area hub commodity series (only HH daily + N3045 state averages). Size if SWMAAC gas sat at the PA level:
   econ mc −$9.5/MWh, enough to close most of SWMAAC's −5.1 TWh.
2. **W→E congestion the 8-zone network cannot form** — the same object pjm-137 parked for Dominion, now measured
   for the whole east (spread ¼ of actual). A topology change, not a parameter.

## Card 3 — COAL_BIT 2021 +20.7 TWh: coal loads too high when on, because its econ rung clears ahead of every CC

- Bench plants carry +17.8 of the +20.7 TWh; the largest are survivors: Rockport +3.57, Gavin +1.84, Keystone +1.52,
  Fort Martin +1.34, Conemaugh +1.23, Clifty Creek +1.16, Amos +1.10.
- **On-fraction matches actual** (Rockport 0.65/0.57, Keystone 0.95/0.94, Conemaugh 0.86/0.86, Amos 0.83/0.84);
  **CF when on is ~10 points high** (Rockport 57/37, Keystone 57/47, Fort Martin 73/58, Clifty 55/44).
- 2021 P1 bids, cap-weighted: COAL_BIT econ **$32.9** (floored by the mid-curve on 63 % of hours), CC_REGULAR
  committed $30.1, CC econ **$37.0**, model price ~$38.8. The 23.8 GW coal econ rung is inframarginal in nearly
  every hour, so every committed coal unit runs near full.
- **Not seasonal** — H1 +8.8 / H2 +9.0 TWh (2021) — so the late-2021 coal-stockpile conservation story does not
  explain it (`coal_fuel_inventory` stays `U`; it raises outside MISO anyway).
- **Why the identification is missing:** the mid-curve surface that prices coal econ is derived from PJM's own
  offers for **2023–2025 only**; 2019–2022 read the **pooled** ladder. pjm-170 already showed the coal passthrough
  sigmoid is centred $1.18/MMBtu below its model-consistent crossover (a second pre-2023 mis-grounding).
- **Follow-on card (measured, admissible):** fetch PJM DataMiner `energy_market_offers` for 2019–2022 (verified this
  session: 2021-06 pages stream normally) and derive year-own mid-curve tables for those years with the existing
  `scripts/data/derive_pjm_offer_midcurve.py`. Rule 23: a re-derive on a source-data update (new years), the
  2023–2025 tables unchanged. Cost: a multi-GB gitignored corpus fetch + derive, then a 7-shard span.

## Card 4 — pre-2023 price over-shoot: the named cause is inert; the residual is the flat-stack trough

- **The reference-price interface freeze cannot reach the LP.** `PJM_SEAM_LADDER_BY_YEAR` now covers every year
  2019–2025, and pjm-173 proved the measured seam ladder replaces the gas × heat-rate seam price (80/80 seam rows
  unmoved under the F-A repair, 2022). F-A itself is repaired in `neighbor_price.py` (pjm-172).
- **What the over-shoot is (payload `lmpDeltaHr` × system hourly, load-weighted):**

| year | mean gap $/MWh | trough (load deciles 1–8) | peak (9–10) | bottom-decile implied HR model / actual |
|---|---|---|---|---|
| 2019 | +3.26 | **+4.56** | −1.97 | 9.00 / 6.28 |
| 2020 | +4.31 | **+4.91** | +1.88 | 9.25 / 6.05 |
| 2021 | +1.76 | +2.41 | −0.82 | 8.32 / 6.76 |
| 2023 | +1.82 | +3.80 | −6.08 | 9.77 / 6.96 |
| 2024 | +0.12 | +2.50 | −9.42 | 10.30 / 7.28 |

  The trough leg is positive in every year. 2019/2020 fail C3a because their peak leg is small (mild, low-scarcity
  years), so nothing offsets the trough surplus. This is the year-invariant flat-stack signature pjm-171 measured,
  whose frontier is owner-closed (`diurnal_price_amplitude` `G`). **Phase 0 stops here** — no measured
  identification exists for a two-ended repair.

## Retrievability

No bundles. Probe scripts are scratch; every number above is in this doc.
