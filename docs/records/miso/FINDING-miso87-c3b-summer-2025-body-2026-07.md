# FINDING (miso-87, 2026-07-24) — C3b-2025 is a summer *body* price miss; the ledgered scarcity-tail caveat covers only ~38 % of it

**Context.** Second of the two crossings that hold
`2026-07-24-miso-86-netrev-margin` at **NOT-YET**: **C3b price duration/shape,
2025 NRMSE 0.204** against a ≤0.20 veto. Scored from committed artifacts only;
no LP re-solve. The handoff asked whether the miss is monthly **level** or
**shape**, and to check it against the C3a-2025 ledgered caveat (same year, same
direction) before touching anything. Answer: it is a **level** miss,
concentrated in two months, and it is **not** fully covered by the existing
ledger.

## 1. C3b is a 12-point monthly metric, and 65 % of it is June + July

`scripts/calibration_verdict.py::score_price_shape` computes NRMSE over the
**twelve monthly load-weighted prices** — not the hourly duration curve. The
2025 decomposition (model demand-weighted across zones vs `rt_lw_mon`):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model | 40.9 | 42.6 | 34.7 | 33.6 | 37.2 | 39.7 | 41.0 | 36.7 | 37.0 | 34.8 | 36.2 | 40.3 |
| actual | 51.2 | 46.3 | 37.9 | 37.7 | 33.9 | 57.4 | 59.5 | 40.4 | 46.4 | 38.7 | 40.5 | 47.2 |
| Δ | −10.3 | −3.7 | −3.2 | −4.1 | +3.3 | **−17.7** | **−18.5** | −3.8 | −9.4 | −3.8 | −4.3 | −7.0 |
| share of Σ Δ² | 11 % | 1 % | 1 % | 2 % | 1 % | **31 %** | **34 %** | 1 % | 9 % | 1 % | 2 % | 5 % |

**June + July = 65 %** of the squared error; adding January and September brings
it to 85 %. Every month but May is negative — the model is low across the board
in 2025 — but the metric is driven by the two summer peak months.

For contrast the same decomposition in the passing years is diffuse: 2023
(NRMSE 0.081) has no month above 27 % and both signs; 2024 (0.128) peaks at 28 %
in May.

## 2. The ledgered scarcity tail explains ~38 % of the summer gap, not all of it

The C3a-2025 ledger states the annual-mean miss is "the arithmetic tail of the
C3c residual, NOT an independent level error". At **monthly** resolution that
claim is only partly true. Indiana-Hub RT 2025, the 88 hours > $200:

| month | hours > $200 | max $/MWh | $/MWh the >$200 hours add to the monthly mean | monthly Δ |
|---|---|---|---|---|
| Jun | 21 | 1,202 | **+7.0** | −17.7 |
| Jul | 13 | 1,783 | **+5.5** | −18.5 |
| Sep | 8 | 1,598 | +4.8 | −9.4 |
| Jan | 16 | 414 | +1.9 | −10.3 |

The tail hours are indeed concentrated where C3b hurts — but they contribute
only **$7.0 of the −$17.7** June gap and **$5.5 of the −$18.5** July gap
(≈38 % and ≈30 %). Censor the actual series at $200 and June still reads $50.4
against the model's $39.7.

So roughly **$11–13/MWh of each summer month's miss sits in the body of the
distribution, below $200** — outside the scope of the C3c
scarcity-representation ledger, which is specifically about an administrative
ORDC/RCPF curve a deterministic LP cannot form. **This portion is currently
unledgered and is a genuine model miss.**

## 3. What it is not

* **Not the gas-price anchor.** MISO citygate 2025 summer gas (Jun $2.72,
  Jul $2.95, Aug $2.62/MMBtu) sits *below* the `GAS_OFFER_MARGIN_ANCHOR` of
  3.0492, so the net-revenue margin's below-anchor firming *raises* the CC offer
  in exactly these months. The margin form pushes summer 2025 prices up, not
  down; it cannot be the source of a low-price miss.
* **Not the companion C1 defects.** Restoring Riverside and Cottonwood to the
  merit order (see `FINDING-miso87-c1-per-plant-input-defects-2026-07.md`) adds
  ~1.4 GW of under-offered CC, which pushes summer prices **further down**. The
  two crossings pull in opposite directions and are not jointly closable by that
  fix.

## 4. Open — needs its own charter

The residual question is why the model's 2025 summer **body** clears $11–13/MWh
low while 2023 and 2024 summers do not. The one structural signature visible in
the committed hourlies is that 2025 is the year the model leans hardest on coal
(`COAL_PRB` 145.4 TWh vs 122.3 in 2023, `CC_REGULAR` down to 122.8 from 134.0)
— a merit-order composition shift, not a level knob — but nothing here
establishes that as the cause and no attempt was made to close it.

**Do not close this with an offer adder, a summer multiplier, or by widening the
C3c ledger to cover it** (rules 1/10; the ledger's own scope is the >$200
administrative tail, and §2 shows most of this miss is below that). The honest
next step is a charter on 2025 summer body price formation, scored
leave-one-year-out within 2023–2025.
