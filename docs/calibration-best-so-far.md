# ERCOT calibration — best config so far

> **STATUS (2026-06-22): NEW KEEPER — run144 = run143 re-solved on the LOCAL
> (seasonal) net-load outage band.** `results/calibration/ercot_dam_2023as_localband`
> (dashboard `run144 local-band outages`). This is a **byte-faithful re-solve of
> run143** (the reproduce driver `scripts/probes/_keeper_2023as_run.py`: measured-
> 2023 storage-AS commitment + load-RRS-UFR credit, ST_GAS committed delta restored
> to 0.0, storage-AS-from-year 2025, ECRS off) changing **nothing but the outage
> input**. The ERCOT outage CSVs (`data/raw/campd-outages.csv`,
> `campd-unit-outages.csv`) were regenerated (commit `152bb99`) on the LOCAL
> seasonal net-load band — `high_load_mask` now compares each hour to a centered
> rolling ±30-day net-load percentile instead of the single annual percentile,
> which **restores the real multi-week shoulder CCGT maintenance** the over-tight
> annual band wrongly dropped as economic idle (ERCOT CC outage GW-days **2906 →
> 5997**, still −36% vs unfiltered; short economic-idle still dropped; summer
> preserved). See `docs/ercot-outage-sensitivity-middle-ground-2026-06.md` and the
> non-negotiable rules in `docs/multi-iso/cross-iso-outage-regate-handoff-2026-06.md`.
>
> **Gated CLEAN vs run143 (demand-weighted system LMP; act in parens):**
>
> | year | run143 avg→new | run143 MAE→new | h>$200 143→new (act) | h>$500 143→new (act) |
> |---|---|---|---|---|
> | 2023 | 36.5 → 35.2 | 12.0 → 14.0 | 104 → 89 (181) | 56 → 51 (104) |
> | 2024 | 23.2 → 25.4 | 9.6 → **7.1** | 22 → 33 (53) | 16 → 23 (16) |
> | 2025 | 31.4 → 32.5 | 2.9 → **2.0** | 1 → 1 (31) | 0 → 0 (3) |
>
> Mean monthly demand-weighted LMP MAE **8.2 → 7.7**. The **expected direction
> holds**: more shoulder CC offline → CC_REGULAR grid −2.6 TWh in 2024 (160.42 →
> 157.80), displaced to ST_GAS (+2.0, toward bench) and CT_PEAKER (+0.8); 2024/2025
> shoulder prices firm modestly toward actual but stay **cooler than the pre-fix
> VOLL over-fire** (Oct-2024 model $22 vs actual $24 — no shoulder over-fire). Summer
> roughly preserved. **One honest flag:** the 2024 summer tail firms (h>$500 16 →
> 23 vs actual 16) — a modest firming in real scarcity months (Aug max $5000), **not**
> the shoulder economic-idle re-inflation the exercise guards against; the tail did
> not collapse. 2023 monthly MAE rises +2.0 from a deeper summer under-fire — 2023 is
> structurally out-of-market (~42% of 2023 $, run140), no outage lever reaches it.
> **No class regresses** (every in-scope fail moves toward bench); **fuel split passes
> all 3 years** (2023 gas −1.5%/coal +0.3%; 2024 +1.3%/−0.6%; 2025 +0.6%/+0.1% vs
> EIA-930). Adopted on the more physically-correct outage input (claude.md: prefer
> measured/defensible over what-fits) **and** it gates a touch better.
>
> **Determination (`scripts/calibration_verdict.py`): NOT-YET.** C6 governance
> **attested PASS** (`calibration_attestation.json` committed in the bundle: byte-
> faithful, exogenous net-load outage filter, no residual fit, no pinning). The
> run stays NOT-YET only because the documented structural ERCOT misses exceed the
> hard caveat budget (2 hard criteria caveated vs 1 allowed) — CT non-CEMS peakers,
> the CC nodal-congestion residual (measured zonal-LP NO-GO), the ST_GAS committed/
> AS-held wedge, the cheap-gas 2024 coal split, and 2023's out-of-market tail, all
> ledgered as ACCEPTED MEASURED-INPUT LIMITATIONS. **Same lineage status as run143**
> (which carried these too, un-attested); the rubric is built to fail a keeper that
> still carries documented structural limitations. Supersedes run143; everything
> below (the run-115b→run143 lineage and the success bar) is retained as history.

