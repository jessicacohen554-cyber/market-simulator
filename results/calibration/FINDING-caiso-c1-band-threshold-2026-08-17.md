# FINDING — CAISO C1 band threshold: the 2023 CC_REGULAR row, and whether it is a C3a symptom

**Session** `claude/caiso-gate-c1-threshold-kf3c3q` · 2026-08-17 · scorer-only, **no LP solve**
**Scored at** `f087c67` (rubric v3.3) · re-verified after rebase; the v3.2→v3.3 amendment does not
touch the C1 bands and every number below is identical before and after.

Owner question: CAISO's keeper fails C1 on one row at −4.24 TWh / −1.8 pp when the rubric standard
reads "8 TWh and 3 pp" — is it failing only because it is 0.09 off, and is that an acceptable caveat?

## 1. Why the row fails — the 8 TWh is a CAP, not the band

`scripts/calibration_verdict.py:1047`:

```python
vol_band = min(FUELMIX_VOL_LOAD_FRAC * total_load, FUELMIX_VOL_CAP_TWH)   # 0.02, 8.0
```

The absolute 8 TWh ceiling binds only above 400 TWh of load (ERCOT, MISO, PJM). CAISO's 2023 load is
207.404 TWh, so its band is **±4.148 TWh**, and the row misses by **0.0955 TWh — 2.3 % past the line**.

**The share leg is not what fails.** −1.75 pp against ±3.0 pp passes with 1.25 pp to spare; the
scorer's own breach label reads `(volume out of band)`, not `volume/share`. A widening of the share
band alone is therefore a no-op for this row.

| year | band | CC_REGULAR miss | vs band | share | C1 |
|---|---|---|---|---|---|
| 2023 | ±4.148 | **−4.244** | **+0.0955 over (102.2 %)** | −1.75 pp | **FAIL** |
| 2024 | ±4.244 | −1.340 | 2.90 under (31.6 %) | −0.66 pp | PASS |
| 2025 | ±4.112 | −2.463 | 1.65 under (59.9 %) | −1.41 pp | PASS |

## 2. Provenance of the 4.148 — derived per run-year, never stored

1. The solve writes `hourly/system_<year>.parquet` with a per-zone-hour `demand` column — the LP
   energy-balance RHS, i.e. the measured zonal load input.
2. `scripts/render_calibration_html.py:2109 → 2117 → 2152` aggregates it into the run payload:
   `dem = zg["demand"]` → `d_tot = dem.sum()` → `"d": round(d_tot / 1e6, 4)` (MWh → TWh) per zone.
3. The committed payload holds seven CAISO zone numbers for 2023 — NP15 82.2601, LA_BASIN 79.2630,
   SDGE 17.8644, SP15_rest 17.2170, ZP26 10.7995, WECC_DSW 0, WECC_PNW 0 (the two WECC entries are
   import nodes with no native load) — **summing to 207.4040**.
4. `calibration_verdict.py:1014-1017` (`_total_load`) sums exactly those.
5. `:1047` → `min(0.02 × 207.4040, 8.0)` = **4.1481**, rendered `±4.15`.

The band is **already on a demand basis**. The only persisted trace is the display `tol` string on
each scored record, recomputed every scoring pass — so a constants change re-scores every registered
bundle in place with no re-solve.

**Stability.** Measured across all 26 registered runs: every ISO-year yields exactly one band value.
The sole variation anywhere is PJM 2024 at 812.741 vs 812.742 TWh, under a binding 8.0 cap, so it
never reaches the band. "Recomputed each time" introduces no run-to-run drift.

## 3. A generation basis would TIGHTEN CAISO, not loosen it

CAISO is the most import-dependent ISO in the set — 207.404 TWh load vs 175.737 TWh generation, so
~15 % of load is imported.

| basis | CAISO 2023 band | vs the 4.243 miss |
|---|---|---|
| 2 % of **load** (current) | **4.148** | fails by 0.095 |
| 2 % of actual generation | 3.515 | fails by 0.728 |
| 3.5 % of actual generation | 6.152 | passes |

The load basis is already the generous one for CAISO, deliberately so — `calibration_verdict.py:313-316`
chose load "so net-importing ISOs get the correct ≈2 pp band; for energy-only ISOs with no
interchange, load = gen and the band is unchanged." Re-basing onto generation at the same 2 % takes
0.63 TWh **away** from CAISO. Only the third row delivers a pass, and that is a 48 % widening, not a
re-derivation.

## 4. The C1 row is NOT a symptom of the C3a miss

The proposition tested: CAISO's C1-2023 flag is spurious and the real defect is C3a. **The year
pattern refutes it.**

| year | CC_REGULAR | total gas miss | C1 | C3a mean LMP |
|---|---|---|---|---|
| 2023 | −4.244 | **−7.33 TWh** | **FAIL** | **+4.1 % PASS** |
| 2024 | −1.340 | −4.06 TWh | PASS | +12.8 % FAIL |
| 2025 | −2.463 | −4.18 TWh | PASS | +15.7 % FAIL |

