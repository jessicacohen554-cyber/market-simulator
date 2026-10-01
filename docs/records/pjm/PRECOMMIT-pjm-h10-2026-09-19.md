# PRECOMMIT — pjm-h10, the PJM ENERGY IDENTITY lane (2026-09-19)

**Session:** pjm-h10 (next free id; latest logged PJM session is pjm-h9 / pjm-h9b, 2026-09-16).
**Branch:** `claude/pjm-energy-identity-s4l8ow` · **Base:** `origin/main` @ `4583e70b864a7d5c99a206b06eddf3c36af495bf`
**Role:** ORCHESTRATOR. Rule 32 `[R-SHARD]` (a): **this session runs no LP.** Every solve is a shard.
**Keeper (unchanged by this session):** `2026-09-11-pjm-d4-4-gasoutage`, bundle `results/calibration/pjm_d4_4_A`,
years 2023–2025, CALIBRATED 8/8, zero caveats, `git_sha f09eddbefe6a3e72ba3ccc2f9d4d97db0b17205d`.
**Touchpoint:** `2026-09-11-pjm-holdout-gasoutage-touchpoint`, bundle `results/calibration/pjm_d4_4_TP`,
years 2020–2022, NOT-YET (C1/C2/C3a-b FAIL, C3c CAVEAT).

This document is written **before either shard lands**, so its predictions cannot be fitted to a result.

---

## 1. Shards launched (rule 32 `[R-SHARD]`, rule 34 `[R-SHARD-PROMOTABLE]`)

Both pinned to the full 40-char SHA `4583e70b864a7d5c99a206b06eddf3c36af495bf`, which
**contains** `2ec096633f5624585eb9db1728ebc7c8ca5ccbdf` (the marginal-emission-rate merge) —
verified with `git merge-base --is-ancestor`, which returned true.

| shard | session | years | source bundle | out-dir | branch | budget |
|---|---|---|---|---|---|---|
| A | `session_01GVm2g4rPYhEHZT6kRmiB3S` | 2023–2025 | `pjm_d4_4_A` | `results/calibration/pjm_h10_mer_A` | `claude/pjm-h10-mer-a` | 120 min |
| TP | `session_01WiG8kSC7zZRG9R6xb85HJp` | 2020–2022 | `pjm_d4_4_TP` | `results/calibration/pjm_h10_mer_TP` | `claude/pjm-h10-mer-tp` | 120 min |

One span per shard, one `replay_keeper.py` invocation each, years sequential inside it
(rule 12 `[R-PARALLEL]`; per-year fan-out is banned — rule 32(b)). Both are told to push
their bundle to their own branch by `.gitignore` negation + a **plain** `git add`
(rule 34(a); never `git add -f`), including `dispatch/<year>_P1.parquet`, and both are
forbidden `git add -A`/`git add .`, the dashboard scripts, `frontend/data/backcast/**`,
any edit under `src/` or `scripts/`, opening a PR, and deleting any result.

They serve three purposes: the marginal-emission-rate series PJM owes the
marginal-abatement page; the **empirical check on the G-DRIFT verdict below**; and the
first per-plant memory measurement of the emissions dual. Memory is genuinely
unvalidated at this scale — an OOM kill inside HiGHS `run()` is not catchable by the
try/except guarding the dual, and both prompts say an OOM is a **reportable finding
about the dual**, not a model regression.

---

## 2. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — **form 4 is FALSIFIED. The keeper's committed
numbers are NOT a valid control at this HEAD.**

`git diff f09eddbe HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`

**81 code files, 9,125 insertions, 264 deletions**, over the eight days 2026-09-11 → 2026-09-19,
plus 23 changed/added files under the two `data/raw` trees. 56 of the 81 code files are
**pure additions**; 25 carry deletions and are where existing behaviour could move.

Unlike pjm-162's, **this keeper's baseline sha resolves** — `git fetch origin f09eddbe…`
returned it. pjm-167's "PJM's G-DRIFT baseline is UNRECOVERABLE" was about the *previous*
keeper (`457ae04`, pre-rewrite); it does not apply here and this audit is dischargeable.

