# PRECOMMIT — SOCO-54 (2026-09-20): the gas-steam/CT inversion is an OFFER-STACK defect, and the object is the EIA-923 *average delivered contract print* used as a *marginal* dispatch cost

**Lane** SOCO-54 · **Model** Opus · **DATA PROFILE** `soco` · **Parent LP cost: ZERO** (rule 32
`[R-SHARD]` (a)).

**Incumbent keeper / control of record (rule 29 `[R-SCREEN]` (b) form 4):**
`2026-09-20-soco53f-measured-coal-hr`, bundle `results/calibration/soco53f_coal_hr`,
basis `git_sha 04f7f849`, years {2023, 2024, 2025} (registered union confirmed from
`frontend/data/backcast/registry/*.json`, rule 35 `[R-PROMOTE]` (b)).

**THE ARM: `gas_plant_monthly_fuel_pricing = False` for SOCO. ONE pre-existing,
default-OFF `ScenarioConfig` field. ZERO new fields. ZERO free parameters.**

---

## 0. RULE 28 `[R-MECH-MATRIX]` (a) — DONE BEFORE THE LEVER WAS PICKED

Read first, not after: `docs/codebase-site/data/mechanism-matrix/SOCO.js` (all 467 lines of
cell verdicts) and `docs/mechanism-testing-matrix.md` §5.8 (the re-ranked SOCO queue).

| cell | verdict at HEAD | this lane |
|---|---|---|
| `gas_commitment_bridge` | **`R`** (SOCO-53) | **NOT re-tested.** |
| `soco_gas_st_campaign_commitment` | **`K`** (armed in the keeper) | **NOT re-tested; measured, not moved.** |
| `tranche_startup_amortization` | **`G`**, no reopen | **NOT re-opened** — and §3 shows why its named successor ("the successor object is COMMITMENT") is *also* refused here, on measurement. |
| `coal_prb_proxy_own_iso` | **`I`** (NWPP-41, re-confirmed SOCO-53g) | **NOT re-tested.** |
| **`gas_plant_monthly_pricing`** | **`U`** | **THE ARM.** No verdict exists in SOCO; ERCOT's `G` and the five keepers' `K` fill nothing here (rules 25 / 28(d)). |
| `gas_marginal_commodity_pricing` | `U` | **NOT armed** — MISO-scoped by hard error, cross-ISO cost convention is owner court. Raised in §9, not taken. |

**No cell adjudicated `R`/`I`/`G` is re-tested by this lane.**

---

## 1. PHASE-0 CHECK #1 — **THE BENCHMARK IS SOUND. IT DOES NOT OUTRANK THE LEVER.**

The handoff required this first, and required a stop if the benchmark were the defect. It
is not.

**(a) The 148.57× Jack Watson flag is REAL and IMMATERIAL.** `2049:CT_PEAKER`'s EIA-923
slice is 0.1985 TWh against a CAMPD gross of 0.0013 — a genuine CT-only-reporting plant,
correctly routed by `_flag_ct_only_reporters` to score its per-plant capture on the EIA-923
monthly row. Its whole magnitude is **0.1985 TWh of the 4.534 TWh CT_PEAKER actual (4.4 %)**.
It cannot explain +9.73 TWh, and it touches the C1 *class* total not at all (C1 scores
`classFull`, the EIA-923 class sum, not the per-plant capture).

**(b) No CT_PEAKER plant is missing from the class actual.** Two plants carrying 2.706 TWh
of model CT_PEAKER energy in 2023 are **absent from the per-plant bench layer** — 7709
**Dahlberg** (Southern Power, GA) and 54538 **Hartwell Energy Facility** (Oglethorpe, GA).
Both were checked against `run_calibration_full._eia923_frame(2023, …, "SOCO")`: **both are
inside the CT_PEAKER class frame**, at 0.2397 and 0.2071 TWh. The class total reconstructs to
4.5961 TWh against `classFull`'s 4.5342 (the difference is the BTM subtraction and the
vintage reconcile). Nothing is missing.

