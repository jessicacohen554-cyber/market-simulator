# PRECOMMIT — NWPP-NEXT-10: EIA-860 exit-month routing of the CAMPD outage layer, 2019–2025

**Control:** keeper #15 `2026-09-28-nwppnext8-coal-monthly-pile`, compared against its committed bundle
`results/calibration/nwppnext8mp_span` (rule 29(b) form 4). No control solve.
**Parent:** zero LP. Seven year-isolated shards (rule 36), one arm.

## 0. Lever 1 closed at phase 0 (owner card, 2026-09-29: "Close lever 1, pivot")

The handoff's first lever was an operator inventory-management mechanism for C4 coal 2023, with a measured
identification. It has none:

- PacifiCorp's per-plant low/high coal-inventory targets exist (2021 Kaptur study, audited yearly by the Utah DPU),
  but every value is **redacted** in the public record (DPU comments, docket 24-035-13, 2024-04-30).
- The only public figure is a 2009 DPU memo (docket 09-035-23): "two to three months at its three Utah plants and a
  somewhat lower range at its four Wyoming plants". It gives Bridger no number and states no days-of-burn basis.
- The 2023 Page 2 stocks sat **below** any two-month level all year (Hunter 291–495 kt, Huntington 267–459 kt). So a
  hard floor contradicts the measurement, which is the same failure as S_min.