(total gas = CC_REGULAR + CT_PEAKER + ST_GAS)

The two are **inversely** related. The year with by far the largest gas under-dispatch is the year
the price is nearly right; the two years carrying the price blowout have ~40 % less gas deficit. If
C1-2023 were the shadow of the C3a defect the table would slope the other way. The direction is
wrong twice over: the model is *over*-priced by 13–16 % in 2024/25 while *under*-dispatching gas —
over-import at too high a price, not CC displacement.

Independently, the keeper's own disposition already establishes the −4.24 as real: caiso-200 measured
that closing the panel-membership artifact returned only **+0.003 TWh** of it (−4.246 → −4.243),
attributing the remainder to the standing CC-side under-dispatch / over-import lane (caiso-121
surplus-belly, caiso-135 ride-through, caiso-140 §B). It is a genuine ~2.4 % shortfall on the class,
not a scoring artifact.

## 5. Blast radius of a widening, measured — not asserted

Across all 26 registered runs, **372 gated C1 rows, exactly 2 failures**:

| ISO | run | year | class | miss / band | share |
|---|---|---|---|---|---|
| PJM | `2026-08-05-pjm-2022-touchpoint` | 2022 | CC_REGULAR | +18.276 / ±8.00 = **228.5 %** | +1.57 pp |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | 2023 | CC_REGULAR | −4.243 / ±4.15 = **102.2 %** | −1.75 pp |

**The share leg has never bound.** Zero breaches in 372 rows; peak utilisation 79.0 % (NYISO 2023
ST_GAS, +2.37 pp). On 41 of 372 rows the share leg is the tighter of the two, but never tight enough
to fail. The volume leg is the only one that has ever decided a C1 row — which is the honest
justification for touching the share constant, and equally the reason touching it alone changes
nothing.

Candidate widenings, each re-scored over all 26 runs:

| candidate | CAISO 2023 | PJM 2022 | determination flips |
|---|---|---|---|
| current 2.000 % / cap 8.0 / 3.0 pp | FAIL | FAIL | — |
| A proportional ×7/6 — 2.333 % / 9.333 / 3.5 pp | PASS | FAIL | **0** |
| B share-equivalent — 3.5 % load / cap 8.0 / 3.5 pp | PASS | FAIL | **0** |
| C minimal — 2.100 % / cap 8.4 / 3.5 pp | PASS | FAIL | **0** |

Every candidate clears CAISO 2023, leaves PJM 2022's genuine +18.276 TWh structural miss correctly
failing, and **flips no determination anywhere** — CAISO included, because C3a fails it
independently. A C1 widening buys no status change for any ISO on the current dashboard.

## 6. Disposition — NO CHANGE MADE

No rubric constant was edited and no run was solved, registered or promoted in this session. The
CAISO keeper stands at `2026-08-17-caiso-200-h1-memberpanel`, determination **NOT-YET** on two
load-bearing FAILs (C1 fuel-mix, C3a mean LMP), C3c the single ledgered caveat.

Recorded for the owner's decision:

- **C1 is not ledgerable at HEAD.** Rubric v3.1 narrowed `LEDGERABLE_CRITERIA` to `{"price_tail"}`
  (`calibration_verdict.py:513`) and `_apply_ledger` fail-closes on anything else (`:873-874`); C1 is
  load-bearing, which the v3.0 guard refuses for `model-class` classification by construction.
  Ledgering this row is a rubric amendment, not a ledger entry.
- **A widening is a 3-line edit** (`calibration_verdict.py:322-324`) plus a `rubric-consts.js`
  rebuild — every other consumer derives from those constants
  (`scripts/lib/rubric_consts.py:74-76` → `frontend/data/backcast/rubric-consts.js` →
  `docs/codebase-site/js/backcast-runs.js:94-96`; `scripts/build_status.py:110-113, 298-299`;
  drift-guarded by `tests/scoring/test_rubric_consts.py:29-31`). The three probe scripts holding
  hardcoded copies (`probes/neiso94_pilgrim_vintage_audit.py:67-68`,
  `probes/_neiso81_chp_phase0.py:75-76`, `probes/pjm130_c1_ccregular_displacement.py:78-79`) are
  frozen per-run calibration records and must NOT be updated by a rubric change.
- **The rule-1 `[R-STRUCT]` hazard is live either way.** Moving a threshold after seeing which side a
  run landed on is the shape rule 1 guards against. What makes a widening defensible is §5's
  measurement — the share leg has never bound in 372 rows, so the two legs are not consistent with
  each other — and NOT the CAISO row that prompted it. What does not make it defensible is §4: the
  miss is real, and it is not the price defect wearing a different hat.
