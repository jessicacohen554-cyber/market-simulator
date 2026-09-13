# PRECOMMIT — SOCO-22: the no-price determination class (rubric v3.8)

**Lane** SOCO-22 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/soco-22-rubric-determination-cnoxsz` · **Base** `33a7c961` (origin/main, pinned) ·
**Data profile** `code` · **Rulings** card S2 (2026-09-13, desk r#2) and card S11 (2026-09-13, desk r#3);
coordinated with NWPP card N2 (ruled 2026-09-13, both limbs) and NWPP-13's NO
(`docs/handoffs/FINDING-nwpp-13-2026-09-13.md`).

Written and pushed BEFORE the scorer is edited. Every design choice below is fixed here so the
implementation cannot be shaped to a result; the FINDING reports against this text.

## 0. What is being added, in one sentence

One determination branch in `scripts/calibration_verdict.py::determine_from_artifacts`, reachable only
by a region that has **no `actual_lmp.json` block at all**, under which a run that is clean on
C1/C2/C4/C6/C8 reads a determination that names its own basis and is never `CALIBRATED`.

## 1. The predicate — keyed on absence, never on a name

`_price_reference_absent(iso) -> bool` is **True iff the committed
`data/raw/_validation-source/actual_lmp.json` has no top-level key for `iso`**. It reads the same
committed reference `_actual_lmp_coverage` already reads, through the same module cache. No ISO name
appears anywhere in the predicate or the branch.

The branch fires only when **both** legs hold:

| leg | test | why it is there |
|---|---|---|
| (i) | `_price_reference_absent(iso)` | the S11 ruling's key, verbatim: "keyed on the ABSENCE of an `actual_lmp.json` block" |
| (ii) | C3a, C3b **and** C3c are `SKIPPED` at the per-criterion level — no scored record in any year | fail-closed: a bench that somehow carried a price the reference does not (a hand-built part) still scores the ordinary way; the branch can never override a scored price criterion |

**Fail-closed on the file.** If `actual_lmp.json` is unreadable the predicate returns **False** —
absence cannot be established, so the run reads exactly as it does today. (The file is tracked in git
and present in every profile, `code` included, so this is a guard, not an expected path.)

**What the predicate does for the three cases the charter names:**

| region state | block? | branch? | reading |
|---|---|---|---|
| **ABSENT** — SOCO: no public price, SEEM's auditor series disqualified on four grounds (SOCO-12 §0.2) | no | **yes** | the new class |
| **REJECTED** — NWPP: WEIM series built, STOP gate D3 read NO, `gate --land` refused, nothing in `_validation-source` (NWPP-13 §0, §4) | no | **yes** | the new class — NWPP-13 §4 option (i), its own recommendation for the first keeper |
| **PARTIAL** — a block exists but some years have no record (MISO 2020/2021 today; NWPP 2023 Jun–Dec if N2 option (ii) is ever ruled) | yes | **no** | the ordinary rubric, unchanged: scored years score, unscored years are `price_reference_blocked_years`, per-criterion aggregation (PASS beats SKIPPED) means a partial series never reaches this branch and never downgrades on the missing years |

A rejected series never lands (`gate --land` refuses on NO), so **absence IS the rejection signal**;
no flag is invented. If a desk later rules a labelled series in (NWPP option (ii)), the block appears and
the ordinary rubric takes over on its own — the branch retires itself with no code change.

**What the predicate does NOT do:** it does not look at `price_reference_blocked_years`, at the ISO
registry, at `TAIL_THRESHOLD`, or at any per-year condition. A region with a block but no scorable
year for this run is the PARTIAL row above — the existing `CALIBRATED-WITH-CAVEATS` / "unscored
criteria" reading — because that is a property of the run's years, not of the region.

## 2. The determination strings — proposed final wording, and why

```
PHYSICALLY_CALIBRATED         = "PHYSICALLY-CALIBRATED (PRICE UNSCORED)"
PHYSICALLY_CALIBRATED_CAVEATS = "PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)"
```

- **`PHYSICALLY-CALIBRATED`** is the owner's own example wording (card S2) and it is accurate: the
  criteria that remain are physical-quantity criteria — C1 fuel mix, C2 system volume, C4 hourly
  dispatch correlation — plus the two protective gates C6/C8.
- **`(PRICE UNSCORED)` replaces the example's `no public price exists`.** The scorer can observe only
  that no committed benchmark exists; it cannot know *why*. For SOCO the why is "no public price exists"
  (true); for NWPP it is "two public prices exist and both were refused as benchmarks" — so the
  example's clause would be **false on the second region this amendment serves**. The label states the
  observable fact; the determination-basis line names the ISO and the file; the plan and the FINDING
  docs carry the why.
- **Two rungs, mirroring the existing ladder.** A single label would read the same for a run carrying
  a C2 commercial-band caveat as for a clean one — information the ordinary ladder carries, and
  dropping it would soften the class. On the criteria it does score, this class is exactly as strict
  as the ordinary one.
- **Hyphenated upper-case tokens**, the grammar of `CALIBRATED-WITH-CAVEATS` / `NOT-YET`, so
  `audit_keepers._DET_TOKENS` can be extended by two tokens longest-first (routed, §6).
- **Never `CALIBRATED`, by construction:** neither string equals `CALIBRATED` or
  `CALIBRATED-WITH-CAVEATS`, and a test pins that.

## 3. What the branch does, route by route

The branch sits **after** the governance, FAIL and caveat-budget checks, which are untouched, so every
`NOT-YET` route is byte-identical for every ISO:

| route | today | on the branch |
|---|---|---|
| C6 not PASS | `NOT-YET` | `NOT-YET`, unchanged |
| any FAIL on C1/C2/C4/C8 | `NOT-YET` | `NOT-YET`, unchanged |
| caveat budget exceeded | `NOT-YET` | `NOT-YET`, unchanged |
| otherwise, no band/protective caveat, no other unscored criterion, no data-blocked year | `CALIBRATED-WITH-CAVEATS` ("unscored criteria: price_mean, price_shape") | **`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`** |
| otherwise, with a band or protective caveat, another unscored criterion, or a data-blocked year | `CALIBRATED-WITH-CAVEATS` | **`PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)`**, with the same reason lines |

Mechanically: on the branch the three price criteria are removed from `skipped_downgrading` (C3a/C3b)
and from `skipped_exempt` (C3c, v3.7) and named **together** on the basis line instead — so the v3.7
"not determination-downgrading" line is not emitted for C3c there, because on a region with no price
at all C3c is unscored for the same reason as C3a/C3b, not for the model-class reason v3.7 names.

**The price gap on the determination basis, at full magnitude, on EVERY route** — including
`NOT-YET`, so a failing no-price run can never be read as having failed on price. The line is
appended **last** (the existing convention for the v3.3 ledgered line and the v3.7 exempt line, so it
never displaces a downgrading reason from `headline()`'s `reasons[0]`; on the clean rung it is the
only reason and therefore the headline). Its content:

> `PRICE UNSCORED — no actual_lmp.json block exists for <ISO>, so C3a mean LMP, C3b price
> duration/shape and C3c price tail / scarcity are NOT SCORED in any year (<years>); this
> determination is scored on C1/C2/C4/C6/C8 ONLY and certifies NO price level, shape or tail (owner
> ruling card S2, 2026-09-13; rubric v3.8). It is not a CALIBRATED reading. Model system
> load-weighted mean LMP, MODEL-ONLY and UNVERIFIED — no measured reference exists to compare
> against: <year: $x.xx/MWh, …>.`

The model's own annual mean price is reported so the unverified quantity is visible at full size,
labelled model-only so it cannot be mistaken for a scored number.

**A `price_unscored` block is added to the verdict dict ONLY on the branch** (the `span_restricted`
pattern), carrying `basis`, `criteria_unscored`, `scored_on`, `model_mean_lmp_by_year`. No key is added
to any other run's verdict — that is what keeps the seven keepers byte-identical.

`render_text` prints the block when present; `condensed_metrics` carries it when present.
`main()`'s exit code is unchanged (non-zero on `NOT-YET` only).

## 4. What is NOT touched — the scope fence

No existing criterion's tier, band, threshold, caveat budget, `LEDGERABLE_CRITERIA`,
`_apply_ledger`, `_apply_c3c_standing_rule` (rule 22 `[R-C3C]`), `_no_price_reason`,
`price_reference_blocked_years`, or any scorer function. No ISO name list. No `TAIL_THRESHOLD`.
No file outside `scripts/calibration_verdict.py`, `tests/scoring/`, and these two docs. If the
implementation needs any of those, the lane STOPS.

`RUBRIC_VERSION` moves **3.7 → 3.8**, because this IS a rubric change (a new determination class);
the neiso-107 entry records the opposite case (not bumped because not a rubric change). It is the one
field of every existing verdict that moves, and §5 states it as such rather than hiding it.

## 5. The byte-identity protocol — the HARD EXIT

Pre-change snapshot, taken at `33a7c961` before any edit (this session,
`scratchpad/snapshot.py`): for **every registered run (14)**, the full-span verdict JSON
(`sort_keys=True, indent=2`), the `render_text` block, and a per-year `--years <y>` verdict for each
scorable year — 68 files. After the change the identical script runs again and the two trees are
diffed.

**Pass condition:** for all 14 runs and every per-year subset, the JSON differs in **exactly one
line** — `"rubric_version": 3.7` → `3.8` — and the `render_text` output differs in **zero** lines.
Every category, row, status, classification, magnitude and reason string is byte-identical. The seven
keepers are the exit; the other seven registered runs and the per-year ladders are reported as
additional measurement. Any other diff line is a STOP.

Also reported: the full `tests/scoring/` lane before and after, with the one pre-existing failure
(present at `33a7c961` before any edit; named in the FINDING) identified as not this lane's.

## 6. Tests to be added — `tests/scoring/test_calibration_verdict_price_unscored.py`

1. **Reached** — synthetic artifacts, `iso="SOCO"` (no block in the committed reference), no `avgLMP`,
   C1/C2/C4/C8 clean, C6 attested → `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; C3a/C3b/C3c `SKIPPED`;
   `price_unscored` present; the basis line names the ISO, the file and all three criteria.
