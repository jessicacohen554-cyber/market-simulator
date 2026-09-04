# PRECOMMIT caiso-243 — ADDENDUM: an INSTRUMENT DEFECT in the lane's zero-LP probe pattern, found after the arm was coded and BEFORE any solve output was read; the footprint and the envelope re-measured ON-RECIPE

**Session caiso-243, 2026-09-04. Pushed while the B1 solve is in year 2023, with
no bundle file read.** Parent: `PRECOMMIT-caiso243-f923-fallback-guard-2026-09-04.md`.

## §A — What was found, and how

The live replay's log for 2023 read *"hub-basis overlay (CAISO 2023, **daily**):
**1443** gas generators … (winter max 24.75)"* while every probe rebuild this
session — and the keeper log caiso-242 §5.1 quoted — read *"… (CAISO 2023,
**monthly**): **1401** gas generators … (winter max 28.08)"*. The keeper's
committed `run_config.json` carries `caiso_citygate_spot_level: True`. **The
replay is the keeper's recipe; the probes were not.**

**Root cause — the probe pattern, not the model.** Every `run_year(fleet_only=True)`
probe in this lane since caiso-202 (`_caiso202_marginal_rung`, `_caiso216`,
`_caiso221`, `_caiso230`, `_caiso239`, `_caiso240` ×2, `_caiso241` ×2,
`_caiso242` ×4, and this session's three) reconstructs the recipe as
`{k: v for k, v in meta.items() if k in run_year params}`, which **silently drops
every meta key whose solve kwarg is spelled differently** — above all
`coal_prb_sigmoid_overrides` → `prb_overrides`, the bag that on the CAISO keeper
carries **36 structural flags**: `caiso_citygate_spot_level`,
`capacity_deliverability_limits`, `caiso_scarcity_pricing` /
`scarcity_pricing_enabled`, the RA-bridge startup flags, the hydro envelope /
ROR / min-flow flags, `measured_ct_heat_rates` / `measured_chp_heat_rates`,
`use_plant_emission_rates_v2`, the WEFOR flags, the firm-import and DSW flags,
`caiso_zonal_loss_surface`, `caiso_supply_consistent_demand`, … The sanctioned
reconstruction, `scripts/replay_keeper.py::build_kwargs` (strict, remapping), was
never used by a probe. The three keys `build_kwargs` yields that `run_year` does
not take (`commitment`, `screen_coal`, `strict_demand_profile`) sit at the
keeper's values = `run_year`'s defaults (False / True / False), so the corrected
reconstruction is exact.

**Consequence, stated at full size:** every zero-LP number the CAISO lane has
published from that pattern since caiso-202 was measured on a lookalike recipe —
in particular the keeper priced gas at the **daily spot level** (caiso-84), not
the monthly N3050CA3 survey the probes rebuilt, so **caiso-242 §3's gas-basis
identity ratios (1.298 / 1.310 / 1.327) were measured against the wrong model
series and need re-measurement by their own lane** (they are NOT re-adjudicated
here). Each probe's *own* byte-identity claims (probe vs probe) stand; their
*keeper-relative* claims do not, until re-run. Filed as an owner ask (§D).

## §B — Repaired and re-measured (this session's three probes, cache `c243v2`)

`keeper_recipe_kwargs()` now builds the recipe through `build_kwargs`. Log
cross-check against the live solve: *"F923 fuel costs for 2023: 81 own, 1376
gap-filled"* and *"(CAISO 2023, daily): 1443 …"* — **identical lines** from the
corrected rebuild and from the replay.

| quantity | off-recipe (§2 of the precommit) | **ON-RECIPE** |
|---|---|---|
| `state` empty, gas rows (2025) | 1,411 / 1,411 (29,319 MW) | **1,453 / 1,453 (29,278 MW)** |
| hub overlay 2025 | monthly, 9/12 | **daily (spot level), 9/12 — Sep/Oct/Nov open, as the spot-level docstring states** |
| (a) footprint | 225 rows / 4,649.3 MW | **228 rows / 4,639.4 MW** |
| (c) footprint | 1,322 rows / 25,568.3 MW | **1,364 rows / 25,526.9 MW** |
| (a)+(c) vs (c) | byte-identical | **byte-identical** |
| (b) 2 % cut | 0 rows | **0 rows** (still misses 55077-Nov) |
| Nov-2025 cap-wt, (c) | 13.47 → 4.38 | **13.48 → 4.38 $/MMBtu** (fuel mc 119.1 → 42.5 $/MWh) |
| SP15_rest pool-of-one MW | 2,446 | **2,445.1** (same six plants; 55077 own 370.1 unchanged) |
| 2023 / 2024 footprint | 0 / 0 | **0 / 0** |
| G-STRUCT (coded vs measured, 5 cases) | PASS | **PASS, byte-identical, on-recipe** |
| **envelope 2025, (a)+(c)** | [−2.634, +0.311] | **[−2.501, +0.311]** |

**The object, its form, its inertness in 2023/2024 and every gate survive the
correction unchanged; the numbers move at the second digit.**

## §C — What changes in the registration, and what does not

* **G-C3a envelope leg (§5.6) is re-registered at the ON-RECIPE value:
  ΔC3a-2025 ∈ [−2.501, +0.311] $/MWh**, 2023 / 2024 exactly 0. Tightening the
  bound before reading the solve is the honest direction; the off-recipe
  figure is kept above for the record.
* P-1 … P-8 are unchanged in wording; P-8's reference arrays are the on-recipe
  caches (`_caiso243_gstruct_presolve.json` is the on-recipe run).
* The promotion rule (§5.7) is unchanged.

## §D — Owner asks added

1. **Re-run caiso-242's four probes on-recipe** (one command each after the
   `build_kwargs` fix) before any session cites its §3 ratios again; its §5
   defect (D1/D2/D3) is CONFIRMED on-recipe here and needs nothing.
2. **Retire the pattern**: a shared `scripts/lib` helper (or `replay_keeper`
   export) for fleet-only rebuilds, so no future probe reconstructs a recipe
   by parameter name.
