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

### Phase 2 — Turn `ct_netload_drag` OFF for CAISO in the split probe (NOT a delete)
**Correction (2026-07-09, post-scope):** an earlier draft of this phase called for deleting
`ct_netload_drag` under rule 25. That was wrong — the mechanism is **shared across ISOs, not a
CAISO-only scaffold**: it is armed `=True` in ERCOT (`scripts/run_ercot41_integration.py`) and in
8+ PJM keepers/probes (`run_pjm75_ct_drag_cc_cap.py`, `run_pjm77_ablation_twin.py`,
`run_pjm78_srmc_baseline.py`, `run_pjm81_coopt_pergen.py`, `run_pjm82_commitment_posture.py`,
`run_pjm86_pjm83_head_baseline.py`, `run_pjm87_pergen_oppcost.py`,
`scripts/diag_pjm_burndown_2024.py`), and shares its `apply_netload_reliability_floor` engine
(`fleet.py:2269`) with the PJM ST_GAS drag (`gas_st_netload_drag`) that landed 2026-07-09
(`b064a6a`). Deleting the mechanism per rule 25 would break ERCOT and every one of those PJM runs.
Only CAISO auto-arms it (`backcast_config.py:1201`, `ct_netload_drag=(iso=="CAISO")`) with
CAISO-specific fitted coefficients (`0.00901 / -0.1124 / 0.36` vs ERCOT's default
`0.00703 / -0.1427 / 0.47`) — that CAISO-specific arming is the only thing in question here.

**What to actually do:** in the SP15-split probe (Phase 3), solve CAISO with `ct_netload_drag=False`
as an explicit config override (a one-line kwarg on the run, not a code change) — this is the A/B
test of whether the sub-pocket import-limited links can call CT_PEAKER onto merit without the floor
propping it up. Do **not** touch `scenarios.py`, `fleet.py`, `floor_mechanisms.py`, or the derive
script — the shared mechanism and the ERCOT/PJM arming stay exactly as-is.

**Deferred cleanup (only if/when the split is promoted to keeper):** at that point, and only then,
CAISO's own use of the drag is genuinely deprecated. The rule-25-scoped cleanup becomes: flip
`backcast_config.py:1201`'s `ct_netload_drag=(iso=="CAISO")` to a plain `False` (or drop the
CAISO branch), delete the CAISO-specific coefficient overrides at `backcast_config.py:1218-1219`,
and delete `scripts/derive_caiso_ct_reliability_floor.py` so the CAISO-fitted coefficients cannot
be re-swept onto the residual. The shared `ct_netload_drag` field, `apply_ct_netload_drag_floor`,
`MECH_CT_NETLOAD_DRAG`, and every ERCOT/PJM caller are permanently out of scope for this ISO's
calibration work.

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

---

## FOUNDATION DECISIONS (2026-07-09 — Phase 1 items 1 & 6, the topology spine)

This block fixes the topology **unambiguously** for every downstream SP15-split task. It is the
authoritative reference — where an earlier section of this doc disagrees (e.g. the 0.074 rounding),
this block wins. Implemented on branch `claude/caiso-sp15-foundation`, touching only
`config/iso_configs.py`, `model/transmission.py`, `config/interchange_config.py` (+ topology tests).

### Exact zone names (final, case-sensitive)
`SP15` is **deleted** and replaced by three zones. Full CAISO zone list, in config order:

```
NP15, ZP26, LA_BASIN, SDGE, SP15_rest, WECC_import
```

Downstream tasks (load-shares parquet, zone_assignment, crosswalk, gas hub, renewables fallback,
`derive_load_shares.py CAISO_ZONES`, `_LARGEST_ZONE`) must use these exact strings. No `SP15` zone
exists anymore.

### Load shares (of full ISO — must sum to 1.0, `validate_topology` hard-errors otherwise)
| Zone | load_share | Source |
|------|-----------:|--------|
| NP15 | 0.3969 | unchanged |
| ZP26 | 0.0646 | unchanged |
| LA_BASIN | **0.374** | LCT peak 19,537 ÷ SP26 peak 28,149 × 0.5385 (2023 Table 3.3-7 / 3.2-1) |
| SDGE | **0.091** | LCT peak 4,768 ÷ SP26 peak 28,149 × 0.5385 |
| SP15_rest | **0.0735** | exact residual: 0.5385 − 0.374 − 0.091 |
| WECC_import | 0.0 | import node, no load |

**Ambiguity resolved by judgment:** the scope table above lists SP15_rest as `0.074`, but
`0.374 + 0.091 + 0.074 = 0.539 ≠ 0.5385`, which fails `validate_topology`'s 1e-6 sum check. The
exact residual **0.0735** is used so the three sub-zones sum to the old SP15 0.5385 and the ISO
total is 1.0. LA_BASIN and SDGE keep their measured LCT-ratio values; SP15_rest absorbs the rounding.

