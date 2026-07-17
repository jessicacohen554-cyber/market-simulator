# Offer-Curve Methodology

This section documents how the simulator turns each thermal plant into a
rising **offer curve** for the dispatch LP: the bid tranches that make up
the curve, the smooth *n*-slice ramp used in the economic window, and the
CAMPD-derived unit-outage data used to constrain availability in backcast
runs.

The unit of representation is the plant: **one EIA plant = one LP
generator** (a single facility whose coal and gas-steam units coexist —
e.g. W A Parish — splits into one bin per `Plant_Group`). Each plant
dispatches on its own measured `Plant_Avg_HR_MMBtu_MWh`; there is no
bin-weighted heat rate. Every tranche described below is priced as that
plant's own base heat rate scaled by a tranche multiplier, and **no
tranche carries a hard `pmin` floor** — minimum-load behaviour emerges
from the Committed and Must-Run tranches bidding cheaply, not from a
binding lower bound.

---

## 1. The offer-curve tranches

Each plant's nameplate capacity is split into a small set of bid
tranches that, stacked from cheapest to most expensive, form a rising
offer curve. The tranches and their LP treatment are:

| Tranche | Meaning | Bid / LP treatment |
|---------|---------|--------------------|
| **Must-Run BTM (CHP)** | Behind-the-meter steam-host load at cogeneration plants (`CC_CHP`, `CT_CHP`). Fixed by a steam contract, not by market economics. | **Removed from the LP capacity.** Its generation and CO₂ are reconstructed in post-processing, not cleared in the dispatch. |
| **Must-Run (coal / lignite)** | The sunk-fuel baseload floor a coal unit holds even at low prices. Coal fuel is take-or-pay, so its fuel cost is sunk. | Bids at **VOM only** (fuel sunk); pins the coal plant's baseload behaviour without a hard `pmin`. Coal only — `0%` for gas groups. |
| **Committed (%)** | Minimum stable load once the unit is started — the floor it backs down to rather than shutting off. | Cheap block at `base_hr × offer["committed"]` (≈ **0.92×**). Carries the unit's start cost and min-run / min-down windows, and is the **only tranche screened** by the commitment layer. |
| **Econ-Low** | The bottom of normal incremental dispatch above the committed floor. | First reach of the economic ramp; `base_hr × offer["econ_low"]`. |
| **Econ-High** | The top of normal incremental dispatch, approaching full load. | Top reach of the economic ramp; `base_hr × offer["econ_high"]`. |
| **Peak** | Duct-firing / scarcity output with a steep incremental cost. | For CC/coal, **folded into the top of the economic ramp** (peak is the ramp endpoint); for CT/ST it stays a **separate flat scarcity tranche**. |

The `Pct_*` shares sum to 100% per plant. Capacities are split as:

```
mustrun_cap   = nameplate * MR%  / 100            # coal only (sunk fuel);
                nameplate * (1 - MR% / 100)        #   for CHP this is the
                                                   #   off-grid steam host
committed_cap = grid_cap * MC%   / (100 - MR%)
peak_cap      = grid_cap * PEAK% / (100 - MR%)
econ_cap      = grid_cap - committed_cap - peak_cap
```

### Must-Run BTM for CHP

At cogeneration plants the must-run tranche represents the **behind-the-meter
steam host**: process steam the plant is contractually obliged to produce
regardless of the power price. Because that output is not dispatchable, it
is **removed from the LP capacity entirely** so it never competes in the
energy stack. After the LP clears, `compute_must_run_emissions()`
reconstructs the host generation and its CO₂ for the asset-level emissions
trajectories:

```
share       = btm_share_by_plant.get(plant, MR% / 100)   # measured host share, else bin MR%
mr_mw       = nameplate * share
cf          = class_cf_by_group.get(plant_group, must_run_cf)  # measured class CF, else 0.85
mr_gen_mwh  = mr_mw * 8760 * cf
mr_co2_tons = mr_gen_mwh * emission_rate    # plant's measured rate when covered, else fuel-class default
```

