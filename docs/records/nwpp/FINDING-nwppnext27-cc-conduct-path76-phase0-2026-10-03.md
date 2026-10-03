# FINDING — NWPP-NEXT-27 phase 0: the CC over-run is conduct and a priced bilateral path, not heat rate

Keeper `2026-10-03-nwpp-next-26-nevp` (bundle `results/calibration/nwppnext26_span`, legs at `30c0e017`). Zero LP
throughout. Probe: `scripts/probes/_nwppnext27_cc_plant_decomp.py` (writes
`results/phase0/nwpp/_nwppnext27_cc_plant_decomp.json`); the rest is reproduced inline below from committed data.

## A. Where the 2024 excess sits, plant by plant (model P1 vs CAMPD hourly)

Split of model-minus-CAMPD energy into hours CAMPD is off / both on / model off (TWh):

| plant | zone | model | CAMPD | commitment | **loading** | short |
|---|---|---:|---:|---:|---:|---:|
| Lake Side 56237 | EAST | 7.95 | 6.29 | 0.01 | **2.08** | −0.43 |
| Chuck Lenzie 55322 | SNV | 6.75 | 5.71 | 0.34 | **1.29** | −0.59 |
| Currant Creek 56102 | EAST | 3.88 | 2.93 | 0.04 | **1.19** | −0.28 |
| Higgins 55687 | SNV | 3.94 | 2.97 | 0.20 | **1.02** | −0.24 |
| Apex 55514 | SNV | 3.11 | 2.04 | 0.22 | **0.94** | −0.09 |
| Grays Harbor | NW | 3.72 | 2.87 | 0.30 | 0.61 | −0.05 |

- The excess is **loading**, not commitment. The long CCs are online in about the same hours as CAMPD, but the model
  runs them at 0.93–0.98 of available capacity, while CAMPD shows 0.60–0.75. 2019 and 2025 show the same pattern.
- **Capability is not overstated**, except at Lake Side. Monthly CAMPD p99 reaches or exceeds the model cap at
  Chuck Lenzie, Higgins, Harry Allen and Silverhawk. At Lake Side, p99 sits about 150 MW under the cap in every month.

## B. Part-load / incremental heat rate: ruled out

CAMPD 2024 hourly heat input against gross load gives these linear input-output fits:

| plant | no-load MMBtu/h | IHR | average HR |
|---|---:|---:|---:|
| Lake Side | 235 | 6.76 | 7.09 |
| Chuck Lenzie | 229 | 6.93 | 7.24 |
| Currant Creek | 124 | 6.81 | 7.17 |
| Higgins | 131 | 6.84 | 7.19 |
| Harry Allen | 210 | 6.77 | 7.28 |

- The decile IHR is flat at 6.4–7.4 up to the top decile. The top-decile duct segment is dear only at Harry Allen and
  Silverhawk (IHR 11–12), and those plants run few hours there.
- An incremental curve would make the econ bands **cheaper** than the average-rate offer, so it cannot cut loading.
- The keeper's econlo, econhi and peak bands share one cost. The cause is that the bands are neutral (rule 25,
  `backcast_config._neutralize_generic_gas_bands`), not a missing heat-rate curve. No NWPP CC marginal-HR summary exists.

## C. Conduct: measured CCs follow their BA's net load and ignore the WEIM price

- Measured 2024 NEVP gas (EIA-930 NG:NG) against NEVP net load gives **r 0.89**. Against the NEVP WEIM LMP it gives
  **r −0.00**, and the lag sweep from −2 to +2 h never exceeds 0.07. PACE gives 0.65 and 0.09.
- Plant level (LMP minus model mc, in buckets):
  - CAMPD loading over the model cap stays flat at 0.58–0.84 whether the plant is $10 out of the money or $40 in it.
  - The model's loading jumps from 0.2–0.6 to 0.95–0.99 at the cost threshold.
  - At the six long plants, corr(CAMPD MW, LMP) runs from −0.06 to 0.09.
- **Model.** SNV gas 28.1 TWh against NEVP 21.7; EAST 14.7 against PACE 11.7. Hourly r against own demand is 0.43 /
  0.47.
