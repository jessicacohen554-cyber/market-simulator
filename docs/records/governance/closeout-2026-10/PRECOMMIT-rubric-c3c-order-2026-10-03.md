# PRECOMMIT — rule-22 lone-C3c test after the owner-signed routes (rubric v3.19 → v3.20)

- **Lane:** `closeout-rubric-c3c-order`, chartered by the backcast close-out desk under owner ruling **R-57** (2026-10-03, decision card: *"Open the amendment lane"*).
- **Rule 37 `[R-RUBRIC-FREEZE]`:** this record proposes a rubric amendment and measures its effect zero-LP. **No rubric code lands here.** The owner rules first; a follow-up lane lands the code in a PR that touches no keeper surface.
- **Base:** `origin/main` `4fcad76bb2e259bef8667b11c6c4b1a43a8c9af4`, rubric `RUBRIC_VERSION = "3.19"`.
- **Zero LP.** Every number below comes from `scripts/probes/rubric_c3c_order_probe.py` over the committed keeper bundles under `results/calibration/`.

## 0. Result

- **No registered determination moves.** Under the amended order, all 9 ISO headlines, all 13 keeper scopes, every criterion-year record and every caveat-budget count are byte-identical to v3.19. The 61-row per-year ladder (rule 30) also shows 0 changes.
- **The amendment only acts on the R-51 shape.** Take the ERCOT carve-out-2023 scope and replace only its 2023 C3c model count with the ×33-strip probe's measured 44 h (vs 181 h actual). That scope reads **NOT-YET under v3.19 and CALIBRATED under v3.20**. C3c becomes a rule-22 ledgered caveat (`c3c-any-year-2026-08-09`), and C3a/C3b stay R-6 configuration exceptions.
- **Recommendation: adopt.** This is a coherence fix with no effect today. It stops the outcome depending on the order in which routes are applied, whenever a lone C3c miss sits beside rows the owner has already excused.

## 1. The defect

`determine_from_artifacts` (`scripts/calibration_verdict.py`, v3.19) runs the routes in this order:

```
_apply_ledger (explicit exceptions)      # per record
score_governance
_apply_c3c_standing_rule(records, gov)   # rule 22 — lone-failure test HERE   (:4428)
_apply_scoped_ledger(...)                # v3.10 / R-8                        (:4432)
_apply_config_exceptions(...)            # v3.14 / R-6                        (:4437)
_apply_reference_coverage(...)           # v3.19 / R-40                       (:4442)
```

- The standing rule's lone-failure test is `remaining = [FAIL records in CRITERIA]`, then "every remaining row is `price_tail`".
- That test runs while the rows the three later routes will reclassify still read `FAIL`. So a C3c miss next to an R-6-excused C3a/C3b (or an R-8 scoped-ledger row, or an R-40 reference-coverage row) counts as "not lone" and stays a `FAIL`. The scope then reads NOT-YET on C3c, even though the owner has already ruled every other row in that scope acceptable.
- The call-site comments show the order was chosen on purpose ("so its lone-failure guard saw these rows as FAILs"). That choice was never put to the owner as a rubric question. R-51 surfaced it, and R-57 opens it.
- **Scope of "lone".** The test is measured over the scored span of the verdict it runs in: one keeper scope, one folded run, or one year of the per-year ladder. It is not measured per calendar year. This amendment keeps that unchanged.

## 2. The amendment (exact)

### 2.1 Code: a pure reorder in `determine_from_artifacts`

Move the one call `_apply_c3c_standing_rule(records, gov)` from directly after `score_governance` to directly after `_apply_reference_coverage(records, iso, gov, bench, exceptions)`:

```
_apply_ledger ; score_governance
_apply_scoped_ledger(records, iso, gov)
_apply_config_exceptions(records, iso, gov, art.get("config"))
_apply_reference_coverage(records, iso, gov, bench, exceptions)
_apply_c3c_standing_rule(records, gov)   # LAST: the lone test sees owner-signed caveats as non-failures
```

The body of `_apply_c3c_standing_rule` is **not changed**. So all of rule 22's guards carry over byte-for-byte:

| Guard | Where it lives | After the amendment |
|---|---|---|
| Lone failure only | `remaining` = every still-`FAIL` record in `CRITERIA`; silent if any is not `price_tail` | unchanged; it now runs after the routes the owner signed, so their `CAVEAT`s are not failures |
| 2023–2025 only; the condition is dropped out of training | `holdout_policy.tier_for_year`, `TIER_TRAIN` = 2023/2024/2025; the v3.6 holdout limb | unchanged |
| Governance C6 must pass | first line: `gov.status != PASS` → return | unchanged |
| Supporting tier only | the rule touches only `price_tail` (SUPPORTING); classifies `MODEL_LIMIT` | unchanged |
| Never a PASS | sets `CAVEAT`, magnitude kept, spends the single ledgered slot | unchanged |

