# FINDING — closeout-ERCOT-ECRS phase 0: the 2023 ECRS config (owner ruling R-39)

Lane `closeout-ERCOT-ecrs`, branch `claude/closeout-ercot-ecrs`. Zero LP: nothing solved, armed or registered.
Owner ruling R-39 (2026-10-03, verbatim): *"I want you to design a config that does a unique config for 2023 bc of ECRS since it was different in 2023 vs 24 and 25 so the model reflects the market reality."*
Keeper: `2026-10-02-closeout-l1-coal-fuel` (bundle `results/calibration/closeout_ercot_l1_span`, legs at `106d6bb7`).
Probe: `scripts/probes/_closeout_ecrs_static_reclear.py`. The pre-fixed bar is in the probe header, committed at `37b37012` before the probe ran. Output: `results/phase0/ercot/closeout_ecrs_static_reclear.json`.

## 0. Answer

1. **The structural 2023 ECRS mechanism is already in the keeper, and it is already date-keyed to 2023.**
   - `ercot_ecrs_conservative_deployment`: ECRS is withheld from energy at VOLL for the whole of 2023, with no price-based release. The release reform comes in 2024 at h5088 (2024-08-01).
   - The withheld quantity is the measured ASPLANNP433 hourly ECRS plan. The data starts it at go-live (h3839, 2023-06-10).
   - `ercot_nonreleasable_as_withholding` keeps RRS and Reg-Up rigid until RTC+B.
   - ercot-217 adjudicated that this regime split already exists and is armed.
   - So the R-39 sequestration and deployment rule add **zero new LP content**.
2. **The design's one new element is refuted by ERCOT's own published series.** That element is "the online reserve the ORDC sees falls by the sequestered MW."
   - The published ORDC curve on **gross** RTOLCAP, with ECRS counted, reproduces ERCOT's published 2023 RTORPA.
   - The curve on RTOLCAP **net of ECRS** produces 21× the published adder (§3).
   - The 2023 tail was formed in SCED λ, not in the adder (RESEARCH-ercot218b §1: λ ≥ 0.8×RT in 162 of 181 tail hours).
   - On the static estimate the element *would* clear the bar (+6.3 %, C3b 0.273), but it gets there by printing an adder ERCOT never printed. Rule 1 forbids that ("never reach a number through a mechanism that is not real"), and rule 14 forbids rejecting the measured RTOLCAP definition.
   - The code already flags it as a rule-19 double count: `reserves/spec.py` notes that `ercot_ecrs_requirement` is NOT applied to the ORDC-total family because "adding it would double-count the ECRS demand".
   - **Killed at phase 0. No shard.**
3. **What the R-39 config can honestly be:** the keeper's own 2023 config with the ×33 peak bands removed (§4, option A).
   - Those bands are not an ECRS representation. They also sit on the 2019–22 pre-ECRS validation legs.
   - They were selected in ercot-236 by minimising |C3a-2023| over k ∈ {24, 27, 30, 33}. That is a gate-swept value, outside the rule-1 channel, and it also scales `phys_peak`.
   - Removing them leaves 2023 represented by its real mechanism: the armed, date-keyed ECRS sequestration. C3a and C3b are then reported at full structural magnitude under the R-6 configuration-exception caveat.

## 1(a). What the 2023 carve-out carries today, field by field (`run_config_2023.json` vs `run_config_2024.json`)

| field | 2023 | 2024–25 (forward) | kind |
|---|---|---|---|
| `offer_curve_by_group.<G>.peak` for CC_CHP / CC_INTERMEDIATE / CC_REGULAR / CT_CHP / CT_INTERMEDIATE / CT_PEAKER / ST_GAS / ST_GAS_INTERMEDIATE | ×33 forward (e.g. CT_PEAKER 433.95 vs 13.15; CC_REGULAR 151.008 vs 4.576) | forward | **tuned band**, residual-identified (ercot-236 §4: min \|C3a-2023\| over k) |
| `<G>.peak_ladder` (CC_CHP, CC_REGULAR, CT_PEAKER, ST_GAS) | ×33 | forward | **tuned band** |
| `<G>.phys_peak` (CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, ST_GAS) | ×33 (e.g. 33.0 vs 1.0) | forward | **tuned `phys_*`**: outside even the rule-1 channel |
| `ercot_offer_swcap_clip` | true | false | structural: the protocol SWCAP offer cap; inert below the cap (ercot-236 V-0). It is also the R-6 caveat's `config_signature`. |
| `ercot_zonal_spread_ep_referenced` | false | true | structural repair (ercot-255) not carried into 2023. Out of R-39 scope; flagged. |
| `CC_REGULAR.econ_high`, `ST_GAS.econ_high` | 1.324 / 1.2 | same to float noise | none |
| `gas_price_override`, `weather_year`, `years` | measured per year | — | measured |

