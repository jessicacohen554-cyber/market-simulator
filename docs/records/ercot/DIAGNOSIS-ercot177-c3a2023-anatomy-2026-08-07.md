# DIAGNOSIS — ercot-177: the anatomy of C3a-2023, measured on committed artifacts

**Session ercot-177, 2026-08-07. NO SOLVE, NO REPLAY, keeper UNCHANGED.** Built
entirely from artifacts of record — the keeper bundle's `hourly/` sidecars
(rule 15's purpose), the committed actual-LMP series, and **ERCOT's own published
ORDC/reserve series** (`data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet`).

Reproduce: `python scripts/probes/ercot177_c3a2023_anatomy.py --json results/calibration/ercot177_c3a2023_anatomy.json`

Keeper: `2026-08-07-run176-control-offline-increment`, C3a-2023 **−32.4 %**.

---

## 1. The miss is August and September, and almost nothing else

Model 2023 load-weighted RT **$43.45** vs actual **$64.32** (−32.4 %, the scorer's
number reproduced exactly off the sidecars).

| month | model lw | actual lw | share of annual $-gap |
|---|---|---|---|
| Jan–May | 21–27 | 22–32 | **5.4 % combined** |
| Jun | 64.83 | 74.55 | 4.5 % |
| Jul | 36.67 | 48.38 | 6.1 % |
| **Aug** | **118.32** | **220.61** | **55.9 %** |
| **Sep** | **55.49** | **109.75** | **25.4 %** |
| Oct–Dec | 22–29 | 23–32 | 2.8 % combined |

**Aug + Sep = 81.3 %** of the annual load-weighted gap; Jun–Sep = 91.9 %. Every
non-summer month is within a few $/MWh, and the **overnight body is slightly
OVER-priced** (h00–h09 the model runs $2–5/MWh above actual; in the $0–50 actual
band across Aug–Sep the model is +6,823 $/MWh-hours *too high*).

This is not a level-calibration problem. **It is ~50–180 summer-afternoon hours.**

## 2. Inside Aug–Sep the gap is extraordinarily concentrated

| | share of the Aug–Sep gap |
|---|---|
| top 10 hours | 29.3 % |
| top 25 hours | 54.6 % |
| **top 50 hours** | **80.6 %** |
| top 100 hours | 103.1 % |
| top 200 hours | 110.5 % |

Over 100 % because the model **over**-prices the remaining ~1,300 hours, which
partly offsets. Hour-of-day: the entire gap lives in **h12–h19** (peak +$325 at
h15, +$288 at h18); every hour from h20 to h11 is neutral or negative.

Tail counts, Aug–Sep: actual **132** hours > $200 vs model **55**; actual **52**
hours > $1000 vs model **16**. The model produces ~40 % of the tail hours.
**Model shed hours: 3.** The model is not in shortage — it is pricing a tight
afternoon on a cheap marginal offer.

## 3. THE DECISIVE RESULT — it is the ENERGY STACK, and the scarcity machinery is already right

ERCOT publishes its RT price decomposition: `RT = system_lambda + RTORPA +
RTORDPA`. The model's is `price = energy_only + ordc_adder + rtordpa_overlay`.
Compared component-for-component on the **top-50 Aug–Sep gap hours**:

| | MODEL | ERCOT actual |
|---|---|---|
| RT price | 468.15 | **1,922.30** |
| **energy-only component** | **360.23** | **1,889.63** ← `system_lambda` |
| scarcity adder | 107.92 | **104.82** |
| online reserve (MW) | 5,902 held | 5,471 PRC |

**Decomposition of the $1,454/MWh mean miss: ENERGY-STACK term $1,529 (100.2 %),
SCARCITY-ADDER term −$3 (−0.2 %).**

Three consequences, each of which closes a lane:

1. **The ORDC / RTORPA machinery is NOT the defect and must not be re-tuned.**
   ERCOT's own published adder averaged only **$104.82** on the worst 50 hours —
   the model produces **$107.92**, a 3 % overshoot. Across all of Aug–Sep,
   ERCOT's adder means $6.78 (175 hours > 0) against the model's $4.61
   (116 hours). Deepening the ORDC would be fitting a mechanism that is already
   correct, and would break 2024/2025.
2. **The reserve LEVEL is not the defect either.** Model holds 5,902 MW against
   ERCOT's measured PRC of 5,471 MW on those hours (+431 MW); across Aug–Sep
   8,276 vs 7,474 (+802 MW). The model is *slightly tighter* than reality and
   still prices 4× lower. This independently corroborates the **CLOSED** reserve
   family (ERCOT-102/107/108, ercot-175) from a new instrument.
3. **ERCOT's real-time ENERGY price itself was $1,890 with only ~$105 of adder.**
   Scarcity in Aug–Sep 2023 was priced *in the offer stack*, not by the ORDC. At
   ~$2.6/MMBtu August gas a CT's SRMC is ≈$29/MWh, so $1,890 is roughly a
   65×-gas offer: **opportunity-cost / scarcity-anticipating conduct at the
   margin**, which the model's cost-based stack clears at $360.

This is the same object ercot-175 measured from the other side ("the missed
>$200 formation is a MARGINAL-PRICE phenomenon, not a quantity phenomenon";
reality cleared p50 $462 over ≥56 GW of sub-$200 offers) — now decomposed
against ERCOT's own published price components, which names *which* component
owns it.

## 4. The named lead: the offer surface's top conditioning bin is DILUTED

The armed measured offer surfaces condition on within-year net-load percentile,
`ercot_offer_surface_netload_pcts = [0.8, 0.9, 0.97]`. Measured on 2023:

| bin | hours | actual p50 | actual max | actual mean | model mean |
|---|---|---|---|---|---|
| p0–p80 | 7,008 | 19.3 | 742 | 22.5 | 23.9 |
| p80–p90 | 876 | 27.8 | 696 | 36.8 | 35.2 |
| p90–p97 | 613 | 45.2 | 1,788 | 69.3 | 54.5 |
| **p97–p100** | **263** | **198.2** | **5,046** | **725.6** | **349.0** |

The top bin pools **263 hours whose actual prices span $198 (p50) to $5,046
(max)** under **one** measured ladder — a 25× range. Split finer:

| slice | hours | actual mean | model mean | short by |
|---|---|---|---|---|
| p97.0–p99.0 | 175 | 404.2 | 197.6 | **2.05×** |
| p99.0–p99.5 | 44 | 846.7 | 226.0 | **3.75×** |
| p99.5–p100 | 44 | 1,882.9 | 1,074.4 | 1.75× |

And the bin edge sits **below the phenomenon**: the tail population (actual
> $200) is **181 hours = the top 2.07 % of the year**, i.e. ≈ p98. A p97 floor
therefore pools roughly one-third tail hours with two-thirds non-tail hours, and
a single conditional ladder fitted across that mixture cannot reproduce either
end. The worst relative miss (p99.0–p99.5, **3.75×**) is exactly where the
pooling is most lopsided.

**This is a conditioning-GRAIN property of an existing measured surface** — the
same class of refinement as ERCOT-96's day→hour grain switch of the ERCOT-95
mechanism, not a new mechanism (rule 19 `[R-ONE-MECH]`), and it regenerates for a
forward year from forward net load (rule 13 `[R-MEASURED]`).

**Not yet tested; no field was added and nothing was armed in this session.** The
bin edges must be derived from the tail population's own definition, never swept
against the residual (rule 20 `[R-DOF]`) — see the ercot-178 handoff for the
pre-registration this requires.

## 5. What the model is running in those hours (context, not a lead)

Model class dispatch on the top-50 Aug–Sep hours (mean MW): CC_REGULAR 26,794
(annual 16,535), COAL_PRB 9,486 (4,979), ST_GAS 9,232 (2,212), solar 8,215, wind
7,675, **CT_PEAKER 4,983 (annual 773)**, nuclear 4,929, CC_CHP 4,328,
COAL_LIGNITE 2,473, oil 206 (annual 3). Total 79,880 MW.

The model is already deep into its stack — peakers at 6.4× their annual mean and
oil running — so this is **not** a "cheap capacity still idle" story at the class
level. It is the **price** of the last increment, consistent with §3.

## 6. Bounds this diagnosis puts on the remaining search

* **ORDC / RTORPA / reserve level: CLOSED** by §3 against ERCOT's own published
  series. Do not re-open without new evidence.
* **Capability / availability: CLOSED** — ercot-177's temp-derate refusal
  (`FINDING-ercot177-temp-derate-refused-2026-08-07.md`) on the measured-flat
  ERCOT hot-hour envelope, and §3's reserve-level agreement.
* **Aggregate cheap depth: REFUTED** at ercot-173; **offered-vs-deliverable
  wedge: FILED-REDIRECTED** at ercot-175 (no term reached the 0.60 bar).
* **What remains: the LEVEL of the marginal offer in ~50–180 summer-afternoon
  hours**, against a corpus that can measure it directly — the delivery-2023
  NP3-965 SCED corpus (315 shards, on disk since ercot-157), which carries the
  submitted offer curves and the marginal resource per 5-minute interval.

## 7. What "under 10 %" requires, quantitatively

C3a-2023 must move from −32.4 % to ≥ −10 %, i.e. the annual load-weighted mean
from **$43.45 to ≥ $57.89** (+$14.44/MWh), which is **69 % of the annual $-gap**.
Since Aug + Sep hold 81.3 % of that gap, the whole job is those two months: their
combined mean must rise from **$78.52 to roughly $128** (actual $140.14). In tail
terms that is approximately the 132 actual > $200 hours (model 55) and 52 actual
> $1000 hours (model 16) — i.e. **C3a-2023 and C3c-2023 are the same object**,
and C3a cannot reach the bar while C3c's tail deficit stands. The C3c ledger
records a model-class limitation; it does **not** license leaving C3a failed.

C3b-2023 (0.602) is a price duration/shape metric over the same hours and should
move with them. **C3b-2024 (0.205, bar ≤0.20) is a different root** — the two
2024 shed hours the model over-amplifies to VOLL (ercot-172), whose only
remaining structural route is the multi-week flat plateau used as an hourly
ceiling (ercot-172 fault 3). That lane is **FROZEN** behind the pending
`DECISION-MEMO-ercot-148149-doublecount-2026-08-07.md`, so 2024 is not
addressable without an owner ruling.

## 8. Governance

No solve, no LP, no `ScenarioConfig` field, no run registered, keeper unchanged.
Rule 22: 2023 only, from committed artifacts; no out-of-training year touched.
Rule 28: no cell minted — this is a diagnosis, not a mechanism test.
