# Third-party audit 2026-10 — Part B: capacity evolution, policy layer, forecast-uncertainty layer

**Auditor posture:** independent, read-only. HEAD `d7ff7c20` (branch `claude/third-party-audit-2026-10`), 2026-10-03.
No solve, no test run, no file edited; every repo claim cites `file:line` at this HEAD. Comparator statements
about other models are from public documentation (NREL ReEDS, EPA IPM, EIA NEMS/EMM, GenX, Switch, PyPSA-USA,
Aurora, PLEXOS LT Plan, E3 RESOLVE, Cambium; PJM RPM/ELCC, MISO PRA, CAISO RA) and carry no version numbers.
Budget note: the container is a depth-1 clone (`git log` holds one commit, dated 2026-10-02), so the §5 delta is
reconstructed from dated records/docs, not from git history.

## 1. Scope and method

Scope: the one-pass annual capacity-evolution loop (`src/market_sim/model/capacity_evolution/`), its per-ISO arms
(`config/iso_configs.py`), the capacity-market/accreditation seam (`config/capacity_market.py`), the policy layer
(`src/market_sim/policy/`), and the forecast-uncertainty layer (`ensemble.py`, `matrix.py`, `uncertainty.py`,
`structural_prior.py`) plus the forecast program's registered state (`frontend/data/forecast/`). Method: read
CLAUDE.md, spec §5 (`model-methodology-spec.md:905-1300`), `docs/codebase/03-*.md`, `docs/codebase/05-policy.md`,
`docs/forecast-development-plan-2026-07.md`, `docs/capacity-price-forward-methodology-2026-07.md`; then verify
each claim against code; then compare with the 2026-08 audit (`docs/audit/third-party-audit-2026-08.md`).

## 2. What the model does (verified against code)

**Loop.** `evolve_fleet` (`capacity_evolution/evolve.py:129`) advances the fleet exactly one year, forecast mode only,
no within-year iteration (rule 10). The in-code call order is: confirmed exits (`evolve.py:487`) → announced non-fossil
retirements (`evolve.py:533`) → owner-filed fossil dates via the same derate machinery (`evolve.py:556`) → CCS retrofit
screen (`evolve.py:687`) → economic retirements (`evolve.py:804`) → known EIA-860 additions (`evolve.py:875`) →
economic new entry (`evolve.py:1014`) → reserve-margin backstop (`evolve.py:1130`) → dispatch LP with RPS as a row.
This matches the spec (`model-methodology-spec.md:911-945`) and the docstring (`evolve.py:160-200`).

**Arms and defaults (all in `config/scenarios.py`, a 22k-line pydantic model):**

| Arm | Field | Default | Code |
|---|---|---|---|
| Confirmed (instrument-bound) exits, bypass reliability floor | `confirmed_exits_enabled` | True | `scenarios.py:5372`; `retirements.py:456` |
| Owner-filed fossil EIA-860 dates (limb 1b), vintage-gated, reversal registry | `fossil_announced_exits_enabled` | True (since 2026-09-02, ruling Q30) | `scenarios.py:5303`; `evolve.py:556` |
| Economic screen governs undated fossil | `forecast_fossil_retirement_economic` | True | `scenarios.py:5286` |
| Hindcast verification of filed dates (defer/cancel only) | `hindcast_verified_announced_exits` | False | `scenarios.py:4333` |
| Retirement decision rule (decision/execution split, per-fuel lags) | `retirement_rule` | `"pipeline"` | `scenarios.py:5439`; `retirements.py:3158` |
| Hourly reserve-price signal in screens | `screen_reserve_value_enabled` | True | `scenarios.py:6642` |
| CCS retrofit joint retrofit-or-retire, 3 GW/yr/ISO cap | `ccs_retrofit_available_year` (2028) | — | `ccs.py:180` |
| Retrofit capex scaled to host CO2 flow | `ccs_retrofit_capex_co2_scaling` | True (since 2026-09-05, Q42) | `scenarios.py:5868` |
| Reserve-margin backstop (tri-state per market design) | `reserve_margin_build_enabled` | None → on for capacity-market ISOs, off for ERCOT | `scenarios.py:6916`; `adequacy.py:866` |
| Locational deliverability (CETO/CETL, LCR, MIC …) | `capacity_deliverability_limits` | False | `scenarios.py:6956`; spec `:1222` |
| Capacity-market supply clearing | `capacity_market_supply_clearing_by_iso` | None; PJM:True in its ISO arm | `scenarios.py:22029`; `iso_configs.py:1262` |
| Published adequacy requirement | `capacity_adequacy_requirement_published_by_iso` | None; PJM:True | `scenarios.py:22141`; `iso_configs.py:1298` |
| PJM VRE accreditation vintage (ELCC) | `pjm_vre_accreditation_vintage` | False; PJM arm True | `scenarios.py:22333`; `iso_configs.py:1365` |
| Retirement sector gate | `retirement_sector_gate` | False; MISO and PJM arms True | `scenarios.py:21903`; `iso_configs.py:1100,1489` |
| Capacity screens use measured peak in hindcast years | `capacity_screen_peak_measured_hindcast` | True | `scenarios.py:22258` |
| Transmission-expansion registry (TTC deltas) | `transmission_expansion_enabled` | False | `scenarios.py:654,2690`; `data/transmission_expansion.py:1-25` |

