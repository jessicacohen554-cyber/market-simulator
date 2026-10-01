# RESULT — SPP-73, xiso lever (b): COMMITMENT REACH IS NOT THE CAUSE

**Zero LP. No shard, no solve, no bundle, no `ScenarioConfig` field.** Pre-registration:
`docs/handoffs/PRECOMMIT-spp-73-commitment-reach-2026-09-22.md`, pushed at `91df082f` before any
number below was read. Base `f8188a1e`. Probes: `scripts/probes/_spp73_commitment_reach.py`
(M1/M1b/M1c/M2), `_spp73_commitment_params_census.py` + `_spp73_startup_ceiling.py` (M4).
Outputs: `results/calibration/_spp73_*.json`.

---

## 0. Headline

- **SPP's own day-ahead unit commitment did not price these hours either.** In the RT top-88
  hours, DA cleared at a median **$26.9 in 2020**, against RT **$144.4** and the model **$23.7**.
  The real commitment market closes **2.6 %** of the gap (2019 4.5 %, 2022 14.9 %). No hourly
  commitment lever can beat the market's own commitment solve.
- **The model's thermal fleet already behaves like the real one in those hours.** CAMPD shows
  real CT output rising ×1.47 into the top hours versus ×1.32 in the model; CC and ST_GAS match.
  Real SPP had some CT online in **100 %** of hours in every year, so "CTs on in 95 % of hours" is
  not a model defect.
- **No published, per-class SPP start-up cost exists.** The pre-registered STOP applies.
- **C3a 2020 is a BODY error, not a tail error.** Non-top hours carry **+$3.78** of the **+$2.27**
  gap; the top-88 carry −$1.51. A lever that raises tail prices moves C3a the wrong way.
- **So commitment reach is not the cause, and every hourly lever on the xiso ranking is now
  exhausted for SPP** (demand SPP-72, reserve SPP-55, offer-curve family xiso). The tail goes to
  the RT-wedge object C3c already ledgers. **But not all four rows are that object:** C3b 2020 and
  2022 are reachable in principle by *some* hourly object (DA passes them), and it is not
  commitment. §6 says what that leaves.

## 1. The four rows, re-verified

`calibration_verdict.py --run-id 2026-09-22-spp-71-rung-ensemble` → NOT-YET. C3a 2020 FAIL
(+17.3 %); C3b 2020 / 2021 / 2022 **0.267 / 0.243 / 0.208**. My reconstruction reproduces all four
from the committed hourlies (+17.4 %, 0.267, 0.243, 0.208), so the instrument below is the scorer's.

## 2. M1 — the DA bound (decides V1)

