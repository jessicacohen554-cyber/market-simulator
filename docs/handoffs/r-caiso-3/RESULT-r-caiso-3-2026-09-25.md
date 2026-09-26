# RESULT — R-CAISO-3: Pastoria and the winter over-import (2026-09-25)

PRECOMMIT: `PRECOMMIT-r-caiso-3-2026-09-25.md` (§1–§6 before wave 1 at `66d96772`; §7 before wave 2 at `d666fd94`).
The parent spent zero LP: 9 shards, one per year per arm (rule 36), all archived after their bytes were
pulled and verified.

## Headline

**Candidate `2026-09-25-caiso-r3-abc-import` (bundle `rcaiso3_ABC_span`, 2022–2025) — DETERMINATION
CALIBRATED.** It carries all three repairs. C1 18/18; C2 / C3a / C3b / C4 / C6 / C8 PASS; the same single
ledgered C3c 2024. DOF ledger 9/6 unchanged, offer curves unchanged, no `authorized_price_tuning` block.
**Not promoted. The owner rules (rule 31).**

| | keeper `r2-cc-gross` | A only (probe) | **ABC (candidate)** |
|---|---|---|---|
| C1 CC_REGULAR 2022 / 2023 / 2024 (TWh) | +0.64 / **−5.14** / −0.89 | +2.06 / −3.94 / −0.80 | +2.45 / **+1.60** / −0.50 |
| C1 CT_PEAKER 2022 / 2023 / 2024 | −1.48 / −1.79 / −2.30 | −1.27 / −1.76 / −2.29 | −1.27 / −1.53 / −2.32 |
| C3a mean LMP vs RT 2022 / 23 / 24 / 25 | +7.1 / +4.2 / +7.2 / +9.0 % | +9.0 / +5.3 / +7.3 / +9.1 % | +8.7 / **+9.7** / +7.0 / +8.6 % |
| C3b NRMSE 2022 / 23 / 24 / 25 | 0.090 / 0.083 / 0.129 / 0.115 | 0.111 / 0.089 / 0.130 / 0.115 | 0.108 / **0.162** / 0.128 / 0.112 |
| C4 gas NRMSE 2022 / 23 / 24 / 25 | 0.268 / **0.298** / 0.260 / 0.298 | 0.264 / 0.288 / 0.259 / 0.297 | 0.265 / **0.255** / 0.260 / 0.299 |
| Determination | CALIBRATED | CALIBRATED | CALIBRATED |

**What moves, stated plainly.** The keeper's two thin margins widen: C1 2023 goes from 0.13 TWh of margin to
3.67, and C4 2023 from 0.002 to 0.045. The new thin margins are C3a 2023 (+9.7 % against 10 %) and
C4 2025 (0.299, unchanged). C3b 2023 doubles but stays inside its band. Both moves are reported at full
magnitude. None of them was a criterion for choosing any arm (rule 1).

D-rows: D-1 fails on ST_GAS 2024/2025 (immaterial) and D-4 fails on CHP conduct rows. Both **fail
identically on the keeper**, so they are pre-existing and not introduced here.

## Object 1 — Pastoria: a CEMS heat-input bias, repaired by lever C

EIA-923's own fuel filing gives Pastoria **7.04–7.08 MMBtu/MWh** in every year 2019–2025. CEMS heat input
reads ×1.09 of that fuel from 2020 on, and eGRID (CEMS heat input ÷ EIA-923 net) inherits the bias as 7.69.
High Desert, on the same Kern River supply, agrees with its EIA-923 fuel to 0.1 %.

With the identity fallback applied, Pastoria dispatches as follows (TWh):

| year | keeper | ABC | actual |
|---|--:|--:|--:|
| 2022 | 1.84 | **3.39** | 3.29 |
| 2023 | 1.81 | **3.58** | 4.34 |
| 2024 | 1.64 | **2.37** | 4.01 |
| 2025 | 1.36 | **2.14** | 3.62 |

