# FINDING — PJM-NEXT-17: the COAL_BIT over-run is econ-band loading, diffuse; a plant-conduct CC window barely moves the off-hour floor (zero LP)

**Keeper:** `2026-09-30-pjm-next16-ovec` (bundle `results/calibration/pjmnext16_A_span`), unchanged.

**Probes** (zero LP; outputs committed next to them):
- `scripts/probes/_pjmnext17_coal_census.py` → `results/calibration/_pjmnext17_coal_census.json`
- `scripts/probes/_pjmnext17_cc_conduct_window.py` → `results/calibration/_pjmnext17_cc_conduct_window.json`
- `scripts/probes/_pjmnext17_coal_offer_audit.py` → `results/calibration/_pjmnext17_coal_offer_audit.json` (§3)

## 1. Card 1 — where the COAL_BIT over-run sits

**Method.** The NEXT-16 partition is applied to bench COAL_BIT plant-hours: model payload `m` vs CAMPD rescaled to EIA-923. LOAD = both on; ON = model on only; OFF = actual on only. Night is HE 24–07.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025* |
|---|---|---|---|---|---|---|---|
| C1 COAL_BIT (gated) | **+18.71** | **+11.92** | **+17.14** | +6.79 | +0.27 | +0.88 | (+11.3) |
| bench gap | +16.0 | +11.3 | +15.4 | +8.5 | +0.3 | 0.0 | +13.0 |
| LOAD | +15.0 | +12.4 | +15.0 | +5.6 | +2.7 | +1.3 | +12.5 |
| LOAD, night | +5.9 | +5.0 | +4.8 | +1.0 | +1.4 | +0.5 | +4.7 |
| LOAD by demand tercile (low / mid / high) | 3.4 / 5.1 / 6.6 | 2.1 / 3.7 / 6.5 | 3.7 / 4.9 / 6.3 | −2.1 / 1.1 / 6.6 | 0.9 / 1.1 / 0.8 | 1.2 / 1.1 / −1.0 | 3.9 / 4.3 / 4.3 |
| ON / OFF | +4.0 / −3.3 | +2.8 / −4.1 | +3.0 / −2.7 | +3.8 / −1.2 | +0.7 / −3.1 | +0.5 / −2.0 | +1.4 / −0.9 |
| model energy, econ bands | 70.9 | 46.8 | 69.2 | 46.2 | 16.6 | 21.0 | 38.1 |
| model energy, mustrun + committed | 111.4 | 99.6 | 100.3 | 95.8 | 83.8 | 81.3 | 93.3 |
| loading-when-on, model / actual (× nameplate) | 0.589 / 0.533 | 0.539 / 0.489 | 0.587 / 0.539 | 0.532 / 0.509 | 0.496 / 0.475 | 0.499 / 0.492 | 0.614 / 0.561 |
| hourly corr(Δcoal, ΔCC) | −0.20 | −0.45 | −0.25 | −0.30 | −0.25 | −0.19 | −0.26 |

\* 2025 C1 is SKIPPED (preliminary EIA-923); its row is reported, not gated.

**Readings.**
1. **The over-run is loading when on, and it sits in the econ bands.**
   - LOAD is 80–100 % of the gap in every over-run year.
   - The floor bands (mustrun + committed) are flat across years.
   - The gap scales with model econ-band energy: large where econ is 38–71 TWh, near zero at 17–21.
2. **It is a diffuse shift, not a pile-up at Pmax.**
   - The on-hour MW-h distribution moves from the 0.05–0.45 × nameplate bins into the 0.6–1.0 bins.
   - In 2019, the 0.75–0.9 bin carries 23.7 % of model MW-h vs 19.5 % actual.
3. **No plant or hour window carries it.**
   - About 30 plants contribute 0.5–2 TWh each in 2019–2021: Gavin 8102, Amos 3935, Rockport 6166, Clifty Creek 983, Fort Martin 3943, Mitchell 3948, Keystone 3136, East Bend 6018, …
   - It appears in every month and every demand tercile.
   - About two-thirds of it is daytime.
