# FINDING — nyiso-175: the blocker is a GRAIN difference, not a defect, and it UNBLOCKS the successor object; the "CT deficit" is TWO objects with opposite signatures; and both East River gates fail on their own pre-registered thresholds, so nothing is armed

**Session:** nyiso-175 · **Date:** 2026-09-02 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Solves run: ZERO.**
**No parameter was touched, no band was swept, no run was registered.**
**Pre-registration:** `results/calibration/PREREG-nyiso175-ct-conduct-and-d2-basis.md`,
committed with the probe at `6c3f0cf7` **before either was run**.

---

## 0. The result in one paragraph

Three things, in the brief's order. **(A) The blocker is cleared, and it was
never a defect.** nyiso-174 §6 item 3 left D-2's `class_total_twh` and the
keeper's P1 `class_hourly` disagreeing about the model's own turbine/steam split
by 13–17× on `ST_CHP` and 1.6–1.8× on `CT_CHP`. The whole disagreement is a
**grain** difference: D-2's row is the **plant**, and its label is the plant's
**most-common LP-unit `plant_group`** — East River carries **4** `CT_CHP`
tranches against **3** `ST_CHP`, so the plant is labelled `CT_CHP` and its
`ST_CHP` energy is counted in D-2's `CT_CHP` denominator. Two identities prove
it off committed bytes alone: D-2's `hydro` equals `class_hourly`'s **to four
decimals in all three years** (so the committed D-2 ran on the full LP dispatch,
the same basis), and the `CT_CHP` / `ST_CHP` deltas are **equal and opposite**
to a residual of **0.0084 / 0.0271 / 0.0746 TWh** — a conservative transfer.
`class_hourly` is therefore the identified per-class model artifact,
**nyiso-174 §6 item 2 is UNBLOCKED**, and the `share_of_class > 1` is a
reporting artifact of a unit-grain numerator over a plant-grain denominator. The
brief's "**LIVE HAZARD** for the rule 20 `[R-FORCED-BUDGET]` gate" is **NOT
live**: `CC_CHP` / `CT_CHP` / `ST_CHP` are in `D2_EXEMPT_CLASSES`, so no CHP
class ever reaches the gated summary — the keeper's own summary carries
`CC_REGULAR`, `CT_PEAKER`, `ST_GAS`, `hydro` and nothing else. **(B) The
instrument spend splits the object in two.** On the pre-registered B5 rule
`CT_PEAKER` is **LEVEL**-limited (q90 ratio **0.050 / 0.053 / 0.369**; starts
**102 / 93 / 156** against **399 / 457 / 293**; only **37.8 / 28.2 / 43.2 %** of
measured class energy falls in an hour the model runs the class at all) —
reproducing nyiso-90/91/96's closed diagnosis on the corrected construction and
a different bar — while `CT_CHP` is **RESPONSE**-limited in every year (q90
ratio **0.739 / 0.870 / 0.756**, hourly **r = 0.016 / 0.258 / 0.395**), a class
that is online **8,760 h** in the market and 8,592–8,736 h in the model, under
the market at **every decile of its own duration curve**, with **56–63 %** of
its deficit in the 0–50 load band. **The −2.4 TWh "CT deficit" is not one
object, and only `CT_PEAKER` was ever the load-pocket story.** **(C) Both East
River gates FAIL on the thresholds fixed in advance, so nothing is armed.** S2(b)
fails — EIA-923's GT:ST ratio is **1.914 / 2.885 / 3.083**, below the 2:1 bar in
2023 — and S3 fails — East River is only **43.2 %** of the misattributed energy
(6.581 of 15.233 TWh over three years), because **Ravenswood (2500) is bigger**
at 8.509 TWh. The attribution defect is real and is named and sized, but it is a
**fleet-wide derive question**, not one plant, and it is handed forward.

---

## 1. What was measured, and off what

`scripts/probes/nyiso175_ct_conduct_and_d2_basis.py`, **zero solve**, over
committed artifacts plus the primary record:

| source | what it supplies |
|---|---|
| `results/calibration/nyiso159_lossarm_B/legitimacy_diagnostics.json` | the committed D-2 rows + summary (the denominator under adjudication) |
| `results/calibration/nyiso159_lossarm_B/hourly/class_hourly_*.parquet` | the keeper's own P1 class dispatch (rule 15: read, don't replay) |
| `results/calibration/nyiso159_lossarm_B/hourly/system_*.parquet` | the keeper's own hourly NYCA demand, for the load-band apportionment |
| `results/calibration/nyiso159_lossarm_B/floors/*_rebuilt.npz` | the LP-unit `plant_group` roster and per-unit floors (rebuilt by `run_year(fleet_only=True)` — a fleet build, **no LP**) |
| `frontend/data/backcast/runs/2026-08-30-nyiso-159-loss-surface.js` | the per-(plant, class) model hourly payload |
| `frontend/data/backcast/bench/NYISO/{year}.json.gz` | committed grid-delivered `classFull` |
| `data/raw/campd-unit-level/NY_{year}.parquet` | per-unit hourly `grossLoad` / `steamLoad` / `opTime` |
| `data/raw/eia-860/eia860_generator_operable.parquet` | prime movers, summer MW, **published Minimum Load** |
| `data/raw/_processed-legacy/eia923_monthly_generation.parquet` | Page-1 net generation by prime mover |
| `data/raw/_processed-legacy/thermal_tranches_NYISO.csv` | the CHP floor level source |
| `scripts/data/derive_thermal_tranches.py` | `_fleet_nameplate_and_group`, the attribution rule under audit |

Output: `results/calibration/_nyiso175_ct_conduct_and_d2_basis.json`.

### 1.1 Reproduction of the inherited probes, run before anything was restated

All **fifteen** NYISO probes in the inherited corpus (nyiso-164 through 174) were
re-run first. **Fourteen reproduce BIT-IDENTICALLY** (`git status` clean);
`nyiso168_reserve_supply_slack` reproduces to a **max relative delta of
1.94e-16** over **309 numeric leaves**, with **zero** structural difference
(0 keys added, 0 removed) — trap (a) exactly as documented, and the churn was
**not committed**.

