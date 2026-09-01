# FINDING — Stage-0 golden capture: NEISO + ERCOT (owner ruling R-L, verbatim "Just NEISO and ERCOT") — both fidelity oracles PASS, and the ERCOT carve-out config is answered explicitly: **NOT covered, and not coverable without a schema change**

**Session `claude/stage0-capture-neiso-ercot-elgk62`, 2026-09-01. THE PROGRAM'S
FIRST SOLVE LANE.** Re-issued by the director after the dispatch-vs-launch check
found the original R-L dispatch **never launched** (no branch, no session). Two
keeper re-solves at HEAD with determinism pinned. **No keeper shard, marker,
matrix shard, registry, freeze or `program-status.json` edit; no determination
changed; no workflow created; MISO deliberately not captured** (restart-checklist
item 5 stands — R-L goes against it for this capture only).

## 0. Headline

| ISO / config | Provenance run | Span solved | Fidelity oracle | Golden state |
|---|---|---|---|---|
| **NEISO** | `2026-08-17-neiso-99-joint-p1` | 2023–2025 | **PASS** — 259 flags identical, 0 drift | **CURRENT** |
| **ERCOT forward** | `2026-08-25-234-eastex-identity` | 2023–2025 | **PASS** — 271 flags identical, 0 drift | **CURRENT** |
| **ERCOT 2023 carve-out** | `2026-08-25-236-swcap-clip-k33` | — | not run | **STILL UNCOVERED** |

**Stage-0 coverage: 1 current / 5 stale → 3 current / 3 stale.** Current =
{ERCOT-forward, NEISO, PJM}; stale = {CAISO, MISO, NYISO}.
`scripts/check_golden_manifest.py` exits **0**; both new entries read
*"provenance run registered, golden CURRENT"*.

**The board's "ERCOT needs TWO captures" count is UNCHANGED — full ERCOT
coverage is still 7-not-6.** This lane closed the forward half only.

## 1. What was captured

`scripts/capture_keeper_goldens.py --iso <ISO> --stage-tag perfb-stage0`,
sequentially (never both at once), each re-solving the keeper's exact recorded
`meta.json` config at HEAD. Determinism pinned by the tool:
`MARKET_SIM_HIGHS_THREADS=1`, `MARKET_SIM_WARMSTART=1`,
`MARKET_SIM_WARMSTART_XYEAR=0` — multi-threaded HiGHS is not bit-identical.

Bundles are written to `results/regression-goldens/perfb-stage0/<ISO>/` and are
**gitignored** (`.gitignore:503`, `/results/regression-goldens/*/*/`). The
committed deliverable is the updated **`manifest.json`** (schema v2 — verified
below), plus this finding.

| | NEISO | ERCOT (forward) |
|---|---|---|
| Keeper bundle | `results/calibration/neiso99_joint_B` | `results/calibration/ercot234_eastex_identity` |
| Years / hours | 2023–2025 / 8760 | 2023–2025 / 8760 |
| Recorded flags replayed | 250 kwargs → **259** meta keys matched | 262 kwargs → **271** meta keys matched |
| `scenario_config` | **718 matched, 0 drifted** | **752 matched, 0 drifted** |
| HEAD-only meta keys | 13 (post-freeze `ScenarioConfig` additions) | 1 (`caiso_offer_surface_measured_ungrounded` — a CAISO field, ISO-irrelevant) |
| `keeper_only` keys | **0** | **0** |
| `dropped_dead_config_keys` | `{}` | `{}` |
| Content-hashed files | 10 | 10 |
| Solves | 6 (P0 cold + P1 warm × 3 yr), 28–91 s | 12 (4 × 3 yr), all cold, 260–422 s (~70 min) |
| Peak RSS | **3.94 GB** | **12.50 GB** |

**`scenario_config` drift is ZERO in both.** The tool treats drift as
informational (goldens are current-HEAD baselines, not byte-reproductions), so
zero drift is a stronger result than the gate requires: HEAD's resolved config
for these two keepers is identical to what was frozen.

### Per-entry provenance shas (manifest schema v2)

| ISO | `provenance.git_sha` | `basis_sha` | `git_dirty` | `source` | `recorded_at` |
|---|---|---|---|---|---|
| NEISO | `3c1f9642` | `3c1f9642fde8e218de4ad362a009de291bc5e00d` | false | `stamped-at-capture` | 2026-09-01T03:06:04Z |
| ERCOT | `a64cc7aa` | `3c1f9642fde8e218de4ad362a009de291bc5e00d` | false | `stamped-at-capture` | 2026-09-01T04:26:34Z |

