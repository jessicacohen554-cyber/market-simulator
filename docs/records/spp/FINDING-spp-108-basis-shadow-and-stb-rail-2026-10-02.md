# FINDING: SPP-108, the 2021–22 COAL_PRB over-count / CC under-count: basis shadow score and the STB rail retest (zero LP, 2026-10-02)

Lane: SPP-108, chartered by the owner's SPP-107 card "Coal 21–22 over-count (Rec.)". Close-out plan §3.4, steps 0a and 3.
Keeper: `2026-10-02-spp-107-mmu-repair`, bundle `results/calibration/spp107EXR_span`. It is **unchanged**.
Base: `origin/main` `0a28fedf`. **No LP was solved, no shard launched, no bundle produced, nothing registered.**

Probes:
- `scripts/probes/_spp108_basis_shadow.py` → `results/phase0/spp/_spp108_basis_shadow.json`
- `scripts/probes/_spp108_stb_rail_remeasure.py` → `results/phase0/spp/_spp108_stb_rail_remeasure.json`

New intake: `data/raw/stb-ep724/`, the STB EP 724 consolidated workbook through 2026-09-30, fetched by this session on the owner's card "Fetch it yourself". It is curated as `stb-coal-loadings` (Category 9) with reader `market_sim.data.stb_ep724`.

## 0. Headline

1. **Step 0a, basis.** The PRB over-count is mostly benchmark basis; the CC under-count is mostly dispatch.
   - On the SPP-87 CEMS-gross coal basis, COAL_PRB 2021 goes +11.37 → **+3.97** TWh and 2022 goes +10.92 → **+3.59**. Both are PASS. Basis is about 7.4 / 7.3 TWh of each year's PRB miss.
   - The SPP-88 gas-coverage term is now only **0.77 / 0.97 TWh** in 2021 / 22. SPP-100's CHP scope already took most of SPP-88's raw 2.7–5.1.
   - CC_REGULAR 2021 is −8.52 committed, **−8.03** with the coverage term spread pro rata (still FAIL against ±7.98), −7.75 only if all of it goes to CC, and −8.52 if CHP takes it first. The pre-fixed reading "CC 2021 ≥ −8.0" is **not met** in the central case.
   - CC 2022 FAILs on every basis (−8.3 to −9.3).
   - Side effect: COAL_PRB 2020 moves PASS → FAIL on the gross basis (−9.08).
   - Train tier: **0 status moves**. 2025 PRB goes +7.96 → +5.03.
2. **Owner ruling (card W5 / D-P3, 2026-10-02): "Hold; measure all ISOs."** No SPP-only rubric change. The successor is a zero-LP census across all ISOs: gross/net coal, gas coverage and coverage breaks. Until then C1 stays on the committed basis.
3. **Step 3, rail retest.** The STB series identifies the 2022 object, but no zero-parameter mechanism keyed to it binds physically.
   - PRB unit-train loadings / plan (BNSF + UP), relative to the mean of the prior two years: 2021 **1.007**, 2022 **0.856**, 2023 1.052, 2024 1.093, 2025 1.034.
   - 2022 sits outside the other years' range and 2021 does not. Spearman ρ against the MMU coal markup is −0.70. **The identification SPP-44 could not get from EIA-923 tonnage, this series gives.**
   - The RR502 opportunity cost is the shadow value of an energy limit. Its zero-parameter physical form is a cumulative inventory: opening stock + lagged deliveries × STB anomaly, never below zero.
   - At fleet level it **never binds**. In 2022 it bottoms at 0.24 Mt, about 1.7 days of burn.
   - Per plant it binds, but almost entirely through the lagged-delivery cap, and measured deliveries contradict that cap. At the binding plants actual receipts were **1.34× / 1.21× / 1.17×** the lagged rate in 2021 / 22 / 25. In 2021 and 2025 those same plants generated **more** than the model (30.9 vs 29.4 TWh; 14.6 vs 10.6 TWh).
   - So the cap is not physical (the SPP-44 §4 artifact class; rule 1). A non-zero adder needs a safety-stock or conservation parameter, which rule 21 refuses.
   - **No lever survives zero LP. No PRECOMMIT, no field, no shards.**
