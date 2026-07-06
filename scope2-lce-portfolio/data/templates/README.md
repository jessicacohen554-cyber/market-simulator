# Input templates

Draft (fillable) templates for the two user-supplied inputs. Each shows the
exact column contract with a few illustrative rows — **replace the example
rows with your data**. Both CSV and Parquet are accepted anywhere a path is
given (extension-detected). The full schema/validation rules live in
`src/lce_portfolio/intake.py` (ADRs 0010/0011) and `docs/02-data-inputs.md`.

Calendar convention (all files): `hour` is an integer `0..8759`, local
standard time, single representative non-leap year — no DST, no leap day.
**Every (iso, hour) must be covered for all 8760 hours** — missing hours are a
hard error, never a zero-fill.

## 1. `load_8760_by_facility_template.csv` — 8760 load by ISO and facility

| column     | type  | notes |
|---|---|---|
| `hour`     | int   | 0..8759, every hour present per ISO |
| `iso`      | str   | `ERCOT`, `CAISO`, `PJM`, `MISO`, `NYISO`, `NEISO` (or `SAMPLE`) |
| `facility` | str   | optional facility/site ID — any string key |
| `load_mwh` | float | that facility's load in that hour, MWh |

**Auto-aggregation:** intake sums all facilities within each `(iso, hour)`
automatically (ADR 0010) — provide as many facility rows per hour as you
like; the tool collapses them to one hourly vector per ISO and runs one
sweep per ISO. The `facility` column may be omitted entirely if your data is
already ISO-level. Optional compound load growth is applied via the
`load_growth_rate` / `load_growth_years` config knobs, not in the file.

## 2. LMP — pick ONE of the two formats

### 2a. `lmp_8760_template.csv` — full hourly BAU LMP (preferred)

| column | type  | notes |
|---|---|---|
| `hour` | int   | 0..8759, every hour present per ISO |
| `iso`  | str   | must cover every ISO in your load file |
| `lmp`  | float | $/MWh BAU wholesale price |

This is the ADR 0011 contract — normally the market simulator's BAU export.
Hourly LMPs preserve the price shape the optimizer exploits (it targets
expensive hours), so premiums and matching frontiers are shape-aware.

### 2b. `lmp_annual_average_template.csv` — annual-average comparison

| column           | type  | notes |
|---|---|---|
| `iso`            | str   | one row per ISO |
| `annual_avg_lmp` | float | $/MWh annual average wholesale price |

No `hour` column — intake detects this schema and expands each ISO's value
to a flat 8760 vector (`np.full`, no re-derivation). Results are then an
**annual-average comparison**: the premium is measured against a flat price,
so hourly shape/covariance value is deliberately excluded, and the run
metadata (`lmp_kind`) + report provenance section label the run
`annual_average_flat` to keep it distinguishable from shape-aware runs.

Validation mirrors the hourly path's idioms: a duplicate `iso` row is a hard
error naming an example, a non-finite or negative `annual_avg_lmp` value is a
hard error, and an ISO requested by the run but absent from the file raises
the same missing-ISO error as the hourly path.

## 3. Generating full-size fillable skeletons

`scripts/make_input_templates.py` writes full-`HOURS_PER_YEAR` fillable
skeleton CSVs — every row present, placeholder values that already pass
intake validation — so you only overwrite values instead of hand-building
the hour/iso plumbing:

```bash
../.venv/bin/python scripts/make_input_templates.py                       # all six ISOs
../.venv/bin/python scripts/make_input_templates.py --isos ERCOT CAISO \
    --out-dir data/templates/skeletons
```

Writes `load_8760_by_facility_skeleton.csv`, `lmp_8760_skeleton.csv`, and
`lmp_annual_average_skeleton.csv` into `--out-dir` (default
`data/templates/skeletons/`, gitignored — these are reproducible and
disposable). The three example templates above stay committed as the small,
human-readable illustrations of each schema.
