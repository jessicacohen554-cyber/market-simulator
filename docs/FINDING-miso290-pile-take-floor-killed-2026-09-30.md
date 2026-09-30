# FINDING — miso-290: per-yard monthly coal pile + MISO contract take floor. Identification holds; the pre-check kills it at 2022. No solve.

```
LANE     : miso-290 (owner ruling "Pile + take floor (Recommended)", miso-289 §6)
KEEPER   : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP       : none
PRECOMMIT: docs/PRECOMMIT-miso290-pile-take-floor-2026-09-30.md (c2ee3162, pushed before CAND ran)
PROBE    : scripts/probes/_miso290_pile_floor_precheck.py (--census, --solver-test, default, --diag)
OUTPUTS  : results/calibration/_miso290_pile_floor_{census,solver,precheck,diag}.json
CELLS    : coal_fuel_inventory_take_floor MISO U -> R; coal_fuel_inventory_monthly_pile stays R (note added)
```

## 1. Answer

The contract take floor is **identifiable** from MISO's own EIA-923 Page 5 (coal ~95 % contracted every
year), but the candidate **fails** three of five kill criteria at 2022. It does not stop winter-to-summer
banking: in 2022 the pile had ~480 M MMBtu of headroom below its prior-years maximum, so the floor binds on
only 14 yards and barely touches Jan–Apr. Killed at 2022, as pre-registered.

## 2. Identification (census, all seven years)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| contract share (MW-wtd) | 0.94 | 0.95 | 0.96 | 0.96 | 0.95 | 0.97 | 0.97 |
| yards with a positive floor | 74 | 66 | 64 | 56 | 47 | 50 | 48 |
| annual floor / ceiling | 82 % | 77 % | 73 % | 67 % | 67 % | 70 % | 71 % |
| Jan–Apr cumulative floor (M MMBtu) | 761 | 687 | 615 | **362** | 383 | 552 | 467 |

Every input predates the solve year; zero fitted parameters; floor never exceeds the min-stock ceiling.

## 3. Solver fix (before CAND)

miso-289's subgradient stalled on cumulative rows (PILE0 residual 0.83). The revised rule converges on both
non-candidate arms: INC 0.016, PILE0 **0.013**. CAND converged at 0.031 (gate 0.05). miso-289's PILE0 night
median was a non-converged point (53.35 → 54.11 on the fixed solver).

## 4. Pre-check, 2022

| 2022 | INC | CAND | bench | criterion | result |
|---|---:|---:|---:|---|---|
| Gate V: max monthly coal dev. vs keeper P1 | 1.11 TWh | — | — | ≤ 1.5, annual ≤ 3 % (+0.34 %) | pass |
| night median ($/MWh) | 51.45 | **57.92** | — | K1: ≤ INC − 2.0 | **FAIL** (+6.47) |
| | | | | K2: ≤ INC + 0.5 | **FAIL** |
| Jul+Aug coal (TWh) | 41.7 | 51.5 | 47.5 | K3: ≤ 52.3 | pass |
| annual coal (TWh) | 235.3 | 218.6 | 226.3 | K4: 7.7 ≤ 9.0 + 5 | pass |
| Jan–Apr coal (TWh) | 76.6 | **58.6** | 74.7 | K5: 16.1 ≤ 1.9 + 3 | **FAIL** |

Night median by month ($/MWh):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| INC | 43.3 | 43.5 | 44.5 | 48.2 | 57.2 | 63.7 | 64.6 | 69.8 | 59.5 | 47.1 | 45.8 | 49.6 |
| CAND | 55.8 | 56.5 | 56.9 | 57.5 | 61.0 | 62.2 | 60.3 | 64.0 | 61.0 | 55.5 | 53.2 | 53.1 |

**KILLED.** Other years not run.

## 5. Why — the decomposition (2022 night median, all arms on the fixed solver)

| step | arm | night median | Δ | Jan–Apr coal |
|---|---|---:|---:|---:|
| incumbent | INC | 51.45 | — | 76.6 |
| pile grain alone (no min stock, no floor) | PILE0 | 54.11 | **+2.66** | 66.6 |
| + min-stock ceiling + take floor (keeper offers) | CAND_KO (diagnostic) | 55.72 | +1.61 | 61.1 |
| + take-or-pay discounts disarmed (rule 19) | CAND | 57.92 | +2.20 | 58.6 |

1. **The pile grain does most of the damage by itself.** Moving from the pooled flat `B/12` rows to per-yard
   cumulative rows lets the LP bank winter coal for summer: +$2.66 before anything else is added.
2. **The take floor does not stop the banking.** It forces burn only on contract coal the pile cannot absorb.
   Dec-2021 stocks were far below each yard's prior maximum, so in 2022 that headroom absorbs almost all of the
   winter contract receipts. The floor binds on 11–14 yards, with 8 M MMBtu of shortfall paid.
3. **Removing the per-hour discounts costs another $2.20.** Rule 19 requires it: the contract is carried once,
   and the floor's dual only reprices coal where the floor binds. In winter 2022 it does not bind, so coal
   loses its discount and gets nothing back.

## 6. What this closes, and what stays open

- **Four budget-grain variants are now killed**: pooled carry (miso-287), yard-only (miso-288), pile + min
  stock (miso-289), pile + min stock + take floor (here). The common cause is structural: a cumulative pile
  with ratable receipts and no carrying cost is a perfect-foresight bank. The only admissible stop tested,
  the contract floor, is slack exactly in the year that matters (2022, low opening stocks). The keeper's pooled
  flat `B/12` limb remains the best-behaved form with admissible inputs.
- **Not tested, no admissible source identified here:** a carrying cost on stock, a seasonal inventory policy,
  or a month-of-year pile envelope. Same-year receipts (NWPP-NEXT-9) remain backcast-only (rule 13).
- **Where MISO stands.** Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span **NOT-YET** on
  three routed misses: C1 ST_GAS 2019, C3a 2022, C3b 2021. **No frontier.** Routed misses are failures.
