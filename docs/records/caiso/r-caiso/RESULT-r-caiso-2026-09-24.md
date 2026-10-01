# RESULT — R-CAISO: CAISO 2022–2025 re-solved on corrected backcast inputs (2026-09-24)

Charter: `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.1. Recipe, census and
G-DRIFT fixed ex ante in `PRECOMMIT-r-caiso-2026-09-24.md` (pin `18bb99b1`). Full tables: `_comparison.md`.

## Headline

**Run `2026-09-24-caiso-r-inputs-vintage` (bundle `rcaiso_inputs_span`, 2022–2025) — DETERMINATION NOT-YET,
on ONE row: C1 2023 CC_REGULAR −5.36 TWh against a ±5.27 TWh band** (incumbent −4.40, PASS). Every other
criterion holds in every year: C2, C3a, C3b, C4, C6, C8 PASS; C3c the same single ledgered 2024 caveat. The
incumbent keeper, re-scored on the same HEAD benchmark, stays **CALIBRATED**. So the C1 flip comes from the
re-solve itself, not from the benchmark change.

## What the re-solve changed (inputs; zero LP, `census_caiso.json`)

| | incumbent keeper | R-CAISO |
|---|---|---|
| EIA-860 source | canonical 2025ER + COD ramp, every year | `vintage_2022/23/24`, canonical 2025 |
| thermal MW at the asset-class heat-rate table | 607 / 607 / 655 / 655 MW (2022–25) | **97 / 97 / 145 / 145 MW** — only plants with no eGRID row and no CEMS (Panoche Peaker 55874, Enchanted Rock Lodi 66638, ≤ 4.5 MW behind-the-meter sites) |
| measured heat rates | CT, CHP | CT, CHP **+ ST, CC** (per-year row, else pooled 2019–25) |
| El Segundo 57901 (510 MW CC) | class table | CEMS 8.53 MMBtu/MWh — **derive repaired** to route through `CAMPD_UNIT_PLANT_REMAP` |
| CAMPD outages | std ≥5-day (hour grain) | std **+ 1–5-day gas full stops** (hour grain; F2 file re-derived with `--hour-grain`, base columns identical) |
| offer-curve multipliers | — | **unchanged** (rule 1(c)) |

## Per year, incumbent → re-solve (both on HEAD's benchmark)

| year | C1 CC_REGULAR err (TWh) | C1 CT_PEAKER err | C3a mean LMP vs RT | C3b NRMSE | C4 gas r / NRMSE | C3c h>$200 (actual) |
|---|---|---|---|---|---|---|
| 2022 | +1.25 → **+0.25** | −1.68 → −1.44 | +6.9 % → +7.3 % | 0.089 → 0.092 | 0.889/0.270 → 0.893/0.266 | 483 → 482 (510) |
| 2023 | −4.40 → **−5.36 FAIL** | −2.10 → −1.74 | +3.0 % → +4.4 % | 0.076 → 0.084 | 0.882/0.294 → 0.884/0.297 | 46 → 45 (47) |
| 2024 | −0.43 → −1.24 | −2.73 → −2.22 | +7.3 % → +7.6 % | 0.138 → 0.131 | 0.919/0.254 → 0.916/0.259 | 0 → 0 (35) caveat |
| 2025 | not gated (prelim. EIA-923) | not gated | +7.4 % → +9.4 % | 0.103 → 0.118 | 0.879/0.296 → 0.882/0.295 | 0 → 0 (8) |

Model TWh (P1), re-solve − incumbent:

| class | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| CC_REGULAR | −1.031 | −0.974 | −0.807 | −1.615 |
| import | +0.433 | +0.610 | +0.376 | +1.162 |
| CT_PEAKER | +0.264 | +0.371 | +0.504 | +0.421 |
| CC_CHP | +0.285 | −0.071 | −0.034 | −0.030 |
| CT_CHP | −0.027 | +0.020 | +0.142 | +0.071 |

Diagnostics: D-1 2 fails and D-4 28 fails, **identical** to the incumbent (pre-existing); D-2 PASS; D-5
**improves** 1 fail → 0. C5a CO2 vs eGRID (reported only): 2022 −10.1 %, 2023 −13.0 % (incumbent −10.0 / −12.3).
DOF ledger 9 entries / 6 residual, unchanged; no `authorized_price_tuning` block.

## Root cause of the one failing row (rule 14 — the input stays; the cause is elsewhere)

The CC_REGULAR loss follows the two new measured channels:

1. **Short gas outages** remove 5.26 / 5.26 / 5.81 / 8.05 TWh of CC_REGULAR capability (in-merit MW × h) in
   2022–25; the CC loss scales with it (2025 largest). These windows are CEMS-measured full stops that pass
   the merit-order guard.
2. **Measured CC heat rates** are 0.2–1.0 % above eGRID on a MW-weighted basis (2023 7.537 → 7.610 MMBtu/MWh),
   which lowers CC's merit against the price-taking import stack.

What replaces the lost CC energy is **imports first, CT second**, which is the incumbent's documented standing
residual: CC-side under-dispatch / over-import (caiso-121 surplus-belly, caiso-135 ride-through, caiso-140 §B;
already −4.40 TWh in 2023 before this lane). The correct inputs make that existing gap more visible. The
2023 row crossing its band is evidence for that lane, not a reason to revert the inputs or to re-tune an
offer curve (rules 1, 14).

## Not done, and why

- **2019–2021 not solved** (PRECOMMIT §0). The armed `caiso_supply_consistent_demand` artifact exists only
  for 2022–25, so a run hard-fails. Past that, the CA carbon price would fall silently to $0, EIA-930 hydro is
  missing for months in 2019–20, and nuclear per-unit, intertie hub prices and the 2021 LMP/tail references
  are also missing. **Intake program for the owner** (each zero-LP data work, then 3 shards ≈ 1 h of LP):
  supply-consistent demand 2019–21 (derive + ex-ante guard); CA cap-and-trade auction prices 2019–21 into
  `STATE_CARBON_PRICE_BY_ISO`; a 2019–20 hydro source (CAISO production reports or EIA-923 monthly); nuclear
  per-unit 2019–21 (NRC daily status); the WECC intertie hub series; the 2021 LMP + tail references from the raw
  `lmp-data/CAISO/*_2021.csv`.
- **`caiso_dam_outages` not armed** (PRECOMMIT §4): coverage starts 2022-11-22 on the crosswalked set, and
  the loader does not filter nature of work (16 % ambient-temperature derates double-count
  `temp_dependent_derate`). Needs its own charter.
- Other ISOs' CC artifacts were **not** re-derived through the remap (rule 25); NYISO's Astoria II entry is
  routed to R-NYISO.

## Retrievability (rule 34(e))

The composite `rcaiso_inputs_span` (slim set + attestation + metrics + diagnostics), its registry sidecar, run
payload and CAISO bench parts are committed on `claude/r-caiso-2019-2025-inputs`. They reach `main` only when
that branch merges. The four per-year legs, with full `dispatch/*_P1.parquet`, sit on this session's disk,
gitignored and not deleted (rule 31). Shard commits, as provenance only (rule 33(d)): 2022 `8a431a2d`,
2023 `4b7b7dce`, 2024 `65e6c12c`, 2025 `cbfc33cc`. All four shards are archived. Promoting from the
committed composite costs **zero LP**: a keeper-shard edit plus a prune. The four year-scoped legs are ≈ 25 min
of LP each if they are ever needed again.

## Promotion question (rule 31) — the owner decides

**Recommendation: promote.** The re-solve is the structurally more faithful model. It uses year-correct
fleets, plant-specific heat rates on all but 97–145 MW of thermal, and measured short outages. It adds zero
free parameters and leaves the offer curves unchanged. Its single regression is a known residual that the
correct inputs expose; the inputs did not create it. Promotion changes CAISO's determination
**CALIBRATED → NOT-YET** until the CC-side under-dispatch / over-import lane closes 2023 CC_REGULAR by
≥ 0.09 TWh. The alternative is to keep the incumbent, which is CALIBRATED on inputs the owner has ruled incorrect.
