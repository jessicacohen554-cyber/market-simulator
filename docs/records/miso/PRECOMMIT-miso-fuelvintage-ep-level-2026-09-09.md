# PRECOMMIT — MISO: the measured monthly gas LEVEL (`gas_electric_power_monthly_level`)

**Session:** `miso-fuelvintage-1` · **Date:** 2026-09-09 · **ISO: MISO only.**
**Base:** `origin/main` @ `9dc1c694` (the session fast-forwarded from its handoff base
`f51c287d`, which was 42 commits behind, **before spending any LP** — §A8).
**Control:** the committed keeper bundle `results/calibration/miso248_fullspan_K`
(run id `2026-09-09-miso-248-spp-ladder`), G-CTRL **form 4**, subject to §1 below.

> **CORRECTION TO THE HANDOFF, made before any LP.** The handoff names
> `results/calibration/miso247_fullspan_K` as MISO's keeper and control. **It is not.**
> `miso-248` (commit `e4247c73`, the SPP hourly seam-ladder clock re-derive) landed on `main`
> after the handoff was written and promoted MISO's keeper to
> **`2026-09-09-miso-248-spp-ladder` / `results/calibration/miso248_fullspan_K`**;
> `miso247_fullspan_K` was pruned under rule 15's keeper-only retention and **does not exist
> at `origin/main`**. Every number below is measured against the CURRENT keeper.

---

## 0. What is being decided, and what is already decided

