# ADDENDUM to PRECOMMIT-miso251 — the 2021 and 2020 rungs ARE worth solving, and my own §5 stop rule was too strict

**Written BEFORE either rung is solved** (the 2022 shard is still in its LP), so this cannot be a
rationalisation of a result. ZERO LP.

## What §5 said, and why it was wrong

`PRECOMMIT-miso251-holdout-ladder-2026-09-10.md` §5.2 pre-registered:

> **No LP is spent on a rung whose load-bearing criteria cannot be scored.**

I wrote that having established only that MISO's **price** bench is missing for 2020/2021 (the hub
staging aged off; the Data Exchange fallback needs `MISO_PRICING_API_KEY`, absent). I then treated
"the price family is unscorable" as if it were "the load-bearing family is unscorable". **It is
not.** C1 `fuelmix` and C2 `sysvol` are load-bearing too, and they are scored against EIA-923 /
EIA-930, which have nothing to do with MISO's LMP retention.

## The measurement that corrects it

`scripts/audit_eia923_completeness.py`, MISO, per class:

| class | 2020 | 2021 | 2022 |
|---|---|---|---|
| CC_REGULAR | COMPLETE | **COMPLETE (gate-eligible)** | COMPLETE |
| CC_CHP | COMPLETE | **COMPLETE (gate-eligible)** | INCOMPLETE (1/22) |
| CT_PEAKER | COMPLETE | **COMPLETE (gate-eligible)** | COMPLETE |
| CT_CHP | COMPLETE | **COMPLETE (gate-eligible)** | COMPLETE |
| ST_GAS | INCOMPLETE (2/40) | **COMPLETE (gate-eligible)** | COMPLETE |
| ST_CHP | COMPLETE | **COMPLETE (gate-eligible)** | COMPLETE |
| COAL_PRB | COMPLETE | INCOMPLETE (pm 95%) | INCOMPLETE (pm 97%) |
| COAL_LIGNITE | COMPLETE | INCOMPLETE (pm 91%) | INCOMPLETE (pm 85%) |
| COAL_BIT | INCOMPLETE (4/34) | COMPLETE | INCOMPLETE (1/29, pm 96%) |
| **complete** | **7 / 9** | **7 / 9**, and the **whole gas family** | **6 / 9** |

2021 is the *best-benched* of the three: MISO's entire gas family is COMPLETE and gate-eligible —
better than 2025, where all 8 classes are SKIPPED on the preliminary vintage. Contrast the
in-sample keeper, whose 2025 C1 scores nothing at all.

## So what each rung actually buys

| | C1 | C2 | C3a/C3b/C3c | C4 | C6 | C8 |
|---|---|---|---|---|---|---|
| **2022** | 6/9 classes | yes | **yes** (10 fully-staged months) | yes | yes | yes |
| **2021** | **7/9, gas family complete** | yes | **NO — no LMP bench** | yes | yes | yes |
| **2020** | **7/9** | yes | **NO — no LMP bench** | yes | yes | yes |

Two of the four load-bearing criteria, plus the supporting dispatch-correlation criterion and both
protective gates, score on every rung. A never-tuned year's **volume and mix** generalization is
exactly the thing a validation touchpoint exists to expose, and it is available here.

## The revised stop rule (this supersedes PRECOMMIT §5.2)

1. **2022** first, as charted.
2. **2021 and 2020 are solved** if 2022 clears — as **two independent single-year touchpoint
   bundles, launched in parallel**, each registered and each stamped to the keeper with its own
   `--holdout-year`. Not one two-year span shard: rule 32 `[R-SHARD]` (b) caps a shard commit at
   20 minutes and a two-year MISO span is ~40, and the shard protocol §3's warning about composing
   per-year shards does not apply because **nothing is composed** — each is its own registered
   bundle, so each year keeps its own input snapshot. They write disjoint paths
   (`registry/<id>.json`, `runs/<id>.js`, `bench/MISO/<year>.json.gz`), so parallel is safe.
3. **Their determinations will read `CALIBRATED-WITH-CAVEATS` at best**, on `unscored criteria:
   price_mean, price_shape` — and that is a **DATA fact about MISO's LMP retention, not a model
   result**. It is reported as such on the rung, on the status ladder and in the session log; it is
   NOT a model miss, and under rule 30(c) it cannot move MISO's determination either way.
4. Everything else in the PRECOMMIT stands unchanged — same frozen recipe, same single declared
   ASM degradation (§3), no tuning, no control solve.

## Why this is a strengthening, not a loosening

The original rule would have spent nothing and learned nothing on two years whose **fuel-mix bench
is better than the keeper's own 2025**. The revision spends two parallel ~20-minute shards and
returns a load-bearing volume/mix reading on two never-tuned years, with the price gap stated at
full magnitude rather than papered over. No band moves, no criterion is waived, and no unscorable
criterion is quietly counted as a pass — an unscored load-bearing criterion still downgrades the
rung exactly as the rubric says it must.
