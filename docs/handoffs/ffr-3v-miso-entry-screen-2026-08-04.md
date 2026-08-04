# FFR-3V — why MISO's entry screen builds no solar

**Session:** ffr-3v, 2026-08-04. **Diagnosis lane.** Nothing was promoted, no
default was flipped, no band was widened, no parameter was tuned. Every number
below is either read off committed artifacts, computed from `src/` at head, or
measured by the one instrumented run this session spent.

**The question (inherited, not re-argued):**
`docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md` §6 — MISO's registered
T1-H leg `miso-2021-2025-realized-ffr3a3` reports **solar model 0.0 GW vs actual
18.649 GW (−100 %)**, and FFR-3S proved the COD-shifted scoring basis cannot
explain a zero. Three consecutive decision cohorts (2021, 2022, 2023) decided
zero solar. Why?

---

## 0. Headline

**It is a MARGIN finding, not a candidate-set finding, and not a damper
finding.** Solar reaches the screen every decision year, its per-tech queue cap
is 6.0 GW and its growth-ladder cap is 1.236 GW — both non-zero — and it is
rejected on economics before any cap is consulted.

The decisive internal contrast is in the leg's own committed sidecar: **wind
built 4.0 GW in the same window, through the same code path, the same zonal-CF
mechanism and the same caps.** Whatever is stopping solar is specific to
solar's own margin, not to VRE entry.

The margin fails because solar's **only** revenue in the screen is merchant
energy:

| revenue stream | credited to solar? | value |
|---|---|---|
| merchant energy at the entry price signal | yes | ~$60–75 k/MW-yr |
| RPS attribute payment (REC) | **structurally zero** — MISO's 11 % target is slack against a 16.9 % modelled VRE share | $0 |
| exogenous EAC / federal CES premium | zero at the shipped config | $0 |
| **RA / capacity accreditation** | **NO — `entry_vre_capacity_revenue` is default-OFF** | would be **$14,364/MW-yr** |

against an annualized fixed cost of **$84.8 k–99.0 k/MW-yr**. Solar's
break-even mean entry price is **$41.9–48.9/MWh**; MISO's modelled price level
is ~$30–40/MWh.

Two further findings sit alongside it, both independent of the margin:

* **Even a profitable solar screen could not have passed FC-3.** The growth
  ladder + pending-queue netting **freeze** MISO solar at 1.236 GW/yr, so the
  maximum solar that can reach COD inside 2021–2025 is **≈3.7 GW against 18.649
  GW actual (−80 %)** (§5). The dampers are not why solar is zero, but they
  cap the best achievable outcome well short of a pass.
* **The wind PTC is credited over the plant's full 30-year book life** with no
  10-year statutory window, while the solar ITC is booked correctly. The screen
  therefore credits wind **$86,549/MW-yr** and solar **$26,787–32,873/MW-yr**
  (§4). This is the mechanical origin of the leg's inverted tech mix (model
  wind share 43.7 % / solar 0.0 % vs actual 22.5 % / 58.3 %). Proposed fix in
  §7, **not** applied here.

---

## 1. State verified at this session's own head

`origin/main` was `bf43122e` in the dispatch prompt and **`2c412668`** when
this session fetched; all work is rebased onto that. Everything below was
re-read at head.

* **MISO keeper has moved since dispatch:** the shard
  `frontend/data/backcast/keepers/MISO.json` reads
  **`2026-08-04-miso-126-steampart-b`**, not the `miso-124-dualfuel-rearm` the
  prompt named. Read as advisory; no keeper work was done here.
* Markers: `complete` = {NEISO, NYISO, PJM}; **MISO is in neither block**;
  `final` is empty. **Holdout freeze active.**
* `env | grep MARKET_SIM` — **empty** (no cache-key shift, FFR-3F §5).
* Rule 22: this session solved **forecast-mode hindcast years only**
  (2021/2023/2024/2025, the plain-hindcast allowed set; 2022 bridged and never
  solved). No out-of-training backcast year was solved, scored or read.

---

## 2. What was instrumented, and how

