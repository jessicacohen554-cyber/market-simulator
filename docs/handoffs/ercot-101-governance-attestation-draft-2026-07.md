# ERCOT-101 — C6 governance attestation DRAFT (pending owner sign-off)

**Keeper:** `2026-07-23-ercot100-netrev-margin-keeper`
(`results/calibration/ercot_netrev_margin`). **Current determination:** NOT-YET
(sole reason: C6 governance UNATTESTED — owner lane). **Proven result of signing
the block below:** CALIBRATED-WITH-CAVEATS (verified by
`scripts/calibration_verdict.py` against the registered payload with this
attestation swapped in — 8 gates PASS, C3a/C3b/C3c ledgered 3/3 within budget, C6
PASS).

> **Amended 2026-07-24 (ERCOT-107/108).** The 2023 `price_mean` / `price_tail`
> exception texts below were corrected: their original reasoning rested on "no 2023
> SCED/RT re-offer disclosure exists", which is **no longer true** — the 2023 RT SCED
> offer wall was recovered and is on main. The conclusion is unchanged and now rests on
> stronger evidence: the wall is in the stack and **fit-neutral**, so the bound is
> **depth, not height**, and ERCOT-107/108's completed 2×2 shows the envelope/ORDC
> reserve family is bistable with no configuration that recovers the depth without
> repricing the whole year. See
> `results/calibration/FINDING-ercot107-108-scarcity-tail-bistable-2026-07-24.md`.
> No other change; the four governance assertions and the DOF ledger are untouched.

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
     "reason": "C3a -27.1% is ONE residual with C3c-2023: an exact load-weighted band decomposition (ercot101_price_decomp) attributes 97% of the mean-price gap to the >$300 scarcity tail. The bound is DEPTH, not height. The 2023 RT SCED offer wall is now RECOVERED and IS in the stack (ercot_sced_offer_wall_condbinned.json carries 2022-2025; the prior 'no 2023 SCED corpus' reading was a missing-data bug), and it is FIT-NEUTRAL: keeper $46.76 -> $46.50 zonal model_lw with it (ercot105), ercot103 $41.46 -> $41.21 (ercot107). The model carries ~1.5 GW too much cheap supply at the spike hours, so the real high RT offers never become marginal. ERCOT-107/108 then closed the reserve-side family on a completed 2x2: the on-line-capacity envelope is BISTABLE (in-LP -> 963/181 tail hours with the 1948-h [30,80) band repriced $921-954; not-in-LP -> 69-76/181), and the ORDC total-reserve span is NOT the confound (span off moves +699.7% -> +680.6%, 2.7% of the over-fire, tail count identical). No reachable configuration recovers the depth without repricing the whole year. Attributed measured-input limitation; rule 13 forbids a residual adder."},
    {"criterion": "price_shape", "year": 2023,
     "reason": "C3b 0.531 is the monthly image of the same 2023 >$300 tail (the Aug/Sep heat-wave months carry the miss). Same attributed RT-re-offer-conduct root as C3a-2023; no separate mechanism and no residual tuning."},
    {"criterion": "price_tail", "year": 2023,
     "reason": "Model reaches 70/181 tail hours, inside the 123/181 intra-hour reach ceiling (ercot99_intrahour_bound; the rest are 15-min transients an hourly LP smooths). Tail is hub-level scarcity (LZ-hub congestion only +$15 at tail), not a zonal-congestion artifact. Residual is the offer-DEPTH bound above (the recovered 2023 RT wall is in the stack and fit-neutral - the model's ~1.5 GW of surplus cheap supply at the spike hours keeps the real high offers off the margin), and ERCOT-102/107/108 show the reserve side cannot close it: the MISSED tail hours carry a SLACK reserve dual (~$0.9) under every non-capped variant, and forcing the cap to bind reprices the entire year. Attributed measured-input limitation."},
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
