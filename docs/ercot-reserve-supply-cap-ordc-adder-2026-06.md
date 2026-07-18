# ERCOT reserve-supply cap + ORDC adder — the measured-RTOLCAP track (structurally correct; broad-May is energy-base)

**Date:** 2026-06-26
**Branch:** `claude/ercot-rtolcap-reserve-supply-mjutzc`
**Status:** lever BUILT, tested, default-off, ERCOT-gated, legacy byte-identical,
pure-LP. The mechanism is **structurally faithful and forms the acute/tail
scarcity endogenously from measured RTOLCAP + the published ORDC curve (no
overlay, no price fit)** — but it does **not** meet the broad-May greenlight gate,
because the broad-May elevation is an **energy-base** phenomenon, not an ORDC-adder
one. The measured DAM-AS overlay (run157) **stays** the ERCOT keeper / pre-RTC+B
broad-month bridge. Dashboard run `161`.
**Reads first:** `docs/ercot-reserve-supply-scarcity-handoff-2026-06.md` (the
measured RTOLCAP target), `docs/ercot-multiproduct-as-coopt-2026-06.md` (run159),
`docs/ercot-as-aware-commitment-2026-06.md` (the previous rejected probe).

---

## The market-design framing (the fork this resolves)

The previous track (AS-aware commitment) tried to make the endogenous co-opt's
*shared-headroom dual* lift the broad-May LMP. This session established the
correct division by market design:

- **Pre-RTC+B (2023-2025, ORDC regime):** ERCOT ran **energy-only real-time SCED**
  and then *added* the ORDC price adder (RTORPA), a published curve evaluated at
  the **on-line reserve level (RTOLCAP)** — literally `RTSPP = SPP +
  ORDC(online reserves)`. The faithful representation is therefore an **additive**
  adder, not a co-opt lift.
- **Forward (RTC+B, 2026+):** energy and AS are co-optimized; the reserve dual
  lifts the LMP through the shared-headroom constraint. That is the endogenous
  multi-product co-opt, already built, and it stays the forward methodology.

A pure reserve-supply cap (`ΣR ≤ RTOLCAP`) **prices reserve without lifting the
energy LMP** — the energy term cancels out of a reserve-only cap (verified in
`tests/test_ercot_multiproduct_coopt.py::TestReserveSupplyCap`). That is exactly
the property the ORDC-regime additive construction needs: the capped reserve dual
*is* the ORDC adder, added to the energy SPP for ORDC-regime years.

## What this build is

1. **`config.ercot_reserve_supply_cap`** (+ `ercot_reserve_supply_cap_from_year`,
   default 2023) — flags; CLI `--ercot-reserve-supply-cap`.
2. **`scarcity.ercot_rtolcap_supply_cap_mw`** — the measured on-line responsive
   reserve-supply cap from `data/raw/ercot/ercot_<year>_ordc_reserves_hourly
   .parquet`: one row at `RTOLCAP` for the single lumped product, or two rows
   (`RTOLCAP`, `RTOLCAP+RTOFFCAP`) for the multi-product stack. The 2025 RTC+B
   go-live tail (NaN RTOLCAP after 2025-12-05) is left uncapped.
3. **`model.dispatch._build_reserve_rows(reserve_supply_cap=…)`** — adds, per
   headroom row, a system-wide cap row `Σ_z Σ_{p∈row} R[p,z] ≤ cap[row,t]`,
   inserted between the headroom and balance blocks so the balance-dual indexing
   is unchanged. Works for both the legacy single-product and additive
   multi-product specs; absent ⇒ byte-identical LP. Threaded through
   `build_constraints` / `DispatchModel` / `solve_dispatch`.
4. **`run_calibration.py`** — both ERCOT co-opt branches set
   `reserve_supply_cap=ercot_rtolcap_supply_cap_mw(config, hours)` when the flag
   is on (forecast mirror in `runner.py`).
5. **`run_calibration_full._system_frame`** — for ORDC-regime ERCOT years with the
   cap on, the capped reserve dual is **added to the energy LMP** as the ORDC
   adder (persisted in an `ordc_adder` column for audit), matching the
   energy-only-SCED-plus-adder design; gated OFF for RTC+B (year ≥ go-live).

