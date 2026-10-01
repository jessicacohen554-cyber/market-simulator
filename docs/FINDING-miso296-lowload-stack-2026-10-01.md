# FINDING — miso-296: at low load the model's marginal unit is gas CC and the seam; the real market's is coal. The gap is the offer level at the margin, not quantity. No solve.

```
LANE    : miso-296 (owner ruling 2026-10-01, miso-295 card: "C3a 2020 low-load stack (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Keeper P1 hourly sidecars, zone-resolved hub RT, measured zonal demand, EIA-930, CAMPD,
          Chicago Citygate daily, fleet-only rebuilds of the keeper recipe (base and bid stacks)
PROBE   : scripts/probes/_miso296_lowload_stack.py  (~6 min/year; blocks A-E)
OUTPUT  : results/calibration/_miso296_lowload_stack.json
SOURCES : Potomac Economics, MISO State of the Market Reports: 2020 (Table 1 p.6; Appendix Fig. A6 p.7-8),
          2022 (Table 1 p.6), 2023 (Table 1 p.6), 2024 (Table 1 p.6; Table 7 p.45). Fetched from
          potomaceconomics.com; cited, not committed, not a model input (rule 13). Page numbers are printed pages.
CELLS   : no verdict moves; no R/I/G cell re-tested (rule 28). Evidence notes added to
          gas_marginal_commodity_pricing (O), gas_variable_transport (O), seam_neighbour_hourly_ladder (K)
```

## 1. Answer

1. **C3a 2020 (+11.6 %, +$2.54/MWh) is a level shift over the bottom four load quintiles, not a night object
   and not a tail object.** Quintiles 1–4 each contribute +$0.67 to +$0.73 of the +$2.54; quintile 5 gives back
   −$0.26. Night hours (h0–5) carry +$1.09 and day hours +$1.45. Hours with an actual price below $10 contribute
   +$0.25; hours between $10 and $20 (5,032 of them) contribute +$3.21.
2. **Who is marginal.** In the bottom two load quintiles the model's marginal row is gas in 65 %, the seam
   (PJM/SPP/South import ladders) in 28 % and coal in 7 % of hours (bid stack, 2020). The IMM reports that coal set
   MISO's system marginal price in **40 % of 2020 intervals, "generally in off-peak hours"**, gas in 57 %
   (2020 SOM Table 1). Over all hours the model has coal marginal 25 % and the seam 21 %; the seam is not a
   price-setting category in the IMM table at all.
3. **What the marginal offer is made of (2020, quintiles 1–2).** When a CC_REGULAR econ tranche is marginal
   (997 of 3,504 hours) its offer is $18.14 = 7.41 MMBtu/MWh × $2.165 + $2.00 VOM, with zero startup markup.
   The same day's Chicago Citygate flow-day price is $1.72, so the fuel print carries a **+$0.34/MMBtu = +$2.57/MWh
   wedge** over the traded hub, against a bid-minus-actual gap of +$3.66 in those hours. The wedge is 70 % of the
   gap at the CC margin. This is the miso-224/225 object (`gas_marginal_commodity_pricing`,
   `gas_variable_transport`, both O; the owner-ruled form is hub + variable transport, of which the measured
   variable leg for CC_REGULAR is $0.21/MMBtu).
4. **Coal is not at the margin because the model's coal offer curve has a hole where the real one is flat.**
   In the low-load hours of 2020 the model's coal runs 18.8 GW: mustrun 9.3 GW at $4.5 (VOM only), committed
   8.7 GW at a cap-weighted $9 (the regulated take-or-pay discount), then econ 6.4 GW PRB / 3.2 GW BIT at a
   cap-weighted **$29.6** (HR 13.0 × $1.91 + $4.50). Nothing is offered between ~$9 and ~$17. CAMPD coal in the
   same hours is 17.8 GW. The real fleet, with 1 GW less on, set the price at ~$15. The model's cheapest
   undispatched coal econ MW sits $0.13 above the clearing price — coal econ is co-marginal at its own level,
   which is ~$10 above the real coal-marginal price.
