# FINDING — nyiso-174: the East River crosswalk defect is REAL, is a ONE-PLANT defect at 97.8 % of the misclassed volume, and the wrong side is the PROBE-SIDE measured construction — the model, the EIA-923 class benchmark and the primary record already agree, so the repair moves NOTHING on C1 and instead FLIPS nyiso-170 §3's CT_CHP identification blocker

**Session:** nyiso-174 · **Date:** 2026-09-02 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Solves run: ZERO.**
**No parameter was touched, no band was swept, no run was registered.**

---

## 0. The result in one paragraph

The brief handed forward a named input defect with a measured size: East River
(2493) is `ST_CHP` in the model's tranche artifact but lands in `CC_CHP` under
the shared CAMPD `unitType` construction, carrying 2.13–2.19 TWh/yr into five
sessions' measured CC_CHP series. **The primary record adjudicates it three
independent ways and they all say the same thing: the model is right and the
CAMPD `unitType` construction is wrong.** EIA-860 codes the plant `GT`×2 +
`ST`×2 with **no combined-cycle prime mover (`CA`/`CT`/`CS`) anywhere**;
EIA-923 files its net generation under **two** prime movers, `GT` and `ST`, in
every year; and CAMPD's own meters refute CAMPD's own label — the two units it
tags `"Combined cycle"` burn at a measured **10.51–10.89 MMBtu/MWh**, a
simple-cycle heat rate ~45 % above the combined-cycle band, and export
**zero** steam, while the steam sits entirely on two boilers that generate
nothing. The model's bins reproduce EIA-860's summer split **to the megawatt**
(`CT_CHP` 306.0 = 152.1 + 153.9; `ST_CHP` 309.5 = 132.7 + 176.8). Run both ways
over the whole NYISO fleet the defect is **one plant**: 228 of 773 NY CAMPD
unit-years disagree, but by volume East River is **6.581 of 6.729 TWh —
97.8 %** — of the misclassed energy, the next entry being nyiso-173 S1's
already-named S A Carlson at 0.142 TWh. And the decisive consequence, which
needed measuring rather than assuming: **the defective construction never
touched a scored quantity.** nyiso-169b's measurement A — the C1 class volume
errors — is recomputed here and reproduces its published numbers exactly
(2025 CC_CHP **+16.30**, CC_REGULAR **+6.40**, CT_PEAKER **−63.73**, ST_GAS
**−28.63**), because both its inputs run on the EIA-860/923 prime-mover basis:
the keeper's P1 `class_hourly`, and `classFull`, which
`_benchmark_eia923_frame` → `_eia923_frame` → `_classify_f923` →
`plant_taxonomy.classify_plant` builds on prime movers. **So there is no
model-side, data-side or config-side repair to arm — the wrong side is not in
the model at all**, and the deliverable is the corrected construction itself
(`scripts/lib/campd_measured_classes.py`), which costs no solve. What the
correction *does* move is four committed findings' probe-side basis, and one
conclusion **flips**: nyiso-170 §3's "**CT_CHP is NOT identifiable from
CAMPD**" (anchor 4.933, 1 unit) becomes **anchor 0.892 on 3 units** — CT_CHP
hourly conduct IS identifiable. nyiso-171's portfolio-artifact conclusion is
**strengthened to unanimity** (sum-of-plant-minima 0.0 MW in all three years,
0 plants never off, against its own 0.0/81.0/85.0), nyiso-172 §3.4's bound
**grows ~60 %** (93 → 219 / 773 → 1,523 / 1,211 → 1,926 hours), nyiso-173's
adjudication **survives untouched**, and **CC_CHP's own anchor gets worse**
(1.070 → 1.241), so nyiso-170's "CC_CHP identifiable" was itself partly an
artifact of the defect.

---

## 1. What was measured, and off what

`scripts/probes/nyiso174_class_crosswalk_audit.py`, zero solve, five
measurements off committed artifacts plus the primary record:

