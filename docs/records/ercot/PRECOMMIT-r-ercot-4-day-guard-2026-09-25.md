# PRECOMMIT — R-ERCOT-4: same-day CEMS guard on the shaped partial-outage layer

**Session:** R-ERCOT-4, 2026-09-25.
**Owner authorization (verbatim):** "Yes to arming". This answers the question at the end of `FINDING-r-ercot-4-validation-years-2026-09-25.md`.
**Keeper and control:** `2026-09-25-r-ercot2-chp-off`, bundle `results/calibration/r_ercot2_chpoff_span`, 2019–2025. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)); no control solve is spent.
**Written before any solve.** The pinned SHA is the commit that carries this file.

## 1. The mechanism (one field, zero new scalars)

**Field:** `ScenarioConfig.ercot_partial_outage_day_guard`.
- Default `False`; ERCOT backcast-only.
- It acts only with `ercot_partial_outage_shaped_derate`, which the keeper arms.

**What it reads when armed:** `data/raw/campd-partial-outages-shaped-dayguard.csv`
- sha256 `9d18dc29…3da`.
- Written by `derive_partial_outages.py --emit-shaped-dayguard`; constructed by `scripts/lib/outage_detect.detect_shaped_dayguard`.
- It has the same plateaus and the same sub-window tiling as the shaped extract (SP-2 asserted in the deriver).
- Each day is floored at the plant's own same-day measured ceiling: `guarded(d) = max(shaped(d), round(min(1, dmax[d]/ref), 3))`.
- `dmax` and `ref` are the frozen detector's own statistics, so the construction adds no scalar (rules 21/23).
- ercot-185's SP-6 median preservation is replaced by the day-floor property. The guard is a net lift by design, and it is stated as such.

**Rule 23 frozen-derive proof.** The deriver was re-run at HEAD over 2018–2026. Excluding 2018, the flat, unit-attributed and shaped extracts are **line-for-line identical** to the committed files.
- **2018 is not reproducible locally.** The 2018 CAMPD unit vintage is gitignored (BLOAT-S2). The guarded file therefore carries no 2018 rows, and the loader falls back to the unguarded shaped layer for any absent year, with a log line. No keeper year is 2018.
- **Found and fixed on the way:** COAL-SUB relabelled the bin sheet, and the deriver's `_DETECT_GROUPS` filter silently lost **every coal plateau** (only 175 of 452 windows came out, all CC). The group is now read through `artifact_class`, the COAL-SUB seam. This is the fix that restores the byte-identical reproduction above. It changes no committed extract.

**Why it is structural (rule 1), not fitted.**
- A plant's available capacity on a day is never below what it measurably produced that day.
- The layer violated this on 59–120 coal plant-days per year (`FINDING-r-ercot-4`).
- It was found from the October 2021 residual. It is kept or rejected on that physical identity, never on how the residual moves.

## 2. Zero-LP seam (fleet-only rebuilds, guard ON vs OFF, keeper recipe)

Measurement setup:
- An A/A null (guard off, built twice) is byte-identical, so the builds are deterministic.
- `mc_base` is byte-identical in every year.
- `pmax` is identical.
- Availability × pmax changes as below.

| year | COAL availability lifted (TWh) | CC_REGULAR net (TWh) | rows changed |
|---|---|---|---|
| 2019 | +0.365 | +0.058 | 518 |
| 2020 | +0.534 | +0.036 | 522 |
| 2021 | +0.505 (lift only, zero cuts) | +0.062 (+0.078 / −0.016) | 501 |
| 2022 | +0.378 | +0.051 | 539 |
| 2023 | +0.602 | +0.108 | 527 |
| 2024 | +0.445 | +0.096 | 547 |
| 2025 | +0.278 | +0.123 | 500 |

- **2021, Oct 20 15:00–19:00:**
  - coal available 7,969 → **9,421 MW**
  - Martin Lake 916 → **2,368 MW**
  - CAMPD gross that afternoon: 11.3 GW coal; Martin Lake 2,577 MW.
- **Downstream consumers of the same measured layer** (reported, not added):
  - Up to 21 coal `min_gen` rows per year move, through the availability-conditional ERCOT min-config floor.
  - The CC_REGULAR −0.016 TWh in 2021 comes from the within-class DAM plant pin.

## 3. G-DRIFT (keeper solve SHA `8beff24de53472d4dfe3c1aec6910eb592c00622` → HEAD)

**Scope:** 61 files on the backcast path, audited hunk by hunk at zero LP.

**Verdict: ALL INERT for ERCOT backcast 2019–2025.** Nothing is LIVE and nothing is UNDETERMINED.

