# FINDING — the 2021 overprice is NOT a capacity story and NOT the 2023 config; it is the flat Uri-contaminated annual gas basis. A real but small EIA-860 vintage gap is found and quantified. **ZERO LP.**

> Owner question, 2026-09-09: *"I also want to do an audit of whether we're using
> the correct EIA 860 data vintage for 2021 and 2022 to actually reflect the right
> capacity available in each year because the crazy overprice in 2021 seems like
> it's a capacity thing not offer curve or merit order. Or is it that 21-23 are on
> the same model and 24-25 different? Like are we using market config from the
> 2023 outlier to try to price 21-22?"*
>
> Both hypotheses are tested here from committed artifacts and this session's own
> solve logs. **No LP was spent on this audit.**

## 0. Bottom line

| question | answer |
|---|---|
| **Is the 2021 overprice a capacity availability problem?** | **No.** §2 is decisive: the model gets the ONE genuine scarcity month (Feb 2021, Uri) right to **−3.3 %**, and misses every *slack* month by **+82 % to +207 %**. A capacity shortage does the opposite. |
| **Is the EIA-860 vintage handling wrong for 2021/2022?** | **There is a real gap, and it is far too small to matter here** — the retired-unit injection window covers **2023–2024 only**, so **35.8 MW** of 2021 and **510.2 MW** of 2022 Texas retirements are missing from those years' fleets. 35.8 MW is **0.05 %** of a ~70 GW peak. §1 |
| **Are 2021–2023 on one config and 2024–2025 on another?** | **Yes, exactly that** — and the 2021–2023 config *was* identified on 2023. §3 |
| **Is that why 2021 overprices?** | **No**, and this was already adjudicated: the ×33 peak bands carry **0.091 %** of 2021 dispatch and are never live below **$51.57**. §3 confirms it independently — the miss lives in the *median* months, where those bands never bind. |
| **What is it?** | **The delivered-gas LEVEL.** The model runs 2021 at **$8.62/MMBtu flat on all 8,760 h** against **$1.99** in 2023, from an EP basis of **+5.28 (corr +5.78) $/MMBtu** vs **+0.00 (corr +0.50)**. At a CC heat rate that is **≈ +43 $/MWh** — which is the observed non-Uri miss. §4 |

---

## 1. THE VINTAGE AUDIT — how the per-year fleet is actually built, and the one real gap

ERCOT's backcast fleet is **not** built from a per-year EIA-860 vintage. It is built
from **one canonical snapshot — the EIA-860 2025 Early Release**
(`fleet/models.py::EIA860_OPERABLE_VINTAGE = 2025`) — and then corrected toward
each solve year by two mechanisms:

1. **The COD ramp** (de-build direction): units are masked offline before their
   commercial online date and after their retirement. Measured in this session's
   own runs — and the gradient is exactly right:

   | year | unit-months masked | units fully absent |
   |---|---|---|
   | 2021 | 1,669 | **117** |
   | 2022 | 945 | 66 |
   | 2023 | 467 | 18 |

2. **`eia860_generator_retired_within_window.parquet`** (re-build direction):
   whole units that retired *inside* the backcast window and are therefore
   absent from the recent operable snapshot are injected back.

**The gap is in mechanism 2.** The committed parquet covers only:

| retirement year | rows (all ISOs) | MW | ERCOT rows |
|---|---|---|---|
| 2023 | 325 | 9,474.5 | 10 |
| 2024 | 152 | 5,413.0 | 6 |

**There is not a single row for a 2021 or 2022 retirement.** A unit that was
running in 2021 and retired in 2021 or 2022 is therefore absent from the 2025
operable snapshot *and* absent from the injection — i.e. **missing entirely from
the model's 2021 and 2022 fleet**, which biases capacity **short** and price
**high**, precisely the mechanism the owner's question names.

**Quantified against the full EIA-860 retired schedule** (Texas, the ERCOT proxy):

| retirement year | units | MW |
|---|---|---|
| 2021 | 10 | **35.8** |
| 2022 | 9 | **510.2** |

The largest single missing unit is **Decker Creek (plant 3548), 404 MW gas ST,
retired 2022**; 2021's entire missing set is 35.8 MW, the biggest being two
10.5 MW Sam Rayburn CTs.

**Verdict: the gap is REAL and worth repairing under rule 14 `[R-ACCURATE]`
— rebuild with `process_eia860.py --retired-window-from 2021` — but it CANNOT
be the 2021 defect.** 35.8 MW is **0.05 %** of ERCOT's ~70 GW peak. It is
carried here as a named follow-up, not as an explanation. (It is more material
for **2022**, at 510 MW, and 2022's own C3a should be re-checked after the
rebuild.)

---

## 2. THE DECISIVE TEST — where in the year the miss actually lives

