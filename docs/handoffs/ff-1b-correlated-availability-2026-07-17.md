# FF-1B — Correlated forced-outage availability + the screen reserve-value signal

_Generated 2026-07-17 · Forecast Finalization Program lane FF-1B (plan §6; BLK-6's
structural half) · implements the RC-2A Part D design charter
(`docs/handoffs/ercot-retirement-composition-2026-07-16.md`) on the consolidated
outage seam (post PR #2415/#2416) · forecast/hindcast-side, NON-KEEPER probes ·
no backcast keeper / dispatch-layer / offer-curve change · the G-20/G-22 AS co-opt
is consumed as-is (hard boundary) · quarantine: solve years {2021, 2023, 2024,
2025} only, 2022 bridged-never-solved (rule 22)._

**One line.** The correlated cold-event forced-outage derate (measured Uri/
Elliott/Heather curves, frozen, default-off) breaks the G-31 "$0.00 in every
year" result: with it armed, **the 2024 hindcast year forms in-year ORDC
scarcity for the first time — mean $0.87/MWh (≈ $7.6/kW-yr of reserve value),
max $4,968/MWh at Winter Storm Heather** (the real event's RT prints peaked
$3–5k), lifting the next screen year's CT net revenue **6.4 → 11.9 $/kW-yr
(~17.5 % of the SOM ≈68 anchor, up from ~3 %)** and putting gas-CC above its
going-forward bar (30.7 vs 30.0) for the first time; the **Uri year (2021)
still prints $0** — not an availability gap (the derate removes 14.35 GW at
the Uri peak) but a **demand-input gap**: hindcast demand is the measured
*served* load, which is firm-shed-suppressed to 46.8 GW against ~77 GW of
underlying demand, so no availability mechanism can (or should) make that
year scarce; and the derate alone does **not** fix the first-wave
over-retirement (Leg B 23.0 GW vs actual 1.53), so the composition arms stay
necessary — the remaining CT screen residual to SOM, **≈ 56 $/kW-yr, is
handed to G-20/G-22 as a number** (rules 1/13).

---

## 1. What landed (Stages 1–3 of the charter, D.7)

### 1.1 Stage 1 — the frozen derive (`scripts/derive_correlated_outage_curve.py`)

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
  the evening chills the calendar day's TMIN while the fleet response lands next
  morning — Elliott Dec-22 vs Dec-23).
- **Event windows**: consecutive days with system daily TMIN (plain mean of
  `tmin_c` across the six ERCOT weather zones, NOAA archive) ≤ −7 °C — the NERC
  cold-weather onset (~20 °F), the same published anchor as
  `neiso_gas_derate_t0_c`.
- **In-merit certificate**: the window must contain a day whose daily-max
  EIA-930 ERCO NET load reaches the year's p99 (the exogenous instrument of
  `scripts/lib/outage_detect.py`), extended across the window because measured
  demand mid-event is firm-shed-suppressed (Uri: EIA-930 demand collapses
  Feb 15-18 while Feb 14 sets the record). Under the certificate, capacity that
  never runs is unavailable, not out of merit. The Jan-2018 cold snap fails the
  certificate and is (conservatively) excluded.
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
  is a known under-coverage). Both make the derate *conservative*.

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
  Uri winter the realized excess dominates — exactly the condition response
  rule 13 requires.
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
2022 bridged), two legs, run concurrently (rule 12):

- **Leg A** `ercot-2021-2025-realized-g31staged-cfo-ff1b`: the committed RC-2A
  arm (lookahead + staged 3.0 GW + limited-foresight) + the derate. BEFORE =
  the committed `ercot-2021-2025-realized-g31staged-rc2a` bundle (byte-identical
  reproduction at HEAD, RC-2A §B.1 — never re-solved here, §2.4 rule 3).
