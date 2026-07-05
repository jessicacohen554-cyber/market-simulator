# Storage AS-Power Withholding — Mechanism Attribution (2026-07)

Attribution map for the *forecast-mode storage AS power withholding* workstream
(CLAUDE.md rule 19 — one mechanism per phenomenon: enumerate what already
withholds/prices the same duty **before** adding anything). Follow-up to
`docs/storage-modeling-audit-2026-07.md` §1.3. Written before any code change.

**Phenomenon:** ERCOT batteries clear most of their value as ancillary services
(AS); power committed to upward AS cannot also arbitrage energy. Two things must
happen for this to be modeled faithfully: (i) the AS-committed power is
*withheld* from energy in the hours it is held, and (ii) the AS duty is *priced*
(the battery earns the AS clearing value, and its entry economics see it exactly
once).

## Mechanism inventory, per mode

| # | Mechanism | Where | Withholds? | Prices? | Mode | Forward-regenerable? |
|---|---|---|---|---|---|---|
| M1 | `reserve_storage_as_power` — subtract **measured** hourly storage up-AS MW from the storage power cap | `model/storage.py:482`, applied only in `scripts/run_calibration.py:4193` | yes (hard cap cut) | no (energy-only LP) | **backcast** | no — reads `ercot_<year>_as_by_restype_hourly.parquet` (measured award) |
| M2 | `ercot_storage_as_reserve` / `ercot_storage_as_product_credit` — net the **measured** battery award off the AS *requirement* so the co-opt doesn't pull it from thermal | `config/reserve_config.py:422-430, 615-660, 730-737` | n/a (requirement netting) | via co-opt duals | **backcast** | no — same measured series |
| M3 | **Endogenous reserve co-opt with storage participation** — storage headroom `cap − Dis + Chg` backs upward reserve on a shared per-zone pool; the LP chooses energy-vs-AS on the same power cap, priced by the AS demand curves | dispatch `_build_reserve_rows` `use_storage` block `model/dispatch.py:893-996`; design `storage_eligible=True` `reserve_config.py:447, 752` → `reserve_storage=True` `reserve_config.py:328` → `reserve_storage_power_cap=storage_power_cap` `dispatch.py:2217` | **yes (endogenous)** | **yes (LP duals)** | **both** | **yes** — requirement from forward drivers (see M4) |
| M4 | AS **requirement** setting | `results/scarcity.py` | — | — | both | `ercot_as_forward_requirement=True` → **forward** (load/wind/solar formulas, `scarcity.py:943-1063`, constants `reserve_config.py:44-69`); **False → measured plan** `ASPLANNP433_<year>.parquet`, and **returns all-zero for a year with no file** (`scarcity.py:915-916`) |
| M5 | `as_revenue_per_mw_yr` — **exogenous** calibrated $/kW-yr AS credit with penetration saturation, added to entry/retirement screens | `model/ancillary.py:50`; storage entry `model/storage.py:966,972`; thermal retire `capacity.py:527`; thermal entry `capacity.py:1221` | no | **yes (separately, off the LP)** | both (gated `as_revenue_enabled`, ERCOT) | yes (saturation on fleet MW) — but it is a *parallel* pricing, not the co-opt's |

## What actually happens today

**Backcast (`scripts/run_calibration.py`).** M1 (or M2) reserves the *measured*
battery award; M3 runs when `energy_reserve_coopt` is on; `ercot_storage_as_endogenous`
switches M1/M2 **off** and hands the full cap to M3 (`run_calibration.py:4188-4190`,
`reserve_config.py:425/618/733`). Rule-13-admissible measured input; backcast only.

**Forecast (`src/market_sim/runner.py`).**
- `dispatch_kwargs` **always** carries `storage_power_cap`/`storage_zone_idx`
  (`runner.py:763-765`), and the reserve co-opt (M3) is merged whenever
  `energy_reserve_coopt` is on and `iso != CAISO` (`runner.py:802-818`). So **the
  endogenous energy-vs-AS withholding is already reachable in forecast** — it is
  an emergent property of the co-opt, not of a dedicated flag.
- The measured overlays (M1/M2) are **never applied in forecast** — `runner.py`
  has no reference to `reserve_storage_as_power`, `storage_as_commitment`,
  `ercot_storage_as_reserve`, or `ercot_storage_as_endogenous`. Correct per rule 13.
- **`ercot_storage_as_endogenous` is a no-op in forecast.** Its only effect is to
  negate the third operand of `storage_as_commitment AND … AND not endogenous`
  gates that forecast never reaches (`storage_as_commitment` is False). The flag
  is *semantically* "storage prices AS endogenously" but drives nothing forward.
