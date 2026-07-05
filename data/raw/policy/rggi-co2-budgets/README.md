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

## DATA (landed — regional; per-state pending)

- [x] `rggi-co2-budgets.csv` — the **regional** (`state=RGGI`) annual allowance
      budget (short tons: 2023-2025 published + 2027-2030 projected at the 2021
      Model Rule ~2.9%/yr decline) and the 2025 CCR/ECR/minimum-reserve
      trigger-price schedule. The regional budget feeds
      `RGGI_STATE_CO2_BUDGET["RGGI"]` in `constants.py` (a test asserts the
      constant mirrors this CSV). 2022 and 2026 omitted (holdout quarantine,
      CLAUDE.md rule 22).
- [ ] Per-member-state (`state` = postal code) annual budgets — pending the RGGI
      per-state allowance-distribution intake. Until then a RGGI ISO's
      power-sector row uses the regional cap (an even looser over-bound, so still
      slack), mirroring PJM shipping OFF pending its crosswalk.
