# FINDING — Stage-0 golden capture: CAISO + NYISO (owner ruling R-Q, re-issued under R-S) — both fidelity oracles PASS, and BOTH captures were blocked first by the same missing-derived-data condition, which the two ISOs fail in **opposite** ways

**Session `claude/stage0-capture-caiso-nyiso-vicx26`, 2026-09-02.** Two keeper
re-solves at HEAD with determinism pinned, run strictly sequentially with the
first committed and pushed before the second began. Follows the proven recipe
`docs/FINDING-stage0-capture-neiso-ercot-2026-09.md`. **No keeper shard,
marker, matrix shard, registry, freeze file or `program-status.json` edit; no
determination changed; no workflow created; no dashboard registration**
(standing reading, §3 of the recipe finding).

## 0. Headline

| ISO | Provenance run | Span solved | Fidelity oracle | Golden state |
|---|---|---|---|---|
| **CAISO** | `2026-09-01-caiso-231-b1-ungrounded` | 2023–2025 | **PASS** — 272 flags identical, 0 drift | **CURRENT** |
| **NYISO** | `2026-08-30-nyiso-159-loss-surface` | 2023–2025 | **PASS** — 271 flags identical, 0 drift | **CURRENT** |

**Stage-0 coverage: 3 current / 3 stale → 5 current / 1 stale.** Current =
{ERCOT-forward, ERCOT-carveout, NEISO, PJM, CAISO, NYISO}; stale = **{MISO}
alone**. `scripts/check_golden_manifest.py` exits **0**; both new entries read
*"provenance run registered, golden CURRENT"*.

**Both designations were re-read at the session pin and both match the
dispatch.** NYISO's was the one the dispatch flagged for verification
("five sessions this window without promoting"): `nyiso-174` (East River class
crosswalk) and `nyiso-175` (CT-deficit probe) both landed *during* this
session, but both are probes / pre-registrations, not promotions, and
`keepers/NYISO.json` is unchanged.

## 1. THE SUBSTANTIVE FINDING — one missing partition, two opposite failure modes

`data/clean/` is **derived, disposable and gitignored**. In a fresh container it
is EMPTY — this session's held exactly nothing. Both keepers arm a mechanism
that reads it, and the two mechanisms behave completely differently when it is
absent:

| | CAISO MIC seam | NYISO PAR attribution |
|---|---|---|
| Mechanism | `capacity_deliverability_limits` | `nyiso_seam_par_attribution` |
| Clean datatype | `capacity-deliverability` | `nyiso-interface-flows` |
| Behaviour when absent | **SILENTLY** fell back to the baked 7,500 MW simultaneous-import scalar | **HARD-FAILED**, naming its own remedy |
| Flag as recorded | `True` — *identical to the healthy case* | n/a, the run aborts |
| Would the fidelity oracle catch it? | **NO** | Yes, trivially |
| Cost if unnoticed | a silently wrong golden | ~40 s and an obvious error |

**The CAISO case is the one that matters, and it is why this finding exists.**
The keeper's own `run_config.json` records
`resolved_inputs.seam_import_cap` resolving from `mic_partition`:

| Year | Keeper recorded | Unrepaired replay | After repair |
|---|---|---|---|
| 2023 | 16,055 MW `mic_partition` | 7,500 MW `baked_fallback` | **16,055 MW `mic_partition`** |
| 2024 | 16,452 MW `mic_partition` | 7,500 MW `baked_fallback` | **16,452 MW `mic_partition`** |
| 2025 | 16,148 MW `mic_partition` | 7,500 MW `baked_fallback` | **16,148 MW `mic_partition`** |

That is **more than half the ISO's import headroom removed** while the run
still logged the flag as armed. The fidelity oracle compares *recorded flag
keys*; `capacity_deliverability_limits` reads `True` in both the healthy and
the degraded case, so **the oracle would have PASSED a materially wrong
golden**. It was caught only by cross-checking the keeper's recorded
`resolved_inputs` against what the replay actually resolved — a check the
capture tool does not perform.

