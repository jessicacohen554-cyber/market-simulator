# FINDING — Stage-0 golden provenance repair (audit item 11, the five-wide defect)

**Date:** 2026-09-01 · **Lane:** `claude/stage0-provenance-repair-jguqmo` ·
**Owner ruling:** 2026-09-01, audit-program board v17 RESTART CHECKLIST item 11 + F-5.

**Pin:** `origin/main` = `6f6e9d11f9ae88ea4005686efe75f3a39e84ea7b` (merge of #4486),
held stable across two consecutive polls before the branch was cut. Every
measurement below is at this pin. *(`origin/main` advanced to `e2fa8ab005` during
the unshallow fetch described in §2; the pin was NOT moved, and every ancestry
test in this document is against `6f6e9d11`.)*

**Scope bar honoured.** `scripts/capture_keeper_goldens.py` was **not run**. **No
golden was captured, no LP solved, no year solved, no run registered.** No
mechanism tested, no matrix shard touched. The golden tier and WS3 remain
**PARKED** — nothing here un-parks either, and **this lane makes no byte-green
claim**. The repair is entirely records + tooling on committed artifacts.

---

## 1 · Headline — the five shas are NOT unrecoverable; all six are recovered with evidence

The dispatch's expectation was that the five older captures' true provenance shas
were *"very likely UNRECOVERABLE — the field was overwritten, not versioned."*
**That is wrong, and it is wrong in the good direction.** The field was
overwritten *in the working tree*, but every intermediate value was **committed**
on its way through. The manifest's own git history therefore preserves, for each
capture, exactly the sha that capture wrote — before the next one overwrote it.

**All six are recovered. None is invented, inferred, or back-dated. None needed
to be recorded UNKNOWN.**

| ISO | entry-adding commit | `git_sha` that capture wrote | resolves at pin | ancestor of `main` @pin | prefix unique |
|---|---|---|---|---|---|
| ERCOT | `dd8b7265` 2026-08-16T21:29:46Z | **`ec413d20`** | yes | **yes** | yes |
| NEISO | `c55d558b` 2026-08-17T02:37:04Z | **`ebd31a9`** | yes | **yes** | yes |
| NYISO | `9f6ff3ee` 2026-08-17T03:04:23Z | **`2dd9dbc`** | yes | **yes** | yes |
| CAISO | `af1ccb6c` 2026-08-17T03:34:14Z | **`9f6ff3e`** | yes | **yes** | yes |
| MISO | `eef80c11` 2026-08-17T04:18:54Z | **`af1ccb6`** | yes | **yes** | yes |
| PJM | `29a9cba5` 2026-08-30T21:29:00Z | **`1cfea72`** | yes | **yes** | yes |

**Method (reproducible, zero-solve).** For each of the six commits that touched
`results/regression-goldens/perfb-stage0/manifest.json`, read that commit's
manifest blob and take its top-level `git_sha`. Which capture wrote it is fixed
independently by the `keepers` key-set delta against the previous blob — the
entry sets grow strictly `{ERCOT} → {+NEISO} → {+NYISO} → {+CAISO} → {+MISO} →
{+PJM}`, one ISO per commit, so each commit's sha is unambiguously that ISO's.

**The chain self-corroborates.** CAISO's recorded sha `9f6ff3e` *is* the NYISO
capture commit, and MISO's `af1ccb6` *is* the CAISO capture commit — exactly what
a single session that commits each capture and keeps working must produce. A
fabricated or mis-assigned set could not reproduce that interlock.

### 1.1 Two board claims re-derived DIFFERENT

| board (v15/v16/v17) asserted | re-derived at this pin |
|---|---|
| `af1ccb6` *"did not resolve at all"* | **resolves**: `af1ccb6ca76ae9b8f4a0e0a8060c308995678659`, and is an **ancestor of `main`** — it is the CAISO capture commit |
| the five true shas are *"very likely UNRECOVERABLE"* | **all five recovered**, each with corroboration; **zero UNKNOWN rows written** |

The "did not resolve" reading was a **shallow-clone artefact**, not a property of
the repository. This session's container cloned `main` at depth 258 (oldest
commit 2026-08-30), so every 2026-08-16/17 capture commit was simply absent
locally. `git fetch --filter=blob:none --unshallow` restored 13,936 commits in
**4.6 s**, after which all seven shas resolve. **Any future lane reading a sha as
"unresolvable" must rule out clone depth before recording it as such** — this
defect has now been mis-diagnosed for three consecutive board cycles.

### 1.2 The two manifest-vs-commit-message discrepancies, resolved and immaterial

