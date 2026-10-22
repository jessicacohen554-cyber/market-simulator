# FINDING — UC-SPP-WIND: is SPP-South wind under-placed by the model's zonal split?

**Lane:** UC-SPP-WIND · **Date:** 2026-10-22 · **Branch:** `claude/uc-spp-wind` · **Base:** `main` `be5fb748`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner ruling R34 ("Keep 3,400 MW; probe wind (Recommended)").
**LP in this session:** zero. **Solve-path change:** none. **Data profile:** `spp`.
**Tables and scripts behind every number:** `docs/records/spp/uc-wind/` (reproducible from the committed inputs there).

## 0. Headline

| question | answer |
|---|---|
| Is the model's **annual** N/S wind split right? | **Yes.** Model South share 46.4–50.6 % vs EIA-923 plant-by-state 46.3–51.3 %; gap ≤ 0.8 pt in every year 2019–2025 (§2). |
| Is the model's **hourly** split noisy? | **Yes.** Hourly South-wind error vs the measured central estimate: p5/p95 ≈ ±1.1–2.2 GW on summer afternoons, MAE 0.5–0.9 GW (§2). |
| Is South wind under-placed **in the UC-unserved hours**? | **Not shown.** The one apportioning-free test (pure reserve zones, §4) says the real N–S wind gradient in those hours was **as steep as the model's or steeper**, including all five 2023-08-10 hours. |
| Does the zonal split explain the implied N→S of 4.6–6.2 GW on 2023-08-10? | **Not by itself.** Even under the most South-favourable defensible estimate (monthly apportioning, §3), implied N→S stays **3.8–4.5 GW (low bound)**, above 3,400 MW in all 5 hours. |

1. **New measured source.** SPP publishes hourly **actual** wind and solar output by **reserve zone** (portal product `resource-forecast-by-reserve-zone`, 2017→). Earlier lanes (SPP-32, the scarcity finding §4) said "no hourly zonal wind measurement exists in the corpus". That was true of the corpus, not of SPP. Intaken here for 2019–2025 (§1).
2. **The reserve zones do not align with the model seam.**
   - RZ1 (Nebraska) and RZ5 (Dakotas) are wholly SPP-North.
   - RZ3 (SPS: Texas Panhandle, New Mexico) is wholly SPP-South.
   - RZ2 (western Kansas plus part of SPS) and RZ4 (eastern Kansas, Missouri, Oklahoma, Arkansas, Louisiana) straddle the seam. They carry **≈ 70 %** of SPP wind energy.
   - So the hourly South total is measured only up to the unknown Kansas/Oklahoma split inside RZ2+RZ4.
3. **Hypothesis (b) of the corridor finding is not supported.**
   - The monthly-apportioned estimate assumes Kansas and Oklahoma move together within a month. On that estimate the model under-places South wind by 0.5–0.9 GW on 2023-08-10, and by 1.9–2.8 GW on 2025-12-21.
   - But the apportioning-free test reads the other way. Take the measured wholly-South zone (RZ3) against the wholly-North zones (RZ1+RZ5), each relative to its annual mean. That ratio was **0.20–0.25** in the 2023-08-10 hours, against the model's **0.28–0.42**. On 2025-12-21 it was 0.01–0.17 against the model's 0.03–0.16.
   - So in the hours that matter the real wind field was strongly North-heavy at its two measured ends. The monthly estimate smooths this away by construction.
   - Across all hours where the model's South share is in its own bottom decile, the pure-zone ratio matches the model's within 0.02 in 6 of 7 years (2025: 0.28 vs 0.21) (§4).
4. **Corridor-finding question (a) vs (b): still open, now narrowed.**
   - What remains unknown is one quantity: the hourly share of RZ2+RZ4 output that came from Oklahoma/Texas rather than Kansas/Missouri.
   - To bring the 2023-08-10 implied flow down to 3,400 MW, that share would have to be **0.73–0.92**. The August-2023 monthly value is 0.60. The measured gradient (North strong, SPS weak) points below 0.60, not above it.
   - Closing just the model's **unserved** energy needs less: a share of 0.40–0.59 that day, and 0.18–0.62 across all 19 hours (§3).

