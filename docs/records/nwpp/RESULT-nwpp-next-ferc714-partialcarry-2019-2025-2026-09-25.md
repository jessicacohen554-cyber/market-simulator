# RESULT — NWPP-NEXT: FERC 714 PSEI fill + partial-plant exit carry, 2019–2025 (PROMOTED)

**Run:** `2026-09-25-nwpp-next-ferc714-partial` · **bundle** `results/calibration/nwppnext_span` (on `main` with this PR)
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-nwpp-next-ferc714-partialcarry-2019-2025-2026-09-25.md`
**Solved:** seven year-isolated shards (rule 36), all pinned to `fd35f164a97f74e241ea90daa8fff2ae95135219`. The
parent session ran no LP.
**Promotion:** NWPP keeper #8. The owner asked for a recommended candidate to be promoted, and this one was
recommended. The outgoing keeper `2026-09-24-rnwpp-inputs-span` was pruned (rule 35).

## 1. Determination

**NOT-YET on {fuelmix, dispatch_corr}.** These are the same two failing gates as the keeper, and **no gate
regresses**. Price is UNSCORED (rubric v3.8). C2, C6 and C8 PASS.

| Year | vs keeper |
|---|---|
| 2019 | Every criterion stays PASS. Kennecott is restored and PSEI's 384 missing hours are filled from FERC 714 (+0.0225 TWh demand). |
| **2020** | **New.** C1 passes every class (CC_REGULAR +2.46, COAL_BIT −3.18, COAL_PRB −2.18, CT_PEAKER +1.02 TWh). C2 PASS. C4 PASS (coal r 0.720, gas r 0.848). C8 PASS. |
| 2021, 2022 | Every criterion row identical. |
| 2023, 2024 | Every criterion row identical. This matches the drift audit, which predicted identical LP arrays for these two years. |
| 2025 | Every criterion row identical. |

**Still failing, unchanged:**
- **C1 CC_REGULAR:** 2022 −11.23 TWh and 2023 −8.32 TWh, against a ±8.00 band. This is the FINDING-nwpp-45 §8
  demand-basis gap, and it is waiting on an **owner decision**.
- **C4 coal r:** 0.671 / 0.622 / 0.687 in 2023–2025.

## 2. Why it is the keeper (rule 1)

The run carries more correct structure than the keeper and regresses nothing:
- PSEI demand now comes from a **measured** source, FERC 714, instead of straight lines drawn through holes of up to
  8,659 hours.
- Partial-plant exits are carried. Centralia 1 and Colstrip 1–2 are back in 2020, and Kennecott is back in 2019.
- The ISO's year set grows from six years to **seven**.
- There are **zero new free parameters**: the lag and scale of the FERC reconciliation are measured from the data.

## 3. Retrievability (rule 34(e))

- **The composed keeper bundle** `results/calibration/nwppnext_span` lands on `main` with this PR, together with its
  registry sidecar, run payload and bench parts.
- **The per-year legs** `results/calibration/nwppnext_20YY/` are gitignored and stay off `main` (rule 32(d)).
- **Shard branches** `claude/nwppnext-{2019..2025}` are provenance only (rule 33(d)): their SHAs are recorded in
  `.gitignore`. Any leg not on `main` would cost a re-solve of about 4–5 minutes of LP.
- **The shards are archived.**

## 4. Also in this lane (zero LP)

- **The pool gap guard, with tests.** Pool frames for 2021–2025 are byte-identical. The pre-guard code had
  fabricated PSEI's 2020 demand, understating the pool by **11.13 TWh**.
- **CROHMS still serves 2019–2022.** The cascade builders hard-code 2023–2025 (`build_nwpp_hydro_budget.py:86`,
  `build_nwpp_hydro_cascade.py:156/175`); that is the next intake.
- **Unrepaired defect in a keeper year:** EIA-930 PSEI demand for 2021-08-02 → 08-15 sits 1,699 MW below FERC 714,
  about 0.573 TWh. No value is missing, so the guard does not catch it.
- **Shard-prompt lesson:** the offer-curve fingerprint and the `hydro_backfill_year` check both needed correcting.
  - The COAL-SUB translation drops the bare `COAL` key. The accepted fingerprint is `6a13731e…`, which is an
    identity with the keeper curve.
  - `hydro_backfill_year` is recorded in `meta.json`, not in `run_config`.
