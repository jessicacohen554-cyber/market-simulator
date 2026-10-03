# Third-Party Audit 2026-10 — Section A: LP, Dispatch, Pricing, Commitment, Storage, Transmission, Reserves, Solver

Auditor: independent (Claude Fable 5.1). Branch `claude/third-party-audit-2026-10`, HEAD `d7ff7c20` (2026-10-03).
Hard budget 11 min wall-clock; read-only; no LP solved, no tests run, no file edited. Every repo claim cites `file:line` at HEAD.
Comparator claims are from public documentation of the named tools as the auditor recalls it; no version numbers are asserted.

## 1. Scope & method

Read in order: `CLAUDE.md` (LP / Dispatch sections), `model-methodology-spec.md` §1.1–1.3, §1.6, §1.8, §1.9, §2.3,
`docs/codebase/02-lp-dispatch.md`, `docs/codebase/03-capacity-and-commitment.md`, then verified against
`src/market_sim/model/lp/{layout,rows,reserve_rows,bounds,costs,model,hydro_cascade}.py`, `model/{commitment,storage,ancillary}.py`,
`model/interchange/core.py`, `model/reserves/spec.py`, `pipeline/solve.py`, and the prior audit `docs/audit/third-party-audit-2026-08.md` §2, §6.
Grep sweeps: hour loops in LP construction (`for t in range|for h in range`), `os.environ` on the solve path, `ramp`, `cyclic`, epsilon constants.
Limitation: the container is a **shallow clone (1 commit, `.git/shallow` present)**, so "delta since 2026-08" is reconstructed from
documents, docstrings and record dates, not from `git log`.

## 2. What the model does (verified)

**Formulation.** One ISO-agnostic LP per ISO-year, T = 8760, hour-major flat column vector
P | W | S | Chg | Dis | SOC | Flow | Slack | Dump (`model/lp/layout.py`, spec §1.1 lines 23-41). Assembled as scipy.sparse CSR/CSC blocks and
loaded straight into `highspy.Highs()` with `addCols`/`addRows` (`model/lp/model.py:671-692`). No Pyomo/PuLP. Pure LP: no integer
columns anywhere (spec §1.9:418-429).

**Objective & pricing.** `min Σ mc·P + ε(Chg+Dis) + VOLL·Slack + dump_cost·Dump` (spec §1.2:43-66); ε = 0.001 $/MWh
(`config/constants.py:6415-6417`, rule 9). Prices are the row duals on the energy-balance block `row_dual[:n_zones*T]`
(`model/lp/model.py:1476-1500`); RPS, clean-energy, mass-cap and reserve-family duals are sliced from the end-anchored tail
(`model.py:1518-1578`). No separate pricing model on the production path (rule 4). Post-solve scarcity overlays (ERCOT ORDC/RTORPA, NYISO RCPF)
exist in `results/` and feed capacity economics, not scored backcast prices except CAISO (prior audit §2, unchanged per `runner.py` references).

**Passes.** Production = P0 (base MC) → monthly startup-amortisation markup → P1 (bid MC) on the **same** matrix via `changeColsCost`,
warm-started from the P0 basis (`pipeline/solve.py:1-20, 340-360, 699-700`). P1 is the scored run. P2 is archived behind `--enable-legacy-p2`
(spec §1.6:323-347). Three P1-native commitment "bridges" inject a `min_gen` floor from P0 run patterns at the P0→P1 seam
(`pipeline/commitment.py`; shared detector `model/commitment.py::caiso_ra_mustoffer_min_gen`): CAISO RA must-offer (default on), ERCOT gas-CC
bridge (min-load 0.574), NYISO slow-start gas bridge (0.523 / 0.239, plus min-run leg) — spec §1.6 and CLAUDE.md "Dispatch and commitment".

