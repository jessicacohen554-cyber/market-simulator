# DESIGN PRECOMMIT closeout-CAISO-w5: the CAISO intra-gas ordering (2026-10-05)

**Status: design for an owner ruling. Nothing is built and nothing is solved.** Desk instruction, 2026-10-04: draft
the rule-17 design (window, driver, forward story, one-mechanism check against `caiso_ra_mustoffer`, forced-energy
budget estimate) with its zero-LP reach, and do not build until the owner rules.

**Evidence.**
- Phase 0: `FINDING-closeout-caiso-w5-phase0-2026-10-04.md`.
- Probes (all zero LP):
  - `_closeout_caiso_w5_intragas_census.py`;
  - `_closeout_caiso_w5_peaker_price_test.py` (including the run-block and block-length splits);
  - `_closeout_caiso_w5_fleet_hr.py`.
- External data:
  - CAISO DMM Annual Reports on Market Issues and Performance 2019–2025
    (`caiso.com/documents/<…>annual-report-on-market-issues-and-performance<…>.pdf`; SHA-256 in §6);
  - EPA CAMD–EIA crosswalk of record, already committed at
    `data/raw/reference/camd-eia-crosswalk/epa_eia_crosswalk.csv`.

**Control.** w3 probe `2026-10-04-closeout-caiso-w3-own`.

## 1. What the measured data says the object is

The phase-0 FINDING proposed a single local-commitment floor, sized from DMM exceptional-dispatch (ED) and
minimum-online volumes. **The DMM data refutes that framing:**

| DMM (CAISO BA), 2019 → 2025 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|--:|--:|
| ED energy, all types, % of load | 0.70 | 0.50 | 0.50 | 0.25 | 0.26 | 0.34 | 0.41 |
| ≈ TWh (× ~215 TWh) | 1.5 | 1.1 | 1.1 | 0.5 | 0.6 | 0.7 | 0.9 |
| ED min-load commitment share | 60 % | | | | 77 % | | |
| RUC min-load capacity, MW | 144 | 270 | 216 | 218 | 500 | 240 | 280 |
| … of which long-start (≥ 5 h start, the only part RUC commits online) | 9 % | | 17 % | 14 % | 22 % | | |

**What DMM does and does not support.**
- DMM publishes these by reason and quarter only: nothing by area, unit or class.
- RUC commits only long-start units (CC and steam), never peakers.
- So measured out-of-market peaker commitment is bounded by ED, under about 1 TWh in every year and not split by
  class. A per-area floor sized from DMM would need an allocation rule DMM does not publish, which is a fitted choice.

**The plant-level decomposition** of the "neither market clears" energy (`_peaker_price_test.json`) shows four objects.
Each has its own admissible fix:

