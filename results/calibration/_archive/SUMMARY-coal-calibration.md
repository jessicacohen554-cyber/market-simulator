# ERCOT coal calibration — config comparison

Locked baseline knobs across all configs below: historic outage overlay, per-plant CAMPD coal must-run floors, plant-specific monthly coal prices, gas-keyed PRB passthrough sigmoid. Configs differ only in coal POF (statistical planned-outage derate) and the sigmoid floor / tiering.

## PRB level — Δ% vs EIA-923

| config | 2023 | 2024 | 2025 | max abs |
|---|--:|--:|--:|--:|
| POF-on floor0.68 (ppmr_sig3) | +4.6% | -3.7% | +2.8% | 4.6% |
| POF-off floor0.68 (nopof) | +9.5% | +0.8% | +8.4% | 9.5% |
| POF-off floor0.80 (nopof_f80) | -9.9% | -21.6% | +2.7% | 21.6% |
| POF-off tiered foll0.58 (tier) | +17.4% | +10.5% | +11.4% | 17.4% |
| POF-off tiered foll0.66 (tier66) | +7.2% | -1.5% | +8.3% | 8.3% |

## Lignite level — Δ% vs EIA-923

| config | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| POF-on floor0.68 (ppmr_sig3) | +2.7% | -3.4% | +23.9% |
| POF-off floor0.68 (nopof) | +8.7% | +1.9% | +32.3% |
| POF-off floor0.80 (nopof_f80) | +10.2% | +5.8% | +32.3% |
| POF-off tiered foll0.58 (tier) | +7.2% | -2.1% | +32.3% |
| POF-off tiered foll0.66 (tier66) | +8.7% | +3.0% | +32.3% |

## Coal hourly fit vs EIA-930 (Pearson r / NRMSE)

| config | 2023 | 2024 | 2025 |
|---|---|---|---|
| POF-on floor0.68 (ppmr_sig3) | 62.92 / 15.1 | 55.52 / 12.8 | 67.03 / 14.6 |
| POF-off floor0.68 (nopof) | 66.04 / 15.8 | 58.21 / 13.5 | 70.93 / 15.4 |
| POF-off floor0.80 (nopof_f80) | 57.50 / 13.8 | 48.98 / 11.3 | 68.20 / 14.8 |
| POF-off tiered foll0.58 (tier) | 69.35 / 16.6 | 61.90 / 14.3 | 72.34 / 15.7 |
| POF-off tiered foll0.66 (tier66) | 64.99 / 15.6 | 57.39 / 13.3 | 70.86 / 15.4 |

## Per-plant hourly r vs CAMPD — does tiering help the load-followers?

global floor 0.80 -> tiered (follower 0.66). * = follower tier (MR<=25%).


**2023**

| plant | MR% | global0.80 | tiered0.66 |
|---|--:|--:|--:|
| *Limestone | 20 | 0.755 | 0.752 |
| *Martin Lake | 20 | 0.674 | 0.665 |
| Coleto | 30 | 0.731 | 0.702 |
| Fayette | 30 | 0.644 | 0.637 |
| *J K Spruce | 12 | 0.545 | 0.527 |
| Sandy Creek | 40 | 0.433 | 0.443 |
| *W A Parish | 15 | 0.676 | 0.699 |

**2024**

| plant | MR% | global0.80 | tiered0.66 |
|---|--:|--:|--:|
| *Limestone | 20 | 0.730 | 0.753 |
| *Martin Lake | 20 | 0.535 | 0.466 |
| Coleto | 30 | 0.611 | 0.581 |
| Fayette | 30 | 0.601 | 0.565 |
| *J K Spruce | 12 | 0.433 | 0.484 |
| Sandy Creek | 40 | 0.463 | 0.472 |
| *W A Parish | 15 | 0.589 | 0.703 |

## Bundle locations (parquet)

Each config has 2023/2024/2025 single-year bundles under `results/calibration/<config>_<year>/` (dispatch parquet now carries per-unit `lmp`). Reprint any bundle's full [1]-[7] tables with `python scripts/run_calibration_full.py --report <dir>`.


---

# Full [1]-[7] report tables

Below: POF-on floor-0.68 then POF-off tiered-0.66, each across 2023-2025.


