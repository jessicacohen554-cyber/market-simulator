# RESULT — NYISO: the 2019–2022 retiree window and the measured monthly gas LEVEL, both PROMOTED

**Session:** `nyiso-fuelvintage-1` (v4, `session_01SvrWuTXxLxC1YRf2oZcGd9`) · **ISO:** NYISO only
· **Date:** 2026-09-09
**Pre-registration:** `results/calibration/PRECOMMIT-nyiso-fuelvintage-1.md` (v3, pushed before any
measurement) + `docs/ADDENDUM-nyiso-fuelvintage-1-promotion-2026-09-09.md` (pushed before the
composed bundle was scored)
**PROMOTED KEEPER:** `2026-09-09-nyiso-221-fuelvintage-span` (bundle `results/calibration/nyiso_fuelvintage_A`) — **CALIBRATED**
**Touchpoint:** `2026-09-09-nyiso-221-fuelvintage-tp2022`, folded to the keeper under rule 30
**Superseded keeper / control:** `2026-09-07-nyiso-213-summer-seam` (G-CTRL form 4 — **no control
solve was spent**, rule 29(b))

---

## 0. Bottom line

**Both changes are promoted, on the owner's ruling of 2026-09-09 (§A7) and on the merits.** The
headline is the **fleet**, and it is not inert: the 2019–2022 retiree window restores **31 units /
3,671.9 MW** to NYISO's held-out fleets, and in the one validation year NYISO can actually spend
it puts **0.655 TWh of Dunkirk coal back into the dispatch that the model previously did not
have**. The gas seam is promoted as measured — **provably LP-inert for NYISO**, reported as such,
and armed anyway because the owner ruled inertness is not a reason to withhold.

Five results:

1. **Card A is LIVE where it should be and DEAD where it should be, measured both ways.** The
   restored coal classes carry **exactly 0.000000 TWh in 2023, 2024 and 2025** and **0.6554 TWh in
   2022**. That two-sided measurement is stronger evidence than the charter's own gate.
2. **Card B is LP-inert for NYISO in every year tested** — `fuel_prices` **and** `mc_base`
   byte-identical in 2021, 2022, 2023, 2024, 2025 — because the Transco Z6 hub overlay covers
   12/12 months of every year and is applied last. Promoted anyway, as a **fallback level**.
3. **The 2022 touchpoint on the corrected fleet is WORSE on price**: C3a −12.5 % → **−13.8 %**,
   C3b NRMSE 0.229 → **0.242**. Under rules 1 / 14 the accurate input **stays** and the worse fit
   is a discovered root cause. Under rule 30(c) it does **not** downgrade NYISO.
4. **NYISO's ladder is 2022 ALONE.** 2020 was already known data-blocked; **2021 is data-blocked
   too**, on a different input, found by attempting it. Both authorizations remain **unspent**.
5. **Charter tasks 3 and 4 are discharged**, task 3 by an instrument that survives the fact that
   the committed keeper is *not* a valid control for a zero-delta claim.

---

## 1. CARD A — the fleet, and the two-sided measurement that proves it

`data/raw/eia-860/eia860_generator_retired_within_window.parquet`, `balancing_authority_code ==
"NYIS"`: 47 rows / 21 plants / 4,153.9 MW net summer. The widening is **additive**, so the added
set is the rows retiring before 2023 — **31 units / 3,671.9 MW**, reproducing the handoff exactly.

| retirement year | units | net summer MW | live in solve year | MW added |
|---|---|---|---|---|
| 2019 | 13 | 410.4 | 2019 | 3,671.9 |
| 2020 | 3 | **1,691.3** | **2020** | **3,261.5** |
| 2021 | 4 | 1,043.6 | **2021** | **1,570.2** |
| 2022 | 11 | 526.6 | **2022** | **526.6** |
| *(2023–24, pre-existing)* | *16* | *482.0* | **2023 / 2024 / 2025** | **0.0** |

Dominated by **nuclear** — Indian Point 2 (plant 2497, 1,011.5 MW net summer, retired 2020-04) and
Indian Point 3 (8907, 1,039.4 MW, 2021-04) = 2,050.9 MW — plus **1,487.0 MW of coal** (Somerset
676.4, Dunkirk 520.0, Cayuga 290.6).

### 1.1 The two-sided measurement

