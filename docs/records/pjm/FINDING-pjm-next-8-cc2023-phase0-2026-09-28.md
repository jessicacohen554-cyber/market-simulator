# FINDING — PJM-NEXT-8 card 1 phase 0: CC_REGULAR 2023 +8.40 is a ZONAL allocation error (zero LP)

**Keeper** `2026-09-28-pjm-next-7-virtual` (bundle `results/calibration/pjmnext7_vs_span`). **Zero LP.**
**Probe** `scripts/probes/_pjmnext8_cc2023_phase0.py` (a `fleet_only` rebuild of the keeper recipe per year,
joined to the registered payload and bench); output `results/phase0/pjm/_pjmnext8_cc2023_phase0.json`.
Actual zonal prices: `data/clean/lmp/PJM/RTM` hub series.

## 1. Where the surplus sits (model − EIA-923, CC_REGULAR bench plants, TWh)

| zone | 2019 | 2020 | 2021 | 2022 | **2023** | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| EMAAC | +10.5 | +6.7 | +4.3 | +2.6 | **+9.0** | −1.4 | −9.4 |
| Central_PA | +7.4 | +7.2 | +3.7 | +7.1 | **+5.1** | +4.5 | +2.3 |
| ComEd | +1.2 | +2.2 | +2.5 | +4.2 | **+5.5** | +5.0 | +5.7 |
| AEP_Ohio | +1.9 | +4.4 | +1.2 | +1.0 | +1.2 | −1.5 | −1.2 |
| Dominion | −9.7 | −4.8 | −8.4 | −2.8 | **−12.8** | −4.1 | −1.6 |
| SWMAAC | −4.3 | −3.5 | −3.8 | −1.9 | +0.5 | −4.3 | −4.3 |
| **net** | +7.1 | +14.0 | +1.1 | +11.1 | **+8.2** | −0.6 | −7.9 |

- The class number is a **net of large opposite zonal errors**. 2024 passes because they cancel, not because the zones are right.
- **Year-consistent:** Central_PA and ComEd over, Dominion under, in every year.
- **2023-specific:** EMAAC +9.0 (vs −1.4 in 2024) and Dominion −12.8 (vs −4.1).
- The −3.8 TWh of 2023 surplus added by PJM-NEXT-7 (virtual supply removed) spreads over every zone; it is not the story.

## 2. Why: the model's east–south price spread has the wrong sign in 2023

| mean RT, 2023 | model | actual hub |
|---|---|---|
| EMAAC − Dominion | −0.05 | **NJ − Dominion −8.50** (Eastern −5.25) |
| EMAAC − Central_PA / Western | +0.91 | **NJ − Western −7.72** |
| Dominion − Central_PA / Western | +0.96 | +0.78 |
| ComEd − AEP | −1.18 | Chicago − AEP −3.37 |

- Model EMAAC 2023 averages ~$32 against the NJ hub's ~$24, **above it in all 12 months** (+$4 to +$13).
- Dominion's CC cost is ~$10/MWh above EMAAC's in 2023 (mc $38.5 vs $28.4, cap-weighted). Two parts:
  - **Gas:** $3.60–3.73/MMBtu for every Dominion CC (EIA-923 utility receipts, and the VA N3045 state average for the rest), +$1.1 over Henry Hub. 2024: $3.12.
  - **RGGI:** Virginia's 2023 allowance cost (≈ $5/MWh; VA left RGGI after 2023). Real, and correctly applied.
- So in 2023 the model moves ~13 TWh of CC output from Dominion to EMAAC / Central_PA, where the real market did the opposite.

## 3. Is there a measured rule-14 operand that fixes it? Not in the repo.

- **Gas basis.** Dominion's price is a delivered *average* that carries firm-transport reservation cost (the concern already on cell `zonal_gas_basis`). The marginal alternative, a daily Transco Z5 / Tetco M3 / Transco Z6 hub series, is **DATA-BLOCKED** (proprietary; no such series in the repo). EIA-923 monthly costs carry no contract/spot split.
- **EMAAC price level.** A $5–13/MWh eastern discount the model does not produce. The candidate is the east-side price formation (eastern gas basis and the 2023 west-to-east interface state), a structural (rule 1) question, not an input correction.
- **Not a level problem.** An offer-band multiplier (rule 1 carve-out) cannot fix opposite-signed zonal errors and would only move the class total. Not recommended.

## 4. Verdict

CC_REGULAR 2023 is a **zonal price-formation defect** (EMAAC too expensive, Dominion too costly to run), the same object that yields Central_PA / ComEd over and Dominion under every year. No measured operand in the repo closes it. Next step, if chartered: a zero-LP diagnostic of the 2023 eastern price level (model EMAAC supply stack and imports vs the published Eastern interface transfers and NJ hub), before any solve.

## 5. Addendum: why model EMAAC is ~$7 too expensive (owner card "Diagnose east price", zero LP)

Probe `scripts/probes/_pjmnext8_emaac_price_phase0.py` → `results/phase0/pjm/_pjmnext8_emaac_price_phase0.json`.
Hour alignment checked: model EMAAC demand vs metered load, lag 0, r = 0.997.

**The actual NJ discount is all congestion.** 2023 RT means, $/MWh:

| hub | total | energy | congestion |
|---|---|---|---|
| NJ | 24.06 | 29.61 | **−5.63** |
| Eastern | 27.32 | 29.61 | −2.73 |
| Western | 31.78 | 29.61 | +1.96 |
| Dominion | 32.56 | 29.61 | +2.78 |
| model zones | 29.4–31.4 | | |

| | 2023 | 2024 |
|---|---|---|
| model EMAAC − NJ, median | +8.67 | +5.70 |
| model EMAAC < Central_PA − $2 | 0.0 % of hours | 0.0 % |
| actual NJ < Western − $2 | **54 %** | 33 % |

- **Not the eastern interface.** The published "Average Eastern" (west→east) averaged 3,720 of 7,367 MW in 2023, never reversed, and sat ≥ 90 % of its limit in only 4.6 % of hours. NJ congestion is *less* negative in those hours. 5004/5005 bound 0.1 %.
- **Not a shortage in EMAAC.** Model EMAAC generates more CC (+9 TWh) and imports less (18.3 vs 24.8 TWh) than actual, yet prices higher. Model demand is +1.9 % vs metered.
- **Not gas.** EMAAC CC gas $2.22 vs Transco Z6 non-NY $2.22; Central_PA $2.18 vs TETCO M3 $2.10. Only Dominion is high (+$0.39 vs Transco Z6 VA).
- **The model's EMAAC just rides the system price.** In hours where it exceeds NJ by > $5, the nearest-cost unit is scattered (ComEd CT, AEP coal, EMAAC CC, AEP CT).

**Verdict: structural (rule 1).** Real 2023 prices fall from east to south (NJ −5.6 → Dominion +2.8, all congestion), from constraints that limit flow out of the eastern PA/NJ gas-and-nuclear cluster toward BGE/Pepco/Dominion. The reduced network has no such binding boundary (EMAAC→SWMAAC is a static 5,000 MW that never binds; there is no Central_PA↔SWMAAC link), so it cannot produce negative congestion at EMAAC. **No measured input in the repo corrects this.** Next step: fetch the 2023–2024 PJM binding constraints (`scripts/data/fetch_pjm_binding_constraints.py`; corpus gitignored, not hydrated) and rank facilities by congestion contribution to the NJ hub, to identify the missing boundary before any solve. An offer-band multiplier cannot create zonal separation.
