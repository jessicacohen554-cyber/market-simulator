# FINDING — Stage-0 golden capture: MISO (owner ruling R-Q, third issue) — fidelity oracle PASS, the last stale golden is CURRENT, and the pre-flight now covers seven clean partitions rather than the two the second precedent met

**Session `claude/stage0-capture-miso-ekq5f9`, 2026-09-02.** One keeper re-solve at
HEAD with determinism pinned. Follows the proven recipe
`docs/FINDING-stage0-capture-neiso-ercot-2026-09.md` and the second precedent
`docs/FINDING-stage0-capture-caiso-nyiso-2026-09.md`. **No keeper shard, marker,
matrix shard, registry, freeze file or `program-status.json` edit; no
determination changed; no workflow created; no dashboard registration**
(standing reading, recipe finding §3). The two prior R-Q dispatches for MISO
never launched; this is the first MISO capture actually run.

## 0. Headline

| ISO | Provenance run | Span solved | Fidelity oracle | Golden state |
|---|---|---|---|---|
| **MISO** | `2026-09-01-miso-198-oomlevel` | 2023–2025 | **PASS** — 271 flags identical, 0 drift | **CURRENT** |

**Stage-0 coverage: 5 current / 1 stale → 6 current / 0 stale.** Every
enforced `perfb-stage0` entry — CAISO, ERCOT, ERCOT__carveout-2023, MISO, NEISO,
NYISO, PJM — now reads *"provenance run registered, golden CURRENT"*, and
`scripts/check_golden_manifest.py` reports **0 stale, 0 pruned, exit 0**.
PERF-B's cross-ISO byte-gated merges are no longer blocked on MISO.

**The designation was re-read at the session pin and matches the dispatch.**
`keepers/MISO.json` → `2026-09-01-miso-198-oomlevel` (bundle
`results/calibration/miso198_oom_B`), the same run the dispatch named. MISO is
not under the R-V freeze; its lane advanced during this session (miso-199 /
miso-200 probes landed) but no promotion did, and the shard is unchanged.

## 1. What was captured

`scripts/capture_keeper_goldens.py --iso MISO --stage-tag perfb-stage0`, in
session, in process, the three years sequential (rule 12 `[R-PARALLEL]`),
re-solving the keeper's exact recorded `meta.json` config at HEAD.
Determinism pinned by the tool: `MARKET_SIM_HIGHS_THREADS=1`,
`MARKET_SIM_WARMSTART=1`, `MARKET_SIM_WARMSTART_XYEAR=0`.

The bundle is written to `results/regression-goldens/perfb-stage0/MISO/`
(293 MB, **gitignored**). The committed deliverable is the updated
`manifest.json` plus this finding.

| | MISO |
|---|---|
| Keeper bundle | `results/calibration/miso198_oom_B` |
| Years / hours / passes | 2023–2025 / 8760 / `['P1']` (P0 cold + P1 warm per year, 6 solves) |
| Recorded flags replayed | 262 kwargs → **271** meta keys matched |
| `scenario_config` | **766 matched, 0 drifted** |
| HEAD-only meta keys | 1 — `unit_outage_mixed_gas_routing` (miso-200, `ab496e44`, MISO-scoped, `bool = False`) |
| `keeper_only` meta keys | 1 — `caiso_bidir_intertie` (see below) |
| `dropped_dead_config_keys` | `{}` |
| Defaulted unrecorded params | 12 (the standard eleven + `unit_outage_mixed_gas_routing`) |
| Content-hashed files | 10 (`btm`, `flows`, `storage`, `system`, `dispatch/<yr>_P1` + `_P1_fleet` × 3) |
| Solve times | 2023: 483.0 s cold / 303.6 s warm · 2024: 477.7 / 274.3 · 2025: 492.3 / 280.1 (matrix build ≈ 34–36 s each) |
| Wall clock | ~48 min launch → manifest (06:05 → 06:53 UTC), the last ~5 min content hashing |
| Peak RSS / peak swap | **13.67 GB / 4.12 GB** — see §4 |

