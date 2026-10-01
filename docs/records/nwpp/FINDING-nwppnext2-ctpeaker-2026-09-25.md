# FINDING — NWPP-NEXT-2 item 5: why the NWPP keeper runs CT_PEAKER short (zero LP)

Keeper `2026-09-25-nwpp-next-ferc714-partial` (`results/calibration/nwppnext_span`); no solve run. Probe
`scripts/probes/_nwppnext2_ctpeaker_diag.py` reads the committed `hourly/` sidecars, bench parts and run payload, the
`build_benchmark_frames` rebuild, and the fleet via `replay_keeper.run_year_kwargs` + `run_year(fleet_only=True)`.

**Verdict.** Two separable parts; neither is heat rate, availability, commitment, or CT-vs-CC classification.
- **(A) Fleet membership, 0.1–0.9 TWh/yr.** Fredonia (ORIS 607, PSEI, 4×GT, 376 MW) and Sun Peak (54854, NEVP,
  222 MW) are EIA-860 status **`SB`** in every vintage. The fleet keeps `status == "OP"` only
  (`data/fleet/eia860.py:751/1261/3319`), so both are absent from the model, yet both report EIA-923 generation.
  Fredonia ran 966 GWh in 2023, a 29 % CF.
- **(B) The model's price level, the remainder.** The LP dispatches essentially every CT MWh that is economic at its
  own zonal prices, and those prices sit below the CT offers in most hours real CTs ran. Real NWPP prices (Mid-C,
  WEIM) were far higher. The CT miss is one face of the lane's gas-short / coal-long / low-price pattern. It is
  **not** the NWPP-45 demand gap: a copper-plate merit test puts ~0 TWh of that gap on CTs.

## 1. The miss per year (C1 `classFull` = EIA-923 reconciled ×0.886–0.911 to EIA-930 fossil; 2025 ×1.000)

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| model / classFull | 1.58/2.98 | 4.17/3.15 | 1.34/3.79 | 1.61/3.99 | 2.33/7.09 | 4.06/7.39 | 6.59/5.24 |
| **Δ** | **−1.39** | **+1.02** | **−2.45** | **−2.38** | **−4.75** | **−3.33** | **+1.35** |
| (A) SB plants absent (607+54854) | −0.22 | −0.28 | −0.41 | −0.27 | **−0.90** | −0.53 | −0.11 |
| remainder = in-fleet dispatch | −1.17 | +1.30 | −2.04 | −2.11 | −3.86 | −2.80 | +1.46 |

**2025 is suspect**: its EIA-923 vintage lists 17 CT plants (33–35 other years). 2020 is a real over (gas $2.03).

## 2. Q1 — peak-concentrated? **No. The miss is spread across all hours.**

**Basis.** C1 scores CT_PEAKER on EIA-923 monthly (payload `volErr.CT_PEAKER.src = "eia923"`). The hourly shape
here is CAMPD, taken on the 13–14 CAMPD-reporting CT plants (67–81 % of 923 CT) and scaled to their 923 level.

| Δ TWh by model-load quintile Q1..Q5 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|
| Q1 / Q2 / Q3 | −.38/−.38/−.23 | −.35/−.31/−.28 | −.47/−.54/−.57 | −.41/−.37/−.37 |
| Q4 / Q5 | −.18/−.24 | −.22/−.24 | −.64/−.71 | −.32/−.09 |
| top-10 % load hrs: share of model / actual CT | 31.3 / 20.3 % | 23.5 / 17.5 % | 17.8 / 14.9 % | 20.6 / 13.9 % |
| hourly r(model, actual) | 0.49 | 0.36 | 0.42 | 0.46 |

**Model CTs are more peak-concentrated than the real ones**, which carry a base: 2023 model vs actual 00h 232/569,
12h 199/519, 18h 418/778 MW; median actual CT plant online 3,902 h (2023), 5,841 h (2024).

