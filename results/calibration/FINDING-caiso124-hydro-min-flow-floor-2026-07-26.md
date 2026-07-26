# FINDING — caiso-124: the hydro MINIMUM-FLOW FLOOR lane, built and A/B'd against pre-registered gates (owner-flagged 2026-07-26) — plus TASK 2: the caiso-123 §5 residual's `src/market_sim/` window is now CLOSED BY MEASUREMENT

**Keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED. Promotion is an
owner call (PREREG §6) and sits behind two open sequencing decisions this
session does not touch (the neiso-66 extract over-count freeze, ACTIVE; the
caiso-123 §6 re-tune-vs-wait question).**

Gates were written down and committed **before arm B solved**
(`results/calibration/PREREG-caiso124-hydro-min-flow-floor-2026-07-26.md`,
commit `353d88e`). This finding scores them; it does not add or move any.

---

## §1 — the mechanism (what was built)

ONE registered switch, `ScenarioConfig.hydro_min_flow_floor`, default off. It
adds the **lower half of the measured two-sided hydro capability envelope** whose
upper half — `hydro_dispatch_envelope`, the caiso-72 p95 (month × hour-of-day)
deliverability ceiling — the CAISO keeper already carries.

**The gap it closes.** The hydro budget family caps a plant's monthly *energy*
and imposes no lower bound, so the purely-economic LP is free to park the whole
fleet at 0 MW. The keeper does exactly that:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model hours < 10 MW | 270 | 693 | 601 |
| model hours < 100 MW | 926 | 1342 | 1169 |
| model hourly p5 (MW) | 25 | 0 | 0 |
| **measured** hourly p5 (MW) | **954** | **876** | **738** |

Reality never approaches zero: run-of-river inflow cannot be stored, and every
licensed project passes an environmental / FERC-licence minimum flow.

**Rule-17 declaration** (mirrored verbatim in the `ScenarioConfig` field, the
`MECH_HYDRO_MIN_FLOW` registry entry and the `D4_WINDOWS` row):

- **driver** — run-of-river inflow + licence minimum releases.
- **window** — ALL 24 h, by physics *and* by measurement: the measured series has
  no hour-of-day bucket that approaches zero (diurnal minimum-of-means
  1.7/1.4/1.2 GW at hod 11–13). The opposite of the CT overnight-offline
  signature rule 12 exists to catch. It BINDS in the solar belly and the
  overnight shoulder.
- **forward story** — the level re-derives from the same EIA-930 `NG: WAT`
  history the ceiling uses (own year in a backcast, pooled
  `HYDRO_CLIMATOLOGY_YEARS` per-month percentile for a year the extract does not
  cover) and scales with the water year through the budget it is clipped against.

**Two design choices carry the rule-13 weight.**

1. **The percentile is the ceiling's, mirrored.**
   `HYDRO_MIN_FLOW_PERCENTILE = 100 − HYDRO_ENVELOPE_PERCENTILE = 5`. Read as an
   exceedance level this is **Q95**, the standard hydrological low-flow index
   that minimum-flow licence conditions are themselves written against. **Zero
   new free parameters** — the two-sided envelope is identified by the one
   percentile the committed ceiling already carries (DOF ledger: +0).
2. **The bucket is the MONTH ALONE, not (month × hour-of-day).** A floor
   carrying the measured diurnal shape would pin the measured *outcome* — and it
   measures out at **~75 % of the annual budget**, i.e. it would *be* the
   dispatch model. The month-constant form is what a minimum-flow condition
   physically is (inflow and licence releases vary seasonally, not by
   hour-of-day) and costs **46.3 / 42.2 / 35.7 %** of the monthly budget, leaving
   54–64 % economically shaped.

**Allocation** — per plant, pro-rata by its own share of that month's energy
budget (`data.hydro.allocate_min_flow_floor`). Measured weight, no free
parameter, and it buys three properties: per-plant monthly feasibility is exact
(worst plant-month floor/budget 0.595/0.531/0.561 — the feasibility clip binds
nowhere), the *geography* of the water stays faithful across CAISO's zones, and
no LP degeneracy is added across equal-cost hydro units (a fleet-aggregate row
would have let the LP pick arbitrarily among them — the vertex-wander failure
mode caiso-123 §5 is already chasing).