> **STATUS (2026-06-17): NEW KEEPER — run 124 = run 121 + `--storage-as-commitment`
> (the measured storage AS-aware design).** `results/calibration/run124_storage_as_keeper`
> = run 121's exact config (CT deployment OFF, `battery_dispatch_adder=10`,
> merit-ramp CC, cc-duct, storage vintage COD ramp) **plus** the measured hourly
> storage up-AS power reservation. ERCOT batteries clear ~2.0 GW (2024) / 2.8 GW
> (2025) of their power as ancillary services (RegUp+RRS+ECRS); that power is
> committed and cannot also arbitrage energy. `--storage-as-commitment` subtracts
> the measured per-resource-type storage-AS MW
> (`data/raw/ercot-AS/ercot_<yr>_as_by_restype_hourly.parquet`, `storage`
> column; Reg-Down and offline Non-Spin excluded) from the battery dispatch power
> cap, pro-rata by available power. **Adopted for ACCURACY, not fit** (claude.md:
> prefer measured/defensible over what fits) — the energy-only LP otherwise dumps
> the full battery fleet into a handful of hours (2024 peak **5.93 GW** in 451 h);
> the reservation caps that to a **physical 4.59 GW** spread over 511 h and lands
> the 2024 storage benchmark dead-on (discharge 0.781 → **0.728 TWh** vs EIA-930
> **0.722**; charge 0.857 vs 0.870). **12 unphysical >4.6 GW dump hours eliminated**
> (a battery holding 2–4 GW of AS cannot also deliver 5–6 GW of energy).
> **Scores identical to run 121** — same **5 fails @0.5%** (CT_PEAKER 2023/24,
> CC_REGULAR 2024/25, COAL_PRB 2024), **7 @0.33%**; **cf_emd [7c] 18/18 PASS**
> (several marginally better: CC_CHP, CT_PEAKER 2024, ST_GAS); **CO₂ 8/9** (2024
> coal −7.0% residual, unchanged). Supersedes run 121.
>
> **Key tuning finding (the "trade the magic number for data" experiment):** the
> measured AS reservation **complements, does not replace,** `battery_dispatch_adder
> =10`. The two discipline different things — the **adder** is the throughput/
> degradation + AS-opportunity cost that bounds storage **energy** (total cycling);
> the **AS reservation** is the measured physical commitment that caps the **peak**
> (power). Dropping the adder to 0 with the reservation on **explodes** 2024 storage
> to **2.72 TWh** (3.8× the 0.722 benchmark; charge 3.21 TWh) and regresses
> CT_PEAKER's hourly r (0.466 → 0.445, [7c] FAIL) — the reservation caps only the
> high-AS peak hours, while zero cycling cost lets the LP over-cycle in 2059 other
> hours. With both on, energy lands at +0.8% of benchmark (no over-suppression =
> no harmful double-count). adder=10 stays — it is a defensible degradation VOM
> (`ScenarioConfig.battery_dispatch_adder`, forecast-applicable), not a CEMS-pinned
> magic number. **Market-integrity:** no double-counting (`as_revenue_enabled` OFF
> in the P1 backcast — that path only feeds the capacity screens; ORDC overlay
> `ordc_as_plan_mw` netting OFF; the reservation touches only the storage power
> cap). Reg-Down correctly excluded; per-restype reconciles with NP3-911 (2025
> +40 MW, 2024 conservative −600 MW). RTE 0.850 (exact target), zero
> simultaneous-charge/discharge hours, zero deliverability violations. **2023
> storage-AS is an ESTIMATE** (intensity transfer from 2024 × EIA-860 COD fleet
> ratio, ECRS zeroed pre-June; `build_ercot_storage_as_2023_estimate.py`); 2024/25
> are measured. Reservation reserves **power, not SOC** — first-order-correct for
> the energy backcast (SOC reservation is a forecast-only AS-deliverability
> refinement, not needed here). NOTE: the earlier single-year probes run 122
> (2024) / run 123 (2023 est) had **CT deployment ON** — they were *not* clean
> run 121 + storage-AS; run 124 is the clean 3-year keeper-grade reproduction.
>
> Reproduce:
> ```
> python scripts/run_calibration_full.py --year 2023 2024 2025 \
>     --storage-daily-cycling --battery-adder 10 --storage-as-commitment \
>     --offer-curve-delta-json data/raw/_validation-source/offer_curve_deltas_cc_merit_ramp.json \
>     --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
>     --prb-floor 0.73 --prb-follower-floor 0.63 \
>     --curve-mid 0.35 --btm-backfill-year 2024 --cc-duct-peaking \
>     --wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP
> ```
> (storage vintage COD ramp auto-enables for ERCOT; CT deployment stays OFF.)

