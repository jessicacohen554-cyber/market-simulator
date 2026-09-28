# RESULT — R-CAISO-10: RA bridge `startup_aware` screen disarmed; PROMOTED (2026-09-28)

**PROMOTED `2026-09-28-caiso-r10-nosa`** (bundle `rcaiso10_A_span`, 2022–2025), CALIBRATED. The standing
direction is "promote if a good candidate"; the promotion rule was fixed in PRECOMMIT §5 before any solve.

- Fold: `2026-09-28-caiso-r10-nosa-fold` (bundle `rcaiso10_A_tp_2019_2021`), stamped to the keeper. It is
  NOT-YET and reported only (rule 30(c)).
- Pruned per rule 35(a): `2026-09-28-caiso-r9-sd-floor` and `2026-09-28-caiso-r9-fold`.
  - Year union before the prune: 2019–2025. The incoming keeper plus its fold cover all of it (35(b)/(c)).
- `audit_keepers.py --iso CAISO`:
  - E1 PASS before the prune;
  - PASS (0 failures) after the prune.
- Complete marker re-keyed (`rekeyed_2026_09_28_rcaiso10`). The matrix shard and the §5.2 header are
  re-stamped.

## Object 1 — the C4 2025 midday CC deficit (zero LP first, then the arm)

**Census** (`scripts/probes/_rcaiso10_object1_census.py` → `results/calibration/_rcaiso10/object1_census.json`).
It covers midday (h9–16) CC_REGULAR plant-hours that CEMS shows on and the model has off.

| year | CEMS-on / model-off MW | model ran before AND after (unfloored gap) | of which CEMS on 24 h |
|---|--:|--:|--:|
| 2022 | 605 | 527 (87 %) | 436 |
| 2023 | 942 | 781 (83 %) | 701 |
| 2024 | 1,164 | 1,009 (87 %) | 882 |
| 2025 | 946 | 781 (83 %) | 721 |

- Outages explain none of it (UNAVAIL = 0).
- caiso-287/292 had traced the missing floor to the `startup_aware` run screen. Its anchor test prices each
  P0 run off the model's own P0 duals.
- **Owner decision card:** "Test disarm, 7 shards".

**A/B:** keeper recipe + `caiso_ra_bridge_startup_aware=false`, one shard per year (rule 36).

- G-DRIFT `980f2ed6 → a6ac7dcf`: one docstring hunk on the SPP branch, INERT.
- Span 2022–25 (keeper → arm):

| | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| C4 gas NRMSE | 0.263 → 0.262 | 0.250 → 0.247 | 0.260 → 0.254 | **0.299 → 0.294** |
| C3a mean price, $/MWh (actual) | 91.96 → 91.81 (84.49) | 58.02 → 57.63 (54.17) | 36.93 → 36.41 (34.65) | 37.43 → 36.79 (34.42) |
| C3b shape | 0.110 → 0.108 | 0.114 → 0.107 | 0.125 → 0.111 | 0.112 → 0.095 |
| C1 CC_REGULAR TWh (actual) | 53.88 → 54.05 (51.61) | 51.50 → 52.00 (51.84) | 45.79 → 46.69 (45.99) | 38.97 → 39.92 (40.0, prelim.) |
| CC_REGULAR midday MW | +53 | +152 | +278 | +305 |
| RA floor midday MW | 837 → 921 | 795 → 999 | 751 → 1,093 | 959 → 1,291 |
| C8 CC_REGULAR forced | 6.8 → 7.8 % | 6.0 → 8.1 % | 6.0 → 9.7 % | 8.5 → 12.4 % |

- Every PRECOMMIT §4 direction held.
- The midday gains stay inside the pre-registered ceilings (275 / 344 / 380 / 534 MW).
- The determination stays **CALIBRATED** with the single ledgered C3c 2024.
- The C8 rise is real forced energy, well under the 30 % cap. The D-2 attribution stays
  `ra_mustoffer_bridge`.

**Fold 2019–21 (reported only):**

- C1 CC_REGULAR moves +0.11 / +0.11 / +0.19 TWh, to +23.0 / +25.2 / +10.6 TWh over actual.
- C3a 2021: 57.25 → 57.13 $/MWh (actual 50.87).
- C3c 2021: 90 → 87 h (actual 27).
- C4 unchanged (0.570 / 0.528 / 0.383).
- C8 CC: 1.5 / 1.3 / 4.9 → 3.3 / 3.0 / 5.8 %.

## Object 2 — 2021 evening price shape (zero LP; `scripts/probes/_rcaiso10_object2_price_setter.py`)

The evening under-price is **not a 2021 object**. In PALOVRDE-printed hours, model SP15_rest h17–22 vs measured
DAM TH_SP15:

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|
| model $/MWh | 69.1 | 109.7 | 57.2 | 43.7 | 43.1 |
| DAM $/MWh | 77.8 | 117.5 | 78.1 | 53.9 | 47.5 |
| hydro sets price | 55 % | 30 % | 48 % | 51 % | 46 % |

- Middays run the other way: 2024 model $23.6 vs DAM $13.0.
- This is the same flat shape the rubric's reported D-A amplitude shows: 70–89 % of measured.
- Model hydro's diurnal shape matches EIA-930 in 2023–25 (evening/mean 1.43 vs 1.41, 1.37 vs 1.36, 1.42 vs 1.42),
  so hydro scheduling is **not** the cause there.
- 2021 over-concentrates evening hydro (1.83 vs 1.62), a partial 2021-only contributor.
- No admissible single-config lever was found, and nothing was armed for it.

## Retrievability (rule 34(e))

- **On `main`:** `rcaiso10_A_span` and `rcaiso10_A_tp_2019_2021` (slim set, hourly sidecars, attestation,
  diagnostics).
- **Local only (gitignored), not recoverable after this session:**
  - the per-year legs;
  - the span's P0 dispatch/prices (`hourly/p0_*`).
  - Any leg not on `main` costs a ~20 min re-solve.
- Provenance only (rule 33(d)):

| year | shard commit |
|---|---|
| 2019 | `1d45e9dd87e072fc2758af9eed20b36472715a6d` |
| 2020 | `3598231f108ae372c969be02dd773862d089ad84` |
| 2021 | `13738fa19a1b99ec726a48e9ce0f8fb8f3f4f0a3` |
| 2022 | `8a16c43d11d1c215824bea220fd0ee390588398d` |
| 2023 | `c6093da37ca9faa8e21a5a915dc0f43120c2ff91` |
| 2024 | `2ec156dc1a3ed17268fd4ff54e2d9b1f9dca1ffe` |
| 2025 | `7f84a4fd9fd9a63aff7ce801340f6493ed64abb9` |

## Leftover branches for the owner to delete

- `claude/r-caiso-9`
- `claude/r-caiso-10-A-2019` … `-A-2025`
- `claude/r-caiso-10` once its PR merges, if the environment does not remove it.
