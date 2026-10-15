# FINDING — UC-DATA-UT: `uc-params` min-up / min-down / `mlf` on a per-UNIT basis (2026-10-15)

Lane UC-DATA-UT (Opus), chartered by UC-DESK r13. Zero LP. Owner ruling r13 (2026-10-15, rule 23):
`ut_h` is re-derived from per-unit CAMPD on-runs. Defect: `FINDING-ucmilp-diag-undercommit-2026-10-14` cause 3.

## 1. Defect and fix

| | before | after |
|---|---|---|
| series | plant sum of the family's units; "on" while ANY unit is on | each unit `(facilityId, unitId)` on its own |
| online test | `load >= max(1 MW, 0.05 x plant HSL)` | `load >= max(1 MW, 0.05 x unit HSL)` |
| reporting holes | bridged (missing hours dropped, neighbours joined) | series cut at every unreported hour |
| statistic | p25 of plant runs / gaps | p25 of per-unit runs / gaps pooled over the cluster (**unchanged statistic**) |
| `n_runs` | plant runs | per-unit runs, summed |

`u` counts units, so its min-up must be a unit's. A plant-mask run lasts while any unit runs (an economic
run length) and has no cap: multi-unit plants read up to 26 304 h (the whole 2023–25 span).

**`dt_h`: the same defect was present and is fixed the same way.** It has no solve effect: the engine
reads the published class min-down (`model/uc/params.py`, `src_utdt = "uc-params(ut)/class-table(dt)"`);
`uc-params.dt_h` is a diagnostic column.

The plant mask also had a second artifact: its threshold scales with PLANT HSL, so one unit ramping
alone read "off" and split runs short (CAISO plant 315 ST_GAS: 26 plant runs ≤ 3 h vs 2 per-unit runs;
p25 3 h → 25 h). That is why some class medians RISE.

## 2. Old → new, by ISO × class (plant rows; weights = HSL; p50 / p90 in hours)

| ISO | class | plants | GW | ut_h p50 | ut_h p90 | dt_h p50 | dt_h p90 | max new ut_h |
|---|---|---|---|---|---|---|---|---|
| CAISO | cc | 57 | 24.2 | 14 → **14** | 18 → **17** | 5 → 6 | 13 → 13 | 549 |
| CAISO | coal | 2 | 0.6 | 16 → **85** | 491 → **491** | 2 → 2 | 7 → 7 | 491 |
| CAISO | ct | 71 | 8.3 | 3 → **3** | 6 → **5** | 12 → 15 | 17 → 19 | 42 |
| CAISO | st_gas | 12 | 3.4 | 6 → **19** | 19 → **32** | 12 → 52 | 81 → 123 | 102 |
| ERCOT | cc | 60 | 44.3 | 18 → **15** | 6854 → **73** | 8 → 8 | 24 → 13 | 596 |
| ERCOT | coal | 14 | 18.1 | 465 → **84** | 12018 → **177** | 18 → 15 | 292 → 26 | 665 |
| ERCOT | ct | 47 | 10.9 | 4 → **4** | 358 → **13** | 9 → 12 | 16 → 17 | 31 |
| ERCOT | st_gas | 32 | 15.8 | 7 → **12** | 60 → **66** | 12 → 14 | 46 → 57 | 380 |
| MISO | cc | 141 | 95.7 | 18 → **17** | 3240 → **118** | 8 → 7 | 27 → 16 | 1385 |
| MISO | coal | 86 | 91.3 | 359 → **102** | 26304 → **295** | 20 → 26 | 139 → 79 | 885 |
| MISO | ct | 195 | 43.4 | 7 → **7** | 12 → **11** | 10 → 12 | 16 → 17 | 624 |
| MISO | st_gas | 65 | 29.3 | 30 → **34** | 115 → **81** | 14 → 31 | 82 → 75 | 1167 |
| NEISO | cc | 33 | 13.4 | 17 → **14** | 88 → **60** | 6 → 6 | 162 → 193 | 91 |
| NEISO | coal | 1 | 0.4 | 50 → **29** | 50 → **29** | 171 → 178 | 171 → 178 | 29 |
| NEISO | ct | 26 | 1.8 | 2 → **2** | 6 → **6** | 10 → 10 | 20 → 62 | 8 |
| NEISO | st_gas | 10 | 2.5 | 19 → **20** | 31 → **24** | 30 → 30 | 112 → 129 | 327 |
| NYISO | cc | 53 | 19.5 | 15 → **13** | 358 → **22** | 8 → 6 | 18 → 11 | 673 |
| NYISO | ct | 44 | 4.5 | 2 → **3** | 5 → **5** | 10 → 10 | 16 → 20 | 36 |
| NYISO | st_gas | 11 | 8.7 | 18 → **20** | 94 → **46** | 22 → 56 | 52 → 67 | 209 |
| SPP | cc | 122 | 77.1 | 18 → **16** | 3792 → **83** | 8 → 8 | 27 → 16 | 1385 |
| SPP | coal | 72 | 67.2 | 217 → **84** | 11494 → **206** | 23 → 24 | 98 → 55 | 665 |
| SPP | ct | 162 | 28.5 | 6 → **6** | 11 → **10** | 11 → 12 | 16 → 17 | 31 |
| SPP | st_gas | 73 | 29.5 | 30 → **36** | 120 → **114** | 16 → 34 | 54 → 64 | 1167 |

