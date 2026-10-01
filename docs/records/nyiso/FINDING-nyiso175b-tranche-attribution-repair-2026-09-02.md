# FINDING — nyiso-175b: the per-unit attribution repair is BUILT and VALIDATED at artifact level, it resolves nyiso-174 §6 item 2's named object, and a NEW blocker — the keeper's tranche input is not reproducible at HEAD — is what stops it becoming a scored run, not anything about the repair itself

**Session:** nyiso-175 (second charter; the first is discharged and merged —
`docs/FINDING-nyiso175-ct-deficit-two-objects-2026-09-02.md`).
**Keeper:** `2026-08-30-nyiso-159-loss-surface`, determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}. **Unchanged — no LP ran, so rule 15 registers nothing.**
**Pre-registration:** `results/calibration/PREREG-nyiso175b-tranche-attribution-repair.md`,
committed at `22bfe37a` **before** the probe or any derivation was run.

---

## 0. The result in one paragraph

The object nyiso-175 §4.4 handed forward is **real, larger than one plant, and
now repaired in code**: `derive_thermal_tranches` attributed a plant's
*facility-summed* CAMPD net to its *largest-nameplate* group, so at a mixed
plant one bin received the whole facility's conduct and the others received
none. All **four pre-solve gates PASS** — after **K2 failed as first constructed
and forced an amendment to the construction, never to the threshold**. The
repair is implemented behind a default-off flag on **both** artifacts that carry
the defect (the tranche deriver and the outage extract), and its artifact-level
effect is measured on an **unconfounded HEAD-vs-HEAD** basis: 13 of 85 tranche
rows, confined to seven plants. **It resolves nyiso-174 §6 item 2's named
object** — East River's measured `ST_CHP` row correctly disappears (its boilers
generate 0.000 TWh) and a `CT_CHP` row appears at 306.0 MW / 26,251 online hours
/ `chp_pmin_cf` 28.4, moving the must-run to the half the market's measurably is
in. **No LP was run**, and the reason is a blocker this session discovered
rather than a judgement about the repair: **the keeper's committed tranche
artifact is not reproducible at HEAD.** A fresh unrepaired derivation differs on
**46 of 78 rows**, `online_hours` by up to **26,271**, and at two of the seven
repair-affected plants the HEAD drift **exceeds the repair itself**. Every route
to a scored run therefore either imports 40 rows of unadjudicated drift at
untouched plants or needs a transfer construction that was not pre-registered.
The repair is delivered ready to solve; the drift is named, sized and handed
forward as its precondition.

---

## 1. What was measured, and off what

| input | what it is |
|---|---|
| `data/raw/campd-unit-level/NY_{2023,2024,2025}.parquet` | CAMPD unit-hourly, the only source carrying unit identity |
| `data/raw/_processed-legacy/thermal_tranches_NYISO.csv` | the **keeper's** tranche input, 78 rows, vintage **unknown** |
| `data/raw/campd-unit-outages-NYISO.csv` | the keeper's outage extract, 4,423 windows |
| model fleet (`load_fleet_from_csv("NYISO")`) | the EIA-860 classification the LP and the benchmark both use |

Three derived artifacts, **all three produced at this HEAD** so the comparisons
below are unconfounded:

* **S-0 control** — `derive_thermal_tranches --iso NYISO --years 2023 2024 2025`,
  unrepaired. 79 rows. Committed as
  `results/calibration/_nyiso175b_tranches_NYISO_S0_control.csv`.
* **ARM** — the same invocation `--per-unit-attribution`. 85 rows. Committed as
  `data/raw/_processed-legacy/thermal_tranches-perunit-NYISO.csv`.
* **outage companion** — `derive_campd_unit_outages --iso NYISO
  --per-unit-crosswalk`, written to `campd-unit-outages-perunit-NYISO.csv`
  (1,996 windows), with its own HEAD-unrepaired control (2,632 windows).

