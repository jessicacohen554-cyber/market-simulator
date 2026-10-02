# FINDING — PJM close-out wave 1: the five zero-LP censuses (0a–0e), hygiene, PRECOMMITs

Lane `closeout-PJM` (branch `claude/closeout-pjm-wave1`, from `4d459da3`), chartered by the close-out desk 2026-10-02 (plan `docs/backcast-closeout-plan-2026-10.md` §3.6, §6.1). **Zero LP.** Keeper unchanged: `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`, `6d4c7749`). Every reading below was fixed in the plan before the number existed; none is re-read.

## 1. Census table vs the pre-fixed readings

| step | pre-fixed reading (plan §3.6) | result | verdict | consequence |
|---|---|---|---|---|
| 0a capacity | every class within ±2 % of IMM §12 at 31 Dec, else name the units | 8 / 63 class-years pass; coal 2020 −3.38 % | **FAIL** (units named, §2) | no lever; two defects routed to W0 |
| 0b Elliott | published forced − model unavailable ≥ 15 GW in ≥ 18 h, 20–28 Dec 2022 | 0 / 216 h; gap negative on 8 of 9 days | **FAIL** (L3 premise not confirmed) | L3 not chartered |
| 0c reserves | coal ≥ 25 % of real sync reserve AND ≈ 0 in model | real coal 25.8 / 47.2 / 16.5 / 14.1 % in 2019/20/21/25; model coal already a pool member | **FAIL** (2021, 2025 fail; L1 a no-op) | L1 not chartered |
| 0d incremental HR | model CC econ HR − CAMPD incremental HR ≥ 0.8 MMBtu/MWh (2020) | +1.12 (2020); +0.77…+1.94 all years | **PASS** | L2 PRECOMMIT written; rule-19 blocker |
| 0e marginal fuel | model coal-marginal share within 1.3× of PJM hourly | 2020 0.96×; all 7 years in [0.78, 1.22] | **PASS** | C3a 2020 floor is a level error, not merit order |

Probes and artifacts: `scripts/probes/_pjmco_0{a,b,c,d,e}_*.py` → `results/phase0/pjm/_pjmco_0{a,b,c,d,e}_*.{json,csv}`.

## 2. 0a — capacity reconciliation (FAIL; units named)

Model MW = EIA-860 `vintage_<Y>` net summer (OP) for the plant set the keeper carries (`unit_marginal_<Y>` membership, PJM BA + OVEC join); IMM = SOM §12 Table 12-1 "Existing capacity: December 31, <Y>" (summer installed rating). The `fleet_only` rebuild was not run (permission classifier denied it in the probe session); membership is read from the keeper's own sidecars instead.

- **Coal 2020: not a capacity error.** Year-end gap −1,696 MW, wholly IMM's external **XIC** row (1,955 MW; residual −259). The research shard's "46.4 GW vs 52.0 GW" compared the LP's availability-scaled annual max (46,643) with IMM's 31-Mar figure; at 31 Dec IMM prints 50,230.8. Without XIC coal is inside ±2 % in 2020/22/23/24; 2019 +2.86, 2021 +3.98, 2025 −2.69 (2025: OVEC rating basis +253, Morgantown OS, Painesville SB; 640 MW unattributed). **COAL_BIT 2019–21 is dispatch, not fleet** — consistent with NEXT-17/22/24.
- **Nuclear −2.3 % every year:** XIC's 1,140 MW; ex-XIC +1.1 % (PASS).
- **Gas ST surplus / oil deficit mirror each other:** Martins Creek 3148 (1,700 MW) typed gas by Energy Source 1 vs IMM oil (candidate); Chalk Point 1571 in 2020; SB oil units (Commonwealth Chesapeake 55381). Labels, not MW.
- **Gas CT +2.6…+5.0 %:** dual-fuel units typed gas (Ladysmith 7839, Troy 55348; candidates — IMM lists no units).
- **CC 2023–25 +3.4…+5.5 %:** Guernsey 62949, CPV Three Rivers 63931, New Covert 55297 — IMM vs EIA dating/basis (NEXT-20 already noted Guernsey/CPV).
- **Solar 2024–25 −8.2 / −25.7 %: a real model-side membership defect.** The renewables loader's eGRID zone lookup drops PJM-BA operating plants absent from the lookup: 129 plants / 3,738 MW (2024), 349 / 6,986 MW (2025) (Mammoth North 65957, AEUG Union 64660, Hecate Highland 62670…); wind loses Timbermill 67910, Top Hat 69225, Dans Mountain 67962 the same way. **Routed to W0** (it is an EIA-860 membership defect, lane B's scope) — not fixed here.
- 2019–23 solar surplus and the wind deficit remainder are nameplate-vs-rating basis. The committed 2025 leg was solved on the EIA-860 Early Release (Final is −0.77 GW PJM nameplate) — W0 re-baselines it.