**Entry economics.** `apply_economic_new_entry` (`new_entry.py:832`): LCOE vs expected revenue from the prior year's
hourly price-duration curve (`estimate_expected_revenue`, `new_entry.py:616`), reserve-price signal included,
zone-profile capture for wind/solar, per-tech queue caps, Wright's-Law learning (`wright_cost`, `new_entry.py:441`,
cross-year `CumulativeDeployment`), IRA credits netted from LCOE (`policy/ira.py:342`), clean attribute revenue
`max(effective EAC, prior-year RPS dual)` (spec `:1074`). Emerging techs join by availability year (spec `:1077`).
Storage enters on a value stack (arbitrage net of degradation + accredited RA value) per spec §5.5 (`:1085`).

**Retirement economics.** Attainable pro-forma inframarginal margin Σ max(0, p − mc, r)·pmax·avail plus attribute,
capacity and AS revenue vs FOM-only going-forward cost (coal 1.3× FOM) — `03-capacity-and-commitment.md:56-80`,
`retirements.py:3158`. The reliability floor is shared with the backstop (`adequacy.py`).

**Capacity accreditation and clearing.** One seam `MarketDesign.capacity_price_per_firm_mw_yr`
(`capacity_market.py:908`) priced on a CR-1 net-CONE-anchored sloped VRR curve where published
(`capacity_market.py:1368+`), with per-ISO thermal accreditation basis (UCAP 1−EFORd default; PJM ELCC class ratings;
spec `:1277-1300`). ERCOT pays zero. Forward net-CONE vintages: `docs/capacity-price-forward-methodology-2026-07.md`.

**Policy layer.** IRA §45Y/§48E phase-out with OBBBA amendment (`ira.py:299-342`), §45V, §45Q
(`ira.py:91,111`), §45U nuclear (`ira.py:145-171`). RPS is an LP row family with K compliance regions whose duals are
the REC price (`model/lp/rows.py:284`, `policy/rps.py:152-190`). State clean tiers and a federal CES premium are a
second, independent row family (`clean_tiers.py:1-8`, `federal_ces.py:1-8`). Carbon: price paths or a unified
cap-and-trade mass-cap resolver with one price source (`cap_and_trade.py:1-8`, `constraints.py:1-8`).
Voluntary clean demand row, default off (`voluntary_demand.py:1-8`). Exogenous EAC table (`eac.py:1-8`).

**Uncertainty layer.** Deterministic AEO/IPM-style 13-case matrix, explicitly "not a probability band"
(`matrix.py:1-10`); weather-year ensemble plus a correlated multivariate sampler over gas, load, tech cost, policy
(`ensemble.py:1-10`, `uncertainty.py:1-10`); a structural-error prior fit from statistical-mode probes and convolved
with the parametric band (`structural_prior.py:1-10`).

