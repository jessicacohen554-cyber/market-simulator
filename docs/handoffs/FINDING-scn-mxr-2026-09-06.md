# FINDING — SCN-MX-R-r2: the rule-28 duty-(c) CI gap, the CES row disposition, and the MISO cache-epoch entry

**Lane:** SCN-MX-R-r2 (relaunch of SCN-MX-R, issued at desk r#2, narrowed r#3, recorded NEVER
LAUNCHED at r#4). **Model:** Fable. **Data profile:** code. **Branch:**
`claude/scn-mxr2-matrix-duty-repair-lk9ndd` (the charter names the stem `…-t7bq`; the harness
assigned `…-lk9ndd` — same charter, one instance). **Main pin at start:** `af6269cf` (PR #4896);
rebased onto `bd0fbefd` at push, which carries the desk's r#4 refresh (`89ca4e23`). **Zero solves, zero PRECOMMITs, zero default moves, zero new
`ScenarioConfig` fields, zero cells moved.** The matrix tree (`mechanism-matrix.js` + the six
shards) was **not edited** by this lane — §2 says why.

Charter items → sections: item 1 (the CI gate defect) → §1; item 2 (the CES row, conditional) →
§2; item 3 (the cache-epoch entry) → §3; the two checker readings → §4; the record corrections
the charter asked for → §5.

---

## 0. Bottom line

| item | outcome |
|---|---|
| **1 — CI gate** | **The gate is not broken and it did not miss.** The Rule-28 guard on PR #4870 ran and **FAILED** with exactly the two expected lines (`new ScenarioConfig field federal_ces_acp_usd_per_mwh …`, `… federal_ces_target_by_year …`, job `101393800190`, exit 1). The PR was **opened 23:28:44Z and merged 23:28:49Z** — the same second its checks *started* — so no check governed the merge. The three "exited 0" readings are the checker's **validate-only mode** (no `--base`), which returns 0 before the diff gate is reached and cannot see a new field by construction. **Post-merge, nothing in the checker can see this field shape**: both diff-free ratchets are blind to a shared (no ISO stem), keeper-unarmed field. Named repair and routing in §1.4. |
| **2 — CES row** | **Did nothing; recorded as owed by SCN-WS2a.** WS-2a is in flight with the row already minted on its own branch — `d57cf785` "federal_ces_target row + one cell line per ISO shard (rule 28c, last commit)", naming both fields in its `def`, inside **open PR #4902** (head `ccdbc4a7`, opened 2026-09-06 00:22Z). Verified (§2.2): with WS-2a's seven matrix files in place, the diff gate's two field errors vanish. Racing a live lane for its own row would be the twin the desk's protocol forbids. |
| **3 — epoch entry** | **Written**, `src/market_sim/results/cache.py` ledger, newest-first, `Epoch 2026-09-05b`, WS-4a's §6 scope paragraph reproduced, three committed pre-epoch MISO sidecars named. No key, no default, no code. |
| **Checker readings** | before = after: `integrity OK … 244 unresolvable beyond the ratchet … keeper stamps match … §5.x prose headers match`, 244 `::warning` anchor lines, **EXIT=0** both times (§4). Identical because the matrix tree was not touched. |
| **Record corrections** | Desk ledger §3 row 5: the Carbon cell's stale "NOT stamped → SCN-MX-R" replaced with what is on disk (`717de664`); the CES-target cell's "CI exited 0" replaced with the job-log fact. Plan §5.1 row 5 was already correct at start (§5). |

---

## 1. The CI gate defect (item 1)

### 1.1 The mechanism of the miss — one paragraph for a repair lane

The registration predicate is sound; the gate never governed the merge, and after the merge no
leg of the checker can see the field. `scripts/check_mechanism_matrix.py` has exactly one leg
that inspects a **new** field's registration: the `--base` diff gate in `main()` (the
`if SCENARIOS_PATH in changed:` block), which regex-extracts the `ScenarioConfig` fields at
base and head (`scenarioconfig_fields`, a 4-space-indented `name:` inside the class body) and
fails on any head-only field with no `\b<field>\b` mention across the base file plus the six
shards. On PR #4870 that leg **ran and failed** — job `101393800190` prints the two
`::error … new ScenarioConfig field … is not registered` lines and exits 1 — but the PR was
created at 23:28:44Z and merged at 23:28:49Z, the same second its check runs *started*, so
the failure was reported to an already-merged PR (the guard is not a merge-blocking required
status, and seven of the PR's eleven checks were red: fast tests, refactor guards, quarantine
gates, forecast parity, invariant audit, shrink-guard, this one). The three "exited 0"
readings the desk took at `db8b6015`, `ea273339` and `21deb4a7` are the checker's
**validate-only mode**: with no `--base`, `main()` prints the anchor drift as `::warning` and
`return 0`s at `if not args.base:` **before** the diff block exists in the control flow — that
mode asserts store integrity and keeper-stamp parity, never field registration, so its 0 is
not a registration verdict. The only two legs that inspect registration **without** a diff are
the two shrink-only ratchets, and both are blind to this field shape by construction:
`gap_ratchet` iterates only fields carrying an `ISO_STEMS` prefix (`ercot_`, `caiso_`, `pjm_`,
`miso_`, `nyiso_`/`nysdec_`, `neiso_`), which `federal_ces_*` does not; `shared_gap_ratchet`
inspects a shared field only when a designated **backcast keeper's** committed
`run_config.json` carries it at a non-default value, and a forecast-only field defaulting to
`None` — refused in backcast mode by `__post_init__` — can never be armed on a keeper. So the
hole is not the spelling of these two fields: **any shared (no ISO stem), forecast-only or
keeper-unarmed `ScenarioConfig` field that reaches `main` without its row is invisible to
every subsequent run of the checker**, on `main` and on every later PR, whose `--base` diff no
longer contains the field (REPRO B below). The same hole would swallow a `carbon_*`,
`storage_*`, `ccs_*` or `entry_*` field added in a PR that merges before its guard reports.

### 1.2 Reproduction — deterministic, at HEAD `af6269cf`

| run | command | field-leg result | exit |
|---|---|---|---|
| **validate-only** (the desk's three readings) | `PYTHONPATH=. python3 scripts/check_mechanism_matrix.py` | **not run** — `return 0` precedes the diff block | **0** (244 anchor `::warning`s) |
| **REPRO A** — the diff CI saw (PR base) | `… --base 6258185e1f704b84eb442adffcf97b710d7773ec` | `::error … new ScenarioConfig field federal_ces_acp_usd_per_mwh …` and `… federal_ces_target_by_year …` | **1** (2 field errors + 244 anchor errors) |
| **REPRO B** — any base at/after the merge | `… --base 089eb4016801dd2532d9f658f210d4a5b54565a4` | **silent** — the fields are in both base and head | 1 (244 anchor errors only, 0 field errors) |
| **REPRO C** — REPRO A with WS-2a's seven matrix files (`origin/claude/scn-ws2a-federal-ces-qm512t`) checked out over HEAD, then restored | `… --base 6258185e…` | **silent — both fields registered** (`grep -c federal_ces_target_by_year\|federal_ces_acp` = 0) | 1 (244 anchor errors only) |
| **CI, PR #4870** | job `101393800190`, `--base 6258185e…` at head `089eb401` | the same two `::error` lines | **1**, reported 23:29:09Z to a PR merged 23:28:49Z |

REPRO B/C's 244 anchor errors are a blame artifact of the old base, not a finding: an anchor
stale at the base only warns, and capx D65's `--fix-anchors` refresh (`ea273339`) rewrote the
anchor *keys* after those bases, so every current stale key reads as "new" against them. On a
PR based on current `main` the same 244 are warnings, which is what matters for §2.2.

A contributing factor worth naming, without editorial: the same job carried **100+**
`mechanism-matrix anchor` errors blamed on the PR — its 132 inserted lines in `scenarios.py`
shifted every row anchor beneath them (by 13 and 47 lines), which the checker's blame rule
attributes to the PR by design — so the two registration errors were the last two lines of a
job that was red for anchors anyway. A guard whose red usually means "you moved line numbers"
is easy to merge through.

### 1.3 Does minting the row make the checker green for the right reason?

**For the PR-time leg: yes.** The `\b<field>\b` mention check is the intended registration
predicate, WS-2a's row names both fields in its `def`
(`federal_ces_target_by_year :3194 … federal_ces_acp_usd_per_mwh :3220`), and REPRO C shows the
two errors disappear on exactly that change and nothing else. On PR #4902 (base = current
`main`, no `scenarios.py` change, the 244 anchors pre-existing) the guard should read green,
and it would be green for the right reason.

**For the validate-only mode: it was never red, so a green there is no evidence at all.**
Minting the row **pays the debt; it does not repair the gate**. After #4902 merges the checker
is exactly as blind to the next such field as it was to these two: the gate still governs
nothing at merge time, and post-merge there is still no leg that sees a keeper-unarmed shared
field. The symptom is removed; the mechanism in §1.1 stands untouched.

### 1.4 The repair, named and routed — to the capx/audit track (owner of `scripts/` and the CI surface)

This lane did not edit `scripts/check_mechanism_matrix.py` or `.github/workflows/ci.yml`. In
order of leverage:

1. **R1 — make "Rule-28 mechanism-matrix guard" a required status check on `main`** (a repo
   settings act, owner-only). Without it every leg of the checker is advisory in effect,
   whatever it prints; PR #4870 merged with the guard red and six other checks red. This alone
   closes the *merge-time* half of §1.1 for every job, not just this one.
2. **R2 — a diff-free, shrink-only ratchet over EVERY `ScenarioConfig` field**, not just
   ISO-stemmed or keeper-armed ones, run in validate-only mode too (i.e. before the
   `if not args.base: return 0`). Mechanically: extend `mechanism_matrix_gap_sweep.py
   --write-baseline` to write an `absent_shared` block (today's list of shared fields with no
   matrix mention — the `_scenarioconfig_defaults` parser already yields the field set), and
   have `check_mechanism_matrix.py` fail on any field absent from BOTH the matrix text and
   that block, exactly as `gap_ratchet` does for `<iso>_*` fields. Then a field that slips
   through at merge is red on `main` and on every subsequent PR until its row lands, and the
   baseline can only shrink. This closes the *post-merge* half.
3. **R3 — make validate-only mode say what it did not check.** One printed line
   ("diff gate NOT RUN — pass `--base <sha>` to check new-field registration") would have
   stopped three desk readings from being recorded as "CI exited 0".
4. **R4 (design call, not prescribed) — the anchor-blame noise.** A PR that inserts lines
   mid-`scenarios.py` inherits ~100 anchor errors it must `--fix-anchors` away; consider
   auto-repairing PR-caused digit drift in the job (or downgrading it to a warning with the
   fix command) so the guard's red means registration.

The desk ledger §4 already records `scripts/check_mechanism_matrix.py` as **NOBODY on the SCN
track**; this section is the handoff that row anticipated.

---

## 2. The CES row — disposition (item 2)

### 2.1 State at start, checked rather than assumed

- **On `main` (`af6269cf`, re-checked at `bd0fbefd`):** the `federal_ces` premium-ladder row
  exists (`def: "federal_ces_enabled :3110 …"`); **no** `federal_ces_target` row and **no**
  mention of `federal_ces_target_by_year` or `federal_ces_acp_usd_per_mwh` in the base file,
  any shard, or `mechanism-matrix-gaps.json`. `d57cf785` is **not** an ancestor of `main`.
- **On `origin/claude/scn-ws2a-federal-ces-qm512t` (head `ccdbc4a7`, open PR #4902, opened
  2026-09-06 00:22:12Z, base `546279a5`):** three commits ahead of `main` —
  `c5f9358a` (the NEISO 2026 T0 pair registered, `FINDING-scn-ws2a-2026-09-05.md`, the
  scorecard), `d57cf785` (**the `federal_ces_target` base row + one `federal_ces_target:` cell
  line in each of the six shards**, `cell: "."` everywhere, `fc: "U"` in five shards and
  `fc: "O"` with the measured ev in NEISO), `ccdbc4a7` (merge of `main`). 22 files, including
  the two probe bundles under `results/scenario-probes/scn-ws2a/` and the two hindcast
  sidecars.

### 2.2 Verdict: WS-2a is in flight **with its row** — leave it alone

The charter's three branches: landed-with-row → do nothing; landed-probe-without-row → mint;
in flight → leave alone and record. The state is the third with a twist that makes the case
stronger, not weaker: the row is not merely owed, it is **already minted by the lane that
earned the evidence**, in the PR carrying the evidence, as its last commit after rebase, one
appended line per shard — exactly the protocol §4 item 2 prescribes. Minting a second row here
would collide with `d57cf785` on seven files and produce the twin the D60-R2 precedent exists
to prevent. REPRO C (§1.2) verifies that WS-2a's files, and nothing else, clear the field leg.

**Recorded as owed by:** SCN-WS2a, via PR #4902. **What re-arms this lane's conditional:** PR
#4902 closed unmerged, or merged without `d57cf785` — neither is the case at `bd0fbefd`. The
desk should re-check at r#5; if #4902 has merged, the CES-target column's "matrix duty" reads
stamped and nothing further is owed.

`docs/mechanism-testing-matrix.md` was consequently **not edited** (its item-2 edit was
conditional on the mint).

---

## 3. The cache-epoch ledger entry (item 3)

Written to `src/market_sim/results/cache.py`, module docstring, "Cache-epoch ledger (same-key
invalidations)", inserted **above** the `Epoch 2026-09-05` capx D60 entry (the ledger is
newest-first; D60's flip commit `13f711bc` is 19:04Z and WS-4a's `0fc2cc58` is 23:15Z on the
same day, hence the `b` suffix by the ledger's own same-day convention). Verbatim:

> **Epoch 2026-09-05b — SCN-WS4a populates `DATACENTER_ZONE_SHARE["MISO"]` from MISO's
> published 2026 LTLF regional data-center decomposition (`0fc2cc58`, `config/constants.py`).
> NO KEY MOVES, BY CONSTRUCTION — and the stored `config.yaml` cannot see it either.** The
> table is a `constants.py` siting input, not a `ScenarioConfig` field, so `cache_key()`
> hashes the same bytes before and after the change and `cache_config_disagreements` compares
> two identical configs: this is the pure same-key invalidation class this ledger exists for.
> What moved: `data/datacenter.py::datacenter_zone_shares` served MISO the `load_share`
> default (`_load_share_zone_shares`) before this commit and serves the published override
> after it. The ISO-total block MW is unchanged; its zonal allocation is not (MISO-South falls
> from its 0.271 `load_share` to the published 0.183, the difference landing on the
> North/Central-region zones).
>
> **INVALIDATED — re-solve before quoting:** MISO **forecast-mode** bundles solved before
> `0fc2cc58` (2026-09-05 23:15Z) with `datacenter_load_path != "off"` (the default is `"mid"`
> since FF-1F) are STALE at their unchanged key: zonal load, and with it zonal dispatch, flows
> and prices, change while the ISO total block does not. Committed PRE-EPOCH evidence,
> retained as the record of what the harness did on the `load_share` split and never
> re-quoted as a current number: the `frontend/data/hindcast/` sidecars
> `miso-2026-2030-d45r-remeasure` and `miso-2026-2030-s123-verify` (both `b1964e71`,
> 2026-09-04) and `miso-2026-2030-d60-arm` (`e7412237`, 2026-09-05 20:38Z), each recording
> `datacenter_load_path: "mid"`; the capx track decides when they re-run. **NOT invalidated:**
> every BACKCAST bundle in every ISO — the block is forecast-only, `validate_datacenter_config`
> refuses a non-`"off"` path in backcast mode and `ScenarioConfig.__post_init__` coerces it
> off in backcast/hindcast; every OTHER ISO — ERCOT and PJM already carried published
> overrides and are byte-identical, CAISO, NYISO and NEISO are untouched (and NEISO's block is
> 0 MW regardless); and MISO's system-level energy, which is unchanged. No keeper,
> determination or dashboard row moves.
>
> Recorded 2026-09-06 by SCN-MX-R-r2 on the scenario desk's explicit grant of this one entry,
> not by the lane that made the change: `results/cache.py` was outside SCN-WS4a's file region
> and the lane routed the entry rather than write it (`FINDING-scn-ws4a-2026-09-05.md` §6,
> whose scope paragraph the INVALIDATED / NOT-invalidated block above reproduces; desk ledger
> `scenario-desk-ledger-2026-09.md` §4). Derivation of the shares: that FINDING §2. This entry
> changes no key and no default.

