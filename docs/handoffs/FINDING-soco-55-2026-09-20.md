# FINDING — SOCO-55 (2026-09-20): SOCO's benchmark was stale and the keeper's headline was wrong; the year-invariant gas basis is repaired, the 2023 fit gets worse, and the input is kept

**Lane** SOCO-55 · **Model** Opus · **DATA PROFILE** `soco` · **Parent LP cost: ZERO** (rule 32(a) `[R-SHARD]`).
**Keeper UNCHANGED** at `2026-09-20-soco54-marginal-gas-basis`. **Nothing was pruned. Nothing was deleted.**
**PROMOTION IS OPEN AND IS THE OWNER'S** (rule 31 `[R-RETAIN]`; §11).

---

## 1. HEADLINE

**TWO results. The first is a DATA decision this desk owed, not a lever, and it outranked the lever.**

### (1) SOCO IS `NOT-YET`. THE BENCHMARK IT REACHED ITS CEILING ON WAS STALE.

`check_bench_freshness` was **RED for SOCO ALONE** repo-wide: 44 parts checked, **3 STALE** — a hard
`::error` — against 41 warning-level engine drift on every other ISO. Rebuilt at HEAD (zero LP, 37 s)
and the incumbent keeper re-scored on it:

| | committed (stale) bench | **rebuilt bench — the one that reproduces at HEAD** |
|---|---|---|
| determination | `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` | **`NOT-YET`** |
| C1 | 14/14 PASS | **13/14 — 2024 `CC_REGULAR` FAILS** |
| 2024 `CC_REGULAR` | +7.417 TWh of ±7.47 (PASS by 0.05) | **+7.505 TWh of ±7.47 (FAIL by 0.035)** |
| C2 / C4 / C6 / C8 | PASS | PASS |
| caveats | 0 ledgered, 0 protective | 0 ledgered, 0 protective |

**Saying it as plainly as the handoff required: SOCO reads `NOT-YET`.** `PRECOMMIT-soco-54` §8 **P4
pre-registered this exact row at 81 % of its margin** and the SOCO-54 FINDING put it in its own
headline — a declared risk materialising once the data decision was actually taken, not a regression
discovered late. `check_bench_freshness` now reads **0 STALE**.

**No dispatch moved.** Every keeper hourly sidecar is byte-identical to the day it was solved, and its
297 KB run payload re-renders byte-identical. **Only the benchmark moved** — the ISO's ceiling reading
had rested on a benchmark that could not be reproduced from the builder at HEAD.

### (2) THE YEAR-INVARIANT GAS BASIS IS REPAIRED. THE 2023 FIT GETS WORSE. THE INPUT IS KEPT.

`2026-09-20-soco55-peryear-gas-basis` (bundle `results/calibration/soco55_peryear_basis`) arms **one**
delta: `gas_basis_differential_measured_by_year = True`. **Zero free parameters** (`n_residual`
unchanged at 1); **one** new default-off `ScenarioConfig` gate; **no pre-existing cache key moves**.

It reads **`NOT-YET`**, C1 **13/14**, with the **same single failing row** as the keeper. That is not a
disappointment — `PRECOMMIT-soco-55` **P7 pre-registered it verbatim**, because at the registered 2dp
the 2024 measured basis equals the scalar, so **2024 is byte-identical on all eight artifacts**.

---

## 2. WHAT WAS WRONG WITH THE INPUT, MEASURED RATHER THAN ARGUED

`GAS_BASIS_DIFFERENTIAL["SOCO"] = 0.64` is **the 2024 value applied to every year**, and its own
comment registers it as a *"Forward-year / fallback value only — the SOCO backcast prices gas per plant
off EIA-923 monthly delivered cost like PJM/NYISO."*

**Since SOCO-54 that sentence is false.** Turning `gas_plant_monthly_fuel_pricing` off put the declared
FALLBACK on SOCO's **PRIMARY** backcast gas-pricing path, where `resolve_annual_gas_price` returns
`gas_price_override + 0.64` for every SOCO gas unit in every year.

**Re-derived at HEAD**, reproducing SOCO-20's committed comment exactly — quantity-weighted EIA-923
Schedule-2 delivered gas to the run's own EIA-860 SOCO gas fleet, minus the Henry Hub annual mean:

| year | plants | quantity (MMBtu) | q-wt delivered | Henry Hub | **measured basis** | applied | **error** |
|---|---|---|---|---|---|---|---|
| 2023 | 26 | 646,487,128 | 3.0288 | 2.5357 | **+0.4931** | 0.64 | **+0.15** |
| 2024 | 27 | 650,711,973 | 2.8320 | 2.1925 | **+0.6395** | 0.64 | **0.00** |
| 2025 | 27 | 641,283,196 | 4.1829 | 3.5289 | **+0.6540** | 0.64 | **−0.01** |

At ~11 MMBtu/MWh, 2023 carried **≈ +$1.65/MWh on every SOCO gas unit**. This is rule 23
`[R-FROZEN-DERIVE]` — a re-derivation cited to **source data**, never to a residual — and rule 14
`[R-ACCURATE]`. **SOCO-54 declared the imprecision against itself** (ADDENDUM §2) and **routed** the
repair rather than taking it, because taking it after seeing its own result would have been selecting a
parameter on the outcome. This lane is that routed repair.

