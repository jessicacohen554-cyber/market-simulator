# FINDING — caiso-172: CAISO **does** resolve sub-TAC load, and the Path-15 split is now MEASURED

**Session** caiso-172 · **Date** 2026-08-04 · **Branch**
`claude/caiso172-subtac-load-survey-8ty8zu`
**Pre-registration** `PRECHECK-caiso172-path15-load-split-2026-08-04.md` (pushed
before any solve, commit `789e28b8`)
**Incumbent keeper at session start** `2026-08-04-caiso-166-measured-dlap`
(CALIBRATED-WITH-CAVEATS, 0 FAILs, 2 owner-ledgered caveats; `audit_keepers
--iso CAISO` PASS; CAISO absent from `complete`; holdout freeze ACTIVE, so
**2023 / 2024 / 2025 only**).

---

## 0. The headline

`ASSESSMENT-caiso171-frontier-2026-08-04.md` §5 item 3 left exactly one
unresolved question gating CAISO's `complete` declaration, and named it the
only thing that could unseat the frontier claim:

> **does CAISO publish load at sub-TAC (NP15/ZP26) grain at all?**

**It does — and the model was not using it.** Not as a load MW series (every
such route is walled, §1), but as the two published halves of the split, which
join to give the quantity directly. `CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']` — the
**last residual-identified member** of that table, issue #1372, and the DOF entry
whose own `root_cause` had deferred this since 2026-07-07 — is now **measured**:

| | NP15 | ZP26 |
|---|---:|---:|
| was (estimate, "unverified provenance") | 0.86 | 0.14 |
| **now (measured, 2023–2025 day-weighted mean)** | **0.883951** | **0.116049** |

The estimate put **17 % too much PG&E load in ZP26**. Because PG&E's TAC area
straddles **Path 15**, this is the load allocation sitting on the exact boundary
that carries KNOWN-OPEN 1.

Per rule 20 `[R-DOF]` this is a **closure, not a new parameter**: zero free
parameters, zero `ScenarioConfig` fields, and the ledger entry moves
`residual → measured`.

---

## 1. The survey — five walls and one open door

Instrument: `scripts/probes/_caiso172_subtac_load_survey.py` (committed, network,
no LP, no solve), built on the caiso-141 model so the verdict is re-checkable the
day a source changes.

| id | candidate | verdict |
|---|---|---|
| **S1** | OASIS `SLD_FCST` — already wired as the `load` dataset | **WALL.** TAC-area grain under **every** `market_run_id` (ACTUAL/DAM/2DA/7DA/RTM) and version. The live domain is 34–35 areas, but the CAISO-internal ones are only `PGE-/SCE-/SDGE-/VEA-TAC` (+`MWD-TAC`); every other area is an **external WECC BA** (BPAT, PACE, NEVP, LADWP, BANC…) carried for the WECC-wide forecast. Zero sub-TAC / zonal areas. |
| **S2** | the OASIS report catalogue | **AVAILABLE** — `ATL_LDF` × `ATL_PNODE_MAP` (§2). Catalogue enumerated from the published Interface Specification v5.1.2, then probed live. |
| **S2b** | `ENE_SLRS`'s `TAC_ZONE_NAME` | **WALL — and this one is a trap worth recording.** `ENE_SLRS` publishes `TOT_LOAD_MW` over `TAC_NORTH / TAC_NCNTR / TAC_ECNTR / TAC_SOUTH / NONTAC`, a *different vocabulary* from the `*-TAC` areas, summing exactly to the ISO total — which is precisely what a Path-15 split would look like. It is not one. `ATL_TAC_AREA_MAP` puts the ZP26-side landmarks (**Gates, Midway, Panoche, Elk Hills, Helms, Balch, Haas**) in `TAC_NORTH` **together with** the Bay-Area/North landmarks (Moss Landing, Geysers, Vaca-Dixon, Round Mountain, Tesla, Cottonwood). `TAC_NORTH` spans Path 15 ⇒ it is the utility geography relabelled. (Corroborating: `TAC_NCNTR` ≈ 72.6 MW ≈ VEA's 76.4 MW; `TAC_SOUTH` ≈ SDG&E; `TAC_ECNTR` ≈ SCE.) |
| **S3** | CAISO DLAP price nodes (the caiso-165 intake) | **dismissed, as chartered.** Every `PRC_LMP` item at `DLAP_PGAE-APND` is a $/MWh component (`LMP/MCC/MCE/MCL/MGHG`); none is a load quantity. **Note for the next session:** OASIS names its generic value column `MW` on *price* reports too, so the presence of an `MW` column proves nothing — the discriminator is the data item. The *load* companion of a DLAP is `ATL_LDF`, which is what §2 uses. |
| **S4** | FERC Form 714 / CEC demand forecast | **WALL.** FERC-714 still HTTP **403** from this environment (unchanged from the 2026-07-05 attempt), on both the bulk CSV and the data landing page. CEC's planning areas (PG&E Bay Area / PG&E Valley) remain **boundary-mismatched to Path 15** regardless of reachability, so CEC is walled on geometry, not access. |
| **S5** | EIA-930 sub-BA route | **WALL.** Demand-only by schema (`data` columns `['value']`, facets `['parent','subba']`); re-confirms caiso-141 S5 by citation rather than re-derivation. |

