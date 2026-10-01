# FINDING — NYISO-NEXT-28 phase 0: Ravenswood 2500 steam over-dispatch in 2023 is a knife-edge merit-guard handback loaded by a pure LP

**Session:** NYISO-NEXT-28 orchestrator, 2026-10-01. **Solves: ZERO.**
**Keeper (unchanged):** `2026-10-01-nyisonext21-astoria-hr-span` plus the stamped `-2021` run.
**Inputs:**
- The keeper's 2022–2025 leg bundles: `unit_hourly_<y>.parquet` on `claude/nyisonext21-<y>`.
- The 2023 leg `83b4652a…/4c519e15…`.
- CAMPD unit-level NY 2022–2025, read with `facilityId` as a string.
- The committed `-perunitmerithour-` outage/layup extract pair (sha `986d1d43…`).
- NYISO DA zonal LBMP for 2023.
- The merit-order guard's own panel (`build_merit_order_panel`).

**Record and probe:** `results/phase0/nyiso/_nyisonext28_ravenswood_phase0.json`, `scripts/probes/nyisonext28_ravenswood_2023_phase0.py`.

## 1. Result

The 2023 excess is **not** a floor, a heat-rate error, a fuel error or a price error. Two things combine:

1. **The merit-order guard flips on unit 30 in 2023 only.** Unit 30 is a 1,030 MW boiler. The guard books every one of its 2023 dark windows as *economic layup*, at an out-of-merit share of 1.000. In 2022, 2024 and 2025 it books the same unit's dark windows as *outage*, at shares of 0.0–0.86, which is below the 0.90 bar. The model's Ravenswood steam availability is therefore 1,112 MW on average in 2023, above 500 MW in all 8,760 hours. In the other years it is 200–393 MW.
2. **The pure LP loads that capacity at thin spreads.** It has no commitment hurdle, so it dispatches the returned capacity whenever the Zone-J price clears the offer. The actual units sit near minimum load when they run, and they commit only on sustained spreads.

## 2. Measurements

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Model Ravenswood ST (TWh) | 0.87 | **4.00** | 1.69 | 1.29 |
| CAMPD Ravenswood ST, gross (TWh) | 0.55 | 0.88 | 0.71 | 1.07 |
| Model ST availability, mean (MW) | 224 | **1,112** | 393 | 200 |
| Unit 30 SRMC p50 vs guard RCC p50 ($/MWh) | 86.8 / 88.8 | 34.5 / 32.1 | 24.4 / 24.3 | 42.2 / 43.6 |
| Unit 30 window out-of-merit shares | 0.20, 0.09, 0.0, 0.21 → outage | **1.0 ×7 → layup** | 0.32–0.75 → outage | 0.0–0.86 → outage |

**What the 2023 excess is not:**
- **Not a floor.** Of the 4.00 TWh, 3.35 TWh is inframarginal (reduced cost < 0), 0.52 TWh is marginal, and 0.14 TWh sits at floors. The plant has no D-4 failure row. Its only D-4 row is the CC bridge, at 0.7 GWh, and it passes.
- **Not heat rate.** The measured year-specific heat rate is applied: Ravenswood 11.32 vs Arthur Kill 10.97, and the Jan→May offer slopes give a ratio of 1.031. nyiso-185 K stands.
- **Not fuel.** The LDC leg is armed (`nyiso_ldc_generator_delivered_gas` K). Arm B's print-level change leaves Ravenswood unchanged (3.99 TWh).
- **Not price.** Model Zone J tracks DA J within −4 to +2 $/MWh in every month of 2023. At the model's own offer, **measured** DA J clears Ravenswood in 3,245 h, against 3,428 h at the model's price.

**Shape:**
- **Where the excess falls:** every month, and every hour band (06–11 and 16–19 carry 0.89 TWh each). Feb–Jun model energy is 1.40 TWh against 31 GWh measured.
- **Output when running (p50):** model 840 MW, CAMPD 203 MW. Unit 30's own p50 is 194 MW of 1,030, and units 10 and 20 run at about 90 of 380 MW. The real fleet is held near minimum load.
- **Upper bound from the handback:** removing the 2023 layup handback at the extract's own unit MW leaves 219 MW of mean availability. Model energy above that cap is **2.69 of the 3.16 TWh** excess, which leaves 1.32 TWh against 0.84 TWh measured, in line with 2024/25.

**Measured conduct is price-responsive.** This supports the guard's economic reading, not an outage reading:
- **Spread when on vs off:** the mean of (DA J − model offer) is +4.2 / +8.3 / +7.6 $/MWh in on-hours for units 30 / 10 / 20, and −1.5 / −2.8 / −1.9 when off.
- **Probability of running:** P(on | spread > $5) is 0.26–0.36. P(on | spread < 0) is 0.09–0.15.
- **What keeps it dark:** on 29 of 46 days with ≥ 12 h above a $5 spread, unit 30 stayed dark. The market's hurdle is commitment economics: start-up, a 24 h minimum run, and no-load at about 20 % loading. None of these is a cost-stack term.

## 3. Structural driver (named) and why no lever is proposed

**Driver.** The guard makes a binary whole-window decision against a statewide (NY+NJ) p90 revealed clearing cost. A unit whose SRMC tracks that stack within ±$2.5 in every year sits on the knife edge. Its availability then swings by about 900 MW on year-specific heat-rate noise: unit 30's 2023 gross HR was 11.47, the highest of the four years. When the guard returns the capacity, the pure LP (rule 4; no MIP) dispatches it at any positive spread. A real 1 GW boiler with a 24 h minimum run and an approximately $55/MW start does not.

**Enumerated, all closed (rules 19/28):**

| Candidate | Status | Why it does not apply here |
|---|---|---|
| `gas_st_startup_cost` | DO-NOT-REDO (nyiso-172) | Also inert by construction on an over-run: P1 amortizes the start over the **P0** run length. A unit running about 5,000 h gets a markup of about $0.1/MWh. |
| Per-plant min-run | R | — |
| `nyiso_incity_commitment_obligation` | R | — |
| `scuc_load_pocket_commitment` | G | — |
| `gas_offer_net_revenue_margin` | R | — |
| Heat rate / LDC gas | K | Already applied. |
| Rule-1 band channel (`offer_curve_by_group` ST_GAS econ) | Class-wide | Would also lower LI steam, which is already under (2023: NYC ST +3.6 TWh, LI ST −1.9 TWh vs CAMPD). It would also move 2022/2024, where class C1 is within band. Not proposed. |

**Possible guard-design reforms.** Each needs its own PRECOMMIT and an owner ruling:
- **(a) Hour-grain classification.** This is inert for 2023, because every dark hour reads out of merit.
- **(b) Same offer basis as the LP** (LDC gas, Zone-J stack). LDC raises unit 30's SRMC by about $2/MWh, so more 2024/2025 windows would cross 0.90. The predicted direction is *more* handback, a worse fit.
- **(c) An identification margin (SRMC − RCC beyond the panel's own noise).** This adds a free parameter (rule 21) and would be derive-side tuning motivated by a residual (rule 23).

None is admissible on today's evidence. **No PRECOMMIT is written. No shard is launched.**

**Disposition:** a model-class limitation (pure LP, no commitment hurdle), concentrated by a knife-edge guard. The `campd_outage_merit_order_guard` cell is annotated and stays **K**.

**Re-open** only with a measured outage source for Ravenswood 30 (NYISO/GADS outage schedules), or with an owner ruling to build a commitment-hurdle representation for the large in-city steam class.
