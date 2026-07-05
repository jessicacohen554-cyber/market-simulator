# CO2 keeper re-gate under the new emission-rate basis — 2026-07-05

**Task:** bring every dashboard keeper's CO2 verdict current under the merged
emissions work (d3077a4 forward estimator, 6ca7247 v2 artifact, **fff2c34 R2
physical-HR CO2 basis**, 968cead quarantine-row strip, R7 NOx unit fix), then
judge keeper status by structural faithfulness (rule #1), flag rather than
silently swap any keeper that no longer qualifies (rule #3), and never touch the
2022 / H1-2026 holdouts (rule #22).

## Headline

**The emissions rate-basis change does not materially move or break any
keeper's CO2 verdict.** R2's isolated effect is **zero** for the three
carbon-zero ISOs and **small** for the three carbon-priced ISOs. No keeper
status change is attributable to the emissions estimator. All six keepers'
committed CO2 verdicts stand under the new basis.

A separate, incidental finding surfaced: **the six keepers (all git-dated
2026-07-03) predate substantial 07-04 ISO-offer merges.** A full HEAD re-solve
therefore moves the CO2 verdict (mostly improving) and, for NYISO, regresses
C1/C7 — but the ablation proves that movement is the 07-04 offer work, **not**
the emissions basis. Those are the owner's re-gate to make deliberately; this
session did **not** swap any keeper.

## Method

- Carbon-zero ISOs (ERCOT/PJM/MISO): `resolve_carbon_price` returns **$0/t** in
  every backcast year, so `emission_rate_co2` never enters `mc` and the CO2
  scorer uses the measured `egrid.fossil_co2_rate_map` (artifact
  `fossil_co2_rates.parquet`, last changed a0faf74 — *before* the emissions
  commits). Re-score = provable no-op.
- Carbon-priced ISOs (CAISO $28-35/t, NYISO $13-22/t, NEISO $15-24/t): carbon
  enters `mc`, so R2 can move the merit order. Re-solved all three, all years
  2023-2025, one bundle per ISO, serial years, via `scripts/replay_keeper.py`
  (byte-faithful replay of the keeper `meta.json` under current code).
- **Ablation twin (rule #25):** re-solved CAISO and NYISO a second time at HEAD
  with the single R2 line reverted (`emission_rate_co2 = get_emission_rate(fuel,
  tr_hr)`, the pre-fff2c34 basis), holding all other current code fixed. The
  edit was temporary and reverted; **not committed.** `resolve − ablation`
  isolates R2; `ablation − keeper` isolates the post-07-03 merges.

## Per-ISO CO2 (model Mt / % vs eGRID)

| ISO | change type | 2023 | 2024 | 2025 | keeper CO2 status → now |
|---|---|---|---|---|---|
| ERCOT | re-score (carbon=0) | −2.1% | −0.7% | −0.9% | PASS → **unchanged** |
| PJM | re-score (carbon=0) | +1.3% | +1.2% | +4.6% | PASS → **unchanged** |
| MISO | re-score (carbon=0) | −2.6% | −3.8% | +3.8% | PASS → **unchanged** |
| CAISO | re-solve (carbon>0) | +0.5→−2.6% | +8.4%**FAIL**→+3.4% | +8.6%**FAIL**→+5.2% | FAIL(24,25) → **all PASS** |
| NYISO | re-solve (carbon>0) | −3.6→−2.3% | −7.2%**CAVEAT**→−6.3% | −6.2→−4.8% | CAVEAT(24) → **all PASS (no caveat)** |
| NEISO | re-solve (carbon>0) | ~−3% | ~−3% | ~+4% | PASS → **unchanged** |

### Attribution (carbon-priced ISOs), model Mt

| | keeper (old code, old basis) | ablation (new code, **old** basis) | resolve (new code, new basis) |
|---|---|---|---|
| CAISO 2024 | 31.24 (FAIL) | 29.45 (PASS) | 29.80 (PASS) |
| CAISO 2025 | 29.44 (FAIL) | 28.33 (PASS) | 28.52 (PASS) |
| NYISO 2024 | 27.17 (CAVEAT) | 27.43 (PASS) | 27.43 (PASS) |

- **CAISO:** the FAIL→PASS is `keeper→ablation` (the 07-04 CAISO offer merges,
  e.g. Lever B firm-import grounding). R2 alone (`ablation→resolve`) is
  **+0.2-0.4 Mt (~+0.5-1%), slightly worse**, still PASS.
- **NYISO:** `ablation ≈ resolve` (R2 effect **<0.1%**). The whole CO2 move is
  the 07-04 NYISO CT-offer grounding (7b891bd) etc.
- **NEISO:** re-solve ≈ keeper on CO2 (R2 ≈ 0); no criterion changed.

## Keeper status

- **No keeper swapped.** The emissions estimator changes no keeper's CO2 verdict
  status. Committed keeper payloads (and their dashboard text) remain truthful;
  `keepers.json` is unchanged.
- **NYISO flag (rule #3):** a HEAD re-gate of nyiso-41 regresses **C1 fuel-mix
  (PASS→FAIL, ST_GAS −3.46 TWh 2024) and C7 diurnal (PASS→FAIL)** because the
  07-04 CT-offer grounding roughly doubles modelled CT_PEAKER energy
  (1.82→4.41 TWh). Confirmed by the ablation (old CO2 basis also FAILs C1/C7), so
  this is **not** the emissions basis. Recommend the owner deliberately re-gate
  NYISO incorporating the 07-04 offer work; do not adopt the confounded HEAD
  re-solve as the keeper.
- **CAISO/NEISO:** likewise stale vs 07-04 merges but no PASS→FAIL regression; a
  clean re-gate is the owner's call.

## Dashboard

Registered as **PROBES** (rule #15; not keeper swaps):
`2026-07-03-caiso51-co2re-probe`, `-nyiso41-co2re-probe`, `-neiso47-co2re-probe`
— each sidecar carries the isolated-R2 attribution. The two ablation-control
bundles used a temporary uncommitted source edit (non-reproducible from HEAD) so
they are **not** registered; their numbers live in this note and the probe
definitions.

## No retune / holdouts

No parameter was tuned to any residual (rule #1/#23). No solve, score, or intake
touched 2022 or H1-2026 (rule #22); `calibration-complete.json` markers remain
empty.
