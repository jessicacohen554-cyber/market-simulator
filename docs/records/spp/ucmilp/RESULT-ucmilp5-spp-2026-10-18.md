# RESULT — UC-5-SPP: U4b (U4 on the R16 MTLF basis) **R**; U5 (U4b + RUC) **R**, RUC inert on the measured basis — 7/7 years

**Lane:** UC-5-SPP · **Session:** `session_01RZka6nPCi64b3Y7J2Jxseq` (Opus) · **Date:** 2026-10-18 · **Branch:** `claude/ucmilp-5-spp`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`); owner rulings R12, R15, R16, R18, r16-1.
**PRECOMMIT:** `PRECOMMIT-ucmilp5-spp-2026-10-18.md`, pushed `7b13f521` before any shard. Addendum A (`c2fe7670`, before any U5 leg), Addendum B (`d64181ee`, after U5 2024, before the other five U5 legs).
**Pin:** `main` `60e7c6fa` (engine `uc-1.10`). **LP in this session:** zero. **Control:** keeper `2026-10-03-closeout-spp-nuc-keeper` (rule 29(b)).
**Comparator:** U4 (`ucmilp4_spp_u4_span`, uc-1.7). **Not registered** (local probe registration only, never committed).

## 0. Headline

- **U4b = R.** Kill #3 (14 PASS→FAIL flips vs the keeper) and the unserved kill (2022 761, 2023 2,656, 2025 3,623 MWh).
- **U5 = R** by the same kills. The RUC is **inert**: reserve-shortfall hours unchanged in every year, unserved halved in none (2023 −33 %). Bars B1/B2 not met.
- **Why the RUC is inert (zero LP, Addendum B, written before 5 of 6 U5 legs):** SPP's own intraday forecast is about as low as its DA forecast at the short hours. The RUC window is short only where ID-RUC error > −need: **1/10, 3/6, 0/13, 8/49, 5/20, 4/17** trigger hours. It adds units elsewhere, where the ID forecast is *above* actual (0–3 of the 0–480 added unit-hours per year fall in a trigger hour).
- **What the shortfalls are:** SPP-South-zonal, behind the 3.4 GW North→South limit, with South ST_GAS committed at 1.1–1.4 of 5.6–6.5 GW. That is the **ST_GAS under-commitment** object (UC-3/UC-4 §8 item 1), not missing system capacity and not a forecast-error problem a RUC can fix.
- **Basis effect (U4b vs U4, basis + FIX-9):** the MTLF basis removes the EIA DF's reporting uplift cushion. Every year now commits short of actual somewhere; the spin sub-row binds 2,700–4,300 h/yr and the load-weighted reserve price doubles to triples. **C3a worsens in every year** (2019 +15.3 → +35.9 %, 2020 +27.8 → +47.2 %).
- **Data flag (rule 14, not fixed):** all of 2025's 3,623 MWh unserved sits in a 155-h stretch (Dec 16–23) where SPP-South demand is constant at 18,597 MW — a fill, not load. Flat ≥ 4-h stretches exist in every year (34–828 h/yr); only 2025's coincides with slack.
- **Engine clean:** DA 2,555/2,555 windows Optimal; RUC 532/532 Optimal; 0 time-limit hits; add-only held in every cluster-hour; R15 digest reuse matched 6/6.

## 1. Gate table — control → U4 → U4b → U5 (rubric as on `main`; F/P = status)

U4b − U4 is **basis + FIX-9** (uc-1.8 lean LP heuristics also differ); not a clean basis isolation. U5 2021 = U4b 2021 (identity adoption).

| year | arm | C3a | C3b | C1 CC_REG TWh | C1 ST_GAS TWh | C1 CT_PEAK TWh | unserved MWh | reserve-short h |
|---|---|---|---|---|---|---|---|---|
| 2019 | keeper | F +12.3 % | P 0.160 | P +2.25 | P −4.96 | P +1.49 | 0 | 0 |
| | U4 | F +15.3 % | P 0.191 | P +1.97 | −7.49 | +3.04 | 0 | 0 |
| | U4b | F **+35.9 %** | **F 0.446** | P +1.29 | **F −8.08** | P +4.85 | 137 | 9 |
| | U5 | F +35.9 % | F 0.446 | P +1.29 | F −8.08 | P +4.84 | 137 | 9 |
| 2020 | keeper | F +27.7 % | F 0.345 | P +1.60 | P −3.42 | P +6.15 | 0 | 0 |
| | U4 | F +27.8 % | F 0.345 | +2.86 | −6.31 | +7.40 | 0 | 0 |
| | U4b | F **+47.2 %** | F 0.493 | P +2.22 | P −7.01 | **F +10.05** | 0 | 6 |
| | U5 | F +47.2 % | F 0.493 | P +2.22 | P −7.01 | F +10.05 | 0 | 6 |
| 2021 | keeper | P +7.1 % | P 0.176 | F −8.92 | P −2.83 | P +1.31 | 0 | 0 |
| | U4 | P +7.1 % | P 0.133 | P −6.86 | −5.00 | +2.39 | 0 | 0 |
| | U4b = U5 | **F +14.8 %** | P 0.154 | F −8.71 | P −5.33 | P +4.34 | 0 | 0 |
| 2022 | keeper | P −4.8 % | P 0.175 | F −9.16 | P −5.18 | P −1.39 | 0 | 0 |
| | U4 | P −3.2 % | P 0.171 | P −7.79 | −7.61 | +0.83 | 0 | 0 |
| | U4b | P +7.2 % | P 0.160 | F −9.11 | **F −8.40** | P +2.75 | **761** | 9 |
| | U5 | P +7.2 % | P 0.160 | F −9.11 | F −8.40 | P +2.75 | **761** | 9 |
| 2023 | keeper | P −6.4 % | P 0.176 | P −4.49 | P −5.55 | P +2.83 | 0 | 0 |
| | U4 | not solved (held) | | | | | | |
| | U4b | **F +37.4 %** | **F 0.517** | P −4.43 | **F −10.43** | **F +8.24** | **2,656** | 42 |
| | U5 | F +37.3 % | F 0.516 | P −4.44 | F −10.42 | F +8.23 | **1,770** | 42 |
| 2024 | keeper | F −11.2 % | F 0.216 | P −5.80 | P −6.31 | P +2.36 | 0 | 0 |
| | U4 | F +47.6 % | F 0.625 | −6.11 | F −10.51 | F +8.26 | 169 | 35 |
| | U4b | F +31.7 % | F 0.419 | P −5.94 | **F −10.31** | P +7.73 | 0 | 20 |
| | U5 | F +31.7 % | F 0.418 | P −5.94 | F −10.30 | P +7.72 | 0 | 20 |
| 2025 | keeper | P −4.3 % | P 0.153 | P −7.86 | P −6.91 | P −0.05 | 0 | 0 |
| | U4 | P −3.6 % | F 0.220 | −6.22 | F −8.61 | +0.40 | 0 | 0 |
| | U4b | **F +17.8 %** | **F 0.253** | **F −8.31** | **F −10.34** | P +4.86 | **3,623**¹ | 12 |
| | U5 | F +17.8 % | F 0.253 | F −8.31 | F −10.34 | P +4.86 | **3,623**¹ | 12 |

¹ inside the 155-h flat-filled SPP-South demand stretch (§0). **Bold** = PASS→FAIL vs keeper, or over the 500 MWh unserved kill.

- **Flips vs keeper, U4b (14):** C1 ST_GAS 2019/2022/2023/2024/2025; C1 CT_PEAKER 2020/2023; C1 CC_REGULAR 2025; C3a 2021/2023/2025; C3b 2019/2023/2025. Plus C3c 2021/2022 CAVEAT→FAIL (2.74× / 0.17× > $200 hours). Upgrades: C4 gas 2022; C3c 2019/2020/2024.
- **U5 flips:** identical set (magnitudes within 0.1 pp / 0.01 TWh).
- **Determination:** NOT-YET for both (C6 UNATTESTED as any probe; 4 fails).
- **C8:** ST_GAS forced share 4–15 %, all PASS; no D-4 FAIL row; the `uc_ruc` D-4 sub-row reads 0 off-window energy every year.

## 2. Pre-registered readings

### 2.1 Basis (U4b; `uc_solve_log.commitment_demand`, basis `spp_mtlf_da_ruc`)

| year | DA increment mean MW | top-100 median MW | U4 (EIA DF) mean | trigger h / days | spin binding h | LW reserve price $/MWh |
|---|---|---|---|---|---|---|
| 2019 | +91 | −594 | +830 | 10 / 5 | 2,676 | 3.47 |
| 2020 | +88 | −441 | +1,078 | 6 / 4 | 2,911 | 2.96 |
| 2021 | — | — | +967 | 0 / 0 | 3,919 | 6.42 |
| 2022 | −42 | −3 | +894 | 13 / 5 | 3,599 | 6.17 (U4 3.10) |
| 2023 | −112 | −143 | +561 | 49 / 15 | 3,694 | 7.85 |
| 2024 | −121 | −421 | −239 | 20 / 6 | 3,117 | 6.79 (U4 9.39) |
| 2025 | −276 | −700 | +2,073 | 17 / 5 | 4,333 | 6.34 (U4 1.98) |

2021 basis block not logged by the shard; 2021 has no trigger hour.

### 2.2 RUC (U5; `uc_solve_log.ruc`)

| year | trigger h (slack / reserve) | RUC-visible h¹ | episodes / windows | swept hours | added unit-h (CC / coal / ST_GAS) | added floor GWh | added at trigger h | RUC net uplift $M | shortfall h U4b → U5 | unserved MWh U4b → U5 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 10 (1 / 9) | 1 | 1 / 150 | 5,160–8,760 | 459 (71 / 23 / 365) | 10.16 | 1 | −0.29 | 9 → 9 | 137 → 137 |
| 2020 | 6 (0 / 6) | 3 | 2 / 121 | 3,672–6,552 + 1 d | 226 (55 / 25 / 146) | 8.11 | 0 | −0.18 | 6 → 6 | 0 → 0 |
| 2021 | 0 | — | adopted | — | — | — | — | — | 0 → 0 | 0 → 0 |
| 2022 | 13 (4 / 9) | 0 | 5 / 44 | 3,288–4,248 + 4 d | 48 (0 / 48 / 0) | 3.05 | 1 | −0.15 | 9 → 9 | 761 → 761 |
| 2023 | 49 (9 / 42) | 8 | 3 / 160 | 4,848–8,640 + 2 d | 480 (0 / 147 / 333) | 18.66 | 3 | −0.58 | 42 → 42 | 2,656 → 1,770 |
| 2024 | 20 (0 / 20) | 5 | 4 / 52 | 3,288–4,440 + 3 d | 151 (24 / 61 / 66) | 9.35 | 0 | −0.27 | 20 → 20 | 0 → 0 |
| 2025 | 17 (5 / 12) | 4 | 4 / 5 | 4 days | 0 | 0 | 0 | 0.00 | 12 → 12 | 3,623 → 3,623 |

¹ hours where ID-RUC error > −need (Addendum B). "Net uplift" = `ruc_start_usd` + `ruc_noload_usd`: negative because the RUC keeps units online across short gaps, removing more DA starts than it adds no-load.

- **Bars:** B1 (shortfall hours ≤ ½ U4b) **not met** in any year. B2 (unserved ≤ ½ U4b) **not met** (2023 −33 %; others 0 %).
- **Sweep behaviour:** once triggered, adds on high-ID-forecast days keep the carried state off the DA schedule, so the sweep runs for weeks to the year-end (2019, 2023). It is in effect a daily ID-RUC from the first trigger day.
- **P1b is real, not P1a:** U5 prices differ from U4b in 86–135 h and unit dispatch moves up to 400 MW; the reserve shortfall MW is identical in every family-hour (max |Δ| 0.0).

### 2.3 Where the short hours are (zero LP, U5 sidecars)

- Every slack hour is in **SPP-South** with the **North→South link at its 3,400 MW limit** (dual −$1,450 to −$1,980).
- At those hours South thermal is at its UC-bounded cap. **South ST_GAS cap 1.1–1.4 GW of 5.6–6.5 GW** (2023, 2025), CC 3.5 of 6.7 GW (2025).
- So the gap is slow South units the DA UC left offline, and a load forecast that is also low intraday gives the RUC no reason to add them.

### 2.4 Starts ÷ CEMS (M1, `_ucmilp_benefit_screen.screen_year`)

| year | CC_REGULAR U4 → U4b → U5 | ST_GAS | COAL_PRB | COAL_LIGNITE |
|---|---|---|---|---|
| 2019 | 0.53 → 0.55 → 0.54 | 0.19 → 0.16 → 0.15 | 0.43 → 0.41 → 0.41 | 0.73 → 0.73 → 0.67 |
| 2020 | 0.56 → 0.60 → 0.60 | 0.15 → 0.13 → 0.12 | 0.49 → 0.49 → 0.49 | 0.51 → 0.63 → 0.63 |
| 2021 | 0.72 → 0.68 → (= U4b) | 0.20 → 0.16 | 0.85 → 0.98 | 0.79 → 0.94 |
| 2022 | 1.02 → 0.98 → 0.98 | 0.36 → 0.29 → 0.29 | 1.24 → 1.34 → 1.34 | 1.50 → 1.45 → 1.45 |
| 2023 | — → 0.56 → 0.56 | — → 0.39 → 0.38 | — → 1.30 → 1.29 | — → 1.79 → 1.79 |
| 2024 | 0.72 → 0.72 → 0.72 | 0.30 → 0.33 → 0.33 | 0.94 → 0.89 → 0.88 | 2.75 → 2.67 → 2.67 |
| 2025 | 0.65 → 0.67 → 0.67 | 0.53 → 0.36 → 0.36 | 0.96 → 1.24 → 1.24 | 0.96 → 1.35 → 1.35 |

ST_GAS remains under-started (0.12–0.39×) in every arm and year.

## 3. Kills

| # | kill | U4b | U5 |
|---|---|---|---|
| 1 | infeasible / time-limited window (DA or RUC) | not fired (0/2,555) | not fired (0/532 RUC) |
| 2 | add-only (`u_final < u_DA`) | n/a | not fired: min(u_final − u_DA) = 0 in all 4.58 M cluster-hours; the stage's own raise never fired |
| 3 | unserved > control + 500 MWh | **fired** 2022, 2023, 2025 | **fired** 2022, 2023, 2025 |
| 4 | non-determinism on a repeated leg | not exercised (no year ran twice) | not exercised. The 6/6 digest matches across separate containers do certify the DA inputs (P0 included) reproduced byte-for-byte |

Per the accepted scope (§5), the U4b kill did not stop U5; the U5 kill fired on legs already running and stops the arm.

## 4. Verdicts

- **U4b vs keeper: R** (kill #3, unserved kill). T1/T2/T3 all move the wrong way past the control.
- **U5 vs keeper: R** (same).
- **RUC (`uc_reliability_commitment` × SPP): R** by the fixed rule ("R on any kill"). The structural reading is narrower and is the useful one: **the pass is faithful and inert on SPP's measured intraday basis.** It did no harm (gates within 0.1 pp, net uplift negative), but it cannot close a South-zonal ST_GAS commitment gap that SPP's own intraday forecast does not see.
- **`uc_commitment_demand_source` × SPP:** stays U (armed in a bundle, not isolated). Its evidence: with the reporting uplift removed, the SPP DA commitment runs short of actual in 6 of 7 years.

**Rule-1 reading.** The binding SPP object is **steam-gas commitment** (ST_GAS 0.12–0.39× CEMS starts, −7 to −10.4 TWh), now visible as South-zone scarcity once the DF uplift no longer over-commits. Neither the R16 basis nor the RUC addresses it. Next lever (desk's call): ST_GAS commitment physics or a zonal reserve / deliverability read of the South, before any further SPP UC arm.

## 5. Cost: wall, memory

| year | U4b wall s (UC seam s) | U4b peak GiB | U5 wall s (RUC s) | U5 peak GiB | container ceiling + swap (U4b / U5) |
|---|---|---|---|---|---|
| 2019 | 3,706 (3,379) | 8.46 | 594 (143) | 8.00 | 22.4 / 16.4 |
| 2020 | 2,895 (2,421) | 7.97 | 663 (132) | 8.58 | 16.4 / 16.4 |
| 2021 | 2,092 (1,618) | 8.75 | adopted | — | 22.4 / — |
| 2022 | 2,782 (1,916) | 8.21 | 511 (46) | 8.00 | 22.4 / 16.4 |
| 2023 | 2,387 (1,980) | 8.19 | 579 (136) | 8.04 | 22.4 / 17.4 |
| 2024 | 5,025 (4,613) | 7.91 | 483 (51) | 8.42 | 22.4 / 22.4 |
| 2025 | 2,612 (1,932) | 7.92 | 436 (16) | 8.59 | 16.4 / 16.4 |

- Every leg on its first attempt; none reclaimed (2024 U4b ran 84 min and survived the expected ~70–75 min reclaim).
- Peak 8.75 GiB < 10.6 GiB gate. R15 reuse cut each U5 leg to 7–11 min.

## 6. Disclosures

1. **Addendum A's expectation was mis-specified** (it compared ID with DA error, not with the need). Corrected in Addendum B after U5 2024 and before the other five U5 legs; bars and kills unchanged.
2. **Composition:** scratch copy of `_ucmilp_compose_span.py` as in UC-3/UC-4 (`gas_price_override` per-year; keeper `_respan_shared_inputs`, re-spanned to `campd-8b15fb193a60` / `eia923-ada99c7451fd` / `eia930-c3bec7e7b952`). The U5 span carries 6 years (2021 adopted, cited to U4b). No repo script edited.
3. **Scoring:** `dashboard_add_run.py --no-prune` locally for `2026-10-18-ucmilp5-spp-u4b` and `…-u5`; sidecars/payloads excluded via `.git/info/exclude`, **not committed**.
4. **Inherited warning (every leg, as U4):** caught `resolved_inputs: split-remap probe failed` — `campd-unit-outages-maxgen-splitremap-SPP.csv` never derived while the keeper arms `campd_split_remap_companions`. Provenance probe only.
5. **Shards** ran `uv sync` when `.venv` was absent (the documented route); none edited `src/`/`scripts/`.

## 7. Where everything is

| artefact | where |
|---|---|
| U4b legs (21 files each, full) | `claude/ucmilp5-spp-u4b-2019` `9d02bc67` · `-2020` `30503285` · `-2021` `7785a5fd` · `-2022` `f2192a33` · `-2023` `e42a97b3` · `-2024` `22481a70` · `-2025` `491d3bb2` |
| U5 legs | `claude/ucmilp5-spp-u5-2019` `f9399a0d` · `-2020` `33822e75` · `-2022` `5a08ee13` · `-2023` `593e4bc0` · `-2024` `efb35e9d` · `-2025` `b2e94988` |
| slim spans (no `dispatch/`, `floors/`, `unit_hourly`) | `docs/records/spp/ucmilp/data/ucmilp5_spp_u4b_span/` (31 MB; includes the R15 reuse files) · `…/ucmilp5_spp_u5_span/` (27 MB) |
| composed full spans | local only; will not survive the container |
| 13 shard sessions | all verified (ls-tree + bytes), then archived; none alive |

- **Promotion:** none proposed (R).
- **Branches for the owner to cut once this PR merges:** `claude/ucmilp5-spp-u4b-{2019..2025}`, `claude/ucmilp5-spp-u5-{2019,2020,2022,2023,2024,2025}` (13).
