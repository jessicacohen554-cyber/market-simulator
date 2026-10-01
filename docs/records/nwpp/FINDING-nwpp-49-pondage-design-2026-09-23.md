# FINDING nwpp-49: pondage for NWPP — design, intake, prediction. Zero LP.

**Lane:** NWPP-49 · **Date:** 2026-09-23 · **Owner ruling:** D1 APPROVED (D2, D3 deferred) ·
**Zero LP. Nothing solved, nothing registered.** No `src/` change.
**Control:** keeper `2026-09-22-nwpp-47-grid-wind` (`results/calibration/nwpp47_gridwind_span`).
**Probe:** `scripts/probes/_nwpp49_pondage_phase0.py` → `results/calibration/_nwpp49_pondage_phase0.json`
(committed probe record, the `_caiso16x_*.json` precedent).
**Evaluator (committed before any leg exists):** `scripts/probes/_nwpp49_gates.py`.

## 0. In one line

**No admissible pondage design is predicted to clear C4 in any year.** The recommended design (a2)
is structurally clean and small: it bounds 2.7 GW of off-chain plants and is predicted to cut
hydro's excess intra-day swing by at most a third, lifting coal `r` to **≤ 0.670 / 0.647 / 0.674**.
The hydro over-swing sits on the **uncoupled Columbia/Snake mainstem (10.9 GW)**. A flat-inflow
pondage row cannot bound those plants correctly: measured operation breaks it.

## 1. What each mechanism constrains, per plant-hour

Both mechanisms build the same row: `P/η + S + V(t) − V(t−1) = arrivals(t)`, with `0 ≤ V ≤ B` and
free spill. They differ only in **arrivals** and **B**.

| | cascade (`hydro_cascade_coupling`, K) | pondage (`hydro_pondage_bound`, U) |
|---|---|---|
| plants with a row | 5: CHJ 3921, WEL 3886, RIS 6200, BON 3075, IHR 3925 | every plant with NID storage < its largest month |
| arrivals | upstream `P_u(t−τ)/η_u` + spill, **hourly-shaped**, plus measured side inflow | own monthly budget ÷ hours, **flat within the month** |
| B | measured **operated** band (CROHMS forebay range × NID area) | NID **gross** volume × head, η = 1 (upper bound) |
| units | kcfs·h, measured η | MWh, η ≡ 1 |
| other plants touched | upstream `P_u` enters d's row: GCL 6163, RRH 3883, TDA 3895, LMN 3927 | none |

**Where they overlap.** They overlap only at the 5 cascade-row plants. Two rows there would mean two
balances on one forebay, which rule 19 forbids. The 4 upstream-only plants carry **no** balance of
their own. Adding a pondage row there would add a second, independent statement about the same
water: the plant's own spill column would be free, while the cascade already counts that plant's
spill as measured monthly-mean spill on the downstream right-hand side.

## 2. Measured test: is a flat-inflow row valid for a regulated mainstem plant?

CROHMS hourly `Power.Total` at the 16 projects, 2023–25. For each plant: how much storage its
**measured** output needs, given the row's own flat inflow, in hours of its mean output. Compare with
each candidate B.

| plant | storage needed with flat monthly inflow (h) | …with flat daily inflow (h) | NID B (h) | operated band B (h) |
|---|---|---|---|---|
| The Dalles 3895 | 90 / 117 / 170 | 3.9 / 3.9 / 2.9 | **62 / 62 / 57** | **2.6 / 2.6 / 2.4** |
| Priest Rapids 3887 | 97 / 133 / 108 | 4.5 / 5.9 / 6.1 | **35 / 35 / 32** | 6.1 / 6.1 / **5.6** |
| Rocky Reach 3883 | 88 / 128 / 115 | 6.8 / 5.8 / 6.4 | **78 / 80 / 75** | **4.1 / 4.2 / 3.9** |
| Lower Monumental 3927 | 264 / 170 / 275 | 10.4 / 12.3 / 7.1 | 249 / 303 / **262** | **7.5 / 9.1 / 7.9** |
| Wanapum 3888 | 113 / 146 / 122 | 6.2 / 6.2 / 5.7 | 141 / **143** / 129 | 14.3 / 14.4 / 13.1 |
| John Day 3082 | 117 / 107 / 180 | 6.9 / 4.7 / 4.9 | 373 / 368 / 338 | 19.9 / 19.6 / 18.0 |
| McNary 3084 · Lower Granite 6175 | 151–269 | 3.4–14.1 | UNSET (no HILARRI link) | 9.9–22.2 |