The 2024/25 gap that remains is Pastoria's own residual. It is not absorbed here.

## Object 2 — the winter over-import: repairs A and B

- **A (coupling ladder-only).** This removes a −$81/−121 per MWh (Dec 2022) and −$77/−115 (Jan 2023)
  stacking on measured-hub DSW gas tranches. Its annual effect is small outside 2022–23:
  CC_REGULAR +1.42 / +1.20 / +0.09 / +0.05 TWh.
- **B (gap fill on measured regional gas).** This is attributed from AB-2023 − A-2023: CC_REGULAR
  **+5.28 TWh**, imports **−5.60 TWh**. January 2023 imports go 5.27 → 2.30 TWh and February
  3.73 → 1.92 TWh. B is inert in 2022, 2024 and 2025 by construction.
- **2023 net imports**, ABC: the keeper's 39.0 TWh falls by 7.1 to about 31.9, against 28.9 actual.

**Still open, not absorbed:**

- the Dec 23–31 2022 envelope binding (caiso-279);
- the static DSW_solar_PV block's negative Dec/Jan coupling (a self-scheduled firm floor);
- the N3050CA3 Dec-2022 in-state gas level (11.42 vs N3045CA 27.7 $/MMBtu).

## Retrievability (rules 33/34)

- **On this branch, and on `main` when the PR merges:** the `rcaiso3_ABC_span` and `rcaiso3_A_span`
  composites (slim set + hourly + attestation + diagnostics), their sidecars and payloads.
- **Per-year legs:** gitignored in the parent and kept on local disk, which will not survive the session.
  - Shard commits are listed for provenance only: A `f253364a` / `c2a3af99` / `f3f7995e` / `a2084569`;
    AB-2023 `739e0ee9`; ABC `418c1f35` / `6b5a8193` / `1dd1388f` / `97d924b3`.
  - Re-solving any leg costs about 22 min.
  - These shard branches are the owner's to delete; this session cannot remove refs.

## Owed / asked

1. **Promotion (rule 31).** Promote `2026-09-25-caiso-r3-abc-import`? The recommendation is **yes, on
   structure**. Three measured-input repairs, each identified without reading the residual, close the two
   standing objects. The determination stays CALIBRATED, and C3a 2023 is the new thin margin. The owner
   may also choose A alone (`2026-09-25-caiso-r3-coupling-ladder`). Whichever is not promoted gets pruned
   at the promotion (rule 35).
2. **Task A, 2019–2021 (unchanged, still owed).** Choose (a), the EIA-930-basis guard for 2019–21, or (b),
   re-deriving the fold-in for all years. See `INTAKE-i-caiso-2019-2021-2026-09-24.md` §1.
3. **Routed (rule 25).** Each other ISO's CC artifact inherits the same CEMS-heat-input basis, and its
   gross < net rows are routed to its own lane.

## PROMOTED 2026-09-26

The owner's instruction was "Is this a recommended keeper candidate? If so plz promote". The session
recommended it, and it is promoted: `2026-09-25-caiso-r3-abc-import` is the CAISO keeper.

- **Re-keyed:** `keepers/CAISO.json`, `calibration-complete.json` `complete.CAISO`, and the
  `program-status.json` gate-(a) row. The matrix shard stamp and the §5.2 header are updated, and both
  new cells are now **K**. `status/CAISO.js` is rebuilt and reads CALIBRATED.
- **Pruned (rule 35):** the outgoing keeper `2026-09-25-caiso-r2-cc-gross` (bundle `rcaiso2_ccid_span`)
  and the A-only probe `2026-09-25-caiso-r3-coupling-ladder` (bundle `rcaiso3_A_span`).
  - The year set is unchanged at 2022–2025.
  - `audit_keepers` passes with E13 clean, and `check_promotion_completeness` is OK on (a) through (d).
  - Git history is the record; the A-only numbers remain in the table above.