The charter's gate is `max |class-hour delta| = 0.000000 MW` against the committed keeper. G-DRIFT
predicted, before any solve, that this gate is **invalid for this arm** — two LIVE hunks landed on
`main` after the keeper solved (§4), so a nonzero delta is not evidence about the window. That
prediction held. What replaces it is **better**, because it measures the window's contribution
*directly* instead of inferring it from a total:

| solve year | `COAL_BIT` TWh | `COAL_PRB` TWh | what that means |
|---|---|---|---|
| 2023 | **0.000000** | **0.000000** | window contributes nothing in-sample |
| 2024 | **0.000000** | **0.000000** | window contributes nothing in-sample |
| 2025 | **0.000000** | **0.000000** | window contributes nothing in-sample |
| **2022** | 0.000000 | **0.655400** | window is LIVE — Dunkirk, 0 → **460.7 MW** peak, Jan–Apr |

The restored units enter `FleetArrays` in every year (the COD ramp deliberately does not touch
`pmax`), so they appear as two new reporting classes in all four — and they carry **identically
zero MW** in the three training years. **A channel that is demonstrably live in 2022 and
demonstrably dead in 2023–2025 is a much stronger statement than "the residual is small".**

This confirms, at the dispatch level, the v3 run's array-level **GATE T3** (charter task 3), which
swapped the *artifact* (shipped 1,094-row parquet vs the same file filtered to
`planned_retirement_year >= 2023`, which reproduces the pre-change 477-row artifact exactly) and
found, in all three training years: strictly additive (58 added columns, 3,694.643 MW, 0 removed),
**added columns pinned to zero availability AND zero `min_gen` across all 8,760 hours**, common
columns byte-identical in matched unit order, non-generator-axis LP inputs byte-identical. A
non-negative-cost LP column with an upper bound of 0 is fixed at 0, so those four conditions
**force** a zero contribution rather than sampling one — and, unlike a dispatch comparison, they
cancel the two LIVE hunks by construction.

### 1.2 What the window does in 2022 — the year NYISO can spend

Against `2026-09-07-nyiso-213-tp2022` (the **same keeper recipe** on the **old** fleet, so the
comparison isolates the window plus HEAD drift):

| class | old fleet TWh | corrected fleet TWh | Δ |
|---|---|---|---|
| **COAL_PRB** | 0.0000 | **0.6554** | **+0.6554** |
| CC_CHP | 13.9630 | 13.4171 | **−0.5459** |
| ST_GAS | 6.5639 | 6.5216 | −0.0423 |
| CT_PEAKER | 4.2780 | 4.2541 | −0.0239 |
| CC_REGULAR | 36.8917 | 36.8700 | −0.0217 |
| oil | 0.6320 | 0.6254 | −0.0066 |
| *(nuclear, import, wind, solar, biomass)* | — | — | **0.0000** |
| **system total** | 154.1835 | 154.1908 | +0.0073 |

Restored coal displaces gas, almost one-for-one, with the system total conserved. That is the
merit order behaving exactly as a real 520 MW PRB plant would make it behave.

---

## 2. CARD B — the gas seam is LP-inert for NYISO, and is promoted anyway

**Pre-registered** before the measurement: *"C3b unchanged to three decimals, and more strongly the
assembled generator gas price expected byte-identical."* Measured through the **sanctioned**
reconstruction (`replay_keeper.run_year_kwargs`, the STRICT meta→kwarg mapping):

| year | max abs Δ `fuel_prices` | max abs Δ `mc_base` | verdict |
|---|---|---|---|
| 2021 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |
| 2022 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |
| 2023 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |
| 2024 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |
| 2025 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |

Those arrays **are** the LP's input, so the LP is byte-identical. The v3 run measured 2023–2025;
this run confirms 2023 on the stricter reconstruction and **extends it to the two holdout years**,
so a flag-off touchpoint and a flag-on touchpoint are the *same solve* — measured, not inferred.