| source | what it supplies |
|---|---|
| `data/raw/eia-860/eia860_generator_operable.parquet` | per-generator `Prime Mover`, `Technology`, summer/winter/nameplate MW, minimum load, CHP flag |
| `data/raw/_processed-legacy/eia923_monthly_generation.parquet` | Page-1 net generation by `prime_mover` × `chp`, 2023–2025 |
| `data/raw/campd-unit-level/NY_{year}.parquet` | per-unit hourly `grossLoad`, `heatInput`, `steamLoad`, `opTime`, `unitType` |
| `market_sim.data.fleet.load_fleet_from_csv` | the model's own loaded NYISO fleet — the EIA-860 side, through `plant_taxonomy.classify_plant` |
| `frontend/data/backcast/bench/NYISO/{year}.json.gz` | committed grid-delivered `classFull` |
| `results/calibration/nyiso159_lossarm_B/hourly/class_hourly_*.parquet` | the keeper's own P1 class dispatch (rule 15: read, don't replay) |
| `results/calibration/nyiso159_lossarm_B/legitimacy_diagnostics.json` | D-1 / D-2 rows |
| `data/raw/campd-unit-outages-NYISO.csv` + `market_sim.data.outages` | the overlay's own routing decision, run through the engine's function |

Output: `results/calibration/_nyiso174_class_crosswalk_audit.json`.

**Reproduction check, run before anything was restated.** On the *old*
construction the probe reproduces nyiso-171 §2.3's committed A3 numbers
exactly — 17 plants, sum-of-plant-minima **0.0 / 81.0 / 85.0 MW**, fleet minima
**282 / 368 / 184 MW**, plants-never-off `[2493]` in 2024 and 2025 and none in
2023 — and nyiso-172 §3.4's violation-hour counts exactly (**93 / 773 /
1,211**), and nyiso-173 S3's violating-hour means exactly (2025 model −
measured = **1,646.5 MW** against its 7,749 − 6,102 = 1,647). The construction
is therefore verified against three committed sessions before it is used to
change any of them.

**All twelve inherited probes were re-run first, and all twelve reproduce.**
nyiso-168 gap anatomy (deficit **−$6.59 = −$2.32 + −$4.27**); nyiso-168 reserve
supply slack (trap (a): reproduces to a max **relative** delta of **3.6e-16**
over 309 numeric leaves, **zero** structural or verdict differences — churn
**reverted, not committed**); nyiso-169 congestion gradient (trap (b) handled —
the container's DA LBMP months were re-fetched and `nyiso-interface-flows`
regenerated before it ran, after which DA `hours_covered` reads **8760/yr**);
nyiso-169b (CC_CHP **+16.3 %**, CC_REGULAR **+6.4 %**); nyiso-170
(`proceed_to_phase_2: false`), nyiso-170b/c/d (`survives_all_years: true`);
nyiso-171 (coverage **0.253 / 0.502 / 0.313**); nyiso-172
(`proceed_to_arm: false`); nyiso-173 (**773 / 1,211** violating hours, coverage
0.831); nyiso-173b (peak utilisation **0.794 / 0.821 / 0.839**, unused headroom
**2,745 / 2,630 / 2,363 MW**). **Eleven produced zero git churn**, i.e.
byte-identical output; the twelfth is trap (a). Trap (c) (`Etc/GMT+5`) and trap
(d) (CAMPD `grossLoad` NULL filled to zero explicitly) are handled throughout
this session's own probe.

> **A NEW TRAP, same family as the brief's trap (b), documented for
> successors.** `nyiso168_reserve_supply_slack` **silently degrades** when the
> `ancillary-services` clean partition is absent from a fresh container: it
> **drops its entire `DAM` and `RTM` measured reserve-price blocks** — 127
> lines, including every `cascade` / `regulation` mean and band — and still
> **exits 0**, writing a truncated JSON that looks like a legitimate result.
> Committing that would silently delete a committed measurement. It also needs
> the `fleet` partition, without which it fails loudly (`FileNotFoundError` on
> `data/clean/fleet/fleet_2023.parquet`) — the loud failure is the *safe* mode;
> the quiet one is not. **Regenerate `fleet` AND `ancillary-services` before
> running it, and diff the output structurally, not just numerically.**

*One unreconciled item, stated rather than papered over:* nyiso-172 §3.4's
reported **"CC mean gap" column (+224 / +495 / +636 MW)** could not be
reconstructed from any of four natural definitions (mean or median of
model − bound over violating hours; mean of model − measured; clipped mean over
all hours), which give 266.4 / 228.3 / 416.0, 241.5 / 153.1 / 364.9,
1,045.7 / 1,307.9 / 1,646.5 and 2.8 / 20.1 / 57.5 respectively. It is a
**reported column, not a gate**, the gated statistic reproduces exactly, and
nothing in this session depends on it. Flagged for whoever next cites it.

---

## 2. M1 — WHICH SIDE IS WRONG. Three independent primary records, one answer

### 2.1 EIA-860: prime movers `GT` and `ST`, and no combined cycle at all

