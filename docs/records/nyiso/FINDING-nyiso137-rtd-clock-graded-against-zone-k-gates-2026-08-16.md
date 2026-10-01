# FINDING nyiso-137 — the RTD-clock disclosure does **NOT** block the joint Zone-K lever, and the reason the handoff gave for thinking it might is **factually wrong**. What it *does* put at risk is the C3c ACTUAL count, harder than the adjudication said.

**Session nyiso-137, 2026-08-16.** The handoff's instruction for lever (a) was
*"Ask for the charter first; and grade the RTD-clock disclosure against its K6
gate up front."* That grading is done. **No LP was solved, no year scored, no run
registered, no keeper moved, no cell verdict moved, no pre-registration filed,
and no product corrected** — `derive_actual_lmp.py` is untouched and the
committed parquet is unchanged. This is the nyiso-136 shape: identification
before mechanism, no solve spent.

Probe `scripts/probes/_nyiso137_rtd_clock_c3c_grading.py`, record
`results/calibration/_nyiso137_rtd_clock_c3c_grading.json`. Read-only, input
side only.

**Rule 22:** 2023–2025 only. The twelve 2022 source zips **are on disk** and were
**deliberately not read** — the ACTIVE holdout spend freeze was re-confirmed HELD
on 2026-08-15 and this session did not test it.

---

## 1. THE HANDOFF'S PREMISE IS FALSE — K6 IS NOT A PER-HOUR TAIL COUNT

The handoff states, twice, that lever (1)'s *"K6 gate is itself a per-hour tail
count"* and that this is what puts the lever at risk. **It is not.** K6 is the
**forcing** gate. Its pre-registered text
(`PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md` §6):

> **K6** | forcing | any D-2 mechanism's forced share **rises**, or
> `nyiso_local_selfsupply` reappears for Long_Island (rule 19), or C8 flips

and what actually fired it at nyiso-130 (§5a) was **forced energy in TWh** —
`reliability_floor × ST_GAS` rising 2.784 → 3.002, 2.797 → 3.216,
2.371 → 2.598 TWh. The implementation agrees:
`scripts/probes/_nyiso130_ab_gates.py::k6_forcing` compares D-2 forced shares
between the two arms' own bundles.

