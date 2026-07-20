---
name: data-intake
description: Add or extend an on-disk data type so it flows through the repo's data contract cleanly and consistently for every ISO. Use when the user wants to intake a new dataset (a new raw source, a new curated datatype, or a new ISO for an existing datatype), "wire up" data, build a curation script, or align data storage/processing with the schema/clean_io contract. Enforces schema-first design, the write_clean/read_clean seam, per-ISO registry modules (no `if iso==` ladders), tmp-CLEAN_DIR tests, and the non-negotiable repo rules.
---

# Data intake

Bring a new dataset into the model through the ONE contract every curated
datatype shares, so `data/clean` stays uniform no matter which session produced
it. The seam is `scripts/lib/clean_io.py` (`write_clean` / `read_clean` /
`validate_clean`); the contract is `data/dictionary/schema/<datatype>.schema.yaml`.
Full rationale and the "clean repo for all ISOs" rules: `docs/adding-new-data-types.md`.

Read that doc first, then follow this recipe. The `capacity-deliverability`
datatype is the worked reference (ISO-agnostic, registry-driven); `outages` is
the single-source reference.

## Recipe (in order)

1. **Schema first — it is the contract.** Write
   `data/dictionary/schema/<datatype>.schema.yaml`: `datatype` (hyphenated to
   match the filename stem), `schema_version: 1`, `key_columns`,
   `allow_additional_columns: false`, and a `columns` list — each with
   `name` (lower_snake_case), `dtype` (`string`/`int64`/`float64`/`bool`/
   `datetime64[ns, UTC]`/`datetime64[ns]`), `unit`, `nullable`, `description`.
   A tidy (long) frame absorbs heterogeneous per-ISO layouts far better than a
   wide one — prefer it when ISOs disagree on columns.

2. **Raw home + README.** Create `data/raw/<datatype>/` (hyphenated) with a
   `README.md` stating the source, the exact file layout expected, the
   authoritative URLs, and a `DATA NEEDED:` line for anything not yet committed.
   Never modify `data/raw` in place; it is the immutable source root.

3. **Per-ISO logic behind a registry — never branch on ISO in shared code.**
   For a multi-ISO datatype, put each ISO's parsing in its own module
   (`scripts/lib/<datatype>/<iso>.py`) that registers a spec in a shared
   registry, and keep the dispatcher generic. This is what lets parallel intake
   sessions add ISOs without touching a shared file or colliding. Build the
   shared scaffolding (the frozen `IsoSpec`, `REGISTRY`, `register`,
   `load_registry`, `raw_dir_for`, `finalize`) from
   `scripts.lib.datatype_registry.make_registry(datatype, canonical_columns,
   spec_fields, …)` and keep only the datatype-specific `validate_tidy` /
   `parse_unified_csv` in the package `__init__.py` (see
   `scripts/lib/capacity_deliverability/__init__.py` and
   `scripts/lib/capacity_market_demand_curve/__init__.py` for the pattern).

4. **Curation script.** `scripts/data/curate_<datatype>.py` (underscored): read only
   `data/raw`, build a schema-shaped frame, then write through
   `clean_io.write_clean(df, "<datatype>", iso=…, year=…, market=…, source=…)`
   and `clean_io.validate_clean(path)`. Provide `curate(raw_root=None, isos=None)`
   returning `list[Path]`, and an argparse `main`. Idempotent; partition with
   `year` only when rows are per-year (put a spanning "delivery_year" in a
   *column* otherwise, `year=None`).

5. **Register in the orchestrator.** Add the datatype to the `DATATYPES` tuple
   in `scripts/regenerate_clean.py`.

6. **Test with a tiny fixture + redirected CLEAN_DIR.** `tests/test_curate_<datatype>.py`:
   subclass **`tests.helpers.base.CleanDirTestCase`** (call `super().setUp()`) — it
   redirects `paths.CLEAN_DIR` to a per-test tempdir and restores it for you, so you
   never hand-roll the save/point/restore dance or a `tearDown`. Use `self.tmp_path`
   for the raw fixture root (or `RawFixtureTestCase`, which adds a `raw_dir`). For a
   pytest-style test use the `tmp_clean_dir` fixture instead. Then write a minimal
   raw fixture (reuse `tests.helpers.raw_fixtures` writers where one fits), run
   `curate(raw_root=tmp, …)`, and assert with `assert_clean_valid` /
   `read_clean_or_fail`. Trivial case first (1 row / 1 area), then scale. See
   `docs/testing.md` for the helper layer.

7. **Consumption seam (when wiring into the model).** Add
   `src/market_sim/data/<datatype>.py` with a reader over
   `clean_io.read_clean("<datatype>", …)`. Gate any new model behaviour behind a
   default-OFF `ScenarioConfig` flag (GATED), and convert Pydantic → numpy
   struct-of-arrays before any LP construction.

8. **Docs.** Update `data/dictionary/data-dictionary.md`
   (`python scripts/render_data_dictionary.py`) and run `/sync-docs` when the
   approach is settled.

## Non-negotiables (from CLAUDE.md)

- No magic numbers — every constant from config/constants or a cited source.
- Every module and public function gets a docstring.
- Measured data is allowed only as a reproducible physical/market *input*, never
  a fitted answer pinned to actuals (rules #12/#13).
- Parquet for results/clean; full data traced to raw via `source=` provenance.
- No Python loop over hours in LP construction (N/A to most intake, but the
  loader must hand the LP arrays, not object graphs).

## Checklist before you call it done

- [ ] schema YAML validates and `datatype` matches the filename stem
- [ ] raw `README.md` lists sources + `DATA NEEDED` gaps
- [ ] per-ISO modules register specs; shared code has no `if iso ==` ladder
- [ ] `curate_<datatype>.py` writes only via `write_clean`, re-runs cleanly
- [ ] datatype added to `regenerate_clean.py` `DATATYPES`
- [ ] `tests/test_curate_<datatype>.py` passes on `CleanDirTestCase` / `tmp_clean_dir`
- [ ] docs/dictionary updated
