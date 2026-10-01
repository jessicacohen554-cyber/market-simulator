# FINDING — nyiso-166: the committed NYISO RT-reserve calibration reference is REPAIRED

**Date:** 2026-08-31 · **Lane:** NYISO calibration · **Shorthand:** nyiso-166
**Rule:** 14 `[R-ACCURATE]` (prefer accurate/measured data; a wrong measured input
is a discovered bug, never something to bury) · **Zero solve.** Committed
artifacts + committed raw only. No LP, no holdout spend, no mechanism, no
parameter, no keeper/marker/determination change.

**Object:** `data/raw/_validation-source/actual_as_reserve_NYISO.parquet`
**Builder:** `scripts/data/process_nyiso_as.py::build_reference`
**Opened by:** nyiso-165 §3, which found the two defects, established the blast
radius, and explicitly deferred the repair to a data lane
(`docs/calibration-log/nyiso.md`, 2026-08-31 nyiso-165 entry).

---

## 1. Result

Both defects are repaired at the source, the reference is regenerated for **every
year it carries (2018–2026)**, and the repaired artifact reproduces
`scripts/probes/nyiso164_nyca_shortage_check.py` — the independent measurement of
record, which reads the raw CSVs directly — **hour by hour, 8,759/8,759 mapped
hours, in each of 2023, 2024 and 2025, in both the NYCA and the NYC tier**
(max |diff| 1.2e-4 on values up to $2,568, i.e. the reference's own float32
storage).

**No gate moves and nothing about the model changes.** The keeper
`2026-08-30-nyiso-159-loss-surface` re-verifies at **NOT-YET** on exactly
{C3a-2025 −11.5 %, C3c}, and `scripts/audit_keepers.py --iso NYISO` re-reads
**PASS 0 failures / 0 warnings** — byte-identical verdicts to the pre-repair
state, because this reference is read by **no scorer and no solve path** (§4).
NYISO holds no `complete` marker, is absent from `final`, and the holdout freeze
is untouched. The nyiso-161 winter-face waiver card remains **filed and unruled**;
this session does not touch it.

What the repair buys is the removal of a **trap**: a committed artifact that
looked like the measured reserve price, was off by up to 3× in level and by one
hour in 65.2 % of the year, and had already walked one audit (nyiso-165) to the
opposite of the right answer on a charter question.

## 2. Defect A — the nested duration cascade was SUMMED

`build_reference` computed `stack = spin_10 + nonsync_10 + op_30`.

NYISO's three posted operating-reserve products **nest by duration**: a
10-minute spinning MW also satisfies the 10-minute total and the 30-minute total
requirement, so the posted prices are **cumulative, not incremental**. Verified
on the committed per-year CSVs:

| year | rows | `spin_10 ≥ nonsync_10 ≥ op_30` | all three exactly equal |
|---|---|---|---|
| 2023 | 96,360 | **100.0000 %** | 82.73 % |
| 2024 | 96,624 | **100.0000 %** | 83.56 % |
| 2025 | 96,360 | **100.0000 %** | 82.11 % |

(11 settlement zones × 8,760 h each.) A reserve MW earns the **largest** of the
three, never their sum; where all three are equal the sum triple-counts one
shadow price — exactly 3.0× in **28.1 % / 73.2 % / 79.1 %** of priced WEST hours
in 2023 / 2024 / 2025.

Worked example, 2023-09-05 17:00 EDT, WEST: `spin_10 = nonsync_10 = op_30 =
$661.77`. The cleared NYCA-tier price is **$661.77**; the summed "stack" was
**$1,985.32**.

**The nested-REGION stacking is real and is NOT what was wrong.** A downstate
zone's posted price already contains the NYCA + East + SENY + NYC shadow prices
added together — that is the cascade the overlay models. What is not additive is
the three **duration** products *within* one zone's posting.

**Repair:** the cleared price is the cascade **max** over `_CASCADE_PRODUCTS`
(equivalently `spin_10` wherever the cascade is intact, which is everywhere).

## 3. Defect B — a naive prevailing-Eastern clock on a standard-time index

`build_reference` mapped the CSV's naive `Time Stamp` positionally onto the
model's 8760 index:

```python
hoy = _MONTH_START_HOUR[month - 1] + (day - 1) * 24 + hour
```

The `Time Stamp` is **prevailing Eastern** (DST-following). The model's NYISO
clock is **fixed standard time**, `derive_actual_lmp._STD_TZ["NYISO"] =
Etc/GMT+5`, which is what `actual_lmp_hourly_NYISO.parquet` — the series every
consumer joins this reference against — rides. Measured on the WEST series:

| year | hours where the two indices disagree |
|---|---|
| 2023 | 5,712 / 8,760 (**65.2 %**) |
| 2024 | 5,712 / 8,760 (**65.2 %**) |
| 2025 | 5,712 / 8,760 (**65.2 %**) |

i.e. the entire DST season, which is where NYISO's price tail sits. (nyiso-165
reported 5,710; the two-hour difference is the boundary-spill row treated below.
Immaterial to every conclusion.)

