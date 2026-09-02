# FINDING — capx D32: the floor-retention selection rule — post-repair the floor decides 100 % of MISO's exit composition, its cross-fuel key has no per-unit identification, its within-fuel tie-break never fires (a float-noise defect), and its selection is indistinguishable from random against the real cohort; the one published per-unit driver that does discriminate is the owner's filed retirement date, which the fossil channel deliberately ignores

**Lane:** capx D32 — Phase-0 characterization of D27 R5 (the floor-retention key's
exit-composition monopoly), sequenced after D31 as directed.
**Scope honoured:** ZERO solves (the only model code executed was the fleet
LOADER, `build_base_fleet`, to read each unit's retention key — no LP, no
screen, no evolution); docs only; no mechanism, no `ScenarioConfig` field, no
matrix cell, no keeper/board/verdict/marker. No repair lands here.
**Data:** D31's committed bundle `results/hindcast/miso-2021-2025-realized-t1h-d31`
(cache key `3649264ca98a1fb4`, the enriched `pipeline_events` per year) + the
committed scoring target `capacity_actuals_miso.csv` + the EIA-860
`vintage_2020` spine + the confirmed-retirements registry. Every number below
is reproducible from those files; the two scratch probes are described in §9.
**Rule 21 `[R-DOF]`, the charter's wall:** nothing here proposes a weight, a
threshold, or any parameter identified against the −74.3 % residual. The
residual is used only to say WHERE the error lives.

---

## 0. Verdict (one paragraph)

**The selection rule is not a defensible model of which units exit, and it
cannot be repaired by re-ranking.** After D31's repair the reliability floor
binds at every screen year but only at the ADMISSION stage (the execution-year
floor never fires), and it binds against a screen that fails **77 % of the
fossil fleet at the 2022 bridge screen and 92.5 % by 2024** — so the floor is
no longer a backstop, it is the exit model: it decides 100 % of the
composition of a 3.7 GW release out of a 100 GW failing pool. Measured against
the real 2021–2025 cohort at plant grain, its choice is **no better than
random**: 13.5 % of the MW it released sits at plants that actually exited,
against a 14.1 % real exit rate among the MW it retained; it retained
**13.6 GW (78 %) of the real cohort** as failing-but-kept, including every one
of the 15 large real coal exits it had in its fleet except Petersburg. The
cross-fuel key (`FOM × multiplier / (1 − EFORd)`, a class constant) has **no
published per-unit identification** — it is an ATB class assumption ranking
fuel *classes*, and it asserts a composition (coal-only while the floor binds)
that the real cohort refutes (gas-steam 12.2 %, oil 10.8 %, coal 20.8 % of
fleet exited). Its within-fuel tie-break (CO2 then heat rate, the plan §3.2
design) **never fires as designed**: the first key is computed per unit as a
quotient that lands on 3–5 distinct floats per fuel at the 1e-11 level, and
`sorted()` orders on that rounding noise before it ever consults CO2 — the
2022 decided set is exactly the suffix of the key-1-only order, and the three
highest-CO2 coal plants in the fleet were retained (§3.2). The honest dead
end on the charter's own question: **no published per-unit driver identifies
an ISO-selected cross-fuel retention preference in MISO 2021–2025, because the
phenomenon the floor models — the ISO holding units back at scale — did not
occur** (the SSR channel fired zero times in-window; the one retention
instrument that did fire, DOE §202(c) on Campbell, retained *coal*, the
opposite of the rule). What DOES discriminate, per unit, published, and
forward-regenerable, is the owner's **EIA-860 Schedule-3 planned retirement
date**: filed by the 2020 vintage for **69 % of the real cohort's MW** (coal
78 %, gas-steam 50 %, oil 54 %, nuclear 100 %), 87 % of dated MW exiting
within ±1 year of the filed date — and the fossil channel ignores it by
design (`forecast_fossil_retirement_economic=True`). Routed (§7): an owner
posture decision on that channel is the PRIMARY; the float-noise key is a
code-correctness repair (not a tuning); a sector gate is the structural
companion; the retention key itself is NOT to be re-weighted.

---

## 1. The post-repair binding census (2021–2025), from D31's ledgers

Where and when `_apply_reliability_floor` bound on the D31 run. The pipeline
rule calls it twice per screen year: at ADMISSION (`new_units` un-admitted
until the scheduled-exit counterfactual clears the requirement at the
`_admission_cap_horizon`) and at EXECUTION (`due` units retained until the
realized fleet clears it). Both calls select by `_floor_retention_merit`.

| screen year | fossil fleet before (MW) | fails the bar (MW) | share failing | admission floor: retained (`entry_capped`) | released (`decided`) | execution floor (`floor_retained`) |
|---|---:|---:|---:|---:|---:|---|
| 2022 (bridge) | 129,825.5 | 99,998.9 | **77.0 %** | 96,314.9 (1,640 units) | **3,684.0 — 23 coal tranches** | — (nothing due) |
| 2023 | 130,971.5 | 96,436.6 | 73.6 % | 92,752.6 (1,080) | 0 (23 coal `re_confirmed`) | — |
| 2024 | 130,971.5 | 121,182.8 | **92.5 %** | 117,498.8 (1,190) | 0 (`re_confirmed`; 3,684.0 `executed`) | **[] — none retained** |
| 2025 | 127,287.5 | 0 | 0 % | — | — | — |

Three facts the census settles:

1. **The floor binds at every screen year 2022–2024, and only at admission.**
   `floor_retained` is empty in every year: the 23 coal tranches admitted in
   2022 executed in 2024 unopposed. Every retention decision in this run is an
   admission-cap decision.
2. **The bar fails essentially the whole non-coal fleet, every year.** 2022:
   100 % of gas_ct (24,385 MW, 517 units), 100 % of gas_st (13,942, 244), 100 %
   of oil (3,517, 562), 84 % of gas_cc, 56 % of coal. gas_ct / gas_st / oil
   units carry **net revenue exactly $0** (median; they never run under the
   LP) so their "depth" is their entire FOM. By 2024 **every coal unit in the
   fleet** (261 tranches, 51,880 MW) fails too. Absent the floor, the screen
   would exit ≈100 GW against a 17.4 GW reality — the floor is the only thing
   standing between the model and a 6× over-exit, which is why its selection
   rule IS the composition.
3. **Composition at the boundary is set by the class constant.** With
   `retirement_fom_multiplier_coal=1.3` and class EFORd, the key is a
   per-class constant ($/firm-MW-yr): gas_ct 22,340 < oil 27,778 < gas_cc
   31,579 < gas_st 37,634 < **coal 63,587** (the probe's reconstruction on
   D31's config; §9). Retention walks that ladder from the cheap end, so coal
   is the last fuel retained and — until the requirement clears — the only
   fuel released. D27 §4 stated this; the D31 ledgers confirm it holds with
   the corrected requirement basis: 2023's oil column (10 units, 328 MW) is
   the only non-coal entry that ever thins, and only because 552 oil units
   cleared the bar that year on a rare positive energy margin.

The release size is the only thing D31's repair moved (25,646.6 → 3,684.0 MW,
100 % coal both times, exactly D31 P2). What this lane adds is the SELECTION
grain: which 3,684 MW, and what that choice looks like against reality.

---

## 2. Unit-level retained vs released vs the real cohort

### 2.1 The real cohort (the committed scoring target, thermal, 2021–2025)

249 unit rows, 17,369 MW: coal 48 / 12,434 MW; gas_st 26 / 2,128; gas_cc 14 /
858; nuclear 1 / 812; oil 103 / 543; gas_ct 18 / 399; biomass 39 / 196. Nineteen
units ≥300 MW (15 coal, 3 gas_st, 1 nuclear). The "158-unit small tail" D27 R5
named is 183 units under 50 MW, 1,120 MW, median age 34 years, 54 % utility-
owned, 29 % with a filed date — municipal / co-op / industrial oil ICs and
small CTs (Hannibal BPW, Barron, Freeburg, Waterloo, Elk River; DTE's 12 Delray-
class peakers) exiting on age, not margin.

### 2.2 The real cohort's plants against the model's own screen-and-floor status

