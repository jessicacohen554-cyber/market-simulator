# PRECOMMIT — SPP-48 (2026-09-19): the mid-vintage-year retiree gap

**Base:** `4583e70b864a7d5c99a206b06eddf3c36af495bf` (contains the marginal-carbon
commit `2ec096633f5624585eb9db1728ebc7c8ca5ccbdf`, verified by
`git merge-base --is-ancestor`).
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`, 2023–2025) — **UNCHANGED, and
provably un-movable by this lane** (§3.4).
**2019–2022 rung:** `2026-09-16-spp-43-outage-intake` (`spp43_holdout_span`) — the arm's target.
**LP spent by the parent: none** (rule 32 `[R-SHARD]` (a)).

---

## 0. What this lane found, in one paragraph

SPP-47's root cause **reproduces exactly** (§1). But it is **one false assumption living at THREE
seams**, not one, and fixing only the seam SPP-47 named produces a *structurally wrong* input:
Oklaunion comes back online in **all twelve months of 2020**, three of them after it had retired.
All three seams are repaired here, gated behind one default-off field, and the result is measured
at **zero LP**: the injected plant is available **May–September only**, on an envelope that covers
the CAMPD-metered generation in every month and is **zero in exactly the months metered generation
is zero**. The cross-ISO blast radius is **SPP alone**, established by a code-level gate plus a
census of all 227 committed `run_config` records (§2).

---

## 1. Phase 0 step 1 — SPP-47 §2 reproduces independently

Measured on the committed `spp43_holdout_span/dispatch/<year>_P1_fleet.parquet`, matching **both**
SPP unit-id conventions (`^127_` *and* `_p127_` — SPP-45 trap (a)):

| year | fleet rows | plant 127 | pmax |
|---|---|---|---|
| 2019 | 1126 | `COAL_SPP-North_p127_{mustrun,committed,econlo,econhi,peak}` | 650.0 MW |
| 2020 | 1110 | **absent** | 0.0 |
| 2021 | 1109 | absent | 0.0 |
| 2022 | 1094 | absent | 0.0 |

EIA's own contemporaneous vintages, read directly:

| | plant 127 (Oklaunion) |
|---|---|
| `vintage_2019/eia860_generator_operable.parquet` | Status **OP**, *Planned* Retirement **9/2020**, 720 MW nameplate / 650 MW summer, SUB |
| `vintage_2020/eia860_generator_retired_and_canceled.parquet` | Status **RE**, Retirement **9/2020** |

**Confirmed. Nothing in SPP-47 §2 failed to reproduce.** One correction to its prose: Oklaunion
lost **five** real operating months (May–September), not nine — the retirement is September, and
CAMPD is zero January–April. The GWh figure (1,209.2) is unaffected and correct.

---

## 2. Phase 0 step 2 — the cross-ISO blast radius (the gate on proceeding)

`scripts/probes/_spp48_midvintage_blast_radius.py`, zero LP, every registered region.

### 2.1 The defect is reachable only through ONE flag, and only SPP arms it

The channel is **backcast-only** (`config.mode == "backcast"` at *both* call sites,
`runner.py` and `scripts/run_calibration.py`). A backcast reaches a native vintage directory
only via `paths.resolve_backcast_eia860_vintage`, which has exactly two limbs:

1. an explicit `eia860_vintage_year` pin — **every one in the program belongs to a
   `mode="forecast"` hindcast** (39 records: PJM, MISO, NEISO, NYISO, CAISO, ERCOT, SPP), which
   never reaches this backcast-only channel;
2. `eia860_vintage_tracks_solve_year` — **armed by SPP and nothing else**.

Census over **all 227 committed `run_config.json` records**:

| armed `eia860_vintage_tracks_solve_year = true` |
|---|
| `SPP` — `spp42_span_a`, `spp43_holdout_span`, `soco15_spp_arm` |

Every other region reads the canonical snapshot, whose
`eia860_generator_retired_within_window.parquet` **already carries these plants**: MISO 17/17,
PJM 12/12, NEISO 2/2, SPP 2/2 present.

### 2.2 The potential exposure elsewhere, recorded because it is large

Mid-vintage-year retirees dropped from the operable sheet **with** metered CAMPD energy:

| region | plants | GWh | largest |
|---|---|---|---|
| MISO | 17 | **13,547.5** | E D Edwards 2,916.4 · Coffeen 2,654.0 · Duck Creek 2,246.6 |
| PJM | 12 | **6,885.3** | W H Zimmer 3,347.3 · Conesville 1,177.5 |
| NYISO | 5 | 365.7 | Somerset 160.4 |
| **SPP** | **2** | **1,257.0** | **Oklaunion 1,209.2** · Ponca 47.8 |
| CAISO | 2 | 33.8 | — |
| ERCOT | 1 | 11.3 | — |
| NEISO | 2 | 4.8 | — |
| SOCO / NWPP | 0 | 0.0 | — |

**None of it is live at HEAD**, per §2.1. It becomes live the moment a region arms the parent —
which is why the repair is landed as a shared, correctly-scoped gate rather than an SPP special case.

### 2.3 A separate, pre-existing gap — REPORTED, NOT FIXED (rule 25)

Three plants are missing from the **canonical** retiree parquet as well, so they are dropped on the
ordinary path too: CAISO **10350** Greenleaf 1 (10.3 GWh), ERCOT **50137** Newgulf Cogen (11.3 GWh),
NYISO **2521** West Babylon (1.9 GWh). Different defect, another lane's, immaterial in magnitude.

---

## 3. The repair — ONE false assumption, THREE seams

`load_retired_within_window`'s docstring states it verbatim: *"the operable fleet already has
them."* True after the vintage year; false during it.

### 3.1 Seam 1 — the injection gate (`data/fleet/eia860.py::_mid_vintage_exit_rows`)

Membership is the **strict complement** of `_partial_plant_exit_rows`' (which requires the plant to
*survive* in the operable snapshot), so the two can never select the same row: on the vintage's
Retired-and-Canceled sheet with `Retirement Year == year`, inside the region's BAs, and whose
**plant** is absent from that same vintage's operable snapshot. Returns `None` wherever the
whole-plant retiree parquet exists — so it cannot double-count on the canonical path.

### 3.2 Seam 2 — `fleet_to_bins` discards the unit's own retirement

SPP is `use_campd_bins` / `plant_level_fleet`, so the injected units are aggregated into plant-level
tranches — and a plant bin carries **no** retirement unless it is a date-scoped **exit cohort**.
This is precisely the defect miso-191 found and fixed for the partial-exit channel, so the **same
router is reused** under its own flag (rule 19 `[R-ONE-MECH]`: one mechanism, two memberships,
neither arming the other), via a `Generator.mid_vintage_exit_unit` provenance stamp mirroring
`partial_exit_unit`.

**Measured with only seam 1 fixed:** Oklaunion online **all twelve months of 2020** — a rule 17
`[R-FLOOR-WINDOW]` violation by construction (carried in hours its own driver evidence says it is
gone). With seam 2: **Jan–Sep**, zero Oct–Dec, unit ids `COAL_SPP-North_p127_r202009_*`.

### 3.3 Seam 3 — the outage derate DENOMINATOR

`outages._iso_plant_capacity`'s own comment already states the rule: a within-window exit's capacity
*"must be in the derate denominator — else their unit-outage rows route to a
`(plant_code, plant_group)` absent from this map and are skipped."* Under a native vintage that map
is built from a fleet that omits the injected plant, so **its real outage rows are silently
skipped**. The committed `data/raw/campd-unit-outages-SPP.csv` carries Oklaunion's actual stops —
**2020-01-01 → 2020-05-19** and **2020-09-26 → 2020-12-31** — which match CAMPD exactly.

Threaded default-off. **Every widened call is made at its ORIGINAL arity while the gate is off**, so
the `lru_cache` key tuples are unchanged and the off path is cache- and byte-identical, not merely
value-identical.

### 3.4 Phase 0 step 3 — the measured effect, at ZERO LP

`scripts/probes/_spp48_midvintage_fleet_reach.py` (one forked interpreter per leg — SPP-45 trap (b)),
control vs arm on each bundle's own recipe via `replay_keeper.run_year_kwargs`:

| year | LP inputs moved | units | Δ pmax | Δ available energy |
|---|---|---|---|---|
| 2019 | all 14 | 1126 → 1134 | +13.613 MW | +0.043 TWh |
| **2020** | **all 14** | **1110 → 1127** | **+931.600 MW** | **+4.700 TWh** |
| 2021 | **NONE — byte-identical** | — | 0.000 | 0.000 |
| 2022 | all 14 | 1094 → 1109 | +54.000 MW | +0.290 TWh |
| **2023** | **NONE — byte-identical** | — | 0.000 | 0.000 |
| **2024** | **NONE — byte-identical** | — | 0.000 | 0.000 |
| **2025** | **NONE — byte-identical** | — | 0.000 | 0.000 |

**The keeper cannot move, by construction and by test**: `vintage_2023/` and `vintage_2024/` ship
**no Retired-and-Canceled sheet at all** (10 files each, against 30 in 2018–2022) and 2025 has no
vintage directory, so the channel is inert in all three scored years.

**Control validity (zero LP, stronger than a control solve):** the control leg reproduces the
committed `<year>_P1_fleet.parquet` **exactly** — rows and pmax — in all four rung years
(2019 1126/59194.773, 2020 1110/58058.290, 2021 1109/58239.216, 2022 1094/58245.606).

**Oklaunion 2020, arm — availability envelope against CAMPD metered generation:**

| month | available GWh | metered GWh | implied CF |
|---|---|---|---|
| Jan–Apr | **0.0** | **0.0** | — |
| May | 181.0 | 92.5 | 0.511 |
| Jun | 454.0 | 222.6 | 0.490 |
| Jul | 469.1 | 288.9 | 0.616 |
| Aug | 469.1 | 334.9 | 0.714 |
| Sep | 363.2 | 270.2 | 0.744 |
| Oct–Dec | **0.0** | **0.0** | — |
| **total** | **1,936.3** | **1,209.1** | **0.624** |

The envelope **covers** metered generation in every month and is **zero in exactly the zero-metered
months**. Seam 3 alone moved this from 3,933.2 → 1,936.3 GWh and the window from Jan–Sep to May–Sep.

---

## 4. Governance

* **Rule 14 `[R-ACCURATE]` is the entire basis; the residual is not.** The repair was specified,
  built and gated *before* any LP. **It does not close the criterion it touches** — 1,209.2 GWh is
  11.1 % of the failing 2020 C1 `COAL_PRB` −10.85 TWh row; best case −9.64 TWh, **still a FAIL**.
  Stated here so it cannot be over-bought later.
* **Rule 29 `[R-SCREEN]`: no screen.** The screen-year regime is removed; a config goes straight to
  the full span. Recorded anyway because the brief asked for the distinction: the mechanism's own
  largest **measured footprint** is unambiguously **2020** (1,209.2 GWh vs 0.0 / 0.0 / 47.8) — a
  *footprint* fact, read off EIA + CAMPD before any solve, and **not** the residual.
* **Rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`: zero free parameters.** The retirement month is EIA's
  own published field; the membership is a set difference over EIA's own two sheets. Registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` at drop value `"False"` and in the DOF identification ledger as
  `"EIA-860 actual retirement month (native vintage)"`. `scripts/check_cache_key_registration.py`
  passes (853 fields, 308 registered, all defaults match HEAD).
