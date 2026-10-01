# PRECOMMIT — nyiso-fuelvintage-1: the 2019–2022 retiree window (+ the near-inert fuel check)

**Session:** `nyiso-fuelvintage-1` · **ISO:** NYISO only (rule 25 `[R-ISO-SCOPE]`) · **Date:** 2026-09-09
**Branch:** `claude/nyiso-fuelvintage-1`, off `origin/main` `87ad084b`
**Keeper / control:** `2026-09-07-nyiso-213-summer-seam`, bundle `results/calibration/nyiso213_summer_seam`
**Charter:** `docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md` tasks 3 + 4
**Prompt:** `docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md` PROMPT 3 + ADDENDUM A1–A4
**Phase-0 basis:** `docs/FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md` §3 §4 §5

Every number below is written **before** any LP is spent. Nothing here is restated after a result.

---

## 1. CARD 0(a) — G-DRIFT, and a correction to how the base is identified

### 1.1 The keeper's `git_sha` is UNREACHABLE, so the base is anchored by CONTENT instead

`run_config.json` records `git.sha = 51f2fc2d` on branch
`claude/nyiso-backcast-calibration-b6er34`. That object **is not in this clone and cannot be
fetched** — the branch was squash-merged and deleted, so its commits survive only under
`refs/pull/*`. `git cat-file -t 51f2fc2d`, `git fetch origin 51f2fc2d` and
`git fetch origin refs/heads/claude/nyiso-backcast-calibration-b6er34` all fail. A date-nearest
guess at the base is not good enough for a form-4 differencing, so the base is identified
**by content** instead, using the capx D79 solve-surface fingerprint the bundle itself records:

```
bundle solve_surface.json : fingerprint 48353917f7510af3, rows 206, moved {}
```

Recomputing `solve_surface.surface_rows("NYISO")` at each distinct historical state of the seven
`SURFACE_MODULES` over the last 400 commits of `origin/main` reproduces that fingerprint **exactly**
at `2084dc8a` and at no later state:

| representative commit | NYISO fingerprint | rows |
|---|---|---|
| `30647483`, `27e058d3`, **`2084dc8a`** | **`48353917f7510af3`** | **206** |
| `8a8498a7` | `8569b48ab932ed6d` | 208 |
| `f2cd8acc`, `87ad084b` (HEAD) | `1eefed492204fab7` | 209 |

**G-DRIFT base := `2084dc8a`** — the NEWEST `origin/main` commit whose NYISO surface projection is
byte-identical to what the keeper recorded. This is a conservative (superset) base: anything the
keeper's own branch carried beyond it is its own mechanism, which is in the replayed recipe.

### 1.2 What the fingerprint proves on its own

Diffing the keeper-base row set against HEAD's:

* **CHANGED VALUE on shared rows: ZERO.** No registry table NYISO's solve is sensitive to has
  moved. This mechanically closes `constants.py`, `capacity_market.py`, `fuel_trajectories.py`,
  `ercot_envelopes.py`, `plant_taxonomy.py`, `entry_config.py` and `offer_curve_base/generic.py`.
* **REMOVED: none. NEW: three** — `EGRID_CT_HR_PHYSICAL_FLOOR`,
  `F923_GAS_PRICE_PLAUSIBILITY_BAND`, `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`. Each is classified
  individually below; a new name cannot move a cache key (it has no declaration to differ from),
  so the key is silent about them and only a read-path audit can settle them.

### 1.3 The code-level audit — `2084dc8a → HEAD`, 36 files, +3,348 / −130

Scope: `src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`.

**Two mechanical closures first.** (a) Every new `ScenarioConfig` field is `default = False`:
`hydro_budget_period_by_instrument`, `netload_drag_merit_allocation`,
`netload_drag_min_run_persistence`, `vre_curtailment_oversupply_allocation`,
`gas_electric_power_monthly_level`, `pjm_seam_neighbour_hourly_ladder`,
`ercot_ep_gas_basis_corroborated` — and none is in the keeper's recipe. (b) `iso_configs.py` is
**not in the diff at all**, so no per-ISO `default_scenario_overrides` moved. (c) The declared
default-flip registry `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` gained **exactly one** entry, and
**zero existing field defaults changed**.

