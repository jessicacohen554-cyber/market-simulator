# RESULT — F1: backcast heat-rate + EIA-860 vintage foundation (2026-09-24)

Executes `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.1
(deliverables 1–7). **Zero LP.** No keeper, registry, bundle or dashboard file touched.
Census tables and residual plant lists: [`census_summary.md`](census_summary.md) (generated
by `summarize.py` from the four `census_*.json` beside it, which `census.py` produces).

## Headline

- **D1 is gone.** Year-matched vintages 2019–2022 priced 95–100 % of every ISO's thermal
  nameplate at the `HEAT_RATE_BINS` class table; post-F1 the exact class-table share is
  **0.0–2.5 % in every ISO-year 2019–2025**, below the pre-F1 vintage_2023 bar in all 63
  ISO-years (exact measure). On the audit's coarser bin-value heuristic ERCOT 2024/2025 read
  3.3 / 4.1 % against a 3.1 % bar — the heuristic counts the SPP-49 simple-cycle floor clamp as
  "class table", and ERCOT's EIA-860 gas/coal rows are not dispatched (curated CAMPD bins).
- **D2 is gone.** Retiree class-table MW falls e.g. PJM 2019 **13,391 → 905**, MISO 2019
  **9,766 → 896**, ERCOT 2019 1,670 → 354; the remainder is plants with no in-window eGRID rate
  in ANY vintage 2018–2024 (listed in `census_summary.md`).
- **D3 is fixed.** NWPP and SOCO retiree rows: 0 → 93 units appended (Boardman 642 MW,
  Wansley 1,957, Gorgas 1,167, Hammond 953 …); every pre-existing row byte-identical.
- **D4 is fixed.** Every `campd_{ct,coal,st,cc}_heat_rates_<ISO>` and
  `chp_power_only_heat_rates_<ISO>` artifact now exists for every ISO with the class
  (44 artifacts; CAISO has no coal), derived over the union of the 2019–2025 backcast fleets
  with a pooled row and per-year rows.
- **Defaults flipped** for `mode == "backcast"` only; forecast / hindcast keys and behaviour
  byte-identical (tested).

## Deliverable by deliverable

**1. Year-matched eGRID heat rate (D1+D2).** One resolver, `market_sim.data.egrid`:
`resolve_plant_heat_rates` (same-year PLHTRT → nearest vintage, tie → earlier → NaN),
`egrid_vintage_for_eia860_dir` (`vintage_<Y>` → eGRID Y; canonical → eGRID 2024, the latest —
there is no eGRID 2025), `egrid_workbook_path` / `egrid_sheet_name`. The plausibility window
`EGRID_HR_WINDOW_BTU_KWH` moved there (re-exported unchanged from `process_eia860`).
`process_eia860._join_egrid_heat_rate(df, vintage)` is vintage-aware; the retiree parquet joins
per row at each unit's last operating year (`retiree_egrid_vintages`). The boundary repair
(`fleet/eia860.py::_egrid_boundary_hr_repairs`) now reads the ACTIVE table's own vintage
(sheets `PLNT<YY>`/`UNT<YY>`); the CT floor reads the joined rate, so it follows automatically;
the CHP derive reads each year's own vintage. Regenerated with the new
`--rejoin-heat-rate` mode, which rewrites ONLY `heat_rate` (verified column-for-column):
vintage_2018…2024, canonical, retiree parquet. Canonical boundary repairs under eGRID 2024:
same set {7350, 55641}, values 6.808 / 6.836 (were 6.918 / 6.880 under eGRID 2023).

**2. NWPP/SOCO retiree channel (D3).** Root cause at the membership seam: the retiree parquet
is filtered through `BA_CODE_TO_ISO` at BUILD time and every later write extended the committed
rows (`--retired-extend`), so BAs registered afterwards (17 NWPP BAs, SOCO) were never admitted
— the same build-time-scope defect `rescope_generator_table_from_parquet` repairs for the
vintages. Fixed the same way (`--rescope-retired-window`, strictly additive, from the committed
vintage_2019–2022 + canonical sheets, no re-fetch). The 2023–2025 gap for EXISTING BAs
(FINDING-xiso-fuelvintage-retiree-window §2) is deliberately left out of scope; under the new
default it no longer reaches a solve (2019–2024 read the vintage operable sheets; 2025 has no
retiree of that class).

**3. Measured CAMPD heat rates, every class × every ISO (D4).** The five derives now take their
target population from `scripts/lib/heat_rate_years.backcast_fleets` (each year's backcast fleet:
vintage_<Y> or canonical, plus the retiree channel), so pre-2023 retirees are covered. Artifact
layout: `year == 0` pooled over 2019–2025, `year == Y` from year Y's hours alone. **Minimum-hours
rule, no new threshold:** a per-year row exists exactly where the derive's OWN trust gate clears
on that year's hours by themselves (`_MIN_LOADED_HOURS` = 50 for CT, `_MIN_STEADY_HOURS` = 200 for
coal / ST / CC) — the same identification each derive already uses to decide whether a pooled
rate is trustworthy. Boundary guards kept: the CC unmetered-steam guard runs per year on that
year's own EIA-923 ratio; the ST capacity pairing is identified ONCE on pooled hours and reused
for year rows; CHP stays out of the CC scope; CHP rows are per eGRID vintage (basis check now
compares like with like) with a net-generation-weighted pooled row over the ok years. Loader:
`campd_bins._measured_rate_map` — solve year's own `ok` row, else pooled `ok`, else eGRID; a
pre-F1 artifact (no `year` column) reads as all-pooled. The solve year is threaded through
`_rows_to_generators(heat_rate_year=…)`, `apply_measured_chp_heat_rates(…, year)`, and the
retiree / mothball channels now take the same five measured flags. ERCOT artifacts were derived
too but are inert (ERCOT's gas/coal dispatch comes from the curated bins); ERCOT's measured
posture is R-ERCOT's.
Provenance recipes preserved: SOCO coal/ST/CC with their keeper flags, MISO CHP with
`--cc-steam-part-capacity`. One latent divide-by-zero in the CHP derive (a zero-heat eGRID row
in an older PJM vintage) guarded → `no_chp_credit`.

**4. Defaults.** `eia860_vintage_tracks_solve_year` and `measured_{ct,coal,st,cc,chp}_heat_rates`
default True; six `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entries dated 2026-09-24 with the
frozen drop value left at "False"; `__post_init__` coerces all six back to it whenever
`mode != "backcast"`. `PINNED_BACKCAST_CACHE_KEY` advanced with a cause block; the six are in
`_DECLARED_BACKCAST_COERCION_REKEYS`; cache-epoch ledger entry in `results/cache.py`. New CLI
`--[no-]eia860-vintage-tracks-solve-year`, `--[no-]measured-cc-heat-rates`,
`--[no-]measured-chp-heat-rates` on `run_calibration_full.py` (ct/coal/st already existed).
**`carry_operating_mothballs` is NOT flipped:** under the vintage default it is inert in every
year — 2019–2024 read `vintage_<Y>` itself, whose OA units are OA in the oracle file too
(`load_mothballed_but_operating` "self-neutralizes"), and 2025 has no `vintage_2025`. Flipping it
would re-key every backcast for zero behaviour.

