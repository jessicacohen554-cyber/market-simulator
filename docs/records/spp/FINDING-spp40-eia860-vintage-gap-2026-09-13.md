# FINDING — SPP-40 holdout shard BLOCKED: the EIA-860 generator parquet carries no SPP rows in 4 of 7 vintages

**Lane:** SPP-40 (holdout shard)
**Date:** 2026-09-13
**Pinned SHA:** `d59422631503cd842108ef97e22acb880f9309e5`
**Status:** STOPPED before any LP. No bundle produced, nothing pushed to `results/`.

## 1. What was asked

Replay SPP keeper 11 (`results/calibration/spp38_span`, years 2023–2025) on held-out
years **2019, 2020, 2021, 2022** — the ISO's first out-of-training coverage.

## 2. Hard stops — both PASSED

| check | required | observed |
|---|---|---|
| `git rev-parse HEAD` | `d5942263…` | **match** |
| `eia860_vintage_tracks_solve_year` | `True` | `True` |
| `unit_outage_short_windows` | `True` | `True` |
| `unit_outage_short_windows_gas` | `False` | `False` |
| `offer_curve_by_group` sha256 | `090abd79…62f65` | **match** |

Note: the mapping has **8 distinct values across 13 groups**, not the "18 distinct
values" the shard prompt's parenthetical asserted. The SHA-256 is the binding check
and it matches exactly, so the recipe is the right one.

## 3. The blocker

The solve died in the **2019 fleet load**, before the LP was ever built:

```
INFO: solving SPP 2019 (hours=8760, Henry Hub=$2.57/MMBtu, commitment=False)
WARNING: EIA-860 parquet has no generators for SPP
FileNotFoundError: No EIA-860 data for SPP: expected a per-ISO override CSV at
  .../data/raw/eia-860/vintage_2019/generators_spp.csv or the generator parquet at
  .../data/raw/eia-860/vintage_2019/eia860_generators.parquet
```

**The error message is misleading.** `eia860_generators.parquet` exists in
`vintage_2019` and is a real 315,803-byte file. `eia860.py:2238` raises
`FileNotFoundError` whenever `_load_fleet_from_parquet` returns `None`, and that
helper returns `None` both when the file is missing **and** when it yields zero
generators for the ISO. Here it is the second case.

## 4. Root cause — SWPP is absent from 4 of 7 committed generator parquets

`_load_fleet_from_parquet` filters rows on
`balancing_authority_code == ISO_TO_BA_CODE["SPP"] == "SWPP"`
(registered by lane SPP-20, 2026-09-06, `zone_assignment.py:80`).

SWPP row counts in `data/raw/eia-860/vintage_<Y>/eia860_generators.parquet`:

| vintage | total rows | **SWPP rows** | distinct BAs | SPP solvable? |
|---|---|---|---|---|
| 2018 | 13,575 | **0** | 6 | no |
| 2019 | 14,043 | **0** | 6 | **no — killed this run** |
| 2020 | 16,082 | 1,527 | 7 | yes |
| 2021 | 15,639 | **0** | 6 | **no** |
| 2022 | 16,232 | **0** | 6 | **no** |
| 2023 | 18,275 | 1,576 | 7 | yes |
| 2024 | 18,943 | 1,626 | 7 | yes |

The vintages that carry SPP are exactly **2020, 2023, 2024** — `nunique_BA = 7`.
The four that do not sit at `nunique_BA = 6`: they were derived **before** SWPP was
registered and were never re-derived.

## 5. The source data is present — this is a stale DERIVED artifact, not a data gap

The raw EIA-860 plant sheet carries SWPP in **every** vintage:

| vintage | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| SWPP plants in `eia860_plant.parquet` | 634 | 654 | 687 | 704 | 724 | 739 | 807 |

So the fix is a **re-derivation** of `eia860_generators.parquet` for vintages
2018 / 2019 / 2021 / 2022 (the BA code is joined from the plant sheet, which already
has it), not a re-fetch from EIA. Candidate owner: `scripts/data/process_eia860.py`.

**This shard did not attempt that** — it is outside a shard's remit (no edits under
`src/` or `scripts/`), and re-deriving a committed input that the keeper's own
2023–2025 years also read is a parent/owner decision, not a shard's.

## 6. Consequences for the SPP holdout ladder

Of the four requested years, only **2020** is solvable at this SHA. A 2020-only
bundle is a one-year solve, which rule 16 `[R-ALLYEARS]` permits solely as a
throwaway diagnostic probe and **never** as a registered run — so solving it alone
would produce something unregistrable. The shard therefore spent no further LP.

## 7. Incidental observation

`results/calibration/_shared/` contains **only `CAISO`**. The shard prompt's push
step (`git add results/calibration/_shared/SPP`) targets a path that does not exist
at this SHA. Whether registration's `bundle_input_path` seam is satisfied for SPP by
some other route is worth the parent confirming before the next SPP shard is
launched, independently of this blocker.

## 8. Container / timing

```
container preflight: memory ceiling 13.34 GiB (MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
container preflight: provisioned 10 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 10.0 = 23.3 GiB
container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: ceiling+swap 23.3 GiB is below the 24 GiB target (per-plant MISO/PJM risk; not binding for 2-zone SPP)
```

No `memory peak:` line — the run died before any solve completed. Wall time to
failure ≈ 3 min, all of it fleet/data loading. Zero LP seconds spent.