Two capture commit messages name a tree different from the manifest stamp. The
field's own semantics explain both: `_git_sha()` is `rev-parse --short HEAD` at
**manifest-write** time, while the message states the tree the **solve** ran at.
Where they differ, the delta was measured:

| ISO | message says | manifest stamps | `git diff` between the two trees |
|---|---|---|---|
| ERCOT | `f8c93afe` | `ec413d20` | **only** `scripts/capture_keeper_goldens.py` (the `basis_sha` fidelity-oracle ignore) — **no model code differs** |
| CAISO | `2dd9dbc` | `9f6ff3e` | **only** this manifest (the NYISO entry landing mid-solve) — the trees are **code-identical** |

NEISO (`ebd31a9`) and NYISO (`2dd9dbc`) match their messages **exactly**. MISO's
message names no tree; its own recorded year totals (643.3/594.3/537.0 s = 29.6
min) place the solve start after the CAISO capture commit (03:34:14Z) and before
its own (04:18:54Z), so HEAD was `af1ccb6` throughout — consistent, but with no
independent sha to cross-check, and recorded as such. PJM's stamp is corroborated
by `docs/model-audit-release-plan-2026-08.md` (Card-1, merged as #4369).

Both discrepancies are recorded verbatim in each entry's `provenance.recovery`
block rather than smoothed away. The 2026-08-17 staleness ledger
(`docs/handoffs/perfb-stage0-staleness-ledger-2026-08-17.md`) independently names
the same solve trees for ERCOT, NEISO, NYISO and CAISO — a fourth corroborating
source, written by a different lane, two weeks before this repair.

---

## 2 · What was built

### (a) Per-entry provenance — `manifest.json` schema **v2**

Schema v1 held **one** top-level `git_sha` / `git_dirty` / `env` /
`highspy_version` block for however many captures the manifest contained. Because
`write_manifest` **merges** a single ISO's entry into the existing file, every
capture silently re-stamped that shared block for all the earlier ones. Six
captures at six trees ended up asserting one tree, and the five older rows carried
a sha that was **valid and wrong** — strictly harder to notice than one that does
not resolve.

In v2 those four fields live in `keepers.<ISO>.provenance`, written by the capture
that owns the entry and never touched again. The top level keeps only what is
genuinely global: `schema_version`, `stage_tag`, `hash_scheme`, `note`. Each
entry's provenance carries:

`git_sha` · `git_sha_full` · **`basis_sha`** · `git_dirty` · `recorded_at` ·
`recorded_at_basis` · `env` · `highspy_version` · `source` · `recovery{…}`

`basis_sha` is deliberately the repo's existing durable-provenance primitive
(`market_sim.pipeline.persist.basis_sha` — `merge-base(HEAD, origin/main)`, full
length), added because a capture's `git_sha` is routinely a session-local branch
commit that squash-merge destroys. That is the *general* form of the very failure
mode this finding repairs, and it was already solved elsewhere in the codebase;
the manifest simply had not adopted it.

### (b) The capture tool can no longer produce the defect

`scripts/capture_keeper_goldens.py` (639 → 753 lines) now stamps `provenance`
and `keeper_snapshot` into the entry it is writing, and `write_manifest` emits no
capture-specific value at the shared scope at all. A future capture of one ISO is
structurally incapable of re-labelling another's. Rule 27 `[R-PUSH]` observed
throughout: edited locally with the Edit tool, pushed as exact on-disk bytes,
blob-verified after the push (§5).

### (c) Retention reconciled **on the manifest side**, and made visible

Per the board, golden runs are **not** exempted from top-15 retention — that would
re-create the dead-bundle class the parity gate already struggles with. Instead
each entry now carries a **`keeper_snapshot`** copied from the provenance run's
registry sidecar *at capture time* (`id`, `iso`, `label`, `date`, `shorthand`,
`definition`, `years`, `bundle`, `sidecar_at_capture`). The entry stays fully
meaningful after its sidecar is pruned, so the prune costs nothing.

The five orphaned snapshots were backfilled from history, not invented: each
pruned sidecar was read from the last commit in which it existed. Every recovered
`bundle` and `years` was asserted **equal to the manifest entry's own** before the
snapshot was written — five independent consistency checks, all passing. And
`sidecar_at_capture: "present"` is *provable* rather than assumed:
`resolve_keeper_bundles()` raises `FileNotFoundError` on a missing sidecar, so a
capture cannot have run without its own.

### (d) A new gate: `scripts/check_golden_manifest.py`, wired into existing CI

Reads committed artifacts only; no solve. Added to the **existing**
`.github/workflows/ci.yml` `keeper-gates` job, beside
`check_registry_payload_parity` (the same registry↔artifact coupling). **No new
workflow file** — private repo, billed minutes.

It **FAILS** on: schema below v2 for any non-grandfathered stage tag; any
forbidden shared top-level key; a missing/incomplete `provenance`; a bare
`git_sha: "unknown"` with no stated reason; a missing `keeper_snapshot`; and a
snapshot whose `id`/`bundle`/`years` disagree with the entry it lives in.

It **REPORTS without failing** — this is the coupling that was silent — per entry:
whether the provenance run is still registered or **PRUNED**, and whether the
golden is **CURRENT** or **STALE** against the live keeper shard. A prune is not a
failure; retention is correct policy. The failure is a prune landing on an entry
that never absorbed its snapshot, which is the only state in which a prune
actually destroys information.

Verified bidirectional: exit **1** against the pre-repair v1 manifest, exit **0**
against the repaired one.

---

## 3 · Item 4 — which entries are CURRENT, re-derived not trusted

Re-derived at the pin from `frontend/data/backcast/keepers/<ISO>.json` and
`frontend/data/backcast/registry/`:

| ISO | golden captured against | live keeper @pin | golden | provenance run in registry |
|---|---|---|---|---|
| PJM | `2026-08-15-pjm-162-inputclock` | same | **CURRENT** | **PRESENT** |
| CAISO | `2026-08-16-caiso-197-w2-r5` | `2026-08-26-caiso-220-c1-crosswalk` | STALE | PRUNED |
| ERCOT | `2026-08-15-ercot204-rule26-delete` | `2026-08-25-234-eastex-identity` | STALE | PRUNED |
| MISO | `2026-08-16-miso-160-wefor-shape` | `2026-08-30-miso-191-bexit` | STALE | PRUNED |
| NEISO | `2026-08-14-neiso-93-envelope` | `2026-08-17-neiso-99-joint-p1` | STALE | PRUNED |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | `2026-08-30-nyiso-159-loss-surface` | STALE | PRUNED |

**The director's derivation is CONFIRMED exactly**: PJM CURRENT, the other five
STALE; five of six provenance runs pruned, PJM's alone registered. This is now
machine-derived on every CI run rather than re-typed each board cycle.

**ERCOT carries an extra condition this table cannot express.** Its keeper is a
**two-config partition** since the 2026-08-26 owner ruling (2023 carve-out +
2024/2025 forward, `keepers/ERCOT.json:config_partition`), whereas its golden was
captured against the single pre-partition `ercot204` config. So ERCOT is not
merely stale — a future ERCOT capture is **two** captures. Recorded; **not acted
on** (it needs captures, which this lane is barred from).

---

## 4 · 🔴 NEW — the orphaning is repo-wide at 96 %, not five-wide

Board F-5 measured `perfb-stage0` alone. Running the new gate across **every**
committed golden manifest:

> **38 manifests · 70 entries · 67 entries (96 %) whose provenance run has been
> pruned from the registry.**

The 37 pre-repair manifests (stage-1…7, wave4c/4d, the A/A determinism pair, the
`3e`/`3f`/`fuel`/`lane`/`eia930`/`constants-split`/`dispatch-lp`/`fleet-*`
before/after pairs, `perfb-d`, `perfb-e`) are **all** schema v1 and **62 of their
64 entries** are orphaned. `perfb-stage0` was not a special case; it was the one
anybody looked at.

**Scope decision, stated rather than taken silently.** Those 37 are retired stage
artifacts, not live baselines, and migrating each needs the same per-manifest
historical recovery `perfb-stage0` just received. That is a separate, owner-scoped
job. This lane therefore repairs `perfb-stage0` in full and installs a **monotone
ratchet**: `LEGACY_V1_MANIFESTS` in the gate **enumerates all 37 by name** — it is
not a glob, so a *new* stage tag can never join it silently, and any manifest
written by the current tool is enforced. A legacy manifest that is later migrated
to v2 becomes fully enforced automatically (tested).

**This 96 % figure is offered to the director as newly-surfaced scope, not as an
adjudication.** Nothing about it is fixed or hidden here.

---

## 5 · Verification

### The five program gates — before and after, exit codes captured directly

| gate | BEFORE (at pin) | AFTER (this branch) |
|---|---|---|
| `audit_keepers.py` | **exit 0** — PASS 0 failures / 0 warnings | **exit 0** — identical |
| `check_registry_payload_parity.py` | **exit 0** — 58 runs / 93 bundle dirs / 0 tolerated | **exit 0** — identical |
| `check_mechanism_matrix.py` | **exit 0** — 194 field + 49 row + 154 path anchors | **exit 0** — identical |
| `check_forecast_staleness.py` | **exit 0** — WARN-level only | **exit 0** — identical |
| `check_bench_freshness.py` | **exit 0** — 20 parts, 0 STALE, 19 with engine drift | **exit 0** — identical |

**All five gates' stdout/stderr is byte-identical before and after** (`diff`
clean on all five) — this lane moves no gated figure. The new
`check_golden_manifest.py` exits **0**.

