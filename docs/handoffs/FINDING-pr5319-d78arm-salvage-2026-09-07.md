# FINDING — PR #5319 (capx D78-ARM) salvage review: the config act is sound and reproduces at HEAD; the solve, the scoring and the registration are still owed

**Lane:** salvage review of `claude/pjm-retirement-sector-gate-at0cao` (PR #5319, open,
2 commits past its merged PRECOMMIT #5317). The D78-ARM lane was **interrupted mid-execution**
by an owner reassignment to SPP-14 and left its own handoff in the WIP commit message
(`3b369f26`). This doc is the salvage verdict, measured — not a re-derivation.

**Verdict: YES, salvage almost all of it.** The arming act itself is complete, correct and
reproduces at today's `main` byte-for-byte, three merges later. What is missing is the *back
half* of owner ruling **Q56** ("ARM, **REGISTRATION REQUIRED**"): the armed `pjm-t1h`
re-solve, its scoring and its registration. Nothing measured had to be re-derived to
establish that.

## 1. What reproduces at HEAD, unchanged (SALVAGED AS-IS)

Measured at `8c5ee2ef` (`origin/main` 2026-09-07), through the shipped harness path the
PRECOMMIT declared:

| check | result |
|---|---|
| `docs/handoffs/d78arm/keys_probe.py` re-run at HEAD vs the branch's committed `keys_measured.json` | **byte-identical** |
| every key leg of `PRECOMMIT-capx-d78arm-2026-09-06.md` §2 (13 rows) | **all reproduce**, bare `pjm-t1h` `b518f5fe7d02f961` → `fb16fda2ddb0a94a`, `--no-retirement-sector-gate` unmoved at `b518f5fe7d02f961` |
| `scripts/probes/capxd78arm_iso_override_no_op_check.py` at HEAD | **the structural property holds**: every moved key is PJM/forecast; every non-PJM and every backcast config byte-identical |
| the branch's re-pinned `tests/unit/model/test_capacity.py`, `test_d53_sector_gate_miso_arming.py`, `test_d60_arming_batch.py`, `test_d67arm_pjm_requirement.py::TestD67ArmGdriftPosture` | **pass** |

So the following are salvaged verbatim: the `_pjm_config` override + its cite block, the
`results/cache.py` epoch entry, the CLAUDE.md capacity-evolution bullet, the
`--retirement-sector-gate` help string, the `build_forecast_dof_ledger.py` PJM row, the
override pin and the three posture tests, `docs/handoffs/d78arm/keys_measured.json`,
`docs/handoffs/d78arm/run_arm.sh`.

## 2. What was STALE and is corrected here

1. **The census numbers moved with `main`.** The branch measured **21 of 157** committed run
   configs; at HEAD it is **25 of 173** (`no-op-measured.json` re-measured; the counts
   corrected in CLAUDE.md and the cache epoch). The *property* — all moves PJM/forecast, every
   backcast key byte-identical — is unchanged, which is the thing the probe exists to assert.
2. **The PJM matrix row conflicted.** The branch flipped `fc: "O" → "K"` on a **pre-D78-R3**
   copy of the row's evidence text; `main` has since grown that text by ~4.3 KB (the D78-R /
   R2 / R3 evidence). Taking the branch's row would have **reverted** that. Resolved by
   keeping `main`'s text and prepending the arm record, `fc: "K"` (the Q52 / Q55 precedent for
   an armed-but-unregistered PJM forecast mechanism).
3. **`TestQ52ArmingKeys` was owed and is now fixed.** The WIP handoff read this file as
   already red on `main`; it is not — another lane re-pinned it on 2026-09-07 to the *pre-D78*
   values. The arm restales it again, exactly as that file's own note predicts ("A future PJM
   arm must re-measure it here"): `BARE_PJM_ARMED` → `fb16fda2ddb0a94a`, and the (b′-1)
   inverse leg needs `retirement_sector_gate=False` beside the Q55 inverse to keep reaching
   `15a723ba3b6dc856`. Both measured, not assumed.
4. **A citation to a document that does not exist.** `iso_configs.py` and CLAUDE.md cited
   `FINDING-capx-d78arm-2026-09-06.md`, which the interrupted lane never wrote. Replaced with
   the PRECOMMIT plus an explicit statement of what is still owed.

## 3. What is HELD, and why

**`scripts/register_forecast_run.py`'s `VERDICT_MAP` re-key is NOT salvaged into this branch.**
The branch's hunk re-keys the D67-ARM bundle to `pjm-t1h-pre-d78arm` and gives the bare
`pjm-t1h` verdict to `pjm-2021-2025-realized-t1h-d78arm` — **a bundle that does not exist**,
because the solve never ran. Measured through `rescore_forecast_verdicts.plan()`: with the
hunk, the board verdict `pjm-t1h` reverse-maps to a nonexistent run, and the D67-ARM bundle
(which is on disk) maps to `pjm-t1h-pre-d78arm`, an id absent from `ff-verdicts.json`. That
re-key is correct **at registration** and wrong before it, so it lands with steps 3–5 below.

## 4. Still owed by the D78-ARM lane (the WIP commit's own list, re-verified)

1. `bash docs/handoffs/d78arm/run_arm.sh` — the armed `pjm-t1h`, key `fb16fda2ddb0a94a`,
   PJM solo, years sequential (rule 12), HEAD-guarded. *(A `data/clean` rebuild may be needed
   first; the interrupted session's was killed at 6/56 datatypes.)*
2. `score_capacity_hindcast.py --bundle … ` + `--flip-gate-extras`.
3. `register_forecast_run.py --bundle …`, landing the held `VERDICT_MAP` re-key **with** it.
4. The slim record + sidecar commit and `FINDING-capx-d78arm-2026-09-06.md`.
5. The board snapshot stays **HELD** (D65-B-R lock), per the lane's charter.

Q56 is not discharged until 1–4 land. This branch discharges the **config act only**, and says
so in every artifact it touches.
