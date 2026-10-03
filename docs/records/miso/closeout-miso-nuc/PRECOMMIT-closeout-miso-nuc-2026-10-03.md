# PRECOMMIT closeout-miso-nuc — MISO nuclear 2019–2022 at measured data, seven-year re-solve (R-43)

Lane `claude/closeout-miso-nuc-b`, 2026-10-03. I wrote this **before any LP**. Every reading below was fixed before any shard was launched.

## 0. Authority

Owner ruling **R-43** is recorded in `docs/backcast-closeout-plan-2026-10.md` §5.0 (PR #7120, 22fb72b1): *"MISO nuclear 2019–22: full rule-14 repair plus a 7-year re-solve, fit-negative accepted"*. The owner's card answer was "A: Full repair + 7 MISO shards". The evidence is `docs/records/miso/FINDING-closeout-miso-2-nuclear-2019-2022-2026-10-03.md`, at zero LP.

## 1. The change: one data repair, landed as PR #7129

**Pin:** `f98c456401918eba82c338676e303a90004bb94c` (the #7129 merge on `main`). The lane commit is `64d1771e`.

1. **Anchor rows.** `NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"]` gains 2019–2022 rows from the frozen `derive_nuclear_monthly_cf.py`.
   - This is an initial derivation, not a rule-23 re-derivation.
   - 2023–24 pass `--check`.
   - The 2025 Oct/Nov preliminary-vintage drift is not re-derived.
2. **NRC daily extract.** `data/raw/nuclear-availability-MISO.csv` is re-derived over 2019–2025.
   - Duane Arnold (1060, through 2020) and Palisades (1715, through 2022) enter as uncovered pass-through rows (`avail = avail_raw`). They are kept out of the anchor fit.
   - NRC renamed River Bend in 2019 ("River Bend 1" → "River Bend Station 1"); the rename is aliased.
   - Every 2023–25 row is byte-identical.
   - Under the frozen WEDGE_TOL/SCALE_CLIP, most 2019–22 months miss the anchor by 1–4 % and are dropped, so the anchor smear stands. NRC daily timing survives in 1, 3, 3 and 4 months of 2019, 2020, 2021 and 2022, and in every month for the two pass-through reactors. The same mechanism already keeps only 4, 6 and 7 months in 2023, 2024 and 2025.
3. **SolveEpoch `2026-10-03d`** (backcast MISO) and its `cache.py` ledger entry.

**What it is not:**
- It adds no `ScenarioConfig` field, so there is no matrix row and no cell edit.
- It moves no tuned value and adds no DOF.
- It does not touch the authorised band channel.

**Admissibility:**
- Rule 14: measured data replaces the forecast fallback `NUCLEAR_MONTHLY_CF × (1 − EFORD)`.
- Rule 13: these are the same inputs the 2023–25 legs already read.
- Rule 19: the change replaces the fallback; nothing is stacked on it.

## 2. G-DRIFT: keeper legs (25da6022) → pin

The full per-hunk table, with the merge-delta addendum, is in `GDRIFT-closeout-miso-nuc-keeper-to-pin.md` in this folder. It was built at zero LP.

**LIVE hunks** are only the R-43 data repair, and only for 2019–2022:
- the extract's 2019–22 rows;
- the MISO table's 2019–22 rows;
- epoch 03d, which moves the key only.

**Everything else is INERT with a reason:**
- ISO-gated away from MISO, or default-off and confirmed absent or False in every `run_config_<Y>.json`.
- `replay_keeper.flipped_default_overlay` returns only the keeper's own `capacity_screen_peak_measured_hindcast=False`.
- `kron_hours` was verified bit-identical to `sp.kron`.
- The loader refactors were read and found value-preserving.
- The EIA-923 Final 2025 refresh does **not** reach MISO: the generation-fuel blob is unchanged since 25da6022.
- In the merge delta, the calamine eGRID reader was re-read exactly for every vintage.

**2023–25 are byte-inert in substance but must be re-solved.**
- MISO's solve-surface fingerprint moves from `a4ebec6b29ae93a1` on every keeper leg to `32cf65618d245617` at HEAD, because of epoch 03d and the declared MISO table row.
- `_w0_compose_span.py` refuses legs whose fingerprints differ.
- The keeper holds only a composed span, not per-year legs.
- **So all seven years are solved at the pin.**

**E-INERT check (fixed now):** the 2023, 2024 and 2025 legs must reproduce the keeper's committed hourly sidecars (`class_hourly`, `system`, `unit_marginal`) to solver tolerance. Any material difference is a missed LIVE hunk or solver non-determinism. Either one is named in the RESULT before any promotion recommendation.

## 3. Pre-fixed readings (zero-LP sizing, FINDING §3–4; not targets)

| Row | Keeper | Sized after repair | Expected status |
|---|---|---|---|
| C1 ST_GAS 2019 | −8.60 TWh (FAIL, ±8.00) | ≈ −9.10 / −9.16 | FAIL, further out |
| C3b 2021 NRMSE | 0.213 (FAIL, ≤ 0.20) | ≈ 0.221 | FAIL, worse |
| C3a 2020 | +9.6 % (PASS, ≤ +10 %) | +8.9 … +10.2 % | PASS, or at its ceiling |
| C1 CC_REGULAR 2021 | PASS | −8.5 / −8.9 TWh vs ±8.00 | **PASS → FAIL** expected |
| C1 COAL_PRB 2022 | PASS | +8.11 in one bracket (B / cheapest) | possible PASS → FAIL |
| Nuclear 2019 / 2020 / 2021 / 2022 | flat fallback | +4.0 / −1.0…−2.3 / +2.3 / +1.2…+1.8 TWh | moves toward EIA-923 plant-matched |

The keeper determination is NOT-YET (C1, C3b). It is expected to stay NOT-YET. The worse readings become MISO's baseline (R-43; rule 14: a worse fit after real data is a discovered bug elsewhere). Nothing is tuned toward any of these numbers.

## 4. Kills: structure only

The lane holds, with no promotion recommendation, if any of these fire:

| Kill | Condition |
|---|---|
| K1 | Any new unserved energy in any year. The keeper has 0 MWh. |
| K2 | C6 governance goes non-PASS. |
| K3 | C8 forced-energy share goes non-PASS (rule 20). |
| K4 | The recipe diff against the keeper (`run_config_<Y>.json`) is anything other than the data repair. Expected: provenance, SHA, epoch and surface fields only; no `scenario_config` value differs. |
| K5 | E-INERT fails for 2023–25 without a named, benign cause. |

## 5. Decision rule (set ex ante)

- **If K1–K5 pass:** recommend promotion **whatever the direction of the fit** (R-43, rules 1 and 14). Every PASS→FAIL flip is named at full magnitude in the RESULT and becomes MISO's baseline.
- **If any kill fires:** report and hold. A session never deletes a result (rule 31).

The promotion slot is requested from the desk before `promote_keeper.py` runs.

## 6. Execution

- **Shards.** Seven year-isolated shards (rule 36), one per year 2019–2025. Each runs at the pin with `replay_keeper results/calibration/w0_miso_span --years Y --out-dir results/calibration/closeout_miso_nuc_<Y>`, with no `--set`.
  - Each shard runs the solve once and stops on the first failure.
  - Each pushes its full bundle to `claude/closeout-miso-nuc-<Y>`.
- **Compose.** `scripts/probes/_w0_compose_span.py` composes the legs into `results/calibration/closeout_miso_nuc_span`.
- **Score and register.** Then `calibration_verdict`, legitimacy diagnostics and the DOF ledger. The RESULT is registered as a probe.