`ScenarioConfig.entry_screen_diagnostics` (RC-0C, default-off, **pure
observability — nothing reads it back**) emits one fully decomposed row per
*candidate* technology per decision year into the year's evolution ledger:
revenue terms, cost terms, the capacity factor used, the margin, and the
binding cap. That is exactly the instrument this lane needs, and it already
existed.

The registered leg ran with it **off** (`entry_screen_diagnostics: false` in
`frontend/data/hindcast/miso-2021-2025-realized-ffr3a3.json`), so it was
re-solved with the flag on and every other flag left at the harness default —
the same "all six solve-affecting flags omitted" posture `results/ffr3a3/README.md`
records for the registered leg:

```
uv run python scripts/run_capacity_hindcast.py --iso MISO --fuel-variant realized \
  --vintage 2020 --start-year 2021 --end-year 2025 --entry-screen-diagnostics \
  --out-dir results/ffr3v/miso-entry-diag
```

Ledgers read from `results/ffr3v/miso-entry-diag/MISO/<cache_key>/evolution_<year>.json`
— **not** the out-dir root (FFR-3C blocker 10; `load_ledgers_for_run` returns
`{}` rather than raising, so a wrong path reads as "no evolution happened",
which in this lane would look exactly like the finding).

*(§3 below carries the measured ledger.)*

---

## 3. The instrumented screen — measured

<!--LEDGER-->

---

## 4. Candidate directions: tested and eliminated

The dispatch named five directions, none privileged. All five were worked.

### 4.1 Eligibility / candidate set — **ELIMINATED. Solar is screened every year.**

`_NEW_ENTRY_TECHS` (`new_entry.py:106`) is
`("wind", "solar", "gas_cc", "gas_ct", "nuclear_smr")` — solar is
**unconditionally** a candidate; only the *emerging* techs carry an
availability-year gate. There is no interconnection-queue representation, no
resource-availability filter, and no share cap on the entry side at all.

Non-zero caps, all read from code at head:

| cap | MISO solar | source |
|---|---|---|
| ISO annual queue budget | 10.0 GW | `QUEUE_CAP_GW["MISO"]` |
| per-tech queue cap | 6.0 GW | `QUEUE_CAP_PER_TECH_GW["MISO"]["solar"]` |
| growth-ladder cap, year 1 | 1.236 GW | 2.0 × the measured EIA-860 seed 0.618 GW |

The ladder seed is measured, not assumed:
`max_annual_build_gw_by_tech("MISO", 2020, 10, vintage_2020)` returns
`{coal 1.766, gas_cc 1.723, gas_ct 0.742, oil 0.063, solar 0.618, wind 4.367}` GW.
**No cap is zero**, so no cap can produce a zero by itself.

### 4.2 The D-2 dampers — **ELIMINATED as the cause of the zero** (they are the ceiling, §5)

`entry_rate_limits` and `entry_commissioning_lag` are both armed in this leg.
Neither can produce a zero: in `apply_economic_new_entry` a technology is only
reached by the cap logic **after** it has entered `margins`, which requires
`margin > 0.0`. An unprofitable candidate never reaches a cap at all — the
ledger's own `binding_cap` field distinguishes `"unprofitable"` from
`"growth_ladder"` / `"per_tech_cap"` / `"iso_budget_exhausted"` precisely here.

Addendum D's HOLD PROMOTION is honoured: nothing was unarmed anywhere, and no
revert is recommended. No paired control was run, because the ledger's
`profitable` flag answers the distinguishing question directly and a control
would have cost four more solve-years to reproduce a zero that is already
explained.

### 4.3 The planned-additions channel (step 4) — **ELIMINATED, and it is a separate structural gap**

