# PRECOMMIT — the 2021 C8 failure is a TRUE POSITIVE, and the family repair that closes it is only PARTIAL (ercot-256)

> Written and pushed **before any LP solve**. Every phase-0 number below is
> zero-LP and reproducible from committed inputs. The screen year, the gates,
> the predictions and the drift audit are all registered here, upstream of the
> arm. Rule 30(c): ERCOT's determination is the **train-tier** verdict and this
> session cannot move it in either direction.

## 0. What this session picked, and the honest headline before the solve

**FAILURE A** of the ercot-256 charter — the 2021 rung's C8 forced-share breach
on ST_GAS (37.6 %, above the 30 % merchant cap), the one failure ercot-255
caused to surface.

**Phase 0 answers the diagnostic question completely and kills half the arm.**

| | |
|---|---|
| Is the C8 failure a true positive? | **YES.** The drag floor really does force two plants their own meters say were idle. §1 |
| Does the model already measure that? | **YES** — its own merit-order guard wrote the windows and deliberately kept them out of availability. §2 |
| Is the family repair already in the repo? | **YES**, on four other mechanisms; **never on this one**. §3 |
| Is the defect in-sample? | **YES** — same mechanism, 2024 and 2025, on other plants. §4 |
| Does the repair clear the 2021 C8 escalation? | **NO — measured pre-solve, and stated here before the solve.** §6 |

So the arm is built and screened **on rule 1 `[R-STRUCT]` grounds** — a floor
must not force a unit its own driver evidence says is offline, whatever that
does to the residual — and **not** because it makes a criterion pass. It does
not. §6 registers that as prediction **P6** so it cannot be re-narrated later.

## 1. The 2021 C8 failure, decomposed (zero LP, committed artifacts)

Scored from `results/calibration/ercot255_five_year_keeper` via
`calibration_verdict.determine("2026-09-07-ercot255-five-year-keeper")`:

```
forced_share ST_GAS 2021 = FAIL  37.6 % forced (4.2050 of 11.1773 TWh)
  — above the 30 % cap and NOT grounded (forcing variables miscalibrated):
    provenance — floors a unit its own meter says is offline (D-4 per-unit
    conduct FAIL): st_netload_drag (plant 3452), st_netload_drag (plant 3628)
```

Rule 16 `[R-FORCED-BUDGET]`'s escalation to a conditional pass needs **both**
legs. They split cleanly:

* **Leg (b), D-1 diurnal shape — PASSES, cleanly.** 2021 ST_GAS
  `profile_r 0.999`, `cv_ratio 1.91` against gates 0.80 / 0.50.
* **Leg (a), D-4 provenance — FAILS**, and only through the **per-unit conduct
  rider**. The window row itself passes vacuously (`st_netload_drag h0-23`,
  off-window share 0.0000) — which is exactly the tautology the rider was
  adopted (nyiso-140 §5/§6.3, K6′) to defeat.

`st_netload_drag` is the **ONLY** mechanism forcing ERCOT ST_GAS in **any**
scored year (the keeper's own D-2 rows: 4.2050 / 4.0298 / 3.3833 / 3.0083 /
3.2467 TWh for 2021–2025), so leg (a) rests entirely on this one mechanism.

### 1a. The two convicted plants, and what their meters actually say

Committed D-4 rows, 2021:

| plant | floored | share of the mechanism's forced energy | binding h | measured median over those h | share of them at zero |
|---|---|---|---|---|---|
| **3452** Lake Hubbard | 0.4970 TWh | 11.8 % | 6,026 | **0.000 MW** | **88.75 %** |
| **3628** R W Miller | 0.3325 TWh | 7.9 % | 6,423 | **0.000 MW** | **57.90 %** |

