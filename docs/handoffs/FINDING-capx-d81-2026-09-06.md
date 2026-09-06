# FINDING — capx D81: the pending owner-filed dated block must offer — measured exactly conservative, and price-neutral in this window

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
PJM 2021–2025: the change is exactly conservative — it moves precisely the pending dated block's
accredited MW from the $0 price-taking residual `Q_0` into the priced sell-offer stack, to the tenth
of the MW phase 0 predicted with no LP — and every other row of the stack is byte-identical.** The
one substantive surprise is that **`DESIGN-capx-d54` §4.2's stated bias (price DOWN, cleared UP)
measures at exactly ZERO** across the window: the block is coal-dominated and deep in the money, so
its offers sit far below the crossing and the clearing price, cleared quantity and every exit
decision are unchanged. The supply-curve misstatement was real (7.2 GW mis-placed in DY2022); its
price consequence at these crossings was nil. **Recommendation: MERGE AS CODE.**

---

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

## 5. PHASE 3 — the full 2021–2025 window (reported, never gated)

PENDING — filled below once both legs land.

---

## 6. Governance attestation

PENDING.

## 7. Matrix (rule 28) and retention (rule 29(c))

PENDING.

## 8. Recommendation

PENDING.

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