4. **The night term is not a coal/CC ordering swap.**
   - Night hours with coal over AND CC over outnumber coal over / CC under in 2019 (1,674 vs 797), 2020 (1,390 vs 672), 2022 and 2023.
   - That is system over-generation at night, the NEXT-16 card-1b export/`U_a` object.
   - Across all hours Δcoal and ΔCC anti-correlate (−0.19 to −0.45): within the day, coal displaces CC.
5. **Already refuted and not re-tested here:** offered EcoMax, outage windows, Pmax, AEP–West congestion, PJM's own offers, incremental-HR pricing, min-load repricing, self-scheduling, availability, replacement-cost fuel, and the band channel (no ex-ante value). See NEXT-10 §3, NEXT-11 to NEXT-14.

**Verdict, card 1:** located (econ-band loading, diffuse, two-thirds daytime). **No admissible, year-discriminating lever found.** It stays **OPEN**; this is not a model-class limit.

## 2. Card 2 — a plant-conduct window for `cc_mustrun_per_plant`

**Owner card:** *"Design + build"*. Before any build, the design was verified at zero LP, as card 3 requires.

**Design under test:**
- Size: the keeper's pooled `online_frac` × 8760 h, unchanged.
- Level and membership: committed tranche, unchanged.
- Hour selection: hours are ranked by the plant's **own** CAMPD online probability in the hour's conduct cell, ties broken by system load.
- The probability is pooled over the **other** bench years (leave-one-year-out), so no same-year outcome enters (rule 13).
- Cell grain was chosen by held-out conduct log-loss only, never by a C1 or price residual. Month × hour-of-day (288 cells) beats month × weekday/weekend × hour in every year (e.g. 2019 −0.436 vs −0.439).

**Result.** Committed-MW floor energy in hours the plant's meter reads offline (< 1 % nameplate), as an upper bound:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| plants floored | 61 | 61 | 65 | 67 | 69 | 69 | 69 |
| keeper window, TWh | 23.33 | 18.47 | 25.54 | 24.07 | 22.58 | 18.12 | 21.82 |
| conduct window, TWh | 21.88 | 16.88 | 25.35 | 22.66 | 19.96 | 16.12 | 19.42 |
| off-share of floored hours, keeper → conduct | 15.6 → 14.5 % | 13.6 → 12.5 | 17.0 → 17.0 | 14.8 → 13.9 | 13.7 → 12.2 | 11.7 → 10.7 | 13.4 → 12.1 |

- The conduct window removes **0.2–2.6 TWh/yr (1–12 %)** of the off-hour floor.
- About 90 % remains. Real CC off-hours are irregular relative to month × hour, so no calendar-cell window can reach them without reading the same-year meter, which rule 13 forbids.
- The NEXT-17 ON census agrees independently: only 1.4–3.0 TWh/yr of model-on/real-off CC energy falls in cells where the plant's own history says "usually off".
- Neither number varies by year in the C1 direction.

**Real-fleet check (owner: "Build + solve anyway", then verified before launch).** The field was built (`cc_mustrun_conduct_window`, default off) and two `fleet_only` rebuilds of the keeper were compared, flag off vs on (`scripts/probes/_pjmnext17_conduct_fleet_delta.py` → `results/calibration/_pjmnext17_conduct_fleet_delta.json`).

| floor in metered-offline hours, TWh | 2019 | 2021 | 2023 | 2025 |
|---|---|---|---|---|
| keeper | 3.306 | 4.508 | 2.815 | 2.883 |
| conduct window | 3.564 | 5.349 | 3.094 | 3.150 |
| change | +8 % | +19 % | +10 % | +9 % |
| CC floor energy, TWh (off → on) | 153.4 → 155.3 | 171.3 → 172.5 | 189.3 → 192.6 | 189.4 → 192.4 |

- **Wiring:** only CC must-run rows move (61–69 per year); no other row changes.
- **Why the real build reverses the census:**
  - In the real fleet, most metered-offline hours are already CAMPD outage windows, and the availability clip zeroes the floor there. That is why the keeper's real exposure is 2.8–4.5 TWh, not the census's 18–26 TWh upper bound.
  - The conduct ranking moves the window into cells the plant usually runs, which are mostly outside outage windows. More floor therefore lands in the plant's short, irregular, non-outage off-runs, and total floor energy rises 1–2 %.

