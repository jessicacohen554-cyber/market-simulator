# PRECOMMIT — SOCO-53f: `measured_coal_heat_rates` for SOCO, and the routing premise that measurement reverses

**Lane** SOCO-53f · **Model** Opus 5 · **Date** 2026-09-20 ·
**Branch** `claude/soco-measured-coal-heat-rates-ppfvts` · **Data profile** `soco` ·
**Incumbent keeper** `2026-09-19-soco53e-measured-st-gas`, bundle
`results/calibration/soco53e_st_hr`, basis `cc1bcb24e11a719c4d02ac3ea75834d988f0ceab`,
full 34-file bundle recovered in this session at
`884dca3132e8d1d1e1f18fbb789c356506a4e343` (VERIFIED: the SHA still resolves;
`results/calibration/_shared/SOCO` at `730ae912e0e608695e3425e00daa00ad18138706`).
**Predecessors** `FINDING-soco-53e-2026-09-19.md` (§7.1 commissions this lane, §2.1 the
parasitic trap, §3 the rule-19 proof, §4.4 the floor tool, §10.2/§10.3 the two defects this
lane must not repeat), `PRECOMMIT-soco-53e-2026-09-19.md`, `docs/calibration-log/soco.md`.
**Rules that bind** 1 `[R-STRUCT]`, 12 `[R-PARALLEL]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`,
15 `[R-DASHBOARD]`, 16 `[R-ALLYEARS]`, 17 `[R-FLOOR-WINDOW]`, 19 `[R-ONE-MECH]`, 21 `[R-DOF]`,
23 `[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`, 25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`,
29 `[R-SCREEN]`, 31 `[R-RETAIN]`, 32 `[R-SHARD]`, 33 `[R-SHARD-ARCHIVE]`,
34 `[R-SHARD-PROMOTABLE]`, 35 `[R-PROMOTE]`, **36 `[R-YEAR-ISOLATION]`**.

**Pushed before anything is solved.** Every number below is ZERO-LP: the committed CAMPD
unit-level record read directly, the fleet loaders called directly, EIA-923 monthly generation,
and the keeper's own committed `mc_base` arrays, `hourly/unit_hourly_<year>.parquet` and
`floors/<year>_P1.npz` replayed through `fleet_only` rebuilds. **The parent ran no LP of any
length** (rule 32(a)). Nothing below is revised after a solve is read.

---

## 0. THE PRICE POSTURE IS UNCHANGED AND UNCHALLENGED

SOCO publishes no LMP and never will. `data/raw/_validation-source/actual_lmp.json` carries **no
SOCO block and must not gain one** — a placeholder breaks
`calibration_verdict._price_reference_absent`. C3a / C3b / C3c are **UNSCORABLE, not failed**.
The ceiling is rubric v3.8 `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can **never** read
`CALIBRATED`. Scored on **C1 / C2 / C4 / C6 / C8 only**. Gate **G17** absolute: no neighbouring
hub, no proxy, no cost-stack price, ever.

**Every `offer_curve_by_group` band stays at the identity 1.0.** With no price benchmark there is
no price residual, so the rule-1 authorized channel is unreachable here, not merely unused. This
lane touches no band, share, floor level, threshold or offer. **The attestation's governance
block will carry NO `authorized_price_tuning` KEY at all** — `calibration_verdict.py` validates
any present value as a structured rule-1 declaration and a prose string there FAILS C6. The
declared-NONE statement goes in `attested_by` prose.

---

## 1. PHASE 0 — THE MEASUREMENT REVERSES THE SIGN OF THE PREMISE THAT COMMISSIONED THIS LANE

### 1.1 The routing said "too cheap". The meter says "too dear", at every one of six plants.

`FINDING-soco-53e` §7.1 routed this lane with: *"Repricing only the gas side leaves the coal
boiler on a rate the same arithmetic says is roughly 0.5 MMBtu/MWh too **cheap** for a coal
machine."* The arithmetic behind it is a weighted-average argument: if E C Gaston's blended ST
family rate 11.5505 mixes an 832 MW coal boiler with 1,020 MW of gas boilers whose own meter
reads 11.0744, the coal side must sit *above* the blend.

**It does not, and the reason is the whole thesis of the mechanism this lane arms.** The blend is
not a weighted mean of two *operating* rates: it is an eGRID **annual average**, `PLHTIAN /
PLNGENAN`, which folds startup fuel, shutdown tails and the offline hours' bank fuel into the
number that sets the offer. That inflates it above BOTH machines' operating rates. Gaston's coal
boiler meters at **11.0505 net** against the blend's 11.5505 — **0.5000 MMBtu/MWh too DEAR, not
too cheap**, and the magnitude the routing named is right to four decimals with the sign
inverted.

`scripts/data/derive_campd_coal_heat_rates.py --iso SOCO --detail --egrid-family-heat-rates
--measured-ct-heat-rates --measured-st-heat-rates` →
`data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv`, **6 of 6 plants / 11,512.0 of
11,512.0 MW = 100 % of SOCO `COAL` capacity**, 252,093 in-band steady hours at 15 units,
AL/GA/MS 2023–2025:

| plant | COAL MW | units | steady h | `heat_rate_gross` | **`heat_rate` (net, applied)** | model (keeper recipe) | Δ | flag |
|---|---|---|---|---|---|---|---|---|
| 703 Bowen | 3,200.0 | 4 | 62,558 | 9.5268 | **10.2439** | 10.6479 | **−0.4040** | `ok` |
| 6002 James H Miller Jr | 2,777.5 | 4 | 97,641 | 10.0386 | **10.7942** | 10.8964 | **−0.1022** | `ok` |
| 6257 Scherer | 2,580.0 | 3 | 55,165 | 10.6173 | **11.4165** | 12.2855 | **−0.8690** | `ok` |
| 3 Barry | 1,118.5 | 1 | 7,789 | 9.9872 | **10.7389** | 12.6100 | **−1.8711** | `ok` |
| 6073 Victor J Daniel Jr | 1,004.0 | 2 | 18,777 | 11.0912 | **11.9260** | 12.8947 | **−0.9687** | `ok` |
| 26 E C Gaston | 832.0 | 1 | 10,163 | 10.2770 | **11.0505** | 11.5505 | **−0.5000** | `ok` |

**Capacity-weighted 11.5267 → 10.8926, −5.5 %** (generation-weighted 11.2434 → 10.8146, −3.8 %).
**Every plant moves the same way: cheaper.** There is no offsetting Barry here — unlike the gas
sibling, whose five plants split four-to-one.

**So this arm is not the asymmetry-closer it was routed as.** SOCO-53e made Gaston's gas boilers
cheaper; this makes Gaston's coal boiler cheaper too, by a comparable amount. What it closes is a
different and larger thing: **the eGRID annual-average defect across SOCO's whole 11.5 GW coal
fleet**, which is five times the capacity the gas-steam lane touched and moves the class's
cost level five times as far.

**A provenance repair landed with the artifact, and it is worth naming because it changed the
number.** nwpp-42's deriver reads its `model_heat_rate_egrid` comparison column off the
**loader-default** fleet. SOCO's keeper carries three heat-rate flags, so that column read a
fleet nobody solves: it reported Barry at 8.9950 and Daniel at 8.3995 — the physically
impossible plant blends `egrid_family_heat_rates` exists to remove — and therefore claimed the
measured rates were **dearer** than the model's. The gas-steam sibling already takes provenance
flags for exactly this reason (soco-53e §1.3); this lane adds the same three to the coal deriver
(`provenance_fleet`, plus a `model_recipe` column recording which recipe the column was read
under, and a guard that the provenance recipe cannot move plant membership). **PROVENANCE ONLY:
no applied number changes, `plant_table` is untouched, and the 14 committed tests pass
unchanged.** `scripts/data/` is not on the solve path, so the control and the arm remain
solve-identical at one SHA.

### 1.2 Barry unit 4 — the decision, stated rather than left implicit

CAMPD files **Barry unit 4, a 330 MW boiler, as *Pipeline Natural Gas***, while the model carries
it as a **362 MW `COAL` row** (`3_4`). nwpp-42's deriver separates a mixed site by
`primaryFuelInfo`, so **unit 4 is EXCLUDED from the measurement** and Barry's applied rate comes
from **unit 5 alone** (7,789 steady hours, 3,783.3 GWh gross). The artifact is at plant grain, so
that rate is then applied to **both** of Barry's model COAL rows, unit 4's included.

**Measured, so the cost is known rather than guessed.** Unit 4's own operating rate over 10,422
in-band steady hours is **11.0878 gross → 11.9224 net** at the committed coal factor. So on that
one row:

| | control | arm | its own meter |
|---|---|---|---|
| `3_5` (756.5 MW, unit 5, coal) | 12.6100 | **10.7389** | 10.7389 |
| `3_4` (362.0 MW, unit 4, gas-fired) | 12.6100 | **10.7389** | 11.9224 |

The arm takes `3_5` from 1.87 wrong to **exactly right**, and `3_4` from 0.69 too dear to 1.18
too cheap. Capacity-weighted over Barry's 1,118.5 MW that is a **+1.11 MMBtu/MWh net
improvement**, so the swap is right on the plant — and it is right for a second reason: unit 4
burns GAS, and the model already charges it a COAL fuel price, which is a larger defect than its
heat rate and is not this lane's to fix. **Both legs are reported at full magnitude and the row's
reclassification is ROUTED, unchanged, as it was by SOCO-53d and SOCO-53e.**

### 1.3 The parasitic class — measured against SOCO's own meter, and the committed default kept

`hr_net = hr_gross / factor`, so the class of the factor is the whole of the level. The committed
`COAL` class default is **0.93**. SOCO's own meter, EIA-923 `ST`/coal-fuel net generation over
CAMPD coal-unit gross, per plant-year:

| plant | 2023 | 2024 | 2025 |
|---|---|---|---|
| 703 Bowen | 0.9140 | 0.9126 | 0.9167 |
| 6002 James H Miller Jr | 0.9239 | 0.9254 | 0.9275 |
| 6257 Scherer | 0.8754 | 0.8660 | 0.8801 |
| 6073 Victor J Daniel Jr | 0.8727 | 0.8818 | 0.8849 |
| 26 E C Gaston *(mixed site)* | 0.8551 | 0.8892 | 0.7339 |
| 3 Barry *(mixed site)* | 0.7739 | 0.8320 | 0.6522 |

