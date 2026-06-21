# Keeper sidecar — ERCOT ORDC tail + AS-reserve re-fit (run139, measured-2023)

**Bundle:** `ercot_dam_2023as_loadcredit` · **Branch:** `claude/ercot-ordc-resfit-agj2i9`
**Recipe:** run134's exact config, re-solved with the measured 2023 AS now in the
repo. Energy+reserve co-opt; CC-only measured DAM offers; run133/134
steam-derate-corrected `campd-unit-outages.csv`; `storage_as_commitment` on;
load-resource RRS-UFR credited from 2023, storage-AS *reserve* credit from 2025.

## Headline — all three years vs actual (demand-weighted system price, P1)

| config (current measured-storage code) | 2023 | 2024 | 2025 |
|---|---|---|---|
| run138 PROBE — no 2023 reserve credit | 58.4 (210/130) MAE 16.0 | 33.8 | 38.0 |
| **run139 KEEPER — +2023 load credit** | **43.1 (129/73) MAE 12.1** | 33.8 (69/43) | 38.0 (18/9) |
| run137 PROBE — +2023 load & storage reserve | 27.0 (33/15) MAE 24.2 | 22.5 (13/5) | 38.0 |
| actual | 48.4 (181/104) | 26.8 (53/16) | 32.5 (31/3) |
| run134 (prior keeper, *estimate* storage) | 49.8 (171/94) | 33.7 (69/43) | 37.9 (18/9) |

Tail = hours >$200 / >$500.

**The decisive result (and a reversal worth stating plainly).** The unlock was
building the measured 2023 AS; the surprise was how it moves 2023. `storage_as_
commitment` caps battery dispatch by the storage-AS series **every year**
(unscoped), so swapping the old intensity *estimate* (0.83 GW) for the measured
2023 storage (1.25 GW) holds more battery out of energy and **over-tightens
2023**: uncredited it runs 49.8 → **58.4**, *over* actual 48.4 with the tail
over-fired (210/130 vs 181/104). The measured **2023 load-resource RRS-UFR
credit** (884 MW) is the offsetting lever — it pulls 2023 to 43.1, the **best
2023 monthly MAE (16.0 → 12.1)**. So with both measured 2023 inputs + the correct
derates, **crediting 2023 load is right** — the brief's "measured 2023 reserves +
correct derates" combination. This *reverses* a mid-campaign read that compared
the credit against run134's estimate-storage baseline (apples-to-oranges).

**Honest caveats (no fitting — `scarcity.py` stays un-fitted):** the two measured
effects *bracket* actual rather than nailing it — uncredited over-shoots (+10,
tail over), credited under-shoots (−5, tail 129/73 under). The gate metric
(monthly MAE) picks the credit. The 2023 storage-RESERVE credit stays scoped off
(run137: crediting it double-relaxes to 27.0). 2024/2025 remain hot (33.8/38.0 vs
26.8/32.5) — the **separate** co-opt-adder over-fire in comfortable years
(run131 decomposition), out of scope for this 2023-focused re-fit.

## (i) Steam-coupling adoptability — YES

run133/134's regenerated `campd-unit-outages.csv` (the orphaned HRSG-steam derate
fix) is adopted as the physical baseline. It lifted the 2023 tail toward actual
(run132 46.7/151/88 → run134 49.8/171/94) and is correct physics, not a fit. The
keeper inherits it; it is what makes the measured-reserve interaction above the
*right* combination rather than papering over an outage bug.

## (ii) Measured-2023 AS build + DAMASAGGNP419 reconciliation

* **Storage AS (battery):** measured **~1.25 GW** (peak ~2.0 GW summer) from the
  60-Day Gen Resource Data PWRSTR awards (`build_ercot_as_by_restype_from_60day.py`,
  merged on main; an independent build via `build_ercot_as_2023.py` gave 1.22 GW
  — convergence within 2%). Replaces the intensity ESTIMATE (~0.83 GW, ~50%
  undercount).
* **Load-resource RRS-UFR:** measured-shape / cleared-level **~884 MW**
  (`scripts/build_ercot_as_2023.py` → `ercot_2023_as_up_mw.parquet`). RRS-UFR is
  load-only (generator awards = 0, verified). Cleared MW is not directly in the
  2023 files — the 60-Day Load file is *offers* (1.5 GW, ~2× cleared) and the
  residual `RRS_req − genPFR − genFFR` also overstates (1.6 GW) — so the series
  is the measured 2023 load-side RRS *shape* level-anchored to measured cleared
  RRS-UFR (NP3-911 Dec-2023 896 MW; 60-Day-derived 2024/2025 904/787), with the
  Dec tail = the NP3-911 series and the Oct 2–Dec 9 disclosure gap interpolated.
* **DAMASAGGNP419 reconciliation:** the aggregated cleared-offer curve gives
  RRSUF ~1505 MW (≈2× the 884 MW cleared anchor), the explicit confirmation that
  offers overstate and the credit must be cleared-level, not read raw.

## (iii) Re-derived ordc_as_plan_mw / RTOFFCAP basis (grounded, not fitted)

* **ordc_as_plan_mw stays 0** — correct for the keeper, which runs in **co-opt**
  mode where `ordc_as_plan_mw` (a *post-solve-overlay* lever) is inert. Co-opt
  nets reserves through the **measured per-resource credits** (load RRS-UFR +
  storage AS, scoped per year), not a flat tuned AS-plan subtraction. The
  ASPLAN-grounded AS-plan totals — 2023 **8.6 GW** (REGUP 0.4 / RRS 2.9 / ECRS
  1.9 / NSPIN 3.4), 2024 7.6, 2025 7.5 — are the measured netting basis those
  credits realize, never a price-target knob.
* **RTOFFCAP basis:** the post-solve overlay's "RTOFFCAP = 0" docstring was
  **stale** and is corrected — `reserve_headroom` returns the online / offline
  (quick-start gas-CT / oil) split and `ordc_adder` prices both tiers. In co-opt
  the offline reserve is **endogenous** (quick-start offline headroom in the
  shared-headroom RHS), grounded in the ASPLAN offline share (NonSpin offline,
  DAMASAGG OFFNS cleared-proxy ~3.9 GW + manual ECRS). No fitted RTOFFCAP
  constant is introduced.

## Not touched (honesty boundary)

VOLL, X, μ/σ, curve shift, RTORPA floors at published values; the offer body is
unchanged (run135 proved offer cooling is a markup, not a fix). `scarcity.py`
remains explicitly un-fitted to price residuals.
