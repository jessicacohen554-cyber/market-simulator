# FINDING — miso-300: lag-aware pooled MISO gas variable transport (one `v` per plant, seven receipt years, the print's lag as a regressor) — phase 0, zero LP

```
LANE    : miso-300 (owner ruling 2026-10-02, miso-299 decision card "What should miso-300 do?": "Lag-aware pooled estimator (phase 0)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), legs at 8f765fef — unchanged
LP      : none in this document. Fleet-only rebuilds (miso-297 census machinery) cleared at the keeper's own P1 thermal quantity
STATUS  : §0 committed BEFORE any lag-aware table or census number existed; §§1–4 are placeholders at that commit and are filled afterwards
VERDICT : (filled in §4)
CELLS   : gas_marginal_commodity_pricing R, gas_variable_transport R — move only on a scored full-span result (rule 28)
PROBES  : scripts/data/derive_miso_gas_variable_transport_lagaware.py -> data/raw/reference/miso_gas_variable_transport_lagaware.csv (+ .pool.csv),
          results/phase0/miso/_miso300_lagaware_table.json; scripts/probes/_miso300_lagaware_census.py -> results/phase0/miso/_miso300_lagaware_census.json
```

## 0. Pre-stated reading (fixed before any number)

**The ruling.** Owner, 2026-10-02 (miso-299 card *"What should miso-300 do?"*): **"Lag-aware pooled estimator (phase 0)"** — re-fit one
`v` per plant on all seven receipt years with the month's hub change as a regressor (the −0.69 lag slope the frozen derive measured
becomes a term, not a contaminant). An estimator change on a frozen derive is admissible only under an owner ruling (rule 23 admits
source-data updates alone); this card is that ruling. Zero LP; pre-stated reading first; shards only if it clears.

**The object.** The frozen table `data/raw/reference/miso_gas_variable_transport.csv` fits `print − hub = v[p] + F[p]/burn` on the
2023–2025 receipts pooled. miso-298 solved the ruled gas form with it over 2019–2025 and was killed by K-1 (the table's level sits above
the 2019–2022 print-over-hub wedge, so the form RAISED CC_REGULAR fuel there). miso-299 showed a per-year re-fit fails because the
single-year intercept absorbs the print's lag on the year's hub trajectory (monthly CC wedge vs Δhub r = −0.54 to −0.85). The lag-aware
estimator removes that term explicitly, so one pooled `v` per plant can be identified on all seven years at once.

**The estimator, declared now and never swept.**

```
wedge[p,m] = v[p] + F[p] / burn[p,m] + λ · Δhub[p,m]          burn-weighted WLS, receipt years 2019–2025 pooled
Δhub[p,m]  = hub_m − hub_{m−1}  on the plant's own hub kind (Chicago flow-day staircase monthly mean for the Chicago and MidCon
             zones, Henry Hub trade-day for MISO-South; `_hub_month_means` of the frozen derive). January takes the prior year's
             December from the prior year's staircase (both daily series carry 2018, so January 2019 is in the panel).
```

* **λ is ONE fleet-wide coefficient.** The lag is a reporting convention of the EIA-923 monthly print (an average over the month's
  takes, lagging the hub), common to the fleet; it is not a plant or class attribute. Per-class λ values are REPORTED as a diagnostic
  and used for nothing. Never per plant.
* **Two steps, both burn-weighted.** Step 1 estimates λ jointly with every plant's own `v[p]` and `F[p]` on the pooled panel (every
  gas plant with ≥ 3 admissible plant-months; a plant with fewer is fitted exactly by its own two terms and carries no information on λ).
  Step 2 forms the lag-cleaned wedge `wedge − λ·Δhub` and runs the FROZEN derive's own machinery on it unchanged: `_fit` (WLS on `1/burn`,
  weight = burn), the own-rung bars `MIN_MONTHS 12` and `MIN_BURN_SPREAD 2.0`, and the ladder own → zone|group → group → MISO-wide.
  So `v` is exactly the frozen estimator applied to a wedge with the lag term removed, and nothing else changes.