**Verdict, card 2: REFUSED at zero LP** (owner card *"Refuse; keep built, off"*).
- The PRECOMMIT's structural condition (offline-hour floor falls in every year) fails in all four years checked, so no solve was spent.
- `cc_mustrun_conduct_window` stays in the code, default off. PJM matrix cell: **R**.
- **The rule-17 window question is now answered for PJM:** the off-hour floor is 2.8–4.5 TWh/yr, about 2 % of CC floor energy. It sits in non-outage short off-runs that no calendar-cell window reaches. This is sized and structural, and it is not a C1 lever.

## 3. Dispatch-vs-offer audit (owner card *"Dispatch-vs-offer audit"*)

**Question.** Do real PJM coal-like units under-dispatch their **own** offers at the actual price, while the model dispatches at its offers?

**Method.**
- Source: the PJM DataMiner2 offers corpus, 84 of 84 month-files for 2019–2025, re-fetched.
- Units: the LONG_RUN segment, using NEXT-11's physics segmentation.
- D = offer-implied MW at the actual DA LMP; Dm = the same at the keeper's own price.
- Comparison: CAMPD COAL_BIT against the model's COAL_BIT, through the ratio RoR = (actual/D) ÷ (model/Dm).
- Over-run split: price-level term = (Dm − D) × actual/D; conduct term = (model/Dm − actual/D) × Dm.

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| D / Dm | 176 / 208 | 162 / 217 | 200 / 231 | 184 / 190 | 129 / 153 | 136 / 154 | 178 / 196 |
| RoR | 1.07 | 1.24 | 1.05 | 0.97 | 1.18 | 1.12 | 1.00 |
| RoR, units floored at EcoMin | 0.97 | 1.04 | 0.97 | 0.95 | 1.05 | 1.03 | 0.94 |
| over-run | +18.2 | +11.7 | +16.0 | +9.0 | +0.5 | +1.2 | +13.3 |
| price-level term | +31.0 | +47.2 | +24.6 | +5.0 | +19.4 | +14.2 | +13.1 |
| conduct term | −12.7 | −35.5 | −8.7 | +4.0 | −18.9 | −13.0 | +0.2 |

**Caveats, stated:**
- LONG_RUN (40–52 GW EcoMax) is not COAL_BIT (33–48 GW nameplate). It includes 4–12 GW of gas-tracking units, and 23 GW in 2022, where the split is unreliable.
- D is a step reading that ignores commitment, congestion and offline units.
- Hours are aligned at lag 0.

**Readings.**
1. **Falsified as a year-discriminating lever.**
   - Real units do not under-run their own offers relative to the model more in the over-run years. RoR is 1.00–1.24 in over-run years against 1.12–1.18 in 2023/2024.
   - The EcoMin-floored variant (0.94–0.97 vs 1.03–1.05) breaks in 2020 and sits inside the population and alignment noise.
2. **Above $35, real units run 10–20 % further below their offers than the model does,** sitting 0.3–0.7 of the way from EcoMin to D. 2023 shows the same gap, so it does not order the years.
3. **On PJM's own offers, the model's price level is the largest term.**
   - The keeper's higher price, mostly in hours under $25, would add +13 to +47 TWh of coal. The model's own conduct offsets part of it.
   - This is the NEXT-11 audit (b) object: the model's price floor is too high in every year (implied heat rate at p10 of 6.9–8.4 vs 4.8–5.5).
   - It is large in 2023/2024 too, so it is not year-discriminating on its own. It is the common root shared with the C3a 2019/2020 bulk-level error.

**Verdict, card 3:** not reached. Neither card 1, card 2 nor the audit yields an admissible, year-discriminating, zero-DOF mechanism. All three objects stay **OPEN**, and none is called a model-class limit.

**Next measurement implied:**
- The low-price-hour price floor: why the model rarely prices below gas-CC cost when real PJM does in 26–45 % of hours.
- Joined with the NEXT-14 marginal-unit census, now across all seven years rather than 2020 only.
