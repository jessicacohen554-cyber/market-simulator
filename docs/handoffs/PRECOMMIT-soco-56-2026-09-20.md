# PRECOMMIT — SOCO-56 (2026-09-20): the model is physically forbidden from reproducing Barry's measured output, and the cause is a unit→class misrouting in the outage overlay

**Lane** SOCO-56 · **DATA PROFILE** soco · **Control of record** `2026-09-20-soco55-peryear-gas-basis`
(bundle `results/calibration/soco55_peryear_basis`, rule 29 `[R-SCREEN]` (b) form 4).

Written BEFORE any LP. Every number below is zero-LP: a `fleet_only` rebuild off the keeper's own
`meta.json`, the committed/recovered hourly sidecars, the CAMPD unit extract, and EIA-860.

---

## 1. THE HANDOFF'S LEAD LEVER IS REFUSED ON MEASUREMENT, EX ANTE

The handoff routed this lane at the `CT_PEAKER` / `COAL_PRB` merit order that SOCO-55 §5 named, and
required that phase 0 confirm or refute that reading at 2024 grain. **It refutes it as the cause of
the 2024 `CC_REGULAR` failure**, and the refusal is arithmetic, not judgement.

**(a) 2024 `CC_REGULAR` IS NOT MARGINAL ENERGY. IT IS CAPACITY-BOUND.**

