# FINDING — R-SOCO-B2: the former Gulf Power plants and load sat inside SOCO's EIA-930 BA until 2022-07-13

Lane R-SOCO-B2, 2026-09-25. Zero LP. Every number is reproduced by
`scripts/probes/_rsocob2_gulf_exit.py`, with output in `rsocob2_boundary/probe.json`. The inputs are EIA-930
BALANCE, PUDL FERC-714 hourly planning-area demand, CAMPD hourly unit data, and EIA-923 monthly generation.

## 0. Answer

**R-SOCO-B's R2 is right from 2022-07-13 and wrong before that date.** The premise that EIA-930's SOCO series
"never included" Gulf (R-SOCO RESULT, "Found after promotion", and the SOCO-60 "930 always excluded Gulf") is
**false for 2019 through 2022-07-13**. Before that hour, Gulf's load and its plants' generation were both inside
SOCO's 930 BA. After it, both sit in FPL's. Three independent instruments find the move at the same hour:

| instrument | before 2022-07-13 | after |
|---|---|---|
| **Load.** SOCO 930 demand − Σ five SOCO-footprint FERC-714 respondents (daily mean) | 2,600–3,070 MW (07-01…07-12) | 816–1,118 MW (07-14…07-31). The step is **−1,700 MW**, which is Gulf's own FERC-714 load (1,529–1,894 MW that week). |
| **Gulf's own filing.** FERC-714 respondent 185, Gulf Power | continuous since 2018 | **last hour 2022-07-13 10:00 UTC**. FPL (63) absorbs the load: FPL 930 − FPL 714 stays ~0–600 MW throughout. |
| **Generation.** Hourly least squares of SOCO 930 fossil net gen on CAMPD gross load (core / Gulf / PowerSouth) | **b_gulf = 0.83–0.89** in every period (R² 0.996–0.998) | **b_gulf = 0.014** (2022 after exit), −0.18 in 2023, −0.04 in 2024 |

The hour-level step: SOCO's residual falls about 1,400 MW against the same hour of the prior day from 10:00 UTC on
07-13. FPL 930 rises 1,750–2,550 MW from 11:00 UTC. **Exit instant: 2022-07-13 11:00 UTC, hour-beginning**, which
is the first hour Gulf 185 does not file.

**2022 is affected as well as 2019–2021.** For 51.2 % of 2022, measured as Gulf's own CEMS gross-load share before
the instant, Gulf was inside SOCO. R2 took it out of the 2022 LP fleet for the whole year.

## 1. The SOCO-60 boundary checks close once Gulf is restored for its in-BA period

Annual figures in TWh. "bench" is `run_calibration_full._eia923_frame(y, …, "SOCO")` at HEAD, fossil classes. "+ Gulf
in BA" adds the five Gulf thermal plants' EIA-923 generation for the in-BA share: all of 2019–2021, 51.24 % of 2022
(CEMS share), and none from 2023.

| year | 930 coal+gas | bench fossil | Gulf 923 | Gulf in BA | **930/923 as bench** | **930/923 + Gulf in BA** | 930 gas − 923 gas, bench | 930 gas − 923 gas, + Gulf |
|---|---|---|---|---|---|---|---|---|
| 2019 | 181.189 | 176.565 | 8.011 | 8.011 | 1.026 | **0.982** | +1.393 | **−6.618** |
| 2020 | 165.115 | 158.973 | 7.658 | 7.658 | **1.039** | **0.991** | +4.335 | **−3.323** |
| 2021 | 171.330 | 167.462 | 7.058 | 7.058 | 1.023 | **0.982** | +2.286 | **−4.772** |
| 2022 | 177.506 | 176.428 | 7.436 | 3.810 | 1.006 | **0.985** | −0.327 | **−4.138** |
| 2023 | 167.839 | 167.475 | 7.674 | 0 | 1.002 | 1.002 | −0.644 | −0.644 |
| 2024 | 166.615 | 169.783 | 8.301 | 0 | 0.981 | 0.981 | −3.459 | −3.459 |

- **B1** (band 0.97–1.03): the ratio lands at **0.982 / 0.991 / 0.982 / 0.985**, inside the band and next to 2024's
  0.981. On the bench boundary 2020 fails at 1.039.
- **B2** ("930 gas ≤ 923 gas"): the check **passes in every year** once Gulf is restored. On the bench boundary it
  failed by +1.39 / +4.34 / +2.29 TWh.