**Forecast program status (registered, machine-scored).** `frontend/data/forecast/program-status.json` (generated
2026-09-06) and `ff-verdicts.json` (111 verdict keys). Every ISO sits at tier T1 (≤5-year POC windows); T1-F
determinations: ERCOT/CAISO/PJM/MISO HOLD, NYISO and NEISO "PROMOTE" on T1-F but HOLD on T1-X crossover; SPP has only a
T1-H hindcast (registered 2026-09-07) and no forecast run; FC-1 structural invariants FAIL for every ISO except NYISO.
No ISO has cleared the §2.1b full-solve authorization gate (`docs/forecast-development-plan-2026-07.md:290`); no
run longer than ~5 years is scheduled; T2/T3 remain deferred. No 2026–2050 result exists in the registry.

## 3. Comparison table

| Dimension | This model | ReEDS-class CEM (ReEDS, GenX, Switch, PyPSA-USA, RESOLVE) | IPM / NEMS-EMM | Commercial LTCE (Aurora, PLEXOS LT Plan) |
|---|---|---|---|---|
| Optimization form | Myopic, one-pass annual screens on last year's prices; dispatch is a pure LP | Intertemporal or sequential-myopic LP/MILP co-optimizing build, retire, dispatch | IPM: intertemporal LP with run-years; NEMS: sequential annual with limited foresight | MILP/LP build-retire co-optimization, usually perfect foresight within horizon |
| Foresight | None beyond prior-year prices and a pipeline lookahead (`new_entry.py:761`) | Perfect foresight (or windowed) over cost paths | IPM perfect foresight; NEMS myopic + expectations | Perfect foresight typical |
| Entry economics | LCOE vs attainable margin on hourly 8760 PDC, queue caps, learning | Endogenous capacity variable with annualized capex in objective | Same, with capacity-value and planning-reserve constraints | Same, with user-set LCOE/cost curves |
| Retirement economics | Going-forward FOM test, per-fuel execution lags, reliability floor, exogenous filed dates | Endogenous retirement variable (GenX/ReEDS) or age-based | IPM endogenous; NEMS mix of age and economics | Endogenous or user retirement schedule |
| Accreditation (ELCC) | Per-ISO published basis; PJM class ELCC; storage ELCC(duration) + saturation; VRE ELCC curves gated | Endogenous ELCC/capacity-credit via stress periods (ReEDS, RESOLVE) | Reserve-margin accounting with fixed capacity credits | Published or user ELCC tables |
| Capacity-market clearing | CR-1 sloped VRR curve per ISO, net-CONE vintages; supply clearing armed only for PJM | Planning-reserve constraint; no market curve | Reserve-margin constraint | Explicit RPM/PRA-style auction modules available |
| Transmission expansion | Committed-project registry only, default off; no endogenous expansion | Endogenous inter-zonal expansion (ReEDS, GenX, PyPSA) | IPM endogenous expansion limited | Endogenous or project list |
| Policy | IRA credits in LCOE and offers; RPS/CES/clean tiers as LP rows with REC duals; carbon price or mass cap | RPS/CES constraints with duals; carbon caps; IRA credits | IPM: RPS, caps, credits; NEMS: full tax-credit logic | RPS/REC and carbon modules |
| Uncertainty | Scenario matrix + correlated sampler + structural prior (built; production band deferred) | Scenario matrix; Cambium publishes scenarios, not bands | Scenario matrix (AEO side cases) | Stochastic LT Plan in PLEXOS; scenarios in Aurora |
| Learning/cost paths | Wright's Law on cumulative GW, ATB-derived capex | Exogenous ATB cost trajectories (ReEDS) or endogenous learning options | Exogenous cost curves with learning in NEMS | Exogenous trajectories |
| Chronology | Full 8760 every year (rule 8) | Representative periods typical | Representative load segments | Chronological or sampled |

Net reading: dispatch chronology exceeds the CEM class; investment logic is a heuristic screening model (the spec
says so, `:909`) and remains below ReEDS/GenX/IPM in co-optimization, foresight and transmission build.

## 4. Findings (ranked)

### Strengths
S1. The loop is implemented exactly as specified, in one place, with every arm gated and declared in `ScenarioConfig`
    (rule 24) and the cache key (`config/solve_surface.py`); default-off arms are byte-identical when off.
