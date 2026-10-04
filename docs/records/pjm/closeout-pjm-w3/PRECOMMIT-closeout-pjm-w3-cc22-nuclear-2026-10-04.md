# PRECOMMIT — closeout-PJM-w3: (A) own-year CC window + (B) nuclear winter-capability basis, keeper base

Written before any solve. Desk direction 2026-10-04: solve (A)+(B) on the **keeper** base, all 7 years, and (A)
alone if shard budget allows. Owner ruling on (B) is pending (frozen-derive basis, rule 23); the scored run is the
evidence for that ruling. Keeper `2026-10-03-closeout-pjm-nuc-keeper`, rubric v3.20.

## Mechanisms

- **(A) `mustrun_online_frac_per_year=true`** (existing field, recipe only). The CC committed window is sized on each
  year's own CEMS online share instead of the 2023–25 pooled vintage. The by-year artifact has no 2019 rows, so
  2019 is inert. Rule 14/17 vintage repair; the coal sibling is K. Phase-0 sizing (closeout-PJM-cc22 §3): CC Δ
  2022 −0.28 to −0.37, 2020 +0.07/+0.09, 2021 −0.26/−0.34, 2023 −0.52/−0.67, 2024 +0.02, 2025 −0.10/−0.13 TWh.
- **(B) `nuclear_winter_capability_basis=true`** (new, default off; commit on this branch). PJM nuclear pmax moves to
  the EIA-860 winter rating, capped at max(nameplate, summer). Availability becomes min(1, unclipped measured monthly
  CF × summer/winter). Predicted nuclear Δ (fleet-ratio arithmetic on the keeper's own units):
  - 2019 **+0.88**
  - 2020 **+0.65**
  - 2021 **+1.24**
  - 2022 **+0.73**
  - 2023 **+0.15**
  - 2024 **+0.90**
  - 2025 **+0.69** TWh
  The per-unit cap can only make these smaller. All of the change falls in months whose measured CF exceeds 1.0
  (Jan/Dec, plus 2020 Jun and 2021 Feb).

## Bars (fixed here)

- **R1 (B mechanics).** Nuclear Δ vs the keeper lies within [0.6×, 1.05×] of the prediction in every year
  (0.05 TWh floor for 2023), and the change is confined to the clipped months: |Δ| < 0.02 TWh in every other month.
- **R2 (A mechanics).** CC_REGULAR 2022 Δ (A+B) lies in [−1.0, −0.4] TWh. On the keeper base this is expected to
  leave **C1 CC_REGULAR 2022 FAIL** (+8.96 → about +8.2–8.3). The flip needs the Elliott base, which the desk
  recommends declining. Declared ex ante: **no gate flip is expected from this run**; it is a structural repair
  measurement.
- **Declared PASS→FAIL risk:** C1 CT_PEAKER 2021, now −7.92 against ±8.00. Winter nuclear (+1.24 TWh in 2021)
  displaces some CT. A CT 2021 flip is a reported structural consequence (rule 14), not a kill.
- **K1 (kill).** Any other C1 PASS→FAIL, or any C3a/C3b PASS→FAIL.
- **K2 (kill).** Nuclear Δ outside R1 in any year, which would mean the mechanism did something else.
- **(A)-only legs, if solved:** CC Δ within ±0.15 TWh of the cc22 §3 sizing above; no PASS→FAIL.

## Solve plan

Pin = this branch's build commit. Seven year-isolated shards replay the keeper recipe with
`--set mustrun_online_frac_per_year=true --set nuclear_winter_capability_basis=true`. Then seven more with only
`mustrun_online_frac_per_year=true`, as slots free (max 6 alive). Compose each set, score against the keeper, and
register as probes on the branch. RESULT, and a slot request only if one beats the keeper on structure with no
undeclared flip.
