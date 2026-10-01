# ADDENDUM — ercot-263: the February object, traced to its cause and KILLED at phase 0

**Session:** ercot-263, 2026-09-09. Parent: `PRECOMMIT-ercot263-c3b-basis-2026-09-09.md`,
`RESULT-ercot263-c3b-basis-2026-09-09.md`. **Zero LP spent. No arm solved, no screen spent.**

Rule 29 `[R-SCREEN]` phase 0 killed the arm before an LP. The five-year shard fan-out the handoff
specified was **not launched**, and this addendum is why.

---

## 1. What the object is

From the basis repair (parent RESULT), 2021 C3b = 0.559 against a 0.20 gate, and **February is
95.7% of the SSE** — model $1,422.13 vs actual $1,767.07, −19.5%. Making February exact scores
**0.1156, a clean PASS**. Within February, from the keeper's committed hourly:

| band | hours | contribution | share |
|---|---:|---:|---:|
| Feb 1–10 | 240 | +$0.07 | 0.0% |
| **Feb 11–14 (onset)** | 96 | **−$179.00** | **52.6%** |
| **Feb 15–19 (deep event)** | 120 | **−$156.07** | **45.9%** |
| Feb 20–28 | 216 | +$5.09 | 1.5% |

The model's storm **starts about two days late**: on Feb 13 the actual cleared $1,000/MWh for
**23 of 24 hours and the model for 1**; Feb 14, 19 vs 6. Once joined it tracks the event
(Feb 15–18: $5,556/$7,896/$8,147/$8,528 vs $6,765/$8,970/$9,002/$8,989) and Feb 19 is **+$66 over**.
No slack and no dump in any hour of the week — the model served all load with capacity to spare.

## 2. The cause — measured, and it is FUEL RESOLUTION

The keeper prices February 2021 gas as an **ordinary month**. Measured from the committed config:

| | Feb 2021 basis ($/MMBtu) |
|---|---:|
| EIA N3045TX3 raw monthly print | **+54.376** |
| **what the keeper actually uses** | **+0.390** |
| (pre-ercot-254 annual form) | +5.278, flat over all 8,760 h |

The keeper runs `ercot_ep_gas_basis_monthly=True` **with** `ercot_ep_gas_basis_corroborated=True`
(ercot-261). February 2021 and December 2021 are the only two months in 2019–2025 that fail
corroboration against the independent EIA-923 Schedule-5 TX plant receipts, so both are replaced by
the mean over that year's corroborated months. **February's $54/MMBtu of Uri fuel cost is
deliberately removed** — and that removal is the 95.7%.

**The removal is correct, and the code already says why** (`data/fuel/basis/ercot.py`, docstring):

> *"the series is a monthly cost/volume RATIO, and February 2021 reads $59.73/MMBtu because Texas
> gas traded near $3 for ~24 days and $100–1,200 for ~4. Applied at monthly resolution the CHEAPEST
> February day still prices gas at $31.26/MMBtu, so all 672 hours clear $200/MWh on fuel alone — the
> measured cause of the ercot-254 re-test's C3c regression (234 → 688 h vs 258)."*

## 3. Every route is closed, and none of the three closures is new

1. **Put the raw monthly basis back** — already tested and rejected at **ercot-254**. It buys C3b by
   making 24 cheap days expensive to make 4 expensive days right, and blows C3c to 688 h against 258
   actual. That is rule 1 `[R-STRUCT]` in its plain form: reaching the right number through a
   mechanism that is not real. **Do not re-run it.**
2. **Resolve the basis DAILY** — the correct repair, and it is **un-armable for lack of data.**
   `gas_hub_basis_daily` exists and is proven in other ISOs, but the daily hub series on disk are
   Algonquin, CAISO citygate, MISO citygate, Transco Z6 and Henry Hub. `ercot_zonal_gas_hub.csv` is
   **annual** basis differentials (55 rows, one per zone-year). There is **no Waha or HSC daily
   file anywhere in `data/raw`**. This is the handoff's own stated blocker — *"a DAILY delivered
   series needs licensed Waha/HSC data = procurement, not a session task"* — reached independently
   from the residual side and now **quantified**: it is worth 95.7% of ERCOT's last rubric failure.
3. **Offer-band scale** — refuted at **ercot-262** (±0.004 on C3b). Arithmetically hopeless here
   regardless: no level shift moves one month by −$345 without wrecking the other eleven, which the
   parent RESULT's month table shows are already biased **+12% to +23% high**.

Non-fuel candidates were checked and do not carry it: **no slack, no dump** in any Uri hour (the
model is not capacity-short), and model demand tracks the measured load through the onset
(Feb 14 peak 68.02 GW, into the shed on Feb 15). The model is **mis-priced, not mis-committed**.

## 4. Verdict

**C3b 2021 is not closable in this session, and the blocker is one named measured input.** Spending
the five-year shard fan-out would have re-measured a fuel-resolution defect that ercot-254 already
measured and ercot-261 already adjudicated. Phase 0 cost minutes; the fan-out would have cost hours
and changed nothing.

**What would close it:** a daily (or hourly) delivered gas series for the ERCOT burner tip across
Feb 2021 — Waha and/or HSC daily spot — arming the existing `gas_hub_basis_daily` path. That is a
**procurement decision for the owner**, not a modelling choice, and it is the single highest-value
open item on ERCOT's calibration: it is worth 0.559 → ~0.116 on the ISO's only remaining rubric
failure, and it needs no new mechanism, no new parameter and no fitted value.

**Nothing in this addendum changes a determination.** ERCOT's train tier is untouched and the ISO
stays CALIBRATED (rule 30(c)). No `ScenarioConfig` field moved; no bundle was produced; nothing was
deleted (rule 31 `[R-RETAIN]`).
