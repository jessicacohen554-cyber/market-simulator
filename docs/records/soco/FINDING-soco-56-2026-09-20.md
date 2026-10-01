# FINDING — SOCO-56 (2026-09-20): the model is physically forbidden from reproducing Barry's measured output, the cause is three misrouted boilers in the outage extract, and repairing it makes the lane's own target row worse

**Lane** SOCO-56 · **DATA PROFILE** soco · **Model** Opus 5 (rule 27 — scope touches `src/`-adjacent
config reads and `scripts/`).
**Control of record** `2026-09-20-soco55-peryear-gas-basis`, rule 29 `[R-SCREEN]` (b) **form 4**, no
control solve.
**Arm** `2026-09-20-soco56-perunit-outage` (`results/calibration/soco56_perunit_outage`), registered
2026-09-20. **PROMOTION OPEN AND THE OWNER'S** — see §11.

---

## 1. HEADLINE

**Two results, and the first one is a data decision this desk owed rather than a lever.**

### (1) THE HANDOFF'S LEAD LEVER IS REFUSED ON MEASUREMENT, BEFORE ANY LP

The handoff routed this lane at the `CT_PEAKER` / `COAL_PRB` merit order SOCO-55 §5 named, and asked
phase 0 to **confirm or refute that reading at 2024 grain**. It **refutes it as the cause of the 2024
`CC_REGULAR` failure**, arithmetically:

> **2024 `CC_REGULAR` IS NOT MARGINAL ENERGY. 112.028 of its 112.414 TWh — 99.66 % — is produced AT
> FULL AVAILABILITY.** In **zero of 8,760 hours** is the cheapest *idle* `COAL_PRB` or `ST_GAS` unit
> cheaper than the marginal *running* CC. The fleet-median CC `mc` sits **$7.00/MWh BELOW** the
> clearing price.

### (2) WHAT PHASE 0 FOUND INSTEAD IS A TRACED DATA DEFECT, AND REPAIRING IT MAKES 2024 WORSE

> **Barry units 1, 2 and 4 are gas-fired BOILERS that the outage extract routes to `CC_REGULAR`.**
> CAMPD files all three as `unitType` **"Tangentially-fired"**, never "Combined cycle". They are
> mostly idle, and their idleness is charged as a **20.3 pp forced outage on Barry's combined-cycle
> block for 342 / 353 / 298 days of 366** — so **the model's availability ceiling sits BELOW the
> plant's own measured CAMPD output in 8,548 of 8,760 hours of 2024**, by up to **1,513 MW and
> 5.080 TWh**.

Repairing it **raises** `CC_REGULAR`, so the lane's own target row goes **+7.505 → +10.178 TWh** of a
±7.466 band and now fails **both** legs where the keeper failed one. `PRECOMMIT-soco-56` §4 **P1 and
P2 pre-registered exactly that**, from a zero-LP greedy re-stack, before the solve. **All fifteen
pre-registered predictions held.** The input is kept anyway, under rules 1 `[R-STRUCT]` and 14
`[R-ACCURATE]`.

---

## 2. THE REFUSAL, IN $/MWh AND TWh-IN-REACH (zero LP, on the control's own committed hourlies)

**(a) The class is capacity-bound, not price-marginal.**

| measurement (2024, P1) | value |
|---|---|
| `CC_REGULAR` energy produced at full availability | **112.028 of 112.414 TWh = 99.66 %** |
| `CC_REGULAR` unit-hours at cap | 505,457 of 586,920 = **86.1 %** |
| `CC_REGULAR` idle headroom, whole year | **5.268 TWh** |
| fleet-median CC `mc` vs clearing price | **$22.60 vs $29.60 — $7.00/MWh below** |
| hours cheapest idle `COAL_PRB` < marginal running CC | **0 of 8,760** (mean gap **+7.04 $/MWh**) |
| hours cheapest idle `ST_GAS` < marginal running CC | **0 of 8,760** (mean gap **+8.15 $/MWh**) |

**(b) The distance no offer-surface lever crosses.** The C1 rows ask for `COAL_PRB` +4.140 and
`ST_GAS` +5.319 = **9.46 TWh**. Idle headroom within a given distance **above** the clearing price:

| class | ≤ $1 | ≤ $2 | ≤ $5 | ≤ $10 |
|---|---|---|---|---|
| `COAL_PRB` | 0.887 | 2.181 | 3.642 | 8.453 |
| `ST_GAS` | 1.802 | 2.855 | 4.974 | 8.962 |
| **coal + steam** | **2.689** | **5.036** | **8.616** | 17.415 |
| `CT_PEAKER` *(already **+4.287 TWh OVER**)* | 5.479 | 9.083 | **20.594** | 42.781 |

≈**$5/MWh** of merit-order movement is needed, and the same $5 band holds **20.594 TWh of
`CT_PEAKER` headroom on a class already 1.9× its actual**. **Refused ex ante**, as SOCO-54 §2 refused
three commitment levers.

**(c) Three more levers refused ON SIGN, recorded so no successor spends a solve on them.**
The handoff's own parasitic-load item (a heat rate biased low makes coal look *cheaper*, so correcting
it moves coal **down**, and 2024 `COAL_PRB` is already 4.140 TWh short); **`coal_takeorpay_from_data`**
(the coal must-run tranche bids its non-contracted share at full delivered cost — coal gets **more**
expensive); **`coal_fuel_inventory`** (a monthly **CEILING** on coal energy). All three are the wrong
direction. *`coal_takeorpay_SOCO.csv` does not exist; eight other ISOs have one. Reported, not taken.*

**(d) What the handoff's reading IS right about.** The merchant `CT_PEAKER` over-run is real and
large — 55061 Tenaska Georgia 2.327 TWh model vs **0.037** actual (63×), 55128 Walton County 3.6×,
55409 Calhoun 3.6×, 55267 Addison 2.6× — while Southern-contracted peakers run at 18–29 % of theirs.
It is simply **not what makes 2024 `CC_REGULAR` fail**, and it is not a merit-order problem in a class
that is 99.66 % at cap.

