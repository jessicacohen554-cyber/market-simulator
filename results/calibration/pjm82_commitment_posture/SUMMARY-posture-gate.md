# PJM commitment-posture honesty gate (design note §A, PJM port)

Modeled online headroom / cleared-reserve behaviour vs the measured
PJM reserve-market series (`data/raw/PJM-AS`). Level + event-day
direction; the >$150/$200 tail count is NEVER the gate (rules 1/13).

**Pre-committed decision (§3): REJECT** — G-P1 level FAIL all-years, G-P2 direction PASS in 2/3 years (accept needs level all-years AND direction ≥2/3).

## 2023

- postured pools: 23, startups 200.5 GW/yr
- G-P1 level [FAIL]: model online headroom mean 9298 MW (pool cleared R mean 919 MW) vs measured online target (SR+REG) 2964 MW — ratio 3.14 (Primary ref 3235 MW; band 0.7-1.5)
- G-P2 direction [FAIL]: daily r(model reserve price, SR MCP) = nan; daily r(headroom, online) = -0.06; top-20 SR-MCP event days same-direction 15/20 (need ≥12)
- G-P3 MAD share (advisory): model 0.42 vs measured 0.804

## 2024

- postured pools: 23, startups 204.7 GW/yr
- G-P1 level [FAIL]: model online headroom mean 9492 MW (pool cleared R mean 1052 MW) vs measured online target (SR+REG) 3289 MW — ratio 2.89 (Primary ref 3522 MW; band 0.7-1.5)
- G-P2 direction [PASS]: daily r(model reserve price, SR MCP) = nan; daily r(headroom, online) = 0.05; top-20 SR-MCP event days same-direction 13/20 (need ≥12)
- G-P3 MAD share (advisory): model 0.434 vs measured 0.75

## 2025

- postured pools: 23, startups 217.6 GW/yr
- G-P1 level [FAIL]: model online headroom mean 8539 MW (pool cleared R mean 994 MW) vs measured online target (SR+REG) 3214 MW — ratio 2.66 (Primary ref 3489 MW; band 0.7-1.5)
- G-P2 direction [PASS]: daily r(model reserve price, SR MCP) = nan; daily r(headroom, online) = 0.08; top-20 SR-MCP event days same-direction 14/20 (need ≥12)
- G-P3 MAD share (advisory): model 0.409 vs measured 0.761