* **Rule 25 `[R-ISO-SCOPE]`: default OFF, and NOT armed in `_spp_config`.** SPP has **no**
  `default_scenario_overrides` — it carries `eia860_vintage_tracks_solve_year` through the per-run
  override bag — so the arm follows SPP's own established route. **A default flip is an owner
  ruling, not this lane's** (§6).
* **Rule 28 `[R-MECH-MATRIX]` (b)+(c):** row added to `mechanism-matrix.js` plus a cell in **all
  nine** ISO shards in this same commit. SPP `O` (open, arm in flight); every other region `U` with
  its own measured exposure recorded. `check_mechanism_matrix.py --base <base>` passes.
* **Rule 23 `[R-FROZEN-DERIVE]`:** nothing re-derived. `thermal_tranches_SPP.csv` and the frozen
  `campd-unit-outages-short-SPP.csv` are untouched.
* **Rule 12 `[R-PARALLEL]` / 16 `[R-ALLYEARS]` / 32 `[R-SHARD]`:** one shard, one
  `--years 2019 2020 2021 2022` invocation, one bundle, pushed (rule 34 `[R-SHARD-PROMOTABLE]` (a)).

### 4.1 Pre-existing test failures on `main` — REPORTED, NOT PATCHED

`main` at `4583e70b` is **red on four tests** before this lane touches anything. Verified by
stashing: each fails identically at base, and for the ERCOT golden the failing `availability` hash
is **byte-identical** at base and at HEAD (`436b4f16…`), so this lane does not move it.

