# PRECOMMIT: PJM-NEXT-25. Measured COAL tranche rows for PJM's 18 uncovered coal plants (soco-70 coverage append)

**Keeper:** `2026-09-30-pjm-next16-ovec` (bundle `results/calibration/pjmnext16_A_span`, 2019–2025).

**Arm:** data only, with no `ScenarioConfig` change. Evidence: `RESULT-pjm-next-25-2026-10-02.md` §§1, 3.

**Solved by:** the NEXT session's shard chain (owner instruction, 2026-10-02). This session launched no shard.

## 1. Mechanism, driver, forward story

- **What.** `data/raw/_processed-legacy/thermal_tranches_PJM.csv` gains 18 COAL rows, appended by `scripts/data/derive_thermal_tranches.py --iso PJM --years 2019 2020 2021 2022 2023 2024 2025 --coal-unit-coverage`.
  - The 29 prior COAL rows, and every other row, are byte-identical: the old file is an exact byte-prefix of the new one.
  - sha256 `497c4844…` → `31455aaa2eda1078885db02c62bfc80c3887aad18bbfbc156396617a2a2e6f73`, 257 → 275 lines.
  - The sidecar records the append.
- **The plants:**
  - 594 Indian River, 883 Waukegan, 884 Will County, 1554 Wagner;
  - 1571 Chalk Point, 1572 Dickerson, 1573 Morgantown, 2836 Avon Lake;
  - 2840 Conesville, 2866 Sammis, 3122 Homer City, 3140 Brunner Island;
  - 3149 Montour, 3797 Chesterfield, 6019 Zimmer, 8226 Cheswick;
  - 10678 Warrior Run, 54304 Birchwood.
- **Driver (rule 13 / 14).** Each plant's own CEMS coal-fired units over its own operating years. The construction and constants are the incumbent COAL branch's (`coal_unit_coverage_rows`, soco-70; zero DOF, rule 21). This replaces the class default (must-run 0, committed ≈ 0.05, econ ≈ 0.93) that an estimate filled where measured data exists. That is rule 14 verbatim.
- **Rule 23 citation.** The incumbent window was 2024, before which these plants had retired. Their CEMS years now sit inside the solved backcast span.
- **Forward story.** Forecast years carry only plants that the 2024-window rows already cover. The appended rows bind only in years the plants exist, and the construction is mode-blind.
- **Known limit.** The appended plants have no per-year `online_frac` row (`thermal_tranches_online_frac_by_year_PJM.csv` covers facility-summed rows only). Under `coal_sync_online_frac_per_year` they therefore keep their pooled operating-years fraction, which is the gate's own declared fallback (`arrays.py`). Not repaired here.
- **Not included:** the Tait 55248 → 2847 remap. One delta per solve.

## 2. Zero-LP verification (done; `_pjmnext25_coalrows_fleet_delta.json`)

- **Confinement.**
  - Outside the appended plants, `pmax` and `mc_base` never move.
  - `min_gen` moves only through the existing reliability floor's limb re-allocation (ComEd / West-APS, ±0.05 TWh).
- **Floored TWh at the appended plants**, incumbent → candidate:

  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|
  | 0.33 → 5.93 | 0.23 → 5.38 | 0.32 → 5.10 | 0.06 → 2.76 | 0.00 → 0.26 | 0.00 → 0.44 | 0 → 0 |

## 3. G-DRIFT (rule 29(b))

- **Keeper pin → `d9668d84`:** NEXT-17 §4 and NEXT-18 §3, all INERT.
- **`d9668d84` → this commit:** RESULT §3, 19 commits, all INERT for PJM.
- **Conclusion:** form 4. The keeper's committed bundle is the control, and no control solve is spent.

## 4. Pre-fixed reading (before any number exists)

| id | statement | falsified if |
|---|---|---|
| S1 | Slack + dump ≤ keeper + 0.01 TWh in every year | exceeded |
| S2 | Default-bin cohort within-plant contrast (`_pjmnext25_coal_cohort.within`, on the candidate's unit layer) moves toward real in 2019–2021 | model − real gap not smaller in ≥ 2 of 3 years |
| S3 | Rule 20 / D-2: no coal class > 30 % forced; D-4 introduces no new coal off-window failure | any |
| S4 | 2023–2025 C1/C3 verdicts unchanged (floors there are ≤ 0.44 TWh) | any training-tier cell flips |
| P1 | COAL_BIT 2019 and 2021 move UP (more coal), by 1–6 TWh | down, or > 6 |
| P2 | No failing cell outside COAL_BIT / CC_REGULAR 2019–2022 flips to PASS (no gate rescue is expected) | (informational) |

**Decision rule.**
- **If S1–S4 hold:** recommend promotion on structure (rule 1; owner precedent: *"If structural integrity improves but gates regress that may still be a keeper"*; soco-70 precedent). The recommendation stands even if P1 worsens COAL_BIT.
- **If S4 fails:** do not recommend. Report the training-tier movement for the owner.

## 5. Execution (next session)

- **Shards.** One per year, 2019–2025 (rule 36), pinned to the full SHA of the branch commit that carries the appended artifact. They are produced by `scripts/shard_prompt.py --iso PJM --all-years --sha <SHA> --lane pjm-next-25 --bundle results/calibration/pjmnext16_A_span --note "PJM-NEXT-25 coal coverage rows"`, with no `--set`.
- **Shard setup:** `uv sync`; `hydrate_data --profile pjm`; `fetch_pjm_da_virtuals`; `regenerate_clean --solve-profile PJM` (transfer-interface-limits required).
- **Bundles.** Each shard pushes its full bundle, including `dispatch/` (gitignore negation, plain `git add`), plus `hourly/unit_marginal_<y>.parquet`.
- **Compose and score.**
  - Compose with a copy of `_pjmnext16_compose_span.py` (with the `nyiso_firm_imports` exemption).
  - Score: `calibration_verdict.determine(run_id)`, years 2023–2025, `iso_determination`.
  - Then `legitimacy_diagnostics`.
