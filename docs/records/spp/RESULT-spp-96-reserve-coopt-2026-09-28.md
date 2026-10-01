# RESULT — SPP-96: reserve co-optimisation (queue item 6, SPP-56) is INERT at zero LP. The §5.7 queue is exhausted.

**Lane** SPP-96 · control = keeper `2026-09-28-spp-94-curtail-rows` (bundle `spp94_arm_span`, rule 29(b) form 4, G-DRIFT
all INERT) · PRECOMMIT `docs/handoffs/PRECOMMIT-spp-96-reserve-coopt-2026-09-28.md`, pushed at `58d98cb8` **before** any
measurement · probe `scripts/probes/_spp96_reserve_coopt_phase0.py` → `docs/handoffs/spp96/phase0.json` · **LP spent: 0.
Shards: 0. Nothing registered; the keeper is unchanged.**

## 1. Result

| year | RT LMP mean $/MWh | Spin MCP mean | RegUp MCP mean | Spin / LMP | cleared up-reserve median MW | keeper headroom median MW | headroom / req | **bind hours** |
|---|---|---|---|---|---|---|---|---|
| 2019 | 20.85 | 5.19 | 10.88 | 25 % | 1,834 | 16,766 | 9.2 | **2** |
| 2020 | 16.52 | 5.46 | 11.16 | 33 % | 1,884 | 17,001 | 9.0 | **0** |
| 2021 | 37.36 | 12.05 | 25.30 | 32 % | 1,898 | 17,145 | 9.2 | **0** |
| 2022 | 44.09 | 7.09 | 18.62 | 16 % | 2,216 | 18,199 | 8.0 | **0** |
| 2023 | 23.47 | 3.50 | 9.13 | 15 % | 2,419 | 17,287 | 6.8 | **0** |
| 2024 | 23.31 | 2.60 | 10.20 | 11 % | 2,511 | 17,257 | 6.5 | **11** |
| 2025 | 27.11 | 2.85 | 11.59 | 11 % | 3,016 | 17,141 | 5.4 | **6** |

"Bind hours" = hours where the keeper's reserve-eligible headroom (Σ pmax × availability over `_reserve_eligible`, minus
the P1 dispatch of those classes) is below SPP's **measured cleared** up-reserve (reg-up + spin + supp + ramp +
uncertainty). Cleared MW over-states a requirement, so the count is an upper bound.

## 2. Expectations and rule (PRECOMMIT §3–§4)

| # | expectation | result | holds? |
|---|---|---|---|
| E1 | bind hours ≤ 20 every year | max 11 (2024) | yes |
| E2 | headroom ≥ 5 × requirement (median) | 5.4–9.2 × | yes |
| E3 | T1 reported | Spin 11–33 % of LMP | reported |
| E4 | wrong-signed for 2019/2020 | by construction | yes |

**Rule:** a solve needs ≥ 88 bind hours **and** Spin/LMP ≥ 5 % in the same 2019–22 year. Bind hours are 0–2 in those
years. **→ INERT. No shard launched.**

## 3. Reading

- **Reserves matter in the real SPP market, not in this LP.** SPP's reserve prices are a material share of its energy
  price, because SPP runs with ~4–5 GW of headroom (SPP-82/83). The LP has no commitment state, so all ~17 GW of available
  thermal counts as spinning, and a 2–3 GW reserve row never binds.
- So M2 is **downstream of the commitment-state defect** SPP-82/83 already routed to an owner-gated design lane. It is not
  an independent lever. Adding it now would be an inert row.
- It would not help the open failures anyway. 2019/2020 are over-prices, and a reserve row can only raise prices.
  2021–22 is the coal/CC swap, where the row does not bind.

## 4. Where SPP stands

- **Train tier 2023–25: CALIBRATED** (lone ledgered C3c). Unchanged.
- **Validation 2019–22: NOT-YET**, unchanged: C3a 2019 +11.5 % / 2020 +27.8 %; C3b 2020 0.348; C1 COAL_PRB 2021 +13.52 /
  2022 +13.49 TWh; CC_REGULAR 2021 −9.16 / 2022 −10.31 TWh; C4 gas 2021 0.317 / 2022 0.365. Under rule 30(c) these do not
  downgrade the ISO.
- **`complete` / `frontier`: not reached** (validation tier NOT-YET).
- **The §5.7 queue is exhausted.** Items 1 and 5 are R/I, 2 is done, 3 and 4 are out of scope or await a ruling, and 6 is
  now I. Every open validation failure already has a DO-NOT-REDO with no admissible forward instrument (SPP-44, 74, 79,
  82, 83, 89, 90, 91). What remains is owner-level: a commitment-state design lane, the West/East partition ruling
  (SPP-93), the rail-reliability data procurement (SPP-44), or the all-ISO benchmark basis (SPP-87 Q1).

## 5. Matrix (rule 28(b))

`energy_reserve_coopt` stays **I** (evidence extended to M2 and 2019–25). `reserve_pergen` and
`reserve_deliverability_scoping` stay **U** with notes. §5.7 carries an SPP-96 note, and queue item 6 is marked done.

## 6. Retrievability (rule 34(e))

Nothing was solved, so nothing needs retrieving. The probe re-runs in ~10 min (7 fleet rebuilds, no LP). Its per-hour
headroom parquets are not committed; `phase0.json` is.
