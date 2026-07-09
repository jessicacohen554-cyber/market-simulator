# CAISO SP15 local-area split — implementation scope (2026-07-09)

Companion to `docs/handoffs/caiso-transmission-ttc-diagnosis-2026-07-09.md`. That diagnosis found
the dominant CAISO failure is **SP15 copperplate under-pricing** (annual mean LMP under by $48–78,
growing 2023→2025) — the LA-basin/SDG&E local congestion that sets real SP15 prices cannot form in
a single copperplate SP15 zone. This doc scopes the fix: **split SP15 into its local capacity
areas** with import-limited links, and retire the `ct_netload_drag` scaffold. Grounded in a
file-by-file code trace; touchpoints are exact.

---

## Two corrections to the diagnosis doc (data + mechanism)

1. **The LCT/LCR data intake is already done — no new authorization needed.** Contrary to the
   diagnosis doc's caveat, the CAISO Local Capacity Technical (LCT) data is already on disk,
   schema'd (`data/dictionary/schema/capacity-deliverability.schema.yaml`), and sourced to the
   CAISO Final LCT reports:
   - `data/raw/capacity-deliverability/caiso/caiso.csv` — per-year `requirement` (LCR) **and**
     `peak_load` for `LA Basin` (LCR 7,529/4,413/4,123 MW; peak 19,537/19,637/19,297) and
     `San Diego/Imperial Valley` (LCR 3,332/2,834/2,709; peak 4,768/4,908/4,780), plus a `SP26`
     zone `peak_load` (28,149/28,310/27,736) — 2023/24/25.
   - `data/raw/reference/lcr_area_membership_CAISO.csv` — 117 plants (ORIS→area): LA Basin 83
     plants / 8,263 MW, San Diego/Imperial 34 plants / 2,762 MW (county-rule/geo-rule/nqc-list).
   - `src/market_sim/data/local_capacity.py` already reads both and computes
     `import_cap_a = peak_load_a − requirement_a` and `share_a = peak_load_a / zone_peak_load` for
     exactly these two pockets. The only data task is optional membership top-ups (Big Creek/Ventura
     has no membership rows yet) and pinning the import-cap reserve convention (below).

2. **The light mechanism is already built AND already shown insufficient.**
   `local_capacity_constraints` (`scenarios.py:816`, GATED default-off) adds an in-pocket min-gen
   row `Σ_{g∈a} P[g,t] + storage_share ≥ max(0, share_a·zone_load[t] − import_cap_a)` — "the exact
   LP relaxation of a load-pocket split." **But its row dual is out-of-market by design and does not
   enter the zonal energy-balance dual, so hub LMP is untouched** (`local_capacity.py:17-20`,
   `dispatch.py:1024-1027`). The prior A/B (`FINDING-ramp-lcr-caiso-2026-07`) measured **+39 MW**
   evening CT — near-inert, and structurally *cannot* move the SP15 price. This is mechanistic proof
   that closing the $48–78 SP15 miss requires a **true zone split** (the pocket's own energy balance
   + an import-limited link), not the min-gen relaxation.

**Decision: implement the true split (Path A).** Reuse the already-built `local_capacity` data
plumbing to *parameterize* the new zones (import-link TTC = `import_cap`, load shares from the LCT
`peak_load` ratios), not to add an out-of-market floor.

---

## The split (LCT-sourced parameters — not calibration guesses)

Split `SP15` → **`LA_BASIN`**, **`SDGE`**, **`SP15_rest`**. Every number below traces to the LCT
`peak_load`/`requirement` rows, which resolves the concern that SCE-TAC has "no measured
LA-basin boundary": the LCT study publishes the pocket peak loads directly, so the intra-SP15 load
split is measured, not a Tier-3 weight.

| Param | LA_BASIN | SDGE | SP15_rest | Source |
|-------|---------:|-----:|----------:|--------|
| load_share (of full ISO; sums to old SP15 0.5385) | 0.374 | 0.091 | 0.074 | LCT `peak_load` ratio ÷ SP26 peak |
| import cap into pocket 2023 (MW) | 12,008 | 1,436 | — | `peak_load − requirement` |
| import cap 2024 / 2025 (MW) | 15,224 / 15,174 | 2,074 / 2,071 | — | grows as LCR falls (new storage counts to LCR — forward-responsive, rule 11) |
| in-pocket gas capacity (MW) | 8,263 | 2,762 | — | membership CSV |

Note SDG&E's ~1.4–2.1 GW import cap is the post-SONGS Path-44 constraint — the physical reason
SDGE is the most import-limited pocket and sets high local prices.

