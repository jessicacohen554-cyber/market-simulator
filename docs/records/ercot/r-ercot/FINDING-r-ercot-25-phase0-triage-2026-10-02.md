# FINDING — R-ERCOT-25: phase-0 triage of the open gates on keeper r-24 (zero LP)

Session R-ERCOT-25, 2026-10-02. Keeper `2026-10-02-r-24-ordc-published` (bundle
`results/calibration/r_ercot24_span`, 2019–2025). Zero LP. Every number below comes
from the committed bundle's sidecars (`hourly/unit_marginal_<Y>.parquet`,
`run_config_<Y>.json`) or from `data/raw/coal-receipts/` at `main` 00648e6e.

## Headline

**No arm in this session.** The triage finds exactly two admissible, zero-DOF,
structurally real levers with a predicted favourable move on an open gate:
L1 (ERCOT arm of `coal_fuel_inventory`, 2022 C1) and L2 (West import-direction
rating, 2024 C3a). Both are already chartered to the close-out desk's
`closeout-ERCOT` lane (session_014k634JEUUTjkccEd9DZCYJ, branch
`claude/closeout-ercot-wave1`, launched 2026-10-02 05:13Z, plan
`docs/backcast-closeout-plan-2026-10.md` §3.5 steps 0b/1/2/3), whose full-span
solves the desk holds until the W0 EIA-860 foundation lane merges (every ERCOT
year's fleet changes under W0; a pre-W0 span would be paid twice). Arming L1 here
would duplicate that lane and spend seven shards W0 will invalidate. Every other
`U`/`O` cell that touches an open gate is inert on ERCOT, the wrong sign, or not
a lever. The 2019/20 route is the owner's R-7 account action; 2023 is R-6
(rubric lane `closeout-C`).

## 1. Per-gate triage

| Gate (r-24) | Candidate (cell) | Admissibility (rules 1/13/14/19) | Zero-LP expected move | Decision |
|---|---|---|---|---|
| 2022 C1 CC_REGULAR −10.07 (COAL_PRB +5.79) | `coal_fuel_inventory` (U) — L1 | Admissible: R-3 / D-P7 ruling (EIA-923 receipts + stock envelope as a take *ceiling*, never the burn) | Martin Lake 6146 model 16.69 TWh vs fuel-feasible ≈ 12.6 (closeout research §4); Coleto 6178 4.31 vs ≈ 2.7 → CC −10.07 → ≈ −4..−6 (PASS) | **closeout-ERCOT owns it** (step 0b census + PRECOMMIT; solves after W0) |
| 2022 C1 CC | CC capacity family: `cc_capacity_reconcile`, `cc_summer_derate_reconciled_basis`, `cc_winter_capability_basis`, `cc_nameplate_summer_derate`, `cc_block_summer_rating` (all U) | Structural, but the gate is not capacity-bound | 2022 CC_REGULAR dispatched 124.67 TWh against 211.7 TWh available; **0 h** with the fleet ≥ 95 % of available cap (2019: 0, 2020: 0, 2024: 15). Extra CC capacity cannot add CC energy; less capacity moves it the wrong way. Confirms R-ERCOT-21 §1 ("CC is priced out, not short") | **Not a lever for this gate**; cells stay U (W0's seasonal capacity basis supersedes the family) |
| 2022 C1 / 2019–20 C1 | `coal_captive_marginal_fuel_price` (U) | Admissible in form (NWPP construction) | Census below: **zero** ERCOT coal plants with 0 < captive share < 1 in any year 2019–2024 → byte-inert | **U → I** (census, this FINDING §2) |
| 2019/20 C1 COAL_PRB −10.48/−11.83, CC +8.85/+10.21; C3b 0.228/0.209 | 60-Day SCED/DAM 2019–22 per-plant coal offer tables (closeout L5) | Admissible (ercot-168 construction, rule 23) — data gated | Bounded by R-ERCOT-3: the whole −10.5/−11.8 TWh object | **Owner action**: R-7 ruled Yes; the ERCOT account must be re-opened before any lane can fetch |
| 2019/20 | `coal_fuel_inventory` (L1) | — | Stocks ample 2019–20 (Fayette 1.3–1.5 Mt): the ceiling does not bind | Inert in these years (part of L1's full span anyway) |
| 2019/20 | `coal_offer_level_rebasis` (R) | DO-NOT-REDO; wrong sign (fuel-indexing raises 2019–20 coal offers) | — | Not reopened |
| 2019/20 C3b; 2024 C3a | `ct_peaker_committed_measured` (U; ERCOT committed 1.48 vs measured phys 1.022, caiso-241 census) | Would need an ERCOT-scoped field (rule 25); lowers CT committed offers ≈ 31 % | CT_PEAKER committed tranches are marginal in 161/141 h (2019/2020) but **580/523 h (2024/2025)** — the cut lowers prices most in the years already under-priced (2024 C3a −11.4 % FAIL, 2025 −9.4 % at the edge) | **Not armed**: net adverse on open gates; stays U with the census in the cell |
| 2024 C3a −11.4 % | West import-direction rating (L2; `internal_congestion_split` G stays closed for sub-zonal) | Admissible as a rating repair (ercot-234 precedent), owner D-P "Yes, L2 only if its census clears" | West LZ premium +$1.30 system-LW, model 0.00 every hour → ≤ 4 pts | **closeout-ERCOT owns it** (step 2 NP6-86 census, step 3 arm after W0) |
| 2024 C3a | `gas_basis_measured_by_year` (U) | Rule 19: ERCOT prices gas on `ercot_zonal_gas_basis` (true in every `run_config_<Y>.json`), not the scalar the field replaces | Inert by its own one-line test (`gas_plant_monthly_fuel_pricing` false but the zonal hub path supersedes the scalar) | Not a lever; cell unchanged |
| 2024 C3a | `gas_electric_power_monthly_level` (U), `ercot_ep_gas_basis_monthly` (O) | Rule 19: same phenomenon as the armed zonal basis; ercot-254 built and left the monthly form default-off | — | DO-NOT-REDO without new evidence |
| 2024 C3a | `maxgen_emergency_tier_pricing` (U), `dynamic_reserve_requirements` (U) | Rule 17: no declared-window driver (closeout research §2: 0 h reach EEA-1); ERCOT's reserve inputs are already the measured AS series (R-ERCOT-13 lineage) | — | Not a lever; cells unchanged |
| 2023 C3a −24.5 %, C3b 0.385 | k=33 carve-out (owner hold) | R-6 ruled (2023 keeps its own config; a 2023-only configuration-exception caveat kind) | — | **closeout-C owns the rubric work**; not this lane |
| 2020 C3c 22/56 h (ledgered) | — | Non-downgrading (rule 22) | — | No action |

## 2. Captive-coal census (zero LP)

Definition as `data/fuel/captive_coal.py::classify_captive` (mine-mouth `TC`/`TR`,
`Coalmine State == Plant State`, `Purchase Type != S`), MMBtu-weighted over each
Texas plant's EIA-923 Page 5 lots:

| Year | Plants with 0 < captive share < 1 | Fully captive |
|---|---|---|
| 2019–2023 | none | San Miguel, Major Oak Power, Pirkey |
| 2024 | none | San Miguel, Major Oak Power |

(`coal_receipts_2025.csv` is not on disk.) The mechanism prices only mixed-source
plants, so it is byte-inert on every ERCOT year that has receipts.

## 3. What this lane does not do

- No solve, no new ScenarioConfig field, no PRECOMMIT: there is no admissible
  lever outside the two the desk has chartered elsewhere (handoff Task 2: "do not
  invent a lever").
- No promotion: the keeper stays `2026-10-02-r-24-ordc-published`.

## 4. Owner ruling (decision card, 2026-10-02)

Answer, verbatim: **"Cede to desk (Recommended)"**. This PR merges the triage (this
FINDING + two ERCOT matrix cells). There is no arm and no promotion, and the R-ERCOT
chain ends here with no R-ERCOT-26 handoff. The `closeout-ERCOT` lane carries L1/L2
after W0 merges. The 2019/20 route still needs the owner to re-open the ERCOT account
(R-7), and the 2023 rubric work stays with `closeout-C` (R-6).
