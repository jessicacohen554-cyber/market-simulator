# FINDING — capx gate-(a) re-key r#65: chartered on SIX red rows; audit lane Y-29 landed the six re-keys mid-lane, then SPP went red AGAIN on the spp-78 promotion before the push — this lane re-keys SPP (the one row red at its HEAD), verifies Y-29's five, re-keys the six row-level `keeper` fields Y-29 left stale, restores one boolean, and records the THIRTY-TWO-promotion chain the rows were stale across (2026-09-24)

**Lane:** capx GATE-(a) RE-KEY r#65 (pack `docs/handoffs/capx-director-prompt-pack-2026-08.md`
"GATE-(a) RE-KEY r#65"; ledger §0bj). **Model:** Fable. **Data profile:** code.
**Branch:** `claude/capx-gate-a-rekey-r65`, started from `6640becc` (= desk pin `40f4ed7a` + the
r#65 charter commit), rebased onto `origin/main` **`3affcd71`** before the first edit and onto
**`8ebb7805`** immediately before the push (the charter's score-after-rebase duty — and a promotion
DID land in between, §1). Every fact below was read live at `8ebb7805` unless a pin is named.
**Scope:** ONE ACT, ZERO LP. No solve, no scoring, no registration, no keeper edit, no marker edit,
no other desk's file. Edits: `frontend/data/forecast/program-status.json` (thirteen changed lines,
all targeted string edits, §3) and this record. **Nothing solved, scored or registered; no verdict
computed.**

---

## 0. The result in one paragraph

`scripts/check_gate_a_provenance.py` is **EXIT 0 on all seven rows** at `8ebb7805` after this
lane's edit. The charter's six red rows were re-keyed **by someone else, mid-lane**: audit lane
**Y-29** (commit `9c99bd47`, PR #6570, merged 2026-09-24 at `origin/main a4708b25`;
`docs/handoffs/FINDING-y29-promotion-provenance-2026-09-24.md`) re-keyed all six gate-(a) rows onto
their live keepers and re-derived SPP's leg (a) **fail → pass** on the literal §2.1b(2)(a) test, so
the guard read EXIT 0 at this lane's first rebase (`3affcd71`). Then, before the push, the **SPP-78
promotion** landed (`8adbc30b`, merged `ca9e41e6` in PR #6580) without touching this file, and SPP
went **red again on identity** (`2026-09-22-hydro-5-spp-floor` → `2026-09-24-spp78-hr-span`) at
`8ebb7805` — the twentieth firing of the guard, and the first row to go stale twice in one day. **That
one row is what this lane re-keyed** (§3, §5). Under the charter's stop gate — *an ISO already green at
your HEAD is not re-keyed, because asserting a supersession that did not happen is a false record* —
the **other five rows'** gate-read leaves (`detail`, `read_live_at`, `corrected_by`, `status`,
`closed_on`, `note`) are **Y-29's and byte-unchanged here**. What this lane did besides SPP, all of it
inside the one file the charter allows: (1) **verified** every Y-29 row against the live stores (§2);
(2) re-keyed the six rows' **top-level `isos.<ISO>.keeper` fields**, which Y-29 §1.4 found stale on
all six and routed to the forecast desk (§3); (3) restored `isos.SPP.marker_complete` from the string
`"True"` to the JSON boolean the field carries everywhere else (§3); (4) re-stamped the file-level
`gate_a_provenance` derivation block (§3); and (5) recorded, per ISO, the **full chain of promotions**
each row was stale across — which Y-29's single-arrow rows do not state — with the promotion
instruments named as documents (§4). **SPP's leg (a) moved fail → pass at Y-29 because the marker
moved, not because any lane did; this lane's SPP re-key moves no verdict** (§5). **No other leg
status, determination or grade moves.** Two things are reported and deliberately not repaired (§6).

---

## 1. Gate exit codes, in order

| where | HEAD | `check_gate_a_provenance.py` |
|---|---|---|
| charter pin (desk read) | `40f4ed7a` | **EXIT 1** — six superseded keepers + SPP marker claim `complete=False` vs file `True` |
| this lane's first run, before rebase | `6640becc` | **EXIT 1** — the same seven problems, reproduced verbatim (§1.1) |
| after rebase onto `origin/main`, before any edit | `3affcd71` | **EXIT 0** (7 rows) — Y-29's `9c99bd47` is between the two pins |
| after this lane's first edit (six `keeper` fields, one boolean, the stamp) | `3affcd71` + edit | **EXIT 0** (7 rows) |
| after the pre-push rebase, before the second edit | `8ebb7805` | **EXIT 1** — **SPP** cites `2026-09-22-hydro-5-spp-floor`; live keeper `2026-09-24-spp78-hr-span` (PR #6580 landed mid-lane) |
| after this lane's SPP re-key | `8ebb7805` + edit | **EXIT 0** (7 rows) |
| tests | — | `tests/scoring/test_gate_a_provenance.py` + `tests/scoring/test_forecast_staleness.py`: **41 passed** at each edit |

### 1.1 What the guard said at `6640becc` (the nineteenth firing), verbatim ids

| ISO | row cited (superseded) | live designated keeper | marker claim |
|---|---|---|---|
| CAISO | `2026-09-12-caiso-275-gascoupling` | `2026-09-20-caiso-290-leftedge` | ok |
| ERCOT | `2026-09-09-ercot265-receipts-fallback` | `2026-09-19-ercot266-mer-five-year` | ok |
| NEISO | `2026-09-09-neiso-108-fuelvintage` | `2026-09-22-hydro-5-neiso-ror` | ok |
| NYISO | `2026-09-09-nyiso-221-fuelvintage-span` | `2026-09-22-nyiso-hydro3-ror-split` | ok |
| PJM | `2026-09-11-pjm-d4-4-gasoutage` | `2026-09-23-pjm-h19-dbs-span` | ok |
| SPP | `2026-09-12-spp-36-shortwindow-span` | `2026-09-22-hydro-5-spp-floor` | **row `complete=False final=False`; file `complete=True final=False`** |

The charter's ids were **right** at my HEAD on every row (the charter's "do not trust those ids"
instruction was obeyed: each was re-read from `keepers/<ISO>.json`, and each agreed). MISO was
green throughout (its row re-keyed by its own promoting lanes: miso-267 at `dd261a33`, miso-268 at
`674b5cc6`).

