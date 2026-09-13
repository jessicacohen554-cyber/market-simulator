# FINDING — NWPP-22: the PRICE-UNSCORED determination class is built; every keeper is byte-identical

**Lane** NWPP-22 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/nwpp-22-verdict-basis-wkmyv5` · **Base** `33a7c961` · **PRECOMMIT**
`docs/handoffs/PRECOMMIT-nwpp-22-2026-09-13.md` (pushed at `49349b8f` before the scorer was edited) ·
**Scorer commit** `8094669a` · **Data profile** `code` · **Ruling** card N2 limb (b); issued under N11.

## 0. Result, first

**Byte-identity over every designated keeper: 7 of 7 IDENTICAL, zero bytes moved.** Full verdict
payloads (`calibration_verdict.py --run-id <id> --json`), scored at `33a7c961` before the edit and
again after it, keepers read from `frontend/data/backcast/keepers/*.json` at the base tree:

| ISO | keeper | determination | payload bytes | sha256 (first 16) before / after | result |
|---|---|---|---:|---|---|
| CAISO | `2026-09-12-caiso-275-gascoupling` | CALIBRATED | 42,128 | `d8984d9abb723375` / `d8984d9abb723375` | IDENTICAL |
| ERCOT | `2026-09-09-ercot265-receipts-fallback` | CALIBRATED | 89,976 | `c1a1cae8ef00357f` / `c1a1cae8ef00357f` | IDENTICAL |
| MISO | `2026-09-12-miso-255-sil-measured` | NOT-YET | 98,065 | `c03ad123f7b9e82d` / `c03ad123f7b9e82d` | IDENTICAL |
| NEISO | `2026-09-09-neiso-108-fuelvintage` | CALIBRATED | 55,258 | `f9c5f43350a845be` / `f9c5f43350a845be` | IDENTICAL |
| NYISO | `2026-09-13-nyiso231-anchor-span` | NOT-YET | 52,951 | `9ad59495ab6ae58a` / `9ad59495ab6ae58a` | IDENTICAL |
| PJM | `2026-09-11-pjm-d4-4-gasoutage` | CALIBRATED | 41,653 | `e88a5ac7664dc106` / `e88a5ac7664dc106` | IDENTICAL |
| SPP | `2026-09-13-spp-38-vintage-cache` | CALIBRATED | 47,607 | `8e56584e61b7fb3d` / `8e56584e61b7fb3d` | IDENTICAL |

`cmp` on each pair returned identical; the text render (`render_text`) and the condensed sidecar
(`condensed_metrics`) were also checked identical on CAISO and SPP, and no keeper's condensed sidecar
gains the new key. The keeper list read from the tree matched the charter's list exactly.

**The exact determination an unscoreable-price ISO now reads** (rendered on a synthetic NWPP-shaped
run, 2023–2025, against the REAL committed store — no NWPP registry object exists and none was made):

```
PHYSICALLY CALIBRATED — PRICE UNSCORED (no admissible hourly price series)
```

and, when the PHYSICAL criteria themselves earn a caveat (an unscored C1/C2/C4/C8, a commercial-band
C2, a data-blocked year):

```
PHYSICALLY CALIBRATED-WITH-CAVEATS — PRICE UNSCORED (no admissible hourly price series)
```

Its determination basis leads with (ISO and years substituted; the per-year tail carries each price
record's own SKIPPED reason, which is the full magnitude that exists when there is no series):

> PRICE UNSCORED — no admissible hourly price series for NWPP: no record in
> `data/raw/_validation-source/actual_lmp.json` and no LMP actual in any scored year (2023, 2024,
> 2025). C3a mean LMP, C3b price duration/shape and C3c price tail / scarcity were NOT TESTED — they
> read SKIPPED, never PASS, and are excluded from grade_summary. This determination certifies the
> PHYSICAL criteria only (C1 fuel-mix, C2 system volume, C4 dispatch correlation, C6 governance, C8
> forced share) and is NEVER a CALIBRATED reading (owner ruling, card N2 limb (b), 2026-09-13).
> Per-year: 2023 C3a mean LMP: no measured LMP reference on disk for NWPP 2023 — C3a UNSCOREABLE
> (reference absent, not passing); … 2025 C3c price tail / scarcity (RT hourly): hourly scarcity
> series not in committed payload (tail>$200)

and the payload carries a structural block so no consumer has to parse the label:

```json
{"iso": "NWPP", "reference": "data/raw/_validation-source/actual_lmp.json",
 "years": [2023, 2024, 2025], "criteria": ["price_mean", "price_shape", "price_tail"],
 "physical_rung": "CALIBRATED"}
```

## 1. What was built — one branch, its guards, nothing else

All in `scripts/calibration_verdict.py` (3,813 → 4,008 lines; +199/−4; the four deletions are the
three-line lift inside the else-branch and one blank). Every element was fixed in the PRECOMMIT
before the edit and none was re-cut after.

| element | where | what |
|---|---|---|
| predicate | `_price_series_absent` | ISO-level, data-driven, four legs each of which keeps the scorer on its old route when it fails: the committed reference store is readable AND non-empty; the ISO has NO record in it; every scored year is in `price_reference_blocked_years`; C3a/C3b/C3c are all SKIPPED. **No ISO name anywhere.** |
| strings | `PHYSICALLY_CALIBRATED_PRICE_UNSCORED`, `…_CAVEATS_PRICE_UNSCORED`, `PRICE_UNSCORED_BY_RUNG` | one per physical rung, so the price half's absence can never shed a physical caveat |
| the lift | `determine_from_artifacts`, else-branch | `skipped_physical` = `skipped_downgrading` minus the three price ids, **only when the predicate holds**; the rung is then earned by the physical criteria; the rename happens LAST, after every physical reason line, and the basis line is inserted FIRST so `headline()` leads with it |
| reason | `_price_unscored_reason` | names the store, the years, the three criteria and each record's own SKIPPED reason |
| output | `price_unscored` block (verdict, `condensed_metrics`, `render_text`) | present ONLY when the class fired — the `span_restricted` pattern — so every other payload is byte-identical |
| header | entry above `RUBRIC_VERSION` | records the class, the predicate, the guards and the version reading |

**Why it cannot fire for an ISO that has a series.** The store at `33a7c961` names exactly
`ERCOT PJM CAISO NYISO NEISO MISO SPP`; leg two returns False for each. A per-year gap inside such an
ISO (MISO 2020–2021 scored alone in a rule-30(b) per-year ladder, `--years 2020`) is exactly the case
leg two exists for: it stays on `_actual_lmp_coverage` / `price_reference_blocked_years`, pinned by
`test_silent_for_a_stored_iso_whose_run_years_lack_a_bench`. An unreadable store (`{}`, what the loader
yields on `OSError`/bad JSON) cannot establish absence for anyone, so the class is silent — pinned by
`test_silent_when_the_store_is_unreadable`. And because the code path reduces to
`skipped_physical == skipped_downgrading` whenever the predicate is False, a series-carrying ISO's
payload is the same bytes with the store present or emptied — pinned by
`test_series_iso_payload_is_byte_identical_with_and_without_the_class`, and measured on the seven
keepers above.

**Why it is never a PASS and never an upgrade** (rule 22 guard (d), transposed): the price records are
not rewritten — they keep SKIPPED, so `grade_summary.target_grade` (which counts PASS only) never
absorbs them; neither string equals `CALIBRATED` or starts with it, so every equality consumer in
the repo reads the class as not-calibrated; governance FAIL/UNATTESTED, any FAIL and both caveat
budgets are evaluated before the branch and are untouched (`test_governance_failure_still_not_yet`,
`test_physical_fail_still_not_yet`); physical caveats still downgrade the physical rung and the label
carries that rung (`test_physical_caveats_carry_into_the_caveats_string`). Against what the SAME run
reads at this pin — `CALIBRATED-WITH-CAVEATS`, a label that read alone says the price was tested and
mildly missed — the class is strictly more explicit and no higher. Against the same run scored WITH a
series (CALIBRATED or NOT-YET) it certifies less than either: it is a statement of what was not tested.

**Stated rather than hidden:** `main()` exits nonzero only on `NOT-YET`, so the class exits 0 exactly
as the `CALIBRATED-WITH-CAVEATS` reading it replaces does. The exit-code contract was not touched.

## 2. RUBRIC_VERSION — stays 3.7, and the reading

The header's precedents show the stamp moving when a registered run's payload moves (v3.4 one row,
v3.5 every payload, v3.7 one reason line) and staying when none does (the 2026-09-06 entry). The
stamp is itself a byte of every payload; this lane's exit is zero moved bytes; the two are consistent
only with **3.7 unchanged**. The header entry records this in the 2026-09-06 form. Cost, stated: the
first NWPP verdict will carry stamp 3.7 while reading a class the 3.7 text did not describe until this
entry — mitigated by the self-describing label and the `price_unscored` block. A bump at NWPP
registration is possible but moves every keeper's stamp byte, so it is a desk/owner decision.

## 3. Tests

New file `tests/scoring/test_verdict_price_unscored.py`, synthetic artifacts only, the store injected
through `cv._ACTUAL_LMP_CACHE` (as the tail part is through `cv._TAIL_CACHE`), the "priceless" ISO
deliberately a made-up key rather than NWPP (the predicate is data-driven, so the name is irrelevant):

| test | pins |
|---|---|
| `test_cannot_fire_for_an_iso_carrying_a_series` | PJM in the store with a bench LMP: C3a/C3b PASS, no `price_unscored`, predicate False |
| `test_fires_for_an_iso_carrying_none` | the exact string; basis line first; headline leads with it; price criteria SKIPPED and not in `target_grade`; `price_unscored` block on verdict and condensed sidecar; `render_text` line |
| `test_silent_when_the_store_is_unreadable` | leg one |
| `test_silent_for_a_stored_iso_whose_run_years_lack_a_bench` | leg two (the MISO-2020-alone shape) |
| `test_silent_when_a_scored_year_carries_a_bench_actual` | leg three (inconsistent artifacts) |
| `test_governance_failure_still_not_yet`, `test_physical_fail_still_not_yet` | ordering guards |
| `test_physical_caveats_carry_into_the_caveats_string` | the `-WITH-CAVEATS` twin |
| `test_strings_are_never_calibrated` | the constants, the rung map, the reference path spelling |
| `test_series_iso_payload_is_byte_identical_with_and_without_the_class` | the lift reduces to the old list |

`uv run python -m pytest -q tests/scoring/test_verdict_price_unscored.py tests/scoring/test_calibration_verdict.py
tests/scoring/test_rubric_consts.py` → **172 passed, 1 failed** — the failure is
`test_coverage_threshold_sits_in_an_empty_interval` and it **fails at the base sha with this lane's
changes stashed** (verified: `git stash -u`, run, same failure). Cause: MISO 2021 `da_cov.mon` carries
`0.9677`, landed by `5e6d3224` ("Stage MISO 2020 and 2021 hub LMP") before this base; the test asserts
no coverage value sits in (0.3653, 0.9911). Not this lane's file (constraint 3: the coverage
machinery is not widened into) — **routed to NWPP-DESK / the MISO lane** as a pre-existing red at
`33a7c961`. `tests/scoring/test_audit_keepers.py`, `test_holdout_render_parity.py`,
`test_dashboard_add_run_sidecar.py`: 25 passed. `ruff check` / `ruff format --check` clean on both files.

## 4. Gate G15 — `scripts/check_mechanism_matrix.py --base 33a7c961`, OUTPUT

```
mechanism-matrix: integrity OK (docs/codebase-site/data/mechanism-matrix.js + 7 ISO shards)
mechanism-matrix: anchors checked (206 field + 51 row + 206 path; skipped 39 non-field token(s) and 4 unresolvable path(s)) — 257 unresolvable beyond the ratchet
mechanism-matrix: keeper stamps match every keepers/<ISO>.json
mechanism-matrix: §5.x prose headers match every keepers/<ISO>.json
mechanism-matrix: gap ratchet OK (no ISO-scoped field is invisible)
mechanism-matrix: shared ratchet OK (no keeper arms an unregistered shared field)
mechanism-matrix: absent-shared ratchet OK (every shared field is registered or baselined)
```

(plus 14 pre-existing `::warning` anchor-drift lines for rows this lane never touched, byte-identical
to the base run). No `ScenarioConfig` field was added, so no matrix row, no cache-key movement, no
bundle change; existing keepers re-score in place. Rule 28(c) does not fire.

## 5. Routed to NWPP-DESK — consumers that do not yet know the class (none edited; none mine)

Every determination consumer was read. All are fail-closed against the new strings today; each is
listed so the registration lanes (NWPP-20/40) know what to teach and the desk can sequence it:

| consumer | today's reading of the class | note |
|---|---|---|
| `docs/codebase-site/js/calibration-status.js` `detClass`/`detLabel` | unknown string → `det-not` / "NOT CALIBRATED" | fail-closed; the owner's ruling wants the basis-naming label visible on the page, so the status renderer needs a case for it |
| `scripts/build_status.py` `_det_rank` (partition fold) | no "NOT"/"CAVEAT" substring → rank 2, tied with CALIBRATED | matters only for a config-PARTITIONED keeper; a partitioned NWPP keeper would need its own rank |
| `scripts/audit_keepers.py` `_DET_TOKENS` / E5 | a shard prose asserting the class is read as its "CALIBRATED" substring and E5 goes RED against the live string | fail-closed; add the token when NWPP registers |
| `docs/codebase-site/js/viz-rubric-scorecard.js` | `=== 'CALIBRATED'` false | fail-closed |
| `main()` exit code | 0 (same as the replaced CALIBRATED-WITH-CAVEATS route) | unchanged by design |

Also routed: the pre-existing `test_coverage_threshold_sits_in_an_empty_interval` red (§3). And the
open question NWPP-13 already routed — option (i) unscored price (this class) vs option (ii) a
labelled imbalance benchmark — is unaffected: if the desk ever lands (ii), it presents to the scorer
as a series in the store and this class does not fire; (ii)'s label is a new owner ruling, not this
branch.

## 6. Rules, files, verification

Rules 1 (no criterion tuned, widened or softened; the branch was never evaluated by whether it
improves anyone's determination — its exit is that it changes no one's), 5 (two strings, one path, one
criteria tuple, all named), 22 (the template, guard for guard), 26 (nothing zeroed; nothing left
re-armable), 27 (Edit tool only; exact bytes pushed; fetch-back verified immediately: remote blob
`8908830a27e9bf2551bc2f8daa2eadddab85656e` = local, 4,008 lines, sha256
`ca97ec68…3d64a8` identical), §8.0 (no shared record touched). **Files touched:**
`scripts/calibration_verdict.py`, `tests/scoring/test_verdict_price_unscored.py` (new),
`docs/handoffs/PRECOMMIT-nwpp-22-2026-09-13.md`, this FINDING. Nothing under `src/`, `frontend/data/**`,
`data/raw/`, any registry, ISO config, keeper shard, bundle, `TAIL_THRESHOLD`, the matrix, the plan,
the ledger, or `docs/calibration-log/nwpp.md`. No LP ran; no shard was launched.

## Log entry

### nwpp-22 — 2026-09-13

**PRICE-UNSCORED determination class (card N2 limb b): BUILT, 7/7 keepers byte-identical.** PRECOMMIT
pushed before the scorer was edited. One added branch in `scripts/calibration_verdict.py`: a run whose
ISO has NO admissible hourly price series — no record in `data/raw/_validation-source/actual_lmp.json`,
no LMP actual in any scored year, C3a/C3b/C3c all SKIPPED — reads **`PHYSICALLY CALIBRATED — PRICE
UNSCORED (no admissible hourly price series)`** (or its `-WITH-CAVEATS` twin from the physical rung)
instead of a bare `CALIBRATED-WITH-CAVEATS`, with the three price criteria named FIRST on the basis and
a structural `price_unscored` block. Predicate data-driven and ISO-level, never an ISO name; fail-closed
on rule 22's pattern (never PASS, never CALIBRATED, after governance/FAIL/budgets, silent for any ISO
the store names or when the store is unreadable). No criterion, band, tier, budget, `TAIL_THRESHOLD` or
standing rule moved; no `ScenarioConfig` field; RUBRIC_VERSION stays 3.7 (zero registered payloads
move). Nine synthetic tests in `tests/scoring/test_verdict_price_unscored.py`. Routed: status-page /
`_det_rank` / `audit_keepers` token cases for the new class; pre-existing red
`test_coverage_threshold_sits_in_an_empty_interval` (MISO 2021 `da_cov` 0.9677, landed `5e6d3224`).
`FINDING-nwpp-22-2026-09-13.md`.
