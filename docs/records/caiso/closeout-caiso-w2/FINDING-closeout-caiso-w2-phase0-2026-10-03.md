# FINDING closeout-CAISO wave 2: phase 0 (zero LP), the open fold steps (2026-10-03)

Lane charter: backcast close-out DESK (`session_01ERkBTm23ZAP4CTZnJVD9Ss`), 2026-10-03, branch
`claude/closeout-caiso-w2` cut from `origin/main` `1e3e4177`. Owner direction (verbatim): *"There are definitely
uncalibrated ISOs that should be being rerun and tested."* **Zero LP**: no shard launched, no run registered, keeper
unchanged: `2026-10-02-closeout-caiso-w1-arm2` (bundle `results/calibration/closeout_caiso_w1_a2_span`, 2019–2025).

## 0. Where the queue stands

Rubric v3.20. The ISO is NOT-YET on two FAILs only, both in the fold:
- **C1 CC_REGULAR**: +5.63 / +13.46 / +6.59 TWh (bands ±4.84 / ±4.60 / ±4.83);
- **C4 gas**: r / NRMSE 0.888 / 0.385, 0.893 / 0.399, 0.857 / 0.348 (bar NRMSE ≤ 0.30).

C3a/C3b 2019–21 are owner-signed reference-coverage caveats (R-40). C3c 2021 is masked to the RT window (R-34).

Plan §3.7, step by step (the plan wins over the desk pointer):

| Step | Status | Where |
|---|---|---|
| 0a OASIS pre-2021 | REFUSED (R-16) | plan §3.7 |
| 0b corridor census | DONE (w1) | `../closeout-caiso-w1/FINDING-…-phase0` §1 |
| 0c `zonal_gas_basis` 2021 sizing | DONE (w1); the arm was then PROMOTED on structure | w1 RESULT arm 2 |
| 0d C3c-2021 census | DONE (w1); scorer fixed by R-34 | closeout-caiso-2 |
| 0e / 1 printed-hour extension 2019–21 | blocked by R-16 (no print exists) | — |
| 2 `caiso_zonal_gas_basis` | DONE (w1 arm 2, keeper) | — |
| 3 `caiso_ra_min_load_frac` 0.570 | DONE (w1 arm 3) | — |
| 4 link-15 joint gas re-basis | CLOSED 2026-10-02, no solve | `../r-caiso-33/` |
| "lever for later": DSW formula-hub shape from the DSW BAs' own net load | **this record §1: NOT CHARTERED** | |
| retest `caiso_citygate_blackout_bridge` on the 2019–21 prints | **this record §2: NOT CHARTERED** | |

After R-33 the closeout-caiso-2 decomposition stands: imports carry 65 % / 90 % of the 2020 / 2021 CC miss. 2019
splits into demand (+3.13), other gas (−2.39) and imports (−1.50). §3 adds one check (outage coverage) and §4 sizes
the one lever left with reach, which is owner-gated.

## 1. DSW (and PNW) formula-hub shape from the corridor's own BAs: NOT CHARTERED

**What it would change.** In the unprinted hours (all of 2019–20, Jan–Apr 2021), R-CAISO-18 prices Palo Verde as
`gas_AZ(month) × 13.0 × (CISO net load / mean)`. Malin uses `gas_OR × 16.0 × (CISO gross load / mean)`. The
candidate swaps the CISO proxy for the corridor's own BAs (`CAISO_CORRIDOR_DIBA`: DSW = AZPS, IID, LDWP, NEVP, SRP,
WALC; PNW = BANC, BPAT, PACW, TIDC). Source: EIA-930 BALANCE archive, committed. No new parameter.

Probe `scripts/probes/_closeout_caiso_w2_dsw_shape.py` → `_dsw_shape.json`.
- It reproduces the keeper's P1 DSW offers to 1e-6 $/MWh once `caiso_eia930_clock_repair` is armed, as the keeper
  solves.
- First-order reach at fixed duals is large:

| | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| DSW net import, first order (TWh) | +7.40 | +9.63 | +1.35 |
| PNW_midC add / drop (TWh) | +4.74 / −0.11 | +3.34 / −1.43 | +0.33 / −1.72 |

- Δhub by hod: overnight −2.5…−4 $/MWh, midday +4…+7, evening −4…−5 (2021 Jan–Apr about ×3).

**The gate, fixed before it was computed.** Probe `_closeout_caiso_w2_shape_validation.py` →
`_shape_validation.json`.
- Test: on PRINTED hours the measured hub exists, so the two shape drivers can be scored against it out of the fold.
- Bar: per corridor, the own-BA shape must beat the CISO proxy on BOTH the hourly Pearson r and the hod-profile RMSE
  (unit-mean) against the measured hub, in ≥ 3 of 4 years 2022–25.

| DSW (Palo Verde) | 2021 May–Dec | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| proxy r / hod RMSE | 0.684 / 0.148 | 0.790 / 0.103 | 0.648 / 0.222 | 0.663 / 0.271 | 0.718 / 0.181 |
| own-BA r / hod RMSE | 0.600 / 0.256 | 0.664 / 0.217 | 0.466 / 0.379 | 0.597 / 0.419 | 0.547 / 0.314 |

| PNW (Malin) | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| proxy r / hod RMSE | 0.576 / 0.202 | 0.755 / 0.192 | 0.490 / 0.244 | 0.564 / 0.227 | 0.363 / 0.266 |
| own-BA r / hod RMSE | 0.373 / 0.241 | 0.727 / 0.236 | 0.367 / 0.297 | 0.555 / 0.257 | 0.255 / 0.278 |