> **STATUS (2026-06-16): prior keeper — run 121 = run 120 + ERCOT storage vintage
> (COD) ramp.** Adopted because it is **more accurate**, not because it fits
> better (claude.md: prefer measured/accurate inputs over what fits the
> backcast). ERCOT storage was using each year's flat year-end battery fleet;
> run 121 ramps each unit's dispatch power/energy caps month-by-month from its
> EIA-860 COD, so spring/summer availability in the growth years is now correct
> (2025 storage discharge drops in Jan–May and converges to full by December).
> Effect on volumes is small and correct-direction (CC_REGULAR 2025 +3.62 →
> +3.11). **Same fail set as run 120: 5 at the 0.5% universal gate** (CT_PEAKER
> 2023/2024 honest under-run, CC_REGULAR 2024/2025 residual, COAL_PRB 2024
> cheap-gas), 7 at 0.33%. Everything else identical to run 120 (merit-ramp CC
> shape fix, CT deployment OFF, no magic numbers; published ORDC overlay as the
> default price line). The open CC over-run is now believed to be partly an
> AS-withholding effect (energy-only LP holds zero ancillary services; ERCOT
> held ~6–8 GW with ECRS new in June 2023) — the next defensible lever, scoped
> for a separate session. Supersedes run 120/run 115b.
>
> **STATUS (2026-06-16): prior keeper — run 120, the forecast-defensible config
> (user directive).** `results/calibration/run120_meritramp_defensible` =
> run 115b **+ the merit-ramp CC shape fix, with the CT AS/RUC-deployment
> overlay turned OFF**. The user set a hard defensibility principle: keep only
> mods that are physically/contractually real AND carry into the 2026–2050
> forecast (unit outage overlays, take-or-pay coal sigmoids, lignite must-run,
> cc-duct manufacturer spec, structural offer-curve shape fixes, actual fuel);
> drop every CEMS-pinned "magic number" with no forward analogue (the CT
> deployment floor, the spatial reliability-deployment floor, multi-pocket
> floors). Result: **5 in-scope fails at the 0.5% universal gate** — CT_PEAKER
> 2023/2024 (the *honest* under-run now that the CEMS floor is gone: an
> energy-only LP cannot dispatch out-of-merit AS/RUC peaker energy, and there is
> no defensible forward way to add it), CC_REGULAR 2024/2025 (the
> spatial-irreducible residual — the binding congestion is **nodal, not zonal**:
> 94% of SCED binding-constraint rent is on <200 kV local pockets, so finer
> zones would not bind; see `docs/audit-followup-tests-2026-06.md`), and
> COAL_PRB 2024 (cheap-gas economics, justified). The merit-ramp **fixes the
> CC_REGULAR operating-shape failure** (cf_emd 0.099/0.105/0.113 →
> 0.088/0.098/0.101, the new `[7c]` gate). CO₂ 8/9 (2024 coal residual). Carries
> the published ORDC overlay (display-only, now the dashboard's default ERCOT
> price line). Supersedes run 115b/run119. The run-115b block below is retained
> as history (it scored 5 fails too, but with the CT floor papering over the
> peaker under-run — less defensible).
>
> **STATUS (2026-06-14, post-run-115b): prior keeper — run 115b, the per-plant
> CC duct-firing overlay + PRB-floor ease on top of run 109a.** The run-110→117
> campaign added a measured per-plant CC peak-band structure (each CC plant's
> duct-firing band sized from its EIA-860 nameplate-vs-net-summer gap, the
> duct-burner flag) and eased the PRB floor 0.74 → 0.73. Run 115b is the keeper:
> **still 3 in-scope fails (CT 2023/2024, PRB 2024)**, and it **fixes CC_REGULAR
> 2023** (−2.3% → −0.8%) and **re-centers CC_CHP** (was running +7/+7/+10% hot,
> now +0.6/+0.8/+3.8% — the duct mechanism strips the phantom peak band off
> non-duct CC plants), with the 2023 coal split now passing (+2.2%) and the LMP
> gate held (32.5 / 8.1 / 2.2 energy-only). Supersedes run 109a. See the "ERCOT
> Runs 110–117" log entry. (run 97a remains the documented prior-prior keeper and
> the basis the campaign stands on; run 109a is the immediate predecessor.)
>
> **Accepted cost (user sign-off 2026-06-14):** the CC duct lift displaces
> CT_PEAKER in the merit order, so CT deepens vs run 109a (2023 −0.53 → −1.61,
> 2024 −0.55 → −2.10 TWh). This is **intrinsic to the CC fix, not the ST relief**
> — easing the relief 0.06 → 0.085/0.10 (runs 117a/b) barely moves CT (+0.1 TWh)
> but craters ST 2024 into a fail, so 0.06 is the correct relief. CT was already
> the documented non-CEMS-peaker fail in run 109a; it is carried deeper here as
> the price of fixing the ±20-TWh CC class and grounding the CC peak band in
> EIA-860 rather than hand-set values. **PRB 2024 is left lumpy (−10.3%) by
> choice:** the 2024 anomaly is *justified* (the LP correctly idles loss-making
> self-committed/contracted coal that ran 40–52% CF while $2.19 gas made it
> uneconomic — no outage), so per the user's standing condition ("prefer 0.71
> unless we find justification for the 2024 anomaly") the floor stays at 0.73
> rather than forcing an even PRB at 0.71, which would over-run 2023 coal (split
> +3.8%) and breach the Limestone guard (runs 114a/116b).