### 1.1 Reproduction traps honoured

Traps (c), (d) and (f) of the inherited corpus all apply and are handled in
`scripts/probes/nyiso175b_tranche_attribution_repair.py`. **Two more were found
here and are recorded because both fail SILENTLY**, which is the class of defect
this corpus keeps paying for:

* **`facilityId` is a STRING dtype** in the NY unit-level parquets. An
  unconverted `== 2493` matches nothing and returns an empty frame, not an error.
* **NY exists in BOTH `campd-facility-level/` and `campd-unit-level/`, and
  `_read_one` resolves facility-first.** The first repaired derivation therefore
  ran against a frame whose units the publisher had already summed away, and
  **silently reproduced facility attribution under a per-unit name** — the exact
  defect being repaired, made invisible. It is caught now by a guard that
  RAISES; see §3.2.

---

## 2. The four pre-solve gates

Verdicts from `results/calibration/_nyiso175b_tranche_attribution_repair.json`.

### 2.1 K1 — the object is the size its predecessor measured: **PASS**

**13.7577 TWh** re-seated over 2023-2025 (bar 4.0), **4.5293 / 4.5612 / 4.6672**
by year, across **six** plants:

| plant | primary (by nameplate) | actual carrier | margin | re-seated TWh |
|---|---|---|---|---|
| 2493 East River | `ST_CHP` 309.5 MW | **`CT_CHP`** | **3.5 MW (1.1 %)** | 6.5811 |
| 2500 Ravenswood | `ST_GAS` 1,724.8 MW | **`CC_REGULAR`** 222.2 MW | 1,502.6 MW | 5.8467 |
| 50292 Bethpage | `CC_REGULAR` 129.0 MW | **`CT_PEAKER`** | — | 0.5006 |
| 2511 E F Barrett | `ST_GAS` 372.2 MW | **`CT_PEAKER`** | — | 0.4570 |
| 2517 Port Jefferson | `ST_GAS` 385.0 MW | **`CT_PEAKER`** | — | 0.2302 |
| 2682 S A Carlson | `ST_GAS` 45.0 MW | **`CT_PEAKER`** 42.0 MW | 3.0 MW | 0.1422 |

The measured per-class split at the three named plants, all three years:

* **East River** — `CT_CHP` 2.1335 / 2.2590 / 2.1886 TWh against `ST_CHP`
  **0.0000 / 0.0000 / 0.0000**. The steam bin's measured output is *zero*, in
  every year, and it is the bin the nameplate rule hands the whole plant to.
* **Ravenswood** — `CC_REGULAR` 1.9667 / 1.9562 / 1.9238 against `ST_GAS`
  0.8834 / 0.7090 / 1.0701. The 222.2 MW bin outproduces the 1,724.8 MW bin
  roughly two to one.
* **S A Carlson** — `CT_PEAKER` 0.0424 / 0.0288 / 0.0710 against `ST_GAS`
  0.0000 in every year.

**Note the honest discrepancy with the predecessor.** nyiso-175 §4.4 reported
15.233 TWh; this measures 13.7577. The two count different things — that
session summed the affected plants' whole CAMPD energy, this sums only the
units whose corrected class differs from the plant's primary group, and it
applies the K2 fallback below. Same object, tighter denominator; **quote
13.7577 for the repair's footprint and 15.233 for the plants' total conduct.**

### 2.2 K2 — a STRICT crosswalk repair: **FAILED as first constructed, then PASS**

This gate did its job and is the most important result in this section.

As first written the repair had **no fallback**, and K2 caught **three
ST_GAS-only plants** — 2490, 8906 and **2516 Northport** — whose CAMPD
combustion turbines correct to `CT_PEAKER`, a bin those plants **do not carry**.
Their energy (0.0029 / 0.0021 / 0.0001 TWh, **0.0051 TWh** over three years)
would have been silently dropped out of the `ST_GAS` denominator. Small — and
irrelevant to whether the gate binds: that is a **reclassification**, not a
crosswalk repair, and the pre-registration says a K2 failure stops the lane and
re-derives.

