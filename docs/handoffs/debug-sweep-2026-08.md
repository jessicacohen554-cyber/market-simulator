# DEBUG-A — debug sweep 2026-08-14 (solve-neutral pass)

**Branch:** `claude/debug-sweep-2026-08-3hzvk8` (off `origin/main` @ 5bf5f13).
**Charter:** `docs/model-audit-release-plan-2026-08.md` §3/WS2 + §7.2.
**Hard rule honored:** every landed fix is solve-neutral (test/tooling/doc
surfaces + one config-serialization repair proven not to move the pinned
default cache key). The one confirmed solve-affecting defect is chartered to
DEBUG-B, not landed.

**Headline.** The fast tier on a clean full checkout of main was 6 failed /
6,830 passed; all six are fixed on this branch (final local re-run: see §Seed 7).
The README's "known-failing" list was stale in both directions — its four
listed failures no longer exist, and none of the six real ones was listed.
The PJM M-1 input-clock defect is **confirmed live in a mutated form** and is
chartered as DEBUG-B with an updated transform (D-5 closed: patch archived,
must not be applied verbatim). `golden-data-tier.yml`'s "never-fired cron" is
simply a cron that has not reached its first Monday.

## Triage table

| # | Finding | Disposition | Evidence | Follow-up |
|---|---|---|---|---|
| 1 | `test_eia_loader` "4 known-failing CAISO/NYISO zonal-share cases" | **ADJUDICATED stale + FIX NOW (docs)**: all 64 tests pass on a clean full checkout at HEAD; the historical reds were cleared by the caiso-175 TAC-series completion and the 2026-07-31 CISO/MISO 2022 wide-extract fill. The residual failure mode (8 reds, CAISO/ERCOT/MISO — none NYISO) exists only on a checkout without `data/raw/zone-specific-demand`, and the fast tier hard-requires `data/raw` by contract (ci.yml header). README note rewritten. | 64/64 pass full-data (2026-08-14); 8 fail with the dir hidden (measured); ci.yml header "6 failures → 780 without data/raw" | none |
| 2 | `test_neiso_bins::test_committed_artifact_is_deterministic` drift | **ADJUDICATED — already fixed on main**: it was a **stale committed CSV** (stale since the D-25 gas_st taxonomy fix, PR #3697), regenerated *under adjudication* by HOUSE-2 on 2026-08-09 (the code change was the intended behavior; the artifact followed it — not a gate-silencing regen). Passes 15/15 at HEAD; committed CSV, builder, and its input path unchanged since the survey snapshot `066abeed`, so the survey's red was a partial-checkout artifact. | `house-2-baseline-wave-2026-08-09.md` §4 row 3; 15/15 pass ×2 (2026-08-14); `git diff 066abeed..HEAD` empty on the CSV + builder | none |
| 3 | `tools/launcher.py:280` stale `run10_peak85` ref | **FIX NOW (landed)**: worse than a stale string — `_run_job` passed the missing bundle to `render_backcast.py` unconditionally (unguarded `meta.json` read), so a UI run would solve and then crash at render. Baseline now resolves keeper shard → registry sidecar → bundle dir (falls to None gracefully); render arg conditional; stale "2025 EIA data is incomplete" year list fixed (2025 is a training year). Launcher path **retained** (owner-visible note: it is README-documented user-facing tooling; retirement would be a BLOAT-lane deletion decision, not a debug fix). | commit `764c486`; resolves to `results/calibration/ercot192_arm_B` on this clone | none |
| 4 | Unfiled top-level test files (9 in census; **10 at HEAD** — `test_miso155_p0_commitment_sidecar.py` landed after) | **FIX NOW (landed)**: all 10 filed per the Wave-5A tiered layout — 1 → `tests/curation/`, 3 → `tests/iso/miso/`, 6 → `tests/iso/nyiso/` (census said "7× nyiso"; 6 exist at HEAD). miso155's `parents[1]` REPO anchor re-pointed at `tests.helpers.REPO_ROOT`. No non-test file referenced the old paths; 99/99 collected tests pass post-move; `ci_refactor_guards --script-refs` green. | commit `67d603f` | none |
| 5 | scripts/ bare sibling-import census ("105 sites / 91 files", 2026-07-27) | **RE-SCOPED with justification**: re-measured at **74 sites / 50 live files** (61 same-directory + 13 cross-directory) — the delta is real conversion progress by intervening lanes. Converting the residue needs, per file: the README's both-paths attribute verification **plus** a direct-run `sys.path` bootstrap check (canonical imports need repo root on the path where bare ones needed only the script's own dir) — too wide to land safely as a sweep side-effect. Made the census re-runnable (`ci_refactor_guards.py --sibling-census`, advisory) and updated the README record. | commit `40a1bb0`; census output in the README section | chartered open work (non-DEBUG-B: solve-neutral conversion lane, per-file protocol in scripts/README.md) |
| 6 | `check_cache_key_declared_defaults` red seen once on cancelled run 31661696810 | **ADJUDICATED — checkout artifact**: on a clean full clone the guard passes ("715 fields, 168 registered, all resolve; 168 declared defaults all match HEAD"), including after this branch's ScenarioConfig change; the one observed red was on a partial-checkout cancelled run. The same job is green on the first completed CI run (31765772123). | local run 2026-08-14; CI run 31765772123 job `Cache-key registration guard` = success | none |
| 7 | Ambient fast-tier reds on clean-clone main | **ENUMERATED + ALL SIX FIXED** (see per-red table below). Full fast lane on main @ 5bf5f13: **6 failed / 6,830 passed / 31 skipped / 2 xfailed** (616 s, `-n 2`), exactly matching ci.yml's header count. | first run + final verification run on this branch | none |
| 8 | `patches/pjm-m1-code.patch` (D-5) | **DEFECT CONFIRMED — CHARTERED to DEBUG-B; patch ARCHIVED** (D-5 closed). See §D-5 below. | probes re-run 2026-08-14 (§D-5); commit `a168b73` | `docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md` |

