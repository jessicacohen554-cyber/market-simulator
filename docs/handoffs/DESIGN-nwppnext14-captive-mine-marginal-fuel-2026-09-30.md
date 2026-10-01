# DESIGN (phase 0 only) — NWPP-NEXT-14: captive-mine coal, average vs marginal fuel cost

Owner card (2026-09-30): "Design captive-mine fuel cost". This is design only: no field, no solve, no offer multiplier.
Motivation: FINDING-nwppnext14 §2. Jim Bridger's 2023 offer sits above summer LMP because the model prices it at the
plant's **blended** EIA-923 delivered cost.

## 1. What the receipts show (EIA-923 Schedule 2, `data/raw/coal-receipts/`, plant 8066)

| year | source (mine type, purchase) | share of MMBtu | $/MMBtu |
|---|---|---|---|
| 2022 | Jim Bridger Mine (S, captive) | 0.52 | 2.47 |
| 2022 | Bridger Underground (U, captive) | 0.17 | 2.42 |
| 2022 | Black Butte & Leucite Hills (S, third-party contract, rail) | 0.31 | 2.62 |
| 2023 | Jim Bridger Mine (S, captive) | 0.56 | **4.21** |
| 2023 | Bridger Underground (closing) | 0.00 | 3.71 |
| 2023 | Black Butte & Leucite Hills (contract) | 0.34 | 2.62 |
| 2023 | North Antelope Rochelle (PRB, contract, rail) | 0.10 | 2.42 |
| 2024 | Jim Bridger Mine (S, captive) | 0.81 | 3.12 |
| 2024 | Black Butte / NARM | 0.12 / 0.07 | 2.58 / 2.43 |

- The captive mine's booked cost is cost-of-service: its fixed cost is spread over the tons delivered. When the
  underground mine closed and captive volume fell, the per-ton cost rose from $2.47 to $4.21.
- The third-party sources held at $2.42–2.62.
- An incremental MWh at Bridger in 2023 displaces (or is fuelled by) a contract ton at about $2.4–2.6/MMBtu, not the
  $3.0–4.2 blend.

## 2. The candidate object (for the next lane to build, after an owner card)

**Marginal-source coal price at multi-source plants.** For a coal plant whose Schedule-2 receipts in year Y include
both a captive (cost-of-service) source and a third-party contract or spot source:

- the **econ** tranches take the quantity-weighted price of the **non-captive** sources;
- the take-or-pay block keeps today's blended cost.

The take is already carried once, by the yard take-floor dual (`coal_fuel_inventory_take_floor`, rule 19), so the
captive mine's fixed cost stays in the take and does not become a per-MWh price.

- **Identification: zero DOF.** It uses EIA-923 Schedule 2 fields that already exist: `Coalmine Type`,
  `Purchase Type`, `Operator` vs `SUPPLIER`, and `FUEL_COST`. How "captive" is identified must be decided before any
  number is seen. Candidates: the supplier or mine is the plant operator's affiliate (Bridger Coal Co. is
  PacifiCorp / Idaho Power owned), or the mine-mouth truck/conveyor transport mode (`TC`) with the same county.
- **Rule 13:** receipts are filed monthly, so the construction regenerates for any year from the then-latest filing.
- **Rule 19 check owed:** `coal_plant_monthly_pricing` and `coal_supply_repricing` already write coal prices. The new
  object must **replace** the econ-tranche price at covered plants, never stack on them.
- **Scope:** NWPP first. The census owes every NWPP coal plant with mixed-source receipts (Naughton, Dave Johnston,
  Hunter/Huntington, Colstrip and others). Rule 25: no other ISO's cell moves.

## 3. What this is not

- Not a haircut or an offer multiplier. The price is the measured price of a real, identified source (rules 1 and 13).
- Not an outcome pin on Bridger's monthly burn. The Feb–May conservation lever stays closed.
- Not guaranteed to fix C4. It lowers Bridger's econ offer by about $7–17/MWh in 2023, which should flatten the
  pile-driven just-in-time timing (FINDING §2), but the pile identity and the flat-receipt assumption still govern.

## 4. Phase-0 owed before any code

1. Census NWPP coal plants 2019–2025: share of captive vs non-captive receipts, and the price gap by year.
2. A written captive-identification rule, fixed before the census numbers are read.
3. The rule-19 map of every seam that writes a coal price today, and which one the new object replaces.
4. An owner card.
