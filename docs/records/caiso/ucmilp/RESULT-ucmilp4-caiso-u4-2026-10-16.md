# RESULT — UC-4-CAISO, arm U4 (UC on uc-1.7/1.8 + DA-forecast commitment + reserve co-opt with the u-gate): **R**

**Lane:** UC-4-CAISO (Opus, `session_01V1SFj7XgW15F44YogU5EKJ`) · **Date:** 2026-10-16 · **Branch:** `claude/ucmilp-4-caiso`.
**Charter:** UC-DESK r14 (`session_01WX9W5tgYMre3Z134LZoGF6`; plan §11 r14, §12).
**PRECOMMIT:** `PRECOMMIT-ucmilp4-caiso-u4-2026-10-15.md`, pushed `23aefcae` before any shard. Its addenda were each pushed before any number they govern:
- A: FIX-8 defect stop.
- B: re-pin `7c93273e`.
- C: owner gate ruling + re-pin `41cd55dc`.

**LP in this session:** zero.
**Registered:** nothing. The scorer needs a sidecar and payload, so the span was registered locally, scored, and both were removed. The regenerated bench parts were restored with `git checkout`.

## 0. Headline

**Verdict R by kill #3:** five PASS → FAIL flips against the keeper.
- C3a 2022 / 2023 / 2024 / 2025: +13.4 / +11.6 / +11.0 / +13.5 % against the ±10 % band.
- C1 CC_REGULAR 2025: −5.66 TWh against a ±5.08 band.

T2 also moved the wrong way: C3a 2021 went from +12.7 to +14.9 %. Every leg solved, with 0 infeasible windows and 0 MWh unserved in every year. All 7 years are covered; no year is held or a coverage gap.

**What U4 changed against UC-3 (uc-1.5):**
- **Commitment counts.** CC_REGULAR starts reach **0.92–0.97× CEMS in 2022–25** (keeper 2.9–3.3×; UC-3 0.64–0.82×). That is the closest any arm has come to the measured start count.
- **Price.** The price result did not improve. C3a 2022–25 is 0.2–2.0 pts worse than UC-3, and one more C1 row flips (2025).
- **Mechanism.** The arm still holds 2.7–5.3 TWh/yr less CC_REGULAR than the keeper in 2021–25. Imports (+1.5–3.9 TWh) and CTs (+0.8–1.2 TWh) replace it. The price lift (+$1.6–4.2/MWh) sits mostly in the low tercile in 2024–25 and in the high tercile in 2021–22.

**Two of the four added mechanisms are inert in CAISO.** The reserve co-opt's spin and non-spin duals are $0 in every hour of every year: the 1,120 MW requirement is fully held against an 18.7–19.1 GW deliverable ramp. The scarcity overlay that the validator forced off was already a stored no-op: caiso-137b shows a $0.00 adder in every hour. The movers are therefore the DA-forecast commitment demand and the per-unit `mlf`/`ut_h` uc-params.

## 1. Gate table: control → UC-3 (uc-1.5) → **U4**

Engine per year (desk condition 1): 2019–20 **uc-1.7**, 2021–25 **uc-1.8**. FIX-9 changes the solver path only; the model and gap are identical (Addendum C). The DF bias is the EIA-930 CISO DF − actual mean (desk request), as applied in each leg log.

