# FINDING — the EIA-930 DA-forecast basis audit (SPP, CAISO) and the SPP MTLF vintage intake, 2026-10-16

**Lane:** UC-DF-AUDIT (Opus) · **Chartered by:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner rulings R13 (audit)
and R14 (intake), `docs/uc-milp-program-plan-2026-10.md` §8.1, basis `main` `d2395da4`.
**Scope:** zero LP. A data intake (new datatype + loader, not wired), two audits, and two rule-14 PROPOSALS. No `src/`
change outside the new loader. No `ScenarioConfig` change. No solve.
**Evidence:** `docs/records/governance/uc-milp-2026-10/data/df_audit/` (scripts + CSVs; §6 reproduces).

## 0. Verdicts

| question | verdict | key numbers |
|---|---|---|
| **SPP 2024 DF < actual** | **Real forecast error.** It is in SPP's own MTLF. | 2024 EIA DF **is** the MTLF vintage issued 00:00 CPT D-1: exact on 55 % of hours, daily median \|Δ\| 0 MW. That vintage is below actual on 63 % of hours, mean −222 MW vs SPP's own actual |
| **SPP 2019–Aug 2023 and May–Dec 2025 DF > actual** | **Reporting artefact.** It is not in SPP's forecast. | In those periods EIA DF ≈ MTLF × **1.04** (to 2023-09-01) and × **1.117** (from 2025-05-07), with only 3–44 exact days a year. SPP's MTLF at every lead is below actual or ≈ 0 in every year |
| **What makes 2024 unique** | The **reporting**, not the forecast | On SPP's own MTLF, every year 2019–2025 under-forecasts the top-100 load hours by −370 to −910 MW (§4.1). Only 2024 had a faithful EIA DF for the whole year |
| **CAISO 2023–25 negative tail** | **Basis drift, not forecast error** (storage charging), plus an unexplained ±1.5 GW diurnal residual | EIA DF = CAISO OASIS DAM forecast (median \|Δ\| 0.25 MW). EIA Demand ≈ CAISO's actual, and both include battery charging. DF − Demand = −0.91 to −1.14 × charging MW (2021–25). Netting charging moves 2025 from mean −1,671 / p5 −6,596 MW to mean −185 / p5 −2,145 MW |

## 1. Intake: `load-forecast-vintages` (R14)

| item | value |
|---|---|
| datatype | `load-forecast-vintages` (`data/dictionary/schema/…schema.yaml`), key `iso, area, issue_time_utc, interval_end_utc`; partition `<ISO>/…_<issue year>.parquet` |
| raw | `data/raw/load-forecast-vintages/spp/{2019..2025}.zip` + `SHA256SUMS.txt` + README. 2019–24 are SPP's year zips byte-for-byte. 2025 is a repack of the 8,730 hourly files SPP serves live (no year zip yet), file bytes unchanged |
| code | `scripts/lib/load_forecast_vintages/{__init__,spp}.py` (registry), `scripts/data/curate_load_forecast_vintages.py`, `regenerate_clean.py` `DATATYPES`, `tests/test_curate_load_forecast_vintages.py` (tmp `CLEAN_DIR`) |
| loader | `market_sim.data.load_forecast_vintages.forecast_at_lead(iso, year, L)` / `select_at_lead(frame, L)`: for each operating hour, the latest vintage issued at or before **hour start − L**. **Not wired** (UC-RUC-BUILD owns that) |
| coverage | vintages per year 2019–25: **8,731 / 8,755 / 8,741 / 8,731 / 8,727 / 8,755 / 8,730** (of 8,760). Each vintage has 193 rows: 24 past hours with SPP's averaged actual, then 169 forward hours (7 days). About 1.69 M rows per year |
| clock | the stamp is the local CPT hour. Issue time = `max(GMTIntervalEnd) − 168 h`, cross-checked against the stamp outside ±2 h of DST. SPP labels the fall-back repeat `…0200d.csv`, so the tz database alone cannot place it |
| gaps | 5–33 unpublished vintages per year (confirmed by the portal listings) |
| footprint (rule 14) | MTLF files carry no `BAA` column before the April 2026 RTO West go-live; until then they are the SPP BA (= EIA-930 `SWPP`). Table A, at clock offset 0: EIA `Demand` / SPP actual = **0.996–1.003**, median \|Δ\| **69–106 MW**, r ≥ 0.978 after the loader's QA cut. ±1 h offsets give 634–776 MW, so EIA `UTC time` = SPP `GMTIntervalEnd` (hour end). One EIA unit slip (2023-06-13 02 UTC, 3.6 M MW) is already screened by the demand loader and dropped by the DF QA cut |