`btm_share_by_plant` prefers a measured per-plant host self-supply share over
the flat bin `MR%`: the backcast caller sizes it from `chp_btm_pct` (sector
default / per-plant override), the forecast caller from the measured
`chp-btm-share` clean datatype (`data.chp.measured_btm_share_by_plant`) — see
`docs/binning-methodology.md`. This applies to `CC_CHP`, `CT_CHP` and
`ST_CHP`.

### Must-Run for coal / lignite

For coal (including lignite), the must-run tranche is the **sunk-fuel
baseload floor**. Coal fuel is procured take-or-pay, so once contracted its
cost is sunk; the must-run block therefore bids at **VOM only**, which keeps
the coal unit running through all but the deepest low-price spells without
imposing a hard `pmin`. Lignite, as a mine-mouth coal supply class, follows
the same treatment but carries its own per-plant delivered fuel cost (see
the calibration notes — lignite mine-mouth vs railed PRB are priced
separately where EIA-923 reports them). The size of the coal must-run floor
is derived per plant from CAMPD rather than assumed (see §3).

### Committed, Econ-Low, Econ-High, Peak

Above the must-run floor, the **Committed** block is the minimum stable
load the unit holds when backed down — a cheap block (≈ `0.92× base_hr`)
that also carries the unit's start cost and min-run/min-down windows and is
the only tranche the commitment screen evaluates. Above it, the
**Econ-Low → Econ-High** region is normal incremental dispatch as price
rises, and the **Peak** tranche is duct-firing or scarcity output. The
committed share is not a coarse class assumption: for combined cycles it is
derived per plant from each unit's own CAMPD record (see §3), applied via
`CC_REGULAR_COMMITTED_PCT_BY_PLANT` under the ERCOT default and via the
per-ISO `thermal_tranches_<ISO>.csv` artifact elsewhere. For per-ISO
artifacts that carry it (CAISO onward), the CC **peaking share** is likewise
measured per plant (`peaking_pct`, consumed by
`fleet.thermal_tranche_peaking` under `cc_peaking_per_plant`): the share of
the plant's demonstrated sustained maximum (P99.5 of online net MW) it
clears in fewer than 5% of its online hours — the duct-firing / scarcity
reach — superseding the offer curve's class-wide `pct_peaking`.

Whenever an offer curve is configured for the group (the ERCOT default),
the band heat rates come from the curve, **not** from the CSV `HR_Mult_*`
columns:

```
committed_hr = base_hr * offer["committed"]                      # e.g. 0.92×
econ ramp    = base_hr * mult(t),  mult: econ_low → econ_high     # n-slice ramp (§2)
peak (CC)    = base_hr * cc_duct_burner_peak_mult(turbine_class)  # 2.0–2.5×, SEPARATE flat tranche above the ramp
```

---

## 2. The *n* = 6 smooth-slope curve in the economic window

The economic window — the capacity between the Committed floor and the top
of the curve — is **not** rendered as one or two flat blocks. Instead it is
sliced into a smooth, rising heat-rate ramp by `_econ_curve_steps`, so the
unit fills gradually as the hourly price clears each successive step rather
than snapping between flat bands.

The economic capacity is divided into `config.offer_curve_smoothing_n`
**equal-capacity** slices, and slice *k* (for *k* = 0 … *n* − 1) is priced
at:

```
mult(t) = lo + (pk − lo) * t**exp        t = (k + 0.5) / n
hr_step_k = base_hr * mult(t)
```

with the active ERCOT values:

- **`n   = offer_curve_smoothing_n`  (default 6)** — the number of
  equal-capacity slices in the economic window.
- **`exp = offer_curve_smoothing_exp` (default 1.0)** — the ramp shape;
  `1.0` is a straight linear ramp, `exp > 1` is convex (cheap-bottomed).
- **`lo  = offer_curve_by_group[group]["econ_low"]`** — the multiplier at
  the bottom of the ramp (CC_REGULAR ≈ 1.06–1.16).