- **Two latent forecast footguns:**
  1. Enabling `energy_reserve_coopt` without `ercot_as_forward_requirement` gives
     a **zero** AS requirement for any year lacking an `ASPLANNP433` file (M4) —
     the co-opt is on but there is *no* AS demand and hence *no* withholding.
  2. **Double-count:** M5 (`as_revenue_per_mw_yr`) is added to the storage entry
     screen unconditionally under `as_revenue_enabled` (`storage.py:966,972`),
     with no awareness of M3. When M3 prices storage AS (duals + AS-widened
     arbitrage spreads captured by `estimate_storage_revenue` off prior-year
     prices), the exogenous M5 credit is a *second* pricing of the same duty.
     There is **no mutual-exclusion validator** (`scenarios.py:2941` checks only
     `mode`/`hydro_year`).

## Answers to the task's step-1 questions

1. *Does runner.py's forecast path pass `reserve_requirement` / storage reserve
   participation?* **Yes.** `storage_power_cap`/`storage_zone_idx` are always in
   `dispatch_kwargs`; `build_reserve_dispatch_kwargs` (with `reserve_storage=True`
   from the ERCOT design) is merged whenever `energy_reserve_coopt` is on.
2. *What does `ercot_storage_as_endogenous` do end-to-end, and is it reachable
   from a forecast config?* Backcast: switches M1/M2 off and hands the full cap
   to M3. Forecast: **reachable but inert** — a no-op, because the measured path
   it disables is never taken in forecast.

## Design implication (what this workstream changes)

The dispatch mechanism (M3) needs **no new LP structure** — it exists and is
tested (`tests/test_ercot_storage_as_endogenous.py`). The gaps are:

- **G-A (reconcile pricing, rule 19):** make M5 and M3 mutually exclusive for
  storage. When `ercot_storage_as_endogenous` is on, the storage entry screen
  must **derive** the AS credit from the co-opt's own duals (M3), never add the
  exogenous M5 credit — exactly one prices storage AS.
- **G-B (make the flag meaningful + close the footguns):** `ercot_storage_as_endogenous`
  requires the co-opt (`energy_reserve_coopt`), and in forecast mode requires a
  forward-regenerable requirement (`ercot_as_forward_requirement`) so M4 is never
  the silent-zero fallback. Enforced in `__post_init__`; surfaced (not silent).
- **G-C (thermal reconciliation, rule 19) — RESOLVED 2026-07-05.** The same
  M5-vs-M3 double-count for *thermal* AS in `capacity.py` (retirement + new-entry
  screens) is now gated by `ercot_thermal_as_endogenous`, the thermal analogue of
  `ercot_storage_as_endogenous`. See the follow-up section below.

## Follow-up seams (2026-07-05)

### Seam 1 — thermal AS double-count (RESOLVED, `ercot_thermal_as_endogenous`)

**Decision: DERIVE, not gate-off.** The exogenous flat `as_revenue_per_mw_yr` was
added unconditionally to the thermal retirement (`capacity.py`
`apply_economic_retirements`) and new-entry (`apply_economic_new_entry`) screens
even when `energy_reserve_coopt` prices thermal AS endogenously — a second pricing
of the same duty (rule 19). Two options were on the table:

