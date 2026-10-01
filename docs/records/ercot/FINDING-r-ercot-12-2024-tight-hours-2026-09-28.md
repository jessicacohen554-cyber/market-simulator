# FINDING — R-ERCOT-12: the 2024 "tight-hour under-pricing" is one VOLL-shed hour, not a new object

**Session:** R-ERCOT-12, 2026-09-28. **Zero LP.** Keeper `2026-09-28-r-11-parish-split` vs the superseded `2026-09-27-r-10-parish-fuelscope` (`r_ercot10_parish_span`, read from `fb116767^`), both from committed hourly sidecars. Probe: `scripts/probes/_r_ercot12_2024_tight_hours.py <old_hourly_dir>`.

## Headline

- **87 % of the 2024 flip is ONE hour.** The superseded keeper shed **3.1 MWh at Panhandle on 2024-05-07 19:00** (hour 3067). That set every zone to the $5,000 VOLL. The Parish capacity correction removed the shed and the hour now clears at $1,108. Actual RT was $3,055 (λ $2,368 + RTORPA $179, PRC 4,778 MW).
- **Share of the old→new LW delta (probe basis):** that hour −0.444 of −0.513 $/MWh. In C3a points: **−1.53 from the shed hour, −0.24 from all other 8,759 hours.**
- **So the prior keeper's 2024 C3a PASS (−8.8 %) was knife-edge on 3 MWh of load shed.** Remove it and the capacity correction alone costs ~0.2 pts. The "74 hours > $100, $229 → $174" statistic in the R-ERCOT-11 RESULT is dominated by the same hour ($5,000 → $1,108 inside a 74-hour mean).
- **No arm is admissible from this object.** Restoring the shed would be restoring an outcome, not a mechanism (rule 1). The shed was never a structural feature: net reserve families and ORDC shortfall are identical in both keepers at that hour (NonSpin short 3,357 MW, ORDC total short 5,601 MW, both runs).

## What the rest of the 2024 gap is (unchanged by the capacity correction)

Gap by actual-price band, $/MWh of annual LW mean (keeper; the superseded keeper is within ±0.02 in every band except ≥ $1,000):

| actual band | hours | model mean | actual mean | gap |
|---|---|---|---|---|
| < $0 | 172 | 7.9 | −5.0 | +0.25 |
| $0–25 | 5,520 | 20.8 | 16.0 | **+3.04** |
| $25–50 | 2,322 | 31.1 | 33.1 | −0.51 |
| $50–100 | 556 | 44.8 | 67.4 | **−1.44** |
| $100–200 | 129 | 68.4 | 137.5 | **−1.02** |
| $200–1,000 | 51 | 90.3 | 345.6 | **−1.49** |
| ≥ $1,000 | 10 | 378.5 | 1,739.4 | **−1.55** (old −1.10) |

- **It is a compressed distribution:** trough hours over-priced, every hour above $50 under-priced. That is the C3b shape object and the ledgered C3c tail, not a capacity shortfall.
- **Actual high prices are energy-offer prices, not reserve adders.** In actual ≥ $200 hours: $574 = λ $553 + RTORPA $25 + RTORDPA $5, at a measured PRC averaging 6,316 MW. ERCOT was not in ORDC scarcity. It was clearing on high energy offers — the conduct object recorded in the C3c ledger (ercot-161/162: storage and other offers made the ≥ $500 stack).
- **The model is simultaneously deep in modelled reserve scarcity in the same hours** (hour 3067: ORDC held 1,584 of 7,185 MW) yet prices lower. This is the same scarcity-formation object the ercot-95…231 exhaustion record closed. The capacity-correct fleet adds no new evidence to it.
- **January (Winter Storm Heather, Jan 14–16) runs the other way:** the model over-prices at $100–228 against $40–300 actual.

## Verdict

- **Lever-queue item 1 closes at phase 0 with no arm.** The named object dissolves into:
  1. a single-hour VOLL shed knife-edge, which is not a mechanism; and
  2. the adjudicated mid-band/tail compression (C3b/C3c, DO-NOT-REDO ercot-95…231).
- **Offer multipliers stay frozen** (rule 1(c)).
- **2024 NOT-YET stands at full magnitude** (C3a −10.7 %, C3b 0.189). It is reported, not reverted (rule 14).
- **The honest reading of the prior 2024 PASS:** it rested on 3.1 MWh of shed. The current NOT-YET is the more faithful number.