### 1.1 Side finding, logged and NOT actioned — `MWD-TAC`

`MWD-TAC` (Metropolitan Water District, ~208 MW ≈ **0.9 % of ISO load**) is a
real CAISO TAC area that is **absent from the committed
`CAISO_tac_load_hourly_*.csv` series and from `CAISO_TAC_ZONE_WEIGHTS`**. The
committed series carries only five areas; the live `SLD_FCST` domain carries six,
and `CA ISO-TAC` reconciles to the six-way sum exactly (22,540 = 22,539).

It is an **SP15-side** omission — MWD's Colorado River Aqueduct pumping load is
southern-California — so it is **not** a Path-15 object and is deliberately out
of scope here. Recorded as a separate open item; closing it means re-fetching the
TAC load series with `MWD-TAC` included and adding its row to the weights table,
which is a demand-input intake in its own right.

---

## 2. The construction

Frozen derive: `scripts/data/derive_caiso_path15_load_split.py` (rule 23
`[R-FROZEN-DERIVE]` — re-derives **only** when its source bytes change; it reads
no model output and no residual). Source bytes committed under
`data/raw/caiso-atlas/` so the derive runs with **no network**.

No report publishes an NP15/ZP26 load **MW series**. CAISO publishes both halves:

* **`ATL_LDF`** — per-pnode **Load Distribution Factors** inside
  `DLAP_PGAE-APND`: CAISO's own published weighting for distributing PG&E LAP
  load onto nodes. **1,668 load pnodes summing to exactly 100.000.**
* **`ATL_PNODE_MAP`** — CAISO's **authoritative** `TH_NP15_GEN` / `TH_ZP26_GEN` /
  `TH_SP15_GEN` pnode membership: the Path-15 / Path-26 geography itself, as
  CAISO defines it for its own trading hubs.

Joined by **substation** (`SUBSTATION_voltage_id`), two-tier:

1. **tier 1 — direct substation match.** A substation counts only if *all* its
   hub pnodes agree; ambiguous substations are dropped, never majority-voted.
   483–492 PG&E load pnodes per year.
2. **tier 2 — PG&E sub-LAP dominant hub.** The 15 `SLAP_PG*` sub-LAPs partition
   **95.78 %** of `DLAP_PGAE` and classify near-perfectly against tier 1:

   | sub-LAP | share of PG&E | tier-1 NP15 : ZP26 |
   |---|---:|---|
   | `SLAP_PGZP` (the ZP26 sub-LAP) | 6.893 | **0 : 39** |
   | `SLAP_PGKN` (Kern) | 4.293 | **0 : 21** |
   | `SLAP_PGF1` (Fresno) | 13.015 | 71 : 3 |
   | the other twelve | 71.583 | 100 % NP15 |

3. **residue** — ~2.2 LDF points reach neither tier; **reported and excluded from
   the normalisation**, never folded into a side.

Effective windows are **day-weighted** within each calendar year (CAISO reissues
the Atlas reports seasonally).

### 2.1 Result and acceptance

