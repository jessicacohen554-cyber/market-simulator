# Storage AS-Power Withholding — Mechanism Attribution (2026-07)

Attribution map for the *forecast-mode storage AS power withholding* workstream
(CLAUDE.md rule 19 — one mechanism per phenomenon: enumerate what already
withholds/prices the same duty **before** adding anything). Follow-up to
`docs/storage-modeling-audit-2026-07.md` §1.3. Written before any code change.

**Phenomenon:** ERCOT batteries clear most of their value as ancillary services
(AS); power committed to upward AS cannot also arbitrage energy. Two things must
happen for this to be modeled faithfully: (i) the AS-committed power is
*withheld* from energy in the hours it is held, and (ii) the AS duty is *priced*
(the battery earns the AS clearing value, and its entry economics see it exactly
once).

## Mechanism inventory, per mode

| # | Mechanism | Where | Withholds? | Prices? | Mode | Forward-regenerable? |
|---|---|---|---|---|---|---|
| M1 | `reserve_storage_as_power` — subtract **measured** hourly storage up-AS MW from the storage power cap | `model/storage.py:482`, applied only in `scripts/run_calibration.py:4193` | yes (hard cap cut) | no (energy-only LP) | **backcast** | no — reads `ercot_<year>_as_by_restype_hourly.parquet` (measured award) |
| M2 | `ercot_storage_as_reserve` / `ercot_storage_as_product_credit` — net the **measured** battery award off the AS *requirement* so the co-opt doesn't pull it from thermal | `config/reserve_config.py:422-430, 615-660, 730-737` | n/a (requirement netting) | via co-opt duals | **backcast** | no — same measured series |
| M3 | **Endogenous reserve co-opt with storage participation** — storage headroom `cap − Dis + Chg` backs upward reserve on a shared per-zone pool; the LP chooses energy-vs-AS on the same power cap, priced by the AS demand curves | dispatch `_build_reserve_rows` `use_storage` block `model/dispatch.py:893-996`; design `storage_eligible=True` `reserve_config.py:447, 752` → `reserve_storage=True` `reserve_config.py:328` → `reserve_storage_power_cap=storage_power_cap` `dispatch.py:2217` | **yes (endogenous)** | **yes (LP duals)** | **both** | **yes** — requirement from forward drivers (see M4) |
| M4 | AS **requirement** setting | `results/scarcity.py` | — | — | both | `ercot_as_forward_requirement=True` → **forward** (load/wind/solar formulas, `scarcity.py:943-1063`, constants `reserve_config.py:44-69`); **False → measured plan** `ASPLANNP433_<year>.parquet`, and **returns all-zero for a year with no file** (`scarcity.py:915-916`) |
| M5 | `as_revenue_per_mw_yr` — **exogenous** calibrated $/kW-yr AS credit with penetration saturation, added to entry/retirement screens | `model/ancillary.py:50`; storage entry `model/storage.py:966,972`; thermal retire `capacity.py:527`; thermal entry `capacity.py:1221` | no | **yes (separately, off the LP)** | both (gated `as_revenue_enabled`, ERCOT) | yes (saturation on fleet MW) — but it is a *parallel* pricing, not the co-opt's |

## What actually happens today

**Backcast (`scripts/run_calibration.py`).** M1 (or M2) reserves the *measured*
battery award; M3 runs when `energy_reserve_coopt` is on; `ercot_storage_as_endogenous`
switches M1/M2 **off** and hands the full cap to M3 (`run_calibration.py:4188-4190`,
`reserve_config.py:425/618/733`). Rule-13-admissible measured input; backcast only.

**Forecast (`src/market_sim/runner.py`).**
- `dispatch_kwargs` **always** carries `storage_power_cap`/`storage_zone_idx`
  (`runner.py:763-765`), and the reserve co-opt (M3) is merged whenever
  `energy_reserve_coopt` is on and `iso != CAISO` (`runner.py:802-818`). So **the
  endogenous energy-vs-AS withholding is already reachable in forecast** — it is
  an emergent property of the co-opt, not of a dedicated flag.
- The measured overlays (M1/M2) are **never applied in forecast** — `runner.py`
  has no reference to `reserve_storage_as_power`, `storage_as_commitment`,
  `ercot_storage_as_reserve`, or `ercot_storage_as_endogenous`. Correct per rule 13.
- **`ercot_storage_as_endogenous` is a no-op in forecast.** Its only effect is to
  negate the third operand of `storage_as_commitment AND … AND not endogenous`
  gates that forecast never reaches (`storage_as_commitment` is False). The flag
  is *semantically* "storage prices AS endogenously" but drives nothing forward.
- **Two latent forecast footguns:**
  1. Enabling `energy_reserve_coopt` without `ercot_as_forward_requirement` gives
     a **zero** AS requirement for any year lacking an `ASPLANNP433` file (M4) —
     the co-opt is on but there is *no* AS demand and hence *no* withholding.
  2. **Double-count:** M5 (`as_revenue_per_mw_yr`) is added to the storage entry
     screen unconditionally under `as_revenue_enabled` (`storage.py:966,972`),
     with no awareness of M3. When M3 prices storage AS (duals + AS-widened
     arbitrage spreads captured by `estimate_storage_revenue` off prior-year
     prices), the exogenous M5 credit is a *second* pricing of the same duty.
     There is **no mutual-exclusion validator** (`scenarios.py:2941` checks only
     `mode`/`hydro_year`).

## Answers to the task's step-1 questions

1. *Does runner.py's forecast path pass `reserve_requirement` / storage reserve
   participation?* **Yes.** `storage_power_cap`/`storage_zone_idx` are always in
   `dispatch_kwargs`; `build_reserve_dispatch_kwargs` (with `reserve_storage=True`
   from the ERCOT design) is merged whenever `energy_reserve_coopt` is on.
2. *What does `ercot_storage_as_endogenous` do end-to-end, and is it reachable
   from a forecast config?* Backcast: switches M1/M2 off and hands the full cap
   to M3. Forecast: **reachable but inert** — a no-op, because the measured path
   it disables is never taken in forecast.

## Design implication (what this workstream changes)

The dispatch mechanism (M3) needs **no new LP structure** — it exists and is
tested (`tests/test_ercot_storage_as_endogenous.py`). The gaps are:

- **G-A (reconcile pricing, rule 19):** make M5 and M3 mutually exclusive for
  storage. When `ercot_storage_as_endogenous` is on, the storage entry screen
  must **derive** the AS credit from the co-opt's own duals (M3), never add the
  exogenous M5 credit — exactly one prices storage AS.
- **G-B (make the flag meaningful + close the footguns):** `ercot_storage_as_endogenous`
  requires the co-opt (`energy_reserve_coopt`), and in forecast mode requires a
  forward-regenerable requirement (`ercot_as_forward_requirement`) so M4 is never
  the silent-zero fallback. Enforced in `__post_init__`; surfaced (not silent).
- **Out of scope (documented seam):** the same M5-vs-M3 double-count exists for
  *thermal* AS in `capacity.py:527/1221`; `ercot_storage_as_endogenous` is
  storage-specific, so thermal reconciliation is left as a labelled follow-up,
  not silently changed. PJM synchronized-reserve storage duty (the
  `PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` note, `constants.py:338-359`) is a
  documented seam — no PJM measured storage-reserve series is intaken here.
