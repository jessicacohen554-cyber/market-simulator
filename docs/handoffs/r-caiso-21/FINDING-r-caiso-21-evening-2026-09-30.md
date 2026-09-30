# FINDING — R-CAISO-21: the evening (h17–22) under-price is a DA-basis effect plus the tail. No lever. Nothing built.

Keeper: `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25). Zero LP.
Probe: `scripts/probes/_rcaiso21_evening_phase0.py`. Outputs: `results/calibration/_rcaiso21/partA_price.json`,
`partB_tail.json` (gitignored scratch; every number cited is below).
Clock: the model's fixed-PST hour-of-year, as `_rcaiso10_object2_price_setter.py`.
Hubs: NP15→TH_NP15, ZP26→TH_ZP26, SP15_rest→TH_SP15 (LA_BASIN/SDGE DLAPs: DAM only after 2022).

## 1. The gated basis is RT, and on RT the evening gap is small

C3a scores the model against measured **RT** (DA is the "DART premium, not gated" diagnostic,
`scripts/calibration_verdict.py:2351`, `:2451`). SP15_rest, model − measured, $/MWh, h17–22:

| Year | vs DAM | vs RTM | Measured DA − RT (evening) |
|---|--:|--:|--:|
| 2022 | −7.8 | **+7.0** | +14.8 |
| 2023 | −19.4 | **−3.7** | +15.6 |
| 2024 | −10.2 | **−2.5** | +7.6 |
| 2025 | −4.4 | **−1.2** | +3.2 |

The "evening under-price" carried from earlier lanes is measured against DAM. Of the DAM gap, **the measured
DART spread accounts for 72–80 %** (2023: 15.6 of 19.4; 2024: 7.6 of 10.2; 2025: 3.2 of 4.4). The LP clears
one energy market on marginal cost; it has no DA risk premium, and adding one would be a fitted adder
(rules 1 / 13). The same pattern holds in every zone (NP15 RT evening −0.5 / −3.9 / −2.4 in 2023–25).

## 2. What remains on RT is the tail

SP15_rest RT evening residual split at each year's measured evening p95 (contribution to the h17–22 mean):

| Year | Residual | from top-5 % hours | from the other 95 % |
|---|--:|--:|--:|
| 2022 | +6.95 | −5.63 | +12.58 |
| 2023 | −3.78 | −3.04 | −0.75 |
| 2024 | −2.54 | −2.19 | −0.35 |
| 2025 | −1.21 | −1.44 | +0.23 |

In 2023–25 the body of the evening is within $0.75/MWh of measured RT. The under-price is scarcity-event
hours (July 2023 −29.8, July 2024 −13.6 by month) — the C3c price tail, **link 4**. 2022's evening is
over-priced, in every window (a level effect of that year, already CALIBRATED).

### 2b. The ramp-peak shape, on RT

SP15_rest model − measured by hour, h16–21:

| Year | Basis | h16 | h17 | h18 | h19 | h20 | h21 |
|---|---|--:|--:|--:|--:|--:|--:|
| 2023 | RT | +1.3 | −4.0 | **−13.9** | −5.3 | −3.5 | −0.7 |
| 2023 | DA | −14.6 | −30.4 | −41.4 | −25.7 | −13.6 | −4.8 |
| 2024 | RT | +1.1 | −3.3 | **−6.0** | −2.1 | −3.0 | −1.0 |
| 2024 | DA | −5.3 | −14.6 | −22.5 | −12.4 | −7.3 | −3.5 |
| 2025 | RT | +0.3 | −1.1 | −1.1 | −0.2 | −1.4 | −2.0 |

The flat evening plateau earlier lanes attributed to storage pinning (R-CAISO-11/13, caiso-127) is real on
RT too, but at about a third of its DA size, and it is fading as the fleet grows (2025 ≈ flat to measured).
Every storage lever on that object is already `R`/`I`/`G` (`caiso_da_rt_two_settlement` R,
`storage_daily_cycling` G, `ercot_storage_adaptive_expectation` I, `battery_dispatch_adder` K at 0). The one
untested pointer is the aggregated battery representation (caiso-170 re-point), a large build whose RT
payoff is bounded by the h18 residual above.

## 3. Consequence for the supply decomposition

The handoff asked to decompose supply in the under-priced hours. On the gated basis there is no body
under-price to decompose; the hours that are under-priced are the tail hours, so that decomposition
(imports by corridor, storage vs Outlook, hydro, CT) belongs to R-CAISO-22 and is routed there. The DSW
h18–23 import shortfall (R-CAISO-19 §1) would, if anything, *raise* the evening price, so it is not a cause.

## 4. Matrix check

No CAISO cell adjudicates a DART premium. `da_virtual_bids` reads `U` for CAISO, but its field is
`pjm_da_virtual_bids` (PJM-gated) and it moves DA volume, not the RT price C3a scores — not an admissible
lever here. No cell was tested, so no cell changes.

## 5. Side finding on the gated basis (not this link's scope)

The larger RT shape defect is **daytime**, not evening: h6–16 the south is over-priced and the north
under-priced, 2023–25 —
SP15_rest h10–16 +9.7 / +10.9 / +7.0; ZP26 +10.8 / +10.7 / +7.1; NP15 −4.8 / −7.9 / −3.6 $/MWh.
The model's NP15–SP15 midday spread has the wrong sign. This compresses the reported diurnal amplitude
(71 % of measured in 2023 and 2024). Candidate cause: Path 15/26 congestion direction or southern solar /
curtailment in the midday. Offered to the owner as an option, not opened here.

## 6. Decision

No admissible, structural, measured lever for link 3. Nothing built, no solve, keeper unchanged.
Next choice put to the owner as a decision card.