- **Why the raw excess (4.6 / 6.1 / 3.9 TWh) is smaller than Gulf's 7–8 TWh.** SOCO's 930 fossil runs about 2 %
  below its 923 plants in every year (b_core 0.97–0.98; 2024's ratio 0.981 carries no Gulf at all). Subtract that
  ~3.5 TWh shortfall from Gulf's ~8 TWh and ~4.5 TWh is left. The excess was never a whole number of plants, so
  the hunt for a "Gulf subset" was looking for the wrong thing.
- **Monthly fit.** Built this way, corr(930 − bench, Gulf 923) is **0.77 / 0.76 / 0.97** for 2019 / 2020 / 2021.
  The weak 0.07–0.48 in the brief came from a different construction, and the hourly CEMS fit above settles the
  question anyway. The ratio with Gulf restored has a seasonal net-vs-gross shape (winter ≈ 0.96, summer ≈ 1.01).
  That is not a boundary signal.

## 2. PowerSouth (R3) is independently confirmed

- **Generation.** b_aec ≈ 0 in 2021 Jan–Aug (0.009) and 1.2–1.6 from 2021-09. In 2019 it is −0.49, which is
  collinearity noise with the plant outside the BA.
- **Load.** AEC's own 930 demand, ~650 MW, stops on 2021-09-01. SOCO 930 absorbs it. In FERC-714, Alabama Power's
  planning area (respondent 2) steps up **+1,157 / +1,207 MW** in September / October 2021 against 2020, while
  Georgia (183) is flat. That is why SOCO − Σ respondents falls about 600 MW at the join: the respondent sum
  gained more than the BA did. **No change to R3.**

## 3. Rule-outs

- **Other recodes.** Intersected with the SOCO universe, the current EIA-860 recode set is exactly the nine Gulf
  plants, all → **FPL**: Crist 641, Lansing Smith 643, Pea Ridge 7715, Standby 50310, Santa Rosa 55242,
  Perdido 57502, and solar 63754 / 64757 / 65036. The only other SOCO BA-code movers in EIA-923 2019–2024 are
  the eight AEC plants, which R3 already covers.
- **EIA-923's own `ba_code`** codes Crist, Smith, Pea Ridge and Perdido `SOCO` through 2023 and Santa Rosa `FPL`
  from 2022. It lags the operational move, and 930 and CEMS pin the move to 2022-07-13. The code is not a clean
  instrument for the date.
- **CHP/BTM.** SOCO chp=Y fossil is 7.45 / 7.32 / 7.75 / 7.27 / 7.20 / 7.53 TWh for 2019–2024. It is flat, so it
  cannot produce a 2019–2021 step.
- **930 revisions.** Adjusted − raw fossil is +0.37 TWh in 2019 and 0.000 in every other year.

## 4. What this means for the R-SOCO-B run

- **Demand is already right.** The LP serves EIA-930 SOCO demand, and that demand includes Gulf's load through
  2022-07-13. Under R2 the 2019–2021 fleet and the first half of the 2022 fleet serve Gulf's load (~11.7–12.0
  TWh/yr, ~1.7 GW summer) **without Gulf's plants** (1,826.6 MW in 2019–2020, 2,760.8 MW in 2021, and 2,524.9 MW
  in 2022 per the R-SOCO-B census). That supply-boundary defect is the one R2 was written to remove, now in the
  other direction.
- **The benchmark has the same defect.** `_iso_plant_ids` drops Gulf in every year, so the 923 benchmark misses
  the 8.0 / 7.7 / 7.1 / 3.8 TWh of Gulf generation that EIA-930 counts.
- **Rule 14.** Restoring Gulf for 2019–2022-07-13 is the accurate boundary. R2 stays exactly as it is from the
  exit instant on. This is a **dating** of R2, not a revert, and the 2023–2025 legs are untouched.

## 5. Proposed ruling (C): a dated BA exit registry — the `ISO_BA_JOINS` twin

- **Registry.** `constants.ISO_BA_EXITS: dict[str, dict[str, str]] = {"SOCO": {"FPL": "2022-07-13 11:00"}}`, UTC
  hour-beginning. The plants that leave are the ones R2 already selects (current EIA-860 recode to the named BA),
  and they are members until the instant. The value is the measured instant above, so there are **zero free
  parameters**. It is SOCO-only: every helper returns its input object for an unregistered region, as the R3
  helpers do.
- **Fleet (`fleet/arrays.py`, beside the join mask).** A year before the exit year keeps the plants all year: the
  recode drop is skipped for that year. The exit year admits them with an **hour-grain** 0/1 mask, with `min_gen`
  scaled the same way. A year after the exit year behaves as R2 does today.
- **Benchmark and injection (`_iso_plant_ids`, `_eia923_frame`).** Same membership. In the exit year's split month
  (July 2022), the plants' EIA-923 monthly generation is scaled by their **measured in-BA CEMS share of that
  month**. This choice is flagged below.
- **Declared inert** at SOCO's pre-lane value `{}` on the solve surface, with matrix rows in every shard.
  `gen_soco60b` B1/B2 read the dated membership.
- **Years that move: 2019, 2020, 2021, 2022.** 2023–2025 are byte-identical by construction (the exit precedes
  them), which E2 checks.

**The one design choice the owner may want to rule on: the grain of the split month.** Hour grain is exact and
carries no rounding rule. Month grain (the `ISO_BA_JOINS` construction) would need a declared rounding rule for
July 2022; Gulf was a member for 12.4 of 31 days, so a majority rule reads "out from July". Recommendation: **hour
grain**, because the instant is measured to the hour.

## 6. Cost of the re-solve if (C) is ruled

The per-year leg branches were deleted on the lane-PR merge. Only `claude/rsocob-2021` (fbe97e08) survives, and it
is superseded under (C). The parked composite on `claude/r-soco-b-hold` @ `99906f86` carries hourly sidecars but no
`dispatch/<Y>_P1.parquet`. **Recomposing therefore needs all seven legs re-solved:** four LIVE (2019–2022) and three
byte-identical replays (2023–2025, E2). Rule 36 puts each year in its own shard, all in parallel: **~2–12 min of LP
per year, ~15 min wall.**

## 7. Option (1), the fallback if (C) is declined

Limit the gen_soco60b B1/B2 checks to 2022+ and disclose the 2019–2021 residual in full (§1 table). There would be
no re-solve, and the parked composite would be attested and landed as it is. **It is not recommended.** §0–§1 give a
clean construction, so (1) would knowingly register a fleet that is missing 1.8–2.8 GW of in-BA plants, and rule 14
says to take the accurate boundary.
