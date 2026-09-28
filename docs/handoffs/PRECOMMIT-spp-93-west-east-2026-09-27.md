# PRECOMMIT — SPP-93: a West/East re-partition of the SPP seam (replaces N↔S; rule 19)

**Lane** SPP-93 · **Date** 2026-09-27 · **Data profile** `spp` · **Pin** `origin/main` = `baaa3656`
(SPP-92 merged at `8b131950`, an ancestor) · **Keeper / control** `2026-09-26-spp-86-coal-extract`,
bundle `results/calibration/spp86_arm_span`, basis_sha `d72e5f107a6fe7ca59f94307f37b239e1a48c14f`
(rule 29(b) form 4). **Charter**: owner decision card on SPP-92, "West/East re-partition (Recommended)".

**Written and pushed BEFORE** any model output under the new partition exists: no fleet_only census,
no wind-shape rebuild, no ψ fit on the new spread, no LP. What was read before writing it is listed in
§0 and is registry/measured data only. Nothing below is re-cut after a number is read (rules 1, 23).

---

## 0. What was read before this was written (measured / registry data only)

| read | what it gave | used for |
|---|---|---|
| SPP-92 FINDING §2, §4 and `spp92/_spp92_bubble_spread.json` | annual mean RT LMP by sub-BA area, 2019–25 (SPP-92's committed record) | the motivation; the §1.4 admissibility test is re-computed hourly after this is pushed |
| `data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv`, `RESZONE` × `NODE_AREA` for current-effective (`TERMINATIONDATE` 2999) `LOAD` settlement locations | §1.2 table | the load rule |
| same file, current-effective `RES` settlement locations by area | SECI 58 of 60 in RZ 2; WR 90 in RZ 4 / 20 in RZ 2 (Flat Ridge, Colby, Goodman, Buckeye, Kingman-area); SPS all in RZ 2/3; OKGE / WFEC all RZ 4 | why the plant rule cannot be a state or ownership map (§1.3) |
| EIA-860 `eia860_generator_operable.parquet` field `RTO/ISO LMP Node Designation`, BA `SWPP` | 530 of 1,646 SWPP generators (47.3 % of nameplate) carry a node; 93.3 % of that MW matches an SPP registry key under §1.3's normalisation | the plant rule's coverage, stated ex ante |

No sidecar, run payload, keeper hourly or LP artifact was opened for the new partition.

---

## 1. The partition rule (primary candidate **P-WE**)

### 1.1 The physical cut: SPP's own reserve zones

SPP's market registry assigns every settlement location a **reserve zone** (`RESZONE` 1–5; 21 = WEIS,
outside the EIA-930 `SWPP` footprint). Reserve zones are SPP's own partition of the footprint along
the transmission limits that constrain reserve deployment, and SPP clears a separate MCP per zone
(`data/raw/spp-or-mcp`). That makes them a published physical cut, not a modeller's line.

**P-WE:** **West = RZ {1, 2, 3, 5}**: Nebraska (1), western Kansas and the northern Panhandle (2), the
SPS south / New Mexico (3), and the Dakotas / WAUE (5). **East = RZ 4**, the Kansas City–Wichita–Oklahoma–
Arkansas–Louisiana core.

### 1.2 Load side (sub-BA → bubble)

A sub-BA goes to the bubble of the reserve zone holding the **majority of its current-effective LOAD
settlement locations**. There are no ties. The result, fixed now:

| sub-BA | LOAD SLs by RZ | bubble |
|---|---|---|
| LES | RZ1 2 | West |
| NPPD | RZ1 17 | West |
| OPPD | RZ1 10 | West |
| SECI | RZ2 6 | West |
| SPS | RZ3 3, RZ2 1 | West |
| WAUE | RZ5 28 | West |
| CSWS, EDE, GRDA, INDN, KACY, KCPL, MPS, OKGE, SPRM, WFEC | RZ4 only | East |
| WR | RZ4 16, RZ2 2 | East |

Hourly zonal demand = the sum of the member sub-BAs' EIA-930 series, through the same curation path
as the keeper's N/S shares (`scripts/data/curate_zonal_shares.py`). Only the grouping changes.

### 1.3 Plant side (generator → reserve zone → bubble)

Neither a state map nor the transmission-owner field follows the cut: Kansas and Texas straddle it, and
WR-owned resources sit in both RZ 2 and RZ 4. The rule, in order:

1. **Node.** Read the generator's EIA-860 `RTO/ISO LMP Node Designation` and normalise it
   (upper-case, alphanumerics only, a trailing `_RA` stripped). Match it against every
   `SETLOCNAME` / `PARENTPNODE` / `CHILDPNODE` / `ENODE` of the non-External registry rows under the
   same normalisation: an exact match first, else a ≥ 8-character prefix match in either direction.
   The generator's RZ set is the union over its matches.
