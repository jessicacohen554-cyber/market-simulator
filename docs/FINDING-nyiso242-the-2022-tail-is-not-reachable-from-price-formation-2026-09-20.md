# FINDING — nyiso-242: the 2022 tail is worth 2.7× what the handoff estimated, and the successor it named cannot reach it

**Session** nyiso-242 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **this container ran ZERO LP and launched NO shard**).
**Date** 2026-09-20. **Base** `origin/main` at `e5f966fd`.
**Keeper under study** `2026-09-19-nyiso241-ct-committed-measured`, bundle `results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025}.
**Nothing was armed, screened, solved, promoted or registered. No `ScenarioConfig` field moves. No mechanism-matrix cell moves** — the object measured here is not a mechanism (the nyiso-239/240 precedent, `mechanism-testing-matrix.md:12729`).

> ## HEADLINE
> 1. **The object is correctly identified and BIGGER than the handoff said.** Closing the missed
>    RT tail is worth **$5.44/MWh** on 2022's load-weighted mean — **2.7× the "~$2/MWh" the
>    nyiso-241 record estimated** — and it takes **C3a-2022 from −10.77 % to −4.06 %** and
>    **C3a-2025 from −9.65 % to −4.71 %**, both from outside a ±10 % band to comfortably inside
>    it. This is the lane's highest-value object and the handoff was right to aim here.
> 2. **The successor the handoff named cannot reach it.** In the 100 missed hours of 2022 the
>    model holds **4,432 MW of capacity that is available and offering BELOW the $300 gate, and
>    is not dispatched** (30.3 % of its available thermal fleet). The energy-balance dual *is*
>    the marginal unit's offer, so while the LP can still buy a cheaper MW the energy price
>    cannot reach $300 — **no RCPF step, ORDC adder, reserve demand curve or offer-cap change
>    moves it.** A reserve product can add a reserve dual; it cannot move the energy dual, and
>    C3a/C3b/C3c are scored on the energy dual.
> 3. **This independently reproduces nyiso-233 with a different instrument.**
>    `FINDING-nyiso233-tail-is-an-availability-object-2026-09-13.md` §5 already concluded that
>    "ORDC / RCPF / reserve demand-curve work cannot close a gap in hours where the reserve
>    requirement is met, slack is zero and 3–6 GW sits idle". That measurement was **six days
>    older than the handoff that sent this session at price formation**. Two independent
>    instruments, same answer.
> 4. **The 2022 miss is TWO objects, not one, and they need different mechanisms.** A **winter**
>    cluster (70 of 100 h, Jan/Feb/Dec) at **58 % fleet utilisation** with **4,716 MW idle below
>    the gate** — availability or fuel, upstream of pricing — and a **summer** cluster (23 h) at
>    **85 %** with **1,733 MW** idle. Aiming one lever at their average would be aiming it at
>    neither.
> 5. **The nyiso-235 gas repair is working and deserves the credit.** On the two Elliott days
>    nyiso-232 measured at **$70.2 / $79.9** against **$383.0 / $747.8** actual, the current
>    keeper reads **$176.87 / $198.60** — a **2.5×** improvement from a data repair. Still short,
>    and the remaining shortfall is the object above.
> 6. **NO SHARD WAS LAUNCHED, deliberately.** Every adjacent lever is already adjudicated
>    (§5), and phase 0 forecloses the one that is not. Spending LP on it is what rule 1
>    `[R-STRUCT]` and the surviving zero-LP-first practice of rule 29 `[R-SCREEN]` exist to
>    prevent.

---

## 1. WHAT THE GATE ACTUALLY COMPARES — and the asymmetry favours the model

The C3c gate compares **two different statistics**, which is worth stating before any number
below is read:

* the **actual** side is the **simple mean of the eleven internal NYISO zones**
  (`derive_actual_lmp._nyiso_wide` → `actual_lmp_hourly_NYISO.parquet`, counted by
  `derive_actual_tail.py`);
* the **model** side is the **max zonal dual** (`calibration_verdict.score_price_tail` over
  `ordc.hoursGt200`).

The model is therefore scored on the **more generous** statistic — a max, against a mean — and
still misses. **The asymmetry cannot explain the miss; if anything it understates it.** This is
reported because it is load-bearing for reading §2, not as a criticism of the rubric.

The zonal reconstruction used below was validated against the committed gate series:
**max |Δ| $5.6e-05** over all 8,760 hours and **101 of 101** tail hours reproduced
(`_nyiso242_tail_zonal.json`, `rebuild_check`). **Only 2022 has complete raw zonal coverage**
(12 monthly RT zips; 2023/2024/2025 carry 2 / 6 / 1), so every per-zone number here is 2022's
and is not extended to the other years.

---

## 2. THE OBJECT, SIZED — $5.44/MWh, not ~$2

The **ceiling** is a deliberate upper bound and **not a candidate mechanism**: in the missed
hours only, every zone is lifted to the actual eleven-zone hub level. It **pins to actuals**, so
rule 13 `[R-MEASURED]` forbids it as an input for all time; it exists solely to size the object.
It is conservative twice over — the actual high zones sit *above* the hub, and nothing outside
the missed hours is touched.

The construction reproduces the scorer exactly, which is why it can be trusted:

| year | model lw | bench actual lw | **C3a scored** | reproduced here | actual tail | missed | **ceiling gain** | **C3a at ceiling** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 72.38 | 81.12 | **−10.8 %** | −10.77 % | 101 | 100 | **+$5.44** | **−4.06 %** |
| 2023 | 31.51 | 32.25 | −2.3 % | −2.28 % | 10 | 10 | +$0.68 | −0.16 % |
| 2024 | 37.95 | 38.12 | −0.4 % | −0.45 % | 13 | 13 | +$0.97 | +2.09 % |
| 2025 | 60.02 | 66.43 | −9.6 % | −9.65 % | 42 | 39 | **+$3.28** | **−4.71 %** |

Two things follow. **The handoff under-estimated the object by 2.7×** — it said "conservatively
~$2/MWh" and it is $5.44. And **the tail is missed in every year, not just 2022**: 100/101,
10/10, 13/13, 39/42. It is a span-wide structural absence that happens to be *scored* only where
the band is tight.

Record: `results/calibration/_nyiso242_tail_ceiling.json`.

---

## 3. THE MEASUREMENT THAT DECIDES THE SUCCESSOR

### 3.1 The argument is the LP's, not a modeller's

The energy-balance dual is the marginal unit's offer. A zonal price above $300 therefore
requires that **every tranche offering below $300 is already fully dispatched**. Idle sub-$300
capacity is a *hard ceiling* on the energy price — a reserve product can post its own dual
alongside, but it cannot make the LP pay $300 for energy it can still buy for $150.

### 3.2 What the keeper actually holds

`scripts/probes/nyiso242_tail_reachability.py` → `_nyiso242_tail_reachability.json`. Median over
each window, from the fleet-only rebuild of the keeper's **own** recipe (`mc_base`,
`availability`, `pmax`) against its committed `class_hourly`:

| year · window | n | available | dispatched | util | **idle below $300** |
|---|---:|---:|---:|---:|---:|
| **2022 all missed** | 100 | 14,606 | 8,955 | 61.3 % | **4,432 MW (30.3 %)** |
| 2022 winter (Jan/Feb/Dec) | 70 | 14,596 | 8,526 | 58.4 % | **4,716 MW (32.3 %)** |
| 2022 summer (Jun/Jul/Aug) | 23 | 19,619 | 16,632 | 84.8 % | 1,733 MW (8.8 %) |
| 2023 all missed | 10 | 18,109 | 14,028 | 77.5 % | 4,079 MW (22.5 %) |
| 2024 all missed | 13 | 18,506 | 15,444 | 83.5 % | 3,059 MW (16.5 %) |
| **2025 all missed** | 39 | 18,507 | 17,331 | 93.6 % | **1,074 MW (5.8 %)** |
| 2025 summer | 31 | 18,507 | 17,559 | 94.9 % | **899 MW (4.9 %)** |

**2022's winter cluster is the least reachable window in the span** and carries 70 % of that
year's object. **2025's summer cluster is the most reachable** — 4.9 % idle, and 1,124.7 MW
already staged in the $200–300 band — which is where a price-formation mechanism would have
something to work with.

### 3.3 The winter cluster is not a scarcity event in the model, and is not one in the actual either

Three independent readings agree, and none of them is a residual:

* **The model's marginal emission rate in the missed hours is indistinguishable from an ordinary
  hour** — 0.377 upstate / 0.53 downstate, in winter, in summer, and across all 8,760 hours
  alike. The LP has no state that distinguishes these hours: same marginal technology, no fuel
  switch, no shortage.
* **Nothing is tight.** Zero slack and zero dump in all 100 hours; **2 of 100** carry any
  reserve-family shortfall. The reserve machinery is armed and correctly grounded in the
  published SOM curves (NYC $25/MW, SENY $500 + $40, East $775 — `reserves/spec.py:400-470`);
  it simply is not the binding thing here.
* **The actual event is statewide, not a downstate pocket.** In **70 of the 100** missed hours
  **all five model zones** clear above $300, Upstate_West included, and the median gap is nearly
  **uniform** across them — Upstate +$251, Capital +$285, Lower Hudson +$266, NYC +$268,
  LI +$269. A uniform additive gap across a transmission network is the signature of a
  **marginal-cost input**, not of congestion or of a locational reserve product.

Median load in the winter cluster is **65 % of the year's peak**. A statewide $383 at 65 % of
peak is not capacity scarcity in any market.

---

## 4. WHAT THE WINTER GAP IS *NOT* — two hypotheses this session killed on its own evidence

Both are recorded because they are the natural next guesses and both are wrong.

**4.1 It is not simply an under-priced gas level.** The implied heat rate of the *actual* price
against the *measured* Transco Z6 print in those hours is **23.0 (upstate) / 26.5 (NYC)
MMBtu/MWh in winter and 38.9 / 51.1 in summer**. No gas unit in the fleet runs at those heat
rates — a CC is 8.6, a CT 15.2, an ST_GAS 16.8 (capacity-weighted, `_nyiso242_fuel_in_missed`).
The actual clearing price in those hours is **far above any unit's fuel cost**, so a fuel-level
repair cannot be the whole story. It is not nothing either: the model's capacity-weighted
delivered gas runs **$14.35/MMBtu against a measured $19.64** in the winter cluster, worth
**$45.56/MWh at the CC heat rate** — but against a **$251** gap that is at most **18 %**, and
the model's *annual* delivered gas is **1.19× the measured hub**, so there is no systematic
under-pricing to correct.

**4.2 The gas prints are not landing a day early.** Elliott's Dec 22 reads **+153 %** too high
in the model ($156.88 against $62.02 actual), which looks exactly like a trade-day/flow-day
misalignment — the defect `caiso_citygate_flow_date` exists for in CAISO, and which nyiso-234b
named as a second NYISO defect. **Tested and not supported.** Shifting the model's daily series
±2 days: 2022 and 2025 both prefer **k = 0** on r *and* RMSE; 2023 and 2024 prefer k = +1 only
marginally (r 0.575 → 0.604 and 0.676 → 0.691). Two of four years, small magnitude, no
consistent sign. **This is reported as a refutation, not filed as a candidate.**

What the Dec 22 overshoot does reflect is visible in the raw series and is a genuine, already
ledgered data limit: Transco Z6 prints **$32.12 (Dec 22) and $35.61 (Dec 23)**, and then
**nothing until Dec 27 ($6.29)**. **Dec 24 — the worst day of the year, actual $747.68 — has no
print at all.** Gap-filling that hole is `nyiso_hub_gap_month_level`, tested on all four solvable
years and **rejected (`R`, nyiso-223)**; the December archive limit is ledgered in
`docs/calibration-log/nyiso.md:6125`.

---

## 5. WHY NO SHARD WAS LAUNCHED (rules 1, 28(a), 34)

Rule 34 `[R-SHARD-PROMOTABLE]` forbids launching a shard whose result cannot back a promotion.
Every lever adjacent to this object is already adjudicated, and the DO-NOT-REDO set was read
before anything was proposed:

| lever | cell | why it is not available |
|---|---|---|
| `nyiso_iroquois_winter_spread` | **R** | solved and rejected twice (nyiso-150, -157); "no fuel-side mechanism can create the winter downstate premium" — and §3.3 here shows the event is *not* a downstate premium at all |
| `temp_dependent_derate` | **G** | refusal re-read and **held** 2026-09-14 (nyiso-234); identification undefeated, slope sign inverts |
| any NYISO ST_GAS availability lever | **I** + blanket DO-NOT-REDO | `NYISO.js:121` — "expect 0 binding hours". Relevant: ST_GAS is **2,080 MW of the 4,716 MW** idle in the winter cluster, so this forecloses **44 %** of it outright |
| `dual_fuel_switching` | **K**, LINE CLOSED | nyiso-179; the armed oil-parity cap already does the work |
| `nyiso_hub_gap_month_level` | **R** | nyiso-223, all four solvable years |
| `tsa_transfer_derate`, `scuc_load_pocket_commitment` | **G** | not identifiable / owner-court |
| NYISO scarcity / RCPF / ORDC family | **K** (armed) | the named successor — **foreclosed by §3** |

**One citation correction, because a successor will otherwise chase it.** The nyiso-241 PRECOMMIT
§7 cites the winter/gas-deliverability/dual-fuel closure as "nyiso-240 §1", and
`RESULT-nyiso240-…` §1 is "WHAT WAS PROMOTED". The real source is the **FINDING**, not the
RESULT: `FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md` HEADLINE 1 and §1. The
section number is right; the document is wrong. Noted here rather than rewritten into the
historical doc.

---

## 6. WHAT A SUCCESSOR SHOULD ACTUALLY DO — and the one thing this session cannot settle

The measurement points at **availability in winter cold snaps**, and it points there by
elimination rather than by enthusiasm. For the energy dual to reach $300 in the winter cluster,
roughly **4.7 GW** of the model's believed-available fleet would have to not be there. The
classes holding it, median MW in the winter cluster:

| class | idle below $300 |
|---|---:|
| ST_GAS | 2,080 |
| CT_PEAKER | 1,208 |
| CC_CHP | 1,129 |
| CC_REGULAR | 912 |
| COAL | 461 |

**ST_GAS's 2,080 MW is closed by the blanket DO-NOT-REDO.** The other **~3.7 GW is not**, and no
NYISO-scoped gas-supply/cold-snap availability mechanism exists at all — the whole family
(`neiso_gas_coldsnap_derate`, `neiso_coldsnap_derate_dualfuel_unswitched`,
`neiso_winter_fuel_mustrun`) is **hard-gated to NEISO in code**
(`model/interchange/neiso.py:105`), and rule 25 `[R-ISO-SCOPE]` means a NEISO verdict never
fills a NYISO cell and its parameters never transfer.

**THIS SESSION DOES NOT PROPOSE BUILDING ONE, and the reason is identification, not appetite.**
The honest blocker is that nobody has yet shown NYISO's own data can identify a cold-snap
availability derate — and the adjacent attempt at exactly that,
`temp_dependent_derate`, was refused **`G`** on identification twice, most recently six days ago.
A new mechanism whose magnitude is set by how much price it produces is the fitted mechanism
rule 1 `[R-STRUCT]` forbids, however well-motivated the physics. **The prerequisite is an
identification intake, not a solve**: measured NYISO winter forced-outage / derate data (GADS,
the ISO's own outage postings, or a CAMPD-based cold-hour availability census) capable of
setting the magnitude from something other than the residual. Until that exists, this lane has
no admissible lever for its largest object, and saying so is the finding.

**What is genuinely open and cheap, in the order the evidence supports:**

1. **The 2025 summer cluster is the one place price formation has room** — 31 hours, 94.9 %
   utilisation, **899 MW** idle sub-gate, 1,124.7 MW staged in $200–300, and worth **$3.28/MWh**
   on a year whose C3a sits 0.35 pp inside its band. It is a *different and smaller* object from
   2022's winter, and it is the only one the named successor could actually reach.
2. **`cc_winter_capability_basis` is `U` with no evidence string at all** (`NYISO.js:132`) — the
   one genuinely untested cell in this family. Note the likely direction is *against* the object
   (CC output rises in cold air), which is a reason to measure it, not to skip it.
3. The ledgered items this session leaves exactly as it found them: the **G2 hydro loss**
   (−55.2 / −25.5 GWh, 2022/2023) remains an **OPEN ROOT-CAUSE ISSUE**, not a caveat;
   `legitimacy_diagnostics.py` remains non-reproducible on nine measured columns and **nobody
   owns it**; `tests/scoring` carries **20 failures on clean main** and this session adds zero
   (it ran none — it wrote no solve-path code).

---

## 7. ARTEFACTS

Four probes, all zero-LP, all re-runnable against the committed keeper:

| probe | record | what it establishes |
|---|---|---|
| `scripts/probes/nyiso242_tail_phase0.py` | `_nyiso242_tail_phase0.json` | where the missed hours sit; slack/dump/reserve state; reserve-family shortfall by family |
| `scripts/probes/nyiso242_tail_zonal.py` | `_nyiso242_tail_zonal.json` | per-zone actual vs model (2022); the rebuild check against the gate series |
| `scripts/probes/nyiso242_fuel_in_missed.py` | `_nyiso242_fuel_in_missed.json` | the model's own delivered fuel price in those hours vs the measured print |
| `scripts/probes/nyiso242_tail_reachability.py` | `_nyiso242_tail_reachability.json` | **the decisive one** — idle capacity below the gate, by year and window |

Plus `_nyiso242_tail_ceiling.json` (§2), which reproduces the scorer's C3a in all four years to
0.03 pp and is the provenance for the $5.44 figure.

**Governance.** Rule 32 `[R-SHARD]` (a): zero LP in this container, no shard launched, so rules
33/34/35 have no subject. Rule 31 `[R-RETAIN]`: nothing was deleted. Rule 28: the queue and the
DO-NOT-REDO set were read **before** anything was proposed, six closed cells were checked and
**none re-tested**, and **no cell moves** because no mechanism was tested. Rules 21/24: zero free
parameters, zero new literals, no `ScenarioConfig` field touched. Rule 15 `[R-DASHBOARD]`: no run
was produced, so there is nothing to register; the keeper's dashboard entry is untouched and
still reads as nyiso-241 left it.
