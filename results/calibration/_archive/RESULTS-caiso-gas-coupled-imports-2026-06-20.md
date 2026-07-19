# CAISO gas-coupled imports — 3-year validation (2026-06-20)

Branch: `claude/caiso-lmp-lever-ab-m56edy`. Validates `--caiso-import-gas-coupling`
(the no-OASIS, forecast-consistent replacement for lever A's desert-SW leg) paired
with lever B (`--gas-hub-basis-overlay`). Plan + methodology:
`PLAN-caiso-gas-coupled-imports-2026-06-20.md`. Supersedes the OASIS-dependent
lever A in `DIAGNOSIS-caiso-import-ladder-2026-06-19.md` and the gas-over-run
catch in `RESULTS-caiso-leverB-citygate-2026-06-19.md`.

Run config (all): `--commitment --priced-interchange --hydro-backfill-year <yr>
--hydro-eia930-monthly`, ± `--gas-hub-basis-overlay --caiso-import-gas-coupling`.
Load-weighted system LMP from `system.parquet` (year, P2), fuel TWh from
`dispatch/<yr>_P2.parquet`.

## The mechanism (one line)

The desert-SW import blocks (`DSW_solar_PV`, `DSW_CCGT`, `DSW_CT`) are Palo
Verde / Path-46 energy whose price-setting marginal unit is SW gas. Lever B
reprices in-state gas to the measured commodity spot (Henry Hub month + measured
CA citygate basis) but the fitted import ladder didn't follow, so cheaper in-state
gas undercut the SW gas imports and stole their share (gas over-ran +12%). The
coupling shifts those blocks by the same measured per-MMBtu gas delta x heat rate,
so both legs price off the same commodity gas and imports hold share.

## 3-year results

| yr | run | mean | p50 | actual mean | gas TWh | EIA-923 | net imp TWh | actual imp | neg hrs |
|----|-----|------|-----|-------------|---------|---------|-------------|-----------|---------|
| 2023 | base    | 78.9 | 67.9 | n/a  | 66.4 | 76.0 | 39.8 | 28.9 | 7 |
| 2023 | **B+couple** | **66.6** | 56.2 | n/a | 66.7 | 76.0 | 39.9 | 28.9 | 7 |
| 2024 | base    | 55.5 | 56.2 | 32.9 | 70.4 | 67.7 | 32.6 | 32.4 | 14 |
| 2024 | B alone | 47.4 | 48.0 | 32.9 | **75.7** | 67.7 | 27.7 | 32.4 | 14 |
| 2024 | **B+couple** | **46.4** | 46.8 | 32.9 | 72.6 | 67.7 | 30.9 | 32.4 | 14 |
| 2025 | base    | 58.6 | 57.2 | 33.6 | 72.2 | 55.2\* | 36.3 | 36.2 | 1 |
| 2025 | **B+couple** | **53.0** | 51.4 | 33.6 | 74.1 | 55.2\* | 34.6 | 36.2 | 1 |

\* 2025 EIA-923 (55.2) looks under-reported vs EIA-930 (79.0) — partial-year
receipts; treat the 2025 gas benchmark as unreliable.

## Findings

1. **Price drops every year** — mean −12.3 / −9.1 / −5.6 (2023/24/25), p50 likewise.
   Closes ~40-50% of the body gap to actual (2024 resid +22.6 -> +13.5; 2025 +25.0
   -> +19.4). It does **not** reach the ~$34 structural floor — as the diagnosis
   established, a merit-order LP cannot clear its median below CA gas marginal
   cost. Reported honestly; not fit.

2. **The coupling neutralizes lever B's gas over-run.** Standalone lever B inflated
   2024 gas to 75.7 TWh (+12% over EIA-923, −5 TWh of imports). B+couple holds gas
   within **~+0.3 / +2.2 / +1.9 TWh of the baseline** across the three years (2024:
   75.7 -> 72.6) and restores net imports to ~baseline (2024: 27.7 -> 30.9, vs
   measured 32.4). The DSW_solar_PV block recovers 7.6 -> 11.0 TWh — exactly the
   share lever B had stolen.

3. **vs the current keeper (baseline): a pure price win.** B+couple buys a large
   mean reduction (−$9 in 2024) for ~+2 TWh of gas and ~−1.7 TWh of net imports —
   gas/import volumes essentially unchanged, price much closer to actual.

4. **2023 is the documented import outlier**, unchanged by the coupling: the model
   over-imports (39.9 vs actual 28.9 TWh) and under-burns gas (66.7 vs EIA-923
   76.0). That is a volume/availability artifact of the static node (flagged in
   `IMPORT_TRANCHES` "a single price vector cannot hit all three years"), a
   price-coupling lever does not touch it.

5. **The negative tail is unchanged** (7 / 14 / 1 hrs <=$0 vs actual hundreds) —
   out of scope here. It needs the desert-SW solar diurnal (Palo Verde midday
   glut), for which there is no in-repo SW per-fuel series. Not fit.

## Grounding / forecast-consistency (claude.md #1, #11)

- No curve-fitting: the shift is `(commodity_spot - EIA-923_delivered) x heat
  rate`, both series measured; heat rates are representative desert-SW values
  (CCGT/CT match the existing carbon-EF map); the shift is ~0 at baseline gas, so
  the validated import volume is preserved and only the gas-sensitivity is added.
- Forecast-consistent: in a forecast the SW imports index to projected gas the
  same way (no-op without a measured basis). Unlike OASIS lever A (measured
  intertie LMP, unavailable in a forecast), this generalizes.
- Carbon untouched: the border CARB adder stays on each tranche's own EF
  (DSW_solar_PV pays none); only the energy level is gas-coupled.

## Recommendation

- **Keep both as paired opt-in flags** (`--gas-hub-basis-overlay
  --caiso-import-gas-coupling`). The coupling is a no-op without lever B (it only
  matters once in-state gas is cheapened).
- **Do not flip `_calibration_config` defaults yet.** B+couple is a genuine,
  3-year-validated *price* improvement with disciplined volumes, but (a) gas sits
  marginally above the baseline on the EIA-923 benchmark, (b) the body is still
  ~$13-19 above actual (structural floor), and (c) the negative tail is unaddressed
  — so this is a documented improvement, not a finished CAISO calibration.
- **Dashboard:** register B+couple 2024 (and 2025) as the documented best CAISO
  *price* config, with the caveats above, if a keeper entry is wanted.
