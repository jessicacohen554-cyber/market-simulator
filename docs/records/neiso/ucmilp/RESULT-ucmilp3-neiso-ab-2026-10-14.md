# RESULT — UC-3-NEISO: clean MILP unit-commitment A/B at engine uc-1.4 on all seven NEISO years (calibrated control) — **R: defect 6 is gone and the span solves 2,555/2,555 windows Optimal; no gated flip; the price body rises in every year (C3a away from 0 by 2.2–3.5 pp in five years; C3b worse by > 0.02 in 2022 and 2025; |ΔC3a 2023| = 2.6 pp toward the actual)**

**Lane:** UC-3-NEISO · **Session:** `session_01XS3YxX7AQRJFBAQoGi6TRF` (Opus) · **Date:** 2026-10-14 · **Branch:** `claude/ucmilp-3-neiso-ab`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), on the owner's ruling of 2026-10-14 (*"Go with your recommendations"*; plan r08 decision 7).
**PRECOMMIT:** `PRECOMMIT-ucmilp-neiso-ab-2026-10-10.md` §§1–8 unchanged, plus **Addendum F**. Addendum F covers the pin, G-DRIFT `eab17188 → 580c4fbf`, the kill and verdict rules restated, and the declared carry of the L1 gate. It was pushed at `b9eed86f` before any shard existed.
**Pin solved:** `b9eed86fd95ba4899a87d35de8b73435e7b2bc37`, which is `580c4fbf` (engine uc-1.4) plus docs only.
**LP in this session:** zero. Seven year-isolated shards (rule 36).
**Registered:** nothing (E13). Scoring used a local sidecar and payload (`2026-10-14-ucmilp3-neiso-uc-b`) that were removed before the commit (§8(d)). No bench part was rebuilt.

## 0. Headline

**Engine defect 6 is fixed in NEISO.**

| | control | uc-1.2 arm | uc-1.4 arm |
|---|---|---|---|
| hours/yr with CC_REGULAR `peak` band > 1 MW | 14–467 | 8,758–8,760 | **74–1,010** |
| CC_REGULAR peak-band TWh/yr | 0.002–0.196 | 0.44–0.66 | **0.009–0.248** |

The arm now keeps the peak tranches near the control (+0.003 to +0.081 TWh). The residual peak-hour increase is in-merit dispatch at higher prices, not a floor. MECH 28 now fills the `committed` tranche (+4.5 to +7.3 TWh/yr).

**The solve is clean.**
- 2,555 / 2,555 windows Optimal, 0 time-limit hits, 0 infeasible.
- Every P1 Optimal, 0 MWh unserved.
- Make-whole 0.74–1.08 % of energy cost.

**The calibrated control does not flip on any gated criterion.**
- C1, C2, C3a, C3b, C4 and C8 are PASS → PASS in every scored year.
- The only status changes are the unattested-probe artefacts: C6 UNATTESTED, and C3c CAVEAT → FAIL in 2022, 2023 and 2025 at identical magnitudes (0 h modelled vs 117 / 15 / 20 h > $300).

**The verdict is R under the fixed §7 rule, on three independent counts:**
1. **C3a moves away from 0 by more than 1 pp in five years:** 2019 +2.67, 2021 +2.18, 2022 +3.16, 2024 +3.14, 2025 +3.49 pp.
2. **C3b worsens by more than 0.02:** 2022 0.091 → 0.113 and 2025 0.070 → 0.103. 2019 is +0.020 at the scorer's rounding.
3. **Kill #3 by the letter:** |ΔC3a 2023| = 2.60 pp (−3.04 → −0.45 %). The move is *toward* the actual.

**2019 is the nearest edge.** C3a reads +9.51 % against the +10 % FAIL band, 0.49 pp of headroom.

**This R is no longer an engine artefact.** The price rise is the UC's commitment decision itself (§2): it holds units of multi-unit CC plants offline that the relaxed P1 ran. The keeper's offer bands were set ex ante on the relaxed posture, so that interaction is part of the reading. Nothing is tuned (rule 1).