```

================================================================================
  CALIBRATION REPORT  (ERCOT; run 2026-05-20T22:34:45; git 0173d38)
  bundle: results/calibration/ppmr_sig3_2023
================================================================================

================================================================================
  ERCOT 2023 BACKCAST
================================================================================

  [1] CHP — 2023  (model grid LP + behind-meter must-run vs EIA-923 total)
     class  grid LP  BTM-MR  model tot  EIA-923  diff %
    CC_CHP    25.40   31.84      57.24    53.00    +8.0
    CT_CHP     3.33    9.58      12.91    13.04    -1.0
    ST_CHP     0.81    0.20       1.01     0.52   +92.9
     TOTAL    29.54   41.63      71.17    66.57    +6.9
    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded from every table below.)

  [2] Grid generation reconciliation — 2023
    EIA-930 net generation (Demand + Interchange)          445.97 TWh
    Model demand target                                    445.97 TWh
    Model grid generation (LP)                             446.20 TWh
    Gap (model grid − EIA-930 net gen)                      +0.23 TWh
    Unserved energy / load slack (should be 0)             0.0000 TWh
    Behind-meter CHP must-run (off-grid; table [1] only)    41.63 TWh

  [3] Non-CHP grid generation — 2023  (model LP vs EIA-930, CHP excluded)
             fuel  model TWh  model %  EIA-930 TWh  EIA-930 %     Δpp
    gas (non-CHP)     180.34     43.3       171.92       41.4    +1.9
             coal      62.92     15.1        62.29       15.0    +0.1
          nuclear      38.07      9.1        40.91        9.9    -0.7
             wind     102.38     24.6       107.99       26.0    -1.5
            solar      32.95      7.9        31.87        7.7    +0.2
            TOTAL     416.66    100.0       414.98      100.0        
    (EIA-930 non-CHP gas = EIA-930 all-gas − 29.5 TWh model CHP grid-delivered.)

  [3b] Thermal by class — 2023  (model grid LP + behind-meter must-run vs EIA-923 total; coal split lignite/PRB)
           class  grid LP  BTM-MR  model tot  EIA-923  diff %
          CC_CHP    25.40   31.84      57.24    53.00    +8.0
      CC_REGULAR   163.28    0.00     163.28   143.70   +13.6
          CT_CHP     3.33    9.58      12.91    13.04    -1.0
       CT_PEAKER     9.71    0.00       9.71     7.47   +30.0
          ST_GAS     7.35    0.00       7.35    16.83   -56.3
          ST_CHP     0.81    0.20       1.01     0.52   +92.9
    COAL_LIGNITE    15.74    0.00      15.74    15.33    +2.7
        COAL_PRB    47.17    0.00      47.17    45.09    +4.6
           TOTAL   272.80   41.63     314.43   294.98    +6.6

  [4] Monthly bias — 2023   (% of EIA-923 per month; coal split; CHP incl. behind-meter)
           class     Jan    Feb    Mar    Apr    May     Jun     Jul     Aug     Sep    Oct    Nov    Dec
          CC_CHP    +4.5   +3.0   +1.1   +9.4  +13.1   +11.8   +13.7   +12.5   +10.2  +12.5   +4.7   -1.9
      CC_REGULAR    +9.3   +8.3  +24.4  +28.4  +14.2   +13.1    +6.9    +4.6    +9.4  +18.1  +31.8  +14.3
          CT_CHP    -0.9   -3.1   -3.1   -1.4   -2.5    -1.2    +0.4    +1.5    +1.0   +0.7   -3.3   -0.8
       CT_PEAKER   -15.7   +5.1  -66.8  -58.3  +31.2   +36.2   +80.4   +56.1   +85.1  +54.7  -28.9  -19.7
          ST_GAS   -20.1  -40.2  -99.7  -98.2  -71.0   -57.8   -48.3   -39.2   -46.2  -72.4  -92.1  -67.8
          ST_CHP  +112.0  +97.6  +47.7  +59.2  +86.8  +119.8  +136.1  +129.3  +138.9  +76.2  +65.4  +70.3
    COAL_LIGNITE    -5.6  -16.9  +33.8  -25.2  -15.7   +11.4   +13.2   +24.2   +24.9   -3.3   -2.5   +6.4
        COAL_PRB   +56.8  +15.7  -17.9  -15.6   -2.7    +6.1   +14.4   +24.8    +8.4  -14.2  -12.6   -2.9
            wind    -4.1   -2.5   -2.1   -5.5   -7.7    -7.8    -7.7    -7.2    -8.5   -5.8   -4.9   -4.9
     solar (930)   +11.1  +25.2  +16.4   +9.5   -0.6    +0.3    -1.2    -2.4    -1.9   +2.1   +1.3   +4.7
         nuclear    -7.9   -6.2   -2.8   +0.7   +3.9    -5.4    -6.7    -5.7    -7.2  -20.0  -11.4   -6.0

  [5] Hourly dispatch fit — 2023 (model vs EIA-930, non-CHP gas)
             fuel  Pearson r   NRMSE  model TWh  EIA-930 TWh
    gas (non-CHP)      0.983   0.122     180.34       171.92
             coal      0.861   0.216      62.92        62.29
          nuclear      0.665   0.112      38.07        40.91
            solar      0.987   0.207      32.95        31.87
             wind      0.995   0.076     102.38       107.99

  [6] Plant-level annual generation — 2023 (EIA-923)
                           plant  EIA code  model GWh  EIA-923 GWh  diff %       class
                Colorado Bend II     60122       8907         7845   +13.5  CC_REGULAR
                  Wolf Hollow II     59812       8710         7018   +24.1  CC_REGULAR
                         Handley      3491        519         1519   -65.9      ST_GAS
         Deer Park Energy Center     55464       1785         6870   -74.0      CC_CHP
           Baytown Energy Center     55327       2517         5051   -50.2      CC_CHP
           Hidalgo Energy Center     55545       3409         2791   +22.1  CC_REGULAR
                Limestone (coal)       298       7148         6059   +18.0    COAL_PRB
     W A Parish (coal units 5-8)      3470       8076        10743   -24.8    COAL_PRB
       Stryker Creek (gas steam)      3504        708         1080   -34.5      ST_GAS
        Morgan Creek (CT peaker)      3492        282           74  +283.2   CT_PEAKER
    Topaz Generating (CT peaker)     63688       1075          722   +48.8   CT_PEAKER

  [7] Per-plant hourly dispatch fit — 2023 (model vs CAMPD net; representative panel)
                           plant  EIA code  Pearson r   NRMSE  model GWh  CAMPD GWh  op hrs
                Colorado Bend II     60122      0.417   0.367       8907       7859    7959
                  Wolf Hollow II     59812      0.534   0.447       8710       7012    7766
                         Handley      3491      0.692   1.256        518       1539    4267
         Deer Park Energy Center     55464      0.231   0.818       1786       6887    8738
           Baytown Energy Center     55327      0.400   0.562       2517       5050    8760
           Hidalgo Energy Center     55545          —       —          —          —       —
                Limestone (coal)       298      0.765   0.506       7148       6062    7712
     W A Parish (coal units 5-8)      3470      0.708   0.497       8076      10750    8760
       Stryker Creek (gas steam)      3504      0.737   1.183        708       1071    3635
        Morgan Creek (CT peaker)      3492      0.534   9.489        282         71     521
    Topaz Generating (CT peaker)     63688      0.652   1.775       1075        717    2958
    (full per-plant fit for all 99 resolved plants written to plant_hourly_fit.parquet)

================================================================================
  CALIBRATION REPORT  (ERCOT; run 2026-05-20T22:35:12; git 0173d38)
  bundle: results/calibration/ppmr_sig3_2024
================================================================================

================================================================================
  ERCOT 2024 BACKCAST
================================================================================

  [1] CHP — 2024  (model grid LP + behind-meter must-run vs EIA-923 total)
     class  grid LP  BTM-MR  model tot  EIA-923  diff %
    CC_CHP    26.63   31.81      58.44    55.04    +6.2
    CT_CHP     3.35   10.31      13.66    13.23    +3.2
    ST_CHP     0.81    0.26       1.07     0.47  +129.1
     TOTAL    30.79   42.38      73.17    68.74    +6.4
    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded from every table below.)

  [2] Grid generation reconciliation — 2024
    EIA-930 net generation (Demand + Interchange)          462.59 TWh
    Model demand target                                    462.59 TWh
    Model grid generation (LP)                             463.23 TWh
    Gap (model grid − EIA-930 net gen)                      +0.64 TWh
    Unserved energy / load slack (should be 0)             0.0000 TWh
    Behind-meter CHP must-run (off-grid; table [1] only)    42.38 TWh

  [3] Non-CHP grid generation — 2024  (model LP vs EIA-930, CHP excluded)
             fuel  model TWh  model %  EIA-930 TWh  EIA-930 %     Δpp
    gas (non-CHP)     182.18     42.1       172.89       40.2    +1.9
             coal      55.52     12.8        58.77       13.7    -0.8
          nuclear      38.07      8.8        38.80        9.0    -0.2
             wind     109.60     25.3       111.54       26.0    -0.6
            solar      47.07     10.9        47.68       11.1    -0.2
            TOTAL     432.44    100.0       429.68      100.0        
    (EIA-930 non-CHP gas = EIA-930 all-gas − 30.8 TWh model CHP grid-delivered.)

  [3b] Thermal by class — 2024  (model grid LP + behind-meter must-run vs EIA-923 total; coal split lignite/PRB)
           class  grid LP  BTM-MR  model tot  EIA-923  diff %
          CC_CHP    26.63   31.81      58.44    55.04    +6.2
      CC_REGULAR   166.40    0.00     166.40   145.41   +14.4
          CT_CHP     3.35   10.31      13.66    13.23    +3.2
       CT_PEAKER     9.09    0.00       9.09     8.12   +12.0
          ST_GAS     6.69    0.00       6.69    18.19   -63.2
          ST_CHP     0.81    0.26       1.07     0.47  +129.1
    COAL_LIGNITE    13.47    0.00      13.47    13.94    -3.4
        COAL_PRB    42.05    0.00      42.05    43.68    -3.7
           TOTAL   268.50   42.38     310.88   298.08    +4.3

  [4] Monthly bias — 2024   (% of EIA-923 per month; coal split; CHP incl. behind-meter)
           class     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec
          CC_CHP    +2.4    -3.5    +1.4    +5.4    +8.6    +9.1    +9.8   +10.6   +12.6    +9.5    +4.8    +1.1
      CC_REGULAR    +5.4    +7.6   +21.9   +40.5   +23.4   +12.1    +7.8    +4.5   +10.2   +20.5   +24.2   +14.9
          CT_CHP    +5.2    +4.2    +3.6    +2.6    +4.2    +4.8    +1.4    +3.7    +1.8    +5.7    +2.0    +0.2
       CT_PEAKER   +63.9   -58.3   -75.8   -61.2   +30.6   +17.2   +53.0   +67.2   +76.8   +36.9   -58.0   -40.6
          ST_GAS   -25.7   -71.6   -96.5   -96.2   -77.5   -57.3   -58.0   -40.0   -49.1   -61.8   -89.7   -87.3
          ST_CHP  +128.8  +109.9   +65.6  +111.8  +123.1  +129.3  +126.6  +237.1  +171.1  +112.6  +138.3  +132.8
    COAL_LIGNITE    -1.5   -22.4  +136.6   -13.9    -6.5   +24.0    +4.3    +0.3   -10.7   -26.5   -13.4   -10.4
        COAL_PRB    -4.6    -2.6   -20.2   -33.2   -14.1   +11.9    +6.1   +21.9    -3.0   -12.2   -14.8    -7.0
            wind    -2.1    -3.4    -2.4    -2.9    -2.7    -1.8    -1.8    -1.5    -0.7    -1.1    -1.3    -1.6
     solar (930)    -0.4    -1.1    -0.9    -1.6    -1.1    -1.5    -1.7    -1.9    -1.6    -0.7    -1.0    -0.8
         nuclear    +1.4    -8.2    +4.7    +2.5    +4.7    -8.4    +0.2    -4.4    -7.3    +2.9    +7.7    -6.0

  [5] Hourly dispatch fit — 2024 (model vs EIA-930, non-CHP gas)
             fuel  Pearson r   NRMSE  model TWh  EIA-930 TWh
    gas (non-CHP)      0.973   0.142     182.18       172.89
             coal      0.832   0.245      55.52        58.77
          nuclear      0.684   0.137      38.07        38.80
            solar      0.999   0.046      47.07        47.68
             wind      0.999   0.036     109.60       111.54

  [6] Plant-level annual generation — 2024 (EIA-923)
                           plant  EIA code  model GWh  EIA-923 GWh  diff %       class
                Colorado Bend II     60122       9127         6979   +30.8  CC_REGULAR
                  Wolf Hollow II     59812       8939         6461   +38.4  CC_REGULAR
                         Handley      3491        420          881   -52.3      ST_GAS
         Deer Park Energy Center     55464       1984         8004   -75.2      CC_CHP
           Baytown Energy Center     55327       2625         5089   -48.4      CC_CHP
           Hidalgo Energy Center     55545       3627         2056   +76.4  CC_REGULAR
                Limestone (coal)       298       5743         5365    +7.1    COAL_PRB
     W A Parish (coal units 5-8)      3470       7286        12166   -40.1    COAL_PRB
       Stryker Creek (gas steam)      3504        676          922   -26.7      ST_GAS
        Morgan Creek (CT peaker)      3492        246           24  +944.4   CT_PEAKER
    Topaz Generating (CT peaker)     63688       1205          689   +74.9   CT_PEAKER

  [7] Per-plant hourly dispatch fit — 2024 (model vs CAMPD net; representative panel)
                           plant  EIA code  Pearson r   NRMSE  model GWh  CAMPD GWh  op hrs
                Colorado Bend II     60122      0.483   0.503       9127       6964    8092
                  Wolf Hollow II     59812      0.460   0.598       8939       6466    7593
                         Handley      3491      0.623   1.813        420        861    2682
         Deer Park Energy Center     55464      0.507   0.782       1984       7987    8760
           Baytown Energy Center     55327      0.518   0.548       2625       5090    8760
           Hidalgo Energy Center     55545          —       —          —          —       —
                Limestone (coal)       298      0.753   0.568       5743       5362    6967
     W A Parish (coal units 5-8)      3470      0.700   0.579       7286      12159    8760
       Stryker Creek (gas steam)      3504      0.487   1.636        676        931    3666
        Morgan Creek (CT peaker)      3492      0.189  26.917        246         26     377
    Topaz Generating (CT peaker)     63688      0.584   1.870       1205        694    2886
    (full per-plant fit for all 100 resolved plants written to plant_hourly_fit.parquet)

================================================================================
  CALIBRATION REPORT  (ERCOT; run 2026-05-20T22:35:04; git 0173d38)
  bundle: results/calibration/ppmr_sig3_2025
================================================================================

================================================================================
  ERCOT 2025 BACKCAST
================================================================================

  [1] CHP — 2025  (model grid LP + behind-meter must-run vs EIA-923 total)
     class  grid LP  BTM-MR  model tot  EIA-923    diff %
    CC_CHP    24.70   31.98      56.68    52.94      +7.1
    CT_CHP     3.30    7.21      10.51     8.02     +31.1
    ST_CHP     0.80    0.00       0.80     0.00  +60406.9
     TOTAL    28.80   39.20      68.00    60.96     +11.5
    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded from every table below.)

  [2] Grid generation reconciliation — 2025
    EIA-930 net generation (Demand + Interchange)          488.06 TWh
    Model demand target                                    488.06 TWh
    Model grid generation (LP)                             488.72 TWh
    Gap (model grid − EIA-930 net gen)                      +0.67 TWh
    Unserved energy / load slack (should be 0)             0.0405 TWh
    Behind-meter CHP must-run (off-grid; table [1] only)    39.20 TWh

  [3] Non-CHP grid generation — 2025  (model LP vs EIA-930, CHP excluded)
             fuel  model TWh  model %  EIA-930 TWh  EIA-930 %     Δpp
    gas (non-CHP)     175.63     38.2       171.41       37.3    +0.9
             coal      67.03     14.6        63.37       13.8    +0.8
          nuclear      38.07      8.3        42.06        9.2    -0.9
             wind     113.10     24.6       115.12       25.1    -0.5
            solar      66.10     14.4        67.39       14.7    -0.3
            TOTAL     459.93    100.0       459.35      100.0        
    (EIA-930 non-CHP gas = EIA-930 all-gas − 28.8 TWh model CHP grid-delivered.)

  [3b] Thermal by class — 2025  (model grid LP + behind-meter must-run vs EIA-923 total; coal split lignite/PRB)
           class  grid LP  BTM-MR  model tot  EIA-923    diff %
          CC_CHP    24.70   31.98      56.68    52.94      +7.1
      CC_REGULAR   157.43    0.00     157.43   133.47     +17.9
          CT_CHP     3.30    7.21      10.51     8.02     +31.1
       CT_PEAKER    10.37    0.00      10.37     4.09    +153.3
          ST_GAS     7.83    0.00       7.83     6.46     +21.3
          ST_CHP     0.80    0.00       0.80     0.00  +60406.9
    COAL_LIGNITE    18.06    0.00      18.06    14.58     +23.9
        COAL_PRB    48.96    0.00      48.96    47.63      +2.8
           TOTAL   271.46   39.20     310.66   267.20     +16.3

  [4] Monthly bias — 2025   (% of EIA-923 per month; coal split; CHP incl. behind-meter)
           class        Jan        Feb        Mar       Apr       May       Jun        Jul       Aug       Sep       Oct       Nov       Dec
          CC_CHP       +4.1       +4.2       +3.6      +4.7      +8.6     +10.6      +10.7      +9.7      +9.6      +9.9      +5.2      +2.3
      CC_REGULAR      +15.9      +17.5      +51.0     +44.9      +9.6     +13.9      +10.1     +10.5      +7.5     +20.7     +33.4     +21.4
          CT_CHP      +26.9      +32.8      +25.5     +34.9     +38.9     +34.6      +32.7     +32.9     +30.4     +31.4     +27.2     +27.6
       CT_PEAKER     +435.4     +182.7      -19.6      -5.9    +218.1    +189.4     +208.0    +184.9    +262.8    +144.5     +38.3     +73.0
          ST_GAS      +85.6      +34.3      -75.7     -45.0     +68.5     +52.8      +45.2     +55.8     +48.3      -6.4     -52.1     -57.7
          ST_CHP  +136067.9  +219186.4  +112554.1  +47312.0  +34120.9  +64499.2  +149902.1  +50537.3  +63878.4  +36572.2  +31221.2  +67890.1
    COAL_LIGNITE       +4.5      +30.4      +28.6     +42.6    +116.1     +24.8      +20.1     +19.9     +33.5     -11.1     +23.0     +18.3
        COAL_PRB      -10.6       -8.4      -18.8      -7.6      -2.3     +16.5      +19.5     +20.7      +5.4      -3.1      -6.5     +17.6
            wind      +21.9      +24.0      +22.9     +25.6     +23.3     +25.8      +23.9     +25.4     +30.4     +27.1     +22.4     +25.3
     solar (930)       -0.8       -1.1       -2.4      -3.8      -2.2      -2.1       -2.8      -1.4      -2.0      -1.1      -0.9      -1.5
         nuclear       -2.9       -5.9      -15.1     -17.9      -8.5     -10.1       -7.7      -6.3      -2.3      -8.5     -11.8      -6.2

  [5] Hourly dispatch fit — 2025 (model vs EIA-930, non-CHP gas)
             fuel  Pearson r   NRMSE  model TWh  EIA-930 TWh
    gas (non-CHP)      0.937   0.166     175.63       171.41
             coal      0.778   0.207      67.03        63.37
          nuclear      0.643   0.126      38.07        42.06
            solar      0.999   0.054      66.10        67.39
             wind      0.999   0.037     113.10       115.12

  [6] Plant-level annual generation — 2025 (EIA-923)
                           plant  EIA code  model GWh  EIA-923 GWh  diff %       class
                Colorado Bend II     60122       8860         6072   +45.9  CC_REGULAR
                  Wolf Hollow II     59812       8678         5438   +59.6  CC_REGULAR
                         Handley      3491        297          894   -66.8      ST_GAS
         Deer Park Energy Center     55464       1470         7822   -81.2      CC_CHP
           Baytown Energy Center     55327       2475         3747   -34.0      CC_CHP
           Hidalgo Energy Center     55545       3263         2721   +19.9  CC_REGULAR
                Limestone (coal)       298       9041         7523   +20.2    COAL_PRB
     W A Parish (coal units 5-8)      3470      10067        15579   -35.4    COAL_PRB
       Stryker Creek (gas steam)      3504        647            0       —      ST_GAS
        Morgan Creek (CT peaker)      3492        214            0       —   CT_PEAKER
    Topaz Generating (CT peaker)     63688       1043          599   +74.3   CT_PEAKER

  [7] Per-plant hourly dispatch fit — 2025 (model vs CAMPD net; representative panel)
                           plant  EIA code  Pearson r   NRMSE  model GWh  CAMPD GWh  op hrs
                Colorado Bend II     60122      0.570   0.631       8860       6102    7828
                  Wolf Hollow II     59812      0.454   0.796       8678       5505    7280
                         Handley      3491      0.588   1.918        296        898    2798
         Deer Park Energy Center     55464      0.526   0.842       1470       7804    8760
           Baytown Energy Center     55327      0.335   0.544       2475       3973    8756
           Hidalgo Energy Center     55545          —       —          —          —       —
                Limestone (coal)       298      0.570   0.525       9041       7471    8496
     W A Parish (coal units 5-8)      3470      0.667   0.468      10067      15511    8760
       Stryker Creek (gas steam)      3504      0.552   1.291        647       1356    4484
        Morgan Creek (CT peaker)      3492      0.287  17.678        214         38     349
    Topaz Generating (CT peaker)     63688      0.583   2.077       1043        609    2804
    (full per-plant fit for all 100 resolved plants written to plant_hourly_fit.parquet)

================================================================================
  CALIBRATION REPORT  (ERCOT; run 2026-05-20T23:40:53; git f3cf502)
  bundle: results/calibration/tier66_2023
================================================================================

================================================================================
  ERCOT 2023 BACKCAST
================================================================================

  [1] CHP — 2023  (model grid LP + behind-meter must-run vs EIA-923 total)
     class  grid LP  BTM-MR  model tot  EIA-923  diff %
    CC_CHP    25.21   32.02      57.24    53.00    +8.0
    CT_CHP     3.32    9.60      12.91    13.04    -1.0
    ST_CHP     0.81    0.20       1.01     0.52   +92.9
     TOTAL    29.34   41.82      71.16    66.57    +6.9
    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded from every table below.)

  [2] Grid generation reconciliation — 2023
    EIA-930 net generation (Demand + Interchange)          445.97 TWh
    Model demand target                                    445.97 TWh
    Model grid generation (LP)                             446.20 TWh
    Gap (model grid − EIA-930 net gen)                      +0.23 TWh
    Unserved energy / load slack (should be 0)             0.0000 TWh
    Behind-meter CHP must-run (off-grid; table [1] only)    41.82 TWh

  [3] Non-CHP grid generation — 2023  (model LP vs EIA-930, CHP excluded)
             fuel  model TWh  model %  EIA-930 TWh  EIA-930 %     Δpp
    gas (non-CHP)     178.47     42.8       172.13       41.5    +1.4
             coal      64.99     15.6        62.29       15.0    +0.6
          nuclear      38.07      9.1        40.91        9.9    -0.7
             wind     102.38     24.6       107.99       26.0    -1.4
            solar      32.95      7.9        31.87        7.7    +0.2
            TOTAL     416.86    100.0       415.19      100.0        
    (EIA-930 non-CHP gas = EIA-930 all-gas − 29.3 TWh model CHP grid-delivered.)

  [3b] Thermal by class — 2023  (model grid LP + behind-meter must-run vs EIA-923 total; coal split lignite/PRB)
           class  grid LP  BTM-MR  model tot  EIA-923  diff %
          CC_CHP    25.21   32.02      57.24    53.00    +8.0
      CC_REGULAR   162.10    0.00     162.10   143.70   +12.8
          CT_CHP     3.32    9.60      12.91    13.04    -1.0
       CT_PEAKER     9.29    0.00       9.29     7.47   +24.4
          ST_GAS     7.09    0.00       7.09    16.83   -57.9
          ST_CHP     0.81    0.20       1.01     0.52   +92.9
    COAL_LIGNITE    16.66    0.00      16.66    15.33    +8.7
        COAL_PRB    48.33    0.00      48.33    45.09    +7.2
           TOTAL   272.80   41.82     314.62   294.98    +6.7

  [4] Monthly bias — 2023   (% of EIA-923 per month; coal split; CHP incl. behind-meter)
           class     Jan    Feb     Mar    Apr    May     Jun     Jul     Aug     Sep    Oct    Nov    Dec
          CC_CHP    +5.0   +3.3    +0.7   +9.1  +12.3   +12.3   +14.0   +12.8   +10.6  +12.1   +3.9   -1.6
      CC_REGULAR    +9.7   +8.9   +21.0  +25.3  +12.3   +13.1    +6.9    +4.6    +9.3  +16.1  +28.4  +14.9
          CT_CHP    -0.8   -2.9    -3.2   -1.4   -2.7    -1.2    +0.4    +1.7    +1.2   +0.4   -3.4   -0.7
       CT_PEAKER   -15.5   +3.2   -76.3  -65.7  +13.2   +36.5   +79.2   +54.9   +83.6  +29.3  -44.3  -21.4
          ST_GAS   -19.8  -40.0  -100.0  -99.6  -79.1   -57.8   -48.4   -41.0   -45.1  -78.8  -95.0  -70.4
          ST_CHP  +112.4  +98.1   +46.2  +58.3  +86.5  +120.2  +136.6  +129.7  +139.3  +76.9  +64.8  +70.7
    COAL_LIGNITE    -5.4  -16.8   +52.7  -15.2   -3.4   +14.1   +15.5   +27.5   +26.3  +10.8  +10.8   +6.6
        COAL_PRB   +54.7  +13.6   -10.8   -8.6   +6.3    +5.0   +14.1   +25.9    +8.1   -7.3   -4.4   -4.3
            wind    -4.1   -2.5    -2.1   -5.5   -7.7    -7.8    -7.7    -7.2    -8.5   -5.8   -4.9   -4.9
     solar (930)   +11.1  +25.2   +16.4   +9.5   -0.6    +0.3    -1.2    -2.4    -1.9   +2.1   +1.3   +4.7
         nuclear    -7.9   -6.2    -2.8   +0.7   +3.9    -5.4    -6.7    -5.7    -7.2  -20.0  -11.4   -6.0

  [5] Hourly dispatch fit — 2023 (model vs EIA-930, non-CHP gas)
             fuel  Pearson r   NRMSE  model TWh  EIA-930 TWh
    gas (non-CHP)      0.982   0.120     178.47       172.13
             coal      0.866   0.220      64.99        62.29
          nuclear      0.665   0.112      38.07        40.91
            solar      0.987   0.207      32.95        31.87
             wind      0.995   0.076     102.38       107.99

  [6] Plant-level annual generation — 2023 (EIA-923)
                           plant  EIA code  model GWh  EIA-923 GWh  diff %       class
                Colorado Bend II     60122       8879         7845   +13.2  CC_REGULAR
                  Wolf Hollow II     59812       8680         7018   +23.7  CC_REGULAR
                         Handley      3491        510         1519   -66.4      ST_GAS
         Deer Park Energy Center     55464       1743         6870   -74.6      CC_CHP
           Baytown Energy Center     55327       2503         5051   -50.4      CC_CHP
           Hidalgo Energy Center     55545       3375         2791   +20.9  CC_REGULAR
                Limestone (coal)       298       7814         6059   +29.0    COAL_PRB
     W A Parish (coal units 5-8)      3470       8985        10743   -16.4    COAL_PRB
       Stryker Creek (gas steam)      3504        680         1080   -37.0      ST_GAS
        Morgan Creek (CT peaker)      3492        262           74  +256.2   CT_PEAKER
    Topaz Generating (CT peaker)     63688       1030          722   +42.6   CT_PEAKER

  [7] Per-plant hourly dispatch fit — 2023 (model vs CAMPD net; representative panel)
                           plant  EIA code  Pearson r   NRMSE  model GWh  CAMPD GWh  op hrs
                Colorado Bend II     60122      0.413   0.366       8880       7859    7959
                  Wolf Hollow II     59812      0.538   0.444       8680       7012    7766
                         Handley      3491      0.705   1.240        510       1539    4267
         Deer Park Energy Center     55464      0.254   0.821       1743       6887    8738
           Baytown Energy Center     55327      0.400   0.564       2504       5050    8760
           Hidalgo Energy Center     55545          —       —          —          —       —
                Limestone (coal)       298      0.752   0.579       7814       6062    7712
     W A Parish (coal units 5-8)      3470      0.699   0.478       8985      10750    8760
       Stryker Creek (gas steam)      3504      0.735   1.191        680       1071    3635
        Morgan Creek (CT peaker)      3492      0.543   8.951        262         71     521
    Topaz Generating (CT peaker)     63688      0.635   1.786       1030        717    2958
    (full per-plant fit for all 99 resolved plants written to plant_hourly_fit.parquet)

================================================================================
  CALIBRATION REPORT  (ERCOT; run 2026-05-20T23:41:18; git f3cf502)
  bundle: results/calibration/tier66_2024
================================================================================

================================================================================
  ERCOT 2024 BACKCAST
================================================================================

  [1] CHP — 2024  (model grid LP + behind-meter must-run vs EIA-923 total)
     class  grid LP  BTM-MR  model tot  EIA-923  diff %
    CC_CHP    26.53   31.90      58.44    55.04    +6.2
    CT_CHP     3.33   10.33      13.66    13.23    +3.2
    ST_CHP     0.81    0.26       1.07     0.47  +129.1
     TOTAL    30.68   42.49      73.17    68.74    +6.4
    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded from every table below.)

  [2] Grid generation reconciliation — 2024
    EIA-930 net generation (Demand + Interchange)          462.59 TWh
    Model demand target                                    462.59 TWh
    Model grid generation (LP)                             463.23 TWh
    Gap (model grid − EIA-930 net gen)                      +0.63 TWh
    Unserved energy / load slack (should be 0)             0.0000 TWh
    Behind-meter CHP must-run (off-grid; table [1] only)    42.49 TWh

  [3] Non-CHP grid generation — 2024  (model LP vs EIA-930, CHP excluded)
             fuel  model TWh  model %  EIA-930 TWh  EIA-930 %     Δpp
    gas (non-CHP)     180.43     41.7       173.00       40.3    +1.5
             coal      57.39     13.3        58.77       13.7    -0.4
          nuclear      38.07      8.8        38.80        9.0    -0.2
             wind     109.60     25.3       111.54       26.0    -0.6
            solar      47.07     10.9        47.68       11.1    -0.2
            TOTAL     432.55    100.0       429.80      100.0        
    (EIA-930 non-CHP gas = EIA-930 all-gas − 30.7 TWh model CHP grid-delivered.)

  [3b] Thermal by class — 2024  (model grid LP + behind-meter must-run vs EIA-923 total; coal split lignite/PRB)
           class  grid LP  BTM-MR  model tot  EIA-923  diff %
          CC_CHP    26.53   31.90      58.44    55.04    +6.2
      CC_REGULAR   165.24    0.00     165.24   145.41   +13.6
          CT_CHP     3.33   10.33      13.66    13.23    +3.2
       CT_PEAKER     8.71    0.00       8.71     8.12    +7.3
          ST_GAS     6.47    0.00       6.47    18.19   -64.4
          ST_CHP     0.81    0.26       1.07     0.47  +129.1
    COAL_LIGNITE    14.35    0.00      14.35    13.94    +3.0
        COAL_PRB    43.04    0.00      43.04    43.68    -1.5
           TOTAL   268.49   42.49     310.98   298.08    +4.3

  [4] Monthly bias — 2024   (% of EIA-923 per month; coal split; CHP incl. behind-meter)
           class     Jan     Feb     Mar     Apr     May     Jun     Jul     Aug     Sep     Oct     Nov     Dec
          CC_CHP    +2.6    -3.1    +1.0    +5.2    +8.5    +9.3    +9.8   +10.7   +12.9    +8.8    +4.2    +1.4
      CC_REGULAR    +5.4    +7.8   +19.2   +37.3   +22.0   +12.1    +7.7    +4.3   +10.2   +18.5   +21.4   +15.2
          CT_CHP    +5.4    +4.4    +3.6    +2.6    +3.9    +5.1    +1.5    +3.6    +1.8    +5.2    +1.9    +0.4
       CT_PEAKER   +64.8   -58.0   -81.6   -63.4   +16.8   +20.9   +49.6   +65.0   +70.1   +21.9   -66.9   -40.7
          ST_GAS   -24.8   -71.5   -98.1   -96.8   -80.8   -57.5   -58.4   -38.7   -50.1   -67.4   -93.8   -87.2
          ST_CHP  +129.1  +110.3   +65.1  +110.8  +123.5  +129.7  +126.9  +237.5  +171.4  +111.7  +137.9  +133.1
    COAL_LIGNITE    -1.3   -21.8  +174.6    -1.5    +5.4   +27.7    +7.4    +4.0    -7.7   -14.2    -2.1    -8.9
        COAL_PRB    -5.0    -4.2   -13.5   -26.1    -7.0   +10.1    +6.5   +21.2    -2.8    -3.6    -6.1    -8.5
            wind    -2.1    -3.4    -2.4    -2.9    -2.7    -1.8    -1.8    -1.5    -0.7    -1.1    -1.3    -1.6
     solar (930)    -0.4    -1.1    -0.9    -1.6    -1.1    -1.5    -1.7    -1.9    -1.6    -0.7    -1.0    -0.8
         nuclear    +1.4    -8.2    +4.7    +2.5    +4.7    -8.4    +0.2    -4.4    -7.3    +2.9    +7.7    -6.0

  [5] Hourly dispatch fit — 2024 (model vs EIA-930, non-CHP gas)
             fuel  Pearson r   NRMSE  model TWh  EIA-930 TWh
    gas (non-CHP)      0.972   0.139     180.43       173.00
             coal      0.830   0.240      57.39        58.77
          nuclear      0.684   0.137      38.07        38.80
            solar      0.999   0.046      47.07        47.68
             wind      0.999   0.036     109.60       111.54

  [6] Plant-level annual generation — 2024 (EIA-923)
                           plant  EIA code  model GWh  EIA-923 GWh  diff %       class
                Colorado Bend II     60122       9101         6979   +30.4  CC_REGULAR
                  Wolf Hollow II     59812       8894         6461   +37.7  CC_REGULAR
                         Handley      3491        389          881   -55.8      ST_GAS
         Deer Park Energy Center     55464       1971         8004   -75.4      CC_CHP
           Baytown Energy Center     55327       2612         5089   -48.7      CC_CHP
           Hidalgo Energy Center     55545       3610         2056   +75.6  CC_REGULAR
                Limestone (coal)       298       6323         5365   +17.9    COAL_PRB
     W A Parish (coal units 5-8)      3470       8383        12166   -31.1    COAL_PRB
       Stryker Creek (gas steam)      3504        662          922   -28.1      ST_GAS
        Morgan Creek (CT peaker)      3492        229           24  +872.8   CT_PEAKER
    Topaz Generating (CT peaker)     63688       1152          689   +67.3   CT_PEAKER

  [7] Per-plant hourly dispatch fit — 2024 (model vs CAMPD net; representative panel)
                           plant  EIA code  Pearson r   NRMSE  model GWh  CAMPD GWh  op hrs
                Colorado Bend II     60122      0.486   0.500       9101       6964    8092
                  Wolf Hollow II     59812      0.461   0.593       8894       6466    7593
                         Handley      3491      0.617   1.825        389        861    2682
         Deer Park Energy Center     55464      0.515   0.783       1971       7987    8760
           Baytown Energy Center     55327      0.522   0.550       2612       5090    8760
           Hidalgo Energy Center     55545          —       —          —          —       —
                Limestone (coal)       298      0.753   0.609       6323       5362    6967
     W A Parish (coal units 5-8)      3470      0.703   0.523       8382      12159    8760
       Stryker Creek (gas steam)      3504      0.487   1.636        662        931    3666
        Morgan Creek (CT peaker)      3492      0.173  25.827        229         26     377
    Topaz Generating (CT peaker)     63688      0.574   1.852       1152        694    2886
    (full per-plant fit for all 100 resolved plants written to plant_hourly_fit.parquet)

================================================================================
  CALIBRATION REPORT  (ERCOT; run 2026-05-20T23:41:15; git f3cf502)
  bundle: results/calibration/tier66_2025
================================================================================

================================================================================
  ERCOT 2025 BACKCAST
================================================================================

  [1] CHP — 2025  (model grid LP + behind-meter must-run vs EIA-923 total)
     class  grid LP  BTM-MR  model tot  EIA-923    diff %
    CC_CHP    24.43   32.25      56.67    52.94      +7.1
    CT_CHP     3.27    7.22      10.49     8.02     +30.9
    ST_CHP     0.80    0.00       0.80     0.00  +60020.5
     TOTAL    28.50   39.47      67.97    60.96     +11.5
    (BTM-MR = behind-the-meter must-run, off-grid. CHP is excluded from every table below.)

  [2] Grid generation reconciliation — 2025
    EIA-930 net generation (Demand + Interchange)          488.06 TWh
    Model demand target                                    488.06 TWh
    Model grid generation (LP)                             488.75 TWh
    Gap (model grid − EIA-930 net gen)                      +0.70 TWh
    Unserved energy / load slack (should be 0)             0.0097 TWh
    Behind-meter CHP must-run (off-grid; table [1] only)    39.47 TWh

  [3] Non-CHP grid generation — 2025  (model LP vs EIA-930, CHP excluded)
             fuel  model TWh  model %  EIA-930 TWh  EIA-930 %     Δpp
    gas (non-CHP)     172.13     37.4       171.71       37.4    +0.0
             coal      70.86     15.4        63.37       13.8    +1.6
          nuclear      38.07      8.3        42.06        9.2    -0.9
             wind     113.10     24.6       115.12       25.0    -0.5
            solar      66.10     14.4        67.39       14.7    -0.3
            TOTAL     460.26    100.0       459.65      100.0        
    (EIA-930 non-CHP gas = EIA-930 all-gas − 28.5 TWh model CHP grid-delivered.)

  [3b] Thermal by class — 2025  (model grid LP + behind-meter must-run vs EIA-923 total; coal split lignite/PRB)
           class  grid LP  BTM-MR  model tot  EIA-923    diff %
          CC_CHP    24.43   32.25      56.67    52.94      +7.1
      CC_REGULAR   155.00    0.00     155.00   133.47     +16.1
          CT_CHP     3.27    7.22      10.49     8.02     +30.9
       CT_PEAKER     9.78    0.00       9.78     4.09    +138.8
          ST_GAS     7.35    0.00       7.35     6.46     +13.8
          ST_CHP     0.80    0.00       0.80     0.00  +60020.5
    COAL_LIGNITE    19.30    0.00      19.30    14.58     +32.3
        COAL_PRB    51.57    0.00      51.57    47.63      +8.3
           TOTAL   271.49   39.47     310.96   267.20     +16.4

  [4] Monthly bias — 2025   (% of EIA-923 per month; coal split; CHP incl. behind-meter)
           class        Jan        Feb        Mar       Apr       May       Jun        Jul       Aug       Sep       Oct       Nov       Dec
          CC_CHP       +4.6       +4.7       +2.9      +4.3      +8.0     +10.9      +10.9     +10.0     +10.0      +9.1      +4.4      +2.8
      CC_REGULAR      +15.7      +17.8      +44.1     +38.6      +6.3     +13.1       +9.4      +9.9      +6.9     +17.1     +27.9     +21.5
          CT_CHP      +27.0      +32.9      +25.3     +34.7     +38.0     +34.7      +32.4     +32.8     +30.3     +30.7     +27.0     +27.7
       CT_PEAKER     +438.0     +182.1      -35.9     -19.2    +178.7    +179.7     +198.9    +176.5    +254.6    +115.4     +15.1     +72.7
          ST_GAS      +79.5      +34.6      -81.5     -57.8     +43.8     +47.2      +41.8     +51.3     +41.9     -18.2     -62.3     -57.8
          ST_CHP  +136067.9  +219186.4  +112546.8  +45306.5  +33902.0  +64062.0  +149768.8  +50449.1  +63822.3  +36285.7  +30625.6  +67890.1
    COAL_LIGNITE       +4.5      +30.4      +48.3     +64.2    +148.8     +28.2      +23.3     +23.1     +37.1      +2.3     +41.9     +18.3
        COAL_PRB       -9.7       -9.2       -9.4      +3.9     +10.3     +19.3      +22.6     +24.0      +7.8      +9.9      +5.8     +17.2
            wind      +21.9      +24.0      +22.9     +25.6     +23.3     +25.8      +23.9     +25.4     +30.4     +27.1     +22.4     +25.3
     solar (930)       -0.8       -1.1       -2.4      -3.8      -2.2      -2.1       -2.8      -1.4      -2.0      -1.1      -0.9      -1.5
         nuclear       -2.9       -5.9      -15.1     -17.9      -8.5     -10.1       -7.7      -6.3      -2.3      -8.5     -11.8      -6.2

  [5] Hourly dispatch fit — 2025 (model vs EIA-930, non-CHP gas)
             fuel  Pearson r   NRMSE  model TWh  EIA-930 TWh
    gas (non-CHP)      0.939   0.161     172.13       171.71
             coal      0.761   0.237      70.86        63.37
          nuclear      0.643   0.126      38.07        42.06
            solar      0.999   0.054      66.10        67.39
             wind      0.999   0.037     113.10       115.12

  [6] Plant-level annual generation — 2025 (EIA-923)
                           plant  EIA code  model GWh  EIA-923 GWh  diff %       class
                Colorado Bend II     60122       8800         6072   +44.9  CC_REGULAR
                  Wolf Hollow II     59812       8627         5438   +58.6  CC_REGULAR
                         Handley      3491        267          894   -70.1      ST_GAS
         Deer Park Energy Center     55464       1413         7822   -81.9      CC_CHP
           Baytown Energy Center     55327       2461         3747   -34.3      CC_CHP
           Hidalgo Energy Center     55545       3214         2721   +18.1  CC_REGULAR
                Limestone (coal)       298       9524         7523   +26.6    COAL_PRB
     W A Parish (coal units 5-8)      3470      10868        15579   -30.2    COAL_PRB
       Stryker Creek (gas steam)      3504        611            0       —      ST_GAS
        Morgan Creek (CT peaker)      3492        193            0       —   CT_PEAKER
    Topaz Generating (CT peaker)     63688        975          599   +62.8   CT_PEAKER

  [7] Per-plant hourly dispatch fit — 2025 (model vs CAMPD net; representative panel)
                           plant  EIA code  Pearson r   NRMSE  model GWh  CAMPD GWh  op hrs
                Colorado Bend II     60122      0.585   0.620       8800       6102    7828
                  Wolf Hollow II     59812      0.454   0.789       8627       5505    7280
                         Handley      3491      0.579   1.941        267        898    2798
         Deer Park Energy Center     55464      0.527   0.849       1413       7804    8760
           Baytown Energy Center     55327      0.339   0.546       2461       3973    8756
           Hidalgo Energy Center     55545          —       —          —          —       —
                Limestone (coal)       298      0.559   0.567       9524       7471    8496
     W A Parish (coal units 5-8)      3470      0.672   0.435      10868      15511    8760
       Stryker Creek (gas steam)      3504      0.550   1.301        611       1356    4484
        Morgan Creek (CT peaker)      3492      0.292  16.809        193         38     349
    Topaz Generating (CT peaker)     63688      0.570   2.021        974        609    2804
    (full per-plant fit for all 100 resolved plants written to plant_hourly_fit.parquet)

```
