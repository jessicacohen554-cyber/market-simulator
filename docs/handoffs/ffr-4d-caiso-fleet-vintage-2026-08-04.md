# FFR-4D — CAISO's 11,711 MW base-year accreditation shortfall, decomposed and half fixed

**Lane.** FC-2 row 4, chartered against the FLEET-VINTAGE cause (FFR-3P B-1) by owner
decision D-15, sitting Addendum O, 2026-08-04. Branch
`claude/caiso-fleet-capacity-shortfall-rahkb5`, based on `origin/main` **`5eac75b0`**
(re-verified at this head; the packet cited the same).

**The anchor route was NOT taken.** No CAISO capacity-price anchor, net-CONE, CPM
soft-offer cap or entry-screen term was read, changed, or quoted anywhere in this work.
Every number below is a fleet or accreditation quantity. §8 states this formally.

---

## 0. Headline — four findings, and the second one changes the charter's premise

1. **The shortfall is NOT all fleet. It is 47.3 % fleet coverage and 52.7 % accreditation
   rate and class boundary.** Correcting the base-year fleet from the model's own
   committed EIA-860 release recovers **+5,540.3 MW** of the 11,711 MW. That is measured
   from the shipped accreditation chain, not projected.

2. **Correcting the fleet alone moves the reserve position 0.8852 → 0.9819, NOT to
   1.0896.** The charter's premise — inherited from FFR-3W §5.3 — reads *"correcting the
   fleet alone moves the reserve position 0.8852 → 1.0896 (11.5 % short → 9.0 % long) and
   collapses row 4's numerator."* **That arithmetic assumed the entire 11,711 MW gap was
   fleet** (50,729 + 11,711 = 62,440; 62,440 / 57,306 = 1.0896). It is not. After the
   fleet is right CAISO is still **1.8 % SHORT**, so the adequacy need does **not**
   vanish and row 4's numerator does **not** collapse. This is the charter's own
   *"if row 4 does not clear after the fleet is right, THAT IS THE FINDING"* branch, and
   it is the branch that fired. Nothing was tuned in response (rule 11).

3. **FFR-3P's own §1.1 hydro row is wrong and reverses sign — its B-2 caveat resolves
   AGAINST the row.** CAISO's Table 1.1 Hydro line **does** include pumped storage. The
   −1,670.2 MW hydro deficit becomes **+292.6 MW of surplus**, and the 1,962.8 MW moves
   into the storage row, taking it from −5,933.2 to **−7,896.0 MW**. The 11,711 MW total
   is unchanged — only the attribution moves — but the attribution is what a fix lane
   acts on. §2 proves it two independent ways.

4. **`load_eia860_storage` was ORPHANED, which made `storage_vintage_ramp` a dead flag
   for batteries on every keeper that armed it — including CAISO's.** The runner built
   the storage fleet from a flat forecast scalar in **both** modes, so a 2023 backcast ran
   on a 2026 constant. §5.

**What is fixed here:** the base-year fleet, both channels (§4). **What is routed, not
fixed:** the accreditation-rate and class-boundary residual (§6), which is the whole of
what remains and whose largest single term — battery — has **no mechanism at all**.

---

## 1. State re-verified at this head

| item | verified |
|---|---|
| `origin/main` | `5eac75b0` |
| CAISO keeper | **`2026-08-04-caiso-166-measured-dlap`** — read from `frontend/data/backcast/keepers/CAISO.json` |
| `complete` markers | {NEISO, NYISO, PJM} — **CAISO absent**, as the packet states |
| `final` markers | EMPTY |
| holdout spend freeze | **ACTIVE** |
| years touched | **2023–2025 (in-sample) and 2026+ (forecast) ONLY.** No out-of-training year was solved, scored, read or approached. |

Prerequisites ran in the briefed order: `uv sync` first (~2 min), then
`scripts/regenerate_clean.py`.

---

## 2. Resolving B-2 — CAISO's Table 1.1 Hydro row DOES include pumped storage

FFR-3P filed this as the one row it did not stand behind, and it is load-bearing: a
1,962.8 MW reattribution between the two classes a fix lane would work. It resolves
cleanly, from committed data, two independent ways.