#### LIVE (2)

| # | hunk | why it is LIVE for THIS keeper |
|---|---|---|
| **L1** | `f923_gas_price_plausibility_screen: bool = True` — new 2026-09-08 (SPP-49, owner ruling P19), a (b′-1) declared default flip with frozen drop value `"False"` | Its `__post_init__` coercion fires only when **not** (`mode=="backcast"` or `hindcast`) **and** `gas_plant_monthly_fuel_pricing`. This keeper is `mode="backcast"` **and** `gas_plant_monthly_fuel_pricing=True`, so **the coercion does not fire and the screen is ON**, where the keeper solved with it absent. It rewrites any own-reported gas plant-month outside `[0.5, 2.0] ×` the plant's state N3045 reference. |
| **L2** | `_apply_simple_cycle_hr_floor` (`data/fleet/eia860.py`, new, +112) | **Unconditional and frame-level by design** — its own docstring: *"A CONSTRUCTION, not a gate … every fleet read path picks it up."* Clamps a simple-cycle-only, non-CHP plant's eGRID heat rate up to `HEAT_RATE_BINS["gas_ct"]["aero"]`. Fires for NYISO iff such a plant exists; `egrid_family_heat_rates` and `measured_ct_heat_rates` (both ON here) still take precedence where armed, so the residual reach is measured, not assumed. |

#### INERT (everything else), each with its reason

