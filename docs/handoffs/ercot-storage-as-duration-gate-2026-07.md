# ERCOT storage-AS duration gate (WS-B, G5 follow-up) — 2026-07-05

**Branch:** `claude/ercot-storage-as-duration-bxwr0w`
**Status:** mechanism BUILT, tested, default-off, ERCOT-gated, flag-off byte-identical,
pure-LP (vectorized, no hour loop). Closes WS-B of
`docs/handoffs/ercot-as-coopt-plan-2026-07.md` and ercot32 **root cause (1)**.
**Reads first:** `docs/handoffs/ercot-as-coopt-plan-2026-07.md` WS-B,
`docs/ercot-storage-as-endogenous-2026-06.md` (G5/run164), the 2026-07-03
ercot32 calibration-log entry (root causes 1 and 2).

---

## The gap (ercot32 root cause 1)

The endogenous storage split (`ercot_storage_as_endogenous`, run164) let a battery
CHOOSE energy vs upward-AS inside the multi-product co-opt, but **nothing stopped a
short-duration battery from selling a long-duration product on its full power**. ERCOT
requires an ESR to hold enough state of charge to sustain each cleared AS award for its
full deployment duration — ECRS 2 h and Non-Spin 4 h sustained (RegUp/RRS 1 h). Absent
that energy limit, the split held **2.1–2.4× the measured 60-Day DAM battery award**
(2023: 2,625 vs 1,249 MW mean; 2024 pooled attribution 1.97×).

## What this build is

`ScenarioConfig.ercot_storage_as_duration_gate` (CLI
`--ercot-storage-as-duration-gate`; default off, requires `ercot_storage_as_endogenous`)
adds the published per-product SOC durations as an **LP-linear, vectorized duration
gate** linking cleared storage AS to state of charge.

### The mechanism (dispatch.`_build_reserve_rows`)

Under the pre-gate endogenous split, storage's upward-reserve room
(`cap − Dis + Chg`) is **pooled** into the thermal shared-headroom rows, so the cleared
per-zone reserve `R[c,z]` is a single value backed by thermal *and* storage — there is no
storage-specific reserve variable to bound by energy. The gate makes storage's AS an
**explicit decision variable**:

1. **New columns `RS[c,z]`** — one per reserve class (AS product) `c` and zone `z`,
   appended after the ORDC block (`layout._storage_reserve_off`; `n_storage_reserve =
   n_reserve_classes × n_zones`, 0 and byte-identical when the gate is off).
2. **Storage leaves the thermal headroom.** With the gate on, storage's `Dis/Chg` terms
   and power cap are removed from the thermal shared-headroom rows (else its power would
   be double-counted), so those rows now bound thermal `R[c,z]` alone.
3. **Power-competition row** (per zone-hour): `Σ_c RS[c,z] + Σ_{s∈z}(Dis[s] − Chg[s]) ≤
   Σ_{s∈z} cap[s]` — the same power split that was implicit in the shared headroom, now
   explicit for storage's own reserve.
4. **Duration gate** (per zone-hour): `Σ_c dur_c · RS[c,z] − Σ_{s∈z} SOC[s] ≤ 0`
   (durations = `ERCOT_AS_PRODUCT_DURATION_H`). A 1-h battery (SOC ≤ power×1 h) can hold
   its full power as RegUp/RRS but at most a quarter as 4-h Non-Spin. Gates on the
   same-hour `SOC[t]` — exact for **held** (undeployed) reserve, since the power row keeps
   that MW from also discharging, so the SOC is not drawn down.