**PRECISION WAS FIXED BEFORE THE SOLVE AND IS NOT SELECTABLE BY A RESULT.** Every row of
`GAS_BASIS_DIFFERENTIAL` is 2dp and SOCO-20 published this derivation at 2dp, so the table lands at 2dp.
Its declared consequence — stated in the PRECOMMIT, not discovered later — is that **the 2024 value is
unchanged**. Choosing 4dp (0.6395) instead would have perturbed the 0.035-TWh-margin 2024 row, and
picking a precision by what it does to a row is exactly what rule 1 `[R-STRUCT]` forbids.

---

## 3. THE MECHANISM — ONE GATE, ZERO FREE PARAMETERS, INERT EVERYWHERE ELSE

* `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR` (`fuel_trajectories.py`), **SOCO only**.
* `ScenarioConfig.gas_basis_differential_measured_by_year: bool = False` — a **gate**, so the repair is
  an auditable single-delta A/B against the incumbent keeper rather than a constant edit that re-keys a
  keeper with no control.
* `resolve_annual_gas_price`: the year's own measured basis **REPLACES** the scalar (rule 19
  `[R-ONE-MECH]` — never scalar-plus-adjustment). Any `(iso, year)` with no measured row falls through
  to the scalar unchanged.
* Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"` **in
  the same commit as the field** (the nyiso-119 discipline) → **no pre-existing cached run is re-keyed**.
* Declared in `solve_surface_declared` at its live hash: SOCO **182 → 183 rows**, `moved_rows("SOCO")
  == {}`. **The scalar row is machine-verified UNMOVED at 0.64** — this lane GATES the scalar, it does
  not edit it, so every unarmed run keeps its key and its number.

**Rule 13 `[R-MEASURED]` forward test PASSES** — the quantity is producible for a forward year from
that year's own receipts and responds to changed conditions; with no receipts the forward scalar is used
unchanged. Verified zero-LP: SOCO 2030 armed = 5.12 = SOCO 2030 unarmed.

**Rule 25 `[R-ISO-SCOPE]`** — the table carries a SOCO row **and nothing else**, machine-verified by the
attestation generator, which raises otherwise. `resolve_annual_gas_price` is identical armed and unarmed
for ERCOT / CAISO / MISO / PJM / NYISO / NEISO / SPP / NWPP.

### 3.1 Rule 19, mechanically, at two grains, BEFORE the solve

| year | `fuel_prices` max\|Δ\| | `mc_base` max\|Δ\| | classes that move |
|---|---|---|---|
| 2023 | 0.177000000000 | 2.588654953887 | the SIX gas classes ONLY |
| **2024** | **0.000000000000** | **0.000000000000** | **none** |
| 2025 | 0.011800000000 | 0.172576996926 | the SIX gas classes ONLY |

`COAL_PRB`, `COAL_BIT`, oil, nuclear, hydro, wind, solar and biomass are at max |Δ| **exactly
0.000000000000** in all three years. (0.177 against a 0.15 basis delta is `GAS_MONTHLY_SEASONALITY`'s
1.18 peak month — the shape multiplies the level, as it does for the scalar.)

---

## 4. WHAT THE RUN DELIVERED — AND IT IS AGAINST THE LANE

### 4.1 The scored C1 rows, rebuilt bench (2025's seven are SKIPPED on the preliminary vintage)

| year | class | keeper | **arm** | actual | keeper Δ | **arm Δ** | arm share | status |
|---|---|---|---|---|---|---|---|---|
| 2023 | `CC_REGULAR` | 112.126 | **112.312** | 107.960 | +4.166 | **+4.352** | +1.68pp | PASS |
| 2023 | `CT_PEAKER` | 10.668 | **11.413** | 4.503 | +6.165 | **+6.910** | **+2.87pp** | **PASS, 0.13pp of margin** |
| 2023 | `ST_GAS` | 3.986 | **4.293** | 10.442 | −6.456 | **−6.149** | −2.57pp | PASS |
| 2023 | `COAL_PRB` | 21.722 | **20.443** | 22.151 | −0.429 | **−1.708** | −0.74pp | PASS |
| 2023 | `COAL_BIT` | 11.672 | 11.672 | 12.911 | −1.239 | −1.239 | −0.53pp | PASS |
| 2024 | **`CC_REGULAR`** | 112.414 | **112.414** | 104.909 | +7.505 | **+7.505** | +2.81pp | **FAIL (byte-identical)** |
| 2024 | `CT_PEAKER` | 9.103 | 9.103 | 4.816 | +4.287 | +4.287 | +1.71pp | PASS |
| 2024 | `ST_GAS` | 3.554 | 3.554 | 8.873 | −5.319 | −5.319 | −2.14pp | PASS |
| 2024 | `COAL_PRB` | 20.569 | 20.569 | 24.709 | −4.140 | −4.140 | −1.70pp | PASS |

**THREE of the four moving 2023 rows go the WRONG way.** Only `ST_GAS` improves. Every row still
PASSES and the determination does not move, but **the 2023 residual is LARGER after the repair than
before it.**

### 4.2 Class volumes, arm − keeper (TWh, P1)

