# FINDING — BLOAT-S2: the §4.8 evidence passes and the Stage-2 (a)-only untrack

**Session BLOAT-S2, 2026-08-17.** Executes the signed O2 grant
(`docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md`, VERDICT block,
owner-signed 2026-08-16): per-corpus §4.8 evidence passes first, then untrack
ONLY corpora whose pass measures a **stable archive** — recovery story (a)
per-corpus re-fetch, evidence-passed, and nothing else. No external archive,
no signed-loss route, pins stay dead: **a corpus that fails its pass simply
STAYS TRACKED and is recorded here.** The §4.7 holdout intakes,
`ercot/cdr.*.zip`, and the §4.2 2023 DAM quarters were never candidates; the
§4.2 DAM-2024+ subset is OUT of this grant (D4).

Method: every pass measures the five legs the charter names — (i) consumer
census (tree-scoped, per-file read calls, classified solve/curation/derive/
probe/test/archive with absent-behavior loud-vs-silent quoted from code);
(ii) golden-tier + holdout overlap including the rule-22 vintage question,
adjudicated against `scripts/lib/holdout_policy.py` tiers (train 2023–2025 ·
validation 2020–2022 · locked-test 2019/2026 · 2018 fail-closed/unsolvable);
(iii) the **measured** retention window of the source archive (live probes
this session, negative controls included); (iv) a working fetch instrument
(existing `fetch_*` script exercised, or a verified per-file URL table);
(v) the manifest plan. **No corpus moved on reputation.**

## 0. Verdict table

| Corpus | Charter MiB | Verdict | Untracked (files / MiB, tree-sha-verified) | Stays tracked — failing leg |
|---|---:|---|---|---|
| `storage-as-awards` | 165.2 | **PASS (full)** | 12 xlsx / **165.2** | — (README + new SHA256SUMS kept) |
| `data/raw/PJM` | 107.1 | **PASS (full)** | 13 csv / **107.1** | — (new README + SHA256SUMS added; `.gitkeep` kept) |
| `campd-unit-level` non-2023 | 692.6 | **SPLIT** | 35 × `*_2018.parquet` / **105.1** | 2019–2026 KEEP — leg (i)/(ii): solve-time year-keyed inputs (holdout + train tiers), silent-degrade absence semantics (§3) |
| `eia-930` bulk | 190.3 | **SPLIT** | 80 per-BA long files + 2 × BALANCE-2018 / **33.8** | BALANCE 2019–2026 KEEP — leg (i)/(ii): `wecc-west-supply` clean-rebuild input for CAISO solve years; 7 hand-assembled derived files KEEP — no (a) story exists (§4) |
| `iso-specific-transmission` | 365.8 | **SPLIT** | 2 × PJM-2018 csv / **33.3** | loss surfaces KEEP (derived solve artifacts, loud); PJM 2019–2026 KEEP (leg ii); SCEDBTCNP686 ×13 KEEP — leg (iv) FAIL: **no fetch instrument exists** (§6) |
| `lmp-data` non-golden | 143.5 | **FAIL — stays tracked** | none | MISO leg (iii) FAIL (measured decaying archive) + 2022/2026 holdout inputs; ERCOT/ subdir leg (ii) (holdout scoring rebuild inputs); passing remainder immaterial (§5) |
| **Total** | | | **144 files / 444.5 MiB** | |

Every untracked byte was tree-sha-verified against HEAD on disk before
hashing (`git hash-object` == `git ls-tree` blob sha, 144/144 files, 0
mismatches — the PR-5/B3 idiom), then recorded in a tracked per-corpus
`SHA256SUMS.txt`. Recovery per corpus README is the (a) story only: verified
source table + fetch command + **measured** window. **Never a pin** — the
2026-08-16 rewrite left pins dead and D2 granted no commitment.

## 1. storage-as-awards — PASS (full), −165.2 MiB