- **`pk`** — the top of the ramp: `offer_curve_by_group[group]["econ_high"]`,
  the econ-high multiplier. This is the **ramp endpoint for every group**; the
  duct-firing / scarcity peak is *not* a ramp endpoint (see below).

Each slice carries no min-run hours and no start cost — it is incremental
output of an already-committed unit. The midpoint sampling `t = (k+0.5)/n`
places each slice's price at the centre of its capacity band, so the six
slices step smoothly from `≈ base_hr × econ_low` up to
`base_hr × econ_high`. A CC plant is therefore a cheap Committed block at
`base_hr × 0.92` followed by **six rising slices** scaled entirely by its
own `base_hr`.

**Uniform shape across groups — the peak is always separate.** Every thermal
group uses the *same* construction (`fleet.py` `_econ_curve_steps`, see the
module comment "Nothing is folded into the ramp"): the smooth economic ramp
spans `econ_low → econ_high`, and the duct-firing / scarcity **peak band is
kept as a SEPARATE flat tranche appended above the ramp top** — its capacity
set by `pct_peaking`, its height by the `peak` multiplier (the per-turbine-class
`cc_duct_burner_peak_mult` for CC when no explicit `peak` is given; an explicit
`offer_curve_by_group[group]["peak"]` otherwise). There is **no** "fold the peak
into the ramp" branch — the former `_CURVE_FOLD_PEAK` / `_CURVE_ECON_ONLY`
distinction no longer exists in the code.

The *n*-slice ramp engages only when `offer_curve_smoothing_n > 0`,
`econ_cap > 0`, and `pk > lo`; otherwise the model falls back to two flat
economic blocks (econ-low / econ-high).

**Why this matters for calibration.** Because the ramp anchors on the
plant's annual-average `base_hr` and starts at `econ_low`, the slope and
the `econ_low` multiplier — together with the per-plant committed share —
are the primary levers for whether a single plant over- or under-runs
relative to its CAMPD history. A flexible cycler whose true full-load
incremental heat rate beats its annual average has its slices priced a
little high and tends to under-run; the fix is `econ_low` / the ramp slope
/ the `base_hr` definition, not the tranche structure.

---

## 3. Backcasting unit-outage data from CAMPD

Forward (forecast) runs use the statistical WEFOR/POF availability model.
**Backcast runs instead overlay actual sustained outages** measured from
EPA CAMPD (Clean Air Markets Program Data) hourly CEMS gross generation for
the historical year. The overlay is applied only when a backcast config
sets `outage_source == "historic"`; the hourly availability mask it builds
is:

```
availability[g,t] = (1 - EFORd[g]) * seasonal_factor[g, month(t)] * outage_mask[plant_code][t]
```

CAMPD is also used to **derive the tranche sizes** themselves — each
plant's committed % and coal must-run % (§1) — so both the offer-curve
shape and the availability are grounded in the plant's own observed
behaviour rather than coarse class assumptions.

The outage overlay answers "was a *built* unit running?"; a separate
**commercial-operation-date (COD) vintage ramp** answers "was the unit *built*
yet?" — the fleet snapshot is a recent vintage, so a backcast must drop capacity
commissioned after the solved year (and add back the months a mid-year-COD unit
was online). That ramp is sourced from EIA-860 (not CAMPD, which has no build
dates), covers every fleet path including the CAMPD bins, and is on by default
for backcasts (`cod_ramp_enabled`). See
[`docs/cod-vintage-ramp.md`](cod-vintage-ramp.md).

### Outage detection: thresholds on days without running

A unit is flagged as on outage when its CEMS output shows it is **not
really running for a sustained number of days**. Two rules are applied,
chosen by the unit's fuel, because what an output gap *means* depends on
how the unit is normally run:

