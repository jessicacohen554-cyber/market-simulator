# FINDING — Y-29: keeper-promotion provenance debt (2026-09-24)

**Lane:** `Y-29`, Model Audit & Release-Finalization Program, chartered at director board
**v42** §4 row 1 + §5 (`docs/handoffs/audit-program-director-board-2026-08.md`). Director pin
`40f4ed7a`; this lane worked at `origin/main` **`a4708b25`** (the pin plus the v42 board
merge, #6556). Records/registry only. **No keeper designation, calibration verdict, scorer
threshold or matrix cell verdict was changed. No LP was solved. No cache-key pin was touched
(Y-28's).**

## 0. Headline

| # | red | before | after | how |
|---|---|---|---|---|
| 1 | `check_gate_a_provenance.py` (FR-21) | **FAIL**: 6 superseded keepers + SPP marker mismatch | **PASS** (7 rows) | re-keyed 6 rows; SPP leg (a) re-derived **fail → pass** (§1.2) |
| 1b | `calibration-complete.json` keeper names | — | all 6 `complete` entries already name the live keeper | verified, no edit |
| 2 | `audit_keepers --check` SOCO E13 | FAIL | **FAIL (unchanged, deliberately)** | `soco53g` is an **unruled candidate**, not soco61's predecessor — rule 31 forbids the prune; **routed to the owner** (§2) |
| 3 | `check_forecast_parity.py` (FR-22) | FAIL: 3 unaccounted | **PASS** (3 new filed GAPs) | registry rows, routed to NYISO / MISO / forecast desks (§3) |
| 4 | fast-tier tests (6 files) | 18 red (+3 env-only) | **1 fixed in code** (E11); the rest need test edits **held for owner approval** (§4) | see §4 |
| 5 | `test_bench_stamp_payload` | ERCOT 5 + CAISO 4 parts unresolved | **unchanged — no entry added** | a PAYLOAD source moved; parts genuinely stale; routed to ERCOT + CAISO desks (§5) |
| 6 | promotion-time check | — | **proposed, not implemented** (it would change gating) | §6 |

## 1. Gate (a) — `frontend/data/forecast/program-status.json`

### 1.1 Re-keys (identity + marker state only; nothing re-scored)

Every fact read live at `a4708b25` from `keepers/<ISO>.json`, both blocks of
`calibration-complete.json` and `status/<ISO>.js`. Edited by a `json` load/dump that was first
verified **byte-identical on a no-op round-trip** (`indent=1, ensure_ascii=True`), so every other
row is untouched. Each row's prior detail is preserved in git; its `sha256[:12]` is quoted in the
new detail.

| ISO | cited (superseded) | live keeper | leg (a) | determination read live (status sidecar) |
|---|---|---|---|---|
| CAISO | 2026-09-12-caiso-275-gascoupling | 2026-09-20-caiso-290-leftedge | pass → pass | CALIBRATED 8/7/1/0 |
| ERCOT | 2026-09-09-ercot265-receipts-fallback | 2026-09-19-ercot266-mer-five-year | pass → pass | CALIBRATED 8/7/1/0 |
| NEISO | 2026-09-09-neiso-108-fuelvintage | 2026-09-22-hydro-5-neiso-ror | pass → pass | CALIBRATED 8/7/1/0 |
| NYISO | 2026-09-09-nyiso-221-fuelvintage-span | 2026-09-22-nyiso-hydro3-ror-split | pass → pass | **NOT-YET** 8/6/0/2 (see §1.3) |
| PJM | 2026-09-11-pjm-d4-4-gasoutage | 2026-09-23-pjm-h19-dbs-span | pass → pass | CALIBRATED 8/8/0/0 |
| SPP | 2026-09-12-spp-36-shortwindow-span | 2026-09-22-hydro-5-spp-floor | **fail → pass** | CALIBRATED 8/7/1/0 |

All six are promoter misses: the promoting lane re-keyed `keepers/<ISO>.json` and
`calibration-complete.json` (all six `complete` entries name the live keeper — verified) but not
the gate row. MISO's row was already current (miso-268 re-keyed its own).

### 1.2 SPP — the one leg that moved, and why it is a derivation, not a verdict

The prior SPP row's own stated reason for FAIL was *"SPP still has NO `complete` entry"*. SPP was
declared `complete` on **2026-09-13** (owner, session spp-40, verbatim *"Complete then run"*);
the declaring lane never touched this row, which therefore claimed `marker complete=False` against
a marker file reading `True` — the verdict-flipping half of F-5 that the guard exists to catch.
Charter §2.1b(2)(a) makes gate (a) = designated full-span keeper **AND** a `complete` entry; both
hold. So: leg (a) `pass`, `closed_on` `[a,b,c,d] → [b,c,d]`, `isos.SPP.marker_complete`
`"False" → "True"`, and a dated prefix on the two SPP notes saying their "never-declared marker"
clause is superseded. **Legs (b)/(c)/(d) and `open: false` are untouched** — SPP's forecast gate
does not open. **Director:** this is the only gate-state movement in the lane; reverse it if you
read the charter differently.

### 1.3 Reported, not adjudicated — NYISO holds `complete` on a NOT-YET keeper

`status/NYISO.js` reads **NOT-YET** on hydro3-ror-split (2023: `fuelmix` and `price_tail` FAIL),
and `calibration-complete.json` `complete.NYISO.determination` itself says `NOT-YET`. The Q5
uniform rule (*"a `complete` marker cannot stand on a NOT-YET keeper"*, owner r#12 2026-08-30)
has withdrawn this marker twice before. Gate (a) does not read determinations, so the row keeps
the charter reading (`pass`). **Routed to the NYISO desk and the owner**: apply or waive Q5.

### 1.4 Other observations (not in the guard's scope, not edited)

* The ISO-level `isos.<ISO>.keeper` field (distinct from the gate row) still names old keepers for
  ERCOT, CAISO, PJM, NYISO, NEISO, SPP. It appears to record the keeper the forecast campaign
  stood on; nothing checks it. **Routed to the forecast desk** to confirm its meaning or re-key it.
* `calibration-complete.json` `determination` prose for CAISO and SPP names the run that was
  keeper when the prose was written (caiso-288, spp-51), not the live keeper — narrative, not
  identity. M1 passes.
* NWPP and SOCO have keeper shards but no forecast-board row (the guard prints a note). Routed to
  the forecast desk.

## 2. SOCO E13 — NOT pruned, and the reason is rule 31

`2026-09-20-soco53g-prb-own-iso` is **not** soco61's superseded predecessor (that was
`2026-09-23-soco60-boundary-span`, pruned by SOCO-61 under rule 35). It is a **separate candidate
that has never been ruled on**: every SOCO promotion from SOCO-54 through SOCO-61 passed it to
`prune_iso_runs.py --keep` for exactly that reason (`docs/calibration-log/soco.md` lines ~1012,
1131–1135, 1309–1311, 1392; `FINDING-soco-55..57`; SOCO-56 asked for it as *"A SECOND RULING I AM
ASKING FOR"*). The owner's standing ruling that promoted soco61 names the recommended candidate
and does not dispose of soco53g. It is not a rung either (same 2023–2025 span as the keeper, no
`holdout` block), so rule 30(a) stamping would be false.

So the charter's premise does not hold: rule 31 `[R-RETAIN]` forbids the delete until the owner
rules. **E13 stays red.** **Owner question:** *decline `2026-09-20-soco53g-prb-own-iso` (the SOCO
desk's standing recommendation)?* A yes lets the next SOCO session run
`prune_iso_runs.py --iso SOCO` and E13 clears.

## 3. FR-22 — three filed GAPs (`scripts/lib/forecast_parity_registry.py`)

No forecast consumer invented. Each disposition is what the mechanism's own code and record give:

| field | ISO | disposition | basis |
|---|---|---|---|
| `nyiso_ct_peaker_committed_measured` | NYISO | GAP | Same class as the filed `caiso_ct_peaker_committed_measured`: band re-grounded on the class's own CAMPD `phys_committed` (0.843 vs fitted 1.35), a regenerable physical ratio, **not** in `_BACKCAST_ONLY_OVERLAY_FIELDS`; consumed only in `pipeline/backcast_config.py`. |
| `nyiso_st_gas_econ_bands_deleaked` | NYISO | GAP | Same class: rule-25 de-leak of ST_GAS econ bands onto the measured steam marginal; consumed only in `backcast_config.py`. |
| `coal_fuel_inventory_plant_grain` | MISO | GAP | Forward story (PRECOMMIT-miso268 §2) is the model's own carried per-yard inventory, **not built**; `run_calibration.py` raises on the parent outside `mode="backcast"`. |

Routed: NYISO rows → NYISO desk + forecast desk (wire-forward vs evidenced BACKCAST_ONLY, owner
ruling R-X). MISO row → MISO desk + forecast desk (build the carry, or declare backcast-only).

**Checker defect found, routed to the FR-22 owner, not repaired:** the parent
`coal_fuel_inventory` reads **FORECAST_WIRED** only because of
`string_key @ src/market_sim/data/input_completeness.py:235` — a completeness-report flag list,
not a consumer. The backcast orchestrator refuses the flag in forecast mode, so that reading is a
false positive. `input_completeness.py` likely belongs in `SOURCE_ROLES` as `bookkeeping`; that
is a gate-behaviour change (it may surface further UNACCOUNTED fields), so it is not made here.
It is also why the plant-grain row is GAP rather than `PARAMETER_OF coal_fuel_inventory`:
`PARAMETER_OF` would inherit the false wiring.

## 4. Fast-tier tests

**The auto-mode classifier refused this lane's test-file edits** (as "Modify Shared Resources"),
so no test file is changed in this PR. Each item says whether the record or the test is stale.
Where the test is stale, the change is written out below for the owner to approve.

| test | stale side | status |
|---|---|---|
| `test_audit_keepers_lineage::test_e11_set_mirrors_replay_ignore` | **code** — `audit_keepers.E11_META_PROVENANCE` had not mirrored `replay_keeper._IGNORE`'s `model_changes_note` (ercot-261) and `composed_from` (pjm-d4-3) | **FIXED** (2 set entries). `audit_keepers --check` output byte-identical before/after. Also on Y-30's list; this lane landed it. |
| `test_gate_a_provenance::test_live_board_passes` | record | **FIXED** by §1 (`check_gate_a_provenance.py` exit 0). |
| `test_forecast_parity::test_check_exits_zero_on_the_current_keepers` | record | **FIXED** by §3. |
| `test_forecast_parity::test_all_seven_keepers_resolve` | **test** — hard-codes 7 ISOs; SOCO + NWPP now carry keepers and resolve clean (45 / 43 armed, 0 unaccounted) | **HELD** — proposed: rename to `test_all_nine_keepers_resolve`, add `"SOCO", "NWPP"` to the set (rule 26: replace, don't hedge). |
| `test_calibration_verdict_price_unscored::test_no_registered_run_carries_the_block` | **test** — written before any SOCO/NWPP run was registered; soco53g, soco61, nwpp-49 now legitimately carry the no-price class | **HELD** — proposed: skip `_NO_BLOCK_ISOS` sidecars in the existing test (and assert the rest are in `_REGISTERED_ISOS`); add `test_no_block_registered_runs_reach_the_class` asserting SOCO/NWPP sidecars read `price_unscored`, never `CALIBRATED`, with a `PRICE UNSCORED` reason. |
| `test_ff_readiness_battery::test_marker_state_reflects_committed_markers` | **test** — pins `caiso-260-b1-demand` and `nyiso-221-fuelvintage-span` literals, and omits SPP from the `complete` set | **HELD** — proposed: `complete` set gains `SPP`; replace both keeper literals with `== json.load(keepers/<ISO>.json)["keeper"]` for every `complete` ISO, so a promotion that re-keys the marker keeps the test green and one that forgets fails it. `declared` pins stay. |
| `test_golden_manifest_provenance` ×8 | **both, and correctly red**: the committed goldens were captured on `ercot248` over 2023–2025; the live ERCOT forward config is `ercot266` over 2021–2025 | **HELD / ROUTED.** The manifests are *truthfully* stale — re-capture is board v42 §6 item 2 (queued, R-AI). The tests hard-code `ercot248` and `[2023,2024,2025]`; the proposal is to read the live partition from `keepers/ERCOT.json` and assert the coverage report says **STALE** (not CURRENT) while the capture record lags. Not written without the owner, because it changes what the golden gate accepts. |
| `test_ff_readiness_battery` ×4 others (`walk_inputs_trivial_single_year`, `resolve_report_no_hard_fail_full_horizon`, `ercot_confirmed_horizon_is_reported_not_failed`, `build_registration_scorecard_no_iso_gate_open`) | **environment** — `data/clean` confirmed-retirements partition unbuilt in a `code`-profile checkout | Not promotion debt; not touched. |

## 5. Bench stamp `64b6829fb757` — genuinely stale, NO entry added

History walk of `BUILDER_SOURCES` since 2026-09-01 (first-parent merges, AST fingerprints
recomputed per commit):

| merge | aggregate | payload |
|---|---|---|
| #5834 (09-09) | bee29e135d42 | 643eac24b565 |
| #6255 (09-16) | e80f0d6fcb96 | 7c262e068a96 |
| #6266 (09-16) | **64b6829fb757** | **5e60d68f23e9** |
| #6460 (09-22) | fb56b7e445d9 | **5b4b05dce3f3** (HEAD) |

The payload fingerprint moved at #6460: commit `7fd12b91e` edited `render_calibration_html.py`
(`bundle_input_path` → `require_bundle_input` for the eia923/eia930/campd frames). Per the
charter and the test's own instruction, **a moved payload source means no mapping entry**. At
pin time NEISO was also unresolved; it has since been rebuilt. Now unresolved: **ERCOT**
(`2021–2025`, 5 parts) and **CAISO** (`2022–2025`, 4 parts). `audit_keepers` already flags both
as STALE BENCHMARK.

**Routed to the ERCOT and CAISO desks:** `run_calibration_full.py --rebuild-benchmark <bundle>`
then `dashboard_add_run.py` (zero LP). The #6460 edit looks value-neutral (it only makes a
missing input raise instead of passing `None`), so the rebuilt parts should be byte-identical
in `bench` content. The rebuild confirms that; this lane does not assume it.

## 6. Proposal — stop the debt accruing at promotion time (NOT implemented)

The guards all exist and all run in CI (`audit_keepers --check`, `check_gate_a_provenance`,
`check_forecast_parity`, `check_golden_manifest`). Debt accrues anyway for two reasons:

1. **None of them blocks a merge.** `main` is `protected: false` (board reading 31), so a
   promotion PR merges red. The remedy already on the board is Card 1: branch protection with
   the keeper-integrity, FR-21 and FR-22 jobs **required**. This is the single highest-leverage
   fix, and it is the owner's.
2. **Some records are checked, but nothing ties them to the promoting PR.** Proposed:
   **`scripts/check_promotion_completeness.py`** (stdlib), run on PRs. For every ISO whose
   `keepers/<ISO>.json` `keeper` changed against the PR base, it FAILS unless in the same diff:
   (a) `check_gate_a_provenance --iso <ISO>` passes; (b) the `complete.<ISO>.keeper` (if the ISO
   holds `complete`) names the new keeper (M1 already checks this whole-tree); (c)
   `check_forecast_parity --iso <ISO>` has 0 UNACCOUNTED; (d) `audit_keepers` E13 is clean for
   the ISO; (e) a partitioned ISO's golden coverage report is re-run and its STALE line is
   quoted in the PR body. Scoping the check to the ISOs whose shard changed puts the failure on
   the promoter's PR, not the next unrelated one. It also adds a gating path, so under this lane's
   boundary it is **proposed only**. The calibration-report skill's promotion checklist should
   list the same five items.
3. **Tests that pin keeper ids** (§4) turn every promotion into a test-edit chore that promoters
   skip. The proposed test changes derive ids from the keeper shards, which removes that class.

## 7. Routing summary

| to | item |
|---|---|
| **owner** | SOCO: rule on `soco53g` (§2). Approve the held test edits (§4). Card 1 branch protection (§6). Director: confirm SPP leg (a) (§1.2). |
| NYISO desk | Q5 on a NOT-YET keeper holding `complete` (§1.3); two FR-22 GAPs (§3). |
| MISO desk | `coal_fuel_inventory_plant_grain` GAP (§3). |
| ERCOT, CAISO desks | `--rebuild-benchmark` for the stale bench parts (§5). |
| forecast desk / FR-22 owner | the three GAPs; `input_completeness.py` false positive (§3); `isos.<ISO>.keeper` meaning; NWPP/SOCO board rows (§1.4). |
| golden program (§6 item 2) | ERCOT re-capture on ercot266 over 2021–2025 (§4). |
