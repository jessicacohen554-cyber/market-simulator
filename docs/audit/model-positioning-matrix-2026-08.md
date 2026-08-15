# Model Positioning Matrix — Market Simulator vs Nine Comparators (AUDIT-A)

**STATUS: RECORD** — Wave-1 deliverable of the Model Audit & Release-Finalization
Program (`docs/model-audit-release-plan-2026-08.md` §3/WS1), companion to
`docs/audit/third-party-audit-2026-08.md`. Written 2026-08-15.

**Method.** Comparator facts were compiled 2026-08-15 from vendor/project
documentation, peer-reviewed papers, national-lab reports, and regulatory
filings; each claim carries a public-source citation and is tagged **[vendor]**
(self-description/marketing) or **[indep]** (independently documented:
regulator, lab, journal, or user filing). Where an axis is not publicly
established the sheet says "not publicly documented" rather than guessing.
None of the comparator tools was operated hands-on for this matrix. Claims
about *this* model cite repository files at `origin/main` @ `9f48419`.

**A naming trap, flagged up front:** "Aurora" the Energy Exemplar software is
distinct from "Aurora Energy Research," a consultancy whose in-house model
authored ERCOT's November 2025 resource-adequacy assessment. Citations below
keep them separate.

---

## 1. This model's column (repository-cited)

