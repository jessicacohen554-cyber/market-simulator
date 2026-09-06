# FINDING neiso-106 (second, incidental) — the Calibration Status per-year ladder reads `NOT-YET` on EVERY year of two ISOs' CALIBRATED keepers, on a spurious governance failure

> **RESOLVED 2026-09-06 by session neiso-107**, run as a **cross-ISO governance session** (not a
> NEISO calibration lane) for the §4 reason. The fix is §5's, in the caller: `determine_from_artifacts`
> now scores C6 on the **run's own** scored span, unfiltered by the caller's `years` argument, so the
> partition-span callers in `build_status` / `audit_keepers` are fixed by the same line. The rule 1 (b)
> equality is **NOT** relaxed. Measured over every registered run, twice — at `49773428` (16 runs,
> 15 rows) and again rebased onto `dd78f46b` (14 runs, 12 rows, after the MISO lane's own prunes):
> **0 run-level determinations move**, and every affected **per-year row** moves off the spurious
> `governance gate FAIL` onto its true determination (`status/NEISO.js` + `status/MISO.js` rebuilt;
> the other four ISOs' parts were untouched and `build_status.py --check` passes for all six). `RUBRIC_VERSION` stays **3.6** — the rubric was
> always right, the caller asked it the wrong question. Guard:
> `tests/scoring/test_calibration_verdict.py::PerYearGovernanceScopeTests` (5 tests; all five fail
> against the pre-fix line, and two of them pin that a genuinely per-year `years_held` still FAILs —
> including on the one year it was held on, the hole a subset test would have opened).
> Session record: `docs/calibration-log/governance.md` § neiso-107.

**2026-09-06, session neiso-106. ZERO LP minutes. NOTHING WAS FIXED — this is an escalation, not a
repair**, for the reason in §4. Found while verifying this lane's own rule 30(b) surface.

---

## 1. The defect

`frontend/data/backcast/status/NEISO.js`, the part that renders the Calibration Status page's
per-year table (rule 30(b)'s surface), currently reads:

| year | tier | rendered determination |
|---|---|---|
| 2020 | validation | **NOT-YET** |
| 2021 | validation | **NOT-YET** |
| 2022 | validation | **NOT-YET** |
| 2023 | **training** | **NOT-YET** |
| 2024 | **training** | **NOT-YET** |
| 2025 | **training** | **NOT-YET** |

…while the run-level determination on the same keeper, in the same file, reads **`CALIBRATED`**.
Every row carries the same reason:

```
governance gate FAIL: attestation false: levers_trace_to_measured_input,
no_fit_to_price_residuals; authorized_price_tuning years_held [2023, 2024, 2025]
does not cover every scored year [2023] (rule 1 (b): ONE config across all years)
```

**The rows are wrong, and they are wrong in the most misleading possible direction**: on the exact
surface rule 30(b) designates for the holdout ladder, and in a way that makes a `CALIBRATED` ISO's
own training years look like failures.

## 2. Root cause

`scripts/build_status.py::build_years` scores each year in isolation —
`cv.determine(run_id, years=[year])` — and that `years` argument propagates into
`calibration_verdict.py`'s rule 1(b) check on the authorized price-tuning declaration
(`scripts/calibration_verdict.py:2776-2781`):

```python
held = dec.get("years_held") or []
if years and sorted({int(y) for y in held}) != sorted({int(y) for y in years}):
    return False, (... "does not cover every scored year" ...)
```

It is an **exact-set equality**, compared against the caller's *display subset*. So for any run
that legitimately declares the channel, the check can never pass when one year is asked for on its
own: `{2023,2024,2025} != {2023}`.

**The check itself is correct and should not be loosened.** Rule 1 condition (b) — ONE config
across every scored year — is exactly what stops per-year fitting, and the equality is the right
test *of a run*. The category error is in the caller: `years_held` describes the config held across
**the run's** scored years, not across whatever subset is being rendered. The per-year path is
asking a run-level question about one row.

## 3. Blast radius — measured, cross-ISO, and pre-existing

Six registered runs declare `authorized_price_tuning`, across **two ISOs**:

| ISO | run | `years_held` |
|---|---|---|
| MISO | `2026-09-05-miso-220-nonsteam-lift` | [2023, 2024, 2025] |
| MISO | `2026-09-06-miso-230-ctdrag-seam` **(MISO's keeper)** | [2023, 2024, 2025] |
| NEISO | `2026-09-06-neiso-105-fossil-offer` | [2023, 2024, 2025] |
| NEISO | `2026-09-06-neiso-105-touchpoints-2020` | [2020, 2021, 2022] |
| NEISO | `2026-09-06-neiso-106-fossil-offer` **(NEISO's keeper)** | [2023, 2024, 2025] |
| NEISO | `2026-09-06-neiso-106-touchpoints-2020` | [2020, 2021, 2022] |

**MISO's committed `status/MISO.js` shows the identical defect at HEAD** — run-level `CALIBRATED`,
all three training rows `NOT-YET`, same reason string. Verified read-only; **no MISO file was
touched** (rule 25 `[R-ISO-SCOPE]`).

**It is pre-existing, not introduced here.** The committed `status/NEISO.js` at the neiso-105
promotion (`774c9207`, on `main`) already renders all six rows `NOT-YET` on the same reason. This
lane inherited it and reproduces it exactly.

## 4. Why this lane did NOT fix it

The fix belongs in `scripts/calibration_verdict.py` or `scripts/build_status.py` — **the scoring
instrument**, shared by all six ISOs. Three reasons to escalate rather than patch:

1. **Cross-ISO blast radius.** Any correct fix changes MISO's rendered status part as well as
   NEISO's. A NEISO calibration lane editing a shared scorer so that another ISO's published page
   changes is precisely what rule 25 `[R-ISO-SCOPE]` exists to prevent.
2. **It is a governance instrument.** A change that turns `NOT-YET` rows into `CALIBRATED` rows is
   a change to what the dashboard asserts about calibration, however sound the reasoning. That is
   not a thing to slip into a promotion commit.
3. **Nothing in this session depends on it.** The run-level determinations — the ones that actually
   gate, and the ones rule 30(c) makes the ISO's determination — are computed correctly and are
   unaffected. Only the per-year display rows are wrong.

## 5. Proposed fix, for whoever owns it

**One line, in the caller, not the check.** In `calibration_verdict.determine`, pass the **run's own
declared scored years** to `score_governance` regardless of the caller's `years` filter — the
governance gate is a property of the run, not of the year being displayed. Equivalently, in
`build_status.build_years`, score governance once per run and reuse it across that run's rows.

**Do not** relax the equality in `_score_authorized_price_tuning` to a subset test: that would let a
genuine per-year config pass rule 1(b), which is the failure mode the rule exists to catch.

**Suggested verification for that lane** (cheap, no solve): rebuild `status/NEISO.js` and
`status/MISO.js` and confirm (a) every previously-`NOT-YET` row on a `CALIBRATED` keeper now reads
its true per-year determination, (b) no run-level determination anywhere moves, and (c) a
synthetic attestation carrying a genuinely per-year `years_held` still FAILs rule 1(b).

## 6. What is true about NEISO in the meantime

Unaffected and independently verified in this session: NEISO's keeper
`2026-09-06-neiso-106-fossil-offer` is **`CALIBRATED`** (0 FAILs; C1 all 12/12 · free 8/8;
C1/C2/C3a/C3b/C4/C6/C8 PASS; C3c the lone ledgered caveat), its touchpoint bundle
`2026-09-06-neiso-106-touchpoints-2020` is **`CALIBRATED`** with 0 degraded criteria against the
in-sample column, and **all six years 2020–2025 PASS C3a** on the measured load-weighted prices.
The per-year *rows* are wrong; the per-year *results* are not.
