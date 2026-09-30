# RESULT — NYISO-NEXT-13: the NE AC node taken out of the monthly net-interchange band — 2026-09-29

- **Session:** NYISO-NEXT-13, the orchestrator. This container ran no LP (rule 32 (a)).
- **PRECOMMIT:** `docs/PRECOMMIT-nyiso-next13-ne-ac-recon-detach-2026-09-29.md`. Its gates (§5) and promotion rule (§6) were fixed before any solve.
- **Code:** PR #6875, which adds `nyiso_ne_ac_recon_detach` (default off, NYISO, backcast only, zero DOF).
- **Arm pin:** `3145578d94c73b6042ecabf1ff6723c70af3c742`.
- **Owner ruling (this session):** "Promote per rule". It was given after the price-fit regression below was put to the owner as a decision card.
- **New keeper:** `2026-09-29-nyisonext13-recon-detach-span`, bundle `results/calibration/nyisonext13_span`, years 2022–2025.
- **Stamped held-out run:** `2026-09-29-nyisonext13-recon-detach-2021`, bundle `results/calibration/nyisonext13_2021`.
- **Superseded and pruned (rule 35):** `2026-09-29-nyisonext12-neac-node-span` and its stamped 2021 run.

## 1. Headline

- **Phase 0 (zero LP) re-routed queue item 1.** The NE AC node's over-export and its hours at the posted bound were not the node responding to Capital_Hudson price.
  - The ±2 % monthly EIA-930 band binds in 11–12 of 12 months every year.
  - It pinned the node together with the pooled seams, and the node is the band's only export-capable row.
  - So the band's dual moved the node off its own bands in 37–66 % of hours.
- **Promoted on structure.** G-1, G-2 (a)(b)(c) and G-3 hold in all five years. With the lever armed, the node follows its own bands in 99.9–100 % of hours.
- **Price fit is worse, and 2021 loses CALIBRATED.**
  - Once the node is detached, the band pins the static pooled import ladder to its measured monthly volume (+4.1 TWh in 2021, +2.2 TWh in 2022). The node had been absorbing that gap.
  - The extra imports lower the price level.
- **Determination: span NOT-YET** (C3a 2022 and 2025; C3b 2022 is new; C1 2023 ST_GAS; C3c not lone). **2021: NOT-YET** (was CALIBRATED). Rule 30(c): a held-out year never downgrades the ISO.

## 2. Gates (arm vs the NEXT-12 keeper's committed bundles, form 4)

Records: `results/calibration/_nyisonext13_gates.json`, `_nyisonext13_compare_span.txt`, `_nyisonext13_compare_2021.txt`, `_nyisonext13_phase0.json`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance | pass | pass | pass | pass | pass |
| **G-2(a)** node on its own bands (keeper) | 100.0 % (36.9) | 99.99 % (33.7) | 100.0 % (61.6) | 99.89 % (33.5) | 99.99 % (63.2) |
| **G-2(b)** pooled node inside the band | 12/12 | 12/12 | 12/12 | 12/12 | 12/12 |
| **G-2(c)** hours exporting / importing | 5005 / 2515 | 5513 / 1785 | 5070 / 2823 | 5362 / 2931 | 6432 / 1229 |
| **G-3** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| node TWh: keeper → arm (measured) | −0.74 → −3.30 (−5.17) | −1.25 → −3.90 (−3.51) | −2.98 → −3.71 (−4.47) | −7.35 → −4.00 (−5.84) | −7.56 → −5.64 (−5.76) |
| pooled TWh, arm (target) | 32.40 (33.06) | 31.32 (31.82) | 27.73 (27.93) | 26.58 (26.19) | 25.11 (24.84) |
| h at posted export bound, keeper → arm | 335 → 567 | 307 → 611 | 382 → 407 | 891 → 503 | 969 → 647 |
| C3a, keeper → arm | −1.7 → **−14.3 %** | −10.1 → **−13.6 %** | −2.1 → −7.0 % | −0.9 → −2.5 % | −11.3 → −11.3 % |
| C3b NRMSE, keeper → arm | 0.153 → **0.219** | 0.192 → **0.226** | 0.118 → 0.159 | 0.160 → 0.158 | 0.177 → 0.179 |
| price MAE $/MWh, keeper → arm | 10.11 → 10.54 | 21.06 → 21.25 | 8.25 → 8.16 | 9.60 → 9.34 | 24.33 → 24.44 |
| Δ system LW price $/MWh | −4.94 | −2.86 | −1.59 | −0.61 | +0.01 |
| C1 | CC_REGULAR +3.1 pp **FAIL** | pass | ST_GAS +3.5 pp FAIL (was +3.2) | pass | preliminary 923, not gated |