The solve itself is not silent about it — it emits a WARNING naming
`source=baked_fallback` (the caiso-190 / FINDING-caiso188 §4 disclosure
channel, working as designed). But a WARNING in a 70-minute log is not a gate,
and nothing downstream consumes it.

Both partitions were rebuilt from `data/raw` before capture
(`curate_capacity_deliverability.py`, `curate_nyiso_interface_flows.py`) and
verified: all three CAISO caps re-resolve to the keeper's exact recorded values
from `mic_partition`, and both NYISO mechanisms were confirmed live in the
capture log — the zonal loss surface, and PAR attribution driving measured caps
materially different from the static incumbents it replaces (Capital_Hudson
p50 import 427 vs 1600, Upstate_West 1597 vs 3000, NYC 1037 vs 1000,
Long_Island 1012 vs 1200 MW).

**This is a rule-14 `[R-ACCURATE]` hazard, not a capture defect**, and it is
recorded here as an owner/infrastructure question, not fixed in this lane:
a mechanism whose measured input is missing should not be able to degrade to a
fitted scalar while still reporting itself armed. `resolved_inputs` already
carries everything a gate would need.

## 2. What was captured

`scripts/capture_keeper_goldens.py --iso <ISO> --stage-tag perfb-stage0`,
sequentially, each re-solving the keeper's exact recorded `meta.json` config at
HEAD. Determinism pinned by the tool: `MARKET_SIM_HIGHS_THREADS=1`,
`MARKET_SIM_WARMSTART=1`, `MARKET_SIM_WARMSTART_XYEAR=0`.

Bundles are written to `results/regression-goldens/perfb-stage0/<ISO>/` and are
**gitignored**. The committed deliverable is the updated `manifest.json` plus
this finding.

| | CAISO | NYISO |
|---|---|---|
| Keeper bundle | `results/calibration/caiso231_b1_ungrounded` | `results/calibration/nyiso159_lossarm_B` |
| Years / hours | 2023–2025 / 8760 | 2023–2025 / 8760 |
| Recorded flags replayed | 263 kwargs → **272** meta keys matched | 262 kwargs → **271** meta keys matched |
| `scenario_config` | **765 matched, 0 drifted** | **759 matched, 0 drifted** |
| HEAD-only meta keys | **0** | 2 (both ISO-irrelevant — see below) |
| `keeper_only` keys | **0** | **0** |
| `dropped_dead_config_keys` | `{}` | `{}` |
| Content-hashed files | 10 | 10 |
| Solves | 6 (P0+P1 × 3 yr), all cold, 628–904 s (~78 min wall clock) | 6 (P0+P1 × 3 yr), all cold, 133–178 s (~15 min wall clock) |
| Peak RSS | **8.04 GB** | **5.79 GB** |

**`scenario_config` drift is ZERO in both** — a stronger result than the gate
requires, since the tool treats drift as informational.

NYISO's 2 HEAD-only meta keys are `caiso_offer_surface_measured_ungrounded` (a
CAISO field) and `unit_outage_mixed_gas_routing` (the MISO gate that landed
mid-session, default off). Both are ISO-irrelevant to NYISO — the same benign
pattern as the ERCOT capture's single head-only key in the recipe lane. CAISO
has zero because its keeper was promoted the day before the capture.

### Per-entry provenance shas (manifest schema v2)

| ISO | `provenance.git_sha` | `basis_sha` | `git_dirty` | `source` | `recorded_at` |
|---|---|---|---|---|---|
| CAISO | `9220243f` | `9220243ff7a3dd6ed37bdee952e93e7109d91614` | false | `stamped-at-capture` | 2026-09-02T04:58:22Z |
| NYISO | `75a55a4c` | `8ffb34db7866c478eefff2f32d925041293976b8` | false | `stamped-at-capture` | 2026-09-02T05:20:28Z |

`9220243f` was `origin/main` when the CAISO capture launched. NYISO's `git_sha`
`75a55a4c` is this branch's CAISO commit (the tree the NYISO capture actually
ran at) and is pushed, hence reachable; its `basis_sha` `8ffb34db` is the
origin-durable anchor. This is exactly the role the tool's docstring assigns
these two fields, and the same shape the recipe lane recorded.

