# FINDING — SPP-79: the 2019–21 C3a over-level is not a 2019–21 defect (zero LP, 2026-09-25)

Keeper `2026-09-24-r-spp-corrected-inputs` (bundle `results/calibration/rspp_span`).
Probe: `scripts/probes/_spp79_c3a_cancellation.py`. It reads only the committed keeper hourlies and
the committed actual LMP. **No LP, no shard, no bundle.**

## 0. Headline

- **The body over-price is the same in every year, 2023–25 included.** Contribution to the annual
  load-weighted mean-price error: low side (RT ≤ $10) **+5 to +14 %** and ordinary hours
  ($10 < RT < p67) **+8 to +16 %**, every year 2019–2025.
- **What differs between the failing and passing years is the UPPER TERCILE**, not the body.
  RT p67–p99 contributes **−5 to −8 %** in 2019–21 (ex-Feb) but **−15 to −19 %** in 2022–25.
- **So 2023–25 pass C3a by cancellation**, a body over-price netted against an upper-tercile
  under-price. 2019–21 fail because their upper tercile is small enough that the body shows
  through. A 2019–21-specific lever does not exist to be found.
- **The year differential lives in the real market, not the model.** RT's upper-tercile implied
  heat rate (mean RT over Henry Hub) was 12.5 / 13.7 / 11.9 in 2019 / 2020 / 2021-exFeb and
  **13.9 / 16.4 / 21.0 / 13.5** in 2022–25. The model's stays at 10.0–14.9 throughout.
  Upper-tercile $ gap (RT − model): 5.1 / 2.9 / 4.4 → 21.4 / 10.5 / 13.5 / 12.2.

## 1. Table (demand-weighted on the model's zonal demand; see §3 for the basis caveat)

| year | err % | low ≤$10 | ordinary | upper p67–p99 | top 1 % | up RT $ | up model $ | up RT HR | up model HR |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | +8.2 | +13.6 | +13.7 | −8.0 | −11.2 | 32.2 | 27.1 | 12.6 | 10.6 |
| 2020 | +14.1 | +14.2 | +14.0 | −5.0 | −9.1 | 27.5 | 24.8 | 13.5 | 12.2 |
| 2021 exFeb | +10.8 | +9.8 | +15.0 | −5.6 | −8.3 | 46.4 | 42.0 | 11.9 | 10.8 |
| 2022 | −7.5 | +5.2 | +8.9 | −15.2 | −6.4 | 86.2 | 66.2 | 13.4 | 10.3 |
| 2023 | −2.4 | +11.2 | +10.4 | −15.2 | −8.8 | 41.5 | 31.1 | 16.4 | 12.2 |
| 2024 | −4.0 | +14.1 | +9.0 | −18.2 | −8.9 | 44.7 | 32.2 | 20.4 | 14.7 |
| 2025 | −1.1 | +12.9 | +11.7 | −14.7 | −10.9 | 47.8 | 35.9 | 13.6 | 10.2 |

2021 all-hours reads +0.5 % only because Uri's February over-shoots the top 1 % (+6.1 % upper,
−29.3 % top-1 %); with February out, 2021 behaves like 2019–20.

## 2. What this means for the lever queue

- **Fixing the body alone would break the train tier.** The low-side object (SPP-74/75: thermal
  staying online, the gas half R) and the ordinary-hours LEVEL object (SPP-74: no measured input
  names it) together carry roughly +20–28 % in 2023–25. Removing them without the upper-tercile
  object would move 2023–25 C3a to about −15 to −20 %, outside ±10 %.
- **The upper-tercile object is SPP-74's C3b-2022 "offer-shape" object**: marginal gas at HR 8–9
  against an RT-implied 11–13. It is xiso §10-refused by construction. It is now shown to be **the
  thing the train-tier C3a pass rests on**, in every year from 2022 on.
- **The one year-invariant multiplier (0.93) sits across two opposite errors.** That is permitted
  under rule 1's 2026-09-05 carve-out (condition (b)/(c) are met: one config, ex ante). It is
  stated here so no successor reads the 2023–25 C3a PASS as evidence that the body is right.
- **No shards were launched.** Phase 0 found no admissible 2019–21 mechanism. The owner agreed
  that launching the seven-year shard fan-out depends on a mechanism turning up.

## 3. Open, routed rather than built

1. **Why the real SPP upper tercile got dearer from 2022.** Implied HR 12–14 → 16–21. Candidates
   (unmeasured here, not asserted): RT uncertainty or ramp premia that a perfect-foresight LP
   cannot price, a change in SPP scarcity-pricing design, or wind-share growth. The object needs
   a measured, forward-reproducible driver before any cell moves (rule 13).
2. **Basis caveat.** This probe weights by the model's zonal demand. The scorer's C3a uses the
   bench `rt_lw` basis, so annual errors differ by a few points (registered C3a 2019 / 2020 / 2021 =
   +13.3 / +21.2 / +10.0 %). The bucket split is the finding, not the level.

## 4. Rules and state

- No keeper, config, flag or scalar changed. No cell verdict changes. The queue note in
  `docs/mechanism-testing-matrix.md` §5.7 carries the DO-NOT-REDO line.
- Retrievability (rule 34(e)): no bundle was produced, so there is nothing to promote.
