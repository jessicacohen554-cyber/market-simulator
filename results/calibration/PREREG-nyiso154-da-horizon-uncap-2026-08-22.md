# PREREG nyiso-154 — uncapping the bridge's economic gap-glue (`nyiso_gas_bridge_da_horizon` → False): the self-commitment restart inequality decides, for the start-conduct residual

Session nyiso-154, 2026-08-22. Committed and pushed BEFORE the arm solves.
Phase-0 record: `_nyiso154_phase0.json` (probe
`scripts/probes/_nyiso154_phase0.py`, measured on the committed keeper bundle
`nyiso152_armSE` ≡ `2026-08-22-nyiso-152-duty-complete` + the committed
actual-LMP series). Holdout freeze ACTIVE; 2023–2025 only (rule 22); all
three years in one invocation (rule 16).

## 1. Object — the start-conduct residual, phase-0-typed

The last testable lane item (nyiso-150 assessment §5 item 4), with its
recorded premise corrected and its confounds ruled out:

* **Identity fix:** the assessment's "Flynn (56234)" row was a name/code
  mislabel — 56234 is CAITHNESS (its 3/2/4 vs 4/6/8 under-starting numbers
  are Caithness's). Flynn is 7314, a genuine cycler (metered 115/78/103
  starts/yr) that the model over-cycles 2.0–3.7× (229/288/284).
* **The material miss is Bethlehem 2539: 45 / 13 / 28 model starts vs
  6 / 7 / 7 metered** (median model runs 44/249/56 h vs the real plant's
  ~1,400 h scale).
* **Outages ruled out:** of Bethlehem's >24 h off-gaps, 40/9/9 are ECONOMIC
  (mean availability ≥ 50 %); only 2/1/1 are outage-driven.
* **The trough story REFUTED on the floor-clean offer:** the naive revealed
  threshold (p05 over all on-hours) is contaminated by the 146c state floor;
  the above-floor p10 offer estimate is $34.4 / $31.1 / $43.4, and the
  mean price deficit inside the economic gaps is $4.2 / $1.7 / $0.1 p50
  (p90 $9.0 / $5.3 / $12.7) — the gaps are shallow-to-moderate price
  deficits over 30–90 h, not deep troughs, and ACTUAL prices in the same
  hours clear the threshold no more often than the model's. The real plant
  rides these stretches anyway (6–7 starts/yr): multi-day owner
  SELF-COMMITMENT on restart economics.

## 2. Mechanism (existing registered flag; no new field)

`nyiso_gas_bridge_da_horizon: False` — removes the 24 h DA-operating-day cap
(`DA_COMMITMENT_HORIZON_HOURS`) from the bridge's ECONOMIC gap-glue, so a
detected idle gap of ANY length is bridged at min-load exactly when the
detector's existing startup-restart inequality holds:
`startup_per_mw > (mc_gap − lmp_gap) × min_load_frac × gap_h`
(`model/commitment.py::caiso_ra_mustoffer_min_gen`, the `startup_bridge`
leg priced at the model's own P0 duals; `max_econ_gap_hours=None` is the
documented byte-identical-when-capped path). Physical (< min-down) bridges
were never capped. Driver (rule 17): the restart inequality itself — the
owner's multi-day self-commitment economics, the conduct the metered record
shows (a 750 MW CC does not shut for a 52 h stretch it can ride for less
than one restart). Window: exactly the gaps where the inequality holds
(self-limiting — a deep or long deficit still shuts the unit). Forward
story: regenerates every year from the LP's own prices and the same
class-table startup basis. ZERO new scalars (rule 21): the cap is removed,
not re-leveled; the inequality's inputs (NREL startup, measured min-load
0.523, P0 duals) are all already registered. D-2 id unchanged
(`nyiso_gas_commitment_bridge`); the bridge's D-2 share is PREDICTED to
rise (more glued floor energy) — declared here, guarded by C8/K6′ below.
Rule 19: this widens ONE existing mechanism's window; nothing is stacked.
DO-NOT-REDO check: no NYISO record tests `da_horizon` off (the 146-lineage
tested per-plant min-run [R] and the online-hours state floor [K]; ercot141
tested the ERCOT online-hours leg, not the horizon).

