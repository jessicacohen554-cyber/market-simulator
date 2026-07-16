# RC-1C — MISO seasonal RBDC + NYISO multi-vintage curves + curve eligibility — 2026-07-16

**Charter.** F-5 / prereq 4 of the flip-gate lane
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §2.1 item 2, §2.3
F-5): the capacity **instrument** validated on per-delivery-year published
parameters for MISO (seasonal grain, prereq 4a) and NYISO (multi-vintage wiring,
prereq 4b), plus the curve-eligibility governance gate. **Scope: annual
capacity-evolution layer only.** No LP solved, no dispatch-layer change, no
backcast keeper touched, no holdout year read/scored, nothing on any dashboard,
**no default flip** (`capacity_market_clearing` stays default-off; everything below
is byte-identical when the gate is off).

Built on RC-1B (`rc1b-plumbing-2026-07-15.md`): `MARKET_DESIGN_VINTAGES` +
`resolve_demand_curve_vintage` + `THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"]`
were verified present on `origin/main` before starting.

## 1. MISO seasonal RBDC (prereq 4a) — `config/constants.py`

- New `MISOSeasonRBDC` / `SeasonalRBDC` records + `MISO_SEASONAL_RBDC` (four
  seasons, days 92/91/90/92 = 365, recovered from the published seasonal
  gross-CONE ÷ annual gross CONE) + `seasonal_rbdc_price_per_firm_mw_yr` — the
  market's own seasonal settlement, `Σ_season frac(position) × daily_net × days`.
- `MarketDesign` and `MarketDesignVintage` gain a `seasonal_rbdc` field (default
  `None`). The MISO registry design and the MISO PY2025-26 vintage carry
  `MISO_SEASONAL_RBDC`; `capacity_price_per_firm_mw_yr` dispatches to the seasonal
  sum when a resolved design/vintage has it, else the scalar-curve branch.
- **Construction choice:** the requirement point (frac 1.0) is the **flat daily
  net-CONE** (79,800 ÷ 365 = 218.63 $/MW-day — MISO publishes seasonal gross-CONE
  caps + annual net-CONE, not a seasonal net-CONE), the per-season cap fraction is
  `seasonal_gross_daily ÷ daily_net` (summer ≈6.33). This keeps the annualization
  self-consistent: **at the requirement the seasonal sum returns exactly annual
  net-CONE** (reduces to the annual curve), and short positions pick up the
  seasonal caps. The RBDC's cap/zero reserve positions (0.97/1.05) stay first-order
  (unpublished shape, shared with the retained annual `_MISO_RBDC_CURVE`).
- **Pre-RBDC vertical vintages (PY2021/22-2024/25)** added to the MISO vintage
  table: `_MISO_VERTICAL_CURVE` (a near-vertical step anchored on North/Central
  gross CONE = the LRZ 1-7 mean: 91.86 / 91.06 / 103.04 / 123.50 $/kW-yr),
  `seasonal_rbdc=None` — replacing the RC-1B hold-first stand-in that served them
  the sloped RBDC (FERC ER23-2977 "vertical-at-CONE"; rule 13 "do not invent
  slope"). PY2026-27 stays omitted (per-LRZ-only Net CONE, rule 5); hold-last
  serves PY2025-26 forward.
- **One-position limit (documented, not a bug):** the model holds ONE annual
  accredited position and feeds all four seasons, so it cannot reproduce the
  observed seasonal price *concentration* — it over-states at a short annual
  position and under-states at a long one. Seasonal fleet accreditation (which
  would let the four positions differ) is a future item, explicitly not invented.

## 2. NYISO multi-vintage + curve eligibility (prereq 4b) — `config/constants.py`

- The NYISO vintage table was already correct on main (RC-1B). This session adds
  the **eligibility gate**: `CAPACITY_CURVE_ELIGIBLE_BY_ISO` +
  `resolve_capacity_curve_eligible(iso)`, consulted in
  `capacity_price_per_firm_mw_yr`'s curve branch. **NYISO = False** (R5a ICAP→UCAP
  pairing adjudicated, owner sign-off pending — `nyiso-neiso-capacity-pairing-
  adjudication-2026-07-15.md` §3, Option D stands), so with the gate on and a
  vintage resolved NYISO still prices its **fixed** anchor. PJM/NEISO/MISO = True.
  `iso=None` and unlisted ISOs default eligible (byte-identity; no silent block).
  Enforcement is in the eligibility logic, not prose (`TestCurveEligibility`).