The owner ruled on 2026-09-09 (handoff §A7, verbatim: *"these should be promoted as keepers on
both 860 and gas shape counts regardless of inertness"*). **Promotion is therefore not this
session's question.** What is still owed, and what this document pre-registers, is the
measurement: the phase-0 census that sizes the promotion, the screen's structural STOP gates,
the full-span solve, and every criterion at full magnitude.

---

## 1. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — one LIVE hunk, and it is not the arm's

`git diff 70493448 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
(`70493448` is the keeper's recorded `git.sha`; its `run_config.json` records
`dirty: true` with `src/market_sim/model/interchange/spec.py` changed, diffstat
**69 insertions / 22 deletions**).

| file | classification | reason |
|---|---|---|
| `model/interchange/spec.py` | **INERT** | The keeper solved DIRTY at `70493448` with this file modified; `git diff 70493448 HEAD` on it is exactly **69 insertions / 22 deletions** — byte-for-byte the diffstat the bundle records. HEAD's content **is** the content the keeper solved on. |
| `data/raw/reference/iso-gas-capacity-state-weights.csv` | **INERT for the control** | New file, read only by `fuel.electric_power.iso_electric_power_monthly_level`, which is gated on the arm's own flag. It is the ARM's input, not drift. |
| `data/fuel/electric_power.py` (new), `data/fuel/resolve.py`, `data/fuel/trajectories.py`, `data/fuel/__init__.py` | **INERT** | The seam itself + its facade export; every call site is behind `getattr(config, "gas_electric_power_monthly_level", False)`, default `False`. |
| `data/fuel/basis/ercot.py`, `constants.ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU`, `solve_surface_declared.py` | **INERT** | ERCOT-scoped (`ercot_ep_gas_basis_corroborated`, default off); another ISO's branch. `solve_surface_declared` gains one frozen declaration hash, which by construction moves no key. |
| `config/scenarios.py` | **INERT** | Two new default-`False` fields + their cache-key **drop declarations** (`"gas_electric_power_monthly_level": "False"`), so a config with the field off keeps its pre-change key. |
| `scripts/run_calibration_full.py` | **INERT** | Three `argparse` flags, all `default=False`, mapped to `None` when unset. No solve-path change. |
| **`data/fleet/eia860.py` — `_PARTIAL_EXIT_WINDOW_START` 2023 → 2019 (ercot-261)** | **LIVE** | MISO's keeper carries `partial_plant_exit_carry = True`, so this ungated module constant changes MISO's fleet **composition**. Measured below. |

### 1a. The LIVE hunk, MEASURED at zero LP rather than asserted

Rebuilding MISO's control fleet through the real `run_year(..., fleet_only=True)` path at
both values of the constant (stable `unit_ids` keying, no index alignment):

| solve year | `n_gen` 2023-window → 2019-window | rows ADDED | rows REMOVED | added nameplate | **max effective MW (pmax × availability) in ANY hour** | max `min_gen` | max `pmin` | shared-row worst fleet delta | shared-row `mc_base` delta |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 3,427 → 3,598 | **171** | **0** | 3,298.899 MW | **0.000000000** | 0.000000000 | 0.0 | **0** | **0** |
| 2024 | 3,415 → 3,586 | **171** | **0** | 3,298.899 MW | **0.000000000** | 0.000000000 | 0.0 | **0** | **0** |
| 2025 | 3,395 → 3,566 | **171** | **0** | 3,298.899 MW | **0.000000000** | 0.000000000 | 0.0 | **0** | **0** |

The 171 added rows are MISO units retired 2019-2022 whose *plant* survives (98 COAL,
32 CC_REGULAR, 15 CT_PEAKER, 2 ST_CHP, 1 CT_CHP, 23 unclassed), spread over all six zones.
They enter as **all-zero-capacity columns**: the per-unit COD mask ages every one of them out
before 2023-01-01 (§A9's mechanism, working). Every pre-existing row is **byte-identical**,
`mc_base` included, in all three years. Their `ramp10` is nonzero (564.208 MW over 160 rows)
but every reserve cap in `model/reserves/spec.py` is **availability-scaled**
(`ramp10 × availability`, `Σ P + R ≤ Σ pmax·availability`), so a zero-availability row
supplies zero reserve.

**Disposition, stated ex ante.** The hunk is LIVE in the ledger and measures **zero effective
MW in every hour of every year in scope**, so form 4 is retained *provisionally* and **NO
CONTROL SOLVE IS SPENT** (rule 29(b)). The one thing the measurement cannot settle from
outside the LP is whether 171 zero-bound columns perturb the solver's basis. **That question
is answered by the screen itself, for free** (§3, gate G-0): the screen solves the ARM, and
§2 proves arm ≡ control at HEAD, so any difference between the screen and the committed
keeper is attributable to those columns alone. If G-0 fails, the control solve is earned at
that point and not before.

**A governance observation, reported and NOT acted on (out of scope, ERCOT's lane's change):**
`_PARTIAL_EXIT_WINDOW_START` is a bare module constant — no `ScenarioConfig` field, and
`data/fleet/eia860.py` is not one of the seven `config/solve_surface.py` `SURFACE_MODULES` —
so this fleet-composition change **moves no cache key** in any ISO that arms
`partial_plant_exit_carry`. For MISO the measured consequence is exactly zero MW; the
observation is about the channel, not this result.

---

## 2. PHASE 0 (rule 29 clause (0)) — the census, ZERO LP, and it is DECISIVE

Measured on the keeper's own recipe at HEAD, through `resolve_fuel_prices` /
`apply_plant_monthly_fuel_prices` / `trajectories._gas_series`.

### 2a. Admission (declared ex ante in the seam's own module, never swept)

| year | basket | covered share | admitted? |
|---|---|---|---|
| 2023 | AR .068 · IA .048 · IL .057 · IN .095 · KY .008 · **LA .238** · MI .147 · MN .076 · MO .017 · MS .046 · MT .002 · ND .003 · SD .009 · TX .091 · WI .095 | **1.000** | **ADMIT** |
| 2024 | (same fifteen states) | **1.000** | **ADMIT** |
| 2025 | IA .048 · IL .057 · IN .095 · MT .002 · ND .003 · SD .009 · TX .091 · WI .095 | **0.400** | **INERT — refused** |

**Correction to the handoff.** It says 2025 drops out because "MN and MS drop out". The
measured 2025 drop-outs are **LA (.238), MI (.147), MN (.076), AR (.068), MS (.046),
MO (.017), KY (.008)** = 0.600 of MISO's gas capacity. **Louisiana and Michigan are the
dominant two**, not MN/MS.

### 2b. What the seam actually reaches — the census the handoff asks for

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| gas generator rows / capacity | 1,609 / 69,078.8 MW | 1,616 / 69,189.7 MW | 1,614 / 68,613.4 MW |
| **print-derived share of gas capacity-hours** (`apply_plant_monthly_fuel_prices` written mask, capacity-weighted) | **1.000** | **1.000** | **1.000** |
| gas rows whose delivered price moves | **0** | **0** | **0** |
| **max \|Δ delivered gas price\|, any gas unit, any hour** | **0.0** | **0.0** | **0.0** |
| max \|Δ\| on any NON-gas fuel | **0.0** | **0.0** | **0.0** |
| ISO series `_gas_series` annual, control → arm | 2.839 → **3.019** (+0.179) | 2.489 → **2.558** (+0.069) | 3.819 → 3.819 (**0.000**) |
| `_gas_series` max monthly move | **+1.000** (Jan) | **+1.551** (Jan) | **0.000** |

The `_gas_series` annual moves reproduce FINDING §3's MISO rows (2023 model 2.839 → measured
3.019, Δ +0.179; 2024 model 2.489 → measured 2.558, Δ +0.069) **to three decimals**, and the
January gaps reproduce its "max month gap" column exactly (1.000 / 1.551). The seam is doing
precisely the arithmetic §3 measured.

### 2c. WHY the delivered array does not move — the rule-19 `[R-ONE-MECH]` answer the handoff's Card 0(d) asks for, IN WRITING AND BEFORE THE SOLVE

MISO's keeper carries `gas_plant_monthly_fuel_pricing = True`. In `resolve_fuel_prices` the
seam sets `gas_price_hourly`, which is broadcast to every gas row; then
`apply_plant_monthly_fuel_prices` runs **after** it and **overwrites** every gas cell with
that plant's own F923 monthly print (or, where a month is unreported, the
`nearby_fuel_price_fallback` / `class_aware_fuel_price_fallback` pool, and where a print is
implausible, the `f923_gas_price_plausibility_screen`'s own `N3045<ST>3` state reference).
The census measures that overwrite at **100.0 % of gas capacity-hours in all three years** —
so the seam's level never survives into `fuel_prices`. **`apply_plant_monthly_fuel_prices`
does overwrite this seam per plant, and for MISO's keeper that makes the arm inert in
dispatch.** That is the answer, established at zero LP as Card 0(d) requires.

The seam's only surviving reach is the ISO-level `_gas_series`, whose consumers are:
`coal_passthrough_series` (gated `coal_{prb,bit,…}_passthrough_sigmoid` — **all False** in the
keeper, so it returns the flat scalar and never calls `_gas_series`);
`prb_follower_passthrough_series` (gated `coal_prb_passthrough_tiered` — **False**); and
`runner.py`'s MISO offer surface (gated `miso_offer_surface_measured` — **False**).
`miso_zonal_gas_basis` is a **mean-zero spread** and orthogonal to a level;
`miso_zonal_gas_basis_skip_923_priced` consumes the same print mask that is already 1.000.

### 2d. The pre-LP identity, MEASURED — and its power demonstrated

Rebuilding the **entire** pre-LP state (`run_year(..., fleet_only=True)`) under control and
arm and diffing every numeric array — `fuel_prices`, `mc_base`, `demand`, `wind_cf`,
`solar_cf`, the capacity vectors, and every `FleetArrays` field including `availability`,
`min_gen`, `pmin`, `pmax`, `heat_rate`, `ramp10`:

| year | worst \|Δ\| across the whole pre-LP state |
|---|---|
| 2023 | **0** |
| 2024 | **0** |
| 2025 | **0** |

**Positive controls, so the zero is a measurement and not a vacuous harness** (same harness,
same year 2023, one field flipped at a time):

| perturbation | worst \|Δ\| |
|---|---|
| `gas_plant_monthly_fuel_pricing = False` | `fuel_prices` 13.875, **`mc_base` 292.467** |
| `coal_plant_monthly_pricing = False` | `fuel_prices` 3.091, **`mc_base` 60.855** |
| `f923_gas_price_plausibility_screen = False` | `fuel_prices` 200.991, **`mc_base` 2,730.599** |

The first of these is the mechanism itself: turning the print path OFF lets the trajectory the
seam moves reach the merit order at 292 $/MWh of `mc_base`. With the print path ON — which is
the keeper — it does not.

**Therefore, pre-registered as a certainty rather than a forecast: the arm's LP is identical to
the control's in 2023, 2024 and 2025, and every scored criterion must be identical to the
control's at HEAD.**

---

## 3. PRE-REGISTERED PREDICTIONS AND GATES

### 3a. The screen year, NAMED BEFORE THE SCREEN RUNS: **2024**

Named on the mechanism's **own measured footprint** — its largest monthly move is
**+1.551 $/MMBtu in January 2024** against **+1.000 in January 2023** (§2b, and FINDING §3's
"max month gap" column). **Never on a residual**, and no criterion, band or actual entered the
choice.

### 3b. Predictions

1. **The delivered gas price array does not move in any year.** Already measured (§2b): 0.0.
2. **Every scored criterion is identical to the control at HEAD, in all three years.**
   Including C3a and C3b. The handoff's pre-registration ("C3b is the criterion most likely to
   move — predicted improvement, magnitude < 0.05") was written before the census; **the census
   supersedes it with a measurement: C3b moves by exactly 0.000**, because the LP is identical.
   The handoff's flatness check ("MISO 2023's measured monthly CV is 0.148 against a model
   0.094 — a small difference, so 2023 MUST BARELY MOVE; if 2023 MOVES A LOT, THAT IS A BUG")
   is *strengthened*: **any** 2023 move at all is now a bug.
3. **2025 is inert by coverage** (basket 0.400) — `iso_electric_power_monthly_level('MISO',
   2025)` returns `None` and even `_gas_series` is byte-identical. Predicted **byte-identical**,
   and CHECKED, not assumed.
4. **The retiree window (commit `7934e92c`) contributes nothing.** MISO gains 9,127.8 MW in
   2019-2022 and **0 MW in 2023-2025**. **This run is a PURE FUEL A/B** and the fleet fix is
   credited with nothing for MISO.
5. **Out of reach, stated up front, not worked around.** MISO's Feb-2021 gas is 11.245 $/MMBtu
   below measured (~84 $/MWh at 7.5 MMBtu/MWh) — the largest in-scope defect in the program.
   Louisiana is 23.8 % of MISO's gas capacity, is the state Uri hit hardest, and EIA prints no
   `N3045LA3` month in 2019, 2020 or 2021, so the seam **refuses** those years rather than blend
   a basket that omits the hot state. **No national backfill is added.** MISO also holds no
   `complete` marker, so 2019-2022 are refused at the launch gate, the registration gate and
   `audit_keepers` regardless.

### 3c. The screen's gates — STRUCTURAL, STOP-ONLY, none referencing the target residual

A screen may KILL an arm; it may never promote one.

- **G-0 (added by this session, and it is the only gate with real information left in it).**
  The screen's 2024 outputs reproduce the committed keeper's 2024 outputs **bit-identically**.
  Because §2d proves arm ≡ control at HEAD, this is the empirical test of G-DRIFT's one LIVE
  hunk (§1a): a miss is attributable to the 171 zero-capacity columns and **earns a control
  solve at that point**, and only then.
- **G-1** the delivered gas array moves in the direction and order of magnitude the pre-solve
  arithmetic implies. **Pre-solve arithmetic says 0.0** (§2b), so G-1 passes iff the array
  moves 0.0.
- **G-2** non-gas fuel prices move **exactly 0.0**. (Already 0.0 pre-solve.)
- **G-3** rule 19: the armed monthly level equals `iso_electric_power_monthly_level('MISO',
  2024)` **exactly** at the ISO series — replaced, never blended. (Measured: `_gas_series`
  annual 2.489 → 2.558, January +1.551, reproducing FINDING §3's MISO-2024 row.)
- **G-4** no non-target load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL.
- **G-5** slack and dump stay 0.0.

---

## 4. Governance

- **Rule 29 `[R-SCREEN]`:** phase 0 first (§2, zero LP); screen year named ex ante on footprint
  (§3a); full span only after the screen clears. **No control solve** (§1a).
- **Rule 31 `[R-RETAIN]`:** the screen and full-span bundle families are **gitignored**
  (`results/screen/miso_ep_level_*/`, `results/calibration/miso_fuelvintage_*/`), which is what
  discharges rule 29(c). **Nothing is deleted.** They stay on local disk until the owner rules,
  and the promotion question is asked explicitly in the session's final report.
- **Rule 16 `[R-ALLYEARS]`:** ONE bundle covering 2023, 2024 and 2025. The screen bundle is a
  throwaway probe and is never registered.
- **Rule 22 `[R-HOLDOUT]`:** MISO holds **no** `complete` marker. Only 2023-2025 are solved,
  `--holdout-authorized` is never passed, and no marker is requested or granted here.
- **Rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`:** the promotion rests on the owner's ruling and on
  the input being the more accurate one, never on a residual. Every criterion is reported at
  full magnitude.
- **Rule 21 `[R-DOF]`:** the seam adds **zero** free parameters (frozen EIA-860 weight table,
  the EIA 1.036 MMBtu/Mcf heat content, two admission conditions declared ex ante in the module
  and never swept).
- **Rule 12 `[R-PARALLEL]`:** years sequential within the invocation, always.
- **Rule 28 `[R-MECH-MATRIX]`:** only `docs/codebase-site/data/mechanism-matrix/MISO.js` is
  edited, cell `gas_electric_power_monthly_level` (currently `O`).
