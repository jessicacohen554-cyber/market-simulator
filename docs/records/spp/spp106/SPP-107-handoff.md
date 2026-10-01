```
SESSION SPP-107: SPP — REPAIR THE MMU OFFER-SIDE CARRIER (design + solve). Chartered by the owner's SPP-106 cards "Hold, investigate shortfall" and "Repair EX" (2026-10-01).
DATA PROFILE: spp
MODEL: Opus or Fable (rule 27). CLAUDE.md is binding; rules 1, 13, 14, 17, 19, 21, 25, 28, 29(b), 31–36 matter most.

STATE (verify against origin/main)
- Keeper: 2026-09-28-spp-100-chp-scope, bundle results/calibration/spp100_arm_span (2019–2025). Train 2023–25 CALIBRATED (lone ledgered C3c).
- SPP-106 (DESIGN / PRECOMMIT / RESULT-spp-106-offer-side-unavailability-2026-10-01.md): field spp_mmu_offer_unavailability (default off, data/raw/spp-mmu-unavailable-capacity). Arm EX solved and HELD:
  * train C3a −6.7/−8.6/−5.4 → −4.4/−6.0/−1.6 %; COAL_PRB over-count 2023/24 +3.3/+3.6 → +0.6/+0.8 TWh; upper tercile +0.6/+1.4/+1.2 $/MWh;
  * E3 FAIL: unserved +2.9 GWh 2024 (21 Oct 13–17h), +1.4 GWh 2025 (21 Dec 10–13h), all SPP-South, N→S link at 3,400 MW; validation 2021 C3a PASS → FAIL.
- Zero-LP diagnosis (RESULT §7): two construction errors against the MMU's own definitions:
  (1) bands applied as share × RATED pmax on partially-outaged units, while the MMU measures vs the derated amount (§3.1.2): multiplicative (share × available MW) saves 359 / 200 MW of South capacity in those hours;
  (2) the economic→emergency band is removed in the reliability hours it exists for (MMU: "only accessible when SPP anticipates or identifies a reliability issue"): 464–525 MW of South.

CHARTER
1. Zero LP first. Design the repair as a sub-gate of spp_mmu_offer_unavailability (rule 19: one mechanism):
   (1) multiplicative band application;
   (2) the econ→emergency slice available ONLY in scarcity. State its form and its price with zero fitted parameters (e.g. offered at the model's own slack/VOLL price minus ε, or an existing emergency-tier seam). Check rule 21 / rule 24 before choosing.
   Measure with the SPP-84 re-clear and the SPP-106 short-hour instrument (scripts/probes/_spp106_offer_unavailability_phase0.py): per-year Δprice (all / upper tercile), short hours, and the share of the train-tier C3a gain that (1) gives back.
2. DESIGN doc + owner card. If approved: field(s) default off, matrix row/cells, tests, PRECOMMIT pinned by full SHA, G-DRIFT vs spp100_arm_span, shard check on synthetic legs, seven year-isolated shards in one message, compose/attest/register/score, RESULT, promotion card (rules 31/35). The parent solves nothing.

DO NOT: re-open spp_ct_lole_efor, spp_gas_crow_residual_outage or wefor_residual (R); carry reliability-status capacity (allocation unidentified, rule 21); tune offer_curve_by_group or wefor_multiplier; pick a band price by its effect on the gates.
OUT OF SCOPE: the coal outage over-count as its own lane; gas-price levers; reserve co-opt; topology (the N→S 3,400 MW limit); other ISOs.
EITHER WAY: owner decisions as clickable cards; merge when required checks pass; comment once per other-lane red check (open: FR-22 CAISO keeper fields; solve-surface pins for six non-SPP ISOs; the 28 fast-tier reds red on main at 2026-10-01); archive all shards (rule 33); end with an SPP-108 card.
Housekeeping owed to the owner (sessions cannot delete refs): claude/spp104-*, claude/spp105a-*, claude/spp105b-*, claude/spp106ex-2019 … claude/spp106ex-2025.
```
