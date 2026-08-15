# FINDING — F6-DIAG: the neighbour-LMP backend parity defect

**Date:** 2026-08-11 · **Lane:** F6-DIAG (diagnosis only) · **Head:** `origin/main` @ `3ae7465`
· **Branch:** `claude/f6-lmp-backend-parity-1rc197`
**Pre-registration:** `docs/PREREG-f6-lmp-backend-parity-2026-08-11.md` (committed before any
measurement). **Instrument:** `scripts/probes/f6diag_lmp_backend_parity.py`.
**Nothing was solved, scored or registered.** No production behaviour changed. Rules 12 and 22
do not bind. No mechanism added, so no rule-28 matrix row is due.

---

## Verdict in one line

**The raw backend is right; the clean-backed *read path* is wrong — and neither data product is
corrupt.** Both reductions are faithful to the published PJM source; they index **different
clocks**. `neighbor_price._neighbor_lmp_clean` reads `interval_start_local` (the DST-prevailing
wall clock) where the model's 8760 calendar is the fixed standard-time chronological clock, so
the clean series sits **exactly one hour later** than the raw series for all ~5,700 DST hours.
This is the same defect `DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md` §1
diagnosed and commit `79285e6` (2026-07-15) repaired **in the producer** — surviving unfixed in
the consumer. **No keeper moves.** All six pre-registered predictions were confirmed.

---

## R1 — REPRODUCE: confirmed, exactly

`tests/curation/test_consume_lmp.py::test_clean_backed_lmp_matches_raw_loader`, PJM 2024 RTM:

```
AssertionError: max |raw-clean| = 408.704 exceeds 0.01
```

| quantity | value |
|---|---|
| `max abs(raw − clean)` | **408.70440** $/MWh — the reported 408.704 **confirmed** |
| ISO / year / market | PJM / 2024 / RTM (real-time) |
| hour index of the max | **1650** = 2024-03-10 18:00 EST — the DST transition day |
| raw / clean at that hour | 439.263 / 30.558 |
| hours with `abs diff > 1e-2` | **5,703** of 8,760 (65.1 %) |
| hours with `abs diff > $1` | 4,671 |
| mean abs diff | $5.95/MWh |

## R2 — WHICH BACKEND IS WRONG: **raw is right**

Both backends were scored against the **first-party source**,
`data/raw/lmp-data/PJM_2024_rt_da_monthly_lmps.csv` (105,408 rows, 12 trading hubs), reduced
independently by the probe on each candidate clock. Neither backend was assumed correct.

| comparison | max abs diff | hours > 1e-2 |
|---|---|---|
| **raw** vs published, indexed on the **fixed-standard (EST)** clock | **1.36e-05** | **0 / 8,760** |
| raw vs published, indexed on the prevailing (EPT) clock | 408.70440 | 5,702 |
| clean vs published, indexed on the fixed-standard clock | 408.70441 | 5,703 |
| **clean** vs published, indexed on the **prevailing (EPT)** clock | **0.000000** | **0 / 8,759** |

Read the diagonal: the raw product reproduces the published hub mean on the standard clock to
float32 storage precision, and the clean-backed read reproduces it **bit-exactly** on the
prevailing clock. Neither is corrupt; they answer different questions. The model's 8760
calendar is the standard-clock one (`eia_loader._eia_hourly_frame` sorts by UTC;
`derive_actual_lmp._STD_TZ`), so **raw is the correct answer and clean is the wrong one**.

