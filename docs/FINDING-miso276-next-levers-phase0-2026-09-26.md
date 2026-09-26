# FINDING — miso-276: phase 0 on the three open MISO objects after the miso-275 promotion

```
LANE    : miso-276 (MISO lever queue §5.4; routed by RESULT-miso275 §3)
KEEPER  : 2026-09-26-miso-275-cc-exempt (results/calibration/miso275_span) — unchanged
LP      : none in this document (zero-LP phase 0; rule 29 clause-0 practice)
PROBES  : scripts/probes/_miso276_c3a2022_phase0.py  -> results/calibration/_miso276_c3a2022_phase0.json
          scripts/probes/_miso276_stack_phase0.py    -> results/calibration/_miso276_stack_phase0.json
          scripts/probes/_miso276_ofy_footprint.py   -> results/calibration/_miso276_ofy_footprint.json
DATA    : DATA PROFILE: miso
```

## 1. C3a 2022 (−15.4 %) is not the Elliott tail and not a flat level. It is the Indiana Hub premium in a congested year plus summer-peak depth.

**What the scorer actually compares.** C3a 2022 is scored on the **legacy equal-hour Indiana Hub** series (the
2022 bench part carries no `rt_lw`), **masked to Jan–Oct** because the staged RT actual covers 36.5 % of November
and 0.1 % of December (`actual_lmp.json` `rt_cov`). Model 60.05 vs actual 71.01 $/MWh.

**So Elliott (Dec 22–26) is not in the scored window at all.** The C3c tail (116 h > $200) is a separate,
already-ledgered object; it does not drive C3a 2022.

**Decomposition, Jan–Oct 2022 (hours with every zonal hub staged):**

| basis | actual $/MWh | model 60.05 vs it |
|---|---:|---:|
| Indiana Hub, equal-hour (the scored actual) | 71.01 | −15.4 % |
| Indiana Hub, load-weighted by system demand | 74.53 | −19.4 % |
| each model zone vs its own hub, load-weighted | 64.17 | −6.4 % |

The Indiana Hub premium over the load-weighted zonal-hub mean is **$10.36 in 2022**, against $1.0–3.3 in every
other year (2019 1.48, 2020 1.02, 2021 1.41, 2023 2.65, 2024 3.02, 2025 3.33). About 62 % of the scored gap is that
premium.

**Per zone, Jan–Oct 2022** (model vs own hub, load-weighted): West 57.5 vs 47.2; Plains 58.2 vs 57.3; Illinois
58.2 vs 67.3; Indiana 57.9 vs 74.5; East 58.2 vs 70.1; South 65.7 vs 65.2. The real system had a **$27 West→Indiana
spread**; the model's is $0.4. Two zones are right, the west is too high and the east too low: a missing-congestion
signature, not a level.

**Re-basing C3a is not a lever.** On the zonal-hub basis 2022 would pass (−6.4 %), but 2020 (+11.0 %) and 2023
(+10.1 %, train tier) would fail. Choosing a benchmark because it passes a gate is exactly what rule 1 (c) forbids,
and it is not proposed.

**What is left after the basis (−6.4 %)** is concentrated in the top of the distribution:
- by month: Jan–Mar model **above** actual (+$5–6), Apr–Sep **below** (−$5 to −$12);
- by actual-price decile: deciles 1–5 model high (+$0.6 to +$1.4 of gap each), decile 10 carries **−$7.3**;
- by hour: hours 14–18 carry the negative side.

**Stack at the top-decile actual hours (fleet_only rebuild, keeper recipe):** model system price $75 vs actual $163,
with **30.2 GW of fossil headroom** (CT_PEAKER 13.6 GW offered at $104–142 median/p90, ST_GAS 5.1 GW at $95–115, CC
3.2 GW). The model's highest system price all year is **$97.7**. CT_PEAKER runs 9.2 TWh vs 14.2 actual (C1 PASS,
−4.98). The model is long on supply at the summer peak and never reaches its own CT offers.

**Verdict.** No admissible lever in this lane:
- the offer channel is excluded without a new owner ruling, and a year-invariant band would not target a 2022-only
  congestion premium anyway;
