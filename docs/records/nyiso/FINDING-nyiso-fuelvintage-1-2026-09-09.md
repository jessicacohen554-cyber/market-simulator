# FINDING — nyiso-fuelvintage-1: the 2019–2022 retiree window is provably inert in-sample, and the fuel seam is provably inert outright

**Session:** `nyiso-fuelvintage-1` · **ISO:** NYISO only · **Date:** 2026-09-09
**Branch:** `claude/nyiso-fuelvintage-1` off `origin/main` `87ad084b`
**Keeper:** `2026-09-07-nyiso-213-summer-seam` (`results/calibration/nyiso213_summer_seam`)
**Pre-registration:** `results/calibration/PRECOMMIT-nyiso-fuelvintage-1.md` (committed `7f211902`,
**before** any measurement below)
**Charter:** `docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md`, tasks 3 + 4

---

## 0. Bottom line

Four results, **all reached at ZERO LP cost**:

1. **CARD 1 — the fuel ordering check PASSES, and the prediction was byte-identity, registered
   before the measurement.** With `gas_electric_power_monthly_level` armed on the keeper recipe,
   the assembled `fuel_prices` **and** `mc_base` arrays are **byte-identical in 2023, 2024 and
   2025** (max |Δ| = 0.0 each year). Those arrays *are* the LP's input, so the LP is byte-identical.
   **The planned SHARD F screen solve was NOT spent.** The flag stays OFF; that is the correct
   outcome and it costs NYISO nothing.
2. **GATE T3 / charter task 3 — PASSES in all three training years**, by an instrument stronger
   than the dispatch comparison the charter asked for, and without the control solve rule 29(b)
   refuses.
3. **G-DRIFT found TWO LIVE hunks** that make the committed keeper an invalid control for a
   zero-delta claim — and then measured both. One (`f923_gas_price_plausibility_screen`) moves
   **zero** NYISO rows; the other (the SPP-49 simple-cycle heat-rate floor) fires on **3 small
   plants**. Neither can affect GATE T3, which cancels them by construction.
4. **Charter task 4 is done**, and it was not a deletion: the retired caveat is replaced by its
   honest successor, found by reading the seam.

The four solve shards (T1/T2 training, H1/H2 validation touchpoints) are running in their own
containers; their results are **not** in this document.

---

## 1. G-DRIFT — the keeper's `git_sha` is unreachable, so the base was anchored by CONTENT

`run_config.json` records `git.sha = 51f2fc2d` on branch `claude/nyiso-backcast-calibration-b6er34`.
**That object is not in this clone and cannot be fetched** — the branch was squash-merged and
deleted, so its commits survive only under `refs/pull/*`. `git cat-file -t`, `git fetch origin
51f2fc2d` and a fetch of the branch ref all fail. (Session nyiso-220 could still resolve it on
2026-09-06 and reported "45 files on the solve path have changed since the keeper's `git_sha`";
that handle is now gone. **Any later NYISO lane should expect the same** and use the method below
rather than a date-nearest guess.)

**The method.** The bundle records the capx D79 solve-surface stamp
(`fingerprint 48353917f7510af3, rows 206`). Recomputing `solve_surface.surface_rows("NYISO")` at
each distinct historical state of the seven `SURFACE_MODULES` over `origin/main`'s last 400
commits reproduces that fingerprint **exactly at `2084dc8a` and at no later state**:

| representative commit | NYISO fingerprint | rows |
|---|---|---|
| `30647483`, `27e058d3`, **`2084dc8a`** | **`48353917f7510af3`** | **206** |
| `8a8498a7` | `8569b48ab932ed6d` | 208 |
| `f2cd8acc`, `87ad084b` (HEAD) | `1eefed492204fab7` | 209 |

**G-DRIFT base := `2084dc8a`**, the newest commit whose NYISO surface projection is byte-identical
to the keeper's — a conservative superset base. The audit is then `2084dc8a → HEAD`: **36 files,
+3,348 / −130**.

### 1.1 What the fingerprint closes mechanically

* **Zero shared rows changed value.** No registry table NYISO's solve is sensitive to has moved —
  closing `constants.py`, `capacity_market.py`, `fuel_trajectories.py`, `ercot_envelopes.py`,
  `plant_taxonomy.py`, `entry_config.py`, `offer_curve_base/generic.py` in one step.
