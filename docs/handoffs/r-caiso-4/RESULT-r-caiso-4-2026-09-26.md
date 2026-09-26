# RESULT — R-CAISO-4: DAM-print intertie gap fill (D) + EIA-923-identity CC CO2 basis (E) (2026-09-26)

PRECOMMIT: `PRECOMMIT-r-caiso-4-2026-09-26.md`, written before any shard at `9a1980bc`. The parent spent zero LP:
5 shards, one per year per arm (rule 36), all archived after their bytes were pulled and verified.

## Headline

**Candidate `2026-09-26-caiso-r4-dam-gapfill` (bundle `rcaiso4_DE_span`, 2022–2025, D+E) — DETERMINATION
NOT-YET.**

- The ONLY failure is C4 2025 gas NRMSE **0.301 against ≤ 0.30** (the keeper reads 0.299).
- Every other criterion passes, and the load-bearing margins widen.
- The DOF ledger stays 9/6, offer curves are unchanged, and there is no `authorized_price_tuning` block.
- **Not promoted.** Promoting a NOT-YET keeper would withdraw CAISO's `complete` marker (the 2026-08-06
  precedent and the D-5(b) re-key policy), which also turns forecast gate (a) red. That is the owner's call, not
  this session's.

| | keeper `r3-abc-import` | **DE (candidate)** |
|---|---|---|
| C1 CC_REGULAR 2022 / 2023 / 2024 (TWh) | +2.45 / +1.60 / −0.50 | +2.45 / **−0.21** / **−0.06** |
| C1 CT_PEAKER 2022 / 2023 / 2024 | −1.27 / −1.53 / −2.32 | −1.27 / −1.68 / −2.36 |
| C3a mean LMP vs RT 2022 / 23 / 24 / 25 | +8.7 / **+9.7** / +7.0 / +8.6 % | +8.7 / **+6.9** / +6.4 / +8.2 % |
| C3b NRMSE 2022 / 23 / 24 / 25 | 0.108 / 0.162 / 0.128 / 0.112 | 0.108 / **0.113** / 0.124 / 0.109 |
| C3c >$200 h 2023 (actual 47) / 2024 (actual 35) | 82 / 0 (ledgered) | **55** / 0 (ledgered) |
| C4 gas NRMSE 2022 / 23 / 24 / 25 | 0.265 / 0.255 / 0.260 / **0.299** | 0.265 / 0.250 / 0.261 / **0.301 FAIL** |
| C8 CC_REGULAR forced 2023 / 2024 | 5.2 / 6.2 % | 6.0 / 6.0 % |
| Determination | CALIBRATED | **NOT-YET (C4 2025)** |

D-rows (D-1 ST_GAS, D-4 chp_steam) fail identically on the keeper, so they are pre-existing.

## Object 1 — Pastoria (lever E)

The CO2 rate on the EIA-923 fuel basis takes Pastoria's committed mc below High Desert's, as its heat rate says
it should be. Pastoria dispatch in TWh:

| year | keeper | DE | EIA-923 actual |
|---|--:|--:|--:|
| 2022 | 3.39 | 3.39 (E inert: no v2 rows) | 3.29 |
| 2023 | 3.58 | **4.51** | 4.34 |
| 2024 | 2.37 | **3.67** | 4.01 |
| 2025 | 2.14 | **3.15** | 3.62 |

High Desert goes 4.14 / 3.88 / 3.40 → 3.84 / 3.69 / 3.27 in 2023 / 2024 / 2025, against 4.08 / 4.60 / 3.33.

E-only 2023 (the attribution leg) shows CC_REGULAR +0.16 TWh and imports −0.13 against the keeper. E mostly
reshuffles plants within CC. In 2025 that reshuffle is what moves C4 from 0.299 to 0.301: the error is 98 %
diurnal shape (§3 of the PRECOMMIT), and E moves energy toward a plant whose hourly profile the model does not
yet shape better.

## Object 2 — the Jan–Feb 2023 intertie gap (lever D)

The measured DAM prints replace B's formula in 1,488 gap hours. Attribution is DE-2023 − E-2023:

| 2023 | keeper | E-only | DE |
|---|--:|--:|--:|
| CC_REGULAR TWh | 53.46 | 53.62 | **51.65** |
| imports Jan / Feb (TWh) | 2.30 / 1.91 | 2.30 / 1.90 | **3.81 / 2.97** |
| load-weighted price Jan / Feb ($/MWh) | 152.9 / 78.1 | 152.8 / 78.0 | **143.3 / 71.1** (RT 129.7 / 66.4) |

So D is −1.97 TWh CC_REGULAR and +2.18 TWh imports in 2023. It moves C3a 2023 from +9.7 % to +6.9 %, C3b 2023
from 0.162 to 0.113, and C3c 2023 from 82 h to 55 h (actual 47 h). **D is inert in 2022, 2024 and 2025 by
construction**, and DE-2022 reproduces the keeper's 2022 to 0.000 TWh in every class (G-REPRO).

## Stop gates (PRECOMMIT §7)

- **G-IDENT PASS.** Each leg differs from the keeper only in the declared flags plus the new default-off
  fields recorded as False.
- **G-FOOT PASS.** Zero-LP, before the solve.
- **G-LIVE PASS.** Pastoria mc < High Desert mc in 2023–25, and the January DSW hub is on the prints.
- **G-REPRO PASS.** 2022 Δ = 0.000 TWh.
- **Not-a-keeper trigger:** none of the load-bearing criteria regress, but **C4 (supporting) FAILs in 2025 by
  0.002.** That is not a listed not-a-keeper trigger, but it changes the determination.

## Retrievability (rules 33/34)

- **On this branch, and on `main` when the PR merges:** the `rcaiso4_DE_span` composite (slim set + hourly +
  attestation + diagnostics), its sidecar and its payload.
- **Per-year legs:** gitignored in the parent, on local disk only.
  - Shard commits for provenance: DE `846d2de8` / `3affb7ae` / `36566c27` / `9dcaefc0`; E-2023 `8fa07fa6`.
  - Re-solving any leg costs about 20 min.
  - The shard branches are the owner's to delete; this session cannot delete refs.
