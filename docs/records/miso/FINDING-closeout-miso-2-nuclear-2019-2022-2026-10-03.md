# FINDING — closeout-miso-2: the MISO 2019–2022 nuclear gap. It is a missing measured anchor plus a bench-scope artefact, not the NRC overlay; the repair moves no failing row toward its gate

```
LANE    : closeout-miso-2 (owner ruling R-38, 2026-10-03: a zero-LP MISO lane that sizes the 2020 overlay gap as new evidence)
KEEPER  : 2026-10-02-w0-miso-fix2 (results/calibration/w0_miso_span, 2019–2025, every leg at 25da6022), unchanged
LP      : none. No PRECOMMIT and no shards: the sized effect is under the lane's bar (§4)
PROBES  : scripts/probes/_closeout_miso2_nuc_plant.py   → closeout-miso-2/nuc_plant_month.csv
          scripts/probes/_closeout_miso2_union_delta.py → closeout-miso-2/union_delta_{class,plant}.csv
          scripts/probes/_closeout_miso2_greedy_nuc.py  → closeout-miso-2/greedy_nuc.csv
CELLS   : no verdict moves. Evidence appended to nuclear_unit_availability (K) and benchmark_membership_vintage_union (O)
```

## 0. Readings fixed before any number

- **R-1.** A plant-month gap is **(a)** if a measured status date in a registry is wrong or missing (rule 14), **(b)** if
  it is an outage the overlay cannot see, and **(c)** if the model is right and the benchmark is the artefact.
- **R-2.** A registry-date repair can land without a card. Any NRC daily-status intake or extension goes to the desk as
  a card first.
- **R-3.** A repair earns a PRECOMMIT only if the zero-LP greedy moves a **failing** row by ≥ 1 TWh or by ≥ 0.01
  NRMSE. The failing rows on the keeper are C1 ST_GAS 2019 (−8.60 TWh against a ±8.00 band) and C3b 2021 (NRMSE
  0.213 against ≤ 0.20). C3a 2020 (+9.6 %) must stay ≤ +10 %.
- **R-4.** A miso-301 row reopens only if the repair moves that row toward its gate.

## 1. The premise is half right: the MISO overlay covers no 2019–2022 date

The keeper arms `nuclear_unit_availability`, but `data/raw/nuclear-availability-MISO.csv` starts on **2023-06-01**:
13 reactors, 6,760 rows, 2023–2025 only. The deriver reconciles each month to the EIA-923 anchor
(`NUCLEAR_MONTHLY_CF_BY_YEAR`). MISO carries anchor rows for 2023–2025 only, so it could not have built 2019–2022.

As a result, every 2019–2022 leg reads the **forecast fallback**:

> `NUCLEAR_MONTHLY_CF["MISO"]` (the 2023–25 mean) × (1 − EFORD 0.03)

This is the same rule-14 defect closeout-soco-2 §(b′) found for SOCO, and §(d) of that record lists it for MISO
2019–2022. It went unnoticed because the overlay flag reads "armed".

The signature is in the per-plant table below. Model nuclear at a given plant is **identical across years**:
- Clinton 8.01 TWh in all four years;
- Fermi 8.58;
- Grand Gulf 10.53;
- Prairie Island 7.82.

The NRC daily Power Reactor Status files for 2018–2026 **are on disk** (`data/raw/nrc-reactor-status/`).

## 2. Per-plant model versus EIA-923, 2019–2022

Each cell reads model / EIA-923 / gap, in TWh. Model values are P1 `unit_marginal_<Y>.parquet` from the keeper.
EIA-923 values are Page 1 NUC net generation, matched by plant.

