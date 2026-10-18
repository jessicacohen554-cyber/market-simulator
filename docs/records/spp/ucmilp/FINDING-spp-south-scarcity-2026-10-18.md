# FINDING — SPP-South scarcity under the UC arm (U4b): what the 7,177 MWh of unserved is

**Lane:** UC-SPP-SOUTH · **Date:** 2026-10-18 · **Branch:** `claude/uc-spp-south` · **Base:** `main` `4dc8d97d`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) under owner ruling R20 (`docs/uc-milp-program-plan-2026-10.md` §8.1).
**LP in this session:** zero. **`src/` change:** none. **Data profile:** `spp`.
**Evidence:** `RESULT-ucmilp5-spp-2026-10-18.md` (PR #7282) and its slim span `data/ucmilp5_spp_u4b_span/`; the U4b shard legs `claude/ucmilp5-spp-u4b-{2019,2022,2023,2025}` (`unit_marginal_<y>`, `dispatch/<y>_P1`, read by `git show`, nothing checked out); the keeper bundle `results/calibration/closeout_spp_nuc_span/` (`2026-10-03-closeout-spp-nuc-keeper`); the CEMS bench `frontend/data/backcast/bench/SPP/<y>.json.gz` (per-plant hourly CAMPD gross load, monthly CAMPD-gross and EIA-923-net GWh); EIA-930 SWPP hourly, sub-BA demand and per-counterparty interchange; SPP hub LMPs (`actual_lmp_hourly_zonal_SPP.parquet`); `data.commitment_demand.backcast_commitment_increment` (the U4b commitment basis, recomputed read-only).
**Tables behind every number:** `data/spp_south_scarcity_2026_10_18/` (`slack_hour_attribution.csv`, `implied_ns_transfer.csv`, `south_st_gas_unit_economics.csv`).

## 0. Headline

| rank | cause | MWh of U4b unserved | share | where |
|---|---|---|---|---|
| 1 | **Data artifact** — 2025-12-21 sits in a system-wide EIA-930 flat fill (BA demand 37,455, NG 7,243, WND 15,786 MW constant; South sub-BA 18,462 constant) | **3,623** | 50 % | 2025 (5 h) |
| 2 | **N→S corridor / South non-thermal side** — model South thermal already equals CEMS (net); reality's balance implies N→S **≥ 4.6 GW** vs the 3,400 MW link | **2,161** | 30 % | 2023-08-10 (5 h) |
| 3 | **South steam-gas commitment** — model South thermal below CEMS net by more than the slack; the gap is ST_GAS units on in CEMS, off in the UC | **1,393** | 19 % | 2019, 2022, 2023-09/10 (9 h) |

- Attribution order: data → thermal → corridor. Reversed (corridor first), rows 2/3 read **2,564 / 990**. The split between 2 and 3 is soft; the total of 3,554 non-artifact MWh is firm.
- **Two proximate conditions each close all 3,554 MWh on their own** (every one of the 14 non-artifact hours):
  - (a) the UC's South commitment demand is **670–2,030 MW below** the P1 South load (South's load-share of SPP's own DA MTLF error, R16 basis);
  - (b) South ST_GAS units that ran in CEMS and were uncommitted by the UC carry **520–2,115 MW net**.
  The UC window *does* see the zone balance and the 3,400 MW link (it is the production LP, `model/uc/window.py`). It just commits against a load that is too low, with no driver that keeps steam online regardless of that forecast.
- **Not a capacity problem.** Real South prices in these hours were $30–262/MWh RT, not scarcity. SPP-wide model thermal is 2.4 GW *below* EIA-930 fossil output at 2023-08-10 15:00, while North has headroom.

## 1. The 19 slack hours

All 19 are in SPP-South with N→S flow at 3,400 MW (`network_<y>`), South price $2,000 (VOLL).

| year | hours (model hour, local HE) | slack MWh | South commitment increment MW | South ST_GAS CEMS net / UC | South thermal (covered) CEMS net / model / keeper |
|---|---|---|---|---|---|
| 2019 | 5870 (09-02 HE15) | 137 | −1,133 | 2,575 / 1,687 | 13,325 / 12,212 / 13,112 |
| 2022 | 3206–07 (05-14), 6902–03 (10-15) | 761 | −669 … −1,684 | 3,013 / 1,845 (mean) | 10,580 / 9,961 / 11,067 (mean) |
| 2023 | 5317–21 (08-10), 6422–24 (09-25), 6759 (10-09) | 2,656 | −1,183 … −2,028 | 3,388 / 2,235 (mean) | 13,947 / 13,375 / 15,543 (mean) |
| 2025 | 8506–10 (12-21) | 3,623 | −2,174 … −2,892 | 1,527 / 1,759 | 8,147 / 9,733 / 10,681 |

- "Covered" = South thermal plants with a CEMS series (the bench covers ≈ 83 % of EIA-930 fossil energy). Model and keeper are taken over the same plant set.
- **CEMS gross → net:** each plant's own measured ratio of monthly EIA-923 net to CAMPD gross. Without it the thermal gap is overstated by 0.5–0.9 GW.
- The slack hours are not the South peaks. In the 30 highest-South-load non-slack hours of each year, U4b commits ST_GAS at CEMS level (2023: 4,311 vs 4,130 MW net) and the link runs below its limit. The shortfall shows up on **moderate-load shoulder days** with a large negative DA forecast error: May, Aug, Sep, Oct, and weekend days.

## 2. Q1 — units that ran in reality and were off in the UC

South ST_GAS/CC units with CEMS output and UC `u = 0` at the slack hours. Mean MW over the year's slack hours; CEMS gross; `on` = slack hours off-in-UC / slack hours.

| unit (plant) | 2019 | 2022 | 2023 | 2025 |
|---|---|---|---|---|
| **Seminole (OK) 2956**, ST 3×~507 | 851 (u 1/3) | **995** (0/3, 4/4 h) | **990** (0/3, 9/9 h) | — |
| **Wilkes 3478**, ST 3×294 | 159 (1/1 h) | 289 (3/4 h) | **600** (8/9 h) | — |
| **Muskogee 2952** gas ST 2×488 | — | 481 (2/4 h) | 322 (1/9 h) | — |
| Plant X 3485 | 272 (1/1 h) | 179 (2/4 h) | 166 (5/9 h) | — |
| Lieberman 1417 | — | 19 | 137 (8/9 h) | — |
| Mooreland 3008 / Arsenal Hill 1416 | 131 / — | 26 / 73 | 72 / 26 | — |
| Harrington 6193 (gas-converted ST) | — | — | — | 333 (5/5 h) |
| Knox Lee 3476 | — | — | — | 90 (5/5 h) |
| Redbud CC 55463 / Comanche CC 8059 / Thomas Fitzhugh CC 201 | — / — / 167 | — | — / 36 / — | 321 / — / — |

**This is year-round, not slack-hour specific.** CEMS online share vs UC online share (u > 0), 2023:

| plant | Seminole | Wilkes | Muskogee | Southwestern | Nichols | Cunningham | Jones | Plant X |
|---|---|---|---|---|---|---|---|---|
| CEMS on | 0.60 | 0.64 | 0.33 | 0.84 | 0.91 | 0.89 | 0.80 | 0.69 |
| **UC on** | **0.15** | **0.07** | **0.00** | **0.01** | 0.56 | 0.52 | 0.58 | 0.29 |
| keeper on (P1 mw > 0) | 0.43 | 0.56 | 0.46 | 0.65 | 0.95 | 0.58 | 0.91 | 0.70 |

- Same pattern in 2022 and 2025 (`south_st_gas_unit_economics.csv`).
- Seasonal campaigns are visible in CEMS. Seminole was off Jan–Mar 2023 and on Apr–Dec. Muskogee ran its summer block.
- CT is the other half of the composition error. U4b runs South CT_PEAKER at its cap (2,359 MW) in every slack hour, against 1,600–1,700 MW CEMS net.

## 3. Q2 — why the UC keeps them off

Cluster parameters from `uc_solve_log_<y>.json`, 2023 (all `integer: True`, `src = uc-params`). `integer_demoted_budget_pinned` is empty in every year, so **no unit is budget-pinned** (ruling (a) is not the cause).

| plant | n × pbar MW | mlf | ut h (p25 measured run) | dt h (class) | start $/unit | no-load MMBtu/h ($/h UC) | measured South-hub DA in its CEMS on-hours | model offer mc | on-hours with DA < mc | margin at measured DA, model costs |
|---|---|---|---|---|---|---|---|---|---|---|
| Seminole | 3 × 507 | 0.225 | **114** | 12 | 38,038 | 289 (731) | $30.4 | $32.3 | **63 %** | +$13.7 M |
| Wilkes | 3 × 294 | 0.137 | 66 | 8 | 16,188 | 176 (561) | $29.5 | $34.6 | **71 %** | +$2.9 M |
| Muskogee (gas ST) | 2 × 488 | 0.426 | 58 | 12 | 36,638 | 326 | $32.8 | $39.6 | **72 %** | — (never committed) |
| Southwestern | 4 × 107 | 0.152 | 52 | 12 | 8,044 | 128 (342) | $28.3 | $38.4 | **78 %** | **−$5.1 M** |
| Plant X | 1 × 411 | 0.301 | 81 | 8 | 22,605 | 90 (258) | $28.6 | $31.7 | 68 % | −$1.3 M |
| Nichols (control: committed) | 3 × 152 | 0.163 | 53 | 12 | 11,425 | 46 (107) | $28.2 | $27.5 | 57 % | +$7.5 M |

Decomposition, per driver:

- **Start cost / no-load.** Moderate per hour. They matter because the UC's demand view never shows a South need on these days: the increment is −0.7 to −2.0 GW (§1). Against that load, the cheapest way to cover the South is continuous CT plus coal already online. A $38 k start plus 114 h × $731/h no-load on a unit whose offer sits above the hub price two hours in three never pays back.
- **Min-up (`ut_h`).** The p25 of measured per-unit runs (UC-DATA-UT, ruling r13): 52–114 h. It is an amplifier, not the root cause. A long min-up makes a one-day commitment carry ~5 days of operation. The same long runs are what the real fleet chose, which is a conduct signature (below).
- **Min-down (`dt_h`).** 8–12 h, the class value. Not binding at the slack hours: these units were off for weeks.
- **mlf.** 0.14–0.43, measured. A low mlf makes commitment *cheaper*, so it is not a cause.
- **Offer / mc.** The decisive economic fact. In **57–85 % of the hours these units actually ran** (2019–2025), the measured SPPSOUTH_HUB DA LMP was below the model's own offer. At measured prices and model costs, Southwestern, Muskogee, Wilkes and Seminole lose money in several years (2019, 2025). Two caveats: hub ≠ node (the OKC/Tulsa FCAs sit inside the South), and offer bands are the rule-1 channel.
- **Availability / outage.** Not the cause. The keeper carries the same units at full availability in those hours (Seminole `cap_mw` 957 MW, Wilkes 588 MW).
- **CT relaxation.** CT clusters are `integer: False` under `uc_integer_scope = physics`, so the UC commits them fractionally with no start lumpiness. That gives a structural tilt toward CT over steam on a short need. It is physics-consistent for quick-start units (rule 18), but it is why the composition flips (§2).

**What the keeper's floor stood in for.** The keeper floors these plants through `st_gas_mustrun_per_plant` (R5). Its rule-17 triple (`PRECOMMIT-spp-64` §2):

- Driver: SPP's gas-steam fleet is **100 % EIA-860 Sector 1** (OG&E 2,888, PSO 2,111, SPS 1,772, SWEPCO 1,543 MW), i.e. vertically integrated utilities self-committing for native load.
- Window: the plant's measured `online_frac` placed in the top system-load hours (Seminole 0.616, Wilkes 0.766, Southwestern 0.773, Muskogee 0.648).
- Forward story: re-derive from each CAMPD vintage.

The UC arm removes the floor (rule 19) and keeps **no commitment driver for self-commitment**. Its only commitment signal is a least-cost schedule against the MTLF forecast. That is the missing driver. The evidence above (long runs, seasonal campaigns, operation below hub price) is the self-commitment signature. The SPP MMU documents self-commitment as roughly half of SPP generation MW (≈ 70 % in 2015 → ≈ 50 % in 2019; DA "self-commit" status 30 % of capacity commitments in 2018). The MMU attributes it to long start times and risk-averse utility practice ([MMU self-commitment whitepaper, 2019](https://assets.documentcloud.org/documents/6573451/Spp-Mmu-Self-Commitment-Whitepaper.pdf); [Utility Dive summary](https://www.utilitydive.com/news/self-committing-coal-suppressing-southwest-power-pool-prices-by-2mwh-mar/568828)). These are published, not in the repo corpus, and mostly about coal; the steam-gas share is not broken out. No RMR or voltage designation for these plants was found in the corpus. That is not shown here and is not claimed.

**Is the driver measurable and forward-reproducible (rule 13)?**
- **Yes for its parts.** EIA-860 Sector is a published per-plant field. `online_frac` and `committed_pct` re-derive from CAMPD (the forecast-emission-rate family). Self-commit status is a declared market-design object.
- **No for the replay forms.** CAMPD on/off hours as the commitment window were killed by SPP-46. A P0-pattern window was killed by SPP-44. Those stay dead.

**The keeper over-covers.** At the Aug-2023 slack hours the keeper runs South ST_GAS 4.75 GW against 3.88 GW CEMS net. At the 2023 South peaks it runs 5.55 vs 4.13 GW. Its floor is partly absorbing the corridor-side gap of §4. Whatever replaces it should not be sized to the keeper's no-slack outcome.

## 4. Q3 — the N→S limit

- **3,400 MW is the registered value** (`iso_configs.py::_spp_config`, `_ns_corridor_ttc`). It is the rule-14 reconciled figure from lane SPP-53: the binding-hours-weighted median of `L_f / psi_f` over 12 identified corridor flowgates, using 2026 RTBM effective limits and 2023–25 hub-spread sensitivities.
- **Honest width:** 2,645 / 3,681 / 11,121 MW in leave-one-year-out fits.
- **No SPP-published N↔S interface rating exists.** ITP constraint ratings are CEII (`FINDING-spp-13` §0; `FINDING-spp-53`). The "> 6,000 MW SPP↔MISO" figure is a seam rating. There is no seasonal published value to compare against. The value is static and symmetric (S→N reading 4,206 MW).
- **What reality implies at the slack hours** (`implied_ns_transfer.csv`). Implied N→S = measured South sub-BA load + measured South-side exports − South CEMS net − model South non-covered thermal − model South wind/solar/hydro/biomass. South-side exports are the ERCOT DC ties (+733 to +833 MW in every slack hour), EPE, PNM and PSCO (Lamar). AECI/MISO/SPA legs are bounded as all-North → all-South.

| hours | implied real N→S, low–high bound |
|---|---|
| 2023-08-10 (5 h) | **4,585–6,205 MW** — above 3,400 even at the low bound |
| 2019-09-02 | 3,487–4,035 |
| 2022, 2023-09/10 | 2,303–5,129 (straddles) |

- The real corridor was congested in most of the same hours. RT South − North hub spread: 2023-08-10 +$30 to +$52 in all 5 h (2023 p90 $20.5), 2019 +$31 (p90 $10.5), 2022-10-15 +$73 / +$163 (p90 $56). Not congested on 2022-05-14 (+$3 / −$4) or 2023-10-09 (+$3). So the real system was N→S-constrained while moving more than 3,400 MW, or while South wind ran higher than the model's reanalysis zonal shape gives it. The model puts only 22 % of SPP wind in the South at 2023-08-10 15:00, against 50 % annually. **This finding cannot separate the two.** No hourly zonal wind measurement exists in the corpus; `spp-wind-shape` is reanalysis.
- **Zone boundaries are consistent.**
  - Model South demand share equals the measured sub-BA share {CSWS, GRDA, OKGE, SPS, WFEC} to the third decimal in every slack hour.
  - The fleet map is by state (`_SPP_STATE_ZONES`), and the bench plant zones agree.
  - One mismatch, stated: the measured net interchange is spread over zones **by load share** (model South demand − sub-BA South = 0.49–0.54 × Total interchange in every hour). The ERCOT DC ties, EPE, PNM and Lamar are physically South. Zoning by counterparty would put **+500 to +600 MW more** export on the South in Aug 2023 (e.g. 1,052 vs 501 MW at 2023-08-10 16:00). That *worsens* the South balance, so it is not a fix for the shortfall. It is a rule-14 alignment item in its own right.
- Bench plant-code mismatches (GREC 165, Anadarko 3006, Hobbs 56458 carry 1–7 MW bench nameplates against 400–540 MW model capacity) are excluded from the covered set on both sides.

## 5. Proposals (owner/desk decisions; nothing lands from this lane)

**P1. ST_GAS self-commitment as a UC-native commitment requirement, replacing the P1 floor.**
- Mechanism: under `unit_commitment_milp`, Sector-1 ST_GAS clusters carry `u ≥ 1` over each plant's `online_frac` share of the window's hours. Placement follows the same model-system-load ranking as SPP-64. Level is the measured mlf (P5-of-online), not p25.
- Rule 19: it replaces `st_gas_mustrun_per_plant`. Never stacked; the UC already refuses the floor family.
- Rule 13: the inputs are EIA-860 Sector plus CAMPD `online_frac`/`committed_pct`, the same admissible triple as R5. No CAMPD-hour replay, no P0 window.
- Rule 14: measured inputs throughout. Zero new free parameters.
- Expected reach: closes the composition gap (rank 3, 1,393 MWh) and ST_GAS starts ÷ CEMS (0.12–0.39×).
- Risk, stated: in the Aug-2023 hours it would cover rank 2 with steam the real system did not run. It would recreate the keeper's over-coverage (§3) for a corridor-side reason.
- Check the mechanism matrix before any test (`mechanism-matrix/SPP.js`; the SPP-44/46 adjudications bind the window form).

**P2. Re-test the corridor with a zone-resolved measured input, not a new limit number.**
- The only admissible moves are (i) the SPP-53 construction re-run with in-window (2023–25) effective limits if a vintage becomes available, or (ii) the pre-declared SPP-54 (SPS pocket) / SPP-57 (Oklahoma pocket) topology levers.
- Raising 3,400 to fit the Aug-2023 balance would be tuning to a residual (rules 1/13). **Not proposed.**
- The zonal wind shape (22 % South share in the hours that matter) is the other unknown. It is measurable only from per-plant hourly wind, which the corpus lacks. Proposed as a data-intake question, not a mechanism.

**P3. Zone the served interchange by counterparty** (ERCOT DC ties, EPE, PNM, PSCO/Lamar → South; SPC, WACM, WAUW → North; AECI/MISO/SPA by a documented tie census).
- Rule-14 alignment of a measured series. It moves South load **up**. Must be read together with P1/P2, never alone as a fit lever.

**P4. Data QA on 2025-12-16 → 12-23.**
- 3,623 MWh (50 %) of U4b unserved is a fill: BA and sub-BA demand, gas and wind are all constant.
- Mask those hours from the unserved kill, or source a repaired EIA-930 vintage. That is a scoring/data-QA ruling, not a model change. Until then, kill #3 for 2025 reads an artifact.

**Not proposed:** any adder, haircut or tuned limit; a CAMPD-hour or P0-pattern window (SPP-44/46); carrying MISO's VLR p25 level to SPP (rule 25); a RUC change (UC-5 showed the RUC inert on the measured ID basis).

## 6. Limits of this reading

1. **CEMS coverage** is ≈ 83 % of EIA-930 fossil energy. The thermal comparisons use the covered set on both sides; implied N→S uses model output for the uncovered remainder.
2. **Implied N→S** carries the model's South wind/solar/hydro and `emergency_band` (400–700 MW dispatched in South at these hours, not credited). Its bounds come from the ambiguous seam legs only.
3. **Hub prices are not nodal** prices, so the DA-below-mc share is indicative. The offer bands are the rule-1 channel and were not touched.
4. **The keeper is a control only:** different engine path and no co-optimised reserves (`energy_reserve_coopt = false`, against U4b `true`).
5. **The commitment increment** was recomputed from `commitment_demand` at `main` `4dc8d97d` after `regenerate_clean.py load-forecast-vintages`. U4b ran at `60e7c6fa`; the solve log's logged mean (2023 −112.2 MW) matches the basis.

## 7. Provenance

- **Shard legs read:** `claude/ucmilp5-spp-u4b-2019` `9d02bc67`, `-2022` `f2192a33`, `-2023` `e42a97b3`, `-2025` `491d3bb2`. These are transport, cut when PR #7282 merges. The three CSVs here carry every number taken from them.
- **Analysis scripts:** scratch only. They read shard-branch files that will not survive, so they are not committed as probes.
- No solve, no `src/` edit, no deletion.
