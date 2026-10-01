# PRECOMMIT — SOCO-55 (2026-09-20)

**Lane** SOCO-55 · **Model** Opus · **DATA PROFILE** `soco` · **Parent LP cost: ZERO** (rule 32(a)).
Written and pushed BEFORE any arm is solved, so nothing below can be written to fit a result.

---

## 1. TWO OBJECTS, IN THE HANDOFF'S OWN ORDER

**(1) THE BENCH — TAKEN, DONE, ZERO-LP, AND IT CHANGES THE PUBLISHED HEADLINE.**
**(2) `GAS_BASIS_DIFFERENTIAL["SOCO"]` PER-YEAR — the lane's solved arm.**

Item (1) outranks every lever and it is finished before item (2) is launched, because item (2)
must be scored against the true bench, not the stale one.

---

## 2. ITEM (1) — THE BENCH IS REBUILT AND THE KEEPER NOW READS `NOT-YET`

`check_bench_freshness` was **RED for SOCO ONLY**, repo-wide: 44 parts checked, **3 STALE**
(SOCO 2023/2024/2025 — a hard `::error`), 41 warning-level engine drift across every other ISO.

Rebuilt at HEAD (`--rebuild-benchmark`, 37 s, no LP), re-rendered and re-scored:

| | committed (stale) bench | **rebuilt bench** |
|---|---|---|
| determination | `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` | **`NOT-YET`** |
| C1 | 14/14 PASS | **13/14 — 2024 `CC_REGULAR` FAILS** |
| 2024 `CC_REGULAR` | +7.417 TWh of ±7.47 (PASS by 0.05) | **+7.505 TWh of ±7.47 (FAIL by 0.035)** |
| C2 / C4 / C6 / C8 | PASS | PASS |
| caveats | 0 ledgered, 0 protective | 0 ledgered, 0 protective |

**SOCO-54 PRE-REGISTERED THIS** (`PRECOMMIT-soco-54` §8 P4, at 81 % of margin) and its FINDING
put it in the headline. It is not a regression discovered late; it is a pre-declared risk
materialising once the data decision the SOCO desk owed was actually taken.

**What moved in the bench** (committed → rebuilt, `classFull` TWh):

| year | class | committed | rebuilt | Δ |
|---|---|---|---|---|
| 2023 | `CC_REGULAR` | 107.829 | 107.960 | **+0.131** |
| 2023 | `COAL_PRB` | 22.374 | 22.151 | −0.223 |
| 2023 | `ST_GAS` | 10.483 | 10.442 | −0.041 |
| 2023 | `CT_PEAKER` | 4.534 | 4.503 | −0.031 |
| **2024** | **`CC_REGULAR`** | **104.997** | **104.909** | **−0.088 ← the flip** |
| 2024 | `CT_PEAKER` | 4.785 | 4.816 | +0.032 |
| 2025 | `CC_REGULAR` | 113.318 | 110.605 | −2.713 |
| 2025 | `COAL_PRB` | 28.333 | 27.445 | −0.889 |
| 2025 | `COAL_BIT` | 14.942 | 14.535 | −0.407 |

Net `classFull` change −0.212 / −0.155 / **−4.523** TWh. 2025's C1 rows are SKIPPED on the
preliminary EIA-923 vintage, so 2025's large move changes no verdict — but it changes every
2025 actual this desk quotes. **2023 `CT_PEAKER` still PASSES on the rebuilt bench**
(+6.164 TWh / +2.56pp against ±7.18 / ±3.00), so SOCO-54's headline result survives the
rebuild; only the 2024 row does not.

**THE KEEPER'S PER-PLANT LAYER WAS RECOVERED AT ZERO LP, AND RULE 33(d) IS TOO PESSIMISTIC.**
The handoff said a leg recovery must be costed as a re-solve because the SOCO-54 PR's merge
deleted the shard branches. The branch REFS are indeed gone — but the OBJECTS are still on the
remote, and `git fetch origin <40-char-sha>` retrieves them:

| leg | SHA | files |
|---|---|---|
| `soco54_arm_2023` | `0ccc7271232fc6bd1fdaf98a4b7e6080c97e3afd` | 16 |
| `soco54_arm_2024` | `a4cf3a5f29e822ff8239752974fb1ddbf73d72d0` | 16 |
| `soco54_arm_2025` | `50e747ca4cd11008d831f1679f9a5bde638e482b` | 16 |