Bold = the measured dispatch **violates** the row.

* **With the measured operated band, a flat-inflow row forbids what these plants do every day**
  (TDA, RRH, LMN, and PRD in 2025). The band is correct. The flat inflow is wrong: a mainstem
  plant's inflow is its upstream neighbour's shaped release. That is why NWPP-36 built the cascade
  row, not a pondage row.
* **Even NID gross volume, the loosest possible B, is broken at month scale** at TDA, PRD and RRH
  (and at LMN in two years, WAN in one). Real inflow varies day to day, and a flat monthly inflow cannot
  represent that. **Within a day, NID never binds at any CROHMS plant.**
* Rule 13/14 consequence: a bound that measured operation violates is not a measured physical input.
  It would be the wrong structure. **Pondage cannot be armed on a regulated mainstem plant.**

## 3. Design options (rule 19) — recommendation: **(a2)**

| option | plant set for pondage rows | verdict |
|---|---|---|
| **(a)** off-cascade | every plant without a cascade row, including upstream-only GCL/RRH/TDA/LMN and the uncoupled mainstem | **Refused.** Breaks at TDA/PRD/RRH on measured data (§2), and stacks a free-spill balance on 3 upstream-only plants whose spill the cascade already counts as measured |
| **(b)** pondage B becomes the cascade pond capacity on the mainstem | cascade plants | **Refused.** Swaps the measured operated band for NID gross volume, a less accurate datum, which rule 14 forbids. The cascade's B is already the better number |
| (c) measured band + flat inflow on the uncoupled mainstem | 9 mainstem plants | **Refused.** Inadmissible per §2. The static clip overshoots too: hydro intra-day sd drops to **0.82 / 0.89 / 0.85×** measured |
| **(a2) off-chain** | every plant **not** in `nwpp_hydro_chain.csv` (NWPP-36's committed reach table: 27 plants on 5 regulated chains) | **Recommended.** Exactly one balance per plant. No shared plant. No change to the cascade's rows |

**(a2), stated so it can be checked.** The cascade formulation owns every plant in the registered
regulated reach table, coupled or not. The flat-inflow pondage row owns every other plant with
identified storage below its largest month. The two plant sets are disjoint by construction.

* **Structural:** the partition, and the fact that inflow below a regulating project is not flat.
* **Measured:** NID volume and head, the HILARRI linkage, and the chain table (a published transcription
  from BPA's *Inside Story* plus EHA). Nothing new is introduced.
* **Zero DOF:** no threshold, no percentile, no efficiency, no registry entry. The chain table was
  committed by NWPP-32 for another purpose and is not chosen here.
* **Cost:** the uncoupled mainstem (10.9 GW) stays **unbounded within the month**. (a2) does not fix
  that. It declines to fix it with the wrong row (§5).

**Code (not written; owner rules first).** `pipeline/kwargs.py::resolve_hydro_cascade`: when both
flags are on, build the cascade spec. Then build `load_hydro_pondage` over the hydro plants whose code
is not in `<iso>_hydro_chain.csv` (a per-ISO artifact that is data-driven, never `if iso ==`). Then
concatenate the two link-free/linked specs into ONE `HydroCascadeSpec`. Pondage rows are appended
after the cascade rows, `eta_dn ≡ 1`, and no links are added. The engine is unchanged, because
`build_hydro_cascade_rows` is per-row. The `ValueError` becomes a check that the two plant sets are
disjoint. Unarmed and cascade-only runs stay byte-identical. The only new key is the one that arms both
flags. Estimated at ~60 lines plus a unit test on the one-zone chain fixture.

## 4. Intake (done, committed)

`data/raw/nwpp-hydro/nwpp_hydro_pondage.csv`: 168 plants, 31,746.8 MW. It was built with the
unchanged `build_hydro_pondage.py --iso NWPP`, and the NID subset
`data/raw/nid/nid_nwpp_hydro_dams.csv` (vintage 2026-9-11) rebuilds it **byte-identical**.
Provenance: `data/raw/nid/README.md` and `data/raw/nwpp-hydro/README.md`. 11 plants (175.7 MW) use
the labelled NID-height proxy.

Coverage on the 2024 LP fleet (35,694.6 MW, 280 plants):

| group | UNSET (no bound) | redundant (holds a month) | row built |
|---|---|---|---|
| on the registered chains | 6 / 2,911 MW (McNary, Lower Granite, Ice Harbor, …) | 6 / 8,630 MW | 15 / 16,557 MW, **excluded by (a2)** |
| off-chain, i.e. **(a2)'s set** | 113 / 1,127 MW | 66 / 3,786 MW | **74 / 2,683 MW** |

Storage in nameplate-hours for (a2)'s 2,683 MW: < 6 h **732**, 6–24 h 529, 24–168 h 893, ≥ 168 h 530.
Only the < 6 h tranche can bind within a day. At flat daily inflow, any daily shape needs at most
24·c·(1−c) ≤ 6 nameplate-hours of storage.

**Contract deviation, stated:** the pondage family (NYISO, PJM, now NWPP) is a raw derived CSV read
directly by `data/hydro.py::load_hydro_pondage`. It has no `data/dictionary` schema and no
`read_clean` seam. Moving it onto the clean contract changes the loader for all three ISOs. That is
`src` work outside a zero-LP intake lane, so it was not done here.

## 5. Zero-LP prediction and pre-registered kill condition

**Method.** The per-plant legs of the keeper are gone (the NWPP-47 shard branches were cut). So each
plant's model shape is a **pro-rata proxy**: the keeper's fleet hydro hour × the plant's share of the
month's budget. Where the proxy's required storage exceeds B, its within-month deviation is shrunk
until it fits, with monthly energy kept. The proxy gives every small plant the fleet's full swing, so
it **over-states** the effect. Treat it as an upper bound.

Metric: hydro intra-day sd, model ÷ EIA-930 (the scorer's pool benchmark; reproduces NWPP-48's
2,004 / 1,918 / 1,913 MW measured and coal r 0.659 / 0.617 / 0.638 exactly).

| year | keeper ratio | **(a2) predicted** | INERT if arm ≥ | coal r (keeper → bracket) | coal r_intra bracket | C4 |
|---|---|---|---|---|---|---|
| 2023 | 1.075 | **1.044 – 1.075** | 1.065 | 0.659 → 0.659–0.670 | 0.374–0.464 | FAIL |
| 2024 | 1.155 | **1.120 – 1.155** | 1.145 | 0.617 → 0.617–0.647 | 0.396–0.589 | FAIL |
| 2025 | 1.169 | **1.129 – 1.169** | 1.159 | 0.638 → 0.638–0.674 | 0.365–0.527 | FAIL |

The coal bracket runs from "coal absorbs none of the removed swing" to "coal absorbs all of it".
For comparison, refused option (a) reaches 0.673 / 0.656 / 0.700 at its upper edge.

**Kill condition** (`_nwpp49_gates.py`; checked on the keeper itself, where it returns INERT as it
must):
* **INERT → I:** the intra-day ratio falls < 0.010 in **every** year.
* **OVERSHOOT → R:** the ratio falls below 0.95 in any year; **or** hydro annual energy moves > 1.0 TWh
  (rule-19 invariant; keeper 106.872 / 107.879 / 113.077); **or** any C1 COAL row leaves ±8.00 TWh.
* C4 is **not** a limb in either direction (rule 1). C1 passes by only 0.79 TWh (2023 CC_REGULAR
  −7.213 vs ±8.00), so any flip is reported at full magnitude.

**Expected verdict:** a real but small move. The INERT limb is **likely to fire in at least one
year**: the upper-bound drop is 0.031–0.040, the ceiling needs 0.010, and the true effect is smaller
than the proxy.

## 6. LP cost, if the owner wants the solve

* First, the resolver change in §3 (Opus/Fable, rule 27), merged behind both flags.
* Then 3 year-isolated shards (rule 36), one per year, `replay_keeper.py … --set
  hydro_pondage_bound=true`. The shard hard-stops on the keeper's four hydro flags. Expect
  ~60–100 min per shard and ~100 min wall-clock in parallel. Then compose, score and register (zero
  LP in the parent).
* **Recommendation:** on this prediction, **do not spend the shards on C4.** Arm (a2) only if the
  owner wants the off-chain bound for its own structural sake (rule 1). That is worth doing but is not
  urgent. It is predicted not to move a determination.

## 7. Where the C4 lever actually is (routed, not acted on)

The over-swing lives on the **uncoupled mainstem**: TDA, JDA, MCN, PRD, WAN, RRH, LWG, LGS, LMN
(10.9 GW). It stays unbounded because NWPP-36 left their links uncoupled. Seven failed only the 2 %
side-inflow floor in spill-season months, a failure NWPP-36 itself attributes to a **spill-metering
artefact** (downstream metered outflow reads 2–8 % below upstream in Apr–Aug). Two more failed on
tau: WEL→RRH celerity and RIS→WAN aliasing. Coupling them puts the **measured band** in the **right**
formulation, with shaped upstream arrivals. For that set, option (c)'s clip (hydro sd 0.82–0.89×
measured, coal r up to 0.692 / 0.729 / 0.666) is the over-constrained bound, not the answer.
**Candidate owner card:** a cascade lane re-examining the side-inflow gate against the spill-metering
evidence. That is `hydro_cascade_coupling`'s own data (K cell), not pondage.

## 8. Reported, not acted on

* **Observability gap (optional item 4, not done):** the hydro budget and envelope duals are still
  written to no sidecar. Wiring them touches `model.py` extraction and the sidecar writer, which is
  not cheap enough for this lane.
* **Benchmark drift:** `--restore-shared-inputs` on the keeper now regenerates `eia923` to different
  bytes (`0c4cb0be34ca` vs recorded `84bb6ac40d29`) and stops before writing `eia930`. The
  benchmark builders have changed since the NWPP-47 solve. A future NWPP leg scored at HEAD will
  score against a different `eia923` than the keeper unless this is resolved. The probe here used
  the scorer's pool builder directly and reproduces the keeper's committed r exactly.
* Inherited and untouched: the C1 demand-basis gap (open owner decision); C5a CO2; Jim Bridger's
  missing COAL tranche row; the NWPP-40/41/42 attestation corrections; the leftover
  `claude/nwpp-47-arm-*` branches, which are already gone from origin at this writing.

## 9. Retrievability

Nothing was solved. The committed artifacts are the pondage CSV, the NID subset, the two probes, the probe's
JSON record and this doc.

## 10. Owner ruling (2026-09-24) — superseding §6's recommendation

"Adopt the same hydro stuff as other ISOs aside from the unique config due to cascade", clarified as
**"RoR split, chain exempt"**. No keeper in any ISO arms pondage, so the arm being solved is
`hydro_ror_split` with the registered chain exempt, **not** pondage (a2). Design, G-DRIFT, prediction
and kill condition: `PRECOMMIT-nwpp-49-ror-split-2026-09-24.md`.