5. **Balance + supply cap.** `RS[c,z]` joins the reserve-balance rows alongside thermal
   `R[c,z]` (the all-class ORDC total family sums every product's `RS`), and joins the
   **RTOLCAP supply-cap** rows — cleared storage AS still counts under the measured
   online-responsive capability (RTOLCAP includes online batteries).

Both new row families are per-zone-hour and built with `sp.kron` over hours (no hour loop,
CLAUDE.md #2). The attribution becomes **exact** (`DispatchResult.storage_reserve_dispatch`
= `Σ_c RS[c,z]`), replacing the storage-first `min()` upper bound the pooled split used.

### Durations (`config/reserve_config.py`, index-aligned with `ERCOT_AS_PRODUCTS`)

| Product | Duration | Source |
|---|---|---|
| RegUp | 1 h | ERCOT ESR SOC rule |
| RRS | 1 h | ERCOT ESR SOC rule |
| ECRS | 2 h | ERCOT ESR SOC rule |
| Non-Spin | 4 h | ERCOT ESR SOC rule |

`ERCOT_AS_PRODUCT_DURATION_H = (1.0, 1.0, 2.0, 4.0)`. Source: ERCOT Nodal Protocols
**§3.17.3** (State of Charge Requirements for Energy Storage Resources) and **§8.1** (AS
definitions); ESR SOC methodology (Business Practice Manual, Dec 2022; ERCOT Ancillary
Services Study Final White Paper, Sept 2024). **Published deployment durations, not
fitted.** Cited in `docs/parameter-citations.md`
(`scenario.ercot_storage_as_duration_gate`).

## Why no ε on the RS columns

The storage-reserve columns carry **no direct cost**, exactly like the thermal reserve
`R[c,z]`. An early build put the storage tiebreaker ε (rule #9) on `RS`; because thermal
reserve is zero-cost, that ε made idle thermal headroom **strictly undercut** storage
wherever it was available, collapsing the split to ~0.01× (the opposite failure). Storage
and thermal reserve must compete on true opportunity cost alone (storage's = forgone
arbitrage via the power row + the SOC gate; thermal's = forgone energy via the headroom).
Storage's own power degeneracy is already broken by the Chg/Dis ε.

## Validation (quantity, never price — CLAUDE.md #12)

`scripts/probes/storage_as_split.py` prints modeled (`storage_reserve_dispatch`, now
exact) vs measured 60-Day DAM award, per year; target 0.8–1.3×.

| Run | 2024 storage AS split (mod/meas) |
|---|---|
| run164 (endogenous, **pooled**, no gate) | **1.97×** (over-hold, ercot32 rc1) |
| ε-on-RS probe (rejected — thermal undercuts) | 0.01× |
| **run166 (endogenous + duration gate)** | **0.55×** |

The gate cuts the over-hold decisively (1.97× → 0.55×). The 2024 residual lands just
**below** the target band: with idle thermal reserve free in loose hours, the endogenous
LP gives storage its tight-hour share, netting 0.55× rather than the measured 1.0×. Per
CLAUDE.md #1 the structurally-faithful mechanism (published durations, LP-linear SOC gate)
is kept as-is; the under-provision is a **documented residual**, not closed by tuning.
Full 2023–2025 split table is on the dashboard (bundle `166`).

## Tests (`tests/test_ercot_storage_as_duration_gate.py`)

* `test_one_hour_battery_gated_at_four_hour_product` — the trivial 24-h case: a 1-h
  battery offered a 4-h product holds ≤ SOC/4 = ¼ of its power as that AS.
* `test_one_hour_battery_ungated_by_one_hour_product` / `test_gate_monotonic_in_duration`
  — held AS follows SOC/duration (1 h ≈ 20, 2 h ≈ 10, 4 h ≈ 5 MW), an LP outcome.
* `test_gate_off_emits_no_duration_kwarg` / `test_gate_on_emits_published_durations` /
  `test_lp_byte_identical_when_durations_none` — flag-off byte-identical.
* `test_storage_as_bounded_by_supply_cap` — cleared storage AS counts under, and is
  bounded by, the RTOLCAP supply cap.

All 324 dispatch/reserve/scarcity/storage tests pass; every non-ERCOT path is
byte-identical (`n_storage_reserve = 0` when the flag is off).

## Run / dashboard

`scripts/run_166.py` = the run164 recipe (run157 keeper, DAM-AS overlay off, endogenous
multi-product co-opt + forward requirement + RTOLCAP cap, P1-only) **+
`ercot_storage_as_duration_gate`** as the one consistent delta (measured
`storage_as_commitment` / `ercot_storage_as_reserve` / `ercot_storage_as_product_credit`
all off — the endogenous split forces them off; never mixed, per the ercot30 blow-up).
`--year 2023 2024 2025`, one bundle `166`.

## Open follow-ups

1. The 2024 under-provision (0.55×): the endogenous LP has no reason to prefer storage over
   free idle-thermal reserve in loose hours. A physically-grounded fast-AS preference (the
   real reason batteries win ERCOT AS) would need a **grounded** cost separation, not a
   tuned adder — an open root-cause item, not a knob.
2. Stage-4 integration (`ercot40`): fold the gate into the overlay-replacement run and
   score C1–C5 / G-1…G-7 against the stage-0 ex-overlay baseline.
