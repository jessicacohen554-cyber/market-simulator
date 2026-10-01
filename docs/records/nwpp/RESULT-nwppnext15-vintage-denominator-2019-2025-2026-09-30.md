# RESULT — NWPP-NEXT-15: vintage denominator + Clark CC floor, 2019–2025 (solved; NOT promoted)

Arm and prediction: `PRECOMMIT-nwppnext14-vintage-denominator-2019-2025-2026-09-30.md`. The arm was solved as written
at pin `b4e567fb`: seven year-isolated shards, composed into `nwppnext14vd_span`.

## Outcome

Two NEXT-14 sessions ran the same handoff.

- **The other session (PR #6951) merged first.** Its keeper #19 `2026-09-30-nwppnext14-clark-hr-bridger` is on `main`:
  keeper #18 + `eia923_cc_family_heat_rates` + `campd_unit_fuel_split` (per-unit). That PR also **deleted
  `cc_subfloor_eia923_heat_rates`** (rule 19: duplicate Clark fix; owner card "Keep #19; retire dup Clark field").
- **This session's run** (`2026-09-30-nwppnext15-vintage-denominator-cc`) was registered and promoted on this branch,
  then **withdrawn before merge**. Owner, 2026-10-01: "Is yours better than theirs or should they be combined? … If
  yours is better then you supersede with promote." The comparison below says it is **not better enough to supersede**,
  and the two Bridger fixes are alternatives, not additions (the selector refuses arming both). So **NEXT-16 solves the
  COMBINED run** — main's #19 with `campd_unit_fuel_split` → false and `campd_per_unit_vintage_denominator` → true — on
  pin, as the new keeper candidate.
- **Not on `main`:** the run's registry sidecar, run payload and bundle. **Every number this lane cites is in this
  doc** (rules 15, 29(c)).

## Head-to-head: this run vs main keeper #19 (same scorer, rubric v3.13)

- **Determination:** NOT-YET in both, on the same single record, C4 coal 2023 r **0.670** (NRMSE 0.317 main vs 0.313
  here).
- **Status:** 0 records differ in status.

**C4, r (main #19 → this run):**

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| coal | 0.728 → 0.721 | 0.764 → 0.764 | 0.763 → 0.764 | 0.719 → 0.712 | 0.670 → 0.670 | 0.745 → 0.741 | 0.712 → 0.716 |
| gas | 0.733 → 0.731 | 0.811 → 0.813 | 0.848 → 0.848 | 0.871 → 0.864 | 0.780 → 0.781 | 0.896 → 0.894 | 0.853 → 0.851 |

This run's r is higher in 4 records and lower in 7, and every difference is 0.007 or less.

**C1 fuel-mix |model − actual|:** this run is closer in 25 records and farther in 11. The largest moves:

| record | main → here | actual |
|---|---|---|
| COAL_BIT 2023 error | 5.20 → 4.82 | |
| COAL_BIT 2024 error | 0.82 → 1.30 | |
| CC_REGULAR 2024 error | 6.27 → 6.60 | |
| CC_REGULAR 2025 error | 7.47 → 7.18 | |
| CT_PEAKER 2025 | 8.06 → 8.30 | 5.24 |

**Structure:**

- **Clark fix:** equivalent. The same EIA-923 CC rate gives Clark CC 0.41–1.21 (main) vs 0.42–1.24 TWh/yr (here),
  against 0.43–0.86 actual.
- **Bridger fix:** differs. Main's fuel split repairs Jim Bridger's coal row only. The vintage denominator repairs
  Bridger **and North Valmy** (must-run 212.45 → 127.89 MW; two units sitting over one unit's nameplate in 2023–24), plus
  small committed-tranche moves at Evander Andrews, Langley Gulch and Bennett Mountain.

**Clark 2322 CC_REGULAR (TWh), this run:**

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| this run | 0.62 | 1.24 | 0.58 | 0.46 | 0.42 | 1.16 | 0.51 |
| EIA-923 CC family | 0.45 | 0.56 | 0.70 | 0.77 | 0.43 | 0.86 | 0.67 |

## Caveats

- **Off-pin solve (owner card 2026-10-01: "Merge now, fix recipe").** The shards ran `pip install -e .`, so they solved
  on highspy 1.15.1 / pandas 3.0.6 / pyarrow 25.0.1 / pydantic 2.13.5 against the pinned 1.14.0 / 3.0.3 / 24.0.0 /
  2.13.4. Main's #19 and today's NYISO keeper carry the same drift. The size of the effect is unmeasured. NEXT-16 solves
  on pin.
- **Bytes.** The composite and the per-year legs are gitignored on this container. Leg provenance (rule 33 d): 2019
  `af7166f6`, 2020 `08349d20`, 2021 `84d73b27`, 2022 `89e5aeda`, 2023 `469d0b60`, 2024 `b4986489`, 2025 `04125b17`.
  Reproducing this run would need a re-solve, and it can no longer be re-solved as-is because
  `cc_subfloor_eia923_heat_rates` is deleted. Its Clark effect is reproduced by `eia923_cc_family_heat_rates`, which is
  what the combined run uses.
- **First launch:** the first 7 shards were archived about 3 minutes in, before any solve, because their branch names
  collided with PR #6932's legs. They were relaunched on `claude/nwppnext15-<Y>`.
- **PR #6932 comparison** (before #6951 merged): its 7 legs composed, class energy only. The local registration the
  scorer needs was refused by the permission classifier. #6951 later registered that run on `main`, and it is the
  "main #19" scored above.