The six documented traps were all hit and all handled, none as a defect:

* **(b)** the gitignored NYISO DA LBMP container was restored with
  `fetch_nyiso_zonal_lmp.py --start 202301 --end 202512 --kind both` (36 DA
  months downloaded) plus `regenerate_clean.py nyiso-interface-flows`;
  `nyiso169` then reproduces bit-identically with DA `hours_covered` **8760 /
  8760 / 8760**. The degraded output was never committed.
* **(e)** `ancillary-services` was regenerated before
  `nyiso168_reserve_supply_slack` ran, and its output was diffed
  **STRUCTURALLY** (key-set equality) as well as numerically — both measured
  DAM and RTM reserve-price blocks are present and unchanged.
* **(c)** every clock in the new probe is `Etc/GMT+5`; **(d)** `grossLoad`,
  `steamLoad`, `opTime` and `heatInput` are filled to zero explicitly before any
  `np.add.at`; **(f)** every measured class series is built through
  `scripts/lib/campd_measured_classes.py`, never the bare `unitType` string.

**One new environment trap, recorded for successors and NOT a defect.** The D-2
floor rebuild needs the `capacity-deliverability` clean partition: without it
`apply_nyiso_li_tsl_import_cap` raises *"no published Long Island
transfer_security_limit … available areas: []"* and the rebuild dies. It is not
in the brief's phase-0 list. `regenerate_clean.py capacity-deliverability`
fixes it.

---

## 2. Object A — the blocker is a GRAIN difference, and it is now cleared

### 2.1 Gate A1 as pre-registered: FAILS, and the failure identifies the basis

The pre-registered route was to recompute D-2 at HEAD and require every gas
class-year and hydro within 0.5 %. It does not clear:

| 2025 | committed | HEAD recompute | rel |
|---|---|---|---|
| `''` (nuclear + HQ) | 36.2274 | 36.2256 | 0.00005 ✓ |
| `CC_REGULAR` | 34.2456 | 33.6291 | 0.018 ✗ |
| `ST_GAS` | 12.3843 | 12.1736 | 0.017 ✗ |
| `CC_CHP` | 19.9516 | 25.7257 | **0.289** ✗ |
| `CT_CHP` | 3.2995 | 4.4299 | **0.343** ✗ |
| `ST_CHP` | 0.0931 | 0.1818 | **0.953** ✗ |
| `CT_PEAKER` | 0.8458 | 0.7096 | 0.161 ✗ |
| `hydro` | 24.0589 | 15.0940 | **0.373** ✗ |

**Gate A1 = FAIL, and hypothesis H-A's limbs (i) and (ii) are REFUTED for the
committed artifact.** The reason is the pjm-149 path divergence, live on this
keeper: the committed D-2 was built at solve time on the run's own
`dispatch/<year>_P1.parquet` (every model plant); that file is gitignored and
absent, so a HEAD recompute falls silently to the **100-plant run payload**,
which carries only CEMS-metered plants and carries the report-only CHP
behind-the-meter add-back. The classes that survive the gate are exactly the
ones the payload covers well; the ones that blow out are the CHP classes (whose
add-back the payload adds) and hydro (which the payload barely covers).

**This is a governance finding in its own right and is handed forward: the
keeper's committed D-2 is NOT reproducible from committed artifacts.** A
recompute moves its CHP and hydro denominators by 29–147 % without any warning
in the artifact.

### 2.2 What the committed denominator actually IS — two identities, off committed bytes

*(POST-HOC: added after gate A1 returned, and labelled as such in the probe
output. It is an identity check, not a threshold.)*

**Identity 1 — the untouched class.** For a class with no mixed-class plant, a
plant rollup and a per-class series must agree exactly. D-2's `hydro` is
**26.6134 / 26.7390 / 24.0589** and `class_hourly`'s is **26.6134 / 26.7390 /
24.0589** — identical to four decimals in all three years — and D-2's `''`
bucket equals `class_hourly`'s `nuclear` plus the 7.884 TWh HQ firm-import
pseudo-unit to **0.005 %**. **So the committed D-2 ran on the full LP dispatch,
on the same basis as `class_hourly`, and carries no add-back.**

**Identity 2 — the conservative transfer.** D-2 minus `class_hourly`, TWh:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CT_CHP` | **+1.1332** | **+1.1209** | **+1.4734** |
| `ST_CHP` | **−1.1248** | **−1.0938** | **−1.3988** |
| **residual** | **+0.0084** | **+0.0271** | **+0.0746** |
| `hydro` | 0.0000 | −0.0000 | 0.0000 |

The pair's deltas are equal and opposite to within 0.008–0.075 TWh. **That is a
relabelling, not a difference of measurement.**

### 2.3 Gate A2 — the sign falsifier PASSES

Read off the floors arrays (LP-unit grain, which is the grain `plant_class_rows`
labels on), East River carries **4 `CT_CHP` tranches and 3 `ST_CHP` tranches** in
every year:

```
CT_CHP_NYC_p2493_{committed, econlo, econhi, peak}    ← 4
ST_CHP_NYC_p2493_{committed, econ, peak}              ← 3
```

so the plant-majority label is **`CT_CHP`**, exactly as gate A2 required. The
same rule explains every other large delta: Ravenswood (2500) carries 8 `ST_GAS`
against 7 `CC_REGULAR` and so pulls **+2.22 / +2.20 / +2.60 TWh** into D-2's
`ST_GAS`, and the `OTHER` / `oil` / `biomass` LP units at gas-labelled plants are
absorbed the same way (`OTHER` −2.20 / −2.20 / −1.95).

### 2.4 What this settles

* **`class_hourly` is the identified per-class model artifact.** D-2's
  `class_total_twh` is a **plant-rollup denominator** and was never a per-class
  quantity — the docstring says so (*"Class DENOMINATORS stay on the row label
  (the dispatch grain)"*); nyiso-174 §6 item 3 read it as one.
* **nyiso-174 §6 item 2 is UNBLOCKED.** §3 and §4 below read it.
* **The `share_of_class` > 1 is fully explained**: since the miso-170/171 repair
  the D-2 *numerator* is re-attributed at **unit** grain (`FloorClassMatrix`
  charges the ST bin's floor to `ST_CHP`) while the *denominator* stays on the
  plant-rollup label (`CT_CHP`) — so `ST_CHP`'s denominator excludes East River
  entirely while its numerator includes East River's ST floor. It is the exact
  pathology `run_d2`'s docstring discloses, in its partial form (the class has a
  denominator, just not a matching one).
* **The rule 20 `[R-FORCED-BUDGET]` hazard is NOT live.**
  `D2_EXEMPT_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP", "nuclear")` and `run_d2`'s
  summary loop `continue`s on them, so **no CHP class can ever produce a gated
  `forced_share` verdict**. The keeper's committed D-2 summary carries
  `CC_REGULAR`, `CT_PEAKER`, `ST_GAS`, `hydro` — and nothing else. The brief's
  carried-forward hazard is **withdrawn on the code**.
