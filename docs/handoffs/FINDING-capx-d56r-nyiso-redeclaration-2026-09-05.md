# FINDING — capx D56-R: NYISO `complete` RE-DECLARED on `2026-09-05-nyiso-189-steam-identity` (owner ruling Q38) — the validation tier returns, NOTHING is spent, NOTHING is solved; the frontier leg stays split pending card C-10 — 2026-09-05

**Lane:** D56-R, capacity-expansion track, GOVERNANCE RECORDS lane (pack §D56-R; capx
ledger §0ag.3; the original §D56 charter binds verbatim with nyiso-188 replaced by nyiso-189).
**Model:** Fable (a marker consequence). **Branch:**
`claude/capx-d56r-nyiso-redeclaration-rme0qs`, fresh off `origin/main` `c9f1d26e`, rebased
onto `f539ca3c` and then `db057c5d` before the push; every provenance leaf below names `db057c5d`, the sha the
keeper, marker and verdict were RE-READ at after that rebase (desk doctrine X-6b).
**Scope:** RECORDS ONLY — zero LP, zero solve, zero re-score, zero registration, no keeper
change, no out-of-training year touched in any way.

---

## 0. The result in one paragraph

`complete.NYISO` exists again in `frontend/data/backcast/calibration-complete.json`,
declared 2026-09-05 on `2026-09-05-nyiso-189-steam-identity` (keeper =
`keeper_at_declaration`), with the determination RE-VERIFIED artifact-only first
(CALIBRATED; C3c the lone ledgered caveat) and the 2026-08-30 withdrawal record moved
WHOLE beneath it. `scripts/audit_keepers.py` reads PASS with M1a/M1b holding;
`holdout_policy.authorized(NYISO, validation)` flips False → True and the locked tier stays
False; the forecast board's NYISO gate (a) re-derives FAIL → PASS on the literal
§2.1b(2)(a) test with `check_gate_a_provenance.py` OK 6/6. NYISO reads (a) PASS · (b) PASS ·
(c) PASS · (d) none — its §2.1b candidacy re-opens; a campaign remains a separate owner
grant. **The frontier leg is NOT re-asserted**: card C-10 carries no Q39 ruling in ledger
§3 at `db057c5d`, so `frontier_basis` reads NONE CLAIMED, `keepers/NYISO.json` `frontier`
stays withdrawn, and the four-instrument alignment is split on `frontier` alone by the
owner's pending choice — stated, never silent. **This lane spent NOTHING and solved
NOTHING.**

---

## 1. The ruling, verbatim, with its provenance — and the R-AG / Q38 record

**Q38** (capx ledger §3): *"RULED 2026-09-04 (r#35) — RE-DECLARE NOW via records lane D56.
Validation tier re-authorized, nothing spent; gate (a) flips to PASS; D-5(b) duty attaches.
§0af amendment 1."* Card C-9's option, verbatim label: **"Re-declare now via a records
lane"** (§0af: *"re-declare now via a records lane / wait for keeper stability /
decline"*). §0af amendment 1: *"C-9 → Q38: RE-DECLARE NOW via a records lane — D56 ISSUED
(pack §D56; Fable — a marker consequence). The declaration is an OWNER act executed by the
lane per the withdrawn block's own `reentry` clause ('a NEW explicit owner declaration … on a
designated keeper that scores CALIBRATED')."*

**The licence** is the withdrawn block's own `reentry` field (now nested at
`complete.NYISO.prior_withdrawal_2026_08_30.reentry`): *"RE-ENTRY IS A NEW EXPLICIT OWNER
DECLARATION, never an automatic restoration: NYISO re-enters `complete` only when the owner
declares it again on a designated keeper that scores CALIBRATED."*

