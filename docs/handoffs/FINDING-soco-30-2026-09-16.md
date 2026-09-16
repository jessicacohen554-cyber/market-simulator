# FINDING — SOCO-30: unit outage windows + thermal tranches (frozen derives)

Lane **SOCO-30** · Opus `claude-opus-5` · branch `claude/soco-30-outages-tranches-r4t8` ·
2026-09-16 · base `origin/main` **`edd40943`**.
Charter: `docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-30, §8 W3 SOCO-30 delta,
§3 card **S7 (RULED)**, §7 gates **G4** / **G19**.
Rules in force: 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 23 `[R-FROZEN-DERIVE]`,
25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]`.

**Status: DONE.** Zero solves (this lane runs no LP). Zero `src/` edits, zero derive-script
edits, zero `ScenarioConfig` edits, zero mechanism-matrix cells moved (rule 28 — this lane arms
nothing). Rule 23 is trivially satisfied: **SOCO has never been solved**, so there is no residual
anything could have been derived against, and the 2023–2025 span was fixed by rule 16
`[R-ALLYEARS]` before the first derive.

Preconditions verified at base sha: `git log origin/main --grep=SOCO-20` → `1100c052`
*"Register SOCO as the ninth region"* + `f4fb5b76`; `git log --grep=SOCO-11` → `90257214`
*"Land EPA CAMPD hourly CEMS for AL and GA, 2023-2026"*. `get_iso_config("SOCO")` resolves,
three zones (`SOCO_AL`, `SOCO_GA`, `SOCO_MS`); `SUPPORTED_ISOS` carries **nine** regions
(`ERCOT CAISO MISO PJM NYISO NEISO SPP NWPP SOCO`) — SOCO is the ninth, as SOCO-20's own PR
title says. `campd.ISO_STATES["SOCO"] = ("AL", "GA", "MS", "FL")`.

---

## 0. COVERAGE, REPORTED FIRST — AND THE CHARTER'S PREMISE NEEDS ONE CORRECTION

**The charter delta reads "CEMS COVERAGE IS 91.6 % OF FOSSIL MW, not 100 % (FINDING-soco-10).
State the uncovered 8.4 %." That inverts SOCO-10's number.** SOCO-10 §1.2 and
`soco-data-audit.md` §2.4 measured **91.6 % as the MISSING share** — 45,797.3 MW of 50,005.0 MW
of CEMS-eligible fossil that had **no CAMPD extract** while AL and GA were absent from
`data/raw/campd-unit-level/`. **SOCO-11 then landed AL and GA**, which is precisely what closed
that gap, so quoting 91.6 % as the post-SOCO-11 *coverage* would double-count the lane that
fixed it. Re-measured here at HEAD on SOCO-10's own denominator (EIA-860 BA `SOCO`, the
CEMS-eligible technology set of audit §2.4, plant 67241 excluded per SOCO-10 §2.6(a)) —
**50,004.8 MW, reconciling SOCO-10's 50,005.0 to 0.2 MW**:

| | MW | share |
|---|---:|---:|
| CEMS-eligible fossil footprint (denominator) | **50,004.8** | 100.00 % |
| **Has a CAMPD unit-level record** (AL/GA/MS × 2023-25) | **47,977.6** | **95.95 %** |
| **Uncovered** | **2,027.2** | **4.05 %** |

**Coverage % by state — the headline the charter asks for first:**

| state | covered MW | state MW | **coverage** | plants |
|---|---:|---:|---:|---:|
| **MS** | 4,200.5 | 4,207.7 | **99.83 %** | 5 / 6 |
| **AL** | 19,306.1 | 19,529.5 | **98.86 %** | 19 / 27 |
| **GA** | 24,471.0 | 26,165.6 | **93.52 %** | 29 / 57 |
| **FL** | 0.0 | 102.0 | **0.00 %** | 0 / 1 |

By technology: **Conventional Steam Coal 100.00 %**, Natural Gas CC **99.68 %**, CAES
**100.00 %**, Natural Gas ST **94.29 %**, Petroleum Liquids 92.97 %, **Natural Gas CT
86.76 %**, and 0 % on the three trivial classes (gas ICE 7.0 MW, Other Gases 3.8 MW, Petroleum
Coke 90.0 MW). The whole coal fleet and essentially the whole CC fleet are observed; the gap is
**peaking CTs and small industrial/campus sites**, which is what CEMS coverage looks like in a
footprint whose fossil fleet is overwhelmingly Part-75 affected.

### 0.1 The uncovered 2,027.2 MW, by plant and class — not padded, not inferred (rule 13)

38 plants. The two that are not small carry **63 % of the whole gap between them**:

| code | plant | st | class | MW |
|---:|---|---|---|---:|
| 7709 | **Dahlberg** | GA | Natural Gas CT | **919.0** |
| 54538 | **Hartwell Energy Facility** | GA | Natural Gas CT | **360.0** |
| 10361 | Savannah River Mill | GA | Petroleum Coke (90.0) + Gas CT (50.4) | 140.4 |
| 10416 | Pensacola Florida Plant | FL | Gas CT (86.0) + Gas ST (16.0) | 102.0 |
| 50398 | International Paper Savanna Mill | GA | Natural Gas ST | 71.2 |
| 54096 | International Paper Riverdale Mill | AL | Gas CC (55.2) + Gas ST (11.6) | 66.8 |
| 62449 | Kimberly Clark Mobile – CHP Plant | AL | Natural Gas CT | 50.0 |
| 54358 | Clearwater Paper Corporation – Augusta | GA | Natural Gas ST | 39.0 |
| 54004 | WestRock Southeast, LLC. | GA | Natural Gas CT | 37.1 |
| 54239 | Naval Submarine Base Kings Bay | GA | Petroleum Liquids | 30.0 |
| 55044 | Packaging Corp. of America Jackson Mill | AL | Natural Gas ST | 28.8 |
| 54789 | Georgia-Pacific Brewton Mill | AL | Natural Gas ST | 28.4 |
| 54802 | Mead Coated Board | AL | Natural Gas CT | 25.0 |
| 753 | Crisp Plant | GA | Gas ST (12.5) + Gas CT (10.0) | 22.5 |
| 54550 | W&T Onshore Treating Facility (OTF) | AL | Natural Gas CC | 12.0 |
| 50146 | Imperial Savannah LP | GA | Natural Gas ST | 11.7 |
| 55274 | State Farm Support Center East | GA | Petroleum Liquids | 10.8 |
| 54985 | Crestwood Dothan | AL | Petroleum Liquids | 8.6 |
| 61927 | Georgia-Pacific Taylorsville Plywood | MS | Natural Gas CT | 7.2 |
| 58484 | MAS ASB Cogen Plant | GA | Gas ICE | 6.6 |
| 56076 | ABC Coke | AL | Other Gases | 3.8 |
| 63535 | Solar BESS Hybrid | GA | Natural Gas CT | 1.0 |
| — | **16 further GA petroleum-liquid standby sets** (hospitals, office towers, water treatment, campus microgrids), each 0.6–6.0 MW, + 0.4 MW of gas ICE at 63775 Tech Square Microgrid | GA | Petroleum Liquids / gas ICE | **45.3** |
| | | | **total** | **2,027.2** |

**Dahlberg (919.0 MW) and Hartwell (360.0 MW) are both `CT_PEAKER` in the model fleet, and
`CT_PEAKER` is outside `outages.QUALIFYING_PLANT_GROUPS` by the overlay's own convention** — a
peaker carries no outage overlay in any ISO because it dispatches economically. So the largest
part of the CEMS gap costs this lane's deliverable **nothing**: it would have been skipped even
if the data existed. No window was inferred for any uncovered plant and no substitute was
fabricated (rule 13 `[R-MEASURED]`).

**FL is the one state with zero coverage and it is a data gap, not a modelling choice.**
`campd.ISO_STATES["SOCO"]` carries `"FL"` on SOCO-10 §1.4's ruling, but no `FL_2023..2025`
extract exists on disk; the derive logs `(no unit-level extract for FL <year>: FL_<year>.parquet)`
three times and continues. Worth **102.0 MW / 0.20 %** of the footprint, one site
(Ascend Performance Materials Pensacola, plant 10416) — exactly SOCO-10 §2.3's "priority 3,
judgement call". It is picked up instead by the `-e923` sibling (§5). **ASK routed to SOCO-DESK:
fetch `FL_{2023,2024,2025}` and re-derive (one command, ~20 s), or record FL as a documented
exclusion.** Not this lane's file scope.

---

## 1. What ran, and what it produced

Five invocations of `scripts/data/derive_campd_unit_outages.py` and one of
`derive_thermal_tranches.py`, all `--iso SOCO --years 2023 2024 2025`. **Zero script edits, zero
flag-value changes, zero constant changes.**

| artifact | rows | sha256 |
|---|---:|---|
| `data/raw/campd-unit-outages-SOCO.csv` | **1119** | `321f9af3a5da9eb91d26944d22a78c10a504fea8eff626459ff1ee05262f7f87` |
| `data/raw/campd-unit-outages-short-SOCO.csv` | 34 | `0bd0e98a68982ba87eb9c5b58c20aa9c85a49b35288b87942485e0bdbaa0276e` |
| `data/raw/campd-unit-outages-layup-SOCO.csv` | 34 | `5317fe5c3fc617fa54c394729c5294e9fc8ec43a2196dff43e8f795837767ed5` |
| `data/raw/campd-unit-outages-e923-SOCO.csv` | 4 | `3fd01681e023f6db81ed22f3c13236b6b43cb0bb0903ee22d809a547bd705804` |
| `data/raw/campd-partial-outages-SOCO.csv` | 12 | `22168550d45271a1e9399723d7bc41388f251a23db510c8ae9f6dd931f85a4d5` |
| `data/raw/_processed-legacy/thermal_tranches_SOCO.csv` | 60 | `7b7f5f27d9cb5e952f040c6ca33405956832b1bab350aa619addbb7c7965df84` |

Provenance sidecars (`*.meta.json`) are emitted by the derives themselves for
`campd-unit-outages-SOCO`, `campd-unit-outages-short-SOCO`, `campd-partial-outages-SOCO` and
`thermal_tranches_SOCO`, each carrying the deriver path, the full `derive_invocation` block and
the per-year / per-group census. The `-layup` and `-e923` companions get no sidecar — that
matches every other ISO's committed set and the deriver is what decides it.

**Determinism.** The standard extract was derived twice from a clean tree and came back
byte-identical (`sha256sum -c` OK).

**The layup ordering trap, handled.** `--merit-order-guard` **rewrites the default-read
extract** (1119 → 1085 windows, the 34 reclassified moving to the companion). Every other ISO
commits the **guard-off** standard extract alongside the guard-on companion, so the standard
extract was re-derived guard-off afterwards and verified byte-identical to the pre-layup blob
(`321f9af3…`, `sha256sum -c` OK). The committed pair is the shape every other ISO carries.

