# FINDING — ercot-248 (2026-08-31): the 2024/2025 all-resource SCED conduct corpus was NOT missing — it was fetched on 2026-08-09 (ercot-183) and UNTRACKED AS PAYLOAD on 2026-08-15 (BLOAT-B-5 item A2), so the funded intake is a RESTORE, executed and verified here (700/700 delivery days 2024-02-01..2025-12-31, 88.56M rows, 0 duplicates, 0 rule-22 leaks, delivery-2023 derive byte-identical); the charter's per-day placement route would have produced a corpus INVISIBLE to every existing consumer, and the corpus's own `SHA256SUMS.txt` cannot accept a re-fetch (writer-version-specific bytes), so a writer-independent acceptance manifest is added

**Session ercot-248, branch `claude/ercot-248-sced-allresource-intake-xzg2qy`.
DATA INTAKE ONLY** — zero solves, zero scoring, zero registration, no
mechanism tested, no keeper/shard/marker/determination/matrix cell moved, no
`ScenarioConfig` field. Every number below is measured in-session against the
live ERCOT MIS and the restored corpus on disk.

---

## 0. Verdict in six lines

1. **The corpus already existed.** `data/raw/ercot/SCED/` publications
   2024-04..2026-03 (700 parts, deliveries 2024-02-01..2025-12-31,
   **all-resource**) were fetched by ercot-183 on 2026-08-09 and untracked as
   gitignored payload by BLOAT-B-5 item A2 on 2026-08-15. They are absent from
   a fresh clone, which is why the charter read the span as CT-only.
2. **What made the charter read it that way is a stale table**, now fixed:
   `data/raw/ercot/SCED-CT/README.md`'s coverage table was written 2026-08-04
   and still said the 2024-01-24..2025-12-31 span was CT-only. It stopped being
   the whole truth five days later.
3. **The restore succeeded completely.** 700/700 ordinary publication days in
   `[2024-04-01 .. 2026-03-01]` were listed by the MIS today; 700 parts written;
   **88,561,421 rows**; every delivery month complete; 0 duplicate delivery
   days; 0 deliveries past 2025-12-31; the only gap the known, permanently
   unreachable 2024-01-10..23.
4. **The charter's placement route would have failed silently — but in the
   opposite direction to the one it feared.** Per-day files named
   `..._<label>_<date>.parquet` in `data/raw/ercot/SCED/` match **neither**
   consumer glob, so they would have been an invisible corpus, not a corrupting
   one. Placement went to the existing publication-month convention instead.
5. **`SHA256SUMS.txt` cannot accept a re-fetch restore**, contrary to the SCED
   README's recovery route 2. Parquet bytes are writer-version specific. A
   writer-independent manifest (`RESTORE-ROWCOUNTS.txt`) and the tool that
   writes and checks it (`scripts/data/audit_sced_corpus.py`) are added.
6. **Regression verification passes byte-identically**: the delivery-2023
   offer-wall derive reproduces sha256 `6601a821…` before and after the restore.

---

## 1. Stage 1 — the measurement, before any bulk fetch

### 1.1 Retention boundary, measured live 2026-08-31

`IceDocListJsonWS`, `reportTypeId=13052`: **898 documents, 891 distinct
publication days, earliest `2024-03-24`, latest `2026-08-31`** (7 supplementals:
2024-10-04, 2026-02-05, 2026-02-23 ×3, 2026-03-12, 2026-04-10).

Earliest reachable **delivery** day = **2024-01-24**. This is **unchanged**
from the 2026-08-04 measurement in `data/raw/ercot/SCED-CT/README.md` and the
2026-08-09 ercot-183 measurement — the floor has not moved in four weeks, so
**Gap 1 (deliveries 2024-01-10..23, 14 days) has NOT grown**, contrary to the
charter's expectation. The free MIS list behaves as a fixed floor over this
observation window, not a strict rolling one. Recorded as measured, not
guaranteed: re-measure before relying on it.

**700/700** ordinary publication days in the target window
`[2024-04-01 .. 2026-03-01]` were listed — the entire span was reachable.

### 1.2 The probe day, unscoped

Publication **2025-06-02**, doc `1108289319`, delivery **2025-04-03**:

| quantity | value |
|---|---|
| zip | 11,288,273 B |
| CSV member, uncompressed | 103,224,375 B |
| rows × columns | **122,106 × 188** |
| CT rows (SCLE90 + SCGT90) | **18,528 = 15.174 %** |
| all-resource : CT row ratio | **6.59×** |