| year | NP15 | ZP26 | residue (pts) | tier-1 nodes | windows |
|---|---:|---:|---:|---:|---:|
| 2023 | 0.883565 | 0.116435 | 2.473 | 483 | 10 |
| 2024 | 0.884464 | 0.115536 | 2.152 | 488 | 9 |
| 2025 | 0.883996 | 0.116004 | 2.152 | 492 | 7 |
| **mean** | **0.883951** | **0.116049** | | | |

Pre-registered §4 data gates: **10/10 PASS** (LDF sum 100.000 ≥ 99.99 each year;
residue ≤ 5.0; tier-1 ≥ 300; inter-year spread 0.0011 ≤ 0.010). The spread is an
order of magnitude below the 0.024 correction itself, which is why a single
static scalar is the right shape.

---

## 3. Why this is admissible — and what it is not

**Rule 14 `[R-ACCURATE]` — the misalignment exception is SPENT.** The incumbent
`constants.py` comment kept the estimate under that exception, on the premise
that *"no TAC boundary exists at Path 15 to measure the split directly."* That
premise is **true and irrelevant**. The exception licenses an estimate only where
the real data is *genuinely misaligned to our representation*. Here the real data
is `ATL_PNODE_MAP` — **CAISO's own Path-15 hub geography**, the exact boundary
the model's `NP15↔ZP26` link represents. It was never misaligned; it had simply
not been found. Rule 14's reconciliation clause then applies directly: prefer the
reconciled real data over the guess, and document the reconciliation — §2 and
this section are that documentation.

**Rule 13 `[R-MEASURED]` admissibility test — passes.** The quantity regenerates
for a forward year from published forward bytes and responds to changed
conditions (Kern/Fresno load growth against Bay-Area growth moves it). Nothing
is tuned to a residual; the derive never reads a model output.

**What it is NOT** — stated so it cannot be over-claimed later:

* **Not an hourly NP15/ZP26 load series.** An LDF is a *typical* distribution
  factor. This replaces a static scalar with a **measured static scalar** — the
  same kind of object, identified instead of assumed. No hourly sub-TAC load
  series is published (S1/S2b).
* **Not a C3a lever**, and **no N–S topology lever is chartered off it**
  (caiso-164 §0/§6 stands).
* **Not a re-pick.** The value is what the published bytes say, not a value
  chosen against any residual.

---

## 4. The A/B