* **The offer is still `hub + v[p]`.** λ never enters the offer; it only cleans the identification. Rule 13: `v` stays a contractual
  attribute of the delivery path; the forward analogue is `v` carried forward and re-identified by this same formula on each new
  EIA-923 vintage. The frozen table is NEVER overwritten: the output is the companion `miso_gas_variable_transport_lagaware.csv`
  (+ `.pool.csv`) in the frozen table's exact format, read by the unchanged consumer `_load_miso_gas_variable_transport`.
* **Admissible months** are the frozen derive's (`quantity > 0`, `price_per_mmbtu > 0`, Natural Gas, a hub mean for that month).

**The reading, stated now.** PROCEED to a PRECOMMIT + 7 shards only if ALL THREE hold; otherwise FINDING only, both R cells stay R,
no field, no shard, and the owner gets a decision card with the measured numbers.

- **(a) Early years reversed.** The lag-aware table moves static fleet cap-weighted **CC_REGULAR fuel DOWN in each of 2019, 2020,
  2021 and 2022** against the keeper print (Δ < −$0.005/MMBtu, i.e. beyond the census identity tolerance), the miso-298 kill mechanism
  reversed.
- **(b) Training-tier gain kept.** It still moves CC_REGULAR fuel **DOWN in 2023 and in 2024** against the print (Δ < −$0.005/MMBtu),
  the direction the miso-298 K-4 gain came from. 2025 is reported, not gated (the IMM share is not published for it and K-4 did not
  gate it).
- **(c) Identification holds**, both halves:
  - the fitted fleet-wide λ has the measured sign and magnitude class: **−1.0 ≤ λ ≤ −0.4** (a one-month lagged average implies −1,
    a hub-tracking marginal cost implies 0; the frozen derive measured the month-over-month slope at −0.69 fleet-wide, −0.76 CC_REGULAR);
  - the regression-free cross-check agrees with `v` at **Pearson r ≥ 0.90** across own-rung plants (the frozen derive's two estimators
    agreed at 0.975). The cross-check is the plant's burn-weighted wedge over its top burn quartile **restricted to flat-hub months**:
    months whose |Δhub| is at or below the median |Δhub| of the whole pooled panel (one threshold for every plant, fixed by the data,
    not chosen), top quartile taken within those months. In a flat-hub month the lag term is ~0 by construction, so the cross-check
    sees `v` plus the plant's own residual fixed leg, exactly as the frozen check did.

Reported at full magnitude either way, per year: own-plant coverage (plants, capacity share, by class), `v` cap-weighted on CC_REGULAR /
CT_PEAKER / ST_GAS / all gas (table-weighted and fleet-weighted), λ fleet-wide with its standard error and the per-class diagnostic
values, the cross-check r, the static CC_REGULAR fuel move against the print and against the frozen table, static dispatch (coal /
CC_REGULAR / all gas / seam, mean GW), static q1–q2 and all-hours load-weighted price error, and the bid-stack coal marginal share (all
hours, quintile 1). Nothing is selected on any of these.

**If it proceeds (declared now).** A ScenarioConfig field `miso_gas_variable_transport_lagaware` (default off, MISO-gated, requires
`miso_gas_marginal_commodity_pricing` + `miso_gas_variable_transport`; registered in `_CACHE_KEY_OPTIONAL_FIELDS` in the same commit;
a row in `mechanism-matrix.js` and a cell in every shard, rule 28; forward analogue = this table carried forward) selecting the
lag-aware table in place of the frozen one. A PRECOMMIT in the miso-298 form (K-1 no C1 PASS→FAIL; K-2 COAL_*/CC_REGULAR in band or toward
actual; K-4 q1–q2 error shrinks in 2023/2024 AND does not grow in 2019/2020), pinned before any shard; seven shards (2022 first).

**Structural note (rules 1 / 13 / 14).** One `v` per plant across every scored year is the object the frozen derive's docstring names
and the one this estimator keeps; the change is to the identification, not to the object. The number is whatever the receipts say with
the reporting lag taken out; zero chosen scalars. The tension miso-299 recorded (a per-year value is a per-year fit) does not arise here.

## 1. Derive provenance (filled after §0 is committed)

_(placeholder)_

## 2. The lag-aware table (filled after §0 is committed)

_(placeholder)_

## 3. Census per year (filled after §0 is committed)

_(placeholder)_

## 4. Reading against §0, and what happens next (filled after §0 is committed)

_(placeholder)_
