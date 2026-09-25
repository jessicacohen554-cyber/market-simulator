# FINDING nwppnext2: the uncoupled mainstem is the wrong target for C4. Zero LP.

**Lane:** NWPP-NEXT2 phase 0 · **Date:** 2026-09-25 · **Zero LP.** Nothing solved, registered or
committed, and no `src/` change. No matrix cell moves, because no mechanism was tested (rule 28(b)).
**Control:** keeper `2026-09-25-nwpp-next-ferc714-partial` (`results/calibration/nwppnext_span`).
**Probe:** `scripts/probes/_nwppnext2_mainstem_census.py --legs <dir>` reproduces every number.
Per-plant `dispatch/<y>_P1.parquet` comes from the NWPP-NEXT shard commits 2019 `37315fe2` … 2025
`b6a96c0c` (provenance only, rule 33(d)). The rebuilt pool EIA-930 benchmark reproduces the
scorer's C4 coal r exactly: 0.671 / 0.622 / 0.687.

## 0. Summary

**DO-NOT-REDO.** This lever was adjudicated yesterday. FINDING-nwpp-50 found no measured repair of
the side-inflow gate and predicted coupling INERT. The owner ruled "no solve", froze the gate and
routed C4 to daily placement and Jim Bridger (card D2). The §5.9 matrix header that still calls the
mainstem "the next C4 lever" is NWPP-49 text and is stale. Four new measurements, all pointing away
from the lever:

1. **Coupling does not restrain swing.** Model/actual intra-day sd is 1.7–6.5× at the 5 coupled
   downstream plants and 2.0–3.9× at the 9 uncoupled ones.
2. **The mainstem residual barely correlates with the coal residual:** r = −0.11 / −0.21 / −0.23.
3. **Even a perfect mainstem shape stays below 0.70.** With the measured shape and coal taking its
   energy share of the displacement, coal r is 0.670 / 0.639 / 0.697 (Δ −0.001 / +0.017 / +0.010).
4. **Nothing separates the pass years from the fail years.** The cascade exists only in 2023–25,
   yet 2019–22 pass without it. The U9 share of model hydro swing is 0.29–0.31 in every year.

**Verdict: not worth an LP.** The footprint is large (~7 TWh/yr of reshape) but mis-aimed.

## 1. Census: the nine uncoupled mainstem plants (U9, 10,919.4 MW)

All nine sit in `NWPP-NW` on an EIA-923 monthly budget. `hydro_ror_split` rule 0 (`regulated_chain`)
exempts them from the RoR pin, so each is **shapeable within the month** between 0 and pmax. Their
only hourly limit is the fleet-wide EIA-930 envelope and floor (`hydro_dispatch_envelope` /
`hydro_min_flow_floor`). None has a water-balance row, because none is downstream of a coupled link.

| stn | plant | EIA id | MW | BA | why no row | intra-day sd model/CROHMS, 23 · 24 · 25 | ratio |
|---|---|---|---:|---|---|---|---:|
| RRH | Rocky Reach | 3883 | 1,349.2 | CHPD | WEL→RRH τ celerity 34.9 mph (+6 SI mo) | 349/189 · 342/171 · 346/169 | 1.96 |
| WAN | Wanapum | 3888 | 1,220.0 | GCPD | RIS→WAN τ 23 h vs 0 h | 312/153 · 307/143 · 310/133 | 2.17 |
| PRD | Priest Rapids | 3887 | 950.0 | BPAT | WAN→PRD side inflow (SI), 13 mo | 252/100 · 247/92 · 245/99 | 2.57 |
| MCN | McNary | 3084 | 990.5 | BPAT | PRD+IHR→MCN SI, 6 mo (τ 13/0) | 257/75 · 251/67 · 251/63 | 3.71 |
| JDA | John Day | 3082 | 2,160.0 | BPAT | MCN→JDA SI, 3 mo | 537/169 · 525/162 · 531/160 | 3.24 |
| TDA | The Dalles | 3895 | 1,819.7 | BPAT | JDA→TDA SI, 15 mo | 401/97 · 399/107 · 404/102 | 3.94 |
| LWG | Lower Granite | 6175 | 810.0 | BPAT | DWR→LWG τ r 0.02 | 170/77 · 161/61 · 165/47 | 2.80 |
| LGS | Little Goose | 3926 | 810.0 | BPAT | LWG→LGS SI, 13 mo | 174/66 · 169/81 · 173/70 | 2.39 |
| LMN | Lower Monumental | 3927 | 810.0 | BPAT | LGS→LMN SI, 1 mo | 150/68 · 139/61 · 141/52 | 2.40 |
| Σ | | | 10,919.4 | | | 1,065/667 · 1,053/630 · 1,095/588 | 1.60–1.86 |