* **Three new names**, each classified individually below (a new name has no declaration to differ
  from, so the cache key is silent about it — only a read-path audit settles it).
* Every new `ScenarioConfig` field is `default = False`; `iso_configs.py` is **absent from the
  diff** (no per-ISO override moved); `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` gained **exactly
  one** entry and **zero existing defaults changed**.

### 1.2 The two LIVE hunks, and their MEASURED footprints

| # | hunk | why LIVE | measured footprint (NYISO 2023, keeper recipe) |
|---|---|---|---|
| **L1** | `f923_gas_price_plausibility_screen`, new 2026-09-08 (SPP-49 / owner ruling P19), a (b′-1) declared default flip to `True` | its `__post_init__` coercion fires only when **not** (backcast or hindcast) **and** `gas_plant_monthly_fuel_pricing`; this keeper is `mode="backcast"` **and** has that flag on, so **the screen is ON where the keeper solved without it** | **68,919 rows examined, 0 moved.** Every own-reported NYISO gas plant-month already sits inside `[0.5, 2.0] ×` its state N3045 reference. **Armed, but its effect on NYISO is nil.** |
| **L2** | `_apply_simple_cycle_hr_floor` (`data/fleet/eia860.py`) — its docstring: *"A CONSTRUCTION, not a gate … every fleet read path picks it up"* | unconditional and frame-level | **3 plants / 10 rows**: Greenport 2681 (8.000 → 9.000), Chautauqua LFGTE 57186 (6.053 → 9.000), Albany Medical Ctr Cogen 59453 (5.773 → 9.000). **LIVE.** Independently reproduced in `derive_nuclear_monthly_cf.py`'s own log. |

**Consequence, stated in the PRECOMMIT before any number existed:** the committed keeper is **not**
a valid control for a `max |class-hour delta| = 0.000000` claim, because L2 moves that number for a
reason that is not the retiree window. **No control solve was spent** (rule 29(b)); §3 replaced it.
L1 and L2 are HEAD's owner-ruled posture and **stay armed** — rules 1 `[R-STRUCT]` / 14
`[R-ACCURATE]`: a correct construction is not disarmed to make a differencing convenient.

