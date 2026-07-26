# wave4d goldens — gate record (complete pair, plus one substituted site)

Byte-identity record for **Wave 4D item 7b** (the iterrows → itertuples
conversion, commit `c2e81d0`), plan §8 protocol. Both halves exist and the
gate CLOSED:

- `wave4d-before/` — hashes-only manifest of the ERCOT keeper
  (`2026-07-23-ercot100-netrev-margin-keeper`, 2023–2025), captured at the
  pre-change tree (commit `89d7ca2`).
- `wave4d-after/` — the same capture after the conversion (commit `025ed73`,
  "Gate PASS"). All SEVEN content hashes (btm, flows, storage, system, three
  `dispatch/<year>_P1` parquets) are the **identical sha256** — not
  within-tolerance, the same digest. `regression_gate.py --mode byte` PASS;
  reshuffle localization Σ|hourly Δ| = 0.0 GWh.

One converted site is NOT exercised by this (or any) backcast golden:
`data/renewables.py::_add_proposed_capacity`. Its Effective Year filter is
`(EIA860_OPERABLE_VINTAGE, cal_year]` with the vintage at 2025, so **no row
survives for 2023–2025 and a keeper replay cannot reach the loop**. Its
verification was deliberately substituted with **function-level parity** —
the mutated monthly array compared on real on-disk EIA-860 inputs over every
vintage carrying a proposed pipeline, values AND type names, before/after
byte-identical — recorded in commit `c2e81d0`'s message. That substitution
was adjudicated correct and is **not to be re-run**; do not read the golden
pair's ERCOT-only scope as an abandoned or partial gate.

Per repo convention only these hashes-only manifests are tracked; the
multi-GB parquet bundles under the goldens dir are gitignored.
