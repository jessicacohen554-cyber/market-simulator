# G-30 — entry_lookahead_reprice on the ERCOT capacity hindcast (2021→2025)

_Generated 2026-07-08 · gap-register G-30 · forecast-side, NON-KEEPER probe · no
quarantine touched (2022/2026 bridged, not solved/read)_

**Question (G-30):** the ERCOT capacity hindcast forms **zero scarcity hours**
even after the FOM flip (G-32), so the ORDC overlay is inert, solar entry can't
clear its fixed cost, and the economic screen exits the whole coal/gas_st fleet
(~22.8 GW over-retire). Does exercising the built-but-off `entry_lookahead_reprice`
corrective arm let scarcity **form from the LP regime** so solar entry clears and
the false-retire drops?

**Answer (one line):** scarcity **does** form — but only in the *screen's
forward pro-forma*, and only for the **second and later** evolution waves. It
halts the gas_st over-retirement (8.83 → 1.87 GW) and unlocks the first non-zero
new entry (solar 0 → 4 GW, +12 GW gas, +3 GW nuclear), yet the headline **coal
over-retirement (13.96 GW) is unchanged**, because that wave is decided in the
quarantined **2022 bridge year** before any admissible forward signal can reach
the screens.

## Runs (both registered on the forecast-validation dashboard)

| run | flag | bundle |
|---|---|---|
| `ercot-2021-2025-realized-g30base` | `entry_lookahead_reprice=False` | control (reproduces g31) |
| `ercot-2021-2025-realized-g30lookahead` | `entry_lookahead_reprice=True` | corrective-arm probe |

Both are ERCOT CAMPD-per-plant, realized fuel, 2020 vintage, evolve 2021→2025,
2022 bridged, 2023–2025 scored. The two configs differ **only** in
`entry_lookahead_reprice` (its ablation twin, rule 20).

## Does scarcity form?

**In-year dispatch (ORDC overlay): NO — zero in every year, both runs.** The
perfect-foresight LP on the over-supplied 2020 fleet clears every hour (incl.
Winter Storm Uri 2021) with ample reserves, so the post-solve ORDC adder is flat:

```
BASE  2021/2023/2024/2025: mean $0.00, >$10 in 0 h   (max $0/$0/$2/$0)
LOOK  2021/2023/2024/2025: mean $0.00, >$10 in 0 h   (max $0)
```

**Screen forward pro-forma (`entry_lookahead_reprice`): YES.** Re-pricing each
entering year's *realized* net load against the *current (post-retirement)* fleet
stack with the published ORDC curve fires hard once the fleet has thinned:

```
LOOK 2023 → 2024 screens: mean $253.57/MWh (raw duals+overlay $16.36);
                          scarcity >$200 in 636 h, >$1000 in 493 h, max $5000
LOOK 2024 → 2025 screens: mean  $78.28/MWh (raw duals+overlay $12.66);
                          scarcity >$200 in 170 h, >$1000 in 121 h, max $5000
```

This is formed from the LP regime — thinned availability-derated stack ×
realized next-year net load × the same ORDC curve the runner's overlay uses,
**zero fitted parameters** (rule 13). It is not an adder tuned to any retirement
or entry number (honesty gate met). The 2024→2025 signal is weaker than
2023→2024 precisely because 2024's new entry (below) partially re-fills the
stack — the intended negative feedback, not tuning.

## Scorecard: baseline vs lookahead vs actual

| metric | baseline | lookahead | actual |
|---|--:|--:|--:|
| thermal retired GW (2021→25) | 22.80 | **15.83** | 1.53 |
| — coal | 13.96 | 13.96 | 0.93 |
| — gas_st | 8.83 | **1.87** | 0.0 |
| false-retire frac | 0.959 | 0.941 | — |
| solar added GW | 0.0 | **4.0** | 25.08 |
| gas_ct added GW | 0.0 | **6.0** | 3.69 |
| gas_cc added GW | 0.0 | **6.0** | 0.24 |
| wind added GW | 15.0 | 15.0 | 12.66 |
| CO2 2025 (Mt) | 95.1 | 79.4 | 193.6 |

## Why the coal wave doesn't move — the first-wave problem

Per-year evolution timing (identical prefix, divergence at 2024):

```
              BASE                                LOOK
2021  (year 1, no evolution)              (same)
2022* coal 13964 retire; wind +5000       coal 13964 retire; wind +5000     ← identical
2023  gas_st 1870 retire; wind +5000      gas_st 1870 retire; wind +5000    ← identical
2024  gas_st 6964 retire; (no adds)       NO retire; solar+4000 gas_cc+3000 ← DIVERGES
                                           gas_ct+3000 nuclear+2000
2025  (wind +5000)                         gas_ct+3000 gas_cc+3000 nuc+1000 wind+5000
* 2022 = quarantine bridge (evolved, never solved/read)
```

The screens consume the **prior** solved year's price signal (one-pass, rule 10):

- **Coal (2022 bridge):** decided on the **2021** signal. The 2021 lookahead
  would re-price 2022's net load — but 2022 is a rule-22 bridge year whose data
  may **never** be read, so the lookahead is correctly skipped and the screen
  sees the raw 2021 duals (ORDC ≈ 0, full un-thinned fleet). Coal exits.
- **gas_st (2023):** the 2023 screens still consume the **2021** signal (the 2022
  bridge produces no solved price signal), so gas_st 1.87 GW exits identically.
- **2024 onward:** the lookahead computed at the end of **2023** (first year with
  both a solved dispatch *and* a non-bridge next year) reaches the **2024**
  screens — halting the 6.96 GW gas_st retirement baseline made and clearing new
  entry. The 2024 lookahead then feeds 2025.

So the over-supply → zero-scarcity → over-retire chain has a structural
**first-wave problem**: the fleet must thin before the forward pro-forma shows
scarcity, but the **largest** thinning (coal) is decided on the un-thinned fleet,
in a year whose forward signal is quarantined. `entry_lookahead_reprice` breaks
the cycle for waves 2+ (2024/2025) but cannot reach wave 1.

## Verdict

- **Keeps the mechanism (rule 1/13):** `entry_lookahead_reprice` is a
  structurally-faithful developer pro-forma with no fitted DOF; it forms scarcity
  from the regime and demonstrably unlocks entry / stops the gas_st over-retire.
  It is retained as the G-30 forward corrective arm (still default-off; this is a
  forecast-side probe, no keeper/backcast touched).
- **Does not close G-30 alone.** Solar entry clears but reaches only 4 of 25 GW,
  and the 13.96 GW coal false-retire is untouched. Both residuals trace to the
  **first-wave timing**, not to the pro-forma being wrong.
- **Residual root cause (next step), not a fit target (rule 11):** the first
  economic-retirement wave lands on the over-supplied vintage fleet with no
  admissible forward scarcity signal. Candidate directions — a limited-foresight
  *dispatch* screen so the in-year LP itself forms scarcity on the tight fleet
  (would also fix the inert ORDC overlay), and/or a vintage-fleet
  over-supply/staged-thinning treatment so the coal wave is spread across years
  the lookahead can price. Neither is a knob; both are structural and out of this
  probe's scope.

CO2 2025 moves further from actual (95 → 79 Mt) because the added solar reduces a
dispatch whose coal generation is already structurally absent (coal retired in
2022); it is a downstream artifact of the still-locked coal retirement, not an
independent signal.