## 3. 0b — Elliott (FAIL; L3 not chartered)

Published `gen_outages_by_type` (PJM RTO, lead 0, daily) vs Σ(installed proxy − `cap_mw`) over thermal units in `unit_marginal_2022` (installed proxy = unit's 2022 max `cap_mw`, which understates model outage, so the gap is conservative in L3's favour).

| Dec 2022 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 |
|---|---|---|---|---|---|---|---|---|---|
| published forced (MW) | 10,396 | 11,585 | 10,433 | 11,914 | 31,078 | 35,844 | 27,058 | 24,052 | 17,957 |
| model unavailable thermal | 34,851 | 26,249 | 26,096 | 30,192 | 33,839 | 33,295 | 34,012 | 31,614 | 27,605 |
| gap | −24,455 | −14,664 | −15,663 | −18,278 | −2,761 | +2,549 | −6,954 | −7,562 | −9,648 |

0 h ≥ 15 GW. Reserve duals, shortfall and slack 0 in every window hour; daily max zonal price ≤ $136. **What the census does show:** no *level* gap — the model already carries more unavailable MW than PJM's forced figure — but no *event rise*: model thermal outage rises 4–7 GW over its 20–22 Dec baseline while published forced rises ~20–25 GW. Only two variants flip the verdict (event increment: 48 h; total − thermal ex-exit-bucket: 24 h), and both are the baseline-differenced form the research shard flagged as the double-count risk. Owner card: one-event caveat (h18 card B) vs an event-windowed increment overlay — not chartered under the pre-fixed reading.

Secondary (pjm-161): annual-mean model thermal unavailable 42.1/43.6/38.6/35.9 GW (2022–25) vs published total 35.1/33.3/33.0/35.9; the 2022 excess over the fleet-wide published rate sits in COAL_BIT (+10.1 GW, 46 % of class out) and ST_GAS (+4.5), while CT_PEAKER (−3.3) and nuclear (−5.8) sit below — a heuristic attribution (PJM publishes no class split).

## 4. 0c — reserves (FAIL; L1 not chartered — and a premise correction)

- **Model:** COAL is already a `pjm_reserve_pergen` pool member: `RESERVE_FUEL_TYPES` (`src/market_sim/model/reserves/spec.py:38-40`) includes coal, membership = `_reserve_eligible` and `ramp10 > 0` (`spec.py:1161-1164`, `2577-2578`), `RAMP10_FRAC_BY_GROUP["COAL_BIT"] = 0.15` (`data/fleet/withholding.py:338`); 475 coal pool members (2021). Register row 31's "gas+oil" describes `_AS_PJM_GROUPS` (`withholding.py:57`), the `as_reserve_withholding` pool (off in the keeper), not the co-opt pool. The research shard's L1 ("COAL_* join `pjm_reserve_pergen`") is therefore **a no-op as written**. The reserve dual is ≈ $0 in every year (0–2 RTO / ≤ 6 MAD hours > 0, no shortfall) because ~25 GW of CT/oil headroom (offline CTs count; pools not online-gated) covers the 2.6–3.6 GW requirement, so forced coal-held is 0 MW in every hour.
- **Real (IMM SOM §10, 2019–2025, all seven reports):** coal share of synchronized reserve 25.8 / 47.2 / 16.5 / 15.7 / 24.0 / 23.5 / 14.1 %; of regulation 3.8–8.2 %. Digitized rows: `results/phase0/pjm/_pjmco_0c_som_sec10_reserve_by_unit_type.csv` (table/page per row; intake into `som_competitive_conduct.csv` left for a data-intake step).
- Verdict on the COAL_BIT fail years: 2019, 2020 pass; 2021 (largest miss) and 2025 fail ⇒ **FAIL**. Real Tier-1 is incidental headroom on economically-loaded units, so even the passing years do not evidence displaced coal energy. Making coal hold reserve would need an online-gated / synchronized-reserve mechanism (`pjm_reserve_pergen_sync` is R, pjm-h3), not a membership change.

## 5. 0d — incremental HR (PASS) and 0e — marginal fuel (PASS)