**5. Census.** `census_summary.md`. Pre-F1 reproduces audit §3a/§3b to the MW.

**6. Matrix.** PJM `eia860_vintage_tracks_solve_year` **R → O** (the pjm-168 arm ran on 100 %
class-table heat rates). Every ISO shard's six cells carry the F1 note; no other verdict moved.
Base-row definitions record the default flip. `check_mechanism_matrix.py --base origin/main`
passes; anchors re-numbered by `--fix-anchors`.

**7. Tests.** `tests/unit/config/test_f1_backcast_heat_rate_vintage_defaults.py` (48): join,
fallback order, tie → earlier, per-row retiree join, rejoin touches only `heat_rate`, per-year
reader, backcast-only coercion, forecast/hindcast key byte-identity, explicit-False posture,
ledger/frozen-value declaration, and key stability over every committed keeper run_config (a
payload with any of the six absent hashes as its registration-time value — ERCOT and CAISO
keepers omit some). Updated for the intended changes: boundary-repair values, SOCO ST 2049
pooled value, retiree-window SHA (re-pinned to the heat-rate-less projection, verified equal
pre/post), and the plumbing / key tests that armed the flags on a forecast config.

## What moves (intended solve-input change)

Every ISO's keeper years move on re-solve: the vintage default changes the fleet source for
2019–2024, the eGRID join changes every EIA-860 table's heat rates (canonical now eGRID 2024),
and the measured artifacts change pooled windows and add per-year rows / new ISOs. The canonical
heat-rate change also reaches forecast solves (their flags stay off, but their snapshot's eGRID
rates are now eGRID 2024) — recorded as a same-key cache epoch. No solve-surface registry value
moved (`solve_surface_register.py --diff HEAD`: 0).

## Not done / handed on

- `egrid_family_heat_rates`, `egrid_steam_collapse_heat_rates`, `egrid_identity_heat_rates`
  artifacts keep their applied eGRID-2023 vintage (they are separate default-off mechanisms with
  their own derives); `zone_assignment` still reads PLNT23 for GEOGRAPHY (not heat rate).
- NWPP / SOCO per-year rows exist only where raw CAMPD exists (AL, GA, AZ, ID, OR, UT, WA, WY
  2019–2022 absent — F2's intake).
- The opt-in `data/clean` fleet (`MARKET_SIM_USE_CLEAN`, default off) was not regenerated.
- Pre-existing, not F1's: 9 `test_persisted_identity` failures on main (unregistered
  `coal_mustrun_requires_measured_row`, stale surface pins, an import cycle) — Y-28 (PR #6561)
  owns them. The F1 backcast pin is `a6b3a99fa1e558ce` on current main; on a Y-28 base it is
  `82031b392ddd276a` (measured, with the six at False reproducing `f61891696e671969` exactly).
