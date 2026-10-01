# FINDING: SPP-86, Holcomb's coal must-run conduct row is an outage-share basis defect, fleet-wide (zero LP, 2026-09-26)

Lane: SPP-86. Parent: SPP-85 (`RESULT-spp-85-netload-mask-repair-2026-09-26.md` §3, §6).
Keeper: `2026-09-26-spp-85-netload-mask`, bundle `results/calibration/spp85_arm_span`,
`basis_sha` `0ff620d11d91797313f5f565b5e94ff3b123330b`. Session base: `origin/main` `9149be2c`.

Probes (zero LP, `fleet_only` rebuilds of the keeper):
- `scripts/probes/_spp86_coal_floor_conduct.py` → `results/calibration/_spp86_coal_floor_conduct.json`
- `scripts/probes/_spp86_coal_basis_delta.py` → `results/calibration/_spp86_coal_basis_delta.json`

## 0. Headline

1. **Card A: Holcomb's D-4 FAIL is not a floor-window defect. It is a missing-availability defect.**
   Holcomb (108) is a single-unit plant. The extract books its unit at 348.7 MW; the fleet bin is
   358.9 MW. The accumulator divides one by the other, so every full stop removes 97.1–97.4 %,
   not 100 %. The `coal_mustrun` floor is correctly clipped to availability and survives on the
   residual, about 3.1 MW, in **every** full-window hour. There the LP cannot dispatch above the
   floor, so it binds by construction while the meter reads zero.
2. **That is the whole of the FAIL in 2019 / 20 / 22 / 24, and most of 2021** (§1). With the full-window
   hours removed, the dark share of Holcomb's binding hours is 0–11 % in every year (median meter
   111–126 MW), so the row passes.
3. **It is a fleet-wide defect with an existing construction.** Numerator and denominator come from
   two sources at every coal plant. nyiso-196's `unit_outage_extract_basis_share` takes both from the
   extract (`_extract_basis_index`), but its scope is combined-cycle only. Widening that scope to coal
   (new field `unit_outage_coal_extract_basis_share`) moves **coal availability +0.19 to +0.32 GW
   mean in every year**: 16–20 plants up, 3–4 down, coal rows only (§2).
4. **Card B: the coal-vs-CC object is smaller than C1 suggests, and mostly not merit order** (§3). On
   the EIA-930 fuel basis the 2021–22 gas deficit (−12.7 / −17.6 TWh) is matched by **wind +8.1 / +9.2**
   and coal +2.9 / +6.8 TWh. EIA-923 COAL_PRB (+9.8 / +11.8) and EIA-930 coal disagree by 5–7 TWh.
   No admissible lever identified; nothing proposed.

**Card taken past phase 0: A**, via the fleet-wide repair. It is admissible (zero new parameters, measured
extract, forward-regenerable) and material (every year, every direction measured). PRECOMMIT:
`PRECOMMIT-spp-86-coal-extract-basis-2026-09-26.md`.

## 1. Card A: Holcomb 108, hour by hour

For each floored hour at a dark meter (CAMPD gross < 1 MW), classed by the keeper's own extracts
(standard + short, both `-netloadmask-`):

| year | D-4 binding h / zero share | dark floored h | in a full-plant window | no window | residual floor MW (median) |
|---|---|---|---|---|---|
| 2019 | 221 / 0.90 FAIL | 1,545 | 1,507 | 38 | 3.09 |
| 2020 | 2,381 / 0.90 FAIL | 2,594 | 2,538 | 56 | 3.18 |
| 2021 | 1,071 / 0.52 FAIL | 1,649 | 1,381 | 268 | 3.18 |
| 2022 | 1,225 / 0.60 FAIL | 1,665 | 1,597 | 68 | 3.18 |
| 2023 | 978 / 0.38 pass | 725 | 410 | 315 | 3.12 |
| 2024 | 2,504 / 0.90 FAIL | 2,341 | 2,325 | 16 | 3.12 |
| 2025 | 666 / 0.12 pass | 528 | 432 | 96 | 3.12 |

- **Full-window availability** is 0.029 on the must-run row and 0.026 on the others. The LP bin is
  358.8–359.1 MW, and the extract row carries `unit_pct_of_plant = 100`.
- **2021's extra 268 no-window hours** are the three short windows the SPP-85 filter dropped
  (Jan 17–22, Jun 22–26, Dec 26–29). That is the accepted SPP-85 construction, and those hours carry only
  about 5 % of the post-fix binding hours.
- **Post-fix estimate** (keeper hourly dispatch from the run payload, 1 % CF quantisation):
  - binding hours outside full windows: 17 / 222 / 513 / 450 / 555 / 237 / 616;
  - dark share: 0.00 / 0.00 / 0.05 / 0.00 / 0.11 / 0.00 / 0.05.
- **Verdict (rule 17).** The floor has its driver, window and forward story; the availability under it
  is wrong. A floor-side fix (exclusion list, window mask) would stack a second mechanism on a
  mis-measured input (rules 19 and 24). The repair belongs in the outage share.

## 2. The fleet-wide defect and the existing construction

- **Keeper construction.** Each coal row removes `unit_capacity_mw / cap[bin]`. The numerator is the
  extract's per-unit basis (`eia_exact` / `eia_digits` nameplate, or a CEMS proxy). `cap[bin]` is the
  fleet's EIA-860 per-plant capacity, the MW the LP's `pmax` sums to.
