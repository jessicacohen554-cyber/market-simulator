# FINDING — miso-268: the four open MISO objects, localized at zero LP

Keeper `2026-09-23-miso-267-dispatched-bin`. Everything here reads committed sidecars, the
committed bench parts, the committed RT price series, and the keeper's per-unit dispatch from
its miso-267 leg commits. No solve.

## 1. C3b 2021 (NRMSE 0.307): February and October–November

Share of the monthly squared error:

| month | model $/MWh | actual RT (LW) | share of SSE |
|---|---:|---:|---:|
| Feb | 78.0 | 45.4 | **57 %** |
| Oct | 47.1 | 59.8 | 9 % |
| Nov | 46.3 | 67.0 | **23 %** |
| other 9 months | | | 11 % |

* **February is high on every day, not just during Uri.** Excluding Feb 13–19 the model
  averages $46.0 against $27.6 actual; Feb 5–12 runs $41–75 against $21–46. During the storm
  (Feb 15–17) the model is $177–234 against $114–153. The whole month is priced too high.
* **October–November is low** by $13–21/MWh.
* Neither pattern is a coal-quantity object. The leading hypothesis, **not tested here**, is the
  gas level at monthly grain. MISO's Feb 2021 EIA-923 delivered price averages the storm-week
  purchases into the month. `miso_winter_citygate_daily` reshapes it within the month but keeps
  the mean, so the non-storm days inherit part of the spike. A lane that takes this should
  compare the model's daily Feb-2021 gas series to the traded Chicago citygate daily before
  proposing anything. Rule: localize, never exclude.

## 2. C3a price body: an overnight object

2020 load-weighted error (model − zonal RT), $/MWh:

* **By hour of day:** +7 to +8 at hours 20–03, falling to −1.6 at hour 16. 2023 (CALIBRATED)
  shows the same shape: +8 to +9 overnight, −3 to −4 at hours 15–17.
* **By month:** positive in every month except Jul–Aug 2020; largest Jan–Mar and Nov–Dec.
* **By zone:** every zone is positive (East +1.3 to West +7.2).
* **By the model's marginal class** (marginal emission rate as a proxy): +2.9 to +5.3 in every
  bin. It is not one class setting the price wrong.

**Reading.** The body is the same overnight low-load regime where coal runs long (object 4, +1.87
TWh in 2020 RT decile 0). In that regime the model runs **more** coal than MISO did and still
prices **higher**, so the real overnight price is set below the coal fleet's fuel cost. That is
the coal self-commitment / below-cost minimum-load conduct miso-224 named as the successor to
its gas-convention screen. Any lever for it is a commitment floor with its own window, driver
and forward story (rule 17), attributed against the existing coal floors first (D-2, rule 19).
A level offset remains forbidden (rules 1/13).

## 3. 2022 coal/gas substitution: the pooled coal budget hides yard-level infeasibility

`coal_fuel_inventory` pools every yard's stock and receipts into one fleet pile. Measured
per coal yard (a plant, or a shared-storage entity with the plants it serves) on the keeper's
own per-unit dispatch, the keeper burns more coal at some yards than that yard held (Dec(Y-1)
stock + prior-years receipts):

| year | static excess, TWh-equiv | of which PRB | BIT | lignite |
|---|---:|---:|---:|---:|
| 2020 | 2.64 | 1.45 | 1.14 | 0 |
| 2021 | 11.76 | 8.69 | 1.82 | 1.18 |
| 2022 | **19.01** | **15.32** | 3.60 | 0 |
| 2023 | 2.33 | 1.55 | 0.58 | 0.19 |
| 2024 | 0.49 | 0.05 | 0.44 | 0 |
| 2025 | 9.38 | 6.03 | 3.34 | 0 |

The pooled annual row has slack in every year. 2022's excess is 80 % PRB, the class running
+10.04 TWh long. The fleet-level numbers also rule out the alternative "minimum operating stock"
lever for 2022: MISO's real 2022 receipts (128.1 Mt, covered plants) **exceeded** the
prior-two-year rate (121.1 Mt), and the real fleet closed 2022 holding 25.7 Mt, the same as it
opened with. The pooled budget is not too loose in total; it is wrong in where the coal is.

Instrument: `scripts/probes/_miso268_plant_grain_phase0.py` →
`results/calibration/_miso268_plant_grain_phase0.json`. Arm and predictions:
`docs/PRECOMMIT-miso268-coal-yard-grain-2026-09-24.md`.

## 4. Coal trough surplus

Same regime as §2. Not separately charterable before a D-2/D-4 attribution of the coal floors in
the overnight hours. Routed with §2.

## 5. Forecast-parity gap filed: `gas_offer_margin_anchor_vintage`

Armed in the MISO keeper since miso-264. The backcast path resolves the anchor to the solve
year's own mean delivered gas (`scripts/run_calibration.py`). The forecast orchestrator's
`apply_gas_offer_margin` (`src/market_sim/runner.py`) reads the frozen
`config.gas_offer_margin_anchor`. The quantity is forward-derivable (the forecast year's own gas
trajectory mean), so this is a **GAP**, not backcast-only. Declared in
`scripts/lib/forecast_parity_registry.py` with this document as its finding. Wiring it is a
forecast-lane change and is not made here.