### 0.1 Gate table, control → arm

- **Control:** keeper `2026-10-02-w0-neiso`, re-scored at HEAD on the same committed bench parts; it is identical to its registered record.
- **Arm:** this span. Both arms scored at rubric 3.20.

| year | C1 (class rows) | C2 | C3a (model/actual − 1) | ΔC3a | C3b NRMSE | C3c (> $300 h, model / RT) | C4 gas (r, NRMSE) | C8 CC_REGULAR forced share, scored (MECH 28 removed) | unserved MWh | uplift % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | all PASS → all PASS | PASS → PASS | +6.84 → **+9.51 %** PASS | **+2.67 (away)** | 0.105 → 0.125 PASS (+0.020) | PASS → PASS (0 / 0) | 0.937 / 0.141 → 0.936 / 0.143 | 0.7 → 2.7 % (0.6 %) PASS | 0 → 0 | 0.92 |
| 2020 | all PASS → all PASS | PASS → PASS | −1.23 → +0.04 % PASS | +1.27 (toward 0) | 0.111 → 0.115 PASS | PASS → PASS (0 / 0) | 0.961 / 0.117 → 0.962 / 0.114 | 1.7 → 3.3 % (1.3 %) PASS | 0 → 0 | 0.90 |
| 2021 | all PASS → all PASS | PASS → PASS | +2.85 → +5.02 % PASS | **+2.18 (away)** | 0.120 → 0.137 PASS | PASS → PASS (0 / 2) | 0.960 / 0.107 → 0.962 / 0.104 | 1.2 → 3.0 % (1.1 %) PASS | 0 → 0 | 0.82 |
| 2022 | all PASS → all PASS | PASS → PASS | +2.47 → +5.63 % PASS | **+3.16 (away)** | 0.091 → **0.113** PASS (**+0.022**) | CAVEAT → FAIL* (0 / 117) | 0.940 / 0.132 → 0.940 / 0.133 | 1.1 → 2.5 % (1.1 %) PASS | 0 → 0 | 0.95 |
| 2023 | all PASS → all PASS | PASS → PASS | −3.04 → −0.45 % PASS | **2.60 (toward 0; the 1-pp bar year)** | 0.096 → 0.104 PASS | CAVEAT → FAIL* (0 / 15) | 0.940 / 0.101 → 0.944 / 0.099 | 0.4 → 1.8 % (0.3 %) PASS | 0 → 0 | 1.08 |
| 2024 | all PASS → all PASS | PASS → PASS | +0.46 → +3.60 % PASS | **+3.14 (away)** | 0.152 → 0.171 PASS (+0.019) | PASS → PASS (0 / 8) | 0.952 / 0.091 → 0.948 / 0.094 | 0.7 → 1.5 % (0.4 %) PASS | 0 → 0 | 0.97 |
| 2025 | SKIPPED → SKIPPED (preliminary EIA-923) | SKIPPED | +3.80 → +7.29 % PASS | **+3.49 (away)** | 0.070 → **0.103** PASS (**+0.033**) | CAVEAT → FAIL* (0 / 20) | 0.904 / 0.145 → 0.880 / 0.165 | 0.5 → 1.4 % (0.4 %) PASS | 0 → 0 | 0.74 |

\* Unattested-probe artefact (Addendum B precedent). The determination reads control CALIBRATED, arm NOT-YET, on governance UNATTESTED only.

- **C8.** The scorer budgets `uc_schedule` energy, so C8 is shown both ways. MECH 28 is 0.59–0.92 TWh/yr of CC_REGULAR (1.0–2.1 % of class); ST_GAS reads ≤ 0.001 TWh.
- **D-4.** The FAIL set is identical to the control's (2021 `chp_steam` plant 54605).
- **D-1.** It is not gated, so it is reported only. The arm adds 2024 COAL_BIT (profile r 0.720) and 2025 COAL_BIT (off-peak CV ratio 0.456). These are the same two rows uc-1.2 added. The other D-1 rows are the control's own.

