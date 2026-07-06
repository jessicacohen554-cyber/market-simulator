# nyiso 54 downstate-daily — CT offer re-grounded on measured DAILY delivered gas

**Run id:** `2026-07-06-nyiso-54-downstate-daily` · **PROBE / CANDIDATE**
(keeper stays `2026-07-06-nyiso-53-li-tsl`). Years 2023/2024/2025, the nyiso-53
recipe (nyiso-41 keeper meta at HEAD + PR-#1442 re-derived floors +
`nyiso_li_lcr_tsl` + `use_plant_emission_rates_v2`) with ONE change:

* **`nyiso_downstate_ct_gas_daily=True`** replaces the monthly premium adder
  (`nyiso_downstate_ct_gas_basis=False`; one mechanism per phenomenon, rule 19).
  Each downstate CT_PEAKER unit's gas is SET to the curated **`nyiso-downstate-gas`**
  daily index = measured Transco Z6 NY pipeline-hub **daily** spot + measured
  monthly LDC city-gate premium (free-data memo §1.4). The daily Transco spot
  carries the cold-snap blowouts (Jan-2024 $23.90, up to $29.84/MMBtu in 2023)
  on the exact days the interruptible peakers run, which the monthly mean smears
  away. Resolves **G-13** (the CT-offer-grounding blocker). Adds **zero new free
  parameters** — a measured, forward-native delivered-fuel input (rules #11/#13),
  not a fitted band.

## Scorecard (vs the nyiso-53 keeper, same scoring basis)

| criterion | nyiso-53 keeper | **nyiso-54 (daily)** | verdict |
|---|---|---|---|
| C1 fuel-mix | PASS | **PASS** | = |
| C3a mean LMP | −9.0/−10.9/−10.6% | **−9.1/−10.7/−10.4%** | wash |
| C3b NRMSE | 0.182/0.221/0.190 | **0.185/0.222/0.181** | wash |
| C3c >$300 h | 0/0/7 (of 10/12/42) | **same** (blocked on #1344) | = |
| C7 diurnal | PASS | **PASS** | = |
| C8 ST_GAS forced | 60.8/69.8/59.7% | **64.8/75.9/59.7%** | marginally worse |
| CT_PEAKER grid vol | 1.28/1.44/2.40 | **1.29/1.35/2.13** (actual 2.26/2.13/2.84) | marginally deeper under-run |

(CT_PEAKER C8 is SKIPPED under rubric v2.1 — 1.4–1.9 % of ISO load < 2 %
materiality floor; the C8 FAIL driver is ST_GAS in both runs.)

## Reading

The daily re-grounding is the correct delivered-fuel physics: pricing the
downstate peakers at the measured daily hub lifts their offer on the scarce cold
days they actually run, nudging ~0.1–0.3 TWh/yr of marginal CT energy to
CC/imports (cheaper than the dearer downstate steam) rather than letting an
HR~9-10 LM6000 run on a smeared monthly-mean gas. ST_GAS absolute energy is
unchanged (7.2/8.2/10.3 TWh), but its economic share shrinks slightly, so its
D-2 forced share rises a few points.

Its price signal is **absorbed by the missing reserve-scarcity commitment
frontier** (#1344, data-blocked, Ask-B): the peakers the real market commits for
reserve sit idle in the pure-ED LP, so pricing their gas correctly cannot
manufacture the >$300 tail (C3c) or move the mean (C3a). The result is a
**structurally-faithful refinement that does not move the residual** — kept in
the codebase as a default-off curated datatype (rule #1: a real market behaviour
stays in even when the fit doesn't improve), but **not promoted** because it is
not ≥ nyiso-53 (a wash on price, marginally worse on C8).

**Determination: NOT-YET** (C6 unattested probe; C8 ST_GAS + C3c ledgered on
#1344; C3a/C3b soft, best-to-date). Keeper stays `2026-07-06-nyiso-53-li-tsl`.
Ablation twin: `2026-07-06-nyiso-54-downstate-daily-ablation`.