### 2.1 LIVE hunks (four, three of them on the solve path)

**L1 — `data/raw/_validation-source/pjm_offer_midcurve_condbinned.json` was REBUILT.
This is the keeper's own live offer input and it is the largest drift item.**
The keeper runs `pjm_offer_midcurve_conditional = True` with
`pjm_offer_midcurve_path = None` (so the default filename resolves to exactly this
artifact) and `pjm_offer_midcurve_segments = ['LONG_RUN', 'CC_LIKE']`.
The artifact went 24,444 → 42,326 bytes: `_provenance.source` moved from delivery years
`[2023, 2024, 2025]` to `[2020, 2021, 2022, 2023, 2024, 2025]`, `n_month_files_parsed`
36 → 72, and the segment unit counts grew (LONG_RUN 216 → 477, CC_LIKE 883 → 1603,
CT_FAST 1064 → 2455). That is the ≤2022 extension, lane pjm-h9b.

`offer_surfaces.py` selects `entry["years"][str(year)] or entry["pooled"]`, so the reach
splits cleanly by span. Measured per-rung over the keeper's two named segments
(48 rungs each = 4 conditioning bins × 12 share points):

| segment | table | rungs moved | max &#124;Δ&#124; $/MWh | mean Δ | mean &#124;Δ&#124; |
|---|---|---|---|---|---|
| LONG_RUN | 2023 | 10 / 48 | 0.050 | +0.0000 | 0.0104 |
| LONG_RUN | 2024 | 14 / 48 | 0.100 | +0.0021 | 0.0187 |
| LONG_RUN | 2025 | **0 / 48** | 0.000 | 0.0000 | 0.0000 |
| LONG_RUN | pooled | 48 / 48 | 0.750 | −0.5198 | 0.5198 |
| CC_LIKE | 2023 | 5 / 48 | 0.050 | −0.0010 | 0.0052 |
| CC_LIKE | 2024 | 27 / 48 | 0.150 | +0.0125 | 0.0333 |
| CC_LIKE | 2025 | **0 / 48** | 0.000 | 0.0000 | 0.0000 |
| CC_LIKE | pooled | 45 / 48 | 4.350 | −0.3979 | 0.6583 |

`CT_FAST` moved much more (pooled mean −7.75 $/MWh) but the keeper does **not** name it,
so `segments` filters it out before the table is loaded — it cannot reach this run.

**L2 — `data/cod_ramp.py` + `data/fleet/arrays.py`: the SOCO-15 / owner-card-S12
COD-grain change.** `cod_ramp_enabled = True`, `plant_level_fleet = True` and
`use_campd_bins = True` in the keeper, so every PJM LP unit is a plant-level CAMPD bin —
precisely the grain the card changed. Two mechanisms move together: `effective_cod` gained
an `is_plant_level` argument and a new `generator_online_mask` resolver replaced the old
`effective_cod` + `monthly_online_mask` pair, so a plant-level bin whose
`(plant_code, fuel)` constituents are in the new `load_unit_cod_map` now takes a
**fractional** monthly online-capacity mask (`bin_online_fraction`) where it previously
took a 0/1 plant-collapsed mask; and `load_cod_map`'s own reduction changed from
"the plant's earliest unit defines its online date" to the capacity-weighted mean.

**L3 — `config/plant_taxonomy.py`: prime mover `PS` is now tested BEFORE hydro**, so
pumped storage classifies `OTHER` instead of `HYDRO` (every PS row also carries fuel code
`WAT`). PJM has pumped storage. This is the merged `gov-hydro-seam-1` repair the lane
charter names, and it is live on both the fleet and the scoring side.

**L4 — `model/lp/model.py`: the marginal-emission-rate dual itself.** After the priced
solve, `_marginal_emission_rate` freezes the cost-optimal basis, swaps the objective to
the per-generator CO2 rate vector and re-prices with the simplex iteration limit at zero.
`objective_value` and `status` are now captured *before* that swap, which is the right
guard, but the HiGHS instance is mutated after the solve that produced the prices, so
this is LIVE by construction and the replay is its first per-plant test. The same commit
also releases `_all_cols` across the solve peak and rebuilds it lazily — a memory change,
result-neutral by construction.

