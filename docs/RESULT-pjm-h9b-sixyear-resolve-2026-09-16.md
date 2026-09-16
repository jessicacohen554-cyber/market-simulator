# RESULT (pjm-h9b) — the six-year keeper-recipe re-solve at HEAD is a **NULL REPRODUCTION**.
# NOT a keeper candidate, and it is not registered.

**Session** `pjm-h9` · **ISO** PJM · **Date** 2026-09-16 · **Pinned SHA** `fa1703335ea8bed04f8a34717d297d7096caa84f`
**Six shards, one per year** (owner instruction: *"Launch shards for each year and don't bother
with a screen"*). Parent ran no LP (rule 32 `[R-SHARD]` (a)).
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**

Per-year is not a fan-out choice here, it is forced: **PJM's keeper is PARTITIONED** — 2020–2022
run the `pjm_d4_4_TP` recipe and 2023–2025 the `pjm_d4_4_A` carve-out, so one `--years` invocation
cannot express the span. Every shard pushed its **full 17-file bundle including
`dispatch/<year>_P1.parquet`** (rule 34 `[R-SHARD-PROMOTABLE]` (a)), so any of them can back a
promotion with zero re-solves.

---

## 1. RESULT — it reproduces the incumbent, to three decimal places

| year | max \|keeper − re-solve\| (TWh) | worst class |
|---|---:|---|
| 2023 | **0.0726** | CC_REGULAR |
| 2024 | **0.0065** | CT_CHP |
| 2025 | **0.0018** | CT_CHP |

**Nothing moved.** The recipe is the keeper's, the inputs are the keeper's, and HEAD has drifted
`f09eddbe → fa170333` without touching PJM's backcast path. That is the useful negative: it is a
**HEAD verification of the designated keeper across its whole registered span**, and it passes.

## 2. C1, all six years, band ±8.00 TWh

| year | C1 | failing classes |
|---|---|---|
| 2020 | **17/18** | COAL_BIT **+22.84** (153.97 vs 131.14) |
| 2021 | **16/17** | CC_REGULAR **+17.01** (305.54 vs 288.53) |
| 2022 | **16/17** | CC_REGULAR **+12.81** (319.69 vs 306.88) |
| 2023 | **17/17** | — |
| 2024 | **17/17** | — |
| 2025 | **16/17** | COAL_BIT **+8.40** (133.83 vs 125.43) |

The training years are the keeper's published headline exactly. The held-out years carry the
same misses the committed touchpoint already reports, and under rule 30 `[R-TOUCHPOINT-FOLD]` (c)
they do not touch PJM's determination.

## 3. THE JUDGEMENT — **NOT a keeper candidate**

The owner's standard is *"if structural integrity improves but gates regress that **may** still be
a keeper."* Here **neither moves**: the configuration is byte-identical to the incumbent's, so
there is no structural gain to weigh and no regression to forgive. A promotion would swap one
recipe for the same recipe.

What the run *does* establish, and it is worth having:
* the keeper still solves clean at HEAD, across **all six** registered years;
* every year now has a **retrievable per-plant bundle at one pinned SHA**, which is what rule 35
  `[R-PROMOTE]` (c)'s year-union coverage needs the day a real candidate arrives;
* the 2021/2022 hourly sidecars are freshly solved, which is the input the standing
  display-stale `volErr`/`nonFosErr` escalation was waiting on.

**NOT REGISTERED, deliberately.** These are six per-year bundles of the *designated keeper's own
recipe*. Registering them would create six runs that are neither PJM's keeper nor stamped to it —
exactly the orphan state `audit_keepers` **E13** exists to fail (rule 35 `[R-PROMOTE]` (f)) — and
would breach rule 15 `[R-DASHBOARD]`'s keeper-only retention. Rule 32 `[R-SHARD]` (d) puts the
composition seam in the parent, and the parent's judgement is that a null reproduction composes to
nothing worth a dashboard card.

## 4. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

All six are **on `origin`**, full per-plant layer, recovery by FULL immutable SHA:

```
2020  7f6f8f616069c7cf72931c9789bf64ef4b5f2110
2021  9b238fc2b9b87dd14fa1784f33920b759c533989
2022  37a64db4269c80548f8a7c19175e16e6f6069ecf
2023  220e170d6353ef9d563185f93f0482da5be52a61
2024  a380ff476e02fb365db605e51197c293812f2529
2025  30f2367894a321f2a3f60697fb27c4fb890a4b63
git checkout <sha> -- results/calibration/pjm_h9_<year>
```

Verified in the parent by checkout + config signature on every one: `git_sha fa170333`,
`iso PJM`, `years [<year>]`, `pjm_offer_midcurve_minload_segments` **null** (the keeper recipe,
not the pjm-h8 arm). The same SHAs are written into `.gitignore` beside the bundles.
**A promotion from this state costs ZERO re-solves for any year.**

## 5. WHAT IS STILL OPEN

* **The holdout-year FIX itself is not in this run.** PJM's measured offer surface covers
  **2023–2025 only**; 2020–2022 read the surface's **pooled fallback** — a 2023–25 average standing
  in for measured data PJM publishes (DataMiner2 retention is indefinite from 2017-11-01). Extending
  it is a rule 14 `[R-ACCURATE]` repair with **zero free parameters** and zero new fields. The
  2020–2022 corpus is being fetched; the derive then re-runs over 2020–2025 and the
  **2023–2025 ladders must be re-checked**, because `_unit_physics` computes segment membership over
  every year given to it and adding three years can move a unit between segments.
* pjm-h7's and pjm-h8's promotions remain open and untouched.

## 6. RULES

Rule 1 `[R-STRUCT]` (no mechanism selected; nothing tuned) · rule 15 `[R-DASHBOARD]` (§3 — why a
null reproduction is not registered, against keeper-only retention) · rule 16 `[R-ALLYEARS]` /
rule 34 `[R-SHARD-PROMOTABLE]` (c) (every registered year solved) · rule 29 `[R-SCREEN]` (its
screen-year regime was removed by owner instruction this session; clause (c) governs what reaches
`main` and is discharged by `.gitignore`) · rule 30(c) (held-out years do not touch the
determination) · rule 31 `[R-RETAIN]` (nothing deleted; the promotion question is put to the owner
in §3) · rule 32 `[R-SHARD]` (a)(d) (the parent ran no LP and owns the seam) · rule 33
`[R-SHARD-ARCHIVE]` (fetched, checked out, verified, then archived; recovery by full SHA) ·
rule 34 (a)(e) (every shard pushed its bundle with the per-plant layer; §4 states retrievability) ·
rule 35 `[R-PROMOTE]` (f) (§3 — registering these would create exactly the E13 orphan state).