**Why, from the seam rather than the residual.** `resolve_fuel_prices` applies the EP-level seam at
`:151`, the F923 plant-monthly prints at `:228`, and `apply_hub_basis_overlay` at **`:229`** — the
Transco Z6 index is the **last** word on gas price, after both. Its coverage is **12/12 months in
every year 2019–2025** (the model's own log: *"hub-basis overlay (NYISO 2023, daily): 492 gas
generators repriced at the measured hub spot in 12/12 months"*), so **there is no month for the
seam's level to survive into**. The keeper series runs **above** the N3045 state blend in six of
seven years (2025 annual +1.180, Jan-2025 +5.107 $/MMBtu) — which is what downstate NYC gas being
dearer than the NY state mean looks like. **The ordering is right**, and the §4 STOP was not tripped.

**What promoting it buys, stated honestly.** At HEAD, nothing measurable. Structurally, a
**fallback level** under the rule 19 `[R-ONE-MECH]` ordering: in any month the hub index does not
cover, NYISO's gas would otherwise fall back to the annual trajectory × generic climatological
shape, and with the flag armed it falls back to that month's **measured** state-blended delivered
cost. Reported at full magnitude and claimed as nothing more.

*(Two corrections to the handoff's account, both found by reading the code. (a) The hub overlay
supersedes **the F923 prints as well as** the seam. That matters because the print path writes only
**56.738 %** of NYISO gas capacity-hours — 265 of 492 gas units — **not** the ~100 % MISO shows, so
**the prints alone would NOT have made this inert**; the hub overlay is what does. (b) §A2's claim
that all five keepers carry `gas_plant_monthly_fuel_pricing = True` is **right for NYISO but
unverifiable from a recipe**: the field is set by `pipeline/backcast_config.py:2178` as
`gas_plant_monthly_fuel_pricing=(iso != "ERCOT")`, so it never appears in a `meta.json` or a
`run_year` kwarg. Check the config builder, not the recipe.)*

---

## 3. The validation ladder — 2022 ALONE, and both blocks are DATA, not governance

| rung | status | binding reason |
|---|---|---|
| 2019 | **REFUSED** | locked-test tier, `final` empty, freeze ACTIVE — every ISO |
| 2020 | **DATA-BLOCKED** | `eia_generation_profiles.parquet` starts at 2021; NYISO alone of seven reaches that fallback, because it reports **zero** utility-scale solar to EIA-930 |
| 2021 | **DATA-BLOCKED** | `data/raw/NYISO-AS/requirements/` starts at 2022; `nyiso_dynamic_reserve_requirements` **fail-closes** rather than reverting to the static requirements it replaces |
| **2022** | **SOLVED · SCORED · REGISTERED** | — |

**2021 was found by attempting it**, and the refusal is the mechanism working. The only way to
make 2021 solve today is to disarm that flag for one year, which is **refused on rule 22**: a
touchpoint *is* the keeper's frozen recipe on a held-out year, so a per-year recipe variant is
per-year fitting wearing a touchpoint's name. Details and the intake route:
`docs/FINDING-nyiso-2020-touchpoint-data-blocked-2026-09-09.md` §§3, 7.

**Nothing is spent.** `holdout_policy` returns no refusal for 2020 or 2021, the `complete` marker
is present and correctly re-keyed, and the freeze is scoped to the locked test alone. Rule 22's own
split settles it: *what is held out is the SCORE, never the DATA* — these are input-readiness gaps,
so **both authorizations remain real and entirely UNSPENT**.

### 3.1 The 2022 result, at full magnitude

Same keeper recipe, same year, corrected fleet — vs `2026-09-07-nyiso-213-tp2022`:

| criterion | old fleet | **corrected fleet** | move |
|---|---|---|---|
| C1 fuel-mix (CC_REGULAR) | FAIL +5.01 TWh, +3.8 pp | FAIL **+4.99 TWh, +3.8 pp** | −0.02 TWh |
| C2 system volume | PASS | **PASS** | held |
| **C3a mean LMP** | FAIL −12.5 % | FAIL **−13.8 %** | **worse, −1.3 pp** |
| **C3b price shape** | FAIL NRMSE 0.229 | FAIL **NRMSE 0.242** | **worse, +0.013** |
| C3c price tail | CAVEAT 10 h vs 101 h | CAVEAT 10 h vs 101 h | unchanged |
| C4 dispatch corr. | PASS | **PASS** | held |
| C6 governance | PASS | **PASS** | held |
| C8 forced share | PASS | **PASS** | held |

**The price fit gets worse, and the input stays.** The mechanism is not mysterious: model 2022
prices were already 12.5 % below actual, and adding 0.655 TWh of cheap PRB coal to the bottom of
the stack pushes them further down. Rule 14 `[R-ACCURATE]` is explicit that this is a **discovered
root cause, not a reason to revert** — the estimate (a fleet missing Dunkirk) was silently
compensating for a NYISO 2022 price level that is too low for some other reason. Rule 1
`[R-STRUCT]`: a structurally-correct mechanism is never judged by the residual.

**Rule 30(c): a held-out year never downgrades the ISO.** NYISO's determination is the train-tier
verdict and nothing else; the 2022 rung is iterable model-**selection** evidence and must never be
quoted as a certified out-of-sample skill number.

---

## 4. G-DRIFT — the committed keeper is not a valid zero-delta control, and why that was fine

The keeper's recorded `git_sha 51f2fc2d` is **unreachable** (squash-merged branch; this clone is
shallow). The v3 run anchored the base **by content** instead — recomputing the capx D79
solve-surface projection over `main`'s history reproduces the bundle's recorded fingerprint
`48353917f7510af3` / 206 rows exactly at `2084dc8a` and at no later state — and audited
`2084dc8a → HEAD` (36 files, +3,348 / −130) hunk by hunk. **Any later NYISO lane should expect the
same unreachable-sha problem and use that method rather than a date-nearest guess.**

