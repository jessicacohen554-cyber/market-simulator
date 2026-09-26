# FINDING: SPP-87, the EIA-923 vs EIA-930 coal gap is net vs gross metering, not membership (zero LP, 2026-09-26)

Lane: SPP-87. Parent: SPP-86 (`FINDING-spp-86-coal-floor-conduct-2026-09-26.md` §3).
Keeper: `2026-09-26-spp-86-coal-extract`, bundle `results/calibration/spp86_arm_span`. Base: `origin/main` `76eaeeea`.
Probe: `scripts/probes/_spp87_benchmark_reconcile.py` → `results/calibration/_spp87_benchmark_reconcile.json`.
**Card taken: A (benchmark reconciliation).** No LP, no shard, no bundle, no scorer change. Cards B and C not scoped.

## 0. Headline

1. **The 4–6 TWh/yr coal disagreement comes from metering basis, not from plant membership.**
   - EIA-930 SWPP coal and the SPP portal gen-mix agree to within 1.2 TWh. The portal is SPP's own data.
   - EIA-930 tracks **CEMS gross** of the scorer's own coal plants hour by hour. The fit slope is 0.97–1.04 and correlation 0.95–1.00.
   - EIA-923 is **net**: 0.89–0.91 × gross, i.e. 7.5–8.5 TWh/yr of station service.
   - Membership accounts for ≤ 0.04 TWh. Subclass routing does not change the family total.
2. **The model's coal output is on the gross basis.**
   - Its 2021 coal peak is 20.1 GW. EIA-860 nameplate for the same plants is 20.2 GW; net summer capacity is 19.1 GW.
   - SPP-41 found the model's coal stays within each plant's own **CAMPD (gross)** maximum.
   - Model demand equals EIA-930 total generation (`NG`) exactly: 269.65 TWh in 2021. That is SPP-metered generation, where coal is booked near gross.
3. **The scorer's coal benchmark is on different bases in different years.**
   - `reconcile_vintage_classes` scales all fossil classes to the EIA-930 fossil total when EIA-923 falls outside its band.
   - For SPP it does not fire in 2019–22 (×1.000). It fires in the **train tier**: ×1.039 in 2023, ×1.054 in 2024, ×1.065 in 2025.
   - So 2023–25 coal is partly raised toward gross (+2.8 / +3.5 / +5.1 TWh). The **gas classes are raised by the same factor**, even though the extra energy is coal station service, not gas.
4. **Choosing a basis barely changes the verdict.**
   - A zero-LP shadow re-score of C1 and C2 on three bases (committed, net with the scale undone, gross coal) moves **3 rows, all in the validation tier**: COAL_PRB 2021 and 2022 FAIL → PASS, and 2020 PASS → FAIL, on the gross basis.
   - **No train-tier status moves.** No C2 status moves. The determination is unchanged on every basis.
   - **CC_REGULAR 2021 and 2022 stay FAIL on every basis.**
5. **So the 2021–22 "coal over, CC under" failure is not mainly coal merit order.**
   - On the aligned (gross) basis, coal is over by **+2.0 / +5.5 TWh**, not the +10.1 / +13.9 TWh C1 shows.
   - The gas-family deficit is −14.3 / −19.3 TWh against EIA-930. **Wind (+8.0 / +9.2 TWh) remains its largest single counterpart on every basis.**
   - Card B (wind CF level) is the next object.

## 1. Coal gap by cause (TWh)

Identity: EIA-930 − scorer `classFull` = reconcile scale + station service + SPP reporting residual + (frame vs raw 923, ≤ 0.17).