- the congestion half is a topology object (West→East interface representation), the same "no north congestion"
  miso-270 found for Oct–Nov 2021. Routed, not solved;
- the peak-depth half (30 GW idle at the peak) is an availability question at summer peak (2022 forced-outage level),
  unlocalized here. Routed.

## 2. C1 ST_GAS 2019 (−8.46 TWh) is a held-out-year VINTAGE object, not merit and not availability

**Not availability.** Keeper fleet, 2019: ST_GAS available 70.6 TWh, dispatched 13.5 TWh, **0 binding hours**,
57 TWh of headroom. The FINDING-miso274 §2 test gives the same answer it gave for CC.

**Not a year-invariant offer object either.** C1 ST_GAS by year: −8.46 / −7.06 / −4.92 / −5.07 (2019–22) against
**−0.29** (2023) and −2.11 (2024). A single band multiplier, which the owner's channel requires (rule 1 (b)), would
lift 2023 as much as 2019. ST_GAS econ bands sit at ×1.0 over measured physics of 0.812 / 0.849 (an ~18–23 % uplift,
larger than CC's ~7 % after miso-275). That is recorded, not proposed: it would not target the held-out years.

**The gap by floor membership** (payload plant grain, model vs EIA-923, TWh):

| year | plants with an ST_GAS floor (p25/oom rows) | plants with **no** ST_GAS tranche row |
|---|---:|---:|
| 2019 | 6.07 vs 11.50 (**−5.43**) | 1.88 vs 6.87 (**−4.99**) |
| 2020 | 8.09 vs 12.88 (−4.79) | 2.31 vs 6.36 (−4.06) |
| 2021 | 5.65 vs 8.32 (−2.67) | 0.56 vs 3.86 (−3.31) |
| 2022 | 5.99 vs 9.47 (−3.48) | 1.03 vs 3.79 (−2.76) |
| 2023 | 11.30 vs 11.58 (**−0.28**) | 2.35 vs 3.55 (−1.19) |

**Half 1: floored plants, held-out years.** The floor windows and levels are measured on the pooled 2023–25 CAMPD
window. Own-year sync fractions (same frozen estimator, `derive_thermal_tranche_online_frac_by_year.py` extended to
2019–22; 2023–25 rows reproduce the committed artifact exactly, 0 of 414 non-coal rows differ) are nameplate-weighted
**0.706 / 0.691 / 0.670 / 0.648** in 2019–22 against a pooled **0.548**.
- This is new evidence on the `R` cell `mustrun_online_frac_per_year`. miso-172 rejected it on a predictor band over
  2023–25 only, where own-year ≈ pooled by construction.
- **Footprint measured and small:** ST_GAS floor energy 9.659 → 9.764 TWh (2019), 10.066 → 10.238 (2020), 9.150 → 9.207 (2021), 10.099 → 9.965 (2022), 9.172 → 9.263 (2023). Seven live
  plants. Sabine / Little Gypsy / Lewis Creek / Nine Mile rise; Harding Street 990 falls (−0.36; its own 2019 sync
  0.557 vs pooled 0.974).
- So the floored plants' 2019 shortfall is **economic dispatch above the floor** in a $2.5-gas year, not the window.
  The per-year window is structurally right and moves ~0.1 TWh; it is not a C1 lever. The cell stays `R`, with this
  footprint added.
- **Estimator hazard found:** the sync statistic is facility-summed. At mixed coal/gas facilities it counts coal units
  as gas-steam sync: Dan E Karn 1702 reads 0.834 / 0.809 / 0.996 / 0.967 in 2019–22 (coal units 1–2 running) and
  Burlington 1104 reads 0.85 while it was still coal. Neither carries an ST_GAS floor today, so nothing is
  mis-floored. Any lane that widens ST_GAS floor membership must fix this first.

**Half 2: the population gap (the larger, structural half).** Brame 6190 (short **every** year, including 2.13 vs 0.49
TWh in 2023), Big Cajun 2 6055, Baxter Wilson 2050 and Teche 1400 carry **no ST_GAS tranche row at all**:
- the thermal-tranche artifact files facilities 6190 / 6055 under COAL only;
- 1400 is filed under CT_PEAKER;
- 2050 has no row.

These are Entergy / Cleco / Louisiana Generating legacy steam in the MISO-South load pockets. The real market commits
them largely for local reliability (MISO VLR commitments in WOTAB / Amite South). The model has no such commitment,
and no floor for these units. Two repairs, neither solve-ready:
1. **Group attribution at mixed facilities** needs unit-level fuel attribution of the CAMPD stacks, which is **the
   same CAMPD-unit → EIA-plant/generator crosswalk** candidate 1 is waiting on (owner ruling "Wait for crosswalk").
   Rule 23 refuses a re-derive of the frozen tranche artifact without that data change.
2. **A MISO VLR / load-pocket commitment mechanism** is a new mechanism (new field plus matrix row in every shard).
   The MISO cell `scuc_load_pocket_commitment` reads `·`. Its identification needs MISO's published VLR commitment
   record (a data ask).

**Verdict:** no solve earned. Route: the crosswalk (a second consumer), then either repair 1 or a chartered VLR lane.

## 3. D1 data intake: no free daily MidCon hub exists; South has one on disk

Searched, 2026-09-26:

| source | daily? | MISO-relevant hubs | years | usable |
|---|---|---|---|---|
| EIA NGWU compact "Spot Prices" table (`miso_citygate_daily.csv`'s source) | yes | Henry Hub, Chicago only (plus NY, CA) | 2018– | Chicago already on disk |
| EIA NGWU narrative | prose | quotes single prints (OGT $1,192 on 2021-02-17, Chicago ~$130 on 02-12) | — | no series |
| EIA wholesale market data (ICE natgas files) | yes | 7 hubs, none MidCon | **2014–2017 only** | no |
| EIA Today in Energy "daily prices" | yes | Midwest, Louisiana | today only, no history | no |
| EIA `henry_hub_daily.csv` (on disk) | yes | Henry Hub (Erath, LA) | full span | **yes, for MISO-South** |
| ICE / NGI / Platts daily indices (Ventura, Demarc, NGPL Mid-Con, Texas Eastern, Columbia Gulf) | yes | all of them | full | **paywalled** |

**Reading.**
- **MISO-South:** Henry Hub is physically in Louisiana and is the South zone's own regional hub. A daily delivered
  construction for South needs no intake: HH daily plus the zone's measured delivered basis.
- **MISO-West / Plains (MidCon, Northern Natural):** no free daily series exists. The two options are a licensed
  ICE/NGI purchase (Ventura/Demarc, NGPL Mid-Con), or Chicago daily as the nearest accessible measured hub under
  rule 14's misalignment exception, stated as a proxy.
- **Hazard carried from miso-269 §2:** routing Chicago's $129.52 Uri weekend print into West/Plains as well raises the
  storm-week hazard the owner has already accepted (158 → 317 vs 141 actual when only the Chicago zones take it).

This is an owner decision (data purchase vs proxy), so the intake is stopped here.

## 4. Candidate 1 (CC outage numerator basis) — status only

Still waiting on the CAMPD-unit → EIA-plant crosswalk (owner ruling 2026-09-26, "Wait for crosswalk"). §2 found the
same facility-vs-unit defect in a second place (mixed coal/gas facilities in the sync estimator), which raises the
value of that crosswalk.

## 5. Verdict and routing

| object | verdict | next |
|---|---|---|
| C3a 2022 −15.4 % | ~62 % Indiana-Hub premium in the congested year ($10.36 vs $1–3); the remaining −6.4 % is summer-peak depth (30 GW idle at the top-decile hours; model max $97.7) | topology lane (West→East interface); summer-peak availability. Not the offer channel, not a benchmark re-base |
| C1 ST_GAS 2019 −8.46 TWh | held-out-year object: floored plants −5.4 (economic, above floor), unfloored mixed-facility South steam −5.0 | CAMPD-unit crosswalk (2nd consumer), then group attribution or a chartered MISO VLR lane |
| C3b 2021 (D1) | South: HH daily on disk; MidCon: no free daily hub | **owner: buy ICE/NGI daily or accept Chicago as the MidCon proxy** |
| candidate 1 | waiting on crosswalk | unchanged |

**No LP was earned, so no shard was launched.** Keeper unchanged; nothing to promote.
