# RESULT — crossover CO2 class-grain repair (FC-4 co2)

**Lane:** crossover-co2-grain-repair (successor of
`docs/handoffs/FINDING-capx-d5-crossover-co2-2026-08-30.md` §5.1) ·
**Date:** 2026-08-30 · **Zero-solve:** yes — no LP was solved, no model input,
rate or curve changed (rule 13: scorer-side only), no backcast surface touched,
no out-of-training year read, freeze posture unchanged. No mechanism tested and
no `ScenarioConfig` field added — no matrix row or cell (rule 28).

---

## 1. What shipped

**Both halves of FINDING §5.1, honestly split by where the data lives:**

1. **Option (a) — the preferred per-generator split — in
   `score_crossover.py::build_gmmodel`**, for every bundle that carries its
   dispatch parquets (all future scoring). (a) was NOT blocked:
   `FleetContext` carries no `plant_code` field, but the canonical unit-id
   parse (`run_calibration_full._plant_codes_from_unit_ids`) recovers the
   code, and the split then runs the keeper's own chain
   (`run_calibration_full._coal_supply_class`: curated ERCOT map → EIA-923
   receipt ranks → EIA-860 retiree fallback → generic `COAL`) — one taxonomy
   chain, no second map (rule 19). This also repairs the spurious ~60 TWh
   phantom C1 fuelmix coal rows at source: the model's coal now lands on the
   bench's `COAL_PRB`/`COAL_LIGNITE`/`COAL_BIT`/`COAL_WC` keys. An
   unresolvable plant stays generic `COAL` — the keeper's own residual
   bucket, so the two lanes remain on one basis.
2. **A zero-solve `--rescore-co2-grain` mode (same file)** for the committed
   bundles, which carry ONLY `crossover_score.json` (dispatch parquets are
   gitignored by design, so (a) cannot re-run on them). It applies the
   FINDING's option-(b) arithmetic from committed artifacts alone: the
   model's unsplit `COAL` family energy (coal-family `model_twh` minus the
   split-rank rows, all committed) valued at the bench's
   actual-coal-CO2-weighted mean coal intensity (full-plant weights,
   `classFull + btmClass`), added to `S = egrid × (1 + forecast_signed)` —
   the committed row's exact identity — then re-banded through
   `calibration_verdict.score_co2` verbatim. T-R8 `--rescore` precedent;
   provenance block `rescore_co2_grain` written into each score.

Plus, from FINDING §2.3 (report-only hygiene, task 5): the capacity-track co2
block now carries an explicit **`actual_basis`** label
(`score_capacity_hindcast.actual_co2_basis`) naming the ERCOT/PJM CAMPD
STATE-SUM footprint (whole-TX ≈ +11 %, PJM states ≈ +54 % vs ISO eGRID) so it
is never again decomposed against the FC-4 eGRID rows in the same file.

And one honesty fix the re-registration surfaced:
`register_hindcast.build_sidecar --preserve-invariants` used to fall through
to a full invariant recompute when no prior sidecar existed — over a
parquet-less committed bundle that emitted 13 vacuous PASS rows (evidence that
is not). It now never recomputes: it reuses the committed block, else omits
the block entirely — the audit-tolerated scoring-only shape
(`check_forecast_invariants.audit_sidecars`).

## 2. Measured vs pre-declared (FINDING §5.2)

FC-4 co2 signed error after the rescore of the four committed bundles
(pre-declared value in parentheses; (b) tolerance ±0.5 pp):

| ISO | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| ERCOT | **−25.2 %** (−25.3) | **−23.2 %** (−23.2) | **+1.3 %** (+1.3) |
| PJM | **−7.4 %** (−7.6) | **−10.3 %** (−10.5) | **−1.1 %** (−1.3) |
| MISO | **+1.2 %** (+1.2) | **−1.8 %** (−1.9) | **+13.4 %** (+13.4) |
| NYISO | **+10.1 %** (+10.1) | **+10.3 %** (+10.3) | **+3.9 %** (+3.9) |