*Note on the staleness gate:* it emits a WARN that the newest scored verdicts sha
`89dacc4c0343` is not reachable in this checkout. That WARN is present **before**
this branch's first edit and is unchanged by it; it reflects a verdict scored on a
commit merged after the pin.

### Tests — `tests/scoring/test_golden_manifest_provenance.py` (new, 20 tests)

Three classes: the committed manifest's v2 conformance (including *"the six
provenance shas must be distinct"* — the property v1 could not express); the
retention invariant on temp trees (pruned-with-snapshot **passes**;
pruned-without-snapshot **fails**; missing-snapshot fails *while the sidecar still
lives*, because absorbing it after the prune is too late; shared top-level sha
rejected; ratchet enforced on new tags and grandfathering legacy ones; a snapshot
of the *wrong* run rejected; STALE/CURRENT reported not failed); and the capture
tool itself (writes v2 only; **a second capture leaves the first entry
byte-identical** — the exact regression; `basis_sha` is a full, origin-durable
sha). **20 passed.**

Proven non-vacuous: with the pre-repair v1 manifest restored, **16 of the 20
fail** and the gate exits 1.

### Regression sweep

`tests/scoring` + `tests/regression`, fast lane, failure sets compared by name at
the clean pin vs this branch:

> **NEW failures introduced: ZERO.** (46 → 40; the six-failure delta is this
> lane's own new tests, which fail against the stashed-out repair and pass with
> it — a bidirectional proof.)

