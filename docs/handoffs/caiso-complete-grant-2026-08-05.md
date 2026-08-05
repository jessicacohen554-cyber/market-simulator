# CAISO `complete` grant — execution record (2026-08-05)

Governance lane, session **CAISO-GRANT** (branch `claude/caiso-complete-grant-robwjk`).
Committed artifacts only: **no solve, no scoring, no year touched, no dashboard run, no keeper
change, no mechanism-matrix cell.** Deliverable is one entry in
`frontend/data/backcast/calibration-complete.json`.

## Citation chain

**caiso-171** (frontier/`complete` assessment, reversed to **YES** at `0043fc22`; the owner
restated the criterion at P.6 — `complete` means (a) the 2022 touchpoint is allowed and
(b) frontier, everything testable tested; **not** a DOF-cleanliness certificate)
→ **caiso-172** (its one gating item, the PGE-TAC TAC-zone weight, closed **MEASURED**)
→ **caiso-174** (PR #3578 — FFR-4D epoch re-solved, keeper moved onto the measured fleet,
`complete` re-recommended **YES** post-epoch)
→ **Addendum S.4/S.5** of `docs/handoffs/ffr-owner-sitting-2026-08-02.md`, signed **2026-08-05**:
`CAISO complete | GRANT`. That addendum **is** the session-logged owner authorization rule 22
requires.

## Verified determination (no solve)

`uv run python scripts/calibration_verdict.py --run-id 2026-08-05-caiso-174-measured-fleet`
— committed artifacts only, never an LP:

**`CALIBRATED-WITH-CAVEATS`**

| criterion | tier | result |
|---|---|---|
| C1 fuel-mix by class (grid-delivered) | LOAD | PASS |
| C2 system volume (gas/coal families) | LOAD | PASS |
| C3a mean LMP | LOAD | CAVEAT [ledgered] — 2024 +11.5 %, 2025 +14.4 % |
| C3b price duration/shape | LOAD | PASS |
| C3c price tail / scarcity (RT hourly) | SUPP | CAVEAT [ledgered] — 2023 0 h vs 47 h; 2024 1 h vs 35 h |
| C4 fleet hourly dispatch correlation | SUPP | PASS |
| C6 governance gate | PROT | PASS |
| C7 diurnal shape (D-1) | PROT | **SKIPPED — unscored protective** |
| C8 forced-energy share (D-2) | PROT | **SKIPPED — unscored protective** |

D-10 free-class C1 all **12/12** · free **8/8** (pinned, excluded from free: CC_CHP, ST_CHP).
0 FAILs. Both caveats are the **owner's act of 2026-07-30 at caiso-145**, carried forward
unchanged, spending no new slot (**2 of 3** non-protective slots used). This reproduces the
determination the keeper shard already records, so the grant is keyed to a determination that
was actually scored against the run it names.

Scorer sanity, same run of checks: the three already-declared keepers each reproduce their
recorded determinations exactly — NEISO `CALIBRATED-WITH-CAVEATS`, NYISO `NOT-YET`,
PJM `CALIBRATED`.

## Recorded against interest — the one delta found

**C7 and C8 are unscored on caiso-174** because its committed bundle
(`results/calibration/caiso174_measured_fleet/`) carries **no `legitimacy_diagnostics.json`**,
while the superseded keeper `2026-08-04-caiso-172-measured-path15` carries one and scores
**both PASS**. The determination *label* is therefore identical to the predecessor's, but the
protective coverage behind it is **narrower**.

This is **not** a re-solve item — rule 21 `[R-FORCED-BUDGET]` makes C7/C8 scorer-only ("no
re-solve, no bundle regen, and existing keepers re-score in place"), so it closes with:

```
scripts/legitimacy_diagnostics.py --bundle results/calibration/caiso174_measured_fleet \
    --iso CAISO --json-out results/calibration/caiso174_measured_fleet/legitimacy_diagnostics.json
```

**Deliberately not done here** — this lane's charter is committed artifacts only, and
improvising the repair was out of scope. It is disclosed verbatim in the marker entry's
`determination` field and logged as the open item the grant carries. It does not block the
grant: `audit_keepers.py --iso CAISO` passes clean, and the NEISO `complete` entry already sets
the precedent that an unscored protective criterion is **disclosed, not disqualifying**
(NEISO's own entry says "C7 shape unscored-protective").

## Gates run

| check | result |
|---|---|
| `scripts/audit_keepers.py --iso CAISO` | **PASS** — 0 failures, 0 warnings; **M1** included |
| `scripts/check_mechanism_matrix.py` | exit 0, **zero delta** — 230 warnings before and after, identical set (no cell changed; all pre-existing anchor-drift + the caiso-174 keeper-stamp warning) |
| marker parses | `marker_blocks` → validation `[CAISO, NEISO, NYISO, PJM]`, locked_test `[_note]` |
| `holdout_policy.authorized` | CAISO/validation **True**; CAISO/locked_test **False**; ERCOT/validation **False** (no other ISO affected) |
| freeze still outranks | `run_calibration_full.py --iso CAISO --year 2022 --holdout-authorized` **refused**, citing the freeze *before* the marker |

## What this does not do

No 2022 solve, score, or registration — the **freeze is ACTIVE** and outranks the marker
(`holdout-freeze.json`'s own text); the grant *stores* the authorization the freeze suspends.
`final` untouched (CAISO's `locked_test` note reads **"never authorized"** — the contract for
absence from `final`, distinct from NEISO's spent one-shot). No other ISO's entry, the freeze
file, keepers, or any matrix cell was modified. Rule 22's tier map is unchanged.

## Incident noted in passing (not mine, not fixed)

The `PostToolUse` hook `.claude/hooks/ruff-autofix.sh` runs whole-tree `uv run ruff format .`
on **any** `.py` Write/Edit. Writing a scratchpad `.py` helper in this session therefore
reflowed `src/market_sim/config/constants.py` from 3,960 → 9,508 lines (AST-identical pure
reformat). It was **restored to its exact HEAD bytes and never staged** — rule 27 `[R-PUSH]`
forbids bulk-rewriting a core file, and this was outside the lane entirely. The underlying
condition is **pre-existing on `main`**: `ruff format --check` reports "would reformat" against
`origin/main`'s own bytes of that file, which is not excluded in `pyproject.toml`'s
`extend-exclude`. Flagged for whoever owns the lint lane; deliberately not repaired here.