The per-hour tail count is **C3c**, which is a *criterion*, not a kill gate — and
under the nyiso-130 disposition (§8) C3c is explicitly **not** part of the
promote test (*"PROMOTE if every kill gate K1–K6 is silent and C1 / C2 / C3a /
C3b / C4 / C6 / C8 all still PASS — **whatever C3c does**"*). The two things the
handoff conflated sit on opposite sides of the promote rule.

## 2. ALL SIX KILL GATES ARE MODEL-SIDE — the disclosure cannot reach any of them

Every gate is computed from the **arms' own output bundles**, control vs
treatment. None reads `actual_lmp_hourly_NYISO.parquet`.

| gate | quantity | source | at risk? |
|---|---|---|---|
| K1 config isolation | differing `scenario_config` fields | arm `meta.json` | **No** |
| K2 feasibility | slack / dump energy | arm bundles | **No** |
| K3 liveness | in-window `limit_up` = 940.0 | `hourly/network_<y>.parquet` | **No** |
| K4 scope | every other link's `limit_up` | same | **No** |
| K5 seam | control-vs-treatment `NYISO_external>*` **energy**, ±2 % | same | **No** |
| K6 forcing | D-2 forced share / forced TWh, C8 | arm bundles | **No** |

K5 was the only candidate worth checking, and it is clean twice over.
`_nyiso130_ab_gates.py::k5_seam` sums external-link **MW from each arm's own
network parquet** — there is no actual-price series in the gate at all. And
independently, the model's import **pricing** path
(`model/interchange/nyiso.py:105-108`) reads only the **PJM** and **NEISO**
neighbour series; NYISO's own file is never passed to `neighbor_lmp_hourly`,
exactly as ADDENDUM §A.6 found. PJM's raw product is separately measured
bit-exact (1.4e-05).

**Conclusion: the NYISO-RTD-CLOCK disclosure does not contaminate the joint
Zone-K lever's kill-gate instrument. Lever (a) is NOT blocked by it.**

## 3. THE PROMOTE-RULE CRITERIA THAT *DO* READ THE SERIES ARE GRADED, AND SAFE

C3a (mean-LMP level) and C3b (monthly price duration / shape) score against the
mis-binned `rt` column. Both are **aggregates**, and the re-binning is a
permutation of samples between adjacent hours, so its level effect is near-nil —
measured, not assumed, on 6,018 whole staged in-training hours:

| quantity | measured |
|---|---:|
| hours moved > $0.01 | 5,654 of 6,018 (**94.0 %**) |
| pooled mean price, BEGINNING → ENDING | 29.1725 → 29.1622 |
| **pooled mean shift** | **−0.0353 %** |
| worst single month mean shift | **−0.5063 %** (2024-04) |
| remaining 8 months | all within ±0.20 %, 7 of 9 within 0.07 % |

C3a's band is ±10 % and the keeper reads +8.8 / +0.8 / −3.4 %, so the nearest
margin is **1.2 pp** — three orders of magnitude above a 0.035 % shift. C3b's
monthly NRMSE ceiling is 0.20 and no month's mean moves by more than 0.51 %.
**Neither can be moved across its band by this defect.** C1 / C2 / C4 / C6 / C8
do not read an LMP series at all.

## 4. WHAT *IS* AT RISK — and the adjudication under-stated it

ADDENDUM §A.6 concluded that *"level statistics (C3a, monthly MAE) are
near-invariant and **the C3c tail region moves by cents**"*. The first half
reproduces (§3). **The second half is refuted.** The convention delta is strongly
**heteroskedastic in price**, and it is largest exactly where the tail lives:

| price region (BEGINNING) | n | mean \|Δ\| | max \|Δ\| | mean signed |
|---|---:|---:|---:|---:|
| all hours | 6,018 | **$0.4237** | 72.43 | −$0.0103 |
| > $100 | 15 | $17.2158 | 72.43 | −$3.73 |
| > $200 | 7 | $30.9854 | 72.43 | −$5.15 |
| **> $300 (the tail itself)** | **3** | **$35.5529** | **72.43** | **−$32.25** |

**An 84× ratio between the tail region and the all-hours figure.** The reason
the adjudication missed it is visible in its own numbers: every reassuring
statistic it quoted is a **signed mean** (Δ annual-mean −$0.024, Δ top-100-hour
mean −$0.49), and signed means cancel. The **absolute per-hour** movement in the
tail is tens of dollars, not cents.

**No staged hour actually crossed $300** — 0 crossings on 6,018 hours. But that
is not reassurance, because all three staged tail hours started far from the
threshold and stayed on the same side of it:

| UTC hour | BEGINNING | ENDING | \|Δ\| |
|---|---:|---:|---:|
| 2024-04-30 00:00 | $450.22 | $377.79 | $72.43 |
| 2025-08-10 22:00 | $593.16 | $598.10 | $4.95 |
| 2025-08-10 23:00 | $392.26 | $362.98 | $29.28 |

The staged months carry only **1 of 10, 3 of 12 and 2 of 42** of the actual tail
hours, so a direct recount of 10 / 12 / 42 is **not possible** on present
coverage and is **not attempted**.

## 5. THE CEILING, AND THE VERDICTS IT REACHES

An hour can only change the count by crossing $300, so the population within ±d
of the threshold is a hard ceiling for any delta bounded by d. Ruler: the
**tail region's own measured max, $72.43** — not the all-hours max, which would
be the wrong sample. Counted on the committed series:

| year | committed tail | hours within ±72.43 | could drop out | could come in | reachable actual |
|---|---:|---:|---:|---:|---|
| 2023 | 10 | 16 | 5 | 11 | **[5, 21]** |
| 2024 | 12 | 11 | 2 | 9 | **[10, 21]** |
| 2025 | 42 | 48 | 8 | 40 | **[34, 82]** |

Mapping that onto the keeper's model counts (21 / 3 / 24) through
`calibration_verdict`'s exact C3c rule (lines 1686–1694, reproduced in the
probe):

| year | model | actual | verdict today | flips? |
|---|---:|---:|---|---|
| 2023 | 21 | 10 | **FAIL** (2.10×) | **→ PASS at actual 11 h — ONE hour** |
| 2024 | 3 | 12 | **FAIL** (0.25×) | **STABLE** — PASS needs actual ≤ 9, below the ceiling floor of 10 |
| 2025 | 24 | 42 | **PASS** (0.571×) | **→ FAIL at actual 49 h — +7 hours** |

**The lone ledgered caveat's 2023 entry is one actual-hour from disappearing, and
2025's PASS is seven from breaking.** The 2023 edge is doubly sharp: actual = 10
sits exactly **on** `TAIL_SMALL_COUNT`, so one hour *down* also switches the
scoring rule from ratio to absolute difference (|21 − 9| = 12 > 10 — still FAIL,
but by a different test).

## 6. THE DIRECTION, REPORTED AGAINST ITS OWN WEIGHT

In the staged tail region the movement is net **downward** (1 up / 2 down, mean
signed −$32.25, −6.74 % of level). Downward movement *reduces* the actual count,
which would preserve both current verdicts. **This finding does not claim that.**
n = 3 is not a rate — asserting a direction from it would be rule 21 in exactly
the form §7 of the nyiso-136 finding refused for solar EFOR. **The ceiling
governs, not the direction.**

## 7. DISPOSITION

