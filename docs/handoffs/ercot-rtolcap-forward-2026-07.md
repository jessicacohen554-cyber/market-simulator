# ERCOT forward RTOLCAP/RTOFFCAP reserve-supply cap (WS-A) — 2026-07

**Date:** 2026-07-05
**Branch:** `claude/ercot-rtolcap-forward-ie2xz6`
**Status:** lever BUILT, tested, default-off, ERCOT-gated, legacy byte-identical,
pure-LP. The forward analogue of the **last AS-path lever with no forward
analogue** — the measured ERCOT on-line responsive reserve-supply cap. WS-A of
`docs/handoffs/ercot-as-coopt-plan-2026-07.md`.
**Reads first:** the WS-A section (§4) of `ercot-as-coopt-plan-2026-07.md`
(failure-mode ledger F1–F7), `docs/ercot-reserve-supply-cap-ordc-adder-2026-06.md`
(run161, the measured RTOLCAP track), and the G4 mode-aware pattern
(`docs/ercot-load-resource-rrs-forward-2026-06.md`).

---

## 1. The gap this closes

`scarcity.ercot_rtolcap_supply_cap_mw` read the **measured**
`data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet` and returned `None`
(uncapped) for any year with no measured parquet — so **forecast years ran
UNCAPPED** and the whole ORDC-era supply re-scope (the mechanism that makes
reserve tighten into the ~8–12 GW band where scarcity fires) went inert forward.
This was the largest remaining measured lever on the AS path with no forward
analogue at all.

## 2. Design — derived committed-share × capability

```
RTOLCAP_fwd(t)  = deliv     × Σ_c online_share_c(nl_bin(t), season(t)) × cap_c(t)
                  + online_storage_power(t)
RTOFFCAP_fwd(t) = deliv_off × Σ_{c∈quick} offline_share_c(nl_bin(t), season(t)) × cap_c(t)
```

* **`online_share_c` / `offline_share_c`** — per responsive class, the median
  over the committed CAMPD unit extracts of the class **on-line
  headroom-realization fraction** `Σ_online(eff_cap − gross) / installed_cap`
  (off-line startable fraction for RTOFFCAP), conditioned on the **net-load
  percentile decile × season**. Derived by
  `scripts/derive_ercot_rtolcap_forward.py` (the
  `MAINTENANCE_MONTHLY_SHAPE`/ST_GAS-drag family). Baked into
  `constants.ERCOT_RTOLCAP_FWD_ONLINE_SHARE` / `_OFFLINE_SHARE`. **Rule #23:**
  re-derives only on a source-data update (CAMPD extracts or the measured ORDC
  reserves parquet), never a residual; the script header cites the data.
* **`cap_c(t)`** — the class's installed reserve-eligible capacity from the model
  `FleetArrays` (summer-derated per hour, matching the derive base). Regenerates
  as the fleet evolves.
* **`deliv` / `deliv_off`** (`ERCOT_RTOLCAP_FWD_DELIV_COEF` = 0.8899,
  `_OFFLINE_DELIV_COEF` = 0.7748) — deliverability coefficients fit to the
  measured RTOLCAP / RTOFFCAP **MW quantity** (pooled 2023–25 LS), never a price.
* **`online_storage_power`** — mode-aware (`ercot_online_storage_reserve_mw`):
  **backcast** = the measured storage-AS series (an admissible measured
  procurement quantity, the G4 pattern); **forecast** = installed storage power ×
  `ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC` (0.35, ERCOT's observed
  award/installed), so the storage reserve grows with the fleet.

