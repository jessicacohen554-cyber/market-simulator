# PRECOMMIT-phase0 — closeout-SOCO-3: the owner's take-or-pay coal hypothesis (R-45), zero LP

Lane `claude/closeout-soco-3`, 2026-10-03. Written **before** any census number was computed.
Keeper `2026-10-03-closeout-soco-2-nuclear` (bundle `results/calibration/closeout_soco_2_span`) is the control (rule 29b).
No LP, no shard, no `src/` edit in this phase.

## 0. The owner's hypothesis, and the cells it touches (rule 28)

R-45: *"Fix the models coal offer for SOCO then they could be take or pay contracts with vertically integrated
utilities?"* — if contracted coal is take-or-pay, its fuel cost is sunk and the economic offer of that energy is
VOM + non-fuel adders, which would keep coal on overnight against gas CC.

| SOCO cell | Verdict | What closed it | What this lane brings that is new |
|---|---|---|---|
| `coal_takeorpay_committed` | G (soco-74) | Page 5 has no minimum-quantity field; contract tons fell −32 % with burn 2019→20; family scope misses `_econ*` | (i) the closeout-SOCO-2 night-decile signature (CC +1.3–1.9 GW / coal BIT flat deficit) that soco-74 never tested against; (ii) a monthly (not annual) contract census incl. 2025 receipts; (iii) the **stock-headroom** test below — the economic precondition for sunk fuel at a cost-of-service utility; (iv) a search for a plant-grain minimum-take source (the reopen condition soco-74 itself named) |
| `coal_fuel_inventory_take_floor` | G (soco-80) | Y-1-volume renewal premise false for SOCO 2020 | none on the Y-1 premise; touched only if (iii) shows a same-year binding pile ceiling |
| `coal_fuel_inventory` | U | — | the same-year R-3 envelope is the only admitted receipt-based form |

The owner's question is the candidate new evidence; on its own it is a hypothesis, not data. A re-test of either G
cell needs (i)+(iii) to support it **or** (iv) to find a quantity term.

## 1. Economics fixed ex ante

Under a take-or-pay or minimum-take contract, a ton that must be paid for is sunk **only if it cannot be stored and
burned later**. A cost-of-service utility with yard room stores it; its opportunity cost is then the replacement
cost of a future ton (≈ delivered cost), not zero. Fuel becomes sunk at the hourly margin only when the pile is at
its physical ceiling (or a stock target) and deliveries keep arriving. So the measurable signature of
"sunk contracted coal" is: **stock at/near its multi-year maximum while contract deliveries continue and burn is
low**, concentrated in the months/plants where the model under-runs coal at night.

## 2. Census (computed after this note is committed to the branch)

- **C-A contract structure**, per SOCO coal plant-month 2019–2025 (EIA-923 Page 5 + coal stocks): contract
  (C/NC/T) share of tons and MMBtu; tonnage-weighted months-to-expiration; contract vs spot $/MMBtu; within-plant
  monthly corr(contract receipts, burn) where burn = receipts − Δ month-end stock.
- **C-B night dispatch**, per plant-year: mean MW in the lowest two system-load deciles, keeper (`unit_marginal`)
  vs CAMPD gross × plant EIA-923 net/gross; night shortfall = actual − model (MWh).
- **C-C stock headroom**, per plant-month: month-end stock / plant's max month-end stock 2018–2025.
- **C-D minimum-take source search**: public Georgia / Alabama / Mississippi PSC fuel filings, FERC Form 1 fuel pages,
  10-K fuel commitments; anything giving a minimum quantity at plant (or operating-company) grain.

## 3. Readings fixed ex ante

**SUPPORT** (charter a mechanism) requires all of:
- S1: night shortfall concentrates at high-contract plants — Spearman ρ(plant-year night shortfall as a fraction of
  actual night MWh, contract MMBtu share) ≥ +0.5 over plant-years with ≥ 100 GWh actual night energy, **and**
  plants with contract share ≥ 0.9 carry ≥ 2/3 of the summed positive night shortfall;
- S2: contract receipts do not track burn at monthly grain — median within-plant corr(contract receipts, burn)
  ≤ 0.3 — **and** in shortfall plant-years contract MMBtu ≥ burn MMBtu;
- S3: the pile is at its ceiling in the shortfall months — median headroom ≥ 0.85 of the plant's max stock in the
  plant-months that carry the night shortfall;
- S4: a quantity term is identifiable (C-D finds a minimum take at plant or operating-company grain), **or** S3 is so
  strong that the pile ceiling itself (a physical measured envelope) is the forcing term.

**REFUTE**: ρ ≤ +0.2, **or** median monthly corr(contract receipts, burn) ≥ 0.5, **or** median headroom ≤ 0.7 in the
shortfall months (the yards had room, so contracted coal carried a positive opportunity cost and was not sunk).

**DATA-LIMITED**: S1 holds but S3 fails and C-D finds no quantity term — the pattern is consistent with the
hypothesis, but no measured input can carry it under rules 13/14.

Anything between REFUTE and SUPPORT is read as DATA-LIMITED, never as SUPPORT. No threshold moves after numbers are
seen.

## 4. Rule-19 D-2 enumeration (step 2) precedes any design (step 3). No solve launches before the owner's ruling.