Composed with `scripts/probes/soco54_compose_span.py --expect-print false`, the result reproduces
the committed keeper's **twelve `hourly/` sidecars BYTE-IDENTICALLY** (sha256 match on all
twelve), and its `meta.json` differs from the committed keeper's in **exactly one key** —
`shared_inputs`, the three benchmark frames `--rebuild-benchmark` re-points. **The recovered
composite IS the keeper.** This is a finding about the environment, not a licence: the retention
window is not documented and not guaranteed, so **rule 33(f)'s instruction stands — land what
must survive on `main`** — but a lane facing a "lost" leg should TRY the SHA fetch before costing
a re-solve.

---

## 3. ITEM (2) — THE ARM

**ONE delta**: `gas_basis_differential_measured_by_year = True`, SOCO only.

### 3.1 What is wrong, measured rather than argued

`GAS_BASIS_DIFFERENTIAL["SOCO"] = 0.64` is **the 2024 value applied to every year**, and its own
comment registers it as a *"Forward-year / fallback value only — the SOCO backcast prices gas per
plant off EIA-923 monthly delivered cost like PJM/NYISO."* **Since SOCO-54 that sentence is false**:
turning `gas_plant_monthly_fuel_pricing` off put this declared FALLBACK on SOCO's **PRIMARY**
backcast gas-pricing path, where `resolve_annual_gas_price` returns `gas_price_override + 0.64`
for every SOCO gas unit in every year.

**Re-derived at HEAD by this lane**, reproducing SOCO-20's committed numbers exactly —
quantity-weighted EIA-923 Schedule-2 delivered gas cost to the run's own EIA-860 SOCO gas fleet,
minus the Henry Hub annual mean:

| year | plants | quantity (MMBtu) | q-wt delivered | Henry Hub | **basis** | applied | **error** |
|---|---|---|---|---|---|---|---|
| 2023 | 26 | 646,487,128 | 3.0288 | 2.5357 | **+0.4931** | 0.64 | **+0.15** |
| 2024 | 27 | 650,711,973 | 2.8320 | 2.1925 | **+0.6395** | 0.64 | **0.00** |
| 2025 | 27 | 641,283,196 | 4.1829 | 3.5289 | **+0.6540** | 0.64 | **−0.01** |

At ~11 MMBtu/MWh, 2023 carries **≈ +$1.65/MWh on every SOCO gas unit**. This is rule 23
`[R-FROZEN-DERIVE]` — a re-derivation cited to **source data**, never to a residual — and rule 14
`[R-ACCURATE]`, which says prefer the accurate input and, if the fit gets worse, treat that as a
discovered bug rather than burying it back in an inaccurate input.

**PRECISION IS THE FAMILY CONVENTION, FIXED BEFORE THE SOLVE.** Every row of
`GAS_BASIS_DIFFERENTIAL` is 2dp and SOCO-20's comment publishes this derivation's own output at
2dp, so the table lands at 2dp. **A consequence, declared here rather than discovered later: at
2dp the 2024 value is unchanged, so 2024 is predicted byte-identical.** Choosing 4dp instead
(0.6395) would perturb the 0.035-TWh-margin 2024 row, and picking a precision by what it does to
a row is exactly the selection rule 1 `[R-STRUCT]` forbids. The 4dp values are recorded in the
table's comment for the record.

### 3.2 The mechanism — zero free parameters, inert everywhere else

* `GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR: dict[str, dict[int, float]]` (`fuel_trajectories.py`),
  **SOCO only**, values as measured above. Rule 25 `[R-ISO-SCOPE]`: no other ISO has a row, and a
  peer lane wanting one derives it from its own receipts.
* `ScenarioConfig.gas_basis_differential_measured_by_year: bool = False` — a gate, not a knob, so
  the repair is an auditable single-delta A/B against the incumbent keeper rather than a constant
  edit that re-keys a keeper with no control.
* `resolve_annual_gas_price`: the year's own measured basis **REPLACES** the scalar
  (rule 19 `[R-ONE-MECH]` — one basis, never scalar-plus-adjustment). Any (iso, year) with no
  measured row falls through to the scalar unchanged.
* Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"`
  in the same commit as the field (the nyiso-119 discipline), so **no pre-existing cached run is
  re-keyed**; and declared in `solve_surface_declared` at its live hash.

**Rule 13 `[R-MEASURED]` forward test: PASSES.** The same quantity is producible for a forward
year from that year's own receipts and responds to changed conditions; where receipts do not
exist the forward scalar is used unchanged, so the forecast methodology is untouched. Verified
zero-LP: SOCO 2030 armed = 5.12 = SOCO 2030 unarmed.

### 3.3 Rule 19 `[R-ONE-MECH]`, MECHANICALLY, AT TWO GRAINS, BEFORE THE SOLVE

`_soco54_phase0.py rule19 --set gas_basis_differential_measured_by_year=true`:

| year | `fuel_prices` max\|Δ\| | `mc_base` max\|Δ\| | classes that move |
|---|---|---|---|
| 2023 | 0.177000000000 | 2.588654953887 | the SIX gas classes ONLY |
| **2024** | **0.000000000000** | **0.000000000000** | **none** |
| 2025 | 0.011800000000 | 0.172576996926 | the SIX gas classes ONLY |

`COAL_PRB`, `COAL_BIT`, oil, nuclear, hydro, wind, solar and biomass are at max\|Δ\| **exactly
0.000000000000** in all three years. (The 0.177 against a 0.15 $/MMBtu basis delta is
`GAS_MONTHLY_SEASONALITY`'s 1.18 peak month — the shape multiplies the level, as it does for the
scalar.)

**Every peer ISO is inert by construction and by measurement**: `resolve_annual_gas_price` is
identical armed and unarmed for ERCOT / CAISO / MISO / PJM / NYISO / NEISO / SPP / NWPP.

### 3.4 THE MERIT-ORDER DISTANCE, MEASURED BEFORE PREDICTING ANYTHING (check A)

The handoff requires the distance be named, and notes this is a **COMMON level shift**, so the
object is the **gas block against COAL**, not CT against ST. Measured on the keeper's own
committed `unit_hourly_<y>` + `system_<y>`, P1:

| 2023 band | coal running within the band BELOW the price (displaceable) | idle gas capacity within the band ABOVE the price |
|---|---|---|
| ±0.5 | 0.466 TWh | 4.365 TWh |
| ±1.0 | 0.663 TWh | 8.402 TWh |
| **±1.5** | **0.956 TWh** | 11.761 TWh |
| ±2.0 | 1.299 TWh | 14.077 TWh |
| ±3.0 | 2.501 TWh | 20.135 TWh |

The arm's 2023 mc cut is **$1.1–2.6/MWh** (fuel × heat rate: CC ≈ 1.13, ST ≈ 1.58, CT ≈ 1.73,
class maxima 1.435 / 2.475 / 2.589), so **≈ 0.96 TWh of coal is inside the reachable band** —
against 33.393 TWh of coal dispatched. **That is the distance: ~2.9 % of coal energy is exposed,
and the displaceable set is the upper bound on the move.**

**Greedy re-stack** (zero-LP; floors, commitment and network IGNORED, so a **lower** bound):

| year | `COAL` | `CC_REGULAR` | `CT_PEAKER` | `ST_GAS` |
|---|---|---|---|---|
| 2023 | **−0.371** | +0.329 | +0.043 | −0.001 |
| 2025 | **0.000** | 0.000 | 0.000 | 0.000 |

**The shift is uniform in $/MMBtu, not $/MWh**, so a high-heat-rate CT gets a LARGER $/MWh cut
than a low-heat-rate CC. The gas stack's internal spread therefore compresses **downward** and
`CT_PEAKER` gains slightly within the gas block as well as against coal. That is why P3 below is
the lane's stated risk.

---

## 4. PREDICTIONS, EX ANTE, WITH FALSIFIERS NAMING THE OBJECT AND A MAGNITUDE

Bands are **DELIBERATELY WIDE on every second-order class** (check C). SOCO-54 falsified three of
twelve predictions and all three were second-order, because a gas reprice changes the **P0 run
pattern the campaign floor is detected from**. I expect that here and band for it.

