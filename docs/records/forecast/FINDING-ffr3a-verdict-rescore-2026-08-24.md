# FINDING — FFR-3A: 7 of 39 forecast verdicts survive; the board's "newest scored" headline was masked by hindcast sidecars

**Date:** 2026-08-24 · **Lane:** FFR-3A verdict re-score · **Charter:**
`docs/forecast-development-plan-2026-07.md` §7.5; FR-21 (staleness detection),
FFR-3A (re-score the battery through the stamped scorer).
**Predecessor:** `docs/FINDING-fr21-provenance-not-lost-2026-08-24.md` — the
stamps were never lost; that question stays closed.

**Headline.** The T1 battery's source artifacts mostly **do not survive**, and
that is the result, not a gap to be filled by re-solving. **7 of the 39** board
verdicts can be re-scored from committed artifacts; they were re-scored and now
carry real stamps. The other **32 are unrecoverable without an LP solve**, by
design rather than by accident. Separately, the FR-21 detector was reproducing
the very failure mode it exists to catch, and that is fixed.

---

## 1. Feasibility (scope 1) — the coverage measurement

**The mapping is committed, not inferred.** `register_forecast_run.VERDICT_MAP`
is the run_id → verdict-key table the registrar itself uses. Crossing it against
tracked score artifacts under `results/hindcast/` and tracked
`full_horizon_summary.json` bundles gives:

| | count | verdicts |
|---|---|---|
| mapped, source bundle **tracked** | **7** | the 4 `*-curve-*-t1h` and the 3 `*-t1x-ffr2a` |
| mapped, source bundle **absent** | 15 | `<iso>-t1f`, `<iso>-t1x`, all `*-ffr3a3-*`, `*-ffr3a4-*` |
| **unmapped** (no `VERDICT_MAP` entry) | 17 | every `*-ff2d`, `<iso>-t1h`, `miso-t1x` |

**The 7 re-scorable verdicts are exactly the 7 that carried no provenance stamp
at all.** That coincidence is the whole shape of the problem: the entries the
board could verify were the ones nobody had stamped, and the entries carrying
stamps were the ones nobody can verify.

### Why the other 32 are gone

They are **gitignored by design**, not lost. `results/ffr3a2/README.md`:
*"Everything under here except this README is gitignored"* — only the README and
`scorecard/` are tracked; `results/ffr3a3/` says the same. The scorer's inputs
(`full_horizon_summary.json`, the `check_forecast_invariants.py` output,
`run_config.json`) never entered the repository. Re-creating them requires a
full-horizon LP solve, which the charter forbids and which would not reproduce
the original verdict anyway (a different HEAD, a different config cache key).

**Near-misses that are NOT identifications.** Four tracked CAISO control arms
reproduce `caiso-t1f`'s FC-1 and FC-2 detail strings exactly — and all four are
excluded by the board verdict's own FC-7 row, which records **671 config keys**
against their 677 / 681 / 672 / 672. Likewise `nyiso-t1f-ff2d` is matched
identically by two different bundles at two different cache keys, so neither is
identified. Substituting any of them would attach a fresh stamp to a verdict
that may not describe it — the exact thing the charter names as worse than no
stamp.

---

## 2. The re-score (scope 2) — 7 done, no determination moves

Run through `scripts/rescore_forecast_verdicts.py --apply`, which shells out to
`scripts/forecast_verdict.py`; every value written is the scorer's own output on
committed artifacts. **All 7 were HOLD and remain HOLD**, so no §2.1b gate
reading changes. Rule 22 `[R-HOLDOUT]` holds throughout: every source artifact
records `scored_years [2023, 2024, 2025]` — the 2021 hindcast seed and 2022
bridge are legal *solve* years that are never scored — and the tool fails closed
on anything else.

### Movement A — FC-7 CAVEAT → FAIL (all 7). A stricter scorer, not a worse model.

The current scorer emits an explicit `run_config.json absent` FAIL row where the
older one silently omitted the row. None of the 7 bundles tracks a
`run_config.json`, so **FAIL is the true reading of the committed record**.

