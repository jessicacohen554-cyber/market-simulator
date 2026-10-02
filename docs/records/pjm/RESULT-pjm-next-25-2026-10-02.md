# RESULT: PJM-NEXT-25. The 2019–21 coal steepness is a coverage defect: 18 retired coal plants carry no measured tranche row (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO all read **NOT-YET**, with the same 10 failing cells.

**Solves:** none. On the owner's instruction (2026-10-02, *"don't launch a shard but the next session … should launch a nested shard chain"*), the arm is solve-ready but unsolved:
- `PRECOMMIT-pjm-next-25-2026-10-02.md`;
- the appended `thermal_tranches_PJM.csv`, on branch `claude/pjm-next-25-btbq8l` after this PR's merge.

| probe | artifact | card |
|---|---|---|
| `scripts/probes/_pjmnext25_coal_cohort.py` | `results/phase0/pjm/_pjmnext25_coal_cohort.json` | 1 |
| `scripts/probes/_pjmnext25_coal_nl_margin.py` | `results/phase0/pjm/_pjmnext25_coal_nl_margin.json` | 1b |
| `scripts/probes/_pjmnext25_ct_location.py` | `results/phase0/pjm/_pjmnext25_ct_location.json` | 2 |
| `scripts/probes/_pjmnext25_coalrows_fleet_delta.py` | `results/phase0/pjm/_pjmnext25_coalrows_fleet_delta.json` | 3 |

Data fetched (gitignored, licence-restricted): PJM zonal RT + DA LMPs 2019–2025, `data/raw/pjm-zonal-lmp/` (84 + 84 month files).

## 1. Card 1: what makes the 2019–21 coal response steep

**Per-plant tranche shares are year-invariant.** For the 44 coal plants present in every year, the keeper's shares barely move, 2019 → 2025:

| tranche | 2019 | 2025 |
|---|---|---|
| must-run | 0.20 | 0.22 |
| committed | 0.32 | 0.34 |
| econ | 0.44 | 0.40 |

The fleet econ share falls from 0.57 to 0.40 because of composition, not because any plant's shares change.

**The composition is a coverage defect.** `thermal_tranches_PJM.csv` has 29 COAL rows. It was derived over a 2024 window, so coal plants that had retired by then have no row. They fall to the class default:
- must-run 0;
- committed ≈ 0.05;
- econ ≈ 0.93.

Under `coal_mustrun_requires_measured_row` they also carry no floor.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| default-bin coal (GW) | **16.6** | **13.6** | **14.8** | 10.6 | 4.4 | 2.7 | 1.2 |
| default-bin within-plant contrast, model / real | **0.69 / 0.24** | **0.76 / 0.20** | **0.53 / 0.15** | 0.35 / 0.16 | 0.50 / 0.15 | 0.46 / 0.08 | 0.35 / 0.16 |
| measured-row within-plant contrast, model / real | 0.60 / 0.45 | 0.52 / 0.40 | 0.61 / 0.26 | 0.34 / 0.23 | 0.28 / 0.25 | 0.32 / 0.22 | 0.25 / 0.23 |
| default-bin model − real (TWh) | +6.9 | −1.3 | +4.7 | +2.6 | −3.7 | −0.6 | −0.7 |
| measured-row model − real (TWh) | +9.4 | +12.3 | +13.4 | +7.8 | +3.7 | +0.3 | +15.4 |

The default-bin cohort is the 2019–22 retirees, among them:
- Homer City, Sammis, Zimmer, Morgantown, Chesterfield;
- Montour, Brunner Island (coal years), Cheswick, Avon Lake;
- Waukegan, Will County, Conesville, Bruce Mansfield.

**Reading.**
- **The steepness is year-specific through the default-bin cohort.** Its plants respond 3–4× real. Measured-row plants are 1.3–2.3× real in 2019–21 and 1.1–1.5× afterwards.
- **The energy excess is not.** It sits mostly in measured-row plants (+9 to +13 TWh in 2019–21, +15 in 2025). The coverage defect explains the steepness metric, not most of the COAL_BIT TWh.
- **Ruled out as the year discriminator:**
  - the bituminous passthrough sigmoid, at 0.75 / 0.67 / 1.01 / 1.32 / 0.76 / 0.75 / 0.97 for 2019–25 (2019 ≈ 2023 ≈ 2024);
  - tranche availability, with ≈ 30 % zero-capacity hours in every year;
  - partial derates: real in-money coal output is 0.73–0.79 of its own monthly maximum, and the PJM partial-outage deriver already emits 0 (R-PJM).

**Card 1b: does real above-floor coal follow net load or margin?** Online hours, capacity-weighted means of within-plant partial correlations:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| real, net load (given zonal-RT margin) | 0.32 | 0.28 | 0.24 | 0.22 | 0.19 | 0.25 | 0.24 |
| real, zonal-RT margin (given net load) | 0.10 | 0.15 | 0.08 | 0.06 | 0.16 | 0.15 | 0.08 |
| keeper, own-price margin (given net load) | 0.47 | 0.48 | 0.34 | 0.28 | 0.71 | 0.40 | 0.41 |

