# ERCOT-183 — the 2024/2025 NP3-965 full-year re-upload (owner card D4, 2026-08-09)

**Authorization:** owner sitting 2026-08-09, card D4 — SIGNED
(`docs/DECISION-CARD-ercot182-c3a2023-reachability-2026-08-09.md` §8 is the
ask; the sitting record carries the signature). Rule 22 places data intake
OUTSIDE the spend gate: no year's answer is looked at here — no solve, no
scoring, no registration, keeper `2026-08-09-run181-position-tail` untouched.

**Scope:** additive intake under `data/raw/ercot/SCED/` + the §3 acceptance
test. No `src/market_sim/` change, no LP, no mechanism, no matrix cell.

---

## 1. Source and provenance

* **Report:** ERCOT MIS NP3-965-ER "60-Day SCED Disclosure Reports"
  (`reportTypeId=13052`), Gen Resource Data members — the telemetered RT
  energy-offer-curve disclosure. Fetched over the unauthenticated legacy MIS
  endpoints (`IceDocListJsonWS` / `mirDownload`), the same path as
  `scripts/data/fetch_ercot_60day_sced_gen_resource.py`, whose verified
  constants and zip/member helpers the intake script imports.
* **Intake tool (this session, committed):**
  `scripts/data/fetch_ercot_sced_corpus_shards.py` — publication-window fetch
  → one part per publication day, raw 187-column all-string copy, zstd
  parquet, `YYYY-MM.partNNNN.parquet` (the existing corpus convention; a
  month's numbering CONTINUES on-disk parts, e.g. `2024-03.part0009` follows
  the delivery-2023 re-upload's `part0000-0008`). Delivery days are read from
  each member's own `SCED Time Stamp` values, never from filenames. Each
  delivery day is written exactly once (reposts/supplemental duplicates
  skipped and logged). NO column slimming — `Submitted TPO-*` are live
  instrument inputs (`scripts/lib/sced_corpus_instruments`).
* **Window fetched:** publications **2024-03-24 .. 2026-03-01** (the free MIS
  list's back edge on 2026-08-09 is 2024-03-24 — unchanged since 2026-07-16)
  plus supplemental catch-up bundles published through 2026-04-30, harvested
  for still-uncovered Gen delivery days ≤ 2025-12-31 (`--max-delivery-date`
  refuses locked-test-year rows arriving through irregular supplemental lags).
* **Manifest:** every written part (DocID, publication day, delivery day,
  rows, bytes) recorded in a session manifest; the §5 coverage table is
  generated from it. The manifest is a session artifact (scratchpad), not a
  repo file; its summary lives here.

## 2. Reachability disclosures (stated before fetching)

* **Delivery 2024-01-10..23 is UNREACHABLE** on the free MIS path
  (publications 2024-03-10..23 have aged out; the owner's local raw archive is
  the only remaining source — the ERCOT-157 precedent). Deliveries
  2024-01-01..09 are already on disk (`2024-03.part0000-0008`, the
  delivery-2023 re-upload's bleed). Delivery-2024 therefore lands with a
  disclosed 14-day January hole unless the owner supplies those publications.
* **Delivery 2025 Nov/Dec are NOW INCLUDED** (publications 2025-12-31..
  2026-03-01 are listed). This EXTENDS the purged 2026-07-21 corpus, whose
  cutoff left Nov-2025 partial (~131k rows) and Dec-2025 absent. The frozen
  RT-wall artifacts disclose that older, thinner 2025 coverage — see §4.
* The 2024-10-04 publication day carries the 245 MB supplemental bundle (32
  displaced delivery days at lags 9–39); it is harvested member-by-member.

## 3. The acceptance test (the session's real deliverable)

Post-intake, re-run the frozen-ladder reproduction asserts, each year
SEPARATELY (the assert stops at the first mismatching year, so a combined run
would mask the later year's result), writing `--out` to scratch so the
committed positiontail artifacts are never touched:

```
python scripts/data/derive_ercot_sced_offer_wall.py  --position-tail --years <Y> --out <scratch>/wall_pt_<Y>.json
python scripts/data/derive_ercot_faststart_pool.py   --position-tail --years <Y> --out <scratch>/pool_pt_<Y>.json
```

for Y in {2023, 2024, 2025} (2023 is the control: its corpus is untouched by
this intake and must keep reproducing). PASS = the re-derived ladders (and
pool_frac for the pool) reproduce the frozen artifacts byte-identically. A
failure is a FINDING, reported at full magnitude — never something to fix by
adjusting the derive (rule 23). No new positiontail artifact is derived or
committed; nothing is armed; the ercot-180 grain identification is not re-run
(its reopen needs its own precommit on this corpus as new evidence).

## 4. PRE-INTAKE BASELINE — measured in this session BEFORE any fetch

Run on the untouched HEAD corpus (315 shards + the four sample-day extracts),
current derive code:

| artifact | year | today's re-derive vs frozen |
|---|---|---|
| faststart pool CT | 2024 | **ladder AND pool_frac reproduce EXACTLY** |
| faststart pool CT | 2025 | **ladder AND pool_frac reproduce EXACTLY** |
| RT wall CC/CT | 2024 | coverage rows (intervals/days/mean_spare_gw) **identical**; 5 ladder rungs differ (CC bin2 q90 −0.013, CC bin4 q90 +0.001, CT bin2 q30 +0.009, CT bin3 q70 +0.136, CT bin5 q10 −0.001) |
| RT wall CC/CT | 2025 | coverage rows **identical**; 3 rungs differ (CT bin5 q10 −0.001, CT bin5 q70 −0.012, CT bin6 q10 −0.003); CC exact |

Two consequences, stated before the intake so they cannot be mistaken for its
results:

1. **The frozen wall 2024/2025 blocks are SAMPLE-DAY-based, not full-corpus
   based.** Their committed coverage (356 intervals in 2024 bin 0) equals
   today's sample-day derivation exactly, where the 2026-07-21 full-corpus
   verification recorded ~8,751 intervals per bin for a corpus year. This
   contradicts PRECOMMIT-ercot181 Amendment 1's premise that those blocks
   "were derived from the 2026-07-21 full-corpus intake": their population
   has been on disk all along; what fails to reproduce is 8 rungs at the
   0.001–0.136 mult scale on an IDENTICAL population — numeric/tie-break
   drift between the ERCOT-86-era derive and today's streaming derive (or a
   small shared-input revision), not a purged population.
2. **The intake itself flips the 2024/2025 selection basis.** Once the corpus
   majority-covers those delivery years, `_sced_source_files` (by the
   ERCOT-157 design) supersedes the sample-day extracts — so byte-identity
   with the sample-day-based frozen blocks is NOT the expected outcome of §3
   post-intake for either member, in either year. The §3 results are still
   run and reported at full magnitude; interpreting them uses this baseline.

## 5. Staging plan (pre-registered BEFORE any corpus push — task §2)

The 2026-07-22 history rewrite is the failure mode being staged against; the
measured transport facts: `push_files` caps at ~457 KB per payload; the git
gateway's pack ceiling is session-dependent (434 KB single-blob pass
2026-07-25; 413 at ≥ ~1.3 MB in the 2026-08-03 session; corpus-scale pushes
have historically been owner-side).

1. **Commit A (this doc + code, before any corpus bytes):** intake script,
   offline tests, `data/raw/ercot/SCED/README.md`, this handoff (plan
   version). Small text pack via `git push`; blob-verify the ≥300-line script
   against the remote (rule 27).
2. **Transport probe ladder (first corpus commits, smallest first):** one
   ~4 MB shard alone → if accepted, batches of ~5 shards (~20 MB) → ~30
   shards (one publication month, ~130 MB). Stop escalating at the first
   failure; settle on batches ≤ half the largest verified pack. On a 413 at
   the single-shard rung, fall back to splitting each publication day into
   sub-MB `partNNNN` slices (the convention is size-agnostic: months on disk
   already vary 9..31 parts) and push per-commit packs ≤ 0.9 MB.
3. **Every push is verified before the next:** `git push` exit + `git
   ls-remote` sha match (content-addressed identity of every blob in the
   pack), with a periodic `git fetch && git status -sb` divergence check and
   one spot fetch-back byte comparison per session. A failed push never
   retries blind: rebase onto fresh `origin/main` if the branch moved, halve
   the batch on transport errors.
4. **Commit order:** corpus months chronologically (2024-03 top-up, 2024-04,
   …, 2026-03), then supplemental parts, then the results commit (this doc's
   §5–§7 filled, calibration-log entry). If the session dies mid-corpus, the
   manifest + on-disk months make the next session's resume exact
   (`--manifest` re-run skips covered delivery days).

## 6. RESULTS — the landed corpus (fetch 2026-08-09, forensics clean)

**708/708 listed ordinary publication days landed** (window pubs
2024-03-24..2026-03-01; 4 docs initially served non-zip error bodies and were
recovered on a retry pass). All 7 supplemental docs opened; the 245 MB
2024-10-04 catch-up bundle contributed nothing new (all 32 displaced delivery
days were also republished ordinarily and already covered). One delivery day
is written exactly once — the full-corpus scan shows **zero duplicate
delivery days, zero part-sequence holes, zero unreadable shards**.

**Post-intake consumable corpus** (`data/raw/ercot/SCED/*.part*.parquet`):
996 parts, 117.60M rows, 1,056 delivery days (2022-12-31..2025-12-04), median
110,208 rows/day, no light days. All parts carry the pre-RTC+B 187/188-column
schema (`HASL` present; the 188th column is `Ancillary Service ECRS`,
appearing when the product launched mid-2023). New parts are written
`string`-typed as before (Arrow physical type `large_string` vs the older
uploads' `string` — immaterial: every consumer reads per-file via pandas).

| delivery window | days | rows | note |
|---|---|---|---|
| 2024 | **352/366** | 40.12M | complete EXCEPT Jan 10–23 (pubs 2024-03-10..23 aged out of free MIS retention — pre-registered §2 gap; Jan 1–9 are the 2023 re-upload's bleed parts, Jan 24–31 fetched at the retention edge) |
| 2025 | **365/365 fetched; 338 consumable** | 44.53M consumable | Jan-01..Dec-04 in the readable format, INCLUDING complete Nov (the purged original had Nov partial/Dec absent); Dec-05..31 (27 parts, 8.66M rows) QUARANTINED — see below |
| 2024-05 | 31/31 | 3.38M | the purged original's "2024-05 sparse (109k rows)" gap does NOT recur — the MIS now serves the full month |

**The RTC+B disclosure-format break (new finding, disclosed at full
magnitude).** Publications 2026-02-02 onward (deliveries **2025-12-05..31**)
carry ERCOT's RTC+B-era Gen member format: `HASL`/`LASL` REMOVED,
`Telemetered Net Output ` renamed (trailing space dropped), `Ancillary
Service *` responsibilities replaced by `AS Awards */AS Capability *`, `Ramp
Rate Up/Down` added (193/195-column variants; daily rows triple to ~320k as
the disclosure's resource scope widens). `HASL` is a required read column of
every corpus consumer, so these shards CRASH the derives — the identical
defect ercot-95/97 quarantined in the Dec-3-9-2025 out-of-band upload. The 27
parts are preserved byte-intact in `data/raw/ercot/SCED/rtcb-format-2026/`,
invisible to the consumers' non-recursive globs. Consuming the RTC+B era
needs its own owner-authorized format adapter; nothing frozen measures those
days (the purged original's 2025 population ended at Nov-partial/Dec-absent).

**Staging record (task §2 discharged).** The corpus landed in **19 verified
pushes** interleaved with the fetch: probe ladder 2.6 MB → 13 MB → 116 MB,
then manifest-complete batches of 16–290 MB, every push confirmed by
`ls-remote` sha match before the next (content-addressed identity of every
blob). Two mid-session branch deletions occurred when the owner-side
automation merged in-flight PRs (#3806, #3813); both recovered by rebasing
onto the new `origin/main` and re-pushing, exactly per the standing
instruction — no bytes lost, no history rewrite, no force-overwrite of
another session's work. One in-flight push was killed by a 2-minute tool
timeout and taught the staging loop to carry a 10-minute ceiling; the largest
verified single pack was 290 MB (this remote's gateway comfortably exceeds
the 2026-08-03 session's ~1.3 MB pathology, which does not reproduce here).

## 7. RESULTS — §3 acceptance outcomes (filled after the runs)

*Pending.*

---

**Bookkeeping duties on completion:** calibration-log entry (ercot-183); NO
mechanism-matrix cell (nothing tested — duty (b) does not trigger); keeper and
its artifacts untouched; no dashboard registration (no run produced).