**The CONSTRUCTION was amended, never the threshold** (the same discipline
nyiso-175 §4.5 applied to its own S5): `reseat_group` now leaves a unit on the
plant's primary group **wherever the plant carries no bin in the unit's own
prime-mover family**. The repair's warrant is *"attribute a unit's energy to the
bin that contains it"*; where there is no such bin the repair has nothing to
say. Re-run: **PASS**, 0 offenders over 96 single-thermal-group plants, and K1
tightens from 13.7628 to 13.7577 over 11 → 6 plants.

### 2.3 K3 — rule 19 `[R-ONE-MECH]`: **PASS**, and it found more than it asked

Measured by **calling the production resolver**, not by reading it. The existing
miso-200 `mixed_gas_routing` gate does **not** reach East River: `_GAS_BIN_GROUPS`
is `{CC_REGULAR, CC_CHP, ST_GAS, ST_CHP}` and **excludes both CT classes**, so
`{CT_CHP, ST_CHP}` intersects it at size 1, `_is_multi_gas_facility` returns
**False**, and units 1/2 resolve to `ST_CHP` with the gate **on or off**.

**The gate is also actively WRONG where it does fire.** At Ravenswood it routes
the combined-cycle block's `CT0001` / `CT0010` / `CT0011` to **`CT_PEAKER`** —
outside `QUALIFYING_PLANT_GROUPS`, so the overlay **drops them entirely** —
although those three are among the 27 units the liquid-fuel guard's own evidence
names as *"GAS-fired members of a genuine block that must keep inheriting it"*.
The per-unit crosswalk keeps them on `CC_REGULAR`. **Arming the existing gate
for NYISO would therefore have traded one mis-routing for another**, which is
exactly what rule 19 asks a session to find out before adding anything.

### 2.4 K4 — the carrier bins genuinely lack a row today: **PASS**

East River `CT_CHP`, Ravenswood `CC_REGULAR` and S A Carlson `CT_PEAKER` are all
in the model fleet and **none has a row** in the committed tranche CSV, while
each plant's *primary* row is present. The bins carrying the energy are the bins
with no measured parameters.

---

## 3. The repair, and what it does to the artifacts

### 3.1 Two flags, one crosswalk, both default-off companions

| deriver | flag | companion written |
|---|---|---|
| `derive_thermal_tranches.py` | `--per-unit-attribution` | `thermal_tranches-perunit-<ISO>.csv` |
| `derive_campd_unit_outages.py` | `--per-unit-crosswalk` | `campd-unit-outages-perunit-<ISO>.csv` |

Both route by the **same** function —
`scripts.lib.campd_measured_classes.corrected_unit_class` — so the two repairs
**cannot disagree about which bin a machine belongs to**. Neither overwrites an
incumbent artifact, matching the `-unitroute-` discipline: the off path stays
byte-inert and each repair is a clean single delta. **Zero free parameters** in
both (rule 21 `[R-DOF]`); the inputs are EIA-860 prime movers and CAMPD unit
types, static attributes that regenerate for any forward year (rule 13
`[R-MEASURED]`); and it is a crosswalk repair justified by the attribution
defect, not a re-derivation against a residual (rule 23 `[R-FROZEN-DERIVE]`).

The outage half's routing, unit-tested on all six cases:

| unit | gate OFF | `mixed_gas_routing` | **per-unit crosswalk** |
|---|---|---|---|
| East River 1/2 (turbine) | `ST_CHP` | `ST_CHP` | **`CT_CHP`** |
| East River 60/70 (boiler) | `ST_CHP` | `ST_CHP` | `ST_CHP` (no-op) |
| Ravenswood CT0001/10/11 | `ST_GAS` | `CT_PEAKER` *(dropped)* | **`CC_REGULAR`** |
| Ravenswood 10/20/30 (boiler) | `ST_GAS` | `ST_GAS` | `ST_GAS` |