### 0.2 GATESPEC §6.1 wall rows

Run conditions:
- standard solve container, 4 cpus, ceiling 13.36 GiB + 10 GiB swap;
- solver path `{presolve on, feasibility_jump off, lp_heuristics off, symmetry on, restart off}`;
- `uc_slim_window=True`;
- pass-2 reuse did not fire in any leg (no second stage in NEISO).

The baseline is the same shard's P0 + P1 (§5 proxy).

| year | P0 s | UC Σ s (mean / p95 MILP s) | P1 s | total s | **total ÷ (P0+P1)** | integer clusters / clusters (CC integer GW) | gate set | nodes p50 / p95 | gap p95 | TL hits | non-opt windows | peak RSS GiB | shard wall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 82.5 | 2,488.1 (6.74 / 26.29) | 100.0 | 2,715.0 | **14.9** | 18 / 61 (10.3) | 38 | 9 / 118 | 9.95e-4 | 0 | 0 | 4.66 | 45 min |
| 2020 | 113.1 | 2,060.3 (5.52 / 17.16) | 135.1 | 2,379.4 | **9.6** | 19 / 64 (10.2) | 40 | 3 / 59 | 9.97e-4 | 0 | 0 | 5.06 | 40 min |
| 2021 | 94.7 | 3,673.7 (9.98 / 42.69) | 87.8 | 3,902.5 | **21.4** | 22 / 68 (10.3) | 40 | 11 / 170 | 9.95e-4 | 0 | 0 | 5.18 | 65 min |
| 2022 | 80.9 | 5,187.5 (14.13 / 45.10) | 90.1 | 5,408.6 | **31.6** | 19 / 69 (10.2) | 35 | 20 / 267 | 9.98e-4 | 0 | 0 | 5.05 | 91 min |
| 2023 | 91.5 | 4,178.4 (11.34 / 39.66) | 105.3 | 4,430.1 | **22.5** | 22 / 70 (9.9) | 37 | 8 / 181 | 9.97e-4 | 0 | 0 | 5.02 | 74 min |
| 2024 | 79.5 | 3,667.4 (9.97 / 52.00) | 83.7 | 3,872.5 | **23.7** | 21 / 71 (9.7) | 36 | 1 / 457 | 9.92e-4 | 0 | 0 | 5.00 | 65 min |
| 2025 | 90.9 | 3,484.1 (9.45 / 47.40) | 97.7 | 3,720.9 | **19.7** | 19 / 68 (8.2) | 33 | 1 / 249 | 9.93e-4 | 0 | 0 | 4.93 | 62 min |

- **Integer set, ruling (a).** The integer set is unchanged from uc-1.2: 18–22 of 61–71 clusters, of which 17–20 CC (8.2–10.3 GW of ~15 GW), 0–3 ST_GAS (≤ 0.11 GW) and 0–1 coal (0.26 GW).
- **Wall.** The wall is the window MILP, which is unchanged from uc-1.2: UC Σ is 0.77–1.26× the uc-1.2 legs' (container noise; the uc-1.2 2022 leg carried one time-limit hit). D-2 ("Keep 3×; fund speedup") is reported, not judged.

## 1. The pre-fixed readings (PRECOMMIT §§2–5)

Order in every cell: 2019 · 2020 · 2021 · 2022 · 2023 · 2024 · 2025.

