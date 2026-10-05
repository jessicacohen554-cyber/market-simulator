# FINDING — closeout-MISO-w3f: the measured-carve CHP grid tranche is cycled like a merchant unit; steam-host cogens are online ~90 % of hours in CEMS

```
LANE    : closeout-MISO-w3 (desk 2026-10-05: "start zero-LP phase 0 on CHP grid-tranche under-dispatch")
BASIS   : the w3e arm legs (closeout_miso_w3e_<y>), reconciled bench (#7210)
LP      : none
PROBE   : scripts/probes/_closeout_miso_w3f_chp_dispatch_phase0.py -> results/phase0/miso/_closeout_miso_w3f_chp_dispatch_phase0.json
```

## 1. What holds the plants below their sold energy

The residual is the arm's CC_CHP C1 records: 2019 −9.70, 2022 −9.03.

The cap is not the constraint. Every plant's grid capacity exceeds its sold energy: in 2019 Midland's grid tranche is 1,692 MW (14.8 TWh) against 8.6 TWh sold. What binds is commitment and price, through three effects.

**(a) The committed tranche is offered above the econ tranches.** The P1 startup-amortization markup (`model/commitment.compute_monthly_markup`) prices each CHP plant's committed (min-load) band above its own econ band. It varies by month with the P0 run length.
- Midland 2019: committed $87.7 against econ $36.9 in January, and +$3 to +$18 through the rest of the year.
- 20 of 31 CHP plants are inverted in 2019. The mean inversion is $2.0–9.0/MWh, depending on year.
- Result: the band designed as the cheapest runs least. Midland's 586 MW committed tranche dispatched 0.26 TWh in 2019.

**(b) The model cycles units that CEMS shows never cycle.** Energy-weighted over the CHP plants with CEMS (16–18 plants):

| year | CEMS online share | model committed online share | CEMS starts/yr (median) | model starts/yr (median) |
|---|---:|---:|---:|---:|
| 2019 | 0.926 | 0.181 | 8 | 65 |
| 2020 | 0.917 | 0.235 | 8 | 116 |
| 2021 | 0.862 | 0.143 | 10 | 76 |
| 2022 | 0.906 | 0.180 | 6.5 | 66 |
| 2023 | 0.920 | 0.308 | 8 | 120 |
| 2024 | 0.933 | 0.400 | 7 | 205 |
| 2025 | 0.907 | 0.297 | 8.5 | 150 |

Midland was online all 8,760 hours in 2019 and 2023 (one start). Taft and Carville were online 96.7–100 % of hours with 1–3 starts.

**(c) The measured carve removed the implicit commitment.** Under the sector default, 35–70 % of each plant ran as a flat held-out BTM block. Under the measured share, the electrical host share is 2–25 %. The steam obligation, which is what keeps these units hot, is not the electrical share, and nothing in the LP now represents it on the grid tranche.

**Heat rate and outages are not the binding constraints.** The econ tranches clear at $24–28 and run at cap in most hours. Peak and duct tranches at $100+ never run, in either the control or the arm.

## 2. Existing mechanisms (rule 19 inventory)

| field | MISO cell | what it does | reach on this object |
|---|---|---|---|
| `chp_steam_following` | K (armed) | electrical host-share carve plus the CHP steam floor | already armed; under the measured share the floor scales with the electrical share |
| `chp_startup_covered` | no row (gap baseline) | exempts CC/CT/ST_CHP from the P1 startup markup ("the host's steam demand keeps the unit hot") | **this object (a)**: registered here, untested in MISO |
| `chp_steam_floor_p25`, `chp_steam_duty_window`, `chp_steam_floor_conduct_scope`, `chp_export_floor_measured`, `chp_layup_duty_split` | U / unregistered | measured steam-floor level/window variants built on the thermal-tranche artifact | MISO's thermal tranches carry no CHP measured rows (miso-192), so most are inert here |

`chp_startup_covered` is a cost-side commitment parameter (rule 18) and adds no floor (rule 17). It is supported by the measured run-length evidence in §1(b).