Every real-cohort (plant, fuel) with ≥50 MW of real exit, joined to the model's
2022–2024 event rows (`RELEASED` = any tranche decided/executed; `RETAINED` =
tranches fail the bar in ≥1 screen and the floor keeps them all; `CLEARS` = in
the fleet, never a candidate; `ABSENT` = not in the model's fleet basis).
`pry2020` = planned retirement year(s) filed in the EIA-860 2020 vintage.

| plant | name | fuel | real exit MW | exit yr | pry2020 | sector | model fleet MW | RELEASED | RETAINED | model status |
|---|---|---|---:|---|---|---|---:|---:|---:|---|
| 6155 | Rush Island | coal | 1,242.0 | 2024 | 2039 | util | 1,244.0 | 0 | 1,244.0 | RETAINED |
| 1743 | St Clair | coal | 1,209.6 | 2022 | 2022 | util | 1,065.0 | 0 | 1,065.0 | RETAINED |
| 6085 | R M Schahfer | coal | 1,096.4 | 2021 | 2021 | util | 1,625.0 | 0 | 1,625.0 | RETAINED |
| 1715 | Palisades | nuclear | 811.8 | 2022 | 2022 | IPP | — | — | — | ABSENT (exited via the announced channel, 2022) |
| 994 | AES Petersburg | coal | 804.9 | 2021/23 | 2021/23 | util | 1,701.5 | **362.4** | 1,339.1 | partly RELEASED |
| 6090 | Sherburne County | coal | 765.3 | 2023 | 2022 | util | 2,238.0 | 0 | 2,238.0 | RETAINED |
| 51 | Dolet Hills | coal | 720.7 | 2021 | 2022 | util | 634.8 | 0 | 634.8 | RETAINED |
| 6055 | Big Cajun 2 | coal | 657.9 | 2025 | — | IPP | 1,110.0 | 22.2 | 1,087.8 | partly RELEASED (a 22 MW peak tranche) |
| 2104 | Meramec | coal | 648.0 | 2022 | 2022 | util | 580.0 | 0 | 580.0 | RETAINED |
| 856 | E D Edwards | coal | 644.3 | 2022 | 2022 | IPP | 560.0 | 0 | 560.0 | RETAINED |
| 4041 | South Oak Creek | coal | 598.4 | 2024 | — | util | 1,112.0 | 0 | 1,112.0 | RETAINED |
| 2050 | Baxter Wilson | gas_st | 544.6 | 2023 | 2023 | util | 494.3 | 0 | 494.3 | RETAINED |
| 1702 | Dan E Karn | coal | 544.0 | 2023 | 2023 | util | 486.0 | 0 | 486.0 | RETAINED |
| 1745 | Trenton Channel | coal | 535.5 | 2022 | 2022 | util | 495.0 | 0 | 495.0 | RETAINED |
| 6137 | A B Brown | coal | 530.4 | 2023 | 2023 | util | 490.0 | 0 | 490.0 | RETAINED |
| 52006 | LaO Energy Systems | gas_cc | 464.5 | 2023/24 | — | ind. | 768.0 | 0 | 384.0 | RETAINED (half clears) |
| 8056 | Waterford 1&2 | gas_st | 445.5 | 2024 | — | util | 831.9 | 0 | 831.9 | RETAINED |
| 1740 | River Rouge | coal | 358.1 | 2021 | 2021 | util | 272.0 | 0 | 272.0 | RETAINED |
| 1400 | Teche | gas_st | 348.5 | 2024 | — | util | 331.4 | 0 | 331.4 | RETAINED |
| 4143 | Genoa | coal | 345.6 | 2021 | 2021 | co-op | 307.5 | 6.2 | 301.4 | partly RELEASED (a 6 MW peak tranche) |
| 862 | Grand Tower | gas_cc | 336.8 | 2021 | — | IPP | 264.0 | 0 | 264.0 | RETAINED |
| 1008 | R Gallagher | coal | 300.0 | 2021 | 2021 | util | 280.0 | 0 | 280.0 | RETAINED |
| 2104 | Meramec | gas_st | 275.0 | 2022 | 2022 | util | 242.0 | 0 | 242.0 | RETAINED |
| 1047 | Lansing | coal | 274.5 | 2023 | 2022 | util | 241.4 | 4.8 | 236.6 | partly RELEASED (a 5 MW peak tranche) |
| 8027 | Blue Lake | oil | 226.8 | 2025 | 2023 | util | 153.0 | 0 | 153.0 | RETAINED |
| 963 | Dallman | coal | 207.3 | 2022 | 2023 | util | 355.0 | 0 | 355.0 | RETAINED |
| 4014 | Wheaton | gas_ct | 194.0 | 2025 | 2025 | util | 186.0 | 0 | 186.0 | RETAINED |
| 10075 | Taconite Harbor | coal | 168.0 | 2023 | 2022 | util | 154.9 | 0 | 0 | CLEARS bar |
| 6705 | Warrick | coal | 166.6 | 2025 | — | IPP-CHP | 721.5 | 0 | 721.5 | RETAINED |
| 1832 | Erickson | coal | 154.7 | 2022 | 2025 | util | 154.5 | 74.2 | 80.3 | partly RELEASED |
| 1081 | Riverside | gas_st | 136.0 | 2021 | 2021 | util | 116.5 | 0 | 116.5 | RETAINED |
| 1943 | Hoot Lake | coal | 129.4 | 2021 | 2021 | util | 138.0 | 6.9 | 131.1 | partly RELEASED |
| 2790 | R M Heskett | coal | 115.0 | 2022 | 2022 | util | 104.3 | 0 | 104.3 | RETAINED |
| (13 more rows 50–82 MW, all RETAINED or ABSENT — full table in the probe output, §9) | | | | | | | | | | |

**Summary of the real cohort by model status (real exit MW):**

| model status | plants | real exit MW | share |
|---|---:|---:|---:|
| **RETAINED — fails the bar, the floor keeps it** | 68 | **13,579** | **78.2 %** |
| partly / fully RELEASED | 9 | 2,421 | 13.9 % |
| ABSENT from the model fleet (biomass, small oil, Palisades) | 43 | 1,099 | 6.3 % |
| CLEARS the bar (never a candidate) | 7 | 270 | 1.6 % |

Per fuel, of the real cohort the model could see: coal 9,821 of 12,434 MW
retained-by-floor; gas_st 2,048 of 2,128; gas_cc 858 of 858; oil 463 of 543;
gas_ct 389 of 399. **The bar is not what loses the cohort — the screen flags
78 % of it as failing. The floor's selection is what loses it.**

### 2.3 What the floor released, against reality

The 20 plants carrying the 23 decided tranches (2022 decided, 2024 executed):

| plant | name | fuel | model released MW | real exit 2021–25? | real MW | pry2020 |
|---|---|---|---:|---|---:|---|
| 6009 | White Bluff | coal | 990.8 | **no** | — | — |
| 6641 | Independence | coal | 633.9 | **no** | — | — |
| 994 | AES Petersburg | coal | 362.4 | yes | 804.9 | 2021/2023 |
| 8023 | Columbia (WI) | coal | 342.7 | **no** (dates moved 2023/24 → later) | — | 2023/2024 |
| 997 | Michigan City | coal | 288.5 | **no** | — | — |
| 6213 | Merom | coal | 235.9 | **no** (sold, kept running) | — | 2023 |
| 4050 | Edgewater | coal | 199.2 | **no** (date moved) | — | 2022 |
| 6823 | D B Wilson | coal | 178.9 | **no** | — | — |
| 1393 | R S Nelson | coal | 170.3 | **no** | — | — |
| 4271 | John P Madgett | coal | 123.2 | **no** | — | — |
| 1832 | Erickson | coal | 74.2 | yes | 154.7 | 2025 |
| 6055 | Big Cajun 2 | coal | 22.2 | yes (peak tranche only) | 657.9 | — |
| 1073 | Prairie Creek | coal | 14.3 | yes | 14.6 | — |
| 2823 | Milton R Young | coal | 13.7 | **no** | — | — |
| 6190 | Brame | coal | 9.9 | **no** | — | — |
| 1943 / 4143 / 1047 / 1167 / 10234 | Hoot Lake / Genoa / Lansing / Muscatine / Biron | coal | 6.9 / 6.2 / 4.8 / 4.5 / 1.8 | yes (peak or committed slivers) | 129 / 346 / 275 / 18 / 22 | var. |

**Plant-grain precision of the release: 497 MW of 3,684 (13.5 %) sits at
plants that actually exited.** The real exit rate among the MW the floor
RETAINED is 13,579 / 96,315 = **14.1 %**. The selection is therefore
indistinguishable from random with respect to the real cohort, and the two
largest releases (White Bluff, Independence — Entergy Arkansas, no filed
date in the 2020 vintage, both still operating) are false at plant grain.

**A scorer note, non-gated (route, do not act here):** `retire.false_retire`
reads **0.0 GW PASS** on this run because its grain is per-fuel EXCESS (G-31) —
3.7 GW of model coal against 12.4 GW of real coal can never be "false" at that
grain, whichever plants it lands on. The per-fuel grain was the right fix for
the tranche-vs-unit artifact; it is blind to the selection question this lane
is about. A plant-grain precision diagnostic (released MW at real-exit plants ÷
released MW) would have read 13.5 % here and 100 % for a perfect selector; it
is reportable from the committed ledgers + target with no re-solve.

---

## 3. The rule as implemented — two findings on source, one new

### 3.1 The cross-fuel key is a class constant with no per-unit content

`_floor_retention_merit` (retirements.py:1284) returns
`(FOM_f × mult_f × pmax × 1000 / (pmax × (1 − EFORd_f)), co2_rate, heat_rate)`.
`FOM_f` is the ScenarioConfig per-fuel FOM (ATB 2024 class values: 21 / 25 /
30 / 35 / 45 $/kW-yr), `mult_f` the per-fuel multiplier (coal 1.3, others 1.0),
`EFORd_f` the NERC-GADS class EFORd (`constants.EFORD`; coal 0.08). Every
factor is a **class** attribute, so key 1 is mathematically identical for every
unit of a fuel and differs only across fuels. The docstring's "all three keys
are physical unit attributes" is true of keys 2–3 and not of key 1. The
plan's own §3.2 design intent was a tie-BREAK between fuels ("the CO2 key
breaks the coal-vs-gas ties the heat-rate key currently gets backwards"),
i.e. it anticipated cross-fuel ties that, at the shipped FOM table, never
occur: the cross-fuel order is fixed by the FOM table alone, and the CO2 key
can only ever order units within a fuel.

### 3.2 The within-fuel tie-break never fires as designed — a float-noise defect (NEW)

Because key 1 is computed per unit as `(FOM × pmax × 1000) / (pmax × (1 −
EFORd))` rather than as the constant `FOM × 1000 / (1 − EFORd)`, IEEE-754
rounding puts different units of the same fuel on **different floats at the
1e-11 level**. On D31's fleet the 110 failing coal units land on 4–5 distinct
values of "63,586.9565…": `…912`, `…913`, `…9135`, `…914`. Python's tuple sort
orders on key 1 first, so the CO2 and heat-rate keys are consulted only among
units that happen to share a rounding bucket. Evidence, all from the committed
2022 events + the probe's reconstruction (§9):

* Sorting the 110 failing coal units by key 1 ALONE puts the 19 matched
  decided units at ranks **91–110 — exactly the suffix** (a pure-CO2 order
  would put them at 92–110 too, but not the same units).
* Inside the `…9135` bucket the CO2 key did its job — the released tail runs
  co2 0.990 → 1.230 t/MWh, the retained head 0.895 → 0.997 (Monroe, Campbell,
  Clay Boswell, Sioux, South Oak Creek, Gibson). But the `…912` / `…913` buckets sort BEFORE that bucket,
  so **Marion (plant 976, 1.533 t/MWh, the dirtiest coal in the fleet),
  Culley (1.186) and Prairie Creek's econ/committed tranches (1.230) were
  RETAINED** ahead of cleaner units in the later bucket; and Michigan City
  (1.046) sits alone in the `…914` bucket at rank 110, released last-in-order
  regardless of CO2. The intended "retain the cleaner unit" ordering is
  reproduced only piecewise.
* The unit test that guards the tie-break
  (`test_capacity.py::test_retention_merit_cost_then_co2`) uses two units of
  **equal pmax (1000.0)**, so the quotient is bit-identical and the defect is
  invisible to it. A test with heterogeneous pmax would fail today.
* Isolated reproduction: `58.5e3 * p / (p * 0.92)` over eight of the run's
  actual coal pmax values yields three distinct floats.

This is a **correctness defect, not a tuning question**: the fix is to compute
key 1 as the class constant (or round it), which changes no parameter and
introduces no DOF. Its composition consequence is **nil at the cross-fuel
level** (coal stays the released fuel) and **real within coal**: with the key
fixed, the 2022 release would have been the highest-CO2 coal tranches
(976, 1073, 1012, 6098, 4271, 963, …) — which, against the real cohort, is
neither better nor worse (§4.3: CO2 rate does not discriminate real exits).
Routed to the repair lane (§7 R2).

### 3.3 What the rule asserts, stated plainly

When adequacy binds, the model asserts: *the ISO procures the cheapest firm
capacity per MW and the expensive-FOM units exit; ties go to the cleaner,
then the more efficient unit.* As PROCUREMENT that is coherent — it is how a
capacity auction clears a supply stack. As a model of **which owners file to
exit**, it makes three claims the record can test: (a) the exiting fuel is the
class with the highest going-forward cost per firm MW (coal, always, at the
shipped table); (b) within that fuel, the dirtiest units go first; (c) the
ISO's adequacy need is what stops the rest. §4 tests each.

---

## 4. Adjudication of the rule against the real MISO process

### 4.1 What a real ISO's process actually holds back — and whether it fired 2021–2025

| retention channel | who decides | what it holds back | published per-unit record | rule-13 (forward-regenerable) | fired in MISO 2021–2025? |
|---|---|---|---|---|---|
| **Attachment Y study → SSR (System Support Resource) agreement** — MISO's RMR analogue | MISO (reliability study), FERC-filed cost-of-service agreement | the specific unit whose exit creates a transmission-security violation, until a transmission fix | YES — SSR agreements are FERC filings (public, named units, term); the approved-retirements/suspensions posting is public but **blocked from this environment** (registry README, three passes) | as an INSTRUMENT set, yes (it is what the confirmed-registry's `rmr_end` class carries); as a *predictor* of which unit, no — it is location-specific and study-driven, not FOM-driven | **No SSR designation in the window is known to this lane.** MISO's SSR era was 2012–2016 (Presque Isle, Escanaba, White Pine, Eckert); the registry README records MISO consuming Attachment Y approvals in its LOLE/MTEP reports without publishing the unit list. Unverified pending the manual download. |
| **DOE FPA §202(c) emergency orders** | federal | the named unit, 90 days at a time | YES — DOE order log (public); already in the registry as `superseded=true` rows | yes as an instrument; not predictable | **Yes, once: J H Campbell 1–3 (1,560.8 MW coal), May 2025 → ongoing.** Schahfer 17/18 + Culley 2 (950.7 MW) from Dec 2025, outside the window. **Every in-window retention held back COAL** — the exact opposite of the rule's release order. |
| **Attachment Y suspension (vs retirement)** | owner elects, MISO studies | reversible mothball up to 36 months | EIA-860 `Status` SB/OS per unit (public, annual) — an outcome record, not the election | as a mechanism, only with an option-value model (DOF); as a data input, the vintage status is admissible | 20 % of surviving oil MW and 3 % of gas_cc MW were already SB/OS in the 2020 vintage — units that earn $0 and "fail" in the model exist in reality as mothballed, not exited |
| **Location / deliverability (LRZ LRR/LCR)** | MISO PRA zonal constraints | zonal position, not a unit | YES (in-repo crosswalk; `capacity_deliverability_limits`, MISO cell `.` backcast / `U` forecast) | yes | Zonal RA never selected a unit to stay in-window; and with 77–92 % of the fleet failing, a zonal exemption cannot change composition |
| **State IRP / securitization / PUC order** | state commission + regulated utility | the utility's entire retirement schedule (dates per unit) | YES when ordered (registry `regulatory_order`: Monroe, Campbell) — but IRPs are plan-level, mostly *acknowledged* not ordered (Indiana), so the per-unit date reaches the public record through **EIA-860 Schedule 3** | the filed date regenerates annually and responds to conditions (it is what moved for Baldwin, Sherco 1, Schahfer 17/18) | **This is the channel that produced the cohort** — see §4.3 |

