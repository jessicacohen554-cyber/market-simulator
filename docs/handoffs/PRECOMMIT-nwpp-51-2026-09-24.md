# PRECOMMIT nwpp-51: arming `eia860_vintage_tracks_solve_year` for NWPP (card D2). Zero LP.

**Lane:** NWPP-51 · **Date:** 2026-09-24 · **Zero LP.** Nothing solved, nothing registered, no `src/`
change. No mechanism was tested, so no matrix cell moves (rule 28(b); the NWPP-48 / NWPP-50 precedent).
**Control:** keeper `2026-09-24-nwpp-49-ror-split` (`results/calibration/nwpp49_ror_span`, basis
`c2d5991ceece88d9ced57bfa84c0a88b98bc423d`), rule 29(b) form 4.
**Probes:** `scripts/probes/_nwpp51_vintage_census.py` → `results/calibration/_nwpp51_vintage_census.json`;
`scripts/probes/_nwpp51_predict.py` → `results/calibration/_nwpp51_predict.json`.
**Evaluator (committed before any leg):** `scripts/probes/_nwpp51_gates.py`.

**Framing.** D2 is a rule-14 accuracy fix, not a C4 lever. Nothing below selects it by a gate.

## 0. In one line

The fuel switch is real and confined, **but arming the flag as the data sits today also re-prices
Colstrip.** `vintage_2023/` and `vintage_2024/` ship no `eia860_utility.parquet`. So the ownership
leg of the self-commit scope silently goes empty, and Colstrip's 709 MW committed band moves from
$4.50 to $29.48 in both years. That is a data gap, not a 2023 fact. **Recommendation: take the
utility sheet for both vintages first (zero LP), then solve the `repaired` variant.**

## 1. Census (flag off vs on, `run_year(fleet_only=True)` on the keeper recipe)

| year | LP units off → on | fuel switch (ST_GAS → COAL) | other movers | byte-identical |
|---|---|---|---|---|
| 2023 | 646 → 629 | **Jim Bridger 8066: 1,070 MW** · **North Valmy 8224: 254 MW** | Colstrip committed-band re-price (§2) · ±60 MW nameplate edits on 11 gas plants · 5 zero-availability rows dropped | no |
| 2024 | 641 → 652 | **North Valmy 8224: 254 MW** | Colstrip re-price (§2) · ±35 MW nameplate edits on 6 gas plants · +5.4 MW oil | no |
| 2025 | 642 → 642 | none | none | **yes** (digest `428020c25d1a…` both sides) |

* COAL class: 2023 +1,324.0 MW / +8.32 TWh available; 2024 +254.0 MW / +1.81 TWh.
* ST_GAS: 2023 −1,324.0 MW / −9.43 TWh available; 2024 −254.0 MW.
* The handoff's "1,441 MW (2023) / 277 MW (2024)" is nameplate. The LP carries 1,324 / 254 MW.
* The dropped CT rows (55841 444 MW, 67766 165.6 MW, 69880, 54374) are built after 2023. They
  carried **0.000 TWh** of availability under the flag-off COD ramp, so they are inert.
* CAMPD confirms the direction: JB 1–2 burned coal all of 2023 (2.31 / 2.32 TWh gross) and gas in
  2024–25. Valmy 1 burned coal in 2023 and 2024, and mostly coal in 2025.

## 2. The defect the census found: the vintage dirs have no utility sheet

`eia860_costofservice_majority_plants` needs `eia860_owner`, `eia860_plant` **and**
`eia860_utility` in the active directory. It returns an empty set when any is missing
(`eia860.py:4104`). `vintage_2023/` and `vintage_2024/` carry the operable-sheet set only (README,
"Vintage snapshot completeness").

| check | canonical | vintage_2023 | vintage_2024 |
|---|---|---|---|
| COS-majority plants | 4,491 | **0** | **0** |
| same, with the canonical utility sheet linked in (scratch test) | — | 4,211 (Colstrip in) | 4,368 (Colstrip in) |
| Colstrip 6076 in the NWPP-44 scope | yes (COS leg) | **no** | **no** |

Colstrip's operator is NR, so it is in scope only through ownership. Its owners are cost-of-service
utilities in all three years. The re-price is therefore an artefact of a missing file (rule 14).

* **Readers:** one (`eia860.py:4102`). The consumers are the NWPP-44 committed-band gate (NWPP only)
  and MISO's `coal_prb_committed_split` / commitment path (MISO artifacts). Only SPP arms the vintage
  flag in a backcast, and neither consumer is armed there. A full blast-radius census belongs to the
  intake.
* **Fix (proposed, not done):** process the `eia860_utility` sheet from EIA's own `eia8602023.zip`
  and `eia8602024.zip` into each vintage dir (`scripts/data/process_eia860.py`). eia.gov is reachable
  from this container. Zero LP. Canonical entity types are **not** substituted: the fix uses the
  vintage's own sheet.

## 3. Prediction (price-taker against the keeper's own P1 prices)