- **Reading.** NEVP and PACE balance native load with their own CCs on bilateral base schedules, and the WEIM trades
  only imbalance. The LP is a pool-wide price-taker that loads every in-the-money CC to its cap and exports the
  surplus. Routed to NEXT-28 as a BA-conduct design question (reserve holding under BAL-002-WECC, WEIM resource
  sufficiency). There is no NWPP reserve design (`iso_configs._nwpp_config` docstring).

## D. Where the SNV surplus leaves: the internal Path 76 / Path 16 ties (2024 keeper leg)

| link (model) | model TWh | hours at limit | measured EIA-930 leg |
|---|---:|---:|---|
| SNV→NW (Path 76, 300 MW) | 2.37 S→N, net 2.20 | 7,745 | NEVP→BPAT **−0.18** net, −211…+160 MW |
| SNV→INLAND (Path 16, 360 MW) | 2.19 | 5,772 | NEVP→IPCO **−0.11** net, −364…+361 MW |
| EAST→INLAND (Path C, 1,250 MW) | 8.49 | 5,288 | PACE→IPCO 6.47, max 2,185 |

- **Measured WEIM transfers** (benefits reports, Appendix 2, `data/raw/nwpp-weim/weim_benefits_appendix2_transfers.csv`):
  - NEVP↔BPAT is **0.00 TWh in both directions in every month, 2023-07 to 2025-12**. BPAT entered the WEIM only
    2022-05.
  - NEVP→IPCO is 0.53 / 0.66 / 0.58 TWh, and IPCO→NEVP 0.08 / 0.28 / 0.51.
  - So Path 16 carries economic WEIM transfers, and Path 76 carries none.
- **Measured price response** (EIA-930 leg against the WEIM spread):
  - NEVP→BPAT does not respond, r 0.09. The mean flow stays −55 to +14 MW across the spread buckets, even when BPAT is
    $40 above NEVP.
  - NEVP→IPCO responds weakly, r 0.22.
- **Model, every year, SNV→NW net TWh:** 1.69 / −0.23 / 0.16 / −0.59 / 2.13 / 2.20 / 1.59. The measured NEVP→BPAT is
  −0.51 / −0.54 / −0.25 / −0.61 / −0.25 / −0.18 / −0.19.

## E. The lever: `nwpp_path76_served_schedule` (owner card 2026-10-03, "Path 76 served")

- **Construction.**
  - Path 76 is priced in no hour, and `nwpp_path76_alturas_link` is disarmed.
  - The measured NEVP→BPAT leg is served at SNV (+) and NW (−) through the zonal served schedule
    (`envelopes.nwpp_path76_served_zone_legs`).
  - Columns conserve, so the footprint total and the remainder are unchanged.
- **Rules.**
  - Rule 19: the leg is priced or served, never both. Arming both raises in `pipeline/ttc.apply_nwpp_path76_link`.
  - Rules 13 and 14: this is a measured interchange schedule built on the keeper's served-schedule construction. No
    number is added.
  - Forward story: a forecast year has no served schedule, and the runner refuses the key.
- **Zero-LP construction, P1 zonal demand.**

  | year | leg TWh | NW | SNV |
  |---|---:|---:|---:|
  | 2019 | −0.510 | 118.09 | 30.65 |
  | 2020 | −0.541 | 119.07 | 28.99 |
  | 2021 | −0.251 | 112.93 | 24.67 |
  | 2022 | −0.610 | 119.02 | 24.92 |
  | 2023 | −0.249 | 108.69 | 24.27 |
  | 2024 | −0.177 | 110.11 | 26.27 |
  | 2025 | −0.189 | 114.43 | 28.11 |

  OR, INLAND and EAST are unchanged from the keeper, and so are the footprint totals.
- **Expected SNV local-need change.** This is the measured leg minus the keeper's priced net flow, in TWh:

  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---:|---:|---:|---:|---:|---:|---:|
  | −2.20 | −0.31 | −0.41 | −0.02 | −2.38 | −2.38 | −1.78 |

## F. Not adopted here

- **Path 16.** It is left priced, because it carries measured economic WEIM transfers. Its transfer capability is not
  published.
- **Path C.** It is left as is. The measured PACE→IPCO maximum of 2,185 MW exceeds the 1,250 MW rating, and part of
  Path C is PACE-internal (Tier 2).
- **The Lake Side capability gap (~150 MW)** is noted. `cc_capacity_reconcile` is not armed for NWPP.
