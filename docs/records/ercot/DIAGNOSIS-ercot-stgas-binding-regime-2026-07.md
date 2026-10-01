# DIAGNOSIS — the ERCOT binding-regime ST_GAS lane (ERCOT-61, 2026-07-12)

**Question (filed by ERCOT-58 §5, sharpened by ERCOT-60 §7.3).** The keeper
(`2026-07-10-ercot56-nucwin`) serves ~+1.3 GW more top-30 %-net-load-hour load
with ST_GAS than CAMPD gross shows reality did (ERCOT-58 §4: model 4,841 vs
3,555 MW), while `st_netload_drag` forces 25–33 % of class energy under an
all-hours declared window. Mask the binding-hour ST_GAS MWh: do they sit ON
the drag floor (defect = the hinge's high-net-load extrapolation — the hinge
was derived from *overnight* CF vs net-load but applies at all hours) or ABOVE
it economically (defect = the ST_GAS offer curve)?

**Answer: neither — the thermal side is exonerated mechanism-by-mechanism on
measured data, and the binding-regime ST_GAS excess is re-attributed to the
storage/supply side of the ERCOT-58 circle.** The excess is the conservation
shadow of the supply the model is missing at binding hours (chiefly the
evening/day storage under-discharge already adjudicated in ERCOT-60), absorbed
by the cheapest live thermal class. Suppressing it with any thermal-side
mechanism would be residual-fitting on the wrong class (rule 1); the B
counterfactual below *demonstrates* the shuffle. The lane closes with the
keeper unchanged.

Probes (rule-16 2023-only throwaways, NEVER registered):
`scripts/probes/_ercot61_stgas_drag_probe.py` (A — keeper reconstructed from
meta.json, zero deltas; price scores reproduce the keeper exactly: C3a +3.9 %,
C3b 0.133, C3c 171 h) and `_ercot61b_stgas_nodeltas_probe.py` (B — A minus the
ST_GAS offer deltas). Mask: `_ercot61_stgas_binding_mask.py`; A/B:
`_ercot61_ab_compare.py`. Binding regime throughout = top-30 % net-load hours
on the `derive_ercot_rtolcap_forward._net_load` convention (2023: p70 =
40,002 MW, 2,628 h).

## 1. The mask: the floor is NOT the carrier

ST_GAS (plant-group rows) binding-hour decomposition, mean MW (A):

| component | binding | non-binding |
|---|---|---|
| total dispatch | 5,299 | 909 |
| ON the drag floor (P≈min_gen, mech 6, D-2 tolerance) | **881** | 575 |
| drag-raised rows, floor part (dispatched above) | 1,320 | 82 |
| drag-raised rows, economic excess above floor | **1,880** | 121 |
| rows the drag never touches (peaker plants, `_peak` tranches) | **1,218** | 131 |

Only ~17 % of binding-hour ST_GAS MW sits on the floor, and the on-floor MW
concentrates overnight (hod 0–5: ~1.6 GW) — falling to ~450–650 MW exactly in
the hod 10–20 window where the excess lives. Hinge line vs measured CF
(CAMPD ST_GAS, 8,970 MW dominant-class cap):

