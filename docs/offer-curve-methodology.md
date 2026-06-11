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
mr_mw       = nameplate * MR% / 100
mr_gen_mwh  = mr_mw * 8760 * must_run_cf      # must_run_cf default 0.85
mr_co2_tons = mr_gen_mwh * emission_rate
```

This applies to both `CC_CHP` and `CT_CHP`.

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
committed_hr = base_hr * offer["committed"]                 # e.g. 0.92×
econ ramp    = base_hr * mult(t),  mult: econ_low → peak    # n-slice ramp (§2)
peak (CC)    = base_hr * duct_burner_mult(turbine_class)    # 2.0–2.5×
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
- **`pk`** — the top of the ramp: `duct_burner_mult(turbine_class)` for CC
  (F-class **2.25×**, G/H-class **2.50×**, older E-class **2.00×**), or
  `offer_curve_by_group[group]["peak"]` for groups whose peak band is not
  folded in.

Each slice carries no min-run hours and no start cost — it is incremental
output of an already-committed unit. The midpoint sampling `t = (k+0.5)/n`
places each slice's price at the centre of its capacity band, so the six
slices step smoothly from `≈ base_hr × econ_low` up to
`base_hr × peak`. A CC plant is therefore a cheap Committed block at
`base_hr × 0.92` followed by **six rising slices** scaled entirely by its
own `base_hr`.

**Where the curve ends depends on the group:**

- **`CC_REGULAR`, `CC_CHP`, `COAL`** (`_CURVE_FOLD_PEAK`) — the duct-firing
  peak band is **folded into the top of the ramp** (`lo → peak`), so the
  six slices span econ-low all the way to the duct-burner multiplier.
- **`CT_PEAKER`, `ST_GAS`** (`_CURVE_ECON_ONLY`) — the ramp spans only
  `econ_low → econ_high`; the **Peak band stays a separate flat scarcity
  tranche** whose high multiplier acts as a price-wall floor, not a real
  ramp endpoint.

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

### Facility-level vs. unit-level detection

- **Facility-level** (`scripts/derive_campd_outages.py`) detects outages on
  the summed CEMS series for each plant. Its limitation is that at a mixed
  coal/gas facility (W A Parish, Barney M Davis) the running gas units mask
  a coal-unit outage, which is never seen in the combined series.
- **Unit-level** (`scripts/derive_campd_unit_outages.py`) reads the
  per-unit CAMPD extracts and runs the *same two rules per unit* (coal →
  real-run, everything else → event-based), so it catches a single-unit
  outage at a multi-unit plant and, critically, a **coal-unit outage hidden
  behind running gas units** at a mixed facility. Each detected unit outage
  derates that unit's capacity share of its model bin over the window.

### Scope and overlay rules

- Only **coal and combined-cycle** plants (`QUALIFYING_PLANT_GROUPS`) are
  overlaid; at a mixed-bin plant only the qualifying coal/CC bin is zeroed.
- **Combustion-turbine peakers** carry no outage overlay — they dispatch
  purely economically — and the spiky-running `ST_GAS_PEAKER_PLANTS` are
  likewise excluded.
- The overlay applies every window the detector emits, guarded by a minimum
  span of **48 hours (≥ 2 days)** (`MIN_OUTAGE_SPAN_HOURS`); detection is
  per calendar year, and a window straddling Dec 31 is clipped at the year
  boundary with each side independently clearing the duration floor.

The output is a schema-compatible CSV
(`oris_code, plant_name, unit, outage_start, outage_stop, duration_hours`)
consumed by the historic-outage overlay. (The `duration_hours` column is
informational only; the overlay measures length as
`outage_stop − outage_start`.)

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
| Facility-level outage detection + thresholds | `scripts/derive_campd_outages.py` |
| Unit-level outage detection | `scripts/derive_campd_unit_outages.py` |
| Historic-outage overlay | `src/market_sim/data/outages.py` |