1. **Lever (a) is NOT blocked by the RTD-clock disclosure.** Its kill gates are
   model-side and invariant (§2); its promote criteria that read the series are
   measured safe by three orders of magnitude (§3). **The charter request
   stands** — see `docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md`.
2. **A CONDITION the charter should carry.** The lever's whole purpose is C3c,
   and C3c's denominator is verdict-fragile (§5). The **arm-vs-control C3c
   delta** stays invariant — both arms score against the same actual — and that
   is what any finding may rest on. **Absolute C3c band membership is what it may
   not.** Any C3c-turning claim must be reported as CONDITIONAL on the clock
   repair, per the disclosure's own instruction.
3. **The disclosure text needs one correction** (flagged, not edited — it lives
   in an owner-gated addendum): *"the C3c tail region moves by cents"* is false;
   the tail region's mean |Δ| is **$35.55**. The rest of §A.6 stands.
4. **Third disclosure on the 2022 touchpoint — now partly discharged.** The
   RTD-clock item is **GRADED for the in-training years** by this session. It is
   **NOT graded for 2022**, which is the year it was quantified on and which this
   session did not read. The other two (import-tranche 719 MW duration RMSE,
   Transco Dec-2022 Elliott hole) are **still ungraded**.
5. **Not re-opened:** the parquet was not re-derived (only 21 monthly zips are
   staged against a 2018-2026 series, and 2022's twelve are frozen), and
   `_nyiso_wide` was not edited. Both remain owner-gated and data-blocked.

## 7a. AN INHERITED DEFECT FOUND WHILE GATING — **the designated keeper is UNREPLAYABLE at HEAD**. Flagged, not fixed.

Not this session's work and not caused by it, but it belongs on the record
because it is an **undisclosed** cost of nyiso-136's rule-26 collapse — the
declared cost that session named was the forecast lane's 11 stale sidecars, not
this:

```
tests/scoring/test_replay_keeper_strict.py::TestCurrentKeepersReplayCleanly::test_all_keeper_metas_build
SystemExit: meta.json keys not bound to solve_and_persist kwargs:
['nyiso_solar_registry_cod_dates']
```

**Confirmed PRE-EXISTING on a stashed pristine tree** (`git stash push -u`, test
re-run, same failure), so it is not an artefact of this session's diff — which is
documentation plus one standalone read-only probe and touches no code path.

**Diagnosis.** nyiso-136 DELETED the `ScenarioConfig` field
`nyiso_solar_registry_cod_dates`, but the keeper `2026-08-08-nyiso-133-cod-arm`
was solved **with the flag armed**, so its committed `meta.json` still carries
the key. `replay_keeper.build_kwargs` is deliberately STRICT — an unmapped
meta key is a hard error, never a silent drop (the miso-50..53 regression
class) — so the keeper's own recipe no longer reconstructs.

**The fix is one line and the error message names it**, but it is a **semantic
governance call, not a mechanical one**, which is why this session does not make
it: adding the name to `replay_keeper._IGNORE` asserts *"the behaviour this flag
selected is now unconditional at HEAD, so a replay that omits it is faithful"* —
which is exactly true after the collapse (`data/renewables.py` calls
`load_market_solar_monthly(..., cod_basis=True)` in both lanes), but it is the
kind of assertion rule 26 wants made deliberately and on the record rather than
as a side effect of an unrelated lever session. **Recommended to the owner as
`_IGNORE`, with the reasoning above; raised as D4 on the decision card.**

Note the contrast with the cache-key hazard nyiso-136 flagged: there,
`_CACHE_KEY_RETIRED_FIELDS` was the WRONG home for a deleted registered-optional
field because it re-inserts the name and moves the pinned key. Here `_IGNORE` is
the RIGHT home, because it governs recipe reconstruction rather than hashing and
its semantics are "not a solve kwarg", which is now true. The two are not the
same call.

## 8. WHAT THIS SESSION DID NOT DO

No LP solved, no run registered, no keeper moved, no cell verdict moved, no
pre-registration filed, no arm written. Keeper remains
`2026-08-08-nyiso-133-cod-arm` at `CALIBRATED-WITH-CAVEATS`, C3c the lone
ledgered caveat 1 of 1 at 21 / 3 / 24 h. Frontier stays **CLEARED** (2026-08-06)
and is **not** re-asserted. `RENEWABLE_AVG_CF["NYISO"]["solar"]` untouched.
Holdout posture unchanged.

**Lever queue after this session.** (1) the chartered **JOINT Zone-K
transfer-bound + downstate ST_GAS `min_gen` reconciliation** — **still open,
still needs its own owner charter and pre-registration, and now GRADED CLEAN
against the RTD-clock disclosure**; do not re-test the bare number swap.
(2) **VRE availability / forced-outage representation** — named and sized by
nyiso-136, low-value on a report-only band. (3) the FLEET-CF COMPOSITION object
is **RETIRED** (nyiso-136), joining the commissioning curve.

* Next number: **nyiso-138**.