| class | 2023 Δ | 2024 Δ | 2025 Δ |
|---|---|---|---|
| `COAL_PRB` | **−1.2789** | **0.0000** | +0.0005 |
| `CT_PEAKER` | **+0.7443** | **0.0000** | −0.0025 |
| `ST_GAS` | **+0.3073** | **0.0000** | −0.0001 |
| `CC_REGULAR` | **+0.1870** | **0.0000** | −0.0011 |
| `CT_CHP` | +0.0017 | 0.0000 | 0.0000 |
| `COAL_BIT` | +0.0001 | 0.0000 | +0.0032 |
| nuclear, hydro, wind, solar, biomass, oil, `CC_CHP`, `ST_CHP`, OTHER | **0.0000** | **0.0000** | **0.0000** |

### 4.3 2024 IS BYTE-IDENTICAL — P5 CONFIRMED ON ALL EIGHT ARTIFACTS

`class_hourly` · `class_band_hourly` · `system` · `unit_hourly` · `network` · `storage` ·
**`dispatch/2024_P1.parquet`** · **`floors/2024_P1.npz`** — every one matches the keeper's sha256.
Every 2023 and 2025 counterpart differs, except `floors/2025_P1.npz`, which is also identical: the
+0.01 $/MMBtu shift did not change the 2025 P0 run pattern.

---

## 5. THE REAL PRODUCT — WHAT THE ACCURATE INPUT LOCALIZES

**Rule 14 `[R-ACCURATE]` anticipates this result exactly:** *"If swapping a hand estimate for real data
makes the backcast worse, that is a signal that something else in the model is miscalibrated and the
estimate was silently compensating for it. Treat the worse fit as a discovered bug: keep the accurate
input, find and fix the real root cause. Do not bury the error back inside an inaccurate input."*

**So: what was the +0.15 $/MMBtu cancelling?** At plant grain, 2023:

| plant | class | keeper | **arm** | Δ | **actual** |
|---|---|---|---|---|---|
| **6002 James H Miller Jr** | `COAL_PRB` | 15.838 | **14.626** | **−1.212** | **15.701** |
| 6073 Victor J Daniel Jr | `COAL_PRB` | 1.236 | 1.194 | −0.042 | 1.499 |
| 6257 Scherer | `COAL_PRB` | 4.648 | 4.623 | −0.025 | 6.461 |
| **2049 Jack Watson** | `ST_GAS` | 1.256 | **1.403** | **+0.147** | **3.270** |
| **55409 Calhoun** | `CT_PEAKER` | 1.383 | **1.498** | **+0.115** | **0.026** |
| **55061 Tenaska Georgia** | `CT_PEAKER` | 2.690 | **2.801** | **+0.111** | **0.238** |
| **7709 Dahlberg** | `CT_PEAKER` | 1.279 | **1.388** | **+0.109** | **0.243** |
| 55267 Edward L. Addison | `CT_PEAKER` | 0.668 | 0.763 | +0.096 | 0.200 |
| **728 Yates** | `ST_GAS` | 0.801 | **0.888** | **+0.087** | **2.239** |
| 56 Lowman Energy Center | `CC_REGULAR` | 0.953 | 1.015 | +0.062 | 1.591 |
| 3 Barry | `CC_REGULAR` | 1.520 | 1.581 | +0.061 | 7.340 |
| 533 McWilliams | `CC_REGULAR` | 3.461 | 3.521 | +0.060 | 3.639 |
| 55128 Walton County | `CT_PEAKER` | 1.403 | 1.458 | +0.055 | 0.259 |
| 26 E C Gaston | `ST_GAS` | 0.731 | 0.778 | +0.047 | 1.654 |

**95 % of the 1.279 TWh of coal displacement is ONE PLANT.** 6002 James H Miller Jr goes 15.838 →
14.626 against a **15.701** actual: the keeper had it **nearly exact** (+0.137) and the arm moves it to
−1.075.

**About half of the energy it sheds lands on merchant turbines already far above their own actuals** —
Calhoun (58× its actual), Tenaska Georgia (12×), Dahlberg (5.7×), Addison (3.8×). **The other half lands
correctly** on Jack Watson (toward 3.270) and Yates (toward 2.239).

> **THE DISCOVERED BUG, NAMED: SOCO's merchant `CT_PEAKER` tranche is priced too cheap against James H
> Miller's PRB coal, so ANY general reduction in the gas level lands disproportionately on a class that
> is already 2.5× its actual.** That is a merit-order defect between `CT_PEAKER` and `COAL_PRB`. It is
> **not** the gas basis, and it is what a successor should attack. This is new evidence the keeper's
> mis-based input was hiding.

---

## 6. THIS LANE'S OWN PREDICTIONS — **FOURTEEN OF FOURTEEN HELD, AND TWO WERE CLOSE**