### Movement B — FC-1 / FC-2 → SKIPPED on the 3 t1x entries. Report this one.

Their previous readings came from a `check_forecast_invariants.py` output that
**was never committed**. Only `crossover_score.json` and `meta.json` are tracked
for those bundles, and the invariant checker needs the gitignored per-year
dispatch parquets and evolution ledgers. So the old readings are not reproducible
from any checkout — they were unverifiable evidence, which is precisely what
FR-21 exists to surface. FC-4, the tier's **primary gating instrument**,
reproduces **byte-identically**, which is also what identifies these bundles.

The superseded readings, preserved here because the board no longer carries them:

- **`ercot-t1x-ffr2a`** — FC-1 `FAIL`: `FAIL ['I12','I3','I6','I7']: I12: scalar
  floor [13.8%, 28.7%]; out: 2024:30.2%, 2025:10.8%, 2026:6.5%, 2027:7.1%; I3:
  2027: slack 0.02% of load; I6: 2025: 26.9% of thermal retired in one year; I7:
  2025: thermal 57437 < retirement-bounded floor 78527 MW`. FC-2 `FAIL` on the
  same I12 band.
- **`miso-t1x-ffr2a`** — FC-1 `FAIL`: `FAIL ['I9']: I9: 2025: simultaneous
  chg+dis 0.23% of throughput; 2026: 0.10%; 2027: 0.84%`. FC-2 `PASS`.
- **`pjm-t1x-ffr2a`** — FC-1 `PASS`, FC-2 `PASS`.

**PJM's t1x loses two PASS readings.** That is the real cost of this lane and it
should be read as one: the board is now more *reproducible* and, on those two
rows, less *informative*. Recovering them honestly needs the invariants artifact
committed alongside the crossover score — a registrar change, not a re-score.

### Movement C — schema only (the 4 t1h entries)

`FC-2/FC-4/FC-5/FC-6` go from absent to `"n/a"`: the legacy sidecar omitted
non-applicable categories, the `forecast-verdict/v1` sidecar records them. FC-3's
band set is **identical**; only the rendering changed (compact-brace →
list repr).

---

## 3. The masking defect (scope 3) — the FR-21 detector had the FR-21 bug

**Measured before the fix:** the board's newest scored stamp was
`8084b135ed8d @ 2026-08-22T16:40:08Z` — a **hindcast sidecar**. The FC verdicts
that gates (b) and (c) rest on were 31-of-32 UNSCORED, with FF-2D's dating from
2026-07-20. A fresh artifact of one class was hiding staleness in another,
through a single collapsed `max()` over every stamp on the board.

`scripts/check_forecast_staleness.py` now measures and renders **per class**
(`CLASS_BY_INPUT`: verdicts / hindcast sidecars / seed / registry / other) and
drives the warning off `GATING_CLASS` = the verdicts. Two new warnings:

- **`FRESHER NON-GATE ARTIFACTS`** — a non-gate class scored more recently than
  the verdicts is named, and does not make the gate evidence fresher. A hindcast
  sidecar is an *input to* a future verdict, never a substitute for one.
- **partly-scored gate evidence** — one re-scored verdict beside thirty unscored
  ones is not a scored board, so the unscored count is reported regardless of
  what the newest scored one says.

**Old vs new on one fixture** (verdicts scored 2026-07-20 at distance 99; sidecar
scored 2026-08-22 at distance 0):

| | newest | Δ | stale | warnings |
|---|---|---|---|---|
| old | `freshfresh12` (sidecar) | 0 | **False** | none — reads FRESH |
| new | gate = `stalestale12` | **99** | **True** | both of the above |

Five new `ArtifactClassTests` pin it; **all five fail against the pre-fix
module**. The 23 prior tests pass untouched — when no verdict artifact is among
the measured paths the check falls back to the whole board, so every existing
caller is unchanged. WARN-only contract intact: the script still exits 0 and CI
still invokes it without `--fail-on-stale`.

### What the live board says now