φ = (med_DA − med_MOD) / (med_RT − med_MOD), over `H_top` (SPP-72's hour set, byte-for-byte).

| year | med RT | med DA | med model | numerator | denominator | **φ** | DA > $200 / RT > $200 in `H_top` |
|---|---:|---:|---:|---:|---:|---:|---|
| 2019 | 209.9 | 33.4 | 25.0 | 8.4 | 184.9 | **0.045** | 0 / 47 |
| **2020** | **144.4** | **26.9** | **23.7** | **3.1** | **120.6** | **0.026** | **0 / 23** |
| 2021 | 1,062.6 | 2,262.6 | 196.4 | 2,066.1 | 866.2 | 2.385 | 70 / 88 |
| 2022 | 279.7 | 92.9 | 60.1 | 32.8 | 219.6 | **0.149** | 1 / 88 |
| 2023 | 193.7 | 39.6 | 31.5 | 8.1 | 162.2 | 0.050 | 2 / 42 |
| 2024 | 222.7 | 87.4 | 36.0 | 51.4 | 186.7 | 0.275 | 18 / 59 |
| 2025 | 246.3 | 49.0 | 36.6 | 12.4 | 209.7 | 0.059 | 0 / 68 |

**V1 = NOT REAL** (φ_2020 < 0.5; 2019 and 2022 < 0.5). 2021 is Uri: DA priced *above* RT.

## 3. M1b — score the measured DA series as if it were the model

Scorer arithmetic (`_nrmse`), committed actual (`bench.avgLMP.rt` / `rt_mon`, reproduced to
$0.005). Pre-registered rule: **DA fails a row ⇒ no hourly commitment representation can pass it.**

| row | model (scorer) | DA, demand-weighted (primary) | DA, equal-hour (robustness) | reading |
|---|---:|---:|---:|---|
| C3a 2020 (±10 %) | +17.3 % FAIL | **+12.8 % FAIL** | +7.2 % pass | UNREACHABLE on the primary basis; split on robustness |
| C3b 2020 (≤ 0.20) | 0.267 FAIL | **0.173 pass** | 0.158 pass | reachable in principle by *some* hourly object |
| C3b 2021 | 0.243 FAIL | **2.877 FAIL** | 2.590 FAIL | UNREACHABLE (Uri DA) |
| C3b 2022 | 0.208 FAIL | **0.163 pass** | 0.103 pass | reachable in principle by *some* hourly object |

Context: DA runs above RT in SPP. Demand-weighted DA fails C3a against RT in **6 of 7 years**
(+10.3 to +93.2 %). A model that matched DA would fail C3a.

## 4. M2 — measured commitment state (CAMPD, SWPP-BA plants) vs the model

145–148 CT, 46–47 CC, 51–60 ST_GAS units. 2019–2022 lack WY's CAMPD file, which is a small SPP
presence. Control = requirement-matched, outside the top-10 % RT hours; no top hour went unmatched.

| year | CT output ratio, top ÷ control: measured / model | CT starts-into-hour share, top / control (measured) | CT hours with output > 0: measured / model | CT mean MW: measured / model | V2 |
|---|---|---|---|---|---|
| 2019 | 1.38 / 1.26 | 0.225 / 0.138 | 1.00 / 0.97 | 1,520 / 1,578 | no |
| **2020** | **1.47 / 1.32** | **0.257 / 0.157** | **1.00 / 0.95** | **1,230 / 1,747** | **no** |
| 2021 | 1.83 / 1.10 | 0.088 / 0.172 | 1.00 / 0.79 | 1,121 / 991 | no |
| 2022 | 1.41 / 1.50 | 0.213 / 0.141 | 1.00 / 0.83 | 1,289 / 971 | no |

CC ratio, measured / model: 0.91 / 0.88 (2020); 0.96 / 0.95; 0.71 / 0.75; 0.98 / 1.03.
ST_GAS: 1.24 / 1.12 (2020). **V2 is absent in all seven years.** Reality does not hold its peakers
back at mid load and start them into the spike more than the model does. In 2020 it runs ~45 of
145 CTs in the top hours and ~29 in matched hours. The model is 42 % too high on annual CT energy
(1,747 vs 1,230 MW mean), a C1/dispatch issue, and it rises into the spike almost as much as reality.

## 5. M3 / M4 — the parameters, and whether P0→P1 can bite

**M3, the source survey (STOP).** SPP's `historical-offers` product publishes energy price/MW
pairs only: no start-up, no-load, min-run or min-down. The MMU ASOM (Figure 3-6) publishes
fuel-level fleet averages of self-reported physical parameters; gas min-run is "just shy of one
day", lumping CT, CC and ST together. Make-whole payments are published only as totals. **There is
no published per-class start-up cost**, so the pre-registered STOP holds.

**M4 — correcting an inherited premise.** SPP-71 §8 said `startup_cost_per_mw = min_run =
min_down = 0` on every unit. A `fleet_only` rebuild of rung 2020 shows that is wrong:

| rows | MW | start-up $/MW | min-run / min-down h |
|---|---:|---:|---|
| coal `_committed`, 32 | 6,273 | 100 | 36 / 16 |
| CC `_committed`, 24 | 3,581 | 50 | 0 / 0 |
| ST_GAS + ST_CHP `_committed`, 37 | 2,061 | 35 | 0 / 0 |
| CT_PEAKER + CT_CHP `_committed`, 42 | 1,123 | 20 | 0 / 0 |
| every gas econ / peak tranche | the rest | **0** | 0 / 0 |

So the P0→P1 channel is live (`compute_monthly_markup`, `commitment.py:314-331`; P1 bid
`mc_base + markup`, `pipeline/solve.py:602-614`) on **98** of those rows. The 37 ST rows are inert
because `gas_st_startup_cost` is off (`commitment.py:307-313`). But it is bounded. The markup is at most
start-up ÷ 1 h. Even in that degenerate case, the highest P1 bid any **gas** row could carry in
2020's top hours is a median **$79** (an over-bound: it credits ST its inert $35), against RT
**$144**. RT exceeds that gas ceiling in **88 of 88** top hours in 2019 and 2020, and 85 of 88 in 2022. The whole-fleet ceiling of $211 exists
only through oil rows, and the LP stops 5.5 GW short of those (SPP-70 §4). M2 shows reality did
not exhaust its gas stack in those hours either. (`_spp73_m4_startup_ceiling.json`.)

## 6. What is left, stated plainly

- **The tail is the RT wedge.** φ ≤ 0.15 in every non-Uri rung year. C3c already ledgers it.
- **C3a 2020 is the body.** The model is too dear in ordinary hours. Scored like-for-like
  (equal-hour model vs the equal-hour actual) it is still **+13.7 %**. That is still a FAIL, but
  demand-weighted DA's +12.8 % shows the market's own hourly price sits in the same place.
- **C3b 2020 and 2022 are open, and not commitment.** DA passes both. The model's monthly errors
  are level errors in whole months: 2020 Nov **+8.6**, Dec +6.2, Oct −6.1 $/MWh; 2022 Jun–Aug
  −11 to −15, Oct–Nov −9 to −12. That is the same class as the C3a body error. This lane does not
  identify it, and does not propose a lever for it.
- **Post-hoc, declared: the scorer's basis.** SPP's benchmark has no `rt_lw`, so C3a/C3b compare a
  demand-weighted model against an equal-hour actual. Scoring like-for-like changes **no**
  verdict: C3a 2020 +13.7 %; C3b 0.257 / 0.286 / 0.225. This is routed to the rubric owners as a
  note, not acted on.

## 7. Predictions, scored

| # | prediction | outcome |
|---|---|---|
| P1 | φ_2020 < 0.5, around 0.1–0.3 | **HIT**. 0.026, below my range. |
| P2 | V1 NOT REAL | **HIT** |
| P3 | DA fails C3a 2020, same sign | **HIT** on the primary basis (+12.8 %). Equal-hour robustness passes (+7.2 %). |
| P4 | DA fails C3b in ≥ 2 of 2020–2022 | **MISS**. Only 2021 fails. |
| P5 | ρ_meas(CT) > ρ_mod(CT) in 2020; V2 met | **Direction HIT** (1.47 > 1.32). **Threshold MISS** (needs ≥ 1.98; starts 1.64×, needs 2×). |
| P6 | measured CT mean ≤ 50 % of model | **MISS**. 70 % (1,230 / 1,747). |
| P7 | M4 counts 0/0/0; markup ≡ 0 | **MISS**. 135 / 32 / 32 rows. The inherited premise was wrong (§5). The verdict does not depend on it. |
| P8 | non-top hours carry > 100 % of C3a 2020's gap | **HIT**. 166 %. |

Expected row movement for any hourly commitment lever, as pre-registered: C3a 2020 gets worse by
sign; C3b is ambiguous; C3c is untouched. Nothing was solved, so nothing moved.

## 8. Rules and state

- **Rule 1 / 13 / 14:** no mechanism proposed. The DA series and CAMPD state are used only as
  **diagnostics**, never as inputs (SPP-46 §4.1 already found measured commitment state
  inadmissible as a window).
- **Rule 19 / 21 / 25:** not engaged, because the §6 gate of the PRECOMMIT did not fire. No field was added.
- **Rule 28:** no cell verdict changed, because no mechanism was tested. SPP-73 bound notes were
  added to the seven `U` cells on this lever. A DO-NOT-REDO block was added to §5.7, and the §5.7
  header was re-stamped to keeper 15 (a pre-existing drift warning).
- **Keeper 15 untouched.** `audit_keepers --iso SPP` and
  `build_dof_ledger --iso SPP --check spp71_ensemble_span` were re-run at the end (§9).
- Every number here is model-SELECTION evidence (`[R-HOLDOUT]` removed 2026-09-09).

## 9. Cost and retrievability

0 LP minutes. No shards and no bundles, so there is nothing to promote, nothing to archive and
nothing at risk under rule 31. Everything reproduces from `main` with the three probes above.