Measured in the committed extract: **all 93 East River windows sit on `ST_CHP`**,
units 1 and 2 included — confirming nyiso-174 §6 item 1 and **sizing it beyond
that session's two 2023 windows**: the mis-routing spans 2018-2026, with units
1/2 contributing 8 and 13 windows respectively. **All 185 Ravenswood windows sit
on `CC_REGULAR`**, including its three steam boilers — the miso-200 Ninemile
pattern, in an ISO where nobody had looked.

**The outage delta, on the same unconfounded HEAD-vs-HEAD basis** (committed
4,423 → S-0 control **2,632** → arm **1,996**; the committed→S-0 step is
**−1,791 windows of pure HEAD drift**, see §4, and only the S-0→arm step of
**−636** is the repair). **22 units re-routed, zero added**, every one
explicable:

| units | S-0 → arm | windows | reading |
|---|---|---|---|
| 2493 East River 1, 2 | `ST_CHP` → **`CT_CHP`** | 8 + 8 | the intended repair — the GT windows leave the steam bin and derate the turbine bin, which qualifies for the overlay |
| 2500 Ravenswood 10, 20, 30 | `CC_REGULAR` → **`ST_GAS`** | 25 + 23 + 22 | the three steam boilers stop derating the 222 MW CC bin |
| 2511 E F Barrett U00004-U00019 (16 units) | `ST_GAS` → **dropped** | ~590 | correctly recognised as combustion turbines; `CT_PEAKER` is outside `QUALIFYING_PLANT_GROUPS`, so peakers carry no overlay **by existing design** |
| 2682 S A Carlson 20 | `CC_REGULAR` → dropped | 32 | same |
| 50292 Bethpage GT3 | `CC_REGULAR` → dropped | 14 | same |

The E F Barrett group is the largest single effect and is worth stating
plainly: **today 16 combustion turbines' windows derate that plant's STEAM bin.**
Removing them makes the `ST_GAS` bin *more* available — the same adverse
direction nyiso-174 §6 item 1 flagged for East River — so this repair is
**not** expected to help the CT deficit, and is proposed only because the
routing is wrong.

### 3.2 Two guards, both earned during this session

`campd.plant_group_hourly_net` **raises** when the frame lacks `unit_id` /
`unit_type` (the curated `emissions` clean datatype carries neither, so under
`MARKET_SIM_USE_CLEAN` the attribution is impossible), **and raises when every
`unit_id` is blank**, which is a facility-level extract. The second guard exists
because its absence produced a wrong answer that looked right — see §1.1. The
loader gained `prefer_unit_level` so a caller that needs unit identity asks for
it explicitly; the default resolution order is unchanged, keeping ERCOT and the
existing PJM states bit-for-bit.

### 3.3 The artifact delta — unconfounded, both legs at HEAD

**13 of 85 rows**, all at the seven affected plants.

**Seven new rows:**

| plant | new bin | MW | online h | committed % | median CF | `chp_pmin_cf` |
|---|---|---|---|---|---|---|
| 2493 East River | `CT_CHP` | 306.0 | 26,251 | 30.1 | 81.0 | **28.4** |
| 2500 Ravenswood | `CC_REGULAR` | 222.2 | 23,607 | 70.0 | 113.9 | — |
| 2511 E F Barrett | `CT_PEAKER` | 281.4 | 5,750 | 6.4 | 23.1 | — |
| 2517 Port Jefferson | `CT_PEAKER` | 82.7 | 3,943 | 21.8 | 55.6 | — |
| 2682 S A Carlson | `CT_PEAKER` | 42.0 | 3,913 | 70.0 | 90.5 | — |
| 50292 Bethpage | `CT_PEAKER` | 44.1 | 11,596 | 34.0 | 104.4 | — |
| 10025 RED-Rochester | `CT_CHP` | 36.0 | 0 | — | — | 0.0 |