**Repair:** localize to `America/New_York` (`ambiguous=True`,
`nonexistent="shift_forward"`) and index with the repo's **own**
`derive_actual_lmp._std_hour_index` — the same conversion nyiso-164 measures
with, which is why the two now agree by construction rather than by coincidence.

Two side effects of using the real helper, both improvements:

* **A boundary spill is now dropped.** Each per-year CSV carries one Jan-1-of-
  the-next-year row (`2024-01-01 00:00` in the 2023 file, and so on). The
  positional map folded it onto hour 0 and let a `max()` pick between it and the
  real hour 0; `_std_hour_index` returns `-1` for it and it is discarded.
* **One hour per year is NaN, deliberately.** The DST fall-back hour (std hours
  7393 / 7345 / 7321) is unrecoverable because the upstream hourly CSV already
  collapsed the repeated wall-clock hour into a single row. nyiso-164 makes the
  same choice, so coverage matches exactly (8,759 mapped hours per year).

## 4. Blast radius — confirmed nil, re-verified at HEAD

The reference has exactly one code consumer,
`scripts/data/derive_nyiso_rcpf_overlay.py`, and there it feeds **only printed
validation reports** (`_actual_as_reserve` at the report block, and
`_actual_zone_reserve` at the per-zone comparison table). It never enters the
written overlay parquet, never sets a parameter, and never reaches an LP. Checked
call-site by call-site.

Re-verified after the repair, unchanged in both directions:

```
python3 scripts/calibration_verdict.py --run-id 2026-08-30-nyiso-159-loss-surface
  → CALIBRATION DETERMINATION: NOT-YET   (C3a 2025 −11.5 %; C3c 2023/24/25)
python3 scripts/audit_keepers.py --iso NYISO
  → PASS: 0 failure(s), 0 warning(s)
```

## 5. Magnitude of the correction

Incidence is essentially untouched — a price is zero on the summed basis exactly
when it is zero on the max basis — but **levels were overstated 1.8×–2.9× and the
maxima badly so**:

| year | series | old mean | new mean | old max | new max | hours >$0 (old → new) |
|---|---|---|---|---|---|---|
| 2023 | `nyca_reserve_adder` | $2.20 | **$1.25** | $1,985.31 | **$761.73** | 629 → 629 |
| 2023 | `nyc_reserve_adder` | $6.37 | **$3.52** | $2,447.95 | **$1,114.53** | 3,020 → 3,020 |
| 2024 | `nyca_reserve_adder` | $2.51 | **$1.02** | $1,496.88 | **$552.90** | 338 → 338 |
| 2024 | `nyc_reserve_adder` | $7.64 | **$3.59** | $2,180.32 | **$876.59** | 3,082 → 3,082 |
| 2025 | `nyca_reserve_adder` | $10.99 | **$3.97** | $2,933.86 | **$1,101.85** | 876 → 876 |
| 2025 | `nyc_reserve_adder` | $28.73 | **$11.69** | $5,568.18 | **$2,146.50** | 4,007 → 4,006 |

All-hours `nyca_reserve_adder` mean, every year in the artifact (a property of
the measured input alone — no model output and no actuals tail is involved, so
this is data prep, not a holdout spend under rule 22): 2018 $5.28 → $4.20;
2019 $1.24 → $1.19; 2020 $1.31 → $1.01; 2021 $1.91 → $1.49; 2022 $8.36 → $5.29;
2023 $2.20 → $1.25; 2024 $2.51 → $1.02; 2025 $10.99 → $3.97; 2026 $9.62 → $4.27.

**The 2025 NYC max of $5,568 should have been the tell.** No attainable NYISO
RCPF cascade reaches it; the corrected $2,146.50 is a plausible nested-region
sum. A published price above every published penalty factor is a construction
error by inspection.

## 6. Validation — mandatory, and it passes

The acceptance test is agreement with `nyiso164_nyca_shortage_check.py`, which
measures the same quantity from the raw CSVs by a **different** construction
(the minimum across zones A–E rather than WEST alone — A–E price identically,
max spread 0.000000 $/MW in every hour of every year, so the two are equal iff
the nesting holds). A mismatch would mean the repair is wrong, not the probe.

Published NYCA tier in the C3c tail hours (`rt > $300`), repaired reference vs
the probe of record:

| year | tail h | mean | median | max | ceiling test |
|---|---|---|---|---|---|
| 2023 | 10 | $306.74 | $248.22 | $761.73 | 0 |
| 2024 | 13 | $254.62 | $239.96 | $552.89 | 0 |
| 2025 | 42 | $393.31 | $403.74 | $1,101.85 | 0 |
| **total** | **65** | | | | **0 / 65** |

Every figure matches the probe exactly. (2024's max prints as $552.90 from the
reference and $552.89 from the probe — the true value is $552.895 and the
reference stores float32; a half-cent display tie, not a disagreement.)

