# PRECOMMIT — SPP-58: the second, independent shift-factor identification ψ₂ (a topology-derived DC-network PTDF/OTDF)

**Lane** SPP-58 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-58-second-identification-r2nmcx` (stem `claude/spp-58-psi-second-identification-j6tw`) ·
**Data profile** `spp` · **Charter** plan §8 W5 r#9 SPP-58 (`docs/multi-iso/spp-addition-plan-2026-09.md`) ·
**Predecessors** PRECOMMIT-/FINDING-spp-53 (the FCITC rule and the FIRST identification ψ₁),
FINDING-spp-57 §3.3 / §8 R-14 (the double attribution), FINDING-spp-57b §2.2 / §7 R-19–R-20 (the SPS-tie width).
**No solve in this lane — ever.** Every number is zero-LP.

**Pushed before a single PTDF is computed.** Everything below is a construction rule, a data-cleaning rule
with its verifiable outcome, a membership table fixed from names and coordinates, a band, a threshold, or
arithmetic on numbers SPP-53 / SPP-57 / SPP-57b already committed. The DC network was BUILT and its
interconnection cleaning VERIFIED before this push (that is structure, like SPP-53's registry census); the
sensitivities ψ₂ that the network yields were NOT computed, and nothing here is revised after they are.

---

## 0. THE PIN and the preconditions

```
1978eb1a0ab8a8ce72d282039cb17b619d1684be   origin/main at PRECOMMIT time (branch cut from it)
```

| precondition | check | result |
|---|---|---|
| SPP-57b landed (PR #5527) | `git log origin/main --grep=SPP-57b` → `b33ae44d`, `04179a59`; `docs/handoffs/spp57b/` + `tstar_ok_s_57b.csv` in tree | **yes** |
| SPP-53 / SPP-57 instruments and tables in tree | `spp53/tstar_table.csv`, `psi_all.csv`; `spp57/psi_n_ok.csv`, `psi_ok_s.csv` (LOYO ψ columns), `tstar_n_ok.csv`, `tstar_ok_s.csv`, `limits_2026_oklahoma_by_constraint.csv` | **yes** |
| the 2023–25 RTBM roll-ups (for per-year binding hours) | `data/raw/spp-binding-constraints/RTBM-BC-*.csv.zip` (14 zips) | **yes**; parsed once with SPP-53's `parse_2325.py` unchanged → `docs/handoffs/spp58/binding_hours_by_year.csv` |
| a public line dataset for construction (c) | HIFLD *Electric Power Transmission Lines*, ArcGIS feature service `services1.arcgis.com/Hp6G80Pky0om7QvQ/…/Electric_Power_Transmission_Lines/FeatureServer/0` (anonymous HTTPS; layer edit date 2023-09-05, i.e. an **in-window 2023 vintage**) | **reachable**; 17,873 features intersect the box (§2.1) |
| no solve | none launched; `results/` untouched | — |

---

## 1. The three constructions the charter offers, and the one chosen

The charter's instruction is that ψ₂ be identified **without** the hub-spread × shadow-price regression, from
one of three sources. Each was evaluated on the data before this push:

| option | what it needs | finding | verdict |
|---|---|---|---|
| **(a)** the constraint's own binding-hour physics — flow-at-bind against the zonal net interchange | (i) a per-row **flow** on the monitored element; (ii) a **measured** hourly North↔South zonal interchange | (i) the served RTBM schema — 10 columns through 2026-03, 14 from 2026-03-17/04-01 (`Source Limit`, `Real Time Effective Limit`, `Initial Effective Limit`, `Interconnect`) — carries **no flow and no marginal-value column** (README, both landed sidecars re-read: `rtbm_bc_corridor_limits_2026.parquet`, `rtbm_bc_oklahoma_limits_2026.parquet`); at bind the flow equals the limit and carries no slope. (ii) EIA-930 publishes SPP sub-BA **demand** only; no intra-BA interchange series exists, and a constructed North net export would need a modelled wind split — not a measured, price-free quantity | **not available on the data** |
| **(b)** a published SPP shift-factor / PTDF product | any public SPP product with shift factors | the *SPP Markets Public Data Guide v35* (tracked, `data/raw/spp-planning/`) contains **zero** occurrences of "shift", "PTDF", "OTDF" or "distribution factor" across its product list; its flowgate products are the Permanent / Temporary / Archive Temporary Flowgate registries, the M2M flowgate list, "Allocations on SPP Flowgates" and "FFE on M2M Flowgates" — ratings and entitlements, never sensitivities. The ITP Constraint Assessment is NDA/CEII (FINDING-spp-13 §0) | **absent — recorded** |
| **(c)** a topology-derived PTDF from a reduced DC network built from public line data | HIFLD lines + EIA-860 plant coordinates | available (§0); the whole of §2 | **CHOSEN** |

**Why (c) is independent of ψ₁'s channel.** ψ₁ was identified from SPP's *prices* — the RT hub spread and
the constraints' shadow prices, 2023–2025. ψ₂ reads **no price, no shadow price, no binding hour and no
model output**: it is the DC power-flow sensitivity of a branch to a bubble-to-bubble injection pair on a
network whose only inputs are public line geometry, voltage class, standard reactance-per-mile, and plant
coordinates/nameplate. The two identifications share nothing but the *names* of the constituents and the
L_f they are later divided into.

**What (c) is blind to, stated now** (the FINDING re-states each with its measured consequence):

1. **Impedance.** HIFLD carries no reactance; every line takes a voltage-class typical Ω/mi (§2.2) and every
   transformer a class rating at 10 %. PTDFs are invariant to a uniform scaling but sensitive to the
   cross-class ratios; the ratio is dominated by kV² and the transformer assumption is the weakest leg.
   Sensitivity reported (transformer X × 0.5 / × 2).
2. **Coverage.** HIFLD is incomplete: no sub-100 kV feature exists in the box (min 115 kV), several SPS
   345 kV ties and Kansas 115/161 kV stations are absent or unnamed. A constituent whose element or
   terminal cannot be located is **UNRESOLVED** and gets no ψ₂ (§2.6); this is the largest limitation and
   it removes the corridor's dominant constituent (Franklin 161/69) before any number is read.
3. **Contingency.** ψ₁ is implicitly an *outage-transfer* sensitivity (SPP monitors flowgates under their
   contingency); ψ₂ is an OTDF only where every contingent element resolves — otherwise a PTDF, which for a
   corridor element **under**-states the outage sensitivity (the outage diverts flow onto the monitored
   element). Direction of bias: PTDF-only ψ₂ ≤ true OTDF ⇒ T*₂ biased **high** for those rows.
4. **Boundary.** The network is a box, not the Eastern Interconnection; loop paths through MISO / AECI /
   Entergy beyond the box are truncated, which pushes more of the transfer through the corridor ⇒ ψ₂ biased
   **high** for corridor elements. Sensitivity reported (inner box).
5. **Injection distribution.** The LP's transfer is a bubble-to-bubble quantity with no spatial form; ψ₂
   fixes one (§2.4, generator-weighted). ψ₁'s object was the Nebraska-hub → Oklahoma-hub pair (SPP-53
   misalignment iii); a like-for-like hub-pair proxy is computed beside the bubble pair.
6. **Vintage / snapping / ownership.** 2023 HIFLD geometry; 300 m endpoint clustering; owner strings used
   only for interconnection labelling (§2.3), never for impedance.

---

## 2. The construction (c), fixed

### 2.1 Data

- **Lines:** every HIFLD feature intersecting the box lon [−108, −88] × lat [29, 49.5] (SPP's states plus
  the MISO / AECI / Entergy / TVA parallel paths), pulled paginated, byte-identical pages to the scratchpad
  (`spp58/pull_hifld_lines.py`): **17,873 features**, 9 pages, sha256 of the concatenated pages
  `f70786b9d46c789b7445713568f069429a44aeabce3a1b413b26325d7cdbf2ef`, pulled 2026-09-07T16:42Z. The
  reduced node/branch tables are landed under `docs/handoffs/spp58/` (this lane's file ownership; a proper
  `data/raw/hifld-transmission-lines/` intake is routed, not done here).
- **Plants:** EIA-860 operable generators at HEAD (`eia860_generator_operable.parquet`, `Status == OP`,
  nameplate summed per plant) joined to `eia860_plant.parquet` for coordinates, `Balancing Authority Code`
  and `Grid Voltage (kV)`.
- **Registries:** `Flowgates.csv` / `Temp_Flowgate.csv` for each constituent's element string, voltage,
  From/To names and contingent elements (rule 23: read, not edited).
- **Reused verbatim (rule 23):** L_f per constituent from `spp53/tstar_table.csv` and
  `spp57b/tstar_ok_s_57b.csv` / `spp57/tstar_n_ok.csv`; ψ₁ and its LOYO columns from `spp57/psi_n_ok.csv`
  (= SPP-53's regression) and `spp57/psi_ok_s.csv`; nothing is re-fitted, no limit is re-read.

### 2.2 Network rules (`spp58/build_network.py`)

| rule | value | basis |
|---|---|---|
| voltage | `VOLTAGE` where > 0, else the `VOLT_CLASS` midpoint; features < 60 kV, `TYPE` containing "DC", `STATUS` under-construction / proposed / decommissioned dropped | 17,873 → 17,869 kept before labelling (2 DC, 2 under construction) |
| endpoint clustering | union-find over line endpoints within **300 m** (great-circle) | a substation's several line terminations coincide within tens of metres in HIFLD |
| nodes | one node per (cluster, kV) | a substation is one bus per voltage level |
| transformers | one branch between each pair of **consecutive** voltage levels present at a cluster (345–230–161–138–115) | the standard chain; parallel banks cannot be separated |
| line reactance | X_pu = x(kV) · miles / (kV² / 100 MVA), x(kV) Ω/mi: 69 → 0.80, 115 → 0.78, 138 → 0.75, 161 → 0.73, 230 → 0.70, 345 → 0.58, 500 → 0.53, 765 → 0.50 | typical 60 Hz ACSR series reactance — single conductor ≤ 230 kV, bundled ≥ 345 kV (order 0.5–0.8 Ω/mi in every standard reference; the PTDF depends on the *ratios*) |
| transformer reactance | 10 % on an assumed rating by high-side class: 765 → 1,500 MVA, 500 → 1,000, 345 → 500, 230 → 300, 161/138 → 150, 115 → 100, 69 → 50 | the 7–12 % impedance range of power transformers; the assumed ratings are the declared weak leg, swept ×0.5 / ×2 |
| registry-completed branches | three SPS 345 kV ties named in `Flowgates.csv` whose BOTH terminals exist in HIFLD but whose feature is absent: Border–Tuco 345, Beaver County–Hitchland 345 ×2; length = great-circle × 1.15 | rule 14: SPP's own registry completes the public geometry; each is listed in the FINDING |

### 2.3 Interconnection cleaning — a declared rule with a verifiable outcome

The box spans three asynchronous systems. A line is labelled **ERCOT** / **WEST** / **EAST** before any node
is built (so no ERCOT or Western line can share a node with an Eastern one):

- **by OWNER** where the owner is a known ERCOT utility (Oncor, CenterPoint, AEP Texas, TNMP, LCRA, the
  central/south-Texas coops and municipals — the full list in `build_network.py`) or a known Western one
  (PNM, EPE, Tri-State, Xcel-Colorado, Black Hills, WAPA, the NM/CO coops);
- **by geography** otherwise: WEST = NM west of −105.0°, CO (37–41°) west of −102.05°, 41–46° west of
  −103.0°, ≥ 46° west of −105.5°; in Texas south of the Oklahoma line, EAST = the SPS Panhandle / South
  Plains (lat ≥ 33.4 & lon ≤ −100.0; 32.0 ≤ lat < 33.4 & lon ≤ −101.9), north-east Texas (lat ≥ 31.9 &
  lon ≥ −95.0) and Entergy Texas (29.9–31.9° & lon ≥ −95.65 with lon ≥ −95.0 or lat ≥ 30.25), else ERCOT;
- **ERCOT's Panhandle CREZ network** (Tule Canyon, Alibates, Gray, Tesla, Cross, Windmill, Ogallala,
  White River, Railhead, AJ Swope, Jack Ramey, David Swinford, Cottonwood, Spinning Spur II/III and the
  CREZ wind stations) carries SPS / coop owner strings in HIFLD and joins SPS through a drawn Spinning
  Spur I–II feature: every line touching a listed station inside the Panhandle box is dropped;
- **East–West ties** (Eddy, Blackwater, Lamar, Stegall, Virginia Smith, Rapid City, Miles City): the
  west-side line at the station is cut; the SPP–ERCOT back-to-back stations (Oklaunion, Welsh) are handled
  by the owner label alone, so SPP's own Oklaunion–Tuco 345 kV survives;
- **two manual transformer cuts** at the Martin Lake and Tenaska Gateway clusters (ERCOT plant sites in the
  NE-Texas ERCOT/SWEPCO interleave whose 345 kV features carry SWEPCO / Upshur owner strings and end within
  the snap radius of a SWEPCO 138 kV bus; the min-cut to SPP is that transformer).

**The verification, stated as the precondition it is** (computed before this push, on the built network):
the component holding SWPP's plants carries **91,200 of 102,447 MW** of SWPP nameplate (9,895 MW unsnapped,
> 15 km from any node); of ERCOT-coded plants snapped within 3 km, only **Kiamichi (1,370 MW, OK) and
Denison Dam (104 MW)** remain — both physically SPP-connected (Pittsburg 345 kV; the SWPA 138 kV), i.e.
EIA-860 code exceptions, not junctions; **zero** PNM / EPE / PSCO nameplate and 232 MW of WACM-coded ND/SD
units (Eastern-side pockets). K1 (§5) is therefore met; the FINDING repeats these numbers.

### 2.4 Transfer pairs (source → sink), generator-weighted by EIA-860 nameplate, SWPP plants snapped to
the network (nearest node ≤ 15 km, preferring a node at the plant's reported grid voltage)

| id | source (inject +1 MW total) | sink (withdraw) | what it is |
|---|---|---|---|
| **P-NS** | every SWPP plant in **SPP-North** (state map `_SPP_STATE_ZONES`, 45,538 MW snapped) | every SWPP plant in **SPP-South** (OK + TX + NM + AR + LA, 45,662 MW) | the registered two-zone link's own object — an LP transfer is North generation up, South generation down |
| **P-NOK** | SPP-North | Oklahoma-state plants (30,483 MW) | SPP-57b's N↔OK object |
| **P-SS** | SPP-South plants NOT in the SPS geography (OK, AR, LA, east Texas: 36,783 MW) | the SPS geography (NM; TX lat ≥ 33.4 & lon ≤ −100.0; 32.0 ≤ lat < 33.4 & lon ≤ −101.9: 8,879 MW) | SPP-54's South↔SPS link; the OK→S direction SPP-57b named |
| **H-NEOK** | Nebraska plants (10,000 MW) | Oklahoma plants | the like-for-like proxy for ψ₁'s Nebraska-hub → Oklahoma-hub object |

Generator-weighted on both sides because that is what an LP transfer *is* (loads are fixed in the LP); a
load-weighted sink is not computable from public data. A wind-only-source / gas-only-sink variant is
reported for P-NS as a sensitivity, never chosen.

### 2.5 ψ₂ — definition, sign, contingency, identification floor

- **ψ₂ = the DC PTDF** of the monitored branch for the transfer pair: solve B·θ = p once per pair on the
  SPP component (`scipy.sparse.linalg`, slack = the largest-nameplate SWPP node), flow = (θ_i − θ_j)/x.
- **OTDF where the contingency resolves:** ψ₂ is re-computed on the **post-contingency network** (the
  contingent branch(es) removed) — exact in DC and handling multi-element contingencies. A generator
  contingency changes no topology (OTDF ≡ PTDF). Where any contingent element is UNRESOLVED the PTDF is
  reported and the row flagged "contingency not modelled" (blind spot 3).
- **Sign:** lines are oriented registry **From → To** (the FROM terminal's coordinates are in
  `element_map.csv`); transformers **high → low**. ψ₂ > 0 = the transfer loads the element in that
  direction. ψ₁'s sign convention is "binding raises the *sink-side* price"; the two agree on a line
  whose registry orientation is the monitored direction, and the FINDING reports sign agreement as a
  statistic, on |ψ| for transformers where the registry states no direction.
- **Interface flowgates** (`SPPSPSTIES`, `SPSNMTIES`): ψ₂ = Σ over the *present* elements (the registry
  lists them); coverage is 6 / 9 and 2 / 10 (§2.6), so these are **lower bounds** and are reported beside
  the cut-set identity check (Σ PTDF over every branch crossing the OK-side / SPS-side node partition = 1
  for P-SS by conservation — a check of the network, not an input).
- **Identified under ψ₂** iff **ψ₂ ≥ +0.005** in the monitored direction (loaded by the transfer);
  **reverse-loaded** iff ψ₂ ≤ −0.005; else "not loaded". The floor: a 100 MW element with ψ < 0.005 needs a
  > 20 GW transfer to load it — below SPP-53's own smallest identified ψ₁ (0.0075) and near B_plaus — so it
  is not a corridor element at any admissible transfer. There is no t-statistic in a topology PTDF; the
  floor is the whole screen.

### 2.6 The element join (fixed before any PTDF; `docs/handoffs/spp58/element_map.csv`)

Rule, in order: (1) both terminal names present in HIFLD `SUB_1`/`SUB_2` at the element's voltage →
class **A**; (2) one terminal named or a contingency-corroborated geography (the registry's contingent
line locates the station, or the town's coordinates and voltage single out one feature) → class **B**
(**B-** where a second feature is arguable); (3) transformers: the cluster carries both levels → **A**; two
clusters within 15 km that the contingency evidence identifies as one station → **B**, declared "manual
co-location"; (4) otherwise **U**, unresolved — no ψ₂, reported with the reason. Applied to every
constituent the charter names, the outcome, fixed now:

| set | constituents | A | B / B- | U (why) |
|---|---|---:|---:|---|
| `n_s_corridor` ψ₁-identified N→S (12) | Franklin xfmr, EDWV xfmr, Nashua xfmr, First Creek–Roanridge, Cooper–St Joe, Marshall–Knob, LEC–LAWH, Sibley ×2, Mullergren–Ellsworth, Hawthorn xfmr, Seward–St John | 5 | 3 | **4 — Franklin** (no 69 kV feature exists in the box: the low side has no path), Nashua (no 345 kV bus at the Nashua cluster), First Creek–Roanridge and Mullergren–Ellsworth (unnamed / broken chain) |
| ψ₁-identified S→N (8) | Viola xfmr, Waverly–LaCygne, Stilwell–Redel, Overland Park–Merriam, Spearville–Mullergren, LaCygne–Stilwell, Coli–Tech, Craig–Lenexa | 3 | 2 | 3 (Redel, Merriam, Coli–Tech unlocatable) |
| not ψ₁-identified (10) | Smoky Hill–Summit ×4, Gordon–Maize, Shays–Mullergren, Jayhawk–Franklin ×2, Colby–Atwood, N345–Blackberry | 0 | 8 | 2 |
| `sps_tie` (7) | Potter County xfmr ×4 names, `SPPSPSTIES`, `SPSNMTIES`, FPL Switch–Woodward | 4 (+2 partial interfaces) | 1 | 0 |
| `oklahoma_internal` (re-examination only) | Cimarron xfmr, Gracemont–Anadarko ×2, Woodward, Cornville–Naples, Osage–Webber, Russett–S Brown ×2, Crescent–Cottonwood, Kinzie, Cleveland–Clev_AEC, Stonewall–Tupelo | 1 | 2 | 9 |

**Consequence declared now:** the corridor's dominant constituent (Franklin, 4,103 of the identified set's
9,254 pooled hours, 44 %) cannot receive a ψ₂ from this network. So the comparison is made on two objects
(§3), and the FINDING says which one each verdict rests on.

---

## 3. The sets (unchanged) and what is computed on each

Sets are SPP-53's / SPP-57b's, verbatim: `n_s_corridor` (30 constituents ≥ 263 pooled hours, `groups.py`
unchanged), `sps_tie` (the 7), `oklahoma_internal` (re-examined, never rated). L_f per constituent is
SPP-53's / SPP-57b's committed value (no re-read).

**Aggregation = SPP-53 §2.1 verbatim:** T*_f = L_f / ψ_f; the link TTC is the binding-hours-weighted
(2023–25 pooled) MEDIAN of T*_f over the identified constituents, rounded to the nearest 100 MW.

| object | ψ₂ pair | what is reported |
|---|---|---|
| **N→S corridor, "all-ψ₂"** | P-NS | T*₂ over every corridor constituent that is ψ₂-identified (any of the 30 that resolve), weighted by pooled hours — the charter's T*₂ |
| **N→S corridor, like-for-like** | P-NS | on S₂ = {ψ₁-identified N→S} ∩ {resolved}: T*₁(S₂) (SPP-53's rule re-run on the subset) and T*₂(S₂) — the identification test proper, free of the set difference |
| **N→S per constituent** | P-NS and H-NEOK | ψ₁ vs ψ₂ (both pairs) per constituent, sign agreement, ratio ψ₂/ψ₁ |
| **S→N reading (4,206)** | P-NS (reverse-loaded, ψ₂ ≤ −0.005) | the same two objects for the S→N set |
| **N↔OK (SPP-57b's object)** | P-NOK | the same corridor ψ₂ under the Oklahoma sink — reported, no band (SPP-57b did not land) |
| **`sps_tie`** | P-SS | ψ₂ per constituent; T*₂ over the ψ₂-identified `sps_tie` set; the **Potter County width**: ψ₂(TEMP50, OTDF with Border–Tuco out) vs ψ₂(TMP555, PTDF) |
| **double attribution** | P-NOK and P-SS | ψ₂ on both pairs for the resolved `oklahoma_internal` constituents (Cimarron xfmr, Woodward, Cornville–Naples) beside ψ₁'s two coefficients |

**LOYO (charter item 4).** A topology PTDF has no year — ψ₂ is year-invariant by construction and that is
said rather than hidden. The LOYO spread of every T*₂ is therefore the **re-weighting** spread: the same
constituents' T*₂ re-aggregated with pooled-minus-one binding hours (`binding_hours_by_year.csv`), drop
2023 / 2024 / 2025 — exactly the year-dependence SPP-53's rule carries through its weights. Beside it, the
FINDING re-prints ψ₁'s own LOYO (from `psi_n_ok.csv` / `psi_ok_s.csv`) so the reader sees which of the two
identifications moves when a year is dropped.

---

## 4. THE DISAGREEMENT BAND and the verdict rules — declared now

**Band = a factor of 1.92, log-symmetric:** a T*₂ CONFIRMS the standing number T*₁ iff
`|ln(T*₂ / T*₁)| ≤ ln 1.92`, i.e. T*₂ ∈ [T*₁ / 1.92, T*₁ × 1.92]. Multiplicative because T* is a ratio
(L / ψ) whose error is multiplicative in ψ.

**Justification from SPP-53's own record (FINDING-spp-53 §4):** 1.92 is the weighted p75 / p25 ratio of
the first identification's own constituents (3,355 / 6,437) — the width within which SPP-53's construction
does not distinguish its constituents from one another. Its leave-one-year-out folds sit at **3,681 (+8 %)
and 2,645 (−22 %)**, both inside that factor, and **11,121 (+227 %)**, outside it — the fold SPP-53 itself
attributed to Franklin's ψ being carried by 2024. A second identification landing inside the factor is
indistinguishable from the first at the first's own resolution; one landing near the outlying fold is not.
The band is set at the construction's self-consistency width, not at its widest fold, precisely because the
widest fold is what ψ₂ exists to adjudicate. (A tighter band would make confirmation unattainable by any
method carrying blind spots 1–4; a band admitting the +227 % fold would be vacuous.)

| comparison | standing T*₁ | verdict rule |
|---|---:|---|
| N→S link | **3,400** (`_spp_config`) | inside the band → **3,400 STANDS, `ttc_mw` untouched, finding = confirmation**; outside → **`ttc_mw` untouched, STOP, the desk is served a card with both identifications side by side** (charter item 3). Applied to the **like-for-like** object first (the identification test) and to the all-ψ₂ object second; where the two disagree the FINDING says so and the card is served |
| S→N reading | **4,206** | same rule |
| `sps_tie` | **10,705** (SPP-57b's weighted median, OK→S-named) | same rule on T*₂ over the ψ₂-identified `sps_tie` set |

**The Potter County width verdict** (one transformer, two names, ψ₁ 0.047 vs 0.132 → T* 10,705 vs 3,850):
ψ₂ yields ONE PTDF for the transformer plus an OTDF under TEMP50's Border–Tuco contingency. Declared:

- **COLLAPSED** (the width is ψ₁'s artifact) iff ψ₂(TEMP50, OTDF) / ψ₂(TMP555, PTDF) ≤ **1.5**;
- **REAL** (the two names are physically different sensitivities) iff the ratio ≥ **2.0** AND its direction
  matches ψ₁'s (TMP555 > TEMP50, i.e. the ratio < 0.5 in this orientation);
- otherwise **INDETERMINATE** (reported with the number; no verdict).

Ex-ante expectation, written so it can be wrong: a *line*-contingency OTDF on a tie-path element should
exceed its PTDF (the outage diverts flow onto it), so ψ₂(TEMP50) ≥ ψ₂(TMP555) — the OPPOSITE ordering of
ψ₁. If that is what ψ₂ says, the 2.8× width is not a property of the transformer but of the price channel,
and SPP-54 should not read the two names as two ratings.

**The double-attribution re-examination** (SPP-57 R-14): a resolved `oklahoma_internal` constituent is
**LOCAL under ψ₂** iff |ψ₂| < 0.005 on BOTH P-NOK and P-SS (loaded by neither bubble transfer — the
intra-pocket delivery element SPP-57b's exclusion rule assumed), **DOUBLE-ATTRIBUTED under ψ₂** iff
|ψ₂| ≥ 0.005 on both, **single-link** otherwise. This re-examines the exclusion; it re-rates nothing.

**What SPP-54 may use** is stated in one line in the FINDING and is fixed now to be exactly: the
`sps_tie` T*₂ over the ψ₂-identified set under P-SS, with its LOYO re-weighting spread, IF K1–K3 hold and
the `sps_tie` band verdict is stated — never a number picked from the Potter County pair.

---

## 5. STOP conditions for the construction (a miss kills it; it never adjusts it)

| id | condition | consequence |
|---|---|---|
| K1 | the SPP component holds < 90 % of snapped SWPP nameplate, or any ERCOT/WECC-coded plant ≥ 300 MW snapped ≤ 3 km lies in it other than the two EIA-code exceptions named in §2.3 | network FAILS; ψ₂ not computed |
| K2 | fewer than **3** ψ₁-identified N→S constituents resolve (§2.6 fixes 8 — met by construction, stated for the record) | like-for-like test FAILS |
| K3 | the cut-set identity fails: Σ PTDF over every branch crossing the North/South node partition for P-NS differs from 1.0 by > 1e-6 (a code defect), or the P-SS crossing sum likewise | ψ₂ not reported until fixed; the fix is a code fix, never a parameter |
| K4 | sign agreement between ψ₁ and ψ₂ over resolved *line* constituents (registry orientation) below **50 %** | the construction is reported as NOT identifying the same object; no band verdict is issued, the card is served with that finding |

Nothing is a rejection condition on the basis of where T*₂ lands relative to 3,400 — that is the verdict,
not a gate.

---

## 6. Ex-ante expectations (not gates; written so they can be wrong)

1. Small under-lay elements (115 kV lines, 161/69 and 115/161 transformers) will carry **ψ₂ < ψ₁**: a
   price regression on 133 correlated regressors loads whatever spread coincides with a small element's
   binding onto its coefficient; a DC network gives a 115 kV parallel path a few tenths of a percent of a
   bubble transfer. Expect T*₂ > T*₁ for those rows and T*₂ for the like-for-like set to sit **above** T*₁.
2. The 345 kV corridor elements (Cooper–St Joe, LaCygne–Stilwell, Waverly–LaCygne) will carry ψ₂ of the
   same order as ψ₁ (0.05–0.2).
3. Potter County: ψ₂(TEMP50 OTDF) ≥ ψ₂(TMP555 PTDF) — the reverse of ψ₁ (§4).
4. The resolved `oklahoma_internal` elements (Cimarron 345/138, Woodward 138) will read LOCAL or
   single-link, not double-attributed, under bubble-to-bubble pairs.
5. Sign agreement on lines ≥ 70 %.

## 7. Deliverables and files

| file | change |
|---|---|
| `docs/handoffs/spp58/` | `pull_hifld_lines.py`, `build_network.py`, `query_lines.py`, `element_map.csv`, `binding_hours_by_year.csv` (this push); then `ptdf.py`, `aggregate_ttc_58.py`, `nodes.csv` / `branches.csv` / `plants.csv` (reduced network), `psi2_by_constituent.csv`, `tstar_58.csv`, the logs |
| `docs/handoffs/PRECOMMIT-spp-58-2026-09-07.md` (this file), `FINDING-spp-58-2026-09-07.md` | the record |
| `docs/multi-iso/spp-addition-plan-2026-09.md` §5 SPP-58 row → LANDED; `docs/handoffs/spp-desk-ledger-2026-09.md` row; `docs/calibration-log/spp.md` spp-9 | the record |
| `docs/codebase-site/data/mechanism-matrix/SPP.js` `measured_interface_limits` | evidence text appended; **cell stays O** |
| `src/market_sim/config/iso_configs.py` `_ns_corridor_ttc` | **ONLY under the band rule of §4 — and the rule as declared never edits it** (inside the band it stands; outside it stops). No edit is expected from this lane |

Not touched: any other ISO's files; `ScenarioConfig`; any keeper, sidecar or shard cell verdict; the
SPP-57 / SPP-57b price-regression instruments (read only); `data/raw/spp-binding-constraints/` (no new
column is needed — the sidecars already carry everything ψ₂ divides into). No solve, no CI workflow.
