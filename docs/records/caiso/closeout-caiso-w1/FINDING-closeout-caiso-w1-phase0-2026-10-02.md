# FINDING closeout-CAISO wave 1: phase 0 (zero LP), steps 0b / 0c / 0d (2026-10-02)

Lane charter: Backcast close-out desk, 2026-10-02 (plan `docs/backcast-closeout-plan-2026-10.md` §3.7; owner
rulings R-11, R-14, R-16). **Zero LP.** No shard launched, no run registered, keeper unchanged:
`2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25, CALIBRATED, one ledgered C3c 2024) and its fold
`-touchpoints` (bundle `rcaiso20_A_tp_2019_2021`, NOT-YET). Base `origin/main` `4d459da3`.

Probes (committed beside this record):
- `scripts/probes/_closeout_caiso_w1_corridor_census.py` (0b): reads the R-CAISO-20 fold legs' P1 `unit_hourly` from
  their shard commits (`fe270e64`, `616bef4e`, `c1040fa2`; provenance only, rule 33).
- `scripts/probes/_closeout_caiso_w1_basis_tail.py` `tail` (0d) and `basis` (0c): the fold / keeper bundles'
  committed hourlies plus the sanctioned fleet-only rebuild (`replay_keeper.run_year_kwargs` +
  `run_year(fleet_only=True)`).

## Headline

| Step | Pre-fixed reading | Measured | Verdict |
|---|---|---|---|
| 0b PNW/DSW vs EIA-930 | close the C1 fold arithmetic (DSW −9.3 vs CC +10.75 in 2019) | net import gap **−1.8 / −11.4 / −8.0 TWh** vs CC_REGULAR **+10.75 / +17.55 / +10.17** | 2019 is **not an import object**; 2020–21 imports explain ~65–80 % |
| 0c `zonal_gas_basis` 2021 | ≥ 2 pp projected on C3a 2021 | **+0.01 pp** (load-weighted Δλ $0.00/MWh on the gated months) | **FAILS the pre-fixed bar.** The mean-zero anchor cancels north against south. |
| 0d C3c-2021 census | count attributable to SDGE cap / $180 placeholder | **0 / 0 of 89.** All 89 hours fall on 2021-02-13…17 (Uri gas spike), **none inside the RT reference window** | the "measured-input limitation" label is wrong; it is a **scoring-window mismatch** (§3) |

## 1. Step 0b: corridor net import vs EIA-930 (R-CAISO-7 Object-1 table on the current fold)

Model = P1 sum over every unit in the corridor's WECC zone (imports +, export sink −), as R-CAISO-7. Measured =
`derive_caiso_import_tranches.corridor_net_import` (EIA-930 CISO interchange by DIBA, model clock; 1 missing hour per
year).

| TWh | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| PNW net import, model / EIA-930 | 16.66 / 9.15 | 21.07 / 17.32 | 15.82 / 13.60 |
| PNW gap | **+7.51** | +3.75 | +2.22 |
| DSW net import, model / EIA-930 | 35.40 / 44.69 | 26.76 / 41.90 | 30.66 / 40.87 |
| DSW gap | −9.29 | **−15.14** | −10.21 |
| **total net-import gap** | **−1.78** | **−11.39** | **−7.99** |
| C1 CC_REGULAR miss (status) | +10.75 | +17.55 | +10.17 |
| CC_CHP + CT_PEAKER + ST_GAS miss | +1.17 | +0.43 | +2.02 |

Monthly gap (model − EIA-930, TWh):

| | J | F | M | A | M | J | J | A | S | O | N | D |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| PNW 2019 | +0.66 | +0.87 | +0.93 | +0.43 | +0.62 | +0.46 | +0.66 | +0.44 | +0.55 | +0.76 | +0.47 | +0.66 |
| DSW 2019 | −2.00 | +0.12 | +0.12 | +0.37 | +0.43 | −0.73 | −0.90 | −1.41 | −1.83 | −0.65 | −0.61 | −2.18 |
| PNW 2020 | +0.50 | +0.49 | +0.59 | +0.58 | +0.10 | −0.17 | −0.37 | +0.03 | +0.60 | +0.42 | +0.32 | +0.66 |
| DSW 2020 | −1.37 | −1.53 | −0.64 | −0.38 | −0.86 | −1.39 | −1.09 | −1.32 | −2.30 | −0.58 | −1.14 | −2.54 |
| PNW 2021 | +0.41 | +0.27 | +0.46 | +0.45 | +0.10 | +0.04 | +0.10 | +0.11 | +0.17 | +0.05 | −0.12 | +0.17 |
| DSW 2021 | −2.89 | −1.49 | −2.03 | −0.62 | +0.26 | −0.37 | −0.74 | −0.52 | −0.80 | −0.01 | −0.05 | −0.95 |

Tranche energy (P1, TWh), 2019 / 2020 / 2021: `PNW_hydro_base` 16.13 / 18.21 / 11.20; `PNW_midC` 0.53 / 2.86 / 4.62;
`export_MALIN` 0.00 all years; `DSW_solar_PV` 18.91 / 17.07 / 12.58; `DSW_overnight_clean` 7.28 / 6.31 / 5.88;
`DSW_CCGT` 5.52 / 2.90 / 1.01; `WECC_scarcity` 3.66 / 0.47 / 0.31; the surplus / daytime / late-evening rungs 0 in
2019–20 and 5.21 / 4.84 / 0.82 in 2021; `export_PALOVRDE` 0.00 all years.

Readings:
1. **The PNW term is what closes 2019, and it closes the import gap rather than the CC gap.** With PNW included,
   2019's net import is within 1.8 TWh of EIA-930. At most ~1.8 of the +10.75 TWh 2019 CC_REGULAR miss is an import
   object, and the "DSW −9.3 vs CC +10.75" pairing in plan §3.7 does not hold. In 2020 and 2021 the import gap
   covers about 65 % and 80 % of the CC miss.
2. **The PNW over-import is the firm block plus a missing export.** `PNW_hydro_base` alone (16.1 TWh in 2019, 11.2 in
   2021) exceeds the measured PNW *net* import (9.15 / 13.60), and the Malin export sink delivers 0 TWh in every fold
   year. EIA-930 nets CAISO's exports to the NW out of the corridor. The +0.4–0.9 TWh/month 2019 excess is flat
   across the year, which is the signature of a firm block and not of the priced tranches. The export-sink family is
   adjudicated R/G (caiso-142/143/167), so this is reported, not proposed.
3. **Where 2019's remaining CC excess sits is a bench-basis question, not a supply one.** Against the EIA-930 CISO
   balance, the 2019 fold leg's total gas (61.2 TWh) is *below* EIA-930 natural gas (65.2), while the C1/C2 bench
   (EIA-923 grid-delivered, CC_REGULAR 36.1, gas family 48.0) sits 17 TWh lower still. Demand is +3.1 TWh over
   EIA-930 and hydro +4.8 (EIA-930's 2019–20 CISO hydro is known incomplete, R-CAISO-7). This is the open
   `EIA930_GAS_FOLD_REFUTED` owner question (R-CAISO-5 §6, R-CAISO-7: the flip raises the 2019–21 targets
   ≈ +5.5 / +3.9 / +2.4 TWh). It is reported here and not re-opened.

Consequence for plan §3.7: the fold's C1 2019 cannot be closed by any DSW import lever, even with the refused OASIS
history. Under R-16 the data route is closed anyway.

## 2. Step 0c: `zonal_gas_basis` 2021 sizing

**The plan's −2.5 pp premise was wrong in construction.** `apply_caiso_zonal_gas_basis` delegates to the shared
**mean-zero capacity-weighted** core (`data/fuel/basis/meanzero.py::_apply_meanzero_zonal_gas_basis`). It does not
move NP15 alone by the PG&E−SoCal differential. It subtracts the gas-pmax-weighted mean basis, so a north discount is
paid for by a south premium. Exact per-unit delta from the double fleet-only rebuild (flag off / on, 2021 fold recipe;
1,408 in-CAISO gas units; the WECC_DSW gas tranches are not in the weighting):

| $/MMBtu | NP15 / ZP26 | LA_BASIN / SDGE / SP15_rest | cap-weighted mean |
|---|--:|--:|--:|
| measured basis vs HH (`caiso_zonal_gas_hub.csv`, 2021) | 0.773 | 1.675 | ≈ 1.265 |
| **applied spread** | **−0.492** | **+0.410** | 0 |
| MC delta ($/MWh, unit mean) | −5.1 / −5.5 | +4.7 / +4.4 / +4.3 | |

First-order Δλ (P0 marginal set, island-coupled; method in the probe docstring), 2021, $/MWh:

| Month | 1 | 2 | 3 | 4 | **5** | **6** | **7** | 8 | **9** | **10** | **11** | **12** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| NP15 | −2.75 | −2.47 | −2.54 | −2.13 | −1.50 | −1.86 | −1.88 | −1.92 | −1.81 | −1.91 | −2.02 | −2.16 |
| LA_BASIN | +2.03 | +2.22 | +1.66 | +1.68 | +1.24 | +1.70 | +1.89 | +1.65 | +1.34 | +1.39 | +0.57 | +0.88 |
| SDGE | +2.21 | +2.42 | +2.00 | +1.75 | +1.49 | +2.14 | +2.48 | +1.91 | +1.46 | +1.57 | +0.84 | +1.15 |
| **load-weighted** | −0.10 | +0.11 | −0.16 | +0.04 | +0.08 | +0.21 | +0.36 | +0.18 | +0.03 | +0.00 | −0.45 | −0.33 |

Bold months are the C3a-gated months (RT coverage ≥ 0.90: May–Jul, Sep–Dec). Gas is marginal in 42–57 % of
load-weighted hours.

- **C3a 2021: Δλ = $0.00/MWh on the gated months → +0.01 pp** (bench RT lw 51.07). Pre-fixed ≥ 2 pp: **FAILS.**
- It does produce the N–S gradient it exists for: NP15 −1.5 to −2.8 $/MWh, south +0.6 to +2.5. That is a fidelity
  case (rule 14: two separately traded citygate hubs over one composite) and a C3b/D-A shape effect. It is not a C3a
  level lever, which is what caiso-221 already said of 2023–25.
- 2024 tripwire (+1.5 pp) and 2025: the spread **reverses sign** in 2024 (north +0.286, south −0.253 $/MMBtu) and is
  small in 2025 (north −0.097, south +0.087). The 2024 first-order reading is in the arm-2 PRECOMMIT §4.
- A non-mean-zero variant, pricing each half at its own citygate *level*, would be a different mechanism. It would
  move the calibrated composite + transport level that R-CAISO-33 (link 15) owns. It is not proposed here.

## 3. Step 0d: census of the 89 C3c-2021 hours

Scorer construction (`render_calibration_html._tail_hours`): an hour counts when the max over **every** zone's P1
dual exceeds $200, over all 8,760 hours. The actual counts RT hub hours > $200 where the RT series exists
(`actual_lmp_hourly_CAISO.parquet`; first RT hour **2021-04-26 23:00**, 5,713 covered hours, 65.2 %).

| | count |
|---|--:|
| model tail hours | **89** |
| … on 2021-02-13 / 14 / 15 / 16 / 17 | 16 / 15 / 24 / 17 / 17 |
| … inside the RT-covered window | **0** |
| … argmax zone NP15 / SDGE / LA_BASIN | 33 / 30 / 26 (all in-CAISO; neither WECC zone) |
| … SDGE-only (SDGE > $200, every other in-CAISO zone ≤ $200) | **0** |
| … with unserved energy (slack > 0) | 0 |
| … price range | $259–448 |
| … attributable to the $180 placeholder | **0** (every tail price is above $259; a $180 rung cannot set a > $200 dual) |
| actual RT hours > $200 | 27 (Jun 3, Jul 8, Sep 10, Oct 3, Nov 2, Dec 1) |
| **model tail hours on the RT-covered hours** | **0** |

**Attribution.** The 89 hours are Winter Storm Uri. The keeper's daily CA-composite gas print
(`gas-prices/caiso_citygate_daily.csv`) reads $9.33 on 2021-02-11, $39.26 on 02-12 (no print 02-13…15, weekend + holiday), $44.27 on 02-16 and
$15.09 on 02-17 (the fleet rebuild logs a winter hub-overlay max of 44.73 $/MMBtu), and the gas stack prices at that measured fuel. The model is pricing a measured input
in a window with no measured price reference. Neither the SDGE LCT cap nor the $180 placeholder is involved.

**The 3.3× "over-fire" is a window mismatch, not a model behaviour.** The scorer counts the model over 8,760 hours
and the actual over 5,713. The coverage note ("count is a lower bound") assumes the missing hours can only add actual
tail hours, but here they also hold every model tail hour. On like-for-like hours the reading inverts: **model 0 vs
actual 27, an under-fire.** The 27 actual hours are summer/autumn evening events. That is the same signature as the
ledgered C3c 2024 (0 vs 35 h, NW import-parity events; R-CAISO-22/26).

**Recommended caveat label** (for the R-10 owner classification, which comes after this census):
- Retire "measured-input limitation (over-fire)".
- C3c 2021 reads **"reference-window mismatch; like-for-like under-fire 0 vs 27 h, same model class as the C3c-2024
  ledger (import-parity scarcity the LP does not price)"**.
- The Feb 2021 gas-spike hours are a **reference gap** (no OASIS print before 2021-04-26, R-16), not evidence about
  the tail.

A scorer-side repair would restrict the model count to the hours where the RT actual exists, the same mask
`_monthly_mae` and C3a's month-coverage gate already apply. It is the like-for-like rule and reads 0 vs 27 for 2021.
Scorer rules belong to the rubric owner. This record recommends; it does not edit `calibration_verdict.py` or the
renderer, and the desk decides whether that repair is a W3 governance item.

## 4. G-DRIFT observation for the wave-1 arms (2025 fleet)

The fleet-only rebuild at HEAD reproduces the keeper unit-for-unit in 2021 (1,633 = 1,633) and 2024 (1,625 = 1,625),
but **not in 2025: HEAD builds 1,632 units against the keeper's 1,710.** That is 83 keeper units absent and 5 hydro
units new. The absent units include CC_REGULAR plants 55853 and 58083 (SP15_rest), ST_GAS 356 (Redondo Beach) and
10446, CT_PEAKER plants 7693, 57714, 7232, 59456, 10110, 50623 and 61027, and plant 50388. Cause: the EIA-860 Final
2025 snapshot landed by #7015 (`39720d35` "Replace the canonical EIA-860 snapshot with the Final 2025 release") and
the storage accreditation re-derive `4284a424`, both after the keeper's basis `cd589798`. These are W0 territory
(plan §2.1). They are **LIVE** for CAISO 2025, so any wave-1 arm solved on HEAD carries a 2025 fleet change that the
incumbent keeper's bundle cannot control for. The PRECOMMITs therefore read every arm against the **post-W0 CAISO
baseline** (§2.1 W0 step 4), not against `rcaiso20_A_span`. The 2025 0c sizing is not computable on HEAD against the
keeper's P0 fleet; the probe refuses it by design.