### Final link list (direction + TTC)
| # | from | to | ttc_mw | bidir? | Path / meaning |
|---|------|----|-------:|:------:|----------------|
| 0 | NP15 | ZP26 | 5400 | yes | Path 15 (unchanged) |
| 1 | ZP26 | SP15_rest | 4000 | yes | Path 26, **re-pointed** off SP15 (same rating) |
| 2 | WECC_import | NP15 | 4800 | yes | Path 66 / COI (unchanged) |
| 3 | WECC_import | SP15_rest | 10623 | yes | Path 46 / WOR, **re-pointed** off SP15 |
| 4 | SP15_rest | LA_BASIN | **12008** | **NO (one-way)** | internal LA import limit = LCT import_cap |
| 5 | SP15_rest | SDGE | **1436** | **NO (one-way)** | Path 44 / SDG&E import limit = LCT import_cap |

`SP15_rest` is the south gateway: Path 26 and Path 46/WOR feed it, and the two pockets import from it
over the one-way import-limited links (4, 5). The one-way import-limited links are the mechanism that
forms the LA-basin/SDG&E locational premium.

### Import-cap values: **STATIC tightest-year (2023)** — per-year is the deferred end state
Convention: **`import_cap = peak_load − LCR`** (literal reading of the LCT `requirement`; the
reserve gross-up is a frozen sensitivity, never tuned to residual — rule 24). From
`data/raw/capacity-deliverability/caiso/caiso.csv` (`peak_load − requirement`):

| Pocket | 2023 | 2024 | 2025 |
|--------|-----:|-----:|-----:|
| LA_BASIN | **12,008** | 15,224 | 15,174 |
| SDGE | **1,436** | 2,074 | 2,071 |

**Decision: STATIC, using the 2023 (tightest / smallest / most-binding) caps** — LA 12,008, SDGE
1,436 — baked into `_caiso_config` as link TTCs. **Why static, not per-year:** per-year caps are the
preferred end state and should be wired through the runner's per-year config build (the same channel
as `transmission.apply_deliverability_seam_limit`, which the runner already calls per solve year).
That requires a **new runner call site** (e.g. an `apply_caiso_local_import_limits(cfg, year)` step),
which is **outside this foundation task's three-file scope**. The static tightest-year value is the
scope-sanctioned MVP; it is conservative (strongest pocket premium) and is a clean drop-in point for
a downstream per-year upgrade — that upgrade only needs to add the runner step and swap links 4/5's
TTC per year (values tabulated above).

### InterfaceLimit change
`WECC_import_simultaneous` (cap 7,500 MW, unchanged) now lists
`[("WECC_import","NP15"), ("WECC_import","SP15_rest")]` — the southern pair follows Path 46's
re-point to SP15_rest. `split_caiso_import_node_per_hub` rewrites both pairs to
`[("WECC_PNW","NP15"), ("WECC_DSW","SP15_rest")]` when `caiso_per_hub_intertie` is on, and
`apply_deliverability_seam_limit` still finds it structurally (all pairs originate at the import
node), so the published-MIC supersession path is intact.

### Corridor collision fix (Phase 1 item 6, the must-fix)
- `transmission._CAISO_CORRIDOR_LINK_TO["WECC_DSW"]` → `("SP15_rest",)` (was `("SP15",)`).
- `transmission.CAISO_PATH_DIRECTIONAL_RATINGS` Path-26 key → `("ZP26","SP15_rest")`.
- `interchange_config` `WECC_DSW.border_zones` → `("SP15_rest",)`.

So the Palo Verde/WOR import terminates on SP15_rest through every path (base config, per-hub split,
asymmetric-ratings, corridor-flow-limit, interchange spec).

### Verification (config-level only — model is not end-to-end runnable until 2A lands the parquet)
- `get_iso_config("CAISO").validate_topology()` passes; zones and links as tabulated above.
- `split_caiso_import_node_per_hub` re-homes DSW→SP15_rest and validates.
- `pytest tests/test_iso_config.py tests/test_transmission.py tests/test_caiso_per_hub_intertie.py
  tests/test_interchange_parity.py` → 171 passed, 2 pre-existing xfails. Four assertions updated to
  the new topology (documented in the commit): the CAISO zone-set (4→6 zones), the
  simultaneous-import link pair, the per-hub re-home pair, and the Path-26 directional-limit key.
  No test was weakened — each encoded the old SP15 topology that legitimately changed.

### Explicitly NOT touched (downstream / parallel tasks)
Load-shares parquet & `derive_load_shares.py`, `data/zone_assignment.py`, `capacity_area_crosswalk`,
`data/local_capacity.py` area specs, `renewables.py` / `data/fuel.py` / gas-hub CSV literals,
`constants.CAISO_TAC_ZONE_WEIGHTS`, and `ct_netload_drag` retirement. Per-year import caps (runner
wiring) are deferred as noted above.