* **A denominator correction that DOES matter.** The brief quotes `chp_steam` as
  forcing `CT_CHP` at **7.6 / 21.3 / 6.3 %** of class energy. That is D-2's
  forced TWh over D-2's inflated denominator. On the identified denominator
  (`class_hourly` `CT_CHP` = 1.7648 / 1.3275 / 1.8261) the true forced share is
  **12.5 / 39.2 / 11.3 %** — about **1.8× larger**, and above the 30 % merchant
  cap in 2024. It still gates nothing (the class is exempt), but every quotation
  of it should now use the larger figure.

---

## 3. Object B — the instrument spend: `CT_PEAKER` and `CT_CHP` are TWO objects

Measured series: `scripts/lib/campd_measured_classes.py` corrected construction
over the CAMPD NY unit-hourly extracts, level-anchored to the committed
`classFull` so only shape is compared. Model series: the keeper's P1
`class_hourly` — identified as the right artifact by §2.

### 3.1 The anchors, on the corrected construction, all three years

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CT_CHP` CEMS gross TWh | 2.6287 | 2.7786 | 2.6717 |
| `CT_CHP` bench `classFull` TWh | 2.4336 | 2.1717 | 2.3829 |
| `CT_CHP` **anchor** | **0.926** | **0.782** | **0.892** |
| `CT_PEAKER` CEMS gross TWh | 1.6476 | 1.5785 | 1.9749 |
| `CT_PEAKER` bench `classFull` TWh | 2.1139 | 1.9108 | 2.8512 |
| `CT_PEAKER` **anchor** | **1.283** | **1.211** | **1.444** |

Both classes anchor in the band nyiso-170 §3 called identifiable, in every year.
**nyiso-174's flip holds and extends backwards**: `CT_CHP` is identifiable in
2023 and 2024 as well as 2025.

### 3.2 The B5 verdict, on the rule fixed in advance

| | q90 model ÷ q90 anchored-measured | hourly `r` | **B5 verdict** |
|---|---|---|---|
| `CT_CHP` 2023 | 0.739 | **0.016** | **RESPONSE** |
| `CT_CHP` 2024 | 0.870 | **0.258** | **RESPONSE** |
| `CT_CHP` 2025 | 0.756 | **0.395** | **RESPONSE** |
| `CT_PEAKER` 2023 | **0.050** | 0.679 | **LEVEL** |
| `CT_PEAKER` 2024 | **0.053** | 0.464 | **BOTH** |
| `CT_PEAKER` 2025 | **0.369** | 0.626 | **LEVEL** |

**The two classes fail in opposite ways, unanimously.** `CT_PEAKER` reaches
5–37 % of the market's p90 with a *good* hourly correlation — it runs in
roughly the right hours and cannot reach the right level. `CT_CHP` reaches
74–87 % of the market's p90 with an hourly correlation near zero — it reaches
the right level in the wrong hours.

### 3.3 `CT_PEAKER` — the closed diagnosis reproduces exactly

At a common online bar (2 % of the class's own demonstrated p99.5):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured on-hours | 5,927 | 5,093 | 6,803 |
| model on-hours | **805** | **779** | **1,556** |
| measured starts | 399 | 457 | 293 |
| model starts | **102** | **93** | **156** |
| measured run median h | 9 | 7 | 10 |
| model run median h | **8** | **7** | **7** |
| measured energy in an hour the model runs the class | **37.8 %** | **28.2 %** | **43.2 %** |

**Run lengths match; starts are 2.5–4.9× too few.** This is nyiso-90 §2 and
nyiso-96 §2 reproduced on a *different construction* (the corrected CAMPD
crosswalk), a *different bar* and a *different keeper* — an independent
confirmation, not a re-test. Per the pre-registered guard **S4, no `CT_PEAKER`
lever is opened**: the surviving cause is on record as **NYISO SCUC load-pocket
security commitment with BPCG make-whole** (`scuc_load_pocket_commitment`, cell
`G`), whose data route the owner closed permanently at nyiso-163b.

### 3.4 `CT_CHP` — a RESPONSE deficit, and where it sits

Model ÷ anchored-measured at each decile of each series' own duration curve:

| decile | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | 0.73 | 0.72 | 0.72 | 0.71 | 0.61 | 0.73 | 0.79 | 0.90 | 0.70 | 0.75 |
| 2024 | 0.88 | 0.87 | 0.61 | 0.44 | 0.34 | 0.40 | 0.47 | 0.56 | 0.72 | 0.75 |
| 2025 | 0.78 | 0.76 | 0.78 | 0.82 | 0.92 | 0.84 | 0.63 | 0.52 | 0.64 | 0.72 |

**The model is below the market at every decile of every year** — so unlike
nyiso-171's `CC_CHP` case, the *sign does not forbid* a floor here, and unlike
it again, the measured class is **never off** (8,760 on-hours, a single
year-long run, in all three years), so a floor could not force a machine to run
in an hour its own meter says it was off. Both of nyiso-171's kills are absent.

The shortfall is worst in the **middle** of the curve, and in 2024 deciles 3–8
the model sits flat at **90–139 MW** — its own `chp_steam` floor — while the
anchored market holds **126–316 MW** there.

Apportioned to the nyiso-168 load bands, the `CT_CHP` deficit is:

| band | 0–50 | 50–80 | 80–90 | 90–95 | ≥95 |
|---|---|---|---|---|---|
| 2023 | **55.5 %** | 33.3 % | 9.0 % | 1.0 % | 1.2 % |
| 2024 | **63.4 %** | 37.1 % | 2.0 % | −0.9 % | −1.5 % |
| 2025 | **61.1 %** | 27.0 % | 8.9 % | 2.7 % | 0.3 % |

**88 / 100 / 88 % of it is in the bottom 80 % of load hours.** That is a commitment
signature, not a scarcity one — and it is *not* the band nyiso-168 located the
C3a deficit in (the 50–90 band carries 73 % of C3a-2025; this class's deficit is
majority *below* it).

### 3.5 B7 — the steam-host driver is measured, and it is NOT there

*(POST-HOC, labelled as such.)* `chp_steam_following` is the sole mechanism
forcing `CT_CHP` (§5), so the obvious successor is to give it a measured hourly
steam profile. **CAMPD meters East River's district-steam send-out directly**,
and the answer is negative:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| plant steam send-out, M klb | 9.424 | 7.661 | 7.221 |
| steam metered on units 60 / 70 | **100 %** | **100 %** | **100 %** |
| steam metered on units 1 / 2 (the turbines) | **0** | **0** | **0** |
| electricity metered on units 60 / 70 | **0 MWh** | **0 MWh** | **0 MWh** |
| `r`(measured plant turbine MW, plant steam klb/h) | **−0.016** | **+0.309** | **+0.077** |
| `r`(measured plant turbine MW, NYCA load) | +0.352 | +0.288 | +0.395 |
| `r`(model `CT_CHP` class MW, plant steam klb/h) | +0.289 | +0.365 | +0.338 |
| `r`(model `CT_CHP` class MW, NYCA load) | **+0.724** | **+0.759** | **+0.644** |

**The host's steam does not predict the turbines' electric output at hourly
grain** — it is made by two separate direct-fired boilers that generate no
electricity at all (which is nyiso-120 KE3's own finding, at 100 % of the dark
fuel, arrived at independently here). So there is **no measured hourly steam
driver to give `chp_steam_following` at this plant**, and that route is closed
before it is built.

What the same table shows is where the model's response comes from instead: the
model's `CT_CHP` tracks **system load** at `r` = 0.64–0.76, while the market's
tracks load at only 0.29–0.40 and steam at ~0. The market's monthly shape is a
**maintenance** shape — 2023 runs 271 / 256 GWh in Jan/Feb and collapses to
114 / 69 GWh in Apr / Oct — not a load shape and not a steam shape.

**So `CT_CHP`'s RESPONSE deficit and `CT_PEAKER`'s LEVEL deficit have DIFFERENT
signatures but the SAME residual driver family**: a commitment/outage process
outside the five-zone economic dispatch. For `CT_PEAKER` that is
`scuc_load_pocket_commitment` (`G`, owner-closed). For `CT_CHP` the measurement
adds a second, cheaper candidate — **unit-level maintenance scheduling that the
outage overlay never reaches**, because `_generic_unit_outage_target` returns
`None` for both CT classes by design (§5).

---

## 4. Object C — East River: the object is named and sized, and BOTH gates fail

### 4.1 The plant, on ONE basis

The comparison basis is stated because mixing two is the trap this measurement
exists to avoid: the run payload's per-(plant, class) series carries a
**report-only** CHP behind-the-meter add-back (`render_calibration_html`:
`mw += btm_mwh / T`, flat, 35 % at this plant) that the LP does not carry. It is
removed explicitly below, so the model side is the LP's own **grid** dispatch —
the basis `class_hourly` and the scored C1 comparison both use.

| 2025, TWh | model grid | market (EIA-923 net) | Δ |
|---|---|---|---|
| `CT_CHP` (EIA-860 `GT` ×2, 306.0 MW) | **1.677** | **2.079** | **−0.402** |
| `ST_CHP` (EIA-860 `ST` ×2, 309.5 MW) | **1.388** | **0.674** | **+0.713** |
| plant total | 3.065 | 2.754 | +0.311 |

**The plant total is right to +11 %; the SPLIT is inverted.** And the split is
essentially the whole of both class errors:

| East River's share of its class's C1 gap | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CT_CHP` | **56.5 %** | **114.3 %** | **72.2 %** |
| `ST_CHP` | 237 % | **109.5 %** | **103.1 %** |