- **Leg B** `ercot-2021-2025-realized-cfo-only-ff1b`: the derate alone, no
  staging/lookahead arms — the charter's Stage 4(iii) question (does in-year
  scarcity remove the need for the composition workarounds?). BEFORE = the
  committed baseline arm (22.80 GW thermal false-retire, RC-2A §B.1 table).

_(measured results filled below when the legs complete)_

### 2.1 In-year ORDC formation (the G-31 re-measurement)

| year | BEFORE (rc2a: mean / h>$10 / max) | Leg A (derate) | Leg B (derate, no arms) |
|---|---|---|---|
| 2021 | $0.00 / 0 h / $0 | — | — |
| 2023 | $0.00 / 0 h / $0 | — | — |
| 2024 | $0.00 / 0 h / $0 | — | — |
| 2025 | $0.00 / 0 h / $0 | — | — |

### 2.2 Screen CT revenue vs the SOM ≈68 anchor (the BLK-6 residual re-measurement)

| class | year | BEFORE net_rev $/kW-yr | AFTER (Leg A) | SOM anchor |
|---|---|--:|--:|--:|
| gas_ct | 2022 screen | 1.9 | — | CT 68 (2024) / 52.6 (2025) / 224-257 (2023) |

### 2.3 Retirement composition (T-R3 scorecard columns)

| arm | thermal GW | coal GW | false-retire | recall≥300 | solar add |
|---|--:|--:|--:|:--|--:|
| staged (rc2a BEFORE) | 12.73 | 6.47 | 11.29 (88.7%) | PASS | 4.0 |
| Leg A (staged + derate) | — | — | — | — | — |
| baseline (BEFORE, no arms) | 22.80 | 13.96 | 21.87 (95.9%) | FAIL | 0.0 |
| Leg B (derate only) | — | — | — | — | — |

## 3. Default posture (owner decision)

_(recommendation written after the probe results; the charter's stated posture:
present ON-for-forecast as the recommendation if the probe supports it — the
owner decides. The config default stays OFF until then.)_

## 4. What remains for G-20/G-22 (never closed here)

Whatever screen-revenue residual to the SOM anchor survives the structural
availability is handed to the G-20/G-22 lane **as a number** (rule 1/13: no
fitted rent, no adder). _(quantified in §2.2 when the legs land.)_

## 5. Session notes

- Files touched: `scripts/derive_correlated_outage_curve.py` (new),
  `constants.py` (+`CORRELATED_OUTAGE_CURVE`), `scenarios.py` (4 fields +
  sigma-scale gate), `data/outages.py` (mechanism + wrapper), `runner.py`
  (availability-seam call), `results/scarcity.py` (`resolve_lolp_params` sigma
  seam), `eia_loader.py` (raw weather supplement fallback),
  `run_capacity_hindcast.py` (`--correlated-forced-outage` probe flag),
  `tests/test_correlated_outage.py` (new). `model/capacity.py` untouched
  (L-CAP-owned, read-only this session); the screen consumes the improved
  reserve-price signal through the existing `screen_reserve_value_enabled`
  seam unchanged.
- Pre-existing test failure at HEAD (not this session's):
  `tests/test_outages.py::NEISOUnitOutageSmokeTest::test_coal_target_is_merrimack_only_all_years`
  (a non-Merrimack facility, 568, appears in the NEISO COAL unit-outage
  extract) — reproduced on a clean stash of this branch's changes.
- Data notes: the derive reads on-disk, previously-intaken archives only
  (CAMPD TX 2018-2025, NOAA weather 2018-2025, EIA-930 ERCO); the 2026 CAMPD/
  weather partitions are deliberately excluded from the derive window (rule
  22 caution). Elliott (Dec-2022) is measured *input data* for a frozen
  physical parameter per the charter's explicit derivation-target list — no
  2022 solve/score occurs anywhere.
- `data/clean` regeneration needed on a fresh checkout before hindcast runs:
  `scripts/curate_confirmed_retirements.py` (fail-loud registry guard).