Derived level (MW by month, each solve year's own EIA-930 series):

| year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | 615 | 664 | 1403 | 2102 | 1731 | 1598 | 1958 | 1722 | 1620 | 852 | 610 | 565 |
| 2024 | 842 | 869 | 1620 | 928 | 1403 | 1179 | 1639 | 1555 | 843 | 766 | 736 | 685 |
| 2025 | 969 | 1406 | 1429 | 849 | 1033 | 634 | 715 | 996 | 876 | 30 | 434 | 1099 |

Applied through `FleetArrays.min_gen` with mechanism id `MECH_HYDRO_MIN_FLOW`,
so the floor is visible to the D-2/D-4 diagnostics; classified **non-thermal**
(reported by D-2, never counted against a merchant thermal class's C8 budget)
and **ablated** in the D-3 registry. The floor survives into P1: both P1-native
bridges maximum-compose onto `min_gen`
(`pipeline.commitment._bridge_floored_fleet`), they never overwrite it.

**Conservative by construction (rule 14, documented).** For CISO the EIA-930
`NG: WAT` series nets pumped-storage load, so a pumping hour *lowers* it and the
derived level is a **lower bound** on the conventional fleet's own minimum flow.
It can only under-state the floor. Levels are clipped at zero for the same
reason (CISO 2025 has pumping hours at −463 MW).

## §2 — the A/B result: KILLED AS WRITTEN by its own pre-registered K3, in 2025 only

Arm A `caiso124_control_A` (keeper recipe, no delta) and arm B
`caiso124_minflow_B` (+ the single switch) both solved 2023-2025 in one
invocation at `basis_sha 4094bbe`, sequentially, same container, same
regenerated `capacity-deliverability` partition (seam import cap 16,055 MW
affirmatively logged in both — the RESULTS-neiso65 §2 silent-degrade trap).
Arm B's log carries the arming line for all three years, matching the offline
derivation to the digit:

```
CAISO 2023: hydro min-flow floor on 171 units — fleet level  565-2102 MW by month (11.30 TWh, 46% of the 24.40 TWh budget)
CAISO 2024: hydro min-flow floor on 160 units — fleet level  685-1639 MW by month ( 9.57 TWh, 42% of the 22.68 TWh budget)
CAISO 2025: hydro min-flow floor on 160 units — fleet level   30-1429 MW by month ( 7.62 TWh, 36% of the 21.32 TWh budget)
```

| year | arm | hydro TWh | h<10MW | h<100MW | p5 MW | belly gap | evening gap | profile r | profile MAE | cv_model/cv_meas |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | A | 24.09 | 270 | 923 | 25 | **−587** | +115 | 0.960 | 366 | — |
| 2023 | **B** | 24.20 | **0** | **0** | 639 | **−98** | −254 | **0.965** | **168** | — |
| 2024 | A | 21.43 | 692 | 1343 | 0 | **−610** | −117 | 0.974 | 348 | 1.439 |
| 2024 | **B** | 21.95 | **0** | **0** | 741 | **−54** | −386 | **0.975** | **148** | **0.977** |
| 2025 | A | 20.68 | 604 | 1163 | 0 | **−548** | +7 | 0.985 | 343 | 1.419 |
| 2025 | **B** | 21.14 | **0** | **172** | 522 | **−84** | −264 | 0.977 | **169** | **1.048** |

**Scored against the pre-registration exactly as written (§3/§5):**

| gate | 2023 | 2024 | 2025 |
|---|---|---|---|
| P1 h<10 MW → 0 | PASS | PASS | PASS |
| P1 h<100 MW < 150 | PASS (0) | PASS (0) | **MISS (172)** |
| P2 belly |gap| ≤ 200 MW and improved | PASS | PASS | PASS |
| P3 profile MAE strictly falls | PASS | PASS | PASS |
| P4 D-2 row + D-4 off-window 0 | PASS | PASS | PASS |
| K1 evening overshoot > +300 MW | pass | pass | pass |
| K2 evening starvation < −600 MW | pass | pass | pass |
| **K3 profile r ≥ arm A's** | pass | pass | **KILL (0.985 → 0.977)** |

**VERDICT: KILLED.** K3 tripped in 2025. No gate was moved, loosened, or
re-scored against a substitute. Arm B is registered as
`2026-07-26-caiso-124-hydro-minflow` (rule 15 — a rejected probe is registered
like any other completed run); arm A is not registered.

**P4 in full** (`legitimacy_diagnostics.json`, committed with the bundle):
D-2 `hydro × hydro_min_flow` = **5.42 / 4.92 / 4.18 TWh forced, 22.4 / 22.4 /
19.8 % of class** — under the 30 % merchant cap even though, being non-thermal,
it is excluded from the gated arithmetic (D-2 summary: hydro `forced_share 0.0`,
verdict pass, C8 PASS). D-4 off-window share **0.0000** all three years, window
`h0-23`. C7 diurnal shape (D-1) PASS.

**What the mechanism demonstrably fixed**, in every year:

- the parks-at-zero pathology is **gone** (hours below 10 MW: 270/692/604 → 0);
- the belly deficit closes by **83–91 %** (−587/−610/−548 → −98/−54/−84 MW);
- the hour-of-day profile MAE **more than halves** (366/348/343 → 168/148/169);
- the model's diurnal **amplitude error is corrected**: cv_model/cv_meas
  **1.44 → 0.98** (2024) and **1.42 → 1.05** (2025) — the swing was 42–44 % too
  large and is now right;
- **budget utilisation** rises to 99.2 / 96.8 / 99.1 % (from 98.7 / 94.5 /
  97.0 %): arm A was *declining* 1.3–5.5 % of the measured monthly water because
  no hour was worth generating in, which the floor also corrects.

**Why K3 still tripped, measured.** The 2025 `r` loss is not an amplitude or
level defect — every level/amplitude measure improved. It is a peak-shape
artifact: with the monthly energy budget a hard cap, the belly lift has to be
paid for, and the LP paid partly out of the evening peak. Arm A's 2025 evening
was already correct (+7 MW), so B's peak now sits 250–390 MW *below* measured
and its maximum shifts from hod 20 to hod 21, while the overnight shoulder stays
150–300 MW above. A 24-point correlation is dominated jointly by amplitude and
peak placement, so **the metric I pre-registered penalised the amplitude
correction it should have rewarded** (`r` −0.008 against cv_ratio 1.42 → 1.05).
That is a finding about the gate, not a licence to ignore it: K3 was written
before the solve and it tripped, so the delta is KILLED as scored, and choosing
a corrected shape gate is an owner decision, not a re-score this session may
perform. If one is authorised, the natural pair is the rubric's **own** D-1
statistics (`cv_ratio` + `profile_r` together, as C7 scores them — C7 PASSES in
arm B) rather than raw `r` alone.

## §3 — rubric, reported not gated (rule 1)

Arm B, from its committed `metrics.json`. Arm A's rubric is unavailable **by
protocol** — scoring requires registration and the control is never registered
(FINDING-caiso92b); its λ is measured instead (§4).

| | keeper (own bytes) | arm B |
|---|---|---|
| C1 fuel-mix | PASS | PASS |
| C2 system volume | PASS | PASS |
| C3a mean LMP | PASS | **FAIL** — 2023/2024 pass, **2025 +10.9 %** |
| C3b price shape | PASS | PASS |
| C3c price tail | FAIL (0 h vs 47/35) | FAIL (0 h vs 47/35) |
| C4 dispatch corr | PASS | PASS |
| C5a CO2 | FAIL −10.7/−10.1/−11.8 % | FAIL **−11.0/−10.2/−13.5 %** |
| C6 governance | PASS | UNATTESTED (a replay carries no attestation) |
| C7 diurnal shape | PASS | PASS |
| C8 forced share | PASS | PASS |

Two entries need saying plainly:

- **C3a-2025 +10.9 % is the attributed extract basis, not this delta** — exactly
  as pre-registered (§4 S4). caiso-123 §3 established that any honest same-HEAD
  control reads ≈ +11.1 %; arm B is marginally *better* than that, and arm A's
  own λ (§4) confirms the control sits in the same place. The floor is neither
  credited nor debited for it.
- **C5a moves the wrong way** (−0.3 / −0.1 / **−1.7** pp vs the keeper), and part
  of that is the delta's own: B carries +0.11 / +0.52 / +0.46 TWh more
  zero-carbon hydro than A, displacing gas in a CO2 residual that is already
  ~11 % low. This is reported as a cost, **not** as a rejection ground — rule 1
  forbids rejecting a structurally-correct mechanism because a fit metric moved,
  and the rejection here rests solely on the pre-registered K3.
- **S3 (C3c direction) is REFUTED.** The mechanism story — removing over-saved
  evening water should raise evening prices toward the measured scarcity tail —
  does not materialise: model h>$200 stays **0** in both arms. Taking 0.3 GW out
  of the evening peak does not create a single scarcity hour in this recipe.

## §4 — λ, and what the floor does to price

Same instrument as caiso-122/123 (`scripts/probes/_caiso122_lambda_delta.py`,
CA demand-weighted):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| keeper (committed bytes) | 55.6158 | 37.5464 | 38.0221 |
| **arm A** (HEAD 4094bbe, no delta) | 55.7159 **(+0.180 %)** | 37.8424 **(+0.788 %)** | 38.4156 **(+1.035 %)** |
| **arm B** (+ floor) | 55.5416 | 37.5209 | 38.3439 |
| **delta B − A** | **−0.313 %** | **−0.849 %** | **−0.187 %** |

The floor *lowers* λ (cheap water displacing gas and imports in the belly
outweighs the evening loss), i.e. it moves λ marginally **toward** the actual in
2025 — small, and not a gate.

## §5 — recommended disposition (owner call)

1. **Do not promote.** The keeper is unchanged and nothing is armed.
2. **Do not revert the mechanism from the tree.** It is default-off, costs
   nothing when off (byte-identical: cache-key-neutral, `min_gen` unallocated,
   11 tests pin the inertness), and it is the only representation of a real
   physical obligation the LP currently lacks.
3. **The open question the numbers actually pose** is not the floor's level but
   its *inevitable side-effect*: with the monthly budget a hard cap, any belly
   lift is paid out of the peak. Both arms are ALSO 150–310 MW **too high
   overnight** (arm A hod 0: 3354 vs 3044 measured in 2025) — a pre-existing
   defect the floor cannot touch, and the only place the belly lift could have
   come from without cutting the peak. A caiso-125 lane should attack the
   overnight over-supply (the p95 ceiling does not bind overnight, and hydro
   carries no water-value/opportunity-cost term), then re-test the floor on top.
4. If a corrected shape gate is authorised (§2), the floor is re-scorable
   **from the committed bundles alone** — no re-solve — via
   `scripts/probes/_caiso124_minflow_ab.py`.

## §7 — TASK 2: the caiso-123 §5 residual — the `src/market_sim/` window is CLOSED BY MEASUREMENT

caiso-123 §5 left a second, smaller basis motion open (~−0.2…−0.5 pp λ,
CC_REGULAR ≈ −0.8 TWh / import ≈ +0.8 TWh common to both its arms) with three
candidate families: the `de62eb1..HEAD` 16-file `src/` window, earlier sessions'
container/partition state, and alternate-optimal vertex wander. **The src window
is now eliminated — by measurement, not inspection.** Every candidate below was
either executed at HEAD and compared, or shown unreachable on the CAISO keeper
path by reading the keeper's own recorded config:

| candidate | verdict | how it was closed |
|---|---|---|
| `model/lp/bounds.py` — ORDC step-width hourly shape | **INERT** | the static-shape branch evaluates to the identical array (`widths[np.newaxis, :]`); only a `(n_steps, T)` input takes the new path, which no CAISO config produces |
| `data/fleet/arrays.py` — `SUMMER_WEFOR_SHARE` / `SUMMER_CLASS_DERATE` re-home (miso-91) | **INERT** | the new home's literals verified identical (0.30; 0.10/0.10/0.125/0.125) — confirms caiso-123's read |
| `data/fleet/campd_bins.py` — `_plant_emission_rate_map` `iterrows`→`itertuples` | **INERT (measured)** | both extraction paths run at HEAD on both live artifacts: resulting dicts **equal** (130 and 0 pooled rows; all four columns int64/float64, so the dtype-upcast difference is exact) |
| `data/fleet/campd_bins.py` — `load_plant_tranche_config` `iterrows`→`itertuples` | **UNREACHED** | the keeper's `plant_tranche_config_path` is `null`; no on-disk artifact carries the loader's schema |
| `data/renewables.py` — `_miso_wind_reference_curtailment_rate` | **MISO-scoped** | by construction |
| `data/renewables.py` — `_add_proposed_capacity` `iterrows`→`itertuples` (the one hunk on a nominally ISO-generic wind/solar capacity path, which caiso-123 scoped as "MISO/forecast") | **CAISO-UNREACHED (measured)** | `_ISO_HOME_STATES` contains **only ERCOT**, so the function returns before the loop for CAISO: executed for CAISO solar and wind 2025 (the only backcast year past the operable vintage that can reach it at all), contribution **0.000 MW-months, 0 zones**. Its extraction was *also* measured identical on the ERCOT frame. |
| `pipeline/solve.py` — cross-year warm-start gate | **INERT for backcast** | `xyear_warmstart=None` (every backcast caller) takes the identical env-var branch; `replay_keeper` additionally pins `MARKET_SIM_WARMSTART_XYEAR=0`, so both arms and both caiso-123 arms are cold |
| `pipeline/backcast_config.py` | **ERCOT-only** | one line, `coal_econ_marginal_hr_bound=(iso.upper() == "ERCOT")` |
| `data/cache_control.py` (new, +83) | **DIAGNOSTIC-ONLY** | read-only footprint reporting at the between-years seam; `clear_all_caches` is never called implicitly (module contract + the only call site, `run_calibration_full.py:4540`, calls the three reporters) |
| `config/scenarios.py`, `model/reserves/spec.py`, `data/fuel/dual_fuel.py`, `config/fuel_trajectories.py`, `config/paths.py`, `config/constants.py`, `data/fuel/__init__.py`, `pipeline/flags.py`, `pipeline/timing.py`, `ensemble.py` | **new default-off / instrumentation / re-export** | caiso-123's `run_config` deep-diff already showed only new default-off fields (`dual_fuel_oil_daily_parity`, `nyiso_ordc_measured_step_span`) differ |

**What survives.** Only the two non-code candidates: the earlier sessions'
**container/partition state** (their arms are uncommitted and gone — notably the
`capacity-deliverability` clean partition, whose silent-degrade trap was
documented only on 2026-07-26, RESULTS-neiso65 §2) and **alternate-optimal vertex
wander**. Arm A additionally measures the `3253345..4094bbe` sub-window directly:
it is the same recipe caiso-123's arm C solved, so the two λ figures bound how
much of the residual (if any) is younger than caiso-123's own basis (§2).

**Recommendation carried forward** (unchanged from caiso-123 §7): extend the
`shared_inputs` content-hash block to the derived outage extracts and any other
derived-not-shared solve input, so a bundle pins the exact bytes it solved on.
Add the clean `capacity-deliverability` partition to that set — it is the one
input a bundle currently records nothing about, and it is the only surviving
code-external candidate that a future session could still close.

## §8 — incidental finding: a stale committed golden on main (NOT this session's)

`tests/test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`
FAILS at pristine HEAD, on the `availability` and `min_gen` hashes. Cause is
attributable: the golden was captured at `2f4cbc3` (2026-07-24) and
**`6a8f285`** ("neiso-65: adopt guard-corrected CAMPD extracts, all six ISOs +
layup companions") then changed `data/raw/campd-unit-outages.csv`, which sets
ERCOT `availability` — and `min_gen`, which is clipped to
`pmax × availability`. That is an owner-authorized data change, so the golden
needs re-capturing under it; doing so is not this lane's call (and must not be
done to silence a gate). Also pre-existing and unrelated:
`tests/test_hydro.py::TestCAISOHydroBudget::test_zones_resolve_to_caiso_topology`
(asserts the CAISO hydro zone set is ⊆ {NP15, ZP26, SP15}, but the topology now
carries LA_BASIN / SDGE / SP15_rest), plus the 8 known
`test_pipeline_facade_shims` / `test_flag_registry` failures.

Latent hazard noticed while wiring, **not touched**:
`src/market_sim/data/fleet/__init__.py` defines `Generator` **and**
`FleetArrays` **twice** (lines 157/254 and 496/591), the blocks differing only
in blank lines. The later definitions win at runtime. The new field was added to
both so they stay in sync, but the duplication should be collapsed by whoever
owns the fleet-package split (it is exactly the class of file damage rule 27
exists for).
