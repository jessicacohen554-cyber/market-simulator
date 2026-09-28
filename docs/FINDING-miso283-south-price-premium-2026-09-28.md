# FINDING — miso-283 phase 0: the MISO-South price premium is mostly the system night overshoot, not a South object. No solve earned.

```
LANE    : miso-283 (owner pick on the miso-282 card "South price premium probe (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025) — unchanged
LP      : none. Keeper's committed hourly sidecars, measured MISO hub RT + DA LMP, fleet-only rebuilds.
PROBES  : scripts/probes/_miso283_premium_localize.py     zone x hub, RT + DA, hour/month/year
          scripts/probes/_miso283_marginal_census.py      offer-matched marginal class, South gas vs HH
          scripts/probes/_miso283_committed_basis_delta.py committed_band_measured_basis footprint (2023)
OUTPUTS : results/calibration/_miso283_{premium_localize,marginal_census,committed_basis_delta}.json
```

## 1. Answer

The South premium has three parts. None is a South lever that is both structural and admissible.

1. **About 80 % is system-wide.** At night (h0–5) the model's Illinois price also sits $5–9/MWh above
   ILLINOIS.HUB, in every year. In the model, South and Illinois are within $0.5 in 78 % of night hours.
   This is the known two-sided diurnal compression (`diurnal_price_amplitude`, cell **G**; miso-130: "night
   +$7.0–8.7 flat overshoot"). It now holds in all seven years, 2019–2025.
2. **The South-specific spread error is small outside 2021–22:** +0.1 to +1.9 $/MWh at night, and +1.2 to
   +2.6 by day. In 2021–22 it is +3.6 / +3.8 at night and +4 to +10.5 by day and evening. That size comes from
   the North being **under**-priced (Illinois by day −4.3 / −8.6, evening −6.9 / −19.7), which is the routed
   C3b 2021 / C3a 2022 object.
3. **The premium is the same in DA and RT** (South DA premium +0.4 to +5.5 against RT +1.1 to +5.9). It is
   not a real-time scarcity artifact.

## 2. Decomposition (model − hub, RT, hub-covered hours, $/MWh)

South hub = mean of LA / MS / AR / TX. Each cell reads: South premium = Illinois premium + South-specific spread error.

| year | night h0–5 | day h7–14 | evening h15–20 | annual South (DA) |
|---|---|---|---|---:|
| 2019 | +5.7 = +5.1 +0.5 | +2.5 = +1.3 +1.2 | +1.3 = +0.0 +1.3 | +3.5 (+2.8) |
| 2020 | +6.0 = +5.0 +1.0 | +2.8 = +1.2 +1.6 | +0.2 = +0.9 −0.6 | +3.2 (+3.3) |
| 2021 | +6.0 = +2.5 +3.6 | +0.0 = −4.3 +4.3 | −3.0 = −6.9 +3.9 | +1.1 (+0.4) |
| 2022 | +11.4 = +7.6 +3.8 | +1.6 = −8.6 +10.2 | −9.2 = −19.7 +10.5 | +2.0 (+1.0) |
| 2023 | +8.2 = +7.0 +1.2 | +5.7 = +3.5 +2.2 | +0.3 = +0.4 −0.0 | +5.1 (+4.0) |
| 2024 | +7.4 = +7.3 +0.1 | +6.4 = +4.1 +2.3 | +0.5 = −2.1 +2.6 | +4.8 (+4.4) |
| 2025 | +10.8 = +8.8 +1.9 | +7.1 = +4.6 +2.5 | −1.9 = −6.6 +4.7 | +5.9 (+5.5) |

The 2021–22 evening misses the handoff named (South −10 to −14 in 2022) are system-level: Illinois misses
by more (−19.7).

## 3. What sets the South night price, and the candidate causes

| candidate | test | verdict |
|---|---|---|
| **Gas price / basis** | model South gas (cap-weighted) vs Henry Hub daily + measured South CC variable transport (v = 0.249, `miso_gas_variable_transport.pool.csv`) | **No.** Model − HH = +0.23 / +0.25 / +0.35 / +0.29 / +0.25 / +0.28 / +0.29 $/MMBtu, 2019–25. That is the owner-ruled convention (hub + variable transport) within ±0.1. It also matches EIA N3045 LA delivered (2023: 2.84 $/MMBtu). |
| **Marginal class** | offer-matched census (±$0.5), night hours | CC_REGULAR econ tranches set the price in 39–72 % of South night hours (2023: `econc04/05` at tranche HR 7.4–9.1 × delivered gas + $2 VOM). The offer is the measured basis (phys_econ_low 0.887 = CEMS incremental HR) plus about $1.5 of margin. It is not a markup object. |
| **Reserve adder** | `reserve_price` in the South | **No.** $0.00 at night in every year checked. |
| **South↔North transmission** | model S−IL at night vs hub S−IL | Coupled in 78 % of model night hours. When the model decouples at night, South is **above** Illinois (13–22 % of hours), meaning the model imports into South. The measured night spread is mixed (−0.9 to +2.1). This is the South-specific residual in §2. It points at South supply the model lacks at night (below). |
| **Measured offer stack (c)** | `data/raw/miso-energy-offers` (JJA 2023–25 only, masked, no class bridge) | Not re-fetched. Already adjudicated: miso-145 measured the real book **$8–15 cheaper** at matched position (universe-contaminated); `measured_offer_surface` is **R** (miso-151). There is no new question this corpus can answer for the South night. |
| **`committed_band_measured_basis`** (MISO cell **U**, zero-DOF, built pjm-h6) | fleet-only footprint, 2023 | **Not a lever for this object.** CC_REGULAR committed offers do not move (22.91 → 22.91; the margin mechanism already prices at phys 1.005). Coal committed moves **up by $18–29/MWh** on 17 GW (PRB 10.8 → 29.4, BIT 6.2 → 34.9), which would override the take-or-pay committed band (a rule-19 collision). Static night effect: South +0.08, Illinois −0.34. The cell stays **U**, with this sizing recorded. |

**Structural reading.** The real night LMP (~$19.5 South, 2023) sits **below** the incremental cost of the
CC tranches that set the model's price (~$25). Supply that runs regardless of price sets the real night
price: out-of-merit steam at minimum load (RO-2, 2.2–8.2 TWh/yr in the South), coal commitment, nuclear
and wind. The LP clears on offers alone and has no commitment-driven price suppression. That South
out-of-merit energy (~250–900 MW average) is also the most likely cause of the South-specific night residual:
without it the model imports into South where the real system does not. It is the routed
`scuc_load_pocket_commitment` (RO-2) object.

## 4. Routing and verdict

- **No solve.** No structural, rule-13-admissible lever in this lane moves the premium. Fuel is ruled out,
  and the offers sit on the measured basis. The system part is **G** (`diurnal_price_amplitude`, raised, not
  re-opened). The South part is the routed RO-2 object, plus C3b 2021 / C3a 2022 in those years.
- **Not proposed:** an `offer_curve_by_group` move (rule 1 channel). The premium is not an offer-level
  markup, so a multiplier would be a wrong-mechanism fit.
- **Matrix:** `committed_band_measured_basis` MISO stays **U**, with its footprint recorded.
  `diurnal_price_amplitude` stays **G**, with the 7-year extension recorded.
- **Rubric:** unchanged. The full span is NOT-YET on the three owner-ruled routed misses. **No frontier.**
