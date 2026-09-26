# FINDING — capx D98: the recorded-surface construction (Q71) — `check_key_provenance` EXIT 1 → 0

Lane capx D98 · Opus · ZERO LP · DATA PROFILE code · branch `claude/capx-d98-surface-construction`
off `origin/main` `f1ea324a`. PRECOMMIT `docs/handoffs/PRECOMMIT-capx-d98-2026-09-26.md`, pushed
first (`b99eec98`). Authority: owner ruling Q71, "Add the construction." (capx ledger §0bl).

## 0. THE CENSUS, BEFORE AND AFTER

`python3 scripts/check_key_provenance.py` (fetch on):

| state | census line | exit |
|---|---|---|
| before (`b99eec98` = `f1ea324a` + PRECOMMIT) | `248 … 192 reproduce, 28 have no key, 28 mismatch` — `16 KNOWN, 10 LAG, 2 UNKNOWN` | **1** (`G1_UNKNOWN` × 2: the d94 legs) |
| after (`18f0bcc2`) | `248 … 192 reproduce, 28 have no key, 28 mismatch` — `16 KNOWN, 10 LAG, 2 SURFACE-RECORDED, 0 UNKNOWN` | **0** |

**Both lines equal the PRECOMMIT's prediction.** The reproduce and mismatch totals do not move, because
the new class is reported inside the mismatch count, the same way `LAG` is. The two new report lines:

```
SURFACE-RECORDED (Q71 construction): results/ff-t3-neiso-golden/d94/vre_long/run_config.json <- moved {'RGGI_MEMBER_STATES_BY_YEAR': '94d8b85ac442ecfd'} from …/d94/vre_long/NEISO/df7b178ae9ccbe41/solve_surface.json; reproduces df7b178ae9ccbe41
SURFACE-RECORDED (Q71 construction): results/ff-t3-neiso-golden/d94/vre_short/run_config.json <- moved {'RGGI_MEMBER_STATES_BY_YEAR': '94d8b85ac442ecfd'} from …/d94/vre_short/NEISO/1be407901f4f8000/solve_surface.json; reproduces 1be407901f4f8000
```

## 1. WHAT WAS BUILT

`scripts/lib/key_provenance.py`:

* `head_key(..., surface_block=)` is the third construction. It appends the given `moved` block as
  `__solve_surface__`. It cannot be combined with `surface=True`, and an empty block collapses to the
  declaration key.
* `recorded_surface_stamp` reads the block only from
  `<run_config dir>/<ISO>/<recorded cache_key>/solve_surface.json`. That path is set by the record's
  own literal, so a record cannot borrow another bundle's stamp. The construction applies only if all
  of these hold:
  * the stamp is in `git ls-files`;
  * `schema == 1`;
  * the stamp's `iso` matches the record's;
  * `moved` is a `{str: str}` map;
  * `epochs` is empty.

  If any of these fails, the construction cannot apply. The block is read from the stamp, never
  synthesized.
* `surface_recorded_verdict` and `surface_recorded_classifications` run only on mismatches, and they
  re-derive the result from the committed bytes. The census records class `surface-recorded` and skips
  the recipe ladder for those rows. `lag_classifications` skips them too, so each record gets one class.
* `check_exceptions(..., surface=)` has three outcomes:
  * a `surface-recorded` row is exempt from `G1_UNKNOWN`;
  * a stamp that exists but does not reproduce stays `G1_UNKNOWN`, with the verdict attached;
  * a **listed** entry that the construction derives is `G2_STALE`.

`scripts/check_key_provenance.py` prints the `SURFACE-RECORDED` count and one line per record.

`key-provenance-exceptions.json` and the lag-registration table are **untouched**.

## 2. WHICH BUNDLES MOVED CLASS

There are 14 committed `solve_surface.json` bundles at `f1ea324a`, not the 10 in the charter: D96
landed four after D95. **Exactly two moved: d94/vre_long and d94/vre_short, UNKNOWN → `surface-recorded`.**

| bundles | result under the new construction |
|---|---|
| seven with `moved: {}` | still reproduce at declaration |
| the four D96 legs | still reproduce on the live surface |
| d90-rescore | stays a Q66 `LAG`: its empty block gives the declaration key, which does not reproduce |

Records with no committed stamp (every pre-D79 bundle) cannot reach the construction.

## 3. TESTS (both directions, synthetic, offline, fast tier)

Six new tests are in `tests/regression/test_key_provenance_exceptions.py`, prefixed `test_q71_`:

* a reproducing stamp classifies the record and no gate fails;
* a perturbed literal gives `G1_UNKNOWN`;
* **no stamp:** the construction does not apply and the record is `G1_UNKNOWN`;
* **uncommitted stamp:** the same, `G1_UNKNOWN`;
* **tampered `moved` block:** `G1_UNKNOWN`, and an empty block is also `G1_UNKNOWN`;
* a listed entry that the construction derives gives `G2_STALE`.

The whole file passes (see the PR). `ruff check` and `ruff format` are clean.

## 4. BOUNDARIES AND RESIDUALS

* Zero LP. No `src/` edits, no surface row re-declared, no exception or lag row added.
* Rule 27: `key_provenance.py` (1453 lines) and the test file (557 lines) were blob-verified after
  push. Local and remote shas are identical.
* **No residuals:** EXIT 0. Concurrent D99 will add run_configs, so the census is re-run after the
  final rebase and reported in the PR.
* Forward effect, stated: from now on, a record solved on a moved surface (every post-`5f8d153c`
  solve) goes to `surface-recorded` on its ISO's next surface move, not to `G1_UNKNOWN`. This holds as
  long as its bundle's `solve_surface.json` is committed. The four D96 legs are the next such records.
