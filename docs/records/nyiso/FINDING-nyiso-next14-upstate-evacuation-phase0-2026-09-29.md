# FINDING — NYISO-NEXT-14 phase 0: the C3a miss is the Upstate_West collapse (ZERO LP)

- **Session:** NYISO-NEXT-14, the orchestrator. No LP, no shard.
- **Keeper read:** `2026-09-29-nyisonext13-recon-detach-span` + stamped 2021 (committed hourly sidecars).
- **Probe:** `scripts/probes/nyisonext14_upstate_phase0.py` → `results/phase0/nyiso/_nyisonext14_phase0.json`.
- **Question:** queue item 1 says the pooled static import ladder lowers the price level. Is that the C3a driver?

## 1. Where the C3a miss sits

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C3a (load-weighted RT) | −14.3 % | −13.6 % | −7.0 % | −2.5 % | −11.3 % |
| Upstate_West model / measured RT, $/MWh | 7.3 / 28.5 | 27.5 / 56.7 | 18.4 / 25.3 | 33.4 / 33.1 | 50.5 / 55.5 |
| **C3a if Upstate_West alone were exact** | **+4.6 %** | **−1.2 %** | **+0.4 %** | −2.8 % | −8.7 % |
| Upstate_West h at the pooled node's price | 8,403 | 7,769 | 5,533 | 5,297 | 4,624 |
| Upstate_West h ≤ $0 (measured: tens) | 3,110 | 1,263 | 723 | 0 | 0 |
| hydro, model / EIA-923 TWh | 24.3 / 28.8 | 24.7 / 27.4 | 26.1 / 28.4 | 26.7 / 27.9 | 24.1 / 24.1 |

- **2021–2023: the whole miss is Upstate_West.** Downstate zones are within a few $/MWh, and above measured in NYC.
- **2025 is different.** The miss is spread across zones and sits in the top price decile (winter gas days, the June heat wave, the >$300 tail).

## 2. Why Upstate_West collapses

- **The model cannot move upstate energy east.** Its one Upstate_West → Capital_Hudson link is capped at the posted CENTRAL EAST limit. The measured TOTAL EAST flow (the A–E → east cutset) exceeds that cap in **99 / 96 / 96 / 63 / 60 %** of hours (2021–2025).
- **The band then prices the surplus.** With the NE AC node detached, the monthly EIA-930 band forces the pooled node to its measured volume. The only zone that can still take it is Upstate_West. Measured hydro is spilled (−4.4 / −2.7 / −2.3 TWh in 2021–2023) and the upstate price falls to the pooled node's price, often below $0.
- **So queue item 1 is this object seen from the import side.** The pooled ladder's shape is not the driver: in the top price decile the model imports *less* than measured, not more.

## 3. The non-CE leg is an internal path, not the external ties

Least-squares read of (TOTAL EAST − CENTRAL EAST) on the external schedules, 2021–2025:

- coefficient on the NE AC tie −0.19 to +0.05, on the downstate DC lines −0.44 to +0.05 (an external-tie sum would carry ~+1);
- coefficient on upstate injections (IESO +0.26 to +0.40, PJM AC +0.50 to +0.56) behaves like a distribution factor;
- R² 0.43–0.73, intercept 374–1,386 MW.

This supports nyiso-225's reading (the leg leaves A–E and bypasses F into G). Adding it to the model's link is not a double count of the external seams.

## 4. What this means

- The object is the **Total-East cutset** (`nyiso_total_east_cutset_ttc`), cell **R**. nyiso-224 tested it on 2022 alone and the owner ruled "reject as constructed".
- **New evidence since that ruling:**
  1. nyiso-224's G-5 fail (phantom COAL_PRB 0.66 → 1.27 TWh) cannot recur: the keeper fleet carries no coal class in any year.
  2. The NEXT-13 detach made the collapse the dominant C3a driver (Upstate_West −15.7 / −12.8 / −4.9 $/MWh in 2021–2023 vs the NEXT-12 keeper).
  3. Its G-1 was a price proxy (separation share 2 %). Its own network sidecar measured the link binding 12.5 % of hours against the market's 10.0 %.
- **nyiso-225's standing caveats still hold:** the arm binds in the wrong hours (lift 0.63), and the rent in binding hours is far too small. A re-test would report both, not gate them away.
- **Re-opening an R cell is the owner's call** (rule 28). This finding is the evidence for that decision.

## 5. Other queue items, checked at zero LP

- **Item 3 (rating-bound downstate lines):** the LI half is already armed (`nyiso_li_seam_posted_limit_cap`, NEXT-6: LI price +0.1–0.3 $/MWh). An NYC analogue is of the same order and cannot move C3a.
- **Loop flow is not the cause:** IESO's physical Ontario→NY flow equals the schedule within 0.4 TWh/yr (IESO `PUB_IntertieScheduleFlowYear`, mean loop −5 to +46 MW).