| generator | technology | prime mover | nameplate | summer | winter | min load | online |
|---|---|---|---|---|---|---|---|
| 1 | Natural Gas Fired Combustion Turbine | **GT** | 180.0 | 152.1 | 196.7 | 110 | 2005 |
| 2 | Natural Gas Fired Combustion Turbine | **GT** | 180.0 | 153.9 | 199.5 | 110 | 2005 |
| 6 | Natural Gas Steam Turbine | **ST** | 156.2 | 132.7 | 132.7 | 45 | 1951 |
| 7 | Natural Gas Steam Turbine | **ST** | 200.0 | 176.8 | 185.9 | 65 | 1955 |

EIA's combined-cycle prime-mover codes are `CA` (steam part), `CT` (turbine
part) and `CS` (single shaft). **None of the three appears at this plant.**
Summer capacity by prime mover: **GT 306.0 MW, ST 309.5 MW.**

### 2.2 The model's bins reproduce that split to the megawatt

`load_fleet_from_csv("NYISO", …, year=2025)` carries four units at plant 2493 —
`2493_1`, `2493_2` (`plant_group = CT_CHP`, `fuel_type = gas_ct`) and `2493_6`,
`2493_7` (`ST_CHP`, `gas_st`) — the EIA-860 generator IDs and prime movers
one for one. `bin_assignments_NYISO.csv` carries **two** rows, `CT_CHP` 306.0
and `ST_CHP` 309.5, flagged `Mixed_Facility = "CT+ST"`, i.e. **exactly**
EIA-860's summer split.

> **A brief-premise correction, recorded.** The brief describes East River as
> "`ST_CHP` in `thermal_tranches_NYISO.csv`". That is true and it is the whole
> story of that file — the tranches CSV carries **only** the plant's `ST_CHP`
> row and no `CT_CHP` row — but the model artifact was never "`ST_CHP`" tout
> court. The fleet and the bin sheet both carry **both** bins. The missing
> tranches row is itself a finding; see §6 item 2.

### 2.3 EIA-923: net generation filed under two prime movers, every year

| year | `GT` net TWh | `ST` net TWh |
|---|---|---|
| 2023 | 2.0221 | 1.0566 |
| 2024 | 2.1492 | 0.7450 |
| 2025 | 2.0792 | 0.6745 |

Both rows carry `chp = Y`. A plant EIA-923 splits across `GT` and `ST` is not a
combined cycle in EIA's taxonomy, and the class benchmark `classFull` — built
through the same `classify_plant` — therefore already places this plant's
energy in **`CT_CHP` + `ST_CHP`**. Corroboration in the numbers: 2025 bench
`CT_CHP` = 2.3829 TWh against East River's `GT` 2.0792 (**87 %** of the class),
and bench `ST_CHP` = 0.7997 against its `ST` 0.6745 (**84 %**).

### 2.4 CAMPD's own meters refute CAMPD's own label

| unit | `unitType` | 2025 gross TWh | peak MW | measured HR | steam export |
|---|---|---|---|---|---|
| 1 | **Combined cycle** | 1.093 | 268 | **10.888** | **0 klb** |
| 2 | **Combined cycle** | 1.095 | 285 | **10.510** | **0 klb** |
| 60 | Dry bottom wall-fired boiler | **0.000** | 0 | — | 3,354,662 klb |
| 70 | Dry bottom wall-fired boiler | **0.000** | 0 | — | 3,866,420 klb |

Measured heat rates on the two `"Combined cycle"` stacks are **10.51–10.89**
MMBtu/MWh in every year (2023: 10.736 / 10.549; 2024: 10.818 / 10.577). A
combined cycle burns ~6.9–7.5. These are simple-cycle numbers, and they are
**not** depressed-then-inflated by cogeneration accounting: those two stacks
report **zero** steam load, so no fuel is leaving them as heat. The steam —
and the CHP character — sits entirely on units 60/70, which report **zero
generation**.

**Verdict on (1)(a): the model artifact is CORRECT; the shared CAMPD
`unitType` construction is WRONG.** `unitType` is a CEMS
monitoring-configuration descriptor, not an EIA prime-mover code, and
`_chp_group_from_unit_type`-style string mapping treats it as one. The plant is
genuinely **MIXED (CT + ST)** — but it needs **no** per-unit split of the
Ravenswood-2500 `_FLEET_GROUP_OVERRIDE` kind, because **the model already
carries the split correctly**. What needed repairing was the measurement.

---

## 3. M2 — HOW MANY OTHER PLANTS. One, at 97.8 % of the volume

