# ADDENDUM — pjm-171: the EMAAC CC over-run is real, and the defect is in how detected outages reach the LP — not in CEMS coverage

**Session** pjm-171 · **ISO** PJM · **Date** 2026-09-07 · **ZERO LP SOLVED**
**Parent** `FINDING-pjm171-2021-c3a-is-the-flat-stack-without-its-offset-2026-09-07.md`
**Keeper UNCHANGED** `2026-08-15-pjm-162-inputclock`. Nothing promoted, nothing registered.
**Trigger:** owner observation — *"it seems like we have too much available capacity for cc regular
… Bergen generating station is +4 twh … they indicate CEMS is missing data but there's no reason
our model should be 2x the 923 data."*

---

## 1. RESULT

> **The owner's read is confirmed, and the CEMS objection is answered: CEMS coverage is NOT the
> explanation.** Every plant named below is present in the raw CAMPD extract with a full 8,760-hour
> record per unit. The model nonetheless dispatches these plants straight through multi-week
> windows in which CEMS reads zero across the whole plant: **26.85 TWh of PJM 2021 gas-fleet energy
> is produced in hours the plant's own CEMS record reads zero**, 9.79 TWh of it in EMAAC.
>
> **The discriminating statistic is the longest continuous off-run**, not the annual total. For
> Bergen the plant's CEMS record is zero for **838 consecutive hours (35 days)** while the model's
> longest continuous off-run all year is **24 hours**. Red Oak: **800 h** measured against **7 h**
> modelled. Hopewell: **1,155 h** against **0 h** — the model never stops it.
>
> **And the outage events ARE detected.** `data/clean/unit-outage-events/PJM` carries 1,379 PJM
> rows for 2021, including a 282-day event at Chalk Point and a 132-day event at Montour. So the
> defect is **not** detection and **not** CEMS coverage — it is how a detected per-unit event
> reaches the plant-level LP row's availability. That is a different card from the one the standing
> `envelopeCaveat` describes, and it is the sharpest lead in this addendum.

---

## 2. THE CENSUS (committed artifacts only)

Model dispatch is the run payload's `plants[<code>]['m']`; CEMS is the bench payload's
`plants[<code>]['campd']`; both are uint8 percent-of-nameplate, scaled `npl/100`. "Phantom" is
model energy produced in hours the plant's CEMS series reads zero — an **upper bound** on the
availability defect, since a CEMS zero can also mean "available but out of merit" (§4).

| plant | zone | npl MW | model CF | CEMS CF | model TWh | CEMS TWh | **phantom TWh** | CEMS longest off (h) | model longest off (h) |
|---|---|---|---|---|---|---|---|---|---|
| Red Oak Power | EMAAC | 821 | 70.2 % | 21.9 % | 5.05 | 1.57 | **2.48** | **800** | **7** |
| **Bergen Generating Station** | EMAAC | 1401 | **45.6 %** | **9.0 %** | 5.60 | 1.10 | **1.99** | **838** | **24** |
| Wildcat Point | SWMAAC | 1114 | 56.4 % | 35.5 % | 5.51 | 3.46 | 1.55 | 460 | 489 ✅ |
| Chalk Point Power | SWMAAC | 1318 | 14.3 % | 0.6 % | 1.65 | 0.07 | 1.47 | 3,852 | 68 |
| TalenEnergy Montour | Central PA | 1758 | 15.1 % | 8.4 % | 2.32 | 1.30 | 1.39 | 2,850 | 68 |
| Hay Road | EMAAC | 1098 | 29.9 % | 11.6 % | 2.88 | 1.11 | 1.30 | 443 | 168 |
| St Joseph Energy Center | AEP Ohio | 780 | 80.1 % | 64.8 % | 5.48 | 4.43 | 0.88 | 299 | 312 ✅ |
| Hopewell Cogeneration | Dominion | 399 | 47.4 % | 20.6 % | 1.66 | 0.72 | 0.88 | 1,155 | **0** |
| Eddystone Generating Station | EMAAC | 862 | 11.8 % | 0.2 % | 0.89 | 0.02 | 0.86 | 4,498 | 68 |
| Tenaska Virginia | Dominion | 1011 | 54.2 % | 41.6 % | 4.80 | 3.68 | 0.79 | 1,589 | 1,608 ✅ |
| Hunterstown Power Plant | Central PA | 898 | 76.0 % | 46.4 % | 5.98 | 3.65 | 0.73 | 898 | 7 |
| Fremont Energy Center | ATSI | 740 | 77.4 % | 57.2 % | 5.02 | 3.71 | 0.56 | 463 | 480 ✅ |
| Woodbridge Energy Center | EMAAC | 773 | 69.8 % | 54.3 % | 4.73 | 3.67 | 0.54 | 315 | 336 ✅ |

Phantom by zone (TWh): **EMAAC 9.79** · Central PA 4.69 · SWMAAC 3.87 · Dominion 3.25 ·
AEP Ohio 1.63 · ComEd 1.38 · West APS 1.13 · ATSI 1.11. **Fleet total 26.85 TWh.**

**The ✅ rows are the control.** Wildcat Point (460 vs 489), Tenaska Virginia (1,589 vs 1,608),
Fremont (463 vs 480), Woodbridge (315 vs 336) and St Joseph (299 vs 312) show the outage machinery
reproducing a measured window to within a few percent. So the mechanism works — it just does not
reach the rows above it. That contrast is what makes this a defect rather than a modelling choice.

---

## 3. CEMS COVERAGE IS RULED OUT, AND THE DETECTOR IS MOSTLY NOT THE PROBLEM

