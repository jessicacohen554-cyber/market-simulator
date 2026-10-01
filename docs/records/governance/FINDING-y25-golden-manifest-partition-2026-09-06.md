# FINDING — Y-25: the golden manifest can represent a config partition (schema v3), and the gate reports coverage per config

**Lane:** Y-25, Model Audit & Release-Finalization Program (the R-O schema lane,
chartered 2026-09-01, launched 2026-09-06). Director pin `5375be8b`.
**Scope:** zero LP. No capture, no solve, no keeper shard / marker / freeze /
matrix shard / `CLAUDE.md` touched.
**Deliverable:** three commits — schema v3, per-config coverage reporting, this
record.

---

## 0. Result in one paragraph

The manifest could already hold two entries for one ISO (the `<ISO>__<role>`
key form, 2026-09-02), so the charter's *"keys `keepers` one entry per ISO"*
premise was already repaired by Y-14 before this lane ran. What was **not**
representable is **which configuration an entry captured**: the ercot-248
consolidation composed both of ERCOT's designated configs onto ONE registered
run, so `keeper_id` is the same string for the forward and the carve-out entry,
and the mapping from role to config lived only in the live keeper shard — a
file that moves. Schema **v3** stamps that mapping into the entry
(`partition.designated_years` → `partition.config_id`). Separately, the gate's
report said `golden CURRENT` for a partitioned ISO's bare entry and nothing at
all about the other config, so a one-config-of-two manifest read as full
coverage; it now prints a per-config coverage line, and ERCOT reads **"forward
CURRENT; carveout-2023 UNCOVERED"**. Both changes are additive: all 100 entries
across the 57 committed manifests still parse, the gate's entry counts are
unmoved, and its output is byte-identical apart from the new coverage lines.

**No capture was taken.** The capture is a solve (rule 12 memory, ~12.5 GB for
ERCOT) and waits on the R-AI clock. §6 carries the exact command the ERCOT desk
will run.

---

## 1. What the charter said, and what was actually left

The charter (restart checklist item 13) states three things. Two had been
overtaken by Y-14's R-AW work on 2026-09-05, and saying so precisely is part of
this record:

| Charter claim | State at `5375be8b` | Verdict |
|---|---|---|
| "`manifest.json` keys `keepers` one entry per ISO, so ERCOT's two-config partition cannot be represented" | The `<ISO>__<role>` sibling-key form landed 2026-09-02; `perfb-stage0` already holds `ERCOT` **and** `ERCOT__carveout-2023` | **Superseded** — one entry per *config*, not per ISO |
| "`live_keeper` … reads 'ERCOT CURRENT' when only the forward config is captured" | **True and unrepaired.** `wc-b-after` printed `[ERCOT]: … golden CURRENT` with no statement about the carve-out | **Fixed here** (§4) |
| "Full ERCOT coverage is 7 captures, not 6, and one of them is not capturable at this schema" | The seventh capture (`ERCOT__carveout-2023`) is **RETIRED by owner ruling R-AW**, not blocked by the schema | **Reframed** (§5) |

The charter also predates the ercot-248 consolidation, which introduced the
defect this lane actually repairs and which no earlier lane could have
anticipated: **a composed keeper's run id stops identifying a config.**

---

## 2. The object: identity, not keys

`frontend/data/backcast/keepers/ERCOT.json` after the 2026-09-05 consolidation:

| role | `run_id` | `source_run_id` | `years` |
|---|---|---|---|
| `forward` | `2026-09-05-ercot248-two-config-keeper` | `2026-08-25-234-eastex-identity` | 2024, 2025 |
| `carveout-2023` | `2026-09-05-ercot248-two-config-keeper` | `2026-08-25-236-swcap-clip-k33` | 2023 |

Both roles designate the same `run_id`. Consequences at schema v2:

1. `live_keeper("ERCOT")` and `live_keeper("ERCOT__carveout-2023")` return the
   **same string**, so run-id equality cannot tell a forward golden from a
   carve-out golden.
2. An entry recorded `role` — a *label into the shard*, not an identity. If the
   shard later re-points `forward` at another config, an already-written entry
   silently starts claiming to be a golden of the new one.

