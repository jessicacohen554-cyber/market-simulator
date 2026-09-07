# PRECOMMIT — SPP-44: the CT / CC / ST gas split as a P1-native commitment-bridge question (`spp_gas_commitment_bridge`)

**Lane** SPP-44 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-44-gas-commitment-bridge-ljv87g` (stem `claude/spp-44-gas-commitment-bridge-r5tc`) ·
**Data profile** `spp` (full clone; every SPP CAMPD state extract on disk) · **Charter** plan §5 row SPP-44 /
§8 W4c (issued r#8); FINDING-spp-42 §7 (the object and the rule-19 enumeration); FINDING-spp-40 §5 R-6.

**Pushed before any solve.** Everything below is either a measured statistic already computed at zero LP
(the CAMPD derive, the on-recipe eligibility census, the footprint table), a declaration (the mechanism's
legs, its constants, its D-4 window), or a gate with its thresholds. No LP has been run in this lane. Nothing
here is revised after a solve; a miss of any declared condition is reported at full magnitude in the FINDING.

---

## 0. THE PIN, the control, the G-DRIFT audit

```
dcb609f4   origin/main at PRECOMMIT time (branch cut from it)
```

| precondition | check | result |
|---|---|---|
| SPP-42 landed — keeper-2 is the control | `keepers/SPP.json` → `2026-09-07-spp-2-crosswalk-hydro`, bundle `results/calibration/spp42_crosswalk_B` (+ `hourly/`), `git.sha 33034499` | **yes** |
| SPP-43 (keeper-3 on the screened input) | `keepers/SPP.json` unchanged since `28f4713c`; no `spp-43` FINDING or bundle at the pin | **NOT landed** — keeper-2 is the control; if it moves before the solve, an addendum re-pins (SPP-57 addendum A form) |
| SPP-41 (the EIA-930 `NG:` unit-slip screen at the `eia930.actuals` seam) | `3d5fe5ed`, PR #5497, landed AFTER keeper-2 was solved | **LANDED** — see G-DRIFT hunk 6, the one LIVE hunk |
| the derive's inputs | `data/raw/campd-unit-level/<ST>_{2023,2024,2025}.parquet` for the 14 SPP states — 13 present, **CO absent** (CO_2023–2025 not on disk; the derive skips them and says so) | usable; the CO gap is stated in §2.4 |

### 0.1 G-DRIFT (rule 29(b)) — keeper-2 `33034499` → `dcb609f4`

```
git diff --stat 33034499 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

| # | file | hunk | verdict for SPP | reason |
|---|---|---|---|---|
| 1 | `data/raw/_validation-source/caiso-supply-consistent-demand/*` | CAISO 2022 demand csv + provenance | **INERT** | CAISO-only artifact |
| 2 | `data/raw/_validation-source/actual_lmp_hourly_area_SPP.parquet` (+ README row) | SPP-57's residual-South price | **INERT** | read by no solve path and by no scorer (the C3 benchmark is `actual_lmp_hourly_zonal_SPP.parquet`, unchanged) |
| 3 | `config/constants.py` | `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"][2022]` | **INERT** | CAISO key |
| 4 | `config/fuel_trajectories.py` | `STATE_CARBON_PRICE_BY_ISO["CAISO"][2022]` | **INERT** | CAISO key; SPP has no carbon programme |
| 5 | `model/interchange/spec.py` | CAISO DSW depths + `IMPORT_TRANCHES_BY_YEAR["CAISO"][2022]` | **INERT** | CAISO keys; SPP's block byte-identical |
| 6 | `data/eia930/actuals.py` | **SPP-41**: `_screen_fuel_spike_columns` on the loader seam every reader shares — the LP's own delivered wind profile included | **LIVE for 2023 ONLY** | FINDING-spp-41 table 0b: exactly one INPUT series moves in 2021–2025 — SPP 2023 wind, h3907, +27 GWh on the clipped CF bound the LP consumes (−3,585.7 GWh on the MW series). 2024 / 2025 inputs byte-identical |
| 7 | `config/scenarios.py` | capx D76-ARM-B: `capacity_screen_peak_measured_hindcast` default flip + the `not hindcast` coercion | **INERT** | a backcast run is coerced back to the frozen declaration; FINDING-capx-d76-arm-b: all seven `*-plain-backcast` keys unmoved, SPP `989da50bbf0f99d8` |
| 8 | `results/cache.py` | +69 lines | **INERT** | prose only (the D76 cache-epoch ledger entry); zero code lines |
| 9 | `pipeline/backcast_config.py` | `_SPP_OFFER_CURVE` on the five coal keys | **INERT as drift** | keeper-2's own recorded dirty change (`run_config.json` `changed_files`); the keeper solved WITH it |

