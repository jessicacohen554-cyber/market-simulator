# PRECOMMIT — NYISO-NEXT-26: apply the published Zone-K import security cap in every hour — 2026-10-01

Phase 0: `docs/records/nyiso/FINDING-nyiso-next26-li-import-window-phase0-2026-10-01.md`. Fixed before any solve.

**The arm.** One new field, default off, zero free parameters: `nyiso_li_tsl_all_hours`.
`apply_nyiso_li_tsl_import_cap(all_hours=True)` caps `NYC>Long_Island` at the published 940 MW N-1-1
limit in all 8,760 hours instead of HB14-21. The other 16 hours currently read the 1,650 MW Gold-Book seed.
- **Rule 17.** NYISO's DAM binds this constraint set outside HB14-21 in 58–64 % of its binding hours.
- **Rule 14.** A published limit replaces an unverified seed.
- **Rule 13.** NYISO republishes the TSL every capability year.

This is a new cell; nyiso-130/143 never tested the off-window hours.

**Pin.** The `main` commit carrying this PRECOMMIT and the field. It is recorded in every shard prompt and in the RESULT.

## 1. G-DRIFT (form 4: committed bundles are the control; no control solve)

| span | solve-path hunks | class |
|---|---|---|
| keeper `fdc41f36` → `5033ad9a` | classified in PRECOMMIT-nyiso-next25 §1 | INERT |
| `5033ad9a` → main `f43f609b` | `nyiso_gas_daily_print_level` field + `hubs.py` branch | INERT off (NEXT-25 unit test) |
| this PR | the new field (hash-dropped at False), the `all_hours` branch, two call sites passing it, log text | INERT off (`test_all_hours_off_is_byte_identical`) |

Solve surface, `surface_rows("NYISO")`: 228 rows, hash `50e8e6cf8632`, at main and with this PR.

## 2. Legs (rule 36: one year-isolated shard per year, 2021–2025)

- **Arm A** (vs the keeper): `--bundle nyisonext21_span` (`nyisonext21_2021` for 2021),
  `--set nyiso_li_tsl_all_hours=true`. Out-dir `nyisonext26_<y>`.
- **Arm B** (composite, vs NEXT-25 arm A): the same bundles with `--set nyiso_gas_daily_print_level=true`
  `--set nyiso_li_tsl_all_hours=true`. Out-dir `nyisonext26p_<y>`.
  - Its control is the NEXT-25 arm A bundles on PR #6987's branch, which is the keeper recipe plus print-level.
  - B exists so the lever is ready on whichever keeper the owner picks. It is promotable only if #6987 arm A is promoted.

## 3. Gates (each arm vs its control's committed bundles, all five years)

- **G-1 leg acceptance.**
  - `git rev-parse HEAD` = the pin.
  - The leg's `scenario_config` equals the control's, except the arm's flag(s) and keys born since, which sit at their dataclass default.
- **G-2 live.**
  - `NYC>Long_Island` `limit_up` = 940.0 in every hour.
  - Flow ≤ 940 + 1e-3 MW.
  - The hours above 940 in the control are ≥ 900 every year.
- **G-3 conservation.**
  - Per year and zone, P1 demand equals the control's within 0.1 GWh.
  - P1 load-slack (all zones) exceeds the control's by ≤ 1 GWh.
- **G-4 protective.** C6 and C8 PASS, every year.
- **G-5 conduct.**
  - The composed `legitimacy_diagnostics.json` may add no D-4 FAIL row, keyed (year, mechanism, plant), that is absent from the control and carries ≥ 5 GWh.
  - Smaller new rows are listed in the RESULT and do not block on their own (the NEXT-25 threshold).
- **G-6 structure.**
  - Every year, the gap between the model's LI fossil energy and CAMPD gross for the same plants shrinks: |arm − CAMPD| < |control − CAMPD|.
  - The model's LI net AC import moves toward the measured implied import.
  - This tests that the cap moves supply onto LI's own fleet, not somewhere else.

## 4. Promotion rule

**Arm A: promote iff G-1 to G-6 hold in all five years and no year's determination downgrades vs the
keeper.** The basis is structural (rules 17 and 14). If any gate fails or any year downgrades, the run is
registered (rule 15), not promoted, and the owner is asked.

**Arm B:** an owner card. It is promoted only if the owner promotes #6987 arm A and B passes G-1 to G-6
against those bundles.

Reported, not gating: C1, C2, C3a, C3b, C3c per year; Zone K error vs DA by season; the K−J spread;
the C3c tail (100 % of the model's tail is Long Island, nyiso-143).

## 5. Prediction (recorded, not a gate)

- **Zone K error vs DA** moves toward zero in every year, by about half to all of the static bracket (FINDING §5):
  2021 −16.1 → −13…−9 %; 2022–2025 1–3 pts. Winter carries it. Summer moves < 1 pt.
- **ISO C3a** moves < 1 pt each year (K is ~12 % of load). NYC and upstream prices dip slightly.
- **LI fossil** rises by roughly the excess energy: 2021 ≈ +0.5 TWh, other years +0.2–0.3 TWh.
  CT_PEAKER and ST_GAS on LI carry it.
- **C3c** LI tail hours rise. That could push C3c from under- to over-production in one year (reported only).
- **Not closed:** the summer K gap (Y49/Y50 loading at modest net import) and the LI-internal pockets.