**Two hunks are LIVE**, and both are **retained** as correct constructions (rules 1 / 14 — a
correct construction is not disarmed to make a differencing convenient):

| # | hunk | measured NYISO footprint |
|---|---|---|
| **L1** | `f923_gas_price_plausibility_screen` — a declared (b′-1) default flip to `True` (SPP-49 / owner ruling P19), reached because this keeper is `mode="backcast"` **and** prices gas per-plant from F923 | **68,919 rows examined, ZERO moved** — every own-reported NYISO gas plant-month already sits inside `[0.5, 2.0] ×` its state N3045 reference. Confirmed again in 2025: *"59 plant-months in band, 0 low, 0 negative, 0 high → reference (0 plants)"* |
| **L2** | `_apply_simple_cycle_hr_floor` (`data/fleet/eia860.py`) — unconditional, frame-level | **3 plants clamped**: Greenport 2681 8.000 → 9.000, Chautauqua LFGTE 57186 6.053 → 9.000, Albany Medical Cogen 59453 5.773 → 9.000 MMBtu/MWh |

**L2 is the whole of the residual dispatch difference, and it is quantified.** Differencing each
training year against the committed keeper:

| year | max abs class-hour Δ | cells moved | largest class Δ (TWh) | system total Δ (TWh) |
|---|---|---|---|---|
| 2023 | 875.03 MW | 3.54 % | CC_REGULAR −0.0030 | **−0.000229** |
| 2024 | 737.42 MW | 4.61 % | CT_PEAKER −0.0039 | **−0.000015** |
| 2025 | 1,000.00 MW | 8.40 % | **CT_PEAKER −0.0139** | **+0.000092** |

The signature is L2's exactly: **the simple-cycle class loses energy** (its three plants' offers
rose) and it reappears in the gas classes (2025: CC_CHP +0.0046, CC_REGULAR +0.0042, ST_GAS
+0.0030, ST_CHP +0.0016, summing to the CT_PEAKER loss), with system totals conserved to ≤ 0.0003
TWh. The large *hourly* numbers are budget-constrained **hydro** reshuffling within its month: 2025
hydro annual energy is **24.058901 TWh on both sides — a delta of exactly 0.000000** — so those are
alternate-optimum reallocations across hours, not a mechanism.

**The effective-config diff confirms there is nothing else.** Comparing the two runs' recorded
`scenario_config` dumps, the only substantive fields that differ are `f923_gas_price_plausibility_
screen` (L1, absent → True) and `gas_electric_power_monthly_level` (this session's promotion,
absent → True). Everything else is a HEAD-added field at its falsy default, or the two per-year
selection keys (`weather_year`, `gas_price_override`). **No control solve was spent** (rule 29(b);
§A6 names a control solve as both a governance deviation and the cause of the PJM OOM).

---

## 5. Governance

- **Rule 21 `[R-DOF]`: ZERO free parameters added or moved.** The keeper's DOF ledger (13 entries,
  `n_residual` 6) is carried **verbatim**, and `scripts/gen_nyiso214_attestation.py` **refuses to
  write the attestation** if it is not — the carry is computed, not typed. `authorized_price_tuning`
  is **NONE**: the offer bands are the superseded keeper's, byte-identical.
