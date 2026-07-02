# Build Plan — Scope 2 Hourly LCE Portfolio Optimization Tool

Handoff document. Read this, then `docs/`, then pick up the next open prompt pack
in `docs/prompt-packs/`. The tool is intentionally **standalone and vendored** —
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
- **Mode A:** `min Σ grid_buy` s.t. premium ≤ delta (pure objective; a least-cost
  tiebreak was tried and removed — it stalled the solver).
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
- `data/profiles/` — real per-ISO CF Parquets, built at runtime by
  `scripts/build_profiles.py` (gitignored; test fixture committed under `tests/fixtures/`).
- `data/reference/` — ADR-ratification reference load (stylized 100-MW facility, generated
  by `scripts/make_reference_load.py`, gitignored).
- `data/emissions/` — (directory, was REMOVED per ADR 0013 — residual CO₂ now computed from
  per-ISO hourly fossil-average rate exported by `scripts/build_fossil_avg_co2_rate.py`).
- `data/sample/` — synthetic load + LMP for the demo/tests (generated by `examples/run_sample_sweep.py`).
- `data/inputs/`, `data/outputs/` — user data & results (gitignored).

## 7. Planning sessions (decisions → ADRs) — `docs/planning-sessions/`

Run each as a focused session; each ends by writing an ADR to `docs/decisions/`.
PS-01 pricing/LCOE · PS-02 premium & netting · PS-03 storage costing ·
PS-04 matching semantics · PS-05 existing-resource treatment · PS-06 caps &
potential · PS-07 load intake & growth · PS-08 LMP coupling & scenarios.
**All eight decided 2026-07-01 → ADRs 0004–0011** (see `docs/decisions/`).
PS-09 gas-CC+CCS resource (partial-capture matching credit) decided
2026-07-02 → **ADR 0012**, implemented by PP-08.
PS-10 stakeholder ratification of provisional ADRs (2026-07-02) → **ADRs 0005/0007/0009/0010 amended & ratified** (0005: f=1.0).
PS-11 reporting deliverable (2026-07-02) → **ADR 0014** (self-contained HTML report + committed results store).
PS-12 forecast LMP selection (2026-07-02) → **ADR 0015** (study years, BAU scenario identity, readiness gate, rollout).

## 8. Prompt packs (build) — `docs/prompt-packs/`

Run in order once their upstream ADRs land: PP-00 scaffold/config → PP-01 intake →
PP-02 catalog → PP-03 CF profiles (first vendoring) → PP-04 LP core →
PP-05 sweep/CLI → PP-06 outputs/reporting → PP-07 tests → PP-08 gas CC + CCS
resource (ADR 0012: two tranches, delivered-gas fuel + 45Q net VOM, load-time
low-carbon threshold, grid/resource residual-CO₂ split). **PP-00 through PP-08 complete**
(build waves of 2026-07-01; PP-08 implemented by 2026-07-02); next open work is PP-09
(reporting deliverable, ADR 0014, in flight) and the on-hold real-LMP validation path
(ADR 0015, stakeholder decision 2026-07-02). **PP-10 (desktop launcher, ADR 0016)
complete** (2026-07-02): `launcher/run_lce.sh`/`run_lce.bat` twins + `src/lce_portfolio/launcher.py`
(stdlib HTTP server, self-contained launch page, run queue, saved configs).

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
- [ ] Execute prompt pack PP-09 (reporting deliverable, ADR 0014) — self-contained HTML run report + committed results store.
- [ ] Export a forecast-year BAU LMP file from the market sim (ADR 0011 contract) and
  build `data/profiles/` for all six ISOs, then run the first real per-ISO sweep.
  **ON HOLD (stakeholder, 2026-07-02): do NOT run market-sim forecasts for this —
  the forecast side is not production-ready yet. Until it is, the tool runs on the
  exporter's `--dummy` synthetic LMP (always labeled SYNTHETIC in outputs/sidecar);
  a calibrated backcast-year export is the approved interim validation path if
  needed (ADR 0015 permits backcast for validation studies only).**
