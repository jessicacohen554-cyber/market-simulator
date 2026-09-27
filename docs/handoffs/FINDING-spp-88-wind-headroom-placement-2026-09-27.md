# FINDING — SPP-88 Card B: the wind excess is NOT a CF-level input defect. It is curtailment the model does not perform, and its counterpart is the known gas low-side.

**Lane** SPP-88 · **ZERO LP** · keeper `2026-09-26-spp-86-coal-extract` (bundle `results/calibration/spp86_arm_span`,
basis_sha `d72e5f10`) · probe `scripts/probes/_spp88_wind_headroom_placement.py` · nothing solved, nothing registered,
keeper unchanged, no promotion question (rule 31).

## 1. Question and why it is new evidence

SPP-67 showed the excess over EIA-930 is 100 % CF LEVEL: the ISO wind bound is `EIA-930 delivered_h × 1/(1−r)` in
**every** hour, so capacity and shape both cancel. SPP-68 then rejected an ex-ante ceiling that removed the headroom.
Neither lane measured **where in the year** the unspent headroom sits. If it sat in hours with no curtailment signal, the
flat gross-up would be putting phantom energy into hours SPP never curtailed. That would be an input-placement defect,
fixable as a measured input under rule 13. This probe tests that hypothesis.

## 2. Result: the placement hypothesis is FALSIFIED

Wind excess (model − EIA-930, TWh), bucketed by the **actual** RT hub LMP (the lower of the two hubs):

| year | excess | actual < $0 | $0–15 | $15–30 | ≥ $30 | **no signal** (≥ $15, no North MCC < −$10) | neg hours: actual / model |
|---|---|---|---|---|---|---|---|
| 2019 | 1.22 | 0.71 | 0.69 | −0.01 | −0.18 | −0.19 | 862 / 22 |
| 2020 | 8.08 | 4.31 | 3.69 | 0.14 | −0.06 | 0.07 | 1347 / 447 |
| 2021 | 8.03 | 4.98 | 2.85 | 0.23 | −0.05 | 0.06 | 1750 / 758 |
| 2022 | 9.17 | 5.16 | 3.01 | 1.12 | −0.12 | 0.48 | 1634 / 692 |
| 2023 | 8.40 | 4.51 | 3.31 | 0.69 | −0.12 | 0.46 | 1506 / 588 |
| 2024 | 11.44 | 6.28 | 4.29 | 0.88 | −0.03 | 0.75 | 1903 / 686 |
| 2025 | 10.93 | 6.14 | 3.69 | 1.19 | −0.10 | 0.97 | 1637 / 584 |

- **86–99 % of the excess falls in hours when SPP's actual price was below $15/MWh.** Those are the hours SPP really
  curtailed. Hours with no curtailment signal hold **−0.19 to +0.97 TWh**. The gross-up puts headroom where the
  curtailment was.
- **In actual negative-price hours the model's median price is +$14.7 to +$19.4/MWh.** It does not reach the wind offer,
  so it never curtails.
- Capacity online by month (EIA-860 COD/retirements/repowers) and the SPP-West vs RTO boundary cannot move the excess:
  capacity cancels in the bound (SPP-67 §2), and the delivered leg is EIA-930 itself.

## 3. What the extra wind displaces: GAS, in the same hours

Model minus EIA-930, TWh, over the same buckets:

| year | gas < $0 | gas $0–15 | coal < $0 | coal $0–15 |
|---|---|---|---|---|
| 2020 | −2.46 | +0.32 | −1.65 | −4.26 |
| 2021 | −4.19 | −5.01 | −0.75 | +1.89 |
| 2022 | −4.28 | −4.24 | −0.83 | +1.12 |
| 2023 | −3.83 | −2.94 | −0.64 | −0.48 |
| 2024 | −5.19 | −3.72 | −0.69 | −0.41 |
| 2025 | −5.40 | −4.75 | −0.37 | +1.23 |

In 2021–2025 the gas deficit in hours below $15 (7.0–10.2 TWh) is about the same size as the wind excess there
(7.8–10.6 TWh). This is the object SPP-74/75/77 already measured: part-loaded utility CC and ST_GAS units stay online
through low-price hours under DA commitment. SPP's measured gas is 3.3–6.0 GW in RT < 0 hours; the model has 0.9–3.2 GW.
SPP-77 found **no admissible, forward-reproducible driver** for it and routed it as model-class (MIP-horizon commitment).
SPP-44 / SPP-66 reject the P0-anchored bridge and net-load window forms.

One exception. In **2021–2022**, gas is short and coal long in **every** price bucket, including ≥ $30 (2022: gas −6.14,
coal +4.56 TWh). That is the high-gas-price coal/CC merit-order swap SPP-75 named, and it is **why CC_REGULAR 2021/22
fails on every basis** (SPP-87). It is a separate object from the low-price curtailment.

## 4. Verdict and routing

- **Card B closes at phase 0 with no admissible input change.** The bound's level and its placement are right. The
  excess is the downstream symptom of too little inflexible gas in low-price hours. Removing wind ex ante is SPP-68's
  refuted form. It also deletes the negative-price signal, and SPP-71 proved an upper limit on wind leaves wind
  non-marginal.
- **No re-test** of `spp_curtailment_ceiling` (R), `spp_gas_commitment_bridge` (R) or `vre_reference_rate_year_own` (K)
  follows from this. The re-open condition is still SPP-77's: a measured, forward-reproducible gas commitment-state
  driver.
- **Next cards, unchanged:** Card D (the EIA-930 vs EIA-923 gas gap, 2.5–3.4 TWh) and Card C (Harrington 6193 D-4).
  Add a successor for the 2021–22 all-hours coal/CC swap (merit order under high gas prices). Do not tune the offer
  multipliers (0.93, rule 1(c)).
- **Owner ruling recorded this session (SPP-87 §6 Q1):** *measure the gross/net coal alignment in every ISO before any
  rubric change.* That is a zero-LP successor. No scorer change lands.

## 5. Housekeeping (checked 2026-09-27)

- `git ls-remote --heads origin | grep -i spp` finds only this lane's branch. The leftover refs SPP-87 named
  (`claude/rspp-2019…2025`, `claude/spp85-*`, `claude/spp86-*`) are **already gone**, so nothing is owed.
- No open PR touches SPP. Nothing needed salvaging.
