# FINDING — miso-289: per-yard monthly coal pile + prior-years minimum stock. Identification holds; the pre-check kills it on price. No solve.

```
LANE     : miso-289 (owner ruling "Min-stock target design (Recommended)", miso-288 §5)
KEEPER   : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP       : none
PRECOMMIT: docs/PRECOMMIT-miso289-minstock-pile-2026-09-30.md (ed7981a8, pushed before the emulator ran)
PROBE    : scripts/probes/_miso289_minstock_precheck.py (--census, then the INC/PILE0/CAND pre-check)
OUTPUTS  : results/calibration/_miso289_minstock_{census,precheck}.json
CELLS    : coal_fuel_inventory_monthly_pile MISO U -> R (pre-check kill, no LP); no other verdict moves
```

## 1. Answer

The minimum-stock target is **identifiable and non-degenerate**, but the candidate built on it **fails its
price criteria**. In 2022 it pulls summer nights toward the hub and pushes winter and spring nights away by
more. Net: the 2022 night median rises **$4.64** against the incumbent. Killed at 2022 as the rule requires.

## 2. Identification (census, all seven years)

Per yard: minimum month-end days of burn on hand over the prior three stock years (2019: one year; 2020: two),
converted at the yard's own budget receipts rate; floor = `min(S_min, S_dec)`, held at every month-end.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| MW-weighted d_min (days) | 52.9 | 46.4 | 46.1 | 43.0 | 41.3 | 41.8 | 51.7 |
| identified share of rowed MW | 99 % | 99 % | 99 % | 99 % | 100 % | 100 % | 100 % |
| annual budget cut | 11.0 % | 9.1 % | 8.3 % | 7.9 % | 7.9 % | 7.7 % | 9.4 % |
| yards opening below target | 2 | 0 | 1 | 0 | 0 | 0 | 0 |

Every input predates the solve year; zero fitted parameters. Fleet cross-check: the 2022 floored cap is
130.0 Mt against a measured burn of 130.2 Mt.

## 3. Pre-check, 2022 (Gate V passes: INC monthly coal within 1.08 TWh of the keeper, annual +0.28 %)

| 2022 | INC | PILE0 (no floor) | CAND | bench / hub |
|---|---:|---:|---:|---:|
| night median ($/MWh) | 51.62 | 53.35 | **56.26** | — |
| annual coal TWh | 235.2 | 239.9 | 219.5 | 226.3 |
| Jul+Aug coal TWh (cap 52.3) | 41.7 | 54.0 | 50.4 | 47.5 |
| max row residual | 0.019 | 0.83 | 0.49 | — |

Night median by month ($/MWh):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hub | 35.0 | 39.3 | 31.9 | 49.4 | 49.3 | 51.2 | 52.9 | 62.0 | 54.2 | 36.5 | 32.3 | 33.3 |
| INC | 43.3 | 43.6 | 44.5 | 48.3 | 57.1 | 63.7 | 65.5 | 69.8 | 59.5 | 47.1 | 45.9 | 49.6 |
| CAND | 51.1 | 53.3 | 54.5 | 55.8 | 62.3 | 62.6 | 58.7 | 64.1 | 59.5 | 51.3 | 49.9 | 50.6 |

Coal TWh by month, CAND vs bench: Jan 17.5/22.9, Feb 15.6/20.0, Mar 14.1/17.1, Apr 12.5/14.8,
Jul 24.8/24.3, Aug 25.6/23.2.

**Kill rule:** K1 (2022 nights −$2): **FAIL**, +$4.64. K2 (no year > +$0.5): **FAIL**. K3 (Jul+Aug ≤ 52.3):
pass, 50.4. K4 (annual guard): pass, |−6.8| ≤ 13.9. **KILLED.** Other years not run.

**Convergence caveat.** The cumulative-row arms stop at 200 iterations with one row oscillating (residual
0.49–0.83; INC 0.019). The verdict is not sensitive to it: K1 misses by $6.64, CAND's ceilings are at or
below PILE0's everywhere, and PILE0 alone already sits +$1.73 above INC.

## 4. Why it fails

1. **The floor works as designed on annual quantity.** It removes ~16 TWh of 2022 coal (235 → 219.5), from
   above the bench to below it.
2. **The cumulative pile is a perfect-foresight bank.** With ratable receipts and no carrying cost, a binding
   August row's dual prices every hour from January to August equally. The LP therefore saves winter coal for
   summer: Jan–Apr coal falls 13 TWh below the bench, and winter nights rise $8–10. The real fleet burned
   hard in January (22.9 TWh) on winter receipts, and its pile still rose Jan→May.
3. **So the grain moves the problem, it does not solve it.** Three variants of the budget grain are now killed.
   The pooled carry (miso-287) and yard-only grain (miso-288) push coal into summer and lift nights. The pile
   with a floor (here) fixes summer but starves winter. The keeper's pooled flat `B/12` limb stays the
   best-behaved form available with admissible inputs.

## 5. What stays open

- Why ~86 % of coal MW sits under a binding yard when the IMM counts 25–45 % conserving (miso-288 §4(b)). That
  is an **offer-level** question, and it is data-gated: the MISO masked offer corpus carries no fuel attribute.
- A pile would need something that stops winter-to-summer banking: measured receipt timing, a seasonal
  inventory policy, or a carrying cost. None has an identified, admissible source here. Same-year receipts
  (NWPP-NEXT-9) are a backcast overlay only and give no forward story (rule 13).
- **Where MISO stands.** Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span **NOT-YET** on
  three routed misses: C1 ST_GAS 2019, C3a 2022, C3b 2021. **No frontier.** Routed misses are failures.