| # | prediction | outcome |
|---|---|---|
| **P1** | 2023 coal falls, point −0.4, band −0.05 to −1.6 TWh | **CONFIRMED** — −1.279, at the wide end |
| **P2** | 2023 `CC_REGULAR` rises, 0.0 to +1.2 | **CONFIRMED** — +0.187 |
| **P3** | 2023 `CT_PEAKER` rises, 0.0 to +0.8 | **CONFIRMED** — +0.744, at **93 % of the upper edge**. The band was nearly too tight and that is recorded |
| **P3-RISK** | **STATED RISK, THE LANE'S #1**: a rise past ≈ +1.0 TWh flips 2023 `CT_PEAKER` to FAIL | **MATERIALISED SHORT OF A FLIP.** The row PASSES, but its share headroom collapses **0.44pp → 0.13pp** of the ±3.00pp cap. It is now the thinnest row in the run after 2024 `CC_REGULAR` |
| **P4** | 2023 `ST_GAS` within ±0.6 | **CONFIRMED** — +0.307 |
| **P5** | **2024 byte-identical** | **CONFIRMED on all eight artifacts** |
| **P6** | every 2025 class < 0.15 TWh | **CONFIRMED** — max 0.0032 |
| **P7** | 2024 `CC_REGULAR` unchanged at +7.505, still FAILs; determination stays `NOT-YET` | **CONFIRMED EXACTLY** |
| **P8** | no 2025 C1 row changes status | **CONFIRMED** — all SKIPPED |
| **P9** | C2/C4/C6/C8 PASS; 0 ledgered, 0 protective | **CONFIRMED** |
| **P10** | DOF gains 3 measured entries, `n_residual` 1, zero free parameters | **CONFIRMED** — 6 entries / 1 residual |
| **P11** | rule 17 holds in all fifteen plant-years; **direction deliberately unpredicted** | **CONFIRMED** — positive margin everywhere; 728 Yates binds MORE (0.482 → 0.514), 2049 Watson slightly LESS (0.557 → 0.548) |
| **P12** | `ST_GAS` forced share under the 0.30 cap; **direction unpredicted** | **CONFIRMED** — 0.1375 → 0.1241 (2023), unchanged 2024/2025 |
| **P13** | peers byte-identical, no key moves | **CONFIRMED** zero-LP |
| **P14** | SOCO 182 → 183 surface rows, `moved_rows == {}` | **CONFIRMED** |

SOCO-54 falsified three of twelve, all second-order, because a gas reprice changes the P0 pattern the
campaign floor is detected from. This lane banded for that (P4, P11, P12 all widened or
direction-free) and none was falsified.

---

## 7. LEGITIMACY, A/B INTEGRITY AND G-DRIFT

**D-2 / C8 PASS on both sides.** `ST_GAS` forced share 0.1375 → **0.1241** (2023), 0.1253 and 0.1381
unchanged, against the 0.30 merchant cap. **D-4 off-window binding PASS.** **D-1** carries the **same
three** failures on both sides (2023 `COAL_BIT` profile r 0.469 → 0.438 and CV ratio 0.003 → 0.002;
2025 `COAL_BIT` r 0.785 unchanged) — none cleared, none added. D-1 is REPORTED, not gated.

**Rule 17 `[R-FLOOR-WINDOW]` holds in all fifteen plant-years**, with positive margin everywhere.

**A/B integrity is EXACT**: `--rebuild-benchmark` on the arm composite reproduces the **same three
benchmark content hashes** as the keeper's (`campd-eecf72fbab56`, `eia923-a3ef92c2e963`,
`eia930-af1df2c6e425`), so arm and control are scored against the **same bench**.

**G-DRIFT (rule 29 `[R-SCREEN]` (b)): form 4 stood, NO CONTROL SOLVE WAS SPENT.** The solve-path diff
between the keeper's basis and this lane's pinned SHA is **this lane's own five files and nothing else**
— the four mechanism files plus `solve_surface_declared.py` — every one default-off and the arm under
test. Recorded in the PRECOMMIT before any leg was solved.

**Regression impact, measured both ways in a clean worktree**:
`tests/unit/config` + `tests/regression/test_persisted_identity.py` fail **11 at `origin/main` and 11
with this change**. **Zero new failures.**

---

## 8. GATES

| gate | state |
|---|---|
| `check_bench_freshness` | **0 STALE** (was 3, SOCO-only, a hard `::error`) — **cleared by this lane** |
| `check_mechanism_matrix --base origin/main` | **PASS** — integrity, 0 unresolvable anchors, keeper stamps, §5.x prose headers, all three ratchets, *"1 new field(s) all registered"* |
| `audit_keepers --iso SOCO` | **E13 + E11 — EXPECTED, RE-RAISED NOT CLEARED** (§8.1). S1 was stale after the bench rebuild and **was repaired** (`build_status.py --iso SOCO`) |
| `check_registry_payload_parity` | **RED LOCALLY, GREEN IN CI** — the unmapped dirs are this session's own **gitignored** bundles, all verified `git check-ignore`-clean with **0 tracked files on HEAD**. Rule 31's 2026-09-16 correction documents exactly this; **no result was deleted to clear it** |
| `check_cache_key_registration` | **RED at HEAD, NOT THIS LANE'S** — `PPA_COST_RECOVERY_YR`, `REGIONAL_RENEWABLE_CF` (commit `3fc20b97`). This lane declared **its own name only** and left those two to their lane |
| `tests/…::test_soco_token_collides_with_no_other_raw_name` | **RED at HEAD, not patched** — a SOCO-desk naming decision, not a lane's |

### 8.1 E13, and the owner is asked for a ruling

**E13 fires for the SEVENTH consecutive SOCO lane.** `2026-09-20-soco53g-prb-own-iso` is a registered
CANDIDATE the owner has not ruled on, so it is neither the keeper nor stamped to one. Rule 31
`[R-RETAIN]` forbids deleting it; rule 30 `[R-TOUCHPOINT-FOLD]` (a) forbids inventing a `holdout.keeper`
stamp. **It is RE-RAISED, not cleared** — and **this lane's own run now adds a second unruled candidate
for the same reason**, which is stated rather than tidied away. E11 (*lineage recipe diff not
computable*) is the expected bundle pruned two promotions ago.

