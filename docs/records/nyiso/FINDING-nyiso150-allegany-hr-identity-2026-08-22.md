# FINDING nyiso-150 — Allegany's "most efficient in the cohort" heat rate is a class default reached through an ORISPL registry split; the plant's own measured rate is 8.4–8.7, proven across seven eGRID vintages

Session nyiso-150, 2026-08-22. No solve; every number below is read from
committed raw data (`data/raw/fleet-egrid/*.xlsx`,
`data/raw/_processed-legacy/eia923_monthly_generation.parquet`,
`data/clean/fleet/fleet_2023.parquet`) and the code at HEAD. This is the
identification the ARM C′ rejection called for (the named successor's
phase 0), and it CHANGES the successor's shape.

## 1. The defect chain, each link verified at HEAD

1. **The model carries hr 7.5 for Allegany (7784)** — not a measurement:
   `HEAT_RATE_BINS["gas_cc"]["older"] = 7.5` (`config/constants.py`), the EIA
   Table 8 legacy-CC class default, assigned by
   `data/fleet/eia860.py` (`heat_rate = data.get("heat_rate") or
   HEAT_RATE_BINS[...]`) because the fleet source row carries no unit heat
   rate. For NYISO, per-plant measured heat rates exist ONLY via CAMPD
   (`use_campd_bins` measures CEMS heatInput/grossLoad); Allegany is absent
   from CAMPD in every year (verified NY_2023/2024/2025 extracts).
2. **The plant's own measured rate exists — under a different ORISPL.** eGRID
   carries the plant as **10619 "Allegany Station No. 133"** while
   EIA-860/923 carry it as **7784 "Allegany Cogen"**. Identity is proven
   seven-for-seven: eGRID `PLNGENAN` equals the EIA-923 plant-7784 annual
   net generation EXACTLY in every vintage on disk (2018: 36,224; 2019:
   17,817; 2020: 18,211; 2021: 14,990; 2022: 43,964; 2023: 11,734; 2024:
   15,549 MWh).
3. **The measured rate is stable and decisively above the default.**
   `PLHTIAN`/`PLNGENAN` (eGRID publishes no `PLHTRT` for this plant; the
   ratio is arithmetic on eGRID's own fields, the same posture as the
   accepted 55641 boundary repair): 8.68 / 7.99 / 8.65 / 8.68 / 8.15 /
   8.58 / 8.44 across 2018–2024 — pooled ΣHI/ΣNG = **8.42** (all vintages)
   or **8.50** (2023–2024). The plant NEVER approaches 7.5 in any year.
4. **The 7.5 is what makes it "the cohort's most efficient".** Sterling's
   8.56 (CAMPD-measured) sits above the default; the merit cliff the
   nyiso-146 prereg measured ($3/MWh between ~1 %-CF and 92 %-CF dispatch)
   puts the 7.5-rated Allegany on the wrong side. Its ARM C′ residual (70/60 %
   falls vs the ≥80 % bar; 148–203 GWh armed vs an 11.7–15.5 GWh meter) is
   the class default dispatching, not the plant.
5. Corollaries checked and closed: EIA-923's CHP flag is `N` in every year
   2018–2024 (the "Cogen" name is historical; the CHP framework does NOT
   apply); it files no Schedule-5 fuel costs (0 rows); EIA-860 lists it as a
   1994 67 MW CC (42 CT + 25 CA).

## 2. The general channel is REFUTED by its own population — the admissible form is identity reconciliation

A "measured eGRID heat rate for every CAMPD-less plant" channel was sized and
is NOT proposed: NY's CAMPD-less fossil set is 99 plants, 57 with a computable
ratio, dominated by behind-the-meter hospital/campus cogens and micro-peakers
whose realized rates at near-zero output are not loaded heat rates (Charles P
Keller 118.2 MMBtu/MWh on 24 MWh/yr; oil micro-plants at 18–22; campus CHPs
at 5.7–5.8 flattered by steam credit). Screening that population down to the
sound cases would take constructed thresholds — a rule-21 hazard — for a
population that is mostly not in the LP fleet at all. What distinguishes
Allegany is not a threshold but an IDENTITY: a proven two-registry split
(the `campd.CAMPD_UNIT_PLANT_REMAP` / Astoria 55375↔57664 family) behind
which a stable multi-vintage measurement of a real LP unit already exists.

## 3. The successor, re-specified (not executed here)

**One measured-input repair + one re-gate, in that order:**

1. **The Allegany heat-rate identity repair** — a derived, committed artifact
   (the eGRID 10619 ↔ EIA 7784 reconciliation with the §1.2 identity proof
   and the pooled ΣHI/ΣNG rate declared a priori), consumed at the existing
   `data.get("heat_rate")` preference seam under a default-off gate;
   NYISO-scoped (rule 25), zero free parameters (the value is arithmetic on
   eGRID's published fields; the pooling rule is declared before any solve).
   Its own prereg; kill gates in the C-K family (exactness; liveness = the
   plant's mc moves by the predicted ≈ +$2–3/MWh; no other plant moves;
   criteria hold).
2. **Re-gate `cc_reserve_duty_split` on the repaired control.** The armed
   peak offer scales with the base rate (≈ +$10 at the 2.25× band), which is
   the direction the C-K2 bar needs; whether it clears is the A/B's question.

The multi-vintage series gives the repair a real LOYO story (any
leave-one-vintage-out pooled rate lands in 8.36–8.50).

## 4. What this changes on the queue

The "reserve-cohort graded duty" successor named by today's ARM C′ rejection
is DEMOTED from a new mechanism build to (1) + (2) above: the graded-duty
construction would have been aimed at conduct the class default manufactures.
If (1) + (2) still leave Allegany over the bar, the graded duty returns as
the successor — with the EIA-923-monthly instrument (its only meter) and its
admissibility case examined then, not now.

## 5. Governance

No solve, no parameter moved, nothing armed; the keeper and every dashboard
artifact are untouched by this finding. Rule 22: only committed raw inputs
read. Rule 28: recorded on the `offer_curve_by_group` NYISO cell alongside
the ARM C′ rejection it re-specifies.
