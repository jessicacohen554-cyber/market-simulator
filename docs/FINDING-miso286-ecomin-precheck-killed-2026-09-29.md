# FINDING — miso-286: the chartered EcoMin online floor is built (default off) and KILLED by its own pre-registered pre-check. No shards spent.

```
LANE    : miso-286 (owner charter docs/handoffs/CHARTER-miso285-ecomin-price-taker-2026-09-29.md)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Fleet-only rebuilds (P0 offer stack) + keeper committed P1 hourly sidecars
PROBE   : scripts/probes/_miso285_night_stack.py --cf4  ->  results/calibration/_miso285_night_stack.json (key "cf4")
CODE    : ScenarioConfig.miso_gas_ecomin_online_floor (default off), MECH_MISO_GAS_ECOMIN_ONLINE (26),
          constants.MISO_GAS_ECOMIN_MIN_LOAD_FRAC = 0.323767, pipeline.commitment.build_miso_gas_ecomin_p1_prep,
          CLI --miso-gas-ecomin-online-floor, D4_WINDOWS entry, tests/iso/miso/test_miso_gas_ecomin_online_floor.py
CELLS   : miso_gas_ecomin_online_floor (new row) MISO = I;  diurnal_price_amplitude O -> G
```

## 1. Answer

The kill rule (charter §3, fixed before measuring) fires in **7 of 7 years**. The floor moves the night median by
at most $0.12. The lane stops; no PRECOMMIT, no shards.

| year | P0 stack median | CF4 median | Δ median | Δ mean | floored MW added | online CC committed MW (stack) | keeper P1 CC committed MW |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 23.59 | 23.59 | −0.01 | −0.01 | 3,837 | 5,495 | 5,224 |
| 2020 | 20.16 | 20.16 | −0.00 | −0.02 | 3,716 | 5,374 | 5,082 |
| 2021 | 29.65 | 29.56 | −0.09 | −0.01 | 2,598 | 3,653 | 4,268 |
| 2022 | 42.99 | 42.86 | −0.12 | −0.03 | 2,149 | 3,046 | 5,636 |
| 2023 | 27.11 | 27.11 | −0.00 | −0.02 | 5,151 | 7,632 | 7,295 |
| 2024 | 23.76 | 23.76 | 0.00 | −0.01 | 5,544 | 8,148 | 7,784 |
| 2025 | 32.83 | 32.83 | −0.01 | −0.01 | 5,117 | 7,486 | 7,584 |

Night = h0–5. Prices in $/MWh. The online pattern (the stack's own per-hour P0 clear) matches the keeper's P1 CC
committed MW within ~±0.5 GW in 5 of 7 years, so the proxy for "P0-online" is sound. 2021 and 2022 sit lower in the
stack clear than in P1; both years' P0 stack already diverges from P1 (miso-285 §4).

## 2. Why it cannot move the price

- The floor only touches units that are **already online**, which in a merit-order clear are already dispatched.
  Making dispatched MW must-take changes nothing unless the floored row is the **marginal** one, and then only by
  the MW between its dispatch and its floor. That happens in ~10–14 % of night hours (214–303 of ~2,190), and each
  time by cents.
- CF1's −$0.6 to −6.3 (miso-285) came from flooring **every** committed CC row, **including offline units**. That
  is forcing extra commitment at night, not EcoMin price-taking. It would also push night CC above CAMPD, where it
  currently matches. It has no admissible driver.
- So the structural claim in the charter holds, but it is already true in the LP at matched Q. It is not the source
  of the $4–10 night overshoot.

## 3. Build details (merged default off)

- **Level:** MISO CC_REGULAR plant-basis minimum stable load **0.323767** (p25 0.286 / p75 0.449; 39 units,
  27,753 MW; CAMPD 2023–2025). From `derive_campd_gas_commitment_params.py --iso MISO --plant-basis` →
  `data/raw/_processed-legacy/campd_gas_commitment_params_plant_MISO.csv`. Plant basis because the detector floors
  `frac × plant pmax`, capped at the committed tranche.
- **Window:** ercot141 online-hours leg only. The detector's physical restart bar has no off switch, so gaps are
  masked back out after the call; no gap is ever floored.
- **Eligibility (rule 18):** gas_cc, not CHP, min-down ≥ 4 h, **and** the plant's base (lowest-heat-rate)
  startup-bearing tranche.
- **One-slot guard:** arming it together with `miso_coal_night_floor` raises. The orchestrators carry one
  `p1_fleet_prep`, and composition is not built.

## 4. Two defects found on the way

1. **Shared-detector eligibility admits `_peak` tranches (cross-ISO, not fixed here).** `assembly.py` gives peak
   tranches the fast-start startup cost (`_fsp_peak`), so `model.commitment._ra_bridge_unit_params` admits them.
   Its docstring says only the committed tranche carries a startup cost, which is false for MISO: 27 CC_REGULAR plus
   7 CC_CHP `_peak` rows in 2024. This field restricts to the base block. Any **other** ISO's armed bridge that
   passes `gas_cc` through the detector may floor its duct-fire block when P0 runs it. That is for each ISO's own
   lane to check (rule 25); no verdict transfers.
2. **My first CF4 draft zeroed MISO's priced export sinks**, the caiso-138 §D defect: `max(pmin < 0, 0)`. The
   draft read −0.3 to −2.7. The shipped probe changes only the floored rows. The mechanism itself uses
   `preserve_absorption=True`. The superseded numbers are recorded here only so nobody quotes them.

## 5. Where MISO stands

- Keeper unchanged. Train tier 2023–2025 **CALIBRATED** (C3c ledgered).
- Full span **NOT-YET** on three routed misses: C1 ST_GAS 2019, C3a 2022, C3b 2021. **No frontier.**
- `diurnal_price_amplitude` returns to **G**. The remaining night level is the real night offer book at matched
  position; `measured_offer_surface` is R (miso-151) and nothing here is new evidence against that.
- **Still open, not chartered:** P1 sits +$5.1 (2022) and +$1.9 (2025) above the P0 stack at the same Q
  (miso-285 §5). 2022 is also the C3a routed-miss year.

## 6. Owner ruling (2026-09-29)

*"P1 vs P0 residual (Recommended)"*. The next lane (miso-287) runs a zero-LP phase 0 on why P1 clears +$5.1 (2022)
and +$1.9 (2025) above the P0 stack at the same night quantity. 2022 is also the C3a routed-miss year.