5. **Quantity is not the object.** Model minus CAMPD in the low-load hours: CC_REGULAR +0.2 GW, COAL_PRB +1.0,
   COAL_BIT −0.1, ST_GAS −1.1, CT_CHP −0.7 (host-steam basis), CT_PEAKER −0.3. The model never curtails wind and
   never dumps (0 hours); the actual price is below $10 in 2.8 % of hours and the model's in 0.0 %, but those
   hours carry only +$0.25 of the +$2.54. Imports: model 5.5 GW vs EIA-930 6.7 GW net import.
6. **West/Plains congestion is a distinct, adjudicated part.** The zone error is West +$5.87, Plains +$4.04,
   South +$3.12, Illinois +$2.15, Indiana +$1.20, East +$0.04. If West and Plains carried the rest-of-footprint
   error, C3a 2020 would read about +8.5 % (PASS). That part is the wind-congestion separation of the West hub
   (`internal_congestion_split`, G, killed 2026-10-01) and is not re-opened here.

(Section 1 is 2020; §§2–6 carry every year. Where a number is quoted without a year it is 2020.)

## 2. Where the C3a 2020 error lives (block A)

TABLE_A

## 3. Who sets the price: IMM vs model (block B)

TABLE_B

Reading:
- The IMM's coal share is the share of five-minute intervals in which a coal resource set the SMP; the model's is
  the share of hours in which a coal row is the marginal row of a merit clear at the keeper's own thermal quantity
  (the P0 base stack and the P1 bid stack; the bid stack reproduces P1 within the miso-287 residual).
- The model's seam rows (import ladders priced at the neighbour's own DA hub) are marginal in 21–28 % of hours.
  The IMM table has no import category: scheduled interchange is price-taking in MISO's SMP.
- Coal's model share rises with load (bid stack 2020: q1 7 %, q5 46 %) — the opposite of the IMM's "generally in
  off-peak hours". The model's coal is marginal when its ~$30 econ tranches are reached at high load; the real
  fleet's coal is marginal at low load, around $15.

## 4. What the marginal offer is made of (block C)

TABLE_C

Reading:
- At the CC_REGULAR margin, the fuel print's wedge over the Chicago Citygate flow-day hub is the largest single
  component of the gap in every year it can be measured. The variable-transport leg the owner's convention keeps
  is $0.21/MMBtu for CC_REGULAR (miso-225); the ruled form would remove roughly (wedge − 0.21) × HR of it.
- The startup markup at the low-load margin is zero in every year (the markup lives on the units that start, not on
  the CC that is already on).
- The coal econ offer anatomy: cap-weighted HR 12.6–13.0 (the econ_high multiplier 1.309 × the tranche heat rate),
  the plant's own EIA-923 delivered price, $4.50 VOM, and the ×1.10 non-steam lift (miso-220) on committed /
  econ_low / econ_high / peak. The resulting ~$30 (2020) offer is what keeps coal out of the low-load margin.

## 5. Quantities and coal bands in the low-load hours (blocks D, E)

TABLE_DE

Reading:
- CC_REGULAR matches CAMPD within ±0.5 GW in the low-load hours of every year except 2025. Coal is +1.0 GW (PRB)
  in 2020 and within ±1 GW elsewhere. The gas shortfall against CAMPD is ST_GAS, CT_CHP and CT_PEAKER — the C1
  ST_GAS object (routed) and the CHP host-steam basis (miso-116), not the margin.
- The model never spills: zero dump hours and zero wind-curtailed hours in every year. The real market clears
  below $10 in 2.8 % (2020) of hours; this tail is worth +$0.25 of the 2020 gap and is the West wind-congestion
  object (G).
- Model net imports sit 0.7–1.6 GW under EIA-930 at low load in most years; the seam ladder's volume behaviour is
  adjudicated (miso-262, K) and is not re-opened.
- The keeper's coal in the low-load hours is ≥ 95 % mustrun + committed in every year: coal econ dispatched share
  of its capacity is 2–7 %. The real coal fleet at the same hours runs ~1 GW less and sets the price.

## 6. What this is, and what it is not

- **Not coal inventory** (miso-295): 2020 is a glut year; the budget dual is ≤ $0.94 of the night residual.
- **Not commitment** (miso-286): flooring online CC at EcoMin moves the night median ≤ $0.12.
- **Not startup markup** (miso-287): zero at the low-load margin.
- **Not quantity**: class MW match CAMPD at the margin-setting classes.
- **It is the offer level of the two rows that are marginal at low load — the CC fuel print over the hub and the
  coal econ tranche level — plus the West/Plains congestion separation (G).**

