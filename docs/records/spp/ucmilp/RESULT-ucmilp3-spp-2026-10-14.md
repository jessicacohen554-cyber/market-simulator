# RESULT — UC-3-SPP: both SPP UC arms re-solved on the clean engine (uc-1.5) — arm A **R**, arm B **R**; arm A's uc-1.1 price gain was a defect artefact

**Lane:** UC-3-SPP · **Session:** `session_01CjZHqjM9ardXPg9RSYzrzt` (Opus) · **Date:** 2026-10-14 · **Branch:** `claude/ucmilp-3-spp-ab`.
**PRECOMMIT:** `PRECOMMIT-ucmilp3-spp-2026-10-14.md`. It was pushed before any shard (`2bfaefdf`, then `f4709734`). Addendum A covers the uc-1.5 pin and G-DRIFT; Addendum B is the launch record.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), on the owner's ruling of 2026-10-14, *"Go with your recommendations"*, decision 7 (plan §11 r09).
**Pin solved:** `2dd69d5aa936547b402a1ba54d2eba57e759b7e7` (`main`, engine `uc-1.5`, defect 7 fixed). Shards pinned the branch head `ca0acb249fc61485982c1a0264fe52e9344254a1`, whose `src/` and `scripts/` equal the pin's.
**LP in this session:** zero. There were 14 year-isolated shards (rule 36).
**Control:** keeper `2026-10-03-closeout-spp-nuc-keeper` (rule 29(b)).
**Rubric:** 3.20.
**Not registered** (E13). The slim spans are in `data/ucmilp3_spp_a_span/` and `data/ucmilp3_spp_b_span/`.

## 0. Headline

**On the clean engine, the UC stage moves SPP prices only where it changes commitment, and neither arm moves them toward actual.**

- **Arm A (UC on, both conduct floors kept)** lands on the control's price level:
  - 2020 C3a: +27.7 → **+27.7 %** (at uc-1.1 it read +19.0 %).
  - 2019 C3a: +12.3 → **+13.6 %**, the wrong way past the control.
  - 2020 C3b: 0.345 → **0.342**.
  - So the uc-1.1 price "gain" (RESULT-ucmilp-spp-ab §0) was the defect-6 artefact: forced peak-tranche energy depressing the LMP. It is not a UC effect.
- **Arm B (UC on, both floors off)** reproduces its uc-1.1 failure mode. The UC alone commits less slow capacity in high-price hours (600–1,400 MW less), CTs set the price about twice as often, and the body rises in every year:
  - 2020 C3a: **+36.7 %**.
  - 2019 C3a: **+18.8 %**.
  - 2020 C3b: **0.421**.
  - All three targets move the wrong way past the control.
- **Engine checks are clean:**
  - forced peak-tranche energy ≤ 0.004 TWh/yr;
  - 5,110 of 5,110 windows Optimal;
  - 0 time-limit hits;
  - 0 unserved MWh;
  - uplift 0.5–1.6 % (A) and 0.06–0.22 % (B), against a 2 % bar.
- **The stacking hypotheses now have a clean answer (arm B vs arm A).** H1, H2, H3 and H4 are all **met**:
  - CC returns to the control's level;
  - coal is lower than arm A in 7 of 7 years;
  - C8 ST_GAS falls to 1–5 %;
  - PRB starts reach 0.36–1.24× CEMS.

  Removing the floors fixes the stacking, but the UC then under-commits steam gas and prices rise.
- **Verdicts:**
  - **Arm A: R.** T2 moves the wrong way past the control. Kill #3 fires: 4 real gate flips and 6 new D-4 FAIL rows.
  - **Arm B: R.** T1, T2 and T3 all move the wrong way past the control. Kill #3 fires: 8 real flips.
  - Rule-1 reading: the remaining SPP price gap is **not engine**. On the clean engine the UC structure itself does not close it, under either commitment posture. The open question is calibration and structure: steam-gas self-commitment and the peak offer stack.

## 1. Gate table — control · arm A · arm B, every registered year (`calibration_verdict.py`, rubric 3.20)

