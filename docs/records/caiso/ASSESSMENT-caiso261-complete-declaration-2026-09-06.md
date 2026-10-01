# ASSESSMENT — caiso-261 (same session, after the FINDING): the owner's four decision cards — **`complete` RE-DECLARED and frontier RE-STAMPED on `2026-09-06-caiso-260-b1-demand`**; the 2022 hourly price archive and the G-26 public-bid economic surface **FUNDED as chartered lanes** (not executed here); the stale forecast-board CAISO stamp **re-keyed**. ZERO LP; determination re-verified on committed artifacts only; nothing spendable today.

**Session caiso-261, 2026-09-06**, branch
`claude/caiso-backcast-calibration-261-2hrovn`. Keeper
**`2026-09-06-caiso-260-b1-demand`** (bundle `caiso260_demand_vintage`,
sha `e162147b`) **UNCHANGED**. The four cards were put to the owner after
`FINDING-caiso261-import-intake-adjudication-2026-09-06.md` landed; the
answers below are the owner's, verbatim from the card labels.

---

## §1 — Card 1: `complete` — **"Declare complete now."** EXECUTED

The caiso-259 §3 recipe, in order, all in this session and one commit:

1. **Re-verification, no solve.** `scripts/calibration_verdict.py --run-id
   2026-09-06-caiso-260-b1-demand` → **CALIBRATION DETERMINATION:
   CALIBRATED** (rubric v3.6). C1 PASS 12/12 free 8/8; C2 PASS; C3a PASS
   (+4.37 / +8.89 / +8.25 %); C3b PASS (0.083 / 0.142 / 0.111); C3c
   CAVEAT [ledgered] (23 / 0 / 0 h vs 47 / 35 / 8 — the accepted
   model-class limitation, non-downgrading since v3.3, the single ledgered
   caveat); C4 PASS (0.881/0.287, 0.912/0.260, 0.877/0.298); C6 PASS
   (attested); C8 PASS. Reported-only: C5a CO₂ 2023 −11.0 % (FAIL, not
   gated), 2024 −5.2 %, 2025 −4.3 %; D-A amplitude 69.1 / 67.3 / 82.8 %.
2. **The marker.** `frontend/data/backcast/calibration-complete.json`:
   CAISO moved from `withdrawn` to `complete` — `declared` 2026-09-06;
   `keeper` = `keeper_at_declaration` = caiso-260; `by` = the card;
   `determination` = the verdict above, criterion by criterion;
   `tier_authorized` = validation ONLY (2022 and the 2020–2021 ladder, the
   touchpoint loop; never training), with the 2022 readiness state carried
   (H-1 buildable on the current bench vintage; H-2/H-3 the funded intake
   of §2; S-1/S-2/S-4 data prep); `locked_test` = NOT AUTHORIZED, never
   spent, frozen; `frontier_basis` = the caiso-259 §4 draft re-stated on
   the caiso-260 keeper with the caiso-261 adjudication of object (i);
   `freeze_interaction` = the tier-scoped freeze (locked test only) leaves
   the validation tier governed by this marker + `--holdout-authorized`,
   and `dashboard_add_run.py` re-asks the marker at registration (R-AZ);
   `keeper_rekey_policy` = D-5(b); `redeclaration_note`; and the whole
   2026-08-06 withdrawn entry preserved verbatim under
   `withdrawal_history_2026_08_06` (history, never a grant, never
   retracted). Every other ISO's entry is parsed-equal to HEAD.
3. **Frontier.** `keepers/CAISO.json` gains `frontier` (declared
   2026-09-06 on caiso-260, note = the basis) and `frontier_history`
   (2026-08-05 declared → 2026-08-06 withdrawn → 2026-09-06 re-declared).
   The keeper id and every note are untouched.
4. **Status and audits.** `build_status.py --iso CAISO` → CALIBRATED;
   `build_status.py --iso CAISO --check` → in sync; `audit_keepers.py --iso
   CAISO` → PASS 0 failures / 0 warnings (M1 re-verification included);
   `check_gate_a_provenance.py` → OK on all six rows;
   `check_mechanism_matrix.py` → no CAISO finding; the
   `calibration-keeper-auditor` agent run on the shard (its report is in
   the session record).

**What the marker does and does not do today.** It authorizes the
validation tier in principle. **Nothing is spendable now**: the 2022 rung
needs the H-1 artifact built (inside a PRECOMMIT; the derive rewrites the
committed files on any invocation) and the funded H-2/H-3 price intake
landed with a rule-14 reconciliation; 2019 and H1-2026 stay under the
tier-scoped freeze and need a `final` entry CAISO does not hold. A
volume-only 2022 rung was **not** chosen (§2).

## §2 — Card 2: 2022 prices — **"Fund an hourly price archive."** CHARTERED

The gap (caiso-259 §1 H-2/H-3): OASIS `PRC_LMP` / `PRC_INTVL_LMP` and the
intertie-price series have a ~39-month retention window and 2022 can never
be re-fetched from OASIS; without them C3a/C3b/C3c cannot be scored in 2022
and the caiso-87/93/94 import rows lose their measured hub, so the 2022
recipe would silently differ from the keeper's.

