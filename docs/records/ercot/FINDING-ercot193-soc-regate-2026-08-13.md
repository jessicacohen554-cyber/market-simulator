# FINDING — ercot-193: the standing ercot-167 SOC-reserve re-gate, discharged — RG-PASS on every gate; both originally-fired kills CLEAR; the keeper reproduces BYTE-IDENTICALLY at HEAD

Session ercot-193, 2026-08-13. Precommit
`docs/PRECOMMIT-ercot193-soc-regate-2026-08-13.md`, pushed at `5ad4975` BEFORE any
solve. Runs `2026-08-13-ercot193-ctl-nosoc` (A, keeper recipe minus
`ercot_storage_as_soc_reserve`) and `2026-08-13-ercot193-arm-soc` (B, the run192
keeper recipe replayed byte-faithfully), both registered (rule 15), full span
2023–2025, years sequential, one invocation at a time (rule 12). Keeper
**UNCHANGED** at `2026-08-12-run192-arm-coal-peak` — the §4 direction-blind rule
forecloses any in-session keeper change, and none was made. Scored artifacts:
`ercot193_ab_gates.json` (G1–G5, G-REPRO, full-magnitude C3), `ercot193_coal148.json`
(G-COAL148 via the committed `ercot185_coal148.py`).

## 1. Verdict — RG-PASS; the standing expectation is DISCHARGED