---

## 9. ROUTED

1. **THE `CT_PEAKER` / `COAL_PRB` MERIT ORDER AT JAMES H MILLER** — §5. New evidence, and the lane's
   recommended successor object.
2. **55061 Tenaska Georgia (12× its actual) and 55409 Calhoun (58×)** — both made worse here, both
   still routed. Against that, **2049 Jack Watson recovers** 1.256 → 1.403 (actual 3.270), partially
   repairing SOCO-54's routed miss.
3. **2024 `CC_REGULAR` at +7.505 TWh** — the failing row, which no lane has yet attacked directly and
   which this arm is provably inert in.
4. **OTHER ISOs DO CARRY CONSTANT-MULTIPLIER CONTRACT FAMILIES — REPORTED, NEVER TAKEN.** SOCO-54 §9
   item 9 routed this and this lane measured it, zero LP, with SOCO-54's own method (largest set of
   reporting plants whose monthly delivered-price ratio series is flat at CV ≤ 0.001 over 10–12 months):

   | ISO | 2023 | 2024 | 2025 | keeper arms `gas_plant_monthly_fuel_pricing`? |
   |---|---|---|---|---|
   | **SPP** | 6/63 | **50/60** | **50/54** | **YES** |
   | **ERCOT** | 9/20 | 10/23 | **26/26** | no (`G`, documented) |
   | SOCO | 7/24 | 8/25 | 8/26 | no (SOCO-54 turned it off) |
   | MISO | 7/102 | 7/98 | 6/100 | YES |
   | PJM | 6/26 | 6/25 | 6/23 | YES |
   | NWPP | 3/28 | 4/29 | 3/26 | ? |
   | NYISO | **none** | **none** | **none** | YES |
   | CAISO | **none** | **none** | **none** | YES |
   | NEISO | VOID (1 reporting plant) | | | YES |

   **SPP is the striking one: 50 of 60 reporting plants on one common shape, on a keeper that arms the
   per-plant print.** Rules 25 `[R-ISO-SCOPE]` / 28(d): **no other ISO's cell is filled and no verdict
   transfers.** Each lane owns its own receipts and must measure them itself.
5. **RULE 33(d) IS TOO PESSIMISTIC ABOUT LEG RECOVERY, MEASURED.** The SOCO-54 shard **branches** are
   gone, but their **objects** are still on the remote: `git fetch origin <40-char-sha>` retrieved all
   three legs, and composing them reproduced the committed keeper's twelve hourly sidecars
   **byte-for-byte**, with `meta.json` differing in exactly one key (`shared_inputs`). That recovery is
   what made item (1) possible at zero LP. **The retention window is undocumented and unguaranteed, so
   rule 33(f) still stands — land what must survive on `main`** — but a lane facing a "lost" leg should
   **try the SHA fetch before costing a re-solve**.
6. **`derive_parasitic_load.py` has never been run for SOCO** — coal meter 0.866–0.928 against the 0.93
   default, so every SOCO coal heat rate is biased **LOW** by 1.5–5.9 %. **Note the sign**, because it
   bears on §5: a heat rate biased low makes coal look **cheaper**, so correcting it moves coal **down**
   — the wrong direction for a 2024 `COAL_PRB` already 4.1 TWh short. Cross-ISO intake; reported, never
   taken.
7. **SOCO-53b, the 2025 hydro hole** — 0.327 TWh modelled against 6.012 measured; the LP posts 8,930.2
   MWh of VOLL slack, identical in arm and keeper. Hydro is byte-identical here in all three years.
8. **Barry unit 4** — a 362 MW COAL model row CAMPD files as Pipeline Natural Gas.
9. **The within-footprint gas dispersion is still unmodelled.** The SOCO backcast prices every gas unit
   off ONE footprint-wide delivered level per year. A credible plant-specific delivered cost needs a
   daily hub index plus measured variable transport, and no free public daily index exists at SONAT or
   Transco/Dalton (SOCO-12 §4).

---

## 10. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** Phase 0, the `fleet_only` rebuilds, the greedy re-stack, the leg recovery,
  both compositions, the two `--rebuild-benchmark` repairs, the floor re-measurement, the cross-ISO
  family census and all scoring are zero-LP.
- **Three shards, ONE YEAR EACH** (rule 36 `[R-YEAR-ISOLATION]` (a)), all pinned to
  `2a7901215f5f8d78835cf3e314caffe06d8c656b`, each pushing a **full 16-file bundle** including
  `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet` (rule 34 (a)). Peak memory
  **2.60–2.65 GiB**; wall-clock **107–118 s** each — far inside the 20-minute ceiling.
- **Retrievability verified before anything was archived** (rule 34(d)): `git ls-tree` returned **16
  files** on each leg, and all three were fetched, checked out and verified before archiving.

  | leg | SHA |
  |---|---|
  | `soco55_arm_2023` | `95f81a8cc91d0de9c7350c8049c902b17ccc9877` |
  | `soco55_arm_2024` | `ef1d35bcd3997ed4b17fe241816ac004fc271a71` |
  | `soco55_arm_2025` | `a16b676b0de852df49f6c5d40d5df64990e3a37d` |

  Re-compose at zero LP with `scripts/probes/soco55_compose_span.py --expect-measured true`.
  **Per rule 33(f)(1) those shard branches are auto-deleted when this lane's PR merges. Item 5 above
  shows the objects may survive the ref — but that is not a durability claim, so these SHAs are
  PROVENANCE and any leg recovery is costed as a RE-SOLVE.**
