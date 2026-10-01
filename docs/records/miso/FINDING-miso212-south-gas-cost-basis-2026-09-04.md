# FINDING miso-212 — THE SOUTH GAS DELIVERED-COST BASIS: there is NO South-specific basis error — the model's South gas is priced above the market that ran it by a cost CONVENTION the whole ISO shares (average delivered EIA-923 cost, not spot commodity), plus a rule-19 layering worth ~$3/MWh; the G-5 trigger is met on the letter by a lever this lane cannot arm; `miso_south_gas_delivered_cost_basis` minted **R**, the ISO-wide question SIZED and left in owner court, the layering NAMED for miso-213; NO SOLVE (2026-09-04)

**Keeper unchanged: `2026-09-04-miso-210-clock`** (bundle `miso210_clock_B`). NO LP, NO
FIELD, NO MECHANISM ARMED, NO RUN REGISTERED. PREREG
`PREREG-miso212-south-gas-cost-basis-2026-09-04.md` pushed BLIND at `db893e8e`.
Instruments: `scripts/probes/_miso212_south_gas_cost_basis.py` (first pass) and
`_miso212_followup.py` (one disclosed post-hoc correction, §6) →
`results/calibration/_miso212_south_gas_cost_basis.json`. Rule 22: 2023–2025 only.

---

## 1. Verdict in one paragraph

In the 177 Jun–Jul 2025 hours where MISO's RDT bound South→North (miso-211's object), the
model's South gas fleet leaves **3.27 GW idle within $20 of the model's South price**
while the market ran 3.7 GW more gas than the LP. That block is **CT peakers (1.53 GW) and
gas steam (1.31 GW)**, not combined cycles, and mostly **econ tranches (2.26 GW)**, not
duct-burner peaks. Its bid decomposes (capacity-weighted) into **fuel $43.3 + VOM $3.5 +
fixed offer margin $2.8 + startup $2.4 = $52.0**, against a South price of $48.3. The fuel
leg sits **$8.7/MWh above Henry Hub spot**: the plants' own EIA-923 delivered prints are
**+$0.55/MMBtu over HH** and the mean-zero zonal basis adds **+$0.29** on top of them.
Neither is a *South* error. The Midwest fleet's prints sit **+$0.73 over HH** while Chicago
Citygate traded **−$0.26 under HH** in the same weeks — the same convention over-prices the
Midwest by more. Replacing every South tranche's fuel with HH spot recovers **2.10 GW** of the
3.27 (2024: 2.03; 2023: 1.56) — over the pre-registered 2.0 GW G-5 trigger in 2025 by
0.1 GW — but that "correction" is a change of **cost convention** (average delivered →
marginal commodity), ISO-wide and cross-ISO, already ledgered adverse-sign and owner-court
at miso-156/miso-189, not a mis-measured South input. **No South-specific measured
correction reaches 1 GW**: the zonal-basis layering on 923-priced plants is 0.78 GW
(2024 0.37, 2023 0.46), the CAMPD heat-rate re-grounding 0.36 GW. The market's own South
RT offer stack prices the measured generation level at **$30 p50** against the model's
marginal gas MW at **$66** — the residual after every measured leg is offer conduct, as
P-7 said, but the fuel convention is a larger share of it than the prereg allowed.

## 2. The block (2025 shoulder, 177 real S→N binding hours; capacity-weighted)

| | GW | share |
|---|---|---|
| Model South gas economic at the South price | 15.24 | |
| Measured South gas (sr_gfm) | 18.90 | |
| **Idle within $20 of the South price ($48.3)** | **3.27** | |
| — CT_PEAKER | 1.53 | 47 % |
| — ST_GAS | 1.31 | 40 % |
| — CC_REGULAR | 0.23 | 7 % |
| — CHP (CC/CT/ST) | 0.20 | 6 % |
| by band: econ / committed / peak | 2.26 / 0.76 / 0.25 | 69 / 23 / 8 % |

**P-1 WRONG on both counts** (CC ≥ 50 % predicted, actual 7 %; peak ≥ 30 %, actual 8 %).
The idle-within-$20 gas is the *cheap end of the peaking fleet*, not the duct block — which
is why fuel convention, not offer shape, dominates the decomposition below. 2024 / 2023
compositions are the same within 0.2 GW per class.

## 3. Legs beside their measured counterparts (2025 shoulder block; §6 correction applied)

