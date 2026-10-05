# FINDING — closeout-MISO-w3e: two cancelling errors in MISO's CHP bench basis (rule-14 record)

```
LANE    : closeout-MISO-w3 (desk follow-up 2026-10-05: "do the 923/930/Sched 6/7 reconciliation for the top 5 cogens first")
LP      : none
PROBE   : scripts/probes/_closeout_miso_w3e_bench_reconciliation.py -> results/phase0/miso/_closeout_miso_w3e_bench_reconciliation.json
CHANNEL : render_calibration_html.reconcile_vintage_classes, via benchmark_semantics.gas_foldin_deflation
RULING  : desk call (a)-held: one draft PR, NOT merged; owner decision #20
```

## The two errors

MISO's benchmark carries two errors of about the same size and opposite sign, and they cancel.

1. **The sector-default CHP share overstates host self-use.** The default `chp_btm_pct` (`CHP_BTM_PCT_BY_SECTOR`) treats about 11 TWh/yr of merchant and tolled cogen output as behind the meter. The plants' own EIA-923 Schedules 6/7 filings say that energy is sold to the grid (w3d census; §1 below).
2. **The fold-in deflation subtracts energy that is not there.** `gas_foldin_deflation` cuts the EIA-930 reconcile target by F = OTHER + biomass − 930 Other, which is 11.0–14.1 TWh/yr for MISO. That assumes MISO's 930 NG cell folds in that biomass/OTHER. It does not (§2). The excess is chp=Y host biomass/OTHER that the BA never meters; w3c measured 930 OTH at 4.5 TWh against about 19 TWh injected.

**How they cancel.** Under the default share, 923 grid fossil runs about 3 % below raw 930 gas+coal, and the deflated target sits about 3 % below raw 930 as well, so the reconcile looks satisfied. Fixing (1) alone pushes 923 grid fossil above the deflated target. The combined reconcile then scales every fossil class down by ×0.95–0.97 in 2019–2022, and COAL_PRB actuals fall 4–8 TWh. Fixing both puts the measured 923 total within the deadband of raw 930 in every year, and the reconcile never fires.

## 1. Plant level: the five largest movers

All five plants are in MISO BA (EIA-860) and are interconnected to MISO transmission owners, so their Schedules 6/7 "sales for resale" are MISO-grid energy.

**2019, GWh:**

| plant | TO | EIA-923 net | Sched 6/7 net | Sched 6/7 grid | CAMPD net | grid under the default share |
|---|---|---:|---:|---:|---:|---:|
| Midland Cogen 10745 | METC | 8,853 | 9,127 | 8,602 | 7,380 | 5,754 (35 %) |
| Taft 55089 | Entergy LA | 5,774 | 5,772 | 4,361 | 3,868 | 1,732 (70 %) |
| Sabine River Works 10789 | Entergy TX | 3,184 | 3,111 | 2,412 | — (no CEMS) | 955 (70 %) |
| Dearborn Industrial 55088 | DTE | 5,483 | 5,355 | 5,355 | 3,689 | 3,564 (35 %) |
| Carville 55404 | Entergy LA | 2,970 | 3,024 | 2,971 | 3,233 | 1,931 (35 %) |

The same pattern holds in 2021 and 2023 (see the JSON).

**Meter agreement.** EIA-923 page-1 net matches the Schedules 6/7 net within about 3 %. At the four plants with CEMS, CAMPD's CEMS-metered output on its own exceeds the grid energy the default share allows. CEMS often covers only the combustion turbines of a combined cycle, which is why CAMPD reads below EIA-923.

**Conclusion.** The default is refuted by two independent meters, and the plant boundary maps onto our representation without misalignment.

## 2. SOCO-60's fold test for MISO

This is the test that admitted SOCO and CAISO to `EIA930_GAS_FOLD_REFUTED`: EIA-930 gas against the EIA-923 gas generation of MISO-BA plants counted in FULL (CHP host included).

| year | 930 gas | 923 gas FULL | 930 − 923 | fold F the deflation subtracts |
|---|---:|---:|---:|---:|
| 2019 | 191.0 | 219.1 | −28.1 | 14.1 |
| 2020 | 197.4 | 220.2 | −22.8 | 13.1 |
| 2021 | 181.0 | 205.4 | −24.4 | 12.6 |
| 2022 | 208.4 | 233.3 | −24.9 | 13.0 |
| 2023 | 241.2 | 258.4 | −17.2 | 13.1 |
| 2024 | 252.1 | 265.5 | −13.4 | 11.8 |
| 2025 | 233.2 | 249.0 | −15.8 | 11.0 |