*(A share above 100 % means the plant's own gap exceeds its class's, i.e. the
rest of the class partly offsets it. The 2023 `ST_CHP` figure divides by a
near-zero class gap of +0.027 TWh and is reported for completeness only.)*

**So `CT_CHP` −23.4 % and `ST_CHP` +86.6 % are not two class objects. They are
one plant's split, seen twice.**

### 4.2 Why the split is set by the floors, not by economics

Both bins carry the **same** offer heat rate — 7.4205, the nyiso-120
`measured_chp_heat_rates` applied value — and the same delivered gas, so the LP
is close to indifferent between them and the split is decided by what is forced.
Read off the floors arrays:

| | floor MW | hours floored 2023 / 2024 / 2025 | floor energy TWh/yr |
|---|---|---|---|
| `CT_CHP_NYC_p2493_econlo` | **90.08** | **8,760 / 8,760 / 8,760** | 0.745 |
| `ST_CHP_NYC_p2493_econ` | **92.82** | 7,272 / 8,040 / 7,872 | 0.591 / 0.667 / 0.672 |

**This CORRECTS nyiso-174 §5.** That table read *"there is no `CT_CHP` tranches
row, so the turbine bin has no floor"* and *"the model floors the STEAM bin …
and leaves the TURBINE bin unfloored and un-derated."* The tranches CSV indeed
has no `CT_CHP` row for 2493 — but the EIA-923 CHP-pmin route floors the turbine
bin anyway, at **90.08 MW in every hour of every year**, which is **more** hours
than the steam bin's floor binds.