| # | prediction | falsifier |
|---|---|---|
| **P1** | 2023 coal (`COAL_PRB` + `COAL_BIT`) **FALLS**. Point **−0.4 TWh**; band **−0.05 to −1.6 TWh** | outside the band, or rising |
| **P2** | 2023 `CC_REGULAR` **RISES**. Point **+0.33 TWh**; band **0.0 to +1.2 TWh** | outside the band |
| **P3** | 2023 `CT_PEAKER` **RISES**. Point **+0.05 TWh**; band **0.0 to +0.8 TWh** | outside the band |
| **P3-RISK** | **STATED RISK, THE LANE'S #1**: 2023 `CT_PEAKER` sits at **+6.164 TWh of ±7.18** and **+2.56pp of ±3.00pp** — 1.02 TWh / 0.44pp of headroom. A rise past ≈ **+1.0 TWh** flips it to FAIL and costs a second C1 row. I judge this **unlikely** (the re-stack says +0.043, the band tops at +0.8) but it is declared here at full magnitude, before the solve | 2023 `CT_PEAKER` FAILs |
| **P4** | 2023 `ST_GAS` moves **< ±0.6 TWh** (re-stack −0.001, widened for campaign-floor re-detection) | outside ±0.6 |
| **P5** | **2024 IS BYTE-IDENTICAL TO THE KEEPER.** `fuel_prices` and `mc_base` are both exactly 0.000000000000 and rule 36 `[R-YEAR-ISOLATION]` removes every cross-year channel, so the 2024 LP input is identical | ANY sha256 difference on `dispatch/2024_P1.parquet`, `hourly/*_2024.parquet` or the 2024 slice of `system.parquet` |
| **P6** | every 2025 class moves **< 0.15 TWh** (re-stack exactly 0.000; +$0.10–0.17/MWh) | any 2025 class moving ≥ 0.15 TWh |
| **P7** | **THE 2024 `CC_REGULAR` C1 ROW IS UNCHANGED AT +7.505 TWh OF ±7.47 AND STILL FAILS. THE DETERMINATION STAYS `NOT-YET`.** This arm **cannot** close SOCO's failing row and is **not taken to** — it is taken on rules 14/23 | 2024 `CC_REGULAR` moves at all |
| **P8** | no 2025 C1 class row changes status (all SKIPPED, preliminary vintage) | any 2025 row scored |
| **P9** | C2 / C4 / C6 / C8 all PASS; **0 ledgered, 0 protective** caveats; C3a/b/c UNSCORABLE | any other criterion moving |
| **P10** | DOF ledger gains **3 entries** (the three measured basis values, identification source = the EIA-923 / Henry Hub derivation); `n_residual` unchanged at **1**; **zero free parameters** | a residual-identified entry appears |
| **P11** | rule 17 `[R-FLOOR-WINDOW]` holds in **all fifteen plant-years**. **I DECLINE TO PREDICT THE DIRECTION OF FLOOR BINDING** — SOCO-54's P11 got the gate right and the direction wrong, for a reason that applies verbatim here | any plant-year breaching its measured synchronized share |
| **P12** | `ST_GAS` forced share stays **under the 0.30 merchant cap** in all three years; **direction unpredicted** (SOCO-54's P12 was falsified on direction) | C8 FAIL |
| **P13** | every peer ISO byte-identical; **no pre-existing cache key moves** | any peer key or number moving |
| **P14** | solve-surface rows SOCO **182 → 183**, `moved_rows("SOCO") == {}` | a moved row |

**MEASURED ALREADY (P13/P14 are discharged zero-LP before the solve):** peer `resolve_annual_gas_price`
identical for all eight; `moved_rows("SOCO") == {}` at 183 rows; `tests/regression/test_persisted_identity.py`
**6 failed / 18 passed both with and without this change** — the six are the pre-existing
`PPA_COST_RECOVERY_YR` / `REGIONAL_RENEWABLE_CF` fingerprint failures RED at HEAD, and this lane
adds **zero** new failures.

---

## 5. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — FORM 4, NO CONTROL SOLVE

The control is the incumbent keeper's **committed bundle**, `2026-09-20-soco54-marginal-gas-basis`
(`results/calibration/soco54_marginal_gas`), re-scored by this lane on the rebuilt bench.

The keeper's basis SHA is `d85e0c47`, and this lane's arm is solved at the SHA this PRECOMMIT
lands on. The solve-path diff between them is **this lane's own five files and nothing else** —
the four mechanism files plus `solve_surface_declared.py` — every one of which is the arm under
test and is **default-off**. There is therefore no third-party LIVE hunk to void form 4, and no
control solve is spent. (The bench rebuild of §2 changes no solve-path code at all: it rewrites
benchmark frames and `meta.json`, which the scorer reads and the LP does not.)

---

## 6. SOLVE SHAPE

Rule 36 `[R-YEAR-ISOLATION]` (a): **ONE SHARD PER YEAR**, three shards, composed in the parent at
zero LP. 2024 is solved rather than asserted inert, so P5 is **verified** rather than claimed.
Each shard pushes its FULL bundle including `dispatch/<y>_P1.parquet` and the bundle-root
`system.parquet` (rule 34 `[R-SHARD-PROMOTABLE]` (a)), negates `results/calibration/_shared/SOCO`
so the parent does not have to repair it, and passes `--note` (rule 32(c) and SOCO-54's §9 item 5).

---

## 7. THE DEFINING CONSTRAINT, UNCHANGED

**SOCO HAS NO PRICE BENCHMARK AND NEVER WILL.** `actual_lmp.json` carries no SOCO block and must
not gain one. C3a/C3b/C3c are **UNSCORABLE, not failed**. The ceiling is
`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can never read `CALIBRATED`. Every
`offer_curve_by_group` band stays exactly **1.0**, `authorized_price_tuning` is declared **NONE**
in prose and **no such key** goes in the attestation's governance block. Gate G17 stands
absolutely: no neighbouring hub, no proxy, no cost-stack price, ever.
