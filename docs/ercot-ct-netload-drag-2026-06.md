# ERCOT CT_PEAKER reliability drag: an evening-ramp net-load min-gen floor (2026-06)

**Question (handoff).** Simple-cycle gas peakers (`CT_PEAKER`) UNDER-run every
year (keeper C1 ≈ −3.0 / −4.5 / −3.7 TWh, 2023/24/25; −39% to −68%) and
CC_REGULAR OVER-runs as the conservation-of-energy counterpart. The hourly
energy-only LP never commits CT peakers — their simple-cycle heat rate puts
their offer at the top of the merit order (~$60–90/MWh), so the LP only runs
them in genuine scarcity hours. Real ERCOT operation commits them for
**summer-peak + evening net-load-ramp local reliability** (RUC / RMR / local
congestion), which the de-committable hourly LP never sees. The previous fix,
`ct_mustrun_per_plant`, pins each peaker to its **observed EIA-923 generation** —
a measured-actuals backcast crutch with no forward analogue (it cannot regenerate
for a forward year and does not respond to changed conditions; borderline
CLAUDE.md #11 generation-pinning). Build the *physics* of the commitment so it
regenerates for a forward year.

**Answer.** Mirror the ST_GAS net-load drag
(`docs/ercot-st-gas-netload-drag-2026-06.md`): a per-hour min-gen floor
`clip(slope·netload_GW + intercept, 0, cap) × capacity` on the non-`_peak`
CT_PEAKER tranches, over which the LP dispatches economically. Two differences
from the gas-steam boiler, both driven by the measured signature:

1. **CT peakers are an evening-ramp resource, not an all-hours one.** Their
   CAMPD overnight capacity factor is ~0 even at high net-load, while the
   afternoon-evening CF rises cleanly with net-load. So the floor is **gated to
   the ramp window** `[ct_drag_ramp_start, ct_drag_ramp_end)` = **15–22h
   local-standard**; it is zero outside it. (CAISO's CT reliability floor uses
   the same evening window — `scripts/data/derive_caiso_ct_reliability_floor.py`.)
2. The curve is fit to the **evening** CF-vs-net-load relationship, not the
   overnight one.

Because both the trigger (net-load) and the magnitude (physical min-gen) are
forward-derivable and condition-responsive, the mechanism is admissible in
**both backcast and forecast** (CLAUDE.md #10/#11) — the forward-native
replacement for the `ct_mustrun_per_plant` actuals pin.

## The measured signature (no LP solve)

CAMPD hourly net for the 27 registry `CT_PEAKER` plants (8.23 GW nameplate),
2023–2025, against ERCOT system net-load built from EIA-930 demand minus
EIA-930 wind+solar. **Critical alignment:** EIA-930 `period` is UTC; CAMPD (and
the model dispatch clock) are local **standard** time (CST = UTC−6, no DST). The
net-load is shifted UTC→CST and laid on the same non-leap `hour_of_year` grid
before regressing — without this the CF and the net-load it keys off are 6 h
apart and the relationship washes out (Spearman ρ collapses from ~0.7 to ~0.2).

* **CT peakers are off overnight, on in the afternoon-evening ramp.** At the
  *same* net-load (e.g. ~47 GW) the overnight CF is ~0.01–0.06 but the evening
  CF is ~0.20–0.30 — net-load alone does not separate them, the diurnal ramp
  does. This is why the floor is window-gated (unlike the all-hours ST_GAS
  boiler, which is committed every night).
* Within the evening ramp the fleet CF rises cleanly and monotonically with
  contemporaneous net-load:

  | net-load (GW) | ~27 | ~32 | ~37 | ~42 | ~47 | ~52 |
  |---|---|---|---|---|---|---|
  | evening CF (2024) | 0.05 | 0.10 | 0.14 | 0.17 | 0.20 | 0.30 |

* The relationship is **year-stable** (2023/24/25 evening curves overlay) and
  strongly **monotonic**: hourly net-load vs CT CF Spearman ρ = **0.64 / 0.73 /
  0.70** (2023/24/25), once time-aligned.
* The evening-ramp floor energy reproduces the measured annual CT total as a
  minimum the LP exceeds in scarcity: ~6.5 / 7.2 / 7.5 TWh floored-total vs
  measured 6.0 / 6.8 / 7.0 — the missing dispatch *is* the evening net-load-ramp
  reliability commitment.

### Pooled fit

Median evening-ramp CF per 2-GW net-load bin, least-squares line (2023–2025
pooled), applied only in the 15–22h window:

```
floor_frac = clip(0.00703 · netload_GW − 0.1427, 0, 0.47)   (zero below ~20.3 GW)
           applied for hour-of-day in [15, 22), else 0
```

These are the `ScenarioConfig` defaults `ct_drag_slope_per_gw / _intercept /
_cap` and `ct_drag_ramp_start / _ramp_end`. Cap 0.47 = the 95th-percentile
evening CF (hottest ramp hours).

## Why net-load (gated), not the actuals pin or a temperature threshold

* The **actuals pin** (`ct_mustrun_per_plant`) forces each plant's measured
  EIA-923 MWh as a floor — it has no forward analogue (a forecast year has no
  measured generation) and does not respond to a changed wind/solar build, so
  it validates plumbing, not skill. The net-load drag derives the same
  commitment from a forward-available driver.
* A bare **temperature threshold** would capture summer peaks but miss the
  winter-morning ramp (cold, low-solar mornings also drive high net-load and
  peaker commitment). **Net-load unifies both** and is already the model's
  exogenous forward input, exactly as for the ST_GAS drag.
* A **pure all-hours net-load floor** (the literal ST_GAS form) over-floors CT
  badly: the evening curve applied to all 8760 h forces peakers on overnight at
  moderate net-load where they are actually off (~+8 TWh, double the measured
  total). The ramp-window gate is what makes the net-load floor correct for a
  peaker fleet.

## Mechanism (code)

* `ScenarioConfig.ct_netload_drag` (default **off**) enables the floor;
  `ct_drag_slope_per_gw / _intercept / _cap / _ramp_start / _ramp_end` carry the
  fitted curve and window.
* `fleet.apply_ct_netload_drag_floor(fleet_arrays, generators, net_load_mw,
  config)` sets `FleetArrays.min_gen` for each non-`_peak` CT_PEAKER tranche
  (the duct-firing `_peak` scarcity band runs purely on price), capped at
  available capacity and composed with any existing floor via `maximum`, zeroed
  outside the ramp window. The LP dispatches economically *above* the floor.
* `run_calibration.run_year` computes system net-load (the same LP-served
  convention the ST_GAS drag uses) and applies the floor before the P0/P1
  solves. **No extra LP solve** — a `min_gen` bound on the existing pass.
* Reproduce the fit: `scripts/probes/_ct_netload_drag_fit.py`.

## Calibration result

On the `run162` merit-order recipe (DAM-AS / co-opt / RTORDPA overlays off, pure
dispatch), CT floor ON vs OFF, both at PRB floor 0.62 / CC_DELTA +0.12:

| class | metric | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **CT_PEAKER** | drag OFF | 3.89 (−43%) | 2.86 (−61%) | 3.65 (−51%) |
|               | **drag ON** | **5.28 (−23%)** | **4.68 (−36%)** | **5.41 (−27%)** |
| **CC_REGULAR**| drag OFF | −2.14 | +4.99 (FAIL) | −4.79 |
|               | **drag ON** | −2.59 | **+4.46 (PASS)** | −5.75 |

CT_PEAKER closes ~40% of its under-run in every year; the freed-from-CC energy
in 2024 pulls CC_REGULAR's over-run into the C1 band. The floor displaces ~1 TWh
of CC in dear-gas 2025 (where CC is already short), so the 2025 CC residual is
closed by the offer-curve pass (a gentler CC offer delta), not the floor — see
`docs/ercot-reserve-supply-scarcity-handoff-2026-06.md` and the calibration log.