Both arms replay the **same** keeper recipe (`caiso166_measured_loss_zones`)
through the sanctioned `scripts/replay_keeper.py` channel, at the **same
commit**, over `2023 2024 2025` in one invocation (rule 16 `[R-ALLYEARS]`),
**sequentially** — one CAISO plant-level multi-zone LP peaks at ~8.4 GB on a
16 GB box, so concurrent arms would OOM (rule 12's caution). Driver:
`scripts/probes/_caiso172_ab_driver.sh`; scorer
`scripts/probes/_caiso172_ab_compare.py`.

| arm | run id | `PGE-TAC` |
|---|---|---|
| **A control** | `2026-08-04-caiso-172-control-pge` | NP15 0.86 / ZP26 0.14 |
| **B candidate** | `2026-08-04-caiso-172-measured-path15` | NP15 0.883951 / ZP26 0.116049 |

### 4.1 The control is BIT-IDENTICAL to the incumbent keeper

| year | max \|Δprice\| | max \|Δdemand\| | Δ mean LMP |
|---|---:|---:|---:|
| 2023 | 0.000000 | 0.000000 | +0.000000 |
| 2024 | 0.000000 | 0.000000 | +0.000000 |
| 2025 | 0.000000 | 0.000000 | +0.000000 |

Over **all** P1 zone-hours of all three years. This is what licenses reading
the Arm B delta as the mechanism's own effect: the replay harness is
byte-faithful and this head introduces no incidental drift. The control also
scores **identically to the keeper**, criterion for criterion.

### 4.2 The QUANTITY observable — checked BEFORE any price

The caiso-162 standing lesson is that a `run_config.json` recording a mechanism
as armed is **not** evidence the LP saw it. Two checks, in order:

1. **Pre-solve, on the call site.** `CAISO_TAC_ZONE_WEIGHTS` is consumed by
   `scripts/data/curate_zonal_shares.py` (via `_PARSE_FUNCS`, which
   `eia930/zonal_shares.load_zonal_shares` falls back to) — the **backcast**
   demand path. Patching the weights moves the hourly zonal share arrays:
   ZP26 share of PG&E `0.1400 → 0.1160` in every year, NP15 `+0.0104…+0.0111`
   of ISO load. *(The first attempt at this check patched the wrong binding and
   returned "identical" — which is exactly the failure mode the lesson names,
   caught here rather than discovered later.)*
2. **Post-solve, on served energy.**

| year | zone | control (TWh) | arm (TWh) | Δ | Δ % |
|---|---|---:|---:|---:|---:|
| 2023 | NP15 | 82.298 | 84.590 | +2.292 | **+2.78 %** |
| 2023 | ZP26 | 13.397 | 11.105 | −2.292 | **−17.11 %** |
| 2024 | NP15 | 80.932 | 83.186 | +2.254 | +2.79 % |
| 2024 | ZP26 | 13.175 | 10.921 | −2.254 | **−17.11 %** |
| 2025 | NP15 | 76.912 | 79.054 | +2.142 | +2.79 % |
| 2025 | ZP26 | 12.521 | 10.379 | −2.142 | **−17.11 %** |
| | ISO total | | | | **−0.0000 %** |

The −17.11 % is exactly the input change (`0.116049/0.14 − 1`), and the ISO
total is conserved to 0.0000 % — the load is **moved**, not created or lost.

### 4.3 The FLOW observable

| year | arm | mean MW | p50 | TWh N→S | hours at bound |
|---|---|---:|---:|---:|---:|
| 2023 | control | 1172.8 | 885.1 | 10.274 | 1 |
| 2023 | **arm** | 1018.3 | 630.4 | **8.920** | 1 |
| 2024 | control | 1391.6 | 1333.8 | 12.191 | 6 |
| 2024 | **arm** | 1221.4 | 1075.4 | **10.700** | 4 |
| 2025 | control | 1396.4 | 1309.6 | 12.233 | 21 |
| 2025 | **arm** | 1228.9 | 1052.1 | **10.765** | 13 |

Path-15 north→south transfer falls **−13.2 / −12.2 / −12.0 %** and the link
sits at its bound in fewer hours (2025: 21 → 13). This is the physically
obligatory direction: less load south of Path 15 needs less transfer across it.

### 4.4 The price basis — REPORTED, NOT GATED

| year | measured | cong. share | control | **arm** | arm / measured |
|---|---:|---:|---:|---:|---:|
| 2023 | +5.947 | 80.2 % | +0.236 | **+0.333** | 4.0 % → **5.6 %** |
| 2024 | +8.576 | 87.2 % | +0.127 | **+0.217** | 1.5 % → **2.5 %** |
| 2025 | +5.727 | 81.7 % | +0.109 | **+0.179** | 1.9 % → **3.1 %** |

The NP15−ZP26 basis moves **toward** the measured value in all three years — a
~40–65 % relative increase. **This closes nothing.** KNOWN-OPEN 1 is the
congestion majority (80–87 % of a $5.7–8.6/MWh basis) and the model still
reproduces only **2.5–5.6 %** of it. Per PRECHECK §6 this quantity was fixed
in advance as **reported and never gated**, because steering a load-split input
by a price residual is the outcome pin rule 13 forbids. **No N–S topology lever
is chartered off this result** (caiso-164 §0/§6 stands).

### 4.5 The scored verdict — determination-NEUTRAL

| | determination | FAILs | ledgered caveats | C3a 2024 / 2025 |
|---|---|---:|---|---|
| keeper (caiso-166) | CALIBRATED-WITH-CAVEATS | 0 | 2 | +11.5 % / +14.4 % |
| control | CALIBRATED-WITH-CAVEATS | 0 | 2 | +11.5 % / +14.4 % |
| **arm** | **CALIBRATED-WITH-CAVEATS** | **0** | **2** | **+11.5 % / +14.4 %** |

**Every criterion is identical between the arms**, including both C3a
magnitudes and the C3c tail counts. Load-weighted mean LMP moves
+0.017 / +0.020 / +0.004 $/MWh (≈ +0.03 %) — far too small to move any gate.

The substitution therefore **costs nothing and buys a degree of freedom**. The
PRECHECK §6 promotion condition (determination no worse, 0 FAILs, caveat count
not increased) is met.

---

## 5. Disposition — PROMOTED

`2026-08-04-caiso-172-measured-path15` is the CAISO keeper. Both arms are
registered on the dashboard (rule 15 `[R-DASHBOARD]`); the control is registered
as a **control, not a candidate**, and its own ledger still carries `PGE-TAC` as
residual so it describes its own solve rather than the arm's.

**DOF ledger — a closure (rule 20 `[R-DOF]`):**

| | before | after |
|---|---:|---:|
| `n_entries` | 11 | **11** |
| `n_residual` | 9 | **8** |
| CAISO ISO-specific residual | 4 | **3** |

`gen_caiso172_attestation.py` **fails closed** on each claim a machine can
check: the arms' `scenario_config` must be identical (the delta is a
`constants.py` table, not a config field); `constants.py` must equal the derived
artifact to 6 dp (so the attestation cannot claim "measured" over a hand-typed
number); and the ledger must show exactly this closure — `measured`,
`n_entries` unchanged, `n_residual` down by exactly one.

