# Adding new data types & features — keeping the repo clean for all ISOs

Rules for adding a new dataset, curated datatype, or ISO so the repo stays
uniform across the six ISOs and every session's output looks the same. These
operationalize the non-negotiable rules in `CLAUDE.md` for the specific job of
data intake and feature addition. The `data-intake` skill walks the mechanical
recipe; this doc is the *why* and the invariants a reviewer checks.

## The one seam

Every curated dataset enters `data/clean` through
`scripts/lib/clean_io.write_clean(...)` and leaves through `read_clean(...)`.
Nothing writes Parquet under `data/clean` by hand, and nothing in the model
reads a clean file except through `read_clean`. The writer validates against the
datatype's schema before touching disk and embeds schema version + source
provenance in the Parquet metadata, so a clean file always traces back to raw
and always conforms. If you find yourself constructing a `data/clean` path or
`pd.read_parquet`-ing one directly, stop — route it through the seam.

## The schema is the contract

`data/dictionary/schema/<datatype>.schema.yaml` is authoritative. Columns,
dtypes, units, nullability and the key are declared there, and both the writer
and a round-trip `validate_clean` enforce them. Change the data shape → change
the schema (and bump `schema_version` if it's breaking) → regenerate. Prefer a
**tidy (long)** frame when ISOs publish different quantities: one row per
(entity, period, metric) with a controlled `metric` vocabulary absorbs
heterogeneity that a wide frame can't, and keeps one schema for all ISOs.

## ISO-agnostic by construction — no `if iso ==` ladders

Shared code must not branch on the ISO name. Per-ISO differences live in per-ISO
modules that **register** themselves in a shared registry; the dispatcher and
the model look the ISO up, never special-case it. Concretely, for a multi-ISO
datatype:

```
scripts/lib/<datatype>/__init__.py   # registry + canonical vocab + generic helpers
scripts/lib/<datatype>/<iso>.py      # one per ISO: declare a spec, register()
scripts/data/curate_<datatype>.py         # thin dispatcher over the registry
data/raw/<datatype>/<iso>/           # one raw subdir per ISO (+ README)
```

Benefits this buys, and why it's mandatory:

- **Additive.** A new ISO is a new file + a `register(...)` call. No shared file
  is edited beyond (optionally) a registry import list, so parallel intake
  sessions don't collide or produce merge conflicts.
- **Uniform.** Every ISO flows through the same generic parse → `finalize` →
  `validate` → `write_clean` path, so `data/clean` is identical in shape
  regardless of who produced it.
- **Reviewable.** The canonical vocabulary (metrics, area types, seasons) lives
  in one place; a reviewer checks new native→canonical mappings, not bespoke
  per-ISO plumbing.

ERCOT-style exclusions are explicit: if an ISO has no analog for the datatype,
document it in the raw `README.md` (as `capacity-deliverability` does for
ERCOT — energy-only, no LDAs) rather than inventing a placeholder.

## Measured data: input, never answer

Real measured values may enter **only** as a reproducible physical/market input
that would regenerate for a forward year and respond to changed conditions
(CLAUDE.md #12/#13). Never feed a measured *outcome* back to force a backcast
match. A capacity requirement or transfer limit published by an ISO is a
legitimate input; a value hand-tuned to move the price residual is not.

## Tests: tmp CLEAN_DIR, trivial case first

`tests/test_curate_<datatype>.py` redirects `clean_io.paths.CLEAN_DIR` to a temp
dir, writes a tiny raw fixture, runs `curate`, and asserts `validate_clean` plus
the reconciliation. Start with the trivial case (1 row / 1 area / 1 period),
then scale. Restore `CLEAN_DIR` in tearDown so the suite never touches the real
tree.

## Wiring into the model (features)

Worked example: `docs/capacity-deliverability-wiring.md` — the 5-ISO
`capacity-deliverability` datatype's model consumer (`data/capacity_deliverability.py`
reader, `config/capacity_area_crosswalk.py` per-ISO area→zone resolver
registry, and the gated `capacity_deliverability_limits` wiring into
`model/transmission.py`, `model/capacity.py`, `model/storage.py`), including
how a datatype with mismatched per-ISO granularity gets a documented,
tested crosswalk instead of a guessed one.

- New behaviour goes behind a **default-OFF** `ScenarioConfig` flag, GATED, so
  keepers are unaffected until the mechanism is validated.
- Judge a new mechanism on **structural fidelity, not backcast MAE** (rule #1).
  If a correct mechanism worsens the fit, find the real root cause (rule #11);
  don't revert the mechanism or bury the error in a fudged input.
- Convert Pydantic config → numpy struct-of-arrays before LP construction; the
  LP builder touches arrays and scalars only, and never loops over hours.
- Every module and public function gets a docstring; no magic numbers.

## Consolidated derive-owned datatypes (sanctioned exception)

Six datatypes deviate from the 1:1 `curate_<datatype>.py` file convention
above and are sanctioned as-is: `fuel-basis`, `fuel-ercot-ep-gas`,
`fuel-hub-monthly`, `fuel-takeorpay`, and `fuel-zonal-hub` are curated
together by one consolidated `scripts/data/curate_fuel_prices.py` (each still
writes through `write_clean` against its own schema, so the contract per
datatype is unaffected — only the file grouping differs), and `border-lmp`
is produced by `scripts/data/build_pjm_border_lmp_miso.py` /
`scripts/data/derive_miso_pjm_border_hr.py` directly into
`data/raw/_validation-source/` rather than through the `write_clean` seam,
since it is a derived measured-input artifact consumed like raw validation
data rather than a modeled clean datatype. Do not split these into
per-datatype scripts or add redundant `curate_<datatype>.py` shims solely
for naming-convention conformance.

## Definition of done

Schema committed; raw README with sources + `DATA NEEDED` gaps; per-ISO modules
registered with no shared-code ISO branching; curate script writing only via
`write_clean` and idempotent; datatype in `regenerate_clean.py`; a passing
tmp-CLEAN_DIR test; data dictionary regenerated; docs synced.
