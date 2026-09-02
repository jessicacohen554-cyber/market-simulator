# FINDING — Golden-manifest config-partition schema + the ERCOT 2023 carve-out capture: schema landed, oracle **PASS**, full ERCOT coverage **CLOSED**

**Session `claude/golden-partition-carveout-3j0le7`, 2026-09-02.** Executes owner
ruling R-O (re-issued under R-S) and the recommendation left open by
`docs/FINDING-stage0-capture-neiso-ercot-2026-09.md` §2. **No keeper shard,
marker, freeze file, matrix shard, registry sidecar, `program-status.json` or
dashboard file was edited; no determination changed; no workflow created; no
bare-ISO golden re-captured.**

## 0. Headline

| | Before | After |
|---|---|---|
| Manifest entries (perfb-stage0, enforced) | 6 | **7** |
| Golden state: CURRENT / STALE | 3 / 3 | **4 / 3** |
| ERCOT configs covered | 1 of 2 (forward only) | **2 of 2** |
| `check_golden_manifest.py` exit | 0 | **0** |
| Carve-out fidelity oracle | not run | **PASS** — 271 flags identical, `scenario_config` 753 matched / **0 drifted** |

**The board's "ERCOT needs TWO captures" count is now DISCHARGED.** Full ERCOT
coverage was 7-not-6; both designated configs now carry a current-HEAD golden.

New coverage line:

```
[CAISO]:                2026-08-16-caiso-197-w2-r5        — PRUNED, golden STALE (live: 2026-09-01-caiso-231-b1-ungrounded)
[ERCOT]:                2026-08-25-234-eastex-identity    — registered, golden CURRENT
[ERCOT__carveout-2023]: 2026-08-25-236-swcap-clip-k33     — registered, golden CURRENT     <-- NEW
[MISO]:                 2026-08-16-miso-160-wefor-shape   — PRUNED, golden STALE (live: 2026-09-01-miso-198-oomlevel)
[NEISO]:                2026-08-17-neiso-99-joint-p1      — registered, golden CURRENT
[NYISO]:                2026-08-16-nyiso-140-layup-exclusion — PRUNED, golden STALE (live: 2026-08-30-nyiso-159-loss-surface)
[PJM]:                  2026-08-15-pjm-162-inputclock     — registered, golden CURRENT
golden-manifest: 38 manifest(s), 71 entr(ies) (7 enforced / 64 legacy); of the
enforced, 3 with a pruned provenance run, 3 stale vs the live keeper — OK
```

The gate's enforced-row output before and after this session differs by **exactly
one added line** (`diff` of the two runs: `2a3`). The three STALE rows are
unrelated ISOs whose keepers moved on independently (CAISO/MISO on 2026-09-01,
NYISO on 2026-08-30); nothing in this lane touched them.

## 1. The schema decision

**Chosen: a SIBLING entry in the same `keepers` map, keyed `<ISO>__<role>`,
where `role` is verbatim the ISO shard's `config_partition.configs[].role`.**
`ERCOT__carveout-2023` is the first. The entry is an ordinary schema-v2 entry —
`keeper_id`, `bundle`, `years`, `hours`, `fidelity`, `content_hashes`,
`provenance`, `keeper_snapshot` — plus one new `partition` block. **No schema
version bump**, because nothing about v2's enforced invariants changes.

Why this shape, on four counts:

1. **It is additive by construction.** `write_manifest` already merges by key,
   so a partition entry *lands beside* the bare-ISO entry instead of replacing
   it. Measured, not asserted — §3(a).
2. **Every v2 invariant applies with zero new enforcement code.** Per-entry
   provenance, the `keeper_snapshot` retention absorb, the forbidden
   top-level-sha check, the legacy-v1 ratchet: all of them see a partition entry
   as just another entry. The gate's only partition-aware code is the key split
   in `live_keeper` and one reporting branch.
3. **The key is DERIVED, not invented.** `role` comes from the shard, so a role
   that is renamed or retired resolves to `None` and the golden reads STALE —
   it cannot silently keep reading CURRENT against a config that was un-ruled.