**Rule 22 leave-one-year-out:** this session fits nothing and moves no free
parameter, so LOYO reduces to the no-held-out-degradation check — all three
years carry the same correction in the same direction and no criterion flips in
any year, so no single year carries the result.

**Holdout:** solved 2023/2024/2025 only. CAISO holds no `complete` marker and
the spend freeze is ACTIVE, so 2022 / 2019 / ≤2021 / H1-2026 stayed fully
quarantined. `calibration-complete.json` and `holdout-freeze.json` are
**untouched** — both are owner acts. Rule 22 D-5(b) re-keying does **not**
apply: it binds only ISOs that hold a `complete` entry, and CAISO does not.

---

## 6. What this means for the `complete` question

The prompt framed this as the fourth-wall test: if no sub-TAC publication
exists, limb (b) of `complete` ("we have tested everything we could have") is
**confirmed**; if one exists and the model is using a residual-fitted split
instead, limb (b) is **false** and the declaration should wait.

**The second branch fired.** At session start limb (b) was **FALSE** — CAISO
published the means to measure this split and the model was carrying an
estimate. It is now **TRUE**, because the session took the measurement rather
than filing a wall. `ASSESSMENT-caiso171` §5.3's own words: *"If **yes**, it is
a rule-14 `[R-ACCURATE]` re-identification … the highest-value CAISO lane
available, and a DOF closure rather than another fitted parameter."* That is
what this is.

The `complete` recommendation is a matter for the owner and this session does
not make it. What it can say factually: the one item caiso-171 left outstanding
is **closed by measurement, not by a wall**, CAISO's ISO-specific residual DOF
count is now **3** (was 4, the highest of any ISO measured), and the
determination is unchanged at CALIBRATED-WITH-CAVEATS with 0 FAILs.

**Newly opened, and named rather than buried:** `MWD-TAC` (§1.1) is a real CAISO
TAC area missing from the committed load series and the weights table. It is
~0.9 % of ISO load on the SP15 side. It is **not** a Path-15 object and does not
bear on this substitution, but it is a genuine demand-input gap and a future
`complete` assessment should account for it.

---

## 7. Files

* pre-registration `results/calibration/PRECHECK-caiso172-path15-load-split-2026-08-04.md`
* survey probe `scripts/probes/_caiso172_subtac_load_survey.py`
* frozen derive `scripts/data/derive_caiso_path15_load_split.py`
* derived artifact `data/raw/zone-specific-demand/CAISO/CAISO_path15_load_split.{csv,json}`
* source snapshots `data/raw/caiso-atlas/{ATL_LDF,ATL_PNODE_MAP}.csv`
* A/B driver `scripts/probes/_caiso172_ab_driver.sh`, scorer `scripts/probes/_caiso172_ab_compare.py`
* attestation generator `scripts/gen_caiso172_attestation.py`
* bundles `results/calibration/caiso172_{control_pge_estimate,measured_path15_split}/`
* matrix row `path15_load_split` (`docs/codebase-site/data/mechanism-matrix.js`)