Method check: the price-taker reproduces the keeper's own plant energy with the flag off. JB comes
out at 4.434 vs 4.413 TWh, Valmy 0.551 vs 0.492, Colstrip 10.844 vs 10.260.

* `hi` = the touched plants' coal tranches as price-takers. This is an upper bound: price is held,
  and only gas is displaced.
* `lo` = the flat-block increment only, which first displaces the keeper's coal econ/peak band
  output in the same hour.

| year | variant | Δ model coal, TWh [lo, hi] | coal r [lo, hi] (keeper) | coal r_intra [lo, hi] (keeper) |
|---|---|---|---|---|
| 2023 | **repaired** | **+0.629 … +5.045** (JB +4.523, Valmy +0.522 at hi) | 0.655 … 0.662 (0.660) | 0.330 … 0.395 (0.375) |
| 2024 | **repaired** | **0.000 … +0.667** (Valmy only) | 0.618 … 0.625 (0.618) | 0.404 … 0.471 (0.404) |
| 2023 | as_is | −0.903 … +3.513 (Colstrip −1.531) | 0.640 … 0.651 | 0.333 … 0.395 |
| 2024 | as_is | **−2.585 … −1.917** (Colstrip −2.585) | 0.580 … 0.582 | 0.422 … 0.469 |
| 2025 | both | **0 (byte-identical fleet)** | 0.638 | 0.369 |

* **C4: unchanged.** Coal r moves ≤ 0.007 in the repaired variant. This matches the charter's
  expectation.
* **C1 CC_REGULAR 2023 (keeper −7.213 vs ±8.00):**
  * It flips if CC_REGULAR loses more than 0.787 TWh.
  * Fixed demand, fixed measured interchange and fixed monthly hydro budgets route the added coal
    into gas. So the worst case is −7.213 − 5.045 = **−12.26 TWh (FAIL)**, and the best case is
    −7.84 (PASS).
  * **A flip is predicted as likely.** Its root cause is the open demand-basis gap (FINDING-nwpp-45
    §8, −7.6 TWh in 2023). The model is already short on load, and accurate coal widens the gas
    deficit. Report it; do not absorb it.
* **C1 coal rows (repaired, hi):** COAL_PRB 2023 goes +0.49 → ≤ +5.0, and COAL_BIT +4.18 → ≤ +4.70.
  Both stay in band.