`3c1f9642` **is** `origin/main` at session start. ERCOT's `git_sha` `a64cc7aa`
is this branch's NEISO commit (the tree the ERCOT capture actually ran at) and
is pushed, hence reachable; if it is squashed on merge, `basis_sha`
`3c1f9642…` is the origin-durable anchor that still resolves — which is exactly
the role the tool's docstring assigns it. Neither entry repeats the `af1ccb6`
unresolvable-provenance defect.

### The schema-v2 invariant, exercised for real for the first time

The v1 defect (`docs/FINDING-stage0-provenance-repair-2026-09.md`) was that one
capture silently re-stamped the shared top-level provenance for every earlier
entry. This session ran **two consecutive captures**, so the repair could be
tested rather than asserted. Measured by diffing the manifest against its
parent commit at each step:

* NEISO capture → **only** the NEISO entry changed; CAISO/ERCOT/MISO/NYISO/PJM
  byte-unchanged.
* ERCOT capture → **only** the ERCOT entry changed; **NEISO byte-unchanged**,
  along with the other four.

No top-level provenance field exists to be re-stamped. The repair holds.

*(One cosmetic delta on the first commit: the top-level `note`'s only change was
`--` → `—`, the tool's own text normalizing an ASCII hyphen pair left by the
hand-written repair. Code is the source of truth.)*

## 2. THE ERCOT CARVE-OUT — the explicit answer

**Q: Does this capture cover the carve-out config? — NO. And it is not
reachable additively; capturing it needs a schema change to two scripts, which
this lane did not make.**

ERCOT is a two-config keeper (`keepers/ERCOT.json` → `config_partition`, owner
ruling 2026-08-26, `docs/FINDING-ercot-two-config-keeper-2026-08-26.md`):

* **forward** `2026-08-25-234-eastex-identity`, designated span **{2024, 2025}**;
* **carve-out** `2026-08-25-236-swcap-clip-k33` (bundle `ercot236_k33_clip`),
  designated span **{2023}**, for the ECRS-era regime.

