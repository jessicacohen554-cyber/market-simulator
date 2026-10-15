# FINDING — UC-DATA-UT: `uc-params` min-up / min-down on a per-UNIT basis (2026-10-15)

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

* Data-only change; no engine code path changes behaviour, so `UC_ENGINE_VERSION` stays `uc-1.6`.
* `data/clean/uc-params` is gitignored and in no key. The new `SolveEpoch` **2026-10-15a** (with a new
  `requires="unit_commitment_milp"` gate) re-keys exactly the UC-armed configs in CAISO, ERCOT, MISO,
  NEISO, NYISO and SPP. No keeper arms the UC, so no keeper key moves. The key-provenance census
  (`scripts/lib/key_provenance.live_epochs`) applies the same gate.
* No solves ran. No repro shard was launched.
