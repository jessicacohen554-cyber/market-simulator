# PRECOMMIT — ercot-193: the standing ercot-167 SOC-reserve re-gate, discharged at HEAD

**Pushed BEFORE any solve. Session ercot-193, 2026-08-13, HEAD `e87647e`
(branch `claude/ercot-193-c3b-ceiling-2xu9lg`).** Scope: ERCOT only (rule 25).
Years {2023, 2024, 2025} only (rule 22; ERCOT holds no `complete`/`final` marker).

## 0. Object, and the queue position

**The object is the STANDING RE-GATE EXPECTATION on record since ercot-167** (its
FINDING §reopen, quoted in matrix §5.1 item 10 and in every keeper stamp since):
*"re-gate the IDENTICAL arm (no parameter exists to change) after the 2024
maintenance-season availability defect (FINDING-ercot166 §5 / handoff H4 item 4)
lands."* This session discharges it: a fresh same-HEAD A/B of
`ercot_storage_as_soc_reserve` (disarmed control vs the keeper recipe), scored on
the ORIGINAL ercot-167 gates verbatim.

Queue adjudication (handoff starting points, in order):
- **(a) TAKEN — this precommit.** The maintenance-season root's remaining
  *buildable* faces are frozen or closed (fault 1 / composition lane FROZEN by the
  signed D2 ruling — not touched here; fault 2 unit-scoping stopped at ercot-174;
  fault 3 REPAIRED and PROMOTED at ercot-185). What the lane still owes is exactly
  the re-gate the record has carried since 2026-08-05.
- **(b) REFUSED — `diurnal_price_amplitude`.** The row is a CROSS-ISO AUDIT ROW
  ("defect not mechanism"); ERCOT's named ISO-local lever for the xiso-1 evening
  amplitude was item 10 — the SOC reservation, already armed in the keeper. C3b is
  a MONTHLY NRMSE, and card R (`docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md`)
  measures the best case of any non-Aug/Sep-2023 lever at NRMSE ≈ 0.592 vs the
  0.20 bar. No new identification exists to test; the cell stays `U`.
- **(c) REFUSED for this round — the outage-season/fuel-shape monthly object.**
  Its named residual patterns (2024 shoulder −/summer +; 2025 worst Apr–May) are
  the two YEARS WHOSE C3b PASSES (0.135 / 0.096). It does not touch the failing
  criterion and is 2024/2025 shape work for a later charter.

**Honesty about the target:** per card R, C3b-2023 (NRMSE 0.604) is 96.2 %
Aug+Sep 2023 — the Q-B-closed model-class scarcity object. This A/B will move
C3b-2023 only marginally and is NOT expected to flip it; the promotion rule (§4)
reads gates, never residual direction. The deliverable is the re-gate record.

## 1. Reopen-condition status, stated before the measurement

The ercot-172-specified corrections C1/C2 never landed as specified (C1+C2 built
as the blanket reconciliation and REJECTED at ercot-173; unit-scoped stopped at
ercot-174; the composition lane then FROZEN by owner ruling D2). What HAS landed
in the keeper chain since the kills fired:
- **ercot-185** (PROMOTED): the fault-3 shaped-partial repair — adjudicated at
  ercot-174 as *"the only remaining structural route to the 2024 object"*.