Model monthly load-weighted mean LMP (the keeper's committed 2021 leg) against
the committed monthly RT actual (`bench/ERCOT/2021.json.gz`, `avgLMP.rt_mon`):

| month | model $/MWh | actual $/MWh | diff | diff % |
|---|---|---|---|---|
| Jan | 58.54 | 20.79 | +37.75 | **+181.6 %** |
| **Feb (URI)** | **1,471.01** | **1,521.84** | **−50.83** | **−3.3 %** |
| Mar | 58.44 | 19.42 | +39.02 | **+200.9 %** |
| Apr | 101.13 | 46.80 | +54.33 | +116.1 % |
| May | 59.44 | 23.39 | +36.05 | +154.1 % |
| Jun | 100.37 | 38.39 | +61.98 | +161.5 % |
| Jul | 93.94 | 36.80 | +57.14 | +155.3 % |
| Aug | 88.11 | 35.37 | +52.74 | +149.1 % |
| Sep | 87.98 | 41.57 | +46.41 | +111.6 % |
| Oct | 143.65 | 46.87 | +96.78 | **+206.5 %** |
| Nov | 73.36 | 40.38 | +32.98 | +81.7 % |
| Dec | 59.81 | 25.82 | +33.99 | +131.6 % |

**This kills the capacity hypothesis outright.** February 2021 *is* the capacity
event — Winter Storm Uri, ~20 GW of load shed, the tightest hours in ERCOT's
history — and it is **the one month the model gets right**, to −3.3 %. If the
model were short capacity in 2021, February would be the *worst* month, not the
best. Instead the error sits in the **slack** months, uniformly, in a tight band
around **+150 %**.

That signature — a near-constant multiplicative overprice in every
non-scarcity month, with the scarcity month accurate — is the fingerprint of a
**flat additive cost-level error**, not a supply-stack error. Merit order and
offer shape cannot produce it either: both would distort the *relative*
ordering, showing up as class-mix and shape misses, not as a uniform level lift
with a correct tail.

---

## 3. THE TWO-CONFIG QUESTION — the premise is CORRECT, the conclusion is not

**The owner's read of the structure is exactly right.** ERCOT is a two-config
keeper (owner ruling 2026-08-26), and the split is:

| years | config | CC_REGULAR peak band | `ercot_offer_swcap_clip` |
|---|---|---|---|
| **2021, 2022, 2023** | **CARVE-OUT** | **151.008** (×33) | **True** |
| 2024, 2025 | FORWARD | 4.576 | False |

and the carve-out **was identified on 2023** (`2026-08-25-236-swcap-clip-k33`,
a 2023-only run). So yes: **2021 and 2022 are being priced with a configuration
fitted on 2023.**

**But it is not what breaks 2021, and this was already measured.** ercot-258
adjudicated exactly this hypothesis at zero LP and found the ×33 peak bands
carry **0.091 % of 2021 dispatch** and are **never live below $51.57/MWh** — so
they cannot touch a defect that lives at p5/p25/p50.

**§2 confirms it independently, from the other direction.** The bands can only
bind at the *top* of the stack. The miss is in the **median** months — Jan, Mar,
May, Dec all sit at model $58–60 against actual $19–26. A band that only prices
above $51.57 cannot lift a month whose whole distribution the model puts near
$58 while the actual is $20. The overprice is already fully present *below* the
level at which the 2023-fitted bands do anything.

---

## 4. WHAT IT ACTUALLY IS — measured from this session's own solve logs

| | 2021 | 2023 |
|---|---|---|
| ERCOT zonal gas basis, measured EP | **+5.28** $/MMBtu (corr **+5.78**) | **+0.00** $/MMBtu (corr +0.50) |
| annual delivered gas | **$8.62/MMBtu** | **$1.99/MMBtu** |

**The model prices all 8,760 hours of 2021 off an $8.62/MMBtu delivered gas
level.** That number is an *annual mean* of a monthly series whose February
print is contaminated by Uri, when spot gas reached hundreds of dollars for a
few days. Spreading it flat across the year overprices the eleven normal months
and — because February's own extreme is what produced the mean — leaves February
roughly right.

**The arithmetic closes.** The excess basis is +5.78 $/MMBtu; at a CC heat rate
of ~7.5 MMBtu/MWh that is **≈ +43 $/MWh**. Observed non-Uri monthly misses run
**+33 to +97 $/MWh, median ≈ +47**. The gas level explains essentially the whole
gap, with no appeal to capacity, merit order or offer shape.

This is **ercot-254's diagnosis**, reached there from the fuel side and
corroborated here from the price side; ercot-258 corroborated it from a third
direction. Its monthly repair was built and measured — it halves the eleven
non-Uri months' bias (**+160.8 % → +79.1 %**) — but was **not promoted**,
because two of three pre-registered C1 predictions came back wrong in sign and
C3c regressed 234 → 688 h. The residual **+79 %** is the open item, and
ercot-254's own read was that the cause is *the same defect one resolution
finer*.

---

## 5. What this changes for the lane

* **Do not open a capacity/vintage lane for the 2021 C3a miss.** It is refuted
  on the strongest available evidence — the scarcity month is the accurate one.
* **DO repair the retired-window gap** (`--retired-window-from 2021`) under rule
  14 `[R-ACCURATE]`: 546 MW across 2021–2022 is genuinely missing fleet, it is a
  correctness issue independent of any residual, and at 510 MW it is **material
  for 2022** even though it is negligible for 2021. Re-check 2022's C3a after.
* **The 2021 C3a lever remains the delivered-gas level**, at a finer time
  resolution than annual, and it is the same object ercot-254 left open — not
  the offer curve (rule 1 `[R-STRUCT]`: the carve-out bands are an authorized
  price-tuning channel but they are provably inert here), and not the merit
  order.
* **The two-config structure is real and the owner's instinct about it is
  sound** — a 2023-fitted config *is* pricing 2021–2022. It happens not to be
  the 2021 culprit, but it remains a standing structural question for 2022,
  whose own residual has not been decomposed this way.

---

*Generated by [Claude Code](https://claude.ai/code)*
