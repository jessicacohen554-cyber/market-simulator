# PRECOMMIT — NWPP-42: C4 coal, attacked at the measured heat rate

**Lane** NWPP-42 · **Base** `4583e70b864a7d5c99a206b06eddf3c36af495bf` (origin/main
2026-09-19, contains `2ec09663` so every shard emits `marginal_emission_rate`) ·
**Branch** `claude/nwpp-42-coal-shape-scop49` · **DATA PROFILE** nwpp

**Control** the incumbent keeper `2026-09-19-nwpp41-coal-taxonomy-own`, bundle
`results/calibration/nwpp41_span_A`, differenced at rule 29 `[R-SCREEN]` form 4.
**No control solve.** Years 2023 · 2024 · 2025 — the whole of NWPP's registered
year set (no held-out year, no stamped touchpoint bundle exists).

Everything below was measured **before any LP was spent**, and every number this
lane will ever cite from phase 0 is here.

---

## §0 What this lane does, in one paragraph

C4 coal FAILs in all three years on **both** legs (`r` 0.539 / 0.546 / 0.502
against a 0.70 floor; NRMSE 0.301 / 0.397 / 0.432 against a 0.30 ceiling). Phase 0
established that the model's coal fleet is priced off an **eGRID plant-average
ANNUAL heat rate that is above the plant's own metered operating rate at every
one of the 12 CEMS-covered NWPP coal plants**, capacity-weighted 11.868 → 11.066
MMBtu/MWh (−6.8 %). The arm derives NWPP's own measured artifact and applies it:
**one new field, `measured_coal_heat_rates`, armed for NWPP alone.** Rule 14
`[R-ACCURATE]` is the basis. Zero free parameters. The prediction, registered
here and not adjustable later, is that **volume improves materially and C4 does
not necessarily pass** — see §6.

---

## §1 The fork the prompt asked me to decide: I took **(b)**, and (a)'s premise is false

The brief offered **(a)** derive `bin_assignments_NWPP.csv` and re-examine the
tranche split, or **(b)** establish why (a) is out of reach and pick another
lever. I ran (a) to the end and it does not lead where the brief expected. Three
findings, each checkable:

1. **NWPP's absence from `CAMPD_BINNING_ISOS` is an OWNER RULING, not a gap.**
   `config/capacity_market.py` carries it verbatim — owner card **N8**, NWPP desk
   sitting #4, 2026-09-14: *"LEGACY HEAT-RATE BINS FOR THE FIRST KEEPER; CAMPD
   PER-PLANT AS A LEVER"* — with gate **G21** naming the reason (939 plants × 5
   zones is the largest per-plant LP the repo would hold; CEMS reaches 30.98 % of
   footprint nameplate). A keeper lane does not overturn that.
2. **NWPP already has the tranche structure (a) was meant to create.** The
   keeper's own `hourly/class_band_hourly_<year>.parquet` carries the full five
   bands — `mustrun` / `committed` / `econlo` / `econhi` / `peak` — on the
   LEGACY path. `thermal_tranches_NWPP.csv` is committed and CEMS committed-share
   coverage is 85.9 % of COAL capacity. The bin file would change which plant
   carries which share; it would not create a split that is missing.
3. **I derived it anyway** (`scripts/export_iso_bin_assignments.py --iso NWPP`,
   105 rows) because it is the crosswalk `derive_campd_marginal_hr.py` keys on,
   and it paid for itself by surfacing the converted-site split in §3.4.
   **It is deliberately NOT committed**: `ct_intermediate_plants` /
   `st_gas_intermediate_plants` read `bin_assignments_<ISO>.csv`, and
   `thermal_tranches_NWPP.csv` exists, so committing it would put a file on a
   solve-adjacent path that this lane did not screen. Both consumers are
   default-off in the keeper (`ct_intermediate_split` false,
   `st_gas_intermediate` false) so it is inert today — but "inert today" is not
   "screened". Recovery is one command, printed above.

**Off-queue, and why.** The NWPP lever queue (`docs/mechanism-testing-matrix.md`
§5.9, items NWPP-55…59) is TTC derive, priced seams, WRAP adequacy, zone
refinement and the retirement sector gate. It was written before any NWPP solve
existed and **contains no C4 lever at all**. The cell this lane moves,
`measured_coal_heat_rates`, does not exist at the base sha; the sibling cell
`measured_ct_heat_rates` reads `U` for NWPP. Nothing adjudicated `R`/`I`/`G` is
re-tested (rule 28 DO-NOT-REDO).

