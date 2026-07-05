# Validation memo — CAISO Mode A degenerate-solution tiebreak fix (ADR 0019)

- **Date:** 2026-07-05
- **Scope:** follow-up to the 5-ISO backcast-validation extension
  (`docs/validation-2026-07-05-5iso-backcast-extension.md`), which flagged
  CAISO's Mode-A premium-cap frontier as a degenerate-solution artifact rather
  than fixing it. This memo records the fix (**ADR 0019**,
  `docs/decisions/0019-mode-a-build-tiebreak.md`) and a real-data before/after
  re-validation.
- **Result:** `config.build_tiebreak_epsilon` (flat per-MW, default `1e-6`,
  Mode A only) resolves the saturate-to-cap degeneracy; ERCOT's frontier is
  unchanged as a control.

## Why real DAM settlement prices, not the original modeled backcast LMP

The 5-ISO memo's CAISO/ERCOT 2024 series came from a one-off bridge script
(not committed) that re-solved each ISO's current calibration keeper via
`scripts.run_calibration.run_year` — a multi-GB, multi-minute market-sim
dispatch solve requiring the full CAMPD/EIA-860 data tree. Reproducing that
exact pipeline is out of scope for an LP-tool-side tiebreak fix (this session
worked only inside `scope2-lce-portfolio/`, per the fix's own scope).

Instead, this re-validation prices against **actual 2024 CAISO/ERCOT DAM
settlement prices** — real, non-modeled market data already present in the
repo (`data/raw/lmp-data/CAISO/CAISO_dam_hourly_2024.csv`,
`data/raw/lmp-data/DAMLZHBSPP_2024.zip`). This is a legitimate, real substitute
for validating the LP mechanism (the tiebreak doesn't care whether the price
series is modeled or measured), though it is **not** a byte-comparable
baseline to the committed `results/caiso_backcast2024_premiumcap/` bundle,
which priced against the market-sim's modeled backcast dispatch. Construction,
documented rather than hidden:

- **CAISO**: `interval_start_gmt` → naive local-standard-time via a fixed −8h
  offset (Pacific Standard Time year-round, no DST toggle, matching this
  tool's "local standard time, no DST" convention, ADR 0010); unweighted
  average of the three DAM trading hubs (NP15/SP15/ZP26) as an ISO-average
  proxy (no published zonal load weights available outside `market_sim`).
- **ERCOT**: the DAM settlement point `HB_BUSAVG` (ERCOT's own published
  ERCOT-wide hub average) directly, in prevailing local time as reported (no
  DST correction attempted — an accepted, disclosed ~1h phase-shift limitation
  around the two DST transitions).
- Both: the 2024 leap day is dropped and the series resampled to exactly 8760
  hourly points (`config.HOURS_PER_YEAR`).
- Real per-ISO 2024 CF profiles (`scripts/build_profiles.py --year 2024`,
  EIA-930-derived) and the same stylized 100 MW reference load
  (`scripts/make_reference_load.py`) as every other ADR-ratification run.

Both series land in the expected real-world range: CAISO mean $35.18/MWh
(min −$41.33, max $541.70); ERCOT mean $27.70/MWh (min −$2.28, max
$2,221.46) — plausible 2024 DAM levels for both ISOs (ERCOT's mean is close to
the modeled-backcast $30.14/MWh the ERCOT memo reported).

## Data-provenance note (unrelated to the tiebreak, found in passing)

The **committed** `results/caiso_backcast2024_premiumcap/CAISO_run_metadata.json`
shows `config.year = 2030` and `config.profile_shape_year = None` — so
`build_cf_matrix` looked for `CAISO_2030.parquet` (never built), silently fell
back to synthetic CF (`profile_source.source == "synthetic"`), and the
"CAISO 2024 backcast" bundle referenced by the 5-ISO memo was actually priced
against **synthetic**, not real, wind/solar shapes. ERCOT's companion bundle
got this right (`year=2024`, `profile_shape_year=2024`, `source: "real"`).
This is an unrelated invocation slip in the earlier session, not a tool
defect; this re-validation uses `year=2024`/`profile_shape_year=2024`
throughout.

## Sweep configuration

Both ISOs: `active_resources=None` (the table's minimal set — `solar_pv`,
`onshore_wind`, `battery_4h` — matching the original committed bundles' own
configuration), `excess_sale_fraction=1.0` (ADR 0005), Mode A premium range
`{1,2,5,7,10,15,20,30,40,50,75,100,150}` $/MWh (same extended range as every
other backcast-validation sweep).

## Results

### CAISO — before (`build_tiebreak_epsilon = 0.0`, reproduces pre-ADR-0019 behavior)

<!-- CAISO_BEFORE_TABLE -->

### CAISO — after (`build_tiebreak_epsilon = 1e-6`, ADR 0019 default)

<!-- CAISO_AFTER_TABLE -->

### ERCOT — control (`build_tiebreak_epsilon = 1e-6`, ADR 0019 default)

<!-- ERCOT_AFTER_TABLE -->

## Findings

<!-- FINDINGS -->

## What this does and doesn't validate

**Validates:** the ADR 0019 tiebreak resolves the saturate-to-cap degeneracy
on real 2024 CAISO price/CF data, and leaves ERCOT's frontier — already
non-degenerate — effectively unchanged (the tiebreak's own sizing rationale
predicts a numerically negligible difference on a real, non-degenerate
optimum; see ADR 0019). **Does not validate:** a byte-exact reproduction of
the original modeled-backcast CAISO/ERCOT bundles (this memo prices against
real DAM settlement data instead, per the scope note above) or Mode B /
storage-charge-policy interactions with the tiebreak (out of scope — the
tiebreak is Mode A-only by construction). As with every other backcast memo,
the market-sim **forecast** LMP path stays on hold (stakeholder, 2026-07-02).
