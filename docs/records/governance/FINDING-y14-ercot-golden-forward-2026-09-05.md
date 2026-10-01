# FINDING — Y-14: the ERCOT stage-0 golden captures the FORWARD 2024–2025 config; the `ERCOT__carveout-2023` capture key is RETIRED (owner ruling R-AW)

**Session `claude/y14-ercot-golden-forward-5rjxrn`, 2026-09-05 (Model Audit &
Release-Finalization Program, dispatch Y-14).** Pin: `2886235c` (= `origin/main`
at session start; the director's pin `5cc1e7ce` is its ancestor and the three
intervening commits touch only `docs/handoffs/wallclock-desk-log-2026-09.md`).
The dispatch named the branch `claude/y14-ercot-golden-forward-r4vx8n`; the
session's assigned branch is `claude/y14-ercot-golden-forward-5rjxrn` and the
work is pushed there.

**No keeper shard, marker, freeze file, matrix shard, bench part,
`program-status.json`, status page, `results/calibration/` file, workflow,
`ci_refactor_guards.py` or `CLAUDE.md` was edited. No solve ran. No golden was
re-captured.** Four files changed: the two scripts, one test file, and the
`perfb-stage0` manifest (one added block, every other byte identical). Plus this
finding and a CHANGELOG entry.

## 0. Headline

