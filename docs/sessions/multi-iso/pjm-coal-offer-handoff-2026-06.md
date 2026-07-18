# PJM HANDOFF — fix the coal over-run via offer curves (post outage re-gate)

MISSION (claude.md #1/#11/#12): production-cost-grade PJM backcast. NO magic
numbers, NO curve-fitting to the residual; every input measured & forecastable.
A keeper is the most STRUCTURALLY FAITHFUL run, not the lowest MAE — right market
structure first, offer tuning second. A negative result is a valid deliverable.

SETUP: `uv sync`. `git config user.email noreply@anthropic.com; git config
user.name Claude`. Scoring symlinks (inputs/ gitignored):
```
mkdir -p inputs/processed
ln -sf ../data/raw/reference/custom-bin-assignments.csv inputs/custom-bin-assignments.csv
ln -sf ../data/raw/reference/master-plant-registry.csv inputs/master-plant-registry.csv
ln -sf ../../data/raw/_processed-legacy/plant_emission_rates.parquet inputs/processed/plant_emission_rates.parquet
ln -sfn ../data/raw/_validation-source inputs/calibration
```
Branch merges to main & goes stale between turns: `git fetch origin`; if behind,
`git checkout -B <branch> origin/main`. MEMORY: a per-plant PJM solve peaks
~8.7 GB on a 15 GB box → RUN ONE YEAR AT A TIME (2 concurrent = silent OOM);
~7–11 min/yr. Run pattern (probes under scripts/probes/): per-year runner →
`_pjm_aswh_merge.py` → `_pjm_score.py`. Clone `_pjm_retiree_run.py` (keeper
runner, retiree_cems_cap=True) for any PJM probe so the keeper baseline holds;
add new flags by keyword.

========================================================================
THE KEEPER (start here)
========================================================================
`results/calibration/pjm_38` = dashboard `pjm 38 outage-regate`, registry
`frontend/data/backcast/registry/2026-06-21-pjm-38-outage-regate.json`. It is the
pjm-36 retiree-cems config (`retiree_cems_cap=True`, per-unit retiree COD fix +
within-window retiree CEMS cap) re-solved on the **net-load-filtered outages**
(commit b0c41cb, now on main). Reproduce per year with
`scripts/probes/_pjm_retiree_run.py <year> <out>` then merge with
`_pjm_aswh_merge.py`; the outages are auto-picked from `data/raw/`. (NOTE: the
git proxy was down at handoff; `run_config.json` and the dashboard payload
`runs/2026-06-21-pjm-38-outage-regate.js` may be missing on the branch —
regenerate via the runner + `dashboard_add_run.py` if so. The keeper config is
fully captured in `pjm_38/meta.json` and `pjm_37/run_config.json`.)

========================================================================
THE PROBLEM (what to fix) — see docs/multi-iso/pjm-outage-regate-2026-06.md
========================================================================
The outage re-gate (right-structure exogenous input, KEPT) amplified PJM's
coal over-run and over-export, which is now the dominant structural miss
(`_pjm_score.py pjm_38`, model vs actual, resid%):

| year | coal-tot | COAL_BIT | gas | net-export (info) | LMP load-wtd |
|---|---|---|---|---|---|
| 2023 | +17.3% | +16.8% | +4.9% | +69% | −1.1% |
| 2024 | +13.9% | +13.4% | +5.7% (FAIL) | +65% | −11.4% |
| 2025 | +22.8% | +21.9% | +3.7% | +204% | −19.3% |

COAL_BIT is the offender (COAL_PRB/WC are small absolute). The cost-based LP runs
the freed cheap **take-or-pay** coal at the margin and **exports the surplus**.
The LMP runs UNDER actual (the $75–200 afternoon-peak regime is empty: model
~0 hrs>$75 in Jul/Aug vs actual 57/110/124) — and these two misses are LINKED:
**coal priced too cheap at the margin both over-dispatches coal AND suppresses
the clearing price.** Fixing the marginal coal offer can move both.

========================================================================
THE TENSION TO RESOLVE FIRST (do not skip — claude.md #1/#11)
========================================================================
The project DELIBERATELY prices coal cheap (`docs/multi-iso/pjm-coal-mustrun-floor.md`,
the ERCOT playbook in the prior handoff): take-or-pay sunk fuel ⇒ coal bids near
zero for its contracted/must-run base, and ERCOT EXCLUDES coal from offer tuning
by design. The prior session ruled the PJM coal-over "settled, forecast-native
merit order — don't chase via coal cost." This handoff REVISITS that, because the
re-gate made coal-over the largest miss. Resolve the tension HONESTLY before
tuning anything:

1. **Is the over-run DOMESTIC dispatch or EXPORT?** Decompose first (probe #0).
   The net-export resid (+69/65/204%) is huge — much of the extra coal MWh may be
   leaving PJM, not setting PJM's price. If so the lever is the **interchange /
   export seam** (`reference_price_interface`, `priced_interchange`), not coal
   cost: the neighbor seam under-prices PJM coal's export opportunity, so the LP
   dumps cheap coal across the border. Tightening the export hurdle / neighbor
   reference price curbs the export WITHOUT re-pricing coal — respects take-or-pay.
2. **Take-or-pay covers the BASE, not the MARGINAL tranche.** Coal's
   contracted/must-run base legitimately bids low; but the *incremental* (econ_high
   / peak) tranche that sets the clearing price in the $30–75 body has no take-or-pay
   justification for bidding below its delivered variable cost. Raising ONLY the
   marginal coal tranche's offer (not the base) is defensible and is the
   structure-faithful fix — not curve-fitting if it's anchored to a measured
   delivered coal $/MMBtu × heat-rate, not to the coal-MWh target.

========================================================================
LEVERS (measured / forecastable only — pick by what probe #0 shows)
========================================================================
Keeper offer overrides today (`pjm_38/meta.json` → `offer_curve_overrides`):
- COAL_BIT: committed 0.548, econ_low 0.6556, econ_high 1.2664, peak 1.044,
  econ_low_share 0.55; plus `coal_bit_passthrough_floor` 0.76 (the BIT fuel
  passthrough sigmoid floor — how much of the delivered coal price the BIT offer
  carries). COAL_PRB/WC/LIGNITE have their own overrides + the tiered/sigmoid
  passthrough machinery (`coal_*_passthrough_*` flags, scenarios.py).

A. **Export seam (try FIRST if probe #0 says export-driven).** The
   `reference_price_interface` builds neighbor seam prices from gas × heat-rate ×
   load-shape (a hurdle in $/MWh). Audit whether the seam under-prices PJM's coal
   export (the export sinks clear at a price the cheap coal beats). The measured
   anchor is the actual PJM net-interchange (the `interchg` actual in the
   scorecard: ~40/33/18 TWh) and the actual hub/seam basis. Make the export bind
   on the measured net-export, not fit to it. `scripts/probes/_pjm_interchange_ab.py`
   exists — start there.
B. **Marginal coal offer / passthrough (the coal-cost lever).** Raise the BIT
   marginal tranche (econ_high / peak) and/or `coal_bit_passthrough_floor` so the
   incremental coal MWh carries its delivered variable cost. MUST be anchored to a
   MEASURED delivered coal $/MMBtu (EIA-923 / the coal supply curve already in the
   model, `coal_plant_monthly_pricing`/`coal_supply_repricing`) × the measured
   heat-rate — NOT to the coal-MWh or LMP target. Leave the must-run/base tranche
   cheap (take-or-pay preserved). Check: does PJM publish a measured coal offer
   analogue (cost-based offer caps / Schedule data)? If not, derive the cost from
   delivered fuel + VOM and DO NOT fabricate a market-offer curve.
C. **CC body offers (ERCOT-style, the LMP body — secondary).** If after A/B the
   $30–75 body LMP is still under, measured 60-Day DAM CC offer multipliers,
   CC-only (`derive_dam_offer_hrmults.py`, `docs/ercot-dam-offer-hrmults-2026-06.md`).
   FIRST verify PJM publishes a 60-Day DAM offer analogue (PJM is less transparent
   than ERCOT). If not, data-blocked — do NOT fabricate. Coal EXCLUDED here by
   design; full-gas craters ST/CT via CT↔ST coupling (ERCOT finding) — CC-only.

========================================================================
PROBES (gate cheap things first)
========================================================================
- **#0 (DO FIRST, no solve): decompose the coal over-run.** From the keeper
  bundle, attribute the +17/14/23% coal MWh to (a) extra EXPORT vs (b) extra
  DOMESTIC dispatch, by month and zone; and identify whether the extra coal is
  the MARGINAL (price-setting) tranche or inframarginal baseload. This decides
  A vs B and whether fixing coal will move the LMP. Use the bundle dispatch +
  system parquets + `analyze_lmp_residual.py`; build a small probe if needed.
- **#1 export seam (one year):** clone `_pjm_retiree_run.py`, tighten the export
  seam to the measured net-export anchor, re-solve 2024 (the worst LMP year),
  score. Target: net-export resid shrinks toward actual; coal-tot falls; LMP
  rises toward actual; gas does not regress. Profile memory.
- **#2 marginal coal offer (one year):** raise the BIT marginal tranche /
  passthrough to the measured delivered-cost anchor, re-solve 2024, score. Target:
  COAL_BIT resid shrinks; LMP body lifts; must-run base unchanged; no gas/CC
  blow-up. If the only way to hit the target is an un-anchored multiplier, STOP
  AND REPORT (claude.md #11) — that's curve-fitting.
- **#3 combine the winners**, gate ALL 3 years + the tail (mean, load-wtd LMP MAE,
  hrs>$200, per year, old-keeper-vs-new), register on the dashboard
  (calibration-report skill, label "pjm 39 …", top-15 PJM retention). Promote to
  keeper ONLY if it gates clean AND is structure-faithful (measured anchors).

GUARDRAILS: No multiplier fit to the coal-MWh or LMP residual. Anchor every coal
offer change to a measured delivered fuel cost × heat-rate; anchor the export
seam to measured net-interchange/basis. Preserve take-or-pay on the must-run base.
Don't touch the outage input (settled — pjm_38 is the keeper). Solve one year at
a time. A negative result (e.g. "the over-run is export-side, coal cost is not the
lever" or "PJM publishes no measured offer ⇒ data-blocked") is a valid deliverable.

KEY FILES: scenarios.py (`offer_curve_overrides`/`offer_curve_by_group`,
`coal_*_passthrough_*`, `coal_bit_passthrough_floor`, `coal_supply_repricing`,
`coal_plant_monthly_pricing`, `reference_price_interface`, `priced_interchange`);
scripts/probes/_pjm_{retiree_run,aswh_merge,score,interchange_ab}.py;
scripts/archive/analyze_lmp_residual.py; scripts/data/derive_dam_offer_hrmults.py.
DOCS (READ FIRST): pjm-outage-regate-2026-06.md, pjm-coal-mustrun-floor.md,
pjm-lmp-residual.md, ercot-dam-offer-hrmults-2026-06.md. Price-formation /
reserve co-opt work (pjm-reserve-ordc.md) is PARKED behind this coal fix.

FIRST STEPS: (1) fetch/rebase, identity, symlinks, uv sync; confirm pjm_38 is the
keeper (registry) and reproduce/score it. (2) Probe #0 decomposition — export vs
domestic, marginal vs baseload — BEFORE touching any offer. (3) Pick A or B from
what #0 shows; gate cheap (one year) first. Push to a PJM feature branch via the
GitHub API if the git proxy is down; do NOT open a PR unless asked.