S2. Capacity accreditation and pricing sit on one seam per ISO (`capacity_market.py:908`) with published bases and
    vintages — closer to PJM/MISO/ISO-NE practice than most academic CEMs.
S3. RPS/CES/clean tiers as LP rows with duals is the correct structural treatment; the REC dual feeds entry next year.
S4. The retirement channel honoring owner-filed EIA-860 dates (limb 1b) is forward-reproducible and measured
    (MISO recall 5/19 → 16/19, spec `:962`), a genuine improvement over the economic-only posture of 2026-08.
S5. The forecast board is candid: no ISO is promoted beyond T1, and the structural FC-1 failures are named per ISO.

### Material weaknesses
W1. **Myopic one-pass vs intertemporal CEM.** Entry/retirement decide on last year's prices only
    (`new_entry.py:616`). No expectations of future gas, carbon, demand or cost declines enter the LCOE hurdle,
    so the model will systematically under-build ahead of load/policy inflections and over-react to a single
    scarce year; ReEDS/GenX/IPM optimize the horizon. The spec acknowledges "screening model" (`:909`).
W2. **No transmission expansion.** Only a committed-project registry exists, default off
    (`scenarios.py:2690`; `data/transmission_expansion.py:17-25` names import-tranche and intra-zonal rows as
    "recorded-not-applied"). A 2050 horizon with static TTCs is a first-order omission vs every comparator class.
W3. **Reliability outcomes fail the model's own invariants.** FC-1 FAILs on reserve-margin band I12 and scarcity
    slack I3 for ERCOT/CAISO/PJM; ERCOT reserve margin reads −1.5 % by 2030 (`program-status.json`, isos.ERCOT).
    The backstop is off for ERCOT by design; the economic entry signal is not forming adequate capacity.
W4. **Storage value stack is structural-only.** No ISO's registered run validates storage entry (MISO's T1-F
    notes +4 GW from cap-market storage entry with FC-1 FAIL); the arbitrage leg is priced off a prior-year LP that
    carries the ε tiebreaker, so storage revenue is model-endogenous with no benchmark.
W5. **Capacity-market clearing is armed for PJM only** (`iso_configs.py:1262`) and the board records "position past
    zero-cross pays $0 (BLK-3 open)"; MISO/NYISO/NEISO curves price but do not clear supply.
W6. **Deliverability (`capacity_deliverability_limits`) is default-off and validated only on its measured-import
    half (CAISO)** per CLAUDE.md; forward LCR/CETL evolution is unmodeled.
W7. **Uncertainty layer is built but not produced.** PB-5 production band deferred (plan `:103`); the only
    published band artifact is `ercot-pb-bands-t1.js` at T1 scale. Structural prior is fit from statistical-mode
    probes of backcast years, which does not measure forward structural error.
W8. **Learning curves are endogenous to ISO deployment** (`CumulativeDeployment`): a single-ISO run under-counts
    global experience, biasing costs high relative to ATB trajectories used by ReEDS/Cambium.

### Risks
R1. The 22k-line `scenarios.py` with hundreds of gated booleans (prior audit counted ~695 fields; more now) is the
    single largest maintainability and reproducibility risk; per-ISO `default_scenario_overrides` make "the
    default" ISO-dependent in ways a reader cannot see from the dataclass.
R2. Every flip since 2026-08 (Q30 fossil dates, Q42 CO2-scaled capex, D48 PJM vintage, D53 sector gate) was
    adjudicated on ≤5-year hindcast/crossover A/Bs; none has been exercised on a 25-year horizon where learning,
    CCS caps and horizon exhaustion (~2030, spec `:968`) actually bind.
R3. IRA/OBBBA phase-out logic (`ira.py:299-342`) is statute-cited but policy-volatile; no scenario axis flags
    repeal risk beyond the CES premium ensemble.