---

## §2 What C4 actually fails on, decomposed (zero LP)

C4 scores two families, gas and coal, on fleet hourly r/NRMSE against CEMS.

| year | **gas** r / NRMSE | **coal** r / NRMSE | coal model / bench TWh |
|---|---|---|---|
| 2023 | 0.746 / 0.200 **PASS** | 0.539 / 0.301 **FAIL** | 39.61 / 42.27 |
| 2024 | 0.829 / 0.149 **PASS** | 0.546 / 0.397 **FAIL** | 27.01 / 38.30 |
| 2025 | 0.830 / 0.169 **PASS** | 0.502 / 0.432 **FAIL** | 27.21 / 42.26 |

Reconstructed from the committed payload + benchmark over the 13 CEMS coal
plants (r 0.530 / 0.619 / 0.540 — the same object), the loss decomposes:

| year | overall r | monthly r | within-month r | within-day r | daily-mean r |
|---|---|---|---|---|---|
| 2023 | 0.530 | 0.607 | 0.370 | 0.184 | 0.563 |
| 2024 | 0.619 | 0.784 | 0.262 | 0.231 | 0.674 |
| 2025 | 0.540 | 0.702 | 0.308 | 0.333 | 0.614 |

**Shape-only** (each series normalised to its own annual mean, so level and the
scorer's flat fill drop out):

| year | coal hod peak/trough act → mdl | gas hod peak/trough act → mdl | coal monthly-shape r | gas monthly-shape r |
|---|---|---|---|---|
| 2023 | 1.183 → **1.018** | 1.366 → 1.259 | 0.607 | 0.713 |
| 2024 | 1.237 → **1.026** | 1.425 → 1.225 | 0.784 | 0.927 |
| 2025 | 1.311 → **1.022** | 1.519 → 1.269 | 0.702 | 0.940 |

**Gas reaches 83–92 % of its measured diurnal amplitude. Coal reaches 10–14 %.**
That asymmetry — same LP, same hours, same price series — is the defect.

**NRMSE is mostly level.** Rescaling the model to the actual mean leaves
0.312 / 0.293 / 0.240, against 0.338 / 0.430 / 0.475 unrescaled. So the level
bias (−20.5 / −35.9 / −41.9 % on the CEMS subset) carries most of 2024–25's
NRMSE, and **a residual shape term of ~0.24–0.31 survives a perfect level fix.**

**The class the gap lives in is COAL_BIT**, and it is not a persistent defect —
it appears between 2023 and 2024 (model vs EIA-923 `classFull`, TWh):

| class | 2023 mdl/act | 2024 mdl/act | 2025 mdl/act |
|---|---|---|---|
| COAL_BIT | 14.98 / 13.95 **+7.4 %** | 7.45 / 12.81 **−41.8 %** | 6.71 / 18.18 **−63.1 %** |
| COAL_PRB | 24.20 / 25.38 −4.6 % | 19.32 / 21.01 −8.0 % | 20.43 / 23.61 −13.4 % |

COAL_BIT is **77 % of the 2025 coal deficit**.

---

## §3 Root cause, measured at four levels

### 3.1 The merit order inverts between 2023 and 2024, and it is gas that moves

Capacity-weighted assembled marginal cost, from a `fleet_only` rebuild on the
keeper's own recipe (`scripts/probes/_nwpp42_offer_stack_phase0.py`):

| year | CC_REGULAR committed | CC_REGULAR econ | COAL committed | COAL econ | COAL mustrun |
|---|---|---|---|---|---|
| 2023 | 47.26 | 56.13 | 33.56 | 37.37 | 4.50 |
| 2024 | **22.31** | **23.99** | 35.52 | 42.60 | 4.50 |
| 2025 | **26.27** | **27.56** | 35.92 | 43.77 | 4.50 |

Coal's own offer is flat across the span. **Gas collapses by half.** In 2023 coal
sits $14–19/MWh *below* gas CC and COAL_BIT is right; in 2024–25 it sits
$9–16/MWh *above* and COAL_BIT collapses.

### 3.2 The fuel prices driving that are MEASURED and are not the defect

Implied delivered fuel, backed out of the assembled `mc` array
(`(mc − vom)/heat_rate`, carbon price 0 in backcast), $/MMBtu:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model gas (CC/CT/ST, cap-wtd) | 6.65 | 2.81 | 3.30 |
| model coal | 2.60 | 2.88 | 2.94 |

Against EIA's own delivered-gas-to-electric-power state series: 2023 WA 5.43 /
OR 4.05 / ID 4.04 / UT 7.82 / WY 6.68 / NV 6.96; 2024 WA 3.36 / OR 1.81 / ID 2.26
/ MT 2.18. **The model's gas price is inside the measured range in every year** —
the 2023 spike is real Western delivered gas, not an artifact. So the merit-order
inversion is REAL in the fuel data and **is not the thing to fix**.

*(Reported, not this lane's: the state series has **zero 2025 months for WA and
OR**, the two largest NWPP gas-CC states. Whatever the model falls back to there
is unaudited. Routed, not absorbed.)*

### 3.3 The coal HEAT RATE is the defect — measured, one-directional, every plant

`scripts/data/derive_campd_coal_heat_rates.py --iso NWPP` over NWPP's own CAMPD
unit-level record (ID/MT/NV/OR/UT/WA/WY, 2023-2025): **12 of 17 plants, 7,956 of
8,104 MW = 98.2 % of COAL capacity.** MMBtu per **net** MWh:

| plant | MW | model (eGRID) | measured | ratio |
|---|---|---|---|---|
| Colstrip | 1480 | 10.5702 | 10.3342 | 1.023 |
| **Hunter** | 1363 | **13.3303** | **10.9688** | **1.215** |
| Jim Bridger | 1049 | 11.2457 | 11.1511 | 1.009 |
| Huntington | 909 | 11.6307 | 11.0325 | 1.054 |
| Dave Johnston | 745 | 12.2829 | 11.6458 | 1.055 |
| Centralia | 670 | 11.4151 | 11.1734 | 1.022 |
| Bonanza | 458 | 11.9190 | 10.9071 | 1.093 |
| Naughton | 357 | 11.6091 | 11.5094 | 1.009 |
| Wyodak | 332 | 13.1065 | 12.0467 | 1.088 |
| **North Valmy** | 268 | **13.1105** | **11.3634** | **1.154** |
| TS Power Plant | 218 | 10.4648 | 10.2183 | 1.024 |
| Hardin | 107 | 15.8428 | 14.3005 | 1.108 |

**Capacity-weighted 11.868 → 11.066 (−6.8 %); generation-weighted 11.726 → 11.025
(−6.0 %). Every single covered plant is over-stated; not one is under-stated.**
Stable across years (Hunter 10.189 / 10.258 / 10.173 gross — a 0.8 % spread), so
it is a machine characteristic, not a year artifact.

**Why eGRID is wrong here** — the same argument `measured_ct_heat_rates`
(nyiso-89) already makes for peakers, transposed: eGRID's plant rate is
`PLHTIAN / PLNGENAN`, an **annual** average, so it folds startup fuel, shutdown
tails and the offline hours' fuel into the number that sets the plant's offer;
and its **level moves with the plant's capacity factor in the vintage year**, so
a low-CF vintage inflates the rate, the model prices the plant out of merit, and
its modelled CF falls further.

**The signature that makes this structural rather than residual-helpful, and I
did not select it** — the derive is non-selective by construction, over every
coal plant the artifact covers: the correction is **near-zero exactly at the
plants the model already dispatches correctly** (Colstrip, measured diurnal
peak/trough 1.07, model 1.00, moves 2.3 %) and **largest at Hunter**, the 1,363 MW
plant whose measured peak/trough is 1.62 against the model's 1.00.

Per-plant measured vs model diurnal peak/trough, 2025: Huntington 1.77/1.00 ·
Naughton 1.70/1.15 · Hunter 1.62/1.00 · TS Power 1.56/1.05 · Jim Bridger 1.55/1.03
· North Valmy 1.24/1.04 · Wyodak 1.21/1.07 · Dave Johnston 1.14/1.01 ·
Colstrip 1.07/1.00.

### 3.4 What phase 0 RULED OUT, recorded so no later lane re-spends it

- **Rule 17 `[R-FLOOR-WINDOW]` off-window binding: NOT the defect.** Model coal
  energy in hours CEMS says the plant is offline is **0.337 / 0.169 / 0.312 TWh**
  — about 1 % of coal. The historic CAMPD outage overlay already windows the
  must-run floor. I was wrong to suspect it and the measurement says so.
- **`coal_committed_takeorpay_regulated` / `_all`: REFUSED, not untested.** It
  would raise volume, but the repo's own record
  (`coal_committed_takeorpay_sunk_fixed`'s docstring) is that the unconditional
  committed-band discount **flattens diurnal shape** — MISO D-1 off-peak
  `cv_ratio` collapsed 0.88/1.04/0.47 → 0.45/0.44/0.36 — and is a rule-17
  no-window mechanism. NWPP's failing criterion is shape. Taking it would buy
  NRMSE by spending `r`.
- **`coal_econ_marginal_hr_bound`: INERT for NWPP by construction.** It clamps
  econ bands **UP** to the measured marginal HR. NWPP's bands are the rule-25
  identity (1.000) and the measured marginal is ~0.89, so `max(1.000, 0.89)` is a
  no-op. Recorded so it is not tried.
- **Converted coal sites are a real EIA-860 fact, not a taxonomy bug.** Jim
  Bridger splits COAL 1,049 MW / ST_GAS 1,070 MW, Naughton 357/247, North Valmy
  268/254 — 1,571 MW of gas-converted boilers at coal sites. The arm must not
  touch them, and §5 verifies it does not.

---

## §4 The arm

**ONE field: `measured_coal_heat_rates: bool = False`, armed for NWPP alone via
`--measured-coal-heat-rates` on the run.** It is the COAL sibling of
`measured_ct_heat_rates`, built on the identical seam
(`fleet/eia860.py::_rows_to_generators`, class-gated in the row loop), the
identical identification, and the identical artifact schema.

Two deliberate departures from the CT deriver, both declared **here, ex ante, on
physics, and never swept**:

1. **The screen is `opTime >= 0.99` (steady-state operating), not the CT
   deriver's `>= 0.8 × p95` loaded window.** A simple-cycle peaker either runs
   at full output or not at all, so for it "at load" and "operating" coincide and
   the part-load hours it drops are transients. A coal steam unit's *normal*
   operating range **is** part load — it is committed and then cycles between
   min-load and HSL, which is precisely the behaviour the model must reproduce —
   so a near-HSL window would price the plant at its best point. `opTime >= 0.99`
   removes exactly the partial clock hours carrying startup and shutdown fuel,
   and nothing else. The near-HSL rate is **reported** in the artifact
   (`heat_rate_gross_hsl`) and is **never applied**; a test pins that.
2. **The technology tag is `primaryFuelInfo`, not `unitType`.** At Jim Bridger,
   Naughton and North Valmy the coal units and the gas-converted units are BOTH
   boilers, so `unitType` maps all of them to one family and cannot separate them.

**Governance.**
- Rule 14 `[R-ACCURATE]` is the basis: a measured plant record replaces an
  estimate. **Never the residual.**
- Rule 13 `[R-MEASURED]`: a machine's operating heat rate is a physical
  characteristic; it regenerates for a forward year from the same pipeline and
  responds to changed conditions (a retrofit moves it; a converted unit drops out
  of the coal population). An INPUT, never a pinned outcome.
- Rule 21 `[R-DOF]`: **ZERO free parameters.** Every applied number is
  `Σ heatInput / Σ grossLoad` over the plant's own hours. The band `[8.0, 25.0]`
  gross is a meter guard (below 8.0 implies > 42 % HHV efficiency; above 25.0 a
  broken channel), applied at both grains, and it excluded **zero** NWPP plants.
- Rule 19 `[R-ONE-MECH]`: it REPLACES the eGRID rate for covered coal rows; it
  stacks on nothing. The `mustrun` band is fuel-free and is provably unmoved (§5).
- Rule 25 `[R-ISO-SCOPE]`: NWPP's own plants, NWPP's own artifact; every other
  ISO's cell enters `U` with nothing transferred, and the field is a strict no-op
  for an ISO with no artifact.
- Rule 1 `[R-STRUCT]`: `authorized_price_tuning = NONE`. No band multiplier, no
  adder, no share. Set ex ante from data, never swept against a gate.
- Default OFF and **byte-identical off**: registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` at its frozen default, so no existing keeper's
  cache key moves (`check_cache_key_registration.py` green: 853 fields, 308
  registered, all defaults match HEAD).

---

## §5 Confinement, PROVEN zero-LP before the solve

`scripts/probes/_nwpp42_measured_coal_hr_phase0.py`, offer-array delta on the
keeper's own recipe:

| year | NON-COAL offer max&#124;Δ&#124; | NON-COAL rows moved | COAL rows moved | pmax max&#124;Δ&#124; | availability max&#124;Δ&#124; |
|---|---|---|---|---|---|
| 2023 | **$0.0000000000** | **0 of 570** | 53 of 76 | **0.0000000000** | **0.000000000000** |
| 2025 | **$0.0000000000** | **0 of 566** | 50 of 76 | **0.0000000000** | **0.000000000000** |

So the 1,571 MW of gas-converted boilers are byte-identical, and the mechanism
**reprices without re-rating**.

Merit position, against the keeper's **own committed P1 zonal duals**:

**2023** (price mean $48.87, p50 $36.50, p90 $52.50)

| band | cap MW | ctl $/MWh | arm $/MWh | Δ | ctl % zone-hrs clearing | arm % |
|---|---|---|---|---|---|---|
| mustrun | 2630.2 | 4.500 | 4.500 | **+0.000** | 94.9 | 94.9 |
| committed | 2733.3 | 33.559 | 31.662 | −1.897 | 59.6 | 74.7 |
| econlo | 1417.9 | 37.371 | 34.800 | −2.571 | 43.8 | 52.2 |
| econhi | 1160.1 | 37.371 | 34.800 | −2.571 | 43.8 | 52.2 |
| peak | 162.1 | 35.308 | 33.234 | −2.074 | 51.9 | 59.6 |

**2025** (price mean $30.52, p50 $28.64, p90 $40.05)

| band | cap MW | ctl $/MWh | arm $/MWh | Δ | ctl % zone-hrs clearing | arm % |
|---|---|---|---|---|---|---|
| mustrun | 2630.2 | 4.500 | 4.500 | **+0.000** | 100.0 | 100.0 |
| committed | 2733.3 | 35.922 | 33.694 | −2.228 | 24.7 | **34.0** |
| econlo | 1417.9 | 43.766 | 40.437 | −3.329 | 0.8 | **9.9** |
| econhi | 1160.1 | 43.766 | 40.437 | −3.329 | 0.8 | **9.9** |
| peak | 162.1 | 38.815 | 36.266 | −2.549 | 17.1 | 24.3 |

Largest movers are the plants §3.3 fingered: North Valmy 13.111 → 11.363
(−$8.64/MWh mean) and Hunter 13.330 → 10.969 (−$8.41/MWh mean) in 2025.

**G-DRIFT (rule 29(b) form 4, no control solve).** The control is the keeper's
committed bundle. `git diff <keeper sha> HEAD` over the solve path contains this
lane's own change and nothing else that reaches a `mode="backcast"` NWPP run; the
new field is default-off and absent from the keeper's recipe, so the control leg
of the probe above **reproduces the keeper's own assembled arrays exactly**,
which is a stronger check than a control solve and cost seconds. The
marginal-carbon control shard (§7) gives the empirical confirmation.

---

## §6 Pre-registered predictions — including the ones that go against the arm

Written before the solve and not adjustable afterwards.

1. **Coal volume rises materially in 2024 and 2025, and does NOT close the gap.**
   From the band clearing shares, I estimate 2025 coal **27.2 → 30–33 TWh**
   against a 42.0 actual. NRMSE improves; **I do not predict C4 NRMSE passes.**
2. **`r` improves but I do NOT predict it reaches 0.70.** `r` is level-invariant
   and today's 0.50 is an amplitude failure. The arm moves energy from the flat
   `mustrun` block toward the price-following bands, which must raise amplitude —
   but the `mustrun` block is unmoved at $4.50 and still ~18 TWh, and a residual
   shape term of 0.24–0.31 survives a perfect level fix (§2). **My central
   expectation is C4 still FAILs and the determination stays NOT-YET.**
3. **2023 is the risk year, and the arm makes it worse.** 2023's committed band
   goes from clearing 59.6 % of zone-hours to 74.7 %. 2023 COAL_BIT is already
   **+7.4 %**. I predict 2023 coal moves further OVER and **a C1 row may cross out
   of band**. Rule 14 is explicit that this is not a reason to revert: the
   accurate input stays and the worse fit is a discovered bug elsewhere. If it
   happens I will report it at full magnitude and route it, not absorb it.
4. **Zero movement anywhere but coal**, already proven in §5 and expected to hold
   in the solved bundle: non-coal class energy should differ only through
   dispatch displacement, never through cost.
5. **DOF ledger unchanged** at the keeper's 3 entries / 3 residual. The arm adds
   a measured input, not a parameter.
6. **C6 governance PASS, `authorized_price_tuning` NONE.**

**Kill condition, declared now:** if the solved arm moves COAL by less than
0.5 TWh in 2025, the mechanism is `I` (inert) for NWPP and I will say so.

---

## §7 Shards (rule 32 `[R-SHARD]`)

**This session runs no LP.** Two shards, both pinned to this doc's own commit sha.

- **ARM** — one shard, one `--year 2023 2024 2025` invocation, years sequential
  inside it (rules 12 / 16 `[R-ALLYEARS]` / 32(b)); slim per-year fan-out banned.
  Budget ≥ 900 min (NWPP-41 measured 749.3 min of LP for the span, peak RSS
  4.78 GiB against a 13.36 GiB cgroup ceiling, no swap). It pushes its full
  bundle including `dispatch/<year>_P1.parquet` (rule 34 `[R-SHARD-PROMOTABLE]`).
- **MARGINAL-CARBON CONTROL** — `replay_keeper.py` on `nwpp41_span_A`, all three
  years, one bundle. **Launched**, on the brief's own test: phase 0 took fork (b),
  and while the arm is structurally sound its promotion is genuinely open because
  §6 predicts it does not flip the determination. NWPP has **no**
  `marginal_emission_rate` data at all today (the keeper pin `666343a2` predates
  `2ec09663`), and the replay doubles as the empirical check on the form-4
  control claim.

Both shards: never rebase / pull / sync; no `git add -A` or `git add .`; no
`dashboard_add_run.py` / `build_manifest.py` / `build_status.py` /
`prune_iso_runs.py`; nothing under `frontend/data/backcast/**`; no edit under
`src/` or `scripts/`; no PR; **delete no result** (rule 31 `[R-RETAIN]`).

---

## §8 Pre-existing REDs and failures that are NOT this lane's

- `check_registry_payload_parity.py` carries two REDs on `main` —
  `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` — belonging to the CAISO
  and SOCO/SPP lanes. Read, confirmed not mine, **not touched** (rules 25 / 31).
- Five unit tests fail identically on `main` with my changes stashed:
  `test_data_profiles_tokens::test_soco_token_collides_with_no_other_raw_name`,
  `test_caiso_st_gas_peak_measured::test_registry_value_matches_the_committed_artifact`,
  `test_fleet::TestLoadRetiredWithinWindow::test_neiso_includes_mystic_cc`, and
  both `test_gas_offer_zonal_anchor_vintage` cases. Reported, not repaired.
- With those deselected the lane is green: **3,518 passed**, and the 25 tests of
  `test_measured_coal_heat_rates.py` + `test_measured_ct_heat_rates.py` all pass.

## §9 Carried forward from NWPP-41, absorbed nowhere

Energy balance −10.02 TWh in 2025 (served-interchange construction) · the Chief
Joseph 2025 pond-balance dual at a constant −325.17 $/kcfs·h for 5,808 hours ·
NWPP-SNV VOLL hours 23 + 34 (a path-rating question) · reported-only C5a CO2
−15.1 / −23.7 / −21.4 % · the cross-ISO PRB-proxy defect still open in MISO (12
plants), PJM (2) and SPP (3–5), which is **not this lane's** (rules 25 / 28(d))
and wants three separate one-flag lanes.