- **ercot-191** (PROMOTED): the A1 DAM-deriver repairs (#9 train-grain collapse,
  #8 multi-year rating basis, #10 pin coverage guard).
Measured state vs the ercot-167 kill context: 2024 shed hours 2 → 1; C3a-2024
+9.0 % (control of the era) → **−0.8 % PASS**; April/May 2024 monthly residual now
+6.2 / +5.5 $/MWh (April was "+72 % over" then). If the owner reads the reopen
condition as strictly "ercot-172's own C1/C2 land", this re-gate is early — in
that reading the record below is still a valid same-HEAD A/B measurement and
changes nothing (§4: the keeper cannot change here in any outcome).

## 2. Identification (rule 23) — zero new DOF

Unchanged and inherited whole from PRECOMMIT-ercot167 §0–§1: measured 60-Day AS
awards × published per-product durations, deployment-netted,
pin-reachability-clipped (amendments 1–2 included). **No derive is re-run, no
scalar is added or changed, no parameter exists to change** — the arm is the
committed flag `ercot_storage_as_soc_reserve` exactly as armed in the keeper.
`free_parameters_added = 0`; `n_residual` must read 6 unchanged (G-DOF).

## 3. The runs (rule 12: years sequential, ONE invocation at a time — 15 GB box, ~12.7 GB peak)

1. **Run B — arm (first): byte-faithful keeper replay at HEAD**
   `python scripts/replay_keeper.py results/calibration/ercot192_arm_B
   --out-dir results/calibration/ercot193_arm_soc --years 2023 2024 2025
   --note "ercot-193 SOC re-gate arm: run192 keeper recipe replayed at HEAD"`
   — doubles as the keeper-reproduction check (G-REPRO disclosure).
2. **Run A — control: single-delta disarm**
   `python scripts/replay_keeper.py results/calibration/ercot192_arm_B
   --set ercot_storage_as_soc_reserve=false
   --out-dir results/calibration/ercot193_ctl_nosoc --years 2023 2024 2025
   --note "ercot-193 SOC re-gate control: keeper recipe minus the SOC reservation"`
   — the exact inverse of the ercot-167 single delta (armed on the ercot-165
   recipe), so A→B here is the same comparison at HEAD.

**Both runs are registered on the dashboard whatever the outcome** (rule 15), as
`2026-08-13-ercot193-ctl-nosoc` and `2026-08-13-ercot193-arm-soc`. Retention: the
15-cap evicts the two oldest registered ERCOT runs
(`2026-08-05-run168b-year-curves`, `2026-08-06-run173a-reconc-control`; neither is
the keeper). Mechanism liveness is verified before scoring (the arm's SOC
reservation engaged; the control's absent).

## 4. Pre-registered gates and the DIRECTION-BLIND rule (no post-hoc softening)

**The ORIGINAL ercot-167 §3 gates, VERBATIM, read A→B** (A = disarmed control,
B = arm — same direction as 2026-08-05): **G1** (target, 2023 scarcity-hour
battery discharge toward the measured 423 MW), **G2** (KILL — 2025 net-discharge ÷
EIA-930 NG:BAT ≥ 0.70 on B), **G3** (KILL — spurious tail hours must not increase
A→B, per year), **G4** (KILL — C1/C2/C4/C8 hold PASS in B; C3a/C3b 2024 and 2025
within ±1.0 pp / ±0.02 NRMSE of A; no new failing D-1 rows), **G5** (KILL — shed
hours with slack > 1 MW must not increase A→B in any year). The two kills that
fired in 2026-08-05 map to G4-2024 and G3-2025; the re-gate verdict is
**RG-PASS iff G2, G3, G4, G5 all hold** (G1 is the target report, as originally).

**Carried live in addition (D2 lineage):** **G-COAL148** — coal dispatch above
the incumbent product ceiling may not RISE more than 0.5 TWh in any year A→B;
scored by the committed `scripts/probes/ercot185_coal148.py` on the pair.
**G-DOF** — `n_residual` 6 unchanged, zero new scalars. **G-REPRO (report, not a
kill)** — B's metrics vs the committed run192 bundle; any drift is the
nyiso-128 K6-class condition, disclosed at full magnitude (the A/B itself is
same-HEAD valid either way, the ercot-150 K2 lesson). **Report-only:** C3a / C3b
/ C3c per year at full magnitude; the A→B C3b-2023 monthly delta through
`scripts/probes/ercot193_c3b_decomposition.py` on both registered payloads (card R
input); the G1 storage HOD shift.

**THE DIRECTION-BLIND RULE — the keeper CANNOT change in this session, in any
outcome.** The arm is already armed in the keeper by the ercot-167 OWNER
promotion; disarming a keeper mechanism is owner-only, and B is a byte-faithful
replay, not a new recipe. The rule reads gate booleans only:
- **RG-PASS** (G2+G3+G4+G5 all hold): the standing re-gate expectation is
  **DISCHARGED** — recorded on the `ercot_storage_as_soc_reserve` cell (stays
  `K`, evidence updated), the §5.1 item-10 block, and the calibration log. Keeper
  id unchanged.
- **RG-FAIL** (any of G2/G3/G4/G5 fires): recorded at FULL magnitude and
  **ESCALATED as an open owner ruling** (the ercot-167 promotion's standing
  premise — promotion taken over fired kills expecting this re-gate to clear).
  Keeper id unchanged pending the owner. No in-session disarm, no softening.
- **STOP rules:** solver infeasibility or OOM in either run → stop, report,
  register whatever completed bundles exist per rule 15. A B-replay whose
  determination differs from the committed keeper's is disclosed under G-REPRO
  and does NOT stop the A/B.

## 5. Fences

Not C3a-2023 spend (card Q ruling Q-B final; residual moves reported, never the
basis — the object is the standing obligation). No C3c ledger change, no rubric
amendment (`LEDGERABLE_CRITERIA`, `MAX_LEDGERED_CAVEATS`, the v3.0 tier guard
byte-unchanged), no holdout marker granted or spent. The frozen composition lane
(fault 1 / double-count) is NOT touched. The ercot-188/E2 P0 bit-identity
forfeiture is inherited unexpired — every A→B difference is read at P1 scoring
grain, as every session since ercot-188 has. DO-NOT-REDO honored: no offer-price
transplant, no aggregate cap, no per-hour telemetered-HSL cap, no re-test of any
`R`/`I`/`G` cell.