The IMM's description of the real conduct is consistent with the data: regulated utilities "often continue to
operate their units as 'must-run,' running them regardless of the price" (2024 SOM p.45–46; Table 7: 2019–2022
regulated coal starts 42 % offered economically, 42 % must-run and profitable, 16 % must-run and unprofitable).
A self-committed unit is a price-taker at its schedule and dispatchable above it at its incremental offer; MISO's
off-peak SMP in 2020 (actual q1 median $15.1) says that incremental offer sat near $15, below the delivered-fuel
cost the model charges its econ tranches ($1.9 × 10.6 + $4.5 ≈ $25 at the mustrun heat rate; ~$30 at the econ
tranche heat rate). The model's regulated take-or-pay discount reaches the mustrun and committed bands only.

## 7. Admissible levers, by rule

| lever | status | what it would do here |
|---|---|---|
| `offer_curve_by_group` coal `econ_low`/`econ_high` (and the ×1.10 lift) | owner-authorized price channel, rule 1 (a)–(e); one value all years, ex ante, never swept | lowers the coal econ tranche offers toward the real coal-marginal level; merit-order change is an intended effect. Risk: one config across years also lowers coal offers in 2021–22, where the model already over-burns coal (+5.3/+10.3 TWh vs EIA-923). |
| `miso_gas_marginal_commodity_pricing` + `miso_gas_variable_transport` | O; owner-ruled form (hub + variable transport, 2026-09-06); killed standalone (miso-224 G-3/G-4: coal collapsed −13 TWh) and jointly with the seam (miso-225, G-3 by 37 MW) | removes ~(wedge − 0.21) × HR at the CC margin: about $1.0/MWh in 2020. Named successor was a JOINT test with a coal-side mechanism, because hub gas alone undercuts the ~$30 coal econ tranches wholesale. |
| coal self-commitment floor | refused at phase 0 (miso-224, rule 19): miso-53's per-plant must-run band is the self-commitment representation | — |
| `internal_congestion_split` | G (killed 2026-10-01; reopens on RO-1 only) | the West/Plains part (~+3 pp of the +11.6 %) |
| `negative_renewable_offers` / `wind_ptc_vintage_offers` | `·` for MISO (never adjudicated) | the <$10 tail: +$0.25 of +$2.54 — too small to carry the gate |
| seam ladder level | `seam_neighbour_hourly_ladder` K (miso-262) | marginal 21–28 % of low-load hours at the PJM DA level; not re-opened |

The one combination that is both admissible and sized to the object is the first two rows together: price gas
at the owner-ruled convention (removing the print wedge the CC margin carries) **and** move the coal econ tranches
through the authorized channel so coal stays in merit where the real fleet's coal was marginal. miso-224 showed
that the first without the second collapses coal (C1); this record shows why — the model's coal econ sits at ~$30
against a real coal-marginal price of ~$15, so any gas repricing below $30 takes coal's energy. Whether to spend a
PRECOMMIT on that joint arm is an owner decision (§8). No value is proposed here, because a multiplier chosen from
these residuals would be a swept value (rule 1 (c)); a PRECOMMIT would have to identify it ex ante from a
declared source (candidates: the IMM Table 1 coal SMP share reproduced at zero LP by the stack census; or the
pre-lift table, as miso-275 did for CC).

## 8. Owner decision

Put as decision cards in the session's final message. Options recorded here so the record is complete:
(A) PRECOMMIT a joint arm — gas at hub + variable transport (O cells, owner-ruled form) + coal econ band
multiplier set ex ante through the authorized channel, one value all years, kill rules on C1 coal/gas and on the
coal marginal share moving toward IMM Table 1; (B) the coal channel alone (exempt coal from the ×1.10 lift, the
miso-275 precedent, or a declared econ value); (C) record and leave C3a 2020 as a known miss, move the chain to
the next failure.

## 9. Where MISO stands

Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span NOT-YET on C1 ST_GAS 2019 (routed),
C3a 2020 (+11.6 %) and C3b 2021 (0.201). **No frontier** (owner, 2026-09-28: routed misses are failures).

## Retrievability

No solve. The probe, its JSON output and this record are in this PR. The six SOM PDFs are not committed.
