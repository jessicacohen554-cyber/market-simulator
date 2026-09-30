# PRECOMMIT — miso-289: per-yard monthly coal pile with a prior-years minimum stock, pre-check written before it is measured

```
LANE    : miso-289 (owner ruling "Min-stock target design (Recommended)", miso-288 §5)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Fleet-only rebuilds + keeper committed P1 hourly sidecars + run payload
PROBE   : scripts/probes/_miso289_minstock_precheck.py
          --census : identification only (measured, §2; no price computed)
          default  : INC / PILE0 / CAND emulation (run AFTER this file is pushed)
STATUS  : pre-registration. No price or dispatch number in §5 exists yet.
```

## 1. The candidate (CAND)

One row family replaces the pooled flat `B/12` limb (`coal_fuel_inventory`, rule 19): the per-yard
cumulative month-end pile (`build_coal_monthly_pile` ceiling side, NWPP-NEXT-8, ratable receipts,
`S_dec` opening stock), with a **stock floor** `S_floor` held at **every** month-end:

    sum_{g at yard, t <= end of m} HR[g] * P[g,t]  <=  S_dec + m/12 * R  -  S_floor      (MMBtu)

At `m = 12` this is the yard's annual row less `S_floor`. No take floor (MISO has no contract census;
the NWPP take limb is not part of this candidate).

**Every month-end, not a chosen season.** A minimum operating stock is a standing inventory floor.
Restricting it to Sep–Dec would be a choice made with the 2022 residual in view; applying it
everywhere is the construction with no month selection in it.

## 2. Identification (rule 13, rule 21 — fixed before measuring)

Per yard row (the keeper's `coal_yard_groups`) and solve year `Y`:

- **`d_min`** = the yard's own **minimum month-end days on hand** over the EIA-923 stock years
  available in `[Y-3, Y-1]`. Days on hand = month-end stock / (that year's mean daily implied burn);
  implied burn = `stock[m-1] + receipts[m] - stock[m]` (Sch. 2 + Sch. 5). Year `Y`'s own stock path
  is never read.
- **`S_min`** = `d_min / 365 * R`, with `R` the receipts rate already in the yard's budget
  (`budget - S_dec`, prior two years). No new quantity.
- **`S_floor` = `min(S_min, S_dec)`.** A yard that opens below its own target holds what it has and
  never draws further. It is not made to rebuild: a rebuild schedule would be a new, unidentified
  timing parameter.
- Missing input: a yard with no usable stock year in the window gets `S_floor = 0` (the incumbent's
  zero minimum), never a substituted value.
- **Window coverage, stated before measuring.** Curated stocks start 2018. 2019 uses 2018 only
  (Jan 2018 implied burn is missing: no Dec 2017, so that year's rate is the mean of Feb–Dec);
  2020 uses 2018–2019; 2021–2025 use the full three years. The shorter window can only raise
  `d_min` (fewer months to take the minimum over), which makes the floor tighter, and that is
  reported, not corrected.
- **Forward story.** In a forecast year the floor is the fleet's own inventory policy in days of
  burn, read from the model's own simulated stock history (the pile it carries), converted at the
  same forward receipts rate. It responds to a fleet that retires units or burns harder.
- **DOF ledger.** `d_min`: measured (EIA-923 Sch. 2/5, prior years). `WINDOW = 3` years: a
  structural declaration, set here, never swept. Months at which the floor applies: all (no
  choice). Zero free parameters are fitted.

## 3. Census (measured with `--census`, identification only)

CENSUS_TABLE

## 4. The emulator and its gate

The miso-288 emulator (P1 bid stack = `mc_base` + startup markup, cleared hourly at the keeper's P1
LP quantity, excluding wind, solar, biomass and OTHER), generalised to cumulative rows: a row's
`λ` applies to every hour up to its month-end, so hour `t` of yard `y` carries
`HR * sum_{m >= month(t)} λ[y, m]`. `λ` by projected subgradient, ≤ 200 iterations, residual
reported. Must-run floors are reconciled to each arm's own rows (INC: the annual yard reconcile,
as the keeper; PILE0/CAND: scaled so the cumulative floor draw fits every month-end ceiling). The
startup markup is computed once, from the incumbent's floors, and shared by every arm.

Arms: **INC** (pooled `B/12` + yard annual), **PILE0** (pile, `S_floor = 0`; diagnostic, never a
candidate, not gated), **CAND** (§1).

**Gate V (fixed now, and changed from miso-288 before this probe runs).** miso-288's Gate V
required INC's price to sit within ±$1.5 of the keeper's and failed at +$3.57: the emulator carries a
level bias it shares with every arm (same stack, markup and clear). So:

- **V (gating):** INC monthly coal within **±1.5 TWh** of the keeper's P1 monthly coal in every
  month, and annual within **±3 %**, in every year run. This is what says the emulator's duals
  place coal where the LP's do.
- **Bias (reported, not gating):** INC − keeper P1 night median. Every price criterion in §5 is a
  **CAND − INC delta**, so the shared bias cancels. A surviving candidate's deltas remain emulator
  deltas, which is why the shards are still owed.

## 5. Kill rule (fixed now)

2022 is run first. If 2022 fails V, K1, K3 or K4, the lane stops there. Otherwise 2019–2021 and
2023–2025 are run and every criterion is checked in every year.

- **K1.** 2022 CAND night (h0–5) median ≤ INC − **$2.0**.
- **K2.** No year's CAND night median > INC + **$0.5**.
- **K3.** Jul+Aug CAND coal ≤ **1.10 × bench** Jul+Aug, in every year where CAND has a binding row.
- **K4.** Every year: |CAND annual coal − bench| ≤ |INC annual coal − bench| + **5 TWh**.

All four pass → build default-off, PRECOMMIT the seven year-isolated shards (miso-280 template
§7/§8, rules 34(c)/36). Any fails → FINDING, matrix, owner card. **No threshold, window or month
set moves after the probe runs.** Bench coal = run payload `volErr` COAL_* `a` (EIA-923 basis).

## 6. What this does not claim

- C3a is a mean over all hours. The mean shift is reported, not gated.
- It does not address why ~86 % of coal MW sits under a binding yard (miso-288 §4(b), offer-level,
  data-gated).