### 2.2 INERT, with the reason cited for each

* **56 pure-add files** — no existing call site changed.
* **NWPP and SOCO registration** (`iso_configs.py` +434, `config/capacity_market.py`,
  `fuel_trajectories.py`, `scripts/lib/{confirmed_retirements,load_forecast,nuclear_license_status,transmission_expansion}/{nwpp,soco}.py`,
  `data/eia930/demand.py`'s two new loaders, the `NWPP_*`/`SOCO_*` renewable-capacity CSVs
  and `soco_seam_*` reference tables) — other regions. `iso_configs.py`'s only
  PJM-containing added lines are two comments. `data/eia930/demand.py`'s +131 adds
  `_load_nwpp_hourly_demand` / `_load_soco_hourly_demand` / `_nwpp_demand_source` /
  `_soco_demand_source` and nothing else; PJM's demand path is untouched.
* **`ISO_TO_BA_CODE` → `ba_codes(iso)` pool refactor** (`fleet/models.py`,
  `fleet/campd_bins.py`, `hydro.py`) — `ba_codes('PJM') == ('PJM',)`, and a one-element
  `.isin(...)` selects exactly the rows `== 'PJM'` did. Pure for a 1:1 region.
* **SPP-38 vintage-keyed caches** (`campd_bins.py`'s four `cc_*`/`coal_summer_capacity`
  shims, `outages.py`'s `_iso_plant_unit_capacity` and `_fleet_status_index` shims) —
  the key only bites when the active EIA-860 directory moves within a span, and the
  keeper has `eia860_vintage_tracks_solve_year = False` with `eia860_vintage_year = None`.
* **`unit_outage_csv_for_iso`'s new `hour_grain` argument** — `arrays.py` gates it on
  `campd_per_unit_attribution AND unit_outage_window_hour_grain`; the keeper has the
  first `False` and the second defaults `False`.
* **`offer_surfaces.py`'s `pjm_offer_midcurve_minload_segments`** (pjm-h8) — a new
  default-off gate absent from the keeper's recipe; `minload_targeted` is identically
  `False` with an empty scope, so `is_target` and the LEVEL-form branch are unchanged.
* **`renewables.py` ISO gates** — `_UNCURTAILED_FALLBACK_ISOS` added only NWPP and SOCO;
  `_SOLAR_ZONE_REANALYSIS_ISOS == {'SOCO'}`, `_SOLAR_ZONE_SHAPE_ISOS == {'CAISO'}`,
  `_WIND_ZONE_SHAPE_ISOS == {'MISO','SPP'}`. PJM is in none of them.
* **`zone_assignment.py` +285** — the EIA-860 plant-file supplement is gated on
  `_EIA860_SUPPLEMENT_ISOS == {CAISO, ERCOT, MISO, NEISO, NWPP, NYISO, SOCO, SPP}`.
  **PJM is not a member.**
* **`data/eia930/actuals.py` + `frames.py`: the fuel-spike screen moved from three
  per-reader call sites to the frame constructors** (NWPP-37). That lane's own census,
  quoted in the docstring, is a proof rather than a sample: *"ERCOT, CAISO, **PJM**, MISO
  and NEISO carry no flagged hour in any column in any year."* Nothing for PJM to repair,
  so no consumer can move. The NWPP-39 zero-baseline guard can only *release* a series.
* **`model/interchange/neiso.py`** — the cold-snap dual-fuel exemption is NEISO's, and
  its new limb is empty unless `dual_switch_active is not None`.
* **`model/lp/hydro_cascade.py` + `hydro.py`'s cascade plumbing** — gated, and PJM
  carries no cascade spec.
* **`run_calibration_full.py`'s `gas_offer_margin_anchor_vintage` mirror block** — moved,
  and the keeper has that flag `False`.
* **`solve_surface.py`** — `SURFACE_ISOS` gained SOCO appended last and no surface name
  carries a SOCO token, so PJM's projection is unchanged by construction (rule-D79 key).
* **`data/raw/reference/reliability_floor_coeffs_NYISO.csv`** — NYISO's.
* **`data/raw/_validation-source/actual_lmp_hourly*_{MISO,SPP}.parquet`** — other ISOs'.
* **`data/raw/_validation-source/calibration_reference.json`** — checked leaf-by-leaf:
  **319 PJM leaf keys, 0 changed.** PJM's scoring reference is stable, so a metrics move
  in the replays cannot be a benchmark artifact on this channel.

### 2.3 What the audit therefore says

A LIVE hunk is the one thing that earns a control solve, and there are four.
**Form 4 is void for PJM at this HEAD**, and the two replays already launched *are* that
control. This is not a "files changed, therefore void" heuristic: each LIVE item is named,
its gate is checked against the keeper's own recipe, and L1 is quantified to the rung.

---

## 3. EX-ANTE PREDICTION — recorded before either shard reports

Stated so it can be wrong. **A metrics difference in these replays is EXPECTED and is not
a regression**, and neither replay may re-register or overwrite the keeper bundle
(a replay that reproduces a keeper is not a new run; a replay that does not is a control,
not a candidate).

* **Shard A (2023–2025).** Scored numbers move, but **slightly**. 2025's offer channel is
  byte-identical (0/48 rungs on both named segments); 2023 and 2024 move on 10–27 of 48
  rungs by at most 0.05–0.15 $/MWh. L2 and L3 act in all three years and are the larger
  unknown. Expect C1/C2 volumes and C3a/C3b price levels to move in the third decimal to
  low-tenths, not across a gate. **If a gate flips, L2 or L3 is the cause, not L1.**
* **Shard TP (2020–2022).** Moves **materially**. Before, none of 2020/2021/2022 had an
  own-year midcurve table, so all three fell through to `pooled`; at HEAD each has its
  own. The pooled table itself also moved (LONG_RUN mean −0.52, CC_LIKE up to 4.35 $/MWh),
  so both the table *and* the selection changed. The touchpoint's already-failing
  C1/C2/C3a-b are the numbers most likely to move, in either direction.
* **The MER series itself.** `marginal_emission_rate` present and non-degenerate in all
  six `hourly/system_<year>.parquet` files. A non-trivial share of zone-hours at exactly
  0.0 is expected wherever the marginal re-dispatch is carbon-free, and is not a defect —
  the shards report that share so it can be judged rather than assumed.
* **Memory.** PJM per-plant against a 13.34 GiB binding cgroup with an 8–24 GiB swapfile
  the runner provisions itself. If either shard is OOM-killed, the finding is about the
  dual's basis refactorization, and no other lane should arm a per-plant MER run until
  it is written up.

---

## 4. Levers pre-registered this session

**None.** No `ScenarioConfig` field is added, no default is flipped, no mechanism-matrix
cell moves on the strength of a solve this session ordered. The session's deliverable is
a reconciliation (the EIA-923 → EIA-930 → model bridge for PJM), the attribution of the
~9–10 TWh interchange under-export, the disposal of the virtual-bid net, and a
**governance proposal** on the rubric's total-energy blind spot that goes to the owner
undecided (rule 1 `[R-STRUCT]`). Any lever that follows is a later session's, with its
own pre-registered gate.

## 5. Standing constraints this session operates under

* Rule 31 `[R-RETAIN]`: nothing is deleted. The promotion question is asked explicitly in
  the final report, and every bundle's location is named.
* Rule 33 `[R-SHARD-ARCHIVE]`: fetch → check out → verify (config signature, and
  `git ls-tree -r <sha> -- <bundle path>` returning more than zero files, rule 34(d))
  **before** archiving any shard; recovery recorded by full immutable SHA, never a branch
  name.
* Rule 15 `[R-DASHBOARD]`: nothing is registered unless it is a run, and a control replay
  of an existing keeper is not one.
* Binding priors not re-litigated (rule 28 `[R-MECH-MATRIX]` (a)): the 2022 miss is the
  18-hour Elliott scarcity tail with no admissible price lever
  (`docs/FINDING-pjm-h3b-2022-miss-is-the-elliott-tail-2026-09-13.md`), and the Dominion
  CT zonal-congestion route is closed by measurement at pjm-137.