| year | engine | DF bias MW | C1 CC_REGULAR TWh | C1 CT_PEAKER | C3a | C3b NRMSE | C3c h (actual) | C4 gas NRMSE | C8 CC (MECH 28) | CC starts ÷ CEMS | ST_GAS starts ÷ CEMS | unserved | uplift |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | uc-1.7 | +586 | +5.63 F → +2.11 P → **+4.87 F** | +0.38 → +1.64 → +1.24 P | no ref | no ref | — | .385 → .373 → .373 F | 8.6 → 3.7 → **18.4 %** P | 2.79 → 0.45 → **0.45** | 0.52 → 0.01 → 0.01 | 0 | 0.62 % |
| 2020 | uc-1.7 | +124 | +13.46 F → +10.33 F → **+11.70 F** | −0.04 → +1.33 → +1.29 P | no ref | no ref | — | .399 → .386 → .393 F | 6.2 → 3.0 → **13.3 %** P | 2.56 → 0.34 → **0.36** | 1.79 → 0.11 → 0.14 | 0 | 0.19 % |
| 2021 | uc-1.8 | −179 | +6.59 F → +3.10 P → **+4.02 P** | +2.52 → +3.44 → +3.43 P | +12.7 % C → +15.7 % → **+14.9 %** (F\*) | .148 → .178 → **.169** P | 0 vs 27 (artefact\*) | .348 → .335 → .333 F | 6.8 → 3.3 → 10.3 % P | 2.65 → 0.54 → **0.64** | 1.12 → 0.33 → 0.21 | 0 | 0.11 % |
| 2022 | uc-1.8 | −416 | +0.95 P → −3.38 P → **−3.66 P** | −0.63 → +0.15 → +0.41 P | +8.6 % P → +12.5 % F → **+13.4 % F** | .121 → .162 → .175 P | 515 → 521 → **527** (510) P | .249 → .249 → .247 P | 7.1 → 2.5 → 8.0 % P | 2.89 → 0.82 → **0.97** | 0.43 → 0.23 → 0.13 | 0 | 0.08 % |
| 2023 | uc-1.8 | −525 | −1.07 P → −3.96 P → **−3.74 P** | −1.14 → −0.43 → −0.32 P | +7.6 % P → +11.4 % F → **+11.6 % F** | .117 → .158 → .174 P | 51 → 73 → **80** (47) P | .235 → .248 → .238 P | 7.6 → 3.3 → 10.5 % P | 2.96 → 0.78 → **0.96** | 0.19 → 0.07 → 0.09 | 0 | 0.17 % |
| 2024 | uc-1.8 | −1,089 | −1.67 P → −4.76 P → **−5.08 P** | −1.04 → −0.07 → +0.19 P | +6.6 % P → +10.5 % F → **+11.0 % F** | .122 → .152 → .160 P | 0 vs 35 (artefact\*) | .240 → .240 → .237 P | 10.8 → 4.9 → 10.3 % P | 3.34 → 0.64 → **0.92** | 9.05 → 0.38 → 0.43 | 0 | 0.22 % |
| 2025 | uc-1.8 | −1,555 | −0.36 P → −4.43 P → **−5.66 F** | −1.74 → −1.20 → −0.86 P | +6.0 % P → +11.5 % F → **+13.5 % F** | .089 → .136 → .157 P | 0 vs 8 P | .283 → .278 → .287 P | 12.3 → 6.0 → 9.7 % P | 3.31 → 0.65 → **0.97** | 0.27 → 0 → 0 | 0 | 0.17 % |

\* These are artefacts of the missing attestation. The probe carries no `calibration_attestation.json`, so C6 reads UNATTESTED and the keeper's ledgered caveats are unavailable. They are compared by magnitude, not counted as flips (PRECOMMIT §3).
- C3c 2021/2024 and C3b 2021 hold the keeper's magnitudes.
- C3a 2021 moved by itself past its band (+12.7 → +14.9 %); that move is T2.

Other notes:
- CO2: 2022 −8.6 % CAVEAT → −12.4 % FAIL. CO2 is reported-only (C5a), not a gated criterion.
- **Sensitivity:** on the bench parts the local registration regenerated, the flip set is the 4 C3a rows. C1 CC_REGULAR 2025 sits on the band edge and does not flip there.
- Determination: NOT-YET → NOT-YET.
- C3c is scored on the energy-only LMP in both bundles (no overlay series is derived for CAISO), so overlay-off cannot move it. The 2023 rise from 51 to 80 hours (actual 47) is the UC energy dual.

## 2. Readings and verdict (PRECOMMIT §3, fixed ex ante)

