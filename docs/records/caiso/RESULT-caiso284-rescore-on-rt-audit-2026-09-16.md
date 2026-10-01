# RESULT caiso-284 Job A — the rescore-on-RT audit: every GATED number is already RT, five non-gated surfaces were not

**Lane:** CAISO calibration · **Date:** 2026-09-16 · **LP spent: ZERO** · keeper unchanged
(`2026-09-12-caiso-275-gascoupling`, CALIBRATED 2023–2025, lone ledgered C3c; folded 2022 rung
`…-gascoupling-2022`, NOT-YET on C3a). Nothing promoted, nothing registered, no mechanism cell
moved, no threshold moved, no band moved, no bundle re-rendered, no LP re-solved.

**Owner instruction (2026-09-16):** *"rescore the keeper so it's against rt LMP"* — asked a
second time after caiso-282 §5 reported the basis already RT, so that check was **re-done from
scratch and widened**, not cited.

---

## 0. Headline

> **A RESCORE IS BYTE-IDENTICAL ON EVERY GATED NUMBER. CAISO'S DETERMINATION DOES NOT MOVE, IN
> EITHER RUN, IN ANY YEAR.** Both keeper runs were re-scored at HEAD: `CALIBRATED` (2023–2025)
> and `NOT-YET` (folded 2022) — the same verdicts, the same magnitudes, the same single ledgered
> C3c. caiso-282's conclusion survives a much wider sweep than the one that produced it.
>
> **But the sweep was not empty.** Twenty-two surfaces were audited. **Every one that GATES is
> RT. Five that do not gate were on DA, on a DA-filled RT series, or on the wrong RT statistic** —
> including the benchmark memo the dashboard itself cites, which states the *opposite* of the
> live rubric. All five are repaired here.

| | |
|---|---|
| Surfaces audited | 22 |
| **Gated** surfaces on the wrong basis | **0** |
| Non-gated surfaces repaired | **5** (+1 rounding bug, +1 stale status part) |
| Determination change | **none** — CALIBRATED / NOT-YET, unchanged |
| New scorer failures introduced | 0 (2 tests updated: they *asserted* the defect) |

---

## 1. The re-score, run at HEAD on committed artifacts only

`scripts/calibration_verdict.py --run-id <id>`, both runs, no bundle touched:

| year | run | C3a | C3b | C3c | determination |
|---|---|---|---|---|---|
| 2022 | folded | **FAIL** +11.3 % (94.07 / 84.49 **vs RT**) | PASS 0.194 | PASS 560 h / **RT** 510 h (1.10×) | **NOT-YET** |
| 2023 | keeper | PASS +3.2 % (55.89 / 54.17 **vs RT**) | PASS 0.077 | CAVEAT 23 h / **RT** 47 h (0.49×) | |
| 2024 | keeper | PASS +8.4 % (37.55 / 34.65 **vs RT**) | PASS 0.137 | CAVEAT 0 h / **RT** 35 h (0.00×) | |
| 2025 | keeper | PASS +7.7 % (37.06 / 34.42 **vs RT**) | PASS 0.106 | PASS 0 h / **RT** 8 h (small-count) | **CALIBRATED** |

Every C3a record's own `metric` string reads `vs RT (load-weighted)`; every C3c record reads
`hours RT-expressible LMP > $200/MWh`. The DA numbers exist only on rows keyed
`da_diagnostic` with status `SKIPPED`.

---

## 2. The audit table — criterion × surface × benchmark series

Basis codes: **RT✓** = pure real-time, correct · **DA-dx** = day-ahead, correctly labelled as a
non-gated diagnostic · **DA✗** = day-ahead where the rubric says RT · **RT-fill✗** = real-time
with day-ahead spliced into missing hours · **RT-eq✗** = real-time but the equal-hour statistic
where the gate uses the load-weighted one.

