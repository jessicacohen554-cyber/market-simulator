# FINDING — capx gate-(a) re-key, ERCOT + MISO (2026-09-08)

**Lane:** capx gate-(a) re-key. **ONE ACT, ZERO LP.** No solve, no scoring, no registration,
no keeper edit, no marker edit, no determination re-computation.
**HEAD:** `4e4ad90d` (identical to freshly-fetched `origin/main`).
**Result:** `scripts/check_gate_a_provenance.py` **EXIT 1 → EXIT 0** on all seven rows;
`scripts/audit_keepers.py --check` still **PASS** (0 failures, 0 warnings).

The **seventeenth** firing of the Q34 standing duty and the **first double** — ERCOT and MISO
were both EXIT 1 at the same pin, and both are promoter misses (neither promoting commit
touches `frontend/data/forecast/program-status.json`; verified as zero hunks).

---

## 1. The two id transitions

| ISO | row cited (before) | live designated keeper (after) | gate verdict |
|---|---|---|---|
| ERCOT | `2026-09-05-ercot248-two-config-keeper` | `2026-09-08-ercot256-drag-layup-mask` | pass → pass (**unmoved**) |
| MISO | `2026-09-07-miso-233-spp-hourly` | `2026-09-07-miso-243-spp-pairing` | fail → fail (**unmoved**) |

Both live ids agree with the charter's reading. Nothing was carried from the charter: every
fact below was re-read at `4e4ad90d`.

## 2. Live facts, with the file each came from