**One dropped row:** S A Carlson `ST_GAS` (120 h, `median_cf` 150.0 — a capped,
physically meaningless value). Its 3,913 online hours reappear on `CT_PEAKER`,
**recovering the committed artifact's own `online_hours` on the correct bin** —
an independent corroboration the repair is finding the right machines.

**Five changed rows:** East River `ST_CHP` `ok` → `eia923_cf` (23,160 → 0 h);
Ravenswood `ST_GAS` 23,472 → 7,293 h, committed 17.7 → 6.5; E F Barrett 25,006 →
24,270; Port Jefferson 9,840 → 8,101; Bethpage `CC_REGULAR` 20,103 → 19,886.

**This resolves nyiso-174 §6 item 2.** That session named the object as *"which
half of East River carries the must-run"*, with the model flooring the steam bin
and the market's must-run measurably in the turbine half. Under the repair the
steam bin loses its measured row entirely and the turbine bin gains one carrying
a `chp_pmin_cf` of 28.4 on 306.0 MW. The floor moves to the half the meters say
is running.

### 3.4 One negative result, reported at full strength

**The physically-impossible `median_cf > 100` census barely improves: 11 → 10.**
The repair removes the two it causes (2493/`ST_CHP` 118.3, 2682/`ST_GAS` 150.0)
and Ravenswood's new `CC_REGULAR` row introduces one at 113.9. So a
capacity factor above nameplate is **not** a general signature of this defect —
above-nameplate CEMS gross has other causes (the gross-vs-summer-nameplate
basis, CEMS noise) that this repair does not touch, and it must not be quoted as
evidence for it. Ten remain in the arm.

---

## 4. THE BLOCKER — the keeper's tranche input is not reproducible at HEAD

This is new, it is not in any brief, and it is what stops the session at the
artifact boundary.

`thermal_tranches_NYISO.csv` is the keeper's input. Its sidecar records
`derive_invocation: null`, `vintage: unknown`, and states in terms: *"It makes
no claim about what HEAD would emit."* It does not. **A fresh unrepaired
derivation at HEAD over the same 2023-2025 window differs on 46 of 78 common
rows:**

| column | rows differing | max abs delta |
|---|---|---|
| `online_hours` | 46 | **26,271** |
| `median_cf` | 37 | 65.6 |
| `committed_pct` | 35 | 27.2 |
| `p25_cf` | 34 | 50.0 |
| `chp_pmin_cf` | 14 | 37.2 |
| `nameplate_mw` | 3 | 102.0 |

Plus one extra row. The three `nameplate_mw` moves are HEAD's own fleet
reconciliations (plants 7314, 10190, 56196, logged at load). The rest is
detector and source drift accumulated since an unknown derive date.

**Why this blocks a scored run.** Of the 71 rows at plants the repair does *not*
touch, **40 drift at HEAD**. A solve on the fully re-derived arm would carry the
repair *and* all 40 of those, and could attribute neither — exactly the confound
miso-200 refused when it chose to relabel the committed extract rather than
re-derive it. And the obvious escape — a minimal-delta arm that keeps committed
values everywhere except the seven affected plants — **does not work here
either**, because at two of those seven the drift is *larger* than the repair:

| plant | drift (committed → S-0) | repair (S-0 → arm) |
|---|---|---|
| 50292 Bethpage `CC_REGULAR` | 22,440 → 20,103 h (**−2,337**) | 20,103 → 19,886 h (−217) |
| 2511 E F Barrett `ST_GAS` | 21,956 → 25,006 h (**+3,050**) | 25,006 → 24,270 h (−736) |

