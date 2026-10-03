# RESULT closeout-CAISO-r40: owner ruling R-40 implemented, rubric v3.19 (2026-10-03, zero LP)

Lane closeout-CAISO-r40b (desk `session_01ALecU5Wjde4tkbLrnMExT9`), branch `claude/closeout-caiso-r40b`.
- **Base:** `origin/main` `5c6c4ee2`.
- **Not done:** no LP, no shard, no promotion. No other ISO's matrix shard was edited.
- **Keeper unchanged:** `2026-10-02-closeout-caiso-w1-arm2`, bundle `results/calibration/closeout_caiso_w1_a2_span`. Its
  attestation gains six owner-signed `exceptions` entries and nothing else; the diff is append-only, +84 lines.

## 1. Ruling (verbatim)

The authoritative text is `docs/backcast-closeout-plan-2026-10.md` §5.0, row R-40 (PR #7111, merged at `0b647b40`).

> "Caiso mean LMP for 2021 should be an accepted caveat or only compared where data is actually available for that
> year for calibration rubric. 2019 and 2020 should have that be accepted caveat for c3a."

Extended by the owner the same day:

> "I want c3b treated the same."

## 2. Design (as approved by the desk)

**New caveat kind.** Rubric v3.19 adds `reference-coverage`, with the classification `OWNER-SIGNED REFERENCE-COVERAGE CAVEAT`.

**Registry.** `scripts/calibration_verdict.py::REFERENCE_COVERAGE_ENTRIES` has exactly six rows:
- Keys: CAISO {2019, 2020, 2021} × {`price_mean`, `price_shape`}, with key `None`.
- Coverage: `absent` for 2019/2020 and `partial` for 2021.
- Each row cites R-40 and the C3b extension.

**`_apply_reference_coverage` is fail-closed.** All of the following must hold:
- (a) Governance is PASS.
- (b) The bundle attestation carries an `exceptions` entry with `kind: "reference-coverage"` for the same criterion
  and year. `_apply_ledger` ignores it, because price_mean and price_shape are not ledgerable; `promote_keeper`
  carries it forward verbatim as "not ledgerable, record only".
- (c) The record's state matches the registry:
  - **absent**: a SKIPPED record with no actual, no bench `avgLMP`, and no `actual_lmp.json` year block. An unreadable
    reference fails closed.
  - **partial**: a scored record whose annual coverage is below 1.
- A record that another route already reclassified is left alone.

**Ordering.** The function runs last, after the C3c standing rule, the scoped ledger and the configuration exceptions.
This follows the v3.14 precedent: none of those routes saw these rows as anything other than scored.

**What each state reads.**
- Absent reads CAVEAT, "reference absent — accepted caveat (R-40)".
- Partial reads CAVEAT and carries the covered-window magnitude, with `window_status` and `window_classification`
  beside it. C3b 2021 reads CAVEAT, never PASS.

**Budgets and reporting.**
- The kind sits outside every budget: it is neither ledgered nor commercial-band, and it never takes the C3c slot.
- It does not downgrade the determination.
- It is named on the determination basis on every route.
- The per-criterion `caveat_kind` reads `reference-coverage`. A configuration exception outranks it if both are present.
- `caveats.reference_coverage` is emitted only when it is non-empty.
- `RUBRIC_VERSION` is now 3.19.

**Tests.** `tests/scoring/test_calibration_verdict_reference_coverage.py` has 11 cases. They were red before the code
change and are green after. They cover:
- the registry;
- absent → CAVEAT;
- partial → covered months only, with junk in the uncovered months masked out, never PASS, and `window_status` set;
- the kind never downgrades, with absent and partial each checked against a full-reference control;
- fail-closed behaviour with no attestation twin, failed governance, a registry/state mismatch either way, or another ISO.

**Docs.**
- Rubric: header, the §2 paragraph and the §9 v3.19 entry.
- `docs/governance/rule-history.md` §29 is new; "Changes to this file" is renumbered to §30.
- `docs/calibration-log/caiso.md` has a new entry.
- The CAISO matrix shard's `gates` stamp is updated. It is evidence only; no cell moves.

## 3. Before → after: the six cells (keeper `2026-10-02-closeout-caiso-w1-arm2`)

Readings were reproduced first on main and match the charter's.

| cell | before (v3.18) | after (v3.19) |
|---|---|---|
| C3a 2019 | SKIPPED: "no measured LMP reference on disk" | **CAVEAT**: reference absent (R-40) |
| C3a 2020 | SKIPPED | **CAVEAT**: reference absent |
| C3a 2021 | FAIL +12.7 % (model $57.30 vs RT lw $50.87; months 5, 6, 7, 9, 10, 11, 12) | **CAVEAT** +12.7 %; window_status FAIL; coverage_annual 0.6522 |
| C3b 2019 | SKIPPED | **CAVEAT**: reference absent |
| C3b 2020 | SKIPPED | **CAVEAT**: reference absent |
| C3b 2021 | PASS, NRMSE 0.148 (same mask) | **CAVEAT**, NRMSE 0.148; window_status PASS |

**Derived CAISO moves.**
- `price_mean` goes from FAIL to CAVEAT, and `price_shape` from PASS to CAVEAT. Both have `caveat_kind` `reference-coverage`.
- `caveats.reference_coverage` is new: [C3a, C3b].
- `ledger_entries` now includes the six entries.
- `grade_summary` changes: fails 3 → 2, target_grade 4 → 3.
- In the reasons, `price_mean` leaves the FAIL line and a basis line names the six caveats.
- In the status part, `determination_scopes[0].failing` loses "price_mean 2021", and the per-year reasons for 2019,
  2020 and 2021 gain the basis line.

**Determination: NOT-YET, unchanged.** The fail set is C1 fuelmix (CC_REGULAR 2019–2021) and C4 dispatch_corr (gas
2019–2021). The per-year ladder for 2019, 2020 and 2021 is still NOT-YET.

## 4. All-ISO diff

I ran `calibration_verdict.py --json` on all 9 keepers twice, once with main's scorer and once with v3.19, and diffed
every (ISO, year, criterion, key) leaf:

| ISO | leaves changed | determination |
|---|---|---|
| CAISO | the six cells and their derived fields (§3), plus `rubric_version` | NOT-YET → NOT-YET |
| ERCOT, MISO, NWPP, PJM, SOCO, SPP | `rubric_version` only | NOT-YET → NOT-YET |
| NEISO, NYISO | `rubric_version` only | CALIBRATED → CALIBRATED |

`build_status.py` rebuilt every ISO:
- For the 8 non-CAISO parts, only `generated` and `keeper.rubric_version` changed.
- In `shared.js`, only `rubric_version` changed.
- No bench part was touched. `render_calibration_html.py` is untouched, so no builder fingerprint is re-stamped and
  there is no bench-inert adjudication to make.

## 5. July de minimis bound

- CAISO 2021's July RT coverage is 0.9987: one uncovered hour inside a month the mask counts as covered.
- The previous lane measured the effect on main `93bce699` at no more than $0.044/MWh on the July mean and no more
  than 0.02 pp on the annual C3a.
- That is below the reported precision of either 2021 cell (C3a +12.7 %, C3b 0.148), so it moves neither.
- As instructed, it is recorded and the render payload is unchanged. `render_calibration_html.py` is a bench
  `PAYLOAD_SOURCE`, and editing it would re-stamp every bench part.

## 6. Gates

| Gate | Result |
|---|---|
| `audit_keepers.py --iso CAISO --check` | PASS, 0 failures, 0 warnings |
| `check_registry_payload_parity.py` | OK, 9 runs, 9 bundle dirs |
| `check_mechanism_matrix.py --base origin/main` | exit 0 |
| fast lane | see the PR body |

## 7. Notes

- **Promotion carry-forward.** The six entries are not C3c, so `promote_keeper.py` carries them verbatim. They are
  never re-measured and never refused. At the next CAISO promotion they keep reclassifying, as long as the incoming
  bundle's records still match the registry state.
- **When the reference changes.** If a CAISO 2019/2020 reference is ever committed, the "absent" rows stop matching
  and fail closed back to an ordinary scored verdict. The same happens to the 2021 rows if 2021 reaches full coverage.
  Either way the registry rows become inert and should be removed (rule 26).