| leg | model | measured counterpart | gap on the block |
|---|---|---|---|
| Delivered gas `F` | **$4.08/MMBtu** | HH daily spot $3.23 | **+$0.84** = **$8.7/MWh** at the implied 10.66 HR |
| — of which the plant's 923 print over HH | +$0.55 | (the print IS the measured input) | $5.9/MWh |
| — of which the zonal-basis increment (`miso_zonal_gas_basis`, South leg) | +$0.29 | applied on top of the print | **$3.1/MWh** |
| — the un-overlaid trajectory (annual HH × season × daily shape) | −$0.48 vs HH | | (would UNDER-price) |
| Heat rate, CC_REGULAR | 1.04 × CAMPD burn (16 plants) | Σ heat / Σ gross, same hours | ≤ $1/MWh |
| Heat rate, CT_PEAKER | 1.02 × (12 plants) | | ~$0.5 |
| Heat rate, ST_GAS | 1.05 × (9 plants) | | ~$2 |
| Fixed offer margin (`markup_hr × anchor`) | $2.8 | not measured (miso-179/180 R/I) | |
| Startup amortization (P1 − base) | $2.4 | not measured | |
| VOM | $3.5 | | |

Fleet-wide (all available South gas, capacity-weighted): F − HH **+$0.62** (print +$0.34,
basis +$0.29). **Midwest gas fleet: F − HH +$0.53 = print +$0.73 with the basis −$0.20** —
the Midwest 923 prints over-shoot spot by MORE than the South's, while Chicago Citygate
traded **−$0.26 under HH** (Jun–Jul 2025; −$0.43 in 2024, −$0.17 in 2023;
`gas-prices/miso_citygate_daily.csv`). The over-pricing is an ISO-wide property of the
average-delivered-cost convention, not a South basis.

**Prior scored:** P-2 F = HH + 0.35–0.55 **WRONG** (+0.84 block / +0.62 fleet, above the
range); layering $1.5–3/MWh **RIGHT at the edge** (2025 $3.1; 2024 $1.3; 2023 $1.5); fuel
leg ≤ $4 of the $17 **WRONG** ($8.7). P-3 CC within ±7 % **RIGHT** (1.04); ST_GAS ≥ 10 %
above **WRONG** (1.05). P-4 markup $2–5 **RIGHT** (2.8). P-5 startup $3–10 **WRONG-low in
2025** (2.4; 3.0–3.3 in 2023/24). Per-plant 923 tail (§5 of the prereg): the probe recorded the
block's print excess capacity-weighted (+$0.55) and the fleet's (+$0.34), not the per-plant
distribution — the concentration question is NOT answered here and is carried to miso-213's
phase 0 (which needs the per-plant 923-priced / fallback split anyway).

## 4. The static counterfactuals — what each measured correction recovers

GW of South gas that becomes economic at the model's own South price (the South price held
fixed, so an upper bound on the LP's response), 2025 shoulder / 2024 shoulder / 2023
shoulder, with the tails in brackets. Implied-heat-rate basis (§6):

| counterfactual | 2025 | 2024 | 2023 | marginal MW bid p50 at measured gas level, 2025 |
|---|---|---|---|---|
| baseline | 0 | 0 | 0 | $66.4 |
| **(a) fuel → HH daily spot** (convention change) | **2.10** [1.32] | **2.03** [2.00] | 1.56 [1.49] | $54.0 |
| (b) zonal-basis increment removed (rule-19 layering) | 0.78 [0.32] | 0.37 [0.35] | 0.46 [0.61] | $61.6 |
| (c) heat rate → CAMPD burn | 0.36 [0.32] | 0.18 [0.14] | 0.45 [0.33] | $65.8 |
| (a)+(b)+(c) all measured | 2.45 [1.53] | 2.31 [2.02] | 1.97 [1.73] | $53.6 |
| (d) fixed margin zero — NOT measured | 0.71 | 0.88 | 0.92 | |
| (e) startup zero — NOT measured | 0.40 | 0.53 | 0.62 | |
| everything (a–e), first-pass basis | 3.17 | 3.62 | 3.35 | $46.6 |

Even with every leg — measured and unmeasured — zeroed to spot, the marginal MW at the
measured level still bids **$46.6** against an actual South hub price of **$41.6**.

**P-7 WRONG on the letter, right in kind.** One input, (a), carries ≥ 2.0 GW in 2025
(2.10) and holds sign in 2023/2024 (1.56 / 2.03) — the G-5 condition as written. The
combined measured recovery (2.45 GW) is above the predicted 0.8–1.5. P-8 (same leg
ordering every year) **RIGHT**: (a) ≫ (b) ≈ (c) in all three years.

## 5. Why G-5 did NOT fire, stated against the prereg

The prereg's G-5 named "a delivered-price basis (923 print vs spot, or the zonal-basis
layering) or a heat-rate basis" and said the correction would be kept whichever way C3a
moves. Counterfactual (a) clears its number. It is nonetheless **not this lane's to arm**,
for reasons that are about scope, not about C3a:

1. **It is not a mis-measured input; it is a different input.** The 923 print is the
   plant's *average* delivered cost (commodity + demand charges + contracted transport,
   amortized over the month's takes). HH spot + variable transport is the *marginal*
   commodity cost of the next MMBtu. Both are measured. Which one belongs in a dispatch
   offer is a **methodology convention** — miso-189 §7.3 named exactly this
   ("marginal-vs-average delivered-cost question … a cross-ISO methodology change, every
   ISO prices F923 average delivered cost, needing its own charter"), and the
   `gas_hub_basis_overlay` R cell carries it as "owner-court, cross-ISO". This session's
   contribution is to **size** it: 2.10 / 2.03 / 1.56 GW of the South's 3.3 GW gap, and
   an ISO-wide over-cost of ~$1/MMBtu in the Midwest (print +0.73 vs Citygate −0.26).
2. **Rule 25.** The convention is applied by `gas_plant_monthly_fuel_pricing`, which is
   ISO-agnostic; a MISO-South-only exception would be a per-zone fuel convention with no
   measured identification of why the South's marginal cost is spot while the Midwest's is
   average — the very thing rule 25 forbids. A MISO-wide switch touches every gas tranche
   in the ISO and miso-156's adjudication (which the prereg said would NOT be re-tested).
3. **The sign is adverse to C3a in every year** — that is NOT the reason (rule 14 states
   the posture), but it is why the owner ruling must come before the solve, not after: a
   lane that arms an ISO-wide adverse-sign convention change to answer a South-zone
   question has chosen the ISO's methodology on a sub-regional residual.

So the pre-registered R-branch applies to the object the row names — a **South-specific
delivered-cost basis** — and the finding is that **no such thing exists**: the South's
prints are *less* over spot than the Midwest's. `miso_south_gas_delivered_cost_basis` is
minted **R** (field-less row, the miso-182/184/211 precedent). The ISO-wide convention is
recorded with its size on `gas_hub_basis_overlay` (evidence only; verdict unchanged) and
put to the owner (§8). **This is a deviation from the prereg's decision rule as literally
written and is disclosed as one.**

## 6. Instrument correction, disclosed (post-hoc block in the JSON)

The first pass reconstructed `mc` as `HR_tr × F + VOM + markup_hr × anchor` and found a
max identity residual of **230 / 739 / 1,525 $/MWh** (2023 / 2024 / 2025) against the LP's
own `mc`. Located (`_miso212_followup.py`): the residual is exactly `markup_hr × F` on the
139 tranches that carry a positive markup — the prereg §1 wrote the identity correctly
(`HR_phys × F + markup × anchor`, `apply_gas_offer_margin`), the probe used the *offer*
heat rate where the *physical* one belongs. Largest on the CT_PEAKER `_peak` tranches
(phys 1.0× vs offer 4.0×, so the LP's bid moves with ¼ of the offer heat rate; the
1,525 outlier is one CT peak tranche in a non-summer hour whose delivered `F` reads
$48/MMBtu — a 923-print outlier or the dual-fuel path; outside the window, not pursued),
$0.8–$3 on CT_CHP/ST_GAS econ and CC econ. Inside Jun–Jul the max is 264. **Effect on the
result:** the block's fuel sensitivity is the implied 10.66 HR, not 11.58; (a) falls 2.28 →
**2.10** (2024 2.22 → 2.03; 2023 1.73 → 1.56), (b) 0.85 → 0.78, (c) 0.38 → 0.36. The
first-pass numbers stay in the record under `years`, the corrected ones under `post_hoc`;
every number quoted above is the corrected one except the "everything (a–e)" row, whose
unmeasured legs (d)/(e) were computed on the first-pass basis and is quoted as such.

## 7. The market's own declaration (P-6, RIGHT)

MISO's masked RT submitted-offer book (`data/raw/miso-energy-offers/rt/`, Region = South,
Jun–Jul 2023–2025, 183 days fetched this session; curated by
`curate_miso_energy_offers.py`, outcome columns dropped by construction; fuel-blind and
region-, not zone-, resolved):

| | 2025 | 2024 | 2023 |
|---|---|---|---|
| measured South generation in the binding hours | 29.9 GW | 28.1 | 28.8 |
| **South offered stack price at that quantity, p50** | **$30.0** | $22.8 | $27.7 |
| actual South hubs | $41.6 | $27.2 | $32.4 |
| model whole-South-stack `mc` at that quantity, p50 | $212 † | $45.3 | $47.2 |
| MW offered at ≤ the model's South price | 36.3 GW | 33.1 | 32.2 |
| model capability at ≤ its South price | 25.3 GW | 25.4 | 26.6 |