**Header/provenance note.** The extract CSVs carry a bare column header, byte-for-byte the
13-column schema of `campd-unit-outages-MISO.csv` that the charter names as the output template
(`facility_name … total_units_at_plant`; `-layup` adds `out_of_merit_share`, `-partial` adds
`derate_factor`). The derive writes no comment banner and rule 23 forbids me adding one by hand,
so "source + method + CEMS vintage" lives in the sidecars, in the commit messages, and in §2
below, which is the record.

## 2. CEMS vintage — the exact blobs every number here was derived from

`data/raw/campd-unit-level/{ST}_{YR}.parquet` at branch HEAD, over the three
`campd.ISO_STATES["SOCO"]` states that have extracts (AL/GA are SOCO-11's intake; MS predates
the program). **FL has no file** (§0.1).

| file | blob | bytes | | file | blob | bytes |
|---|---|---:|---|---|---|---:|
| AL_2023 | `5e82e715192a` | 3,344,419 | | GA_2025 | `9525e4057514` | 3,227,774 |
| AL_2024 | `d2859fdbcc6d` | 3,314,917 | | MS_2023 | `4d4efe89569a` | 2,609,467 |
| AL_2025 | `9516df4071fe` | 3,303,950 | | MS_2024 | `38978f08ca87` | 2,668,598 |
| GA_2023 | `624b4766e925` | 3,111,090 | | MS_2025 | `3964237eefc7` | 2,613,158 |
| GA_2024 | `38aeff9a97dc` | 3,110,440 | | | | |