Raw CAMPD (`data/raw/campd-unit-level/<ST>_2021.parquet`, `facilityId` is a **string**) and the
derived event table, per plant:

| plant | EIA code | CAMPD rows 2021 | units | detected 2021 events | longest detected | CEMS longest off (h) |
|---|---|---|---|---|---|---|
| Red Oak | 55239 | 26,280 | 3 | 5 | 37.2 d | 800 |
| Bergen | 2398 | 52,560 | 6 | 3 | 18.2 d | 838 |
| Chalk Point | 1571 | 78,768 | 10 | 6 | **282.0 d** | 3,852 |
| Montour | 3149 | 17,520 | 2 | 13 | **132.3 d** | 2,850 |
| Hay Road | 7153 | 52,560 | 6 | 30 | 115.1 d | 443 |
| Hopewell | 10633 | 26,280 | — | 3 | 42.7 d | 1,155 |
| Eddystone | 3161 | 17,520 | — | **1** | 11.7 d | 4,498 |
| **Hunterstown** | 55976 | 26,280 | — | **0** | — | 898 |

**No plant is absent from CAMPD.** Bergen's bench record additionally carries `nodata = False`, so
the model does not treat it as CEMS-missing. CEMS *does* under-report Bergen — 1.104 TWh against
EIA-923's 1.740 — but **the model sits above both**, at 5.586 TWh, i.e. **3.21× the 923 figure**.
The owner's point stands exactly as put: no CEMS-coverage argument reaches a 3.2× over-run.

**Chalk Point is the clean contradiction.** A 282-day outage event is detected, and the model's
longest continuous off-run is 68 hours. Detection is not the failure; **application** is. The
event table is per-**unit** with `unit_pct_of_plant`, while the LP row is a per-**plant** CAMPD bin
(`use_campd_bins`), so a plant whose units are out at different times can carry a large derate
without the plant ever going offline. **Hunterstown (0 events against 37 measured days off) and
Eddystone (1 event of 11.7 d against 187 measured days) are the two genuine detection gaps.**

---

## 4. WHAT IS **NOT** CLAIMED — the honest split

**A CEMS zero is not proof of unavailability.** For a peaker or an old steam unit a long zero is
ordinary economics, and a model that runs it has a merit-order problem, not an availability one.
The table above mixes the two and must be split before any repair is designed:

- **Availability is the live hypothesis** for the modern CCs — **Bergen** (45.6 % model CF vs
  9.0 % measured), **Red Oak** (70.2 % vs 21.9 %), Hay Road, Woodbridge, West Deptford. A 33–35
  day continuous plant-wide zero at a merchant CC is a layup or a major outage, not economics.
- **Merit order is the likelier owner** for **Eddystone** (a 1960s oil/gas steam plant, 187 days
  off) and the **Chalk Point ST_GAS** bin (0.6 % measured CF, model 15.3× the EIA-923 figure).
  These belong with the parent finding's offer-stack object, not here.

**Phantom energy is an upper bound, not the defect's size.** Some of it is legitimate re-timing.
The 26.85 TWh figure should never be quoted as "the availability error".

**The link to the standing `envelopeCaveat` is a hypothesis, not a measurement.** This addendum did
not reconstruct the model's availability array — the fleet rebuild is blocked at HEAD because
`pjm_da_virtual_bids` requires `data/raw/pjm-da-virtuals/hrl_da_incs_decs_2021_*`, whose payload is
a **converted corpus** (gitignored; recovery is re-fetch, per its README). Phase B needs that
fetch, or a reconstruction with the virtual layer disabled and the deviation declared.

---

## 5. SUCCESSOR — a named, zero-LP first step

**Card: "does a detected per-unit outage event reach the plant's LP availability?"** The test is
exact and needs no solve beyond a fleet rebuild:

1. Re-fetch `pjm-da-virtuals` for 2021 (or rebuild with `pjm_da_virtual_bids` off, declaring the
   deviation — it cannot affect thermal availability).
2. Reconstruct the 2021 fleet (`run_year(fleet_only=True)`) and take `pmax × availability` summed
   over each plant's LP rows.
3. For Chalk Point, compare that series against its **detected** 282-day event and against CEMS.
   One of three things is true, and each is a different repair: the event never reaches the fleet;
   it reaches it as a partial derate that leaves the plant dispatchable; or it reaches it and the
   binning re-spreads it across tranches.

Bergen and Red Oak are the sharpest CC test cases; Chalk Point is the sharpest *mechanism* test
case because its event is detected and long.

**This is not a route to 2021 inside ±10 % either.** Cutting phantom CC energy reduces CC volume
(toward the C1 miss of +26.77 TWh) but removes cheap-ish mid-merit supply, which raises price —
the same direction as the seam repair, and away from 2021's +10.8 %. Both repairs are correctness
work under rule 14 `[R-ACCURATE]`; neither is a route to the band, and rule 30(c) holds PJM's
headline at **CALIBRATED** throughout.

---

## 6. A CORRECTION MADE IN-SESSION

An earlier pass of this census used plant codes recalled from memory rather than read from the
data, and on those codes reported "Eddystone is NOT in CAMPD" and "Hunterstown has zero events in
all years". **Both were artifacts of wrong identifiers** — Eddystone is **3161** (not 3169) and
Hunterstown is **55976** (not 55196). Corrected above from the bench payload's own keys: Eddystone
has 17,520 CAMPD rows and one detected event; Hunterstown has 26,280 rows and zero detected events
(that one survives, on the correct code). Every plant code in this document is now read from the
committed artifacts, never typed from recall.
