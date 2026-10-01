# FINDING — capx gate-(a) re-key r#66: EXIT 1 → EXIT 0 on FOUR rows (CAISO, ERCOT, MISO, NEISO), every charter id stale, six promoter misses re-keyed, no leg status moves (2026-09-25)

**`scripts/check_gate_a_provenance.py`: EXIT 1 (4 rows) → EXIT 0 (7 rows) at origin/main `c64e69eb`.**
`tests/scoring/test_gate_a_provenance.py` + `tests/scoring/test_forecast_staleness.py`: 41 passed.

| ISO | row cited (Y-31, `20aefec0`) | promotion chain | live keeper | leg (a) | determination (committed sidecar) |
|---|---|---|---|---|---|
| CAISO | `2026-09-24-caiso-r-inputs-vintage` | → R-CAISO-2 `8e9d7f80` | `2026-09-25-caiso-r2-cc-gross` | pass → pass | NOT-YET → **CALIBRATED** 8/7/1/0 |
| ERCOT | `2026-09-25-r-ercot2-chp-off` | → R-ERCOT-4 `1b3607ee` | `2026-09-25-r-4-day-guard` | pass → pass | CALIBRATED → CALIBRATED (ISO level, config partition; registered NOT-YET) |
| MISO | `2026-09-24-rmiso-arm-b-mid` | → miso-271 `b7afb06e` (`2026-09-25-miso-271-wefor-stack`) → miso-272 `413fb768` | `2026-09-25-miso-272-edwardsport-block` | fail → fail (no `complete` entry) | NOT-YET → **CALIBRATED** (ISO level, train tier 8/7/1/0; registered NOT-YET) |
| NEISO | `2026-09-24-r-neiso-inputs-2019` | → neiso-114 `2c2d324d` (PR #6651) | `2026-09-25-neiso114-coal-mustrun-measured` | pass → pass | NOT-YET → NOT-YET 8/6/1/1 |

**Lane:** capx GATE-(a) RE-KEY r#66 RELAUNCH (pack `capx-director-prompt-pack-2026-08.md` "GATE-(a) RE-KEY r#66"; ledger §0bk).
**Data profile:** code. **Branch:** `claude/capx-gate-a-rekey-r66` off `origin/main c64e69eb`; re-fetched and rebased
immediately before the edit (no new commits), and the gate re-run after it. ZERO LP; nothing solved, scored or registered.
**Edits:** `frontend/data/forecast/program-status.json` (19 lines, targeted string edits) and this record. Nothing else.

## 1. The charter's ids were all stale

The charter was written at `a1b8ebd9` and named CAISO/ERCOT/MISO/NEISO/PJM re-keys onto the R-* input-vintage keepers.
Audit lane **Y-31** (`20aefec0`, "R-BC follow-on") then re-keyed those five rows at `7c778943`. After that, **six
promotions** landed without touching `program-status.json`. Each is a promoter miss. Five of them left four rows red at `c64e69eb`:

- **CAISO**: R-CAISO-2, `8e9d7f80`. Owner: *"Is this a recommended keeper candidate? If so plz promote"*. Instrument:
  `docs/handoffs/r-caiso-2/RESULT-r-caiso-2-2026-09-25.md` (+ PRECOMMIT); marker field `complete.CAISO.rekeyed_2026_09_25_rcaiso2`.
- **ERCOT**: R-ERCOT-4, `1b3607ee`. The r-ercot2-chp-off recipe plus `ercot_partial_outage_day_guard=true`. Owner:
  *"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."*
  Instrument: `docs/handoffs/RESULT-r-ercot-4-day-guard-2026-09-25.md`; marker field `complete.ERCOT.keeper_supersession`.
- **MISO**, two promotions, both under the same standing ruling:
  - miso-271, `b7afb06e`, WEFOR retired on {CC_REGULAR, ST_CHP, ST_GAS}: `docs/RESULT-miso271-cc-regular-shortfall-wefor-stack-2026-09-25.md`.
  - miso-272, `413fb768`, `cc_block_summer_rating=true`: `docs/RESULT-miso272-cc-block-summer-rating-2026-09-25.md`.
  - Shard fields: `promotion_note_miso271`, `promotion_note_miso272`.
- **NEISO**: neiso-114, `2c2d324d` / merge `1788d66e`, `coal_mustrun_requires_measured_row=true`. Instrument:
  `docs/handoffs/neiso114/RESULT-neiso114-2026-09-25.md`; shard field `neiso114_promotion_note`.

The sixth promotion was PJM-NEXT (`bba37cf2`). It re-keyed its own row at source (`fb35e260`), so PJM was green, as
were NYISO and SPP. Those three rows are **byte-unchanged**, per the stop gate. NWPP and SOCO show as notes only
(Q68), so no rows were added for them.

## 2. Method (as r#65 / `1b175ce9`)

Per ISO, every fact was read live at `c64e69eb`:
- the keeper id from `keepers/<ISO>.json`;
- both blocks of `calibration-complete.json` (`complete` = {ERCOT, NEISO, PJM, CAISO, SPP}; `final` empty; `withdrawn` = {NYISO});
- the determination and grade summary from `status/<ISO>.js`. Each sidecar's `run_id` equals the live keeper; nothing was re-scored;
- years and bundle from `registry/<id>.json`.

Each row got the same edits:
- The `detail` gets a new head keyed to the live keeper. Y-31's detail follows it verbatim under a
  "PRIOR DETAIL, CARRIED VERBATIM" label that quotes the prior text's sha256[:12].
- `read_live_at` is re-stamped to `c64e69eb`.
- The new `corrected_by` sentence is followed by `Supersedes: ` and then Y-31's chain.
- The top-level `isos.<ISO>.keeper` is set to the live id. Y-31 had left CAISO, ERCOT, MISO and NEISO one to three keepers stale.

`gate_a_provenance` `derived_at_sha/date/derived_by` are re-stamped, with the prior stamp kept. All edits were
position-scoped `str.replace` calls, each asserted to match exactly once inside its ISO block. There was no
`json.dumps` round-trip, and the file stays ASCII-escaped.

**Stop gates.** No marker moved, so no leg status moves. MISO's determination moved to CALIBRATED at miso-271. That
cannot move a leg whose test is the `complete` marker, which MISO does not hold (Q49).

## 3. Reported, not repaired (outside this lane's one file)

1. **audit_keepers E13 FAIL on CAISO and NEISO (rule 35 [R-PROMOTE] (a))**. The outgoing keepers are still registered in
   all three stores:
   - `2026-09-24-caiso-r-inputs-vintage` (registry + runs + `results/calibration/rcaiso_inputs_span`). R-CAISO-2's commit
     says the prune was "left for the owner: auto-mode refused prune_iso_runs --force-uncite".
   - `2026-09-24-r-neiso-inputs-2019` (registry + runs + `results/calibration/rneiso_span`), left behind by neiso-114.
   - Owners: the CAISO and NEISO backcast lanes. For CAISO, it is the owner's to authorize.
2. **`complete.NEISO` is one promotion behind its own `keeper` field.** Its `determination` prose still re-verifies
   against `2026-09-24-r-neiso-inputs-2019`, and it has no neiso-114 re-key field. Owner: the NEISO lane.
3. **The `keepers/ERCOT.json` `promotion_note` still opens on R-ERCOT-3.** The R-ERCOT-4 record lives in
   `config_partition.r_ercot4_extension` and in the marker. This is a prose lag only. Owner: the ERCOT lane.
4. **NEISO holds `complete` on a keeper whose run-level determination is NOT-YET** (C1 fuelmix 2019/2022, held-out years;
   the train tier is CALIBRATED). Y-31 reported this, not adjudicated. The owner decides whether Q5 applies; R-BC applied it
   to NYISO only. CAISO's matching non-concurrence is **resolved by R-CAISO-2**, whose live keeper reads CALIBRATED.

No marker entry names a keeper other than the live one: all four `complete.<ISO>.keeper` fields match their shards.
Nothing is deferred without an owner.
