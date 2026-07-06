# Build Plan — Scope 2 Hourly LCE Portfolio Optimization Tool

Handoff document. Read this, then `docs/`, then pick up the next open handoff
prompt in `docs/handoff/`. The tool is intentionally **standalone and vendored** —
no `import market_sim`.

## 1. Purpose

Select a least-premium portfolio of clean/low-carbon resources + storage to match
a company/facility 8760 load hour-by-hour, given BAU wholesale LMPs. Sweep the
"clean premium" ($/MWh above wholesale) and report how high hourly carbon-free
matching can go at each premium, per ISO, with the resource mix.

## 2. Scope & non-goals

- **In scope:** portfolio capacity selection + hourly operation LP; per-resource
  cost (low/mid/high) and capacity caps; storage (batteries/LDES/hydrogen);
  premium↔matching sweep both directions; facility→ISO load aggregation + growth.
- **Non-goals:** re-simulating the wholesale market (that's `src/market_sim`);
  intra-ISO transmission/nodal detail (single aggregated node per ISO);
  unit commitment. LMPs are an **input**, not recomputed here.

## 3. Locked design decisions (this session)

| Decision | Choice |
|---|---|
| Coupling | Vendored — standalone, no `market_sim` import |
| Default mode | Premium-cap → maximize hourly CFE matching % |
| Directory | Top-level `scope2-lce-portfolio/` |
| Deliverable | Scaffold + docs + prompts + minimal working LP |

Open decisions are staged as planning sessions (§7).

## 4. The model (summary)

Single aggregated node per ISO, full 8760. Column vector:

```
build_mw[r] | gen[r,t] | chg[s,t] | dis[s,t] | soc[s,t] | grid_buy[t] | excess[t] | build_energy[k]
```

- **Energy balance:** `Σ gen + Σ(dis−chg) + grid_buy − excess = load` (per hour).
- **Gen bound:** `gen[r,t] ≤ cf[r,t]·build_mw[r]`; budget-flagged hydro also capped
  per calendar month (ADR 0008).
- **Caps:** `cap_min[r] ≤ build_mw[r] ≤ cap_max[r]` (per-ISO table, ADR 0009).
- **Storage:** cyclic SOC dynamics; fixed-duration techs bound `soc ≤ duration_h·build_mw`;
  split techs (LDES/H₂) size `build_energy[k]` separately within duration bounds (ADR 0006).
- **Matching (ADR 0007, volumetric):** per hour, clean energy counts only up to load —
  `matched_t = load_t − grid_buy_t`, surplus excluded; annual % = `Σ matched / Σ load
  = 1 − Σbuy/Σload` (NOT "% of hours at 100%"). Additionality toggle moves existing-resource
  gen to the unmatched side (ADR 0008). Gas CC+CCS counts fully toward matching if it
  clears the ADR 0012 threshold (capture > 0.90, residual < 0.050 tCO₂/MWh); its residual
  stack emissions are tracked separately (ADR 0012).
- **Residual carbon:** grid purchases attributed at the market simulator's **hourly fossil-only
  average** CO₂ rate (ADR 0013, superseding the per-MWh scalar marginal rate), plus residual
  stack emissions from partial-capture resources (ADR 0012), reported separately for each
  frontier point.
- **Premium:** `(net cost − BAU) / Σload`, where net cost nets grid buys (+) and
  excess sales (−) at LMP (× `excess_sale_fraction`, ADR 0005 default **f=1.0**).
- **Mode A:** `min Σ grid_buy` s.t. premium ≤ delta (pure objective, no cost
  term), plus a flat `build_tiebreak_epsilon` (default 1e-6) on `build_mw`
  to break the degenerate tie once matching saturates below a resource's cap
  (ADR 0019 — fixes the CAISO onshore-wind saturate-to-cap finding; a
  `net_cost`-weighted least-cost tiebreak was tried first and rejected, see
  the ADR).
- **Mode B:** `min net cost` s.t. matching ≥ target (annual or strict per-hour).

Full math: `docs/01-lp-formulation.md`. Implementation: `src/lce_portfolio/lp.py`.

## 5. Module map (`src/lce_portfolio/`)

| Module | Responsibility | Status |
|---|---|---|
| `config.py` | `PortfolioConfig` dataclass (all knobs) | done (PP-00: validation + `from_file`) |
| `resources.py` | resource catalog + ATB capex/CRF costs + caps → `ResourceArrays` | done (PP-02: ATB 2024 CRF catalog, per-ISO caps/eligibility, hydro budgets, split-tech parse; PP-08: gas CC+CCS tranches, delivered-gas + 45Q net VOM, ADR 0012 threshold) |
| `intake.py` | load/LMP/emission-rate read → validation → facility/ISO aggregation → growth | done (PP-01: hard missing-hour/dup errors, `prepare_lmp`, `collapse_zonal_lmp`, load growth; PP-08: `emissions_intake`, `prepare_emission_rate` wiring per ADR 0013) |
| `profiles.py` | `(n_res,T)` CF matrix; real per-ISO Parquet + synthetic fallback; shape-year pinning | done (PP-03: real path keyed by (iso, year), SAMPLE/fallback synthetic; `profile_shape_year` parameter) |
| `lp.py` | portfolio LP build + HiGHS solve | done (PP-04: both modes; split-storage vars + hydro budget + additionality; infeasible-safe; PP-08: grid/resource residual-CO₂ split) |
| `sweep.py` | parametric sweep driver | done (PP-05) |
| `outputs.py` | Parquet frontier + build-mix, text summary | done (PP-06: enriched metrics + residual CO₂ + run metadata) |
| `report.py` | ADR 0014 report payload + self-contained HTML renderer | done (PP-09: provenance, frontier, build-mix, cost, residual-CO₂, multi-ISO, hourly heatmap/SOC views; versioned `report.json`) |
| `cli.py` / `__main__.py` | CLI entry point | done (PP-01: `--config` load_file/lmp_file wiring, clean errors, `--all-isos`) |
| `vendored/` | copied market-sim logic (CF shapes) | done (PP-03: `renewable_shapes.py`, pinned upstream commit + re-sync header) |
| `scripts/build_profiles.py` | build per-ISO CF Parquets from the market-sim data tree (no import) | done (PP-03) |
| `scripts/build_fossil_avg_co2_rate.py` | compute hourly fossil-only average CO₂ rate per ISO from market-sim dispatch (ADR 0013 export) | done (PP-08) |
| `scripts/make_reference_load.py` | generate stylized 100-MW facility load for ADR-ratification validation | done (PP-10) |
| `launcher.py` / `launcher/` | desktop launcher: stdlib HTTP server + self-contained launch page, `run_lce.sh`/`run_lce.bat` twins | done (PP-10: ADR 0016) |

## 6. Data

- `data/lcoe/resource_costs.csv` — NREL ATB 2024 cost table (capex/FOM/life + CRF
  annualization, split-storage columns, `eac_premium_mwh`, CCS columns `heat_rate_mmbtu_mwh`,
  `capture_rate`, `emission_rate_ton_mwh`; ADRs 0004/0006/0008/0012).
- `data/caps/resource_caps.csv` — per-(ISO, resource) MW caps + eligibility (ADR 0009).
- `data/hydro/monthly_budgets.csv` — existing-hydro monthly energy budgets, GWh (ADR 0008).
- `data/fuel/gas_prices.csv` — per-ISO delivered natural gas prices ($/MMBtu) and basis
  differential, matching market-sim forward-year fidelity; used to compute fuel VOM
  for gas CC+CCS resources (ADR 0012).
- `data/profiles/` — real per-ISO 2024 CF Parquets, **committed** for standalone
  pull-out (HP-02, 2026-07-06; all six ISOs). Derived-but-bundled: regenerate with
  `scripts/build_profiles.py` when the source EIA-930 data updates.
- `data/bundled/lmp/` — real 2024 backcast BAU LMP exports (ADR 0011 contract),
  each with a `.provenance.json` sidecar naming the source calibration keeper.
  **Committed: all six ISOs** (HP-02, PR #1547: ERCOT/CAISO/PJM; HP-02b,
  PR #1554 + this session: MISO/NYISO/NEISO). Backcast-validation carve-out
  only (ADR 0015); each export is a 2024-only bridge re-solve of that ISO's
  *then-current* calibration keeper via `run_calibration_full.solve_and_persist`
  (never registered on the dashboard — rule #16 forbids single-year keepers).
  Bundle inventory (file sizes, source keeper id, mean/min/max $/MWh — see each
  `.provenance.json` for the full record):

  | ISO | LMP CSV | mean | min | max | source keeper id |
  |---|---:|---:|---:|---:|---|
  | ERCOT | 165,372 B | $25.96 | $8.78 | $2,244.80 | `2026-07-06-ercot34-stage4-overlay-off` |
  | CAISO | 165,338 B | $46.83 | $-20.00 | $77.31 | `2026-07-03-caiso-51-firm-base` |
  | PJM | 147,845 B | $26.41 | $-21.24 | $54.21 | `2026-07-05-pjm-77-ct-relfloor` |
  | MISO | 156,583 B | $26.22 | $16.34 | $48.33 | `2026-07-06-miso-42-coal-econ-ablation` |
  | NYISO | 165,438 B | $30.89 | $-26.00 | $182.91 | `2026-07-06-nyiso-53-li-tsl` |
  | NEISO | 165,307 B | $36.11 | $8.39 | $198.91 | `2026-07-06-neiso-49-stgas-netload` |

  MISO's keeper moved to an ablation-labelled bundle
  (`miso_42_coal_econ_srmc-ablation`) mid-session (a concurrent calibration
  session updated `frontend/data/backcast/keepers.json` while this bridge ran);
  the provenance sidecar records the bundle actually solved, which is what
  matters for reproducibility — re-run `scripts/build_profiles.py`-style
  bridging against the *current* keeper if this drifts further and the export
  should track it.
- `data/emissions/` — per-ISO 2024 hourly fossil-avg CO₂-rate Parquets
  (ADR 0013), **committed for all six ISOs** alongside their LMP bundles
  (same HP-02/HP-02b provenance as `data/bundled/lmp/` above). The tool
  degrades gracefully where a rate file is absent (emission file is optional) —
  exercised by the SAMPLE ISO, which carries none.
- `data/templates/` — committed draft input templates + schema README;
  full-8760 fillable skeletons via `scripts/make_input_templates.py`
  (written to `data/templates/skeletons/`, gitignored).
- `data/reference/` — ADR-ratification reference load (stylized 100-MW facility, generated
  by `scripts/make_reference_load.py`, gitignored).
- `data/sample/` — synthetic load + LMP for the demo/tests (generated by `examples/run_sample_sweep.py`).
- `data/inputs/`, `data/outputs/` — user data & results (gitignored).

## 7. Planning sessions (decisions → ADRs)

All decisions are recorded as ADRs in `docs/decisions/` (the PS-NN
planning-session prompt docs were removed at handoff cleanup, 2026-07-06;
they live in git history).
PS-01 pricing/LCOE · PS-02 premium & netting · PS-03 storage costing ·
PS-04 matching semantics · PS-05 existing-resource treatment · PS-06 caps &
potential · PS-07 load intake & growth · PS-08 LMP coupling & scenarios.
**All eight decided 2026-07-01 → ADRs 0004–0011** (see `docs/decisions/`).
PS-09 gas-CC+CCS resource (partial-capture matching credit) decided
2026-07-02 → **ADR 0012**, implemented by PP-08.
PS-10 stakeholder ratification of provisional ADRs (2026-07-02) → **ADRs 0005/0007/0009/0010 amended & ratified** (0005: f=1.0).
PS-11 reporting deliverable (2026-07-02) → **ADR 0014** (self-contained HTML report + committed results store).
PS-12 forecast LMP selection (2026-07-02) → **ADR 0015** (study years, BAU scenario identity, readiness gate, rollout).

## 8. Prompt packs (build history — PP-NN docs removed at handoff cleanup; in git history)

Run in order once their upstream ADRs land: PP-00 scaffold/config → PP-01 intake →
PP-02 catalog → PP-03 CF profiles (first vendoring) → PP-04 LP core →
PP-05 sweep/CLI → PP-06 outputs/reporting → PP-07 tests → PP-08 gas CC + CCS
resource (ADR 0012: two tranches, delivered-gas fuel + 45Q net VOM, load-time
low-carbon threshold, grid/resource residual-CO₂ split). **PP-00 through PP-08 complete**
(build waves of 2026-07-01; PP-08 implemented by 2026-07-02). **PP-09 (reporting
deliverable, ADR 0014 §1–§6) complete**: `src/lce_portfolio/report.py` (payload
builder + self-contained HTML renderer covering provenance, frontier, build-mix,
cost breakdown, residual-CO₂, multi-ISO comparison, and the hourly dispatch
heatmap/SOC view), `scripts/render_report.py`, CLI `--run-id`/`--results`/
`--no-report`/`--report-hourly`, and the committed `results/<run-id>/` store
(two real bundles committed: `SAMPLE_premium_cap_20260702-171842/`,
`ercot_backcast2024_premiumcap/`). **PP-10 (desktop launcher, ADR 0016)
complete** (2026-07-02): `launcher/run_lce.sh`/`run_lce.bat` twins + `src/lce_portfolio/launcher.py`
(stdlib HTTP server, self-contained launch page, run queue, saved configs);
post-merge adversarial review **PP-13** (2026-07-02) fixed 11 findings
(request-body hardening, batch run-id collisions, loopback-only enforcement,
error-message purity — PP-13 review doc in git history).
The ERCOT backcast-validation bridge (§10 below) has now been extended to
CAISO/PJM/MISO/NYISO/NEISO (2026-07-05, see
`docs/validation-2026-07-05-5iso-backcast-extension.md`) — all six ISOs have
a real-priced validation sweep on the dashboard-adjacent `results/` store.
Next open work: the market-sim **forecast** LMP path stays on hold
(stakeholder decision 2026-07-02, ADR 0015) pending each ISO's production-
readiness sign-off; CAISO's premium-cap frontier surfaced a pre-existing Mode
A no-cost-tiebreak degenerate-solution limitation (see the 5-ISO memo) that
is real LP-design follow-up work, not yet scheduled.

## 9. Verification

```bash
../.venv/bin/python examples/run_sample_sweep.py     # end-to-end frontier on synthetic data
../.venv/bin/python -m pytest tests/ -q              # 147 tests: config, intake, LP core, CLI, extensions, cross-feature
grep -rn "import market_sim" src/ || echo "OK: standalone"   # isolation check
```

Expected: sweep prints a matching%-vs-premium table for `{1,2,5,7,10,20}`; matching%
is non-decreasing in the premium cap; all 147 tests pass (trivial cases first, then
extensions like split-storage, hydro budget, additionality, CCS threshold logic, cross-feature interplay).

## 10. Handoff checklist

- [x] Read this + `docs/00-overview.md` + `docs/01-lp-formulation.md`.
- [x] Run the demo and tests (§9). ✓ 147 tests passing (measured 2026-07-02).
- [x] Work the open planning sessions to record decisions in `docs/decisions/`. ✓ PS-01..12 → ADRs 0004..0015 (2026-07-01/02).
- [x] Execute prompt packs PP-00 through PP-08 in order, updating docs/PLAN.md status. ✓ PP-00..08 complete (PP-08 gas-CC+CCS, ADR 0012, implemented 2026-07-02).
- [x] ADR ratification (PS-10, 2026-07-02): ADRs 0005/0007/0009/0010 amended & ratified (0005: f=1.0, excess credited at full LMP).
- [x] Fossil-avg CO₂-rate export wiring (ADR 0013): `scripts/build_fossil_avg_co2_rate.py` available; hourly rate file contract wired into intake & LP.
- [x] Execute prompt pack PP-09 (reporting deliverable, ADR 0014) — self-contained
  HTML run report + committed results store. ✓ `report.py` renders all six ADR
  0014 §2 views from a versioned `report.json` payload; `results/<run-id>/` is a
  committed store (two real bundles landed); CLI gained
  `--run-id`/`--results`/`--no-report`/`--report-hourly`; 254 tests passing
  (measured 2026-07-05, includes `tests/test_report.py`).
- [x] Build `data/profiles/` for all six ISOs (`scripts/build_profiles.py --year
  2024`; real EIA-930-derived CF shapes for ERCOT/CAISO/PJM/MISO/NYISO/NEISO,
  2026-07-05).
- [x] Run the first real per-ISO sweep, via the ADR 0015 **backcast-validation**
  interim path (ERCOT, weather_year 2024; 2026-07-05). Discovered along the way:
  `scripts/export_lce_lmp.py`'s cache-reading path was never actually wired for
  backcast years (no code path had ever populated
  `results/{iso}/{cache_key}/year_{year}.parquet` for 2023-2025) — worked around
  with a one-off bridge script (zero edits to `run_calibration.py`/`runner.py`),
  not a tool-side hack; see full diagnosis, frontier sanity checks, and caveats in
  `docs/validation-2026-07-05-ercot-2024-backcast.md`. Result committed:
  `results/ercot_backcast2024_premiumcap/`.
  **The market-sim FORECAST path stays ON HOLD (stakeholder, 2026-07-02)** — this
  item is the backcast-validation carve-out ADR 0015 explicitly permits, not a
  stakeholder sign-off that any ISO's forecast is production-ready.
- [x] Extend the backcast-validation sweep to CAISO/PJM/MISO/NYISO/NEISO
  (2026-07-05), each via its own per-ISO bridge re-solve from that ISO's
  current calibration keeper (all five carry their own `meta.json`
  schema-drift caveat, same class as ERCOT's; CAISO also needed the
  per-hub WECC-import topology replicated). Results committed:
  `results/{caiso,pjm,miso,nyiso,neiso}_backcast2024_premiumcap/`. PJM/MISO/
  NYISO/NEISO all reproduce ERCOT's sanity checks cleanly (monotonic
  premium-vs-matching, late storage entry, plausible fossil-CO₂-rate
  ordering); CAISO's frontier instead surfaced a pre-existing Mode A
  no-cost-tiebreak degenerate-solution limitation (saturates at 100%
  matching from $1/MWh by building onshore wind near its 20 GW resource
  cap) - flagged, not fixed at the time, see
  `docs/validation-2026-07-05-caiso-mode-a-tiebreak-fix.md`. 259 tests
  passing (measured 2026-07-05, includes '2026-07-06-ercot34-stage4-overlay-off' inserted 'CAISO' 'PJM' 'MISO' 'NYISO' 'NEISO' 'ERCOT' 'inventory' 'lce_bridge' inventory (ie.