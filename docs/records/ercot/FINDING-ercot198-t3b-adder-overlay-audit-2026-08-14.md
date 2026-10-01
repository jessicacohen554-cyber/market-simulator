# FINDING — ercot-198: T-3b published-adder overlay-completeness audit — the committed overlay is INCOMPLETE in 2024 (missing published RTORPA, +0.24 $/MWh demand-weighted) and near-complete in 2025 (+0.015)

**Session ercot-198 `[FABLE]` (T3B-AUDIT executor lane), 2026-08-14, branch
`claude/ercot-scar-t3b-adder-audit`.** Executes **T-3b only** — the
published-adder overlay-completeness audit signed as card T's read-only
companion (`docs/DECISION-CARD-ercot196-shape-2024-2025-2026-08-13.md` §4
T-3b, RESOLUTIONS appended 2026-08-14, on main at `fb6d08d` via PR #3931;
dispatch: pack §0 cycle-9 / A9 staging). READ WORK ONLY: no mechanism, no
`ScenarioConfig` field, no solve, no LP, no run registered, no year scored,
no matrix cell or row edit, no keeper/registry/bench edit. Probe:
`scripts/probes/ercot198_t3b_adder_overlay_audit.py` → committed JSON
`results/calibration/ercot198_t3b_adder_overlay_audit.json`.

## 0. VERDICT

The card §2(d) question — *does the committed RTORPA/RTORDPA overlay capture
the full published adder content of 2024/2025 RTSPP?* — has a measured,
year-split answer:

* **2024 — INCOMPLETE.** The committed overlay carries **0.240 $/MWh**
  demand-weighted of the **0.477 $/MWh** settled published adder content —
  **50 %**. The missing component is named: the published **RTORPA** (the
  ORDC on-line reserve price adder), worth **+0.237 $/MWh** demand-weighted,
  concentrated **Apr +0.76 / Aug +0.64 / May +0.63 / Nov +0.27 / Jan
  +0.19**. The keeper's endogenous stand-in for RTORPA (the sidecar
  `ordc_adder`, the ORDC total-family reserve dual) is measured **≈ zero**
  (2 non-zero hours in 2024, max $0.15/h) — so the published RTORPA content
  is in bench `rt_lw_mon` and in *neither* the scored `pMon` *nor* the
  committed overlay.
* **2025 — NEAR-COMPLETE.** Committed **0.395** of **0.410 $/MWh** settled
  published content — **96 %**; gap **+0.015 $/MWh** (single visible month:
  Oct +0.13). 2025's published adder content is RTORDPA-dominated (ORDC
  active only 57 hours per the 2025 SOM), and the committed overlay carries
  the published RTORDPA **exactly** (input ≡ published series, max abs diff
  0.0). **Feb-2025's +1.50 $/MWh is fully captured — gap 0.00.**

**The true basis wedge of card §2(d) is therefore larger than measured in
2024 and essentially as measured in 2025**: on the card's mean-of-months
convention, 2024 **+0.25 → +0.48 $/MWh** (demand-weighted-hourly 0.240 →
0.477) and 2025 **+0.42 → +0.43** (0.395 → 0.410). Per §4 T-3b's charter this
finding states measured sizes only; the T-3a settlement-basis scoring
question stays with the owner, unsigned, and nothing is recommended here.

## 1. THE IDENTITY AUDITED

Bench `rt_lw_mon` is settlement RTSPP: per-LZ settlement point prices
(RTM 15-min averaged hourly), zone-demand-weighted
(`scripts/data/derive_actual_lmp.py::_lw_fields`). ERCOT's pre-RTC+B RTSPP =
time-weighted RTLMP + **RTORPA** + **RTORDPA** — the design's *only two*
energy-settlement price adders ("The current ERCOT market design features
two distinct price adders, the ORDC and the RDPA", 2024 SOM p. 43; both
retired at the RTC+B go-live 2025-12-05). ECRS-era price effects (ECRS
launched 2023-06) reach RTSPP *through* these two published adders — there
is no third settled adder; **RTOFFPA** (published in the same report) is not
part of energy settlement and is excluded (measured anyway: 0.178 $/MWh dw
2024, 0.010 2025).