At East River and Ravenswood the repair dominates comfortably (a deleted row and
a −69 % move against −12 % and −5 % drifts), but two plants where the confound
inverts is enough: the A/B would not be a single object. **A clean A/B needs a
control leg — two three-year solves — and even then the arm could not be
promoted, because promotion would import the drift as an unadjudicated change.**

### 4.1 It is not one artifact — the outage extract drifts too, and harder

The same test on the outage extract: committed **4,423** windows, HEAD
unrepaired **2,632**. **−1,791 windows, 40 %, from nothing but re-running the
deriver at HEAD.** So *both* NYISO solve inputs this session touches are
non-reproducible, and the outage one more severely in proportion. Any A/B that
re-derives either carries that drift.

**The drift is therefore the precondition, not a footnote.** It is the same
family as nyiso-175's own handed-forward item 2 (the D-2 reproducibility gap),
and it is larger and broader: there the *diagnostic* could not be re-derived
from committed bytes; here **two solve inputs** cannot.

---

## 5. Rule 19 `[R-ONE-MECH]` enumeration — what already routes a CAMPD unit to a bin

| mechanism | where | reaches East River? | reaches Ravenswood's block CTs? |
|---|---|---|---|
| `fac_group` short-circuit (pjm-75) | `_resolve_unit_group` | routes both to `ST_CHP` / `ST_GAS` — the defect | — |
| liquid-fuel CT guard (neiso-99, rule 14) | same, runs first | no (units are gas-fired) | no |
| `mixed_gas_routing` (miso-200, default off) | same | **no** — `_GAS_BIN_GROUPS` excludes CT classes | yes, but to the **wrong** bin (`CT_PEAKER`) |
| `forced_group` steam-host rebuild | outage deriver | only orphaned gross-blank boilers | no |
| **`per_unit_crosswalk` (this session, default off)** | same | **yes → `CT_CHP`** | **yes → `CC_REGULAR`** |
| `_fleet_nameplate_and_group` primary rule | tranche deriver | attributes the whole facility to `ST_CHP` — the defect | attributes it to `ST_GAS` |
| **`--per-unit-attribution` (this session, default off)** | same | **yes** | **yes** |

No mechanism is stacked: each repair **replaces** a routing decision at the
plants where the incumbent rule is wrong and is a no-op everywhere else.

---

## 6. Corrections to the committed record

1. **nyiso-174 §6 item 1's size is understated.** It reports *"two windows, both
   in 2023"* for East River's mis-routed turbines. The committed extract carries
   **21** windows on units 1/2 (8 and 13), spanning **2018-2026**; 2023 is
   simply where the training window clips it. The 2023 pair (33.5 d from
   09-15, 18.5 d from 10-21) is reproduced exactly.
2. **The mis-routing is not East-River-specific.** All **185** Ravenswood
   windows sit on `CC_REGULAR`, its three steam boilers included — a second,
   larger instance in the same ISO, in the opposite direction (steam windows
   derating a CC bin).
3. **nyiso-175 §4.4's 15.233 TWh and this session's 13.7577 TWh are different
   statistics, not a disagreement** — see §2.1.
4. **`mixed_gas_routing` is not a safe transfer to NYISO.** Its miso-200
   adjudication does not carry: at Ravenswood it drops three block CTs from the
   overlay. Rule 25 `[R-ISO-SCOPE]` working as intended.

---

## 7. Lines this session closes, and what is handed forward

### Closed

* **CLOSED — "does the existing `mixed_gas_routing` gate already cover the East
  River routing defect?" NO**, measured by calling the resolver, and it is
  *wrong* at Ravenswood where it does fire (§2.3). Do not re-open as
  "just arm the existing flag for NYISO".
* **CLOSED — "is the tranche attribution defect a real, sizeable object?" YES**,
  13.7577 TWh across six plants, all four pre-solve gates passed (§2).
