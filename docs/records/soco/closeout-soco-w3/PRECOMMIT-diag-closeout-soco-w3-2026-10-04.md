# PRECOMMIT closeout-SOCO-w3 — DIAGNOSTIC: metered coal commitment state on the holdout recipe (7 shards)

Lane closeout-SOCO-w3, 2026-10-04. Desk direction (2026-10-04): build the CEMS coal online-state overlay as a
default-OFF, labelled **DIAGNOSTIC** probe; never promotable; stack on the holdout recipe; solve all 7 years; score
against the holdout control; the result goes to frontier row SOCO-F1 as conduct evidence. No slot request.
Written and pushed before any shard launches.

## 1. What it is, and why it can never be a keeper

- **Field.** `ScenarioConfig.diagnostic_coal_metered_online_floor` (new, default False, backcast-only via
  `_BACKCAST_ONLY_OVERLAY_FIELDS`, cache-key optional at False, TIER_TAGS 1). Matrix row
  `diagnostic_coal_metered_online_floor`, cell O in SOCO and U in the other eight shards, each marked
  **NEVER PROMOTABLE**.
- **Engine.** `pipeline.commitment.wrap_coal_metered_online_diagnostic_prep` chains after the incumbent P1 fleet
  prep (the SOCO gas-steam campaign floor) in all three orchestrators. D-2 id `MECH_DIAG_COAL_METERED_ONLINE` (28),
  ablated.
- **Input.** `data/raw/_processed-legacy/coal_metered_online_floor_SOCO.parquet`, written by
  `scripts/data/derive_coal_metered_online_floor.py`. The derive imports the frozen `derive_thermal_tranches`
  coal-unit crosswalk and parasitic map. Per plant-year the floor is the P5 of the plant's own online coal net MW,
  applied in every metered-online hour. Each plant's floor fills mustrun → committed → econ → peak, capped at
  pmax × availability.
- **Rule 13.** It pins measured commitment **state**, an observed outcome with no forward story, which rule 13
  forbids in a keeper. It is admitted only in the form rule 13 allows: a default-off, labelled diagnostic probe.
  It is never stacked into any keeper recipe and never registered on main.

## 2. Recipe

Keeper `closeout_soco_3_span` replayed with `--set mustrun_chp_btm_holdout=true --set
diagnostic_coal_metered_online_floor=true`, i.e. the holdout control plus the diagnostic. Pin = this branch's HEAD
after this commit (a full SHA, recorded in the RESULT). The G-DRIFT from the holdout pin `487bfdb8` to the new pin is
this lane's own diff: the new field, its wrapper and wiring, the `_run_config_mustrun_chp_btm` rebuild-reader fix
(scoring side), docs, probes and the artifact. Each hunk is INERT for the control recipe because the field is off
there (fast lane 6,701 passed).

## 3. The question and how it is read (fixed now)

Zero-LP upper bound (FINDING-cc-overrun §6): +4.49 / 2.94 / 2.00 / 1.78 / 2.06 / 2.05 / 1.30 TWh of coal for
2019–2025.

**Q (the desk's): is metered commitment practice the whole story behind the CC over-run?** Read per year on the
probe − control class deltas:

- **Realised floor energy:** Δ(COAL_BIT + COAL_PRB).
- **Displacement share:** −ΔCC_REGULAR / Δcoal; also reported for CT_PEAKER, ST_GAS and hydro timing.
- **CC 2021 / 2023:** does C1 CC_REGULAR return to PASS? The control has +8.63 TWh against a 7.10 band (2021) and
  +7.57 TWh against 7.04 (2023).

**Pre-registered readings.**

- **"Commitment practice explains the CC over-run"**: CC 2021 and CC 2023 both PASS, and the displacement share
  from CC is ≥ 0.5 in both.
- **"Partly"**: at least one of the two flips clears, or the CC share is between 0.3 and 0.5.
- **"No"**: neither clears, and the CC share is < 0.3 (the coal then displaces CT, ST or hydro timing instead).

Also reported, never gating: C3a/C3b every year (night price effect), C4, C8 (the diagnostic's forced coal share is
attributed to its own id), COAL_BIT 2019.

**Kills (structural only):** unserved energy or dump > 0; the shard log lacks the `DIAGNOSTIC coal metered online
floor` line (the arm was not live); the recipe differs from control + the diagnostic.

## 4. Disposition

Whatever the reading, the run is registered nowhere on main, never promoted, and recorded in the SOCO `SOCO.js` cell
and in frontier row SOCO-F1's evidence via the desk. The bundle is kept on a `-diag` branch.