Resource-type census: WIND 37,440 · PWRSTR 24,000 · PVGR 23,136 · SCLE90 15,552
· CCGT90 5,568 · SCGT90 2,976 · GSREH 2,688 · CLLIG 2,496 · DSL 2,304 · HYDRO
2,112 · CCLE90 1,152 · GSNONR 1,050 · NUC 768 · RENEW 480 · GSSUP 384.

The 6.59× row ratio and 15.17 % CT share reproduce the SCED-CT README's
measured 18,816/124,608 (15.10 %) on its own 2025 day.

### 1.3 The disk projection — it fits, ~8× over

Same day written four ways:

| storage form | bytes/day | × 700 days |
|---|---|---|
| **raw-string zstd (the corpus convention — chosen)** | 3.37 MB | **≈ 2.36 GB** |
| post-slim 108-col zstd-15 | 2.61 MB | ≈ 1.83 GB |
| coerced float64, snappy (the 60day fetcher's default) | 5.29 MB | ≈ 3.75 GB |
| coerced float64, zstd | 4.05 MB | ≈ 2.83 GB |

Writable disk available at session start: **20 GB**. No STOP condition.
**Measured outcome: 2,341.5 MiB actual** over the 700 restored parts
(3.51 MB/part), i.e. the projection was accurate to ~1 %. Transient download
≈ 7.9 GB streamed, never stored. Throughput measured at 3.06 MB/s, ~3.7 s per
publication zip; the full restore ran ~2.9 h wall-clock single-threaded.

---

## 2. Stage 2 — the placement decision, and why the charter's route was wrong

### 2.1 The discovery that reframes the task

`data/raw/ercot/SCED/README.md` §"Untracked 2024+ payloads" and `.gitignore`
lines 913–923 record it plainly: publications **2024-04..2026-02 (673 shards)**
plus the whole **`rtcb-format-2026/` quarantine (27 parts)** — 700 files,
1,846.9 MiB post-slim — were untracked at tip on 2026-08-15 under the
owner-signed BLOAT-B-5 item A2 conversion, with **re-fetch as the primary
recovery route**. The bytes are absent from a clone; the *design* is fully at
tip. `scripts/data/fetch_ercot_sced_corpus_shards.py` exists for exactly this.

So the funded work is a **restore into an existing corpus**, not the creation
of a new one. That is the single most consequential thing this session
establishes, and it is why nothing new needed a home, a gitignore entry, or a
placement adjudication.

### 2.2 Why the charter's per-day route was rejected

The charter proposed `fetch_ercot_60day_sced_gen_resource.py` with
`--resource-types` omitted, writing per-day files, and asked whether
`data/raw/ercot/SCED/` could host them given two flagged differences
(per-month vs per-day naming; raw-string vs coerced-float64 dtype). Both
differences are real. Neither is the decisive one:

* **`derive_ercot_sced_offer_wall._sced_source_files` selects the corpus by the
  glob `[0-9][0-9][0-9][0-9]-[0-1][0-9].part*.parquet` over `_CORPUS_DIRS`.**
  A file named `60_DAY_SCED_DISCLOSURE_..._<label>_<YYYY-MM-DD>.parquet` does
  not match it. The legacy sample-day glob it *might* have matched
  (`..._{year}_*.parquet`) is rooted at `data/raw/ercot/`, **not** the `SCED/`
  subdirectory, and requires `_{year}_` immediately after `Data`. So the
  charter's route, placed as proposed, yields a corpus **invisible to every
  existing consumer** — a dead 2.4 GB.
* The corrupting placement the SCED-CT README warns about is the *other* one:
  a scoped file at `data/raw/ercot/` whose label begins `<year>_` **does** match
  the legacy glob. Both failure modes are silent; the README's warning has been
  sharpened to name the actual mechanism.
* Choosing the corpus route makes the dtype and column-count differences
  **disappear** rather than needing handling: `fetch_ercot_sced_corpus_shards.py`
  writes the raw all-string 188-column copy, identical in kind to the tracked
  2023 window.

**Decision: restore into `data/raw/ercot/SCED/` in the existing
publication-month convention.** No new directory, no new naming family, no new
opt-in, no consumer change.

### 2.3 The two placement traps inside the chosen route, and how each was avoided

1. **`--pub-start` must be 2024-04-01, not the 2024-03-24 retention floor.**
   Verified by reading stamps out of the tracked shards: `2024-03.part0009-0016`
   already carry deliveries **2024-01-24..31**. The fetcher resumes off its own
   manifest, not off disk, so starting at the floor would append 8 duplicate
   parts and silently **double-weight** those days in every consumer that
   streams the corpus. Starting at 2024-04-01 leaves exactly the 700-day hole
   2024-02-01..2025-12-31 — which matches the A2 record's 700 untracked files
   exactly, an independent confirmation the window was identified correctly.
2. **The 27 RTC+B parts must be quarantined, and detected by CONTENT.** The
   fetcher writes flat; RTC+B-format parts (publications 2026-02-03 onward,
   deliveries 2025-12-05..31) lack `HASL`, a required read column of every
   corpus consumer, and **crash the derives** at the top level. They were
   identified by the missing column, not by assumed numbering — and the set so
   identified is exactly `2026-02.part0002-0027` + `2026-03.part0000`, the 27
   parts `rtcb-format-2026/README.md` names. Part numbering therefore
   reproduced the original run precisely.

---

## 3. The restore, and its verification

### 3.1 What was run

```bash
python scripts/data/fetch_ercot_sced_corpus_shards.py \
    --pub-start 2024-04-01 --pub-end 2026-03-01 \
    --max-delivery-date 2025-12-31 --manifest <scratch>/manifest.json
# then: move the 27 HASL-less parts into rtcb-format-2026/
```

Result line: `700 part(s) on manifest; 53 member(s) skipped; 0 unlisted
publication day(s)`. The 53 skips are supplemental-bundle members whose
delivery days were already covered by the ordinary pass (the 2024-10-04
32-member catch-up bundle and the 2026-02-23 16-member one), i.e. the
write-once guard working.

### 3.2 Coverage — complete, per delivery month

| delivery month | days | of | rows | | delivery month | days | of | rows |
|---|---|---|---|---|---|---|---|---|
| 2024-02 | 29 | 29 | 3,062,400 | | 2025-01 | 31 | 31 | 3,679,680 |
| 2024-03 | 31 | 31 | 3,316,755 | | 2025-02 | 28 | 28 | 3,361,920 |
| 2024-04 | 30 | 30 | 3,239,844 | | 2025-03 | 31 | 31 | 3,746,824 |
| 2024-05 | 31 | 31 | 3,383,712 | | 2025-04 | 30 | 30 | 3,662,202 |
| 2024-06 | 30 | 30 | 3,302,976 | | 2025-05 | 31 | 31 | 3,862,978 |
| 2024-07 | 31 | 31 | 3,441,907 | | 2025-06 | 30 | 30 | 3,756,294 |
| 2024-08 | 31 | 31 | 3,484,032 | | 2025-07 | 31 | 31 | 3,971,347 |
| 2024-09 | 30 | 30 | 3,422,784 | | 2025-08 | 31 | 31 | 4,003,392 |
| 2024-10 | 31 | 31 | 3,573,216 | | 2025-09 | 30 | 30 | 3,905,280 |
| 2024-11 | 30 | 30 | 3,484,455 | | 2025-10 | 31 | 31 | 4,059,555 |
| 2024-12 | 31 | 31 | 3,620,166 | | 2025-11 | 30 | 30 | 4,024,788 |
| | | | | | 2025-12 | 31 | 31 | 9,194,914 |

**700 parts, 88,561,421 rows, every month complete.** (2025-12's row count is
~2.5× its neighbours because 27 of its 31 days are RTC+B-format, which
publishes more rows per day.)

**Gaps, reported and never inferred.** Exactly one, and it is the known one:

* **deliveries 2024-01-10 .. 2024-01-23 (14 days)** — publications
  2024-03-10..23, aged out of the free MIS list before any fetch reached them.
  The credentialed `data.ercot.com` archive is the only remaining source and is
  **owner-declined** (`docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E).
  Measured today as still 14 days, not grown.

No other delivery day in 2022-12-31 .. 2025-12-31 is missing.

### 3.3 Structural audit — five checks, all pass

`scripts/data/audit_sced_corpus.py --check` over the whole corpus (1,023 parts:
323 tracked + 700 restored):

| check | result |
|---|---|
| duplicate delivery days | **0** of 1,083 distinct days |
| coverage gaps | 1 run, exactly the known 2024-01-10..23 |
| rule-22 locked-test leakage (deliveries > 2025-12-31) | **0** |
| RTC+B parts stranded at the top level | **0** (27 quarantined, 0 mis-quarantined) |
| restored parts carrying ≠ 1 delivery day | **0** (+60 in the early-2023 two-days-per-part months, by design) |

Column census `{107: 101, 108: 222, 188: 673, 193: 16, 195: 11}` — the tracked
post-slim shards at 107/108, the restored pre-RTC+B at the raw 188, the RTC+B
quarantine at its documented 193/195 variants. Corpus on disk: 3,069.8 MiB
(tracked 728.4 + restored 2,341.5).

### 3.4 The charter's regression requirement — PASSES BYTE-IDENTICALLY

The charter required that the shared consumer's class shares on the **old span**
be unchanged after the new shards land. Run before the restore and again after,
over the same 323 tracked shards:

```
scripts/data/derive_ercot_sced_offer_wall.py --years 2023
BEFORE sha256 6601a821c533acc0e35bfadff52b2d3eb162a2fe19ac1c9edaaf1ea233caf2f4
AFTER  sha256 6601a821c533acc0e35bfadff52b2d3eb162a2fe19ac1c9edaaf1ea233caf2f4   IDENTICAL
```

This is also true *by construction* and the empirical check confirms the
reasoning: `_sced_source_files(2023)` selects publication months
`[2023-02 .. 2024-03]`, and every restored shard is publication 2024-04 or
later, so the delivery-2023 file list cannot change.

**Consumability of the new span, demonstrated (not committed).** The same
derive over the restored window produces a dense, fully-populated surface in
**both** forward years, across all seven net-load bins:

| year | class | p50 offer multiplier by bin | intervals by bin |
|---|---|---|---|
| 2024 | CC | 10.478, 11.500, 12.523, 13.988, 15.283, 17.647, 20.835 | 8579, 8468, 6808, 3340, 3364, 2236, 900 |
| 2024 | CT | 12.037, 12.743, 14.540, 16.209, 16.414, 18.894, 25.079 | (same) |
| 2025 | CC | 8.146, 9.806, 10.782, 11.573, 12.249, 13.513, 13.712 | 7700, 7920, 6619, 3332, 3339, 2396, 1140 |
| 2025 | CT | 8.677, 9.776, 10.977, 13.248, 14.177, 14.561, 22.182 | (same) |

Before the restore, `_sced_source_files` found too few delivery months for
2024/2025 to clear `_CORPUS_MIN_DELIVERY_MONTHS` and fell back to the legacy
sample-day extracts; it now selects the corpus. **The committed frozen artifact
was NOT re-derived and NOT touched** — rule 20 `[R-FROZEN-DERIVE]` puts a
re-derivation behind its own authorization, and this session has none. The runs
above went to scratch purely to prove the restored corpus reads.

---

## 4. The `SHA256SUMS.txt` correction

The SCED README's recovery route 2 instructed a restorer to "re-run
`slim_ercot_dam_disclosure.py --sced-only` and judge the result against
`SHA256SUMS.txt` (the manifest is the byte truth)". **That is not achievable**,
and a future restoring session following it would have concluded, wrongly, that
its restore had failed.

Measured:

| | sha256 |
|---|---|
| tracked `2024-03.part0016.parquet` rehashed vs its manifest line | **matches exactly** (`a8c53a34…`) |
| manifest line for `2024-04.part0000.parquet` | `11c02e4e…` |
| re-fetch + `slim_ercot_dam_disclosure.py --sced-only` of the same day | `93f9d398…` |

The cause is not corruption: the tracked shards carry
`created_by = parquet-cpp-arrow version 24.0.0`, this environment writes
`25.0.1`, and parquet encoding is writer-version specific. Content, row counts
and column sets reproduce; bytes cannot.

**Disposition.** `SHA256SUMS.txt` is left untouched and keeps its real job — the
identity record of the *original* bytes. Added alongside it:

* **`data/raw/ercot/SCED/RESTORE-ROWCOUNTS.txt`** (tracked, 700 lines +
  provenance header): per part, the delivery day(s), row count and column
  count — all writer-independent. This is what a restore is judged against.
* **`scripts/data/audit_sced_corpus.py`** — writes it (`--write-manifest`),
  verifies a corpus against it (`--check`), and runs the five structural checks
  of §3.3. Read-only over `data/raw/` except for the manifest write; it never
  moves, edits or deletes a payload.

---

## 5. What a future lane can now identify — and what this does NOT buy

**Can.** The corpus carries, per resource per ~5-minute SCED interval over
deliveries 2024-02-01..2025-12-31: `Telemetered Resource Status`, `Base Point`,
`Output Schedule`, the full `HSL`/`HASL`/`HDL`/`LSL`/`LASL`/`LDL` telemetry
envelope, `Telemetered Net Output`, the SCED1/SCED2 as-dispatched energy offer
curves, the submitted three-part offer, and per-service AS responsibilities —
**at unit grain, for every resource, across the whole forward span**. That is
the object ercot-245 §3/§4.1 named as the only residue a future instrument
could express: **per-UNIT forward-regime commitment state** — startup and
notice cycles, which cold unit comes on when, unit-level min-run and
min-down conduct observed rather than transferred.

Note it lands **raw and un-slimmed** (188 columns), deliberately: the 108-column
`SCED_KEEP` projection drops `SCED1 Curve-*`, `Min Gen Cost` and
`Start Up Hot/Inter/Cold Offer`, which are precisely the startup-economics
columns a commitment-state lane would want. Keeping them cost 0.5 GiB of
ephemeral disk and nothing in the repo (the payload is gitignored either way).

**Cannot — stated so the next reader is not misled.** Per ercot-245 §4.1 and
its D-V5 null, this corpus does **not** buy a better class-share table. A
class-grain re-identification on 2024/2025 data would inherit the same FORM
defects ercot-245 measured at census (§2.2–2.3): reality's per-class online
shares at missed events are statistically indistinguishable from same-net-load
ordinary hours (CC 0.805 vs 0.807, ST 0.553 vs 0.589, COAL 0.715 vs 0.737,
NUC 0.966 vs 0.982), so **no net-load-conditioned class-share bound, however
identified, carries an event-discriminating signal**. That lane died at census
and this intake does not reopen it. K-A additionally stands: the SCED `GS*`
restype universe cannot express the model's `ST_GAS` class, and more data at
the same grain does not repair a mis-scoped universe.

Two further standing limits inherited unchanged: every existing corpus consumer
**stops at delivery 2025-12-04** (the RTC+B boundary; later days are readable
only through `scripts/lib/sced_rtcb_adapter`), and deliveries 2024-01-10..23
are permanently absent on the free path.

---

## 6. Deliverables

| file | status |
|---|---|
| `data/raw/ercot/SCED/RESTORE-ROWCOUNTS.txt` | **new, tracked** — the writer-independent acceptance manifest (700 parts) |
| `scripts/data/audit_sced_corpus.py` | **new** — writes/checks it + the five structural checks |
| `data/raw/ercot/SCED/README.md` | recovery route 2 rewritten: verified command, the `--pub-start` trap, the RTC+B move, the SHA256SUMS correction, the measured retention floor, raw-vs-slim guidance |
| `data/raw/ercot/SCED-CT/README.md` | stale coverage table corrected; scope warning sharpened to the real glob mechanism; all-resource sibling pointed to |
| `docs/FINDING-ercot248-sced-allresource-intake-2026-08-31.md` | this record |
| `.gitignore` | **unchanged** — the existing owner-signed A2 globs already cover every restored shard (verified with `git check-ignore`; working tree clean) |
| `data/raw/ercot/SCED/SHA256SUMS.txt` | **unchanged, deliberately** — see §4 |

The 2,341.5 MiB of restored payload is gitignored and lives only in this
container; the deliverable is the verified, reproducible route to it.

---

## 7. Hygiene

Zero solves; zero scoring; zero registration (rule 15 not triggered — nothing
produced to register); no keeper, shard, marker, determination or matrix cell
moved (rule 28 not triggered — no mechanism proposed or tested); no
`ScenarioConfig` field (rule 24, 26); ERCOT surfaces only (rule 25); the frozen
derived artifacts **not** re-derived (rule 20 — the 2024/2025 derive of §3.4 went
to scratch, and the committed artifact is untouched); `data/raw/` treated as
immutable — new files only, and the only move was of files this session had
just written, into the layout their own README mandates; rule 22 upheld at every
gate (`--max-delivery-date 2025-12-31` left at its default and never overridden,
`--holdout-authorized` never passed, no locked-test year solved/scored/
registered, and the result independently re-checked for leakage in §3.3); data
intake itself needs no marker (rule 22's spend-only clause); the ercot-244 and
ercot-163 DO-NOT-REDO records honoured (neither re-litigated, neither's variant
touched); no GitHub Actions workflow created and no CI job used — the fetch ran
in-session (~2.9 h, single-threaded); pushed on the designated branch, rebased
on a freshly fetched `origin/main`, with blob verification on every file ≥300
lines.