What this lane added beyond WS-4a's ready-to-paste paragraph, each verified in the tree: the
commit and its time (`0fc2cc58`, 2026-09-05 23:15:35Z; `constants.py` + `test_datacenter.py`
only), the pre/post allocation path (`datacenter_zone_shares` → `_load_share_zone_shares`
fallback vs the override), the one number the change moves that a reader can check
(MISO-South 0.271 → 0.183, from the commit's own comment), and the three committed MISO
2026–2030 sidecars carrying `datacenter_load_path: "mid"` whose commit dates precede the
change (`miso-2023-2027-crossover-ffr2a` records no DC path and is not listed). `py_compile`
passes; the runtime import was not exercised here (no `numpy` in this code-profile session),
and the edit is docstring-only.

---

## 4. The two checker readings, verbatim

**BEFORE** (HEAD `af6269cf`, working tree clean, `PYTHONPATH=. python3 scripts/check_mechanism_matrix.py`):

```
mechanism-matrix: integrity OK (docs/codebase-site/data/mechanism-matrix.js + 6 ISO shards)
mechanism-matrix: anchors checked (195 field + 49 row + 164 path; skipped 39 non-field token(s) and 4 unresolvable path(s)) — 244 unresolvable beyond the ratchet
mechanism-matrix: keeper stamps match every keepers/<ISO>.json
mechanism-matrix: §5.x prose headers match every keepers/<ISO>.json
[244 lines of `::warning file=docs/codebase-site/data/mechanism-matrix.js::mechanism-matrix anchor: … does not resolve … Run --fix-anchors`]
EXIT=0
```

**AFTER** (same HEAD, with the cache.py entry and the ledger row-5 correction on disk; the
matrix tree untouched):

```
mechanism-matrix: integrity OK (docs/codebase-site/data/mechanism-matrix.js + 6 ISO shards)
mechanism-matrix: anchors checked (195 field + 49 row + 164 path; skipped 39 non-field token(s) and 4 unresolvable path(s)) — 244 unresolvable beyond the ratchet
mechanism-matrix: keeper stamps match every keepers/<ISO>.json
mechanism-matrix: §5.x prose headers match every keepers/<ISO>.json
[244 `::warning` anchor lines]
EXIT=0
```

`cmp` of the non-warning lines: identical. The 244 stale anchors are pre-existing on `main`
(the two `federal_ces_enabled :3110` → `:3120`-class shifts included) and belong to
`--fix-anchors` in whichever lane next touches the base file; this lane, which touched no
matrix file, did not run it.

---

## 5. Record corrections (the charter's "check rather than assume")

- **Desk ledger §3 row 5, Carbon cell** — read "NOT stamped — CORRECTED r#2 AGAINST THE LANE'S
  OWN CLAIM … → SCN-MX-R". On disk: `717de664` mints both rows with a cell in every shard, on
  `main`. Rewritten to that fact, with the accurate genealogy (true at `db8b6015`; the claim
  ran one PR ahead of the commit; the lane closed it itself). The r#3 §0 log already said this;
  the scorecard row had not caught up — and the r#4 refresh (`89ca4e23`, landed on `main`
  during this session) still carries the same row-5 text, so the correction was re-applied
  against the r#4 copy after rebase.