The crosswalk run both ways over every NY CAMPD unit-year of 2023–2025 — a unit
"disagrees" when the class its `unitType` implies is not one its plant's model
fleet carries:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| CAMPD NY measured TWh | 57.825 | 65.216 | 67.375 |
| disagreeing TWh | 2.353 | 2.439 | 2.514 |
| disagreeing share | 4.07 % | 3.74 % | 3.73 % |

**773 unit-years, 228 disagreeing.** By volume over the three years:

| plant | name | `unitType` class | model classes | 3-yr TWh |
|---|---|---|---|---|
| **2493** | **East River** | `CC_CHP` | `CT_CHP,ST_CHP` | **6.5811** |
| 2682 | S A Carlson | `CC_REGULAR` | `CT_PEAKER,ST_GAS` | 0.1421 |
| 2490 | Arthur Kill | `CT_PEAKER` | `ST_GAS` | 0.0029 |
| 8906 | Astoria Generating Station | `CT_PEAKER` | `ST_GAS` | 0.0022 |
| 2500 | Ravenswood | `CT_PEAKER` | `CC_REGULAR,ST_GAS` | 0.0008 |
| 2516 | Northport | `CT_PEAKER` | `ST_GAS` | 0.0001 |

**Misclassed total 6.7292 TWh, of which East River is 6.5811 = 97.8 %.**

**Answer to (1)(b): this is a ONE-PLANT repair, not a systematic crosswalk
defect.** The 227 other disagreeing unit-years are 0.148 TWh in aggregate —
0.07 % of measured NY energy — and **2682 (S A Carlson) is confirmed as the
same family** as nyiso-173 S1 named it, now sized at 0.142 TWh over three
years. The four `CT_PEAKER → ST_GAS` entries are small auxiliary turbines at
steam plants the model carries no CT bin for; they are a **population**
question, not a classification one, and the correction deliberately leaves them
alone (§4.1).

A separate **0.5775 TWh** over three years sits at plants CAMPD sees and the
model fleet has no bin for at all — largest Oswego Harbor Power (2594) at
0.222 TWh, then Holtsville 0.088 and Hawkeye Greenport 0.075. That is
0.29 %/yr of measured NY energy and is **consistent with nyiso-172 S7's
population finding (off-model < 0.7 %)**, not a new object.

---

## 4. M3 / M5 — WHAT THE REPAIR MOVES

### 4.1 The correction, stated precisely

A unit keeps its prime-mover **family** (turbine-fired vs boiler-fired) and its
own plant's model roster picks the class inside that family
(`scripts/lib/campd_measured_classes.py`). Three properties make it a strict
**crosswalk repair** rather than a reclassification, and all three are unit
tested:

* wherever the `unitType` class is one the plant carries it is a **no-op** —
  units actually move at **three** plants only (2493, 2500, 2682), so
  **96.47 %** of measured NY energy (183.69 of 190.42 TWh over three years) is
  reproduced exactly;
* it **never crosses the turbine/boiler line**, so a genuine population gap
  (the four `CT_PEAKER`-at-a-steam-plant rows) stays visible as one instead of
  being absorbed into a neighbouring class;
* a plant absent from the model keeps its `unitType` class — the correction
  **never invents a bin**.

For East River: units 1/2 are turbine-family at a `{CT_CHP, ST_CHP}` plant →
**`CT_CHP`**; units 60/70 are boiler-family → **`ST_CHP`**, unchanged.

### 4.2 The C1 class volume errors do NOT move. Measured, not assumed

This is the load-bearing result of §4 and it was worth measuring rather than
asserting. Recomputing nyiso-169b measurement A reproduces its published
figures exactly:

| 2025 | CC_CHP | CC_REGULAR | CT_CHP | CT_PEAKER | ST_CHP | ST_GAS |
|---|---|---|---|---|---|---|
| model P1 TWh | 19.7268 | 35.6914 | 1.8261 | 1.0341 | 1.4919 | 9.7866 |
| bench `classFull` TWh | 16.9617 | 33.5445 | 2.3829 | 2.8512 | 0.7997 | 13.7121 |
| **Δ %** | **+16.30** | **+6.40** | −23.37 | **−63.73** | +86.55 | **−28.63** |

Both inputs are on the prime-mover basis — the keeper's P1 `class_hourly` from
the EIA-860 fleet, and `classFull` from `_classify_f923` →
`plant_taxonomy.classify_plant`. **The defective CAMPD construction never
entered a scored quantity.** So the repair moves **nothing** on C1, C3a or any
gate, and this session correctly registers no run.