(2) is defect B's shape exactly — an entry whose meaning lives in a file that
moves — and defect B's fix was `keeper_snapshot`: absorb the identity into the
entry. v3 does the same thing for the config.

---

## 3. Schema v3 (commit 1, `8db6fbd7`)

### 3.1 The block

A partition entry's `partition` block gains four keys (the first two are the
year-set → config map):

```json
"partition": {
  "iso": "ERCOT",
  "role": "forward",
  "designated_years": [2024, 2025],
  "config_id": "2026-08-25-234-eastex-identity",
  "config_bundle": "results/calibration/ercot234_eastex_identity",
  "shard_run_id": "2026-09-05-ercot248-two-config-keeper",
  "composed": true,
  "composed_roles": ["carveout-2023", "forward"],
  "label": "FORWARD KEEPER (2024-2025) …",
  "declared": "2026-08-26",
  "ruling_source": "Owner, program-director sitting 2026-08-26 (verbatim) …"
}
```

* **`config_id`** — the run whose *configuration* was replayed:
  `config_partition.configs[].source_run_id`, else `run_id`. This is the
  identity `keeper_id` lost.
* **`shard_run_id`** — what the shard designates, i.e. the run actually
  replayed. Equal to `keeper_id` at capture time; differs from `config_id`
  precisely when roles are composed.
* **`composed` / `composed_roles`** — whether that run carries more than one
  role, and which. A reader of the manifest alone can see why the run id is not
  the identity.

Required keys are `REQUIRED_PARTITION_V3_KEYS = (iso, role, designated_years,
config_id, shard_run_id)`.

### 3.2 Backward compatibility, stated as invariants

| Invariant | How it holds |
|---|---|
| Every v2 entry still parses and is enforced identically | `MIN_SCHEMA_VERSION` **stays 2**; the identity keys are required only of a manifest declaring v3 |
| A partition-keyed entry at v3 must carry the block | new failure: *"schema v3 requires a 'partition' block on a config-partition entry"* |
| Merging a v3 capture into a pre-v3 file must not re-label the older entries | `capture_keeper_goldens.manifest_version(entries)` declares what the **merged entries actually satisfy** — a mixed file stays **v2**. Same defect-A reasoning as per-entry provenance: one capture may not make a claim on behalf of entries it did not write |
| A future schema must not pass unread | new `MAX_SCHEMA_VERSION = 3`; a manifest declaring more **FAILS** |
| The benefit is not gated on the version stamp | the gate reads `config_id` wherever one is present, at any declared version |

### 3.3 The payoff, in the gate's behaviour

`live_state()` now demotes CURRENT → STALE when the run id still matches but
the config has been superseded:

```
[ERCOT]: … golden STALE (run run-composed is still designated, but its
'forward' config is now run-fwd-src; this golden captured run-an-older-config)
```

At v2 that entry read **CURRENT**. This state was unreachable before the
consolidation and unrepresentable after it.

---

## 4. Per-config coverage (commit 2, `f7525282`)

`config_coverage()` adds one line per partitioned ISO present in a manifest.
`UNCOVERED` always names *which* of three situations it is, so a decision is
never read as a gap:

* `no entry in this manifest`;
* `only the RETIRED capture key <key> (R-AW) — a historical capture record, not
  compared to the live shard`;
* `capture key <key> RETIRED (R-AW); no entry`.

It is a **report, never a failure**. The carve-out is uncovered *by ruling*, and
a gate must not demand a capture the owner retired.

The CURRENT/STALE computation was extracted into `live_state(key, entry)` and is
shared by the entry loop and the coverage report, so the two cannot drift into
two answers for one question.

### 4.1 Before / after — the gate's output

Command: `python scripts/check_golden_manifest.py` (CI's exact invocation,
`.github/workflows/ci.yml` job `quarantine-gates`).

**Before** (the two lines the charter names, and the summary):

```
  results/regression-goldens/wc-b-after/manifest.json [ERCOT]: 2026-09-05-ercot248-two-config-keeper — provenance run registered, golden CURRENT
  results/regression-goldens/perfb-stage0/manifest.json [ERCOT]: 2026-08-25-234-eastex-identity — provenance run PRUNED from registry, golden STALE (live keeper: 2026-09-05-ercot248-two-config-keeper)
golden-manifest: 57 manifest(s), 100 entr(ies) (36 enforced / 64 legacy); of the enforced, 15 with a pruned provenance run, 9 stale vs the live keeper, 8 under a retired capture key (historical, not compared)
golden-manifest: OK
```