## 3. Q2 — capacity or availability limited? **No. The CTs are economically not dispatched.**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Σpmax MW / envelope TWh | 3007/22.4 | 3007/22.4 | 3009/22.4 | 3087/22.9 | 3082/22.9 | 3645/24.9 | 3648/27.0 |
| model CF / actual CF (classFull on model Σpmax) | 6.0/11.3 % | 15.8/12.0 % | 5.1/14.4 % | 5.9/14.8 % | 8.6/26.3 % | 12.7/23.1 % | 20.6/16.4 % |
| economic envelope† / dispatched TWh | 1.78/1.58 | 4.66/4.17 | 1.44/1.34 | 1.72/1.61 | 2.48/2.33 | 4.59/4.06 | 7.18/6.59 |

† Σ pmax·availability over hours where the zonal price ≥ the unit's mc.

The class never reaches 95 % of its envelope in any hour. **Dispatch ≈ economic envelope (within 0.1–0.6 TWh)**: the
LP clears every CT MWh its own prices support. No floor to blame (C8/D-2 PASS, fast-start, pure LP).

## 4. Q3 — merit position, and what displaces the CTs

**Heat rate** 10.7–11.1 (CT) vs 7.3 MMBtu/MWh (CC_REGULAR), cap-weighted: CT sits above CC in every zone.

| Median unit mc, $/MWh | EAST | INLAND | NW | OR | SNV |
|---|---|---|---|---|---|
| CC / CT, 2023 | 58.9 / 92.2 | 34.4 / 49.8 | 38.9 / 70.8 | 34.6 / 65.4 | 62.0 / 93.2 |
| CC / CT, 2024 | 23.1 / 36.7 | 20.4 / 28.9 | 23.5 / 43.6 | 16.8 / 29.3 | 24.3 / 35.4 |

**In actual-CT top-decile hours** the model price p50 is $36.6 vs cap-weighted CT mc $57.2 (2024: $36.6 vs $43.4).

**Diagnostic reference price, NOT a benchmark** (`nwpp-weim` gate verdict NO; WEIM is an RT imbalance price):

| mean $/MWh (NW/OR/INLAND/EAST/SNV) | WEIM | model, same hours |
|---|---|---|
| 2023 Jun–Dec | 47.8/46.0/44.7/39.1/40.4 | 33.3/33.3/33.3/33.1/50.5 |
| 2024 | 42.8/41.8/38.6/31.1/29.6 | 27.2/27.2/27.2/26.0/35.8 |
| 2025 | 33.7/32.6/31.5/28.5/28.7 | 30.7/30.7/30.8/30.8/32.3 |
**Mid-C Peak** ICE daily wavg vs model NW HE7–22 mean: 87.5 vs 43.1 (2023), 61.7 vs 27.8 (2024), 46.4 vs 30.7 (2025).

**CT economic energy at WEIM prices vs model prices** (same mc, same envelope):

| Year | at WEIM prices | at model prices | actual (CAMPD plants) |
|---|---|---|---|
| 2023 (5,137 h) | 4.99 | 1.67 | 3.66 |
| 2024 | 10.46 | 4.59 | 5.61 |
| 2025 | 8.78 | 7.18 | 4.26 |

The CT miss tracks the price gap: largest in 2023–24; 2025 (gap ≤$3) is the year CT runs over.

**What displaces the CTs: not CC.** The whole gas family is short while coal is long:

| model − classFull, TWh | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| coal | +6.87 | +13.20 | +8.05 | +1.59 | −7.39 |
| gas | −12.23 | −16.49 | −15.55 | −11.45 | −4.47 |
| CC_REGULAR | −6.60 | −11.23 | −8.32 | −2.57 | −0.92 |

Coal offers run $12–24/MWh; hydro is within ±0.3 TWh of actual (2019–24). Together they set a price neither CC nor
CT clears.

## 5. Q4 — classification mismatch? **No CT↔CC mismatch, but one fleet-membership defect.**

**Classification is sound.** In every year, the top-12 EIA-923 CT plants are GT/IC in both the benchmark and the
model, which share the same `classify_plant` path. The multi-class plants split correctly: Clark 2322, Tracy 2336,
Harry Allen 7082 and Silverhawk 55841. No model CT plant lacks 923 CT, apart from one 10 MW row in 2019–20.

**The miss is dispatch, not labelling.** Actual 923 CF vs model CF by plant:

| Plant | 2023 offer | 2023 CF actual / model | 2024 CF actual / model (offers ≈$24) |
|---|---|---|---|
| Port Westward 2 (58266, IC, HR 9.0) | $41 | 60 / 2 % | — |
| West Valley (55622) | $45 | 52 / 0.1 % | — |
| Rathdrum (7456) | $38 | 67 / 23 % | 75 / 20 % |
| Bennett Mtn (55733) | $37 | 43 / 23 % | 60 / 20 % |
| Whitehorn (6120, HR 13.2) | — | 38 / 0.3 % | — |
| Evander Andrews (7953) | — | — | 48 / 6 % |
**The mirror case.** Dave Gates (56908, MT; implied fuel $1.1–2.1) is over-run in 2023–25 at 63–80 % against
41–47 % actual. It is the one fuel basis that puts a CT under the model price.
**Membership (A).** EIA-923 gas MWh on plants with **no** fleet rows is 0.70 / 1.27 / 0.90 TWh (2021 / 23 / 24).
Most of it is SB-status Fredonia and Sun Peak. The rest is small OP/OS ST_CHP plants (50187, 56192, 50637, 54562;
0.03–0.08 TWh each), reported but not pursued here.

## 6. Q5 — the NWPP-45 demand-basis gap: **separate, and closing it would not reach the CTs**

**The gap is not what keeps CTs off.** Keeper system gap (model − classFull total, TWh): −5.85 / −6.41 / −5.47 /
−5.24 / −7.55 / −9.93 / −6.97 (2019–25). In 2021–24 the gas shortfall exceeds the gap, because coal runs long.
**Copper-plate merit test:** add the gap uniformly (598–1,134 MW/h), fill cheaper headroom (CC_REGULAR + coal + CC_CHP
envelope − dispatch, p1 1.66–2.71 GW) first → **CT pickup 0.000–0.003 TWh every year**; CC headroom only (coal pinned)
→ ≤0.50 TWh (2020), 0.30 (2024), 0.006 (2023).
Closing the demand gap alone leaves ≥95 % of the CT miss; CTs recover only if prices in their running hours reach
~$40–60.

## 7. Root cause and structurally legitimate next tests

**Root cause, ranked:**
1. **Price and merit formation, shared with CC_REGULAR's shortfall and coal's surplus.** NWPP model prices sit
   $6–16 below WEIM (2023–24) and at about half of Mid-C Peak. At those prices the LP correctly leaves the
   measured-heat-rate CT offers out of merit. This is not a CT offer-level or commitment defect.
2. **Fleet membership (A):** `SB` units reporting EIA-923 generation are excluded (~0.9 TWh of 2023's miss).
3. **Not supported:** availability, commitment, CT↔CC classification, or the demand gap as the CT mechanism.

**Next tests.** None of these is a fitted adder, and none tunes offer-curve multipliers.
- **(i) Admit `SB` generators with EIA-923 net generation** to the fleet: measured input, zero DOF, rule 14; a gated
  `ScenarioConfig` field (rule 24) with a matrix row (rule 28); zero-LP SB-MW vs 923-MWh census first, NWPP's own
  data (rule 25). Expected +0.2–0.9 TWh CT; will not close C1 alone.
- **(ii) Explain why coal clears ahead of gas at low prices** — the real CT lever; one mechanism per phenomenon
  (rule 19), so no CT-specific mechanism. Measure zero-LP first: coal offer/availability (+7 to +13 TWh long in 2021–23), hydro shaping, zonal gas basis (CT
  implied fuel spans $1.1–4.4/MMBtu within a year). A labelled WEIM/Mid-C reference, if the owner rules one in, would
  let C3 score this; never pinned (rule 13).
- **(iii) Not recommended:** raising the CT band multipliers against this residual (gate selection, rule 1(c)); a CT
  floor or must-run (rule 17) — the evidence shows economic running at real prices, not a reliability window.

**Caveats:** `mc` is a fleet-only rebuild, not G-DRIFT-audited (econ envelope within 0.1–0.6 TWh of dispatch); sibling
uncommitted EIA-930 edits touch demand only; WEIM/Mid-C are diagnostics; CAMPD shape covers 67–81 % of 923 CT.