### 4.3 nyiso-170 §3's CT_CHP identification blocker FLIPS

Anchor = bench grid-delivered TWh ÷ CEMS gross TWh, 2025:

| class | units old → new | CEMS gross old → new | bench | **anchor old → new** | nyiso-170 verdict |
|---|---|---|---|---|---|
| CC_CHP | 31 → 29 | 15.858 → 13.669 | 16.962 | 1.070 → **1.241** | "identifiable" — **now weaker** |
| CC_REGULAR | 37 → 36 | 33.992 → 33.921 | 33.544 | 0.987 → 0.989 | identifiable, unchanged |
| **CT_CHP** | **1 → 3** | **0.483 → 2.672** | 2.383 | **4.933 → 0.892** | **"NOT identifiable" — FLIPS** |
| CT_PEAKER | 112 → 113 | 1.904 → 1.975 | 2.851 | 1.498 → 1.444 | identifiable, unchanged |
| **ST_CHP** | 10 → 10 | **0.000 → 0.000** | 0.800 | — → — | **"NOT identifiable" — SURVIVES** |
| ST_GAS | 43 → 43 | 15.138 → 15.138 | 13.712 | 0.906 → 0.906 | identifiable, unchanged |

Three readings, in order of importance:

1. **CT_CHP becomes identifiable.** nyiso-170 §3 filed it as an identification
   blocker — "represented by a **single** unit carrying a fifth of its class's
   benchmark volume", anchor 4.933. With East River's two turbines correctly
   seated the class is 3 units at 2.672 TWh gross against a 2.383 TWh
   grid-delivered benchmark, anchor **0.892** — gross above delivered, the
   right side of 1, and in the same band as the four classes that session
   called identifiable. **A future NYISO lane MAY now identify CT_CHP hourly
   conduct from CAMPD.** That reverses a standing "the data does not exist"
   and is this session's headline flip.
2. **ST_CHP's blocker survives exactly.** East River's steam units are 2 of the
   5 CEMS-registered steam units at NY CHP plants nyiso-170 counted, and they
   report **0.000 TWh**. Corrected CEMS gross stays 0.000. nyiso-170 §3's
   ST_CHP conclusion — and, with it, its point 2 that nyiso-169b's ST_GAS
   figures stand unrepaired — is **untouched**.
3. **CC_CHP's own anchor gets WORSE**, 1.070 → 1.241. So nyiso-170's
   "CC_CHP, anchor 1.070, identifiable" was **partly an artifact of the
   defect**: on the corrected basis CEMS sees only 13.669 TWh of a 16.962 TWh
   grid-delivered class, a 19 % coverage gap. This does not overturn that
   session's conclusions (its gates J1–J4 ran on the admissible four and its
   kill was strengthened by the repair, not rescued), but the CC_CHP anchor
   should be quoted at 1.241 from here on.

### 4.4 nyiso-171's portfolio-artifact conclusion is STRENGTHENED to unanimity

nyiso-171 A3's stop condition asked whether the measured CC_CHP class floor is
per-plant physics or a portfolio statistic. Its committed answer: sum-of-plant
minima **0.0 / 81.0 / 85.0 MW** against fleet minima **282 / 368 / 184 MW**,
with **1 of 17** plants never off in 2024 and 2025 — **and that one plant was
East River**.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| plants, old → new | 17 → **16** | 17 → **16** | 17 → **16** |
| plants never off, old → new | 0 → **0** | **1 (2493)** → **0** | **1 (2493)** → **0** |
| Σ plant minima MW, old → new | 0.0 → **0.0** | 81.0 → **0.0** | 85.0 → **0.0** |
| fleet minimum MW, old → new | 282 → **182** | 368 → **277** | 184 → **81** |

**On the corrected construction every one of the 16 remaining CC_CHP plants
reaches zero, in every year, and the sum of their minima is exactly 0.0 MW —
while the class still never drops below 81–277 MW.** The residual class floor
is now demonstrably built **entirely** out of plants that each individually
shut down; it exists only because they are never all off at once. That is
precisely nyiso-171's claim, now holding **unanimously and exactly**, with its
single counter-example removed and the marginal 2024 case (which was the one
year meeting its 0.50 coverage threshold) resolved. Its rule 17
`[R-FLOOR-WINDOW]` conclusion — a per-plant `min_gen` would force machines to
run in hours their own meters say they were off — is **stronger**, not weaker.

