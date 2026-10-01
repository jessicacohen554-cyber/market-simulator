# FINDING — NEISO & NYISO phantom-outage re-audit (2026-07-19)

**Charter.** ERCOT-79 (2026-07-17) found the CAMPD facility-outage detector
manufactured phantom outages for daily-cycling combined-cycle plants, withdrew
ERCOT's frontier ("we can't have a keeper on inaccurate data"), consolidated the
per-unit detector as the sole outage source repo-wide, and flagged the fix as a
**per-ISO regenerate-and-re-audit lane for all six ISOs**
(`FINDING-ercot79-phantom-outage-2026-07.md`). NEISO's and NYISO's keepers
(`neiso-59`, `nyiso-62`, both 2026-07-13) and their frontier declarations
(2026-07-11) and calibration-complete markers (NEISO 2026-07-07, NYISO
2026-07-13) all **predate** the ERCOT-79 discovery, and their committed
unit-outage extracts (mtime 2026-07-16) predate the detector consolidation
(2026-07-17). This is that re-audit for NEISO and NYISO.

## Method (the PJM-115 protocol)

1. Regenerate each ISO's unit-outage extract on the consolidated detector
   (`scripts/data/derive_campd_unit_outages.py --iso <ISO>`).
2. Install the corrected extract, re-solve the frozen keeper recipe verbatim
   (`scripts/replay_keeper.py`) across 2023–2025, copy the parent bundle's
   `calibration_attestation.json` (same recipe → same ledger), register
   (`dashboard_add_run.py`), and score (`calibration_verdict.py`).
3. Compare model dispatch/price/tail to the committed keeper — inert (PJM-115)
   vs co-dependent (ERCOT-79).

## Data-layer change (both material)

| ISO | Committed extract (07-16) | Corrected extract | Δ |
|-----|--------------------------:|------------------:|---|
| NEISO | 3,892 rows | 1,425 rows | −2,957 dropped (mostly BTM CHP full-year phantom), +490 real |
| NYISO | 1,598 rows | 2,641 rows | +1,056 added, −13 (matches the intake-log-flagged 1,598-vs-2,641 detector-vintage gap) |

## NEISO — HOLDS CALIBRATED on the corrected envelope (PJM-115 pattern)

Re-audit run `2026-07-13-neiso-60-phantom-outage`
(`results/calibration/neiso59_reaudit_corrected_outages`).

**Determination unchanged: CALIBRATED-WITH-CAVEATS** (identical to `neiso-59`).
Every criterion PASS→PASS; C3c ledgered caveat byte-identical (model 0h both).

- **C3a mean LMP inert / improves** (vs DA): 2023 −5.4%→−1.2%, 2024 −4.8%→−1.4%,
  2025 +3.0%→+6.0% — all comfortably in band.
- **Scarcity tail inert**: `ordc` model h>$200 = 0 → 0 in every year.
- **Gen mix inert**: only movers >0.1 TWh are CT_PEAKER (+0.11–0.40 TWh) with a
  compensating CC_REGULAR (−0.34–0.36 TWh) — a small, correct effect from the
  ~490 real CC outage windows the old extract missed (Salem Harbor et al.).

NEISO's keeper does **not** rest on the phantom. Its frontier (2026-07-11) and
calibration-complete marker (2026-07-07) survive the re-audit. `neiso-60` is the
corrected-fleet keeper-in-place candidate (fix-in-place, no re-tune — like
PJM-115).

## NYISO — DOES NOT HOLD (ERCOT-79 pattern)

Re-audit run `2026-07-13-nyiso-63-phantom-outage`
(`results/calibration/nyiso62_reaudit_corrected_outages`).

**Determination flips CALIBRATED-WITH-CAVEATS → NOT-YET**, three load-bearing
criteria fail on the accurate envelope:

| Criterion | `nyiso-62` (stale) | `nyiso-63` (corrected) |
|-----------|-------------------:|-----------------------:|
| C1 fuel-mix | PASS | **FAIL** — 2024 ST_GAS −3.36 TWh (−2.3 pp) |
| C3a mean LMP | PASS | **FAIL** — 2023 +25.0% (DA +22.4%) |
| C3b shape | PASS | **FAIL** — 2023 NRMSE 0.385 |
| C3c tail | CAVEAT (28h) | over-forms — 2023 model 50h vs actual 10h (5.0×) |

Model mean LMP: 2023 $30.6→$47.2 (actual $31 — a **+51% overshoot**), 2024
$18.8→$30.0, 2025 $46.9→$66.4; ST_GAS sheds ~1.1–1.5 TWh/yr into CT_PEAKER/CC in
every year. The corrected extract *adds* real outage capacity-unavailability the
stale detector under-counted; removing that capacity exposes that the `nyiso-62`
keeper's offer curves were **silently compensating for the under-counted
outages** (CLAUDE.md rule 11). The keeper's calibration is co-dependent on the
inaccurate availability envelope — the ERCOT-79 condition exactly.

## Determination & recommended governance actions

- **NEISO — frontier STANDS.** Adopt `neiso-60` as the NEISO keeper-in-place
  (owner-authorized keeper swap; metric-identical, accuracy upgrade).
- **NYISO — frontier + calibration-complete marker should be WITHDRAWN.** By the
  ERCOT-79 precedent ("no keeper on inaccurate data"), NYISO is NOT at frontier
  on the corrected availability envelope. **Do not run the one-shot holdout** —
  the locked test (2019, H1-2026) is touch-once-ever (rule 22); spending it on a
  keeper known to fail three criteria on accurate data would waste it. Open
  successor lane: re-calibrate NYISO's offer curves against the corrected
  outages (keep the accurate input, fix the root cause — rule 11), reproducing
  the full 2023–2025 span (rule 16).
- **Cross-ISO:** the corrected per-ISO extracts (`campd-unit-outages-{NEISO,
  NYISO}.csv`) are the adopted-standard regeneration and are installed. CAISO
  and MISO remain their own regenerate-and-re-audit lanes.

## Reproduce

```
scripts/data/derive_campd_unit_outages.py --iso NEISO   # 1,425 rows
scripts/data/derive_campd_unit_outages.py --iso NYISO   # 2,641 rows
scripts/replay_keeper.py results/calibration/neiso59_cc_hr_regate --out-dir <dir>
scripts/replay_keeper.py results/calibration/nyiso62_cc_hr_regate --out-dir <dir>
scripts/calibration_verdict.py <dir>
```

(NYISO replay requires the derived clean partition
`data/clean/capacity-deliverability/NYISO/` — build with
`PYTHONPATH=. scripts/data/curate_capacity_deliverability.py`; raw data intact,
the clean partition is gitignored and absent on a fresh clone.)
