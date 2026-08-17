# Bloat Removal Plan — 2026-08 (BLOAT-A deliverable)

**Program:** Model Audit & Release-Finalization, WS6 · BLOAT
(`docs/model-audit-release-plan-2026-08.md` §3/WS6, prompt §7.5).
**Session:** BLOAT-A, read-only inventory → itemized plan. **No deletion, move,
or conversion was executed in this session** — execution is BLOAT-B, gated on G2
plus the owner-signed list below (G1 item-level veto retained, plan §6 decision 4).
**Base commit measured:** `f2de3b0a83a0515567720967642e4ae94378c6d3`
(origin/main, 2026-08-14). All sizes are **MiB of logical blob bytes in the git
tree at that commit** (method: `git ls-tree -r -l`, tree-only reads), so they are
directly comparable to the 2026-08-13 Trees-API baseline at `066abeed` after a
MB↔MiB units note (§2).
**Branch note:** the WS6 prompt names `claude/bloat-inventory-2026-08`; this
session's harness-designated branch is `claude/bloat-inventory-removal-plan-zonu2l`
and the deliverable lands there.

**Inherited charter honoured (2026-08-13):** the FFR desk withdrew RAW-UNTRACK
into this workstream (`ffr-owner-sitting-2026-08-02.md` AS.5;
`forecast-readiness-prompt-pack-2026-07.md` §0as — never re-dispatched). The
three inherited inputs — `docs/FINDING-rewrite-prep-2026-08-11.md` §8 (GO half),
`docs/fast-clone.md` (#3909), §0ar-3's pre-merge checklist — are reconciled with
the per-corpus candidates in §1, which is this plan's charter-mandated first
section.

**Standing constraints restated:**

- **History rewrite is NO-GO** (owner decision, REWRITE-PREP Addendum AQ
  2026-08-13; FINDING-rewrite-prep §8). Nothing below rewrites history. Scope is
  tip prune + corpus conversion only.
  *[SUPERSEDED 2026-08-16 — after this plan's execution completed, the owner
  overrode AQ and executed the rewrite: `cleanup-large-blobs.yml` run
  31955205445, force-push landed 15:49 UTC. This plan's own work was untouched
  (the prunes are tip-state), but the conversion class's restore-from-pin
  recovery contracts (§3–§4 below) were invalidated — the pins no longer
  resolve and the superseded blobs are stripped. Record:
  `docs/FINDING-history-rewrite-2026-08-16.md`.]*
- `cleanup-large-blobs.yml` may be run **as a dry run only** (`dry_run=true`
  input verified present in the workflow; the real-run `confirm=REWRITE-HISTORY`
  phrase is never to be supplied). Planned in §8 as the BLOAT-B close-out
  quantification, never an execution. *[Overtaken with the AQ supersession
  above: real runs #16 (aborted at verify) and #18 (executed) followed.]*
- Owner pre-approval (release plan §6 decision 4): the
  gitignore+README+SHA256+fetch-script conversion **class** is approved for
  corpora **proven re-fetchable** (per-item evidence below); irreplaceable
  corpora fall back to ERCOT-157-style in-place slimming. Each item below is
  marked **class-approved** or **needs-sign-off** accordingly.

---

## 1. The inherited question first: does wholesale `data/raw` untracking subsume the per-corpus conversions?

**Answer: No — it sequences after them; it cannot subsume them.** Wholesale
untracking (FINDING-rewrite-prep §8 GO half: `git rm -r --cached data/raw` +
`.gitignore`, metadata-only commit, history kept) and per-corpus conversion share
the *same recovery story* — history is kept, so every untracked byte remains
fetchable forever from the promisor remote at the last-tracked sha
(`git restore --source=<pin> -- <path>`, the §0ar-3 recovery command). The
difference is not recoverability; it is **what must keep working at tip**, and
three measured facts pin that:

1. **`golden-data-tier.yml` pins 1,500.0 MiB / 1,038 files of `data/raw` at
   tip** (measured this session by evaluating the workflow's sparse-checkout
   globs with gitignore semantics against the `f2de3b0` tree — the result
   matches the workflow's own "~1.5 GB" comment exactly, validating the method).
   CI sparse-checks out **the PR/main ref**, so every glob-matched path must
   stay tracked at tip or the tier must be re-engineered to restore data from a
   pinned sha inside the job. That re-engineering is possible but it modifies
   the repo's **authoritative data-dependency guard** (release plan: "the
   authoritative data-dependency inventory") — an owner decision, not cleanup.
2. **Forward intake needs a committed home.** Several corpora are committed
   *because their sources expire*: ERCOT MIS publications age out on a rolling
   window measured in this repo (SCED pubs ≤ 2024-03-23 already unreachable —
   `ercot-sced-2024-2025-reupload-2026-08.md`; the 2_DAY AS disclosures are
   ~31-day), and CAISO OASIS retention is a measured, moving ~39-month boundary
   (2023-04-22 as of 2026-08-04 — `fetch_caiso_oasis.py` docstring). After a
   wholesale untrack, a *new* irreplaceable snapshot would have nowhere durable
   to land. The per-corpus pattern keeps that contract: README + SHA256SUMS
   stay tracked; payloads are per-corpus decisions.
3. **The candidate classes and the golden tier don't overlap where it counts.**
   `data/raw` at tip decomposes exactly (§2): golden-tier 1,500.0 MiB +
   this plan's candidate classes 4,705.1 MiB + residual 3,561.6 MiB. The
   candidate classes are prunable **without touching a single CI contract**
   (two candidate groups sit *inside* golden-listed directories but are opened
   by no test — §4.5/§4.6 — and sparse checkout tolerates their absence; the
   tier's loud-failure guard plus the G3 post-prune dispatch is the proof
   mechanism).

**Sequencing (the reconciliation):**

- **Stage 1 — this plan's itemized classes (BLOAT-B, after G2).** Per-corpus
  conversions + in-place slims + results/script/dashboard hygiene. Recovers
  **≈ 1.9–2.0 GiB on class-approved items alone, ≈ 4.0 GiB with the
  needs-sign-off items** (§8 accounting), taking the tip from 10,080 MiB to
  ≈ 8.1 GiB (conservative) / ≈ 6.1 GiB (full sign-off). Zero workflow edits,
  zero test edits, zero contract rewrites (one CLAUDE.md touch, §8/PR-2).
- **Stage 2 — wholesale untrack of the residual (standing owner option, not
  scheduled by this plan).** The measured residual is **3,561.6 MiB / 1,444
  files** (§2 table — CAMPD unit-level non-2023, ercot-AS/CAISO-AS bulk,
  ercot-hsl non-golden, iso-specific-transmission, eia-930 bulk,
  storage-as-awards, …). Untracking it takes the tip to ≈ 2.5 GiB. It requires
  the full §0ar-3 pre-merge checklist (workflows walk, integrity-guard label,
  skip-when-absent test verification, CLAUDE.md data-contract + Git & Pushing
  rewrite, pinned-sha recovery documentation, `hydrate_data.py` pin support) —
  and it *still* leaves Stage-1's items to do, because the golden-tier paths
  and irreplaceable-forward corpora are exactly what it cannot take.
- **Stage 2′ — golden-tier retarget (deliberately out of scope).** Only if the
  owner ever re-engineers `golden-data-tier.yml` to hydrate from a pin does the
  final 1,500 MiB leave the tip (floor ≈ 1.0 GiB incl. non-data trees). Not
  recommended while the tier is the release program's G3 proof.

Why Stage 1 first (and not the one-shot wholesale move): it is the signed path
(decision 4), it needs no CI/tooling re-engineering, it preserves per-corpus
provenance manifests that a wholesale move would not create, and it de-risks
Stage 2 (after Stage 1, the residual is a smaller, better-understood set with
its own follow-on evidence pointers, §4.8). The §0ar-3 checklist is applied
where it bites in Stage 1 (§8 per-PR duties) and carried forward whole for
Stage 2.

**Effect on `docs/fast-clone.md` profiles:** conversion shrinks hydration, it
does not break it — converted payloads leave the profiles (attribution derives
from the tree at HEAD), and re-derivation sessions restore them from the pinned
sha recorded in each corpus README. The `ercot` profile drops from ~5.9 GB
packed toward ~2–3 GB after Stage 1's SCED items.

---

## 2. Measured baseline at `f2de3b0` (re-verification of the 2026-08-13 numbers)

Method: full `git ls-tree -r -l` of the tip tree (11,127 blobs), tree-only reads.
The session's working tree drifts from fresh main by 7,361 files (a checkout
crashed before the session started), so **no measurement or evidence in this
plan reads the working tree** — everything is `git show`/`git grep`/`ls-tree`
against `f2de3b0`. (Two exceptions, both content-stable: the four NYISO zip
listings and nothing else.)

| Quantity | 2026-08-13 baseline @ `066abeed` (Trees API) | This session @ `f2de3b0` | Reconciliation |
|---|---:|---:|---|
| Tip total | 10,531 MB | **10,080.0 MiB** = 10,569 MB | Units: baseline is decimal MB. 10,569 vs 10,531 = net +38 MB from the ~200-file delta since (76 `results/calibration` adds incl. the ercot-193 pair, 14 probe adds, 7−6 payload churn, hindcast + docs adds) — verified by `git diff-tree 066abeed f2de3b0` |
| Files | 11,011 | **11,127** | +116, same delta |
| Files > 512 KB | 2,084 | **2,330** (> 524,288 B) | Threshold/units definition + the ~24 new hourly parquets; non-material to any item below |
| `data/` | 10,222 MB | **9,767.1 MiB** = 10,242 MB | Matches in decimal MB |
| `results/` | 159 MB | **169.0 MiB** | Grew by the ercot-193/miso-155/neiso-93 adds since baseline |
| `frontend/data/backcast/runs/` | 73 MB / 66 payloads | **70.1 MiB / 66** | Matches (2 pruned + 2 added since July figures) |

**The load-bearing decomposition of `data/raw` (9,766.7 MiB / 4,722 files):**

| Block | MiB | Files | Meaning |
|---|---:|---:|---|
| Golden-tier-matched (sparse globs of `golden-data-tier.yml`, gitignore semantics) | **1,500.0** | 1,038 | KEEP-REQUIRED at tip while the tier checks out the PR ref (§1 fact 1) |
| This plan's candidate classes (A + B, non-golden) | **4,705.1** | 2,240 | Itemized in §3–§4 |
| Residual (neither) | **3,561.6** | 1,444 | Stage-2 territory; mapped in §4.8 |

Residual top constituents (for Stage-2 sizing, no action in this plan):
`campd-unit-level` non-2023 692.6 · `ercot-AS` non-golden 598.5 · `CAISO-AS`
535.8 · `ercot-hsl` non-golden 428.3 · `iso-specific-transmission` 365.8 ·
`data/raw/ercot` misc 301.0 · `eia-930` bulk 190.3 · `storage-as-awards` 165.2 ·
`lmp-data` (MISO/PJM non-golden) 143.5 · `PJM` 107.1 · smaller tails ~33.

Other verified anchors: `results/calibration` 141.3 MiB / 1,362 files (of which
904 loose FINDING/ASSESSMENT/DIAGNOSIS/… records = 15.4 MiB — keep-required);
`results/hindcast` 20.1 MiB (forecast namespace, rule 15 — keep);
`results/regression-goldens` present (0.2 MiB — keep); `scope2-lce-portfolio`
7.0 MiB (charter: not worth it — untouched); `.gitignore` currently 752 lines
(the 818 in the charter predates the 08-13 edit); root-level LMP zips: **none at
tip** (D-4 executed — §9).

---

## 3. Class A — `data/raw/ercot/SCED` (3,258.0 MiB, 1,025 files)

**Composition (measured):** 1,023 publication-month shards + `README.md`
(no SHA256SUMS at tip — must be created before any conversion):

| Window | Pubs | MiB | Files | Provenance (README + `ercot-sced-2024-2025-reupload-2026-08.md`) |
|---|---|---:|---:|---|
| ERCOT-157 window | 2023-03 .. 2024-03 | 916.5 | 323 | 2026-08-03 **owner re-upload** (delivery-2023 + Jan-24 bleed). The original 2026-07-21 upload was purged by the 2026-07-22 large-blob history rewrite and restored by hand |
| ercot-183 window | 2024-04 .. 2026-02 | 2,180.3 | 673 | Fetched 2026-08-09 from the free MIS path by `scripts/data/fetch_ercot_sced_corpus_shards.py` (owner card D4) |
| RTC+B quarantine | `rtcb-format-2026/` | 161.2 | 27 | Format-break shards, readable only via `sced_rtcb_adapter.py`; **subdirectory is load-bearing, never flattened** (README) |

**Consumers (grep `src/ scripts/ tests/`, tree-scoped):** derive-time only —
`derive_ercot_sced_offer_wall.py`, `derive_ercot_faststart_pool.py`,
`derive_ercot_energy_online_capability.py`, `derive_coal_perplant_offer.py`,
`derive_ercot_storage_rt_offer_surface.py`, `scripts/lib/sced_rtcb_adapter.py`,
`sced_corpus_instruments`, plus frozen probes and the two fetch scripts. **No
solve-time or test-time consumer**; the golden tier's sparse list does not
include `data/raw/ercot/SCED` (verified against the glob set). Solves read the
committed derived surfaces; the corpus is needed only to re-derive under rule 23
`[R-FROZEN-DERIVE]` (source-data updates only).

**Re-fetchability (measured, split):** publications ≤ 2024-03-23 are **already
unreachable** on the free MIS path (reupload handoff §2: delivery 2024-01-10..23
lost because pubs 2024-03-10..23 aged out mid-fetch; Jan 24–31 fetched "at the
retention edge"). Publications ≥ 2024-03-24 were re-fetchable as of 2026-08-09
— a **rolling ~28-month window that shrinks daily**, not a stable archive. So
the charter's "~31-day retention" caution is directionally right for this
corpus class: the 2023 window is irreplaceable-from-source **today**, and the
2024+ window becomes so continuously.

**Slim status (verified by parquet schema read from the git blobs):**
`2023-07.part0010` = **187 columns**, `2025-06.part0010` = **188 columns** —
the raw all-string CSV copy. The ERCOT-157 column projection (owner-ordered
2026-07-22, `scripts/data/slim_ercot_dam_disclosure.py`, whose docstring is the
consumer-column registry; 315 shards 896 → 490 MB verified lossless by
byte-identical re-derivation of every consumer artifact) **is not applied at
tip** — the slim blobs were purged with the July-22 rewrite and the re-uploads
restored raw bytes. The slimming headroom therefore still exists, for **both**
windows.

**Items:**

| ID | Action | Est. recovery | Risk | Status |
|---|---|---:|---|---|
| **A1** | In-place slim of all 1,023 shards (+ the `rtcb-format-2026/` 27 via the adapter's column contract) with `slim_ercot_dam_disclosure.py`; write `SHA256SUMS.txt` **before and after**; re-derive every consumer artifact and byte-compare (the ERCOT-157 acceptance protocol) | **≈ −1,450 MiB** (precedent ratio 490/896 = 0.547 applied to 3,258; verify at execution) | Low (values untouched; column projection + zstd-15; dropped columns re-fetchable *within retention* and always via history) | **class-approved** (decision-4 fallback, precedent executed once already) |
| **A2** | Conversion of the 2024+ window (post-slim ≈ 1,280 MiB incl. rtcb): gitignore payload globs, keep README + SHA256SUMS, record the last-tracked sha in the README | −≈ 1,280 MiB further | Medium: "re-fetchable" decays; the honest recovery story is history-as-archive, same as Stage 2 | **needs-sign-off** (recommend deferring A2 into the Stage-2 decision — it is the same call in miniature) |
| — | The ERCOT-157 window (2023) is **never converted**: irreplaceable-from-source, restored by hand once already. It is slimmed under A1 and stays tracked | — | — | recorded |

**A2 EXECUTED 2026-08-15 (BLOAT-B-5, PR #3978) — owner-SIGNED at the
in-session G1 item card** *(the defer-to-Stage-2 recommendation above was
declined)*: top-level publications 2024-04..2026-02 (673 shards) + the whole
`rtcb-format-2026/` quarantine (27 parts) untracked at tip — measured
**−1,846.9 MiB** of post-slim bytes (above the ≈1,280 estimate because B-1's
slim recovered 21.3 % rather than the SNAPPY-era 45 %, leaving more bytes for
this conversion). The ERCOT-157 window (323 shards) stays tracked exactly as
the table's third row records; `README.md` + post-slim `SHA256SUMS.txt` stay
tracked (pin sha + whole-window and single-shard restore commands in the
corpus README), and a tracked `rtcb-format-2026/README.md` stub keeps the
load-bearing quarantine layout. Execution record: §8 PR-5.

**BLOAT-B execution notes for A1:** the rewrite touches ~1.75 GiB of blobs, far
beyond a single push. Chunk by publication month (~35 commits of 25–90 MB
packs, each within the measured `git push` envelope), blob-verify per chunk
(Git & Pushing §4), never a placeholder state in between (`[R-PUSH]` applies in
spirit — these are data files, but the no-partial-overwrite discipline is the
same). If proxy throughput makes even chunked pushes unreliable, hand the
branch to the owner for the push leg — never a CI job (CLAUDE.md GitHub-Actions
rule).

---

## 4. Class B — loose corpora (itemized per corpus)

### 4.1 The four loose `60_DAY_SCED_DISCLOSURE_*` probe extracts — the repo's 4 largest files (208.6 MiB)

`60d_SCED_Gen_Resource_Data_2025_ercot86_tail_days.parquet` 63.5 ·
`…_2024_ercot74_tail_days.parquet` 55.6 · `…_2025_ercot75_control_days.parquet`
52.8 · `…_2024_ercot75_control_days.parquet` 36.7.

**Consumers:** `scripts/data/derive_sced_coal_uppertail.py` — a **standing
rule-23 derive** — loads subset `2025_ercot86_tail_days` (output
`offer_curve_sced_coal_uppertail.json`, committed). The other three are read
only by frozen probes (`_ercot74_sced_headroom.py`, `_ercot75_control_gate.py`,
+ downstream probe census scripts). Re-fetch: same NP3-965 instrument as Class A
(`fetch_ercot_60day_sced_gen_resource.py --delivery-range`, the SCED-CT
precedent) — delivery-2024/2025 windows currently inside the rolling retention,
decaying.

**Items:** **B1a (class-approved):** include all four in the A1 slim pass
(same layout/registry; est. **−≈ 95 MiB** at the precedent ratio; verify —
extracts may already be column-subset, in which case the yield shrinks and the
item self-cancels at measurement). **B1b (needs-sign-off):** convert the three
probe-only files (145.1 MiB pre-slim) under history-as-archive; keep
`ercot86_tail_days` tracked while `derive_sced_coal_uppertail.py` is standing.

**B1b EXECUTED 2026-08-15 (BLOAT-B-5, PR #3978) — owner-SIGNED**: the three
probe-only extracts untracked, measured **−111.7 MiB** post-slim (B1a's slim
had already banked the projection half). `ercot86_tail_days` stays tracked for
the standing derive; bytes pinned by the tracked
`SHA256SUMS-60day-sced-extracts.txt` (post-slim at head, pre-slim raw at
`971eaa3`); pin sha, restore command and the decaying NP3-965 re-fetch route
in `data/raw/ercot/README.md`. Execution record: §8 PR-5.

### 4.2 The 21 loose `60_DAY_DAM_DISCLOSURE_*` parquets (244.1 MiB) — **verified KEEP, removed from the candidate list**

By year: 2023 49.8/4 · 2024 60.5/5 · 2025 73.2/7 · 2026 60.5/5 (incl. 2 ESR).
Schema read: **37 columns** — these already carry the ERCOT-157 treatment (the
slim script's DAM section, "KEEP 38"). Consumers: 8+ standing derives
(`build_ercot_as_2023.py`, `build_ercot_as_by_restype_from_60day.py`,
`build_ercot_dam_as_mcpc.py`, `derive_ct_offer_surface.py`,
`derive_dam_offer_hrmults.py`, `derive_ercot_offer_midcurve.py`,
`derive_ercot_storage_as_products.py`, …). The 2023 quarters' publications have
aged out of MIS (irreplaceable). Already-slimmed + actively consumed +
partially irreplaceable ⇒ **no action**; the 2024+ subset re-enters only with
Stage 2.

### 4.3 `data/raw/lmp-data/CAISO` (586.6 MiB, 69 files)

Composition: **8 hourly aggregate CSVs** (`CAISO_dam_hourly_*`,
`CAISO_rtm_hourly_*`, 23.0 MiB) — **golden-tier-listed, KEEP-REQUIRED**, the
product every consumer reads (`derive_caiso_loss_surface.py`, clean-lmp
curation); **60 raw OASIS SingleZip daily archives** (`20230101_20230101_DAM_
LMP_GRP_N_N_v12_csv.zip`, `…RTM_LMP_GRP_01..07_N_v3_csv.zip`, ~Jan 1–25 2023,
559.9 MiB); and **1 junk-named file** `{28377242-…}.pdf, attachment` (3.7 MiB).

**Evidence:** `postprocess_oasis_downloads.py`'s docstring states the corpus
design — "the raw OASIS window CSVs are bulky … the repo keeps tidy hourly
aggregates instead and **the raw files are staged out**". The committed dailies
contradict their own corpus contract (they were committed during the
caiso-163…168 nodal-decomposition lanes; only frozen probes reference them).
**Re-fetchability: NO** — OASIS retention is a measured moving ~39-month
boundary, at **2023-04-22 as of 2026-08-04** (`fetch_caiso_oasis.py`), so the
January-2023 trade dates are gone from the source.

**Item B3 (needs-sign-off, −563.6 MiB):** untrack the 60 dailies + the junk
file under **history-as-archive** (record the pin sha in a corpus README;
gitignore the SingleZip pattern so future OASIS pulls stay out per the corpus's
own design). Not class-approved because decision 4's conversion class requires
*proven re-fetchability*, which these demonstrably lack; the fallback (in-place
slim) does not apply to already-compressed zips. This is the cleanest concrete
instance of the Stage-2 recovery story and a good owner test-case for it. The
`{GUID}.pdf, attachment` file is a hygiene sub-item (identify, then delete or
rename to convention) — **class-approved** at its 3.7 MiB.

**B3 EXECUTED 2026-08-15 (BLOAT-B-5, PR #3978) — owner-SIGNED**: the 60
dailies untracked, **−559.9 MiB** (the GUID hygiene sub-item had already
executed in PR-2 #3956). New tracked `SHA256SUMS.txt` — every zip's disk bytes
tree-sha-verified against HEAD before hashing — plus a corpus `README.md` with
the source table, the past-retention statement (history-as-archive is the only
recovery), pin sha and restore command; `.gitignore` gains the
date-range-prefixed SingleZip glob so future OASIS pulls stay out per the
corpus's own staged-out design. Execution record: §8 PR-5.

### 4.4 `data/raw/caiso-dam-outages` (163.7 MiB: 1,094 xlsx = 155.0 + parquet/README/patch/missing-days 8.7)

**Evidence:** the consolidated `caiso-dam-outage-windows.parquet` **exists at
tip and supersedes the dailies for every runtime consumer** —
`src/market_sim/data/caiso_outages.py` reads only the parquet (verified lines
45/87); `scenarios.py`, `paths.py`, `tests/iso/caiso/test_caiso_dam_outages.py`
likewise. The 1,094 `daily/cnog-YYYYMMDD.xlsx` are read only by
`curate_caiso_dam_outages.py` (re-derivation) and the crosswalk derives.
**Re-fetch (proven):** `fetch_caiso_dam_outages.py [START END]` — resumable,
against the documented CAISO library URL pattern; series start 2021-06-18;
known publication gaps already recorded in `missing-days.txt`. Not
golden-tier-listed. The backcast overlay consumes the parquet, which stays.

**Item B4 (class-approved, −155.0 MiB):** the textbook conversion — gitignore
`daily/*.xlsx`, keep README + `caiso-dam-outage-windows.parquet` +
`missing-days.txt` + `loader-wiring.patch`, add `SHA256SUMS.txt` over the
dailies as the provenance record, record the pin sha. Risk note for the README:
the CAISO library's retention is observed, not contractual — history-as-archive
is the backstop, and `missing-days.txt` plus the SHA manifest make a future
re-fetch verifiable.

### 4.5 The 34 committed PDFs (144.5 MiB)

Per-directory, with consumers (grep-verified):

| Group | Files | MiB | Consumers | Re-fetch evidence | Verdict |
|---|---:|---:|---|---|---|
| `data/raw/ERCOT/` SOM reports 2019–2025 | 7 | 33.7 | None parsed (hand-read; SOM-derived thresholds cite `docs/parameter-citations.md`) | Potomac Economics public archive | **convert** (class-approved) |
| `data/raw/MISO/` SOM + IMM quarterlies | 7 | 31.0 | None parsed | Potomac/MISO public archive | **convert** (class-approved) |
| `data/raw/NYISO/` SOM reports ×5 | 5 | 44.9 | `curate_nyiso_som_hub_fuel_annual.py` parses Figure A-6 tables | Potomac/NYISO public archive | **convert** (class-approved, fetch instructions mandatory in README since a curate step parses them) |
| `data/raw/NYISO/` Gold Books 2023–2026 | 4 | 11.1 | `build_nyiso_scr_edrp.py` parses ("the immutable PDFs live at data/raw/NYISO/") | NYISO public archive | **convert** (class-approved, same fetch-instruction duty) |
| `data/raw/PJM-AS/` Manual 11 revisions + E-3 + fact sheet | 5 | 17.2 | None parsed (citation sources) | PJM manual revision archive | **convert** (class-approved) |
| `data/raw/NYISO-AS/…/locational-reserve-requirements/` | 3 | 0.5 | `fetch_nyiso_lrr_pdfs.py` + curation; two are **Wayback snapshots** (2020/2021) | Wayback captures are point-in-time | **KEEP** (irreplaceable snapshots, immaterial size) |
| `data/raw/capacity-market/…/caiso/` | 2 | 2.6 | `curate_caiso_lcr.py` / `curate_caiso_mic.py` parse | CPUC/CAISO publications | **KEEP** (parsed inputs, small; optional convert later) |
| `lmp-data/CAISO/{GUID}.pdf, attachment` | 1 | 3.7 | None | n/a (junk-named) | hygiene item under B3 |

**Item B5 (class-approved, −≈ 137.9 MiB):** convert the 28 publication PDFs
(first five rows): gitignore the payloads, add per-corpus `SOURCES.md` (or
README section) with title→URL table + `SHA256SUMS.txt`, keep the 3+2 parsed
snapshots/small inputs tracked. Note: 14 of the 28 sit inside golden-tier
sparse **directories** (`NYISO/`, `PJM-AS/`) — materialized in CI but opened by
no test; the post-prune tier dispatch (G3) is the proof, and shrinking those
directories reduces CI checkout weight.

### 4.6 The four `data/raw/NYISO/nyiso load reports N.zip` (65.2 MiB)

**Evidence:** zero consumers (line-level grep across `src/ scripts/ tests/`
for the filenames, "load report", and any zip-open under `data/raw/NYISO` —
the directory's consumed contents are fuel-mix csv.gz, interface-flows,
ATC_TTC.zip, Gold Books/SOM PDFs, all separately referenced). Zip listings show
the standard NYISO MIS monthly archive products — `YYYYMM01pal_csv.zip`,
`…palIntegrated_csv.zip`, `…zonalBidLoad_csv.zip` — i.e. the permanently
archived public series at `mis.nyiso.com` (P-58 family); the derived
`zone-specific-demand/NYISO_load_actuals_<year>.csv` the model actually reads
is golden-listed and stays. Inside the golden-listed `NYISO/` directory but
opened by no test (same proof mechanism as §4.5). Charter sized them ~96 MB;
measured 65.2 MiB.

**Item B6 (class-approved, −65.2 MiB):** conversion — gitignore the four zips,
README section with the `mis.nyiso.com` URL pattern per month-product +
`SHA256SUMS.txt`, pin sha recorded. (No fetch script exists; the README URL
table + a trivial `curl` loop documented inline satisfies the pattern — or
BLOAT-B adds `fetch_nyiso_load_reports.py` if the owner prefers scripts
everywhere.)

### 4.7 Discovered adjacent items — verified KEEP (recorded so BLOAT-B doesn't re-litigate)

- `2_DAY_SCED_AS_DISCLOSURE_*_2026*.parquet` (15 files, 199.8 MiB) and
  `DAMASAGGNP419_2025_Jan-Nov.parquet` (23.2 MiB): holdout-equivalency intakes
  (`docs/holdout-data-equivalency-register-2026-07.md`) preserving ~31-day-
  retention MIS products for the H1-2026 crossover/locked-test future —
  **irreplaceable snapshots, KEEP**. Already column-projected (4-col verified).
  Optional zstd recompression is possible but low-yield — not itemized.
- `data/raw/ercot/cdr.*.zip` (100 files, 39.5 MiB; 2018 13.0 / 2019 14.6 /
  2020 0.5 / 2026 11.4): holdout-tier load inputs (rule 22: inputs applied
  consistently across all years). The 2018 subset (13.0 MiB) covers the
  **dropped** span — flagged as optional owner hygiene, immaterial; default
  KEEP.
- `data/raw/ercot-AS` 60d files for 2018/2019/2022: holdout-tier inputs, KEEP
  (golden-listed subset already carved out by globs).

### 4.8 Follow-on conversion candidates surfaced by the residual map (Stage-2 preview, NOT itemized)

For the Stage-2 decision, the largest residual constituents with *prima facie*
re-fetch stories: `campd-unit-level` non-2023 (692.6 — CAMPD API),
`eia-930` bulk (190.3 — EIA API), `CAISO-AS` (535.8 — OASIS, **retention
decays**), `ercot-AS` non-golden (598.5 — MIS, mixed retention),
`ercot-hsl` non-golden (428.3), `storage-as-awards` (165.2),
`iso-specific-transmission` (365.8 — mixed derived/source). Each needs the same
per-item evidence pass this plan performed before any of it moves; none is
part of BLOAT-B under this plan.

---

## 5. Class C — `results/calibration` (141.3 MiB)

Keeper set re-verified from `frontend/data/backcast/keepers/<ISO>.json` at
`f2de3b0`: `2026-08-09-caiso-188-d1-micseam` / `2026-08-12-run192-arm-coal-peak`
/ `2026-08-09-miso-148-basis-aware` / `2026-08-06-neiso-87-control` /
`2026-08-08-nyiso-132-cf-arm` / `2026-08-04-pjm-152-collapse` — bundle dirs
`caiso188_d1_micseam`, `ercot192_arm_B`, `miso148_basis_B`, `neiso87_control_A`,
`nyiso132_cf_arm`, `pjm152_collapse_A`. **Keeper bundles and their hourly
sidecars are byte-irreproducible and are not listed anywhere below** (rule 15).

### 5.1 Hourly parquets of non-keeper bundles — 92.9 MiB total

Per rule 15, hourly sidecars are a **keeper** obligation; non-keeper bundles
need only their slim files (meta/run_config/scores/README — the A/B evidence
the charter's keep-required list protects) plus their dashboard payload. Item:
delete `hourly/` of non-keeper bundles, keep every slim file. `[R-DELETE]`
applies — deleted means deleted.

| Bundle | hourly MiB | Disposition | Evidence note |
|---|---:|---|---|
| `ercot188_topfine_arm_B` / `_ctl_A` | 9.8 | prune | superseded by ercot-191/192 lineage |
| `ercot191_dam_rederive_regate` | 4.9 | prune | superseded by ercot-192 keeper |
| `ercot192_ctl_A` | 4.9 | prune hourly, keep slim | keeper's control twin = A/B evidence |
| `caiso184_c0_control` / `_c1_lpbasis` | 8.0 | prune | superseded by caiso-188 |
| `caiso188_d0_control` | 4.9 | prune hourly, keep slim | keeper's control twin |
| `miso148_basis_A` | 4.8 | prune hourly, keep slim | keeper's control twin |
| `miso151_surface_A` / `_B` | 9.5 | prune | adjudicated (DECISION-miso151-item9 …) |
| `nyiso132_cf_control` | 3.6 | prune hourly, keep slim | keeper's control twin |
| `pjm158_ctl_A` / `_novirt_B` | 12.3 | prune | adjudicated; the run's record is its payload + slim files (cited in CLAUDE.md rule 22 as the guard-(b) example — the citation reads the verdict, not the hourlies) |
| **subtotal — class-approved now** | **62.7** | | |
| `ercot193_arm_soc` / `_ctl_nosoc` | 9.8 | **HOLD** | L-SCAR lane active (ercot-197 sitting record 2026-08-14: L-2 chartered) — prune only after that lane adjudicates |
| `miso155_p0_C` | 6.2 | **HOLD — verify** | `tests/test_miso155_p0_commitment_sidecar.py` (added 2026-08-13) reads this bundle's sidecar; prune nothing a committed test opens — resolve the test's fixture path first |
| `nyiso133_cod_arm` / `_control` | 7.2 | **HOLD** | nyiso-134 2022-readiness assessment dated 2026-08-14 — lane open |
| **subtotal — hold until lane adjudication** | **23.2** | | |
| `neiso86_2022_corrected` | 3.7 | **VETOED 2026-08-15 (owner) — keep** | 2022 touchpoint evidence — the rule-22 touchpoint loop is iterative and may re-read it. Vetoed at the BLOAT-B-5 G1 item card while both 2022 loops are LIVE (pjm-2022 root-cause #3939/#3951 merged 08-14/15; neiso-92/93 envelope repair); revisit when the 2020–2022 ladder closes |
| `pjm2022_touchpoint` | 2.2 | **VETOED 2026-08-15 (owner) — keep** | same |
| **subtotal — owner call: VETOED, kept** | **5.9** | | |

### EXECUTED 2026-08-15 (PR-3) — re-derived at `11b59ee`, 24 bundles / 288 files / −117.01 MiB

Shipped as PR #3982 (branch `claude/bloat-b3-hourly-prune-xt1i22`, label
`intentional-shrink`), re-deriving the whole table at execution HEAD per the §8
recipe. By execution the hourly corpus had grown to **34 dirs / 158.4 MiB**
against the table's 19 rows (BLOAT-B-6's interim census: 30 / 137.3), keepers
had moved in three ISOs, and main moved twice mid-session (`726f389` →
`b26c13e` → `11b59ee`: the nyiso-135 promotion #3977 and BLOAT-B-5 #3978/#3979)
— the list was re-derived after each move. `hourly/` only; every slim file,
payload and sidecar untouched.

**Pruned (24):** ERCOT ×9 — `ercot188_topfine_{arm_B,ctl_A}`,
`ercot191_dam_rederive_regate`, `ercot192_{arm_B,ctl_A}`,
`ercot193_{arm_soc,ctl_nosoc}`, `ercot202_{plantphysics_B,graincontrol_A}`
(44.37 MiB) · CAISO ×3 — `caiso184_{c0_control,c1_lpbasis}`,
`caiso188_d0_control` (12.80) · MISO ×4 — `miso148_basis_A`,
`miso151_surface_{A,B}`, `miso155_p0_C` (20.45) · NEISO ×1 —
`neiso87_control_A` (3.65) · NYISO ×3 — `nyiso132_{cf_arm,cf_control}`,
`nyiso133_cod_control` (10.77) · PJM ×4 — `pjm158_{ctl_A,novirt_B}`,
`pjm161_{ctl_A,evcap_B}` (24.97).

**The three HOLDs all lifted on lane state:** `ercot193_*` — L-SCAR CLOSED-OUT
(cycle-11 sitting record, PR #3960: L-1 dead at V0, L-2 Phase-0 STOP
`ercot-201`, regime card WAIT-FOR-DATA, queue empty). `miso155_p0_C` — the
committed test (now `tests/iso/miso/test_miso155_p0_commitment_sidecar.py`) is
fully synthetic at HEAD and opens nothing under `results/calibration`; miso-155
closed the lane's blocker with the P0 instrument "consumed by nothing
downstream" (the open owner question — P0 sidecar in the committed bundle SPEC
— concerns future bundles, not this bundle's retention; FINDING/PREREG/probe
records all kept). `nyiso133_*` — nyiso-134 concluded (2022 touchpoint REFUSED
on data readiness, no LP), then the nyiso-135 promotion made `nyiso133_cod_arm`
the KEEPER: the arm KEEPS its hourly (rule 15) and only the control twin
pruned.

**Keeper churn absorbed (immunity test re-run per demotion):** executed keeper
set = `ercot204_rule26_delete` / `caiso188_d1_micseam` / `miso148_basis_B` /
`neiso93_envelope_A` / `nyiso133_cod_arm` / `pjm152_collapse_A`. Demoted and
pruned: `ercot192_arm_B` and the `ercot202_*` pair (ERCOT holds no
`complete`/`final` marker → no keeper_at_declaration immunity; ercot202's 12
hourly sidecars are sha256-identical to the ercot-204 keeper's, G-REPRO 12/12,
so no bytes left the tree), `neiso87_control_A` (twin of the superseded
neiso-87), `nyiso132_cf_arm` (keeper_at_declaration is nyiso-100). The pjm161
pair was adjudicated NOT-keeper by
`_pjm161-KEEPER-ADJUDICATION-2026-08-14.md`.

**NEW HOLD, not in the table:** `pjm_debugb_inputclock_A`
(`2026-08-15-pjm-162-inputclock`, 6.32 MiB) — live KEEPER CANDIDATE pending the
owner's promotion call (DEBUG-B input-clock charter §3.4); pruning it would
force a re-solve at promotion. Falls to the ordinary non-keeper disposition if
the owner declines.

**Untouched, verified:** the 6 keeper hourlies (28.1 MiB); the two VETOED
touchpoint rows above; `_nyiso114_baseattrib_2024` (§5.2); the 904+ loose
records; `results/hindcast`; `results/regression-goldens`; `scripts/probes/`.
keeper_at_declaration bundles (neiso-54 / nyiso-100 / pjm-140) no longer exist
on disk, and zero `ablation_twin`/`ablation_of` references exist in the
registry at HEAD — both immunity classes empty in practice.

**Gates:** PERF-B verified NOT mid-golden-capture before deletion (no perf
branch or PR; the release-plan ledger holds PERF-B ⛔ behind undeclared G1).
Same-PR greens pre- and post-prune: `check_registry_payload_parity.py` (70 runs
OK) and `audit_keepers.py --check` (PASS 0/0). No dashboard file changed. The
`golden-data-tier.yml` dispatch stays deferred (owner decision 2026-08-15,
pre-existing `curate_emissions` OOM, separate fix lane) — not part of this
PR's close.

### 5.2 The four `_`-prefixed dirs — **citation check answers KEEP (all four)**

The charter called them "the 4 unreferenced dirs"; line-level verification says
otherwise, and at 1.5 MiB combined they are immaterial anyway:

- `_archive` (0.3): cited by `DIAGNOSIS-ercot132-…` (a FINDING lives inside it)
  and is the refactor prompt-pack's designated move **destination**.
- `_ercot144_scratch` (0.1): artifacts cited by `PRECOMMIT-ercot144-…` and the
  ffr-1d enforcement handoff (which also encodes it in the ruff exclude
  rationale).
- `_nyiso114_baseattrib_2024` (1.1): **read by**
  `scripts/probes/_nyiso114_reserve_family_gates.py` (`BASE_ATTRIB = CAL / …`).
- `_pjm152_keeper_recipe` (0.04): **read by**
  `scripts/probes/pjm152_collapse_arm.py` — the current PJM keeper's recipe.

### 5.3 No-touch inventory (verified present)

904 loose `.md`/`.json` records (15.4 MiB) — the finding/measurement record;
`results/hindcast` (20.1) — forecast namespace; `results/regression-goldens`;
`results/ffr*` evidence dirs. All keep-required, none itemized.

---

## 6. Class D — script rotation (`scripts/README.md`'s own keeper-rotation rule; ≈ 0 MiB, hygiene + discoverability)

**Census at `f2de3b0`:** 83 top-level `gen_*_attestation.py` (charter's 82 + the
in-flight `gen_ercot193_attestation.py`), 194 top-level `.py` total.

**Keep-set at top level (6):** `gen_ercot192_attestation.py` (keeper),
`gen_miso148_attestation.py` (keeper), `gen_neiso87_attestation.py` (keeper),
`gen_caiso189_attestation.py` (docstring: writes the **caiso-188 keeper's** C6
attestation), `gen_pjm153_collapse_attestation.py` (docstring: writes the
**pjm-152 keeper arm's** attestation), `gen_ercot193_attestation.py`
(**in-flight hold** — rotates when the L-SCAR lane adjudicates ercot-193).
NYISO's current keeper (nyiso-132) has no top-level generator —
`gen_nyiso130_attestation.py` / `gen_nyiso130_keeper_ledger.py` attest the
*superseded* nyiso-128/130 lineage (docstring-verified) and rotate.

**Item D1 (class-approved): rotate 77 of 83 attestation generators** to
`scripts/archive/`, plus the per-run drivers/validators the same rule names:
the **miso-72 lineage** (`gen_miso72_attestation.py`,
`miso72_perzone_validate.py`, `run_miso72_winter_probe.py`) and the miso-74/75
probe drivers (`run_miso74_manitoba_probe.py`, `run_miso75_composition_probe.py`).

**Item D2 (the "~8 one-shot helpers", named here as the charter requires;
per-item verification at execution):**

| Script | Evidence | Status |
|---|---|---|
| `run_foresight_ab.py` | 0 standing refs (docs index/forecast plan/README/CI) | rotate |
| `run_calibration_eia930.py` | 0 standing refs; superseded lane | rotate (verify no skill/doc quotes it) |
| `run_ces_leg.py` | 0 refs in the checked standing set, **but** CES-POC is a named forecast family (CLAUDE.md rule 15) | **verify before moving** |
| `scripts/data/regen_caiso_bench_cems.py` | named "self-declared SUPERSEDED" in refactor plan WS-E; still present | rotate |
| `gen_nyiso130_keeper_ledger.py` | superseded lineage (above) | rotate |
| `miso72_perzone_validate.py` | miso-72 lineage | rotate (in D1) |
| `run_miso74_manitoba_probe.py`, `run_miso75_composition_probe.py` | superseded probe drivers | rotate (in D1) |

`run_driver_battery.py` / `run_equilibrium_battery.py` have standing doc
references — **excluded** (verified, so BLOAT-B doesn't re-ask).

**Mechanics (the PR #2486 discipline, all in one PR):** pure `git mv` +
mechanical reference rewrite; repo-root path math re-anchored for the extra
directory level; `python scripts/ci_refactor_guards.py --script-refs` green in
the same PR (flag verified present); `scripts/probes/` untouched (frozen
record); `file-integrity-guard` treats renames at destination with content
preserved, so **no `intentional-shrink` label is needed for pure moves**.

### EXECUTED 2026-08-15 (PR-4) — what actually shipped, and the three deltas from the plan above

**86 top-level scripts rotated** to `scripts/archive/` (194 → 108 top-level
`.py`; 151 → 237 in `archive/`): 79 `gen_*_attestation.py`,
`gen_nyiso130_keeper_ledger.py`, the miso-72 lineage
(`gen_miso72_attestation.py`, `miso72_perzone_validate.py`,
`run_miso72_winter_probe.py`), `run_miso74_manitoba_probe.py`,
`run_miso75_composition_probe.py`, `run_foresight_ab.py`,
`run_calibration_eia930.py`.

**Delta 1 — the keep-set is 4, not 6.** Re-derived at execution from
`keepers/<ISO>.json` + docstrings, as this section requires. Two of the six
rotated because the lane state moved after 2026-08-14:

- `gen_neiso87_attestation.py` — NEISO's keeper is now **neiso-93**
  (`2026-08-14-neiso-93-envelope`, promoted 2026-08-14), a `replay_keeper`
  zero-delta re-solve whose attestation was written by `build_dof_ledger.py`
  plus hand-authored governance sections, not by any `gen_*` script (the
  FINDING's own §"two things that needed doing" records this). neiso-87 is
  therefore superseded lineage and rotates under the standing rule.
- `gen_ercot193_attestation.py` — the in-flight hold **expired**. The ercot-193
  SOC re-gate was executed and discharged (RG-PASS on the original gates, run192
  reproduces byte-identically, keeper unchanged; `docs/calibration-log/ercot.md`
  §ercot-193), and ERCOT has since run to ercot-202.

Kept: `gen_ercot192_attestation.py`, `gen_miso148_attestation.py`,
`gen_caiso189_attestation.py` (caiso-188 keeper), `gen_pjm153_collapse_attestation.py`
(pjm-152 keeper arm). NYISO's keeper still has no top-level generator.

**Delta 2 — `run_ces_leg.py` STAYS** (the "verify before moving" row resolves to
keep). It has standing references, not zero: `tests/unit/policy/test_run_ces_leg.py`
imports it, `tests/regression/test_run_record_provenance.py` lists it in its
standing-entry-point set and imports it, and `run_full_horizon.py` re-exports
`assert_schedulable` specifically for it. It is live FF-3F harness code.

**Delta 3 — `scripts/data/regen_caiso_bench_cems.py` needed no action:** it was
**already** at `scripts/archive/regen_caiso_bench_cems.py` at execution HEAD,
which is why `scripts/data/derive_caiso_supply_consistent_demand.py` already
cites the `archive/` path.

**Mechanics as executed.** Pure `git mv`; the only content edits inside the moved
files are 86 repo-root expressions re-anchored one level
(`Path(__file__).resolve().parents[1]` → `parents[2]`, `.parent.parent` →
`.parent.parent.parent`), each re-verified by evaluating it at the new path and
asserting it equals the repo root, plus one sibling import in
`gen_caiso160_attestation.py` re-pointed `scripts.gen_caiso159_attestation` →
`scripts.archive.gen_caiso159_attestation`. Live references rewritten:
`src/market_sim/model/capacity_evolution/evolve.py`,
`src/market_sim/pipeline/reference.py`,
`tests/regression/test_capacity_evolution_facade.py`,
`docs/codebase-site/data/mechanism-matrix.js`, `scripts/README.md` (rotation
record + the sibling census, 74/50 → 73/49), `scripts/archive/README.md`.
`.github/workflows/` needed no edit (its only match names the KEPT
`gen_caiso189_attestation.py`). **Not** rewritten, per the `scripts/README.md`
frozen-record convention: `results/calibration/`, `docs/calibration-log/`,
`docs/sessions/`, `frontend/data/`, `CHANGELOG.md`, dated `docs/handoffs/` /
`FINDING-` / `PRECOMMIT-` records, and `scripts/probes/` (including the
`artifacts/_miso7{2,4,5}_chain.sh` repro drivers — charter: probes untouched).
Bare-name evidence citations inside the per-ISO mechanism-matrix shards were
likewise left alone: they are historical `ev:` pointers, and rewriting them
would mean a cross-ISO shard edit (rule 25 / 28d) for no live-path gain.
`ci_refactor_guards.py --script-refs` green (11 known-dangling tolerated,
unchanged); no `intentional-shrink` label (pure renames).

---

## 7. Class E — `frontend/data/backcast/runs` (70.1 MiB, 66 payloads)

**Re-verification result: the July defect no longer exists.** At `f2de3b0`,
`registry/*.json` ↔ `runs/*.js` are in exact 1:1 parity (66 = 66, both
directions, `comm`-verified). The D-3/B4 mechanics shipped since the July
audit: `dashboard_add_run.py::prune_iso` deletes the displaced run's sidecar,
payload **and** mapped `results/calibration/` bundle (keepers and
ablation-referenced twins immune; structural-prior source payloads immune), and
`check_registry_payload_parity.py` enforces **both** parity directions in CI —
its docstring records the payload→sidecar direction existing "so retention can
never leave a store behind". The 11 orphaned payloads flagged in July are gone.

**Item E1 — recovery now: 0 MiB (nil-action).** Nothing to prune; do not
invent work here.

**Item E2 — retention rule proposal (the charter ask), for owner adoption:**

1. **Payload lifetime = registry membership** (already enforced; adopt as the
   stated rule). A payload exists iff its sidecar exists.
2. **Per-ISO cap stays the rule-15 top-15**, executed by `prune_iso` at
   registration time (current counts are at/below cap).
3. **Immunity set as implemented**: current keeper, `keeper_at_declaration`,
   ablation-referenced twins, structural-prior sources.
4. **Bundle linkage**: pruning a run prunes its bundle dir in the same commit
   (already wired) — plus a **quarterly parity sweep** extension: fail if any
   `results/calibration/<bundle>` maps to no retained sidecar `bundle` field
   and is not otherwise keep-required (closes the last drift channel; extend
   `check_registry_payload_parity.py` or `audit_keepers.py`, one PR, no data
   change).

---

## 8. PR batching for BLOAT-B (all after G2; owner list-review at G1)

Recovery accounting (MiB, tip tree):

| Stage | Items | Class-approved | Needs-sign-off / hold |
|---|---|---:|---:|
| PR-1 | A1 + B1a SCED slim | ≈ 1,450 + 95 | — |
| PR-2 | B4 xlsx + B5 PDFs + B6 zips + B3-hygiene GUID | 155.0 + 137.9 + 65.2 + 3.7 | — |
| PR-3 | C-5.1 hourly prunes | 62.7 | 23.2 hold + 5.9 sign-off |
| PR-4 | D1 + D2 rotation | ~0 (hygiene) | — |
| PR-5 (only if signed) | B3 dailies 563.6 · B1b extracts 145.1 · A2 ≈ 1,280 | — | ≈ 1,989 |
| **Totals** | | **≈ 1,970** | **≈ 2,018** |

Tip trajectory: 10,080 → **≈ 8.1 GiB** (class-approved only) → **≈ 6.1 GiB**
(with all signed items). Stage 2 (separate decision) → ≈ 2.5 GiB.

- **PR-1 — "SCED manifests + in-place slim" (A1, B1a).** Sequence:
  `SHA256SUMS.txt` over current bytes (provenance of what slimming replaced) →
  slim → new `SHA256SUMS.txt` → re-derive **every** consumer artifact listed in
  §3 and byte-compare (ERCOT-157 acceptance) → chunked pushes per §3's
  execution note. Label `intentional-shrink` (data paths do not trip
  `file-integrity-guard` — its `is_core` set is `src/`, `scripts/`, CLAUDE.md,
  the spec, workflows — but G3's definition expects prune PRs labeled, so label
  by convention). README provenance paragraphs updated in the same PR.
  **EXECUTED 2026-08-15** (BLOAT-B-1 session, PR #3958; step-1 manifests
  landed separately via PR #3957 / `971eaa3`): A1 + B1a slimmed in place over
  all 1,027 files; the ERCOT-157 byte-identity acceptance passed 15/15 (12
  derive artifacts + the 27-part rtcb adapter fingerprint + both
  `--position-tail` STOP records — evidence table in the PR). Measured
  recovery **739.8 MiB / 21.3%** against the ≈1,545 estimate: the precedent
  ratio (0.547) was measured on SNAPPY originals and the 2026-08 re-uploads
  were already default-zstd, so the codec half of the yield was banked before
  this PR — the projection half is what remained. The consumer registry was
  re-audited first (KEEP 79→108 corpus / 180 extracts; rtcb recompress-only
  per the adapter contract, card D/D1 — no consumer subset exists to project
  to). A2 untouched (needs-sign-off, Stage-2 call).
- **PR-2 — "corpus conversions, evidence-complete set" (B4, B5, B6, GUID
  hygiene).** One PR, per-corpus commits: gitignore blocks in the §4
  established idiom (payload glob + `!README` + `!SHA256SUMS.txt`), SOURCES/URL
  tables, SHA256SUMS, **pin sha recorded per corpus README** (the §0ar-3
  recovery command), deletions. Label `intentional-shrink`. **Same-PR
  CLAUDE.md touch** (Cloning & session data: profile-size table note; the
  data/raw README sentence gains "some corpus payloads are gitignored — see
  each corpus README for the re-fetch/restore recipe") — CLAUDE.md is core and
  ≥300 lines: rule 27 mechanics (edit locally, push exact bytes, blob-verify).
  After merge: **manual `golden-data-tier.yml` dispatch** (decision 7
  authorizes BLOAT-B's re-dispatch) — green run = proof no test opened the
  removed files.
- **PR-3 — "non-keeper hourly prune" (C-5.1 class-approved rows).** Label
  `intentional-shrink`. Same-PR green: `check_registry_payload_parity.py`,
  `audit_keepers.py`. No dashboard files change (payloads/sidecars untouched).
  Holds re-checked at execution date against lane state; sign-off rows only if
  signed at G1.
  **EXECUTED 2026-08-15**, PR #3982 (branch
  `claude/bloat-b3-hourly-prune-xt1i22`): **24 bundles / 288 files /
  −117.01 MiB** at tip, list re-derived at `11b59ee` (twice — main moved
  mid-session). All three holds lifted on lane state, one NEW hold honoured
  (`pjm_debugb_inputclock_A`, live keeper candidate pending the owner's
  promotion call), the C-sign-off rows already VETOED-kept by B-5. Both greens
  pre- and post-prune; zero dashboard files changed. Execution record and the
  full disposition table: §5.1 "EXECUTED 2026-08-15".
- **PR-4 — "script rotation" (D1, D2). SHIPPED 2026-08-15**, PR
  [#3955](https://github.com/jessicacohen554-cyber/market-simulator/pull/3955)
  (branch `claude/bloat-b4-script-rotation-dmktqx`). `git mv` + reference rewrite
  + `ci_refactor_guards.py --script-refs` green. No label needed (renames).
  86 scripts rotated; keep-set re-derived to 4; `run_ces_leg.py` verified and
  kept; `regen_caiso_bench_cems.py` already archived. Execution record and the
  three deltas from the itemization: §6 "EXECUTED 2026-08-15".
- **PR-5 — signed-item batch** (whichever of B3 / B1b / A2 / C-sign-offs the
  owner approves at G1), same mechanics as PR-2/PR-3.
  **EXECUTED 2026-08-15** (BLOAT-B-5 session, PR #3978, label
  `intentional-shrink`): the owner answered the G1 item card **in-session** —
  **A2 SIGNED / B1b SIGNED / B3 SIGNED / C-touchpoint rows VETOED** (kept
  while the 2022 touchpoint loops are live). Executed **−2,518.5 MiB / 763
  payload files** at tip (A2 1,846.9 + B3 559.9 + B1b 111.7 — post-slim
  bytes; no history rewrite, pack unchanged): per-corpus commits in the PR-2
  idiom, manifests tracked (B3's newly created over tree-sha-verified bytes;
  A2/B1b reuse B-1's post-slim manifests), pin sha `726f389d` + restore
  commands per corpus README, ignore semantics asserted for every payload and
  kept class. Item records: §3 (A2), §4.1 (B1b), §4.3 (B3), §5.1 (C veto).
  The charter's post-merge golden-tier dispatch is **DEFERRED** — see
  Close-out below.
- **Close-out (per WS6):** `cleanup-large-blobs.yml` **DRY RUN** —
  `dry_run=true` — to quantify what the prunes turned into
  superseded-blob reclaim for the standing owner option (the workflow's
  2026-08-12 patch made its protect/verify steps sound; execution remains
  NO-GO under AQ). Then the post-prune `golden-data-tier.yml` dispatch result
  goes into the G3 gate evidence, and the recovery table above is re-measured
  against the actual tree for the BLOAT-B report.
  **Golden-tier dispatch DEFERRED (owner decision 2026-08-15, BLOAT-B-5
  sitting):** the tier has never been green — the pre-existing
  `curate_emissions.py` runner OOM (salvaged report
  `docs/bloat-removal-report-2026-08.md` §4) fails every dispatch regardless
  of prunes — so the owner accepted deferring the B-1/B-2/B-5 post-merge
  dispatch duty until the GOLDEN-TIER-FIX lane lands the memory fix and runs
  the single authorized dispatch; G3 stays evidence-blocked until that run is
  green.
  **DISCHARGED 2026-08-15 (GOLDEN-TIER-FIX lane):** the
  `curate_emissions.py` streaming-assembly fix landed
  (`claude/golden-tier-emissions-oom-03qlck` @ `ccca569`; peak RSS
  10.05 → 5.17 GiB on the tier's 2023 inputs, output verified
  data-byte-identical for 2023 and 2024) and the single authorized dispatch
  was spent on that branch, whose base `870c4c8` carries every executed
  BLOAT-B prune: run `31913648051` — **GREEN in 11m33s** (the emissions step
  1m31s), loud-failure guard PASS, zero data-missing skips, no corpus
  restored, sparse list untouched. The
  B-1/B-2/B-5 duty and PR-3 are covered by the one run; **G3's evidence gate
  reopens** (full entry: release plan §8 ledger, 2026-08-15
  GOLDEN-TIER-FIX).
  **Close-out EXECUTED 2026-08-15 (BLOAT-B-7,
  `docs/bloat-removal-report-final-2026-08.md` — THE after-measurement):**
  dry run `31912344135` at `04d1cf0` re-quantified the superseded-blob pool
  against the salvaged 922.3 MiB / 3,974-blob pre-prune floor: **7,053 blobs /
  7,338.4 MiB removable** vs 6,225.7 MiB protected, disjointness PASSED — the
  ≈6,416 MiB growth is the prune-created reclaim this bullet chartered the
  measurement for, and
  the AQ NO-GO stands with its rationale inverted (the superseded pool is now
  the conversion class's recovery archive; report §5, which also records the
  aborted run-#16 rewrite attempt). Recovery table re-measured: tip
  **6,405.7 MiB / 9,204 files**, −3,674.3 vs the 10,080.0 base; measured PR
  sum 3,737.1 vs the ≈3,988 full-sign-off estimate, variances reconciled
  (report §3). Golden-tier status at the close-out's measurement commit
  `04d1cf0`: the tier's FIRST GREEN already existed — run `31867650665` at
  `c447199`, post-PR-1/2/4, stock `curate_emissions`, discharging the
  deferred B-1/B-2 dispatch duty for those PRs — and the GOLDEN-TIER-FIX
  discharge above landed while the close-out was in flight, supplying the
  post-PR-3/PR-5 green (`31913648051`) that completes the G3 evidence
  (report §6, incl. its rebase addendum).

Ordering within Wave 3: PR-4 (no data) any time; PR-2 → PR-3 → PR-1 (PR-1's
chunked pushes are the long pole; nothing depends on them landing first);
PR-5 last. The one scheduling hazard the release plan flags — PERF-B stage
captures re-solving keeper bundles — is upstream of G2 and therefore already
closed by the time any of this executes.

---

## 9. D-ledger update section (resuming `docs/refactor-consolidation-plan-2026-07.md` §9 — not restarting it)

Status found this session, and proposed entries for the PM to append (numbering
assigned by the PM/owner at G1 to avoid colliding with ledger numbers cited
elsewhere, e.g. the D-13 cache-key gate):

- **D-3 (retention sweep + prune-extension): CLOSE AS SHIPPED.** Verified live
  at `f2de3b0`: `prune_iso` deletes sidecar + payload + mapped bundle with the
  immunity set; parity checker guards both directions in CI; zero orphans
  measured. Residual from B4's text now proposed as Class-E rule 4 (§7, the
  quarterly bundle-parity sweep).
- **D-4 (root LMP zips): CLOSE AS EXECUTED.** Zero root-level zips at tip
  (measured); the moved dailies inside `lmp-data/CAISO` are now item B3.
- **D-5 (`patches/pjm-m1-code.patch`): UNTOUCHED by this plan** — keep-required
  honored; its disposition is release-plan decision 2 (DEBUG lane), not BLOAT.
  *(Superseded 2026-08-15 — **D-5 is CLOSED**: DEBUG-A closed it on 2026-08-14,
  archiving the patch to `patches/archive/pjm-m1-code.patch` beside
  `ARCHIVED-2026-08-14-pjm-m1.md`. Moved, not deleted, so keep-required still
  holds. `docs/bloat-removal-report-2026-08.md` §5.4.)*
- **D-8 (data-in-git long-term: "Defer; document status quo"): SUPERSEDE.**
  The deferral is spent: FINDING-rewrite-prep §8 (GO/NO-GO), fast-clone (#3909)
  and release-plan decision 4 replace the status quo with the two-stage
  architecture in §1. Proposed new entries:
  - **(new) BLOAT-1:** approve/veto the Stage-1 itemized list per class
    (§3–§7), the G1 review this plan exists for. Class-approved items carry
    decision 4's signature; the named needs-sign-off items (A2, B1b, B3,
    C-touchpoint rows) are the item-level calls. *(SPENT 2026-08-15 — the G1
    item card was served and answered in-session at the BLOAT-B-5 sitting:
    A2 SIGNED, B1b SIGNED, B3 SIGNED, C-touchpoint rows VETOED-kept — and
    every verdict is executed and verified at `04d1cf0`. Proposed CLOSE:
    `docs/bloat-removal-report-final-2026-08.md` §7.)*
  - **(new) BLOAT-2:** adopt the Class-E retention rule text (§7 E2).
    *(Still open at the 2026-08-15 close-out; rule 4's quarterly
    bundle-parity sweep also unbuilt.)* *(CLOSED 2026-08-16 — the E2 card
    was served and **ADOPTED** in-session at the BLOAT-2 sitting: all four
    points written verbatim with the adoption date into
    `frontend/data/backcast/keepers/README.md` (the rule's standing home),
    and point 4's bundle-parity sweep BUILT in the same PR —
    `check_registry_payload_parity.check_bundle_retention` fails any
    top-level `results/calibration/<bundle>` dir that no retained sidecar's
    `bundle` field maps and that is not keep-required (`_`-dirs per §5.2,
    regression-golden-referenced bundles, the documented
    `KEEP_REQUIRED_UNMAPPED_BUNDLES` allowlist — empty at adoption). It
    lives in the always-on CI parity gate, a strict superset of the
    quarterly cadence. No data change; both checkers green at HEAD before
    and after (15 runs / 15 bundle dirs swept; `audit_keepers --check`
    PASS 0/0).)*
  - **(new) BLOAT-3:** the Stage-2 charter decision — whether/when to untrack
    the measured 3,561.6 MiB residual under the §0ar-3 checklist, with §4.8's
    follow-on evidence passes as its BLOAT-A-equivalent prerequisite. Until
    signed, Stage 2 remains a standing option, not scheduled work. *(Still
    open; charter input re-measured at `04d1cf0` by the close-out —
    adjudication pool 4,008.7 MiB / 1,487 files, takeable residual
    ≈ 3,311.9 MiB after the §4.2/§4.7 keep-verdicts, full untrack → tip
    ≈ 3.0 GiB; the report's §7 adds the A2-precedent and rewrite-NO-GO
    hardening notes.)* *(Decision card DRAFTED AND SERVED 2026-08-16, session
    BLOAT-3 — `docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md`. The
    2026-08-16 history rewrite invalidated the history-as-archive premise the
    stage was chartered on, so the card's central question is the RECOVERY
    STORY, not just the untrack: (a) per-corpus re-fetch evidence-passed /
    (b) owner-held external archive for the irreplaceable subset / (c)
    explicit signed loss — with pin-based recovery admissible only under an
    explicit no-further-rewrite commitment. Card recommends the staged
    (a)-only GO (O2, ≈ 1.1 GiB prima facie). **VERDICT: SIGNED IN-SESSION
    2026-08-16 — BLOAT-3 is ADJUDICATED: O2 staged (a)-only GO.** Story (a)
    alone admitted — no (b) external archive, no (c) loss route (a corpus
    failing its pass STAYS TRACKED), no (d) pin commitment (pins stay dead;
    no `hydrate_data.py` pin support). §4.8 evidence passes AUTHORIZED as
    the prerequisite; golden-tier proof = the weekly cron green; the §4.2
    DAM 2024+ subset stays OUT (travels with any future archive decision).
    Full ruling text: the card's verdict banner. Open follow-on work:
    the per-corpus evidence passes, then untrack PRs for passing corpora
    only.)* *(EXECUTED 2026-08-17, session BLOAT-S2 — the §4.8 evidence
    passes ran for six corpora and the passing subset was untracked in
    per-corpus commits (PR-2/PR-5 idiom, `intentional-shrink`), **−444.5 MiB
    / 144 files** at tip, tree-sha-verified before hashing. Verdict table
    (full evidence: `docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md`):
    `storage-as-awards` **PASS** −165.2 · `data/raw/PJM` **PASS (zero
    consumers — a naming-trap orphan)** −107.1 · `campd-unit-level`
    **SPLIT** −105.1 (2018 only; 2019–2026 are solve-time year-keyed inputs
    — the prima facie 692.6 story REFUTED by the census) · `eia-930`
    **SPLIT** −33.8 (per-BA long files + 2018 BALANCE; BALANCE 2019–2026
    stay as `wecc-west-supply` rebuild inputs, the 7 hand-assembled `eia_*`
    files have no (a) story) · `iso-specific-transmission` **SPLIT** −33.3
    (PJM-2018 pair; loss surfaces + PJM 2019–2026 + the instrument-less
    NP6-86 parquets stay) · `lmp-data` non-golden **FAIL — stays tracked**
    (MISO's archive measured decaying, ERCOT/ zips are holdout scoring
    rebuild inputs, remainder immaterial). Every retention window was
    measured live with negative controls; golden-tier sparse list needed
    ZERO edits (verified per-glob at execution HEAD); skip-when-absent
    verified by like-for-like full-suite runs in a payload-absent worktree.
    The session also surfaced main's pre-existing `run_calibration.py`
    breakage (#4036 merge-race duplicate kwarg, then the twin-fix collision
    that dropped the kwarg's `with_overrides` application; both re-fixed
    upstream mid-flight — FINDING §8 carries the genealogy). Post-merge proof = the first weekly golden-tier cron
    green after merge (no dispatch spent, per D3).)*

---

## 10. Keep-required verification (charter list, checked against `f2de3b0`)

All present, none itemized anywhere above: golden-tier sparse-list paths
(**1,500.0 MiB measured**, §2); `data/dictionary/`; every README/SOURCES/
SHA256SUMS (conversions *add* manifests, never remove); the 6 keeper bundles +
hourly sidecars; the 904 loose finding/measurement records (15.4 MiB);
`results/regression-goldens/`; slim A/B evidence dirs (the §5.1 "keep slim"
column is this rule applied); `frontend/data/backcast` (frozen surface, rule
15 — Class E is nil-action); `scripts/probes/` + `scripts/archive/` (frozen
record — §6 only *adds* to archive; nothing in either is touched, and any
future removal there is an owner decision this plan does not request);
`patches/` (pending D-5); `scope2-lce-portfolio` (7.0 MiB, confirmed not worth
listing). Workflows reading `data/raw` were walked per §0ar-3(a):
`golden-data-tier.yml` (handled §1/§4/§8), `fetch-caiso-oasis-bulk.yml`
(writes/stages raw, consistent with B3's corpus design), and
`cleanup-large-blobs.yml` (dry-run-only tool, §8).
