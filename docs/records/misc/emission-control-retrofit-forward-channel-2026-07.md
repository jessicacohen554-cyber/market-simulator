# Forward emission-control retrofit channel — 2026-07-05

**Owner direction / context:** the CO2-first emissions plan
(`docs/handoffs/emissions-co2-rate-plan-2026-07.md`) §7 flagged a gap in the
forward rate estimator: the trailing-window average in
`market_sim.data.emission_rates.forward_plant_co2_rate` only picks up **realized**
emission-rate drift as measured history grows. It has **no forward channel** for
an **announced** control install (SCR, scrubber/FGD, DSI, carbon-capture) that
will step a unit's NOx/SO2/CO2 rate in a future year — the step lands in the
estimate only *after* the control shows up in CAMPD, years late. §7 explicitly
deferred "a policy-driven retrofit channel" as "a separate design." This is that
design and its implementation.

The mechanism mirrors the existing **CCS retrofit screen** (methodology spec
§5.6, `model.capacity.apply_ccs_retrofit`) in form —
`post_rate = pre_rate × (1 − removal_fraction)` — but differs in *trigger*: the
CCS screen fires on **economics** (payback beats remaining life), while this
channel fires on an **announcement** (a committed EIA-860 install with a future
Inservice Year). It is forecast-only, config-registered, and ships **default
OFF** so it is byte-identical to the base estimator until deliberately enabled.

---

## 1. The forward driver (EIA-860 committed-control pipeline)

`data/raw/eia-860/eia860_enviro_assoc_emissions_control_equipment.parquet`
(EIA-860 Schedule 6) is the source. It carries, per plant × control:

| Field | Use |
|---|---|
| `Plant Code` | match to the model plant (the rate map is keyed by plant) |
| `Equipment Type` | control technology → target pollutant + removal fraction |
| `Status` | committed-but-not-operating gate (`PL`/`CO`/`TS`/`OZ`) |
| `Inservice Year` | the **committed install year** — the step's forward driver |

A row that is (a) in a committed status, (b) a modelled control type, and (c) has
an Inservice Year **after** the measured-history window is an *announced forward
install*. As of the 2025 Early-Release vintage there are 7 such controls
nationally (e.g. Ghent 1356 SCR 2028, Wolf Summit 60206 SCR 2027, Hu Honua 61364
DSI+SCR 2027) — all NOx (SCR) or SO2 (DSI). Operating (`OP`) controls are already
in the measured rate and never re-fire; retired/cancelled/out-of-service
(`RE`/`CN`/`OS`/`SB`) never fire.

The install *date* is the driver, not any residual — the defining property that
makes the channel a forecast method rather than an overlay (§4).

### Control-type → pollutant + removal fraction

`constants.CONTROL_RETROFIT_TYPE_MAP` (class-typical engineering removal
fractions, EPA AP-42 Ch.1 / EIA-860 reported efficiencies):

| EIA code | Control | Pollutant | Removal |
|---|---|---|---|
| `SR` | Selective catalytic reduction (SCR) | NOx | 0.90 |
| `SN` | Selective non-catalytic reduction (SNCR) | NOx | 0.35 |
| `JB` | Jet-bubbling reactor (wet FGD) | SO2 | 0.95 |
| `SD` | Spray-dryer / dry FGD | SO2 | 0.95 |
| `CD` | Circulating dry scrubber | SO2 | 0.95 |
| `DSI` | Dry sorbent injection | SO2 | 0.50 |

The post-control rate is the unit's **own measured pre-control rate** stepped by
the fraction, so an efficient host stays efficient after the control — exactly
the CCS screen's `emission_rate_co2 *= (1 − capture_rate)` pattern. Particulate /
mercury controls (`EH`, `MC`, `BP`, `ACI`, …) are unmapped and dropped — the
model prices no PM/Hg rate.

**CO2/carbon-capture is intentionally absent from the default map** — see §5.

---

## 2. Mechanism

Two functions in `market_sim.data.emission_rates`:

* **`load_announced_controls(path, *, min_install_year, statuses=None, type_map=None)`**
  — reads the EIA-860 artifact, applies the status / type / year filters, and
  returns a list of `AnnouncedControl(plant_id, pollutant, install_year,
  removal_fraction, fuel_class=None, equipment_type)`. Returns `[]` when the
  artifact is absent. `min_install_year` is the first year *after* the measured
  history (so already-reflected controls are excluded).

