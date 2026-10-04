# FINDING — closeout-SPP-w3 desk item 2 (zero LP): C3b 2024 and C3c 2023–25 residuals land on the signed frontier rows

- **Desk instruction:** item (1) is to take UC-MILP SPP 2019/20 if no lane owns it. A lane does own it: UC-2-SPP A/B
  (`session_01QBeFQCYTmVafRpi7Ujb9gs`, `docs/uc-milp-program-plan-2026-10.md` §12, ruling R6, all SPP years at the
  engine SHA). This lane therefore takes item (2).
- **Probes:** `scripts/probes/_closeoutsppw3_c3b2024_f1.py`, `scripts/probes/_closeoutsppw3_c3c_tail.py`. They read
  the keeper `closeout_spp_nuc_span`, the arm `closeout_spp_w3_span`, the SPP RT/DA hub and LMP-component series,
  and EIA-930 SWPP.

## 1. C3b 2024 (keeper 0.216, arm 0.207; band 0.200): the residual is F1

- **Where the error sits.** Monthly SSE shares on the keeper: Sep 20 %, Oct 32 %, Jul 12 %, Aug 11 %, Dec 8 %, the
  rest ≤ 6 %.
- **Counterfactual.** Remove the excess Sep–Oct South–North RT congestion component from the actual. "Excess" means
  above the 2023 Sep–Oct level of 5.68 $/MWh, the R-62 construction; the system hub is the mean of the N and S hubs.

| run | C3b vs actual | C3b vs actual − excess Sep–Oct S−N MCC |
|---|---:|---:|
| keeper | 0.216 | **0.197** |
| arm (PTC + hydro envelope) | 0.207 | **0.195** |

- Everything above the band is the Sep–Oct 2024 Oklahoma-pocket congestion object. That is signed frontier row
  **SPP-F1** (DATA-LIMITED).
  - Re-checked today: the 2024 `da-binding-constraints` and `rtbm-binding-constraints` archives on portal.spp.org
    carry shadow prices only, with no limit columns. SPP's 2024 archives are yearly zips only.
- **No new lever.** The Jul–Aug part (23 %) is the common upper-tercile compression. On its own it keeps C3b inside
  the band.

## 2. C3c 2023–25 (model 0 h vs 42 / 59 / 68 RT hours > $200): event structure

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| RT > $200 hours | 42 | 59 | 68 |
| distinct events (consecutive runs) / days | 37 / 34 | 40 / 36 | 54 / 50 |
| DA in those hours: mean / hours > $200 | $46 / 0 | $129 / 14 | $49 / 0 |
| model P1 price there: mean / max | $30.7 / 42.4 | $43.0 / 75.8 | $34.9 / 64.0 |
| model thermal headroom: min / median (all-hour median) | 5.4 / 12.7 GW (18.8) | 4.6 / 10.2 GW (19.2) | 7.1 / 13.5 GW (19.2) |
| net-load rank, median | 0.69 | 0.96 | 0.74 |
| EIA-930 wind ramp, median MW/h (all hours) | −845 (−12) | −21 (0) | −378 (0) |
| months | spread over the year | Jan 20 (Winter Storm Heather), rest spread | spread over the year |

- **The tail is isolated real-time events, not hourly scarcity.**
  - Most are single hours, with no DA counterpart in 2023 or 2025.
  - The model has 5–13 GW of hourly thermal headroom in them.
  - In 2023 and 2025 they sit on wind ramp-downs at ordinary net load.
- **That is the 5-minute ramp/deviation object** (wave-1 §2; SPP-29). An hourly perfect-foresight LP has no measured,
  forward-reproducible driver for it. Scarcity or ORDC-like adders are not structurally real here: the co-opt binds
  0 h, as re-measured in wave 2.
- **The only hourly-representable piece is Jan 13–16 2024** (DA > $200 in 14 hours). Even fully represented, its
  ≤ 20 hours cannot reach 2024's 0.5× bar (30 h). 2023 and 2025 carry no such event.
- **Conclusion:** C3c stays **SPP-F4 model-class**, with this decomposition as its evidence.

## 3. Queue

- With the UC-MILP SPP arm owned elsewhere, every SPP failing record now maps to an owned lane, a signed frontier
  row, or an owner ruling:
  - F1: data;
  - F2 and C1 2021/22: UC-2-SPP and W5;
  - F4: model-class;
  - the 2019–22 legacy price basis: owner ask.
- This lane has no admissible lever left to build.