## 2. SPP audit (R13): EIA-930 SWPP DF vs SPP MTLF, 2019–2025

### 2.1 (a) Which vintage does the EIA DF track? Three reporting regimes (tables E, H)

| regime (local operating day) | EIA DF is… | exact days / days | DF ÷ MTLF(D-1 00h), non-exact days | DF − MTLF, non-exact days |
|---|---|---|---|---|
| **R1** to 2023-09-01 | MTLF D-1 00h on some days; otherwise a load-shaped **≈ +4 % uplift** | 2019 36/364 · 2020 28/365 · 2021 9/364 · 2022 44/363 · 2023 22/243 | 1.036–1.043 | +0.99 to +1.34 GW |
| **R2** 2023-09-02 → 2025-05-06 | **MTLF vintage issued 00:00 CPT D-1** | 2023 77/121 · 2024 205/365 · 2025 56/126 | 1.000 | −7 to +41 MW |
| **R3** from 2025-05-07 | a **≈ +11.7 % uplift** | 3/238 | 1.117 | +3.86 GW |

- **(c) Break dates:** **2023-09-02** (last uplift day 2023-09-01; from 2023-09-03 exact days dominate) and **2025-05-07**
  (preceded by one uplift day on 2025-05-03).
Shape of the uplift (`spp_uplift_shape.py`):

- **The uplift is not a clock shift.** Exact matches occur only at offset 0. Shifting by ±1–3 h only worsens the match
  (2022: median \|Δ\| 1,211 MW at 0 h, 1,271 / 1,232 MW at ∓1 h).
- **The uplift is not an additive constant either.** Its within-day std is about 336 MW and its hour-of-day profile is
  load-shaped (2021: +0.83 GW overnight to +1.77 GW at HE17).
- **The uplift does carry the same forecast signal.** Corr(DF − actual, MTLF − actual) is 0.76–0.91. So it is SPP's
  forecast scaled up on some basis that is not metered `SWPP` demand. What that basis is (losses, a wider area, another
  product) is **UNVERIFIED**; the audit establishes only that it is not on the `Demand` basis.

### 2.2 (b) Is the 2024 under-forecast in SPP's own forecast? Yes, and in every other year too (table F, vs EIA `Demand`, QA as the loader)

| forecast | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **EIA-930 DF (model DA basis today)**, mean MW | **+836** | **+1,082** | **+974** | **+894** | **+561** | **−239** | **+2,088** |
| share of hours below 0 | 23 % | 13 % | 14 % | 19 % | 31 % | **63 %** | 27 % |
| MTLF D-1 00h, mean MW | −100 | −41 | −118 | −162 | −248 | −244 | −382 |
| share below 0 | 55 % | 55 % | 61 % | 56 % | 63 % | 63 % | 66 % |
| MTLF D-1 13h (DA-RUC time), mean MW | +88 | +89 | +15 | −42 | −113 | −120 | −276 |
| MTLF lead ≥ 4 h (ID-RUC cycle), mean MW | +133 | +112 | +44 | +42 | −31 | −41 | −169 |
| MTLF lead ≥ 1 h, mean MW | +121 | +102 | +30 | +55 | −25 | −36 | −146 |

- **What this means for the design's §3.3 premise.** That premise was "2024 is the only SPP year whose DF runs below actual".
  It is true of the EIA-930 report only. On SPP's own forecast at a fixed vintage, 2024 is **typical**: the D-1 00h
  vintage is below actual on 55–66 % of hours in every year.
- **The years that looked over-forecast** owe their positive DF − actual to the R1 and R3 uplift.

## 3. CAISO audit (R13): EIA-930 CISO DF − demand, 2019–2025

