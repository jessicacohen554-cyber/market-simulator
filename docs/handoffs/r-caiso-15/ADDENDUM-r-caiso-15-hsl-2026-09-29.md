# ADDENDUM — R-CAISO-15 (2026-09-29): repair completed to the HSL generation term and the battery envelope

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

Checked against the keeper recipe (`rcaiso11_A_span/run_config.json`). "Late" = derived from EIA-930 CISO data inside the
generation window without passing the repair seam.

| # | Artifact (reader) | Hourly shape at solve? | Status |
|---|---|---|---|
| 1 | `data/raw/reference/caiso-storage-shape-envelope.csv` (`model/storage.py::caiso_storage_shape_caps`; keeper `caiso_storage_shape_anchor=true`). Builder `scripts/derive_caiso_storage_shape.py` reads raw `CISO hourly.parquet` `NG: OTH` by Local date/Hour, no seam | YES: per-(year, hour-of-day) p95 battery charge/discharge caps, 2023–25 | **GAP, live → REPAIRED (this lane, §7)** after the owner card |
| 2 | `data/raw/eia-930-interchange/CISO interchange hourly.parquet` (per-DIBA feed; `envelopes.measured_corridor_flow_envelope`, `measured_firm_import_shape`). Clock set by fixed lags `_CAISO_INTERCHANGE_LAG_STD_H=1` / `_DST_H=2` (`envelopes.py:885-890`), fitted against the unrepaired `Total interchange` | YES: month × hour-of-day | **GAP, live.** Under the arm the extract's interchange moves 1 h, this feed does not. Needs a lag re-scan against the repaired column |
| 3 | DSW clean-depth / surplus / wedge / import-tranche constants (`model/interchange/spec.py`) | No (one p95 per year; only the hour window is clock-dependent) | GAP, second-order; inherits #2 |
| 4 | `caiso_offer_surface_condbinned.json` (net-load bin join) | No (per net-load bin) | GAP, weak |
| 5 | CT-drag / ST-gas overnight drag scalars | No (regression scalars) | GAP, scalar |
| 6 | Solar-shape band 10/30 percentiles | No | N/A (clock-robust) |
| 7 | caiso-80 supply-consistent demand | YES | REPAIRED (R-CAISO-13) |
| 8 | `data/raw/caiso-hsl/*` | YES | **REPAIRED (this lane)** |
| 9 | `eia-930/eia_generation_profiles.parquet` etc. | YES | Dormant fallback, not reached for CAISO 2022–25 |
| 10–14 | storage-dispatch actuals (Outlook), Outlook fuelsource, intertie self-sched, CEMS/TAC artifacts, calibration_reference | — | N/A (not EIA-930, or scoring-only) |
| 15 | `data/clean/*` generation | YES | Inert (clean path off); clean renewables pass the HSL seam |

Live frame readers (demand, `caiso_solar_fraction`, WAT hydro envelope, `measured_interchange_envelope`,
`measured_gas_floor_profile`, `_eia_hourly_cf_profile`) are REPAIRED through the seam.

**Scoring side.** C4 gas NRMSE for CAISO 2023+ is scored against CEMS bench gas + flat cogen
(`calibration_verdict.py`), not the EIA-930 NG cell, so the arm does not move the benchmark. The in-solve e930 bench
is built after the arm is set (repaired). The zero-LP benchmark rebuilds (`build_benchmark_frames`,
`--rebuild-benchmark`, `restore_shared_inputs`, `build_bench_part_zero_lp.py`, `regen_caiso_bench_cems.py`) do NOT arm
the repair: a rebuild of an armed bundle would regenerate the e930 bench unrepaired.

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

## 7. Scope widened by owner card (2026-09-29, after the census): "Add battery envelope"

- **Build (same flag, zero parameters):** `model/storage._caiso_storage_envelope_clock_repaired`, called from
  `caiso_storage_shape_caps`. Armed and the envelope year reaching the window → the derive script's own construction
  (Local date/Hour order, NaN→0, canonical EIA-860 battery fleet by month, per-hour-of-day p95, 4 dp) re-run on the
  extract after `frames._repair_clock_late_windows`. The committed CSV is not modified. A non-canonical EIA-860 vintage
  raises (the keeper uses the canonical one).
- **Precondition, measured and pinned by test:** on the unrepaired extract the reader's derivation reproduces the
  committed `chg_frac_p95` / `dis_frac_p95` exactly (max |Δ| 0.0) for 2023, 2024, 2025.
- **Effect (zero-LP):** 2024–25 caps become the committed caps rolled one hour earlier (e.g. 2024 discharge p95 peak
  0.66 moves from h19–20 to h18–19). 2023 changes in hours reached by Nov–Dec (max |Δ| 0.11).
- **Arm liveness, envelope entries changed (of 48):** envelope year 2023 → 34; 2024 → 40; 2025 → 38.
- **P4 amended (before any solve).** 2019–22 solves borrow the **2023** envelope (`caiso_storage_shape_anchor=true` in
  every keeper year), so they are no longer expected to be byte-identical. **P4′:** 2019–22 move only through the
  battery caps; HSL, demand and frame are unchanged there. Reported at full magnitude, not a criterion.
- **Left for the next link (recorded, not built):** #2 per-DIBA interchange lag re-scan, and its dependants #3; the
  weak/scalar gaps #4–#5; the zero-LP benchmark-rebuild seam.
