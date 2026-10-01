# PRECOMMIT — SPP-61: the Harrington 6193 fuel-vintage repair

**Lane** SPP-61 · **Issued against** `docs/handoffs/CHARTER-spp-61-2026-09-10.md` ·
**Base** `283afe5d62ab0a0fd8acffccd59963fcbc3d8961` · **DATA PROFILE `spp`** ·
**Control** SPP keeper 5 `2026-09-09-spp-52a-fossil-offer`, bundle
`results/calibration/spp52a_fossil93` (committed with `hourly/` sidecars; rule 29(b) **form 4**).

Written and pushed **before any solve**. Every number below is re-derived in this session from the
committed artifacts and the raw data — none is quoted from a predecessor lane's prose.

---

## 1. HEADLINE — THE CHARTER'S TWO-SIDED PREMISE IS FALSIFIED AT ZERO LP

The charter (§2) states the defect is **two-sided**: a model side (the fleet carries Harrington as
`gas_st` against its EIA-860 vintage) **and** a bench side (*"the benchmark population … books
Harrington's **coal** generation under **`ST_GAS`** (`e_ann` **3.44 / 2.23 TWh** in 2023 / 2024)"*).

**The bench side does not exist.** Measured, full-frame, both legs:

| year | bench klass rows differing by >1 MWh, canonical vs year-matched vintage | `group_by_code` plants that DO differ |
|---|---|---|
| 2023 | **0** | 26 |
| 2024 | **0** | 17 |
| 2025 | **0** | 0 |

The SPP EIA-923 benchmark frame is **completely inert** to the EIA-860 vintage. Harrington's own
bench rows are identical under both legs in every year:

| year | bench `COAL_PRB` | bench `ST_GAS` |
|---|---|---|
| 2023 | **3.1775 TWh** | 0.2601 TWh |
| 2024 | **2.0590 TWh** | 0.1749 TWh |
| 2025 | 0.0000 TWh | 2.0181 TWh |

**The benchmark already books Harrington's coal as `COAL_PRB`.** `_classify_f923` buckets each
EIA-923 Page-1 row by **that row's own reported fuel** (`SUB`→`COAL_PRB`, `NG`→`ST_GAS`), and the
raw survey splits the plant correctly (2023: 3,177,542.5 MWh `SUB` + 33,749.5 MWh `NG`; 2024:
2,059,002.3 + 174,858.7; 2025: 0 + 2,018,141.0). The one path that could have collapsed the plant
onto the fleet's `ST_GAS` label — `_backfill_eia923_with_campd`, which buckets by
`_fleet_group_by_code` — **never fires for Harrington in any year**, because its firing test
(`_plant_klass_annual(e923, 6193, mapped) >= 50,000 MWh`) is satisfied by the plant's own reported
`ST_GAS` class in every year.

**What the charter saw** is the bench **per-plant display panel**, where `plants["6193"]` carries
`group: "ST_GAS"` — a label keyed off the fleet, on a different object from `classFull`. `classFull`
is the C1 actual, and it is correct.

**Consequences, stated before the solve so they cannot be written to fit the result:**

- **C1's *actual* cannot move.** The 2024 `ST_GAS` actual of 20.101 TWh contains **0.175 TWh** of
  Harrington, not 2.23 TWh. There is no bench-side repair to make and no bench-side seam to name.
- **The charter's arithmetic for closing C1 rested on the bench side.** It is unavailable. The
  0.13 TWh of overshoot must be closed — if at all — entirely by the model side, whose sign this
  PRECOMMIT deliberately does not predict (§4).
- **This does not touch the warrant.** The repair is owed under rule 14 `[R-ACCURATE]` and rule 13
  `[R-MEASURED]` because the model's fuel vintage **is wrong and the accurate data exists**. It
  would be owed if C1 already passed. *"It would close C1" was the PRIZE, never the JUSTIFICATION*
  (charter §3), and the prize is now largely gone while the justification is untouched.

---

## 2. THE OBJECT, RE-MEASURED

### 2.1 The vintage census (EIA-860 `Generator` / operable, every committed vintage)

| vintage | unit 1 | unit 2 | unit 3 | planned repower |
|---|---|---|---|---|
| 2018–2023 | `SUB` Conventional Steam Coal | `SUB` | `SUB` | none filed |
| **2024** | **`NG` Natural Gas Steam Turbine** | `SUB` | `SUB` | **1 → 2/2025, 2 → 3/2025, 3 → 6/2025, all to `NG`/`ST`** |

All three units 360 MW nameplate; summer 339 / 339 / 340 MW.

**Fuel-switch date per unit, with source:** EIA-860 **2024** vintage `Planned Repower Month/Year`
— **unit 1 February 2025, unit 2 March 2025, unit 3 June 2025**, `Planned Energy Source 1 = NG`,
`Planned New Prime Mover = ST`. Corroborated by EIA-923 net generation, which is the measured
outcome of those dates: `SUB` **3.178 → 2.059 → 0.000 TWh** across 2023 → 2024 → 2025 while `NG`
goes **0.034 → 0.175 → 2.018 TWh**. The 2024 vintage's reclassification of unit 1 to `NG`-primary
ahead of its own filed February-2025 repower date is EIA's, not ours, and is carried as filed.

### 2.2 What the fleet builder currently does — and the ONE seam

`load_fleet_from_csv` resolves its data directory as `data_dir = active_eia860_dir()`
(`src/market_sim/data/fleet/eia860.py`). With no vintage armed that is the canonical **2025 Early
Release** snapshot, in which **all three Harrington units read `NG` / Natural Gas Steam Turbine** —
which is why the fleet carries `gas_st` in every year, matching neither the 2023 nor the 2024
release. The COD ramp can filter a snapshot by commissioning date; it cannot un-convert a fuel.

**THE ONE SEAM (rule 19 `[R-ONE-MECH]`), and it is already registered:**
**`ScenarioConfig.eia860_vintage_tracks_solve_year`** (plain bool, GATED default `False`) →
`config/paths.py::resolve_backcast_eia860_vintage`, the single resolution both backcast entry points
share. Built by pjm-167 for the same root cause — *the registry is not year-matched* — and
**never armed by any committed run, in any ISO**; SPP-61 would be its first arm anywhere.

No second channel is built. A per-plant fuel table would be an off-registry hardcoded dict
(rule 24 `[R-REGISTRY]`); a second vintage channel beside this one would be stacking on the
unexplained residual of an existing mechanism (rule 19). **There is no bench-side seam** — §1.

**Zero code change.** The arm rides `replay_keeper.py --set eia860_vintage_tracks_solve_year=true`,
the registered generic `prb_overrides` channel, which `backcast_config` applies to `config` before
`run_year` reads the field at `scripts/run_calibration.py:2585`. Verified by the phase-0 census,
which armed it through exactly that path and produced the armed fleet.

### 2.3 What the arm actually does to the fleet — MEASURED, and it is NOT confined to plant 6193

`scripts/probes/_spp61_phase0_census.py`, `run_year(fleet_only=True)` on the keeper's own recipe,
control vs arm. Registry `pmax` MW:

| class | 2023 control | 2023 arm | Δ | 2024 control | 2024 arm | Δ |
|---|---|---|---|---|---|---|
| COAL | 20,694.7 | 20,036.3 | **−658.4** | 20,694.7 | 19,849.6 | **−845.1** |
| ST_GAS | 10,463.5 | 9,719.0 | **−744.5** | 10,463.5 | 9,515.1 | **−948.4** |
| CT_PEAKER | 11,799.6 | 10,491.6 | **−1,308.0** | 11,846.6 | 10,564.5 | **−1,282.1** |
| CC_REGULAR | 10,047.8 | 10,057.1 | +9.3 | 10,047.8 | 9,955.3 | −92.5 |
| **_TOTAL** | **60,749.0** | **58,033.6** | **−2,715.4** | **60,739.9** | **57,564.6** | **−3,175.3** |
| 2025 (no `vintage_2025/`) | 60,739.9 | 60,739.9 | **0.0** | | | |

Harrington itself lands exactly on its vintage: **2023 → 1,018.0 MW all in `COAL`**;
**2024 → 679.0 MW `COAL` + 339.0 MW `ST_GAS`** (units 2+3 coal, unit 1 gas); **2025 unchanged at
1,018.0 MW `ST_GAS`**, because no `vintage_2025/` directory is committed and the resolver falls
through to the canonical snapshot — which for 2025 is the *correct* answer, the units having
converted in Feb/Mar/Jun 2025.

**This is stated at the gate rather than absorbed: the arm swaps the whole registry, not one
plant.** The charter's provisional gate wording *"is the footprint confined to plant 6193"* cannot
be met by any honest construction of this repair and is replaced by G2 in §5, which asks the
question rule 29 actually asks — is the footprint confined to **the rows the mechanism claims**.

**The wider footprint is the vintage being right, not the vintage being broken.** Root-caused at
plant grain (2023): the three largest non-Harrington moves are `CT_PEAKER` plant **64547
(−442.2 MW, absent entirely)**, plant **64548 (−151.2 MW, absent entirely)** and plant **57881
(763.0 → 232.8 MW)** — high-numbered plant codes, i.e. units that **did not exist in 2023** and are
correctly absent from the 2023 release while the canonical snapshot carries them. The control's own
totals give the same verdict independently: **60,749.0 / 60,739.9 / 60,739.9 MW** across three years
— a registry that barely moves, which is precisely the pjm-167 defect (*"an IDENTICAL 38,722 MW coal
fleet in 2021, 2022 and 2023"*). The vintage files are complete annual releases, not truncated
ones: 26,011 / 26,856 / 27,769 rows for 2023 / 2024 / canonical, 73 columns each, growing with
vintage as they should.

---

## 3. SCOPE CHECK — rule 25 `[R-ISO-SCOPE]` (charter §4 item 5)

The charter warns the fuel-switch seam is *"a **fleet** seam and explicitly **not SPP-only**"*.
**As constructed here it is per-run and cannot reach another ISO:**

- `eia860_vintage_tracks_solve_year` is a **`ScenarioConfig` field, dataclass default `False`**,
  registered in `_CACHE_KEY_OPTIONAL_FIELDS` **at its declared `"False"`** — so it is dropped from
  the hash at that value and **every pre-existing cache key of all seven ISOs is byte-stable**.
- It is armed **per run, through `--set` on SPP's own bundle**. **No shared default is flipped**, no
  `ISOConfig.default_scenario_overrides` is touched, **no file under `src/` or `scripts/` is edited
  at all.** Every other ISO's keeper config still carries `False` and re-solves byte-identically.
- **Nothing is transferred between ISOs** — no fitted number crosses a boundary; the arm derives
  entirely from SPP's own EIA-860 releases.

**Verdict: zero other ISOs move, by construction.** Nothing is silently re-keyed and no ruling is
required. What IS routed rather than acted on here: the same repair is presumptively owed in every
other ISO on rule-14 grounds, and each ISO's desk owns that decision on its own measurement
(rule 28(d) — a verdict in SPP never fills another ISO's cell).

**One latent defect found and ROUTED, not touched.** In `scripts/run_calibration_full.py` the
benchmark's `group_by_code` is built at **line 5286**, before `run_year` sets the year's vintage at
**line 5396** — so under an armed run the bench bucket reads the *previous* year's vintage (or the
canonical snapshot in the first year). **Measured effect for SPP: exactly zero** (§1 — the bench
frame is inert to the vintage in all three years, 0 rows > 1 MWh). It is therefore **not fixed in
this lane**: repairing an inert path would be an unmeasured change to a shared driver outside this
lane's object. Routed to the desk register for the ISOs where the CAMPD backfill does fire.

---

## 4. THE ZERO-LP PREDICTION — AND WHAT IT HONESTLY CANNOT SAY

**Control, re-derived here with `scripts/calibration_verdict.py` at HEAD** (not quoted): keeper 5
reads **NOT-YET**, grade **6 of 8**, 2 fails, `protective: 0 / ledgered: 0 / commercial_band: 0`
against a ledgered budget of 1. C1 fails on **one row**:

| year | class | model | actual | magnitude | verdict |
|---|---|---|---|---|---|
| 2023 | ST_GAS | 8.073 | 15.020 | −6.95 TWh, −2.4 pp | PASS — **1.05 TWh of volume headroom** |
| **2024** | **ST_GAS** | **11.970** | **20.101** | **−8.13 TWh, −2.8 pp** | **FAIL — volume only** (share passes) |
| 2024 | COAL_PRB | 59.463 | 59.961 | −0.50 TWh | PASS |
| 2024 | COAL_LIGNITE | 6.503 | 8.670 | −2.17 TWh | PASS |
| 2024 | CT_PEAKER | 19.684 | 15.911 | +3.77 TWh | PASS |
| 2025 | all | — | — | SKIPPED, preliminary EIA-923 vintage | — |

**Prediction, per year, both sides:**

- **Bench side, all three years: 0.000 TWh, on every class.** Measured, not estimated (§1).
- **Model side:** Harrington stops being a gas-priced `ST_GAS` unit that the SPP-49 gas-price screen
  had pushed out of merit, and becomes a coal-priced `COAL_PRB` unit whose measured 2023/2024 coal
  output is **3.178 / 2.059 TWh**. Direction: **`COAL_PRB` up**, `ST_GAS` down by whatever
  Harrington was contributing, and ~2–3 TWh of displacement onto whichever classes it undercuts.
  `COAL_PRB` has wide headroom in both years (−1.81 / −0.50 TWh against ±8.00) and **survives** even
  if it takes Harrington's full measured coal volume. Simultaneously the arm removes 1,282–1,308 MW
  of `CT_PEAKER` and 744–948 MW of `ST_GAS` capacity against unchanged load, which pushes energy
  *back* toward the surviving thermal fleet.

**The two model-side effects oppose each other on the target row and this PRECOMMIT does not
predict which wins.** Saying more would be arithmetic reverse-engineered from a band. What can be
said honestly:

- **C1-2024 `ST_GAS` is 0.13 TWh outside a 8.00 TWh bound and can go either way — including
  further out.**
- **2023 is at real risk and this lane may break it.** It passes with **1.05 TWh** of headroom and
  the arm moves Harrington's **larger** coal volume (3.178 TWh) in that year.
- **If the repair makes the fit worse it stays in** (rule 1 `[R-STRUCT]` first half; rule 14 in
  terms). A worse fit is a discovered bug elsewhere, to be root-caused and routed — **not** buried
  back in the input, and **not** answered by repairing one side only to keep both years green.

---

## 5. THE SCREEN (rule 29 `[R-SCREEN]`)

### 5.1 Screen year — **2023**, named by MEASURED FOOTPRINT

| | 2023 | 2024 |
|---|---|---|
| Harrington capacity reclassified to coal | **1,018.0 MW (3 of 3 units)** | 679.0 MW (2 of 3) |
| Harrington measured coal, EIA-923 `SUB` net | **3.1775 TWh** | 2.0590 TWh |
| Harrington measured coal, CAMPD gross (charter §2) | **3.54 TWh** | 2.51 TWh |

**Every measure of the object's own footprint is larger in 2023**, confirming the charter's
expectation by this session's own measurement. It is also the choice that **cannot** be
residual-driven: the failing row is in **2024**, so screening 2023 is the opposite of picking the
year with the biggest residual. (The *whole registry* delta is marginally larger in 2024,
−3,175.3 vs −2,715.4 MW; the object this lane was chartered on is Harrington, and 2023 is its year.
Stated so the choice is auditable either way.)

### 5.2 STOP gate — STRUCTURAL, and it reads C1's residual NOWHERE

Pre-registered here, before the solve. It **may kill the arm; it may never promote one**.

- **G1 — fleet identity.** The armed 2023 registry carries Harrington at **1,018.0 MW in `COAL`
  and 0.0 MW in `ST_GAS`**, and the class totals reproduce §2.3 (`_TOTAL` **58,033.6 MW ± 1 MW**;
  COAL 20,036.3, ST_GAS 9,719.0, CT_PEAKER 10,491.6). A miss means the arm is not the mechanism
  this PRECOMMIT describes. **FAIL ⇒ STOP.**
- **G2 — footprint confinement (the rows the mechanism CLAIMS).** Every plant whose class or
  capacity moves is a plant whose **2023 EIA-860 release differs from the canonical snapshot** —
  the set enumerated at phase 0. **Zero plants outside that set move.** **FAIL ⇒ STOP.**
- **G3 — the dispatch response has the direction and order of magnitude the pre-solve arithmetic
  implies.** Model `COAL_PRB` **rises** in 2023, by an amount of the same order as Harrington's
  measured 3.1775 TWh (accepted band **+1.0 to +4.5 TWh**), and model `ST_GAS` does not rise. A
  reclassified 1,018 MW coal unit that dispatches ~0, or a `COAL_PRB` move an order of magnitude
  off, means the mechanism is not doing what its own arithmetic says. **FAIL ⇒ STOP.**
- **G4 — no NON-TARGET load-bearing criterion flips PASS → FAIL in 2023**: C2 `sysvol`, C3a
  `price_mean`, C3b `price_shape`. **FAIL ⇒ STOP.** *(C1 `fuelmix` is the TARGET criterion and is
  deliberately **excluded**: under rule 1 a structurally-correct mechanism is never rejected because
  its residual moved the wrong way. C1-2023 is **REPORTED at full magnitude**, never gated.)*
- **G5 — bench inertness holds.** The rebuilt 2023 bench `classFull` is byte-identical to the
  committed one, as §1 predicts (0 rows > 1 MWh). A move here falsifies §1 and the lane re-plans.
  **FAIL ⇒ STOP.**

**Not in the gate, by design:** C1's residual on any row, in any year. A screen that reads *"did
C1-2024 improve"* is the fitted-mechanism selection rule 1 exists to forbid, done one year at a
time.

### 5.3 If the screen clears

The full span as **ONE `--years 2023 2024 2025` invocation and ONE bundle** (rules 12 / 16
`[R-ALLYEARS]`), `results/calibration/spp61_vintage`. The screen bundle is a **throwaway diagnostic
probe**: never registered, never a keeper, never quoted as a keeper number, and 2023 is re-solved
inside the full bundle. Per rule 29(c) it is kept out of `main` — the screen shard **pushes
nothing** and reports in numbers, which discharges the duty absolutely; per rule 31 `[R-RETAIN]`
nothing is ever `rm`'d.

---

## 6. G-DRIFT — the code-level drift audit (rule 29(b)), so NO CONTROL SOLVE IS SPENT

Keeper 5's recorded `git.sha` `c1393878` is a squashed branch commit and does not resolve in this
repo; its `basis_sha` **`fc927c2f439a4e00207bab7c35abd10dc556142b`** does and is the anchor used.

**Mechanical instrument first (capx D79).** The SPP **solve-surface fingerprint** at HEAD is
**`7ab7e3b0c4741dc3`, 182 rows, `moved: {}`** — **byte-identical** to the value recorded in the
keeper's `run_config.json`.

**Hunk-by-hunk classification** of `git diff fc927c2f HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
(17 files, +1,338 / −423):

| file | classification | reason |
|---|---|---|
| `data/fleet/eia860.py` (`_PARTIAL_EXIT_WINDOW_START` 2023→2019) | **INERT** | the whole `_partial_plant_exit_rows` path is behind `partial_plant_exit_carry`, **`False` in the keeper's recipe** and default-off |
| `model/interchange/spec.py` | **INERT** | every changed hunk is inside `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR` / `_POOLED` — **MISO's** branch, gated `miso_seam_neighbour_hourly_spp` (`False` in the recipe); an SPP solve never reads them |
| `data/fuel/{resolve,trajectories,__init__}.py`, `data/fuel/electric_power.py` (new), `data/raw/reference/iso-gas-capacity-state-weights.csv` | **INERT** | all reached only under `gas_electric_power_monthly_level`, a **new default-off field absent from the keeper's recipe**; both call sites return the incoming series unchanged when off |
| `data/fuel/basis/ercot.py`, `config/constants.py` (`ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU`) | **INERT** | another ISO's branch |
| `data/raw/_validation-source/actual_lmp.json` | **INERT** | 10 changed leaves, **all under the `ERCOT` block; zero SPP** (verified by structural diff) |
| `config/scenarios.py` | **INERT** | four new fields, all `bool = False`, all absent from the recipe |
| `config/solve_surface_declared.py` | **INERT** | two declarations, ERCOT- and NYISO-scoped; SPP fingerprint unmoved (above) |
| `data/fleet/floors.py` | **INERT** | the pjm-177 `netload_drag_min_run_persistence` helpers, default-off and absent from the recipe |
| `scripts/run_calibration{,_full}.py` | **INERT** | `netload_drag_min_run_persistence` plumbing (default `None` ⇒ no override applied) + removal of the `[R-HOLDOUT]` year gate — **gate machinery, not solve physics** |
| `scripts/lib/holdout_policy.py`, `scripts/lib/key_provenance.py` | **INERT** | `[R-HOLDOUT]` removal / cache-key provenance accounting; neither on the solve path |

**ALL HUNKS INERT ⇒ rule 29(b) form 4 is VALID: keeper 5's committed bundle IS the control, and
no control solve is spent.** Corroborated end-to-end — re-scoring the committed keeper at HEAD
reproduces its published determination and every C1 row exactly (§4).

---

## 7. DOF LEDGER EFFECT — rule 21 `[R-DOF]`

**ZERO new free parameters.** `eia860_vintage_tracks_solve_year` is a boolean gate whose selection
is **by calendar year alone** — the solved year selects its own annual EIA-860 release. Nothing
here reads a model output, a price, a residual or a scoring target; there is no scalar to set, no
band, no share, no threshold. Its identification source is **the published EIA-860 annual releases
themselves** (rule 13 `[R-MEASURED]`: the same construction regenerates for a forward year from the
then-current release and responds to changed conditions). The keeper's DOF ledger is carried forward
unchanged — `n_residual` stays **2**, entries stay **3**.

**No authorized-price-tuning change.** The keeper's `offer_curve_by_group` block is replayed
**verbatim** — all ten registered fossil classes at **0.93** on exactly the four bands
(`committed` / `econ_low` / `econ_high` / `peak`) — one config across every scored year, never
swept, and it remains declared in the attestation's `authorized_price_tuning` block. **Nothing in
this lane touches it.**

---

## 8. RULE 32 `[R-SHARD]` — the shard plan

**This session is an ORCHESTRATOR and runs no LP** (rule 32(a)). Phase 0, the G-DRIFT audit, the
gate evaluation, composition, scoring and registration all stay here; every solve is a shard.

Measured span cost is **~7 min of LP for all three years** (SPP is a two-zone ISO), so each unit
below is comfortably inside the 20-minute shard-commit bound and **no shard needs to launch
children**.

| shard | scope | out-dir | pushes? |
|---|---|---|---|
| **A — screen** | `--years 2023` | `results/calibration/spp61_screen_2023` | **NO** — reports numbers only (rule 29(c): the bundle never reaches `main`) |
| **B — full span** (only if A clears §5.2) | `--years 2023 2024 2025`, ONE invocation | `results/calibration/spp61_vintage` | yes, its own branch, `git add -f` that path only |

Both are single-delta replays of the committed keeper:
`python scripts/replay_keeper.py results/calibration/spp52a_fossil93 --set
eia860_vintage_tracks_solve_year=true --years <…> --out-dir <…> --note "SPP-61 …"`.

Each shard prompt carries, per rule 32(c): the **full 40-char pinned SHA** with
`git rev-parse HEAD` as its first hard stop and **no rebase / no `git pull` / no sync**;
`DATA PROFILE: spp`; its own out-dir and branch; the **config signature hard stop** — all ten
fossil classes at **0.93** on the four bands **and** `eia860_vintage_tracks_solve_year: true` in the
solved `run_config.json`, **and** Harrington at 1,018.0 MW in `COAL` for 2023 — a shard that sees
otherwise **STOPS and does not push**; exactly what to report, in numbers; and the forbid list by
name — `git add -A` / `git add .`, `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`,
`prune_iso_runs.py`, anything under `frontend/data/backcast/**`, any edit under `src/` or
`scripts/`, opening a PR, deleting any result — plus: *"A shard that stops with a clear report is a
SUCCESS; a shard that repairs infrastructure is a FAILURE."*

---

## 9. WHAT THIS LANE WILL AND WILL NOT CLAIM

- **CALIBRATED is the scorer's to produce.** Whatever it says is reported as-is.
- **The `complete` marker and any `frontier` declaration are OWNER acts.** Not added, not requested,
  not implied.
- **No year in this program is protected from being iterated against** (`[R-HOLDOUT]` removed
  2026-09-09). Every number this lane produces — a CALIBRATED determination included — is model-**
  SELECTION** evidence, not a certified out-of-sample skill claim, and will be labelled that way
  wherever it is quoted.
- **Retention (rule 31 `[R-RETAIN]`):** no bundle is ever `rm`'d. Anything solved stays on local
  disk, `.gitignore` discharges the keep-it-out-of-`main` duty, and the **promotion question is
  asked explicitly in-session while the bundle is alive**, stating that the container is ephemeral.
