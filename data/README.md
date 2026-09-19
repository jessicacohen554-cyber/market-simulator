# `data/` — raw inputs and the curated clean tree

This directory holds every on-disk input the model reads. Paths are resolved
centrally in [`src/market_sim/config/paths.py`](../src/market_sim/config/paths.py)
(never with `Path(__file__).parents[...]`), and the whole tree can be relocated
with the `MARKET_SIM_DATA_ROOT` environment variable.

## Target layout

```
data/
├── raw/            # immutable source downloads — NEVER modified in place
│   ├── lmp-data/{CAISO,ERCOT,NYISO,NEISO}/   per-ISO LMP downloads
│   ├── {ercot-AS,NYISO-AS,PJM-AS}/           per-ISO ancillary services
│   ├── eia-930/, eia-930-hourly/             demand + generation by BA
│   ├── campd-facility-level/, campd-unit-level/   EPA CEMS emissions
│   ├── eia-860/, fleet-egrid/                fleet registries
│   ├── gas-prices/                           fuel-price benchmarks
│   ├── reference/                            crosswalks / lookups
│   ├── _processed-legacy/, _validation-source/   not-yet-curated (leading _)
│   └── ...
├── clean/          # curated, schema-validated Parquet (DERIVED — disposable)
│   └── <datatype>/[<iso>/][<market>/]<datatype>[_<year>].parquet
├── exports/        # hand-off CSV cuts of a raw archive (DERIVED — not inputs)
│   └── <family>/   each carries a README naming its source + regen command
└── dictionary/     # the data contract
    ├── schema/<datatype>.schema.yaml         one canonical schema per datatype
    └── data-dictionary.md                    overview + ISO coverage matrix
```

- **`raw/`** is the single source root (the W1 relocation collapsed the old
  `inputs/` + `data/` roots into `data/raw`). It is byte-for-byte the upstream
  downloads and is never edited; curation only ever *reads* it.
- **`clean/`** is the curated output every session produces. It is **derived
  and disposable** — regenerate it from `raw/` with the per-datatype curation
  scripts rather than hand-editing. Files are partitioned by `datatype` and the
  optional `iso` / `market` / `year` keys (see `paths.clean_path`).
- **`dictionary/`** is the contract `clean/` must satisfy: one schema YAML per
  clean datatype, plus the human-facing data dictionary.

## The clean-write contract

Every curation script writes through the one shared seam,
[`scripts/lib/clean_io.py`](../scripts/lib/clean_io.py):

```python
from scripts.lib.clean_io import write_clean, validate_clean

path = write_clean(df, "lmp", iso="CAISO", year=2024, market="DAM",
                   source="data/raw/lmp-data/CAISO/CAISO_dam_hourly_2024.csv")
validate_clean(path)   # round-trip check against the embedded schema
```

`write_clean` validates `df` against `dictionary/schema/<datatype>.schema.yaml`
(column presence, dtypes, units, tz-aware UTC, snake_case), writes Parquet to
`paths.clean_path(...)`, and embeds the schema version + source provenance in
the file metadata. See [`dictionary/data-dictionary.md`](dictionary/data-dictionary.md)
for the per-datatype schemas, conventions and ISO coverage matrix.

### What gets committed

`data/clean/` is **gitignored** — the curated parquet is derived output, not a
source artifact. A curation session commits its `scripts/curate_<datatype>.py`
and `tests/test_curate_<datatype>.py`; anyone regenerates the parquet by
re-running the script. The contract under `data/dictionary/` (schema YAMLs +
this dictionary) and `scripts/lib/clean_io.py` **are** committed.

`scripts/lib/clean_io.py` is the shared, frozen seam: curation scripts import
it but must not edit it. If a datatype can't be expressed within the current
schema/writer, raise it as a contract change rather than patching the writer in
a curation branch — that keeps the parallel sessions conflict-free.