What the funded lane must do, in this order, before any rung is solved:
1. **Source adjudication first.** Candidates, none on disk: CAISO's own
   historical price archives outside OASIS retention; a third-party hourly
   archive of SP15 / NP15 / ZP26 hub LMPs and of the MALIN / PALOVRDE
   intertie prices; the EIA / ICE daily indices are **daily**, a different
   aggregation, and admissible only with a documented rule-14
   reconciliation, never as a silent substitute.
2. **Both halves or neither.** The rung needs the hub LMPs (scoring) AND
   the intertie hub series (the injector's own input,
   `wecc_intertie_lmp_hourly_CAISO.parquet`); a source that carries only
   the first leaves H-3 open and the import structure different.
3. **Same basis as 2023–2025.** The scored basis is the load-weighted RT
   hourly hub price (`actual_lmp_hourly_CAISO.parquet` schema, `rt` /
   `da` columns); a 2022 series enters `_validation-source` through the
   same loader, byte-identity-checked on the 2023–2025 rows.
4. Then `derive_actual_tail.py` (marker-gated) emits the CAISO 2022 tail
   row, and the rung runs under `--holdout-authorized` on the frozen
   caiso-260 recipe, with S-1 (2022 CARB price), S-2 (DMM 2022 RA-import
   row), S-4 (NRC 2022 windows) prepared and S-3 (static clean depths)
   **stated on the rung** because its inputs are H-3's.

**Not executed here** — a data-intake session (`data-intake` skill) with
its own PRECOMMIT.

## §3 — Card 3: G-26 surface — **"Fund as G-26 audit item."** CHARTERED

What is funded: the gap-register G-26 / audit C-6 CAISO closure — replace
the import ladder's "static-fitted-pending-measured" Tier-3 $/MWh (and the
hub-plus-wheel delivered-cost pricing of the economic rungs) with a
**measured intertie economic offer surface** from CAISO's own as-submitted
DAM bids (`PUB_DAM_GRP`), the way `derive_nyiso_import_tranches.py` /
`derive_neiso_import_tranches.py` / `MISO_SEAM_LADDER_BY_YEAR` closed C-6
for those ISOs.

Binding conditions, fixed now so the lane cannot drift into the lever
caiso-252 §7 #2 forbids:
1. **It is an audit item, not a lever on the hod 22–23 residual.** Its
   PRECOMMIT declares the residual **excluded** from its basis, C3a and C4
   excluded both ways, and re-states the C4-2025 (0.298 vs ≤ 0.30) and
   C3c-2023 (23 vs 47) exposures before any solve. Rule 29(a): its screen
   year is the year of the mechanism's largest footprint (the largest
   re-priced MW), never the largest residual.
2. **The corpus is off disk** (gitignored payload; `README.md` +
   `SHA256SUMS.txt` tracked): re-fetch with
   `scripts/data/fetch_caiso_public_bids.py` — ~1,096 daily zips at ≥ 6 s per
   request (OASIS AUP throttle), 0.5–0.9 GB. It cannot be committed; the
   derived (month × hod × price-bin) surface can, exactly as the caiso-151
   ceiling is.
3. **The caiso-150 §H wall stands.** Economic curves are classifiable
   import / export by monotonicity (149 / 162 at caiso-150); self-schedules
   are not, and no import/export split of them is attempted by any route.
   Rows are RLE-expanded before any hourly statistic (caiso-150 §E1).
4. **Rule 23**: frozen gates (year-stability CV, LOYO level and shape,
   coverage) fixed ex ante on the caiso-81/86/87/88 standard; a FAIL files
   a FINDING and stops.
5. **Rule 19**: it replaces the static ladder prices; it never stacks on
   them, and it does not touch the firm block, the clean rows or their
   windows.

**Not executed here** — its own session, Opus/Fable (it writes
`src/market_sim/model/interchange/spec.py`).

## §4 — Card 4: `program-status.json` — **"Update it to caiso-260."** EXECUTED

`frontend/data/forecast/program-status.json`: `isos.CAISO.keeper`
`2026-08-26-caiso-220-c1-crosswalk` → `2026-09-06-caiso-260-b1-demand`;
`marker_complete` false → true; the gate-(a) row re-keyed from caiso-257
to caiso-260 with `status` `fail` → `pass` (both charter §2.1b(2)(a)
conditions now met: full-span keeper AND a `complete` entry; the prior
detail preserved verbatim); `gate_a_provenance` re-stamped at
`origin/main ff418aa4`. A stamp re-key plus the marker-state change — no
forecast run solved or re-scored; gates (b)/(c) untouched.
`check_gate_a_provenance.py` OK; `register_forecast_run.py --reindex`
rebuilt the gitignored preview (113 runs).

## §5 — What did NOT change

No solve; no `ScenarioConfig` field; no derive run; no bench regeneration;
no corpus re-fetch; no run registered; no 2022 (or any out-of-training)
year solved, scored or registered; the holdout freeze untouched; `final`
untouched; every other ISO's marker, keeper shard and status part
untouched.

## §6 — Owner asks still open (carried)

The C3a weight basis (caiso-247 §4.5); the per-zone storage/class sidecar;
S2 funding; the DMM 2025 RA-import basis; Panoche's obligation instrument.

**Next number: caiso-262.**