The defect is a **consumer** defect, not a data defect. The clean `lmp` partition carries
`interval_start_utc` as its authoritative column (`curate_lmp.py`, "Timezone & partitioning
conventions"); `_neighbor_lmp_clean` reads the other one.

Worst hours — the published value adjudicates every row:

| hoy | std timestamp | raw | clean | published @ this **STD** hour | published @ this **prevailing** label |
|---|---|---|---|---|---|
| 1650 | 2024-03-10 18:00 EST | 439.263 | 30.558 | **439.263** | 30.558 |
| 1651 | 2024-03-10 19:00 EST | 44.648 | 439.263 | **44.648** | 439.263 |
| 5008 | 2024-07-28 16:00 EST | 300.982 | 38.555 | **300.982** | 38.555 |
| 5703 | 2024-08-26 15:00 EST | 238.488 | 58.227 | **238.488** | 58.227 |

**The line-35 docstring is false.** "float32 storage in the realized product is the only source
of disagreement" — float32 accounts for **1.4e-05** of a **408.70** gap, i.e. 0.0000033 % of it.
The claim was *true when written* (see the genealogy below); it stopped being true on
2026-07-15 and was never revisited.

## R3 — SHAPE: **(b) timestamp alignment**, a one-hour DST shift

Not (a) outlier hours, not (c) units/sign, not (d) a float32 story the tolerance mis-sizes.

| segment (std-clock slots) | max abs diff | hours > 1e-2 | mean |
|---|---|---|---|
| pre-DST `[0:1634]` | 9.21e-06 | 0 / 1,634 | 6.0e-07 |
| DST `[1634:7345]` | **408.704** | 5,702 / 5,711 | 9.13 |
| post-DST `[7345:]` | 1.059 | **1** / 1,415 | 7.5e-04 |

**The lag-1 test is decisive:** `clean[k]` vs `raw[k−1]` across the 5,710-hour DST window gives
**max 1.36e-05, 0 hours > 1e-2** — an exact one-slot shift at float32 precision, not an
approximation.

The two DST singularities behave exactly as the clock mismatch predicts:

* **spring-forward slot 1634** — 12 published rows on the standard clock, **0** on the
  prevailing clock (that wall-clock label does not exist). The prevailing reduction leaves one
  empty slot for the year, which `_fill_hourly` interpolates.
* **fall-back slot 7345** — 12 rows on the standard clock, **24** on the prevailing clock: the
  two real instances collapse into one label and are averaged. This is the single post-DST
  hour above tolerance (1.059).
* the standard clock has **0** empty slots — dense and correct.

**Relation to ercot-187 (`9568611`).** Same broad family — calendar handling in a derive — but a
**different mechanism, and the opposite failure mode.** ercot-187 was a stale boolean mask
indexed against a post-filter frame: **fail-closed**, it raised `IndexError` and no artifact
could pass through it. This one is a clock-convention mismatch that **fails silently**, emitting
plausible prices attached to the wrong hour. Not the same bug.

**The real genealogy — the fix was applied to the producer and to no consumer:**

| date | commit | event |
|---|---|---|
| 2026-06-19 | `f4486c7` | clean backend + parity test added. The raw parquet was **also** on the prevailing clock, so the two agreed — the docstring's float32 claim was **true**, and the test would have passed. |
| 2026-07-15 | `79285e6` | "Rebuild actual-LMP hourly parquets on the model's chronological clock" — fixes the producer for all six ISOs, citing the ERCOT clock-artifact diagnosis §1. |
| — | — | the clean-backed **consumer** is not updated. **Parity silently breaks that day.** |
| 2026-08-11 | this lane | found, 28 days later. |

## R4 — BLAST RADIUS: **no keeper moves; not a stop-the-line**

**The raw path is load-bearing, and the NYISO keeper is on it.**
`neighbor_lmp_hourly`'s one production consumer is
`model/interchange/nyiso.py::inject_nyiso_import_hub_prices`, which reprices NYISO's
`PJM_west` / `ISONE_tie` / `import_scarcity` / `export_surplus` import-node tranches at the
neighbour's measured hourly LMP. The NYISO keeper **`2026-08-08-nyiso-132-cf-arm` carries
`nyiso_import_hub_prices: true`** in its committed `run_config.json` `scenario_config`.

That keeper is nevertheless **safe, affirmatively** — not merely "the flag is off":

1. it reads the **raw** backend, which R2 measured correct to 1.36e-05 against the published
   source over all 8,760 hours; and
2. the clean backend is **unreachable**: `MARKET_SIM_USE_CLEAN` is set nowhere in any run path
   (only inside `tests/` and one explanatory comment), defaults OFF, and `data/clean` is
   gitignored.

Everything else on or near the path is clear:

* **No other ISO's seam is on it.** `inject_miso_pjm_lmp_import_prices` and
  `inject_caiso_import_hub_prices` read their own committed products, not `neighbor_lmp_hourly`.
* **No committed constant was derived through the clean backend.**
  `derive_neighbor_convexity.py`, `derive_neighbor_hr_elasticity.py` and
  `validate_neighbor_price.py` all read `actual_lmp_hourly_<ISO>.parquet` **directly**, bypassing
  `neighbor_lmp_hourly` entirely — so `hr_by_year`, `_HR_GAS_ELASTIC` and the convexity exponents
  carry no contamination.
* **No registered forecast run** references the flag.

**One rule-24 observation, filed not fixed.** `MARKET_SIM_USE_CLEAN` is an environment switch
that *can* change a solve (through the NYISO injector) and is **not recorded in
`run_config.json`** — the `environment` block carries only `python_version`, `platform` and
package versions. A solve made with the flag set would be indistinguishable from one made
without it. It is a data-source switch rather than a tunable, but it is an unrecorded channel
that reaches the LP.

## R5 — WHY IT WAS INVISIBLE: two independent locks, never runnable in CI

1. **Marker exclusion (unconditional).** `pytestmark = [pytest.mark.slow,
   pytest.mark.integration]`, and `@requires_raw` adds `fulldata`. CI's only general pytest tier
   runs `-m "not slow and not integration and not fulldata"` (`.github/workflows/ci.yml:299`) —
   **all three** of the test's markers are in the exclusion list. The workflow's other two
   pytest invocations run two named guard files only.
2. **Skip guard.** `_clean_available()` is evaluated at import/collection and skips wherever
   `data/clean/lmp/PJM/RTM/lmp_2024.parquet` is absent. **No CI job builds `data/clean`** — no
   workflow anywhere in `.github/workflows/` references `regenerate_clean`, `data/clean` or
   `MARKET_SIM_USE_CLEAN`.

So the test is green exactly where it cannot fire. It has been **unrunnable in CI for its entire
53-day life** (added 2026-06-19) and **failing for the last 28 days** (since 2026-07-15).

## Scope sweep — 44 clean partitions, 4 ISOs (rule 25: no verdict transferred)

All four ISOs' clean-backed reads disagree with their raw counterparts, **for different
reasons**. Each row was measured on that ISO's own data; nothing below is inferred from PJM.

| ISO (partitions) | shipped max | after **clock** fix | after **clock + hub** fix | residual |
|---|---|---|---|---|
| **PJM** (16, 2018–25, DAM+RTM) | 19.2 – 1,284.5 | **≤ 1.0e-04** | ≤ 1.0e-04 | **none — clock only** |
| **CAISO** (8, 2023–26) | 46.0 – 759.0 | 11.2 – 193.1 | **≤ 2.7e-05 on 7 of 8** | 2023 DAM: 48 h, from the raw product's own 120 interpolated-NaN hours (OASIS retention) |
| **NEISO** (16, 2018–25) | 19.8 – 1,659.9 | 11.7 – 39.6 | max 0.4 – 40.2 but **mean 0.02, only 2–45 hours/yr** | DST-transition-day hour labelling |
| **NYISO** (4, 2022–25) | 802.8 – 2,038.7 | ~unchanged | ~unchanged | **a distinct third defect** |

Per-ISO root causes:

* **PJM** — clock only. The clean partition holds exactly the 12 trading hubs the raw product
  averages, so the hub definition already matches and the DST shift is the whole story. This is
  precisely why the test picked PJM, as its own line-28 comment says.
* **CAISO** — clock **+ hub weighting**. Raw load-weights TH_NP15 / TH_ZP26 / TH_SP15 at
  0.3969 / 0.0646 / 0.5385; the clean consumer takes a simple mean. Both repairs together give
  bit-parity on 7 of 8 partitions.
* **NEISO** — clock **+ hub definition**. Raw's hub is the `.H.INTERNAL_HUB` ("ISO NE CA") sheet
  **alone**; the clean consumer averages all 9 sheets (8 zones + the hub). Both repairs reduce
  the disagreement to 2–45 hours a year on the DST-transition days, where
  `curate_lmp.parse_neiso_file`'s `Hr_End` arithmetic + `tz_localize(nonexistent="shift_forward")`
  diverges from `derive_actual_lmp._neiso_sheet_series`'s positional intra-day offset.
* **NYISO** — clock + hub definition (raw excludes the four external proxy buses H Q / NPX / O H
  / PJM; the clean consumer averages all 15 nodes) **plus a genuine third disagreement that
  neither repair touches**. Measured on June 2024 against the published 5-minute zip, hub mean
  over the 11 internal zones:

  | reduction of the published source | vs **raw** parquet | vs **clean + clock + hub** |
  |---|---|---|
  | stamps as interval-**BEGINNING** | **mean 0.003, 1 of 720 h off** | mean 0.616, 686/720 off |
  | stamps as interval-**ENDING** | mean 0.616, 685/719 off | **exactly 0.000000, 0 of 719 off** |

  The two products adopt **opposite conventions** for NYISO's RTD "Time Stamp":
  `derive_actual_lmp._nyiso_wide` bins it as interval-beginning, `curate_lmp.parse_nyiso_zip`
  as interval-ending (`(ts_end − 1s).floor("h")`). One boundary sample in twelve swaps per
  hour, so the mean effect is small ($0.62/month) but the max is large ($59 in June, up to
  $2,038 across the year on a spiky RT series). **This lane did NOT adjudicate which convention
  matches NYISO's published definition** — that needs the NYISO data dictionary and is an open
  sub-object for the FIX lane, not a settled verdict.

---

## CARD-READY RECOMMENDATION

### ✅ A — Fix the clean-backed consumer reduction. **RECOMMENDED.**

Make `_neighbor_lmp_clean` index `interval_start_utc` converted to the ISO's fixed standard
offset (not `interval_start_local`), and apply the raw product's hub definition per ISO.

* **Scope:** confined to `src/market_sim/data/neighbor_price.py` — a standard-clock variant of
  `_hour_of_year`, plus a small per-ISO hub-definition table. No ScenarioConfig field, therefore
  **no matrix row, no `_CACHE_KEY_OPTIONAL_FIELDS` entry, no defaults-ledger line** (rule 28).
* **Measured effect** (this lane, not asserted): bit-parity on all 16 PJM partitions and 7 of 8
  CAISO; NEISO down to 2–45 hours a year; NYISO still open on the interval convention.
* **Keeper risk: none.** The raw product is untouched and the clean path is unreachable at
  defaults, so no keeper can move.
* **Also fold in the docstring correction** (line 35 of the test, and the two module docstrings
  that repeat the float32 claim) — it is false today and must be fixed whatever else happens.
* **The real exposure this closes:** `docs/iso-model-unification-plan.md` plans to "remove the
  `MARKET_SIM_USE_CLEAN` env var gating — clean is now mandatory". On the day that lands, a
  one-hour-shifted neighbour price flows straight into the NYISO keeper's import stack.

### ❌ B — Fix the raw product. **REJECT.**

Measured wrong: the raw product matches the published source at 1.4e-05 over 8,760 hours.
**Cost of choosing it:** it would re-introduce the exact artifact the ERCOT clock-artifact
diagnosis identified and `79285e6` already paid to repair, and — unlike A — it **would move the
NYISO keeper**, which is live on that series.

### ❌ C — Re-size the tolerance and correct the docstring. **REJECT as the primary action.**

The docstring correction is necessary and belongs inside A. Re-sizing `_TOL` to admit a $408 gap
is not: it converts the only instrument in the repo capable of detecting a one-hour clock shift
into a test that asserts nothing. **Cost of choosing it:** the second LMP backend stays silently
one hour off, with its detector disarmed, until the clean seam becomes mandatory.

### ⚠️ D — Make CI build `data/clean`. **RECOMMEND A NARROW VERSION ONLY.**

Building the full clean tree per PR is not justified — `regenerate_clean.py` (all datatypes) is
~63–65 min of billed private-repo runner time, and even the `lmp` datatype alone measured ~10 min
in this container (CLAUDE.md, "never offload work to CI"). The cheaper and more valuable
structural fix is that **a guard which turns a failing test into a passing run is worse than no
test**: `_clean_available()` currently makes the suite green precisely where the test cannot
fire. Recommend (i) making the skip **loud** — surfaced in the run summary rather than silent —
and (ii) reconsidering the blanket `slow`+`integration` marker on a 0.34-second test. *This is a
recommendation only; no workflow was written in this lane.*

**Take A, with the docstring correction inside it, plus D-narrow.** The NYISO interval-convention
question travels with the FIX lane as a separate, un-adjudicated sub-object.

---

## RESOLUTION — option A landed, 2026-08-13/14 (lane D-32-F6FIX)

*Appended, not edited: everything above is the diagnosis exactly as it landed on 2026-08-11.*

Option A was signed by the owner (**D-32**, Addendum AT.2) and implemented on branch
`claude/f6-lmp-backend-parity-fuc03v`. **B and C were not revisited.** Nothing was solved,
scored, registered or promoted; no keeper moved; no `ScenarioConfig` field was added, so no
rule-28 matrix row and no `_CACHE_KEY_OPTIONAL_FIELDS` entry were due — as §A predicted, and
`check_mechanism_matrix.py` / `check_cache_key_registration.py` both exit 0.

**What changed**, confined to the two files §A named:

* `src/market_sim/data/neighbor_price.py` — `_neighbor_lmp_clean` now indexes
  `interval_start_utc` converted to the ISO's fixed standard offset (`_std_hour_of_year`, a
  mirror of `derive_actual_lmp._std_hour_index`) and reduces with the realized product's own hub
  definition, from a small fail-closed per-ISO table `_HUB_SPECS` (PJM every node; CAISO's three
  trading hubs load-weighted; NYISO's eleven internal zones; NEISO's `.H.INTERNAL_HUB` sheet
  alone). The prevailing-clock `_hour_of_year` is **deleted**, not left callable (rule 26).
