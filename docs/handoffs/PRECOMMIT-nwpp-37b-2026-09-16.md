# PRECOMMIT — lane NWPP-37: route every EIA-930 fuel-column reader through the unit-slip screen

Lane NWPP-37 · model Fable (`claude-fable-5-1`) · branch `claude/charming-cannon-q5hkxw` (the
session's designated branch; the charter's `claude/nwpp-37-envelope-screen-<4>` stem was
superseded by the session's branch assignment) · base `6d1a144d62949b53af088df51787de68d2edf738`
(= `origin/main` at issuance; the desk's pin `02c08154` is an ancestor — `git log
HEAD..origin/main` is empty) · DATA PROFILE nwpp (the clone is full; every region's
`<BA> hourly.parquet` is on disk, so the nine-region table is measurable here).

Written BEFORE any source edit. Every number in §1–§3 was measured at the base sha; §4–§6 are
pre-registered and cannot be rewritten to fit the result.

## 0. First duty — the desk's diagnosis, re-verified at my own base sha

**Confirmed.** `actuals._screen_fuel_spike_columns` (actuals.py:219) is applied at exactly three
call sites, all in `actuals.py`: `:351` (`_ercot_hourly_frame_screened`), `:412`
(`load_eia_hourly_benchmark`), `:488` (`load_eia_hourly_renewable_gen`).
`frames._eia_hourly_frame_filled` (frames.py:405-459) does no screening: it returns the strict
cached frame when one exists, else reindexes the present rows onto the complete hourly clock. Its
docstring says exactly that and nothing about the screen. The actuals docstring's claim "no
consumer can reach an unscreened copy" is therefore true of `actuals.py` readers only.

Measured cost at the base sha (the BEFORE run, `scratchpad/before.json`, all nine regions ×
2019–2026, screen applied to the frame the seam hands out): the columns a frames-seam reader
currently reads UNREPAIRED are listed in §3. For NWPP the AVA 2025 `NG: WAT` hour reads
810,113 MW against the member's own p99.9 of 1,137 MW (712×; the desk's "~1,350×" was against a
smaller robust-peak estimate — the order of magnitude is the point and it stands).

## 1. Enumeration — every `src/` reader of a frames.py frame, classified at `6d1a144d`

`grep -rn "_eia_hourly_frame_filled\|_eia_hourly_frame(\|_ercot_hourly_frame(" src/market_sim/`.
Classes: **F** = reads an `NG: <CODE>` fuel column (must be screened); **T** = reads only
`Demand` / `Total interchange` / `Net generation` / the clock columns (outside the screen by
ruling P9; inert to it by construction); **S** = already screened at its own read.

| # | site | function | columns read | class | screened today? |
|---|---|---|---|---|---|
| 1 | envelopes.py:109 | `measured_monthly_hydro` | `NG: WAT` | **F** | NO |
| 2 | envelopes.py:167 | `_hydro_wat_month_hod` → `measured_hydro_hourly_envelope`, `measured_hydro_min_flow_level` | `NG: WAT` | **F** | NO |
| 3 | envelopes.py:371 | `measured_interchange_envelope` | `Total interchange` | T | n/a |
| 4 | envelopes.py:440 | `measured_gas_floor_profile` | `NG: NG` | **F** | NO |
| 5 | envelopes.py:1050 | `caiso_solar_fraction` | `Demand`, `NG: SUN` | **F** | NO |
| 6 | envelopes.py:1639 | `_eia930_net_interchange` (NYIS/ISNE/SWPP/SOCO schedules) | `Total interchange` | T | n/a |
| 7 | envelopes.py:1883 | `nwpp_net_interchange` | `Total interchange`, `UTC time` | T | n/a |
| 8 | neighbor_price.py:396 | `_neighbor_load` (net kind: WECC_DSW, `SRP`→proxy `CISO`) | `Demand`, `NG: SUN`, `NG: WND` (:407-408) | **F** | NO |
| 9 | neighbor_price.py:574 | `caiso_hub_load_shape` (net kind: PALOVRDE hub, `CISO`) | `Demand`, `NG: SUN`, `NG: WND` (:580-581) | **F** | NO |
| 10 | virtual_bids.py:274 | `_hour_index_map` | `Local time` | T | n/a |
| 11 | zonal_shares.py:384 | `_miso_utc_to_local_hoy` | `UTC time` | T | n/a |
| 12 | demand.py:229 | `_load_ercot_hourly` (via `_ercot_hourly_frame`) | `Demand`, `Total interchange` | T | n/a |
| 13 | demand.py:343 | `_load_caiso_hourly_demand` | `Demand`, `Local date` | T | n/a |
| 14 | demand.py:390 | `_load_nyiso_hourly_demand` | `Demand` | T | n/a |
| 15 | demand.py:526 | `_load_neiso_hourly_demand` | `Demand` | T | n/a |
| 16 | demand.py:560 | `_load_miso_hourly_demand` | `Demand` | T | n/a |
| 17 | demand.py:600 | `_load_spp_hourly_demand` | `Demand` | T | n/a |
| 18 | demand.py:632 | `_load_nwpp_hourly_demand` | `Demand` | T | n/a |
| 19 | demand.py:679 | `_load_soco_hourly_demand` | `Demand` | T | n/a |
| 20 | demand.py:735 | `_load_pjm_hourly_demand` | `Demand` | T | n/a |
| 21 | actuals.py:348 | `_ercot_hourly_frame_screened` → the five ERCOT readers | every `NG:` | S | yes (:351) |
| 22 | actuals.py:405 | `load_eia_hourly_benchmark` (reads the parquet itself, NOT frames — it tolerates a short / partial year) | every `NG:` | S | yes (:412) |
| 23 | actuals.py:485 | `load_eia_hourly_renewable_gen` | `NG: WND`, `NG: SUN` | S | yes (:488) |
| 24 | frames.py:295 | `_pool_member_frames` (clock member only) | `UTC time` | T | n/a |
| 25 | frames.py:263→312 | `_pool_hourly_frame` (members re-read from parquet, summed) | every `NG:` of 17 members | **F** | NO — the pool sums RAW member columns |

**Count against the desk's:** the desk named 7 envelopes + 2 neighbour + 1 virtual_bids + 1
zonal_shares + 8 demand = 19 direct `_eia_hourly_frame_filled` reads. Measured: 19, exactly. Of
those, **six are fuel-column readers** (rows 1, 2, 4, 5, 8, 9) — the desk's "at least the
neighbour-price solar/wind series" was right, and `caiso_solar_fraction` (row 5) is the one the
desk's list did not name. The demand.py docstrings that say the renewable CF series are "drawn
from the same frame" describe the `actuals.load_eia_hourly_renewable_gen` path (row 23), not a
read inside demand.py: **all eight demand.py reads are class T.** Row 25 is the seventh
fuel-column reader and the one that matters most for NWPP: the pool constructor itself sums
unscreened member columns, so even a pool-level screen would see the members' slips only after
dilution by sixteen other BAs.

Direct `_eia_hourly_frame` (strict, raw) readers outside frames.py: `actuals._ercot_hourly_frame`
(row 21, screened downstream), `scripts/data/build_calibration_reference._pool_hourly_benchmark`
(:847-856, screens per member itself — the per-member precedent), and
`scripts/data/derive_neiso_offer_surface._netload_pct` (:196, `Demand − NG: WND − NG: SUN`; a
rule-23 frozen derive script, not in FILES YOU OWN, ISNE has zero flags in every year so a
re-derive would be byte-identical).

Script readers of `_eia_hourly_frame_filled` (out of scope, listed so the seam change is
auditable — they inherit whatever the seam returns): fuel-column consumers are
`derive_caiso_offer_surface`, `derive_pjm_offer_surface`, `derive_miso_offer_surface`,
`derive_neighbor_convexity`, `derive_caiso_solar_shape_band`, `derive_caiso_supply_consistent_demand`
(`NG: NG`), `build_nwpp_hydro_budget` (per-member `NG: WAT`), `scripts/lib/wind_shape`
(`NG: WND` via the ISO's BA), and the four `scripts/probes/` files. Clock/demand-only:
`curate_zonal_shares`, `derive_pjm_da_virtual_surface`, `build_calibration_reference:462`.

## 2. The shape — (A), and the rule that decides it

**(A) STRUCTURAL is taken iff the AFTER measurement (§5) shows every non-NWPP reader output
byte-identical.** If any non-NWPP reader moves, the lane reports the mover and falls back to (B).

I agree with the desk's position, on the enumeration rather than on preference: with seven
fuel-column reader sites across four modules plus the pool constructor, (B) is seven patches that
the next `frames` importer silently reopens (and the scripts list above shows how many importers
there are). (A) makes the docstring's existing single-seam claim true. §3 predicts (A) is clean
for every pre-existing region because the columns that flag in those regions have **no
frames-seam reader** — that prediction is what §5 tests.

The seam, stated so it can be checked against the diff:

1. `frames._eia_hourly_frame` (strict, cached) STAYS RAW. It is the substrate `_ercot_hourly_frame`
   builds on before the measured long-format fill, and the screen must see every raw observation
   (the fill adds some) before it runs — the order the SPP-41 docstring already calls load-bearing.
2. `frames._eia_hourly_frame_filled` applies the screen to every non-pool frame it returns (both
   the strict-passthrough and the reindexed branch), via a lazy in-function import of
   `actuals._screen_fuel_spike_columns` — the same pattern this file already uses for
   `demand._screen_demand_dropouts`, because `actuals` imports `frames` at module level and the
   factor is bound BY IMPORT from `demand` (rule 19: no re-spelled threshold; the function, its two
   constants and the test that pins `_FUEL_SPIKE_RATIO is _DEMAND_SPIKE_THRESHOLD` are untouched).
3. `frames._ercot_hourly_frame` applies the screen AFTER the long-format fill; `actuals.
   _ercot_hourly_frame_screened` is deleted and the five ERCOT readers call `_ercot_hourly_frame`.
4. `frames._pool_member_frames` screens EACH MEMBER before the sum (the NWPP-10 dropout precedent
   and the `build_calibration_reference._pool_hourly_benchmark` precedent), and bridges a flagged
   member hour by that member's own linear interpolation at the flagged hours ONLY — the fill a
   single-BA reader applies, restricted so the pool's other NaN semantics (`min_count=1` sums; a
   storage series that has not started reporting) are untouched. A pool frame is NOT screened a
   second time at pool level (rule 19: one application per series; per-member is provably at least
   as strong for a non-negative column since member p99.9 ≤ pool p99.9).
5. `actuals.load_eia_hourly_renewable_gen` drops its now-redundant call (:488).
   `actuals.load_eia_hourly_benchmark` KEEPS its call (:412): it reads the parquet directly because
   it tolerates a short or partial year the frames loaders reject, so its frame never comes from
   the seam — documented as the one reader that screens at its own read, and why.
6. Docstrings: `actuals` module + `_screen_fuel_spike_columns` + `load_eia_hourly_renewable_gen`;
   `frames` module + `_eia_hourly_frame` + `_eia_hourly_frame_filled` + `_pool_member_frames` +
   `_pool_hourly_frame` + `_ercot_hourly_frame`; the four envelope readers (rows 1, 2, 4, 5).
   `neighbor_price.py`, `virtual_bids.py`, `zonal_shares.py`: **no edit** — their reads arrive
   screened by construction under (A).

No threshold, statistic, per-region branch or `ScenarioConfig` field changes. No matrix row.

## 3. What is EXPECTED to move — pre-registered from the BEFORE run

Columns the screen flags on the frame the seam hands out (per region × year, 2019–2026; a region
absent from this list flags NOTHING in any year — ERCOT, CAISO, PJM, MISO, NEISO all read `{}`
in every year 2019–2025 and have no 2026 frame):

| region | year | column | hours (0-based model clock) | max vs p99.9 (MW) | frames-seam reader of that column |
|---|---|---|---|---|---|
| NYISO | 2024 | `NG: OTH` | 6759 | 16,117 vs 3,290 | none |
| SPP | 2023 | `NG: WND` | 3907 | 3,589,445 vs 22,597 | none in src (scripts: `wind_shape`, a frozen derive) |
| SOCO | 2023 | `NG: OIL` | 7975 | 390 vs 88 | none |
| SOCO | 2024 | `NG: OIL` | 386–392 | 801 vs 72 | none |
| SOCO | 2025 | `NG: NG` | 1172, 1240, 2751, 7527 | 70,683 vs 26,642 | `measured_gas_floor_profile` is generic but its only caller is CAISO's RA floor → no consumer |
| NWPP | 2023 | member PGE `NG: OTH` | 732 | 119 vs 33 | pooled OTH: none |
| NWPP | 2024 | AVA `NG: OTH` 97–102; IPCO `NG: OIL` 298; NWMT `NG: COL` 4354; NWMT `NG: WAT` 5556, 5723, 6707, 7603; NEVP `NG: NG` 3663; NEVP `NG: OIL` 82 | — | NWMT WAT 65,891 vs 641; NEVP NG 63,796 vs 8,614; NWMT COL 21,625 vs 1,581 | **WAT → rows 1, 2 (hydro budget repin, envelope, min-flow); NG → row 4** |
| NWPP | 2025 | AVA `NG: WAT` 6817, 6818; AVA `NG: OTH` 2669; NWMT `NG: COL` 4523; NWMT `NG: WAT` 6874, 6875, 7236, 8052; NEVP `NG: NG` 3990, 4339, 4865, 6184, 7748 | — | AVA WAT 810,113 vs 1,137; NWMT WAT 99,225 vs 659; NEVP NG 66,310 vs 8,389 | **WAT → rows 1, 2; NG → row 4** |

Two things this table establishes before the patch. (i) The SPP-41 control set (SPP 2023 wind,
NYISO 2024 other, NYISO H1-2026 other, one delivered wind profile) is reproduced on the bench
path, and **SOCO adds three column-level entries to it** — SOCO was registered 2026-09-14, after
SPP-41 measured "all seven ISOs" on 2026-09-07, and its bench path ALREADY carries these repairs
today (the BEFORE run's `bench` control logs them); they are the same defect class and not a new
effect of this lane. (ii) A pool-LEVEL screen would catch only 2 of NWMT's 4 hydro hours in 2024
and 3 of the 6 hydro hours in 2025 (the pool p99.9 is 19,533 / 23,358 MW, so 65,891 MW passes a
2.5× bar there and fails a 641 MW member bar by 100×) — the per-member construction is required,
not preferred.

Predicted reader-level movers: **NWPP only** — `measured_monthly_hydro` 2024 and 2025 (and the
2019–2022/2026 climatology fallbacks of `measured_hydro_hourly_envelope` /
`measured_hydro_min_flow_level`, which pool 2023–2025), `_hydro_wat_month_hod` 2024/2025,
`measured_gas_floor_profile` NWPP 2024/2025 (no caller), and the pooled `NG: COL/OTH/OIL` columns
(no reader). Predicted BYTE-IDENTICAL: every reader output for ERCOT, CAISO, PJM, MISO, NYISO,
NEISO, SPP, SOCO in every year; every `bench` and `renewable_gen` control everywhere; every
class-T reader everywhere including NWPP.

The NWPP-32 §3.2 number this lane exists for: October 2025 pooled hydro carries **+1,166 GWh
(14.1 %)** of phantom energy from the AVA hour. The AFTER run reports `measured_monthly_hydro
("NWPP", 2025)[9]` before → after at full magnitude.

## 4. Gates (stop rules, structural, never on a residual)

- **G1 byte-identity**: for every `(iso, year)` with `iso ≠ NWPP`, every reader digest in
  `after.json` equals `before.json`. One mismatch ⇒ (A) is refused, (B) taken, the mover named.
- **G2 control set**: `bench` and `renewable_gen` digests equal before/after for ALL nine regions
  (they were screened before and are screened after; (A) must not move them).
- **G3 column-level**: the set of `ng_cols` digests that differ between before and after is
  exactly the §3 table (single-BA rows) — nothing beyond it.
- **G4 NWPP direction and magnitude**: after − before of `measured_monthly_hydro("NWPP", 2025)[9]`
  is negative and within ±5 % of −1,166 GWh (the AVA hour's 810,113 + 190,346 MW against the
  member's interpolated ~1 GW), and no NWPP class-T reader moves.
- **G5 tests**: the existing screen tests pass with the one seam-property test rewritten to the
  new (true) property; new tests pin that each envelope reader, the pool member path and the
  frames seam are screened, and that the strict raw cache is not mutated.
- **G6 ruff clean** on every touched file.

## 5. Measurement protocol

`scratchpad/measure_seam.py before` was run at the base sha (done). After the patch,
`measure_seam.py after` runs with the identical script; `diff_seam.py` compares every digest and
prints the nine-region table §4 needs. The BEFORE artefacts are not regenerated after the patch.

## 6. Files this lane touches — and nothing else

`src/market_sim/data/eia930/{frames,actuals,envelopes}.py`,
`tests/unit/data/test_eia930_fuel_spike_screen.py`, this PRECOMMIT, `FINDING-nwpp-37-2026-09-16.md`.
Not touched: `demand.py` (the two demand screens are a different phenomenon),
`neighbor_price.py`, `virtual_bids.py`, `zonal_shares.py`, any registry/config/ScenarioConfig,
`scripts/calibration_verdict.py`, `frontend/data/**`, the plan, the ledger, any matrix file.