| Plant | 2019 | 2020 | 2021 | 2022 |
|---|---|---|---|---|
| Clinton (204) | 8.01 / 8.36 / **−0.36** | 8.01 / 9.46 / **−1.46** | 8.01 / 8.35 / **−0.34** | 7.90 / 9.22 / **−1.33** |
| Duane Arnold (1060) | 4.52 / 5.24 / **−0.71** | 4.14 / 2.90 / **+1.23** | — | — |
| Palisades (1715) | 5.80 / 6.87 / **−1.06** | 5.78 / 6.00 / **−0.22** | 5.98 / 7.01 / **−1.03** | 2.81 / 2.73 / **+0.08** |
| Fermi 2 (1729) | 8.58 / 9.89 / **−1.31** | 8.58 / 6.07 / **+2.51** | 8.58 / 9.37 / **−0.79** | 8.58 / 6.66 / **+1.92** |
| Monticello (1922) | 4.64 / 4.96 / **−0.33** | 4.64 / 5.59 / **−0.95** | 4.64 / 5.02 / **−0.38** | 4.64 / 5.55 / **−0.91** |
| Prairie Island (1925) | 7.82 / 9.14 / **−1.32** | 7.82 / 9.08 / **−1.26** | 7.82 / 9.10 / **−1.28** | 7.82 / 9.15 / **−1.33** |
| Point Beach (4046) | 9.03 / 10.03 / **−1.00** | 9.00 / 9.77 / **−0.77** | 8.97 / 9.97 / **−1.00** | 8.99 / 10.08 / **−1.08** |
| Waterford 3 (4270) | 8.76 / 7.56 / **+1.20** | 8.76 / 8.96 / **−0.20** | 8.76 / 9.81 / **−1.04** | 8.76 / 7.86 / **+0.90** |
| Grand Gulf (6072) | 10.53 / 11.03 / **−0.50** | 10.53 / 6.47 / **+4.06** | 10.53 / 11.77 / **−1.24** | 10.53 / 8.60 / **+1.93** |
| Callaway (6153) | 8.95 / 9.19 / **−0.24** | 9.38 / 7.74 / **+1.63** | 9.38 / 4.29 / **+5.08** | 8.95 / 8.87 / **+0.07** |
| River Bend (6462) | 7.27 / 6.42 / **+0.85** | 7.27 / 7.99 / **−0.71** | 7.27 / 7.44 / **−0.17** | 7.27 / 8.31 / **−1.03** |
| Arkansas Nuclear One (8055) | 13.67 / 13.57 / **+0.09** | 13.67 / 15.06 / **−1.40** | 13.67 / 13.56 / **+0.11** | 13.70 / 14.32 / **−0.62** |
| **Total, plant-matched** | 97.58 / 102.26 / **−4.68** | 97.57 / 95.11 / **+2.46** | 93.61 / 95.69 / **−2.09** | 89.94 / 91.35 / **−1.41** |
| **Bench `classFull`** | 97.03 (**+0.55**) | 92.20 (**+5.37**) | 95.69 (**−2.09**) | 91.35 (**−1.41**) |

**The bench is short by Duane Arnold's EIA-923 exactly:**
- 2019: 102.26 − 5.24 = 97.03;
- 2020: 95.11 − 2.90 = 92.20.

The reason is the bench membership. MISO scores on `_iso_plant_ids` with `benchmark_membership_vintage_union` off
(cell **O**), and the canonical eGRID snapshot no longer knows 1060. The fleet does carry the plant: since R-MISO,
`mid_vintage_exit_carry` (K) injects Duane Arnold, Palisades, E D Edwards, Duck Creek and others in 2019–2022.

### 2020 +5.37 TWh, decomposed (sums to 5.368)

| Piece | TWh | Class |
|---|---|---|
| Duane Arnold's EIA-923 sits outside the bench membership; the model carries the plant | **+2.90** | (c) bench artefact |
| Duane Arnold after the 2020-08-10 derecho. NRC shows 0 % from 2020-08-11; the model runs until EIA-860's retirement month (11/2020): Aug +0.32, Sep +0.39, Oct +0.34, Nov +0.34, partly offset by Jan–May under-run | **+1.23** | (b) |
| The other 11 plants on the flat fallback, which mis-times every refuelling or forced outage: Grand Gulf +4.06 (Mar–May at 0, Aug/Nov derates), Fermi +2.51 (Apr–Jul), Callaway +1.63 (Oct–Dec), against −0.2 to −1.5 at each of the other 8, where the fallback level runs low | **+1.23** | (a) + (b) |

