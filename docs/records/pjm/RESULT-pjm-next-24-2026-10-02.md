# RESULT: PJM-NEXT-24. Coal and CT are two objects: coal is within-plant (year-specific), CT is across-plant (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO all read **NOT-YET**. The same 10 failing cells.

**Solves:** none. No PRECOMMIT: card 4 was not reached.

| probe | artifact | card |
|---|---|---|
| `scripts/probes/_pjmnext24_loading_margin.py` | `results/phase0/pjm/_pjmnext24_loading_margin.json` | 1 |
| `scripts/probes/_pjmnext24_within_across.py` | `results/phase0/pjm/_pjmnext24_within_across.json` | 1b |
| `scripts/probes/_pjmnext24_ct_runblocks.py` | `results/phase0/pjm/_pjmnext24_ct_runblocks.json` | 2 |
| `scripts/probes/_pjmnext24_campd_split_census.py` | `results/phase0/pjm/_pjmnext24_campd_split_census.json` | 3 |

**Common axis**, per plant-hour:
- Margin = actual PJM system RT (or DA) − the plant's keeper offer.
- Offer = the capacity-weighted P1 `mc` over the plant's tranches. It is set by fuel, heat rate and bands, not by dispatch.
- Loading = output ÷ the plant's LP available capacity.
- Model output comes from `unit_marginal_<y>`; real output from the C1 bench (EIA-923 net, CAMPD shape).

## 1. Card 1: loading vs margin, coal and CT on one axis

**Model − real TWh, by actual-RT margin bin:**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| COAL, margin < −10 | −0.7 | −2.1 | −1.5 | −0.6 | −4.2 | −4.2 | −0.8 |
| COAL, −10..0 | +2.7 | +1.0 | +2.6 | +1.3 | +0.2 | +0.2 | +1.6 |
| COAL, ≥ 0 | **+14.2** | **+12.1** | **+17.0** | +9.7 | +4.1 | +3.7 | +13.9 |
| CT, margin < −10 | **−5.4** | **−5.8** | **−7.9** | **−5.7** | **−6.0** | **−5.3** | −3.0 |
| CT, −10..0 | −0.9 | −0.3 | −0.8 | −0.4 | +0.7 | +2.0 | +2.2 |
| CT, ≥ 0 | +0.2 | +0.3 | −0.4 | −0.8 | +2.9 | +4.0 | +4.3 |

- **Real response is flat and close to year-invariant** in both classes:
  - Real coal loading runs 0.45–0.55 at −40..−10 and 0.78–0.92 at +10..+40.
  - Real CT loading runs 0.05–0.10 at −40..−10 and 0.34–0.41 at +10..+40.
- **The gaps sit on opposite sides:**
  - Coal over-loads **in money** (the 2019–21 and 2025 excess).
  - CT under-runs **deep out of money** in every year, plus an in-money over-run from 2023.

**Card 1b: within-plant vs across-plant.** The question is whether a plant's own loading tracks its own margin over time (within), or whether plant loading tracks plant cost across the fleet (across).

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| COAL within, model / real | **0.66 / 0.30** | **0.69 / 0.25** | **0.56 / 0.19** | 0.35 / 0.19 | 0.29 / 0.24 | 0.34 / 0.20 | 0.26 / 0.22 |
| COAL across (per $10), model / real | 0.17 / 0.20 | 0.29 / 0.16 | 0.14 / 0.16 | 0.05 / 0.06 | 0.19 / 0.08 | 0.23 / 0.12 | 0.16 / 0.07 |
| CT within, model / real | 0.35 / 0.30 | 0.34 / 0.34 | 0.23 / 0.26 | 0.24 / 0.26 | 0.36 / 0.30 | 0.33 / 0.28 | 0.32 / 0.28 |
| CT across (per $10), model / real | 0.014 / 0.004 | 0.022 / 0.010 | 0.019 / 0.010 | 0.015 / 0.008 | 0.038 / 0.013 | 0.053 / 0.017 | 0.049 / 0.021 |

**Verdict, card 1: the "one object" hypothesis is refuted.**
- **Coal is a within-plant object, and it is year-specific.** The keeper's own-plant response is 2.2–3× real's in 2019–21, exactly the COAL_BIT fail years, and 1.2–1.7× in 2022–25. Across-plant ordering is near real in 2019, 2021 and 2022.
  - The keeper's coal econ-tranche share is 0.46–0.49 of capacity in 2019–22 and 0.37–0.40 in 2023–25. Must-run is 0.19–0.23 and committed 0.29–0.35.
  - Reading: half the coal capacity toggles on price in the LP, while real plants follow price only about a quarter as far.
  - This is suggestive, not established. 2022 has a 0.46 econ share but only 0.35 contrast, because the deep-in-money coal there toggles little.
- **CT is an across-plant object.** Within-plant, model ≈ real. The keeper's cost ordering across plants is 2–3.5× steeper than real in every year. This is NEXT-23's "cheap CTs over-run, dear CTs under-run".

A candidate therefore cannot "flatten both classes" with one mechanism. They need different levers.

## 2. Card 2: what real CTs below their offer are doing

**Run blocks.** A run block is a maximal stretch of hours with output > 5 % of mean capacity. Each block is classified by its best hour against the keeper offer:

