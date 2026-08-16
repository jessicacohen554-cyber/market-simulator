# Bloat Removal Report — FINAL (BLOAT-B-7, the re-measured WS6 close-out)

**Program:** Model Audit & Release-Finalization, WS6 · BLOAT
(`docs/model-audit-release-plan-2026-08.md` §3/WS6). **Session:** BLOAT-B-7,
the re-measured close-out the PM ruling left OPEN when it salvaged PR #3954
(release plan §8, 2026-08-15). **Branch:** `claude/bloat-b7-ws6-closeout-62o3p1`.
**Measured at:** `04d1cf05180ba74a6c2535b1b2bd75ea60439268` (origin/main,
2026-08-15 22:22 UTC), with **all five BLOAT-B data PRs merged**: PR-1
(#3957 + #3958), PR-2 (#3956), PR-3 (#3982), PR-4 (#3955), PR-5 (#3978 + #3979).

This report is the AFTER measurement that
`docs/bloat-removal-report-2026-08.md` — the **salvaged pre-prune baseline**
at `315a245`, landed via #3976 under its supersession banner — was preserved
for. That document is not rewritten; every "vs `315a245`" figure below
subtracts from it. Method is unchanged and re-validated there (§3): full
`GIT_NO_LAZY_FETCH=1 git ls-tree -r -l` over the tip tree, tree-only reads;
sizes are MiB of logical blob bytes in the git tree.

---

## 1. HEADLINE — the program executed, and the tip landed on the full-sign-off trajectory

| | BLOAT-A base `f2de3b0` (2026-08-14) | Pre-prune `315a245` (2026-08-15 ~02:00) | **This close-out `04d1cf0`** |
|---|---:|---:|---:|
| Tip total | 10,080.0 MiB / 11,127 files | 10,115.0 MiB / 11,214 files | **6,405.7 MiB / 9,204 files** |
| vs BLOAT-A base | — | +35.2 MiB | **−3,674.3 MiB (−36.5 %)** |

Reconciliation of the −3,674.3: the five data PRs measured **−3,737.1 MiB at
tip** as executed (739.8 + 361.8 + 0 + 2,518.5 + 117.0), and the repo
organically grew **+62.8 MiB / +255 files** over the same two days (new
calibration bundles and payloads ercot-202/204, neiso-93, nyiso-135, pjm-162,
the miso-159 transfer pack, the five 2018–2022 NYISO Gold Books, docs). The
two figures close the ledger exactly.

Against the plan's §8 trajectory:

| Trajectory point (plan §8) | Est. MiB | Actual |
|---|---:|---:|
| Class-approved only (PR-1..PR-4) | ≈ 8,110 | — (overtaken: PR-5 was signed and executed) |
| Full sign-off (all items, C rows included) | ≈ 6,092 | **6,405.7** |

The executed program is the full-sign-off trajectory **minus the two vetoed
C-touchpoint rows** (kept, 5.9 MiB) — and it landed within ~315 MiB of the
≈6.1 GiB line. The gap is fully explained: +62.8 organic growth plus the net
−250.5 MiB estimate variance itemized in §3 (PR-1 under-recovered by 805.2,
A2 over-recovered by 566.9 — the same codec fact seen from both sides — and
PR-3's target had grown by the time it executed).

The clone/hydration story this feeds (`docs/fast-clone.md`, CLAUDE.md
"Cloning & session data"): these are tip-tree logical bytes, the quantity
that governs sparse-checkout hydration weight — **what a profile hydrates is
now ~36 % lighter overall**, and the `ercot` profile far more (Class A alone
took data/raw/ercot/SCED from 3,258.0 to 728.5 MiB). Pack size is unchanged
by design — history is kept; it is the archive (§5).

---

## 2. Re-measured tip decomposition

| Tree | `f2de3b0` | `04d1cf0` | Δ | Note |
|---|---:|---:|---:|---|
| `data/raw` | 9,766.7 / 4,722 | **6,161.8 / 2,850** | −3,604.9 | PRs 1+2+5 removed 3,620.1; organic +15.2 (Gold Books +12.4, misc) |
| `results/calibration` | 141.3 / 1,362 | **63.9 / 1,238** | −77.4 | PR-3 −117.0; organic +39.6 (new bundles/records since 08-14) |
| `frontend/data/backcast/runs` | 70.1 / 66 | **76.9 / 70** | +6.8 | 4 net registrations; rule-15 retention live |
| `docs` | — | 22.9 / 1,095 | — | |
| `scripts` | — | 19.5 / 1,722 | — | 110 top-level `.py` / 237 in `archive/` (§4 D-row) |
| **Tip total** | **10,080.0 / 11,127** | **6,405.7 / 9,204** | **−3,674.3** | |

**The `data/raw` load-bearing decomposition at `04d1cf0`** (same glob-evaluation
method as plan §2, re-validated in the salvaged report §3):

| Block | `f2de3b0` | `315a245` | `04d1cf0` |
|---|---:|---:|---:|
| Golden-tier-matched (KEEP-REQUIRED at tip) | 1,500.0 / 1,038 | 1,512.8 / 1,043 | **1,375.9 / 1,028** |
| Everything else in `data/raw` | 8,266.7 / 3,684 | 8,267.2 / 3,684 | **4,785.9 / 1,822** |

The golden-matched block **shrank by 136.9 MiB** without a single sparse-glob
edit: PR-2's B5/B6 conversions removed payloads that lived *inside*
golden-listed directories (`NYISO/` SOM PDFs 44.9 + 2023–26 Gold Books 11.1 +
load-report zips 65.2, `PJM-AS/` PDFs 17.2 ≈ 138.4) — exactly the CI-checkout
weight reduction §4.5 predicted, and the golden tier's green run (§6) is the
proof no test opened any of it.

**Stage-2 territory re-measured** — the §9/BLOAT-3 input. The non-golden
remainder minus the plan's keep-verdict carve-outs that Stage 2 explicitly
cannot take (§1 fact 3, §3 row 3: the irreplaceable post-slim ERCOT-157 SCED
window 728.5/327, the `ercot86_tail_days` standing-derive extract 39.9, the
`caiso-dam-outages` derived parquet + manifests 8.8, corpus manifests 0.01):

| Stage-2 adjudication pool at `04d1cf0` | MiB | Files |
|---|---:|---:|
| **Pool total** | **4,008.7** | **1,487** |
| — of which §4.2 KEEP (21 loose + 8 `DAM/` 60-day DAM parquets; 2023 quarters irreplaceable, 2024+ "re-enters only with Stage 2") | 367.2 | 29 |
| — of which §4.7 KEEP (holdout-equivalency intakes 2_DAY/DAMASAGG/DRUC, grown 223.0 → 290.1 with the 2026 snapshots; `cdr.*.zip` 39.5) | 329.5 | 147 |
| **— takeable remainder (the residual proper)** | **≈ 3,311.9** | **≈ 1,311** |

The residual's named constituents are **byte-unchanged from the plan's §2
table** — `campd-unit-level` non-2023 692.6 · `ercot-AS` non-golden 598.5 ·
`CAISO-AS` 535.8 · `ercot-hsl` non-golden 428.3 · `iso-specific-transmission`
365.8 · `eia-930` bulk 190.3 · `storage-as-awards` 165.2 · `lmp-data`
non-golden 143.5 · `PJM` 107.1 · loose-ercot ORDC-adder/misc 48.3 · smaller
tails ~36. BLOAT-B touched none of it. A full Stage-2 untrack of the takeable
remainder takes the tip to **≈ 3.0 GiB** (from the plan's pre-execution
"≈ 2.5 GiB", the difference being the keep-verdict carve-outs now counted
where they belong). See §7/BLOAT-3.

---

## 3. Per-PR reconciliation against the plan's §8 estimate table

| PR | Items | Est. (plan §8) | Measured | Variance |
|---|---|---:|---:|---:|
| PR-1 #3957+#3958 | A1 + B1a SCED in-place slim | ≈ 1,545 | **739.8** | **−805.2** |
| PR-2 #3956 | B4 xlsx + B5 PDFs + B6 zips + B3-GUID | 361.8 | **361.8** | 0.0 |
| PR-3 #3982 | C-5.1 hourly prune | 62.7 appr. (+23.2 hold +5.9 sign-off) | **117.0** | +25.2 vs all-rows |
| PR-4 #3955 | D1 + D2 rotation | ~0 | **~0** | 0 |
| PR-5 #3978 | A2 + B1b + B3 (signed) | ≈ 1,989 | **2,518.5** | **+529.5** |
| **Total** | | **≈ 3,988** | **3,737.1** | **−250.5** |

The three material variances, all diagnosed at execution — cited, not
re-derived:

1. **PR-1: 739.8 vs ≈ 1,545.** The 0.547 precedent ratio was measured on the
   ORIGINAL SNAPPY blobs (ERCOT-157, 2026-07-22); the 2026-08 re-uploads
   landed already default-zstd, so the codec half of the yield was banked
   before the PR ever ran and only the column-projection half remained
   (21.3 % measured). The plan anticipated this ("verify at execution"; B1a
   "self-cancels at measurement"). Diagnosis: PR #3958 body; plan §8 PR-1
   EXECUTED note.
2. **PR-5/A2: 1,846.9 vs ≈ 1,280 — the same fact in reverse.** The A2
   estimate assumed a post-slim window of ≈ 1,280 MiB; because the slim
   recovered 21.3 % rather than the SNAPPY-era 45 %, more bytes were left in
   the 2024+ window for the conversion to take. The two variances are one
   codec fact double-entry-booked, and they net to −238.3 across A1+A2.
   Diagnosis: plan §3 A2 EXECUTED note. (PR-5's other legs: B1b −111.7 vs
   145.1 — B1a's slim had already banked the projection on the three
   extracts, §4.1; B3 −559.9 vs 563.6 — the 3.7 GUID hygiene sub-item had
   executed early, in PR-2, §4.3.)
3. **PR-3: 117.0 across 24 bundles vs 62.7 across 19.** The hourly corpus
   kept growing while BLOAT-B waited (92.9 MiB/19 named rows at BLOAT-A →
   137.3/30 at B-6's census → 158.4/34 at execution), all three lane HOLDs
   lifted on lane state, keepers moved in three ISOs mid-session, and the
   list was re-derived twice as main moved (`726f389` → `b26c13e` →
   `11b59ee`). Diagnosis: plan §5.1 EXECUTED record; PR #3982 body.

---

## 4. Per-item executed / vetoed ledger (plan §3–§7, verified against the `04d1cf0` tree)

| Item | Plan status | Outcome | Verified at `04d1cf0` |
|---|---|---|---|
| **A1** SCED in-place slim (1,027 files) | class-approved | **EXECUTED** PR-1 (#3957 manifests, #3958 slim) — −739.8 MiB w/ B1a, ERCOT-157 acceptance 15/15 byte-identical | corpus = 323 post-slim shards + README + SHA256SUMS + rtcb README stub = 728.5 MiB / 327 files |
| **A2** SCED 2024+ window conversion | needs-sign-off | **SIGNED & EXECUTED** PR-5 — −1,846.9 MiB (673 shards + 27 rtcb parts) | zero 2024+ shards tracked; rtcb quarantine layout kept via README stub |
| ERCOT-157 window "never converted" row | recorded | **HONOURED** | the 323 shards are the corpus |
| **B1a** 4 loose extracts slimmed with A1 | class-approved | **EXECUTED** PR-1 — 208.6 → 151.6 MiB | — |
| **B1b** 3 probe-only extracts converted | needs-sign-off | **SIGNED & EXECUTED** PR-5 — −111.7 MiB | only `ercot86_tail_days` tracked (39.9 MiB, standing rule-23 derive) |
| **B2** 21 loose 60-day DAM parquets (§4.2) | verified KEEP | **HONOURED** — untouched | 244.1 MiB / 21 loose + 123.1 / 8 in `DAM/`; Stage-2 re-entry per §4.2 |
| **B3** `lmp-data/CAISO` 60 OASIS dailies + GUID | needs-sign-off | **SIGNED & EXECUTED** — dailies −559.9 in PR-5; GUID −3.7 in PR-2 | 10 tracked files: 8 golden hourly aggregates (23.0 MiB) + README + SHA256SUMS |
| **B4** `caiso-dam-outages` 1,094 xlsx | class-approved | **EXECUTED** PR-2 — −155.0 MiB | 5 tracked files (8.8 MiB): derived parquet + README + SHA256SUMS + missing-days + patch |
| **B5** 28 publication PDFs | class-approved | **EXECUTED** PR-2 — −137.9 MiB; the five 2018–2022 Gold Books (+12.4, post-inventory arrivals with unrecorded re-fetch URLs) held back OUT OF SCOPE in the PR's recorded deviation (a) | 10 PDFs remain under `data/raw` (15.5 MiB): 3 NYISO-AS LRR (§4.5 KEEP), 2 capacity-market/caiso (§4.5 KEEP), 5 Gold Books 2018–2022 (the recorded holdback) |
| **B6** 4 NYISO load-report zips | class-approved | **EXECUTED** PR-2 — −65.2 MiB | zero `nyiso load reports` zips at tip |
| **§4.7** adjacent holdout intakes / cdr zips | verified KEEP | **HONOURED** — untouched, organically grown | intakes 290.1 MiB / 47 (2026 snapshots landed since); `ercot/cdr.*.zip` 39.5 / 100 |
| **C-5.1** class-approved rows + lifted HOLDs | class-approved / HOLD | **EXECUTED** PR-3 — 24 bundles / 288 files / −117.0 MiB; all three HOLDs lifted on lane state | hourly corpus = 41.4 MiB / 97 files / 10 dirs: the 6 keeper bundles, `_nyiso114_baseattrib_2024`, the 2 vetoed rows, `pjm_debugb_inputclock_A` |
| **C-5.1** touchpoint rows (`neiso86_2022_corrected`, `pjm2022_touchpoint`) | needs-sign-off | **VETOED by owner (B-5 G1 card) — KEPT** while both 2022 loops are live | both carry `hourly/` intact: 3.66 MiB / 6 files and 2.19 / 4 |
| **C-5.1** new hold `pjm_debugb_inputclock_A` | (post-plan) | **HONOURED** — live keeper CANDIDATE, owner promotion call pending | present, 6.32 MiB / 12 |
| **§5.2** the four `_`-prefixed dirs | verified KEEP | **HONOURED** | all four present (`_archive`, `_ercot144_scratch`, `_nyiso114_baseattrib_2024`, `_pjm152_keeper_recipe`) |
| **D1+D2** script rotation | class-approved | **EXECUTED** PR-4 — 86 rotated, keep-set re-derived to 4, `run_ces_leg.py` verified-kept, all gates green | 110 top-level `.py` / 237 archived. The 2 above PR-4's 108 are *post-PR additions* (`gen_ercot202_attestation.py`, `gen_ercot204_attestation.py`) — the rotation rule's next ordinary backlog, not regression |
| **E1** dashboard payload prune | nil-action | **CONFIRMED nil** | registry 70 = payloads 70; parity green (§8) |
| **E2** Class-E retention rule | proposal | **PENDING OWNER ADOPTION** → BLOAT-2 (§7) | rule 4's quarterly bundle-parity sweep also still unbuilt |
| §5.3 / §10 keep-required inventory | keep | **HONOURED** | 903 loose records (14.2 MiB) at the `results/calibration` root; `results/hindcast` 20.2; `results/regression-goldens` present; `scripts/probes/` untouched |

Nothing on the plan's item list is unaccounted for: every class-approved item
executed, every needs-sign-off item got its owner verdict (three SIGNED, one
VETOED), every KEEP verdict held at the measured tree.

---

## 5. `cleanup-large-blobs.yml` DRY RUN — the post-prune superseded-blob floor

Dispatched by this session with `dry_run=true`; the `REWRITE-HISTORY` confirm
phrase was **not supplied** (`confirm=DRY-RUN-ONLY-NOT-A-REWRITE`). Run
**`31912344135`** (run #17) at head `04d1cf0` — this close-out's exact
measurement commit. Step record confirms the guard held: `Validate
confirmation` skipped, `Validate push token` skipped, and the run ends at
the breakdown ("Re-run with dry_run=false and confirm=REWRITE-HISTORY to
execute") — strip, repack, verify and push never reached. (Units note as before: the workflow prints
"MB" while dividing by 1048576 — read as MiB.)

| Quantity | Pre-prune floor @ `315a245` (run `31857841269`, salvaged §2) | Post-prune @ `04d1cf0` (run `31912344135`) | Δ |
|---|---:|---:|---:|
| PROTECTED (live at `main` tip) | 6,032 blobs / 9,901.7 MiB | **4,063 blobs / 6,225.7 MiB** | −1,969 / −3,676.0 |
| REMOVABLE (superseded) | 3,974 blobs / 922.3 MiB | **7,053 blobs / 7,338.4 MiB** | **+3,079 / +6,416.1** |
| Disjointness (removable ∩ protected = ∅) | PASSED | **PASSED** | |
| Mirror-clone pack (all refs) | 17.92 GiB | **20.45 GiB** | +2.53 GiB |

(In-scope blobs in history: 11,116 of 36,283 total; whole-repo unique tip
blobs 8,890. The pack GREW because the slim wrote ~2.7 GiB of new post-slim
blobs while history kept every old one — the visible, by-design cost of the
no-rewrite recovery model.)

**What the delta means.** The removable pool grew by exactly what the prunes
manufactured, and the run's by-directory table attributes it item by item:
`data/raw/ercot/SCED/` + `rtcb-format-2026/` **5,105.0 MiB** = the whole
pre-slim raw corpus (3,258.0) plus the post-slim 2024+/rtcb blobs A2 then
untracked (1,846.9); loose `data/raw/ercot/` **320.3** = the four probe
extracts' raw versions (208.6) plus the three post-slim blobs B1b untracked
(111.7); `lmp-data/CAISO/` **570.0** ≈ B3's 60 dailies (559.9) + the GUID +
churn; `caiso-dam-outages/daily/` **155.0** = B4's xlsx exactly; `NYISO/`
**121.1** = B6's zips (65.2) + B5's SOM PDFs and 2023–26 Gold Books (56.0);
`ERCOT/` + `MISO/` + `PJM-AS/` **95.7** = the rest of B5; the
`results/calibration/` long tail carries PR-3's 288 hourlies on top of the
prior per-bundle churn. By extension it is 6,322.1 MiB `*.parquet`, 559.9
`*.zip`, 155.0 `*.xlsx`, 141.5 `*.pdf` — the prunes' signature, where the
old floor was fragmented churn. **Prune-created superseded blobs are exactly
what a history rewrite would now reclaim** — that was the point of
quantifying the floor before and after: 922.3 MiB of it is prior churn,
≈ 6,416 MiB is the prunes' recovery archive.

*[ADDENDUM 2026-08-16 (BLOAT-B-8): the owner overrode AQ the next day and
executed the rewrite — run 31955205445 (run #18), SUCCESS, force-push landed
15:49 UTC, reclaiming this pool (7,254 blobs / 7,373.4 MiB at execution; pack
20.48 → 5.45 GiB on the runner). The paragraph below was this report's
warning about exactly that trade; it stands as written — the archive it
describes is now burned, the affected corpus READMEs carry honest
unrecoverability statements, and the durable record is
`docs/FINDING-history-rewrite-2026-08-16.md`. The run-#16 abort recorded
further below was diagnosed correctly: its 9 failing commits were
refs/pull-only, the workflow was patched to classify them, and all 9 survive
untouched.]*

**And it still doesn't change the NO-GO (Addendum AQ) — it inverts its
rationale from "pointless" to "harmful".** Pre-prune, the rewrite was refused
because it reclaimed ~1 % of the pack (everything was live at tip). Post-prune
the arithmetic is different — the removable pool is now **54 % of in-scope
logical history** (7,338.4 of 13,564.1 MiB) — but those superseded blobs
**are the archive**: every
corpus conversion's recovery contract (the README pin shas `971eaa3`,
`315a245`, `726f389d` and their `git restore --source=<pin>` commands, the
history-as-archive story that made B3's past-retention dailies and A2's
decaying-retention window safe to untrack) resolves into precisely the blobs
a rewrite would strip. Several of those payloads are already
irreplaceable-from-source (B3's OASIS dailies; the ERCOT-157-era raw columns
as MIS retention rolls). Executing the rewrite now would not be cleanup; it
would burn the archive the conversion class is contractually built on, and
convert "untracked but recoverable forever" into "gone".

**A real rewrite was in fact attempted — and the workflow's integrity guard
stopped it.** The artifact record shows run **`31907287115`** (run #16, head
`b26c13e`, 2026-08-15 20:39 UTC) executed with `dry_run=false` and the
confirm phrase supplied (its `Validate push token` step ran — that step is
conditioned on `dry_run == false` — and `Validate confirmation` passed by
skip). The strip and repack ran against the runner's mirror; then **`Verify
branch and tag integrity` FAILED: 9 commits cited in
`docs/governance/citation-tags.json` were pruned from the rewritten history**
("maps to itself, which does not exist" — cited evidence reachable only
outside the rewritten refs), and the job aborted with "No data was pushed.
The remote is untouched." The main-branch strict manifest itself verified
clean; the failure is the citation-integrity model doing its job. Two
consequences worth recording: (a) the remote history is confirmed intact —
this close-out's measurements and every pin-recovery command are unaffected;
(b) even setting AQ aside, the rewrite is *mechanically* blocked as the repo
stands: the workflow's own integrity model rejects it over cited evidence, and
that diagnosis (which cited commits, reachable from where) is a prerequisite
for any future owner decision to even be executable. This run is not
otherwise recorded in any program ledger — flagged to the PM/owner in the
release-plan §8 entry for this session.

---

## 6. Golden tier & G3 (status read at `04d1cf0` — no dispatch spent by this session)

Three facts, in order of surprise:

1. **The tier has its first-ever GREEN: run `31867650665`** (run #3,
   dispatched 2026-08-15 05:43 UTC at main `c447199` — four minutes after
   the PR-1/PR-2/PR-4 merges, i.e. the PR-2 post-merge dispatch duty window).
   Every step succeeded: sparse checkout, both provisioning steps —
   **including `curate_emissions.py --years 2023`, 2m05s, no OOM** — the
   serial pytest tier (2m53s), and the loud-failure guard. The tier reached
   and passed its own tests for the first time, and this green is direct
   §4.5/§4.6-style proof that no test opened anything PR-1/PR-2/PR-4
   removed. The B-5 sitting's "the tier has never been green" and the
   §2 G3-warning's premise were already stale hours after they were written;
   the ledger entries recording the deferral did not know about this run.
2. **The GOLDEN-TIER-FIX lane has NOT landed at HEAD.**
   `scripts/data/curate_emissions.py` was last touched 2026-08-12
   (`8fdb137`, its introduction) — the run above went green on the **stock**
   script, whose 3× whole-year materialization (salvaged report §4; PERF-A's
   10.04 GiB stock peak) is unchanged. No fix commit, no fix PR exists at
   `04d1cf0`, and no golden-tier dispatch has occurred after the lane was
   chartered (run #3 predates the director's dispatch of the lane by ~15
   hours). The lane's single authorized dispatch is **unspent**. One green
   against two identical OOM reds is a knife-edge margin, not a repealed
   diagnosis — the low-mem adoption is still the right fix.
3. **G3's evidence gate: materially opened, not yet closed.** G3 reads
   "`golden-data-tier.yml` manually dispatched once **post-prune** and green".
   Run #3 is post-PR-1/2/4 but **pre-PR-5 and pre-PR-3** — the two largest
   remaining prunes (−2,518.5 MiB in `data/raw`, −117.0 MiB in `results/`,
   both trees the tier checks out) landed after its head. So: the
   "tier-can-never-reach-its-tests" blocker is empirically gone, a pre-/
   mid-prune green baseline now EXISTS to attribute any future red against,
   and what remains for G3 is exactly one green dispatch at a
   post-`11b59ee`-or-later sha — which belongs to the GOLDEN-TIER-FIX lane,
   whose authorized dispatch this session deliberately did not spend.

**ADDENDUM (2026-08-16, added at the rebase onto `e1760bb6` for merge).**
Point 2's "unlanded" was true of `04d1cf0` and expired while this close-out
was in flight: the GOLDEN-TIER-FIX lane delivered late on 2026-08-15 — the
`curate_emissions.py` streaming-assembly fix merged (#3996; peak RSS
10.05 → 5.17 GiB on the tier's 2023 inputs, output verified
data-byte-identical for 2023 and 2024), and the single authorized dispatch
was SPENT and GREEN: run `31913648051`, on a base (`870c4c8`) carrying every
executed BLOAT-B prune (PR-1/2/3/4/5), loud-failure guard PASS, zero
data-missing skips, no corpus restored. That is exactly the post-PR-3/PR-5
green point 3 said was outstanding, so **G3's evidence gate is now fully
open** — recorded in the release-plan §8 ledger (the GOLDEN-TIER-FIX entry,
and the 2026-08-16 G1 declaration naming G3's proof mechanism restored).
Points 1–3 stand unedited above as the state measured at `04d1cf0`.

---

## 7. D-ledger (resuming `docs/refactor-consolidation-plan-2026-07.md` §9 via plan §9) — proposed final entries

- **BLOAT-1 — SPENT, propose CLOSE.** The G1 item-level review the plan
  existed for happened in-session at the BLOAT-B-5 sitting (2026-08-15), and
  every verdict is executed and verified above: **A2 SIGNED** (executed
  −1,846.9), **B1b SIGNED** (executed −111.7), **B3 SIGNED** (executed
  −559.9), **C-touchpoint rows VETOED — kept** (both bundles carry their
  `hourly/` at `04d1cf0`; revisit when the 2020–2022 ladder closes).
  Class-approved items executed under the standing decision-4 signature.
  Nothing on the §3–§7 list is unadjudicated (§4).
- **BLOAT-2 — STILL OPEN.** The Class-E retention rule text (§7 E2) awaits
  owner adoption; points 1–3 are already enforced mechanics, point 4's
  quarterly bundle-parity sweep is unbuilt (one PR on
  `check_registry_payload_parity.py` or `audit_keepers.py`, no data change).
- **BLOAT-3 — STILL OPEN, charter input re-measured.** The Stage-2 decision
  now reads over the `04d1cf0` numbers (§2): adjudication pool
  **4,008.7 MiB / 1,487 files**, takeable residual **≈ 3,311.9 MiB** after
  the §4.2/§4.7 keep-verdicts, full untrack → tip ≈ 3.0 GiB. Two facts from
  execution belong in the charter: PR-5/A2 was this decision **in miniature,
  signed and executed cleanly** — the same history-as-archive recovery story
  Stage 2 needs, exercised at 1.8 GiB scale without incident; and the run-#16
  rewrite attempt (§5) shows that story is now **load-bearing** — any
  Stage-2 execution further hardens the rewrite NO-GO, because it deepens
  the archive's dependence on history staying intact.

**Salvage-anticipated closures confirmed:** PR **#3954** closed unmerged
2026-08-15 20:01:21 UTC, PR **#3946** closed unmerged 20:01:33 UTC — both
after their durable parts landed via the salvage branch (#3976), exactly as
the salvage record said they could be.

---

## 8. Sanity checks — the prune set survived (all at `04d1cf0`, this session)

- `scripts/check_registry_payload_parity.py` — **green**: "registry/payload
  parity OK (70 runs checked, 0 known-unsynced tolerated)". 70 sidecars ↔ 70
  payloads, both directions.
- `scripts/audit_keepers.py --check` — **green**: "all checks passed — PASS:
  0 failure(s), 0 warning(s)".
- The six keeper bundles all carry their `hourly/` (caiso188_d1_micseam,
  ercot204_rule26_delete, miso148_basis_B, neiso93_envelope_A,
  nyiso133_cod_arm, pjm152_collapse_A — keeper ids re-read from
  `frontend/data/backcast/keepers/<ISO>.json` at HEAD), as do the two
  owner-vetoed touchpoint bundles and the pjm-162 keeper-candidate hold.
  The hourly corpus is exactly the 10 expected directories, nothing more.

---

## 9. Session provenance

- Docs-only: no data file, corpus, bundle, script, or workflow touched. The
  four files of this PR: this report, the release-plan §8 ledger entries, the
  bloat plan's §8/§9 close-out annotations, CHANGELOG.
- One workflow dispatch: `cleanup-large-blobs.yml` **dry run** `31912344135`
  (`dry_run=true`; confirm phrase never supplied). `golden-data-tier.yml` was
  **not** dispatched — its single authorized dispatch belongs to the
  GOLDEN-TIER-FIX lane (§6).
- All measurements are tree-only reads of `04d1cf0` under
  `GIT_NO_LAZY_FETCH=1`; the working tree was used only to run the two §8
  checker scripts, which read committed files.
- This PR touches only `docs/**` and `CHANGELOG.md` — outside `ci.yml`'s
  `pull_request` paths filter, so zero check runs is by design. Rule 27
  blob-verification performed after push on every ≥300-line file.