**NEW in-LP commitment posture (undocumented in spec).** `model/lp/rows.py:1213 _build_posture_energy_rows` adds continuous pool
variables `U[p,t]` (online capacity) and `SU[p,t]` (started capacity) with rows: energy headroom `ΣP − U ≤ 0`; min-load coupling
`ΣP − mlf·U ≥ 0`; cyclic startup counting `U_t − U_{t−1} − SU_t ≤ 0` with SU priced in the objective; optional min-up / min-down
window rows (`rows.py:1236-1262`). Gate `ScenarioConfig.spp_commitment_posture: bool = False` (`config/scenarios.py:9457`).
This is a **clustered-UC LP relaxation inside the dispatch LP** (Palmintier-style clustering with the integrality dropped) — a fourth commitment
mechanism, structurally different from the three bridges. `grep -c commitment_posture` returns 0 in `model-methodology-spec.md`, `CLAUDE.md`,
`docs/codebase/02-lp-dispatch.md` and `03-capacity-and-commitment.md`.

**Reserves.** In-LP reserve co-optimisation, zone-aggregate and per-generator forms (`model/lp/reserve_rows.py:20-30`), with online-gated
(spinning) classes expressed as `R − ρ·ΣP ≤ 0` (`reserve_rows.py:259-275`), supply caps and online-capacity caps per tier
(`reserve_rows.py:420-470`). Per-ISO reserve designs, ERCOT ORDC floor steps (OBDRR048) and PJM ORDC curve path in `model/reserves/spec.py:102-145`;
ERCOT's post-9/30 $10,000-VOLL LOLP-ORDC regime is noted but not modelled (`spec.py:168-173`). Storage reserve columns `RS[p,z]` participate
under duration gating (`reserve_rows.py:421-425`).

**Transmission.** Zonal pipe-and-bubble: node-link incidence matrix `(n_zones, n_links)` ±1 (`model/interchange/core.py:28-40`),
`−TTC ≤ Flow ≤ TTC`, interface groups (`core.py:69`), optional per-link marginal-loss fraction only on the gated MISO surface
(`rows.py:1512-1568`). No PTDF, no DC-OPF, no Kirchhoff voltage law. Priced interchange = import tranches / export sinks (`interchange/*.py`).

**Storage.** SOC dynamics rows for hours 1..T−1 plus a cyclic hour-0 row (`rows.py:1795-1822`), efficiencies in/out, perfect annual foresight
(spec §1.9:437-440). Optional AS-sustain SOC floor via `bounds.py` (spec §1.3). Storage entry/value-stack logic in `model/storage.py` (2,231 lines).

**Hydro.** Monthly energy budgets per plant (`rows._build_hydro_rows`) and, since NWPP-36 (2026-09-16), an hourly hydraulic-cascade
water-balance family with spill and pond-volume columns and measured lags τ (`model/lp/hydro_cascade.py:1-60, 158`).

**Ramping.** Spec §1.9:431-434 says "No inter-hour generator ramp-rate constraints". Code carries `_build_ramp_rows` — two-sided plant-group
hourly ramp envelopes from CAMPD-measured max 1-h deltas with availability-edge widening (`rows.py:992-1022`), gated
`ScenarioConfig.ramp_limits = False` (`scenarios.py:7162`). The spec limitation is therefore true only for the default posture.

**Solver.** HiGHS dual simplex; `presolve off` by design (~17 s overhead, negligible reduction — `model.py:683-686`); threads from
`MARKET_SIM_HIGHS_THREADS` (`model.py:678`); `MARKET_SIM_HIGHS_LEAN=1` sets `simplex_scale_strategy=0` (`model.py:687-688`); warm-start toggles
`MARKET_SIM_WARMSTART`, `_XYEAR`, `_P1_BASIS_SEED` (`pipeline/solve.py:488, 536, 577`). Ancillary revenue for capacity economics is an exogenous,
calibrated stream (`model/ancillary.py:1-12`), not an LP output.