Fleet basis: `load_fleet_from_csv("SOCO", …) + load_retired_within_window(…)` = **393 units /
55,092.3 MW**, of which **43 plants / 34,576.1 MW** fall in `QUALIFYING_PLANT_GROUPS` (peakers
excluded by the overlay's own convention).

**GATE G19 — the timezone convention is INHERITED, not re-decided.** Every window in every
extract is `America/Chicago`, DST-aware, hour-ending, exactly as SOCO-10 §1.3 measured and
closed it (0 mismatching hours of 26,304 against that candidate; 26,301 against
`America/New_York`). All three zones are Central, Georgia included — the timezone is a property
of the balancing authority, not of the zone, and splitting Georgia onto Eastern would put one
zone's hour *t* against another's *t+1* in the same LP row. **No lane-level timezone decision was
taken and none was available to take.**

---

## 3. GATE G4 leg 1 — windows per CEMS state-year

| state | 2023 | 2024 | 2025 | total | verdict |
|---|---:|---:|---:|---:|---|
| **AL** | 196 | 206 | 240 | **642** | PASS |
| **GA** | 115 | 118 | 155 | **388** | PASS |
| **MS** | 21 | 31 | 37 | **89** | PASS |
| FL | — | — | — | — | no extract on disk; 102.0 MW / 0.20 % of the footprint (§0.1) |
| **total** | **332** | **355** | **432** | **1119** | |

**GATE G4 LEG 1: PASS — windows > 0 in every CEMS state in every year.** No state-year has a
zero to explain away.

Window shape: mean **25.2 d**, median 12.9 d, p90 55.8 d. By model group:

| group | windows | plants | mean days |
|---|---:|---:|---:|
| `CC_REGULAR` | 647 | 18 | 20.5 |
| `ST_GAS` | 186 | 4 | 22.6 |
| `COAL` | 170 | 6 | 33.9 |
| `CC_CHP` | 107 | 6 | 25.4 |
| `CT_CHP` | 5 | 3 | 153.7 |
| `ST_CHP` | 4 | 4 | 365.0 |

Capacity-source mix: `observed_peak` 473, `eia_exact` 290, `eia_digits_cc` 209, `eia_digits`
100, `eia_exact_cc` 39, `eia923_netzero` 8.

**Concentration is moderate and has no single-plant artefact.** Top plants by window count:
E C Gaston 116, Barry 104, Mid-Georgia Cogeneration 93, E B Harris 86, McWilliams 64, Bowen 64,
Tenaska Lindsay Hill 47, Victor J Daniel Jr 44, Greene County 40. The largest single plant is
**10.4 %** of the extract — nothing like NWPP's Clark (60.6 %), so there is no one plant SOCO-40
must sanity-check first.

**Vogtle 3 (COD 2023-07) and Vogtle 4 (COD 2024-04) emit ZERO rows**, as the charter requires:
plant 649 appears **0 times** in the extract, and no nuclear plant appears at all. A unit that
did not exist yet is a COD, not an outage; SOCO-15's online-mask repair owns it and the phantom
it removed was not re-introduced here.

**Card S7 is applied, not re-opened.** McIntosh (AL), EIA plant 7063, is carried in the fleet as
**`CT_PEAKER` at `pmax_mw = 25.0`** — the real summer/winter rating, not the 110 MW nameplate —
beside the site's four conventional CTs (110 / 110 / 169 / 166 MW). It is `CT_PEAKER`, so the
outage overlay skips it by the same convention it skips every peaker, and the CAES nameplate
reads **100 % CEMS-covered** in §0. Nothing about the ruling was revisited.

## 4. GATE G4 leg 2 — full-year windows, reported by unit with the reason

**Eight windows span a whole calendar year, and every one of them is the `eia923_netzero`
structural fallback. There is no measured full-year CEMS outage in SOCO, and no unit fell back
for want of data.**

The mechanism: a fleet plant that reported real grid generation in an earlier EIA-923 year but
has **no F923 filing and no CAMPD gross output** in the target year delivered nothing the
benchmark counts, so one full-year window is written. All eight are small non-CEMS
industrial/CHP sites; the reason is the same for every one — *ran in a prior EIA-923 year,
~zero grid delivery in the target year, absent from the CAMPD panel*:

| plant | name | group | year | unit MW |
|---:|---|---|---:|---:|
| 54096 | International Paper Riverdale Mill | CC_CHP | 2025 | 104.2 |
| 54789 | Georgia-Pacific Brewton Mill | ST_CHP | 2025 | 103.4 |
| 54358 | Clearwater Paper Corporation – Augusta | ST_CHP | 2025 | 84.7 |
| 62449 | Kimberly Clark Mobile – CHP Plant | CT_CHP | 2025 | 50.0 |
| 55044 | Packaging Corp. of America Jackson Mill | ST_CHP | 2025 | 44.4 |
| 54550 | W&T Onshore Treating Facility (OTF) | CC_CHP | 2025 | 12.0 |
| 50146 | Imperial Savannah LP | ST_CHP | 2025 | 11.7 |
| 61927 | Georgia-Pacific Taylorsville Plywood | CT_CHP | 2025 | 7.2 |

Eight rows totalling **417.6 MW**, comfortably inside the cross-ISO band (MISO 135 rows, PJM 95,
CAISO 78, NEISO 56, NWPP 12, NYISO 30, SPP 9). **All eight land in 2025** — and the deriver's own
`-e923` diagnostic says why, in terms that make this a *reporting* caveat rather than an outage
claim: *"2025: 8 candidate plants had NO EIA-923 filing → no window (assumed available)"*
against **0** in 2023 and **0** in 2024. The 2025 EIA-923 vintage is preliminary; **SOCO-40
should read the 2025 rows as a filing gap, not as eight simultaneous industrial shutdowns.** No
adjustment was made here — the measurement stands and the caveat is carried (rule 1
`[R-STRUCT]`).

## 5. Plant coverage of the qualifying fleet, and the four sibling extracts

Of the **43** `QUALIFYING_PLANT_GROUPS` fleet plants (peakers excluded), **38 carry ≥ 1
window — 88.4 % by plant count, 99.32 % by capacity (34,339.3 of 34,576.1 MW).** **Every one of
the five uncovered plants is absent from the CAMPD panel entirely** — not one is a plant the
detector saw and declined to flag, and every one is a ≤ 98 MW industrial/campus cogen site:

| plant | group | MW | state |
|---:|---|---:|---|
| 10416 Pensacola Florida Plant | CT_CHP/ST_CHP | 98.0 | FL *(no extract, §0.1)* |
| 50398 International Paper Savanna Mill | ST_CHP | 71.2 | GA |
| 54004 WestRock Southeast, LLC. | CT_CHP | 40.0 | GA |
| 54802 Mead Coated Board | CT_CHP | 21.0 | AL |
| 58484 MAS ASB Cogen Plant | CT_CHP | 6.6 | GA |

**Two** of the five (10416, 50398) are picked up by the `-e923` sibling; 54004, 54802 and 58484 — 67.6 MW between them — carry no availability evidence of any kind. **Sibling extracts by state-year:**

| state | short 23/24/25 | layup 23/24/25 | partial 23/25 | e923 23/24/25 |
|---|---|---|---|---|
| AL | 7 / 6 / 2 | 11 / 7 / 6 | 4 / 3 | 1 / 0 / 0 |
| GA | 1 / 4 / 10 | 3 / 4 / 2 | 1 / 4 | 0 / 0 / 1 |
| MS | 0 / 0 / 4 | 0 / 1 / 0 | — | — |
| FL | — | — | — | 1 / 1 / 0 |
| **total** | **34** | **34** | **12** | **4** |

- **`-short`** (34, coal-only by its detector's own construction) and **`-partial`** (12,
  likewise) cover the five big coal plants — Bowen, Miller, Scherer, Gaston, Daniel. Partial
  derate factors run **0.323 / 0.561 / 0.644** (min / median / max), inside NWPP's
  0.359 / 0.572 / 0.662.
- **`-e923`** (4 windows, 3 plants) out of **13 qualifying non-CAMPD candidates**; **0 skipped
  for a missing EIA-860 nameplate, 0 skipped for no EIA-923 history**. It carries no full-year
  row of its own. It stays **default-off**; no loader reads it.
- **`-layup`** (34) is coal-only too, and **that is a defect, not a fact about SOCO** — §6.1.

---

## 6. THREE MEASURED FINDINGS ROUTED TO SOCO-DESK — each needs a file this lane must not touch

### 6.1 The merit-order layup guard is COAL-ONLY in SOCO, because SOCO has no gas basis row

The guard reclassified **34 windows, all `COAL`** (Barry, E C Gaston, Bowen, Victor J Daniel Jr),
against SPP's 1,089 and every other priced ISO's hundreds. The cause is exact and measured, not
speculative — **it is NWPP-30 §7.1 reproduced in a second unpriced footprint:**

- The guard logged `merit-order panel SOCO 2023/2024/2025 [scope AL+GA+MS+FL]: 15 priced units`.
- The AL+GA+MS 2024 CAMPD panel contains **279 units: 238 gas (236 "Pipeline Natural Gas" + 2
  "Natural Gas"), 23 diesel oil, 17 coal, 1 wood.** 15 priced ≈ the coal units.
- `outage_detect.delivered_gas_price_hourly` returns `None` when the ISO carries no rows in
  `data/raw/gas_basis_by_iso_month.csv`, and that file's `iso` column is **`CAISO ERCOT MISO
  NEISO NYISO PJM SPP` — there is no SOCO row** (measured: `0`). Its docstring is explicit that
  Henry Hub is *"deliberately NEVER substituted for a missing basis"*, precisely so a missing
  basis cannot switch the test off while appearing to run.

So **every gas unit drops out of the SOCO merit panel and no gas window can ever be reclassified
as economic layup.** The companion is default-off and no loader reads it, so nothing downstream
is wrong today — but the artifact is **not comparable to a priced ISO's** and must not be read as
"SOCO has almost no economic layup".

**ASK:** `data/raw/gas_basis_by_iso_month.csv` is a shared reference table and the SOCO gas hub is
**lane SOCO-32**'s deliverable. When SOCO-32 lands one, the `-layup` companion should be
re-derived (one command, ~25 s) so it covers the gas fleet. Until then the desk should record the
companion as coal-only. *(Filed under rule 14 `[R-ACCURATE]`: the honest artifact with its
limitation named beats a fabricated basis.)*

### 6.2 THE PRIMARY-GROUP FILTER DROPS 4,872.9 MW — 2,954.5 MW OF IT COAL — FROM THE TRANCHE FILE

`derive_thermal_tranches.py` writes a row only for a plant's **primary** group (the one holding
the most nameplate) and attributes the **facility-summed** CAMPD net to it; the header calls the
primary-group filter *"the defect (nyiso-175b)"* in its own words. SOCO has **7 mixed plants**
(more than one model group behind one EIA plant code) and the cost is measured, not asserted:

| code | plant | primary → gets a row | **gets NO row** |
|---:|---|---|---|
| 3 | Barry | CC_REGULAR 1,821.2 | **COAL 1,118.5** · ST_GAS 160.0 |
| 6073 | Victor J Daniel Jr | CC_REGULAR 1,132.4 | **COAL 1,004.0** |
| 26 | E C Gaston | ST_GAS 1,020.0 | **COAL 832.0** |
| 10 | Greene County | CT_PEAKER 740.0 | ST_GAS 516.1 |
| 2049 | Jack Watson | ST_GAS 721.0 | CT_PEAKER 33.0 |
| 10416 | Pensacola Florida Plant | CT_CHP 82.0 | ST_CHP 16.0 |
| 54096 | International Paper Riverdale Mill | CC_CHP 17.0 | ST_CHP 11.6 |

**15 `(plant, group)` pairs / 4,872.9 MW of the fleet have no tranche row, including
2,954.5 MW — 25.7 % — of SOCO's entire coal fleet.** The file's three `COAL` rows (Bowen,
Miller, Scherer) are the three *unmixed* coal plants; every mixed one is missing. The same
filter shows up on the measurement side as an inflated `median_cf`: **Barry reads 150.0 %** (the
file's cap and its single highest value) and **Victor J Daniel Jr 113.9 %**, because the plant's
whole CEMS gross is divided by the CC group's nameplate alone. Measured directly on the 2024
panel with `campd_measured_classes.corrected_unit_class`, Barry's gross splits
CC_REGULAR 92.9 % / ST_GAS 7.1 % and Daniel's 83.2 % / 16.8 % — i.e. the denominator, not the
numerator, is what is wrong.

**Consequence today is bounded and stated plainly: nothing in W4 reads this file.** SOCO is
**deliberately absent from `CAMPD_BINNING_ISOS`** (`config/capacity_market.py`, SOCO-20's own
comment), so the first keeper runs legacy equal-width heat-rate bins and
`thermal_tranches_SOCO.csv` is the input to the **pre-declared per-plant-binning lever**, not to
SOCO-40. This lane makes **no argument for arming per-plant binning** — that is a ruled decision
and is not re-opened here.

**ASK (two parts, both `src/`, both out of this lane's file scope):**
1. That same SOCO-20 comment says *"SOCO-30 adds `SOCO` [to `CAMPD_BINNING_ISOS`] with the
   artifact."* **This lane cannot**: `CAMPD_BINNING_ISOS` lives in `src/`, it is a declared
   `config/solve_surface_declared.py` value (`65b4e3e163ffd580`), and moving it is a
   solve-surface fingerprint change with a cache-key blast radius — squarely gate-G8 territory
   and squarely a `[FABLE]` adjudication. The artifact now exists; the arming decision is the
   desk's, and §6.2 is the evidence it should weigh first.
2. `--per-unit-attribution` is the deriver's own repair for this defect, but it reads a
   `campd-unit-outages-perunit-SOCO.csv` companion that does not exist, and its classifier
   (`campd_unittype_class`) keys on CAMPD `unitType` — a **prime-mover** descriptor that has no
   coal concept at all, so on the 2024 panel it re-seats Barry/Daniel/Gaston entirely onto
   CC/ST classes and finds **zero coal**. **A naive per-unit re-derive would not fix SOCO's coal
   attribution and might silently make it worse.** Routed with that caveat attached rather than
   run: it needs a `[FABLE]` look at the classifier, not an extra flag from this lane.

### 6.3 Four SOCO CC plants carry corrupt EIA-860 summer-capacity rows, reconciled at load

Every fleet load in this lane logs, before any derive:

```
SOCO: CC plant 6073 fleet pmax sum 1904.4 MW exceeds trusted bound 1132.4 MW — reconciled (772.0 MW removed)
SOCO: CC plant 7897 fleet pmax sum 1314.8 MW exceeds trusted bound 1304.0 MW — reconciled ( 10.8 MW removed)
SOCO: CC plant 55382 fleet pmax sum 1353.0 MW exceeds trusted bound 1192.0 MW — reconciled (161.0 MW removed)
SOCO: CC plant 57037 fleet pmax sum 1308.5 MW exceeds trusted bound  840.0 MW — reconciled (468.5 MW removed)
```

**1,412.3 MW reconciled away across four plants**, three of them > 160 MW. The reconciliation is
existing committed behaviour and this lane changed nothing about it — but every capacity ratio in
this FINDING and every `unit_pct_of_plant` in the extract sits on the reconciled basis, so the
desk should know it is there. **Recorded, routed, not repaired** (`src/`).

---

## 7. Steps 3 and 4 — run, and why they commit nothing

- **`scripts/tag_mixed_plants.py`** takes **no `--iso`** and rewrites the ERCOT CAMPD bin sheet
  `data/raw/reference/custom-bin-assignments.csv` in place. That sheet is ERCOT-only (304 rows,
  an `ERCOT_Zone` column) and **the intersection of its `Plant_Code` set with SOCO's 110 fleet
  plant codes is EMPTY — measured, zero plants.** SOCO reaches its plant groups through the
  fleet path (`load_fleet_from_csv`), never the bin sheet, because it is absent from
  `CAMPD_BINNING_ISOS`. **There are no SOCO rows to append**, so the charter's "append, never
  reorder" instruction is satisfied vacuously. It was run against **scratch copies** so the
  committed sheets could not be disturbed — output `bins already split — reconciling registry
  only` / `registry already in sync with bins`, the copies came back byte-identical, and both
  committed sheets verified unchanged by `sha256sum -c` (`custom-bin-assignments.csv`
  `19d726cd…`, `master-plant-registry.csv` `49e8d9ee…`).
  *(Note the name collision: §6.2's "mixed plants" are SOCO's 7 multi-group EIA codes, which this
  ERCOT-only script does not and cannot address.)*
- **`scripts/data/build_offer_curve_overrides.py`** writes no file — it turns operator tweak
  lines into stdout JSON for `--offer-curve-delta-json`. Run as `--iso SOCO --list`, the
  non-mutating read, it returns the **load-bearing rule 25 `[R-ISO-SCOPE]` result**: every one of
  the 13 classes SOCO will carry — `CC_CHP`, `CC_INTERMEDIATE`, `CC_REGULAR`, `COAL`,
  `COAL_BIT`, `COAL_LIGNITE`, `COAL_PRB`, `COAL_WC`, `CT_CHP`, `CT_INTERMEDIATE`, `CT_PEAKER`,
  `ST_GAS`, `ST_GAS_INTERMEDIATE` — is **1.0 on every band** (`committed` / `econ_low` /
  `econ_high` / `peak`), and SOCO carries **no `phys_*` rows at all**. Only the structural
  shares differ (`econ_low_share` 0.5–0.556, `pct_peaking` 5–15), which are not the tuning
  channel. Against ERCOT's fitted set in the same run — `CT_PEAKER` 1.48 / 1.27 / 1.98 /
  **13.15** plus a full `phys_*` set, `CC_REGULAR` 0.92 / 1.16 / 1.41 / 2.25 — **no ERCOT-fitted
  multiplier leaks into SOCO.** The emitted delta JSON is `{}`. **SOCO-40 declares
  `authorized_price_tuning: NONE`** — and under card S2's no-price ruling there is no price
  residual to tune on in the first place.

---

## 8. Class summaries against MISO as a sanity band — REPORTED, NEVER TUNED (rule 1)

`thermal_tranches_SOCO.csv`: 60 rows over `(plant_code, plant_group)`, **47 `status=ok`** and
**13 `status=eia923_cf`** (CHP steam floors); 33 `(plant, group)` pairs skipped for too little
run-time. Capacity-weighted, `ok` rows only:

| group | SOCO n / MW | committed % | must-run % | must-run online % | peaking % | MISO committed % |
|---|---|---:|---:|---:|---:|---:|
| `CC_REGULAR` | 18 / 18,652.9 | 48.2 | 0.0 | 0.0 | 7.7 | 42.4 |
| `COAL` | 3 / 8,557.5 | 48.5 | 47.0 | 24.3 | 0.0 | 40.5 |
| `CT_PEAKER` | 18 / 8,419.5 | 12.8 | 0.0 | 0.0 | 0.0 | 16.1 |
| `ST_GAS` | 3 / 2,455.0 | 21.4 | 0.0 | 0.0 | 0.0 | 20.2 |
| `CC_CHP` | 4 / 718.5 | 48.3 | 0.0 | 0.0 | 5.9 | 45.3 |
| `CT_CHP` | 1 / 137.0 | 48.2 | 0.0 | 0.0 | 0.0 | 69.5 |

**Every distribution sits inside MISO's, class by class** (committed % p10 / p50 / p90):

| group | SOCO | MISO |
|---|---|---|
| `CC_REGULAR` | 22.5 / 44.8 / 70.0 | 28.4 / 42.1 / 70.0 |
| `CT_PEAKER` | 7.3 / 12.2 / 21.0 | 7.2 / 13.4 / 34.3 |
| `ST_GAS` | 17.2 / 18.6 / 27.6 | 9.3 / 18.4 / 32.5 |
| `COAL` | 36.6 / 43.2 / 59.8 | 27.1 / 36.7 / 61.2 |

Three divergences are named rather than smoothed:

1. **SOCO coal's `mustrun_pct` reads 47.0 % against MISO's 28.9 %**, while `mustrun_online_pct`
   — the physically-truer synchronization floor the derive's own docstring prefers — reads
   **24.3 % against 27.6 %, i.e. essentially identical**. The all-hours must-run statistic is the
   one the docstring warns reads *"~2× high for an always-online coal unit"*, and SOCO's coal is
   about as always-online as coal gets (Bowen 8,684 online hours, Miller **8,760**, Scherer
   8,730). So the divergence is the known estimator behaviour on a high-availability fleet, not a
   SOCO fact, and the floor a solve would use is in-band.
2. **`CC_REGULAR` `peaking_pct` 7.7 % vs MISO's 4.9 %** — SOCO's per-plant values run
   0.9 → 23.6 with a 3.3–4.0 mode, against MISO's p10/p50/p90 of 1.2 / 4.7 / 7.6. A hot, summer-
   peaking, duct-fired CC fleet showing a larger rarely-used top band is the expected direction;
   reported, untouched.
3. **`CT_CHP` 48.2 % vs MISO's 69.5 %** rests on **one plant on each side** (SOCO: Chevron Oil,
   137.0 MW; MISO: 5 plants / 830.2 MW). A one-plant mean is not a band; it is listed for
   completeness, not as a comparison.

Five `CC_REGULAR` rows and three `CC_CHP` rows sit exactly at the **70.0 %** committed cap, which
is a shared ceiling of the estimator, not a SOCO-specific value. **Nothing in this section was
used to change any parameter** — rule 1 `[R-STRUCT]` and rule 23 `[R-FROZEN-DERIVE]` both forbid
it, and there is no residual to tune against anyway.

---

## 9. Gates

| gate | result |
|---|---|
| **G4 leg 1** — windows > 0 in every CEMS state | **PASS** — AL 642, GA 388, MS 89; every state-year non-zero. FL has no extract (102.0 MW, 0.20 %), routed §0.1 |
| **G4 leg 2** — zero full-year fallbacks, else reported by unit with the reason | **8 fallback rows, every one reported by unit in §4** with its reason and the 2025 EIA-923 preliminary-vintage caveat; **zero measured full-year CEMS outages**; no unit fell back for want of data |
| **G19** — two-timezone footprint | **PASS by inheritance** — every window is `America/Chicago`, DST-aware, hour-ending per SOCO-10 §1.3; no lane-level timezone decision taken (§2) |
| committed-% and tranche distributions vs MISO as a sanity band | **§8** — reported, never tuned; the three divergences named with a structural reading and left alone |
| every output header cites source + method + CEMS vintage | sidecars (§1) + §2 + the commit messages; the CSVs carry the bare MISO-template column header, which rule 23 forbids me altering |
| offer-curve bands stay 1.0 (rule 25 `[R-ISO-SCOPE]`) | **PASS** — §7: all 13 classes 1.0 on every band, no `phys_*`, delta JSON `{}`, no ERCOT leak |
| non-SOCO diff = ∅ (gate G9) | `git diff origin/main --name-only` is **eight new SOCO-suffixed files and this doc**; both ERCOT reference sheets verified byte-identical by `sha256sum -c` |
| no `src/`, no derive-script, no `ScenarioConfig` edit (rule 28: no cell moves) | none — the three things that wanted one are **routed** in §6 |

## 10. Deliverables

| file | action | commit |
|---|---|---|
| `data/raw/campd-unit-outages-SOCO.csv` (+ `.meta.json`) | **NEW** | 1/4 `901a673d` |
| `data/raw/campd-unit-outages-short-SOCO.csv` (+ `.meta.json`) | **NEW** | 1/4 |
| `data/raw/campd-unit-outages-layup-SOCO.csv` | **NEW** | 1/4 |
| `data/raw/campd-unit-outages-e923-SOCO.csv` | **NEW** | 1/4 |
| `data/raw/campd-partial-outages-SOCO.csv` (+ `.meta.json`) | **NEW** | 1/4 |
| `data/raw/_processed-legacy/thermal_tranches_SOCO.csv` (+ `.meta.json`) | **NEW** | 2/4 `68407667` |
| `scripts/tag_mixed_plants.py` | run against scratch copies, **commits nothing** (§7) | 3/4 — no-op |
| `scripts/data/build_offer_curve_overrides.py` | `--list` read, **writes nothing** (§7) | 4/4 — no-op |
| `docs/handoffs/FINDING-soco-30-2026-09-16.md` | this file | — |

Plan §5 row **SOCO-30 → LANDED**. Gate **G4** is the precondition SOCO-40 checks by
`git log origin/main --grep=SOCO-3[012]`; this lane discharges the `SOCO-30` leg of it.

---

## Log entry

## soco-30 — 2026-09-16 — unit outage windows + thermal tranches (W3 frozen derives, zero-LP)

Lane SOCO-30, Opus claude-opus-5, branch claude/soco-30-outages-tranches-r4t8, base edd40943.
Source `docs/handoffs/FINDING-soco-30-2026-09-16.md`. Zero solves, zero src/ edits, zero
derive-script edits, zero matrix cells moved (rule 28 — this lane arms nothing). Rule 23
trivially satisfied: SOCO has never been solved, so there is no residual to derive against.

COVERAGE BY STATE, the headline, re-measured on SOCO-10's own 50,004.8 MW denominator:
MS 99.83 % · AL 98.86 % · GA 93.52 % · FL 0.00 % (no extract); footprint 95.95 %, uncovered
2,027.2 MW / 4.05 %. THE CHARTER'S PREMISE IS INVERTED AND IS CORRECTED HERE: SOCO-10's 91.6 %
was the MISSING share BEFORE SOCO-11 landed AL and GA, not a coverage ceiling. Coal 100.00 %,
CC 99.68 %, CAES 100.00 % covered; the 4 % gap is peaking CTs and small industrial sites, and
its two largest members (Dahlberg 919.0 MW, Hartwell 360.0 MW — 63 % of the gap) are CT_PEAKER,
which the overlay skips in every ISO anyway. Uncovered plants listed by plant and class in the
FINDING §0.1; nothing padded, no window inferred (rule 13).

SIX ARTIFACTS, six invocations, no flag or constant changed: campd-unit-outages-SOCO.csv 1119
windows (321f9af3), -short 34, -layup 34, -e923 4, campd-partial-outages-SOCO.csv 12,
thermal_tranches_SOCO.csv 60 rows (7b7f5f27). Standard extract derived twice byte-identical;
re-derived guard-off after --merit-order-guard rewrote it (1119 -> 1085) and verified identical
to the pre-guard blob. CEMS vintage: AL/GA/MS x 2023-2025, nine blobs pinned in FINDING §2.

GATE G4 LEG 1 PASS: AL 196/206/240, GA 115/118/155, MS 21/31/37 = 1119. No state-year zero.
GATE G4 LEG 2: 8 full-year rows, ALL the eia923_netzero structural fallback, ALL 2025, all small
non-CEMS CHP, each named by unit in §4; ZERO measured full-year CEMS outages and no unit fell
back for want of data. The deriver's own diagnostic says 8 candidate plants had NO 2025 EIA-923
filing against 0 in 2023/2024, so SOCO-40 reads the 2025 rows as a preliminary-vintage FILING gap
— stated, not adjusted (rule 1). GATE G19 PASS BY INHERITANCE: every window America/Chicago,
DST-aware, hour-ending per SOCO-10 §1.3; no lane-level timezone decision was taken.

CARD S7 APPLIED, NOT RE-OPENED: McIntosh 7063 is CT_PEAKER at pmax 25.0 MW beside the site's four
conventional CTs. VOGTLE EMITS ZERO ROWS (plant 649 absent from the extract; no nuclear plant
appears) — SOCO-15's COD mask owns it and the phantom was not re-introduced.

CLASS BANDS vs MISO, reported never tuned (§8): committed p10/p50/p90 CC_REGULAR 22.5/44.8/70.0
vs 28.4/42.1/70.0 · CT_PEAKER 7.3/12.2/21.0 vs 7.2/13.4/34.3 · ST_GAS 17.2/18.6/27.6 vs
9.3/18.4/32.5 · COAL 36.6/43.2/59.8 vs 27.1/36.7/61.2. Three divergences named: coal mustrun_pct
47.0 vs 28.9 is the estimator's known ~2x-high behaviour on an always-online fleet (Miller 8,760
online hours) while mustrun_online reads 24.3 vs 27.6, in band; CC peaking 7.7 vs 4.9 is a
duct-fired summer-peaking fleet; CT_CHP 48.2 vs 69.5 is one plant against five.

STEPS 3 AND 4 COMMIT NOTHING: tag_mixed_plants.py is ERCOT-only and its Plant_Code intersection
with SOCO's 110 fleet codes is EMPTY (run against scratch copies; both committed sheets verified
byte-identical, 19d726cd / 49e8d9ee). build_offer_curve_overrides --iso SOCO --list: all 13
classes 1.0 on committed/econ_low/econ_high/peak, no phys_* rows, delta JSON {} — no ERCOT-fitted
multiplier leaks (rule 25). SOCO-40 declares authorized_price_tuning: NONE.

THREE FINDINGS ROUTED TO SOCO-DESK, each needing a file this lane must not touch. (1) The layup
merit guard is COAL-ONLY because gas_basis_by_iso_month.csv has ZERO SOCO rows, so all 238 gas
units of the 279-unit panel drop out and 15 priced units approx = the 17 coal — NWPP-30 §7.1
reproduced; re-derive when SOCO-32 lands a gas hub, and until then do not read the companion as
"SOCO has no economic layup". (2) THE PRIMARY-GROUP FILTER DROPS 15 (plant,group) PAIRS /
4,872.9 MW FROM THE TRANCHE FILE, INCLUDING 2,954.5 MW — 25.7 % — OF SOCO'S COAL: SOCO has 7
mixed plants and Barry/Daniel/Gaston each lose their COAL row to a CC or ST primary, which also
inflates Barry's median_cf to the 150.0 cap. Bounded today because SOCO is deliberately absent
from CAMPD_BINNING_ISOS and NOTHING IN W4 READS THIS FILE. SOCO-20's comment says SOCO-30 adds
SOCO to CAMPD_BINNING_ISOS "with the artifact" — THIS LANE CANNOT: it is src/, a declared
solve_surface value (65b4e3e163ffd580), a gate-G8 cache-key move and a [FABLE] call; the artifact
now exists and §6.2 is the evidence the desk should weigh. --per-unit-attribution is NOT a safe
fix as-is: its classifier keys on CAMPD unitType, a prime-mover descriptor with no coal concept,
and on the 2024 panel it re-seats Barry/Daniel/Gaston onto CC/ST and finds ZERO coal. (3) Four
SOCO CC plants (6073, 7897, 55382, 57037) carry corrupt EIA-860 summer-capacity rows and
1,412.3 MW is reconciled away at every fleet load — existing committed behaviour, unchanged here,
but every unit_pct_of_plant in the extract sits on that basis.

Plan §5 row SOCO-30 -> LANDED. Gate G4 discharged for the SOCO-30 leg of SOCO-40's precondition.