**Proposed treatment:** no replacement of the split now. Keep 3,400 MW (R34 unchanged). Detail in §6.

## 1. Data intake

| item | value |
|---|---|
| source | `portal.spp.org` file-browser, `fsName=resource-forecast-by-reserve-zone`, anonymous HTTPS. Found via `GET /api/menu/`. SPP's own description: "Wind and Solar *Forecast* for the next 168hrs and *Actual* for the previous 24hrs by Reserve Zone." |
| columns | `IntervalEnd, GMTIntervalEnd, ReserveZone (1–5), WindForecastMW, WindActualMW, SolarForecastMW, SolarActualMW` |
| coverage | hourly files 2017 → present. 2019–2024 as yearly ZIPs (38–96 MB). 2025 served per day: the 00:00 and 12:00 files of each day were fetched (730 files; one 404, 2025-08-10 00:00, covered by the neighbouring files' 24 h restatement) |
| reduction | per (GMT interval end, reserve zone), the actual from the latest-published file that carries one. 8,742–8,756 complete hours per year |
| committed | `uc-wind/rz_actual_hourly_2019_2025.csv.gz` (2.8 MB, 306,710 rows); `fetch_reduce_rz_actuals.py` rebuilds it. Raw ZIPs not committed (~0.5 GB) |
| zone definitions | `data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv` (`NODE_AREA` × `RESZONE`, the SPP-93 registry): RZ1 = NPPD / OPPD / LES (+ 41 KCPL nodes); RZ5 = WAUE; RZ3 = SPS (+ 1 WFEC); RZ2 = SECI / west-WR / part SPS; RZ4 = CSWS / OKGE / GRDA / WFEC / WR / KCPL / MPS / EDE … |
| EIA-923 monthly | Page 1 monthly net generation, SWPP-BA WND/SUN plants, by plant state, 2019–2025 (`uc-wind/f923_swpp_vre_monthly.csv.gz`, from the same release ZIPs as `data/raw/eia-923-generation-fuel`; all seven SHA-256 match that directory's `SHA256SUMS.txt`) |

**Clock.**
- Model hour *h* = the *h*-th local (America/Chicago) hour of the year, with 29 Feb dropped (`eia930/frames.py`).
- Measured series aligned as hour-beginning = GMT interval end − 1 h, in local time.
- Lag scan on 2023 system wind: r = 0.949 / **0.959** / 0.943 at −1 / 0 / +1 h.
- The slack-hour results move by ≤ 0.35 GW at ±1 h; no conclusion changes.

**Reconciliation.**
- Hourly r between the measured system total and the model's system wind is 0.93–0.99 in every year.
- The model level runs +1.6 % (2019) to +11 % (2024–25) above measured. The model carries SPP's *uncurtailed* potential; the measured series is delivered output.
- **Only shares are compared below**, plus MW in the shortage hours, where curtailment is nil.

## 2. Per-year, per-zone table (wind)

`uc-wind/annual_by_year.csv`, `split_error_by_year.csv`. "South share, measured" = EIA-923 monthly plant net generation by state, which is exact and needs no apportioning. "Hourly" columns use the monthly-apportioned central estimate (§3) and inherit its caveat (§4).

| year | SPP RZ actual TWh | model TWh | South share, EIA-923 | South share, model | hourly r (South) | summer 13–18 h ΔS mean (p5 / p95), MW |
|---|---|---|---|---|---|---|
| 2019 | 74.4 | 75.6 | 51.3 % | 50.6 % | 0.93 | +67 (−1,073 / +1,215) |
| 2020 | 81.9 | 84.0 | 48.5 % | 48.0 % | 0.93 | +91 (−1,379 / +1,494) |
| 2021 | 93.6 | 99.8 | 47.4 % | 47.5 % | 0.93 | +115 (−1,602 / +1,753) |
| 2022 | 107.6 | 118.1 | 46.3 % | 46.4 % | 0.91 | +8 (−1,759 / +1,435) |
| 2023 | 104.1 | 112.6 | 49.4 % | 50.2 % | 0.91 | +144 (−1,618 / +2,067) |
| 2024 | 110.2 | 122.4 | 48.2 % | 49.0 % | 0.88 | +57 (−1,859 / +2,234) |
| 2025 | 110.4 | 122.6 | 48.1 % | 47.6 % | 0.90 | +123 (−1,621 / +2,031) |

ΔS = measured South (central) − model South.

- The annual level split is right. SPP-54's R-21 concern ("sample mean levels act as zonal CF levels") does not show up as an annual bias in the two-zone build.
- The hourly split carries about ±2 GW of two-sided error, near zero on average in summer afternoons.

**Solar.**
- Small: SPP RZ solar 0.5–2.1 TWh, matching the model total within 1.3 %. The measured RZ series sits mostly in RZ3/RZ4.
- The model's South solar share runs 5–28 pt below the EIA-923-anchored measured share. At the slack hours that is **+10 to +72 MW** of South solar, carried in every number below.

## 3. The shortage-hour test (all 19 UC-unserved hours, U4b)

`uc-wind/slack_hours_wind_split.csv`. Constructions, all measured except *f*:

- S_lo = RZ3 (wholly South).
- S_hi = RZ3 + RZ2 + RZ4.
- S_c (central) = RZ3 + *f*_m · (RZ2+RZ4), where *f*_m = (EIA-923 South share_m × SPP RZ total_m − RZ3_m) / (RZ2+RZ4)_m.
- *f*_m is measured monthly: 0.51–0.65 across 2019–2025, and 0.60 in August 2023. **Its hourly value is not measured.**
- *f* needed (slack) = (model South + slack − ΔS_solar − RZ3) / (RZ2+RZ4): the share at which measured South VRE covers the model's unserved 1:1. The South is short at the link limit, so extra South supply offsets slack directly.
- Implied N→S (scarcity finding, §4) re-stated with measured South wind and solar in place of the model's.

| hour (model idx · local HB) | slack MWh | model South wind | RZ3 / S_c / S_hi | *f*_m | *f* needed (slack) | implied N→S lo–hi: model → with S_c | ratio S/N rel., model / pure-RZ |
|---|---|---|---|---|---|---|---|
| 2019 5870 · 09-02 15:00 | 137 | 1,270 | 176 / 2,989 / 5,431 | 0.54 | 0.23 | 3,487–4,035 → 1,720–2,268 | 0.21 / 0.20 |
| 2022 3206–07 · 05-14 15–16 | 236, 307 | 242–561 | 456 / 1,471–2,142 / 2,255–3,443 | 0.56 | −0.01–0.12 | 3,061–5,129 → 1,784–3,491 | 0.07–0.13 / **0.53–0.56** |
| 2022 6902–03 · 10-15 15–16 | 72, 147 | 1,523–1,637 | 358–420 / 2,203–2,778 / 3,566–4,628 | 0.57 | 0.33–0.37 | 2,654–4,502 → 1,561–3,416 | 0.26–0.27 / 0.23–0.25 |
| **2023 5317–21 · 08-10 14–18** | 11–821 (2,170 total) | 1,462–2,225 | 212–375 / 2,322–2,704 / 3,684–4,286 | **0.60** | **0.40–0.59** | **4,585–6,205 → 3,846–5,451** | **0.28–0.42 / 0.20–0.25** |
| 2023 6422–24 · 09-25 15–17 | 22–373 | 567–599 | 29–34 / 714–927 / 1,188–1,545 | 0.59 | 0.36–0.62 | 2,303–4,219 → 1,965–3,884 | 0.28–0.39 / **0.07–0.08** |
| 2023 6759 · 10-09 16:00 | 49 | 572 | 314 / 926 / 1,409 | 0.56 | 0.21 | 2,735–3,433 → 2,309–3,007 | 0.43 / 1.55 |
| 2025 8506–10 · 12-21 10–14 | 85–1,522 (3,623 total) | 249–1,045 | 13–216 / 2,621–3,236 / 4,298–5,403 | 0.60 | 0.18–0.34 | (not computed upstream) | 0.03–0.16 / 0.01–0.17 |

Read it two ways.

- **If *f* held at its monthly value**, the measured split would close **18 of 19** slack hours. The exception is 2023-09-25 16:00, which needs 0.62 against 0.59. It would also cut the 2023-08-10 implied N→S by 0.5–0.9 GW, still above 3,400 at the low bound in all five hours.
- **The last column says *f* did not hold.** In the hours that matter, the measured wholly-South zone ran far weaker relative to the wholly-North zones than the model's South ran relative to its North. That holds on 2023-08-10 (0.20–0.25 vs 0.28–0.42) and on 2023-09-25 (0.07–0.08 vs 0.28–0.39). On 2025-12-21 the two agree.
  - When the extremes of the wind field are that North-heavy, the Kansas part of RZ2+RZ4, which sits between Nebraska and Oklahoma, would plausibly run above its monthly share. That would push *f* **below** 0.60, not above.
  - This is an inference from geography, not a measurement. The data do not give *f* hourly.
- **The opposite cases are 2022-05-14 (0.53–0.56 vs 0.07–0.13) and 2023-10-09 (1.55 vs 0.43).** There the measured gradient was much flatter than the model's, so South wind was likely under-placed. The slack involved is 592 MWh.

## 4. Why the monthly central estimate cannot carry the conclusion

`uc-wind/low_south_decile_test.csv`.

- The monthly *f* gives every hour in a month the same Kansas/Oklahoma mix. That damps the measured South share toward its monthly mean by construction.
- The model's low-South hours are exactly the hours selected by the unserved test. A damped comparator will therefore always read "model too low" there: regression to the mean built into the estimator.
- The pure-zone test avoids it. It compares RZ3 against RZ1+RZ5, each relative to its own annual mean, with the model's South/North ratio relative to its own annual means.

| year | hours (model South share in its bottom decile) | model South share | measured South share, monthly-*f* | relative S/N, model | relative S/N, pure RZ (measured) |
|---|---|---|---|---|---|
| 2019 | 875 | 18.8 % | 36.7 % | 0.23 | 0.21 |
| 2020 | 876 | 16.6 % | 33.7 % | 0.22 | 0.21 |
| 2021 | 876 | 18.0 % | 33.2 % | 0.24 | 0.23 |
| 2022 | 875 | 15.3 % | 31.5 % | 0.21 | 0.20 |
| 2023 | 876 | 18.2 % | 36.1 % | 0.22 | 0.23 |
| 2024 | 876 | 17.1 % | 33.8 % | 0.22 | 0.21 |
| 2025 | 876 | 15.8 % | 34.6 % | 0.21 | 0.28 |

(medians over the decile)

- Where the model says "South calm, North windy", SPP's own wholly-South and wholly-North zones say the same, to within 0.02 in six of seven years.
- The monthly-*f* column's 17–21 pt gap is the estimator's damping, not a model bias. This is what overturns the reading of §3's first bullet.

## 5. Zero-LP effect on implied N→S

| construction | 2023-08-10 implied N→S (low–high bound) | vs 3,400 MW |
|---|---|---|
| scarcity finding (model South VRE) | 4,585–6,205 | above in all 5 h |
| measured, monthly *f* (South-favourable) | 3,846–5,451 | above in all 5 h |
| measured, extreme (all RZ2+RZ4 South, S_hi) | 2,445–3,123 | below |
| measured, *f* that brings the low bound to 3,400 | — | needs *f* = 0.73–0.92 |

- No defensible measured construction closes the 2023-08-10 corridor gap. A wind-split replacement would move implied N→S by at most −0.5 to −0.9 GW there.
- The pure-zone gradient suggests even less, possibly a move the other way.
- Corridor-finding reading (a), real N→S capability above 3,400 MW for that flow pattern (no corridor element bound in RTBM), remains the more consistent of the two. It is **not** a measured capability, so R34 stands: the limit is not raised.

## 6. Proposed treatment (owner/desk decisions; nothing solve-affecting lands here)

**W1 — Do not replace the zonal wind split now (recommended).**
- The annual level is right (§2).
- In the shortage hours the apportioning-free evidence does not show the reanalysis split to be biased (§4).
- A measured replacement on the two-zone seam would need an *hourly* estimate of the Kansas/Oklahoma share for ≈ 70 % of SPP wind energy. That is the hard-stop case (data requiring an estimate), and the monthly form of it is shown to be biased in exactly these hours.

**W2 — Keep `_ns_corridor_ttc = 3,400` (R34, unchanged).** This lane adds no measured capability above it.

**W3 — Re-attribution note for the scarcity finding (desk record, no model change).**
- 2025-12-21: the model's system wind there matches SPP's measured total (7.8–9.6 GW, within 1 %). The stale-snapshot repair works.
- Its North-heavy split agrees with the pure-zone measurement (0.03–0.16 vs 0.01–0.17).
- So the 3,623 MWh stays attributed to the EIA-930 load fill (rank 1), not to the wind split.
- 2022-05-14 and 2023-10-09 (592 MWh) are the hours where the measured gradient was much flatter than the model's. There, wind under-placement is the likely cause.

**W4 — A measured zonal VRE series exists for the reserve-zone topology (routing note, not a lever proposal).**
- SPP-93's West/East partition is built from these same reserve zones: West = RZ{1,2,3,5}, East = RZ4.
- Under that partition, hourly zonal wind and solar would be **fully measured** (RZ sums, no apportioning). That is rule 14's preferred form, and it is weather-year data, so forecast-reproducible in the same way as the EIA-930 system series already read.
- This lane does not re-open SPP-93; its matrix cell stands.
- If the desk ever re-tests that topology, `uc-wind/rz_actual_hourly_2019_2025.csv.gz` is the zone-resolved input it would need. The two-zone N/S build cannot use it without W1's estimate.

**W5 — Matrix.** No cell moves: no mechanism was tested and nothing was solved. The SPP shard is not edited.

## 7. Limits of this reading

1. **RZ membership** comes from SPP's settlement-location registry (`NODE_AREA` × `RESZONE`). RZ1/RZ5 ⊂ North and RZ3 ⊂ South hold by sub-BA. A stray plant node (KCPL's 41 RZ1 nodes are Missouri, so still North) does not move a pure zone across the seam.
2. **Measured actuals are SPP's delivered output.** The model carries uncurtailed potential, so only shares are compared outside the shortage hours.
3. **The pure-zone ratio** compares the extremes of each zone, not zone totals. It shows the *gradient* was real; it does not measure Oklahoma vs Kansas directly.
4. **Implied N→S** inherits the scarcity finding's construction: seam-leg bounds, CEMS coverage, and `emergency_band` not credited.
5. **The hour mapping** follows the model clock as above; ±1 h moves ΔS by ≤ 0.35 GW.
6. **No plant-level hourly wind source** (SCADA, settlement meter) is public for SPP. The Kansas/Oklahoma split inside RZ2+RZ4 stays unmeasured hourly. An SPP data request for RZ-by-sub-BA actuals, or a finer reserve-zone split, would close it. That is an owner download / request item, not available here.

## 8. Provenance

- Inputs:
  - The keeper's own recipe (`results/calibration/closeout_spp_nuc_span/run_config_<y>.json`) through `market_sim.data.renewables.load_renewable_profiles`, on clean data from `scripts/regenerate_clean.py --solve-profile SPP` at `be5fb748`. Data layer only; no LP was built.
  - The scarcity finding's `slack_hour_attribution.csv` / `implied_ns_transfer.csv`.
- Scripts (`uc-wind/`), run from the repo root in this order: `fetch_reduce_rz_actuals.py`, `f923_swpp_vre_monthly.py`, `model_zone_vre.py` (needs `PYTHONPATH=.`), `compare_wind_split.py`.
- No solve, no `src/` edit, no deletion of any registered result.