* **ST_GAS:** the keeper's JB / Valmy ST_GAS dispatch leaves the class: 0.026 TWh in 2023, and
  0.209 TWh in 2024 (Valmy's 0.027 TWh only, since JB stays gas).
* **The as_is variant cuts coal in 2024 for the wrong reason.** Its C1 COAL_PRB 2024 improvement
  (+3.27 toward 0) is Colstrip's missing utility sheet, not the fleet vintage.

## 4. Charter item 3: does JB's missing COAL tranche row change this? Yes, materially (report only)

`thermal_tranches_NWPP.csv` has no COAL row for 8066. It has an `ST_GAS` row built from all four
units' CEMS, attributed to the 1,070 MW bin. The artifact is derived once, from the canonical fleet,
so D2 does not create the row. Under D2 the whole 2,119 MW plant takes the 45 / 5 / 2 default:
1,060 MW of flat block at $4.50.

| JB 2023, price-taker vs EAST P1 price | default 45 / 5 | measured-like (P5 ≈ 7.3 / 7.3 %, CAMPD gross, approximate) |
|---|---|---|
| flag off (1,049 MW coal) | 4.434 TWh | 2.495 TWh |
| flag on (2,119 MW coal) | 8.957 TWh | 5.039 TWh |
| D2 increment | **+4.52** | **+2.54** |
| CAMPD gross (all 4 units) | 9.109 | 9.109 |

* The default flat block is what keeps JB near its metered energy.
* A measured row would halve D2's increment, and would leave JB about 4 TWh under CAMPD. Its econ
  bands ($42.62) clear in only 2,245 EAST hours.
* So repairing the row alone is predicted to worsen JB's volume unless its offers also change. That
  is the NWPP-48 §4 finding again, from the volume side.
* The row stays a separate card (`campd_per_unit_attribution` collateral, FINDING-nwpp-48 §5).

## 5. G-DRIFT (keeper `c2d5991c` → HEAD `06d7de40`), rule 29(b)

11 files changed on the audited paths. **All INERT for NWPP:**

* `coal_fuel_inventory_plant_grain` (miso-268): `scenarios.py`, `run_calibration.py`,
  `coal_fuel_inventory.py`, `lp/{__init__,model,rows}.py`, `pipeline/spec.py`. The flag is
  default-off, absent from the NWPP recipe, and raises unless `coal_fuel_inventory` is armed (it is
  not).
* `campd_dark_unit_year_windows` (SOCO-61): `outages.py`, `arrays.py`, `resolved_inputs.py`. The
  flag is default-off, absent from the recipe, and also needs `campd_per_unit_attribution` (off for
  NWPP).
* `scripts/lib/forecast_parity_registry.py`: forecast-only declaration, never on the backcast path.
* `data/raw/_validation-source`, `data/raw/reference`: no change.

**Form 4 is valid; the keeper is the control. No control solve.**

## 6. Pre-registered stop conditions (`_nwpp51_gates.py`, default `--variant repaired`)

* **INERT (STOP):** 2023 Δcoal < +0.629, or 2024 Δcoal < 0.000. Also STOP if any `ST_GAS` row of
  8066 dispatches in 2023, or of 8224 in 2023 or 2024.
* **OVERSHOOT (STOP):** Δcoal > the `hi` value (2023 +5.045, 2024 +0.667), or NWPP hydro annual
  energy moves > 1.0 TWh in any year.
* **IDENTITY (STOP, not a verdict):** any 2025 class moves > 0.001 TWh.
* **Reported, never gated:** C1 CC_REGULAR 2023 against −8.00, and coal r / r_intra against §3.

Sanity check: fed the keeper itself as the "arm", the evaluator exits INERT, as it must.

## 7. To the owner (no LP spent; none requested)

1. **Utility-sheet intake first?** Recommended: `eia860_utility` for vintage_2023 and vintage_2024
   from EIA's archive zips, plus a blast-radius census. Zero LP, one short session.
2. **Then solve the `repaired` variant?** Cost: rule 36, three single-year shards in parallel,
   ~60–100 min each (FINDING-nwpp-50 §3), ~1.5–2 h wall. 2025 is solved too; it is predicted
   byte-identical and serves as the identity check.
3. **Or solve `as_is` now?** Not recommended. It ships a known-inaccurate Colstrip input (rule 14),
   and its 2024 coal cut would read as an improvement it did not earn.

## 8. Reported, not absorbed

* **C1 demand-basis gap** −7.6 / −10.0 / −7.1 TWh (FINDING-nwpp-45 §8). This is what makes the C1
  flip likely.
* **JB 1–2 on gas, 2024–25:** CAMPD gross 3.38 / 2.94 TWh, while the model's JB ST_GAS dispatches
  0.18 / 0.10 TWh. A gas-offer or commitment question, separate from D2.
* **North Valmy 1 in 2025:** canonical 860 lists it as gas, but it burned mostly coal (0.52 TWh,
  co-fired). There is no vintage_2025 directory, so D2 cannot reach it.
* **Inherited:**
  * C5a CO2 reported-only FAIL.
  * The NWPP-40/41/42 attestation corrections.
  * D3 stacking audit (deferred).
  * Budget/envelope duals are written to no sidecar.
  * The fish-spill floor is routed only.
  * `check_registry_payload_parity.py` goes RED locally on gitignored leg dirs.

## 9. Retrievability

Nothing was solved. The committed artifacts are the two probes, their JSON records, the evaluator
and this doc.

## 10. ADDENDUM: owner ruling and the utility-sheet intake (written before any leg is launched)

**Owner ruling (2026-09-24):** "Add utility sheet then solve repaired."

**Intake, zero LP:**

* `data/raw/eia-860/vintage_{2023,2024}/eia860_utility.parquet` come from EIA's own archive zips:
  * `eia8602023.zip`, sha256 `1447e23e608bea1523961542a90eb93ea86715067a37f211282541461049b46f`;
  * `eia8602024.zip`, sha256 `0aaae04812cd4ab87a3e346bdf93848a3cc15053fd4dc2a4cf82d2aeac95f12b`.
* They were extracted with `process_eia860.extract_all_workbooks`. The same extraction reproduces
  the committed `owner`, `plant` and `generator_operable` sheets of both dirs **frame-identically**,
  so this is the same release. Rows: 6,193 (2023) and 6,643 (2024). Columns are identical to the
  canonical sheet.
* Nothing else was added, and canonical entity types were **not** substituted.

**Blast radius, measured:**

* The utility sheet has one reader (`eia860.py:4102`).
* A scan of 365 committed `run_config` / `meta` records finds exactly one run whose active directory
  is vintage_2023 or vintage_2024: the SPP keeper `hydro5_spp_floor_span`. It arms none of the three
  consumers (`coal_committed_takeorpay_regulated`, `coal_prb_committed_split`,
  `miso_coal_night_floor`).
* Confirmed directly: SPP fleet-only rebuilds with and without the file give identical digests
  (2023 `ee3a845e…`, 2024 `9ad746e3…`). **Inert for every committed keeper.**

**NWPP census re-run with the intake** (`results/calibration/_nwpp51_vintage_census_repaired.json`):

* Colstrip no longer moves.
* **Zero offer-price (mc) changes in any year.** The fuel switch and the §1 nameplate edits are the
  whole change.
* 2025 is byte-identical (`428020c25d1a…`).
* The arm is therefore exactly the pre-registered `repaired` variant. `_nwpp51_gates.py` runs at its
  default `--variant repaired`, unchanged.

**Legs:** rule 36, one single-year shard each for 2023, 2024 and 2025. Each runs
`replay_keeper.py results/calibration/nwpp49_ror_span --out-dir results/calibration/nwpp51_vint_<y>
--years <y> --set eia860_vintage_tracks_solve_year=true`, pinned to the full SHA of the commit that
carries this addendum and the intake.