* **RESOLVED — nyiso-174 §6 item 2, "which half of East River carries the
  must-run."** Under the repair the floor moves to the turbine bin
  (`chp_pmin_cf` 28.4 on 306.0 MW) and the steam bin loses its measured row
  (§3.3). Resolved *in the artifact*; its dispatch consequence is unmeasured
  because no LP ran.
* **NOT OPENED — any parameter, band, floor or offer change**; **no C3c lever**;
  **none of the twenty-six closed lines re-tested.**
* **REFUTED — "median_cf > 100 is a signature of this defect."** 11 → 10 (§3.4).

### Handed forward

1. **THE TRANCHE-ARTIFACT REPRODUCIBILITY GAP (§4) — now the precondition for
   everything else.** 46 of 78 rows, `online_hours` to 26,271, vintage unknown.
   Until it is adjudicated, no NYISO tranche change can be scored as a single
   object. Two candidate routes, neither pre-registered here: (a) adjudicate the
   drift on its own and re-baseline the keeper's input at HEAD, then land the
   repair on top as a clean delta; (b) run the A/B with a HEAD control leg
   (**two** three-year solves) purely to measure the repair, accepting that the
   arm is not promotable. **(a) is the better buy** — it fixes the reason (b)
   costs double.
2. **THE A/B ITSELF, ready to run.** Both companions exist and are committed.
   With the drift settled, the arm is `--per-unit-attribution` +
   `--per-unit-crosswalk` together, three years, one bundle. **They must land
   together**: the repaired tranche row for East River's `CT_CHP` bin is
   currently derived against an **un-derated** denominator, because every one of
   the plant's outage windows is still routed to `ST_CHP`. The two repairs are
   coupled, exactly as nyiso-175 said.
3. **THE SOLVE-SIDE SELECTOR IS NOT BUILT.** Nothing in `src/` reads the
   `-perunit-` tranche companion: the path is hardcoded at **11 call sites**
   (`campd_bins.py` ×9, `coal.py`, `chp.py`), and 9 of the 11 take only `iso`,
   no config. Wiring it needs a resolver plus threading a `ScenarioConfig` field
   (rule 24) through those callers. The outage half **is** already wired — its
   companion pattern exists (`unit_outage_csv_for_iso`) and needs only the new
   mode added.
4. **S A Carlson's 120-hour `ST_GAS` row with `median_cf` 150.0** is a
   capped, physically meaningless statistic in the *control*, and the same
   plant's committed row reads 3,913 h. Whatever produced that collapse is part
   of the §4 drift and is a good place to start diagnosing it.
5. **nyiso-175's own carry-forwards stand unchanged**: the D-2 `dispatch_source`
   provenance stamp, the `CT_CHP` maintenance shape (recorded, not proposed),
   `wefor_residual = null`, and `nyiso_gas_bridge_ct`'s missing matrix cell.

---

## 8. Honest expected value

**What is delivered.** A real defect, sized on its own evidence, repaired in
code behind default-off flags on both artifacts that carry it, with the repair's
artifact-level effect measured on an unconfounded basis and one of its
predecessor's named objects resolved. Two silent-failure traps found and
guarded, one of which had already produced a wrong answer that looked right. A
rule 19 enumeration that stopped a plausible-looking shortcut (arming
`mixed_gas_routing`) which would have introduced a new mis-routing.

**What is NOT delivered, and will not be oversold.** No LP ran, so **there is no
C1 number, no D-1 profile, no C3a-2025 number, and nothing to register on the
dashboard**. The keeper and its NOT-YET determination are untouched. The
predicted C1 direction from nyiso-175 §4.5 (`CT_CHP` +0.378 / +0.965 / +0.402
TWh, `ST_CHP` −0.064 / −0.343 / −0.713) remains **predicted, not measured**.