Everything else is identical to 2024 and 2025, including the whole AS and ORDC stack. Measured inputs: the ASPLANNP433 per-product plan, published ORDC μ/σ, RTORDPA, the LR credit and the RTOLCAP supply cap.

## 1(b). Measured 2023 ECRS facts

- **Procurement.** The ASPLANNP433 ECRS plan is on disk for 2022–2026. Its 2023 onset is h3839 (2023-06-10, market notice M-D050523-01). The mean is 1,925 MW over Jun 10–Dec, and 2,041–2,127 MW in Jun–Sep.
  - 2023 DAM-cleared ECRS equals the plan in all 8,760 h (ercot-227 F1c, measured from the 60-Day DAM).
  - The 2_DAY_AS_DISCLOSURE ECRSM/ECRSS parquets on disk are **2026 only**. 2023 is not needed, because cleared equals plan.
- **Deployment rule.** There was no price-based SCED release until 2024-08-01. The ERCOT operating-procedure change followed the PUCT's 2024-07-25 rejection of the NPRR1224 $750 floor. Before that date ECRS deployed only manually or automatically at < 59.91 Hz or on 10-minute net-load insufficiency. Constants `ERCOT_ECRS_RELEASE_REFORM_*`. RTC+B went live 2025-12-05.
- **Dec-2023 methodology change.** The OBDRR048 multi-step RTORPA floor took effect 2023-11-01 (`floor_active_mask`), and it is armed. No separate December ECRS rule change is carried in any committed source, and none was needed for the test below.
- **ORDC counting.** In ERCOT's published RTOLCAP, every online Resource's capacity counts, including capacity carrying AS responsibility. §3 confirms this from the data.
- **IMM.** SOM 2023 §II.H: ECRS sequestration "doubled" Jun–Dec RT prices, at more than $12 B through November. The ECRS-neutral load-weighted counterfactual is about $35 against the actual $62–65.
  - Plan §4 row 19 (the monthly "simulated correction" bars, SOM 2023 Fig. 13 / 2024 Fig. 11) is **not digitized on disk**. The verdict does not depend on it.

## 1(c). The rule-13 / rule-19 census of the briefed design

- **Rule 13.** ECRS procurement MW and the deployment rule are published operating-condition inputs, and the forward analogue is the year's AS plan. That half is admissible, **and it is already armed.** The ORDC-quantity half is a statement about how ERCOT computed RTORPA, so it is testable against the measured series, and it fails that test (§3).
- **Rule 19.** These mechanisms already floor or add price in the 2023 ECRS hours:
  1. `ercot_ordc_total_reserve` with the R-ERCOT-24b published curve. It counts ECRS MW toward total reserve, as RTOLCAP does.
  2. The `ECRS_withheld` rigid VOLL family (`ercot_ecrs_conservative_deployment`).
  3. The `RRS_withheld` and `RegUp_withheld` rigid families.
  4. The measured RTORDPA overlay (mean $0.75).
  5. The adaptive-expectation conduct layer (`ercot_storage_adaptive_expectation`, K).
  6. The ×33 peak bands.
  7. The SWCAP clip.
- The design would have replaced item 6. Its ORDC element would have stacked a second ECRS demand on top of items 1 and 2, which is the double count the code already names.

## 1(d). Static re-clear (pre-fixed bar: C3a ≥ −12.35 % [model ≥ $57.00] and C3b ≤ 0.30)

The design's ORDC element is ΔRTORPA = published curve at (R − ECRS plan) minus the curve at R. It is added to every zone-hour of the keeper's 2023 P1 price and scored with the repo's own C3a/C3b scorers. The harness reproduces the keeper exactly: C3a −24.7 % ($48.98 vs $65.02), C3b 0.393.

| reserve basis | baseline adder reproduces keeper's realized $1.64? | Δ adder mean (Jun 10–Dec) | hours Δ > $100 | C3a 2023 | C3b 2023 |
|---|---|---|---|---|---|
| measured RTOLCAP + RTOFFCAP (NP6-905) | **yes** ($0.81) | $13.41 ($23.88) | 173 | **+6.3 %** ($69.09) | **0.273** |
| model's own ORDC-total held MW | **no** ($24.05; the held MW is censored at the requirement) | $174.69 | 2,220 | +334 % | 5.156 |