- **Node volume versus measured.** The node's annual TWh now lands closer to measured in 2021, 2024 and 2025 and further away in 2022 and 2023.
- **Hours at the posted export bound.** The node still sits at its bound 407–647 h/yr. Measured prices pushed through the same bands give 311–587 h (phase 0), so that count is a property of the construction, not a pricing error.
- **Why price falls.** In 2022 the arm raises pooled imports mostly in low-price hours (+262 MW in the bottom half of hours), and the node exports there instead (−450 MW). The top-decile hours barely move.
- **Benchmark inputs.** Resolved inputs are byte-identical to the keeper's in every leg.
- **Solver environment.** The shard containers solved on highspy 1.15.1 against a pinned 1.14.0 (audit E14 warning). The CAISO keeper is in the same off-pin state.

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `17a6552bbf2e1ca06be9dbb2cc529cc655853215` | 17 |
| 2022 | `f97399a2db90a8f0dd47e7149153b3dbeb69d48e` | 17 |
| 2023 | `6a660910b9aaa311878fd8c00b7cb2a99db37af7` | 17 |
| 2024 | `f8a4da9f8b9f625fc6df49d6e968ae3c74e8a6c8` | 17 |
| 2025 | `bd54263cc6cd928a8b195635b8fe242415fefb0f` | 17 |

- **Launch incidents.** It took three waves; every shard session was archived.
  - Wave 1: the permission classifier in the shard containers stopped responding (2023/2024/2025). Separately, the `capacity-deliverability` clean partition was absent in 2021; that loader only warns, then fails later with a misleading "no published Long Island limit".
  - Wave 2: hard stop 2 rejected `miso_gas_ecomin_online_floor: false`. That field post-dates the keeper and sits at its default, so this was a defect in my prompt. The 2024 leg pushed anyway.
  - Wave 3 fixed both. The next handoff's prompt carries the fixes.
- **Retrievability.**
  - The keeper bundle `nyisonext13_span` and the 2021 bundle land on `main` with this PR.
  - The per-year legs for 2022–2025 are gitignored (rule 32 (d)).
  - Recovering a leg that is not on `main` costs a re-solve (~5 min of LP per year).

## 4. What remains

1. **The pooled static import ladder.** With the node detached, the band forces the ladder to its measured monthly volume, and the added imports lower the price level. The object is the ladder's shape: a static annual rung price against the neighbour's hourly price. The band is not the object.
2. **C3a 2022 / 2025** (−13.6 / −11.3 %) and **C3b 2022** (0.226).
3. **NYC steam over-dispatch** (C1 2023 ST_GAS) and **the in-city commitment requirement**. MyNYISO access is held by the owner.
4. **Rating-bound downstate lines** (Neptune / VFT / CSC) as availability blocks at published ratings (rule 13).
5. **The >$300 RT tail** (nyiso-242).
6. **IESO May–Dec 2025 price** is a public-data gap.
7. **Leftover branches for the owner to delete** (a session cannot delete refs): `claude/nyisonext12-{2021..2025}` and `claude/nyisonext13-{2021..2025}`.
