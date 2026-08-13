# FFR-9C-PROMOTE completion — the stage-B rule-28 half, the epoch declaration, and what broke

**Lane.** FFR-9C-PROMOTE continuation `[FABLE]`, branch
`claude/ffr-9c-stage-b-commit-av87x7`, off `origin/main` **`9c52ea8`**
(2026-08-13). Owner card **D-30, SIGNED 2026-08-11, sitting Addendum AK.8**.
Predecessor lane: `claude/ffr-9c-promote-stageb-hlfnpg` (merged and deleted
mid-lane; see §1). Pre-registration:
`docs/handoffs/PREREG-ffr-9c-promote-stageb-2026-08-12.md` (its §6 is this
lane's execution record).

---

## 1. What this lane found on arrival — the plan it was given was already moot

The continuation brief said: amend `a71fc84d` on
`claude/ffr-9c-promote-stageb-hlfnpg` and force-with-lease, so ERCOT.js and the
promotion land as ONE commit (rule 28). At this lane's head that was
impossible, for the sharpest possible reason:

**`a71fc84d` — subject "FFR-9C-PROMOTE: arm stage B for ERCOT (D-30)
[INCOMPLETE - do not push]" — was already merged to `main`, as PR #3888, and
the lane branch was deleted.** A commit its own author marked *do not push* is
in main's history. Sitting **Addendum AQ** (commit `51c4c36`, 2026-08-13) had
already found and adjudicated this before this lane opened: stage B IS armed on
main, the cache epoch fired **undeclared**, ERCOT joined MISO in the
control-arm exposure, and the OVERRIDE-FIX dispatch was upgraded from blocker
to live-exposure remediation. AQ.2 also verified the narrow good news: all
five flags were already in the cache-key ledgers and the ERCOT matrix shard
carried the stage-B measurement rows, so the *registration* gap was the cell
verdicts, the epoch declaration and the governance record — not the ledgers.

The rule-28 one-commit invariant is therefore **broken for this promotion and
not repairable** (history is not rewritten). This lane's commit is the owed
other half, landed as one commit, with the breach recorded rather than
papered over. This is the HOUSE-1 X.2 pattern — merges do not wait for their
own author — in its sharpest form yet; the standing-clause fix (do not title a
commit "do not push" and push it; land it complete or keep it local) is worth
a future manager ruling.

## 2. What this lane landed (one commit)

All acceptance evidence re-verified at `9c52ea8` before any edit — the PREREG
§1.6 numbers reproduce exactly: ERCOT leg passing NO stage-B flag resolves all
five armed; resolved key `8d9ef77edb3e44cb`, pre-arm pole `062d440558103f81`,
global pin `603c2498bf71d21d`; CAISO/MISO/NYISO/NEISO/PJM all construct and
resolve `False/False`.

1. **The epoch, DECLARED** (it had fired undeclared — AQ's core finding):
   * `scripts/probes/_ffr9c_stageb_cache_epoch.py` — the measured half, on the
     `_arm3arm_cache_epoch.py` (D-29) model. Three reads, ALL PASS: global pin
     unmoved; ERCOT resolved default key sits at the armed pole with the
     pre-arm pole reconstructed by `dataclasses.replace` (NOT by constructor —
     the seam would re-arm it); no other ISO moves.
   * `tests/unit/config/test_ercot_stageb_arming.py` — 10 pins on the
     `test_miso_rps_region_arming.py` model: the five-flag unit, rule 25 at
     construction (non-ERCOT restoration raises), the pair constraint, the
     seam (field defaults stay unarmed), **both epoch poles as literals** (so
     the epoch now has a test naming it), the global pin, and the backcast
     lane's byte-stability + the armed-backcast key hazard.
2. **ERCOT matrix shard** (`docs/codebase-site/data/mechanism-matrix/ERCOT.js`,
   ERCOT shard ONLY, rule 25): the five stage-B cells' `fc` verdicts **O → K**
   with the D-30 execution record — full narrative (premature merge, epoch,
   accepted cost at full magnitude, control-arm consequence, attestation
   pointer) on `entry_pipeline_aware_signal`, compact cross-referenced records
   on the other four; a 2026-08-13 tail stamp; and the header keeper re-stamp
   run191 → **`2026-08-12-run192-arm-coal-peak`** with its gates text (the
   ercot-192 lane had updated its cell but the header stamp lagged).
   `scripts/check_mechanism_matrix.py` exit 0 (the anchor-digit warnings
   pre-exist on main — 237 at HEAD before this lane's edits — and belong to the
   base file, which this lane does not touch: no new mechanism row is owed).
3. **The §1.5 correction** (owed by the FINDING §5): the PREREG's "an explicit
   caller value always wins" is struck and restated — callers passing a
   NON-default value stay byte-identical; callers passing the default value
   are overridden. The same false claim sat in the `iso_configs.py` comment
   block above the override rows (inherited from the PREREG) and is corrected
   there too, along with sharpening its ambiguous "the pinned default cache
   key MOVES" line (the GLOBAL pin does NOT move; the ERCOT resolved key
   does).
4. **C6 attestation**:
   `results/calibration/ATTESTATION-ffr9c-stageb-promotion-2026-08-13.json`
   (`"schema": "calibration-attestation/v1"`, 4/4 governance assertions,
   empty exceptions ledger, zero-parameter DOF block; PREREG §4 / E10).
5. **PREREG §6 execution record** + this handoff.

## 3. The epoch — operational consequences (unchanged from the PREREG, now enforced)

* Every pre-epoch ERCOT forecast/hindcast sidecar is **historical record and
  never a post-epoch baseline** — FH-5's ERCOT legs included. FH-5 is NOT
  re-solved and NOT "refreshed"; its artifacts pin `src/ == 3ae7465`.
* The accepted cost, at full magnitude as signed: **wind −57 % → −73 %;
  CC GW error +5.8 → +8.8; CO2 2023 −11.28 → −12.84** — against: additions
  basis 45.05 → 50.0 GW vs 55.4 actual; solar −60 % → −40 %; and the
  mid-window price/reserve objects land onto measured levels for the first
  time in this posture.
* The ERCOT **backcast** lane is untouched: the calibration path never applies
  ISO scenario overrides, every backcast key is byte-stable (pinned), and the
  keeper `2026-08-12-run192-arm-coal-peak` is unaffected.

## 4. OPEN — the owner decision this lane surfaces and does NOT take

`FINDING-ffr-9c-iso-override-precedence-2026-08-12.md`: with stage B armed, an
ERCOT control arm is **inexpressible through the config path and fails
silently** (a caller's `False`/`None` equals the field default and is re-armed).
Addendum AQ upgraded the dispatched **OVERRIDE-FIX** lane (§0ap-1) from blocker
to remediation of a live two-ISO exposure (MISO D-29 + ERCOT D-30) and flagged
one stale line in its prompt ("ERCOT's stage-B rows are NOT on main") that the
manager must correct before pasting. The prior session's read — remedy 2,
track explicitly-set fields at the seam — stands recorded in the FINDING §4;
the choice among the three remedies is the owner's / that lane's, not this
one's. This lane deliberately wrote **no test pinning today's defective
precedence**, so OVERRIDE-FIX inherits no test it must rewrite.

## 5. Container provenance (recorded for reproducibility)

This container's initial clone arrived half-dead in a NEW variant: `.git`
intact at `8efea89` with a stale 0-byte `index.lock`, an **empty index** (all
~11k tracked paths staged-deleted) and **8,049 files missing from the working
tree** (`docs/handoffs/` entirely absent) — the checkout died partway, one step
further along than the §5 zero-commit case the PREREG documents. Recovery:
remove the stale lock, `git read-tree HEAD`, `git checkout -- .` (all blobs
were already local in the 7.5 GB pack), then branch from a fresh
`origin/main`. The environment-side clone filter remains unset (PREREG §5
item 1) — this recurs, in varying stages of death, every container.
`git push` from this container works with a generous timeout (see the
continuation brief's measured 1m42s; never 120 s).