### Seed 7 detail — the six ambient reds, each root-caused

| Red (fast tier, main @ 5bf5f13) | Root cause | Fix (this branch) |
|---|---|---|
| `test_ercot_thermal_as_endogenous::TestScreenMutualExclusion` ×2 | FF-1A `retirement_rule` default flip to `"pipeline"` — the probe calls the screen without `year` and reads legacy loss counters. Carried since 2026-08-03 as "D-1 fallout, owned by the retirement lane" (ffr-sc §9.5, HOUSE-2 baseline rows 1–2); that lane completed (Wave FH) without picking it up, so the charter had gone stale. | pin `retirement_rule="legacy"` in the probe config — the established sibling pattern (8 sites in `test_capacity.py`); the mutual-exclusion mechanism under test lives in the margin computation shared by both rules (`ae80c38`) |
| `test_cache.py::TestConfigSidecar::test_config_yaml_present_alongside_parquet` | **Real config-serialization bug**: YAML has no tuple, so a `to_yaml_full` sidecar reloads tuple-typed fields as lists; `cache_key()`'s optional-field drop-at-default compares `[…] == (…)` → False, so a byte-faithful reload hashed to a *different key than its writer* | coerce list→tuple for tuple-typed fields in `__post_init__` (all construction paths). Pinned default key `603c2498bf71d21d` proven unmoved: pinned-key + flip-guard tests 22/22, registration guard clean (`01d5748`) |
| `test_ff_readiness_battery::test_config_completeness_all_isos_green`, `…cache_key_stable_round_trip` | same root as above | same fix (`01d5748`) |
| `test_configs_yaml_roundtrip[data-profiles.yaml]` | fails **by design** for an unrouted `configs/*.yaml`; `data-profiles.yaml` (hydration manifest, 2026-08-13) landed without a route | route to its consumer `scripts.hydrate_data.load_manifest` with key assertions (`c4b47bc`) |

