# PRE-REGISTRATION — FH-5 CAISO Arm K, the twelfth arm

**Session.** FH-5-ARMK `[OPUS]`, branch `claude/caiso-arm-k-fh5-z4wd2n`, off
`origin/main` **`cfb8127`**. Solve lane. Written and committed **BEFORE** the
solve was launched; nothing in this document changes after that commit.

**This lane designs nothing.** The prereg of record is
`docs/handoffs/fh-5-phase-b-2026-08-11.md` **§1**, in force unmodified — its
window (§1.2), arm definitions and per-ISO arming (§1.3), I6 rider (§1.5),
horizon read (§1.6) and governance (§1.8) all bind here verbatim. This session
executes the ONE cell that section left unexecuted and adds the completed row to
§4. It re-litigates none of FH-5's adjudicated reads.

**What was blocked, and what unblocked it.** FH-5 §1.4 recorded CAISO Arm K as
BLOCKED: `resolve_demand_growth_rate` refused CAISO at
`demand_growth_vintage=2021` because `DEMAND_GROWTH_RATES_VINTAGES[2021]` carried
no CAISO row — the FH-2 seam failing closed exactly as designed, on the one cell
of FH-3's 12 that was a MANUAL DOWNLOAD. That cell has since been intaken
(CEDU 2020, CEC Resolution 21-0125-2, `caiso-vintage-2021-intake-2026-08-11.md`),
so the refusal no longer fires. **No value is substituted, interpolated or
borrowed** — the run is unblocked by a cited edition or not at all (rules 5, 13,
25).

---

## 1. THE PIN — this arm must run the eleven siblings' code

A multi-arm comparison whose arms ran different code is not a comparison. The
eleven landed FH-5 arms ran at `src/` == **`3ae7465`** (FH-5 §1.1, §3):

```
3ae7465:src     = 66d789dced7308dcaa837f2e6441d06de9f6454b
3ae7465:scripts = 1e79b7b675f7cce8210703ce2023b55e7c22587d
```

Both hashes were re-verified in this session and match.

