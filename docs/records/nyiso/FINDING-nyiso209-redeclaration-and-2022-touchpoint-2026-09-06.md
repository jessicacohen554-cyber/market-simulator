# FINDING — nyiso-209 (records + touchpoint half): NYISO `complete` and `frontier` RE-DECLARED on `2026-09-06-nyiso-202-startup-aware` by owner ruling; the 2022 validation touchpoint SPENT on the frozen recipe — NOT-YET on C1 / C3a / C3b, every miss smaller than the un-registered nyiso-189 diagnostic, and the ISO stays CALIBRATED under rule 30(c)

**Session:** nyiso-209, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-6l12xd`, off `main` `2a243bf9`. **Date:** 2026-09-06.
**Keeper:** `2026-09-06-nyiso-202-startup-aware` — **UNCHANGED**. No `ScenarioConfig` field, no
coefficient, no offer curve, no scorer, no derive script touched. **One LP spent: the 2022 year, on
the keeper's frozen recipe, under the owner's ruling.**

**The ruling, verbatim (owner, in session, 2026-09-06):** *"Ok declare it and run 22"* — in reply
to the lane's assessment that NYISO was *"not yet, on the record; on the merits, yes, and one
owner declaration away"*, which closed: *"If you rule 're-declare `complete` (and `frontier`) on
nyiso-202 and run 2022', I'll execute the records lane, launch the 2022 solve, and fold the
result."* The lane reads *"declare it"* as **both instruments**, per the Q39 precedent (2026-09-05:
*"both instruments, as the withdrawal removed both"*); the 2026-09-05 withdrawal removed both.

**Companion record (the first half of this session):**
`docs/FINDING-nyiso209-gas-bridge-params-reproduce-2026-09-06.md` — the zero-LP clean negative
that preceded the owner's question.

---

## 0. The result in one paragraph

NYISO holds `complete` again — its **fourth** grant — and `frontier` with it, both on the unchanged
keeper `2026-09-06-nyiso-202-startup-aware`, whose determination was re-verified from committed
artifacts at `2a243bf9` before any marker byte moved: **CALIBRATED, grade 7 of 8, fails 0, C3c the
lone ledgered caveat**. The withdrawn block's own `reentry` clause asked for exactly one thing — *"a
NEW explicit owner declaration on a designated keeper that scores CALIBRATED"* — and the ruling
supplied it. The forecast board's NYISO gate (a) moved **fail → pass** on the marker in the same
commit (rule R-T). The same ruling spent the 2022 validation touchpoint: the keeper recipe replayed
verbatim on 2022 (`--replay-bundle`, recipe identity **PASS, 0 differing keys, +0/−0 solve-surface
drift**), registered as `2026-09-06-nyiso-209-2022-touchpoint` and **stamped to the keeper** (rule
30 fold). It reads **NOT-YET**: C1 CC_REGULAR **+4.35 TWh / +3.3 pp**, C3a **−11.2 %**, C3b **NRMSE
0.227**; C3c 15 vs 101 h (caveat under rubric v3.6); C2 / C4 / C6 / C8 PASS. **Every degraded number
is smaller than the un-registered nyiso-189 diagnostic of 2026-09-05** (+5.19 TWh / +3.9 pp, −12.2 %,
0.240, 17 vs 101 h). Under rule 30(c) a held-out year never downgrades the ISO: **NYISO's
determination is CALIBRATED**, the rung is reported, and the touchpoint loop's step 2 is what it
hands forward.

---

## 1. Records half — what moved, surface by surface

Every edit was made on the parsed objects' exact text with the Edit tool; every untouched block is
byte-identical (asserted by JSON re-parse and by the auditor / guards in §3).

### 1.1 `frontend/data/backcast/calibration-complete.json`

| field | before | after |
|---|---|---|
| `complete` membership | {ERCOT, NEISO, PJM} | {ERCOT, NEISO, **NYISO**, PJM} — the three existing entries untouched |
| `complete.NYISO` | — | **NEW 12-field entry in the D56-R schema**: `declared` 2026-09-06 · `keeper` = `keeper_at_declaration` = nyiso-202 · `by` = the ruling verbatim, the reentry licence, the fact that the clause's *named* route back (the duct-burner offer) was NOT the route taken (nyiso-198 rejected it; C1-2024 returned to band structurally via nyiso-196 / nyiso-202), card C-19 / Q51 discharged · `determination` = CALIBRATED re-verified at `2a243bf9`, criterion by criterion with the C3c magnitudes · `tier_authorized` validation only, rule 30(c) stated · `locked_test` NOT AUTHORIZED, freeze covers it · `frontier_basis` = same ruling, both instruments, mechanism-set limb never retracted · `freeze_interaction` tier-scoped; **2022 SPENT by this ruling, 2020/2021 not** · `keeper_rekey_policy` D-5(b), Q5 stated (withdrawn twice that way) · `redeclaration` FOURTH grant, all three prior grants and withdrawals named · `prior_withdrawal_2026_09_05` (next row) |
| `withdrawn.NYISO` | the 2026-09-05 withdrawal record (nesting the D56-R entry and the 2026-08-30 / 2026-07-19 records) | **MOVED WHOLE** to `complete.NYISO.prior_withdrawal_2026_09_05`, verbatim, plus ONE dated `superseded` field. `withdrawn` holds **CAISO alone**. Nothing deleted. *(The nested block keeps its former indentation; the file is valid JSON but no longer round-trips its serializer byte-for-byte — cosmetic, and the same state D56-R once recorded.)* |
| top-level `note` | ended at the nyiso-193 withdrawal sentence | dated sentence **appended**: fourth grant, withdrawal nested, `withdrawn` = CAISO, frontier back, gate (a) pass, 2022 spent / 2020-2021 not, `final` and freeze untouched |
| `withdrawn.CAISO`, `final`, `intake_log`, `complete.{ERCOT,NEISO,PJM}` | — | **untouched** |

`holdout_policy.authorized(doc, "NYISO", "validation")` reads **True** and
`authorized(doc, "NYISO", "locked_test")` reads **False**; `frozen_tiers` = {locked_test}.

### 1.2 `frontend/data/backcast/keepers/NYISO.json`

| key | before | after |
|---|---|---|
| `frontier` | absent (`frontierActive()` FALSE) | **NEW live block, 8 fields in the 2026-09-05 shape**: `declared` 2026-09-06 · `keeper_at_declaration` nyiso-202 · `by` (the ruling, both instruments) · `note` (what it is: the exact inverse of the 2026-09-05 withdrawal, whose cause is gone by *structural* repair; what it claims: the never-retracted mechanism-set limb plus the restored determination limb; what it does NOT claim: C3c ledgered at full magnitude, rule 20 leg (a) and the unit-grain C8 exposure open, five owner cards unruled, the 2022 rung selection evidence only, NOT `final`) · `basis` · `supersedes` (seventh genealogy layer) · `not_final` · `recorded_by` |
| `frontier_withdrawn_2026_09_05` | 11 fields | **retained whole**, plus ONE dated `superseded` field |
| `keeper`, `promotion_note`, `determination_note`, `superseded`, `de_designation_history`, `frontier_withdrawn_2026_08_30`, `frontier_cleared`, `site_retention_note` | — | **untouched** |

`status/NYISO.js` rebuilt by `build_status.py --iso NYISO` — twice: once after the marker
(`[NYISO:CALIBRATED]`, frontier block embedded) and once after the touchpoint stamp (the holdout
ladder now carries the 2022 rung).

### 1.3 `frontend/data/forecast/program-status.json`

| field | before | after |
|---|---|---|
| `isos.NYISO.gate.a_keeper_marker.status` | **fail** | **pass** — on the re-declared marker |
| `…a_keeper_marker.detail` | fail-form (nyiso-202 re-key) | pass-form: keeper, determination, marker complete=True; the ruling; C-19 / Q51 discharged; what the marker grants and that the 2022 rung lives on the backcast side only and cannot move this leg; the (a)/(b)/(c)/(d) reading; §2.1b candidacy re-opened for the director; re-key genealogy. **Prior fail-form detail preserved verbatim inside it** (sha256[:12] `ebf89cfa1da8`) |
| `…read_live_at` / `corrected_by` | `2617a5d3` / nyiso-202 re-key | `2a243bf9` / this lane, "THE GATE VERDICT MOVED (fail → pass) on the marker"; prior text kept |
| `isos.NYISO.gate.closed_on` / `note` | `["a"]` / nyiso-193 note | `[]` / dated nyiso-209 note **prepended**, prior preserved verbatim inside |
| `isos.NYISO.marker_complete` / `keeper` (display) | false / `…nyiso-192-astoria-panel` (two promotions stale) | **true** / `2026-09-06-nyiso-202-startup-aware` |
| `generated` | 2026-09-05 | 2026-09-06 |
| `gate_a_provenance.derived_at_sha/date/derived_by` | `9da4f567` (NEISO re-key) | `2a243bf9`, one row re-derived, passer set = `complete` membership; prior stamp text kept; `note` / `inputs` untouched |
| `sources` | 32 | 33 (this lane's edit prepended) |
| *(new)* `nyiso209_redeclaration` | — | records block in the `nyiso193_promotion_withdrawal` convention (note / lane / derived_at_* / derived_from / what_changed / what_did_NOT_change / flagged_not_edited); avoids the forecast-provenance field names by design |
| legs (b)/(c)/(d), `open`, every other NYISO field, all five other ISO blocks, every other top-level block | — | **untouched** |

### 1.4 Test pin, matrix shard

- `tests/scoring/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers` —
  the marker pin moved with the marker in the same commit (NYISO `complete` on nyiso-202, declared
  2026-09-06; CAISO the sole `withdrawn`), with a dated comment in the test's own desync-class
  convention.
- `docs/codebase-site/data/mechanism-matrix/NYISO.js` `gates` stamp — a dated "(nyiso-209 records
  half) MARKER RE-DECLARED, NO VERDICT LETTER MOVES" sentence **prepended** (rule 28(d)); no cell
  verdict moved; key set verified identical to `main`; `node --check` passes.

## 2. Touchpoint half — the 2022 spend

### 2.1 Zero-LP gate before the spend

`scripts/lib/bundle_fleet.reconstruct_bundle_fleet(nyiso202_startup_aware, 2022)` — the no-LP
fleet rebuild the 2026-09-05 completeness pass used as its loader-resolvability proof — **passed**:
815 units, 6 zones, 152.68 TWh demand, HH 2022 auto-resolved at $6.45, every 2022 overlay
resolved (LI N-1-1 TSL 940 MW row present, NY Harbor ULSD 2022 daily 249 rows, market solar 2022
rows, weather 2022 365 days, LMP bench 2022, CAMPD NY/NJ 2022 extracts).

### 2.2 The solve

```
run_calibration_full.py --iso NYISO --replay-bundle results/calibration/nyiso202_startup_aware
  --year 2022 --holdout-authorized --out-dir results/calibration/nyiso209_2022_touchpoint