Derive-row medians, not the fleet-matched cluster medians of the 10-14 FINDING (which read e.g. SPP CC 18,
ST_GAS 55, coal 57). 195 of 1 389 plant rows rise; the rest fall or hold.

## 3. Outliers against a published bound (reported, NOT clipped)

Bound = the repo's published class min-run table, the values the engine uses where no plant row exists:
`COMMITMENT_PARAMS_BY_FUEL` (CC ≤ 10 h, CT 1 h, gas steam ≤ 48 h) and `COAL_BIN_MIN_RUN_HOURS` = 36 h,
both cited in-repo to NREL/SR-5500-55433 (Kumar et al. 2012) plus OEM specs. Caveat: that report is a
cycling-cost study. The min-run attribution is the repo's own; an independent published min-up table
was not found in this session.

| ISO | CC rows > 10 h (GW) | coal > 36 h | ST_GAS > 48 h | CT > 1 h |
|---|---|---|---|---|
| CAISO | 32 (16.9) | 2 (0.6) | 1 (0.0) | 68 (8.2) |
| ERCOT | 46 (36.6) | 14 (18.1) | 9 (3.4) | 47 (10.9) |
| MISO | 114 (83.5) | 79 (86.5) | 22 (9.7) | 191 (43.2) |
| NEISO | 22 (10.6) | 0 | 2 (0.1) | 23 (1.7) |
| NYISO | 29 (14.8) | — | 2 (0.5) | 38 (4.3) |
| SPP | 95 (66.4) | 64 (61.2) | 30 (12.3) | 158 (28.4) |

Largest non-CT values: CC 55089 (3 units) 1 385 h; ST_GAS 1391 1 167 h; coal 1379 885 h; CC 55259 881 h;
NYISO CC 56234 673 h (1 unit, 16 runs in 3 years). 68 of the 563 non-CT outliers rest on fewer than 30
runs. Full list: lane scratch `outliers.csv` (regenerable from `compare.py` over two `derive_iso` runs).

## 4. What this does and does not fix

* **Fixed:** the tail. p90 falls from thousands of hours to 13–295 h; ERCOT/MISO/SPP coal medians
  fall from 217–465 h to 84–102 h.
* **Not fixed: CC medians barely move** (13–17 h, against a published ≤ 10 h). CCs two-shift on daily
  ~14–18 h economic runs. p25 of observed **unit** runs is still how long a unit chose to run, an upper
  bound on min-up, not the min-up. The start-ratio deficit (CC starts 0.46–0.89× CEMS) is unlikely to close
  from this change alone.