- **The seven side-inflow-only links** are WAN→PRD, PRD+IHR→MCN, MCN→JDA, JDA→TDA, LWG→LGS and
  LGS→LMN, plus WEL→RRH, which also fails τ. Their τ r ranges from 0.35 to 0.88. Each fails
  `SIDE_INFLOW_FLOOR_MAX_FRAC = 0.02` (`build_nwpp_hydro_cascade.py:161`) in 1–15 plant-months.
- **NWPP-36** read the 2–8 % downstream shortfall as spill-metering at the federal projects.
- **NWPP-50** found that only half right. JDA→TDA loses 4.4 % even in no-spill months (n = 21). The
  turbine-flow basis makes 4 of the 7 links worse, and USGS 14105700 is ~10× too noisy to arbitrate.
- **Plants that do have rows over-swing too.** Coupled downstream: CHJ 1.91, WEL 1.73, RIS 1.96,
  **BON 6.50**, IHR 2.45. Heads: GCL 1.61 (6,495 MW), DWR 9.13. In the model, 15 of 16 chain
  plants swing 0.21–0.27 × pmax within the day whether coupled or not; GCL swings 0.13 ×.

## 2. Hourly shape against actual, and the coal residual

U9 actual = CROHMS `Power.Total` (2023–25 only, aligned +1 h). cres / hres = model − EIA-930 coal / pool hydro. Swing = intra-day sd, model/actual (ratio).

| year | coal r | r_daily / r_intra | coal swing | pool hydro swing | BPAT hydro swing | r(cres,hres) | U9 share of hydro swing |
|---|---:|---|---|---|---|---:|---:|
| 2019 | 0.769 | 0.817 / 0.312 | 260/609 | 2,397/2,176 (1.10) | 1,670/1,275 (1.31) | −0.557 | 0.309 |
| 2020 | 0.720 | 0.778 / 0.553 | 297/685 | 2,075/2,052 (1.01) | 1,434/1,099 (1.31) | −0.517 | 0.299 |
| 2021 | 0.740 | 0.812 / 0.418 | 212/561 | 2,147/2,012 (1.07) | 1,549/1,345 (1.15) | −0.573 | 0.305 |
| 2022 | 0.771 | 0.844 / 0.467 | 202/549 | 2,090/1,883 (1.11) | 1,519/1,225 (1.24) | −0.574 | 0.309 |
| 2023 | **0.671** | 0.702 / 0.426 | 244/489 | 2,143/2,004 (1.07) | 1,572/1,168 (1.35) | −0.464 | 0.308 |
| 2024 | **0.622** | 0.679 / 0.454 | 126/615 | 2,221/1,918 (1.16) | 1,543/1,157 (1.33) | −0.453 | 0.293 |
| 2025 | **0.687** | 0.784 / 0.430 | 148/751 | 2,237/1,913 (1.17) | 1,579/1,037 (1.52) | −0.554 | 0.313 |

| U9 vs CROHMS | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| hourly r | 0.745 | 0.576 | 0.713 |
| r_intra | 0.536 | 0.480 | 0.499 |
| within-month day-to-day sd, model/actual (MW) | 419/451 | 412/391 | 467/588 |
| energy, model/actual (TWh) | 33.43/33.80 | 32.84/33.04 | 35.56/36.24 |
| r(cres, U9 residual): all | −0.107 | −0.208 | −0.230 |
| r(cres, U9 residual): daily | −0.195 | −0.326 | −0.346 |
| r(cres, U9 residual): intra | −0.104 | −0.179 | −0.209 |