**0d.** Capacity-weighted CC_REGULAR, MMBtu/MWh (net basis): model econ HR 7.54/8.06/7.99/7.87/8.10/8.83/8.82 vs CAMPD incremental slope 6.76/6.94/6.88/6.88/6.95/6.90/6.92 (2019–25); gap +0.77/**+1.12**/+1.11/+0.99/+1.15/+1.94/+1.89. Two findings bound L2: (i) the gap sits entirely in the upper econ slices (CC_LIKE shape ratio 1.04 → 1.5); the cheapest econ slice is already at incremental HR (−0.19…+0.14), so the low-end floor effect is expected small; (ii) **rule-19 blocker** — with `pjm_offer_midcurve_shape_segments=['CC_LIKE']` the belt *sets* these rows (signed replacement), so L2 can only replace that scope. PRECOMMIT: `PRECOMMIT-pjm-closeout-l2-incremental-hr-2026-10-02.md` (owner question: replace vs re-base).

**0e.** New intake: IMM Marginal Fuel Postings 2019-01 → 2025-12 (`data/raw/pjm-marginal-fuel/`, fetch `scripts/data/fetch_pjm_marginal_fuel.py`, schema `data/dictionary/schema/pjm-marginal-fuel.schema.yaml`; raw gitignored pending a licence ruling — Monitoring Analytics posts "All rights reserved"; SHA256SUMS committed). Time-weighted coal-marginal share, PJM vs keeper `unit_marginal`: .316/.287, **.251/.241**, .197/.161, .143/.175, .154/.132, .152/.157, .137/.106 ⇒ ratios 0.91/**0.96**/0.82/1.22/0.86/1.04/0.78, all PASS (dispatchable-only sensitivity: 2022 1.30, a hair over). **Correction to NEXT-18:** "model coal sets price 1.7–2.6× the IMM rate" compared a time-weighted model share with the IMM's unit-count share; on a like-for-like basis the excess disappears. The C3a 2020 floor is a **level** error.

## 6. Hygiene

- **`coal_drop_pof` cell U → K** (`mechanism-matrix/PJM.js`): armed in all seven keeper `run_config_<Y>.json` (runner default, `pipeline/flags.py` `--coal-drop-pof`). Registration, not adjudication.
- **Tait remap — proposed, not applied** (a `src/` identity edit; NEXT-24 card 3). EIA-860 lists GT1–GT7 under plant 2847 in every vintage 2019–2025, while CAMPD files GT4–GT7 as facility 55248 units CT4–CT7 (the EPA–EIA crosswalk still maps them to a stale EIA 55248). Proposed cited override in `data/campd.py::CAMPD_UNIT_PLANT_REMAP`:
  ```python
  # Tait Electric Generating Station (PJM, OH, CT_PEAKER): CAMPD files the
  # 2002 GT4-GT7 block as facility 55248 units CT4-CT7, while EIA-860 carries
  # them as plant 2847 GT4-GT7 in every vintage 2019-2025. [R-ACCURATE]
  # RESULT-pjm-next-24-2026-10-02.md §3; FINDING-pjm-closeout-wave1-censuses-2026-10-02.md §6.
  (55248, "CT4"): 2847,
  (55248, "CT5"): 2847,
  (55248, "CT6"): 2847,
  (55248, "CT7"): 2847,
  ```
  It moves derived artifacts (bench shape, CT HR, outage windows) only through the default-off `campd_split_remap_companions` gate (miso-280 pattern); its re-derive and a G-DRIFT audit belong to the first PJM solve that carries it. Size ≈ $1–2/MWh on Tait's offer (NEXT-23) — a data repair, not a lever.

## 7. PRECOMMITs and what the lane solves after W0

| PRECOMMIT | status |
|---|---|
| R-13 `gas_offer_margin_anchor_vintage`, displacement-aware S4 (`PRECOMMIT-pjm-closeout-r13-anchor-vintage-2026-10-02.md`) | written; phase-0 delta reproduces pjm-169's 2022 identity (7.1208, +$10.58); 2020 −$2.42 |
| L2 incremental-HR CC econ (`PRECOMMIT-pjm-closeout-l2-incremental-hr-2026-10-02.md`) | written; build waits on the replace-vs-re-base ruling |
| L1 coal reserve pool | **not written** — 0c FAIL and the lever is a no-op |
| L3 Elliott overlay | **not written** — 0b FAIL; owner card above |

Solves HOLD until `claude/closeout-b-w0-foundation` merges and the desk releases the lane. Out of scope here (other lanes): PJM C1 coal/CC rulings (lane D, R-4), zonal C3a (lane C, R-13 second half).