* **PRECOMMIT item for the desk, not decided here:** change the statistic (for example, the minimum or
  p5 of unit runs, with a sample floor), or use the published class min-up with p25 as a diagnostic upper
  bound (the 10-14 FINDING's alternative). Either one is a rule-23 derivation change that needs an owner
  ruling.

## 5. Cache key, engine version

* Data-only change (`ut_h` and `mlf` both reach a UC solve); no engine code path changes behaviour,
  so `UC_ENGINE_VERSION` stays `uc-1.6`.
* `data/clean/uc-params` is gitignored and in no key. The new `SolveEpoch` **2026-10-15a** (with a new
  `requires="unit_commitment_milp"` gate) re-keys exactly the UC-armed configs in CAISO, ERCOT, MISO,
  NEISO, NYISO and SPP. No keeper arms the UC, so no keeper key moves. The key-provenance census
  (`scripts/lib/key_provenance.live_epochs`) applies the same gate.
* No solves ran. No repro shard was launched.

## 6. `mlf` per unit (scope extension)

**Same derivation path as `ut_h`** (`_plant_stats` in `scripts/lib/uc_params/__init__.py`). #7262
merged the `ut_h` change before this one landed, so `mlf` ships in its own PR under its own epoch,
**2026-10-15b**, with the same `requires="unit_commitment_milp"` gate. 15a is not edited (rule 26).

**Defect.** `mlf` was `p5(summed plant load over online plant-hours) / plant HSL`. The UC applies it per
committed unit (`mlf · p̄ · a · u`; `pipeline/uc.py`, `model/uc/window.py`, `model/uc/schedule.py`).
A multi-unit plant reaches its p5 with one unit of n at minimum, so the ratio read about 1/n of a unit's
minimum stable fraction.

**Fix (owner ruling 2026-10-15 on the statistic).** `mlf = Σ unit LSL / Σ unit HSL`, where
- unit LSL = p5 of the unit's own load over its **FULL operating hours** (CEMS `opTime == 1` and online,
  load ≥ max(1 MW, 0.05 × unit HSL)), so start-up and shut-down partial hours never set the minimum
  (`FULL_HOUR_OPTIME = 1.0`);
- unit HSL = p99.5 of its series;
- `lsl_mw = mlf × hsl_mw`.

**The one fallback, stated:** a unit with **no** full online hour in 2023–25 takes p5 over all its online
hours. There is no minimum-sample floor; counts are below.

**Check that the fix touches the defect.** On multi-unit plants the median new/old ratio is **2.08**.
On single-unit plants it is **1.08**: that 8 % is the full-hour restriction alone, since the plant basis
equals the unit basis for one unit. MISO ST_GAS goes 0.141 → **0.266** (HSL-weighted mean), inside the
0.20–0.30 that #7259 measured.

The table runs old (plant basis) → **new (unit basis, full hours)**. The parenthesised p50 is the interim
unit-basis, all-online-hours value this PR first carried. HSL-weighted. The reference is
`MIN_STABLE_PCT_PHYSICAL`, the engine's fallback (WWSIS-2, as cited in `constants.py`).