What this shows:
- **Mainstem shape:** U9 over-swings 1.6–1.9× within the day, while the pool over-swings only
  1.07–1.17×, so the rest of the fleet under-swings. The day-to-day term and the energy are about
  right.
- **The hydro↔coal residual link does not mark the C4 failure.** It is the generic substitution at
  about −0.5 and is equally strong in the pass years.
- **What changes in 2023–25 is coal, not hydro.**
  - Model coal intra-day amplitude falls to 0.20× in 2024–25, while actual coal swing rises to
    615–751 MW.
  - r_daily slips to 0.68–0.70 in 2023–24.
  - BPAT's over-swing is only mildly larger (1.33–1.52× against 1.15–1.31× in the pass years), and
    the U9 share stays flat.
- **So the amplitude defect is on coal's side, not the mainstem's.** This matches FINDING-nwpp-48
  (Jim Bridger / Huntington / Hunter, daily placement). The mainstem residual explains ≤ 5 % of
  coal-residual variance (r² ≤ 0.053).

## 3. Upper bound on what coupling could move

The counterfactual puts U9 on its **measured** shape, scaled per plant-month to the model's own
energy, since coupling conserves each budget. No coupling row can restrict the plants more than this.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| reshape Σ\|Δ\| on U9 (TWh) | 6.74 | 7.16 | 7.09 |
| coal residual Σ\|cres\| (TWh) | 10.02 | 7.53 | 9.65 |
| coal r, all displacement → coal | 0.616 | 0.541 | 0.558 |
| coal r, coal takes its energy share | 0.670 | 0.639 | 0.697 |
| coal r, whole-pool hydro measured-shape, all → coal | 0.755 | 0.655 | 0.655 |

- **Size vs direction:** the reshape is comparable in size to the coal residual, but orthogonal to
  it.
- **Ceiling:** a perfect mainstem shape still fails C4 in all three years, and a perfect **pool**
  hydro shape still fails 2024–25.
- **Real rows reach less than this.** Rows of this construction are slack ≥ 8,686 h/yr at RIS, IHR,
  BON and WEL (NWPP-50 §2), and those coupled plants still over-swing 1.7–6.5× (§1).

## 4. Verdict, and what an arm would be

**Not worth an LP.** The lever is mis-aimed rather than too small. It is also blocked three ways:
- rule 23: the gate may not be re-derived because a residual moved;
- rule 1: a structure is not selected by C4;
- the NWPP-50 owner ruling.

**The arm, for the record.** There is **no `ScenarioConfig` flag to set**:
- `hydro_cascade_coupling` is already `True` in the keeper.
- Coupling the 7 links would mean flipping `coupled` in
  `data/raw/nwpp-hydro/nwpp_hydro_cascade_links.csv`. That is done through `SIDE_INFLOW_FLOOR_MAX_FRAC`
  or a flow-basis change in `scripts/data/build_nwpp_hydro_cascade.py`, a script constant that is
  off-registry (rule 24).
- `load_hydro_cascade` would pick the change up through the solve-surface fingerprint.

**Missing measured data.** An independent lower-river flow measurement (dam acoustic gauges, or BPA's
modified-flow study) is the only thing that could reopen the gate; neither is in hand. A fish-spill
floor on `S_d` (ROD / Fish Operations Plan) stays routed and unchartered.

**Where C4 lives:** coal amplitude and daily placement. Jim Bridger's CAMPD shape alone cleared C4 in
all three years (FINDING-nwpp-48 §3, on the NWPP-47 keeper). The owner's post-NWPP-50 routing stands.

**Routed, not acted on:** the model gives 15 of 16 chain plants nearly the same swing-to-pmax
fraction, and BON (6.5×) and DWR (9.1×) over-swing most. That is a hydro-allocation question for a
hydro-structure lane under rule 1, not a C4 lever; §3 caps its payoff.

## 5. Reported, not absorbed

- The §5.9 matrix header is stale; a matrix lane should re-point it.
- CROHMS RIS/RRH `Power` has sentinel spikes; values < 0 or > 1.1 × pmax are screened and interpolated.
- Inherited, unchanged: the C1 demand-basis gap, C5a CO2, and the attestation corrections owed.