C1 rows show the model-minus-actual deviation in TWh; F means FAIL, and everything else PASSes. C8 is the ST_GAS forced share, shown as scored / with MECH 28 removed (R4).

| year | C1 CC_REGULAR | C1 COAL_PRB | C1 ST_GAS | C1 CT_PEAKER | C3a | C3b | C3c (model h vs actual, >$200) | C4 gas / coal | C8 ST_GAS (scored / R4) |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | +2.25 · −0.08 · +1.42 | +0.24 · +2.18 · +0.38 | −4.96 · −6.11 · **−8.36 F** | +1.49 · +2.64 · +4.86 | +12.3 F · **+13.6 F** · **+18.8 F** | 0.160 · 0.170 · **0.213 F** | 0 · 0 · 0 / 47 | PASS ×3 | 18.1 · 19.9/19.1 · 1.3/0.0 % |
| 2020 | +1.60 · +0.14 · +2.13 | −3.03 · −1.36 · −4.20 | −3.42 · −4.80 · −7.40 | +6.15 · +7.06 · **+9.84 F** | +27.7 F · +27.7 F · **+36.7 F** | 0.345 F · 0.342 F · **0.421 F** | 0 · 0 · 0 / 23 | PASS ×3 | 15.7 · 18.0/17.3 · 2.0/0.0 % |
| 2021 | −8.92 F · −10.17 F · −8.75 F | +10.98 F · +10.99 F · +10.23 F | −2.83 · −3.11 · −5.48 | +1.31 · +2.68 · +3.67 | +7.1 · +8.6 · **+14.7 F** | 0.176 · **0.134** · 0.153 | 372 · 383 · 395 / 140 | PASS ×3 | 28.8 · **30.1 F**/29.2 · 2.4/0.0 % |
| 2022 | −9.16 F · −10.33 F · −8.84 F | +10.75 F · +10.43 F · +9.55 F | −5.18 · −5.20 · **−8.71 F** | −1.39 · +0.36 · +1.69 | −4.8 · −4.7 · +3.8 | 0.175 · 0.167 · 0.149 | 0 · 0 · 2 / 99 | gas FAIL ×3 | 33.8 grounded · **33.3 F**/32.3 · 5.2/0.0 % |
| 2023 | −4.49 · −6.20 · −4.23 | +0.57 · +2.37 · +0.23 | −5.55 · −6.93 · **−10.81 F** | +2.83 · +4.29 · +7.06 | −6.4 · −7.2 · +3.3 | 0.176 · 0.176 · 0.162 | 0 · 0 · 0 / 42 | PASS ×3 | 23.1 · 25.7/24.4 · 4.5/0.0 % |
| 2024 | −5.80 · −7.83 · −5.65 | +0.82 · +2.68 · −0.09 | −6.31 · −7.07 · **−10.51 F** | +2.36 · +3.50 · +6.52 | −11.2 F · −12.0 F · **−1.7** | 0.216 F · 0.219 F · **0.174** | 0 · 1 · 1 / 59 | PASS ×3 | 18.3 · 20.2/19.2 · 3.1/0.0 % |
| 2025 | −7.86 · **−9.77 F** · −7.74 | +7.39 · **+8.13 F** · +7.37 | −6.91 · −6.53 · **−10.50 F** | −0.05 · +0.93 · +2.78 | −4.3 · −4.3 · +3.5 | 0.153 · 0.153 · 0.160 | 0 · 1 · 1 / 68 | PASS ×3 | 17.7 · 21.3/15.2 · 3.6/0.0 % |

**C2:** PASS in all 21 cells. **C6:** UNATTESTED on both arms; a probe carries no attestation.

**C3c:** the CAVEAT → FAIL change in 2019–2022 on both arms is the known attestation artefact, not a scored flip. The keeper's rule-22 ledger route needs the attestation, so magnitudes are compared instead. They barely move: 2021 is 372 / 383 / 395 h, and 2022 is 0 / 0 / 2 h.

