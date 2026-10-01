# PRECOMMIT — capx D93: the key-provenance `lag` CLASS RULE (owner ruling Q66, "Class rule.")

Lane: capx D93 · Opus · DATA PROFILE code · ZERO LP · branch `claude/capx-d93-key-lag-class`
Charter: `docs/handoffs/capx-director-prompt-pack-2026-08.md` "D93".
Written and pushed BEFORE any edit under `scripts/` or `src/`.

## 0. STATE AT MY HEAD — THE CHARTER'S STATE HAS ALREADY MOVED ONCE

The charter quotes `40f4ed7a`: EXIT 1, **11** failures (10 `G1_UNKNOWN` + 1 `G6`). Verified at the
checkout `6640becc` (= `40f4ed7a` + the r#65 charter commit): **exactly that, 11**.

`origin/main` then advanced to **`3affcd71`**, which carries **`bb749a94` — "Y-28: register
coal_mustrun_requires_measured_row in the cache key"** (2026-09-24T15:33Z, merged via PR #6576's
line). My branch is rebased onto it. Measured there:

| gate | at `6640becc` | at `3affcd71` (my base) |
|---|---|---|
| `G1_UNKNOWN` | 10 | 10 |
| `G6_UNREGISTERED_SCHEMA_DRIFT` | 1 (`coal_mustrun_requires_measured_row`) | **0** |
| **total** | **11** | **10** |

**Part 3 is therefore already executed on `main` by Y-28, not by this lane.** I verify it rather than
redo it (§3) and make no `scenarios.py` edit.

## 1. PART 1 — THE DIAGNOSIS (measured, zero LP, before any code)

### 1(a) The six pre-D91 records — RE-VERIFIED at `3affcd71`

Each reproduces its recorded literal EXACTLY under `{"undrop": ["pjm_seam_neighbour_hourly_ladder"]}`,
each payload **carries** that field at `False` (its frozen drop value), and at each record's recorded
`git.sha` **`ee2275d2` is NOT an ancestor** (`git merge-base --is-ancestor` exit 1):

| record | solved | git.sha | undrop reproduces | ee2275d2 ancestor? |
|---|---|---|---|---|
| scn-ws5b-neiso/ALL-CLEAN | 09-09T07:06Z | e81c6e61 | yes | no |
| scn-ws5b-neiso/CAP-STATE-TIGHT | 09-09T05:39Z | 2c1b0379 | yes | no |
| scn-ws5b-neiso/CARB-HI | 09-09T07:59Z | e81c6e61 | yes | no |
| scn-ws5b-neiso/CES-P60 | 09-09T07:36Z | e81c6e61 | yes | no |
| scn-ws5b-neiso/CES-T80 | 09-09T11:21Z | e81c6e61 | yes | no |
| ff-t3-neiso-golden/d90-rescore | 09-09T02:29Z | 09ef52a3 | yes | no |

`ee2275d2197965609fe23f79d0e3005e720beed3` VERIFIED in history: "capx D91: register
pjm_seam_neighbour_hourly_ladder, repair the two guards it defeated", 2026-09-09T03:06:51Z.

### 1(b) The four d92/* legs — ATTRIBUTED BY EXPERIMENT, AND IT IS **NOT** THE G6 FIELD

The charter predicted `coal_mustrun_requires_measured_row`. **It cannot be, structurally, and it is
not, by measurement.**

