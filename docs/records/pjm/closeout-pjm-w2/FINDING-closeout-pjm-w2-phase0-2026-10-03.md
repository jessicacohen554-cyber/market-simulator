# FINDING — closeout-PJM-w2 phase 0: the Elliott overlay has no reach; the PJM §3.6 queue is exhausted (ZERO LP)

**Verdict: NOT CHARTERED.** Nothing built, solved or registered. Keeper `2026-10-03-closeout-pjm-nuc-keeper`
unchanged (NOT-YET). Bars: `PRECOMMIT-closeout-pjm-w2-phase0-2026-10-03.md` (plan §3.6 bars, unchanged).
Probe `scripts/probes/_closeoutpjmw2_elliott_overlay_reach.py` → `results/phase0/pjm/_closeoutpjmw2_elliott_overlay_reach.json`.

## 1. What a perfect Elliott fix would be worth (ceiling)

On the scorer's zonal load-weighted RT basis (the probe reads 2022 at −17.2 % / 0.298; the scorer's committed
bench gives −16.7 % / 0.293):

| 2022 | C3a | C3b |
|---|---|---|
| all hours | −17.2 % | 0.298 |
| 23–26 Dec removed | **−9.9 %** | **0.182** |

So Elliott is the whole 2022 price failure. Even a perfect fix leaves C3a only 0.1 pp inside the ±10 % band.

## 2. Reach of the step-4 overlay (event-increment form, the most favourable one)

The overlay takes the published RTO forced outage (`gen_outages_by_type`, lead 0, 06:00 daily snapshot), minus its
20–22 Dec mean, minus the model's own rise in unavailable thermal MW. It withdraws that from the keeper's in-LP
thermal headroom. Window: 20–29 Dec 2022 (240 h).

| Dec 2022 | 23 | 24 | 25 | 26 |
|---|---|---|---|---|
| published forced (MW) | 11,914 | 31,078 | 35,844 | 27,058 |
| increment over baseline, net of model rise (mean MW) | +336 | +15,864 | +20,917 | +11,417 |
| keeper headroom, min (MW) | 20,754 | 21,704 | 31,220 | 27,218 |
| headroom after overlay, min (MW) | 20,418 | **5,840** | 10,303 | 15,801 |
| keeper max price | $128 | $127 | $117 | $112 |
| merit-walk upper bound, max | $130 | $265 | $233 | $152 |
| real zonal RT max | $3,720 | $3,615 | $239 | $549 |

- **R2 FAIL: 0 of 240 hours** fall below the `pjm_primary` requirement (0 below requirement + 190 MW, 0 below zero).
  The minimum headroom left is 5.8 GW, so the ORDC ($850/$300) and VOLL never bind.
- **R1 FAIL:** the Dec 23–24 mean is $110.91 on the keeper and $168.72 at the merit-walk upper bound. The bar is
  $800 and real was $948.38, with 18 hours ≥ $800.
- **Timing defect:** the daily 06:00 snapshot reads 11.9 GW on 23 Dec, before the event, but 23 Dec evening carries
  the $3,720 peak. A daily published series cannot place the outage in the hours that priced. Even a perfectly
  timed overlay at the published *daily* level falls short: 23 Dec headroom is 20.8 GW against an increment that
  the snapshot puts at 0.3 GW.

This agrees with census 0b (wave 1) and with R-26. The published daily outage is not big enough or timed well enough
to create scarcity in this LP. Step 4 is NOT CHARTERED on reach, whatever the wording of R-26.

## 3. The rest of the queue

| step | reading | verdict |
|---|---|---|
| 3 `gas_offer_margin_anchor_vintage` | Recorded price reach is ≤ 1 pp (PJM cell, closeout-PJM R-13 retest). 2022 needs +6.7 pp and 2020 already PASSes (+9.0 %). | not chartered on reach; cell stays R |
| COAL_BIT 2019–21 | R-56: leave open; decommitment is not year-discriminating (#7159) | no candidate |
| CC_REGULAR 2022 | NOT CHARTERED (#7166) | — |
| 2025 C3a/C3b | R-37 documented FAIL, no re-open; `pjm_reserve_pergen_sync` R with DO-NOT-REDO on reserve-product refinement | — |
| Tait 55248→2847 CAMPD remap | a rule-14 hygiene repair (≈ $1–2/MWh on one CT plant), not a lever; it rides the next PJM solve | not a step |

**The PJM §3.6 queue is exhausted at phase 0.** No admissible lever has reach on any failing PJM gate with the data
on disk.

## 4. Owner asks (data or ruling; nothing proceeds without one)

1. **Elliott hourly forced-outage data.** PJM's published *Winter Storm Elliott Event Analysis* (2023) reports
   forced outages hourly and by fuel, peaking at about 46 GW on 24 Dec (the figure PJM reports; verify on intake). The daily snapshot on disk shows 31 GW on
   24 Dec and 11.9 GW on 23 Dec. A digitized hourly RTO series from that report is not in R-26's reopen list,
   which names GADS per-unit data or a daily Z5/M3 series. Ruling asked: is it admissible as a backcast outage
   overlay (rule 13, measured outage, windowed)? Phase-0 reach, pre-computable on receipt: 23–24 Dec headroom is
   20.8–21.7 GW, so an hourly rise of ≥ ~21 GW over baseline would bind the ORDC.
2. **COAL_BIT 2019–21 frontier text** (R-47/R-55/R-56), still an unsigned DRAFT. With the queue exhausted, the
   owner may want the card again.