| real CT | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| energy in blocks that clear somewhere (TWh) | 11.3 | 14.4 | 16.2 | 15.8 | 17.3 | 20.8 | 22.3 |
| ... of which in the blocks' out-of-money hours | 5.8 | 7.6 | **8.4** | 5.2 | 6.8 | 7.1 | 6.5 |
| whole blocks deep out of money (≤ −$10) | 2.6 | 2.6 | 2.3 | 1.6 | 2.5 | 1.9 | 1.2 |
| blocks, real / keeper | 5007 / 2508 | 5109 / 2621 | 6547 / 2621 | 6476 / 2145 | 6040 / 2529 | 7579 / 3491 | 8976 / 3786 |
| median block length (h), real / keeper | 9 / 11 | 11 / 13 | 10 / 12 | 9 / 12 | 10 / 13 | 8 / 12 | 8 / 11 |

Notes on the table:
- Real blocks are classified on actual DA or RT. Keeper blocks are classified on the keeper's own zonal price.
- Keeper out-of-money-hour energy inside cleared blocks is 1.8–4.6 TWh.

**Reading.**
- Real CTs start about twice as often as the keeper's.
- About half their energy in cleared blocks falls in out-of-money shoulder hours. The real-minus-keeper shoulder gap is largest in 2021 (+6.6 TWh), the CT_PEAKER fail year.
- Whole deep-out-of-money blocks are small, 1.2–2.6 TWh/yr. In 2021 that is AEP-Ohio 0.9 and Dominion 0.7 (Tait and Doswell), with a median best margin of −$24.
- **Not min-run.** Keeper blocks are already as long as real ones or longer, so a CT min-run floor (the NYISO bridge leg) would not bind.
- **Not tested here:**
  - Balancing Operating Reserve / reliability commitments: the IMM State of the Market and PJM BOR credits by zone are not on disk.
  - DA commitment against the DA price: the DA axis is no sharper than RT for real CTs (card 1).

**Verdict, card 2:** the CT gap is more starts, spread across more plants. It is not longer runs and not an out-of-market tail. **OPEN, not a limit.**

## 3. Card 3: CAMPD facility vs EIA-923 plant-ID splits

**Census scope:** CAMPD unit-level facilities in PJM's states, 2019–2025.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| orphan CAMPD facilities, ≥ 10 GWh with no EIA-923 fossil generation under their own ID | 8 | 9 | 9 | 9 | 10 | 9 | 10 |
| ... whose host plant is in the C1 bench | 1 | 2 | 1 | 1 | 1 | 1 | 1 |
| ... their gross load (GWh) | 664 | 747 | 719 | 818 | 931 | 951 | 754 |

- **Tait 55248 → 2847 is the only bench-relevant split.** 2020 adds a second, short-lived host. The other orphans are outside the bench:
  - H F Lee and L V Sutton, Duke NC;
  - Cove Point LNG;
  - industrial and biomass sites.
- **Bench plants with CAMPD gross < 0.7 × EIA-923 net are not splits.** They are:
  - CC steam turbines not in CEMS (Ironwood, Hunterstown, Allegheny 3–5);
  - non-CEMS sites (waste coal: Seward, John B Rich, Grant Town, St Nicholas; CHP).
- **Effect:**
  - C1 totals: none (EIA-923).
  - Tait's bench hourly shape and measured HR: drawn from GT1–3 only. NEXT-23 sized the offer effect at about $1–2/MWh.
  - **Fix:** a one-entry PJM `CAMPD_UNIT_PLANT_REMAP` (55248 CT4–CT7 → 2847). It is a rule-14 data correction with zero DOF. Its re-derive cost (bench, CT HR, outage windows) is not yet sized.

## 4. Card 4

**Not reached.** Cards 1–3 yield no admissible, year-discriminating, zero-DOF mechanism:
- Coal is year-discriminating (within-plant, 2019–21) but has no measured lever yet.
- The CT ordering object is not year-discriminating.
- The Tait remap is too small to move a cell.

## 5. Next (NEXT-25)

1. **Coal within-plant, 2019–21.** Measure why the keeper's own-plant response is 2–3× real's in exactly these years:
   - Per plant, the keeper's econ-tranche share and floor (must-run + committed) by year, against the real plant's measured within-plant response.
   - Whether the binning (`docs/binning-methodology.md`) turns a real load-following band into a price-following band. The test: does real econ-band output track net load rather than margin?
   - Check the `use_campd_bins`, `coal_mustrun_per_plant` and `committed_band_measured_basis` (R; pjm-h8) history first. Do not re-test the R cell without new evidence.
2. **CT across-plant ordering.** Real CT dispatch is 2–3.5× flatter across plant cost. Two questions to measure:
   - Is real per-plant CT run-hours explained by location (zonal DA, which needs a `fetch_pjm_zonal_lmp_components.py` DA pull) rather than cost?
   - Is it explained by BOR credits? That needs an intake of the PJM operating-reserve credit reports.
3. **Tait remap:** optional, as a rule-14 data repair bundled with a future solve, not a lever.

**Retrievability:** no bundles. The probe JSONs are committed under `results/phase0/pjm/`.
