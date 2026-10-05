# FINDING — closeout-MISO-w3d: measured EIA-923 Sched 6/7 self-use is far below MISO's `chp_btm_pct` sector defaults (+8 to +13 TWh/yr more grid CHP), but the first-order reach trades C3a 2020 for ST_GAS 2020 and CC_REGULAR 2021

```
LANE    : closeout-MISO-w3 (desk follow-up 2026-10-05, after CAISO-w6's Sched 6/7 finding: "census the same zero-LP comparison for MISO")
LP      : none
CONTROL : seam-full-span probe 2026-10-04-closeout-miso-w3-seam (legs closeout_miso_w3_<y>, committed unit_marginal sidecars)
PROBE   : scripts/probes/_closeout_miso_w3d_chp_selfuse_census.py -> results/phase0/miso/_closeout_miso_w3d_chp_selfuse_census.json
SOURCE  : EIA-923 f923_<y>.zip (archive), Schedules 6/7 "Source and Disposition, Non-Utility Generators"
          zip SHA-256 prefixes 2019 c2fd692e, 2020 b8c6516c, 2021 9db69876, 2022 2f030b7d, 2023 f96326c0, 2024 272055f2
          (2019 and 2024 match CAISO-w6's); xlsx hashes are in the JSON
```

## 1. Census

The definition is the same as CAISO-w6's:

- own = (gross − station) − resale − retail − tolling − outgoing
- share = own / (gross − station)

That share is compared with `chp_btm_pct(pid, group, iso="MISO")`, which is the share that both the LP carve (`chp_steam_following` → grid cap = nameplate × (1 − share)) and the bench `_btm_frame` subtrahend use.

**Coverage.** Sched 6/7 covers 106 of the ~123 MISO CHP plants and 96 % of their EIA-923 net generation. The plants it misses are utility-owned and keep the default.

| year | CHP netgen (TWh) | BTM under defaults | BTM under measured | dE grid (TWh) | of which CC_CHP |
|---|---:|---:|---:|---:|---:|
| 2019 | 65.5 | 36.3 | 25.5 | **+10.80** | +11.03 |
| 2020 | 60.9 | 33.0 | 22.9 | **+10.12** | +10.56 |
| 2021 | 57.8 | 32.4 | 24.4 | +7.99 | +9.16 |
| 2022 | 61.9 | 35.1 | 24.9 | +10.15 | +10.61 |
| 2023 | 66.8 | 36.9 | 24.0 | +12.92 | +12.68 |
| 2024 | 66.0 | 36.5 | 24.5 | +12.04 | +11.98 |

**Where the gap comes from.** It is concentrated in large merchant or tolling cogens:

| plant | group | default share | measured share | note |
|---|---|---:|---:|---|
| Midland Cogen 10745 | CC_CHP | 0.35 | 0.013 | sells 8.6 of 9.1 TWh for resale |
| Taft 55089 | CC_CHP | 0.70 | 0.245 | |
| Sabine River Works 10789 | CC_CHP | 0.70 | 0.117 | |
| Dearborn 55088 | CT_CHP | 0.35 | 0.000 | |
| Carville 55404 | CC_CHP | 0.35 | 0.018 | |

ST_CHP goes the other way (−0.3 to −0.5 TWh), because its measured self-use is above the default.

**This is new evidence for the `chp_btm_measured` cell R (miso-192).** miso-192 refuted that cell because the CAMPD steam-load construction covered only 5.8 % of MISO CHP MW. Sched 6/7 is a per-plant disposition meter, separate from the page-1 net generation, and it covers 96 % of CHP energy. It also regenerates for a forward year (EIA publishes it each year), so it is rule-13 admissible.

## 2. First-order grid reach (static, on the control legs)

**Method.**
- **Model side.** Each covered plant's solved grid tranche is scaled by (default − measured)/(1 − default). The added MW is dispatched at the plant's own solved hourly utilisation. That is the lower bound. The upper bound assumes the added MW delivers the full census dE, i.e. scales the lower bound by k = dE / model-add = 1.14–1.72.
- **Displacement.** The hourly added energy is walked down the solved stack. Only units offered at or below the hour's marginal offer are displaced; floor-held units above it are not. Imports are included; nuclear, hydro and CHP are excluded.
- **Bench side.** The bench's CHP classes rise by dE, because the subtrahend uses the same share. Every other bench class is unchanged.

