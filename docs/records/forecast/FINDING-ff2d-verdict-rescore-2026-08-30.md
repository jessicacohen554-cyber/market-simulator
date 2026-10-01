# FINDING — FF-2D verdict re-score 2026-08-30: all 7 re-scorable verdicts reproduce byte-identically at HEAD; the FR-21 staleness gate resets

**Date:** 2026-08-30 · **Lane:** FF-2D verdict re-score (scorer-only, owner
ruling 2026-08-30, director sitting) · **Charter:**
`docs/forecast-development-plan-2026-07.md` FR-21 + CLAUDE.md rule 15
`[R-DASHBOARD]` forecast-namespace half.
**Predecessor:** `docs/FINDING-ffr3a-verdict-rescore-2026-08-24.md` — the
coverage measurement (which verdicts are re-scorable at all) is unchanged and
is not re-litigated here.
**Commit:** `2e398cf` on `claude/ff-2d-verdict-rescore-jh3xfs`.

**Headline.** The FR-21 gate had reached its threshold: Δ = 10 solve-affecting
commits at dispatch (12 by the time this lane's HEAD `67f1557` was cut) past
the board's newest scored verdict evidence (2026-08-25). All **7 re-scorable
verdicts** were re-scored through the stamped scorer at HEAD and **every one
reproduces byte-identically** — no determination, category, row, reason or
caveat moves anywhere on the 40-entry board. The kill-rule (freeze on any
flip) did not fire. The diff is provenance-only: `scored_at_sha`
`4fc57ecdd57a → 67f1557422ce`, `scored_at_date` `2026-08-24 → 2026-08-30`.
The board's verdicts are now *known* to describe HEAD, which is the entire
deliverable of a staleness refresh.

---

## 1. What was re-scored, and how

`scripts/rescore_forecast_verdicts.py --apply` (shelling out to
`scripts/forecast_verdict.py`; every written value is the scorer's own output
on committed artifacts). The re-scorable set is exactly the FFR-3A seven —
the only board verdicts whose `register_forecast_run.VERDICT_MAP` run holds a
tracked score artifact under `results/hindcast/`:

| verdict | tier | determination |
|---|---|---|
| `pjm-2021-2025-curve-ff2c-t1h` | t1h | HOLD → HOLD |
| `miso-2021-2025-curve-ff2c-t1h` | t1h | HOLD → HOLD |
| `neiso-2021-2025-curve-t1h` | t1h | HOLD → HOLD |
| `nyiso-2021-2025-curve-t1h` | t1h | HOLD → HOLD |
| `ercot-t1x-ffr2a` | t1x | HOLD → HOLD |
| `pjm-t1x-ffr2a` | t1x | HOLD → HOLD |
| `miso-t1x-ffr2a` | t1x | HOLD → HOLD |

Zero rule-22 `[R-HOLDOUT]` blocks (every artifact records
`scored_years [2023, 2024, 2025]`). Verified beyond the tool's own
category-level diff: a structural deep-compare of the pre-change vs
post-change board, excluding only the `provenance` blocks, over all 40
entries — **zero content differences**. The 12 solve-affecting commits since
2026-08-25 did not change the scorer's reading of any committed artifact.

## 2. The gate reset (measured)

`python3 scripts/check_forecast_staleness.py`, exit code captured bare
(no pipe): **exit 0**.

```
gate evidence       : verdicts
newest scored sha   : 67f1557422ce  @ 2026-08-30T17:18:18Z
solve-affecting Δ   : 0 commit(s) (threshold 10)
verdicts            : 40 stamped, 9 scored  <- gate evidence
WARN: 31 of 40 verdicts stamps record no scored-at date …
```

The Δ-threshold warning and the `FRESHER NON-GATE ARTIFACTS` masking warning
are both gone. The one remaining WARN — **31 of 40 never re-scored** — is the
structural FFR-3A fact, not residue of this lane: those verdicts' source
bundles are gitignored by design and only an LP re-solve could produce a
re-scorable artifact, which this lane's charter forbids (reported, not
solved). No stamp was minted that a re-score did not earn.

Count reconciliation vs the 2026-08-24 finding (32 unrecoverable of 39): the
board is now 40 because capx-d2 (`3786191`, 2026-08-25) preserved the prior
NYISO gate verdict as `nyiso-t1f-ffr3a2` when it refreshed the bare
`nyiso-t1f` → 33 without a tracked artifact. Two of the 33 still carry real
(older) stamps earned at their original scoring and stay exactly as they
were: `miso-2023-2027-crossover-ffr3a4-t1x` (`6fbd3f28eb9a` @ 2026-08-04) and
`nyiso-t1f` (`ea4e4faf65de` @ 2026-08-25, PROMOTE-WITH-CAVEATS — the board's
only non-HOLD, untouched).

## 3. Backcast gates untouched (verified, not assumed)

- `scripts/audit_keepers.py`: **PASS**, 0 failures, 0 warnings, exit 0.
- Both parity gates run twice — on the pre-change tree and on this lane's
  tree — with **byte-identical output and identical exit codes (1/1)**, i.e.
  their standing red is pre-existing on main and owned elsewhere:
  `check_registry_payload_parity.py` fails on the unmapped
  `results/calibration/caiso217_crosswalk` bundle (the
  `bench-restamp/caiso217-prune` lane's surface), and
  `check_forecast_parity.py` (FR-22) reports 5 unaccounted armed keeper
  mechanisms / 8 filed gaps on ERCOT/NYISO/MISO keeper surfaces (those
  calibration lanes' in-flight work). Nothing in either report moves by this
  change.
- No backcast file touched: the lane's whole diff is
  `frontend/data/forecast/ff-verdicts.json` plus this finding.

## 4. Not done, deliberately

- **No LP solve, no hindcast sidecar regeneration** — a verdict that would
  need fresh artifacts to become re-scorable is reported (§2), not solved.
- **No stamp for the 33 unrecoverable verdicts**, per the FFR-3A precedent.
- **`program-status.json` untouched** — the §2.1b board seed is the
  DIRECTOR-RECORDS lane's surface; its `refresh` block still records the
  FFR-3A-2 sitting and that is correct until that lane re-keys it.
- **Nothing committed to the generated namespace** (`registry/`, `runs/`,
  `manifest.js`, `program-status.js`): `register_forecast_run.py --reindex`
  was run only as a local assembly check (it completes; outputs stay
  gitignored; the Pages deploy remains their single writer, plan §7.5).
- **No forecast lane proposed** — the program stays parked at G1; this
  refresh keeps its board honest, nothing more.
