# ADDENDUM neiso-104 — G-DRIFT audit: the keeper is NOT a valid control, and the audit does not cost seconds

**Written BEFORE any arm is solved**, per rule 29(b) `[R-SCREEN]` ("the audit is recorded in the
PRECOMMIT (or its addendum) before the arm is solved, so it cannot be written to fit the result").
Amends `PREREG-neiso104-fossil-offer-level-2026-09-06.md` §4 phase 0. **Zero LP minutes at
writing.**

---

## 1. Headline

**G-CTRL form 4 is VOID for this lane. The NEISO keeper's committed bundle cannot serve as the
control, and a control solve on the screen year is earned** under rule 29(b)'s LIVE-hunk clause.

Two findings, the second of which is about the rule rather than about NEISO:

1. **The drift is large and lands on the NEISO backcast path.** 160 solve-path files changed
   between the keeper's `git_sha` and HEAD, 131,626 line-changes, of which **28,119 across 111
   files are live candidates** — including `data/offer_curves.py` (**the mechanism's own path**),
   `pipeline/solve.py` (the P0→P1 seam), `data/fleet/campd_bins.py` (NEISO runs
   `use_campd_bins=True`), `data/outages.py`, `model/reserves/spec.py`, `runner.py` and
   `results/cache.py`.
2. **Rule 29(b)'s cost premise fails at this staleness.** The rule states G-DRIFT "costs seconds"
   and is "*stronger* than a control solve … a control solve shows that two numbers differ, while
   the audit says which line did it". That holds against a keeper days old. **NEISO's keeper is
   from 2026-08-17 — three weeks and 111 live-candidate files behind HEAD** — and a hunk-by-hunk
   classification of 28,119 lines is neither seconds nor proportionate to one screen. This is
   filed as a rule-mechanics observation for the owner, not as grounds to skip the audit: the
   lane is taking the *stricter* branch (spend the control), not the cheaper one.

---

## 2. Method, and a resolution defect worth recording

The rule's audit command is
`git diff <keeper git_sha> HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`.

**The keeper's recorded `git_sha` `b7904a1` did not resolve on first attempt** — this session's
checkout is a **shallow** clone whose history began 2026-09-05, three weeks after the keeper.
`git rev-list -1 --before=<date>` against that truncated history returned **empty**, and an empty
anchor silently produces an **empty diff** — i.e. a false "no drift, all INERT" G-DRIFT result
obtained by asking the question wrong. It was caught because an empty diffstat on a three-week-old
keeper is not credible, and the clone was then deepened
(`git fetch --filter=blob:none --shallow-since=2026-08-15`), after which `b7904a1` resolves as
`b7904a1db60a3f08ce6b8247bebceeab3f9ae7ae`, *Add neiso-99 arm-decomposition probe*, 2026-08-17
09:48:59 +0000, and the real diff appears.

**Filed for the program, not acted on here:** any lane running G-DRIFT in a shallow checkout can
get a clean-looking all-INERT answer from a truncated history. The audit should assert that the
keeper `git_sha` resolves before trusting its output. This lane's own guard was disbelief at the
result, which is not a guard.

## 3. The triage

Bucketed by path over `git diff --numstat b7904a1 HEAD` on the rule's own file set:

| bucket | line-changes | share |
|---|---:|---:|
| OTHER-ISO branch (CAISO / MISO / NYISO / PJM / ERCOT-scoped paths) | 99,020 | 74 % |
| **LIVE CANDIDATE — NEISO backcast path** | **28,119** | **21 %** |
| FORECAST-ONLY (capacity evolution, policy, ensemble — a `mode="backcast"` run never enters) | 6,641 | 5 % |

Largest live candidates:

| lines | file | why it is not dismissible |
|---:|---|---|
| 5,531 | `config/scenarios.py` | the config surface the recipe is built from |
| 1,952 | `config/capacity_market.py` | forecast-leaning but reached from shared config |
| 1,487 | `scripts/run_calibration_full.py` | the entry point itself |
| 1,266 | `runner.py` | the P0→P1 solve loop |
| 1,253 | `config/constants.py` | shared constants incl. offer-path literals |
| 775 | `data/fleet/eia860.py` | fleet build |
| 750 | `data/outages.py` | NEISO's availability envelope |
| 652 | `results/cache.py` | incl. the capx-D79 solve-surface fingerprint in `cache_key()` |
| 635 | `data/fleet/campd_bins.py` | **NEISO runs `use_campd_bins=True`** |
| 610 | `model/reserves/spec.py` | the RCPF co-opt NEISO arms |
| 553 | `pipeline/solve.py` | the P0→P1 seam |
| **391** | **`data/offer_curves.py`** | **the band multipliers' own consumption path** |
| 384 | `data/fleet/arrays.py` | the SoA the LP reads |

`data/offer_curves.py` alone settles it: the object this lane tunes is consumed by a file that has
moved 391 lines since the keeper solved. **Declaring that INERT without reading every hunk would
be exactly the "files changed, therefore \<verdict\>" heuristic rule 29(b) forbids — in the
permissive direction, which is the worse one.**

## 4. Consequence for the plan

PREREG §4 is amended:

- **Phase 1 spends TWO solves on the screen year 2025, not one**: the **arm** (scalar 0.9547 on
  the 12 bands of PREREG §2.1) and a **same-HEAD control** (the incumbent keeper recipe, zero
  scenario deltas). Launched as **separate concurrent invocations** with their own `--out-dir`,
  per rule 12 `[R-PARALLEL]` (cap ~2 for per-plant multi-zone LPs — this is exactly 2); years are
  not parallelised because each invocation solves one year.
- **The screen gates of PREREG §4 are differenced arm-vs-control at the same HEAD**, not
  arm-vs-committed-keeper. This is what the control buys and it is strictly more correct.
- **Both bundles are deleted before the PR merges** (rule 29(c) — the clause covers "any control
  bundle a screen earns under (b)'s LIVE-hunk case" explicitly). Every number either bundle
  produces is carried in the FINDING doc.
- **Nothing else in the PREREG moves.** The declared scalar is unchanged at 0.9547, the estimator
  is unchanged (owner-selected: geometric mean), the screen year is unchanged at 2025, and the
  §3.3 pre-registered landings stand as written.

## 5. A finding this earns independently of the arm

The control solve measures **the incumbent NEISO keeper's recipe at HEAD against its own committed
2025 numbers**. If those differ materially, **NEISO's designated keeper is stale relative to
HEAD** — a governance fact about the ISO's dashboard determination, independent of anything this
lane proposes, and one no session has measured since 2026-08-17. It is reported either way in the
FINDING, and **it is not this lane's to act on**: a stale-keeper repair is its own lane with its
own promotion, and the C3c lone-failure fragility noted in PREREG §6.1 makes that the owner's call.

