# PRECOMMIT — capx D81: the PENDING owner-filed dated block MUST OFFER — extend owner ruling Q53's must-offer reading to the residual price-taker channels D54 §4.2 chose

**Lane:** capx D81 (director r#48, pack §D81). **Branch:** `claude/capx-d81-must-offer-8jzvbj`,
fresh off `origin/main` `acbb5350`. **Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.
**Phase 0 — ZERO LP — measured, written and pushed BEFORE any code and BEFORE any solve.**
Charter inputs: `DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md` §4 (the channel table) and
§4.1; `FINDING-capx-d78-2026-09-06.md` §5.1 and §8 item 3;
`DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` §4.2 (the design reading being replaced).
Companion: `FINDING-capx-d81-2026-09-06.md` (written after the screen).

**NOTHING ARMS.** No new `ScenarioConfig` field (§2.3 says why), no default flip, no override, no
parameter value, zero DOF. The change is unconditional because it is the seam's correct semantics
under a rule the owner has already ruled.

---

## 0. The one paragraph

Owner ruling Q53 (2026-09-06) ruled **reading 1** for the sector gate: *"a sector-1 unit MUST
STILL OFFER at its cost-based price; only its exit decision is exempt"* — PJM's must-offer
requirement keys on **existing and in-footprint**, never on why a unit's exit is exogenous
(Manual 18 Rev 62 §1.2 / §5.4.1; three enumerated exceptions, none of them ownership or a filed
plan that has not yet taken effect). D78 built the seam that expresses it — `exit_exempt_unit_ids`,
evaluated and offered, partitioned out of `margins` after the clearing — and routed the sector gate
onto it. D78 §4 then enumerated **every other channel** that reaches the same residual construction
and found two that the identical rule reaches and the code still treats as $0 price takers: the
**pending owner-filed dated block** (a plant whose filed date is LATER than the delivery year — it
must offer for every DY before the removal is effective) and the **this-year CCS retrofit** (an
existing resource). D78 did not move them because Q53 had ruled the sector case only and D54 §4.2
was a landed design reading. The director extends the same rule to both (ledger §0as.3(c)). This
lane is that extension: `evolve_fleet` routes `_dated_exempt` and `_retrofitted_ids` to
`exit_exempt_unit_ids` instead of `exempt_unit_ids`. Executed step-0/1 exits are **already**
correct — they left the fleet before step 3, which is exception [c] (`§5.4.7`: removal effective ⇒
*"no longer eligible to offer"*) — and stay untouched.

---

## 1. PHASE 0 — ZERO LP: the pending dated block, sized

**Instrument:** `docs/handoffs/d81/phase0_dated_block.py` → `docs/handoffs/d81/phase0_dated_block.json`.
**Construction (why it needs no LP, and why it is exact):** the base fleet, both exogenous-exit
registries and the resolved config are the **run's own** — captured by patching
`market_sim.runner.build_base_fleet` inside the D78/D57 recipe (`--iso PJM --start-year 2021
--end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics`) and aborting
before the first solve, so nothing is a re-derivation. The fleet is then walked through evolve
steps **0 / 1 / 1b** for each year and the block read as `dated_plant_unit_ids(fleet_Y, afx, Y)` —
the same call `evolve_fleet` makes. Those three steps are the **only** fleet mutations that can
change the block: step 3 cannot (a dated unit is exempt from the screen at HEAD — the very seam
this lane repairs) and steps 4/5 cannot (a new plant code carries no pending registry row).
D78 §5.1 could not separate this block from the committed ledgers; this reads it from the fleet and
the registry instead, exactly as the charter directs.

**Resolved recipe posture** (from the captured config, not asserted):
`fossil_announced_exits_enabled` **True**, `confirmed_exits_enabled` **True**,
`capacity_market_supply_clearing` **True** (PJM's `default_scenario_overrides`),
`capacity_going_forward_bar_published` **False**, `capacity_no_default_cap_convention` **False**
(so no D74 class skip is live in this recipe and the GFC is the ATB FOM proxy),
`ccs_retrofit_available_year` **2028**, internal-supply accounting ratio **1.0**.
Registries: 33 live announced-fossil rows / 13,168.7 MW; 1 confirmed row; 3 reversal plants.
Base fleet 2,112 units.

### 1.1 The block table

| DY | fleet units | pending dated units | nameplate MW | offering units | **accredited MW (`Σ A_g`)** | by fuel (accredited MW) |
|---|---|---|---|---|---|---|
| **2022** | 2,068 | **29** | **7,855.0** | 29 | **7,246.3** | coal 6,139.2 (23 u) · gas_st 734.7 (3 u) · gas_cc 372.4 (3 u) |
| 2023 | 2,061 | 19 | 5,667.0 | 19 | 5,213.6 | coal 5,213.6 (19 u) |
| 2024 | 2,057 | 15 | 5,423.0 | 15 | 4,989.2 | coal 4,989.2 (15 u) |
| 2025 | 2,056 | 15 | 5,081.3 | 15 | 4,217.5 | coal 4,217.5 (15 u) |

`A_g = _thermal_firm_mw(g, "PJM", config, Y) × ratio` — the ledger's own accreditation basis, the
same operand `_settle_capacity_supply_clearing` uses. Every unit in the block is a
`_THERMAL_FOM` class with positive accredited MW, so the *offering* subset and the block coincide
in every year.

**The retrofit channel is zero in every year of the window**: `ccs_retrofit_available_year` = 2028,
so `_retrofitted_ids` is empty by construction in every backcast, hindcast and crossover year. Its
half of the fix is therefore provably inert on everything this lane (or any keeper) solves, and is
carried by a test rather than a measurement.

**Stated limits of the census** (in the JSON's `limits`): it is exact for the block; the *offering*
count is an upper bound because a unit reaches the stack only if it also has dispatch rows in the
screen year, which no zero-LP read can see; nameplate is the post-derate `pmax` the walk carries.

### 1.2 The pre-declared SIGN, stated before any solve

Moving the block from `exempt_unit_ids` to `exit_exempt_unit_ids` moves exactly `Σ A_g` out of the
$0 price-taking block `Q_0` and into the priced sell-offer stack, at
`offer_g = max(0, GFC_g − EAS_g) / (A_g × 365)`:

1. `offered_mw` **RISES** by `Σ A_g` of the block's dispatch-carrying units (**≤ 7,246.3 MW** in
   2022); `n_offers` rises by the same unit count (**≤ 29**).
2. `price_takers_mw` **FALLS** by the identical MW. `accredited_total_mw`, `requirement_mw`,
   `census_mw` and `census_position` are **UNCHANGED** — invariant I1 (`Q_0 + Σ A_g == accredited`)
   holds in both legs by construction.
3. Clearing **price UP or equal**; **cleared position DOWN or equal**. This is the exact reversal
   of D54 §4.2's stated bias (*"price-taking dated MW biases the cleared quantity UP and the price
   DOWN relative to letting them offer their net ACR"*). It is weak, not strict: supply at any
   price `p` falls by `A_g` only for `p < offer_g`, so a block whose units all offer $0
   (`EAS ≥ GFC`) moves nothing but the stack's bookkeeping.
4. **Second-order in the window**, as D54 §4.2 predicted for itself: the block is 7,246.3 of
   ~181,435 MW accredited in 2022 (4.0 %), it is coal-dominated (the coal median offer D54 §4.2
   quotes, ~$9/MW-day, is far below the design's clearing price), and the VRR segment 2023 sat flat
   across a 34 GW move in D58.
5. **No dated unit is decided in either leg.** `exempt_unit_ids` and `exit_exempt_unit_ids` are both
   out of the decision, so the block appears in no `pipeline_events`, `decided`, `entry_capped` or
   economic-`retirements` row in either leg. Whatever economic exits move, they move only through
   the single clearing price the merchant fleet is settled at.

---

## 2. PHASE 1 — the change

### 2.1 The one seam

`src/market_sim/model/capacity_evolution/evolve.py`, the ONE call site of
`apply_economic_retirements`:

```
-            exempt_unit_ids=_retrofitted_ids | _dated_exempt,
+            exempt_unit_ids=frozenset(),
             ...
-            exit_exempt_unit_ids=_sector_exempt,
+            exit_exempt_unit_ids=_retrofitted_ids | _dated_exempt | _sector_exempt,
```

Nothing inside `apply_economic_retirements` moves: the D78 partition line
(`margins = [m for m in margins if m[0].unit_id not in exit_exempt_unit_ids]`, after the clearing
and before either decision rule) already does exactly what the rule requires, for any member.
Every consumer table D78 §2.2–§2.3 wrote applies unchanged — M1/M5/M6 read the repaired stack,
M2/M3/M4 read the decision partition, and the dated block is out of the decision in both legs,
which is what makes this a pure offer-side change.

### 2.2 `exempt_unit_ids` after the change

The parameter keeps its meaning (*out of the screen entirely — no margin, no offer, no decision*)
and its tests, and **has no producer at HEAD** once this lands: the only two members the call site
carried are the two channels the rule reaches. It is **not** deleted here — it is a structural API
declaration, not a fitted knob (rule 26 `[R-DELETE]` is about a deprecated tuned value that still
parses), it is one day old as a distinct declaration, and D78's T3 asserts the difference between
the two semantics on a toy stack. The FINDING routes the deletion question rather than settling it.

### 2.3 No new field — this IS the seam's correct semantics

Stated as the charter asks. The must-offer requirement is not a modelling option with an off
position: a unit that is existing and in the footprint offers. A gate would make the tariff's own
rule selectable, which is a re-armable answer key for a behaviour the tariff does not contain, and
rule 24 `[R-REGISTRY]` is unviolated because no tunable is added or changed. **No new
`ScenarioConfig` field, no cache-key registration, no matrix row** — rule 28(c) is not triggered;
rule 28(b) (PJM's shard cell) is.

**Cache-key consequence, stated.** No field moves, so every key is unchanged and this is a
**same-key semantic change** for any clearing-armed ISO. Blast radius: **zero committed bundles** —
the clearing is armed for PJM only, no PJM hindcast bundle is registered anywhere in
`results/`, and every backcast keeper of every ISO runs `mode="backcast"`, which reaches neither
step 1b nor the clearing. `results/cache.py`'s epoch ledger receives one entry saying exactly this
in the build commit.

### 2.4 Tests

- **T1 pending dated unit OFFERS at its cap and is never decided** (clearing ON, toy stack): a unit
  whose plant carries a pending dated row appears in `capacity_clearing.offer_stack` with
  `offer == max(0, GFC − EAS)/(A_g × 365)`, contributes its `A_g` to `offered_mw`, and has no
  `pipeline_events` row, no `retired` row and no loss-counter change.
- **T2 an EXECUTED exit is absent from both**: a unit whose dated row is effective for the delivery
  year is removed by step 1b before the screen — absent from `margins`, from `offer_stack`, from the
  accredited census and from every decision structure (exception [c], `§5.4.7`).
- **T3 conservation**: with the dated block routed to `exit_exempt_unit_ids`, `offered_mw` rises and
  `price_takers_mw` falls by the identical `Σ A_g`, and `Q_0 + Σ A_g == accredited` in both
  routings (invariant I1 unmoved).
- **T4 retrofit channel inert below 2028**: for a delivery year `< ccs_retrofit_available_year`,
  `_retrofitted_ids` is empty, so the routing change is a no-op — every ledger, decision and cache
  key of a below-2028 hindcast is byte-identical.
- **T5 evolve routing**: the spy sees `exempt_unit_ids == ∅` and
  `exit_exempt_unit_ids == dated ∪ retrofit ∪ sector`, with the `sector_gated` census unchanged.
- **T6 clearing OFF byte-identity**: on an ISO with no supply clearing (MISO's armed keeper
  posture), moving the dated set between the two parameters changes nothing in `pipeline_events`,
  `retired`, `floor_retained`, the pipeline state or the survivors, under both decision rules.

---

## 3. PHASE 2 — SCREEN (rule 29 `[R-SCREEN]`), named here, before it runs

**SCREEN YEAR = 2022 (DY 2022/23)**, span `--start-year 2021 --end-year 2023` (solve years
{2021, 2023}, 2022 the rule-22 bridge, never scored) — the delivery year in which **phase 0
measures this mechanism's own footprint largest**: 7,246.3 MW accredited across 29 units, against
5,213.6 / 4,989.2 / 4,217.5 MW in 2023 / 2024 / 2025. Chosen from the mechanism's measured
footprint, never from a residual. It is also D78's own screen span, so the two lanes' ledgers are
directly comparable.

**Two legs, PJM solo, sequential (rule 12), each under a HEAD guard**
(`docs/handoffs/d81/run_screen.sh`):

| leg | code | role |
|---|---|---|
| **control** | `acbb5350` (pre-fix; the branch's base, `src/` byte-identical to `origin/main`) | the differencing pair |
| **arm** | the phase-1 build commit | the mechanism |

Recipe, both legs identical (the fix is unconditional, so **no flag selects it**):
`run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2023 --vintage 2020 --fuel-variant
realized --entry-screen-diagnostics --out-dir results/hindcast/pjm-2021-2023-realized-t1h-d81-<leg>`.
`cachemod.CACHE_ROOT` is repointed at `--out-dir`, so neither leg can read the other's cache.
The control is solved FIRST, on the un-edited tree, so the two legs differ by this lane's own hunk
plus tests and docs alone (`git diff --stat` in the FINDING).

**G-DRIFT / G-CTRL:** not invoked. Charter clause (b)'s form-4 differencing against a keeper's
committed bundle does not apply — there is no committed PJM hindcast bundle to difference against
(D78's were deleted before merge, rule 29(c)), and the charter directs **two legs at HEAD**, which
is a same-HEAD control pair rather than a drift question. A matched cache key is likewise not a
verdict here and is not offered as one: both legs resolve to the same key by design (§2.3) and are
told apart by `meta.json`'s git sha and their out-dirs.

**The screen gate is STRUCTURAL and a STOP gate only** — it may kill the arm, never promote it; no
gate reads `retire.total_gw`, `false_retire`, recall, precision or any residual.

| # | question | pass condition (2022 unless stated) |
|---|---|---|
| **G1** | **conservation, to the MW** | `offered_mw(arm) − offered_mw(ctl)` == `price_takers_mw(ctl) − price_takers_mw(arm)` == `Σ A_g` over the dated units that appear in the arm's stack, ±0.001 MW (the ledger's rounding); `n_offers(arm) − n_offers(ctl)` == that unit count, **≤ 29** |
| **G2** | **the identity I1** | `price_takers_mw + offered_mw == census_mw` in BOTH legs, ±0.001 MW; `requirement_mw`, `census_mw`, `census_position` **identical** between legs |
| **G3** | **footprint confined to the rows the mechanism claims** | the arm's stack minus the control's = **exactly** the phase-0 dated set for 2022 (no other unit appears); the control's stack minus the arm's = **∅**; every shared offer row byte-identical (`offer` to 1e-4, `A_g` to 1e-3, fuel) |
| **G4** | **decision purity** | **zero** dated units in any `pipeline_events` row, `retired` row or `floor_retained` row of 2021–2023 in **either** leg — the block is out of the decision in both routings |
| **G5** | **direction** | price(arm) **≥** price(ctl) and `cleared_position`(arm) **≤** (ctl), ±1e-6; `how` reported either way |
| **G6** | **no non-target flip** | 2021: every ledger block identical (the base year runs no evolve, so the arm cannot touch it). 2022–2023: `announced_derates`, `confirmed_derates`, `ccs_retrofits` (empty in both — the retrofit channel's inertness, measured), `sector_gated` (absent in both), `no_default_cap_price_takers` (absent in both), `peak_demand_mw`, `screen_peak_demand_mw`, `screen_adequacy_requirement_mw`, and the `retirements` rows with `reason` in {`confirmed`, `announced`} **identical**; economic `retirements` and `thermal_additions` may differ, and differ **only** through the one clearing price (reported, never gated) |

**ALL PASS ⇒ the full window (§4); any FAIL ⇒ the arm is killed, the remaining years are never
spent, and the kill is the session's result.** Both bundles are throwaway probes: never registered,
never a keeper, never quoted as a keeper number, **DELETED from `results/` before the PR merges**
(rule 29(c)); this document, the FINDING and `docs/handoffs/d81/screen_compare.json` carry every
number the session will ever cite.

---

## 4. PHASE 3 — the full window, only if §3 clears

`--start-year 2021 --end-year 2025`, both legs, same recipe. Reported, **not gated** (nothing here
is a criterion and nothing here can promote the arm):

- the per-DY stack deltas against the phase-0 block table of §1.1 — 2023 / 2024 / 2025 should move
  `offered_mw` up and `price_takers_mw` down by 5,213.6 / 4,989.2 / 4,217.5 MW **less** whatever the
  years' own exits removed, with the differences attributed;
- the clearing price and position path across the window, against D54 §4.2's stated bias;
- `retire.total_gw`, unit recall and `false_retire` at full magnitude, with the rule-14 line stated
  here **before** the solve: PJM's control over-retires (D58 PREDECL §3 P5), so a price that rises
  raises merchant capacity revenue and can only reduce exits — a movement toward the actual that is
  a **consequence reported**, never evidence for the mechanism, and a worse band would not be
  evidence against it.

---

## 5. Rules, stated

Rule 1 `[R-STRUCT]` — the mechanism is the tariff's must-offer rule, chosen on the text and on an
owner ruling that already settled it; every screen gate is an identity, a sign or a footprint, none
a band or a residual. Rule 13 / 14 `[R-MEASURED]` / `[R-ACCURATE]` — published market design that
regenerates for any forward delivery year; the sign line is stated before the solve (§1.2) and any
violation is reported at full magnitude and diagnosed, never absorbed. Rule 19 `[R-ONE-MECH]` — no
new mechanism: the two channels move onto the ONE seam D78 built, and no unit's exit is decided
twice (a dated unit's exit remains its owner's filed date, decided at step 1b). Rule 21 `[R-DOF]` —
zero DOF; no number is introduced. Rule 22 `[R-HOLDOUT]` — every solve year is in {2021, 2023, 2025}
∪ the 2022/2024 bridges, all training-tier or forecast-mode hindcast; nothing out-of-training is
solved, scored or registered. Rule 24 `[R-REGISTRY]` — no tunable added or changed. Rule 25
`[R-ISO-SCOPE]` — PJM's cell carries PJM's own letter; no other ISO's shard is touched, and the
change is inert for every ISO whose clearing is off. Rule 27 `[R-PUSH]` — `evolve.py`,
`retirements.py`, `test_capacity.py`, `cache.py` and the PJM shard are edited locally and
**blob-verified after push**. Rule 28 `[R-MECH-MATRIX]` — (b) PJM's shard cell only; (c) not
triggered (no field). Rule 29 `[R-SCREEN]` — phase 0 is zero-LP and pushed first; the screen year is
named here from the mechanism's own measured footprint; STOP-only structural gates; both bundles
deleted before merge.

## 6. Collision register (this lane's writes)

`src/market_sim/model/capacity_evolution/evolve.py` (the one call site and its comment block),
`retirements.py` (the two docstring paragraphs and the loop comment that name which set carries
what — **not** the D57 clearing function, **not** the D62 bar seam, **not** the D74 class skip,
**not** the D67 requirement seam, **not** the partition line), `results/cache.py` (one epoch entry),
`tests/unit/model/test_capacity.py`, the PJM matrix shard cell, `docs/handoffs/` (this document, the
FINDING, `d81/` instruments, dated cross-references appended to D54 §4.2 and D78 §4 — never a
rewrite), the capx ledger row. **D78-R touches no code, so this lane composes with it**; if both are
live the branch rebases onto D78-R's PRECOMMIT. **D65-B-R is the sole board writer** until its batch
registers — this lane writes no board file.

---

## ADDENDUM A — the screen's literal result, its two instrument defects, and the phase-3 declaration

**Written and committed AFTER the screen and BEFORE the full window.** The §3 gate table is not
edited: both literal misses stand in the record and in
`docs/handoffs/d81/screen_compare.json`'s `gates` block exactly as the comparator graded them. What
this addendum adds is the separate per-year re-measurement (`diagnosis_by_year`, in the same JSON)
that says whether each miss is the MECHANISM or the INSTRUMENT, plus the phase-3 signs.

### A.1 The screen, graded

| gate | literal | reading |
|---|---|---|
| G1 conservation | **FAIL** | **INSTRUMENT.** `Δoffered = Δprice_takers = 7,246.260 MW` — the identity the gate exists to test holds **exactly, on the ledger's own digits, with no tolerance**. What failed is the third comparand: `Σ` of the 29 added rows' accredited MW reads 7,246.259, i.e. **0.001 MW** low, because `CapacityClearing.as_ledger` rounds *each row* to 3 dp as well as the total. The §3 tolerance (±0.001 MW) was specified for one rounded quantity; for a sum of *n* independently-rounded rows the achievable bound is *n* × 0.0005 = **0.0145 MW**. Relative magnitude of the miss: **1.4 × 10⁻⁷**. |
| G2 identity I1 | PASS | `Q_0 + Σ A_g == census` in both legs; requirement, census and census position identical |
| G3 footprint | PASS | **+29 rows, 0 dropped, every added row in the phase-0 block, all 1,370 shared rows byte-identical** |
| G4 decision purity | **FAIL** | **INSTRUMENT.** The gate asked whether the **2022** block appears in **any** year's decision rows, and 8 units (Dominion p3797 / p3809 tranches) appear in **2023's** — **identically in both legs**, so no mechanism effect is possible. Cause: their plant's last pending row COMPLETES, and `dated_plant_unit_ids` documents that its survivors then "re-enter the screen as an undated residual plant". Facing the 2023 decision is correct for them. The per-year question — year Y's block against year Y's decision rows — reads **0 in both legs in both years**. |
| G5 direction | PASS | price and cleared position **identical**, not merely weakly ordered (A.2) |
| G6 no non-target flip | PASS | every non-target ledger block identical in both years, base year identical, **economic exits identical** (7,333.7 / 3,105.455 MW) |

**Neither miss is the mechanism.** Both are defects in gates this session wrote, each diagnosed
from the committed ledgers with the arithmetic shown, and each corrected reading is a PASS. Phase 3
proceeds on that basis and the FINDING says so in those words — not on a literal all-pass.

### A.2 What the screen measured, and the one substantive surprise

The mechanism is **exactly conservative and, in this window, price-neutral**:

| DY | +offers | +offered MW | −price-taker MW | phase-0 predicted | price | position | census |
|---|---|---|---|---|---|---|---|
| 2022 | +29 | +7,246.26 | −7,246.26 | 7,246.3 | 67.760162 → **67.760162** | 1.048349 → **1.048349** | unchanged |
| 2023 | +19 | +5,213.64 | −5,213.64 | 5,213.6 | 67.760162 → **67.760162** | 1.049022 → **1.049022** | unchanged |

Phase 0 predicted the moved MW to the tenth in both years, from a zero-LP read.

**The price does not move at all — and that is a structural result, not a null.** §1.2 item 3 stated
the direction as *weak, not strict*: supply at price `p` falls by `A_g` only for `p < offer_g`. The
block is coal-dominated and deep in the money (D54 §4.2's own coal median, ~$9/MW-day, against a
$67.76 clearing price), so every dated unit's offer sits **below** the crossing, `supply(p)` is
unchanged at the crossing for both legs, and the clearing is identical. So **D54 §4.2's stated bias
— price DOWN, cleared UP — is measured at exactly ZERO in this window**, which is stronger than
§1.2 item 4's "second-order": the reading it chose cost nothing *here*, and the repair costs nothing
either. The repair is not thereby cosmetic: the bias returns the moment a dated unit's net-ACR cap
sits above the clearing price (a low-E&AS steam or oil unit under the D62 published bar, or any
year whose crossing falls below the block's offers), and the model would then have been crediting
un-offered MW with clearing. What the window shows is that the *misstatement of the supply curve*
was real (7.2 GW mis-placed in 2022) and its *price consequence* was nil at this crossing.

### A.3 Phase 3 — declared before it runs

Span `--start-year 2021 --end-year 2025`, both legs, same recipe, sequential, HEAD-guarded.
**Reported, not gated** — nothing below is a criterion and nothing below can promote the arm:

1. **2024 and 2025 conservation**, against phase 0's block table: +15 offers / +4,989.2 MW and
   +15 / +4,217.5 MW, less whatever each year's own exits removed, with the difference attributed.
2. **The price path.** The pre-declared expectation is **unchanged in every year**, on A.2's
   reasoning (the block clears in every year the crossing sits above ~$9/MW-day). A year in which
   the price *does* move is the interesting case and is reported with the marginal unit and the
   block offers that bracket it.
3. **`retire.total_gw`, unit recall, `false_retire`** at full magnitude. The rule-14 line, stated
   before the solve: with the price unchanged in the screen span, the expectation is that these are
   **identical to the control**, and any movement is the exit-cohort consequence of a price that did
   move in a later year — reported, never evidence for the mechanism, and a worse band never
   evidence against it.
