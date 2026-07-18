# ERCOT endogenous storage energy-vs-AS co-optimization (forward analogue of the measured battery AS-award reservation)

**Date:** 2026-06-27
**Branch:** `claude/ercot-storage-as-endogenous-t6eeyz`
**Status:** lever BUILT, tested, default-off, ERCOT-gated, legacy byte-identical,
pure-LP. Closes G5 of `docs/forecast-methodology-gaps-2026-06.md` (the last
measured input in the ERCOT AS stack: the storage up-AS reservation).
**Reads first:** `docs/forecast-methodology-gaps-2026-06.md` G5,
`docs/ercot-multiproduct-as-coopt-2026-06.md` (run159/163, the co-opt this builds
on), `docs/ercot-reserve-supply-cap-ordc-adder-2026-06.md` (the RTOLCAP cap).

---

## The gap (what was measured)

The ERCOT keeper's storage AS was **read from the measured 60-Day DAM
disclosure**, not chosen. `storage_as_commitment` subtracts the measured hourly
battery AS-award MW (`reserve_storage_as_power`, the `storage` column of
`ercot_<year>_as_by_restype_hourly.parquet`, ~1.25 → 2.0 → 2.8 GW 2023→25) from
the battery dispatch power cap, and `ercot_storage_as_reserve` credits the same
MW back into the co-opt reserve balance. So the model **reads how much AS
batteries cleared** — a measured *outcome* with no forward analogue (a future
year has no 60-Day disclosure), the exact pattern the methodology spec §1.7
flags.

## What this build is

`ScenarioConfig.ercot_storage_as_endogenous` (CLI
`--ercot-storage-as-endogenous`; default off, ERCOT multi-product co-opt only)
makes the battery **choose** energy vs upward-AS inside the LP, replacing the
measured reservation:

1. **Full battery cap to the co-opt.** Under the flag, `run_calibration` does
   **not** call `reserve_storage_as_power` — the full power cap is handed to the
   dispatch. In the multi-product co-opt (`reserve_storage=True`) a storage
   unit's upward-reserve room `cap − discharge + charge` already enters every
   shared-headroom row (`dispatch._build_reserve_rows` `use_storage` block), so
   the battery's discharge (energy/arbitrage) and the cleared reserve `R[p,z]`
   compete for the **same power cap**. The energy-vs-AS split is therefore the
   LP's choice: the battery holds AS only when a product's reserve dual
   (`DispatchResult.reserve_price_by_family`) exceeds its energy-arbitrage
   opportunity cost — the real bid. **No new LP rows** — the storage-reserve
   coupling is the existing vectorized shared-headroom block (no hour loop).
2. **Measured credit guarded off.** `ercot_reserve_coopt_inputs` applies the
   measured storage-AS reserve credit only when `storage_as_commitment` is on
   **and** `ercot_storage_as_endogenous` is off, so the two paths never combine.
   The multi-product input builder never read the measured credit.
3. **Cleared storage AS counts toward RTOLCAP.** Paired with
   `ercot_reserve_supply_cap` (300b89c), the cleared reserve `R` — storage-backed
   and thermal-backed alike — is capped at the measured online-responsive
   capability by the LP cap row. **RTOLCAP already includes online batteries** (it
   grows 13.5 → 16.7 → 19.1 GW in lockstep with the 2023→25 battery fleet, while
   the offline RTOFFCAP holds ~5 GW), so storage's endogenously-cleared AS is
   correctly counted toward the online reserve supply with no augmentation and no
   double count. Under the endogenous flag the cap acts as a **pure reserve-supply
   bound**: the post-solve additive ORDC adder (run161's energy-only-SCED-plus-
   adder construction, `_system_frame`) is **gated OFF** — the multi-product
   co-opt already prices the AS scarcity endogenously through its reserve duals
   and shared headroom, so re-adding the capped reserve dual would DOUBLE-count
   it (the broad-month over-fire run161 documented, sharpest in the low-RTOLCAP
   2023 year that also carries the RTORDPA overlay). This is the same retirement
   the additive adder already takes under RTC+B (the forward co-opt regime). The
   LMP therefore stays the co-opt's own price, so the **acute/tail incidence holds
   vs the uncapped run163** while storage's AS is now bounded by and counted
   toward the measured online reserve supply.

**Forward response.** As the battery fleet grows and AS saturates, each
product's reserve dual falls and the batteries tilt back to energy —
endogenously, no measured award needed (unit-tested:
`test_split_flips_on_the_reserve_price`).

## Honesty gate / validation

The split is the LP's choice; the measured 60-Day DAM award is kept **only** as
the backcast realization to validate against. `run_calibration_full` writes
`storage_as.parquet` (per hour: `modeled_as_mw`, `modeled_discharge_mw`,
`measured_as_mw`) and `scripts/probes/storage_as_split.py` prints the annual
measured-vs-modeled table. `modeled_as_mw` is the **storage-first attribution**
(`dispatch.storage_reserve_mw`): the cleared zone reserve attributed to storage
as `min(storage upward room, total cleared zone reserve)` — exact when storage is
the marginal fast-AS provider (ERCOT batteries are the cheapest, fastest fast-AS,
so they clear first), an upper bound otherwise. Nothing reads the LMP, RTSPP,
MCPC or the measured award on the dispatch path (CLAUDE.md #11/#12).

## Tests (`tests/test_ercot_storage_as_endogenous.py`)

* `test_battery_releases_as_when_arbitrage_wins` / `_holds_as_when_reserve_dual_wins`
  — the trivial 1-storage/1-zone/24h case: with a single peak hour worth ~$180/MWh
  of arbitrage and the battery the sole AS supplier, a cheap AS offer cap ($50)
  makes the battery discharge for energy (holds ~0 AS); a dear cap ($5000) makes
  it hold its power as AS (discharges ~0). The split is the LP's choice.
* `test_split_flips_on_the_reserve_price` — raising *only* the AS offer cap flips
  the battery from all-energy to all-AS (the price, not a tuned level, sets it).
* `TestStorageReserveAttribution` — the storage-first `min` attribution helper.
* `TestWiringByteIdentical` — the endogenous flag suppresses the measured credit.

All 229 dispatch/reserve/scarcity/storage tests pass; the legacy and
NYISO/PJM/MISO paths are byte-identical (every new parameter defaults off).

## Run / dashboard

`scripts/archive/run_164.py` = the run163 recipe (run157 keeper with the DAM-AS overlay
swapped for the endogenous multi-product co-opt + forward AS requirement,
P1-only) **+ `ercot_storage_as_endogenous` + `ercot_reserve_supply_cap`**.
Solved 2023/2024/2025; the acute/tail incidence vs run163 and the
measured-vs-modeled split table are recorded on the backcast dashboard
(bundle `164`).