**Consequence.** Eight hunks INERT; hunk 6 is LIVE and — because §2.5 names **2023** as the screen year — it is
live for exactly the year the screen needs. Form 4 is therefore **void for 2023 and valid for 2024 / 2025**. Rule
29(b)'s LIVE-hunk clause fires as written: **one control solve is earned, for 2023 only** — keeper-2's recipe,
flag-free, at HEAD (`results/calibration/_spp44_control_2023`, TEMPORARY, deleted before the PR, rule 29(c)). It
is exactly the 2023 leg of SPP-43's object and is NOT registered by this lane. For 2024 / 2025 (the full span, if
reached) keeper-2's committed `hourly/` sidecars remain the control.

---

## 1. Rule 19 `[R-ONE-MECH]` — what floors SPP's gas fleet today: NOTHING

Read from keeper-2's committed `legitimacy_diagnostics.json` D-2 rows (2023 / 2024 / 2025): the only forced
energy on the SPP fleet is `nuclear_mustrun` (100 % of nuclear, exempt) and `chp_steam` on the three CHP classes
(1.8 / 3.9 / 0.9 % of CC_CHP, 1.1 / 3.4 / 0.9 % of CT_CHP, 5.2 / 4.2 / — % of ST_CHP; all exempt). **CC_REGULAR,
ST_GAS and CT_PEAKER carry 0.0 % forced energy**: no reliability floor is registered for SPP
(`reliability_floor_overrides` none; the per-ISO floor CSV registry has no SPP entry), no bridge, no drag, no
must-run per plant, no posture; every offer band is 1.0 (`_SPP_OFFER_CURVE` identity on every class;
`authorized_price_tuning` NONE). CT_PEAKER clears purely on SRMC. So this lane adds a mechanism to a class that
carries none — it stacks on nothing, and there is nothing to reconcile or replace (the NYISO bridge's
`NYISO_PEAK_WINDOW_FLOORS_OFF` companion has no SPP analogue because SPP has no windowed limbs).

**The object** (FINDING-spp-42 §3.1 / §7): C1-2024 CC_REGULAR −8.60 TWh (volume band ±8) and CT_PEAKER +9.94 TWh
(+3.4 pp, band ±3.0); the same sign pattern in 2023 within band (CT +6.14 / CC −4.62 / ST_GAS −7.78) and in 2025
(preliminary 923, unscored). Rule 29: the screen is NEVER graded on those rows (§4).

---

## 2. MEASURE FIRST (zero-LP) — the parameters, the eligibility census, the footprint

### 2.1 The derive: `derive_campd_gas_commitment_params.py --iso SPP --years 2023 2024 2025 --detail` (+ `--plant-basis`)

The WP-3 loading-when-on construction verbatim (HSL = p99.5 of pooled gross load; online ≥ max(`_ONLINE_MW`,
0.05 × HSL); LSL = p5 of online-hour load; class value = HSL-weighted p50 across units; runs computed within each
year). Artifacts: `data/raw/_processed-legacy/campd_gas_commitment_params_SPP.csv` (+ `_units.csv`, 114 units) and
`campd_gas_commitment_params_plant_SPP.csv` (+ `_units.csv`, 45 facilities).