The **four single-fuel coal sites** cluster at **0.866–0.928**; the two mixed sites read lower
because EIA-923 splits a co-firing boiler's net between its fuels while CAMPD's gross is the
whole machine, so their coal-fuel rows understate the unit's net. **No cell is above 1.0, so
unlike the gas sibling there is nothing to discard — and unlike the gas sibling, the committed
default does NOT reproduce the measurement: 0.93 sits above every plant but Miller.**

**The committed default is used anyway, and that is a deliberate rule-13/21 choice, not an
oversight.** The factor that converts this rate must be the SAME factor the benchmark's net
"actual" is built with (`run_calibration_full._parasitic_factor_map` → the identical
`parasitic_load_factors.parquet`, class default otherwise), or the derived rate and the
generation it is scored against sit on two different boundaries. Substituting a
this-lane-measured number would be a new free parameter (rule 21) on an artifact shared by 544
plants across seven ISOs.

**The consequence is stated rather than buried: the applied rates are biased LOW.** Against each
plant's own measured factor the arm's net rates would be **+1.5 % (Bowen, Miller) to +5.9 %
(Scherer, Daniel)** dearer than what is applied. **So this arm's cheapening is, if anything,
UNDERSTATED at Scherer and Daniel** — and the real repair is
`scripts/data/derive_parasitic_load.py --iso SOCO`, which has never been run and which
SOCO-53e already routed as a cross-ISO data intake. **Re-routed here with SOCO's own numbers.**

### 1.4 The physical band is measurably inert (rule 21)

`[_HR_MIN_GROSS, _HR_MAX_GROSS] = [8.0, 25.0]` MMBtu per gross MWh is nwpp-42's data-integrity
guard, fixed on physics (below 8.0 implies > 42 % HHV efficiency, which no subcritical coal
boiler reaches). It is inherited, never chosen here, and never swept against a gate — and on
SOCO's own fleet it does no work:

| gross band | cap-weighted measured | Δ vs model |
|---|---|---|
| none (unbanded) | 10.8928 | −0.6338 |
| [7.0, 25.0] | 10.8912 | −0.6354 |
| **[8.0, 25.0] (applied)** | **10.8926** | **−0.6341** |
| [8.5, 25.0] | 10.8958 | −0.6309 |
| [9.0, 25.0] | 10.9212 | −0.6054 |
| [8.0, 20.0] | 10.8920 | −0.6347 |
| [8.0, 30.0] | 10.8930 | −0.6337 |

Every plausible band lands within **0.029** MMBtu/MWh of the applied value, and the **unbanded**
value is **0.0002** away. The band cannot be carrying the result.

### 1.5 Rule 19 `[R-ONE-MECH]`, established MECHANICALLY at two grains

**Built-fleet grain** (`load_fleet_from_csv`, keeper recipe ± the field), 393 rows: row set,
`pmax_mw`, `pmin_mw`, `emission_rate_co2`, `vom`, `fuel_type`, `zone` all identical; `heat_rate`
moves on **exactly 16 rows, all `COAL`, all six plants**; every other class at max |Δ|
**0.000000000000** — **`ST_GAS` (12 rows)**, CT_PEAKER (100), CC_REGULAR (90), CC_CHP (14),
CT_CHP (14), ST_CHP (13), and the 134 unclassed rows.

