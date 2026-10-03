# FINDING closeout-nwpp-anchor: the NWPP plant-basis anchor, decoupled from the keeper roster (2026-10-03)

**Charter:** owner ruling R-28 "Keep old figures, fix later" (PR #7076; plan §5.0 R-28, §6.2 NWPP lane;
`RESULT-closeout-b-w0-phase3-2026-10-02.md` §2 ruling 9). Zero LP. Keeper `2026-10-02-w0-nwpp-fix2`
(`results/calibration/w0_nwpp_span`, every leg at `25da6022`).

## 1. The defect, located

`scripts/data/derive_nwpp_plant_basis_energy.py` read `bench.classFull` from the rendered bench parts. The
render builds `classFull` with a plant -> class map taken from the keeper's EIA-860 **fleet**
(`run_calibration_full._fleet_group_by_code` -> `load_fleet_from_csv`). That map drives four places:

1. the CAMPD annual backfill (which plants fire, and into which class);
2. the missing-month repair;
3. the dual-fuel oil re-attribution (a plant absent from the fleet keeps its `oil` MWh);
4. the behind-the-meter CHP subtrahend (`_btm_frame`: only fleet CHP groups carry a host share).

After those, the combined fossil level is reconciled to EIA-930 (`reconcile_vintage_classes`), so a roster
change keeps the fossil total and moves the **COL / NG split** (and the oil share of OTH).

Reproduction (zero LP, `scripts/data` builders at HEAD 792e55ad): the fleet-map sequence reproduces the W0
bench parts (`44ad9f44`, the reverted re-render) **exactly**, every class in every year (max |Δ| 0.0000 TWh).
So the W0 render moved the anchor only through the fleet map.

## 2. The decoupled construction

Same sources and the same benchmark sequence (EIA-923 Page 1 + CAMPD backfill + missing months + EIA-930
renewable repair, minus the bench-basis BTM; VRE on the EIA-930 grid series; combined fossil reconcile to
EIA-930), with one change: the plant -> class map is **roster-free**.

- **Footprint:** the plants EIA-860 BA-codes to NWPP at load time (`_iso_plant_ids`, the E.6 list).
- **Class:** each footprint plant's EIA-923 class (`_classify_f923`: fuel, prime mover, filed CHP flag) with
  the largest net generation in the year. If the plant has none that year, the class comes from the latest of
  the `_CLASS_SHARE_MAX_PRIOR_YEARS` (4) prior years that reports one. These are the same look-back and the same
  crosswalk the benchmark's class shares already use.

The keeper's fleet is never read (the test mocks it to raise). Rule 23 freeze: re-derive only when the EIA-923
vintage, the footprint list or the crosswalk changes.

## 3. Per (year, family): old anchor vs source-based vs W0-rendered (TWh)