### 2021 (−2.09) and 2022 (−1.41)

**2021.**
- Callaway carries **+5.08 TWh**: it was offline January–July 2021 (EIA-923 reads 0 in every one of those months),
  while the fallback runs it at about 0.9.
- The fallback runs low at the other ten plants, by −0.17 to −1.28 each (−7.17 in total).
- Both pieces are (a) + (b).

**2022.**
- Fermi Jan–Apr: +1.92.
- Grand Gulf Mar–Apr and Jul: +1.93.
- Waterford Apr–Jun: +0.90.
- **Palisades June 2022: +0.49.** NRC shows 0 % from 2022-05-21. EIA-860 retires the plant in 6/2022, and the model
  runs it through June 30.
- Low-level under-runs elsewhere: −0.6 to −1.3 per plant.

### 2019 (+0.55 against the bench)

Against the plant-matched EIA-923 total, the model is actually **−4.68**: the bench hides Duane Arnold's 5.24 TWh.

### Classification

- **(a) Rule 14: a measured anchor that is missing, not a wrong date.**
  - `NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"]` has no 2019–2022 rows.
  - `derive_nuclear_monthly_cf.py --isos MISO --years 2019 … 2022` derives them from EIA-923, which is on disk:

    ```
    2019: [0.91, 0.88, 0.90, 0.75, 0.76, 0.90, 0.93, 0.97, 0.95, 0.85, 0.92, 1.00]
    2020: [1.00, 1.00, 0.78, 0.71, 0.80, 0.88, 0.89, 0.87, 0.93, 0.72, 0.75, 0.87]
    2021: [0.91, 0.89, 0.83, 0.76, 0.81, 0.91, 0.89, 0.97, 0.91, 0.75, 0.93, 0.99]
    2022: [0.94, 0.93, 0.79, 0.57, 0.74, 0.91, 0.90, 0.96, 1.00, 0.93, 0.93, 0.93]
    ```

  - The rows would be an initial derivation for years the table never carried (the ercot-253 / closeout-soco-2
    precedent), not a rule-23 re-derivation.
  - **The EIA-860 exit dates are not defects.** Duane Arnold is RE 11/2020 (vintage_2020 retired sheet) and
    Palisades is RE 6/2022 (vintage_2022/2023). The fleet honours both. No registry-date repair exists to land.
- **(b) Outages the overlay cannot see.**
  - The cases: Grand Gulf 2020/2022, Fermi 2020/2022, Callaway 2020/2021, Waterford 2022, the Duane Arnold derecho,
    and Palisades 2022-05-21.
  - All of them are in the NRC daily status on disk.
  - The overlay cannot see them for two reasons:
    1. The MISO extract was never derived for 2019–2022, because it lacked the anchor.
    2. The MISO reactor map in `derive_nuclear_availability.py` omits 1060 and 1715. Its comment ("carries NO model
       fleet unit") predates R-MISO's `mid_vintage_exit_carry` and is stale for 2019–2022.
  - Extending the extract therefore needs the anchor rows plus two reactor-map rows. That is a data step, so it goes
    on a card (R-2).
- **(c) Benchmark artefact.**
  - Duane Arnold's EIA-923 is outside the bench in 2019 and 2020 (−5.24 / −2.90 TWh against a model that carries the
    plant).
  - The same artefact hits coal: the union census (`union_delta_class.csv`) adds E D Edwards COAL_PRB
    3.21 / 3.10 / 2.71 / 2.70 TWh in 2019–2022 and Duck Creek COAL_BIT 2.24 TWh in 2019. The model carries both
    (856 coal 2.79 / 2.17 / 3.48 / 2.99 TWh; 6016 1.94 TWh in 2019).
  - On the keeper's records the union moves COAL_PRB +5.70 / +3.40 / +5.63 / +5.76 to about
    +2.5 / +0.3 / +2.9 / +3.1, and COAL_BIT 2019 from −2.07 to −4.47. **It flips no row.**
  - It is not scoring-only: `_eia923_frame` also feeds the must-run residual injection. It therefore stays the
    lane-owned O cell that SPP-49 described.