- Jim Bridger (Wyoming, unquantified) carries +1.98 TWh of the ~2.95 TWh Q1-2023 over-burn at the three PacifiCorp
  yards (keeper #15 `m_mon` against CAMPD gross): Bridger +1.98, Hunter +0.65, Huntington +0.32.

Disposition: matrix NWPP has no field for it (nothing built). C4 coal 2023 stays the named open record.

## 1. Why this arm (zero-LP census, rule 14)

A plant cannot generate more than it is available to generate. `scripts/probes/_nwppnext10_coal_availability_census.py`
rebuilds keeper #15's fleet (`run_year(fleet_only=True)` on its own recipe) and compares each coal plant's
`Σ_t pmax·availability` with its own EIA-923 net generation. Colstrip 6076 in 2020 is the largest breach in the span:
**5.855 TWh available against 7.935 TWh generated.**

The root cause is on the outage layer:

- Colstrip Units 1–2 (438 MW in the extract) retired in 2020-01. `mid_vintage_exit_carry` gives them their own
  dated exit bin (`_p6076_r202001`, 614 MW), which is zeroed after January.
- The CAMPD extract books their post-retirement darkness as outage windows, 2020-01-02..12-31 and 01-03..12-31.
- With no dated key, those windows derate the plant key. That is the surviving Units 3–4 bin (1,480 MW), which
  loses 438/2,094 all year.
- Units 3–4's own windows divide by 2,094 (a retiree-inclusive denominator), not 1,480.
- Measured bin availability: Jan–Apr 0.58–0.64, Sep–Nov 0.10–0.24.

**Existing repairs tried first (2020, zero LP).** None removes the retirees' darkness:

| Variant | Colstrip 2020 avail (TWh) |
|---|---|
| keeper #15 | 5.855 |
| `unit_outage_fleet_status_scope` | 5.855 (inert: retirees fail open) |
| `unit_outage_per_unit_clip` | 5.855 (inert) |
| `unit_outage_dispatched_bin_denominator` | 7.571 |
| `unit_outage_coal_extract_basis_share` | 7.553 |

`unit_outage_exit_cohort_repair` (PJM-NEXT-8) has the right construction, since it routes a row by `exit_ym` to its
dated bin. But it reads `exit_ym` only from a PJM-specific re-derived companion chain.

## 2. The arm (one new key, default off)

`unit_outage_exit_ym_from_eia860`: absent → **True**.

1. **Stamp.** Each row of the ≥5-day extract gets `exit_ym` from EIA-860's own per-unit retirement month, but only
   where that month is one of its facility's dated bins. The source is the active vintage's Retired-and-Canceled sheet,
   falling back to the canonical one. A frame that already carries `exit_ym` is untouched.
2. **Activate per plant.** Routing turns on only at plants with a stamped row whose window overlaps the solved year.
   The fleet side keeps dated shares only where the factors carry a dated key. Every other plant keeps the incumbent
   plant-key derate byte-for-byte.
   - This guard exists because of Centralia 3845. Its CAMPD ids `BW21`/`BW22` never match EIA-860's `1`/`2`. Without
     the guard, its dated Unit-1 bin would silently have lost every real window (+2.58 TWh, measured and refused).
3. **Accumulate.** PJM-NEXT-8's accumulator runs unchanged: a stamped row derates its dated bin over that bin's share,
   and an unstamped row derates the undated remainder over `cap × (1 − Σshares)`.

Zero free parameters (rule 21). Backcast-only, like the overlay (rule 13). Rule 19: it removes a double count and does
not stack on anything.

**Zero-LP prediction (census with the arm, every year).**

| Year | Coal avail keeper #15 → arm (TWh) | Plants moved |
|---|---|---|
| 2019 | 80.100 → 80.100 | none |
| 2020 | 65.631 → 67.689 | Colstrip 5.855 → 7.913 (EIA-923 net 7.935) |
| 2021–2025 | unchanged | none |

So **2019 and 2021–2025 are byte-identical to keeper #15 by construction**: no live plant means the shares are
`None`, which is the incumbent path. Those six legs are the empirical G-DRIFT check. Only 2020 is a new solve in
substance.

Expected direction, stated and not selected on: more Colstrip energy is available in 2020. Keeper #15 already has
COAL_PRB 2020 at +2.14 TWh in C1, so C1 COAL_PRB 2020 may worsen, and C4 coal 2020 (0.762) may move either way. The
case for the arm is rule 14 physics, not the residual (rule 1).

## 3. G-DRIFT (rule 29(b)) against keeper #15's `git_sha` e7478536

NEXT-9 audited e7478536 → `40fc286b` as ALL INERT. Re-audited `40fc286b..526b75ee` (main at branch point) over
`src/market_sim scripts/run_calibration*.py scripts/lib data/raw/_validation-source data/raw/reference`:

| Commit | Hunks | Class |
|---|---|---|
| bdf44f8e / ee0c6971 NWPP-NEXT-9 | `coal_monthly_pile_measured_receipts` (default off, absent from recipe); plant-basis `source_sha256` only | INERT |
| 2ff9c9ae SPP-100 | `chp_steam_floor_conduct_scope` (default off, absent from recipe); `CHP_STEAM_ALLHOURS_MIN_ON_FRAC` appended to the solve surface at a frozen declaration | INERT |
| e9fc1a5e PJM-NEXT-8 | `unit_outage_exit_cohort_repair` (default off); every changed line in `arrays.py` / `outages.py` sits behind `_dated_shares is not None` / the flag | INERT |

**ALL INERT.** This lane's own diff is inert while the new key is off (it defaults off, and every path is gated).

## 4. Recipe (per shard, year Y)

Keeper #15's recipe (PRECOMMIT-nwppnext8 §5), plus one key:

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext10xy_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  --set nwpp_demand_plant_basis=true \
  --set coal_committed_nested_on_mustrun=true \
  --set admit_standby_units=true \
  --set nwpp_path76_alturas_link=true \
  --set coal_fuel_inventory_plant_grain=true --set coal_fuel_inventory_take_floor=true \
  --set coal_takeorpay_from_data=false --set coal_committed_takeorpay_regulated=false \
  --set coal_fuel_inventory_monthly_pile=true \
  --set unit_outage_exit_ym_from_eia860=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-10 exit-month routing: keeper #15 recipe + EIA-860 exit_ym routing of the CAMPD outage layer"
```

## 5. Hard stops (any miss means STOP, no push)

1. `git rev-parse HEAD` equals the pin.
2. `sha256sum data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` =
   `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`.
3. `scenario_config` in `run_config.json` differs from keeper #15's `run_config_<Y>.json` only in
   `unit_outage_exit_ym_from_eia860` (True). Keys absent in the keeper and False/None/default in the arm are also
   accepted (e.g. the retired `nyiso_firm_imports`).
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. P1 summed `demand` equals keeper #15 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 /
   302.532.
6. **Arm-live.** For 2020 the solve log carries `unit-outage exit_ym routing live (year 2020): plants [6076]`. For
   every other year it carries **no** `routing live` line; a `... row(s) stamped with a dated exit bin` line is allowed
   there, because it is inert without a live plant. Every year also carries the keeper's lines: `coal per-yard budget`,
   `coal take floor ... M yard rows floored` (M > 0), `coal monthly pile ... x 12 month-ends`, and
   `NWPP Path 76 (Alturas)`.
7. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
8. The solve is not infeasible. An infeasible or Unknown LP is a STOP, with the log reported and no retry.

## 6. Decision

The owner's standing ruling applies: promote if structural integrity improves, even if a gate regresses, and report
every regression at full magnitude. The arm's structural claim is that no NWPP plant-year is left available below its
own EIA-923 generation because of a double-counted exit. That is checked from the census, not from the score.
