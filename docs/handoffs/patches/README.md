# docs/handoffs/patches — mechanical patch transport for oversized source files

Some source files (`constants.py` ~350 KB, `CHANGELOG.md` ~300 KB) exceed what
the `mcp__github__push_files` API can carry in one call (the model cannot emit
the full file content inline reliably), and `git push` is forbidden on this
remote (HTTP 413). The repo's established workaround is to ship the change as a
patch a human — or any large-file-capable mechanism — applies after merging the
branch (precedent: FF-2B, `docs/handoffs/ff-2b-APPLY-SPEC.md`).

## capacity-cost-constants-changelog.patch (2026-07-19)

New-build cost grounding — the `constants.py` cost-value changes
(`TECH_COST_MULTIPLIERS` literature envelope, li-ion `STORAGE_TECHS`,
`OFFSHORE_WIND_PARAMS`, EGS `fom_kw_yr`, `HYDROGEN_TURBINE_PARAMS`) plus the
`CHANGELOG.md` entry. Everything else in the change (ATB EGS extract, derive
script, tests, methodology, benchmark datatype) lands directly via the API.

**Generated as** `git diff origin/main → 3-way-merged(main + this session's
cost edits)`. The cost edits are textually disjoint from main's concurrent
constants change (reserve-margin / adequacy-DR region), so the merge is clean.

**Verified 2026-07-19:** applies cleanly onto a pristine `origin/main`
checkout and reproduces the merged files byte-for-byte; the resulting tree
passes all 19 cost tests (`tests/test_cost_benchmark_envelope.py` +
`tests/test_atb_entry_cost_consistency.py`).

**Apply (after this branch is on `main`, from the repo root):**
```
git apply docs/handoffs/patches/capacity-cost-constants-changelog.patch
```
If `main` has moved and a hunk is stale, `git apply --3way` resolves it
(the change is disjoint from other regions). After applying, the cost tests go
green — until then main CI is red because the already-merged tests assert these
values.

## neiso-operable-capacity-wiring.patch (2026-07-19)

NEISO operable-capacity availability overlay — the model-consumption wiring for
the ISO-NE Morning Report intake (`docs/handoffs/neiso-operable-capacity-intake-2026-07.md`).
Two disjoint, additive edits the API cannot carry inline (`scenarios.py` ~534 KB,
`fleet.py` ~505 KB):

- `src/market_sim/config/scenarios.py` (+26): the `neiso_operable_capacity_availability`
  gate (default `False`), beside `ercot_thermal_dam_availability`.
- `src/market_sim/data/fleet.py` (+79): the pooled-thermal measured-availability
  water-fill block in `generators_to_fleet_arrays`, beside the ERCOT class-day
  block.

Everything else (the committed CSV, fetch/build scripts, the
`data.neiso_operable_capacity` loader, the test, docs) lands directly via the API.

**Generated as** `git diff origin/main` with the two edits applied. Both edits
are purely additive (new field / new gated block) and textually disjoint from
any concurrent main change, so the merge is clean.

**Verified 2026-07-19:** applies cleanly onto a pristine `origin/main` checkout
and re-adds the config field; the end-to-end drive lands the covered-day
cap-weighted thermal availability on the measured fleet fraction, and is inert
when the gate is off. Unlike the cost patch, this one does **not** turn CI red
before it applies — no committed test asserts the gate (the committed
`tests/test_build_neiso_operable_capacity.py` exercises only the build + loader).

**Apply (after this branch is on `main`, from the repo root):**
```
git apply docs/handoffs/patches/neiso-operable-capacity-wiring.patch
```
`git apply --3way` if a hunk is stale.