---

## 3. THE DEFECT, TRACED TO PRIMARY SOURCES

**The contradiction test** — hours in which the model's availability ceiling is **below the same
plant's measured CAMPD output in that very hour**, i.e. output the model is forbidden from producing:

| plant | 2023 | 2024 | 2025 | 2024 hours | 2024 max MW |
|---|---|---|---|---|---|
| **3 Barry (`CC_REGULAR`)** | **5.031** | **5.080** | **4.598** | **8,548 of 8,760 (97.6 %)** | **1,513** |
| 710 McDonough | 1.442 | 1.528 | 1.174 | 5,944 | 758 |
| 6002 James H Miller | 0.893 | 1.217 | 1.845 | 4,646 | 902 |
| *(every other plant)* | ≤ 0.95 | ≤ 0.91 | ≤ 0.89 | | |

The fleet-wide residue is the CAMPD-gross vs model-net-summer wedge (`npl_model` is systematically
88–94 % of `npl_bench`). **Barry is categorically different** — 3–4× the next plant, at 1.5 GW, in
94–99.6 % of the hours of every year. Its availability p50 is **1,028 MW against a measured output p50
of 1,624 MW**; it reaches full capacity in **144 hours** where every peer CC reaches it in 1,800–2,160;
its `cap_p95` is 77 % of its own `cap_max` where every peer's is 100 %.

**The cause, from the sources rather than inferred:**

| unit | CAMPD `unitType` | CAMPD `primaryFuelInfo` | EIA-860 Technology | extract routes to | 2024 GWh / h | days "out" of 366 |
|---|---|---|---|---|---|---|
| 1 | **Tangentially-fired** | Pipeline Natural Gas | Natural Gas Steam Turbine (ST) | **`CC_REGULAR`** | 17.01 / 519 | **342** |
| 2 | **Tangentially-fired** | Pipeline Natural Gas | Natural Gas Steam Turbine (ST) | **`CC_REGULAR`** | 10.08 / 303 | **353** |
| 4 | **Tangentially-fired** | Pipeline Natural Gas | Conventional Steam Coal (ST) | **`CC_REGULAR`** | 152.02 / 1,539 | **298** |
| 5 | Tangentially-fired | Coal | Conventional Steam Coal | `COAL` ✓ | 838.36 / 1,795 | 284 |
| 6A/6B/7A/7B/8 | **Combined cycle** | Pipeline Natural Gas | NG Fired Combined Cycle | `CC_REGULAR` ✓ | 13,402 total | 6–29 |

Units 1, 2 and 4 are **boilers, measurably**. The deriver's plant-level `fac_group` short-circuit hands
every unit at a multi-bin facility to the plant's dominant model group, so 4.4 + 4.4 + 11.5 = **20.3 pp**
of derate lands on the combined-cycle block. **This is the identical defect already adjudicated at
pjm-75** (Chesterfield 3797 — 1,036 MW of retiring coal tagged `CC_REGULAR`, ~2.35 TWh of CC under-run)
**and miso-200** (Ninemile Point 1403 — two gas-steam boilers dumped on a 649.5 MW CC bin), and
`scripts/data/derive_campd_unit_outages.py::_resolve_unit_group`'s own docstring names it in both.

**The handoff's open item "Barry unit 4 — a 362 MW COAL model row CAMPD files as Pipeline Natural Gas"
is RESOLVED IN FAVOUR OF CAMPD.** The unit measurably burns gas; EIA-860's `Energy Source 1 = BIT` is
stale. *(The model's FLEET-side treatment of unit 4 still follows EIA-860 and is untouched here —
ROUTED, §9.)*

---

## 4. THE MECHANISM — ONE EXISTING GATE, ZERO FREE PARAMETERS, TWO KEYS MOVED