- **Rule 19 `[R-ONE-MECH]`:** three strictly-ordered gas levels — national annual < state-average
  monthly (this seam) < measured hub index — each superseding the last, nothing stacked.
- **Rule 16 `[R-ALLYEARS]`:** ONE registered bundle covering 2023–2025, solved in a single
  invocation. The T1 / T2 shards are throwaway diagnostics, gitignored, never registered.
- **Rule 29 `[R-SCREEN]`:** the planned SHARD F screen solve was **not spent** — a zero-LP
  pre-solve gate answered it (clause (0)).
- **Rule 31 `[R-RETAIN]`:** every bundle stays on local disk; the delete-before-merge duty is
  discharged by `.gitignore`, never by `rm`. See §6.
- **Rule 12 `[R-PARALLEL]`:** at most two concurrent invocations, years sequential within each.

### 5.1 An operational finding for every lane

**Cloud solve shards that finish and are archived without pushing lose their bundles.** This
session's v3 run launched five; T1 and T2 both **completed** and were archived with no branch
pushed, so ~2 hours of LP went with their containers. That is rule 31's failure mode arriving by
container reclamation rather than by `rm`. This run re-solved everything **in its own container**,
where the artifacts survive to be registered. Two contributing gotchas, both now fixed here:
`data/clean/` is gitignored and absent in a fresh container (a NYISO solve **hard-fails** deep in
`run_year` without it; `regenerate_clean.py` takes 30+ minutes), and an untracked `results/_shared/`
made the tree dirty, which **refuses `--reuse-solved`** on the next shard — measured: the composed
run could not reuse T1's already-solved 2023/2024 and re-solved all three years. `results/_shared/`
is now gitignored.

---

## 6. Bundles on disk — RULE 31, AND THE PROMOTION QUESTION

**This container is ephemeral and these bundles are gitignored, so they do not survive the
session.** Nothing has been deleted.

| bundle | years | disposition |
|---|---|---|
| `results/calibration/nyiso_fuelvintage_A` | 2023 2024 2025 | **PROMOTED KEEPER** `2026-09-09-nyiso-221-fuelvintage-span` — registered, and its slim files + `hourly/` sidecars are **COMMITTED** (rule 15) |
| `results/calibration/nyiso_fuelvintage_H2` | 2022 | touchpoint `2026-09-09-nyiso-221-fuelvintage-tp2022` — registered, stamped, **COMMITTED** |
| `results/calibration/nyiso_fuelvintage_T1` | 2023 2024 | throwaway shard, superseded by `_A` |
| `results/calibration/nyiso_fuelvintage_T2` | 2025 | throwaway shard, superseded by `_A` |
| `results/nyiso_fuelvintage_H1` | 2021 | **aborted** — data-blocked before the LP (§3) |

### 6.1 THE PROMOTION QUESTION, ASKED EXPLICITLY (rule 31)

**What is already promoted, and needs no further decision:** the keeper move to
`2026-09-09-nyiso-221-fuelvintage-span` and the touchpoint, both **committed** — they survive the
session and are on the dashboard.

**What does NOT survive, and what I would like ruled on:**

1. **The T1 / T2 shards** (`nyiso_fuelvintage_T1`, `_T2`) are gitignored throwaways fully
   superseded by the composed `_A` bundle, which carries the same three years solved in one
   invocation. **I recommend letting them go** — nothing in this report depends on them that `_A`
   does not also carry. Say so and they can be discarded; say otherwise and they need committing
   before this container is reclaimed.
2. **The aborted 2021 run** produced no artifacts (it died in input assembly), so there is nothing
   to keep.
3. **The open decision I cannot make**: whether to fund the two intakes that would unblock NYISO's
   2020 and 2021 rungs — the additive 2020 extension of `eia_generation_profiles.parquet` (§3, and
   it is an **all-ISO** artifact, so it should be done once for every ISO per rule 22) and the
   backward extension of the Ask-B NYISO reserve-requirement series to 2021 and earlier. Both are
   unrestricted under rule 22 and neither needs a marker. **Until they land, NYISO's validation
   ladder is 2022 and cannot be anything else.**

**Nothing was deleted.** Rule 29(c)'s delete-before-merge duty is discharged by `.gitignore`, per
rule 31 and the ercot-255 correction.
