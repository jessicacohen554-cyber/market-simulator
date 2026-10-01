# RESULT — PJM-NEXT-22: 2025 coal is a deep-in-money year, not a special one; west congestion and the capacity basis refuted; the 2023/24 coal fit is a cancellation (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO all read **NOT-YET**. Same 10 failing cells.

**Solves:** none. No PRECOMMIT (card 3 not reached).

| probe | artifact | card |
|---|---|---|
| `scripts/probes/_pjmnext22_coal_2025_plants.py` | `results/phase0/pjm/_pjmnext22_coal_2025_plants.json` | 1 |
| `scripts/probes/_pjmnext22_coal_zonal_margin.py` | `results/phase0/pjm/_pjmnext22_coal_zonal_margin.json` | 1b |
| `scripts/probes/_pjmnext22_west_spread.py` | `results/phase0/pjm/_pjmnext22_west_spread.json` | 1c |

Inputs: the keeper's `unit_marginal_<y>` and `system_<y>`, the C1 bench (EIA-923 net, CAMPD-shaped), PJM actual RT (`actual_lmp_hourly_PJM`) and, new here, **PJM actual RT zonal LMPs 2019–2025** (DataMiner2 `rt_hrl_lmps`, type ZONE, refetched with `scripts/data/fetch_pjm_zonal_lmp_components.py --feeds rt_hrl_lmps --years <y>`; gitignored). Hour axis: fixed EST with Feb 29 dropped. On it, PJM-RTO correlates 0.98–0.99 with the repo's actual series. Probe coal totals cover all COAL_* plants in the bench, so they are close to C1 COAL_BIT but are not C1.

## 1. Card 1 — what is specific to 2025?

### 1a. Per plant, 2025 vs 2024

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| coal over-run, all COAL_* (TWh) | +14.9 | +8.8 | +15.7 | +8.7 | −2.2 | −1.6 | +12.9 |
| actual RT mean ($/MWh) | 25.4 | 20.2 | 37.1 | 68.8 | 28.4 | 29.5 | **42.9** |
| keeper coal offer, cap-weighted ($) | 18.2 | 16.7 | 22.9 | 38.9 | 23.3 | 23.8 | 24.8 |
| CF on LP capacity, model / real | .82/.76 | .76/.72 | .87/.80 | .80/.75 | .70/.72 | .70/.71 | **.87/.80** |

- **2025 − 2024 = +14.5 TWh.** 44 continuing plants carry +15.5. Fleet change works against 2025: the two plants gone after 2024 (Indian River and one unnamed) carried +1.0 of 2024's over-run, and the 21 plant entries new in 2025 run at zero.
- **Concentrated in the west:** AEP-Ohio +7.6, West-APS +5.8. The top 15 plants carry 97 % (Rockport, Gavin, Harrison, Fort Martin, Clifty Creek, Mitchell, Conemaugh).
- **Every one of those plants' actual-RT margin rose by more than $5.** RT rose $13 and the keeper's coal offers rose $1.
- On the same plants, real output rose +20.3 TWh and the model's +35.8.

### 1b. Loading on LP capacity by margin (actual RT − keeper offer), model / real (net)

| margin | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| < 0 | .58/.53 | .56/.57 | .62/.58 | .59/.56 | **.52/.59** | **.52/.57** | .64/.61 |
| 0–5 | .80/.67 | .81/.70 | .84/.73 | .71/.65 | .74/.70 | .76/.71 | .83/.72 |
| 5–15 | .92/.86 | .92/.85 | .93/.84 | .77/.72 | .81/.76 | .82/.78 | .91/.79 |
| > 15 | .97/.92 | .93/.89 | .97/.88 | .88/.82 | .87/.84 | .88/.84 | .97/.88 |
| over-run, margin < 0 (TWh) | +3.2 | −0.9 | +1.4 | +0.9 | **−3.9** | **−3.4** | +0.8 |
| over-run, margin ≥ 0 (TWh) | +15.4 | +12.3 | +17.2 | +10.1 | **+4.1** | **+4.3** | +14.1 |
| coal capacity at margin > 15 (TWh-cap) | 34 | 19 | 72 | 117 | 32 | 38 | **74** |

**Reading.**
- **2025 is a deep-in-money year, like 2021.** Deep-margin coal capacity doubles from 2024 (38 → 74 TWh-cap). The model loads it to 0.97, real coal to 0.88, about the same as real in 2021 and 2019.
- **The 2023/24 coal "fit" is a cancellation.** Out of the money the model under-runs real coal (−3.9 / −3.4 TWh); in the money it over-runs (+4.1 / +4.3). The keeper's loading-vs-margin response is steeper than real coal's in **every** year. The year's C1 sign tracks how many coal hours sit in the money. This restates NEXT-11's "response, not price" at margin grain and explains why 2025 broke every ordering tried (price-gap volume, ladder width, ladder slope).
- It is not a clean year order either. 2019/20 carry their excess at shallow margin (0–5: +8.1 / +7.2). In 2022 the model does not saturate in the money (0.88), the NEXT-11 tail-compression year.

### 1c. Candidates refuted for 2025