| measurement (2024, P1, keeper's own `unit_hourly`) | value |
|---|---|
| CC_REGULAR energy produced **at full availability** | **112.028 of 112.414 TWh = 99.66 %** |
| CC_REGULAR unit-hours at cap | 505,457 of 586,920 = **86.1 %** |
| CC_REGULAR **total** idle headroom, whole year | **5.268 TWh** |
| fleet-median CC `mc` vs the clearing price | **$22.60 vs $29.60 — $7.00/MWh BELOW** |
| hours the cheapest **idle** `COAL_PRB` is cheaper than the marginal running CC | **0 of 8,760** |
| hours the cheapest **idle** `ST_GAS` is cheaper than the marginal running CC | **0 of 8,760** |
| mean $/MWh gap, cheapest idle COAL_PRB − marginal CC | **+7.04** (ST_GAS **+8.15**) |

**(b) THE DISTANCE, IN $/MWh AND TWh-IN-REACH.** The reallocation the C1 rows ask for is
`COAL_PRB` +4.140 and `ST_GAS` +5.319 = **9.46 TWh**. Idle headroom within a given distance
**above** the clearing price:

| class | ≤ $1 | ≤ $2 | ≤ $5 | ≤ $10 |
|---|---|---|---|---|
| `COAL_PRB` | 0.887 | 2.181 | 3.642 | 8.453 |
| `ST_GAS` | 1.802 | 2.855 | 4.974 | 8.962 |
| **coal+steam together** | **2.689** | **5.036** | **8.616** | 17.415 |
| `CT_PEAKER` *(already **+4.287 TWh OVER**)* | 5.479 | 9.083 | **20.594** | 42.781 |

Closing 9.46 TWh needs roughly **$5/MWh** of merit-order movement — and the same $5 band holds
**20.594 TWh of `CT_PEAKER` headroom on a class already 1.9× its actual**. No offer-surface lever
crosses that distance without making `CT_PEAKER` worse than it fixes coal. **Refused ex ante**, the
way SOCO-54 §2 refused three commitment levers.

**(c) THE HANDOFF'S LEVER (3), parasitic load, is refused ON SIGN exactly as the handoff predicted**
— a heat rate biased low makes coal look cheaper, so correcting it moves coal DOWN, and 2024
`COAL_PRB` is already 4.140 TWh short. Two further sign-refusals found and recorded here so a
successor does not spend a solve on them: **`coal_takeorpay_from_data`** makes the coal must-run
tranche bid its *non-contracted* share at full delivered cost, i.e. coal gets MORE expensive (wrong
sign), and **`coal_fuel_inventory`** is a monthly **CEILING** on coal energy (wrong sign). Neither is
taken. *(`coal_takeorpay_SOCO.csv` does not exist; eight other ISOs have one. Reported, not taken.)*

**(d) WHAT THE HANDOFF'S READING *IS* RIGHT ABOUT.** The merchant `CT_PEAKER` over-run is real and
large — 55061 Tenaska Georgia **2.327 TWh model vs 0.037 actual (63×)**, 55128 Walton County 3.6×,
55409 Calhoun 3.6×, 55267 Addison 2.6× — while Southern-contracted peakers run at 18–29 % of theirs
(Hawk Road 0.169/0.701, Talbot 0.095/0.529, Sewell Creek 0.160/0.552). It is simply **not what makes
2024 `CC_REGULAR` fail**, and it is not a merit-order problem in a class that is 99.66 % at cap.

---

## 2. WHAT PHASE 0 FOUND INSTEAD — AND IT IS A DATA DEFECT, NOT A PRICE ONE

**The 2024 `CC_REGULAR` class total of +7.505 TWh is the NET of a ~12 TWh gross misallocation.**
Southern-owned CCs run far UNDER their measured output while merchant/IPP CCs run at ~100 % of their
availability. Per plant, 2024, model vs the bench's own CAMPD series:

| plant | model | **actual** | ratio | `util_of_avail` |
|---|---|---|---|---|
| **3 Barry** | 6.536 | **13.361** | **0.49** | 0.785 |
| 56 Lowman | 2.767 | 4.343 | 0.64 | 0.668 |
| 6073 Daniel | 6.855 | 8.196 | 0.84 | 0.884 |
| 710 McDonough | 17.369 | 18.186 | 0.96 | 1.000 |
| — | | | | |
| 55271 Tenaska Lindsay Hill | 4.391 | 1.795 | **2.45** | 0.999 |
| 7897 E B Harris | 6.991 | 5.080 | 1.38 | 1.000 |
| 57037 Ratcliffe | 6.057 | 4.305 | 1.41 | 0.985 |
| 55440 Central Alabama | 5.082 | 3.587 | 1.42 | 0.969 |
| 7946 Wansley 9 | 3.508 | 2.307 | 1.52 | 1.000 |
| 533 McWilliams | 3.162 | 2.020 | 1.57 | 0.806 |

**THE CONTRADICTION TEST.** Hours in which the model's own availability ceiling is **below the same
plant's measured CAMPD output in that very hour** — i.e. output the model is physically forbidden
from producing:

| plant | 2023 | 2024 | 2025 | 2024 hours | 2024 max MW |
|---|---|---|---|---|---|
| **3 Barry (CC_REGULAR)** | **5.031** | **5.080** | **4.598** | **8,548 of 8,760 (97.6 %)** | **1,513** |
| 710 McDonough | 1.442 | 1.528 | 1.174 | 5,944 | 758 |
| 6002 James H Miller | 0.893 | 1.217 | 1.845 | 4,646 | 902 |
| *(every other plant)* | ≤ 0.95 | ≤ 0.91 | ≤ 0.89 | | |

The broad fleet-wide residue is the CAMPD-gross vs model-net-summer wedge (`npl_model` is
systematically 88–94 % of `npl_bench`). **Barry is categorically different**: 3–4× the next plant, at
1.5 GW, in 94–99.6 % of the hours of every year. Its availability p50 is **1,028 MW against a
measured output p50 of 1,624 MW**; it reaches full capacity in **144 hours** against 1,800–2,160 for
every peer; `cap_p95` is 77 % of its own `cap_max` where every peer's is 100 %.

**THE CAUSE, TRACED TO PRIMARY SOURCES — NOT INFERRED.** `data/raw/campd-unit-outages-SOCO.csv`
routes **Barry units 1, 2 and 4 to `plant_group = CC_REGULAR`**:

| unit | CAMPD `unitType` | CAMPD `primaryFuelInfo` | EIA-860 Technology | extract routes to | 2024 days "out" of 366 |
|---|---|---|---|---|---|
| 1 | **Tangentially-fired** | Pipeline Natural Gas | Natural Gas Steam Turbine (ST) | `CC_REGULAR` | **342** |
| 2 | **Tangentially-fired** | Pipeline Natural Gas | Natural Gas Steam Turbine (ST) | `CC_REGULAR` | **353** |
| 4 | **Tangentially-fired** | Pipeline Natural Gas | Conventional Steam Coal (ST) | `CC_REGULAR` | **298** |
| 5 | Tangentially-fired | Coal | Conventional Steam Coal | `COAL` ✓ | 284 |
| 6A/6B/7A/7B/8 | **Combined cycle** | Pipeline Natural Gas | NG Fired Combined Cycle | `CC_REGULAR` ✓ | 6–29 |

Units 1, 2 and 4 are **boilers**, measurably — CAMPD files them `Tangentially-fired`, never
`Combined cycle`. They are mostly idle (17 / 10 / 152 GWh in 519 / 303 / 1,539 hours of 2024), and
**their idleness is charged as a forced outage on Barry's combined-cycle block**: 4.4 + 4.4 + 11.5 =
**20.3 pp of spurious derate for ~300–350 days of 366**. This is the deriver's plant-level
`fac_group` short-circuit at a facility carrying THREE model bins — **the identical defect already
adjudicated at pjm-75 (Chesterfield 3797, 1,036 MW of retiring coal tagged `CC_REGULAR`, ~2.35 TWh)
and miso-200 (Ninemile Point 1403, two gas-steam boilers dumped on a 649.5 MW CC bin)**, whose own
docstring in `scripts/data/derive_campd_unit_outages.py` names it.

**THE HANDOFF'S OPEN ITEM "Barry unit 4 — a 362 MW COAL model row CAMPD files as Pipeline Natural
Gas" IS RESOLVED IN FAVOUR OF CAMPD.** The unit measurably burns gas (152.02 GWh, `primaryFuelInfo =
Pipeline Natural Gas`, 2024); EIA-860's `Energy Source 1 = BIT` is stale. That the model's *fleet*
still carries unit 4 inside `COAL_BIT` is a separate, smaller defect and is **ROUTED, not taken**.

---

## 3. THE ARM — ONE EXISTING GATE, ZERO FREE PARAMETERS, TWO KEYS MOVED

`campd_per_unit_attribution = True` (cell **`U`** in SOCO's shard — not adjudicated `R`/`I`/`G`, so
rule 28 `[R-MECH-MATRIX]` (a)'s DO-NOT-REDO discipline is clear). It selects the `-perunit-`
companion extract, in which every unit routes by the shared `scripts/lib/campd_measured_classes`
crosswalk rather than by the plant-level `fac_group` short-circuit.

**The artifact was derived in this session, from SOCO's own CAMPD and EIA-860** —
`scripts/data/derive_campd_unit_outages.py --iso SOCO --years 2023 2024 2025 --per-unit-crosswalk`
→ `data/raw/campd-unit-outages-perunit-SOCO.csv`. **Rule 25 `[R-ISO-SCOPE]` / 28(d): NYISO's verdict
transfers to nothing; SOCO's parameters come from SOCO's own market's data.**

**BLAST RADIUS, MEASURED:** of **1,119** extract rows, **48 change routing, all at facility 3**, and
the changed set is **exactly units 1, 2 and 4** (`CC_REGULAR` → `ST_GAS`). Every other SOCO unit is
unchanged.

### 3.1 Rule 19 `[R-ONE-MECH]`, mechanically, at THREE grains, BEFORE the solve

`fleet_only` rebuild off the keeper's own `meta.json`, `--set campd_per_unit_attribution=true`:

| year | `fuel_prices` global max\|Δ\| | `mc_base` global max\|Δ\| | `availability` keys moved |
|---|---|---|---|
| 2023 | **0.000000000000** | **0.000000000000** | **2 of 128** |
| 2024 | **0.000000000000** | **0.000000000000** | **2 of 128** |
| 2025 | **0.000000000000** | **0.000000000000** | **2 of 91** |

Both moved keys are plant 3 in every year. This is a pure availability repair; it touches no price,
no heat rate, no fuel, no offer curve, and no other plant.

| year | (3, `CC_REGULAR`) mean avail | (3, `ST_GAS`) mean avail |
|---|---|---|
| 2023 | 0.1426 → **0.2803** (+0.1377) | 0.8130 → 0.0330 |
| 2024 | 0.5217 → **0.8369** (+0.3152) | 0.8130 → 0.0140 |
| 2025 | 0.5072 → **0.7901** (+0.2830) | 0.8130 → 0.0220 |

### 3.2 THE STRUCTURAL SIGNATURE — and it is NOT a fit

| year | keeper Barry CC available | **arm available** | **measured output** | arm − measured |
|---|---|---|---|---|
| 2023 | 2.275 | 4.471 | 7.303 | **−2.83 (still far short)** |
| 2024 | 8.323 | **13.352** | **13.361** | **−0.009 (0.07 %)** |
| 2025 | 8.091 | **12.604** | **12.566** | **+0.038 (0.30 %)** |

2024 and 2025 land on the measured output to within a third of a percent. **2023 deliberately does
NOT** — because Barry unit 8's 345-day commissioning outage in 2023 is a GENUINE CC outage and the
repair correctly leaves it in the `CC_REGULAR` bin. A mechanism that repaired 2023 to its actual too
would be a fit; this one does not, and that asymmetry is its signature.

### 3.3 THE COST, STATED AT THE GATE RATHER THAN LEFT TO BE DISCOVERED

The three re-routed units (709.9 MW) land on Barry's `ST_GAS` bin, whose EIA-860 nameplate basis
(306.2 MW) is smaller, so the removed share clips and that bin's availability collapses to ~0.02.
**That is a NEW over-derate and I am not hiding it.** Its cost is bounded by measurement:

| year | Barry `ST_GAS` model energy | hours `price > mc` | bound on the loss |
|---|---|---|---|
| 2023 | 2.349 GWh | 18 of 8,760 | **≤ 0.0023 TWh** |
| 2024 | 0.000 GWh | 3 of 8,760 | **0.0000 TWh** |
| 2025 | 7.149 GWh | 88 of 8,760 | **≤ 0.0071 TWh** |

≤ 0.18 % of the `ST_GAS` class in the worst year. Rule 17: plant 3's campaign-floor share is
**0.000 with a 0.0632 margin in all three years** — the floor never binds at Barry, so the collapse
costs no forced energy either. The correct repair for the denominator is
`unit_outage_extract_basis_share` (nyiso-196) or `unit_outage_st_capacity_basis`; arming either here
would be a SECOND mechanism on the same object and is **ROUTED, not stacked** (rule 19).

---

## 4. EX ANTE PREDICTIONS — AND THE ARM IS AGAINST THE LANE'S OWN OBJECT

Zero-LP greedy re-stack: Barry takes its repaired availability in every hour it is in merit; the most
expensive dispatched non-fixed MW is displaced. Prices are held FIXED, so this is a bound, not a
solve — the LP will re-price downward, which displaces more. **Second-order classes are banded wide
and floor/forcing DIRECTION is deliberately not predicted** (the SOCO-55 lesson).

| # | prediction | falsifier |
|---|---|---|
| **P1** | **2024 `CC_REGULAR` gets WORSE and STILL FAILS.** Point **+2.9 TWh**, band **+1.5 to +4.5** → 112.414 → **113.9–116.9**, i.e. Δ **+9.0 to +12.0** against a ±7.47 band | a move outside +1.5…+4.5, or the row PASSING |
| **P2** | 2024 `CC_REGULAR` now fails the **SHARE** leg too (+2.81pp → **>3.00pp**), so it fails BOTH legs | share stays ≤ 3.00pp |
| **P3** | **determination stays `NOT-YET`; C1 stays 13/14**; no OTHER class changes status in 2023 or 2024 | any second row flipping |
| **P4** | 2024 `CT_PEAKER` **IMPROVES**: −1.5 TWh, band −0.7 to −2.5 → Δ +4.287 → **+1.8 to +3.6** | outside the band, or worsening |
| **P5** | 2024 `ST_GAS` worsens −0.9 TWh, band **−0.3 to −1.6**; stays PASS | outside band, or FAIL |
| **P6** | 2024 `COAL_PRB` worsens −0.5 TWh, band **−0.1 to −1.2**; stays PASS | outside band, or FAIL |
| **P7** | **2023 `CT_PEAKER` — THE LANE'S THINNEST ROW (0.13pp of a ±3.00pp cap) GETS SAFER, NOT THINNER.** −0.6 TWh, band −0.2 to −1.3; share +2.87pp → **2.4–2.8pp** | the share RISING, or the row flipping to FAIL |
| **P8** | 2023 `CC_REGULAR` +1.2 TWh, band +0.5 to +2.2 → Δ +4.352 → **+4.9 to +6.6**; **stays PASS** on a ~7.18 band | outside band, or FAIL |
| **P9** | Barry (plant 3) CC goes 6.536 → **10.6 TWh**, band **9.5–13.4**, against a 13.361 actual — ratio 0.49 → **0.71–1.00** | outside the band |
| **P10** | **2025 is NOT byte-identical** (unlike SOCO-55's 2024): every 2025 artifact differs, and the 8,930.2 MWh of VOLL slack **falls** | 2025 identical, or slack rising |
| **P11** | rule 17 `[R-FLOOR-WINDOW]` holds in all fifteen plant-years; **plant 3 stays at 0.000 share**; **direction at plants 10/26/728/2049 deliberately UNPREDICTED** | any plant-year with negative margin |
| **P12** | C8 forced share stays under the 0.30 merchant cap; **direction UNPREDICTED** | any class over cap |
| **P13** | C2 / C4 / C6 PASS; **0 ledgered, 0 protective**; C3a/b/c UNSCORABLE | any change |
| **P14** | DOF: **zero new free parameters**, `n_residual` unchanged at **1** | any new residual-identified value |
| **P15** | **no peer ISO moves and no pre-existing cache key moves** — `campd_per_unit_attribution` is already in `_CACHE_KEY_OPTIONAL_FIELDS` at `"False"`, and the `-perunit-SOCO` artifact is a NEW file no other ISO reads | any non-SOCO key moving |

**I AM PREDICTING THAT MY OWN ARM MAKES THIS LANE'S TARGET ROW WORSE, AND I AM TAKING IT ANYWAY.**
Rule 14 `[R-ACCURATE]` is the governing text — *"if swapping a hand estimate for real data makes the
backcast worse, that is a signal that something else in the model is miscalibrated and the estimate
was silently compensating for it… keep the accurate input, find and fix the real root cause"* — and
rule 1 `[R-STRUCT]` forbids rejecting a structurally-correct mechanism because the residual moved the
wrong way. A model that is **physically forbidden from reproducing a 1.8 GW plant's measured output
in 97.6 % of the year** is not modelling that plant, whatever the class total reads.

**WHAT IT BUYS, WHICH IS THE POINT.** Barry's spurious outage was **silently compensating for a real
merchant-CC over-dispatch**. Remove it and ~4 TWh of that over-run is exposed at full size, attributed
at plant grain to units running at ~100 % of availability against measured CFs of 0.22–0.59.
**That is the named successor object.** It also matters for the FORECAST: a forecast year carries no
CAMPD outage overlay at all, so the compensation is not there — the backcast's flattering CC number
is a backcast-only artifact, and the forecast already carries the full error.

---

## 5. G-DRIFT (rule 29 `[R-SCREEN]` (b) form 4)

The control is the keeper's **committed** bundle. No control solve. Its per-plant layer was recovered
at zero LP by `git fetch origin <40-char-sha>` on the SOCO-55 leg SHAs (`95f81a8c…`, `ef1d35bc…`,
`a16b676b…`), and all **twelve** committed hourly sidecars verify **byte-identical** to the recovered
legs, with the recipe signature read back from `run_config.json`
(`gas_plant_monthly_fuel_pricing=false`, `gas_basis_differential_measured_by_year=true`,
`coal_prb_sigmoid_overrides` absent/null). HEAD `eb56d7eb` is the SOCO-55 merge itself, so there is
no solve-path drift between the keeper's `git_sha` and this lane's pin beyond that merge.

## 6. SOLVE SHAPE

Rule 36 `[R-YEAR-ISOLATION]` (a): **one shard per year**, 2023 / 2024 / 2025, each `--years <one>`,
composed in the parent at zero LP with `scripts/probes/soco55_compose_span.py`. Each shard pushes its
**full 16-file bundle** including `dispatch/<y>_P1.parquet` and the bundle-root `system.parquet`
(rule 34 `[R-SHARD-PROMOTABLE]` (a)). SOCO solves in ~110 s/year at ~2.6 GiB.

## 7. GATE NOISE EXPECTED, NOT CHASED

`audit_keepers` **E13** for `2026-09-20-soco53g-prb-own-iso` (ninth consecutive firing — rule 31
forbids deleting it, rule 30(a) forbids stamping it; **RE-RAISED to the owner**); **E11** lineage
diff not computable after the SOCO-55 prune; **E5** unsatisfiable for a price-unscored ISO
(`_DET_TOKENS` has no `PHYSICALLY-CALIBRATED` entry — sidecar definitions stay RECIPE-ONLY, ROUTED);
`check_cache_key_registration` RED at HEAD for `PPA_COST_RECOVERY_YR` / `REGIONAL_RENEWABLE_CF`
(commit `3fc20b97`, **not this lane's**); `check_registry_payload_parity` RED locally for this lane's
own gitignored leg bundles (rule 31's 2026-09-16 correction) and for
`results/calibration/nwpp44_takeorpay_2025` (NWPP-44's, `ee276d87`, **not this lane's**);
`tests/unit/config/test_data_profiles_tokens.py::test_soco_token_collides_with_no_other_raw_name`
RED at HEAD (a SOCO-desk naming decision).

## 8. GATE G17 — SOCO HAS NO PRICE BENCHMARK AND GAINS NONE

`actual_lmp.json` gets **no SOCO block**. C3a/C3b/C3c stay UNSCORABLE. Every `offer_curve_by_group`
band stays **1.0**; there is **no `authorized_price_tuning` key** in the attestation's governance
block, and declared-NONE goes in `attested_by` prose. No SOCO run is cited as
`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`.