---

## 2. The verification of Y-29's rows (every fact read live at `3affcd71`)

Read per ISO: keeper id from `frontend/data/backcast/keepers/<ISO>.json`; BOTH blocks of
`frontend/data/backcast/calibration-complete.json` (`complete` membership = {CAISO, ERCOT, NEISO,
NYISO, PJM, SPP}; `final` EMPTY; `withdrawn` EMPTY); determination from the committed status
sidecar `frontend/data/backcast/status/<ISO>.js` (NOT a re-score); registry years and bundle from
`frontend/data/backcast/registry/<id>.json`. Every Y-29 row agrees with all four instruments, and
the `sha256[:12]` of the prior detail each Y-29 row quotes reproduces from `6640becc`:

| ISO | live keeper | registry years · bundle | sidecar determination (rubric v3.8) | `complete` entry `keeper` | Y-29 prior-detail sha reproduces |
|---|---|---|---|---|---|
| CAISO | `2026-09-20-caiso-290-leftedge` | 2022–2025 · `xiso8_leftedge_span` | CALIBRATED 8/7/1/0 (2022/23/24 CALIBRATED; 2025 CALIBRATED-WITH-CAVEATS, fuelmix/sysvol unscored) | same | `0fb07131d4d5` ✓ |
| ERCOT | `2026-09-19-ercot266-mer-five-year` | 2021–2025 · `ercot_mer20260919_five_year` | CALIBRATED 8/7/1/0 (ISO-level AND registered, agreeing; config-partition rollup; all five years CALIBRATED) | same | `969cdb2096ed` ✓ |
| NEISO | `2026-09-22-hydro-5-neiso-ror` | 2020–2025 · `hydro5_neiso_ror_span` | CALIBRATED 8/7/1/0 (2020–2024 CALIBRATED; 2025 CALIBRATED-WITH-CAVEATS) | same | `1ce8e42174a7` ✓ |
| NYISO | `2026-09-22-nyiso-hydro3-ror-split` | 2022–2025 · `hydro3_nyiso_ror_span` | **NOT-YET** 8/6/0/2 (2023 NOT-YET: fuelmix, price_tail; 2022/2024 CALIBRATED; 2025 CALIBRATED-WITH-CAVEATS) | same; entry's own `determination` = `"NOT-YET"` | `cd3c899387b1` ✓ |
| PJM | `2026-09-23-pjm-h19-dbs-span` (+ folded `…-dbs-touchpoint` 2020–2022) | 2023–2025 · `pjm_h19_dbs_span` | CALIBRATED 8/8/0/0 (touchpoint 2020/21/22 NOT-YET, reported under rule 30(c)) | same | `9bfd2a5d7160` ✓ |
| SPP at `3affcd71` (Y-29's row) | `2026-09-22-hydro-5-spp-floor` (+ folded `…-spp-rung` 2019–2022) | 2023–2025 · `hydro5_spp_floor_span` | CALIBRATED 8/7/1/0 (rung 2019 CALIBRATED; 2020/21/22 NOT-YET, reported under rule 30(c)) | same | `8b749c0fbba8` ✓ |
| **SPP at `8ebb7805` (this lane's row)** | **`2026-09-24-spp78-hr-span`** (+ folded `2026-09-24-spp78-hr-rung` 2019–2022, `holdout.keeper` = the span) | 2023–2025 · `spp78_hr_span` | CALIBRATED 8/7/1/0, rubric v3.8, sidecar generated 2026-09-24 17:39 (2023/2024 CALIBRATED; 2025 CALIBRATED-WITH-CAVEATS; rung 2019 CALIBRATED, 2020 NOT-YET price_mean+price_shape, 2021 NOT-YET price_shape, 2022 NOT-YET fuelmix+dispatch_corr) | same (`complete.SPP.keeper` = spp78; `rekeyed_spp78` present, determination re-verified CALIBRATED) | — (Y-29's detail carried verbatim beneath the new head) |

Y-29's read pin `a4708b25` and this lane's first pin `3affcd71` differ only by merges that did not
touch the keeper shards or the marker file (verified: `git diff --stat 6640becc 3affcd71 --
frontend/data/backcast` shows two run payloads, `status/NEISO.js` regenerated by neiso-113 on the
repaired EIA-923 frame with the keeper re-scored CALIBRATED unchanged, and no shard/marker change).
Between `3affcd71` and the push pin `8ebb7805` exactly one store moved: SPP's — `keepers/SPP.json`,
`complete.SPP`, `status/SPP.js` and the two SPP registry sidecars, all in `8adbc30b` / `ca9e41e6`
(PR #6580). Neither commit touches `program-status.json`.

### 2.1 Before / after `detail` head, verbatim (before = `6640becc`; after = Y-29's row at `3affcd71`, byte-unchanged by this lane)

**CAISO** — before (status pass): `keeper 2026-09-12-caiso-275-gascoupling (full-span 2023-2025, rule 16 [R-ALLYEARS]; registry years [2023, 2024, 2025], bundle results/calibration/caiso275_B_gascoupling_span); determination CALIBRATED (rubric v3.7; grade summary scored 8 / target 7 / ledgered 1 / fails 0; the single ledgered caveat is C3c price tail / scarcity, non-downgrading under rubric v3.3). marker complete=True final=False`
— after (status pass): `keeper 2026-09-20-caiso-290-leftedge (registry years [2022, 2023, 2024, 2025], bundle results/calibration/xiso8_leftedge_span; covers the train span 2023-2025, rule 16 [R-ALLYEARS]); determination CALIBRATED (grade summary scored 8 / target 7 / ledgered 1 / fails 0; read live from frontend/data/backcast/status/CAISO.js, NOT re-scored); marker complete=True final=False`

**ERCOT** — before (status pass): `keeper 2026-09-09-ercot265-receipts-fallback (five-year run 2021-2025, covering the full train span 2023-2025, rule 16 [R-ALLYEARS]; registry years [2021, 2022, 2023, 2024, 2025], bundle results/calibration/ercot265_receipts_five_year); determination CALIBRATED at ISO level (rubric v3.7; grade summary scored 8 / target 7 / ledgered 1 / fails 0; … read live from frontend/data/backcast/status/ERCOT.js, generated 2026-09-10 05:07, and NOT re-scored here); marker complete=True final=False`
— after (status pass): `keeper 2026-09-19-ercot266-mer-five-year (registry years [2021, 2022, 2023, 2024, 2025], bundle results/calibration/ercot_mer20260919_five_year; covers the train span 2023-2025, rule 16 [R-ALLYEARS]); determination CALIBRATED (grade summary scored 8 / target 7 / ledgered 1 / fails 0; read live from frontend/data/backcast/status/ERCOT.js, NOT re-scored); marker complete=True final=False`

**NEISO** — before (status pass): `keeper 2026-09-09-neiso-108-fuelvintage (full-span 2023-2025, rule 16); determination CALIBRATED (rubric v3.6; grade summary scored 8 / target-grade 7 / commercial-grade 0, 0 FAILs, 1 ledgered caveat — C3c price tail / scarcity, RT hourly; C1 all 12/12, free 8/8); marker complete=True final=False`
— after (status pass): `keeper 2026-09-22-hydro-5-neiso-ror (registry years [2020, 2021, 2022, 2023, 2024, 2025], bundle results/calibration/hydro5_neiso_ror_span; covers the train span 2023-2025, rule 16 [R-ALLYEARS]); determination CALIBRATED (grade summary scored 8 / target 7 / ledgered 1 / fails 0; read live from frontend/data/backcast/status/NEISO.js, NOT re-scored); marker complete=True final=False`

**NYISO** — before (status pass): `keeper 2026-09-09-nyiso-221-fuelvintage-span (full-span 2023-2025, rule 16); determination CALIBRATED (rubric v3.6; grade 7 of 8, fails 0, single ledgered C3c caveat; …); marker complete=True final=False`
— after (status pass): `keeper 2026-09-22-nyiso-hydro3-ror-split (registry years [2022, 2023, 2024, 2025], bundle results/calibration/hydro3_nyiso_ror_span; covers the train span 2023-2025, rule 16 [R-ALLYEARS]); determination NOT-YET (grade summary scored 8 / target 6 / ledgered 0 / fails 2; read live from frontend/data/backcast/status/NYISO.js, NOT re-scored); marker complete=True final=False`

**PJM** — before (status pass): `keeper 2026-09-11-pjm-d4-4-gasoutage (full-span 2023-2025, rule 16; bundle results/calibration/pjm_d4_4_A); determination CALIBRATED; marker complete=True final=False`
— after (status pass): `keeper 2026-09-23-pjm-h19-dbs-span (registry years [2023, 2024, 2025], bundle results/calibration/pjm_h19_dbs_span; covers the train span 2023-2025, rule 16 [R-ALLYEARS]); determination CALIBRATED (grade summary scored 8 / target 8 / ledgered 0 / fails 0; read live from frontend/data/backcast/status/PJM.js, NOT re-scored); marker complete=True final=False`

**SPP** — before (status **fail**): `keeper 2026-09-12-spp-36-shortwindow-span (full-span 2023-2025, rule 16 [R-ALLYEARS]; registry years [2023, 2024, 2025], bundle results/calibration/spp36_span), promoted 2026-09-12 by lane SPP-36 … SPP still has NO `complete` entry and this promotion deliberately does NOT create one, so marker complete=False final=False`
— after Y-29, at `3affcd71` (status **pass**): `keeper 2026-09-22-hydro-5-spp-floor (registry years [2023, 2024, 2025], bundle results/calibration/hydro5_spp_floor_span; covers the train span 2023-2025, rule 16 [R-ALLYEARS]); determination CALIBRATED (grade summary scored 8 / target 7 / ledgered 1 / fails 0; read live from frontend/data/backcast/status/SPP.js, NOT re-scored); marker complete=True final=False`
— **after THIS LANE, at `8ebb7805` (status pass, unmoved):** `keeper 2026-09-24-spp78-hr-span (full-span 2023-2025, rule 16 [R-ALLYEARS]; registry years [2023, 2024, 2025], bundle results/calibration/spp78_hr_span; the held-out 2019-2022 ride 2026-09-24-spp78-hr-rung, stamped to it under rule 30 [R-TOUCHPOINT-FOLD] (a)); determination CALIBRATED (rubric v3.8; grade summary scored 8 / target 7 / ledgered 1 / fails 0; C1 / C2 / C3a / C3b / C4 / C6 / C8 PASS and C3c price tail / scarcity the single ledgered caveat, non-downgrading under rubric v3.3; per year 2023 CALIBRATED / 2024 CALIBRATED / 2025 CALIBRATED-WITH-CAVEATS on unscored fuelmix and sysvol; the rung reads 2019 CALIBRATED / 2020 NOT-YET (price_mean, price_shape) / 2021 NOT-YET (price_shape) / 2022 NOT-YET (fuelmix, dispatch_corr), reported and never downgrading under rule 30(c); read live from frontend/data/backcast/status/SPP.js, generated 2026-09-24 17:39, and NOT re-scored here); marker complete=True final=False` — followed by the RE-KEYED / OWNER INSTRUMENT / PROMOTION INSTRUMENT / promoter-miss / verdict-unmoved sentences, then `PRIOR DETAIL, CARRIED VERBATIM AND UNCHANGED BELOW (audit lane Y-29's row of 2026-09-24 at a4708b25; this row is a chain): ` + Y-29's detail verbatim. SPP's `read_live_at` is now `8ebb7805 (…)` and its `corrected_by` opens with this lane's sentence and continues `Supersedes: audit lane Y-29 (2026-09-24), re-key from 2026-09-12-spp-36-shortwindow-span -> 2026-09-22-hydro-5-spp-floor; …` — the chain convention the charter's method §3 requires.

Every OTHER after-row's `read_live_at` is `a4708b25 (… read live by lane Y-29 …)` and its `corrected_by`
is `audit lane Y-29 (2026-09-24), re-key from <old> -> <live>; docs/handoffs/FINDING-y29-promotion-provenance-2026-09-24.md`.
The `corrected_by` chains that stood at `6640becc` (the r#64 stamp on ERCOT/CAISO, the promoting-lane
stamps on NEISO/NYISO, FR-21 on PJM, SPP-45 on SPP) were **replaced, not prepended to**, by Y-29; the
prior text is in git at `6640becc` and its sha is quoted in each Y-29 row. This lane did not re-touch
the five: prepending a second "Supersedes:" on a row this lane did not re-key would assert an act that
did not happen.

---

## 3. What this lane edited — one file, `git diff` = 13 insertions / 13 deletions

Edited with position-scoped `str.replace` on uniquely-anchored lines (each anchor asserted to occur
exactly once; the three SPP leaves scoped to the SPP `a_keeper_marker` block by line index because
Y-29's `read_live_at` string is identical on six rows), **never a `json.dumps` round-trip**; the file is
ASCII-escaped and stays so; every other byte is identical.

| leaf | before | after | why it is this lane's |
|---|---|---|---|
| `isos.SPP.gate.a_keeper_marker.detail` | Y-29's row keyed to `2026-09-22-hydro-5-spp-floor` (§2.1) | new head keyed to `2026-09-24-spp78-hr-span` (§2.1), Y-29's detail carried verbatim beneath | **the one row red at this lane's HEAD** — the SPP-78 promotion (`8adbc30b` / `ca9e41e6`, PR #6580) landed between the two rebases and did not touch this file |
| `…a_keeper_marker.read_live_at` | `a4708b25 (… lane Y-29 …)` | `8ebb7805 (origin/main at the read; keeper shard + BOTH blocks of calibration-complete.json + the committed status sidecar + the registry sidecars, all read live in this session - no re-score, no verdict computed)` | as above |
| `…a_keeper_marker.corrected_by` | `audit lane Y-29 (2026-09-24), re-key from …spp-36… -> …hydro-5-spp-floor; …` | this lane's sentence + `Supersedes: ` + Y-29's text verbatim | as above; charter method §3 |
| `…a_keeper_marker.status`, `gate.closed_on`, `gate.note`, row `note` | pass / `[b, c, d]` / Y-29-prefixed | **unchanged** | the verdict does not move on a keeper re-key |
| `isos.CAISO.keeper` | `2026-09-06-caiso-260-b1-demand` | `2026-09-20-caiso-290-leftedge` | charter method §2 names the row's top-level `keeper` field; Y-29 §1.4 found it stale on all six and routed it "to the forecast desk to confirm its meaning or re-key it". Its meaning is fixed by this file's own `refresh` block (FFR-3A-3: *"Criterion (a) keeper + marker + determination for all six ISOs, read LIVE"*) and by the MISO precedent (`1b175ce9`, the charter's worked example, which re-keyed it) — it is the gate-(a) keeper. No script or page reads it (grepped `scripts/`, `docs/codebase-site/`, `frontend/`, `tests/`). |
| `isos.ERCOT.keeper` | `2026-08-25-234-eastex-identity` | `2026-09-19-ercot266-mer-five-year` | as above (this one was FOUR keepers stale: 234 → ercot248 → ercot256 → ercot261 → ercot265 → ercot266) |
| `isos.NEISO.keeper` | `2026-09-06-neiso-106-fossil-offer` | `2026-09-22-hydro-5-neiso-ror` | as above |
| `isos.NYISO.keeper` | `2026-09-09-nyiso-221-fuelvintage-span` | `2026-09-22-nyiso-hydro3-ror-split` | as above |
| `isos.PJM.keeper` | `2026-08-15-pjm-162-inputclock` | `2026-09-23-pjm-h19-dbs-span` | as above |
| `isos.SPP.keeper` | `2026-09-07-spp-2-crosswalk-hydro` | `2026-09-24-spp78-hr-span` (set to hydro-5 at the first edit, then to spp78 at the second) | as above |
| `isos.SPP.marker_complete` | `"True"` (a JSON **string**, written by Y-29; the field was the boolean `false` at `6640becc`) | `true` (boolean) | type restoration: every other row carries a boolean; a string is truthy in JS and Python so nothing broke, but a records file should not carry two types in one field |
| `gate_a_provenance.derived_at_sha` | `6f2d7332` | `8ebb7805` | the file-level derivation stamp records the sha the keeper/marker read was taken at; every prior re-key lane (r#64, r#57, D56-R, …) re-stamped it; Y-29 did not |
| `gate_a_provenance.derived_at_date` | `2026-09-10` | `2026-09-24` | as above |
| `gate_a_provenance.derived_by` | r#64 stamp | r#65 stamp prepended, `Prior stamp: ` + the r#64 text carried verbatim | the chain convention this block has always used |

**Not edited, deliberately:** every gate-read leaf of every row (§0); `headline`, `gate_reading`,
`readiness`, `refresh`; MISO's row; NWPP/SOCO rows (none exist; owner ruling Q68 adds them only after
each declares backcast `complete`); anything outside this file.

---

## 4. The full chain each row was stale across — 32 promotions in 15 days, all promoter misses on this file

Sources per arrow: the keeper shard's own history fields (`keepers/<ISO>.json`), the marker file's
re-key fields (`complete.<ISO>.*`), `docs/calibration-log/<iso>.md`, and the RESULT/PRECOMMIT docs
named. "Promoter miss" = the promoting commit did not touch `program-status.json`: verified by
`git show --stat <sha> -- frontend/data/forecast/program-status.json` (empty) for every promoting commit
inside this clone's history (`e102603b`, `b1e523c1`, `d9cdfc1a`, `9c8b1d6e`, `49c237e9`, `107be503`,
`8adbc30b`, `ca9e41e6`);
the earlier promotions predate the shallow clone's graft root (`git rev-list --count HEAD` = 247) and are
established from the shards, the marker file and the logs — and the fact that the rows still cited the
2026-09-09..12 keepers at `6640becc` proves none of them touched the row.

### 4.1 CAISO — THREE promotions

| # | from → to | date · session | delta | owner instrument (verbatim) | record |
|---|---|---|---|---|---|
| 1 | `2026-09-12-caiso-275-gascoupling` → `2026-09-19-caiso-287-mer-keeper` | 2026-09-19 · caiso-287 | the caiso-275 recipe re-solved for the marginal emission rate; CALIBRATED unchanged | *"Mer should be promoted either way."* | `docs/RESULT-caiso287-startup-decommit-split-2026-09-19.md` §7; `complete.CAISO.rekeyed_2026_09_19` (which also records that the marker's `determination` prose had been stale since caiso-271) |
| 2 | → `2026-09-20-caiso-288-citygate-recovery` (+ stamped 2022 rung) | 2026-09-20 · caiso-288 | 85 EIA-published CA-composite citygate prints the scraper had discarded restored to `data/raw/gas-prices/caiso_citygate_daily.csv`; zero ScenarioConfig fields; 2022 C3a +11.344 % FAIL → +6.852 % PASS | *"If so plz promote"* | `docs/RESULT-caiso288-the-prints-were-published-2026-09-20.md`; `complete.CAISO.rekeyed_2026_09_20` |
| 3 | → `2026-09-20-caiso-290-leftedge` | 2026-09-20 · xiso-8 | `gas_flow_date_year_start_package` armed as a single-flag delta (the year-start left-edge repair of `data.fuel.hubs._flow_date_staircase`); zero new free parameters; all four years in ONE bundle, so the 2022 rung stamp is retired | *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."* | `docs/RESULT-xiso8-the-year-start-left-edge-2026-09-20.md` (its §7 left the promotion open; the ruling came after); `keepers/CAISO.json` `note` + `prior_keeper_note`; `complete.CAISO.rekeyed_2026_09_20_xiso8` |

### 4.2 ERCOT — ONE promotion

| # | from → to | date · session | delta | owner instrument | record |
|---|---|---|---|---|---|
| 1 | `2026-09-09-ercot265-receipts-fallback` → `2026-09-19-ercot266-mer-five-year` | 2026-09-19 · ercot-mer | NOT a recipe change: the superseded keeper's own configuration re-solved at HEAD, five years, one shard each (rule 36), composed by the parent; every scored criterion identical, CALIBRATED unchanged; adds the `marginal_emission_rate` dual; disclosed cost: does not reproduce the superseded prices (2023 +6.0 %, 2025 byte-exact), localised to a plant→class reallocation and NOT root-caused | *"Promote it"* | `docs/handoffs/RESULT-ercot-mer-keeper-resolve-2026-09-19.md`; `keepers/ERCOT.json` `promotion_note`; `complete.ERCOT.keeper_supersession`; `## ercot-mer — 2026-09-19` in `docs/calibration-log/ercot.md` |

### 4.3 NEISO — FOUR promotions

| # | from → to | date · session | delta | owner instrument | record |
|---|---|---|---|---|---|
| 1 | `2026-09-09-neiso-108-fuelvintage` → `2026-09-16-neiso109-gas-repair` | 2026-09-16 · neiso-109 | the contaminated Algonquin delivered-gas series repaired (82 rows of the committed file were other hubs' prices), recipe solved across all six years | in-session owner ruling of 2026-09-16 (the RESULT itself promoted nothing: *"A screen may kill an arm; it may never promote one"*); the promotion is recorded by `keepers/NEISO.json` `prior_keeper_note` ("The outgoing keeper 2026-09-16-neiso109-gas-repair") and by `PRECOMMIT-neiso110` naming it the keeper/control | `docs/RESULT-neiso109-gas-repair-2026-09-16.md`; `docs/FINDING-neiso109-the-agt-series-is-contaminated-2026-09-16.md` |
| 2 | → `2026-09-16-neiso110-dualfuel-derate-scope` | 2026-09-16 · neiso-110 | `neiso_coldsnap_derate_dualfuel_unswitched` False → True, a rule-19 scope correction; zero free parameters; CALIBRATED unchanged | *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper."* | `docs/RESULT-neiso110-coldsnap-dualfuel-screen-2026-09-16.md`; `complete.NEISO.rekeyed` |
| 3 | → `2026-09-19-neiso112-mer-year-isolated` | 2026-09-19 · neiso-112 | same recipe re-solved one year per shard (rule 36) plus the marginal emission rate; prices BIT-IDENTICAL; CALIBRATED unchanged | *"Promote when they land."* | `docs/RESULT-neiso112-mer-year-isolated-2026-09-19.md`; `## 2026-09-19 — neiso-112` in `docs/calibration-log/neiso.md`; `complete.NEISO.keeper_history` |
| 4 | → `2026-09-22-hydro-5-neiso-ror` | 2026-09-23 · hydro-5 (commit `e102603b`) | `hydro_ror_split=true`; zero new free parameters; CALIBRATED, same criteria | *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper."* | `docs/RESULT-hydro-5-2026-09-22.md`; `keepers/NEISO.json` `keeper_at_promotion_hydro5`; `complete.NEISO.rekeyed_hydro5` |

### 4.4 NYISO — TEN promotions

| # | from → to | date · session | delta / determination | record |
|---|---|---|---|---|
| 1 | `2026-09-09-nyiso-221-fuelvintage-span` → `2026-09-12-nyiso229-hourgrain-span` | 2026-09-12 · nyiso-229 | owner *"Flip it to keeper"* | `## nyiso-229 — 2026-09-12` (calibration-log/nyiso.md) |
| 2 | → `2026-09-13-nyiso231-anchor-span` | 2026-09-13 · nyiso-231 | the keeper's environment record was off-pin; promoted under the standing formula | `## nyiso-231 — 2026-09-13`; `docs/RESULT-nyiso231-the-mirror-and-the-2022-rescreen-2026-09-13.md` |
| 3 | → `2026-09-13-nyiso-232-st-gas` | 2026-09-13 · nyiso-232 | `nyiso_st_gas_econ_bands_deleaked`; owner *"Arm it"* | `### nyiso-232 CODA`; `docs/RESULT-nyiso232-st-gas-deleak-screen-2026-09-13.md`; shard `superseded` chain |
| 4 | → `2026-09-14-nyiso-235-gas-repair` | promoted 2026-09-16 · nyiso-235 | the nyiso-234b delivered-gas INPUT repair; zero fields; ISO tier CALIBRATED unchanged | `### nyiso-235 PROMOTION — 2026-09-16`; `complete.NYISO.keeper_rekeyed` (PRIOR) |
| 5 | → `2026-09-16-nyiso-238-hydro-budget` | 2026-09-16 · nyiso-238 | hydro budget span | `docs/RESULT-nyiso238-hydro-budget-span-2026-09-16.md`; shard `superseded` chain |
| 6 | → `2026-09-17-nyiso239-bench-oil-basis` | 2026-09-17 · nyiso-239 | C1 benchmark gas/oil attribution repair; model identical (G-1 5.0e-7 TWh); **NOT-YET → CALIBRATED**, zero flips | `docs/RESULT-nyiso239-bench-oil-promotion-2026-09-17.md`; `complete.NYISO.keeper_rekeyed` |
| 7 | → `2026-09-17-nyiso240-bench-attribution` | 2026-09-19 · nyiso-240 | benchmark boundary repairs R1/R2; identical dispatch, zero LP; CALIBRATED unchanged | `## nyiso-240 (promotion) — 2026-09-19`; `docs/RESULT-nyiso240-bench-attribution-promotion-2026-09-19.md`; `complete.NYISO.keeper_history` |
| 8 | → `2026-09-19-nyiso241-ct-committed-measured` | 2026-09-19 · nyiso-241 | CT_PEAKER `committed` band grounded on NYISO's measured 0.843; **CALIBRATED → NOT-YET** on two 2022 crossings, accepted under rule 14 | `docs/RESULT-nyiso241-ct-peaker-merit-2026-09-19.md`; `complete.NYISO.keeper_rekey_2026_09_19` |
| 9 | → `2026-09-20-nyiso247-fuel-invariance-disarm` | 2026-09-20 · nyiso-247 | `gas_offer_net_revenue_margin`'s fuel-invariance limb disarmed; **NOT-YET → CALIBRATED** | `docs/RESULT-nyiso247-the-market-prices-scarcity-in-and-the-model-priced-it-out-2026-09-20.md`; `complete.NYISO.rekeyed_2026_09_20` + `determination_note_2026_09_20` |
| 10 | → `2026-09-22-nyiso-hydro3-ror-split` | 2026-09-22/23 · hydro-3 (commit `b1e523c1`) | `hydro_ror_split=true`; **CALIBRATED → NOT-YET** (C1 2023 ST_GAS +3.61 TWh / +3.0 pp at the band edge; C3c no longer lone); owner rulings *"1"* and *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper."* | `docs/RESULT-hydro-3-nyiso-ror-split-promotion-2026-09-22.md`; `keepers/NYISO.json` `promotion_note` + `determination_note`; `complete.NYISO.keeper_rekey_2026_09_22` + `determination_note_2026_09_22` |

### 4.5 PJM — SEVEN promotions

| # | from → to | date · session | delta | record |
|---|---|---|---|---|
| 1 | `2026-09-11-pjm-d4-4-gasoutage` → `2026-09-19-pjm-h11-c1seam-span` | 2026-09-20 · pjm-h11 | card C-1: 2020 joins `PJM_SEAM_LADDER_BY_YEAR`; owner *"Promote anyway"* | `## pjm-h11 (promotion) — 2026-09-20`; `docs/RESULT-pjm-h11-c1-seam-ladder-2026-09-20.md` |
| 2 | → `2026-09-20-pjm-h13-meritalloc-span` | 2026-09-20 · pjm-h13 | `netload_drag_merit_allocation` False → True; owner *"If structural integrity improves but gates regress that may still be a keeper"* | `docs/RESULT-pjm-h13-the-drag-is-an-allocation-defect-2026-09-20.md`; `keepers/PJM.json` `promotion_note` (PRIOR) |
| 3 | → `2026-09-20-pjm-h14-coalmustrun-span` | 2026-09-20 · pjm-h14 | `coal_mustrun_requires_measured_row` | `docs/RESULT-pjm-h14-2026-09-20.md`; `complete.PJM.keeper_history` |
| 4 | → `2026-09-20-pjm-h15-coalwindow-span` | 2026-09-21 · pjm-h15 | `coal_sync_online_frac_per_year`; owner ruling 2026-09-21 | `docs/RESULT-pjm-h15-2026-09-21.md`; `complete.PJM.keeper_history` |
| 5 | → `2026-09-22-pjm-h16-coalgrain-span` | 2026-09-22 · pjm-h16 (commit `49c237e9`) | COAL-scoped whole-operating-day commitment grain | `docs/RESULT-pjm-h16-2026-09-22.md` |
| 6 | → `2026-09-22-pjm-hydro2-ror-span` | 2026-09-23 · hydro-2 (commit `9c8b1d6e`) | `hydro_ror_split`; owner *"Does it improve or is it more structurally sound if so yes"* / *"Promote it"* | `docs/RESULT-hydro-2-pjm-2026-09-22.md` |
| 7 | → `2026-09-23-pjm-h19-dbs-span` (+ folded `…-touchpoint` 2020–2022) | 2026-09-24 · pjm-h19 (commit `d9cdfc1a`) | `demand_balance_screen` False → True; owner *"Promote"*; all eight criteria PASS, zero status changes in either span | `docs/RESULT-pjm-h19-demand-balance-screen-2026-09-23.md`; `complete.PJM.rekeyed` + `determination` |

### 4.6 SPP — SEVEN keeper promotions (keepers 10 → spp-78; the seventh landed mid-lane), plus rung re-solves that are NOT keeper promotions

| # | from → to | date · lane | delta | owner instrument | record |
|---|---|---|---|---|---|
| 1 | `2026-09-12-spp-36-shortwindow-span` (keeper 10) → `2026-09-13-spp-38-vintage-cache` (11) | 2026-09-13 · SPP-38 | keeper 10's recipe re-solved on repaired code (twelve `lru_cache`'d loaders re-keyed on the active EIA-860 vintage); no config change | *"Keeper 10's committed 2024/2025 numbers are computed on an LP input we have proven wrong. Promote?"* → PROMOTE | `docs/handoffs/RESULT-spp-38-vintage-repair-2026-09-13.md`; `keepers/SPP.json` `prior_keeper_note_spp38` |
| 2 | → `2026-09-16-spp-42-commitment-feasibility` (12) | 2026-09-16 · SPP-42 | `mustrun_commitment_feasibility_clip` (new field) | *"Promote it when they land"* | `docs/handoffs/RESULT-spp-42-commitment-feasibility-2026-09-16.md`; `prior_keeper_note_spp42` |
| 3 | → `2026-09-20-spp-51-coal-sync` (13) | 2026-09-20 · SPP-51 | `coal_mustrun_online_pmin` + `coal_sync_srmc_tranche`, SPP's first commitment floor | *"Promote then Archive your stale shards and give me a handoff prompt."* | `docs/handoffs/RESULT-spp-51-coal-sync-floor-2026-09-20.md`; `complete.SPP.determination`; shard `superseded_promotion_note_…spp-71…` |
| 4 | → `2026-09-20-spp-67-yearown-rate` (14) | 2026-09-20 · SPP-67 | `vre_reference_rate_year_own` | in-session owner ruling | `docs/handoffs/RESULT-spp-67-year-own-rate-2026-09-20.md`; `complete.SPP.rekeyed_spp67` |
| 5 | → `2026-09-22-spp-71-ensemble-syncfloor` (15) | 2026-09-22 · SPP-71 (commit `107be503`) | `coal_sync_ensemble_level` (card R-bc) | *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper."* | `docs/handoffs/RESULT-spp-71-ensemble-sync-floor-2026-09-22.md`; `complete.SPP.rekeyed_spp71`; `keepers/SPP.json` `gates` |
| 6 | → `2026-09-22-hydro-5-spp-floor` (16) (+ rung `…-spp-rung` 2019–2022) | 2026-09-23 · hydro-5 (commit `e102603b`) | `hydro_min_flow_floor=true` | same ruling as row 5, given 2026-09-23 | `docs/RESULT-hydro-5-2026-09-22.md`; `keeper_at_promotion_hydro5`; `complete.SPP.rekeyed_hydro5` |
| **7** | → **`2026-09-24-spp78-hr-span`** (+ rung `2026-09-24-spp78-hr-rung` 2019–2022) — **landed between this lane's two rebases; the one row this lane re-keyed** | 2026-09-24 · SPP-78 (commit `8adbc30b`, merged `ca9e41e6`, PR #6580) | the hydro-5 recipe replayed unchanged plus three pre-existing measured fields `measured_cc_heat_rates` / `measured_st_heat_rates` / `measured_coal_heat_rates` = true (SPP's CAMPD artifacts, existing derives, default 2023–25 window); one year per shard at pinned `1e6c50da`, each with its own control; zero new free parameters; span CALIBRATED unchanged (lone ledgered C3c); rung NOT-YET unchanged with C3b 2022 FAIL → PASS (0.197) and a NEW C1 CC_REGULAR 2022 −8.14 TWh FAIL, both reported at full magnitude | *"Promote"* — in reply to *"Is it a keeper candidate?"* answered YES on rule-14 fidelity, not fit | `docs/handoffs/RESULT-spp-78-measured-heat-rates-2026-09-24.md` (PRECOMMIT `fe318fd8` + ADDENDUM pushed before any solve); `keepers/SPP.json` `note` + `keeper_at_promotion_spp78`; `complete.SPP.rekeyed_spp78` (determination re-verified CALIBRATED) |

Rung-only events in the same window, **not** keeper promotions and not counted: spp-40's first
2019–2022 rung (2026-09-13, the *"then run"* half of the declaration), spp-49's
`2026-09-19-spp-49-benchmark-membership` rung (promoted 2026-09-19 over the spp-48 rung; *"The keeper
itself is untouched"*), and the per-keeper rungs of SPP-51 / SPP-71 / hydro-5.

---

## 5. SPP — the one leg that moved, and why it is a marker consequence

The literal charter test, `docs/forecast-development-plan-2026-07.md` §2.1b(2)(a): *"a designated
full-span keeper (rule 16) on the calibration dashboard AND an entry for the ISO in the `complete`
block of `frontend/data/backcast/calibration-complete.json`"*. Both limbs, read live at `3affcd71`:

- **Full-span keeper:** `2026-09-24-spp78-hr-span` at `8ebb7805` (`2026-09-22-hydro-5-spp-floor` at
  Y-29's pin), registry years [2023, 2024, 2025] (the ISO's train span), with the held-out 2019–2022
  folded under rule 30(a). Met at both pins.
- **`complete` entry:** `complete.SPP` present, `declared: "2026-09-13"`, `keeper_at_declaration:
  "2026-09-13-spp-38-vintage-cache"`, `by` verbatim: *"OWNER RULING in session spp-40, 2026-09-13,
  verbatim: 'Complete then run' -- given in reply to this session's status, which reported that
  `complete` had no technical blocker, that docs/handoffs/PLAN-spp-31-complete-frontier-2026-09-12.md
  had recommended DECLARE on 2026-09-12 and gone unactioned, and that `frontier` was NOT close (18 of
  175 matrix cells adjudicated, 10 %, against a lowest-declared bar of 43 %). The ruling is read as
  `complete` ALONE …"*. Met. `final`: absent (EMPTY program-wide).
- **Concurring evidence (the charter's stop gate):** `status/SPP.js` `keeper.determination` =
  **CALIBRATED** for the live keeper (rubric v3.8, scored 8 / target 7 / ledgered 1 / fails 0; C3c the
  single ledgered caveat). The stop gate ("if SPP's committed status sidecar does NOT read CALIBRATED
  for the live keeper, do NOT flip") **did not fire**.

So leg (a) reads **pass**. It read **fail** at `6640becc` only because the row's own stated reason —
*"SPP still has NO `complete` entry"* — was written 2026-09-12 and became false on 2026-09-13 when the
owner declared; the declaring lane (spp-40) and the six keeper promotions since never re-keyed the
row. That is the verdict-flipping half of F-5 (a gate closed on a marker the ISO holds), open for
eleven days. **The marker moved; no lane moved the verdict.** Y-29 executed the flip at `a4708b25`
following the D56-R precedent (`docs/handoffs/FINDING-capx-d56r-nyiso-redeclaration-2026-09-05.md`:
status fail → pass, `closed_on` loses `a`, notes prefixed, prior text preserved); this lane re-derived
it independently on the same test and concurs. Legs (b)/(c)/(d) and `open: false` are untouched — SPP's
forecast gate does not open; (b) and (c) are still closed by the absence of any T1-F / T1-X
measurement, (d) by the absence of any authorization.

Gate-(a) passer set at `3affcd71`: **{CAISO, ERCOT, NEISO, NYISO, PJM, SPP} = the `complete`
membership.** MISO fails on the absent marker (owner declined it at Q49), unchanged.

---

## 6. Reported, not repaired

1. **CAISO marker `determination` prose lags its own `keeper` field (CAISO lane / audit board).** The
   charter said the `complete.CAISO` entry "named caiso-288 while the shard names caiso-290" at
   `40f4ed7a`. Read live: the entry's **`keeper` field names `2026-09-20-caiso-290-leftedge` at BOTH
   `40f4ed7a` and `3affcd71`** (the `rekeyed_2026_09_20_xiso8` field is present at the desk pin). What
   names caiso-288 is the entry's `determination` **prose**, which still opens *"CALIBRATED on
   2026-09-20-caiso-288-citygate-recovery (bundle caiso288_gasfix_span, git pin 35adf93c)"* — a D-5(b)
   determination text one promotion behind its own keeper field. `complete.SPP.determination` likewise
   still opens on `2026-09-20-spp-51-coal-sync` (four keepers behind at `8ebb7805`; the SPP-78
   promotion added `rekeyed_spp78` with its own re-verification and left the prose as it was). Narrative, not identity;
   `audit_keepers` M1 passes (Y-29 §1.4 concurs). Not repaired: not this lane's file.
2. **NYISO holds `complete` on a NOT-YET keeper (NYISO desk / owner).** Leg (a) stays **pass** on the
   literal test — both limbs hold — and the determination is concurring evidence, never the gate
   test; but it no longer concurs. The marker file's own entry says so (`determination: "NOT-YET"`;
   `keeper_rekey_2026_09_22.by`: *"the rekey designates the keeper and does not re-declare
   calibration — the incoming keeper scores NOT-YET"*), and hydro-3 promoted on the owner's ruling
   that a structural improvement may be a keeper though gates regress. Whether the Q5 uniform rule
   (a `complete` marker cannot stand on a NOT-YET keeper) applies after the 2026-09-09 `[R-HOLDOUT]`
   removal is the owner's to rule; Y-29 §1.3 routed the same question. Nothing here re-derives,
   re-asserts or moves a determination.
3. **`isos.<ISO>.keeper` has no reader.** It is now truthful on all seven rows, but nothing enforces
   it — `check_gate_a_provenance.py` reads only the detail prose. A one-line extension of that guard
   (compare `isos.<ISO>.keeper` to the shard) would close the gap; it is a `scripts/` edit outside
   this lane's charter. **Live owner:** the capx desk (this file's guard is its instrument).
4. **The promoter-miss rate is now structural, not incidental.** Thirty-one promotions in fourteen
   days, thirty-one misses on this file; Y-29 §6 proposes a promotion-time check and did not
   implement it because it would change gating. **Live owner:** the audit board (Y-29's) and the
   capx desk (Q34's standing duty). This lane names it and adds nothing.

---

## 7. What this lane did NOT do

No LP. No solve, no score, no registration. No keeper shard, `calibration-complete.json`, status
sidecar, registry sidecar, ff-verdicts, hindcast sidecar, `results/calibration/` path, matrix shard,
`src/`, `scripts/`, or backcast-namespace byte touched. No row re-keyed that was green at HEAD. No
NWPP/SOCO row added (Q68). No determination, grade, caveat budget or leg status computed or moved.