12 CAISO quarterly Daily-Energy-Storage-Report xlsx (2023q1–2025q4; caiso.com
flipped the filename pattern in 2025 — both patterns handled by every
consumer's `storage-report-*.xlsx` glob).

- **(i) Census.** No `src/` file opens the xlsx. The solve reads the curated
  clean datatype only (`src/market_sim/data/storage_as_awards.py:97-99`
  `read_clean`, loud `FileNotFoundError` with regenerate hint), and the one
  solve mechanism gated on it — `ScenarioConfig.caiso_storage_as_reservation`
  (`scenarios.py:5680`) — is **default OFF, probe-adjudicated INERT**
  (caiso-74; refuted at caiso-127/129), armed in **no keeper and no persisted
  run config** (`holdout-data-equivalency-register-2026-07.md:799` — "NONE
  for the keeper"). Curation-absent behavior is a soft `[skip]` print
  (`curate_storage_as_awards.py:60-62`, codified by
  `test_skip_when_raw_absent`). The other consumer chain —
  `derive_caiso_charge_allocation.py` (loud on absence) → the **committed**
  `data/raw/reference/caiso-charge-allocation-profile.csv` — leaves the solve
  reading the committed derived CSV, never the xlsx. Probes (caiso-102/103/
  105/129/176) are probe-time; re-fetch first.
- **(ii) Overlap.** Zero. Not in the golden sparse list, not in any CI glob;
  no test opens the real files. Years 2023–2025 only — **no 2019–2022
  vintage exists**, so the rule-22 question is empty here.
- **(iii) Retention, measured.** `https://www.caiso.com/documents/
  storage-report-2023q1.xlsx` and `.../storage-report-q1-2025.xlsx` both
  HTTP 206 on a ranged GET, 2026-08-17, through the session proxy — the
  oldest and newest vintages of both filename patterns serve. Quarterly
  publication cadence regenerates the series forward (README).
- **(iv) Instrument.** No fetch script exists; the corpus README carries the
  per-file URL table verified 2026-07-11 and **re-verified live this
  session** — the charter's "verified per-file URL table" alternative.
- **(v) Manifest.** New `SHA256SUMS.txt` over all 12 payloads; README gains
  the untrack + recovery section.

## 2. data/raw/PJM — PASS (full), −107.1 MiB

5 × `PJM_<2018..2022>_rt_hrl_lmps.csv` + 8 × `PJM_gen_by_fuel_<2018..2025>.csv`.

- **(i) Census: ZERO functional consumers.** The corpus is an orphan created
  by a naming trap: the live gen-by-fuel reader
  (`curate_generation.py:380`) globs `PJM_*_gen_by_fuel.csv` under
  `ISO-specific-gen-data/` (year-before-fuel — both directory and pattern
  miss this corpus), and the live LMP actuals pipeline
  (`derive_actual_lmp.py:278`, `curate_lmp.py:332`) reads
  `lmp-data/PJM_<year>_rt_da_monthly_lmps.csv`. The single textual reference
  is a filename listing in an archived audit. No paths.py constant, no
  data-register row, no README existed.
- **(ii) Overlap.** Not golden-listed; no test reads it. The card's rule-22
  flag ("PJM 2018–2022 LMPs" as suspected holdout inputs) **resolves
  negative**: the PJM holdout LMP bench is built from the golden-listed
  `lmp-data` monthly files ("LMP bench 2018–2025 full" —
  `iso-2022-holdout-data-availability-audit-2026-07.md:155`), not from these
  hourly files. Nothing reads them for any tier.
- **(iii) Retention, measured.** PJM DataMiner2, probed live 2026-08-17 via
  the repo's own client (`scripts/lib/pjm_dataminer.py`, public subscription
  key): `rt_hrl_lmps` and `gen_by_fuel` both return 2018-01-01 rows.
  Data-Miner-class stable — exactly the class the O2 grant admits.
- **(iv) Instrument.** `scripts.lib.pjm_dataminer.fetch_page` exercised live
  on both feeds (1-row probes, 2018 window). `rt_hrl_lmps` is scripted by
  `fetch_pjm_transmission.py`'s hub-LMP leg; `gen_by_fuel` is a documented
  manual DataMiner2 export (`docs/storage-dispatch-data-sources.md:67`). The
  new README carries feed names, API base, key mechanism and the probe record.
- **(v) Manifest.** New `README.md` + `SHA256SUMS.txt` over all 13 payloads.

## 3. campd-unit-level non-2023 — SPLIT: 2018 only, −105.1 MiB

The census **fails the prima facie story for 2019–2026**: this corpus is a
**solve-time input**, not a derive-only archive. `run_calibration_full.py:1651`
loads `campd.load_campd_hourly(states, [year])` for the **solve year** (per-
plant hourly net MW), and `outages.py:1469` reads
`campd-unit-level/{STATE}_{YEAR}.parquet` for the solve year (backcast retiree
availability envelope). Both degrade **silently** on absence (`return None` /
warning). So: 2023 golden (KEEP, tier sparse list `*_2023.parquet`);
2024–2025 train-tier solve inputs (KEEP — every rule-16 keeper re-solve
hydrates them; silent degradation on absence is disqualifying); 2019–2022 +
2026 holdout-tier solve inputs (**KEEP per the grant** — hydration for
touchpoint/locked solves must keep working, and re-fetch would break the
rule-22 vintage freeze).

**The 2018 vintage passes.** 2018 is outside the working span (owner decision
2026-08-06; fail-closed unsolvable tier — no solve can read it):

- **(i)** All 2018 consumers are derive/curation-time: the forward CO2-rate
  history (`derive_fossil_co2_rates.py --years 2018 2019 2020 2021`), the
  committed 2018–2026 outage-extract recipe (`derive_campd_unit_outages.py`,
  gate probes `_caiso198/_caiso199`), `derive_correlated_outage_curve.py`
  (2018–2025 → hand-frozen constants), `curate_emissions*.py` glob-defaults.
  All rule-23 contexts: re-derivation sessions re-fetch 2018 first (README).
- **(ii)** No test reads any non-2023 file (the only real-data read is
  `RI_2023`; every other fixture is synthetic tmp-dir). Golden glob untouched.
- **(iii) Measured:** EPA CAM-API bulk-files served
  `emissions-hourly-2018-tx.csv` and `emissions-hourly-2019-pa.csv` (HTTP
  206, `x-api-key: DEMO_KEY`) 2026-08-17 — stable federal archive, full
  history.
- **(iv)** `scripts/data/fetch_campd_unit_level.py --year 2018 --states …` is
  the documented producer of the vintage (README: "any missing file
  regenerates from the committed fetcher"); 2018 carries no quarantine gate.
- **(v)** New `SHA256SUMS.txt` over the 35 payloads; README gains the
  recovery section (re-fetch **before** running any 2018-spanning derive).

## 4. eia-930 bulk — SPLIT: long files + BALANCE-2018, −33.8 MiB

- **TAKEN (82 files):** the per-BA per-year long files
  (`<BA>_{fueltype,region}_<year>.parquet`, incl. the consumer-less
  `NYIS_*_2025ext` pair) and `EIA930_BALANCE_2018_{Jan_Jun,Jul_Dec}`.
  Census: **no solve-time reads** — they are rebuild inputs for the
  **committed** wide `eia-930-hourly/<BA> hourly.parquet` extracts (which are
  golden-listed and stay), plus probe fallbacks. The rule-22 flag resolves:
  holdout solves read the committed extracts, not these files. Retention
  measured: `eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_
  2018_Jul_Dec.csv` and `2019_Jan_Jun.csv` HTTP 200 (full bytes) 2026-08-17 —
  stable federal bulk archive serving the corpus's **oldest** vintage.
  Instruments: `fetch_eia930_balance.py` (BALANCE), `fetch_eia930_bulk_long.py`
  (2018 long files — exists precisely because the v2 API floor is 2019),
  `fetch_eia930_long.py` (2019+, `EIA_API_KEY`). Note recorded in the README:
  `api.eia.gov` is proxy-blocked in CCR sessions; the sixMonthFiles bulk host
  (used by the first two instruments) is reachable and is the measured route.
- **KEPT — BALANCE 2019–2026 (15 files):** `derive_wecc_west_supply.py` reads
  them to rebuild the **clean** `wecc-west-supply` datatype, which
  `src/market_sim/data/wecc_west_fleet.py:191` reads at **solve time** for
  CAISO's WECC_import node (core default topology; clean is gitignored/
  disposable, so calibration lanes rebuild it from these files). Train years
  need 2023–2025; the validation ladder and locked test need 2019–2022/2026
  under the same rule-22 vintage freeze as §3.
- **KEPT — the 7 hand-assembled derived files** (`eia_demand_profiles`,
  `eia_demand_meta`, `eia_generation_profiles` [golden], `eia_fossil_mix`,
  3 × `*_multiyear.json`): README records "no producing script found …
  refetch procedure unknown". **No (a) story exists**, and O2 admits no loss
  route — irreplaceable-class, stay tracked. (`eia_demand_profiles` /
  `eia_generation_profiles` are also direct solve-time reads.)
- **KEPT — unsuffixed `NYIS_fueltype.parquet`/`NYIS_region.parquet`:**
  full-span files of uncertain construction (no per-year decomposition
  documented) — same no-measured-story caution.

## 5. lmp-data non-golden — FAIL, stays tracked (0 MiB)

- **Golden re-walk at HEAD:** the sparse list now covers `lmp-data/NEISO/`
  and `lmp-data/NYISO/` **as whole directories** (plus CAISO hourly + PJM
  monthly globs), so the charter's 143.5 MiB over-counts today's non-golden
  remainder; what is left is MISO/ + ERCOT/ + 6 root SPP zips + misc.
- **MISO stagings — leg (iii) FAIL, measured.** `docs.misoenergy.org`
  marketreports probed 2026-08-17: `20220601`/`20221231` → **404**,
  `20230101`/`20230215`/`20230301`/`20260101` → 200. The rolling ~3.5-year
  window is real and year-quantized — the 2023 gz stagings' source dies
  ~Jan 2027; the 2022 chunks are already past it (recoverable only via the
  key-gated Data Exchange API) **and** are the 2022 validation-touchpoint
  scoring source (MISO holds no committed 2022 bench part) — holdout KEEP
  besides. "Re-fetchable decays" is exactly the A2 lesson the grant priced.
- **ERCOT/ subdir zips (2018–2022 + 2026) — leg (ii) KEEP.** Sole rebuild
  source for the holdout-year ERCOT actual-LMP blocks and the zonal parquet
  (`derive_actual_lmp.py` rglob; ERCOT holds no 2020–2022 bench/tail rows,
  so touchpoint scoring must re-derive). Holdout inputs are KEEP under this
  grant. (Their archive did measure stable — MIS annual SPP archive doc
  642564845 (DAM 2018) served its exact provenance bytes 1,765,054 live,
  negative control: bogus doc-id returns a 105-byte error XML — recorded for
  a future sitting, but the holdout rule decides.)
- **Root 2023–2025 SPP zips (~12 MiB) + misc zero-consumer files**
  (`dartmonthlylmpindex_*`, `my_reports.zip`): admissible-or-junk but
  immaterial; four standing ERCOT probes hard-code the root zip paths. Not
  worth a conversion in a corpus that otherwise stays tracked. Recorded, not
  taken. `my_reports.zip` has no provenance/no consumers — flagged as an
  owner hygiene question, **not** untracked (no measured story).

## 6. iso-specific-transmission — SPLIT: PJM-2018 pair, −33.3 MiB

The derived/source split the charter asked for:

- **DERIVED, KEEP:** `CAISO/MISO/PJM_loss_surface.csv` — derive artifacts
  committed here and read **directly at solve time**
  (`data/loss_surface.py:88` raises loudly on absence). Small; stay.
- **SOURCE, KEEP — PJM 2019–2026:** `import_export_act_sch_interchange` is a
  **direct solve-time read keyed on the solve year**
  (`eia930/envelopes.py:1083ff`, silent fallback = seam left uncapped —
  disqualifying absence semantics); `transfer_limits_and_flows` reaches
  solves via the disposable clean `transfer-interface-limits` rebuild
  (loud, pjm-119 contract). Train + holdout tiers per §3's logic.
  (`tests/iso/pjm/test_pjm_seam_flow_limit.py` reads the real 2024 file —
  train-tier, kept, so no test impact.)
- **SOURCE, KEEP — SCEDBTCNP686 ×13 (NP6-86): leg (iv) FAIL.** No fetch
  instrument exists in the repo (README: the MIS listing retains ~7 days;
  the Data Portal archive sits behind an Incapsula-protected login —
  "the archives must be supplied manually"). Also the rebuild input for the
  clean `gtc-limits` partitions ERCOT solves read (silent "static TTC kept"
  degrade). Not re-fetchable, not takeable under (a).
- **TAKEN — the two `PJM_2018_*` csvs.** 2018 is unsolvable (§3); the
  curation glob tolerates a missing year; the year-keyed envelope reader
  never asks for 2018; `derive_pjm_seam_ladders.py`'s window is
  2019/2021/2022 + train. Retention/instrument measured live 2026-08-17:
  both DataMiner2 feeds (`act_sch_interchange`, firstAvailable 2014-01-01;
  `transfer_limits_and_flows`, firstAvailable 2011-01-01) returned
  2018-01-01 rows through `scripts.lib.pjm_dataminer`;
  `fetch_pjm_transmission.py --years 2018` is the exact committed producer.
  Manifest: new `SHA256SUMS.txt`; README gains the recovery section.

## 7. Workflows re-walk at execution HEAD

All 7 workflows walked at `a4ef2a9`:

- `golden-data-tier.yml` — **ZERO edits needed, verified per-glob**: the
  sparse list's only touchpoints with the take-set's corpora are
  `campd-unit-level/*_2023.parquet` (2023 kept), `eia-930/
  eia_generation_profiles.parquet` (kept), and the lmp-data golden globs
  (corpus untouched). `data/raw/PJM`, `storage-as-awards`,
  `iso-specific-transmission` appear in no glob. The in-job clean
  provisioning (9 datatypes + emissions 2023) reads nothing untracked here.
- `ci.yml` — the data-bearing job's sparse list mirrors the tier's
  (verified: `storage-as-awards` absent, `/data/raw/reference/` present so
  the committed charge-allocation CSV still materializes); the other jobs
  exclude `data/raw` wholesale. `quarantine-gates` unaffected (no bundles).
- `deploy-pages.yml`, `perf-a-ci-probe.yml` (same five lmp-data lines),
  `file-integrity-guard.yml` (excludes `data/raw`; the one core-file edit
  here, `run_calibration.py`, shrinks 12 lines ≪ 30 %),
  `fetch-caiso-oasis-bulk.yml`, `cleanup-large-blobs.yml` — no reads of any
  taken path.

**Golden-tier proof (D3):** the weekly cron (Mondays 05:37 UTC; first firing
2026-08-17) is the proof mechanism — **no dispatch spent**, per the grant.
The post-merge proof is the first cron green after merge. A red on a
data-missing skip means RESTORE the corpus, never widen the sparse list.

## 8. Pre-existing red found and fixed: `scripts/run_calibration.py` SyntaxError at origin/main

The §5(c) baseline run could not even collect: `origin/main` (`a4ef2a9`)
carried a **duplicate `reliability_floor_plant_exclusions` kwarg** in
`run_year` (lines 529 + 538) plus a duplicated `with_overrides` block — a
`SyntaxError` failing collection of 32 test modules and blocking every
`run_calibration.py` import. Genealogy: nyiso-140 (`3febd5c`) landed the
mechanism minus the `run_year` kwarg; the ercot-213 repair (`7246272`) added
it; merge #4036 then brought both copies together. This session fixed it by
deleting the duplicate kwarg + duplicate override block; both runners
AST-parse clean and the fast lane collects 6,900 tests green after the fix.

**Post-rebase addendum (same day):** two OTHER sessions fixed the same
SyntaxError on main concurrently (`ebd31a9`, `fff285a`), their collision
dropped BOTH copies (`2dd9dbc` "lost to twin fixes" restored only the
signature parameter), so at the rebase base `296adea` `run_year` **accepts
the kwarg and silently ignores it** — the `with_overrides` application block
is gone while `run_calibration_full.py` still passes the flag through,
making the nyiso-140 arming a silent no-op via that path (the dead-flag
class the caiso-98 lesson forbids). This branch's original dedup commit was
auto-dropped at rebase (contents already upstream); a follow-up commit
restored the missing application block, matching every sibling kwarg's
pattern. **Final state:** the #4044 miso-160 merge (`ce7ce8e`) then restored
the same wiring on main, so at the final rebase (base `bad0807`) that commit
auto-dropped too — the branch ships NO `run_calibration.py` delta, and this
section stands as the discovery/genealogy record.

## 9. Skip-when-absent verification (§0ar-3(c) / card §5(c))

Protocol: identical pytest invocations before and after the untrack —
fast lane (`-n auto -m "not slow and not integration and not fulldata"`) and
the tier's marker lane (`-m "slow or integration or fulldata"`, serial, the
three perf benchmarks deselected), each preceded by the tier's own
`data/clean` provisioning (`regenerate_clean.py` × 9 datatypes +
`curate_emissions.py --years 2023`) — the "after" runs in a scratch worktree
checked out from the branch tip, where the untracked payloads do not
materialize (the exact state of a fresh clone post-merge). None of the nine
provisioned datatypes nor the emissions-2023 curation reads any taken
payload (verified against each curator's raw globs), so provisioning is
invariant across the comparison.

An un-provisioned first pass also measured the **clean-absent** slow-lane
state (15 fails, all `data/clean`-missing effects: confirmed-retirements
partitions, clean reference, ff-readiness resolution — none names a taken
corpus); it is recorded here because a `code`-profile session that skips
provisioning sees exactly those, before and after this PR alike.

The gate is **zero new reds vs the like-for-like baseline** — a corpus whose
absence reds a test is RESTORED, per the charter, not merged over.

### 9a. Result (measured at execution) — ZERO new reds, identical skip sets

The clean provisioning itself also ran **in the absent worktree** and
completed identically (9 datatypes + emissions-2023, exit 0) — the
provisioning-invariance claim is execution-proven, not census-only.

### 9b. Lane counts, like-for-like

| Lane | Baseline (present) | Absent-worktree | New reds / new skips |
|---|---|---|---|
| fast (`-n auto`, not slow/integration/fulldata) | 6,900 P / 31 S / 2 XF / 0 F | **6,900 P / 31 S / 2 XF / 0 F** | **0 / 0** (skip sets identical) |
| slow/integration/fulldata (serial, 3 perf deselects) | 44 P / 2 S / 0 F | **44 P / 2 S / 0 F** | **0 / 0** (skip sets identical) |

## 10. Second pre-existing red, DIAGNOSED BUT NOT REPAIRED (out of lane): the miso-160 stranded registration

`check_registry_payload_parity.py` is **RED at origin/main**, before and
independent of this session: the sidecars
`registry/2026-08-16-miso-160-{control,wefor-shape}.json` are committed with
**no `runs/<id>.js` payloads and no bundle dirs** — the exact
sidecar-without-payload stranding of
`docs/handoffs/dashboard-payload-push-gap-2026-07.md`. Diagnosis: PR #4035
merged an early point of `claude/miso-backcast-calibration-nk4zhj`; the
session kept pushing to the branch after the merge, and the branch tip
(`c7dbccd`) holds everything main is missing — both payloads (~1.5 MB each),
the `miso160_wefor_{A,B}` bundles (hourly sidecars included), **plus ~67
files of unmerged mechanism code** (new `ScenarioConfig` fields, tests, a
probe — and its own copy of the §8 SyntaxError fix). This session does NOT
bring any of it over: completing a MISO mechanism + registration is that
lane's work (rules 25/28 — a new mechanism needs its matrix row; a keeper
question needs its own session), and payloads alone would put runs on the
dashboard whose generating code is absent from HEAD. **Disposition: left
red, reported to the owner** — either merge the branch tail (MISO lane
session) or prune the two orphan sidecars. `audit_keepers --check` PASS 0/0
and `check_bundle_retention` PASS are unaffected, and this PR adds no parity
item (verified: the failure list at this branch's HEAD is identical to
origin/main's — the two miso-160 rows only). **RESOLVED UPSTREAM while this
PR was in flight:** PR #4044 merged the branch tail (payloads, bundles and
the mechanism code) at `bad0807`, and the parity gate is GREEN at the final
rebase base — re-verified by this session's closing gate run. This section
stands as the diagnosis record. **A successor instance appeared with the
same merge wave:** at `bad0807` the caiso-200 lane's `caiso200_h0_control`
bundle (landed `c39de54`, the lane's live promotion work) maps to no
retained sidecar, so `check_bundle_retention` now fails on IT — again
pre-existing on main, again another lane's in-flight artifact (register /
prune / allowlist is the caiso-200 session's call, not this PR's). Same
disposition: reported, not touched.

## 11. Manifest + ignore semantics assertions (per payload class, in-PR)

For every taken class: `git check-ignore` matches each removed payload after
the `.gitignore` block lands, and matches **no kept file** (READMEs,
SHA256SUMS, `.gitkeep`, golden 2023 campd files, BALANCE 2019–2026, unsuffixed
NYIS pair, loss surfaces, SCED parquets, PJM 2019–2026 — asserted
per-corpus in the untrack commits). SHA256SUMS hashed from disk bytes only
after per-file tree-sha verification against HEAD (144/144 clean, §0).
