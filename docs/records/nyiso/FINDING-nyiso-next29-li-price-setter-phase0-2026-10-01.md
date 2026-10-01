# FINDING — NYISO-NEXT-29 phase 0: the Zone-K spread miss is in the hours the 940 MW cap does NOT bind

**Session:** NYISO-NEXT-29 orchestrator, 2026-10-01. **Solves: ZERO.**
**Keeper (unchanged):** `2026-10-01-nyisonext21-astoria-hr-span` plus the stamped `-2021` run.
**Inputs:**
- NEXT-26 arm-A legs (`nyiso_li_tsl_all_hours`, pin `4213945e`): `unit_hourly`, `network`, `system` from `claude/nyisonext26-<y>`.
- NYISO DA zonal LBMP 2021–2025 (`fetch_nyiso_zonal_lmp.py --kind da`), with the published congestion component.
- Measured P-32 schedules and posted limits on the LI ties (Neptune, CSC, 1385; `nyiso-interface-flows`).

**Record and probe:** `results/phase0/nyiso/_nyisonext29_li_price_setter.json`, `scripts/probes/nyisonext29_li_price_setter.py`.

## 1. Result

1. **NEXT-26's explanation does not hold.** RESULT §3 read the small K-over-J spread as "the LI units that replace imports are priced close to J". In the capped hours the modelled spread is already at or near DA in 2021, 2022 and 2024.
2. **69–100 % of the annual K-over-J spread miss sits in the uncapped hours** (60–80 % of the year). There the model's NYC→LI link is below 940 MW, so K = J (spread $0.1–0.3/MWh). DA still carries $1.8–10.8/MWh of K-over-J congestion in those same hours.
3. **That congestion appears at every model flow level.** In 2021 it is $9–12/MWh even when the model imports < 300 MW. The measured Zone-K import set binds at net imports the model never treats as constrained. This is open item 2's mechanism, now shown to carry most of the annual miss, in winter as well as summer.

## 2. Where the spread miss sits

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| capped hours (NYC>LI = 940) | 3,567 | 2,269 | 2,797 | 2,134 | 1,768 |
| capped: spread model / DA ($/MWh) | 12.7 / 12.7 | 9.1 / 8.9 | 3.1 / 8.0 | 2.4 / 3.7 | 5.9 / 9.2 |
| uncapped: spread model / DA | 0.1 / 10.7 | 0.3 / 11.5 | 0.3 / 6.3 | 0.2 / 4.1 | 0.1 / 2.0 |
| annual spread error | −6.3 | −8.2 | −5.6 | −3.3 | −2.2 |
| **share of that error in uncapped hours** | **100 %** | **100 %** | **72 %** | **91 %** | **69 %** |

Uncapped-hour spread error by season ($/MWh):

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| winter | −14.0 | −7.4 | −11.2 | −2.1 | −3.5 |
| spring | −6.0 | −13.3 | −3.0 | −1.5 | 0.0 |
| summer | −18.5 | −17.3 | −7.2 | −10.5 | −4.3 |
| fall | −7.0 | −5.6 | −4.8 | −0.7 | −0.5 |

DA K-over-J congestion ($/MWh) by the model's own NYC→LI flow:

| model flow (MW) | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| < 300 | 11.8 | 7.4 | 2.5 | 2.1 | −0.2 |
| 300–500 | 8.8 | 10.4 | 4.8 | 4.2 | 1.7 |
| 500–700 | 9.1 | 12.6 | 7.2 | 5.2 | 4.3 |
| 700–900 | 11.7 | 15.5 | 7.7 | 6.3 | 7.3 |
| at 940 cap | 12.2 | 7.9 | 7.4 | 3.1 | 8.3 |
| *model spread, every bin below cap* | *0.1–0.2* | *0.2–0.6* | *0.1–0.4* | *0.1–0.4* | *−0.1–0.8* |

## 3. Who sets K in the capped hours

The capped hours split by the state of the other Zone-K import path, `NYISO_external>Long_Island` (Neptune, CSC, 1385):

| share of capped hours | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| external link inside its bounds → **K = external price + monthly band dual** | 52 % | 66 % | 51 % | 78 % | 62 % |
| external link at its hourly cap → **an LI unit sets K** (92–96 % of these hours) | 45 % | 31 % | 50 % | 22 % | 37 % |
| external link at zero | 3 % | 3 % | 0 % | 0 % | 1 % |

- **First regime: an exact identity, not a fit.** `price_K − price_ext` has zero within-month variance in every month of 2021, 2022, 2023 and 2025. The 2024 maximum is $7.3, in November only. So K equals the pooled external price plus the dual of `nyiso_import_landing_band` (K, NEXT-15) on that link. The monthly wedge runs $1.6–71/MWh, and is largest in winter.
- **Second regime: LI units.** Marginal plant group, over capped hours with a marginal LI unit: LI steam (Northport 2516, Port Jefferson 2511) 18–53 %, CCs 27–44 %, CTs 11–33 %. The capped-hour residual is here only in 2023 (spread 5.7 vs DA 11.8) and 2025 (11.9 vs 15.1). In those hours the model's external flow is 80–135 MW above measured, in every year.
- **Shape of the external link (diagnostic, adjudicated mechanism).**
  - Monthly volume matches measured to +2 % (the band works).
  - The hourly shape does not: the model sits at ≥ 95 % of its own p90 envelope in 70–77 % of hours. Measured flow does so in 28–39 %.
  - In capped hours the model carries 75–195 MW less than measured. Restoring measured flow there would lower K, not raise it, so this is not a route to the K miss.

## 4. Reading and why no lever is proposed

- **LEAD A answered.** In capped hours, K is set by either (a) the external cable's monthly energy budget, or (b) LI steam, CCs and CTs once both import paths are full. The capped hours are not where the Zone-K error lives. In 2021, 2022 and 2024 they are already close to DA.
- **The object is open item 2.** The measured Zone-K import set (Y49/Y50, ConEd–LIPA, Shore Road; NEXT-26 FINDING §2) binds in 1,680–5,782 DAM hours a year. Measured implied net import is far below 940 when it binds. In those hours the model's net link is unconstrained.
- **The net-link representation cannot produce that congestion:**
  - A tighter static net limit would be a fitted number (rule 1).
  - An hourly cap at measured net import is pinning to an observed flow (rule 13).
- **The re-open condition is unchanged.** A lever needs a forward-reproducible driver of the effective limit: either measured Y49/Y50 / 138 kV PAR schedules and outage windows, or published shift factors. The DAM limiting-constraint posting names the binding facility and its shadow cost, but carries no MW limit. It identifies *what* binds, not *at what flow*.
- **Secondary, not a lever:** in the 2023 and 2025 capped hours where LI units set K, K is $3–6/MWh under DA. NEXT-28 measured LI steam under CAMPD by 1.9 TWh in 2023. Under-dispatch and under-pricing together point to a commitment hurdle (local reliability commitment of LI steam), not to the offer level. That joins open item 6 (in-city / local commitment requirement, owner-held). No commitment lever is open (NEXT-28 §3).

**No PRECOMMIT, no shard.** Every cell stays as it is. `nyiso_li_tsl_all_hours` stays O pending card 1.