### 4.5 nyiso-172 §3.4's bound grows ~60 %; nyiso-173's adjudication survives

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| violating hours, old → new | 93 → **219** | 773 → **1,523** | 1,211 → **1,926** |
| share of hours, old → new | 1.06 → **2.50 %** | 8.82 → **17.39 %** | 13.82 → **21.99 %** |
| mean (model − bound) MW, old → new | 266.4 → 282.0 | 228.3 → 381.9 | 416.0 → 562.5 |
| measured CC TWh, old → new | 45.976 → 43.801 | 51.327 → 49.049 | 49.850 → 47.590 |

Slightly larger than nyiso-173 P3's figures (208 / 1,500 / 1,864) because the
full correction also moves S A Carlson's 0.142 TWh out of `CC_REGULAR`;
nyiso-173 removed East River alone.

**nyiso-173's adjudication is unaffected, and this was already anticipated
there.** Its decisive S3 measurement — the model reaches its CC availability
envelope in **0 hours** of all three years and leaves **2,745 / 2,630 /
2,363 MW** of already-derated headroom unused in the violating hours — was
taken **"with and without East River"**, and 2.0–2.7 GW of unused envelope
dwarfs the bound's growth. The measured-availability-input family stays
**CLOSED**, on its stated re-open condition (a future keeper whose CC
utilisation actually reaches its envelope), and the object stays relocated to
the merit-order/economics lane. What changes is only the **magnitude** of the
symptom: nyiso-172 §3.4 should be quoted at 219 / 1,523 / 1,926 hours, still
**portfolio-only** (nyiso-173 P3: 0 hours above the additive per-plant bound in
every year).

---

## 5. M4 — RULE 19 `[R-ONE-MECH]` ENUMERATION for plant 2493

Every mechanism whose eligibility for this plant is keyed on `plant_group`,
read off the engine rather than off documentation:

| mechanism | reaches 2493? | which bin | note |
|---|---|---|---|
| `chp_steam` floor (`chp_pmin_cf = 30.0`) | **yes** | **`ST_CHP` only** | from the tranches row; there is **no `CT_CHP` tranches row**, so the turbine bin has no floor |
| unit-outage overlay (`campd_outage_windows`) | **yes** | **`ST_CHP`** | the extract tags **all four** units `plant_group = ST_CHP`, the two 180 MW GTs included; `_generic_unit_outage_target(2493, ·, "ST_CHP") → (2493, "ST_CHP")` |
| unit-outage overlay, CT path | **no** | — | `_generic_unit_outage_target` returns `None` for `CT_CHP`/`CT_PEAKER` by design ("combustion turbines dispatch economically"), so the 306 MW turbine bin takes **no outage derate at all** |
| `_FLEET_GROUP_OVERRIDE` | **no entry** | — | only `{2500: "ST_GAS"}`. **None is needed and none should be added**: the extract's `ST_CHP` tag routes to an *existing* bin, so this is not the Ravenswood delivery failure — it is mis-targeting *within* a mixed plant |
| `nyiso_gas_commitment_bridge` | **no** | — | gates on `CC_REGULAR` + `ST_GAS`; neither of this plant's bins qualifies |
| reliability-floor limbs | **no** | — | NYISO's are keyed `<ZONE>:<CLASS>:<driver>` on `ST_GAS`; the downstate `tmax` limbs are disabled anyway as the bridge's replacement (owner, 2026-07-27) |

**A reclassification would therefore have REPLACED the `chp_steam` floor's
target, not stacked on it** — but no reclassification is warranted, because the
model's classification is already correct.

The enumeration does surface **one genuine model-input defect**, which is
handed forward rather than repaired (§6 item 1): the outage extract routes the
two gas turbines' windows onto the steam bin.

---

## 6. Lines this session closes, and what is handed forward

### Closed

* **CLOSED — "which side of the East River crosswalk is wrong."** The CAMPD
  `unitType` construction is, on three independent primary records that agree
  (EIA-860 prime movers, EIA-923 Page-1, CAMPD's own measured heat rate and
  steam export) plus a fourth corroboration (the committed `classFull`
  benchmark already classes the plant `CT_CHP` + `ST_CHP`). **Do not re-open
  as a model-side defect.** The plant needs no per-unit override; the model
  already has the split.
* **CLOSED — "is this a systematic NYISO crosswalk defect?" NO.** One plant at
  97.8 % of the misclassed volume; every other misclassed plant together is
  0.148 TWh over three years (0.07 % of measured energy).
* **CLOSED — "does the repair move C1 / C3a?" NO, and not by inference.**
  nyiso-169b measurement A reproduces exactly on both bases because neither of
  its inputs ever used the defective construction. **Do not re-open the East
  River crosswalk as a C3a-2025 lever.**