* **Structural.** The census's `head_key` is payload-driven (`out = dict(payload)`): a field ABSENT
  from a payload never enters its hash. The four legs' payloads do NOT carry
  `coal_mustrun_requires_measured_row` (solved 2026-09-10; the field landed at `f7d6112c` on
  2026-09-20), so registering it can neither move nor restore their census key. The G6 field moves
  the *dataclass* construction of NEWER configs (D91's census split), not these records.
* **Measured.** On `d92/base` I ran: undrop of every registered optional field; omission of every
  `_CACHE_KEY_RETIRED_FIELDS` insertion; removal of every payload field; the live-surface
  construction. **Exactly one hit:** `{"undrop": ["caiso_dsw_lateevening_clean"]}` → `dd8203a8bf1546b9`
  = recorded. Then on all four legs:

| leg | solved | git.sha | payload `caiso_dsw_lateevening_clean` | undrop reproduces | 15beb03c ancestor? |
|---|---|---|---|---|---|
| d92/base | 09-10T07:40Z | aac390a6 | False | yes | no |
| d92/carbon_plus25 | 09-10T08:10Z | aac390a6 | False | yes | no |
| d92/gaspm5 | 09-10T07:55Z | aac390a6 | False | yes | no |
| d92/gasup150 | 09-10T08:09Z | aac390a6 | False | yes | no |

**THE ATTRIBUTION.** `caiso_dsw_lateevening_clean` (caiso-269) landed unregistered and was registered
by **`15beb03c68eb6409416cf35a19a7bfb9d08c975d`** ("Repair three CI gates that are red on main
itself", 2026-09-10T06:24:41Z). D92's shards were pinned (rule 32(c)(1)) to `aac390a6`, which does
**not** contain `15beb03c`: they solved 1 h 16 min – 1 h 46 min AFTER the registration merged, on
code that still hashed the field. D92's "they reproduce" (2026-09-10) was measured against code
that did not yet drop it. **It is D92 §2's structural shape exactly, on a second field** — and the
seam field is correctly NOT their explanation (`ee2275d2` IS an ancestor of `aac390a6`; undrop of the
seam does not reproduce them).

**THE CHARTER'S STOP CLAUSE, AND WHY I DO NOT STOP.** The charter says "If it is NOT [the G6 field],
STOP and report. Do not widen the class rule to absorb an unexplained record." The record is not
unexplained: it is named by single-field experiment, it satisfies every leg of Q66's class
independently (payload, sha, exact reproduction), and adding it costs **one table row**, which is
precisely the scaling property Q66 bought ("every future registration then adds one row").
**The row lands in its own commit**, so the director can strike it with a one-line revert if Q66 was
meant to cover only the chartered field — in which case the four legs revert to `G1_UNKNOWN` and the
gate reads EXIT 1 with four named residuals. That is the reversible reading of the stop clause.

## 2. PART 2 — THE CLASS RULE, AS DECLARED BEFORE CODING

A NON-LISTED mismatch is classified **`lag`** (reported, not a failure) iff, for some row
`{field, registration_sha}` of the committed table `docs/governance/key-provenance-lag-registrations.json`:

1. **payload leg — CORRECTED FROM THE CHARTER.** The charter reads "its payload **lacks** the named
   field". That leg is unsatisfiable jointly with leg 3: `undrop` is a no-op on an absent field, so a
   record lacking it hashes identically under the undrop and cannot be a mismatch that the undrop
   repairs. Every one of the ten **carries** the field. The encoded leg is: **the payload carries
   the field at its frozen drop value** (`cache_key_drop_defaults()[field]`) — the value at which
   today's rule drops it and the pre-registration rule hashed it.
2. **sha leg.** `registration_sha` is **not an ancestor** of the record's recorded solve sha.
   The solve sha is `git.sha` (the exact commit the solve ran at); if that does not resolve, the
   origin-durable `git.basis_sha` (`pipeline/persist.py::basis_sha`). **DECLARED FALLBACKS:**
   (i) a record with **no sha** → the leg FAILS (no class; it stays `G1_UNKNOWN`) — never a
   timestamp inference, because D92 §2 proved pinned shards solve on pre-registration code for
   hours after the merge; (ii) a record with `git.dirty: true` → the leg FAILS (the tree may carry
   an uncommitted registration); (iii) ancestry **not determinable** in this clone (a commit absent,
   or a shallow boundary reachable from the solve sha that is newer than the registration) →
   `G1_LAG_UNVERIFIED`, treated exactly as `G3_UNVERIFIED` already is: fatal in
   `check_key_provenance.py` unless `--no-fetch`, tolerated by the offline regression test. The CLI
   fetches the history it needs (`--filter=blob:none --shallow-since`), mirroring `fetch_commit`.
3. **reproduction leg.** `head_key(payload, undrop=(field,))` equals the recorded literal EXACTLY.

**A record meeting legs 1 and 2 but NOT 3 FAILS** as `G1_LAG_NO_REPRODUCE` — a real defect wearing
the lag signature. A record meeting no row stays `G1_UNKNOWN`. Every `lag` classification prints as a
REPORTED line (`LAG (Q66 class rule): <record> <- undrop <field>, <reg sha> not in solve <sha>`).
The class rule applies only to UNLISTED mismatches; listed exceptions keep their own G2–G5 gates.

**Tests, both directions** (new, in `tests/regression/test_key_provenance_exceptions.py`, offline,
synthetic, NOT census-backed so they run in the fast tier): (a) a synthetic lag record classifies
`lag`; (b) the same record with a perturbed literal → `G1_LAG_NO_REPRODUCE`; (c) a record whose
payload does not carry the field → `G1_UNKNOWN`; (d) a post-registration sha → `G1_UNKNOWN`;
plus (e) no sha → `G1_UNKNOWN`, (f) unverifiable ancestry → `G1_LAG_UNVERIFIED`. The ancestry oracle
is injectable so the synthetic tests need no real commits.

**Not touched:** `key-provenance-exceptions.json` and `key-provenance-unregistered-baseline.json`
(both records forbid appending; this lane appends to neither).

## 3. PART 3 — THE G6 REGISTRATION (already on `main` via Y-28 `bb749a94`)

Verified, not redone: `coal_mustrun_requires_measured_row` is in `_CACHE_KEY_OPTIONAL_FIELDS` and
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"`; the dataclass default is `False`; G6 reads 0.

**Orphan count** (committed configs that carry the field, i.e. solved after `f7d6112c` landed it):
**9**, and **every one has `cache_key: null`** — they are census "no key" rows and cannot mismatch.
So the orphan set that gates is **zero**. I still add the table row
`{coal_mustrun_requires_measured_row, bb749a9418fdc95d4f256883e6ee60b040e89dbe}` because a pinned
shard solving on a pre-`bb749a94` sha from now on WILL mint a keyed lag record (D92 §2's lesson);
the row makes that a reported `lag`, not a new G1. Its sha is already known and merged, so it is
not deferred to the lane's last act.

## 4. EXPECTED FAILURE COUNT AFTER EACH PART (pre-declared)

| step | expected `check_key_provenance` failures |
|---|---|
| base `3affcd71` | **10** (10 `G1_UNKNOWN`, 0 `G6`) — measured |
| Part 2, table seeded with the seam row only | **4** (the four d92 legs, `G1_UNKNOWN`); six REPORTED `lag` |
| + row `caiso_dsw_lateevening_clean / 15beb03c` | **0** — EXIT 0; ten REPORTED `lag` |
| + row `coal_mustrun_requires_measured_row / bb749a94` | **0** — moves nothing (no keyed record carries it) |
| Part 3 | **0** — already on main, no edit |

Cache-key pin tests (`tests/regression/test_persisted_identity.py`,
`tests/unit/config/test_cache_key_default_flip_guard.py`): expected **unchanged** before → after,
since this lane edits no `scenarios.py` line. Measured values go in the FINDING.

## 5. OBSERVED, NOT OWNED HERE

At `3affcd71` the census reads **0** keys reproducing under both constructions (188 at declaration
only): `RGGI_MEMBER_STATES_BY_YEAR` has moved off declaration in **every** ISO, plus three PJM RGGI
rows. That is D79's designed re-key, reported by the census and repaired nowhere; it gates nothing.

---

## ADDENDUM A1 — written after the first measurement, BEFORE the code commit (recorded, not silently folded in)

The first implementation encoded §2's declared fallback (ii) literally ("`git.dirty: true` → the sha
leg FAILS") and measured **5** failures with the seam row seeded, not the pre-declared **4**: the
extra one was `scn-ws5b-neiso/CES-T80`, recorded `dirty: true` with
`changed_files: ["docs/handoffs/FINDING-scn-ws5b-neiso-2026-09-08.md"]` — its own FINDING doc.

Fallback (ii)'s stated reason was "the tree may carry an uncommitted registration", and a
registration lives in exactly one file, `src/market_sim/config/scenarios.py`. **Refined leg (ii):** a
dirty tree fails the sha leg iff its recorded `changed_files` is absent OR contains
`src/market_sim/config/scenarios.py`. CES-T80's tree provably could not carry the registration, so
it classifies `lag`; the count then measured **4**, as pre-declared. This is a correction of an
over-broad fallback to its own stated rationale, not a widening to fit a result: the refined leg is
pinned by a test in both directions (dirty-with-scenarios.py FAILS, dirty-docs-only holds).
