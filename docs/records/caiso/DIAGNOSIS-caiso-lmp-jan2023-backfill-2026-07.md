# DIAGNOSIS — CAISO LMP residual after the Jan-2023 OASIS backfill (2026-07-14)

Companion to the caiso-80 keeper entry (2026-07-13 calibration log) and
`results/calibration/FINDING-caiso80-demand-basis-wedge-2026-07-13.md`. This
session folded the hand-downloaded OASIS GRP zips (Jan 1–25 2023 DAM, 19
trade dates) into the CAISO actuals, rescored the keeper, and decomposed the
remaining price residual. Handoff for the candidate-bundle campaign:
`docs/handoffs/caiso-price-residual-campaign-2026-07.md`.

## 1. What the backfill changed (scorer-side only; no re-solve)

Data: `CAISO_dam_hourly_2023.csv` +1,368 hub rows (Jan 1–5, 7, 8, 11–15, 17,
18, 20–23, 25 — 19 of 31 days); DA coverage 82% → 87% of 8760. The RTM GRP
zips on hand (~34 scattered hours, Jan 1–4) were deliberately NOT folded — a
January RT monthly mean fabricated from storm-day hours would enter the gated
C3a basis as if it covered the month. HASP zips are a different market run
and are never folded.

| metric (2023) | before | after |
|---|---|---|
| actual DA (legacy equal-hour) | $49.84 | $55.71 |
| actual DA (load-weighted) | $53.41 | $58.92 |
| actual DA January (lw) | — (uncovered) | **$150.09** |
| actual DA tail >$200 (C3c) | 41 h (82% cov) | **79 h** (87% cov, lower bound) |
| C3a gated (vs RT, Mar–Dec masked) | +18.5% | +18.5% (RT coverage unchanged) |
| C3a DA diagnostic | +8.7% (11-mo mask) | **+21.8%** (12-mo, Jan unmasked) |
| C3c ratio | 16.3× | 8.4× |

Verdict unchanged: NOT-YET (C3a/C3b/C3c/C4). The January unmask moves the
2023 DA-basis residual from "close" (+8.7%) to "clearly over" (+21.8%),
because the model's January is $221.99 (payload `pMon`) against a measured
$150.09 — the single largest monthly miss in the three-year span.

## 2. Month-resolved residual (model demand-wtd `pMon` vs lw actual, RT basis
with DA fallback for Jan/Feb-2023; implied HR = λ ÷ CA-composite citygate,
`data/raw/gas-prices/caiso_citygate_daily.csv` monthly means)

2023: gas $16.1 (Jan, from Jan-5; Jan 1–4 higher), $7.1 (Feb), $2.6–6.5 rest.

| mon | model | actual | Δ% | iHR model | iHR actual |
|---|---|---|---|---|---|
| 1 | 222.0 | 150.1 (DA) | **+48%** | 13.8 | 9.3 |
| 2 | 95.7 | 100.9 (DA) | −5% | 13.5 | 14.2 |
| 5 | 36.3 | 17.2 | **+111%** | 14.1 | 6.7 |
| 6 | 45.3 | 26.9 | **+68%** | 17.4 | 10.4 |
| 7 | 59.7 | 60.7 | −2% | 13.8 | 14.1 |
| 9 | 53.4 | 37.3 | +43% | 18.2 | 12.7 |
| 12 | 70.7 | 47.0 | **+50%** | 18.6 | 12.4 |

2024: model over in 11 of 12 months (Feb–May iHR 17–24 vs actual 7–14),
**UNDER only in January** (55.5 vs 68.7 RT, −19% — the Jan-2024 cold snap).
2025: over in all 12 (iHR 12–17 vs 9–14; Dec +72%).

**Structural reading:** the model's implied marginal heat rate is roughly
CONSTANT (~13–19) across regimes; the real market's swings from ~7 (soft,
solar/hydro/import-margin months) to ~14+ (tight months). In genuinely tight
months the model is within ±5% (Feb/Jul 2023, Jul 2024). The overprice lives
where the real marginal unit is NOT an in-state gas unit.

## 3. Three residual lanes

### Lane W — winter seam mispricing (Jan-2023 +48%, Jan-2024 −19%)
- Model Jan-2023 $222 vs actual DA $150; actual has only 38 of 456 covered
  January hours >$200 (worst day mean $217, Jan 4) — elevated-but-merit
  pricing at iHR ~9 on $16 gas. The model's 667 h energy-only tail >$200
  (2023) must sit essentially in January (Feb gas $7.1 needs iHR>28 to clear
  $200; Dec $3.8 needs >52) — the model manufactures a month-long scarcity
  regime the real market never had. Opposite sign in Jan-2024: the one month
  the model is LOW. The seam's winter response is wrong in both directions.