**`scenario_config` drift is ZERO**, the same stronger-than-required result
the four earlier captures recorded.

**The one keeper-only key is benign and worth naming precisely.** The keeper's
`meta.json` records `caiso_bidir_intertie: null`; HEAD's golden does not carry
the key at all because the mechanism was **deleted under rule 26
`[R-DELETE]`** (`d1e86893`, *"Delete the dead caiso_bidir_intertie mechanism
and its fitted export cap"*) after the keeper froze, so it is no longer a
`solve_and_persist` parameter and `build_solve_kwargs` cannot pass it. It is a
CAISO field, recorded as unset, ISO-irrelevant to MISO — the same benign class
as the head-only keys the ERCOT and NYISO captures carried. The oracle reports
it, does not fail on it, and correctly so.

**The keeper's armed mechanisms were confirmed live in the capture log**, not
inferred from the flags: `st_gas_mustrun_oom_level ARMED (MISO): 133
out-of-merit level(s)` (the promotion's single delta), the maxgen event-window
derate (1,263 plant-tranches, every year), maxgen tier pricing (the 2023-08-24
step-2 footprint at the $1000 slack floor), the nuclear unit-availability
overlay on measured daily windows, and `miso_south_seam_split`. And the
capture reproduces the keeper's own recorded `resolved_inputs` exactly: the
seam import cap resolves `flag_off` / 8,700 MW in all three years, the CAMPD
MISO outage file hashes to the keeper's recorded `690ae220…` (1,008,000 B), and
`hydro_plant_modes.partition_present` is `false` in both — so the solve's
`no hydro-plant-modes clean partition for MISO` WARNING is faithful, not a gap
(the same reading the CAISO/NYISO lane made).

### Per-entry provenance (manifest schema v2)

| ISO | `provenance.git_sha` | `basis_sha` | `git_dirty` | `source` | `recorded_at` |
|---|---|---|---|---|---|
| MISO | `0a3d22c7` | `0a3d22c79c0b8193dff689a309eb6f44fd043c25` | false | `stamped-at-capture` | 2026-09-02T06:53:27Z |

`0a3d22c7` **was `origin/main` at launch** (the merge of #4592, the CAISO/NYISO
capture), so `git_sha` and `basis_sha` coincide and both are origin-durable.
The golden's own `run_config.json` stamps the same tree, `dirty: false`,
`changed_files: []`. No `af1ccb6`-class unresolvable-provenance defect.

## 2. The schema-v2 invariant and the merge-base hazard — both checked, not assumed

Measured by loading `origin/main`'s manifest and this branch's and comparing
entry by entry (canonical JSON):

* `hash_scheme`, `note`, `schema_version`, `stage_tag` — **SAME**;
* CAISO, ERCOT, ERCOT__carveout-2023, NEISO, NYISO, PJM — **BYTE-SAME**;
* MISO — CHANGED (the only entry the capture rewrote).

The tool wrote *"manifest written … (7 keepers)"*, i.e. it merged into a
working tree that already carried the `ERCOT__carveout-2023` partition entry
and PERF-B's stage tags, exactly as the dispatch required. **Main advanced by
17 commits during the solve** (`0a3d22c7` → `f45fb607`), and the CAISO/NYISO
lane's §3 hazard — a capture silently dropping a sibling's mid-solve manifest
change — was checked explicitly: `git diff 0a3d22c7 origin/main --
results/regression-goldens/perfb-stage0/manifest.json` is **empty**, so there
was nothing to splice. The commit carries a 32-insertion / 39-deletion delta
confined to the MISO entry (the superseded miso-160 entry's `recovery` and
`sidecar_source` blocks leave with it, as they should — this entry is stamped
at capture, not recovered from history).

**What landed on main mid-solve, and why none of it invalidates a golden
taken at `0a3d22c7`.** The 17 commits touch four source files:
`config/scenarios.py` (+`entry_vre_zone_selection`, GATED default-off),
`config/iso_configs.py` (the same flag ARMED in MISO's **forecast** config
under capx D33), `data/campd.py` (a `prefer_unit_level` parameter defaulting
`False`, the nyiso-175b default-off companion), and
`model/capacity_evolution/new_entry.py`. Capacity evolution and new entry gate
on `config.mode == "forecast"` and never run in a backcast replay; the two
default-off parameters are byte-inert off. A stage-0 golden is a
*current-HEAD* baseline, and `0a3d22c7` is on `main`'s first-parent history,
so the entry's provenance resolves durably. Unlike the CAISO capture, no
mid-solve commit repaired a defect in *this* keeper's own flags, so there was
no reason to restart.

## 3. THE SUBSTANTIVE FINDING — MISO's clean-partition surface is wider than the two-ISO precedent, and the audit had to be done against `scripts/`, not just `src/`

The CAISO/NYISO lane established that `data/clean` is empty in every fresh
container and that a keeper's armed mechanisms fail in one of two ways when
their partition is missing — hard-fail, or **silently degrade while still
recording the flag as armed** (its §1). It recommended a documented pre-flight.
This lane ran that pre-flight for MISO, and three things are worth recording.

**(a) MISO has a documented silent degradation that is NOT flag-gated at all.**
`scripts/run_calibration.py:2678` calls
`build_miso_deliverability_groups` **unconditionally for MISO** — the per-zone
seasonal CIL/CEL interface caps from the LOLE Study Report
`capacity-deliverability` partition. When the partition is absent the caller
keeps the static PY2025-26 summer caps (*"never silent-zero"*, but a
structurally different network), and it does so **independently of
`capacity_deliverability_limits`**, which is `false` in the keeper (miso-93
correction 1; `RESULTS-neiso65-crossiso-reaudit-2026-07.md` §2, amended
2026-07-26). Reading the flag is not sufficient to conclude the partition is
unneeded, and the fidelity oracle cannot see it — the only evidence is the
log line. All three years of this capture carry the healthy tell:

```
MISO 2023: seasonal CIL/CEL interface caps on 5 zone group(s) (per-season hourly vectors from the LOLE deliverability data; static summer fallbacks replaced)
MISO 2024: seasonal CIL/CEL interface caps on 5 zone group(s) ...
MISO 2025: seasonal CIL/CEL interface caps on 5 zone group(s) ...
```

**(b) The regeneration list.** Seven partitions were rebuilt from `data/raw`
before launch — the four the MISO calibration lanes always regenerate (the
miso-93/94 charters' "four clean partitions regenerated first"), plus three the
call-site audit added:

| partition | why | how |
|---|---|---|
| `capacity-deliverability` | (a) above — unconditional, degrades silently | `regenerate_clean.py` |
| `ramp-capability` | MISO 991-row partition (miso-93); hard-fails if armed, `measured_ramp_capability` is off | `regenerate_clean.py` |
| `transfer-interface-limits` | charter hygiene; PJM-only at HEAD | `regenerate_clean.py` |
| `winter-fuel-inventory` | charter hygiene; NEISO-only at HEAD | `regenerate_clean.py` |
| `maxgen-events` | **reachable** — `unit_outage_maxgen_events` + `maxgen_emergency_tier_pricing` are armed. `data/maxgen_events.py:158-162` self-heals by running the curate script *mid-solve* when the partition is missing, then hard-fails if the raw parse yields nothing. Pre-built so the solve never writes into `data/clean` | `regenerate_clean.py` |
| `zonal-shares` (MISO 2023–25) | **reachable** — the six-zone demand split. `eia930/zonal_shares.py:338-349` falls back to the same raw parser (byte-identical), but a parse failure there degrades silently to the static Gold-Book `load_share`. **Not a `regenerate_clean.py` datatype** — it is missing from `DATATYPES`, so it must be built with `scripts/data/curate_zonal_shares.py --iso MISO --year 2023 2024 2025` | direct curate script |
| `demand-profile` | insurance only — MISO 2023–25 takes the raw per-BA extract, so this site is bypassed; if it were not, the fall-through is the corrupted legacy `eia_demand_profiles.parquet` with `strict_demand_profile=False` | `regenerate_clean.py` |

Every other `read_clean` site is ISO-gated away from MISO, forecast-only,
callerless, or sits behind `MARKET_SIM_USE_CLEAN` (default off, never set by
the capture tool) with a `clean_exists` guard and an identical raw fallback.
The keeper's armed unit-outage, reserve and gas-basis mechanisms all read
**raw** (`campd-unit-outages-MISO.csv`, `MISO-AS/asm_rt_cleared_mw_<yr>`,
`miso_zonal_gas_hub.csv`), not clean.

**(c) A `src/`-only audit misses the two live callers that matter.** A
thorough call-site audit of `src/market_sim/` concluded that
`build_miso_deliverability_groups` had *no live caller* and that the ERCOT GTC
hourly loader was likewise callerless. Both live callers are in
`scripts/run_calibration.py` (`:2678` and `:2476-2486` respectively). The
audit was corrected by grepping `scripts/` before launch; it is recorded here
because the same mistake would let a future lane skip exactly the partition
whose absence is invisible to the oracle.

## 4. Operational record (honest, including what paged)

* **The container had no Python dependencies**, as both precedents found.
  Resolved the same way: a venv at `/home/user/.venv-msim` from the
  fully-pinned `requirements.txt` (numpy 2.4.6, pandas 3.0.3, scipy 1.17.1,
  pyarrow 24.0.0, highspy 1.14.0, pydantic 2.13.4 — matching the keeper's own
  recorded `environment` stamp exactly). `highspy` exposes no `__version__`,
  so the entry records `"highspy_version": "unknown"`, consistent with every
  pre-existing entry.
* **Data hydration was a no-op:** this is a **full clone** (5.8 GB `data/raw`
  local), so `hydrate_data.py --profile miso` reported every blob already
  present. **No converted-corpus re-fetch was required**; no corpus loader
  hard-failed. The seven items in §3(b) were *derived* partitions.
* **Memory — this capture PAGED, unlike the four before it.** A 10 GiB
  swapfile was enabled before launch. Sampled every 30 s on the Python process:
  peak RSS **13.67 GB** (the highest of the program's six captures, above
  ERCOT's 12.50 GB), and system swap-in-use peaked at **4.12 GB**; only 5 of
  the 86 samples read zero swap. The solve completed with no `MemoryError` or
  OOM kill, and the per-year solve times (478–492 s cold) are in line with the
  superseded miso-160 golden's recorded 537–643 s totals, so paging cost time
  but not correctness (HiGHS at one thread is deterministic regardless). This
  matches the MISO lanes' own record — miso-96/98 measured a 14.3 GB
  single-year peak on a 15 GB box and moved to one-process-per-year — and is
  the reason the dispatch's "assume ERCOT-class" was the right floor, not the
  ceiling. **Any lane capturing MISO without swap on a 15 GB container should
  expect an OOM kill.** Disk fell to ~8.8 GB free (swapfile + the 293 MB
  golden, retained).
* **Log audit.** 310 lines; no ERROR, no Traceback, no `baked_fallback`, no
  `static summer` fallback, no missing-partition line other than the faithful
  hydro-plant-modes WARNING (2×). The remaining 71 WARNINGs are all
  keeper-intrinsic fleet-build reconciliations: the eGRID heat-rate
  reconciliation at plant 55641 (co-located 64020 double-count, → 6.880), and
  the `cc_capacity_reconcile` clamp on seven MISO CC plants with corrupt
  summer-capacity rows (1403, 55218, 55220, 55380, 55418, 55467, 55620; 10×
  each across the fleet builds), the armed mechanism doing its job, present in
  the keeper solve too.
* **One log observation recorded without interpretation:** the nuclear
  unit-availability overlay logs *"0 reactor(s) on measured daily windows"* at
  its first 2023 invocation (line 32) and *"13 reactor(s)"* at the second
  (line 67), before the P0 solve. The keeper bundle carries no solve log to
  compare against; the mechanism is the keeper's own, its flag replayed
  identically, and nothing in the two-invocation pattern is capture-specific.
  Noted so the MISO lane can say whether it is expected.
* **A monitoring artifact, disclosed so no one quotes it.** As in both
  precedents, background-task and monitor notifications arrived on their own
  schedule — including a monitor timeout mid-2025 and a "completed" waiter
  event after the manifest write. Every timing, count, hash and status in this
  finding is read from the capture log
  (`scratchpad/capture_miso.log`), the memory sampler, and the committed
  manifest, never from those notifications.

## 5. Holdout compliance (rule 22 `[R-HOLDOUT]`)

The capture solved **only** the years recorded in the keeper's own
`meta.json` — **2023, 2024, 2025**, entirely in-sample. No 2022 touchpoint, no
2019/H1-2026 locked-test year, no `--holdout-authorized`. MISO's `complete` /
`final` markers were neither read, written nor relied upon.

`demand-profile` regeneration wrote 42 partitions spanning 2019–2025 for all
six ISOs because the curate script covers its whole raw span; **only MISO
2023–2025 could have been read, and in fact none were** (the raw per-BA
extract is taken first). Data preparation is explicitly unrestricted under
rule 22's own clause — *"what is held out is the SCORE, never the DATA or the
ARCHITECTURE"*. No out-of-training year was solved, scored or registered.

## 6. Deliverables

* `results/regression-goldens/perfb-stage0/manifest.json` — MISO entry
  (commit `ecefdce6`), pushed over `git push` (HTTP/1.1, lowSpeedLimit 1000 /
  lowSpeedTime 20) and **blob-verified** against the remote: local
  `git hash-object` and the fetched remote blob both `4e2ff5a1…`, 752 lines
  (rule 27 `[R-PUSH]`).
* `docs/FINDING-stage0-capture-miso-2026-09.md` — this file.
* Golden bundle under `results/regression-goldens/perfb-stage0/MISO/` —
  gitignored by design, retained on disk in this container.

## 7. Open items handed back

1. **The ERCOT goldens (forward AND carve-out) may have been captured on the
   silently-degraded static-TTC network.** Both ERCOT keepers' `meta.json`
   record `ercot_gtc_limits_measured: true`; the live caller is
   `scripts/run_calibration.py:2476-2486` → `data/gtc.py::load_gtc_hourly`,
   which on a missing `gtc-limits` clean partition logs at **INFO** and returns
   `None` so the caller keeps the static symmetric TTC — the same class of
   silent degradation as CAISO's MIC seam (CAISO/NYISO finding §1) and one the
   neiso-65 §2 table already flags for ERCOT (*"degrades silently to static
   TTC"*). The recipe finding records no `gtc-limits` regeneration and says
   *"no loader hard-failed"*, which is exactly what this failure mode looks
   like. Whether that container had the partition is not knowable from here.
   **Recommended:** the ERCOT lane grep its capture logs for the GTC hourly
   tell (or its absence), and if the partition was missing, re-capture both
   ERCOT entries with `regenerate_clean.py gtc-limits` run first. Deliberately
   not acted on in this lane (rule 12 concurrency, and it is another ISO's
   golden).
2. **The silent-degradation class remains un-gated, and MISO adds a
   flag-independent member.** The CAISO/NYISO finding proposed asserting the
   replay's `resolved_inputs` against the keeper's; MISO's CIL/CEL groups are
   not in `resolved_inputs` at all, so that fix would not cover them. A
   `resolved_inputs` row for the deliverability-group source (`partition` vs
   `static_summer_fallback`) would make the oracle able to see it.
3. **`zonal-shares` is absent from `regenerate_clean.DATATYPES`** while being on
   the demand path of every multi-zone ISO; a documented pre-flight (open item
   4 of the CAISO/NYISO finding) should either register it or name the direct
   curate command.
4. **MISO cannot be captured on a 15 GB container without swap** (§4). The
   program's memory floor for a stage-1 "after" capture of MISO is the 13.7 GB
   measured here, not the 12.5 GB ERCOT figure.
5. **Stage-0 is now fully current.** PERF-B's byte-gated cross-ISO merges have
   their MISO "before" set; the next PERF-B MISO gate re-solve counts against
   rule 12's two-concurrent-lane cap.
