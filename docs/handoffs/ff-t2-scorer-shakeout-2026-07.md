# FF-3G — T2 determination scorer shakeout (T1-scale, L-VAL)

**Session.** FF-3G (Wave 3, L-VAL) of `docs/forecast-development-plan-2026-07.md`.
Exercises the `scripts/forecast_verdict.py --tier t2` path — which had **never been
run on any bundle** before this session (FF-2D scored only `t1f`/`t1x`/`t1h`;
`docs/handoffs/ff-t1-gate-verdicts.json`). Real T2 solves (2026–2035) are
**§2.1b-deferred**, so this is a scorer shakeout against **existing + synthetic**
inputs — **NO LP solve of any kind**. Findings-first; no model code, threshold,
band, or default changed (rules 1/6/22). The only code added is the additive T2
shakeout tests (a new sibling test file); no existing source file is rewritten.

## 1. Headline

**The `--tier t2` (and, by reuse, `--tier t3`) scorer path is functionally sound.**
Across every configuration exercised, all eight categories FC-1..FC-8 resolve to a
valid `PASS`/`CAVEAT`/`FAIL`/`SKIPPED`/`UNATTESTED`/`n/a` token, offending values
print, the JSON sidecar emits, `render_text`/`condensed_sidecar` never crash, and
the HOLD exit code (1) is correct. **No crash and no scorer/plumbing bug requiring a
logic fix was found.** The §2.1b-gated instruments degrade to `SKIPPED` cleanly
(never a spurious `FAIL`), which correctly `HOLD`s a T2 promotion (unscored required
evidence never promotes, rubric §3/§4).

