# miso-m2m-flowgates raw-mirror restoration — intake record (2026-08-30)

**Lane:** MISO M2M flowgates raw-mirror intake. **Authority:** owner card
ruling 2026-08-30 (director sitting): `scripts/regenerate_clean.py` runs
50/51 because `miso-m2m-flowgates` is the one datatype with no raw mirror
under `data/raw` — restore full from-source reproducibility. **NO LP, no
`ScenarioConfig` change, no keeper/matrix impact (rule 15 not engaged); no
solve code touched.**

## 1. Provenance — why there was no mirror

The datatype's intake was executed by session **miso-176 (2026-08-22)** under
the full data-intake contract — schema
(`data/dictionary/schema/miso-m2m-flowgates.schema.yaml`), fetch
(`scripts/data/fetch_miso_m2m_flowgates.py`), curate
(`scripts/data/curate_miso_m2m_flowgates.py`, registered in
`regenerate_clean.DATATYPES`), tmp-CLEAN_DIR tests
(`tests/curation/test_curate_miso_m2m_flowgates.py`), dictionary entry —
landing on `main` in merge `02e3f0f` (PR #4285, 2026-08-25; the log's cited
intake commit `9d4681c` is the squashed branch head, not on `main`
first-parent). Narrative: `docs/calibration-log/miso.md` miso-176;
measurement record `FINDING-miso176-m2m-seam-binding-reality-2026-08-22.md`.

**The missing mirror was a deliberate posture, not an accident:** miso-176
gitignored the bulk mirrors (`data/raw/miso-m2m-flowgates/*` with only
`README.md` tracked) on the bc_HIST precedent, leaving the fetch script as
the sole reproducibility path and recording each mirror's raw-csv
sha256/bytes/rows in the raw README. Consequence: the raw could not be
materialized by hydration on ANY tree (it was absent from git, not merely
from a profile), so even a full clone regenerated only 50/51 datatypes —
the operational caveat carried by
`docs/FINDING-entry-signal-forward-expectation-2026-08-25.md`,
`FINDING-capx-d2-nyiso-extcap-2026-08-25.md` and
`FINDING-capx-d14-neiso-t1x-2026-08-30.md` (all three now annotated).
Two things the bc_HIST precedent did not carry over here: the m2m corpus is
only **~5.4 MB gzipped total** (bc_HIST raw is 20–70 MB/yr), and this
datatype is a **registered `regenerate_clean` datatype** whose absence broke
the 51/51 invariant, which bc_HIST's gitignored mirrors do not (their
curated form ships tracked).

## 2. What this session changed

1. **Mirrors fetched and tracked** — `data/raw/miso-m2m-flowgates/
   M2M_Settlement_srw_{2023,2024,2025}.csv.gz` committed; the
   `data/raw/miso-m2m-flowgates/*` gitignore block retired (replaced by a
   do-not-re-add note). `SHA256SUMS.txt` added (committed-file identity,
   house `# sha256  size_bytes  file` layout).
2. **Deterministic gzip container** in `fetch_miso_m2m_flowgates.py`
   (mtime=0, empty filename field): a `--force` refetch of an unchanged
   source now reproduces the committed mirror byte-for-byte, so `git diff`
   clean after a refetch certifies the source is unrestated; a dirty diff is
   an intake event. Docstring updated from the gitignored-era wording.
3. **Raw README rewritten** under corpus conventions: payload-posture note
   (TRACKED, superseding the miso-176 posture), verified source-URL table
   (unchanged fetch-time identities), re-fetch command, re-verification
   record; the schema header comment's "gitignored" wording fixed. The
   dictionary narrative needed no change (never mentioned the posture).
4. **`ALL_DATATYPES` snapshot re-frozen** in
   `tests/curation/test_clean_io.py`: miso-176 registered the datatype in
   `regenerate_clean.DATATYPES` without extending the test's frozen
   snapshot, so `TestRegenerateEntrypoint::test_datatype_list_matches_schemas`
   had been failing on `main` since `02e3f0f` (the drift class
   `docs/handoffs/fast-tier-triage-2026-07-26.md` documents). One list entry
   added; pre-existing failure, not introduced by this lane.