- **WHAT SURVIVES ON `main`** (rule 33(f)(4)(ii)): the composed, registered bundle
  `results/calibration/soco55_peryear_basis` in its rule-15 slim shape, its registry sidecar and its run
  payload — **a promotion from that state costs ZERO re-solves** — plus the re-scored keeper bundle
  `results/calibration/soco54_marginal_gas` and the three rebuilt `bench/SOCO/*.json.gz` parts.
- **The three arm legs, the recovered SOCO-54 legs, the recovered fat keeper and the composer-validation
  bundle are gitignored, NOT deleted** (rule 31; `.gitignore` discharges rule 29(c), `rm` never does).
  **Nothing was deleted.**
- **The composer was VALIDATED BEFORE USE**: `soco55_compose_span.py --expect-measured false` over the
  three recovered SOCO-54 legs reproduces the committed keeper's hourly sidecars **byte-identically,
  18 of 18**.
- **All three shard sessions ARCHIVED** after fetch + checkout + verify + report-read (rule 33(a), (b),
  (e)). **None left alive.**

---

## 11. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — AND MY RECOMMENDATION

**SOCO's keeper is unchanged at `2026-09-20-soco54-marginal-gas-basis`. Nothing has been pruned.**
There are now **TWO** registered SOCO candidates the owner has not ruled on:
`2026-09-20-soco53g-prb-own-iso` (open since the previous-but-one lane, E13's seventh consecutive
firing) and **`2026-09-20-soco55-peryear-gas-basis`** (this lane's).

### MY RECOMMENDATION: PROMOTE IT — and the case is explicitly NOT the residual.

**The structural case (rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]`, which decide).** The keeper
prices every 2023 SOCO gas unit with a basis measured on **2024's** receipts — a constant its own
comment registers as a forward-year fallback, promoted onto the primary backcast path by the previous
lane, wrong by a measured **+0.15 $/MMBtu**. The arm replaces it with each year's own measured basis,
from the same committed receipts, at the same precision convention, with **zero free parameters** and
**no pre-existing cache key moved**. That is right **whatever the residual did**.

**And the residual got worse, which I am not going to dress up.** 2023 `CT_PEAKER`, `CC_REGULAR` and
`COAL_PRB` all move away from their actuals; only `ST_GAS` improves; and 2023 `CT_PEAKER`'s share
headroom collapses to 0.13pp. **Rule 14 says that is a discovered bug, not a reason to revert** — and
this lane converted it into a named, plant-level successor object (§5) that the mis-based input had been
hiding. A reader who wants the lowest MAE should keep the keeper; a reader who wants the model whose
mechanisms mirror the market should take the arm. Rule 1 says which of those a keeper is.

**What promotion would cost: ZERO re-solves.** The composed bundle, its sidecar and its 19 MB payload
are on this lane's branch and will be on `main` when it merges.

**THE TWO QUESTIONS, PUT PLAINLY:**

1. **Promote `2026-09-20-soco55-peryear-gas-basis` to SOCO's keeper?** If yes, rule 35 `[R-PROMOTE]`
   applies in that session: the year union is `{2023, 2024, 2025}` and the incoming bundle covers it in
   full, so the outgoing keeper's three stores are prunable once `audit_keepers` E1 is green on the
   incoming run.
2. **What should happen to `2026-09-20-soco53g-prb-own-iso`?** It has been an unruled candidate for
   seven consecutive lanes. It is a measured `I` (inert) verdict — the lane that produced it recommended
   against promotion — and E13 will keep firing until you rule. **I recommend declining it and letting
   the next promoting session prune it.**

**NOTE ON THIS CONTAINER (rule 31, final bullet):** the arm's composed bundle, the three legs, the
recovered SOCO-54 legs and the recovered fat keeper are all on **local disk and gitignored**, and **will
not survive this session's reclamation**. What survives is what this lane committed: the registered
composite, its sidecar and payload, the re-scored keeper, the rebuilt bench parts and every number in
this document.

---

## 12. CODA — THE OWNER RULED, AND THE PROMOTION WAS EXECUTED IN THIS SESSION

**Written after §§1–11, which were composed while the promotion was still open. Those sections are
left as they stood; this coda records what changed rather than rewriting the record.**

The owner ruled, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a keeper."*

**SOCO's keeper is now `2026-09-20-soco55-peryear-gas-basis`.** Rule 35 `[R-PROMOTE]` was executed
in this session, in order:

- **(b)** the year union `{2023, 2024, 2025}` was enumerated over all three registered SOCO sidecars
  **before** anything was deleted;
- **(c)** the incoming keeper covers that union in one composed span — **the promotion shrinks nothing**;
- **(e)** the new designation was written and `audit_keepers` re-run, resolving the incoming keeper's
  three stores, **before** `prune_iso_runs` touched anything;
- **(a)** the outgoing keeper's **three stores** were then deleted together — registry sidecar,
  `runs/<id>.js` payload and `results/calibration/soco54_marginal_gas`. Its bundle is recoverable from
  git history at this branch point.

**`2026-09-20-soco53g-prb-own-iso` was deliberately NOT pruned** (passed to `--keep`). The ruling names
*the recommended candidate*, which is this lane's; it does not dispose of soco53g. Rule 31
`[R-RETAIN]` forbids deleting it and rule 30 `[R-TOUCHPOINT-FOLD]` (a) forbids inventing a stamp, so
**E13 still fires once — down from twice — and is RE-RAISED, not cleared.** §11's recommendation
stands: decline it, and let the next promoting session prune it.

**ON THE OWNER'S STANDARD, STATED PRECISELY, BECAUSE THIS CASE IS NOT THE ONE IT ANTICIPATES.** The
ruling contemplates structural gain paid for by a gate regression. **Here the gates do not move at
all**: determination `NOT-YET`, C1 13/14, C2/C4/C6/C8 PASS, 0 ledgered and 0 protective caveats,
`grade_summary` identical on both sides — and the single failing row is 2024 `CC_REGULAR`, in a year
this keeper's delta is **provably inert** in. What regresses is the **2023 residual** (§4.1), and rule
14 `[R-ACCURATE]` is the reason it is kept rather than reverted. The promotion buys **structure and a
named successor object** (§5), not a gate.

**Rebased onto `origin/main` before promoting** (27 upstream commits), and the numbers were
re-verified across them: both runs re-scored to their committed `metrics.json` byte-for-byte, same
determination, same single failing row. Two conflicts, both mechanical — 66 `mechanism-matrix.js`
hunks differing **only** in stale line-number anchors (verified programmatically, 66/66; this lane's
new base row sat outside every conflict region), and one additive tail collision in
`_CACHE_KEY_OPTIONAL_FIELDS` where SPP-66 and xiso-8 appended to the same HOUSE-3 slot, resolved by
**keeping both sides**, which is what that convention prescribes.

**One correction to §10 that the rebase forces, stated rather than left to be discovered.** The
shards were solved at pinned SHA `2a7901215f5f8d78835cf3e314caffe06d8c656b`, and the rebase means that
commit is **no longer an ancestor of this branch**. The pin is still an accurate record of what the
shards cloned — it is provenance, exactly as §10 says — but a reader should not expect to find it in
the branch's history. Nothing about the solves changed.

**A parity RED that is NOT this lane's, reported not touched:**
`results/calibration/nwpp44_takeorpay_2025` is a committed, unregistered bundle that arrived with the
upstream commits (NWPP-44, `ee276d87`); none of this lane's commits touch it. Rule 25 `[R-ISO-SCOPE]`
— it is that lane's to resolve.

**Post-promotion gates:** `check_mechanism_matrix --base origin/main` GREEN including keeper stamps
and §5.x prose headers (the shard's `keeper` + `gates` line and the §5.8 header were re-stamped in
this session per rule 28); `check_bench_freshness` **0 STALE**; `audit_keepers` holdout / marker /
status all pass, with the one expected E13 and the expected E11. `calibration-complete.json` carries
**no SOCO entry**, confirmed rather than assumed, so there was nothing to re-key there.

---

## Log entry

```
## soco-55 — 2026-09-20

TWO results; the first is a DATA decision this desk owed and it outranked the lever.

(1) THE BENCH. check_bench_freshness was RED for SOCO ALONE repo-wide -- 44 parts
checked, 3 STALE (a hard ::error) against 41 warning-level engine drift on every
other ISO. Rebuilt at HEAD (zero LP, 37 s) and the incumbent keeper
2026-09-20-soco54-marginal-gas-basis re-scored on it: 2024 CC_REGULAR crosses
+7.417 -> +7.505 TWh against a +/-7.47 band, on a -0.088 TWh change in that row's
benchmark ACTUAL, so C1 reads 13/14 and SOCO'S PUBLISHED HEADLINE MOVES OFF ITS
CEILING TO NOT-YET. PRECOMMIT-soco-54 P4 pre-registered exactly that row at 81 %
of its margin. NO DISPATCH MOVED: every keeper hourly sidecar is byte-identical to
the day it was solved and its 297 KB run payload re-renders byte-identical -- only
the benchmark moved, and the ceiling reading had rested on a bench that could not
be reproduced from the builder at HEAD. check_bench_freshness now reads 0 STALE.
The keeper's per-plant layer, believed lost with the SOCO-54 shard branches, was
RECOVERED AT ZERO LP: the refs are gone but the objects are still on the remote,
and git fetch origin <40-char-sha> retrieved all three legs; composed, they
reproduce the committed keeper's twelve hourly sidecars BYTE-FOR-BYTE.

(2) THE LEVER. Run 2026-09-20-soco55-peryear-gas-basis (bundle
results/calibration/soco55_peryear_basis), a registered CANDIDATE the owner has NOT
ruled on; the keeper is unchanged and nothing was pruned. ONE delta:
gas_basis_differential_measured_by_year = true. GAS_BASIS_DIFFERENTIAL['SOCO'] =
0.64 is the 2024 value applied to every year and its own comment calls it a
"forward-year / fallback value only", but SOCO-54 promoted that fallback onto
SOCO's PRIMARY backcast gas path -- so 2023 carried +0.15 $/MMBtu (~+$1.65/MWh) on
every SOCO gas unit. SOCO-54 declared the imprecision against itself and ROUTED the
repair; this lane took it on the source-data citation (rule 23), re-deriving at HEAD
and reproducing SOCO-20's committed comment exactly: +0.4931 / +0.6395 / +0.6540,
registered at the 2dp every other GAS_BASIS_DIFFERENTIAL row carries -- a convention
fixed BEFORE the solve, whose declared consequence is that 2024 is byte-identical.

THE RESULT IS AGAINST THE LANE AND THE INPUT IS KEPT ANYWAY. The 2023 residual gets
LARGER: CT_PEAKER 10.668 -> 11.413 TWh (actual 4.503; share +2.56 -> +2.87pp of a
+/-3.00pp cap, headroom collapsing 0.44 -> 0.13pp), COAL_PRB 21.722 -> 20.443
(22.151), CC_REGULAR 112.126 -> 112.312 (107.960); only ST_GAS improves, 3.986 ->
4.293 (10.442). Every row still PASSES, C1 stays 13/14 with the SAME single failing
row, determination NOT-YET -- which PRECOMMIT-soco-55 P7 pre-registered verbatim.
Rule 14 [R-ACCURATE] is the governing text: a worse fit after an accurate input is a
DISCOVERED BUG, not a reason to revert to an estimate that was silently compensating.

WHAT IT LOCALIZES, the lane's real product: 95 % of the 1.279 TWh coal displacement
is ONE PLANT -- 6002 James H Miller Jr, 15.838 -> 14.626 against a 15.701 actual --
and about half the energy it sheds lands on merchant turbines already far above their
actuals (55409 Calhoun +0.115 vs 0.026; 55061 Tenaska Georgia +0.111 vs 0.238; 7709
Dahlberg +0.109 vs 0.243) while the other half lands correctly on 2049 Jack Watson
(+0.147 toward 3.270, partially repairing SOCO-54's routed miss) and 728 Yates
(+0.087 toward 2.239). THE NAMED SUCCESSOR IS THE CT_PEAKER / COAL_PRB MERIT ORDER,
NOT THE GAS BASIS.

GOVERNANCE. ZERO free parameters (n_residual unchanged at 1); ONE new default-off
ScenarioConfig gate, registered in _CACHE_KEY_OPTIONAL_FIELDS at "False" in the same
commit as the field so NO pre-existing cache key moves; declared in
solve_surface_declared at its live hash (SOCO 182 -> 183 rows, moved_rows {}); the
SCALAR machine-verified UNTOUCHED at 0.64, because this lane GATES it rather than
editing it. Rule 19 at two grains before the solve: the six GAS classes move on
fuel_prices AND mc_base, every other class at max |delta| EXACTLY 0.000000000000 in
all three years, and 2024 is 0.000000000000 at BOTH grains -- confirmed byte-identical
on all eight 2024 artifacts including dispatch/2024_P1.parquet and floors/2024_P1.npz.
Rule 25: the measured table carries a SOCO row AND NOTHING ELSE, machine-verified.
ALL FOURTEEN pre-registered predictions HELD; the declared #1 risk (2023 CT_PEAKER
crossing to FAIL) materialised SHORT of a flip and is reported at full magnitude.
C2/C4/C6/C8 PASS, C3a/b/c UNSCORABLE, 0 ledgered and 0 protective caveats, rule 17
holds in all fifteen plant-years, D-1 carries the same three COAL_BIT failures as the
keeper. Three shards, one year each (rule 36), pinned to 2a790121, 2.60-2.65 GiB peak
and 107-118 s each; all three ARCHIVED after fetch + checkout + verify.

REPORTED, NOT TAKEN: other ISOs DO carry constant-multiplier contract families.
Measured zero-LP with SOCO-54's own method (largest set of reporting plants whose
monthly delivered-price ratio series is flat at CV <= 0.001), 2023/2024/2025: SPP
6/63, 50/60, 50/54 -- on a keeper that ARMS gas_plant_monthly_fuel_pricing; ERCOT
9/20, 10/23, 26/26; SOCO 7/24, 8/25, 8/26; MISO 7/102, 7/98, 6/100; PJM 6/26, 6/25,
6/23; NWPP 3/28, 4/29, 3/26; NYISO and CAISO NONE in any year; NEISO void at 1
reporting plant. Rules 25 / 28(d): no other ISO's cell is filled and no verdict
transfers.