**The cross-desk record, verbatim from audit board v27 (Z-4) and capx ledger §0ag.5 / §3
r#36 header — recorded here as the charter's limb B requires, re-litigating nothing:**
owner ruling **R-AG** (2026-09-04 22:20Z, the audit sitting) *"route the NYISO `complete`
re-declaration question to the calibration director for a recommendation; the audit board
records the split as a real state with its cause; no marker edit by any audit lane"* —
recorded nowhere until the audit board's own v27 entry. **Q38** (23:18Z, the capx desk)
ruled the execution 58 minutes later without sight of it. Ledger §3 r#36: *"Both are the
owner's; they coexist; C-10 is the recommendation R-AG asked for."* This lane executes Q38
(and would execute Q39 if ruled — §6). Neither ruling is adjudicated against the other here.

**Why nyiso-189 and not nyiso-188.** D56 was issued on nyiso-188 and never launched (ledger
§0ag.1: no branch, no commit, marker unchanged). nyiso-189 superseded 188 on 2026-09-05 (PR
#4743, the owner's Bethlehem form B2), CALIBRATED → CALIBRATED, and re-keyed its own gate-(a)
stamp. §D56's own stop clause anticipated the move: re-run step 1 on the new id; declare only
if it reads CALIBRATED. It does (§2).

---

## 2. Step 1 — the artifact-only re-verification (run FIRST, and again after the rebase)

`python3 scripts/calibration_verdict.py --run-id 2026-09-05-nyiso-189-steam-identity`
at `c9f1d26e` and again at `db057c5d` (identical output):

| criterion | tier | status | detail |
|---|---|---|---|
| C1 fuel-mix by class | LOAD | PASS | 14/14; D-10 free 10/10 (pinned CC_CHP, ST_CHP); 2025 per-class rows SKIPPED on the preliminary EIA-923 vintage, covered by C2 |
| C2 system volume | LOAD | PASS | 2025 gas −1.0 % |
| C3a mean LMP | LOAD | PASS | +4.9 / +1.7 / −8.3 % vs ±10 % |
| C3b price shape | LOAD | PASS | 0.119 / 0.166 / 0.177 vs ≤0.20 |
| **C3c price tail (RT hourly)** | SUPP | **CAVEAT [ledgered]** | >$300 RT hours: 2023 model 3 vs actual 10 (0.30×); 2024 0 vs 13 (0.00×); 2025 4 vs 42 (0.10×) — ACCEPTED MODEL-CLASS LIMITATION, rubric v3.3 standing rule; NOT a PASS; 1 of 1 ledgerable slot |
| C4 dispatch correlation | SUPP | PASS | |
| C6 governance | PROT | PASS | attested, computed premises |
| C8 forced-energy share | PROT | PASS | |
| **Determination** | | **CALIBRATED** | grade 7 of 8, fails 0, 1 ledgered caveat |

This is the same reading the keeper's own promotion recorded (`keepers/NYISO.json`
`determination_note`, 2026-09-05) and the same the audit board v27 re-derived on the
superseded nyiso-188. The charter premise ("a CALIBRATED reading") holds on the live keeper.

