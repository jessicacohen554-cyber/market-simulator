# RESULT — PJM-NEXT-21: C1 stays on EIA-923 (owner ruling); PJM's own coal offers are steeper than the keeper's ladder (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO all read **NOT-YET**. Same 10 failing cells.

**Solves:** none. No PRECOMMIT (card 3 not reached).

| probe | artifact | card |
|---|---|---|
| `scripts/probes/_pjmnext21_c1_reconcile.py` | `results/phase0/pjm/_pjmnext21_c1_reconcile.json` | 1 |
| `scripts/probes/_pjmnext21_coal_offer_slope.py` | `results/phase0/pjm/_pjmnext21_coal_offer_slope.json` | 2 |

## 1. Card 1 — size a rule-14 C1 reconciliation to PJM's fuel-mix telemetry

**Method.** The keeper's C1 was re-scored with `calibration_verdict.score_fuelmix`, unchanged, against `classFull` re-bounded month by month to EIA-930 by fuel (EIA-930 equals PJM `gen_by_fuel`). Within each month, benchmark plants are scaled pro rata on a grid-delivered basis (`e_mon` net of BTM). Variants:
- `gas`: gas classes are scaled to 930 gas. Hopewell, Martins Creek and Montour are held at their EIA-923 value (NEXT-20 card 2).
- `gas_all`: as `gas`, with no plants held.
- `gas_coal`: `gas`, plus coal classes scaled to 930 coal.

`base` reproduces the keeper exactly.

| C1 miss, TWh (* = FAIL) | base | gas | gas_all | gas_coal |
|---|---|---|---|---|
| CC_REGULAR 2019 | +6.3 | +7.4 | +8.7* | +7.4 |
| CC_REGULAR 2020 | +9.8* | +14.2* | +15.7* | +14.2* |
| CC_REGULAR 2022 | +10.9* | +8.3* | +8.9* | +8.3* |
| CC_REGULAR 2023 | +8.5* | +9.6* | +10.8* | +9.6* |
| CC_REGULAR 2024 | −0.8 | +4.8 | +10.3* | +4.8 |
| COAL_BIT 2019 | +18.7* | +18.7* | +18.7* | +8.9* |
| COAL_BIT 2021 | +17.1* | +17.1* | +17.1* | +10.3* |
| COAL_BIT 2023 | +0.3 | +0.3 | +0.3 | −6.1 |
| COAL_BIT 2025 (SKIPPED, prelim 923) | +11.3 | +11.3 | +11.3 | +3.0 |
| **failing cells, all criteria** | **10** | **10** | **12** | **10** |

**Reading.**
- 930 gas is below the benchmark, so re-bounding lowers actual CC. That makes the CC_REGULAR over-run **worse** in 2019–2021 and 2023–2024; only 2022 improves, and it still fails.
- **The CC 2023 miss is the model's, not the benchmark's.**
- 930 coal sits +3.4 to +12.5 TWh above EIA-923 net coal in every year. The monthly scale is a near-uniform k ≈ 1.04–1.09, the size of coal station service, but that cause is **not established**. Re-bounding coal shrinks COAL_BIT misses by ~7–10 TWh in the miss years and turns them to −4 to −6 TWh in the fit years 2022–24. It fixes no failing cell.
- 2025 C1 is SKIPPED (preliminary EIA-923). The 2025 bench coal (137.4 TWh) agrees with CEMS (134.8), so the 2025 coal over-run is real.

**Owner ruling (decision card, 2026-10-01):** *"Keep EIA-923"*. C1 is unchanged. Rule 14 is not invoked.

## 2. Card 2 — coal offer-curve slope, PJM's own offers vs the keeper's econ ladder

**Method.**
- **Data:** the offers corpus was refetched for Jan, Apr, Jul and Oct of 2019–2025 (28 months). The feed is anonymised. Population: NEXT-17's `COALLIKE` heuristic, i.e. LONG_RUN units whose daily bid does not track gas (r < 0.5), 29–71 units.
- **Keeper:** COAL_* econ + peak tranches from `unit_marginal_<y>`, over the same months.
- **Metrics, both sides:** over the dispatchable range above the floor, S(d) is the share of range MW priced ≤ the range's MW-weighted mean + d. IQR is p75 − p25 of price.

| | PJM S(0) / S(+5) / S(+15) | PJM IQR $ | keeper S(0) / S(+5) / S(+15) | keeper IQR $ | keeper − PJM, S(+5) | COAL_BIT over-run |
|---|---|---|---|---|---|---|
| 2019 | .64 / .94 / .97 | 1.4 | .62 / .96 / 1.00 | 2.8 | +.01 | +18.7 |
| 2020 | .64 / .95 / .97 | 1.0 | .57 / .98 / 1.00 | 2.9 | +.02 | +11.9 |
| 2021 | .59 / .91 / .94 | 0.7 | .57 / .94 / 1.00 | 4.1 | +.03 | +17.1 |
| 2022 | .61 / .83 / .94 | 2.2 | .50 / .75 / .97 | 11.3 | −.08 | +6.8 |
| 2023 | .60 / .92 / .95 | 1.3 | .52 / .89 / 1.00 | 5.2 | −.03 | +0.3 |
| 2024 | .60 / .93 / .95 | 1.1 | .53 / .83 / .99 | 6.8 | −.10 | +0.9 |
| 2025 | .57 / .93 / .97 | 1.2 | .54 / .83 / .99 | 7.1 | −.10 | +11.3 |

**Reading.**
- **PJM's own coal offers are steeper than the keeper's ladder in every year:** IQR $0.7–2.2 vs $2.8–11.3. The keeper's ladder is not over-steep.
- At +$5 the keeper sits +0.01 to +0.03 above PJM in 2019–21 and −0.03 to −0.10 in 2022–25. **2025 (a miss year) reads like 2024 (a fit year).** The difference does not order the years, as with NEXT-20's ladder width.
- The only systematic difference is PJM's high tail: 3–6 % of range MW is offered above mean + $15. The keeper has ~0 there. It is small and the same in every year.
- Real coal loads 0.64–0.72 at $0–5 of margin (NEXT-20) while its own offers clear ~0.6–0.9 of range within $5 of their mean. Real units under-run their own offers, and by a similar amount in every year (NEXT-17 RoR).

**Verdict, card 2.** **Refuted.** The keeper's coal ladder is flatter than PJM's offers, not steeper. Moving it to PJM's shape would steepen the fit years 2022–25 most. No admissible, year-discriminating, zero-DOF mechanism. **OPEN, not a limit.**

## 3. Card 3

Not reached.

## 4. Next (NEXT-22)

1. **Coal: the interaction of the price gap and ladder density.** The model clears $3.5–5.1 above RT in coal hours, about the same in every year (NEXT-20). The keeper's ladder IQR grows from $2.8 (2019/20) to $5–7 (2023–25). The same gap therefore clears more of the ladder in 2019–21. 2025 again breaks the order. The open question is what is specific to 2025: its ladder is wide, yet it over-runs by +11.3 TWh. Start with per-plant 2025-vs-2024 loading at matched margin.
2. **The non-coal open cells** (check the §5.3 queue first): CT_PEAKER 2021 (−9.6), and the 2022 cluster (CC_REGULAR +10.9, C3a, C3b).

**Retrievability:** no bundles. Probe JSONs are committed under `results/phase0/pjm/`. The offers corpus is gitignored raw and lost with the container.