Conclusion on (c): the model's premise that ISO adequacy need is what stops
units from exiting is not what happened. MISO's offered position stayed
1.03–1.05 through the window (D31 §2) *while* 17.4 GW exited, because entry
replaced it; the ISO retained nothing through its own instrument, and the
only retention that did fire (federal, 2025) retained coal.

### 4.2 Claim (a) — is exit composition FOM-rank-ordered? No.

Real 2021–2025 exit as a share of each fuel's 2020-vintage MISO fleet
(EIA-860 spine, BA = MISO, nameplate):

| fuel | fleet MW | exited MW | exit share | model rule predicts while the floor binds |
|---|---:|---:|---:|---|
| coal | 59,717 | 12,446 | **20.8 %** | all of the release |
| gas_st | 17,467 | 2,134 | **12.2 %** | 0 |
| oil | 5,030 | 543 | 10.8 % | 0 |
| biomass | 2,487 | 196 | 7.9 % | (not screened) |
| nuclear | 13,081 | 812 | 6.2 % | announced channel (correct) |
| gas_cc | 13,621 | 465 | 3.4 % | 0 |
| gas_ct | 50,963 | 788 | 1.5 % | 0 |

Coal IS the largest exiting class, so the rule's first pick is right in
direction — but gas_st and oil exit at 12 % and 11 % of fleet while the rule
holds them at exactly 0 % as long as the floor binds, and the floor binds
every year. The rule is not "mostly right with a residual"; it is a
deterministic zero for four classes whose real exits sum to 3.93 GW.