| # | reading | bar | U4 | met? |
|---|---|---|---|---|
| T1a | C1 CC_REGULAR 2019 | ≤ +5.24 | +4.87 | yes |
| T1b | C1 CC_REGULAR 2020 | ≤ +9.03 | +11.70 | no (right sign) |
| T1c | C1 CC_REGULAR 2021 | ≤ +5.71 | +4.02 | yes |
| T2 | C3a 2021 | ≤ +11.35 % | +14.9 % | **no: wrong way** |
| T3 | CC_REGULAR starts ≤ (control + CEMS)/2 | 5,075 / 5,619 / 5,995 / 6,748 / 6,375 / 6,295 / 6,071 | 1,214 / 1,147 / 2,098 / 3,356 / 3,083 / 2,678 / 2,745 | yes, every year |
| T4 | sub-min-up CC energy share | falls | 12.8–19.4 % → 1.1–3.6 % | yes |
| T5 | reserve dormancy / MCP | falls / rises | MCP $0 every hour (co-opt inert) | no move |
| kill #1 | infeasible window / no incumbent | — | 0 / 2,555 windows (7 time-limit hits, 2019, incumbents kept) | not fired |
| kill #2 | non-determinism | — | not exercised (no year solved twice to completion) | — |
| kill #3 | control flip incl. unserved > keeper + 500 MWh | none | **5 flips**; unserved 0 | **fired** |