- **Gate-off** (suppress the exogenous credit under the co-opt): rejected. The
  co-opt lifts the *energy* price in scarcity hours (already captured in the
  screens' `energy_margin`), but the direct *reserve* payment a part-loaded
  thermal unit earns on its held headroom is **not** in the energy margin.
  Dropping the exogenous credit with nothing in its place would strip that real
  income and over-retire tail thermal — the exact bias `ancillary.py` warns about.
- **Derive** (chosen): credit the per-fuel AS value read straight off the co-opt's
  own reserve duals via `ancillary.realized_thermal_as_revenue_per_mw_yr_by_fuel`
  (built on `scarcity.ercot_as_aware_unit_value`, the model's own P1 reserve dual —
  never a measured MCPC), and suppress the exogenous flat rate. Exactly one
  mechanism prices thermal AS, and it is forward-regenerable (falls as the fleet
  grows and the AS price collapses; rule 13). Mirrors the storage G-A treatment.

**Mechanism.** `runner.py` computes the per-fuel `$/MW-yr` map from the solved
year's `reserve_price_by_family` + dispatch (ERCOT + flag only) into
`prior_results["thermal_as_revenue_per_mw_yr"]`; `evolve_fleet` reads it and
passes it to both screens, which use `map.get(fuel, 0.0)` in place of the
exogenous rate. **Attribution caveat:** `ercot_as_aware_unit_value` prices the
unit's full reserve-eligible headroom, so the pooled per-fuel rate is an *upper
bound* on realized AS income — the same upper-bound attribution the storage helper
carries (documented in both docstrings).

**Keeper-invariance.** Capacity evolution (`evolve_fleet` and both screens) runs
**only in forecast** — backcast calibration (`scripts/run_calibration.py`) never
calls it — and the flag defaults off, so every backcast keeper is byte-identical.
Guards in `__post_init__`: requires `energy_reserve_coopt`; forecast +
`ercot_multiproduct_as_coopt` requires `ercot_as_forward_requirement` (same
zero-requirement footgun as the storage flag). Tests:
`tests/test_ercot_thermal_as_endogenous.py`.

### Seam 2 — PJM synchronized-reserve storage duty (LEFT, no code change)

**Decision: leave the seam.** The gate was: proceed only if a *forward-valid,
storage-specific* PJM synchronized-reserve power series (the ERCOT
`reserve_storage_as_power` analogue — a resource-specific MW reservation) can be
intaken through the data contract, with no cross-ISO reuse of any ERCOT-calibrated
value (rule 24). The PJM AS data already on disk (`data/raw/PJM-AS/`) carries only
**market-level** synchronized-reserve requirement and clearing, broken out by
`locale ∈ {PJM_RTO, MAD}` and `service ∈ {REG, SR, PR/NSR, 30MIN}` — there is **no
resource-type / storage / pumped-storage breakout** anywhere in
`reserve_market_results`, `ancillary_services`, or `pjm_*_as_up_mw` (whose columns
are `sr_req_mw` / `as_up_mw`, market totals). A PS reservation cannot be recovered
from a market total without either a fitted storage share or an ERCOT-borrowed one
— both forbidden. And the phenomenon that would motivate it is absent: the
`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` note (`constants.py`) records that PJM PS
cycles ~correctly (~9–10 TWh) and the old $10 adder was retired as a
mis-measurement, so the sync-reserve reservation was only ever the "if PS later
over-cycles" replacement. No over-cycling, no forward-valid storage-specific
series → nothing to intake. Seam stays documented, unbuilt.

### Seam 3 — real ERCOT forecast before/after delta (measured)

Bounded ERCOT forecast **2026–2030**, weather-year 2024, legacy heat-rate bins
(fast-fleet probe — the four flags act on the reserve co-opt / storage block,
independent of thermal offer-curve granularity, so the mechanism deltas are
directional; absolute levels are not keeper-grade). NOT a backcast; **no
dashboard** (per task). 2022 / H1-2026 stay quarantined. Baseline = all four flags
off; treatment = `energy_reserve_coopt + ercot_multiproduct_as_coopt +
ercot_as_forward_requirement + ercot_storage_as_endogenous` on. Script:
`scratchpad/seam3_forecast_delta.py` (probe, not committed).

| year | Δ daily spread $/MWh | Δ mean price $/MWh | Δ discharge TWh | Δ storage build MW | Δ cycles/yr |
|------|---------------------:|-------------------:|----------------:|-------------------:|------------:|
| 2027 | +0.00 | +0.01 | +0.08 | 0 | +4.2 |
| 2028 | −0.01 | −0.02 | −0.04 | 0 | −1.5 |
| 2029 | −0.00 | +0.00 | −0.10 | 0 | −4.5 |
| 2030 | −0.03 | −0.03 | −0.00 | 0 | −0.2 |

**Finding: the stack is essentially inert in this forecast (all deltas <1 %).**
Storage build is *identical* (20 GW in 2027, 23 GW 2028–2030 in both — economics-
bound below the 45 GW ceiling, not cap-bound), and price spread / cycling move by
noise-level amounts with no consistent sign.

**Why — the mechanism is working as designed, not broken.** At the forecast's
20–23 GW battery penetration the co-optimized AS price collapses (a large fast-AS
fleet against a small forward AS requirement), so the endogenous storage AS credit
derived from the reserve duals is ≈ 0. It therefore neither pulls extra storage
across the entry hurdle nor withholds meaningful energy — exactly the
forward-saturation behavior the endogenous pricing exists to produce (AS value → 0
as the fleet grows), and the reason it is *safe* to enable in forecast: it adds no
spurious build or price distortion where AS is no longer scarce. The double-count
it closes only bites when AS is scarce *and* the exogenous `as_revenue_enabled`
rate is live; at forecast saturation both the double-count and its fix are moot.

**Thermal path (seam 1) verified in the same forecast.** A 2026–2028 run with
`ercot_thermal_as_endogenous` additionally on confirms
`realized_thermal_as_revenue_per_mw_yr_by_fuel` is invoked each evolved year and
attributes the right fuels (coal, gas_cc, gas_ct, oil), with derived rates ≈ $0/MW-
yr for the same AS-saturation reason — so the thermal reconciliation runs cleanly
end-to-end and likewise introduces no forecast distortion at this penetration.
Script: `scratchpad/seam3_thermal_verify.py` (probe, not committed).