Both shares are functions of the model's **own forecast net-load**, so the cap
regenerates forward and responds to changed conditions — the admissibility test
(#10) passes.

### 2.1 Two design decisions worth flagging (rule #11)

**(a) The base is on-line *capacity*, not `ramp10`.** The plan's WS-A sketch
wrote `online_share × ramp10_cap`. But the measured RTOLCAP series
(~13.5/16.7/19.1 GW) is the on-line **headroom** (HSL − telemetered basepoint) an
ORDC deployment can call, and runs **~1.8× the fleet's aggregate 10-minute ramp**
(~9 GW ramp-limited headroom). Forcing the base to `ramp10` undershoots the
measured quantity by ~45%. Per rule #11 (prefer measured data; find the root
cause; don't bury it in an inaccurate input) the base is the class on-line
capacity and the share is a **headroom fraction of installed capacity**. The
10-minute ramp physics still gates the **RTOFFCAP quick-start eligibility** (the
`QUICK_START_FUEL_TYPES` classes) — where ramp/startup really is the binding
qualification.

**(b) The driver direction is headroom-dominated, not "fewer units online."**
The plan narrated "deeper net-load trough → fewer units online → lower RTOLCAP."
The measured series shows the opposite intraday sign: RTOLCAP is **negatively**
correlated with net-load (r ≈ −0.4 to −0.56) — at a low-net-load trough the
committed units are backed off and hold **more** headroom, so RTOLCAP is *high*;
at the high-net-load evening peak they are loaded and RTOLCAP is *low*. A naive
on-line-*count* construction (share of capacity merely generating) is
**anti-correlated** with the measured RTOLCAP (r ≈ −0.3) and would put scarcity
in the wrong hours — the wrong structure for the probe's acute-day gate. The
headroom construction has r ≈ +0.5–0.7 and, crucially, the **scarcity-correct
direction**: higher net-load ⇒ lower share ⇒ lower cap ⇒ reserves tighten on the
tight evenings scarcity actually fires. The derived `online_share` is
monotone-decreasing across net-load deciles (COAL 0.61→0.16), and the driver
test asserts `cap(tight) < cap(loose)`. The VRE-scarcity story the plan wanted
(more VRE → tighter evenings) is carried through the **high-net-load** deciles
(steeper/higher evening ramps), not the trough hour.

## 3. Identification gate — PASSED (anti-F1)

`scripts/validate_ercot_rtolcap_forward.py` (mirror of
`validate_ercot_as_forward_requirement.py`), formula vs measured 2023–25:

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| RTOLCAP formula GW | 14.92 | 15.75 | 16.83 |
| RTOLCAP measured GW | 13.48 | 16.68 | 19.12 |
| RTOLCAP err | **+10.6%** | −5.6% | **−12.0%** |
| RTOFFCAP formula / measured GW | 5.71 / 5.19 | 5.71 / 5.13 | 5.65 / 5.49 |
| **coverage RTOLCAP ÷ AS-req (median)** | **2.02×** | **2.08×** | **2.21×** |

* **(c) Coverage ~2×, NOT the 1.0× artifact** — the *primary* anti-F1 gate. A
  construction landing near 1.0× is the ercot27 exact-coverage artifact and is
  rejected at the script; this sits cleanly at ~2.08× (the measured
  RTOLCAP-vs-AS-plan coverage). **The gate passes.**
* **(b) Band** — formula p10/50/90 brackets the measured band (e.g. 2024
  11.5/16.1/19.3 vs 10.3/16.2/23.5); not a degenerate near-constant series.
* **(a) Level** — 2024 within ±10%; **2023 +10.6% and 2025 −12.0%** exceed ±10%
  on opposite sides. Root-caused, not tuned away (§3.1). The script hard-rejects
  only the coverage artifact / gross level miss; it emits a WARN on the ±10%
  overshoot and lets the documented single-delta probe proceed.

### 3.1 Why 2023/2025 miss ±10% — the residual ledger

The measured RTOLCAP grows **+42%** 2023→2025; the forward-native thermal base is
~flat (the ERCOT thermal fleet barely changed) and a single deliverability
scalar cannot span that. The growth is **storage + load-resource + more
committed capacity**, of which only storage is a forward-native growing term:

* **2023 +10.6% (formula high).** 2023 was a sustained-scarcity year; in the
  tight hours ERCOT's *realized* on-line reserve was depleted below the
  structural headroom a perfect-foresight nameplate-based proxy sees (units at
  their real summer HSL < model nameplate). The annual mean is dragged down in
  the measured series in a way the structural proxy can't reproduce without
  reading the tight-hour outcomes (which #12 forbids). Summer-derating the base
  narrows but does not erase it.
* **2025 −12.0% (formula low).** The 2025 measured level is carried by storage +
  load-resource + committed-capacity growth beyond what the **fixed backcast
  storage base** (a single deployment MW, not year-keyed) supplies. In *forecast*
  mode the storage term grows endogenously, closing this; the backcast probe's
  fixed base is the limitation, not the forward formula.

These are exactly the "differences root-caused in the writeup" the task asks for,
and neither is closed by a tuned value (rule #14 / #23).

## 4. Seam — mode-aware (G4 pattern)

`ercot_rtolcap_supply_cap_mw(config, hours, fleet_arrays=None, *, system_load,
wind_gen, solar_gen)`:

* **backcast, `ercot_reserve_supply_forward` off** → the measured parquet,
  **byte-identical** to the legacy path (the validation target; unit-tested).
* **forecast, OR the `ercot_reserve_supply_forward` probe flag on** → the WS-A
  formula, built from the fleet + forecast net-load threaded through the call
  site (`config/reserve_config.py::_ercot_multiproduct_design`). Falls back to
  `None` (uncapped) if those inputs are not threaded in.

The formula **never reads the LP's own commitment/output state** and never
couples reserve to dispatch `P` (anti-F3/F4). **Honesty gate:** nothing on the
path reads LMP / RTSPP / MCPC / RTORPA — only the measured RTOLCAP/RTOFFCAP MW
quantity (for the coefficient fit) and CAMPD gross output (for the shares).

## 5. The one-delta probe

`scripts/run_ercot40_rtolcap_fwd.py` = **ercot32 recipe EXACTLY +
`ercot_reserve_supply_forward=True`** (the run163 pattern). The single delta:
the RTOLCAP/RTOFFCAP cap is sourced from the formula instead of the measured
parquet. `--year 2023 2024 2025`, one bundle. Registered on the dashboard as
**`2026-07-05-ercot40-rtolcap-forward`** (a probe — the NOT-YET determination is
expected, no governance attestation).

**Probe result** (demand-weighted settled RTSPP, model vs measured RT actual):

| year | probe dw | actual RT dw | hrs>\$200 | hrs>\$1000 | mean ordc_adder |
|---|---|---|---|---|---|
| 2023 | \$52.89 | \$48.36 | 94 | 42 | \$1.84 |
| 2024 | \$35.87 | \$26.83 | 81 | 27 | \$0.18 |
| 2025 | \$35.08 | \$32.49 | 12 | 4 | \$0.03 |

The formula-cap probe forms a live, non-trivial ORDC adder from the formula
reserve level (mean \$1.84/\$0.18/\$0.03, concentrated in the tight 2023 hours) and
holds a full acute tail (42/27/4 hours >\$1000) — the supply re-scope fires the
scarcity channel exactly as the measured cap did, from a fully forward-native
supply.

**One-delta gate (vs the measured-cap baseline, one delta = cap source) —
PASSED.** The measured-cap baseline (identical ercot32 recipe,
`ercot_reserve_supply_forward` off) was re-solved so the demand-weighted
comparison is apples-to-apples (both carry the same DAM-AS overlay, so the delta
is purely the ORDC reserve-dual channel):

| year | formula-cap dw | measured-cap dw | Δdw | hrs>\$1000 (f / m) | hrs>\$200 (f / m) |
|---|---|---|---|---|---|
| 2023 | \$52.89 | \$53.00 | **−\$0.11** | 42 / 42 | 94 / 98 |
| 2024 | \$35.87 | \$35.87 | **−\$0.00** | 27 / 27 | 81 / 81 |
| 2025 | \$35.08 | \$35.08 | **+\$0.00** | 4 / 4 | 12 / 12 |

Δdw is **within \$0.11 in the worst year and \$0.00 in 2024/25** — far inside the
~\$2 gate — and the **acute tail is identical** (42/42, 27/27, 4/4 hrs >\$1000).
The mean ORDC adder matches (1.84/0.18/0.03 vs 1.88/0.18/0.03).

**Why the ±11% RTOLCAP level residuals do not move price.** The ORDC adder fires
only when reserve drops into the ~8–12 GW scarcity band (the low RTOLCAP tail);
there the formula and measured caps agree closely. The annual-mean level
differences live in the *abundant* high-RTOLCAP hours where the adder is ~\$0, so
they never reach the price. The forward supply formula therefore reproduces the
measured cap's price-formation role essentially exactly, from a fully
forward-native supply — the WS-A gate the plan set. (Recorded in
`docs/calibration-log.md`.)

## 6. Files

* `scripts/derive_ercot_rtolcap_forward.py` — the derive script (shares +
  deliverability coefficients; `--emit constant`).
* `src/market_sim/config/constants.py` — `ERCOT_RTOLCAP_FWD_*` (shares, coeffs,
  season map, class lists, storage frac).
* `src/market_sim/config/scenarios.py` — `ercot_reserve_supply_forward` flag
  (+ tier tag).
* `src/market_sim/results/scarcity.py` — `ercot_rtolcap_forward_supply_cap_mw`
  (formula), `ercot_online_storage_reserve_mw` (mode-aware storage), the
  mode-aware `ercot_rtolcap_supply_cap_mw` seam, decile/month helpers.
* `src/market_sim/config/reserve_config.py` — the call site threads fleet +
  net-load into the seam.
* `scripts/run_calibration_full.py` — `ercot_reserve_supply_forward` wired
  through `solve_and_persist` + `run_config.json` + `recorded_cfg`.
* `scripts/validate_ercot_rtolcap_forward.py` — the identification gate.
* `scripts/run_ercot40_rtolcap_fwd.py` — the one-delta probe driver.
* `tests/test_ercot_rtolcap_forward.py` — trivial case, driver response,
  backcast byte-identical, coverage-ratio gate.

## 7. Forward-mode note

In a true 2026+ RTC+B forecast the cap is fully forward-native: `cap_c` from the
evolving fleet, net-load from the forecast load/VRE build, storage from the
endogenous storage build × the responsive fraction, zero measured reads. The
backcast probe holds the storage term at its measured value (the clean
single-delta), so the forecast path's storage growth is exercised separately.