**Flips vs the keeper, real ones only:**
- **Arm A: 4 downgrades, 0 upgrades.** C8 ST_GAS 2021 and 2022, C1 CC_REGULAR 2025, C1 COAL_PRB 2025.
  - It also has **6 new D-4 FAIL rows**: `coal_mustrun` on plant 2079 in 2019–21 and 2023–25. The meter reads zero output in 65–100 % of those floored hours, against an off-window share ≤ 0.2 %.
- **Arm B: 8 downgrades, 2 upgrades.**
  - Downgrades: C1 ST_GAS in 2019 and 2022–25, C1 CT_PEAKER 2020, C3a 2021, C3b 2019.
  - Upgrades: 2024 C3a and C3b.
  - The control's seven `st_gas_mustrun_per_plant` D-4 FAIL rows are gone, as expected. No D-4 FAIL row is new.

**Determination:** NOT-YET for all three. The control grades 3 of 8, arm A 1 of 7 and arm B 2 of 7. Both arms have 0 unserved MWh in every year and P1 Optimal in every leg.

## 2. The pre-registered readings (PRECOMMIT §2), answered

### 2.1 Targets T1–T5

| # | bar | control | arm A uc-1.1 | **arm A uc-1.5** | arm B uc-1.1 | **arm B uc-1.5** |
|---|---|---|---|---|---|---|
| T1: 2020 C3a | ≤ +18.85 % | +27.7 % | +19.0 % | **+27.7 %**: no move, not met | +32.4 % | **+36.7 %**: wrong way |
| T2: 2019 C3a | ≤ +11.15 % | +12.3 % | +10.3 % | **+13.6 %**: wrong way, past the control | +17.2 % | **+18.8 %**: wrong way |
| T3: 2020 C3b | ≤ 0.2725 | 0.345 | 0.273 | **0.342**: right sign, about 1 % of the bar | 0.380 | **0.421**: wrong way |
| T4: M3 ratios ≤ $15 / < $0 (2019; 2020) | rise | 0.025 / 0.040; 0.150 / 0.111 | — | **0.044 / 0.069; 0.191 / 0.183**: rise (sign met) | — | **0.028 / 0.020; 0.129 / 0.056**: fall (sign not met, except 2019 ≤ $15) |
| T5: M4 reserve dormancy | falls | 1.00 (MCP $0) | 1.00 | **1.00**: no move | 1.00 | **1.00**: no move |

For 2021–25, arm A's T4 ratios also rise (≤ $15: 0.29–0.52; < $0: 0.53–0.86), while arm B's fall below the control (0.20–0.38 and 0.29–0.50).

### 2.2 Stacking hypotheses H1–H4 (arm B vs arm A, both on the clean engine; P1 TWh from `class_hourly`)

| # | reading | bar | result |
|---|---|---|---|
| H1 | CC_REGULAR TWh | B − A ≥ ½·(control − A) in ≥ 4 of 7 years, and B > A in every year | **MET.** Arm A sits 1.2–2.4 TWh below the control. Arm B gains 1.4–2.2 TWh on arm A, which puts it within −0.9 / +0.5 TWh of the control in every year. |
| H2 | COAL_PRB + COAL_LIGNITE TWh | A − B ≥ ½·(A − control) in ≥ 4 of 7, and B < A in every year | **MET.** B < A in 7 of 7 years (by 0.7–3.0 TWh). Arm A sat −0.2 to +2.4 TWh off the control, and arm B returns to within ±1.0 TWh of it. |
| H3 | C8 ST_GAS forced share | B < A in every year, and B ≤ 30 % | **MET.** B is 1.3–5.2 % (0.0 % under R4); A is 18.0–33.3 %. |
| H4 | PRB starts, model ÷ CEMS (M1) | B > A in ≥ 5 of 7 | **MET, 7 of 7.** A is 0.23–0.43×, B is 0.36–1.24×, and the control 0.30–0.95×. Lignite starts under B reach 0.37–1.42× CEMS, against 0.05–0.53× under A and the control. |

### 2.3 Structure, cost and engine