**Neither obvious option is correct.** A byte-pure `3ae7465` `src/` lacks the
CAISO vintage row and refuses this arm exactly as §1.4 measured. HEAD is wrong
twice over: it is a different code version than the siblings ran, and stage B
(#3888/#3903) moved ERCOT posture bytes under `src/`
(`COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO`, `iso_configs`, `scenarios`, `fleet/*`,
`resolved_inputs.py`, `runner.py`, …).

**The pin actually applied:** `3ae7465`'s `src/` and `scripts/` **PLUS exactly
the additive `DEMAND_GROWTH_RATES_VINTAGES` CAISO-2021 delta in `constants.py`,
and nothing else.** Procedure, executed in order:

1. Branched from latest `origin/main` (`cfb8127`).
2. `git restore --worktree --source=3ae7465 -- src/ scripts/`.
3. Removed the files that did not exist at the pin, so the pin is internally
   consistent (the FH-5 §3 step-2 precedent, which removed `resolved_inputs.py`):
   `src/market_sim/data/resolved_inputs.py` plus **31** post-pin `scripts/`
   files (list: `scratchpad/scripts_removed_for_pin.txt`; all are tracked on this
   branch and restored from the index after the solve).
4. Re-applied HEAD's three CAISO-vintage `constants.py` hunks — the registry
   header note, the `near =` base-year construction note, and the `"CAISO"` cell
   itself.
5. Verified, then cleared stale bytecode (`__pycache__`, `*.pyc`).

**Verification, as run:**

| Check | Result |
|---|---|
| `git diff 3ae7465 -- scripts/` | **EMPTY** (0 lines) |
| `git diff 3ae7465 -- src/` | `constants.py` only, 3 hunks, +54/−8 |
| Hunk headers | `@@ -2311,7` `@@ -2340,8` `@@ -2391,11` — all inside the vintage registry |
| Vintage-registry region vs HEAD | **byte-identical**, sha256 `54ceff39b6a8473efa22b3e9b92c80228d238823cfaf83c88142a25e7d009a80` |

**Resulting tree hashes — the durable, rewrite-proof handles** (the FH-5 §3
addendum's recommended citation form):

```
working src/     = 093f366b6fa84d28af3edcb23595ff8ccced6d0b   (pin + the vintage delta)
working scripts/ = 1e79b7b675f7cce8210703ce2023b55e7c22587d   (== pin, unmodified)
constants.py sha256 = 04fd408dde9ac56ebff4d17417389d7307b5532b9ecddff79f833b54bc780292
```

**The pin is worktree-only.** `git restore --worktree` leaves the index at
`cfb8127`, so no commit in this lane reverts anyone's work (FH-5 §3 step 2). The
artifacts are produced at the pinned `src/`; the branch they are committed on is
based on later `main`. Those are deliberately different things and both are
stated.

**Why the siblings stay comparable.** The vintage row is adjudicated purely
additive — no existing run reads `DEMAND_GROWTH_RATES_VINTAGES[2021]["CAISO"]`,
because every ISO resolving that vintage reads only its own row, and every run
with `demand_growth_vintage=None` never touches the registry at all. This
session measured the claim rather than asserting it: the Arm K config key built
at this pin is **`4dcb08ecf9fecfc6`**, **identical** to the key FH-5 §1.3
recorded at prereg *when the CAISO row was still absent*. The cache key hashes
the vintage **selector**, not the table, so the eleven siblings are
byte-unaffected and the comparison stands.

## 2. THE RUN, pre-registered

ONE invocation; years sequential inside it (rule 12); shipped CAISO defaults
with **no screen flags** — Phase-A arming verbatim (FH-5 §1.3: only ERCOT armed
screens):

```
uv run python scripts/run_capacity_hindcast.py --iso CAISO \
  --forward-from-base --arm asknown --vintage 2020 \
  --start-year 2021 --end-year 2025 \
  --out-dir results/hindcast/caiso-2021-2025-t1ff-armk-fh5
```

**Expected config key `4dcb08ecf9fecfc6`** (prereg build, measured at this pin —
§1). **The RUNTIME key is the key of record.** The bundle lands at
`<out-dir>/CAISO/<runtime-key>/` and the two need not agree: CAISO's own Arm R
sibling was pre-registered at `b40e1d9dc01a63f0` and **solved at
`ecb416fd9b9073a3`**, so for this ISO the divergence is demonstrated, not
hypothetical. The ledger path is read from the bundle's `meta.json` before any
zero is believed (the D-13 hazard).

Resolver state confirmed at the pin before launch: the CAISO 2021 row resolves to
`{low 0.0009, mid 0.0091, high 0.0158}` (near == long, edge-held), and
`resolve_demand_growth_rate` returns **0.0091/yr** for each of 2021/2023/2024/2025
under the shipped `mid` path.

**Window.** Solve years `[2021, 2023, 2024, 2025]` — 4 solve-years, inside the
§2.1b ≤5 cap. **2022 is BRIDGED** — evolved, never solved, its data never read.
**2021 is the seed and is NEVER scored.** Scoring is **2023–2025 ONLY**.

**Then, in order:** `score_crossover.py --bundle <out>` →
`register_hindcast.py --bundle <out>`, the sibling sequence
(`scripts/probes/fh5_run_leg.sh`). **The arm registers regardless of verdict or
reads** (rule 15 / the FH-4 registration commitment).

## 3. THE RIDER, pre-registered

`scripts/check_forecast_invariants.py` runs on the arm. **I6** (single-year
economic retirement > 0.20 of prior thermal MW) is the rider criterion: an **I6
FAIL is a STOP-THE-LINE report to the manager, never a skill claim** — the run is
still registered with its verdict and numbers, and no skill read from it is
quoted. I7 and I12 are reported alongside at full magnitude; they are not the
criterion. The I6 rider PASSED on all eleven siblings, so a FAIL here would be
this arm's own finding.

## 4. WHAT THIS ARM CAN AND CANNOT SAY — pre-registered

FH-5 §1.3's confound binds unchanged: **Arm K's horizon read is confounded by
AEO-edition luck** (AEO2021 sat closer to realized 2023–2025 gas than AEO2023
did), so **a Phase-B Arm K that scores better than a Phase-A Arm K is not
evidence that a longer horizon forecasts better.** The headline horizon claim
rests on Arm R and is unaffected by this cell.

What this arm DOES complete is the §4.1 dominance table, which is computed from
`forecast_err` per ISO × metric and currently carries **no CAISO Arm K
contribution**. Pre-registered: the completed table is regenerated with
`scripts/probes/fh5_horizon_table.py` verbatim — **no new metric, no
re-derivation** — and §4.1's headline ("year effect dominates in 12 of 13 cells")
is re-checked against the new cells and **reported whichever way it lands**. If
the new cells overturn it, that is this lane's finding, reported as such, not
smoothed over.

**Reading rule (rules 1 / 13).** Nothing is tuned in response to any number
produced here. A large or growing gap is the measurement, not a failure to fix.

## 5. GOVERNANCE, pre-registered

- **Rule 22.** Solve years `{2021, 2023, 2024, 2025}`; 2021 is the T1-H-allowed
  unscored seed, 2022 bridged and never solved; **scoring never leaves
  2023–2025**, the training tier. **CAISO holds no `complete` and no `final`
  marker and needs neither** — nothing out-of-training is solved or scored. The
  holdout freeze is ACTIVE, read at launch by the harness and recorded in
  `meta.json`; it is untouched. No measured H1-2026 contact.
- **Namespace (rule 15).** Hindcast namespace ONLY —
  `frontend/data/hindcast/caiso-2021-2025-t1ff-armk-fh5.json`,
  `meta.kind="full_forward"`, registered exactly as the eleven siblings.
  **NEVER** the backcast registry; never `frontend/data/forecast/`.
- **Rules 1 / 13 / 14.** No tuning, no bar re-level, no signal scaling, no band
  widened, no default flipped, no keeper touched, no promotion.
- **Rule 28.** This lane tests **no new mechanism** and arms nothing beyond the
  pre-registered arm, so **no new matrix row is owed** (duty c does not fire) and
  **no verdict cell moves**. Any citation added goes to CAISO's own shard
  (`docs/codebase-site/data/mechanism-matrix/CAISO.js`) and never another ISO's
  (rule 25).
- **Rule 23 / E10.** No keeper promoted; no attestation owed.
- **Rule 27.** Opus. Edits are local on-disk bytes; no `push_files` of any
  ≥300-line file; no new GitHub Actions workflow.
- **Deliverable shape.** FH-5's landed §1–§7 are **never edited**. The completion
  lands as an **ADDENDUM `§8 Arm K completion`**.

## 6. CONTAINER NOTE

The clone arrived half-dead (mass staged deletions, missing worktree, stale
`.git/index.lock`) — the third-plus occurrence of the documented failure. It was
recovered per the standing solve-lane recipe (`rm` the lock, `git read-tree
HEAD`, `git checkout -- .`; all blobs local in the 7.5 GB pack), restoring
`data/raw` to its full 9.6 GB and the worktree to 0 pending paths, **before** the
branch was cut. No blob was fetched from the remote to do it.
