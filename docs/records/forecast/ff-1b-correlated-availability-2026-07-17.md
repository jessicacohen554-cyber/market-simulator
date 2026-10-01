# FF-1B — Correlated forced-outage availability + the screen reserve-value signal

_Generated 2026-07-17/18 · Forecast Finalization Program lane FF-1B (plan §6;
BLK-6's structural half) · implements the RC-2A Part D design charter
(`docs/handoffs/ercot-retirement-composition-2026-07-16.md`) on the consolidated
outage seam (post PR #2415/#2416) · forecast/hindcast-side, NON-KEEPER probes ·
no backcast keeper / dispatch-layer / offer-curve change · the G-20/G-22 AS co-opt
is consumed as-is (hard boundary) · quarantine: solve years {2021, 2023, 2024,
2025} only, 2022 bridged-never-solved (rule 22)._

**One line.** The correlated cold-event forced-outage derate (measured Uri/
Elliott/Heather curves, frozen, default-off) breaks the G-31 "ORDC $0.00 in
every year of every arm" result — but **conditionally**: on the un-staged (thin)
fleet, **2024 forms in-year ORDC scarcity for the first time — mean $0.87/MWh
(≈ $7.6/kW-yr of reserve value), max $4,968/MWh at Winter Storm Heather** (the
real event's RT prints peaked $3–5k), lifting the next screen year's CT net
revenue **6.4 → 11.9 $/kW-yr (~17.5 % of the SOM ≈68 anchor, up from ~3 %)**;
on the staged (full) fleet the same 3.3 GW Heather derate is absorbed and ORDC
stays $0 — **in-year scarcity formation is fleet-thickness-dependent**. The
**Uri year (2021) prints $0 in both legs** — not an availability gap (the
derate removes 14.35 GW at the Uri peak, curve-validated against the FERC/NERC
report) but a **demand-input gap**: hindcast demand is the measured *served*
load, firm-shed-suppressed to 46.8 GW against ~77 GW of underlying demand, so
no availability mechanism can (or should) make that year scarce. The derate
alone does **not** fix the first-wave over-retirement (Leg B 23.0 GW vs actual
1.53); the staged leg's headline improvement (12.73 → 6.26 GW, coal wave → 0)
is **confounded — the RC-1A-D1 coal-threshold adoption (`retirement_years_coal`
1→3) landed on main mid-session** and re-baselines the BEFORE exactly as RC-2A
§A.1 predicted. The remaining CT screen residual to SOM (**≈ 56 $/kW-yr
post-event, ≈ 66 in event-free years**) is handed to G-20/G-22 as a number
(rules 1/13).

---

## 1. What landed (Stages 1–3 of the charter, D.7)

### 1.1 Stage 1 — the frozen derive (`scripts/data/derive_correlated_outage_curve.py`)

Per-class temperature → excess-forced-outage hinge curves, era-split on the PUCT
weatherization rule (16 TAC §25.55, adopted Oct-2021, phase-1 compliance winter
2021-22), frozen into `constants.CORRELATED_OUTAGE_CURVE` (rule 23 — re-derives
only on a source-data change):

| era | class | slope /°C | cap | winter event share | anchors |
|---|---|--:|--:|--:|---|
| pre | COAL | 0.0381 | 0.270 | 0.0018 | Uri 2021-02-16 (TMIN −14.1 °C) |
| pre | CC_REGULAR | 0.0618 | 0.438 | 0.0029 | 〃 |
| pre | CT_PEAKER | 0.0784 | 0.556 | 0.0037 | 〃 |
| pre | ST_GAS | 0.0779 | 0.552 | 0.0037 | 〃 |
| post | COAL | 0.0204 | 0.077 | 0.0004 | Elliott 2022-12-23, Heather 2024-01-16 |
| post | CC_REGULAR | 0.0605 | 0.157 | 0.0011 | 〃 |
| post | CT_PEAKER | 0.1878 | 0.466 | 0.0033 | 〃 |
| post | ST_GAS | 0.1304 | 0.306 | 0.0023 | 〃 |

**Identification** (all inputs measured + exogenous; no LMP/price/residual
anywhere):

- **Instrument**: CAMPD TX unit-level hourly gross load
  (`data/raw/campd-unit-level/TX_<yr>.parquet`) summed per class against the
  ERCOT CAMPD bin-sheet capacities — per event day, the class's *best-mustered
  hour* fraction, measured at each cold window's coldest (TMIN-min) day so the
  muster response aligns with the temperature driver (a front that arrives in
  the evening chills the calendar day's TMIN while the fleet response lands
  next morning — Elliott Dec-22 vs Dec-23).
- **Event windows**: consecutive days with system daily TMIN (plain mean of
  `tmin_c` across the six ERCOT weather zones, NOAA archive) ≤ −7 °C — the NERC
  cold-weather onset (~20 °F), the same published anchor as
  `neiso_gas_derate_t0_c`.
- **In-merit certificate**: the window must contain a day whose daily-max
  EIA-930 ERCO NET load reaches the year's p99 (the exogenous instrument of
  `scripts/lib/outage_detect.py`), extended across the window because measured
  demand mid-event is firm-shed-suppressed (Uri: EIA-930 demand collapses
  Feb 15-18 while Feb 14 sets the record). Under the certificate, capacity
  that never runs is unavailable, not out of merit. The Jan-2018 cold snap
  fails the certificate and is (conservatively) excluded.
- **Baseline**: NERC-GADS class EFORd (`constants.EFORD`) — the same baseline
  the statistical WEFOR model is built on, so the excess is by construction the
  event increment *on top of* the model's existing forced-outage representation.
- **External anchor**: capacity-weighted Feb-16 thermal excess ≈ 44 %,
  consistent with the FERC/NERC February 2021 Cold Weather Report (~half the
  expected-available ERCOT fleet lost at the Uri peak).
- **Winterization signal**: the post-era saturation depths are roughly half the
  pre-era ones (CC 0.157 vs 0.438; ST 0.306 vs 0.552) — the measured effect of
  the PUCT weatherization program, and the forward-responsiveness lever the
  charter requires (rule 13: a hardened fleet shrinks the derate).
- **Exclusions, stated**: CHP classes (host-loaded gross output cannot certify
  grid availability) and nuclear (no CAMPD trace; the STP-1 Uri trip, 1.28 GW,
  is a known under-coverage). Roughly half the hindcast thermal fleet's
  capacity is therefore uncovered (measured Uri-peak removal 14.35 GW vs the
  ~30 GW the curves would imply at full class coverage) — the derate is
  *conservative* by construction.

### 1.2 Stage 2 — the wired mechanism (default OFF)

`ScenarioConfig.correlated_forced_outage` (+ `correlated_outage_t0_c`,
`correlated_outage_winterized_year`) → `data/outages.apply_correlated_outage_derate`,
called at the runner availability seam (`runner.py`, next to the NEISO cold-snap
derate, before the LP bounds and the ORDC reserve read availability). Per
covered class:

    avail[g,t] ← clip( avail[g,t] + winter_event_share·1[Dec-Feb]
                                  − clip(slope·(t0 − TMIN_sys(day t)), 0, cap), 0, 1 )

- **Correlated by construction**: every unit reads the same system daily-TMIN
  series (the validated `neiso_gas_coldsnap_derate` pattern, generalized).
- **WEFOR coordination (rule 19 / charter D.3)**: the era's climatological
  Dec-Feb mean of the curve (`winter_event_share`) is added back first, so the
  mechanism *relocates* the cold-event share embedded in the flat GADS-based
  WEFOR into the actual cold days instead of stacking a second forced-outage
  representation on it. In an average winter the two cancel in the mean; in a
  Uri winter the realized excess dominates — the condition response rule 13
  requires.
- **Weather-driver resolution**: the solve year's own weather when the archive
  covers it (a hindcast leg reads its realized TMIN — 2021 sees Uri), else the
  pinned `config.weather_year` sample. The raw-CSV weather fallback now folds in
  the year-partitioned supplement files (`eia_loader._load_weather_from_raw`),
  matching the curated clean tree's coverage — before this, ERCOT 2021 weather
  silently resolved to `None` on a fresh checkout.
- **Mode gating (charter D.5)**: forecast/hindcast only. In backcast the
  measured CAMPD overlays already carry the actual events; the wrapper is a
  hard no-op there (plus an `outage_source == "historic"` belt-and-braces
  guard). ISOs without a curve entry are a no-op (rule 25 — an ERCOT-fitted
  curve never crosses an ISO boundary; no generic fallback exists).

### 1.3 Stage 3 — the ORDC double-count seam (charter D.6), documented + gated

The derate enters the ORDC **only through the deterministic mean**: the
post-solve point reserve reads `pmax × availability` (`scarcity.py::
reserve_headroom`), so a deep-cold event thins both the dispatchable stack in
the LP and the reserve the ORDC prices — additively and correctly. The LOLP
convolution's `sigma_mw` (NP6-576-ER, the historical reserve-error spread that
already blends net-load forecast error AND forced-outage uncertainty) is left
untouched at the default: the mechanism injects **no outage-variance term**, so
sigma at 1.0 is not a double count by construction.

The re-decomposition seam is `correlated_outage_sigma_scale` (default 1.0),
applied in `scarcity.py::resolve_lolp_params` and **gated with the derate
flag** — `ScenarioConfig.__post_init__` rejects any non-1.0 value while
`correlated_forced_outage` is off, so the two can never fire inconsistently and
the scale can never be re-armed as a free-standing ORDC tuning channel. It is
identified only by a re-derived reserve-error decomposition (or a re-derived
NP6-576-ER table via `ordc_lolp_params_path`), never by a residual (rule 21).

Two further surfaces from D.6, closed by construction: (i) the in-fleet WEFOR
share — handled by the event-share relocation above; (ii) the backcast
measured scarcity-rent overlays — unreachable, the mechanism is
forecast/hindcast-only.

### 1.4 Validation (Stage 4(i) — charter D.5 self-consistency)

`tests/test_correlated_outage.py` (13 tests, trivial-first: synthetic TMIN, one
generator, 48 hours → gating/era semantics → sigma guard). The Uri
self-consistency test runs the **forecast-mode** model on the real 2021 weather
year and asserts it regenerates the measured Uri-scale derate depth for every
covered class from the temperature series alone (and no summer leakage) — the
rule-13 proof that the event regenerates from weather + physics, not from a
pinned outcome.

## 2. Probe — does in-year ORDC scarcity now form (G-31), and what does the CT screen see (BLK-6)?

_Setup_: ERCOT capacity hindcast (2020 vintage, 2021→2025 realized fuel/demand,
2022 bridged), two legs run concurrently (rule 12), registered on the
forecast-validation dashboard:

- **Leg A** `ercot-2021-2025-realized-g31staged-cfo-ff1b`: the RC-2A arm
  (lookahead + staged 3.0 GW + limited-foresight) + the derate. **Base-config
  caveat (central to reading this leg):** the run executed after a mid-session
  rebase onto main, which had adopted **RC-1A-D1 Option B
  (`retirement_years_coal` 1 → 3)** — the exact re-baseline RC-2A §A.1
  anticipated. Leg A is therefore **derate + threshold-3**, NOT a one-delta
  arm against the committed rc2a (threshold-1) BEFORE.
- **Leg B** `ercot-2021-2025-realized-cfo-only-ff1b`: the derate alone, no
  staging/lookahead arms — the charter's Stage 4(iii) question. BEFORE = the
  committed baseline arm (22.80 GW thermal false-retire, RC-2A §B.1; solved
  pre-rebase at main 2a30c28 + FF-1B, where the D1 flip had not yet applied to
  anything this leg exercises differently — its coal exits are all first-wave
  economic).

### 2.1 In-year ORDC formation (the G-31 re-measurement)

| year | rc2a BEFORE (all arms) | Leg A (staged + derate, thr-3) | Leg B (derate only) |
|---|---|---|---|
| 2021 (Uri, pre-era) | $0.00 / 0 h / $0 | $0.00 / 0 h / $0 | $0.00 / 0 h / $0 |
| 2023 (no cold event) | $0.00 / 0 h / $0 | $0.00 / 0 h / $0 | $0.00 / 0 h / $0 |
| 2024 (Heather) | $0.00 / 0 h / $0 | $0.00 / 0 h / $0 | **mean $0.87 / 7 h>$10 / max $4,968** |
| 2025 (no event ≤ t0) | $0.00 / 0 h / $0 | $0.00 / 0 h / $0 | $0.01 / 2 h / $32 |

**Read.** The G-31 blocker is broken, with a precise boundary:

1. **Heather 2024 forms real in-year scarcity on the thin (un-staged) fleet**
   — max $4,968 vs the real event's $3–5k RT prints, 7 h > $10 concentrated in
   the Jan 15-17 mornings. The 3,283 MW Heather derate (post-era curve on the
   evolved fleet) is what tips it.
2. **The same derate on the staged (full) fleet is absorbed** — Leg A's 2024
   fleet carries ~10 GW more thermal (coal retained by threshold-3 + staging),
   and ORDC stays $0. In-year scarcity formation is **fleet-thickness-
   dependent**; the availability mechanism is necessary but not sufficient on
   an over-supplied stack.
3. **Uri 2021 cannot form scarcity in ANY hindcast leg, by construction of the
   demand input**: the derate removes 14.35 GW at the Uri peak (hour 1104,
   Feb 16), but hindcast demand is the measured *served* load — Feb 15-18
   collapses to 44-49 GW under firm shed vs ERCOT's ~77 GW estimate of
   underlying demand. With ~60 GW still available, the LP holds double-digit
   reserve. This is a **demand-input information gap** (the served-load series
   embeds the event's own load shed), NOT an availability gap, and it does not
   affect forecast years (forecast demand is weather-scaled, never
   shed-suppressed). Closing it would need a counterfactual (weather-driven)
   demand input for shed windows — a separate, explicitly-scoped intake, not
   this mechanism's job.

### 2.2 Screen CT revenue vs the SOM ≈68 anchor (the BLK-6 residual re-measurement)

Capacity-weighted `screen revenue stack [gas_ct]` $/kW-yr (the capacity.py
diagnostic; screen year N consumes year N−1's signal):

| screen year | rc2a BEFORE | Leg A (staged+thr3+derate, lookahead basis) | Leg B (derate only, raw duals+ORDC) | SOM anchor |
|---|--:|--:|--:|--:|
| 2022 (from 2021) | 1.9 | 1.9 | 1.8 | (2021 not a SOM comparator) |
| 2024 (from 2023) | 757.3 | 166.6 | 6.4 | CT 224–257 (2023) |
| 2025 (from 2024) | 241.8 | 95.7 | **11.9** | CT **68** (2024) |

**Read, per leg:**

- **Leg B (the clean derate measurement):** the 2024 in-year ORDC contributes
  ≈ $7.6/kW-yr of reserve value (mean adder × 8760 h), lifting the post-event
  screen 6.4 → 11.9 $/kW-yr ≈ **17.5 % of the SOM 68 anchor** (the pre-derate
  level captured ~3 %). In event-free years the screen stays starved (1.8–6.4).
  **Residual to SOM: ≈ 56 $/kW-yr in the event year, ≈ 66 in event-free years
  (co-opt off) — G-20/G-22's number, unchanged in kind, now smaller in the
  event years the availability model can reach.**
- **Leg A (confounded but informative):** the lookahead pro-forma's ~11×
  overshoot (rc2a: 757 vs SOM 224–257) collapses to **166.6 (~0.7× the 2023
  anchor) and 95.7 (~1.4× the 2024 anchor)** — the fuller (coal-retaining)
  stack prices far less pro-forma scarcity. This is composition-mediated
  (threshold-3 + derate jointly), so it is NOT attributed to the derate alone;
  but it shows the screen-signal *level* entering the SOM corridor for the
  first time on a production-shaped arm.

### 2.3 Retirement composition (T-R3 scorecard columns)

| arm | thermal GW | coal GW | gas_ct | gas_st | false-retire GW (%model) | recall≥300 | CO₂'25 Mt |
|---|--:|--:|--:|--:|--:|:--|--:|
| baseline BEFORE (rc2a, thr-1, no arms) | 22.80 | 13.96 | 0.00 | 8.83 | 21.87 (95.9 %) | FAIL | 95.2 |
| **Leg B (derate only, thr-1)** | **23.01** | **7.22** | **4.52** | **11.27** | **21.58 (93.8 %)** | **PASS** (3/3 fuel-MW) | — |
| staged BEFORE (rc2a, thr-1, all arms) | 12.73 | 6.47 | 3.02 | 3.24 | 11.29 (88.7 %) | PASS | 115.6 |
| **Leg A (staged + derate, thr-3)** | **6.26** | **0.00** | **3.02** | **3.24** | **5.76 (92.0 %)** | **FAIL** (1/3) | 140.2 |
| actual | 1.53 | 0.93 | 0.50 | 0.00 | — | — | 193.6 |

**Read.**

- **Stage 4(iii) answer: NO — in-year scarcity does not remove the need for
  the composition arms.** Leg B's first wave is decided on the 2021/2022
  starved signals (Uri shed-suppressed, 2023 event-free), so its total
  over-retirement is unchanged (23.0 vs 22.8 GW); the derate reshapes the mix
  (coal 13.96 → 7.22, more CT/ST) but cannot reach the level. Staging/lookahead
  (or the successor FF-0C decision rule) remain necessary.
- **Leg A's composition deltas vs rc2a are threshold-3-driven, not
  derate-driven**: ledger diff localizes the entire coal-wave disappearance to
  the 2022/2023 evolutions (rc2a: 3.03 + 3.43 GW coal; Leg A: none, no floor
  involvement, near-identical 2022-screen class averages 21.4 vs 21.3) — with
  `retirement_years_coal=3`, coal's counters are reset by the recovered
  2024-screen (173.6 > bar) before reaching three loss years. Recall drops to
  FAIL (1/3) because the real 2021-25 coal exits are no longer produced —
  the same D1 recall-elimination RC-1A-D1 measured on PJM, now visible on
  ERCOT. This belongs to the FF-0C/FF-1A decision-rule lane (their memo covers
  it); it is recorded here, not acted on.
- RC-2A §A.1's standing note applies: with D1 Option B on main,
  `staged_oversupply_thinning` should be re-examined for default-off (the
  threshold now carries the deactivation queue — rule 19); that call is
  FF-1A's, with this leg as evidence that the two together over-retain
  (coal 0.0 vs actual 0.93).

### 2.4 Runtime honesty (§2.4 rule 5)

4-CPU / 15 GiB box. Leg B (no arms): 4 solve years in ~12 min wall (~3 GB) —
the un-staged fleet's LPs are small. Leg A (all arms, post-rebase re-solve):
~89 min wall for 2021/2023/2024/2025 (~3 GB), dominated by the staged 2025
solve (~44 min). Concurrent-leg CPU contention roughly doubled Leg A's first
(killed) attempt's year times; the two-invocation cap (rule 12) held on RAM
but is CPU-bound on this box — prefer sequential legs at 4 CPUs.

## 3. Default posture (owner decision)

**Recommendation: arm `correlated_forced_outage=True` for forecast/hindcast
runs** (the charter's ON-for-forecast posture), on this evidence:

- It is the only mechanism that has ever formed in-year ORDC scarcity in a
  hindcast (Leg B 2024), and its magnitude validates externally (max $4,968 vs
  Heather's real $3–5k prints; Uri depth reproduced from weather alone).
- It is measured, frozen, era-aware (winterization), conservative (CHP/nuclear
  uncovered), and rule-13/19/23-clean; default-off it is dead code in exactly
  the runs (forecast) whose scarcity formation it exists to fix.
- Cost: none measurable (a per-class availability adjustment at data-prep).

Two caveats for the owner's call: (a) on full (staged/threshold-3) fleets the
in-year effect is currently absorbed — the flag's value grows as the FF-0C
rule lands and fleets thin honestly; (b) the config default stays OFF until
the owner signs off (this doc is the recommendation, not the flip — the flip
would be LOYO-scored per rule 22 in whichever lane adopts it).

## 4. What remains for G-20/G-22 (never closed here)

- **CT screen residual to SOM ≈68: ≈ 56 $/kW-yr in an event year (screen
  11.9), ≈ 66 $/kW-yr in event-free years (screen 1.8–6.4), co-opt off** —
  the availability half is now structural; the *level* remains the co-opt/AS
  lane's (their ~15 $/kW-yr co-opt increment plus the ~51 residual, per RC-2A
  §C, both still open).
- The event-year reserve value the ORDC now prices (≈ $7.6/kW-yr) is a floor
  on what the co-opt should reproduce in those hours (RTORPA parity), a
  useful cross-check when G-20/G-22 lands.

## 5. Session notes

- Files touched: `scripts/data/derive_correlated_outage_curve.py` (new),
  `constants.py` (+`CORRELATED_OUTAGE_CURVE`), `scenarios.py` (4 fields +
  sigma-scale gate), `data/outages.py` (mechanism + wrapper), `runner.py`
  (availability-seam call), `results/scarcity.py` (`resolve_lolp_params` sigma
  seam), `eia_loader.py` (raw weather supplement fallback),
  `run_capacity_hindcast.py` (`--correlated-forced-outage` probe flag),
  `tests/test_correlated_outage.py` (new). `model/capacity.py` untouched
  (L-CAP-owned, read-only this session); the screens consume the improved
  reserve-price signal through the existing `screen_reserve_value_enabled`
  seam unchanged.
- Registered (forecast-validation dashboard, `frontend/data/hindcast/`):
  `ercot-2021-2025-realized-cfo-only-ff1b`,
  `ercot-2021-2025-realized-g31staged-cfo-ff1b`. Both carry the expected
  probe invariant failures of their arms (Leg B: I6/I7 over-retire, I9
  storage tiebreak, I12; Leg A: recall/thermal bands per §2.3).
- Pre-existing issues at HEAD found in passing (not this session's, not
  fixed here): `tests/test_outages.py::NEISOUnitOutageSmokeTest::
  test_coal_target_is_merrimack_only_all_years` fails (facility 568 in the
  NEISO COAL extract); `runner.py:~1852` F821 (`hours` undefined in the
  CAISO scarcity import-headroom block — would NameError if
  `caiso_scarcity_import_headroom` is armed on that path).
- Data notes: the derive reads on-disk, previously-intaken archives only
  (CAMPD TX 2018-2025, NOAA weather 2018-2025, EIA-930 ERCO); the 2026
  partitions are deliberately excluded from the derive window (rule 22
  caution). Elliott (Dec-2022) is measured *input data* for a frozen physical
  parameter per the charter's explicit derivation-target list — no 2022
  solve/score occurs anywhere.
- `data/clean` regeneration needed on a fresh checkout before hindcast runs:
  `scripts/data/curate_confirmed_retirements.py` (fail-loud registry guard).
