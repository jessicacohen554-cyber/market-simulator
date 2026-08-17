# FINDING — DEBUG-B(NEISO): the SMD 2018–2023 DST-naive workbook-clock repair

**Date:** 2026-08-17 · **Lane:** DEBUG-B(NEISO) (measured-input repair; audit row **O8**)
· **Session:** neiso-97 · **Branch:** `claude/neiso-smd-dst-naive-repair-8b2eez` (off `origin/main` @ `a4ef2a9`)
**Charter:** `docs/audit/third-party-audit-2026-08.md` §8 row O8 ("Owner: charter the repair"),
served as an in-session owner card per the `debug-sweep-2026-08.md` §A.2 two-card pattern and
**SIGNED 2026-08-17: option A (repair + full-span re-solve) with promotion pre-signed on
not-worse**. Direct precedent: `docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` (the PJM
EIA-930 input-clock repair — same genus, same §2a verification protocol).
**Instruments:** `scripts/probes/neiso97_smd_dst_defect_quantify.py` (Phase-1 quantification +
truth adjudication) and `scripts/probes/neiso97_smd_repair_byteverify.py` (§2a verification),
both committed with their JSON outputs.

---

## Verdict in one line

**The committed NEISO actual-LMP series was displaced by one hour around every DST transition
of 2018–2023 — six fabricated mean cells and one lost hour per year included — and now is
not.** The 2018–2023 SMD workbook vintage is DST-naive (flat 24 rows every day); the repair
re-places each affected cell value-preservingly and takes the twelve defective operating days
from the market's own daily hourly-LMP reports. All §2a checks pass; the C3c $300 tail is
provably untouched; annual means move ≤ $0.008/MWh — this repair cannot buy a score
(rules 13 `[R-MEASURED]` / 14 `[R-ACCURATE]`).

---

## 1. REPRODUCE — the neiso-96 §1.4 finding confirmed, then measured to the cell

neiso-96 (`results/calibration/ASSESSMENT-neiso96-h12026-intake-2026-08-15.md` §1.4) found the
defect on four sampled DST days and deliberately did not repair it in an intake lane. This
session measured the full extent from the committed bytes before serving the owner card.

**Census** (hub sheet; all 9 SMD sheets agree on every DST day):

| year | days at 24 rows | spring day rows (true 23) | fall day rows (true 25) |
|---|---|---|---|
| 2018–2023 | **every day of the year** | **24** | **24** |
| 2024–2025 | 364 / 363 | 23 ✓ | 25 ✓ |

**Mechanism, adjudicated against the market's own published day** (ISO-NE daily hourly-LMP
reports, the route neiso-96 proved equivalent; 5 truth years × 9 sheets × 2 markets,
**0 mismatches** under the winning mapping; the alternative fails ~198 of 198):

* **Spring-forward** (23 real hours, 24 rows): positional row 1 — labeled "02" — is a
  **fabricated entry for the nonexistent hour, the mean of its two neighbours** (exact to the
  cent on every sheet, every truth year: e.g. 2023-03-12 hub DA 27.97 = mean(28.79, 27.14)).
  The true HE02 sits at row 2 mislabeled "03"; every true value from 01:00 on is placed **one
  hour late**, and the day's last hour spills onto the next day's first slot, where
  `_densify_std` folds it with the true value into a second fabricated mean.
* **Fall-back** (25 real hours, 24 rows): the repeated hour's two instances are **collapsed to
  their mean** (2023-11-05 hub DA 18.69 = mean(18.53, 18.84); the neiso-96 2021 example
  reproduces); every later value is placed **one hour early**; the day's true last hour is
  **lost** — the single NaN each of 2018–2023 carries (the 0.9999 coverage of the committed
  parquet).

**Blast radius in `data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet`** (the probe's
committed JSON has the per-year table): **562 hub cells** across 2018–2023 — 46–47 per
market-year, in-sample 2023 included (47 DA + 47 RT) — every one inside the derived mechanism
window (`changed_outside_expected_mechanism` empty in all 24 year×market audits). Max
displacement **$40.17/MWh** (2022 RT); 2023 max $36.98 RT / $20.12 DA. Per year: two
neighbour-mean phantoms, two spill means, two pair means, and one lost hour per market.

**What provably does not move:** no affected cell — committed or corrected — exceeds
**$138.65/MWh**, so the C3c $300 tail counts are untouched by construction
(`derive_actual_tail.py` re-run: `actual_tail.json` byte-unchanged). Annual hub means move
≤ $0.008/MWh.