| year | 930 coal | portal | 923 frame (net) | classFull | CEMS gross* | **930 − classFull** | reconcile scale | station service | SPP residual (930 − gross) | outside scorer set |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 94.12 | 94.57 | 89.73 | 89.73 | 98.04 | **+4.39** | 0.00 | +8.44 | −3.92 | 0.00 |
| 2020 | 82.69 | 81.50 | 77.00 | 77.00 | 84.50 | **+5.69** | 0.00 | +7.79 | −1.81 | 0.00 |
| 2021 | 97.03 | 96.48 | 90.87 | 90.87 | 99.03 | **+6.16** | 0.00 | +8.33 | −2.01 | 0.00 |
| 2022 | 96.84 | 96.10 | 90.80 | 90.80 | 99.13 | **+6.04** | 0.00 | +8.50 | −2.30 | 0.00 |
| 2023 | 78.41 | 77.52 | 71.99 | 74.81 | 79.21 | **+3.60** | +2.82 | +7.52 | −0.80 | 0.00 |
| 2024 | 72.44 | 72.08 | 65.24 | 68.73 | 73.13 | **+3.70** | +3.50 | +8.04 | −0.69 | 0.00 |
| 2025 | 87.70 | 87.35 | 78.40 | 83.53 | 86.15 | **+4.17** | +5.13 | +7.84 | +1.55 | 0.04 |

\*CEMS gross of the scorer's coal plants (coal units, `grossLoad × opTime`), plus the EIA-923 net of the one unmetered plant, River Valley 10671 (about 1 TWh; CAMPD `grossLoad` is null, SPP-86 §3).

Hourly EIA-930 coal against CEMS gross (OLS; a net-basis series would show a slope of about 0.91 and a positive intercept):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| slope | 0.97 | 1.04 | 1.01 | 1.00 | 1.03 | 1.00 | 0.99 |
| intercept MW | −47 | −457 | −179 | −168 | −272 | +69 | +369 |
| corr | 0.946 | 0.994 | 0.992 | 0.998 | 0.992 | 0.982 | 0.957 |

Reading:
- **Station service is the whole gap**, and it is stable at 7.5–8.5 TWh.
- SPP reports coal a few hundred MW below gross in 2020–24. The shortfall is larger in 2019 (−3.9 TWh, weaker fit) and flips sign in 2025 (+1.6 TWh; intercept +369 MW). That residual is an SPP-reporting feature, **not** a stable basis. This is why raw EIA-930 coal is not the right substitute either.
- **Subclass routing is clean.** The three lignite plants (2817, 6469, 7902) carry the refined-coal (`RC`) rows of 2019–21, and PRB / LIG sum to the family total in every year.
- **Missing reporters:** only River Valley (unmetered by CEMS; present in both EIA-923 and the frame).

## 2. Keeper minus each benchmark (TWh)

| year | coal vs 923 (C1) | coal vs gross | coal vs 930 | gas vs 923 | gas vs 930 | wind vs 930 (= C1) |
|---|---|---|---|---|---|---|
| 2019 | +1.31 | −7.00 | −3.08 | −2.96 | −0.43 | +1.22 |
| 2020 | −4.34 | −11.84 | −10.04 | −3.30 | +0.04 | +8.09 |
| 2021 | +10.13 | **+1.97** | +3.98 | −16.93 | −14.29 | **+8.03** |
| 2022 | +13.88 | **+5.54** | +7.84 | −20.25 | −19.28 | **+9.18** |
| 2023 | +2.00 | −2.40 | −1.61 | −9.99 | −7.42 | +8.41 |
| 2024 | +1.55 | −2.84 | −2.15 | −12.56 | −10.18 | +11.44 |
| 2025 | +7.68 | +5.06 | +3.51 | −18.19 | −14.82 | +10.92 |

- C1 wind is **already** EIA-930 (`render_calibration_html` overwrites `classFull` wind/solar with EIA-930). The portal agrees within 1.2 TWh in 2020–25, so the wind excess is real on every basis.
- Gas: EIA-930 gas sits 2.5–3.4 TWh below EIA-923 grid gas in every year. That gap is **not** coal-related and is not explained here. It is left open, not absorbed.

## 3. Which benchmark each row should trust (rule 14 test)

