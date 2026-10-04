# FINDING — closeout-MISO-w3 phase 0: the 2019–2022 legs run the seam on a flat annual ladder because the hourly neighbour offsets stop at 2023; the data boundary that stopped them has moved

```
LANE     : closeout-MISO-w3 (desk charter 2026-10-04, session_01ERkBTm23ZAP4CTZnJVD9Ss; owner direction 2026-10-04)
KEEPER   : 2026-10-03-closeout-miso-nuc-r (results/calibration/closeout_miso_nuc_span), rubric v3.20, NOT-YET
LP       : none (keeper hourly sidecars + unit_marginal, EIA-930 balance, frozen derive scripts)
PROBE    : scripts/probes/_closeout_miso_w3_seam_hourly_phase0.py -> results/phase0/miso/_closeout_miso_w3_seam_hourly_phase0.json
```

## 1. Failing records and what carries them (keeper, zero LP)

| record | value | band | carried by |
|---|---:|---:|---|
| C1 ST_GAS 2019 | −8.71 TWh | ±8.00 | MISO-South VLR steam (MISO-F1, DATA-LIMITED) |
| C1 CC_REGULAR 2021 | −8.15 TWh | ±8.00 | Sep–Dec −10.4 TWh vs EIA-923 (MISO-F2) |
| C3a 2020 | +10.2 % ($24.21 vs $21.97) | ±10 % | Jan–Jun, Sep, Nov +$2–4.8; Jul–Aug −$1.3/−$1.7 |
| C3b 2021 | NRMSE 0.219 | 0.20 | Feb (Uri) −$16; Sep–Nov −$9.5/−$16.0/−$13.2 |

Monthly load-weighted LMP, keeper vs RT actual ($/MWh):

| | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020 model | 24.9 | 23.6 | 22.5 | 21.5 | 22.6 | 22.7 | 25.4 | 25.5 | 23.7 | 25.2 | 24.9 | 27.1 |
| 2020 actual | 22.2 | 19.5 | 18.0 | 18.3 | 19.1 | 20.1 | 26.7 | 27.2 | 18.9 | 24.5 | 21.1 | 24.4 |
| 2021 model | 29.2 | 44.8 | 28.7 | 30.1 | 30.4 | 32.9 | 40.0 | 42.4 | 36.7 | 40.3 | 39.2 | 33.8 |
| 2021 actual | 23.9 | 60.9 | 23.0 | 28.3 | 27.7 | 35.6 | 37.4 | 40.5 | 46.2 | 56.3 | 52.4 | 37.8 |

Both years miss in the same pattern: the model is too flat across the year. It is too high when neighbour prices were low (spring 2020) and too low when they were high (summer 2020, fall 2021). The marginal-unit census (`unit_marginal`, P1, `marginal == 1`) shows the seam import bands set the price in a large share of hours:
- **2020: 31 %** of marginal unit-hours are seam bands, at a median $24.75. PJM band 6 sits at $21.60 for 1,035 h and band 7 at $26.74 for 473 h.
- In fall 2021, when the seam is not marginal, CC_REGULAR is (58 % of Sep–Nov marginal hours).

## 2. The defect: the seam ladder's hourly form stops at 2023

The keeper arms `miso_seam_neighbour_hourly_ladder` and `miso_seam_neighbour_hourly_spp` in **all seven legs** (every `run_config_<y>.json`). Band k's offer is `anchor(t) + δ_k`, where the anchor is the measured PJM western-border DA price or the SPP North hub DA price. But `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY{,_SPP}_BY_YEAR` carries only 2023–2025. For 2019–2022, `inject_miso_seam_ladder_prices` therefore falls back to the annual MISO-hub Q-Q ladder, and every band takes **one price all year**.

PJM/SPP seam-band offer std across the 8,760 hours, in the keeper's own `unit_marginal`:

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|
| PJM band mc std ($/MWh) | 0.00 | 0.00 | 0.00 | 0.00 | 12.88 | 16.10 |
| SPP band mc std ($/MWh) | 0.00 | 0.00 | 0.00 | 0.00 | 19.76 | 25.78 |

