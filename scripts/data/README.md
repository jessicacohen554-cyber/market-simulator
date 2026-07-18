# scripts/data/ — data fetching & processing

Everything between an external source and the model's on-disk inputs. Moved
here 2026-07-18 from the flat `scripts/` directory (imports/references updated
mechanically; `git log --follow` connects history). Not core engine: the LP,
dispatch, and capacity-evolution code lives in `src/market_sim/`, and the
operational entry points stay at `scripts/` top level.

Stages, by prefix:

1. **`fetch_*`** — download raw source data into `data/raw/<source>/`
   (EIA-860/923/930, CAMPD/CEMS, ISO portals, gas hubs, NRC, NREL ATB, …).
   Raw files are immutable once landed (CLAUDE.md: `data/raw` is never
   modified in place).
2. **`curate_*`**, plus `process_*` / `convert_*` / `parse_*` / `extract_*` /
   `fold_*` / `extend_*` / `reassemble_*` / `postprocess_*` — transform raw
   into curated, schema-validated Parquet under `data/clean/` via the
   `scripts/lib/clean_io.py` seam. The data contract is
   `data/dictionary/schema/<datatype>.schema.yaml` + `data-dictionary.md`;
   the `data-intake` skill documents the pattern (schema-first, per-ISO
   registry modules, no `if iso ==` ladders).
3. **`derive_*`** — derive measured-behaviour model parameters (min-stable
   loads, sigmoid anchors, offer surfaces, outage envelopes, seam ladders, …)
   from curated/raw data. **Rule 23: frozen against residuals** — a derive
   script re-runs only when its *source data* updates, never because a
   backcast residual moved, and the re-derivation commit must cite the data
   change.
4. **`build_*`** — per-source reference builders (HSL frames, LMP references,
   AS withholding series, ownership maps, …) consumed by loaders in
   `src/market_sim/data/`.

Tests for curation live in `tests/` (e.g. `tests/test_curate_lmp.py` imports
`scripts.data.curate_lmp`); the tmp-`CLEAN_DIR` pattern keeps them hermetic.