| # | Object | 2020 gap (TWh, actual − model) | Years live | Nature |
|---|---|--:|---|---|
| O1 | **Carlsbad Energy Center (EIA 59002, 527.5 MW, 5 × LMS100)** files CEMS under CAMD 302 units 6–10 (legacy Encina ORIS). `CAMPD_UNIT_PLANT_REMAP` lacks the rows, so the plant gets no measured CT heat rate, no CEMS outages and a flat benchmark shape. caiso-146 recorded it as "does not report to CAMPD at all"; **the EPA crosswalk of record says otherwise (new evidence, rule 28).** Same defect at King City Peaking (10294 unit 2 → EIA 55811, small). | 0.32 (Carlsbad) | 2019–25 | data correction (rule 14) |
| O2 | **Industrial self-generators labelled CT_PEAKER:** THUMS (56051, 57 MW, CF 0.71, "Industrial Non-CHP") and New-Indy Ontario Mill (10427, CHPFLAG = Yes; EIA-923 class CT_CHP in 2019, CT_PEAKER from 2020). Host-driven baseload priced as peakers. | 0.61 | 2019–25 | classification (measured EIA-860/eGRID sector and CHP flags) |
| O3 | **Humboldt Bay (246, 10 × 16.7 MW reciprocating engines)**, the generation of the transmission-isolated Humboldt area. Actual CF 0.20–0.33; the model holds it in NP15 with no pocket. | 0.40 | 2019–25 | local topology (rule 17 if a floor) |
| O4 | **Legacy OTC steam** (Alamitos 3/4/5, Redondo 5/6/8, Huntington 2, Ormond 1/2): online 41–56 % of hours at min load in multi-day blocks, offer $20–41 above both prints. These are long-start steam units held committed (RA/reliability, plus DMM's long-start RUC). | ≈ 0.7 | 2019–23 (retired after) | commitment physics (rule 18) |
| O5 | **True peaker minimum-run tails:** neither-market hours inside an actual run block ≤ 24 h that contains a measured-clearing hour. | ≈ 0.3–0.6 | 2019–25 | commitment physics (rule 18) |

The price test shows O5's other face: 0.4–1.0 TWh of peaker energy that cleared the measured DA price while the model
λ sat $13–22 below DA. That is the adjudicated evening under-price (R-CAISO-21) and is not re-opened here.

## 2. Designs (owner picks per object; each default-off with a `--no-` flag, matrix row and cell in every shard, cache-key registration, tests)

**D1 — CAMPD remap completion (O1).**
- Add `(302, "6".."10") → 59002` and `(10294, "2") → 55811` to `campd.CAMPD_UNIT_PLANT_REMAP`.
- Both rows are CONFIRMED by the crosswalk of record (`campd_crosswalk.classify_remap_rows`; no override citation
  needed).
- Re-derive the CAISO CT heat-rate artifact and the CEMS outage extracts on the corrected map. Rule 23: the cited
  change is the mapping, not a residual.
- **Not a floor:** rule 17 does not apply, and there is no ScenarioConfig field unless the owner wants the remap
  flag-gated. If gated: `campd_remap_crosswalk_confirmed_caiso`.
- Rule 13: the same mapping serves a forward year (forward-year rates derive from the multi-year CAMPD history).

**D2 — Industrial self-generation class (O2).**
- Route plants whose EIA-860/eGRID record is industrial-sector or CHP-flagged out of CT_PEAKER into the existing
  CHP / must-run profile family (`chp_steam_following` K).
- **This touches the adjudicated CHP limb**, so it needs an owner ruling on scope.
- The benchmark class map must move with it (classFull is keyed on the EIA-923 class), or C1 compares unlike classes.
- Field: `caiso_industrial_selfgen_reclass`.

**D3 — Humboldt local area (O3). Topology preferred to a floor (rule 1 / rule 19).**
- Split a `HUMBOLDT` zone from NP15 with:
  - its measured load share;
  - Humboldt Bay as its generation;
  - a link limit equal to the area's published import capability (CAISO LCR/LCT study, Humboldt area; the
    `lcr_tsl_published` K family).
- The commitment then emerges from the LP. There is no floor, so rules 17 and 20 do not bind.
- **If the owner prefers a floor instead:**
  - window: all hours;
  - driver: Humboldt area load minus the published import capability;
  - forward story: the LCR study publishes forward-year needs;
  - floor = that need on the Humboldt units.
- Field: `caiso_humboldt_local_area`.

**D4 — Long-start steam commitment (O4). Rule 18, by parameters.**
- `caiso_ra_mustoffer`'s eligibility is the `fuel_types=("gas_cc", "gas_ct")` tuple plus min-down ≥ 4 h.
- Make it physics-only: any merchant gas unit with min-down ≥ 4 h, measured CEMS min-down/min-load, which admits the
  OTC steam units. ST min-load comes from CEMS (measured), not the CC 0.570.
- One mechanism (rule 19): the same bridge, wider eligibility. Nothing stacks.
- **D-2 reconcile:** `caiso_st_gas_committed_measured` / `caiso_st_gas_peak_measured` (K) are offer-surface bypasses,
  not floors, so they stay. The `st_gas_mustrun_*` floor family is off in CAISO (U) and must stay off.
- Field: `caiso_ra_mustoffer_physics_eligibility`.