One **documentation defect** was identified: the comment on the `STABILITY_WINDOW` /
`I12_WARN_CHAIN_FAIL` constants claims they "fail FC-2 row 1 at t2", but they are
**unused** — that escalation is delivered **upstream** by the I12 producer (§3). The
correct reading is recorded here (§4a); the one-comment in-code edit is **deferred**
to a session that substantively touches the scorer, so a 1,844-line core file is not
rewritten wholesale over the push API for a comment (rule 27). Two further items are
**recorded, not fixed** (both correctly out of a no-tuning shakeout's scope): the
same I12 mirror-constant coupling, and the FC-4 raw-crossover schema seam already
owned by L-VAL (§4).

## 2. What was run (shakeout matrix)

Inputs, per prompt: an **existing T1 bundle** (the FF-0B ERCOT baseline,
`frontend/data/hindcast/ercot-2026-2030-ff-t1f-baseline.json`) reconstructed into
the `full_horizon_summary` shape the scorer consumes, plus a **synthetic t2 summary**
built from it (its 2026–2030 trajectory extended to 2035 so the t2-only FC-2 rows
have a final year + a multi-year window). Real committed instruments were reused
where they exist: the MISO `curve-ff2c` hindcast `score.json` (FC-3), the ERCOT
`ff2d` crossover (FC-4, both raw and adapter-shaped). Corridor/battery are synthetic
authored fixtures. **No committed dashboard artifact, keeper, or holdout year was
touched.**

| # | Config | Result | Every FC token valid? | Crash? |
|---|---|---|---|---|
| A | t2, **instruments absent** (synthetic summary + run_config + dof; clean invariants) | **HOLD** (FC-3/4/5/6 SKIPPED) | yes | no |
| B | t2, **faithful** synthetic summary (real FF-0B invariants: I3 FAIL, I12/I14 WARN) | HOLD (FC-1 FAIL, FC-2 CAVEAT, FC-3/4/5/6 SKIPPED) | yes | no |
| C | t2, **fully wired** (real hindcast + adapter-shaped crossover + corridor + battery) | HOLD (FC-3/FC-4 FAIL on real bands, FC-5 CAVEAT) | yes | no |
| D | t2, **fully wired, all green** (synthetic passing instruments) | **PROMOTE** | yes | no |
| E | t2, **raw crossover** (FF-0E emitter shape, no adapter) | HOLD (FC-4 FAIL — quarantine marker not found top-level) | yes | no |
| F | t3, all t2 instruments present+green, **no attestation** | HOLD (FC-7 **UNATTESTED**) | yes | no |
| G | t3, full bundle **+ attestation** | **PROMOTE** | yes | no |
| — | 5 edge probes (empty trajectory; missing RM/scarcity; curve-ON no-position; no-summary; unknown-ISO floor) | all HOLD, all resolve | yes | no |

Both poles are reachable: **HOLD** when the §2.1b instruments are absent, **PROMOTE**
when every required instrument is present and green — so the gate is neither stuck-open
nor stuck-closed. The FC-2 t2-only rows (row2 terminal drift, row6 scarcity gate) and
the FC-7 t3 attestation path fire for the first time and behave per rubric §2/§3.

## 3. Which T2 categories are genuinely un-scorable without the gated instruments

Per prompt item 3 — these stay **§2.1b-gated**; the scorer's only job (met) is to
degrade honestly (SKIPPED, never a silent pass or a stray FAIL). "Scorable from the
summary alone" means a real 2026–2035 `full_horizon_summary.json` is sufficient; the
others need a distinct committed instrument that only a real (deferred) solve or an
intake produces.

| Category (t2 applicability) | Instrument it needs | Absent ⇒ | Scorable today? |
|---|---|---|---|
| FC-1 structural (**R**) | I1–I14 in the summary | SKIPPED | **from summary** |
| FC-2 rows 1/2/3/4/6 (**R**) | trajectory + I12/I13 in the summary; floor from constants | SKIPPED | **from summary** |
| FC-2 row 5 position / "equilibrium" (**R**, curve-ON) | a committed position-validation artifact (real curve-ON solve) | row5 SKIPPED ⇒ FC-2 SKIPPED for curve-ON ISOs | **gated** (needs solve) |
| FC-3 capacity skill (**R**) | imported t1h hindcast `score.json` | SKIPPED | instrument exists per-ISO; **t2-native evolution has no measured actual** |
| FC-4 crossover skill (**R**) | imported t1x `score_crossover.py` output | SKIPPED | instrument exists per-ISO (ERCOT/PJM); **schema seam, see §4** |
| FC-5 external corridor (**R**) | committed benchmark tables + authored disposition (FF-0D/FF-0F) | SKIPPED (holds T2 — self-enforcing, rubric §6) | **gated** (intake pending) |
| FC-6 driver response (**R**) | `run_driver_battery.py` output / paired P1–P3 at the t2 config vintage | SKIPPED | **gated** (needs battery run) |
| FC-7 provenance/DOF (**R**) | `run_config.json` + `dof_ledger.json` (+ attestation at t3) | run_config absent ⇒ FAIL; dof absent ⇒ CAVEAT; attestation absent ⇒ UNATTESTED (t3) | **from run artifacts** |
| FC-8 runtime (**R\***, non-blocking) | per-year perf in the summary | SKIPPED | **from summary** |

Net: FC-1, FC-2 (rows 1/2/3/4/6), FC-7, FC-8 are scorable the moment a real T2
summary + run_config exist. **FC-2 row 5, FC-3, FC-4, FC-5, FC-6 require their own
committed instruments** and honestly SKIP until those land — exactly the §2.1b-gated
set, and exactly what the scorer must (and does) surface as unscored rather than pass.

**Tier-applicability tokens** (`APPLICABILITY`) were re-verified against rubric §3
and match verbatim (already pinned by `test_matrix_transcribes_rubric_table`; no
change).

## 4. Two recorded items (out of scope for a no-tuning shakeout)

**(a) The I12 t2/t3 stability escalation is delivered upstream — mirror constants,
not a dead gate.** Rubric §3 says a t2/t3 "I12 breach trend (I12 FAIL, or a WARN
chain of ≥3 consecutive years inside 2031–2035) fails row FC-2.1". The scorer
constants `STABILITY_WINDOW = (2031, 2035)` and `I12_WARN_CHAIN_FAIL = 3` were
defined but **never referenced**, and the old comment wrongly claimed they gate at
t2. In fact the escalation is already enforced by the **I12 producer**:
`check_forecast_invariants.py`'s `reserve_margin_consecutive_fail` (default **3**)
turns any ≥3-consecutive-year reserve-margin breach into **I12 FAIL**, which
`score_fc2` row 1 maps to **row FAIL** at every tier. So a genuine 2031–2035 chain
reaches the scorer as I12 FAIL (→ FAIL), never as a stray WARN; a sub-3-year
excursion is I12 WARN (→ CAVEAT). Verified end-to-end (I12 FAIL ⇒ FC-2 row1 FAIL;
I12 WARN ⇒ CAVEAT). The two constants equal the producer's threshold (3 == 3), so
there is **no gap** and no bundle can slip through. They are retained as the
committed rubric-§3 mirror; **re-implementing a scorer-side windowed chain would
double-count I12 and risk a threshold change (forbidden by the binds)**. Disposition:
the correct reading is recorded here; the one-comment in-code correction (state where
the behaviour lives + note the mirror must track the producer if that threshold ever
drifts, since they are not auto-coupled) is **deferred** to a session that
substantively edits the scorer, rather than rewrite the 1,844-line file over the push
API for a comment (rule 27). A new test pins the live coupling
`I12_WARN_CHAIN_FAIL == reserve_margin_consecutive_fail` (skips when the model stack
is absent), so a future producer-threshold drift is caught regardless of the comment.

