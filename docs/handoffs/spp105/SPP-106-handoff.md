```
SESSION SPP-106: SPP — OFFER-SIDE UNAVAILABILITY (design lane, zero LP). Chartered by the owner's SPP-105 card "Offer-side design" (2026-09-30).
DATA PROFILE: spp
MODEL: Opus or Fable (rule 27). CLAUDE.md is binding; rules 1, 13, 14, 17, 19, 21, 23, 25, 28, 29(b), 31–36 matter most.

STATE (verify against origin/main)
- Keeper: 2026-09-28-spp-100-chp-scope, bundle results/calibration/spp100_arm_span (2019–2025). Train 2023–25 CALIBRATED (lone ledgered C3c); validation 2019–22 NOT-YET. Train C3a −6.7 / −8.6 / −5.4 % (under-priced), C3c 0 / 7 / 2 h vs RT 42 / 59 / 68.
- SPP-105 (docs/handoffs/DESIGN-spp-105-gas-family-outage-2026-09-30.md, RESULT-spp-105-gas-family-outage-2026-09-30.md; results/calibration/_spp105_gas_outage_phase0.json; data/raw/spp-gen-outage):
  * The keeper's gas outage tracks SPP's published hourly gas outage (r 0.65–0.91). No SPP CT/ST/CC split exists for 2024–25.
  * Arm A (wefor_residual 0.0 on CC/ST) and arm B (spp_gas_crow_residual_outage, the CROW pin) were both solved and REJECTED (cells R). A broke C3a 2024 (−12.5 %). B added 64 / 20 GWh unserved in 2024 / 25, and its price move was scarcity.
  * READING: the 2023+ upper-tercile price shortfall is NOT an outage-availability object. Candidates are offer / commitment side.
- MMU "Unavailable Generation Capacity in SPP Markets: Causes and Impacts" (Dec 2025; spp.org/documents/75563) quantifies offer-related unavailability that CROW outage does not carry:
  * "reliability" commitment status: ~4 % of rated conventional capacity (3 % of all), offline unless SPP identifies a reliability issue (Figs 2–3, by technology/fuel);
  * emergency-max below rated capability: 1.5–3 % of rated conventional capacity;
  * unreported ambient derates: 185–422 MW/day average, 115–134 days/yr (Fig 12);
  * offered physical parameters (min-run, ramp, start times) less flexible than the reference levels.

CHARTER (design first; nothing solve-affecting is built until the owner rules on the design)
1. Phase 0, zero LP.
   - Decompose the keeper's upper-tercile (RT ≥ p67, < p99, Feb excluded) available gas and coal headroom 2023–25 against what the MMU classes would remove. Say whether any class is concentrated in the scarce hours (season / hour) rather than flat.
   - Search for an ADMISSIBLE SPP-own, forward-reproducible series for each class:
     * portal products (offer-side commitment status, historical offers with emergency max vs economic max, the ~90-day-lagged offer data SPP-81b used);
     * MMU ASOM / QSOM tables;
     * the Dec 2025 report's figures (digitizable? rule-14-reconcilable?).
   - For each candidate, state the rule-13 forward story and give per-year zero-LP predictions with the SPP-84 re-clear instrument (scripts/probes/_spp105_gas_outage_hourly_phase0.py has the harness; add a carrier to _spp105_carriers.py).
2. DESIGN doc covering: form (a replacement per rule 19 — what existing mechanism, e.g. the flat summer derate or the statistical stack, would it displace?); driver/window/forward story (rule 17); zero fitted parameters (rule 21); failure modes (SPP-105 B's scarcity trap: check unserved-energy risk at zero LP before any solve); the owner-accepted cost profile.
   - If no admissible series exists, say so plainly and recommend recording it as a model-class limit.
3. Put it to the owner as a clickable decision card (AskUserQuestion). If approved, follow the standard procedure (field default off + matrix row + cell in every shard + tests; PRECOMMIT pinned by full SHA; G-DRIFT vs spp100_arm_span; shard check tested on a synthetic leg; seven year-isolated shards in one message, relaunching any shard stuck PENDING > 15 min; compose/attest/register/score; RESULT; promotion card per rules 31/35). The parent solves nothing (rule 32(a)).

DO NOT: re-open spp_ct_lole_efor, spp_gas_crow_residual_outage or the SPP-105 wefor_residual arm (all R); pin availability or offers to published totals (rule 13); tune offer_curve_by_group; touch wefor_multiplier; re-run spp_commitment_posture alone (SPP-102/103 R).
OUT OF SCOPE: the coal outage over-count; gas-price levers; reserve co-opt; topology; other ISOs.
EITHER WAY: owner decisions as clickable cards; merge when the required checks pass (Promotion completeness, Keeper-integrity gates, Rule-28 matrix guard, Ruff, Cache-key guard, shrink-guard); comment once per other-lane red check (open at SPP-105 close: FR-22 CAISO keeper fields; solve-surface pin for six non-SPP ISOs); archive all shards (rule 33); end with an SPP-107 card.
Housekeeping owed to the owner (sessions cannot delete refs): claude/spp104-2019 … claude/spp104-2025; claude/spp105a-2019 … claude/spp105a-2025; claude/spp105b-2019 … claude/spp105b-2025.
```