- **The keeper's measured per-hub seam has NO Jan–Mar 2023 coverage.**
  `wecc_intertie_lmp_hourly_CAISO.parquet` 2023 starts at hour 2040 (~Mar 27,
  OASIS retention); before that the corridors ride the static fitted ladder
  the 2026-06-19 import-ladder diagnosis flagged as "priced too high and
  aseasonally". **The GRP zips already on this branch contain the intertie
  nodes** (`MALIN_5_N101`, `CAPTJACK_5_N003`, `PALOVRDE_ASR-APND` — 24 h/day
  each in every DAM zip): the measured January seam is recoverable with an
  extension of `scripts/data/fold_caiso_oasis_grp_zips.py` + the
  `fetch_caiso_intertie_lmp.py` component-sum convention (LMP+MCC+MCL, no
  MGHG). Rule-14: use the measured input; whichever way it moves the
  residual, it replaces a fitted ladder in the miss month.

### Lane T — soft-month floor too high (the C3a body, 2024/25 + 2023 May/Jun/Sep/Dec)
- Actual sub-zero hours (hub series): 2023 DA 227/RT 397; 2024 DA 755/RT 868;
  2025 DA 561/RT 605. Hours <$15: ~1.3–1.6k/yr in 2024/25. The
  `caiso_import_solar_shape` flag doc records the model at **14 h ≤$0 vs
  actual ~868 (2024)** — but that legacy injector is superseded by the
  keeper's `caiso_per_hub_intertie`; whether the per-hub Path-46 corridor
  reproduces the midday negative tail post-caiso-80 is UNMEASURED (first
  no-LP check of the campaign).
- B1 (caiso-80 lane): model over-commits CC around the clock (+0.6…+2.5 GW
  overnight/morning). Overnight price rides committed-CC marginal cost while
  the real market clears cheaper (imports/hydro margin) — consistent with the
  constant-iHR signature and the C4 gas r=0.861 / NRMSE 0.305 (2023) miss.

### Lane S — tail formation (C3c, supporting tier)
- 2023: model 667 h >$200 (energy-only duals) vs actual DA 79 (lower bound),
  RT 21. 2024/25: model 0 h vs actual DA 52/0. Both signs wrong. The 2023
  spurious tail is Lane W's January; the missing 2024 tail is real local/
  sub-hourly scarcity the hourly single-zone-price LP cannot see (cf. the
  MISO DA-expressible-tail memo). Treat as W's dependent, not its own lane.

## 4. Already adjudicated — do NOT re-run
- Offer re-tune of the overprice: CONTRAINDICATED (caiso-80 B3, rule 1).
- Daily gas hub basis (`gas_hub_basis_daily`): caiso-54 probe, inert pre-80.
  Re-opening requires a stated cause (e.g. Jan-2023 intra-month citygate
  collapse $16–24 → $8–11 vs a flat monthly mean), not the residual.
- Belly under-commitment story: dead (B1 — model OVER-commits).
- NP15→Greater-Bay split: refuted ex-ante (caiso-79, cap cannot bind).
- Local-commitment response curve: refuted at estimation (caiso-81 LOYO);
  CT_PEAKER deficit (model 0.71/0.56/0.27 vs actual 4.13/4.33/2.37 TWh) stays
  open pending a measured regime source.
- `caiso_storage_as_reservation`: caiso-74 probe pair pruned as inert.
- `caiso_solar_cap_at_delivered`: rule-13 diagnostic ONLY (pins to outcome).

## 5. Campaign candidates
See the handoff (`docs/handoffs/caiso-price-residual-campaign-2026-07.md`)
for the ranked single-delta matrix, run mechanics (`replay_keeper.py --set`),
and governance rails. Headline order: (T1) measure the keeper's trough
formation vs the ≤$0 benchmark (no LP — needs one in-place keeper replay to
regenerate hourly parquets); (W1) intertie Jan-2023 backfill from the
committed GRP zips, then re-solve; (T2) per-hub midday shape / negative-tail
mechanism on the Path-46 corridor; (W2) `caiso_import_gas_coupling` /
`caiso_per_year_import_caps` winter legs; (T3) in-state solar negative-offer
depth audit (REC value vs observed DA floor).