### 4.3 Claims (b)–(c) — which published per-unit attributes DO discriminate exits?

Measured on the same spine (2,658 MISO thermal units, 248 matched exits),
univariate, no fitting — the rank AUC of each published attribute for
"exited vs survived", by fuel (0.5 = no information):

| attribute (published, per unit, EIA-860) | coal | gas_cc | gas_ct | gas_st | oil | biomass |
|---|---:|---:|---:|---:|---:|---:|
| age (older exits) | **0.77** | **0.94** | 0.70 | **0.50** | 0.63 | 0.49 |
| size (smaller exits) | 0.60 | 0.78 | 0.64 | 0.50 | 0.58 | 0.55 |
| **filed planned-retirement date ≤2025 in the 2020 vintage** — MW recall / precision | **0.78 / 0.52** | 0.05 / 1.00 | 0.25 / 0.34 | **0.50 / 0.45** | **0.54 / 0.64** | 0 / 0 |
| owner sector = regulated utility (share of exited MW) | 0.88 | 0.09 | 0.46 | 0.90 | 0.92 | 0.02 |

Readings:

* **The filed date is the strongest single discriminator by a wide margin**:
  12,070 of 17,385 cohort MW (69 %) carried a ≤2025 date in the 2020 vintage;
  of dated cohort MW, 87 % exited within ±1 year of the filed year (9,391 MW
  exactly on the year). Its false positives (34 units, 10,813 MW) are almost
  entirely **deferrals, sales and federal retention** — Campbell (202(c)),
  Sherco 1 (moved to 2026), Baldwin (moved to 2027), Coal Creek (sold to
  Rainbow Energy, kept), Columbia (extended), Merom (sold to Hallador), Schahfer
  17/18 (moved, then 202(c)), Edgewater 5, R D Green, Lake Catherine 4. Those
  are exactly the class the reversal registry exists for.