This is the defect miso-226 named, now present on four of seven years: a fixed ladder is cleared against the model's own price, so it leaves merit when MISO's price falls. miso-252 and miso-261 recorded these years as "blocked on data (PJM border LMP and the SPP hub both start 2023; an intake charter, not a lever)".

**What is new: that boundary has moved.**
- `data/raw/lmp-data/PJM_{2019..2022}_rt_da_monthly_lmps.csv` (tracked; PJM Data Miner 2 `da_hrl_lmps`) carry CHICAGO GEN / AEP GEN / ATSI GEN hourly, 105,120 rows a year.
- `actual_lmp_hourly_zonal_SPP.parquet` carries SPPNORTH_HUB DA for 2019–2025.
- `build_pjm_border_lmp_miso.py --years 2019 … 2025` adds the 2019–2022 border rows ($25.28 / $19.83 / $36.41 / $65.20 mean) with 2023–2025 byte-identical (max |diff| 0.0).
- The frozen `derive_miso_seam_ladders.py --years 2019 … 2025` then prints 2019–2022 PJM and SPP hourly offsets. It reproduces every committed 2023–2025 PJM/SPP offset and every committed 2019–2022 base row exactly.

## 3. Candidates, ranked by computed reach on the failing records

| # | candidate | cell | reach (zero LP) | admissible? |
|---|---|---|---|---|
| **1** | **hourly neighbour seam ladder, full span 2019–2022** (`miso_seam_neighbour_hourly_full_span`) | `seam_neighbour_hourly_ladder` K (year extension; new evidence §2) | static, keeper price held: net import 2019/20/21/22 −5.3/−4.1/−8.7/−8.2 TWh. ΔP load-weighted +0.36/+0.29/+2.59/+4.22. 2021 Sep/Oct/Nov +3.3/+7.3/+5.8, Feb +6.5. 2020 low-load quintile −0.81, Mar–May −0.13/−0.55/−0.37, Jul–Aug +0.6/+0.8. C3b 2021 0.219 → 0.198 at the 0.27 LP constant (0.146 static). Fall-2021 import cut lands on CC_REGULAR (58 % of Sep–Nov marginal hours) | yes: rule 14 (a measured neighbour price replaces an own-hub estimate), rule 23 (source-data extension, frozen derive), zero DOF, the K mechanism's own construction |
| 2 | `mustrun_chp_btm_holdout` | O (miso-253 OOM, no verdict) | removes ~12.5 TWh/yr of BTM must-run from the grid (2023 footprint). CC_REGULAR rises in every year, but prices rise in every year: C3a 2020 worse, and C3a 2019 (+6.2 %) at risk of PASS→FAIL | yes (rule 14). Ranked second because it moves C3a 2020 the wrong way and risks a new C3a FAIL; footprint for 2019–2022 not yet measured |
| 3 | wind gross-up `vre_curtailment_oversupply_allocation` | U | wind +2.9…+5.1 TWh/yr is the un-recurtailed 4.9 % reference gross-up (P1 on the bound in 8,760 h). Removing it lifts CC_REGULAR 2021 (~+1.5 TWh) but raises low-load prices (C3a 2020 worse) | the curtailment it represents is West/Plains congestion (`internal_congestion_split` G), so a re-allocation stands in for a refused object; not chartered |
| 4 | `vre_reference_rate_year_own` | U | MISO's own table has no 2019/2020 curtailment rows; 2021 6.7 % > the 4.9 % reference, which is the wrong sign for CC_REGULAR 2021 | not chartered (sign) |

## 4. Reading

Candidate 1 is the only admissible lever with reach on C1 CC_REGULAR 2021 and C3b 2021 that needs no ruling or download. It repairs the shape object on both failing price records: spring 2020 down, summer 2020 up, fall 2021 up. On the 2020 annual mean it is the wrong sign: +$0.08 to +$0.29 on a record already failing at +10.2 %. That is declared ex ante in the PRECOMMIT. Nothing here reaches C1 ST_GAS 2019 beyond a small by-product (ST_GAS is 12 % of 2019 marginal hours).
