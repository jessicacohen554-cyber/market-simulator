# FINDING soco-91 — zero-LP intra-day census: who sets SOCO's price, hour by hour, against lambda

**Owner ruling in force (soco-90 card, 2026-09-29):** "Zero-LP intra-day census (Recommended)". No solve, no
registration. Keeper unchanged: `2026-09-29-soco87-gas-hh-monthly` (`results/calibration/soco87_span`),
NOT-YET 7/4/0/1/2. Branch base `origin/main` 0a5eb910. soco-90's PR #6885 was still open, so its head is cited
as `ae3a6a567c2b076a37c9131db725bf94c450a7d0`.

## Conclusion

**No real intra-day structure outside the DO-NOT-REDO list explains the C3a residual.** The census splits it
into two offer-level gaps at two different setters. Both belong to adjudicated families:

- **Night (low-40 % λ hours, 46–63 % of them in 21:00–05:00 CST).** A CC_REGULAR plant sets the price in
  41–71 % of these hours, at its flat average-HR offer. λ is **0.75–0.83 × that offer in every year**. The ratio
  is stable across season, weekday/weekend, gas price, and whether the model's night coal is short (2019–21,
  2023–24) or long (2022, 2025). It is proportional to the offer and does not depend on the dispatch mix, so it is
  a price-level error, not a missing-MW error. Only two objects can make a proportional cut at the CC setter:
  a heat rate below average, or fuel below delivered cost. The first is CC incremental-HR offers (owner "Keep
  refused"; soco-85 measured incremental ≥ average above the ramp bottom). The second is replacement fuel or daily
  gas (closed: soco-85 §7, soco-88 R, soco-90 "Don't buy").
- **Afternoon (top-20 % λ hours, 58–71 % of them in 11:00–19:00 CST).** A CT_PEAKER sets the price in 37–67 %
  of these hours, at its average-HR offer and 10–35 % band loading. λ sits **+$1.0 to +$24.6/MWh above** that
  offer. The gap grows with gas price and spikiness (2019 +1.0, 2021 +8.3, 2022 +24.6, 2025 +14.6). That is
  CT start / no-load recovery (owner NO) or a daily/winter basis spike (closed).
- **Hydro + pumped storage: a real intra-day miss, but not a C3a lever.** In every year, the model's hydro plus
  PS discharge is 140–570 MW below EIA-930 in the low-40 % hours and 650–1,200 MW above it in the top-20 % hours.
  A perfect-hindsight reshape (§4) moves the low-40 % error by $0.0–0.3/MWh and the top-20 % error by ~0.
  C3a moves ≤ 1.1 pp and no status flips.
- **Floors cannot be the night cause.** In an LP a floored unit is at its lower bound and cannot set the dual,
  so a floor can only lower price. D-2 floors at night are nuclear (5.1–7.3 GW, structural), CHP steam (~220 MW)
  and the ST_GAS per-plant floor (190–234 MW). Out-of-merit MW is 256–382 MW. None sets the night price.
- **Interchange** is the measured EIA-930 schedule on the model's own clock. Model demand equals EIA-930
  demand + total interchange to the MW in every year. It is not a lever.
- **Offer-curve band multipliers (rule 1 channel).** SOCO's gate G5 posture is identity, because SOCO takes no
  offers. Condition (c) needs an ex-ante value, and a cost-based pool publishes no offers to set one from. The
  census shows what a non-identity config would have to do: cut the CC bands at night and raise the CT bands in
  the afternoon. That is the soco-89 two-sided residual, so any value picked for it would be read off the residual,
  which condition (c) forbids.

C3a stays failed in 2019, 2020 and 2022 for the reason soco-89 gave. This census finds nothing new to build for C3a.

## 1. Method

Probe: `scripts/probes/_soco91_intraday_census.py` (new). Per year:

- It does a `fleet_only` rebuild of the keeper recipe (`replay_keeper.run_year_kwargs` + `derived_run_year_inputs`,
  the soco-89/90 construction). That gives each unit's `mc_base`, `pmax × availability`, `min_gen` and its D-2
  `min_gen_mechanism`.
- It reads the keeper's committed `hourly/{system,class_band_hourly,class_hourly,storage}_<y>.parquet`.
- It reads Southern's λ on the bench's dense CST 8760, and EIA-930 `SOCO hourly` on the model's own positional
  clock (`_eia_hourly_frame_filled`, fixed UTC−6). Zonal prices are identical in every hour (the links cannot
  bind), so the system price is one series.

**Setter rule, tighter than soco-89.** A unit counts as the setter only if two things hold: its offer is within
±$0.50 of the price, and its class-band is interior that hour (strictly between its floor and its available
capacity, 1 MW margin). This matches 78–93 % of hours. SOCO's CC plants carry one flat HR across all four
tranches, so which band sets the price within a plant is an LP tie. The tables report the class, and the band
label is not evidence.

C3a reproduces exactly: +14.0 / +14.4 / −2.4 / −12.7 / +2.3 / −3.6 / −1.5 %.

## 2. Who sets the price, and at what offer

Night = low-40 % λ hours at 00–05 CST. Afternoon = top-20 % λ hours at 12–18 CST. Offers are `mc_base`
($/MWh), fuel is $/MMBtu, loading is the setter band's MW ÷ available MW.

| year | night setter (share) | offer / HR / fuel / loading | λ | λ ÷ offer | afternoon setter (share) | offer / HR / fuel / loading | λ | λ − offer |
|---|---|---|---:|---:|---|---|---:|---:|
| 2019 | CC_REGULAR 0.41 | 23.10 / 7.43 / 2.84 / 0.89 | 17.35 | **0.75** | CT_PEAKER 0.37 | 34.89 / 11.35 / 2.77 / 0.35 | 35.85 | **+1.0** |
| 2020 | CC_REGULAR 0.45 | 19.05 / 7.42 / 2.30 / 0.84 | 14.30 | **0.75** | CT_PEAKER 0.47 | 29.86 / 11.40 / 2.33 / 0.26 | 31.15 | **+1.3** |
| 2021 | CC_REGULAR 0.53 | 27.72 / 7.31 / 3.53 / 0.76 | 22.93 | **0.83** | CT_PEAKER 0.52 | 55.94 / 10.65 / 4.93 / 0.10 | 64.20 | **+8.3** |
| 2022 | CC_REGULAR 0.71 | 49.28 / 7.25 / 6.53 / 0.71 | 38.31 | **0.78** | CT_PEAKER 0.63 | 108.61 / 10.79 / 9.77 / 0.26 | 133.19 | **+24.6** |
| 2023 | CC_REGULAR 0.57 | 24.97 / 7.53 / 3.06 / 0.87 | 20.23 | **0.81** | CT_PEAKER 0.67 | 37.05 / 11.31 / 2.97 / 0.26 | 43.35 | **+6.3** |
| 2024 | CC_REGULAR 0.52 | 22.04 / 7.42 / 2.71 / 0.83 | 17.26 | **0.78** | CT_PEAKER 0.63 | 35.16 / 11.03 / 2.88 / 0.19 | 46.57 | **+11.4** |
| 2025 | CC_REGULAR 0.69 | 30.90 / 7.32 / 3.95 / 0.77 | 24.94 | **0.81** | CT_PEAKER 0.57 | 47.76 / 11.14 / 3.99 / 0.21 | 62.37 | **+14.6** |

The second night setter is COAL_PRB in most years (9–17 % of hours; COAL_BIT in 2022). Its offer is $0.3–3.7
above the CC setter's, and λ sits $4–7 below it. Hydro/storage (its budget dual) sets up to 15 % of night hours,
also above λ. Every class that sets a night price prices above λ, so this is a fleet-wide level, not one class.

## 3. The night gap does not follow commitment or dispatch mix

Mean hourly gap (model − λ, $/MWh) in the low-40 % hours:

| year | JJA | DJF / MAM / SON | weekday | weekend | coal, model − EIA-930 (MW) | gas, model − EIA-930 (MW) |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 4.6 | 8.2 | 7.6 | 7.0 | −954 | +1,500 |
| 2020 | 3.3 | 6.3 | 5.6 | 5.6 | −376 | +1,017 |
| 2021 | 4.4 | 6.8 | 6.4 | 6.0 | −824 | +1,036 |
| 2022 | 10.1 | 9.6 | 9.4 | 10.1 | +490 | −449 |
| 2023 | 2.7 | 6.2 | 5.3 | 5.4 | −372 | +655 |
| 2024 | 3.2 | 6.5 | 5.9 | 5.4 | −669 | +686 |
| 2025 | 3.7 | 9.2 | 8.0 | 7.6 | +466 | −45 |

- **Weekday vs weekend: no difference.** A commitment-driven night error (units held on overnight for the next
  day's peak) would differ between the two, and it does not.
- **Coal short vs coal long: the same gap.** In 2019–21 and 2023–24 the model's night coal is 0.4–1.0 GW below
  EIA-930. In 2022 and 2025 it is 0.5 GW above. The λ ÷ offer ratio (§2) is 0.75–0.83 in both groups. So adding
  night coal (the adjudicated coal-floor family) would not remove it.
- **Summer is smaller.** JJA nights have the highest load, so more CC is loaded and the CC setter sits higher in
  its range. That is consistent with a proportional offer-level gap, not a new mechanism.

## 4. Hydro + pumped storage: real miss, bounded effect

Discharge side (conventional hydro + PS discharge), mean MW. EIA-930 `NG: WAT` folds PS discharge before
2024-07-15; after the split, PS discharge is added back.

| year | low-40 %: model / EIA-930 | top-20 %: model / EIA-930 |
|---|---:|---:|
| 2019 | 545 / 1,053 | 2,659 / 1,637 |
| 2020 | 614 / 1,148 | 2,576 / 1,556 |
| 2021 | 858 / 1,107 | 2,266 / 1,560 |
| 2022 | 709 / 1,274 | 2,410 / 1,201 |
| 2023 | 450 / 728 | 2,024 / 1,373 |
| 2024 | 523 / 660 | 1,983 / 1,130 |
| 2025 | 321 / 595 | 2,141 / 1,419 |

The model concentrates hydro into the highest-price hours far more than the measured dispatch does, even with
`hydro_ror_split` live (K, keeper hydro minimum 81–304 MW, no zero-MW hours). This is the gap soco-hydro-4
recorded: top-decile share 0.25–0.29 vs measured 0.14–0.18.

**Bound (`--hydro-shape-arm`).** Each day's model discharge MWh is redistributed onto that day's measured
EIA-930 shape. Where EIA-930 reports PS (2025, and 2024 after 07-15), pumping is reshaped too. The thermal
residual is then re-stacked greedily (the soco-90 instrument) and re-scored through `calibration_verdict`.

| year | ΔMW low-40 / top-20 | Δprice low-40 / top-20 | C3a | low-40 % | top-20 % | C3b |
|---|---|---|---|---|---|---|
| 2019 | +132 / −182 | −0.71 / +0.19 | +14.0 → +13.1 FAIL | 2.60 → 2.37 | −0.32 → −0.28 | 0.166 → 0.156 |
| 2020 | +210 / −179 | −0.71 / +0.26 | +14.4 → +13.3 FAIL | 1.95 → 1.71 | −0.28 → −0.23 | 0.177 → 0.162 |
| 2021 | +141 / −250 | −0.85 / −0.19 | −2.4 → −3.2 PASS | 1.90 → 1.61 | −2.93 → −2.93 | 0.119 → 0.118 |
| 2022 | +71 / −132 | −0.02 / −0.34 | −12.7 → −13.0 FAIL | 3.21 → 3.20 | −11.71 → −11.79 | 0.275 → 0.277 FAIL |
| 2023 | +150 / −199 | −0.46 / +0.14 | +2.3 → +1.6 PASS | 1.88 → 1.72 | −2.03 → −1.99 | 0.094 → 0.089 |
| 2024 | +137 / −212 | −0.35 / +0.01 | −3.6 → −4.2 PASS | 2.03 → 1.92 | −3.60 → −3.59 | 0.180 → 0.180 |
| 2025 | +161 / −243 | −0.36 / +0.15 | −1.5 → −1.9 PASS | 2.70 → 2.56 | −4.54 → −4.50 | 0.189 → 0.192 |

No C1 status moves (2019 COAL_BIT stays the ledgered caveat). With perfect hindsight, the most a hydro-shape
mechanism can reach on C3a is ~1 pp. The peak side moves ~0 because the CT stack is flat: 200 MW less hydro
moves the setter along a run of similar CT offers.

Hydro shape is still a real structural miss, and rule 1 says to fix structure on its own merits. The existing route
is `hydro_min_flow_floor` (O), "re-open only as the rule-19 RECONCILED floor on the reservoir class under the ror
keeper". PS cycling depth (U) is the other half: in 2025, the one year with clean PS data, the model pumps 599 MW
in low-40 % hours vs 438 measured and discharges 725 MW in top-20 % hours vs 502.

## 5. Checks named in the handoff

| candidate | finding | status |
|---|---|---|
| night setter's band | CC_REGULAR plant at flat average HR (band is an LP tie) | offer level, §2 |
| min-gen / commitment floors raising night price (rule 17 windows) | impossible in an LP; D-2 floors and 256–382 MW out-of-merit set no night price | not a cause |
| offer-curve band multipliers (rule 1 channel) | G5 identity; no ex-ante source for a cost-based pool; the needed shape is the residual | not admissible |
| hydro / storage shifting | real, 140–570 MW short at night, 650–1,200 MW long at peak; bound ≤ 1.1 pp C3a | structure only, §4 |
| interchange at night | measured schedule, on-clock, demand closes to the MW | not a lever |
| weekday / weekend | no difference | no commitment signature |

## 6. Records

- Probe: `scripts/probes/_soco91_intraday_census.py` (`--out DIR`; `--hydro-shape-arm` for §4). Scratch outputs
  (`census91_<y>.json`, `fleet91_<y>.npz`, `soco91_hydro_shape_arm.csv`) are not committed.
- Matrix: notes only, no verdict moves. `hydro_min_flow_floor` stays O and `pumped_storage_cycling_depth` stays U,
  each with the §4 bound cited. No ScenarioConfig field was added or tested.
- Retrievability: no bundle was produced. Keeper unchanged; SOCO is not frontier.
