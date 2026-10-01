# NEISO record correction — the locked test was NEVER GRANTED, not "SPENT"

**Session:** NEISO-RECORD, 2026-08-06 · **Branch:** `claude/neiso-locked-test-correction-b0vcej`
**Lane:** GOVERNANCE. **Committed artifacts only — NO solve, NO scoring, NO year touched, NO
grant of anything.**
**Authorization:** owner decision **D-23, SIGNED at the 2026-08-06 sitting Addendum X.6** (the
session-logged authorization for this correction).
**Finding:** `results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1, independently
corroborated by `docs/third-party-peer-review-2026-07.md` §6.3 item 1.

---

## 0. What changed, in one line

The governance record said NEISO's 2019 + H1-2026 locked test was **"SPENT, NOT RE-GRANTABLE"**.
It never was. The record now reads **NEVER GRANTED**.

**This grants nothing.** NEISO remains absent from `final`;
`holdout_policy.authorized(NEISO, locked_test)` still returns **False**; the holdout spend freeze
is still **ACTIVE**. NEISO's `final` readiness answer is untouched and still **NOT YET**
(neiso-87 §3).

---

## 1. Re-verification at this session's HEAD (step 1 — done before any file was edited)

neiso-87 §1's artifact search was reproduced independently, and **extended beyond it**: where
neiso-87 searched the *current* registry, this session searched the **full git history**,
recovering retention-pruned sidecars from their pre-deletion blobs.

| evidence | neiso-87 | this session, at HEAD | agree? |
|---|---|---|---|
| NEISO registry entries declaring a 2019 solve year | none | **none** — all **27** NEISO sidecars *ever committed* (incl. pruned) declare years ⊆ {2022, 2023, 2024, 2025} | ✅ (stronger) |
| the one textual "2019" hit in the registry | the 2022 touchpoint's `holdout` block | the 2022 touchpoint's **`tierCaveat`**, which says the locked test *"is NOT spent here"* — a reference, not an artifact | ✅ |
| bundle / bench / metrics for a NEISO out-of-training year | `bench/NEISO/` 2022–2025 only | **`bench/NEISO/` = 2022, 2023, 2024, 2025** — no 2019 anything | ✅ |
| `actual_tail.json` NEISO | 2022–2025 | **2022–2025** — no 2019 row exists to score against | ✅ |
| the memo cited as the authorization | 0 mentions of 2019 | **`grep 2019` → 0 hits**; its one-shot was on **2022**, execution **HELD** the same day (G-19) | ✅ |
| what `locked_test_scored_on` named | a config id, not a 2019 run | `2026-07-07-neiso53-winter-fuelsec-coldsnap` — the memo records it **solved full-span 2023–2025**; a **TRAIN-tier** id | ✅ |
| has a correction already landed? | no | **no** — `git log --all` over `calibration-complete.json` shows no commit touching the claim | ✅ |
| `docs/out-of-sample-results-2026-07.md` | D-6 NOT RUN | **"D-6 (holdout scoring): NOT RUN"** | ✅ |

**Verdict: no 2019 artifact exists that neiso-87 missed.** Nothing contradicted the finding, so
the correction proceeded. Had any 2019 artifact surfaced, this session's instruction was to STOP
and report.

---

## 2. Files corrected — before / after

**20 live files.** neiso-87 estimated **13**; §2.3 reconciles the difference.

### 2.1 Load-bearing governance record

| # | file | field / locus | before → after |
|---|---|---|---|
| 1 | `frontend/data/backcast/calibration-complete.json` | `complete.NEISO.locked_test` | *"SPENT, NOT RE-GRANTABLE. The 2019 + H1-2026 one-shot was scored ONCE with the frozen neiso-53 config on 2026-07-07 and STANDS"* → **"NEVER GRANTED. NOT SPENT. NOT AUTHORIZED."** + what the correction does/doesn't do + the NOT-YET readiness answer |
| 2 | ″ | `complete.NEISO.locked_test_note` | the *"scored ONCE … and STANDS"* claim → the **full artifact search**, with the old text quoted verbatim as genealogy |
| 3 | ″ | `complete.NEISO.locked_test_scored_on` | **key renamed** → `locked_test_scored_on_WITHDRAWN`, value explains the retraction (old value preserved in the text). Renamed, not deleted, so the retracted assertion stays legible and no gate can read a live `locked_test_scored_on` for NEISO. **No code reads this field** — `audit_keepers.py` states it "is not read here" |
| 4 | ″ | `complete.NEISO.phantom_reaudit_2026_07_19` | *"The frozen neiso-53 locked-test one-shot is NOT re-opened"* → "No locked-tier year was touched by this re-audit" + bracketed correction |
| 5 | ″ | `complete.NEISO.determination` | the `NOTE:` clause calling `locked_test_scored_on` *"the SPENT one-shot's frozen config"* → correction; the re-key exemption is **moot**, not exercised |
| 6 | ″ | `complete.NEISO.keeper_rekey_policy` | + bracketed note that the generic SPENT-one-shot policy sentence does not apply to NEISO |
| 7 | ″ | `final._note` | *"NEISO is absent because its one-shot is already SPENT (2026-07-07, frozen neiso-53 config), not because it is pending."* → **"absent because its locked test has NEVER BEEN GRANTED"** + the NOT-YET merits |
| 8 | `CLAUDE.md` | **rule 22** `[R-HOLDOUT]` | *"(NEISO is the latter)"* → **"NO ISO IS CURRENTLY IN THE SPENT state"** + a full parenthetical correction with the citation chain and a pointer to `docs/governance/rule-history.md` §4 |
| 9 | `frontend/data/backcast/holdout-freeze.json` | `lift_scope` | *"the 2019 one-shot is SPENT and stands as scored"* → **"NEISO's locked test has NEVER BEEN GRANTED"** + note that 2019/H1-2026 stay outside every lift scope |
| 10 | `frontend/data/backcast/keepers/NEISO.json` | `.holdout_touchpoint.caveat` | *"(NEISO's 2019 + H1-2026 one-shot was spent 2026-07-07 on the frozen neiso-53 config)"* → "NOT touched here" + correction |
| 11 | `frontend/data/backcast/status/NEISO.js` | **generated** | regenerated by `scripts/build_status.py --iso NEISO` (S1 was stale after #10) |
| 12 | `frontend/data/backcast/registry/2026-08-05-neiso-2022-touchpoint.json` | `.definition` | *"NEISO's locked test (2019 + H1-2026) is SPENT and is NOT re-opened here."* → "is NOT touched here" + correction. *(`.holdout.tierCaveat` already said "is NOT spent here" — correct, left alone.)* |

### 2.2 Reference docs, matrix, logs, handoffs

| # | file | locus | note |
|---|---|---|---|
| 13 | `docs/codebase-site/data/mechanism-matrix.js` | header comment | **the LIVE rendered matrix data** (rule 28) — the SPENT claim corrected in place |
| 14 | `docs/mechanism-testing-matrix.md` | §5.6 NEISO | *"`final` NOT PROPOSABLE — locked test is SPENT and never re-grantable"* → **"NOT PROPOSED — NEVER BEEN GRANTED"**; posture unchanged, reason corrected |
| 15 | `docs/calibration-best-so-far-neiso.md` | §"Locked-test scored on" + §5 | both bullets rewritten; old text quoted; §5 now records the full artifact search |
| 16 | `docs/FINDING-nyiso104-c3c-frontier-and-tiered-holdout-2026-07-31.md` | tier table + para | NEISO row moved into the same category as NYISO ("never scored, not granted") + a blockquoted correction |
| 17 | `docs/forecast-readiness-prompt-pack-2026-07.md` | 4 loci (L75, L382, L3226, L3943) | three SPENT assertions corrected; the fourth (neiso-87's own "the claim is FALSE → card D-23") updated to record **EXECUTED** |
| 18 | `docs/iso-2022-holdout-data-availability-audit-2026-07.md` | §intro + §3.6 header | corrected |
| 19 | `docs/handoffs/ffr-owner-sitting-2026-08-02.md` | L29 + L1214 | both corrected by bracketed note; the signed decisions themselves untouched |
| 20 | `docs/handoffs/ffr-3b-staleness-bookkeeping-2026-08-02.md` | L75 | the `locked_test_scored_on` "SPENT one-shot" description corrected; that lane's action was right but the exemption was **moot** |
| 21 | `docs/handoffs/xiso-4-queue-ratchet-2026-08-04.md` | L38 | corrected to past tense + correction |
| 22 | `docs/handoffs/oil-plantgroup-outage-routing-charter-2026-08.md` | L190 | corrected |
| 23 | `docs/handoffs/ffr-3q-window-recut-2026-08-04.md` | L464 | corrected |

**Calibration logs — correct-by-addendum, historical entries NOT rewritten:**

| # | file | treatment |
|---|---|---|
| 24 | `docs/calibration-log/neiso.md` | **one dated correction entry appended** (newest-at-bottom) that enumerates and supersedes all **10** affected entries in a table (L702 neiso-70, L803 neiso-71, L860 neiso-72, L921 neiso-73, L991 neiso-74, L1255 neiso-76, L1442 neiso-78, L1574 neiso-79, L1673 neiso-80, L1700 neiso-84). The 10 entries are left **exactly as written**. Note `neiso-84`'s headline *"the 2022 VALIDATION TOUCHPOINT is SPENT"* is **correct and untouched** — 2022 is validation tier and genuinely was spent; only its *locked*-tier clause is superseded |
| 25 | `docs/calibration-log/nyiso.md` | correction entry appended — the NEISO half of its tiered-holdout contrast was false; **NYISO's own posture unchanged** |
| 26 | `docs/calibration-log/pjm.md` | correction entry appended — **the most consequential**: pjm-159's *"The precedent that should settle it"* argument for HOLD rested on the false premise. See §4 |

*(#19–#26 are 8 files; #13–#18 are 6; #1–#12 are 7 distinct files. **20 files total.**)*

### 2.3 Reconciliation with neiso-87's count of 13

neiso-87 named: the marker's `locked_test` + `locked_test_note` + `final._note`, CLAUDE.md rule 22,
`holdout-freeze.json`, the 2022 touchpoint sidecar, `docs/mechanism-testing-matrix.md`, 10 entries
in `docs/calibration-log/neiso.md`, "plus four handoff/audit docs".

**This session found 7 loci neiso-87 did not enumerate:**

1. `frontend/data/backcast/keepers/NEISO.json` — `.holdout_touchpoint.caveat`
2. `frontend/data/backcast/status/NEISO.js` — generated from it, and **stale-failing `audit_keepers` S1** until rebuilt
3. `docs/codebase-site/data/mechanism-matrix.js` — the **live rendered** matrix, distinct from the `.md`
4. `docs/calibration-log/nyiso.md` and 5. `docs/calibration-log/pjm.md` — cross-ISO second-hand
6. `docs/handoffs/ffr-3b-staleness-bookkeeping-2026-08-02.md` and 7. `docs/handoffs/ffr-owner-sitting-2026-08-02.md` L29 (a **second** locus in that file beyond L1214)

Plus **3 additional loci inside `calibration-complete.json` itself** (`phantom_reaudit_2026_07_19`,
`determination`, `keeper_rekey_policy`) that repeated the claim in the very file being corrected.

The difference is counting scope, not disagreement: neiso-87's §1 was a *finding*, not an
exhaustive edit manifest, and it explicitly invited this reconciliation.

### 2.4 Deliberately NOT rewritten — `results/calibration/` (≈22 files)

Twenty-two per-run session records (`FINDING-*`, `PREREG-*`, `CHARTER-*`, `ASSESSMENT-*`,
`neiso2022_touchpoint/run_config.json`) repeat the claim. These are **immutable historical
artifacts** — a faithful record of what each session believed when the governance record told it
so. Rewriting them would be rewriting history, which this session's brief forbids. They are
superseded by the live record and by the log addenda. The two whose *conclusions* a future
session might act on are handled through their **live** channel instead:
`ASSESSMENT-pjm159-final-declaration-2026-08-06.md` → the `docs/calibration-log/pjm.md` addendum,
and `FINDING-neiso84-frontier-recheck-2026-08-05.md` → the `docs/calibration-log/neiso.md` entry.

---

## 3. Verification (step 4) — the correction must not accidentally grant

```
$ python3 scripts/audit_keepers.py --iso NEISO
[✓] NEISO  2026-08-05-neiso-83-ca1-reclass   all checks passed
[✓] -      holdout                           all checks passed
[✓] -      marker                            all checks passed
[✓] -      status                            all checks passed
PASS: 0 failure(s), 0 warning(s)
```

*(First run FAILed S1 — `status/NEISO.js` stale after the keeper-shard edit — resolved by
`scripts/build_status.py --iso NEISO`, which reported `[NEISO:CALIBRATED-WITH-CAVEATS]`, i.e. the
determination is **unchanged**. `status/shared.js` was NOT modified: the rubric did not change,
so it is deliberately not committed.)*

**Gate check — `scripts/lib/holdout_policy.authorized`, after the correction:**

| ISO | validation | **locked_test** |
|---|---|---|
| **NEISO** | True | **False** ✅ |
| PJM | True | False |
| NYISO | True | False |
| CAISO | False | False |

`tier_for_year`: 2019 → `locked_test`, 2026 → `locked_test`, 2022 → `validation` (unchanged).
`holdout-freeze.json` `active` → **true** (unchanged).

**All four JSON files re-parse cleanly** (`calibration-complete.json`, `holdout-freeze.json`,
`keepers/NEISO.json`, the touchpoint sidecar).

**The correction grants nothing.** The only thing that changed is *which question is open*.

---

## 4. The one place this materially misinformed an open decision

`docs/calibration-log/pjm.md` §*"The precedent that should settle it"* (pjm-159, **dated
2026-08-06 — today**) argued PJM's `final` decision from the NEISO precedent:

> "NEISO's locked test was spent 2026-07-07 … Its honest out-of-sample number describes a model
> that no longer exists and is never re-grantable."

**There is no such number and no such precedent.** The pjm-159 *conclusion* (HOLD) is untouched
and was not revisited — B1–B4 stand on their own evidence. What is withdrawn is a supporting
analogy. Note the direction of the error: the analogy was deployed as a **caution**, and the true
state — *nobody has ever spent a locked test* — is if anything a **stronger** caution, because the
program has no worked example of a locked-test spend at all. A future PJM session must cite NEISO
for **neither** half: it is not an example of a spent one-shot, nor of a foreclosed one.

---

## 5. What is explicitly NOT changed

- **NEISO's `final` readiness: still NOT YET** (neiso-87 §3). 2019 is **unsolvable at HEAD**
  (`eia_demand_profiles.parquet` carries NEISO 2021–2025 only), three further scoring inputs are
  absent, and 2019 **cannot discriminate** on C3c (zero actual RT hours > $300 in 2019 ⇒ a free
  small-count PASS whatever the model does).
- **No grant, no marker, no lift.** `final` still EMPTY; freeze still ACTIVE; no year solved,
  scored or registered.
- **The touch-once discipline itself.** Unchanged, and still governs whenever a grant is made.
- **Every keeper, determination and verdict.** Untouched — `[NEISO:CALIBRATED-WITH-CAVEATS]`.
- **neiso-87 §§2–4** (frontier re-verification, preparedness audit, the stale-row A/B) — out of
  scope here.
- **The open items neiso-87 raised** stand: the 2019/2020 preparation work (cross-ISO F3 demand
  gap), the `CONSIDERED_HOLDOUT_YEARS` widening, the outage-detector vintage split, and the
  keeper's **January-2025 non-reproduction at HEAD**.

---

## 6. Rule compliance

| rule | status |
|---|---|
| 22 `[R-HOLDOUT]` | **No year solved, scored or registered.** Freeze untouched and not engaged. Gate re-verified: NEISO `locked_test` = **False**. Record-keeping only — which rule 22 as rewritten places outside the marker regime. |
| 27 `[R-PUSH]` | Opus session. Every file edited **locally** with the Edit tool and pushed as exact on-disk bytes; **no `push_files`**. Blob verification run after push on every file ≥300 lines (§7). |
| 15 `[R-DASHBOARD]` | No run produced ⇒ nothing to register. `status/NEISO.js` regenerated and committed so the dashboard stays truthful. |
| 28 `[R-MECH-MATRIX]` | **No mechanism tested ⇒ no cell verdict minted** (duty d); no new `ScenarioConfig` field ⇒ duty (c) not engaged. The matrix's governance header corrected in both the `.md` and the live `.js`. |
| 25 `[R-ISO-SCOPE]` | No ISO's calibration state changed. The NYISO/PJM log addenda correct a **second-hand NEISO claim** and change neither lane's posture. |
| 5 `[R-NO-MAGIC]` / 24 `[R-REGISTRY]` | No solve-affecting value touched. |

**Model assignment (rule 27):** CLAUDE.md is core infrastructure ⇒ Opus/Fable only. This session
is Opus.

---

## 7. Push integrity (rule 27) — files ≥300 lines in this change

`CLAUDE.md` (478), `docs/mechanism-testing-matrix.md` (7,421), `docs/calibration-log/neiso.md`
(1,759 → +~90), `docs/calibration-log/nyiso.md` (5,519), `docs/calibration-log/pjm.md` (3,875),
`docs/forecast-readiness-prompt-pack-2026-07.md` (4,083),
`docs/codebase-site/data/mechanism-matrix.js`, `docs/handoffs/ffr-owner-sitting-2026-08-02.md`.

All edited **in place** with the Edit tool (never regenerated from response content) and pushed
via `git push` as exact on-disk bytes, on a branch freshly rebased on `origin/main` so the pack
stays small. Post-push blob verification (line count + SHA-256, local vs fetched) is recorded in
§8.

## 8. Post-push blob verification

Every file ≥300 lines in this change, fetched back from the pushed branch and compared to the
local on-disk bytes (line count + SHA-256):

| file | lines (local = remote) | sha256[:10] (local = remote) | verdict |
|---|---|---|---|
| `CLAUDE.md` | 493 | `ec867c1c73` | MATCH |
| `docs/mechanism-testing-matrix.md` | 7,439 | `d494ec9778` | MATCH |
| `docs/calibration-log/neiso.md` | 1,844 | `ac920c5e0b` | MATCH |
| `docs/calibration-log/nyiso.md` | 5,546 | `085d55520f` | MATCH |
| `docs/calibration-log/pjm.md` | 3,938 | `7ad32a12be` | MATCH |
| `docs/forecast-readiness-prompt-pack-2026-07.md` | 4,096 | `0befeedcaf` | MATCH |
| `docs/codebase-site/data/mechanism-matrix.js` | 2,328 | `caae5239d5` | MATCH |
| `docs/handoffs/ffr-owner-sitting-2026-08-02.md` | 2,926 | `d06a672ac6` | MATCH |
| `docs/handoffs/ffr-3q-window-recut-2026-08-04.md` | 505 | `b9c5573eb0` | MATCH |
| `docs/iso-2022-holdout-data-availability-audit-2026-07.md` | 526 | `24090598c9` | MATCH |

**No truncation, no drift.** Every change is additive (CLAUDE.md 478 → 493 lines), so
`file-integrity-guard.yml`'s >30 % shrink check is not engaged.

**Final gate state at the pushed commit:**

```
scripts/audit_keepers.py --iso NEISO --check   →  PASS: 0 failure(s), 0 warning(s)  (exit 0)

NEISO locked_test authorized : False      <-- required
NEISO validation authorized  : True       (unchanged)
NEISO in `final` block       : False      (unchanged)
holdout freeze active        : True       (unchanged)
RESULT: PASS — nothing granted
```

The branch was rebased onto a freshly-fetched `origin/main` (`dd4e919c`) before pushing, so the
pack carried only this session's objects. The rebase was clean; the two files that also moved
upstream (`docs/calibration-log/pjm.md`, `docs/mechanism-testing-matrix.md`) merged without
conflict, and the newly-landed `ASSESSMENT-pjm160-final-declaration-2026-08-06.md` was checked
and does **not** repeat the claim.
