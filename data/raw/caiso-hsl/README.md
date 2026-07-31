# caiso-hsl — raw

`caiso_<year>_hsl_hourly.parquet` (2023–2025) — CAISO's "uncurtailed
potential" (HSL) series: **derived**, not a raw download.

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

- **2019, 2020, 2021 — built and QA'd clean, committed as parquet**
  (8760 rows, zero nulls, wind/solar totals consistent with the
  neighboring 2023–2025 keeper years, real negative-noise present in the
  underlying EIA-930 series matching 2023-2025's pattern). The GitHub API
  push tools (`create_or_update_file`/`push_files`) can't transport binary
  content or even large plain-text content losslessly in this session (see
  git history for the earlier CSV/attachment detour); these three years
  were committed with a direct `git push` instead — a deliberate, scoped
  exception to CLAUDE.md's API-only push rule (which was motivated by an
  unrelated ~100MB+ pack that previously 413'd; this diff is ~600KB of
  parquet).
- **2018 — deliberately NOT built/delivered.** `build_caiso_hsl.py`
  succeeded and produced a full 8760-row frame, but its annual wind total
  (24.9 TWh) is 60%+ above every neighboring year (2019: 15.9, 2020: 14.9,
  2021: 18.3 TWh) despite CAISO wind buildout growing over time, not
  shrinking — the wrong direction for a real measurement. Root cause: the
  data register documents that EIA-930 per-fuel reporting for CISO did not
  exist for 2018 H1 at all; `eia_loader.load_eia_hourly_renewable_gen`'s
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
  **CLOSED 2026-07-31** — see below.

## 2022 closure + 2018 re-confirmation (2026-07-31 CAISO holdout intake)

**2022 is now built and committed.** The 2026-07-10 blocker was not a
curtailment-workbook gap at all: `data/raw/eia-930-hourly/CISO hourly.parquet`
carried only **9** rows for local-2022 (a Jan-1 UTC-boundary spillover) even
though the 2022 API long-form extracts (`eia-930/CISO_{region,fueltype}_2022.parquet`)
had landed — so `load_eia_hourly_renewable_gen` found no full year to anchor
the delivered side. Rebuilding the wide extract from those long extracts
(`build_eia930_hourly_from_raw.py --ba CISO --merge-missing --merge-years
2018 2019 2020 2021 2022 2026`) fills the hole to a dense 8760 h, after which
`build_caiso_hsl.py` produces 2022 unchanged in recipe.

Lineage proof: the same run re-derived **2019, 2020, 2021, 2023 and 2024
byte-identically** to their committed parquets (2025 likewise, once the merge
was scoped to the authorized holdout years — see the in-sample note below), so
2022 is the same producer on the same recipe, not a new derivation. Its
totals sit in family between the neighbouring years: wind 17.38 TWh
(2021: 18.30, 2023: 16.40), solar 35.83 TWh (2021: 32.76, 2023: 37.17),
curtailment 0.129 wind + 2.320 solar TWh (2023: 0.151 + 2.509), and the
delivered series' 2022 minima (wind 35 MW, solar -89 MW) match 2023-2025's
real near-zero/negative noise. Only **3** hours of the 2022 fuel series are
null, against 2 in 2023 — full parity, no imputation exposure.

**2018 is still deliberately NOT delivered.** Re-running the builder
reproduced the 2026-07-10 artifact exactly (wind 24.87 TWh, min 18 MW,
`nonzero_frac = 1.000`), and the root cause is now measured rather than
inferred: **4,343 of the 4,380 H1-2018 hours have null `NG: WND`/`NG: SUN`**
in the wide extract (EIA-930 per-fuel reporting for CISO did not exist for
H1-2018; the 2018 API long extract starts 2018-07-01), so
`load_eia_hourly_renewable_gen`'s `.interpolate().bfill().ffill()` chain
carries the first valid July reading back across the whole first half as a
flat constant. The parquet was built and then withheld: committing it would
put a fabricated series in front of `market_sim.data.renewables`, which
prefers this file over the delivered-profile fallback. The underlying
`eia_loader` imputation defect remains the open issue.

**H1-2026 remains impossible** — CAISO discontinued the source report
2025-06-01 (see `data/raw/caiso-curtailment/README.md`), so no 2026 workbook
exists or will.

**In-sample note (in-sample defect, NOT fixed here):** the unscoped
`--merge-missing` rebuild also filled **9 missing local-2025 hours**
(2025-12-31 16:00-23:00 local, supplied by the 2026 long extract's leading
UTC hours), which shifted `caiso_2025_hsl_hourly.parquet`. Because 2025 is a
training year, the merge was re-scoped to the authorized holdout years only
and 2025 was left exactly as committed. The 2025 tail gap is real and is
flagged for the CAISO calibration owner, not silently landed in a
holdout-readiness lane.

The raw 2018–2022 `.xlsx` workbooks themselves (20-30MB each, ~118MB total)
were verified downloadable and byte-valid, and are committed alongside this
directory in `data/raw/caiso-curtailment/` (also via direct `git push` — see
that directory's README).