Measured CAMPD conduct (`data/raw/campd-unit-level/TX_<year>.parquet`, gross
load summed over each plant's units):

| plant | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **3452** Lake Hubbard, TWh / hours > 0 | **0.3578 / 1,924** | 0.5816 / 3,048 | 0.9410 / 3,717 | 1.7537 / 4,713 | 1.9882 / 5,496 |
| **3628** R W Miller, TWh / hours > 0 | **0.2865 / 3,317** | 0.3893 / 3,416 | 0.5149 / 3,898 | 0.5217 / 5,401 | 1.1258 / 7,707 |

**Lake Hubbard generated exactly ZERO in January, February and March 2021** —
through Winter Storm Uri — and ran 1,924 of 8,760 hours all year (unit 1: 907 h,
unit 2: 1,581 h). **R W Miller unit 1 produced 0.0 GWh in all of 2021.** The
model floors these plants for 6,026 and 6,423 hours. The rider is right.

## 2. The model's own pipeline ALREADY measures the absence — and the drag contradicts it

`scripts/lib/outage_detect.py`'s **merit-order guard** reclassifies a detected
≥ 5-day full stop as **ECONOMIC LAY-UP** when the unit's measured SRMC sat above
the revealed clearing cost for ≥ 90 % of the window, and writes it to
`data/raw/campd-unit-outages-layup.csv` (unsuffixed = ERCOT) **on the express
charter that the window stays OUT of the availability envelope** — *"an
economically idle unit is AVAILABLE; the LP declines it on its own economics."*

That charter is right for the **LP**. It is wrong for a **forcing** mechanism,
and nothing had noticed:

| ERCOT 2021, plant | detected in the AVAILABILITY overlay | reclassified as ECONOMIC LAY-UP |
|---|---|---|
| 3452 Lake Hubbard **unit 1** (396.5 MW) | **no 2021 row at all** | **272.8 unit-days** |
| 3452 Lake Hubbard **unit 2** (531 MW) | 197.0 unit-days | 9.2 unit-days |
| 3628 R W Miller unit 3 (200 MW) | 9 windows | — |
| 3628 R W Miller unit 5 (118.8 MW) | — | 20 windows |

Plant-hour shares on the model's own clock (`unit_outage_derate_factors` and
`unit_layup_removed_fractions`, ERCOT 2021):

| plant | availability multiplier, mean | lay-up share, mean | eligible = max(0, avail − lay-up) | hours eligible == 0 |
|---|---|---|---|---|
| 3452 | 0.6749 | 0.3507 | 0.3278 | **72 → 5,088** |
| 3628 | 0.3863 | 0.2000 | 0.1942 | **168 → 4,704** |

So the drag floor holds these boilers at min load inside the very windows the
model's own pipeline classified as not-operating. That is rule 17
`[R-FLOOR-WINDOW]` verbatim: *"a floor binding in hours its own driver evidence
says the class is offline is a bug by definition, whatever it does to the
residual."*

**Why the class-level driver cannot see it.** The drag's evidence base
(`docs/ercot-st-gas-netload-drag-2026-06.md`) is a **FLEET** overnight capacity
factor regressed on net load — *"committed every day and every night, never
fully off"* — and the applier then puts that one fraction on **every** non-peaker
tranche's `pmax`, i.e. asserts every gas-steam plant is equally committed. The
2021 meter says otherwise: V H Braunig 8,095 h online, Dansby 8,121, Cedar Bayou
4,809, Sommers 4,710, Handley 3,872, R W Miller 3,317, Sim Gideon 3,278, **Lake
Hubbard 1,924**. A fleet average spread uniformly over-forces the least
committed units. That is the "forcing variables are wrong" signal rule 16 exists
to raise, and the rider is detecting it correctly.

## 3. The family repair exists — and this is the one mechanism that never got it

| mechanism | correction | session |
|---|---|---|
| `reliability_floor` | `reliability_floor_plant_exclusions` (membership) | nyiso-140 |
| NYISO gas commitment bridge | `nyiso_gas_bridge_plant_exclusions` | nyiso-144 |
| `cc_/st_gas_mustrun_per_plant` | `mustrun_plant_exclusions` (membership) | miso-170 |
| `cc_/st_gas_mustrun_per_plant` | `mustrun_layup_window_mask` (**window**) | miso-173 |
| **`st_netload_drag` / `ct_netload_drag`** | **none** | — |

**The arm: `ScenarioConfig.netload_drag_layup_window_mask` (default False).**
The exact miso-173 construction on this family's shared engine
(`data/fleet/floors.py::apply_netload_reliability_floor`): the per-hour clip
basis becomes `pmax × max(0, availability − layup_share(t))`, from
`data.outages.unit_layup_removed_fractions` — the same accumulator, unit→plant
routing and capacity denominator as the outage overlay, so the two shares are
additive by construction.

* **Rule 19 `[R-ONE-MECH]`** — no new floor, no membership change, no second
  mechanism id: the existing drag's *hour eligibility* is refined by the same
  measured-conduct family that identifies its window. D-2/D-4 attribution
  unchanged.
* **Rule 21 `[R-DOF]` — ZERO free parameters.** Windows, per-unit shares and the
  0.90 out-of-merit threshold all live in the frozen derive layer (rule 23); the
  extract is consumed, never re-derived.