| ISO | class | WWSIS-2 | mlf p10 | mlf p50 (online-hours basis) | mlf p90 | GW below WWSIS-2 (old→new) | GW above |
|---|---|---|---|---|---|---|---|
| CAISO | cc | 0.52 | 0.11 → **0.40** | 0.26 → **0.55** (0.39) | 0.38 → **0.68** | 23.8 → 10.5 | 0.3 → 13.7 |
| CAISO | coal | 0.40 | 0.16 → **0.30** | 0.16 → **0.30** (0.30) | 0.41 → **0.41** | 0.4 → 0.4 | 0.2 → 0.2 |
| CAISO | ct | 0.38 | 0.07 → **0.36** | 0.14 → **0.54** (0.28) | 0.33 → **0.80** | 8.0 → 0.9 | 0.4 → 7.5 |
| CAISO | st_gas | 0.12 | 0.05 → **0.09** | 0.07 → **0.20** (0.20) | 0.25 → **0.42** | 2.4 → 0.8 | 1.0 → 2.5 |
| ERCOT | cc | 0.52 | 0.20 → **0.38** | 0.31 → **0.53** (0.51) | 0.44 → **0.66** | 41.1 → 20.0 | 3.2 → 24.3 |
| ERCOT | coal | 0.40 | 0.10 → **0.30** | 0.19 → **0.34** (0.34) | 0.45 → **0.51** | 13.9 → 13.9 | 4.2 → 4.2 |
| ERCOT | ct | 0.38 | 0.09 → **0.46** | 0.15 → **0.74** (0.45) | 0.53 → **0.85** | 9.0 → 0.8 | 1.9 → 10.1 |
| ERCOT | st_gas | 0.12 | 0.06 → **0.14** | 0.09 → **0.20** (0.19) | 0.20 → **0.30** | 12.4 → 0.0 | 3.4 → 15.8 |
| MISO | cc | 0.52 | 0.22 → **0.44** | 0.32 → **0.59** (0.56) | 0.56 → **0.75** | 81.5 → 28.4 | 14.2 → 67.4 |
| MISO | coal | 0.40 | 0.14 → **0.30** | 0.22 → **0.41** (0.41) | 0.45 → **0.56** | 79.0 → 43.0 | 12.3 → 48.3 |
| MISO | ct | 0.38 | 0.08 → **0.46** | 0.15 → **0.67** (0.33) | 0.33 → **0.85** | 40.3 → 3.4 | 3.1 → 40.0 |
| MISO | st_gas | 0.12 | 0.06 → **0.14** | 0.10 → **0.23** (0.23) | 0.30 → **0.44** | 17.7 → 1.4 | 11.6 → 27.9 |
| NEISO | cc | 0.52 | 0.22 → **0.48** | 0.34 → **0.56** (0.51) | 0.51 → **0.69** | 12.6 → 5.3 | 0.8 → 8.1 |
| NEISO | coal | 0.40 | 0.22 → **0.48** | 0.22 → **0.48** (0.46) | 0.22 → **0.48** | 0.4 → 0.0 | 0.0 → 0.4 |
| NEISO | ct | 0.38 | 0.09 → **0.26** | 0.22 → **0.70** (0.34) | 0.42 → **0.94** | 1.6 → 0.6 | 0.2 → 1.1 |
| NEISO | st_gas | 0.12 | 0.07 → **0.14** | 0.18 → **0.30** (0.25) | 0.30 → **0.52** | 0.6 → 0.1 | 1.9 → 2.4 |
| NYISO | cc | 0.52 | 0.13 → **0.43** | 0.25 → **0.54** (0.50) | 0.49 → **0.71** | 18.6 → 8.3 | 0.9 → 11.2 |
| NYISO | ct | 0.38 | 0.08 → **0.33** | 0.13 → **0.79** (0.33) | 0.38 → **0.94** | 4.1 → 0.5 | 0.4 → 4.1 |
| NYISO | st_gas | 0.12 | 0.06 → **0.19** | 0.11 → **0.24** (0.22) | 0.14 → **0.30** | 6.5 → 0.0 | 2.2 → 8.7 |
| SPP | cc | 0.52 | 0.20 → **0.38** | 0.30 → **0.54** (0.52) | 0.53 → **0.70** | 68.6 → 28.9 | 8.5 → 48.2 |
| SPP | coal | 0.40 | 0.13 → **0.29** | 0.20 → **0.37** (0.36) | 0.45 → **0.55** | 56.8 → 39.3 | 10.4 → 27.9 |
| SPP | ct | 0.38 | 0.08 → **0.35** | 0.15 → **0.65** (0.34) | 0.36 → **0.83** | 25.8 → 3.5 | 2.7 → 25.1 |
| SPP | st_gas | 0.12 | 0.06 → **0.14** | 0.09 → **0.23** (0.23) | 0.31 → **0.43** | 18.1 → 0.5 | 11.4 → 29.0 |

**Outliers, reported and NOT clipped.** WWSIS-2 gives one typical value per class, not a band, so I
invented no tolerance around it. The "GW above / below" columns are the flag.
- **CT is the large mover:** p50 0.65–0.79, p90 up to 0.94, against WWSIS-2's 0.38. A CT's full hours
  are dispatched near its maximum, so its full-hour p5 is how it chose to run, not its physical minimum.
  **This has no effect on a UC solve:** CT clusters fail the E1 integer gate (class min-down 1 h, start
  cost < $30/MW; `integer_gate`), and the `mlf` floor applies only to integer clusters. The CT rows are
  diagnostic.
- Rows ≥ 0.90: 63 of 1 389, mostly CT. Non-CT examples: CAISO CC 54271 (2 units, 93 MW) 0.51 → 0.92; CC
  6358 (42 MW) 0.93; SPP ST_GAS 7013 and 1271 (16–18 MW) 0.94.
- Rows < 0.05: 8 of 1 389. Lowest non-CT: MISO ST_GAS 6035 at 0.066 (single unit, unchanged).
- Integer classes against WWSIS-2:
  - CC p50 0.53–0.59 vs 0.52;
  - coal p50 0.30–0.48 vs 0.40;
  - ST_GAS p50 0.20–0.30 vs 0.12, about 2× in every ISO and consistent with #7259.