`load_planned_additions` (`data/fleet/eia860.py:1916`) **skips wind, solar,
hydro and storage entirely** — `_map_fuel_type` returns `None` for them, by
design ("renewable capacity growth is handled by the zonal `wind_cap` /
`solar_cap` pools"). Measured: **all 42** MISO committed-proposed solar rows in
`vintage_2020/eia860_generator_proposed.parquet` map to `None`.

So the answer to "is the planned channel delivering solar the economic screen
never adds to?" is **no — it delivers none, ever, in any ISO**. Confirmed on
the other side too: `renewable_additions` (runner.py:1124–1127) is the **only**
writer of `solar_cap`, and its sole upstream is `evolve_fleet`'s economic screen
plus the commissioning pipeline. **The economic screen is a single point of
failure for all solar in every forecast.**

That said it **cannot** be the explanation for this leg's magnitude: MISO's
committed proposed solar at vintage 2020 (statuses U/V/TS, effective year >
2020) totals **1.034 GW** against an 18.649 GW actual. Worth closing on its own
merits; not this residual.

### 4.4 The zonal siting of new solar — **tested, NOT the cause**

`RENEWABLE_ZONE_ALLOCATION["MISO"]["solar"] = "MISO-South"`, so 100 % of
screened solar is valued at, and built into, one zone. Measured against
EIA-860 v2024 with the model's own state→zone map, MISO's 2021–2024 solar COD
splits South 3.475 / East 2.822 / Illinois 2.408 / Indiana 1.125 / Plains 1.042
/ West 0.620 GW — **MISO-South is genuinely the largest single zone (30 %)**, so
the allocation is defensible even though concentrating every build there is a
siting-realism simplification.

It is moot for this leg anyway: `entry_lookahead_reprice` is **on** (harness
default, and recorded `true` in the registered leg's meta), and
`_lookahead_reprice_signal` returns a **system-wide** signal — "every zone sees
the same stack price" (runner.py:446). The screen's price signal carries no
zonal differentiation at all, so the choice of MISO-South changes only the CF
profile, not the price.

### 4.5 The vintage capacity ramp — **tested, INERT in this leg** (a live trap for other lanes)

Under the canonical EIA-860 snapshot, `vintage_capacity_ramp` (default **True**)
depresses MISO-South's *annual mean* solar CF to 0.105 (2023) / 0.139 (2024) /
0.194 (2025), because the zone's own plants commission mid-year. Had that fed
the screen it would roughly double solar's shortfall.

**It does not, here.** A 2020-vintage hindcast calls `set_eia860_vintage(2020)`
before `load_renewable_profiles`, and the vintage-2020 sheet has no post-2020
CODs to ramp, so every MISO zone's solar CF is a flat **0.22** in every year of
this leg — measured both ways:

| basis | 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| canonical snapshot, ramp on (MISO-South) | 0.2174 | 0.1048 | 0.1392 | 0.1944 |
| **vintage 2020, ramp on (this leg)** | **0.2195** | **0.22** | **0.22** | **0.22** |
| vintage 2020, ramp off | 0.2195 | 0.22 | 0.22 | 0.22 |

Recorded because a future lane reading the canonical-vintage numbers would
reach the wrong conclusion. In a *backcast* the ramp is correct — it represents
the fleet that actually existed.

### 4.6 The revenue side — **THIS IS THE CAUSE, together with §4.7**

Solar's screened revenue, term by term, at the shipped config:

* **Energy.** `estimate_expected_revenue(prices_for_rev, cf_profile)` =
  Σₜ pₜ·cfₜ per MW-yr, on the system lookahead signal (§4.4) and a flat 0.22 CF
  (§4.5).
* **Attribute payment** = `max(effective_eac_price_for_tech, rps_shadow_price)`.
  Both are **zero**. The EAC/CES premium is 0.0 for solar in every year
  2021–2025 at the shipped config (measured). The RPS shadow price is zero
  because **MISO's RPS is slack by construction**: `get_rps_target("MISO", y)`
  is 0.11 through 2025, while the forecast pools alone put modelled VRE at
  32,000 MW × 0.34 + 7,000 MW × 0.22 = **108.8 TWh on 644.6 TWh of MISO load =
  16.9 %**. A slack constraint has a zero dual, so the REC channel pays nothing.
* **RA / capacity.** **Zero, by an armed gate.** `entry_vre_capacity_revenue`
  is default-**OFF**, so the whole `vre_capacity_payment` block
  (`new_entry.py:1007–1027`) is skipped. Everything needed to pay it resolves
  cleanly at head: `MARKET_DESIGN["MISO"].net_cone_per_kw_yr = 79.8` →
  **$79,800/MW-yr per firm MW**, and
  `resolve_renewable_capacity_credit("solar", "MISO", curves_enabled=True)` =
  **0.18**. The credit MISO solar is denied is **$14,364/MW-yr**.

  This is a genuine **asymmetry inside one screen**: the thermal branch
  (`new_entry.py:899–905`) credits `capacity_revenue_per_mw_yr(...)`
  **unconditionally**, with no gate. In a capacity-market ISO, thermal entry is
  paid for accredited capacity and VRE entry is not.

### 4.7 The cost side — **correct in construction; two identified input issues**

`compute_lcoe("solar", …)` is `capex → Wright → ITC → CRF → +FOM`, and
`annual_cost = lcoe × 8760 × base_cf` is **exactly** `(capex·CRF + FOM)×1000`
— `base_cf` cancels, so the cost is genuinely CF-independent and the docstring's
claim holds. Measured trajectory (ATB 2024 Moderate UtilityPV/Class5 @2026, in
2026$, learning from `WRIGHT_REFERENCE_GW["solar"]=1800` at +400 GW/yr):

| year | cum GW | capex base | after Wright | after 30 % ITC | CRF | **$/MW-yr** | **BE $/MWh** | BE if RA credited |
|---|---|---|---|---|---|---|---|---|
| 2021 | 1800 | 1562.2 | 1562.2 | 1093.5 | 0.0701 | **99,003** | **48.93** | 41.83 |
| 2022 | 2200 | 1562.2 | 1464.5 | 1025.1 | 0.0701 | **94,204** | **46.55** | 39.46 |
| 2023 | 2600 | 1562.2 | 1387.8 | 971.5 | 0.0701 | **90,440** | **44.69** | 37.59 |
| 2024 | 3000 | 1562.2 | 1325.3 | 927.7 | 0.0701 | **87,372** | **43.18** | 36.08 |
| 2025 | 3400 | 1562.2 | 1273.0 | 891.1 | 0.0701 | **84,802** | **41.91** | 34.81 |

*(break-even mean price at CF 0.22 and a capture ratio of 1.05 — see below)*

The ITC treatment is **right**: a one-time investment credit belongs on capex
before annualization, and that is where it is. Two input issues are flagged,
neither tuned here:

1. **The screening CF is the ISO fleet mean, not the siting zone's resource.**
   `RENEWABLE_AVG_CF["MISO"]["solar"] = 0.22` is applied to every zone. A new
   tracking plant in MISO-South (AR/LA/MS) is a materially better resource than
   the MISO fleet average, which is weighted by northern fixed-tilt. Under rule
   14 the accurate input for a *new MISO-South plant* is MISO-South's own
   resource. At CF 0.25 the 2023 break-even falls $44.69 → $39.31/MWh.
2. **The learning curve is anchored to a calendar-blind stock.**
   `CumulativeDeployment.initial()` starts at the IRENA-2025 reference 1800 GW
   in the run's *first* year whatever that year is, then adds 400 GW/yr — so a
   2021-start hindcast prices 2025 solar at a 3400 GW global stock the world
   reaches around 2029. **This biases the screen towards building**, not away,
   so it cannot be the cause of the zero; recorded for completeness.

### 4.8 Capture shape — measured, and it is not the problem

Using the MISO keeper `miso126_steampart_B`'s committed MISO-South hourly P1
prices against the measured EIA-930 MISO solar generation shape, the solar
**capture ratio** (capture price ÷ mean price) is **1.055 / 1.053 / 1.071** in
2023 / 2024 / 2025 — solar captures *above* the mean at MISO's current
penetration. Value cannibalization is not suppressing this screen.

*(Clearly labelled: this is a keeper **backcast** price series used as a
level/shape proxy for the sensitivity. It is **not** the hindcast's own entry
price signal — that is §3's job.)*

---

## 5. The second, independent blocker: the ladder cannot ratchet under the COD lag

This is arithmetic on the code, not a measurement of this leg (solar decides
zero, so the leg never exercises it) — but it bounds what any fix could
achieve, and it is checkable.

`entry_rate_caps_mw[tech] = 2.0 × prior_max_gw[tech] × 1000`
(`ENTRY_GROWTH_LIMIT_MULTIPLE`, the ReEDS hard bound), and the ladder budget is
netted by the **pending pipeline**:
`_ladder_remaining = max(0, cap − pending_by_tech)` (`new_entry.py:1140–1148`).
`prior_max_gw` rises only when a year's decision **exceeds** it
(runner.py:1094–1100). With `ENTRY_COD_LAG_YEARS = 2`, exactly one year of
decisions is pending at any time. Writing M for the prior max:

| decision year | ladder cap | pending | remaining | decides | new prior max |
|---|---|---|---|---|---|
| 2021 | 2M₀ = 1.236 GW | 0 | 1.236 | 1.236 | M₁ = 1.236 |
| 2022 | 2M₁ = 2.472 | 1.236 (2021, COD 2023) | 1.236 | 1.236 | 1.236 (no rise) |
| 2023 | 2.472 | 1.236 (2022, COD 2024) | 1.236 | 1.236 | 1.236 |
| … | … | … | … | 1.236 | **frozen** |

**The doubling is exactly cancelled by the one year of pending MW, so economic
entry is pinned at 2 × the measured seed forever.** For MISO solar that is
1.236 GW/yr; the three in-window decision cohorts commission in 2023/2024/2025
for **≈3.71 GW**, a −80 % FC-3 additions band at best.

This reconciles with FFR-2B's observation that the MISO gas_ct ladder *did*
double (1,350 → 2,700 → 5,241 MW): that channel was the **reserve-margin
backstop**, which commissions **in-year**, so it never nets a pending row and
the ratchet works. **The ladder ratchets for the backstop and freezes for
economic entry** — a structural asymmetry between two consumers of the same
budget. Recorded as an observation; whether it is a defect or the intended
conservatism is an owner call.

---

## 6. Two adjacent defects found while instrumenting (reported, not actioned)

### 6.1 The hindcast's renewable pools are NOT vintage-initialized

`load_renewable_profiles` gates the vintage branch on
`is_backcast = config.mode == "backcast"` (`renewables.py:2327`). A capacity
hindcast is **`mode="forecast"` + `hindcast=True`**, so it falls through to the
canonical constant `RENEWABLE_INSTALLED_MW["MISO"]["solar"] = 7,000 MW`.

Measured: **vintage_2020's own EIA-860 MISO solar operable nameplate is
2.056 GW** (vintage_2024: 13.575 GW). A 2020-vintage MISO hindcast therefore
starts holding **3.4× the solar that existed at its vintage** — post-vintage
information in a run whose entire premise is the vintage cutoff. Zone *shares*
and the monthly ramp do come from vintage 2020; only the total does not.

It compounds this lane's finding: `_lookahead_reprice_signal` subtracts the
current year's VRE output from next year's demand before pricing the stack, so
an over-seeded solar pool depresses the very price signal the solar screen is
judged against.

### 6.2 The wind PTC is credited over 30 years; §45 runs 10

`apply_ira_credits_to_lcoe` (`policy/ira.py:248–251`) and `compute_lcoe`'s wind
branch subtract the full `ira_ptc_wind` = $26/MWh from the levelized cost with
**no credit window**, so it is earned for the plant's whole 30-year life. IRC
§45 (and the tech-neutral §45Y) run **10 years from placed-in-service**.

The codebase already contains the correct, zero-DOF pattern — `_emerging_lcoe`
levelizes §45Q by exactly `CRF(life)/CRF(window)` with an explicit
`ira_45q_credit_window_years = 12` (`new_entry.py:264–271`). Applying the same
construction to §45:

| | as screened | levelized over 10 yr |
|---|---|---|
| effective PTC | $26.00/MWh | **$13.63/MWh** (× CRF(30)/CRF(10) = 0.5243) |
| credit booked, wind | **$86,549/MW-yr** | ≈ $45,378/MW-yr |
| credit booked, solar (ITC) | $26,787–32,873/MW-yr | unchanged (already correct) |
| wind break-even mean price, 2023 | **$19.32/MWh** | ≈ $33/MWh |
| solar break-even mean price, 2023 | **$44.69/MWh** | $44.69/MWh |

That 2.3× hurdle gap is the mechanical origin of the leg's inverted tech mix
(model wind 43.7 % share / solar 0.0 % vs actual 22.5 % / 58.3 %). Correcting it
does **not** make solar build — solar's own margin is negative on its own terms
— but it is a real, identified, zero-free-parameter defect on the same screen.

---

## 7. What I would propose (owner's call — a diagnosis lane does not land its own fix)

Ranked by evidence strength, each with the measurement that supports it. **None
of these was applied.**

1. **Arm `entry_vre_capacity_revenue` for MISO** (and re-examine it wherever
   `MARKET_DESIGN` has a capacity market). Evidence: the payment resolves
   cleanly today ($79,800 × 0.18 = $14,364/MW-yr), it moves solar's break-even
   from $41.9–48.9 to $34.8–41.8/MWh, and the thermal branch already takes the
   same payment **ungated** — the asymmetry is inside one function. It is the
   single largest identified omission on solar's revenue side and the code
   exists. This is the "D-2′ HELD pending its own probe row" cell in the
   `entry_dampers` matrix row; this session is the evidence for opening that probe.
2. **Window the §45 wind PTC** with the existing `_ccs_45q_window_years`
   pattern. Zero free parameters, one published statutory number (10 years),
   and a precedent in the same file. Expect wind additions to fall — under rule
   1 that is the faithful direction, not a regression.
3. **Give the VRE screen the siting zone's own resource CF** rather than the
   ISO fleet mean, per rule 14. Smaller, and it needs its own derivation.
4. **Close the hindcast renewable-pool vintage leak** (§6.1) — a one-line gate
   widening (`mode == "backcast" or config.hindcast`), but it changes every
   hindcast's base fleet, so it belongs to whoever owns the T1-H lane.
5. **Decide whether the ladder freeze (§5) is intended.** Even with 1–3 done,
   FC-3 solar cannot clear −15 % while the ceiling is 3.7 GW.

---

## 8. What I did NOT separate

Stated explicitly, because the decomposition above is additive only where I say
it is:

* **I did not separate the RA-payment gate from the CF input from the price
  level by running arms.** §4.6/§4.7 are a *decomposition of one measured
  screen*, plus break-even sensitivities. Which combination first flips the sign
  in the leg's own solve is untested; only the measured margin in §3 is a
  measurement.
* **I did not run a paired damper control.** The ledger's `profitable` flag
  distinguishes margin from cap without one (§4.2), and Addendum D forbids
  unarming outside an explicitly-labelled control. §5's ceiling is code
  arithmetic, not a measured arm.
* **I did not test the §6.2 PTC fix or the §6.1 vintage fix.** Both are
  proposals with their arithmetic shown; neither was implemented, so neither has
  a measured effect on any band.
* **I did not attribute the wind (−44 %), gas_cc (−70 %), gas_ct (−100 %) or
  storage (+438 %) FC-3 misses.** They share this screen and some of them
  probably share §6.2, but this lane's question was solar.
* **I did not re-score the registered leg**, and no number here supersedes a
  band on `miso-2021-2025-realized-ffr3a3`. §3's run is a separate,
  diagnostics-on solve under its own out-dir and is not registered (rule 15
  registers *backcast* runs; this is a forecast-family diagnostic probe with no
  scored output).
* **Rule 25:** every number here is derived from MISO's own data and code paths.
  No parameter, verdict or piece of evidence was imported from another ISO's
  lane, and nothing here fills another ISO's cell.