* **Age discriminates coal and gas-CC strongly and gas-steam not at all**
  (AUC 0.50): MISO's gas-steam fleet is uniformly old (median 51 years,
  survivors and exits alike), so no age-based key can pick the three large
  steamers (Baxter Wilson 1967, Waterford 1975, Teche 1971) out of their
  peers. Any key that reaches gas_st must be owner-decision-based.
* **CO2 rate and heat rate — the model's tie-breaks — carry no signal about
  real exits at plant grain** (the released vs retained sets in §2.3 sit on
  the same CO2 range as the cohort; the three largest real coal exits, Rush
  Island, St Clair, Schahfer, are mid-CO2 plants retained in every screen).
* **Exits are overwhelmingly regulated-utility decisions** (88–92 % of coal /
  gas_st / oil exit MW, sector 1), i.e. IRP outcomes, while the model applies
  a merchant net-revenue screen to the whole fleet. The IPP fleet in MISO is
  small (12 % of coal, 22 % of gas_cc, 16 % of gas_ct MW). This is why the
  "energy-only revenue vs FOM" bar fails 77–92 % of a fleet 97 % of which
  stayed: the screen models a decision most of these owners do not face.

### 4.4 The rule-19 point that outranks the ranking question

Before any re-specification: the floor is a **backstop** by every document
that defines it (plan §3.2: "a mechanism change that grows [floor-retained
share] is masking an economics bug, not fixing adequacy"). On this run it
retains 96 GW of 100 GW failing — the masking share is 96 %. A selector that
decides 100 % of the composition from a 100 GW failing pool is no longer
choosing among marginal units; it is doing the screen's job with a key that
has no unit-level content. Re-specifying the key (any of §5's candidates)
while the screen still fails 77–92 % of the fleet would just move the
composition decision from one class constant to another attribute; the
discriminating information (§4.3) belongs in the **exit decision** — the
screen, or an exogenous channel that carries the owner's decision — not in
the adequacy backstop's sort order. That is the structural reading of D31 §7's
chain (additions under-build → floor binds → exits throttled): the floor is
throttling because the screen is wrong about who is failing, and the additions
gap sets how much of that wrongness the floor can hide.

---

## 5. Candidate re-specifications — driver, identification, expected consequence (stated before any implementation; none is implemented here)

| # | candidate | external driver | identification source (published, per unit?) | rule-13 forward test | rule-21 exposure | expected composition consequence (from the census, no solve) | disposition |
|---|---|---|---|---|---|---|---|
| **C1** | **Fix key 1 to the class constant** (`FOM × 1000 / (1 − EFORd)`) so CO2/heat-rate tie-breaks fire as designed | none — a correctness defect (§3.2) | n/a | n/a | **none** (no parameter) | cross-fuel: nil. Within coal: the release becomes the highest-CO2 tranches; vs the real cohort, indifferent (§4.3) | **ROUTE — repair lane, with a heterogeneous-pmax test** |
| C2 | Depth-ordered release (deepest shortfall first) | the owner's own margin | none new (uses the screen's depth) | passes trivially | none | gas_st (depth = full 35 $/kW-yr) → oil (25) → gas_ct (21) released BEFORE coal (median depth 18): the whole 42 GW of $0-revenue non-coal fleet would be first in line — a gross non-coal over-exit, worse than D27's coal over-exit and in the direction FFR-2B already refuted (legacy MISO gas_st 12.9 GW false-retire) | **REFUTED ex ante — do not test** |
| **C3** | **Honor fossil EIA-860 Schedule-3 planned dates as an exogenous exit input** (vintage-gated, reversal-registry-countered), i.e. `forecast_fossil_retirement_economic=False` posture or a new step-1 fossil arm with the economic screen residual | the owner's filed plan — the IRP outcome, published annually | **YES**: EIA-860 Schedule 3 `Planned Retirement Year/Month`, every unit, every vintage (the additions pipeline already uses the same form's proposed-generator schedule as a forecast input, so the asymmetry is a posture, not a data limit) | **passes**: the date regenerates every vintage and responds to conditions (it moved for Baldwin, Sherco 1, Schahfer); an announcement is a forward driver, not an outcome | none — no parameter; a channel posture | **Opens the non-coal channel**: would carry gas_st 1,065 / oil 291 / gas_ct 199 / gas_cc 22 MW of the real 2,127 / 543 / 399 / 858, plus coal 9,682 of 12,434; recall 69 % MW, precision 53 % MW, 87 % of dated MW within ±1 yr. The 10.8 GW false-positive class is the reversal/deferral class — the existing `hindcast_verified_announced_exits` counters only *superseded* registry rows (Campbell), NOT date deferrals (Baldwin, Sherco 1, Coal Creek, Columbia, Merom, Edgewater ≈ 6.5 GW) — a hindcast at the 2020 vintage would false-retire those unless a deferral is treated as the later vintage's information; in a forecast from a current vintage they carry their current dates. **rule 19**: two mechanisms would then decide fossil exits (dates + screen) — the reconciliation is the confirmed-exit precedent (exogenous step, screen residual), and it must be stated, not stacked | **ROUTE — PRIMARY; an owner POSTURE decision + T1-H A/B (`forecast_fossil_retirement_economic` posture, 2021–2025, LOYO)** |
| C4 | Age (operating year) as the within-fuel retention key, or as a screen going-forward-cost driver (remaining-life capex) | physical/depreciation life | YES: EIA-860 `Operating Year`, per unit | passes (ages forward deterministically) | **as a rank key: none. As a threshold or life-adjusted FOM: a parameter** — admissible only from a published life assumption (ATB/EIA plant life), never from the residual | coal AUC 0.77 / gas_cc 0.94 / gas_ct 0.70 — real gains within those classes; **gas_st 0.50 — no help** for the three large steamers; cross-fuel composition unchanged unless the class key also changes | ROUTE as a within-fuel successor to C1 only if C3 is refused; not a composition lever |
| C5 | Sector gate: regulated-utility units exit via C3 (filed plan), IPP/merchant units via the economic screen | who makes the decision (ratebase IRP vs merchant margin) | YES: EIA-860 `Sector` (1 = electric utility) per unit; plant `Regulatory Status` | passes (an attribute, regenerates) | none (a partition, no weight) | Routes 88–92 % of the real exit MW to the channel that identifies it, and confines the merchant screen to the ~15 % of the fleet whose owners face it; predicted to shrink the failing pool from 77–92 % of fleet to the IPP subset, which is what un-binds the floor | ROUTE — structural companion to C3; design doc first (interaction with confirmed exits, RPS-credited units, CHP sectors 3/5/7) |
| C6 | ISO/federal retention instruments as explicit retention (SSR, `rmr_end`, §202(c)) | reliability retention by MISO / DOE | YES: FERC SSR filings, DOE order log; registry already carries §202(c) as `superseded` rows; Attachment Y posting **blocked** | passes as an instrument set (the confirmed-exit precedent) | none | negligible for 2021–2025 composition (Campbell 1.56 GW retained in 2025 only), and it points the OPPOSITE way to the rule (retains coal). Verification needs the manual Attachment Y download (registry README, standing item) | already represented (superseded rows); no lever |
| C7 | Locational exemption (`capacity_deliverability_limits`, MISO LRZ) | zonal RA saturation | YES (in-repo LRR/LCR crosswalk) | passes | none | cannot change composition while 77–92 % of the fleet fails; the MISO forecast cell is `U` on its own merits, not this object | not this lane's object |
| C8 | Suspension/mothball state (SB/OS) as an exit-vs-suspend option | option value of a reversible mothball | EIA-860 `Status` per unit (an outcome record); the election itself is in the blocked Attachment Y posting | as a *mechanism*, only with an option-value model (a DOF); as a vintage-status INPUT (`retiree_vintage_status_scope` exists, default off), admissible | mechanism = DOF; input = none | modest: 20 % of surviving oil MW already SB/OS in 2020; explains part of the $0-revenue oil fleet that neither exits nor runs | note for the screen lane; not a retention key |