## 3. Static reach: committed tranche priced at econ (`chp_startup_covered`)

**Method.**
- **Gain:** committed headroom in hours where the plant's econ-low tranche is at cap and the committed band carries a markup.
- **Displacement:** walked down the solved stack at or below each hour's marginal offer, as in w3d.

**Gain:** +7.1 to +9.8 TWh/yr, about 97 % of it CC_CHP.

**Displaced:** CC_REGULAR 2.4–5.2, COAL_PRB 0.8–1.8, imports 0.8–1.6, ST_GAS 0.3–1.1 TWh/yr.

**C1 on the reconciled basis, arm → arm + startup-covered (static) → also + the w3c holdout's realised model deltas (additive):**

| year | CC_CHP | CC_REGULAR | ST_GAS | COAL_PRB | C3a (holdout's price delta only) |
|---|---|---|---|---|---|
| 2019 | −9.70 → −0.15 → +0.84 | −5.21 → −8.45 → −4.51 | −9.83 → −10.63 → −9.88 | −1.53 → −3.36 → −0.65 | +4.7 → +7.3 % |
| 2020 | −7.08 → +1.78 → +2.97 | −5.48 → −8.77 → −4.87 | −8.01 → −9.07 → −8.04 | +3.24 → +2.03 → +3.95 | +8.0 → +11.0 % |
| 2021 | −7.88 → +1.43 → +2.44 | −9.52 → −14.76 → −9.56 | −5.39 → −5.71 → −5.16 | +4.26 → +3.13 → +4.57 | −6.8 → −3.4 % |
| 2022 | −9.03 → −0.80 → +0.22 | −5.63 → −10.41 → −4.44 | −5.91 → −6.26 → −5.38 | +5.44 → +4.67 → +4.79 | −5.5 → −2.1 % |
| 2023 | −5.08 → +2.71 → +3.95 | −2.90 → −5.82 → −2.45 | −2.74 → −3.50 → −2.26 | −1.48 → −2.50 → −1.14 | +2.8 → +5.6 % |
| 2024 | −2.01 → +4.92 → +5.89 | +0.62 → −1.82 → +0.81 | −3.99 → −4.92 → −3.77 | −2.02 → −2.89 → −1.52 | +0.2 → +2.7 % |
| 2025 | −6.69 → +1.01 → +1.94 | +3.17 → −0.21 → +2.57 | −5.53 → −6.04 → −5.16 | −5.30 → −6.37 → −5.40 | −6.4 → −3.9 % |

**Reading.**
- **Startup-covered alone** closes every CC_CHP record. The displacement then lands on CC_REGULAR, which fails 2019–2022 at first order. That is a trade, not a close.
- **The model's fossil fleet is short in total** (2019: about −30 TWh summed over the gas and coal classes). The space it lacks is held by about 10–15 TWh/yr of injected chp=Y host biomass/OTHER that never reaches the grid (w3c).
- **The three CHP corrections are one object**, the host/grid partition:
  - w3c removes host-only biomass/OTHER;
  - w3e uses the measured electrical host share;
  - w3f restores steam-host commitment.
- **With all three stacked**, the first-order picture leaves:
  - CC_REGULAR 2021 (−9.56);
  - ST_GAS 2019 (−9.88, MISO-F1 VLR);
  - ST_GAS 2020 (−8.04, on the line);
  - C3a 2020 (+11.0 % before the commitment fix's own price drop, about −0.5 pt; borderline).

**Static caveat.** This is an upper bound on the gain (econ-low-at-cap hours only), and the holdout deltas were measured on a different control (the seam probe), so interactions are not captured.

## 4. Rule-13 admissibility

The exemption's driver is measured: CEMS run length and starts per plant, which are reproducible for any forward year from CAMPD. Its forward story is that steam-host contracts keep CHP units hot; the Schedules 6/7 host-use filing persists. It sets no floor, no window and no tuned value, and adds zero DOF.

A measured per-plant variant (exempt only plants with CEMS online share ≥ x) would add a threshold, which is a parameter. It is not proposed.