## 3. The schema-v2 invariant — re-proven, plus one merge hazard the recipe lane never met

The two-consecutive-captures invariant holds, measured by diffing the manifest
at each step:

* CAISO capture → **only** the CAISO entry changed; the other six byte-unchanged.
* NYISO capture → **only** the NYISO entry changed; **CAISO byte-unchanged**,
  `ERCOT__carveout-2023` preserved, top-level block untouched.

**A NEW hazard, hit and handled — `write_manifest` merges into the WORKING
TREE's copy, not main's.** `909dbd3e` added the `ERCOT__carveout-2023` sibling
entry to main *while the CAISO capture was solving*. The capture therefore
merged its entry into this session's older 6-entry file and wrote a manifest
that **silently dropped the carve-out** (its own log says `manifest written …
(6 keepers)`). Left alone, the CAISO commit would have deleted a sibling
lane's brand-new entry.

Handled by resetting onto current `origin/main` and splicing **only** the CAISO
entry into main's 7-entry file, then verifying every other entry byte-identical
before committing. The second capture needed no such handling — by then the
working tree already carried main's 7 entries, and the tool wrote `7 keepers`
on its own.

This is worth recording because it is **not** the v1 defect the schema-v2
repair fixed (that was one capture re-stamping another's *provenance*). It is a
plain merge-base staleness: any capture whose solve outlives a manifest change
on main will silently drop it. The mitigation is procedural — re-read main's
manifest before committing a capture — and cheap.

## 4. Operational record (honest, including what was restarted and why)

* **The container had no Python dependencies**, exactly as the recipe lane
  found. Resolved the same way: a venv at `/home/user/.venv-msim` from the
  fully-pinned `requirements.txt` (numpy 2.4.6, pandas 3.0.3, scipy 1.17.1,
  pyarrow 24.0.0, highspy 1.14.0). `highspy` exposes no `__version__`, so both
  entries record `"highspy_version": "unknown"`, consistent with every
  pre-existing entry.
* **Data hydration was a no-op:** this is a **full clone**, so
  `hydrate_data.py --profile caiso` and `--profile nyiso` both reported every
  blob already local. **No converted-corpus re-fetch was required**; no corpus
  loader hard-failed. The two failures in §1 were *derived* `data/clean`
  partitions, not raw corpora.
* **Memory.** An **8 GiB swapfile** was enabled before the first solve as
  headroom. Neither capture ever paged — swap usage stayed at 0 throughout.
  CAISO peaked at 8.04 GB and NYISO at 5.79 GB against 15 GB of RAM, both well
  inside the ERCOT-class 12.5 GB the dispatch told us to assume. Disk held at
  ~11 GB free; the two goldens together are ~218 MB (CAISO 146 MB, NYISO 72 MB)
  and were retained.
* **ONE capture was restarted, deliberately, and the ~25 minutes spent were
  written off.** The first CAISO attempt ran at `07472e7c`. Mid-solve, main
  advanced and `1f184a54` landed: it registers
  `caiso_offer_surface_measured_ungrounded` — **this keeper's own armed flag** —
  in `_CACHE_KEY_OPTIONAL_FIELDS`, a root-cause repair of a red
  `Pinned default cache key` CI job; the field had landed at `aebeb60e`
  (caiso-231) without its entry, moving both pinned cache keys and orphaning
  every on-disk cache. `909dbd3e` in the same batch rewrote both goldens
  scripts (+367 lines) for the config-partition representation. A stage-0
  golden is by definition a *current-HEAD* baseline, so capturing at a
  20-commit-stale, CI-red tree — on a defect in this very keeper's flag —
  would have produced an artifact not worth committing. Killed and relaunched
  at `9220243f`.
* **Main advanced ~44 commits during the two captures; only that one warranted
  a restart, and each batch was checked rather than assumed.** The rest were:
  a CAMPD-loading perf optimization (`27b3a92c`, self-described *"value- and
  dtype-identical by construction"*); `unit_outage_mixed_gas_routing`
  (`ab496e44`, MISO-scoped, `bool = False`); and the capx D31 MISO
  capacity-revenue repair touching `capacity_market.py` /
  `capacity_evolution/*`, which a backcast replay never enters — capacity
  evolution gates on `config.mode == "forecast"` (`runner.py:319`, `:1097`,
  `:1132`). None can move a CAISO or NYISO backcast dispatch.
* **Benign warnings, recorded rather than smoothed over.** Both solves WARNed
  `no hydro-plant-modes clean partition for <ISO>` — which is **faithful**, not
  a gap: both keepers' own `run_config.json` record
  `hydro_plant_modes.partition_present: false`, so an absent partition
  reproduces the keeper exactly. CAISO additionally logged two fleet
  reconciliation WARNs (plants 56041, 55985 — corrupt summer-capacity rows) and
  one eGRID heat-rate reconciliation (plant 55641), all intrinsic to the fleet
  build and present in the keeper solve too.
* **CAMPD outage inputs verified by hash, not assumed:**
  `campd-unit-outages-CAISO.csv` → `cf156483…` (527,829 B) and
  `campd-unit-outages-NYISO.csv` → `587dd6fa…` (450,345 B), both byte-matching
  the `sha256` each keeper's `resolved_inputs` recorded.
* **A monitoring artifact, disclosed so no one quotes it.** As in the recipe
  lane, streamed background-task notifications arrived announcing capture
  "completion" at moments the process was still running — they fire when a
  *waiter* exits, including when this session deliberately killed a capture.
  Every timing, count, hash and status in this finding is read from the capture
  logs and the committed manifest, never from those notifications.

## 5. Holdout compliance (rule 22 `[R-HOLDOUT]`)

Both captures solved **only** the years recorded in the keepers' own
`meta.json` — **2023, 2024, 2025**, entirely in-sample. No 2022 touchpoint, no
2019/H1-2026 locked-test year, no `--holdout-authorized`. Neither ISO's
`complete` or `final` marker was read, written or relied upon.

The `nyiso-interface-flows` regeneration wrote partitions for 2021–2026 because
the curate script covers its whole raw span; **only 2023–2025 were read**, and
data preparation is explicitly unrestricted under rule 22's own clause —
*"what is held out is the SCORE, never the DATA or the ARCHITECTURE"*. No
out-of-training year was solved, scored or registered.

## 6. Deliverables

* `results/regression-goldens/perfb-stage0/manifest.json` — CAISO entry
  (commit `75a55a4c`) and NYISO entry (commit `9613842c`), each blob-verified
  byte-identical against the remote after push (rule 27 `[R-PUSH]`; 756 and 759
  lines).
* `docs/FINDING-stage0-capture-caiso-nyiso-2026-09.md` — this file.
* Golden bundles under `results/regression-goldens/perfb-stage0/{CAISO,NYISO}/`
  — gitignored by design, retained on disk in this container.

## 7. Open items handed back

1. **The silent-degradation hazard of §1** — a measured-input mechanism that
   falls back to a fitted scalar while still recording its flag as armed, and
   which the fidelity oracle cannot see. `resolved_inputs` already carries the
   evidence; wiring it into the oracle (assert the replay's `resolved_inputs`
   matches the keeper's) would close the class, not just this instance. An
   owner/infrastructure question — deliberately not fixed in this lane.
2. **The manifest merge-base hazard of §3** — cheap procedural mitigation now,
   but a capture that outlives a manifest change on main will silently drop it.
3. **MISO is the last stale golden**, and its live keeper has MOVED since the
   recipe finding was written: the gate now names
   `2026-09-01-miso-198-oomlevel`, not the `miso-191-bexit` that finding cites.
   Whoever captures it must re-read the shard rather than trust that citation.
   Its provenance sidecar is pruned.
4. **`data/clean` is empty in every fresh container.** Neither §1 failure is
   CAISO- or NYISO-specific; any lane whose keeper arms a clean-partition
   mechanism will meet one of the two behaviours. A documented pre-flight
   (`regenerate_clean.py` for the ISO's armed datatypes) would save the next
   lane the same two discoveries.