The **ceiling test** is the one the summed reference broke: a resource holding
reserve forgoes energy, so its opportunity cost is bounded by the concurrent
LMP, while an RCPF demand-curve shortage price is not. On the repaired basis the
NYCA-tier price never exceeds the concurrent LMP in **0 of 65** tail hours; on
the summed basis it "exceeded" LMP in 46 of 65 — which is precisely how
nyiso-165 reached the opposite verdict. Re-running the probe against the
repaired tree returns a byte-identical JSON (it reads raw, not the reference),
confirming it is a genuinely independent check.

Hour-by-hour parity, both tiers, all three years: `np.allclose(rtol=1e-6,
atol=1e-3)` over all 8,759 mapped hours, with identical NaN patterns.

## 7. Regression test

`tests/test_nyiso_as_reference_repair.py` (9 tests, all passing) pins:

* **Cascade invariant** — `spin_10 ≥ nonsync_10 ≥ op_30` in every row of every
  committed year, and `max(_CASCADE_PRODUCTS) == spin_10`. If this ever fails
  the products are no longer cumulative and the aggregation must be re-derived
  from the posting convention, not patched.
* **Cascade MAX end-to-end** — a synthetic CSV row with all three at $100 must
  yield $100, not $300; with $90/$50/$25 must yield $90, not $165.
* **Std-clock identity** — a DST-season timestamp lands exactly one hour earlier
  than the retired positional map (and the naive slot is left NaN); a winter
  timestamp is unmoved; the two clocks disagree in >60 % of hours on the real
  data; the std index is injective.
* **Parity with nyiso-164** — hourly parity in both tiers, the per-year tail
  table of §6, and the 0/65 ceiling test.

The four synthetic-CSV and helper tests need no committed data and are the
standing guard; the data-backed tests skip when the `nyiso` data profile is not
hydrated.

## 8. Two secondary repairs in the same class

* **`derive_nyiso_rcpf_overlay._actual_zone_reserve` had a raw-CSV fallback that
  re-implemented BOTH defects** — it summed the cascade and mapped the naive
  timestamp positionally — one missing file away from firing. Deleted rather
  than fixed (rule 23 `[R-DELETE]`: a defective duplicate that still parses is a
  re-armable wrong answer). The function now reads the reference or returns
  empty, in which case the report prints "-". Report-only path; no solve input.
* **The emitted column order is now deterministic.** `build_reference` iterated
  `set(columns.values())`, so the parquet's column order varied run to run. It
  now sorts, and the artifact is byte-reproducible from the same CSVs
  (sha256 `60be007f34b3599d735d87eb71842e9309ec174ee18f71b9f7577647d0a52156`,
  identical across two consecutive regenerations). Names and dtypes are
  unchanged, so every by-name consumer is unaffected.

## 9. Records touched

* `docs/nyiso-rcpf-overlay.md` — the "Measured validation" section quoted the
  pre-repair levels ($2,448 NYC max, NYCA mean $2.20, NYC mean $6.37). Corrected,
  with a dated note that the **model-vs-measured mean comparisons stated earlier
  in that doc have a superseded measured side** (the model side is unchanged, so
  the modelled adder is *closer* to the measured level than those lines suggest).
* `scripts/probes/c3c_q2_nyiso_nyca_shortage.py` — the superseded probe's
  docstring and its `SUPERSEDED` JSON key described the defects in the present
  tense. Now dated to this repair, with the explicit note that the probe re-run
  at HEAD no longer reproduces its own committed record
  (`results/calibration/_c3c_q2_nyiso_nyca_shortage.json`, deliberately **not**
  re-run — it is the frozen artifact of the false positive) and stays superseded
  regardless, because its verdict was wrong on the merits.

## 10. Mechanism matrix — DO-NOT-REDO discharged, no cell moves

Rule 26 duty (a): `docs/codebase-site/data/mechanism-matrix/NYISO.js` checked.
**No cell moves and no shard is edited** — this is a data-reference repair, not a
mechanism: duty (b) is not triggered (nothing tested, armed or adjudicated) and
duty (c) is not triggered (no `ScenarioConfig` field). The adjudicated cells
stand as read: `nyiso_ordc_measured_step_span` **K**,
`nyiso_li_locational_reserve` **K**, `nyiso_east_reserve_families` **I**,
`energy_reserve_coopt` **K**, `ordc_scarcity_overlay` **·**.

Nothing here re-opens the twice-refuted lines: "arm a NYCA-level family or
requirement so the tail can price" and "the model lacks tail headroom" (3.0–5.1
GW lower-bound headroom against a 2,620 MW requirement). The repair **reinforces**
them — the corrected reference is what nyiso-164 already measured, and it says
reality was not NYCA-short in its own tail.

## 11. Honest expected value

This moves **no gate**. It does not touch C3a-2025 or C3c, and NYISO's
rubric-moving path stays owner-gated on the nyiso-161 card. What it delivers is a
committed measured input that is now correct, agrees with the measurement of
record by construction, is byte-reproducible, and is guarded by a regression test
— and the removal of an artifact that had already produced one wrong answer to a
charter question.
