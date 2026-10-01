# PRECOMMIT — the forward-expectation entry signal, its A/B and its predictions

_2026-08-25 · ENTRY-SIGNAL LANE (charter: the rung named by
`docs/FINDING-entry-signal-disarm-2026-08.md` §6; root object
`docs/FINDING-entry-screen-t1h-2026-08.md` §6 D-8, §7 L-1/L-1b). **Committed
BEFORE any solve of the treatment arm exists** — the predictions below are
pre-registered against bundles that have not been produced. The mechanism
itself (`entry_forward_expectation_signal`, GATED default-OFF) landed one
commit earlier with its matrix row and unit tests._

---

## 1. The construction under test (fixed by the prior commit; zero DOF)

`signal[z,t] = econ_prices[z,t] + (S_entering[t] − S_current[t])`

- `econ_prices` — the run's own prior-year hourly **zonal** LP dual surface
  plus the same post-solve ORDC overlay the disarm fallback reads: locational
  congestion, real intraday shape, realized scarcity.
- `S(·)` — the **existing** lookahead stack instrument
  (`runner._lookahead_reprice_signal`) evaluated twice at identical settings
  (same merit stack, same FFR-5D level repairs, same FFR-8A tail):
  `S_entering` exactly as shipped (entering-year demand + committed pipeline
  under `entry_pipeline_aware_signal`); `S_current` at the current year's own
  dispatched demand with **no** pipeline terms. The hourly delta is the
  stack's own forward view of exactly what changes between the two years —
  load growth, committed fleet, ORDC curve vintage — and nothing else.

This is a **replacement** of the reprice's zone-flat MC-step object (rule 19
`[R-ONE-MECH]`), not a correction stacked on it; `entry_lookahead_reprice`
stays `True`. **No elasticity, damping or scaling coefficient exists anywhere
in the construction** (rule 21 `[R-DOF]`): both terms are objects the model
already produces and the composition is exact arithmetic. Two design choices
are fixed here so they cannot drift post-hoc:

1. **Additive re-level, hourly.** The delta is applied per hour, zone-uniform
   (a multiplicative form would explode on near-zero dual hours and is not a
   re-*level*). The duals' cross-zone structure survives exactly.
2. **`S_current` baseline = the year's own dispatched demand, no pipeline.**
   The committed pipeline is part of what *changes* between the two years, so
   it belongs to the delta, not the baseline; every instrument setting that
   does not change between the years (VRE potential basis, storage shave,
   tail) is identical in both evaluations.

## 2. The A/B protocol (single delta)

- **Treatment** (`results/hindcast/ercot-2021-2025-realized-t1h-fwdexp`):
  `uv run python scripts/run_capacity_hindcast.py --iso ERCOT --start-year
  2021 --end-year 2025 --entry-forward-expectation-signal --out-dir …` — the
  registered t1h posture (bare invocation inherits the shipped ERCOT
  defaults: unified lookahead, scarcity restoration, pipeline-aware signal,
  reprice ON) plus **exactly one** non-default field.
- **Same-tree control**
  (`results/hindcast/ercot-2021-2025-realized-t1h-fwdexp-control`): the bare
  invocation re-solved from this HEAD. It exists because HEAD has moved since
  the committed brackets were solved (2026-08-24; notably ercot-234's EASTEX
  static GTC 1,300 → 2,300 MW crosswalk repair, which plausibly moves ERCOT
  hindcast dispatch). **Pre-registered handling:** the single-delta
  comparison is treatment vs the same-tree control; the committed brackets
  (`…-t1h-control`, key `28cef3500ec1fd9e`; `…-t1h-disarm`, key
  `2eab21467a4214c7`; ledger evidence
  `results/calibration/entry_signal_disarm_ledger_ercot.json`) are the
  registered anchors, and any drift of the same-tree control from the
  committed control is **reported at full magnitude, never chased** (the
  disarm finding §5.2 pattern). If the same-tree control reproduces the
  committed control's score exactly, the committed brackets stand unmodified.
- **Span:** 2021 seed + 2023–2025 solved, 2022 bridged — the registered
  window; no year outside it, no holdout marker touched (rule 22).
- **Years sequential within each invocation; at most the two invocations run
  concurrently** (rule 12).
- **Scoring:** `scripts/score_capacity_hindcast.py --bundle <each>`; then the
  ledger-compare probe (the disarm pattern) emits
  `results/calibration/entry_signal_fwd_expectation_ercot.json`.

## 3. Pre-registered predictions

Scored against the treatment's evolution ledgers and score.json, with the
committed disarm/control rows as the brackets. Thresholds are fixed **now**:

- **P1 — the disarm's storage repair reproduces.** Storage entry is decided
  in **≥ 3 of the 4** decision steps (ledger years 2022/2023/2024/2025) with
  a long-duration tech leading, and the shipped one-shot pattern (**all**
  storage in the 2023 step alone) does **not** recur. (Brackets: control =
  5.0 GW all in 2023; disarm = iron_air 3,000 MW in every step.)
- **P2 — wind economic entry appears.** Decided wind > 0 MW in ≥ 1 step
  (control: zero in every step; disarm: 1,092.2 MW in 2022).
- **P3 — the +15 pp terminal-RM overshoot does NOT reproduce.** The
  forward view (the screens see the entering year's own stack move, including
  their own committed pipeline) damps the rebound the backward-looking duals
  amplified. Thresholds on the ledger-2025 reserve margin (brackets: control
  25.19 %, disarm 40.24 %):
  - **CONFIRMED** if terminal RM ≤ **30.2 %** (control + 5 pp);
  - **OVERSHOOT SURVIVES** if terminal RM ≥ **35.2 %** (disarm − 5 pp);
  - **BORDERLINE** in between → **escalate to the owner** (charter), no
    unilateral adjudication.

**Pre-registered fallback (P3 fails):** if the overshoot survives a
forward-looking locational signal, the expectation model is exonerated and
**D-1's bang-bang volume rule owns the overshoot** — L-1b's zero-DOF
candidate (build until the screen's own repriced margin is exhausted, never a
tuned damping coefficient). That outcome is **a finding, not a failure**, and
is written up as such.

## 4. Pre-registered cell adjudication rule

The `entry_forward_expectation_signal` row's ERCOT cell (currently `O`/`O`)
updates in-session with the evidence citation (rule 26 duty b), under this
direction-blind rule:

- **`R` (rejected)** only if P1 **and** P2 both fail — the construction loses
  the locational repairs the disarm measured — or the composed signal is
  degenerate (e.g. unbounded deltas, NaNs).
- **Otherwise the cell stays `O`** with the measured evidence recorded.
  **This lane does not self-promote**: arming the construction as the lane
  default is the owner's decision (exactly the disarm's posture), and a
  mixed/borderline verdict escalates to the owner rather than being
  adjudicated here.
- Bands and RM trajectories are **attached evidence, never the verdict**
  (rule 1 `[R-STRUCT]`) — reported at full magnitude in both directions.

## 5. Out of scope, pre-declared

No `as_revenue_enabled` arming (a separate later composition, both ISOs); no
CAISO solve (CAISO enters as `U`, rule 25); no elasticity/damping parameter
under any outcome (rule 21); `entry_vre_capacity_revenue` / `entry_dampers`
ERCOT cells stay closed (`I`/`I` — DO-NOT-REDO);
`results/calibration/caiso217_crosswalk` untouched; no new CI workflows.
