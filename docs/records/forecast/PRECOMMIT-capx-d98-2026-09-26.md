# PRECOMMIT — capx D98: the recorded-surface construction (owner ruling Q71)

Lane capx D98 · Opus · ZERO LP · DATA PROFILE code · branch `claude/capx-d98-surface-construction`
off `origin/main` `f1ea324a`. Charter: `capx-director-prompt-pack-2026-08.md` "D98"; context: capx
ledger §0bl; attribution: `FINDING-capx-d95-2026-09-25.md`. Pushed BEFORE any code.

## 1. THE CONSTRUCTION (what will be built)

A third key construction in `scripts/lib/key_provenance.py`, beside "declaration" and "live":
hash the record's own payload with the `moved` block from **its own committed**
`<run_config dir>/<ISO>/<recorded cache_key>/solve_surface.json` appended as `__solve_surface__`.

* **Applicability legs (all must hold, else the construction cannot apply):** a recorded key; the
  stamp path is in `git ls-files` (an uncommitted stamp is not evidence); `schema == 1`; the stamp's
  `iso` equals the record's; `moved` is a `{str: str}` object; `epochs` empty (not modelled). The
  path is derived from the record's OWN literal, so a record can never borrow another bundle's block,
  and the block is READ, never synthesized.
* **Reached only by a mismatch** (neither declaration nor live reproduces). A record reproducing under
  it is classified **`surface-recorded`** — a REPORTED class, one printed line per record like the
  Q66 `LAG` rows, counted in the mismatch total and on the "KNOWN / LAG / SURFACE-RECORDED /
  UNKNOWN" line. A stamp that exists but does not reproduce (tampered block, perturbed literal) is
  NOT a pass-through: the row stays `G1_UNKNOWN`.
* A **listed** exception that the construction derives is `G2_STALE` (dead scaffolding).
* `key-provenance-exceptions.json` is **not** touched; no lag-table row is added.

## 2. EXPECTED CENSUS (`python3 scripts/check_key_provenance.py`, fetch on)

| state | census line | exit |
|---|---|---|
| before (`f1ea324a`) | `248 … 192 reproduce, 28 have no key, 28 mismatch — 16 KNOWN, 10 LAG, 2 UNKNOWN` | **1** |
| after (this lane) | `248 … 192 reproduce, 28 have no key, 28 mismatch — 16 KNOWN, 10 LAG, 2 SURFACE-RECORDED, 0 UNKNOWN` | **0** |

The "reproduce" and "mismatch" totals do not move: the class is reported inside the mismatch count,
exactly as `LAG` is. (Measured in this clone with `--no-fetch`: the same 28 mismatch, of which the
10 Q66 rows read `G1_LAG_UNVERIFIED` because the history is shallow; the fetch run resolves them to
`LAG` as D95 measured. If the fetched before-line differs from the row above, the FINDING reports the
measured line and the difference.)

## 3. WHICH COMMITTED `solve_surface.json` BUNDLES MOVE CLASS

The charter says 10 bundles; at `f1ea324a` there are **14** (D96 landed four since D95). Zero-code
probe (head_key with the stamp's block substituted), per bundle:

| bundle | `moved` rows | today | after |
|---|---|---|---|
| `capacity-hindcast/pjm-…-d75rarm`, `…-d84arm` | 0 | reproduce (declaration) | unchanged |
| `ff-t1f-d65br/{caiso,miso,pjm}` | 0 | reproduce (declaration) | unchanged |
| `ff-t3-neiso-golden/bau-d65br` | 0 | reproduce (declaration) | unchanged |
| `hindcast/spp-…-spp60` | 0 | reproduce (declaration) | unchanged |
| `ff-t3-neiso-golden/d96/{base,carbon_plus25,gaspm5,gasup150}` | 7 | reproduce (live only) | unchanged |
| `ff-t3-neiso-golden/d90-rescore` | 0 | Q66 `LAG` | unchanged (its empty block = the declaration key, which does not reproduce) |
| **`ff-t3-neiso-golden/d94/vre_long`** | 1 | **`G1_UNKNOWN`** | **`surface-recorded`** |
| **`ff-t3-neiso-golden/d94/vre_short`** | 1 | **`G1_UNKNOWN`** | **`surface-recorded`** |

**Exactly two records move class**, both from UNKNOWN to `surface-recorded`. Every record with no
committed stamp (all pre-D79 bundles) cannot reach the construction.

## 4. TESTS (both directions, D91 doctrine; synthetic, offline, fast tier)

1. a synthetic record whose committed stamp's `moved` block reproduces its literal → `surface-recorded`,
   no gate failure;
2. the same record with a perturbed literal → `G1_UNKNOWN`;
3. the same record with NO `solve_surface.json` → construction does not apply → `G1_UNKNOWN`;
4. the same record with a tampered `moved` block → `G1_UNKNOWN`;
plus: an uncommitted stamp cannot be used; a listed entry the construction derives → `G2_STALE`.

## 5. BOUNDARIES

Zero LP. Edits: `scripts/lib/key_provenance.py`, `scripts/check_key_provenance.py`,
`tests/regression/test_key_provenance_exceptions.py`, this PRECOMMIT and the FINDING. Rule 27:
`key_provenance.py` is ≥300 lines — blob-verified after push. Concurrent D99 adds run_configs; the
census is re-run after the final rebase and the FINDING reports that line.
