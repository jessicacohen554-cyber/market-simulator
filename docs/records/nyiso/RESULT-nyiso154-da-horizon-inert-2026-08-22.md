# RESULT nyiso-154 — the DA-horizon uncap is MEASURED EFFECTIVELY INERT; the start-conduct residual closes as tested, typed to an owner-court cycling-cost identification

Session nyiso-154, 2026-08-22. Prereg
`PREREG-nyiso154-da-horizon-uncap-2026-08-22.md` + phase-0 record
`_nyiso154_phase0.json` + gates probe committed and pushed BEFORE the arm
solved. ONE solve (ARM D = the nyiso-152 keeper recipe +
`nyiso_gas_bridge_da_horizon: False`; control = the committed keeper bundle,
no re-solve — solve-affecting tree verified unchanged). Run
`2026-08-22-nyiso-154-da-horizon`, registered per rule 15. Gates record
`_nyiso154_ab_gates.json`. Holdout freeze ACTIVE; 2023–2025 only.

## 1. Phase-0 (the typing work, all from committed artifacts)

* **Identity fix:** the nyiso-150 assessment's "Flynn (56234)" row was a
  name/code mislabel — 56234 is CAITHNESS (mildly UNDER-starting, 3/2/4 vs
  4/6/8). Flynn is 7314, a genuine cycler (metered **115/78/103** starts/yr)
  the model over-cycles 2.0–3.7×. The material miss is **Bethlehem 2539:
  45/13/28 model starts vs 6/7/7 metered**.
* **Outages ruled out:** 40/9/9 of Bethlehem's >24 h off-gaps are economic
  (availability ≥ 50 %); 2/1/1 outage-driven.
* **Price-trough typing refuted on the floor-clean offer:** the naive
  revealed threshold is contaminated by the 146c state floor; on the
  above-floor p10 offer ($34.4/$31.1/$43.4) the gap deficits are
  $4.2/$1.7/$0.1 p50 (p90 $9.0/$5.3/$12.7) — and actual prices in the same
  stretches clear no better. The real plant rode through real deficits.

## 2. The A/B — inert, and the inertness is the finding

D-K1 PASS (exact single delta, True→False). **D-K2/D-K3 FAIL on
liveness/capture: the uncapped restart inequality glues ONE >24 h segment in
2023 (+29 floored hours; starts 45→44) and ZERO in 2024/2025** (Bethlehem
floored hours bit-identical at 7,688/7,797). The phase-0 capture
(11–12/5/5 glued at a $35–50/MW band on the offer estimate) over-predicted:
the detector's own `mc_base`/startup arithmetic finds riding through the
surviving gaps uneconomic in all but one case — **the 24 h DA-horizon cap
was never the binding constraint.** D-K4 PASS (zero new D-4/D-1 — nothing
moved). D-K5: criteria statuses identical to the keeper (C3a
+5.2/−2.7/−8.1 %; C3c bit-identical 1/0/0); C6 unattested-probe.

## 3. The closure this buys (pre-committed in the prereg's §5)

On the model's own prices and its registered NREL startup basis, **shutting
down over these 30–90 h stretches IS the economic choice** — the real
plant's 6–7-start/yr ride-through implies an effective cycling /
self-commitment cost several times the registered startup table. Every
admissible in-repo lever for the start-conduct object has now been tested:
per-plant measured min-run (nyiso-146, R), the online-hours state floor
(nyiso-146c, K — carrying the bulk of the repair: 327/526/262 → 45/13/28),
and the economic-glue horizon (this session, inert). **The residual is not
closable at HEAD.** The two remaining routes are:

* an **owner-court identification intake**: adopting a published
  cycling-cost basis materially above the NREL startup table (e.g. the
  NREL/Intertek-APTECH power-plant cycling-cost study) — an identification
  decision the owner makes on the source's merits, never a residual fit
  (rule 13); or
* the **ledgered trough-compression object** moving in its own
  (G-adjudicated) lane, which would shrink the gap deficits themselves.

The start-conduct queue item — the LAST testable lane from the nyiso-150
path-to-frontier — **closes as tested.** Flynn's 2–3.7× over-cycling shares
the same typing (a cycler whose start economics are too cheap in the model),
and no separate admissible lever exists for it either (its per-plant
min-run form is the tested-R nyiso-146 mechanism).

## 4. Dispositions

* Matrix: the `nyiso_gas_bridge_da_horizon` leg's nyiso-154 record appended
  to the `gas_commitment_bridge` NYISO cell (cell stays **K** on the keeper's
  capped form — the OFF position is adjudicated inert-at-recipe, not armed).
  Keeper unchanged (`2026-08-22-nyiso-152-duty-complete`); no re-key.
* Registration auto-pruned `2026-08-19-nyiso-146b-online-hours` (top-15).
* Frontier: see `ASSESSMENT-nyiso154-frontier-2026-08-22.md` — with this
  closure the testable set is EXHAUSTED and the assessment recommends the
  owner ratify a frontier declaration.

## 5. Reproduction

```
python3 scripts/probes/_nyiso154_phase0.py
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso154_armD_recipe --out-dir results/calibration/nyiso154_armD
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso154_armD --iso NYISO --json-out results/calibration/nyiso154_armD/legitimacy_diagnostics.json
python3 scripts/probes/_nyiso154_ab_gates.py --arm-log <solve log>
```