The 40 remaining failures are **pre-existing at the clean pin** and untouched by
this lane (`test_soundness.py` physics/economics, and
`test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers`,
which reads NYISO's marker as `withdrawn` where it expects `complete` — verified
failing at the pin with this branch's changes stashed).

### Rule 27 `[R-PUSH]` blob verification

`scripts/capture_keeper_goldens.py` is ≥300 lines. It was edited locally with the
Edit tool, never regenerated from response content, and pushed as exact on-disk
bytes; the pushed blob was fetched back and compared on line count and SHA-256
before any subsequent commit. Result recorded in §7.

---

## 6 · Open items for the director (adjudicated by nobody here)

1. **The 96 % repo-wide orphaning (§4).** 37 legacy manifests, 62 orphaned
   entries. Migrate, or accept and document as retired-artifact debt?
2. **ERCOT needs TWO captures, not one** (§3) — its golden predates the two-config
   partition ruling entirely.
3. **The five stale goldens.** Re-capture is a real solve (board checklist item 4:
   13.3 GiB cgroup limit, a 12 GB swapfile, a corpus re-fetch). **Untouched here
   by the scope bar** — whether to spend that compute remains the open owner
   question at the director desk.
4. **Clone depth as a diagnostic hazard (§1.1).** A shallow container clone made a
   resolvable sha read as unresolvable across three board cycles. Worth a standing
   note in the audit protocol: rule out clone depth before recording a sha as
   unrecoverable.

---

## 7 · Files changed

| file | change |
|---|---|
| `results/regression-goldens/perfb-stage0/manifest.json` | schema v1 → **v2**; six per-entry `provenance` blocks (all recovered, evidenced) + six `keeper_snapshot` blocks; shared top-level `git_sha`/`git_dirty`/`env`/`highspy_version` **removed** |
| `scripts/capture_keeper_goldens.py` | per-entry provenance + keeper snapshot; `_git_sha_full`/`_basis_sha`/`_provenance`/`_keeper_snapshot`; `write_manifest` emits v2 and no shared capture state |
| `scripts/check_golden_manifest.py` | **new** — the schema + retention-invariant gate with the enumerated legacy ratchet |
| `tests/scoring/test_golden_manifest_provenance.py` | **new** — 20 tests |
| `.github/workflows/ci.yml` | one step added to the existing `keeper-gates` job; **no new workflow** |
| `docs/FINDING-stage0-provenance-repair-2026-09.md` | this finding |

**Not touched:** the board, the release plan, any keeper shard, marker,
`holdout-freeze.json`, the registry, any mechanism-matrix shard, any bench part,
`results/regression-goldens/<iso>/` bundles. The records lane
(`claude/audit-records-v18-*`) owns the board and plan.