**(b) FC-4 raw-crossover schema seam — already owned by L-VAL.** The committed FF-0E
emitter (`score_crossover.py`) nests the quarantine marker under `meta.refusal_marker`
and errors under `dispatch_skill.*_forecast_err_frac`; the scorer's FC-4 reads a
top-level `refusal_marker` and a flat `metrics` list. Feeding the **raw** committed
crossover directly therefore trips the rule-22 "marker ABSENT ⇒ FAIL" gate
(config E) — a plumbing artifact, not a real verdict. This is **tier-agnostic**
(identical at t1x, which already shipped) and is bridged by the sanctioned
`scripts/_ff2d_crossover_adapter.py`; FF-2D §4.2 already routed the proper fold-in
into `score_crossover.py` to L-VAL. It is **not a t2-scorer bug** and editing the
FC-4 reader here would re-litigate that routing and risk changing t1x behaviour — so
it is recorded, not changed. A test pins the current raw-shape FAIL so any future
fold-in is a conscious verdict change, not a silent flip.

## 5. What changed / what did not

**Added (new file only):**
- `tests/test_forecast_verdict_t2.py` — new `T2ShakeoutTests` (11 tests) + the
  `_t2_summary` / `_t2_all_instruments` synthetic fixtures (reusing the base module's
  fixture builders by path-load, so thresholds are still READ from the scorer's
  constants): clean SKIPPED degradation ⇒ HOLD; every-category-valid-token sweep;
  fully-wired ⇒ PROMOTE; the t2-only FC-2 rows (terminal drift, scarcity gate); I12
  FAIL ⇒ row1 FAIL and I12 WARN ⇒ CAVEAT at t2; the I12 mirror-constant coupling
  guard; the raw-crossover quarantine trip; the t3 UNATTESTED path and
  t3-with-attestation PROMOTE. **84 tests pass** across both files (1 skip: the
  coupling guard, which needs numpy/`market_sim` — runs in CI). A **sibling** file
  (not appended to the 866-line `tests/test_forecast_verdict.py`) so no ≥300-line
  existing source file is regenerated wholesale over the push API (rule 27).

**Not changed:** no model code, no scorer logic, no offer curve, no default, no
rubric threshold or band, no `APPLICABILITY` token, and — deliberately — **no
existing `≥300`-line source file** (`scripts/forecast_verdict.py`,
`tests/test_forecast_verdict.py`): the scorer's constant-comment correction is
documented here (§4a) and deferred rather than pushed as a full-file rewrite (rule
27). No LP solved. No dashboard artifact, keeper, or holdout year (2022 / ≤2021 /
2019 / H1-2026) touched (rule 22). No GitHub Actions workflow added (CLAUDE.md CI
policy). Pushed via `push_files`; only new files (each < 300 lines) are added.

## 6. Follow-ups (routed, not done here)

1. **Real T2 shakeout** — re-run `--tier t2` on a genuine 2026–2035 bundle once a T1
   ISO clears the §2.1b gate; this session proves the scorer is ready for that input.
2. **FC-4 marker fold-in** (L-VAL, from FF-2D §4.2) — emit `refusal_marker` + a flat
   `metrics` list from `score_crossover.py` so the adapter is unnecessary; when it
   lands, the §4(b) test flips deliberately.
3. **FC-5 benchmark intake** (FF-0D) — until the §6 tables land, FC-5 SKIPs and holds
   every T2 promotion (self-enforcing, as designed).

*Produced 2026-07-21 (FF-3G). No solve; scores existing + synthetic bundles only.
Forecast-mode scorer shakeout; no backcast keeper, dashboard artifact, or holdout
year touched (rules 1/6/22).*