5. **Standing 50/51 notes annotated** in the three FINDING docs above.

Deliberately NOT done: no curate-logic change (the write_clean seam, the
per-year partitioning and the missing-mirror skip/exit-1 behavior are
untouched — the wiring was already contract-complete; the only gap was the
data); no test rewrite (see §4); no touch of the DATA-NEEDED family (daily
FFE files, allocations, registry snapshots — still deliberately
un-mirrored); no other ISO's surfaces.

## 3. Verification (rule 14 — nothing shaped)

- **Source identity:** all three URLs refetched 2026-08-30; raw-csv sha256,
  byte size and line count **identical** to the miso-176 fetch-time table
  (`bcf31ce0…` / `9b2af9c9…` / `d992560c…`) — MISO has not restated any
  file. The committed `.csv.gz` decompress to exactly those raw bytes
  (`zcat | sha256sum` verified).
- **Clean identity:** identical raw bytes + unchanged curate code ⇒ the
  regenerated clean partitions are identical to the previously-used data.
  **Delta against the primary source: zero.**
- **Regeneration accounting:** `regenerate_clean.py miso-m2m-flowgates`
  succeeds; rows 124,821 / 162,394 / 181,989 (= source lines − header);
  `validate_clean` passes per partition.
- **Semantics re-checked against the documented source characteristics:**
  distinct hours 8,760 / 8,784 (leap) / 8,760 — full-year coverage, no DST
  gap/dup, confirming the fixed-EST clock; seams exactly {PJM, SWPP}
  (2025: 41,971 / 140,018 rows); both-sides-zero shadow-price share
  0.824 / 0.833 / 0.860 (README's "~82–86 %"); flowgate counts
  309 / 385 / 401 (matches miso-176's log line).
- **Frame digests** (sha256 over canonical CSV serialization of the sorted
  clean frame, for future identity audits):
  - 2023 `38895becac336fc56945706cd9d7617df268384ca19f5822fb5ddbf5eda455d8`
  - 2024 `c590359704112e64db406052a58af268abc2e5fe3cab7c0f4efb646852a9728f`
  - 2025 `dde4f1df21bb9cdfadc7e62627bc46f2d6b2306127917b441cabb15865032538`
- **Tests:** `test_curate_miso_m2m_flowgates.py` (6),
  `test_derive_miso_hub_lmp.py`, `test_derive_miso_loss_surface.py`,
  `test_clean_io.py` — 40/40 pass (the one prior failure was the §2.4
  snapshot drift).

## 4. Session note (honest record)

This session initially re-wrote
`tests/curation/test_curate_miso_m2m_flowgates.py` from scratch after two
truncated directory listings hid the existing miso-176 test; the mistake was
caught the same session by tracing the intake's landing commit, and the
original was restored verbatim from HEAD before any commit (`git diff` on
the file: empty). The settled miso-176 test stands untouched — its coverage
(HE→EST→UTC incl. HE 24, all four monitor/counterparty seam combos, schema
round-trip with NO-RTO NaNs, year/duplicate guards, missing-mirror skip)
already satisfies the intake contract, and test expansion was not this
lane's charter.

## 5. Operational effect

- A fresh clone whose hydration covers the MISO subtrees (`--profile miso`
  or wider; the mirrors ride the derived profile's `miso` name token) now
  rebuilds `miso-m2m-flowgates` from source: **the 50/51 exception is
  closed — a fully-hydrated tree regenerates 51/51.**
- Partial-profile trees behave as before for every datatype: a profile that
  does not hydrate a datatype's raw cannot regenerate it; m2m is no longer
  special.
- Re-fetch remains quarantine-gated (train window 2023–2025;
  `--allow-out-of-train` + owner authorization for anything else, rule 22).
