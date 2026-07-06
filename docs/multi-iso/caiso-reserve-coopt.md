# CAISO energy + operating-reserve co-optimization (per-generator contingency reserve)

**Status:** built 2026-07-06 (issue #1492, lane L-10). CAISO was the **only**
registered ISO with no `_caiso_design` — `pipeline/kwargs.apply_reserve_coopt`
hard-excluded it (`iso == "CAISO"` short-circuit). This adds the design behind a
new default-off flag `caiso_reserve_coopt` (the short-circuit is preserved when
the flag is off, so the default CAISO path is byte-identical). The in-LP CAISO
analogue of the ERCOT ORDC / PJM Primary-Reserve / MISO RBDC / NYISO RCPF
co-optimization. **Zero parameters fitted to the price residual** — every
requirement basis and demand-curve step is a NERC/tariff value (rules 5/23).

**Code:** `config/reserve_config.py` (`_caiso_design`,
`_caiso_reserve_eligible`; constants `CAISO_CONTINGENCY_FRAC`,
`CAISO_SPIN_FRACTION`, `CAISO_ENERGY_BID_CAP_SOFT`, `CAISO_SPIN_DEMAND_CURVE`,
`CAISO_NONSPIN_DEMAND_CURVE`), `results/scarcity.py`
(`caiso_reserve_demand_steps`, `largest_single_contingency_mw`),
`pipeline/kwargs.py` (flag gate + CAISO log branch), `config/scenarios.py`
(`caiso_reserve_coopt` field + the `requires energy_reserve_coopt` validation).
The dispatch machinery is the **unchanged** MISO/PJM per-generator path
(`model/dispatch.py::_build_reserve_rows_pergen`) — no core dispatch change.
**Tests:** `tests/test_reserve_config.py` (`TestCaisoDesign`),
`tests/test_pipeline_kwargs.py`
(`test_apply_reserve_coopt_caiso_flag_lifts_short_circuit`).

## Why the naive (zone-aggregate) build is inert — the design constraint

A zone-aggregate, ungated single reserve family never binds on CAISO: the model's
CC fleet carries ~10 GW of idle evening headroom, so the requirement clears from
idle capacity at zero opportunity cost — the MISO lesson verbatim
(`docs/multi-iso/miso-scarcity-tail-diagnosis.md`). The fix is the **per-generator**
structure: one `R[r,t]` column per (zone, fuel-class) pool of reserve-eligible
units, with

* joint headroom `Σ_{members} P + R ≤ Σ pmax·availability` per pool-hour, and
* the 10-minute deliverability bound `R[r] ≤ Σ FleetArrays.ramp10`
  (`RAMP10_FRAC_BY_GROUP × pmax`, NREL/TP-5500-55588 App. H class ramp rates,
  availability-scaled per hour) as a **variable bound**.

Reserve then competes with energy on the same marginal unit *and* cleared reserve
is capped at what the fleet can physically deliver in 10 minutes. On the real
2023 CAISO fleet the pool is ~1103 units → 11 (zone, fuel-class) R columns with
Σ ≈ 12.9 GW deliverable ramp against a ~2.2 GW requirement — so it clears at ~$0
in normal hours and only bites in the tight evenings when most of that ramp is
already dispatched as energy.

## Requirement — BAL-002-WECC-3 R1 Contingency Reserve

`requirement[t] = max(MSSC, CAISO_CONTINGENCY_FRAC × load[t])`, split
`CAISO_SPIN_FRACTION` (½) spinning / ½ non-spinning across the two co-drawn
families:

* **MSSC** = the fleet-derived most-severe single contingency
  (`largest_single_contingency_mw`, availability-aware, plant-aggregated
  common-mode) — forward-responsive (retire the largest plant and it falls).
* **6% of load** — BAL-002-WECC-3 R1 is `max(MSSC, 3% load + 3% gen)`; with
  gen ≈ load that is ≈ 6% of load. CAISO DMM Annual Report AS chapters report
  operational practice ≈ 6.3% of the load forecast (net imports pull the true
  value toward ~5.4%). Anchored at 6%.
* **Half spinning** — BAL-002-WECC-3 retired the WECC-2a half-spinning
  requirement (FERC 2021); CAISO practice per the DMM AS chapters keeps
  spinning ≈ non-spinning ≈ half.

## Scarcity demand curves — tariff §27.1.2.3.5

Percentages of the `CAISO_ENERGY_BID_CAP_SOFT` ($1,000/MWh) energy bid cap,
discretized into ascending-shortage LP steps by `caiso_reserve_demand_steps`:

* **Spinning:** 10% ($100/MWh), **flat** at any shortage depth — one step
  spanning the requirement.
* **Non-Spinning:** 50% / 60% / 70% ($500 / $600 / $700) at the 70 MW / 210 MW
  absolute shortage tiers, remainder to the requirement.

Both families span every CAISO zone and share the same R pool, so their
shortfall duals **sum** into the marginal energy unit's LMP — CAISO tariff
§27.1.2.4 co-optimization ("upward products sum toward the bid cap when all
short"). Verified in a trivial LP: reserve-short + energy-abundant prices reserve
at $700 (spin $100 + non-spin $600) without lifting LMP; reserve-short +
energy-tight lifts LMP by the summed reserve dual (`test_reserve_coopt`).

## Documented gaps (issue #1492 "Honest expectation" — next increments)

Each would ADD reserve supply, so this first build **over-states** scarcity
ex-ante (rule 1: right structure first, level tuning later — a real mechanism
stays in even if it worsens the fit):

* **Storage** — the dominant CAISO AS provider (2023–25), but
  `_build_reserve_rows_pergen` backs no per-unit storage reserve columns
  (`storage_eligible` is inert on the pergen path). Extending the pergen builder
  with per-unit storage reserve columns is the highest-value next step.
* **Hydro** — a certified spin/non-spin provider (166 plants, ~6.4 GW), but
  `RAMP10_FRAC_BY_*` has no hydro entry so its `ramp10 = 0` and the
  `ramp10 > 0` pergen filter drops it. `_caiso_reserve_eligible` is the seam
  where a published 10-minute hydro ramp fraction would enable it.
* **Regulation Up / Down** — no forward-derivable requirement series; RegDown is
  a downward product the upward-headroom pergen row does not model.

## Measured ramp capability (data intake, #1500 pattern)

The `ramp-capability` clean datatype now carries a CAISO partition
(`scripts/lib/ramp_capability/caiso.py`, BA code `CISO`, CAMPD state `CA`):
per-plant EIA-860 fast-start + CAMPD CEMS 1-hour up-ramp envelope, pooled
2023–2025 (351 plants, 36.8 GW thermal nameplate, 6.5 GW fast-start). It is the
measured *ceiling* on the class-rate `ramp10` when `measured_ramp_capability` is
enabled — an available refinement to the deliverable-reserve pool, kept OFF in
the first A/B probe so the reserve co-opt is a clean single delta.

## A/B probe vs the caiso-51 keeper

*(results appended after the full-span 2023–2025 solve — bundles
`caiso59_reserve_ab_base` (reserve off) and `caiso59_reserve_coopt` (reserve
on); see the calibration log and the backcast dashboard.)*