## 3. Consequence at zero LP: greedy same-setter re-clear on the committed hourlies

Method:
- Each nuclear unit's cap is rescaled hour by hour from the fallback (× 0.97) to the derived row.
- Extra nuclear displaces in-merit thermal, highest offer first.
- A shortfall is filled two ways, which bracket the answer:
  - **cheapest fill**, the closeout-soco-2 convention, which over-credits coal held under its cap by floors and fuel
    envelopes;
  - **next-up fill**, which uses the setter and the offers above it.
- The price moves only when the in-merit setter is exhausted.
- C1, C3a and C3b are re-scored with the live `calibration_verdict` scorers on the edited payload.

Scenarios:
- **A** = anchor rows only.
- **B** = A plus Duane Arnold and Palisades dark from their NRC dates.

| Year | Scenario / fill | ΔNuc | ΔCC | ΔCC_CHP | ΔST_GAS | ΔPRB | ΔBIT | C1 ST_GAS | C3a | C3b | New flips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | A / cheapest | +4.02 | −1.73 | −0.58 | −0.56 | −0.60 | −0.31 | −8.60 → **−9.16** FAIL | +7.2 → +5.2 % | 0.102 → 0.086 | — |
| 2019 | A / next-up | +4.02 | −1.58 | −0.53 | −0.50 | −0.82 | −0.37 | −8.60 → **−9.10** FAIL | +7.2 → +5.4 % | 0.102 → 0.086 | — |
| 2020 | A / cheapest | −1.02 | −0.17 | −0.18 | −0.30 | +0.87 | +0.80 | −7.28 → −7.58 | +9.6 → +8.9 % | 0.149 → 0.137 | — |
| 2020 | A / next-up | −1.02 | +0.41 | −0.02 | −0.07 | +0.41 | +0.18 | −7.28 → −7.35 | +9.6 → +9.7 % | 0.149 → 0.142 | — |
| 2020 | B / cheapest | −2.32 | +0.27 | −0.09 | −0.20 | +1.27 | +1.00 | −7.28 → −7.48 | +9.6 → +9.3 % | 0.149 → 0.139 | — |
| 2020 | B / next-up | −2.32 | +0.94 | +0.08 | +0.07 | +0.72 | +0.29 | −7.28 → −7.21 | +9.6 → **+10.2 %** | 0.149 → 0.146 | C3a at its ceiling |
| 2021 | A / cheapest | +2.27 | −2.04 | −0.30 | −0.20 | +0.23 | +0.16 | −5.28 → −5.48 | −7.8 → −9.2 % | **0.213 → 0.221** | CC_REGULAR PASS → **FAIL** (−8.87) |
| 2021 | A / next-up | +2.27 | −1.70 | −0.19 | −0.15 | −0.14 | −0.03 | −5.28 → −5.42 | −7.8 → −8.7 % | **0.213 → 0.221** | CC_REGULAR PASS → **FAIL** (−8.53) |
| 2022 | A / cheapest | +1.84 | −2.69 | −0.76 | −0.70 | +2.02 | +0.59 | −5.68 → −6.38 | −6.8 → −8.9 % | 0.131 → 0.143 | — |
| 2022 | A / next-up | +1.84 | −1.10 | −0.36 | −0.43 | +0.00 | +0.05 | −5.68 → −6.12 | −6.8 → −7.7 % | 0.131 → 0.134 | — |
| 2022 | B / cheapest | +1.18 | −2.53 | −0.73 | −0.66 | +2.35 | +0.67 | −5.68 → −6.34 | −6.8 → −8.8 % | 0.131 → 0.141 | COAL_PRB PASS → FAIL (+8.11) |
| 2022 | B / next-up | +1.18 | −0.64 | −0.29 | −0.36 | +0.00 | +0.05 | −5.68 → −6.04 | −6.8 → −7.3 % | 0.131 → 0.130 | — |