| hunk(s) | INERT because |
|---|---|
| `data/hydro.py` (+122), `pipeline/kwargs.py` `resolve_hydro_period_hours`, `model/lp/rows.py` hydro families | double-gated on `hydro_budget_period_by_instrument` (default off, absent from the recipe). With `hydro_period_hours is None` the family list is `[(0, all)]`, which reproduces the pre-change single `_build_hydro_rows` call exactly. |
| `data/fleet/floors.py` (+306) | all new behaviour behind `netload_drag_merit_allocation` / `netload_drag_min_run_persistence`, both off; the rest is docstring. |
| `data/renewables.py` (+185) | behind `vre_curtailment_oversupply_allocation`, off. |
| `data/fuel/electric_power.py` (+172), `fuel/resolve.py`, `fuel/trajectories.py`, `fuel/__init__.py`, `data/raw/reference/iso-gas-capacity-state-weights.csv` | the seam itself — behind `gas_electric_power_monthly_level`, off (and it is this session's own arm). |
| `data/fuel/basis/ercot.py` (+118) | ERCOT's branch **and** behind `ercot_ep_gas_basis_corroborated`, off. |
| `model/interchange/spec.py` (+133), `interchange/pjm.py` (+46), `data/eia930/envelopes.py` (+50) | PJM's branch (`PJM_SEAM_LADDER_*`), behind `pjm_seam_neighbour_hourly_ladder`, off. |
| `model/capacity_evolution/ccs.py` (+121), `evolve.py` (+98), and `runner.py`'s evolution-ledger block | forecast-only path; a `mode="backcast"` run rebuilds its base fleet yearly and **never enters `evolve_fleet`**. |
| `data/fleet/arrays.py` duplicate-`unit_id` guard (+39) | raises on a defect, decides nothing; duplicates are an EVOLVED-fleet event only, so it is silent on every backcast (the hunk says so, and a backcast never evolves). |
| `results/cache.py` (+154) | docstring only — no code line added. |
| `scripts/lib/key_provenance.py` (+99), `scripts/run_calibration*.py` (+306) | provenance/CLI surface; new flags default off, no solve default moved. |
| `data/raw/_validation-source/actual_lmp.json` (+158) | one hunk, entirely inside the **SPP** trading-hub block. NYISO's scoring actuals are untouched. |
| `_PARTIAL_EXIT_WINDOW_START` `2023 → 2019` (`eia860.py`, ercot-261) | gated on `partial_plant_exit_carry`, which is **`False`** in this keeper's recipe. The channel is off, so the ADDITION-0 double-count question against the whole-plant parquet **cannot arise for NYISO** and is reported as moot rather than tested. |

### 1.4 CONSEQUENCE — G-CTRL form 4 is NOT valid for the training span, and I say so before solving

Rule 29(b) makes the committed keeper the control **when every hunk is INERT**. Two are not.
Therefore:

* The keeper's committed bundle **remains** the control for the *touchpoint* differencing (CARD 2),
  where the comparison is against `2026-09-06-nyiso-209-2022-touchpoint` and the effect under
  study (≈3.7 GW of restored fleet) is orders of magnitude above the L1/L2 footprint. The L1/L2
  delta is reported beside it, never netted out.
* The keeper's committed bundle **is NOT** a valid control for charter task 3's
  `max |class-hour delta| = 0.000000 MW` gate, because L1 and L2 move that number **for reasons
  that are not the retiree window**. Spending a control solve to recover it is refused (rule 29(b));
  §4 replaces it with a stronger, zero-LP instrument.

**No control solve is spent.** L1 and L2 are HEAD's owner-ruled posture and stay armed: rules 1
`[R-STRUCT]` and 14 `[R-ACCURATE]` say a correct construction is not disarmed to make a
differencing convenient.

---

## 2. CARD 0(b) — the near-inertness prediction, in numbers, before the solve

The seam is admissible in all seven NYISO years, but the keeper carries `gas_hub_basis_overlay`
(Transco Z6), and `resolve.py` applies the overlay **after** the seam
(`resolve.py:151` seam → `:166` daily shape → **`:229` `apply_hub_basis_overlay`**), so a measured
constrained-hub index supersedes a state-average delivered cost. **Measured, this session, zero LP:**

| year | hub months covered | hub annual | EP-seam annual | hub − EP annual | max month gap | Jan gap |
|---|---|---|---|---|---|---|
| 2019 | **12 / 12** | 3.052 | 3.012 | +0.040 | 1.082 | +0.169 |
| 2020 | **12 / 12** | 2.101 | 2.135 | −0.034 | 0.473 | −0.433 |
| 2021 | **12 / 12** | 4.413 | 3.879 | +0.533 | 0.977 | +0.554 |
| 2022 | **12 / 12** | 8.427 | 7.050 | +1.377 | 3.644 | +3.644 |
| 2023 | **12 / 12** | 3.368 | 2.936 | +0.432 | 1.330 | −1.330 |
| 2024 | **12 / 12** | 2.789 | 2.683 | +0.106 | 0.774 | +0.686 |
| 2025 | **12 / 12** | 5.558 | 4.378 | +1.180 | **5.107** | +5.107 |

This reproduces FINDING §3's NYISO rows (sign convention there is measured − model) and confirms
its premise exactly: the keeper's series runs **above** the state average in six of seven years —
expected, since downstate NYC gas is dearer than the New York state mean — and, decisively, the
overlay covers **12 of 12 months in every year**, so there is no month for the seam's level to
survive into.

**PRE-REGISTERED (CARD 1):** with `gas_electric_power_monthly_level=true` on the keeper recipe,
**C3b is unchanged to three decimals**, and more strongly the assembled generator gas price is
expected **byte-identical**. A LARGE NYISO MOVE MEANS THE ORDERING IS WRONG — I stop and report,
and do not bank it.

**ADDENDUM A2 census (the second independent reason it may be inert):** the keeper also carries
`gas_plant_monthly_fuel_pricing = True`, so `apply_plant_monthly_fuel_prices` runs after the
overlay and overwrites gas plants with their own F923 prints. The written-cell mask is censused at
zero LP before CARD 1 and reported in the RESULT.

**The screen replaces SHARD F where it can.** Rule 29 clause (0): an arm with a computable
pre-solve gate does not reach a solve until that gate passes. The assembled `fuel_prices` array is
exactly the LP's input, and the `fleet_only` exit returns it — so the ordering check is settled by
an **array comparison, not an LP**. SHARD F is spent only if that comparison is non-identical
(i.e. only if my own prediction fails), which is the case where a dispatch answer is actually
worth buying.

---

## 3. CARD 0(c) — the capacity predictions for 2020 / 2021 / 2022

**The retiree window, censused for NYISO** (`eia860_generator_retired_within_window.parquet`,
`balancing_authority_code == "NYIS"`): 47 rows / 21 plants / 4,153.9 MW net summer in total, of
which the **ADDED** rows — the ones the 2023 → 2019 window move introduces, i.e.
`planned_retirement_year ≤ 2022` — are:

| retirement year | units | plants | net summer MW |
|---|---|---|---|
| 2019 | 13 | 9 | 410.4 |
| 2020 | 3 | 3 | 1,691.3 |
| 2021 | 4 | 2 | 1,043.6 |
| 2022 | 11 | 5 | 526.6 |
| **added total** | **31** | — | **3,671.9** |

which reproduces the handoff's 31 units / 3,671.9 MW exactly. Restored capacity **live in each
solve year** (added rows with `retirement_year ≥ Y`): **2020 +3,261.5 MW · 2021 +1,570.2 MW ·
2022 +526.6 MW** — again exactly the handoff's figures. It is dominated by **nuclear**: Indian
Point 2 (plant 2497, 1,011.5 MW net summer, retired 2020-04) and Indian Point 3 (plant 8907,
1,039.4 MW, retired 2021-04) — 2,050.9 MW of nuclear — plus **1,487.0 MW of coal** (Somerset 676.4,
Dunkirk 520.0, Cayuga 290.6).

**ZERO added rows carry `retirement_year ≥ 2023`**, so the COD monthly online mask is all-`False`
for 2023/2024/2025 and their availability is identically zero. (The 16 NYISO rows that *do* retire
in 2023–2024 were already in the pre-change 477-row artifact and are already in the keeper.)

**PREDICTIONS, registered before the solve:**

1. **Prices FALL in 2020 and 2021**, 2020 the larger (Indian Point 2 present Jan–Apr 2020, and
   3,261.5 MW restored vs 1,570.2 in 2021). 2022 (+526.6 MW, no nuclear) moves modestly.
2. **Nuclear generation UP** in 2020 and 2021; **coal generation UP** in 2020–2022.
3. **Gas CC generation DOWN**, displaced at the margin — this is where the nyiso-209 comparison
   bites (see §5).
4. **2023 / 2024 / 2025: EXACTLY ZERO change** attributable to the retiree window (§4).

---

## 4. CARD 3 / charter task 3 — how in-sample inertness is PROVED, given §1.4

The charter's gate is `max |class-hour delta| = 0.000000 MW` in 2023–2025 against a control that
differs **only** by the artifact. At HEAD there is no flag to toggle and the committed keeper is
not a clean control (§1.4), so a naive keeper-differencing would measure L1 + L2 + the window and
attribute the sum to the window.

**The instrument used instead — stronger, exact, and zero-LP.** The charter's own stated worry is
that *"the ramp deliberately does not touch `pmax`, so the added units still enter `FleetArrays`
… fleet capacity totals, per-class denominators and shares, CAMPD binning and tranche
construction, `_join_egrid_heat_rate`, the plant-group/outage crosswalks, and the LP column
count"* can move at zero availability. **Every one of those objects is a `FleetArrays` array or a
count of one.** So:

> **GATE T3 (pre-registered).** For each of 2023, 2024, 2025: rebuild the fleet on the keeper
> recipe via `run_year(fleet_only=True)` twice at **identical code** — once with the shipped
> 1,094-row artifact, once with the artifact filtered to `planned_retirement_year ≥ 2023` (the
> pre-change 477-row window) — and require **every array on `FleetArrays` to hash identically**
> (`pmax`, `availability`, `min_gen`, `heat_rate`, `unit_ids`, `fuel_type_idx`, the tranche/bin
> arrays, and `n_gen` itself), plus identical `mc_base` and `fuel_prices`.

Array identity is **strictly stronger** than an 8760-hour dispatch comparison: identical LP inputs
force identical dispatch, whereas matching dispatch could coincide. A hash mismatch is a FAIL and
means capacity-denominated code is reading retired units — it is root-caused, not waved through.

The 2023–2025 class-hour delta against the committed keeper is **also** reported, at full
magnitude, as the L1 + L2 drift measurement — labelled as such, and never as the window's effect.

---

## 5. CARD 2 — the touchpoints, and what they supersede

NYISO holds `complete`, so 2020 / 2021 / 2022 are open with `--holdout-authorized`.
**2019 is REFUSED** for every ISO (locked-test tier, `final` empty, freeze ACTIVE) — not attempted
and not designed around.

The H shards **supersede `2026-09-06-nyiso-209-2022-touchpoint`**, which was scored on a fleet
missing Indian Point 3. The RESULT will difference against it and state what the nuclear
restoration did to **C1 CC_REGULAR** (nyiso-209: +4.35 TWh / +3.3 pp) and to **C3a** (−11.2 %).

**Rule 30 `[R-TOUCHPOINT-FOLD]`:** the touchpoints are stamped to the keeper
(`stamp_touchpoint_holdout.py --run-id <tp> --keeper-id 2026-09-07-nyiso-213-summer-seam`), then
`build_status.py --iso NYISO`. **Rule 30(c): a held-out year NEVER downgrades NYISO's
determination** — a degraded rung is reported on the keeper's panel, the status card and the
assessment doc, and NYISO's headline (the 2023–2025 train-tier verdict) is untouched.
Rubric v3.6: on an out-of-training year C3c reads CAVEAT whatever else that year does.

---

## 6. The shard plan (ADDENDUM A1), and rule 16

Years are sequential **within** an invocation, always. Shards are separate child sessions so
rule 12's RAM cap does not bind across them; `source_revision` is passed as the **full 40-char
commit SHA** of the pushed branch tip, never a branch name (A4).

| shard | years | flags | out-dir |
|---|---|---|---|
| **F** | 2023 | `--set gas_electric_power_monthly_level=true` | `results/screen/nyiso_ep_level_2023` — **spent only if the §2 zero-LP array comparison is non-identical** |
| **H1** | 2020 2021 | `--holdout-authorized` | `results/nyiso_fuelvintage_H1` |
| **H2** | 2022 | `--holdout-authorized` | `results/nyiso_fuelvintage_H2` |
| **T1** | 2023 2024 | — | `results/nyiso_fuelvintage_T1` |
| **T2** | 2025 | — | `results/nyiso_fuelvintage_T2` |

All arms: `scripts/replay_keeper.py results/calibration/nyiso213_summer_seam`.

**ADDITION 3 / rule 16 `[R-ALLYEARS]`:** sharding the SOLVE never becomes registering FRAGMENTS.
T1 and T2 are **composed into ONE bundle covering 2023, 2024 and 2025** before registration, the
way ERCOT's keeper composes several configs into one registered run. A 2-year or 1-year fragment
is never registered as a keeper. H1 and H2 compose into the holdout ladder and are stamped per §5.

---

## 7. Governance, restated before any number exists

* **Rule 31 `[R-RETAIN]`** — no solve's results are deleted until the **owner** rules on
  promotion. The bundle families are **gitignored, not removed**; they live on local disk, they do
  **not** survive this ephemeral container, and the promotion question is asked **explicitly** in
  the final report.
* **Rule 29 `[R-SCREEN]` (c)** — a screen bundle is kept OUT of `main` by `.gitignore`, which
  discharges the duty in full. `rm -rf` is not the instrument (the ercot-255 incident).
* **Rule 15 `[R-DASHBOARD]`** — every completed run is registered in this session, keeper or
  rejected probe.
* **Rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`** — these land because they are **correct**. A worse
  fit is a root-cause investigation, never a revert. Every criterion is reported at full
  magnitude, and no gate is set on the target residual.
* **Rule 28 `[R-MECH-MATRIX]`** — only `docs/codebase-site/data/mechanism-matrix/NYISO.js` is
  edited, cell `gas_electric_power_monthly_level` (currently `O`).
* **Charter task 4** — retiring the `NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO']` caveat text in
  `constants.py` is NYISO's lane's work and is done in this session.
* **No pull request** is opened unless the owner asks for one.

**I will not restate any threshold in §2, §3 or §4 after seeing a number.**
