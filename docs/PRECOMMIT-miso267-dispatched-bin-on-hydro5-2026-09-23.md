# PRECOMMIT — miso-267: the dispatched-bin denominator, re-solved on the hydro-5 keeper

```
SESSION : miso-267        ISO: MISO        DATA PROFILE: miso
KEEPER  : 2026-09-22-hydro-5-miso-ror (results/calibration/hydro5_miso_ror_span,
          2020-2025, git_sha fda9ece3, composed from SIX single-year bundles).
          Train tier 2023-2025 CALIBRATED; full span NOT-YET.
STEP 1  : DONE, zero LP. MISO's bench parts regenerated ONCE through a repaired
          builder; keeper re-scored, 0 status flips
          (FINDING-miso267-the-oil-reattribution-was-one-sided-2026-09-23.md).
STEP 2  : zero-LP diagnosis (§1) -> the 2020 coal shortfall and the 2020 price
          bias are TWO objects. The coal half is a quantity (ceiling) object;
          the lever below repairs one identified defect inside it.
ARM     : keeper + unit_outage_dispatched_bin_denominator=true. ONE flag. Built,
          default-off, cache-key registered (miso-266). Zero free parameters.
CONTROL : the committed keeper bundle (rule 29(b) form 4), licensed by §3.
SOLVE   : six shards, one year each (rule 36), full bundles pushed (rule 34).
```

## 0. The baseline is the keeper on the REGENERATED bench

Every "before" number below is the keeper scored on the bench parts STEP 1
regenerated (`frontend/data/backcast/status/MISO.js`, rebuilt this session). The
arm is scored on the same parts, so the A/B has one moving side.

| criterion | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| C1 worst cell, TWh (band ±8) | COAL_BIT **−10.76 FAIL** | COAL_BIT −6.66 | CC_REG −7.69 · COAL_PRB +7.67 | CC_REG −7.40 | COAL_PRB −5.68 | unscored (prelim 923) |
| C3a mean LMP (band ±10 %) | **+14.7 % FAIL** | +5.4 % | −9.5 % | +6.9 % | +0.7 % | −0.8 % |
| C3b shape NRMSE (≤ 0.20) | 0.182 | **0.307 FAIL** | 0.139 | 0.105 | 0.102 | 0.107 |
| per-year determination | NOT-YET | NOT-YET | CALIBRATED | CALIBRATED | CALIBRATED | CAL-W-CAVEATS |

## 1. STEP 2 — one cause or two? Two. (zero LP)

`scripts/probes/_miso267_2020_one_cause_phase0.py`: the keeper's own
`hourly/class_hourly` against raw CAMPD (the measured coal series), and its
load-weighted internal price against MISO RT, hour by hour.

| 2020, by RT-price decile | d0 | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 |
|---|---|---|---|---|---|---|---|---|---|---|
| price error, $/MWh | +8.2 | +6.6 | +6.6 | +6.9 | +6.9 | +7.2 | +6.7 | +5.9 | +2.8 | **−19.7** |
| coal model − CEMS, TWh | +1.87 | +0.21 | −1.12 | −2.17 | −2.74 | −3.27 | −3.70 | −3.91 | −3.87 | −3.72 |

* **Hour-grain correlation of coal deficit with price error: 0.10 (BIT) / 0.14
  (all coal).** A coal shortfall that drove the price bias would correlate
  strongly and would lift price most where coal is shortest. It does neither.
* **The price error is a flat body offset** of +$6–8 in RT deciles 0–7 plus a
  −$19.7 miss in the spike decile. **CALIBRATED 2023 carries the same body**
  (+$4.3–10.0 across d0–d7) and passes C3a only because its larger spike miss
  (−$31.8) cancels it. So C3a 2020 +14.7 % is the body without the cancelling
  spikes — **not a 2020-specific object and not the coal object.**
