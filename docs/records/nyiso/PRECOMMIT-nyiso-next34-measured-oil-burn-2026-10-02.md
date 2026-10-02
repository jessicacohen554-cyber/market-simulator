# PRECOMMIT — NYISO-NEXT-34: price NYISO gas units at their measured plant-day oil burn — 2026-10-02

Phase 0: `docs/records/nyiso/FINDING-nyiso-next34-feb2023-oilburn-phase0-2026-10-02.md`. Fixed before any solve.

**The arm.** `--set dual_fuel_measured_oil_burn=true` on the keeper recipe. There is no new field and no new
code on the solve path. The input is NYISO's own CAMPD plant-day oil share
(`data/raw/_processed-legacy/campd_measured_oil_burn_days_NYISO.csv`, produced by
`derive_measured_oil_burn_days.py --iso NYISO`, zero parameters). On a covered plant-day a gas unit is
priced at `f·oil + (1 − f)·gas` in place of the parity cap (rule 19). The mechanism is backcast-only and already
admitted under rule 13 (soco-96). Zero DOF.

**Pin.** The `main` commit carrying this PRECOMMIT and the artifact. It is recorded in every shard prompt and in the RESULT.

## 1. G-DRIFT (keeper legs `4213945e` → main `e7986d4a`; no control solve)

`scripts/probes/nyisonext32_gdrift_ast.py`: 4 added, 10 code, 1 identical-AST.

| hunk | class |
|---|---|
| `results/scarcity.py`, `reserves/spec.py` (ERCOT ORDC published curve), new `ercot_ordc_published_curve` field | INERT: ERCOT-gated; field default off |
| `lp/costs.py` ORDC `(n, T)` penalty shape | INERT: the static `(n,)` path broadcasts identically |
| `interchange/spec.py` NWPP `IMPORT_ZONE`/`IMPORT_EFORD`, SOCO `hr_by_year`; `run_year` `require_priced_interchange_rows` | INERT: NWPP/SOCO entries; a guard that raises only on an empty priced spec (NYISO's is not) |
| `fleet/campd_bins.py` per-unit fuel-split deletion | INERT: raises only under `campd_unit_fuel_split` + per-unit attribution (not in the recipe) |
| `run_calibration_full.py`, `scripts/lib/*` (unit_marginal writer, CAISO libs) | INERT: output-only / other ISO |

Solve surface `surface_rows("NYISO")`: 228 rows, hash `50e8e6cf8632`, at `4213945e` and `e7986d4a`. They are byte-identical.

## 2. Legs (rule 36: one year-isolated shard per year, 2021–2025)

The keeper recipe: `--bundle nyisonext26p_span` (`nyisonext26p_2021` for 2021), `--set dual_fuel_measured_oil_burn=true`.
Out-dir `nyisonext34_<y>`. The control is the keeper's committed bundles.

## 3. Gates (arm vs keeper, all five years)

- **G-1 leg acceptance.**
  - `git rev-parse HEAD` = the pin.
  - The leg's `scenario_config` equals the keeper's, except `dual_fuel_measured_oil_burn` and keys born since, which sit at their default.
- **G-2 live.** The leg's log reports the measured oil-burn writer active (generator-hours > 0) in every year.
- **G-3 conservation.**
  - Per year and zone, P1 demand equals the keeper's within 0.1 GWh.
  - P1 load-slack exceeds the keeper's by ≤ 1 GWh.
- **G-4 protective.** C6 and C8 PASS, every year.
- **G-5 conduct.**
  - No new D-4 FAIL row keyed (year, check, floor, plant) that carries ≥ 5 GWh.
  - Smaller new rows are listed, not blocking (the NEXT-25/26 threshold).
- **G-6 object.** Both must hold:
  - (a) Feb 2023 system load-weighted P1 vs RT: |error| falls below the keeper's 9.7 %.
  - (b) Σ|daily err| vs RT on the off-cap high-oil days (fleet oil share ≥ 0.10, keeper cap not binding; FINDING §2)
    falls in ≥ 4 of 5 years.
- **G-7 no collateral.**
  - C3a stays within ±10 % in every year. **C3a 2025 ≥ −9.6 %** (no erosion of the 0.4-pt margin).
  - C3b NRMSE rises by ≤ 0.02 in every year.
  - C1, C2 and C4 statuses do not downgrade in any year.

## 4. Promotion rule

**Recommend promotion iff G-1 to G-7 hold and the ISO determination stays CALIBRATED** (every registered year,
worst-of, rule 30). The keeper changes on the owner's decision card, not on this session's say-so. If any gate fails,
the run is registered as a probe (rule 15) and recorded; the bundles are kept until the owner rules (rule 31), and
the cell is set to the verdict the gates read.

Reported, not gating: C3c per year; the cap-binding high-oil days (FINDING §3 expects them to worsen); the
Oct 2023 test-burn days; zone errors for Capital_Hudson / Long_Island / NYC on Feb 3–4 2023.

## 5. Prediction (recorded, not a gate)

- The FINDING `lo` bracket: C3a 2021..2025 ≈ +6.2 / +1.2 / +3.9 / −1.3 / −6.3 (probe weighting, ±0.6 pt vs the scorer).
- Feb 2023 moves to roughly −2…+3 %.
- 2025 cap-binding days worsen (Σ|err| ≈ +150). C3b 2024 is the closest call (+0.008 in the bracket).
- C1 moves < 0.2 TWh per class: the arm is objective-only and moves dispatch only where oil-priced units leave merit.
