# RESULT (pjm-h9c) — giving PJM 2020–2022 their OWN measured offer ladders is a
# **RECOMMENDED KEEPER CANDIDATE**: structure improves, the determination does not move,
# and the held-out regression is the defect pjm-h8 named

**Session** `pjm-h9` · **ISO** PJM · **Date** 2026-09-17 · **Pinned SHA** `73a682347d175fd001c8a5cfcd08e3241d03c82e`
**Six shards, one per year.** Parent ran no LP (rule 32 `[R-SHARD]` (a)). No control solved —
G-CTRL form 4 against `docs/RESULT-pjm-h9b-sixyear-resolve-2026-09-16.md`'s six bundles (same
recipe, same HEAD, same pinned SHA). **No screen** — that regime was removed by owner
instruction 2026-09-16 (`rule-history.md` §21).
Pre-registration: `docs/PRECOMMIT-pjm-h9c-offer-surface-own-year-2026-09-16.md`.

---

## 1. RESULT

| year | | COAL_BIT | CC_REGULAR | CT_PEAKER | C1 |
|---|---|---:|---:|---:|---|
| **2020** | control | 153.97 (+22.8 ✗) | 290.64 (+7.6 ✓) | 19.33 (+0.7 ✓) | 16/17 |
| | **arm** | **162.22 (+31.1 ✗)** | 287.45 (+4.5 ✓) | 18.05 (−0.5 ✓) | 15/16 |
| **2021** | control | 152.06 (−3.7 ✓) | 305.54 (**+17.0 ✗**) | 15.82 (−5.5 ✓) | 16/17 |
| | **arm** | **177.28 (+21.5 ✗)** | **289.74 (+1.2 ✓)** | **12.83 (−8.5 ✗)** | 14/16 |
| **2022** | control | 143.63 (+3.1 ✓) | 319.69 (+12.8 ✗) | 17.02 (−2.1 ✓) | 16/17 |
| | **arm** | 144.50 (+3.9 ✓) | 319.13 (+12.3 ✗) | 16.93 (−2.1 ✓) | 15/16 |
| **2023** | arm − control | **−0.02** | **+0.00** | **+0.01** | **16/16 unchanged** |
| **2024** | arm − control | **−0.00** | **+0.01** | **+0.00** | **16/16 unchanged** |
| **2025** | arm − control | **+0.00** | **+0.00** | **−0.00** | **15/16 unchanged** |

> **The in-sample years are byte-identical.** The zero-LP prediction (PRECOMMIT §3) is confirmed
> empirically to ≤ 0.02 TWh, so **PJM's calibration determination does not move at all** — it is
> the train-tier verdict and nothing else (rule 30 `[R-TOUCHPOINT-FOLD]` (c)).

## 2. THE JUDGEMENT — **RECOMMEND PROMOTE**

Against the owner's standard (*"if structural integrity improves but gates regress that **may**
still be a keeper"*), this is the case that standard describes, and on the cleanest possible
terms:

* **Structural integrity improves unambiguously.** The surface carried own-year ladders for
  2023–2025 only, so 2020/2021/2022 were priced from `pooled` — a capacity-weighted blend **of
  2023–2025** — an average of years that had not happened yet. Each year now reads its
  publisher's own measured offers. **Zero free parameters, zero new `ScenarioConfig` fields,
  nothing swept** (rules 21/24). Rule 14 `[R-ACCURATE]` does not merely permit this, it
  *requires* it.
* **The gates that regress cannot reach the determination.** 2021 loses COAL_BIT and CT_PEAKER
  and **gains CC_REGULAR** (+17.0 → +1.2); 2020 worsens a FAIL that was already a FAIL; 2022 is
  inert. All three are held-out years, and rule 30(c) is explicit that a held-out year never
  downgrades the ISO.
* **The cost is paid in the right currency.** Rule 14: *"If swapping a hand estimate for real
  data makes the backcast worse, that is a signal that something else in the model is
  miscalibrated and the estimate was silently compensating for it… Do not bury the error back
  inside an inaccurate input."* The pooled blend was compensating. Reverting to it to protect a
  held-out number is exactly what the rule forbids.

## 3. WHAT THE REGRESSION MEASURES — it corroborates pjm-h8 §5 directly

2021's own-year ladder sits **1.9–2.5 implied-HR below** the pooled value it replaces (~$10/MWh
at 2021 delivered gas) on 12.5 GW of coal `committed` capacity. The dispatch response:

> **COAL_BIT +25.22 TWh, CC_REGULAR −15.80 TWh, CT_PEAKER −2.99 TWh.**

A ~$10/MWh move on one rung of one class relocates **25 TWh**. That is the same hyper-elastic
merit order pjm-h8 measured from the other direction (pricing coal's min-load block at PJM's own
offers sent COAL_BIT −12.70 TWh), and it is the strongest evidence yet for **route (a)**: the LP
carries **no minimum-run or minimum-down constraint at all**, and PJM is the only large ISO here
with **no P1-native commitment bridge** where CAISO, ERCOT, NYISO, SPP and MISO each have one
(`RESULT-pjm-h9-comparator-admixture-bound` §5). Real PJM coal cannot swing 25 TWh on a $10
offer change because it is committed; the model's can, because nothing stops it.