Two further facts place the levels against the primary record:

* the plant's own measured minimum is **0 MW / 81 MW / 85 MW** (25 zero hours in
  2023, none in 2024–2025) and its measured p05 is **87 / 93 / 94 MW** — so the
  `CT_CHP` floor at 90.08 MW sits essentially *at* the plant's measured p05, and
  is **below one single GT's EIA-860 published Minimum Load of 110 MW**;
* the market's measured p25 / p50 are **162 / 224** (2023), **176 / 275** (2024),
  **171 / 239** MW (2025), while the model's grid p25 / p50 are **157 / 167**,
  **87 / 87**, **86 / 255**. In 2024 the model's turbine bin sits at its floor
  for more than half the year against a market median of 275 MW.

**The gap is therefore at the p25–p50 of the plant's conduct, not at its
minimum** — a *committed loading level*, not a min-gen floor. Raising the floor
to the measured median would bind in hours the plant was demonstrably below it:
rule 17 `[R-FLOOR-WINDOW]`, refused.

### 4.3 Gate S2 — FAILS on (b)

| | 2023 | 2024 | 2025 | bar | verdict |
|---|---|---|---|---|---|
| **(a)** turbine-family share of the plant's CAMPD `grossLoad` | **1.000** | **1.000** | **1.000** | ≥ 0.90 | **PASS** |
| **(b)** EIA-923 GT : ST | **1.914** | 2.885 | 3.083 | ≥ 2.0 every year | **FAIL** |
| **(c)** model `ST÷CT` ÷ EIA-923 `ST÷GT` | 1.212 | **2.007** | **2.082** | ≥ 1.5 in ≥ 2 yr | **PASS** |

**S2 requires all three, so the East River attribution lane is KILLED on its own
pre-registered threshold, and this session arms nothing.** The failure is
substantive rather than a near-miss of bookkeeping: in 2023 the steam half
generated **1.057 TWh against the turbine half's 2.022** — 34 % of the plant's
electricity. The premise nyiso-174 §6 item 2 handed forward — *"the market's
must-run is measurably in the turbine half … its boilers having generated
0.000 TWh"* — **does not survive the primary record**, and §6 below states why.

### 4.4 Gate S3 — FAILS: it is a fleet-wide derive rule, not one plant

`derive_thermal_tranches._fleet_nameplate_and_group` attributes a plant's
**facility-summed** CAMPD net to *"the group holding the most nameplate at each
plant"*. At a mixed plant that is a guess, and it is wrong at three NYISO plants
in every year:

| plant | primary group (by nameplate) | group actually carrying the CAMPD energy | carrier share | nameplate margin | CAMPD TWh/yr |
|---|---|---|---|---|---|
| **2500 Ravenswood** | `ST_GAS` (1,724.8 MW) | **`CC_REGULAR`** (222.2 MW) | 0.64–0.73 | **1,502.6 MW** | 2.850 / 2.665 / 2.994 |
| **2493 East River** | `ST_CHP` (309.5 MW) | **`CT_CHP`** (306.0 MW) | **1.000** | **3.5 MW** | 2.134 / 2.259 / 2.189 |
| **2682 S A Carlson** | `ST_GAS` (45.0 MW) | **`CT_PEAKER`** (42.0 MW) | 1.000 | 3.0 MW | 0.042 / 0.029 / 0.071 |

Total misattributed CAMPD energy over 2023–2025: **15.233 TWh**, of which East
River is **6.581 TWh = 43.2 %** — **below the 50 % bar, so S3 FAILS and the
object is handed forward as a fleet-wide derive question, not armed here.**

Two readings worth keeping. First, **Ravenswood is the bigger case and it is not
a near-tie**: a 1,502.6 MW nameplate majority picks the wrong carrier because
the plant's big steam units barely run while its 222 MW combined-cycle unit
carries two thirds of the energy — so the defect is not "mixed plants with
similar bins", it is the *rule*. Second, East River's is decided by **3.5 MW,
1.1 % of the bins' capacity** — the most fragile possible basis for a decision
that moves 2.1–2.3 TWh/yr of measured conduct onto the wrong tranche row.

This is the same defect family as nyiso-174 §6 item 1 (`_resolve_unit_group`'s
last-writer-wins `fac_group` short-circuit in the *outage* extract) and as
neiso-99's rule 14 `[R-ACCURATE]` exception — **a per-plant aggregate assigned
to one of a mixed plant's classes by a proxy instead of by the units' own
meters** — and the corrected per-unit construction that fixes it already exists
and is tested (`scripts/lib/campd_measured_classes.py`, nyiso-174).

### 4.5 Gate S5 — the required-move bound

**S5 as pre-registered is uninterpretable, and that is disclosed rather than
quietly fixed.** Its construction compared the payload's East River series
(which carries the report-only BTM add-back) against a class gap taken on the
grid basis — two different bases — and returned **−0.493 / +0.252 / −0.585**, a
figure that changes sign for a reason that has nothing to do with the object.
**The single-basis version (§4.1, both sides on the LP grid basis) is the one
that answers the question**, and it is reported here in its place, as a
correction of the probe's own construction, never of its threshold.

On that basis, closing East River's split entirely would move `CT_CHP` by
**+0.378 / +0.965 / +0.402 TWh** and `ST_CHP` by **−0.064 / −0.343 /
−0.713 TWh** — **more than half** of the `CT_CHP` class error in 2023 and 2025
and **more than all** of it in 2024. **S5's "less than half" caveat therefore
does not fire: the object genuinely is the class.**