- **Desk ledger §3 row 5, CES-target cell** — read "… `check_mechanism_matrix.py` **exited 0**
  at the pin → SCN-MX-R, CI gap routed". Rewritten: row not on `main`, minted at `d57cf785` in
  open PR #4902, owed by SCN-WS2a; and the record correction that CI on #4870 **failed** on
  these two fields and the PR merged before any check reported — the "exited 0" readings were
  validate-only runs.
- **Plan §5.1 row 5** already read "stamped (`carbon_price_path` + `policy_bundle` rows minted
  at WS-1a)" at start — correct on disk, **not edited**.
- **Left for the desk, outside the two sections the charter named:** the §0 r#2 refresh
  prose ("**and CI passed**") and its plan mirror (plan ~line 1094, "**and CI exited 0**"),
  and the r#3 line "`check_mechanism_matrix.py` still exits 0". They are dated log entries;
  the accurate statement is §1.1 here. Recommend a one-line r#5 annotation rather than a
  rewrite.
- **Collision note:** PR #4902 also rewrites §3 row 5 (its CES-target cells). Whichever of
  #4902 and this lane's PR merges second takes a one-line conflict on that row; the resolution
  is WS-2a's CES-target text over this lane's, and this lane's Carbon text over the stale one.

---

## 6. Duties, deliverables, commits

