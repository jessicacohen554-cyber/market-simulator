## 2026-07-12 — ERCOT-61: the binding-regime ST_GAS drag-floor lane adjudicated (two rule-16 probes + measured-data-only checks) — the thermal side is EXONERATED mechanism-by-mechanism; the +1.3 GW (honest +1.0 GW) binding-hour ST_GAS excess is the conservation shadow of the missing storage/supply at binding hours, not a floor or offer defect; keeper stays ercot56-nucwin unchanged

**Task (the ERCOT-60 §7.3 filed next lever, this session).** Mask the
keeper's binding-hour (top-30 % net-load) ST_GAS MWh: ON the
`st_netload_drag` floor (defect = the hinge's high-net-load extrapolation)
vs ABOVE it economically (defect = the offer curve)? Full workings:
`docs/DIAGNOSIS-ercot-stgas-binding-regime-2026-07.md`.

**Probes (rule-16 2023-only throwaways, never registered).**
`_ercot61_stgas_drag_probe.py` (A: ercot56-nucwin reconstructed from
meta.json, zero deltas — price scores reproduce the keeper exactly: C3a
+3.9 %, C3b 0.133, C3c 171 h; ST_GAS class total 19.4997 TWh matches the
committed D-2 byte-for-byte) and `_ercot61b_stgas_nodeltas_probe.py` (B: A
minus the pre-drag ST_GAS offer deltas).

**Mask verdict — (a) refuted.** Only 881 of 5,299 binding-hour ST_GAS MW sit
ON the floor (concentrated overnight); the excess window (hod 10–20) carries
just ~450–650 MW on-floor. In the hinge's own evidence window (binding
overnight) the line is calibrated (floor-frac 0.261 vs measured CF 0.251);
at binding day/evening it sits BELOW measured (0.302 vs 0.420). Hinge and
window stay frozen (rule 23).

**Counterfactual verdict — (b) refuted, and the deltas are
measured-corroborated.** B closes only −183 MW of the ~+1,000 binding excess
(annual 19.50 → 18.89 vs actual 16.83 TWh), the floor backfills (on-floor
881 → 1,068 MW), the displaced energy shuffles inside the thermal stack
(CT +100 / CC +48 / COAL +21), and C3a worsens (+3.9 → +4.3 %). The measured
60-Day DAM submitted curves for the GS types show why: real ST_GAS offers
are FLAT at ~SRMC to HSL (binding-hour median $24–27 across 50–100 % of HSL;
97 % of online offered MW ≤ $37) — the keeper's delta'd bands
(0.91/1.02/1.20/3.20) sit closer to the measured surface than the un-delta'd
base (0.91/1.15/1.55/4.20). Rule 14: the deltas stay.

**Measured-basis corrections (benchmark side, for future rounds).** The
ERCOT-58 §4 class table mis-attributes the split-code plants: W A Parish
[ST] 34702 and Barney M Davis [ST] 49392 report under parent ORIS 3470/4939,
whose gross lands in COAL/CC_REGULAR. Honest measured ST_GAS binding mean
3,555 → 4,006 MW; model COAL binding excess widens +327 → +715. CFB 56708
(310 MW) is absent from CAMPD (~100 MW coverage wedge). Honest ST_GAS
excess: **+989 binding / +1,423 day-binding MW**. CT_PEAKER counterpart on
the keeper config: −310 MW (the −645 was the ercot58-joint config).

**Envelope checks (measured only, no solve).** Binding hours 2023: live
(non-OUT) DAM HSL 7,492 MW (28 % of the 10.4 GW rating on outage); DA COP
online HSL only 3,373 MW (the fleet is mostly OFF day-ahead even at
binding); RT committed capability (CAMPD online × month-p95) 6,371 MW ≥
model dispatch; measured AS-up on ST_GAS 174 MW (trivial). A measured
commitment operating rule exists (committed frac = 0.0179·netload_GW −
0.303, r 0.80, deciles 0.044 → 0.770) and is recorded as the derive basis
for an optional future `gas_st_commitment_ceiling` — it would bind only on
the model's hod 14–16 surge (~0.2–0.4 GW), so it is filed, not built
(rules 1/19).

**Determination.** The binding-regime ST_GAS excess is NOT a thermal-side
defect: floor, offers, availability, commitment and AS are each consistent
with measured operating data, and the B counterfactual demonstrates that
suppressing the class merely relocates the excess within the thermal stack.
The excess is the thermal fleet absorbing the binding-hour supply the model
is missing — chiefly the evening/day battery discharge (ERCOT-58 §4 circle,
ERCOT-60 thread-1) — so the lane hands back to the storage/price-formation
side. **Keeper stays ercot56-nucwin**; nothing registered (both probes
rule-16). The ERCOT-58 v3 realized-room RTORPA re-probe stays parked; C5c
monthly shape stays its own root-cause item.

**Holdouts / governance.** No solve, score, or intake outside 2023 (train
year); no offer curve, sigmoid, floor, hinge, or derive-script value changed;
no dashboard registration (rule 16); ORDC tariff params untouched (rule 26).