* `tests/curation/test_consume_lmp.py` — the false line-35 float32 claim and the module
  docstring corrected. **`_TOL` unchanged at 1e-2**; the test passes **un-skipped** on a rebuilt
  clean tree.

**Measured effect — R2's verdict held: the raw product needed no change.** The clean-backed read
now agrees with it at float32 storage precision wherever the two products define the same hub:
bit-parity on **all 16 PJM** partitions (0 hours over tolerance, max ≤9.8e-05) and **7 of 8
CAISO** (≤2.7e-05; 2023 DAM excepted at 48 h / $37.24, on the raw product's own
OASIS-retention NaN hours), NEISO down to **2–45 DST-transition-day hours a year**, mean
≤$0.058. PJM 2024 RTM goes **408.70440 → 1.36e-05**, and its 5,703 out-of-tolerance hours to
**0**. Every number is two runs of this lane's own `--sweep` instrument, and the fixed code
matches this lane's independently-written `--fixcheck` `clock+hub` candidate on all 44
partitions.

**The NYISO interval-convention residual is UNCHANGED and remains OPEN at full magnitude.** It
was not forced closed, absorbed into a widened tolerance, or carved out of the test. Deciding it
still requires the NYISO data dictionary; it is the first carried-forward item of the fix lane.

Full record — authority, the per-partition before/after table, the acceptance ledger and the
un-actioned §D-narrow: `docs/handoffs/d32-f6fix-2026-08-13.md`.
