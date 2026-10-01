# FINDING — miso-269: the two held-out MISO failures, measured at zero LP. No solve earned.

Keeper `2026-09-24-miso-268-coal-yard` (`results/calibration/miso268_yard_span`), confirmed on
`origin/main` at session start. **Zero LP.** Nothing solved, registered, promoted or deleted.
Every number is a `run_year(..., fleet_only=True)` rebuild of the keeper's own recipe
(`replay_keeper.run_year_kwargs` + `derived_run_year_inputs`), the keeper's committed hourly
sidecars, or the committed bench parts. Scorer basis reproduced first: keeper 2021 monthly
load-weighted NRMSE on the bench `rt_lw_mon` = **0.309** (registered 0.309).

Instruments (committed): `scripts/probes/_miso269_feb2021_gas_phase0.py`,
`_miso269_transport_static_phase0.py`, `_miso269_feb2021_setter_phase0.py` → the three
`results/calibration/_miso269_*.json`.

## 1. C3b 2021 — the February gas array is wrong in both directions

Keeper gas fuel price, capacity-weighted, Feb 2021:

| day type | Chicago-hub zones (East, IL, IN; 29.0 GW) | other zones (West, Plains, South; 40.1 GW) | traded |
|---|---:|---:|---:|
| non-storm (Feb 1–10, 22–28) | **$0.73–1.01** | **$11.1–15.6** | Chicago $2.5–4.0, HH $2.6–3.7 |
| storm (Feb 13–16) | $31.6 | $24–42 | Chicago $129.5, HH $6–17 |

Both columns are construction artifacts, not data:

* **Chicago zones — sub-commodity gas.** `miso_winter_citygate_daily` multiplies the monthly
  level ($5.73) by `print_d / mean(print_month)`. Feb 2021's calendar print mean is $22.71
  because four flow days carry the $129.52 weekend print, so a normal day's factor is **0.11–0.15**
  and Chicago gas lands at $0.75 — below the traded commodity it is derived from. The level is a
  *purchase-weighted* F923 average (plants bought little at $129); the shape is normalized by a
  *calendar* mean. They only agree when the month is calm.
* **Other zones — storm cost smeared onto every day.** Their monthly F923 level is ~$20 (storm
  purchases averaged in), shaped by the national HH series, which barely spikes. Every non-storm
  day inherits ~4× the hub. **This confirms FINDING-miso268 §1's hypothesis for these zones.**

Not a 2021-only defect — median Chicago shape factor by storm month: **Feb 2021 0.154, Jan 2024
0.465 (Heather, training tier), Dec 2022 0.647 (Elliott)**; every calm winter month 0.97–1.03.

**What actually sets Feb-2021 non-storm prices** (price-setter census, keeper P1 duals, TOL
$0.05): coal econ bands ~45 % of MWh at $25–32 — identical to Jan and Mar — and the elevated
hours are gas rows at the distorted fuel: Chicago-zone CT_PEAKER at $1.24/MMBtu, non-Chicago
ST_GAS at $4.6–6.0. Model non-storm LW $47.7 vs Jan $32.5.

## 2. The owner-ruled gas convention is NOT the lever on the current keeper

The miso-225 ruling ("marginal commodity PLUS variable transport") exists as
`miso_gas_marginal_commodity_pricing` + `miso_gas_variable_transport` (cell `O`). Static re-merit
(matched marginal rows shifted by the measured Δmc; an upper bound on the price move — miso-225
realized 64 % of its static):

| year | C3a mean error, keeper → arm | C3b NRMSE, keeper → arm |
|---|---:|---:|
| 2020 | +14.2 % → **+16.3 %** | 0.170 → 0.181 |
| 2021 | +4.7 % → +14.4 % | **0.309 → 0.583** |
| 2023 | +5.1 % → +5.6 % | 0.090 → 0.093 |

* It fixes the non-storm gas *levels* (both zone groups → ~$3) but moves non-storm Feb price only
  47.1 → 45.1 (actual ~28), and it passes the thin $129.52 Chicago weekend print straight through:
  storm-week price 158 → **317** vs 141 actual. Real MISO RT during Uri implies ~$15–19/MMBtu at
  the margin, far below that print.
* **miso-224's decomposition is stale.** It found the average print $0.5–1.3 over the hub
  (74–101 % of the body wedge, 2023). On today's keeper — after `gas_electric_power_monthly_level`,
  `f923_gas_price_plausibility_screen` and `miso_zonal_gas_basis_skip_923_priced` — the arm
  **raises** capacity-weighted gas in every month of 2020 (+$0.06 to +$0.32) and in 9 of 12 months of
  2023. The fuel-convention wedge behind the overnight body is gone.

## 3. C3a 2020 — the overnight body has no open lever

* The gas convention is inert on it (hour-of-day error profile unchanged, §2).
* **Rule 19 attribution done:** the keeper's D-2 puts coal forced energy at **0.21 / 0.25 / 0.40 /
  0.36 / 0.35 / 0.22 %** of the class (2020–2025), one mechanism (`reliability_floor`). The
  overnight coal surplus is economic, not floor-driven. A new self-commitment floor would add
  volume to a class that already over-runs overnight; `miso_coal_night_floor` is `I` and miso-225
  refused a coal floor at phase 0 on the same rule.
* What remains is where coal's econ bands **offer** overnight (delivered cost × HR × the registered
  band multiplier). The only admissible channel for that level is the rule-1 band-multiplier
  carve-out — one year-invariant value, set ex ante, never swept. That is the owner's channel; no
  value is proposed here.

## 4. What is escalated, not absorbed

1. **Construction defect in a keeper `K` mechanism** (`miso_winter_citygate_daily`): in storm
   months it prices Chicago-zone gas below the commodity. No zero-DOF repair exists inside the
   average-cost convention: a faithful day allocation needs purchase weights (an outcome) or a
   regional daily hub for MidCon/South (not on disk; the free EIA NGWU table carries none).
   Owner decision needed on the storm-month convention.
2. **The ruled marginal convention imports thin storm prints.** Arming it for held-out years
   makes both failures worse statically. Owner decision needed if the ruling was meant to cover
   extreme-event prints.
3. **Oct–Nov 2021** (model low by $13–21, 32 % of the C3b SSE) is *not* a gas object: model gas is
   $0.4–0.6 above the hub those months. Unlocalized; a successor lane.

Held-out years never downgrade the ISO (rule 30(c)): MISO's train tier stays CALIBRATED.
