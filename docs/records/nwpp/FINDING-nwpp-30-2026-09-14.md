# FINDING — NWPP-30: unit outage windows + thermal tranches (frozen derives)

Lane **NWPP-30** · Opus `claude-opus-5` · branch `claude/nwpp-30-outages-tranches-q7m4` ·
2026-09-14 · base `origin/main` **`d54cd9c5`**.
Charter: `docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-30, §3 card **N8 (RULED)**,
§7 gates **G4** / **G5**, §8 W3 NWPP-30 delta.
Rules in force: 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 23 `[R-FROZEN-DERIVE]`,
25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]`.

Preconditions verified at base sha: `get_iso_config("NWPP")` resolves, five zones
(`NWPP-NW`, `NWPP-OR`, `NWPP-INLAND`, `NWPP-EAST`, `NWPP-SNV`); `SUPPORTED_ISOS` now carries
**nine** regions (`ERCOT CAISO MISO PJM NYISO NEISO SPP NWPP SOCO`) — the charter said eight,
and the ninth is SOCO, which registered the same day (plan §0 re-count rule: I report the
count I found). `campd.ISO_STATES["NWPP"] = (ID, MT, NV, OR, UT, WA, WY)`; all 21 state-years
on disk, the twelve ID/OR/UT/WA files landed by NWPP-11.

---

## 0. COVERAGE ARITHMETIC — REPORTED FIRST, MEASURED AT THIS SHA