```

Launch gate: *"solving designated validation-tier holdout year(s) [2022] under
--holdout-authorized ('complete' marker present)"*. One year, sequential, ~10 min wall.
Registration gate (R-AZ, re-checked at `dashboard_add_run.py`): passed on the re-declared marker.

**Recipe identity is COMPUTED, not asserted** (`scripts/gen_touchpoint_attestation.py`): **0
differing shared `meta.json` keys** outside the provenance set; solve-surface drift **+0 / −0
kwargs** (keeper `c7523509` → replay `2a243bf9`). Nothing was tuned for, against, or in response
to 2022.

### 2.3 The verdict — `2026-09-06-nyiso-209-2022-touchpoint`

| criterion | tier | keeper in-sample 2023–25 | **2022 touchpoint** | nyiso-189 diagnostic (2026-09-05, un-registered) |
|---|---|---|---|---|
| C1 fuel-mix by class | LOAD | PASS 14/14 | **FAIL** — CC_REGULAR **+4.35 TWh / +3.3 pp** (6/7; free 4/5) | +5.19 TWh / +3.9 pp |
| C2 system volume | LOAD | PASS | PASS | PASS |
| C3a mean LMP | LOAD | +5.7 / +6.5 / −6.3 % | **FAIL −11.2 %** (−7.4 % vs DA; DA−RT premium −$3.33; model $67.96) | −12.2 % |
| C3b price shape | LOAD | 0.124 / 0.185 / 0.152 | **FAIL NRMSE 0.227** | 0.240 |
| C3c price tail (RT >$300) | SUPP | CAVEAT 3/10, 1/13, 4/42 h | **CAVEAT 15 vs 101 h (0.15×)** — rubric v3.6, ledgered | 17 vs 101 h |
| C4 dispatch correlation | SUPP | PASS | PASS | PASS |
| C6 governance | PROT | PASS | PASS (touchpoint attestation, recipe identity computed) | PASS |
| C8 forced share (D-2) | PROT | PASS | PASS | PASS |
| C5a CO2 vs eGRID (reported) | — | +1.7 / +0.4 / +4.5 % | +2.6 % | +2.5 % |
| D-A diurnal amplitude (reported) | — | 65 / 54 / 43 % | 65.3 % of measured, phase h17/h03 correct, hod r +0.871 | 66 % |
| **Determination** | | **CALIBRATED** | **NOT-YET** (3 degraded, 1 carried, 4 held) | NOT-YET |

**Every degraded number moved toward its actual** between the nyiso-189 diagnostic and this
keeper — CC_REGULAR −0.84 TWh / −0.6 pp, C3a +1.0 pt, C3b −0.013, C3c +2 h — with zero
in-sample criterion flips across the two promotions in between (nyiso-196, nyiso-202: both
structural, both zero-DOF). That is the touchpoint loop working in the direction it should: the
2023–2025 repairs generalize, partially, to a year they never saw.

### 2.4 Reading (touchpoint loop step 2 — the object, never a tuning claim)

2022 is a **gas-year level miss**: CC_REGULAR over-dispatched **+4.35 TWh** while the system
price sits **11 % low**, in a **$6.45 Henry Hub** year carrying the largest downstate
basis / oil-parity exposure of the span, with shape, dispatch correlation (C4), volume (C2) and
forcing legitimacy (C8) all held. It is the **same CC_REGULAR sign** the in-sample keeper carries
in 2024 (+2.39 TWh, inside band) — the cell-G out-of-market-commitment fill — scaled up by the
2022 fuel regime. This is **not** a new object: it is the one nyiso-201 §5.3 / nyiso-203 named
(the NYC persistent-base limb's basis) and `DECISION-CARD-nyiso193` §5/§5.1 carries (unit-grain
C8 re-base), plus the winter downstate locational premium `INTAKE-SPEC-nyiso156` Leg 2 left
blocked on identification. The touchpoint says those are the right objects and that the price
side (C3a/C3b, both PASS in-sample) is where 2022 diverges most. **No parameter is identified
against 2022 here, and none may be** (rule 22 step 3: fitting happens only on 2023–2025).

### 2.5 What is registered, and how it renders

- Bundle `results/calibration/nyiso209_2022_touchpoint/` — slim files + `hourly/` sidecars
  (`class_band_hourly`, `class_hourly`, `reserve_family`, `storage`, `system` for 2022; the prior
  touchpoint pattern), `legitimacy_diagnostics.json` (D-1 … D-10; **D-10: wind/solar ride the L1
  delivered-outcome bound, advisory-only, never gating**), `calibration_attestation.json`
  (touchpoint form, carried sections from the keeper), `metrics.json`.
- Sidecar `frontend/data/backcast/registry/2026-09-06-nyiso-209-2022-touchpoint.json` **stamped**
  `holdout.keeper = 2026-09-06-nyiso-202-startup-aware` (`stamp_touchpoint_holdout.py`): tier
  validation, keeperDetermination CALIBRATED, holdoutDetermination NOT-YET, nDegraded 3,
  nCarried 1. Per rule 30(a) the Run Explorer hides it from the run list and renders 2022 as an
  ordinary year column in the keeper's Report; a deep link to the id resolves to the keeper.
- Payload `runs/2026-09-06-nyiso-209-2022-touchpoint.js` (224 KB) and bench part
  `bench/NYISO/2022.json.gz` (183 KB).
- `status/NYISO.js` — the Calibration Status page's per-year holdout ladder carries the 2022 rung
  with the Tier column and the "reported, not gating" line (rule 30(b)).

**Rule 30(c), stated in place:** the ISO's determination is the train-tier verdict and nothing
else. NYISO reads **CALIBRATED**; the NOT-YET rung beside it is not a contradiction.

## 3. Guards, auditors and tests

| check | result |
|---|---|
| `scripts/calibration_verdict.py --run-id 2026-09-06-nyiso-202-startup-aware` at `2a243bf9` | CALIBRATED, grade 7 of 8, fails 0, C3c lone ledgered — **not worse** than the promotion determination (D-5(b) stop did not fire) |
| `scripts/audit_keepers.py --iso NYISO` (after marker; after stamp + status rebuild) | **PASS 0 failures / 0 warnings** (M1a marker keeper == shard keeper; M1b CALIBRATED == live verdict; holdout / marker / status checks all pass) |
| `scripts/check_gate_a_provenance.py` | NYISO row OK; **one pre-existing failure, CAISO's**: its gate-(a) row cites the superseded `2026-09-06-caiso-257-b1-ctonly` while `keepers/CAISO.json` names `2026-09-06-caiso-260-b1-demand` — another lane's stale stamp (audit board F-5), **not fixed here** (rule 25) |
| `scripts/check_registry_payload_parity.py` | OK (17 runs, 50 bundle dirs, 0 tolerated) before registration |
| `scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` (after registration) | **Overall PASS** — D-9 overlay quarantine PASS, **D-6 holdout quarantine PASS** over every registered bundle with the 2022 sidecar present |
| `scripts/check_mechanism_matrix.py`; `node --check` NYISO shard; key-set diff vs `main` | clean for NYISO (two pre-existing anchor-drift warnings on other rows); parses; identical |
| `pytest tests/scoring/{test_gate_a_provenance,test_audit_keepers,test_holdout_year_gate,test_ff_readiness_battery,test_legitimacy_diagnostics}.py -m "not integration"` | **189 passed, 1 failed** — `test_gate_a_provenance::test_live_board_passes`, the same CAISO stale stamp above |

### 3.1 Reported, not fixed — other lanes

- CAISO gate-(a) stamp stale (above). Owner of the CAISO lane; a one-field re-key under Q34.
- The six charter-named files re-measured earlier this session: **36 failed / 69 passed** (one
  fewer than nyiso-208; `test_constants_facade::test_moved_surface_is_complete` now passes on
  main). Unchanged by this half.

## 4. What is deliberately NOT done

- **2020 and 2021 are NOT spent.** The ruling said "run 22"; the ladder's lower rungs remain
  available under the marker and are a separate spend.
- **No re-tune.** Step 3 of the touchpoint loop (re-train on 2023–2025 around what 2022 surfaced)
  is the next lane's work and is owner-charterable; nothing here selects a mechanism or moves a
  value.
- **No marker beyond the ruling.** `final` is untouched (still empty); the locked test
  (2019 / H1-2026) is never granted and stays frozen; `holdout-freeze.json` untouched.
- **No prune.** The touchpoint is stamped to the keeper, so rule 15's keeper-only retention
  keeps it; no other NYISO run exists to prune.
- **No offer-curve, level or `offer_curve_by_group` change** (owner court).
- **The five pending owner cards stay UNRULED** (nyiso-193 §5/§5.1, -206, -207, -208, nyiso-203
  §6). The 2022 result bears on which of them matters most (§2.4) and rules none.

## 5. Governance

| item | state |
|---|---|
| **Owner act** | the ruling verbatim in every record that cites it; both instruments; executed by the session that received it |
| **Keeper** | `2026-09-06-nyiso-202-startup-aware`, UNCHANGED; no promotion, no re-stamp of the keeper id |
| **D-5(b)** | determination re-verified artifact-only BEFORE the marker was written; not worse |
| **Rule 22** | one validation-tier year solved, scored and registered under the re-declared marker and `--holdout-authorized`; locked test untouched; **nothing identified against 2022** |
| **Rule 30** | (a) stamped to the keeper, folded; (b) status ladder rebuilt per year; (c) ISO headline untouched, stated on both surfaces |
| **Rule 28(d)** | NYISO shard `gates` stamp; key set identical to `main` |
| **Rule R-T / Q34** | gate (a) re-keyed in the same commit as the marker |
| **Rule 15** | run registered the moment it finished; bundle + sidecar + payload + bench + status committed and pushed in this session |
| **Rule 27** | every pushed file ≥ 300 lines blob-verified against the remote before the next commit |
| **Rule 29(c)** | no screen and no control bundle exist; the touchpoint bundle is a registered run, not a screen |
| **Files** | 6 records files (§1), the touchpoint bundle + 3 dashboard files + status part, this finding, the calibration-log entry |

---

*(nyiso-209, records + touchpoint half, 2026-09-06. One owner ruling executed on four surfaces in
one commit; one LP spent on the year it named; the result folded onto the keeper and reported at
full magnitude, in the direction it moved.)*