| duty | status |
|---|---|
| Rule 28(b)/(c) — matrix tree | **no edit** (item 2 did not fire; §2). No cell moved; no row minted. |
| Cache-epoch ledger entry | `src/market_sim/results/cache.py` (+41 lines, docstring only; 1035 → 1076 lines; ≥300 lines so blob-verified by fetch-back after push per rule 27 `[R-PUSH]`). |
| `scripts/` | **untouched**, including `check_mechanism_matrix.py`. |
| Files outside the granted regions | none touched except the two charter-directed record corrections in `scenario-desk-ledger-2026-09.md` §3 (one line). |
| Solves / PRECOMMIT / defaults / new fields | none. |

Commits on `claude/scn-mxr2-matrix-duty-repair-lk9ndd`: (1) the cache-epoch entry; (2) this
FINDING + the ledger row-5 correction. No conditional matrix commit.

---

## 7. Sources cited by this lane

- `scripts/check_mechanism_matrix.py` at `af6269cf` (read only): `main()` control flow,
  `scenarioconfig_fields`, `gap_ratchet`, `shared_gap_ratchet`, `anchor_ratchet`, the
  `--base` diff block; `.github/workflows/ci.yml` `mechanism-matrix-guard` job (steps:
  sparse checkout, `git fetch --depth=1 origin <base.sha>`, `--base <base.sha>`).
- GitHub: PR #4870 (`089eb401` ← base `6258185e`; created 2026-09-05T23:28:44Z, merged
  23:28:49Z; 11 check runs, 7 failed); job `101393800190` log (tail retrieved twice); PR
  #4902 (open, head `ccdbc4a7`); PR #4903 (merged).
- Commits: `089eb401`, `717de664`, `d57cf785`, `c5f9358a`, `ccdbc4a7`, `0fc2cc58`,
  `13f711bc`, `4b28c93f`, `ea273339`, `db8b6015`, `21deb4a7`, `b1964e71`, `e7412237`.
- `docs/handoffs/FINDING-scn-ws4a-2026-09-05.md` §1, §2, §6; `scenario-desk-ledger-2026-09.md`
  §0 r#3, §3, §4; `forecast-scenario-readiness-plan-2026-09.md` §5.1;
  `src/market_sim/data/datacenter.py` (`datacenter_zone_shares`, `_load_share_zone_shares`,
  `validate_datacenter_config`); `src/market_sim/config/constants.py` `DATACENTER_ZONE_SHARE`
  and the `0fc2cc58` diff; `frontend/data/hindcast/miso-2026-2030-*.json`.