**Which classes absorb the 2020 nuclear change.**
- In 2020 nuclear moves **down**, by 1.0–2.3 TWh, not up. Once the bench artefact is removed, the measured anchor sits
  below the fallback.
- **Coal absorbs it.** Under next-up fill: PRB +0.4 / +0.7, BIT +0.2 / +0.3, CC +0.4 / +0.9 TWh.
- The +5.4 TWh "excess" that the headline suggests is not displacing anything in the model. 2.9 TWh of it is EIA-923
  the bench does not count.

## 4. Verdict against the pre-fixed readings

- **C1 ST_GAS 2019 (failing).** The row moves **away** from its band by 0.50–0.56 TWh. That is under the 1 TWh bar (R-3)
  and in the wrong direction. The measured nuclear is 4.0 TWh higher, and it displaces part of the gas steam that is
  already short.
- **C3b 2021 (failing).** NRMSE rises from 0.213 to 0.221 in both brackets. That is under the 0.01 bar (R-3) and in the
  wrong direction.
- **C3a 2020 (passing).** It ranges from +8.9 to +10.2 %. Scenario B with next-up fill breaches the +10 % ceiling.
- **A new failure.** C1 CC_REGULAR 2021 goes PASS → FAIL (−8.5 to −8.9 TWh against ±8.00) in both brackets. Correct
  2021 nuclear exposes a larger CC under-run.
- **R-4: no miso-301 row reopens as a closing route.** The repair moves all three rows the wrong way or not at all.
  It is **new evidence on their baselines**:
  - the ST_GAS 2019 residual is about −9.1 TWh, not −8.6, once nuclear is right;
  - C3b 2021 is 0.221, not 0.213;
  - the C3b SSE cut needed to clear grows from about 12 % (0.213 on the W0 keeper; the miso-301 ledger's "1 %" was
    written against 0.201) to about 18 %.

**Outcome (task step 3):** no failing row moves by ≥ 1 TWh or ≥ 0.01 NRMSE. So there is no PRECOMMIT and no shards.
The lane stops.

**One thing for the desk. Rule 14 cuts against the fit bar.** The anchor rows are measured data that is on disk, and a
worse fit after swapping in real data "is a discovered bug elsewhere", never a reason to keep the estimate. This lane
does **not** land the constants rows. Landing them re-keys MISO backcast (`solve_surface` `NUCLEAR_MONTHLY_CF_BY_YEAR`
MISO) and would leave HEAD LIVE against the keeper with no solve: a G-DRIFT hunk. Whether to carry the repair
(anchor rows + the 2019–2022 extract + Duane Arnold / Palisades in the reactor map, then 7 MISO shards) **knowing it is
fit-negative** is a desk or owner call, not a lever.

## 5. Notes

- **2025 EIA-923 data drift.** `derive_nuclear_monthly_cf.py --isos MISO --years 2025 --check` now reads Oct/Nov
  0.86 / 0.87 against the committed 0.85 / 0.86. The preliminary 2025 vintage moved. This is not re-derived here
  (rule 23: it re-derives when the final 2025 EIA-923 posts, citing that data change).
- **Bench-scope cross-ISO note.** Any ISO whose fleet carries `mid_vintage_exit_carry` plants while
  `benchmark_membership_vintage_union` is off carries the same artefact. For MISO the union adds 12.5 / 6.76 / 3.24 / 3.03 TWh of EIA-923 in
  2019–2022 (0 from 2023). It is each lane's to measure (rule 25).
- **Probe convention.** The greedy is the closeout-soco-2 construction. The next-up variant is added here because
  MISO's coal floor bridges and fuel envelopes hold cheap coal below its cap, and cheapest fill would hand that coal
  the shortfall.
