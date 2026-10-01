# FINDING — R-CAISO-25: same-day gas for the winter events. Zero LP. No admissible series. Nothing built.

Keeper `2026-09-30-caiso-r20-overnight` (bundle `rcaiso20_A_span`, 2022–25), unchanged. No shard, no cell moved.
Probe: `scripts/probes/_rcaiso25_prc_fuel.py` (CAISO OASIS `PRC_FUEL` vs the keeper's delivered gas).

## 0. The question

R-CAISO-22 §3: on the Jan 15–16 2024 event evenings, measured RT ($207–286) implies HR **15.5** on the
next-day CA composite print the model uses ($17.34, the MLK weekend package). The model implies **10.3**.
Is there a measured same-day/intraday CA citygate series that would raise the fuel cost on those days?

**What a same-day series would have to show.** At the model's event marginal cost (λ $177–180 on
$17.80 delivered = $17.34 + 0.46 transport), measured $207–286 needs delivered gas of **$20.7–28.6**,
i.e. a same-day premium of **+16 % to +61 %** over the next-day print.

## 1. What exists

| Source | Product | Public? | Same-day? | Verdict |
|---|---|---|---|---|
| NGI Daily GPI, CA Composite (in repo, `caiso_citygate_daily.csv`) | next-day, weekend packages | displayed by EIA; licence flagged | **No** | What the model already uses (flow-dated, `caiso_citygate_flow_date` on) |
| ICE next-day gas (EIA wholesale archive) | next-day, PG&E/SoCal citygate | yes | **No** | Same product class as NGI. Adds nothing for same-day |
| **CAISO OASIS `PRC_FUEL`** | CAISO's own per-fuel-region gas price for cost-based bids (hub + transport) | **yes** | **No** — flat within each day; MLK Jan 13–15 carry one print (§2) | Next-day index. New in the repo's record, but answers a different question (§3) |
| ICE same-day trades (8–9 am) | same-day | **licensed** | yes | CAISO uses it only to auto-approve RT bid-cap raises (RLCR, +10–25 % thresholds). No public series |
| Platts Gas Daily / NGI intraday | same-day / intraday | **licensed**, not redistributable (`docs/data-licensing.md` §5) | partly | Vendor purchase. Owner ruled "Don't buy" on the analogous SOCO ask (soco-90 §6) |
| Per-resource RLCR data | resource-specific | **no** (confidential) | yes | Not obtainable |

**No public, measured same-day/intraday CA citygate series exists for 2022–25.**

## 2. The measured record says the event was not a gas event

CAISO DMM, *Winter Market Performance Report, January 2024*:
- "Gas conditions and prices in the West were generally **moderate**, with modest price increases across
  hubs in California." PG&E Citygate peaked at **$17**, SoCal Citygate at **$13.52** (next-day, Jan 13 trade).
- The ICE trade spread was widest for the Jan 13 weekend trade, but "the settled index price remained
  close to the median of trades." No same-day premium is reported.
- The electricity drivers named are **Pacific NW shortage**, a **forced NOB outage** for the whole
  weekend, Oregon transmission outages, and **Malin congestion** (~$125 M DA congestion rent).

CAISO's own `PRC_FUEL`, flow date Jan 14 2024 ($/MMBtu, vs model $17.80 delivered everywhere):

| Region family | PRC_FUEL |
|---|--:|
| PG&E (FRPGE1–B) | 18.28–19.40 |
| SCE (FRSCE*) | 13.44–16.79 |
| SDG&E (FRSDG*) | 13.75–16.51 |

CAISO's own gas reference for the SP15 fleet was **below** the model's. At CAISO's *highest* in-state
region ($19.40), measured $207–286 still implies HR 10.7–14.7. The 15.5 is the signature of **import
parity with a short NW** (R-CAISO-22 §2–3: Malin $230–255), not of a fuel price the model is missing.

## 3. Does 2022–25 differ from the ICE failure (R-CAISO-12)?

**Coverage, yes; product, no.** R-CAISO-12 rejected the ICE daily *power* index as a 2019–20 hub
substitute: ~180 on-peak days a year, no hours, a year-drifting bias needing a fitted basis. For gas in
2022–25 that problem does not arise — the repo already holds a dense, flow-dated daily citygate series,
and CAISO's own `PRC_FUEL` tracks it at r = 0.996 (PG&E) / 0.989 (SCE), Dec 2022–Jan 2023. But every
public series in 2022–25 is still a **next-day** product. The obstacle is the product, not the period.

## 4. A side observation (not this link's lever)

`PRC_FUEL` sits above the model's delivered gas in the 2022–23 winter crisis (median +$2.4 PG&E,
+$2.9 SCE, Dec 2022–Jan 2023, n = 60 days) and below it in SoCal during MLK 2024. 2024 full-year
comparison: §4.1. This is CAISO's measured fuel-region transport/delivery cost, the open owner
methodology ask on `CAISO_CITYGATE_TRANSPORT_ADDER` (CAISO shard, `measured_offer_surface` evidence:
"the transport adder's admissibility … is filed as an owner methodology ask, not moved"). It is evidence
for that ask, not a C3c lever, and it is not tested here.

### 4.1 2024 full year

PLACEHOLDER_2024

## 5. Decision

- Nothing built, no PRECOMMIT, no shard, no solve. The keeper is unchanged; no matrix cell moves.
- Link 7 closes: no public same-day series exists, and the measured record (DMM, `PRC_FUEL`) places the
  2024 event at NW import parity, which is link 8's object.
- C3c 2024 stays a lone ledgered, non-downgrading caveat (rule 22 `[R-C3C]`).
- The next step goes to the owner as a decision card (§6).

## 6. Owner ruling

PLACEHOLDER_RULING

## Sources

- CAISO DMM, Winter Market Performance Report Jan 2024: https://www.caiso.com/documents/wintermarketperformancereportforjan2024.pdf
- CAISO BPM Market Instruments, Attachment O (RLCR; same-day ICE 8–9 am, +10–25 % thresholds): https://www.caiso.com/documents/draftmarketinstrumentsbpmattachmento-referencelevelchangerequests-commitmentcosts-defaultenergybidenhancements.pdf
- CAISO OASIS `PRC_FUEL`: `https://oasis.caiso.com/oasisapi/SingleZip?queryname=PRC_FUEL&fuel_region_id=<REG>&startdatetime=<YYYYMMDD>T08:00-0000&enddatetime=<YYYYMMDD>T08:00-0000&version=1&resultformat=6`

## Retrievability (rule 34(e))

Nothing was solved. The probe refetches `PRC_FUEL` from OASIS; no data file is committed.