## 3. Arms (ONE new solve)

* **Control = the committed keeper bundle** `nyiso152_armSE`
  (`2026-08-22-nyiso-152-duty-complete`) — no re-solve; solve-affecting
  tree unchanged since it solved (verified at prereg time:
  `git log 12b90ca..HEAD -- src/ scripts/run_calibration*.py` empty).
* **ARM D** `nyiso154_armD` — keeper recipe + `nyiso_gas_bridge_da_horizon:
  false` (`nyiso154_armD_recipe` = `nyiso152_armSE_recipe` + the one key).

## 4. Gates (probe `scripts/probes/_nyiso154_ab_gates.py`)

* **D-K1 exactness** — scenario diff vs the keeper =
  {`nyiso_gas_bridge_da_horizon`} exactly (True→False).
* **D-K2 liveness** — Bethlehem's floored hours GROW (the glue fires:
  bridge-mech floored hours vs control rise in every year with ≥ 1 newly
  glued > 24 h segment), and the solve log's segment-length buckets show
  > 24 h floored segments.
* **D-K3 control-side capture** — Bethlehem P1 starts land inside the
  phase-0 prediction band: **[17, 51] (2023), [4, 12] (2024), [12, 35]
  (2025)** (predicted ~33–34 / 8 / 23 at the $35–50/MW startup band, ± 50 %
  for P1-feedback uncertainty), AND starts FALL vs control (45/13/28) in
  every year, AND the 146-convention no-degrade harness holds on the
  metered-start comparator set (each tracked plant:
  |arm − metered| ≤ 1.5·|ctl − metered| + 5).
* **D-K4 (K6′)** — ZERO new D-4 FAILs (the glue must never floor a
  meter-dark plant — the lay-up/duty membership exclusions bound it away
  from those populations) and zero new D-1 misses; the DECLARED bridge D-2
  share rise is admissible only with both legs clean; C8 stays PASS.
* **D-K5** — no CRITERIA PASS→FAIL vs the keeper in any year; C3a/C3c
  reported (glued min-load energy in trough hours can only ADD supply —
  adverse case: deeper troughs / C3a down; watched, 2025 at −8.1 % has
  1.9 pp headroom).

## 5. Decision tree (pre-committed)

* **All gates pass** → ARM D registers (rule 15); promotion to keeper iff
  determination not worse AND legitimacy strictly improves (the standing
  convention) — the structural case being a real conduct mechanism closing
  a 4–7.5× start-count miss to its economic remainder with zero new
  scalars.
* **D-K3 band miss with D-K2/K4/K5 clean** → register as probe; adjudicate
  on the numbers: the capture said the lever closes only ~25–55 % of the
  gap-count, so a partial-but-real repair with clean gates still promotes
  ONLY if the no-degrade harness and criteria hold and the owner-standing
  legitimacy test is met; otherwise the record stands R with the residual
  typed (below).
* **D-K4 or D-K5 fail** → REJECTED-AS-ARMED (a glue that manufactures
  convictions or moves criteria is the 146b over-glue class).
* **WHATEVER THE BRANCH, the residual typing stands and goes in the
  RESULT:** the un-glued remainder (gaps whose deficit × 0.523 × length
  exceeds any registered startup basis) is NOT closable by an admissible
  lever at HEAD — closing it needs either a published cycling-cost basis
  materially above the NREL table (an OWNER-COURT identification intake:
  choosing a bigger number because the residual wants it is rule-13
  fitting) or the ledgered trough-compression object moving (its own
  G-adjudicated lane). The start-conduct queue item CLOSES as tested with
  this typed remainder.

## 6. Reproduction

```
python3 scripts/probes/_nyiso154_phase0.py
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso154_armD_recipe --out-dir results/calibration/nyiso154_armD
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso154_armD --iso NYISO --json-out results/calibration/nyiso154_armD/legitimacy_diagnostics.json
python3 scripts/probes/_nyiso154_ab_gates.py --arm-log <solve log>
```