**Reserve-margin convention (the one modeling choice to pin):** `import_cap = peak_load − LCR`
takes the LCR literally. CAISO's LCT identity is `LCR ≈ peak_load + reserve − import_capability`, so
the strict reading is `import_cap = peak_load·(1+PRM) − LCR`. Pick one, cite the LCT methodology,
and hold it frozen (rule 24 — derive-frozen-against-residuals). Recommend the literal
`peak_load − LCR` first (conservative/tighter import) and treat the reserve gross-up as a
sensitivity, never tuned to the price residual.

---

## Implementation phases

### Phase 0 — Data confirmation (small)
- Confirm the `local_capacity.load_lcr_parameters` outputs match the table above; decide the
  reserve convention; optionally add Big Creek/Ventura membership rows (else fold into SP15_rest).
- No holdout/authorization issue: all data is 2023–2025 train-year, already on disk and schema'd.

### Phase 1 — Topology split (the core build)
Minimum edit set (file:line from the code trace). Guardrails fail loud; silent hazards flagged ⚠.

1. **`config/iso_configs.py` `_caiso_config` (273–338).** Replace the `SP15` `Zone` with the three
   sub-zones (shares summing to 0.5385 — `validate_topology:129` hard-errors otherwise). Re-point
   Path 26 (`ZP26→SP15`) and Path 46/WOR (`WECC_import→SP15`) onto the chosen sub-zone; add internal
   links **`SP15_rest→LA_BASIN` (ttc = LA import_cap ≈ 12 GW, one-way `is_bidirectional=False`)** and
   **`SP15_rest→SDGE` or `LA_BASIN→SDGE` (ttc = Path-44 ≈ 1.4 GW, one-way)**. Update the
   `WECC_import_simultaneous` `InterfaceLimit` link pair to match a real post-split link
   (`validate_topology:120` hard-errors otherwise). The import-limited internal links are what
   create the pocket LMP premium — this is the mechanism the whole fix turns on.
2. **`config/constants.py:2800-2805` `CAISO_TAC_ZONE_WEIGHTS`.** `SDGE-TAC→{SDGE:1.0}` (measured,
   clean); `SCE-TAC→{LA_BASIN:w, SP15_rest:1-w}` with `w` = LA_Basin/(LA_Basin+rest) peak ratio ≈
   0.835 (LCT-sourced, documented); `VEA-TAC→{SP15_rest:1.0}`. ⚠ `_zonal_shares_from_raw` swallows a
   `KeyError` and silently drops to static shares if these zone names drift from the config zone
   names (`eia_loader.py:2031-2035`) — keep them in lockstep.
3. **`data/zone_assignment.py:76-79, 515-548`.** Add county branches to `_caiso_zone` before the
   latitude test (LA/Orange → LA_BASIN; San Diego/Imperial → SDGE; else SP15_rest); re-point the
   Arizona/Nevada-south import hardcodes; update `_LARGEST_ZONE["CAISO"]` off the removed `SP15`
   name. ⚠ EIA-860 greenfield cohort (`_eia860_ba_zones:817`) routes coords-only, so add a lat/lon
   LA/SD cut too or the 2024+ SoCal solar/storage lands in the default. The membership CSV
   (`local_capacity.caiso_area_of`, county geography) is reusable to build these rules.
4. **`config/capacity_area_crosswalk.py:257-269`.** Re-point `LA Basin → LA_BASIN`,
   `San Diego/Imperial Valley → SDGE`, `Big Creek/Ventura → LA_BASIN or SP15_rest`. ⚠ an area left
   out resolves to `unmapped` and silently drops from the zone rollup.
5. **`data/local_capacity.py:130-142`.** The `LOCAL_CAPACITY_AREAS["CAISO"]` specs' `zone="SP15"`
   becomes `zone="LA_BASIN"`/`"SDGE"` (these areas ARE the new sub-zones — the two mechanisms
   converge here). Fix the `storage_area_share` `lat<35.0` bucket (`:248-249`) which no longer
   isolates one sub-zone. Keep `local_capacity_constraints` **off** in the keeper — the split
   supersedes it; do not stack both on the same pocket (rule 12, one-mechanism).
6. **Per-hub corridor collision (must-fix, not optional).** `transmission.py:573-574`
   `_CAISO_CORRIDOR_LINK_TO = {"WECC_DSW":("SP15",)}` and `split_caiso_import_node_per_hub:801-846`
   re-home the WECC_DSW (Palo Verde/WOR) import onto SP15 — re-point to the chosen sub-zone.
   `transmission.py:2313-2318` `CAISO_PATH_DIRECTIONAL_RATINGS` Path-26 key and
   `interchange_config.py:556` `WECC_DSW border_zones=("SP15",)` likewise.