**LP-row grain** (`mc_base`, 2023 `fleet_only` rebuild off the keeper's own bundle), 327 rows ×
8,760 hours: **25 of 327 rows move, all of them `COAL` tranche rows**; **`ST_GAS` (20 rows)**,
CT_PEAKER (89), CC_REGULAR (67), CC_CHP (14), CT_CHP (14), ST_CHP (11) and hydro (42) all at max
|Δmc| **0.0000000000**.

**`ST_GAS` is the load-bearing cell here and it is byte-identical on both.** SOCO-53e repriced
`ST_GAS` one day ago, and plant codes **3** and **26** carry `COAL` and `ST_GAS` rows behind one
ORIS code — which is exactly where a class gate leaks. It does not: `measured_coal_heat_rates`
gates on `group == "COAL"`, `measured_st_heat_rates` on `== "ST_GAS"`,
`measured_ct_heat_rates` on `== "CT_PEAKER"`, and a row resolves to one group. The frame-level
`egrid_family_heat_rates` runs earlier, so this field **replaces** the family rate on the rows it
covers rather than stacking. **No row is priced twice.**

---

## 2. THE MECHANISM — AND WHY THIS LANE WRITES NO CODE THAT CAN CHANGE A SOLVE

`ScenarioConfig.measured_coal_heat_rates` **already exists at HEAD** (nwpp-42, 2026-09-19),
default off, registered in the cache key at its frozen default `"False"`, gated in `eia860.py`'s
row loop on `group == "COAL"`. SOCO had no artifact, so the flag was a **strict no-op** here.
**This lane adds ZERO `ScenarioConfig` fields and ZERO free parameters.** It derives SOCO's
artifact from SOCO's own plants (rule 25) and solves.

**Refused ex ante, each with its reason:**

- **`coal_prb_proxy_own_iso`.** §5's biggest routed finding and a **larger** lever than this one,
  in the opposite direction. Stacking it here would destroy attribution and is refused (rule 19,
  rule 29 single-delta).
- **Any re-derivation of `parasitic_load_factors.parquet` for SOCO** (§1.3) — a cross-ISO intake
  that re-keys 544 plants in seven ISOs.
- **Barry unit 4's class** (§1.2) — this lane *depends* on the current assignment and does not
  change it.
- **The 2025 hydro backfill** (SOCO-53b) — §5. A second delta, and an input-completeness question
  rather than a cost one.

---

## 3. G-DRIFT (rule 29(b)) — ZERO LIVE HUNKS ON SOCO'S LP PATH, AND A CONTROL SOLVE EARNED ANYWAY BY RULE 36

`git diff cc1bcb24e11a719c4d02ac3ea75834d988f0ceab HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
returns **887 insertions over 6 files**, decomposing exactly into six upstream commits:

| commit | lane | object | classification |
|---|---|---|---|
| `e63f730a` | spp-49 | `benchmark_membership_vintage_union` | **INERT** — `bool = False`, ABSENT from the keeper's `meta.json`; a benchmark gate, not an LP one |
| `13aaedd4` | miso-263 | `coal_fuel_inventory` partition guard in `input_completeness.py` | **INERT** — SOCO's `meta.json` records `coal_fuel_inventory: None` and `run_calibration.py` refuses the flag outside MISO, so the guard never fires. (It is a *fatal* guard when armed — a shard-hygiene warning this lane's prompts carry.) |
| `5356fb71` | nyiso-241 | `nyiso_ct_peaker_committed_measured` | **INERT** — new `bool = False`, NYISO-gated, ABSENT from the recipe |
| `cb1e60b7` | miso-262 | **rule 36**: cross-year warm start + same-year P1 basis seed default OFF | **INERT for this A/B, LIVE against the keeper** — see below |
| `3b719484` | pjm-h11 | `PJM_SEAM_LADDER_BY_YEAR` + 2020 | **INERT** — the only consumer is `interchange/import_nodes.py`, PJM-gated |
| `03eed7e9` | nyiso-240 | `_backfill_eia923_missing_months`, `_reattribute_dual_fuel_oil` | **INERT for the LP, NAMED for scoring** — both live in the BENCHMARK builder, and that commit's own record states no solve path is touched and that every ISO's keeper was re-scored against a repaired copy of its bench with **zero status changes**. SOCO's committed bench predates it and is NOT rebuilt here (§9), so scoring is on the same bench as the keeper; the rebuilt-bench verdict is reported beside it, labelled. |

Two precedents re-verified rather than assumed: **SOCO is not in
`eia930/frames.py::_POOL_HOURLY_MEMBERS`** (only NWPP is), so the pool path is inert for SOCO;
and the keeper's `run_config.json` records `measured_coal_heat_rates: None`.

**So form 4 would be valid on CODE grounds — and a control is solved anyway, because rule 36
`[R-YEAR-ISOLATION]` makes the keeper the wrong baseline.** The keeper was solved on
**2026-09-19 at 22:26**, through `run_calibration_full.main`'s fresh-solve path, as **ONE
three-year span**, at a basis where `MARKET_SIM_WARMSTART_XYEAR` and `MARKET_SIM_P1_BASIS_SEED`
both defaulted **ON**. Rule 36 was ruled the same day and **withdraws the neutrality claim that
justified them**. So the keeper's 2024 and 2025 carry a cross-year basis artifact of unmeasured
size at SOCO, and **every** keeper year carries a same-year P1 basis seed that a year-isolated
replay does not (the campaign floor makes SOCO a P1-native-bridge ISO, so the seed was live).
Differencing a rule-36-compliant arm against it would charge that to this lane's mechanism.
**The control is therefore earned under rule 36(e)/(f), which is a stronger reason than a LIVE
G-DRIFT hunk**, and it simultaneously discharges the FIRST TASK this lane was handed.

**Cache-key inertness.** This lane adds no field, so no key moves at any default; the SOCO
artifact is read only when the flag is armed. `check_cache_key_registration` state is recorded in
§9.

---

## 4. THE CONSEQUENCE, MEASURED BEFORE THE SOLVE

From the keeper's own committed `mc_base` arrays and `hourly/unit_hourly_<year>.parquet`.

### 4.1 Merit order (2023, hour-mean per tranche row)

| plant | economic-tranche mc, control → arm | Δ | where it lands |
|---|---|---|---|
| **6257 Scherer** | 46.203 → **43.254** | **−2.950** | squarely inside `CT_PEAKER` (p25 33.61 / p50 36.21 / p90 43.40) — **this is the row that moves dispatch** |
| 6073 Daniel | 54.151 → **50.421** | −3.730 | crosses the top of the CT band (max 50.15) |
| 6002 Miller | 28.348 → **28.124** | −0.224 | already in the money, below `CC_REGULAR`'s 31.49 max |
| 703 Bowen | 62.388 → **60.192** | −2.196 | stays above the whole gas stack |
| 3 Barry | 75.599 → **65.049** | −10.550 | stays far above the whole gas stack |
| 26 Gaston | 83.934 → **80.496** | −3.439 | stays far above the whole gas stack |

The must-run tranches sit on a floor at 4.500 and move by < 1e-6; every economic tranche falls in
**all 8,760 hours of all three years**, with no hour in either direction at any plant. For scale,
`CT_PEAKER` mc runs 27.15–50.15, `CC_REGULAR` 19.06–31.49 and `ST_GAS` 32.76–50.56.

### 4.2 Displacement UPPER BOUND, hour by hour, capped by the keeper's own headroom

For each moved row: the energy the keeper dispatched on rows the arm does **not** move, whose own
hourly mc lies strictly inside the crossed band, capped by that row's own headroom in that hour
and pro-rated when the band holds more than the headroom. **This is an upper bound and is
labelled one.**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| net COAL gain | **≤ +0.580** | **≤ +1.579** | **≤ +4.203** |
| displaced `ST_GAS` | **0.369** | 0.480 | 0.752 |
| displaced `CT_PEAKER` | **0.053** | **0.902** | 1.710 |
| displaced `CC_REGULAR` | 0.159 | 0.166 | 1.714 |
| displaced `CT_CHP` / `ST_CHP` | 0.000 | 0.030 / 0.000 | 0.024 / 0.003 |

### 4.3 STATED AT THE GATE, BEFORE THE SOLVE — this arm does NOT fix SOCO's headline defect, and it puts a passing row at real risk

The keeper's scored rows, against the committed bench (2023 denominator 239.0 TWh, 2024 248.1,
`±3.00pp` bands):

| year | class | model | actual | Δ TWh | Δ pp | status | margin |
|---|---|---|---|---|---|---|---|
| 2023 | `CT_PEAKER` | 14.356 | 4.534 | **+9.822** | +4.11 | **FAIL** | — |
| 2023 | **`ST_GAS`** | 3.601 | 10.483 | −6.882 | −2.88 | PASS | **0.288 TWh / 0.12pp** |
| 2023 | `COAL_PRB` | 20.045 | 22.374 | −2.329 | −0.97 | PASS | 2.04 pp |
| 2023 | `COAL_BIT` | 11.671 | 12.857 | −1.186 | −0.50 | PASS | 2.50 pp |
| 2023 | `CC_REGULAR` | 110.458 | 107.829 | +2.629 | +1.10 | PASS | 1.90 pp |
| 2024 | `CT_PEAKER` | 11.161 | 4.785 | +6.376 | +2.57 | PASS | 0.43 pp |
| 2024 | `ST_GAS` | 3.668 | 8.879 | −5.211 | −2.10 | PASS | 0.90 pp |
| 2025 | all | — | — | — | — | **SKIPPED** | preliminary EIA-923 vintage |

**Two things follow and both are registered here rather than explained afterwards.**

1. **The single failing row barely moves.** 2023's displaced class is **64 % `ST_GAS` and only
   9 % `CT_PEAKER`** — the crossed band at Scherer (43.25–46.20) is where SOCO's gas *steam* sits,
   not where its peakers do. A `CT_PEAKER` bound of 0.053 TWh closes **0.5 %** of a +9.822 TWh
   failure. **SOCO's headline defect is untouched by this arm**, exactly as it was by SOCO-53c and
   SOCO-53e, and for the same reason all three lanes recorded: the CT/ST misallocation is absent
   commitment physics, not a cost-side error.
2. **The 2023 `ST_GAS` row is at genuine risk of crossing OUT of band, and the bound EXCEEDS the
   margin.** It passes today by **0.288 TWh**; the 2023 `ST_GAS` displacement bound is
   **0.369 TWh**, 1.28× the margin. The campaign floor protects only the 9.2 % of `ST_GAS` energy
   it forces, and it can cut the other way: a cheaper coal fleet commits less gas steam in P0,
   which SHORTENS the campaigns the floor detects and amplifies the loss. **A flip to FAIL is a
   live, roughly even-odds outcome, it is named here with its number, and it is not a reason to
   revert anything** (rules 1 / 14: a measured physical input replaces a demonstrably
   startup-inflated annual average, and a worse fit is a discovered bug elsewhere, not a bad
   input).

**Where the arm is unambiguously right at the fuel level.** Model coal is **17–20 % BELOW** the
benchmark in 2023–2024 (31.72 vs 38.25 TWh; 32.26 vs 40.45) and model gas is **+8.4 TWh ABOVE**
(132.19 vs 123.82). This arm moves coal up and gas down — toward the benchmark on both, at the
fuel level, in the two gated years.

**Where it is unambiguously wrong, and why that is not this lane's defect.** 2025 model coal is
already **+1.86 (PRB) and +0.48 (BIT) TWh ABOVE** actual and the arm adds up to +4.2 TWh more.
That excess is the **SOCO-53b hydro input hole**: 2025 model hydro is **0.327 TWh against 6.012
measured**, and coal backfills the missing 5.68 TWh. The arm makes an artifact of a missing input
worse; the fix is the input, and it is routed in §5, not absorbed here. 2025's C1 rows are
SKIPPED, so nothing gated turns on it.

---

## 5. ROUTED, WITH NUMBERS — INCLUDING ONE LEVER LARGER THAN THIS ONE

1. **`coal_prb_proxy_own_iso` IS SOCO-53g, AND IT IS ~3× THIS LANE'S LEVER, POINTING THE OTHER
   WAY.** SOCO's three PRB plants — **6002 Miller, 6073 Daniel, 6257 Scherer, 6,361.5 MW = 55 % of
   SOCO's coal capacity** — are priced off the hand-curated **ERCOT-only** reporter pool at
   **1.8228 / 1.7520 / 1.6147 $/MMBtu** (2023/24/25). SOCO's own three reporters paid
   **2.6711 / 2.4982 / 2.4610** — the model under-prices their fuel by **+0.85 / +0.75 / +0.85
   $/MMBtu, 47–52 %**, which at a measured heat rate ~11.4 is **≈ $9.7/MWh** against this lane's
   −$2.95. It is a textbook rule 25 `[R-ISO-SCOPE]` / rule 14 `[R-ACCURATE]` defect, the gate is
   already built and default-off, and nwpp-42 explicitly left it for each ISO's own lane.
   **This lane makes coal cheaper on three plants the model already prices far too cheap on
   fuel — that is stated at the gate, and it is a reason to run SOCO-53g next, not a reason to
   stack it here** (rule 19; a single-delta arm is what makes either result attributable).
2. **`derive_parasitic_load.py` has never been run for SOCO** (§1.3), and SOCO's own coal meter
   reads **0.866–0.928** against the committed 0.93 default. Cross-ISO intake (544 plants, seven
   ISOs), re-routed with SOCO's numbers.
3. **SOCO-53b, the 2025 EIA-923 hydro hole** (§4.3): 0.327 TWh modelled against 6.012 measured,
   backfilled by coal, and this arm adds to it. The instrument is
   `--hydro-backfill-year` / `--hydro-eia930-monthly`. **DEFERRED, with the reason**: it is an
   input-completeness repair on a different input, it would be a second delta in a single-delta
   A/B, and it bites only in a year whose C1 rows are SKIPPED.
4. **Barry unit 4** (§1.2) — 362 MW the model prices as coal on a coal fuel price while CAMPD
   files it as gas. Unchanged, and this lane now measures what that costs.
5. **The coal deriver's own membership rule.** Because it selects on `primaryFuelInfo`, a model
   COAL row whose CAMPD unit is tagged gas gets its *plant's other units'* rate. At SOCO that is
   one row and it improves on net; at an ISO with more converted boilers it might not. Recorded
   for nwpp-42's successor, not changed here (rule 23).

---

## 6. EX-ANTE PREDICTION, registered BEFORE the solve, with falsifiers that name the object

The A/B is **arm − CONTROL** (both per-year, both at this SHA, both on pinned deps). P10/P11 are
the FIRST TASK's questions and are predicted here too.

| # | prediction | falsifier |
|---|---|---|
| **P1** | **COAL (`COAL_PRB` + `COAL_BIT`) RISES in every year**, by **+0.15 to +0.75 TWh** (2023), **+0.40 to +2.00** (2024), **+1.00 to +5.00** (2025). | COAL falls in any year, or rises past the upper edge in any year. |
| **P2** | **`ST_GAS` FALLS in every year**, by **0.05–0.45 TWh** (2023), 0.05–0.60 (2024), 0.10–0.90 (2025). | `ST_GAS` rises in any year, or falls by more than 1.0 TWh in any year. |
| **P3** | **The 2023 `ST_GAS` C1 row is a COIN FLIP and BOTH outcomes are predicted in advance**: it fails if it loses more than **0.288 TWh** and passes otherwise, and its bound is 0.369 TWh. Registered as a live flip either way; **neither outcome is a reason to revert** (rule 1). | The row moves by more than 1.0 TWh, i.e. the bound was not a bound. |
| **P4** | **`CT_PEAKER` FALLS in every year**, by **0.01–0.20 TWh** (2023), 0.20–1.20 (2024), 0.40–2.00 (2025) — and **the 2023 `CT_PEAKER` row STAYS FAILED above +9.5 TWh**. This arm does not fix SOCO's headline defect. | `CT_PEAKER` rises in any year, or the 2023 row changes status. |
| **P5** | **`CC_REGULAR` FALLS** by 0.02–0.40 TWh in 2023 and 2024 and by 0.30–2.50 in 2025; no `CC_REGULAR` C1 row changes status. | `CC_REGULAR` rises in any year, or any `CC_REGULAR` row changes status. |
| **P6** | **Determination `NOT-YET` (PRICE UNSCORED) on BOTH sides.** C2 / C4 / C6 / C8 PASS both sides; C3a/b/c UNSCORABLE; 0 ledgered and 0 protective caveats; **DOF unchanged at 3 entries / 1 residual**; C1 all **13/14 or 12/14** and free **9/10 or 8/10**, the split decided by P3 alone. | Any criterion other than C1 changes status, or any caveat appears, or the DOF ledger moves. |
| **P7** | **`CC_CHP` / `CT_CHP` / `ST_CHP`, nuclear, wind, solar, biomass and oil move by less than 0.010 TWh, and hydro by less than 0.001 TWh** (its monthly energy budget is binding, so its annual total is fixed by construction). The falsifier names the OBJECT: §1.5 shows every one of these classes at max \|Δmc\| exactly 0.0000000000, so movement there is a re-commitment at most and a seam defect at worst. | Any of them moves by more than 0.05 TWh, or hydro by more than 0.01 TWh. |
| **P8** | **Rule 17 `[R-FLOOR-WINDOW]` HOLDS and the shares FALL or hold**: every one of the twelve `ST_GAS` plant-years' campaign-floor binding share stays **at or below that plant's own measured synchronized share** (3 → 0.063, 10 → 0.752, 26 → 0.639, 728 → 0.843, 2049 → 0.920), **Barry keeps ZERO floored hours**, and the mechanism still touches `ST_GAS` and nothing else. Direction: cheaper coal commits less gas steam in P0, so detected campaigns shorten. | Any plant-year's share exceeds its own measured share, or Barry carries any floored hour. **A miss here is a rule 17 finding and OUTRANKS this arm's gate result.** |
| **P9** | **The marginal emission rate RISES**: the P1 load-weighted mean moves **+0.003 to +0.060** tCO2/MWh in every year from the keeper's 0.6263 / 0.6090 / 0.6369, and p90 rises or is unchanged. Direction: coal (≈0.95 t/MWh) takes marginal hours from gas steam and peakers (≈0.45–0.60). | The mean FALLS in any year, or moves by more than 0.10. |
| **P10** | **CONTROL 2023 reproduces the keeper's 2023 to < 0.010 TWh on every class.** 2023 is the FIRST year of the keeper's span, so cross-year warm start could not have reached it; only the same-year P1 basis seed and the dependency pins differ. | Any 2023 class differs by more than 0.05 TWh → the P1 basis seed is not neutral at SOCO either, and the E14 question is wider than deps. |
| **P11** | **CONTROL 2024 / 2025 may differ materially from the keeper, and that is rule 36's artifact, not this lane's mechanism.** Predicted \|Δ\| **< 2.0 TWh on every class**; reported at full magnitude whatever it is. | Any class differs by more than 5.0 TWh → SOCO carries MISO-scale year-grouping contamination and the keeper's registered 2024/2025 numbers need re-registering, which goes to the owner. |
| **P12** | **The DEP shard (control recipe, 2023, on the keeper's OFF-PIN dependency set) reproduces CONTROL 2023 to < 0.001 TWh on every class**, closing the E14 question directly instead of bounding it. | Any class differs by more than 0.01 TWh → HiGHS 1.15.1 is NOT neutral on SOCO's LP and the keeper's off-pin solve is material, which stops this lane and goes to the owner. |

**The determination is predicted UNCHANGED at `NOT-YET`.** The arm is taken anyway, and that is
rules 1 `[R-STRUCT]` and 14 `[R-ACCURATE]` operating as written: a measured operating heat rate
replaces an annual average that demonstrably folds startup fuel and offline bank fuel into the
offer, on 100 % of an 11.5 GW fleet, at **zero free parameters**, on an ISO where no price
residual exists that it could have been fitted to.

---

## 7. WHAT THE SHARDS SOLVE, AND HOW EACH IS VERIFIED

**SEVEN shards, ONE YEAR EACH, composed in the parent** — rule 36 `[R-YEAR-ISOLATION]` (a), which
is where rule 32(b)'s per-year-fan-out ban does not apply, and the owner's standing instruction of
2026-09-19 (*"Make sure to abide by the no span rule - only shards per year in it"*). **The parent
runs no LP** (rule 32(a)).

SOCO's registered year union, read from `frontend/data/backcast/registry/*.json` **before** any
prune (rule 35(b)), is exactly **{2023, 2024, 2025}** — one registered run, the keeper, no folded
touchpoints, no dangling `holdout.keeper`. All three are solved on both legs (rules 16 / 34(c)).

| shard | years | recipe | out-dir |
|---|---|---|---|
| CTL-2023 / 2024 / 2025 | one each | the keeper's `meta.json`, replayed | `results/calibration/soco53f_ctl_<year>` |
| ARM-2023 / 2024 / 2025 | one each | the same **+ `--set measured_coal_heat_rates=true`** | `results/calibration/soco53f_arm_<year>` |
| DEP-2023 | 2023 | the keeper's `meta.json`, replayed **on the keeper's OFF-PIN dependency set** | `results/calibration/soco53f_dep_2023` |

**The recipe is the keeper's own `meta.json`, not a hand-rebuilt CLI.** Every leg runs
`scripts/replay_keeper.py results/calibration/soco53e_st_hr`, whose `meta.json` is the
authoritative snapshot of every `solve_and_persist` kwarg, and the arm's single delta rides
`--set measured_coal_heat_rates=true`, which `replay_keeper` routes through **both** the explicit
kwarg and the generic `prb_overrides` channel. **A single-delta A/B by construction**, with no
risk that a hand-typed flag list drops a gate — the failure mode `scripts/lib/bundle_fleet.py`'s
header was written out of.

**Config signature each shard must see, or STOP and not push:** `measured_ct_heat_rates: true`,
`egrid_family_heat_rates: true`, `measured_st_heat_rates: true`,
`soco_gas_st_campaign_commitment: true`, every `offer_curve_by_group` band exactly 1.0, and
`measured_coal_heat_rates` **`true` on an ARM leg and `false`/absent on a CTL or DEP leg**.

**Dependencies are pinned and hard-stopped** (the SOCO-53e defect, its §10.2): every prompt runs
`pip install -r requirements.txt --ignore-installed PyYAML` — this container image ships
**without** the scientific stack, and the bare `--ignore-installed PyYAML` is required because a
Debian-installed PyYAML 6.0.1 has no RECORD file and aborts the whole install — then asserts
**highspy 1.14.0 / numpy 2.4.6 / scipy 1.17.1 / pandas 3.0.3 / pyarrow 24.0.0 / pydantic 2.13.4**
and STOPS if any differs. The DEP shard asserts the keeper's set instead
(**highspy 1.15.1 / pandas 3.0.6 / pyarrow 25.0.1 / pydantic 2.13.5**), which is the whole point
of it.

**Every shard BLOCKS on its solve** rather than ending a turn with a background process running
(the SOCO-53e defect, its §10.3: a parent cannot read a shard's disk and an idle cloud shard
cannot be woken).

**Every shard PUSHES its FULL bundle** to its own branch (rule 34(a)) — `.gitignore` NEGATION for
its own out-dir then a **plain `git add`**, never `git add -f` — including
`dispatch/<year>_P1.parquet` and the bundle-root `system.parquet`, without which composition and
registration both fail. The parent composes and registers **the ARM composite only**, keeping the
per-year dirs out of `main` (rule 32(d)).

---

## 8. ARTIFACT IDENTITY (rule 23 `[R-FROZEN-DERIVE]`)

| file | rows | sha256[:16] |
|---|---|---|
| `data/raw/_processed-legacy/campd_coal_heat_rates_SOCO.csv` | 6 plants | **`efd5926eecc62d8f`** |
| `data/raw/_processed-legacy/campd_coal_heat_rates_SOCO_units.csv` | 15 units | **`19a51bdf66c8a9ef`** |

Re-derives ONLY when CAMPD publishes new or revised vintages, never because a residual moved; the
re-derivation commit must cite the data change.

---

## 9. DOF LEDGER (rule 21 `[R-DOF]`) AND GATES AT PRECOMMIT

**This lane adds ZERO free parameters.** The keeper's ledger is unchanged at `n_entries` 3 /
`n_residual` 1. Every applied number is `sum(heatInput)/sum(grossLoad)` over the plant's own
steady hours; the deriver's four constants are nwpp-42's data-integrity guards, inherited and
shown inert in §1.4; the gross-to-net factor is the committed class default, measured against
SOCO's own meter in §1.3 with the bias stated. `authorized_price_tuning`: **NONE, and
unreachable** — SOCO has no price benchmark, so there is no price residual to tune against. **No
`authorized_price_tuning` key is written into the attestation's governance block**; the
declared-NONE statement goes in `attested_by` prose.

| gate | state at PRECOMMIT |
|---|---|
| `tests/unit/data/test_measured_coal_heat_rates.py` | **PASS (14)** — unchanged by the provenance edit |
| `ruff check` / `ruff format` | clean on every file this lane touched |
| `check_cache_key_registration` | expected PASS — no field added, no default moved |
| `check_mechanism_matrix --base origin/main` | expected PASS — no new `ScenarioConfig` field, so duty (c) is not engaged; duty (b) is discharged at registration |
| `check_bench_freshness` | RED repo-wide from `ed96378e` (caiso-284); not this lane's |
| `check_registry_payload_parity` | SOCO's namespace is CLEAN; this session's own gitignored working-tree bundles appear in a LOCAL run only (rule 31's 2026-09-16 correction) |
| `check_gate_a_provenance` | SOCO's only line is the expected NOTE; **no gate-(a) stamp**, no `calibration-complete.json` entry |
| `audit_keepers --check --iso SOCO` | E11 (post-prune lineage, expected), **E14 ×4** (the keeper's off-pin solve — this lane's DEP shard closes it), E13 will fire on registration (the documented "registered candidate, promotion pending" state) |
| `tests/unit/config/test_data_profiles_tokens.py::test_soco_token_collides_with_no_other_raw_name` | RED at HEAD, and this artifact adds one more offender. **NOT patched** — it is a naming-convention decision across every SOCO artifact and belongs to the SOCO desk (SOCO-53e routed item 7) |

**SOCO's bench parts are deliberately NOT rebuilt**, exactly as SOCO-53c / 53d / 53e did: the
auto-rebuild `dashboard_add_run.py` performs is reverted and `metrics.json` re-written on the
committed bench, because rebuilding SOCO's alone would score the arm against a different
benchmark from its control. The verdict is reported on **both** benches, labelled.

---

## 10. RETRIEVABILITY AND THE PROMOTION QUESTION (rules 31 / 34(e))

Every shard pushes its full bundle to its own branch, so a promotion costs **zero re-solves**.
The keeper's own 34-file bundle is recovered in this session at
`884dca3132e8d1d1e1f18fbb789c356506a4e343` and is gitignored, so it reaches neither `main` nor
CI. **Nothing is deleted** (rule 31). The promotion question goes to the owner in the RESULT,
with every bundle's full SHA named.

**FLAGGED FOR THE OWNER, NOT THIS LANE'S TO DECIDE (re-raised from SOCO-53e, third time):**
CLAUDE.md rule 32(b) still reads "SLIM PER-YEAR FAN-OUT IS BANNED", which is stale against rule
36 `[R-YEAR-ISOLATION]` (a) — added to the same file one day later and stating in terms that
"this is the one place rule 32(b)'s ban on per-year fan-out does NOT apply" — against rule 34(c)
("launch one shard for **each**" year), and against the owner's own standing instruction. The
ban's stated reason ("a shard can only push the slim set") was fixed by rule 34(a). **CLAUDE.md
is internally inconsistent on its face; this lane follows rule 36 and the owner's instruction and
does not silently edit the rule.**
