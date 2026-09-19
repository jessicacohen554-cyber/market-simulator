# PRECOMMIT — SOCO-53d: `soco_gas_st_campaign_commitment`, the multi-week-campaign commitment floor

**Lane** SOCO-53d · **Model** Opus 5 · **Date** 2026-09-19 ·
**Branch** `claude/soco-commitment-mechanism-rnlt19` · **Data profile** `soco` ·
**Incumbent keeper (the control of record)** `2026-09-19-soco53c-egrid-family-hr`,
bundle `results/calibration/soco53c_family`, basis `0f8ebad9`.
**Predecessors** `FINDING-soco-53-2026-09-17.md` (§2.3 / §2.4 the commitment measurements this
lane inherits), `PRECOMMIT-soco-53c-2026-09-19.md` (§2.2 the ex-ante-prediction pattern),
`docs/calibration-log/soco.md` (soco-53, soco-53 promotion, soco-53c).
**Rules that bind** 1 `[R-STRUCT]`, 12 `[R-PARALLEL]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
15 `[R-DASHBOARD]`, 16 `[R-ALLYEARS]`, 17 `[R-FLOOR-WINDOW]`, 18 `[R-PHYSICS]`, 19 `[R-ONE-MECH]`,
20 `[R-FORCED-BUDGET]`, 21 `[R-DOF]`, 23 `[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`,
25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]`, 29 `[R-SCREEN]`, 31 `[R-RETAIN]`,
32 `[R-SHARD]`, 33 `[R-SHARD-ARCHIVE]`, 34 `[R-SHARD-PROMOTABLE]`, 35 `[R-PROMOTE]`.

**Pushed before anything is solved.** Every number below is ZERO-LP: the keeper's committed
`dispatch/`, `hourly/` and `legitimacy_diagnostics.json`, the fleet loaders called directly through
`scripts/lib/bundle_fleet.reconstruct_bundle_fleet`, the EPA CAMPD unit-level record read directly,
and the ISO-neutral commitment detector itself run offline against the keeper's committed dispatch.
**The parent ran no LP of any length** (rule 32(a)). Nothing below is revised after the solve is read.

---

## 0. THE PRICE POSTURE IS UNCHANGED AND UNCHALLENGED

SOCO publishes no LMP and never will. `data/raw/_validation-source/actual_lmp.json` carries **no
SOCO block and must not gain one** — a placeholder breaks
`calibration_verdict._price_reference_absent` and silently moves SOCO onto the ordinary
determination path. C3a / C3b / C3c are **UNSCORABLE, not failed**. The ceiling is rubric v3.8
`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can **never** read `CALIBRATED`. Scored on
**C1 / C2 / C4 / C6 / C8 only**. Gate **G17** absolute: no neighbouring hub, no proxy, no cost-stack
price, ever.

**Every `offer_curve_by_group` band stays at the identity 1.0.** With no price benchmark there is no
price residual, so the rule-1 authorized channel is unreachable here, not merely unused. This lane
touches no band, share, floor level, threshold or offer. **The attestation's governance block will
carry NO `authorized_price_tuning` KEY at all** — `calibration_verdict.py:3299` validates any
present value as a structured rule-1 declaration and a prose string there FAILS C6 (the trap
SOCO-53c hit). The declared-NONE statement goes in `attested_by` prose.

---

## 1. PHASE 0 — THE DEFECT IS A COMMITMENT DEFECT, AND THE MEASUREMENT IS UNAMBIGUOUS

### 1.1 What the keeper gets wrong, per zone

Model vs actual annual TWh, from the keeper's own committed run payload (`volErr`, EIA-923 basis):

| class | zone | 2023 m/a | 2024 m/a | 2025 m/a |
|---|---|---|---|---|
| `CT_PEAKER` | SOCO_GA | **11.892 / 3.222** | **9.543 / 3.451** | **11.664 / 3.971** |
| `CT_PEAKER` | SOCO_AL | 2.675 / 0.900 | 1.913 / 0.772 | 2.646 / 0.558 |
| `ST_GAS` | SOCO_AL | 0.872 / 3.567 | 0.527 / 2.963 | 0.661 / 3.253 |
| `ST_GAS` | SOCO_GA | **0.052 / 2.239** | 0.811 / 2.095 | 0.786 / 1.300 |
| `ST_GAS` | SOCO_MS | 2.199 / 3.270 | 1.759 / 2.371 | 1.776 / 2.627 |

Class totals: `CT_PEAKER` **+10.30 / +7.11 / +9.67 TWh**, `ST_GAS` **−5.95 / −4.33 / −3.96 TWh**.
The scored C1 rows (BTM-adjusted `classFull` basis) read 2023 `CT_PEAKER` **+10.09 TWh / +4.2pp**
and 2023 `ST_GAS` **−7.36 TWh / −3.1pp** — the two failing rows of fourteen.

### 1.2 The real fleet runs CAMPAIGNS; the model runs the same plants like peakers

Measured on SOCO's own CAMPD record (2023–2025), at **plant grain**, with CAMPD **boiler**
`unitType`s paired to the plant's own model boiler rows by capacity rank and restricted to the units
paired to a `gas_st` row. A plant is SYNCHRONIZED in any hour at least one of its kept units is
online by that unit's own threshold — the union of the per-unit masks, not a threshold on the plant
sum, which fragments a multi-unit plant whose units cycle independently (on Gaston 2023 a sum
threshold reports 56 blocks of median 5 h where the union reports 10 of median 305 h).

| plant | model `gas_st` MW | **measured** campaigns/yr | **measured** campaign p25 / p50 (h) | **measured** synchronized share | **MODEL** runs/yr (2023 P1) | **MODEL** run p50 (h) |
|---|---|---|---|---|---|---|
| 26 E C Gaston | 1,020.0 | 9.7 | **64 / 286** | **0.639** | 61 | 9 |
| 2049 Jack Watson | 721.0 | 5.0 | **76 / 546** | **0.920** | 349 | 11 |
| 728 Yates | 714.0 | 5.3 | **192 / 394** | **0.843** | 20 | 5 |
| 10 Greene County | 516.1 | 7.7 | **132 / 384** | **0.752** | 121 | 10 |
| 3 Barry | 160.0 | 5.3 | 38 / 77 | **0.063** | 10 | 2 |

**That is the finding in one line: SOCO's gas boilers start 5–10 times a year and stay synchronized
64–92 % of all hours; the model starts the same plants 10–349 times a year in blocks of 2–11 h
median.** The model gives every one of them `min_run_hours = min_down_hours = 0` and no committed
state at all. It is operating SOCO's steam boilers as if they were peaking turbines, and the energy
a synchronized boiler's minimum-load block would carry is bought from combustion turbines instead.

The arithmetic closes against the benchmark: plant CF × plant HSL × 8760 summed over the five plants
is **8.96 TWh** against the 2023 metered `ST_GAS` **9.076 TWh**, so the measured campaign picture
*is* the actual the model is scored against.

### 1.3 The `CT_PEAKER` side of the same measurement, which is why no CT leg is armed

SOCO's combustion turbines measure ~57–60 starts/unit/yr with a run p50 of 8–9 h (FINDING-soco-53
§2.3). The model's CT plants run 100–349 blocks a year with a p50 of **3–16 h**. **The model already
reproduces SOCO's CT run SHAPE**; what it gets wrong is the number of starts and the resulting
capacity factor (54538 at CF 0.672, 55141 at 0.570, 55244 at 0.397 — against a measured class CF of
~6 %). A minimum-run floor on CT would make CT run **more**, which is the wrong direction. The CT
leg NYISO arms (`nyiso_gas_bridge_ct`) is therefore **refused for SOCO ex ante**, on SOCO's own
evidence rather than by omission.

---

## 2. RULE 19 `[R-ONE-MECH]` — WHAT ALREADY FLOORS THESE CLASSES: NOTHING, MEASURED

From the keeper's committed `legitimacy_diagnostics.json` D-2, all three years:

| class | forced TWh | class total TWh | forced share | cap |
|---|---|---|---|---|
| `CC_REGULAR` | **0.0** | 114.209 / 113.547 / 113.334 | **0.000** | 0.30 |
| `COAL` | **0.0** | 27.137 / 28.061 / 38.783 | **0.000** | 0.30 |
| `CT_PEAKER` | **0.0** | 15.091 / 11.823 / 14.790 | **0.000** | 0.15 |
| `ST_GAS` | **0.0** | 3.691 / 3.764 / 4.271 | **0.000** | 0.30 |

The only mechanisms that force anything in SOCO are `nuclear_mustrun` and `chp_steam`, both D-2
exempt and both on other classes. **This mechanism stacks on nothing and replaces nothing.**

Four alternatives were enumerated and are refused, each with its reason:

- **`gas_commitment_bridge` (cell `R`, SOCO-53).** Its object is the RESTART decision across an idle
  gap shorter than min-down, and it is inert for SOCO by measurement: of 386 boiler downtime gaps
  68.7 % exceed 72 h and account for 169,303 of 171,734 gap-hours (98.6 %); only 150 unit-hours
  across three years fall inside the 8 h `ST_GAS` min-down. **This lane does not re-test that cell**
  — `startup_bridge` stays **off**, so no gap is ever bridged on economics, and the detector's
  unconditional sub-min-down physical bridge is the same 150 unit-hours, reported as an inert
  incidental rather than claimed as an effect.
- **`tranche_startup_amortization` (cell `G`, no reopen condition).** It is the FERC Order-825
  fast-start **pricing** object — a bid markup only — and SOCO has no clearing price. Untouched.
- **`st_gas_mustrun_per_plant` (`MECH_ST_GAS_MUSTRUN_PER_PLANT`, id 16, default off).** A real
  alternative and the closest existing `ST_GAS` mechanism, refused on two grounds. Its driver is
  MISO SOM **out-of-market VLR** commitment — a market-design object a vertically-integrated BA has
  no analogue of, since all of SOCO's commitment is "out of market" by construction and the
  distinction is empty. And it places capacity by an **exogenous clock** (the plant's measured
  top-`online_frac` system-load hours), which is the G-20 placement rule 17 exists to catch;
  SOCO's boilers are not peak-correlated, they run multi-week campaigns.
- **`class_commitment_overrides`.** A P2-pass channel; P2 is archived and no keeper uses it.

---

## 3. THE MECHANISM, AND EVERY PARAMETER IT CARRIES

`ScenarioConfig.soco_gas_st_campaign_commitment` (bool, default **False**, SOCO-gated) →
`pipeline.commitment.build_soco_gas_st_campaign_p1_prep` → the **shared ISO-neutral detector**
`model.commitment.caiso_ra_mustoffer_min_gen`, injected at the P0→P1 seam, run **once on `gas_st`
alone** with exactly **two of its legs armed**:

1. **the measured minimum-RUN extension** (`min_run_hours`) — a P0-detected run shorter than the
   plant's own measured minimum campaign is extended to it, and the extension floored at minimum
   stable load; and
2. **the online-hours LSL state floor** (`floor_online_hours`) — the committed STATE the extension
   interpolates between: a synchronized boiler cannot operate below its minimum stable load, so its
   LSL block is must-take in every hour the model's own P0 pattern has it online.

**Off, deliberately and with reasons stated ex ante:** `startup_bridge` (§2 — SOCO's boilers do not
two-shift) and `startup_aware`. The commitment-real run screen asks whether an individual unit's
margin **against an LMP** repays its published startup cost. That is a **merchant** test. SOCO is a
vertically-integrated cost-based balancing authority with no LMP, no offers and no market at all
(owner card S5; gate G17), so its boilers are committed against total system production cost, not
against a unit's own margin. Importing the screen would assert a market design SOCO does not have —
the identical ground on which `tranche_startup_amortization` is refused for this ISO. **It is
refused before the solve and never swept.**

### 3.1 The parameters, all MEASURED, all per-plant, zero free

`scripts/data/derive_campd_gas_st_campaign_params.py --iso SOCO` →
`data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv`, read through
`market_sim.data.gas_st_campaign`, which applies **only `flag == "ok"`** rows.

| plant | `min_load_frac` (PLANT basis) | `min_run_hours` | `sync_share` | `flag` |
|---|---|---|---|---|
| 26 E C Gaston | **0.0657** | **64** | 0.6392 | `ok` |
| 2049 Jack Watson | **0.1000** | **76** | 0.9202 | `ok` |
| 728 Yates | **0.0829** | **192** | 0.8429 | `ok` |
| 10 Greene County | **0.1365** | **132** | 0.7516 | `ok` |
| 3 Barry | 0.1628 | 38 | **0.0632** | **`not_campaign_duty`** |

- **Level** is the PLANT-basis minimum stable load — p5 of the plant's summed output over its
  synchronized hours, over its p99.5. The PLANT basis is required because the detector floors
  `min_load_frac × plant_pmax` (the caiso-135 adjudication); on SOCO it lands at 0.066–0.137, close
  to one unit at its own turndown, which is what a minimum stable *configuration* is.
- **Horizon** is the **p25** of the plant's own campaign-length distribution — the LOW order
  statistic, because an observed run bounds a minimum-run CONSTRAINT from above. This is the
  nyiso-90 / SPP-44 convention verbatim; the median would assert a constraint a quarter of the
  plant's own observed campaigns violate.
- **Membership** is the plant's own measured synchronized share against the derive's ex-ante
  `CAMPAIGN_DUTY_MIN_SYNC_SHARE = 0.50`. **Barry is refused by it**, and that refusal is rule 17
  `[R-FLOOR-WINDOW]` operating rather than a tuning choice: Barry's two 80 MW boilers are
  synchronized **6.3 %** of the year — standby iron — and flooring them would bind in hours their
  own driver evidence says they are offline. **The gate selects nothing.** The population separates
  by an order of magnitude (0.063 against 0.639 / 0.752 / 0.843 / 0.920, in every year), so **every
  value in (0.07, 0.63) yields the identical partition**. It is declared here and never swept.

**Rule 21 `[R-DOF]`: ZERO free parameters.** Every number above is a measured conduct statistic of
SOCO's own plants. **Rule 25 `[R-ISO-SCOPE]`:** nothing is inherited — not NYISO's 0.239, not SPP's
0.090, not their 5 h and 15 h horizons. **Rule 23 `[R-FROZEN-DERIVE]`:** the artifact re-derives only
on a CAMPD vintage change; a test pins all eight values against this document.

### 3.2 One construction disagreement, reported rather than adopted

The pairing is unambiguous at every plant (within 5–10 % on all fifteen units), and it resolves the
one place CAMPD's own `primaryFuelInfo` disagrees with the model: **CAMPD files Barry unit 4 (HSL
367 MW) as Pipeline Natural Gas, and the model carries a 362 MW `coal` row there.** The model's
class assignment governs here because the floor is applied to model rows — but the disagreement is a
real question about 362 MW of SOCO coal and is **routed, not adopted** (§8).

---

## 4. RULE 17 `[R-FLOOR-WINDOW]` AND RULE 20 `[R-FORCED-BUDGET]`, WORKED BEFORE THE SOLVE

### 4.1 The window declaration

`D4_WINDOWS[(MECH_SOCO_GAS_ST_CAMPAIGN, "ST_GAS")] = (0, 24)` — all 24 hours **by driver**, and the
row is added in this PR because rule 20's escalation path requires it to exist. **WINDOW:**
self-windowing by construction — the floor exists only in the hours of a P0-detected run or in the
hours after a P0 run-start that lie inside the plant's own measured minimum campaign. There is no
clock hour anywhere in the mechanism, and it **cannot start a plant**: it can only refuse to let one
sink below its minimum stable load inside a campaign the model itself began. **DRIVER:**
campaign-commitment physics, with the plant's own meter as its evidence (§1.2). **FORWARD STORY:**
regenerates from any year's own P0 pattern plus an artifact that re-derives only on a CAMPD vintage
change; the meter sets the LEVEL and the POPULATION, never the placement.

### 4.2 The floor, computed offline against the keeper's own committed dispatch

The detector was run **zero-LP** on the keeper's committed `dispatch/<year>_P1.parquet`, fleet
rebuilt through `reconstruct_bundle_fleet`:

| year | floor volume | incremental (floor − dispatch, plant level) | projected `ST_GAS` total | **projected forced share** |
|---|---|---|---|---|
| 2023 | 0.8671 TWh | **+0.534 TWh** | 3.658 TWh | **0.237** |
| 2024 | 0.8179 TWh | **+0.506 TWh** | 3.603 TWh | **0.227** |
| 2025 | 0.9084 TWh | **+0.584 TWh** | 3.807 TWh | **0.239** |

Per-plant binding share against that plant's **own measured synchronized share** — the rule-17 test,
and it holds in **all twelve plant-years**:

| plant | 2023 bind / meas | 2024 bind / meas | 2025 bind / meas |
|---|---|---|---|
| 10 Greene County | 0.467 / 0.752 | 0.361 / 0.752 | 0.578 / 0.752 |
| 26 E C Gaston | 0.199 / 0.639 | 0.116 / 0.639 | 0.158 / 0.639 |
| 728 Yates | 0.200 / 0.843 | 0.643 / 0.843 | 0.761 / 0.843 |
| 2049 Jack Watson | 0.882 / 0.920 | 0.677 / 0.920 | 0.772 / 0.920 |

**Including Barry would have broken this**: with Barry in the population its 2025 binding share is
**0.228 against a measured 0.060** — the one rule-17 violation in the whole design, found before the
solve and removed by the membership gate rather than reported after it.

### 4.3 The C8 prediction, with its uncertainty stated

`ST_GAS` is a **material** class for SOCO (load share 0.043 / 0.036 / 0.033, above the 2 % floor), so
the 30 % merchant cap binds. Predicted forced share **0.227–0.239 — under the cap, C8 PASSES.** Two
honest caveats: (a) the projection is an upper bound that assumes no re-dispatch of `ST_GAS` above
the floor; and (b) **the offline computation uses P1 as a proxy for the P0 pattern the seam actually
reads**, because the keeper commits no P0 dispatch. The proxy is good but not exact: `gas_st` bids
identically in both passes (`gas_st_startup_cost` is False, so `compute_monthly_markup` skips every
`gas_st` row), and only the `_committed` tranches of `gas_ct` reprice between P0 and P1 (~10 % of CT
capacity, ~+$20/MWh). Direction: P0's cheaper CT committed band means marginally fewer/shorter
`ST_GAS` runs in P0, so the delivered floor is **more likely below than above** these figures.
**If C8 nonetheless escalates, the path is prepared**: the D-4 row exists (§4.1) and the D-1 leg is
predicted in §5.

---

## 5. EX-ANTE PREDICTION, registered BEFORE the solve, with falsifiers

**This arm does NOT fix SOCO's headline defect, and that is registered here rather than discovered
afterwards.** The displacement was measured: in the 3,988 hours of 2023 that carry incremental floor
energy, the marginal class is `CC_REGULAR` in 1,170 h (0.108 TWh), `CT_PEAKER` in 681 h (0.061 TWh),
`COAL` in 431 h (0.046 TWh) and `hydro` in 589 h (0.042 TWh). **Most of what the floor displaces is
combined cycle, not peakers.**

| # | prediction | falsifier |
|---|---|---|
| **P1** | `ST_GAS` **rises +0.4 to +0.7 TWh** in every year (2023 3.124 → ~3.66). The 2023 row stays **FAILED** at roughly −6.8 TWh. | `ST_GAS` does not rise in some year, or rises by more than 1.5 TWh in any year. |
| **P2** | `CT_PEAKER` **falls, by 0.05 to 0.35 TWh** — less than the `ST_GAS` gain, because the marginal class is mostly CC. The 2023 row stays **FAILED** above +9.5 TWh. | `CT_PEAKER` rises in any year, or falls by more than 1.0 TWh in any year. |
| **P3** | `CC_REGULAR` **falls 0.05 to 0.35 TWh**. It stays in band in 2023/2024 (currently +0.77 / −0.02 against ±7.5 TWh); 2025 moves further negative from −1.69. | `CC_REGULAR` moves by more than 1.0 TWh in any year, or a `CC_REGULAR` C1 row changes status. |
| **P4** | **C1's failing-row SET is unchanged**: the same two rows fail, no row changes status in either direction, C1 all 12/14 and free 8/10 on both sides. | Any C1 row changes status in either direction. |
| **P5** | **C8 PASSES** on the budget with `ST_GAS` forced share in **0.15–0.30**. | Forced share above 0.30 (→ the §4 escalation) or below 0.10 (→ the mechanism is far more inert than §4.2 measured). |
| **P6** | **D-1 `ST_GAS` `model_offpeak_cv` FALLS** toward the measured actual (0.281 / 0.263 / 0.207) from 0.709 / 0.864 / 0.608, and `cv_ratio` falls from 2.528 / 3.281 / 2.941 but **stays above 1.0** in every year. This is the shape signature of replacing turbine conduct with campaign conduct. | Any `ST_GAS` `cv_ratio` rises, or falls below 1.0, in any year. |
| **P7** | **`CC_CHP` / `CT_CHP` / `ST_CHP`, nuclear, hydro, wind and solar are BYTE-IDENTICAL**, and COAL moves by less than 0.5 TWh in each year. | Any `*_CHP` class moves by more than 0.001 TWh, or any COAL class by more than 0.5 TWh. |
| **P8** | **Barry (3) carries ZERO floored unit-hours** in all three years, and the per-plant binding share is at or below that plant's own measured synchronized share in all twelve plant-years. | Any Barry floor at all, or any plant-year whose binding share exceeds its measured synchronized share. |

P7's falsifier names the OBJECT rather than a proxy: the CHP classes are floored by `chp_steam`,
which this mechanism never touches, so any movement there is a seam defect and not a re-dispatch.
The 0.001 TWh wording is deliberate — SOCO-53c's F3 said "if any CHP class moves at all" and was
falsified on a ≤0.003 TWh re-dispatch that was not the defect it targeted.

**The determination is predicted UNCHANGED at `NOT-YET`** (rubric v3.8, PRICE UNSCORED), with C2 /
C4 / C6 / C8 passing and C3a/b/c unscorable. **It is armed anyway**, and that is rules 1
`[R-STRUCT]` and 14 `[R-ACCURATE]` operating as written on a model that cycles a 2,971 MW steam
fleet 10–349 times a year against a metered 5–10. Whatever the gates read afterwards is reported at
full magnitude and nothing is reverted.

---

## 6. G-DRIFT (rule 29(b)) — ONE HUNK, INERT, NO CONTROL SOLVE SPENT

```
git diff 0f8ebad9 HEAD -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference
```

returns exactly **one changed file, `src/market_sim/config/paths.py`, +8 lines**: an additive
`EXPORTS_DIR` constant for a handoff-export tree. **INERT**, verified mechanically rather than
asserted: the only reader anywhere in the repo is `scripts/data/derive_ercot_hub_rt_lmp_csv.py`
(`grep -rn EXPORTS_DIR --include=*.py src/ scripts/`), nothing under `src/market_sim/` reads it, and
`paths` is not one of the seven `config/solve_surface.SURFACE_MODULES`, so no cache key moves.
**All hunks INERT ⇒ form 4 is valid and the keeper's committed bundle is the control. No control
solve is spent.**

Two precedents the handoff supplies were re-verified rather than assumed: `_POOL_HOURLY_MEMBERS`
carries the single key `NWPP`, so the eia930 pool path is inert for SOCO by construction; and commit
`fba0ecd7`'s unconditional emissions-dual re-pricing was measured byte-identical on SOCO by
SOCO-53c's own control solve (0.000000 TWh, 15 classes × 3 years), so it needs no second one.

---

## 7. THE ARM

```
uv run python scripts/run_calibration_full.py --iso SOCO --year 2023 2024 2025 \
    --measured-ct-heat-rates --egrid-family-heat-rates \
    --soco-gas-st-campaign-commitment \
    --out-dir results/calibration/soco53d_campaign \
    --note "soco-53d: P1-native gas-steam CAMPAIGN commitment floor on SOCO's four campaign-duty boilers at their own measured plant-basis minimum stable load and minimum campaign duration (rules 1/14/17/19); measured_ct_heat_rates + egrid_family_heat_rates retained from the keeper; every offer band 1.0, authorized_price_tuning NONE"
```

No other flag. Years sequential inside ONE invocation (rules 12 / 16 / 32(b) / 34(c)). SOCO's
registered year union, enumerated from `frontend/data/backcast/registry/*.json` **before anything is
pruned** (rule 35(b)): **{2023, 2024, 2025}** — one registered run, the keeper, and the arm covers
the same three years in its own bundle, so no `holdout.keeper` stamp is owed.

**Config signature the shard must see, as its hard stop:** `measured_ct_heat_rates: true`,
`egrid_family_heat_rates: true`, `soco_gas_st_campaign_commitment: true`, every
`offer_curve_by_group` band exactly `1.0`, `authorized_price_tuning` absent.

**Rule 34(a): the shard PUSHES its bundle**, including `dispatch/<year>_P1.parquet`, plus
`results/calibration/_shared/SOCO/` (outside the out-dir; `render_calibration_html.build_payload`
dies without `eia923`).

---

## 8. ROUTED, NOT ABSORBED

1. **`measured_st_heat_rates` — the premise this lane was handed is FALSIFIED, and this is probably
   the larger lever.** The handoff states the cost side is exhausted. On `ST_GAS` it is not, and its
   own predecessor made it so: `measured_ct_heat_rates` moved `CT_PEAKER` from 12.69 to **11.2666**,
   while `ST_GAS` still rides eGRID at **10.9613**. Measured on SOCO's own CAMPD boiler record
   (net basis, the same 0.99 parasitic factor the CT derive uses), the `gas_st` fleet is
   **10.4223** cap-weighted — the model is **+0.539 MMBtu/MWh, +5.2 %, too dear**, on 3,131 MW:
   Greene 9.795 vs 10.256 (−0.461), Watson 9.938 vs 10.413 (−0.475), **Gaston 10.642 vs 11.551
   (−0.909)**, Yates 10.359 vs 10.814 (−0.455); only Barry's 160 MW is understated (13.512 vs
   12.610). SOCO-53 §2.2's "the model over-separates the classes by 2.8×" was measured on the
   PRE-ARM fleet; at HEAD the model separation is **+0.305** against a measured **+0.713**, so the
   model now **under-separates by 2.3×** — `ST_GAS` is too dear relative to `CT_PEAKER`, which is
   the sign of the defect. At $3.2–3.6/MMBtu delivered that is $1.5–3.3/MWh, enough to move Gaston
   (43.23 → ~40.1) and Yates (43.24 → ~41.6) below a large part of the CT stack. It is the exact
   sibling of SOCO's promoted keeper mechanism, a pure rule-14 repair with zero free parameters, and
   it is **not armed here** because rule 19 forbids stacking a second mechanism on the same
   phenomenon in one run. **SOCO-53e, and it should go first in the queue.** Note the interaction:
   this lane's measured floor volumes are conditional on a cost input known to be wrong in a stated
   direction, so §4.2 is owed a re-measurement after SOCO-53e lands.
2. **Barry unit 4 — 362 MW the model prices as coal and CAMPD files as gas** (§3.2). A fuel-class
   question, not a heat-rate one.
3. **E C Gaston (26) — the fuel-subfamily lever**, unchanged from SOCO-53c's routing.
4. **SOCO-53b — the 2025 EIA-923 hydro input hole**, unchanged.
5. **NWPP-41's ERCOT-pooled PRB proxy reaches SOCO** (6002 Miller, 6073 Daniel, 6257 Scherer priced
   off seven Texas plants); `coal_prb_proxy_own_iso` is a cheap rule-14/25 data lever.
6. **`tests/unit/config/test_data_profiles_tokens.py::test_soco_token_collides_with_no_other_raw_name`
   is RED at HEAD and this lane adds one more offender to it**, in the established convention: the
   artifact is named `campd_gas_st_campaign_params_SOCO.csv`, exactly as SOCO-53's committed
   `campd_ct_heat_rates_SOCO.csv` is. Verified: the test fails identically with and without this
   lane's file (it asserts on the first offender alphabetically, `campd-partial-outages-SOCO.csv`).
   **The shared contract test is deliberately NOT patched** — it is the SOCO desk's, and the fix is a
   naming convention decision across every SOCO artifact, not a lane's.

---

## 9. REPO SURFACE, and the guards run before the push

**New:** `scripts/data/derive_campd_gas_st_campaign_params.py`,
`data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv`,
`src/market_sim/data/gas_st_campaign.py`, `tests/unit/data/test_gas_st_campaign_params.py`.
**Changed, all additive (no file shrank — rule 27):** `scenarios.py` (the field + its three
registration sites), `floor_mechanisms.py` (`MECH_SOCO_GAS_ST_CAMPAIGN = 25`, its name and its
ablation entry), `pipeline/commitment.py` (the detector call and its D-4 trace), `pipeline/year.py`
+ `runner.py` + `run_calibration.py` (all **three** orchestrators), `pipeline/__init__.py`,
`legitimacy_diagnostics.py` (the D4_WINDOWS declaration), both runners' CLI,
`test_p1_prep_wiring.py` (the roster row), the matrix base row and **all nine ISO shards**.

Green before the push: `check_cache_key_registration.py` (853 fields, 308 registered, all declared
defaults match HEAD), `check_mechanism_matrix.py` (integrity OK, base + 9 shards),
`floor_mechanisms.assert_ablation_coverage()`, `tests/unit/data/test_gas_st_campaign_params.py`
(6 passed), `tests/unit/pipeline` + `tests/unit/model/test_commitment.py` (366 passed),
`tests/unit/config` (205 passed, the one pre-existing RED at §8.6), `ruff check` + `ruff format`
(the two remaining `ruff` errors are pre-existing in another lane's
`scripts/gen_nyiso229_attestation.py`, verified at HEAD).

**`test_p1_prep_wiring.py` earned its keep**: it caught the prep wired into `pipeline/year.py` only
and missing from `runner.py` and `scripts/run_calibration.py` — the exact miso-113 failure mode, and
it was caught before a single LP was spent rather than after an arm solved byte-identical to its
control.