### Doc/code mismatches
D1. `docs/codebase/03-capacity-and-commitment.md:8-26` lists six steps with economic retirement (2) BEFORE CCS (4),
    and `:43-48` states fossil announced dates are "a default no-op". Code runs CCS (`evolve.py:687`) before
    retirement (`evolve.py:804`) and honors fossil dates by default (`evolve.py:556`, `scenarios.py:5303`).
    The spec (`:928-938`) and `evolve.py` docstring are correct; the code-reference page is stale.
D2. `03-capacity-and-commitment.md:9` cites `capacity.py:1412`; `model/capacity.py` is a 32-line shim and the
    logic lives in `capacity_evolution/` (`evolve.py`, `retirements.py` 4058 lines, `new_entry.py`, `ccs.py`,
    `adequacy.py`). Same page cites `apply_economic_retirements` at "line 279" and `apply_ccs_retrofit` at "1257".
D3. `03-*.md:30-41` calls confirmed exits "the ONLY exogenous fossil exit channel"; limb 1b is a second one.
D4. `docs/forecast-development-plan-2026-07.md:84-96` "Current state" is stamped 2026-07-17 and still says
    "Capacity-market instruments … all OFF"; PJM clearing/adequacy arms are on in `iso_configs.py:1262,1298`.
D5. Prior audit D4 (`third-party-audit-2026-08.md:575`, warm-start docstring vs default) — not re-verified here;
    CLAUDE.md rule 36 now states both warm-start env knobs default off.

## 5. Delta since the 2026-08-15 audit

- **Fossil retirement channel changed materially**: 2026-08 audit described economic-only fossil exits; owner
  ruling Q30 (2026-09-02) armed owner-filed EIA-860 dates by default (`scenarios.py:5303`; record
  `docs/records/forecast/FINDING-capx-d42-fossil-dates-ab-2026-09-02.md`).
- **CCS retrofit capex re-based** to the host's CO2 flow by default (Q42, 2026-09-05; `scenarios.py:5868`).
- **PJM arms added**: supply clearing, published adequacy requirement, VRE accreditation vintage (D48);
  retirement sector gate for PJM/MISO (D53). Rule 36 year-isolation and rule 35 one-command promotion are new.
- **Forecast board**: still HOLD everywhere as in 2026-08, but NYISO/NEISO now read T1-F "PROMOTE" (T1-X HOLD),
  SPP gained a T1-H hindcast (2026-09-07), and the FC-1 blocker map was redrawn per ISO (2026-09-01).
  Prior-audit finding O6 ("locked tests unspent; forecast validity still asserted") remains open: no run beyond
  T1, no full-solve authorization, no forward-skill number.
- **Uncertainty layer**: unchanged in kind (PB-0…PB-4 landed in July); PB-5 still deferred.
- Positioning vs comparators (prior audit `:454-470`): unchanged — dispatch above class, capacity evolution below.

## 6. Recommendations

**Owner rulings needed**
O-1. Decide whether a 2026–2050 product requires an intertemporal (or rolling-window with expectations)
     investment step; if yes, scope it as a new mechanism-matrix row rather than more screen arms.
O-2. Rule on transmission: either arm `transmission_expansion_enabled` with the committed registry as a default
     forecast posture, or declare static TTCs a stated limitation in spec §1.9.
O-3. Rule on ERCOT adequacy: an energy-only ISO whose own invariants show −1.5 % reserve margin in 2030 needs
     either a scarcity-price fix that forms entry or a documented acceptance that T1-F cannot pass.
O-4. Authorize (or explicitly defer again) PB-5 so a published band exists before any forward number is quoted.

**Engineering**
E-1. Fix `docs/codebase/03-capacity-and-commitment.md` (D1–D3) and plan §1 (D4) via `/sync-docs`; add a CI
     check that doc step order matches `evolve.py` call order.
E-2. Add a benchmark cell for storage entry (e.g., MISO/CAISO realized storage additions 2023–2025) before the
     value stack is relied on in any T2 run.
E-3. Add a horizon-length regression (one ISO, 2026–2035, default arms) so learning, CCS cap and horizon
     exhaustion are exercised at all before the full-solve gate is argued.
E-4. Split `scenarios.py` into per-domain config modules with the same field names (no cache-key change).
E-5. Make learning experience read a national/ATB cumulative base, with the ISO's own builds as an increment.