| reading | arm A | arm B |
|---|---|---|
| Forced peak-tranche energy (P1 MWh on `_peak*` tranches at a MECH 28 floor) | 0.000–0.004 TWh/yr (≈ 0; defect 6 gone) | 0.000–0.0001 TWh/yr |
| MECH 28 (D-2) share of class energy | CC 1.5–5.4 %, PRB 1.9–4.4 %, ST_GAS 0.9–6.2 % (0.07–1.00 TWh) | CC 1.1–5.0 %, PRB 2.2–4.9 %, LIG 5–20 %, ST_GAS 1.3–5.2 % (all of the class's forcing) |
| Uplift = Σ make-whole ÷ Σ λ_P1·load (bar 2 %) | 0.54 / 0.78 / 1.62 / 1.55 / 1.31 / 1.61 / 1.36 % ($35–187 M) | 0.06 / 0.08 / 0.14 / 0.16 / 0.18 / 0.19 / 0.22 % ($4–21 M) |
| CC_REGULAR starts ÷ CEMS (M1) | 0.48–0.87× (control 1.68–2.27×) | 0.46–0.89× |
| ST_GAS starts ÷ CEMS (M1) | 0.14–0.31× (control 0.45–0.95×) | 0.09–0.36× |
| Integer clusters / gate set, of all clusters | 94 / 92 / 88 / 86 / 86 / 83 / 82, each equal to its gate (226 / 219 / 208 / 219 / 218 / 221 / 217 clusters); by class: coal 29–35, ST_GAS 31–36, CC 22–23 | identical |
| Clusters with no integer under ruling (a) | 0: integer set equals gate set in every year (SPP has no all-budget-pinned cluster) | 0 |
| No-load source | `uc-params` 125–126 clusters, class fallback 83–100 | identical |
| Windows Optimal / time-limit hits / infeasible | 2,555 / 0 / 0 | 2,555 / 0 / 0 |
| MILP s per window, mean (p95); B&B nodes p50 / p95; relative gap p95 | 1.59–2.57 (2.48–4.02); 1 / 1; ≤ 8.1e-4 | 2.63–4.06 (4.80–6.81); 1 / 7–13; ≤ 9.1e-4 |
| S3: online capacity vs the SPP portal series | skipped: the comparator is still not on disk | skipped |

### 2.4 Wall clock (GATESPEC §6.1; baseline = the shard's own `solve_p0 + solve_p1`, the declared proxy)

| leg | P0 s | P1 s | markup (UC seam) s | total s | ratio ÷ (P0+P1) | peak RSS GiB (cgroup / process) |
|---|---|---|---|---|---|---|
| A 2019 | 106.6 | 116.1 | 1,073.1 | 1,363.8 | 6.1× | 8.47 / 4.75 |
| A 2020 | 106.5 | 95.6 | 966.5 | 1,234.3 | 6.1× | 8.46 / 5.35 |
| A 2021 | 101.2 | 105.7 | 736.7 | 989.7 | 4.8× | 8.39 / 5.61 |
| A 2022 | 82.6 | 101.2 | 690.9 | 923.2 | 5.0× | 8.36 / 4.73 |
| A 2023 | 95.6 | 102.3 | 740.4 | 990.9 | 5.0× | 8.45 / 4.67 |
| A 2024 | 93.9 | 102.4 | 758.8 | 1,010.5 | 5.1× | 7.88 / 5.63 |
| A 2025 | 90.1 | 94.3 | 666.4 | 892.8 | 4.8× | 8.47 / 4.72 |
| B 2019 | 87.1 | 99.3 | 1,482.9 | 1,715.8 | 9.2× | 8.32 / 4.79 |
| B 2020 | 109.1 | 117.1 | 1,613.0 | 1,895.0 | 8.4× | 7.82 / 5.67 |
| B 2021 | 93.0 | 98.5 | 1,060.5 | 1,303.0 | 6.8× | 8.48 / 5.67 |
| B 2022 | 100.3 | 105.6 | 1,177.0 | 1,451.1 | 7.0× | 8.48 / 5.63 |
| B 2023 | 94.2 | 103.1 | 1,376.9 | 1,625.9 | 8.2× | 7.99 / 5.59 |
| B 2024 | 104.1 | 108.0 | 1,327.1 | 1,595.4 | 7.5× | 7.99 / 4.74 |
| B 2025 | 96.6 | 89.9 | 1,057.9 | 1,284.6 | 6.9× | not in transcript |

- Solver settings: `lean` preset and slim window, the declared defaults.
- Every leg is above the ruled 3× ceiling. That is a cost finding (GATESPEC §7.3), not a defeat.
- Both arms beat uc-1.1, which ran 5.1–10.2× (A) and 10.1–17.5× (B).
- Year-solve totals were 893–1,895 s, far inside the 720-min budget.
- Timing lines come from each shard's `INFO: year <y> phase timing` log line, read from the archived transcripts.

## 3. Price-move diagnosis (zero LP, descriptive; PRECOMMIT §2)

It was triggered for arm B in every year and for arm A in 2021 (C3b moved −0.042). The rows below are means over hours in each hour class:
- ΔP is arm minus control, $/MWh.
- Δonline is the change in slow-class (CC, coal, ST_GAS) online capacity, on the 1 %-of-cap convention.

| arm-year | trough (actual ≤ $15): ΔP / Δonline | top tercile: ΔP / Δonline | top-100 actual h: ΔP / Δonline | marginal mix shift in the top tercile |
|---|---|---|---|---|
| B 2019 | +0.59 / +126 MW | +2.29 / −620 MW | +5.39 / −967 MW | CT_PEAKER econ tranches set the price 0.24 → 0.42 per hour |
| B 2020 | +0.96 / +45 | +2.30 / −790 | +4.01 / −991 | CT 0.21 → 0.41 |
| B 2021 | +2.28 / +50 | +4.63 / −646 | +18.71 / −659 | CT 0.27 → 0.51; CC committed falls 0.12 → 0.04 |
| B 2022 | +3.46 / −69 | +5.89 / −810 | +10.43 / −1,437 | CT 0.23 → 0.47; CC 0.38 → 0.21 |
| B 2023 | +2.90 / −88 | +3.18 / −1,061 | +5.78 / −1,337 | CT 0.26 → 0.44; ST_GAS leaves the margin |
| B 2024 | +2.21 / −149 | +3.27 / −869 | +12.62 / −1,109 | CT 0.28 → 0.48 |
| B 2025 | +2.13 / −10 | +3.25 / −724 | +4.55 / −1,151 | CT 0.25 → 0.45 |
| A 2021 | −1.88 / +449 | +2.83 / −357 | +12.92 / −296 | CT 0.27 → 0.44; COAL_PRB committed sets the trough 0.23 → 0.37 |

**Attribution, by sign:**
- **Arm B:** cause (i). The UC decommits steam gas and CC in the high-price hours, and CT econ tranches take the margin.
  - The trough also rises (+$0.6 to +$3.5) with almost no change in online capacity. There, the marginal unit shifts from CC tranches to PRB `_committed` / `_mustrun` tranches. The offer levels behind that shift were not decomposed here.
  - Cause (iii) is excluded: the reserve MCP stays $0 in every hour of every bundle (T5).
- **Arm A 2021:** cause (ii) runs in reverse. About 450 MW more slow capacity sits online in the trough, which lowers it by $1.9. Cause (i) is present at the top (−300 MW, +$2.8 to +$12.9). The net is a flatter shape error (C3b 0.176 → 0.134) at an unchanged mean.

Nothing here creates a parameter (rule 21), and nothing was tuned (rule 1).

## 4. Kills and engine

- **Kill #1 (infeasible window): not fired.** 0 of 5,110 windows were infeasible.
- **Kill #2 (non-deterministic schedule): not exercised.** No arm-year ran twice to completion. The five arm-B shards relaunched at 13:45Z never started, so the first launches produced no schedule.
- **Kill #3 (control flip): fired on both arms** (§1).
- **No engine defect was found at uc-1.5.** Defect-6 energy is about 0. Uplift is inside the 2 % sanity bar (arm A 0.5–1.6 %, against 1.0–4.4 % at uc-1.1; that change is not attributed to a single fix).

## 5. Deviations and disclosures (as in the prior arms; no reading, bar or kill changed)

1. **Composition:**
   - a scratch copy of `_ucmilp_compose_span.py`, with `gas_price_override` added to `PER_YEAR_FIELDS`;
   - the keeper composer's `_respan_shared_inputs` applied to the span's `meta.json`. The re-spanned frames are the keeper's own: `campd-8b15fb193a60`, `eia923-ada99c7451fd`, `eia930-c3bec7e7b952`.

   No repo script was edited.
2. **Scoring:** `calibration_verdict.py` refuses an unregistered bundle. The lane therefore ran `dashboard_add_run.py --no-prune` locally, to write the registry sidecar and run file for `2026-10-14-ucmilp3-spp-arm-b` and `…-arm-local` (arm A; the label parser trimmed the id). They are excluded via `.git/info/exclude` and **none is committed**.
3. **Relaunch:** five arm-B shards (2021–25) stayed PENDING for 51 min. They were archived with nothing started and relaunched at 13:45Z with identical prompts.
4. **Extra commits on some shard branches:**
   - Shards a-2021 and b-2020 pushed a second commit with the one-year `_shared/SPP` benchmark frames. These were not used: the span was re-spanned to the keeper's frames.
   - Every shard pushed `hourly/unit_hourly_<y>.parquet` inside the bundle. It is excluded from the slim spans (rule 15).

## 6. Where everything is; promotion

| artefact | where | promotable? |
|---|---|---|
| 14 leg bundles (full: `dispatch/`, `floors/`, `unit_hourly`, 20 files each), all parented on `ca0acb24` | arm A: `claude/ucmilp3-spp-a-2019` `4e613ad1` · `-2020` `38d7de04` · `-2021` `89dadd98` (head `86bdc2cf` adds frames) · `-2022` `99dd1dae` · `-2023` `c1dc8dba` · `-2024` `c33401a6` · `-2025` `9a08a26e`<br>arm B: `claude/ucmilp3-spp-b-2019` `1db5fa5a` · `-2020` `9b72d4df` (head `7aacd796`) · `-2021` `a679930d` · `-2022` `4edb2fe8` · `-2023` `d86ad5fa` · `-2024` `f5f4533f` · `-2025` `7db92857` | yes in form (rule 34). **No promotion proposed:** both arms read R. A promotion would need these bundles on `main` (about 1 GB per arm) and an attestation. |
| composed spans | local only (`results/calibration/ucmilp3_spp_{a,b}_span`, gitignored); slim copies in this PR under `data/ucmilp3_spp_{a,b}_span/` (28–29 MB each) | not registered (E13) |
| 14 shard sessions | all verified, then archived (rule 33) | — |

**Branches for the owner to cut once this PR merges:** `claude/ucmilp3-spp-{a,b}-{2019..2025}` (14 branches). A session cannot delete a remote branch.

## 7. D-6 card (verbatim-ready)

> **SPP UC (clean engine, uc-1.5): both arms R.**
>
> **Floors kept:** prices unchanged from the keeper, coal over-held, 4 flips and 6 new D-4 rows.
>
> **Floors off:** stacking fixed (H1–H4 met), but the UC under-commits steam gas, so CTs set the peak price and the body rises in every year: 2020 C3a +36.7 %, 8 flips.
>
> The uc-1.1 price gain was defect 6.
>
> **Options:**
> - record R on clean evidence and close the SPP UC cell (recommended);
> - hold for a steam-gas commitment-physics lane (ST_GAS min-up/down and no-load provenance, no tuning) before any third arm.

## Log entry

- 2026-10-14 · UC-3-SPP · pin `2dd69d5a` (uc-1.5) · 14 shards · arm A (floors kept) **R**: T2 wrong way, 4 flips, 6 new D-4 rows, prices at the control.
- Arm B (floors off) **R**: T1–T3 wrong way, 8 flips; H1–H4 met.
- Engine clean: defect-6 energy about 0, uplift ≤ 1.6 %, 0 infeasible windows, wall 4.8–9.2×.
- Not registered. Matrix cell `unit_commitment_milp` × SPP stays **R**, on clean evidence.