What changed in that window:
- **SOCO / NWPP / CAISO / MISO / PJM changes:** gated on their own tables.
- **COAL-SUB:**
  - `RESULT-coal-sub` §2 proves every FleetArrays field and `mc_base` byte-identical for ERCOT 2019–2025.
  - The post-fleet hunks (reserves posture, RUC class groups, scarcity envelopes, ramp-group fallback) read the subclass back through `artifact_class` / `COAL_CLASSES` to the identical mask or value.
- **Scoring-only changes:** the benchmark code changes are SOCO-gated or label-equivalent. `_validation-source` has no ERCOT change.
- **The one operational effect:** ERCOT's cache key moves with the solve-surface fingerprint. That changes identity, not numbers.

**Form 4 is therefore valid.** The arm is differenced against the committed keeper numbers.

## 4. Sealed predictions (per year, arm vs keeper)

Keeper baselines, read from the committed bundle and payload:

| year | LW price | P1 slack MWh | hours > $1k | C3a | C3b |
|---|---|---|---|---|---|
| 2019 | 94.29 | 7,205.5 | 74 | +101.1 % FAIL | 1.850 FAIL |
| 2020 | 30.62 | 0.0 | 5 | +20.1 % FAIL | 0.459 FAIL |
| 2021 | 181.07 | 14,907.0 | 142 | +9.4 % PASS | 0.203 FAIL |
| 2022 | 73.13 | 0.0 | 25 | −1.8 % PASS | 0.100 PASS |
| 2023 | 61.96 | 163.5 | 66 | −3.7 % PASS | 0.137 PASS |
| 2024 | 31.58 | 687.4 | 8 | +1.9 % PASS | 0.141 PASS |
| 2025 | 34.40 | 0.0 | 0 | −5.2 % PASS | 0.096 PASS |

Predictions:
- **P1 (2021, the object).**
  - The Oct 20–25 scarcity event is removed: October P1 slack falls from 3,709 MWh to **< 500 MWh**, and October's model month mean drops toward the ~$55 non-event level.
  - **C3b 0.203 → ≤ 0.17 (PASS).**
  - C3a stays PASS and falls (+9.4 % → between +3 % and +8 %).
  - February (Uri) slack is essentially unchanged.
- **P2 (every year).**
  - Coal P1 energy rises by 0.05–1.0 TWh, and gas falls by about the same.
  - LW price does not rise.
  - Slack does not rise.
- **P3 (2019).**
  - Slack and hours above $1k fall.
  - C3a improves but stays FAIL (> +10 %).
  - C3b stays FAIL.
- **P4 (2020).**
  - C3a improves and most likely stays FAIL.
  - The C1 COAL_PRB gap (−13.75 TWh) closes by **< 1.5 TWh**. The shortfall stays FINDING-r-ercot-3's offer-conduct object.
- **P5 (2022–2025).**
  - Every year stays CALIBRATED at the year level.
  - Each C3a moves by ≤ 4 points, toward cheaper.
  - 2025 C3a (−5.2 %) stays inside ±10 %.
  - Train-tier determination **stays CALIBRATED**.
- **P6 (C8 forced share).** No material class crosses its forced-energy cap because of this arm.

## 5. Decision rule (fixed now)

- **Rule 1 governs.** The guard is kept or rejected on the physical identity, not on the scores.
  - If every train year stays CALIBRATED, the recommendation is **promote**, whatever the validation years do.
  - If a train year flips to NOT-YET, report it at full magnitude with the root cause (rule 14), and put it to the owner **with no recommendation to revert**. A structurally correct input that worsens the fit exposes a compensating error elsewhere.
- **Promotion is the owner's call** (rules 31/35). Nothing is pruned in this session without that ruling.

## 6. DOF ledger (carried VERBATIM from the keeper attestation)

- 12 entries, 7 residual.
- This arm adds **no entry**: the guard's only quantities are the frozen detector's `dmax` and `ref`.
- Offer-curve band multipliers are unchanged leg-for-leg (rule 1(c)). Nothing is re-tuned.

## 7. Execution

**Shards:** seven, one per year 2019–2025 (rules 34(c) / 36). Prompts are in `docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-4.md`, pinned to the SHA of the commit carrying this file.

**Each shard:**
- runs `replay_keeper.py results/calibration/r_ercot2_chpoff_span --years <Y> --set ercot_partial_outage_day_guard=true`;
- checks the input sha256s and the per-year config signature before pushing;
- pushes its full bundle, `dispatch/<Y>_P1.parquet` included, through a `.gitignore` negation and a plain `git add`.

**The parent then:**
1. composes with `scripts/probes/_r_ercot_compose_span.py`;
2. checks with `stamp_config_partition.py --check`;
3. attests, then registers with `dashboard_add_run.py --no-prune`;
4. updates the ERCOT matrix cell and writes the RESULT and calibration-log entries;
5. archives the shards;
6. asks the owner the promotion question.
