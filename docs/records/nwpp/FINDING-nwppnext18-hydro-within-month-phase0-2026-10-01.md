# FINDING — NWPP-NEXT-18 phase 0 (ZERO LP): NWPP hydro does not have too much within-month freedom

Object: keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`). Its north-zone price is flat within each month (NEXT-17 §3:
within-day and between-day SD ~1/10 of WEIM). The handoff hypothesis was that the monthly hydro budget gives the LP too
much freedom to move energy between days. Lever under test: `hydro_budget_period_by_instrument` (NWPP cell `U`).

Source: keeper #20's legs 2022 `11bb59fb`, 2023 `a54c7b97`, 2024 `91f0bc29`, 2025 `1a41ba51` (`unit_hourly`,
`system.parquet`). Measured: CROHMS hourly project power for 16 Columbia/Snake projects (`data/raw/nwpp-hydro/crohms`,
PST clock per its catalog), EIA-930 NG:WAT envelope, WEIM hourly ELAP, CAISO hourly RT LMP.
Probe: `scripts/probes/_nwppnext18_hydro_freedom_phase0.py <leg root>` prints every table. No LP was run.

## 1. Who carries the water value

Hydro plants sitting off their monthly bounds (interior, so price-setting), north zones, weighted by hours × MW:

| | 2023 | 2025 |
|---|---:|---:|
| share on the Columbia/Snake chain (`nwpp_hydro_chain.csv`) | **99.3 %** | **99.4 %** |
| top plants | Grand Coulee 6,495 MW (3,067 h), Chief Joseph, Bonneville, Wells, The Dalles | same order |

- The water value is carried by the **Columbia mainstem storage projects**, led by Grand Coulee. The small high-pondage
  reservoirs NEXT-17 §2 found in NWPP-EAST are marginal too, but they hold < 1 % of the interior MW.
- Grand Coulee is the chain's head and is not in the cascade water balance (coupled links: GCL→CHJ, CHJ→WEL, RRH→RIS,
  TDA→BON, LMN→IHR). Its only energy constraint is the monthly budget.

## 2. Measured freedom, model vs CROHMS

Between-day = SD of daily energy within the month (month mean). Within-day = SD of hourly MW within the day (day mean).

| year | set | between-day meas GWh | model GWh | **ratio** | within-day meas MW | model MW | **ratio** |
|---|---|---:|---:|---:|---:|---:|---:|
| 2022 | 16 projects | 28.3 | 24.4 | **0.86** | 1,315 | 1,590 | **1.21** |
| 2023 | 16 projects | 27.1 | 20.2 | **0.75** | 1,745 | 1,712 | **0.98** |
| 2024 | 16 projects | 22.7 | 20.5 | **0.90** | 1,443 | 1,746 | **1.21** |
| 2025 | 16 projects | 26.5 | 22.9 | **0.86** | 1,271 | 1,786 | **1.41** |
| 2022 | Grand Coulee | 10.0 | 7.1 | 0.71 | 548 | 791 | 1.44 |
| 2023 | Grand Coulee | 7.5 | 6.2 | 0.83 | 505 | 860 | 1.70 |
| 2024 | Grand Coulee | 7.5 | 6.0 | 0.81 | 488 | 841 | 1.72 |
| 2025 | Grand Coulee | 8.2 | 6.8 | 0.83 | 515 | 832 | 1.62 |

- **Between days, the model moves less energy than the real projects do** (ratio 0.75–0.90; Grand Coulee 0.71–0.83).
  NYISO's case was the opposite (1.86–2.25×, nyiso-218). A shorter budget period can only remove freedom. Here it would
  move the model further from measurement.
- **Within the day, the model over-shapes**: 0.98–1.41× for the 16 projects and 1.44–1.72× at Grand Coulee. That is
  excess freedom, but it is hourly, not a budget-period question.

## 3. Rule 19: the envelope already binds, and the price barely moves when it does

`hydro_dispatch_envelope` (fleet p95 of EIA-930 NG:WAT per month × hour) binds in 17 / 27 / 31 / 33 % of hours
(2022–2025), and in 23–33 % of top-decile price hours. In 2023 the price in binding hours is only **$1–5 above** free hours
in every month Mar–Dec (Jan +$85, May +$16). When hydro is capped, the next unit is a gas CC at about the same cost.
**The flat price is the gas stack as much as the water value.** NWPP gas is monthly (Henry Hub monthly + annual zonal basis,
`nwpp_zonal_gas_hub.csv`), so there is no between-day fuel signal either.

## 4. What the measured price co-moves with

Measured NW prices against CAISO RT, r of daily means (between-day) and of daily-demeaned hours (within-day):

| | BPAT | PACE | IPCO |
|---|---|---|---|
| between-day r, 2023 / 24 / 25 | 0.72 / 0.72 / 0.74 | 0.90 / 0.83 / 0.87 | 0.75 / 0.82 / 0.83 |
| within-day r, 2023 / 24 / 25 | 0.21 / 0.12 / 0.22 | 0.71 / 0.54 / 0.68 | 0.55 / 0.37 / 0.40 |

The real between-day variation is West-wide (common gas and load drivers). PACE and IPCO also carry CAISO's within-day
shape. In keeper #20, NWPP's interface is a **fixed** schedule (`priced_interchange` False, `reference_price_interface`
False; both NWPP cells `U`), and gas has no daily shape (`gas_daily_shape`, `U`).

## 5. Reading (rules 13, 14, 17, 19)

- **Do not arm `hydro_budget_period_by_instrument` for NWPP.** Measurement says the price-setting projects have *more*
  between-day freedom than the model gives them. Rule 13 allows a restriction only where measurement shows the plant lacks
  the freedom. The governing-instrument search (CRT operating plans, BiOp flow objectives, Hanford Reach) is moot for a
  sub-monthly period. It was not pursued, and no registry entries are added.
- **The within-month flatness is not hydro banking.** It has two parts. (i) The resource behind hydro is a flat monthly
  gas stack. (ii) The interface that couples NWPP to the West's price is fixed. Both are untested on NWPP (`U`).
- **Grand Coulee's within-day over-shaping (1.4–1.7×) is real.** It is a per-plant hourly object. NWPP-49 showed the LP
  re-routes swing onto other shapeable reservoirs when one is constrained, and the 16-project ratio is only 0.98–1.41.
  It is not a lever on its own.
- C3 (price) is still UNSCORED for NWPP. Without it, no NWPP gate sees price-formation work.