| Fuel / role | Rule | "Running" threshold | Minimum outage length |
|-------------|------|---------------------|-----------------------|
| **Coal (baseload)** | Real-run / averaged | Sustained CF **> 5%** (`REAL_RUN_CF`) held for **≥ 24 h** (`MIN_REAL_RUN_HOURS`) counts as a real run; everything else is "not running". | Maximal not-running span of **≥ `--min-outage-days`** (typically **≥ 5 days**). |
| **Combined cycle / gas-steam (load-following)** | Event-based | A window is broken by **any single hour** with CF **≥ 2%** (`ST_GAS_CF_PEAK`). | A maximal span with **every** hour below 2% lasting **≥ 120 h ≈ 5 days** (`ST_GAS_MIN_OUTAGE_HOURS`). |

**Coal (baseload) — the real-run rule.** Coal runs continuously when
available, so a multi-day gap genuinely marks an outage. A "real run" is a
spell of CF above **5%** sustained for at least **24 hours**; outage
windows are the complementary not-really-running spans that last at least
the `--min-outage-days` floor (typically **5 days**). The 5% CF threshold
(rather than 0%) means a unit idling at 5–10% CF — e.g. J K Spruce, or a
low-output baseload unit — is **not** mislabelled as out, while genuine
full-off gaps are still caught. The 24-hour real-run minimum prevents a
brief test spike from prematurely ending an outage.

**Combined cycle / gas-steam — the event-based rule.** These units are
load-following: an idle hour is usually economics, not a forced outage, so
the averaged coal rule would badly over-flag a merchant turbine that simply
isn't dispatched. The event-based rule flags an outage only when the unit
produced essentially nothing — CF below **2%** for **every** hour of the
span — for at least **120 hours (5 days)**. **Any single hour at or above
2% CF breaks the window**, so an economically-idle-but-occasionally-firing
unit is left to the economic dispatch instead of being called out.

### Unit-level detection (the sole CAMPD outage source)

The per-unit detector (`scripts/derive_campd_unit_outages.py`) reads the
per-unit CAMPD extracts and runs the *same two rules per unit* (coal →
real-run, everything else → event-based), so it catches a single-unit outage at
a multi-unit plant and, critically, a **coal-unit outage hidden behind running
gas units** at a mixed facility (W A Parish, Barney M Davis). Each detected unit
outage derates that unit's capacity share of its model bin over the window; a
genuinely single-unit plant (unit capacity = plant-bin capacity) is fully
zeroed. The shared detection primitives live in
`scripts/lib/outage_detect.py`.

> The old **facility-level** detector (`scripts/derive_campd_outages.py` →
> `campd-outages*.csv`, a hard `availability=0` per plant) was **removed
> 2026-07-17**: summing a plant's units hid single-unit outages, and it folded a
> daily-cycling combined cycle's overnight-down gaps into phantom summer outages
> (`results/calibration/FINDING-ercot79-phantom-outage-2026-07.md`). The
> per-unit detector — event-based for load-following classes — never had that
> bug, so it is now the sole CAMPD outage layer for every ISO.

### Scope and overlay rules

- Only **coal and combined-cycle** plants (`QUALIFYING_PLANT_GROUPS`) are
  overlaid; at a mixed-bin plant only the qualifying coal/CC bin is zeroed.
- **Combustion turbines** (`CT_PEAKER` *and* `CT_CHP`) carry no outage
  overlay — they dispatch purely economically, and the revealed-availability
  filter cannot certify a CT down-window as a forced outage vs out-of-merit at
  peak (unlike baseload coal/CC, where down-at-peak reliably implies an outage);
  the spiky-running `ST_GAS_PEAKER_PLANTS` are likewise excluded. (The detector
  still writes CT_CHP windows to the extract for audit, but the derate skips
  them.)
- The overlay applies every unit window the detector emits, guarded by a minimum
  span of **5 days** (`UNIT_OUTAGE_MIN_DAYS`); detection is
  per calendar year, and a window straddling Dec 31 is clipped at the year
  boundary with each side independently clearing the duration floor.