**Own-BA wins: 0 of 4 years, both corridors. FAILS.**
- Within-day r tells the same story (DSW 2022: 0.649 proxy vs 0.508 own).
- The western hubs clear on the WEIM/CAISO duck. Palo Verde's diurnal shape follows CAISO's net load, not its host
  BAs'. The plan's premise that "the code proxies with CISO's" was a defect is refuted on measured prints: the proxy is
  the better measured driver (rule 14), so it stays.
- Reported for completeness: AZPS's EIA-930 solar centroid reads 13.1–13.6 h MST against 12.5–12.7 for the other DSW
  BAs. It is immaterial here (1.7 TWh of 30 TWh demand) and is not repaired.

## 2. `caiso_citygate_blackout_bridge` on the 2019–21 prints: NOT CHARTERED

G-FOOT289 was re-run (`scripts/probes/caiso288_blackout_census.py`, post-repair series):
- 2019: 59 bridged days, mean −0.171 $/MMBtu → **−1.28 $/MWh** of CC marginal cost;
- 2020: 62 days, −0.102 → **−0.76 $/MWh**;
- 2021: 0 days;
- 2024 / 2025: 11 days each, +$1.47 / +$2.91 (the Thanksgiving weeks the caiso-288 G-DUP guard refuses);
- left-edge channel: 0 everywhere.

On ~17 % of fold days, cheaper in-state gas would **raise** CC dispatch against the formula-priced imports. That is
the wrong sign for the only fold FAIL it could touch, and it is sub-noise. The cell stays **O**. Its open question is
the 2024/25 G-DUP conflict, not the fold.

## 3. CC outage-window coverage in the fold: no gap

The armed CAMPD unit-outage extracts carry the fold years:
- `campd-unit-outages-CAISO.csv`, CC_REGULAR events by start year 2019 / 2020 / 2021: 443 / 429 / 460 (2022–25:
  377–533);
- `-shortgas-CAISO.csv`: 340 / 281 / 250.

CC over-availability from missing fold outage data is not the object.

## 4. The one lever with reach is owner-gated: the R-CAISO-20 pattern for the daytime and late-evening rungs

Probe `scripts/probes/_closeout_caiso_w2_unprinted_rungs.py` → `_unprinted_rungs.json`. It reads the keeper
sidecars and the EIA-930 corridor net import (`corridor_net_import`).

**What changed since the 2026-09-30 card ("Arm overnight rung pre-2021" + "Ledger the fold gap").** R-33 moved the
C1 bench. The CC_REGULAR energy a fold lever must remove is now **0.79 / 8.86 / 1.76 TWh**; under R-CAISO-20's bench
it was 5.9 / 12.9 / 3.3. The remaining DSW gap sits in exactly the windows this arm would open:

| TWh | 2019 | 2020 | 2021 (Jan–Apr) |
|---|--:|--:|--:|
| unprinted hours | 8,760 | 8,760 | 2,784 |
| EIA-930 DSW gap, hod 6–21 / 22–23, model − measured | −8.10 / −1.30 | −10.56 / −2.35 | −4.79 / −0.84 |
| measured p95 depth, hod 6–21 / 22–23 (MW) | 7,348 / 6,922 | 7,122 / 7,281 | (static 5,733 / 6,415) |
| capability at that depth | 29.6 + 3.1 | 28.9 + 3.2 | 8.3 + 1.1 (static) |
| **first-order added DSW import** (non-binding hours, offer < λ_SP15, net of running DSW fossil) | **+19.1** | **+22.6** | **+4.8** |
| same at the pooled static depth | +12.1 | +15.7 | +4.8 |
| DSW fossil displaced | 9.2 | 3.6 | 0.9 |

- R-CAISO-20 realized 26–63 % of its first-order estimate. That projects about +5–12 / +6–14 / +1.3–3 TWh of added
  DSW import.
- **Likely reading:** C1 2019 and 2021 → PASS; 2020 uncertain.
- **Risk:** 2019 overshoot, since its overnight hours already sit +0.3 TWh over EIA-930.
- **No price exposure:** 2019–20 carry no C3 reference, and Jan–Apr 2021 is outside the RT window.

**Why it is not admissible on measurement.** R-CAISO-19 FINDING §3:
- without a raw print the caiso-87 trigger compares two gas constructions, and the caiso-269 DA-hub spread cannot be
  formed;
- the WEIM DSW footprint was also smaller in 2019–20 (AZPS, NEVP; SRP from 2020-04).

So arming is a **transfer** of the 2022–25 structure, which only an owner ruling can authorise (rule 13). The
R-CAISO-20 overnight arm is the precedent.
- Sent to the desk as an owner-card ask, 2026-10-03: A "Arm daytime + late-evening pre-2021" / B "Keep the ledger".
- The flag is pre-built default-off (`caiso_dsw_daytime_lateevening_unprinted_arm`, no solve). The conditional
  PRECOMMIT is `PRECOMMIT-closeout-caiso-w2-unprinted-rungs-2026-10-03.md`.

## 5. Matrix

- `caiso_dsw_daytime_lateevening_unprinted_arm`: new row; CAISO **U** (built, not solved); `.` in every other shard
  (rule 28(c)).
- `caiso_citygate_blackout_bridge`: stays **O**; the fold census is added to its evidence.
- `caiso_intertie_unprinted_year_measured_gas`: stays **K**; the own-BA shape alternative is recorded as refuted on
  printed hours.