**But its C3a expectation is ~zero and must not be sold otherwise.** Both bins
carry the same heat rate and the same delivered gas, so moving energy between
them changes no unit's marginal cost and no marginal price. **This is a C1 /
structural-representation repair, not a C3a-2025 lever.** Under rule 1
`[R-STRUCT]` that is a reason to do it eventually, and not a reason to expect
the residual to move.

---

## 5. Rule 19 `[R-ONE-MECH]` enumeration — what floors, gates or derates the CT classes

Read off the keeper's committed `legitimacy_diagnostics.json`, its `run_config`
and the engine, not off documentation:

| | `CT_PEAKER` | `CT_CHP` |
|---|---|---|
| `chp_steam` (`chp_steam_following = True`) | — | **the SOLE forcing mechanism**: 0.2199 / 0.5208 / 0.2072 TWh forced |
| forced share on D-2's own (plant-rollup) denominator | 0.0 | 7.6 / 21.3 / 6.3 % |
| forced share on the **identified** denominator (§2.4) | 0.0 | **12.5 / 39.2 / 11.3 %** |
| unit-outage overlay (`campd_outage_windows`) | **never reaches** — `_generic_unit_outage_target(·, ·, "CT_PEAKER") → None` | **never reaches** — `… "CT_CHP" → None` |
| `ct_mustrun_per_plant` | **False** | — |
| `nyiso_incity_commitment_obligation` | **False** (built and rejected, nyiso-83) | False |
| `nyiso_gas_bridge_ct` (the CT limb of `nyiso_gas_commitment_bridge`) | **False** — probe-tested and rejected at nyiso-90 (12 / 28 / 74 unit-hours floored; +0.01–0.03 % of the gap) | not in scope: the limb admits `CT_PEAKER` only |
| `reliability_floor` limbs | NYISO's are keyed on `ST_GAS`; the downstate `tmax` limbs are disabled as the bridge's replacement (owner, 2026-07-27) | same |
| `temp_derate_slope_ct_chp` | — | **None** (field exists, unset) |
| D-2 total forced energy | **0.0000 TWh in every year** | 0.2199 / 0.5208 / 0.2072 TWh |

**`CT_PEAKER` is completely unforced and completely underated**: nothing floors
it, no outage overlay reaches it, and its D-2 forced energy is exactly zero in
all three years. **`CT_CHP` carries exactly one mechanism, `chp_steam`** — so any
correction there **REPLACES** its level source rather than stacking, which is
what rule 19 requires and what §4.2 shows is the live question.

Note for successors: the outage overlay reaching *neither* CT class is a
deliberate design decision (*"combustion turbines dispatch economically"*), and
§3.5 has just measured the one place it costs something — East River's turbine
half shows a maintenance-shaped monthly profile (2023: 271 / 256 GWh in Jan–Feb
against 114 / 69 GWh in Apr / Oct) that no mechanism in the model can produce.

---

## 6. Corrections to the committed record

Four, all measured rather than argued, and all of them narrow rather than widen
what a successor may claim.

1. **nyiso-174 §5 — "the turbine bin has no floor" is WRONG.** East River's
   `CT_CHP` bin carries a `chp_steam` floor of **90.08 MW in all 8,760 hours of
   every year** (floors arrays, §4.2), *more* hours than the steam bin's
   92.82 MW binds. The absence of a `CT_CHP` row in
   `thermal_tranches_NYISO.csv` does not mean the bin is unfloored: the EIA-923
   CHP-pmin route floors it. The rest of that table (the outage overlay reaching
   only `ST_CHP`; no `_FLEET_GROUP_OVERRIDE` needed; the bridge not gating either
   bin) reproduces and stands.