> **CANDIDATE KEEPER (2026-06-16, audit follow-up D4): merit-ramp CC shape fix.**
> `results/calibration/d4a_meritramp` = run 115b **+ the CC_REGULAR merit-ramp
> econ deltas** (`data/raw/_validation-source/offer_curve_deltas_cc_merit_ramp.json`:
> econ_low −0.24 / econ_high −0.20, restoring a rising econ ramp). It **fixes
> the CC_REGULAR operating-shape failure** (the missed >90% CF hours): per-class
> cf_emd 0.099/0.105/0.113 → 0.088/0.098/0.101 and hourly r 0.74 → 0.76, with
> the new `[7c]` regression gate 18/18 PASS (no class regresses), and it cuts
> the CC over-run (2024 +6.31→+5.18, 2025 +3.61→+2.77 TWh). Cost: CC 2023
> over-corrects low (−2.08, a 0.6-TWh fail at the 0.33% gate, so 6 in-scope
> fails vs run115b's 5). Reproducible from the committed deltas alone. **Same CC
> delta set as run119** (dashboard probe = merit-ramp + a CPS
> local-reliability-mustrun floor, whose mechanism + bundle are not in the
> repo). **Keeper of record stays run 115b** — promote the candidate when the
> spatial axis closes the residual CC 2024/25 volume over-run (measured *not*
> offer-closable: run118 spatial overlay weak, run119 CPS floor weak, finer-zone
> topology now a **measured NO-GO** — 2026-06-17 nodal-pockets session:
> over-run is in North, no unmodelled aggregate GTC isolates it; Permian binders
> are diffuse <200 kV (no export GTC); the one clean unmodelled GTC, VALEXP/RGV,
> is in South + an export limit on a load pocket; a forced North-bind moves only
> ~2.5 of +4.5 TWh and substitutes fuel — see calibration-log). Cheapening the
> duct wall (d4b) was rejected (no shape gain, worse volume). See
> `docs/audit-followup-tests-2026-06.md`.

Keeper: **run 115b / bundle `results/calibration/run115b_ccduct_prb73_relief06`**
(2026-06-14, highspy 1.14.0). Run 115b = run 109a's config **plus** the per-plant
CC duct-firing overlay, with the PRB floor eased one notch and the ST relief
re-threaded for the new equilibrium:

- **`--cc-duct-peaking` (the run-115b structural add):** each CC_REGULAR /
  CC_CHP plant's peaking-tranche % is sized from its **EIA-860 duct-burner flag**
  — duct-fired plants get their nameplate-vs-net-summer capability gap as the
  expensive peak band, non-duct CC plants get **0** (no phantom scarcity band on
  a plant that physically cannot duct-fire). Supersedes the offer curve's
  class-wide `pct_peaking`; the band heat-rate multipliers still apply on top,
  plants absent from the EIA-860 sheet keep the class value, and the ERCOT
  hand-set `CC_REGULAR_PEAKING_PCT_BY_PLANT` map stays the final word for its
  plants. Built from `fleet.cc_duct_peaking_pct()`; applied in
  `fleet.generators_to_fleet_arrays` (`ScenarioConfig.cc_duct_peaking`).
  **Fixes CC_REGULAR 2023 (−2.3% → −0.8%)** by moving the peak band to where the
  duct firing actually is, and **re-centers CC_CHP** (+7.3/+7.0/+10.4% →
  +0.6/+0.8/+3.8%) by removing the phantom band from non-duct CHP. Default off —
  forecast mode and other ISOs are byte-identical (no-op without the flag).
- **`--prb-floor 0.73 --prb-follower-floor 0.63`** (was 0.74 / 0.64): one notch
  cheaper, nudging the PRB multi-year mean toward center (−3.7% → −3.3%) and
  lifting 2023 PRB to +0.9% while keeping the **2023 coal split passing (+2.2%)**
  and the Limestone/Martin Lake guards clean. NOT eased to 0.71/0.72 (the user's
  even-PRB ideal): at those floors the evened 2023 PRB *is* an over-run of the
  2023 coal plants (split +3.0/+3.8%, Limestone guard breach — runs 114a/116b),
  and the 2024 PRB low is independently justified (self-commitment, see below),
  so the lumpy PRB is left honest at 0.73 rather than force-flattened.
- **`--ct-deployment`** (unchanged from run 109a): the measured per-plant hourly
  CT out-of-merit floor; see the run-109a bullet retained below.
- **`--wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP`** (was 0.11):
  the cc-duct lift re-orders the low-merit stack, so the ST_GAS/ST_CHP relief is
  re-threaded to **0.06** to hold ST 2024 in the new equilibrium (2023
  +5.8%/+0.97, 2024 −4.2%/−0.76, 2025 +3.2%/+0.49 — all pass). This is the
  correct level, not over-relief: easing it back toward 0.085/0.10 (runs 117a/b)
  fails ST 2024 while barely sparing CT (the CT deepening is cc-duct-intrinsic).
- **`--lignite-floor 0.675`** (unchanged from run 109a): lignite sigmoid
  passthrough floor; 2023 +6.0%/2024 −6.1% both pass.

**Retained run-109a foundation** (the gas-side structural unlock 115b builds on):

- **`--ct-deployment`** (CT AS/RUC-deployment overlay): a measured per-plant
  *hourly* min-generation floor pinning each CEMS-covered simple-cycle peaker to
  its observed net output ONLY in the out-of-merit hours where the RT price was
  below the unit's marginal cost — the IMM-documented AS / reliability-unit-
  commitment + reserve-adequacy wedge the energy-only LP cannot dispatch.
  Measured 1.34/1.88/2.22 TWh out-of-merit (29.9/35.0/42.5% of covered CT CEMS
  energy). In-merit hours stay economic (CT not floored to full CEMS); a pure LP
  min-gen bound (no MIP — prices stay LP duals). Built by
  `scripts/data/derive_ct_deployment.py` → `data/raw/_validation-source/
  ct_deployment_floor_ERCOT.parquet`.

Reproduce with:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 \
    --offer-curve-delta-json <run92/run96/run97a deltas> \  # run_config.json offer_curve_deltas
    --coal-lignite-sigmoid --lignite-floor 0.675 --lignite-ceil 1.00 \
    --prb-floor 0.73 --prb-follower-floor 0.63 \
    --curve-mid 0.35 --btm-backfill-year 2024 \
    --ct-deployment --cc-duct-peaking \
    --wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP
```

**The remaining 3 fails are all structurally diagnosed (do not chase):**

- **CT_PEAKER 2023/2024** (−1.61/−2.10): the deployment overlay recovers the
  CEMS-covered out-of-merit wedge (covered plants match CEMS), but ~1.0–1.2
  TWh/yr of bench sits in **non-CEMS small peakers** (Ector County, Permian
  Basin, Pearsall …) that have no hourly CEMS for the overlay to key off and that
  the merit order cannot reach. **Deepened vs run 109a** (−0.53/−0.55 → −1.61/
  −2.10) because the cc-duct CC lift displaces CT in the merit order — measured
  intrinsic to the CC fix (easing the ST relief 0.06 → 0.085/0.10 barely moves CT
  but fails ST 2024, runs 117a/b), not relief-driven. Accepted as the price of
  fixing the ±20-TWh CC class. Honestly diagnosed, not overlay-reachable.
- **COAL_PRB 2024** (−10.3% / −4.49 TWh): the documented cheap-gas year-gradient
  residual (run 90). **Justified, left lumpy by choice:** the 2024 low is the LP
  correctly idling loss-making self-committed/contracted coal — the plants ran
  40–52% CF while $2.19 gas put them below their marginal cost, no outage. Per
  the user's standing condition ("prefer 0.71 unless we find justification for
  the 2024 anomaly"), the justification holds, so the floor stays at 0.73 and the
  spread is carried under the PRB carve-out. Do NOT chase (cheapening PRB to
  0.71/0.72 floods 2023 coal — split +3.0/+3.8% + Limestone guard breach, runs
  114a/116b; the CC and ST bid levers crater their classes — runs 101/105/109b).
- **2024 coal split** (−9.3%, ~unchanged from run 109a's −9.5%): the cheap-gas
  PRB/lignite residual; the **2023 coal split now passes (+2.2%, was over at the
  0.71/0.72 probes)** with the 0.73 floor. The gas split holds (+1.0% in 2024).
  *PRB per-plant detail (the run-90/97a diagnosis, unchanged):* the 2024 PRB
  deficit is **distributed cheap-gas merit displacement across the whole fleet**
  — Spruce, Parish coal, Fayette, Limestone, Martin Lake, Coleto, offset by
  Sandy Creek — not one plant. The plants are **price-responsive and the model
  captures it** (W A Parish whole-plant +0.22 / −1.36 / +0.15 TWh vs CEMS
  2023/24/25, dead-on except the single cheapest-gas year; the earlier −3.7 TWh
  "self-commitment" was a split-plant diagnostic artifact, corrected in
  `_plant_hourly_fit`). Carry under the PRB carve-out; do **not** floor or
  re-benchmark it as price-blind.

**ST_GAS is no longer a structural fail** — run 97a left ST_GAS 2024 at −1.99
(the CPS steamers + Cedar Bayou, the committed band's startup amortization
capping the per-plant gain). The CT deployment floor + the ST_GAS/ST_CHP WEFOR
relief together fill it: the availability deficit run 97a diagnosed was real,
and with CT floored the relief lands without re-cratering CT to a fail.

## Success bar (size-aware)

**GRID-DELIVERED basis (2026-06-14, user directive).** Every gate below judges
what the LP actually dispatches to the grid against what actually reached the
grid: model = the grid LP dispatch (NO behind-the-meter CHP add-back), actual =
EIA-923 whole-plant **minus** the per-class BTM host supply (`btm.parquet`, the
authoritative BTM held out of the LP). The host steam is held out of the LP, so
crediting the model for it would score generation the model never optimized.
(The absolute TWh miss is identical to the old whole-plant basis — the BTM
cancels — so the ±1 TWh classes are unchanged; only the ±5% denominators are
now honest grid-delivered sizes.) The dashboard's class/system scorecard + mix
table use the same basis (`scripts/lib/session_score.py`, `render_calibration_html
.build_payload`); only the per-plant heatmaps stay whole-plant, because CEMS —
their comparison series — is itself whole-plant.

Judge each class by size, not a flat percentage (a flat % is loosest exactly
where the system mix is dominated):

- class total **≥ 20 TWh** (CC_REGULAR, CC_CHP, COAL_PRB): within **±5%** every
  year.
- class total **< 20 TWh** (ST_GAS, COAL_LIGNITE, CT_PEAKER, CT_CHP): within
  **±1 TWh** (absolute) every year.
- CT_CHP excluded (known CHP-benchmark gap; ~+49% on the grid-delivered 2025
  basis, where the grid-delivered actual is smaller than the whole-plant 923).
- **Fuel-split gate:** total gas and total coal **grid** generation each within
  **±2.5%** per year — model grid gas/coal vs (EIA-923 − BTM) gas/coal for
  2023/2024. **For 2025 the benchmark is EIA-930** (the 2025 EIA-923 is the
  incomplete monthly-survey vintage, so 923−BTM is unreliable; EIA-930 is itself
  grid-side and is the correct grid-delivered 2025 actual — `_session_score`
  switches source by year). The other year's source is shown alongside as the
  independent grid check; the two differ structurally (930 gas runs ~14% below
  923 gas on the ~35 TWh of BTM CHP host supply, so 930 ≈ 923−BTM). On the keeper
  the 2024 gas split sits at +1.0% vs 923−BTM / +4.2% vs 930, and the 2025 gas
  split at +2.2% vs 930 / +3.6% vs 923−BTM. **solar/wind are benchmarked against
  EIA-930 only** and sit outside this gate.
- PRB carve-out (user judgment, 2026-06-12): PRB stays on the ±5% class bar
  and its year-to-year spread is accepted as long as the multi-year mean is
  centered (the run-90 gradient finding: 2023 responds at ~2.2× 2024 per
  unit passthrough, so a per-year PRB fix structurally over-trades).
- LMP gate: monthly demand-weighted LMP MAE vs actual RT within **±$1/yr**
  of the corrected-fleet baseline (32.1 / 7.3 / 2.2 — run 92), defined on
  the **energy-only LMP** (raw duals). The ORDC overlay series
  (`lmp_scarcity`) is additive and never gates volumes or LMP.

Never regress a class vs the keeper — **with one signed-off exception:** run 115b
carries CT_PEAKER deeper than run 109a (2023/2024 −1.61/−2.10 vs −0.53/−0.55) as
the measured, intrinsic cost of fixing the ±20-TWh CC class (the cc-duct lift
displaces CT in merit order; not relief-reachable, runs 117a/b). Run 115b's three
fails (CT 2023/2024, PRB 2024) are the structurally diagnosed set above. Honest
caveats: the 2024 coal split is −9.3% grid-delivered (the cheap-gas PRB/lignite
residual), CT runs deep (above), and PRB's multi-year mean sits at −3.3%
(+0.9 / −10.3 / −0.6, lumpy-but-justified, see the COAL_PRB 2024 bullet).

## Config (the knobs that matter)

- **CC duct-firing peak band (the run-115b structural add):**
  `cc_duct_peaking = on` (`--cc-duct-peaking`). Sizes each CC_REGULAR/CC_CHP
  plant's peaking tranche from its EIA-860 duct-burner flag (nameplate-vs-net-
  summer gap; non-duct plants → 0). `fleet.cc_duct_peaking_pct()`; the hand-set
  `CC_REGULAR_PEAKING_PCT_BY_PLANT` map still overrides for its plants. Fixes
  CC_REGULAR 2023 and re-centers CC_CHP. Default off — other ISOs/forecast
  byte-identical. (`cc_peaking_per_plant`, the offer-curve-`pct_peaking` analogue,
  stays a separate off-by-default knob.)
- **CT AS-deployment overlay (the run-109a structural unlock):**
  `ct_deployment_overlay = on` (`--ct-deployment`). The per-plant hourly
  out-of-merit floor; see the keeper bullets above and
  `scripts/data/derive_ct_deployment.py` / `outages.ct_deployment_floor_for_year`.
  `ct_deployment_floor_frac = 1.0` (the full measured wedge; a safety knob to
  dial back if a year overshoots its CT bar). Default off — forecast mode and
  any other ISO are byte-identical (no artifact → no-op).
- **ST availability relief (run-109a Phase-2 retune, re-threaded in run 115b):**
  `wefor_residual = 0.06` scoped to `wefor_residual_groups = {ST_GAS, ST_CHP}`
  (`--wefor-residual 0.06 --wefor-relief-groups ST_GAS,ST_CHP`). Caps the
  ST_GAS/ST_CHP forced-outage rate at the 6% short-outage residual (the CAMPD
  overlay carries the ≥5-day events). Lands only because CT is floored first; the
  level dropped 0.11 → 0.06 to hold ST 2024 once the cc-duct lift re-ordered the
  low-merit stack (0.085/0.10 fail ST 2024, runs 117a/b).
- `td_loss_factor = 0.0` (EIA-930 demand is generation-side; no gross-up).
- Locked tier-pass-2 family: per-plant CAMPD coal must-run, gas-keyed PRB
  passthrough sigmoid (baseload + follower tiers), `coal_drop_pof`,
  historic outage overlay, per-plant monthly coal pricing — all defaults of
  `run_calibration_full.py`.
- Coal passthrough sigmoids:
  - `coal_lignite_passthrough_sigmoid = on`, **floor 0.675** (the run-109a
    thread to recover the CT-displaced lignite 2024; was 0.69 run 96→97a,
    0.75 run 85→95b) / ceil 1.00.
  - `coal_prb_passthrough_floor = 0.73`, `coal_prb_follower_floor = 0.63`
    (run 115b eased one notch from 0.74/0.64; NOT 0.71/0.72 — those over-run
    2023 coal, runs 114a/116b).
  - Gas-mid/slope at the built-in defaults (2.85 / 2.5) for all tiers (the
    run-90 year-gradient finding: do NOT retune these for 2024).
- **`offer_curve_smoothing_mid = 0.35`** (`--curve-mid 0.35`, the run-89 add).
- Fleet: **Kiamichi (EIA 55501) is in the registry + bins** (the run-92 fix)
  with the run-94 cost-side trim committed (split 20/65/15, econ HR mult
  1.06). It still over-runs its EIA actual (6.0/6.8/6.2 TWh vs ~5.2) —
  a within-class watch item; the capacity-withholding trim (peaking share
  15 → 30) was measured dead in run 95 (the over-run is bid-price-driven).
- Per-plant committed shares (the run-97a adds): **Braunig (3612) and
  Sommers (3611) `Pct_Committed` 40** (was 30). NOTE for future per-plant
  CC moves: `cc_committed_per_plant`/`cc_peaking_per_plant` override the
  CSV shares for CAMPD-covered CC plants (the Sand Hill 7900 edit was a
  measured no-op; Kiamichi takes CSV values only because it has no CAMPD
  extract) — per-plant CC offer surgery needs `--plant-tranche-config`.
- **`--btm-backfill-year 2024`** (the run-97a add, in the keeper command):
  CAMPD-gated prior-year 923 carry for plants missing from the incomplete
  2025 vintage (San Jacinto's CT_PEAKER add-back).
- `storage_daily_cycling = on`; **`battery_dispatch_adder = 10.0`** $/MWh;
  nuclear per-year EIA-923 monthly CF overlay (−0.7%/yr).
- Full offer-curve deltas vs calibrated defaults (identical to run 92/91,
  recorded in the bundle's `run_config.json`): CC_REGULAR {committed −0.05,
  econ_low −0.10, econ_high −0.40, peak +0.32}; CC_CHP {econ_high +0.43,
  peak −0.50, pct_peaking −4}; CT_CHP {committed −0.20, econ_low −0.08,
  econ_high +0.10, peak −0.08}; CT_PEAKER {committed −0.34, econ_high
  +0.20}; ST_GAS {committed −0.385, econ_low −0.13, econ_high −0.35, peak
  −1.0}; COAL_PRB {committed −0.04, econ_low −0.30, econ_high +0.44, peak
  +0.082}; COAL_LIGNITE {committed −0.07, econ_low +0.076, econ_high −0.037}.
- **ORDC scarcity overlay** (`docs/ordc-overlay.md`): the post-solve
  baseline bundle is now **run109a_relief11_lig675** (moved from run97a);
  `availability.parquet` + `scarcity.parquet` (flat 1400/shift0.5 default) +
  `scarcity_np6shift0.parquet` (published NP6-576-ER table, `--shift 0`,
  canonical) are committed in the bundle. 2023 energy-only LMP MAE 32.3 → 29.3
  with the adder (8% of the summer gap, 22 h >$200 vs 0); 2024/2025 hold the
  ±$1 gate (7.8 → 7.5, 2.1 → 2.1). The published NP6-576-ER seasonal μ/σ table
  (`data/raw/_validation-source/ercot_ordc_lolp_params.csv`, user-fetched 2026-06-13)
  is used with `ordc_lolp_shift_sigma = 0` (the published Average embeds the
  PUCT 0.5σ shift; μ/σ ≈ 0.68 in every season).

## Results (P1, run 109a, GRID-DELIVERED: model grid vs EIA-923 − BTM)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −2.3% | +2.9% | +0.9% |
| CC_CHP | +1.6% | +1.1% | +3.5% |
| COAL_PRB | +0.0% | **−10.6%** | −0.6% |
| COAL_LIGNITE | +6.0% (+0.92 TWh) | −6.1% (−0.85 TWh) | +2.0% |
| CT_PEAKER | **−15.5% (−1.08)** | **−21.0% (−1.55)** | +2.5% (+0.16 TWh) |
| ST_GAS | +5.4% (+0.91) | −5.1% (−0.93) | +1.7% (+0.26 TWh) |
| nuclear | −0.7% | −0.7% | −0.7% |
| fuel split gas/coal | −2.0 / +1.6% | +0.5 / **−9.5%** | (see 930) |
| LMP MAE vs actual RT ($/MWh, energy-only) | 32.3 | 7.8 | 2.1 |

(Grid-delivered shifts the ±5% denominators vs the old whole-plant table — the
CHP classes most, e.g. CC_CHP +1.0% → +1.6% on the smaller grid actual — but
the absolute TWh misses and the pass/fail verdicts are unchanged.)

Bold = the 3 in-scope fails (CT 2023/2024, PRB 2024) + the carried 2024 coal
split. Unserved energy 0.000 in all years. Plant guard: Martin Lake /
Limestone 2023 at +380/+704 GWh; Martin Lake 2025 +1.43 TWh (the same watch
item as run 97a — unchanged by this campaign). Vs run 97a: ST_GAS fixed all
three years (2024 −11.0% → −5.1%), CT 2023/2024 improved (−1.53/−2.56 →
−1.08/−1.55), CT 2025 still passes; cost is the 2024 coal split −8.5% → −9.5%
(CT out-of-merit gas displacing marginal cheap-gas PRB) — the documented,
accepted tradeoff (user sign-off 2026-06-13).

## History

Run 97a (`run97a_gas_plants`, 4 fails) was the keeper through 2026-06-13 and
is the basis run 109a stands on; the run-103→109 campaign ("ERCOT Runs
103–109") built the CT AS-deployment overlay (the candidate mechanism run 97a
flagged) and re-ran the ST availability relief on top of it, naming run 109a
(3 fails). Before run 97a:
Run 96 (`run96_lignite_keeper`, the lignite-floor move, 5 fails) was the
keeper for the first half of 2026-06-12→13; run 92 (`run92_kiamichi`, the
Kiamichi fleet fix) is the corrected-fleet baseline both stand on; run 91
(`run91_cc_shave055`) was the last pre-fix keeper and is not reproducible
on current inputs; run 85 (`run85_coal_soft`) before it. Runs 93/94/95/95b
are the measured class-lever probes ("ERCOT Runs 93–96" log entry) and
runs 97a/97b the per-plant campaign ("ERCOT Runs 97a/97b") — 97b measured
the coal committed-share lever backfiring under the commitment screen.
Bundles stay in `results/calibration/`. Structural follow-ups: the
CT/Parish AS-deployment + self-commitment wedge (an explicit deployment
overlay from measured out-of-merit CEMS hours is the candidate mechanism),
the Sand Hill per-plant tranche config (its CT capacity dispatches at the
blended 7.37 CC heat rate — ~1.5 TWh of the CC 2024 over-run), the CT_CHP
2025 benchmark gap, and the NP6-576-ER seasonal μ/σ table for the ORDC
overlay (ercot.com egress-blocked again 2026-06-13).
