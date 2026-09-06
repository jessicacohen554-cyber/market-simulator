# ADDENDUM to PRECOMMIT-caiso255 — PHASE 0 SCORED, and the SCREEN YEAR NAMED: **2023**

**Session caiso-255, 2026-09-06.** Pushed **BEFORE the screen solve is
launched**, as PRECOMMIT §7.1 requires ("the measured value of `argmax_y F(y)`
will be written into this document and pushed before the screen solve is
launched, so the naming cannot be back-fitted"). Keeper
`2026-09-05-caiso-252-b1-notrim` UNCHANGED, DETERMINATION **CALIBRATED**.
**ZERO LP spent so far.**

---

## §B.1 — P-1 … P-4, SCORED

| # | registered | measured | verdict |
|---|---|---|---|
| **P-1** | corpus re-fetches to 1,095 / 1,096, `20230601` the one genuine OASIS hole | **1,095 / 1,096**, per-year {2023: 364, 2024: 366, 2025: 365}, missing exactly `['20230601']` | **HOLDS** |
| **P-2** | the re-derive reproduces caiso-254's numbers **EXACTLY** | antimode `st_cut` **11.738**; CC **1.066/1.072/1.386**; CT_PEAKER **1.103/1.146/1.154**; ST_GAS **1.563/1.546/1.196**; G1 **0.871 / 0.970 / 0.895**; CT `bucket_mw` **7,391**; `ST_GAS.committed` no sample in 2024 & 2025 — **every value identical to the digit** | **HOLDS** |
| **P-3** | the **written** CT_PEAKER bucket is identical to the three-way run's | bands **1.103/1.146/1.154**, `bucket_mw` **7,391.0**, ratio **0.970**, `base_hr` 10.862 — identical; CC untouched at 1.066/1.072/1.386 | **HOLDS** |
| **P-4** | ST_GAS's G4 failure is still computed and **published** | `_provenance.reported_not_consumed.ST_GAS` carries bands 1.563/1.546/1.196, unarmed committed 1.367, **G4 `{"ordered": false, "pass": false}`** and G1 `{"ratio": 0.895, "pass": true}`; `classifier.classes` = all three, `classifier.consumed_classes` = CC+CT. The failure also remains in the top-level `gates.G4_physical_sanity` block | **HOLDS** |

**P-2 is the one worth pausing on.** The caiso-254 corpus died with its
container; this session re-fetched all 1,095 trade dates from OASIS
independently and rebuilt the reduced store from scratch. **Two independent
fetches and two independent store builds produce bit-identical measured
bands.** That is a reproducibility result the frozen artifact never had.

**GATES ALL PASS** on the consumed classes, and the artifact was written:
`caiso_offer_curve_measured.json` and `caiso_offer_surface_condbinned.json`,
both carrying top-level keys `['CC_REGULAR', 'CT_PEAKER']` only.

---

## §B.2 — PHASE 0: THE SCREEN YEAR IS **2023**

Estimator exactly as registered (PRECOMMIT §7.1): two on-recipe `fleet_only`
rebuilds per year differing ONLY in which artifact pair is on disk,
differenced on the model's own offer arrays.
**F and X contain no price actual, no residual and no criterion.**

| year | **F** (MW·$/MWh) | F_p1 | X (merit crossings) | gas tranches moved | **non-gas moved** | max abs Δmc |
|---|--:|--:|--:|--:|--:|--:|
| **2023** | **14,207.7** | **13,849.1** | 17,393 | 945 / 1,443 | **0** | $5.77 |
| 2024 | 7,514.4 | 7,324.9 | 15,374 | 951 / 1,448 | **0** | $3.05 |
| 2025 | 8,643.6 | 8,425.6 | 17,071 | 957 / 1,453 | **0** | $3.51 |

> ### **SCREEN YEAR = `argmax_y F(y)` = 2023.**
> The P1 channel independently agrees (`argmax_y F_p1(y)` = 2023), and the two
> channels are recorded as agreeing in the artifact's `channels_agree` field.

Evidence: `results/calibration/_caiso254_partition_footprint_phase0.json`.

**BOTH artifacts were swapped together.** The keeper carries
`caiso_offer_surface_conditional = True`, so the conditional ladder is armed
and it moves too (CT_PEAKER `peak_p50` 1.234 → 1.211, the whole binned ladder
shifting; CC_REGULAR's ladder is **byte-identical**). The probe swaps both and
**refuses a hybrid arm**; its log confirms the P1 channel is live — "repriced
380 gas peak-rung rows across 4 net-load bins (tightest bin binds 263/8760
hours)". A single-artifact swap would have made **F_p1**, i.e. the pass every
run is scored on, invisible to its own footprint estimator.

### §B.2.1 — Two things stated because they are uncomfortable, not because they help

1. **caiso-254 ADDENDUM P-8 is FALSIFIED.** It predicted "F(2025) largest, so
   2025 is the screen year". **2023 is the argmax by 1.64×** over the next
   year. Its own escape clause ("a different argmax is fine and is simply
   used") applies, and the discriminating condition it worried about is
   comfortably met: F is **not** within ±10 % across the three years
   (14,208 / 7,514 / 8,644), so the criterion separates cleanly and no
   tie-break is needed.
2. **2023 is the year in which the disclosed C1 gate weakness does NOT apply,
   and this is an ACCIDENT, not a design.** ADDENDUM-caiso254 §1.3.2 disclosed
   — before any year was named — that the keeper's **C1 gas records for 2025
   are all SKIPPED** on the preliminary EIA-923 vintage, so a 2025 screen would
   have left S-3 with little bite. The year was named by F alone, which
   contains no criterion; that it landed on the year with the *stronger* gate
   is luck running in the arm's favour. **It is reported as luck.** Had F named
   2025, 2025 would have been screened with the weakness disclosed, exactly as
   §1.3.2 committed.

---

## §B.3 — WHAT THE SCREEN WILL BE, unchanged from PRECOMMIT §7.2

The gate is **STRUCTURAL and STOP-ONLY**, fixed before F was measured and not
re-specified now:

* **S-1** — CT_PEAKER energy **RISES** in 2023, within a factor of 3 of what
  F(2023) implies. (The ST_GAS leg is reported INERT-BY-CONSTRUCTION, not
  relaxed — caiso-254 §3.)
* **S-2** — nuclear / hydro / wind / solar each move **< 0.5 %** of keeper
  annual energy. Storage, imports and the CC classes are reported, not gated.
* **S-3 / S-4** — a C1 or C4 PASS → FAIL flip **STOPS** the screen and
  **ESCALATES to the owner**; it neither kills the arm nor lets it proceed
  silently.
* **C3a is EXCLUDED in both directions. Neither C3a nor C4 may PROMOTE.
  `co2` is excluded.**

**Solve driver** (ADDENDUM-caiso255-solve-path-correction): the arm is the
keeper's byte-faithful replay with **both** artifacts swapped underneath it —
`scripts/replay_keeper.py results/calibration/caiso252_b1_notrim --out-dir
<arm> --years 2023`. The P1 basis seed is hard-off on that driver twice over,
and the FINDING records the arm's resolved `MARKET_SIM_WARMSTART_XYEAR` /
`MARKET_SIM_P1_BASIS_SEED` and the solve log's cold-P1 line as evidence rather
than assertion.

**The screen bundle is a throwaway probe** — never registered, never a keeper,
its year re-solved inside the full bundle, and **DELETED from
`results/calibration/` before the PR merges** (rule 29(c)).