**(c) The two bench-absent plants are the MOST over-dispatched in the model**, which is the
opposite of a benchmark defect: 54538 model 1.7275 vs actual 0.2071 (**8.3×**), 7709 model
0.9781 vs actual 0.2397 (**4.1×**) — together **2.259 TWh, 23 % of the 9.73 TWh gap, at two
plants.**

**VERDICT: the benchmark stands; the +9.73 TWh is the model's.**

---

## 2. PHASE-0 CHECK #2 — **THE CAMPAIGN FLOOR FIRES. IT IS THE OFFER STACK THAT CAPS IT.**

The handoff asked whether P0 fails to start enough campaigns. It does not. Measured on the
keeper's own committed `unit_hourly_<y>.parquet`, at PLANT grain, P1:

| year | plant | online h | **median load frac while online** | share of ONLINE hours with `mc < price` | model TWh | actual TWh |
|---|---|---|---|---|---|---|
| 2023 | 728 Yates | 659 | **0.083** | **0.073** | 0.0605 | 2.239 |
| 2023 | 26 Gaston | 1,734 | **0.066** | 0.295 | 0.5570 | 1.654 |
| 2023 | 10 Greene Co | 2,938 | **0.137** | 0.348 | 0.5743 | 1.314 |
| 2023 | 2049 Watson | 7,234 | 0.419 | 0.495 | 2.3553 | 3.270 |
| 2024 | 728 Yates | 4,281 | **0.083** | 0.328 | 0.9118 | 2.096 |
| 2025 | 728 Yates | 6,572 | **0.074** | 0.259 | 0.9394 | 1.300 |

**SOCO's gas steam is COMMITTED and cannot generate.** The `soco_gas_st_campaign_commitment`
floor holds these boilers synchronized for 659–7,234 hours a year — its job, done — and they
then sit **pinned at 6–14 % of capacity** because they are out of merit in **65–93 %** of the
hours they are online. Yates 2023 is the extreme: online 659 h, in-merit in **7.3 %** of them.

The model's start counts are not the problem either: Gaston 4, Yates 7, Barry 3, Greene 39,
Watson 44 starts/yr against a measured 5.0–9.7. **Strengthening commitment adds online hours,
not MWh.**

---

## 3. PHASE-0 CHECK #3 — **THE MERIT-ORDER DISTANCE, AND WHY EVERY COMMITMENT LEVER IS CAPPED FAR BELOW IT**

The handoff named this the lever's ceiling, and required a magnitude. Measured per LP tranche
against its own zone's hourly `price`:

> **In-merit-but-not-dispatched ST_GAS headroom, 2023: 0.0727 TWh** — against a **−6.935 TWh**
> C1 gap. **One percent.**

There is no idle in-merit gas steam to find. Everything missing is **out of merit**, and the
distance is large: Yates `mc` p50 **$44.59/MWh**, Gaston **$41.50**, Greene **$40.23**, against
a mean clearing price of **$31.56** and against Hartwell at **$27.15** and Hawk Road at
**$28.38**.

**Three commitment levers are refused here on measurement, ex ante:**

1. **A start cost in the objective** (the `tranche_startup_amortization` `G` cell's own named
   successor). Measured: the model's CTs do **not** two-shift — 54538 runs at **73.6 % CF**
   with a **760-hour** maximum block, 55141 at **62.5 %** with 738 h. At 207 starts × 268 MW ×
   ~$40/MW over 1.728 TWh a start cost amortizes to **≈$1.28/MWh**. Against a $17.44/MWh
   distance it is **INERT**. (This is the P3 error of `FINDING-soco-53g` §6, avoided by
   measuring the distance before predicting.)
2. **A CT min-run / min-down floor.** It raises CT energy. Wrong sign.
3. **Strengthening the ST campaign floor.** SOCO-53d already measured that its incremental
   hours are marginal-`CC_REGULAR` in 1,170 of 3,988 against `CT_PEAKER` in 681; and §2 shows
   the floored plants are already at min-load. It adds online hours, not the 6.9 TWh.

**The handoff's own stop condition is met: "If SOCO's gas steam is priced above the margin, no
commitment floor will fix it and the object is the offer stack instead."** It is, and it is.