`wc-b-after` reads as full ERCOT coverage. It is one config of two.

**After** — every line above is byte-identical (including the summary and its
counts); these 12 coverage lines and one summary sentence are **added**:

```
  results/regression-goldens/perfb-campd-ercot-after/manifest.json (ERCOT partition coverage): forward STALE [ERCOT] (live keeper: 2026-09-05-ercot248-two-config-keeper); carveout-2023 UNCOVERED (capture key ERCOT__carveout-2023 RETIRED (R-AW); no entry)
  results/regression-goldens/perfb-campd-ercot-before/manifest.json (ERCOT partition coverage): forward STALE [ERCOT] (live keeper: 2026-09-05-ercot248-two-config-keeper); carveout-2023 UNCOVERED (capture key ERCOT__carveout-2023 RETIRED (R-AW); no entry)
  results/regression-goldens/perfb-s2-after/manifest.json (ERCOT partition coverage): forward STALE [ERCOT] (live keeper: 2026-09-05-ercot248-two-config-keeper); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/perfb-s2-before/manifest.json (ERCOT partition coverage): forward UNCOVERED (no entry in this manifest); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/perfb-s2-final/manifest.json (ERCOT partition coverage): forward UNCOVERED (no entry in this manifest); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/perfb-s3-after/manifest.json (ERCOT partition coverage): forward STALE [ERCOT] (live keeper: 2026-09-05-ercot248-two-config-keeper); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/perfb-s3-before/manifest.json (ERCOT partition coverage): forward STALE [ERCOT] (live keeper: 2026-09-05-ercot248-two-config-keeper); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/perfb-stage0/manifest.json (ERCOT partition coverage): forward STALE [ERCOT] (live keeper: 2026-09-05-ercot248-two-config-keeper); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/wc-a6-after/manifest.json (ERCOT partition coverage): forward UNCOVERED (no entry in this manifest); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/wc-a6-before/manifest.json (ERCOT partition coverage): forward UNCOVERED (no entry in this manifest); carveout-2023 UNCOVERED (only the RETIRED capture key ERCOT__carveout-2023 (R-AW) — a historical capture record, not compared to the live shard)
  results/regression-goldens/wc-b-after/manifest.json (ERCOT partition coverage): forward CURRENT [ERCOT]; carveout-2023 UNCOVERED (capture key ERCOT__carveout-2023 RETIRED (R-AW); no entry)
  results/regression-goldens/wc-b-before/manifest.json (ERCOT partition coverage): forward CURRENT [ERCOT]; carveout-2023 UNCOVERED (capture key ERCOT__carveout-2023 RETIRED (R-AW); no entry)
  partition coverage: 12 partitioned-ISO report(s), 16 designated config(s) UNCOVERED — reported, never failed (the ERCOT carve-out is uncovered BY RULING: R-AW retired its capture key, so the gate must not demand it)
```

**The charter's target line**, verbatim from the run above:

```
results/regression-goldens/wc-b-after/manifest.json (ERCOT partition coverage): forward CURRENT [ERCOT]; carveout-2023 UNCOVERED (…)
```

Diff of the two runs: `37a38,49` and `38a51` — **additions only**. Exit 0 in
both.

---

## 5. "Seven captures, not six" — the honest reading

Six ISOs plus ERCOT's second config is seven, and the charter is right that the
seventh is not represented by any *live* golden. But it is not the schema that
blocks it: **owner ruling R-AW (2026-09-05, card "ERCOT key"), verbatim — *"The
golden config should be the 2024:2025 one not 2023"*** — retired the
`ERCOT__carveout-2023` capture key. `capture_keeper_goldens.py` refuses it and
the gate reports its historical entries without comparing them.

So the correct statement is: **full ERCOT stage-0 coverage is six captures by
ruling, and the seventh is UNCOVERED by decision.** This lane makes that visible
instead of invisible, and nothing here re-authorizes the retired capture. Should
the owner ever un-retire it, the schema and the gate are now ready: remove the
`RETIRED_CAPTURE_KEYS` entry and the key captures, reports and covers like any
other.