* **The coal deficit is a peak-hours ceiling shape.** By load decile: +0.40 TWh
  in d0 falling to −4.00 in d9 (2020); the fleet is long in the cheapest hours
  and short where load is highest. Annual on the CEMS basis: coal 187.0 vs 209.4
  TWh (−22.4) in 2020, 180.3 vs 195.1 (−14.8) in 2023; BIT 55.6 vs 63.1 in 2020.

**Verdict:** two objects. miso-264 §7 named the 2020 coal object a quantity /
commitment object from the offer side; this is the same verdict from a third
instrument. The short-at-peak half is a ceiling (availability) object; the
long-in-troughs half is a commitment/floor object this lane does not touch.

## 2. The lever, chosen on structure

**`unit_outage_dispatched_bin_denominator`** (MISO cell `O`). Picked because it is
the one built, zero-DOF repair of an identified defect inside the ceiling object
— not because miso-266 measured coal moving:

* **The identity it repairs is `denom == cap_LP`**, which the code claims and
  does not satisfy: `_iso_plant_capacity` returns 50,365.4 MW of MISO coal in
  every year 2020–2025 while the LP's own coal falls 54,238.1 → 53,391.6 MW, and
  at the contradicted plants `denom / cap_LP` is 0.414–0.695 (PRECOMMIT-miso266
  §1). Rule 14 `[R-ACCURATE]` + rule 1 `[R-STRUCT]`.
* **Already adjudicated once.** Solved on the miso-264 base: an exact gate wash,
  the owner ruled promote, and the promotion was withdrawn ONLY because hydro-5
  (a sibling on the same base) landed first (RESULT-miso266 §8.3). This run is
  that arm on the current keeper — nothing about the mechanism changes.
* **Not re-testing an R/I/G cell.** Everything on the DO-NOT-REDO list stays
  closed: FINDING-miso265 §4's four levers, `unit_outage_lp_capacity_basis`,
  `unit_outage_extract_basis_share`, the nameplate numerator half,
  `ordc_scarcity_overlay` (G), `dynamic_reserve_requirements`,
  `energy_reserve_coopt`. MISO hydro is not touched (`hydro_min_flow_floor` /
  `hydro_dispatch_envelope` barred).

**What it cannot fix, stated now:** the C3a price body (routed — no admissible
queue lever reaches a body offset without being a fitted adder); the coal
fleet's trough surplus (commitment); 84.5 % of the ceiling contradiction
(PRECOMMIT-miso266 §3.3); C3b 2021.

## 3. G-DRIFT — form 4 is valid; the keeper is the control

`git diff fda9ece3 <pinned SHA> -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source
data/raw/reference`: 7 files from `main`, plus this branch's builder repair.
**Every hunk INERT for MISO's LP:**

| file | hunk | why INERT |
|---|---|---|
| `scripts/run_calibration.py` | passes `nwpp_grid_carried_wind_served` | NWPP-47 field, default `False`, absent from the keeper recipe |
| `scripts/run_calibration_full.py` (main) | resolves the same flag | same |
| `src/market_sim/config/scenarios.py` | the field + cache-key drop at `False` | default-off; key byte-stable |
| `src/market_sim/data/eia930/demand.py` | `if iso == "NWPP" and …` | another ISO's branch |
| `src/market_sim/data/eia930/envelopes.py` | NWPP-only helper + gated subtraction | another ISO's function |
| `src/market_sim/runner.py` | kwarg pass-through | flag off |
| `src/market_sim/config/constants.py` | `EIA930_PS_SPLIT_COMPLETE_FROM` gains `"SOCO"` | another ISO's entry (MISO is in `EIA930_PS_FOLDED_INTO_WAT`) |
| `scripts/run_calibration_full.py` (this branch) | benchmark-builder repair | `_benchmark_eia923_frame` runs in the post-solve frames step and in `build_benchmark_frames`; it writes the benchmark frame, never an LP input |

**The keeper is year-isolated** (`composed_from` = six single-year bundles), the
exact condition under which miso-266's control legs reproduced their keeper to
0.000008 TWh (RESULT-miso266 §4). No control solve is earned.

## 4. The decision rule, fixed now

