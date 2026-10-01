# RESULT — NYISO-NEXT-14: the Total-East cutset envelope re-tested on five years — 2026-09-30

- **Session:** NYISO-NEXT-14, the orchestrator. This container ran no LP (rule 32 (a)).
- **Phase 0:** `docs/FINDING-nyiso-next14-upstate-evacuation-phase0-2026-09-29.md`.
- **PRECOMMIT:** `docs/PRECOMMIT-nyiso-next14-total-east-cutset-2026-09-30.md`. Its gates (§5) and promotion rule (§6) were fixed before any solve.
- **Owner ruling (decision card, this session):** "Re-test all 5 years". This re-opened cell R `nyiso_total_east_cutset_ttc` (nyiso-224, ruled "reject as constructed" 2026-09-10).
- **Code:** none. The flag and its table already existed.
- **Arm pin:** `ac7d36d66bb864211201176f11c9fdd16b64ab10`.
- **New keeper:** `2026-09-30-nyisonext14-total-east-span`, bundle `results/calibration/nyisonext14_span`, years 2022–2025.
- **Stamped held-out run:** `2026-09-30-nyisonext14-total-east-2021`, bundle `results/calibration/nyisonext14_2021`.
- **Superseded and pruned (rule 35):** `2026-09-29-nyisonext13-recon-detach-span` and its stamped 2021 run.

## 1. Headline

- **Span: NOT-YET → CALIBRATED.** C3c is the lone ledgered caveat (rubric v3.3). C1, C2, C3a, C3b, C4, C6 and C8 pass in every scored year.
- **Held-out 2021: NOT-YET.** C3a flips from −14.3 % to +10.9 %. Rule 30(c): a held-out year never downgrades the ISO.
- **Promoted on structure.** G-1 to G-4 hold in all five years.
- **Open: the upstate price now overshoots.** Upstate_West moves from collapsed to above measured in 2021–2023. The link binds in hours that do not match the market's. nyiso-225's caveat is confirmed, not cleared.

## 2. Gates and reported numbers (arm vs the NEXT-13 keeper's committed bundles, form 4)

Records: `results/calibration/_nyisonext14_gates.json`, `_nyisonext14_compare_span.txt`, `_nyisonext14_compare_2021.txt`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance | pass | pass | pass | pass | pass |
| **G-2** link at its bound, % of h (band 1–50) | 7.3 | 17.2 | 7.1 | 3.0 | 5.5 |
| market CENTRAL EAST ≥ 95 % of limit, % of h | 19.2 | 10.0 | 4.4 | 2.5 | 3.6 |
| **G-3** Upstate_West h ≤ $0 (keeper; measured DA 0) | 0 (3,110) | 0 (1,263) | 0 (723) | 0 (0) | 0 (0) |
| **G-4** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| C3a, keeper → arm | −14.3 → **+10.9 %** | −13.6 → +2.3 % | −7.0 → +5.0 % | −2.5 → −1.4 % | −11.3 → −8.8 % |
| C3b NRMSE, keeper → arm | 0.219 → 0.165 | 0.226 → 0.195 | 0.159 → 0.141 | 0.158 → 0.155 | 0.179 → 0.160 |
| Upstate_West $/MWh: keeper → arm (measured RT) | 7.3 → 41.1 (28.5) | 27.5 → 77.4 (56.7) | 18.4 → 32.1 (25.3) | 33.4 → 35.6 (33.1) | 50.5 → 57.5 (55.5) |
| NYC $/MWh: keeper → arm (measured RT) | 47.7 → 44.7 (42.5) | 92.5 → 85.9 (87.2) | 36.0 → 34.6 (33.5) | 39.1 → 38.7 (39.5) | 62.8 → 61.7 (67.2) |
| hydro TWh: arm (EIA-923) | 27.25 (28.76) | 26.18 (27.43) | 26.83 (28.40) | 26.74 (27.88) | 24.06 (24.10) |
| C1 ST_GAS share, keeper → arm | +0.1 → −1.7 pp | +0.7 → −0.5 pp | **+3.5 → +2.5 pp** | +0.3 → +0.2 pp | not gated |
| link binding-hour lift vs market | 1.37 | 0.74 | 1.07 | 0.31 | 0.69 |
| CH − UW spread in binding h: model (measured basis in market binding h) | 2.8 (20.2) | 7.8 (55.8) | 2.8 (19.7) | 2.1 (34.7) | 3.4 (42.1) |
| price MAE $/MWh, keeper → arm | 10.54 → 11.75 | 21.25 → 25.92 | 8.16 → 9.44 | 9.34 → 9.41 | 24.44 → 24.87 |

- **The structural target is met.** Before, the upstate surplus priced at ≤ $0 in thousands of hours; now it never does, which matches measured. Model hydro rises by 2.9 / 1.5 / 0.7 TWh in 2021–2023 (less spill).
- **The replacement limit is too loose in the hours that matter.** The measured Capital_Hudson − Upstate_West basis in the market's CE-binding hours is $20–56. The model's spread in its own binding hours is $2–8, and those hours coincide with the market's no better than chance.
- **So the level is now too high upstate in 2021–2023.** Upstate_West is $12.6 above measured in 2021 and $20.7 above in 2022. The 2021 C3a flips sign.
- **Price MAE rises in 2021–2023.** A better mean with a worse hourly fit is the signature of the wrong binding hours. This is reported, not gated (rule 1).

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `ff2aeb0a0199a6b3b13efc8861d35395c5171cb3` | 17 |
| 2022 | `0e0cceaf09bbf300fe4c2bd6642dd0967e4faf19` | 17 |
| 2023 | `0ddf46df65a455c6a49f83c6809dab707aedd4fd` | 17 |
| 2024 | `bb42e16e58eb67d475b9ce8391a438e265a84ba9` | 17 |
| 2025 | `b267908e4314c132bc655da7e0d17a973ba2439f` | 17 |

- **Launch incident.** Four of five shards first hit a missing `hydro-plant-modes` clean partition, then regenerated it and re-launched. The next handoff adds it to the mandatory pre-solve list.
- **Retrievability.** The keeper bundle `nyisonext14_span` and the 2021 bundle land on `main` with this PR. The 2022–2025 legs are gitignored (rule 32 (d)). Recovering a leg not on `main` costs a re-solve (~5–15 min of LP per year).

## 4. What remains

1. **The overshoot and the wrong-hours binding.** The cutset envelope removes the fabricated collapse but binds in the wrong hours, and the rent is too small when it does. The object is how the one zonal link represents a sub-cutset that binds (CENTRAL EAST) inside a cutset that never does (TOTAL EAST). A monthly p90 cap is a level, not a binding pattern.
2. **2025 peak formation.** C3a −8.8 % passes, but the top price decile still carries the miss: winter gas days, the June heat wave and the >$300 tail.
3. **NYC steam.** C1 2023 ST_GAS now passes at +2.5 pp, but NYC steam is still 8.3 TWh against 2.6 measured.
4. **The `complete` marker.** It was withdrawn 2026-09-25 (R-BC, Q5: no marker on a NOT-YET keeper). The keeper now reads CALIBRATED, so Q5 no longer bars it. The held-out 2021 run is NOT-YET, so the rubric does not clear every year. Reinstating the marker is the owner's call.
5. **IESO May–Dec 2025 price** is still a public-data gap.
