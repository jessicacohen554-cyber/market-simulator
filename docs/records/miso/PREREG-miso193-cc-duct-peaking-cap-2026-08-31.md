# PREREG miso-193 — `cc_duct_peaking_cap_pct=8.0` single-delta A/B (2026-08-31)

Pre-registration for the miso-193 A/B, frozen and pushed BEFORE the arm leg
exists. Phase-0 rule and census: `scripts/probes/_miso193_duct_peaking_phase0.py`
(rule frozen at commit `92847a8`, census at `9a27c7a`),
`results/calibration/_miso193_duct_peaking_phase0.json`.

## 1. Premise correction (carried from phase 0)

The handoff chartered `cc_duct_peaking` as un-armed in MISO with A/B arm =
"`cc_duct_peaking` only". That premise is stale: the designated keeper
`2026-08-30-miso-191-bexit` (`results/calibration/miso191_bax_B/run_config.json`)
records `cc_duct_peaking=True`, `cc_duct_peaking_cap_pct=None`,
`cc_peaking_per_plant=True` — armed on every MISO default run since the
2026-07 G-26/C-12 generalization. NYISO's K on this row is a registration-K
(nyiso-115). The one genuinely untested single delta in MISO is the charter's
own ~8% physical cap, `cc_duct_peaking_cap_pct=8.0` (PJM-armed, None here).

Why the cap is the structurally-preferred variant and not a fit (rule 14/21):
the raw EIA-860 nameplate-vs-net-summer gap conflates the ambient summer
derate with the duct-firing increment (the field's own docstring,
`scenarios.py`; the matrix base-row note). MISO already carries the ambient
half through the armed `summer_derate_basis_aware` (miso-148), so the
uncapped band sizes the expensive tranche from a conflated quantity — a
double-count of the ambient gap in band SIZING on top of its availability
treatment. 8.0 is the F-class supplementary-firing engineering maximum, the
identical physical bound the PJM default carries
(`pipeline/backcast_config.py`), identified from engineering practice, never
from any residual.

## 2. Design

- **Control** `miso193_control_A`: `scripts/replay_keeper.py
  results/calibration/miso191_bax_B --out-dir
  results/calibration/miso193_control_A` — byte-faithful keeper replay,
  expected value-identical. Launched before this PREREG froze (it carries no
  adjudicating content of its own; the arm did not exist).
- **Arm** `miso193_cap_B`: same replay `--set cc_duct_peaking_cap_pct=8.0
  --out-dir results/calibration/miso193_cap_B`. Single delta.
- Years 2023 2024 2025, one invocation per leg, years sequential within the
  invocation, legs sequential (rule 12). Both legs registered same-session
  whatever the outcome (rule 15).

Phase-0 static reach: the cap clips 1,013.5 MW of LP-realized peak-band MW
(6.76% of duct-flagged CC MW; 33 rows with gap > 8, 16.2 GW flagged MW ≥ 8
gap) on the base-fleet build. The per-year dispatch fleets carry vintage
snapshots and exits, so per-year clips will differ; S-2 below is therefore
RELATIONAL on each year's own fleet parquet, never a frozen MW constant
(miso-191 mis-freeze lesson).

## 3. Directional prereg (frozen in phase 0, before any census quantity)

Model mean LMP moves DOWN (C3a-2025 more negative, ADVERSE to the −12.3405%
gap), confidence 0.8. Mechanism: the cap only ever shrinks the expensive top
band. Reported at full magnitude whichever way it lands.

## 4. Gates

- **S-0 control integrity**: the control's scored criteria reproduce the
  keeper's (C3a per year to 2 dp; same fail set {C3a-2025}). Any drift is
  disclosed; the A/B is scored control-vs-arm regardless.
- **S-1 single delta**: the arm's `run_config.json` `scenario_config` differs
  from the control's in exactly `cc_duct_peaking_cap_pct: null → 8.0`
  (run-identity fields — timestamps, note, paths — exempt).
- **S-2 capacity-grain liveness (anti-inert)**, on each year's committed
  `dispatch/<year>_P1_fleet.parquet` (the witness channel): joining CC rows
  by plant between legs, (a) Σ peak-tranche MW falls arm-vs-control by > 0
  in every year; (b) the fall is confined to duct-flagged plants with
  gap > 8 — no other CC row's peak band moves by more than 1 MW.
  SATISFIABILITY of the join/schema is verified on the CONTROL leg before
  the arm launches (miso-191 lesson); a schema mismatch amends the witness
  procedure only, disclosed in the FINDING before the arm solve, never after
  scoring.
- **Kills** (frozen from the charter's §D): **K-1** any criterion-year
  PASS→FAIL flip vs control; **K-2** C3b NRMSE crossing its 0.20 gate in any
  year; **K-3** any new D-4 conduct failure vs control; **K-4** DOF
  `n_residual` > 2 (the cap is engineering-identified — the ledger gains one
  non-residual parameter, 37→38, or the kill fires).

## 5. Promotion rule (miso-188 §4 pattern)

Promote the arm to keeper iff S-0/S-1/S-2 clean AND K-1..K-4 all silent AND
the adverse face stays declared: max over years of the C3a worsening
(arm minus control, in the adverse direction) ≤ 1.5 pp. Then the promoting
session re-stamps keeper shard/status/matrix per rules 15/22/28.

- A kill fires → the cap leg is REJECTED on its own gates; keeper unchanged;
  both legs still registered; the cell evidence records the rejection.
- Gates silent but the adverse face exceeded (>1.5 pp worsening in any
  year) → no self-promotion: register both, write the finding, escalate the
  structural-vs-scored conflict to the owner (the miso-186/191 path).

## 6. Cell stamp (rule 28(b), in-session, whichever way)

`mechanism-matrix/MISO.js` `cc_duct_peaking`: U → the evidence-bearing
verdict this A/B licenses — K (the mechanism is armed on the designated
keeper and phase-0 proves it live: 100% class coverage, 100% of CC_REGULAR
MW conforming; the 7.9%-of-covered-MW CC_CHP deviation is the documented
steam-host committed-first clamp `assembly.py:630` + steam-floor re-banding
`:827` superseding the duct band by design, rule 19) — with the cap leg's
own outcome (promoted / rejected / escalated) recorded in the note at full
magnitude, including the phase-0 A1 mis-freeze disclosure (frozen 99% line
FAILED at 92.07%; amended adjudication reported against interest).
