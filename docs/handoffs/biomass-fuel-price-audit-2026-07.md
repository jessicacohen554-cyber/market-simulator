# Biomass fuel price — P-1D fuel-audit residual, closed (2026-07-21)

**Scope.** Close the last open item of the P-1D forecast-driver fuel audit (D2:
"oil/biomass flat scalars"). Gas / coal / oil / nuclear were wired to AEO-derived
paths by P-1D and re-vintaged to AEO2026 by FF-G2; biomass was the remaining flat
scalar. This session investigated whether biomass can take an AEO forward path
like the others (it cannot — §2) and specified the correction for its misleading
citation (landed in `resolve.py` + this doc; the source-constant and registry
edits are deferred to a byte-safe push — §4). **Forecast-scoped, no solve or
scoring of any holdout year (rule 22) — no LP ran at all.**

## 1. P-1D fuel audit — closure status (independently verified this session)

The audit this branch was opened against is **already implemented and merged on
main** (landed by P-1D for AEO2025, re-vintaged to AEO2026 by FF-G2, 2026-07-20).
The task description (constants "still run off hardcoded snapshots";
`HENRY_HUB_TRAJECTORIES` at `constants.py:931`; the `TODO: verify against AEO
Table 13`) describes the **pre-P-1D** file — those line numbers, the TODO, and the
hand-typed values no longer exist. The constants were refactored into
`config/fuel_trajectories.py` and the resolvers into the `data/fuel/` package.

Independent verification performed here (no code change needed):

| Fuel | Forecast path | Consumed in dispatch | Verified |
|---|---|---|---|
| Gas | `HENRY_HUB_TRAJECTORIES` (AEO2026 T13 + ISO basis) | `resolve_annual_gas_price` → `resolve_fuel_prices` | ✅ |
| Coal | `COAL_PRICE_TRAJECTORIES` real-growth ratio on per-ISO `COAL_PRICE_BASE` anchor (forecast only) | `resolve_annual_coal_price` (mode-gated) | ✅ |
| Oil | `OIL_PRICE_TRAJECTORIES` (AEO2026 T12 distillate+residual blend, forecast only) | `resolve_annual_oil_price` (mode-gated) | ✅ |
| Nuclear | `NUCLEAR_FUEL_PRICE_HISTORICAL` (EIA-UMAR fuel-cycle cost, both modes) | `resolve_nuclear_fuel_price` | ✅ |