The scored `pMon` is the demand-weighted energy-only dual (card §2(d),
verified on the keeper's sidecars). The keeper's committed settlement-side
content is sidecar `rtordpa_overlay` (measured published RTORDPA,
`ercot_rtordpa_overlay=True`, from
`data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`) **plus**
`ordc_adder` (the model's endogenous RTORPA analogue). The audit compares,
month by month on the shared non-leap 8760 clock with the keeper's own
demand weights: **published (RTORPA + RTORDPA) vs committed
(`rtordpa_overlay` + `ordc_adder`)**.

## 2. THE COMPARISON — demand-weighted $/MWh, month by month

**2024** (settled published; committed = rtordpa_overlay + ordc_adder, the
latter ≈ 0 everywhere):

| 2024 | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **dw yr** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| published RTORPA | 0.19 | 0.00 | 0.10 | **0.76** | **0.63** | 0.01 | 0.03 | **0.64** | 0.07 | 0.09 | **0.27** | 0.00 | **0.237** |
| published RTORDPA | 0.65 | 0.06 | 0.31 | 0.65 | 0.14 | 0.08 | 0.05 | 0.19 | 0.12 | 0.29 | 0.24 | 0.21 | **0.240** |
| published TOTAL | 0.84 | 0.06 | 0.42 | 1.41 | 0.77 | 0.08 | 0.08 | 0.83 | 0.19 | 0.38 | 0.51 | 0.21 | **0.477** |
| committed overlay | 0.65 | 0.06 | 0.31 | 0.65 | 0.14 | 0.08 | 0.05 | 0.19 | 0.12 | 0.29 | 0.24 | 0.21 | **0.240** |
| **GAP** | +0.19 | 0.00 | +0.10 | **+0.76** | **+0.63** | +0.01 | +0.03 | **+0.64** | +0.07 | +0.09 | **+0.27** | 0.00 | **+0.237** |

**2025** (through the RTC+B go-live 2025-12-05, hour 8112; the retired-regime
tail carries zero adder content by design):

| 2025 | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **dw yr** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| published RTORPA | 0.00 | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | **0.13** | 0.00 | 0.00 | **0.015** |
| published RTORDPA | 0.76 | **1.50** | 0.70 | 0.25 | 0.26 | 0.26 | 0.20 | 0.17 | 0.34 | 0.25 | 0.22 | 0.10 | **0.395** |
| published TOTAL | 0.76 | 1.50 | 0.72 | 0.25 | 0.27 | 0.26 | 0.20 | 0.17 | 0.35 | 0.38 | 0.22 | 0.10 | **0.410** |
| committed overlay | 0.76 | 1.50 | 0.70 | 0.25 | 0.26 | 0.26 | 0.20 | 0.17 | 0.34 | 0.25 | 0.22 | 0.10 | **0.395** |
| **GAP** | 0.00 | **0.00** | +0.02 | 0.00 | 0.00 | 0.00 | +0.01 | 0.00 | +0.01 | **+0.13** | 0.00 | 0.00 | **+0.015** |

Component identities, verified: `rtordpa_overlay` ≡ published RTORDPA (max
abs diff 0.0 — the overlay input *is* the published series, complete); the
entire gap is published RTORPA vs the model's ≈-zero endogenous `ordc_adder`
(2024: 2 non-zero hours, max $0.15; 2025: 1 hour, max $0.03). The committed
monthly overlay reproduces the ercot-196 `model_overlay_dw` column to
< $0.005 (its 2-dp rounding).

## 3. WHAT THE MEASURED SIZES DO TO THE RECORDED NUMBERS (sizes only)

* **Card §2(d) restated at full magnitude:** the basis wedge between scored
  `pMon` (energy-only) and bench `rt_lw_mon` (settlement) is **2024:
  0.477 $/MWh dw (0.48 mean-of-months), not 0.240 (0.25)** — the committed
  overlay measures half of it — and **2025: 0.410 (0.43), vs 0.395 (0.42)
  measured** — the committed overlay was already ~96 % of it.
  **Feb-2025 +1.50 stands unchanged** (~25 % of Feb-2025's −5.88 miss), and
  the "~15 % of the 2025 uniform bias" reading stands.
* **Month grain relevant to T1-EXEC's 2025/2024 interpretation** (resid =
  energy-only model − settlement actual; scoring both sides energy-only
  would shift each month's resid by +publishedTOTAL): Apr-2024 +6.16 →
  +7.57 and May-2024 +5.54 → +6.31 (the outage-season over-read is *larger*
  on a basis-consistent read); Aug-2024 −5.82 → −4.99; Nov-2024 −7.38 →
  −6.87; Feb-2025 −5.88 → −4.38; Dec-2025 −3.43 → −3.34.
* **T-3a is not touched:** the settlement-basis C3b scoring question remains
  merely recorded (card T signature: "T-3a is NOT signed"). This audit only
  fixes its measured size: the wedge T-3a would price is 0.48/0.43 $/MWh
  (2024/2025 mean-of-months), not 0.25/0.42.

## 4. INTAKE AND PROVENANCE (the "one data ask" resolved)

The card §4 T-3b cost line assumed the month-grain published adder series
was "not currently on disk". **It is on disk, committed, in two independent
published forms** — no new intake was needed and none was performed:

1. `data/raw/ercot/ercot_{2024,2025}_ordc_reserves_hourly.parquet` — curated
   from ERCOT MIS **NP6-905-CD "Historical Real-Time Price Adders by SCED
   Interval"** (reportTypeId 13231, annual archives
   `RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_<year>`, www.ercot.com MIS;
   fetcher `scripts/data/fetch_ercot_ordc_reserves.py`, provenance in the
   parquet metadata). Coverage: 2024 full 8760 h; 2025 8112 h with the
   post-go-live tail NaN (the regime ended 2025-12-05 — the series ends
   there, honestly).
2. `data/raw/ercot/RTSCEDPRICEADDERNP6323_RTORDCRELDEPpriceAdderNP6323_
   {2024,2025}.parquet` — the recovered raw **NP6-323-CD** SCED-interval
   report (34 columns incl. RTORPA/RTOFFPA/RTORDPA; committed at
   `d349be8b2`). Cross-check: monthly means agree with (1) to ≲ 0.2 $/MWh,
   the residual being pooled-interval vs hourly-mean aggregation (SCED runs
   extra intervals in events) plus CPT→CST edges. **Caveat: its 2024 file is
   missing June entirely** — (1) is the complete record and is the audit's
   basis.
3. Independent published cross-check — the committed **ERCOT State of the
   Market reports** (Potomac Economics, `data/raw/ERCOT/`): 2024 SOM Fig. 4
   (ORDC: 161 active h, $11.07 active, **$0.25 all-hours** vs our
   time-weighted 0.20) and Fig. 5 (RDPA: 837 h, $2.53, **$0.24** vs our
   0.23); 2025 SOM p. 30 (ORDC active 57 h, "contributed less than
   **$0.02/MWh**" vs our settled 0.013) and p. 31 (RDPA "**$0.41** per MWh
   for the year" vs our 0.40 over the pre-go-live span, 0.37 over the full
   8760). Agreement is within the settlement-interval vs hourly aggregation
   basis everywhere.

**Settlement-closure guard (one archive print rejected):** the MIS archives
retain original pre-price-correction values. Exactly one hour trips the
guard (archive adder total > settled hub RTSPP + $50): **2025 hour 4334
(Jun-30 14:00 CST) — archive RTORPA $414.12/h** (SCED prints near VOLL
against RTOLCAP 14.9 GW) **while the settled hub RTSPP was $54.96** (system
λ $41.61) — a corrected print that never settled, and the entire distance
between the archive's 2025 RTORPA (0.079 dw) and the SOM's < $0.02. Headline
numbers exclude it; with it included, 2025 published TOTAL would read 0.474
dw (Jun-2025 0.84) — reported in the JSON as
`published_uncorrected_archive`. Every other top adder hour in both years
closes against the settled bench (e.g. 2025 h7049 Oct-21 17:00: RTORPA
$36.07, settled RT $214.08 over λ $183.33).

## 5. GOVERNANCE — fences honored, what this session did not touch

Rulings **Q-B** and **R-A** cited and honored: 2023 was not read, solved,
scored, or discussed beyond this citation; ERCOT's determination posture is
untouched. Rule 22: data comparison only, no year solved or scored
(measured-vs-measured, rule 13 clean — actuals entered comparison only,
never any model input). No mechanism, no `ScenarioConfig` field, no matrix
cell or row edit (`ercot_rtordpa_overlay` stays **K**, read only — the card
§5 posture verbatim), no keeper/registry/bench edit, no run registered, no
new workflow. The keeper stays `2026-08-12-run192-arm-coal-peak`. New
artifacts of this session: the probe, its JSON, this finding, and one
calibration-log entry — nothing else.
