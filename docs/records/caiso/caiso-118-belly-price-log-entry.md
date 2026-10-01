# CAISO belly price-formation (caiso-118) — calibration-log entry (append to docs/calibration-log/caiso.md)

> Delivered as a handoff doc: `docs/calibration-log/caiso.md` is large and
> parallel CAISO sessions append to it, so a full-file API push would risk
> clobbering their entries (the caiso-114/115/116/117 precedent). Merge this
> single entry into caiso.md on integration.

## 2026-07-24 — caiso-118 BELLY PRICE-FORMATION derive: both suspects REFUTED; the belly over-price + over-import are ONE defect (the model UNDER-COMMITS belly gas). NO SOLVE, nothing registered. Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a})

**Derive-first (rule #1), measurement-only, register nothing** (the caiso-115/116/117
precedent). Full finding: `results/calibration/FINDING-caiso118-belly-price-undercommit-2026-07-24.md`.
Reproduction: `scripts/probes/_caiso118_belly_price_derive.py` (no LP; keeper-proxy
`caiso104_m1_B` hourlies + raw EIA-930 CISO + `load_renewable_profiles` +
`measured_import_hub_prices` + `measured_corridor_flow_envelope`).

**Charter:** the caiso-117 redirect — make the model belly clear near actual ~$15
(from ~$26) before re-arming the belly VOLUME cap, testing one of two named
suspects: (1) a curtailable-solar $0 marginal rung, or (2) pricing belly imports
at the measured (low) belly hub.

**Both suspects refuted; a third, unifying mechanism identified.**

- **Suspect 1 (solar rung) — REFUTED.** `caiso_solar_endogenous_spill` is ON, so
  the deliverability derate is already SKIPPED and the LP gets full solar
  potential. Measured belly solar spill is only **0.5–2.0%** — solar is already at
  its bound (inframarginal). No suppressed pool; a $0 rung is inert; re-enabling
  the derate would REMOVE solar and RAISE the belly. The model even dispatches MORE
  utility solar than reality generates (47.2 vs 44.6 TWh).
- **Suspect 2 (belly-hub import reprice) — REFUTED/COUPLED.** The model's OWN
  solved WECC border duals are already low in the belly (PNW $2.6–6.3, DSW
  $14.6–28.7) and the belly hub series it reads is already DSW $10.5 (2024). The
  cheap border is corridor-CAPPED (import at/near the corridor belly cap) and the
  next economic import tranche ($36 ladder) is above CA's domestic gas, so CA
  clears at gas. Repricing the remaining tranches down is a VOLUME lever (worse
  C5a) — not a C5a-neutral price lever.
- **The lever — the committed-gas belly STATE.** Killer comparison (model vs
  actual belly gas): 2023 4.3 / **8.5 GW**, 2024 3.7 / **9.6 GW**, 2025 2.9 /
  **10.5 GW**. Reality runs **2–3.6× MORE** belly gas than the model yet clears
  LOWER ($15 vs $26) — its committed gas bids min-load DOWN (must-take, never
  marginal), so the belly clears at curtailed solar / the min-load block. The
  model economically backs gas off to a ~2 GW duck trough and OVER-IMPORTS (3.1–3.9
  vs actual 0.7–1.8 GW), so full-MC gas/import sets $26. **C3a-belly-overprice and
  C5a-belly-overimport are the SAME defect** (the missing committed STATE), not two
  coupled-and-opposed lanes. The keeper's `caiso_ra_mustoffer` bridge floors only
  3.2–3.7 TWh/yr (~1.5 GW belly) vs reality's ~10 GW — under-committed by ~5–6 GW.
  This is the ERCOT-63 result ("the model needs the STATE, not the PRICE").

**Why this explains the caiso-117 coupling.** The belly VOLUME cap fixes C5a but
breaks C3a (2025 +8.6 → +13.2%) because it cuts imports and lets **full-MC** gas
fill (raising the belly). With the committed min-load bid-down STATE in place,
cutting imports and running committed gas at its bid-down min-load fixes BOTH — the
volume cap and the price lane stop fighting.

**Redirect (caiso-119).** Single physics-grounded C5a-neutral-or-better delta:
raise the CAISO committed-gas belly floor to the MEASURED committed level (CEMS /
CAISO 60-Day DAM disclosures — the ERCOT-63 template: measured committed-CC min-load
p50 × the P0-committed belly fleet), extending `caiso_ra_mustoffer` /
`caiso_ra_p1_floor_fleet` toward reality's ~8–10 GW. Gate: belly LMP → ~$15, belly
gas → 8–10 GW, belly import → ~1.3 GW (C5a↑), C3a STAYS PASS all years incl 2025,
C3b↑, evening untouched. Guardrails: cited D-4 window + C8 forced-energy budget (at
~10 GW commitment CC_REGULAR exceeds the 30% merchant cap → needs the rule-14 v2.2
grounded-above-budget escalation, D-4 off-window clean + D-1 shape faithful; score
it, don't assert it). KILL if the level is residual-fitted (rule 13), forces gas in
hours the disclosures say the fleet is off (rule 12), or breaks the evening. THEN
re-arm `caiso_belly_import_cap` jointly; LOYO within 2023–2025 before promotion.

**DO-NOT-REDO (added):** curtailable-solar $0 belly rung / re-enabling the solar
deliverability derate (solar 98% absorbed; inert / raises price); repricing belly
imports to the border hub as a belly-PRICE lever (border already cheap +
corridor-capped; pulls volume, worse C5a).