- **Real coal is a weak load-follower in every year.** Its response to margin is a third to a half of its response to net load, and both are small (raw r ≤ 0.37). The keeper is a price-follower.
- **This is the binning hypothesis: confirmed, but not year-specific.** System and zonal RT give the same answer, so margin noise is not the cause.

## 2. Card 2: is real CT run-time explained by location?

**Correlation across plants** (capacity-weighted r of plant run-hours against in-money hour counts):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| real vs system DA | 0.05 | 0.45 | 0.42 | 0.14 | 0.25 | 0.20 | 0.31 |
| real vs zonal DA | 0.13 | 0.49 | 0.48 | 0.41 | 0.36 | 0.34 | 0.51 |
| keeper vs system DA | 0.78 | 0.90 | 0.87 | 0.81 | 0.85 | 0.79 | 0.86 |

**Real − keeper CT TWh by zone:**

| zone | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| AEP-Ohio | +2.6 | +1.7 | +3.0 | +3.7 | +3.8 | +5.3 | +2.5 |
| Dominion | +2.1 | +1.5 | +2.2 | +2.4 | +2.3 | +1.3 | +0.1 |
| ComEd | +0.5 | +0.6 | +1.4 | −2.4 | −3.7 | −5.0 | −5.2 |
| West-APS | +1.0 | +0.4 | +0.1 | +0.9 | −2.1 | −2.9 | −2.8 |

- **Location helps but does not close it.** Zonal DA beats system DA in every year, by +0.04 to +0.27. Real CT run-hours remain weakly price-ordered across plants (r ≤ 0.51), against the keeper's 0.68–0.90.
- **The zonal residual is persistent and zone-shaped.** After the zonal-DA predictor, AEP-Ohio and Dominion CTs run more hours than their local price explains in most years, and ComEd fewer from 2022.
- **That pattern points at out-of-market (reliability / BOR) commitment.** No measurement is on disk. **OPEN.** The next measurement is an intake of PJM's Balancing Operating Reserve credits by zone or unit type (IMM State of the Market).

## 3. Card 3: the coverage repair, verified at zero LP

**The arm.** It reuses the existing soco-70 deriver mode, the SOCO keeper precedent:

```
derive_thermal_tranches.py --iso PJM --years 2019 … 2025 --coal-unit-coverage
```

- It appends **18 COAL rows**, each from the plant's own CEMS coal units over its operating years.
- The 29 existing rows stay byte-identical; the old file is an exact byte-prefix of the new one.
- There is no `ScenarioConfig` change and zero DOF.
- **Rule 23 citation:** the source-data change is that the backcast span now covers these plants' CEMS years. Their rows were never derived.

**Fleet delta**, from a real-fleet `fleet_only` rebuild of the keeper recipe with `pjm_da_virtual_bids` off:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| LP units moved | 165 | 152 | 138 | 98 | 41 | 31 | 72 |
| … outside the appended plants (`min_gen` only) | 22 | 25 | 19 | 11 | 2 | 0 | 0 |
| floored TWh at appended plants, incumbent → candidate | 0.33 → 5.93 | 0.23 → 5.38 | 0.32 → 5.10 | 0.06 → 2.76 | 0.00 → 0.26 | 0.00 → 0.44 | 0 → 0 |

- **Confinement holds.** Outside the appended plants, `pmax` and the offer never move. The foreign `min_gen` moves are ±0.05 TWh in total: the existing reliability floor re-allocating within its ComEd and West-APS limbs.
- **Each retiree gains a measured must-run block** (e.g. Zimmer 531 MW, Homer City 271 MW) and a committed block in place of the econ default.
- **Their capacity-weighted P0 cost falls by $3–8/MWh.**
- **Expected direction is more coal in 2019–21,** so COAL_BIT likely worsens. That is the rule-14 consequence of replacing a default with measured data, not a reason to skip it.
- **Rule 20 headroom:** keeper coal binding-floor shares are ≤ 8 % of class energy, against a 30 % budget.

**G-DRIFT `d9668d84`..HEAD: 19 solve-path commits, all INERT for PJM.**
- NWPP per-unit fuel-split delete: PJM selectors are off.
- ERCOT ORDC / SWCAP: gated; the 1-D penalty path is value-identical.
- NYISO gas hubs and `nyiso_li_tsl`: gated.
- SOCO `INTERFACE_NEIGHBORS["SOCO"]`.
- Probes, CI and docs.

Together with NEXT-17 §4 and NEXT-18 §3, the chain from the keeper pin is complete.

## 4. Next

1. **Solve the arm:** one shard per year, 2019–2025, per the PRECOMMIT. The shard chain belongs to the next session.
2. **BOR intake** for card 2's zone residual.
3. **The measured-row coal excess** (+9 to +15 TWh in 2019–21 and 2025) remains the main COAL_BIT object. Card 1b says it is a load-follower vs price-follower structure (an LP-step vs CEMS conduct question). No measured, zero-DOF lever is identified yet. **OPEN, not a limit.**
4. **The Tait remap** may ride along as a rule-14 data repair.
