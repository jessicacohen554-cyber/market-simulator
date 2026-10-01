# FINDING — capx D80: the eight capx-track invariant declarations — the Y-24 ratchet reads EXIT 0, the baseline is empty, and the five T1-H rows are cited to the findings that actually state them (Y-19 / Y-22 / Y-24), not to the ones the charter named

**Lane:** capx D80 (records only, zero LP) · **Charter:** pack §D80 (r#47) + the r#48 id-list
correction · **HEAD at start:** `2485e611` (= `origin/main`, one merge past the charter's
`2617a5d3`) · **Date:** 2026-09-06 · **DATA PROFILE:** code

## 0. Bottom line

- `python scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` read
  **EXIT 1 on eight ids** at HEAD and reads **EXIT 0** after this change, on the same 102
  sidecars / 1,428 records. The eight are exactly the charter's eight — nothing added, nothing
  dropped (§2).
- Eight rows added to `declared_failures` (10 run–ident pairs); the same eight removed from
  `registration_ratchet_baseline`, which is now `{}` — its terminal state, since the baseline may
  only shrink and a declared pair is stale by the ledger's own rule (§4).
- **One report line, not buried:** the charter's premise that "D45 / D57 / D62 findings state
  each I7 at full magnitude" is **false for the five T1-H rows** — none of those documents names
  I7, FC-1 or the reliability floor for these runs (their FC-1 read `SKIPPED` at T1-H when they
  were written). The readings **are** stated, at full magnitude and per run, in three committed
  findings — Y-19 §4.2, Y-22 §2 / §3.6, Y-24 §4.2–4.3 — and the rows are declared on those
  citations, with the registering lane's finding as provenance only (§3, §3.1).
- Nothing was scored, re-scored, registered, solved or edited beyond the ledger: no sidecar, no
  board byte, no verdict text, no threshold, no mechanism, no matrix cell. One test assertion
  was corrected because it encoded a non-empty backlog (§4.1).

## 1. The ratchet at HEAD, verbatim

```
forecast-invariant artifact audit: 102 sidecar(s) with an invariants block, 1428 record(s), 97 FAIL(s) declared

forecast-invariant artifact audit FAILED:
  - caiso-2026-2030-d60-arm: FAILs ['I12', 'I7'] are not declared in invariant-failures.json. …
  - neiso-2026-2050-t3-golden3-d60: FAILs ['I3'] are not declared …
  - nyiso-2021-2025-realized-t1h-d45r-curveon: FAILs ['I7'] are not declared …
  - pjm-2021-2025-realized-t1h-d45: FAILs ['I7'] are not declared …
  - pjm-2021-2025-realized-t1h-d45r: FAILs ['I7'] are not declared …
  - pjm-2021-2025-realized-t1h-d57-clearing: FAILs ['I7'] are not declared …
  - pjm-2021-2025-realized-t1h-d62-pubbar: FAILs ['I7'] are not declared …
  - pjm-2026-2030-d60-arm: FAILs ['I12', 'I7'] are not declared …
```

(The container's scientific stack was absent; installed with
`pip3 install --ignore-installed PyYAML -r requirements.txt` to run the ratchet at all — the same
environment defect r#47 recorded.)

## 2. Reconciliation against the charter's eight

| on the ratchet's list | named in the r#48 charter | idents match |
|---|---|---|
| all eight above | all eight | yes, ident-for-ident |

No id is on the list and unnamed; no id is named and absent. The r#47 list's ninth id,
`pjm-2026-2026-scn-ws4-probe-t0-load-hi`, is gone — SCN-FIX1 declared it (#5136/#5139) exactly as
the r#48 correction says. `pjm-2021-2025-realized-t1h-d74-nodefaultcap` is already declared by
its own lane (#5145) and never appeared on the list.

## 3. The rows, id → idents → the committed sentence that states the reading

Every ident is exactly what the ratchet prints for that id; the sidecar's own `detail` string is
reproduced in the right-hand column so the quote and the artifact can be checked against each
other without a solve.

| # | run id | idents | the committed finding, quoted | sidecar detail (committed) |
|---|---|---|---|---|
| 1 | `caiso-2026-2030-d60-arm` | I12, I7 | `FINDING-capx-d60-2026-09-05.md` §5.3: *"Determination HOLD → HOLD and EVERY SCORED ROW IS IDENTICAL — FC-1 `FAIL ['I12','I7']` on the same three years with the same MW"* (vs its control). Pre-derived before the solve in `PREDECL-capx-d60` §6.1 P2/P4: *"I7 stays FAIL in 2026, 2027 and 2028 … FC-1 therefore stays `FAIL ['I12','I7']`."* | I7 2026–2028: firm 55,030 / 54,936 / 57,589 < req 57,306 / 58,671 / 60,082 MW; I12 10.4 / 7.7 / 10.2 % vs band [15, 30] % |
| 2 | `pjm-2026-2030-d60-arm` | I12, I7 | D60 §5.4: *"THE STOP. Addendum C.4 declared 'any I12 year more negative than the control's' a STOP"* — arm **−11.6 / −15.6 / −15.8 / −16.5 %** in 2027–2030 (the table there; identical to the sidecar). D60 Addendum E.4: *"I7 and I12 both FAIL on all four runs (control, D50, arm, D45-R) — no determination anywhere is disturbed by this control"*, with the STOP re-attributed to the SCN-LOAD demand hunk (−4.6 to −8.4 pts) against gates pushing +4.18–4.50 pts the other way. | I7 all five years, 2030: firm 168,299 < req 189,450 MW; I12 2026→2030: −9.5 → −16.5 % |
| 3 | `neiso-2026-2050-t3-golden3-d60` | I3 | D60 §5.5: *"P16 HIT exactly: determination HOLD → HOLD, identical reasons and caveats, and ZERO of the 19 scored rows changes status"* — against GOLDEN-3 (`neiso-2026-2050-t3-golden3-bau`, declared I3), whose reading is `FINDING-capx-d47-golden3-attestation` §1.1: *"FC-1 (I3 renewable dump) … still FAIL"*, cause `FINDING-capx-t3-neiso-golden-2026-08-30.md` §6.3(2): *"I3 FAIL — out-year renewable dump, rising monotonically."* The arm's own terminal values: `FINDING-y24` §4.2 *"dump leg, not slack: 2043 2.36 % → 2050 7.97 % of renewable potential"*. | I3 2043–2050: dump 2.36 → 7.97 % of renewable potential (control 2.17 → 7.74 %) |
| 4 | `pjm-2021-2025-realized-t1h-d45` | I7 | `FINDING-y22-t1h-invariant-skip-2026-09-06.md` §3.6: *"`pjm-…-d45` — FAIL 2025, −6,346 — partly — (A) 18.1 GW exit wave 2024 + FPR basis step + peak growth; (B) backstop capped 1,012.8; (C) bar gap present, unmeasurable pre-D52"*; §2 lists it `FAIL ['I7']`. `FINDING-y19` §4.2: *"2025: 138,286 < 144,632 MW (−6,346)"*. Provenance: D45 §1 (the L1 pool). | 2025: firm 138,286 < req 144,632 MW |
| 5 | `pjm-2021-2025-realized-t1h-d45r` | I7 | Y-22 §3.6: *"`pjm-…-d45r` — FAIL 2025, −6,623 — partly — as d45, +277 MW from the dates channel — deepens, does not cause"*. Y-19 §4.2: one-field sibling `pjm-…-t1h-d45r-fixed` reads *"I7 PASS: held"*. Provenance: D45 §4–§5 as filled by D45-R (the L1 replay at HEAD). | 2025: firm 138,009 < req 144,632 MW |
| 6 | `pjm-2021-2025-realized-t1h-d57-clearing` | I7 | Y-22 §3.6: *"`pjm-…-d57-clearing` — FAIL 2025, −3,020 — partly — 60 % is bar — (C) measured 1,807 MW; residual ~1,213 MW real, (A)+(B)"*; §0: *"on `pjm-…-d57-clearing` 2025 the screens defended 148,798 MW while I7 grades 150,605 MW"*. Provenance: D57 §3.1 arm A, the bare `pjm-t1h` key. | 2025: firm 147,585 < req 150,605 MW |
| 7 | `pjm-2021-2025-realized-t1h-d62-pubbar` | I7 | Y-22 §3.6: *"`pjm-…-d62-pubbar` — FAIL 2025, −4,750 — partly — as d57, same screen bars"*; Y-24 §4.2: *"a new supply level (145,855 MW) against the D57-era 150,605 MW requirement"*. Provenance: D62 §8 DO-NOT-ARM, registered suffixed by D63 (which *"declares no invariant failure and adjudicates none"*). | 2025: firm 145,855 < req 150,605 MW |
| 8 | `nyiso-2021-2025-realized-t1h-d45r-curveon` | I7 | Y-22 §3.6: *"`nyiso-…-d45r-curveon` — FAIL 2023 −1,119, 2025 −1,683 — partly — (A) 3,496 MW exit wave 2023; backstop never fires; both failing years are non-weather, the passing year is the weather year"*. Y-19 §4.2: the `capacity_clearing_posture` flip is the **only** delta vs `nyiso-…-t1h-d45r`, which reads *"I7 PASS: held"*. Provenance: D45 §5.3 as filled by D45-R. | 2023: 31,493 < 32,612; 2025: 32,712 < 34,395 MW |

### 3.1 The citation discrepancy, reported rather than papered over

The charter's STEP 2 rule is *"A FAIL you cannot cite from a committed finding gets NO row and a
report line instead."* Rows 4–8 **are** citable — Y-22 §3.6 states each one by run, year, MW and
cause — but **not from the findings the charter named**. Checked by grep for `I7`, `FC-1`,
`reliability floor`, `accredited firm` and each run's own MW figures:

| charter-named finding | what it says about the run's I7 |
|---|---|
| `FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md` (incl. the D45-R-filled §4–§9) | nothing — the only I7 text is the T1-**F** P13/P14 grading rows |
| `PREDECL-capx-d45r-2026-09-04.md` | nothing at T1-H |
| `FINDING-capx-d57-2026-09-05.md` §3 | nothing — 150,605 appears only as a requirement reconciliation (§3.1 table) |
| `FINDING-capx-d62-2026-09-06.md` §8 | nothing |
| `FINDING-capx-d63-2026-09-06.md` | *"this lane declares no invariant failure and adjudicates none"* |

That is not those lanes' omission: at every one of their solves the T1-H verdict key read
`FC-1: SKIPPED — "no committed invariant record"` — the dead `_invariant_map` branch Y-22 §1
quotes at the line — so there was no FC-1 row for them to write down. The readings entered the
record only through the audit lanes, which is why the rows cite Y-19 / Y-22 / Y-24 and carry the
capx finding as provenance.

**What the declaration does and does not say about the T1-H five.** Y-22 §4.1 declined to
declare them because cause (C) — I7 grades the LP's *measured* hindcast peak while the floor and
backstop defended the *screen* peak, 1,807 MW / 60 % of the d57-clearing shortfall — makes the
bar partly wrong, and routed that adjudication to the capx director desk (§4.2 item 2). The
director's r#47/r#48 charter then ordered the declaration as a records act. The `d80_note` in the
ledger therefore carries Y-22's (A)/(B)/(C) decomposition **verbatim and un-re-attributed**,
records the reading exactly as the checker grades it, at full magnitude, and adjudicates nothing
about which bar I7 should grade: Y-22 §3.5 and §4.2 items 2–5 stay open as routed, and a bar
re-adjudication that shrinks or clears a row means deleting its line per `how_to_update`.

## 4. The baseline prune, and the one test it broke

All eight were the **last** lines of `registration_ratchet_baseline`. `invariant_ledger
.stale_baseline_entries` reports a pair as stale the moment it is declared (*"the declaration is
the real record and the baseline line is dead weight"*), so — as SCN-FIX1 §1.5 already
established — the prune is mandatory, and the block is now `{}`. Exactly the eight declared
runs and no others were removed; the ratchet's `--sidecar-dir` audit prints no stale-baseline
line after the change.

### 4.1 `test_committed_ledger_baseline_is_consistent_with_the_committed_sidecars`

Read `assert baseline, "the ratchet baseline block is missing"` — which treats an **empty**
block as a **missing** one. It passes on the pre-edit file and fails on the post-edit file for
that line alone; every other assertion in the test (real sidecar, still-failing ident, not
also declared) is vacuous over an empty block, which is the test's docstring intent (*"the
baseline being exactly the standing backlog and nothing more"*) reached at a backlog of zero.
Corrected to assert the **key is present and is a dict**, with a comment naming this finding.
22 / 22 pass; ruff check + format clean. No other test or script reads the committed baseline
(grep over `tests/` and `scripts/`).

## 5. The ratchet after, verbatim

```
forecast-invariant artifact audit: 102 sidecar(s) with an invariants block, 1428 record(s), 97 FAIL(s) declared
forecast-invariant artifact audit OK
```

EXIT 0. Same sidecar set; the 97 declared-FAIL count is unchanged because the audit counts FAIL
records, not declarations — the eight runs' 10 pairs moved from *undeclared* to *declared*.

## 6. What this lane did NOT do

No solve, no score, no re-score, no registration, no sidecar edit, no `ff-verdicts.json` /
`program-status.json` byte (D65-B-R's this window), no verdict text, no threshold or
invariant definition, no `curated_subsets` entry, no keeper / marker / freeze file, no
`ScenarioConfig` field, no mechanism-matrix cell (rule 28 — nothing tested). The `d18_note`
and `dominant_open_causes` text are untouched; the T1-H I7 cause stays as Y-22 routed it.

## 7. Files touched

| file | change |
|---|---|
| `frontend/data/hindcast/invariant-failures.json` | +8 `declared_failures` rows (10 pairs); `registration_ratchet_baseline` → `{}`; `d80_note` appended (244 lines — under rule 27's 300-line blob-verify bar; the pushed blob's sha256 was compared to local anyway) |
| `tests/scoring/test_invariant_declaration_ratchet.py` | the empty-baseline assertion (§4.1) |
| `docs/handoffs/FINDING-capx-d80-2026-09-06.md` | this document |