GATES. check_bench_freshness 0 STALE (cleared by this lane). check_mechanism_matrix
--base origin/main PASS, "1 new field(s) all registered". audit_keepers --iso SOCO:
E13 fires for the SEVENTH consecutive lane on 2026-09-20-soco53g-prb-own-iso, an
unruled candidate -- RE-RAISED, NOT CLEARED, and the owner is asked for a ruling;
E11 expected; S1 went stale on the bench rebuild and WAS repaired.
check_registry_payload_parity RED LOCALLY / GREEN IN CI on this session's own
gitignored bundles, all verified check-ignore-clean with 0 tracked files -- no result
deleted. check_cache_key_registration still RED at HEAD for PPA_COST_RECOVERY_YR and
REGIONAL_RENEWABLE_CF; this lane declared its OWN name only. tests/unit/config +
tests/regression/test_persisted_identity.py fail 11 at origin/main and 11 with this
change, measured both ways in a clean worktree: ZERO new failures.

PROMOTION IS OPEN AND IS THE OWNER'S (rule 31). Recommendation: PROMOTE, on rules 1
and 14 and explicitly NOT on the residual, which got worse. Cost from the current
state: ZERO re-solves. Record: docs/handoffs/PRECOMMIT-soco-55-2026-09-20.md,
docs/handoffs/FINDING-soco-55-2026-09-20.md.
```