**The honest dead end on the charter's question.** Re-specifying the
RETENTION key requires a published per-unit driver of *which unit an ISO holds
back when adequacy binds*. In MISO 2021–2025 that driver does not exist,
because the event did not happen: no SSR was designated, the PRA never fell
short (cleared exactly PRMR in the vertical years, 1.7 % long in PY25/26), and
the one retention was federal and coal. The retention key therefore cannot be
identified from data — and rule 21 forbids identifying it from the residual.
The discriminating information lives one step upstream, in the owner's
decision (C3/C5), which is published per unit and forward-regenerable.

---

## 6. What this lane did NOT do, and why (rule 21 / charter)

* No retention weight, threshold, age cut-off, or FOM re-ranking was proposed
  as a parameter. C1 is a bit-exactness fix; C3 and C5 are channel postures
  with zero free parameters; C4's parametric form is explicitly flagged as
  admissible only from a published life table.
* The −74.3 % residual identified nothing here. It was used once, in §4.4,
  to locate the error (the failing pool is 4–6× the real cohort), and that
  location is independent of the residual's sign (D27's +52 % had the same
  pool).
* No solve. The fleet loader was called to read unit attributes already
  implied by the committed run (its pmax values match D31's event rows on
  1,026 of 1,463 units bit-exactly; the 437 differences are 2021→2022 fleet
  evolution and CC pmax reconciliation, none of which touch key 1's structure
  or the suffix result).
