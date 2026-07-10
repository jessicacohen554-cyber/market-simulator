# FINDING — caiso-70: RA-bridge de-crowding does NOT unlock CT_PEAKER; the ablation's CT lift is an evening commitment/seam effect (2026-07-10)

**Probe:** `2026-07-10-caiso-70-g61b-decrowd` (+ `-ablation` twin), pre-registered A/B on the
caiso-69 recipe (SP15 split topology, `ct_netload_drag=False`) with ONE delta:
`caiso_ra_bridge_startup_aware=True` (G-61 path (b), caiso-63/66 mechanism).
Script: `scripts/probes/_caiso_g61b_decrowd_ab.py`. Negative result, registered per rule 15.

## Hypothesis (from caiso-69's corrected redirect)

caiso-69's zero-forcing ablation cleared MORE CT_PEAKER than its main run (2.02/1.41/0.98 vs
0.90/0.91/0.79 TWh) → read as: the RA must-offer bridge's forced CC min-gen (~3.2–3.8 TWh at
`min_load_frac` 0.26 across the midday gap) crowds peakers out of the pockets. Predicted: the
startup-aware release (drops phantom P0 micro-run bridging, −38 to −43 % of bridge forced
energy on caiso-63/66) lets pocket CTs clear on merit toward actual 4.56/5.24/3.09 TWh.

## Result — the release engaged; CT did not move

| metric (2023/24/25) | caiso-69 main | caiso-70 main | caiso-70 ablation | actual |
|---|---|---|---|---|
| D-2 bridge forced CC (TWh) | 3.62 / 3.46 / ~2.8 | **2.26 / 2.02 / 1.56** (−37/−42/−45 %) | 0 | — |
| CT_PEAKER (TWh) | 0.89 / 0.91 / 0.79 | **0.90 / 0.92 / 0.82** | 2.02 / 1.41 / 1.01 | 4.56 / 5.24 / 3.09 |
| CC_REGULAR (TWh) | 62.42 / 65.51 / 65.53 | 61.94 / 65.05 / 65.32 | 64.65 / 66.95 / 65.33 | — |
| LA_BASIN mean LMP | 70.18 / 47.82 / 51.26 | 70.05 / 47.65 / 51.45 | — | SP15 49.39 / 32.68 / 32.22 |
| hrs > $200 | 530 / 0 / 0 | 540 / 0 / 0 | 607 / 63 / 0 | 21 / 35 / 8 |

The de-crowding hypothesis is **refuted**: releasing a third to a half of the bridge's forced CC
frees belly headroom, and the LP fills it with CC-on-merit and imports — never CTs. Prices,
tail, and pocket premia are all essentially unchanged.

## Attribution — where the ablation's extra CT actually comes from

Hour-of-day deltas (ablation − main, caiso-70 pair):

- **CT_PEAKER: +0.3–0.4 GW concentrated in the evening ramp h18–21** (belly hours ≈ 0).
- **Imports: −1.0 to −1.4 GW in the same evening hours** (also −0.7 to −1.1 GW morning shoulder).
- CC_REGULAR: +0.2–0.5 GW spread across all hours (total CC is HIGHER without its own floors).

So the caiso-69 "ablation clears more CT" signal was never midday pocket headroom. Removing the
whole bridge changes the committed-run structure (P0 run pattern → P1 startup amortization) and
shifts the evening supply mix from seam imports to domestic CC+CT. Both arms confirm what the
seam-tz FINDING §4.3 and the belly-commitment probe already measured from the other side: the
model's miss is the **evening CC/CT commitment posture** (reality commits +1.9/+1.2/+0.3 GW more
evening CC than the model, plus the entire 3.7–4.4 TWh/yr CT gap), and no bridge-side release
can create it.

## Consequences for the probe queue (handoff order)

1. ~~RA-bridge de-crowding (G-61b on the split)~~ — **closed, negative** (this probe).
2. **AS/reserve-driven CT energy is now the live lead**: a channel that DISPATCHES CTs
   (RTPD/RUC-like awards → energy) against a measured CAISO AS-procurement requirement
   (rule-13 admissible, forward-regenerable). The evening-ramp locus measured here is exactly
   where CAISO holds/deploys spin + non-spin.
3. C3a belly/evening overprice remains a commitment-posture question (one mechanism per
   phenomenon — any evening-commitment mechanism must reconcile with the RA bridge, not stack).

Dead ends re-confirmed: pocket-limit tightening and offer-level moves (pockets already
over-priced ~+15–21 vs corrected actuals); tail unchanged by bridge-side releases.

## Probe-#2 scoping (same session): the posture lever is ported but ex-ante INERT on the system-wide requirement — the binding driver must be locational

The award→energy channel probe #2 calls for exists as machinery: the MISO/PJM pooled
commitment-posture lever (U/SU columns; providing reserve from a postured pool costs a real
NREL-table start + a CEMS-measured min-load ride — endogenous, no floor, no D-2 id, zero fitted
parameters). It is now ported to CAISO (`caiso_commitment_posture`, default off, tested,
composing with CAISO's storage duration gate; reads only under
`energy_reserve_coopt + caiso_reserve_coopt`).

**But do not solve it on the current system-wide requirement.** BAL-002-WECC-3 contingency
(max(MSSC ≈ 2.2 GW, 6 % × load) split spin/non-spin) tops out ~2.2–2.7 GW, while the
UN-postured free reserve pool is ≥ 3–5× that: hydro ≥ 6.6 GW (ramp10 backfilled at full
nameplate, fast-start by physics → never postured), fast-start CT ≥ 4.3 GW (rule-18 exempt,
offline ramp free), batteries ~5–8 GW (0.5 h ASSOC SOC gate, trivially met). The LP will never
pay a CC start + min-load ride while free supply covers the requirement several times over —
the same reason caiso-59/62 measured inert, now established ex-ante instead of with another
solve (rule 1: the mechanism's own driver evidence says it cannot bind).

**What would make it bind — the ranked next build:** CAISO procures AS against published
SUB-REGIONAL constraints (the expanded-system/SP26/NP26 AS regions with regional
minima/maxima) — a measured, forward-regenerable, LOCATIONAL requirement. On the split
topology, a SoCal AS-region minimum that in-region units must serve cannot be met by NP15-side
hydro — exactly the configuration in which the posture forces SoCal gas online through the
evening AS hold, which is (i) the RUC-like award→energy channel for pocket CTs/CCs, (ii) an
evening commitment-posture driver for the C3a body, and (iii) a candidate former of the missing
2024/25 LOCAL tail (C3c) that the system-wide co-opt could never price. Data intake needed:
CAISO AS-region definitions + regional procurement minima (OASIS AS_REQ / DMM AS chapters);
zero fitted parameters. Secondary candidates: the spin product's online gating via the
sync/non-sync split composed with posture (a dispatch.py extension — the split and posture are
mutually exclusive today), and an FRP-like intra-hour ramp requirement (measured net-load
forecast-error percentiles).

## Governance note

caiso-70 is the **first CAISO bundle with C6 governance PASS** (rubric governance attestation +
carried caiso-65 DOF ledger; drag entry marked INERT; the startup-aware flag adds zero free
parameters). Scored under rubric v2.4 — C5a CO2 reads FAIL where caiso-69's stored v2.2 metrics
gave a commercial-band CAVEAT; cross-version comparisons should re-score, not read stored
statuses. Determination NOT-YET (8 fails), not promotable, not proposed.