2. A plant's bubble is the **capacity-majority bubble over its matched generators**. An RZ set that
   spans both bubbles (e.g. {1, 4}) resolves through the matched `NODE_AREA` under §1.2.
3. **No node, or no match:** **1-nearest-neighbour** (haversine on EIA-860 plant coordinates) among the
   plants labelled in steps 1–2. This has no parameter.
4. Plants absent from the HEAD plant file (older vintages) take step 3 on their own vintage's
   coordinates. A plant with no coordinates is a hard error, never a default.

The labelled set and every plant's assignment and source (`node` / `1nn`) are written to a committed
CSV, so the rule regenerates for any vintage (rule 13's forward test).

### 1.4 Measured-price admissibility (ACTUAL prices only; never model output)

This uses SPP-92's route: RTBM LMP at all 112 LOAD SLs, area = mean over its load SLs, bubble =
EIA-930 sub-BA-energy-weighted, clock GMT HE − 7 h. P-WE is admissible only if **both** hold:

- **A1.** The annual mean of (East − West) is **> 0 in every year 2019–2025**, i.e. West is the cheap side.
- **A2.** The mean |East − West| is **greater than** the mean |South − North| on the same weights in
  **≥ 5 of 7 years**, i.e. the new cut separates more than the cut it replaces.

A miss on either is a **STOP**: the physical cut does not carry the price divide, and the partition is
not re-drawn to make it pass.

Stated in advance, not gated: SPS reads dear in 2025 (36.52 vs OKGE 35.26). The reserve-zone rule
still places it West, and that misalignment is reported, not fixed.

### 1.5 Other candidates, stated and not taken

| candidate | partition | links | why it is not taken |
|---|---|---|---|
| **P3** | NW = RZ {1, 5}; SW = RZ {2, 3}; E = RZ 4 | NW↔E, SW↔E, NW↔SW (west Kansas–Nebraska 345 kV ties exist) | Three ratings, each needing its own identified construction. The triangle is a loop, and a transport LP routes a loop by cost, not impedance: a known misrepresentation of parallel flow that this model has no PTDF layer to correct. |
| **P5** | one bubble per RZ | ≥ 5 | the same issue, compounded; RZ 5 and RZ 1 are small |
| **N/S + SPS pocket** | SPP-54 | 2 | already designed (`8d427adc`); it is the South half of a West/East split and leaves the North's east/west mix in place (SPP-92 §6) |

P-WE is the only candidate this lane censuses as a candidate, rates or solves. P3's measured bubble
spreads (§1.4 arithmetic) and a P3 census row are **reported for information only** and select nothing.

---

## 2. The link and its rating

- **One link West↔East. It REPLACES the N↔S link (3,400 MW) and is never stacked on it** (rule 19).
  It is symmetric, as SPP-20 registered N↔S: SPP-92 measured the spread reversing sign.
- **Rating rule: SPP-53's construction (A), the FCITC reading, on the new bubble-pair spread.**
  - Take SPP-92's `_spp92_psi_repair.py` mechanics verbatim: 2023–25, GMT clock, hourly regressors =
    the mean |shadow| of every constraint with ≥ 263 binding hours, OLS with HC1.
  - The spread is the ACTUAL East-bubble − West-bubble price.
  - **Constituent set** = SPP-14 groups `n_s_corridor` ∪ `sps_tie` (the two groups whose areas straddle
    the W/E cut). `oklahoma_internal` is wholly East and `other` is WEIS, so both are excluded.
  - **Identified** = ψ > 0, t ≥ 2, ψ ≤ 1.
  - L_f is looked up in SPP-53's order (archive by name ≥ 100 binds → by element → registry) over the
    union of SPP-53's `limits_2026_by_constraint.csv` + `registry_xcheck.csv` and SPP-57's
    `limits_2026_oklahoma_by_constraint.csv`. A constituent with no L_f is dropped and counted.
  - T*_f = L_f / ψ_f. **TTC = the binding-hours-weighted median, rounded to the nearest 100 MW.**
- **Rejection conditions** (a miss is a STOP, never an adjustment):
  - **R1**: fewer than 3 identified constituents carry an L_f.
  - **R2**: TTC ≥ B_plaus.
  - **R3**: TTC ≥ B_hard.
  - **R4**: hours-weighted p75/p25 > 10.
- **The bounds**, from the census (§3), before the ψ fit is read:
  - **B_plaus** = West non-gas capability (wind + coal + nuclear + hydro) − West minimum hourly load.
  - **B_hard** = West total capability − West minimum hourly load.
  - Both use SPP-53's convention on the 2023 fleet and load. West is the exporter by §1.4.
- **ψ₂ cross-check (not a gate):** SPP-58's `ptdf.py` with the P-WE generator-weighted West→East
  transfer, on the same identified constituents. Reported beside ψ₁. The band verdict is informational,
  as in SPP-58; ψ₁ governs.
- **Rule-14 misalignment**, carried into the citation comment:
  1. 2026 limits applied to 2019–25.
  2. An element-under-contingency rating is not a corridor capability.
  3. ψ is identified on 2023–25 and applied to 2019–22.
  4. The group superset relies on the ψ screen to drop East-internal Kansas elements.

---

## 3. The zero-LP census (after this is pushed)

`run_year(fleet_only=True)` on the keeper's recipe (`run_config_<y>.json`), 2019–2025, with plants
remapped under §1.3. Per bubble and year:

- plants and LP units;
- thermal + hydro MW by class;
- wind MW and potential TWh;
- solar MW and TWh;
- demand TWh (min–max MW);
- net position = annual (thermal availability-weighted + wind + solar potential) − demand, reported
  and not gated;
- B_plaus / B_hard.

Every SWPP plant must resolve to exactly one bubble; any plant that does not is a **STOP**. The census
also reports the plant-rule coverage (node vs 1-NN, by MW and by class) and a P3 split row for information.

---

## 4. The STOP legs

### 4.1 Pre-solve (this session, zero LP): any miss stops the lane before a shard is launched

| leg | test |
|---|---|
| A1, A2 | §1.4 |
| R1–R4 | §2 |
| C-0 | census completeness (§3) |
| **C-1 / C-2** (SPP-54's R-18 wind reconciliation, under SPP-48's R-LEVEL builder) | Σ_z cap·cf = M(t) to ≤ 1e-9 relative in every hour of every year 2019–25; no cf > 1; no lost overflow |
| **C-3** (the SPP-54 h8509 test, generalised) | For every hour of 2019–2025, compute each bubble's **availability-net margin** from the keeper's own inputs: thermal + hydro available (the keeper's availability arrays) + wind potential + solar potential + the link rating as import − demand. **STOP** iff any hour has min over W/E bubbles < 0 while min over the keeper's N/S bubbles ≥ 0 (N/S at 3,400 MW). Hours where the keeper's own LP already served slack are exempt. The Dec-21-2025 window (h8496–8519) is tabled explicitly, whatever the result. |

### 4.2 Post-solve (the shards; graded by the parent)

| leg | test |
|---|---|
| L1 | the W↔E link is at bound in ≥ 5 % of hours in the measured-dominant direction (W→E), every year |
| L2 | the model's annual mean (E − W) has the sign of the actual's, every year |
| L3 | unserved hours ⊆ the keeper's unserved hours, every year |
| L4 | every fuel family's TWh within [0.1×, 10×] of reference (SPP-54 (v)) |

A miss on L1–L4 is recorded: the design **fails** and is not re-cut. Scoring (`calibration_verdict.py`)
is reported at full magnitude for **2023–25 first**:

- A train-tier criterion that PASSES in the keeper and FAILS under P-WE is stated plainly.
- The promotion question goes to the owner (rules 1, 31). It is never answered by re-cutting the
  partition, re-rating the link or moving the 0.93 multipliers (rule 1(c)).

---

## 5. How it lands (only if every pre-solve leg passes)

- **A new `ScenarioConfig` field `spp_zone_partition`**, values `"north_south"` (default; the keeper's
  topology, byte-identical) and `"west_east"`.
  - Cache key: the frozen default is dropped, so every existing key is unchanged.
  - A matrix row plus a cell line in **every** ISO shard (rule 28(c)).
  - No other field. No offer, floor or adder is touched.
- **G-DRIFT** against `d72e5f10` (rule 29(b) form 4), recorded before any shard.
- **One shard per year, 2019–2025** (rule 36).
  - Each is pinned to a full 40-char SHA and pushes its full bundle, including
    `dispatch/<y>_P1.parquet`, via a `.gitignore` negation plus a plain `git add` (rule 34(a)).
  - Each prompt carries the full rule-32(c) checklist.
- **Parent:**
  1. compose (`_rspp_compose.py`);
  2. attest (after `gen_spp86_attestation.py`);
  3. `build_dof_ledger --check`;
  4. register with `--no-prune`;
  5. score;
  6. land the bundle on `main` before the PR merges (33(f)).
- **DOF:**
  - The partition is a registry rule with zero tuned scalars.
  - 1-NN has no parameter.
  - The TTC is a measured construction.
  - Nothing is ledgered as free beyond the keeper's existing entries.

## 6. Out of scope (the charter's list, restated)

Re-rating the existing N↔S link; ramp limits; coal availability/derate/outage re-derivation; reserve
headroom; the < $30 gas commitment gap; gas-price levers; the 2022 coal markup; the 0.93 multipliers;
other ISOs.