## 3. Refreshed validation (prereq 3, no LP) — `scripts/validate_capacity_prices.py`

- **MISO Pass 1 at seasonal grain** (`miso_seasonal_pass1` + `render_miso_seasonal`):
  per-season cleared price → implied position on the season's model curve, +
  annualized seasonal SUM vs net-CONE. Result: **seasonal SUM = 79,071 vs 79,800
  net-CONE (−0.9%)**; summer short (0.988), others long — concentration
  reproduces directionally.
- **NYISO Pass 1B per-vintage** (`nyiso_year_params` reads each year's own ARV +
  cap + reference point; model side threads `resolve_demand_curve_vintage`):
  2023/24 & 2024/25 reproduce cleared spot + shape to **0%** on their own anchors;
  2021/22 & 2022/23 non-scoreable (no ARV/cap — explicit, no interpolation);
  2025/26 locked.
- PJM/NEISO Pass 1/Pass 2 model side is left on the registry reference
  (`year=None`), so their numbers are byte-stable. Refreshed report section:
  `docs/handoffs/capacity-price-validation-2026-07-16.md`; committed JSON:
  `results/capacity-price-validation/validation.json`.

## 4. Tests

`tests/test_capacity_demand_curve.py`: `TestMISOSeasonalRBDC` (hand values —
reduces-to-net-CONE at 1.0, zero when long, seasonal-gross-sum cap when short,
monotone, short>annual, pre-RBDC vertical), `TestCurveEligibility` (NYISO fixed
when iso supplied, iso=None still curves, defaults). Updated the annual-grain
parametrized tests to `_ANNUAL_CURVE_ISOS` (MISO is seasonal), the MISO resolution
test, and `_expected_anchor` (pre-RBDC gross-CONE reconciliation).
`tests/test_validate_capacity_prices.py`: MISO seasonal reproduction + concentration,
NYISO per-vintage scoring + sparse exclusion, flat-anchor vintage, curve inversion.

Verified clean before & after: `uv run python -c "import market_sim.runner"` and
`estimate_capacity_value(..., year=2026)` (PJM 50,000; MISO 48,000). Affected
suites green (`test_capacity*`, `test_validate_capacity_prices`, `test_storage`,
`test_reliability_floor`, `test_driver_directionality`, `test_forecast_storage_as_entry`).
Pre-existing, unrelated: `test_data_dictionary_sync::test_every_schema_has_a_section`
fails identically on `origin/main` (RC-1B/RC-0A noted it).

## 5. Follow-ups (not this session)

- **RC-1A MISO/NYISO curve-ON probe** consumes this: MISO forecast years price the
  seasonal RBDC (2023/24 hindcast prices the vertical vintage); NYISO stays fixed
  until R5a sign-off flips `CAPACITY_CURVE_ELIGIBLE_BY_ISO["NYISO"]`.
- **Seasonal fleet accreditation** would remove the one-position limit (lets the
  four seasonal positions differ) — a designed future item, not started.
- **Parameter-registry regeneration deferred** (same size reason as RC-1B/RC-1D:
  `frontend/data/parameters.json` too large for the `push_files` transport). New
  params (`CAPACITY_CURVE_ELIGIBLE_BY_ISO`, `MISO_SEASONAL_RBDC`, the two
  `seasonal_rbdc` fields) carry full inline citations in `constants.py` (the source
  of truth); `validate_parameters.py` is not wired into CI. Close in a follow-up
  with a size-appropriate transport.

## Files touched

`src/market_sim/config/constants.py` (seasonal structures + seam eligibility +
seasonal dispatch + MISO vintages), `scripts/validate_capacity_prices.py`,
`model-methodology-spec.md` §5.9, `tests/test_capacity_demand_curve.py`,
`tests/test_validate_capacity_prices.py`,
`docs/handoffs/capacity-price-validation-2026-07-16.md`,
`results/capacity-price-validation/validation.json`.

*Produced 2026-07-16 (RC-1C). No LP solved. No holdout year touched (rule 22).
Nothing on any dashboard. No default flipped.*
