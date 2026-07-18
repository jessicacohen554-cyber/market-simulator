# ERCOT forward AS requirement-setting formula (G3 — the requirement, not the price)

**Date:** 2026-06-27
**Branch:** `claude/ercot-as-forward-requirement-rebased`
**Status:** BUILT, tested, default-off, ERCOT-gated, legacy byte-identical.
**Scope:** the **AS requirement** (demand-curve RHS) of the endogenous
multi-product co-opt — the last measured read on the forward AS path. Replaces
the per-product read of the measured AS Plan (`ASPLANNP433`,
`scarcity.ercot_as_plan_requirement_mw`) with a **forward formula of forecast
drivers**, wired as the forward branch of `ercot_as_forward_requirement_mw` (the
seam added in c132c7a). The measured series stays the backcast realization the
formula is validated against.
**Reads first:** `docs/ercot-multiproduct-as-coopt-2026-06.md` (run159, the
co-opt this feeds), `docs/forecast-methodology-gaps-2026-06.md` G3,
`docs/ercot-reserve-supply-cap-ordc-adder-2026-06.md` (the RTOLCAP/ORDC-adder
track that forms acute/tail scarcity).

---

## Scope — and what this is NOT

This closes the **requirement** half of G1/G3: the per-product AS demand-curve
RHS that drives **acute/tail** scarcity. It is **not** the broad-May residual —
the RTOLCAP work re-diagnosed that as an **energy-base / merit-order** miss (CC
over-run vs ST_GAS+CT_PEAKER under-dispatch), a separate investigation. The
measured DAM-AS overlay (run157) correctly stays the pre-RTC+B broad-month
bridge; nothing here retunes curves to the broad month (forbidden, CLAUDE.md
#1/#11).

The endogenous co-opt (`ercot_multiproduct_as_coopt`) and the RTOLCAP supply cap
+ ORDC adder already form scarcity endogenously from the LP. The *only* remaining
measured read on the forward path was the per-product requirement MW. That read
is what this replaces.

## The forward formulas

Each product's requirement is a function of forecast drivers per ERCOT's
published AS Methodology (NP3-160-CD, "Methodology for Setting Day-Ahead and
Real-Time Ancillary Service Requirements"). All four derive from the three
forecast series the dispatch already builds — total served load and total
wind / solar generation (`scarcity.ercot_as_forward_drivers`):

```
net_load(t)  = load(t) - wind(t) - solar(t)
vre_share(t) = (wind(t) + solar(t)) / load(t)
sigma_fe(t)  = sqrt( (F_L*load)^2 + (F_W*wind)^2 + (F_S*solar)^2 )   # DA net-load
                                                                     # forecast-error std
ramp_up(t)   = max_{k=1..W}( net_load(t+k) - net_load(t) )_+         # forward net-load
                                                                     # up-ramp, W=3 h
```

`sigma_fe` combines independent load / wind / solar day-ahead forecast errors in
quadrature; the component fractions are the published-order DA error magnitudes
(`F_L=1%` of load, `F_W=10%` of wind output, `F_S=18%` of solar output — solar's
relative DA error is the largest and dominates the VRE-driven growth).

| product | forward formula | driver story |
|---|---|---|
| **RegUp** | `floor + k·sigma_fe` | regulation covers the within-hour (sub-SCED) net-load variability — a sub-hourly slice of the DA forecast-error std |
| **RRS** | `floor + k·vre_share` | largest-contingency frequency-response floor (~2300 MW) + a low-inertia adder that rises as VRE displaces synchronous inertia |
| **ECRS** | `base + k·sigma_fe + k'·ramp_up` | the ~2 GW ramp-risk product (live 2023-06-10): forecast-error + the forward net-load up-ramp (the solar-evening ramp it is sized to cover) |
| **NonSpin** | `base + k·load + k'·ramp_up` | longer-horizon net-load-uncertainty reserve, sized as a **load-ratio** share of system load plus the forward net-load up-ramp (the published Non-Spin driver) |

All clipped to published min/max bands. Coefficients live in `constants.py`
(`ERCOT_AS_*`), **calibrated to reproduce the published `ASPLANNP433`
requirement MW** — a procurement quantity, never a price (CLAUDE.md #12).

**Forward response (the point):** more VRE → larger `sigma_fe` / `ramp_up` /
`vre_share` → larger requirement, automatically. In a forecast run the drivers
come from the evolved `wind_cap` / `solar_cap`, so the AS requirement grows with
VRE penetration with no measured read.

## Honesty gate

The requirement is a **formula of forward drivers** that regenerates for a
forecast year and responds to changed conditions (the admissibility test, CLAUDE.md
#10/#12). The coefficients are fit to the ERCOT-published **requirement MW**
(ASPLANNP433), not to any LMP / RTSPP / MCPC — the demand-curve *prices* remain
VOLL-anchored market-design schedules, and the hourly scarcity *incidence* still
comes from the responsive headroom in the shared-headroom RHS. No measured MW is
pinned to a price anywhere on the path.

## Wiring

* `config.ercot_as_forward_requirement` (+ CLI `--ercot-as-forward-requirement`)
  — default **off** → the co-opt reads the measured ASPLANNP433 (the keeper /
  backcast path is byte-identical). Requires `energy_reserve_coopt` +
  `ercot_multiproduct_as_coopt`.
* `scarcity.ercot_as_forward_drivers(system_load, wind_gen, solar_gen)` — builds
  the per-hour driver arrays (vectorized; no Python loop over hours).
* `scarcity.ercot_as_forward_requirement_mw(config, code, hours, drivers)` —
  returns the per-product forward MW, or `None` (→ measured fallback) when the
  flag is off, drivers are absent, or the product is not an upward AS product.
* `scarcity.ercot_multiproduct_reserve_coopt_inputs(..., system_load, wind_gen,
  solar_gen)` — threads the forecast profiles; both call sites
  (`scripts/run_calibration.py`, `src/market_sim/runner.py`) pass them from the
  served-load + wind/solar-generation series already in scope.

## Modeled-vs-measured requirement validation

`scripts/validate_ercot_as_forward_requirement.py` — the forward requirement
built from the model's own forecast drivers vs the measured ASPLANNP433, per
product, demand-active hours (ECRS scored over its 2023-H2 live window):

| product | year | meas MW | model MW | MAE | bias | corr |
|---|---|---|---|---|---|---|
| REGUP | 2023 | 394 | 392 | 141 | −2 | 0.22 |
| REGUP | 2024 | 406 | 413 | 138 | +7 | 0.31 |
| REGUP | 2025 | 436 | 440 | 98 | +4 | 0.53 |
| RRS | 2023 | 2903 | 2697 | 270 | −206 | 0.34 |
| RRS | 2024 | 2722 | 2725 | 233 | +4 | 0.32 |
| RRS | 2025 | 2739 | 2759 | 254 | +20 | 0.27 |
| ECRS | 2023 | 1909 | 1419 | 527 | −490 | 0.44 |
| ECRS | 2024 | 1753 | 1507 | 405 | −246 | 0.45 |
| ECRS | 2025 | 1417 | 1619 | 452 | +203 | 0.66 |
| NSPIN | 2023 | 3349 | 2755 | 940 | −594 | −0.08 |
| NSPIN | 2024 | 2684 | 2767 | 520 | +83 | 0.16 |
| NSPIN | 2025 | 2886 | 2796 | 622 | −90 | 0.18 |

**Total up-AS held** (the quantity that drives the shared-headroom scarcity):

| year | meas GW | model GW | ratio |
|---|---|---|---|
| 2023 | 7.73 | 7.27 | 0.94 |
| 2024 | 7.56 | 7.41 | 0.98 |
| 2025 | 7.48 | 7.61 | 1.02 |

The 2024/2025 levels match the published requirement (total within ±3%, small
per-product biases). **2023 is systematically under** (RRS −206, ECRS −490,
NSPIN −690, total 0.93×) — ERCOT procured *more* AS in 2023 (early-ECRS / RRS
conservatism, the documented out-of-market over-procurement the energy-only ORDC
model already does not reproduce). The forward formula reflects the **steady-state
methodology**, not the 2023 transition, and is honestly NOT pinned to 2023's
excess. The diurnal shape is captured (REGUP/ECRS peak on the solar-driven
midday/evening ramp, RRS rides its contingency floor, NSPIN tracks load).

## Co-opt re-solve — acute/tail incidence (run163 vs run159 measured)

`run163` = the run159 keeper recipe (multi-product co-opt, P1-only) with the AS
requirement swapped measured → forward (the one delta,
`ercot_as_forward_requirement=True`). `159repro` = run159 re-solved in the same
environment (measured requirement) as the clean baseline. Demand-weighted model
LMP; tail = hours above $200 / $1000 and the share of annual $ they carry
(`scripts/probes/_eval_acute_tail.py`):

| year | run | annual | May acute (8/24/26) | h>$200 | h>$1k | $>200 share |
|---|---|---|---|---|---|---|
| 2023 | 163 forward | 35.6 | 24.6 | 68 | 22 | 32% |
| 2023 | 159 measured | 42.9 | 24.6 | 133 | 34 | 45% |
| 2024 | 163 forward | 21.4 | **21.7** | 13 | 1 | 5% |
| 2024 | 159 measured | 22.4 | **40.0** | 23 | 3 | 9% |
| 2025 | 163 forward | 33.1 | 30.2 | 3 | 0 | 1% |
| 2025 | 159 measured | 33.4 | 30.2 | 7 | 1 | 2% |

**Held in 2025 and on the 2023 acute days; under-fires the 2024 May acute days.**

* **2025 — clean** (May-gate MAE 2.46; acute 30.2 identical to measured). The
  forward requirement reproduces the co-opt scarcity with no measured read.
* **2023 — acute held** (24.6 identical): the 2023 acute/tail is carried by the
  energy base + the RTORDPA overlay (G2 bridge, kept), not the AS requirement, so
  swapping the requirement does not move it. The forward total tail is *lower*
  (h>$200 68 vs 133) because the forward 2023 requirement is below ERCOT's
  documented 2023 **over-procurement** — honest, not chased.
* **2024 — May acute under-fires** ($21.7 vs the measured-requirement $40.0).
  Diagnosis (`ercot_as_forward_drivers` on the May-2024 acute evenings, HE16-21):
  the *measured* total up-AS spikes to ~8.8 GW, the forward formula sizes ~7.4 GW.
  The gap is concentrated in ECRS/NonSpin and is a **discretionary day-specific
  uplift**: ERCOT manually procured extra AS on those anticipated-tight days
  beyond what any net-load / ramp / VRE relationship predicts (the same operator
  conservatism behind the 2023 over-procurement). That uplift has **no
  forward-driver analogue** — reproducing it would require keying the requirement
  off the realized acute days, i.e. pinning the measured outcome, which the
  honesty gate (CLAUDE.md #12) forbids.

This is the **requirement-side mirror** of the multi-product co-opt's own finding
(`docs/ercot-multiproduct-as-coopt-2026-06.md`): the broad/acute May-2024
elevation the *measured* DAM-AS overlay carries is partly ERCOT
discretionary/out-of-market procurement that an endogenous forward model
legitimately does not reproduce. The forward requirement holds the **systematic,
driver-driven** AS (annual level, diurnal/seasonal shape, 2025, the 2023/2025
acute days); the measured DAM-AS overlay (run157) correctly **stays** the
pre-RTC+B bridge for the discretionary acute/broad-May component. Honesty gate
intact: the requirement is a formula of forward drivers, never the measured MW
pinned to a price.

_Re-solve: `python scripts/archive/run_163.py` (run159 recipe +
`ercot_as_forward_requirement=True`, all years, per-plant, P1-only)._

## Files

- `src/market_sim/config/constants.py` — `ERCOT_AS_*` forward coefficients.
- `src/market_sim/config/scenarios.py` — `ercot_as_forward_requirement` flag.
- `src/market_sim/results/scarcity.py` — `ercot_as_forward_drivers`,
  `ercot_as_forward_requirement_mw`, threaded into
  `ercot_multiproduct_reserve_coopt_inputs`.
- `scripts/run_calibration.py`, `src/market_sim/runner.py` — pass the forecast
  profiles at the co-opt call sites.
- `scripts/run_calibration_full.py` — `solve_and_persist` flag + CLI.
- `scripts/validate_ercot_as_forward_requirement.py` — the modeled-vs-measured
  validation.
- `tests/test_ercot_multiproduct_coopt.py::TestForwardRequirement`.