```
  gate evidence       : verdicts
  newest scored sha   : 4fc57ecdd57a  @ 2026-08-24T05:28:39Z
  per class           :
      hindcast sidecars      7 stamped,   7 scored, newest 8084b135ed8d @ 2026-08-22T16:40:08Z
      seed                   1 stamped,   0 scored, newest (none)
      verdicts              39 stamped,   8 scored, newest 4fc57ecdd57a  <- gate evidence
  WARN: 31 of 39 verdicts stamps record no scored-at date …
```

Note that **the re-score alone would have made this worse**: with 7 verdicts
freshly stamped, the pre-fix check read `OK: the board's evidence is current with
HEAD` while 31 verdicts remained unscored. The class split is what keeps that
honest.

---

## 4. Sha normalization (scope 4) — 20 expanded, 0 left short

Nineteen verdict stamps and the seed's `refresh` block carried 8-char shas,
because `merge_ffr3a2_verdicts._sha` and `build_ffr3a2_scorecard.scored_at_sha`
stamp with `git rev-parse --short HEAD` instead of
`forecast_provenance.head_sha()`. Both prefixes resolved against the GitHub
commit API to **exactly one** commit each, and each commit corroborates the
session named in the stamps' own `session` field:

| prefix | full sha | commit | stamps |
|---|---|---|---|
| `8ba59281` | `8ba592814d921122cf9cb1121a0f3c080f7c6938` | "FFR-3A-2: the per-ISO §2.1b gate scorecard", 2026-08-04 | 13 verdicts |
| `e2a422c1` | `e2a422c191aa693a3fbc4f94b407deee99b8268f` | "FFR-3A-3: PJM T1-X post-FFR-3F", 2026-08-04 | 6 verdicts + seed |

These are **expansions of the same commit, never substitutions**. Neither is
reachable locally — this is a **shallow clone (2 grafts, 255 commits)**, so local
absence proves nothing either way — and neither appears in
`docs/governance/citation-commit-map.txt`. Had a prefix failed to resolve
uniquely it would have stayed at 8 characters.

**Deliberately not touched:** `derived_at_sha` (the records lane keeps those
field names outside `forecast-provenance/v1` precisely so a re-key cannot read as
a re-score) and the seed's `solved_at_sha: 941f4983`, which records where a leg
was *solved* rather than *scored* and is not a provenance stamp. It remains
8 chars, noted here rather than changed.

---

## 5. Not done, deliberately

- **No LP solve.** No T1-F / T1-X / T1-H re-run, no `full_horizon_summary`
  regeneration. Where a solve was the only route to an honest stamp, the answer
  is "unrecoverable", recorded above.
- **No hand-edited gate reading or determination.** Gate (a)'s three passers
  (PJM, NYISO, NEISO) and every ISO's HOLD stand; all 7 re-scores returned HOLD.
- **Backcast namespace untouched.** No keeper shard, no
  `calibration-complete.json`, no `holdout-freeze.json` (freeze **ACTIVE**,
  `final` **EMPTY**, no locked-test year spent by any ISO).
- **Nothing written to the generated namespace** (`registry/`, `runs/`,
  `manifest.js`, `program-status.js`) — the Pages deploy is their single writer.
- **No stamp minted.** The 32 unrecoverable verdicts keep whatever they had; none
  was given a fresh date it did not earn.

## 6. Open items for a successor

1. **The registrar should commit the invariants artifact** next to each
   crossover/hindcast score. That is the one change that would have made
   Movement B unnecessary, and it makes future t1x verdicts reproducible.
2. **`merge_ffr3a2_verdicts` and `build_ffr3a2_scorecard` should stamp through
   `forecast_provenance.head_sha()`** rather than `git rev-parse --short`, so no
   new 8-char sha reaches the board.
3. **The 32 unrecoverable verdicts stay unverifiable** until their tier is
   re-solved and registered with committed scorer inputs. Until then the board's
   staleness reading is honest about them — 31 of 39 verdict stamps carry no
   scored-at date, and the check now says so on every run.