`campd_per_unit_attribution = True`. SOCO's cell was **`U`** (untested), so rule 28 `[R-MECH-MATRIX]`
(a)'s DO-NOT-REDO discipline was clear. The `-perunit-` companion was **derived in this lane from
SOCO's own CAMPD and EIA-860** — `scripts/data/derive_campd_unit_outages.py --iso SOCO --years 2023
2024 2025 --per-unit-crosswalk`. **Rules 25 `[R-ISO-SCOPE]` / 28(d): NYISO's verdict, where the gate
was built, transfers to nothing.**

**Blast radius, machine-verified:** of **1,119** extract rows, **3 unit rows / 48 window rows**
change routing, **all at facility 3**, and the changed set is exactly units 1, 2 and 4
(`CC_REGULAR` → `ST_GAS`). `gen_soco56_attestation._verify_extracts` raises if it is any wider.

### 4.1 Rule 19 `[R-ONE-MECH]`, at THREE grains, BEFORE the solve

`fleet_only` rebuild off the keeper's own `meta.json`:

| year | `fuel_prices` max\|Δ\| | `mc_base` max\|Δ\| | `availability` keys moved |
|---|---|---|---|
| 2023 | **0.000000000000** | **0.000000000000** | **2 of 128** (both plant 3) |
| 2024 | **0.000000000000** | **0.000000000000** | **2 of 128** (both plant 3) |
| 2025 | **0.000000000000** | **0.000000000000** | **2 of 91** (both plant 3) |

| year | (3, `CC_REGULAR`) mean avail | (3, `ST_GAS`) mean avail |
|---|---|---|
| 2023 | 0.1426 → **0.2803** | 0.8130 → 0.0330 |
| 2024 | 0.5217 → **0.8369** | 0.8130 → 0.0140 |
| 2025 | 0.5072 → **0.7901** | 0.8130 → 0.0220 |

### 4.2 SCOPE — ONLY THE OUTAGE HALF OF THE GATE FIRES, AND THAT IS A LANDMINE FOR A SUCCESSOR

The matrix base row documents `campd_per_unit_attribution` as **"ONE gate over BOTH artifacts"** — the
unit-outage windows *and* the thermal tranches (11 readers). **For SOCO only the outage half fires:**

```
thermal_tranche_csv_for_iso("SOCO", per_unit=True)  -> thermal_tranches_SOCO.csv   (the INCUMBENT)
unit_outage_csv_for_iso("SOCO", per_unit_crosswalk=True) -> campd-unit-outages-perunit-SOCO.csv
```

No `thermal_tranches-perunit-SOCO.csv` exists, so that reader falls back. **That is precisely why
§4.1 reads `mc_base` at exactly 0.000000000000** — the tranche half sets heat rates, min-stable loads
and band shares, and it never fired.

> **A SUCCESSOR THAT DERIVES `thermal_tranches-perunit-SOCO.csv` ARMS THE TRANCHE HALF SILENTLY UNDER
> THIS SAME FLAG, WHICH IS NOW ON FOR SOCO.** Derive it behind its own A/B, never as a data-intake
> side effect.

### 4.3 The structural signature — and it is NOT a fit

| year | keeper Barry CC available | **arm available** | **measured output** | arm − measured |
|---|---|---|---|---|
| 2023 | 2.275 | 4.471 | 7.303 | **−2.83 — still far short** |
| 2024 | 8.323 | **13.352** | **13.361** | **−0.009 (0.07 %)** |
| 2025 | 8.091 | **12.606** | **12.566** | **+0.040 (0.32 %)** |

2024 and 2025 land on the measured output to within a third of a percent. **2023 deliberately does
NOT**, because Barry unit 8's 345-day 2023 commissioning outage is a **genuine** combined-cycle outage
the per-unit crosswalk correctly leaves in the `CC_REGULAR` bin. *A mechanism that repaired all three
years to their actuals would be a fit; this one does not.*

---

## 5. WHAT THE RUN DELIVERED — AND IT IS AGAINST THE LANE

### 5.1 The scored C1 rows (band 7.180 / 7.466 / 7.545 TWh; share cap ±3.00 pp)

| year | class | keeper Δ | **arm Δ** | keeper share | **arm share** | status |
|---|---|---|---|---|---|---|
| 2023 | `CC_REGULAR` | +4.352 | **+5.752** | +1.68 | **+2.26** | PASS |
| 2023 | `CT_PEAKER` | +6.909 | **+6.058** | **+2.87** | **+2.52** | **PASS — headroom 0.13 → 0.48 pp** |
| 2023 | `ST_GAS` | −6.149 | **−6.461** | −2.57 | −2.70 | PASS |
| 2023 | `COAL_PRB` | −1.708 | **−1.928** | −0.74 | −0.83 | PASS |
| 2023 | `COAL_BIT` | −1.239 | −1.239 | −0.53 | −0.53 | PASS |
| **2024** | **`CC_REGULAR`** | **+7.505** | **+10.178** | **+2.81** | **+3.88** | **FAIL — now BOTH legs** |
| 2024 | `CT_PEAKER` | +4.286 | **+3.148** | +1.71 | **+1.25** | PASS |
| 2024 | `ST_GAS` | −5.319 | **−5.749** | −2.14 | −2.32 | PASS |
| 2024 | `COAL_PRB` | −4.140 | **−5.143** | −1.70 | −2.10 | PASS |
| 2024 | `COAL_BIT` | −0.624 | −0.690 | −0.27 | −0.30 | PASS |
| *2025 (SKIPPED — preliminary EIA-923)* | `CC_REGULAR` | *−1.963* | ***+0.390*** | *−1.07* | *−0.14* | *ungated* |
| *2025 (SKIPPED)* | `CT_PEAKER` | *+6.253* | ***+4.732*** | *+2.46* | *+1.86* | *ungated* |

**On the GATED rows the arm mostly moves against itself** — 2 better, 7 worse, 1 unchanged. **On
2025's ungated rows it mostly moves for itself** — 4 better, 1 worse, with `CC_REGULAR` going from
−1.963 to **+0.390**, a 5× reduction in absolute residual. Both are reported; neither is claimed.

### 5.2 Class volumes, arm − keeper (TWh, P1)

| class | 2023 Δ | 2024 Δ | 2025 Δ |
|---|---|---|---|
| `CC_REGULAR` | **+1.3995** | **+2.6728** | **+2.3530** |
| `CT_PEAKER` | **−0.8516** | **−1.1377** | **−1.5204** |
| `ST_GAS` | −0.3118 | −0.4301 | −0.3448 |
| `COAL_PRB` | −0.2205 | **−1.0031** | −0.3302 |
| `COAL_BIT` | −0.0000 | −0.0661 | −0.1429 |
| `CT_CHP` | −0.0038 | −0.0017 | −0.0038 |
| oil | 0.0000 | 0.0000 | −0.0059 |
| **nuclear, hydro, wind, solar, biomass, `CC_CHP`, `ST_CHP`, OTHER** | **0.0000** | **0.0000** | **0.0000** |

### 5.3 Barry, and the VOLL slack

| year | Barry CC model | ratio to actual | 2025 system slack |
|---|---|---|---|
| 2023 | 1.581 → **3.219** TWh | 0.22 → **0.44** | — |
| 2024 | 6.536 → **9.597** TWh | 0.49 → **0.72** | — |
| 2025 | 6.015 → **8.867** TWh | 0.48 → **0.71** | **8,930.2 → 7,907.2 MWh (−11.5 %)** |

---

## 6. THIS LANE'S OWN PREDICTIONS — **FIFTEEN OF FIFTEEN HELD**

| # | prediction | outcome |
|---|---|---|
| **P1** | 2024 `CC_REGULAR` WORSE and still FAILs; point +2.9, band +1.5 to +4.5 TWh | **CONFIRMED** — **+2.673**, row +10.178 of the predicted +9.0…+12.0 |
| **P2** | it now fails the **SHARE** leg too (>3.00 pp) | **CONFIRMED** — **+3.88 pp**, both legs |
| **P3** | determination stays `NOT-YET`; C1 stays 13/14; no other row changes status | **CONFIRMED** — identical `grade_summary` on both sides |
| **P4** | 2024 `CT_PEAKER` IMPROVES, −0.7 to −2.5 TWh → Δ +1.8 to +3.6 | **CONFIRMED** — −1.138, Δ **+3.148** |
| **P5** | 2024 `ST_GAS` worsens −0.3 to −1.6; stays PASS | **CONFIRMED** — −0.430, PASS |
| **P6** | 2024 `COAL_PRB` worsens −0.1 to −1.2; stays PASS | **CONFIRMED** — −1.003, near the wide edge, PASS |
| **P7** | **the thinnest row gets SAFER**: 2023 `CT_PEAKER` share 2.87 → 2.4–2.8 pp | **CONFIRMED** — **2.52 pp**, headroom 0.13 → 0.48 pp (3.7×) |
| **P8** | 2023 `CC_REGULAR` +0.5 to +2.2; stays PASS | **CONFIRMED** — +1.400, PASS |
| **P9** | Barry CC 2024 → 9.5–13.4 TWh, ratio 0.71–1.00 | **CONFIRMED** — **9.597**, ratio **0.72**, at the low edge |
| **P10** | 2025 NOT byte-identical, and its VOLL slack FALLS | **CONFIRMED** — every artifact differs; slack 8,930.2 → **7,907.2 MWh** |
| **P11** | rule 17 holds in all 15 plant-years; plant 3 stays 0.000; **direction unpredicted** | **CONFIRMED** — positive margin everywhere; plant 3 at 0.000, margin 0.0632 |
| **P12** | C8 under the 0.30 cap; **direction unpredicted** | **CONFIRMED** — `ST_GAS` 0.1241/0.1253/0.1381 → **0.1290/0.1307/0.1468** (it rose) |
| **P13** | C2/C4/C6 PASS; 0 ledgered, 0 protective; C3a/b/c UNSCORABLE | **CONFIRMED** |
| **P14** | zero new free parameters, `n_residual` unchanged at 1 | **CONFIRMED** — DOF 6 entries / 1 residual, identical to the keeper |
| **P15** | no peer ISO moves, no pre-existing cache key moves | **CONFIRMED** — `moved_rows("SOCO") == {}`; field already registered at `"False"` |

Second-order classes were banded wide and floor/forcing **direction** deliberately left unpredicted —
the SOCO-55 lesson, applied. P6 and P9 both landed near a band edge and that is recorded.

---

## 7. LEGITIMACY, AND THE COST THE ARM INTRODUCES

**C8 / D-2 PASS both sides.** `ST_GAS` forced share 0.1241/0.1253/0.1381 → **0.1290/0.1307/0.1468**
against the 0.30 merchant cap. **D-4 off-window binding PASS. D-9 quarantine PASS. D-10 PASS.**

**Rule 17 `[R-FLOOR-WINDOW]` holds in all fifteen plant-years**, positive margin everywhere, and
**plant 3 (Barry) stays at 0.000 forced share with a 0.0632 margin on both sides** — so the ST_GAS
availability collapse below costs no forced energy.

**D-1 gains ONE failure, and it is reported at full magnitude.**

| year | class | keeper | arm | |
|---|---|---|---|---|
| 2023 | `COAL_BIT` | r 0.438 / cv 0.002 **FAIL** | r 0.436 / cv 0.002 **FAIL** | inherited |
| 2025 | `COAL_BIT` | r 0.785 / cv 1.145 **FAIL** | r 0.798 / cv 1.012 **FAIL** | inherited, r improves |
| **2024** | **`COAL_PRB`** | r 0.964 / **cv 0.532 pass** | r 0.963 / **cv 0.463 FAIL** | **NEW, cv gate 0.50** |

Against that, six D-1 metrics improve (`CC_REGULAR` cv 0.244→0.284, 0.423→0.518, 0.857→1.000;
`CT_PEAKER` cv 0.602→0.637, 0.661→0.706, 0.614→0.660). **D-1 is REPORTED, not gated** — the standalone
C7 diurnal gate was retired at rubric v3.1, and rule 17's shape leg binds only for a class over its
forced-share budget, which D-2 shows none is.

**THE NEW OVER-DERATE ON BARRY'S `ST_GAS` BIN, stated at the gate rather than left to be discovered.**
The three re-routed units total 709.9 MW and land on a bin whose EIA-860 nameplate basis is 306.2 MW,
so the removed share clips and that bin's availability falls to ~0.02. **Bounded by measurement:**

| year | Barry `ST_GAS` model energy | hours `price > mc` | bound on the loss |
|---|---|---|---|
| 2023 | 2.349 GWh | 18 of 8,760 | **≤ 0.0023 TWh** |
| 2024 | 0.000 GWh | 3 of 8,760 | **0.0000 TWh** |
| 2025 | 7.149 GWh | 88 of 8,760 | **≤ 0.0071 TWh** |

≤ 0.18 % of the `ST_GAS` class in the worst year. The correct repair is a **sibling gate** —
`unit_outage_extract_basis_share` (nyiso-196) or `unit_outage_st_capacity_basis` — and arming either
here would be a **second mechanism on the same object**. **ROUTED, NOT STACKED** (rule 19).

---

## 8. GATES

| gate | result |
|---|---|
| **determination** | **`NOT-YET`** (rubric v3.8, PRICE UNSCORED) — identical to the keeper |
| **C1** | **FAIL**, 13/14 all · **9/10 free** — identical counts; the one failing row is 2024 `CC_REGULAR` |
| **C2 / C4 / C6 / C8** | **PASS** |
| **C3a / C3b / C3c** | **SKIPPED — UNSCORABLE**, not failed (no `actual_lmp.json` block for SOCO) |
| caveats | **0 ledgered · 0 protective**; `grade_summary` scored 5 / target 4 / fails 1 — identical |
| DOF | **6 entries / 1 residual** — identical; zero free parameters added |
| `check_bench_freshness` | **0 STALE** (41 engine-drift warnings, every ISO, pre-existing) |
| `check_mechanism_matrix --base origin/main` | **GREEN**, keeper stamps match every shard |
| `solve_surface` | `moved_rows("SOCO") == {}` |
| G-DRIFT vs `origin/main` | **clean** — the only solve-path change is `nyiso_offer_level_dispersion.json`, another ISO's ADDED artifact a SOCO run never reads |

**C5a CO2 (REPORTED-ONLY, contributes no status)**: −7.0/−10.7/+3.5 % → **−7.5/−11.8/+2.7 %**. 2024
reads FAIL on that reported-only stream both sides of the rubric's demotion; 2025 improves.

### 8.1 Expected gate noise, verified and reported, not chased

- **`audit_keepers` E13 fires TWICE**: for `2026-09-20-soco53g-prb-own-iso` (the **ninth** consecutive
  firing — rule 31 forbids deleting it, rule 30(a) forbids inventing a stamp) and for **this lane's own
  candidate**, which is the same posture. **RE-RAISED to the owner, §11.**
- **`audit_keepers` E11** — lineage recipe diff not computable after the SOCO-55 prune. Expected.
- **`check_cache_key_registration` RED** for `PPA_COST_RECOVERY_YR` and `REGIONAL_RENEWABLE_CF`
  (commit `3fc20b97`). **Verified NOT this lane's**: `campd_per_unit_attribution` is already in
  `_CACHE_KEY_OPTIONAL_FIELDS` with frozen drop value `False`.
- **`check_registry_payload_parity` RED LOCALLY** for seven dirs — `soco55_arm_{2023,2024,2025}`,
  `soco55_keeper_fat3`, `soco56_arm_{2023,2024,2025}`. **Every one machine-verified gitignored**, so
  none reaches `main` and CI stays green; the gate walks the filesystem (`:437`), which is exactly
  rule 31's 2026-09-16 correction. **Nothing deleted** (rule 31 `[R-RETAIN]`). `nwpp44_takeorpay_2025`
  no longer appears — NWPP-44 removed it upstream.
- **PJM §5.x prose header drift** — flagged by the matrix gate as pre-existing and PJM's lane's.

---

## 9. ROUTED

1. **PER-PLANT CC ALLOCATION IS THE SUCCESSOR'S OBJECT — AND IT IS NOT AN OWNERSHIP SPLIT.** The 2024
   CC per-plant ratio spans **0.49× (3 Barry) to 2.45× (55271 Tenaska Lindsay Hill)**, and every plant
   above 1.35× — Tenaska Lindsay Hill 2.45, McWilliams 1.57, Wansley 9 1.52, Central Alabama 1.42,
   Ratcliffe 1.41, E B Harris 1.38 — runs at **0.97–1.00 of its model availability** against measured
   CFs of 0.22–0.59. **This lane TESTED the ownership reading and it does not hold**: on EIA-860
   `Utility Name`, Southern-affiliated CC is 79.602 vs 80.851 TWh (**0.985×**) against non-Southern
   32.814 vs 29.397 (**1.116×**) — but Southern-affiliated `CT_PEAKER` is **2.219×** against
   non-Southern **1.705×**, i.e. the tilt runs the *other* way in the class SOCO-55 read it in.
   Recorded because a successor would otherwise inherit the inference.
2. **BARRY'S SPURIOUS OUTAGE WAS COMPENSATING FOR THAT, AND THE FORECAST NEVER HAD THE COMPENSATION.**
   A forecast year carries **no** CAMPD outage overlay, so the backcast's flattering CC number is a
   backcast-only artifact and the forecast already carries the error at full size.
3. **THE `ST_GAS` DENOMINATOR** — §7. `unit_outage_extract_basis_share` or
   `unit_outage_st_capacity_basis`, behind its own A/B.
4. **THE TRANCHE HALF OF `campd_per_unit_attribution`** — §4.2. The flag is now ON for SOCO; deriving
   `thermal_tranches-perunit-SOCO.csv` arms a second mechanism silently.
5. **BARRY UNIT 4'S FLEET ROW.** EIA-860 files it Conventional Steam Coal (`BIT`); CAMPD measures it
   burning Pipeline Natural Gas (152.02 GWh, 2024). The outage overlay now routes it correctly; the
   **fleet** row does not.
6. **`derive_parasitic_load.py` has never been run for SOCO** — coal meter 0.866–0.928 against the 0.93
   default. **Note the sign**: correcting it moves coal **down**, the wrong way for a `COAL_PRB` already
   short. Cross-ISO intake; reported, never taken.
7. **`coal_takeorpay_SOCO.csv` does not exist** while eight other ISOs have one — and arming
   `coal_takeorpay_from_data` would make coal *more* expensive. Wrong sign; reported, not taken.
8. **SOCO-53b, the 2025 hydro hole** — 0.327 TWh modelled against 6.012 measured. Hydro is
   byte-identical here in all three years; the arm reduces the VOLL slack it causes by 11.5 % without
   touching it.
9. **The within-footprint gas dispersion is still unmodelled** (SOCO-12 §4). Inherited from SOCO-55.

---

## 10. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** Phase 0, the `fleet_only` rebuilds, the extract derivation, the greedy
  re-stack, the composition, `--rebuild-benchmark`, the floor re-measurement and all scoring are
  zero-LP.
- **Three shards, ONE YEAR EACH** (rule 36 `[R-YEAR-ISOLATION]` (a)), all pinned to
  `3b1fc39a0005f4543c7feb8fbd5b2d242981f538`, each pushing a **full 16-file bundle** including
  `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet` (rule 34 (a)). Solve wall-clock
  ~110–120 s each, far inside the 20-minute ceiling.
- **Retrievability verified before anything was archived** (rule 34(d)): `git ls-tree` returned **16
  files** on each leg, all three were fetched, checked out, and their config signatures verified.

  | leg | SHA |
  |---|---|
  | `soco56_arm_2023` | `b0811ecac98cbaeb90abbedf20b5de8d2fe5a43a` |
  | `soco56_arm_2024` | `000f1ac781b79cf491e2feb9fbe465523be8a6c5` |
  | `soco56_arm_2025` | `94bb4b5a62129fe2432eac5cdcc5034491cd987c` |

  **Per rule 33(f)(1) those shard branches are cut when this lane's PR merges, and per rule 33(d) those
  SHAs are PROVENANCE, not a recovery route — cost any leg recovery as a RE-SOLVE.**
- **WHAT SURVIVES ON `main`** (rule 33(f)(4)(ii)): the composed, registered bundle
  `results/calibration/soco56_perunit_outage` in its rule-15 slim shape, its registry sidecar and its
  288 KB run payload. **A promotion from that state costs ZERO re-solves.**
- **THE CONTROL'S PER-PLANT LAYER WAS RECOVERED AT ZERO LP**, confirming SOCO-55 §9 item 5 a second
  time: the SOCO-55 shard branches are gone but `git fetch origin <40-char-sha>` retrieved all three
  legs, and **all twelve committed hourly sidecars verified byte-identical**. *The retention window is
  still undocumented, so this is not a durability claim.*
- **The seven leg / recovered-control dirs are gitignored, NOT deleted** (rule 31; `.gitignore`
  discharges rule 29(c), `rm` never does). **Nothing was deleted.**
- **All three shard sessions ARCHIVED** after fetch + checkout + verify + report-read (rule 33(a),
  (b), (e)). **None left alive.**

---

## 11. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — AND MY RECOMMENDATION

**SOCO's keeper is UNCHANGED at `2026-09-20-soco55-peryear-gas-basis`. Nothing was pruned. The
decision is yours.**

**WHERE THE BYTES ARE.** The registered arm bundle is **committed on `main`** in its rule-15 slim
shape with its sidecar and run payload, so **a promotion costs ZERO re-solves**. The seven per-year
leg and recovered-control dirs are on this container's local disk, gitignored; **this container is
ephemeral and they will not survive it** — but they are not needed for a promotion.

### MY RECOMMENDATION: **PROMOTE IT** — and the case is explicitly NOT the residual.

**FOR:**
1. **The defect is a fact, not a judgement.** CAMPD files Barry 1/2/4 as `Tangentially-fired` boilers;
   the extract calls them `CC_REGULAR`. The model is **physically forbidden** from reproducing a 1.8 GW
   plant's measured output in **97.6 % of the hours of 2024**.
2. **The repair is surgical and machine-verified**: 3 unit rows of 1,119, one facility, 2 of 128
   availability keys, `fuel_prices` and `mc_base` at exactly 0.000000000000.
3. **The repaired availability lands on the measured output** to 0.07 % (2024) and 0.32 % (2025) —
   and **deliberately not in 2023**, which is what tells you it is a mechanism and not a fit.
4. **Zero free parameters, no key moves, no ISO transferred.** Two other lanes have already adjudicated
   the identical defect in their own ISOs.
5. **The owner's standing ruling covers this case**: *"If structural integrity improves but gates
   regress that may still be a keeper."* Structure improves and one gate row regresses — this is that
   case, squarely.

**AGAINST, stated plainly:**
1. **The arm makes the lane's own target row worse** — 2024 `CC_REGULAR` +7.505 → +10.178 TWh, now
   failing both legs. If you want SOCO's headline residual to shrink, this is not it.
2. **It adds one D-1 failure** (2024 `COAL_PRB` cv_ratio 0.463 of a 0.50 gate) and a small new
   over-derate on Barry's `ST_GAS` bin (≤ 0.0071 TWh).
3. **On the gated rows it moves against itself 7 times and for itself twice.**

**If you promote**, rule 35 `[R-PROMOTE]` applies: the year union is **{2023, 2024, 2025}** over all
SOCO sidecars — enumerated **before** anything is deleted, per (b) — and the incoming bundle covers it
in one composed span, so **the promotion shrinks nothing**.

### A SECOND RULING I AM ASKING FOR — `2026-09-20-soco53g-prb-own-iso`

**E13 has now fired for this run NINE consecutive times.** It is a registered candidate SOCO-53g
recommended against promoting, adjudicated `I` (inert — it moves nothing scored in any year), and no
lane may delete it (rule 31) or stamp it (rule 30(a)) without your ruling. **My recommendation is to
DECLINE it**, which lets the next promoting session prune it and clears a nine-lane-old gate failure.

---

## Log entry

```
## soco-56 — 2026-09-20