2. **Unreachable with a block, price absent** — the same artifacts, `iso="PJM"`, no `avgLMP` →
   `CALIBRATED-WITH-CAVEATS` with "unscored criteria: price_mean, price_shape" (today's reading);
   no `price_unscored` key. **And with a block, price present** → `CALIBRATED`; no key.
3. **Unreachable by leg (ii)** — `iso="SOCO"` but the bench carries an `avgLMP` → C3a scores, ordinary
   path, no key.
4. **Never CALIBRATED** — the new strings are distinct from all three existing labels, and the clean
   no-price run's determination is not `CALIBRATED`.
5. **NOT-YET preserved** — `iso="SOCO"` with a C1 FAIL → `NOT-YET`; `reasons[0]` is the FAIL line;
   the price-unscored line is present and last.
6. **Caveat rung** — `iso="SOCO"` with a C2 commercial-band miss →
   `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)`, band reason first, price line last.
7. **Predicate** — `False` for each of the seven registered ISOs, `True` for `SOCO` and `NWPP`,
   `False` for everything when the reference path is unreadable (fail-closed).
8. **Registered runs** — every registered run's verdict carries no `price_unscored` key and none of
   the new labels (the durable form of the §5 proof).

## 7. Routed, not done here (outside this lane's files)

- `docs/calibration-determination-rubric.md` — needs a v3.8 entry; the FINDING quotes the paragraph
  to paste.
- `scripts/audit_keepers.py::_DET_TOKENS` — add the two new tokens longest-first before any
  no-price keeper is registered, or E5 will read `PHYSICALLY-CALIBRATED` as its `CALIBRATED` substring.
- `docs/codebase-site/js/calibration-status.js::detClass/detLabel` — an unknown label renders
  `NOT CALIBRATED` (red). Conservative until taught, but SOCO's W2/W4 registration lane must teach it.
- `_MULTI_YEAR_ISOS` in `audit_keepers.py` gains `SOCO` in W2 (plan §3 defaults), not here.