The re-gate ercot-167 pre-registered as its own reopen condition (*"re-gate the
IDENTICAL arm — no parameter exists to change — after the 2024 maintenance-season
availability defect lands"*) has now been run, on the original §3 gates verbatim,
and **every kill holds**:

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| G1 target (2023): battery discharge in the 61 actual >$1000 h | 663.7 → **516.1 MW** (actual 423; 61.3 % of gap closed, no overshoot) | — | — | **PASS** |
| G2 KILL: 930 NG:BAT volume ratio (arm) | n/a | 1,707.5 GWh (report) | **0.72** (≥ 0.70) | **PASS** |
| G3 KILL: spurious tail hours A→B | 2 → 2 | **6 → 5** | **1 → 1** | **PASS** |
| G4 KILL: C1/C2/C4/C8 hold; C3a/C3b 2024–25 bands | — | C3a Δ **0.989 pp** (≤ 1.0); C3b Δ 0.004 | C3a Δ 0.607 pp; C3b Δ 0.006 | **PASS** |
| G5 KILL: shed hours A→B | 4 → 4 | 1 → 1 | 0 → 0 | **PASS** |
| G-COAL148 (live, D2 lineage) | rise −0.003 TWh | −0.000 | −0.0003 | **PASS** (bar 0.5) |

**Both kills that fired on 2026-08-05 now clear, exactly as the reopen condition
predicted they would once the maintenance-season defect landed:**

- **RG-1 / G4-2024**: at ercot-167 the arm added +1.4 pp to a control already
  +9.0 % over (the lift concentrated on the Apr 28 / May 8 / Nov 9 fabricated-spike
  days, April +72 % over in control). After the chain that landed in the keeper —
  ercot-185's fault-3 shaped-partial repair (ercot-174: *"the only remaining
  structural route to the 2024 object"*) and ercot-191's A1 deriver repairs — the
  control sits at **−1.81 %** and the arm at **−0.81 % (PASS)**: the arm's 2024
  price motion is now toward actual, and 2024 spurious hours FALL on the arm
  (6 → 5). Knife-edge disclosed, not hidden: the 2024 C3a delta is **0.989 pp on
  the scorer's exact (unrounded) basis** — the 2-decimal display values round it
  to a spurious 1.000; the gate is adjudicated on the exact basis, and the margin
  is thin either way.
- **G3-2025**: at ercot-167 the arm introduced one spurious hour (2025-10-21 19h,
  a $43 graze). At HEAD it introduces **none** (1 → 1; the graze hour is present
  in BOTH arms of the pair, i.e. it belongs to the surrounding recipe, not to this
  mechanism).

Under the precommit's direction-blind rule, RG-PASS means exactly one thing: the
standing expectation carried on the cell, the item-10 block, and every keeper
stamp since 2026-08-05 is **discharged** — the owner promotion that carried the
arm over its fired kills is now backed by a clean gate record. No keeper change
follows (none is available to this session), and no residual was the basis.

## 2. G-REPRO — the keeper reproduces BYTE-IDENTICALLY at HEAD

The arm replay doubles as the keeper-reproduction check, and it is exact at every
grain measured: **zero drift** on all scored C3a/C3b/C3c values in all three
years, determination identical (NOT-YET {C3a-2023, C3b-2023}, C3c ledgered ×3 at
58/22/1), and **all 12 committed hourly sidecars sha256-IDENTICAL** to
`ercot192_arm_B` (class_hourly / reserve_family / storage / system × 3 years).
The nyiso-128 K6-class non-reproduction condition that has dogged ERCOT controls
since ercot-173 (run168b drift, disclosed again at ercot-176) is **not present**
for this keeper at this HEAD. The mid-session merges to the branch (card-R
signing, L-SCAR charter record, the stage-B epoch declaration #3903) were
comment/docs/test-only on the solve path — verified by diff before the control
launched — and `ercot_storage_as_soc_reserve` is not among the five stage-B
override-table flags, so the FINDING-ffr-9c override-precedence defect does not
touch this pair (empirically confirmed: the control log carries zero SOC
reservation lines; the arm carries one per year).

## 3. What the mechanism is now measured to carry (full magnitude, never the basis)

Card R (SIGNED R-A, 2026-08-13) requires any C3b-2023 side-effect reported with
the ceiling stated up front: **C3b-2023 cannot pass within this model class**
(~0.59 floor without re-opening the Q-B-closed Aug/Sep object; both sides of this
A/B remain ~96 % Aug+Sep in squared residual). Within that ceiling, disarming the
SOC reservation shows what the armed mechanism carries in the keeper:

| | control (disarmed) | arm (keeper) | the mechanism carries |
|---|---|---|---|
| C3a-2023 | −33.56 % | −33.20 % | +0.36 pp toward actual |
| C3b-2023 | 0.611 | 0.604 | −0.007 NRMSE |
| C3c-2023 tail | 50 h | 58 h | +8 real tail hours (vs actual 181) |
| C3a-2024 | −1.81 % | −0.81 % | +1.0 pp toward actual, spurious 6→5 |
| C3a-2025 | −8.09 % | −7.49 % | +0.6 pp toward actual |
| 2023 scarcity-hour battery discharge | 663.7 MW | 516.1 MW | 61 % of the gap to the measured 423 MW |

Every row moves toward the measured market, in all three years, with zero fitted
scalars — the profile of a real mechanism (rule 1), and the strongest evidence to
date that the ercot-167 owner promotion was structurally correct.

## 4. Bookkeeping

- OOM disclosure: the first control launch was OOM-killed mid-2023 (dmesg: pid
  4170, ~8.6 GB RSS) — an environmental collision with a concurrent `git push`
  pack build, not a solve defect; relaunched solo and completed cleanly. Per the
  precommit STOP rule the interruption is reported; no artifact from the killed
  attempt survives (the bundle was rebuilt from scratch).
- The `dashboard_add_run` metrics-sidecar path bug (relative-vs-absolute) was
  worked around by writing the sidecar directly with
  `calibration_verdict.write_metrics_sidecar` on the resolved path; both runs'
  determinations printed and recorded (NOT-YET {C3a-2023, C3b-2023} both — the
  control loses no criterion, the fail set is recipe-level).
- `legitimacy_diagnostics.json` generated for both bundles (the replay does not
  write it; C8 scores from it and reads PASS on both).
- Retention: registering the pair evicted `2026-08-05-run168b-year-curves` and
  `2026-08-06-run173a-reconc-control` (top-15, as pre-registered; neither was the
  keeper).
- Attestations: both bundles carry the keeper's attestation deep-copied
  (`scripts/gen_ercot193_attestation.py`) — ledger unchanged by construction
  (n_entries 18, n_residual 6), C3c magnitudes re-measured on each bundle's own
  sidecars on the scorer's max-zonal basis (arm 58/22/1, control 50/17/1).
- The sibling defect fix this session: `gen_ercot188_attestation.py::_tail_counts`
  re-pointed from demand-weighted to the scorer's max-zonal basis (the
  ercot-192-filed defect), verified to reproduce the keeper's 58/22/1.
- Fences honoured: no C3a-2023 spend (the object was the standing obligation;
  residuals reported, never gated on direction), no C3c ledger change, no rubric
  amendment, no marker granted or spent, the frozen composition lane untouched,
  the ercot-188/E2 P0 bit-identity forfeiture inherited unexpired (this A/B is
  read at P1 scoring grain throughout).

## 5. Successor state

With the re-gate discharged, the ercot-167 lane is CLOSED-CLEAN: the arm is
armed in the keeper, owner-promoted, and now gate-clean on its own original kill
set. Under signed card R (R-A), ERCOT bandwidth goes to hygiene, the 2024/2025
shape queue, and forecast readiness. The one item this record newly informs: the
DECISION-MEMO §5 sequel question (whether removing the fault-1 double-count
against the REPAIRED partial layer still floods) remains owner-gated —
G-COAL148's headroom here (rise ≈ 0.0 of the 0.5 TWh bar on this pair) is
consistent with ercot-185's evidence but is NOT a charter to open the frozen
composition lane.