4. The residual is ledgered under plan step 5 (§4).

## 1. Step 0a: C1 shadow score (model − bench, TWh; band ±min(max(2 % load, 3 % gen), 8); scored with the scorer's own `score_fuelmix`)

| year | row | committed | gross coal (SPP-87) | + coverage pro rata | + coverage all on CC | + coverage CHP first |
|---|---|---|---|---|---|---|
| 2020 | COAL_PRB | −2.25 PASS | −9.08 **FAIL** | −9.08 FAIL | −9.08 FAIL | −9.08 FAIL |
| 2021 | COAL_PRB | +11.37 FAIL | **+3.97 PASS** | +3.97 PASS | +3.97 PASS | +3.97 PASS |
| 2021 | CC_REGULAR | −8.52 FAIL | −8.52 FAIL | −8.03 FAIL | **−7.75 PASS** | −8.52 FAIL |
| 2022 | COAL_PRB | +10.92 FAIL | **+3.59 PASS** | +3.59 PASS | +3.59 PASS | +3.59 PASS |
| 2022 | CC_REGULAR | −9.29 FAIL | −9.29 FAIL | −8.72 FAIL | −8.32 FAIL | −9.29 FAIL |
| 2023 | COAL_PRB | +1.08 | −3.14 | −3.14 | −3.14 | −3.14 |
| 2024 | COAL_PRB | +1.35 | −2.84 | −2.84 | −2.84 | −2.84 |
| 2025 | COAL_PRB | +7.96 | +5.03 | +5.03 | +5.03 | +5.03 |

Gas-coverage term (scorer gas bench − EIA-930 SWPP gas), 2019–2025: +2.54 / +1.10 / +0.77 / +0.97 / −0.40 / −1.98 / −1.01 TWh.

Family view on the 930 / CEMS basis:

| year | coal (model − CEMS gross) | gas (model − 930) | wind (model − 930) |
|---|---|---|---|
| 2021 | +3.8 | −11.4 | +5.2 |
| 2022 | +4.1 | −16.2 | +9.1 |

The gas deficit's counterparts are wind and coal together, as SPP-87 found. Coal on the aligned basis is no longer the dominant term.

## 2. Step 3: STB EP 724 re-measure

**Series.** Category 9, PRB, BNSF + UP summed, annual (actual / plan):

| | 2019 | 2020 | 2021 | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| BNSF | 0.816 | 0.906 | 0.881 | **0.778** | 0.881 | 0.894 | 0.912 |
| UP | 0.864 | 0.957 | 0.883 | **0.752** | 0.855 | 0.894 | 0.911 |
| weeks < 0.90 (BNSF / UP) | 40 / 29 | 21 / 11 | 28 / 30 | **52 / 49** | 26 / 33 | 24 / 28 | 22 / 24 |

2019 is also low; that is the spring 2019 Missouri River floods. 2019 cannot be scored on the inventory leg because there is no 2017 stock vintage.

**Identification against SPP-44's target, the MMU coal markup in $/MWh** (2021–25: 6.02 / 21.12 / 6.88 / 4.29 / 5.81). The anomaly is 0.856 in 2022 against [1.007, 1.093] in the other years: **outside**. ρ = −0.70.

**Binding test.** Cumulative inventory against the keeper's own burn. Deficit is in TWh; plants binding in brackets.

