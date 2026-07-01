# PP-01 — Load Intake & LMP Coupling

**Upstream:** PS-07 (intake & growth), PS-08 (LMP coupling).
**Targets:** `src/lce_portfolio/intake.py`, `src/lce_portfolio/cli.py`
(`load_lmp`).
**Status:** minimal done (sum-by-hour aggregation, uniform growth, LMP reader).

## Build

1. **Aggregation (PS-07).** Implement the decided facility→ISO rule (weighting,
   loss adjustment if any). Confirm multi-ISO = one sweep per ISO. Decide
   missing-hour handling (zero-fill vs error) and enforce it in `load_intake`.
2. **Growth (PS-07).** If shaped/per-facility growth was chosen, replace the
   uniform `(1+rate)^years` with the decided model; add config fields.
3. **Calendar (PS-07).** Enforce the agreed hour convention; validate load & LMP
   share it (both 8760, same indexing).
4. **LMP contract (PS-08).** Implement the decided zonal→ISO reconciliation
   (load-weighted average) *if* the export is zonal; otherwise document that the
   upstream export already produces per-ISO LMP. Validate 8760 rows/ISO.
5. **Escalation (PS-08).** Apply the decided price escalation, if any.

Do **not** import `market_sim`. If any market-sim helper is needed, copy it into
`vendored/` with a source+revision header.

## Acceptance

`test_intake` covers aggregation (multi-facility, multi-ISO), growth, missing
hours, and calendar validation; `test_cli`/`test_lmp` covers the LMP reader and
reconciliation. The sample flow still runs.