* **Rule 13 `[R-MEASURED]` — BACKCAST ONLY, enforced at TWO layers.** The field
  is registered in `_BACKCAST_ONLY_OVERLAY_FIELDS`, so `ScenarioConfig.__post_init__`
  **raises** if it is armed in forecast mode (verified); and
  `floors._resolve_drag_layup_shares` independently returns `{}` for any
  non-backcast run. Availability itself is never touched.
* **Rule 25 `[R-ISO-SCOPE]`** — the extract is per-ISO by construction; an ISO
  without one gets `{}` and no effect. Nothing is transferred from MISO: the
  construction is shared, the data is ERCOT's own.
* The lay-up extract carries **no CT rows at all** (the derive excludes
  combustion turbines), so the CT limb is inert under the mask **by
  construction** — and `ct_netload_drag` is not armed on the ERCOT keeper
  anyway (`meta.json: ct_netload_drag = None`, and no `ct_netload_drag` row in
  any year's D-2).

## 4. The defect is IN-SAMPLE — the lever is identified on 2023–2025, never on 2021 (rule 22 step 3)

Committed D-4 per-unit conduct FAILs on `st_netload_drag` in the keeper's own
**training** years:

| year | plant | floored | share of the mechanism's forced energy | binding h | median | at zero |
|---|---|---|---|---|---|---|
| 2024 | 3491 Handley | 0.6472 TWh | **21.5 %** | 5,227 | 0.000 MW | 75.6 % |
| 2025 | 3491 Handley | 0.8756 TWh | **27.0 %** | 6,222 | 0.000 MW | 69.8 % |
| 2025 | 3460 Cedar Bayou | 0.2006 TWh | 6.2 % | 2,396 | 0.000 MW | 57.1 % |

C8 happens to PASS in those years (17.1 / 15.3 / 20.1 %) because the class runs
19.8 / 19.6 / 16.2 TWh there against 11.2 TWh in 2021 — the *share*'s
denominator, not the floor's soundness. **Nothing in this session is identified
on 2021.**

## 5. Phase 0 — the mask's own footprint, by year (zero LP)

`run_year(fleet_only=True)` on the committed keeper's recipe, differencing the
drag floor's **mandated energy** `Σ_t min(frac_t·pmax, basis_t·pmax)` between
`basis = availability` and `basis = max(0, availability − layup_share)`:

| year | drag floor, control | with mask | **removed** | **% removed** |
|---|---|---|---|---|
| 2021 | 6.6290 TWh | 5.7671 | 0.8619 | 13.0 % |
| 2022 | 7.7874 | 7.0023 | 0.7851 | 10.1 % |
| 2023 | 8.4409 | 7.0861 | 1.3548 | 16.1 % |
| 2024 | 8.0658 | 7.0721 | 0.9937 | 12.3 % |
| **2025** | **7.2884** | **5.8192** | **1.4692** | **20.2 %** |

### 5a. THE SCREEN YEAR IS **2025**, named here before the solve

Rule 29 `[R-SCREEN]`: the screen year is the year the mechanism's **own measured
footprint is largest**, never the year with the biggest residual. 2025 is
largest on **both** measures — 1.4692 TWh absolute and 20.2 % relative — and it
is a **training** year, so the choice cannot be residual-driven. It is also the
year whose control is reproducible: the merged keeper `meta.json` carries the
**forward** config, which is what 2025 actually solved under (the two-config
provenance defect of `RESULT-ercot255` §6 corrupts only the 2023 leg).

Per-plant, 2025 (drag-floor MWh removed; binding-eligible hours ctrl → arm):

| plant | pmax | control | arm | removed | hours |
|---|---|---|---|---|---|
| 3460 Cedar Bayou | 1300.5 | 1.3647 | 0.7696 | **0.5950** | 7,205 → 3,906 |
| 49392 | 299.2 | 0.3140 | 0.0034 | 0.3106 | 7,205 → 48 |
| 3491 Handley | 1117.6 | 1.1730 | 0.8694 | 0.3036 | 7,205 → 5,238 |
| 34702 | 1330.2 | 1.3959 | 1.2536 | 0.1423 | 7,205 → 6,959 |
| 3452 Lake Hubbard | 788.4 | 0.8275 | 0.7644 | 0.0630 | 7,205 → 6,600 |
| 3628 R W Miller | 457.0 | 0.4796 | 0.4250 | 0.0547 | 7,205 → 6,438 |

## 6. THE PRE-SOLVE KILL, registered before the arm runs

The rider convicts a plant when its **measured median over the hours the floor
binds for it** is exactly zero. Masking removes floor-hours, but the plant is
convicted again if the *remaining* hours are still majority-dark. Measured
pre-solve on the **eligibility set** (`{t : basis_t > 0}`, an upper bound on the
binding set — and the binding set is systematically darker, since a floor binds
where the LP would not run the unit; measured 2021/3452 eligibility zero-share
78.3 % vs binding-set 88.75 %):

| year | plant | CURRENT eligible h / median / zero-share | **MASKED** eligible h / median / zero-share | reading |
|---|---|---|---|---|
| 2021 | **3452** | 8,688 / 0.00 / 0.783 | **3,672 / 0.00 / 0.564** | **STILL CONVICTED** |
| 2021 | 3628 | 8,592 / 0.00 / 0.620 | **4,056 / 52.00 / 0.304** | clears |
| 2024 | 3491 | 8,760 / 0.00 / 0.694 | **5,928 / 0.00 / 0.570** | **STILL CONVICTED** |
| 2025 | 3491 | 8,760 / 0.00 / 0.681 | **6,168 / 0.00 / 0.581** | **STILL CONVICTED** |
| 2025 | 3460 | 8,760 / 0.00 / 0.550 | **4,368 / 250.50 / 0.153** | clears |

**Why it is only partial, stated as a mechanism property and not an excuse.**
`UNIT_OUTAGE_MIN_DAYS = 5`: neither extract sees idleness in spells shorter than
five days. Lake Hubbard's 2021 idleness is mostly in short spells — outage +
lay-up together account for ~63 % of its capacity-hours while the plant ran at a
4.4 % capacity factor. The residual is a **grain limit of the measured window
extract**, not a defect in the mask's logic, and closing it is a different piece
of work (§9).

## 7. G-DRIFT — the code-level drift audit that licenses G-CTRL form 4 (rule 29b)

The keeper's 2021/2022/2024/2025 legs solved at `df46537c`, which **is an
ancestor of `origin/main`** (`ad78cc3e`). `git diff df46537c origin/main --
src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` = 18 files, six
non-merge commits. **Every hunk classified INERT for an ERCOT backcast:**

| commit | files | classification |
|---|---|---|
| 19e1c867 SPP-44 | `scenarios.py` +68, `constants.py` +33, `floor_mechanisms.py` +20, `pipeline/commitment.py` +174, `pipeline/kwargs.py`, `runner.py`, `pipeline/year.py`, both CLIs | **INERT** — `spp_gas_commitment_bridge`, ISO-exclusive and default off; `build_spp_gas_bridge_p1_prep` returns `None` for every non-SPP run (its own comment: "byte-identical") |
| 5bf43374 SPP-55 | `model/reserves/spec.py` +268, `reserves/__init__.py` | **INERT** — the whole addition sits under `elif iso == "SPP":` |
| 12d1d553 SPP-51 | `model/interchange/spec.py` | **INERT** — `INTERFACE_NEIGHBORS["SPP"]` only; the ERCOT DC-tie edit is SPP's view of the tie and the commit states *"ERCOT's own registry row stays 820 (rule 25)"*; blocks default-off and topology-less |
| e1165ee7 SPP-60 | `capacity_actuals_spp.csv`, `confirmed_retirements/spp.py` | **INERT** — SPP-only, and confirmed exits are forecast-mode only |
| d3808711 / d4e8cbde capx D85-R | `pipeline/persist.py` +34, `scripts/lib/key_provenance.py` (new, +846) | **INERT** — a RECORD block; its own docstring: *"not an input to any key (`cache_key` never reads it)"*. `key_provenance` is imported by no solve-path module (verified by grep over `src/market_sim` + both CLIs) |
| 19e1c867 (cont.) | `config/solve_surface_declared.py` +2 | **INERT** — two **new** SPP constant hashes appended; ERCOT's declared rows are untouched, so no ERCOT cache key moves |

**All hunks INERT ⇒ G-CTRL form 4 is valid**: the committed keeper bundle is the
control, and **no control solve is spent**. This is consistent with, and
independent of, ercot-255 §2e's measured HEAD drift of +0.0293 $/MWh on 2025 at
two different HEADs a day apart.

## 8. The screen — gates and predictions, registered before the LP

**Arm (one flag over the keeper's own recorded recipe):**

```
.venv/bin/python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/ercot255_five_year_keeper \
  --out-dir results/calibration/ercot256_screen_2025_arm \
  --year 2025 --netload-drag-layup-window-mask \
  --note "ercot-256 screen: net-load drag measured lay-up window mask, 2025"
```

The flag is **first-class** on the CLI, not routed through `--set` /
`prb_overrides`, so `run_config.json` records it under its own name — the
provenance defect `RESULT-ercot255` §6 names (and which this bundle exhibits
live: `meta.json` records `gas_st_netload_drag = false` at top level while
`coal_prb_sigmoid_overrides.gas_st_netload_drag = true`) is not reproduced here.

### 8a. Screen gates — STRUCTURAL, **STOP-only**, never read against C8/2021

| gate | question | STOP bar |
|---|---|---|
| **G-1 confinement** | only ST_GAS rows attributed to `st_netload_drag` move | any other class's or mechanism's forced energy moves |
| **G-2 direction + bound** | `st_netload_drag` forced energy FALLS, by ≤ the pre-solve mandated-energy removal (1.4692 TWh) | forced energy RISES, or the fall exceeds 1.4692 TWh |
| **G-3 magnitude** | \|Δ system load-weighted LMP\| | > $5.00/MWh |
| **G-4 non-target load-bearing** | C1 / C2 / C3a / C3b status on 2025 | any PASS → FAIL |
| **G-5 protective** | no NEW above-cap C8 class in 2025; C6 UNATTESTED in both (replay identity) | a new above-cap class |
| **G-6 shed** | slack and dump | slack > 1.0 MWh |
| **G-7 does it reach its object** | at least one 2025 `st_netload_drag` per-unit conduct row flips FAIL → pass | none flips |

**C8 is not a gate in either direction, in any year.** Neither is C3a/C3b's
magnitude. A screen read against the target criterion is the fitted-mechanism
selection rule 1 forbids, done one year at a time.

### 8b. Predictions — reported at full magnitude, hits and misses alike

| # | prediction | basis |
|---|---|---|
| **P1** | 2025 `st_netload_drag` forced energy FALLS from 3.2467 TWh; the fall is **0.30–1.47 TWh** | mandated-energy removal 1.4692 TWh is the upper bound; forced energy counts only at-floor hours, so the realised fall is strictly smaller |
| **P2** | 2025 D-4 conduct: **3460 flips FAIL → pass**; **3491 stays FAIL** | §6 masked eligibility medians 250.50 and 0.00 |
| **P3** | 2025 ST_GAS class energy falls by **less** than the forced-energy fall (the LP re-dispatches part of the freed floor economically) | the floor is below the class's economic dispatch in the tighter hours |
| **P4** | CT_PEAKER is **exactly inert** — 0.000 MWh | structural: no CT rows in the extract, and `ct_netload_drag` unarmed on this keeper |
| **P5** | 2025 system load-weighted LMP **RISES**, by **< $1.00/MWh** | removing an overnight floor removes non-economic supply from the cheapest hours |
| **P6** | **2021 ST_GAS C8 STAYS FAIL** on the full span — plant 3452 stays convicted | §6, measured pre-solve |
| **P7** | 2023/2024 remain within the same status set (no new FAIL) on the full span | the mask only removes forcing |

**If the screen clears every STOP gate**, the full span
`--year 2023 2024 2025` follows as ONE invocation and ONE bundle (rule 16), and
then 2021 and 2022 as the keeper's folded validation rungs. The screen bundle is
a throwaway diagnostic probe: never registered, never a keeper, its year
re-solved inside the full bundle. Per rule 31 `[R-RETAIN]` the bundles are
**gitignored, not deleted**, and stay on local disk until the owner rules on
promotion.

## 9. Named, and NOT taken here

* **The sub-5-day grain.** `UNIT_OUTAGE_MIN_DAYS = 5` is why Lake Hubbard 2021
  stays convicted (§6). A shorter-spell conduct instrument is a separate lever
  with its own derivation and its own DOF question; it is not attempted here and
  nothing in this session is tuned toward it.
* **The uniform-`pmax` allocation itself.** The deeper object (§2) is that a
  fleet-average commitment fraction is spread uniformly across a radically
  heterogeneous fleet. The per-plant analogue already exists elsewhere in the
  repo (`cc_mustrun_per_plant`'s top-`online_frac` placement). Redesigning the
  drag's allocation is a much larger change with a real identification question,
  and it is **named as the successor**, not attempted.
* **The two-config `meta.json` provenance defect** (`RESULT-ercot255` §6) is
  untouched and still live; it is why the screen year's control had to be a
  forward-config year.