| # | Surface | Series it uses for CAISO | Gated? | Basis | Action |
|---|---|---|---|---|---|
| 1 | `calibration_verdict.score_price_mean` (C3a) | `avgLMP.rt_lw` | **GATED** | RT✓ | — |
| 2 | `score_price_mean_da_diagnostic` | `avgLMP.da_lw` | never | DA-dx | — |
| 3 | `score_price_shape` (C3b) | `avgLMP.rt_lw_mon` | **GATED** | RT✓ | — |
| 4 | `score_price_tail` (C3c) | `tail/actual_tail.json` → `rt_gt` | **GATED** | RT✓ | — |
| 5 | C3c `da_diagnostic` row | `da_gt` | never | DA-dx | — |
| 6 | `score_diurnal_amplitude` (D-A) | actual `rt_hod`; **model reconstructed via `lmpDeltaHr`** | reported-only, band-free | **RT-fill✗** | fixed at source (#10) |
| 7 | `bench/CAISO/<y>.json.gz` `avgLMP` | carries `rt`,`da`,`rt_lw`,`da_lw` + monthlies | data | complete | — |
| 8 | `derive_actual_lmp._lw_stats` → `rt_lw` | pure `rt` column, NaN-aware, **no DA fill** | data | RT✓ | — |
| 9 | `derive_actual_tail` → `rt_gt` | `np.nansum(rt > thr)` on the pure column | data | RT✓ | — |
| 10 | `render_calibration_html._actual_lmp_hourly` | RT, **DA-filled where RT is NaN** | feeds payload | **RT-fill✗** | **REPAIRED** |
| 11 | `render_calibration_html._actual_rt_padded` | same fill, scattered to 8760 | feeds payload | **RT-fill✗** | **REPAIRED** |
| 12 | payload `ordc.hoursGt200.actual`, CAISO 2023 | **62 h** (DA-filled) vs gated **47 h** | never read | **RT-fill✗** | fixed at source (#10) |
| 13 | payload `lmpDeltaHr` | model − DA-filled RT | heatmap + D-A | **RT-fill✗** | fixed at source (#11) |
| 14 | Run Explorer year scorecard "LMP vs actual" | `actualLMPGated` → `rt_lw` | display | RT✓ | — |
| 15 | Run Explorer `lmpDeltaRef` | equal-hour `rt` first, **deliberately** | display | RT✓ | — (documented, correct) |
| 16 | Run Explorer `mountLmpCharts` mini charts | `rt_mon` **w:2**, `da_mon` **w:3** | display | RT-eq✗ | **REPAIRED** |
| 17 | Run Explorer `drawPriceDuration` | **`da_mon` ONLY**, legend "Actual DA" | **dead code** | **DA✗** | **DELETED** |
| 18 | Run Explorer `drawMonthlyLmpChart` | `rt_mon` w:2, `da_mon` w:3 | display | RT-eq✗ | **REPAIRED** |
| 19 | Run Explorer `lmpMonthlyTable` | DA columns first, equal-hour | display | RT-eq✗ | **REPAIRED** |
| 20 | `calibration-status.js` | renders scorer `metric` strings verbatim | display | RT✓ | — |
| 21 | `status/shared.js` rubric "source" rows | names `avgLMP.rt` / `.rt_mon` | display | RT-eq✗ | **REPAIRED** |
| 22 | `docs/rubric-v2-benchmark-memo-2026-07.md` §4(b)/(c) + §4 table | *"Gates the **DA-expressible tail**… The RT count is a report-only companion"* | doc **cited by the dashboard** | **DA✗** | **ANNOTATED SUPERSEDED** |

`status/CAISO.js` carries 8 `vs RT` strings (the gated C3a records) and 12 `vs DA` strings —
**all twelve** on `key: "da_diagnostic"` rows with status `SKIPPED`. Correct by construction.

### 2.1 The one that mattered most — the memo says the opposite of the rubric (#22)

`docs/rubric-v2-benchmark-memo-2026-07.md` §4(c) states that C3c **gates the DA tail** and that
"the RT count is a report-only companion." That was true of rubric **v2** (2026-07-06). It was
**inverted by v2.7** (owner amendment 2026-07-16, "RT-everywhere") and the memo was never
updated — eleven rubric revisions ago. The memo is not obscure: `status/shared.js`'s benchmark
table cites it by name ("Sources and evidence grades: docs/rubric-v2-benchmark-memo-2026-07.md"),
so a reader who follows the dashboard's own citation to check CAISO's tail basis lands on a
paragraph that tells them it is day-ahead.

Repaired by annotation in place, not rewrite: a READ-THIS-FIRST box in the header, a superseded
box on §4(c), an inline flag on §4(b), and a flag in the §4 comparison-table cell. The v2 text
stays readable as lineage (the repo's own convention for a superseded decision).

### 2.2 The DA fill, quantified (#10–#13) — and whether it matters

`_actual_lmp_hourly` / `_actual_rt_padded` filled an RT-NaN hour with that hour's **day-ahead**
price, on the stated rationale that it "mirrors the rt→da fallback in `_actual_avg_lmp` / C3a."
That rationale is wrong in kind: C3a's ladder falls back to the DA series *as a whole* and then
**labels the record `vs DA`**, so the basis is always declared. This fill spliced DA hours into a
series the payload then calls `actual`, with nothing recording that it had.

Measured over **every** committed ISO-year in the repo, the fill changed a tail count in
**exactly one**:

| ISO-year | RT-NaN h | DA-filled h | pure-RT > thr | DA-filled > thr |
|---|---|---|---|---|
| **CAISO 2023** | 48 | 48 | **47** | **62** |
| MISO 2021 | 1 | 1 | 48 | 48 |
| MISO 2022 | 1,200 | 672 | 116 | 116 |
| NYISO 2025 | 2 | 2 | 42 | 42 |
| SPP 2024 | 12 | 6 | 59 | 59 |

CAISO 2023's 48 RT-NaN hours are **two whole days** — Jan 4 and Jan 11 — filled from DA at a mean
of **$187.22**, of which **15 exceed $200**. Hence 47 → 62.

**Does it matter? For the determination, no — and the reason is worth stating plainly rather than
waved at.** C3c's gated actual comes from `tail/actual_tail.json`, which `derive_actual_tail.py`
builds with `np.nansum(rt > thr)` straight off the pure `rt` column — **no fill**. And
`ordc.hoursGt200.actual` is read by **nothing**: an exhaustive grep finds the scorer reading only
`.model` / `.overlay`, and the dashboard JS reading neither. So the 62 was a DA-contaminated
number sitting in a keeper's committed payload under the label `actual`, seen by no gate and no
chart. That is a **trap for the next session**, not a scoring error — and it is repaired at the
source rather than left to be rediscovered.

Two live consequences of the fill did exist, both small and both now fixed at the same seam:

* **D-A diurnal amplitude (#6).** `score_diurnal_amplitude` reconstructs the model profile as
  `hod(rt_hod part) + hod(lmpDeltaHr)`, and its docstring asserts the two missing-hour masks
  "coincide." With the fill they did not: the committed `rt_hod` part drops Jan 4 and Jan 11
  (`rt_days` 363) while the delta carried values there (365 days). CAISO 2023 therefore reported
  **72.5 %** where the like-for-like number is **72.9 %** — a **0.4 pp** error on a measurement
  that is REPORTED-ONLY and BAND-FREE, so it moves nothing. 2022/2024/2025 are unaffected
  (0.0 pp). Removing the fill makes the docstring's invariant true.
* **LMP delta heatmap.** 48 of 8,760 cells were model−DA; they now read NaN (neutral).

**Already-committed payloads keep the old numbers** until their next natural re-render — no
bundle was re-rendered here (that is a solve-path artifact regeneration across every ISO, far
outside a basis audit). Nothing reads the changed field, so nothing is stale that anyone sees.
**Cross-ISO consequence, stated rather than hidden:** the next render of any run in MISO 2022,
MISO 2021, NYISO 2025 or SPP 2024 will also drop the fill. Their tail counts do not move (table
above); their `lmpDeltaHr` gains sentinels in the formerly-filled hours, which *repairs* the same
D-A calendar mismatch in those ISOs. No gate in any ISO reads either field.

### 2.3 The equal-hour / load-weighted mismatch (#16, #18, #19, #21)

C3a and C3b gate the **load-weighted** actual (`rt_lw`, `rt_lw_mon`) — the hub series weighted by
the same measured demand the model dispatches. Every monthly chart and table plotted the
**legacy equal-hour** `rt_mon` / `da_mon` against a model series that *is* demand-weighted. Two
different statistics on one chart, and neither pair is the pair C3b scores. For CAISO 2022 the
annual gap between the two actual bases is **$5.42/MWh** (rt 79.07 vs rt_lw 84.49) — larger than
several of the residuals those charts are read to judge.

A new `actualMonGated(yr)` helper mirrors `score_price_shape`'s ladder
(`rt_lw_mon > da_lw_mon > rt_mon > da_mon`) and now feeds all three views, which additionally
**lead with RT**: the gated RT series is the heavy line / first column, DA the thin dashed
companion / second column, labelled `(gated)` and `(diag)`. Previously DA was drawn at `w:3`
over RT at `w:2` and tabled first — the never-gated series given the visual weight.

`status/shared.js`'s rubric rows named `avgLMP.rt` / `avgLMP.rt_mon` as the C3a/C3b source; they
now name `avgLMP.rt_lw` / `avgLMP.rt_lw_mon` with the full fallback ladder, so a reader checking
the published number against the named field gets the published number.

### 2.4 Two smaller things found on the way

* **`RT coverage 100% — count is a lower bound`.** The C3c coverage note fires below 99.9 % but
  formatted at `.0%`, so every partial year in the 99.5–99.9 band printed a self-contradiction.
  CAISO 2023 (0.995) now correctly reads **99.5 %**; SPP (0.999) is likewise unstuck.
* **`status/CAISO.js` was two rubric revisions stale** — built at `rubric_version` 3.7, missing
  v3.8's `price_reference_blocked_years` field. Rebuilding it here catches that up. The
  determination is unchanged (`CALIBRATED`). Unrelated pre-existing staleness, surfaced because
  this session had to rebuild the part anyway.
* **Not repaired, deliberately:** `check_bench_freshness` reports all four CAISO bench parts
  stale against the builder at HEAD (payload fingerprint `7c262e068a96`). Pre-existing, unrelated
  to price basis, and regenerating a bench part is bundle work, not audit work. Named for the
  next CAISO lane.

---

## 3. What was repaired, file by file

| File | Change |
|---|---|
| `docs/rubric-v2-benchmark-memo-2026-07.md` | superseded annotations on §4(b), §4(c), the §4 table cell, and a header box (rule 26 — annotated, not rewritten) |
| `scripts/render_calibration_html.py` | `_actual_lmp_hourly` / `_actual_rt_padded`: **DA fill removed**, RT-NaN stays NaN |
| `scripts/calibration_verdict.py` | C3c coverage note `.0%` → `.1%` |
| `scripts/build_status.py` | C3a/C3b rubric "source" rows name the gated `*_lw` fields |
| `docs/codebase-site/js/backcast-runs.js` | `drawPriceDuration` **deleted** (dead, DA-only, rule 26); new `actualMonGated`; RT leads in both charts and the monthly table |
| `tests/scoring/test_tail_metric_payload.py` | two tests **reversed** — they asserted the DA fill |
| `frontend/data/backcast/status/{CAISO,shared}.js` | rebuilt (`build_status.py --iso CAISO`) |

**Nothing in the solve path was touched** — no `src/market_sim/`, no LP, no offer curve, no
threshold, no band, no `ScenarioConfig` field. Rule 28: **no mechanism cell moved**, because no
mechanism was tested.

### 3.1 Verification

* Both keeper runs re-scored at HEAD after every edit: **CALIBRATED** / **NOT-YET**, unchanged,
  same magnitudes.
* `tests/scoring/` full sweep: **12 failures on clean `main`, 12 failures with these changes** —
  a byte-for-byte identical set, plus the 2 tests updated above, which now pass. The 12 are
  pre-existing (`test_forecast_parity`, `test_gate_a_provenance`,
  `test_golden_manifest_provenance`, `test_replay_keeper_strict`,
  `test_audit_keepers_lineage::test_e11_set_mirrors_replay_ignore`) and were confirmed by
  `git stash` baseline, not assumed. **None is in this lane's scope and none is touched here.**
* `node --check` on the edited JS; `py_compile` on all three edited Python files.
* `_actual_lmp_hourly('CAISO', 2023)` now returns 48 NaN and **47** hours > $200 — exactly the
  gated count.

---

## 4. The honest answer to the question that was asked

**The keeper was already scored against RT LMP, and it still is.** No number on the Calibration
Status page, in either keeper's verdict, or in any determination changed as a result of this
audit — and the right conclusion from that is that caiso-282 was right, not that the second ask
was wasted. What the second ask bought is the five surfaces above, which a check confined to the
scorer could not have found: a benchmark memo telling readers the tail gates on DA, a dead
DA-only chart, a DA-filled "actual" in a committed keeper payload, and three monthly views
plotting a different statistic from the one they are read as.

**What this audit does NOT establish:** that CAISO's price residual is small. C3a-2022 still
fails at +11.3 % against RT, and C3a runs +3.2 / +8.4 / +7.7 % in the training years — all inside
the ±10 % band, all one-signed. Being on the right benchmark is a precondition for that number
meaning anything; it is not evidence about the number.

---

## 5. Successor

Nothing in Job A opens a lever. The C3a/C3c objects are unchanged and still point where
caiso-275 and caiso-283 left them: **CAISO commitment / clearing**, not any offer. Job B takes
that up under its own PRECOMMIT.