---

## 4. THE OBJECT, MEASURED — IT IS **FUEL PRICE**, NOT HEAT RATE, AND THAT IS NEW EVIDENCE

SOCO-53 closed the cost side with *"the model already over-separates `CT_PEAKER` from `ST_GAS`
by +1.983 MMBtu/MWh against a measured +0.713 — 2.8× — so no cost-side lever can close it."*
**That claim was derived from HEAT RATES alone.** It holds, and it is not the whole cost side.
Decomposing `mc = HR × fuel + vom` off a `fleet_only` rebuild of the keeper's own recipe:

| plant | class | HR | **$/MMBtu** | mc | model TWh | actual TWh |
|---|---|---|---|---|---|---|
| 54538 Hartwell | CT_PEAKER | 11.500 | **2.057** | **27.15** | 1.7275 | 0.207 |
| 55141 Hawk Road | CT_PEAKER | 11.275 | **2.207** | **28.38** | 2.2090 | 0.569 |
| 55244 Doyle | CT_PEAKER | 12.119 | **2.397** | 32.55 | 1.0376 | 0.054 |
| 2049 Jack Watson | ST_GAS | 10.360 | 2.776 | 32.76 | 2.3553 | 3.270 |
| 10 Greene County | ST_GAS | 10.207 | **3.550** | 40.23 | 0.5743 | 1.314 |
| 26 E C Gaston | ST_GAS | 11.074 | **3.386** | 41.50 | 0.5570 | 1.654 |
| **728 Yates** | **ST_GAS** | 10.797 | **3.759** | **44.59** | **0.0605** | **2.239** |

**The heat rates are the same machine class (10.2–12.1). The separation is $1.0–1.7/MMBtu of
FUEL, which at ~11 MMBtu/MWh is $11–19/MWh — exactly the $17.44 distance §3 measured.** No
lane has examined it: `gas_plant_monthly_pricing` is `U` in SOCO's shard.

**The prices are genuine filings, not a loader artifact.** `scripts/data/process_f923_fuel_costs.py`
is a straight quantity-weighted aggregation of EIA-923 Schedule-2 receipts with no imputation,
and each plant's series reconstructs from its own receipts (Hartwell 2.474 TBtu at $2.051
quantity-weighted; Yates 26.544 TBtu at $3.585).

**What makes them inadmissible as a MARGINAL cost is their basis, and it is measurable.**
Seven SOCO plants carry a monthly delivered-price series that is **one common shape × a
plant-constant multiplier to four significant figures** (ratio CV ≤ 0.0008 across all twelve
months): 54538 ×1.0000, 55141 ×1.0730, 55244 ×1.1349, 7813 ×1.4382, 7829 ×1.4441, 7916
×1.4905, **728 Yates ×1.8279**. Every other SOCO gas plant's ratio series has CV 0.03–1.63.
**These are formula contract prices** — an index times a negotiated multiplier — and
**Hartwell's is below Henry Hub in eleven of twelve months of 2023** ($1.66–2.26 against
HH $2.15–3.27), which no *delivered* gas can be.

**And the model burns volume the contract never covered.** Model gas burn against the plant's
own EIA-923 procurement, 2023: **55409 Calhoun 159.6×, 6124 McIntosh 26.1×, 55244 Doyle 20.6×,
54538 Hartwell 8.0×, 55141 Hawk Road 4.0×** — while burning only **2 %** of Yates's
procurement, **33 %** of Gaston's and **42 %** of Greene County's.

**THE CLAIM (rule 1 `[R-STRUCT]` + rule 14 `[R-ACCURATE]`'s misalignment clause):** a dispatch
offer is a **marginal** cost; the EIA-923 print is an **average delivered contract cost**
carrying demand charges, reserved transport and a negotiated multiplier amortized over the
month's takes. Extending one party's contract multiplier to eight times the volume it covered,
and letting it set the merit order against another party's, prices a **rent transfer** as a
**physical cost**. This is MISO-224's own accepted reasoning (`miso_gas_marginal_commodity_pricing`,
`scenarios.py`: *"the print is an average cost measured on a different basis (rule 14
misalignment clause)"*) — **derived here from SOCO's own data and never transferred**
(rules 25 / 28(d)).