Source: CAISO OASIS `SLD_FCST`, `CA ISO-TAC`, DAM (`SYS_FCST_DA_MW`) and ACTUAL (`SYS_FCST_ACT_MW`). It was reachable, so the
full 2019–25 run was fetched. Hourly extract: `caiso_oasis_ca_iso_tac.csv.gz`. Battery charging = max(−`NG: OTH`, 0) on the
EIA CISO frame (`NG: OTH` is CAISO's battery net output: −5.6 GW at midday and +5.7 GW in the evening, 2025 means).

| year | EIA DF − OASIS DAM, median \|Δ\| | EIA Demand − OASIS actual, mean | DF − Demand: coefficient on charging | charging mean / max (MW) |
|---|---|---|---|---|
| 2021 | 0.25 MW (99.7 % exact) | −131 | **−1.01** | 118 / 1,281 |
| 2022 | 0.25 MW | −126 | **−1.30** | 202 / 2,202 |
| 2023 | 0.25 MW | −117 | **−1.14** | 465 / 4,059 |
| 2024 | 0.25 MW | −95 | **−0.91** | 997 / 6,686 |
| 2025 | 0.25 MW | −91 | **−0.92** | 1,486 / 8,504 |

- **The forecast:** EIA's CISO DF *is* CAISO's DAM load forecast. It is not an EIA reporting artefact.
- **The actual:** EIA Demand ≈ CAISO's integrated actual load. The charging coefficient on their difference is about 0, so
  both include battery charging. The median \|Δ\| of 675–832 MW in 2023–25 is the known +1 h Demand-clock dipole
  (`caiso_demand_clock_realign`).
- **Why the tail grows.** CAISO's load forecast excludes storage charging, which is a bid-in, market-dispatched resource. The
  actual includes it. Their gap tracks the battery build-out, about 1:1.

Forecast error under each basis (table G2):

| year | EIA DF − EIA Demand (today) mean / p5 / days with an hour < −1 GW | EIA DF − (Demand − charging) | CAISO's own DAM − actual |
|---|---|---|---|
| 2019 | +631 / −814 / 66 | +638 / −807 / 66 | +25 / −1,124 / 122 |
| 2021 | −180 / −1,290 / 162 | −62 / −1,058 / 113 | −307 / −1,617 / 242 |
| 2023 | −525 / −3,025 / 363 | −60 / −1,983 / 352 | −642 / −2,841 / 354 |
| 2024 | −1,105 / −4,892 / 364 | −107 / −2,168 / 360 | −1,205 / −4,992 / 366 |
| 2025 | −1,671 / −6,596 / 363 | −185 / −2,145 / 345 | −1,764 / −6,636 / 365 |

- **Verdict: basis drift.** The bulk of the 2023–25 tail and mean (−1.5 GW of the −1.67 GW mean in 2025) is storage
  charging, which sits in the actual but not in the forecast.
- **Residual, UNVERIFIED.** After netting charging, a stable diurnal residual remains: overnight −1.2 to −1.7 GW and HE16–18
  +1.4 to +1.8 GW, nearly identical across 2023–25 and not a ±1 h clock effect. That keeps about 345–360 days a year with
  an hour below −1 GW.
  - Pumped-storage load cannot be separated on EIA (`NG: WAT` is net ≥ 0).
  - Other non-conforming load is also untested.
  - A stable shape repeating across three years is not typical forecast error. It needs CAISO-side data (e.g. OASIS
    `ENE_SLRS` / non-conforming load) before it is called either error or basis.
- **Bearing on caiso-80** (`docs/records/caiso/FINDING-caiso80-demand-basis-wedge-2026-07-13.md` §2). Its "daylight
  solar-shaped hump" in the 930 Demand cell grows 3.9 → 6.0 GW (2024–25), in step with the charging measured here. That
  lane's attribution ("fabricated block") should be re-checked against `NG: OTH`. Flagged for the CAISO lane; this lane
  does not adjudicate it.
- **Model consequence (zero LP).** The CAISO keeper arms `caiso_supply_consistent_demand`, so P1 demand is not the 930 cell.
  The `da_forecast` increment still subtracts the raw cell, charging included. The commitment demand is therefore
  understated by roughly the charging MW at midday: mean −1.1 GW in 2024 and −1.6 GW in 2025.

## 4. Proposals (rule 14). Owner via the desk; nothing landed

### 4.1 P-SPP: put the SPP DA increment on SPP's own forecast

- **Where:** `src/market_sim/data/commitment_demand.py::ba_forecast_error_mw`.
- **Change:** for SPP, the forecast term becomes the MTLF vintage issued at or before **00:00 CPT D-1**, read through
  `load_forecast_vintages`. This is the vintage EIA-930 itself carries whenever its DF is on SPP's basis (R2). The actual
  term (EIA `Demand`), the zone split, the clock and the QA cut are unchanged.
- **Why this vintage:** it removes only the R1/R3 artefact and keeps r13's "the BA's own DA forecast". Option B, the DA-RUC
  vintage (≤ 13:00 CPT D-1, Protocols §4.3.2), is a separate design choice for the owner.
- **Effect** (zero LP, `spp_proposal_effect.csv`, model clock, QA as the loader):

| year | today: mean / share below 0 / top-100 median (MW) | P-SPP (D-1 00h) | option B (D-1 13h) |
|---|---|---|---|
| 2019 | +836 / 23 % / +941 | −101 / 55 % / −823 | +91 / 45 % / −636 |
| 2020 | +1,082 / 13 % / +773 | −41 / 55 % / −683 | +88 / 47 % / −399 |
| 2021 | +974 / 14 % / +997 | −117 / 61 % / −369 | +15 / 53 % / −126 |
| 2022 | +894 / 19 % / +1,256 | −161 / 56 % / −407 | −42 / 49 % / +84 |
| 2023 | +561 / 31 % / +165 | −248 / 63 % / −826 | −112 / 57 % / −137 |
| 2024 | −239 / 63 % / −592 | −244 / 63 % / −670 | −121 / 59 % / −421 |
| 2025 | +2,088 / 27 % / +3,518 | −381 / 66 % / −912 | −276 / 61 % / −673 |

- **Reading:** 2024 barely moves. Every other year's commitment demand falls by 0.6–2.5 GW on average and turns into a peak-hour
  **under**-forecast.
- **Implication, stated, not predicted (no LP):** U4's non-2024 years were committed against a forecast inflated 4–12 %.
  On the faithful basis, the 2024 shortfall pattern can appear in other years. That strengthens the case for the RUC, and
  it changes the U5 "identity" argument (design §5 Q3): fewer years can be expected to be zero-trigger.
- **Forecast mode:** the SPP `load-forecast-error` profile is pooled from the same EIA DF, so it carries the uplift.
  Mean relative error per year is +1.8 to +6.2 % today (2024: −0.6 %), against −0.1 to −1.0 % on the MTLF. Re-derive it from the MTLF
  vintage under rule 23: a source-data change, cited.

### 4.2 P-CAISO: net storage charging out of the actual in the CAISO increment

- **Where:** `src/market_sim/data/commitment_demand.py::ba_forecast_error_mw`.
- **Change:** for CISO, `err = DF − (Demand − charging)`, with charging = max(−`NG: OTH`, 0) on the same filled frame. The
  DF is CAISO's DAM forecast and it excludes charging. The commitment demand is then the P1 demand plus genuine load-forecast
  error, and battery charging stays an LP decision (rule 3/4 spirit: storage is dispatched, not netted).
- **Effect** (`caiso_proposal_effect.csv`):

| year | today: mean / p5 / days with an hour < −1 GW | proposed | QA-dropped hours today → proposed |
|---|---|---|---|
| 2021 | −180 / −1,290 / 164 | −62 / −1,058 / 114 | 5 → 5 |
| 2022 | −416 / −2,300 / 297 | −214 / −1,913 / 255 | 3 → 3 |
| 2023 | −525 / −3,025 / 363 | −60 / −1,983 / 351 | 2 → 2 |
| 2024 | −1,097 / −4,869 / 363 | −106 / −2,170 / 360 | 62 → 49 |
| 2025 | −1,587 / −6,326 / 364 | −187 / −2,145 / 346 | 178 → 59 |

- **Top-100-load-hour increments are unchanged**: there is no charging at the peak.
- **Open item:** the residual ±1.5 GW diurnal shape (§3) is not addressed. That needs the CAISO-side data first.
- **Forecast mode:** the CAISO `load-forecast-error` profile carries the charging drift, growing with the fleet. Re-derive
  it on the same netted basis.

## 5. What this lane did not do

- No change to `commitment_demand.py`.
- No wiring of the vintages into UC/RUC (UC-RUC-BUILD owns that).
- No mechanism-matrix cell: no mechanism was tested and no `ScenarioConfig` field was added.
- SPP 2013–18 and 2026 vintages (with the `BAA` split) remain at source.

## 6. Reproduce (zero LP, `.venv`, repo root)

```
python3 scripts/hydrate_data.py --profile spp      # + shared (EIA-930) and caiso
PYTHONPATH=. .venv/bin/python -m scripts.data.curate_load_forecast_vintages --isos SPP
PYTHONPATH=. .venv/bin/python docs/records/governance/uc-milp-2026-10/data/df_audit/spp_df_vs_mtlf.py        # tables A-F, H
PYTHONPATH=. .venv/bin/python docs/records/governance/uc-milp-2026-10/data/df_audit/spp_uplift_shape.py     # §2.1 shape
PYTHONPATH=. .venv/bin/python docs/records/governance/uc-milp-2026-10/data/df_audit/spp_proposal_effect.py
PYTHONPATH=. .venv/bin/python docs/records/governance/uc-milp-2026-10/data/df_audit/caiso_df_audit.py [<oasis zip dir>]  # G1-G3; no arg = committed extract
PYTHONPATH=. .venv/bin/python docs/records/governance/uc-milp-2026-10/data/df_audit/caiso_proposal_effect.py
```