THE HANDOFF'S LEAD LEVER IS REFUSED ON MEASUREMENT, EX ANTE. 2024 CC_REGULAR is
NOT marginal energy: 112.028 of 112.414 TWh -- 99.66 % -- is produced AT FULL
AVAILABILITY, 86.1 % of its unit-hours are at cap, and the whole class holds
5.268 TWh of idle headroom all year. In ZERO of 8,760 hours is the cheapest idle
COAL_PRB or ST_GAS unit cheaper than the marginal RUNNING CC (mean gaps +7.04 and
+8.15 $/MWh), and the fleet-median CC mc sits $7.00/MWh BELOW the clearing price.
Closing the 9.46 TWh the C1 rows ask for needs ~$5/MWh of merit-order movement
against 8.616 TWh of in-reach coal+steam headroom, while the same $5 band holds
20.594 TWh of CT_PEAKER headroom on a class already 1.9x its actual. Three more
levers refused ON SIGN and recorded so no successor spends a solve: the handoff's
own parasitic-load item, coal_takeorpay_from_data (makes coal MORE expensive) and
coal_fuel_inventory (a coal CEILING) -- all the wrong way for a COAL_PRB already
4.1 TWh short.

THE DEFECT FOUND INSTEAD IS A DATA DEFECT TRACED TO PRIMARY SOURCES.
data/raw/campd-unit-outages-SOCO.csv routes Barry (plant 3) units 1, 2 and 4 to
CC_REGULAR through the deriver's plant-level fac_group short-circuit. CAMPD files
all three as unitType "Tangentially-fired" -- BOILERS, never "Combined cycle" --
and EIA-860 files 1 and 2 as Natural Gas Steam Turbine, 4 as Conventional Steam
Coal. They are mostly idle (17.01 / 10.08 / 152.02 GWh in 519 / 303 / 1,539 h of
2024) and that idleness is charged as a 20.3 pp forced outage on Barry's
COMBINED-CYCLE block for 342 / 353 / 298 days of 366. THE CONSEQUENCE IS PHYSICAL:
the model's availability ceiling sits BELOW the plant's own measured CAMPD output
in 8,548 of 8,760 hours of 2024, by up to 1,513 MW and 5.080 TWh (2023: 5.031,
2025: 4.598); availability p50 1,028 MW against a measured output p50 of 1,624 MW;
full capacity reached in 144 hours where every peer CC reaches it in 1,800-2,160.
SAME DEFECT AS pjm-75 (Chesterfield) AND miso-200 (Ninemile Point), both already
adjudicated. It also resolves the standing "Barry unit 4 is a COAL model row CAMPD
files as Pipeline Natural Gas" item IN FAVOUR OF CAMPD -- the unit measurably
burns gas; EIA-860's BIT is stale.