Every cell is within ±0.2 pp of the pre-declared value. The residual ≤0.2 pp
(PJM rows) is the ī_coal weighting: this implementation weights each rank's
intensity by its actual full-plant CO2 (`(classFull+btm)×i`), the FINDING's
family reallocation used a slightly different mean (its stated PJM ī ≈ 1.012
vs 1.0185/1.0107/1.0035 here) — inside its own declared ±0.5 pp band for (b).

**FC-4 verdict outcomes, exactly as pre-declared:** ERCOT co2 2023/24 still
FAIL (>K1.5×10 % — the honest volume gap), 2025 PASS; PJM co2 leaves the FC-4
FAIL set (2023/25 clear, 2024 CAVEAT at |10.3 %|); MISO co2 leaves the FAIL
set (2023/24 clear, 2025 CAVEAT at |13.4 %|); NYISO untouched. FC-4 category
statuses do not flip (the surviving price/volume rows still gate) — the co2
instrument is repaired, the honest misses remain with their owners.

## 3. Hard controls — all pass

Checked semantically on before/after JSON of all four bundles:

- **NYISO no-op:** co2 err/signed/status byte-identical in all three years
  (no coal family, no coal intensity → structural no-op).
- **Grain-reconciled family rows untouched:** `family_volume`
  (gas_twh/coal_twh) deep-equal before/after in every ISO-year, and the flat
  rubric gas_twh/coal_twh/price rows deep-equal.
- **C1 records, price_mean, price_shape, retirements, additions, capacity
  co2 model/actual:** all deep-equal.

Unit tests pin the seam both ways: `tests/scoring/test_score_crossover.py`
(unsplit-COAL fleet vs rank-keyed bench through `build_gmmodel` for ERCOT
p-token and non-ERCOT numeric-head ids; the weighted-intensity helper; the
rescore moving only the co2 seam; the NYISO-shaped no-op) and
`tests/scoring/test_register_hindcast_collision.py` (preserve-invariants
never recomputes over an absent cache).

## 4. Board / registration effects

- `frontend/data/forecast/ff-verdicts.json` re-emitted via the standard
  `scripts/rescore_forecast_verdicts.py --apply`: the 9 verdicts with tracked
  artifacts re-scored at this HEAD. Substantive movement is confined to the
  three coal-ISO t1x detail rows (`ercot-t1x-ffr2a`, `pjm-t1x-ffr2a`,
  `miso-t1x-ffr2a`); the other six (nyiso-t1x incl.) changed provenance
  stamps only. Two side effects of the standard path, noted for the record:
  `nyiso-t1x`/`neiso-t1x` entries are replaced by condensed sidecars and so
  drop their informational `session` field; determinations all stay HOLD.
- The four bundles re-registered through the SINGLE
  `scripts/register_forecast_run.py --bundle … --preserve-invariants` path.
  `nyiso-2023-2027-crossover-capxd10.json` keeps its committed 14-row
  invariant block; the three ffr2a runs gain first-ever hindcast sidecars in
  the scoring-only shape (score, no invariant block — their solve sessions
  never registered one and the parquets are gone). Forecast-namespace
  registry/runs/manifest are regenerated at deploy (gitignored; `--reindex`
  ran locally).
- Rescore sections appended to the four committed crossover reports under
  `docs/hindcast-reports/`.

**Not touched, and why:** the LIVE §2.1b gate keys `ercot-t1x`,
`pjm-2023-2027-crossover-ffr3a3-t1x`, `miso-2023-2027-crossover-ffr3a4-t1x`
still carry the mismeasured co2 rows — their FFR-3A-2/3/4 bundles were never
committed (FINDING §1.1), so no zero-solve re-measure exists for them. The
defect is representation-level and invariant across those re-solves
(agreement ≤2.9 pp with the committed ffr2a artifacts); any future t1x
re-solve scores through the repaired `build_gmmodel` automatically.

## 5. Residual misses stay with their existing owners (FINDING §5.3)

ERCOT's 2023/24 co2 FAILs are its real crossover volume gap (co-moving with
its coal_twh/gas_twh FAIL rows — ERCOT forecast lane); the 2025 coal
over-dispatch (MISO +13.4 % CAVEAT) belongs to the evolved-fleet /
2025-actuals-vintage question; NYISO's +10 % gas over-dispatch is D10's open
item. None was chased here.
