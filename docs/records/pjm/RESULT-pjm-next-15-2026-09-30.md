# RESULT — PJM-NEXT-15 (2026-09-30): cheap CC block refuted as the C3a lever; CC over-run is loading, not commitment

**Keeper unchanged:** `2026-09-28-pjm-next8-exitfix`.
- **Solves:** none (zero LP, zero shards). Nothing registered or promoted.
- **Detail:** `docs/records/pjm/FINDING-pjm-next-15-cc-cheap-block-and-commitment-2026-09-30.md`.

| card | result |
|---|---|
| 1 — PJM's cheap CC block, 2019–2025 | 59–86 % of it is at or below ecomin (PJM's min-load block) on a distinct ~0-start-cost unit set. Above ecomin, the mid-curve share is **0.05 / 0.17 (2019 / 2020) vs 0.30 / 0.32 (2023 / 2024)**: inverted against the C3a miss. **Refuted as the C3a lever.** |
| 2 — CC volume root cause | Commitment is a **constant** +2–8 TWh bias (short real off-runs; the model starts CCs as often as reality or more). The **year signal is loading when on**: +3.0 to +5.7 TWh in the C1-fail years, −4.7 to −10.0 in the pass years. |
| 2b — CC floor window | `cc_mustrun_per_plant` puts 20–28 TWh/yr of committed MW (upper bound) in real off-hours, flat by year. A rule-17 structural question, not a C1 lever. |
| 3 — design card | **Not reached**: no admissible, year-discriminating, zero-DOF design. |

**Status (unchanged):** training span NOT-YET on one row (C1 CC_REGULAR 2023 +8.48); run-level NOT-YET, 14 out-of-span rows.

**OPEN (not limits):** C3a 2019/2020 and the floor; C1 CC 2019/2020/2022/2023; COAL_BIT 2019/2021; CT_PEAKER 2021; C3a/C3b/C3c 2022.

**Next:** decompose the CC loading term (2019/2020 vs 2023/2024) by zone and hour against the coal econ bid and net interchange (zero LP). Owner call: charter a P0-pattern CC min-load bridge to replace the system-load window?

**Retrievability:** no bundles. All numbers are in `results/calibration/_pjmnext15_cc_{cheap_block,commitment,floor_window}.json` on `main` with this PR.
