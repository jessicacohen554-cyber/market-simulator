# RESULT — SPP-47 (2026-09-18): SPP's four rubric failures on the 2019–2022 rung, at ZERO LP

**Base:** `8f0d41df86d497fcb502b9a3ea3cbe135ba54b7d`.
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`) — **UNCHANGED**.
**2019–2022 rung:** `2026-09-16-spp-43-outage-intake` (`spp43_holdout_span`) — **UNCHANGED**.
**LP spent: none. Bundles produced: none. Runs registered: none. Cells armed: none.**
**Shards launched: none** (rule 32 `[R-SHARD]` (a): the parent never solves, and nothing
survived phase 0 that needed solving).

---

## 0. Headline

Four things, in descending order of how much they change what the next lane does.

1. **THE BRIEF'S CENTRAL HYPOTHESIS IS REFUTED.** "2020's COAL_PRB shortfall is the single
   thread that ties three of the four criteria together" is **false**. C3a/C3b-2020 are not
   a coal-volume defect at all: the model's monthly price error is **positive in 10 of 12
   months**, `corr(price error, model coal) = −0.292`, and the model's cheapest month is
   **$16.46 against the market's $9.65**. The model captures **44 %** of the real monthly
   price variation. C3a/C3b is a **price-FLOOR** defect — the model has no price-setter
   below coal SRMC — and it is the same object in all three failing years.
2. **A CONFINED, MATERIAL, ZERO-DOF INPUT DEFECT IS FOUND AND ROOT-CAUSED** (rule 14
   `[R-ACCURATE]`): under `eia860_vintage_tracks_solve_year`, a plant that retires **during**
   its own native vintage year is dropped from that year's fleet entirely. In SPP 2019–2022
   the entire material footprint is **one plant in one year** — **Oklaunion (127), 720 MW,
   1,209.2 GWh metered May–Sep 2020**, which is **11.1 % of the failing 2020 COAL_PRB row**.
3. **DO NOT REBUILD SPP'S BENCHMARK YET.** The brief instructed a rebuild if the actuals
   move. They do — but the rebuild is **one-sided**: it makes one correct repair and one
   **regression** that would delete Oklaunion's 1.209 TWh of real metered coal from the
   2020 *actual*, silently shrinking a failing criterion by 11 % for the wrong reason
   (rule 13 `[R-MEASURED]`, rule 14). **The keeper's own benchmark reproduces byte-exactly,
   so SPP's CALIBRATED headline was never at risk.**
4. **C1's four failing rows are TWO objects, not one**, and neither is 2020-specific.
   COAL_PRB and CC_REGULAR are an antisymmetric pair (`r = −0.971`) whose split error is
   **monotonic in the gas price** (`r = +0.885`, slope **+4.081 TWh per $/MMBtu**). ST_GAS
   is short **4.6–4.9 TWh in every single year**, independent of gas price — a separate,
   already-routed object (SPP-63's successor R-ba).

Rule 30(c) is untouched: this is a held-out rung, it reports and cannot decertify, and
SPP's headline stays **CALIBRATED** on 2023–2025.

---

## 1. The stale-benchmark triage, discharged first

The brief required this before any C1 number was trusted. `check_bench_freshness.py --iso SPP`
reports **7 of 7 parts STALE**, all on `(unresolvable: unknown builder state)` — the recorded
aggregate stamp `bee29e135d42` cannot be resolved to a payload fingerprint, so the parts
*cannot be shown* to reproduce. That is a statement about provenance, not about the numbers.
The numbers are a separate question, and it is answerable at zero LP.

**Method.** `run_calibration_full.py --rebuild-benchmark <bundle>` is pure post-processing —
the benchmark frames are pure functions of `(year, iso)` and the reference data and do not
touch the dispatch, so this is zero-LP and belongs in the parent. The shared inputs are
**content-addressed**, so a rebuild that reproduces writes *the same filename*. That makes the
test exact rather than approximate.

### 1.1 The keeper (2023–2025) reproduces EXACTLY

`spp42_span_a` is committed slim, so `report_run` fails at the end of the rebuild — but the
shared-input write happens first. Run on a copy, all **8 of 8** shared inputs reproduce to the
same content hash the committed `meta.json` records:

| input | committed | rebuilt at HEAD |
|---|---|---|
| `eia923` | `7da41467dba7` | **`7da41467dba7`** |
| `eia930` | `017f3b3531c0` | **`017f3b3531c0`** |
| `campd` | `85eb94dac24b` | **`85eb94dac24b`** |
| `unit_outages{,_short,_partial,_e923,_layup}` | (5) | **all 5 identical** |

**SPP's CALIBRATED determination is not at risk from the staleness flag.** Note in passing
that none of those three files is committed (the keeper is slim), so the keeper's `meta.json`
references shared inputs absent from a fresh checkout; they regenerate in ~2 min by the command
above. Reported, not repaired — not this lane's object.

### 1.2 The rung (2019–2022) moves in exactly three class-years

| year | class | committed | HEAD | Δ TWh |
|---|---|---|---|---|
| 2020 | COAL_PRB | 67.0581 | 65.8489 | **−1.2092** |
| 2021 | ST_GAS | 9.6509 | 9.9101 | +0.2591 |
| 2022 | ST_GAS | 10.8470 | 11.0998 | +0.2527 |

Everything else is byte-identical. Resolved to **two plants**:

* **Plant 6193, ST_GAS 2021/2022 — HEAD IS RIGHT.** New COAL_PRB + ST_GAS sums to
  **5,140,010 MWh** in 2021 against CAMPD's **5,140,010 MWh** — an exact reconciliation to the
  meter. The committed value under-counted ST_GAS by 259,133 MWh. This half is a genuine repair.
* **Plant 127, COAL_PRB 2020 — HEAD IS A REGRESSION.** 1,209,201 MWh is **dropped entirely**
  (`left_only`). §2 shows the energy is real, metered, and SPP's.

**A methodological note that cost this lane two hours.** A hand-rolled reconstruction of
`_benchmark_eia923_frame` disagreed with the committed part on classes the clean test says are
stable (e.g. 2019 CC_CHP, +0.87 TWh), because it did not reproduce the bundle's own
`btm_backfill_year` / `mustrun_chp_btm_holdout` settings and because `classFull` mixes EIA-923
with EIA-930-sourced classes. **It was discarded.** Every number above is from
`--rebuild-benchmark` on the bundle itself, which is the only construction that carries the
bundle's own settings. A second probe that scored "unmapped" plants against the shared `campd`
frame returned **581 TWh** for a ~250 TWh ISO — the frame is **state**-scoped, not ISO-scoped —
and was discarded too. Both are recorded because both were *plausible* and both were silently
wrong, which is the SPP-45 lesson applied to this lane's own work.

---

## 2. The root cause: a plant that retires mid-vintage-year is dropped from that year

Plant 127 is **Oklaunion**, `ba_code = SWPP`, sub-bituminous ST — a real 720 MW SPP coal plant.

**It is in the LP fleet in 2019 and absent in 2020–2022** (measured on the committed
`dispatch/<year>_P1_fleet.parquet`, matching **both** SPP unit-id conventions per SPP-45 trap (a)
— `^127_` *and* `_p127_`; the prefix-only test would have reported it absent in 2019 too):

| year | fleet rows | plant 127 | pmax |
|---|---|---|---|
| 2019 | 1126 | **`COAL_SPP-North_p127_{mustrun,committed,econlo,econhi,peak}`** | 650.0 MW |
| 2020 | 1110 | **absent** | 0.0 |
| 2021 | 1109 | absent | 0.0 |
| 2022 | 1094 | absent | 0.0 |

**But it ran for most of 2020.** Metered, by month (GWh):

| | Jan–Apr | May | Jun | Jul | Aug | Sep | Oct–Dec |
|---|---|---|---|---|---|---|---|
| CAMPD 2020 | 0 | 92.5 | 222.6 | 288.9 | 334.9 | 270.2 | 0 |

**1,209.2 GWh, May–September 2020.** EIA-923 reports 1,100,658 MWh of SUB for the same year.

**The mechanism, from EIA's own contemporaneous vintages:**

| | plant 127 |
|---|---|
| `vintage_2019/eia860_generator_operable.parquet` | Status **OP**, *Planned* Retirement **9/2020** |
| `vintage_2020/eia860_generator_retired_and_canceled.parquet` | Status **RE**, Retirement **9/2020** |

Oklaunion retired **September 2020**. `load_retired_within_window`'s docstring states the
assumption that makes this fail: *"A year-matched native vintage carries its within-window exits
in its own operable file and ships no retiree parquet, so this returns an empty list there — the
operable fleet already has them, and injecting again would double-count."* That holds for a plant
retiring **after** the vintage year. It is **false for a plant retiring during it**: the 2020
vintage's operable sheet is a year-end snapshot that has already moved Oklaunion to the retired
sheet, and the retiree-injection path is switched off precisely there. The plant vanishes, along
with its nine real operating months.

The machinery to handle it correctly **already exists** — the COD ramp is documented to
"dispatch each through its real retirement month and zero it after", and it keys on the same
plant code. What is wrong is the injection gate, not the ramp.

### 2.1 Footprint confinement — the whole SPP 2019–2022 exposure is one plant-year

Every SPP plant whose native vintage retires it **within** the solve year, against fleet presence
and metered energy:

| year | mid-year retirees (SPP) | missing from fleet **with** metered energy | energy lost |
|---|---|---|---|
| 2019 | 9 | **none** | **0.0 GWh** |
| 2020 | 11 | **Oklaunion (127)** | **1,209.2 GWh** |
| 2021 | 6 | **none** | **0.0 GWh** |
| 2022 | 11 | Ponca (762) | 47.8 GWh |

Every other mid-year retiree is either carried in the fleet (GREC 165, 540 MW, 2,615.4 GWh —
the machinery working) or has **zero** metered energy. Ponca's 47.8 GWh is the SPP-45 plant,
already measured there to sit behind an availability array that is identically zero, so it is
inert on both counts.

**So the defect is real, general, and — in this ISO and this rung — worth exactly one number:
1,209.2 GWh in 2020, or 11.1 % of the failing −10.85 TWh COAL_PRB row.** It is an **input**
defect with **zero free parameters** (the retirement month is EIA's own published field), so
under rule 13 `[R-MEASURED]` / rule 29 `[R-SCREEN]` it is a data repair and **takes no screen** —
the SPP-38/42/43/45 precedent.

**It does not close C1.** Best case −10.85 → −9.64 TWh, still a FAIL. Stated so the next lane
does not over-buy it.

### 2.2 Why the benchmark must NOT be rebuilt first

The two repairs point opposite ways. Rebuilding today applies both: it fixes 6193 **and** deletes
Oklaunion from the *actual*, shrinking the 2020 COAL_PRB miss by 11 % by removing real metered
generation rather than by dispatching it. That is "rescaling an input so the model's output lands
on the actuals" (rule 13) and "burying the error back inside an inaccurate input" (rule 14). The
governed order is **fleet first, benchmark second** — and once the fleet carries Oklaunion, the
benchmark question is moot, because the plant is then in the fleet map the builder keys on.

---

## 3. C1 is two objects, and the 2020/2022 sign flip is one of them

Measured against the **committed bench `classFull`** — which reproduces the brief's rows exactly
(2020 COAL_PRB −10.85, 2022 +8.01), confirming the basis:

| class | 2019 | 2020 | 2021 | 2022 |
|---|---|---|---|---|
| gas price $/MMBtu | 2.57 | 2.03 | 3.72 | 6.45 |
| **COAL_PRB** | −6.40 | **−10.85** | +5.34 | **+8.01** |
| **CC_REGULAR** | +4.72 | +4.19 | −5.84 | −6.82 |
| **ST_GAS** | −4.59 | −4.64 | −3.68 | −4.92 |
| CT_PEAKER | +2.63 | +7.59 | +1.47 | −1.14 |
| COAL_LIGNITE | −2.48 | −2.66 | −1.42 | −0.02 |
| wind | +8.23 | +8.74 | +9.50 | +10.90 |

**Object A — the coal↔CC crossover is too elastic.** COAL_PRB and CC_REGULAR are an almost
perfect antisymmetric pair, `r = −0.971`; their sum is −1.68 / −6.66 / −0.50 / +1.19. COAL_PRB's
error is **monotonic in the gas price**, `r = +0.885`, OLS slope **+4.081 TWh per $/MMBtu**,
zero-crossing at **$3.93/MMBtu**. The physics is visible in the inputs: SPP coal is
**$1.46–$1.82/MMBtu** across the window (§4) so coal SRMC is near-fixed at ~$16/MWh, while gas
SRMC swings from ~$14 to ~$45/MWh. The model follows that swing **all the way**; the market does
not. **This is the level miss, not a duration miss** — hours-on is ~8,760 for COAL_PRB in both
model and actual in every year, and the decomposition puts 98 %+ of the 2020 gap on
mean-output-when-on (−1,863.6 MW) rather than on hours (−43 h).

**Object B — ST_GAS is short 4.6–4.9 TWh in EVERY year**, with no gas-price dependence. That is
SPP-63's already-routed successor **R-ba** (the merit-order inversion: SPP gas steam offered
above CT_PEAKER at every stack depth to 6 GW despite a better capacity-weighted heat rate,
10.543 vs 10.974). Untouched by this lane; recorded as corroborated on a second, independent
year set.

**C4-2022 is Object A and B's arithmetic consequence, and it is a LEVEL defect** — as the brief
suspected. Decomposing `NRMSE²` into bias / scale / shape:

| year | model gas TWh | actual TWh | r | NRMSE | **bias** | scale | shape |
|---|---|---|---|---|---|---|---|
| 2019 | 72.078 | 75.725 | 0.913 | 0.195 | 6.1 % | 6.3 % | **87.6 %** |
| 2020 | 77.569 | 72.961 | 0.929 | 0.204 | 9.6 % | 14.5 % | **75.9 %** |
| 2021 | 44.304 | 61.042 | 0.937 | 0.341 | **64.5 %** | 0.6 % | 34.8 % |
| 2022 | 44.943 | 66.247 | 0.967 | 0.358 | **80.8 %** | 1.1 % | 18.1 % |

(CEMS-covered proxy basis; the scorer's own 2022 figures are r 0.957 / NRMSE 0.312, so the
attribution carries.) **2022's C4 failure is 80.8 % pure bias** — 21.3 TWh of missing gas, a 32 %
level shortfall — with near-perfect timing. There is also a clean **regime change at 2021**: the
gas failure switches from shape-dominated to bias-dominated, exactly where the gas price crosses
Object A's $3.93 zero-crossing.

---

## 4. Two hypotheses killed on measurement, so the next lane does not spend them

**Fuel-price data is NOT the cause of Object A.** Both legs were checked and both are clean:

* **Gas is already rich.** `gas_plant_monthly_fuel_pricing = True` **and**
  `f923_gas_price_plausibility_screen = True` are armed in `scenario_config` (they are *not* in
  `calibration_flags`, which is where a reader naturally looks and why the flat annual
  `gas_prices` scalar reads as the whole story — it is not). SPP-46's routed repair **R-1 is
  built and armed**.
* **SPP's coal price frame is clean.** Of **1,100** SPP coal plant-months 2019–2022:
  **0** at ≤ $0.00, **0** at ≤ $0.30, **0** at ≥ $6.00. Coverage 24 of 26 plants, 273–282 of 312
  plant-months every year. Quantity-weighted delivered price 1.535 / 1.457 / 1.503 / **1.822**
  $/MMBtu — plausible, and correctly rising into 2022. **The gas seam's garbage problem
  (SPP-46: 91 plant-months ≤ $0.50, 31 negative) has no coal analogue in SPP**, so the absence of
  a coal plausibility screen is not costing this ISO anything. Recorded because the asymmetry is
  otherwise an obvious thing for a later lane to go and re-measure.

**The 2022 slack is not a defect and not a coincidence with anything.** SPP-43's declared cost is
**563.6284 MWh in 4 zone-hours**, all SPP-South, in **two consecutive-hour pairs** (h3350–3351,
h6326–6327) at demand 19.4–22.5 GW. That is **0.0002 %** of 2022 load. 2019/2020/2021 carry
exactly **0.0000 MWh**. These are genuine scarcity hours, they touch C3c (auto-caveated on a
held-out year), and they are immaterial to C1, C3a, C3b and C4.

---

## 5. C3a/C3b: the brief's thread does not hold, and the real object is a price FLOOR

| year | actual monthly RT ($/MWh) | model | C3a | C3b |
|---|---|---|---|---|
| | mean / sd / min / max | mean / sd / min / max | | |
| 2019 | 20.86 / 2.98 / 13.61 / 24.51 | 22.31 / 2.14 / 18.88 / 25.64 | +7.0 % | 0.125 |
| **2020** | 16.48 / **4.52** / **9.65** / 24.87 | 20.31 / **1.97** / **16.46** / 23.74 | **+23.3 %** | **0.319** |
| **2021** | 38.47 / 46.95 / 10.20 / 192.25 | 40.23 / 39.27 / 15.95 / 168.35 | +4.6 % | **0.213** |
| **2022** | 43.90 / 19.47 / 18.75 / 80.82 | 42.37 / 13.31 / 24.73 / 66.23 | −3.5 % | **0.213** |

(C3b reproduces the brief's 0.319 / 0.213 / 0.213 **exactly**; C3a reproduces to rounding on a
load-weighted cross-zone mean.)

**The refutation.** If C3a-2020 were the COAL_PRB shortfall, the price error would concentrate
where coal is missing. It does not: `corr(monthly price error, model monthly coal) = −0.292`, the
model is **too expensive in 10 of 12 months** (mean overshoot **+$5.05**), and the single worst
month is **November** (+$11.06: actual $9.65, model $20.71) — a mid-range coal month. The other
three years give −0.491 / −0.237 / +0.063: no year supports the thread.

**The real object.** The model captures **44 %** of 2020's real monthly price variation
(sd 1.97 vs 4.52). Its **floor gap is +$6.81** — larger than its **mean** error of +$3.83. The
model cannot price below ~$16.5/MWh, which is coal SRMC ($1.46/MMBtu × ~10.5 heat rate). The
market reached $9.65. **The defect is the absence of a price-setter below coal SRMC**, and it is
the same object in all three failing years — 2021 captures 84 % of real dispersion, 2022 68 %,
each compressed at both ends.

This closes cleanly onto existing routed work rather than opening a new lane. SPP-64 established
the **ceiling** half (the model has nothing between the ~$74 top of its thermal stack and VOLL;
the tail is the RT/DA wedge and congestion, R-bc/R-bd). This lane adds the **floor** half, and
SPP-64 already supplies its mechanism: `spp_curtailment_ceiling` holds wind at its **CF upper
bound**, and *a unit held at its bound is never marginal*, so bounded-off wind cannot set a price
at all — the model's minimum price is exactly **−26.000** in every year and both zones (wind's
flat `-ira_ptc_wind` offer) and nothing sits between that and coal SRMC. Wind being long
**+8.2 to +10.9 TWh in every year** and the price floor being too high are therefore **the same
defect seen from two sides**, and **R-bc — curtailment entering as an LP constraint whose dual
reaches the zonal price — is the successor that addresses both.** It is already the routed
successor; this lane corroborates it from the price side on a second year set and adds nothing to
its queue position.

---

## 6. What this lane did NOT do, and why

* **No mechanism was tested**, so under rule 28(b) **no matrix cell is minted or moved**. The
  findings are an input defect (§2) and two corroborations of already-routed successors (§3, §5).
  `docs/codebase-site/data/mechanism-matrix/SPP.js` is annotated only where this lane's
  measurement bears on an existing cell's evidence, with the cell letter untouched.
* **No LP, no shard, no registration.** Nothing survived phase 0 that needed solving: the one
  actionable defect is a measured-input repair, which takes no screen.
* **DO-NOT-REDO was respected.** Nothing here re-tests the deliverability-keyed coal markup,
  `coal_fuel_inventory`, `coal_passthrough_sigmoids`, `mustrun_plant_exclusions`,
  `st_gas_mustrun_p25_level`, `unit_outage_short_windows_gas`, the P0-anchored
  `spp_gas_commitment_bridge` (either lane), the window variants, or the Ponca extract block.
  Object A (§3) is **not** the coal↔gas crossover lane SPP-44 adjudicated data-blocked: that
  adjudication covers coal **supply** constraints (deliverability markup, stockpile inventory)
  and rests on an identification failure against the MMU target. Object A is a statement about
  the **relative merit-order elasticity** of an already-clean coal price against an already-rich
  gas price, and it is offered as a **measurement**, not as a lever — no mechanism is proposed
  for it here.
* **Both SPP-45 traps were honoured.** Every fleet census matches both unit-id conventions
  (trap (a) — and it mattered: prefix-only reports Oklaunion absent in 2019, which would have
  destroyed §2's central contrast). No path-swapped measured input was compared in-process, so
  trap (b)'s `lru_cache` hazard was never reached.

---

## 7. Known defects, reported not patched (rule 25)

* **The parity gate is RED on two bundles, neither SPP's to prune** —
  `caiso279_ablate_dswcouple_span` (CAISO) and `soco15_spp_arm`. Re-confirmed still present at
  this base. `soco15_spp_arm`'s `meta.json` reads `iso = SPP` so it is nominally in SPP's
  rule-35(a) scope, but it is cited as live evidence across the SOCO, NWPP, PJM, MISO and NYISO
  lanes and rule 31 `[R-RETAIN]` reserves that call for the owner. **Unchanged; not pruned.**
* **`stamp_touchpoint_holdout.py`** still hardcodes NEISO-specific `[R-HOLDOUT]`-era caveat text
  onto every ISO's touchpoint. SPP's sidecar carries corrected text and **was not re-stamped by
  this lane because no run was registered** — no re-stamp is owed. It becomes owed the moment the
  rung is re-registered.
* **The keeper's shared benchmark inputs are not committed** (§1.1) — `meta.json` references
  three `_shared/SPP/` parquets absent from a fresh checkout. Regenerable; reported.
* **`check_bench_freshness.py` will keep reporting 7/7 STALE for SPP** until a rebuild lands,
  and §2.2 says a rebuild should wait for the fleet repair. The flag is **provenance**, and §1.1
  establishes the keeper's numbers reproduce regardless; a lane reading the flag alone would
  reasonably but wrongly conclude the keeper is at risk.

---

## 8. The promotion question (rule 31 `[R-RETAIN]`), asked explicitly

**There is nothing to promote and nothing at risk of being lost.** This lane produced no bundle,
spent no LP, and registered no run; the keeper and the rung are untouched at HEAD. The only
artifacts are this document and four regenerated `results/calibration/_shared/SPP/*.parquet`
files, left **uncommitted and untracked** — they are the §1 evidence and each regenerates in
~2 min from the command in §1. Nothing needs the owner's protection before this container is
reclaimed.

**What the owner is actually being asked to decide is the ORDER of two repairs**, because they
interact and the wrong order flatters a failing criterion:

1. **The fleet repair** — inject mid-vintage-year retirees when
   `eia860_vintage_tracks_solve_year` is on, so a plant retiring during its own vintage year
   keeps its real operating months (the COD ramp already zeroes it afterwards). Zero free
   parameters; a rule-14 input repair; **cross-ISO in reach** (it is a shared seam in
   `data/fleet/eia860.py`, so it is *not* SPP's to change unilaterally under rule 25
   `[R-ISO-SCOPE]` — it needs its own charter, and this lane deliberately did not build it).
   SPP's exposure is 1.209 TWh in 2020.
2. **The benchmark rebuild** — correct for plant 6193, a regression for plant 127, and safe only
   **after** (1) lands.

**Recommended: (1) then (2), and neither in this session.** If the owner prefers the benchmark
rebuilt now regardless, it should be done knowing it improves the 2020 COAL_PRB row by 11 % by
deleting real metered generation — which is the outcome rules 13 and 14 exist to prevent.

---

## 9. Successors, ranked

| # | object | status | why |
|---|---|---|---|
| **S-1** | mid-vintage-year retiree injection | **new, owed** | rule 14, zero DOF, root-caused in §2; cross-ISO seam so it needs its own charter |
| **S-2** | **R-bc** — curtailment as an LP constraint whose dual reaches the zonal price | already routed (SPP-64) | §5 corroborates it from the price side; it is the **only** object that addresses C3b's floor half, and the wind excess is its other face |
| **S-3** | **R-ba** — the ST_GAS/CT_PEAKER merit-order inversion | already routed (SPP-63) | §3 Object B: short 4.6–4.9 TWh in **every** year, gas-price-independent; corroborated on a second year set |
| **S-4** | the coal↔CC elasticity (Object A) | **measured, no lever proposed** | §3; `r = +0.885` vs gas price, slope +4.081 TWh/$; the honest statement is that SPP-44 killed the supply-side levers and this lane did not find a structural successor — it should not be closed by tuning |

**S-4 is the one to be careful with.** It is the largest single C1 residual and the most
temptingly closeable by an offer-curve multiplier. Rule 1 `[R-STRUCT]`'s carve-out cannot reach
it: the required correction changes **sign** between 2020 and 2022, and condition (b) requires
**one config across every scored year**. A multiplier that fixes 2020 makes 2022 worse by
construction. Recorded here so the next lane does not rediscover that the expensive way.