*(One observation, reported and not acted on: plant 59453 is named a cogen and the SPP-49 docstring
puts CHP plants out of scope, yet it is clamped. That is the SPP-49 lane's design to adjudicate,
not NYISO's — routed, not absorbed.)*

### 1.3 INERT, each with its reason

Hydro budget period (`hydro_budget_period_by_instrument`, off — and with `hydro_period_hours=None`
the new family loop in `lp/rows.py` reduces to `[(0, all)]`, the pre-change single call);
`floors.py` (+306, behind two off flags); `renewables.py` (+185, behind `vre_curtailment_oversupply_allocation`);
the EP-seam files themselves (behind this session's own flag); `fuel/basis/ercot.py` (ERCOT's
branch **and** an off flag); `interchange/spec.py`, `interchange/pjm.py`, `eia930/envelopes.py`
(PJM's branch); `capacity_evolution/ccs.py` + `evolve.py` + `runner.py`'s evolution ledger
(forecast-only — a backcast rebuilds its base fleet yearly and never enters `evolve_fleet`);
`arrays.py`'s duplicate-`unit_id` guard (raises on a defect, decides nothing, and duplicates are an
evolved-fleet event); `results/cache.py` (docstring only — no code line added);
`scripts/lib/key_provenance.py` + the CLI surface; `data/raw/_validation-source/actual_lmp.json`
(**one hunk, entirely inside the SPP block** — NYISO's scoring actuals untouched); and
`_PARTIAL_EXIT_WINDOW_START 2023 → 2019` (ercot-261), which is gated on `partial_plant_exit_carry`
— **`False` in this keeper**, so the handoff's double-count question **cannot arise for NYISO** and
is reported moot rather than tested.

---

## 2. CARD 1 — the fuel seam is provably inert, and the ordering is right

**Pre-registered** (PRECOMMIT §2, before the measurement): *"C3b unchanged to three decimals, and
more strongly the assembled generator gas price expected byte-identical."*

**Measured:**

| year | `fuel_prices` byte-identical | max abs Δ | `mc_base` byte-identical | max abs Δ |
|---|---|---|---|---|
| 2023 | **yes** | 0.0 | **yes** | 0.0 |
| 2024 | **yes** | 0.0 | **yes** | 0.0 |
| 2025 | **yes** | 0.0 | **yes** | 0.0 |

**Why, from the seam rather than the residual.** `resolve.py` applies the EP-level seam at `:151`,
the F923 plant-monthly prints at `:228`, and `apply_hub_basis_overlay` at **`:229`** — the Transco
Z6 index is the **last** word on gas price. Phase 0 measured its coverage at **12/12 months in
every one of 2019–2025**, running above the N3045 state blend in six of seven years:

| year | hub months | hub annual | EP-seam annual | hub − EP | max month gap | Jan gap |
|---|---|---|---|---|---|---|
| 2019 | 12/12 | 3.052 | 3.012 | +0.040 | 1.082 | +0.169 |
| 2020 | 12/12 | 2.101 | 2.135 | −0.034 | 0.473 | −0.433 |
| 2021 | 12/12 | 4.413 | 3.879 | +0.533 | 0.977 | +0.554 |
| 2022 | 12/12 | 8.427 | 7.050 | +1.377 | 3.644 | +3.644 |
| 2023 | 12/12 | 3.368 | 2.936 | +0.432 | 1.330 | −1.330 |
| 2024 | 12/12 | 2.789 | 2.683 | +0.106 | 0.774 | +0.686 |
| 2025 | 12/12 | 5.558 | 4.378 | +1.180 | **5.107** | +5.107 |

So there is **no month for the seam's level to survive into**, and the "downstate NYC gas is dearer
than the state mean" reasoning is confirmed in the numbers.

**Two corrections to the handoff's account**, both found by reading the seam:

* The hub overlay supersedes **the F923 prints as well as** the seam, not merely the seam.
* The A2 written-cell census is why that matters here: the print path writes only **56.738 % of
  NYISO gas capacity-hours** (265 of 492 gas units; 35.982 % of all cells) — **not** the ~100 % MISO
  shows. **The prints alone would NOT have made this inert.** The hub overlay is what does.

**SHARD F was not spent** (rule 29 `[R-SCREEN]` clause (0)). Matrix cell
`gas_electric_power_monthly_level` moved **O → I** with a DO-NOT-REDO condition naming the only
evidence that could reopen it: *a month the hub index does not cover* — not a re-run.

---

## 3. GATE T3 / charter task 3 — PASS, and a correction to my own first test

**My first formulation was wrong and I corrected it before reporting.** It required an identical
`n_gen` between the arm (shipped 1,094-row artifact) and the control (the same artifact filtered to
`planned_retirement_year ≥ 2023`). That is the wrong test: the charter itself says the COD ramp
*never touches `pmax`*, so the added units are **supposed** to enter `FleetArrays`. Demanding
identical arrays fails by construction and proves nothing.

**The correct test, and what now runs** — the swap is on the **artifact**, not on one call site,
because `load_retired_within_window` is reached from `runner`, `outages` and the COD map, and a
per-call patch would let those three disagree:

1. **strictly ADDITIVE** — no control unit disappears;
2. **added columns PINNED TO ZERO** — `availability` *and* `min_gen` identically zero across all
   8,760 hours;
3. **common columns byte-identical in matched unit order** — every generator-axis array plus
   `mc_base` and `fuel_prices`;
4. **non-generator-axis LP inputs byte-identical**.

| year | control `n_gen` | arm `n_gen` | added | added pmax | added max avail | added max `min_gen` | removed | common | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 812 | 870 | 58 | 3,694.643 MW | **0.0** | **0.0** | 0 | 812 identical | **PASS** |
| 2024 | 809 | 867 | 58 | 3,694.643 MW | **0.0** | **0.0** | 0 | 809 identical | **PASS** |
| 2025 | 809 | 867 | 58 | 3,694.643 MW | **0.0** | **0.0** | 0 | 809 identical | **PASS** |

**Why this is stronger than the gate the charter asked for.** A non-negative-cost LP column whose
upper bound is 0 is fixed at 0 and contributes exactly 0 to any optimal solution. So (1)–(4)
**force** `max |class-hour delta| = 0.000000 MW` **by construction**, where an 8,760-hour dispatch
comparison could merely coincide. It is also immune to L1/L2: both are identical in the two arms of
the artifact swap and cancel exactly — which is what let charter task 3 be discharged **despite**
the committed keeper being an invalid control.

**The pre-change reconstruction is exact**, not an approximation: filtering to
`planned_retirement_year ≥ 2023` yields **477 rows / 141 plants / years 2023–2024 only**, matching
the charter's description of the shipped pre-change artifact byte-for-byte.

**The grains reconcile.** `load_retired_within_window("NYISO")` returns **45** generators /
4,187.600 MW / 19 plants on the shipped window and **14** / 491.900 MW / 3 plants on the
reconstruction — a difference of **31 generators / 3,695.700 MW / 16 plants**. That 31 is the
handoff's unit count exactly; 3,695.700 vs its 3,671.9 MW is nameplate vs net-summer on the same
rows; and 31 generators become 58 LP columns under the keeper's CAMPD per-plant binning.

---

## 4. The NYISO retiree census (the fleet, which is the headline)

Parquet grain, `balancing_authority_code == "NYIS"`: 47 rows / 21 plants / 4,153.9 MW net summer.
The **added** rows — those the 2023 → 2019 window move introduces:

| retirement year | units | plants | net summer MW |
|---|---|---|---|
| 2019 | 13 | 9 | 410.4 |
| 2020 | 3 | 3 | 1,691.3 |
| 2021 | 4 | 2 | 1,043.6 |
| 2022 | 11 | 5 | 526.6 |
| **added total** | **31** | — | **3,671.9** |

Live in each solve year: **2020 +3,261.5 MW · 2021 +1,570.2 MW · 2022 +526.6 MW** — reproducing the
handoff exactly. Dominated by **nuclear**: Indian Point 2 (2497, 1,011.5 MW net summer, retired
2020-04) and Indian Point 3 (8907, 1,039.4 MW, retired 2021-04) = 2,050.9 MW; plus **1,487.0 MW of
coal** (Somerset 676.4, Dunkirk 520.0, Cayuga 290.6). **Zero added rows retire in 2023 or later**,
which is the artifact-level precondition for §3.

---

## 5. Charter task 4 — retired, and replaced rather than deleted

The caveat read *"A 2018-2021 solve is short that capacity regardless of this overlay."* **That is
now false** — the fleet channel restores it, and the CF overlays are **intensive** and never could
have. Retired.

It is **not** a plain deletion. Reading the seam turned up the successor caveat, which is now in
the file: `derive_nuclear_monthly_cf.py` builds its fleet from `load_fleet_from_csv`, which the
retiree injection **does not feed**, so both numerator and denominator remain the operable
4-reactor upstate fleet — every committed value is byte-unchanged and `--check` still reports
*"committed table matches the EIA-923 derivation"*. But `fleet/arrays.py` applies the monthly CF
**uniformly to every nuclear row**, so the restored Indian Point units carry the **upstate fleet's**
measured monthly CF rather than their own metered output: their *presence and retirement timing* are
measured, their *within-year shape* is not.

**Routed, not absorbed:** re-deriving the CF over the injected fleet is a change to the derive's
**fleet definition**, not a rule-23 `[R-FROZEN-DERIVE]` data refresh (the source data has not
moved), so it goes back to the charter rather than being done here.

---

## 6. Gate baselines, re-measured on THIS tree (ADDITION 6)

| gate | result | verdict |
|---|---|---|
| `pytest tests/scoring` | **16 failed / 1,532 passed** / 12 skipped | exactly A3's corrected baseline — **this branch adds none** |
| `check_cache_key_registration --base origin/main` | RED, `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` undeclared | the named pre-existing red — **not this lane's** |
| `check_mechanism_matrix --base origin/main` | **exit 0** (anchor warnings pre-existing) | green, and still green after the cell edit |

## 7. One operational finding worth carrying to every lane

**`data/clean/` is gitignored, derived, and absent in a fresh container**, and a NYISO solve dies
deep in `run_year` on a hard `FileNotFoundError` (capacity-deliverability, then
`nyiso-interface-flows`) rather than no-opping. `scripts/regenerate_clean.py` must run before any
solve; it took **well over 30 minutes** here because it curates every datatype for every ISO, while
an individual datatype takes seconds. Every shard prompt in this session carries the step
explicitly.