THE LEVER -- campd_per_unit_attribution, cell U -> O. SOCO's own -perunit-
companion derived in-lane from SOCO's own CAMPD + EIA-860 (rules 25 / 28(d): NYISO's
verdict transfers to nothing). It re-routes 3 unit rows / 48 window rows of 1,119,
ALL at facility 3, machine-verified in gen_soco56_attestation._verify_extracts.
SCOPE, BECAUSE THE BASE ROW SAYS "ONE GATE OVER BOTH ARTIFACTS": ONLY THE OUTAGE
HALF FIRES -- thermal_tranche_csv_for_iso("SOCO", per_unit=True) returns the
INCUMBENT thermal_tranches_SOCO.csv, no -perunit- tranche companion existing, which
is exactly why rule 19 at three grains reads fuel_prices and mc_base at global
max |delta| EXACTLY 0.000000000000 in all three years while availability moves
exactly 2 of 128 (plant, group) keys, both plant 3. A SUCCESSOR THAT DERIVES THAT
TRANCHE COMPANION ARMS THE OTHER HALF SILENTLY UNDER THIS SAME FLAG.

THE RESULT IS AGAINST THE LANE AND THE INPUT IS KEPT ANYWAY. The gates DO NOT MOVE
-- NOT-YET, C1 13/14 all / 9/10 free, C2/C4/C6/C8 PASS, C3a/b/c UNSCORABLE, 0
ledgered and 0 protective, grade_summary identical on both sides -- and the single
failing row, 2024 CC_REGULAR, goes +7.505 -> +10.178 TWh of a +/-7.466 band and
+2.81 -> +3.88 pp of a +/-3.00 pp cap: it now fails BOTH legs where the keeper
failed one. PRECOMMIT-soco-56 P1 and P2 pre-registered exactly that from a zero-LP
greedy re-stack, with a +1.5 to +4.5 TWh band the measured +2.673 lands inside.
FIFTEEN OF FIFTEEN pre-registered predictions HELD. Rules 1 [R-STRUCT] and 14
[R-ACCURATE] govern: a model that cannot reproduce a 1.8 GW plant's measured output
in 97.6 % of a year is not modelling that plant, whatever the class total reads.