| window | hours | measured CF | hinge floor-frac | model CF |
|---|---|---|---|---|
| binding & overnight (23–05h, the hinge's own evidence window) | 368 | 0.251 | 0.261 | 0.298 |
| binding & day/evening | 2,260 | 0.420 | 0.302 | 0.638 |
| non-binding & overnight | 2,187 | 0.069 | 0.108 | 0.086 |

In its evidence window the hinge is calibrated (+0.01); at binding day/evening
hours it sits *below* measured CF — the floor is not pushing dispatch above
reality anywhere in the excess window. **(a) is refuted**; the hinge and its
all-hours window stay frozen (rule 23).

## 2. Measured-basis correction: the honest excess is ~+1.0 GW

The ERCOT-58 §4 class table attributes each CAMPD plant's *whole* gross to its
*dominant* model class. The model's synthetic split codes — W A Parish [ST]
34702 (1,565 MW; CAMPD units WAP1–4 under parent ORIS 3470, whose dominant
class is COAL) and Barney M Davis [ST] 49392 (unit 1 under ORIS 4939, dominant
CC_REGULAR) — therefore land their measured ST gross in the *wrong measured
class*. Re-attributed (unit-level CAMPD): measured ST_GAS binding mean 3,555 →
4,006 MW (+388 Parish, +62 Davis); measured COAL 10,437 → 10,049 (model COAL
excess widens +327 → +715); CC_REGULAR 22,333 → 22,271. Plant 56708 ("CFB
Power Plant", 310 MW) is absent from CAMPD entirely — a ~100 MW binding-hour
benchmark coverage wedge, not model excess. Honest per-plant totals
(steam-units-only CAMPD): **model 5,299 vs measured 4,311 binding (+989);
6,424 vs 5,001 day-binding (+1,423)**. Largest single items: Parish-ST +361,
ORIS 3612 +222, peaker-class Ray Olinger +135 / Mountain Creek +109 (no floor,
purely economic), CFB +100 (unmeasured); offset by under-runs at 3611 (−108)
and 3601 (−67).

## 3. B counterfactual: the offer markdowns are not the carrier either — and the measured offer surface corroborates them

The keeper's ST_GAS deltas (econ_low −0.13 / econ_high −0.35 / peak −1.0)
predate the drag (present in ercot42) and looked like the rule-19 leftover the
drag derive doc says it supersedes. Removing them (B) moves almost nothing:

* binding-hour ST_GAS 5,299 → 5,116 (−183 of the ~+1,000 needed); annual
  19.50 → 18.89 TWh (actual 16.83);
* the floor **backfills** part of what the offers give up (on-floor 881 →
  1,068 MW binding; forced share 0.299 → 0.342);
* the displaced energy just shuffles inside the thermal stack (CT_PEAKER
  +100, CC_REGULAR +48, COAL +21 at binding) — conservation in action;
* prices barely move and move the wrong way (C3a +3.9 → +4.3 %, C3b 0.133 →
  0.135, C3c tail unchanged; evening–morning spread +0.35 $/MWh).

The measured 60-Day DAM submitted curves (GSREH/GSNONR/GSSUP, online hours,
2023) explain why — **real ST_GAS offers are flat at ~marginal cost all the
way to HSL**: median $23.9/$25.1/$26.7/$27.1/$27.4 at 50/70/85/95/100 % of
HSL at binding hours; 97 % of binding-hour online offered MW priced ≤ $37,
99 % ≤ $60. At 2023 gas that is ~1.0× base-HR SRMC with no upper-range
hockey stick. The keeper's *delta'd* bands (0.91/1.02/1.20/3.20) are therefore
**closer to the measured offer surface** than the un-delta'd base
(0.91/1.15/1.55/4.20): the deltas are measured-corroborated, not a residual
leftover. Rule 14: keep them; B is rejected. **(b) is refuted.**

## 4. The rest of the operating envelope is also consistent — measured, no solve

From the 60-Day DAM Gen Resource Data (39–46 GS resources, 10.4 GW p98
rating) and unit-level CAMPD, 2023 binding hours:

* **Availability:** live (non-OUT) HSL 7,492 MW — 28 % of the fleet rating is
  on outage at binding hours; the model's CAMPD-window outage overlay leaves
  it a comparable live fleet. Model binding dispatch (5,299) is well inside it.
* **Commitment:** DA COP online HSL only 3,373 MW (the fleet is mostly
  status-OFF even at binding); RT commitment (CAMPD online units ×
  month-conditional p95 capability) 6,371 MW binding / 6,461 day-binding —
  above the model's dispatch. A measured commitment operating rule exists
  (committed frac = 0.0179 × netload_GW − 0.303, r 0.80, monotone 0.044 →
  0.770 across deciles) and is recorded here as the derive basis for an
  optional future `gas_st_commitment_ceiling` (the upper half of the drag's
  commitment envelope; availability-style pmax cap, same driver/window/forward
  story as the floor). It would bind only against the model's hod 14–16 surge
  (~0.2–0.4 GW) — it is NOT the excess's carrier and is not built now
  (rule 19: nothing else currently caps ST_GAS; rule 1: don't add structure to
  chase a residual it cannot close).
* **AS withholding:** measured DAM AS-up awards on ST_GAS at binding hours are
  trivial — 174 MW (NonSpin 130, RRS-PFR 31, RegUp 12). The committed fleet's
  part-loading is not a reserve reservation the model fails to hold.

## 5. Determination and disposition

* **The binding-regime ST_GAS excess (+1.0 GW honest basis) is not a thermal
  defect.** Floor, offers, availability, commitment and AS are each consistent
  with measured operating data; the B counterfactual demonstrates that
  suppressing ST_GAS merely relocates the excess within the thermal stack.
  The excess is the thermal fleet absorbing the binding-hour supply the model
  is missing — chiefly the evening/day battery discharge (measured 1–2 GW at
  2023 evening peaks vs model ~0.15 GW; the ERCOT-58 §4 circle, ERCOT-60
  thread-1) — so the lane hands back to the storage/price-formation side.
  Rule 1 applies squarely: a structurally-faithful mechanism stack is not
  re-tuned because the residual sits on it.
* **Keeper stays `2026-07-10-ercot56-nucwin`, unchanged.** Both probes are
  rule-16 throwaways (2023-only, never registered).
* **ERCOT-58 §4 numbers carry two benchmark-side corrections** for future
  rounds: the Parish/Davis [ST] split-code attribution (+451 MW to measured
  ST_GAS, −388 COAL, −62 CC at binding) and the CFB-56708 CAMPD coverage
  wedge (~100 MW). On the keeper config the CT_PEAKER counterpart is −310 MW
  binding (not −645 — that figure was measured on the ercot58-joint config,
  whose plan-withholding shifts dispatch).
* **Filed, not built:** (i) the `gas_st_commitment_ceiling` derive basis (§4)
  if a future round needs the hod-14–16 surge shaved on structural grounds;
  (ii) a measured ST_GAS DAM offer-surface derive (extending
  `derive_ct_offer_surface.py` to the GS types) to replace the fitted base
  bands + deltas with the measured flat curve outright — cosmetic for
  dispatch (the delta'd bands already sit on it) but it would retire two
  fitted DOF from the ledger; (iii) the peaker-class ST over-run (+245 MW
  binding on no-floor plants) — below the 2 % materiality line.
* **The storage-side lane continues** (C5c monthly shape stays its own
  root-cause item; the ERCOT-58 v3 realized-room RTORPA re-probe stays parked
  — its room is bounded by this same supply-mix gap, now localized to
  storage/supply rather than any ST_GAS mechanism).