**Proof 1 — arithmetic impossibility.** Table 1.1 reports Hydro **Net Dependable
Capacity of 9,076 MW**. EIA-860 (2025 Early Release, BA `CISO`, status `OP`) carries
**6,411.5 MW** of conventional hydro (prime mover `HY`) against **2,077.6 MW** of pumped
storage (`PS`). A conventional-hydro-only NDC of 9,076 MW would be **1.42× the
nameplate** of the fleet it accredits, which is not a quantity NDC can take. `HY` + `PS`
net summer capability is **8,748.7 MW** — within **3.7 %** of the published 9,076 MW,
the expected residual for publicly-owned units EIA-860 tags to a different BA.

**Proof 2 — the resources are in the NQC list and Table 1.1 has no PS row.** CAISO's own
CY2026 NQC list (committed at
`data/raw/capacity-market/nqc/caiso/net-qualifying-capacity-report-cy2026.xlsx`) carries
its pumped-storage fleet explicitly, at **1,962.8 MW of September NQC**:

| resource | Sep NQC |
|---|--:|
| `HELMPG_7_UNIT 1/2/3` — Helms | 407.00 + 407.00 + 404.00 |
| `HYTTHM_2_UNITS` — Hyatt-Thermalito | 545.59 |
| `EASTWD_7_UNIT` — Eastwood | 199.00 |
| `ONLLPP_6_UNITS` — O'Neill | 0.21 |
| `SLUISP_2_UNITS` — San Luis (Gianelli), `DMDVLY_1_UNITS` — Diamond Valley | 0.00 |
| **total** | **1,962.80** |

Those MW are in the published 59,069 MW total. Table 1.1 has no pumped-storage row, so
Hydro is the only line they can sit on.

**The corrected attribution** (the model's own class boundaries — PS is a storage
resource in this model, `constants.py:1369`):

| class | FFR-3P §1.1 said | **corrected** |
|---|--:|--:|
| hydro (conventional) | −1,670.2 | **+292.6** *(model is OVER)* |
| storage (battery + PS) | −5,933.2 | **−7,896.0** |
| every other row | unchanged | unchanged |
| **total** | **−11,711.0** | **−11,711.0** |

FFR-3P's §2.1 conclusion is *strengthened*, not weakened: it said the hydro **rate** is
already 1.1 pp generous and the fleet was the problem. On the corrected boundary the
hydro **fleet** is not short either. **Conventional hydro is not a defect in this ledger
and should be dropped from the queue.** FFR-1C's F-4 controllable/run-of-river split has
even less claim on priority than FFR-3P gave it.

---

## 3. The decomposition — 11,711 MW by cause, with megawatts

Model figures are FFR-3P §1.3's base-year ledger (cache key `e5822277b72184f6`, control-arm
reproduced twice). CAISO figures are Table 1.1 as transcribed by FFR-3P — **the PDF is not
committed and I did not re-extract it**, so those cells carry FFR-3P's transcription risk;
the PS split in §2 is my own measurement from the committed workbook.

