# RESULT — PJM-NEXT-13 (2026-09-30): availability falsified; replacement-cost fuel built and refuted at zero LP

**Keeper unchanged:** `2026-09-28-pjm-next8-exitfix`. **Zero LP, zero shards, nothing registered or promoted.** Detail: `docs/FINDING-pjm-next-13-availability-gas-coalmarginal-2026-09-29.md` (the addendum carries the arm delta).

| card | result |
|---|---|
| 1 — coal availability | **Falsified.** Real monthly max ÷ model available MW is 0.95–0.99 in every year, lowest in the fit years. A monthly derate removes ≤ 0.7–2.9 TWh of a 12–19 TWh gap. |
| 2 — production-area gas | **The floor gap is real.** Against IMM production gas, only 1–8 % of real hours sit below an efficient CC's fuel cost (26–45 % against delivered). The owner ruled *"Hub + transport, joint with coal"*, which was built as `pjm_replacement_cost_fuel`. Its zero-LP delta moves prices **up** in every year (+0.5 to +2.7 $/MWh), and its coal bids exceed PJM's own measured offers in 32–61 % of floored hours. Owner: *"Don't solve; record."* Matrix **R**. |
| 3 — model coal-set share | Model coal is marginal in 35/33/28/22/14/19/15 % of load-weighted zone-hours against the IMM's 24/18/14/10/9/10/8 %. The year ordering matches, so coal is not under-represented as a price-setter. |

**Status (unchanged):**
- Training span 2023–2025: NOT-YET on one row (CC_REGULAR 2023 +8.48, east→south limit).
- Run-level 2019–2025: NOT-YET, with 14 out-of-span rows.

**OPEN (not limits):** COAL_BIT 2019/2021, CT_PEAKER 2021, C3a 2019/2020 and the all-year floor.

**Next tests (PJM-NEXT-14):**
1. **Where each CC buys its gas.** Map each CC to production- vs market-area supply at plant level (pipeline receipt/delivery points), not by zone. The low end is priced by CCs on production gas.
2. **The keeper's own low-price marginal units.** A one-year dispatch replay, needed because `dispatch/<y>_P1.parquet` is not committed.

**New in the repo:**
- `pjm_replacement_cost_fuel`, default off, every keeper byte-identical.
- The frozen derive `scripts/data/derive_pjm_replacement_fuel.py` and its reference tables.
- Raw intakes: `data/raw/eia-coal-mine-region/`, `data/raw/eia-coal-transport-rates/`, and the IMM monthly spot rows in `som-competitive-conduct`.
- Probes `_pjmnext13_{fleet_dump,cards,arm_delta}.py`.

**Retrievability:** nothing was solved. Every number here regenerates at zero LP from committed files: `fleet_only` rebuilds of about 4 min per year.