**Rule checks.** No `for t in range(T)` in any `model/lp/*` builder; the `for h in range(n_hr)` loops in `reserve_rows.py:259/415/456`
iterate reserve *classes*, not hours (rule 2 PASS). `interchange/caiso.py:1273` loops month×hour-of-day on a mask (12×~5), not LP assembly.
Epsilons are named constants with citations (`constants.py:6415, 6668-6674`) — rule 5 PASS on the sampled surface.

## 3. Comparison table

Comparator columns are the auditor's reading of public documentation; "typical" means the common configuration, not every option.

| Dimension | This model | Commercial PCM (PLEXOS ST / Aurora / EnCompass / GridView / PROMOD) | Open CEM dispatch (GenX / PyPSA(-USA) / Switch / ReEDS / IPM / RESOLVE) | ISO real-time (ERCOT SCED, PJM RT-SCED) |
|---|---|---|---|---|
| Time resolution | Full chronological 8760 h, 1 h step, non-leap calendar (rule 8) | Hourly or sub-hourly chronological, full year or sample weeks | Rep. days/weeks or clustered hours typical; PyPSA/GenX can do 8760; ReEDS 17–~70 timeslices (+ hourly Osprey/PRAS adjuncts); IPM ~load-duration segments | 5-min (SCED) with DA hourly SCUC |
| UC formulation | Pure LP; P0→P1 heuristic bridges inject min_gen floors; optional clustered-UC LP relaxation (`spp_commitment_posture`) | MIP SCUC standard (PLEXOS/EnCompass/GridView); Aurora historically LP/heuristic commitment | GenX: linear clustered UC or MIP optional; PyPSA: linear relaxation default, MIP optional; Switch/ReEDS/IPM: no UC | MIP SCUC (DA/RUC), SCED is LP with fixed commitment |
| Pricing | LP duals on zonal balance rows; post-solve scarcity overlays for capacity economics only (CAISO exception) | Duals of the dispatch LP with commitment fixed; some tools add uplift/ELMP | Duals (shadow prices) of the relaxed problem; not settlement-grade | Settlement LMPs from SCED duals + ORDC/RDPA adders, make-whole uplift |
| Reserves / ORDC | In-LP co-optimised reserve rows, ORDC demand steps, online-gating proxy; NYISO RCPF post-solve | Co-optimised reserves with demand curves common | Usually a reserve margin or simple requirement; GenX/PyPSA have reserve rows | Co-optimised with ORDC (ERCOT) or RT penalty factors (PJM) |
| Transmission | Zonal pipe-and-bubble, TTC bounds, interface groups, gated MISO loss surface; no PTDF | Zonal or nodal DC-OPF with PTDF/losses (PROMOD, GridView nodal) | Zonal transport (ReEDS, GenX default) or linearised DC-OPF (PyPSA, Switch option) | Full nodal SFT/ACOPF-approximated, security-constrained |
| Storage | Explicit SOC, cyclic year, perfect annual foresight, ε tiebreak, AS-sustain SOC floor | Explicit SOC with look-ahead horizons (limited foresight) | Explicit SOC, perfect foresight within horizon | Self-scheduled / offer-based, no foresight modelled |
| Renewables as variables | Decision variables, 0 ≤ W,S ≤ CF·cap, negative PTC offers allowed, dump column (rule 3) | Decision variables with curtailment | Decision variables with curtailment | Dispatchable down via offers (HDL/LDL) |
| Hydro | Monthly budgets + NWPP hourly cascade with lags, spill, pond volume | Monthly/weekly budgets, optional cascades | Monthly budgets, simplified | Self-scheduled with limits |
| Solver | HiGHS dual simplex, presolve off, basis warm-start P0→P1 | Commercial (Gurobi/CPLEX/Xpress) MIP | HiGHS/CBC/Gurobi | Commercial MIP/LP (proprietary) |