* **Adjudicated on rule 14 and rule 1 only.** The arm is reported as the
  candidate whatever §5 shows; a worse gate does not retract it and a better
  gate does not validate it. Every regression is reported at full magnitude.
* **Nothing is swept.** One boolean, `true`. No scope, cohort or threshold
  variant, in this session or a successor's, on the strength of a gate.
* **Rule 21: zero free parameters added. Rule 25: nothing armed outside MISO.**
* **The promotion is the owner's** (rule 31). This session recommends; it
  deletes nothing.

## 5. The prediction, registered before any shard

Direction from miso-266's measured arm − control (its RESULT §2.2), applied to §0.
Magnitudes are indicative: `hydro_ror_split` sits under this arm now and its
interaction is not predicted.

| criterion | year | keeper | predicted arm | |
|---|---|---|---|---|
| C1 COAL_BIT | 2020 | −10.76 FAIL | ≈ −6.8 PASS | leaves the fail set |
| C1 COAL_BIT | 2021 | −6.66 | ≈ −3.4 | better |
| C1 COAL_PRB | 2022 | +7.67 | **≈ +10.1 FAIL** | **adverse** — PRB already long |
| C1 CC_REGULAR | 2022 | −7.69 | **≈ −9.1 FAIL** | **adverse** — gas displaced |
| C3a | 2020 | +14.7 % FAIL | ≈ +13.0 % FAIL | the body offset remains |
| C3a | 2022 | −9.5 % | **≈ −10.3 % FAIL** | **adverse** |
| C3b | 2021 | 0.307 FAIL | ≈ 0.307 FAIL | untouched |
| C1 CC_REGULAR | 2023 | −7.40 | ≈ −7.37 | 0.6 TWh headroom — exposed |
| C3a | 2023 / 24 / 25 | +6.9 / +0.7 / −0.8 % | ≈ +5.8 / −0.1 / −1.7 % | |
| **train tier** | 2023–25 | CALIBRATED | CALIBRATED | predicted, **not promised** |
| **full span** | | NOT-YET | NOT-YET | same failing criteria; fail cells move 2020 → 2022 |

Also expected: price −0.25 to −0.73 $/MWh; coal up and gas/imports down in
every year; CT_PEAKER worse in 4 of 6 years; total generation conserved.

## 6. How it is solved

Six shards, one per year, **arm only**:

```
python scripts/replay_keeper.py results/calibration/hydro5_miso_ror_span \
  --years <Y> --set unit_outage_dispatched_bin_denominator=true \
  --out-dir results/calibration/miso267_dbd_<Y> --note "miso-267 arm <Y>"
python scripts/probes/_miso267_shard_check.py --leg results/calibration/miso267_dbd_<Y> --year <Y>
```

* Prep: `uv sync`; `hydrate_data.py --profile miso`; `curate_coal_stocks.py`;
  `curate_coal_receipts.py`; `curate_hydro_plant_modes.py --iso MISO`.
  (`input_completeness` makes a missing coal or hydro partition fatal.)
* Hard stops: `HEAD` = the pinned SHA; the shard check (recipe = keeper +
  exactly the one flag, per year, including the 2023–25 overlay; hydro
  classifier sha `dc2a9d4be30a0727`).
* Push: `.gitignore` negation for its own out-dir + a **plain** `git add`,
  bundle including `dispatch/<Y>_P1.parquet` (rule 34 (a)).
* Budget: ~15 min solve + setup; a shard at 60 min with no artifact stops.
* **All six years** = the registry's union for MISO (one run, the keeper; none
  stamped to it) — rule 34 (c) / 35 (b).
* Parent: fetch by SHA, `git ls-tree` > 0, re-run the shard check, compose with
  `_miso266_compose_span.py`, `stamp_config_partition.py --check`, register,
  score against the keeper on the same bench, write the RESULT.

## 7. What this session does not claim

* That the arm closes any gate. The argument is the identity in §2.
* That the availability envelope is repaired: 84.5 % of it survives.
* That the price body offset has a cause here. It is routed.
* Anything about another ISO.

## 8. Launch record

(appended at launch)