| year | fleet, STB-scaled: min stock | per plant, lagged only (net / gross conv.) | per plant, STB-scaled (net / gross) | STB increment |
|---|---|---|---|---|
| 2020 | 15.2 Mt (151 d) | 0 / 0 | 0 / 0 | 0 |
| 2021 | 5.6 Mt (40 d) | 5.32 [9] / 7.25 [10] | 5.59 / 7.50 | +0.25 |
| 2022 | **0.24 Mt (1.7 d)** | 3.63 [12] / 3.56 [11] | 7.29 [20] / 6.08 [15] | **+2.5 to +3.7** |
| 2023 | 11.6 Mt (111 d) | 0.09 / 0 | 0.25 / 0.01 | ≤ 0.16 |
| 2024 | 20.0 Mt (219 d) | 0 / 0 | 0 / 0 | 0 |
| 2025 | 14.4 Mt (120 d) | 0.85 / 1.84 | 0.87 / 1.85 | ≤ 0.02 |

**Forbidden comparator** (rule 13: diagnostic only, never an input), at the plants where the lagged cap binds:

| year | actual receipts / lagged rate | model TWh | actual net TWh |
|---|---|---|---|
| 2021 | **1.335** | 29.43 | **30.88** |
| 2022 | **1.205** | 26.18 | 23.54 |
| 2025 | **1.166** | 10.63 | **14.64** |

**Reading.**
- The lagged delivery rate is not a physical ceiling: deliveries flex above it whenever plants burn more. The per-plant leg binds hardest in 2021, a year with no rail anomaly, and at plants the model actually **under**-runs.
- Removing that cap leaves the fleet inventory, which does not bind.
- The STB increment is real and 2022-specific (+2.5 to +3.7 TWh at its ceiling). But it can only act through a non-physical base cap or a fitted safety-stock / conservation parameter. The first is rule 1 (c) [R-STRUCT]; the second is rule 21 [R-DOF].
- This matches SPP-69's reading of the $21.12 markup: a **precautionary risk premium** against a shortage that did not happen (2022 fleet minimum stock was 8.5 Mt actual). The STB series now names *why* the premium was 2022-specific, but not *how big* it was.

**Verdicts.**
- `coal_fuel_inventory`: stays `R` on SPP, re-measured on the new evidence. The cumulative per-plant form also fails, now on measured delivery flexibility.
- Deliverability-keyed coal offer markup: **identified but not buildable at zero DOF**, recorded in the §5.7 queue.

## 3. Rules

- Rule 1 (c), rule 13 (same-year receipts and stocks are labelled forbidden comparators), rule 21 (no safety-stock parameter proposed), rule 23 (no derive touched), rule 28 (cell evidence appended in `SPP.js`; queue updated).
- Rule 29(b): no solve, so no control.
- Rule 31: nothing produced, nothing deleted. Rules 32–36: no shards (§0.3), so nothing to archive.
- Step 0a never adopted a basis because it passes: the owner ruled hold.

## 4. Ledger (plan step 5) and successors

- **C1 COAL_PRB 2021/22.** Residual is +3.97 / +3.59 TWh of dispatch on the aligned basis. The rest (≈ 7.4 / 7.3 TWh) is the gross/net station-service basis held by W5. It is ledgered as basis-pending, not as a model miss of +11.
- **C1 CC_REGULAR 2021/22.** Dispatch miss of −8.0 / −8.7 TWh at the central coverage allocation. The counterparts are wind (+5 / +9 TWh vs EIA-930) and aligned coal (+4 / +4). It is ledgered as model-class (DA commitment of CCs, plan §3.4 diagnosis) with no admissible lever identified.
- **C4 gas 2022 (0.326).** Ledgered per plan step 5. Rail step 3 fails, see §2.
- **Successor 1 (owner-ruled W5):** zero-LP all-ISO census of gross/net coal, gas coverage and coverage breaks (the SPP-87 / 88 constructions generalised).
- **Successor 2:** plan §3.4 step 2, the pairing span `spp_commitment_posture` + SPP-107. It touches the CC-commitment half of this object.
- **Successor 3:** step 0b, the CT pmax basis vs `SUMMER_CLASS_DERATE` audit.

No promotion question arises (rule 31): nothing was solved.