"old" is the committed CSV (pre-W0 render, = main's bench parts). "new" is this lane's derive. "W0" is the
reverted W0 render (`44ad9f44`). Wind and solar are identical on all three (the EIA-930 series) and the
consumer skips them. NUC and WAT are identical on all three in every year.

| year | family | old | new (roster-free) | W0 render | new − old | W0 − old |
|---|---|---|---|---|---|---|
| 2019 | COL | 56.4777 | 56.6037 | 56.4319 | +0.1260 | −0.0458 |
| 2019 | NG | 61.4256 | 61.3039 | 61.4714 | −0.1217 | +0.0458 |
| 2019 | OTH | 8.7756 | 8.7713 | 8.7756 | −0.0043 | 0 |
| 2020 | COL | 48.0185 | 48.0348 | 47.9849 | +0.0163 | −0.0336 |
| 2020 | NG | 62.8673 | 62.8562 | 62.9008 | −0.0111 | +0.0335 |
| 2020 | OTH | 8.6453 | 8.6400 | 8.6453 | −0.0053 | 0 |
| 2021 | COL | 47.6581 | 47.6742 | 47.6404 | +0.0161 | −0.0177 |
| 2021 | NG | 66.1873 | 66.1719 | 66.2050 | −0.0154 | +0.0177 |
| 2021 | OTH | 8.8467 | 8.8460 | 8.8467 | −0.0007 | 0 |
| 2022 | COL | 47.3385 | 47.3619 | 47.3267 | +0.0234 | −0.0118 |
| 2022 | NG | 62.0229 | 62.0019 | 62.0349 | −0.0210 | +0.0120 |
| 2022 | OTH | 8.5956 | 8.5932 | 8.5956 | −0.0024 | 0 |
| 2023 | COL | 40.3966 | 40.4156 | 40.3966 | +0.0190 | 0 |
| 2023 | NG | 72.2946 | 72.2780 | 72.2946 | −0.0166 | 0 |
| 2023 | OTH | 8.6897 | 8.6874 | 8.6897 | −0.0023 | 0 |
| 2024 | COL | 34.4366 | 34.4564 | 34.4366 | +0.0198 | 0 |
| 2024 | NG | 77.3796 | 77.3687 | 77.3796 | −0.0109 | 0 |
| 2024 | OTH | 8.1679 | 8.1617 | 8.1679 | −0.0062 | 0 |
| 2025* | COL | 39.8545 | 39.9544 | 39.9380 | +0.0999 | +0.0835 |
| 2025* | NG | 74.1331 | 74.0386 | 74.0497 | −0.0945 | −0.0834 |

\* 2025: a preliminary-vintage year (`frontend/data/backcast/completeness/eia923_2025.json` exists), so only
COL / NG are written. **2025 EIA-923 data drift:** the 2025 bench was re-benched on EIA-923 Final at
closeout-A (`65ada533`). The completeness part still marks 2025 preliminary. That is reported here, not changed.

**Net change of the anchored requirement** (Σ of non-VRE families, new − old): 2019 −0.0000, 2020 −0.0001,
2021 −0.0000, 2022 −0.0000, 2023 +0.0001, 2024 +0.0027, 2025 +0.0054 TWh. The fossil reconcile holds the level,
so the change is a re-split of the same energy between the EIA-930 COL, NG and OTH hourly shapes.

## 4. Pre-fix reading: met

The pre-fixed bar was within 0.5 TWh per family-year wherever the roster did not change, and otherwise a named
membership fact. **No family-year moves by more than 0.5 TWh.** The largest is 2019 COL +0.126. Attribution,
2019, swapping one plant at a time back to its fleet class (COL TWh, base 56.6037):

| plant | fleet class | EIA-923 class | COL with the fleet class | effect |
|---|---|---|---|---|
| 4162 Naughton | ST_GAS | COAL_PRB (2.81 TWh SUB vs 0.03 NG in 2019) | 56.4970 | **−0.107** |
| 3648 Gadsby | CT_PEAKER | ST_GAS | 56.5873 | −0.016 |
| 57653 Oregon State Univ. | CT_CHP | CC_CHP | 56.5974 | −0.006 |
| 58382 / 56163 / 550 / 2336 / 8073 / 7082 | various | various | 56.604–56.612 | ≤ 0.008 each |

Membership fact: the EIA-860 fleet labels **Naughton ST_GAS in 2019** (its current gas-conversion
designation), while EIA-923 reports it burning coal. Under the fleet map its CAMPD / missing-month repair
books under gas. The roster-free map follows what the plant burned. Every other difference is a CHP or
prime-mover labelling difference between the fleet and the plant's own filing, worth ≤ 0.02 TWh.

Four plants are in the fleet map but have no EIA-923 class in the look-back: 63423, 65380, 67766, 69880. All
carry zero CAMPD energy, so dropping them moves nothing.

## 5. Bench parts (C1 scoring) are not changed by this lane

The scored `classFull` still uses the fleet map (`render_calibration_html`, every ISO). The anchor and the
bench now differ by ≤ 0.13 TWh per family-year. That is the same order as the W0 roster shift, and it is
now a fixed fact of the construction rather than something that moves at a promotion. Moving the bench
itself to the roster-free map would be a cross-ISO benchmark change. It is out of scope here and is named
for the desk.

## 6. G-DRIFT vs 25da6022 (rule 29(b))

155 commits. Every hunk on the backcast path is classified below.

| hunk | NWPP |
|---|---|
| `data/raw/reference/nwpp_plant_basis_energy.csv` (this lane) | **LIVE**, all seven years (§3) |
| `scenarios.py` `spp_mmu_offer_repair`, `fleet/arrays.py` MMU pool, `runner.py` / `run_calibration.py` pool append, `models.py` / `export.py` `emergency_band`, `run_calibration_full._model_class_for_unit` | INERT: SPP-gated (`iso == "SPP"`, validator) |
| `solve_surface` epoch 2026-10-02e | INERT: isos=("SPP",) |
| `backcast_config` `caiso_ra_min_load_frac` | INERT: CAISO-scoped (non-CAISO keeps 0.40) |
| `neighbor_price` / `interchange/spec.py` `forward_heat_rate`, FPL `hr_by_year` | INERT: SOCO seams, forecast years only |
| `coal_fuel_inventory.reconcile_floors_to_yard_budget` monthly branch, `run_calibration.py` ceiling-only pile | INERT: ERCOT-only (`COAL_PILE_CEILING_ISOS`). NWPP has the take floor armed, so `_coal_ceiling_pile` is False and the annual reconcile path is unchanged |
| `run_calibration.py` `load_coal_measured_receipts` | INERT: an extraction of the NWPP-NEXT-9 block into a helper, same calls and same return |
| `replay_keeper` / `replay_recipe` (flipped-default overlay, rule-26 tolerance) | INERT: replay tooling. `w0_nwpp_span` records the ten W0 fields, so the overlay pins them to their recorded values |
| `stb_ep724`, `stb-coal-loadings`, CAISO crosswalk CSVs | INERT: intake only / CAISO |

This lane adds SolveEpoch **2026-10-03a** (backcast NWPP), because the anchor CSV is not part of any cache key.
Hence **7 shards** replay `w0_nwpp_span` at this lane's pin (PRECOMMIT).
