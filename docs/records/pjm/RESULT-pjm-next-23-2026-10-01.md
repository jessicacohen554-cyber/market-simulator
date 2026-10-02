# RESULT — PJM-NEXT-23: the CT_PEAKER 2023 step is the gas price level, not a CT input; real CTs dispatch far flatter in cost than the LP (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO all read **NOT-YET**. Same 10 failing cells.

**Solves:** none. No PRECOMMIT (card 4 not reached).

| probe | artifact | card |
|---|---|---|
| `scripts/probes/_pjmnext23_ct_plants.py` | `results/phase0/pjm/_pjmnext23_ct_plants.json` | 1, 2 |
| `scripts/probes/_pjmnext23_ct_inmoney.py` | `results/phase0/pjm/_pjmnext23_ct_inmoney.json` | 1, 2 |

Inputs: the keeper's `unit_marginal_<y>` and `system_<y>`, the C1 bench (EIA-923 net, CAMPD-shaped), PJM actual system RT and DA (`actual_lmp_hourly_PJM`), EIA-860 generators, EIA-923 generation-fuel, CAMPD unit-level. The offer is each plant's first econ tranche (`econc00`, P1 `mc`, hourly). A run-hour is output > 5 % of the plant's mean LP capacity.

## 1. Card 1 — the CT_PEAKER 2022 → 2023 step

| CT_PEAKER | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| model / bench (TWh) | 9.2/15.3 | 12.9/18.6 | 11.2/20.1 | 11.7/18.2 | 18.7/21.0 | 24.5/23.6 | 28.1/24.3 |
| committed-band output (TWh) | 4.0 | 4.7 | 4.4 | 4.4 | 6.5 | 8.2 | 8.6 |
| committed-band capacity (GW) | 2.97 | 2.96 | 2.98 | 2.98 | 3.07 | 3.15 | 3.00 |
| cap-weighted median offer ($/MWh) | 42 | 35 | 56 | 90 | 43 | 39 | 52 |
| hours, model zonal price ≥ offer | 316 | 625 | 468 | 521 | 935 | 1215 | 1424 |
| hours, actual RT ≥ offer | 599 | 694 | 901 | 1477 | 1354 | 1823 | 1954 |
| run-hours, model / real | 1181/1120 | 1340/1384 | 1234/1515 | 1318/1391 | 1680/1555 | 2110/1627 | 2357/1825 |

**Which input steps.** None of the CT inputs checked:
- **Fleet:** 108 continuing plants carry +6.3 TWh of the model's 2022 → 2023 rise (bench +2.4). Entries add 0.67 TWh (204 MW); exits 0 (79 MW).
- **Committed capacity** is flat (~3.0 GW). The keeper's CT_PEAKER committed band is already 1.05 (`offer_curve_overrides`), i.e. the measured `phys_committed` 1.049.
- **Heat rates:** `measured_ct_heat_rates` per-year rows, 2022 → 2023, over 60 plants: median +0.01, capacity-weighted mean 0.00 MMBtu/MWh (range −1.47 to +0.87).

**What moves is the gas price level.** In West-APS and ComEd, CT offers fall from $65–80 (2022) to $27–35 (2023–24). That is the system price level for 5,000–7,000 hours.
- Armstrong (West-APS, 570 MW): model 5,800–7,200 run-hours vs real ~2,500 (2.7–3.4 vs 1.1 TWh).
- University Park North (ComEd, 459 MW): model 5,100–6,300 vs real 700–1,300 (1.6–2.0 vs 0.1–0.3 TWh).

Real CTs also rose, by less: bench +2.4 TWh vs model +6.3 on the same plants.

**Verdict, card 1.** The step is the model's response to cheap gas, not a CT input defect. It is the CT form of NEXT-22's coal finding: the LP's response to margin is steeper than the real fleet's. **OPEN, not a limit.**

## 2. Card 2 — the persistent per-plant under-run

| plant (zone) | model TWh/yr | bench TWh/yr | real run-h | model run-h | median offer | median actual DA when running |
|---|---|---|---|---|---|---|
| Doswell GT7–9 (Dominion) | 0.0 | 0.9–1.0 | 2,900–3,650 | 0–150 | $50–99 | $22–80 |
| Tait (AEP) | 0.0–0.1 | 0.2–1.3 | 2,300–4,600 | 600–1,050 | $50–91 | $24–82 |
| West Lorain (ATSI) | 0.1–0.3 | 0.0–1.7 | 120–5,800 | 750–1,650 | $31–87 | $23–96 |
| Louisa (Dominion) | 0.0–0.2 | 0.2–0.6 | 1,080–2,480 | 600–1,400 | $32–143 | $27–98 |

(2019–2025 ranges; per-year rows are in the JSON.)

**Reading.**
- Real CT energy produced in hours where actual DA **or** RT clears the plant's modeled offer is **0.44 / 0.43 / 0.49 / 0.68 / 0.56 / 0.64 / 0.71** of the bench (2019–2025). Real CTs produce half or more of their energy below their modeled offer in 2019–2021.
- The under-run plants run when actual DA sits at about **half** their modeled offer. The over-run plants (Armstrong, University Park North, Rockford) are the cheapest-gas CTs; the under-run plants are the dearest.
- **Real CT dispatch is much flatter across plant cost than the LP's merit order.** The same object as card 1, seen across plants instead of across years.
- **Inputs checked, not the object:**
  - Prime movers: all GT per EIA-860; Doswell's CT_PEAKER slice is GT7–9 only, and its CC sits in CC_REGULAR.
  - **One data defect, too small to matter:** Tait is split across two CAMPD facility IDs (2847 = GT1–3; 55248 = CT4–7). EIA-923 reports all seven GTs under 2847. The C1 total is right (EIA-923), but the measured HR 13.12 covers only GT1–3; EIA-923 plant net HR is 12.5–12.7 (2021–2024). About $1–2/MWh on the offer, against a ~$20 gap.
  - Delivered gas: `pjm_replacement_cost_fuel` is already adjudicated **R**. Not re-tested.

**Verdict, card 2.** No per-plant input defect large enough. **OPEN, not a limit.**

## 3. Card 3 — coal response slope

Not re-tested. Cards 1–2 add one constraint on any mechanism: the CT object has the same sign structure as coal (cheap units over-run, dear units under-run, every year), so a candidate should be judged on both classes at once.

## 4. Card 4

Not reached. No admissible, year-discriminating, zero-DOF mechanism.

## 5. Next (NEXT-24)

1. **One object across coal and CT: the LP dispatches steeper in cost than the real fleet.** Before any lever, measure the real fleet's loading-vs-margin curve for CT_PEAKER and COAL_* on the same axis (actual DA and RT, plant offer), and the keeper's. A candidate must be measured, apply in every year, and flatten both. Check the §5.3 queue first.
2. **What real CTs below their offer are doing.** Candidate explanations to measure (not levers): DA commitment against the DA price vs RT; PJM reliability / reactive commitments (Balancing Operating Reserve credits by zone, IMM State of the Market); CT run-length minimums (`campd_ct_run_lengths_PJM.csv` exists).
3. **Tait CAMPD facility split:** check how many PJM plants have a CAMPD facility ID different from their EIA-923 plant ID. That affects the bench's hourly shape and the measured heat-rate coverage, not the C1 totals.

**Retrievability:** no bundles. Probe JSONs are committed under `results/phase0/pjm/`.
