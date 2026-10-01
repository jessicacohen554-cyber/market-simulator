# FINDING — PJM-NEXT-15: PJM's "price-taking" CC block is the min-load block and points the wrong way by year; the CC over-run's year signal is loading, not commitment (zero LP)

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`), unchanged. **Zero LP, zero shards, nothing registered or promoted.** Card 3 (design card) is **not reached**: neither card yields an admissible, year-discriminating operand.

**Probes** (all zero LP):
- `scripts/probes/_pjmnext15_cc_cheap_block.py` → `results/phase0/pjm/_pjmnext15_cc_cheap_block.json` (card 1; offers corpus 2019–2025, 84 month-files re-fetched this session, no errors).
- `scripts/probes/_pjmnext15_cc_commitment.py` → `results/phase0/pjm/_pjmnext15_cc_commitment.json` (card 2; keeper payload vs CAMPD bench).
- `scripts/probes/_pjmnext15_cc_floor_window.py` → `results/phase0/pjm/_pjmnext15_cc_floor_window.json` (card 2b; the `cc_mustrun_per_plant` window rebuilt from the keeper's own hourly demand).

## Card 1 — the cheap CC block, all seven years

**Method.** Every CC_LIKE unit-hour (the derive's own segmentation, per year), step curve walked segment by segment. Segment `(mw_{k-1}, mw_k]` priced at `bid_k`. "Below ecomin" = the segment's upper edge ≤ `avg_ecomin` (+0.5 %). Delivered gas = the model's HH + PJM basis day series; production gas = IMM Platts monthly.

| year | share of offered CC MW < 3.5 × delivered gas | of which ≤ ecomin | **mid-curve (0.25–0.65), above ecomin, < 3.5 × delivered** | mid, above ecomin, < 6.5 × production | mid, above ecomin, < 6.5 × delivered | C3a keeper |
|---|---|---|---|---|---|---|
| 2019 | 0.091 | 0.86 | **0.05** | 0.14 | 0.54 | **+11.8 %** FAIL |
| 2020 | 0.179 | 0.74 | **0.17** | 0.14 | 0.59 | **+15.9 %** FAIL |
| 2021 | 0.117 | 0.64 | 0.13 | 0.30 | 0.55 | +1.8 % |
| 2022 | 0.097 | 0.59 | 0.11 | 0.39 | 0.55 | −11.5 % FAIL |
| 2023 | 0.228 | 0.63 | **0.30** | 0.22 | 0.58 | +5.2 % |
| 2024 | 0.207 | 0.65 | **0.32** | 0.35 | 0.60 | +0.5 % |
| 2025 | 0.184 | 0.68 | 0.27 | 0.37 | 0.64 | −1.9 % |

**1. What the block is.**
- **59–86 % of it sits at or below the unit's ecomin.** That is PJM's min-load block. A committed unit must run it whatever the LMP, and PJM does not let a unit at ecomin set LMP. Its offer price there is not a marginal-cost statement. The fixed part is carried by no-load and start cost in commitment and make-whole, not by the LMP.
- **It belongs to a distinct set of units** (units whose median offer puts ≥ 25 % of ecomax below 3.5 × delivered gas):

| year | cheap units: n / GW | first-segment bid ÷ gas | cold start $/MW | no-load ÷ ecomin ÷ gas | rest: first bid ÷ gas | rest: cold start $/MW |
|---|---|---|---|---|---|---|
| 2019 | 21 / 8.3 | 0.3 | 3.0 | 1.03 | 8.2 | 13.6 |
| 2020 | 42 / 17.0 | 2.8 | 3.2 | 1.52 | 8.5 | 11.3 |
| 2021 | 25 / 9.2 | 1.7 | 4.7 | 0.61 | 8.9 | 21.0 |
| 2022 | 27 / 7.8 | 1.0 | 12.3 | 0.00 | 12.2 | 34.2 |
| 2023 | 58 / 24.2 | 2.0 | 0.0 | 1.11 | 13.9 | 28.6 |
| 2024 | 51 / 20.9 | 0.3 | 0.0 | 1.27 | 16.0 | 31.7 |
| 2025 | 43 / 17.7 | 0.0 | 0.0 | 0.81 | 15.8 | 45.7 |

  Near-zero start costs and first segments at 0.3–2.8 × gas are what a unit submits when it intends to run regardless of price: self-schedule, contract, or tolling conduct. The corpus is unit-masked (DataMiner), so these units cannot be mapped to model plants.

**2. Is it year-discriminating?** **No — and it points the wrong way.**
- The C3a misses to be closed are 2019/2020 (too high).
- The above-ecomin cheap share is **smallest in 2019 (0.05)** and **largest in the fit years 2023/2024/2025 (0.30/0.32/0.27)**.
- Giving the model such a block would lower prices most where C3a already passes and least where it fails worst.
- The same holds against production gas: mid-curve, above ecomin, < 6.5 × production gas is 0.14 in 2019/2020 and 0.22–0.39 in 2021–2025.

**3. What stays true (NEXT-5 card 1's level half).** Above ecomin, 54–64 % of PJM's mid-curve CC capacity is offered below 6.5 × delivered gas in **every** year. The model's committed rung sits at 6.4–7.1 ×. That is the same all-year level wedge NEXT-5 found (+$7–10.5/MWh). It is flat across years, so it cannot separate 2019/2020 from 2023/2024.

## Card 2 — the CC volume over-run: commitment or loading?

**Energy split** (bench CC_REGULAR plants, TWh, model − actual). `on` = extra on-hours × actual loading; `load` = model on-hours × loading difference. On-threshold 5 % of nameplate; the on-hours term is robust at 2 % and 10 %.

| year | gap | **on-hours** | **loading** | extra-on energy in actual off-runs < 7 d / ≥ 7 d | starts model / actual | C1 CC |
|---|---|---|---|---|---|---|
| 2019 | +11.0 | +5.8 | **+5.2** | 7.9 / 0.6 | 2,954 / 2,004 | FAIL |
| 2020 | +14.2 | +8.4 | **+5.7** | 9.4 / 0.9 | 2,317 / 2,355 | FAIL |
| 2021 | +1.0 | +5.7 | **−4.7** | 9.4 / 0.8 | 3,329 / 2,873 | pass |
| 2022 | +11.3 | +6.6 | **+4.7** | 9.9 / 0.5 | 3,060 / 2,932 | FAIL |
| 2023 | +8.3 | +5.4 | **+3.0** | 9.2 / 0.6 | 2,251 / 2,199 | FAIL |
| 2024 | −0.6 | +5.0 | **−5.6** | 7.4 / 0.4 | 2,599 / 2,209 | pass |
| 2025 | −7.9 | +2.2 | **−10.0** | 6.4 / 0.3 | 2,343 / 2,092 | pass |

- **Commitment is a constant bias, not the year signal.**
  - The model has +2 to +8 TWh of extra on-hours in every year, pass and fail alike.
  - It sits almost entirely in the real plant's short off-runs: overnight/weekend cycling under 7 days.
  - Under 1 TWh sits in ≥ 7-day outages, so availability is not the driver (consistent with pjm-h21).
  - The low-CF third runs 250–440 h more than actual (2019–2024).
- **The model does not under-cycle.** Its start counts equal or exceed CAMPD's in every year, so a min-run / start-count constraint has nothing to bind on. What differs is **where** the on-hours fall, not how many starts there are.
- **The year signal is loading when on.** It is positive in exactly the four C1-fail years (+3.0 to +5.7) and negative in the three pass years (−4.7 to −10.0). That is economic dispatch above min-load: the merit-order position of the CC econ ladder against coal and imports, year by year.

**Card 2b — the commitment floor's window.** `cc_mustrun_per_plant` forces each plant's committed tranche on in its top-`online_frac` **system-load** hours.

| year | window energy (committed MW × window h, upper bound) | of which in hours the real plant was OFF | low-CF third: pooled online_frac − own-year on-share |
|---|---|---|---|
| 2019 | 186.0 | 28.0 | +0.20 |
| 2020 | 190.4 | 20.8 | +0.10 |
| 2021 | 202.1 | 27.9 | +0.22 |
| 2022 | 210.1 | 26.7 | +0.12 |
| 2023 | 220.5 | 25.1 | +0.06 |
| 2024 | 220.5 | 20.2 | +0.00 |
| 2025 | 220.5 | 24.2 | +0.02 |

- 20–28 TWh/yr of the floor window (an upper bound: availability ignored) falls in hours the real plant was off. It is placed by system load, not by the plant's own commitment.
- D-2 attributes 6.7–21.9 TWh/yr of CC energy to this floor.
- **Not year-discriminating:** the off-hours share is flat, and the pooled-vs-own-year excess is largest in 2019 and 2021, which split fail/pass.
- It is a real rule-17 placement question, and a **structural** one. It is not a C1 lever.

## Why card 3 (a design card) is not written

A cheaper CC block is admissible only with a real commitment constraint (rules 1/19), and it must be year-discriminating. Measured here:
- **(i)** the cheap block is the **min-load block**, and its above-ecomin share **anti-correlates** with the C3a miss;
- **(ii)** the CC over-run's year signal is **loading**, while commitment is a constant bias the model already over-cycles into.

So no zero-fitted-parameter design with a year-discriminating prediction exists on this evidence. Solving one would be selecting a mechanism by residual (rule 1).

**One structural reading is recorded, not chartered.** In PJM the min-load block is inflexible once committed and cannot set LMP. In the keeper, the CC committed rung is an LP-dispatchable tranche (0..cap outside the floor window). NEXT-14 found it marginal in 11 % of 2020 low-end hours, which is a fractional-commitment artifact. The real-market form is "min-load is a price-taker **when committed**, with commitment placed by the plant's own economics". That is the `gas_commitment_bridge` family: P0 run pattern → min-load floor, **replacing** `cc_mustrun_per_plant`'s system-load window (rule 19).
- That family is **R** for PJM (pjm-142), killed for a different purpose (overnight price amplitude, pool 1.4 GW vs a 3 GW bar).
- This finding is new evidence for a different phenomenon: rule 17 placement plus the committed rung as a price-setter.
- Its volume sign cannot be predicted at zero LP (it needs P0's run pattern), and nothing here says it is year-discriminating. **Owner's call whether to charter it.**

## Verdict

| object | status | next test |
|---|---|---|
| C3a 2019/2020 | **OPEN.** The cheap CC block is refuted as the lever (min-load block; year order inverted). | The one year-discriminating quantity measured on the CC side is **loading when on**. Next: split the 2019/2020 vs 2023/2024 loading term by zone and hour against the coal econ bid and net interchange, from the committed payloads and the bench (zero LP). |
| C1 CC_REGULAR 2019/2020/2022/2023 | **OPEN.** Commitment falsified as the year driver: constant +2–8 TWh bias, model over-cycles, extra hours in short real off-runs. | Same loading split, plus the NEXT-6 net-interchange ledger by year. |
| `cc_mustrun_per_plant` window placement | **OPEN, structural (rule 17), not a C1 lever.** 20–28 TWh/yr of window in real off-hours. | Owner decision on a P0-pattern bridge replacing the system-load window (reopening `gas_commitment_bridge` R on new evidence). |
| COAL_BIT 2019/2021, CT_PEAKER 2021, C3a/C3b 2022, C3c | OPEN, unchanged | as NEXT-13/14 |

Nothing here is called a model-class limit.

**Retrievability (rule 34(e)).** No bundles were produced. Every number above is in the three committed JSON artifacts. The offers corpus is gitignored (licensing, size) and re-fetches with `fetch_pjm_energy_offers.py --years 2019 … 2025` (~3.5 min/month, ~2 h at 3 parallel).