---

## 6. The capture command the ERCOT desk will run

**Not run here.** When the R-AI clock releases, the ERCOT stage-0 re-capture is
the FORWARD config on its designated span, under the bare key:

```bash
python scripts/capture_keeper_goldens.py --iso ERCOT --stage-tag perfb-stage0
```

Facts the desk should have before running it:

* **What it captures.** `ERCOT` resolves (R-AW) to the `forward` role:
  run `2026-09-05-ercot248-two-config-keeper`, bundle
  `results/calibration/ercot248_two_config_keeper`, **years [2024, 2025]** —
  sliced from the run's registered [2023, 2024, 2025], which is recorded in the
  entry as `registered_years`. A 3-year replay under this key is a **hard gate
  failure** (R-AW), not a warning.
* **Cost.** One ERCOT per-plant multi-zone LP per year, ~12.5 GB peak (rule 12);
  years sequential within the invocation. Do not launch beside another
  per-plant capture.
* **Schema.** The entry is written with the v3 `partition` block. Because
  `perfb-stage0` also holds the pre-v3 `ERCOT__carveout-2023` historical record,
  `manifest_version()` will keep that file at **`schema_version: 2`** — correct
  and expected, not a regression. A fresh stage tag whose partition entries are
  all v3 declares 3.
* **Verify after.** `python scripts/check_golden_manifest.py` — expect exit 0,
  `[ERCOT]: … golden CURRENT`, and the coverage line reading
  `forward CURRENT [ERCOT]; carveout-2023 UNCOVERED (…RETIRED (R-AW)…)`.
* **Do not** pass `--include-partitions` expecting the carve-out: it is refused
  by `RETIRED_CAPTURE_KEYS` with the ruling in the message.

Dry-run the resolution first, no solve:

```bash
python scripts/capture_keeper_goldens.py --list-configs
```

---

## 7. Verification

| Check | Result |
|---|---|
| `tests/scoring/test_golden_manifest_provenance.py` | **75 passed, 76 subtests passed** (was 65; +10 tests) |
| `scripts/check_golden_manifest.py` over all 57 committed manifests | **exit 0**, entry counts unmoved (100 entries / 36 enforced / 64 legacy / 15 pruned / 9 stale / 8 retired), output additions only |
| `ruff check` + `ruff format --check` on the three touched files | clean |
| Committed manifests parse under the v3 reader | asserted per manifest by `test_every_committed_manifest_passes_and_reports_one_note_per_entry`, which also pins one entry note per entry (coverage adds none) |
| Live-data v3 identity | `test_partition_block_carries_the_v3_config_identity`: `config_id` = `2026-08-25-234-eastex-identity` for forward, distinct from the carve-out's, while `live_keeper` returns one string for both |

New tests follow the repo's trivial-first pattern: single-ISO temp-tree
manifests for the schema and coverage mechanics
(`PartitionStalenessLookupTest`), then the committed manifests byte-for-byte
(`GoldenManifestSchemaTest`).

---

## 8. Files touched

| File | Change |
|---|---|
| `scripts/check_golden_manifest.py` | `MAX_SCHEMA_VERSION`, `PARTITION_IDENTITY_SCHEMA_VERSION`, `REQUIRED_PARTITION_V3_KEYS`, `COVERAGE_MARK`; `shard_config_identity()`, `live_state()` (extracted), `config_coverage()`; v3 entry validation; coverage split out of every tally |
| `scripts/capture_keeper_goldens.py` | `MANIFEST_SCHEMA_VERSION = 3`; `_partition_block()` emits the identity; `manifest_version()` declares what the merged entries satisfy |
| `tests/scoring/test_golden_manifest_provenance.py` | +10 tests (coverage reporting, v3 identity, version bounds, mixed-file honesty, live-corpus sweep) |
| `docs/handoffs/FINDING-y25-golden-manifest-partition-2026-09-06.md` | this record |

Untouched, per the lane's scope: every keeper shard, every marker, the holdout
freeze, every mechanism-matrix shard, `CLAUDE.md`, and every committed manifest
(no manifest bytes were rewritten — the schema is additive and the next capture
writes it).
