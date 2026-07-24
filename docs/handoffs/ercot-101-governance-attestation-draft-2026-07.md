# ERCOT-101 — C6 governance attestation DRAFT (pending owner sign-off)

**Keeper:** `2026-07-23-ercot100-netrev-margin-keeper`
(`results/calibration/ercot_netrev_margin`). **Current determination:** NOT-YET
(sole reason: C6 governance UNATTESTED — owner lane). **Proven result of signing
the block below:** CALIBRATED-WITH-CAVEATS (verified by
`scripts/calibration_verdict.py` against the registered payload with this
attestation swapped in — 8 gates PASS, C3a/C3b/C3c ledgered 3/3 within budget, C6
PASS).

This is a governance sign-off, not a model change. It asserts the four
machine-cross-checked governance claims and ledgers the three price gates as
**accepted measured-input limitations** (attributed scarcity-tail bound, evidence
in `docs/DIAGNOSIS-ercot-101-scarcity-tail-attribution-2026-07.md`). No solve
input changes; the DOF ledger is carried byte-identical from ercot99/100 (9
entries / 8 residual, zero delta for the margin flag).

**Machine check (already clean, verified this session):** `outage_source=historic`
(exogenous); no forbidden fitted-mechanism flags active. So C6 turns solely on the
four attestations below being true and owner-signed.

## The four governance assertions (owner attests these are true)

1. `levers_trace_to_measured_input = true` — every keeper lever is a measured or
   derived market/physical input (offer-curve HR-band multipliers are the
   rule-1-sanctioned tuning surface, in the DOF ledger; the net-revenue anchor is
   a derived measured input; the RT/DAM walls, DAM availability, drag, reserves,
   ORDC overlay are all measured).
2. `no_fit_to_price_residuals = true` — ERCOT-101 attributed the scarcity tail;
   it added **no** residual adder/offset, no ladder-quantile extension, no
   room-pin (all pre-registered forbidden). The offer form (net-revenue margin)
   and the state-off / honest-input fixes are structural (rule 1/11), not
   residual fits.
3. `no_pinning_to_actuals = true` — no unit pinned to CEMS generation, no output
   rescaled to actuals, no measured-outcome feedback.
4. `outage_filter_exogenous_net_load = true` — availability is the historic
   CAMPD/DAM overlay (a physical availability event), never a residual filter.

## Proposed attestation additions (merge into the keeper's calibration_attestation.json)

```json
{
  "governance": {
    "attested_by": "<OWNER NAME / SIGNOFF ID> (ercot-101, 2026-07-24)",
    "levers_trace_to_measured_input": true,
    "no_fit_to_price_residuals": true,
    "no_pinning_to_actuals": true,
    "outage_filter_exogenous_net_load": true,
    "note": "ERCOT-101: machine check clean (outage_source=historic exogenous; no forbidden flags). The three price gates are ledgered below as attributed measured-input limitations (scarcity-tail bound; docs/DIAGNOSIS-ercot-101-scarcity-tail-attribution-2026-07.md), not model misses. No residual tuning applied (rule 1/11/13). DOF ledger unchanged from ercot99/100 (9/8)."
  },
  "exceptions": [
    {"criterion": "price_mean", "year": 2023,
     "reason": "C3a -27.1% is ONE residual with C3c-2023: an exact load-weighted band decomposition (ercot101_price_decomp) attributes 97% of the mean-price gap to the >$300 scarcity tail. That tail is set by real-time re-offer conduct (marginal ST_GAS/CT_PEAKER re-offering $500-5000 in RT vs their measured DAM/merit basis; model clears within ~480 MW of $200 at the Aug missed hours). The only 2023 offer corpus on disk is the DAM disclosure, whose energy offers are measured-cheap (wall p50 $327, model tail already $211-1244) - no 2023 SCED/RT re-offer disclosure exists. Unfixable with measured constructions; rule 13 forbids a residual adder."},
    {"criterion": "price_shape", "year": 2023,
     "reason": "C3b 0.531 is the monthly image of the same 2023 >$300 tail (the Aug/Sep heat-wave months carry the miss). Same attributed RT-re-offer-conduct root as C3a-2023; no separate mechanism and no residual tuning."},
    {"criterion": "price_tail", "year": 2023,
     "reason": "Model reaches 70/181 tail hours, inside the 123/181 intra-hour reach ceiling (ercot99_intrahour_bound; the rest are 15-min transients an hourly LP smooths). Tail is hub-level scarcity (LZ-hub congestion only +$15 at tail), not a zonal-congestion artifact. Residual = the unmeasured 2023 RT re-offer wall; attributed measured-input limitation."},
    {"criterion": "price_tail", "year": 2024,
     "reason": "Measured 2024 SCED online-spare wall (60-Day SCED disclosure) is cheap up to p90 (CC top-net-load-bin p50 $41, p90 $115) - below the model's own repriced wall; only the p95-p99 band ($150-VOLL) is expensive, and it is (i) sample-day-selection-biased (tail-days corpus) and (ii) VOLL-adjacent scarcity re-offers that are the ORDC overlay's domain (double-count if put in energy merit). The wall is already repriced ABOVE the model marginal (depth, not height), and ~1/3 of missed tail hours sit at moderate net load (below the net-load surface's firing bins). Actual tail $1058 is ORDC/conduct-set beyond any merit wall. Attributed bound; extending the ladder is residual-motivated (rules 1/23)."},
    {"criterion": "price_tail", "year": 2025,
     "reason": "2025 tail is fully RT-only scarcity: DA energy merit is cheap at the tail hours (DA p50 $91), the model catches 0/31, and the largest LZ-hub congestion of the three years (+$64 mean) sits above system lambda a reduced-network copperplate LP cannot form. Same attributed family as 2023/2024; no 2025-specific residual tuning."}
  ]
}
```

## To apply after sign-off (one commit, no re-solve)

1. Merge the `governance` + `exceptions` blocks above into
   `results/calibration/ercot_netrev_margin/calibration_attestation.json` (keep
   `free_parameters` unchanged), replacing `<OWNER NAME / SIGNOFF ID>`.
2. `python scripts/calibration_verdict.py --run-id 2026-07-23-ercot100-netrev-margin-keeper --write-metrics`
   → determination CALIBRATED-WITH-CAVEATS.
3. Refresh the ERCOT keeper dashboard status
   (`scripts/build_status.py --iso ERCOT`) + run the
   `calibration-keeper-auditor` subagent.
4. Commit the bundle attestation + metrics + status shard; push.

Until signed, the keeper stays NOT-YET and this file is the standing draft.