- **Constants byte-match the source.** Ran `scripts/data/derive_fuel_trajectories.py
  --aeo-year 2026` and diffed its output against the committed constants:
  **0 mismatches** across every forecast year for gas, coal, oil, and nuclear.
  The ≤2025 historical gas actuals are correctly kept measured (2025 = $3.52, not
  AEO2026's $3.47 base). `tests/test_fuel_trajectory_consistency.py` locks this.
- **Uncited escalators replaced.** The flat 1%/yr `COAL_PRICE_ESCALATION` and the
  flat oil scalar are superseded by AEO paths in forecast mode (backcast keeps the
  flat/measured fallback for byte-identity); nuclear's old `$0` default is now a
  real fuel-cycle cost. The silent last-YoY-ratio extrapolation tail is fixed
  (`_hold_flat_extrapolate`). All on-registry via `ScenarioConfig` paths (rule 24).
- **Tests green.** `test_fuel_trajectory_consistency.py`, `test_fuel.py`,
  `test_fuel_facade.py`, `test_curate_eia_aeo_fuel_prices.py` → **134 passed**.

Gas/coal/oil/nuclear are done. The only residual was biomass.

## 2. Biomass — can it take an AEO path? No.

**Finding: EIA's AEO publishes no forward delivered-biomass fuel price.** Verified
2026-07 against the live AEO2026 series catalog
(`api.eia.gov/v2/aeo/2026/facet/seriesId`, 13,727 series): the only biomass
"price" series is `prce_otc_elep_NA_wbm_bioig_NA_y13dlrkw` — a **$/kW capital
cost**, not a fuel price. Everything else biomass-tagged is CO₂-supply
(`sup_ccs_elep_..._bioengy_...`) or transportation biofuel. NEMS models biomass as
regional **supply curves + consumption**, not a single delivered-price projection.

So biomass **cannot** be wired the way `COAL_PRICE_TRAJECTORIES` /
`OIL_PRICE_TRAJECTORIES` were — there is no series to read. Inventing an escalator
would violate rules 5/13. This is the rule-14 "accurate data doesn't map to our
representation" case: biomass gets the same **held-flat real-anchor** treatment as
nuclear fuel (also no forward EIA/AEO series). This is a documented limitation, not
an un-closed gap.

## 3. Why the one published $/MMBtu number is rejected (rule 14)

EIA **SEDS** publishes an electric-power-sector "wood and waste" price in $/MMBtu
([sum_pr_eu](https://www.eia.gov/state/seds/sep_sum/html/sum_pr_eu.html)): **~$17.5
/MMBtu in 2024** (vs coal $2.51 / gas $2.79 in the same table). It is **deliberately
not adopted** as the marginal fuel cost. It is a blended
expenditure-over-consumption imputation over the whole reported wood+waste stream,
dominated by comparatively costly purchased-wood segments. At the fleet's ~13.5
MMBtu/MWh heat rate it implies a **~$240/MWh** marginal cost — which would zero out
the baseload/must-run biomass dispatch that actually runs (MSW, landfill gas, and
mill-residue units operate on waste-stream / tipping-fee economics, not purchased
wood). Using the "accurate" number literally would make results *less* reflective
of reality — the textbook rule-14 misalignment. It is cited in the constant so the
rejection is transparent (rule 11).

The model's **$2.50/MMBtu** is the cheap-waste-stream delivered cost (forest/mill
residue is delivered in the low-single-digit $/MMBtu range; MSW / landfill gas
lower still) — low enough to reproduce observed biomass dispatch. **Value unchanged**
(no residual tuning); only the citation was wrong.

## 4. Changes made / deferred (citation/documentation only — no value, no LP)

**Pushed this session:**

- `data/fuel/resolve.py` — the biomass docstring + inline comment (where the
  value is *consumed* into the LP fuel-cost array) now document that biomass is
  held flat in both modes because EIA/AEO publishes no forward biomass price
  (NEMS uses supply curves, AEO2026-API-verified), pointing at this doc.
- This handoff doc.

**Deferred to a byte-safe follow-up (NOT pushed — the containing files exceed
what inline `mcp__github__push_files` can reproduce without rule-27 truncation
risk):**

1. `config/fuel_trajectories.py` (~1,080 lines) — the `BIOMASS_PRICE_PER_MMBTU`
   comment still carries the misleading "AEO 2024" attribution. The corrected
   comment (drafted and verified this session) should: remove the "AEO 2024"
   source, document the AEO-API "no forward biomass price" finding + the
   held-flat-like-nuclear rationale (§2) and the SEDS rejection (§3). **The
   value stays $2.50 — no functional change.**
2. `frontend/data/parameters.json` (~32,000 lines) + `docs/parameter-citations.md`
   (~1,600 lines) — the `biomass_price_per_mmbtu` registry entry (auto-generated,
   also already ~160 lines stale vs `generate_parameter_registry.py` at HEAD).
   Set: source = the §2/§3 waste-stream/no-AEO-series text; `url` =
   `https://www.eia.gov/state/seds/sep_sum/html/sum_pr_eu.html`; drop the
   `auto-generated` flag; `last_verified` 2026-07-21. A clean generator regen
   both refreshes this entry and clears the pre-existing drift.

Both deferrals are documentation-only (no value, no dispatch effect); the
authoritative correct citation now lives in this doc and in `resolve.py`.

## 5. Optional future upgrade (only if biomass materiality rises)

Biomass is a small, rarely price-setting share of every ISO. If fidelity ever
matters, the upgrade path is an EIA-923 Schedule-5 biomass-receipts intake (the
same measured channel coal/gas use) to replace the $2.50 anchor with a
consumption-weighted measured delivered cost — still held flat (no forward series).
Not warranted now.
