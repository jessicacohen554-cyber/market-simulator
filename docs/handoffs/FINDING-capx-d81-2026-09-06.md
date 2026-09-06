# FINDING — capx D81: the pending owner-filed dated block must offer — exactly conservative, price-neutral, and it returns 2.1 GW of cleared position to the merchant fleet

**Lane:** capx D81 (director r#48, pack §D81), extending **owner ruling Q53** (2026-09-06) from the
sector gate to the two remaining channels `DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md` §4
enumerates. **Branch:** `claude/capx-d81-must-offer-8jzvbj`, fresh off `origin/main` `acbb5350`.
**Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.
Companion: `PRECOMMIT-capx-d81-2026-09-06.md` (phase 0 + the gate table, pushed at `5428387b`
**before any code and before any solve**; Addendum A pushed at `6123188e` **before the full
window**). Instruments and every number: `docs/handoffs/d81/`.

**NOTHING ARMS.** No `ScenarioConfig` field added or changed, no default flip, no override, zero
DOF, no cache key moved (`ScenarioConfig().cache_key()` = `547053bdfccd4264` before and after).

---

## 1. Result in one paragraph

PJM's must-offer requirement keys on *existing and located in the footprint* and its three
enumerated exceptions (Manual 18 Rev 62 §5.4.1) do not include a filed plan that has not yet taken
effect — so a plant whose owner-filed date is LATER than the delivery year must offer for every year
before the removal is effective, exactly as a sector-gated unit must. `evolve_fleet` now routes
`_dated_exempt` and `_retrofitted_ids` to `exit_exempt_unit_ids`, the seam D78 built. **Measured on
PJM 2021–2025, both legs at the same basis: the repair moves precisely the pending dated block's
accredited MW out of the $0 price-taking residual `Q_0` and into the priced sell-offer stack — to
the tenth of the MW phase 0 predicted with no LP — and it is not merely bookkeeping.** In DY2022,
2,306.4 MW of that block turns out to be UNCOMPETITIVE at the clearing price, and because the
cleared quantity is pinned by the demand curve at an unchanged price, that cleared position is
handed back to the merchant fleet: **10 merchant gas-CC units (2,088.8 MW) move from uncleared-and-
failing to cleared** (1 unit / 907.7 MW in DY2023; none in 2024–25, where the whole block clears on
merit). That is exactly the misallocation `DESIGN-capx-d54` §4.2's price-taker reading created —
dated capacity clearing ahead of merchant capacity that outbid it. **Every scored metric is
unmoved: the two legs' `score.json` are identical but for their generation timestamp**, and the
clearing price, cleared quantity, census and executed economic exits are identical in all four
delivery years. So the lane delivers a structural correction at zero cost to any gate.
**Recommendation: MERGE AS CODE** (already merged — §8).

## 2. PHASE 0 — the pending dated block, sized with no LP

`docs/handoffs/d81/phase0_dated_block.py` → `phase0_dated_block.json`. The base fleet, both
exogenous-exit registries and the resolved config are the run's own — captured by patching
`market_sim.runner.build_base_fleet` inside the D78/D57 recipe and aborting before the first solve —
then walked through evolve steps 0/1/1b per year, reading `dated_plant_unit_ids(fleet_Y, afx, Y)`,
the same call `evolve_fleet` makes. D78 §5.1 could not separate this block from the committed
ledgers; this reads it from the fleet and the registry instead.

| DY | fleet units | pending dated units | nameplate MW | **accredited MW (`Σ A_g`)** | by fuel (accredited MW) |
|---|---|---|---|---|---|
| **2022** | 2,068 | **29** | **7,855.0** | **7,246.3** | coal 6,139.2 (23 u) · gas_st 734.7 (3 u) · gas_cc 372.4 (3 u) |
| 2023 | 2,061 | 19 | 5,667.0 | 5,213.6 | coal 5,213.6 (19 u) |
| 2024 | 2,057 | 15 | 5,423.0 | 4,989.2 | coal 4,989.2 (15 u) |
| 2025 | 2,056 | 15 | 5,081.3 | 4,217.5 | coal 4,217.5 (15 u) |

Recipe posture read from the captured config, not asserted: `fossil_announced_exits_enabled` True,
`confirmed_exits_enabled` True, `capacity_market_supply_clearing` True (PJM's ISO overrides),
`capacity_going_forward_bar_published` **False** and `capacity_no_default_cap_convention` **False**
(so no D74 class skip is live here and the GFC is the ATB FOM proxy),
`ccs_retrofit_available_year` 2028, accounting ratio 1.0. Registries: 33 live announced-fossil rows
/ 13,168.7 MW, 1 confirmed row, 3 reversal plants.

**The retrofit channel is zero in every year of the window** (`ccs_retrofit_available_year` = 2028),
so its half of the fix is provably inert on every backcast, hindcast and crossover year and is
carried by a test rather than a measurement.

---

## 3. PHASE 1 — the change

One executable hunk, at the ONE call site of `apply_economic_retirements`
(`src/market_sim/model/capacity_evolution/evolve.py`):

```
-            exempt_unit_ids=_retrofitted_ids | _dated_exempt,
+            exempt_unit_ids=frozenset(),
-            exit_exempt_unit_ids=_sector_exempt,
+            exit_exempt_unit_ids=(_retrofitted_ids | _dated_exempt | _sector_exempt),
```

Nothing inside `apply_economic_retirements` moves: D78's partition line already does what the rule
requires for any member. Proven mechanically — `ast.dump` after stripping docstrings is **identical**
between `acbb5350` and the build commit for `retirements.py` and `results/cache.py`, and differs for
`evolve.py` alone. That is also what licenses this session's control leg to be produced by checking
out `evolve.py` alone at the base commit (§4).

**`exempt_unit_ids` now has no producer.** It keeps its meaning (*not eligible to offer at all — no
margin, no offer, no decision*) and its tests; it is not deleted here, because it is a structural API
declaration rather than a fitted knob (rule 26 `[R-DELETE]` addresses the latter), it is one day old
as a distinct declaration, and D78's own T3 asserts the difference between the two semantics on a
toy stack. **Routed as an open item (§8 item 3), not settled here.**

**No new field.** The must-offer requirement has no off position — a resource that is existing and
in the footprint offers. A gate would make the tariff's own rule selectable, i.e. a re-armable answer
key for a behaviour the tariff does not contain. Rule 24 `[R-REGISTRY]` is unviolated: no tunable is
added or changed, no key moves, and rule 28(c) is not triggered.

`results/cache.py` records **epoch 2026-09-06e**: a same-key semantic change whose blast radius is
**zero committed bundles** — the clearing is armed for PJM alone, every PJM hindcast probe of D57 /
D58 / D74 / D78 was deleted before merge under rule 29(c), and every backcast of every ISO reaches
neither step 1b nor the clearing.

Tests: `tests/unit/model/test_capacity.py::TestDatedBlockMustOffer` (a pending dated unit offers at
its cap and faces no exit; the conservation identity with I1 held under both routings and the
direction weakly signed; an EXECUTED exit absent from the stack AND from every decision structure;
the retrofit channel inert below 2028), plus the amended D42 and D78 routing tests.
`tests/unit/model`: **10 reds, byte-identical to the branch base's 10** — the D65-B key-pin family
`FINDING-capx-d78` §6 / §8 item 4 already routed to D80. This commit introduces none.

---

## 4. PHASE 2 — the screen (rule 29), DY2022

Two legs, PJM solo, sequential, HEAD-guarded, on D78's own span
(`--start-year 2021 --end-year 2023`, solve {2021, 2023}, 2022 bridged): control at the branch base
`acbb5350`, arm at the build `18432bda`. Both resolve to cache key **`afda79ba04cbfdbf`** as
pre-declared, told apart by out-dir and `meta.json`'s git sha; `cachemod.CACHE_ROOT` is repointed at
`--out-dir`, so neither leg could read the other's cache. **Free G0:** the control reproduces D78's
own control-P to the digit — 1,370 offers, 150,857.184 / 30,577.888 MW, 67.760162 $/MW-day, position
1.048349.

**G-DRIFT / G-CTRL:** not invoked and not needed — there is no committed PJM hindcast bundle to
difference against (form 4's operand does not exist; every prior probe was deleted before merge), so
the charter's two-legs-at-HEAD control pair is the instrument. A matched cache key is not offered as
a drift verdict: both legs resolve to the same key **by design** (no field moves).

### 4.1 What the screen measured

| DY | +offers | +offered MW | −price-taker MW | phase-0 predicted | shared rows identical | dropped | price | cleared position | census |
|---|---|---|---|---|---|---|---|---|---|
| 2022 | +29 | **+7,246.26** | **−7,246.26** | 7,246.3 | 1,370 / 1,370 | 0 | 67.760162 → **67.760162** | 1.048349 → **1.048349** | unchanged |
| 2023 | +19 | **+5,213.64** | **−5,213.64** | 5,213.6 | 907 / 907 | 0 | 67.760162 → **67.760162** | 1.049022 → **1.049022** | unchanged |

Economic exits identical in both years (7,333.7 / 3,105.455 MW). Every added row is in the phase-0
block; no row is dropped; requirement, census and census position identical.

**CORRECTION (made after the full window, §5.2).** The "shared rows identical" column above was
produced by a comparator that compared each shared row's fuel, offer and accredited MW **but not its
`cleared` flag**. It is not true that every shared row is byte-identical: **10 rows in DY2022 and 1
in DY2023 flip from uncleared to cleared**, which is the mechanism's real effect and is reported in
§5.2. The corrected column reads *1,370 shared rows, identical in fuel / offer / A_g, 10 with a
flipped cleared flag*. The commit message of `6123188e` carries the uncorrected claim; this is the
correction of record.

### 4.2 The gates, graded — two literal misses, both instrument defects

| gate | literal | reading |
|---|---|---|
| G1 conservation | **FAIL** | **INSTRUMENT.** The identity the gate exists to test, `Δoffered == Δprice_takers`, holds **exactly on the ledger's digits with no tolerance** (7,246.260 both). What failed is the third comparand: `Σ` over the 29 added rows reads 7,246.259, **0.001 MW** low, because `CapacityClearing.as_ledger` rounds *each row* to 3 dp as well as the total. The §3 tolerance (±0.001 MW) was written for one rounded quantity; for a sum of *n* independently-rounded rows the achievable bound is *n* × 0.0005 = **0.0145 MW**. Relative magnitude **1.4 × 10⁻⁷**. |
| G2 identity I1 | PASS | `Q_0 + Σ A_g == census` in both legs; requirement, census, census position identical |
| G3 footprint | PASS | +29 rows, 0 dropped, every added row in the block, all 1,370 shared rows byte-identical |
| G4 decision purity | **FAIL** | **INSTRUMENT.** The gate asked whether the **2022** block appears in **any** year's decision rows; 8 units (Dominion p3797/p3809 tranches) appear in **2023's — identically in both legs**, so no mechanism effect is possible. Their plant's last pending row COMPLETES, and `dated_plant_unit_ids` documents that its survivors then "re-enter the screen as an undated residual plant", where facing the decision is correct. The per-year question reads **0 in both legs in both years**. |
| G5 direction | PASS | price and position **identical**, not merely weakly ordered |
| G6 no non-target flip | PASS | every non-target ledger block identical in both years; base year identical; economic exits identical |

Both misses stand unedited in `d81/screen_compare.json`'s `gates` block; the corrected per-year
re-measurement is the separate `diagnosis_by_year` block, declared in **Addendum A and pushed before
the full window ran**, so no gate was rewritten to fit a result. **Phase 3 proceeded on a diagnosed
instrument defect, not on a literal all-pass** — stated in those words.

### 4.3 The substantive result: D54 §4.2's bias measures at ZERO

The PRECOMMIT declared the direction as *weak, not strict*: supply at price `p` falls by `A_g` only
for `p < offer_g`. The block is coal-dominated and deep in the money — D54 §4.2's own coal median,
~$9/MW-day, against a $67.76 crossing — so every dated unit's offer sits **below** the crossing,
`supply(p)` at the crossing is unchanged, and the clearing is identical. So the bias D54 §4.2 stated
against itself (*price DOWN, cleared UP*) is **exactly zero here**, which is stronger than the
PRECOMMIT's "second-order".

That does not make the repair cosmetic, and the finding does not claim it does. The misstatement of
the published supply curve was real: 7.2 GW of DY2022 capacity sat in a $0 price-taking block that
PJM's own §5.7.1 treatment of un-offered existing MW does not contain. The price consequence returns
the moment a dated unit's net-ACR cap sits above the crossing — a low-E&AS steam or oil unit under
the D62 published bar, or any year whose crossing falls below the block's offers — and until now the
model would have been crediting un-offered MW with clearing in exactly that case.

---

## 5. PHASE 3 — the full 2021–2025 window

Two legs, PJM solo, sequential, HEAD-guarded, same recipe, both resolving to cache key
**`15a723ba3b6dc856`** (the bare full-span key — no field moves, so both legs share it by design).
The control was produced by checking out `evolve.py` alone at `acbb5350`, which §3's AST proof
licenses: it is the only file carrying an executable change. Two free consistency checks: the
screen-span and full-span **arms are byte-identical on their shared years** (DY2022, DY2023), and
the control reproduces D78's control-P.

### 5.1 Conservation — phase 0 predicted every year with no LP

| DY | +offers | +offered MW | −price-taker MW | phase-0 predicted | block rows in the arm's stack |
|---|---|---|---|---|---|
| 2022 | +29 | +7,246.260 | −7,246.260 | 7,246.3 | 29 / 29 |
| 2023 | +19 | +5,213.640 | −5,213.640 | 5,213.6 | 19 / 19 |
| 2024 | +15 | +4,989.160 | −4,989.160 | 4,989.2 | 15 / 15 |
| 2025 | +15 | +4,217.507 | −4,217.506 | 4,217.5 | 15 / 15 |

Zero rows dropped in any year; every added row is in the phase-0 block; `census_mw`,
`requirement_mw` and `census_position` identical in every year (invariant I1 holds in both legs).

### 5.2 The substantive result — the displacement at the margin, and the third instrument defect

**A whole-ledger diff of the two bundles**, run independently of the gate table, is the honest
instrument here and it found what the gates did not:

| DY | ledger blocks differing between legs |
|---|---|
| 2021 | **NONE — byte-identical** (the base year runs no evolve) |
| 2022 | `capacity_clearing`, `pipeline_events`, `entry_screen_diagnostics` |
| 2023 | `capacity_clearing`, `pipeline_events` |
| 2024 | `capacity_clearing` only — and within it only `n_offers`, `offer_stack`, `offered_mw`, `price_takers_mw` |
| 2025 | `capacity_clearing` only — the same four fields |

`pipeline_events` differs in 2022–23, which the gate table said could not happen. The cause is the
mechanism working exactly as designed:

| DY | block cleared MW | block **uncleared** MW | merchant rows flipped → cleared | flipped MW | `cleared_mw` | price |
|---|---|---|---|---|---|---|
| 2022 | 4,939.9 | **2,306.4** | **10** (all gas_cc) | **2,088.8** | 153,914.867 → identical | 67.760162 → identical |
| 2023 | 4,006.9 | 1,206.8 | **1** (gas_cc) | 907.7 | 164,467.856 → identical | 67.760162 → identical |
| 2024 | 4,989.2 | 0.0 | 0 | 0.0 | identical | 166.479752 → identical |
| 2025 | 4,217.5 | 0.0 | 0 | 0.0 | identical | 451.610 → identical |

**The mechanism.** Under D54 §4.2's price-taker reading the whole dated block sat in `Q_0`, which
clears by construction. Moving it into the merit stack exposes the part of it that is *not*
competitive — 2,306.4 MW in DY2022. The cleared quantity is pinned by the demand curve at the
clearing price (`clear_capacity_supply_stack` rule 4: the crossing quantity solves `D(Q) = offer_g`
by bisection), and the price is unchanged, so `cleared_mw` cannot move. The freed cleared position
is therefore taken by the units sitting at the marginal offer — 10 merchant gas-CC units at
67.7602 $/MW-day to the ledger's 4-dp precision, 2,088.8 MW — which **leave the failing set**
(`pipeline_events` 715 → 705 rows in 2022, 303 → 302 in 2023). The remainder is the marginal unit's
partial step, which rule 4 bisects rather than clearing whole-unit.

So D54 §4.2's stated bias (*price DOWN, cleared UP*) does not show up as a price move at all: it
shows up as a **misallocation of cleared position** — dated capacity clearing ahead of merchant
capacity that outbid it. That is the defect the repair removes, and 2,088.8 MW is its size in
DY2022.

**The third instrument defect, stated.** The §3 G3 gate compared each shared offer row's fuel, offer
and accredited MW — **not its `cleared` flag** — so it reported "1,370 shared rows byte-identical"
while 10 of them had flipped. The gate is now repaired to compare the flag (a **strictly stronger**
check: it catches a difference it previously passed over), and re-running it turns G3 from PASS to
FAIL on both the screen and the full window. **That FAIL is the correct reading of a gate that was
mis-specified, not a mechanism miss** — the flips are the mechanism's intended effect, pre-declared
in PRECOMMIT §1.2 item 5 only as far as "no dated unit is decided", which remains true. The repair
was made *after* seeing the result and is reported as such rather than folded in silently; §4 above
carries the correction of record for the uncorrected claim in commit `6123188e`.

### 5.3 Every scored metric is unmoved

Both bundles scored with `scripts/score_capacity_hindcast.py`. **The two `score.json` files are
identical except for `generated_utc`.** Nothing in the FC scorecard moves:

| metric | both legs | band |
|---|---|---|
| `retirements.total_gw` | 18.171 (actual 15.062, err +20.6 %) | FAIL |
| `unit_recall_gt300` | 0.65 (13 / 20; plant recall 0.70) | FAIL |
| `false_retire.false_gw` | 8.211 (45.2 % of model) | FAIL |
| executed economic exits by DY | 7,333.7 / 3,105.455 / 1,189.408 / 0.0 MW | — |
| additions (decision basis) | 21.893 GW total; gas_cc PASS, wind/solar/gas_ct/storage FAIL | — |
| `co2.model` 2023–25 | 274.7 / 276.8 / 320.1 Mt | — |

Those three FAIL bands are **PJM's pre-existing state, not this lane's** — they are the same bands
the D57 record reports, and they are identical in the control. **This lane moves no gate in either
direction.** Rule 14's line, stated in Addendum A.3 before the solve, is therefore satisfied
trivially: there is no movement to attribute.

Why exits do not move even though 10 units leave the failing set: the pipeline **admission cap**
binds in 2022, so it admits the same MW from a pool that is 10 units smaller — the same
cap-re-fill mechanic D78 §4 diagnosed for its own G6.

---

## 6. Governance attestation

**Rule 1 `[R-STRUCT]`:** the mechanism is the tariff's must-offer rule, chosen on its text and on an
owner ruling that had already settled it for the sibling channel; every screen gate is an identity,
a sign or a footprint, never a band or a residual; no gate reads `retire.total_gw`, recall,
`false_retire` or any residual. **Rule 12:** PJM solo, four legs strictly sequential, years
sequential within each. **Rules 13 / 14:** published market design that regenerates for any forward
delivery year; the sign line was stated before each solve and the result is reported at full
magnitude — including the fact that the pre-declared price move measured at zero and that the real
effect appeared somewhere the pre-declaration did not look. **Rule 19 `[R-ONE-MECH]`:** no new
mechanism; the two channels move onto the ONE seam D78 built, and no unit's exit is decided twice (a
dated unit's exit remains its owner's filed date at step 1b). **Rule 21 `[R-DOF]`:** zero DOF; no
number is introduced. **Rule 22 `[R-HOLDOUT]`:** every solve year is 2021–2025 forecast-mode
hindcast; no out-of-training year is solved, scored or registered. **Rule 24 `[R-REGISTRY]`:** no
tunable added or changed; `ScenarioConfig().cache_key()` = `547053bdfccd4264` before and after.
**Rule 25 `[R-ISO-SCOPE]`:** PJM's shard carries PJM's own letter; no other ISO's shard is touched
and the change is inert for every ISO whose clearing is off. **Rule 27 `[R-PUSH]`:** `evolve.py`,
`retirements.py`, `cache.py` and `test_capacity.py` edited locally and **blob-verified after push**
(local `hash-object` = remote blob on all four, line counts equal). **Rule 28:** (b) PJM's shard
cell updated in this session; (c) not triggered — no field. **Rule 29 `[R-SCREEN]`:** phase 0 was
zero-LP and pushed before any code; the screen year was named from the mechanism's own measured
footprint; STOP-only structural gates; both screen bundles and both full-window bundles deleted
before merge (§7).

**Stated deviations.**

1. **The full-window arm leg's HEAD guard fired** (`HEAD MOVED during arm`). Cause: this session
   committed the WIP FINDING (`7e784ebf`) while that leg was solving. The guard's *substance* holds
   and is verifiable: `git diff 6123188e HEAD -- src scripts` is **empty**, so no code the leg was
   solving changed. Recorded rather than left unexplained. The other three legs' guards passed.
2. **The G1 and G4 gates failed literally and are instrument defects** (§4.2), diagnosed from the
   committed ledgers with the arithmetic shown and published as Addendum A **before** the full
   window ran.
3. **The G3 gate was under-specified** and is repaired *after* seeing the full window (§5.2). The
   repair is strictly stronger and the affected claim is corrected in §4 rather than overwritten.
4. **The control legs were produced by checking out `evolve.py` alone at the base commit**, not by a
   second worktree. Licensed by §3's AST proof that it is the only file with an executable change;
   chosen because `scripts/run_capacity_hindcast.py` hard-inserts the repo's own `src/` at
   `sys.path[0]` (so a `PYTHONPATH` override cannot select different code) and a full worktree costs
   2.4 GB of a constrained disk.
5. **Main moved 38 commits during the session** and merged this lane's phases 0–2 (PR #5158). The
   only solve-path change to `evolve.py` since the legs' basis is D65-B-R step 0's additive
   `ccs_retrofits` ledger keys, which are **provably inert here**: that list is empty in every year
   of the window (retrofits open 2028). `retirements.py` and `cache.py` on main are byte-identical
   to this branch's.

**Pre-existing reds on main, not this lane's:** `tests/unit/model` carries 10 failures on the branch
base and **the identical 10** after this change (the D65-B key-pin family; `FINDING-capx-d78` §6 and
§8 item 4 already routed them to D80's records lane).

---

## 7. Matrix (rule 28) and retention (rule 29(c))

**Matrix.** PJM's shard cell `fossil_announced_exits` is updated with this lane's measured result
(the cell's own "OPEN HERE" question is the dated channel's behaviour); `capacity_market_supply_clearing`
carries a cross-reference to the stack-composition repair. No base row is added — no
`ScenarioConfig` field exists to add one for — so rule 28(c) is not triggered. MISO's and every
other ISO's shard is untouched (rule 25).

**Retention.** All four bundles are throwaway diagnostic probes: never registered, never keepers,
never quoted as a keeper number, and **deleted from `results/` before this PR merges**. The two
screen bundles were deleted once their numbers were in `d81/screen_compare.json`; the two
full-window bundles are deleted once their numbers are in `d81/full_window_compare.json` and this
document. Git history is the record (rule 15 `[R-DASHBOARD]`'s delete-not-archive discipline). Every
number this session will ever cite lives in the PRECOMMIT, this FINDING,
`d81/phase0_dated_block.json`, `d81/screen_compare.json` and `d81/full_window_compare.json`.

---

## 8. Recommendation

1. **MERGE AS CODE — done.** Phases 0–2 landed on `main` via PR #5158 during the session
   (`5428387b`, `18432bda`, `6123188e`). The full window confirms the decision after the fact: the
   repair is exactly conservative, corrects a real misallocation of cleared position (2,088.8 MW in
   DY2022), and moves **no** scored metric. It is the owner's ruled reading applied to the channels
   D78 §4 enumerated, one seam, zero DOF, no new field, no key moved, byte-identical wherever the
   clearing is off or the year is below 2028.
2. **`exempt_unit_ids` has no producer — route the deletion question.** Rule 26 `[R-DELETE]`'s
   concern (a deprecated tuned value that still parses is a re-armable answer key) does not squarely
   apply to a structural API parameter, and D78's T3 uses it to assert the difference between the
   two semantics. But a parameter no call site can reach is a dead branch, and the honest options are
   (a) delete it and rewrite T3 as a negative test on the residual construction, or (b) keep it with
   an explicit "no producer" docstring, which is what this lane did. **An owner/director call, not
   this lane's.**
3. **The uncompetitive dated block is a finding for the E&AS-operand lane.** 2,306.4 MW of DY2022
   dated capacity does not clear at its net-ACR cap. Under the ATB FOM proxy that is expected; under
   the D62 published bar it would be a different number, and the D57 record already names the
   CT / ST / oil **zero-E&AS** operand as the successor question. Whether real PJM dated units clear
   is checkable against the BRA record — a validation observable, never a target.
4. **The gate-writing lesson, for the pack.** Three of six gates in this lane were mis-specified,
   and the mechanism's real effect was found by a **whole-ledger diff**, not by the gate table. A
   structural screen should difference *every* committed block and then explain the differences,
   rather than assert a list of fields that must match — an assertion list can only catch what its
   author already thought of.

---
## 9. Reproduction

```
uv run python docs/handoffs/d81/phase0_dated_block.py --out docs/handoffs/d81/phase0_dated_block.json
bash docs/handoffs/d81/run_screen.sh control     # base code (acbb5350)
bash docs/handoffs/d81/run_screen.sh arm         # post-fix code
uv run python docs/handoffs/d81/screen_compare.py \
    --ctl results/hindcast/pjm-2021-2023-realized-t1h-d81-control \
    --arm results/hindcast/pjm-2021-2023-realized-t1h-d81-arm \
    --phase0 docs/handoffs/d81/phase0_dated_block.json \
    --out docs/handoffs/d81/screen_compare.json
bash docs/handoffs/d81/run_full.sh arm
bash docs/handoffs/d81/run_full.sh control       # with evolve.py checked out at acbb5350
```