| | Before (Y-11, PR #4846) | After |
|---|---|---|
| Bare `ERCOT` capture key resolves to | shard `keeper`, replayed on the run's whole registered span | the **`forward`** role: the composed run's registered bundle sliced to **[2024, 2025]**; `registered_years` [2023, 2024, 2025] kept beside it |
| `ERCOT__carveout-2023` capture key | live partition key; `resolve_capture_targets` reached the composed run on **[2023, 2024, 2025]** (the Y-11 STOP) | **RETIRED** — refused by the capture tool; its six manifest records stay as written and the gate reports them as historical, not compared |
| `check_golden_manifest.py` | exit 0; 24 enforced / 15 pruned / **15 stale** | exit 0; 24 enforced / 15 pruned / **9 stale / 6 under a retired key**; every bare-`ERCOT` line byte-identical |
| The two red tests | 2 failed / 43 passed | 0 failed / **57 passed**, 19 subtests (the two rewritten, 11 added) |
| `tests/scoring` | — | 4 failed / 1267 passed — all four in `test_ff_readiness_battery.py`, **reproduced identically at clean HEAD**, not this lane's (§8) |
| Fast tier (`-m "not slow and not integration and not fulldata"`) | — | **8114 passed**, 43 skipped, 2 xfailed, exit 0, 6 min 37 s |

## 1. The ruling, verbatim, and the reading taken

> **"The golden config should be the 2024:2025 one not 2023"** — owner,
> audit-program director sitting 2026-09-05 ~23:00Z, card "ERCOT key",
> off-menu answer; minted **R-AW**.

Reading: the ERCOT stage-0 golden captures the **FORWARD** config on its
designated span **{2024, 2025}**, and the `ERCOT__carveout-2023` capture key is
**RETIRED**. Where the shard left that ambiguous, the reading that changes the
least was taken, never a wider one:

- **Retire the capture KEY, not the keeper's designation.** `keepers/ERCOT.json`
  still designates the carve-out config for 2023 (`config_partition.configs[1]`,
  role `carveout-2023`, years [2023]) and the coverage invariant stands. The
  ruling is about the golden — what the regression baseline captures — so the
  retirement is a golden-program fact, recorded as a constant in the gate
  (§6), and the shard is untouched.
- **The `__forward` partition key survives as an alias of the bare key.** Both
  resolve to the same config, bundle and span. Nothing in the ruling asked to
  remove it; making it identical to the bare key is the smallest change that
  keeps every key form the shard derives well-defined.
- **Historical capture records are not rewritten.** A manifest `keeper_id`
  records which run's outputs were actually captured. The five refactor-pair
  manifests (`perfb-s2-{after,before,final}`, `perfb-s3-{after,before}`) keep
  their `ERCOT__carveout-2023` entries byte-for-byte; only the `perfb-stage0`
  entry gains a `retired` block, with its provenance intact.

## 2. Resolution table

Shard facts at `2886235c` (unchanged from the director's `5cc1e7ce` reading):
both roles carry `run_id 2026-09-05-ercot248-two-config-keeper` and `bundle
results/calibration/ercot248_two_config_keeper`; role `forward` → years
[2024, 2025], `source_run_id 2026-08-25-234-eastex-identity`, `source_bundle
results/calibration/ercot234_eastex_identity`; role `carveout-2023` → years
[2023], `source_run_id 2026-08-25-236-swcap-clip-k33`, `source_bundle
results/calibration/ercot236_k33_clip`.

**What exists on disk after the keeper-only prune** (checked, not assumed):
all three bundle directories exist — `ercot248_two_config_keeper` (15 hourly
sidecars, `composite_provenance.json`, `run_config_forward_2024_2025.json`,
`run_config_carveout_2023.json`), `ercot234_eastex_identity` (15 hourly
sidecars, 3-year) and `ercot236_k33_clip` (5 hourly sidecars, 2023 only) — but
**only `2026-09-05-ercot248-two-config-keeper` has a registry sidecar**
(`frontend/data/backcast/registry/`). The two source runs' sidecars are pruned.
The composed bundle's `meta.json` is **identical to `ercot234_eastex_identity`'s
on all 280 keys** (zero differing keys; `composite_provenance.json`: "meta.json
/ run_config.json carry the FORWARD config").

| Capture key | Role | Bundle replayed | Years replayed | `registered_years` | Status |
|---|---|---|---|---|---|
| `ERCOT` (before) | — (bare `keeper`) | `results/calibration/ercot248_two_config_keeper` | [2023, 2024, 2025] | — | would have replayed the carve-out year under the forward config |
| **`ERCOT` (after)** | **`forward`** | `results/calibration/ercot248_two_config_keeper` | **[2024, 2025]** | [2023, 2024, 2025] | the R-AI re-capture target (§7) |
| `ERCOT__forward` (before) | `forward` | `ercot248_two_config_keeper` | [2023, 2024, 2025] | — | |
| **`ERCOT__forward` (after)** | `forward` | `ercot248_two_config_keeper` | **[2024, 2025]** | [2023, 2024, 2025] | identical to the bare key |
| `ERCOT__carveout-2023` (before) | `carveout-2023` | `ercot248_two_config_keeper` | [2023, 2024, 2025] | — | the Y-11 STOP: 3 years under the carve-out key |
| **`ERCOT__carveout-2023` (after)** | — | — | — | — | **RETIRED**: `KeyError` naming R-AW; never captured again |
| `NEISO` / any one-config ISO | none | its keeper's bundle | registered span | not recorded | **unchanged** |

## 3. Which bundle, and why: the composed run's REGISTERED bundle

The dispatch offered two bundles for the bare key — the composed run's
registered bundle or the forward `source_bundle`. **The composed run's
registered bundle, in both scripts**, on three facts:

1. **It is the only ERCOT bundle with a live sidecar.** `_bundle_info` /
   `resolve_keeper_bundles` resolve a run id through its sidecar, and
   `_keeper_snapshot` absorbs the sidecar's identity so the entry survives the
   next prune. A capture keyed to `2026-08-25-234-eastex-identity` would have no
   sidecar to absorb (`sidecar_at_capture: absent`, empty `iso`/`label`/`date`)
   and — because `live_keeper("ERCOT")` is the shard's designation — would read
   **STALE-by-id forever**, which defeats task 2(d).
2. **Its `meta.json` IS the forward config**, verbatim: 280 keys, zero
   differences from `ercot234_eastex_identity/meta.json`. Replaying it on
   [2024, 2025] replays exactly the forward recipe on exactly its designated
   span; nothing of the carve-out (`ercot_offer_swcap_clip`, `k_peak 33`) is in
   that file (`run_config_carveout_2023.json` carries those separately).
3. **Neither script read `source_bundle` before**, so choosing it would have
   been the widening, not the minimum. `source_run_id` / `source_bundle` are
   used only where they belong: the provenance assertion on the retired record
   (§5, test (c)).

The one thing the composed bundle's whole span would have done wrong — replay
2023 under the forward config — is exactly what the slice removes, and the gate
now fails a CURRENT ERCOT golden that does it (§6).

## 4. Which manifests changed, and how

**One manifest changed: `results/regression-goldens/perfb-stage0/manifest.json`.**
Its `keepers["ERCOT__carveout-2023"]` entry gained a `retired` block
(`declared 2026-09-05`, `ruling R-AW`, the ruling verbatim, its source, and the
effect). Verified by round-trip: with that block removed, the file re-serializes
to the committed bytes exactly (`json.dumps(indent=2, sort_keys=True)`, 36,497
bytes both ways). `keeper_id`, `bundle`, `years`, `provenance`, `fidelity`,
`content_hashes`, `keeper_snapshot`, `partition` — untouched.

**Five manifests deliberately NOT changed** (task 2(a)): `perfb-s2-after`,
`perfb-s2-before`, `perfb-s2-final`, `perfb-s3-after`, `perfb-s3-before`. Their
`ERCOT__carveout-2023` entries record captures that actually happened; the gate
reports them as retired records ("entry carries no retired block" is stated in
the note, never failed).

Gate output, before → after, on the same 47 manifests / 88 entries (the
`diff` is exactly six carve-out lines plus the summary; **every bare `ERCOT`
line is byte-identical**, still `STALE (live keeper:
2026-09-05-ercot248-two-config-keeper)`):

```
< …/perfb-stage0/manifest.json [ERCOT__carveout-2023]: 2026-08-25-236-swcap-clip-k33 — provenance run PRUNED from registry, golden STALE (live keeper: 2026-09-05-ercot248-two-config-keeper)
> …/perfb-stage0/manifest.json [ERCOT__carveout-2023]: 2026-08-25-236-swcap-clip-k33 — provenance run PRUNED from registry, capture key RETIRED (R-AW; historical capture record, not compared to the live shard)
  (the five refactor-pair lines read the same, with "; entry carries no retired block")
< golden-manifest: 47 manifest(s), 88 entr(ies) (24 enforced / 64 legacy); of the enforced, 15 with a pruned provenance run, 15 stale vs the live keeper
> golden-manifest: 47 manifest(s), 88 entr(ies) (24 enforced / 64 legacy); of the enforced, 15 with a pruned provenance run, 9 stale vs the live keeper, 6 under a retired capture key (historical, not compared)
golden-manifest: OK        (exit 0, both)
```

## 5. The two tests, before and after

**`GoldenManifestSchemaTest::test_partition_entries_agree_with_the_keeper_shard`**
— before: asserted `live_keeper(key) == entry["keeper_id"]` for every partition
key, red on `ERCOT__carveout-2023` (`2026-09-05-ercot248-two-config-keeper !=
2026-08-25-236-swcap-clip-k33`). After: a LIVE partition key keeps the original
assertion **plus** `designated_years(key) == partition.designated_years`; a
RETIRED key must (a) be in `RETIRED_CAPTURE_KEYS` with an R-AW citation, (b)
carry a `retired` block whose `ruling_verbatim` is the owner's sentence, and
(c) still agree with the shard's **provenance** for that role —
`config_partition.configs[role].source_run_id == keeper_id` and
`source_bundle == bundle`. (c) is the stronger statement for a record that, by
ruling, never moves again: it ties the historical capture to the run the shard
itself names as the 2023 source. Exactly one retired entry is required.

**`PartitionCaptureKeyTest::test_resolve_capture_targets_reaches_the_carveout_bundle`**
— before: asserted the carve-out key resolved to `…236-swcap-clip-k33` on
[2023]; red on both. Replaced by
**`test_retired_key_is_shared_with_the_gate_and_refused`** (the key raises
`KeyError` naming RETIRED / R-AW / "2024:2025"; the capture tool's table equals
the gate's) and
**`test_bare_ercot_resolves_to_the_forward_config_on_its_designated_span`**
(keeper_id = the live keeper = `…ercot248-two-config-keeper`; bundle
`ercot248_two_config_keeper`; role `forward`; years [2024, 2025];
`registered_years` [2023, 2024, 2025]; `years ⊂ registered_years` strictly; the
gate's `designated_years` / `resolve_role` agree; the snapshot replays the same
slice and keeps the sidecar span).

The rule-22 guard the old line held ("the run's own REGISTERED span, never
widened") is kept and strengthened into an **inclusion asserted in three
places**: `slice_to_designated_span` (resolution), `capture_one` (the solve
site), and the gate (`registered_years ⊇ years`, hard). The dispatch's added
assertion — *a designated span is never a superset of the registered span* —
is `test_a_designated_span_is_never_a_superset_of_the_registered_span`: four
widening shapes raise at the unit, and a forward config widened to
[2022, 2024, 2025] raises through `resolve_capture_targets` against the live
registered span, before any solve.

Other changes in the file: the `GoldenManifestSchemaTest` coverage test is
rewritten as `test_the_bare_ercot_entry_is_the_forward_config_on_its_designated_span`
(green before AND after the R-AI re-capture: it reads the live shard and
sidecar, and holds a CURRENT bare entry to [2024, 2025] while leaving today's
STALE 234 capture to rule 22 only); the temp-shard gate tests use a hypothetical
`carveout-x` role so the generic partition mechanics stay tested independently
of the R-AW retirement; new gate tests cover the forward-role bare key (incl.
the `keeper`-field-disagrees case), a partition without a forward role, the
CURRENT-span failure (bare and partition key), STALE entries being exempt,
one-config ISOs being unconstrained, the `registered_years` inclusion, and the
retired-key report with and without a `retired` block. Nothing is xfailed,
skipped or deleted without a replacement.

## 6. The mechanism in the two scripts

`scripts/check_golden_manifest.py` (stdlib-only, unchanged in that respect):

- `FORWARD_ROLE = "forward"`; `RETIRED_CAPTURE_KEYS = {"ERCOT__carveout-2023": "<R-AW citation>"}`.
  **An explicit constant, not a shard field**: the shard is a calibration-lane
  surface this gate only reads (and this lane may not edit), and the ruling is
  about the golden, not the keeper — the shard's 2023 designation is intact.
- `resolve_role(key)`: a bare key of a partitioned ISO → its `forward` role;
  `live_keeper` resolves the bare key through that role's `run_id` (equal to
  `keeper` today; the role the ruling names wins if they ever differ);
  `designated_years(key)` returns the role's span.
- `check_manifest`: (i) `registered_years ⊇ years` or FAIL; (ii) a key in
  `RETIRED_CAPTURE_KEYS` is reported as a historical record and skips the
  CURRENT/STALE comparison — after every v2 invariant has been applied to it;
  (iii) a **CURRENT** entry whose key resolves to a partition config must
  replay exactly that config's designated span, or FAIL (STALE entries are
  history and exempt; one-config ISOs unconstrained). Fires on nothing
  committed today; it is what makes a whole-span re-capture of the bare key
  fail loud.

`scripts/capture_keeper_goldens.py` imports `FORWARD_ROLE` and
`RETIRED_CAPTURE_KEYS` **from the gate** (the gate never imports the
solve-side tool; the reverse direction is free), so the two cannot disagree:

- `resolve_capture_targets`: a retired key → `KeyError` with the citation; a
  bare key of a partitioned ISO → the designated keeper, which must equal the
  forward role's `run_id` (else `KeyError`), with `role`/`partition_config` set
  and the span sliced; every `<ISO>__<role>` key sliced likewise.
- `slice_to_designated_span`: keeps `registered_years`, sets `years`, raises
  `ValueError` unless designated ⊆ registered.
- `capture_one`: replays `info["years"]` (re-asserting ⊆ `meta["years"]`) and
  writes `registered_years` on the entry; `_keeper_snapshot` carries the
  sidecar's span as `registered_years` too. `--list-configs` shows the bare
  key's slice and marks the retired key; `--all --include-partitions` never
  emits a retired key.

## 7. The re-capture command — NOT run here (R-AI)

R-AI holds every stage-0 re-capture until 48 h of keeper stillness. ERCOT's
clock runs from the promoting commit `4b7a515e` (2026-09-05T19:02:03Z) →
**eligible 2026-09-07 19:02Z**, keeper unmoved. This lane changed nothing about
the hold; it made the target well-defined. The re-capture lane runs, on a
checkout carrying this PR, from the repo root with the solve env:

```
python scripts/capture_keeper_goldens.py --iso ERCOT --stage-tag perfb-stage0
```

Expected: `[ERCOT] re-solving keeper 2026-09-05-ercot248-two-config-keeper
years=[2024, 2025]`, fidelity oracle PASS against
`results/calibration/ercot248_two_config_keeper/meta.json`; the written
`perfb-stage0` entry `ERCOT` carries `keeper_id
2026-09-05-ercot248-two-config-keeper`, `years [2024, 2025]`,
`registered_years [2023, 2024, 2025]`, `partition.role "forward"`,
`partition.designated_years [2024, 2025]`, and `check_golden_manifest.py`
reports it `golden CURRENT`. The `ERCOT__carveout-2023` entry is left as it is
(retired record). Do **not** pass `ERCOT__carveout-2023` — it is refused — and
do not widen `--iso`; `--all` is a different, larger capture.

## 8. Verification

- `uv run --frozen pytest tests/scoring/test_golden_manifest_provenance.py -q`: **57 passed**, 19 subtests.
- `uv run --frozen pytest tests/scoring tests/regression/test_script_import_env_hygiene.py -q`: 4 failed / 1267 passed / 3 skipped / 1 xfailed. The four are
  `test_ff_readiness_battery.py::{test_walk_inputs_trivial_single_year,
  test_resolve_report_no_hard_fail_full_horizon,
  test_ercot_confirmed_horizon_is_reported_not_failed,
  test_build_registration_scorecard_no_iso_gate_open}`; **all four fail
  identically in a clean worktree at `2886235c`** (pre-existing, no file of
  this lane's is in their path; they are outside the fast tier).
- Fast tier, `uv run --frozen pytest -n auto -m "not slow and not integration and not fulldata" -q` (`docs/testing.md` §"Fast"): **8114 passed, 43 skipped, 2 xfailed, exit 0**, 6 min 37 s.
- Seven gate scripts, each invoked alone, `$?` read directly:
  `check_mechanism_matrix.py` 0 · `check_forecast_staleness.py` 0 ·
  `check_bench_freshness.py` 0 · `check_gate_a_provenance.py` 0 ·
  `check_golden_manifest.py` 0 · **`audit_keepers.py --check` 1** (S1:
  `frontend/data/backcast/status/NEISO.js` stale vs current verdicts) ·
  **`check_registry_payload_parity.py` 1** (two unmapped bundle dirs,
  `miso220_nonsteamlift_screen2025` and `neiso_headctrl_k99`). **Both reproduce
  identically at clean `2886235c`**; both live in files this dispatch forbids
  (`status/*.js`, `results/calibration/`) and are Y-13's, not fixed here.
- `ruff check .` 0 · `ruff format --check .` 0.
- Rule 27: the three ≥300-line files were edited with the Edit tool only; after
  the push, each was fetched back from the branch and compared to the local
  file by line count and sha256 (recorded in the PR body).

## 9. What this lane did NOT do

No solve; no re-capture; no shard, marker, freeze, matrix, bench, status,
`results/calibration/`, workflow, `ci_refactor_guards.py`, `CLAUDE.md`, board
or plan edit. The R-AE jobs expected red on this head until Y-13 lands
(Structural guards, Rule-22) are Y-13's; this PR's own surfaces — the golden
manifest gate, the fast tier, ruff — are green locally.
