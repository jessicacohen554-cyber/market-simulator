# ADDENDUM — R-CAISO-15 (2026-09-29): repair completed to the HSL generation term

Extends `docs/handoffs/r-caiso-13/PRECOMMIT-r-caiso-13-2026-09-28.md` and
`docs/handoffs/r-caiso-14/ADDENDUM-r-caiso-14-gdrift-2026-09-29.md`. Written before any shard is launched.
Owner card 2026-09-29: "Complete repair, re-solve". §3 predictions and decision rule are reused **unchanged**.

## 1. The build (zero parameters; rules 14, 19, 23)

- **Same flag, one mechanism (rule 19):** `caiso_eia930_clock_repair`. No new field, no new constant.
- **Where:** `renewables.load_hsl_hourly` → `_repair_caiso_hsl_clock` (reader seam; raw and clean sources both pass).
  The parquet on disk is not rewritten (rule 23).
- **What:** when armed and `iso == "CAISO"` and the year's stamps reach `EIA930_CISO_CLOCK_LATE_WINDOWS_UTC["generation"]`:
  - `*_gen_mw` is re-read from `load_eia_hourly_renewable_gen("CAISO", year)`, whose frame the seam
    (`frames._repair_clock_late_windows`) has already repaired. That is the frame seam's own row mapping, seam hour and
    year edge, not a second implementation.
  - curtailment `*_hsl_mw − *_gen_mw` (CAISO 5-min, model clock) is kept; `*_hsl_mw` = repaired gen + curtailment.
- **Precondition, measured:** the file's `wind_gen_mw` / `solar_gen_mw` are **byte-identical** to the unarmed loader in
  every year 2019–2025 (max |Δ| = 0.0, 0 rows differ). Pinned by
  `test_live_hsl_precondition_file_gen_is_unarmed_loader`.
- **Fail-closed:** armed, in-window, no repaired series → `RuntimeError`, never a silent fallback.

## 2. Measured effect on the HSL frame (zero-LP)

Monthly solar centroid, h PST (hour-beginning + 0.5), `solar_gen_mw`:

| Year | Off | Armed |
|---|---|---|
| 2019–2022 | unchanged | frame-equal (same object) |
| 2023 | Nov/Dec 12.63 / 12.78 | Nov/Dec 11.62 / 11.77 (Jan–Oct unchanged) |
| 2024 | 12.54–13.00 | **11.52–12.00** |
| 2025 | 12.58–13.00 (Dec 11.86) | **11.57–11.99** (Dec 11.81) |

Curtailment totals (wind, solar): Δ = 0.0 MWh every year.

## 3. Arm-liveness hard stop (per year)

Output: `Demand` frame rows, `NG: SUN` frame rows, caiso-80 SC demand rows, **HSL solar rows**, **HSL wind rows**.

| Year | Output |
|---|---|
| 2019 / 2020 / 2021 | `0 0 0 0 0` |
| 2022 | `4776 0 0 0 0` |
| 2023 | `8752 1140 1465 1140 1454` |
| 2024 | `8758 7666 8755 7664 8743` |
| 2025 | `8049 6943 8051 6943 8031` |

The first three columns equal R-CAISO-14's. (2024 HSL solar 7,664 vs frame 7,666: the frame count is on the
pre-interpolation columns.)

## 4. Census of other CAISO consumers of EIA-930-derived artifacts

CENSUS_PLACEHOLDER

## 5. G-DRIFT 332c8048 → pin

PIN_PLACEHOLDER

9 non-merge commits touch the solve-path set between `332c8048` and `2cc1e2ae`. Every hunk is INERT for a CAISO
backcast.

| Commit | Verdict | Gate |
|---|---|---|
| 159696a8 R-ERCOT-14 | INERT | `ercot_swcap_vintage` (default off); `shed_penalty_voll` returns `iso_config.voll` for every non-ERCOT solve |
| edbfdad5 / 3c398753 R-ERCOT-14/15 | INERT | `ISO_PLANT_EXITS` has an ERCOT key only (`plant_exit_first_outside_row` empty for CAISO); Oklaunion/Sandy Creek rows are ERCOT plants; bin-assignment and DAM-crosswalk rows are ERCOT |
| bdf44f8e / ee0c6971 NWPP-NEXT-9 | INERT | `coal_monthly_pile_measured_receipts` (default off, plant-grain coal path); `nwpp_plant_basis_energy.csv` is NWPP |
| c1cb07f0 soco-88 | INERT | SOCO rows in `iso-gas-capacity-state-weights.csv` only |
| 196d1e69 / c23608b8 spp-102 | INERT | `spp_commitment_posture` (default off). `_standalone_posture_pools` refactor keeps ERCOT's call byte-identical; `zero_posture_markup` returns the same object when the field is off; LP min-up/down columns gated on `standalone_posture` |
| 70baf173 NYISO-NEXT-12 | INERT | `nyiso_ne_ac_node` and `iso == "NYISO"` |
| this lane | THE ARM | `renewables._repair_caiso_hsl_clock`, under the existing flag |

No `ScenarioConfig` default flip. Solve-surface: the two new names (`ISO_PLANT_EXITS`, `SPP_POSTURE_MIN_DOWN_HOURS`)
carry no CAISO rows.

**Result:** form 4 is valid; the keeper's committed bundles are the control (rule 29(b)).

## 6. Solve

7 shards, one per year 2019–2025 (rule 36), prompt `docs/handoffs/r-caiso-15/shard-prompt.md`, out-dir
`rcaiso15_A_{Y}`, branch `claude/r-caiso-15-A-{Y}`. `{SRC}` = `rcaiso11_A_tp_2019_2021` (2019–21) /
`rcaiso11_A_span` (2022–25); `{SDCAP}` = 1436.0 (2019–23) / 2074.0 (2024) / 2071.0 (2025).