**Honesty gate.** The supply is the measured RTOLCAP/RTOFFCAP (an exogenous
physical on-line reserve capability), the demand is ERCOT's published NP6-576-ER
ORDC curve (`ordc_lolp_params_path`). Nothing reads the LMP, RTSPP, RTORPA or
MCPC; the adder forms from the LP balance dual against the published curve. No
price fit (CLAUDE.md #11/#12).

## Greenlight gate — NOT met (broad May is energy-base, not adder)

2024, overlay OFF, single-product published-ORDC co-opt + RTOLCAP cap + additive
adder (`scripts/archive/run_161.py`, `KEEPER_YEARS=2024`; `_eval_may_gate.py`):

| metric | run161 (cap+adder) | run159 (no cap) | target / actual |
|---|---|---|---|
| 2024 annual | 23.7 | 22.4 | 26.8 |
| May month | **24.3** | 21.3 | 40.6 (RT) / 46.7 (DAM) |
| May acute (8/24/26) | 58.2 | 40.0 | ~45 |
| Aug month | 33.2 (held) | ~29 | 38.6 |

**Full 3-year (run `161`, `_eval_may_gate.py`, demand-wtd model vs actual RTSPP):**

| yr | model | actual | MAE | May μ | May act | acute | Aug μ | Aug act |
|----|-------|--------|-----|-------|---------|-------|-------|---------|
| 2023 | 62.3 | 61.3 | 15.4 | **72.1** | 30.9 | 78.9 | 180.9 | 216.6 |
| 2024 | 23.7 | 28.6 | 4.8 | 24.3 | 40.6 | 58.2 | 33.2 | 38.6 |
| 2025 | 33.5 | 33.4 | 2.7 | 30.2 | 37.4 | 30.4 | 41.3 | 37.1 |

2025 is clean (MAE 2.7); 2024 broad-May under-fires (energy-base, below); **2023
May over-fires hard ($72 vs $31)** — in the low-RTOLCAP 2023 year (mean 13.5 GW vs
16.7 in 2024) the cap binds across far more hours so the adder fires too broadly,
and it double-counts with the RTORDPA overlay (kept from the run157 recipe, which
itself carried 2023). 2023's annual ($62 vs $61) is coincidental cancellation
(May over, Aug under), not a fit. Clear **rejected probe**.

**What works:** the lever forms the acute/tail scarcity **endogenously** from the
measured on-line reserve + published curve, with no overlay — the structurally
faithful ORDC-regime mechanism, clean in 2025. But it is not deployable as-is: the
broad-month behaviour is wrong in both directions (2024 under, 2023 over), and
neither failure is a reserve problem.

**Why the broad month does not lift — and why that is correct, not a tuning
failure.** Decomposing May 2024: the ORDC adder fires in only **70 of 744 May
hours** (the low-RTOLCAP tail), adding **$5 dw** ($18.5 base → $23.5). May RTOLCAP
is p10/p50/p90 = **9.5 / 14.0 / 21.6 GW**; the published ORDC curve tops out at
~11.3 GW, so >80% of May hours have too much on-line reserve for the adder to
fire. **This matches measured reality**: ERCOT's actual RTORPA was ~$0 in the
moderate band and only fired at RTOLCAP ~6.5-8 GW (the handoff's own numbers).

So the broad-May elevation (~$17 of the gap vs actual RT $40.6) is an **energy-base**
phenomenon — the model's May energy LMP is too low because its fleet isn't tight
enough (the documented CC over-run / ST_GAS+CT_PEAKER under-dispatch / offer-curve
merit-order miss). An ORDC adder structurally **should not** paper over an
energy-base miss (CLAUDE.md #1), and the handoff already classes that miss as a
**separate offer-curve track, explicitly NOT a reserve-supply target**.

## Conclusion / status

- The reserve-supply cap + ORDC adder is the **faithful pre-RTC+B ORDC-regime
  mechanism** the user confirmed: it forms acute/tail scarcity from measured
  RTOLCAP + the published curve, endogenously, with no overlay and no fit. Kept as
  a default-off, ERCOT-gated lever; the forward structure stays the endogenous
  multi-product co-opt.
- It is a **structurally-correct probe**, not a broad-month keeper. The DAM-AS
  overlay (run157) **stays** the ERCOT keeper / pre-RTC+B broad-month bridge.
- The broad-May residual is re-attributed to the **energy-base / offer-curve /
  merit-order track** (CC over-run vs ST_GAS+CT_PEAKER under-dispatch) — the next
  lever for the broad month, independent of reserve supply.

### Ruled out / confirmed this session (adds to the rejected-approach log)

- **Headroom-RHS reduction (online-capacity pool / RTOLHSL)** — would lift the LMP
  via the shared-headroom dual but carries feasibility/load-shed risk and is the
  RTC+B (co-opt) mechanism, not the ORDC-regime one. Not the backcast lever.
- **Pure reserve cap at RTOLCAP** alone — prices reserve but cannot lift the LMP
  (energy cancels); only meaningful paired with the additive ORDC adder (this
  build).
- **Broadening the published curve to fire across the moderate band** — would be a
  price-fit (the measured RTORPA was ~$0 there); rejected. The broad month is
  energy-base.

## Files

- `src/market_sim/config/scenarios.py` — `ercot_reserve_supply_cap`,
  `ercot_reserve_supply_cap_from_year` (+ TIER_TAGS).
- `src/market_sim/results/scarcity.py` — `ercot_rtolcap_supply_cap_mw`.
- `src/market_sim/model/dispatch.py` — `reserve_supply_cap` cap rows
  (`_build_reserve_rows`, `build_constraints`, `DispatchModel`, `solve_dispatch`).
- `scripts/run_calibration.py` / `src/market_sim/runner.py` — cap wiring (both
  co-opt branches).
- `scripts/run_calibration_full.py` — `solve_and_persist` flag + CLI; the
  `_system_frame` ORDC-regime additive adder (`ordc_adder` column).
- `scripts/archive/run_161.py` — the overlay-off cap+ORDC-adder run driver.
- tests: `tests/test_ercot_multiproduct_coopt.py`
  (`TestReserveSupplyCap`, `TestReserveSupplyCapLoader`).