Adjacent finding (report-only, no landed change): the four `integration`-marked
tests in `test_ff_readiness_battery.py` fail on a container whose derived
`data/clean/confirmed-retirements` partition is absent — correctly deselected
from the fast tier, but a bare `pytest tests/scoring/test_ff_readiness_battery.py`
on a fresh container reds on environment, not code (the FFR-3A "data/clean
prerequisite" blocker, still true).

### CI health

* **Cancellation mechanism identified:** ci.yml is `pull_request`-triggered
  only (no push trigger, no concurrency group). The wall-to-wall `cancelled`
  record (29 of the 30 preceding runs) is the merge-fast pattern: PRs merge
  and their branches delete before the ~7–15 min run completes, which cancels
  the in-flight run. Nothing is wrong with the workflow itself.
* **First completed run on record:** 31765772123 (2026-08-14, PR #3936 head).
  Conclusion `failure` — job map: 6 green; red = `Fast test tier`,
  `Structural refactor guards` (the `gen_caisoNNN` dangling ref; fixed on
  this branch), `FR-22 parity` + `Forecast-invariant artifact audit` (both
  red **by design** as other lanes' live signals — HOUSE-2 §4; not touched by
  this sweep, per its own charter). This sweep's own PR #3937 produced the
  second and third completed runs (31768130935 / 31768417379): 7 green + the
  same two by-design reds + `Fast test tier`.
* **Fast test tier cannot currently complete in CI at all — checkout-level
  failure, not test failures.** On every completed run inspected (main's
  31765772123 and both of #3937's), the fast-tests job died **inside its
  `actions/checkout` step** after 6–7.5 min with pytest never invoked, while
  the nine data-free-checkout jobs finished checkout in ~20 s on the same
  runs. The tier's full checkout (it hard-requires `data/raw`, ~10 GB at tip)
  no longer survives on GitHub runners. So the tier's CI red is
  INFRASTRUCTURE — the branch's test content is green (6,836/0 locally on the
  identical tree) — and the ci.yml header's "6 failures with data/raw"
  empiricism was measured locally, not in CI. Disposition: **chartered to
  PERF-A** (plan §3/WS3 item 5 owns per-job checkout strategy; ci.yml's own
  header forbids the naive sparse "fix" for this job since the tier needs the
  data), with the note that the data-provisioning approach
  `golden-data-tier.yml` uses is the likely template. Until it lands,
  requiring `Fast test tier` as a status check would block every merge on an
  infra failure — the memo's required set is amended accordingly.
* A fully-green ci.yml run is therefore **structurally unreachable** until
  (a) the two by-design lanes clear their content and (b) PERF-A fixes the
  fast-tier checkout; every job this program owns is green on #3937's runs.
* **`golden-data-tier.yml` never-fired cron:** resolved trivially — the
  workflow landed on main 2026-08-12 (F1 signature) and its schedule is
  `37 5 * * 1` (Mondays 05:37 UTC); the first Monday since landing is
  2026-08-17, which has not occurred yet. Not a defect; if 08-17 passes
  without a run, then investigate (schedule runs also require the workflow on
  the default branch — it is — and can be suspended by billing state).
* **`golden-data-tier.yml` manual dispatch (owner-authorized, §6 decision 7):**
  dispatched once from `main` this session; result recorded in §Dispatch below.
* **Branch-protection memo:** `docs/governance/branch-protection-memo-2026-08.md`
  — exact ruleset steps, the 8-check required set, the two deliberate
  exclusions, bypass caveat. Executed at G2, not now (owner decision 3).
* **New finding (found by this sweep's own PR #3937, fixed in it):**
  `file-integrity-guard.yml`'s `shrink-guard` job failed at its **checkout
  step** — the guard script never ran. Its `fetch-depth: 0` +
  `filter: blob:none` checkout had no data/raw sparse exclusion (the separate
  workflow was missed by ci.yml's 2026-08-14 data-free-checkout pass), so it
  lazy-fetched the ~10 GB tip working tree and died. Rule-27's CI enforcement
  was therefore red on infrastructure, not content — verified by replaying the
  guard's own script locally under `bash -e` against the identical
  BASE..HEAD: `scanned=3 expected=3 fail=0`. Fixed with the same non-cone
  `!/data/raw/` sparse block ci.yml's nine jobs use; the guard needs no
  working-tree data (tree-level diff scan + per-blob `cat-file`, which
  lazy-fetches on demand).

### D-5 — `patches/pjm-m1-code.patch` (recommendation + closure)

**Defect status: CONFIRMED on main, in a mutated form.** Re-measured with the
patch README's own instruments on the committed `PJM hourly.parquet`:

* Region family **healed** (demand vs `hrl_load_metered` best-lag 0, all
  years/seasons — the parquet was replaced after the 2026-07 diagnosis; last
  touch PR #3852's lane, 2026-08-10).
* Fueltype family (`NG: *`) **one hour early in BOTH 2023 and 2024** — July
  solar centroid 10.91 / 10.94 vs gate [11.5, 12.3] (astronomical ≈ 11.9);
  wind/solar/gas diff-lag +1 vs the PJM UTC feed (solar r = 0.993/0.994 at
  +1). 2025 correct (source fixed upstream ~Feb-2025; Jan straddle stands).
* Code half unapplied: four `datetime_beginning_ept` read sites live
  (`eia930/envelopes.py` ×3 — one **new since the patch** — and
  `scripts/data/curate_zonal_shares.py::parse_pjm_shares`). The patch's
  `--reuse-solved` hunk is already on HEAD independently.

**Recommendation executed under the pre-authorization:** the fix is
solve-affecting (renewable CF shapes, interchange envelopes, zonal shares),
so it is **chartered as DEBUG-B** — full-span PJM re-solve + same-session
registration — in `docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md`,
with the transform **updated to the currently measured state** (fueltype
+1 h for 2023 *and* 2024; region untouched). The patch itself is
**archived-with-note** (`patches/archive/ARCHIVED-2026-08-14-pjm-m1.md`):
applying it verbatim would *double-shift* the now-correct region family and
*keep* the still-wrong 2023 fueltype. **D-5 is closed** — both decision arms
resolved (defect confirmed → chartered; patch → archived, never silently
deleted).

### Commits on this branch

| commit | what |
|---|---|
| `764c486` | launcher keeper-resolved baseline + render-crash fix |
| `01d5748` | ScenarioConfig tuple coercion (cache-key round-trip repair) |
| `ae80c38` | AS-screen probe legacy pin |
| `c4b47bc` | data-profiles.yaml roundtrip route |
| `e77987e` | README stale known-failing note retired |
| `67d603f` | 10 test files filed into tiers + `gen_caisoNNN` allowlist |
| `40a1bb0` | sibling-import census re-measure + `--sibling-census` mode |
| `a168b73` | D-5 closure: patch archived + DEBUG-B charter |
| (this)  | handoff + branch-protection memo + dispatch record |

### Dispatch record — `golden-data-tier.yml` (first-ever run)

Dispatched from `main` @ 5bf5f13, 2026-08-14 03:46 UTC (owner authorization
§6 decision 7). **Run 31767823203: completed FAILURE in 9 m 44 s** (well
under the ≤ ~90-billed-min budget). A red run is a finding, and this one is
precise:

| step | outcome | detail |
|---|---|---|
| checkout | ✅ 72 s | its checkout strategy works — the template the fast tier needs |
| uv + deps | ✅ | |
| `regenerate_clean.py` (9 datatypes) | ✅ 5 m | "regenerated 9 datatype(s) into data/clean" |
| `curate_emissions.py --years 2023` | ❌ | **"The runner has received a shutdown signal … exit code 143"** — a runner-VM-level SIGTERM ~3 min into the curation, i.e. **resource exhaustion of the runner, not a script error**. The identical command succeeds on this session's container (26,534,489 rows → `emissions_2023.parquet`), so the data and code are fine; the workflow's own comment already flags the curation's multi-GB RSS. |
| pytest tier + loud-failure guard | skipped (never reached) | |

**Unifying observation:** the same runner-shutdown signature explains every
infrastructure red seen today — the fast-tier and (pre-fix) shrink-guard
jobs die mid-checkout of the ~10.5 GB tip (ubuntu-latest has ~14 GB free
disk; their logs are not even downloadable, consistent with the runner dying
before log finalization), and the golden tier dies in its one multi-GB
curation step. **The repo's data mass has crossed what a standard GitHub
runner can hold**, which converts the BLOAT workstream (data-corpus
conversion, §6 decision 4) and PERF-A's checkout item from nice-to-haves
into the prerequisites for any data-touching CI.

Dispositions: the weekly cron stands (first opportunity 2026-08-17 — if it
also reds on the emissions step, that is the same finding, not a new one);
the emissions step needs either a larger runner, a lower-RSS curation path,
or the post-BLOAT slimmer corpus — routed to the owner via this record, with
BLOAT-B's re-dispatch (§6 decision 7) as the natural retest point. No
workflow edit made here: the step's failure is capacity, and choosing the
remedy (paid larger runner vs code change) is an owner cost decision.

---

## Addendum — reissued DEBUG manager, post-DEBUG-B continuation (2026-08-16)

**Branch:** `claude/fable-debug-manager-reissue-t8dg4w` (off `origin/main` @
`8a118e7`). **Charter:** the director's reissued DEBUG-manager dispatch
(plan §8 ledger, 2026-08-15 AUDIT-A entry): pjm-162 promotion card, ≤2022
clock card, clean-main re-verification, sibling-import residue, plus audit
gap rows B1/B2/O2 routed to this lane by
`docs/audit/third-party-audit-2026-08.md` §8.

### A.1 — Audit gap row O2 RESOLVED: the PJM C6-attestation "discrepancy" is a stale quote, not scorer drift

The two committed records describe two different points in time, and both
were correct when written. The DEBUG-B finding's like-for-like table
(`docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` §9) quotes the
incumbent's **registration-time** grade — its column header says "rubric
2.9" — scored 2026-08-04 when `results/calibration/pjm152_collapse_A`
shipped **without** `calibration_attestation.json`: C6 UNATTESTED,
determination NOT-YET. `status/PJM.js` (generated 2026-08-09) reflects the
bundle's **current** state: pjm-153 retro-generated the attestation the same
day with every premise computed (`scripts/gen_pjm153_collapse_attestation.py`)
and the D-5(b) re-key re-verified CALIBRATED — the sequence the PJM
`complete` marker's own `determination` text narrates verbatim. The
definitive re-score on committed artifacts at `8a118e7`
(`scripts/calibration_verdict.py --run-id`, no solve, rubric v3.2) confirms
the current state on both sides: **pjm-152 = CALIBRATED, C6 PASS**
("determination basis: all criteria pass, governance attested") and
**pjm-162 = NOT-YET with the single reason "governance gate UNATTESTED: no
governance attestation in bundle"** — every model-determined criterion PASS.
There is no scorer/artifact-schema drift: `score_governance` reads
`calibration_attestation.json` from the sidecar-resolved bundle identically
for both runs; the finding's incumbent column was a stale quote, not a
re-score. **Corrected baseline for the promotion card: the incumbent keeper
is CALIBRATED; the candidate's only gap is the promotion-time governance
attestation, which the promotion mechanics themselves produce** (pjm-153,
nyiso-135 #3977, ercot-202/204 #3947/#3970 precedents). One hygiene note for
future finding tables: a "like-for-like" verdict column quoted from a
registration-time snapshot should say so explicitly, or be re-scored at
writing time — this row cost an audit gap and a re-score to un-confuse.

### A.2 — Both owner cards served and signed; both outcomes executed same-session

**Card 1 (pjm-162 promotion, audit row O1): PROMOTE signed → executed.**
Keeper is now `2026-08-15-pjm-162-inputclock`. Full mechanics + evidence:
`docs/calibration-log/pjm.md` pjm-163 entry (attestation with computed
premises via `scripts/gen_pjm163_inputclock_attestation.py`; D-5(b)
re-verification CALIBRATED before landing; keeper shard + status rebuild;
complete-marker re-key; `audit_keepers --iso PJM --check` PASS 0/0; rule-28
re-stamps of `diurnal_price_amplitude` + `seam_flow_envelopes` +
§5.3 prose header, `check_mechanism_matrix.py` green).

**Card 2 (≤2022 input clock, audit row O3): CHARTER EXTENSION NOW signed →
executed.** `_PJM_INPUT_CLOCK_SHIFTS` now declares 2018–2022 fueltype +1 h;
applied via the new explicit `--apply-years` mechanism (the committed table
is a one-shot migration record, not an idempotent transform — re-running an
embodied entry double-shifts, so the CLI now refuses to run without naming
the not-yet-embodied years). Byte-verified per the finding §2a protocol:
non-fueltype columns identical every row; NG:* outside 2018–2022 identical
(corrected 2023/24 blocks untouched); every in-block cell == pristine at
T−1h (350,592 cells); NaN 49,305 → 49,313 (+8 = the one pre-extract
boundary instant, left NaN not fabricated). July centroids post-fix:
2018–2022 = 11.72/11.73/11.72/11.81/11.73 (were ~10.7), 2023–2025 unchanged.
**Data repair only — no ≤2022 year solved, scored or registered; the spend
freeze and tier markers are untouched.** Execution annotation appended to
the finding §6; audit rows O1/O2/O3 all annotated resolved.