| basis | class | n | capacity MW | **min_load_frac** (p25 / p75) | runs | run h p25 / p50 / p75 | cap-wtd p25 / p50 / p75 |
|---|---|---:|---:|---|---:|---|---|
| per-UNIT | CC_REGULAR | 49 units | 10,654 | **0.440** (0.327 / 0.523) | 15,090 | 10 / 16 / 39 | 14 / 20 / 46 |
| per-UNIT | ST_GAS | 65 units | 12,229 | **0.266** (0.215 / 0.361) | 7,321 | 8 / 14 / 73 | 10 / 49 / 134 |
| per-PLANT | CC_REGULAR | 19 plants | 10,403 | **0.209** (0.141 / 0.320) | 5,290 | 12 / 19 / 48 | **15** / 20 / 65 |
| per-PLANT | ST_GAS | 26 plants | 11,373 | **0.090** (0.076 / 0.139) | 2,931 | 7 / 14 / 93 | **5** / 14 / 128 |

One mixed-class facility dropped as unattributable at CAMPD facility level (2963). Cross-check against the two
published identifications: SPP's per-unit CC 0.440 sits below ERCOT's published LSL/HSL 0.574 and NYISO's
reconstructed 0.523 — SPP's combined-cycle fleet turns down deeper per train, and its p75 (0.523) is NYISO's p50.

### 2.2 BASIS ADJUDICATION — declared now, before any floor is written

The consumer is the shared detector `caiso_ra_mustoffer_min_gen`, which floors **`min_load_frac × PLANT pmax`**,
clipped to the plant's base (committed) tranche capacity. FINDING-caiso135 §A / §R adjudicated that a floor
multiplied by PLANT capacity must carry the PLANT statistic (the facility's minimum stable CONFIGURATION over its
full capability), not one turbine's turndown — on CAISO the two differ ~2× (0.57 unit vs 0.29 plant) and the
per-unit value applied to plant capacity "asserts a minimum CAISO's own plants sit below in ~2 of every 5 online
hours". SPP's fleet is the same shape, more so: its ST_GAS class is legacy multi-unit stations (2956 Northeastern
1,521 MW, 6193 1,018 MW, 2952 989 MW) that run one boiler at a time, so the plant-basis 0.090 against the per-unit
0.266 is a 3× gap. **The floor level is therefore the PLANT-basis statistic**: `gas_cc` **0.209**, `gas_st`
**0.090**. The per-unit values are reported beside them and are not used. This is the basis the LP row (a per-plant
tranche stack) is on; rule 14 `[R-ACCURATE]` — the aligned measurement, not the larger number.