930 gas is below 923 gas in every year, so there is no room for a fold. The negative gap is host gas output the BA does not meter. That is the BTM quantity, and it is of the same order as the measured Schedules 6/7 BTM, 22–26 TWh.

## 3. System level: fossil family total by basis (TWh) against raw EIA-930 gas+coal

| year | 930 gas+coal | default (committed) | measured shares | reconciled (measured + MISO fold refuted) |
|---|---:|---:|---:|---:|
| 2019 | 429.9 | 415.8 (scaled) | 415.8 (scaled ×0.938) | 443.2 (+3.1 %, at the deadband edge, not scaled) |
| 2020 | 389.0 | 382.9 | 376.0 (scaled) | 394.1 (+1.3 %) |
| 2021 | 420.1 | 418.6 | 407.5 (scaled) | 428.7 (+2.0 %) |
| 2022 | 425.5 | 415.7 | 412.5 (scaled) | 426.7 (+0.3 %) |
| 2023 | 416.2 | 402.9 (−3.2 %) | 414.5 | 414.5 (−0.4 %) |
| 2024 | 419.2 | 404.6 (−3.5 %) | 416.2 | 416.2 (−0.7 %) |
| 2025 | 425.3 | 414.4 (scaled) | 425.4 | 425.4 (0.0 %) |

## 4. Effect on the incumbent keeper (2026-10-03-closeout-miso-nuc-r), C1 fuelmix

Zero LP. Scored locally from re-rendered bench parts; nothing was committed.

**Measured shares only (the artifact lands without the fold fix):** 10 PASS→FAIL, 1 FAIL→PASS.

| record | original | measured | change |
|---|---:|---:|---|
| CC_CHP 2019 | −5.25 | −15.88 | PASS→FAIL |
| CC_CHP 2020 | −4.49 | −14.06 | PASS→FAIL |
| CC_CHP 2021 | −5.04 | −13.89 | PASS→FAIL |
| CC_CHP 2022 | −5.83 | −15.75 | PASS→FAIL |
| CC_CHP 2023 | −3.24 | −14.65 | PASS→FAIL |
| CC_CHP 2024 | −1.40 | −12.66 | PASS→FAIL |
| COAL_PRB 2019 | +4.56 | +8.87 | PASS→FAIL, through `reconcile_vintage_classes` |
| COAL_PRB 2020 | +3.87 | +9.70 | PASS→FAIL, through `reconcile_vintage_classes` |
| COAL_PRB 2021 | +5.03 | +13.12 | PASS→FAIL, through `reconcile_vintage_classes` |
| COAL_PRB 2022 | +5.72 | +10.73 | PASS→FAIL, through `reconcile_vintage_classes` |
| CC_REGULAR 2021 | −8.15 | −2.99 | FAIL→PASS |

**Reconciled basis (artifact + MISO fold refuted, this PR):** only the CHP rows move. 6 PASS→FAIL, nothing else flips.

| record | original | reconciled |
|---|---:|---:|
| CC_CHP 2019 | −5.25 | −17.90 |
| CC_CHP 2020 | −4.49 | −15.51 |
| CC_CHP 2021 | −5.04 | −15.28 |
| CC_CHP 2022 | −5.83 | −16.75 |
| CC_CHP 2023 | −3.24 | −14.65 |
| CC_CHP 2024 | −1.40 | −12.66 |

ST_GAS 2019 and CC_REGULAR 2021 keep their prior status. The seam-full-span control gives the same picture; for example, COAL_PRB 2019 goes from +6.01 to +0.42.

**Reading.** On a consistent bench, MISO's only remaining residual from this object is that the model's grid CHP tranche is short by about 11 TWh. The `miso_chp_btm_measured` arm addresses exactly that.

## Rule-14 disposition

- The real data (Schedules 6/7) is kept.
- The misalignment was in a benchmark-side hypothesis, the MISO gas fold, which is refuted on the same test that refuted it for SOCO-60 and CAISO R-33.
- The fix is a registry entry, `EIA930_GAS_FOLD_REFUTED += {"MISO"}`. There is no `iso==` branch.
- Other ISOs are unchanged: ERCOT, PJM, NYISO, NEISO, SPP and NWPP keep their deflation, and SOCO and CAISO were already refuted.
- `benchmark_semantics.py` is outside `bench_stamp.PAYLOAD_SOURCES`, so no part re-stamp is needed.
- The keeper's committed bench parts are not rebuilt by this PR. Per the desk's ruling, that happens only at a promotion.