**What it is worth when it does run.** Per the pre-registration and nyiso-175
§4.5, **the C3a-2025 expectation is ~zero** — both East River bins carry heat
rate 7.4205 and the same delivered gas, so moving energy between them changes no
unit's marginal cost and no marginal price. Gate **K5** was written to *fail* a
large favourable C3a move for exactly this reason. This is a **C1 /
representation repair proposed on rule 1 `[R-STRUCT]` grounds**, and it must
never be presented as a route to the load-bearing C3a-2025 failure. Its value is
that the model's CHP and steam bins stop being parameterised from machines that
are not in them — and that the next session working East River or Ravenswood is
reading measured statistics attached to the right bins.

**The honest headline is the blocker, not the repair.** The repair was the easy
half. The finding that a keeper's own solve input cannot be regenerated at HEAD
is the one that should change what the next session does first.

---

## 9. Governance

* **Rule 1 `[R-STRUCT]`** — the repair is justified by the primary record
  (EIA-860 prime movers, CAMPD unit types, the plant's own model roster), not by
  a residual. Nothing was tuned; no LP was consulted in building it.
* **Rule 13 `[R-MEASURED]`** — inputs are static unit attributes that regenerate
  for a forward year. No measured *outcome* enters.
* **Rule 14 `[R-ACCURATE]`** — the accurate input is kept. Its backcast effect is
  unmeasured; if it degrades, §8 and the prereg both bind the successor to
  diagnose rather than revert.
* **Rule 19 `[R-ONE-MECH]`** — §5 enumerates before adding; each repair replaces
  a routing decision rather than stacking on one.
* **Rule 21 `[R-DOF]`** — zero free parameters in both flags.
* **Rule 23 `[R-FROZEN-DERIVE]`** — a crosswalk repair citing the attribution
  defect, not a re-derivation against a residual.
* **Rule 24** — the two derive flags are CLI-side and write **separate
  companions**; **no `ScenarioConfig` field was added**, because nothing in a
  solve reads them yet (handed forward, item 3). No off-registry channel exists.
* **Rule 25 `[R-ISO-SCOPE]`** — the code is ISO-agnostic; **only NYISO's
  artifacts were derived.** Every other ISO's committed tranche and outage CSVs
  are byte-untouched.
* **Rule 22 `[R-HOLDOUT]`** — every year read is 2023 / 2024 / 2025. NYISO holds
  no `complete` marker, none was requested, the freeze is untouched.
* **Rule 15 / 16** — no solve, so nothing is registered; that is correct, not an
  omission.
* **Tests** — 167 campd + 758 tranche/outage/fleet pass. One failure,
  `test_capacity_evolution_changes_fleet` (`RuntimeError` in
  `confirmed_retirements.py:168`), **reproduces on a clean stash of HEAD** and is
  pre-existing.

---

## 10. Evidence

| artifact | what it holds |
|---|---|
| `results/calibration/PREREG-nyiso175b-tranche-attribution-repair.md` | the four pre-solve gates and the post-solve kills, committed at `22bfe37a` before anything ran |
| `scripts/probes/nyiso175b_tranche_attribution_repair.py` | the gate probe, incl. `reseat_group` and the K2 amendment |
| `results/calibration/_nyiso175b_tranche_attribution_repair.json` | all four gate verdicts and the per-plant census |
| `results/calibration/_nyiso175b_tranches_NYISO_S0_control.csv` | the HEAD-unrepaired control derivation (79 rows) |
| `data/raw/_processed-legacy/thermal_tranches-perunit-NYISO.csv` | the repaired tranche companion (85 rows) |
| `data/raw/campd-unit-outages-perunit-NYISO.csv` | the repaired outage companion |
| `src/market_sim/data/campd.py` | `plant_group_hourly_net`, the two guards, `prefer_unit_level` |
| `scripts/data/derive_thermal_tranches.py` | `_per_unit_group_resolver`, `--per-unit-attribution` |
| `scripts/data/derive_campd_unit_outages.py` | `per_unit_crosswalk`, `--per-unit-crosswalk` |