**Why a reorder is enough, and safe.** None of the three routes moved ahead of the rule can take a `price_tail` row:

- the keys of `SCOPED_LEDGER_ENTRIES`, `CONFIG_EXCEPTION_ENTRIES` and `REFERENCE_COVERAGE_ENTRIES` at v3.19 name only `fuelmix`, `price_mean` and `price_shape`;
- the standing rule touches only `price_tail`.

So the four routes write to disjoint rows, and the only thing the reorder changes is what the lone test sees. Every route checks the governance gate the same way, so governance gating is also unchanged.

- **Fail-closed note for the code lane.** If a future amendment ever adds a `price_tail` key to one of those three tables, that route will now reach the row before rule 22 does. The code lane should add an assertion, at import or in a test, that none of the three tables carries a `price_tail` key, so that case cannot happen silently.

**Monotone: no reading can get worse.** The reorder can only turn a C3c `FAIL` into a C3c `CAVEAT`, and only in a verdict where every other failure was already owner-excused. The resulting ledgered caveat still spends the slot (`MAX_LEDGERED_CAVEATS = 1`):

- If a scope already spends the slot on an R-8 scoped-ledger row that is still on the slot, the new caveat pushes it over budget. It stays NOT-YET, as it was.
- R-6 and R-40 caveats are off every budget, so there the lone C3c becomes the scope's one ledgered caveat. Under rule 22 / v3.3 that caveat does not downgrade.

In practice the amendment is live only next to configuration-exception and reference-coverage caveats.

**Equivalent guard change (not recommended).** Leave the order alone and have `remaining` ignore rows a later route would reclassify. That means calling the three routes' predicates twice, which is two code paths for one decision (rule 19 in spirit). The reorder is one line plus comments.

### 2.2 What else changes in the code lane

- **`RUBRIC_VERSION = "3.20"`**, plus a `# v3.20 — 2026-10-0x owner ruling R-57 / R-xx (...)` header entry in `calibration_verdict.py`. It records the reorder, the guards it leaves unchanged, and the §3 measurement of this record (0 of 13 scopes, 0 of 61 ladder rows, 0 of 9 ISOs move).
- **Call-site comments** at the four `_apply_*` calls, rewritten to state the new order and its reason. Also the `_apply_scoped_ledger` / `_apply_config_exceptions` / `_apply_reference_coverage` docstrings and the v3.10/v3.14/v3.19 header lines that say the standing rule "saw these rows as FAILs".
- **`C3C_STANDING_RULE_REASON`:** the sentence "C3c (price tail / scarcity) is the ONLY failing criterion" becomes "C3c is the ONLY failing criterion once the owner-signed scoped-ledger, configuration-exception and reference-coverage caveats are applied (rubric v3.20, R-57)". The lone-failure paragraph keeps its claim that the rule "can never mask a second defect". Every excused row is one the owner signed by its exact `(iso, year, criterion, key)` key, and none of them is unexplained.
- **Tests** (`tests/scoring/test_calibration_verdict_closeout_c.py`), on synthetic artifacts:
  - (a) ERCOT 2023, carve-out config armed, C3a/C3b `FAIL` matching R-6, and C3c `FAIL` → C3c `CAVEAT` (`c3c-any-year-2026-08-09`); the determination is CALIBRATED;
  - (b) the same, plus an unexcused C1 `FAIL` → C3c stays `FAIL`, NOT-YET;
  - (c) CAISO 2021-style partial-reference C3a `FAIL` with its signed twin, plus a lone C3c in a training year → C3c caveat;
  - (d) governance `FAIL` → nothing reclassified;
  - (e) the disjoint-keys assertion from §2.1.
- **`docs/governance/rule-history.md`:** a new section *"Rubric v3.20 — the rule-22 lone test sees owner-signed caveats (owner, R-57/R-xx)"*.

### 2.3 Rubric text (`docs/calibration-determination-rubric.md`)

- **Banner** (line 3): `Scorer RUBRIC_VERSION is **3.20** (2026-10-0x)`.
- **§3 "The exceptions ledger"**: add a paragraph after the standing-rule mechanics:

  > **Order of the automatic routes (v3.20, owner ruling R-57/R-xx).** The rule-22 lone-C3c standing rule is applied **last**, after the explicit exceptions ledger, the governance gate, the scoped ledger (v3.10/R-8), the configuration exceptions (v3.14/R-6) and the reference-coverage caveats (v3.19/R-40). "Lone" is therefore measured over the criterion-years still failing once every owner-signed caveat has been applied: a row the owner has excused by its exact (ISO, year, criterion, key) is not a second failure. Every other guard of rule 22 is unchanged — lone failure only (on 2023–2025; dropped for out-of-training years, v3.6), governance (C6) must pass, supporting tier only, the caveat spends the single ledgered slot and never reads PASS.