**D5 — Peaker minimum-run (O5). Rule 18.**
- Only the UC MILP stage (`unit_commitment_milp`, default off, not armed in CAISO) can carry a fast-start min-up
  without a bridge. Rule 18 forbids bridging fast-start units beyond min-down.
- Arming it for CAISO replaces the bridges wherever it is armed (CLAUDE.md, the UC stage), so it is a recipe-level
  change.
- **Recommended: defer.** Reach is small (0.3–0.6 TWh) and the scope is the largest.

## 3. Window, driver and forward story (rule 17), for the items that floor

| Item | Floor? | Window | Driver | Forward story |
|---|---|---|---|---|
| D1 | no | — | — | the mapping is year-invariant |
| D2 | the existing CHP profile mechanism's floor | that mechanism's declared window | host operation (CHP flag / sector) | EIA-860 forward roster |
| D3 (topology) | no | — | area load vs published import capability | LCR forward years |
| D3 (floor variant) | yes | all hours | area load − published import capability | LCR forward years |
| D4 | yes (the RA bridge) | P0-detected commitment gaps ≤ measured min-down (the bridge's own window) | P0 commitment | P0 regenerates in a forecast |

## 4. Forced-energy budget (rule 20) and the one-mechanism check (rule 19 / D-2)

- **CT_PEAKER** (≥ 2 % of load): D1 adds no floor. D3 adds no floor in its topology form; the floor variant would add
  about 0.3–0.4 TWh forced against roughly 4–5 TWh of class energy, about 8 % (< 15 %). D5 deferred. **Within budget.**
- **ST_GAS:** 1.3–1.8 TWh is under 2 % of load, so it is immaterial and not gated. D-1/D-2 still report it.
- **CC_REGULAR:** D4 does not change the CC limb of the bridge; CC forced share stays at 8–12 % (w3).
- **D-2 against `caiso_ra_mustoffer`:**
  - D4 IS the bridge, widened;
  - D1 and D3 (topology) are not floors;
  - D2 reuses an existing mechanism.
  - No class ends up floored by two mechanisms.

## 5. Zero-LP reach (first order: the full gap recovered, displacing CC one for one; an upper bound)

**Recovered energy (TWh).**

| Year | D1 Carlsbad | D2 THUMS + New-Indy | D3 Humboldt | D4 OTC steam | Sum (D1–D4) |
|---|--:|--:|--:|--:|--:|
| 2019 | 0.27 | 0.54 | 0.36 | ≈ 0.7 | ≈ 1.9 |
| 2020 | 0.32 | 0.61 | 0.40 | ≈ 0.7 | ≈ 2.0 |
| 2021 | 0.30 | 0.55 | 0.26 | ≈ 0.6 | ≈ 1.7 |
| 2022 | 0.15 | 0.42 | 0.37 | 0.73 | 1.67 |
| 2023 | 0.26 | 0.53 | 0.35 | 0.72 | 1.86 |
| 2024 | 0.20 | 0.60 | 0.34 | 0.03 | 1.17 |
| 2025 | 0.21 | 0.41 | 0.35 | 0.02 | 0.99 |

**Projected C1 CC_REGULAR** at a realisation of 0.5–1.0× the sum.

| Year | C1 CC_REGULAR on w3 (band) | Projected |
|---|---|---|
| 2019 | −2.04 (±4.84) | **−3.0 … −3.9, WATCH** |
| 2020 | **+5.00 (±4.60)** | **+3.0 … +4.0, PASS** |
| 2021 | +3.47 (±4.83) | +1.8 … +2.6 |
| 2022 | +0.95 (±5.01) | −0.7 … +0.1 |
| 2023 | −1.07 (±5.27) | −2.0 … −2.9 |
| 2024 | −1.67 (±5.29) | −2.3 … −2.8 |
| 2025 | −0.36 (±5.08) | −0.9 … −1.4 |

**Declared ex ante.**
- **No C1 PASS→FAIL is expected.** 2019 CC_REGULAR is declared a WATCH: at full realisation it reaches −3.9 against
  −4.84.
- **CT_PEAKER 2021** (+1.63 on w3) rises by D1 + D3 (≈ 0.6) to about +2.2 (±4.83): WATCH.
- **C3a** moves down where min-load energy displaces marginal CC (DMM §7.1: min-load energy cannot set price). That
  helps 2021 (+12.0 %).
- **Effects are live in 2022–25.** Every keeper year re-solves, and the PRECOMMIT for the build carries the
  per-criterion bars.

## 6. Provenance

**DMM annual report PDFs** (scratch; to be committed under `data/raw/reference/caiso-dmm-annual/` with a README if
the owner adopts any DMM-derived item; D1–D4 above use no DMM number as an input). SHA-256:

```
ce2d59eb7278779f92d52b341743d09dad0eb097ae0efb94e56bb00138d61f55  dmm_2019.pdf
92423e068605eeb0aa21a0670c71b5c792f09e61481c77a116b51549ae4822a8  dmm_2020.pdf
c7f3dfc7dfb1a113312e949729b49ac10564a25c1b92559d9bd7ee917350d260  dmm_2021.pdf
a450f362fa5522d274875f3bea061db69d5ea59dc0b5658b1c8ec8f0c34c17b8  dmm_2022.pdf
0414fc5a965145049d4880c3948913c19924dac7ed83a94cd6c400f8fbad422b  dmm_2023.pdf
bdf292ce89b4caa6b6a0a89af21f248bbb910039e7c9355108773875a47dcdda  dmm_2024.pdf
7c89fdc42ef10968b194a3919dfb8f3ecf3ce52b53ffbe4bb9607e92a9915ea9  dmm_2025.pdf
```

**Plant identities:** eGRID 2020 PLNT20 / GEN20 (`data/raw/fleet-egrid/eGRID2020_Data_v2.xlsx`).

**Crosswalk rows:** `epa_eia_crosswalk.csv` lines for CAMD 302 units 6–10 and 10294 unit 2.

## 7. Recommendation

**Rule now (low risk, rule 14):**
- **D1**: a data correction under the existing crosswalk-of-record policy;
- **D3 in topology form**: structural; the floor variant only if the topology build is refused.

**Rule with scope:**
- **D4**: widens an existing bridge by physics, consistent with rule 18's "by parameters, not class names";
- **D2**: it touches the adjudicated CHP limb and the benchmark class map.

**Defer:** **D5** (UC MILP arming).

**Next steps.**
- The package D1 + D3 + D4 recovers ≈ 1.4 TWh in 2020 and projects C1 CC_REGULAR 2020 at +3.6 … +4.3 (band ±4.60): a PASS, but with thin margin at low realisation. Adding D2 (+0.6) widens it to +3.0 … +4.0.
- One full-span arm of 7 year-isolated shards on the w3 recipe, after the ruling.

## Addendum A: build, arms, bars and kills (2026-10-05, written before any solve)

**Desk ruling (2026-10-05).** D1, D3 and D4 build and solve now. Each is default-off and structural, and the owner
rules at promotion. D3 is the topology variant; D2 is held for the owner; D5 is deferred.

**As built.** Each item is its own flag, and each is byte-identical when off.

| Item | Flag | What changed from the design |
|---|---|---|
| D1 | `measured_ct_heat_rates_crosswalk_remap` | **Narrowed to the CT heat-rate artifact.** Arming the full `campd_split_remap_companions` set for CAISO would mean rebuilding companions whose CAISO recipes the builder cannot reproduce (tranche invocation unrecoverable; the CC family aborts on 2020 identity rows). That is infrastructure repair, not the lever. The deriver gains `--apply-remap`; the control derive reproduces the incumbent byte for byte (313 / 313). The companion is the incumbent plus 16 rows: Carlsbad, 9.07 pooled net vs eGRID 9.71, and King City 55811. Carlsbad's CEMS outage windows stay unread, as before (documented). |
| D4 | `caiso_ra_mustoffer_physics_eligibility` + `caiso_ra_st_min_load_frac` (0.119, measured CAMPD 2019–25) | Built as designed. **Reach revised:** the bridge only holds a unit across gaps between its own P0 runs. The upper bound on the w3 run pattern is 0.12 / 0.57 / 0.28 / 0.26 / 0.07 TWh for 2019–23. |
| D3 | `caiso_humboldt_local_area` | Built as designed. Load weight 0.005878 of PG&E (ATL_LDF SLAP_PGHB, pooled 2023–25). Import capability per year from the LCT Table 3.1-1: 22 / 23 / 23 / 33 / 34 / 40 / 50 MW. Carve by Humboldt County: 246, 10052, 10764, 50049, 59428, 64766. |

The D1 remap rows also re-key the benchmark's shared CAMPD frame for any new CAISO run. Carlsbad's hourly benchmark
shape becomes its own CEMS instead of flat. This moves C4 hourly shapes only; C1 levels are EIA-923.

**G-DRIFT** (`90cea720` → this build):
- **Fleet-only fingerprint of the w3 recipe, new flags off:** identical in all 7 years to the w3 build (`519dbd84`).
- **Hunks:** the w4/w5 probes are inert. D1, D3 and D4 are gated. The remap rows are LIVE only on raw-CAMPD readers,
  which means the benchmark frame and the derive scripts.

**Arms** (recipe = the w3 probe = `closeout_caiso_w1_a2_span` + the three w3 arm fields; one SHA, year-isolated):
- **A1 (stacked):** + D1 + D3 + D4.
- **A2 (D1-only):** + D1.
- **A3 (D1 + D4)**, if shard budget allows. Then D3 = A1 − A3 and D4 = A3 − A2.

**Targets and bars** (control = the w3 probe):

| Target | Bar |
|---|---|
| T1: C1 CC_REGULAR 2020 | +5.00 → ≤ +4.60 (PASS) |
| T2: CT_PEAKER energy | moves toward actual in ≥ 5 of 7 years (reported) |
| T3: Humboldt Bay (246) energy | reported against EIA-923 0.35–0.55 TWh |

**Declared ex ante (WATCH, not kills unless they cross the band):**
- C1 CC_REGULAR 2019 (−2.04, ±4.84);
- C1 CT_PEAKER 2021 (+1.63, ±4.83).

**Kills** (any one means NOT PROMOTED; the cell moves to R with the reason):
1. **K1:** any C1 PASS → FAIL in any year.
2. **K2:** C4 gas NRMSE worse by more than 0.02 in any year.
3. **K3:** C3a worse by more than 1.0 pp in any year.
4. **K4:** HUMBOLDT unserved energy (slack) over 0.1 % of HUMBOLDT load in any year. That would mean an infeasible pocket, which is a data or representation error.
5. **K5:** a C8 forced-energy breach on CT_PEAKER or CC_REGULAR (rule 20).
6. **K6:** C2 gas leaves its band.

**Decision rule:**
- Every kill clears and T1 is met: request a promotion slot superseding the w3 probe.
- Kills clear but T1 is missed: report; the cells stay U with evidence.

**Launch (pin `d24bd6aaeab257e52251c972cdfa32ba29bc7ea8`, environment `env_016R8xUY4maDbppZ6TEns5V8`; fast lane
11,534 passed, the one failure fixed in the same commit):**

| A1 leg | Shard session |
|---|---|
| 2019 | `session_01WS3eFjt4xkRaAuF8wnd6ZA` |
| 2020 | `session_014VeALCfe7WPEa9xBpzqQLm` |
| 2021 | `session_018azZPZ6VMbjdRh8jBUpz9K` |
| 2022 | `session_01BmX1h6LXvGijJJyeKHes6H` |
| 2023 | `session_01WMAq5naAP659x7vLqQRBFG` |
| 2024 | `session_01RttHzBMTK9FLJad8nwGRgN` |

A1 2025 and the seven A2 (D1-only) legs are queued under the 6-alive cap.
