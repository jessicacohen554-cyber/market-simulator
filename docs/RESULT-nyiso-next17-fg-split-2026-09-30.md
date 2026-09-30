# RESULT — NYISO-NEXT-17: the F/G re-partition (`nyiso_fg_split`) — 2026-09-30

- **Session:** NYISO-NEXT-17 (orchestrator; no LP in this container).
- **Pre-registration:** `docs/PRECOMMIT-nyiso-next17-fg-split-2026-09-30.md`, merged in PR #6925 before any shard. Pin `fd1269a703a68c8298beee97f28533ede43c8d79`.
- **Design and phase 0:** `docs/DESIGN-nyiso-next17-fg-split-2026-09-30.md`.
- **Owner card:** "Build design A anyway".
- **Registered (not promoted):**
  - `2026-09-30-nyisonext17-fg-split-span` (2022–2025): **CALIBRATED**, with C3c the lone ledgered caveat.
  - `2026-09-30-nyisonext17-fg-split-2021`: **NOT-YET** (C3a).
- **Verdict under the pre-registered rule: NOT PROMOTABLE.** G-3 fails in 2024 and 2025. G-7 fails in 2021, 2022, 2023 and 2025. The promotion decision is the owner's (rule 31).

## 1. Gates (arm vs the NEXT-16 keeper's committed bundles, form 4)

Record: `results/calibration/_nyisonext17_gates.json`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance | pass | pass | pass | pass | pass |
| **G-2** NYCA demand arm = keeper, GWh | 151,979.89 = | 152,681.67 = | 147,048.85 = | 150,516.66 = | 151,589.75 = |
| **G-3** UW→CH at bound, % h (≥ 1) | 24.3 | 24.0 | 16.4 | **0.91** | **0.55** |
| **G-3** UW→LH flow > 0, % h (≥ 50) | 99.95 | 99.2 | 99.4 | 99.7 | 98.9 |
| **G-4** Upstate_West h ≤ $0 | 0 | 0 | 0 | 0 | 0 |
| **G-5** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| **G-6** P1 slack GWh (keeper) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| **G-7** new D-4 rows | floor × ST_GAS 8006 | bridge × ST_GAS 8906; floor × ST_GAS 8006 | bridge × ST_GAS 8906 | none | bridge × CC_REGULAR 54574 |

- **G-2** holds exactly in every year: Capital_Hudson + Lower_Hudson demand is also equal to 0.01 GWh.
- **G-3 fails in 2024–2025.** With the non-CE paths on their own link, the CE link (UW→CH) binds under 1 % of hours. The new UW→LH link carries the upstate transfer and binds 47–81 % of hours.
- **G-7 fails in four years.**
  - Plant 8006 (Roseton, zone G) now fails D-4 on its reliability-floor limb, which moved with it to Lower_Hudson. Plant 2480 (Danskammer) cleared in 2021.
  - The Astoria (8906) and 54574 bridge rows recur from the NEXT-16 lineage.

## 2. Reported (not gating)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C3a, keeper → arm | +11.1 → +11.0 % | +2.6 → +2.6 % | +5.4 → +5.3 % | −1.1 → −1.2 % | −8.6 → −8.8 % |
| C3b NRMSE, keeper → arm | 0.178 → 0.178 | 0.159 → 0.160 | 0.132 → 0.132 | 0.117 → 0.117 | 0.147 → 0.150 |
| Capital_Hudson LW $: keeper / arm / measured DA (CAPITL) | 43.48 / 43.33 / 44.60 | 83.55 / 82.99 / 94.52 | 34.11 / 34.02 / 36.38 | 38.05 / 37.83 / 38.17 | 62.06 / 61.69 / 65.15 |
| Upstate_West LW $: keeper / arm / measured DA | 41.15 / 41.07 / 28.51 | 78.01 / 77.97 / 55.41 | 32.41 / 32.35 / 26.08 | 35.70 / 35.63 / 33.62 | 57.88 / 57.75 / 55.89 |
| CE-binding hours, Capital − Upstate spread: keeper / arm / measured | 2.11 / 2.16 / 19.12 | 4.66 / 4.64 / 48.03 | 1.77 / 1.80 / 17.73 | 3.74 / 3.74 / 21.42 | 6.09 / 6.02 / 35.94 |

- **The prediction held** (PRECOMMIT §5, DESIGN §2). The split's upstate cut is no tighter than the one-link envelope, so every scored criterion moves by ≤ 0.4 points and no status changes.
- The 2021 C3a over-pricing (+11.0 %) is untouched. The Capital − Upstate spread in CE-binding hours stays at $2–6 against a measured $18–48.
- **What this rules out:** splitting F from G does not create the E → F price step. Upstate_West still has a slack path east through G (the non-CE TOTAL EAST paths at their p90), so it never separates.

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `53e240a65ff60c837c92d43383e8239485e8893b` | 17 |
| 2022 | `5faec6e4c37cddb82a048060131dbdcebf31af4c` | 17 |
| 2023 | `1ad333b364acb2d6bbcd5b9ec51bbd37e5c003de` | 17 |
| 2024 | `5af0e1b11cf19996fbae40eb28aa650cf293c42f` | 17 |
| 2025 | `c09e1194c827aea919afeaa7fe1b2f551ebfde38` | 17 |

- **Composition:** zero LP. The span's shared benchmark inputs were rebuilt to the four-year frames, and they hash-equal the keeper's exactly.
- **Retrievability:** the registered span and 2021 bundles land on `main` with this PR. The 2022–2025 legs are gitignored (rule 32 (d)). A leg not on `main` costs a re-solve (~6 min of LP per year).
- **Benchmark parts:** the per-year `bench/NYISO/<y>.json.gz` re-render only relabels seven zone-G plants' `zone` to Lower_Hudson. It was **not** committed, so the incumbent keeper's view is unchanged. A promotion would commit it.
