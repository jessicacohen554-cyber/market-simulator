# FINDING — UC-BANDS-ERCOT: are ERCOT's offer bands identified for a UC commitment structure?

Lane UC-BANDS-ERCOT (Opus), 2026-10-14, chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`)
on owner decision 8 (2026-10-14). Pin `580c4fbf`; branch `claude/ucmilp-bands-ercot`.
**Zero LP.** No solve, no shard, nothing registered, nothing deleted.
Inputs: the keeper `2026-10-02-closeout-l1-coal-fuel` (`results/calibration/closeout_ercot_l1_span`) and the
uc-1.4 2019 bundle `claude/ucmilp-fix5-ercot-2019` @ `f832aa52`. Arm: keeper + `unit_commitment_milp` +
`ercot_gas_commitment_bridge=false`.
Script and readings: `data/bands/bands_zero_lp.py` → `data/bands/readings_2019.json`.

## 0. Answer

1. **No ERCOT gas band is a clean measured offer, and none is the rule-1 channel.**
   - The keeper's attestation reads `authorized_price_tuning.declared: false`.
   - Its own DOF ledger lists `offer_curve_by_group` as `identification: residual` (107 scalars, ≥ 165 solves).
   - Only the CC_REGULAR / CC_CHP core comes from measured offers: 60-Day DAM, pooled 2023–25.
   - Residual deltas sit on top of that core in every year.
   - In 2019–2023, the peak bands also carry the ×33 carve-out. It was swept against the gates (ercot-235/236).
2. **The identification depends on the commitment structure.** This shows in three places:
   - **The residual layer and ×33 were fitted on bridge-armed keepers.** The bridge was armed in the ERCOT keepers by ERCOT-119 (2026-07-27), a month before the ×33 sweep.
   - **The CC committed anchor is the DAM three-part *Min Gen Cost*.** That is the all-in $/MWh at LSL, no-load included.
     - The base heat rate it multiplies is a measured *average* operating rate, which also contains no-load fuel.
     - The UC adds the CAMPD no-load intercept explicitly on top. Its stated assumption is "start and no-load are explicit".
   - **The ST_GAS and CT_PEAKER committed bands are, by their own source comment, "a P1 startup-cost proxy".**
3. **2019 decomposition (+$5.90/MWh, $49.41 → $55.32):**
   - **The peak-band / scarcity wall is not the residual.** Hours above $200 carry **$0.41 (7 %)**. Ninety of those 111 hours were already above $200 in the keeper. CC peak-tranche energy is 0.002 TWh in both runs.
   - **$5.42 (92 %)** sits in hours where the UC holds ≥ 0.5 GW of CC/ST capacity offline that is offered below the hour's price.
   - The UC holds 4.0 GW of CC and 5.4 GW of ST_GAS offline on average. The keeper's LP could call that capacity in every hour.
   - **The UC's commitment is not below measured:**

     | | UC online fraction | CEMS online fraction |
     |---|---|---|
     | CC | 0.693 | 0.634 |
     | ST_GAS | 0.254 | 0.244 |

   - So the "decommitment" moves toward the measured fleet state, not away from it.
4. **Verdict under the charter's decision rule: branch 2.**
   - The residual is the band surface: it was identified on a structure where all available gas capacity was callable every hour, and it is now exposed by a measured-like commitment. It is not a UC engine defect.
   - A re-derivation from measured SCED offers is proposed in `PRECOMMIT-ucmilp-bands-ercot-2026-10-14.md`, for the owner's ruling.
   - Nothing changes until then.

## 1. Provenance (keeper `run_config_2019`, resolved `offer_curve_by_group`)

Resolution order: generic base (`pipeline/offer_curve_base/generic.py`) → ERCOT fitted base (`offer_curve_base/ercot.py`, "run57 baseline") → `_ERCOT_OFFER_CURVE` phys_* merge (`backcast_config.py`) → recipe `offer_curve_overrides` → recipe `offer_curve_deltas` → `ercot_offer_surface_conditional` peak-ladder split → **partition override 2019–2023** (`meta.config_partition_overrides`, peak bands ×33).

| class · band | 2019 value | source | measured / residual |
|---|---|---|---|
| CC_REGULAR committed | 0.998 | DAM Min-Gen-Cost p50 1.048 (`derive_dam_offer_hrmults.py`, cconly artifact `offer_curve_dam_hrmults_cconly.json`, 2023–25 pooled, HH−0.50 basis) + recipe delta −0.05 | measured core + residual |
| CC_REGULAR econ_low / econ_high | 0.723 / 1.324 | DAM incremental curve p50 0.963 / 1.454 + deltas −0.24 / −0.13 | measured core + residual |
| CC_REGULAR peak | 151.008 (2024–25: 4.576) | DAM top-of-curve, mode B, 4.326 + 0.25; × 33 in 2019–23 | measured core + residual + gate-swept carve-out |
| CC_CHP c / el / eh / peak | 1.029 / 0.946 / 1.857 / 123.684 | DAM cconly 1.029 / 0.946 / 1.427 / 4.248 + deltas (eh +0.43, peak −0.5) and × 33 | same pattern |
| ST_GAS c / el / eh / peak | 0.91 / 1.02 / 1.20 / 105.6 | generic 0.81 / 1.05 / 1.40 / 4.20 (committed: "startup-cost proxy", uncited), ERCOT fit 0.91 / 1.15 / 1.55, deltas 0 / −0.13 / −0.35 / −1.0, × 33 | residual throughout |
| CT_PEAKER c / el / eh / peak | 1.14 / 1.27 / 2.18 / 433.95 | generic 1.55 / 1.27 / 1.98 / 13.15 (committed: "P1 startup-cost proxy"; peak: $5,000-ORDC wall), ERCOT fit c 1.48, deltas c −0.34 / eh +0.2, × 33 | residual throughout |
| phys_* (all classes) | e.g. CC 1.006 / 0.825 / 0.950 | CAMPD marginal-HR p50s (`ercot_campd_marginal_hr_summary.csv`); phys_peak × 33 in 2019–23 | measured; out of scope (charter) |
| econ_low_share, pct_peaking, peak_ladder shares | — | structural shares | out of scope (charter) |

- **The SCED files do not set the static bands.** The `ercot_sced_offer_wall_*` artifacts feed the P1-only conditional-surface markups (`ercot_offer_surface_cleared_share_rt`, `_position_tail`). None of them sets a static band.
- **The ×33 has a record.** It was swept against the gates (ercot-235 grid → ercot-236, min |C3a-2023|; `FINDING-r-ercot-9` §3).
  - The owner held it twice: R-ERCOT-9 ("Hold k=33") and R-51 ("Keep the ×33 keeper").
  - It is one value on 2019–23 and another on 2024–25, so it fails rule 1(b) as a tuning channel. It is also not declared as one.

## 2. Commitment dependence, per band

| band | depends on the commitment structure? | evidence (code / data) |
|---|---|---|
| CC committed | **Yes** | `derive_dam_offer_hrmults.py` docstring: the committed band is "anchored on the three-part Min Gen Cost (the all-in $/MWh price the unit holds at LSL)". `measured_cc_heat_rates` = heatInput ÷ net MWh over steady-state hours (an average rate, no-load included). The UC objective adds `noload_mmbtu_h` (the CAMPD OLS intercept) on top of `mc_base` (`model/uc/params.py::noload_cost_per_unit_h`, DESIGN §1.2). In 2019 that term is **$224.7 M on CC (10.9 % of UC CC energy cost, $1.69/MWh)** and **$52.4 M on ST_GAS (13.5 %, $4.25/MWh)**. The band was identified for a structure with no separate no-load. |
| CC econ_low / econ_high (measured core) | No | Incremental energy-curve points above LSL, read while committed: the quantity a UC's dispatch needs. |
| CC / CC_CHP / ST / CT residual deltas | **Yes** | Ledgered `residual`, fitted against gates on keepers that armed `ercot_gas_commitment_bridge` (bridge forced energy measured in both arms of ERCOT-119, 2026-07-27, `calibration-log/ercot.md` ~L1507). ERCOT-118/119 recorded the coupling directly: cheaper CC econ bands collapse the bridge's forced energy 0.77/1.41/0.97 → 0.20/0.46/0.30 TWh. |
| all peak bands, 2019–23 (× 33) | **Yes** | Swept against the 2023 gates on a bridge-armed keeper (ercot-235/236, 2026-08-25). |
| ST_GAS / CT_PEAKER committed | **Yes, by construction** | `generic.py`: "CT/ST committed band raised as a P1 startup-cost proxy". Start cost is the UC's own explicit term. CT is non-integer under the UC, so its proxy also stacks on the P1 start markup. That stacking already exists in the keeper (rule 19). |

## 3. The 2019 +18.8 % decomposed (zero LP; `readings_2019.json`)

C3a basis: load-weighted P1 price. Keeper $49.41, UC $55.32, **Δ +$5.90/MWh**. Both reproduce the FIX-4 table.

| bucket (UC-arm hour) | hours | Δ contribution $/MWh | share |
|---|---|---|---|
| A. price > $200: scarcity / peak-band wall (90 of the 111 already > $200 in the keeper) | 111 | **+0.41** | 7 % |
| D. ≥ 0.5 GW of UC-offline CC/ST capacity offered below the hour's price | 8,325 | **+5.42** | 92 % |
| E. other | 324 | +0.07 | 1 % |

- **The price lift grows with the capacity held offline.** In bucket D, the mean Δp rises monotonically:

  | UC-offline CC/ST capacity offered below price | mean Δp ($/MWh) |
  |---|---|
  | 0.5–1 GW | +2.3 |
  | 1–2 GW | +3.7 |
  | 2–4 GW | +3.8 |
  | > 4 GW | +6.9 |

- **The same Δ split by channel:**
  - class switch to a dearer class: **+$4.26** (5,917 h). CT_PEAKER marginal unit-hours rise from 325 to 1,042.
  - same class, dearer step: **+$1.23** (2,732 h). In CC→CC hours the marginal offer rises from $31.2 to $35.3.
  - scarcity: +$0.41.
- **Capacity:** the UC holds offline, on average, 4.01 GW of CC_REGULAR and 5.40 GW of ST_GAS. The keeper's LP could dispatch that capacity in any hour.
- **Energy:** CC −8.8 TWh, ST_GAS −1.7, CT +2.2, coal +6.8 (the C1 PASSes in FIX-4).
- **Peak tranches:** CC peak-tranche energy is 0.002 TWh in both runs, so the 151× wall almost never runs.
- **Against CEMS** (cap-weighted online fraction; on = `opTime > 0` and `grossLoad > 0`; coverage 88 % CC / 84 % ST cluster-hours):

  | | UC (all hours) | CEMS (all hours) | UC night | CEMS night | UC day | CEMS day |
  |---|---|---|---|---|---|---|
  | CC | 0.693 | 0.634 | 0.66 | 0.50 | 0.72 | 0.70 |
  | ST_GAS | 0.254 | 0.244 | | | | |

  The UC over-commits CC at night. The ST_GAS hour-of-day shapes match.

**Read.**
- **The wall is not the residual.** FIX-4 §6.3's "peak-band scarcity wall" is bounded at ≤ $0.41 (7 %), and the keeper shares most of those hours.
- **The UC's decommitment is not the defect either.** Relative to the keeper it removes ~9.4 GW of gas capacity that the LP treated as always callable. That moves commitment to, or slightly above, the CEMS-measured level.
- **What remains is the band surface.** It was fitted against gates on a structure with all available gas capacity callable every hour, plus the bridge floors. Under measured-like commitment, the same bands put CT and the upper CC/ST steps on the margin more often.
- **Limit.** This is an accounting association, not a counterfactual. Separating "bands" from "commitment" causally needs a solve.

**Engine note (routed, not this lane's).** The no-load double count in §2 pushes the UC toward decommitment. It cannot be the cause of the 2019 gap, because UC CC commitment already exceeds CEMS. It is still a cost-basis inconsistency, and it also inflates `uc_uplift`'s cost side. Two forms of the fix are possible:
- price integer clusters' energy on the incremental (OLS slope) basis;
- or drop the explicit no-load while the bands stay all-in.

Rule 19 says one place only.

## 4. Matrix

No mechanism was tested, so no cell moves. `offer_curve_by_group` (K) and `unit_commitment_milp` (R) keep their verdicts. If phase 1 is ruled in, its result writes the cells.

## Log entry

- 2026-10-14 · UC-BANDS-ERCOT · `claude/ucmilp-bands-ercot` · zero LP.
  - Bands are ledgered residual; not the rule-1 channel; commitment-dependent: CC committed via the Min-Gen-Cost / no-load basis, all deltas and the ×33 via bridge-era gate fitting, CT/ST committed as startup proxies.
  - 2019 Δ +$5.90: 7 % > $200 hours, 92 % hours with UC-offline cheap capacity. UC online fraction CC 0.693 / ST 0.254 vs CEMS 0.634 / 0.244.
  - PRECOMMIT for a measured SCED re-derivation filed for owner ruling.