2. **nyiso-174 §6 item 2's premise — "its boilers having generated 0.000 TWh" —
   conflates two different things.** The 0.000 TWh is a **CEMS-coverage** fact
   about CAMPD units 60 / 70, which are **direct-fired steam boilers** that make
   no electricity at all — exactly what nyiso-120 KE3 measured in 2026-08 (100 %
   of the plant's "dark" fuel, 30.6–37.5 % of its total). They are **not** the
   EIA-860 `ST` generators 6 and 7 (132.7 + 176.8 MW summer, 1951/1955), which on
   EIA-923 generate **1.057 / 0.745 / 0.674 TWh a year**. The plant is a topping
   cogen whose electricity splits GT : ST at **1.91 : 1 → 3.08 : 1**, not a
   turbine plant with idle boilers. **This is what fails gate S2(b)**, and it is
   the reason the successor object cannot be stated as "the must-run is in the
   turbine half".

3. **nyiso-174 §1's heat-rate evidence leg does not support its conclusion**
   (the conclusion itself stands on EIA-860 prime movers and EIA-923 Page-1, and
   is not disturbed). It reads units 1/2's measured **10.51–10.89 MMBtu/MWh** as
   *"a simple-cycle heat rate ~45 % above the combined-cycle band"* refuting
   CAMPD's `"Combined cycle"` label. But that ratio divides the **whole power
   train's** fuel — units 1/2 burn all of it — by **GT-only** gross load, because
   the steam turbines have no stack and are invisible to CEMS. nyiso-120 KE2
   already measured the power-train rate on two independent meters at
   **7.3763** (CAMPD power-train fuel ÷ eGRID `PLNGENAN`) against eGRID's
   credited **7.4205**, agreeing to **0.6 %** — squarely in the combined-cycle
   band. The label argument should be made on prime movers alone.

4. **The `chp_steam` forced share for `CT_CHP` is ~1.8× larger than recorded.**
   **12.5 / 39.2 / 11.3 %** of class energy, not 7.6 / 21.3 / 6.3 % (§2.4). It
   gates nothing — the class is in `D2_EXEMPT_CLASSES` — but the smaller figure
   should not be quoted again.

---

## 7. Lines this session closes, and what is handed forward

### Closed

* **CLOSED — nyiso-174 §6 item 3, the D-2 vs `class_hourly` split
  disagreement.** It is a **grain** difference (plant rollup + plant-majority
  LP-unit label), proved by two identities off committed bytes: `hydro`
  identical to four decimals, and a `CT_CHP`/`ST_CHP` transfer conserving to
  0.0084 / 0.0271 / 0.0746 TWh. **Neither artifact is defective.**
  `class_hourly` is the identified per-class model series. **Do not re-open.**
* **CLOSED — the rule 20 `[R-FORCED-BUDGET]` hazard the brief carried
  forward.** `ST_CHP`'s `share_of_class > 1` can never gate: the three CHP
  classes are in `D2_EXEMPT_CLASSES` and never reach the D-2 summary. **It is a
  reporting artifact, not a live hazard.**
* **UNBLOCKED — nyiso-174 §6 item 2.** §4 reads it, and its answer is that the
  premise was wrong (correction 2) and that the object is a *split inversion*,
  not a must-run location.
* **CLOSED — "is the CT deficit one object?" NO**, and the two halves fail in
  opposite directions (§3.2). **Do not treat `CT_PEAKER` and `CT_CHP` as one
  lane again.**
* **CLOSED — the measured-hourly-steam-driver route for `chp_steam_following`
  at East River.** The host's steam is metered entirely on two boilers that
  generate zero electricity, and `r`(turbine MW, steam klb/h) is
  **−0.016 / +0.309 / +0.077**. There is no hourly steam profile to give the
  mechanism at this plant. **Do not build one.**
* **CONFIRMED, NOT RE-OPENED — `CT_PEAKER`'s diagnosis.** Starts 2.5–4.9× too
  few with matching run lengths reproduces on the corrected construction, a new
  bar and a different keeper. The surviving cause remains
  `scuc_load_pocket_commitment` (`G`, owner-closed at nyiso-163b). **No
  `CT_PEAKER` lever was opened (guard S4).**
* **NOT RE-OPENED — the twenty-six closed lines** carried into this session, and
  **no C3c lever was opened**.
* **NOT OPENED — any parameter, band, floor or offer change.** Both East River
  gates failed on thresholds fixed before measurement, so no arm was
  pre-registered and no solve was run.

### Handed forward

1. **THE FLEET-WIDE TRANCHE-DERIVE ATTRIBUTION DEFECT** (the S3 object, §4.4).
   `derive_thermal_tranches._fleet_nameplate_and_group` assigns a plant's
   facility-summed CAMPD net to its **largest-nameplate** group. At three NYISO
   plants that is the wrong carrier, for **15.233 TWh** of measured conduct over
   2023–2025 — **Ravenswood 8.509 TWh** (a 1,502.6 MW margin picking a bin that
   carries a third of the energy), **East River 6.581 TWh** (decided by
   **3.5 MW**, 1.1 %), **S A Carlson 0.142 TWh**. The corrected per-unit
   construction already exists and is tested (`scripts/lib/campd_measured_classes.py`).
   **Zero DOF; a crosswalk repair, not a re-derivation against a residual**, so
   rule 23 `[R-FROZEN-DERIVE]` is satisfied by citing the attribution defect
   rather than a data change. **Re-open condition:** a session that can carry a
   full three-year NYISO re-solve, since re-deriving the tranche artifact is
   solve-affecting. **Expected value, stated honestly: it is a C1 /
   representation repair with a ~zero C3a expectation** (§4.5), and it should be
   proposed on rule 1 `[R-STRUCT]` grounds alone. It belongs in the same commit
   as nyiso-174 §6 item 1's outage-extract routing repair — same defect family,
   same two plants, same corrected construction.
2. **THE D-2 REPRODUCIBILITY GAP** (§2.1). The keeper's committed D-2 cannot be
   re-derived from committed artifacts: the solve-time path
   (`dispatch/<year>_P1.parquet`) is gitignored, so a HEAD recompute silently
   falls to the 100-plant run payload and moves the CHP and hydro denominators
   by **29–147 %** with no warning in the artifact. The code documents the
   divergence (`build_plant_matrices`, pjm-149 §2) but the artifact does not
   record **which** path produced it. **A one-line provenance stamp
   (`dispatch_source`, already computed at line 3012/3024 and used only in a
   coverage note) written into the D-2 block would close it** — a
   diagnostics-integrity lane, cross-ISO, no solve.
3. **`CT_CHP` MAINTENANCE SHAPE, recorded and NOT proposed.** The market's East
   River turbine half runs a maintenance-shaped year (2023: 271 / 256 GWh in
   Jan–Feb against 114 / 69 GWh in Apr / Oct) that no armed mechanism can
   produce, because `_generic_unit_outage_target` returns `None` for both CT
   classes by design. Recorded because it is the one measured place that design
   decision costs something; **not proposed**, because extending the overlay to
   CT classes is a cross-ISO design change and its direction at `CT_PEAKER`
   (which is already 63–86 % short) is adverse.
4. **The nyiso-174 carry-forwards that this session did not reach** stand
   unchanged: the outage-extract routing defect (§6 item 1 there), S A Carlson's
   extract side, `wefor_residual = null`, and the model's East River heat-rate
   allocation note.
5. **`nyiso_gas_bridge_ct` has no matrix cell** — it is adjudicated only in the
   2026-07-27 calibration-log entry (probe, rejected, default-off). A rule 28(c)
   gap; recorded, not repaired here, because the row lives in the shared
   base file and touching it is a cross-ISO edit.

---

## 8. Honest expected value

**What is delivered.** (a) The blocker the brief put first is **cleared on
identities rather than on argument** — two of them, both computable from
committed bytes, one of which (`hydro` agreeing to four decimals) is decisive on
its own — and the answer is that *neither artifact was wrong*, which is why the
successor object it was blocking is now readable. (b) The brief's own
carried-forward rule 20 hazard is **withdrawn on the code**, and a *different*
number in the same family is **corrected upward by 1.8×**. (c) The new `CT_CHP`
instrument is spent, and it **splits the object**: two classes, opposite
signatures, unanimous across three years, which retires the framing that the
−2.4 TWh CT deficit is one lane. (d) `CT_PEAKER`'s closed diagnosis is
**independently confirmed** on a construction, bar and keeper none of
nyiso-90/91/96 used — so the strongest reason not to spend anything on it is now
reproduced rather than inherited. (e) The one obvious successor route
(`chp_steam_following` with a measured hourly steam profile) is **closed before
it is built**, on the plant's own steam meter. (f) The real object underneath is
**named, sized to 15.233 TWh, attributed 56 % to Ravenswood rather than East
River, and traced to a single line of a derive script**, with its C3a
expectation honestly stated as ~zero so nobody proposes it as a C3a lever.

**What is NOT delivered, plainly.** **No movement on C3a-2025, and none was
available.** §3.4 is the measurement that says why: `CT_CHP`'s deficit is
**88–100 % in the bottom 80 % of load hours**, while nyiso-168 located 73 % of
the C3a-2025 deficit in the 50–90 band. The two objects barely overlap. The gain
law, the 55 %-vs-118 % non-physical steepness deficit and the $27.79–$56.03/MWh
pass window are exactly where nyiso-168 left them. **No solve was run and no run
was registered** — correct under rule 15, not an omission — and **no arm was
pre-registered**, because both of the pre-registered gates that would have
licensed one failed.

**What a successor should NOT do with this.** Do not re-open the D-2 vs
`class_hourly` question; it is a grain difference and it is closed in both
directions. Do not open a `CT_PEAKER` lever — the diagnosis is confirmed twice
over and its cause is owner-closed. Do not put a floor on `CT_CHP`: §4.2 shows
the floor is already at the plant's measured p05 and the gap is at its p25–p50,
so a floor large enough to close it would bind in hours the plant was
demonstrably below it (rule 17 `[R-FLOOR-WINDOW]`). Do not propose the S3
attribution repair as a C3a lever (§4.5). And do not quote the East River
heat-rate refutation of CAMPD's `"Combined cycle"` label (correction 3).

---

## 9. Governance

* **Rule 1 `[R-STRUCT]`** — no adder, haircut or offer re-level was built. The
  two routes the trap named (an offer re-level, a CHP floor) were both reached
  by the measurement and both refused on the measurement: §3.4/§4.2 for the
  floor, nyiso-170 §5 unchanged for the re-level.
* **Rule 13 `[R-MEASURED]`** — every input is a reproducible measured record
  used for classification, attribution or characterisation. Nothing is pinned to
  an outcome; no statistic was tuned to a residual.
* **Rule 14 `[R-ACCURATE]`** — the handed-forward attribution repair is
  proposed *because* it is the accurate input, with its expected C1 direction
  disclosed and its C3a expectation stated as ~zero in advance.
* **Rule 15 / 16** — no LP ran, so nothing is registrable; no single-year
  anything was produced. Every year read is 2023, 2024, 2025.
* **Rule 19 `[R-ONE-MECH]`** — §5 enumerates before anything is proposed, and
  the one live mechanism on `CT_CHP` would be **replaced**, never stacked.
* **Rule 20 `[R-FORCED-BUDGET]`** — the CHP classes are exempt by construction;
  the corrected forced share is reported at full magnitude anyway.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only. NYISO holds no `complete` marker
  (withdrawn 2026-08-30) and is absent from `final`; none was requested and the
  freeze is untouched.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no measured-behaviour parameter was
  re-derived. The handed-forward re-derivation cites an attribution **defect**,
  not a residual.
* **Rule 28 `[R-MECH-MATRIX]`** — the tested cells are updated in
  `docs/codebase-site/data/mechanism-matrix/NYISO.js` in this session
  (`chp_steam_following`, `thermal_tranche_artifact_coverage`,
  `scuc_load_pocket_commitment`, `diagnostics_plant_set`,
  `measured_chp_heat_rates`), NYISO's shard only.
* **Pre-registration integrity.** Gates A1, A2, B5, S2, S3, S4 and S5 are
  reported at the thresholds committed at `6c3f0cf7`, before the probe ran; none
  was moved after a result was seen. Two blocks (§2.2 / §2.3's identities and
  §3.5's steam driver) are **post-hoc**, are labelled as such in both this
  document and the probe output, and neither is used to reverse a gate verdict.

---

## 10. Evidence

* `results/calibration/PREREG-nyiso175-ct-conduct-and-d2-basis.md` — committed
  with the probe at `6c3f0cf7`, before either ran
* `scripts/probes/nyiso175_ct_conduct_and_d2_basis.py` — A / B / B6 / B7 / C +
  the rule 19 enumeration, zero solve
* `results/calibration/_nyiso175_ct_conduct_and_d2_basis.json` — full output
* Prior: `docs/FINDING-nyiso174-east-river-class-crosswalk-2026-09-02.md`
  §4.3, §5, §6 · `docs/FINDING-nyiso173-cc-availability-envelope-not-binding-2026-09-02.md`
  §2.5 · `docs/FINDING-nyiso171-chp-floor-portfolio-artifact-2026-09-01.md`
  §2.5–§2.6 · `docs/FINDING-nyiso170-merit-order-displacement-2026-09-01.md`
  §3, §5 · `docs/FINDING-nyiso168-supply-curve-slope-anatomy-2026-09-01.md`
  §2, §6.3 · `docs/FINDING-nyiso96-ct-start-frequency-2026-07-29.md` §2, §5 ·
  `docs/FINDING-nyiso91-ct-start-frequency-2026-07-27.md` §5–§6 ·
  `docs/FINDING-nyiso90-ct-block-commitment-2026-07-27.md` §2 ·
  `results/calibration/FINDING-nyiso120-eastriver-scope-gate-2026-08-04.md`
  KE1–KE3