* **FLIPPED — nyiso-170 §3's `CT_CHP` identification blocker.** Anchor
  4.933 → **0.892** on 1 → 3 units. CT_CHP hourly conduct **is** identifiable
  from CAMPD; that session's "the data does not exist" applies to **ST_CHP
  only**, which survives at 0.000 TWh.
* **AMENDED — nyiso-170 §3's `CC_CHP` anchor**, 1.070 → **1.241**: partly an
  artifact of the defect. Quote 1.241.
* **STRENGTHENED — nyiso-171's portfolio-artifact conclusion**, to
  sum-of-plant-minima **0.0 MW and 0 plants never off in all three years**.
* **RESTATED — nyiso-172 §3.4's bound**, to **219 / 1,523 / 1,926** hours
  (2.50 / 17.39 / 21.99 %), still portfolio-only per nyiso-173 P3.
* **NOT RE-OPENED — the twenty-three closed lines** carried into this session,
  and **no C3c lever was opened**.
* **NOT OPENED — any parameter, band, floor or offer change.** No arm was
  pre-registered and no solve was run, because §4.2 establishes there is
  nothing model-side to repair. Manufacturing an arm here would have been the
  trap the brief named.

### Handed forward

1. **A real, zero-DOF model-input defect: the outage extract routes East
   River's two gas turbines onto its steam bin.** `_resolve_unit_group`
   (`scripts/data/derive_campd_unit_outages.py:622`) short-circuits on
   `fac_group` — the plant's group under a **last-writer-wins** dict over the
   fleet iteration, which for 2493 resolves to `ST_CHP` — before it ever
   consults the unit's own `unitType`. So units 1 and 2, EIA-860 `GT`, are
   written to the extract as `plant_group = ST_CHP` and their windows derate
   the 309.5 MW steam bin. This is the **same short-circuit** the docstring
   itself calls "a deliberate pjm-75 conservatism rather than a physical claim"
   and that neiso-99 already had to carve a rule 14 `[R-ACCURATE]` exception
   out of. **Size in the training window is small: two windows, both in 2023**
   (unit 1, 33.5 d from 2023-09-15; unit 2, 18.5 d from 2023-10-21), at 26.9 %
   of plant capacity each; units 60/70's 26 windows are correctly on the steam
   bin. **Not repaired here** on three grounds: it is solve-affecting and would
   need a full three-year re-solve to register; its direction makes the steam
   bin **more** available, which deepens the model's largest CHP error rather
   than closing it; and it sits inside the unresolved object below, which
   should be settled before its input is touched.
2. **The successor object: which half of East River carries the must-run.**
   The model floors the **steam** bin (`chp_pmin_cf = 30.0` on 309.5 MW =
   92.85 MW) and leaves the **turbine** bin unfloored and un-derated. The
   market's must-run is measurably in the **turbine** half: units 1/2 ran
   7,183–7,698 h each in 2025 and the plant never fell below **85 MW**, while
   units 60/70 generated **0.000 TWh**. The C1 signature matches — 2025
   `ST_CHP` **+86.55 %** over-run against `CT_CHP` **−23.37 %** under-run, with
   East River **65.8 %** of the model's whole `ST_CHP` capacity (309.5 of
   470.1 MW) and **68.6 %** of its whole `CT_CHP` (306.0 of 445.9 MW). Also
   missing: the plant has **no `CT_CHP` row in `thermal_tranches_NYISO.csv`**
   at all. **This is a named object, not a proposal**, and it is explicitly
   **blocked from resolution on committed artifacts** by item 3.
3. **A diagnostics-integrity limit, larger than the one recorded.** The brief
   carried forward a D-2 denominator basis mismatch on `ST_GAS` (ratio
   1.19/1.24/1.27). The same mismatch on the CHP classes is **an order of
   magnitude worse and two-sided**: D-2's `class_total_twh` reads `ST_CHP`
   0.0712 / 0.0913 / 0.0931 against the P1 `class_hourly` sidecar's 1.196 /
   1.185 / 1.492 — a factor of **13–17×** — and `CT_CHP` 2.898 / 2.448 / 3.300
   against 1.765 / 1.328 / 1.826, in the **opposite** direction, while the two
   artifacts **agree on the CT_CHP + ST_CHP total to within 2.2 %** in every
   year. The two artifacts therefore disagree about the model's own turbine/
   steam split at exactly the plant this session is about, which is why item 2
   cannot be settled without either a zone/plant-resolved sidecar or a re-solve.
   D-2's ST_CHP `share_of_class` is consequently **> 1** (2.847 in 2024, 1.795
   in 2025), which is a live hazard for the rule 20 `[R-FORCED-BUDGET]` gate.
   **Recorded, not scoped** — a diagnostics-integrity lane, as the brief
   directs.