**C1 records, control → lower / upper bound (TWh; band ±8.00):**

| year | CC_REGULAR | ST_GAS | COAL_PRB | COAL_BIT | CC_CHP (model add − bench dE) |
|---|---|---|---|---|---|
| **2019** | +0.67 → −0.68 / −1.57 | **−8.42 → −9.63 / −10.42 (FAIL deepens)** | +6.01 → +4.58 / +3.63 | −1.47 → −2.19 / −2.66 | −5.19 → **−9.17 FAIL** / −5.19 |
| **2020** | −3.10 → −4.67 / −5.21 | −6.79 → **−8.48 / −9.06 (new FAIL)** | +4.70 → +3.51 / +3.10 | −4.14 → −4.60 / −4.76 | −4.59 → −6.75 / −4.59 |
| 2021 | −6.41 → **−8.20 / −9.49 (FAIL again)** | −5.00 → −5.55 / −5.94 | +4.99 → +4.35 / +3.90 | −0.68 → −0.96 / −1.16 | −4.48 → −7.59 / −4.48 |
| 2022 | −2.70 → −5.03 / −6.34 | −5.19 → −6.07 / −6.57 | +5.43 → +4.68 / +4.26 | +5.12 → +4.76 / +4.55 | −5.05 → −7.68 / −5.05 |
| 2023 | −0.87 → −3.16 / −3.77 | −1.48 → −3.06 / −3.47 | −0.10 → −1.72 / −2.15 | +1.17 → +0.86 / +0.78 | −3.24 → −4.41 / −3.24 |
| 2024 | +2.61 → +0.86 / +0.61 | −2.43 → −4.46 / −4.75 | −0.56 → −2.10 / −2.33 | −0.74 → −1.13 / −1.18 | −1.40 → −1.14 / −1.40 |

**C3a.** The static marginal-offer moves are −0.77 (2019), −0.74 (2020), −0.80 (2021) and −2.16 (2022) $/MWh at the lower bound. Reading them at the w3 seam arm's 0.53 static→LP ratio:

| year | C3a, control | C3a, lower → upper bound | note |
|---|---:|---:|---|
| 2020 | +10.3 % | **≈ +8.5 → +7.9 % (FAIL → PASS)** | |
| 2019 | +6.4 % | ≈ +4.8 → +3.7 % | |
| 2021 | −4.9 % | ≈ −6.0 → −6.8 % | |
| 2022 | −3.7 % | ≈ −5.5 → −6.6 % | the 2021/22 moves shrink the w3 seam gain |

## 3. Reading

**Structure.** The defaults overstate host self-use by about 10 TWh/yr. This is a rule-14 input error in the same family as CAISO-w6's.

**Where the energy lands.** The extra CHP energy lands in the classes that are already short: ST_GAS in 2019/2020 and CC_REGULAR in 2021. It does not land on COAL_PRB, the class that is over.

**Gates, at first order.** The swap trades:
- **gained:** C3a 2020 FAIL → PASS;
- **lost:** C1 ST_GAS 2020 PASS → FAIL, C1 CC_REGULAR 2021 PASS → FAIL, and at the lower bound C1 CC_CHP 2019 PASS → FAIL;
- **deepened:** C1 ST_GAS 2019, which goes further below band.

Static gates are not a rule-14 verdict. A worse fit after real data is a bug found elsewhere. The likely candidate is the ST_GAS under-dispatch (MISO-F1 VLR), which this swap would expose further.

**It is the opposite direction to the w3c holdout.** The w3c holdout (`mustrun_chp_btm_holdout`) removes chp=Y biomass/OTHER must-run, about 10–15 TWh of injected must-run. This swap adds about 10 TWh of gas-CHP grid energy. The two are separate rows on separate classes and do not net out.

**Not built or solved here.** A MISO field would mirror NYISO's `nyiso_chp_btm_measured` (per-plant measured share, consumed in both the carve and the bench). It would need a frozen derive from Sched 6/7, a PRECOMMIT, and seven legs. Those are for a successor lane on the desk's or owner's call.
