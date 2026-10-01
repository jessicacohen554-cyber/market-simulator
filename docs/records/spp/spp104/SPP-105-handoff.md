```
SESSION SPP-105: SPP — GAS-FAMILY OUTAGE ALLOCATION (design lane, zero LP). Chartered by the owner's SPP-104 card "Continue: gas-family design" (2026-09-30).
DATA PROFILE: spp
MODEL: Opus or Fable (rule 27). CLAUDE.md is binding; rules 1, 13, 14, 17, 19, 21, 23, 25, 28, 29(b), 31–36 matter most.

STATE (verify against origin/main)
- Keeper: 2026-09-28-spp-100-chp-scope, bundle results/calibration/spp100_arm_span (2019–2025). Train 2023–25 CALIBRATED (lone ledgered C3c); validation 2019–22 NOT-YET.
- SPP-104 (docs/handoffs/DESIGN-spp-104-ct-outage-2026-09-29.md, RESULT-spp-104-ct-lole-efor-2026-09-30.md; results/calibration/_spp104_ct_availability_phase0.json):
  * "CT_PEAKER carries no outage" was an artifact of SPP-84's max-available metric. CTs carry the statistical GADS stack (WEFOR 0.07 x wefor_multiplier 0.7, POF 0.03, derate 0.05, summer 12.5 %).
  * Keeper gas outage-type minus SPP published (capacity-of-generation-on-outage, Natural Gas MW): -1.04/-0.31/+0.80/+1.97/-0.46/-1.29/+0.60 GW (2019–25). 2025 is measurable from the portal daily CSVs (/2025/<MM>/Capacity-Gen-Outage-<YYYYMMDD>.csv).
  * spp_ct_lole_efor (SPP 2023 LOLE EFOR for CTs) was solved and rejected (cell R). It raised train-tier prices toward RT (C3a 2024 -8.6 -> +1.4 %) but over-stated CT outage vs SPP's own data in every year and raised unserved energy.
- READING carried forward: the 2023+ keeper is short of gas unavailability in the scarce (upper-tercile) hours. The carrier must be consistent with SPP's measured hourly gas outage.

CHARTER (design first; nothing solve-affecting is built until the owner rules on the design)
1. Phase 0, zero LP.
   - Decompose the keeper's hourly gas unavailability by class (CC / ST_GAS / CT, plus CHP) on the outage-type basis (scripts/probes/_spp104_ct_availability_phase0.py --variant outage). Compare it hour by hour, not only annual means, against SPP's published hourly Natural Gas outage, especially in the upper-tercile RT-price hours of 2023–25.
   - Search for an ADMISSIBLE SPP-own CT/ST/CC split of that outage:
     * MMU ASOM "Resource outages and derates" (CC vs simple-cycle, where simple-cycle includes gas steam; charts only) — say whether digitization is reproducible and rule-14-reconcilable;
     * MMU "Unavailable Generation Capacity" (Dec 2025);
     * CROW-derived public data, FERC filings, SPP OPS/RC outage postings.
   - State the rule-13 forward story and give per-year zero-LP predictions (the SPP-84 re-clear instrument, gas-only).
2. DESIGN doc covering: form (a replacement per rule 19 — e.g. ST_GAS already carries full WEFOR on top of CAMPD windows, since wefor_residual is None); driver/window/forward story (rule 17); zero fitted parameters (rule 21); failure modes; the owner-accepted cost profile.
   - If no admissible split exists, say so plainly and recommend recording it as a model-class limit.
3. Put it to the owner as a clickable decision card (AskUserQuestion). If approved, follow the standard procedure (field default off + matrix row + cell in every shard + tests; wire both paths; PRECOMMIT pinned by full SHA; G-DRIFT vs spp100_arm_span; shard check tested on a synthetic leg; seven year-isolated shards in one message; compose/attest/register/score; RESULT; promotion card per rules 31/35). The parent solves nothing (rule 32(a)).

DO NOT: re-run SPP-84's aggregate pro-rata rebase as-is; pin availability to published totals (rule 13); re-open spp_ct_lole_efor or a CT-only layer (SPP-104 R); tune offer_curve_by_group; touch wefor_multiplier as a lever.
OUT OF SCOPE: the coal outage over-count; commitment posture; gas-price levers; reserve co-opt; topology; other ISOs.
EITHER WAY: owner decisions as clickable cards; merge when the required checks pass (Promotion completeness, Keeper-integrity gates, Rule-28 matrix guard, Ruff, Cache-key guard, shrink-guard); comment once per other-lane red check; archive all shards (rule 33); end with an SPP-106 card.
Housekeeping owed to the owner (sessions cannot delete refs): claude/spp104-2019 … claude/spp104-2025.
```
