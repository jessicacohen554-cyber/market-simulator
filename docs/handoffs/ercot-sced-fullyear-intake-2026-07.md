# ERCOT full-year 60-Day SCED Disclosure intake + SCED-basis extension to 2023 (2026-07-21)

## What landed

The owner uploaded the full-year **60-Day SCED Disclosure — Gen Resource Data
(NP3-965)** corpus to `data/raw/ercot/` (committed directly to `main` via the
GitHub web UI as `Add files via upload`). It replaces the earlier 4 scoped
sample-day extracts that the RT/SCED offer wall was built from.

- **799 parquet shards**, ~3.26 GB, named `YYYY-MM.partNNNN.parquet`.
- 187 columns: `SCED1/SCED2 Curve-MW/Price 1..35`, `HSL/HASL/HDL/LSL/LASL/LDL`,
  `Base Point`, `Telemetered Resource Status/Net Output`, AS responsibilities,
  `Submitted TPO`, startup offers. All string-typed (raw copy).

### Naming ≠ delivery date (the load-time gotcha)

The `YYYY-MM` in a filename is the **publication month**. NP3-965 posts ~60 days
after delivery, so a file's rows carry delivery timestamps ~2 months earlier —
e.g. `2023-02.part*` holds **Nov/Dec 2022** delivery rows. Files are therefore
selected by a publication *window* and rows are filtered to the exact **delivery
year** read from `SCED Time Stamp` (`_delivery_year_rows`). This is what keeps
the **validation-holdout (2022)** and **locked-test (2026)** rows that ride in
adjacent publication files out of the training-year surfaces (rule 22).

Timestamps in this corpus are `MM/DD/YYYY HH:MM:SS` (the legacy sample-day
extracts were ISO `YYYY-MM-DD`); the year is extracted as the sole 4-digit run,
robust to both.

### Delivery-year coverage (parsed from timestamps)

| Delivery year | Rows | Coverage | Use |
|---|---|---|---|
| 2022 (Nov–Dec) | 4.5M | partial | **validation holdout — excluded from derives** |
| 2023 | 34.9M | all 12 months | training ✅ |
| 2024 | 35.4M | complete except **2024-05 sparse (109k)**, 2024-02 half | training ✅ |
| 2025 | 38.1M | Jan–Oct full, **Nov partial (131k), Dec absent** | training ✅ |
| 2026-04/05 | — | held back on disk | **locked test — excluded** |

2025 Nov/Dec are absent because they publish ~Jan–Feb 2026, past the corpus
cutoff. This is disclosed in each artifact's per-(class×bin) coverage.

## What changed in code

`scripts/data/derive_ercot_sced_offer_wall.py` (CC/CT) and
`derive_ercot_sced_offer_wall_steam.py` (steam leg):

1. **File selection + delivery-year filtering** — publication-window glob, exact
   delivery-year row filter, full-year corpus *supersedes* the legacy sample-day
   extracts (unioning both would double-weight those days).
2. **Numeric coercion** — the corpus stores unused curve steps as empty strings;
   coerced `'' → NaN` at load (the segment builder already treats NaN as absent).
3. **Streaming rewrite** — the non-streaming full-year build **OOM'd at ~12 GB**.
   `derive_year` now streams one shard at a time, accumulating only the compact
   `(mult, mw)` arrays + interval/day sets per `(class, bin)`. Peak RSS **0.77 GB**
   (CC/CT) / **0.74 GB** (steam).
4. **Two new gas-steam resources** surfaced by the full-year corpus —
   `SL_SL_G3`, `SL_SL_G4`, both max HSL = 0.0 (registered but non-operating,
   like the CFB zero-CEMS note), belonging to no model ST_GAS plant — reviewed
   and classed **non-fleet** (excluded + disclosed), per the map's
   review-on-source-update discipline (rule 23).

## SCED basis extended to 2023 (authorized methodology change)

Both walls were year-scoped to 2024/2025 with 2023 deliberately barred (the
post-Uri regime clause, charter §3.4/§5) — a *methodology* bar, not just a data
gap. With full-year 2023 now in hand, the **owner authorized extending the SCED
basis to 2023** (this session). The CC/CT wall's apply seam is presence-keyed by
year (`data/fleet.py:4177`, no year gate), so the 2023 block auto-applies for
2023 solves; bin geometry is shared with the DAM wall by construction and the
apply-seam assertion still holds.

- **Rule 24 gate:** the 2023 extension is a structural mechanism change — it must
  be scored **leave-one-year-out within 2023–2025** before any keeper promotion.
- The **steam** artifact has **no apply path in `src/`** (measure-first, step-2
  arming owner-gated per ERCOT-92); re-deriving it keeps it in sync with the
  CC/CT wall but **changes no solve**.

## Verification

- CC/CT: full-year interval counts (8751/bin vs sample-day 356); mid-band
  q90 exceeds DAM for all years incl. 2023 (e.g. 2023 bin −3: RT 512 vs DAM 23).
- Tests: `tests/test_ercot_offer_surface_cleared_share_rt.py` (13),
  `tests/test_derive_ercot_sced_offer_wall_steam.py` (9) — all pass.

## Next (handoff to a fresh session): re-solve + register

The re-solve reads the refreshed CC/CT wall + the `ercot91` keeper config (which
already has `ercot_offer_surface_cleared_share_rt: true`). It does **not** need
the raw SCED shards on disk once the wall JSON is present. Since the derived wall
JSONs are regenerable from the committed derive code + the committed raw shards,
the fresh session re-derives them first (2 commands, ~2 min), then reproduces
the keeper via `scripts/replay_keeper.py` on
`results/calibration/ercot91_seasonal_drag_fullspan`, years 2023 2024 2025
(sequential, per-year with `--reuse-solved`, fresh `--out-dir`), scores, then
registers on the backcast dashboard (rule 15). The delta being measured: 2023
now on the SCED basis + 2024/2025 refreshed from full-year vs sample days.