**What the arm falls back to is a measured market price, not a guess.** With the field off,
every SOCO gas unit prices on ONE monthly series — 2023 $3.657 / 3.498 / 3.244 / 2.926 / 2.862 /
2.957 / 3.021 / 3.021 / 2.862 / 3.021 / 3.339 / 3.752, annual mean **$3.179/MMBtu** — built on
the run's `gas_price_override = 2.54`, the **realized 2023 Henry Hub annual average**, plus the
model's delivery basis. It sits inside the three states' own quantity-weighted receipt averages
(GA $3.074, AL $3.204, MS $2.760). `nearby_fuel_price_fallback` is gated **by** this field, so
one flag moves one object (rule 19 `[R-ONE-MECH]`).

---

## 5. RULE 19 `[R-ONE-MECH]`, ESTABLISHED MECHANICALLY AT TWO GRAINS, BEFORE THE SOLVE

`fleet_only` rebuilds off the keeper's own `meta.json`, per-class max |Δ|
(`scripts/probes/_soco54_phase0.py rule19`):

| year | `fuel_prices` classes moved | `mc_base` classes moved | every other class |
|---|---|---|---|
| 2023 | CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, ST_CHP, ST_GAS | same six | **max \|Δ\| exactly 0.0000000000** |
| 2024 | same six | same six | **0.0000000000** |
| 2025 | same six | same six | **0.0000000000** |

Max |Δ| `mc_base`: 2023 32.276 (CT_PEAKER) / 25.641 (ST_GAS) / 14.440 (CC_REGULAR);
2024 44.425 / 35.292 / 26.158; 2025 41.484 / 29.469 / **52.437** (CC_REGULAR).
**COAL, oil, nuclear, hydro, wind, solar, biomass, OTHER: untouched in all three years.**
The arm moves **exactly one object** — the source of the gas fuel-price series — and it moves
**every gas class**, which is the mechanism's correct scope, not stacking.

---

## 6. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — **ALL HUNKS INERT. NO CONTROL SOLVE.**

