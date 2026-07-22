# MISO commitment-posture honesty gate (design note §A)

Modeled online headroom / cleared-reserve behaviour vs the measured
MISO ASM series (`data/raw/MISO-AS`). Level + event-day direction;
the >$200 tail count is NEVER the gate (rules 1/13).

## 2023

- postured pools: 18, startups 101.7 GW/yr
- G-P1 level: model online headroom mean 10525 MW (pool cleared R mean 1561 MW) vs measured cleared 2480 MW — ratio 4.24
- G-P2 direction: daily r(model reserve price, measured spin MCP) = 0.00; daily r(headroom, cleared) = -0.11; top-20 measured event days same-direction 19/20
- G-P3 regional share: model {'Central': 0.404, 'North': 0.22, 'South': 0.376} vs measured {'North': 0.405, 'Central': 0.461, 'South': 0.134}

## 2024

- postured pools: 18, startups 107.3 GW/yr
- G-P1 level: model online headroom mean 11092 MW (pool cleared R mean 1657 MW) vs measured cleared 2666 MW — ratio 4.16
- G-P2 direction: daily r(model reserve price, measured spin MCP) = 0.20; daily r(headroom, cleared) = 0.34; top-20 measured event days same-direction 19/20
- G-P3 regional share: model {'Central': 0.397, 'North': 0.237, 'South': 0.366} vs measured {'North': 0.395, 'Central': 0.454, 'South': 0.151}

## 2025

- postured pools: 18, startups 138.5 GW/yr
- G-P1 level: model online headroom mean 9929 MW (pool cleared R mean 1802 MW) vs measured cleared 2679 MW — ratio 3.71
- G-P2 direction: daily r(model reserve price, measured spin MCP) = 0.31; daily r(headroom, cleared) = 0.03; top-20 measured event days same-direction 15/20
- G-P3 regional share: model {'Central': 0.425, 'North': 0.236, 'South': 0.339} vs measured {'North': 0.404, 'Central': 0.413, 'South': 0.183}