- **Category:** chronological zonal production-cost/price simulator (full-8760
  LP, prices = duals) with a one-pass annual capacity-evolution wrapper —
  "production-cost center of gravity" (prior review's phrase, confirmed).
  Forecast 2026–2050 by default; backcast mode for calibration
  (`CLAUDE.md` "What This Is"; `model-methodology-spec.md`).
- **Topology:** zonal, six US ISOs sharing one ISO-agnostic LP — ERCOT 7 /
  CAISO 6 / MISO 6 / PJM 8 / NYISO 5 / NEISO 5 zones incl. import nodes
  (`src/market_sim/config/iso_configs.py:186-1095`); pipe-and-bubble links +
  interface groups + measured seam ladders; no PTDF/DC-OPF, no nodal claims.
- **Commitment/dispatch:** pure LP, no binaries (`model-methodology-spec.md:1241`);
  two-solve P0 base-cost → P1 bid-cost with startup-amortization markup and
  warm-start (`src/market_sim/pipeline/solve.py:124`); heuristic commitment
  bridges gated by unit physics; full 8760 always, non-leap standard-time
  calendar (`src/market_sim/utils/hour_calendar.py`).
- **Price formation:** LP duals on energy balance (`model/lp/model.py:1087`);
  in-LP reserve co-optimization with per-ISO designs incl. ERCOT ORDC demand
  steps (`model/reserves/spec.py`); post-solve published-formula ORDC/RTORPA
  and NYISO RCPF overlays on the forecast capacity-economics signal
  (`results/scarcity.py`, `results/rcpf.py`, `runner.py:3061-3192`); REC
  prices are RPS-row duals, ACP-capped by construction (`model/lp/layout.py:71-79`).
- **Capacity evolution:** one-pass annual screens, deliberately no equilibrium
  iteration (`model-methodology-spec.md:728,1244`); retirement on attainable
  pro-forma inframarginal margin; entry on expected-revenue-vs-LCOE with
  learning and IRA credits; accredited-basis reliability floor with ELCC
  curves (`model/capacity_evolution/evolve.py`).
- **Calibration/validation:** machine-scored determination rubric v3.2 with
  externally-anchored bands (`docs/calibration-determination-rubric.md`;
  `scripts/calibration_verdict.py`); three-tier fail-closed holdout
  (`scripts/lib/holdout_policy.py`); 206 pre-registration documents;
  byte-identity golden gates; public dashboard registering rejected probes.
  Current determinations: PJM CALIBRATED; NYISO/NEISO
  CALIBRATED-WITH-CAVEATS; ERCOT/CAISO/MISO NOT-YET (audit §4).
- **Solver & performance:** HiGHS via `highspy`, direct sparse matrices,
  presolve off, dual simplex + warm starts; measured ~183–339 s per ISO-year
  at ~13.2M columns plant-level (`docs/handoffs/wallclock-baseline-2026-07.md`).
- **Data ecosystem:** bundled six-ISO US pipeline — EIA-860/923/930, EPA
  CAMPD/CEMS, eGRID, ISO disclosures — behind a schema-validated raw→clean
  contract with a generated data dictionary (`data/dictionary/`).
- **License/users:** private in-house model, single-owner governance; no
  regulatory-docket deployment history.

## 2. Capability matrix

| Tool | Category | Topology / network | Commitment formulation | Chronology | Price formation | Endogenous expansion | Published validation regime | License |
|---|---|---|---|---|---|---|---|---|
| **This model** | PCM + evolution wrapper | Zonal, 5–8 zones × 6 US ISOs, pipe-and-bubble + interface groups | Pure LP; P0/P1 heuristic commitment + physics-gated bridges | Full 8760, always | LP duals + in-LP reserve/ORDC co-opt; published-formula scarcity overlays | Yes — one-pass myopic screens (deliberately non-equilibrium) | **Yes** — machine-scored rubric, holdout tiers, pre-registration, published failures | Private |
| Aurora (Energy Exemplar) | PCM + CEM (LTCE) | Zonal (links/ATC); nodal offered | Not publicly documented in detail | Hourly/sub-hourly 8760 | Marginal unit sets zonal price; reserve-margin price-adder option | Yes (iterative LTCE build/retire) | No published rubric; IRP-docket benchmarking | Commercial |
| PLEXOS (Energy Exemplar) | PCM + CEM (LT/PASA/MT/ST) | Zonal + nodal | MILP SCUC, co-optimized reserves | 8760 down to 5-min | Duals; administrative scarcity prices + VoLL | Yes (LT Plan) | Regulator-driven SEM backcast series (NERA) — the industry's clearest example | Commercial |
| EnCompass (Anchor/Yes Energy) | PCM + CEM unified | Zonal + nodal (shift factors) | SCUC/SCED (details not public) | Annual to 1-min steps | Zonal prices + nodal LMPs | Yes, integrated | No published rubric; IRP-docket benchmarking | Commercial |
| GridView (Hitachi Energy) | PCM | Nodal DC load-flow w/ contingencies | SCUC/SCED hourly | Full 8760 chronological | Nodal LMPs (marginal) | Not documented (exogenous fleets) | WECC ADS *dataset* validation manual (input QA, not backcast) | Commercial |
| NREL ReEDS | CEM | Zonal (134 BAs), transport model | Pure LP, no UC | Representative timeslices/days; sequential 2-yr solves | Constraint duals (planning prices) | Yes, incl. retirements | No rubric; Standard Scenarios as de facto benchmark; one builds-vs-actuals hindcast (Cole & Vincent 2019) | BSD-3-Clause |
| GenX (MIT/Princeton) | CEM (configurable ops) | Zonal transport | LP / clustered UC / MILP UC | 8760 or representative periods | LP duals | Yes (single optimization) | Per-study, peer-reviewed | GPL-2.0 |
| PyPSA / PyPSA-USA | CEM + PCM framework | Nodal DC-OPF or zonal; US 30–4,786 nodes | LP; optional MILP UC | Fully flexible | Nodal LMP duals | Yes, co-optimized incl. transmission | Per-study; one open price hindcast (PyPSA-Eur retrospective) | MIT |
| Switch 2.0 | CEM | Zonal transport | Linearized or MIP UC (modular) | Sampled chronological days, multi-period | LP duals | Yes | Peer-reviewed GE MAPS intercomparison (Hawaii) | Apache-2.0 |
| Antares (RTE) | PCM / adequacy (Monte Carlo) | Zonal areas + NTC links | Heuristic linearized ("fast"/"accurate") or MILP | Full 8760, weekly problems × many MC years | Hourly zonal duals + VoLL | No (Antares-Xpansion is a separate module) | Institutional vetting (RTE adequacy report, ENTSO-E ERAA); no backcast rubric | MPL-2.0 (v9+) |

Comparator-row sources are itemized per tool in §3; the "This model" row cites §1.

## 3. Comparator fact sheets

### 3.1 Aurora (Energy Exemplar; formerly EPIS AURORAxmp)

- Both chronological production-cost/price forecasting and Long-Term Capacity
  Expansion (LTCE). [vendor: https://www.energyexemplar.com/aurora] [indep:
  Idaho Power AURORA overview,
  https://docs.idahopower.com/pdfs/AboutUs/PlanningForFuture/irp/AURORA_Overview.pdf]
- Primarily zonal ("Zone — smallest region modeled") with transmission links
  and ATC limits; vendor now also markets nodal simulation with LMP
  decomposition. Typical scope: full interconnections (e.g. WECC) for utility
  IRPs. [indep: Idaho Power PDF; vendor: energyexemplar.com/aurora]
- Hourly/sub-hourly chronological dispatch with ramp, min up/down, must-run,
  maintenance and transmission constraints; the precise formulation (LP vs MIP
  vs proprietary heuristic) is **not publicly documented** at open-model
  detail. [indep: Idaho Power PDF slides 9, 33–34]
- Price formation: "marginal generation units set the zonal price"; ORDC-style
  scarcity represented as a **price adder** to units needed for zonal
  operating-reserve margin (UT Austin ERCOT study of AURORAxmp; $1,000/MWh cap
  in that configuration). [indep:
  https://energy.utexas.edu/sites/default/files/UTAustin_FCe_ERCOT_2017.pdf]
- Endogenous LTCE builds/retires on load-resource balance, economics, RPS/
  emissions constraints; expansion and zonal costing are separate passes.
  [indep: Idaho Power PDF slides 28–33; UT Austin report]
- No formal published backcast rubric; IRP stakeholder processes refine the
  default database; Illinois Power Agency published an Aurora-based study
  describing setup and benchmarking. [indep:
  https://ipa.illinois.gov/content/dam/soi/en/web/ipa/documents/appendix-e-aurora-report-03012024.pdf]
- Solver identities and runtimes not publicly documented. Ships default
  databases from NERC/EIA/WECC; vendor sells simulation-ready North American
  datasets. [indep: Idaho Power PDF; vendor:
  https://www.energyexemplar.com/power-datasets]
- Commercial, proprietary. Users: utility IRPs (Idaho Power, PSE, WECC
  utilities), state agencies, price forecasting for traders/developers.

### 3.2 PLEXOS (Energy Exemplar)

- Both: LT Plan (capacity expansion), PASA (adequacy), MT/ST Schedule
  (chronological production cost), automatically linked. [vendor:
  https://www.energyexemplar.com/plexos; indep: SAARC LT Plan study,
  https://www.saarcenergy.org/wp-content/uploads/2020/07/Energy-System-Optimization-Modelling-through-PLEXOS-for-SAARC-member-states.pdf]
- Zonal and nodal, down to intra-hour; used at ISO scale by NREL and for the
  Irish SEM. MILP security-constrained UC/ED with co-optimized energy +
  reserves; NREL ran hourly DA + 5-minute RT two-settlement emulation
  ("PLEXOS version 7.3 R04 with Xpress-MP solver"). [indep: NREL/Frew et al.,
  https://www.osti.gov/servlets/purl/1807793]
- Prices are duals from the co-optimized SCUC/SCED; scarcity via
  administratively set reserve-scarcity prices and VoLL — the UT Austin study
  notes their PLEXOS configuration had "no scarcity pricing other than the
  value of lost load ($10,000/MWh)". [indep: OSTI 1807793; UT Austin report]
- Endogenous MIP/LP expansion in LT Plan; stochastic optimization supported.
  Solvers: Xpress, CPLEX, Gurobi, MOSEK. [indep: OSTI 1807793; vendor:
  https://www.energyexemplar.com/multi-objective-decision-optimization]
- **Validation standout:** the SEM Committee (Irish regulator) publishes
  recurring PLEXOS input-validation and backcast reports comparing modeled
  fuel-mix generation and prices against actuals (produced with NERA) —
  regulator-driven, not a vendor rubric. [indep:
  https://www.semcommittee.com/files/semcommittee/media-files/SEM-21-086%20SEM%20PLEXOS%20Model%20(2021-2029)%20Input%20Validation%20and%20Backcast%20Report.pdf]
- Commercial, proprietary. Users: ISOs/TSOs, national labs, regulators,
  utilities, consultants.

### 3.3 EnCompass (Anchor Power Solutions / Yes Energy)

- Deliberately unified capacity-expansion + production-cost + power-flow
  platform on one database. Zonal and nodal in one system; nodal pricing via
  stored interval bus prices or calculated shift factors. North American
  focus. [vendor: https://www.yesenergy.com/products/encompass]
- Vendor describes SCUC/SCED with "single-pass co-optimization of energy,
  capacity, and ancillary services"; time steps annual to one minute; formal
  MIP documentation **not publicly documented**; independent consultant pages
  corroborate the combined CEM+PCM role. [vendor: yesenergy.com; indep:
  https://www.synapse-energy.com/tools/capacity-expansion-and-production-cost-modeling]
- Endogenous expansion and retirement integrated with production cost —
  flagship IRP use (Minnesota Power, Great River Energy, DTE). [indep:
  utility-attributed statements,
  https://anchor-power.com/great-river-energy-selects-encompass-software-model-for-integrated-resource-planning/,
  https://anchor-power.com/dte-electric-company-selects-encompass-software/]
- Scarcity/ORDC treatment, solver identity, runtimes: **not publicly
  documented**. No published backcast rubric; case-specific benchmarking in
  MN PUC / Michigan PSC dockets.
- Ships a National Database (78 zones) plus nodal datasets for the three
  interconnections, refreshed with Horizons Energy. [vendor: yesenergy.com]
- Commercial, proprietary.

### 3.4 GridView (Hitachi Energy, formerly ABB)

- Production-cost simulator; endogenous expansion **not publicly documented**
  (fleets are scenario inputs). [indep: ABB Review 1/2003,
  https://library.e.abb.com/public/e47a1e24320e77e9c1256ddd00346ff7/26-29%20M805.pdf]
- Nodal: full transmission load-flow with DC controls, thermal limits,
  contingency constraints, interface limits; interconnection-scale Western US
  studies. Emulates the day-ahead market via SCUC/ED "hour-by-hour
  chronological sequence, for time spans ranging from one day to several
  years." Produces LMPs. Scarcity/ORDC treatment not publicly documented.
  [indep: ABB Review article]
- **Validation practice:** WECC uses GridView for its Anchor Data Set and
  publishes a Data Development and Validation Manual — *dataset* QA, not a
  model backcast rubric. [indep:
  https://www.wecc.org/system/files/documents/anchor_data_set/2024/ADS_Data_Development_and_Validation_Manual_6-30-2020_V3.0.pdf]
- Solver/runtimes not publicly documented; Hitachi is consolidating
  GridView/PROMOD branding in a cloud successor. [vendor:
  https://www.hitachienergy.com/products-and-solutions/energy-portfolio-management/enterprise/gridview]
- Commercial, proprietary. Users: WECC regional planning, utilities, national
  labs (e.g. PNNL,
  https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-35165.pdf),
  transmission developers.

### 3.5 NREL ReEDS

- Capacity-expansion model; NREL typically hands portfolios to a PCM (PLEXOS/
  Cambium) for operational validation rather than trusting CEM dispatch.
  [indep: https://docs.nrel.gov/docs/fy20osti/75322.pdf]
- Zonal: contiguous US, 134 model balancing areas, **transport-model**
  transmission with pre-calculated interface limits — no DC OPF. Pure **LP**,
  no integer UC; recursive-dynamic two-year steps to 2050; chronology via
  representative timeslices/days (17 slices historically; ~33 representative
  days in newer versions) with hourly stress-period augmentation. [indep:
  https://docs.nrel.gov/docs/fy21osti/78195.pdf; https://github.com/NREL/ReEDS-2.0]
- Prices are constraint duals (planning prices); no scarcity/ORDC market
  emulation. Fully endogenous investment/retirement incl. transmission;
  adequacy via capacity-credit/Augur checks between solves.
- No formal backcast rubric; annual Standard Scenarios are the de facto
  benchmark regime. The one institutional hindcast of builds-vs-actuals
  (Cole & Vincent 2019) is quantity, not price. GAMS + CPLEX (commercial);
  open-sourced BSD-3-Clause; the ReEDS-2.0 repo was archived April 2026 with
  development moved to a successor repository. [indep: GitHub]
- Users: DOE/NREL national studies, academics; not typically in IRP dockets.

### 3.6 GenX (MIT/Princeton ZERO Lab)

- Capacity expansion with configurable operational fidelity: LP economic
  dispatch, linearized/clustered UC, or full MILP UC; full 8760 or
  representative periods via built-in time-domain reduction. Zonal transport
  network. [indep: https://github.com/GenXProject/GenX.jl; https://genx.mit.edu]
- Prices: duals of supply-demand balance and policy constraints; VoLL-type
  non-served energy, no ORDC/scarcity emulation. Endogenous builds and
  retirements in a single central-planner optimization (single or
  multi-stage); no equilibrium iteration.
- No formal backcast rubric; validation per-study in the peer-reviewed
  literature (e.g. REPEAT/IRA analyses). Solvers: HiGHS default, Cbc/Clp,
  Gurobi/CPLEX. No bundled national dataset (PowerGenome ecosystem builds US
  cases). Open source, **GPL-2.0**. [indep: GitHub]

### 3.7 PyPSA / PyPSA-USA

- Framework for both expansion planning and operations, nodal or zonal;
  linearized DC-OPF in several equivalent formulations or simple transport
  links. **PyPSA-USA** builds a continental US model on the Breakthrough
  Energy/TAMU synthetic network + EIA data, clusterable 30–4,786 nodes.
  [indep: https://github.com/PyPSA/PyPSA; https://docs.pypsa.org/stable/home/features/;
  Tehranchi et al., https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5029120;
  https://github.com/PyPSA/pypsa-usa]
- LP by default, per-generator MILP UC available; chronology fully flexible
  (full 8760 multi-year or clustered snapshots). Prices are nodal/zonal duals;
  no scarcity machinery beyond configurable load-shedding at VoLL. Endogenous
  co-optimization of generation, storage and transmission, single or
  multi-period; central-planner paradigm.
- No formal backcast rubric; PyPSA-Eur/USA papers document per-study
  validation (the PyPSA-Eur 2020–24 price retrospective is the one open-model
  price hindcast). Solver-agnostic via linopy (HiGHS, Gurobi, CPLEX…). Open
  source, **MIT** (both). [indep: GitHub repos;
  https://pypsa-usa.readthedocs.io/en/latest/about-introduction.html]

### 3.8 Switch 2.0

- Modular capacity-expansion model (Pyomo) with optional operational modules
  (UC, reserves, hydro); zonal load zones with transport-model transmission;
  applied to Hawaii, WECC, Chile, China, Mexico. Linearized or mixed-integer
  UC; chronology via sampled timeseries within multi-period investment frames
  (not full 8760). [indep: https://arxiv.org/pdf/1804.05481;
  https://www.sciencedirect.com/science/article/pii/S2352711018301547;
  https://switch-model.org/]
- Prices: LP duals; no market/scarcity emulation. Endogenous multi-period
  investment and retirement.
- **Validation note:** a peer-reviewed intercomparison against GE MAPS for
  high-renewable Hawaii systems — one of the few formal cross-model
  validations among open tools. [indep:
  https://link.springer.com/article/10.1186/s13705-018-0184-x]
- Any Pyomo-compatible solver. Open source, **Apache-2.0**. [indep:
  https://github.com/switch-model/switch]

### 3.9 Antares-Simulator (RTE)

- Production-cost / adequacy simulation via sequential Monte Carlo (weather/
  outage draws); expansion lives in the separate **Antares-Xpansion**
  companion (Benders), not endogenous in the simulator. [indep:
  https://github.com/AntaresSimulatorTeam/Antares_Simulator;
  https://github.com/AntaresSimulatorTeam/antares-xpansion]
- Zonal "areas" + NTC transport links (flow-based/Kirchhoff extensions via
  binding constraints); canonical pan-European scope. Full 8760-hourly years
  solved as weekly problems across many Monte Carlo years; UC configurable:
  "fast" linearized, "accurate" two-pass linearized + heuristic, or full MILP.
  [indep: https://antares-simulator.readthedocs.io/en/stable/user-guide/solver/07-thermal-heuristic/;
  https://antares-simulator.org/media/files/page/4NOGQ-optimization-problems-formulation.pdf]
- Prices: hourly zonal duals + unsupplied-energy cost (VoLL) — an
  adequacy-economics framing, not bid-based market emulation.
- No published backcast rubric, but heavy institutional vetting: underpins
  RTE's statutory French Generation Adequacy Report and ENTSO-E TYNDP/ERAA.
  [indep: http://opensource.rte-france.com/projects/antares;
  https://antares-simulator.org/]
- C++, solved via OR-Tools interface (RTE's Sirius solver in RTE builds).
  **No US ISO coverage.** Open source — GPLv3 from 2018, **MPL-2.0** at v9.0
  (January 2024). [indep: GitHub/readthedocs]

## 4. Scarcity pricing / ORDC practice in commercial ERCOT studies

Documented practice is heterogeneous and mostly approximation **by adder or by
co-optimization**, not native ORDC curves:

- UT Austin's 2017 AURORAxmp/PLEXOS ERCOT study: AURORAxmp captures ORDC "by
  providing a price adder to units that may be needed to meet operating
  reserve margin in a zone" (the authors declined to impose it for lack of
  history); their PLEXOS setup had "no scarcity pricing other than the value
  of lost load ($10,000/MWh)", producing max prices of $68–88/MWh.
  [indep: https://energy.utexas.edu/sites/default/files/UTAustin_FCe_ERCOT_2017.pdf]
- NREL's peer-reviewed ERCOT-like PLEXOS study replaced the real-time ORDC
  with co-optimization of energy and reserves at administratively set
  reserve-scarcity prices, explicitly flagged as a deviation from actual
  ERCOT. [indep: https://www.osti.gov/servlets/purl/1807793]
- ERCOT's November 2025 resource-adequacy/market-design assessment was
  performed by Aurora Energy Research (the consultancy's in-house model — not
  Energy Exemplar's Aurora), modeling ORDC changes and DRRS options. [indep:
  https://www.ercot.com/files/MarketNotice/2025/11/310252/Aurora%20Assessment%20of%20Resource%20Adequacy%20Needs%20in%20ERCOT%20Region%20and%20Impact%20of%20Market%20Design%20Changes%20(2025.11.10).pdf]

**Positioning consequence:** a zonal LP that applies a reserve-shortage-indexed
price adder on top of LP duals is squarely within observed commercial
practice; this model's in-LP ORDC demand steps and published-formula RTORPA
overlay (`src/market_sim/model/reserves/spec.py`;
`src/market_sim/results/scarcity.py:16-32`) are *ahead* of the documented
commercial treatments, and its RCPF nested-product implementation
(`src/market_sim/results/rcpf.py`) has no documented commercial equivalent.

## 5. Validation-practice norms — where the governance regime sits

Formal, published backcast rubrics are **rare, confirmed**:

- The clearest industry example is regulator-driven, not vendor-driven: the
  SEM Committee's recurring PLEXOS **Input Validation and Backcast Report**
  (with NERA), comparing modeled fuel-mix and prices to actuals.
  [indep: SEM-21-086, URL in §3.2]
- WECC publishes a *dataset* validation manual for its GridView-based Anchor
  Data Set — input QA, not output backcasting. [indep: URL in §3.4]
- Open-model analogues: the Switch-vs-GE-MAPS Hawaii intercomparison and the
  PyPSA-Eur price retrospective; NREL's one builds-vs-actuals hindcast (Cole &
  Vincent 2019) covers quantities, not prices.
- Commercial vendors otherwise assert validation ("proven methodology")
  without publishing rubrics — marketing, not evidence.

Against that landscape, this repository's regime — a versioned machine-scored
rubric with externally-anchored bands, a three-tier fail-closed holdout
policy, 206 pre-registration documents with direction-blind promotion rules,
published NOT-YET determinations, and a dashboard that registers rejected
probes — **exceeds the documented validation practice of every surveyed
comparator**. Two honest counterweights: (1) the SEM series is
regulator-audited while this regime is self-administered (single-owner
sign-off); (2) the commercial tools carry decades of adversarial stakeholder
review in IRP dockets and market-monitor use that this model has never faced.
The regime is stronger on paper *and in operation* (it demotes its own
keepers); what it lacks is external adversarial exposure.

## 6. Positioning conclusions

1. **As a production-cost simulator** the model sits inside the commercial
   zonal tier on formulation (LP-heuristic commitment: Aurora/SERVM/legacy
   SEM-PLEXOS class), matches the commercial norm on chronology (full 8760),
   sits below the nodal tier on network (no congestion/basis/FTR work), and
   sits above documented commercial practice on scarcity-price structure and
   on ancillary/reserve co-optimization at zonal grain.
2. **As a capacity-expansion tool** it is structurally below the co-optimized
   CEM class (ReEDS/GenX/PyPSA/Switch) and the integrated commercial
   expansions (PLEXOS LT, EnCompass): one-pass, myopic, screen-based, no
   transmission expansion. This is a documented deliberate choice
   (merchant-behavior representation; `model-methodology-spec.md:728`), and
   its distinctive compensation is embedding the full PCM-grade 8760 LP inside
   the evolution loop rather than soft-linking two models.
3. **On calibration and reproducibility governance** it exceeds every surveyed
   comparator's documented practice; the nearest analogue (SEM/NERA backcasts)
   is narrower in scope and externally imposed rather than self-adopted.
4. **On deployment evidence** it is behind every commercial comparator: no
   docket history, no third-party user base, single-owner governance, and (at
   HEAD) three of six ISOs NOT-YET on its own rubric with no certified
   out-of-sample number — see the companion audit §4/§7 for what may and may
   not be claimed today.

---

*Prepared as part of the AUDIT-A deliverable set. Comparator claims were
compiled from the cited public sources on 2026-08-15 and were not verified by
hands-on operation of those tools. Repository claims verified at `origin/main`
@ `9f48419`.*