4. **It expresses the distinction the partition exists for.** `partition.designated_years`
   (the shard's span for this config) is recorded *separately* from the entry's
   `years` (the replayed run's REGISTERED span). For the carve-out both are
   `[2023]`; for the forward config they are `[2024, 2025]` and
   `[2023, 2024, 2025]`. Conflating them is precisely the gloss
   `FINDING-stage0-capture-neiso-ercot-2026-09` §2 warns against, and a test
   pins the difference.

**Rejected: a nested `configs` list inside the existing `ERCOT` entry.** It
changes the shape of an entry that already exists — so the forward entry's bytes
move, failing the dispatch's own requirement — and every per-entry invariant
would need a second, parallel implementation for the nested rows. The separator
`__` appears in no ISO name and no `role` value, and is filesystem-safe because
the same key names the golden subdirectory.

Documented in: both module docstrings, the manifest's own top-level `note`, and
this file.

### What changed in the two scripts

| Blocker (finding §2) | Fix |
|---|---|
| 1. Carve-out unreachable — `resolve_keeper_bundles` builds from `keeper_list()` (the six designated keepers), CLI takes `--iso` only | `partition_configs` / `partition_run_id` / `resolve_capture_targets` resolve through `config_partition.configs[].run_id`; `--iso` accepts `<ISO>__<role>`; new `--list-configs` and `--all --include-partitions` |
| 2. Golden dir collides — `GOLDENS_ROOT / stage_tag / iso` | keyed by the capture key: `perfb-stage0/ERCOT__carveout-2023/` |
| 3. Manifest key collides — `write_manifest(tag, {iso: entry})` | keyed by the capture key; the merge is what makes it additive |
| 4. CI gate misreports forever — `live_keeper('ERCOT__…')` → `None` | `live_keeper` splits the key and resolves the partition role; a *retired* role now says so rather than printing `live keeper: None` |

The fidelity oracle is **unchanged and exactly as strict**: the meta comparison
is still a hard gate that fails the capture on any diverged recorded flag.

An undesignated role **fails loud** (`KeyError` listing the roles that exist)
rather than writing a golden the gate would then call STALE in perpetuity — the
failure mode blocker 4 describes, closed from the other end too.

### One pre-existing test relaxed, deliberately and narrowly

`test_provenance_shas_are_distinct_per_capture` asserted all entries carry
distinct `git_sha`. Once one ISO can hold two entries, two configs captured in
the same session legitimately share a sha, so the assertion would have become a
false red. It now keys on `(git_sha, recorded_at)` — which still detects the v1
defect it exists for (a re-stamp overwrote one *shared* block, collapsing the
timestamps too) while admitting a legitimate same-tree pair. This is the only
existing assertion this lane weakened, and it is named here rather than left to
be discovered.

## 2. The capture

`scripts/capture_keeper_goldens.py --iso ERCOT__carveout-2023 --stage-tag perfb-stage0`,
replaying `results/calibration/ercot236_k33_clip/meta.json` verbatim at HEAD.
Determinism pinned by the tool (`MARKET_SIM_HIGHS_THREADS=1`,
`MARKET_SIM_WARMSTART=1`, `MARKET_SIM_WARMSTART_XYEAR=0`).

| | ERCOT 2023 carve-out |
|---|---|
| Provenance run | `2026-08-25-236-swcap-clip-k33` |
| Keeper bundle | `results/calibration/ercot236_k33_clip` |
| Designated span / registered span | `[2023]` / `[2023]` |
| Years / hours solved | 2023 / 8760 |
| Recorded flags replayed | 262 kwargs → **271** meta keys matched |
| `scenario_config` | **753 matched, 0 drifted** |
| HEAD-only meta keys | 1 (`caiso_offer_surface_measured_ungrounded` — a CAISO field, ISO-irrelevant) |
| `keeper_only` keys | **0** |
| `dropped_dead_config_keys` | `{}` (no rule-26 deletion touches this recipe) |
| Content-hashed files | 6 |
| Solves | 4, all cold: 422.4 / 442.8 / 449.8 / 534.6 s (1,849.6 s of solve) |
| Peak RSS (sampled) | **9.73 GB** |
| Golden bundle size | 94 MB, gitignored |

**`scenario_config` drift is ZERO** — a stronger result than the gate requires,
since drift is treated as informational. HEAD's resolved config for this keeper
is identical in value to what was frozen; the 14 `scenario_config_head_only`
keys are fields *added* to `ScenarioConfig` since 2026-08-25 (among them
`st_gas_mustrun_oom_level` and `carbon_price_delta`, which landed on main
earlier today), not changed ones.

### The two carve-out deltas, verified in the REPLAYED config

Read out of the golden's own `run_config.json`, with the forward keeper's shown
for contrast — the shard's "no leak into forward runs" claim, re-measured:

| Field | Carve-out golden | Forward keeper |
|---|---|---|
| `ercot_offer_swcap_clip` | **True** | *absent* (default off) |
| `offer_curve_by_group.CT_CHP.phys_peak` | **33.0** | — |
| `offer_curve_by_group.CT_PEAKER.phys_peak` | **33.0** | 1.0 |
| `offer_curve_by_group.ST_GAS.phys_peak` | **33.0** | — |

Both ride the `coal_prb_sigmoid_overrides` → `prb_overrides` channel and are
live `ScenarioConfig` fields at HEAD, exactly as the §2 "what is NOT the
blocker" note predicted. Config fidelity was never the obstacle; the keying was.

### Per-entry provenance

| Entry | `provenance.git_sha` | `basis_sha` | `git_dirty` | `source` | `recorded_at` |
|---|---|---|---|---|---|
| `ERCOT` (forward, untouched) | `a64cc7aa` | `3c1f9642…` | false | `stamped-at-capture` | 2026-09-01T04:26:34Z |
| `ERCOT__carveout-2023` (new) | `909dbd3e` | `07472e7c…` | **true** | `stamped-at-capture` | 2026-09-02T03:50:41Z |

`909dbd3e` is this branch's schema commit (pushed, hence reachable);
`07472e7c…` is `origin/main` at session start and is the origin-durable anchor.
**`git_dirty: true` is recorded honestly and is explained, not smoothed over:**
at capture time the working tree carried this finding's placeholder file as an
untracked doc. No tracked source file differed from `909dbd3e` — the schema
commit was already made and pushed before the solve started, precisely so the
capture would run at a reachable tree.

## 3. Verification

**(a) The forward entry's bytes are untouched — the additive requirement.**
Every one of the six pre-existing entries was hashed before and after the
capture (canonical `json.dumps(entry, indent=2, sort_keys=True)`):

```
CAISO b77f62b12012eb15   ERCOT ea53f2a763f605d5   MISO 41243ae92d5f3eb0
NEISO bf60a84127d3ee73   NYISO 47f163fddb606b94   PJM  22f77496b3848563
```

identical on both sides. The manifest's `git diff` is **95 insertions, 1
deletion**, and the single deleted line is the top-level `note`, replaced by the
version that documents the partition key form. No entry-level line was removed.

**(b) The gate, before and after.** Exit **0** both times. The enforced-row
diff is one added line (§0). The six bare-ISO rows and the 64-entry legacy-v1
ratchet are unchanged.

**(c) Tests.** `tests/scoring/test_golden_manifest_provenance.py`: **44 passed,
15 subtests passed** (23 pre-existing + **21 new**), up from 23. The new tests
cover the key algebra, both `live_keeper` resolution paths, case handling,
missing/unreadable shards, an ISO with no partition block, the three reporting
branches (CURRENT / superseded / retired role), a partition entry held to every
v2 invariant, a partition entry surviving a pruned sidecar, both configs
reported side by side, the loud failure on an undesignated role,
designated-vs-registered years, and the byte-identity of the bare-ISO entry
across a partition capture.

**(d) Adjacent gates.** `scripts/check_registry_payload_parity.py` — OK, 60
runs / 95 bundle dirs, 0 tolerated (it reads golden manifest entries' `bundle`
fields via `.values()`, so a partition entry widens its carve-out correctly with
no change). `ruff check` and `ruff format --check` clean on all three files.

**(e) Six unrelated pre-existing test failures, reported not owned.**
`tests/scoring/test_forecast_parity.py::test_all_six_keepers_resolve` and five
in `tests/scoring/test_ff_readiness_battery.py` fail on this branch. They
**reproduce identically at the merge-base tree `07472e7c` with this lane's three
files reverted**, neither test file references the goldens tooling, and the
forecast-parity failure names an ERCOT forecast-orchestrator declaration gap
(`ercot_adaptive_event_release`, `ercot_storage_adaptive_expectation`) that has
nothing to do with this change. Recorded so no one attributes them here; they
are handed back in §5.

## 4. Rules

* **Rule 22 `[R-HOLDOUT]`** — the capture solved **2023 only**, the carve-out's
  own registered span as recorded in its `meta.json`, entirely in-sample. No
  widening, no touchpoint year, no locked-test year, no `--holdout-authorized`.
  A test pins `years == [2023]` on the committed entry.
* **Rule 12 `[R-PARALLEL]`** — one solve lane, one invocation, years sequential
  (there is only one). Never more than this lane running concurrently here.
* **Rule 15 `[R-DASHBOARD]`** — **no registration, deliberately**, on the
  standing reading carried from `FINDING-stage0-capture-neiso-ercot-2026-09` §3:
  a golden's "provenance run" is the keeper it was captured against, and
  `2026-08-25-236-swcap-clip-k33` is already registered (its sidecar is present,
  and the entry absorbed a `keeper_snapshot` so the entry survives a later
  prune). The registry contains zero golden/stage-0/`perfb` runs; registering
  one would spend top-15 retention on a regression baseline.
* **Rule 27 `[R-PUSH]`** — exact on-disk bytes pushed; all three ≥300-line files
  blob-verified against the remote after push (line count + sha256): 1,008 /
  403 / 627 lines, all OK. `http.version HTTP/1.1` set before pushing.
* **Rule 26 `[R-MECH-MATRIX]`** — no mechanism proposed, tested or added; no
  `ScenarioConfig` field added. No matrix shard edited, correctly.

Bundle parquets stay gitignored (`.gitignore` `/results/regression-goldens/*/*/`).
Committed deliverables: the manifest, the two scripts, the tests, this finding.

## 5. Operational record and open items

* **The container started with no Python dependencies** (same as the prior
  stage-0 lane) and no data hydration was needed — a full clone, so
  `hydrate_data.py --profile ercot` was a no-op. A venv at `/home/user/.venv-msim`
  on the fully-pinned `requirements.txt` (numpy 2.4.6, pandas 3.0.3, scipy
  1.17.1, pyarrow 24.0.0, highspy 1.14.0). `highspy` exposes no `__version__`,
  so the entry records `"highspy_version": "unknown"` — consistent with every
  other entry. **No converted-corpus hard-fail occurred**; no loader re-fetch
  was required.
* **Memory.** An 8 GiB swapfile was enabled before the solve, per the dispatch.
  Peak sampled RSS **9.73 GB** against 15 GB of RAM; **swap was never touched**
  (usage stayed 0). The 12.5 GB the 3-year forward capture reached was not
  approached — this is a single-year solve.
* **The `ercot_wtx_*` two-channel conflict RECURRED, verbatim**, and is the
  keeper's own recorded config, not something the capture introduced:
  `ercot_wtx_curtailment_driver: explicit kwarg False is stomped by
  prb_overrides True (this channel applies last) — the LP solves with the prb
  value. Pass the driver through ONE channel.` The golden records the `prb`
  values, i.e. it reproduces the keeper's live behaviour, which is what a
  regression baseline must do. It is **not** a fidelity failure and did not
  affect the oracle. It was flagged as an owner-look item by the previous
  stage-0 lane (§7 item 3) and is confirmed here as present on the carve-out
  config too — i.e. it is a property of the shared ERCOT recipe, not of one run.
* Expected warnings, unchanged from the prior ERCOT capture: `no
  hydro-plant-modes clean partition for ERCOT`, `capacity-deliverability: no
  partition for ISO ERCOT (energy-only)`, and `gtc-limits: no clean partition
  for ERCOT 2023`.

**Handed back:**

1. **CAISO, MISO and NYISO goldens remain STALE** against their live keepers
   (`2026-09-01-caiso-231-b1-ungrounded`, `2026-09-01-miso-198-oomlevel`,
   `2026-08-30-nyiso-159-loss-surface`), all three with pruned provenance
   sidecars. Unchanged by this lane and still the next capture work.
2. **The six unrelated pre-existing test failures of §3(e)** — a forecast-parity
   declaration gap and the FF readiness battery. Not this lane's scope; they are
   red on `main`.
3. **The `ercot_wtx_*` two-channel conflict** — an owner/calibration-lane
   question about the ERCOT recipe, now measured on both partition configs.
4. **The 64 legacy-v1 manifests** are untouched and still grandfathered by the
   ratchet; migrating them remains the separate owner-scoped job of
   `FINDING-stage0-provenance-repair-2026-09` §6.