| row | trust | why |
|---|---|---|
| C1 COAL_PRB / COAL_LIGNITE, level | **CEMS gross of the scorer's own plants**, routed per class (measured, complete, plant-level) | EIA-923 net is accurate but **misaligned**: it is defined net of station service, while the model's coal is dispatched on nameplate (gross) capacity into a demand (EIA-930 `NG`) that carries coal near gross. Raw EIA-930 coal has no subclass split and a reporting residual that drifts from −3.9 to +1.6 TWh. |
| C1 coal, split between PRB and LIG | EIA-923 | Routing verified clean (§1). |
| C1 gas classes | EIA-923 **without** the fossil reconcile scale in SPP | In 2023–25 the uniform scale pushes coal's station service onto gas targets: CC_REGULAR +1.7 / +2.3 / +2.6 TWh in 2023 / 24 / 25. |
| C1 wind / solar | EIA-930 (as now) | The portal corroborates it. |
| C2 families | unchanged | No status moves on any basis. |
| C4 hourly correlation | unchanged | A basis difference is a near-constant scale on coal, which Pearson r ignores. |

## 4. What a benchmark fix would move (the pre-registered statement; computed, not landed)

The fix would be: per-plant CEMS gross for coal classes, and the fossil reconcile scale undone for SPP. Against the committed keeper, it moves exactly the following, and nothing else:

| row | model | committed actual → gross actual | status |
|---|---|---|---|
| C1 COAL_PRB 2020 | 63.98 | 66.13 → 72.96 | PASS → **FAIL** |
| C1 COAL_PRB 2021 | 91.78 | 80.35 → 87.74 | FAIL → **PASS** |
| C1 COAL_PRB 2022 | 91.63 | 78.14 → 85.47 | FAIL → **PASS** |

- Train tier 2023–25: **0 status moves**. The magnitudes do change: the COAL_PRB actual rises by +4.2 / +4.2 / +2.5 TWh (2023 / 24 / 25; +6.8 to +7.4 in 2019–22), and gas targets fall by up to 2.6 TWh. **2025 C1 stays SKIPPED** (preliminary vintage).
- Determination: unchanged. Train tier CALIBRATED; validation tier NOT-YET (CC_REGULAR 2021/22, C3a, C3b, C4 remain).

**Not landed, for three reasons:**
1. It changes a load-bearing criterion's benchmark basis, which is a rubric decision.
2. `reconcile_vintage_classes` and the C1 basis are ISO-agnostic by construction ("one rule for every BA"). An SPP-only branch would split the rubric, and the gross/net alignment of every other ISO's demand has not been measured.
3. It moves no train-tier status, so nothing in the SPP keeper depends on it.

This is an **owner decision** (§6).

## 5. Consequences for the lever queue

- **SPP-41 / SPP-44's coal-markup object was sized on the net basis.** On the aligned basis, the 2021–22 coal excess is +2.0 / +5.5 TWh (2 % / 6 %), not +10 / +14. This adds to SPP-44's `R` rather than reopening it.
- **The 2021–22 gas deficit's largest counterpart is wind on every basis.** Card B (the wind CF level in 2020–21, the SPP-67 object) is the next lane. Check its §5.7 DO-NOT-REDO first: the CF-LEVEL decomposition is already done, and a rate must never be interpolated.
- **The coal floor in dark hours** (SPP-86 §3.4, 0.57–1.11 TWh/yr) and **the 930-vs-923 gas gap** (2.5–3.4 TWh) remain open. The gas gap is a successor reconciliation: gas plant membership and behind-the-meter treatment, zero LP.

## 6. Owner questions

1. **Benchmark basis.** Should C1 score coal classes against **CEMS gross** of the scorer's own plants, matching the model's gross-basis coal and SPP-metered demand? It would be ISO-wide or SPP-only. Should the uniform fossil reconcile stop scaling gas to cover coal station service? Measured effect on SPP: §4 (3 validation-tier rows, 0 train-tier). Other ISOs are unmeasured; measuring them is a zero-LP successor.
2. **Housekeeping (not attempted, per rule 33(f)(5)):** leftover branches `claude/rspp-2019` … `claude/rspp-2025`, `claude/spp85-2019` … `claude/spp85-2025` and `claude/spp86-2019` … `claude/spp86-2025` need the owner to remove them. Sessions get HTTP 403 on ref deletion.

Nothing promotable was solved (no LP), so there is no promotion question under rule 31.
