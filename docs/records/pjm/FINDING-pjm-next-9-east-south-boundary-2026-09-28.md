# FINDING — PJM-NEXT-9 cards 1–2 phase 0: the missing east→south boundary is the Peach Bottom / Conastone corridor (zero LP), 2026-09-28

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`). **Zero LP; no model input changed.**
**Probe** `scripts/probes/_pjmnext9_congestion_boundary.py` → `results/phase0/pjm/_pjmnext9_congestion_boundary.json`.
**Inputs:** PJM DataMiner2 `da_marginal_value` 2019–2025 (re-fetched with `scripts/data/fetch_pjm_binding_constraints.py`; gitignored, `SHA256SUMS.txt` rewritten) and DA hub LMP components (`data/clean/lmp/PJM/DAM`).

## 1. Method

A hub's DA congestion component is linear in the binding constraints' shadow prices, `MCC_hub,t = Σ_k β_k μ_k,t`, where β_k is the hub's (negated) shift factor on constraint k. PJM does not publish shift factors, so β is recovered by least squares per year, fitting each hub **spread** on the top 250 constraints by rent (85–92 % of all rent). Each constraint's contribution to the spread is `β_k · mean(μ_k)`. The corridor is the facility set named by the 2023 ranking: NOTTINGH / GRACETON / CONASTON / Yorkana / PEACHBOT / SAFEHARB.

## 2. Result: one corridor sets the east–south spread in every year

| year | NJ − Western DA congestion ($/MWh) | fit R² | corridor share | top facility |
|---|---|---|---|---|
| 2019 | −2.82 | 0.97 | 85 % | Conastone 500 kV CNS-PEA |
| 2020 | −2.72 | 0.94 | 35 % (+ Bagley–Graceton, also BGE border) | Bagley 230 kV BAG-GRA |
| 2021 | −6.00 | 0.96 | 42 % (+ TMI 500 kV bank) | Nottingham 230 kV 2-3 |
| 2022 | −8.87 | 0.94 | 79 % | Nottingham 230 kV 2-3 |
| **2023** | **−8.09** | **0.98** | **91 %** | **Nottingham 230 kV 2-3** |
| 2024 | −6.16 | 0.95 | 69 % | Nottingham 230 kV 2-3 |
| 2025 | −8.06 | 0.90 | 60 % | Nottingham 230 kV 2-3 |

- **2023:** Nottingham 230 kV 2-3, for the loss of Conastone–Peach Bottom 500 kV 5012, binds in **5,341 h** (61 %) at a mean of −$34/MWh. It alone contributes **−3.7 of the −8.1 $/MWh** NJ discount. Graceton–Safe Harbor 230 and Conastone–Northwest 230 add most of the rest.
- **Physically:** the corridor limits flow **south** from the PECO/PPL (Peach Bottom, Safe Harbor) nuclear-hydro-gas cluster into BGE (Conastone), i.e. into model **EMAAC / Central_PA → SWMAAC**. It prices everything north of it down (NJ, Eastern hub) and everything south of it up.
- **Model network:** EMAAC↔SWMAAC is a static 5,000 MW link that never binds, and **there is no Central_PA↔SWMAAC link at all**. So the model cannot produce this separation: EMAAC rides the system price (FINDING-pjm-next-8 §5).

## 3. Card 2: 2019 CC_REGULAR is the same object

Model − EIA-923, CC_REGULAR bench plants, TWh (registered keeper payload):

| zone | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| EMAAC | **+11.2** | +6.7 | +4.3 | +2.7 | **+9.0** | −1.4 | −9.4 |
| Central_PA | **+7.8** | +7.1 | +3.7 | +7.1 | +5.1 | +4.4 | +2.2 |
| ComEd | +1.4 | +2.2 | +2.5 | +4.2 | +5.5 | +5.0 | +5.7 |
| SWMAAC | −3.7 | −3.5 | −3.8 | −1.9 | +0.5 | −4.3 | −4.3 |
| Dominion | **−8.4** | −4.7 | −8.4 | −2.8 | **−12.7** | −4.1 | −1.5 |
| net | +11.0 | +14.2 | +1.0 | +11.3 | +8.3 | −0.6 | −7.9 |

Every failing CC_REGULAR year (2019/2020/2022/2023) has the same signature: too much CC north of the corridor and too little south of it. 2019 is not a separate 2019-specific input; card 1 covers it.

## 4. Is there a measured operand (rule 14)? No limit is published.

- **Not in the transfer-limit feed.** The feed posts 10 series (AP-South, Bedington–BlackOak, AEP/DOM, 5004/5005, Average W/C/E, Cleveland). BC/PEPCO is a Manual-03 interface that is **not posted** (already recorded in `DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md` §10).
- **The binding element is a single 230 kV facility.** Its thermal rating is a TO rating, not a zonal transfer limit. Converting it to a zonal cap would need the facility's base flow from intra-zonal dispatch, which the 8-zone model does not have. Shift factors could be measured (zonal LMP congestion regressed on μ, as here), but the **limit** could only be backed out of binding frequency or prices. That is fitting to an outcome (rules 1/13): **refused**.
- **SWMAAC CETL** (published, in the capacity-deliverability data) is an emergency planning import limit on all SWMAAC imports, including AP-South. It is a different quantity and boundary, and misaligned under rule 14. Not recommended.
- **Published RTEP record** (web search, 2026-09-28): PJM treats the Peach Bottom–Conastone corridor as a facility-deliverability problem with baseline upgrades (Peach Bottom North, Conastone capacitors/statcoms, Bramah substation). It publishes no MW interface limit.

## 5. Verdict

The east→south separation is a **sub-zonal facility constraint with no published zonal limit**. It is the same class as the ERCOT/MISO `internal_congestion_split` refutation (missing epochs are sub-zonal 138–230 kV elements). With committed or public data it is **identifiable** (facility, direction, hours, $ contribution) but **not buildable** without a fitted limit. It explains CC_REGULAR 2019/2020/2022/2023, C3a signs in 2019/2020/2022, and the every-year Central_PA/ComEd over and Dominion under. The owner decides whether to treat it as a model-class limit (decision card).
