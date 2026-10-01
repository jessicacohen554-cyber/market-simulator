# RESULT caiso-292 — the fleet-rebuild defect is ONE missing argument, and the belly split holds on the live keeper

**Lane:** caiso-292 · **Date:** 2026-09-20 · **LP spent: ZERO** (rule 32 `[R-SHARD]` (a) — the
parent never solves; no shard was launched, because both objects are arithmetic over committed
artifacts). **Nothing armed, nothing disarmed, no `ScenarioConfig` field added, no constant moved,
no derive re-run, no run registered, keeper untouched.**

Keeper on `main`: **`2026-09-20-caiso-290-leftedge`** (bundle `xiso8_leftedge_span`), one
registered CAISO run, `audit_keepers` clean. The lane instruction's §1 is accurate as of this
session (caiso-291's §5.1 objection described `main` before the xiso-8 promotion landed).

---

## 0. The answer in two paragraphs

**Object 1 — the rebuild.** `legitimacy_diagnostics._rebuild_fleet_arrays` built **1,905 rows where
the solve had 1,705**, and the cause is **one missing argument**, not 28 lost `ScenarioConfig`
fields. The rebuilt *config* round-trips essentially perfectly; what `meta.json` cannot carry is
what `solve_and_persist` **derives from its own locals**, and `replay_keeper` has named that gap
`DERIVED_RUN_YEAR_INPUTS` since **caiso-248**, told every caller *"every fleet-only rebuild should
splat this"*, and `scripts/lib/bundle_fleet.reconstruct_bundle_fleet` discharges it for the probe
lane. The scorer did not. With the splat the rebuild reproduces the solve fleet **unit-for-unit in
order, `pmax` exact to 0.000000000 MW**. Shipped in commit `e255252e`. The owner gate — *"a repair
re-scores D-1/D-2/D-4 for every ISO and a gate can flip"* — measures at **0 differing leaves of
1,189** on CAISO, and the invariance is mechanical: the 200 phantom rows carry **min_gen sum
0.000000 MWh**.

**Object 2 — the belly split.** It was **not open**. caiso-287 answered it unanimously on all four
years; what is open is the *admissibility* of `caiso_ra_bridge_startup_aware`, which stays in owner
court. The live question was whether caiso-287's verdict **survives the keeper change**, since the
keeper's own arm moves `mc_base`, an input to both screens. Re-measured at zero LP on the keeper's
committed P0: **(A) GAP-MERGING DOMINANT, unanimous, with the margin wider** — the decommit screen
removes **1.2–2.6** mean-belly-MW while the `startup_aware` run screen removes **91–584**. Two
numbers on the record are corrected along the way.

---

## 1. Object 1 — what the rebuild defect actually is

### 1.1 The measurement, on a self-consistent bundle

caiso-291 compared the **keeper's** meta-only rebuild against **caiso-285's** committed floors —
two different recipes, so recipe differences and rebuild defects were mixed. The clean test is a
bundle rebuilt from its **own** `meta.json` against its **own** committed floors.
`caiso285_instr_2024` (recovered from `203124e310f7be4f806ad968d6cf5755f96bbc00`) carries
`meta.json`, `run_config.json` **and** `floors/2024_P1.npz`, so it is that test.

| | rows |
|---|--:|
| solve (`floors/2024_P1.npz`, and the keeper's own committed `hourly/p0_dispatch_2024.parquet`) | **1,705** |
| rebuild, `meta.json` only | **1,905** |
| rebuild, `meta.json` + `derived_run_year_inputs` | **1,705** |

`only_real = 0` in both bundles: the rebuild never **lost** a unit. It is a strict **superset** of
exactly **200 rows**, every one a raw per-unit id (`10026_EG10`, `10091_GEN1`, `…_UNT1`, `…_COGEN`)
totalling **874.300 MW** of `pmax`.

### 1.2 It is not the 28 fields

Diffing the rebuilt `ScenarioConfig` field-by-field against `run_config.json`'s committed
`scenario_config` on the same bundle returns **11 differing fields of 851 — every one absent from
the recipe** (`gas_flow_date_year_start_package`, `measured_coal_heat_rates`, … : fields added to
`ScenarioConfig` after that bundle was written, rebuilt at their defaults). None of the 7
"fleet-shaping losses" caiso-291 named — `chp_steam_floor_p25`, `caiso_ps_plant_params`,
`hydro_min_flow_floor` and the rest — is lost on this bundle, and the extra rows are **biomass**,
not CHP or pumped storage. The `meta.json` → `run_config.json` recipe gap is a real thing, but it
is **not** what moved the row count, which is also why caiso-291's "re-apply the committed recipe"
attempt made it *worse* (1,905): it was treating the wrong cause.

### 1.3 The actual cause, and why it can never be fixed by reading `meta.json` harder

`run_calibration_full.py` computes `inject_biomass = "biomass" in must_run` from the year's
injected residual must-run classes and passes it to `run_year`, which forwards it as
`drop_biomass_units` — **removing the raw biomass LP units**, because the same energy is injected
as a measured EIA-923 must-run profile and would otherwise be served twice. It is a **derived
local**, so it appears in no kwarg record; `_rebuild_fleet_arrays`'s loop over `meta.items()` could
map every key perfectly and still never reach it.

`scripts/replay_keeper.py` already solves exactly this, and says so at the constant:

> `DERIVED_RUN_YEAR_INPUTS: tuple[str, ...] = ("inject_biomass_mustrun",)` — *"A rebuild that omits
> it carries phantom biomass units the scored solve never had (caiso-248; it invalidated
> caiso-247's DOM_OTHER attribution)."* … *"Every fleet-only rebuild should splat this into
> `run_year`."*

`derived_run_year_inputs` recovers it from the bundle's own committed
`hourly/class_hourly_<year>.parquet` by the injected class's **monthly-step shape**. ~30 probes do
this; `bundle_fleet.reconstruct_bundle_fleet` does it. **The scorer — the rebuild rule 19
`[R-FORCED-BUDGET]`'s "keepers re-score in place" promise runs through — did not.** The repair is
that splat, applied after the mapped kwargs so the solve-side value always wins.

**It reaches existing keepers with no re-solve**: every one of the **12** registered bundles carries
`class_hourly_<year>.parquet` for **every year it covers**.

### 1.4 The repair verified

| bundle | truth artifact | rebuilt | identical in order | max \|Δ pmax\| |
|---|---|--:|---|--:|
| `caiso285_instr_2024` | `floors/2024_P1.npz` | 1,705 | **yes** | **0.000000000 MW** |
| `xiso8_leftedge_span` 2024 | `hourly/p0_dispatch_2024.parquet` | 1,705 | **yes** | — |

`plant_group` and `plant_code` identical; on the second bundle the `pmax × availability` envelope
now admits the solve's own P0 with **0 violating cells** (§2.4).

### 1.5 The owner gate, measured

Regenerating the keeper's `legitimacy_diagnostics.json` for **2022–2025** with and without the
splat: **0 differing leaves of 1,189.** Gate verdicts identical (D-1 FAIL, D-2 PASS, D-4 FAIL, D-5
FAIL, D-9 PASS, D-10 PASS — the same set caiso-291 recorded as pre-existing).

The invariance is **mechanical, not luck**. On the same year, the 200 phantom rows carry
**`min_gen` sum 0.000000 MWh** and **zero** non-zero mechanism cells, and every shared row's
`min_gen` / `mechanism` / `pmax` is **bit-identical**. D-2 and D-4 score *floored* energy, so they
cannot move; D-1 reads dispatch. **No gate can flip through this path** unless an ISO has a biomass
unit carrying a floor. Only CAISO is measurable today under keeper-only retention — the same limit
caiso-291 stated honestly.

### 1.6 What is NOT repaired, named rather than absorbed

1. **`scripts/data/derive_pjm_ordc_overlay.py`, `derive_ordc_overlay.py`,
   `derive_nyiso_rcpf_overlay.py`** each call `run_year(fleet_only=True)` without the splat. They
   are **derive scripts**, and rule 23 `[R-FROZEN-DERIVE]` says a re-derivation must cite a
   **source-data** change. Repairing them would move measured parameters on no data change, so it
   is left as a named object.
2. **`scripts/probes/caiso291_bridge_candidacy_census.py`** carries its own private copy of the
   meta-only rebuild. Its census is what §2.5 corrects.
3. **THE BIGGER DEFECT THIS LANE FOUND AND DID NOT FIX.** A keeper does **not** re-score in place
   today, and the fleet rebuild is not why. Regenerating the keeper's diagnostics from its
   **committed** bundle differs from the committed artifact in **697 of 1,396 leaves**, because the
   committed run was scored on `dispatch/<y>_P1.parquet` and the regeneration falls back to
   `dispatch_source = "run payload …"`, losing rows (**D-2 24 → 20, D-4 52 → 37**). **10 of the 12
   registered keeper bundles commit no `floors/` and none commits `dispatch/`** (SPP's two are the
   exception, which commit floors). That is a bundle-retention question under rules 15 / 34, it
   costs a re-solve or a bytes-landing decision, and it is **the owner's call** — stated here rather
   than absorbed.

---

## 2. Object 2 — the split, re-measured on the live keeper

### 2.1 The correction that defines the object

The lane instruction carries caiso-286's open 270.279 mean-belly-MW as *"OPEN"*. **It is not.**
`RESULT-caiso287-startup-decommit-split-2026-09-19.md` §2 split it, unanimously, on all four years:
**(A) GAP-MERGING DOMINANT**, decommit exonerated. What caiso-287 left standing (§5) is the
**admissibility** of `caiso_ra_bridge_startup_aware` — its anchor test prices runs off the model's
own P0 duals, the circularity `scenarios.py:12824` refused for ERCOT — and that is a rules-1/13
question in owner court which this lane **does not decide**.

The live question is different and real: caiso-287 measured on the **caiso-275-era** bundles, and
the current keeper's defining arm `gas_flow_date_year_start_package` **moves `mc_base`**, which
feeds **both** screens (the run-anchor margin, `commitment.py:1066`; the gap hold cost, `:1229`).
So the verdict is not inheritable.

### 2.2 The result

`scripts/probes/caiso292_screen_split_keeper.py` **imports** caiso-287's own `run_detector`,
`belly_mean_mw`, sidecar readers, posture map and cuts — the arithmetic is reproduced, not
re-implemented — and supplies the keeper's bundle. Artifact:
`results/calibration/_caiso292_screen_split.json`.

| year | M_both | M_none | **R_SA** (startup_aware) | **R_DC** (decommit) | bar @70 % | verdict |
|---|--:|--:|--:|--:|--:|---|
| 2022 | 991.816 | 1113.810 | **91.101** | **2.591** | 85.395 | (A) GAP-MERGING DOMINANT |
| 2023 | 816.431 | 1207.582 | **298.998** | **2.285** | 273.806 | (A) GAP-MERGING DOMINANT |
| 2024 | 671.486 | 1218.437 | **427.197** | **1.157** | 382.866 | (A) GAP-MERGING DOMINANT |
| 2025 | 781.745 | 1492.728 | **583.567** | **2.283** | 497.688 | (A) GAP-MERGING DOMINANT |

mean-belly-MW. **Unanimous, and not close in any year**: the surplus decommit screen removes
1–3 MW where the run screen removes 91–584. The keeper's own 2024 belly hashes to
`c5948fb0d43620a1` — **caiso-285's frozen set**, so the 2024 column is directly comparable with
caiso-287's, and it barely moved (M_both 670.470 → 671.486; R_SA 430.444 → 427.197; R_DC 1.157 →
1.157). The 2022–2023 columns moved much more, which is where the gas repairs of §2.3 land.

### 2.3 G-V, corrected in the open

The PRECOMMIT wrote **G-V** as *reproduce caiso-287's published artifact within 0.05 MW*. That form
**conflates two questions** — *is my harness caiso-287's arithmetic* (a property of this probe) and
*has the solve path moved since caiso-287* (a G-DRIFT question rule 29 `[R-SCREEN]` (b) answers at
**code** level, never by differencing numbers). It failed, at 25.42 MW. Both forms are reported
rather than the convenient one — the handling caiso-287 itself gave its own mis-specified G-R2
(a float64 gate over a float32 store):

* **G-V1, the gate — PASS at `0.000e+00` MW.** This probe equals caiso-287's **own probe run at the
  same HEAD** on `caiso287_instr_2022`, on all four metrics and the belly sha.
* **G-V2, reported — SUPERSEDED.** HEAD is 25.4163 mean-belly-MW from caiso-287's published 2022,
  and the code audit puts that inside the **keeper's own lineage**, not in drift:
  **`35adf93c`** (caiso-288 recovered **85 published CA-composite citygate prints** the scraper had
  dropped — a rule 14 `[R-ACCURATE]` input improvement that moves CAISO `mc_base` in every year)
  and **`75e57fd9`** (caiso-289 separated the year-start left-edge channel; **measured here** on
  caiso-287's own 2022 bundle at **−11.960 mean-belly-MW**). caiso-287's G-R2 correspondingly FAILs
  at HEAD, which is evidence **of** the supersession rather than of a harness defect.
* **The interval that matters is clean.** Between the keeper's own solve (`e7091f56`) and HEAD,
  every solve-path hunk is **INERT for CAISO**: SPP-66's `commitment_floor_window_netload` (a
  default-off gate whose OFF branch `arrays.py` states, and the diff shows, evaluates the identical
  expression as before), soco-55's `gas_basis_differential_measured_by_year` (table carries one
  entry, `{"SOCO": …}`), nwpp-44's take-or-pay (`iso in ("MISO","NWPP")`), nyiso-245/246.

### 2.4 G-A — a new check worth keeping

If the rebuilt fleet **is** the solve's fleet, the solve's own P0 dispatch must fit inside
`pmax × availability`, because that product is the LP's upper bound. Measured on the keeper, all
four years: **0 violating cells, worst excess 2.3e-13 MW.**

### 2.5 G-D FAILS — and the miss is diagnosed, not smoothed

The PRECOMMIT declared the detector's `screen_stats` drop rate must reproduce caiso-291's published
census to ±0.1 pp. It does not, in any year.

| year | runs **detected** (both) | caiso-291 kept | this lane kept | caiso-291 drop % | **this lane drop %** |
|---|--:|--:|--:|--:|--:|
| 2022 | 24,006 | 8,426 | 11,866 | 64.90 | **50.57** |
| 2023 | 19,088 | 4,522 | 8,317 | 76.31 | **56.43** |
| 2024 | 22,455 | 2,462 | 6,480 | 89.04 | **71.14** |
| 2025 | 18,760 | 1,320 | 5,261 | 92.96 | **71.96** |

`runs_detected` — which reads only `pmax` and the committed P0 — is **identical in every year**, so
the divergence is **entirely in `runs_kept`**, i.e. in the anchor test, whose only rebuilt input is
**`base_mc`**. caiso-291's census ran on its own meta-only rebuild (its artifact records
`join.fleet_rows` **1859** against the solve's **1705**) and flagged **646,108** `p0 > pmax ×
availability` cells which its FINDING recorded as *"observed and not yet attributed"*. **§2.4
attributes them**: on the sanctioned rebuild the count is **zero**. So caiso-291's drop rates are
**superseded, not contradicted** — they were measured on a fleet that is not the keeper's.

**This matters to the owner decision the lane instruction routes.** The corrected rates still rise
monotonically 2022 → 2025, but they land much closer to caiso-287 §5's **42–60 %** band than to
93 %. The evidence for the admissibility question should be quoted as **50.57 / 56.43 / 71.14 /
71.96 %**.

---

## 3. Provenance, and what is on disk

* Probe: `scripts/probes/caiso292_screen_split_keeper.py`; artifact
  `results/calibration/_caiso292_screen_split.json` (carries the G-DRIFT audit verbatim, written
  before the keeper years were measured).
* Two bundles were recovered **read-only from git history** for validation and are left on local
  disk (rule 31 `[R-RETAIN]`): `caiso285_instr_2024` (`203124e3…`, already present from caiso-291)
  and `caiso287_instr_2022` (`bb303421…`). **Neither is committed.** Note that `.gitignore:2817`
  carries a stale **negation** for `caiso287_instr_2022/` — written when that run was a registered
  touchpoint, which it no longer is — so a careless `git add -A` would re-commit a pruned run's
  slim set. Left for the lane that owns that block; this lane added only explicit paths.
* `check_registry_payload_parity.py` walks the **filesystem**, so it goes RED locally on those two
  recovered dirs while CI stays green (rule 31, the pjm-h8 correction). Nothing was deleted to
  green it.
* `tests/regression/test_run_year_kwargs_recipe.py` + `tests/scoring`: **1,564 passed / 22 failed**
  with this lane's change, **1,562 / 22** without it — the 22 (`test_golden_manifest_provenance.py`,
  ERCOT partition-capture keys) are **pre-existing on `origin/main` and not this lane's**.
* The `mechanism-matrix-guard` PJM §5.x prose-header warning is likewise pre-existing.

## 4. Open, and NOT this lane's to decide

1. **`caiso_ra_bridge_startup_aware` admissibility** — owner court, unruled, exactly where caiso-287
   §5 and the lane instruction put it. §2.5 supplies corrected evidence for that decision and
   nothing else.
2. **The slim-bundle re-score gap (§1.6 item 3)** — 10 of 12 registered keepers commit no `floors/`
   and none commits `dispatch/`, so rule 19's "keepers re-score in place" does not hold for them.
   Fixing it costs either a re-solve per keeper or a decision to land the per-year `dispatch/`
   bytes on `main`. Cross-ISO blast radius; owner call.
3. **The three `derive_*_overlay.py` rebuilds (§1.6 item 1)** — the same missing splat, blocked
   behind rule 23 `[R-FROZEN-DERIVE]`.