| fact | ERCOT | MISO | source |
|---|---|---|---|
| designated keeper | `2026-09-08-ercot256-drag-layup-mask` | `2026-09-07-miso-243-spp-pairing` | `frontend/data/backcast/keepers/<ISO>.json` → `keeper` |
| marker `complete` | **True** (declared 2026-08-31) | **False** (never held one; declined at Q49) | `calibration-complete.json` → `complete` block |
| marker `final` | **False** | **False** | `calibration-complete.json` → `final` block |
| determination | ISO-level **CALIBRATED**; registered run-level **NOT-YET** | **CALIBRATED** (rubric v3.6) | `frontend/data/backcast/status/<ISO>.js` (committed sidecar, **not** a re-score) |
| per-year | 2021 NOT-YET · 2022 CALIBRATED · 2023 CALIBRATED · 2024 CALIBRATED · 2025 CALIBRATED | 2023 CALIBRATED · 2024 CALIBRATED · 2025 CALIBRATED-WITH-CAVEATS (unscored `fuelmix`, `sysvol`) | same sidecar, `keeper.years` |
| grade summary | scored 8 / target 4 / ledgered 1 / fails 3 (the fails are the 2021 rung's `price_mean`, `price_shape`, `forced_share`) | scored 8 / target 7 / ledgered 1 / fails 0 | same sidecar, `keeper.grade_summary` |

**`final` is EMPTY for every ISO** in this repo — it holds only its `_note`. No locked-test
claim appears in either row. `complete` membership read live at `4e4ad90d` is
{ERCOT, NEISO, PJM, CAISO, NYISO}.

ERCOT's `complete` entry carries `keeper: 2026-09-08-ercot256-drag-layup-mask` — the promotion
re-keyed the marker itself under rule 22 D-5(b), so the marker did **not** go stale with the
board row. This is why the ERCOT verdict is unmoved despite a two-promotion gap.

## 3. Promotion instruments, named as documents

**ERCOT** — `docs/RESULT-ercot256-drag-layup-window-mask-2026-09-08.md`
(the ercot-256 RESULT, added at `fe63e461`). Executed by `baa5fe16`
("ercot-256 PROMOTION: netload_drag_layup_window_mask armed in all five years; train tier
re-verifies CALIBRATED"), merged in **PR #5605** (`ffc25ece`). An intervening promotion —
ercot-255, `614f3691`, the five-year keeper — also skipped the re-key, so this discharges
**two** ERCOT promoter misses.

**MISO** — `results/calibration/ASSESSMENT-miso243-spp-pairing-repair-fullspan-2026-09-07.md`
(added in the promotion commit itself). Executed by `e998cc9c`
("miso-243: PROMOTE keeper -> 2026-09-07-miso-243-spp-pairing (CALIBRATED)"), merged in
**PR #5604** (`6a0d55cf`).

## 4. Before / after `detail` head, verbatim

### ERCOT — BEFORE

> keeper 2026-09-05-ercot248-two-config-keeper (full-span 2023-2025, rule 16); determination CALIBRATED at ISO level; marker complete=True final=False.

### ERCOT — AFTER

> keeper 2026-09-08-ercot256-drag-layup-mask (five-year run 2021-2025, covering the full train span 2023-2025, rule 16; bundle results/calibration/ercot256_five_year_keeper); determination CALIBRATED at ISO level; marker complete=True final=False.

### MISO — BEFORE

> keeper 2026-09-07-miso-233-spp-hourly (full-span 2023-2025, rule 16; registry years [2023, 2024, 2025], bundle results/calibration/miso233_sppseam_K, solved at e852c85c); determination CALIBRATED (rubric v3.6; grade 7 of 8, fails 0, single ledgered C3c caveat, non-downgrading under rubric v3.3; per year 2023 CALIBRATED, 2024 CALIBRATED, 2025 CALIBRATED-WITH-CAVEATS on unscored C1/C2; C1 16 PASS / 0 FAIL / 8 SKIPPED, all eight 2025 cells unscored; C2 4 PASS, C3a 3 PASS, C3b 3 PASS, C4 6 PASS, C6 PASS, C8 10 PASS; read live from frontend/data/backcast/status/MISO.js at origin/main f37121bd); marker complete=False final=False.

### MISO — AFTER

> keeper 2026-09-07-miso-243-spp-pairing (full-span 2023-2025, rule 16; registry years [2023, 2024, 2025], bundle results/calibration/miso243_sppair_K); determination CALIBRATED (rubric v3.6; grade summary scored 8 / target 7 / ledgered 1 / fails 0; per year 2023 CALIBRATED, 2024 CALIBRATED, 2025 CALIBRATED-WITH-CAVEATS on the unscored criteria fuelmix and sysvol; C3c the single ledgered caveat, non-downgrading under rubric v3.3; read live from frontend/data/backcast/status/MISO.js, generated 2026-09-07 19:20, and NOT re-scored here - this lane computes no verdict); marker complete=False final=False.

In both rows the prior head is **preserved verbatim** further down, behind a
`PRIOR TEXT (<lane> re-key, preserved):` label — the row is a chain, not a snapshot. Asserted
by test in the edit script: `new_detail.endswith(old_detail)` for both ISOs.

## 5. Method — how the edit was made

**TARGETED STRING EDIT at five uniquely-anchored positions, never a `json.dumps` round-trip.**
`program-status.json` is a hand-maintained committed seed that `build_program_status` wraps
verbatim; a reserialization would silently reformat every other desk's row and make the diff
unreviewable. Each anchor was asserted to occur **exactly once** in the raw text before
replacement, and the new prose carries no escape sequences.

Machine-checked after the edit, before the file was written:

- the document still parses;
- a recursive structural diff against the pre-edit parse finds **exactly seven** changed
  leaves and no key-set or list-length movement:
  `isos.{ERCOT,MISO}.gate.a_keeper_marker.{detail,read_live_at}` and
  `gate_a_provenance.{derived_at_sha,derived_at_date,derived_by}`;
- each row's prior `detail` is a **suffix** of the new one, and the prior provenance stamp is a
  suffix of the new `derived_by`;
- `status` and `corrected_by` are byte-identical on **all seven** rows.

Diff: **1 file, 7 insertions, 7 deletions**, three hunks (lines 112, 293, 691).

## 6. Stop gates — none tripped, and one thing deliberately not done

- Neither ISO was already EXIT 0 at HEAD; both genuinely needed the re-key.
- Neither live keeper id disagreed with both the row and the charter.
- **No determination, marker, leg status or grade was changed.** This guard compares identity
  only. Both gate verdicts are unmoved, and the reason each ISO passes or fails is the *marker*,
  not the keeper: ERCOT holds `complete` on both sides, MISO is absent from it on both sides.
- Only the ERCOT and MISO rows were touched.

**Reported, not repaired (out of charter):** each row's `corrected_by` leaf now trails its
`detail` head by one re-key, because the charter scoped this lane to the `detail` head,
`read_live_at` and the `gate_a_provenance` block, and instructed that everything else in the
row stay byte-identical. Nothing reads `corrected_by` (no `.py` under `scripts/` or `src/`
references it), and the new `detail` head carries this lane's attribution in full, so the row's
attribution is complete — but a desk that wants the `corrected_by` chain to lead with the
current corrector should extend the leaf set in the next charter rather than treat this as
drift.

## 7. Gate evidence at close

| gate | result |
|---|---|
| `scripts/check_gate_a_provenance.py` | **EXIT 0** — "7 row(s) checked: keeper identity + marker state match the backcast store; no determination read" |
| `scripts/audit_keepers.py --check` | **PASS** — 0 failures, 0 warnings |
| `scripts/check_registry_payload_parity.py` | OK — 22 runs, 55 bundle dirs, 0 known-unsynced tolerated |
| `scripts/check_forecast_staleness.py` | EXIT 0 (pre-existing warnings only; the gate-(a) block deliberately avoids `forecast-provenance/v1` field names, so it is unreadable by this checker by design) |