* `tests/regression/test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`
* `tests/regression/test_persisted_identity.py::test_solve_surface_fingerprint_is_pinned[NYISO]`
* `tests/regression/test_soundness.py::TestEndToEnd::test_capacity_evolution_changes_fleet`
* `tests/unit/data/test_fleet.py::TestLoadRetiredWithinWindow::test_neiso_includes_mystic_cc`

With those four deselected, **1,199 passed / 0 failed** across the outage, retiree, COD-ramp, fleet,
binning, CAMPD, cache-key and solve-surface suites.

---

## 5. The arm

One shard, `replay_keeper.py` on the rung bundle with the single delta
`--set mid_vintage_exit_carry=true`, all four years in one invocation, bundle pushed.
Expected to move **2019, 2020 and 2022** and to leave **2021** byte-identical.

**Pre-declared, so it cannot be written to fit the result:** the arm is a **structural input
repair** under rule 14. A criterion that gets *worse* is a discovered bug to root-cause, **not** a
reason to revert (rule 1 `[R-STRUCT]`). C1-2020 `COAL_PRB` is expected to improve and **still fail**.

---

## 6. Open questions for the owner (rule 31 `[R-RETAIN]`)

1. **Promote the arm** to replace the 2019–2022 rung `2026-09-16-spp-43-outage-intake`? The keeper
   `spp42_span_a` needs no re-solve — it is byte-identical under the arm.
2. **Arm `mid_vintage_exit_carry` as SPP's default posture** (a `_spp_config`
   `default_scenario_overrides` entry)? That is a default flip and therefore an owner ruling.
3. On promotion the rung's `holdout.keeper` stamp must be **re-applied**
   (`stamp_touchpoint_holdout.py`), and its corrected caveat text **re-authored** — a re-stamp
   resets it (known defect, `docs/calibration-log/spp.md`).