`git diff 04f7f849 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
= 5 files, +445/−11. Every hunk classified, with its reason verified mechanically:

| file | hunk | classification |
|---|---|---|
| `config/scenarios.py` +89 | one new field `caiso_citygate_blackout_bridge: bool = False` + comment | **INERT** — default-off flag, absent from the SOCO recipe, CAISO-gated at its applier. |
| `data/fuel/hubs.py` +262, `data/fuel/__init__.py` +1 | `_basis_bridge_blackouts` | **INERT** — the only call site (`hubs.py:1163`) is inside the `config.caiso_citygate_blackout_bridge` branch. |
| `config/constants.py` +62 | `REGIONAL_RENEWABLE_CF`, `PPA_COST_RECOVERY_YR` | **INERT** — `grep -rl` over `src/`+`scripts/` returns exactly `constants.py`, `scripts/build_mac_sidecar.py`, `scripts/data/derive_regional_renewable_cf.py`. Neither consumer is on the solve path. |
| `model/capacity_evolution/new_entry.py` +42 | `wind_ptc_levelized_per_mwh` | **INERT** — capacity-evolution new-entry / `policy/ira.py` screen only; a `mode="backcast"` run never enters `evolve_fleet`. |

**DECLARED, because it is visible and is NOT this lane's:** SOCO's solve-surface fingerprint
(capx D79) moved `f4d250dfebdf2c96` (keeper, **180 rows**) → `60895cac1f7c8879` (HEAD, **182
rows**). `moved_rows("SOCO")` is **`{}`** — **zero existing rows changed value**; the delta is
the two new `constants.py` names above, which are exactly the pair `check_cache_key_registration`
has RED at HEAD (commit `3fc20b97`, the MAC-sidecar lane). A fingerprint that grew by two
undeclared names **re-keys the cache and cannot change a number**. Form 4 stands; routed in §9,
not patched.

---

## 7. THE DECLARED `--set` TRANSPORT (audit_keepers E11)

`replay_keeper.py --set` routes a `ScenarioConfig` field that is not a `solve_and_persist`
kwarg through the generic `prb_overrides` channel, so each leg's `meta.json` will record a
`coal_prb_sigmoid_overrides` diff. **DECLARED HERE, BEFORE THE SOLVE, and benign:** the
composer and the attestation both assert the **RESOLVED**
`scenario_config.coal_prb_sigmoid_overrides` is **`null`** on every leg, as SOCO-53f and
SOCO-53g did. A leg that resolves non-null is a STOP.

---

## 8. PREDICTIONS — EX ANTE, PER CLASS, WITH FALSIFIERS THAT NAME THE OBJECT AND A MAGNITUDE

The magnitude is not asserted. It is computed by a **calibrated greedy merit re-stack**
(zero-LP): every non-competing class held at the keeper's own hourly output, the competing
block (`CC_REGULAR` + `CT_PEAKER` + `ST_GAS` + `COAL`) re-stacked hour by hour against its own
LP energy under BASE and ARM `mc_base`. Its BASE leg reproduces the keeper to
CC 110.871 vs 110.425, CT 13.006 vs 14.261, COAL 33.813 vs 31.912, ST_GAS 2.456 vs 3.548 —
so it **under-states** ST_GAS (it cannot see the campaign floor) and is used for **deltas only**.

| # | prediction | falsifier |
|---|---|---|
| **P1** | **2023 `CT_PEAKER` FALLS**, by **1.5–3.5 TWh** (point estimate **−2.45**), from 14.261 to **10.8–12.8**. | A fall < 1.0 TWh, or any RISE. |
| **P2** | **2023 `ST_GAS` RISES**, by **0.3–1.2 TWh** (point **+0.66**), from 3.548. | A fall > 0.10 TWh. |
| **P3** | **2023 `CT_PEAKER` STAYS FAILED.** It needs −2.54 TWh *and* −1.05pp to re-band; P1's point estimate is −2.45, **just short**. A flip to PASS is possible and would be a *narrow* pass, reported as such. | Either outcome is consistent; a fall that leaves it above **+8.7 TWh** falsifies P1 instead. |
| **P4** | **THE STATED RISK: 2024 `CC_REGULAR` may cross from PASS to FAIL.** It sits at +5.030 TWh / +1.86pp with headroom **+2.16 TWh / +1.14pp**, and the re-stack predicts **+1.745 TWh** — **81 % of its volume margin**. | If `CC_REGULAR` 2024 moves < +0.5 TWh the predictor is wrong about the CC leg. **Under rule 1 a FAIL here does not reject the mechanism**; it is reported at full magnitude. |
| **P5** | **2023 `ST_GAS` is the second thinnest row** — headroom 0.255 TWh / **0.10pp**. P2 says it improves; if it *worsens* by > 0.26 TWh it FAILS and C1 goes 13/14 → 12/14. | A worsening of any size falsifies P2. |
| **P6** | **2024 `CT_PEAKER` FALLS 0.8–2.0 TWh** (point −1.37), from 10.597; it PASSES either way (headroom +1.38 TWh / +0.68pp) and a fall can only widen that. | A rise of any size. |
| **P7** | **NO 2025 C1 CLASS ROW CHANGES STATUS** — all seven are SKIPPED (preliminary EIA-923 vintage). 2025 moves are REPORTED, never scored. | Any 2025 class row acquiring a PASS/FAIL. |
| **P8** | **`COAL_PRB`, `COAL_BIT`, `nuclear`, `hydro`, `wind`, `solar`, `biomass`, `oil`, `OTHER` move by < 1.0 TWh in each year** — they carry `mc_base` max \|Δ\| **exactly 0.0** (§5), so any move is pure re-dispatch. | Any of them moving > 1.0 TWh. |
| **P9** | **`CC_CHP` / `CT_CHP` / `ST_CHP` each move < 0.30 TWh.** Their `mc_base` moves (max \|Δ\| 5.5–18.7) but they are must-run. | Any moving > 0.30 TWh. |
| **P10** | **Determination `NOT-YET` in every case**, C3a/C3b/C3c UNSCORABLE, ceiling PHYSICALLY-CALIBRATED (PRICE UNSCORED). C2/C4/C6/C8 PASS. **0 ledgered, 0 protective caveats. DOF 3 entries / 1 residual — ZERO free parameters, ZERO new fields.** | Any caveat appearing, or any DOF entry added. |
| **P11** | **Rule 17 `[R-FLOOR-WINDOW]` holds in all fifteen plant-years** — every campaign-floor binding share stays at or below that plant's own measured synchronized share (Barry 0.0632, Greene 0.7516, Gaston 0.6392, Yates 0.8429, Watson 0.9202). The arm **cheapens** Yates/Gaston/Greene, so the floor should bind **less**, not more. | Any plant-year binding share exceeding its measured synchronized share. |
| **P12** | **Rule 20 `[R-FORCED-BUDGET]` / C8 PASSES** — ST_GAS forced share falls from 0.094 / 0.100 / 0.116 against the 30 % cap, because cheaper gas steam dispatches above its floor. | Forced share rising above 0.30 in any year. |

**Stated at the gate, before the solve: P1's point estimate closes roughly a QUARTER of the
9.73 TWh headline, and P3 says the failing row most likely stays failed.** This lane is not
predicting a fix. It is predicting that a mis-based cost input is removed and the residual
moves the right way. Rule 1 `[R-STRUCT]` decides, not the residual — and **P4 pre-registers
the cost, which is that a currently-passing row may fail.**

---

## 9. ROUTED, NOT TAKEN

1. **`gas_marginal_commodity_pricing` for SOCO** — the *reconciled* form rule 14 prefers (hub
   daily + measured variable transport) instead of this arm's blunt fall-back to one monthly
   series. `miso_gas_marginal_commodity_pricing` is **MISO-scoped by hard error** and its
   comment puts the cross-ISO cost convention in **owner court**. SOCO has no committed daily
   hub series (`data/raw` carries no Transco Zone 4 / SONAT dailies). **Owner question, §11.**
2. **`check_cache_key_registration` RED at HEAD** for `PPA_COST_RECOVERY_YR` and
   `REGIONAL_RENEWABLE_CF` (commit `3fc20b97`). It also **moves every ISO's solve-surface
   fingerprint** by growing the row set with two undeclared names (§6) — SOCO 180 → 182 rows,
   `moved_rows` `{}`. Not this lane's; measured and routed.
3. **`derive_parasitic_load.py` has never been run for SOCO** — carried forward unchanged from
   `FINDING-soco-53f` §2.4 and `-53g` §9.3.
4. **SOCO-53b, the 2025 hydro hole** — 0.327 TWh modelled against 6.012 measured.
5. **Barry unit 4** — a 362 MW COAL model row CAMPD files as Pipeline Natural Gas.
6. **`audit_keepers` E13** fires for the **sixth** consecutive SOCO lane (the registered
   `soco53g-prb-own-iso` candidate the owner has not ruled on). Re-raised, not cleared.
7. **SOCO's committed bench does not carry nyiso-240's EIA-923 repair.** Both benches scored.

---

## 10. SHARDS (rules 32 / 34 / 36)

**One shard per year** — rule 36 `[R-YEAR-ISOLATION]` (a), the one place rule 32(b)'s fan-out
ban does not apply — 2023 / 2024 / 2025, each pushing its **full** bundle including
`dispatch/<y>_P1.parquet` and the bundle-root `system.parquet` (rule 34 `[R-SHARD-PROMOTABLE]`
(a)). Composed in the parent at zero LP. Every leg is driven from the keeper's own `meta.json`
so the A/B is single-delta by construction:

```
python3 scripts/replay_keeper.py results/calibration/soco53f_coal_hr \
  --years <Y> --out-dir results/calibration/soco54_arm_<Y> \
  --set gas_plant_monthly_fuel_pricing=false
```

**THE PARENT NEVER SOLVES** (rule 32(a)).