**Reported, and it gated nothing** (rule 1 `[R-STRUCT]`): the PRECOMMIT fixed every reading
before the corpus finished downloading and no criterion in it reads a residual.

## 4. THE PRE-REGISTERED RISK — measured and disproven

| | |
|---|---|
| **D-1 segment stability** | CT_FAST 1064→2455, CC_LIKE 883→1603, LONG_RUN 216→477 |
| **D-2 in-sample ladder drift** | 129 of 432 cells, **median 0.0**, p90 0.145, 73 up / 56 down |
| **D-3 vs the reproduction floor** | **AT OR BELOW** — restatement noise, not this change |

D-1's apparent explosion is **masks, not units**: PJM re-keys the masked `unit_code` between
vintages, so one physical unit appears as several masks across six years. That is why D-2 holds —
a 2020–2022 mask never contributes to a 2023–2025 unit's median physics. **The same masking that
defeated pjm-h9's coal-only classification is what makes the six-year derive safe**, and the
byte-identical in-sample solves in §1 confirm it in dispatch rather than only in the ladder.

## 5. THE PROMOTION, AND WHY IT IS THE TOUCHPOINT AND NOT THE KEEPER

2023–2025 are byte-identical, so **the designated keeper `2026-09-11-pjm-d4-4-gasoutage` is
already correct at HEAD and needs no re-registration**. What is stale against HEAD's inputs is
PJM's held-out registration: the touchpoint `2026-09-11-pjm-holdout-gasoutage-touchpoint` carries
2020–2022 numbers produced from the pooled fallback that no longer exists.

So the minimal, rule-correct promotion is: **register the 2020–2022 own-year bundles as the new
touchpoint, stamp it to the existing keeper (rule 30(a)), and prune the superseded one (rule 35
`[R-PROMOTE]` (a))** — enumerating PJM's registered year union first (rule 35(b)), which is
2020–2025 and is fully covered. The keeper's three stores are untouched, so rule 35(e)'s
promote-verify-then-delete ordering is trivially satisfied.

## 6. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

All six on `origin` with their per-plant layer; **a promotion costs ZERO re-solves**:

```
2020  a75c4cda97c7025e8405ce6bd2afaa5e4e939c5b
2021  7d524b6654f2c337b39478caac74d8f7751cf078
2022  be240ce55424cfdc12f248005e14b60adece0a25
2023  d73cbc83c26e9c28bf3fe17e48fa43d7cf94fc42
2024  da3edc9481f584e3dbad25dc2abe984ae89e372f
2025  f4991368d6016ef61613f6ffdf6e7508f45ff7aa
git checkout <sha> -- results/calibration/pjm_h9c_<year>
```

Verified in the parent by checkout + config signature on all six: `git_sha 73a68234`,
`years [<year>]`, `pjm_offer_midcurve_minload_segments` **null** (keeper recipe, not the pjm-h8
arm). 2022's bundle carries 14 files rather than 17 — it is missing `floors/`, `hourly/network_`
and `hourly/unit_hourly_`, and **has** both artifacts registration needs
(`dispatch/2022_P1.parquet`, bundle-root `system.parquet`). Stated rather than discovered later.

## 7. DISK — rule 31 `[R-RETAIN]` trigger (ii), invoked explicitly and in advance

The container filled (**92 K free**). Named before removing, as the rule requires:
`results/calibration/pjm_h9_{2020..2025}` — the wave-1 **null reproduction**, every byte on
`origin` at the six full SHAs recorded in `.gitignore` and `RESULT-pjm-h9b` §4 — and
`data/raw/pjm-energy-offers/*.parquet`, re-fetchable, whose derived surface is already committed.
**Nothing whose promotion is undecided was touched.**

## 8. RULES

Rule 1 `[R-STRUCT]` (every reading fixed before the corpus landed; no criterion reads a residual;
§3's direction gated nothing) · rule 13 `[R-MEASURED]` (PJM's own published offers, a formulaic
input with a forward analogue) · **rule 14 `[R-ACCURATE]` (§2 — the whole basis; the worse
held-out fit is treated as a discovered root cause, and the estimate is not restored)** ·
rule 16 `[R-ALLYEARS]` / rule 34 (c) (all six registered years solved) · rule 21 `[R-DOF]` (zero
free parameters) · rule 23 `[R-FROZEN-DERIVE]` (re-derived on a SOURCE-DATA change, cited in the
commit) · rule 24 `[R-REGISTRY]` (no new field) · rule 25 `[R-ISO-SCOPE]` · rule 28
`[R-MECH-MATRIX]` (b) · rule 29 `[R-SCREEN]` (regime removed; clause (b) form 4 used, no control
solved; clause (c) discharged by `.gitignore`) · rule 30 `[R-TOUCHPOINT-FOLD]` (a)(c) (§5 the
stamp; §2 the held-out years never downgrade the ISO) · rule 31 `[R-RETAIN]` (§7) · rule 32
`[R-SHARD]` (a)(d) · rule 33 `[R-SHARD-ARCHIVE]` · rule 34 (a)(e) (§6) · rule 35 `[R-PROMOTE]`
(§5 the year-union enumeration and the prune).
