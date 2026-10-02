# FINDING — NYISO-NEXT-34 phase 0: the 2023 winter miss is Feb 3–4, and it is oil burned while gas was cheap

```
LANE      : NYISO-NEXT-34 (orchestrator, rule 32 (a)). Zero LP in this document.
KEEPER    : 2026-10-01-nyisonext26p-tslprint-span (+ -2021 folded). Unchanged.
PROBE     : scripts/probes/nyisonext34_oilburn_offcap.py -> results/phase0/nyiso/_nyisonext34_oilburn_offcap.json
MEASURED  : CAMPD plant-day oil share, scripts/data/derive_measured_oil_burn_days.py --iso NYISO (zero parameters;
            artifact data/raw/_processed-legacy/campd_measured_oil_burn_days_NYISO.csv, committed);
            NYISO zonal RT/DA (actual_lmp_hourly_zonal_NYISO.parquet); keeper sidecars (committed).
```

## 1. Open item 3 is February, and February is one event

System load-weighted keeper P1 vs measured, 2023, by month (%): Jan +2.9 RT / −1.2 DA; **Feb −9.7 / −17.6**;
Dec +10.0 / 0.0. Only February is under.

| Feb 2023 | model | RT | DA | Z6 print (trade date) | fleet oil share (CAMPD) |
|---|---:|---:|---:|---:|---:|
| Feb 2 | 115.1 | 42.2 | 67.1 | 28.4 | 0.002 |
| Feb 3 | 62.7 | 130.9 | 165.5 | 3.52 | **0.428** |
| Feb 4 | 54.6 | 182.3 | 235.0 | (weekend) | **0.488** |
| Feb 5 | 41.3 | 88.0 | 62.8 | (weekend) | 0.044 |
| Feb 8–23 (ordinary) | ≈ 35 | ≈ 26 | ≈ 26 | ≈ 2.1 | 0.000 |

- Feb 3–5 carry −$242·day vs RT. The rest of the month is **over** by ≈ +$9/day.
- The keeper prices Feb 3–4 on the $3.52 weekend print. The fleet burned 43–49 % oil (16 plants ≥ 1 %, 8–10 ≥ 50 %).
- The parity cap `min(gas, oil)` can only **lower** fuel cost. It cannot represent a unit burning oil while gas is cheaper.
- Zones: Capital_Hudson (model 42.6 vs RT 59.8) and Long_Island (43.9 vs 70.2) carry the month, not NYC.

## 2. The pattern recurs every year

Days with fleet oil share ≥ 0.10 (a population cut only). Keeper, summed daily error ($·day):

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| days | 12 | 34 | 8 | 5 | 26 |
| of which the keeper's cap binds | 2 | 17 | 0 | 1 | 14 |
| Σ err vs RT | −38 | −1,592 | −197 | −120 | −64 |
| Σ err vs DA | −19 | −805 | −284 | −166 | −429 |

The miss concentrates on days when the Z6 print drops (weekend packages, the day after a spike) while plants
keep burning oil: 2022-12-27/28, 2023-02-03/04, 2024-12-22/23, 2025-01-23/24, 2025-12-16.

**New evidence vs NEXT-24.** NEXT-24 tested the cap-binding days on the flow-dated series and found measured-mix
pricing doubles |error| there (card 4, option A). Feb 3–4 2023 are not in that population: on the keeper's
trade-dated series no 2023 high-oil day is cap-binding. The off-cap high-oil days are a population NEXT-24 did
not read.

## 3. Bracket (zero LP, fleet-only rebuild ± `dual_fuel_measured_oil_burn`)

`lo` = keeper price + the pmax-weighted mean `mc_base` change of the zone's gas tranches. It is an
indicative shift, not a solve.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| C3a vs RT, keeper → lo (%)¹ | +3.9 → +6.2 | −1.0 → +1.2 | +1.0 → +3.9 | −2.7 → −1.3 | −9.5 → **−6.3** |
| monthly NRMSE, keeper → lo | .120 → .128 | .131 → .112 | .130 → .130 | .130 → .138 | .160 → .155 |
| Σ\|err\| vs RT, off-cap high-oil days | 247 → 221 | 748 → 536 | 219 → 206 | 167 → 156 | 336 → 254 |
| Σ\|err\| vs RT, cap-binding high-oil days | 64 → 71 | 1,241 → 1,194 | — | 40 → 66 | 317 → 468 |
| Feb 2023 vs RT | | | −9.7 → +2.5 | | |

¹ The probe's own load-weighting; it sits within ±0.6 pt of the scorer's C3a (+3.4 / −2.1 / +0.4 / −2.6 / −9.6).

- The off-cap object closes in every year. 2025 moves **away** from the −10 % edge.
- The cost is on cap-binding days, as NEXT-24 found (2025 Σ|err| 317 → 468).
- Spill-over: the artifact covers ≈ 22 % of gas generator-hours, almost all at small f. The visible spill months
  are Oct 2023 (+8.5 pt; in-city oil-capability test burns, Oct 17–25) and Jan 2025 (+13 pt; MLK cap-binding days).

## 4. Admissibility

- **Rule 13.** The mechanism and its rule-13 admission already exist (soco-96, owner ruling 2026-09-30, "Oil price at
  measured burn"). It is backcast-only (`_BACKCAST_ONLY_OVERLAY_FIELDS`). Its forward substitute is the parity switch.
- **Rule 19.** On a covered plant-day the measured mix **replaces** the cap; it is never stacked.
- **Rules 21 / 1.** Zero parameters. No band, adder or offset. `offer_curve_by_group` is not invoked.
- **Rule 25.** The per-ISO artifact is NYISO's own CAMPD.
- **Rule 28.** `dual_fuel_measured_oil_burn` is `U` for NYISO and was not solved by NEXT-24. Section 2 is the new evidence.

## 5. Ruled out on the way

- **Flow-dating** would move the Feb 2 spike onto Feb 3. It does not reach Feb 4 ($3.52 package). It was tested with
  print-level as NEXT-25 arm B (2025 −10.3 %), so it is not re-proposed.
- **Commitment (item 5)** is owner-held. **Imports:** the Feb miss is Capital/LI-led and coincides with the fuel signature.
- **unit_hourly** is not needed. It is absent for this keeper (the leg branches were deleted on 2026-10-02).

Next: `PRECOMMIT-nyiso-next34-measured-oil-burn-2026-10-02.md`.