* **`apply_control_retrofits(rate_map, controls, target_year, pollutant)`** — a
  pure, unit-agnostic override. For every control matching `pollutant` whose
  `install_year ≤ target_year`, each `(plant_id, fuel_class)` entry of the base
  rate map for that plant is multiplied by `(1 − removal_fraction)` (narrowed to
  the control's `fuel_class` when set; plant-wide otherwise). Rates only ever
  step **down**; multiple controls on one plant/pollutant compound
  multiplicatively. The input map is never mutated (a fresh dict is returned), so
  an upstream cached base map is untouched. Before `install_year` the entry keeps
  its trailing-average base — the channel is a clean step at the install year.

### Where it binds

In the fleet build (`data.fleet.apply_plant_emission_rates_v2`), after the
forecast CO2 rate map is assembled, the channel is applied for `pollutant="co2"`
when `config.control_retrofit_forward` is set **and** the mode is forecast:

```
rates = _measured_plant_rate_map_v2(...)                 # gen-weighted base
if forecast and config.control_retrofit_forward:
    controls = load_announced_controls(path, min_install_year=HISTORY_END+1)
    rates = apply_control_retrofits(rates, controls, year, "co2")
```

The step is on the **base (merit-order) rate** — a control genuinely changes the
unit's marginal emission cost in a carbon-priced ISO, and its reported intensity
everywhere. No fixed-point iteration is introduced (it is a one-pass override of
a precomputed map, honouring the one-pass rule).

---

## 3. Backcast / forecast line

**Forecast only.** `apply_plant_emission_rates_v2` calls the channel *only* when
`mode != "backcast"`. In a backcast the mode-aware source already books each
year's **own measured rate**, which by construction reflects whatever control was
actually operating that year — an announced-step overlay would double-count and,
worse, would be pinning to an outcome. So the channel is silent in backcast, on
exactly the same footing as the estimator itself: measured rate in backcast,
estimator (+ this forward step) in forecast.

---

## 4. Rule-13 admissibility argument

CLAUDE.md rule 13 admits a measured quantity when it enters as a **reproducible
physical/market input grounded in physics or market design**, and the test is:
*could this same quantity be produced for a forward year from forward drivers, and
would it respond to changed conditions?* The channel passes on both counts:

* **Forward-driver-sourced, not residual-sourced.** The step year is EIA-860's
  committed **Inservice Year** — a forward-looking, publicly-reported project
  milestone, identical in kind to the EIA-860 proposed-additions pipeline the
  model already uses for known builds (`load_planned_additions`, forecast-only).
  The step magnitude is a published engineering removal fraction applied to the
  unit's own measured rate. Nothing in the channel reads a price or volume
  residual, and nothing is tuned to a backcast fit — it re-derives entirely from
  the EIA-860 vintage.
* **Regenerates for a forward year.** Point the loader at next year's EIA-860
  vintage and the announced-control set regenerates automatically; a newly
  announced SCR appears, a cancelled one (`Status = CN`) drops out.
* **Responds to changed conditions.** If an install is cancelled or slips, the
  step vanishes or moves; if a unit retires, it leaves the rate map and the step
  has nothing to apply to. The forward rate is not frozen — it tracks the
  committed-control pipeline.

What rule 13 **forbids** — feeding a measured *outcome* back to force a fit — the
channel does not do: it never consumes the target year's CEMS, never adds a
residual-tuned adder, never rescales an output onto actuals. It is the same class
of admissible measured input as CAMPD outage windows, delivered fuel prices, and
the trailing-average estimator itself.

This is also consistent with the L21 governance wording the CO2 plan §6 set: the
overlay list forbids *same-year pinned* rates as a forecast method; a
forward-driver-sourced announced step is not that.

---

## 5. Rule-15 reconciliation (one mechanism per phenomenon)

Carbon capture (CO2) is deliberately **excluded from the default control-type
map**. Economically-triggered CCS on gas-CC units is already owned by the CCS
retrofit screen (`model.capacity.apply_ccs_retrofit`, methodology spec §5.6);
adding a second CO2-stepping mechanism would stack two floors on the same
phenomenon. The two triggers are disjoint by design:

* **CCS retrofit screen** — *economic* trigger (payback < remaining life), gas-CC
  hosts, capacity-evolution step.
* **This channel** — *announcement* trigger (committed EIA-860 install), any
  covered unit, forward-rate step. Default map = **SO2/NOx only**, the controls
  the CCS screen does not touch.

The `apply_control_retrofits` function stays pollutant-general (so a future
explicit *announced-CCS* source could use it), but the shipped default emits no
CO2 rows, so the live CO2 seam is inert with the default source and there is no
overlap with the CCS screen today. Should EIA-860 gain committed capture codes,
the reconciliation is a guard: a unit with an announced capture install is
skipped by the economic screen (it is already committed).

---

## 6. NOx / SO2 wiring status (awaiting E2)

The default map's pollutants are **NOx and SO2**, but the fleet forecast path
today writes only a forecast **CO2** rate map (`apply_plant_emission_rates_v2`
sets `emission_rate_co2`; NOx/SO2 remain on the legacy artifact per the CO2
plan's R7 note). Forward NOx/SO2 rate *estimators* and their fleet application
are a separate wave ("E2"). This wave therefore delivers:

* the **override function and EIA-860 loader**, pollutant-general and unit-tested
  for the SO2 case (so E2 is a pure wiring change, not new mechanism);
* the **live CO2 seam**, wired and gated (inert with the default SO2/NOx-only
  source, per §5);
* the config flag, constants, and this design.

When E2 lands its forward NOx/SO2 maps, they plug into the **identical seam**:
`rates_nox = apply_control_retrofits(rates_nox, controls, year, "nox")` — the
SCR/SNCR/FGD/DSI steps then bite on the pollutants they actually control.

---

## 7. Configuration & constants (rule 24 — every tunable registered)

| Symbol | Where | Default | Meaning |
|---|---|---|---|
| `control_retrofit_forward` | `ScenarioConfig` (Tier 2) | `False` | master switch; OFF ⇒ byte-identical |
| `control_retrofit_path` | `ScenarioConfig` (Tier 2) | EIA-860 enviro-control parquet | source artifact |
| `CONTROL_RETROFIT_HISTORY_END_YEAR` | `constants` | `2025` | last measured-history year; controls online after it are forward steps |
| `CONTROL_RETROFIT_ANNOUNCED_STATUSES` | `constants` | `("PL","CO","TS","OZ")` | committed-but-not-operating status gate |
| `CONTROL_RETROFIT_TYPE_MAP` | `constants` | SR/SN/JB/SD/CD/DSI | control-type → (pollutant, removal fraction) |

All are frozen against backcast residuals (rule 23): they re-derive only when the
EIA-860 source vintage or the published removal-efficiency references update — not
because a residual moved. No off-registry channel (rule 25): every knob is in
`ScenarioConfig`/`constants` and surfaces in `run_config.json`.

---

## 8. Tests

`tests/test_emission_rates.py`:

* `TestControlRetrofitForward` — the required case: an announced **2030
  scrubber** (95% SO2 removal) leaves the covered plant at its trailing-average
  rate through 2029 and steps it to 5% of base from 2030 on, while a plant with
  no announced control is unchanged; plus input-immutability, pollutant-mismatch
  no-op, fuel-class narrowing, multiplicative stacking, and empty-controls
  identity.
* `TestLoadAnnouncedControls` — the EIA-860 loader keeps only committed-status,
  modelled-type, post-floor-year rows (SCR→NOx@0.90, DSI→SO2@0.50) and returns
  `[]` for a missing artifact.

Default-OFF byte-identity is structural: with `control_retrofit_forward=False`
the fleet path never enters the override branch.

---

## 9. Acceptance

* Forward-driver-sourced measured input (rule 13) — install year from EIA-860,
  step from published removal fractions, no residual. ✅ §4
* Default **OFF** ⇒ byte-identical to the base estimator. ✅ §2, §8
* Forecast-only; backcast never consults it. ✅ §3
* No keeper change, no solve, no registered bundle year outside 2023–2025 (no
  calibration run was launched). ✅
* One-mechanism-per-phenomenon preserved vs the CCS screen (rule 15). ✅ §5