* The MISO lever queue (`docs/mechanism-testing-matrix.md` §5.4) was checked:
  it carries no item on the retirement floor's retention key; this lane adds
  no lever and writes no cell (charter). The repair lane, if chartered, owns
  rule 28 for anything it adds.
* The confirmed-registry's standing manual-download item (Attachment Y
  approved retirements/suspensions) stands unchanged; this lane could not
  reach it either and did not try alternative hosts.

---

## 7. Routed recommendation

1. **R1 — PRIMARY, owner decision: the fossil announced-date posture (C3).**
   Charter a T1-H A/B on MISO 2021–2025 with fossil EIA-860 planned dates
   honored as an exogenous step-1 input (vintage-gated at 2020; reversal
   registry armed; the economic screen residual), against the shipped
   posture, scored LOYO. Pre-declare from this finding's numbers: coal
   +9.7 GW, gas_st +1.1, oil +0.3, gas_ct +0.2 of exits carried by the
   channel; recall 5/19 → ≥13/19; false positives concentrated in the six
   deferred/sold coal plants (≈6.5 GW) unless the deferral class is countered.
   The rule-19 reconciliation (dates vs screen for fossil) is part of the
   charter, not an afterthought. **This is a posture question the owner must
   decide** — the shipped default's rationale ("an announcement is not a
   certainty") is a statement about precision (53 %), not admissibility, and
   the same form's proposed-generator schedule is already a forecast input.
2. **R2 — repair lane (code correctness, no DOF): fix `_floor_retention_merit`
   key 1 to the class constant** and add a heterogeneous-pmax tie-break test.
   Expected verdict change: none at the cross-fuel level; within-coal order
   becomes the designed CO2/heat-rate order. Rule 28: no field, no row —
   but the MISO `economic_retirement_screen` cell note should carry the
   defect citation when the repair lands.
3. **R3 — design doc for the sector gate (C5)** as C3's structural companion:
   which owners face the merchant screen. Zero parameters; interactions to
   state: confirmed exits (step 0), RPS-credited clean units, CHP sectors,
   and the additions screen's mirror image (utility builds are IRP-driven
   too — the same asymmetry probably explains part of the solar/wind
   under-build in D31 §7).
4. **R4 — scorer diagnostic, non-gated:** add plant-grain release precision
   (released MW at real-exit plants ÷ released MW) to `score_retirements`'
   reported block, alongside `plant_recall_frac`. Reads 13.5 % on D31.
   Committed artifacts only; no re-solve.
5. **R5 — DO NOT test C2** (depth-ordered release); the census refutes it
   ex ante and FFR-2B's legacy MISO arm already measured its signature.
6. **R6 — C4 (age) only as a within-fuel successor to R2 and only if R1 is
   refused**; never as a threshold identified against a residual.
7. **R7 — the Attachment Y manual download** remains the single item that
   would let C6 be verified (SSR/suspension count 2021–2025); it changes no
   recommendation above whichever way it reads.

---

## 8. Governance attestation

Rule 12: no solve launched, so nothing to sequence. Rule 22: no out-of-training
year solved, scored or registered; the analysis uses 2021–2025 committed
artifacts only, the holdout freeze untouched. Rules 13/14/21: no measured
outcome enters any proposal as an input (the filed date is an ex-ante owner
plan, admissible by the same test as the planned-additions pipeline; the
cohort is used only to MEASURE candidates' discriminating power, never to
identify a parameter — no parameter is proposed). Rule 15: no run produced,
nothing to register. Rule 27: the only pushed file is this new document; no
≥300-line source file touched. Rule 28: no mechanism tested, no field added,
no cell written; the lever queue was read. Collision check: D40/D41/D39
(NEISO/CCS/cross-ISO docs) and miso-200 (backcast namespace) share no file
with this lane; the branch was rebased onto `origin/main` before the push.

## 9. Reproduction (scratch probes, not committed)

* **Fleet key reconstruction:** `ScenarioConfig(**run_config.json["scenario_config"])`
  → `get_iso_config("MISO")` → `apply_interchange_topology` →
  `load_retired_within_window` → `load_or_synthesize_bins` →
  `load_planned_additions` → `load_confirmed_exits` → `build_base_fleet(…, 2021)`
  (2,085 units, 133,132 MW thermal); `_floor_retention_merit(config, g)` per
  unit; join to `evolution_2022.json` `pipeline_events` on `unit_id` (1,463 of
  1,663 matched; 19 of 23 decided). Sort by key 1 alone → decided ranks
  91–110 of 110 coal.
* **Cohort attributes:** `data/raw/eia-860/vintage_2020/eia860_generators.parquet`
  (BA = MISO) joined to `vintage_2020/eia860_generator_operable.parquet`
  (Sector, Utility) and to `capacity_actuals_miso.csv` retirement rows on
  `unit_id`; fuel taxonomy by energy source + prime mover; AUC = Mann-Whitney
  U / (n_exit × n_stay).
* **Status join:** union of 2022/2023/2024 `pipeline_events` by `unit_id`,
  plant code from `_p<id>_` (binned tranches) or the `<plant>_<gen>` prefix
  (legacy per-unit ids); real cohort grouped by (plant, fuel).