Positioning (unchanged from 2026-08): formulation tier sits with Aurora-class LP/heuristic commitment and with GenX/PyPSA in their linear
mode — below MIP-SCUC commercial tools on commitment fidelity; above typical CEMs on temporal resolution and in-LP scarcity design; below
all nodal tools on congestion.

## 4. Findings (ranked)

### Strengths
S1. The LP core is genuinely as described: vectorised block assembly, no hour loops, direct HiGHS, duals as prices, 8760 always
(`rows.py`, `model.py:671-692, 1476-1500`). Rules 2/4/5/6/8/9 verified on the sampled surface.
S2. P0→P1 re-cost on one matrix (`solve.py:11-20, 699-700`) is an efficient and honest way to put cycling cost into prices without a MIP.
S3. In-LP reserve co-optimisation with ORDC steps and an online-gating proxy (`reserve_rows.py:259-275`) is ahead of most open CEMs and
comparable to commercial PCM practice.
S4. The hydro cascade family (`hydro_cascade.py`) is a real physical mechanism, cleanly scoped under rule 19 (redistributes timing, never quantity).
S5. Commitment limitations are stated in the spec (§1.9) rather than hidden.

### Material weaknesses
W1. **Price formation without integer commitment.** With no binaries, every committed unit can sit at any fraction of Pmax; the min_gen bridges
and the posture relaxation make this *less* wrong but the clearing price is still a relaxed-LP dual: no make-whole/uplift, no ELMP-style
convex-hull pricing, and committed-unit inflexibility enters only where a bridge is armed. Expect systematic under-pricing of off-peak hours when
real units are held at LSL for min-run reasons and under-representation of start-cost-driven price spikes. This is the model's single largest
structural divergence from both commercial PCM and ISO practice, and the calibration residuals it is tuned against (band multipliers, rule 1)
partly stand in for it. Owner-level, not engineering-level.
W2. **The clustered-UC LP relaxation (`spp_commitment_posture`) is undocumented** in the spec, CLAUDE.md and the codebase docs (0 hits). It is a
solve-affecting `ScenarioConfig` field (`scenarios.py:9457`) adding new columns and ≥3 row families; spec §1.6 still describes commitment as
"a heuristic screen *between* LP solves". A reader of the spec cannot learn that SU cost can enter the objective directly. Rule 28 requires a
mechanism-matrix row; this audit did not have budget to verify the shard cells.
W3. **Spec/code mismatch on ramping.** Spec §1.9:431 states no inter-hour ramp constraints; `rows.py:992` implements them (gated off).
The limitation should read "default-off".
W4. **Codebase docs are stale on the LP core.** `docs/codebase/02-lp-dispatch.md:3` cites `model/dispatch.py (~2,400 lines)` and
`DispatchModel` at "lines 1653–2149"; at HEAD `dispatch.py` is a 34-line facade and `DispatchModel` is `model/lp/model.py:68` (2,240 lines).
`03-capacity-and-commitment.md:141-150` still titles the sequence "P0→P1→P2 … three LP solves per year" though production is P1-only and P2 archived.
W5. **Zonal, no losses, no PTDF** (`core.py:28-40`). Fine for the stated scope, but intra-zone congestion (ERCOT West/Houston, CAISO SP15 LCAs)
is absorbed into zone prices; the zone definitions are therefore a calibration object and should be ledgered as such.
W6. **Perfect annual storage foresight** (`rows.py:1795-1822`, spec §1.9:437) overstates arbitrage; with growing battery fleets (ERCOT, CAISO)
this is no longer second-order for evening-ramp prices.