- **Direction 1, under-removal** (extract < bin): Holcomb 348.7 / 358.9 keeps a dark plant 2.9 % alive.
- **Direction 2, over-removal** (extract > bin):
  - Jeffrey 6068 has three 720 MW units against a 2,010.6 MW bin. One unit out removes 35.8 %,
    not 33.3 %.
  - Harrington 6193 (2024, mid-conversion, coal group basis 1,130 MW vs 1,018): with two of three
    units out, the keeper leaves 267 MW, where one unit's share is 342.
- **Extract basis.** One construction for both terms: the row's `plant_capacity_mw` at a
  single-group facility (the published `unit_pct_of_plant`), else the coal group's distinct-unit sum.
  All units out lands on exactly 1.0, and a unit removes its own share of the bin the LP dispatches.

`fleet_only` delta, keeper recipe + `unit_outage_coal_extract_basis_share=true`. The field reproduces
the pre-field patch probe exactly:

| year | Δ coal avail GW (mean) | COAL_PRB TWh | COAL_LIGNITE TWh | coal_mustrun floor TWh (keeper → arm) | plants up / down |
|---|---|---|---|---|---|
| 2019 | +0.202 | +1.739 | +0.027 | 31.67 → 32.13 | 18 / 4 |
| 2020 | +0.286 | +2.474 | +0.033 | 28.48 → 29.11 | 20 / 3 |
| 2021 | +0.240 | +2.042 | +0.059 | 30.30 → 30.80 | 20 / 3 |
| 2022 | +0.228 | +1.975 | +0.024 | 30.36 → 30.86 | 19 / 3 |
| 2023 | +0.296 | +2.524 | +0.073 | 25.84 → 26.59 | 19 / 3 |
| 2024 | +0.317 | +2.712 | +0.062 | 23.61 → 24.61 | 18 / 4 |
| 2025 | +0.188 | +1.636 | +0.013 | 25.32 → 25.70 | 16 / 4 |

- **Coal rows only.** `pmax`, heat rate and VOM are byte-identical.
- **Holcomb.** −4.9 to −25.0 GWh a year; every full-window hour reads availability 0.0 and floor 0.0
  (verified 2021, 1,488 h).
- **The floor moves only where availability moves.** The incumbent must-run floor re-applies on restored
  capacity (+0.4–1.0 TWh placed floor). No new floor (rule 19).
- **Rule-14 direction check, against a measured source rather than the residual.** SPP's published
  coal outage sat 0.61–2.48 GW below the keeper's coal unavailability after SPP-85 (FINDING-spp-85
  §2.1). This moves the keeper 0.19–0.32 GW toward it in every year.

**Rules.**
- **Rule 13:** the removal test is unchanged. Only the share basis moves, it is a property of the
  accumulator on any year's extract, and it is forward-regenerable.
- **Rule 21:** zero new parameters.
- **Rule 24:** no plant list.
- **Rule 25:** SPP's own extract and fleet. Other ISOs get a `U` cell.

## 3. Card B: the 2021–22 coal-vs-CC object, phase 0 only

Keeper, arm − benchmark TWh:

| year | EIA-930 coal | EIA-930 gas | EIA-930 wind | EIA-923 COAL_PRB | EIA-923 COAL_LIG | EIA-923 CC_REG | EIA-923 ST_GAS |
|---|---|---|---|---|---|---|---|
| 2021 | +2.87 | −12.74 | +8.09 | +9.79 | −1.29 | −9.02 | −4.31 |
| 2022 | +6.77 | −17.62 | +9.22 | +11.77 | +0.42 | −9.77 | −4.70 |

1. **Most of the gas deficit is wind on the fuel basis.** Wind is over by 8–11 TWh against EIA-930 in
   every year 2020–25, the SPP-67 CF-level object (2020–21 have no published curtailment). Coal-vs-CC
   merit order is at most about 40 % of the 2021–22 gas deficit.
2. **The two benchmarks disagree on coal by 5–7 TWh** (PRB + LIG vs EIA-930 coal). Before any coal lever,
   the boundary / subclass reconciliation of EIA-923 coal against EIA-930 SWPP coal is owed. It is a
   zero-LP successor.
3. **Timing.** In 2021 the COAL_PRB excess is largest Jun–Oct in both zones (monthly error +9 to +31 %),
   plus Jan–Feb in SPP-North (+18–19 %). 2022 is
   SPP-44's adjudicated object: the MMU-measured delivery-reliability markup, with no admissible
   instrument in EIA-923. That is DO-NOT-REDO.
4. **Coal floor in dark hours.** The `coal_mustrun` floor sits in plant-dark hours for 0.57–1.11 TWh
   a year (3.6–7.4 % of floored hours; 2021 0.80, 2022 0.87). Almost all of it is outside full-plant
   windows: the ensemble-level floor (SPP-71 `coal_sync_ensemble_level`, K) placing E[online] × Pmin in
   hours a plant was economically dark. That is the commitment-state design object, out of scope here.
   River Valley 10671 (CAMPD `grossLoad` null in every hour) is unmetered, not dark.

**No Card B lever is proposed.** Each candidate above is either adjudicated (SPP-44 / SPP-67 / SPP-71)
or needs the benchmark reconciliation first.

## 4. Card C: not scoped this session

The merit-order-guard construction (`-perunitmerit-SPP` + `campd_per_unit_attribution`) was not scoped.
The repair above closes 0.19–0.32 GW of the same keeper−SPP residual by a different, basis-level route.
The guard's scoping should be measured after it.