**Consumers, measured from committed configs, not assumed:**

| consumer | exposure |
|---|---|
| NEISO keeper `2026-08-14-neiso-93-envelope` | **Scoring target only** — its `run_config.json` arms no LMP-consuming flag; dispatch at corrected inputs is expected unchanged, the measurement surface (bench parts, run-payload benchmark, `actual_lmp.json`) moves. |
| NYISO keeper `2026-08-08-nyiso-133-cod-arm` | **Live solve input**: `nyiso_import_hub_prices=True` prices its ISONE_tie tranche off this parquet's DA hub series (`neighbor_price.neighbor_lmp_hourly`). The repair moves 47 of its 2023 input cells (max $20.12); 2024–2025 are byte-identical. **Rule 25 `[R-ISO-SCOPE]`: the NYISO consequence is filed here for the NYISO lane, not acted on** — the analogue of the PJM finding's §6 ≤2022 scope note. |
| 2022 validation touchpoint `2026-08-06-neiso-2022-corrected-basis` | Its record **stands as scored** on the pre-repair instrument (the audit row O3 posture); the next owner-authorized 2022 iteration measures against the corrected one. Its bench part is not regenerated here. |
| clean `lmp` datatype (`curate_lmp.py`) | Same workbooks, label clock — smaller defect surface (phantom curated as HE02, true HE02 shifted onto a nonexistent local time, fall pair-mean at the first instance). Fixed with the same per-day rule; consumer is default-off (`MARKET_SIM_USE_CLEAN`) and `data/clean` is derived-disposable. |

## 2. THE REPAIR

### 2a. Data — value-preserving, per-day, in the deriver (raw workbooks untouched)

One uniform, year-agnostic rule: **a day is taken from a published packaging that can
represent it.**

* `derive_actual_lmp._neiso_sheet_series` is vintage-aware: on a flat-24 spring day it drops
  the neighbour-mean phantom and re-places rows 2..23 at positions 1..22 (recovering **every**
  published hour); on a flat-24 fall day it drops the collapsed pair-mean and re-places rows
  2..23 at positions 3..24. True-shape days keep the positional clock **byte-for-byte**.
* `neiso_zone_hourly` overlays, day-scoped, the twelve defective operating days from the daily
  historical-report route (`smd-zonal-lmp/NEISO_smd_zonal_lmp_<year>.csv`, fetched and
  committed this session) — the only source of the fall-back repeated hour's two true
  instances, which the workbook averaged away.