### Risks / rule observations
R1. **Env-var knobs on the solve path** (rule 24 "no env-var knobs"): `MARKET_SIM_HIGHS_LEAN` changes `simplex_scale_strategy` (`model.py:687-688`);
`MARKET_SIM_WARMSTART` (`solve.py:488`). Scaling and warm-start do not change the optimum but **can change which degenerate vertex (and thus
which dual) is returned** in a degenerate LP — and 8760-h dispatch LPs are highly degenerate. CLAUDE.md rule 36 declares `_XYEAR` and
`_P1_BASIS_SEED` as solve-affecting choices but is silent on `HIGHS_LEAN` and the base `WARMSTART` toggle. Whether these are fingerprinted by
`cache_key()`/`solve_surface.json` was not verified in budget (`model.py:1890` logs `threads_env` only).
R2. **Presolve off** (`model.py:686`) is a sound speed choice but removes HiGHS's detection of redundant/implied-free rows; dual values on
such rows can differ between presolved and unpresolved solves. Documented, acceptable, worth one regression test on a toy LP.
R3. Second tiebreak epsilon `ERCOT_SWCAP_SHED_TIEBREAK_EPS = 0.01` (`constants.py:6668-6674`) sits "above HiGHS dual-feasibility tolerance at the
$5,000 scale" — a correct concern that implies the 0.001 storage ε may be *below* tolerance at VOLL-scale hours; no evidence it was checked.
R4. Dead/facade surface: `model/dispatch.py`, `model/transmission.py`, `model/capacity.py` are ≤34-line aliases kept for pickle/import identity
(spec §1.3 note). Not dead code, but rule 26 readers should know they are intentional.
R5. ERCOT post-2025 $10,000-VOLL / LOLP-ORDC regime is acknowledged and not modelled (`reserves/spec.py:168-173`) — a forecast-mode gap.

## 5. Delta since the 2026-08-15 audit

Git history is unavailable (shallow clone); delta is from documents and code at HEAD.
- Scope grew from six to **nine** regions (SPP, NWPP, SOCO — CLAUDE.md "What this is"); prior audit §2 cited six.
- **New in-LP mechanisms:** clustered-UC posture relaxation (`rows.py:1213`, SPP-102), NWPP hydraulic cascade (`hydro_cascade.py`, 2026-09-16),
plant-group ramp envelopes (`rows.py:992`, default off). None of the three appear in spec §1.3/§1.6/§1.9.
- NEISO legacy-P2 anomaly (prior O5) confirmed closed: production path is P1-only everywhere this audit could see.
- Rule set grew (rules 29–36: shard, year-isolation, promotion). Rule 36 explicitly names the cross-year warm-start env vars.
- Positioning tier unchanged (§3). The documentation lag the prior audit flagged (D2/D3) has **widened**, not narrowed, on the LP core.

## 6. Recommendations

**Owner decisions**
O-A. Decide whether the posture relaxation (`spp_commitment_posture`) is a candidate production commitment mechanism for every ISO or an SPP-only
probe. If the former, it supersedes the three bridges under rule 19 and spec §1.6/§1.9 must be rewritten; if the latter, label it so.
O-B. Rule on W1: accept relaxed-LP pricing as the model's class (and say so in the determination rubric), or charter a convex-hull/uplift
diagnostic as a default-off probe. Do not let band multipliers silently absorb it.
O-C. Rule whether `MARKET_SIM_HIGHS_LEAN` / `MARKET_SIM_WARMSTART` are registry knobs (rule 24) or infrastructure; if the latter, require the
solve-surface fingerprint to record them.

**Engineering**
E-1. Spec sync: add §1.6 text for the posture rows, §1.9 "ramp: default-off", §1.3 hydro cascade; add mechanism-matrix rows if missing.
E-2. Rewrite `docs/codebase/02-lp-dispatch.md` §2.7 and `03-…md` §3.2 against `model/lp/model.py` and the P1-only production path (`/sync-docs`).
E-3. Add a toy-LP test that the energy-balance duals are invariant to presolve on/off, scaling strategy and warm/cold start on a degenerate case.
E-4. Verify ε = 0.001 against HiGHS `dual_feasibility_tolerance` at VOLL scale; document the result next to `constants.py:6415`.
E-5. Ledger zone boundaries as a DOF-adjacent structural choice per ISO (W5).