| candidate | measured | verdict |
|---|---|---|
| Fleet composition after retirements | Exits lower 2025 − 2024 by 1.0; entries add 0. The +15.5 is continuing plants. | Not the object. |
| Coal LP capacity on a gross (nameplate) basis vs a net bench | The keeper's max hourly coal MW is **0.97–0.98 × EIA-860 net summer** (0.87–0.88 × nameplate) in 2021/2024/2025. The basis is already net. `coal_nameplate_summer_derate` would apply ns/np ≈ 0.93 on top: a double count on PJM (rule 19). | Refuted. The cell stays **U**, with this sizing as its PJM evidence. |
| West congestion (actual AEP/APS below RTO in 2025) | Actual west − RTO, coal-weighted mean: AEP −3.7, APS −2.3 in 2025 vs ≈ 0 in 2021/2024. The keeper reproduces it: −2.6 / −2.5. Medians are ≈ 0 on both sides in every year. Outside 2022 the model is within $1.4 of actual, and below it in 2019–2024 (table below); the one premium is AEP 2025, +$1.1, against a +7.6 TWh AEP delta. | Refuted. Congestion does not over-value western coal. |
| Margin re-based on actual zonal RT | Bin membership barely moves (≤ 5 TWh-cap per bin). Over-run splits unchanged to ±0.5 TWh. | Not the object. |

West minus system spread, coal-MW-weighted mean ($/MWh), actual / model:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| AEP-Ohio | +0.7 / −0.7 | +0.5 / −0.1 | +0.9 / −0.2 | −2.9 / −0.5 | +0.5 / −0.2 | −0.5 / −1.3 | −3.7 / −2.6 |
| West-APS | +0.4 / −0.7 | +0.8 / −0.2 | −0.1 / −0.3 | −3.7 / −0.3 | +0.7 / −0.4 | −0.2 / −1.5 | −2.3 / −2.5 |

(2022 is the one year the model misses a west discount, ≈ $3. That would argue for **less** 2022 coal. COAL_BIT 2022 passes.)

**Verdict, card 1.** 2025 has no special cause: it is the deep-in-money year that 2019/2021 also were. Every year shares one object, the keeper's coal response to margin being steeper than real coal's. It is localized but has no admissible, year-discriminating, zero-DOF lever. **OPEN, not a limit.**

## 2. Card 2 — non-coal cells (zero-LP localisation)

**CT_PEAKER** (probe-level model − bench, TWh):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| model / bench | 9.2 / 15.3 | 12.9 / 18.6 | 11.2 / 20.1 | 11.7 / 18.2 | 18.7 / 21.0 | 24.5 / 23.6 | 28.1 / 24.0 |
| ComEd | −0.5 | −0.6 | −1.4 | +2.4 | +3.7 | +5.0 | +5.2 |
| West-APS | −1.0 | −0.4 | 0.0 | −0.8 | +2.1 | +2.9 | +2.8 |
| AEP + Dominion + ATSI + SWMAAC | −5.0 | −4.6 | **−7.6** | −8.2 | −8.3 | −7.6 | −4.3 |
| CT committed-band output (keeper) | 4.0 | 4.7 | 4.4 | 4.4 | **6.5** | **8.2** | **8.6** |

- **Two objects.**
  - **(i) A persistent per-plant under-run,** the same plants every year: Tait, Doswell, Madison, Louisa, Aurora, Marsh Run, Pleasants and others. 0.3–1.3 TWh each, the top 12 = 73 % of 2021's gap.
  - **(ii) An over-run that steps up from 2022/23,** in ComEd and West-APS. Every CT band doubles from 2022 to 2024, committed included.
- **2021 fails** because (i) is at its widest there and (ii) has not started.
- **(ii) is not the reserve vintage.** The keeper's reserve requirement rises only +0.35–0.5 GW from 2023 (duals zero). In ComEd, price exceeds the CTs' mean offer in only 95–444 h/yr while they produce 6–8 TWh. The 2023 step is **not localized**.
- **`ct_peaker_committed_measured` (U)** is the one queued CT lever. It is year-invariant: it raises CT in every year, helping 2021 but worsening 2024/25, which already over-run. It fails the year-discriminating bar. Not proposed.

**2022 cluster (CC_REGULAR +10.9, C3a, C3b).** Nothing new beyond NEXT-10/11 (tail compression, p99 $105 vs $210; PJM's own 2022 offers ≈ 2× delivered fuel, already carried). Card 1c adds one piece: the keeper misses 2022's ≈ $3 west discount. That is not a CC lever. **OPEN.**

## 3. Card 3

Not reached. No admissible, year-discriminating, zero-DOF mechanism.

## 4. Next (NEXT-23)

1. **CT_PEAKER's 2022→2023 step.** Every CT band doubles 2022 → 2024 while ComEd prices rarely clear CT offers. Diff the keeper's CT inputs 2022 vs 2023, zero LP: fleet, heat rates (`measured_ct_heat_rates`), outage windows (`unit_outage_rederive_peaker_windows`), floors (`ct_deployment_floor`, forced-energy census) and gas basis. Find which input steps, then judge it against the real CT trend (bench +2.8 TWh 2022 → 23 vs model +7.0).
2. **CT object (i): the persistent per-plant under-run.** Per plant (Tait, Doswell, Madison, Louisa), measured heat rate, delivered gas and outage windows vs real run-hours. These plants under-run every year, so a per-plant input defect is plausible.
3. **Coal response slope:** the object is now framed at margin grain (out-of-money under-run, in-money over-run, every year). Any mechanism must lift out-of-money coal **and** lower in-money coal. Not re-tested: price level, offered EcoMax, outages, self-scheduling, own-offer RoR, offer slope, ladder width, capacity basis, west congestion (NEXT-10..22).

**Retrievability:** no bundles. Probe JSONs are committed under `results/phase0/pjm/`. The zonal RT corpus is gitignored raw and lost with the container. The fetcher rewrites `data/raw/pjm-zonal-lmp/SHA256SUMS.txt` to the files on disk; that rewrite was reverted so the DA provenance behind the committed loss surface is kept.