* **2018-03-11 (spring)**: its RT daily report is a genuine upstream publication stub
  (31 bytes, HTTP 200, reproduced twice). Repaired by pure re-placement of the workbook's own
  rows — spring days lose nothing, so **no boundary value is fabricated anywhere** (the same
  posture as the PJM extension's +8 boundary NaNs, except here nothing is even left NaN).

**Byte-verification** (`neiso97_smd_repair_byteverify.py` — **PASS on every check**, committed
JSON has the full table):

| check | result |
|---|---|
| row grid / dtypes / column order (78,840 rows) | **unchanged** |
| 2024 / 2025 / 2026 year blocks | **byte-identical** |
| changed cells outside the mechanism window (24 year×market audits) | **zero** |
| every displaced cell == pristine value at the defective offset | **holds** (spring 1..21 direct; position 22 + spill via the collision decomposition, since the pristine spill slot stored the two-value mean) |
| fall repeated-hour pair == the market's published instances (float32) | **holds, all 6 years × 2 markets** |
| NaN accounting | exactly **one NaN per market-year filled** with the measured value (coverage 0.9999 → 1.0000); **zero introduced** |

### 2b. Sibling artifacts

* `actual_lmp.json` regenerated + `--lw-retrofit`: **NEISO 2018–2025 entries only**; every
  other ISO's entry and NEISO 2026 are byte-identical. The cent-level 2024/2025 deltas are
  **not** a repair effect: they are the previously-deferred dense-series completeness deltas
  the `--parquet-only` contract postpones "to an authorized JSON re-derivation" — proven
  code-invariant by rebuilding with the pre-repair code (identical output; the committed JSON
  was stale, both code versions agree). The unaffected-year `*_lw` fields reproduce their
  committed values exactly (2024: 41.68/43.59; 2025: 70.23/72.2).
* `curate_lmp._neiso_flat24_repair`: spring phantom dropped + true HE02 relabeled; fall
  pair-mean dropped rather than curated (the two instances exist only as totals in the report
  route — components are deliberately not fabricated, so those two node-hours are absent from
  the clean datatype in 2018–2023, documented in the helper's docstring).
* Tests: `tests/test_neiso_smd_dst_repair.py` pins the repaired placement in both readers and
  pins true-shape pass-through. Fast lane after the repair: **6,907 passed / 0 failed**.

### 2c. Fixed in passing — an ambient HEAD blocker, unrelated to O8

`origin/main` @ `a4ef2a9` carries a **SyntaxError** in `scripts/run_calibration.py`: the
`7246272` hotfix added `reliability_floor_plant_exclusions` to `run_year` in parallel with
merge #4036, which had already landed the same parameter — the signature declared it twice,
making the module unimportable: **every calibration solve of every ISO was blocked at HEAD**
(18 fast-lane failures / 32 collection errors, all downstream of this one line). Fixed on this
branch (`fff285a`, one declaration and one duplicated override block removed); the fast lane
went from 18F/32E to 0F/0E with no other change.

## 3. GATES — source-anchored, residual-blind

| gate | result | bar |
|---|---|---|
| placement vs the market's published day (5 truth years × 9 sheets × 2 markets) | **0 mismatches** | 0 |
| spring phantom is the neighbour mean (fabrication proof) | **9/9 sheets, every truth year, both markets, to the cent** | — |
| fall pair mean reproduces from the published pair | **all 6 years, to the cent** | — |
| C3c tail exposure | max affected value **$138.65** | < $300, both sides |
| reproduce-check discipline | pre-repair code + current inputs reproduce the committed parquet **md5-identical** before the repair landed | byte-identity |

## 4. LOYO

Structurally n/a: **zero free parameters** — no parameter is introduced or moved; the repair is
a measured-input re-placement plus the same publisher's published values. The `neiso-85/86`
gas-basis and PJM input-clock precedents.

## 5. Scope left open, deliberately

1. **NYISO**: the live NYISO keeper solves on this parquet's DA hub series
   (`nyiso_import_hub_prices=True`); its 2023 input changed at 47 cells (max $20.12/MWh).
   Whether that warrants a NYISO re-solve is the NYISO lane's call (rule 25) — filed, not
   acted on.
2. **Clean-tree NEISO fall-back pair**: absent (totals exist only in the report route;
   components not fabricated). If the clean `lmp` datatype ever becomes a NEISO solve input,
   inject the pair from the report CSVs with null components.
3. **2018-03-11 RT daily report**: unpublished upstream (31-byte stub). The day is fully
   recovered by re-placement; if ISO-NE ever backfills the report, the overlay picks it up on
   the next authorized re-derivation with no code change.
4. **The 2022 touchpoint** stands as scored on the pre-repair instrument; the next
   owner-authorized 2022 iteration measures against the corrected one (its 2022 bench part is
   regenerated at that spend, not before).

## 6. Re-solve, registration and promotion — executed same-session

**Run id: `2026-08-17-neiso-97-dstrepair`** · bundle
`results/calibration/neiso97_dstrepair_A` · registered on the backcast dashboard in the same
session (rule 15 `[R-DASHBOARD]`). Full-span NEISO `--year 2023 2024 2025` in **ONE** bundle
(rule 16 `[R-ALLYEARS]`), replaying the keeper recipe `2026-08-14-neiso-93-envelope` via
`scripts/replay_keeper.py` with **zero scenario deltas** (computed, not asserted: zero
shared-value diffs; the only recipe-key differences are two rule-26 schema deletions by other
lanes and four post-incumbent fields recorded falsy at HEAD defaults). `meta.json` records
`reuse: null` — **all three years solved fresh**, P1+P2 like-for-like with the incumbent
(the O5 legacy-P2 anomaly deliberately not confounded into this lane).

### The headline measurement: the instrument moved, the model did not

**The arm's dispatch is BIT-IDENTICAL to the incumbent keeper's committed sidecars — every
year, every sidecar (`system`, `class_hourly`, `reserve_family`), both persisted passes, zero
differing cells** (`scripts/probes/neiso97_arm_vs_incumbent_sidecars.py` →
`_neiso97_arm_vs_incumbent_sidecars.json`). The prediction (§1: scoring target, not a NEISO
solve input) was measured, not assumed, and the neiso-91 reproducibility record extends by
one more byte-faithful replay. Bench blast radius exactly as predicted: `bench/NEISO/2023`
moves **only in the two DST months**; 2024/2025 move **only** by the previously-deferred
stale-JSON completeness deltas on the actuals side (`bench/avgLMP`), proven code-invariant
(§2b).

### Verdict — identical, criterion for criterion (D-5(b) satisfied)

| criterion | incumbent neiso-93 | **neiso-97 (rubric 3.2)** |
|---|---|---|
| C1 fuel-mix (grid-delivered) | PASS | **PASS** (all 12/12 · free 8/8) |
| C2 system volume | PASS | **PASS** |
| C3a mean LMP | PASS | **PASS** |
| C3b price duration/shape | PASS | **PASS** |
| C3c price tail / scarcity | CAVEAT (ledgered) | **CAVEAT (ledgered, carried verbatim)** |
| C4 dispatch correlation | PASS | **PASS** |
| C6 governance | PASS | **PASS** (attestation: `gen_neiso97_dstrepair_attestation.py`, every premise computed) |
| C8 forced-energy share | PASS | **PASS** |
| **determination** | **CALIBRATED-WITH-CAVEATS** | **CALIBRATED-WITH-CAVEATS** |
| grade summary | 8 / 7 / 0 / 1, 0 fails | **8 / 7 / 0 / 1, 0 fails** |

Pre-attestation the arm scored NOT-YET on `governance UNATTESTED` alone — guard (b) of the
C3c standing rule working as designed. The promotion-time attestation carries the incumbent's
DOF ledger (7 entries / 5 residual) and exceptions ledger (7 entries, C3c included)
**verbatim, asserted**; the corrected clock is **recomputed from committed sources at
attestation time** (float32-exact for all six repaired years), not quoted.

### Promotion — pre-signed on not-worse, executed

Keeper re-keyed to `2026-08-17-neiso-97-dstrepair` in `keepers/NEISO.json`;
`status/NEISO.js` rebuilt (`build_status.py --check` in sync); the `complete` marker's NEISO
entry re-keyed with the determination re-verified per D-5(b) **before** the re-key landed;
`audit_keepers.py --iso NEISO` **PASS 0 failures / 0 warnings** (independently confirmed by
the `calibration-keeper-auditor` agent, which found zero repairs needed); rule-28 re-stamps
landed on the NEISO matrix shard and the §5.6 prose header (`check_mechanism_matrix.py`
green: keeper stamps and prose headers match every shard). Under the NEISO lane's standing
site-retention directive (2026-08-15: keeper + 2022 touchpoint only), the superseded
`2026-08-14-neiso-93-envelope` was **pruned** from the site with `--force-uncite` — its
bundle directory travels with the prune per that directive's own precedent; the durable
evidence is this finding, the committed probe records (the bit-identity measurement was taken
before the prune), and the promoted bundle itself, whose dispatch is the superseded keeper's
own to the bit.

### Ambient defects found and disposed of along the way (not O8's, all reported)

1. **`origin/main` HEAD SyntaxError** (§2c) — fixed on this branch; every calibration solve
   of every ISO was blocked.
2. **Registry/payload parity was RED on main for two MISO-160 sidecars**
   (`2026-08-16-miso-160-control`, `-wefor-shape`: sidecars with no `runs/<id>.js` payload —
   the exact stranded-sidecar failure mode the calibration-report skill warns about). True at
   measurement time; **resolved by the #4044 MISO merge** before this promotion rebased onto
   it. At the rebased base the parity check instead flags `caiso200_h0_control` — a bundle
   dir with no retained sidecar, dead solve output from the just-merged caiso-200 lane
   (Class-E retention rule point 4). CAISO lane's to disposition (rule 25); this lane's
   files are parity-clean throughout.
3. **The committed `actual_lmp.json` NEISO 2024/2025 entries were stale** (§2b) — healed by
   this authorized re-derivation, proven code-invariant.
4. **D-1 actual-side third-decimal drift** vs the incumbent's committed
   `legitimacy_diagnostics.json` (same 7 gate failures, same classes; model side identical) —
   ambient upstream-actuals drift since 2026-08-14; `legitimacy_diagnostics.py` provably never
   reads the repaired LMP series.

**Rule 14 was never invoked**: nothing worsened at the corrected instrument, so there was no
accurate-input-versus-residual trade to disclose. Had one appeared, the accurate input would
have stayed.