**Stop-clause C, executed before every push:** `keepers/NYISO.json` re-read at `c9f1d26e`
at `f539ca3c` and at `db057c5d` (the lane rebased twice; every stamp names the last pin) →
`2026-09-05-nyiso-189-steam-identity` each time. The commits that landed on `origin/main`
during this lane (`c9f1d26e..db057c5d`) are three PREREG documents (caiso-247, miso-214,
nyiso-190) and the PERF-B s3 finding (#4755); none touches a keeper shard, the marker, the
board or any file this lane edits. No re-key was needed.

---

## 3. Before/after — every changed field, both surfaces (the Q5-W §3 format, inverted)

### 3.1 `frontend/data/backcast/calibration-complete.json`

Serializer used: the file's own — `json.dumps(obj, indent=1, ensure_ascii=False)`, no
trailing newline. Byte round-trip of the pre-edit file verified before editing; leaves
edited on the parsed object; re-serialized; byte-identity of every untouched block asserted
programmatically (`intake_log`, `final`, `withdrawn.CAISO`, `complete.ERCOT`,
`complete.NEISO`, `complete.PJM`, top-level key order).

| Field | Before (`c9f1d26e`) | After |
|---|---|---|
| `complete` membership | {ERCOT, NEISO, PJM} | {ERCOT, NEISO, **NYISO**, PJM} — the three existing entries byte-identical |
| `complete.NYISO` | — | **NEW 12-field entry in the PJM/ERCOT schema:** `declared` 2026-09-05 · `keeper` = `keeper_at_declaration` = `2026-09-05-nyiso-189-steam-identity` · `by` = Q38 verbatim with §0af amendment 1 / §3 citations, the `reentry` licence, the D56 → D56-R relaunch, and the R-AG / Q38 / C-10 cross-desk record · `determination` = "CALIBRATED on … RE-VERIFIED 2026-09-05 without a solve (scripts/calibration_verdict.py --run-id, committed artifacts only, at origin/main db057c5d): …" with every criterion and the C3c magnitudes (§2) · `tier_authorized` validation ONLY (2022 + 2020/2021 ladder; the touchpoint loop's rules) · `locked_test` NOT AUTHORIZED (absent from `final`; never scored 2019/H1-2026; freeze covers the tier) · `frontier_basis` **NONE CLAIMED** (§6) · `freeze_interaction` tier-scoped, validation spendable, NOTHING spent · `keeper_rekey_policy` D-5(b) with the Q5 uniform rule stated · `redeclaration` THIRD grant naming both prior grants and withdrawals · `prior_withdrawal_2026_08_30` (next row) |
| `withdrawn.NYISO` | the 2026-08-30 withdrawal record (20 fields, 11-entry `rekey_history`, the 2026-07-19 record nested as `prior_withdrawal_2026_07_19`) | **MOVED WHOLE** to `complete.NYISO.prior_withdrawal_2026_08_30` — byte-verbatim (asserted against the pre-edit serialization), plus ONE added dated field `superseded` ("SUPERSEDED 2026-09-05: NYISO re-declared … Retained WHOLE as the historical record …"), exactly as the 2026-07-31 re-declaration nested the 2026-07-19 record. Nothing deleted. `withdrawn` now holds CAISO alone. |
| top-level `note` | ended at the Q5 UNIFORM RULE sentence | **appended** (dated): NYISO re-declared 2026-09-05 by Q38 on nyiso-189, third grant, withdrawal nested whole, validation re-authorized / nothing spent, `final` and freeze untouched, `frontier` not re-asserted pending C-10 |
| `withdrawn.CAISO`, `final`, `intake_log` | — | **byte-identical**, asserted |

Schema note: `_marker_state` (`scripts/ff_readiness_battery.py`) reads `complete.NYISO`
first, so the nested withdrawal is invisible to it by construction; `holdout_policy` reads
only `complete` / `final`; `audit_keepers` M1 iterates `complete` and now audits NYISO.

### 3.2 `frontend/data/forecast/program-status.json`

Serializer used: the file's own — `json.dumps(obj, indent=1, ensure_ascii=True)` plus a
trailing newline (byte round-trip verified pre-edit; the charter's note that the file was
no longer round-trippable does not hold at this HEAD). Leaves edited on the parsed object;
byte-identity asserted for every other ISO's block, for every NYISO field outside `gate` /
`marker_complete` / `keeper`, for every NYISO gate leg other than (a) / `closed_on` /
`note`, and for every top-level block not named below.

| Field | Before | After |
|---|---|---|
| `generated` | 2026-09-01 | 2026-09-05 |
| `isos.NYISO.gate.a_keeper_marker.status` | **fail** | **pass** — on the re-declared marker; charter §2.1b(2)(a)'s second condition holds again |
| `…a_keeper_marker.detail` | fail-form, keyed to nyiso-189 (re-keyed by the promoting lane), carrying the Q5-W withdrawal narrative and the v23 / nyiso-186/187/189 re-key genealogy | **rewritten in the ERCOT/PJM/NEISO pass form**: `keeper 2026-09-05-nyiso-189-steam-identity (full-span 2023-2025, rule 16); determination CALIBRATED …; marker complete=True final=False.` + the Q38 citation, the relaunch, the artifact-only re-verification, the R-AG record, the frontier leg stated as split pending C-10, what the marker grants, the (a)/(b)/(c)/(d) reading, and the re-key genealogy carried forward in one sentence. The prior fail-form text is preserved in git at `db057c5d` and its sha256[:12] `dfa6d55a1fd4` is named inside the new detail. |
| `…a_keeper_marker.read_live_at` / `corrected_by` | `c73f78f5` / audit records lane v23 (2026-09-03) | `db057c5d` / capx records lane D56-R (2026-09-05) executing Q38, "THE GATE VERDICT MOVED (fail → pass) on the marker" — derivation-stamp convention only; **no forecast-provenance field names written** |
| `isos.NYISO.gate.closed_on` | `["a"]` | `[]` — the board's 'd'-omission convention left as flagged (D7 / Q5-W); `open` stays false on the absent leg (d) |
| `isos.NYISO.gate.note` | "NO LONGER THE PROGRAM'S LEAD ISO … (a) fail · (b) PASS · (c) PASS · (d) none" | rewritten: (a)+(b)+(c) held, (d) none, `open` false and why, §2.1b candidacy re-opened, a campaign a SEPARATE owner grant (D52 landed at r#36 — arming is card C-12; D59 issued); **prior note preserved verbatim inside it** |
| `isos.NYISO.marker_complete` | false | true |
| `isos.NYISO.keeper` (display) | `2026-08-30-nyiso-159-loss-surface` (three promotions stale) | `2026-09-05-nyiso-189-steam-identity` — the Q5-W inverse; the shard itself untouched |
| `headline` | the D19 reconcile text | a dated D56-R lead paragraph **prepended**; the D19 text kept verbatim with its two stale facts **annotated in place** (`complete` membership; the leg-count line) |
| `gate_reading` | the D19 leg map | the leg-(a) membership sentence and the "WHERE THAT LEAVES THE SIX" sentence **annotated in place** (`[D56-R 2026-09-05: …]`); everything else byte-unchanged |
| `sources` | 29 | 31 — the Q38 / §0ag citation and this finding appended |
| `gate_a_provenance` | derived at `e75250c7` (r#36 MISO re-key), passers {ERCOT, PJM, NEISO} | `derived_at_sha` `db057c5d`, `derived_at_date` 2026-09-05, `derived_by` rewritten (one row re-derived, passers {ERCOT, NEISO, NYISO, PJM} = `complete` membership); `note` and `inputs` byte-identical |
| *(new)* `d56r_nyiso_redeclaration` | — | records block in the `q5w_marker_withdrawal` convention: note (not a scoring stamp) · lane · derived_at_date/sha · derived_from · what_changed · what_did_NOT_change · flagged_not_edited |

**Untouched on the board, asserted programmatically:** leg (b) `b_t1f_verdict` (bare
`nyiso-t1f` PROMOTE, caveats []), legs (c)/(d), `c_readiness`, `c_cost`, NYISO's
`t1f_determination` / `t1x_determination` / `t1h_*` / `fc` / `blocking_rows` / `golden` /
`candidate` / `flip` / `tier_reached` / `marker_final`, and the **entire blocks of all five
other ISOs**; `readiness`, `tier_ladder`, `flip_config`, `honest_unfit`, `open_frontier`,
`readiness_limits`, `refresh` and every prior records block.

---

## 4. The validation-tier consequence — re-authorized, NOTHING spent

Verified post-edit against the live files via `scripts/lib/holdout_policy.py`:

| ISO | authorized(validation) | authorized(locked_test) |
|---|---|---|
| **NYISO** | **True** (was False) | False (unchanged — never authorized) |
| NEISO / PJM / ERCOT | True (unchanged) | False |
| CAISO / MISO | False (unchanged) | False |
| `frozen_tiers` | | `{locked_test}` (freeze file untouched) |

What returns is exactly rule 22's touchpoint loop for 2020–2022: solve the touchpoint on
the frozen keeper recipe under `--holdout-authorized`; diagnose the OBJECT it surfaces;
re-train on 2023–2025 around it; re-test; never fit anything to the touchpoint. A touchpoint
number is selection evidence, never a skill claim. **Nothing was ever spent under the prior
marker** (Q5-W §4: all NYISO sidecars declare years ⊂ {2023, 2024, 2025}; `bench/NYISO/`
holds 2023–2025 only) and **nothing is spent by this act**: the CI-tier D-6 sweep
(`legitimacy_diagnostics.py --keepers --no-d2-recompute`) reads PASS over all registered
bundles after the edit, with the only registered touchpoints still PJM 2022 and NEISO 2022.
The locked test (2019, H1-2026) stays NEVER GRANTED and frozen for every ISO; `final` is
byte-identical (still `_note` only).

---

## 5. Auditor, guard and test outputs (run after the edits, again after the rebase)

| Check | Result |
|---|---|
| `scripts/audit_keepers.py --iso NYISO` | **PASS — 0 failures, 0 warnings**; M1a (marker keeper == shard keeper) and M1b (asserted token CALIBRATED == live `calibration_verdict.determine`) both hold on `complete.NYISO`; the auditor asked for **no** shard stamp |
| `scripts/audit_keepers.py --check` (CI form) | PASS 0/0, exit 0 |
| `scripts/check_gate_a_provenance.py` | **OK 6/6** (keeper identity + marker state match the backcast store; no determination read) |
| `scripts/check_forecast_staleness.py` | exit 0 — the D56-R records block is **not** read as a re-score; its two pre-existing WARNs (fresher hindcast sidecars; 25 never-re-scored stamps) predate and are untouched by this lane |
| `scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` | exit 0 — Overall PASS; D-9 PASS; **D-6 holdout quarantine PASS over all registered bundles** |
| `scripts/check_registry_payload_parity.py` | OK (66 runs, 108 bundle dirs, 0 tolerated) |
| `scripts/check_mechanism_matrix.py` | clean before and after the shard stamp (keeper stamps and §5.x headers match every shard) |
| `node --check` on all seven matrix files | OK after the one-character repair (§7) — the NYISO shard did NOT parse at HEAD |
| `pytest tests/scoring/{test_gate_a_provenance,test_audit_keepers,test_holdout_year_gate,test_ff_readiness_battery,test_legitimacy_diagnostics}.py -m "not integration"` | **189 passed** after the marker-pin move in §8 |

---

## 6. Four-instrument alignment — the frontier leg is SPLIT BY THE OWNER'S PENDING CHOICE

Card **C-10** (ledger §0ag.5): the director's recommendation, as R-AG asked, is option **A** —
re-declare `complete` AND `frontier` together on nyiso-189. Options B (`complete` only,
frontier read as optional) and C (decline both) were also served. **At `db057c5d` ledger §3
carries NO Q39 row** (grep over the ledger and the audit board: the only "Q39" is the r#36
header's "Rulings, when given, are Q39–Q41"). Pack §D56-R limb A therefore applies its
no-ruling branch: `frontier_basis` = NONE CLAIMED, the shard's `frontier` untouched, and the
split stated here:

| instrument | membership after this lane | source |
|---|---|---|
| `frontier` in `keepers/<ISO>.json` | **{ERCOT, NEISO, PJM}** — NYISO `frontier.withdrawn` 2026-08-30 stands | keeper shards (untouched) |
| `complete` marker | **{ERCOT, NEISO, NYISO, PJM}** | `calibration-complete.json` (this lane) |
| gate-(a) `status: pass` | **{ERCOT, NEISO, NYISO, PJM}** — guard OK 6/6 | `program-status.json` (this lane) |
| ISO-level determination CALIBRATED | **{ERCOT, NEISO, NYISO, PJM}** | `status/<ISO>.js` (untouched) |

Three of four instruments now agree at four ISOs; `frontier` is the odd one out **because
the owner has not yet chosen**, not by omission. If Q39 rules A, the executing session
re-declares `frontier` in `keepers/NYISO.json` in the ERCOT/PJM/NEISO shape (the inverse of
the 2026-08-30 withdrawal's `withdrawn` / `withdrawn_note` fields), rewrites
`frontier_basis` in the marker to name it, and re-stamps this table; if B, this table is the
steady state and `frontier_basis` stays as written. Routed to the audit board (its Z-4 row)
and the capx desk.

---

## 7. Rule 28(d) — the NYISO matrix shard stamp, and one disclosed side repair

`docs/codebase-site/data/mechanism-matrix/NYISO.js`: a dated "(2026-09-05, records lane
D56-R) MARKER RE-DECLARED, NO VERDICT LETTER MOVES" sentence prepended to the `gates`
stamp (marker state, tier consequence, frontier not re-asserted), and a matching block
comment appended in the shard's re-stamp-history convention. **No cell verdict moved.**

**Side repair, disclosed:** the file did not parse at HEAD — `node --check` failed at the
`da_virtual_bids` line because the preceding `egrid_steam_collapse_heat_rates` entry (the
nyiso-189 promotion) ended without its trailing comma, the identical one-character defect
nyiso-172 repaired once before (its own footer comment records it). Without the comma
`window.MECH_MATRIX_SHARDS.NYISO` is never assigned and NYISO's entire column — this stamp
included — is absent from the rendered matrix; `check_mechanism_matrix.py` cannot see it
because it parses shards Python-side. Repaired: one character (`}` → `},`). All seven
matrix files now pass `node --check`. Not a verdict, not a mechanism, not a solve.

---

## 8. Test pins moved with the marker (and what is pre-existing)

`tests/scoring/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers`
pins the committed marker membership and its own comments call a lagging assertion a
"desync class" corrected after the fact three times before. Moved in the same commit as the
marker this time: NYISO `withdrawn` → `complete`, CAISO the sole `withdrawn`, with a dated
comment. The integration-marked `test_build_registration_scorecard_no_iso_gate_open`
carries the same pin (`sc["NYISO"]["gate_a_backcast"]["marker"]`) — moved likewise, with the
invariant it protects unchanged (gate B still HOLD on the FF-2D key, so no gate opens).

**Pre-existing, not this lane's, measured at HEAD by stash-and-run:**
`test_walk_inputs_trivial_single_year` and
`test_build_registration_scorecard_no_iso_gate_open` (both `@pytest.mark.integration`; they
walk the real data tree, which the `code` data profile does not hydrate) fail identically
at `c9f1d26e` before any edit, on the same assertion lines. Recorded; not repaired here.

---

## 9. Flagged, not edited

1. **The frontier leg** — card C-10 / Q39 (§6). Owner's court.
2. **The capx ledger's D56-R lane row** (§0ag / §4 "ISSUED r#36") and the audit board's Z-4 row
   ("D56 not launched; marker unchanged") — the directors' own documents; their LANDED /
   resolved stamps belong to their next refreshes.
3. `closed_on` 'd'-omission convention — standing, left as flagged by D7 / Q5-W.
4. `docs/codebase-site/model-validity.html`'s dated membership sentence — self-dating prose;
   neither the CAISO nor the Q5-W precedent edited it.
5. `keepers/NYISO.json` — read only; no stamp required by the auditor; `frontier` deliberately
   untouched (limb A, no-ruling branch).

---

## 10. What this lane did NOT do

- **Solved NOTHING.** No LP was built; no year of any tier was solved, scored or registered.
- **Spent NOTHING.** The validation-tier authorization RETURNS; it is not USED. No NYISO
  year outside 2023–2025 exists in any sidecar, bench or bundle. The locked tier is untouched,
  never granted, and frozen for every ISO.
- Edited no keeper shard, registry, bundle, bench, `ff-verdicts.json`, `holdout-freeze.json`
  or `final` byte; moved no matrix cell verdict; armed or disarmed no mechanism.
- Re-litigated nothing between R-AG and Q38; decided nothing on C-10.

**Rule 27:** `calibration-complete.json` (283 lines) and `program-status.json` (1,175 lines)
were edited locally through their own serializers and pushed as the exact on-disk bytes over
`git push`; the pushed blobs were fetched back and compared to local — §11 below carries the
verification.