4. **The model's East River heat rate, recorded and NOT proposed.** All four
   model units carry `heat_rate = 7.4205` (the `bin_assignments` plant average),
   while the two turbine stacks measure **10.51–10.89** with zero steam export.
   That would place 306 MW of in-city NYC capacity ~31 % cheaper than its meters
   say, in the merit-order lane the CC over-run object was relocated to. It is
   recorded rather than proposed because the correct electric heat rate for a
   cogen is a **fuel-allocation** question (the plant's 36.3 TBtu of 2023 fuel
   also produced 9.4 million klb of district steam, all of it metered at units
   60/70), and because item 3 blocks the model-side check. `measured_chp_heat_rates`
   is `K` on the matrix; this is a note on its per-plant allocation, not a
   challenge to the mechanism.
5. **S A Carlson (2682) is confirmed in the same family and sized**: 0.142 TWh
   over 2023–2025, `CC_REGULAR`-tagged extract rows at a `{CT_PEAKER, ST_GAS}`
   plant, the 87 MW `_FLEET_GROUP_OVERRIDE` class nyiso-173 S1 named. The
   corrected construction seats it on `CT_PEAKER`; the **outage-extract** side
   of it is unrepaired, alongside item 1.

---

## 7. Honest expected value

**What is delivered.** A reproducible, zero-solve adjudication that (a)
**answers the brief's phase-0 question on the primary record rather than the
residual**, with three independent sources agreeing and a fourth — the
committed benchmark — corroborating, and with the measured heat rate refuting
the very label the defect rests on; (b) **answers "one plant or systematic?"
decisively**, at 97.8 % of the misclassed volume, so no successor has to open a
fleet-wide crosswalk lane; (c) **measures, rather than assumes, that the defect
never reached a scored quantity**, which is what makes "no arm, no solve" the
correct outcome instead of a punt; (d) **flips a standing identification
blocker** — CT_CHP conduct is now identifiable from CAMPD, reopening an
instrument three sessions were told did not exist; (e) **strengthens nyiso-171
to unanimity and restates nyiso-172 §3.4 at ~60 % larger**, both with the old
basis reproduced exactly first, so the restatements are verified rather than
asserted; and (f) leaves behind a **tested shared helper** so the defective
construction cannot be re-introduced by session 175+.

**What is NOT delivered, plainly.** **No movement on C3a-2025, and none was
available.** The brief said not to expect this session to close it, and §4.2 is
the measurement that explains why the East River lane never could: the scored
comparison was already on the correct basis. The gain law, the 55 %-vs-118 %
non-physical steepness deficit and the $27.79–$56.03/MWh pass window are
exactly where nyiso-168 left them. **No solve was run and no run was
registered** — correct under rule 15, not an omission.

**What a successor should NOT do with this.** Do not re-open the East River
crosswalk; it is closed on the primary record in both directions. Do not treat
item 6.1 (the outage-extract routing) as a C3a lever — it is a correctness
repair worth ~2 windows in one training year, and its direction points away
from the model's largest CHP error. Do not attempt item 6.2 (which half carries
the must-run) from committed artifacts until item 6.3 is resolved: **D-2 and
`class_hourly` disagree about the model's own turbine/steam split by 13–17×**,
so any model-side reading of that object is currently unidentified.

---

## 8. Evidence

* `scripts/probes/nyiso174_class_crosswalk_audit.py` — M1–M5, zero solve
* `results/calibration/_nyiso174_class_crosswalk_audit.json` — full output
* `scripts/lib/campd_measured_classes.py` — the corrected construction
* `tests/unit/data/test_campd_measured_classes.py` — 19 tests, crosswalk-repair
  properties
* Prior: `docs/FINDING-nyiso173-cc-availability-envelope-not-binding-2026-09-02.md`
  §2.5, §5 · `docs/FINDING-nyiso172-st-gas-response-deficit-2026-09-01.md`
  §3.4, §5 · `docs/FINDING-nyiso171-chp-floor-portfolio-artifact-2026-09-01.md`
  §2.3, §5 · `docs/FINDING-nyiso170-merit-order-displacement-2026-09-01.md` §3 ·
  `docs/FINDING-nyiso168-supply-curve-slope-anatomy-2026-09-01.md` §4