- **§9 Version history**: a v3.20 entry with this record's measurement (§3) and citation.

### 2.4 Freeze gate (`scripts/check_rubric_freeze.py`)

- The code lane changes only the rubric surface (set A). It changes no keeper JSON, status part, `calibration-complete.json` or bundle (set B), so the gate passes **without** `RUBRIC_FREEZE_OVERRIDE`. The commit cites the owner's ruling (rule 37).
- The override is needed only if that PR also rebuilt `frontend/data/backcast/status/*.js`, for example to restamp the displayed rubric version. That restamp belongs in the next status rebuild, not in the amendment PR. If the desk wants both in one PR, then the override carries the ruling citation.

## 3. Effect, zero-LP (BEFORE = v3.19 as committed; AFTER = the §2.1 reorder applied in memory)

- **Method.** `scripts/probes/rubric_c3c_order_probe.py` patches the module in memory only. It no-ops `_apply_c3c_standing_rule` at its current call site and re-invokes the unchanged function right after `_apply_reference_coverage`. `calibration_verdict.py` is never edited.
- **What it scores.** Each ISO's keeper through `iso_determination` (partition scopes plus every run folded through `holdout.keeper`). It diffs every record's `(status, classification, standing_rule)` and every scope's determination and `grade_summary`. It then re-scores every scope one year at a time.

### 3.1 ISO determinations and scopes

| ISO | Keeper | Scope | Years | BEFORE | AFTER | Failing (both) | Ledgered slot used (both) |
|---|---|---|---|---|---|---|---|
| **ERCOT** | `2026-10-02-closeout-l1-coal-fuel` | forward | 2024–25 | NOT-YET | NOT-YET | C3a 2024 | 1 (C3c 2024/25, explicit) |
| | | carveout-2023 | 2023 | CALIBRATED | CALIBRATED | — (C3a/C3b R-6 config-exc.; C3c 138 h PASS) | 0 |
| | | carveout-validation | 2019–22 | NOT-YET | NOT-YET | C1 2019/20, C3b 2019/20 | 1 (C3c 2020/22 holdout limb, 2021 explicit) |
| | | **ISO** | | **NOT-YET** | **NOT-YET** | | |
| **CAISO** | `2026-10-02-closeout-caiso-w1-arm2` | keeper | 2019–25 | NOT-YET | NOT-YET | C1 2019–21, C4 2019–21 (C3a/C3b 2019–21 R-40 ref-coverage) | 1 (C3c 2021 holdout, 2024 explicit) |
| **PJM** | `2026-10-03-closeout-pjm-nuc-keeper` | keeper | 2019–25 | NOT-YET | NOT-YET | C1 2019–22, C3a 2022/25, C3b 2022/25 | 1 (C3c 2019/21/22 holdout) |
| **MISO** | `2026-10-03-closeout-miso-nuc-r` | train | 2023–25 | CALIBRATED | CALIBRATED | — | 1 (C3c 2023–25 explicit) |
| | | validation | 2019–22 | NOT-YET | NOT-YET | C1 2019/21, C3a 2020, C3b 2021 | 1 (C3c holdout) |
| | | **ISO** | | **NOT-YET** | **NOT-YET** | | |
| **NYISO** | `2026-10-02-w0-nyiso` | keeper | 2021–25 | CALIBRATED | CALIBRATED | — | 1 (C3c 2023–25 standing rule, 2022 holdout) |
| **NEISO** | `2026-10-02-w0-neiso` | keeper | 2019–25 | CALIBRATED | CALIBRATED | — | 1 (C3c 2022 holdout, 2023/25 explicit) |
| **SPP** | `2026-10-03-closeout-spp-nuc-keeper` | train | 2023–25 | NOT-YET | NOT-YET | C3a 2024, C3b 2024, **C3c 2023/24/25** | 0 |
| | | validation | 2019–22 | NOT-YET | NOT-YET | C4 2022, C1 2021/22, C3a 2019/20, C3b 2020 | 1 (C3c holdout) |
| | | **ISO** | | **NOT-YET** | **NOT-YET** | | |
| **NWPP** | `2026-10-03-nwpp-next-24-head` | keeper | 2019–25 | NOT-YET | NOT-YET | C4 2019/23/24, C1 2019/24, C3a 2023/24, C3b 2023/24 (C3c not scored) | 0 |
| **SOCO** | `2026-10-03-closeout-soco-3-coalpile` | keeper | 2019–25 | NOT-YET | NOT-YET | C1 2019 (C3a/C3b R-8 scoped, off-slot; C3c not scored) | 2 recorded, 0 budgeted (R-8 ref-definition) |