The output is a schema-compatible CSV
(`oris_code, plant_name, unit, outage_start, outage_stop, duration_hours`)
consumed by the historic-outage overlay. (The `duration_hours` column is
informational only; the overlay measures length as
`outage_stop − outage_start`.)

### Detection coverage: CEMS-measured vs statistical

The historic overlay only reaches a plant for a year in which that plant's
units appear in the CAMPD CEMS extract for that year; everything else falls
back to the statistical WEFOR/POF availability model. Coverage therefore
splits three ways — **measured** (a CEMS unit-outage window overlays the
statistical model), **statistical** (qualifying fossil bin, but no window
landed — either the unit ran without a sustained dead span, or no CEMS
extract exists for that year), and **no overlay by design** (combustion-turbine
peakers and the listed `ST_GAS_PEAKER_PLANTS`, which dispatch purely
economically).

**NYISO worked example.** NYISO has **no coal** in its CEMS data, so the
coal real-run rule (`detect_outages`) fires on **zero** units — every NYISO
unit is detected by the load-following **event-based** rule
(`detect_outages_eventbased`: a window is broken by any single hour ≥ 2% CF
and must run ≥ 120 h). The qualifying fossil fleet (CC + sustained ST_GAS,
`QUALIFYING_PLANT_GROUPS` minus the peaker exclusions) totals **≈ 21.2 GW**
across 65 plants:

| Coverage | Plants | Capacity | Source |
|----------|-------:|---------:|--------|
| **CEMS-measured** (unit-outage windows) | 44 | ≈ 18.9 GW (**89%**) | `campd-unit-outages-NYISO.csv` (2023 + 2025) |
| **Statistical** (qualifying, no window) | 21 | ≈ 2.3 GW (11%) | WEFOR/POF |

Outside this qualifying set, **≈ 2.6 GW** of `CT_PEAKER` and a further
**≈ 2.9 GW** of unbinned oil peakers carry **no overlay by design** and
dispatch economically, while nuclear and biomass use their own availability
models. The big NYC / Hudson-valley oil-gas steamers — Ravenswood, Astoria
Generating, Roseton, Danskammer, Bowline — sit cold for long stretches and
the event-based rule resolves each cold spell into its own window (e.g.
Danskammer 2480 ≈ 1.4 k unit-outage-days/yr, Bowline 2625 ≈ 0.5–0.6 k),
whereas the modern baseload CCGTs (Astoria Energy 55375, Cricket Valley
57185) run far more and carry only short, sparse windows.

**The 2024 gap.** No `campd-unit-level/NY_2024.parquet` CEMS extract has
landed, so a NYISO **2024** backcast has *no* measured windows in either
overlay layer and degrades entirely to the statistical model — the
`unit_outage_derate_factors` lookup returns an empty dict for 2024 and
`generators_to_fleet_arrays` logs the statistical-only fallback. The CSV
covers **2023 and 2025 only**; it regenerates byte-identically from the
present extracts and adds 2024 automatically once `NY_2024.parquet` is
supplied.

> **A note on the unit-outage CSV vs the tranche shares.** The unit-outage
> windows above (`campd-unit-outages-NYISO.csv`) are 2023 + 2025 only,
> because they read the *unit-level* CEMS extracts and no unit-level 2024
> file exists. The committed / peaking *tranche* shares in
> `thermal_tranches_NYISO.csv` are derived over **2023 + 2024 + 2025**: that
> derivation reads the *facility-level* hourly net (`load_campd_hourly`),
> and the facility-level `NY_2024.parquet` *is* present, so the extra year of
> dispatch history sharpens each plant's measured minimum-stable-load and
> duct-firing reach even though 2024 outage windows are still missing.

### NYISO inflexible layer (no coal must-run)

NYISO's CEMS data has **zero coal rows**, so the offer curve carries **no
coal must-run tranche** — the sunk-fuel baseload floor that pins ERCOT/PJM
coal simply has no NYISO target (`mustrun_pct` is `0.0` for every NYISO
plant-group). The genuinely inflexible NYISO generation is instead:

- **CHP behind-the-meter steam hosts** — removed from LP capacity and
  reconstructed in post-processing (§1; sized from the P3 CHP floors in
  `thermal_tranches_NYISO.csv`).
- **Nuclear** (FitzPatrick, Nine Mile 1 & 2, Ginna ≈ 3.3 GW upstate) on its
  monthly-CF baseload model; Indian Point is retired (Units 2/3, 2020/2021)
  and absent from the 2023+ fleet.
- **Hydro min-flows** — the Niagara / St-Lawrence treaty-mandated minimum
  flows (`nyiso_hydro_treaty_min_flow`).
- **Reliability-must-run (RMR) units.** NYISO designated the four NYC peaking
  barges — **Gowanus 2 & 3 (EIA 2494) and Narrows 1 & 2 (EIA 2499)**, ≈ 565
  MW nameplate / 508 MW reliability capability — as RMR to keep them online
  past their planned 1 May 2025 deactivation, addressing the NYC reliability
  deficiency in NYISO's Q2-2025 Short-Term Assessment of Reliability.[^nyiso-rmr]
  That designation begins **after** the 2023 + 2025 backcast window, so the
  model treats both barges as ordinary economic `CT_PEAKER` units (each a
  measured single-digit committed floor, no must-run pin) rather than forcing
  them on — the correct historical behaviour for the backcast years.

[^nyiso-rmr]: NYISO, "PRESS RELEASE | NYISO Identifies Solution to Solve New
York City Reliability Need" and "Future New York City Electric Grid
Reliability Deficiency Explained," nyiso.com (2024); reported in Utility Dive,
"NYISO to keep 4 NYC peakers running past planned 2025 retirement to maintain
reliability" (2024).

---

### NEISO inflexible layer (no coal must-run) and the oil / dual-fuel peaker band

NEISO's committed / peaking tranche shares are derived per plant from the
**2023 + 2024 + 2025** NE-state facility-level CEMS (`ME, NH, MA, CT, RI, VT`),
the same `derive_thermal_tranches.py` machinery used for the other ISOs, and
emitted with per-row source tags as `data/raw/_processed-legacy/bin_assignments_NEISO.csv`.
The pooled three-year window gives strong CAMPD coverage of the dispatchable
fleet: **100%** of CC_REGULAR capacity (≈ 12.8 GW), **≈ 87%** of CC_CHP, and
**≈ 89%** of CT_PEAKER capacity carry a *measured* committed share; the rest —
the sub-CEMS fuel-cell / micro-cogen tail — keeps the class default. The same
artifact carries each combined cycle's measured duct-firing **peaking** share
(P95 vs P99.5 of online net MW, capped at 25%), applied under
`cc_peaking_per_plant`.

**No coal must-run tranche.** NEISO's only operating coal unit is **Merrimack**
(EIA 2364, Bow NH; Granite Shore Power). EIA-860 carries unit 1 (113.6 MW
nameplate / 108 MW net summer, `BIT`, status `OP`, planned retirement 2027) as
operating across the whole 2023-2025 window and the larger unit 2 (345.6 MW,
`BIT`, status `OS`) as out of service, so the dispatched coal capacity is the
~108 MW unit 1 — confirming the EIA-930 ISNE coal column (0.18/0.24/0.28 TWh)
is a low-CF winter-peaking run, not zero and not a baseload. Its **coal rank is
derived, not assumed**: `scripts/derive_coal_supply.py --iso NEISO` sums the
plant's EIA-923 Schedule-5 fuel receipts (54,050 tons 2023-2025, **100 %
bituminous**) and writes `data/raw/_processed-legacy/coal_supply_NEISO.csv`, which
`fleet.coal_supply_class` merges on top of the curated ERCOT map. Merrimack
therefore resolves to the **`COAL_BIT`** dispatch class, offer curve, and
delivered-cost path (`COAL_PRICE_BASE["NEISO"]` = 3.0, the bituminous-by-rail
blend) rather than the generic unclassified `COAL` fallback it carried before.
By the 2023-2025 window it survives in CEMS as a **winter-peaking** unit — a few
hundred online hours a year, not a continuously run baseload — so its derived
`mustrun_pct` is **0.0**. The sunk-fuel take-or-pay floor that pins ERCOT/PJM
coal has no NEISO target: every NEISO plant-group's must-run share is `0.0`,
Merrimack included. It dispatches on economics like any other thermal unit, with
a measured committed floor and the historic-outage overlay, rather than being
forced on. The genuinely inflexible NEISO generation is instead:

- **CHP behind-the-meter steam hosts** — removed from LP capacity and
  reconstructed in post-processing (§1; sized from the P3 CHP floors in
  `thermal_tranches_NEISO.csv`). The cogen tail is dominated by sub-CEMS
  university / hospital / industrial plants whose floor comes from the EIA-923
  monthly-CF fallback (`status = eia923_cf`).
- **Nuclear** — Millstone 2 & 3 (EIA 566, CT, ≈ 2.1 GW) and Seabrook (EIA 6115,
  NH, ≈ 1.25 GW), ≈ 3.4 GW total on the monthly-CF baseload model.
- **Hydro min-flows** — run-of-river and treaty/licence minimum flows on the
  Connecticut and Androscoggin systems.
- **Reliability units** — any RMR-designated capacity for the modelled years;
  none binds across the 2023-2025 backcast window, so no thermal bin carries a
  reliability must-run pin.

**The oil / dual-fuel peaker band — tagged, not re-derived.** ISO-NE's winter
price mechanism leans on oil and dual-fuel switching, the back half of which P13
activated (`dual_fuel_switching`, default-on for NE/NY/PJM). The plants that
make up that band are **tagged**, not re-derived here: `dual_fuel_plant_groups()`
reads the EIA-860 multifuel schedule and flags every gas-primary unit that can
switch to oil backup, keyed `(plant_code, plant_group)` so the tags line up with
the offer-curve bins. In NEISO that flags ≈ 50 `(plant, group)` keys in the
dispatched fleet — the **ST_OIL-capable** steamer **Montville** (546) and the
gas-primary **CT peakers** (Potter Station, Waters River, A L Pierce, Bucksport,
Waterbury, Exelon West Medway II, MMWEC, …) among them. These are ordinary
**economic** peaker / steam bins (low annual CF, no must-run pin); the oil
switch is a *fuel-price* overlay (`apply_dual_fuel_pricing` caps the
AGT-blown winter hub gas at `min(hub_gas, oil)`), not a capacity floor or a
forced commitment. Oil-**primary** RFO/DFO units (Canal, Wyman, New Haven, the
oil-primary Montville/Newington boilers) are carried separately as `oil`-fuel
generators and are not part of the gas offer-curve tranche fleet.

---

### Source references

| Component | File |
|-----------|------|
| Tranche structure, capacity split, CHP must-run post-processing | `docs/binning-methodology.md`; `src/market_sim/data/fleet.py` |
| *n*-slice economic ramp (`_econ_curve_steps`) | `src/market_sim/data/fleet.py` |
| Smoothing config (`offer_curve_smoothing_n` / `_exp`) | `src/market_sim/config/scenarios.py` |
| Committed % / coal must-run % / CC peaking % derivation | `scripts/derive_thermal_tranches.py` |
| Per-ISO bin-assignment export (source-tagged) | `scripts/export_iso_bin_assignments.py` |
| CEMS→EIA split-plant remap (AES Alamitos / Huntington Beach) | `src/market_sim/data/campd.py` (`CAMPD_UNIT_PLANT_REMAP`) |
| Shared outage detectors + thresholds (ERCOT-79-tightened) | `scripts/lib/outage_detect.py` |
| Unit-level outage detection (sole CAMPD outage source) | `scripts/derive_campd_unit_outages.py` |
| Historic-outage overlay | `src/market_sim/data/outages.py` |