WHAT IT BUYS IS PHYSICS. Barry's CC availability 8.323 -> 13.352 TWh against a
measured 13.361 (0.07 %) in 2024 and 8.091 -> 12.606 against 12.566 (0.32 %) in
2025 -- and DELIBERATELY NOT in 2023, where unit 8's 345-day commissioning outage
is a genuine CC outage the crosswalk correctly leaves in place (4.471 vs 7.303).
That asymmetry is the mechanism's signature; a lever that repaired all three years
to their actuals would be a fit. 2025's VOLL slack falls 8,930.2 -> 7,907.2 MWh, and
the keeper's thinnest row -- 2023 CT_PEAKER at 0.13 pp of headroom -- gets 3.7x
safer (2.87 -> 2.52 pp).

COSTS, AT FULL MAGNITUDE. The three re-routed units (709.9 MW) land on Barry's
146.5 MW ST_GAS bin whose EIA-860 basis (306.2 MW) is smaller, so that bin's
availability clips to ~0.02 -- a NEW over-derate, bounded by measurement at
<= 0.0023 / 0.0000 / 0.0071 TWh (in merit 18 / 3 / 88 h of 8,760) and costing no
forced energy (plant 3's rule-17 share is 0.000 on both sides, margin 0.0632). The
correct repair is unit_outage_extract_basis_share or unit_outage_st_capacity_basis
and is ROUTED, NOT STACKED (rule 19). D-1 gains ONE failure -- 2024 COAL_PRB
cv_ratio 0.532 -> 0.463 of a 0.50 gate -- against six D-1 metrics that improve;
D-1 is REPORTED, not gated. Rule 17 holds in all fifteen plant-years; C8 ST_GAS
share 0.129 / 0.131 / 0.147 against the 0.30 cap. ZERO free parameters: DOF 6
entries / 1 residual, unchanged; the field was already in
_CACHE_KEY_OPTIONAL_FIELDS at "False" so no pre-existing key moves and
moved_rows("SOCO") == {}.

THE NAMED SUCCESSOR, AND AN INFERENCE THIS LANE TESTED AND REFUTED. Barry's
spurious derate was SILENTLY COMPENSATING for a real merchant-CC over-dispatch: the
2024 CC per-plant ratio spans 0.49x (Barry) to 2.45x (Tenaska Lindsay Hill), and
every plant above 1.35x runs at 0.97-1.00 of its model availability while its
measured CF is 0.22-0.59. THE OWNERSHIP READING DOES NOT HOLD -- on EIA-860 Utility
Name, Southern-affiliated CC is 79.602 vs 80.851 TWh (0.985x) against non-Southern
32.814 vs 29.397 (1.116x), but Southern-affiliated CT_PEAKER is 2.219x against
non-Southern 1.705x, i.e. the tilt runs the OTHER way in the class SOCO-55 read it
in. So the successor's object is PER-PLANT CC ALLOCATION -- heat rate, offer
surface, availability -- not a merchant/utility partition. It also matters for the
FORECAST: a forecast year carries NO CAMPD outage overlay, so the compensation is
not there and the backcast's flattering CC number is a backcast-only artifact.

KEEPER UNCHANGED at 2026-09-20-soco55-peryear-gas-basis; nothing pruned. The run
2026-09-20-soco56-perunit-outage is registered as a CANDIDATE and ITS PROMOTION IS
OPEN AND THE OWNER'S (rule 31 [R-RETAIN]); the lane's recommendation is TO PROMOTE,
on structure and not on the residual. A SECOND RULING IS ASKED FOR:
2026-09-20-soco53g-prb-own-iso has now fired audit_keepers E13 for the NINTH
consecutive lane; the standing recommendation is to DECLINE it so the next
promoting session may prune it. Records:
docs/handoffs/PRECOMMIT-soco-56-2026-09-20.md,
docs/handoffs/FINDING-soco-56-2026-09-20.md, scripts/gen_soco56_attestation.py,
scripts/probes/soco56_compose_span.py.
```

---

## 12. CODA — THE OWNER RULED, AND THE PROMOTION WAS EXECUTED IN THIS SESSION

**Written after §§1–11, which were composed while the promotion was still open. Those sections are
left as they stood; this coda records what changed rather than rewriting the record.**

The owner ruled, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper."*

**SOCO's keeper is now `2026-09-20-soco56-perunit-outage`.** Unlike SOCO-55 — whose coda had to record
that the ruling's second sentence did *not* describe its case, because its gates did not move at all —
**this promotion IS the ruling's harder limb, exactly**: structural integrity improves and a gate row
**regresses**, from +7.505 to +10.178 TWh on 2024 `CC_REGULAR`, which now fails both legs where the
outgoing keeper failed one. That regression was pre-registered in `PRECOMMIT-soco-56` §4 P1/P2 before
the solve and is the declared price of the repair.

Rule 35 `[R-PROMOTE]` was executed in this session, **in order**:

- **(b)** the year union `{2023, 2024, 2025}` was enumerated over **all three** SOCO sidecars —
  `soco53g`, `soco55`, `soco56` — **before** anything was deleted;
- **(c)** the incoming keeper covers that union in one composed span, so **the promotion shrinks
  nothing**;
- **(e)** the new designation was written, `build_status.py --iso SOCO` rebuilt, and `audit_keepers`
  re-run to resolve the incoming keeper's three stores, **before** `prune_iso_runs` touched anything;
- **(a)** the outgoing keeper's **three stores** were then deleted together — registry sidecar,
  `runs/<id>.js` payload and `results/calibration/soco55_peryear_basis` — via `--force-uncite`, which
  rule 35(d) names as the **intended** route here rather than a safety override. Its bundle is
  recoverable from git history at this branch point.

**`2026-09-20-soco53g-prb-own-iso` was deliberately NOT pruned** (passed to `--keep`). The ruling names
*the recommended candidate*, which is this lane's; it does not dispose of `soco53g`. Rule 31
`[R-RETAIN]` forbids deleting it and rule 30 `[R-TOUCHPOINT-FOLD]` (a) forbids inventing a stamp, so
**E13 still fires once — down from two — and is RE-RAISED, not cleared.** §11's recommendation stands:
decline it, and let the next promoting session prune it.

**ONE GATE FINDING SURFACED BY THE PROMOTION AND DECLARED RATHER THAN SUPPRESSED.** `audit_keepers`
**E11** — the silent-de-arm guard — flagged `meta.composed_from` moving
`['soco55_arm_*'] → ['soco56_arm_*']` as an undeclared keeper-recipe change. It is neither a de-arm nor
a solve-affecting field: it is the provenance list of the per-year shard bundles the parent composed,
which rule 36 `[R-YEAR-ISOLATION]` (a) **requires** be re-solved per year, so it cannot carry across a
promotion and necessarily renames at **every** sharded keeper. It is declared in the shard's
`promotion_note_soco56` and E11 now passes. *A successor promoting a sharded keeper on any ISO will
hit the same guard and owes the same declaration.*

**G-DRIFT re-run against the refreshed `origin/main`** (rule 29(b) form 4): the only solve-path change
since this lane's pin is SPP-67's `vre_reference_rate_year_own` — a new `ScenarioConfig` field shipping
**default `False`**, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `"False"` **in the same commit**, and
gating code (`_spp_wind_annual_rates`, `_spp_wind_year_own_curtailment_rate`) that is **SPP-only** and
reads an SPP wind-curtailment artifact. **INERT for SOCO** on two independent grounds — another ISO's
branch, and a default-off flag absent from this keeper's recipe — and SOCO dispatches **0.000 TWh of
wind in every year**. Form 4 holds and the A/B stands.

**Post-promotion gates:** `check_mechanism_matrix --base origin/main` GREEN, keeper stamps matching
every shard, with the SOCO shard's `keeper` + `gates` and the §5.8 header re-stamped and the
`campd_per_unit_attribution` cell moved **`O` → `K`** in this session (rule 28); `build_status --iso
SOCO` rebuilt and in sync; `audit_keepers` holdout / marker / status all pass with the **one** expected
E13. `calibration-complete.json` carries **no SOCO entry**, confirmed rather than assumed, so there was
nothing to re-key there.