**A nuance that must not be glossed:** the golden **does** solve 2023 — because
the forward keeper's *registered* span is 3-year and the capture replays
`meta.json` verbatim. But 2023's **designated** config is the carve-out. So the
golden is a faithful baseline of *the forward config across its registered
3-year record*, and **not** a baseline of the ISO's designated 2023 behaviour.
The coverage invariant ("every training year covered by exactly one designated
config") is a statement about the keeper, not about this golden.

### Why it is not additive — four blockers, each measured, not assumed

1. **The carve-out is unreachable by the tool.**
   `capture_keeper_goldens.resolve_keeper_bundles()` builds its map from
   `keeper_store.keeper_list()`, which returns exactly the six *designated*
   keepers. Measured: keys `['CAISO','ERCOT','MISO','NEISO','NYISO','PJM']`;
   `ERCOT` → `2026-08-25-234-eastex-identity`; carve-out reachable → **False**.
   The CLI takes `--iso` only; there is no run-id entry point.
2. **The golden directory collides.** `golden_dir = GOLDENS_ROOT / stage_tag /
   iso` — a bare ISO. A second ERCOT config would overwrite the first.
3. **The manifest key collides.** `write_manifest(stage_tag, {iso: entry})` →
   `keepers[iso]`, a bare ISO key. A second ERCOT entry would replace, not add.
4. **The CI gate would misreport it forever.**
   `check_golden_manifest.live_keeper()` resolves an entry key to
   `keepers/<KEY>.json`. Measured: `live_keeper('ERCOT')` →
   `'2026-08-25-234-eastex-identity'`, but `live_keeper('ERCOT-carveout-2023')`
   and `live_keeper('ERCOT:carveout-2023')` → **`None`**. A partition-keyed entry
   would be reported *"golden STALE (live keeper: None)"* on every CI run, in
   perpetuity, while actually being current.

So the change needed is not a manifest representation but a schema extension
across the capture tool's **resolution, directory layout and manifest key**
*plus* the **CI gate's staleness lookup**. The dispatch's condition — *"a purely
ADDITIVE manifest representation … possible"* — is not met, so the fallback
branch applies and **no schema was invented**.

### What is NOT the blocker (worth recording, because it is the cheap part)

The carve-out config is **fully replayable at HEAD**. Its two deltas over the
forward recipe are recorded in its own `meta.json`, inside the
`coal_prb_sigmoid_overrides` channel (which `build_solve_kwargs` maps to
`prb_overrides` and replays verbatim):

* `ercot_offer_swcap_clip: True` — **live `ScenarioConfig` field at HEAD**
  (default off; the forward keeper's `run_config` carries neither delta,
  confirming the shard's no-leak claim);
* `offer_curve_by_group` carrying `phys_peak: 33.0` for `CT_CHP` / `CT_PEAKER` /
  `ST_GAS` — the "k 33.0" of the run's shorthand — **live `ScenarioConfig`
  field at HEAD**.

Neither is rule-26-deleted, so a replay would not be stripped by
`drop_dead_config_keys`. **The obstacle is purely the tool's one-keeper-per-ISO
keying, not config fidelity** — which is the useful half of this answer for
whoever scopes the follow-up.

### Recommendation (for the owner/director — not executed here)

Close the remaining half with an explicit, owner-scoped schema decision: give
the manifest a per-ISO **config-partition** representation (e.g. an entry's
`configs` list, or a nested key with its own `keeper_snapshot`), and teach
`check_golden_manifest.live_keeper()` to resolve a partition entry through
`keepers/<ISO>.json`'s `config_partition.configs[].run_id`. Both touch
program-gate infrastructure, so both belong to a lane chartered for it.

## 3. Dashboard / provenance-run registration (rule 15 `[R-DASHBOARD]`)

**Both captures are in the healthy state, and no new registration was made —
deliberately.** Read precisely, a golden's *"provenance run"* is the **keeper it
was captured against**, and its *"registry presence"* is that keeper's sidecar
existing. This is the board's own vocabulary (§(f) board E-7: *"the WS3 manifest
maps the ERCOT golden to `keeper_id: 2026-08-15-ercot204-rule26-delete`; that
run's registry sidecar was DELETED … under top-15 retention"*), and it is what
`check_golden_manifest.py` prints. After this session:

```
[ERCOT]: 2026-08-25-234-eastex-identity — provenance run registered, golden CURRENT
[NEISO]: 2026-08-17-neiso-99-joint-p1  — provenance run registered, golden CURRENT
[PJM]:   2026-08-15-pjm-162-inputclock — provenance run registered, golden CURRENT
```

identical to the PJM Card-1 precedent. Both entries also carry
`keeper_snapshot` with `sidecar_at_capture: "present"`, so they stay meaningful
after retention eventually prunes those sidecars.

**Why the golden bundles were NOT registered as dashboard runs.** Three reasons,
stated so the director can overrule if a different thing was meant:

1. **No precedent.** The registry contains **zero** golden/stage-0/`perfb` runs
   (measured: 0 of 58 sidecars match), so the cited precedent — the PJM Card-1
   capture — registered none either. *(This checkout is a shallow clone, so the
   Card-1 commit object itself is unreachable and its file list could not be
   re-derived here; the board's own §Card-1 entry records it as a manifest
   update. The registry measurement above stands on its own.)*
2. **It would spend retention on a non-calibration artifact.** Top-15-per-ISO
   would evict a real calibration run to seat a regression baseline.
3. **It is the fix the board explicitly rejected.** E-7's recommendation is
   *"on the manifest side (self-contained provenance), **NOT** exempting golden
   runs from retention"* — and self-contained provenance is exactly what the v2
   `keeper_snapshot` in both new entries provides.

No `dashboard_add_run.py` / `build_manifest.py` invocation was therefore needed;
nothing on the backcast dashboard changed.

## 4. Operational record (honest, including what nearly blocked it)

* **The container had no Python dependencies at all.** `numpy`, `scipy`,
  `pandas`, `pyarrow`, `highspy`, `pydantic` were absent from both system
  interpreters, so the first capture attempt died at
  `ModuleNotFoundError: No module named 'numpy'`. A `pip install -r
  requirements.txt` into system Python failed on a Debian-owned `PyYAML 6.0.1`
  (`Cannot uninstall … RECORD file not found`). Resolved by building a venv at
  `/home/user/.venv-msim` and installing the **fully-pinned** `requirements.txt`
  (numpy 2.4.6, pandas 3.0.3, scipy 1.17.1, pyarrow 24.0.0, highspy 1.14.0).
  All later commands use that interpreter. `highspy` exposes no `__version__`,
  so the manifest records `"highspy_version": "unknown"` — consistent with every
  pre-existing entry.
* **Data hydration was a no-op:** this is a **full clone**, so
  `hydrate_data.py --profile neiso` reported every blob already local and no
  widening was needed for ERCOT. **No converted-corpus re-fetch was required**
  (unlike the PJM capture's `pjm-da-virtuals`); no loader hard-failed.
* **Memory.** A **10 GiB swapfile** was enabled before ERCOT as headroom against
  the PJM Card-1 memcg OOM (13.9 GB RSS). ERCOT peaked at **12.50 GB** against
  15 GB of RAM and **never actually paged** — swap usage stayed at 0. NEISO
  peaked at 3.94 GB. This container reports an effectively unbounded cgroup
  `memory.max`, so the binding constraint here was physical RAM, not a 13.3 GiB
  memcg. Disk fell to ~8.9 GB free (the swapfile is the bulk of the draw); the
  two goldens together are ~344 MB (NEISO 57 MB, ERCOT 287 MB) and were kept.
* **A real config warning in the ERCOT keeper, recorded verbatim rather than
  smoothed over:** `ercot_wtx_* channel conflict: explicit kwargs
  {'ercot_wtx_curtailment_driver': False, …} are stomped by prb_overrides
  {'ercot_wtx_curtailment_driver': True} in the LIVE solve (run_year applies
  prb_overrides last); recording the prb values. Pass the driver through ONE
  channel.` This is the **keeper's own** recorded config — the capture did not
  introduce it — and the golden records the `prb` values, i.e. it reproduces the
  keeper's live behaviour, which is what a regression baseline must do. Flagged
  here because a keeper setting one field through two channels is a latent
  rule-24 `[R-REGISTRY]`-adjacent hazard worth an owner look; it is **not** a
  fidelity failure and did not affect the oracle.
* Both solves also WARNed `no hydro-plant-modes clean partition for
  <ISO>` (as PJM's capture did); ERCOT additionally logged
  `capacity-deliverability: no partition for ISO ERCOT (energy-only / no
  locational RA construct)` — expected for an energy-only market.
* **NEISO's golden shape changed vs the entry it replaces**, correctly: the
  superseded `2026-08-14-neiso-93-envelope` golden carried `P2` parquets, this
  one is **P1-only**, matching neiso-99's move off the archived P2 pass onto the
  production P1 basis (audit row O5).
* **A monitoring artifact, disclosed so no one quotes it.** Three streamed
  progress events arrived through the session's log-tail notifications that the
  capture logs do not corroborate, in two distinct ways. `Solve: 163.216s
  (warm)` and `Solve: 342.735s (cold)` appear in **no log file** (`grep` count 0
  in both) and match none of the 12 real ERCOT solve times — and ERCOT ran
  **zero** warm solves, so a "(warm)" ERCOT event could not have been genuine.
  `solving ERCOT 2024` **is** real (log line 89) but was delivered *before* it
  existed in the file — a re-`grep` at that moment returned 0, and the log was
  then still 72 lines, mid-2023. So: two fabricated, one premature. Every
  timing, count and status in this finding is read from the capture logs and the
  committed manifest, never from those notifications.

## 5. Holdout compliance (rule 22 `[R-HOLDOUT]`)

Both captures solved **only** the years recorded in the keepers' own
`meta.json` — **2023, 2024, 2025**, entirely in-sample. No 2022 touchpoint, no
2019/H1-2026 locked-test year, no `--holdout-authorized`. NEISO's 2022 bench
rows come from a separate touchpoint run and were not read or re-solved here.

## 6. Deliverables

* `results/regression-goldens/perfb-stage0/manifest.json` — NEISO entry
  (commit `a64cc7aa`) and ERCOT entry (commit `637e51ce`), each blob-verified
  byte-identical against the remote after push (rule 27 `[R-PUSH]`; 670 and 676
  lines).
* `docs/FINDING-stage0-capture-neiso-ercot-2026-09.md` — this file.
* Golden bundles under `results/regression-goldens/perfb-stage0/{NEISO,ERCOT}/`
  — gitignored by design, retained on disk in this container.

## 7. Open items handed back

1. **The ERCOT 2023 carve-out golden** — uncovered; needs the §2 schema decision.
   Full ERCOT coverage stays **2 captures**; the board's 7-not-6 stands.
2. **CAISO, MISO, NYISO goldens remain stale** against their live keepers
   (`caiso-220-c1-crosswalk`, `miso-191-bexit`, `nyiso-159-loss-surface`), and
   all three have **pruned** provenance sidecars. MISO was deliberately not
   captured here (R-L); restart-checklist item 5 still recommends it next.
3. **The `ercot_wtx_*` two-channel conflict** in the ERCOT keeper's recorded
   config (§4) — an owner/calibration-lane question, not a capture question.
