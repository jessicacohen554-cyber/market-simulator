# CARB cap-and-trade allowance budget & floor-price schedule (raw)

Source root for the `carb-cap-schedule` clean datatype
(`data/dictionary/schema/carb-cap-schedule.schema.yaml`). Curated by
`scripts/curate_carb_cap_schedule.py`, which reads `carb-cap-schedule.csv` in
this directory and writes schema-valid Parquet to
`data/clean/carb-cap-schedule/carb-cap-schedule.parquet`. Until the CSV lands
the curator skips this datatype (empty frame), and the optional power-sector
mass-cap row stays inert — consistent with the design (the row is a gated,
default-OFF scenario instrument; see
`docs/handoffs/emissions-mass-cap-plan-2026-07.md` §2, §7, §8).

## Expected file

`carb-cap-schedule.csv` — one row per (budget_year, metric), columns:

```
budget_year,metric,value,unit,source_doc,source_page
```

- `metric`: `allowance_budget` (unit `mmt_co2e`) |
  `auction_reserve_price` (unit `usd_per_tonne`).

## Authoritative sources

- **Allowance budget** — CARB Cap-and-Trade Regulation, 17 CCR §95841 (annual
  allowance budgets) and the 2022 Scoping Plan / post-2030 cap-decline
  amendment: https://ww2.arb.ca.gov/our-work/programs/cap-and-trade-program
- **Auction Reserve (floor) price** — CARB Cap-and-Trade Regulation §95911(c),
  the statutory 5% + CPI annual escalation, and the annual
  Auction-Reserve-Price notice:
  https://ww2.arb.ca.gov/our-work/programs/cap-and-trade-program/auction-information

## DATA (landed)

- [x] `carb-cap-schedule.csv` — annual allowance budget (MMT CO2e, 17 CCR §95841
      Table 6-2: 2023-2025 + forward 2027-2031) and the Auction Reserve floor
      price ($/tonne, CARB Annual Auction Reserve Price Notices 2023-2025). The
      budget feeds `CARB_ALLOWANCE_BUDGET` in `constants.py` (a test asserts the
      constant mirrors this CSV). 2022 and 2026 omitted (holdout quarantine,
      CLAUDE.md rule 22).