**Fallback and sample counts (units with 0 / < 20 / < 200 full online hours):**

| ISO | units (cc / coal / ct / st_gas) | 0 full hours (fallback) | < 20 | < 200 | p10 full hours, integer classes (cc / coal / st_gas) |
|---|---|---|---|---|---|
| CAISO | 118 / 3 / 164 / 21 | **0** | 0 | 15 (14 CT, 1 CC) | 2 215 / 21 267 / 477 |
| ERCOT | 166 / 29 / 172 / 77 | **0** | 0 | 2 (ST_GAS) | 8 243 / 13 677 / 695 |
| MISO | 365 / 184 / 628 / 133 | **0** | 0 | 13 (10 CT, 3 ST_GAS) | 11 552 / 7 148 / 710 |
| NEISO | 61 / 2 / 53 / 15 | **0** | 1 (CT) | 32 (31 CT, 1 CC) | 1 457 / 613 / 391 |
| NYISO | 104 / – / 143 / 28 | **0** | 0 | 30 (27 CT, 2 CC, 1 ST_GAS) | 1 039 / – / 368 |
| SPP | 310 / 125 / 474 / 156 | **0** | 0 | 13 (9 CT, 4 ST_GAS) | 7 842 / 9 439 / 675 |

**No unit in any ISO takes the fallback.** One unit has fewer than 20 full hours (a NEISO CT, which is
non-integer). The integer classes have fewer than 200 full hours in at most 4 units per ISO.

## 7. Registered min-run / min-up in on-disk ISO offer disclosures (zero LP, no fetch)

Asked by UC-DESK before it puts the statistic question to the owner: does a **registered** physical
duration exist on disk? One would beat both the p25 and the class table (rules 14, 18).

**Answer: none on disk. The only ISO feed that publishes one (PJM `min_runtime`) is gitignored; only
its README is present.**

| ISO | corpus | registered duration field | on disk | unit → EIA plant |
|---|---|---|---|---|
| PJM | `data/raw/pjm-energy-offers/` | **`min_runtime`** → `min_runtime_h` ("Minimum continuous runtime (hours) once the unit is committed", `energy-offers.schema.yaml`); also `max_daily_starts` | README only (gitignored; re-fetchable, 2019–25) | masked `unit_code`, no crosswalk |
| MISO | `data/raw/miso-energy-offers/` | none (Economic / Emergency Min are **MW**) | README only | masked; class bridge refuted (miso-138) |
| NYISO | `data/raw/nyiso-bid-data/genbids/` | none (Fixed Min Gen MW) | `SHA256SUMS.txt` only | no published crosswalk |
| ISO-NE | `data/raw/NEISO-AS/da-energy-offers/` | none (Economic Min MW) | README only | masked |
| CAISO | `data/raw/caiso-public-bids/` | none | README only | masked |
| ERCOT | 60-day DAM Gen Resource Data; SCED extracts | **none**. DAM has `LSL`, start-up offers and `Min Gen Cost`; SCED has HSL/LSL/HDL/LDL | yes | resource names unmasked (network-model map exists) |
| SPP | — | no offer corpus | — | — |

Notes:
- Coverage by class is **zero in every ISO × class on disk**.
- PJM `min_runtime` is used today only as a CT ≤ 2 h / CC (2, 16] h / LONG_RUN > 16 h class splitter
  (`derive_pjm_offer_surface.py`, `derive_pjm_offer_midcurve.py`). PJM is not a UC ISO.
- Masked unit codes would need a mapping to plants before the field could feed `uc-params`.
- No existing min-run input comes from an ISO offer file:
  - ERCOT `custom-bin-assignments.csv` (`Min_Run_Hours`) is hand-authored.
  - `derive_campd_perplant_min_run.py` and `uc-params` are observed-run p25s.
  - The coal 36/16 h defaults are the NREL SR-5500-55433 attribution.
- The ERCOT DAM `LSL` is an offered or telemetered **MW** limit. It could serve as a measured check on
  the per-unit `mlf` in ERCOT (a later card, not done here).

Survey method: corpus READMEs plus a schema-only read of the ERCOT parquet headers; no payload was
loaded and nothing was fetched.
