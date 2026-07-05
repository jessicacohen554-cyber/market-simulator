# RGGI CO2 allowance budgets & price-band trigger schedule (raw)

Source root for the `rggi-co2-budgets` clean datatype
(`data/dictionary/schema/rggi-co2-budgets.schema.yaml`). Curated by
`scripts/curate_rggi_co2_budgets.py`, which reads `rggi-co2-budgets.csv` in this
directory and writes schema-valid Parquet to
`data/clean/rggi-co2-budgets/rggi-co2-budgets.parquet`. Until the CSV lands the
curator skips this datatype (empty frame), and the optional power-sector
mass-cap row stays inert — consistent with the design (the row is a gated,
default-OFF scenario instrument; see
`docs/handoffs/emissions-mass-cap-plan-2026-07.md` §2, §7, §8).

## Expected file

`rggi-co2-budgets.csv` — one row per (state, budget_year, metric), columns:

```
state,budget_year,metric,value,unit,source_doc,source_page
```

- `state`: two-letter member-state postal code (NY, CT, MA, ME, NH, RI, VT, MD,
  DE, NJ, VA) or `RGGI` for the regional total.
- `metric`: `allowance_budget` (unit `short_tons`) |
  `ccr_trigger_price` | `ecr_trigger_price` | `minimum_reserve_price`
  (unit `usd_per_short_ton`).

## Authoritative sources

- **Allowance budgets** — RGGI, Inc. "Allowance Distribution" tables and the
  updated Model Rule cap trajectory (published through 2030, then the fixed
  ~2.9%/yr real decline; Third Program Review schedule):
  https://www.rggi.org/allowance-tracking/allowance-distribution
- **CCR / ECR / minimum reserve prices** — RGGI 2017 Model Rule §5.3 (CCR) and
  §6.3 (ECR), with the published annual 7%/yr (CCR) escalation:
  https://www.rggi.org/program-overview-and-design/design-archive

## DATA (landed — regional and per-state, 2023-2025)

- [x] `rggi-co2-budgets.csv` — the **regional** (`state=RGGI`) and **per
      member-state** (`state` = postal code: CT, DE, ME, MD, MA, NH, NJ, NY,
      RI, VT, and VA for 2023 only) annual **CO2 Allowance Base Budget**
      (short tons) for 2023-2025, plus 2027-2030 regional-only projections at
      the 2021 Model Rule ~2.9%/yr decline, and the 2025 CCR/ECR/
      minimum-reserve trigger-price schedule.
    - Source: RGGI, Inc.'s official "Distribution of VYyyyy CO2 Allowances By
      State" spreadsheets (`rggi.org/sites/default/files/Uploads/
      Allowance-Tracking/{2023,2024,2025}_Allowance-Distribution.xlsx`,
      release date 2026-06-23), "CO2 Allowance Base Budget" column — the
      GROSS annual issuance under each state's own CO2 Budget Trading Program
      regulation, BEFORE the Third Adjustment for Banked Allowances (a
      bank-clearing haircut this model's no-bank row deliberately excludes,
      plan §8).
    - Feeds `RGGI_STATE_CO2_BUDGET` in `constants.py` (per-state and the
      "RGGI" regional total; a test asserts the constants mirror this CSV).
      A RGGI ISO's power-sector row (`policy/cap_and_trade.py::
      _published_power_sector_budget`) sums its own member states' rows
      (`RGGI_MEMBER_STATES_BY_YEAR` ∩ the program's states) instead of the
      regional over-bound; the regional total remains the fallback for years
      without a per-state breakdown (2027-2030).
    - 2022 and 2026 omitted (holdout quarantine, CLAUDE.md rule 22).
- [ ] Per-state budgets for 2027-2030 (projected years) — not published by
      RGGI, Inc. (only the regional trajectory is); a RGGI ISO's forecast-year
      row falls back to the regional total (documented over-bound) until a
      cited per-state projection method is added.
