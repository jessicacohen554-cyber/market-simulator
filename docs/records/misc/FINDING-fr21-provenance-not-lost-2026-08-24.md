# FINDING — FR-21: the forecast board's provenance stamps were never lost

**Date:** 2026-08-24 · **Lane:** FR-21 provenance restore · **Verdict:** NO LOSS
OCCURRED. The prime suspect (`8452e1c`, the v12 gate-(a) re-key) is **exonerated
by direct measurement**. Nothing was restored, and nothing was minted.

## 1. The report

A director measurement on 2026-08-23 at `a13da3c` read:

```
  newest scored sha   : (none recorded)
  stamped / scored    : 0 stamped, 0 scored
  distinct epochs     : 0
  WARN: The forecast board carries NO provenance stamps at all …
```

One cycle earlier, at `1b8ddac`, the same check read **39 stamped / 8 scored /
8 epochs**. The stamps looked lost between those two heads, and the suspected
mechanism was the records-lane gate-(a) re-key rewriting the seed without
carrying provenance forward.

## 2. The measurement that settles it

`scripts/check_forecast_staleness.py` reads `BOARD_PATHS`. Two of the three are
tracked: `frontend/data/forecast/ff-verdicts.json` and `frontend/data/hindcast`
(the third, `frontend/data/forecast/registry`, is gitignored and generated). So
the question is answerable entirely from git.

**(a) Every blob the check reads is byte-identical across the window.**

| path | `1b8ddac` | `a13da3c` | HEAD (`c9a07b9`) |
|---|---|---|---|
| `frontend/data/forecast/ff-verdicts.json` | `f4ee783fdc` | `f4ee783fdc` | `f4ee783fdc` |
| `frontend/data/hindcast/caiso-2021-2025-realized.json` | `eddc6a5625` | `eddc6a5625` | `eddc6a5625` |
| `frontend/data/hindcast/ercot-2021-2025-realized-t1h-refresh.json` | `0ccd5082d1` | `0ccd5082d1` | `0ccd5082d1` |
| `frontend/data/hindcast/pjm-2021-2025-realized-k162.json` | `db95a66844` | `db95a66844` | `db95a66844` |
| `scripts/check_forecast_staleness.py` | `7efcd5761a` | `7efcd5761a` | `7efcd5761a` |
| `scripts/lib/forecast_provenance.py` | `31e6e081f2` | `31e6e081f2` | `31e6e081f2` |

**(b) The check, run at `a13da3c` from `a13da3c`'s own tree, reads 39/8/8** —
identical to `1b8ddac`. Reproduce with `git archive <sha> -- scripts
frontend/data/forecast/ff-verdicts.json frontend/data/hindcast` into a temp dir
and running the extracted script there. Measured at `1b8ddac`, `bea4181`,
`8452e1c`, `a13da3c` and HEAD; the counts never move.

**(c) `8452e1c` is the ONLY commit in `1b8ddac..HEAD` touching the namespace**,
and it changed **one file, five lines**: `program-status.json`, which is not even
a `BOARD_PATH`. Inside it, two gate-(a) `detail` strings and the
`gate_a_provenance` block's `derived_at_sha` / `derived_at_date` / `derived_by`.
Those field names are deliberately outside `forecast-provenance/v1`
(`PROVENANCE_FIELDS = scored_at_sha, scored_at_date, cache_epoch`) precisely so a
re-key cannot be misread as a re-score — the design worked. **No stamp was
touched, moved or removed.** The file's own stamp (its `refresh` block's
`scored_at_sha: e2a422c1`) survives on both sides.

**(d) The director's own cycle-A record corroborates it**: the release plan's
audit entry reads "newest scored sha `8084b135` is **not reachable in this
checkout** … across 8 distinct config cache epochs"
(`docs/model-audit-release-plan-2026-08.md`). That is the board *with* its
stamps, at the same vintage.

## 3. What actually produced the 0-stamp reading

Deleting the two tracked board inputs from an otherwise-correct `a13da3c` tree
reproduces the reported output **exactly**, warning text included. That is the
only way to reach `0 stamped`: `fp.collect_stamps` is total — it skips
unreadable and unstamped files silently — so an absent file and an unstamped file
are indistinguishable in its output.

So the reading was **a measurement taken against a tree that did not hold the
board**, rendered by the check as a finding *about the board*. The attribution is
environmental (an incomplete checkout), not a content loss, and no repository
change is implicated.

## 4. Nothing to restore — and why no stamp was minted

Scope item 2 asked for a restore. There is nothing to restore: the committed
inputs carry their stamps, unchanged since before the suspected commit. Minting
fresh stamps would have written "scored at HEAD" over verdicts scored at
`8084b135` on 2026-08-22 (and FF-2D's on 2026-07-20) — the exact failure the
charter names as worse than no stamp. **No stamp was written.**

Board position at HEAD is unchanged from `1b8ddac`: newest scored sha
`8084b135ed8d`, dated `2026-08-22T16:40:08Z`, 8 scored records, 8 epochs. That
sha is **not reachable in this checkout** — expected, and left alone: the
2026-08-16 history rewrite orphaned pre-rewrite shas
(`docs/FINDING-history-rewrite-2026-08-16.md`), and an unreachable true sha beats
a reachable false one. Staleness stays **UNKNOWN**, which is not the same as
fresh.

## 5. The guard

The defect worth fixing is the one that cost this session: **the check could not
distinguish an absent board from an unstamped board**, and asserted the stronger,
false claim. `scripts/check_forecast_staleness.py` now:

- splits `BOARD_PATHS` into `BOARD_INPUTS_COMMITTED` (tracked — absence is a
  defect) and `BOARD_INPUTS_GENERATED` (gitignored, Pages-deploy-written —
  absence is normal and stays silent, so `registry/` never nags);
- reports `BOARD INPUT(S) MISSING` first, naming each, and **suppresses** the
  "carries NO provenance stamps at all" claim whenever any input is absent;
- renders a `board inputs` line on every run.

It also adds `frontend/data/forecast/program-status.json` to the watched set.
That is the file the records lane re-keys, it carries a v1-readable stamp, and it
was unwatched — watching it is what makes a re-key that *does* drop its stamp
visible instead of silent. Board stamp count consequently reads **40** rather
than 39; the newest scored sha is unchanged, because that stamp carries no date
and can never become newest.

Five tests in `tests/scoring/test_forecast_staleness.py::BoardInputPresenceTests`
pin the behaviour, including a standing regression guard that every committed
board input exists in the checkout. WARN-only contract untouched; the check still
exits 0.

## 6. Not done, deliberately

No verdict, gate reading or determination was changed. Gate (a)'s three passers
(PJM, NYISO, NEISO) and every ISO's HOLD stand. No solve, no re-score, no
registration; nothing outside 2023–2025 touched ([R-HOLDOUT] rule 22 — freeze
active, `final` empty). Only committed inputs were considered; the generated
namespace was not written.