**Verdict: R** (kill #3; T2 wrong way). Met: T1a, T1c, T3, T4. Not met: T1b (sub-bar), T5 (no move).
The CAISO `unit_commitment_milp` cell stays R, with evidence re-pointed here. The CAISO `uc_commitment_demand_source` cell U → **R**, adjudicated jointly as part of this arm, as are the other three mechanisms. This lane does not isolate any single mechanism.

## 3. Mechanism diagnosis (zero LP; `data/ucmilp4_readings/price_class_diag.py`)

**Price,** CAISO load-weighted over the five load zones, $/MWh, control → UC-3 → U4:

| year | control | UC-3 | U4 | U4 − control |
|---|---|---|---|---|
| 2019 | 38.06 | 40.79 | 38.33 | +0.27 |
| 2020 | 34.30 | 35.46 | 34.64 | +0.34 |
| 2021 | 54.60 | 56.74 | 56.21 | +1.61 |
| 2022 | 88.02 | 91.42 | 92.22 | +4.20 |
| 2023 | 56.48 | 58.68 | 58.76 | +2.28 |
| 2024 | 35.31 | 36.71 | 36.91 | +1.61 |
| 2025 | 35.09 | 37.03 | 37.72 | +2.63 |

- By control-price tercile in 2024–25 the lift is low +3.4 / +4.7, mid +0.9 / +1.9, high +0.5 / +1.3.
- In 2021–22 it sits mostly in the high tercile (+3.7 / +5.7).
- Hours at or below $15 fall 1,024 → 827 (2024) and 869 → 654 (2025).

**Class energy, U4 − control, TWh:**

| year | CC_REGULAR | imports | CT_PEAKER |
|---|---|---|---|
| 2019 | −0.82 | 0.00 | +0.86 |
| 2020 | −1.85 | +0.86 | +1.36 |
| 2021 | −2.57 | +1.51 | +0.92 |
| 2022 | −4.63 | +3.39 | +1.05 |
| 2023 | −2.67 | +1.60 | +0.81 |
| 2024 | −3.41 | +1.91 | +1.23 |
| 2025 | −5.30 | +3.93 | +0.88 |

Against UC-3, U4 adds CC in 2019–21 (+2.76 / +1.37 / +0.92 TWh) and removes it in 2024–25 (−0.32 / −1.24 TWh).

**What moved, by mechanism:**
- **Per-unit `mlf` (epoch 15b).** Each committed unit carries more minimum-load energy: the MECH 28 CC share is 8–18 %, against UC-3's 2.5–6 %. Commitment is lumpier. Starts rise toward CEMS (T3: 0.92–0.97× in 2022–25), but the UC commits fewer units in the hours that set the price.
- **DA-forecast commitment demand.** The CISO forecast bias is positive in 2019 (+0.59 GW) and turns more negative every year from 2021 to 2025 (−0.18 → −1.56 GW mean). The UC therefore commits against less load than materialises in exactly the years where C3a fails.
  - The years with the largest negative bias (2024–25) show the largest CC loss against UC-3 and the largest C3a worsening in 2025 (+2.0 pts).
  - This is a correlation across 7 years, not an isolated effect; no arm here separates it.
- **Reserve co-opt + u-gate:** inert (§0).
- **Overlay off:** a no-op (§0).
- **Desk condition 2 (engine confound).** The near-zero price lift in 2019–20 (+$0.27 / +0.34) against +$1.6–4.2 in 2021–25 is a 2019–20 vs 2021+ contrast, so it is **flagged as engine-confounded** (uc-1.7 vs uc-1.8, bounded by the 1e-3 gap per window).
  - The DF bias also changes sign between the two groups, which is the more plausible driver.
  - C3a is unscoreable in 2019–20 either way (no reference), so the verdict does not turn on this contrast.

**Reading for the owner.** U4 brings commitment counts close to physics, but CAISO's price fit does not follow them. The uc-1.5 reading stands, slightly stronger: once the RA bridge's extra CC is gone, the model's replacement supply (import ladder, CTs, through hydro water value) is dearer than CAISO's real one. The missing object is still a measured import/WEIM price. That is a calibration-lane item, not a UC value. Nothing was tuned.

## 4. Wall and memory (GATESPEC §6.1; ratio = total ÷ (P0 + P1), same shard)

| year | engine | P0 s | UC (markup) s | P1 s | total s | ratio | MILP mean / p95 s | TL hits | int / clusters | cgroup peak GiB | container |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | uc-1.7 | 1,140 | 10,849 | 580 | 12,621 | **7.34** | 29.4 / 164.6 | **7** | 32 / 110 | 9.30 | 22.4 |
| 2020 | uc-1.7 | 1,242 | 2,271 | 714 | 4,302 | 2.20 | 5.83 / 10.0 | 0 | 35 / 114 | 9.38 | 22.4 |
| 2021 | uc-1.8 | 4,716 (cold, 516 k iters) | 1,854 | 761 | 7,384 | 1.35 | 4.79 / 22.1 | 0 | 33 / 112 | 9.47 | 22.4 |
| 2022 | uc-1.8 | 1,575 | 2,321 | 578 | 4,527 | 2.10 | 6.07 / 24.8 | 0 | 34 / 115 | 9.59 | 22.4 |
| 2023 | uc-1.8 | 533 | 2,616 | 563 | 3,801 | 3.47 | 6.82 / 26.4 | 0 | 34 / 115 | 9.69 | 17.4 |
| 2024 | uc-1.8 | 618 | 2,737 | 646 | 4,081 | 3.23 | 7.17 / 25.7 | 0 | 34 / 115 | 9.58 | 17.4 |
| 2025 | uc-1.8 | 753 | 2,673 | 682 | 4,177 | 2.91 | 7.04 / 24.7 | 0 | 33 / 114 | 9.82 | 17.4 |

- Windows: 2,555 / 2,555 Optimal or incumbent-kept; 0 infeasible.
- 2019 breaches W2 (7 time-limit hits) and runs 7.3×, the same February windows as uc-1.5. The other years run 1.4–3.5×.
- 2021's 1.35× is low only because its P0 ran cold (78.6 min) in its container. The UC stage itself took 1,854 s.
- Swap peak was 0 in every year. Peak cgroup was 9.30–9.82 GiB, so the owner's 11.8 GiB gate holds with 2.0 GiB of margin.
- Three 17.4 GiB containers solved cleanly.

## 5. Coverage and attempt log (`data/ucmilp4_readings/attempt_log.txt`)

- **Pin `23aefcae` (uc-1.7, pre FIX-8):** 4 shards, all stopped on the FIX-8 defect hold. None reached the UC stage, nothing was pushed, and the stop spends no attempt.
- **Pin `804aa916` (uc-1.7):**
  - 2019 and 2020 solved.
  - 2021–25 met the then-22.4 GiB gate at 17.4–18.4 GiB on 3/4 attempts each. Free disk was 10.3–11.4 GiB, which capped swap at 4–5 GiB.
  - Each year was held at 3/4 by desk ruling, pending the owner.
- **Pin `45574487` (uc-1.8, gate 11.8 GiB):** 2021–25 each solved on attempt 4/4.
- **Coverage: 7 / 7 years.** None held, none a gap.

## 6. Bundles and cost (rule 31: nothing deleted)

| leg | branch | commit | files |
|---|---|---|---|
| 2019 | `claude/ucmilp4-caiso-2019` | `f0b8f03c` | 21 |
| 2020 | `-2020` | `2dcd1cbb` | 21 |
| 2021 | `-2021` | `5ce9bc0a` | 21 |
| 2022 | `-2022` | `67b13b5a` | 21 |
| 2023 | `-2023` | `9550f03c` | 21 |
| 2024 | `-2024` | `f03c510a` | 21 |
| 2025 | `-2025` | `63e49e26` | 21 |

Each leg is a full bundle including `dispatch/<y>_P1.parquet` and the four UC sidecars; no file exceeds 95 MB.

- Slim span: `docs/records/caiso/ucmilp/data/ucmilp4_caiso_span/` (JSONs and `hourly/`; no `dispatch/`, floors or `unit_hourly`). The respanned benchmark frames reproduce the keeper's hashes exactly (`campd-9f21d7777a17`, `eia923-7b9c8f11474a`, `eia930-d44f3b3a0aee`), so the arm is scored on the control's basis.
- Readings: `data/ucmilp4_readings/`.
- Shards: 26 launched, 26 archived, none left alive.
- No promotion is proposed. The seven `claude/ucmilp4-caiso-*` branches are transport only and can be cut when this PR merges; a session cannot delete them (403).

## 7. D-6 card (copy-paste)

*"UC-4 CAISO (arm U4: UC + DA-forecast commitment + per-unit ut/mlf + reserve co-opt with the u-gate), all 7 years — record R. CC starts reach 0.92–0.97× CEMS in 2022–25 (keeper 2.9–3.3×), the closest any arm has come. But C3a 2022–25 sits at +11.0 to +13.5 % (band ±10 %) and C1 CC 2025 drops to −5.66 TWh: 5 flips, against UC-3's 4. The reserve co-opt never prices in CAISO, and the overlay it displaces was already $0. The DA forecast under-states load by 0.4–1.6 GW in 2022–25, so the UC commits less CC, and imports/CTs fill at a higher price. Options: (1) record R, stage default-off for CAISO [recommended]; (2) hold for a measured import/WEIM price object (CAISO calibration lane), then re-run U4; (3) promote on structure (not recommended: 5 flips)."*

## Log entry

- 2026-10-16 · UC-4-CAISO (Opus) · `claude/ucmilp-4-caiso` · PRECOMMIT `23aefcae` + Addenda A–C before any number · 7/7 legs (2019–20 uc-1.7, 2021–25 uc-1.8), 0 infeasible, 0 unserved · **R**: 5 flips (C3a 2022–25, C1 CC 2025); T1a/T1c/T3/T4 met; T2 wrong way · CC starts 0.92–0.97× CEMS in 2022–25 · reserve co-opt inert ($0 dual), overlay already $0 · wall 1.4–3.5× (2019 7.3×) · peak 9.8 GiB · not registered · cells `unit_commitment_milp` R (re-pointed), `uc_commitment_demand_source` U → R.
