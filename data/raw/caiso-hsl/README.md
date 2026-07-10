# caiso-hsl — raw

`caiso_<year>_hsl_hourly.parquet` (2023–2025) / `.csv` (2019–2021) —
CAISO's "uncurtailed potential" (HSL) series: **derived**, not a raw
download.

`HSL = EIA-930 CISO delivered wind/solar generation + reported curtailment`
(from `data/raw/caiso-curtailment/`).

**Regeneration:** `python scripts/build_caiso_hsl.py` (see
`data/raw/caiso-curtailment/README.md` for its input). Matches the
`renewables._HSL_COLUMNS` schema.

**Consumer:** `scripts/curate_renewables.py` (`market_sim.data.renewables`
reads this in preference to the CAMPD-derived proxy when present).

## 2018–2022 holdout intake (2026-07-10, rule-22 pre-authorized)

CAISO's `productionandcurtailmentsdata_<year>.xlsx` source workbook (see
`data/raw/caiso-curtailment/README.md`) was verified fetchable for
2018–2022 at the same stable URL pattern already used for 2023–2025:
`https://www.caiso.com/documents/productionandcurtailmentsdata_<year>.xlsx`
(full Jan1–Dec31 coverage confirmed by direct read for all five years).
**H1-2026 is not fetchable: CAISO's own library page states "As of 6/1/2025
the ISO is no longer publishing this report."** — a genuine source
discontinuation, not a fetch gap (curtailment now only appears in CAISO's
daily renewables reports, a differently-shaped source; reconstructing an
hourly HSL series from those would be a new derivation project, out of
scope for this intake).

Running `build_caiso_hsl.py` against the fetched workbooks produced:

- **2019, 2020, 2021 — built and QA'd clean** (8760 rows, zero nulls,
  wind/solar totals consistent with the neighboring 2023–2025 keeper years,
  real negative-noise present in the underlying EIA-930 series matching
  2023-2025's pattern). Committed here as `.csv` — **not** `.parquet` —
  because this session's only available push mechanism (GitHub API
  `create_or_update_file`/`push_files`) transports file content through a
  JSON string field that does not survive raw binary content: a controlled
  round-trip test showed a NUL byte silently replaced with a space and a
  high/control byte dropped entirely. The real parquet output for these
  years carries ~20,000+ NUL bytes each, so pushing it through that
  mechanism would silently corrupt the committed file — a `git push` of
  this modest (~1MB) diff was not available as a fallback (CLAUDE.md
  restricts pushing to the API path only, a rule motivated by an unrelated
  ~100MB+ pack that previously 413'd). Plain CSV has no NUL/control bytes
  and round-trips the API path intact. **Regenerate the parquet locally**
  with `pd.read_csv(...).to_parquet(...)` (or re-run `build_caiso_hsl.py`
  once the raw xlsx workbooks below are restored) before treating these
  years as equivalent to the 2023–2025 parquet keepers.
- **2018 — deliberately NOT committed.** `build_caiso_hsl.py` succeeded and
  produced a full 8760-row frame, but its annual wind total (24.9 TWh) is
  60%+ above every neighboring year (2019: 15.9, 2020: 14.9, 2021: 18.3
  TWh) despite CAISO wind buildout growing over time, not shrinking — the
  wrong direction for a real measurement. Root cause: the data register
  documents that EIA-930 per-fuel reporting for CISO did not exist for
  2018 H1 at all; `eia_loader.load_eia_hourly_renewable_gen`'s
  `.interpolate().bfill().ffill()` fallback then carries the first valid
  H2 hourly reading backward across the entire missing H1 window as a flat
  constant (confirmed: the 2018 series never dips near zero — `min=18,
  nonzero_frac=1.0` — physically impossible for real wind output, vs.
  2019-2021's real near-zero/negative noise). This is a pre-existing
  `eia_loader` imputation defect surfaced by this intake, not something to
  paper over per CLAUDE.md's "never bury the error" rule — flagged here as
  a discovered issue for a future session, out of scope for this holdout
  fetch/verify-only task.
- **2022 — genuinely unavailable**, exactly as `build_caiso_hsl.py` itself
  reports (`SKIP 2022: no full-year EIA-930 'CISO hourly' wind/solar
  series`), consistent with the data register's note that CAISO's 2022
  EIA-930 per-fuel coverage remains incomplete.

The raw 2018–2022 `.xlsx` workbooks themselves (20-30MB each, ~118MB total)
were verified downloadable and byte-valid in this session but were **not**
committed to `data/raw/caiso-curtailment/` — the same binary-transport
constraint applies at a much larger scale. Re-fetch them directly from the
URL pattern above (unchanged, no auth) to regenerate 2018's raw source or
to rebuild any of these years' parquet locally.
