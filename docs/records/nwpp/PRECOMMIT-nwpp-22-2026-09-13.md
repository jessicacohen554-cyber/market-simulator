# PRECOMMIT — NWPP-22: the determination class for an ISO with NO admissible hourly price series (card N2 limb b)

**Lane** NWPP-22 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/nwpp-22-verdict-basis-wkmyv5` · **Base** `33a7c961` (`origin/main` at launch; the
charter's pin) · **Data profile** `code` · **Charter** `docs/multi-iso/nwpp-addition-plan-2026-09.md`
§5 row NWPP-22 / §7 gate G25 · **Ruling** card N2 limb (b), sitting #1, verbatim: *"a failed gate yields
a determination naming its own basis, never a bare CALIBRATED, with the price gap on the determination
basis at full magnitude"*; issued under owner ruling N11, "send it now".

**This document is pushed BEFORE the scorer is edited.** The predicate, the exact strings, every guard,
the RUBRIC_VERSION reading and the byte-identity protocol are fixed here, ex ante. A guard designed after
the diff is seen is not a guard (charter, verbatim), and the exit of this lane is a byte-identity proof
whose meaning depends on the protocol having been written first.

---

## 0. What was read, and what the scorer sees today

Read in full before this document: CLAUDE.md (rule 22 `[R-C3C]` as the template, rule 1 `[R-STRUCT]` as
the constraint); the module header of `scripts/calibration_verdict.py` (v2 → v3.7, plus the 2026-09-06
"NOT A RUBRIC CHANGE" entry); `_apply_c3c_standing_rule`; `CRITERIA`; `_actual_lmp_coverage`;
`determine_from_artifacts` end to end; plan §2.6, §3 cards N2 and N11, §5 NWPP-22, §7 G6/G15/G17/G25;
`FINDING-nwpp-13-2026-09-13.md` §0 and §3.

**What an ISO with no price series presents to the scorer today, traced through the code, not assumed:**

| stage | what happens for such an ISO | where |
|---|---|---|
| bench parts | `frontend/data/backcast/bench/<ISO>/` holds no `avgLMP` → `ybench["avgLMP"]` is `{}` | `load_artifacts`, `score_price_mean` |
| C3a | `actual is None` → SKIPPED, reason `_no_price_reason` ("no measured LMP reference on disk … UNSCOREABLE") | `score_price_mean` |
| C3b | `actual_mon is None` → SKIPPED, same reason family | `score_price_shape` |
| C3c | no `TAIL_THRESHOLD`/`actual_tail.json` record → SKIPPED ("no committed RT actual tail") | `score_price_tail` |
| reported-only | `price_reference_blocked_years` = every scored year | `determine_from_artifacts` |
| determination | gov PASS, no FAIL → else-branch → `skipped_downgrading` = `[price_mean, price_shape]` → **`CALIBRATED-WITH-CAVEATS`**, reason "unscored criteria: price_mean, price_shape" + the v3.7 C3c exempt line | `determine_from_artifacts` |

So at this pin an NWPP run with clean physical criteria would read **`CALIBRATED-WITH-CAVEATS`** — a label
that, read alone, says the price was tested and mildly missed. That is the defect card N2(b) names.

**The committed price-reference store the scorer already reads** is
`data/raw/_validation-source/actual_lmp.json` (`_ACTUAL_LMP_PATH`, read by `_actual_lmp_coverage`). It is
git-tracked, present in the `code` profile, and keyed `ISO → year → {rt, da, rt_mon, …}`. At `33a7c961`
its keys are exactly the seven registered ISOs: `ERCOT PJM CAISO NYISO NEISO MISO SPP`. NWPP is absent.
The bench `avgLMP` block is built from this store by `render_calibration_html._actual_avg_lmp`, so the
store is the stdlib-visible form of "an admissible hourly price series was landed for this ISO".

---

## 1. The predicate — data-driven, ISO-level, fail-closed

The branch fires **iff ALL of the following hold**, evaluated inside `determine_from_artifacts` after the
existing governance / FAIL / budget rungs (so it is unreachable from any of them):

| # | condition | why it is there |
|---|---|---|
| P1 | The committed price-reference store is **readable and non-empty** (it names ≥ 1 ISO) | if the store cannot be read, absence cannot be established → the branch is SILENT and the existing unscored route stands. A missing file must never fire this for every ISO at once |
| P2 | The ISO being scored has **no record at all** in that store (`store.get(iso)` is empty) | this is the ISO-level test the charter requires: an ISO that HAS a series — for ANY year, even years outside this run (MISO 2020–2021 scored alone in a per-year ladder) — never reaches this branch. Partial or per-year absence stays with `_actual_lmp_coverage` / `price_reference_blocked_years`, untouched |
| P3 | The run has ≥ 1 scorable year, and **every** scorable year is in `price_reference_blocked_years` (no bench `avgLMP` for any of them) | belt-and-braces consistency: a bench that somehow carries a price for an ISO the store does not name is an inconsistent artifact set → SILENT, criteria score as today |
| P4 | `per_criterion` status is **SKIPPED** for all three of `price_mean`, `price_shape`, `price_tail` | nothing was scored; if any price criterion holds a PASS/CAVEAT/FAIL the branch is SILENT |

No `if iso == "NWPP"` anywhere. The predicate covers both failure modes the charter names — "no series was
ever built" and "a series was built and its STOP gate refused it" — identically, because a refused series
is never landed to the store. NWPP-13's verdict changes nothing in this code; it changes only whether P2
holds for NWPP.

Helper: `_price_series_absent(iso, scorable_years, price_reference_blocked, per_criterion) -> bool`,
stdlib-only, reading the store through the existing `_ACTUAL_LMP_CACHE` (so tests inject it exactly as
they inject `_TAIL_CACHE`).

---

## 2. The exact strings an unscoreable-price ISO will read

Two determination constants, one per physical rung, so the physical half's reading is never upgraded
by the price half's absence:

```
PHYSICALLY_CALIBRATED_PRICE_UNSCORED = (
    "PHYSICALLY CALIBRATED — PRICE UNSCORED (no admissible hourly price series)"
)
PHYSICALLY_CALIBRATED_CAVEATS_PRICE_UNSCORED = (
    "PHYSICALLY CALIBRATED-WITH-CAVEATS — PRICE UNSCORED (no admissible hourly price series)"
)
```

Mapping: the existing else-branch computes its rung over the **physical** downgrading items only (the two
price skips are lifted out of `skipped_downgrading` on this path and nowhere else); a rung of `CALIBRATED`
maps to the first string, `CALIBRATED-WITH-CAVEATS` to the second. The label form follows card N2's own
example (`PHYSICALLY CALIBRATED — …`).

**The reason line, emitted FIRST in `reasons`** (so `headline()`'s `reasons[0]` leads with the basis),
for the absence case (card N2 limb (b), option (i) of NWPP-13's routing — no series at all):

```
PRICE UNSCORED — no admissible hourly price series for <ISO>: no record in
data/raw/_validation-source/actual_lmp.json and no LMP actual in any scored year (<years>). C3a mean
LMP, C3b price duration/shape and C3c price tail / scarcity were NOT TESTED — they read SKIPPED, never
PASS, and are excluded from grade_summary. This determination certifies the PHYSICAL criteria only
(C1 fuel-mix, C2 system volume, C4 dispatch correlation, C6 governance, C8 forced share) and is NEVER
a CALIBRATED reading (owner ruling, card N2 limb (b), 2026-09-13). Per-year: <year>: <the SKIPPED
record's own reason>; …
```

The per-year clause carries each price record's own `_no_price_reason` text — that is the "full
magnitude" available when no series exists: which criteria, which years, why. (The "price gap at full
magnitude" wording of the ruling describes option (ii) — a landed-but-labelled imbalance benchmark — which
nobody has built and which this lane does not build; if the desk ever lands one, it will present to the
scorer as a series and this branch will not fire.)

A structural block travels with the verdict, present ONLY when the branch fires (the `span_restricted`
pattern, so every other payload is byte-identical):

```
"price_unscored": {
    "iso": <ISO>, "reference": "data/raw/_validation-source/actual_lmp.json",
    "years": [...], "criteria": ["price_mean", "price_shape", "price_tail"],
    "physical_rung": "CALIBRATED" | "CALIBRATED-WITH-CAVEATS"
}
```

`condensed_metrics` and `render_text` carry it only when present.

---

## 3. The guards — and how I know it is never an upgrade

| guard | statement | rule-22 analogue |
|---|---|---|
| G-a | **Never a PASS.** C3a/C3b/C3c keep status SKIPPED; no record is rewritten; `grade_summary.target_grade` counts only PASS, so it can never absorb them | guard (d) |
| G-b | **Never CALIBRATED.** Neither string equals `CALIBRATED`, and any consumer testing `== CALIBRATED` (calibration-status.js `detClass`/`detLabel`, viz-rubric-scorecard.js, audit_keepers E5) reads it as NOT calibrated — fail-closed by construction | guard (d) |
| G-c | **Ordered after every downgrading rung.** Governance FAIL/UNATTESTED → NOT-YET; any FAIL → NOT-YET; budget breach → NOT-YET — all evaluated before this branch, unchanged | guards (a)–(b) |
| G-d | **Physical caveats still downgrade.** Band caveats, protective caveats, other unscored criteria (C1/C2/C4/C8) and data-blocked years keep producing the WITH-CAVEATS rung and their reason lines; only the two price skips are lifted, and only because they are named on their own line | v3.7 pattern |
| G-e | **Narrow.** P1–P4 above; the branch cannot fire for any ISO with a record in the store, and cannot fire when the store is unreadable | guard (c) |
| G-f | **No existing criterion, band, tier, budget, `TAIL_THRESHOLD` entry or standing rule moves.** The diff is additive: two constants, one reason constant, one helper, one lift inside the else-branch, one optional output block | charter (5) |

**How I know it cannot make a run read better than the same run scored WITH a series.** A run with a
series reads `CALIBRATED` (price passes, or lone ledgered C3c) or `NOT-YET` (a price criterion fails).
The same run with no series reads `PHYSICALLY CALIBRATED — PRICE UNSCORED (…)`, which (i) is not
`CALIBRATED` and is read as not-calibrated by every equality consumer in the repo, (ii) names in its
own label and its first reason line that three criteria — two of them load-bearing — were not tested,
and (iii) stamps `price_unscored` on the payload so no downstream can miss it structurally. It is a
statement of what was not tested, on the one ladder rung the ruling authorised, and it certifies less
than either outcome a series would produce. Relative to what the SAME run reads at this pin
(`CALIBRATED-WITH-CAVEATS`, whose label implies a tested-and-mildly-missed price) it is strictly more
explicit and no higher: the physical rung is carried unchanged into the new label, so a physically
caveated run cannot shed its caveats through the price half.

**One thing stated rather than hidden.** `main()` exits nonzero only on `NOT-YET`; the new class exits 0,
exactly as the `CALIBRATED-WITH-CAVEATS` reading it replaces does today. The exit-code contract is not
touched (touching it would touch existing behaviour).

---

## 4. RUBRIC_VERSION — the header's own convention, read before the edit

Four precedents in the header decide when the stamp moves:

| entry | registered payloads moved? | stamp |
|---|---|---|
| v3.4 | one C1 row flipped | bumped |
| v3.5 | every payload gained the `reported` block | bumped |
| v3.7 | one run's reason line split | bumped |
| 2026-09-06 "NOT A RUBRIC CHANGE" | **zero** | **stayed 3.6** |

The operative convention, read from what happened rather than from any one sentence: **the stamp moves
when a registered run's verdict payload moves; it stays when none does.** `rubric_version` is itself a
byte of every payload, and this lane's exit is ZERO moved bytes over every keeper. The two demands are
consistent only one way: **RUBRIC_VERSION stays 3.7.** A header entry records the added class and this
reading, in the 2026-09-06 form. Cost stated: the first NWPP verdict will carry stamp 3.7 while reading a
class 3.7's text did not describe until this entry — which is why the entry is written in the header and
why the class is self-describing in its label and its `price_unscored` block. A bump at NWPP
registration would move every keeper's stamp byte and is a desk/owner decision, not this lane's.

---

## 5. The byte-identity protocol

1. At `33a7c961`, BEFORE any edit: `python3 scripts/calibration_verdict.py --run-id <id> --json` for
   each designated keeper read from `frontend/data/backcast/keepers/*.json` at this base (not from
   the charter's list) — saved as `scratch/before/<id>.json`. **Done before this document was written**;
   determinations at base: CAISO CALIBRATED · ERCOT CALIBRATED · MISO NOT-YET · NEISO CALIBRATED ·
   NYISO NOT-YET · PJM CALIBRATED · SPP CALIBRATED.
2. AFTER the edit: the same seven commands → `scratch/after/<id>.json`.
3. `cmp` / `sha256sum` per keeper on the FULL JSON payload. **Zero bytes may move.** One moved byte
   is a STOP: reported, not explained.
4. Also run: the existing `tests/scoring/test_calibration_verdict.py` (must stay green) and the new
   `tests/scoring/test_verdict_price_unscored.py`.
5. `python3 scripts/check_mechanism_matrix.py` — OUTPUT pasted in the FINDING (gate G15). No
   `ScenarioConfig` field is added, so no matrix row and no cache-key movement.

Keepers at base (read from the tree): `2026-09-12-caiso-275-gascoupling` ·
`2026-09-09-ercot265-receipts-fallback` · `2026-09-12-miso-255-sil-measured` ·
`2026-09-09-neiso-108-fuelvintage` · `2026-09-13-nyiso231-anchor-span` · `2026-09-11-pjm-d4-4-gasoutage`
· `2026-09-13-spp-38-vintage-cache` — identical to the charter's list.

---

## 6. Tests (new file `tests/scoring/test_verdict_price_unscored.py`, synthetic fixtures, no registry)

- **cannot fire** for an ISO carrying a series (store names it; bench carries `avgLMP`) — payload
  byte-identical to the pre-change route, no `price_unscored` key;
- **cannot fire** for an ISO the store names when the run's years lack a bench (the MISO-2020-alone
  shape) — stays `CALIBRATED-WITH-CAVEATS` with "unscored criteria" (P2);
- **cannot fire** when the store is unreadable/empty (P1);
- **fires** for an ISO carrying none → exact string, first reason line, `price_unscored` block, price
  statuses SKIPPED, `target_grade` excludes them;
- **physical caveat variant** → the `-WITH-CAVEATS` string and the caveat reason lines still present;
- **guards**: governance FAIL → NOT-YET; a physical FAIL → NOT-YET; label never `== CALIBRATED`.

---

## 7. Rules this lane is bound by

1 `[R-STRUCT]` (no criterion tuned, widened or softened; never evaluated by whether it improves a
determination) · 5 `[R-NO-MAGIC]` (two strings and one path, all named constants) · 22 `[R-C3C]`
(the guard template) · 26 `[R-DELETE]` (nothing zeroed; nothing left re-armable) · 27 `[R-PUSH]`
(`calibration_verdict.py` is 3,813 lines: Edit tool only, exact on-disk bytes, fetch-back blob verify
immediately after every push) · §8.0 (no shared record; one FINDING + this PRECOMMIT; no matrix row;
no registry; no `frontend/data/**`; no `src/`).