**One structural point governs the whole table.** The solar, wind, battery, hybrid and
"other" classes **cannot be differenced class-by-class** against Table 1.1, because
EIA-860 splits a hybrid plant's PV onto the solar schedule and its battery onto the
storage schedule (`load_eia860_storage`'s own docstring says so), while CAISO books
hybrids as their own class. Any class-level split of that block double-counts. So the
block is differenced **merged**, and only the battery *rate* is separated inside it —
battery being the one class that is a single, cleanly-comparable class in both ledgers.

| # | cause | class | MW | share | disposition |
|---|---|---|--:|--:|---|
| **A** | **Base-year battery fleet is a stale hand-rounded scalar** | storage | **−5,121.9** | 43.7 % | **FIXED** §4.1 |
| **B** | **Battery accreditation rate** — model's generic blended 0.6875 vs CAISO's published class ratio 13,365/14,131 = 0.9458 | storage | **−3,990.6** | 34.1 % | **ROUTED** §6.1 — *no mechanism exists* |
| **C** | **Solar/wind accreditation rate + hybrid POI boundary + deliverability truncation** — jointly, NOT separable (see above) | VRE / boundary | **−2,684.1** | 22.9 % | **ROUTED / DOCUMENTED** §6.2, §6.3 |
| **E** | **Base-year solar nameplate** stale (22,000 vs EIA-860 24,919.2) | VRE | −525.6 | 4.5 % | **FIXED** §4.2 |
| **F** | **Base-year wind nameplate** stale — *the model is OVER by 670 MW* | VRE | **+107.2** | −0.9 % | **FIXED** §4.2 *(makes the deficit worse)* |
| **G** | Conventional hydro — model above published | hydro | +292.6 | −2.5 % | no defect §2 |
| **H** | Thermal — model above published | thermal | +242.4 | −2.1 % | no defect (FFR-3P §2.2 stands) |
| **I** | Pumped storage — model marginally under published NQC | storage | −30.6 | 0.3 % | immaterial |
| | **TOTAL** | | **−11,710.6** | 100 % | |

The total closes on FFR-3P's −11,711.0 to **0.4 MW** — rounding in its transcription, not
a missing term. ("Other", 451 MW NDC / 42 MW NQC, is inside the merged block, not a
separate row.)

Causes A + E + F are **fleet coverage** and total **−5,540.3 MW (47.3 %)** — this is what
was fixed. Causes B + C are **accreditation rate and class boundary** and total
**−6,674.7 MW (57.0 %)**. G + H + I net **+504.4 MW** of model surplus.

**The one-sentence answer to the charter's question:** the capacity is missing in **two**
of the four places it named — *units present but under-accredited* (the majority) and *a
vintage/as-of misalignment in how the base year is assembled* (the plurality) — and in
**neither** of the other two: no units are absent from the base fleet once the vintage is
right, and the crosswalk drops no class except a hybrid boundary the model covers by
merged pools.

---

## 4. What was fixed

### 4.1 Cause A — `STORAGE_BASE_FLEET_MW["CAISO"]`, and why this is unambiguous

The registry documents its own construction in prose, and applies it to four ISOs:

> *mid = operable Status="OP" nameplate MW; high = mid + proposed-schedule Status in
> {U, V, TS}; low = mid × 0.75, rounded to the nearest 10 MW* — from the EIA-860 2025
> Early Release energy-storage schedule, plants assigned by BA code through
> `zone_assignment._ISO_TO_BA_CODE`.

Re-running that construction against the committed parquet reproduces those four rows
**exactly**:

| ISO | measured mid | shipped | measured high | shipped |
|---|--:|--:|--:|--:|
| MISO | 801.9 | **800** | 1,435.4 | **1,440** |
| PJM | 497.1 | **500** | 874.2 | **870** |
| NYISO | 252.7 | **250** | 278.3 | **280** |
| NEISO | 765.4 | **770** | 1,280.1 | **1,280** |
| **CAISO** | **15,448.4** | **8,000** ✗ | **19,262.3** | **12,000** ✗ |

CAISO's row was never built that way — its cited source is *"CAISO TPP 2024 — ~8 GW
operational + under construction"*, a hand-rounded figure that is roughly CAISO's **2023**
fleet applied flat to a **2026** base year. This is rule 14 `[R-ACCURATE]` in its plainest
form: a measured source is committed, already trusted for four sibling rows, and
contradicts the estimate by 7,448 MW.

**Independent closure check, from a second document:** CAISO's own published battery Net
Dependable Capacity is **14,131 MW** against the EIA-860 nameplate of 15,448.4 MW — NDC is
**91.5 %** of nameplate, exactly the post-derate relationship NDC should carry.

**Changed to** `low / mid / high = 11,590 / 15,450 / 19,260`. At the model's own shipped
blended duration credit (0.6875 = 0.70×0.60 + 0.25×0.87 + 0.05×1.00 over
`STORAGE_TECH_POWER_SHARE`), that is **+5,121.9 MW of accredited firm capacity**.

**ERCOT is the other hand-entered row** (17,000 shipped vs 13,709.3 by this construction)
and is deliberately **UNTOUCHED** — rule 25 `[R-ISO-SCOPE]`. It is routed in §7, not fixed.

### 4.2 Causes E/F — `RENEWABLE_INSTALLED_MW["CAISO"]`

Same vintage problem, same release, forecast-only blast radius (`data.renewables` reads
this registry only when `mode != "backcast"`; a backcast already takes that year's EIA-860
month-end capacity — §5 is about why storage lacks that path).

The measured object is deliberately **the one the backcast itself resolves** —
`data.renewables._eia860_monthly_capacity(..., 2025)` year-end, i.e. the EIA-860
per-technology *schedules* — not the generators parquet's prime-mover totals. The two
agree exactly on wind and differ by 923 MW on solar (schedule 24,919.2 vs prime-mover PV
23,996.4; the solar schedule carries 1,012 CISO rows to the generator file's 1,005). The
schedule is correct here **because it is what the backcast reads**: a forecast base year
built on a different solar object than the 2025 backcast it follows would step
discontinuously at the seam.

| class | shipped | measured (loader's own object) | adopted | CAISO published NDC |
|---|--:|--:|--:|--:|
| wind | 7,000 | **6,326.3** | **6,330** | **6,330** |
| solar | 22,000 | **24,919.2** | **24,920** | 20,459 + 2,043 hybrid = 22,502 |

The wind closure check is the strongest single number in this document: EIA-860's CISO
wind nameplate and CAISO's own published wind NDC agree to **0.06 %**. That is two
independent instruments landing on the same fleet, and it is what licenses using EIA-860
CISO nameplate as the comparison object for the other classes.

**Note the direction on wind: the accurate value is 674 MW LOWER, i.e. it makes the
deficit worse.** It is adopted anyway. Rule 14 forbids keeping an estimate because it
flatters a residual, and a lane that fixed only the favourable half of a vintage error
would be doing exactly that.

### 4.3 Measured effect of §4.1 + §4.2

Computed from the shipped accreditation chain (`build_default_storage` →
`_elcc_for_duration`, `RENEWABLE_CAPACITY_CREDIT`), no solve required:

```
battery firm   5,500.0 -> 10,621.9   (+5,121.9)
pumped storage 1,932.2 ->  1,932.2   (unchanged)
solar firm     3,960.0 ->  4,485.6   (  +525.6)
wind firm      1,120.0 ->  1,012.8   (  -107.2)
                                     ----------
                                      +5,540.3 MW

accredited firm  50,729 -> 56,269.6
reserve position 0.8852 -> 0.9819     (11.5 % short -> 1.8 % short)
```

**Row 4's position after the fleet is right.** The reserve position rises but stays
**below 1.0**, so the adequacy requirement is still unmet in the base year and the
reserve-margin backstop still has a deficit to size against. The FC-2 row-4 numerator is
reduced, **not collapsed** — the charter's premise that it collapses rested on the
1.0896 figure, which §0 finding 2 corrects. The exact landing cell is not claimed here:
it needs the five-year forecast solve, and §7 D-8 records that as the owed measurement
rather than estimating it.

---

## 5. The wiring defect underneath cause A — an orphaned loader and a dead flag

`STORAGE_BASE_FLEET_MW` is a **forecast** object: its own docstring calls it *"the base
year (2026)"* and its `low/mid/high` are the `storage_deployment` **scenario ladder**. Yet
`runner.py:762` fed it to **every solve year in both modes**, so a 2023 backcast ran on a
2026 constant. That is a vintage/as-of misalignment, not a scenario choice.

The correct object already existed and was **never called by any runner path**.
`model/storage.py::load_eia860_storage` — month-precise COD ramp, real zone assignment,
real per-unit durations, pumped storage appended — documents itself as exactly this fix:

> *"This grounds a calibration backcast in the historical storage fleet rather than the
> forward-looking `STORAGE_BASE_FLEET_MW` scenario constant. … first-order for CAISO,
> which added 3.0 GW mid-2023 and 3.6 GW mid-2024."*

Two consequences, both live before this session:

* **`storage_vintage_ramp` was a DEAD FLAG for batteries.** The CAISO keeper arms it
  (`run_config.json`: `storage_vintage_ramp: true`). With the battery fleet a flat scalar
  there is no COD ramp to apply; the flag was reaching pumped storage only. This is the
  `caiso-98` dead-flag failure mode the codebase already names.
* **The CAISO backcast ran 48 % short of the fleet that operated.** Measured battery fleet
  at year-end: **7,492 / 11,131 / 15,448 MW** for 2023 / 2024 / 2025, against a flat 8,000.
  And `caiso_storage_shape_caps` — armed on the keeper — is a *per-MW-of-EIA-860-fleet*
  rate (`EIA-930 NG:OTH ÷ EIA-860 monthly fleet`) applied to that scalar, so the
  envelope's **denominator and its multiplicand were on different fleets**.

**Fixed** by `ScenarioConfig.storage_measured_base_fleet` (default **True**, registered in
`_CACHE_KEY_OPTIONAL_FIELDS`), scoped by `STORAGE_MEASURED_BASE_FLEET_ISOS = {"CAISO"}`.
A CAISO backcast now resolves its base fleet as of its solve year — precisely the
mode-aware pattern `data.renewables` has always had for wind and solar.

**Verified end-to-end through the keeper's own storage chain** (no solve; `storage_units_to_arrays`
→ `storage_cap_profiles` → `caiso_storage_shape_caps`, at the keeper's `storage_vintage_ramp=True`
and `caiso_storage_shape_anchor=True`):

| year | total MW | battery MW | `power_cap` shape |
|---|--:|--:|---|
| 2023 | 9,570.0 | 7,492.4 | (6, 8760) |
| 2024 | 13,208.9 | 11,131.3 | (6, 8760) |
| 2025 | 17,526.0 | 15,448.4 | (6, 8760) |

Three things this confirms. **The caps are now 2-D** — `storage_vintage_ramp` is genuinely
live for batteries for the first time, which is the dead flag closing. **`_battery_mask`
classifies the measured units correctly** (5 battery + 1 pumped storage; the mask is a
negative test on `tech_name != "pumped_storage"`, so the loader's `li_ion` passes). And
**the shape envelope's basis mismatch closes as a side effect**: `caiso_storage_shape_caps`
multiplies a per-MW-of-EIA-860-fleet rate by `power_cap`, which is now that same EIA-860
fleet rather than a scalar on a different basis.

> **HYPOTHESIS, EXPLICITLY NOT CLAIMED.** The CAISO keeper carries C3a-2025 (mean LMP
> **+14.4 %** hot) as a ledgered caveat whose root cause is recorded as a pumped-storage
> data wall. A 2025 backcast missing **7.4 GW** of evening-peak battery leaves that load
> to thermal, which pushes price up — the right direction and roughly the right place. **No
> solve has tested this and it must not be quoted as measured until one does.** It is
> written here as a lead for the CAISO lane, not as a result.

---

## 6. What remains — after the fleet is right, the residual is accreditation rate and class boundary

Post-fix ledger against CAISO's published internal total of 59,069 MW:

| class | CAISO NQC | model after fix | residual |
|---|--:|--:|--:|
| thermal | 29,979 | 30,221.4 | **+242.4** |
| conventional hydro (Table 1.1 hydro − measured PS) | 4,332.2 | 4,624.8 | **+292.6** |
| pumped storage | 1,962.8 | 1,932.2 | −30.6 |
| **solar + wind + battery + hybrid + other, MERGED** | **22,795.0** | **16,120.3** | **−6,674.7** |
| **total** | **59,069** | **52,898.7** | **−6,170.3** |

The VRE+battery block **must** be compared merged: EIA-860 reports a hybrid plant's PV on
the solar schedule and its battery on the storage schedule (the loader's own docstring
says so), so the model's corrected pools already carry the MW CAISO books in a separate
hybrid class. Comparing class-by-class here would double-count.

**Thermal and conventional hydro now sit ABOVE CAISO's published values and pumped storage
is within 30 MW of it. Every megawatt of the residual is in the one merged block, and it
reduces to a single comparison:**

```
model accredits this block at   16,120.3 / 46,700 nameplate = 0.3452
CAISO's own realized rate is    22,795.0 / 43,414 NDC       = 0.5251
```

### 6.1 Cause B — battery accreditation rate. **No mechanism exists. Largest single item.**

The model credits batteries through the **generic** `STORAGE_ELCC_BY_DURATION` table
(NREL/E3; 4 h → 0.60), blended to **0.6875** over a synthetic 70/25/5 duration mix. CAISO's
published whole-class realized ratio is **13,365 / 14,131 = 0.9458**. On the corrected
15,450 MW fleet the difference is **+3,990.6 MW** — 59.8 % of everything left.

`STORAGE_ELCC_BY_DURATION_BY_ISO` exists and today holds **PJM only**. CAISO has no entry.

**Why this session did not add one**, though it is the single largest remaining term and
FFR-3P's standing methodological warning points straight at it (*prefer the published
whole-class realized ratio*):

* It is a **rate, not a fleet**. The charter is explicit: *"Work the FLEET, not the
  screen"*, and adding an accreditation rate is not fleet work.
* It would move row 4 substantially, and a lane that turns row 4 green by a route its
  charter did not authorize is the same failure the anchor refusal exists to prevent —
  whichever route it is.
* The **objects do not map cleanly**. PJM's registry entry is a published *duration
  table*; CAISO publishes a *realized whole-class ratio* over its real duration mix, while
  the model's 15,450 MW carries a synthetic 70/25/5 mix. Dropping 0.9458 onto that is a
  substitution, not a reconciliation — rule 14's own misalignment clause asks for the
  latter.

**Routed as the top FFR-4D successor item**, with a live caveat: `STORAGE_ELCC_DILUTION_*`
holds **ERCOT only**, so CAISO's portfolio dilution factor is a hard **1.0** — an
assumption that was cheap at 8,000 MW of storage and is not at 15,450 MW.

### 6.2 Cause C — solar/wind accreditation rate. **Mechanism exists, default-off.**

`caiso_nqc_accreditation` (solar 0.2096 / wind 0.2202, closure-checked against Table 1.1
to within 0.3 pp) is built, merged and **default-off**, held by owner decision D.1. On the
**corrected** pools it is worth more than the +1,072.6 MW FFR-3P measured on the old ones.
The gap to CAISO's whole-fleet realized rates (solar 0.3179, wind 0.2213) is **partly a
deliberate, documented conservatism**: FFR-3P §3.3 adopted the min-over-Jul/Aug/Sep value
specifically to offset the deliverability truncation the model has no representation of
(CAISO gives zero NQC to energy-only solar). That reconciliation stands and is not
reopened here.

**Ordering note, corrected.** FFR-3P §3.4 recommended *"B-1 (storage vintage) first, this
second"*. B-1 is now done. **This is now next among the armable items** — but §6.1 is
larger, and neither is chartered.

### 6.3 Cause D — the hybrid boundary. **Documented misalignment, per rule 14.**

CAISO accredits solar+storage hybrids as a distinct class with its own QC construction
(renewable component + storage component, capped at the POI limit): 2,043 MW NDC /
1,484 MW NQC. The model has no hybrid class. This is **not missing capacity** — it is a
class boundary. EIA-860 splits a hybrid across the solar and storage schedules, so the
corrected pools carry those MW; what the model cannot reproduce is the **POI cap** that
makes a hybrid's combined NQC less than the sum of its parts. Rule 14's misalignment
exception applies exactly: the boundary is documented here rather than guessed at, and no
reconciled hybrid class is invented to close a residual. FFR-3P's B-6 is thereby answered
— the MW are **not** absent, and the −1,484 row **is** partly a double-count.

---

## 7. Open items, routed not fixed

| id | item | why not here |
|---|---|---|
| **D-1** | **Battery accreditation rate — CAISO absent from `STORAGE_ELCC_BY_DURATION_BY_ISO` while CAISO publishes 13,365/14,131 = 0.9458.** +3,990.6 MW, the largest remaining term. | §6.1: a rate not a fleet; objects don't map one-for-one; and it would move row 4 by an unchartered route. |
| **D-2** | **THE CAISO KEEPER `2026-08-04-caiso-166-measured-dlap` IS PRE-EPOCH AND OWES A RE-SOLVE + RE-GATE.** Its metrics were produced on the flat 8,000 MW scalar. Cache epoch 2026-08-04c records it. | A keeper re-solve is a 3-year run plus a full re-gate under rules 15/16 — its own session in the CAISO lane. **Stated as owed, not done.** |
| **D-3** | **ERCOT's storage row is the other hand-entered entry** (17,000 shipped vs 13,709.3 by the registry's own EIA-860 construction). | Rule 25 `[R-ISO-SCOPE]`. ERCOT's cited source (ERCOT Monthly Dec 2025) is a *later* vintage than EIA-860 2025 ER, so this may be a legitimate misalignment rather than a defect — it needs ERCOT's lane to judge, not mine. |
| **D-4** | **CAISO's storage ELCC portfolio dilution is a hard 1.0** (`STORAGE_ELCC_DILUTION_*` hold ERCOT only) — a much larger assumption at 15,450 MW than at 8,000. | New registry entry for another ISO; belongs with D-1. |
| **D-5** | **The other five ISOs still take a forecast scalar for their backcast storage fleet.** Immaterial for PJM/MISO/NYISO/NEISO (their rows were derived from EIA-860 and sit within a few MW), material only for ERCOT. | Enrolling an ISO in `STORAGE_MEASURED_BASE_FLEET_ISOS` moves that ISO's keeper; each needs its own lane. |
| **D-6** | **`check_cache_key_registration.py` check 1 was RED on `main`** before this branch (`ercot_storage_rt_offer_surface` registered with no declared default). Backfilled here as a zero-behaviour bookkeeping entry so this PR's CI is readable. | Pre-existing; fixed only because it blocks a guard, not as scope. |
| **D-7** | Table 1.1's cells are carried from **FFR-3P's transcription**; the source PDF is not committed. The PS split in §2 is my own measurement from the committed workbook, but the class totals are not independently re-extracted. | An intake, with its own authorization. Flagged so nobody reads §3 as fully first-party. |
| **D-8** | **The five-year CAISO forecast solve that would place FC-2 row 4 exactly was NOT completed in this session.** §4.3's +5,540.3 MW and the 0.9819 reserve position are exact arithmetic over the shipped accreditation chain, but the row-4 *cell* (PASS / CAVEAT / FAIL) additionally depends on how the backstop and the economic entry screen split the reduced deficit across 2026-2030. | Container time. The direction is unambiguous and is stated (§4.3): the numerator falls, the position stays below 1.0, so the need does not vanish. **The cell itself is not claimed.** `scripts/run_full_horizon.py --iso CAISO --start-year 2026 --end-year 2030 --golden-posture` against a stashed-constants control is the exact measurement owed. |

---

## 8. Governance

* **The refusal that is the point of this charter — honoured, formally.** No CAISO
  capacity-price anchor, CPM soft-offer cap, net-CONE value or entry-screen term was read,
  changed, or quoted. **No row-4 improvement obtained by that route is claimed anywhere**,
  and §0 finding 2 reports row 4 *not* clearing rather than reaching for the route that
  would clear it. `data/raw/capacity-market/demand-curve/caiso/caiso.csv` was not opened.
* **Rule 1 `[R-STRUCT]` / rule 11.** Nothing is tuned to a residual. The wind correction
  (§4.2) makes the deficit **worse** and is adopted; the two largest remaining terms are
  **routed rather than armed**, precisely because arming them would move row 4 by a route
  this charter did not authorize.
* **Rule 13 `[R-MEASURED]`.** Every value is a physical asset registry (EIA-860 nameplate)
  or a published accreditation, entering as a formulaic input that regenerates for a
  forward year. No measured *outcome* is fed back.
* **Rule 14 `[R-ACCURATE]`.** Two estimates replaced by the measured source already
  trusted for four sibling rows; one of the two is adverse to the residual. The hybrid
  boundary (§6.3) and the CAISO-vs-PJM storage-rate object mismatch (§6.1) are the
  documented-misalignment exception, stated rather than buried.
* **Rule 19 `[R-ONE-MECH]`.** Nothing is stacked. `storage_measured_base_fleet` **replaces**
  the scalar on the path it governs; it does not sit beside it.
* **Rule 22 `[R-HOLDOUT]`.** In-sample 2023–2025 and forecast-mode 2026+ only. No
  out-of-training year was solved, scored, read or approached. CAISO holds no marker and
  the freeze is ACTIVE; both are respected. No marker was written.
* **Rule 23 `[R-FROZEN-DERIVE]`.** The re-derivation licence is the **source-data vintage**
  (EIA-860 2025 Early Release, already on disk and already cited by four rows), never a
  residual. `tests/unit/model/test_storage.py::test_caiso_base_fleet_matches_eia860_construction`
  re-runs the construction against the committed parquet, so the row cannot drift from its
  source silently.
* **Rule 24 `[R-REGISTRY]`.** The new field is a `ScenarioConfig` field and lands in
  `run_config.json`. No env var, no per-plant dict, no `getattr` fallback literal.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. Both registry edits are CAISO rows; the new
  field resolves through a frozenset containing CAISO alone, pinned by a test whose whole
  purpose is to make enrolling another ISO deliberate. ERCOT's parallel defect is routed,
  not fixed. No MISO/PJM parameter or verdict was imported.
* **Rule 27 `[R-PUSH]`.** Opus. No file ≥300 lines was rewritten from generated content;
  every change is a local `Edit` of on-disk bytes.
* **Rule 28 `[R-MECH-MATRIX]`.** Row `storage_measured_base_fleet` minted in the same
  commit as its field (duty c), CAISO cell **O** — built and armed but **not yet
  adjudicated by a solve**, since only a CAISO *backcast* can adjudicate a backcast-scoped
  field and this was a forecast-lane charter. Entered as O rather than K deliberately, so
  the default-ON arming is not misread as a tested verdict.
* **Cache.** Same-key invalidation, epoch **2026-08-04c** in `results/cache.py`. The pinned
  default key `603c2498bf71d21d` is **unmoved** (measured). Invalidates every cached CAISO
  bundle in both modes — including the designated keeper (D-2). No other ISO is touched.
* **Rules 15/16.** No calibration run was produced, so there is nothing to register on
  either dashboard. The forecast measurement in §4.3 is arithmetic over the shipped
  accreditation chain, not a solve.

---

## 9. Reproduction

```bash
uv sync                                    # ~2 min
uv run python scripts/regenerate_clean.py  # ~63 min

# the decomposition, entirely solve-free
uv run python -m pytest tests/unit/model/test_storage.py -q

# cause A: the registry's own EIA-860 construction, all six ISOs
uv run python - <<'PY'
import pandas as pd
plant = pd.read_parquet('data/raw/eia-860/eia860_plant.parquet')
ba = plant.set_index('Plant Code')['Balancing Authority Code']
op = pd.read_parquet('data/raw/eia-860/eia860_energy_storage_operable.parquet')
pr = pd.read_parquet('data/raw/eia-860/eia860_energy_storage_proposed.parquet')
for iso, code in {"ERCOT":"ERCO","CAISO":"CISO","MISO":"MISO","PJM":"PJM","NYISO":"NYIS","NEISO":"ISNE"}.items():
    m = op[(op['Plant Code'].map(ba)==code) & (op['Status']=='OP')]['Nameplate Capacity (MW)'].sum()
    p = pr[(pr['Plant Code'].map(ba)==code) & (pr['Status'].isin(['U','V','TS']))]['Nameplate Capacity (MW)'].sum()
    print(f'{iso:6s} mid={m:10,.1f}  high={m+p:10,.1f}')
PY

# cause B/§2: CAISO pumped storage in the published NQC list
uv run python -c "
import pandas as pd
d = pd.read_excel('data/raw/capacity-market/nqc/caiso/net-qualifying-capacity-report-cy2026.xlsx','2026 NQC List')
n = (d['Generator Name'].astype(str)+' '+d['Resource ID'].astype(str)).str.upper()
ps = n.str.contains('HELM|EASTWD|EASTWOOD|HYATT|THERMALITO|ONEILL|GIANELLI|DIAMOND VALLEY')
print(d.loc[ps,['Resource ID','Generator Name','SEP']].to_string())
print('PS Sep NQC total:', pd.to_numeric(d.loc[ps,'SEP'],errors='coerce').sum())
"

# §4.3: the measured ledger delta, no solve
uv run python -c "
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.storage import build_default_storage, _elcc_for_duration, load_eia860_pumped_storage
cfg = ScenarioConfig(iso='CAISO', mode='forecast'); iso = get_iso_config('CAISO')
f = lambda us: sum(u.power_cap_mw*_elcc_for_duration(u.energy_cap_mwh/u.power_cap_mw,'CAISO') for u in us)
print('battery firm', f(build_default_storage(iso,cfg)), 'PS firm', f(load_eia860_pumped_storage('CAISO',2026,cfg)))
"
```