- **Criterion-year grades that change: none (0).**
- **Caveat-budget use that changes: none.** Every scope's `grade_summary` (scored / target / commercial / ledgered / fails) is identical.
- **Per-year ladder:** 61 scope-years, 0 change.
- No folded runs are registered at this base. Every registered run is a keeper scope (E13), so the folded set is empty.

**Why nothing moves today.** A C3c `FAIL` that survives v3.19 appears in only one scope, SPP train 2023–25. That scope also has C3a/C3b 2024 failing **unexcused**, so the lone test stays silent under either order. SPP reads NOT-YET on C3a/C3b 2024 before and after (plan §3.4: the C3c row "reverts to a caveat once validation rows close"; the amendment does not change that). Every other scope's C3c is already a caveat or a PASS.

### 3.2 Sensitivity: the R-51 case (the shape the amendment is for)

- **Input.** The ERCOT keeper's carve-out-2023 scope (`2026-10-02-closeout-l1-coal-fuel`, years `[2023]`). Only `payload.years["2023"].ordc.hoursGt200.model` is replaced, by the ×33-strip leg's measured **44 h** (`RESULT-closeout-ercot-ecrs-x33-strip-2026-10-03.md` §3; actual RT 181 h). That composite is kept off `main`, so this stands in for it at zero LP.

| Record | BEFORE (v3.19) | AFTER (v3.20) |
|---|---|---|
| C3a 2023 | CAVEAT, configuration exception (R-6) | same |
| C3b 2023 | CAVEAT, configuration exception (R-6) | same |
| C3c 2023 | **FAIL**, model miss | **CAVEAT**, accepted model-class (`c3c-any-year-2026-08-09`) |
| Scope determination | **NOT-YET** | **CALIBRATED** |
| `grade_summary` ledgered / fails | 0 / 1 | 1 / 0 |

- This reproduces the scope flip the R-51 RESULT recorded (§3: carve-out 2023 CALIBRATED → NOT-YET on C3c 2023 under the strip). The amendment is the reason that flip would not occur.
- The ERCOT ISO headline stays NOT-YET either way, on the forward C3a 2024 and the validation C1/C3b.

## 4. What this does not do

- It does not touch any band, tier, `LEDGERABLE_CRITERIA`, `MAX_LEDGERED_CAVEATS`, `MAX_PROTECTIVE_CAVEATS` or ledger-table entry. It adds no new caveat kind and no ISO-specific branch.
- It does not touch the v3.6 holdout limb, the v3.7 unscored-C3c exemption, or the explicit exceptions ledger (`_apply_ledger` still runs first).
- It does not change any keeper, status part, `calibration-complete.json` or bundle. This PR carries this record and the probe only (`scripts/probes/` is outside the rubric-freeze surface).

## 5. Owner card (for the desk)

> **Rule 22 lone-C3c test: apply it after the owner-signed caveats?** Today the rule-22 auto-caveat decides "lone" *before* the R-6 configuration exceptions, the R-8 scoped ledger and the R-40 reference-coverage caveats are applied, so a C3c miss beside rows you already excused still counts as a second failure (the R-51 ERCOT 2023 strip case: NOT-YET only for that reason). Proposed v3.20: run the rule last; all its guards unchanged (lone only, 2023–25, C6 must pass, supporting tier, spends the slot, never PASS). Measured: **0 of 9 ISO determinations, 0 of 13 scopes, 0 of 61 per-year rows move today**; it only acts on the R-51 shape. Options: **Adopt v3.20** (recommended) · Keep v3.19 order.

## 6. Provenance

- **Probe:** `uv run python scripts/probes/rubric_c3c_order_probe.py [--json OUT]`. Read-only and zero-LP; patches in memory only.
- **Base** `4fcad76bb2e259bef8667b11c6c4b1a43a8c9af4`. Bundles read:
  - `results/calibration/{closeout_ercot_l1_span, closeout_caiso_w1_a2_span, closeout_pjm_nuc_full_span, closeout_miso_nuc_span, w0_nyiso_span, w0_neiso_span, closeout_spp_nuc_span, nwppnext24_span, closeout_soco_3_span}`
  - their registry sidecars in `frontend/data/backcast/registry/`
- **Rulings cited:**
  - R-6 (2026-10-02) and R-8 (2026-10-02)
  - R-40 (2026-10-03)
  - R-51 (2026-10-03, the open follow-on)
  - R-57 (2026-10-03, this lane)
  - rule 22 `[R-C3C]` and rule 37 `[R-RUBRIC-FREEZE]`