† 2025 the model's whole stack at 29.9 GW is already into its peak wall (capability at the
South price is 25.3 GW). The market offered **~11 GW more supply at ≤ $48** than the model
carries at that price. The comparison is whole-stack (coal and nuclear self-schedules
included), so it bounds, rather than measures, the gas offer level — but its direction is
unambiguous and consistent with miso-211's "priced out" reading; the against-interest
outcome of prereg §5 (offers clustered near $60+) did NOT occur.

## 8. What this licenses, and what it hands on

* **Licensed: nothing armed.** `miso_south_gas_delivered_cost_basis` **R**.
* **Owner-court, now SIZED (not a lane lever):** the marginal-vs-average delivered-cost
  convention. Question for the owner, stated plainly: *should gas offers be priced at the
  plant's EIA-923 average delivered cost (the current, every-ISO convention) or at
  marginal commodity (hub spot + variable transport)?* Evidence: it is 2.1 / 2.0 / 1.6 GW
  of MISO-South's 3.3 GW shoulder gap; it over-prices the Midwest fleet by ~$1/MMBtu vs
  Chicago Citygate; its sign is adverse to C3a in every year (miso-156). A ruling FOR
  marginal commodity is a spec change (methodology §1.7 fuel convention) with a cross-ISO
  A/B program, not a MISO session. A ruling AGAINST closes the item and the residual is
  offer conduct by construction.
* **Named for miso-213 — the rule-19 layering repair, MISO-scoped, single-delta:**
  `miso_zonal_gas_basis` (K, miso-119) adds its mean-zero zonal increment to EVERY gas
  tranche, including the plants whose `F` was just set from their own 923 print — a print
  that already embeds the regional delivered premium. Two mechanisms price one
  phenomenon (rule 19 `[R-ONE-MECH]`). Size on the block: **0.78 GW / $3.1/MWh** (2025;
  2024 0.37 / $1.3; 2023 0.46 / $1.5); sign: South +0.29 (over-priced), Midwest −0.20
  (under-priced) — so the repair *widens* the model's South-vs-Midwest gas cost differential
  the wrong way for the object unless the fallback-priced plants (where the basis is the
  only regional signal and is legitimate) are kept. Charter: phase 0 measures the 923-priced
  vs fallback capacity share per zone and the increment each receives; the arm skips the
  increment on 923-priced tranches only; single-delta A/B on the miso-210 ten-gate scorer
  with the South boundary net / S→N flow / Indiana−South spread pre-registered. Predicted
  small and C3a-adverse in the South; it is a structural repair regardless (rule 1).
* **Not chartered:** offer margin / startup (unmeasured, R/I at miso-179/180); the CAMPD
  heat-rate re-grounding of ST_GAS (0.36 GW; the class is 1.05× CAMPD, within the
  measurement's own noise — ERCOT-146-class hazard).

## 9. Reported against interest

1. The G-5 numeric trigger WAS met (2.10 ≥ 2.0 in 2025, sign held) and the session did not
   solve. §5 gives the reason; a reader who holds the prereg to its letter should read
   this as a governance deviation, disclosed, not as a null result.
2. The idle-within-$20 block is a static object at the model's own South price. A fuel
   change that lowers the South stack also lowers the South price; the GW figures are
   ceilings on the LP's response, not its response.
3. The counterfactual (a) HH spot carries NO transport adder; the true marginal delivered
   cost is HH + variable transport (~$0.10–0.30 in the Gulf), so (a) slightly overstates
   even the convention's own recovery.
4. The whole-stack offer comparison is fuel-blind; a share of the $30 vs $66 spread is
   coal/nuclear self-scheduling that the model also represents at low mc.
5. The first-pass identity error (§6) was caught by the probe's own check and corrected;
   had the check not been written, (a) would have been reported as 2.28 and the deviation
   in §5 would have looked less marginal than it is.

## 10. Governance

Rule 15: zero-solve, nothing registered (the miso-156 no-solve precedent). Rule 28(a): no
R/I/G cell re-tested (`gas_hub_basis_overlay` R, `miso_offer_*` R/I untouched). Rule
28(b)/(c): `miso_south_gas_delivered_cost_basis` base row + six cells (MISO **R**, five
`.`); evidence appended to `gas_hub_basis_overlay` (size of the owner-court residue),
`miso_zonal_gas_basis` (the layering, named), `rdt_tcdc` (object status); §5.4 queue stamp.
Rule 25: MISO's verdict only. Rule 22: 2023–2025 (the offer fetch refused other years by
construction). Rule 13: 923 prints, HH spot, CAMPD, PBC, the RT offer book — read as
diagnostics, none an LP input. Rule 27: blob-verify on push. Data: the RT offer payload is
gitignored (corpus README governs); `data/clean/energy-offers/MISO/RT/` is derived.

Next shorthand: **miso-213**.