On the admissible basis, with the ×33 bands kept (an upper bound), the numbers clear the bar. Removing the bands, as R-39 asks, lowers that. **The bar is moot**, because the element fails identification first (§3).

## 3. Identification: which basis did ERCOT's 2023 RTORPA form on? (decisive)

| window | published RTORPA mean | curve on GROSS RTOLCAP (ECRS counted) | curve NET of ECRS | hours > $100: published / gross / net |
|---|---|---|---|---|
| 2023 | $0.95 | $0.81 (RMSE 4.9) | $14.22 (RMSE 126.4) | 17 / 17 / 179 |
| ECRS live (h3839 on) | $1.18 | $1.13 (RMSE 6.2) | **$25.01** (RMSE 168.7) | 12 / 14 / **176** |
| pre-ECRS | $0.64 | $0.38 | $0.38 (identical) | 5 / 3 / 3 |

- ERCOT's published adder is the gross-basis curve, hour for hour.
- RTOLCAP *rose* at go-live: May 10,621 MW → Jun 10–30 14,166 MW → Jul 14,363 MW, while ECRS was 2,041–2,072 MW. ERCOT did not net ECRS out of the ORDC reserve.
- A model whose ORDC sees reserves net of ECRS prints an adder about 21× the published one and adds about 165 hours above $100 that ERCOT never had. That is the ercot-219 manufactured-shortage signature from the adder side, and it lands on the `ercot_artificial_shortage_pricing` R cell's DO-NOT-REDO.

**Verdict: the ORDC-net-of-ECRS element is KILLED AT CENSUS** under rule 14 and rule 1, with rule 19 as the code-documented double count. No field is built and no shard is launched.

## 4. Mechanism-matrix cells touching ECRS / ORDC / reserve co-opt / scarcity / AS (ERCOT shard; prior R cells named)

| cell | verdict | relevance |
|---|---|---|
| `ercot_multiproduct_as` (legs: `ercot_ecrs_conservative_deployment`, `ercot_nonreleasable_as_withholding`, `ercot_ecrs_requirement`, `ercot_ordc_total_reserve`, LR credit, RTOLCAP cap) | K | the armed ECRS stack. This lane's note lands here (ORDC-net-of-ECRS leg killed at census). |
| `energy_reserve_coopt` | K | parent co-opt |
| `ercot_ordc_published_curve` | K | R-ERCOT-24b, promoted. Not retuned. |
| `ercot_rtordpa_overlay` | K | measured reliability-deployment adder |
| `ercot_swcap_vintage` / `ercot_swcap_effective_hourly` | K / K | cap vintage |
| `ercot_offer_swcap_clip` | K | 2023 carve-out guard; the R-6 caveat signature |
| `ercot_storage_adaptive_expectation` | K | conduct layer |
| `offer_curve_by_group` | K | holds the ×33 2023/2019–22 bands |
| **`ercot_artificial_shortage_pricing`** | **R** (ercot-219) | prior R: manufactured shortage, G-SPUR/G-SHED. The killed element is the same phenomenon priced through the adder. |
| **`ercot_as_held_location`** | **R** (ercot-226) | prior R: AS held-location. 2023 sequestration channel closed as mis-located. |
| `ercot_as_held_requirement` | I (ercot-227) | held-depth null: procurement never exceeded the plan |
| **`ordc_scarcity_overlay`** | **R** (ERCOT-97) | prior R: post-solve scarcity overlay |
| **`ercot_ruc_commitment_floor`** | **R** | prior R: RUC floor |
| **`energy_online_capability_cap`** | **R** (ercot-159/244) | prior R: aggregate online cap, DO-NOT-REDO |
| **`online_capacity_envelope`** | **R** | prior R |
| `reserve_family_dual_sidecar` / `reserve_family_sidecar` | I / I | diagnostics |
| `dynamic_reserve_requirements` | U | not ERCOT-relevant here |
| `capacity_screen_scarcity_restoration` / `entry_forward_reserve_leg` | O / O | forecast-side |

No R, I or G cell is re-tested here. The briefed element is a new leg, killed on new measured evidence (§3) without a solve.

## 5. Recommendation → card

Option A: 2023 config = keeper 2023 config with the ×33 bands set to the forward values. It is one 2023 shard at `106d6bb7`, so no G-DRIFT applies, and a single-SHA compose. See `PRECOMMIT-closeout-ercot-ecrs-2023-structural-2026-10-03.md`.