| # | reading | control | arm | bar | met? |
|---|---|---|---|---|---|
| T1 | M3 lower-tercile mean error $/MWh | +10.56 · +6.75 · +11.15 · +25.92 · +9.95 · +10.21 · +15.90 | +11.38 · +7.30 · +12.01 · +28.62 · +10.80 · +11.13 · +17.36 | toward 0 | **no, away every year** (+$0.6 … +$2.7) |
| T2 | ratio of hours ≤ $15, model / actual | 0.350 · 0.020 · 0.006 · 0 · 0.427 · 0 · 0 | 0.350 · 0.000 · 0.006 · 0 · 0.455 · 0 · 0 | rises | rises in 1 of 7 (2023), falls in 2020 |
| T3 | ratio of hours < $0 | 0 · 0 · 0.033 · 0 · 0 · 0 · 0 | identical | rises | no move |
| T4 | reserve dormancy | n/a (no NEISO AS reference on disk) | reserve MCP < $1 every hour, as the control | — | no move |
| §3 | gated flip | — | **none** (artefacts aside) | none | met |
| §3 | \|ΔC3a 2023\| ≤ 1 pp | −3.04 % | −0.45 % (**2.60 pp**, toward the actual) | ≤ 1 pp | **not met → kill #3** |
| §3 | P1 Optimal; unserved ≤ +500 MWh; no new D-4 row | — | 7 / 7; 0 MWh; D-4 identical | — | met |
| §7 | C3a away from 0 by > 1 pp | — | 2019 · 2021 · 2022 · 2024 · 2025 (+2.2 … +3.5 pp) | none | **fires (R)** |
| §7 | C3b worse by > 0.02 | — | 2022 +0.022, 2025 +0.033 (2019 +0.020 rounded, 2024 +0.019) | none | **fires (R)** |
| S1 | MECH 28 CC_REGULAR (TWh, % of class) | 0 | 0.92 · 0.90 · 0.92 · 0.76 · 0.75 · 0.61 · 0.59 TWh (2.1 · 1.9 · 1.9 · 1.5 · 1.4 · 1.1 · 1.0 %); ST_GAS ≤ 0.001 TWh; coal 0 | reported | — |
| S2 | CC_REGULAR starts vs CEMS | 1.049 · 1.187 · 0.998 · 1.063 · 1.245 · 1.378 · 1.139 | 0.870 · 1.170 · 0.892 · 0.949 · 1.157 · 1.290 · 1.085 | closer in ≥ 4 of 7 | **closer in 5** (2020, 2022–2025); 2019 and 2021 overshoot below 1 |
| S2 | ST_GAS starts (model / CEMS) | 709/73 · 301/80 · 764/150 · 156/38 · 440/52 · 284/66 · 149/20 | 793 · 386 · 647 · 228 · 577 · 416 · 223 | toward CEMS | **no: higher in 6 of 7**. ST_GAS clusters are still almost all continuous under ruling (a) |
| S2 | COAL_BIT starts (model / CEMS) | 76/85 · 24/36 · 120/16 · 43/16 · 28/6 · 27/9 · 17/10 | 88 · 25 · 124 · 37 · 27 · 32 · 17 | — | flat |
| S3 | online capacity vs a measured series | none on disk | skipped as declared | — | — |
| S4 | integer set | UC-0 M6: 37 clusters | 18 · 19 · 22 · 19 · 22 · 21 · 19 of 61–71 (§0.2) | reported | — |
| S5 | M2(a) CEMS-on / model-off | — | not re-measured in this lane (the uc-1.2 column came from a field this lane did not reproduce; omitted rather than mislabelled) | — | — |
| W2 | time-limit hits | — | 0 every year | ≤ 3 / year | met |
| W3 | uplift share | — | 0.92 · 0.90 · 0.82 · 0.95 · 1.08 · 0.97 · 0.74 % ($31.3 · 20.9 · 40.4 · 91.5 · 39.5 · 43.3 · 59.7 M) | ≤ 2 % | met |
| W4 | infeasible windows | — | 0 | 0 | met (no kill #1) |
| kill #2 | non-determinism | — | not exercised (no relaunched leg) | — | — |

**K-candidate structure bars.** S2 CC is met (5 of 7 years closer to CEMS). T2 is not (1 of 7). The R triggers decide the verdict regardless.

## 2. Why the price rises (zero LP, from the composed sidecars)

**The move is in every year and every load tercile.** Load-weighted price change, $/MWh:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| all hours | +0.87 | +0.31 | +1.04 | +2.88 | +0.99 | +1.31 | +2.44 |
| low-load tercile | +1.14 | +0.63 | +1.40 | +3.71 | +1.25 | +1.43 | +2.64 |
| mid | +1.22 | +0.59 | +1.10 | +2.92 | +1.22 | +1.56 | +2.78 |
| high | +0.43 | −0.09 | +0.77 | +2.32 | +0.64 | +1.01 | +2.05 |

The rise is largest in low and mid-load hours and in the high-gas years (2022, 2025). The scarcity tail is untouched (0 h > $300 in both arms).

**The mechanism is commitment, not a floor.** Per integer plant and hour, from `uc_schedule`, `unit_marginal` and the control's `unit_marginal`:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| control energy above the arm's P1 ceiling (u/n·cap) on integer plants, TWh | 6.83 | 6.89 | 6.62 | 6.73 | 8.77 | 8.48 | 9.01 |
| …of which in hours the plant is fully off in the arm, TWh | 4.71 | 5.10 | 4.45 | 4.29 | 7.14 | 7.18 | 7.16 |
| share of on-hours with partial commitment (0 < u < n) | 0.31 | 0.21 | 0.26 | 0.31 | 0.22 | 0.17 | 0.21 |
| integer-plant net output, control → arm TWh | 32.0 → 30.8 | 34.3 → 33.6 | 36.3 → 34.9 | 38.1 → 36.0 | 39.2 → 38.0 | 41.7 → 40.5 | 42.7 → 41.1 |
| replaced by: non-integer CC_REGULAR / CT_PEAKER / CC_CHP, TWh | +0.92 / +0.06 / +0.08 | +0.71 / −0.01 / +0.01 | +1.15 / +0.16 / +0.05 | +1.61 / +0.29 / +0.10 | +0.84 / +0.15 / +0.09 | +0.83 / +0.24 / +0.08 | +1.26 / +0.31 / +0.10 |
| hours an integer plant is marginal, control → arm | 2,733 → 1,747 | 2,845 → 2,039 | 2,940 → 2,159 | 3,372 → 2,423 | 3,459 → 2,226 | 3,625 → 1,978 | 3,112 → 1,845 |
| hours CT_PEAKER is marginal, control → arm | 208 → 320 | 198 → 209 | 272 → 408 | 325 → 445 | 226 → 293 | 336 → 583 | 354 → 484 |
| hours hydro is marginal, control → arm | 1,339 → 1,555 | 1,345 → 1,494 | 1,386 → 1,512 | 1,222 → 1,444 | 1,351 → 1,543 | 1,276 → 1,628 | 1,238 → 1,347 |

**Reading.**
- **The relaxation over-ran the efficient plants.** The control's continuous P1 dispatches the efficient multi-unit CC plants part-loaded across many hours, with fractional commitment and no start or no-load cost.
- **The UC commits whole units and keeps them on longer.** Measured on the control's part-load hours, 6.6–9.0 TWh/yr of that control output sits above what the arm's committed units can supply. The arm moves those plants' energy into the committed tranche at min-load, by +4.5–7.3 TWh.
- **Less-efficient units set price more often.** The integer plants set price in roughly 30–45 % fewer hours. Non-integer CC, CT_PEAKER, CC_CHP and hydro (opportunity-cost priced) set it more often.
- **Starts fall toward CEMS.** CC starts move toward CEMS in 5 of 7 years. This is the right direction, and it is what a UC is for.
- **Prices rise.** The price consequence is a body rise of $0.3–2.9/MWh.

**Why the control does not show this.** The keeper's authorized offer-band level was fixed ex ante on the relaxed posture. That level is the one scalar 0.9547 on the committed/econ bands, and it was not swept. Under rule 1 that scalar is legitimate, and it stays untouched here. Its consequence is that a structurally tighter commitment lands on a price surface fitted to the relaxation. The lane draws no tuning conclusion from this. Whether a UC keeper would re-declare its band level ex ante is an owner/desk question, not this lane's.

**Limits of this diagnosis.**
- It is a zero-LP decomposition of two solved bundles, not a counterfactual LP. The ceiling and off-hour energies are accounting identities on the control's dispatch, not causal shares of the price move.
- The `u/n·cap` ceiling uses `unit_marginal.cap_mw` (available capacity) as `p̄·a`.

## 3. Verdict, the D-6 card, the matrix

- **Verdict: `R`** (PRECOMMIT §7, fixed before any number).
  - C3a moves away from 0 by > 1 pp in five years.
  - C3b worsens by > 0.02 in 2022 and 2025.
  - Kill #3 fires on |ΔC3a 2023| = 2.60 pp.
  - No gated criterion flips.
  - Unlike the uc-1.2 R, this one is not confounded by an engine defect. Defect 6 is gone (peak tranches 74–1,010 h vs 8,758–8,760 h), and the price move is traced to the commitment decision (§2).
- **Matrix:** NEISO `unit_commitment_milp` stays **R**, with this RESULT as the citation, superseding the uc-1.2 citation.
- **D-6 card (copy-paste):**

  > "UC-3 NEISO A/B at uc-1.4 (580c4fbf) — R, clean engine. All seven years solve (2,555/2,555 windows Optimal, 0 TL hits, 0 infeasible, 0 MWh unserved); wall 9.6–31.6× P0+P1; make-whole 0.7–1.1 % of energy cost. Defect 6 is gone: CC peak tranches 74–1,010 h/yr (control 14–467; uc-1.2 8,760). No gated flip on the calibrated control, but the price body rises in every year and tercile (+$0.3–2.9/MWh): C3a moves away from 0 by 2.2–3.5 pp in 2019/2021/2022/2024/2025 (2019 reaches +9.5 %, 0.5 pp from FAIL), C3b worsens > 0.02 in 2022/2025, |ΔC3a 2023| = 2.6 pp (toward the actual). Cause, from the bundles: the UC commits whole units of multi-unit CC plants and keeps them on longer. CC starts move toward CEMS in 5/7 years. 6.6–9.0 TWh/yr of the relaxation's part-load output on those plants is above what the arm's committed units can supply; integer plants set price ~30–45 % fewer hours and non-integer CC/CT/hydro set it more. The keeper's band level (0.9547, ex ante on the relaxed posture) is untouched. Options: (1) record R, stage default-off for NEISO [recommended]; (2) if the owner wants a UC-native NEISO keeper, a separate PRECOMMIT would declare its band level ex ante under the UC posture (rule 1 channel), never swept against these gates; (3) promote on structure (not recommended: five wrong-way C3a moves, 2019 near the edge)."

- **Not a tuning invitation.** No `uc_*` value, floor, budget, limb or band was moved.

## 4. Bundles, cost, what survives (rule 31: nothing deleted)

| artefact | where | promotable? |
|---|---|---|
| seven leg bundles (full, incl. `dispatch/<y>_P1.parquet` and `unit_hourly_<y>`; 35–44 MB each, no file > 100 MB, nothing split) | shard branches, all parented on `b9eed86f`: `claude/ucmilp3-neiso-2019` `3731eb03` · `-2020` `de4c4cad` · `-2021` `213b91c3` · `-2022` `98572701` · `-2023` `3c3227e8` · `-2024` `25c12d94` · `-2025` `fcc8cf9b` | in form yes (rules 16, 34); **no promotion proposed** (verdict R) |
| composed span (full) | `results/calibration/ucmilp3_neiso_span` in this container only (excluded locally, never committed) | — |
| slim span | `docs/records/neiso/ucmilp/data/ucmilp3_neiso_span/` (27 MB, this PR). Carries every `hourly/` sidecar incl. `uc_schedule`, `uc_uplift` and `unit_marginal`, plus `uc_solve_log_<y>.json`, the regenerated `legitimacy_diagnostics.json`, `metrics.json` and configs. No dispatch, `unit_hourly`, `network` or `reserve_family` | the record |

- **Composition (§8 (a)/(b), as declared).** A scratch wrapper around `_ucmilp_compose_span.py` adds `gas_price_override` to the per-year set and applies `_hydro5_compose_span._respan_shared_inputs`. The respanned frame hashes equal the keeper's (`eia930-37748ca9a57e`, `eia923-0edb30122b08`, `campd-8b9518ebc11b`, …). `legitimacy_diagnostics.json` was regenerated over all seven years.
- **Cost.** Seven shard containers at 40–91 min each, about 1.5 h elapsed in parallel. Zero LP in the parent.
- **Shard branches.** These are transport (rule 33). The owner may cut the seven `claude/ucmilp3-neiso-*` branches once this PR merges; a session cannot (403).
- **Promotion question: none proposed; the lane records R.** The leg bundles will not survive this container; they survive on the shard branches.

## 5. Process record

| year | session | outcome | wall |
|---|---|---|---|
| 2019 | `session_019PMrU4BS5aVaiuTEZMCL2r` | solved, 365/365 Optimal, pushed, verified, archived | 45 min |
| 2020 | `session_011KDtpofX9JheMpTLrdDy4b` | same | 40 min |
| 2021 | `session_017cxYx2SvUp4s4HkW4oQZJx` | same; P1 dump 3,334 MWh | 65 min |
| 2022 | `session_01LxXLHJG2vLJjbLtDjtGzXm` | same | 91 min |
| 2023 | `session_01Sh64ipWvSYAdMopdGVHw3u` | same | 74 min |
| 2024 | `session_01M47YkJcbfsnYbYWQAhhcaJ` | same | 65 min |
| 2025 | `session_01Qun8kvF1KYzLkWQYLYBSqT` | same | 62 min |

- **Verification and archiving.** Every leg was fetched and checked before its shard was archived (rule 33): parented on `b9eed86f`, 21 files, the five required files present, and `.gitignore` the only change outside the bundle. All seven are archived.
- **Shard conduct.** Every shard ran `uv sync` once (no `.venv`). Each prepared 23.4 GiB of ceiling plus swap, against a 24 GiB target; this was a warning only, and the peak was 5.2 GiB. Shards for 2020 and 2022 logged the absent `NEISO_load_hourly_<y>.csv` zonal file (reported, not investigated). None edited `src/`, `scripts/` or `frontend/data/`, and none opened a PR.
- **No engine defect was found.** Nothing was routed to UC-DESK as a defect.

## Log entry

- 2026-10-14 · UC-3-NEISO `session_01XS3YxX7AQRJFBAQoGi6TRF` · `claude/ucmilp-3-neiso-ab` · zero LP in the parent.
  - **Setup:** Addendum F at `580c4fbf` (uc-1.4). G-DRIFT: UC-path LIVE, gate-off INERT, no registry value moved. L1 gate carried (window MILP byte-identical).
  - **Solve:** seven shards at `b9eed86f`, 2,555/2,555 windows Optimal, wall 9.6–31.6× P0+P1.
  - **Defect 6:** gone. Peak tranches 74–1,010 h/yr (uc-1.2: 8,760).
  - **Gates:** no gated flip. C3a 2019 +6.8→+9.5, 2020 −1.2→+0.0, 2021 +2.8→+5.0, 2022 +2.5→+5.6, 2023 −3.0→−0.4, 2024 +0.5→+3.6, 2025 +3.8→+7.3 %. C3b 2022 +0.022, 2025 +0.033.
  - **Verdict R:** C3a wrong-way > 1 pp ×5; C3b ×2; kill #3 2.60 pp.
  - **Cause:** whole-unit commitment on multi-unit CC plants (6.6–9.0 TWh/yr of relaxed part-load output above the arm's ceiling); CC starts closer to CEMS in 5/7 years.
  - **Housekeeping:** cell stays R with the new citation. Nothing registered, promoted or deleted; 7 shards archived.
