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

## DATA NEEDED

- [ ] `carb-cap-schedule.csv` with the annual allowance budget (MMT CO2e) and
      the Auction Reserve floor price ($/tonne).
- Do **NOT** include 2022 or H1-2026 rows (holdout quarantine, CLAUDE.md
  rule 22). Populate 2023-2025 and forward years from 2027 onward; leave 2026
  out until the holdout is released.