**Minimum run duration** — the same basis, the LOW order statistic: the detector's min-run leg extends a PLANT
row's detected P0 run, so the plant-summed run distribution is the population, and an observed run bounds a
minimum-run CONSTRAINT from above (the derive's own docstring; the nyiso-90 CT leg used p25 on the same reasoning).
Declared: `gas_cc` **15 h**, `gas_st` **5 h** — the capacity-weighted p25 of the plant-basis run distribution.
(NYISO's keeper carries the per-unit p50s, 21 / 13 h; SPP does NOT inherit them — rule 25.)

### 2.3 The rule-18 eligibility census on keeper-2's recipe (`docs/handoffs/spp44/census_eligibility.py`)

`run_year(fleet_only=True)` per year; every gas LP row resolved through `_ra_bridge_unit_params` exactly as the
detector will resolve it. Identical in all three years:

| class | fuel | LP rows | plants | MW | **eligible rows** | eligible (base-tranche) MW | resolved min-down (h) | resolved startup ($/MW) | verdict |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| CC_REGULAR | gas_cc | 85 | 23 | 10,048 | **23** (one committed tranche per plant) | **3,466** | {4, 6} | 50 | ELIGIBLE, physical + economic legs (min-down ≥ 4 h) |
| ST_GAS | gas_st | 124 | 31 | 10,281 | **31** | **2,026** | {8, 12} | 35 | ELIGIBLE, physical + economic legs |
| CT_PEAKER | gas_ct | 383–389 | 123–125 | 11,708–11,755 | **0** | 0 | {1} | 20 | **FAILS ON PHYSICS**: a 1 h min-down makes the physical bridge unreachable and fails `RA_BRIDGE_ECON_MIN_DOWN_HOURS` (4 h) — never named, never bridged |
| CC_CHP / CT_CHP / ST_CHP | — | 4 / 23–31 / 14 | 1 / 7–9 / 9 | 271 / 210–240 / 113 | 0 | 0 | — | — | excluded by the detector's cogen rule (steam host) |

The econ/peak tranches carry `startup_per_mw = 0` and are rejected by the detector (never floored above the
plant's minimum stable load). **The bridge is not inert by construction on SPP** — the PJM kill (pjm-142: bins with
no commitment physics) does not recur; every committed tranche carries the class startup and a class min-down.

Per-plant floor levels (2024 fleet, `spp44/floor_levels_2024.csv`): CC 23 plants, 10,482 MW plant / 3,596 MW base
tranche; floor Σ **2,084 MW** on the plant basis (the base-tranche cap binds at 5 plants) vs 3,303 MW on the
per-unit basis (cap binds at 14). ST_GAS 31 eligible rows at 31 plant codes (the per-plant table lists 30 because 2963 carries both CC and ST
tranches and is tabled once, under CC), 9,846 / 1,895 MW;
floor Σ **884 MW** plant basis (cap binds at 1) vs 1,698 unit basis (cap binds at 15). Eligible plants with NO
CAMPD series, which take the class scalar: 1270, 1317, 1330, 2963, 3602, 3604, 7546, 56565 (two of them material —
2963 Northeastern CC 878 MW and 56565 J Lamar Stall 511 MW; the rest ≤ 88 MW).

### 2.4 Stated limits of the measurement (rule 14, misalignment declared)

- The CO extracts are absent from the corpus (`CO_2023-2025.parquet`), so any SPP CC/ST plant in Colorado is
  unmeasured; the fleet's CO gas is small (the SPP-30 state census) and no eligible plant is lost to it beyond
  the eight above.
- The plant-basis facility is CAMPD's `facilityId`, which is the EIA plant code; a campus split across two plant
  codes measures as two plants.

### 2.5 The FOOTPRINT by year → the SCREEN YEAR (`docs/handoffs/spp44/footprint.py`)

Construction (declared here, ran once): for the 45 eligible plants with a CAMPD series, the plant's hourly
ONLINE state is its summed gross load ≥ max(`_ONLINE_MW`, 0.05 × HSL_plant) — the derive's own threshold. The
measured committed-state floor F(t) = Σ_online plants LSL_plant (plant-basis p5-of-online MW); the model's economic
dispatch D(t) = keeper-2's committed `class_hourly_<year>` P1 series. **Footprint = Σ_t max(0, F − D)** — the volume
by which the real committed state exceeds the keeper's dispatch, i.e. the room a minimum-load hold has to act in.
(The bridge anchors on the model's OWN P0 pattern, so this is the measured-conduct proxy, not the floor it writes.)

| year | class | CAMPD plants | plant-online h | F mean MW | D mean MW | **footprint GWh** | hours F > D | CAMPD runs | gaps < min-down (n / h) | gaps min-down…24 h (n / h) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2023 | CC_REGULAR | 19 | 109,875 | 1,918 | 4,729 | 657 | 1,111 | 1,904 | 139 / 299 | 1,274 / 12,266 |
| 2023 | ST_GAS | 26 | 113,665 | 835 | 859 | **3,551** | 5,914 | 965 | 206 / 695 | 307 / 4,278 |
| 2024 | CC_REGULAR | 19 | 109,766 | 1,882 | 4,299 | 1,000 | 1,440 | 1,579 | 103 / 222 | 1,074 / 10,229 |
| 2024 | ST_GAS | 26 | 120,537 | 886 | 1,711 | 545 | 1,427 | 973 | 169 / 587 | 300 / 4,321 |
| 2025 | CC_REGULAR | 19 | 102,811 | 1,808 | 3,718 | 1,209 | 1,611 | 1,793 | 83 / 173 | 1,187 / 11,692 |
| 2025 | ST_GAS | 26 | 115,556 | 871 | 1,122 | 1,448 | 4,380 | 988 | 148 / 523 | 306 / 4,350 |

**Footprint by year: 2023 = 4,209 GWh · 2024 = 1,545 · 2025 = 2,656 → SCREEN YEAR = 2023.** Named on the
footprint, not on the residual (2023 is the year whose C1 gas rows are all IN band; the year with the biggest gas
residual is 2024, which is NOT chosen). 2023's footprint is carried by ST_GAS: the keeper runs SPP's gas steam
at zero in 5,914 hours where the real fleet holds ~800 MW online at minimum load.

### 2.6 DOF ledger entries this lane adds (rule 21) — FOUR MEASURED, ZERO TUNED

| parameter | value | identification source | basis |
|---|---|---|---|
| `SPP_GAS_BRIDGE_MIN_LOAD_FRAC["gas_cc"]` | 0.209 | `campd_gas_commitment_params_plant_SPP.csv` (cap-wtd p50 of plant lsl_frac) | MEASURED (rule 23) |
| `SPP_GAS_BRIDGE_MIN_LOAD_FRAC["gas_st"]` | 0.090 | same | MEASURED |
| `SPP_GAS_BRIDGE_MIN_RUN_HOURS["gas_cc"]` | 15 | same artifact, `run_hours_p25_capwtd` | MEASURED |
| `SPP_GAS_BRIDGE_MIN_RUN_HOURS["gas_st"]` | 5 | same | MEASURED |

The startup costs ($50 / $35 per MW) and min-down hours (4–12 h) the legs gate on are the registered class
physics already on every SPP committed tranche (NREL/SR-5500-55433 via `COMMITMENT_PARAMS_BY_FUEL`), not new
entries. The inherited `wefor_multiplier` 0.7 residual entry carries over unchanged. Nothing is swept.

---

## 3. THE MECHANISM, as declared (ONE new field; nothing else tunable)

`ScenarioConfig.spp_gas_commitment_bridge: bool = False` — registered in `_CACHE_KEY_OPTIONAL_FIELDS` with
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["spp_gas_commitment_bridge"] = "False"` in the same commit, so every committed
key is unmoved (proof: the seven keepers' `cache_key()` before / after, §5). TIER_TAGS 1 (a structural flag). CLI
`--spp-gas-commitment-bridge` on both runners; threaded through `run_config.json`.

Branch: `pipeline.commitment.build_spp_gas_bridge_p1_prep(config, iso, fleet, fleet_arrays, mc_base)` beside the
NYISO builder — returns `None` unless `iso == "SPP"` and the flag is on (every other ISO byte-identical); wired into
all three orchestrators' `p1_fleet_prep` chains (the `test_p1_prep_wiring` roster). It runs the SHARED detector
once per eligible fuel (`("gas_cc",)`, `("gas_st",)`; composed by maximum over disjoint rows) with:

| leg | setting | physics |
|---|---|---|
| physical restart bar | always | a P0 gap shorter than the unit's min-down (CC 4–6 h, ST 8–12 h) is floored at min-load |
| economic restart inequality | on, `max_econ_gap_hours = DA_COMMITMENT_HORIZON_HOURS` (24) | a gap ≥ min-down and ≤ one DA operating day is floored when re-paying the published startup exceeds (MC − LMP_P0) × frac × gap |
| minimum-run extension | on, `min_run_hours` = the measured 15 h / 5 h per fuel (a `(n_gen,)` vector; 0 on every ineligible row) | a P0 run shorter than the plant's min-run is extended, floored at min-load; extended blocks define the pattern the gap legs scan (never double-floored) |
| commitment-real run screen | on (`startup_aware`) | a P0 run anchors any leg only if its P0 margin per MW repays the unit's own startup — the nyiso-200 leg, zero parameters |
| online-hours state floor | **off** | not chartered; no SPP evidence for it |

Level = `min(frac × plant pmax, base-tranche pmax) × availability`. D-2 id: NEW `MECH_SPP_GAS_COMMITMENT_BRIDGE`
(24), name `spp_gas_commitment_bridge`, ablation entry `{"spp_gas_commitment_bridge": False}`, in `BRIDGE_MECHS`.
Rule 18: eligibility is `_ra_bridge_unit_params` (min-down, startup) — no class tuple anywhere in the branch; the
fuel-type filter selects the population the measured constants describe, the physics gate decides.

**Rule 17 `[R-FLOOR-WINDOW]` declaration** (the `D4_WINDOWS` entry, both classes, `(0, 24)` by driver):
- DRIVER — unit-commitment physics only: minimum run, minimum down, the restart inequality priced at the model's
  own P0 duals; level = the measured plant-basis minimum stable load.
- WINDOW — self-windowing: the floor exists only inside an idle gap between two P0-detected runs of the same plant
  (< min-down, or ≤ 24 h on restart economics) or in the hours after a P0 run-start inside the plant's min-run. No
  clock-hour rule; no hour of day is declared off. The measured record supports an all-hours window: SPP's
  eligible plants show 1,274 / 1,074 / 1,187 CC gaps and 307 / 300 / 306 ST gaps of min-down…24 h per year (§2.5).
- FORWARD STORY — regenerates in any forecast year from that year's own P0 pattern plus four measured constants
  that re-derive only on a CAMPD vintage change (rules 13 / 23).

---

## 4. THE SCREEN (rule 29(a)) — 2023, one invocation, and the STOP gate

```
uv run python scripts/run_calibration_full.py --iso SPP --year 2023 \
    --out-dir results/calibration/_spp44_control_2023 --hydro-backfill-year 2024 --hydro-eia930-monthly   # control
uv run python scripts/run_calibration_full.py --iso SPP --year 2023 --spp-gas-commitment-bridge \
    --out-dir results/calibration/_spp44_screen_2023 --hydro-backfill-year 2024 --hydro-eia930-monthly    # arm
```

Keeper-2's recipe (FINDING-spp-42 §3 command) plus the one flag; sequential; no other per-plant solve runs in this
container (rule 12; the desk's r#8 note on concurrent SPP solves applies across containers, not within this one).
Both bundles are TEMPORARY and deleted before the PR (rule 29(c)); every number cited from them lives in the
FINDING. Grader: `docs/handoffs/spp44/grade_screen.py`, written before the solve, reading only the two bundles'
sidecars (`hourly/class_hourly_2023`, `hourly/system_2023`, `floors/2023_P1.npz`), the CAMPD online matrix
`spp44/campd_online_2023.parquet`, and the committed bench part `bench/SPP/2023.json.gz`.

**STOP gate — structural, kill-only, thresholds fixed now. It never reads C1's gas rows, C3a or C3b.**

| leg | quantity (2023, arm vs control) | STOP if |
|---|---|---|
| (i) window agreement | over plants with a CAMPD series: the floor-MWh-weighted share of bridge-floored plant-hours (`mechanism == 24`, `min_gen > 0`) in which CAMPD has THAT plant ONLINE, per class. Reported beside it: the class's unconditional 2023 online fraction (CC 0.660, ST 0.499 from §2.5) and the lift over it | agreement < max(0.60, unconditional + 0.10) for either class — i.e. CC < **0.76** or ST_GAS < **0.60**: a floor that lands on plants CAMPD has online no better than chance is not anchored to real commitment |
| (ii) direction and magnitude | V = the bridge's floor volume (TWh, Σ `min_gen` over bridge-tagged plant-hours); ΔE = arm − control P1 class energy from `class_hourly` | ΔE(CC_REGULAR + ST_GAS) ≤ 0, OR outside **[0.25 V, 2.0 V]** (the response must be the order of the floor's own arithmetic); OR ΔE(CT_PEAKER) > **+0.05 TWh** (the peaker class moving the WRONG way). CT falling by less than 0.05 TWh is REPORTED, not a kill: the gap floor displaces whatever is marginal in the gap hours, and whether that is CT is a finding |
| (iii) C8 forced share | `legitimacy_diagnostics.py --bundle … --iso SPP --years 2023 --only D1 D2 D4`: `share_of_class` for CC_REGULAR and ST_GAS (both material, ≥ 2 % of load); D-4 off-window share | share > **0.30** on either class (the rule-20 merchant cap, applied as the charter wrote it — a screen kill, not the conditional-pass escalation); D-4 off-window > 0.05 |
| (iv) no non-target load-bearing flip | C1 rows for the NON-target classes (COAL_PRB, COAL_LIGNITE, COAL_BIT, CC_CHP, CT_CHP, ST_CHP) on the rubric's own band (volume ±min(max(2 % load, 3 % gen), 8 TWh) AND share ±3.0 pp); C2 coal family (= its per-class roll-up); C4 gas and coal hourly r (Pearson, model family hourly vs EIA-930 SWPP fuel-type hourly — the grader must first REPRODUCE the keeper's committed 2023 r of 0.967 / 0.950 from the same sidecars to within 0.005, else leg (iv)'s C4 limb is VOID and said so) | any of those rows in band in the control and out of band in the arm; C4 gas or coal r below the rubric floor having been above it |

Reported beside the legs, never gated: the C1 gas rows (CC / CT / ST_GAS TWh and pp), load-weighted price vs RT /
DA, hours > $200, negative-price hours, unserved energy (control: 0 in 2023), the per-leg census the branch logs
(runs detected / dropped as phantom; unit-hours floored per fuel; floored-segment length buckets), and the 2023
control's own differences from keeper-2's committed 2023 (the SPP-41 seam's measured LP effect, reported for
SPP-43's benefit).

**A kill on any leg is this session's result; the full span is not spent.** A pass promotes nothing (rule 29).

---

## 5. If the screen clears — the full span, LOYO, registration

- `--year 2023 2024 2025 --spp-gas-commitment-bridge` → `results/calibration/spp44_bridge_B`, one invocation,
  years sequential (rule 12). Scored on the rubric; registered as a **CANDIDATE** (rule 15), never promoted here
  (P15 is the desk's). Differenced against keeper-2 for 2024 / 2025 (form 4 valid — the seam is inert there) and
  against the 2023 control.
- **LOYO (rule 22)** for a zero-tuned-scalar mechanism is parameter stability, not a fit: the derive re-run with
  each year dropped (`--years` 2024 2025 / 2023 2025 / 2023 2024) and the four constants reported per fold,
  plus legs (ii)–(iv) of the gate on each of the three years.
- Gates before push: `check_mechanism_matrix.py` (row + 7 cells) 0; `pytest tests/unit/config tests/unit/pipeline
  tests/unit/model -q`; `tests/regression/test_persisted_identity.py`; `solve_surface_register.py --diff` 0 moved
  for the six; `check_cache_key_registration.py --base`; `audit_keepers --check`; parity. The seven keepers'
  `cache_key()` before the field: ERCOT `462eb83763c2eb34`, CAISO `014b4cc10d4ab6da`, PJM `0b5867afa886b9ad`, MISO
  `f130587822fbf565`, NYISO `95d4d8d167373eb7`, NEISO `38b460ca08f63a01`, SPP `392dcca76cd6156f` — the FINDING
  prints the same seven after.
- Matrix: NEW row `spp_gas_commitment_bridge` in `mechanism-matrix.js` (cross-referenced to the shared
  `gas_commitment_bridge` family row, which stays as it is) + one cell line in EVERY shard (`.` for the six —
  ISO-exclusive elsewhere by the shard header's own rule (a); SPP `U` → the verdict); §5.7 entry; plan §5 / §9 rows.

## 6. What is not a rejection condition, and what is not touched

No comparison of a modelled price with a measured one; no C1 gas row; no C3a / C3b. No band moves (rule 25 — a
bridge is a floor, never a multiplier), no constant is re-cut after a solve, no second arm without a new
PRECOMMIT. Not touched: any other ISO's branch, shard cells beyond the one `.` line each, the NYISO bridge and its
fields, `keepers/SPP.json`, `reliability_floor_overrides`, `calibration-complete.json`, `frontend/data/forecast/`.