7. **Sub-zone literal re-points:** `renewables.py:170-174` (`solar":"SP15"` fallback),
   `data/fuel.py:2891-2936` + `data/raw/caiso_zonal_gas_hub.csv` (⚠ add SDGE/LA_BASIN/SP15_rest rows
   on SoCal Citygate or they get no basis shift), `scripts/derive_load_shares.py:90` `CAISO_ZONES`.
8. **Tests:** ~16 CAISO-specific files assert the 3+1 zone set (`test_iso_config`,
   `test_zone_assignment`, `test_caiso_zonal`, `test_capacity_area_crosswalk`,
   `test_capacity_deliverability_caiso`, `test_local_capacity`, `test_caiso_per_hub_intertie`,
   `test_caiso_corridor_flow_limit`, `test_transmission`, `test_interchange_parity`, …). Trivial-case
   first (rule: 1 gen/1 zone/24 h) then scale.

### Phase 2 — Retire `ct_netload_drag` (rule 25 delete, not default-off)
The drag is the reduced-form proxy for exactly the LA-basin/Big-Creek local commitment the split now
models structurally (its own derive-script header names those areas as the driver). Same phenomenon,
two mechanisms — retire the scaffold. Per rule 25 (deleted-means-deleted) a default-off is
insufficient (CAISO ON-state is set at `backcast_config.py:1201`, not a kwarg, and a parseable fitted
coefficient is a re-armable answer key). **Delete:** the `ct_netload_drag`/`ct_drag_*` fields
(`scenarios.py:3089-3094`), `apply_ct_netload_drag_floor` + call sites (`fleet.py:2418-2478, 2628,
2650`), `MECH_CT_NETLOAD_DRAG` (`floor_mechanisms.py`), the `backcast_config.py:1201, 1218-1219`
lines, `scripts/derive_caiso_ct_reliability_floor.py`, the DOF-ledger row, and the runner gate. The
zero-forcing ablation twin naturally captures the retirement.

### Phase 3 — Solve, score, register (rule 16)
- Solve **2023–2025 in one bundle** (per-plant multi-zone LP; years sequential within the run; ≤2
  concurrent separate invocations). If `capacity_deliverability_limits` warns "clean partition
  absent," run `scripts/curate_capacity_deliverability.py --isos CAISO` first.
- Register **main + zero-forcing ablation twin as PROBES** (`calibration-report` /
  `scripts/dashboard_add_run.py` + `build_manifest.py`; never edit `keepers.json`).
- **Score leave-one-year-out within 2023–2025 before proposing promotion** (rule 22). Holdout
  discipline: no 2022/2019/H1-2026 touch.

---

## Pre-registered A/B (vs caiso-65, both temp-derate on, all three years)

| Metric | Baseline (caiso-65) | Success direction |
|--------|--------------------:|-------------------|
| SP15/LA_BASIN mean LMP | $47–70 | → toward actual $117–127 (the headline) |
| CT_PEAKER dispatch | 1.4–2.1 TWh | → toward actual 3.1–5.2 TWh, **cleared on merit** (not floored) |
| CC_REGULAR dispatch | 61–64 TWh | ↓ |
| C8 forced-energy (CT drag) | 60/56/63 % FAIL | drag retired → C8 driven only by RA bridge (~5–6 %) |
| 2023 hrs>$200 | 507 (vs 21 actual) | ↓ toward actual; 2024/25 tail (0 vs 35/8) forms locally |

Judged on **structural faithfulness, never MAE alone** (rule 1). A worse system-mean with a correct
SP15 premium and merit-cleared peakers is a keeper candidate; a better mean via a re-armed floor is
not. If the split moves SP15 toward $117–127 and lets CT clear on merit, the drag deletion is
vindicated and the offer-curve re-tune (Tier 4 of the diagnosis plan) becomes the *next* pass.

---

## Effort & risk

- **Effort:** multi-day structural build. ~7 source files + 1 data CSV + ~16 test files + 3-year
  solve × (main + ablation). The blast radius is the new-zone surgery in Phase 1, especially the
  per-hub corridor collision (item 6) and the silent-hazard sites.
- **Biggest risks:** (a) per-hub corridor re-homing (WECC_DSW→SP15) — a miss silently mis-routes the
  Palo Verde import; (b) the reserve-margin convention for `import_cap` (pin and freeze); (c) the
  EIA-860 greenfield coords-only routing (item 3); (d) internal links must connect the sub-zones or
  they island in the LP.
- **De-risking option:** if the full 3-way is too large for one pass, `LA_BASIN` carries the bulk of
  the $48–78 miss (peak 19.5 GW vs SDGE 4.8 GW) — an `LA_BASIN` + `SP15_rest` (SDGE folded into rest)
  MVP is the 80/20 first probe, with SDGE added second. The topology surgery (Path-26/46 re-home,
  corridor collision) is similar either way, so the incremental cost of the full 3-way is modest.
