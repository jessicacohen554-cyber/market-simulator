# FINDING — capx D96: `neiso-t3` back on one data vintage (post-F1)

**Lane:** capx **D96** (relaunch) · **Date:** 2026-09-25 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/capx-d96-neiso-t3-postf1` · **Authority:** OWNER RULING **Q69** (capx ledger §0bk / §3): *"Re-solve now."*
**Pre-registration:** `PRECOMMIT-capx-d96-2026-09-25.md` (+ Addendum A), pushed before any LP at
**`5a48f43787c3ec0d29ae451680ab62a5e53b5156`**, the SHA every shard was pinned to. The lane branch was later
rebased onto `origin/main` for scoring (charter PART 3). The pushed PRECOMMIT commit is the parent of every
shard commit: `e70ea547` / `024469ac` / `eab16583` / `325c9c25`.

---

## 0. THE VERDICT TRANSITION

| | determination | FC-1…FC-8 |
|---|---|---|
| **BEFORE** `neiso-t3` (capx D94, 2026-09-24): two vintages | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT FAIL PASS |
| **AFTER** (D96): one post-F1 vintage | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT FAIL PASS |

**Every status, reason and caveat is identical.** The prior record is preserved byte-equal at
**`neiso-t3-pre-d96`**. `program-status.json` is untouched because no FC letter moved.

**In one sentence:** F1 was the whole of the vintage gap. `base` lands on D94's `vre_short` to the last cell,
and no score moves. But F1 does **not** shift the four legs uniformly. The carbon arm moves **opposite** to
the base, driven by a flipped horizon-edge retrofit decision in 2049. The FC-6 P1 carbon-sensitivity margin
therefore shrinks 17 %, from **50.92 to 42.42 Mt**. It still passes.

**Detail strings that moved, and only these:**
* FC-2: `final RM 6.4% → 6.1%` and `backstop share 1.0% → 1.2%`.
* FC-2 cobweb: `gas_ct(4); gas_cc(7)` → `gas_cc(7); gas_ct(4)`. Same content, opposite order (§3.2).
* FC-6: the P1/P2/P3 operands.
* FC-7: `837 → 879 config keys` (schema growth).
* FC-8: `wall 31.9 → 33.4 min`.

FC-1's I3 detail string is byte-identical, and so is FC-5's divergence list.

---

## 1. PREDICTIONS, GRADED AS WRITTEN (PRECOMMIT §4)

**23 graded: 15 HIT, 8 MISS.** Seven of the hits were declared near-certainties and are worth nothing.

| # | prediction | realized | grade |
|---|---|---|---|
| **E1** | `base` reproduces `d94/vre_short` BYTE-FOR-BYTE on the trajectory: 151.2747 Mt, 6,979.7 MW, 0.06107, 0 differing cells | **0 differing cells** across 25 yr × every `trajectory` field. The `invariants` block differs only in the order of two items inside one I13 detail string (§3.2) | **HIT** |
| C1 | `carbon_plus25` cum CO2 ∈ [96.0, 104.0], < D92 | **108.8519**: +5.17 %, **wrong direction** | **MISS** |
| C2 | `carbon_plus25` CCS₂₀₃₀ ∈ [7,821.3, 8,600] | 8,144.3 | HIT |
| C3 | `carbon_plus25` RM₂₀₅₀ ∈ [0.055, 0.066] | **0.04840** | **MISS** |
| G1 | `gasup150` cum CO2 ∈ [198.0, 209.0], < D92 | **209.2940**: +0.16 %, **wrong direction** | **MISS** |
| G2 | `gasup150` CCS₂₀₃₀ ∈ [3,551.1, 4,400] | 3,574.7 | HIT |
| G3 | `gasup150` RM₂₀₅₀ ∈ [0.072, 0.083] | **0.06360** | **MISS** |
| M1 | `gaspm5` cum CO2 ∈ [159.0, 168.0], < D92 | 162.5514 (−3.26 %) | HIT |
| M2 | `gaspm5` CCS₂₀₃₀ ∈ [5,984.2, 6,800] | 6,402.8 | HIT |
| M3 | `gaspm5` RM₂₀₅₀ ∈ [0.040, 0.050] | **0.05829**: it rose | **MISS** |
| PM | FC-6 P1 margin ∈ [47.0, 55.0] Mt, \|Δ\| < 4 Mt | **42.42 Mt**, Δ −8.50 Mt | **MISS** |
| P1 | P1 stays PASS | PASS | HIT — *near-certainty* |
| P1p | P1.premise PASS at +25.00 $/t all 25 yr | PASS | HIT — *near-certainty* |
| P2 | P2 PASS, all signs correct, with its `not scored` clause | PASS, clause kept | HIT |
| P3 | P3 PASS, builds moved < 5 % | PASS, **0.0 %** (41,204 → 41,203 MW) | HIT |
| W | every leg wall ∈ [28, 50] min, RSS < 5 GB | 33.4 / 34.2 / 36.0 / **50.3** min; RSS 3.53–3.71 GB | **MISS**: `gaspm5` over by 0.3 min |
| S1 | HOLD, FC letters unchanged | unchanged | HIT — *near-certainty* |
| S2 | reasons and caveats identical | identical | HIT — *near-certainty* |
| S3 | FC-5 CAVEAT, 25/29/0, no row changes class | exactly that | HIT |
| S4 | FC-6 CAVEAT on the two vacuous T1.6 rows | exactly that | HIT — *near-certainty* |
| S5 | FC-7 does not move | FAIL, same 2 UNIDENTIFIED | HIT — *near-certainty* |
| **S6** | exactly the listed detail strings move, and no others | two unpredicted: the FC-2 cobweb **order** flip, and FC-7 reads **879**, not 875, config keys (I read the count off `vre_short`'s payload and forgot the 4 schema-growth fields §1.1 itself listed) | **MISS** |
| S7 | `program-status.json` untouched | untouched | HIT — *near-certainty* |

**The one-sentence summary, graded clause by clause:** *"F1 was the whole of the vintage gap and this window
adds nothing: `base` lands on D94's `vre_short` to the last cell, the three arms each move a little in the
same direction, the P1 margin barely moves, and not one FC status, reason or caveat changes."*

| clause | verdict |
|---|---|
| F1 was the whole gap; this window adds nothing; `base` lands on `vre_short` to the last cell | **RIGHT**. This is E1, the strongest claim, and the test of §2's argued 2027–2050 half |
| the three arms each move a little in the same direction | **WRONG.** Only `gaspm5` moved down, and by more than the base (−3.26 % vs −2.04 %). The carbon arm moved **up** 5.17 % and `gasup150` up 0.16 %. |
| the P1 margin barely moves | **WRONG.** 50.92 → 42.42 Mt (−16.7 %) |
| not one FC status, reason or caveat changes | **RIGHT** |

**Two clauses right, two wrong, and both wrong clauses fail for the same reason, §2.** I assumed F1's effect
would propagate uniformly through the arms. It does not.

---

## 2. THE FINDING: F1 DOES NOT MOVE THE ARMS UNIFORMLY, AND THE P1 MARGIN RIDES A HORIZON-EDGE DECISION

The carbon arm is **lower** than D92's carbon arm in almost every year through 2048. It then crosses above in
**2049–2050**, the last two years of the horizon:

| year | D92 `gas_cc_ccs` MW | D96 `gas_cc_ccs` MW | D92 CO2 Mt | D96 CO2 Mt |
|---|---|---|---|---|
| 2030 | 7,821.3 | 8,144.3 | 4.160 | 3.552 |
| 2036 | 6,752.8 | 8,236.4 | 2.893 | 2.772 |
| 2040 | 5,636.9 | 6,167.9 | 3.116 | 3.051 |
| 2048 | 5,636.9 | 6,157.0 | 3.653 | 3.532 |
| **2049** | **8,636.9** (+3,000 retrofit tranche) | **4,404.5** (−1,752.5) | **1.811** | **5.239** |
| **2050** | 8,636.9 | 4,404.5 | 1.932 | 5.586 |

2049 and 2050 alone contribute **+7.08 Mt**, more than the arm's whole +5.35 Mt net change. The D92 arm took
a 3 GW CCS retrofit tranche in 2049 and the post-F1 arm took none. It shrank its CCS fleet instead. F1's
heat-rate vintage changes which hosts clear the retrofit-or-retire screen late in the horizon, and one late
tranche is worth ~7 Mt of cumulative CO2.

**Consequence for FC-6, stated at the gate.** The P1 row asks only whether the carbon arm emits less than
the base in cumulative terms, and it still passes with a 28 % margin. But **about 8.5 Mt of the margin D92
reported was one terminal-year retrofit decision.** A cumulative 2026–2050 margin is sensitive to what
happens in the last two years, where the model has no post-horizon value to weigh a retrofit against. That
is a property of the instrument, and the vintage swap exposed it. It is **not** a defect this lane repairs.
Named in §6.

The terminal reserve margins moved in **both** directions: carbon arm 0.0624 → 0.0484, `gasup150`
0.0800 → 0.0636, `gaspm5` 0.0474 → 0.0583. None is near FC-2's [3.8 %, 38.8 %] band edge, and FC-2 scores
only `base`.

---

## 3. G-DRIFT — THE AUDIT WAS RIGHT, AND E1 PROVES IT

### 3.1 The window `924017c8 → c64e69eb`

The PRECOMMIT §2 audit covered 49 code files and ~250 `data/raw` paths and classified **every hunk INERT**
for a NEISO forecast. The 2026 half was **measured**: an identical fleet was built at both commits, and the
only differences were Merrimack's labels (`COAL` → `COAL_BIT`). The 2027–2050 half was **argued**. **E1
tests the argued half, and it holds:** the leg solved at `5a48f437` reproduces the leg solved at `924017c8`
on every trajectory cell of every year.

**Therefore the D92 → D96 difference is F1's and nothing else's** (368–406 differing cells per leg, table
§4). D94 §3 attributed the `vre_short`-vs-`d92/base` drift to F1 as "likely, not proven", because D92's
solve SHA did not resolve in the clone. The attribution is still not proven hunk-by-hunk across
`aac390a6 → 924017c8`. What is now proven is that nothing **after** `924017c8` contributes.

### 3.2 The one byte that differs: an ordering nondeterminism in I13's detail

`invariants[12].detail` reads `gas_cc(7); gas_ct(4)` in D96 and `gas_ct(4); gas_cc(7)` in D94. It is the
same config and the same trajectory, and every number is identical. The I13 cobweb detail's class order is
not deterministic across runs. It flows into FC-2's cobweb row, which is why that detail string moved
(S6's first miss). **No score depends on it.** It does make a byte-level comparison of two identical solves
fail, so it is named in §6.

### 3.3 Keys, and the census

All four keys were predicted in the PRECOMMIT before any solve, and all four came out exact. They reproduce
under `head_key(payload, surface=True)` at the rebased scoring HEAD. For an identical config, the key
literal moved away from D94's `1be40790…` only because the NEISO solve surface is off its declaration on 7
rows (the coal-subclass change; PRECOMMIT §1.2).

`check_key_provenance.py` census:

* **Before any leg** (at `c64e69eb`): 245 records, 188 reproduce, 29 no key, 28 mismatch
  (16 KNOWN + 10 LAG + **2 UNKNOWN**).
* **After landing** (at the rebased HEAD): **249 records, 192 reproduce**, 29 no key, 28 mismatch (16 KNOWN + 10 LAG + **2 UNKNOWN**). All four `d96` run_configs reproduce their own keys and add no mismatch, exactly as PRECOMMIT §6 predicted.

The 2 UNKNOWN are `d94/{vre_short,vre_long}/run_config.json`, which D95 is attributing. **Observed here, not
attributed:** those records were keyed while the live surface carried one moved row (`RGGI…`). It now
carries seven, so neither the at-declaration nor the live-surface construction reproduces them. The four
`d96` records will join that class if the NEISO surface moves again before they are re-checked.

---

## 4. THE PER-LEG TABLE, AT FULL MAGNITUDE

| leg | key | cum CO2 D92 → **D96** | CO2 2026 / 2029 / 2030 / 2035 / 2040 / 2050 | CCS 2030 / 2050 MW | RM₂₀₅₀ | LW ₂₀₅₀ | cells ≠ D92 | wall | RSS |
|---|---|---|---|---|---|---|---|---|---|
| `base` | `dbef1ecac9596c90` | 154.4195 → **151.2747** (−2.04 %) | 16.0074 / 6.5706 / 6.6509 / 4.3399 / 4.0525 / 7.3448 | 6,979.7 / 2,940.5 | 0.06107 | 79.44 | 368 | 33.4 min | 3.53 GB |
| `carbon_plus25` | `f66e7b51d3731465` | 103.5042 → **108.8519** (+5.17 %) | 13.0592 / 4.1027 / 3.5517 / 2.8328 / 3.0513 / 5.5858 | 8,144.3 / 4,404.5 | 0.04840 | 82.36 | 406 | 34.2 min | 3.56 GB |
| `gasup150` | `d3ff933838e3fb12` | 208.9630 → **209.2940** (+0.16 %) | 13.4496 / 9.6156 / 10.0078 / 6.3179 / 7.0666 / 9.6656 | 3,574.7 / 1,223.3 | 0.06360 | 93.15 | 405 | 36.0 min | 3.71 GB |
| `gaspm5` | `8d23ff10a99c4a8a` | 168.0340 → **162.5514** (−3.26 %) | 15.5009 / 6.5514 / 7.1398 / 4.4869 / 4.5214 / 8.3164 | 6,402.8 / 2,273.2 | 0.05829 | 81.91 | 389 | 50.3 min | 3.57 GB |

All four legs solved 25/25 years with no error, at the pinned SHA, on a clean tree, with both pins and exactly
one override each, verified by the parent off each `run_config.json`.

### 4.1 FC-6 paired block (`d96/paired_invariants.json`)

| row | D92 (pre-F1) | **D96** |
|---|---|---|
| P1 | PASS — `base 154.42 Mt vs high 103.50 Mt` | PASS — **`base 151.27 Mt vs high 108.85 Mt`** |
| P1.premise | PASS — `+25.00 $/t` all 25 yr | PASS — identical |
| P2 | PASS — `gas-fired 33.83→32.60 TWh, LW 79.64→92.05` `[not scored at this grain: objective↑]` | PASS — `gas-fired 33.93→32.61 TWh, LW 79.44→93.15` `[not scored at this grain: objective↑]` |
| P3 | PASS — `moved 1.7% (41149 → 40429 MW)` | PASS — **`moved 0.0% (41204 → 41203 MW)`** |

Assembled by D92's instrument at the **registered summary grain**. That instrument was re-validated
byte-identical at HEAD before use, so the paired diff is a data diff and not a change of grain.

**Cache-grain cross-check, reported and NOT registered (declared in PRECOMMIT §5).** The shards pushed their
full bundles this time, so `check_forecast_invariants.py --paired` could run over the parquets:

* **P1:** `base 151.27 Mt vs high 108.85 Mt`. Identical operands, a **third** validation point that the
  summary grain equals the cache grain.
* **P1.premise:** identical.
* **P2:** PASS, `all signs correct` **with `objective↑` scored**. This closes D92 Addendum A §A.3's disclosed
  weakening *for this pair*: the missing sub-check passes when scored.
* **P3:** identical.

### 4.2 FC-5 (`dispositions/neiso-t3.json`; prior byte-equal at `neiso-t3-pre-d96.json`)

**0 of 54 rows changed class: 25 EXPLAINED DIVERGENCE, 29 IN CORRIDOR, 0 UNEXPLAINED.** The re-base was
mechanical, by D92's validated instrument (54/54 values and 54/54 divergences reproduce from `d96/base`).
Anchors are untouched (rule 13 `[R-MEASURED]`).

Six explanations quoted figures of the bundle and were refreshed. D92's historical transitions were left
as history, and one D96 sentence was appended to each:

| row | divergence | quoted figures refreshed |
|---|---|---|
| `co2@2030` | −25.0 → **−28.2 %** | CCS 6,979.7 MW beside 4,347.1 unabated; 21.286 of 33.925 TWh gas abated |
| `co2@2035` | −57.0 → **−58.6 %** | 21.832 of 28.430 TWh gas abated |
| `co2@2040` | −60.0 → **−61.5 %** | 4,795.4 MW CCS beside 5,347.1 unabated, **47 %** abated (was 44 %); 4.05 Mt |
| `generation:gas@2030` | +47.8 → +47.2 % | the 2030 abated split |
| `capacity:gas_cc@2040` | −20.2 → **−20.6 %** | 10,142.5 MW = 5,347.1 + 4,795.4 |
| `generation:total@2040` | −15.3 → −15.3 % | imports 30.515 TWh; CC fleet 20.6 % short |

**Direction, reported rather than argued:** all three co2 rows moved **further** below the AEO2025 anchor.
F1 deepens the CCS wave, which deepens the corridor gap. Script: `docs/handoffs/d96/rebase_fc5_d96.py`.

### 4.3 FC-7 — did not move, and D90-R Addendum B was not triggered

`d96/base/dof_ledger.json` was built by the committed instrument. It has the same 9 names and the same 2
UNIDENTIFIED as D92, plus the instrument's `epoch_field_gaps` block. `forecast_attestation.json` was
authored from committed bytes; `dof_ledger_complete` is recorded **false**, honestly.

---

## 5. RULES 32 / 33 / 34 / 31 / 27

* **The parent ran no LP.** Four legs went to four shards, each pinned to `5a48f437…` with H1/H2 hard stops.
* **Two operational incidents, both recorded in Addendum A.3:**
  1. The first `base` shard never got a container: PENDING for 65 min, the failure that killed this lane's
     first launch. It was archived with nothing produced and relaunched as `claude/capx-d96-base-r`.
  2. `gasup150` ended a turn with its data build still backgrounded (D92 §7's mode). A scheduled
     `create_trigger` nudge resumed it.
* **Parent verification, before each archive:**
  * fetch;
  * `git ls-tree` = 78 files under each bundle (rule 34(d));
  * only its own path plus `.gitignore` touched;
  * config signature, both pins, override and key off `run_config.json`;
  * slim bundle landed on this branch;
  * blob-verified;
  * then archived. **All four shards are archived.**
* **What lands on `main` (rule 33(f)):** each leg's slim bundle (summary, run_config, `config.yaml`,
  `solve_surface.json`, 25 evolution ledgers), `d96/paired_invariants.json`, `d96/base/{dof_ledger,
  forecast_attestation}.json`, both disposition files, and `ff-verdicts.json`. The per-year parquets are kept
  off `main` by `.gitignore` (added in the PRECOMMIT commit).
* **Retrievability (rule 34(e)).**
  * Everything the verdict reads is on this branch, headed for `main`.
  * The per-year cache parquets exist on the four shard branches (transport, cut when this PR merges) and in
    this container's working tree (ephemeral). Leg SHAs, recorded as **provenance only** (rule 33(d)):
    `base` `9f4f845f793180f403b17722a0cb7aad39cdaa3b`, `carbon_plus25`
    `2c77386d1eac7eed20f18b3acb622140cf0cbaa1`, `gasup150` `3a71d44f949808584734747da1154beb9a938e58`,
    `gaspm5` `ce75978ecfe81e7957d65d7c8ad2492f52acd889`.
  * **Re-deriving anything from the parquets after those branches are cut costs a re-solve:** ~35–50 min per
    leg plus ~40 min of container preparation, or ~1.5 h wall in four parallel shards.
* **Leftover refs the owner must remove:** `claude/capx-d96-base-r`, `claude/capx-d96-carbon_plus25`,
  `claude/capx-d96-gasup150`, `claude/capx-d96-gaspm5`. A session cannot delete a ref (rule 33(f)(2)), and
  no deletion was attempted.
* **Rule 31:** nothing was deleted.
* **Rule 27:** every pushed file of 300+ lines was pushed with `git push` as its exact on-disk bytes and
  blob-verified against the remote (38/38 MATCH at the scoring push).
* **Boundaries:** no file under `src/` or `scripts/` was edited. Rule 28 `[R-MECH-MATRIX]` does not fire:
  no mechanism was proposed, tested or added.

---

## 6. NAMED AND LEFT

1. **The two `d94` `G1_UNKNOWN` rows.** OWNER: **capx D95** (live, concurrent). §3.3 records an observation
   for it and nothing more.
2. **FC-6 P1's cumulative margin rides horizon-edge retrofit decisions (§2).** About 8.5 Mt of D92's margin
   was one 2049 tranche. OWNER: **the capx CCS lane** (D92 §9.9 already routes *"the CCS retrofit wave's
   size or economics"* there). Whether the rubric should score a terminal-effect-robust P1 variant is a
   **rubric owner** call. None has been chartered, and **no live owner exists for that half.**
3. **The I13 detail's class order is nondeterministic (§3.2).** It is cosmetic, but it breaks byte-level
   comparison of identical solves. **No live owner exists.** `check_forecast_invariants.py` is standing
   tooling this lane may not edit.
4. **T1.6 cannot discriminate in NEISO on this code** (D94 §1.1, unchanged). OWNER: **the owner**, since a
   Q27-class ruling is needed to re-point a ladder.
5. **Every other T3 golden's carried FC-6** (D92 §9.8, D94 §6.4). **Still has no live owner.**
6. **FC-3 / FC-4 inputs are carried** (T1-H `d46`, T1-X `rcrepair`). They are scored instruments on their
   own bundles, out of this charter. Whether they too should be re-solved post-F1 is an **owner** call; no
   lane is chartered.

## 7. THE PROMOTION QUESTION

The forecast board has determinations, not keepers, so there is nothing to promote in rule 15's sense. The
re-score is **already registered** as `neiso-t3`, with the prior record at `neiso-t3-pre-d96`. Two decisions
are the owner's:

* **(a)** Merge this as the standing `neiso-t3`. It moves no score, puts the verdict on one vintage, and
  changes the FC-6/FC-5 operands reported in §4.
* **(b)** Should the per-year parquets be kept anywhere beyond the shard branches that this PR's merge
  will cut? The verdict does not need them. Without them, the cache-grain P2 cross-check and any per-hour
  question cost a re-solve (§5).