NWPP-10 §2 item (8) **projected** what CAMPD would reach once NWPP-11 landed. NWPP-11 has
landed, so this is no longer a projection. Re-measured here on NWPP-10's own denominator
(EIA-860 generators whose `balancing_authority_code ∈ NWPP_BAS`, all statuses —
**939 plants / 98,238.1 MW**, reconciling NWPP-10's footprint total exactly):

| | plants | MW | % of footprint nameplate |
|---|---:|---:|---:|
| NWPP footprint (denominator) | 939 | 98,238.1 | 100.00 % |
| **Has a CAMPD unit-level record** (7 states × 2023-25) | **54** | **29,617.9** | **30.15 %** |
| **Carries ≥ 1 row of the outage extract this lane landed** | **55** | **28,007.4** | **28.51 %** |
| NWPP-10's projected post-NWPP-11 expectation | — | 30,431.8 | 30.98 % |
| NWPP-10's Part-75 proxy upper bound | — | 32,059.5 | 32.63 % |

**The projection holds: 30.15 % measured against 30.98 % projected, 0.83 pt low** — the
residue is the nine predicted-but-absent small cogeneration/industrial sites NWPP-10 itemised
as the expected non-Part-75 residue, which really are absent. (54 vs 55 plants is not a
contradiction: the extract's 55 include the 8 non-CEMS plants carrying an `eia923_netzero`
full-year row, and exclude CEMS plants whose only model bin is `CT_PEAKER`.)

**On energy**, EIA-923 net generation over the same footprint:

| year | footprint | CAMPD-present plants | share | plants carrying an outage row | share |
|---|---:|---:|---:|---:|---:|
| 2023 | 297.66 TWh | 119.63 TWh | **40.2 %** | 115.69 TWh | **38.9 %** |
| 2024 | 307.35 TWh | 118.52 TWh | **38.6 %** | 114.31 TWh | **37.2 %** |
| 2025 | 235.48 TWh *(preliminary vintage, 260 reporting plants — not comparable)* | 103.12 TWh | 43.8 % | — | — |

Measured 40.2 / 38.6 % against NWPP-10's Part-75 proxy **bound** of 43.6 / 41.8 %: again
slightly under the bound, for the same reason.

**Why the share is structural and not a data gap** — footprint nameplate by technology,
measured here, not quoted:

| conventional hydro | onshore wind | solar PV | pumped storage | nuclear | *(CEMS-eligible fossil combustion)* |
|---:|---:|---:|---:|---:|---:|
| **34.28 %** | 15.44 % | 10.41 % | 0.34 % | 1.28 % | ~33 % |

34.3 % hydro + 25.9 % VRE + 1.3 % nuclear + 2.5 % batteries + 1.0 % geothermal is **65 % of
the footprint that CEMS can never cover, by construction**. CAMPD reaching ~30 % of nameplate
here is CEMS working correctly on a hydro-dominated pool, not an intake failure. **CO** is
absent from `ISO_STATES` by design (its one footprint plant is 7.5 MW of hydro) and **CA** is
measured **inert** (50.8 MW of footprint, 0.0 MW CEMS-present) — both confirmed at this sha.

**Per state**, CAMPD-present share of that state's footprint nameplate:

| NV | UT | WY | MT | ID | OR | WA | CA | CO |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 58.0 % | 58.8 % | 48.7 % | 28.3 % | 19.1 % | 16.9 % | 13.2 % | 0.0 % | 0.0 % |

WA and OR read low because that is where the hydro is; NV and UT read high because that is
where the thermal is.

---

## 0b. WHAT EACH OUTPUT IS FOR — CARD N8 IS RULED, AND IT SPLITS THIS LANE IN TWO

- **The outage windows are read by the first keeper regardless of binning.**
  `market_sim.data.outages.unit_outage_derate_factors` consumes
  `campd-unit-outages-NWPP.csv` off the fleet path, not the bin sheet. This is the
  load-bearing half of the lane.
- **The thermal tranches are NOT read by anything in W4.** Card N8 ruled
  `use_campd_bins=False` at sitting #4 and **NWPP is absent from `CAMPD_BINNING_ISOS`**, so
  the first keeper runs legacy equal-width heat-rate bins. `thermal_tranches_NWPP.csv` is
  landed as the input to the **pre-declared W5 CAMPD-per-plant lever**. Stated plainly as the
  charter requires: **nothing in W4 reads it.** This lane makes no argument for arming
  per-plant binning — that is a ruled decision and is not reopened here.

---

## 1. What ran, and what it produced

Five invocations of `scripts/data/derive_campd_unit_outages.py` and one of
`derive_thermal_tranches.py`, all `--iso NWPP --years 2023 2024 2025`. **Zero script edits,
zero flag-value changes, zero constant changes.** Rule 23 `[R-FROZEN-DERIVE]` is trivially
satisfied: NWPP has no solve, so there is no residual anything could have been derived
against, and the three-year span was fixed before the first derive to match the training span
(rule 16 `[R-ALLYEARS]`).

| artifact | rows | sha256 |
|---|---:|---|
| `data/raw/campd-unit-outages-NWPP.csv` | **2270** | `39bb3416ef51993c300d6a89e7198783a60cef6a3dfc7c43634e18ecf718b52a` |
| `data/raw/campd-unit-outages-short-NWPP.csv` | 209 | `7fa91b1ec0877f276ceb2da13974376d228043987b8e1c1e82b4f0dc3e07aa4f` |
| `data/raw/campd-unit-outages-layup-NWPP.csv` | 17 | `05c37836b5afc455863518fc466d93f0cf1bc1305c8b70c647446e05f9889581` |
| `data/raw/campd-unit-outages-e923-NWPP.csv` | 19 | `c09d92c12e035f917c6ad3e96dca7528995432740fab7c3ec5f3311e9859675f` |
| `data/raw/campd-partial-outages-NWPP.csv` | 111 | `e58d90047ced7d5bd0b6dd198984590ed0c7e3fb78339ed876ddff7ee28174e2` |
| `data/raw/_processed-legacy/thermal_tranches_NWPP.csv` | 68 | `486ef1dec8dfe11467252500c06cc266e9eb4883af2b259852b421b626d20205` |

Provenance sidecars (`*.meta.json`) are emitted by the derives themselves for
`campd-unit-outages-NWPP`, `campd-unit-outages-short-NWPP`, `campd-partial-outages-NWPP` and
`thermal_tranches_NWPP`, each carrying the deriver path, the full `derive_invocation` block
and the per-year / per-group census. The `-layup` and `-e923` companions get no sidecar —
that matches every other ISO's committed set and the deriver is what decides it.

**Header/provenance note.** The extract CSVs carry a bare column header, byte-for-byte the
13-column schema of `campd-unit-outages-MISO.csv` that the charter names as the template
(`facility_name … total_units_at_plant`; `-layup` adds `out_of_merit_share`, `-partial` adds
`derate_factor`). The derive writes no comment banner and rule 23 forbids me adding one by
hand, so "source + method + CEMS vintage" lives in the sidecars plus §2 below, which is the
record.

**The layup ordering trap, handled.** `--merit-order-guard` **rewrites the default-read
extract** (2270 → 2253 windows, the 17 reclassified moving to the companion). Every other ISO
commits the **guard-off** standard extract alongside the guard-on companion, so the standard
extract was re-derived guard-off afterwards and verified **byte-identical** to the pre-layup
blob (`sha256 39bb3416…`, `sha256sum -c` OK). The committed pair is the same shape every
other ISO carries.

## 2. CEMS vintage

`data/raw/campd-unit-level/{ST}_{YR}.parquet` at branch HEAD, one file per state-year over
`campd.ISO_STATES["NWPP"]` (7 states × 3 years = 21 files; **CO has no file and needs none**).
ID/OR/UT/WA 2023-2025 are the NWPP-11 intake; MT/NV/WY predate the program. Blob identities:

| file | blob | bytes | | file | blob | bytes |
|---|---|---:|---|---|---|---:|
| ID_2023 | `ef8876d53b9a` | 447342 | | UT_2023 | `45cae3fd0fab` | 2009161 |
| ID_2024 | `44472a3e3a08` | 457720 | | UT_2024 | `4b4dc6b8142f` | 2156004 |
| ID_2025 | `4f01186b9d90` | 469855 | | UT_2025 | `07f01bf163de` | 2027202 |
| MT_2023 | `07748ff8e6c4` | 813547 | | WA_2023 | `3f457737b630` | 1116153 |
| MT_2024 | `e4f12c0c51a9` | 743566 | | WA_2024 | `ea8353f1d942` | 1073764 |
| MT_2025 | `21ac65851956` | 673141 | | WA_2025 | `3fd046c56875` | 950958 |
| NV_2023 | `164c17606130` | 2069958 | | WY_2023 | `2ab497b793be` | 2501243 |
| NV_2024 | `c68a2cf8a124` | 2251216 | | WY_2024 | `6e97ce3851a0` | 2462811 |
| NV_2025 | `42daa3f38c34` | 2090399 | | WY_2025 | `213a0e43aaa7` | 2367721 |
| OR_2023 | `27d7934d43e3` | 846350 | | | | |
| OR_2024 | `2758061e9fce` | 862751 | | | | |
| OR_2025 | `fd2aea4e40c2` | 715454 | | | | |

Fleet basis: `load_fleet_from_csv("NWPP", …) + load_retired_within_window(…)` =
**445 thermal units / 29,639.8 MW**, of which **69 plants / 24,238.1 MW** fall in
`QUALIFYING_PLANT_GROUPS` (peakers excluded by the overlay's own convention).

## 3. Gate G4 leg 1 — windows per CEMS state-year

| state | 2023 | 2024 | 2025 | total | verdict |
|---|---:|---:|---:|---:|---|
| **NV** | 572 | 654 | 565 | **1791** | PASS |
| **WA** *(NWPP-11)* | 51 | 61 | 82 | **194** | PASS |
| **WY** | 27 | 18 | 39 | **84** | PASS |
| **UT** *(NWPP-11)* | 28 | 20 | 30 | **78** | PASS |
| **OR** *(NWPP-11)* | 23 | 16 | 20 | **59** | PASS |
| **MT** | 12 | 13 | 12 | **37** | PASS |
| **ID** *(NWPP-11)* | 4 | 7 | 4 | **15** | PASS |
| (non-CEMS) | 2 | 1 | 9 | 12 | the `eia923_netzero` structural fallback, §4 |
| CO | — | — | — | — | no extract, none needed (NWPP-10 §2.3: 7.5 MW of hydro) |
| CA | — | — | — | — | on disk, **measured inert** — zero footprint facilities |

**GATE G4 LEG 1: PASS — windows > 0 in every CEMS state in every year, all four NWPP-11
states included.** No state has a zero to explain away.

Window shape: mean 19.6 d, median 10.9 d, p90 37.6 d. By model group: `CC_REGULAR` 1882
windows / 23 plants (mean 16.0 d), `COAL` 147 / 15 (25.1 d), `CC_CHP` 127 / 7 (31.6 d),
`ST_GAS` 104 / 6 (28.8 d), plus the 10 non-CEMS `CT_CHP`/`ST_CHP` full-year rows.

**NV carries 78.9 % of all windows, and ONE PLANT carries most of those.** Of the 1,791 NV
windows, **1,376 (76.8 % of NV, 60.6 % of the whole extract) are NV Energy's Clark**
(EIA 2322, 24 monitored units), then Las Vegas Generating Station 134, Silverhawk 58, Nevada
Cogeneration #1 54, Apex 35, Tracy 32. Clark is 24 heavily-cycled units each going genuinely
dead for ≥ 5 days many times a year, and the event-based detector flags each one — a real-fleet
fact about a 24-unit peaking CC site, not a detector artifact. It is reported, not adjusted
(rule 1 `[R-STRUCT]`), and it is the single number NWPP-40 should sanity-check first.

## 4. Gate G4 leg 2 — full-year windows, reported by unit with the reason

**Twelve windows span a whole calendar year, and every one is the `eia923_netzero` structural
fallback. There is no measured full-year CEMS outage in NWPP, and no unit fell back for want
of data.** (Contrast SPP-30, which carried one genuine measured full-year outage.)

The mechanism: a fleet plant that reported real grid generation in an earlier EIA-923 year but
has **no F923 filing and no CAMPD gross output** in the target year delivered nothing the
benchmark counts, so one full-year window is written. All twelve are small non-CEMS
industrial/CHP/commercial plants; the reason is the same for every one — *ran in a prior
EIA-923 year, ~zero grid delivery in the target year, absent from the CAMPD panel*:

| plant | group | year | unit MW |
|---|---|---|---:|
| 7028 Whitehead | CT_CHP | 2025 | 26.5 |
| 10215 Snowbird Power Plant | CT_CHP | 2025 | 6.5 |
| 10504 Amalgamated Sugar Twin Falls | ST_CHP | 2025 | 12.7 |
| 10784 Colstrip Energy LP | COAL | 2025 | 46.1 |
| 54374 Sinclair Oil Refinery | CT_CHP | 2023 | 5.0 |
| 54690 Amalgamated Sugar LLC Nampa | ST_CHP | 2025 | 8.2 |
| 57915 WE Soda Alkalai LLC | COAL | 2025 | 41.0 |
| 58191 US Magnesium | CT_CHP | 2023 | 48.0 |
| 58191 US Magnesium | CT_CHP | 2024 | 48.0 |
| 58191 US Magnesium | CT_CHP | 2025 | 48.0 |
| 58382 Threemile Digester | CT_CHP | 2025 | 4.8 |
| 63423 BYU Central Heating Plant | CT_CHP | 2025 | 16.5 |

Twelve rows totalling **311.3 MW** is squarely inside the cross-ISO band (MISO 135, PJM 95,
CAISO 78, NEISO 56, NYISO 30, SPP 9 rows). **Nine of the twelve land in 2025**, which is the
preliminary EIA-923 vintage NWPP-10 flagged (260 reporting plants against 848-879) — so some
of the 2025 rows are a *reporting* gap rather than an outage, and NWPP-40 should read them
that way. The deriver's own diagnostic says so directly: *"2025: 9 candidate plants had NO
EIA-923 filing → no window (assumed available)"* in 2025 against **0** in 2023 and 2024.

**Capacity-source mix** of the standard extract: `eia_digits` 1431, `observed_peak` 310,
`eia_digits_cc` 235, `eia_exact` 156, `eia_exact_cc` 126, `eia923_netzero` 12.

## 5. Plant coverage of the qualifying fleet, and the 14 that carry nothing

Of the **69** `QUALIFYING_PLANT_GROUPS` fleet plants (peakers excluded),
**55 carry ≥ 1 window — 79.7 % by plant count, 95.2 % by capacity (23,081.3 of 24,238.1 MW).**
**Every one of the 14 uncovered plants is absent from the CAMPD panel entirely** — not one is
a plant the detector saw and declined to flag:

| plant | group | MW | | plant | group | MW |
|---|---|---:|---|---|---|---:|
| 8073 Beaver | CC_REGULAR | 468.8 | | 56509 Tesoro SLC Cogeneration | CT_CHP | 23.0 |
| 7931 Coyote Springs II | CC_REGULAR | 287.0 | | 57348 CityCenter Central Plant | CT_CHP | 8.0 |
| 54268 HF Sinclair Puget Sound | CT_CHP | 120.0 | | 56163 Kennecott Power Plant | CT_CHP | 5.9 |
| 56312 Shute Creek Facility | CT_CHP | 100.5 | | 58597 HTW Plant 303 COGEN | CT_CHP | 5.6 |
| 54349 Nevada Cogen 2 Black Mtn | CC_CHP | 93.1 | | 57653 Oregon State Univ. Energy Ctr | CT_CHP | 5.2 |
| 54318 General Chemical | COAL | 30.0 | | 59496 BYUI Central Energy Facility | CT_CHP | 4.6 |
| | | | | 69880 University of Montana CHP | CT_CHP | 3.6 |
| | | | | 62319 Western Sugar Coop Billings | COAL | 1.5 |

Twelve of the fourteen are ≤ 120 MW industrial/campus CHP — the expected non-Part-75 residue,
and six of them are picked up by the `-e923` sibling (§6). **The two that are not small are
both real and both have a named cause**, and the second is a defect:

- **8073 Beaver (468.8 MW CC, PGE, Clatskanie OR) is the largest genuinely-blind plant in the
  footprint, and it is not a small one.** It does not appear in `OR_2023/24/25` under its own
  code or any name — the committed OR panel is seven facilities (54761, 55103, 55328, 55544,
  56227, 58503, 7350), no `facilityId` 8073 and no facility whose name matches *Beaver* in any
  of the seven NWPP state files. **It is not idle**: EIA-923 puts it at **1.692 TWh (2023) and
  1.713 TWh (2024)**, ~41 % capacity factor, so it also takes no `eia923_netzero` row — the
  fallback fires only on a plant that delivered nothing. Its six 1974/1977-vintage CTs are
  plausibly outside Part 75's affected-unit scope, which is the same reason the Part-75 proxy
  over-predicts (§0). **Consequence for NWPP-40: 468.8 MW of working combined cycle dispatches
  with no outage overlay and no availability evidence of any kind.** Recorded as measured; no
  action available inside this lane's file scope, and no fabricated substitute offered.
- **7931 Coyote Springs II (287.0 MW CC, Avista, BPAT)** is uncovered because **its CEMS units
  are filed under its neighbour's ORIS code** — see §7, which is routed.

## 6. The four sibling extracts, by state-year

| state | short 23/24/25 | layup 23/24/25 | partial 23/24/25 | e923 23/24/25 |
|---|---|---|---|---|
| WY | 40 / 39 / 47 | 1 / 0 / 0 | 43 / 27 / 13 | — |
| MT | 15 / 12 / 7 | — | 0 / 1 / 4 | — |
| UT | 10 / 6 / 19 | 1 / 0 / 0 | 1 / 0 / 3 | — |
| WA | 5 / 4 / 4 | — | 1 / 1 / 1 | — |
| NV | 0 / 0 / 1 | 5 / 6 / 4 | 7 / 8 / 1 | — |
| (non-CEMS) | — | — | — | 6 / 5 / 8 |
| **total** | **209** | **17** | **111** | **19** |

- **`-short`** (209) and **`-partial`** (111) are **100 % COAL**, as their coal-only detectors
  require. Partial-derate factors run 0.359 / 0.572 / 0.662 (min / median / max).
- **`-e923`** (19 windows, 8 plants: Amalgamated Sugar ×2, Colstrip Energy LP, Nevada Cogen 2,
  Sinclair Oil Refinery, Kennecott, Oregon State University, US Magnesium) out of 23 qualifying
  non-CAMPD candidates; **0 skipped for a missing EIA-860 nameplate**, 1 skipped for no EIA-923
  history. It carries four full-year rows of its own (Sinclair 2023; US Magnesium 2023/24/25),
  distinct from the standard extract's twelve. It stays **default-off**; no loader reads it.
- **`-layup`** is the one that is not like the other ISOs', and the reason is measured, §7.

## 7. THREE MEASURED FINDINGS ROUTED TO NWPP-DESK — each needs a file this lane must not touch

### 7.1 The merit-order layup guard is COAL-ONLY in NWPP, because NWPP has no gas basis row

The guard reclassified **17 windows, all COAL** (North Valmy 7, TS Power 7, Hunter 1, Jim
Bridger 1), against SPP's 1,089 and every other ISO's hundreds. The cause is exact, not
speculative:

- The guard's panel logged `merit-order panel NWPP [scope ID+MT+NV+OR+UT+WA+WY]: 35 / 33 / 32
  priced units` for 2023 / 2024 / 2025.
- The 7-state 2024 CAMPD panel contains **170 units: 137 gas (122 "Pipeline Natural Gas" +
  15 "Natural Gas") and 33 coal.** 33 priced ≈ 33 coal.
- `outage_detect.delivered_gas_price_hourly` returns `None` when the ISO carries no rows in
  `data/raw/gas_basis_by_iso_month.csv`, and that file's `iso` column is
  **`CAISO ERCOT MISO NEISO NYISO PJM SPP` — there is no NWPP row.** Its docstring is explicit
  that Henry Hub is *"deliberately NEVER substituted for a missing basis"*, precisely so a
  missing basis cannot switch the test off while appearing to run.

So **every gas unit drops out of the NWPP merit panel and no gas window can ever be
reclassified as economic layup.** The companion is default-off and no loader reads it, so
nothing downstream is wrong today — but the artifact is *not* comparable to another ISO's and
must not be read as "NWPP has almost no economic layup".

**ASK:** `data/raw/gas_basis_by_iso_month.csv` is a shared reference table and the NWPP gas hub
is **lane NWPP-33**'s deliverable. When NWPP-33 lands a gas hub/basis, the `-layup` companion
should be re-derived (one command, ~40 s) so it covers the gas fleet. Until then the desk
should record the companion as coal-only.

### 7.2 CEMS ORIS 7350 carries BOTH Coyote Springs plants — a split-plant remap is missing

**The arithmetic, four independent ways:**

1. CEMS facility 7350 "Coyote Springs" (OR) has exactly two units, `CTG1` and `CTG2`, summing
   **4.27 / 4.44 / 4.24 TWh** in 2023/24/25 — an annual mean of **505.7 MW** against EIA plant
   7350's **296.0 MW** of nameplate (208 CT + 88 CA). That is a 171 % capacity factor, which is
   not a thing.
2. EIA plant **7931 Coyote Springs II** (170 CT + 117 CA = **287.0 MW**, BPAT, same Boardman OR
   site) has **zero CEMS presence anywhere in the committed extracts**, while reporting
   2.26 / 2.33 / 2.16 TWh of EIA-923 net generation.
3. Matching each CEMS unit's gross against each EIA plant's net settles which is which
   unambiguously — the correct pairing gives a physical gross/net ratio in all three years and
   the cross pairing does not:

   | year | CTG1 / plant 7350 | CTG2 / plant 7931 | *(cross)* CTG1 / 7931 | *(cross)* CTG2 / 7350 |
   |---|---:|---:|---:|---:|
   | 2023 | **1.033** | **1.014** | 0.874 | 1.199 |
   | 2024 | **1.020** | **1.015** | 0.895 | 1.156 |
   | 2025 | **1.019** | **1.016** | 0.949 | 1.091 |

   **`CTG2` is EIA plant 7931**, not 7350.
4. The tranche derive reproduces the same defect independently: `thermal_tranches_NWPP.csv`
   reads plant 7350 at **`median_cf` 150.0 %** — the single highest in the file, and the only
   row above 120 %.

**Consequence today:** the standard extract books both units' windows onto plant 7350 (5 + 5
windows, `unit_pct_of_plant` 77.1 % / 22.9 % of a 384.0 MW plant capacity) and gives plant 7931
none, so in the first keeper Coyote Springs II dispatches with **no outage overlay at all**
while Coyote Springs I carries a derate share computed on the wrong denominator.

**ASK:** the repair is one entry in `market_sim.data.campd.CAMPD_UNIT_PLANT_REMAP` —
`(7350, "CTG2"): 7931` — the exact shape of the committed AES Alamitos/Huntington Beach
entries. That is a **`src/` change**, which this lane's charter routes rather than makes
(a derive-script or src-adjacent change is an explicit STOP-and-route). Once landed, this
extract should be re-derived. Filed under rule 14 `[R-ACCURATE]`: the accurate attribution is
available and measured, and burying it is not an option.

### 7.3 Jim Bridger is carried as `ST_GAS`, 1,070 MW, and reads `median_cf` 106.6 %

`thermal_tranches_NWPP.csv` and the layup companion disagree about plant 8066: the tranche row
is `ST_GAS` at 1,070.0 MW, the outage extract's Jim Bridger row is `COAL` at 2,280.0 MW plant
capacity. Units 1-2 converted to natural gas in Jan-2024 and units 3-4 remain coal, so **both
labels are partly right and the plant genuinely spans two model bins mid-span**. The
`median_cf` of 106.6 % on the `ST_GAS` row is the symptom of four units' CEMS gross scored
against a two-unit nameplate. Nothing in W4 reads the tranche file (§0b) so this is not
blocking, but the **fleet-side** bin assignment for a 2,280 MW coal/gas plant **is** read by
the keeper. **ASK:** route to NWPP-33/NWPP-40 as a fleet-classification question; it is outside
this lane's file scope (`src/`, fleet registry) and is reported, not touched.

## 8. Thermal tranches — class summary vs MISO (REPORTED, never tuned)

`derive_thermal_tranches.py --iso NWPP --years 2023 2024 2025`. The three-year span matches the
outage extract's vintage and the training span (rule 16 `[R-ALLYEARS]`), was fixed before the
derive, and could not have been selected against a residual — **there is none, and rule 1
`[R-STRUCT]` forbids consulting one even if there were.** 68 plant-groups written (52 `ok`,
16 `eia923_cf`), 59 skipped for insufficient run-time.

Capacity-weighted, `status=ok` rows only:

| group | n (NWPP/MISO) | MW (NWPP) | committed % NWPP / MISO | mustrun % | mustrun-online % | peaking % |
|---|---|---:|---|---|---|---|
| CC_CHP | 7 / 14 | 1780.2 | 62.1 / 45.3 | 0.0 / 0.0 | 0.0 / 0.0 | 2.6 / 5.0 |
| CC_REGULAR | 22 / 39 | 10533.3 | 40.4 / 42.4 | 0.0 / 0.0 | 0.0 / 0.0 | 7.4 / 4.9 |
| COAL | 12 / 44 | 6958.4 | 39.4 / 40.5 | 30.4 / 28.9 | **33.4 / 27.6** | — |
| CT_PEAKER | 8 / 79 | 1714.3 | 23.2 / 16.1 | 0.0 / 0.0 | 0.0 / 0.0 | — |
| ST_GAS | 3 / 16 | 1533.5 | 18.7 / 20.2 | 0.0 / 0.0 | 0.0 / 0.0 | — |
| CT_CHP | 0 / 5 | — | — / 69.5 | — | — | — |
| ST_CHP | 0 / 2 | — | — / 70.0 | — | — | — |

**Every class with more than a handful of plants lands inside a plausible band of MISO's.**
`CC_REGULAR` committed (40.4 / 42.4), `COAL` committed (39.4 / 40.5), `ST_GAS` (18.7 / 20.2)
and `COAL` all-hours must-run (30.4 / 28.9) are close. Three read apart and **none is touched**:

- `COAL` mustrun-online 33.4 vs 27.6 — a 5.8 pt higher synchronization floor, consistent with a
  PacifiCorp/NV Energy coal fleet run as regulated baseload against MISO's more heavily cycled
  merchant coal.
- `CT_PEAKER` 23.2 vs 16.1 on 8 plants vs 79 — NWPP's eight are large regulated frame units
  (Rathdrum, Evander Andrews, Bennett Mountain) rather than MISO's long tail of small peakers.
- `CC_CHP` 62.1 vs 45.3 on 7 plants — Hermiston and Klamath are steam-host cogen that hold a
  high floor; a seven-plant mean is not a band, and it is listed for completeness.

NWPP has **no `CT_CHP` or `ST_CHP` `ok` row at all**: of the 16 `eia923_cf` rows, 13 are
`CT_CHP` and 2 are `ST_CHP` — every one of them — plus one `CC_CHP` (54349 Nevada Cogen 2).
That is what a fleet of ≤ 26 MW campus/industrial cogen looks like against a run-time floor,
and it is why the MISO `CT_CHP` / `ST_CHP` columns have no NWPP counterpart to compare.

## 9. Steps 3 and 4 — run, and why they commit nothing

- **`scripts/tag_mixed_plants.py`** takes **no `--iso`** and rewrites the ERCOT CAMPD bin sheet
  `data/raw/reference/custom-bin-assignments.csv` in place. That sheet is ERCOT-only (304 rows,
  an `ERCOT_Zone` column) and **the intersection of its `Plant_Code` set with NWPP's 69-plant
  qualifying fleet is EMPTY — measured, zero plants.** NWPP reaches its plant groups through
  the fleet path (`load_fleet_from_csv`), never the bin sheet, and card N8's ruling
  (`use_campd_bins=False`, NWPP absent from `CAMPD_BINNING_ISOS`) is why. **There are no NWPP
  rows to append**, so the charter's "APPEND, never reorder" instruction is satisfied vacuously.
  It was run against **scratch copies** so the committed sheets could not be disturbed — output
  `bins already split — reconciling registry only` / `registry already in sync with bins`, the
  copies came back byte-identical, and both committed sheets verified unchanged by
  `sha256sum -c` (`custom-bin-assignments.csv` `19d726cd…`, `master-plant-registry.csv`
  `49e8d9ee…`).
- **`scripts/data/build_offer_curve_overrides.py`** writes no file — it turns operator tweak
  lines into stdout JSON for `--offer-curve-delta-json`. Run as `--iso NWPP --list`, the
  non-mutating read, and it returns the **load-bearing gate G5 / rule 25 `[R-ISO-SCOPE]`
  result**: every ISO-scoped class NWPP will carry — `CC_CHP`, `CC_REGULAR`, `COAL`,
  `COAL_BIT`, `COAL_LIGNITE`, `COAL_PRB`, `COAL_WC`, `CT_CHP`, `CT_PEAKER`, `ST_GAS` — is
  **1.0 on every band** (`committed` / `econ_low` / `econ_high` / `peak`), and NWPP carries
  **no `phys_*` rows**. The only non-1.0 values are the three generic all-ISO
  `*_INTERMEDIATE` class defaults (`CC_INTERMEDIATE` 0.92/0.95/1.08/2.25, `CT_INTERMEDIATE`
  1.0/1.0/1.2/3.0, `ST_GAS_INTERMEDIATE` 1.0/1.0/1.15/2.2), visibly distinct from ERCOT's
  fitted set (`CT_PEAKER` 1.48/1.27/1.98/**13.15** plus a full `phys_*` set; `CC_REGULAR`
  0.92/1.16/1.41/2.25). **No ERCOT-fitted multiplier leaks into NWPP.** The emitted delta JSON
  is `{}`. This is exactly the posture gate G5 requires and the desk's ruled position: NWPP-40
  declares `authorized_price_tuning: NONE`.

## 10. Gates

| gate | result |
|---|---|
| G4 windows > 0 in every CEMS state, incl. the four NWPP-11 landed | **PASS** — NV 1791, WA 194, WY 84, UT 78, OR 59, MT 37, ID 15; no zero to explain |
| zero full-year fallbacks, else reported by unit with the reason | **12 fallback rows, all reported by unit in §4** with the reason and the 2025-vintage caveat; **zero measured full-year CEMS outages**; no unit fell back for want of data |
| class distributions summarised against MISO as a sanity band | **§8** — reported, never tuned; the three divergences named with a structural reading and left alone |
| every output header cites source + method + CEMS vintage | sidecars (§1) + §2; the CSVs carry the bare MISO-template column header, which rule 23 forbids me altering |
| G5 offer-curve bands stay 1.0 | **PASS** — §9, every ISO-scoped class 1.0 on every band, no `phys_*`, delta JSON `{}` |
| non-NWPP diff = ∅ (gate G9) | `git diff origin/main --name-only` is **seven new NWPP-suffixed files and this doc**; both reference sheets verified byte-identical by `sha256sum -c` |
| no `src/`, no derive-script, no `ScenarioConfig` edit | none — the three things that wanted one are **routed** in §7 |
| rule 28 — no matrix cell moves | no `ScenarioConfig` field, no mechanism, no calibration CLI flag touched; nothing to stamp |
| §8.0 rule 1 — no shared record touched | this lane wrote **one new file** plus its own data outputs; the plan, the ledger, `nwpp.md`, `CHANGELOG.md` and the matrix are untouched |

## 11. Commits

1. `66712d2b` — NWPP-30 step 1: the five outage extracts + their three sidecars
2. `442f2ce4` — NWPP-30 step 2: `thermal_tranches_NWPP.{csv,meta.json}`
3. this FINDING

Steps 3 and 4 of the charter sequence commit nothing, for the reasons in §9.

---

## Log entry (for the desk to append verbatim to `docs/calibration-log/nwpp.md`)

## 2026-09-14 — NWPP-30: unit outage windows + thermal tranches landed (frozen derives)

Lane NWPP-30 `[OPUS]`, branch `claude/nwpp-30-outages-tranches-q7m4`, base `d54cd9c5`.
`docs/handoffs/FINDING-nwpp-30-2026-09-14.md`.

**Coverage, measured now that NWPP-11 has landed** (NWPP-10 §2 item (8) projected it):
CAMPD reaches **30.15 %** of the 98,238.1 MW footprint nameplate (projected 30.98 %,
Part-75 bound 32.63 %) and **40.2 % / 38.6 %** of EIA-923 footprint energy in 2023 / 2024
(proxy bound 43.6 / 41.8 %). The outage overlay this lane landed governs **28.51 %** of
nameplate and **38.9 % / 37.2 %** of energy. The share is low because **34.3 % of the
footprint is conventional hydro** and another 25.9 % is wind + solar — CEMS covers none of it.
CO needs no extract (7.5 MW of hydro); CA is measured **inert** (0.0 MW CEMS-present).

**Six artifacts, five derive invocations, zero script edits** (rule 23 `[R-FROZEN-DERIVE]`;
NWPP has no solve, so no residual could have been consulted):
`campd-unit-outages-NWPP.csv` **2270** rows (`39bb3416…`), `-short-` 209, `-layup-` 17,
`-e923-` 19, `campd-partial-outages-NWPP.csv` 111, `thermal_tranches_NWPP.csv` 68.
The guard-on pass rewrites the default-read extract, so the standard extract was re-derived
guard-off and verified byte-identical to the pre-layup blob.

**Gate G4 PASS** — windows > 0 in every CEMS state in every year, the four NWPP-11 states
included (NV 1791 · WA 194 · WY 84 · UT 78 · OR 59 · MT 37 · ID 15). **Twelve full-year
windows, all `eia923_netzero` structural fallbacks on non-CEMS plants, itemised by unit; zero
measured full-year CEMS outages and no unit fell back for want of data.** Nine of the twelve
sit in 2025, the preliminary EIA-923 vintage NWPP-10 flagged. Of the 69 qualifying fleet
plants, **55 carry a window — 79.7 % by count, 95.2 % by capacity**; all 14 uncovered plants
are absent from the CAMPD panel entirely, twelve of them ≤ 120 MW campus/industrial cogen. The
largest, **8073 Beaver (468.8 MW CC, PGE)**, is blind but **not idle** — 1.69/1.71 TWh of
EIA-923 generation in 2023/24 — so it dispatches in W4 with no availability evidence at all.

**Gate G5 PASS** — every ISO-scoped offer-curve class NWPP carries is **1.0 on every band**,
no `phys_*` rows, delta JSON `{}`; no ERCOT-fitted multiplier leaks in (rule 25
`[R-ISO-SCOPE]`). NWPP-40 declares `authorized_price_tuning: NONE`.

**Card N8 consequence, stated as the charter requires: nothing in W4 reads the thermal
tranches.** `use_campd_bins=False` and NWPP is absent from `CAMPD_BINNING_ISOS`, so the
tranche artifact is landed as the input to the pre-declared **W5 CAMPD-per-plant lever** only.
The outage windows *are* read by the first keeper regardless of binning. Class shares are
reported against MISO as a sanity band and nothing is tuned.

**THREE ITEMS ROUTED TO THE DESK**, each needing a file this lane may not touch:
(1) the merit-order **layup guard is coal-only in NWPP** — `gas_basis_by_iso_month.csv` has no
NWPP row, so all 137 gas units drop from the merit panel and only 33 coal units are priced;
re-derive once **NWPP-33** lands the gas hub. (2) **CEMS ORIS 7350 carries both Coyote Springs
plants** — gross/net matching identifies `CTG2` as EIA plant **7931** in all three years
(1.014/1.015/1.016 vs 1.199/1.156/1.091 for the cross pairing); 7931 has zero CEMS presence
today and 7350 reads a 150 % `median_cf`. Needs one
`campd.CAMPD_UNIT_PLANT_REMAP[(7350, "CTG2")] = 7931` entry — a `src/` change, routed, not
made (rule 14 `[R-ACCURATE]`). (3) **Jim Bridger** (8066) spans `ST_GAS` and `COAL` bins after
its 2024 unit 1-2 gas conversion and reads `median_cf` 106.6 %; the fleet-side classification
of a 2,280 MW plant is read by the keeper and is routed to NWPP-33/NWPP-40.

No shared record touched (§8.0 rule 1); no matrix cell moves (rule 28).
